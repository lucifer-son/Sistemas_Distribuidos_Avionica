import json
import os
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from kafka import KafkaProducer

from kafka_topics import MQTT_TO_KAFKA

MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt-broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC_FILTER = os.getenv("MQTT_TOPIC_FILTER", "avionica/#")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")


def create_producer():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_serializer=lambda value: json.dumps(value).encode("utf-8"),
                key_serializer=lambda value: value.encode("utf-8") if value else None,
                acks="all",
                retries=3,
            )
            print(f"[mqtt-kafka-bridge] conectado ao Kafka em {KAFKA_BOOTSTRAP}")
            return producer
        except Exception as erro:
            print("[mqtt-kafka-bridge] Kafka ainda nao esta pronto. Tentando em 5s")
            time.sleep(5)


producer = create_producer()


def parse_payload(raw_payload):
    try:
        return json.loads(raw_payload.decode("utf-8"))
    except Exception:
        return {"raw": raw_payload.decode("utf-8", errors="replace")}


def build_kafka_message(mqtt_topic, payload, event_type):
    return {
        "source": "mqtt-kafka-bridge",
        "originalTopic": mqtt_topic,
        "type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }


def on_connect(client, userdata, flags, rc):
    print(f"[mqtt-kafka-bridge] conectado ao MQTT rc={rc}")
    client.subscribe(MQTT_TOPIC_FILTER)
    print(f"[mqtt-kafka-bridge] assinando {MQTT_TOPIC_FILTER}")


def on_message(client, userdata, msg):
    mapping = MQTT_TO_KAFKA.get(msg.topic)

    if not mapping:
        print(f"[mqtt-kafka-bridge] ignorado topico sem mapeamento: {msg.topic}")
        return

    payload = parse_payload(msg.payload)
    kafka_topic = mapping["topic"]
    event_type = mapping["type"]
    kafka_message = build_kafka_message(msg.topic, payload, event_type)

    producer.send(kafka_topic, key=msg.topic, value=kafka_message)
    producer.flush()

    print(f"[mqtt-kafka-bridge] {msg.topic} -> {kafka_topic}: {kafka_message}")


def main():
    print("[mqtt-kafka-bridge] iniciando")
    print(f"[mqtt-kafka-bridge] MQTT={MQTT_BROKER}:{MQTT_PORT}")
    print(f"[mqtt-kafka-bridge] Kafka={KAFKA_BOOTSTRAP}")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            client.loop_forever()
        except Exception as error:
            print(f"[mqtt-kafka-bridge] erro: {error}. Tentando novamente em 5s")
            time.sleep(5)


if __name__ == "__main__":
    main()
