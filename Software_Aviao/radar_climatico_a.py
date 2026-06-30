import json
import os
import socket
import threading
import time
from typing import Any

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None

from servico_clima import buscar_metar, resumir_clima, classificar_risco


# Região monitorada pelo Radar A
AEROPORTO_REGIAO_A = os.getenv("RADAR_A_ICAO", "SBRF")

# Intervalos de execução
INTERVALO_ATUALIZACAO = int(
    os.getenv("RADAR_A_INTERVALO", "60")
)

INTERVALO_GOSSIP = int(
    os.getenv("RADAR_GOSSIP_INTERVALO", "10")
)

INTERVALO_MQTT = int(
    os.getenv("RADAR_MQTT_INTERVALO", "3")
)

# Servidor TCP do Radar A
TCP_MEU_HOST = "0.0.0.0"

TCP_MINHA_PORTA = int(
    os.getenv("RADAR_A_PORT", "5001")
)

# Endereço do Radar B
TCP_PEER_HOST = os.getenv(
    "RADAR_B_HOST",
    "127.0.0.1"
)

TCP_PEER_PORT = int(
    os.getenv("RADAR_B_PORT", "5002")
)

# Configuração MQTT
BROKER_MQTT = os.getenv(
    "MQTT_BROKER",
    "broker.hivemq.com"
)

PORTA_MQTT = int(
    os.getenv("MQTT_PORT", "1883")
)

TOPICO_TELEMETRIA = "avionica.telemetry.radar"


