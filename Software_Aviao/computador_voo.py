import socket
import json

# Configuração do Servidor (Computador de Voo)
IP = '127.0.0.1' # Localhost (o seu próprio computador)
PORTA = 5000

# Criação do Socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((IP, PORTA))

print(f"✈️ Computador de Voo INICIADO. A escutar na porta {PORTA}...")
print("-" * 50)

try:
    while True:
        # Fica à espera de receber dados
        dados_brutos, endereco_origem = sock.recvfrom(1024) 
        
        # Descodifica o pacote JSON recebido
        mensagem = json.loads(dados_brutos.decode('utf-8'))
        
        origem = mensagem.get('origem', 'Desconhecido')
        dados = mensagem.get('dados', {})
        
        print(f"📥 Recebido de [{origem}] via {endereco_origem}:")
        print(f"   ↳ Dados: {dados}")
        
        # Lógica simples de alerta
        if origem == "Sensor_Freio" and dados.get('pressao', 0) < 50:
            print("   ⚠️ ALERTA CRÍTICO: Pressão dos freios demasiado baixa!")
        print("-" * 50)
            
except KeyboardInterrupt:
    print("\nComputador de Voo desligado.")
    sock.close()