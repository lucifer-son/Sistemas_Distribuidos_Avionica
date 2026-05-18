import socket
import json
import time
import random

IP_DESTINO = '127.0.0.1'
PORTA_DESTINO = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print("📡 Líder do Cluster WAIC INICIADO. A agregar dados...")

try:
    while True:
        # O Líder "finge" que leu dois sensores sem fio e junta tudo num só pacote
        pacote_agregado = {
            "origem": "Lider_WAIC_Agregador",
            "timestamp": time.time(),
            "dados": {
                "sensor_pressao_motor": round(random.uniform(200.0, 250.0), 2),
                "sensor_temperatura": round(random.uniform(80.0, 110.0), 2)
            }
        }
        
        mensagem = json.dumps(pacote_agregado).encode('utf-8')
        sock.sendto(mensagem, (IP_DESTINO, PORTA_DESTINO))
        
        print(f"Pacote Agregado Enviado: Motor={pacote_agregado['dados']['sensor_pressao_motor']}, Temp={pacote_agregado['dados']['sensor_temperatura']}")
        time.sleep(3) # Envia a cada 3 segundos
        
except KeyboardInterrupt:
    sock.close()