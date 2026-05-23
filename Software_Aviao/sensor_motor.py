import os
import json
import time
import random
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORTA = 1883

# O Docker vai dizer a cada clone se ele é o A, B ou C
ID_SENSOR = os.getenv("SENSOR_ID", "A") 
TOPICO_PUBLISH = f"avionica/sensores/motor/{ID_SENSOR}"
TOPICO_SABOTAGEM = f"avionica/comandos/falhas/sensor_{ID_SENSOR}"

sensor_corrompido = False

def ao_conectar(client, userdata, flags, rc):
    print(f"⚙️ Sensor de Motor {ID_SENSOR} ONLINE.")
    client.subscribe(TOPICO_SABOTAGEM)

def ao_receber_mensagem(client, userdata, msg):
    global sensor_corrompido
    try:
        if msg.topic == TOPICO_SABOTAGEM:
            sensor_corrompido = True
            print(f"💥 [FALHA BIZANTINA] O Sensor {ID_SENSOR} enlouqueceu e vai mentir!")
    except: pass

def iniciar():
    cliente = mqtt.Client()
    cliente.on_connect = ao_conectar
    cliente.on_message = ao_receber_mensagem
    cliente.connect(BROKER, PORTA, 60)
    cliente.loop_start()

    while True:
        # Se for sabotado, envia 0.0. Se estiver saudável, envia a pressão real (~40 psi)
        pressao = 0.0 if sensor_corrompido else round(random.uniform(40.0, 42.0), 2)
        
        pacote = {"id": ID_SENSOR, "pressao": pressao}
        cliente.publish(TOPICO_PUBLISH, json.dumps(pacote))
        time.sleep(1)

if __name__ == "__main__":
    iniciar()
