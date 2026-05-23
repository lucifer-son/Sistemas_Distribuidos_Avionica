import json
import os
import time
import random
import uuid
import paho.mqtt.client as mqtt

# Configurações do Middleware MQTT
BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
PORTA = int(os.getenv("MQTT_PORT", "1883"))
TOPICO = "avionica/sensores/waic"

def iniciar_lider():
    cliente = mqtt.Client()
    cliente.connect(BROKER, PORTA, 60)
    print("📡 Líder do Cluster WAIC INICIADO.")
    print("A agregar dados dos motores via rede sem fios e publicando no Middleware...")
    print("-" * 50)

    try:
        while True:
            # Agrega a informação de vários sensores sem fio num só pacote
            pacote_agregado = {
                "id_mensagem": str(uuid.uuid4()),
                "origem": "Lider_WAIC",
                "timestamp": time.time(),
                "dados": {
                    "pressao_motor": round(random.uniform(200.0, 240.0), 1),
                    "temperatura": round(random.uniform(85.0, 110.0), 1)
                },
                "canal": "Wireless"
            }

            # Publica no tópico de rádio (WAIC)
            cliente.publish(TOPICO, json.dumps(pacote_agregado))
            
            print(f"📡 Pacote WAIC Enviado! Motor: {pacote_agregado['dados']['pressao_motor']} psi | Temp: {pacote_agregado['dados']['temperatura']} °C")
            
            # Envia mais rápido para simular o tráfego que vimos no OMNeT++ (a cada 2 segundos)
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nNó Líder WAIC Desligado.")
        cliente.disconnect()

if __name__ == "__main__":
    iniciar_lider()
