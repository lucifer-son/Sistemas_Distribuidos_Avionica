import json
import os
import time
import random
import uuid
import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
PORTA = int(os.getenv("MQTT_PORT", "1883"))
TOPICO = "avionica/sensores/waic"
TOPICO_SIMULACAO = "avionica/comandos/simulacao"

simulacao_ativa = False

def ao_conectar(client, userdata, flags, rc):
    client.subscribe(TOPICO_SIMULACAO)

def ao_receber_mensagem(client, userdata, msg):
    global simulacao_ativa
    try:
        pacote = json.loads(msg.payload.decode("utf-8"))
        status = pacote.get("status")
        if status == "START":
            simulacao_ativa = True
        elif status == "STOP":
            simulacao_ativa = False
    except Exception:
        pass

def iniciar_lider():
    global simulacao_ativa
    cliente = mqtt.Client()
    cliente.on_connect = ao_conectar
    cliente.on_message = ao_receber_mensagem
    cliente.connect(BROKER, PORTA, 60)
    cliente.loop_start()
    
    print("📡 Líder do Cluster WAIC INICIADO (Aguardando simulação...).")
    print("-" * 50)

    try:
        while True:
            if not simulacao_ativa:
                time.sleep(1)
                continue

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

            cliente.publish(TOPICO, json.dumps(pacote_agregado))
            print(f"📡 Pacote WAIC Enviado! Motor: {pacote_agregado['dados']['pressao_motor']} psi | Temp: {pacote_agregado['dados']['temperatura']} °C")
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nNó Líder WAIC Desligado.")
        cliente.loop_stop()
        cliente.disconnect()

if __name__ == "__main__":
    iniciar_lider()