import socket
import json
import time
import random

IP_DESTINO = '127.0.0.1'
PORTA_DESTINO = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print("⚙️ Sensor de Freio (Cabo) INICIADO. A enviar dados...")

try:
    while True:
        # Simula a leitura física da pressão dos freios
        pressao_atual = random.uniform(40.0, 100.0)
        
        pacote = {
            "origem": "Sensor_Freio",
            "timestamp": time.time(),
            "dados": {
                "pressao": round(pressao_atual, 2),
                "unidade": "psi"
            }
        }
        
        # Converte para JSON e envia
        mensagem = json.dumps(pacote).encode('utf-8')
        sock.sendto(mensagem, (IP_DESTINO, PORTA_DESTINO))
        
        print(f"Enviado: {pacote['dados']['pressao']} psi")
        time.sleep(2) # Envia a cada 2 segundos
        
except KeyboardInterrupt:
    sock.close()