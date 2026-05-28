# 🐍 Plano 05 — API Python: Como Funciona Hoje e o que Deve Melhorar

> **Diretório:** `Software_Aviao/`  
> **Protocolo:** MQTT via `paho-mqtt`  
> **Broker:** Eclipse Mosquitto (container Docker)  
> **Análise feita sobre todos os 14 arquivos Python do projeto**

---

## 🗺️ Mapa Completo do Sistema — Como Tudo Se Conecta Hoje

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        BARRAMENTO MQTT: avionica/#                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  PUBLICADORES (sensores que geram dados)                                     ║
║  ┌─────────────────┐  tópico: avionica/sensores/voo                          ║
║  │ sensores_voo.py │──────────────────────────────────────────────────►      ║
║  │ (loop 1s)       │  Publica: combustivel, altitude, mach                   ║
║  │ + escuta cmds   │  Escuta:  avionica/comandos/velocidade                  ║
║  └─────────────────┘                                                         ║
║                                                                              ║
║  ┌─────────────────┐  tópico: avionica/sensores/freios                       ║
║  │ sensor_freio.py │──────────────────────────────────────────────────►      ║
║  │ (loop 3s)       │  Publica: pressao hidráulica (Canal A + Canal B)        ║
║  │ + id_mensagem   │  Estratégia de deduplicação por UUID                    ║
║  └─────────────────┘                                                         ║
║                                                                              ║
║  ┌─────────────────┐  tópico: avionica/radar                                 ║
║  │ radar_externo.py│──────────────────────────────────────────────────►      ║
║  │ (loop 3s)       │  Publica: vento, turbulencia, clima, temp, qnh, atc     ║
║  └─────────────────┘                                                         ║
║                                                                              ║
║  ┌─────────────────┐  tópico: avionica/navegacao                             ║
║  │ computador_     │──────────────────────────────────────────────────►      ║
║  │ navegacao.py    │  Publica: proa, vs_fpm, piloto_auto, waypoint, eta      ║
║  │ (loop 3s)       │                                                         ║
║  └─────────────────┘                                                         ║
║                                                                              ║
║  ┌─────────────────┐  tópico: avionica/sensores/waic                         ║
║  │ lider_waic.py   │──────────────────────────────────────────────────►      ║
║  │ (loop 2s)       │  Publica: pressao_motor, temperatura (agregado)         ║
║  └─────────────────┘                                                         ║
║                                                                              ║
║  ┌─────────────────┐  tópicos: avionica/sensores/motor/A|B|C                 ║
║  │ sensor_motor.py │──────────────────────────────────────────────────►      ║
║  │ (loop 1s)       │  Publica: pressao do motor (pode ser sabotado)          ║
║  │ (x3 instâncias) │  Escuta:  avionica/comandos/falhas/sensor_A|B|C         ║
║  └─────────────────┘                                                         ║
║                                                                              ║
║  PROCESSADORES (leem e reagem)                                               ║
║  ┌─────────────────┐  Escuta: avionica/sensores/motor/#                      ║
║  │ consenso_motor  │  Algoritmo TMR (mediana de 3 valores)                   ║
║  │ .py (loop 1s)   │  Publica: avionica/sensores/waic (valor verificado)     ║
║  └─────────────────┘                                                         ║
║                                                                              ║
║  ┌─────────────────┐  Escuta: avionica/radar                                 ║
║  │ computador_     │  Lógica: TEMPESTADE + temp<0 → Liga anti-gelo           ║
║  │ automacao.py    │  Publica: avionica/sistemas/anti_ice                    ║
║  └─────────────────┘                                                         ║
║                                                                              ║
║  ┌─────────────────┐  Escuta: avionica/fms/dados + avionica/sensores/voo     ║
║  │ fms_distribuido │  Lógica: Calcula rota via API Ninjas (Haversine)        ║
║  │ .py (loop 2s)   │  Publica: avionica/fms/dados                            ║
║  └─────────────────┘                                                         ║
║                                                                              ║
║  CONSUMIDORES PUROS (apenas leem)                                            ║
║  ┌─────────────────┐  Escuta: avionica/# (tudo)                              ║
║  │ caixa_preta.py  │  Grava: flight_data_recorder.csv (CSV local)            ║
║  └─────────────────┘                                                         ║
║                                                                              ║
║  ┌─────────────────┐  Escuta: avionica/comandos/falhas + avionica/waic       ║
║  │ sistema_alertas │  Ação:   Sintetiza voz via PowerShell (Windows)         ║
║  │ .py             │  (TCAS, EGPWS, Engine Failure)                          ║
║  └─────────────────┘                                                         ║
║                                                                              ║
║  INTERFACES COM O USUÁRIO                                                    ║
║  ┌─────────────────┐  GUI: CustomTkinter (Glass Cockpit)                     ║
║  │ computador_     │  Escuta: todos os tópicos aviônicos                     ║
║  │ voo.py          │  Publica: comandos (velocidade, proa, rota)             ║
║  └─────────────────┘                                                         ║
║                                                                              ║
║  ┌─────────────────┐  GUI: CustomTkinter (Painel do Instrutor)               ║
║  │ injetor_falhas  │  Publica: avionica/comandos/falhas (motor, TCAS, EGPWS) ║
║  │ .py             │  Publica: avionica/comandos/falhas/sensor_B (bizantino) ║
║  └─────────────────┘                                                         ║
║                                                                              ║
║  FORA DO SISTEMA (não integrado ao Docker)                                   ║
║  ┌─────────────────┐  Usa: socket UDP (porta 5000)                           ║
║  │ sensor_cabo.py  │  NÃO usa MQTT — protocolo completamente diferente!      ║
║  └─────────────────┘                                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## ✅ O que Funciona Bem Hoje

