import os
import time

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

from kafka_topics import KAFKA_TOPICS

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")


def create_topics():
    admin = KafkaAdminClient(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        client_id="avionica-topic-admin"
    )

    topics = [
        NewTopic(name=topic, num_partitions=1, replication_factor=1)
        for topic in KAFKA_TOPICS
    ]

    try:
        admin.create_topics(new_topics=topics, validate_only=False)
        print(f"[kafka-create-topics] topicos criados: {KAFKA_TOPICS}")
    except TopicAlreadyExistsError:
        print("[kafka-create-topics] alguns topicos ja existem")
    finally:
        admin.close()


if __name__ == "__main__":
    while True:
        try:
            create_topics()
            break
        except Exception as erro:
            print("[kafka-create-topics] Kafka ainda nao esta pronto. Tentando em 5s")
            time.sleep(5)