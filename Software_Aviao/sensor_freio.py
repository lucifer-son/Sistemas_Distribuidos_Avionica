"""
sensor_freio.py — Sensor de Freios com Exclusão Mútua Distribuída
Algoritmo: Ricart-Agrawala
Responsável: Nickolas / Nickollas
"""

import json
import os
import random
import threading
import time
import uuid
from datetime import datetime, timezone

from kafka import KafkaConsumer, KafkaProducer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
NODE_ID = int(os.getenv("BRAKE_NODE_ID", "1"))
MUTEX_PEERS = [
    int(item.strip())
    for item in os.getenv("MUTEX_PEERS", "2,3").split(",")
    if item.strip()
]

TOPICO_REQUEST = os.getenv("BRAKE_MUTEX_REQUEST_TOPIC", "avionica.mutex.brakes.request")
TOPICO_GRANT = os.getenv("BRAKE_MUTEX_GRANT_TOPIC", "avionica.mutex.brakes.grant")
TOPICO_RELEASE = os.getenv("BRAKE_MUTEX_RELEASE_TOPIC", "avionica.mutex.brakes.release")
TOPICO_TELEMETRIA = os.getenv("BRAKE_TELEMETRY_TOPIC", "avionica.telemetry.brakes")

RESOURCE_NAME = "brakes_hydraulic_actuator"
GRANT_TIMEOUT_SECONDS = float(os.getenv("RICART_GRANT_TIMEOUT_SECONDS", "8"))
INTERVAL_SECONDS = float(os.getenv("BRAKE_INTERVAL_SECONDS", "3"))

clock_lock = threading.Lock()
state_lock = threading.Lock()
logical_clock = 0
estado = "LIVRE"  # LIVRE | QUERER | NA_SECAO
meu_timestamp = 0
request_id_atual = None
grants_recebidos = set()
fila_pendente = []
running = True
producer = None


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def criar_producer():
    while True:
        try:
            kafka_producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_serializer=lambda value: json.dumps(value).encode("utf-8"),
                key_serializer=lambda value: str(value).encode("utf-8") if value is not None else None,
                acks="all",
                retries=3,
            )
            print(f"[freios] conectado ao Kafka em {KAFKA_BOOTSTRAP}")
            return kafka_producer
        except Exception as erro:
            print("[freios] Kafka ainda nao esta pronto. Tentando em 5s")
            time.sleep(5)


def criar_consumer():
    while True:
        try:
            return KafkaConsumer(
                TOPICO_REQUEST,
                TOPICO_GRANT,
                TOPICO_RELEASE,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_deserializer=lambda value: json.loads(value.decode("utf-8")),
                auto_offset_reset="latest",
                enable_auto_commit=True,
                group_id=f"brake-sensor-{NODE_ID}-{uuid.uuid4()}",
            )
        except Exception as erro:
            print("[freios] Kafka ainda nao esta pronto para consumer. Tentando em 5s")
            time.sleep(5)


def tick():
    global logical_clock
    with clock_lock:
        logical_clock += 1
        return logical_clock


def atualizar_clock(clock_recebido):
    global logical_clock
    with clock_lock:
        logical_clock = max(logical_clock, int(clock_recebido or 0)) + 1
        return logical_clock


def minha_requisicao_tem_prioridade(clock_outro, node_outro):
    return (meu_timestamp, NODE_ID) < (int(clock_outro), int(node_outro))


def publicar(topico, payload, key=None):
    producer.send(topico, key=key, value=payload)
    producer.flush()


def enviar_grant(para_node_id, request_id):
    clock_value = tick()
    publicar(TOPICO_GRANT, {
        "type": "GRANT",
        "resource": RESOURCE_NAME,
        "para_node_id": para_node_id,
        "de_node_id": NODE_ID,
        "request_id": request_id,
        "logical_clock": clock_value,
        "timestamp": utc_now(),
    }, key=para_node_id)
    print(f"[freios][RA] GRANT enviado para nó {para_node_id} | clock={clock_value}")


def responder_pendentes():
    global fila_pendente
    with state_lock:
        pendentes = list(fila_pendente)
        fila_pendente = []

    for item in pendentes:
        enviar_grant(item["node_id"], item["request_id"])


def tratar_request(payload):
    if payload.get("resource") != RESOURCE_NAME:
        return

    node_outro = payload.get("node_id")
    if node_outro is None or int(node_outro) == NODE_ID:
        return

    clock_outro = int(payload.get("logical_clock", 0))
    request_id = payload.get("request_id")
    atualizar_clock(clock_outro)

    with state_lock:
        devo_adiar = estado == "NA_SECAO" or (
            estado == "QUERER" and minha_requisicao_tem_prioridade(clock_outro, node_outro)
        )

        if devo_adiar:
            fila_pendente.append({"node_id": int(node_outro), "request_id": request_id})
            print(f"[freios][RA] REQUEST do nó {node_outro} adiado")
            return

    enviar_grant(int(node_outro), request_id)