Antes de listar problemas, é importante reconhecer o que está bem arquitetado:

### 1. Desacoplamento real via Pub/Sub
Cada arquivo Python é completamente independente. O `computador_automacao.py` não importa nem conhece o `radar_externo.py` — eles se comunicam apenas pelo tópico MQTT. Isso é boa arquitetura de sistemas distribuídos.

### 2. Algoritmo TMR implementado corretamente
O `consenso_motor.py` usa a mediana de 3 sensores, que é matematicamente a estratégia correta para tolerância a falhas bizantinas. Se um sensor mentir, o valor do meio dos 3 ordenados é sempre o valor da maioria saudável.

### 3. Deduplicação de mensagens no sensor de freios
O `sensor_freio.py` envia Canal A e Canal B com o **mesmo `id_mensagem` (UUID)**. O `computador_voo.py` detecta a duplicata e descarta a segunda — exatamente como sistemas AFDX reais funcionam com redundância ativa.

### 4. Inércia física simulada no controle de velocidade
O `sensores_voo.py` usa `threading.Timer(3.0, ...)` para aplicar uma nova velocidade apenas 3 segundos após o comando — simulando a inércia dos motores. Isso representa bem um sistema de tempo real.

### 5. Decisão autônoma no anti-gelo
O `computador_automacao.py` toma decisões sem intervenção humana: detecta `TEMPESTADE + temp < 0` e aciona o anti-gelo. Isso representa a lógica autônoma de um sistema embarcado real.

---

## ❌ Problemas Encontrados — Análise Arquivo por Arquivo

---

### 🔴 Problema 1 — `except: pass` em toda parte (Crítico)

**Onde acontece:** Todos os arquivos sem exceção.

```python
# computador_automacao.py — linha 35
except: pass

# consenso_motor.py — linha 18
except: pass

# computador_voo.py — linha 279
except: pass

# sistema_alertas.py — linha 42
except: pass

# sensor_motor.py — linha 27
except: pass
```

**Por que é um problema grave:**
O `except: pass` captura **qualquer exceção** — incluindo `KeyboardInterrupt`, `SystemExit`, erros de memória, e erros de lógica do seu próprio código — e os **descarta silenciosamente**. Se um sensor parar de publicar por causa de um bug, você nunca saberá. O sistema vai parecer estar rodando mas os dados serão inválidos.

**Como corrigir:**

```python
# ❌ Errado — engole tudo silenciosamente
except: pass

# ✅ Correto — captura só o que você espera e loga o problema
import logging

logger = logging.getLogger(__name__)

try:
    pacote = json.loads(msg.payload.decode())
    dados = pacote['dados']
except json.JSONDecodeError as e:
    logger.error("Payload MQTT inválido no tópico %s: %s", msg.topic, e)
except KeyError as e:
    logger.warning("Campo ausente no pacote de %s: %s", msg.topic, e)
```

