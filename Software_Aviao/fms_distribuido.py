import argparse
import json
import math
import os
import threading
import time
from typing import Any

import paho.mqtt.client as mqtt
import requests

from cache_aeroportos import CacheAeroportosSQLite


BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
PORTA = int(os.getenv("MQTT_PORT", "1883"))

TOPICO_ROTA_CMD = "avionica/comandos/rota"
TOPICO_VOO = "avionica/sensores/voo"
TOPICO_FMS_DADOS = "avionica/fms/dados"

API_KEY = os.getenv("FMS_API_KEY") or os.getenv("API_NINJAS_KEY")
URL_API_AEROPORTOS = "https://api.api-ninjas.com/v1/airports"


class FlightManagementSystem:
    def __init__(self):
        self.velocidade_mach = 0.80
        self.cache_aeroportos = CacheAeroportosSQLite()

        self.rota_atual: dict[str, Any] = {
            "origem": "N/A",
            "destino": "N/A",
            "distancia_nm": 0.0,
            "eta_minutos": 0,
            "status": "AGUARDANDO",
            "fonte_origem": None,
            "fonte_destino": None,
        }

        if hasattr(mqtt, "CallbackAPIVersion"):
            self.cliente = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2
            )
        else:
            self.cliente = mqtt.Client()

        self.cliente.on_connect = self.ao_conectar
        self.cliente.on_message = self.ao_receber_mensagem

        print(
            "[FMS] Cache SQLite iniciado com "
            f"{self.cache_aeroportos.quantidade()} aeroportos."
        )

    @staticmethod
    def validar_icao(icao: str) -> bool:
        return len(icao) == 4 and icao.isalpha()

    @staticmethod
    def calcular_distancia(
            lat1: float,
            lon1: float,
            lat2: float,
            lon2: float,
    ) -> float:
        """Calcula a distância em milhas náuticas pela fórmula de Haversine."""
        raio_terra_nm = 3440.065
        diferenca_latitude = math.radians(lat2 - lat1)
        diferenca_longitude = math.radians(lon2 - lon1)

        calculo = (
                math.sin(diferenca_latitude / 2) ** 2
                + math.cos(math.radians(lat1))
                * math.cos(math.radians(lat2))
                * math.sin(diferenca_longitude / 2) ** 2
        )

        angulo = 2 * math.atan2(
            math.sqrt(calculo),
            math.sqrt(1 - calculo),
        )

        return raio_terra_nm * angulo

    def buscar_aeroporto_api(
            self,
            icao: str,
    ) -> dict[str, Any] | None:
        if not API_KEY:
            print(
                f"[FMS] API não configurada para {icao}. "
                "Consultando cache SQLite."
            )
            return None

        try:
            resposta = requests.get(
                URL_API_AEROPORTOS,
                params={"icao": icao},
                headers={"X-Api-Key": API_KEY},
                timeout=(3, 5),
            )
            resposta.raise_for_status()
            dados = resposta.json()

            if not dados:
                print(
                    f"[FMS] A API não encontrou o aeroporto {icao}. "
                    "Consultando cache SQLite."
                )
                return None

            aeroporto_api = dados[0]
            latitude = float(aeroporto_api["latitude"])
            longitude = float(aeroporto_api["longitude"])

            aeroporto = {
                "icao": icao,
                "nome": aeroporto_api.get("name"),
                "cidade": aeroporto_api.get("city"),
                "latitude": latitude,
                "longitude": longitude,
                "fonte": "API_EXTERNA",
            }

            self.cache_aeroportos.salvar_ou_atualizar(
                icao=icao,
                nome=aeroporto["nome"],
                cidade=aeroporto["cidade"],
                latitude=latitude,
                longitude=longitude,
                fonte="API_EXTERNA",
            )

            print(
                f"[FMS] Coordenadas de {icao} obtidas pela API "
                "e atualizadas no cache."
            )
            return aeroporto

        except (
                requests.RequestException,
                ValueError,
                KeyError,
                TypeError,
        ) as erro:
            print(
                f"[FMS] Falha na API para {icao}: {erro}. "
                "Consultando cache SQLite."
            )
            return None

    def buscar_aeroporto_cache(
            self,
            icao: str,
    ) -> dict[str, Any] | None:
        aeroporto = self.cache_aeroportos.buscar(icao)

        if aeroporto:
            print(
                f"[FMS] Aeroporto {icao} recuperado do cache SQLite. "
                f"Última atualização: {aeroporto['atualizado_em']}."
            )
            aeroporto["fonte"] = "CACHE_SQLITE"
            return aeroporto

        print(
            f"[FMS] Aeroporto {icao} não existe no cache SQLite."
        )
        return None

    def buscar_aeroporto(
            self,
            icao: str,
    ) -> dict[str, Any] | None:
        codigo = icao.strip().upper()

        aeroporto_api = self.buscar_aeroporto_api(codigo)
        if aeroporto_api:
            return aeroporto_api

        return self.buscar_aeroporto_cache(codigo)

    def processar_rota(
            self,
            origem: str,
            destino: str,
    ) -> dict[str, Any] | None:
        origem = origem.strip().upper()
        destino = destino.strip().upper()

        if not self.validar_icao(origem) or not self.validar_icao(destino):
            print(
                "[FMS] Origem e destino devem possuir quatro letras ICAO."
            )
            return None

        print(f"[FMS] Calculando rota {origem} -> {destino}...")

        aeroporto_origem = self.buscar_aeroporto(origem)
        aeroporto_destino = self.buscar_aeroporto(destino)

        if aeroporto_origem is None or aeroporto_destino is None:
            print(
                "[FMS] Não foi possível localizar um dos aeroportos "
                "nem pela API nem pelo cache."
            )
            return None

        distancia = self.calcular_distancia(
            float(aeroporto_origem["latitude"]),
            float(aeroporto_origem["longitude"]),
            float(aeroporto_destino["latitude"]),
            float(aeroporto_destino["longitude"]),
        )

        velocidade_knots = self.velocidade_mach * 600.0
        eta_minutos = round((distancia / velocidade_knots) * 60)

        fontes = {
            aeroporto_origem["fonte"],
            aeroporto_destino["fonte"],
        }
        status = (
            "ONLINE"
            if fontes == {"API_EXTERNA"}
            else "OFFLINE_FALLBACK"
        )

        self.rota_atual = {
            "origem": origem,
            "destino": destino,
            "distancia_nm": round(distancia, 1),
            "eta_minutos": eta_minutos,
            "status": status,
            "fonte_origem": aeroporto_origem["fonte"],
            "fonte_destino": aeroporto_destino["fonte"],
        }

        print(f"[FMS] Rota calculada: {origem} -> {destino}")
        print(f"[FMS] Distância: {distancia:.1f} NM")
        print(f"[FMS] ETA: {eta_minutos} minutos")
        print(f"[FMS] Status: {status}")

        return self.rota_atual.copy()

    def ao_conectar(
            self,
            cliente,
            dados_usuario,
            flags,
            codigo_retorno,
            propriedades=None,
    ) -> None:
        print("[FMS] Conectado à rede aviônica MQTT.")
        cliente.subscribe(
            [
                (TOPICO_ROTA_CMD, 0),
                (TOPICO_VOO, 0),
            ]
        )

    def ao_receber_mensagem(
            self,
            cliente,
            dados_usuario,
            mensagem,
    ) -> None:
        try:
            pacote = json.loads(
                mensagem.payload.decode("utf-8")
            )

            if mensagem.topic == TOPICO_VOO:
                velocidade = pacote.get(
                    "dados",
                    {},
                ).get("velocidade_mach")

                if velocidade is not None:
                    self.velocidade_mach = float(velocidade)

            elif mensagem.topic == TOPICO_ROTA_CMD:
                origem = str(
                    pacote.get("origem", "")
                ).strip().upper()
                destino = str(
                    pacote.get("destino", "")
                ).strip().upper()

                threading.Thread(
                    target=self.processar_rota,
                    args=(origem, destino),
                    daemon=True,
                ).start()

        except (
                json.JSONDecodeError,
                TypeError,
                ValueError,
        ) as erro:
            print(f"[FMS] Mensagem MQTT inválida: {erro}")

    def criar_payload_rota(self) -> dict[str, Any]:
        velocidade_knots = self.velocidade_mach * 600.0
        eta_minutos = self.rota_atual["eta_minutos"]

        if (
                self.rota_atual["distancia_nm"] > 0
                and velocidade_knots > 0
        ):
            eta_minutos = round(
                (
                        self.rota_atual["distancia_nm"]
                        / velocidade_knots
                )
                * 60
            )

        return {
            "dados": {
                "rota_texto": (
                    f"{self.rota_atual['origem']} -> "
                    f"{self.rota_atual['destino']}"
                ),
                "origem": self.rota_atual["origem"],
                "destino": self.rota_atual["destino"],
                "distancia_nm": round(
                    self.rota_atual["distancia_nm"],
                    1,
                ),
                "eta_minutos": eta_minutos,
                "status": self.rota_atual["status"],
                "fonte_origem": self.rota_atual["fonte_origem"],
                "fonte_destino": self.rota_atual["fonte_destino"],
            }
        }

    def iniciar(self) -> None:
        print(
            f"[FMS] Conectando ao broker {BROKER}:{PORTA}..."
        )
        self.cliente.connect(BROKER, PORTA, 60)
        self.cliente.loop_start()

        try:
            while True:
                self.cliente.publish(
                    TOPICO_FMS_DADOS,
                    json.dumps(
                        self.criar_payload_rota(),
                        ensure_ascii=False,
                    ),
                )
                time.sleep(2)

        except KeyboardInterrupt:
            print("\n[FMS] Encerrando módulo.")

        finally:
            self.cliente.loop_stop()
            self.cliente.disconnect()


def executar_teste_local(
        fms: FlightManagementSystem,
        origem: str,
        destino: str,
) -> None:
    resultado = fms.processar_rota(origem, destino)

    if resultado:
        print("\n========== RESULTADO FMS ==========")
        print(
            json.dumps(
                resultado,
                indent=4,
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FMS de Planejamento de Rotas"
    )
    parser.add_argument(
        "--teste-local",
        nargs=2,
        metavar=("ORIGEM", "DESTINO"),
        help=(
            "Calcula uma rota sem iniciar MQTT. "
            "Exemplo: --teste-local SBRF SBGR"
        ),
    )
    argumentos = parser.parse_args()

    sistema_fms = FlightManagementSystem()

    if argumentos.teste_local:
        executar_teste_local(
            sistema_fms,
            argumentos.teste_local[0],
            argumentos.teste_local[1],
        )
    else:
        sistema_fms.iniciar()