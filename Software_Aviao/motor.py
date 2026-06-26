import os
import time
import random
import json
import threading
try:
    from kafka import KafkaProducer, KafkaConsumer
    _kafka_import_error = None
except Exception as e:
    KafkaProducer = None
    KafkaConsumer = None
    _kafka_import_error = e

# --- Configuration ---
MOTOR_ID = os.getenv('MOTOR_ID', 'A').lower()
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:9092')
TELEMETRY_TOPIC = f'avionica.telemetry.motor.{MOTOR_ID}'
COMMAND_TOPIC = f'avionica.commands.motor.{MOTOR_ID}'

# --- State ---
is_corrupted = False

def create_kafka_producer():

    if KafkaProducer is None:
        print(f"Warning: kafka-python not available ({_kafka_import_error}). Running in local/dry-run mode (no real Kafka).")

        class DummyFuture:
            def __init__(self, topic):
                self._topic = topic

            def get(self, timeout=None):
                class Meta:
                    topic = self._topic

                return Meta

        class DummyProducer:
            def send(self, topic, value):
                print(f"[DRY-RUN] Would send to {topic}: {value}")
                return DummyFuture(topic)

            def flush(self):
                pass

            def close(self):
                pass

        return DummyProducer()
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("Conexão com o Kafka estabelecida com sucesso como produtor.")
            return producer
        except Exception as e:
            print(f"Falha ao conectar-se ao Kafka como produtor: {e}. Retrying in 5 seconds...")
            time.sleep(5)


def _safe_deserialize(v: bytes):

    try:
        s = v.decode('utf-8')
    except Exception:
        return v
    try:
        return json.loads(s)
    except Exception:
        return s


def create_kafka_consumer():

    if KafkaConsumer is None:
        class DummyConsumer:
            def subscribe(self, topics):
                print(f"[DRY-RUN] Nenhum consumidor Kafka disponivel: {topics}")

            def __iter__(self):
                return iter(())

            def close(self):
                pass

        return DummyConsumer()

    while True:
        try:
            consumer = KafkaConsumer(
                bootstrap_servers=KAFKA_BROKER,
                auto_offset_reset='latest',
                group_id=f'motor-{MOTOR_ID}-commands',
                value_deserializer=_safe_deserialize,
                consumer_timeout_ms=1000,
            )
            print(f"Successfully connected to Kafka as a Consumer (commands) on {KAFKA_BROKER}.")
            return consumer
        except Exception as e:
            print(f"Failed to connect to Kafka as Consumer: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def command_listener():

    global is_corrupted

    consumer = create_kafka_consumer()
    consumer.subscribe([COMMAND_TOPIC])
    try:
        for message in consumer:

            raw = message.value
            command = str(raw).strip().upper()
            if command == 'CORRUPT':
                is_corrupted = True
                print(f"!!! Motor {MOTOR_ID.upper()} received CORRUPT command. Simulating failure. !!!")
            elif command == 'RESTORE':
                is_corrupted = False
                print(f"!!! Motor {MOTOR_ID.upper()} received RESTORE command. Restoring normal operation. !!!")
    except Exception as e:
        print(f"Error while listening for commands on {COMMAND_TOPIC}: {e}")
    finally:
        try:
            consumer.close()
        except Exception:
            pass


def simulate_and_publish(producer):

    global is_corrupted

    if is_corrupted:

        telemetry_data = {
            'rpm': round(random.uniform(9000, 12000), 2),
            'temperature': 9999.99,
            'pressure': round(random.uniform(500, 1000), 2),
            'timestamp': time.time(),
            'status': 'FAILURE'
        }
    else:
        # Simulação normal de telemetria
        telemetry_data = {
            'rpm': round(random.uniform(1000, 1500), 2),
            'temperature': round(random.uniform(80, 100), 2),
            'pressure': round(random.uniform(30, 40), 2),
            'timestamp': time.time(),
            'status': 'OK'
        }

    try:
        future = producer.send(TELEMETRY_TOPIC, telemetry_data)
        record_metadata = future.get(timeout=10)
        status_icon = "🔥" if is_corrupted else "✅"
        print(f"{status_icon} Motor {MOTOR_ID.upper()} | Sent to {record_metadata.topic}: {telemetry_data}")
    except Exception as e:
        print(f"Error sending message to Kafka: {e}")

if __name__ == "__main__":
    print(f"--- Motor Simulation: {MOTOR_ID.upper()} ---")
    print(f"Kafka Broker: {KAFKA_BROKER}")
    print(f"Telemetry Topic: {TELEMETRY_TOPIC}")
    print(f"Command Topic: {COMMAND_TOPIC}")
    print("------------------------------------")
    # Iniciar o ouvinte de comandos em uma thread separada.
    listener_thread = threading.Thread(target=command_listener, daemon=True)
    listener_thread.start()

    kafka_producer = create_kafka_producer()

    try:
        while True:
            simulate_and_publish(kafka_producer)
            time.sleep(5)
    except KeyboardInterrupt:
        print("Shutting down motor simulator...")
    finally:
        try:
            kafka_producer.flush()
            kafka_producer.close()
        except Exception:
            pass