class RadarClimaticoA:
    def __init__(self):
        self.malha_climatica: dict[
            str,
            dict[str, Any] | None
        ] = {
            "Regiao_A": None,
            "Regiao_B": None
        }

        self.lock = threading.Lock()
        self.encerramento = threading.Event()

    def extrair_timestamp(
            self,
            pacote: dict[str, Any] | None
    ) -> int:
        if not pacote or "id_mensagem" not in pacote:
            return 0

        try:
            return int(
                pacote["id_mensagem"].split("_")[1]
            )
        except (IndexError, TypeError, ValueError):
            return 0

    def mesclar_dados(
            self,
            regiao: str,
            novo_pacote: dict[str, Any] | None
    ) -> None:
        """
        Mantém na memória somente o pacote mais recente.

        Essa comparação por timestamp implementa a regra de
        consistência eventual utilizada pelos radares A e B.
        """
        if regiao not in self.malha_climatica:
            print(f"[GOSSIP] Região desconhecida: {regiao}")
            return

        if not novo_pacote:
            return

        with self.lock:
            pacote_atual = self.malha_climatica[regiao]

            timestamp_atual = self.extrair_timestamp(
                pacote_atual
            )

            timestamp_novo = self.extrair_timestamp(
                novo_pacote
            )

            if timestamp_novo > timestamp_atual:
                self.malha_climatica[regiao] = novo_pacote

                print(
                    f"[GOSSIP] Malha atualizada para {regiao}. "
                    f"ID: {novo_pacote['id_mensagem']}"
                )

    def classificar_turbulencia(
            self,
            dados_brutos: dict,
            risco: str
    ) -> str:
        try:
            vento = float(dados_brutos.get("wspd") or 0)
        except (TypeError, ValueError):
            vento = 0

        fenomeno = str(
            dados_brutos.get("wxString") or ""
        ).upper()

        if (
                risco == "Alto"
                or "TS" in fenomeno
                or vento >= 30
        ):
            return "SEVERA"

        if risco == "Médio" or vento >= 20:
            return "MODERADA"

        return "LEVE"

    def identificar_clima(
            self,
            dados_brutos: dict,
            risco: str
    ) -> str:
        fenomeno = str(
            dados_brutos.get("wxString") or ""
        ).upper()

        categoria = str(
            dados_brutos.get("fltCat") or ""
        ).upper()

        if "TS" in fenomeno or risco == "Alto":
            return "TEMPESTADE"

        if (
                fenomeno
                or categoria in ["MVFR", "IFR", "LIFR"]
        ):
            return "NUVENS"

        return "CÉU LIMPO"

    def gerar_mensagem_atc(
            self,
            clima: str,
            turbulencia: str
    ) -> str:
        if clima == "TEMPESTADE":
            return (
                "Evite formações meteorológicas severas"
            )

        if turbulencia == "MODERADA":
            return (
                "Possibilidade de turbulência moderada"
            )

        return "Rota livre"

    def gerar_pacote_regiao_a(
            self
    ) -> dict[str, Any] | None:
        dados_brutos = buscar_metar(
            AEROPORTO_REGIAO_A
        )

        if "erro" in dados_brutos:
            print(
                f"[ERRO CLIMA] {AEROPORTO_REGIAO_A}: "
                f"{dados_brutos['erro']}"
            )

            # O último pacote válido permanece em cache.
            return None

        dados_resumidos = resumir_clima(
            dados_brutos
        )

        risco = classificar_risco(
            dados_brutos
        )

        clima = self.identificar_clima(
            dados_brutos,
            risco
        )

        turbulencia = self.classificar_turbulencia(
            dados_brutos,
            risco
        )

        return {
            "id_mensagem": (
                f"radA_{int(time.time() * 1000)}"
            ),
            "dados": {
                "aeroporto": AEROPORTO_REGIAO_A,
                "nome_aeroporto": (
                    dados_resumidos.get("nome")
                ),
                "vento_knots": dados_brutos.get(
                    "wspd"
                ),
                "turbulencia": turbulencia,
                "radar_clima": clima,
                "temp_externa_c": dados_brutos.get(
                    "temp"
                ),
                "qnh_hpa": dados_brutos.get(
                    "altim"
                ),
                "condicao_voo": dados_brutos.get(
                    "fltCat"
                ),
                "visibilidade": dados_brutos.get(
                    "visib"
                ),
                "fenomeno": dados_resumidos.get(
                    "fenomeno"
                ),
                "risco": risco,
                "atc_msg": self.gerar_mensagem_atc(
                    clima,
                    turbulencia
                ),
                "metar": dados_brutos.get(
                    "rawOb"
                )
            }
        }

    def atualizar_clima_local(self) -> None:
        pacote_local = self.gerar_pacote_regiao_a()

        if pacote_local:
            self.mesclar_dados(
                "Regiao_A",
                pacote_local
            )

    def exibir_malha_climatica(self) -> None:
        with self.lock:
            conteudo = json.dumps(
                self.malha_climatica,
                indent=4,
                ensure_ascii=False
            )

        print(
            "\n========== RADAR CLIMÁTICO A =========="
        )

        print(conteudo)

    def monitorar_clima_local(self) -> None:
        print(
            f"[RADAR A] Monitoramento iniciado para "
            f"{AEROPORTO_REGIAO_A}."
        )

        print(
            f"[RADAR A] Atualização METAR a cada "
            f"{INTERVALO_ATUALIZACAO} segundos."
        )

        while not self.encerramento.is_set():
            self.atualizar_clima_local()
            self.exibir_malha_climatica()

            if self.encerramento.wait(
                    INTERVALO_ATUALIZACAO
            ):
                break

    def processar_malha_externa(
            self,
            malha_externa: dict
    ) -> None:
        for regiao in ("Regiao_A", "Regiao_B"):
            if regiao in malha_externa:
                self.mesclar_dados(
                    regiao,
                    malha_externa[regiao]
                )

    def servidor_gossip(self) -> None:
        """
        Recebe conexões do Radar B na porta 5001.
        """
        try:
            servidor = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            servidor.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1
            )

            servidor.bind(
                (TCP_MEU_HOST, TCP_MINHA_PORTA)
            )

            servidor.listen(5)
            servidor.settimeout(1.0)

        except OSError as erro:
            print(
                f"[ERRO TCP] Não foi possível iniciar "
                f"o servidor Gossip: {erro}"
            )
            return

        print(
            f"[TCP SERVER] Radar A aguardando Gossip "
            f"na porta {TCP_MINHA_PORTA}..."
        )

        with servidor:
            while not self.encerramento.is_set():
                try:
                    conexao, endereco = servidor.accept()

                except socket.timeout:
                    continue

                except OSError as erro:
                    print(
                        f"[ERRO TCP] Falha ao aceitar "
                        f"conexão: {erro}"
                    )
                    continue

                try:
                    with conexao:
                        conexao.settimeout(5.0)

                        dados_recebidos = conexao.recv(
                            65536
                        )

                        if not dados_recebidos:
                            continue

                        malha_externa = json.loads(
                            dados_recebidos.decode(
                                "utf-8"
                            )
                        )

                        self.processar_malha_externa(
                            malha_externa
                        )

                        with self.lock:
                            resposta = json.dumps(
                                self.malha_climatica,
                                ensure_ascii=False
                            )

                        conexao.sendall(
                            resposta.encode("utf-8")
                        )

                        print(
                            "[GOSSIP SERVER] "
                            "Sincronização concluída com "
                            f"{endereco[0]}:{endereco[1]}."
                        )

                except (
                        json.JSONDecodeError,
                        UnicodeDecodeError
                ) as erro:
                    print(
                        "[ERRO GOSSIP] Pacote inválido: "
                        f"{erro}"
                    )

                except socket.timeout:
                    print(
                        "[ERRO GOSSIP] Tempo limite "
                        "da conexão excedido."
                    )

                except OSError as erro:
                    print(
                        "[ERRO GOSSIP] Falha na conexão: "
                        f"{erro}"
                    )

    def cliente_gossip_loop(self) -> None:
        """
        Envia periodicamente a malha do Radar A ao Radar B.
        """
        print(
            f"[GOSSIP CLIENT] Radar B configurado em "
            f"{TCP_PEER_HOST}:{TCP_PEER_PORT}."
        )

        while not self.encerramento.is_set():
            if self.encerramento.wait(
                    INTERVALO_GOSSIP
            ):
                break

            try:
                with socket.socket(
                        socket.AF_INET,
                        socket.SOCK_STREAM
                ) as cliente:
                    cliente.settimeout(3.0)

                    cliente.connect(
                        (TCP_PEER_HOST, TCP_PEER_PORT)
                    )

                    with self.lock:
                        payload = json.dumps(
                            self.malha_climatica,
                            ensure_ascii=False
                        )

                    cliente.sendall(
                        payload.encode("utf-8")
                    )

                    resposta = cliente.recv(65536)

                    if resposta:
                        malha_externa = json.loads(
                            resposta.decode("utf-8")
                        )

                        self.processar_malha_externa(
                            malha_externa
                        )

                    print(
                        "[GOSSIP CLIENT] Sincronização "
                        "com Radar B concluída."
                    )

            except (
                    ConnectionRefusedError,
                    socket.timeout
            ):
                print(
                    "[GOSSIP CLIENT] Radar B offline. "
                    "Mantendo os dados em cache."
                )

            except (
                    json.JSONDecodeError,
                    UnicodeDecodeError
            ) as erro:
                print(
                    "[ERRO GOSSIP] Resposta inválida "
                    f"do Radar B: {erro}"
                )

            except OSError as erro:
                print(
                    "[ERRO GOSSIP] Falha ao acessar "
                    f"o Radar B: {erro}"
                )

    def publicar_mqtt(self) -> None:
        """
        Publica a malha consolidada no tópico usado pelo projeto.
        """
        if mqtt is None:
            print(
                "[MQTT] Biblioteca paho-mqtt não instalada. "
                "Publicação MQTT desativada."
            )
            return

        while not self.encerramento.is_set():
            cliente_mqtt = None

            try:
                if hasattr(mqtt, "CallbackAPIVersion"):
                    cliente_mqtt = mqtt.Client(
                        mqtt.CallbackAPIVersion.VERSION2
                    )
                else:
                    cliente_mqtt = mqtt.Client()

                cliente_mqtt.connect(
                    BROKER_MQTT,
                    PORTA_MQTT,
                    60
                )

                cliente_mqtt.loop_start()

                print(
                    f"[MQTT] Conectado a "
                    f"{BROKER_MQTT}:{PORTA_MQTT}."
                )

                while not self.encerramento.is_set():
                    with self.lock:
                        regiao_a_disponivel = (
                                self.malha_climatica[
                                    "Regiao_A"
                                ] is not None
                        )

                        payload = json.dumps(
                            self.malha_climatica,
                            ensure_ascii=False
                        )

                    if regiao_a_disponivel:
                        cliente_mqtt.publish(
                            TOPICO_TELEMETRIA,
                            payload
                        )

                        print(
                            "[MQTT] Malha climática "
                            "publicada."
                        )

                    if self.encerramento.wait(
                            INTERVALO_MQTT
                    ):
                        break

            except OSError as erro:
                print(
                    f"[MQTT] Broker indisponível: {erro}. "
                    "Nova tentativa em 5 segundos."
                )

                if self.encerramento.wait(5):
                    break

            except Exception as erro:
                print(
                    f"[MQTT] Falha inesperada: {erro}. "
                    "Nova tentativa em 5 segundos."
                )

                if self.encerramento.wait(5):
                    break

            finally:
                if cliente_mqtt is not None:
                    try:
                        cliente_mqtt.loop_stop()
                        cliente_mqtt.disconnect()
                    except Exception:
                        pass

    def iniciar(self) -> None:
        tarefas = [
            (
                self.monitorar_clima_local,
                "radar-a-clima"
            ),
            (
                self.servidor_gossip,
                "radar-a-servidor"
            ),
            (
                self.cliente_gossip_loop,
                "radar-a-cliente"
            ),
            (
                self.publicar_mqtt,
                "radar-a-mqtt"
            )
        ]

        for tarefa, nome in tarefas:
            thread = threading.Thread(
                target=tarefa,
                daemon=True,
                name=nome
            )

            thread.start()

        print(
            "[RADAR A] Todas as tarefas distribuídas "
            "foram iniciadas."
        )

        try:
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print(
                "\n[SHUTDOWN] Encerrando Radar "
                "Climático A..."
            )

            self.encerramento.set()
            time.sleep(1)


if __name__ == "__main__":
    radar = RadarClimaticoA()
    radar.iniciar()