---

### 🔴 Problema 2 — `sensor_cabo.py` usa UDP puro — completamente isolado

**Arquivo:** `sensor_cabo.py`

```python
# sensor_cabo.py — linha 9
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(mensagem, ('127.0.0.1', 5000))  # UDP para localhost:5000
```

**Por que é um problema grave:**
- Este arquivo **não usa MQTT** — usa UDP cru para `127.0.0.1:5000`
- Ninguém está escutando na porta 5000. Nenhum outro arquivo do projeto abre um socket UDP
- O arquivo está **completamente desconectado** da arquitetura. Os dados são enviados para o vazio
- Representa o conceito correto (sensor por cabo = AFDX, diferente do sensor WAIC = wireless), mas a implementação está quebrada

**Como corrigir:**
Migrar para MQTT como todos os outros, publicando no tópico `avionica/sensores/cabo`:

```python
# ✅ Correto — integrar ao barramento MQTT como os outros sensores
import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "localhost")
TOPICO = "avionica/sensores/cabo"

cliente = mqtt.Client()
cliente.connect(BROKER, int(os.getenv("MQTT_PORT", "1883")), 60)

# No loop:
pacote = {"origem": "Sensor_Freio_Cabo", "dados": {"pressao": pressao_atual}}
cliente.publish(TOPICO, json.dumps(pacote))
```

---

### 🔴 Problema 3 — `caixa_preta.py` grava em arquivo local — dados perdidos no Docker

**Arquivo:** `caixa_preta.py`

```python
# caixa_preta.py — linha 12
ARQUIVO_LOG = "flight_data_recorder.csv"

# linha 36
with open(ARQUIVO_LOG, mode='a', newline='') as file:
    writer = csv.writer(file, delimiter=';')
    writer.writerow([timestamp, topico, payload])
```

**Por que é um problema grave:**
- O arquivo `flight_data_recorder.csv` é gravado **dentro do container Docker** no diretório de trabalho
- Quando o container é parado ou recriado (`docker compose down`), **o arquivo CSV é destruído junto com o container**
- A caixa preta perde todos os dados do voo — a finalidade dela é exatamente o oposto disso
- O arquivo abre e fecha a cada mensagem recebida — se chegar 10 mensagens por segundo (realista com 8 tópicos), são 10 operações de I/O de disco por segundo, desnecessariamente caro

**Como corrigir — Opção 1: Volume Docker**

No `docker-compose.yml`, adicionar um volume persistente:
```yaml
# No docker-compose.yml
caixa-preta:
  build:
    context: ./Software_Aviao
    dockerfile: docker/Dockerfile
  command: python caixa_preta.py
  volumes:
    - ./logs:/app/logs   # ← monta diretório local dentro do container
  environment:
    MQTT_BROKER: mqtt-broker
```

No `caixa_preta.py`, usar o caminho correto:
```python
ARQUIVO_LOG = os.getenv("LOG_PATH", "/app/logs/flight_data_recorder.csv")
```

**Como corrigir — Opção 2 (melhor): Publicar no banco via backend**

Em vez de CSV, a caixa preta publica cada registro em um tópico Kafka dedicado, e o consumer Java persiste na tabela `mensagens_barramento` do PostgreSQL. Assim os dados ficam no banco com toda a durabilidade do Plano 01.

---

### 🟠 Problema 4 — `sistema_alertas.py` usa PowerShell para síntese de voz — não funciona no Docker

**Arquivo:** `sistema_alertas.py`

```python
# sistema_alertas.py — linha 16
comando = f'powershell -Command "Add-Type -AssemblyName System.Speech; ...'
threading.Thread(target=lambda: os.system(comando)).start()
```

**Por que é um problema:**
- Este arquivo abre `powershell` do Windows via `os.system()` — isso **só funciona na máquina do desenvolvedor (Windows)**
- No container Docker (Linux), `powershell` não existe → erro silencioso pois o `os.system()` falha sem exceção
- Cria uma nova thread do sistema operacional por alerta — se vierem 20 alertas seguidos, são 20 processos PowerShell simultâneos

