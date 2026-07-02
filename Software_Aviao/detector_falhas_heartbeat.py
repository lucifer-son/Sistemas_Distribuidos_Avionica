import json
import os
import time
import threading
import psycopg2
from datetime import datetime, timezone
from kafka import KafkaConsumer, KafkaProducer

# ── Configuração ──────────────────────────────────────────────
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
DB_HOST      = os.getenv("DB_HOST", "postgres")
DB_PORT      = int(os.getenv("DB_PORT", "5432"))
DB_NAME      = os.getenv("DB_NAME", "avionica")
DB_USER      = os.getenv("DB_USER", "avionica")
DB_PASS      = os.getenv("DB_PASS", "avionica_dev")

TOPIC_HEALTH      = "avionica.module.health"
TOPIC_EVENTS      = "avionica.system.events"
TOPIC_ALERTS      = "avionica.alerts.generated"

TIMEOUT_SECONDS   = 15  # Módulo offline se > 15s sem heartbeat
CHECK_INTERVAL    = 2   # Intervalo de verificação (segundos)

# ── Mapeamento de nomes ──────────────────────────────────────
MODULE_NAME_MAP = {
    "FlightComputer_Node1": "Computador_Primario",
    "FlightComputer_Node2": "Computador_Secundario",
    "Computador_Primario":  "Computador_Primario",
    "Computador_Secundario": "Computador_Secundario",
    "computador_primario":  "Computador_Primario",
    "computador_secundario": "Computador_Secundario",
    "SensoresVoo":          "Sensores_Voo",
    "RadarClimaticoA":      "Radar_Externo",
    "ComputadorNavegacao":  "Computador_Navegacao",
    "LiderWAIC":            "Lider_WAIC",
    "VoterTMR":             "Voter_TMR",
    "FMS":                  "FMS_Distribuido",
}

# ── Estado em memória ─────────────────────────────────────────
last_heartbeat = {}   # {modulo: timestamp}
module_status  = {}   # {modulo: "UP" | "DOWN"}
lock = threading.Lock()


# ── Funções de banco de dados ─────────────────────────────────

