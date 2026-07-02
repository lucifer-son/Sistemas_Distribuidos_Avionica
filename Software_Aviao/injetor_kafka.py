import os
import time
from kafka import KafkaProducer

# --- Configuration ---
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:9092')

def create_kafka_producer():

    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: v.encode('utf-8')
            )
            print("Successfully connected to Kafka.")
            return producer
        except Exception as e:
            print(f"Failed to connect to Kafka: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def send_command(producer, motor_id, command):
    """Mandar um comando para um motor em especifico."""
    topic = f'avionica.commands.motor.{motor_id.lower()}'
    try:
        future = producer.send(topic, command)
        future.get(timeout=10)
        print(f"Successfully sent command '{command}' to motor {motor_id.upper()} on topic {topic}")
    except Exception as e:
        print(f"Error sending command to {topic}: {e}")

def display_menu():
    """ Exibe o menu principal e solicita a escolha do usuário."""
    print("\n--- Distributed Fault Injector ---")
    print("1. Corrupt Motor A")
    print("2. Corrupt Motor B")
    print("3. Corrupt Motor C")
    print("----------------------------------")
    print("4. Restore Motor A")
    print("5. Restore Motor B")
    print("6. Restore Motor C")
    print("----------------------------------")
    print("q. Quit")
    return input("Choose an option: ")

if __name__ == "__main__":
    kafka_producer = create_kafka_producer()

    while True:
        choice = display_menu()

        if choice == '1':
            send_command(kafka_producer, 'a', 'CORRUPT')
        elif choice == '2':
            send_command(kafka_producer, 'b', 'CORRUPT')
        elif choice == '3':
            send_command(kafka_producer, 'c', 'CORRUPT')
        elif choice == '4':
            send_command(kafka_producer, 'a', 'RESTORE')
        elif choice == '5':
            send_command(kafka_producer, 'b', 'RESTORE')
        elif choice == '6':
            send_command(kafka_producer, 'c', 'RESTORE')
        elif choice.lower() == 'q':
            print("Exiting...")
            break
        else:
            print("Invalid option. Please try again.")

        time.sleep(1) # Small delay before showing menu again
