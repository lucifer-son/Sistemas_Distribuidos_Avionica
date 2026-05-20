import json
import customtkinter as ctk
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORTA = 1883
TOPICO_FALHAS_GERAIS = "avionica/comandos/falhas"
TOPICO_FALHA_B = "avionica/comandos/falhas/sensor_B" # Alvo específico!

class PainelInstrutor(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("⚡ IOS - Painel do Instrutor")
        self.geometry("400x350")
        ctk.set_appearance_mode("dark")

        self.cliente = mqtt.Client()
        self.cliente.connect(BROKER, PORTA, 60)
        self.cliente.loop_start()

        ctk.CTkLabel(self, text="INJEÇÃO DE FALHAS", font=("Arial", 20, "bold"), text_color="red").pack(pady=15)

        # Novo Botão de Falha Bizantina
        btn_bizantino = ctk.CTkButton(self, text="😈 Corromper Apenas Sensor B (Bizantino)", fg_color="#800080", hover_color="#4B0082", height=40, command=self.falha_bizantina)
        btn_bizantino.pack(pady=5)

        btn_motor = ctk.CTkButton(self, text="💥 Explodir Todos os Motores", fg_color="#8B0000", hover_color="#FF0000", height=40, command=self.falhar_motor)
        btn_motor.pack(pady=10)

        btn_tcas = ctk.CTkButton(self, text="✈️ Simular Tráfego (TCAS)", fg_color="#B8860B", hover_color="#DAA520", height=40, command=self.simular_trafego)
        btn_tcas.pack(pady=10)

        btn_pullup = ctk.CTkButton(self, text="⛰️ Simular Montanha (EGPWS)", fg_color="#FF4500", hover_color="#FF6347", height=40, command=self.simular_queda)
        btn_pullup.pack(pady=10)

    def falha_bizantina(self):
        self.cliente.publish(TOPICO_FALHA_B, "sabotar")
        print("SABOTAGEM: 😈 Sensor B foi corrompido! Verifique o nó de Consenso.")

    def falhar_motor(self):
        self.cliente.publish(TOPICO_FALHAS_GERAIS, json.dumps({"tipo": "motor"}))
        print("SABOTAGEM: 💥 Falha catastrófica geral enviada!")

    def simular_trafego(self):
        self.cliente.publish(TOPICO_FALHAS_GERAIS, json.dumps({"tipo": "trafego"}))
        print("SABOTAGEM: ✈️ Comando de Tráfego (TCAS) enviado!")

    def simular_queda(self):
        self.cliente.publish(TOPICO_FALHAS_GERAIS, json.dumps({"tipo": "queda"}))
        print("SABOTAGEM: ⛰️ Comando de Montanha (EGPWS) enviado!")

if __name__ == "__main__":
    app = PainelInstrutor()
    app.mainloop()
