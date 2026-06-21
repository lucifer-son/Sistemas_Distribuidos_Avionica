import json
import os
import time
from kafka import KafkaConsumer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

TOPICS = [
    "avionica.telemetry.flight",
    "avionica.telemetry.brakes",
    "avionica.telemetry.radar",
    "avionica.route.calculated",
    "avionica.navigation",
    "avionica.telemetry.waic",
    "avionica.automation.anti_ice",
    "avionica.system.events",
    "avionica.mutex.brakes.request",
    "avionica.mutex.brakes.grant",
    "avionica.mutex.brakes.release",
]

def main():
    while True:
        try:
            consumer = KafkaConsumer(
                *TOPICS,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_deserializer=lambda value: json.loads(value.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                group_id="kafka-telemetry-debug"
            )
            break
        except Exception as erro:
            print("[kafka-telemetry-consumer] Kafka ainda nao esta pronto. Tentando em 5s")
            time.sleep(5)

    print("[kafka-telemetry-consumer] aguardando mensagens")
    print(f"[kafka-telemetry-consumer] Kafka={KAFKA_BOOTSTRAP}")

    for record in consumer:
        print(
            "[kafka-telemetry-consumer] "
            f"topic={record.topic} "
            f"partition={record.partition} "
            f"offset={record.offset} "
            f"value={record.value}"
        )

if __name__ == "__main__":
    main()
