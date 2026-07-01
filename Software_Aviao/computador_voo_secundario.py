import paho.mqtt.client as mqtt
import time
import threading
import json
import random
import os

# Configurações do Broker
BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))

# Tópicos MQTT
TOPIC_HEALTH = "avionica.module.health"
TOPIC_KEEPALIVE = "avionica.system.keepalive"
TOPIC_ELECTION = "avionica.system.election"
TOPIC_TELEMETRY = "avionica/navegacao"

class FlightComputerNode:
    def __init__(self, node_id=1):
        self.node_id = node_id
        self.is_leader = False
        self.leader_id = None
        self.last_heartbeat_time = time.time()
        self.election_in_progress = False
        
        # Identificação e configuração do Client MQTT
        self.client_id = f"FlightComputer_{self.node_id}"
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def start(self):
        print(f"[INIT] Iniciando Computador de Voo Secundário (Node ID: {self.node_id})")
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()

        # Inicia as threads de processamento e monitoramento em background
        threading.Thread(target=self.monitor_leader, daemon=True).start()
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        threading.Thread(target=self.telemetry_loop, daemon=True).start()

        # Assim que entra na rede, desafia os outros nós iniciando uma eleição
        time.sleep(1) # Aguarda a conexão se estabelecer
        self.start_election()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("[SHUTDOWN] Desligando computador de backup...")
            self.client.disconnect()

    def on_connect(self, client, userdata, flags, rc):
        print(f"[MQTT] Conectado ao broker com código de resultado {rc}")
        self.client.subscribe(TOPIC_KEEPALIVE)
        self.client.subscribe(TOPIC_ELECTION)

    def on_message(self, client, userdata, msg):
        payload = json.loads(msg.payload.decode('utf-8'))
        
        # 1. Tratamento de Heartbeat (Keep-Alive)
        if msg.topic == TOPIC_KEEPALIVE:
            sender_id = payload.get("node_id")
            if sender_id != self.node_id:
                self.last_heartbeat_time = time.time()
                self.leader_id = sender_id
                if self.is_leader and sender_id > self.node_id:
                    # Conflito de líderes: se o remetente tem ID maior, passo a passivo
                    print(f"[RECUO] Líder de prioridade superior ({sender_id}) detectado. Passando para Passivo.")
                    self.is_leader = False

        # 2. Tratamento de Mensagens de Eleição (Bully Algorithm)
        elif msg.topic == TOPIC_ELECTION:
            action = payload.get("action")
            sender_id = payload.get("node_id")

            if action == "ELECTION":
                # Se alguém com ID menor pediu eleição, respondemos ALIVE para calá-lo e iniciamos a nossa
                if sender_id < self.node_id:
                    print(f"[ELECTION] Nó {sender_id} pediu eleição. Respondendo com ALIVE (sou maior).")
                    self.publish_election("ALIVE")
                    self.start_election()
                
            elif action == "ALIVE":
                # Se recebemos ALIVE de um nó maior, perdemos a eleição e aguardamos o novo líder
                if sender_id > self.node_id:
                    print(f"[ELECTION] Nó maior ({sender_id}) está vivo. Abortando minha candidatura.")
                    self.election_in_progress = False

            elif action == "COORDINATOR":
                # Alguém venceu a eleição e se declarou líder
                if sender_id != self.node_id:
                    print(f"[ELECTION] Novo Líder eleito: Nó {sender_id}. Assumindo postura PASSIVA.")
                    self.leader_id = sender_id
                    self.is_leader = False
                    self.election_in_progress = False
                    self.last_heartbeat_time = time.time()

    def publish_election(self, action):
        msg = {"node_id": self.node_id, "action": action}
        self.client.publish(TOPIC_ELECTION, json.dumps(msg))

    def start_election(self):
        if self.election_in_progress: return
        
        self.election_in_progress = True
        self.is_leader = False
        print(f"[BULLY] Iniciando eleição... Desafiando outros nós.")
        self.publish_election("ELECTION")

        # Aguarda 2 segundos para ver se algum nó de ID maior responde com ALIVE
        time.sleep(2.0)

        if self.election_in_progress:
            # Se ninguém maior calou este nó, ele assume a liderança
            print(f"[BULLY] Ninguém com prioridade superior respondeu. Assumindo a liderança!")
            self.is_leader = True
            self.leader_id = self.node_id
            self.election_in_progress = False
            self.publish_election("COORDINATOR")

    def monitor_leader(self):
        """Secundário: Monitora se o Primário parou de enviar pings."""
        TIMEOUT = 6.0 # Segundos sem ping antes de considerar o líder morto
        while True:
            if not self.is_leader and not self.election_in_progress:
                if time.time() - self.last_heartbeat_time > TIMEOUT:
                    print("[FALHA] Timeout de Heartbeat! O Líder caiu. Iniciando Bully Algorithm.")
                    self.start_election()
            time.sleep(1)

    def heartbeat_loop(self):
        """Secundário/Ativo: Publica heartbeats a cada 3 segundos se for líder."""
        while True:
            if self.is_leader:
                health_msg = {"node_id": self.node_id, "status": "active", "timestamp": time.time()}
                self.client.publish(TOPIC_HEALTH, json.dumps(health_msg))
                self.client.publish(TOPIC_KEEPALIVE, json.dumps({"node_id": self.node_id}))
                print(f"[LÍDER-SECUNDÁRIO] Ping enviado para health e keep-alive (Node {self.node_id})")
            time.sleep(3)

    def telemetry_loop(self):
        """Líder: Processa dados de guiamento e publica em produção."""
        while True:
            if self.is_leader:
                # Simulação de cálculo de velocidade vertical e posicionamento
                vertical_speed = round(random.uniform(-5.0, 5.0), 2)
                altitude = round(random.uniform(10000, 10050), 2)
                
                telemetry = {
                    "source": f"FlightComputer_Node{self.node_id}",
                    "vertical_speed_fts": vertical_speed,
                    "target_altitude_ft": altitude,
                    "autopilot_engaged": True
                }
                
                self.client.publish(TOPIC_TELEMETRY, json.dumps(telemetry))
                print(f"[PRODUÇÃO-SECUNDÁRIO] Guiamento publicado: {telemetry}")
            
            time.sleep(1) # Frequência de atualização da navegação

if __name__ == "__main__":
    node = FlightComputerNode(node_id=1)
    node.start()
