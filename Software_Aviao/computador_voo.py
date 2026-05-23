import json
import math 
import customtkinter as ctk
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORTA = 1883

TOPICO_FREIOS = "avionica/sensores/freios"
TOPICO_WAIC = "avionica/sensores/waic"
TOPICO_VOO = "avionica/sensores/voo"
TOPICO_NAV = "avionica/navegacao"
TOPICO_RADAR = "avionica/radar"
TOPICO_FMS_DADOS = "avionica/fms/dados"

TOPICO_CMD_VEL = "avionica/comandos/velocidade"
TOPICO_CMD_ROTA = "avionica/comandos/rota"
TOPICO_CMD_PROA = "avionica/comandos/proa" 
TOPICO_FALHAS = "avionica/comandos/falhas"
TOPICO_ANTI_ICE = "avionica/sistemas/anti_ice"

class GlassCockpit(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("✈️ Phenom 300 MFD - Glass Cockpit Distribuído")
        self.geometry("1100x750")
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#0A0A0A")
        
        self.mensagens_processadas = set()
        self.target_mach = 0.80 
        self.target_proa = 0 

        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=2) 
        self.grid_columnconfigure(2, weight=1) 
        self.grid_rowconfigure(0, weight=1)    
        self.grid_rowconfigure(1, weight=0)    

        self.construir_painel_instrumentos()

        self.tela_desligada = ctk.CTkFrame(self, fg_color="#050505")
        self.tela_desligada.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lbl_logo = ctk.CTkLabel(self.tela_desligada, text="AERONAVE DESLIGADA\n(COLD & DARK)", font=("Arial", 30, "bold"), text_color="#333333")
        self.lbl_logo.pack(expand=True) 
        self.btn_power = ctk.CTkButton(self.tela_desligada, text="⏻ AVIONICS MASTER SWITCH", font=("Arial", 24, "bold"), 
                                       fg_color="#8B0000", hover_color="#FF0000", width=350, height=80, command=self.sequencia_arranque)
        self.btn_power.pack(pady=60)

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
        except: pass
        self.tela_desligada.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lbl_logo.configure(text="AERONAVE DESLIGADA\n(COLD & DARK)", text_color="#333333")
        self.btn_power.pack(pady=60)

    def construir_painel_instrumentos(self):
        # ==========================================
        # COLUNA 0: VELOCIDADE E VENTO
        # ==========================================
        self.frame_esq = ctk.CTkFrame(self, fg_color="#141414", border_width=2, border_color="#333333")
        self.frame_esq.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(self.frame_esq, text="AIRSPEED", font=("Arial", 14, "bold"), text_color="#1E90FF").pack(pady=10)
        
        self.frame_botoes = ctk.CTkFrame(self.frame_esq, fg_color="transparent")
        self.frame_botoes.pack(pady=5)
        self.btn_menos = ctk.CTkButton(self.frame_botoes, text="-", width=40, font=("Arial", 20, "bold"), fg_color="#8B0000", hover_color="#FF0000", command=self.diminuir_vel)
        self.btn_menos.grid(row=0, column=0, padx=5)
        self.btn_mais = ctk.CTkButton(self.frame_botoes, text="+", width=40, font=("Arial", 20, "bold"), fg_color="#006400", hover_color="#00FF00", command=self.aumentar_vel)
        self.btn_mais.grid(row=0, column=1, padx=5)

        self.lbl_target = ctk.CTkLabel(self.frame_esq, text=f"TARGET: {self.target_mach:.2f} M", font=("Arial", 14, "bold"), text_color="#FFD700")
        self.lbl_target.pack(pady=5)

        self.lbl_mach = ctk.CTkLabel(self.frame_esq, text=".---", font=("Consolas", 50, "bold"), text_color="#00FFCC")
        self.lbl_mach.pack(pady=5)
        ctk.CTkLabel(self.frame_esq, text="MACH", font=("Arial", 12)).pack()
        self.bar_velocidade = ctk.CTkProgressBar(self.frame_esq, orientation="vertical", height=200, width=30, progress_color="#00FFCC")
        self.bar_velocidade.pack(pady=15)
        self.bar_velocidade.set(0.0)
        self.lbl_vento = ctk.CTkLabel(self.frame_esq, text="Vento: -- kt\nN/A", font=("Arial", 16), text_color="#FFA500")
        self.lbl_vento.pack(pady=20)

        # ==========================================
        # COLUNA 1: PFD CENTRAL E ALERTAS
        # ==========================================
        self.frame_centro = ctk.CTkFrame(self, fg_color="#1A1A24", border_width=2, border_color="#333333")
        self.frame_centro.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.lbl_piloto_auto = ctk.CTkLabel(self.frame_centro, text="AP: DESLIGADO", font=("Arial", 18, "bold"), text_color="gray")
        self.lbl_piloto_auto.pack(pady=10)
        
        self.frame_proa_cmds = ctk.CTkFrame(self.frame_centro, fg_color="transparent")
        self.frame_proa_cmds.pack(pady=5)
        ctk.CTkButton(self.frame_proa_cmds, text="< 5º", width=40, fg_color="#555555", command=lambda: self.ajustar_proa(-5)).grid(row=0, column=0, padx=2)
        ctk.CTkButton(self.frame_proa_cmds, text="< 1º", width=40, fg_color="#8B0000", command=lambda: self.ajustar_proa(-1)).grid(row=0, column=1, padx=2)
        self.lbl_alvo_proa = ctk.CTkLabel(self.frame_proa_cmds, text=f"SEL: {self.target_proa:03d}º", font=("Arial", 16, "bold"), text_color="#FFD700")
        self.lbl_alvo_proa.grid(row=0, column=2, padx=10)
        ctk.CTkButton(self.frame_proa_cmds, text="1º >", width=40, fg_color="#006400", command=lambda: self.ajustar_proa(1)).grid(row=0, column=3, padx=2)
        ctk.CTkButton(self.frame_proa_cmds, text="5º >", width=40, fg_color="#555555", command=lambda: self.ajustar_proa(5)).grid(row=0, column=4, padx=2)
        
        self.lbl_proa = ctk.CTkLabel(self.frame_centro, text="000°", font=("Consolas", 35, "bold"), text_color="white")
        self.lbl_proa.pack(pady=2)
        self.canvas_bussola = ctk.CTkCanvas(self.frame_centro, width=160, height=160, bg="#1A1A24", highlightthickness=0)
        self.canvas_bussola.pack()
        self.desenhar_bussola(0)

        # 🚨 LUZ DE EMERGÊNCIA (MASTER WARNING) - Fica invisível até ser ativada
        self.lbl_master_warning = ctk.CTkLabel(self.frame_centro, text="", font=("Arial", 22, "bold"))
        self.lbl_master_warning.pack(pady=2)

        self.frame_alt = ctk.CTkFrame(self.frame_centro, fg_color="transparent")
        self.frame_alt.pack(pady=5)
        ctk.CTkLabel(self.frame_alt, text="ALTITUDE", font=("Arial", 12, "bold"), text_color="#1E90FF").grid(row=0, column=0, columnspan=2)
        self.lbl_altitude = ctk.CTkLabel(self.frame_alt, text="-----", font=("Consolas", 35, "bold"), text_color="#39FF14")
        self.lbl_altitude.grid(row=1, column=0, padx=10)
        self.bar_altitude = ctk.CTkProgressBar(self.frame_alt, orientation="vertical", height=100, width=18, progress_color="#39FF14")
        self.bar_altitude.grid(row=1, column=1, padx=5)
        self.bar_altitude.set(0.0)
        
        self.lbl_vs = ctk.CTkLabel(self.frame_centro, text="VS: ---- fpm", font=("Consolas", 18))
        self.lbl_vs.pack()

        self.lbl_waypoint = ctk.CTkLabel(self.frame_centro, text="ROUTE: N/A | DIST: 0 NM | ETA: -- min", font=("Arial", 14), text_color="#FFD700")
        self.lbl_waypoint.pack(pady=5)
        
        self.frame_fms = ctk.CTkFrame(self.frame_centro, fg_color="transparent")
        self.frame_fms.pack(pady=2)
        self.input_origem = ctk.CTkEntry(self.frame_fms, placeholder_text="Origem", width=90)
        self.input_origem.grid(row=0, column=0, padx=5)
        self.input_destino = ctk.CTkEntry(self.frame_fms, placeholder_text="Destino", width=90)
        self.input_destino.grid(row=0, column=1, padx=5)
        self.btn_rota = ctk.CTkButton(self.frame_fms, text="SET ROUTE", width=70, fg_color="#1E90FF", command=self.enviar_rota)
        self.btn_rota.grid(row=0, column=2, padx=5)

        # ==========================================
        # COLUNA 2: EIS E RADAR
        # ==========================================
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

        # ==========================================
        # LINHA INFERIOR: ATC E ALERTAS
        # ==========================================
        self.frame_alertas = ctk.CTkFrame(self, fg_color="#1A1A1A")
        self.frame_alertas.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        
        self.btn_desligar = ctk.CTkButton(self.frame_alertas, text="⏻ SHUTDOWN", width=80, fg_color="#8B0000", command=self.desligar_aviao)
        self.btn_desligar.pack(side="left", padx=10)

        self.lbl_atc = ctk.CTkLabel(self.frame_alertas, text="✉️ ATC: STANDBY", font=("Arial", 16, "italic"), text_color="#1E90FF")
        self.lbl_atc.pack(side="left", padx=20, pady=10)
        self.lbl_alerta_freio = ctk.CTkLabel(self.frame_alertas, text="BRAKE SYS: NOMINAL", font=("Consolas", 16, "bold"), text_color="green")
        self.lbl_alerta_freio.pack(side="right", padx=20, pady=10)

    # (Funções mantidas perfeitamente iguais: bussola, botões de enviar, etc)
    def desenhar_bussola(self, graus):
        self.canvas_bussola.delete("all") 
        cx, cy, r = 80, 80, 65 
        
        self.canvas_bussola.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#333333", width=2, fill="#0A0A0A")
        cardeais = {0: "N", 90: "E", 180: "S", 270: "W"}
        
        for i in range(0, 360, 30):
            rad_i = math.radians(i - graus - 90)
            if i in cardeais:
                cor = "#1E90FF" if i == 0 else "white"
                tx = cx + (r - 12) * math.cos(rad_i)
                ty = cy + (r - 12) * math.sin(rad_i)
                self.canvas_bussola.create_text(tx, ty, text=cardeais[i], fill=cor, font=("Arial", 10, "bold"))
            else:
                x1 = cx + (r - 2) * math.cos(rad_i)
                y1 = cy + (r - 2) * math.sin(rad_i)
                x2 = cx + (r - 6) * math.cos(rad_i)
                y2 = cy + (r - 6) * math.sin(rad_i)
                self.canvas_bussola.create_line(x1, y1, x2, y2, fill="gray", width=1)

        ponta_y = cy - (r - 15)
        self.canvas_bussola.create_line(cx, cy + 12, cx, ponta_y, arrow="last", arrowshape=(12,15,5), fill="#39FF14", width=3)
        self.canvas_bussola.create_line(cx - 12, cy, cx + 12, cy, fill="#39FF14", width=2)
        self.canvas_bussola.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill="white")

    def ajustar_proa(self, incremento):
        self.target_proa = (self.target_proa + incremento) % 360
        self.lbl_alvo_proa.configure(text=f"SEL: {self.target_proa:03d}º")
        self.cliente_mqtt.publish(TOPICO_CMD_PROA, json.dumps({"nova_proa": self.target_proa}))

    def aumentar_vel(self):
        self.target_mach = round(min(self.target_mach + 0.05, 1.0), 2)
        self.enviar_comando_vel()

    def diminuir_vel(self):
        self.target_mach = round(max(self.target_mach - 0.05, 0.4), 2)
        self.enviar_comando_vel()

    def enviar_comando_vel(self):
        self.lbl_target.configure(text=f"TARGET: {self.target_mach:.2f} M")
        self.cliente_mqtt.publish(TOPICO_CMD_VEL, json.dumps({"nova_velocidade": self.target_mach}))

    def enviar_rota(self):
        origem = self.input_origem.get()
        destino = self.input_destino.get()
        if origem and destino:
            self.cliente_mqtt.publish(TOPICO_CMD_ROTA, json.dumps({"origem": origem, "destino": destino}))
            self.lbl_waypoint.configure(text="ROUTE: CALCULATING VIA FMS...", text_color="#1E90FF")

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
        client.subscribe([(TOPICO_FREIOS, 0), (TOPICO_WAIC, 0), (TOPICO_VOO, 0), (TOPICO_NAV, 0), (TOPICO_RADAR, 0), (TOPICO_FMS_DADOS, 0), (TOPICO_FALHAS, 0), (TOPICO_ANTI_ICE, 0)])

    def ao_receber_mensagem(self, client, userdata, msg):
        try:
            pacote = json.loads(msg.payload.decode())
            id_msg = pacote.get("id_mensagem")
            
            is_duplicada = False
            if id_msg: 
                if id_msg in self.mensagens_processadas: is_duplicada = True
                else:
                    self.mensagens_processadas.add(id_msg)
                    if len(self.mensagens_processadas) > 100: self.mensagens_processadas.pop()

            if msg.topic == TOPICO_FREIOS: self.after(0, self.atualizar_freios, pacote, is_duplicada)
            elif msg.topic == TOPICO_WAIC and not is_duplicada: self.after(0, self.atualizar_waic, pacote)
            elif msg.topic == TOPICO_VOO: self.after(0, self.atualizar_voo, pacote)
            elif msg.topic == TOPICO_NAV: self.after(0, self.atualizar_nav, pacote)
            elif msg.topic == TOPICO_RADAR: self.after(0, self.atualizar_radar, pacote)
            elif msg.topic == TOPICO_FMS_DADOS: self.after(0, self.atualizar_fms, pacote)
            elif msg.topic == TOPICO_FALHAS: self.after(0, self.atualizar_alertas_visuais, pacote)
            elif msg.topic == TOPICO_ANTI_ICE: self.after(0, self.atualizar_anti_ice, pacote)
        except: pass

    # ==========================================
    # NOVAS FUNÇÕES DE FALHA VISUAL
    # ==========================================
    def atualizar_alertas_visuais(self, pacote):
        tipo = pacote.get("tipo")
        if tipo == "trafego":
            self.lbl_master_warning.configure(text="⚠️ TRAFFIC! TRAFFIC! ⚠️", text_color="yellow")
        elif tipo == "queda":
            self.lbl_master_warning.configure(text="🚨 PULL UP! TERRAIN! 🚨", text_color="red")
        elif tipo == "motor":
            self.lbl_master_warning.configure(text="💥 ENGINE FAILURE 💥", text_color="red")
            self.lbl_motor_press.configure(text_color="red")
            
        # O alerta desaparece sozinho após 5 segundos!
        self.after(5000, lambda: self.lbl_master_warning.configure(text=""))

    def atualizar_anti_ice(self, pacote):
        status = pacote.get("status")
        if status == "ON":
            self.lbl_gelo.configure(text=pacote["msg"], text_color="#39FF14") # Verde a avisar que ligou
        else:
            self.lbl_gelo.configure(text=pacote["msg"], text_color="gray")

    def atualizar_nav(self, pacote):
        d = pacote['dados']
        proa_real = d.get('proa_graus', 0)
        self.lbl_proa.configure(text=f"{proa_real:03d}°")
        self.desenhar_bussola(proa_real)
        
        vs = d.get('vs_fpm', 0)
        self.lbl_vs.configure(text=f"VS: {vs} fpm")
        cor_vs = "white"
        if vs > 0: cor_vs = "#39FF14"
        elif vs < 0: cor_vs = "#FFA500"
        self.lbl_vs.configure(text_color=cor_vs)

    def atualizar_voo(self, pacote):
        d = pacote['dados']
        mach = d['velocidade_mach']
        texto_mach = f"{mach:.2f}".replace("0.", ".")
        self.lbl_mach.configure(text=texto_mach) 
        self.bar_velocidade.set(min(mach / 1.0, 1.0))
        
        alt = d['altitude_ft']
        self.lbl_altitude.configure(text=f"{alt} FT")
        self.bar_altitude.set(min(alt / 45000.0, 1.0))
        
        comb = d['combustivel_pct']
        self.lbl_combustivel.configure(text=f"FUEL: {comb}%")
        self.bar_combustivel.set(comb / 100.0)
        if comb < 20.0:
            self.lbl_combustivel.configure(text_color="red")
            self.bar_combustivel.configure(progress_color="red")

    def atualizar_fms(self, pacote):
        d = pacote['dados']
        self.lbl_waypoint.configure(text=f"ROUTE: {d['rota_texto']} | DIST: {d['distancia_nm']} NM | ETA: {d['eta_minutos']} min", text_color="#FFD700")

    def atualizar_freios(self, pacote, is_duplicada):
        if not is_duplicada:
            pressao = pacote['dados']['pressao']
            if pressao < 50: self.lbl_alerta_freio.configure(text=f"⚠️ HYD BRAKE FAIL ({pressao} psi)", text_color="red")
            else: self.lbl_alerta_freio.configure(text=f"BRAKE SYS: OK ({pressao} psi)", text_color="green")

    def atualizar_waic(self, pacote):
        # Só volta a pintar o motor de branco se a pressão estiver normal
        if pacote['dados']['pressao_motor'] > 10:
            self.lbl_motor_press.configure(text_color="white")
        self.lbl_motor_press.configure(text=f"N1: {pacote['dados']['pressao_motor']} psi")
        self.lbl_motor_temp.configure(text=f"EGT: {pacote['dados']['temperatura']} °C")

    def atualizar_radar(self, pacote):
        d = pacote['dados']
        self.lbl_vento.configure(text=f"Vento: {d['vento_knots']} kt\n(Turb: {d['turbulencia']})")
        clima = d['radar_clima']
        cor_clima = "#39FF14" 
        if "NUVENS" in clima: cor_clima = "#FFD700" 
        elif "TEMPESTADE" in clima: cor_clima = "red"
        
        self.lbl_radar.configure(text=clima, text_color=cor_clima)
        self.lbl_temp_ext.configure(text=f"OAT: {d['temp_externa_c']} °C")
        self.lbl_atc.configure(text=f"✉️ ATC (QNH {d['qnh_hpa']}): {d['atc_msg']}")

if __name__ == "__main__":
    app = GlassCockpit()
    app.mainloop()
