import requests

URL_METAR = "https://aviationweather.gov/api/data/metar"

def buscar_metar(icao: str) -> dict:
    icao = icao.strip().upper()

    if len(icao) != 4 or not icao.isalpha():
        return {
            "icao": icao,
            "erro": "Código ICAO inválido. Informe exatamente quatro letras."
        }

    params = {
        "ids": icao,
        "format": "json",
        "hours": 4
    }

    headers = {
        "User-Agent": "Sistemas-Distribuidos-Avionica/1.0"
    }

    try:
        resposta = requests.get(
            URL_METAR,
            params=params,
            headers=headers,
            timeout=(5, 15)
        )

        if resposta.status_code == 204:
            return {
                "icao": icao,
                "erro": "Nenhum METAR recente disponível para esse aeroporto."
            }

        resposta.raise_for_status()

        dados = resposta.json()

        if not dados:
            return {
                "icao": icao,
                "erro": "Nenhum METAR encontrado para esse aeroporto."
            }

        metar_mais_recente = max(
            dados,
            key=lambda metar: metar.get("obsTime", 0)
        )

        return metar_mais_recente



    except requests.exceptions.Timeout:
        return {
            "icao": icao,
            "erro": "A consulta climática excedeu o tempo limite."
        }

    except requests.exceptions.ConnectionError:
        return {
            "icao": icao,
            "erro": "Não foi possível conectar ao serviço meteorológico."
        }

    except requests.exceptions.HTTPError as erro:
        return {
            "icao": icao,
            "erro": f"Erro HTTP na consulta climática: {erro}"
        }

    except ValueError:
        return {
            "icao": icao,
            "erro": "A API retornou dados em formato inválido."
        }
    except requests.exceptions.RequestException as erro:
        return {
            "icao": icao,
            "erro": f"Falha durante a consulta climática: {erro}"
        }

def exibir_clima(titulo, dados):
    print(f"\n===== {titulo} =====")

    if "erro" in dados:
        print(f"Aeroporto: {dados.get('aeroporto')}")
        print(f"Erro: {dados.get('erro')}")
        return

    print(f"Aeroporto: {dados.get('aeroporto')} - {dados.get('nome')}")
    print(f"Temperatura: {dados.get('temperatura')}°C")
    print(
        f"Vento: {dados.get('vento_direcao')}° "
        f"a {dados.get('vento_velocidade')} kt"
    )
    print(f"Visibilidade: {dados.get('visibilidade')}")
    print(f"Condição de voo: {dados.get('condicao_voo')}")
    print(f"Fenômeno: {dados.get('fenomeno')}")
    print(f"METAR: {dados.get('metar')}")

def buscar_clima_voo(origem: str, destino: str) -> dict:
    return {
        "origem": buscar_metar(origem),
        "destino": buscar_metar(destino)
    }

def traduzir_fenomeno(codigo):
    fenomenos = {
        "FG": "nevoeiro",
        "BR": "névoa/neblina",
        "RA": "chuva",
        "DZ": "garoa",
        "TS": "trovoada",
        "HZ": "névoa seca",
        "SN": "neve",
        "GR": "granizo",
        "SH": "pancadas",
        "VC": "nas proximidades"
    }

    if not codigo:
        return "Nenhum fenômeno identificado"

    return fenomenos.get(codigo, codigo)

def resumir_clima(dados):
    if "erro" in dados:
        return {
            "aeroporto": dados.get("icao", "Desconhecido"),
            "erro": dados["erro"]
        }

    fenomeno_codigo = dados.get("wxString", "")

    return {
        "aeroporto": dados.get("icaoId"),
        "nome": dados.get("name"),
        "temperatura": dados.get("temp"),
        "vento_direcao": dados.get("wdir"),
        "vento_velocidade": dados.get("wspd"),
        "visibilidade": dados.get("visib"),
        "condicao_voo": dados.get("fltCat"),
        "fenomeno": traduzir_fenomeno(fenomeno_codigo),
        "metar": dados.get("rawOb")
    }

def classificar_risco(dados):
    if "erro" in dados:
        return "Indisponível"

    categoria = dados.get("fltCat")

    if categoria in ["LIFR", "IFR"]:
        return "Alto"

    if categoria == "MVFR":
        return "Médio"

    if categoria == "VFR":
        return "Baixo"

    return "Não classificado"

if __name__ == "__main__":
    clima = buscar_clima_voo("SBRF", "EGLL")

    origem_resumida = resumir_clima(clima["origem"])
    destino_resumido = resumir_clima(clima["destino"])

    exibir_clima("CLIMA NA ORIGEM", origem_resumida)
    print(f"Risco: {classificar_risco(clima['origem'])}")

    exibir_clima("CLIMA NO DESTINO", destino_resumido)
    print(f"Risco: {classificar_risco(clima['destino'])}")