import requests

def buscar_metar(icao: str) -> dict:
    url = "https://aviationweather.gov/api/data/metar"
    params = {"ids": icao,
    "format": "json"
    }

    resposta = requests.get(url, params=params, timeout= 10)
    resposta.raise_for_status()

    dados = resposta.json()

    if not dados:
        return {
            "icao": icao,
            "erro": "Nenhum METAR encontrado para esse aeroporto."
        }
    return dados[0]

def exibir_clima(titulo, dados):
    print(f"\n===== {titulo} =====")
    print(f"Aeroporto: {dados.get('aeroporto')} - {dados.get('nome')}")
    print(f"Temperatura: {dados.get('temperatura')}°C")
    print(f"Vento: {dados.get('vento_direcao')}° a {dados.get('vento_velocidade')} kt")
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
    categoria = dados.get("fltCat")

    if categoria in ["LIFR", "IFR"]:
        return "Alto"

    if categoria == "MVFR":
        return "Médio"

    if categoria == "VFR":
        return "Baixo"

    return "Desconhecido"

if __name__ == "__main__":
    clima = buscar_clima_voo("SBRF", "EGLL")

    origem_resumida = resumir_clima(clima["origem"])
    destino_resumido = resumir_clima(clima["destino"])

    exibir_clima("CLIMA NA ORIGEM", origem_resumida)
    print(f"Risco: {classificar_risco(clima['origem'])}")

    exibir_clima("CLIMA NO DESTINO", destino_resumido)
    print(f"Risco: {classificar_risco(clima['destino'])}")