**Como corrigir:**
Separar a lógica de alerta da síntese de voz. O serviço deve apenas publicar o alerta no barramento e o frontend (Vue.js) ou o computador de voo (GUI) apresenta o alerta visualmente:

```python
# ✅ Correto — publica o alerta como mensagem MQTT estruturada
def ao_receber_mensagem(client, userdata, msg):
    try:
        pacote = json.loads(msg.payload.decode())
        tipo = pacote.get("tipo")

        if tipo == "trafego":
            alerta = {"nivel": "WARNING", "codigo": "TCAS", "mensagem": "Traffic! Traffic!"}
        elif tipo == "queda":
            alerta = {"nivel": "CRITICAL", "codigo": "EGPWS", "mensagem": "Terrain! Pull up!"}
        elif tipo == "motor":
            alerta = {"nivel": "CRITICAL", "codigo": "ENG_FAIL", "mensagem": "Engine Failure"}
        else:
            return

        # Publica no barramento em vez de chamar PowerShell
        client.publish("avionica/alertas/processados", json.dumps(alerta))
        logger.warning("[ALERTA] %s: %s", alerta['codigo'], alerta['mensagem'])

    except json.JSONDecodeError as e:
        logger.error("Payload de alerta inválido: %s", e)
```

---

### 🟠 Problema 5 — `computador_automacao.py` tem lógica de anti-gelo frágil

**Arquivo:** `computador_automacao.py`

```python
# computador_automacao.py — linhas 26-34
if clima == "TEMPESTADE" and temp < 0 and not anti_ice_ligado:
    anti_ice_ligado = True
    client.publish(TOPICO_ANTI_ICE, json.dumps({"status": "ON", "msg": "ICE DETECTED - SYS ON"}))

elif clima != "TEMPESTADE" and temp > 0 and anti_ice_ligado:
    anti_ice_ligado = False
    client.publish(TOPICO_ANTI_ICE, json.dumps({"status": "AUTO", "msg": "ANTI-ICE: AUTO"}))
```

**Por que é um problema:**

1. **Sem histerese:** A condição de desligar é `temp > 0`. Se a temperatura flutuar entre -1 e +1 grau (o que `radar_externo.py` pode gerar), o anti-gelo vai **ligar e desligar rapidamente** a cada segundo — um comportamento chamado *chattering* que danificaria um sistema real.

2. **Estado global mutável em thread:** `anti_ice_ligado` é uma variável global modificada no callback MQTT (que roda em uma thread separada). Sem lock, em Python pode haver condição de corrida.

3. **Lógica de domínio acoplada ao callback:** Mistura a recepção da mensagem com a tomada de decisão — difícil de testar e de expandir.

**Como corrigir — adicionar histerese e separar responsabilidades:**

```python
# ✅ Correto — com histerese e lógica desacoplada
import threading

lock = threading.Lock()
anti_ice_ligado = False

# Histerese: liga abaixo de -2°C, desliga acima de +3°C (zona morta de 5°C)
TEMP_LIGAR  = -2.0   # temperatura para ativar
TEMP_DESLIGAR = 3.0  # temperatura para desativar (diferente de ligar!)

def avaliar_anti_ice(client, clima, temp):
    global anti_ice_ligado

    with lock:
        if clima == "TEMPESTADE" and temp < TEMP_LIGAR and not anti_ice_ligado:
            anti_ice_ligado = True
            publicar_anti_ice(client, "ON", f"ICE DETECTED ({temp}°C) - SYS ACTIVATED")
            logger.warning("Anti-ice ATIVADO. Temperatura: %.1f°C", temp)

        elif (clima != "TEMPESTADE" or temp > TEMP_DESLIGAR) and anti_ice_ligado:
            anti_ice_ligado = False
            publicar_anti_ice(client, "AUTO", f"CONDITIONS NORMAL ({temp}°C) - SYS AUTO")
            logger.info("Anti-ice desativado. Temperatura: %.1f°C", temp)

def publicar_anti_ice(client, status, mensagem):
    payload = {"status": status, "msg": mensagem, "timestamp": time.time()}
    client.publish(TOPICO_ANTI_ICE, json.dumps(payload))

def ao_receber_mensagem(client, userdata, msg):
    try:
        pacote = json.loads(msg.payload.decode())
        dados = pacote.get("dados", {})
        clima = dados.get("radar_clima", "")
        temp = float(dados.get("temp_externa_c", 0))
        avaliar_anti_ice(client, clima, temp)
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.error("Erro ao processar mensagem de radar: %s", e)
```

