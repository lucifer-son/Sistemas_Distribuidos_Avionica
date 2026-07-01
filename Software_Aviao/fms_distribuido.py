import argparse
import json
import math
import os
import threading
import time
from pathlib import Path

import paho.mqtt.client as mqtt
import requests


# Configurações MQTT
BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
PORTA = int(os.getenv("MQTT_PORT", "1883"))

TOPICO_ROTA_CMD = "avionica/comandos/rota"
TOPICO_VOO = "avionica/sensores/voo"
TOPICO_FMS_DADOS = "avionica/fms/dados"


# Configuração da API externa
API_KEY = (
        os.getenv("FMS_API_KEY")
        or os.getenv("API_NINJAS_KEY")
)


# Arquivo local usado em caso de falha da API
CAMINHO_AEROPORTOS_FALLBACK = (
        Path(__file__).resolve().parent
        / "aeroportos_fallback.json"
)


def carregar_aeroportos_fallback() -> dict:
    try:
        with CAMINHO_AEROPORTOS_FALLBACK.open(
                "r",
                encoding="utf-8"
        ) as arquivo:
            dados = json.load(arquivo)

        print(
            f"[FMS] Base local carregada: "
            f"{len(dados)} aeroportos."
        )

        return dados

    except FileNotFoundError:
        print(
            "[FMS] Arquivo aeroportos_fallback.json "
            "não foi encontrado."
        )
        return {}

    except json.JSONDecodeError as erro:
        print(
            f"[FMS] JSON de aeroportos inválido: {erro}"
        )
        return {}

    except OSError as erro:
        print(
            f"[FMS] Não foi possível ler a base local: "
            f"{erro}"
        )
        return {}


