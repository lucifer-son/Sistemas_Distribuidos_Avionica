import json
import os
import time
import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
PORTA = int(os.getenv("MQTT_PORT", "1883"))
TOPICO_ESCUTA_SENSORES = "avionica/sensores/motor/#" # Escuta todos (A, B e C)
TOPICO_WAIC_FINAL = "avionica/sensores/waic"         # Envia o consenso para o painel

leituras = {"A": 40.0, "B": 40.0, "C": 40.0}

def ao_receber_mensagem(client, userdata, msg):
    try:
        pacote = json.loads(msg.payload.decode())
        motor_id = pacote["id"]
        leituras[motor_id] = pacote["pressao"]
    except: pass

def iniciar():
    cliente = mqtt.Client()
    cliente.on_message = ao_receber_mensagem
    cliente.connect(BROKER, PORTA, 60)
    cliente.subscribe(TOPICO_ESCUTA_SENSORES)
    cliente.loop_start()
    
    print("⚖️ Algoritmo de Consenso TMR Iniciado. A proteger os motores...")

    while True:
        # 1. Extrai os três valores lidos
        valores = list(leituras.values())
        
        # 2. ALGORITMO DE CONSENSO (MEDIANA)
        # Se os valores forem [0.0, 41.2, 41.5], ao ordenar fica [0.0, 41.2, 41.5].
        # O valor do meio (índice 1) será sempre o valor da maioria saudável!
        valores_ordenados = sorted(valores)
        pressao_consensual = valores_ordenados[1] 

        # 3. Alerta o sistema se descobrir um mentiroso
        for sensor, valor in leituras.items():
            if abs(valor - pressao_consensual) > 10:
                print(f"⚠️ AVISO: Sensor {sensor} descartado (Falha Bizantina)! Lido: {valor}")

        # 4. Envia o valor verificado para o painel do piloto!
        pacote_final = {
            "dados": {
                "pressao_motor": pressao_consensual,
                "temperatura": 600.0
            }
        }
        cliente.publish(TOPICO_WAIC_FINAL, json.dumps(pacote_final))
        time.sleep(1)

if __name__ == "__main__":
    iniciar()