---

### 🟠 Problema 6 — `consenso_motor.py` publica temperatura fixa de 600°C

**Arquivo:** `consenso_motor.py`

```python
# consenso_motor.py — linha 48
pacote_final = {
    "dados": {
        "pressao_motor": pressao_consensual,
        "temperatura": 600.0   # ← valor hardcoded! Nunca muda.
    }
}
```

**Por que é um problema:**
- A temperatura do motor está **hardcoded** como `600.0` sempre — independente de qualquer sensor
- O `computador_voo.py` exibe `EGT: 600.0 °C` permanentemente no painel — o dado parece real mas é falso
- O algoritmo de consenso foi implementado apenas para pressão. Temperatura não tem consenso.

**Como corrigir:**
Os 3 sensores de motor (`sensor_motor.py`) também devem publicar temperatura, e o consenso deve calculá-la da mesma forma:

```python
# ✅ Em sensor_motor.py — adicionar temperatura ao pacote
pacote = {
    "id": ID_SENSOR,
    "pressao": pressao,
    "temperatura": round(random.uniform(550.0, 650.0), 1)  # EGT simulado
}

# ✅ Em consenso_motor.py — consenso de pressão E temperatura
leituras = {
    "A": {"pressao": 40.0, "temperatura": 600.0},
    "B": {"pressao": 40.0, "temperatura": 600.0},
    "C": {"pressao": 40.0, "temperatura": 600.0}
}

pressoes    = sorted([leituras[s]["pressao"]    for s in leituras])
temperaturas = sorted([leituras[s]["temperatura"] for s in leituras])

pressao_consensual    = pressoes[1]      # mediana
temperatura_consensual = temperaturas[1]  # mediana

pacote_final = {
    "dados": {
        "pressao_motor": pressao_consensual,
        "temperatura": temperatura_consensual  # ← valor real com consenso
    }
}
```

---

### 🟡 Problema 7 — `fms_distribuido.py` falha silenciosamente sem API Key

**Arquivo:** `fms_distribuido.py`

```python
# fms_distribuido.py — linhas 34-36
def buscar_coordenadas(self, icao):
    if not API_KEY:
        print("❌ Erro: defina FMS_API_KEY no .env para consultar a API Ninjas.")
        return None, None   # ← retorna None e o FMS nunca calcula rotas
```

**Por que é um problema:**
- Sem `FMS_API_KEY`, o FMS publica indefinidamente `"N/A → N/A | 0 NM | 0 min"` a cada 2 segundos
- Não há fallback com aeroportos conhecidos — o sistema fica inutilizável sem a chave
- O `print()` de erro some nos logs do Docker

**Como corrigir — banco de coordenadas local:**

```python
# ✅ Fallback com coordenadas hardcoded dos principais aeroportos
COORDENADAS_LOCAIS = {
    "SBGR": (-23.4356, -46.4731),  # São Paulo - Guarulhos
    "SBGL": (-22.8099, -43.2505),  # Rio de Janeiro - Galeão
    "SBBR": (-15.8711, -47.9186),  # Brasília
    "EGLL": (51.4775, -0.4614),    # Londres Heathrow
    "KJFK": (40.6413, -73.7781),   # Nova York JFK
    "LEMD": (40.4936, -3.5668),    # Madri Barajas
    "LFPG": (49.0097, 2.5479),     # Paris Charles de Gaulle
}

def buscar_coordenadas(self, icao):
    # Primeiro tenta o banco local (zero dependência de rede)
    if icao in COORDENADAS_LOCAIS:
        return COORDENADAS_LOCAIS[icao]

    # Só vai para a API se tiver a chave E o aeroporto não for local
    if not API_KEY:
        logger.warning("FMS_API_KEY não definida e ICAO '%s' não encontrado localmente.", icao)
        return None, None

    # ... chamada à API Ninjas como antes
```

