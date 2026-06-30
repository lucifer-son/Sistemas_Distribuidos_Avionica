import json
import os
import threading
import time
from typing import Any

from servico_clima import buscar_metar, resumir_clima, classificar_risco


AEROPORTO_REGIAO_A = os.getenv("RADAR_A_ICAO", "SBRF")


class RadarClimaticoA:
    def __init__(self):
        self.malha_climatica: dict[str, dict[str, Any] | None] = {
            "Regiao_A": None,
            "Regiao_B": None
        }

        self.lock = threading.Lock()

    def extrair_timestamp(
            self,
            pacote: dict[str, Any] | None
    ) -> int:
        """
        Extrai o timestamp do identificador da mensagem.

        Exemplo:
        radA_1782799200000
        """
        if not pacote or "id_mensagem" not in pacote:
            return 0

        try:
            return int(pacote["id_mensagem"].split("_")[1])
        except (IndexError, TypeError, ValueError):
            return 0

    def mesclar_dados(
            self,
            regiao: str,
            novo_pacote: dict[str, Any] | None
    ) -> None:
        """
        Mantém somente o pacote mais recente de cada região.

        Essa regra será utilizada posteriormente na consistência eventual
        entre os radares A e B.
        """
        if regiao not in self.malha_climatica:
            print(f"[ERRO] Região desconhecida: {regiao}")
            return

        if not novo_pacote:
            return

        with self.lock:
            pacote_atual = self.malha_climatica[regiao]

            timestamp_atual = self.extrair_timestamp(pacote_atual)
            timestamp_novo = self.extrair_timestamp(novo_pacote)

            if timestamp_novo > timestamp_atual:
                self.malha_climatica[regiao] = novo_pacote

                print(
                    f"[RADAR A] Malha atualizada para {regiao}. "
                    f"ID: {novo_pacote['id_mensagem']}"
                )

    def classificar_turbulencia(
            self,
            dados_brutos: dict,
            risco: str
    ) -> str:
        vento = dados_brutos.get("wspd") or 0
        fenomeno = str(dados_brutos.get("wxString") or "").upper()

        if risco == "Alto" or "TS" in fenomeno or vento >= 30:
            return "SEVERA"

        if risco == "Médio" or vento >= 20:
            return "MODERADA"

        return "LEVE"

    def identificar_clima(
            self,
            dados_brutos: dict,
            risco: str
    ) -> str:
        fenomeno = str(dados_brutos.get("wxString") or "").upper()
        categoria = str(dados_brutos.get("fltCat") or "").upper()

        if "TS" in fenomeno or risco == "Alto":
            return "TEMPESTADE"

        if fenomeno or categoria in ["MVFR", "IFR", "LIFR"]:
            return "NUVENS"

        return "CÉU LIMPO"

    def gerar_mensagem_atc(
            self,
            clima: str,
            turbulencia: str
    ) -> str:
        if clima == "TEMPESTADE":
            return "Evite formações meteorológicas severas"

        if turbulencia == "MODERADA":
            return "Possibilidade de turbulência moderada"

        return "Rota livre"

    def gerar_pacote_regiao_a(self) -> dict | None:
        dados_brutos = buscar_metar(AEROPORTO_REGIAO_A)

        if "erro" in dados_brutos:
            print(
                f"[ERRO CLIMA] {AEROPORTO_REGIAO_A}: "
                f"{dados_brutos['erro']}"
            )
            return None

        dados_resumidos = resumir_clima(dados_brutos)
        risco = classificar_risco(dados_brutos)

        clima = self.identificar_clima(dados_brutos, risco)

        turbulencia = self.classificar_turbulencia(
            dados_brutos,
            risco
        )

        pacote_local = {
            "id_mensagem": f"radA_{int(time.time() * 1000)}",
            "dados": {
                "aeroporto": AEROPORTO_REGIAO_A,
                "nome_aeroporto": dados_resumidos.get("nome"),
                "vento_knots": dados_brutos.get("wspd"),
                "turbulencia": turbulencia,
                "radar_clima": clima,
                "temp_externa_c": dados_brutos.get("temp"),
                "qnh_hpa": dados_brutos.get("altim"),
                "condicao_voo": dados_brutos.get("fltCat"),
                "visibilidade": dados_brutos.get("visib"),
                "fenomeno": dados_resumidos.get("fenomeno"),
                "risco": risco,
                "atc_msg": self.gerar_mensagem_atc(
                    clima,
                    turbulencia
                ),
                "metar": dados_brutos.get("rawOb")
            }
        }

        return pacote_local

    def atualizar_clima_local(self) -> None:
        pacote_local = self.gerar_pacote_regiao_a()

        if pacote_local:
            self.mesclar_dados(
                "Regiao_A",
                pacote_local
            )

    def exibir_malha_climatica(self) -> None:
        with self.lock:
            malha_copia = dict(self.malha_climatica)

        print("\n========== RADAR CLIMÁTICO A ==========")
        print(
            json.dumps(
                malha_copia,
                indent=4,
                ensure_ascii=False
            )
        )

    def iniciar_teste_local(self) -> None:
        print(
            f"[RADAR A] Consultando clima real de "
            f"{AEROPORTO_REGIAO_A}..."
        )

        self.atualizar_clima_local()
        self.exibir_malha_climatica()


if __name__ == "__main__":
    radar = RadarClimaticoA()
    radar.iniciar_teste_local()