class FlightManagementSystem:
    def __init__(self):
        self.velocidade_mach = 0.80

        self.aeroportos_fallback = (
            carregar_aeroportos_fallback()
        )

        self.rota_atual = {
            "origem": "N/A",
            "destino": "N/A",
            "distancia_nm": 0.0,
            "eta_minutos": 0,
            "status": "AGUARDANDO",
            "fonte_origem": None,
            "fonte_destino": None
        }

        # Evita o aviso de API antiga nas versões recentes do paho-mqtt.
        if hasattr(mqtt, "CallbackAPIVersion"):
            self.cliente = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2
            )
        else:
            self.cliente = mqtt.Client()

        self.cliente.on_connect = self.ao_conectar
        self.cliente.on_message = (
            self.ao_receber_mensagem
        )

    def calcular_distancia(
            self,
            lat1: float,
            lon1: float,
            lat2: float,
            lon2: float
    ) -> float:
        """
        Calcula a distância entre dois aeroportos usando
        a fórmula de Haversine.

        O resultado é retornado em milhas náuticas.
        """
        raio_terra_nm = 3440.065

        diferenca_latitude = math.radians(
            lat2 - lat1
        )

        diferenca_longitude = math.radians(
            lon2 - lon1
        )

        calculo = (
                math.sin(diferenca_latitude / 2) ** 2
                + math.cos(math.radians(lat1))
                * math.cos(math.radians(lat2))
                * math.sin(
            diferenca_longitude / 2
        ) ** 2
        )

        angulo = 2 * math.atan2(
            math.sqrt(calculo),
            math.sqrt(1 - calculo)
        )

        return raio_terra_nm * angulo

    def buscar_coordenadas_api(
            self,
            icao: str
    ) -> tuple[float, float] | None:
        if not API_KEY:
            print(
                f"[FMS] Chave da API não configurada. "
                f"Usando fallback para {icao}."
            )
            return None

        url = (
            "https://api.api-ninjas.com/v1/airports"
            f"?icao={icao}"
        )

        try:
            resposta = requests.get(
                url,
                headers={
                    "X-Api-Key": API_KEY
                },
                timeout=(3, 5)
            )

            resposta.raise_for_status()
            dados = resposta.json()

            if not dados:
                return None

            aeroporto = dados[0]

            return (
                float(aeroporto["latitude"]),
                float(aeroporto["longitude"])
            )

        except (
                requests.RequestException,
                ValueError,
                KeyError,
                TypeError
        ) as erro:
            print(
                f"[FMS] Falha na API para {icao}: "
                f"{erro}"
            )
            return None

    def buscar_coordenadas_fallback(
            self,
            icao: str
    ) -> tuple[float, float] | None:
        aeroporto = self.aeroportos_fallback.get(
            icao
        )

        if not aeroporto:
            return None

        try:
            return (
                float(aeroporto["latitude"]),
                float(aeroporto["longitude"])
            )

        except (
                KeyError,
                TypeError,
                ValueError
        ):
            return None

    def buscar_coordenadas(
            self,
            icao: str
    ) -> tuple[
        float | None,
        float | None,
        str
    ]:
        icao = icao.strip().upper()

        coordenadas_api = (
            self.buscar_coordenadas_api(icao)
        )

        if coordenadas_api:
            latitude, longitude = coordenadas_api

            return (
                latitude,
                longitude,
                "API_EXTERNA"
            )

        coordenadas_fallback = (
            self.buscar_coordenadas_fallback(icao)
        )

        if coordenadas_fallback:
            latitude, longitude = (
                coordenadas_fallback
            )

            return (
                latitude,
                longitude,
                "FALLBACK_LOCAL"
            )

        return (
            None,
            None,
            "NAO_ENCONTRADO"
        )

    def processar_rota(
            self,
            origem: str,
            destino: str
    ) -> dict | None:
        origem = origem.strip().upper()
        destino = destino.strip().upper()

        if (
                len(origem) != 4
                or not origem.isalpha()
                or len(destino) != 4
                or not destino.isalpha()
        ):
            print(
                "[FMS] Origem e destino devem possuir "
                "quatro letras ICAO."
            )
            return None

        print(
            f"[FMS] Calculando rota "
            f"{origem} -> {destino}..."
        )

        lat1, lon1, fonte_origem = (
            self.buscar_coordenadas(origem)
        )

        lat2, lon2, fonte_destino = (
            self.buscar_coordenadas(destino)
        )

        if None in (
                lat1,
                lon1,
                lat2,
                lon2
        ):
            print(
                "[FMS] Não foi possível localizar "
                "um dos aeroportos."
            )
            return None

        distancia = self.calcular_distancia(
            lat1,
            lon1,
            lat2,
            lon2
        )

        velocidade_knots = (
                self.velocidade_mach * 600.0
        )

        eta_minutos = round(
            (
                    distancia
                    / velocidade_knots
            )
            * 60
        )

        if (
                fonte_origem == "API_EXTERNA"
                and fonte_destino == "API_EXTERNA"
        ):
            status = "ONLINE"
        else:
            status = "OFFLINE_FALLBACK"

        self.rota_atual = {
            "origem": origem,
            "destino": destino,
            "distancia_nm": round(
                distancia,
                1
            ),
            "eta_minutos": eta_minutos,
            "status": status,
            "fonte_origem": fonte_origem,
            "fonte_destino": fonte_destino
        }

        print(
            f"[FMS] Rota calculada: "
            f"{origem} -> {destino}"
        )

        print(
            f"[FMS] Distância: "
            f"{distancia:.1f} NM"
        )

        print(
            f"[FMS] ETA: "
            f"{eta_minutos} minutos"
        )

        print(
            f"[FMS] Status: {status}"
        )

        return self.rota_atual.copy()

    def ao_conectar(
            self,
            cliente,
            dados_usuario,
            flags,
            codigo_retorno,
            propriedades=None
    ):
        print(
            "[FMS] Conectado à rede aviônica MQTT."
        )

        cliente.subscribe(
            [
                (TOPICO_ROTA_CMD, 0),
                (TOPICO_VOO, 0)
            ]
        )

    def ao_receber_mensagem(
            self,
            cliente,
            dados_usuario,
            mensagem
    ):
        try:
            pacote = json.loads(
                mensagem.payload.decode("utf-8")
            )

            if mensagem.topic == TOPICO_VOO:
                dados_voo = pacote.get(
                    "dados",
                    {}
                )

                velocidade = dados_voo.get(
                    "velocidade_mach"
                )

                if velocidade is not None:
                    self.velocidade_mach = float(
                        velocidade
                    )

            elif mensagem.topic == TOPICO_ROTA_CMD:
                origem = str(
                    pacote.get("origem", "")
                ).strip().upper()

                destino = str(
                    pacote.get("destino", "")
                ).strip().upper()

                thread_rota = threading.Thread(
                    target=self.processar_rota,
                    args=(origem, destino),
                    daemon=True
                )

                thread_rota.start()

        except (
                json.JSONDecodeError,
                TypeError,
                ValueError
        ) as erro:
            print(
                f"[FMS] Mensagem MQTT inválida: "
                f"{erro}"
            )

    def iniciar(self):
        print(
            f"[FMS] Conectando ao broker "
            f"{BROKER}:{PORTA}..."
        )

        self.cliente.connect(
            BROKER,
            PORTA,
            60
        )

        self.cliente.loop_start()

        try:
            while True:
                velocidade_knots = (
                        self.velocidade_mach * 600.0
                )

                eta_minutos = (
                    self.rota_atual[
                        "eta_minutos"
                    ]
                )

                if (
                        self.rota_atual[
                            "distancia_nm"
                        ] > 0
                        and velocidade_knots > 0
                ):
                    eta_minutos = round(
                        (
                                self.rota_atual[
                                    "distancia_nm"
                                ]
                                / velocidade_knots
                        )
                        * 60
                    )

                pacote = {
                    "dados": {
                        "rota_texto": (
                            f"{self.rota_atual['origem']} "
                            f"-> "
                            f"{self.rota_atual['destino']}"
                        ),
                        "origem": (
                            self.rota_atual["origem"]
                        ),
                        "destino": (
                            self.rota_atual["destino"]
                        ),
                        "distancia_nm": round(
                            self.rota_atual[
                                "distancia_nm"
                            ],
                            1
                        ),
                        "eta_minutos": eta_minutos,
                        "status": (
                            self.rota_atual["status"]
                        ),
                        "fonte_origem": (
                            self.rota_atual[
                                "fonte_origem"
                            ]
                        ),
                        "fonte_destino": (
                            self.rota_atual[
                                "fonte_destino"
                            ]
                        )
                    }
                }

                self.cliente.publish(
                    TOPICO_FMS_DADOS,
                    json.dumps(
                        pacote,
                        ensure_ascii=False
                    )
                )

                time.sleep(2)

        except KeyboardInterrupt:
            print(
                "\n[FMS] Encerrando módulo."
            )

        finally:
            self.cliente.loop_stop()
            self.cliente.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "FMS de Planejamento de Rotas"
        )
    )

    parser.add_argument(
        "--teste-local",
        nargs=2,
        metavar=(
            "ORIGEM",
            "DESTINO"
        ),
        help=(
            "Calcula uma rota sem iniciar MQTT. "
            "Exemplo: "
            "--teste-local SBRF SBGR"
        )
    )

    argumentos = parser.parse_args()

    fms = FlightManagementSystem()

    if argumentos.teste_local:
        origem, destino = (
            argumentos.teste_local
        )

        resultado = fms.processar_rota(
            origem,
            destino
        )

        if resultado:
            print(
                "\n========== RESULTADO FMS =========="
            )

            print(
                json.dumps(
                    resultado,
                    indent=4,
                    ensure_ascii=False
                )
            )

    else:
        fms.iniciar()