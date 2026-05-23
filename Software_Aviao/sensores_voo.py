import json
import os
import time
import random
import threading
import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
PORTA = int(os.getenv("MQTT_PORT", "1883"))
TOPICO_VOO = "avionica/sensores/voo"
TOPICO_CMD = "avionica/comandos/velocidade" # NOVO TÓPICO PARA OUVIR COMANDOS

# Variável global para a velocidade real do avião
velocidade_atual_mach = 0.80

# Função que será chamada após os 3 segundos de inércia
def aplicar_nova_velocidade(nova_vel):
    global velocidade_atual_mach
    velocidade_atual_mach = nova_vel
    print(f"⚙️ [FÍSICA] Inércia superada. Velocidade real do avião agora é {velocidade_atual_mach} Mach.")

# Callbacks do Middleware
def ao_conectar(client, userdata, flags, rc):
    print("🛫 Módulo de Voo conectado. A escutar comandos do cockpit...")
    client.subscribe(TOPICO_CMD) # Começa a escutar os botões do painel

def ao_receber_mensagem(client, userdata, msg):
    try:
        pacote = json.loads(msg.payload.decode())
        nova_vel = pacote.get("nova_velocidade")
        
        if nova_vel is not None:
            print(f"📥 [COMANDO] Autothrottle ajustado para {nova_vel} Mach. Aguardando 3s de resposta dos motores...")
            # MAGIA DO SISTEMA DISTRIBUÍDO: Dispara um temporizador de 3 segundos em background (Thread)
            # Isto permite que o avião continue a mandar dados de combustível enquanto a velocidade não muda!
            threading.Timer(3.0, aplicar_nova_velocidade, args=[nova_vel]).start()
    except Exception as e:
        pass

def iniciar_sensores_voo():
    global velocidade_atual_mach
    cliente = mqtt.Client()
    cliente.on_connect = ao_conectar
    cliente.on_message = ao_receber_mensagem
    
    cliente.connect(BROKER, PORTA, 60)
    # INICIA A THREAD DO MIDDLEWARE PARA CONSEGUIRMOS RECEBER MENSAGENS AO MESMO TEMPO QUE ENVIAMOS
    cliente.loop_start() 

    combustivel = 100.0
    altitude = 35000 

    try:
        while True:
            combustivel = max(0.0, combustivel - 0.01)
            altitude += random.randint(-50, 50)
            
            pacote = {
                "origem": "Sensores_Gerais_Voo",
                "timestamp": time.time(),
                "dados": {
                    "combustivel_pct": round(combustivel, 2),
                    "altitude_ft": altitude,
                    "estabilizador_graus": round(random.uniform(-3.0, 3.0), 1),
                    "pressao_cabine_psi": round(random.uniform(10.8, 11.2), 2),
                    # Adiciona uma turbulência mínima (+- 0.002) para o número no painel parecer "vivo"
                    "velocidade_mach": round(velocidade_atual_mach + random.uniform(-0.002, 0.002), 3) 
                }
            }

            cliente.publish(TOPICO_VOO, json.dumps(pacote))
            print(f"📡 Enviando Telemetria -> Combustível: {pacote['dados']['combustivel_pct']}% | Mach: {pacote['dados']['velocidade_mach']}")
            time.sleep(1) 

    except KeyboardInterrupt:
        cliente.disconnect()

if __name__ == "__main__":
    iniciar_sensores_voo()