---

### 🟡 Problema 8 — Módulos não integrados ao Docker Compose

Dos 14 arquivos Python, apenas **7 estão no `docker-compose.yml`**. Os outros 7 existem mas não são executados na stack:

| Arquivo | Status no Docker | Impacto da ausência |
|---|---|---|
| `caixa_preta.py` | ❌ Ausente | Sem gravação de histórico de voo |
| `consenso_motor.py` | ❌ Ausente | TMR não funciona (lider_waic envia valor direto sem consenso) |
| `sensor_motor.py` (x3) | ❌ Ausente | Não há motores A, B, C para o consenso processar |
| `sistema_alertas.py` | ❌ Ausente | Sem processamento de alertas do barramento |
| `sensor_cabo.py` | ❌ Ausente | + problema próprio (UDP, não funciona de qualquer forma) |
| `computador_voo.py` | ❌ Ausente | GUI roda apenas local (depende de display) — ver nota |
| `injetor_falhas.py` | ❌ Ausente | GUI roda apenas local — correto não estar no Docker |

> **Nota sobre GUIs no Docker:** `computador_voo.py` e `injetor_falhas.py` usam `customtkinter` (GUI) e não devem rodar em Docker. Eles devem ser executados diretamente na máquina do usuário, apontando para o broker MQTT.

**Como adicionar os serviços faltantes ao Docker Compose:**

```yaml
# docker-compose.yml — adicionar estes serviços:

  caixa-preta:
    build:
      context: ./Software_Aviao
      dockerfile: docker/Dockerfile
    container_name: avionica_caixa_preta
    command: python caixa_preta.py
    environment:
      MQTT_BROKER: mqtt-broker
      MQTT_PORT: "1883"
      LOG_PATH: /app/logs/flight_data_recorder.csv
    volumes:
      - ./logs:/app/logs          # ← persiste o CSV fora do container
    depends_on:
      - mqtt-broker

  sensor-motor-a:
    build:
      context: ./Software_Aviao
      dockerfile: docker/Dockerfile
    container_name: avionica_sensor_motor_a
    command: python sensor_motor.py
    environment:
      MQTT_BROKER: mqtt-broker
      SENSOR_ID: "A"             # ← ID_SENSOR lido via os.getenv()
    depends_on:
      - mqtt-broker

  sensor-motor-b:
    build:
      context: ./Software_Aviao
      dockerfile: docker/Dockerfile
    container_name: avionica_sensor_motor_b
    command: python sensor_motor.py
    environment:
      MQTT_BROKER: mqtt-broker
      SENSOR_ID: "B"
    depends_on:
      - mqtt-broker

  sensor-motor-c:
    build:
      context: ./Software_Aviao
      dockerfile: docker/Dockerfile
    container_name: avionica_sensor_motor_c
    command: python sensor_motor.py
    environment:
      MQTT_BROKER: mqtt-broker
      SENSOR_ID: "C"
    depends_on:
      - mqtt-broker

  consenso-motor:
    build:
      context: ./Software_Aviao
      dockerfile: docker/Dockerfile
    container_name: avionica_consenso_motor
    command: python consenso_motor.py
    environment:
      MQTT_BROKER: mqtt-broker
    depends_on:
      - sensor-motor-a
      - sensor-motor-b
      - sensor-motor-c
```

---

### 🟡 Problema 9 — `computador_navegacao.py` não escuta comandos de proa

**Arquivo:** `computador_navegacao.py`

```python
# computador_navegacao.py — linha 26
"proa_graus": random.randint(265, 275),   # ← sempre aleatório, ignora comandos
```

O `computador_voo.py` (Glass Cockpit) publica comandos de proa em `avionica/comandos/proa` quando o piloto clica nos botões `< 1º` / `1º >`. Mas o `computador_navegacao.py` **nunca escuta este tópico** — ele sempre gera valores aleatórios entre 265° e 275°.

**Como corrigir:**

