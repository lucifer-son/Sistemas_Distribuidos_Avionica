import json
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORTA = 1883
TOPICO_RADAR = "avionica/radar"
TOPICO_ANTI_ICE = "avionica/sistemas/anti_ice"

anti_ice_ligado = False

def ao_conectar(client, userdata, flags, rc):
    print("🤖 FADEC/Automação ONLINE. A monitorizar perigos meteorológicos...")
    client.subscribe(TOPICO_RADAR)

def ao_receber_mensagem(client, userdata, msg):
    global anti_ice_ligado
    try:
        pacote = json.loads(msg.payload.decode())
        if msg.topic == TOPICO_RADAR:
            dados = pacote.get("dados", {})
            clima = dados.get("radar_clima", "")
            temp = dados.get("temp_externa_c", 0)

        
            if clima == "TEMPESTADE" and temp < 0 and not anti_ice_ligado:
                anti_ice_ligado = True
                print(f"❄️ Gelo detetado (Temp: {temp}°C). A ligar ANTI-ICE automaticamente!")
                client.publish(TOPICO_ANTI_ICE, json.dumps({"status": "ON", "msg": "ICE DETECTED - SYS ON"}))
            
            elif clima != "TEMPESTADE" and temp > 0 and anti_ice_ligado:
                anti_ice_ligado = False
                print(f"☀️ Clima normalizado (Temp: {temp}°C). A desligar ANTI-ICE.")
                client.publish(TOPICO_ANTI_ICE, json.dumps({"status": "AUTO", "msg": "ANTI-ICE: AUTO"}))
    except: pass

if __name__ == "__main__":
    cliente = mqtt.Client()
    cliente.on_connect = ao_conectar
    cliente.on_message = ao_receber_mensagem
    cliente.connect(BROKER, PORTA, 60)
    cliente.loop_forever()
