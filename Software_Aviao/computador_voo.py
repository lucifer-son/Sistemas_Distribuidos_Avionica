import json
import customtkinter as ctk
import paho.mqtt.client as mqtt

# ==========================================
# CONFIGURAÇÕES DO MIDDLEWARE MQTT
# ==========================================
BROKER = "broker.hivemq.com"
PORTA = 1883

# Tópicos de Escuta (Sensores e Sistemas)
TOPICO_FREIOS = "avionica/sensores/freios"
TOPICO_WAIC = "avionica/sensores/waic"
TOPICO_VOO = "avionica/sensores/voo"
TOPICO_NAV = "avionica/navegacao"
TOPICO_RADAR = "avionica/radar"
TOPICO_FMS_DADOS = "avionica/fms/dados" # <-- Novo: Recebe dados da API

# Tópicos de Publicação (Comandos do Piloto)
TOPICO_CMD_VEL = "avionica/comandos/velocidade"
TOPICO_CMD_ROTA = "avionica/comandos/rota" # <-- Novo: Envia ICAO para o FMS

class GlassCockpit(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("✈️ Phenom 300 MFD - Glass Cockpit Distribuído")
        self.geometry("1100x750")
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#0A0A0A")
        
        self.mensagens_processadas = set()
        self.target_mach = 0.80 

        # --- A GRELHA DO PAINEL (Fica no fundo) ---
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=2) 
        self.grid_columnconfigure(2, weight=1) 
        self.grid_rowconfigure(0, weight=1)    
        self.grid_rowconfigure(1, weight=0)    

        self.construir_painel_instrumentos()

        # ==========================================
        # SISTEMA "COLD AND DARK" (MÁSCARA)
        # ==========================================
        self.tela_desligada = ctk.CTkFrame(self, fg_color="#050505")
        self.tela_desligada.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.lbl_logo = ctk.CTkLabel(self.tela_desligada, text="AERONAVE DESLIGADA\n(COLD & DARK)", font=("Arial", 30, "bold"), text_color="#333333")
        self.lbl_logo.pack(expand=True) 

        self.btn_power = ctk.CTkButton(self.tela_desligada, text="⏻ AVIONICS MASTER SWITCH", font=("Arial", 24, "bold"), 
                                       fg_color="#8B0000", hover_color="#FF0000", width=350, height=80, 
                                       command=self.sequencia_arranque)
        self.btn_power.pack(pady=60)

    # ==========================================
    # SEQUÊNCIA DE ARRANQUE (BOOT SEQUENCE)
    # ==========================================
    def sequencia_arranque(self):
        self.btn_power.pack_forget()
        self.lbl_logo.configure(text="INITIATING FLIGHT SYSTEMS...", text_color="#1E90FF")
        self.after(1500, self.boot_step_1)

    def boot_step_1(self):
        self.lbl_logo.configure(text="CONNECTING TO AVIONICS DATABUS (MQTT)...", text_color="#FFD700")
        self.iniciar_middleware()
        self.after(1500, self.boot_step_2)

    def boot_step_2(self):
        self.lbl_logo.configure(text="SYSTEMS ONLINE.", text_color="#39FF14")
        self.after(1000, self.revelar_painel)

    def revelar_painel(self):
        self.tela_desligada.place_forget()

    def desligar_aviao(self):
        try:
            self.cliente_mqtt.disconnect()
            self.cliente_mqtt.loop_stop()
        except:
            pass
        self.tela_desligada.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lbl_logo.configure(text="AERONAVE DESLIGADA\n(COLD & DARK)", text_color="#333333")
        self.btn_power.pack(pady=60)

    # ==========================================
    # CONSTRUÇÃO DOS INSTRUMENTOS
    # ==========================================
    def construir_painel_instrumentos(self):
        # --- COLUNA 0: VELOCIDADE E VENTO ---
        self.frame_esq = ctk.CTkFrame(self, fg_color="#141414", border_width=2, border_color="#333333")
        self.frame_esq.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        ctk.CTkLabel(self.frame_esq, text="AIRSPEED", font=("Arial", 14, "bold"), text_color="#1E90FF").pack(pady=10)
        
        # Botões de Controle de Velocidade
        self.frame_botoes = ctk.CTkFrame(self.frame_esq, fg_color="transparent")
        self.frame_botoes.pack(pady=5)
        self.btn_menos = ctk.CTkButton(self.frame_botoes, text="-", width=40, font=("Arial", 20, "bold"), fg_color="#8B0000", hover_color="#FF0000", command=self.diminuir_vel)
        self.btn_menos.grid(row=0, column=0, padx=5)
        self.btn_mais = ctk.CTkButton(self.frame_botoes, text="+", width=40, font=("Arial", 20, "bold"), fg_color="#006400", hover_color="#00FF00", command=self.aumentar_vel)
        self.btn_mais.grid(row=0, column=1, padx=5)

        self.lbl_target = ctk.CTkLabel(self.frame_esq, text=f"TARGET: {self.target_mach:.2f} M", font=("Arial", 14, "bold"), text_color="#FFD700")
        self.lbl_target.pack(pady=5)

        # Fita de Velocidade
        self.lbl_mach = ctk.CTkLabel(self.frame_esq, text=".---", font=("Consolas", 50, "bold"), text_color="#00FFCC")
        self.lbl_mach.pack(pady=5)
        ctk.CTkLabel(self.frame_esq, text="MACH", font=("Arial", 12)).pack()
        self.bar_velocidade = ctk.CTkProgressBar(self.frame_esq, orientation="vertical", height=200, width=30, progress_color="#00FFCC")
        self.bar_velocidade.pack(pady=15)
        self.bar_velocidade.set(0.0)

        self.lbl_vento = ctk.CTkLabel(self.frame_esq, text="Vento: -- kt\nN/A", font=("Arial", 16), text_color="#FFA500")
        self.lbl_vento.pack(pady=20)

        # --- COLUNA 1: PFD CENTRAL E FMS ---
        self.frame_centro = ctk.CTkFrame(self, fg_color="#1A1A24", border_width=2, border_color="#333333")
        self.frame_centro.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.lbl_piloto_auto = ctk.CTkLabel(self.frame_centro, text="AP: DESLIGADO", font=("Arial", 18, "bold"), text_color="gray")
        self.lbl_piloto_auto.pack(pady=10)
        
        # Inserção de Rota FMS
        self.frame_fms = ctk.CTkFrame(self.frame_centro, fg_color="transparent")
        self.frame_fms.pack(pady=10)
        self.input_origem = ctk.CTkEntry(self.frame_fms, placeholder_text="Origem (ex: SBGR)", width=130)
        self.input_origem.grid(row=0, column=0, padx=5)
        self.input_destino = ctk.CTkEntry(self.frame_fms, placeholder_text="Destino (ex: KJFK)", width=130)
        self.input_destino.grid(row=0, column=1, padx=5)
        self.btn_rota = ctk.CTkButton(self.frame_fms, text="SET ROUTE", width=90, fg_color="#1E90FF", command=self.enviar_rota)
        self.btn_rota.grid(row=0, column=2, padx=5)

        # Proa e Rota (Atualizado pelo FMS)
        self.lbl_proa = ctk.CTkLabel(self.frame_centro, text="---°", font=("Consolas", 60, "bold"), text_color="white")
        self.lbl_proa.pack(pady=10)
        ctk.CTkLabel(self.frame_centro, text="PROA MAGNÉTICA (HDG)", font=("Arial", 12, "bold"), text_color="#1E90FF").pack()
        
        self.lbl_waypoint = ctk.CTkLabel(self.frame_centro, text="ROUTE: N/A | DIST: 0 NM | ETA: -- min", font=("Arial", 16), text_color="#FFD700")
        self.lbl_waypoint.pack(pady=15)
        
        # Altitude
        self.frame_alt = ctk.CTkFrame(self.frame_centro, fg_color="transparent")
        self.frame_alt.pack(pady=10)
        ctk.CTkLabel(self.frame_alt, text="ALTITUDE", font=("Arial", 12, "bold"), text_color="#1E90FF").grid(row=0, column=0, padx=10)
        self.lbl_altitude = ctk.CTkLabel(self.frame_alt, text="-----", font=("Consolas", 45, "bold"), text_color="#39FF14")
        self.lbl_altitude.grid(row=1, column=0, padx=10)
        self.bar_altitude = ctk.CTkProgressBar(self.frame_alt, orientation="vertical", height=150, width=20, progress_color="#39FF14")
        self.bar_altitude.grid(row=1, column=1, padx=10)
        self.bar_altitude.set(0.0)
        
        self.lbl_vs = ctk.CTkLabel(self.frame_centro, text="VS: ---- fpm", font=("Consolas", 20))
        self.lbl_vs.pack(pady=5)

        # --- COLUNA 2: EIS E RADAR ---
        self.frame_dir = ctk.CTkFrame(self, fg_color="#141414", border_width=2, border_color="#333333")
        self.frame_dir.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(self.frame_dir, text="ENGINE & FUEL", font=("Arial", 14, "bold"), text_color="#1E90FF").pack(pady=10)
        self.lbl_motor_press = ctk.CTkLabel(self.frame_dir, text="N1 (Press): --- psi", font=("Consolas", 16))
        self.lbl_motor_press.pack(pady=2)
        self.lbl_motor_temp = ctk.CTkLabel(self.frame_dir, text="EGT (Temp): --- °C", font=("Consolas", 16))
        self.lbl_motor_temp.pack(pady=2)
        
        self.lbl_combustivel = ctk.CTkLabel(self.frame_dir, text="FUEL: ---%", font=("Consolas", 24, "bold"), text_color="#39FF14")
        self.lbl_combustivel.pack(pady=15)
        self.bar_combustivel = ctk.CTkProgressBar(self.frame_dir, height=25, width=200, progress_color="#39FF14")
        self.bar_combustivel.pack(pady=5)
        self.bar_combustivel.set(0.0)
        
        ctk.CTkLabel(self.frame_dir, text="WEATHER RADAR", font=("Arial", 14, "bold"), text_color="#1E90FF").pack(pady=20)
        self.lbl_radar = ctk.CTkLabel(self.frame_dir, text="SCANNING...", font=("Arial", 18, "bold"), text_color="#FF4500")
        self.lbl_radar.pack(pady=5)
        self.lbl_temp_ext = ctk.CTkLabel(self.frame_dir, text="OAT: -- °C", font=("Consolas", 16))
        self.lbl_temp_ext.pack(pady=2)
        self.lbl_gelo = ctk.CTkLabel(self.frame_dir, text="ANTI-ICE: AUTO", font=("Consolas", 16))
        self.lbl_gelo.pack(pady=2)

        # --- LINHA INFERIOR: ATC E ALERTAS ---
        self.frame_alertas = ctk.CTkFrame(self, fg_color="#1A1A1A")
        self.frame_alertas.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        
        self.btn_desligar = ctk.CTkButton(self.frame_alertas, text="⏻ SHUTDOWN", width=80, fg_color="#8B0000", command=self.desligar_aviao)
        self.btn_desligar.pack(side="left", padx=10)

        self.lbl_atc = ctk.CTkLabel(self.frame_alertas, text="✉️ ATC: STANDBY", font=("Arial", 16, "italic"), text_color="#1E90FF")
        self.lbl_atc.pack(side="left", padx=20, pady=10)
        self.lbl_alerta_freio = ctk.CTkLabel(self.frame_alertas, text="BRAKE SYS: NOMINAL", font=("Consolas", 16, "bold"), text_color="green")
        self.lbl_alerta_freio.pack(side="right", padx=20, pady=10)

    # ==========================================
    # ENVIOS PARA A REDE (COMANDOS)
    # ==========================================
    def aumentar_vel(self):
        self.target_mach = round(min(self.target_mach + 0.05, 1.0), 2)
        self.enviar_comando()

    def diminuir_vel(self):
        self.target_mach = round(max(self.target_mach - 0.05, 0.4), 2)
        self.enviar_comando()

    def enviar_comando(self):
        self.lbl_target.configure(text=f"TARGET: {self.target_mach:.2f} M")
        pacote_comando = {"nova_velocidade": self.target_mach}
        self.cliente_mqtt.publish(TOPICO_CMD_VEL, json.dumps(pacote_comando))

    def enviar_rota(self):
        origem = self.input_origem.get()
        destino = self.input_destino.get()
        if origem and destino:
            pacote_rota = {"origem": origem, "destino": destino}
            self.cliente_mqtt.publish(TOPICO_CMD_ROTA, json.dumps(pacote_rota))
            self.lbl_waypoint.configure(text="ROUTE: CALCULATING VIA FMS...", text_color="#1E90FF")

    # ==========================================
    # RECEBIMENTO E ROTEAMENTO (MQTT)
    # ==========================================
    def iniciar_middleware(self):
        self.cliente_mqtt = mqtt.Client()
        self.cliente_mqtt.on_connect = self.ao_conectar
        self.cliente_mqtt.on_message = self.ao_receber_mensagem
        try:
            self.cliente_mqtt.connect(BROKER, PORTA, 60)
            self.cliente_mqtt.loop_start()
        except Exception as e:
            self.lbl_atc.configure(text=f"❌ ERRO DE REDE: {e}", text_color="red")

    def ao_conectar(self, client, userdata, flags, rc):
        client.subscribe([
            (TOPICO_FREIOS, 0), (TOPICO_WAIC, 0), (TOPICO_VOO, 0), 
            (TOPICO_NAV, 0), (TOPICO_RADAR, 0), (TOPICO_FMS_DADOS, 0)
        ])

    def ao_receber_mensagem(self, client, userdata, msg):
        try:
            pacote = json.loads(msg.payload.decode())
            id_msg = pacote.get("id_mensagem")
            
            is_duplicada = False
            if id_msg: 
                if id_msg in self.mensagens_processadas:
                    is_duplicada = True
                else:
                    self.mensagens_processadas.add(id_msg)
                    if len(self.mensagens_processadas) > 100:
                        self.mensagens_processadas.pop()

            if msg.topic == TOPICO_FREIOS:
                self.after(0, self.atualizar_freios, pacote, is_duplicada)
            elif msg.topic == TOPICO_WAIC and not is_duplicada:
                self.after(0, self.atualizar_waic, pacote)
            elif msg.topic == TOPICO_VOO:
                self.after(0, self.atualizar_voo, pacote)
            elif msg.topic == TOPICO_NAV:
                self.after(0, self.atualizar_nav, pacote)
            elif msg.topic == TOPICO_RADAR:
                self.after(0, self.atualizar_radar, pacote)
            elif msg.topic == TOPICO_FMS_DADOS:
                self.after(0, self.atualizar_fms, pacote)
        except Exception as e:
            pass

    # ==========================================
    # ATUALIZAÇÃO VISUAL DOS INSTRUMENTOS
    # ==========================================
    def atualizar_freios(self, pacote, is_duplicada):
        if not is_duplicada:
            pressao = pacote['dados']['pressao']
            if pressao < 50:
                self.lbl_alerta_freio.configure(text=f"⚠️ HYD BRAKE FAIL ({pressao} psi)", text_color="red")
            else:
                self.lbl_alerta_freio.configure(text=f"BRAKE SYS: OK ({pressao} psi)", text_color="green")

    def atualizar_waic(self, pacote):
        self.lbl_motor_press.configure(text=f"N1: {pacote['dados']['pressao_motor']} psi")
        self.lbl_motor_temp.configure(text=f"EGT: {pacote['dados']['temperatura']} °C")

    def atualizar_voo(self, pacote):
        d = pacote['dados']
        mach = d['velocidade_mach']
        texto_mach = f"{mach:.2f}".replace("0.", ".")
        self.lbl_mach.configure(text=texto_mach) 
        self.bar_velocidade.set(min(mach / 1.0, 1.0))
        
        alt = d['altitude_ft']
        self.lbl_altitude.configure(text=f"{alt}")
        self.bar_altitude.set(min(alt / 45000.0, 1.0))
        
        comb = d['combustivel_pct']
        self.lbl_combustivel.configure(text=f"FUEL: {comb}%")
        self.bar_combustivel.set(comb / 100.0)
        if comb < 20.0:
            self.lbl_combustivel.configure(text_color="red")
            self.bar_combustivel.configure(progress_color="red")

    def atualizar_nav(self, pacote):
        d = pacote['dados']
        self.lbl_piloto_auto.configure(text=f"AP: {d.get('piloto_automatico', 'ON')}", text_color="#39FF14")
        self.lbl_proa.configure(text=f"{d.get('proa_graus', 0)}°")
        
        vs = d.get('vs_fpm', 0)
        self.lbl_vs.configure(text=f"VS: {vs} fpm")
        cor_vs = "white"
        if vs > 0: cor_vs = "#39FF14"
        elif vs < 0: cor_vs = "#FFA500"
        self.lbl_vs.configure(text_color=cor_vs)

    def atualizar_fms(self, pacote):
        d = pacote['dados']
        self.lbl_waypoint.configure(text=f"ROUTE: {d['rota_texto']} | DIST: {d['distancia_nm']} NM | ETA: {d['eta_minutos']} min", text_color="#FFD700")

    def atualizar_radar(self, pacote):
        d = pacote['dados']
        self.lbl_vento.configure(text=f"Vento: {d['vento_knots']} kt\n(Turb: {d['turbulencia']})")
        
        clima = d['radar_clima']
        cor_clima = "#39FF14" 
        if "NUVENS" in clima: cor_clima = "#FFD700" 
        elif "TEMPESTADE" in clima: cor_clima = "red"
        
        self.lbl_radar.configure(text=clima, text_color=cor_clima)
        self.lbl_temp_ext.configure(text=f"OAT: {d['temp_externa_c']} °C")
        cor_gelo = "red" if "DETETADO" in d['gelo'] else "gray"
        self.lbl_gelo.configure(text=f"ICE: {d['gelo']}", text_color=cor_gelo)
        self.lbl_atc.configure(text=f"✉️ ATC (QNH {d['qnh_hpa']}): {d['atc_msg']}")

if __name__ == "__main__":
    app = GlassCockpit()
    app.mainloop()