def tratar_grant(payload):
    if payload.get("resource") != RESOURCE_NAME:
        return

    if int(payload.get("para_node_id", -1)) != NODE_ID:
        return

    atualizar_clock(payload.get("logical_clock", 0))
    de_node_id = int(payload.get("de_node_id"))
    request_id = payload.get("request_id")

    with state_lock:
        if estado == "QUERER" and request_id == request_id_atual and de_node_id in MUTEX_PEERS:
            grants_recebidos.add(de_node_id)
            print(f"[freios][RA] GRANT recebido do nó {de_node_id} ({len(grants_recebidos)}/{len(MUTEX_PEERS)})")


def tratar_release(payload):
    if payload.get("resource") == RESOURCE_NAME:
        atualizar_clock(payload.get("logical_clock", 0))


def loop_consumidor():
    consumer = criar_consumer()
    print(f"[freios][RA] escutando {TOPICO_REQUEST}, {TOPICO_GRANT} e {TOPICO_RELEASE}")

    for record in consumer:
        if not running:
            break

        payload = record.value
        if record.topic == TOPICO_REQUEST:
            tratar_request(payload)
        elif record.topic == TOPICO_GRANT:
            tratar_grant(payload)
        elif record.topic == TOPICO_RELEASE:
            tratar_release(payload)


def solicitar_lock():
    global estado, meu_timestamp, request_id_atual, grants_recebidos

    request_id = str(uuid.uuid4())
    clock_value = tick()

    with state_lock:
        estado = "QUERER"
        meu_timestamp = clock_value
        request_id_atual = request_id
        grants_recebidos = set()

    publicar(TOPICO_REQUEST, {
        "type": "REQUEST",
        "resource": RESOURCE_NAME,
        "node_id": NODE_ID,
        "request_id": request_id,
        "logical_clock": clock_value,
        "timestamp": utc_now(),
        "peers": MUTEX_PEERS,
    }, key=NODE_ID)

    print(f"[freios][RA] REQUEST enviado | nó={NODE_ID} | clock={clock_value} | aguardando={MUTEX_PEERS}")

    if not MUTEX_PEERS:
        with state_lock:
            estado = "NA_SECAO"
        return True

    deadline = time.time() + GRANT_TIMEOUT_SECONDS
    while time.time() < deadline:
        with state_lock:
            if set(MUTEX_PEERS).issubset(grants_recebidos):
                estado = "NA_SECAO"
                return True
        time.sleep(0.1)

    with state_lock:
        pendentes = sorted(set(MUTEX_PEERS) - grants_recebidos)
        estado = "LIVRE"

    print(f"[freios][RA] TIMEOUT aguardando GRANTs. Pendentes: {pendentes}")
    return False


def liberar_lock():
    global estado, request_id_atual, meu_timestamp, grants_recebidos

    clock_value = tick()
    publicar(TOPICO_RELEASE, {
        "type": "RELEASE",
        "resource": RESOURCE_NAME,
        "node_id": NODE_ID,
        "request_id": request_id_atual,
        "logical_clock": clock_value,
        "timestamp": utc_now(),
    }, key=NODE_ID)

    with state_lock:
        estado = "LIVRE"
        request_id_atual = None
        meu_timestamp = 0
        grants_recebidos = set()

    responder_pendentes()
    print(f"[freios][RA] Lock liberado | clock={clock_value}")


def acionar_freios():
    pressao_atual = round(random.uniform(45.0, 100.0), 1)
    id_unico = str(uuid.uuid4())
    clock_value = tick()

    pacote = {
        "id_mensagem": id_unico,
        "type": "TELEMETRY_BRAKE",
        "origem": f"SensorFreio_No{NODE_ID}",
        "module_id": f"sensor_freio_no_{NODE_ID}",
        "timestamp": utc_now(),
        "logical_clock": clock_value,
        "algoritmo_lock": "RICART_AGRAWALA",
        "dados": {
            "pressao": pressao_atual,
            "unidade": "psi",
            "node_id": NODE_ID,
            "estado_lock": "NA_SECAO",
        },
    }

    publicar(TOPICO_TELEMETRIA, pacote, key=NODE_ID)
    print(f"[freios] telemetria publicada em {TOPICO_TELEMETRIA} | pressão={pressao_atual} psi | clock={clock_value}")


def iniciar_sensor():
    global producer, running

    producer = criar_producer()
    threading.Thread(target=loop_consumidor, daemon=True).start()

    print(f"⚙️ Sensor de Freios iniciado | Node ID: {NODE_ID} | Peers: {MUTEX_PEERS}")
    print("-" * 60)

    try:
        while True:
            print(f"[freios] tentando acionar freios | estado={estado}")

            if solicitar_lock():
                try:
                    acionar_freios()
                finally:
                    liberar_lock()
            else:
                print("[freios] acionamento bloqueado: permissão distribuída incompleta")

            print("-" * 60)
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        running = False
        print("\n[freios] Sensor desligado.")
        if producer:
            producer.flush()
            producer.close()


if __name__ == "__main__":
    iniciar_sensor()
