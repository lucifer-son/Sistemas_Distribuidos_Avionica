import os
import csv
import json
import paho.mqtt.client as mqtt
from datetime import datetime

BROKER = "broker.hivemq.com"
PORTA = 1883

# O '#' significa "Ouve todas as sub-camadas dentro de avionica/"
TOPICO_TUDO = "avionica/#" 
ARQUIVO_LOG = "flight_data_recorder.csv"

def ao_conectar(client, userdata, flags, rc):
    print("🖭️ FDR (Caixa Preta) ONLINE. A gravar todos os dados do voo...")
    client.subscribe(TOPICO_TUDO)
    
    # Cria o cabeçalho do ficheiro CSV se ele ainda não existir
    if not os.path.exists(ARQUIVO_LOG):
        with open(ARQUIVO_LOG, mode='w', newline='') as file:
            writer = csv.writer(file, delimiter=';') # Usamos ';' para o Excel poder ler melhor
            writer.writerow(["Timestamp", "Topico", "Dados_JSON"])

def ao_receber_mensagem(client, userdata, msg):
    # Captura a hora exata ao milissegundo
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    topico = msg.topic
    
    try:
        # Tenta descodificar a mensagem
        payload = msg.payload.decode()
    except:
        payload = "[DADOS BINÁRIOS]"
    
    # Abre o ficheiro e adiciona a nova linha no fim (modo 'a' de append)
    with open(ARQUIVO_LOG, mode='a', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow([timestamp, topico, payload])
    
    # Opcional: Imprime na tela um resumo para sabermos que está gravando
    print(f"[{timestamp}] 💾 GRAVADO <- {topico}")

if __name__ == "__main__":
    cliente = mqtt.Client()
    cliente.on_connect = ao_conectar
    cliente.on_message = ao_receber_mensagem
    
    print("⏳ A iniciar gravador de voo...")
    cliente.connect(BROKER, PORTA, 60)
    cliente.loop_forever() # Fica gravando até fecharmos o programa (ou apertar Ctrl+C)

        # O resultado final será um ficheiro CSV com todas as mensagens recebidas, incluindo o timestamp e o tópico correspondente.
        # Para criar dados limpos para um novo voo, basta apagar o ficheiro "flight_data_recorder.csv" antes de iniciar a gravação.
