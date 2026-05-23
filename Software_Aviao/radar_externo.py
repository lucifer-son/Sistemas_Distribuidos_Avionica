import json
import os
import time
import random
import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
PORTA = int(os.getenv("MQTT_PORT", "1883"))
TOPICO_RADAR = "avionica/radar"

def iniciar_radar():
    cliente = mqtt.Client()
    cliente.connect(BROKER, PORTA, 60)
    cliente.loop_start()

    climas = ["CÉU LIMPO", "NUVENS", "TEMPESTADE"]

    try:
        while True:
            clima_atual = random.choices(climas, weights=[50, 30, 20])[0]
            # Se for tempestade, a temperatura cai drasticamente para baixo de zero
            temp = random.randint(-30, -5) if clima_atual == "TEMPESTADE" else random.randint(5, 15)

            pacote = {
                "id_mensagem": f"rad_{int(time.time()*1000)}",
                "dados": {
                    "vento_knots": random.randint(0, 40),
                    "turbulencia": "SEVERA" if clima_atual == "TEMPESTADE" else "LEVE",
                    "radar_clima": clima_atual,
                    "temp_externa_c": temp,
                    "qnh_hpa": random.randint(1000, 1025),
                    "atc_msg": "Evite formacoes" if clima_atual == "TEMPESTADE" else "Rota livre"
                }
            }
            cliente.publish(TOPICO_RADAR, json.dumps(pacote))
            time.sleep(3) # O radar varre a cada 3 segundos
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    iniciar_radar()