```python
# ✅ computador_navegacao.py — escutar e aplicar comandos de proa
TOPICO_NAV = "avionica/navegacao"
TOPICO_CMD_PROA = "avionica/comandos/proa"  # ← novo

proa_atual = 270  # valor inicial

def ao_conectar(client, userdata, flags, rc):
    client.subscribe(TOPICO_CMD_PROA)       # ← escuta comandos

def ao_receber_mensagem(client, userdata, msg):
    global proa_atual
    try:
        pacote = json.loads(msg.payload.decode())
        nova_proa = pacote.get("nova_proa")
        if nova_proa is not None:
            proa_atual = int(nova_proa) % 360
            logger.info("Proa atualizada para %d°", proa_atual)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("Comando de proa inválido: %s", e)

# No loop de publicação, usar proa_atual em vez de random:
"proa_graus": proa_atual + random.randint(-1, 1),  # ± 1° de oscilação natural
```

---

### 🟡 Problema 10 — Sem `requirements.txt` com versões fixadas

Todos os arquivos importam `paho-mqtt`, `customtkinter`, `requests`, mas não há um `requirements.txt` com versões fixas no projeto.

**O que pode acontecer:**
- Ao reconstruir o container em 6 meses, `paho-mqtt` pode ter uma nova versão com API quebrada
- A build do Docker pode instalar versões diferentes em máquinas diferentes

**Como corrigir:**

```txt
# Software_Aviao/requirements.txt
paho-mqtt==1.6.1
requests==2.32.3
customtkinter==5.2.2
```

No `Dockerfile`:
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

---

## 📊 Resumo: Fluxo Completo Corrigido

```
[sensor_motor.py A] ─┐
[sensor_motor.py B] ─┼─► avionica/sensores/motor/# ─► [consenso_motor.py]
[sensor_motor.py C] ─┘                                       │
                                                              ▼
[sensores_voo.py] ──────────────────────────────► avionica/sensores/voo
[sensor_freio.py] ──────────────────────────────► avionica/sensores/freios
[radar_externo.py] ─────────────────────────────► avionica/radar
[lider_waic.py] ────────────────────────────────► avionica/sensores/waic ◄─(TMR)
[computador_navegacao.py] ──────────────────────► avionica/navegacao
[fms_distribuido.py] ───────────────────────────► avionica/fms/dados
                                                              │
                          ┌───────────────────────────────────┤
                          ▼                                   ▼
               [computador_automacao.py]         [caixa_preta.py]
               Decide anti-gelo                 Grava tudo em CSV
               Publica: avionica/sistemas/anti_ice

[injetor_falhas.py] ────────────────────────────► avionica/comandos/falhas
                                                              │
                                                              ▼
                                                  [sistema_alertas.py]
                                                  Processa e republica alertas

[computador_voo.py] ─── ESCUTA TUDO, PUBLICA COMANDOS ──────►
```

---

## 🏆 Tabela de Prioridades de Correção

| # | Problema | Severidade | Esforço | Por onde começar |
|---|---|---|---|---|
| 1 | `except: pass` em todos os arquivos | 🔴 Crítico | Baixo | Substituir por logging em cada arquivo |
| 2 | `sensor_cabo.py` usando UDP sem receptor | 🔴 Crítico | Baixo | Migrar para MQTT |
| 3 | `caixa_preta.py` perdendo dados no Docker | 🔴 Crítico | Médio | Adicionar volume no docker-compose |
| 4 | Módulos faltando no docker-compose | 🟠 Alto | Médio | Adicionar sensor-motor-a/b/c, consenso, caixa-preta |
| 5 | `sistema_alertas.py` com PowerShell | 🟠 Alto | Baixo | Publicar alertas como MQTT em vez de voz |
| 6 | Anti-gelo sem histerese | 🟠 Alto | Baixo | Adicionar zona morta de temperatura |
| 7 | Temperatura do motor hardcoded 600°C | 🟡 Médio | Baixo | Adicionar consenso de temperatura |
| 8 | `computador_navegacao.py` ignora comandos de proa | 🟡 Médio | Baixo | Escutar `avionica/comandos/proa` |
| 9 | FMS sem fallback de aeroportos | 🟡 Médio | Baixo | Adicionar dict com coordenadas locais |
| 10 | Sem `requirements.txt` fixado | 🟡 Médio | Baixo | Criar arquivo com versões exatas |