def get_db_connection():
    """Cria uma conexão com o PostgreSQL."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )


def update_module_status_db(modulo, status):
    """Atualiza ou insere o status de um módulo no banco de dados."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO module_status (modulo, status, ultima_atualizacao)
            VALUES (%s, %s, NOW())
            ON CONFLICT (modulo) DO UPDATE
            SET status = EXCLUDED.status,
                ultima_atualizacao = NOW()
        """, (modulo, status))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[Heartbeat-Detector] ❌ Erro ao atualizar banco: {e}", flush=True)


def insert_alert_db(tipo, descricao, severidade, origem):
    """Insere um alerta na tabela alertas do PostgreSQL."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO alertas (tipo, descricao, severidade, origem, resolvido)
            VALUES (%s, %s, %s, %s, FALSE)
        """, (tipo, descricao, severidade, origem))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[Heartbeat-Detector] ❌ Erro ao inserir alerta: {e}", flush=True)


# ── Thread: Consumidor Kafka de Heartbeats ────────────────────

def consumer_loop():
    """Escuta heartbeats no tópico avionica.module.health."""
    print("[Heartbeat-Detector] Conectando ao Kafka...", flush=True)

    while True:
        try:
            consumer = KafkaConsumer(
                TOPIC_HEALTH,
                bootstrap_servers=KAFKA_BROKER,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="latest",
                group_id="heartbeat-detector-group",
                consumer_timeout_ms=-1,
            )
            print(f"[Heartbeat-Detector] Inscrito no tópico: {TOPIC_HEALTH}", flush=True)
            break
        except Exception as e:
            print(f"[Heartbeat-Detector] Kafka indisponível ({e}). Retry em 5s...", flush=True)
            time.sleep(5)

    for msg in consumer:
        payload = msg.value
        
        modulo_raw = payload.get("modulo") or payload.get("module") or payload.get("node_id")
        if modulo_raw is None:
            continue
        
        modulo_raw = str(modulo_raw)
        
        if modulo_raw == "1":
            modulo_raw = "FlightComputer_Node1"
        elif modulo_raw == "2":
            modulo_raw = "FlightComputer_Node2"
        
        modulo = MODULE_NAME_MAP.get(modulo_raw, modulo_raw)
        
        now = time.time()
        
        with lock:
            last_heartbeat[modulo] = now
            
            prev_status = module_status.get(modulo)
            if prev_status == "DOWN" or prev_status is None:
                module_status[modulo] = "UP"
                update_module_status_db(modulo, "UP")
                if prev_status == "DOWN":
                    print(f"[Heartbeat-Detector] 🟢 Módulo {modulo} RECUPERADO (voltou UP)", flush=True)
                else:
                    print(f"[Heartbeat-Detector] 🟢 Módulo {modulo} registrado (UP)", flush=True)


# ── Thread: Verificador de Timeout ────────────────────────────

def checker_loop():
    """Verifica a cada CHECK_INTERVAL segundos se algum módulo expirou."""
    print("[Heartbeat-Detector] Iniciando verificador de timeout...", flush=True)

    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            print("[Heartbeat-Detector] Producer Kafka pronto para alertas.", flush=True)
            break
        except Exception as e:
            print(f"[Heartbeat-Detector] Kafka producer indisponível ({e}). Retry em 5s...", flush=True)
            time.sleep(5)

    while True:
        time.sleep(CHECK_INTERVAL)
        now = time.time()

        with lock:
            for modulo, last_ts in list(last_heartbeat.items()):
                elapsed = now - last_ts
                current_status = module_status.get(modulo, "UP")

                if elapsed > TIMEOUT_SECONDS and current_status != "DOWN":
                    module_status[modulo] = "DOWN"
                    
                    print(f"[Heartbeat-Detector] 🔴 TIMEOUT: Módulo {modulo} offline "
                          f"(último heartbeat há {elapsed:.1f}s)", flush=True)

                    update_module_status_db(modulo, "DOWN")
                    desc = f"Modulo {modulo} ficou offline (Heartbeat Timeout > {TIMEOUT_SECONDS}s)"
                    insert_alert_db("FALHA_CONEXAO", desc, "CRITICAL", "heartbeat-detector")

                    alerta_evento = {
                        "tipo": "FALHA_CONEXAO",
                        "descricao": desc,
                        "severidade": "CRITICAL",
                        "origem": "heartbeat-detector",
                        "modulo": modulo,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    producer.send(TOPIC_EVENTS, alerta_evento)
                    producer.send(TOPIC_ALERTS, alerta_evento)
                    producer.flush()


# ── Main ──────────────────────────────────────────────────────

def main():
    print("=" * 60, flush=True)
    print("  💓  Detector de Falhas — Heartbeat Monitor", flush=True)
    print("=" * 60, flush=True)

    # Aguardar banco de dados
    print("[Heartbeat-Detector] Aguardando PostgreSQL...", flush=True)
    while True:
        try:
            conn = get_db_connection()
            conn.close()
            print("[Heartbeat-Detector] PostgreSQL conectado!", flush=True)
            break
        except Exception as e:
            print(f"[Heartbeat-Detector] DB indisponível ({e}). Retry em 3s...", flush=True)
            time.sleep(3)

    # Inicializar status dos módulos pré-cadastrados no banco
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT modulo, status FROM module_status")
        for row in cur.fetchall():
            modulo, status = row
            module_status[modulo] = status
            last_heartbeat[modulo] = time.time()
            print(f"[Heartbeat-Detector] Carregado do banco: {modulo} = {status}", flush=True)
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[Heartbeat-Detector] ⚠️ Erro ao carregar status inicial: {e}", flush=True)

    t_consumer = threading.Thread(target=consumer_loop, daemon=True)
    t_checker  = threading.Thread(target=checker_loop, daemon=True)

    t_consumer.start()
    t_checker.start()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("[Heartbeat-Detector] Encerrando...", flush=True)


if __name__ == "__main__":
    main()
