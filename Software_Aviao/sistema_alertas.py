import json
import os
import threading
import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
PORTA = int(os.getenv("MQTT_PORT", "1883"))
TOPICO_FALHAS = "avionica/comandos/falhas"
TOPICO_WAIC = "avionica/sensores/waic"

motor_ja_falhou = False

def falar_texto(texto):
    print(f"🔊 ALARME ACIONADO: {texto}")
    # Usa o motor de voz nativo do Windows (infalível e não congela o Python)
    comando = f'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{texto}\')"'
    threading.Thread(target=lambda: os.system(comando)).start()

def ao_conectar(client, userdata, flags, rc):
    print("✅ 🔈 Módulo de Áudio (EGPWS/TCAS) CONECTADO e à escuta!")
    client.subscribe([(TOPICO_FALHAS, 0), (TOPICO_WAIC, 0)])

def ao_receber_mensagem(client, userdata, msg):
    global motor_ja_falhou
    try:
        pacote = json.loads(msg.payload.decode())
        
        if msg.topic == TOPICO_FALHAS:
            tipo = pacote.get("tipo")
            if tipo == "trafego": falar_texto("Traffic! Traffic!")
            elif tipo == "queda": falar_texto("Terrain! Pull up! Pull up!")
            elif tipo == "motor": falar_texto("Warning. Engine Failure.")
            
        elif msg.topic == TOPICO_WAIC:
            pressao = pacote['dados']['pressao_motor']
            if pressao < 10 and not motor_ja_falhou:
                motor_ja_falhou = True
                falar_texto("Engine pressure lost.")
            elif pressao > 10:
                motor_ja_falhou = False
    except Exception as e:
        pass

if __name__ == "__main__":
    print("⏳ A iniciar sistemas vocais nativos...")
    cliente = mqtt.Client()
    cliente.on_connect = ao_conectar
    cliente.on_message = ao_receber_mensagem
    cliente.connect(BROKER, PORTA, 60)
    cliente.loop_forever()
