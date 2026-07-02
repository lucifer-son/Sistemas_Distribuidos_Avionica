import json
import time
import threading
import sqlite3
from kafka import KafkaConsumer, KafkaProducer

# Configurações Kafka
KAFKA_BROKER = 'localhost:9092'
TOPIC_HEALTH = 'avionica.module.health'
TOPIC_ALERTS = 'avionica.alerts.generated'

# Thresholds de Tempo
TIMEOUT_SEGUNDOS = 15

class DetectorDeFalhas:
    def __init__(self):
        # Tabela em memória com timestamp do último ping
        self.modulos_ativos = {}
        # Impede múltiplos alertas para o mesmo módulo já caído
        self.modulos_down = set()
        self.lock = threading.Lock()
        
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        self.inicializar_banco_dados()

    def inicializar_banco_dados(self):
        """Inicializa um banco SQLite para persistir o status (module_status)."""
        self.conn = sqlite3.connect('avionica_status.db', check_same_thread=False)
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS module_status (
                modulo TEXT PRIMARY KEY,
                callsign TEXT,
                status TEXT,
                ultimo_visto REAL
            )
        ''')
        self.conn.commit()

    def atualizar_banco(self, modulo, callsign, status, timestamp):
        """Atualiza a tabela de status no banco de dados."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO module_status (modulo, callsign, status, ultimo_visto)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(modulo) DO UPDATE SET
            status=excluded.status, ultimo_visto=excluded.ultimo_visto
        ''', (modulo, callsign, status, timestamp))
        self.conn.commit()

    def consumir_heartbeats(self):
        """Escuta pings continuamente e atualiza a tabela em memória."""
        consumer = KafkaConsumer(
            TOPIC_HEALTH,
            bootstrap_servers=KAFKA_BROKER,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        print("[HEALTH] Monitoramento de Heartbeats Iniciado...")
        for message in consumer:
            payload = message.value
            modulo = payload.get('modulo')
            callsign = payload.get('callsign', 'UNKNOWN')
            
            with self.lock:
                self.modulos_ativos[modulo] = {
                    "timestamp": time.time(),
                    "callsign": callsign
                }
                
                # Se o módulo estava DOWN e voltou a responder, atualizamos o status
                if modulo in self.modulos_down:
                    self.modulos_down.remove(modulo)
                    self.atualizar_banco(modulo, callsign, "UP", time.time())
                    print(f"[RECOVERY] Módulo {modulo} ({callsign}) voltou a responder.")

    def verificar_timeouts(self):
        """Thread que varre a tabela em memória a cada 1 segundo procurando timeouts."""
        while True:
            time.sleep(1)
            agora = time.time()
            
            with self.lock:
                for modulo, dados in list(self.modulos_ativos.items()):
                    if modulo in self.modulos_down:
                        continue # Já está marcado como caído
                        
                    tempo_sem_ping = agora - dados['timestamp']
                    
                    if tempo_sem_ping > TIMEOUT_SEGUNDOS:
                        callsign = dados['callsign']
                        self.modulos_down.add(modulo)
                        
                        # 1. Altera o status no banco de dados
                        self.atualizar_banco(modulo, callsign, "DOWN", dados['timestamp'])
                        
                        # 2. Gera o alerta crítico
                        alerta = {
                            "tipo": "FALHA_CONEXAO",
                            "descricao": f"Modulo '{modulo}' ({callsign}) offline. Sem heartbeats há > {TIMEOUT_SEGUNDOS}s",
                            "severidade": "CRITICAL",
                            "timestamp": agora
                        }
                        self.producer.send(TOPIC_ALERTS, alerta)
                        print(f"\n[CRÍTICO] {alerta['descricao']}")

    def iniciar(self):
        # Inicia a thread responsável por verificar quem "morreu"
        t_checker = threading.Thread(target=self.verificar_timeouts, daemon=True)
        t_checker.start()
        
        # Inicia o consumo na thread principal
        try:
            self.consumir_heartbeats()
        except KeyboardInterrupt:
            print("[SHUTDOWN] Desligando detector de falhas.")
            self.conn.close()

if __name__ == "__main__":
    detector = DetectorDeFalhas()
    detector.iniciar()