
import json
import time
import random
import uuid
import paho.mqtt.client as mqtt

# Configurações do Middleware MQTT
BROKER = "broker.hivemq.com"
PORTA = 1883
TOPICO = "avionica/sensores/freios"

def iniciar_sensor():
    cliente = mqtt.Client()
    cliente.connect(BROKER, PORTA, 60)
    print("⚙️ Sensor de Freios INICIADO e conectado ao Middleware.")
    print("A enviar telemetria redundante (Canal A e Canal B)...")
    print("-" * 50)

    try:
        while True:
            # Simula a pressão física dos freios hidráulicos (40 a 100 psi)
            # Ocasionalmente vai cair abaixo de 50 para testarmos o Alarme na Interface!
            pressao_atual = round(random.uniform(45.0, 100.0), 1)
            
            # GERA UM ID ÚNICO PARA A MENSAGEM (Sincronização e Desduplicação)
            id_unico = str(uuid.uuid4())

            # Monta o pacote de dados base
            pacote = {
                "id_mensagem": id_unico,
                "origem": "Sensor_Freio_Principal",
                "timestamp": time.time(),
                "dados": {
                    "pressao": pressao_atual
                }
            }

            # Envia via CANAL A
            pacote["canal"] = "A"
            cliente.publish(TOPICO, json.dumps(pacote))
            print(f"[Canal A] Enviado ID: {id_unico[:8]}... | Pressão: {pressao_atual} psi")
            
            # Pequeno atraso simulando a rede
            time.sleep(0.1)

            # Envia exatamente o mesmo dado via CANAL B (Redundância)
            pacote["canal"] = "B"
            cliente.publish(TOPICO, json.dumps(pacote))
            print(f"[Canal B] Enviado ID: {id_unico[:8]}... (Cópia Redundante de Segurança)")
            print("-" * 50)

            # Aguarda 3 segundos para a próxima leitura
            time.sleep(3)

    except KeyboardInterrupt:
        print("\nSensor Desligado.")
        cliente.disconnect()

if __name__ == "__main__":
    iniciar_sensor()
