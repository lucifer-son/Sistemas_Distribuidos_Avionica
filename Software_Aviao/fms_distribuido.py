import json
import time
import math
import os
import requests
import threading
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORTA = 1883
TOPICO_ROTA_CMD = "avionica/comandos/rota" # Escuta o que o piloto digitou
TOPICO_VOO = "avionica/sensores/voo"       # Escuta a velocidade do avião
TOPICO_FMS_DADOS = "avionica/fms/dados"    # Publica o resultado calculado

API_KEY = os.getenv("FMS_API_KEY") or os.getenv("API_NINJAS_KEY")

class FlightManagementSystem:
    def __init__(self):
        self.velocidade_mach = 0.80
        self.rota_atual = {"origem": "N/A", "destino": "N/A", "distancia_nm": 0}
        
        self.cliente = mqtt.Client()
        self.cliente.on_connect = self.ao_conectar
        self.cliente.on_message = self.ao_receber_mensagem

    def calcular_distancia(self, lat1, lon1, lat2, lon2):
        # Fórmula de Haversine para a curvatura da terra (em Milhas Náuticas)
        R = 3440.065 
        dLat, dLon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
        return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

    def buscar_coordenadas(self, icao):
        if not API_KEY:
            print("❌ Erro: defina FMS_API_KEY no .env para consultar a API Ninjas.")
            return None, None

        url = f"https://api.api-ninjas.com/v1/airports?icao={icao}"
        resposta = requests.get(url, headers={'X-Api-Key': API_KEY})
        if resposta.status_code == 200 and len(resposta.json()) > 0:
            dados = resposta.json()[0]
            return float(dados['latitude']), float(dados['longitude'])
        return None, None

    def processar_rota(self, origem, destino):
        print(f"🌍 FMS a calcular rota {origem} -> {destino} via API...")
        lat1, lon1 = self.buscar_coordenadas(origem)
        lat2, lon2 = self.buscar_coordenadas(destino)
        
        if lat1 and lat2:
            dist = self.calcular_distancia(lat1, lon1, lat2, lon2)
            self.rota_atual = {"origem": origem, "destino": destino, "distancia_nm": dist}
            print(f"✅ Rota planeada: {dist:.1f} NM")
        else:
            print("❌ Erro: ICAO não encontrado.")

    def ao_conectar(self, client, userdata, flags, rc):
        print("💻 FMS Conectado à Rede Aviônica.")
        client.subscribe([(TOPICO_ROTA_CMD, 0), (TOPICO_VOO, 0)])

    def ao_receber_mensagem(self, client, userdata, msg):
        try:
            pacote = json.loads(msg.payload.decode())
            if msg.topic == TOPICO_VOO:
                self.velocidade_mach = pacote['dados']['velocidade_mach']
            elif msg.topic == TOPICO_ROTA_CMD:
                origem, destino = pacote.get("origem").upper(), pacote.get("destino").upper()
                threading.Thread(target=self.processar_rota, args=(origem, destino)).start()
        except: pass

    def iniciar(self):
        self.cliente.connect(BROKER, PORTA, 60)
        self.cliente.loop_start()

        while True:
            eta_minutos = 0
            vel_knots = self.velocidade_mach * 600.0
            
            if self.rota_atual["distancia_nm"] > 0 and vel_knots > 0:
                eta_minutos = (self.rota_atual["distancia_nm"] / vel_knots) * 60

            pacote = {
                "dados": {
                    "rota_texto": f"{self.rota_atual['origem']} ➔ {self.rota_atual['destino']}",
                    "distancia_nm": round(self.rota_atual["distancia_nm"], 1),
                    "eta_minutos": round(eta_minutos)
                }
            }
            self.cliente.publish(TOPICO_FMS_DADOS, json.dumps(pacote))
            time.sleep(2) # Atualiza a rede a cada 2 segundos

if __name__ == "__main__":
    fms = FlightManagementSystem()
    fms.iniciar()
