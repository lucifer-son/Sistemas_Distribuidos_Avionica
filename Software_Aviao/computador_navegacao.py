import json
import os
import time
import random
import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
PORTA = int(os.getenv("MQTT_PORT", "1883"))
TOPICO_NAV = "avionica/navegacao"

def iniciar_navegacao():
    cliente = mqtt.Client()
    cliente.connect(BROKER, PORTA, 60)
    print("🧭 Computador de Navegação e Automação INICIADO.")
    print("A calcular rotas, proa e status do Piloto Automático...")
    print("-" * 50)

    waypoints = ["LISBOA_FIR", "WAYPOINT_ALFA", "ROTA_OCEANICA", "APROXIMACAO_FINAL"]

    try:
        while True:
            # Simulando os cálculos de navegação
            pacote = {
                "origem": "Computador_Nav",
                "dados": {
                    "proa_graus": random.randint(265, 275), # Voando para Oeste
                    "vs_fpm": random.randint(-150, 150),    # Razão de subida/descida (Pés por Minuto)
                    "piloto_automatico": "LIGADO (LNAV/VNAV)",
                    "waypoint_ativo": random.choice(waypoints),
                    "eta_minutos": random.randint(15, 120)
                }
            }
            cliente.publish(TOPICO_NAV, json.dumps(pacote))
            print(f"📍 Navegação | Proa: {pacote['dados']['proa_graus']}° | Rumo a: {pacote['dados']['waypoint_ativo']}")
            time.sleep(3) # Atualiza a cada 3 segundos
            
    except KeyboardInterrupt:
        print("\nNavegação Desligada.")
        cliente.disconnect()

if __name__ == "__main__":
    iniciar_navegacao()
