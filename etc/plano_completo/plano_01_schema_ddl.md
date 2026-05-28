# 📦 Plano 01 — Schema DDL: Banco de Dados PostgreSQL

> **Sistema:** Gateway Tolerante a Falhas para Redes Aviônicas Híbridas (AFDX/WAIC)  
> **Banco:** PostgreSQL 17 (rodando via Docker)  
> **Schema:** `public`  
> **Propósito:** Persistir telemetria, alertas, rotas de voo e logs de eventos críticos

---

## 🧠 Visão Geral das Tabelas

O banco `avionica` precisa armazenar os dados que hoje existem apenas em memória (no `AircraftTelemetryService`). A estrutura é dividida em grupos lógicos:

| Grupo | Tabela | Responsabilidade |
|---|---|---|
| Telemetria | `telemetria_voo` | Dados de sensores de voo (combustível, altitude, Mach) |
| Telemetria | `telemetria_freios` | Dados de pressão dos freios |
| Telemetria | `telemetria_radar` | Dados de radar e clima externo |
| Telemetria | `telemetria_waic` | Sensores WAIC dos motores/asas |
| Navegação | `telemetria_navegacao` | Dados do computador de navegação |
| FMS | `rotas_fms` | Rotas calculadas pelo FMS distribuído |
| Alertas | `alertas` | Alertas e falhas do sistema |
| Anti-Gelo | `eventos_anti_ice` | Eventos do sistema autônomo anti-gelo |
| Logs | `mensagens_barramento` | Log histórico de todas as mensagens MQTT |

---

## 📋 Passo a Passo para Subir o Banco

### ✅ Pré-requisitos

Certifique-se que você tem instalado:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) com WSL2 habilitado (Windows)
- O arquivo `.env` preenchido na raiz do projeto

### Passo 1 — Verifique o `.env` na raiz do projeto

O arquivo `.env` deve conter as variáveis abaixo (já existentes no projeto):

```env
POSTGRES_DB=avionica
POSTGRES_USER=avionica
POSTGRES_PASSWORD=avionica_dev
```

Se não existir, copie o exemplo:
```powershell
copy .env.example .env
```

---

### Passo 2 — Suba APENAS o container do PostgreSQL

> ⚠️ Não suba todos os serviços agora. Suba só o banco primeiro para executar o DDL.

```powershell
# No diretório raiz do projeto (onde está o docker-compose.yml)
docker compose up -d postgres
```

Aguarde o banco ficar saudável (~15 segundos):
```powershell
docker compose ps
# O campo "Status" do serviço postgres deve mostrar: healthy
```

---

### Passo 3 — Salve o arquivo DDL

Crie o arquivo `infra/db/schema.sql` copiando o conteúdo da seção DDL abaixo.  
Ou crie via PowerShell:
```powershell
# Cria o diretório se não existir
New-Item -ItemType Directory -Force -Path "infra\db"
```
Depois cole o conteúdo DDL desta seção no arquivo `infra/db/schema.sql`.

---

### Passo 4 — Execute o DDL dentro do container

```powershell
# Copia o arquivo SQL para dentro do container PostgreSQL
docker cp infra/db/schema.sql avionica_postgres:/tmp/schema.sql

# Executa o script SQL no banco 'avionica' com o usuário 'avionica'
docker exec -it avionica_postgres psql -U avionica -d avionica -f /tmp/schema.sql
```

Saída esperada:
```
CREATE EXTENSION
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
...
COMMENT
```

---

### Passo 5 — Verifique as tabelas criadas

```powershell
# Abre o console interativo do PostgreSQL
docker exec -it avionica_postgres psql -U avionica -d avionica
```

Dentro do `psql`, execute:
```sql
-- Lista todas as tabelas criadas
\dt

-- Veja a estrutura completa de uma tabela
\d telemetria_voo

-- Veja os índices criados
\di

-- Saia do console
\q
```

---

### Passo 6 — Suba o restante dos serviços

Após o banco estar pronto com o schema aplicado, suba toda a stack:

```powershell
docker compose up -d --build
```

Para acompanhar os logs em tempo real:
```powershell
docker compose logs -f backend-gateway
```

---

## 🗂️ DDL Completo — `infra/db/schema.sql`

```sql
-- ============================================================
-- SISTEMA AVIÔNICO DISTRIBUÍDO — GATEWAY AFDX/WAIC
-- Schema DDL — PostgreSQL 17
-- Criado para persistir os dados que chegam via MQTT
-- ============================================================

-- Extensão para geração de UUIDs seguros
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 1. TELEMETRIA DE VOO
--    Fonte: sensores_voo.py
--    Tópico MQTT: avionica/sensores/voo
--    Campos: combustível, altitude, estabilizador, pressão, Mach
-- ============================================================
CREATE TABLE IF NOT EXISTS telemetria_voo (
    id                  UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    recebido_em         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    combustivel_pct     NUMERIC(5,2),        -- % de combustível restante (0.00 - 100.00)
    altitude_ft         INTEGER,             -- Altitude em pés acima do nível do mar
    estabilizador_graus NUMERIC(4,1),        -- Posição do estabilizador horizontal em graus
    pressao_cabine_psi  NUMERIC(5,2),        -- Pressão da cabine em PSI
    velocidade_mach     NUMERIC(5,3),        -- Velocidade em Mach (ex: 0.802)
    origem              VARCHAR(100)          -- Identificador do sensor de origem
);

-- ============================================================
-- 2. TELEMETRIA DE FREIOS
--    Fonte: sensor_freio.py
--    Tópico MQTT: avionica/sensores/freios
-- ============================================================
CREATE TABLE IF NOT EXISTS telemetria_freios (
    id          UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    recebido_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    pressao_psi NUMERIC(7,2),               -- Pressão hidráulica dos freios em PSI
    origem      VARCHAR(100)
);

-- ============================================================
-- 3. TELEMETRIA DE RADAR EXTERNO
--    Fonte: radar_externo.py
--    Tópico MQTT: avionica/radar
-- ============================================================
CREATE TABLE IF NOT EXISTS telemetria_radar (
    id              UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    recebido_em     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    vento_knots     NUMERIC(6,1),            -- Velocidade do vento em nós
    turbulencia     VARCHAR(50),              -- Nível de turbulência (NENHUMA, LEVE, MODERADA, SEVERA)
    radar_clima     VARCHAR(100),             -- Condição climática detectada (ex: LIMPO, CHUVA, TEMPESTADE)
    temp_externa_c  NUMERIC(5,1),             -- Temperatura externa em graus Celsius
    qnh_hpa         NUMERIC(6,1),             -- Pressão barométrica de referência (QNH) em hPa
    atc_msg         TEXT,                     -- Última mensagem ATC recebida
    origem          VARCHAR(100)
);

-- ============================================================
-- 4. TELEMETRIA WAIC (Wireless Avionics Intra-Communications)
--    Fonte: lider_waic.py (sensores sem fio nas asas/motores)
--    Tópico MQTT: avionica/sensores/waic
-- ============================================================
CREATE TABLE IF NOT EXISTS telemetria_waic (
    id              UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    recebido_em     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    pressao_motor   NUMERIC(7,2),            -- Pressão do motor em PSI
    temperatura_c   NUMERIC(6,1),            -- Temperatura do motor em graus Celsius
    origem          VARCHAR(100)
);

-- ============================================================
-- 5. DADOS DO COMPUTADOR DE NAVEGAÇÃO
--    Fonte: computador_navegacao.py
--    Tópico MQTT: avionica/navegacao
-- ============================================================
CREATE TABLE IF NOT EXISTS telemetria_navegacao (
    id                  UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    recebido_em         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    proa_graus          NUMERIC(5,1),        -- Proa magnética (heading) em graus (0-360)
    vs_fpm              INTEGER,              -- Velocidade vertical em pés por minuto (fpm)
    piloto_automatico   BOOLEAN,              -- TRUE = piloto automático ativo
    waypoint_ativo      VARCHAR(100),         -- Nome/código do waypoint atual
    eta_minutos         INTEGER,              -- Tempo estimado de chegada em minutos
    origem              VARCHAR(100)
);

-- ============================================================
-- 6. ROTAS DO FMS (Flight Management System)
--    Fonte: fms_distribuido.py (usa API Ninjas para coordenadas)
--    Tópico MQTT: avionica/fms/dados
-- ============================================================
CREATE TABLE IF NOT EXISTS rotas_fms (
    id              UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    registrado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    icao_origem     CHAR(4),                 -- Código ICAO do aeroporto de origem (ex: SBGR)
    icao_destino    CHAR(4),                 -- Código ICAO do aeroporto de destino (ex: EGLL)
    rota_texto      VARCHAR(200),            -- Rota por extenso (ex: "SBGR → EGLL")
    distancia_nm    NUMERIC(8,1),            -- Distância calculada em milhas náuticas
    eta_minutos     INTEGER,                 -- ETA calculado em minutos
    ativa           BOOLEAN DEFAULT TRUE      -- TRUE = rota atualmente em uso pelo FMS
);

-- ============================================================
-- 7. ALERTAS E FALHAS DO SISTEMA
--    Fonte: sistema_alertas.py e injetor_falhas.py
--    Tópico MQTT: avionica/comandos/falhas
-- ============================================================
CREATE TABLE IF NOT EXISTS alertas (
    id              UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    registrado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tipo            VARCHAR(100) NOT NULL,   -- Tipo: FALHA_SENSOR, OVERSPEED, PRESSAO_BAIXA, etc.
    descricao       TEXT,                    -- Descrição detalhada do alerta
    severidade      VARCHAR(20) NOT NULL DEFAULT 'INFO'
                    CHECK (severidade IN ('INFO', 'WARNING', 'CRITICAL')),
    origem          VARCHAR(100),            -- Subsistema que gerou o alerta
    resolvido       BOOLEAN NOT NULL DEFAULT FALSE,  -- FALSE = alerta ainda ativo
    resolvido_em    TIMESTAMPTZ              -- Timestamp de quando foi resolvido
);

-- ============================================================
-- 8. EVENTOS DO SISTEMA ANTI-ICE (Autônomo)
--    Fonte: computador_automacao.py
--    Tópico MQTT: avionica/sistemas/anti_ice
-- ============================================================
CREATE TABLE IF NOT EXISTS eventos_anti_ice (
    id              UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    registrado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status          VARCHAR(50),             -- ATIVADO | DESATIVADO | STAND_BY
    mensagem        TEXT,                    -- Mensagem gerada pelo sistema autônomo
    temperatura_c   NUMERIC(5,1),            -- Temperatura que disparou o evento
    origem          VARCHAR(100)
);

-- ============================================================
-- 9. LOG HISTÓRICO DO BARRAMENTO MQTT
--    Equivale ao recentMessages em AircraftTelemetryService.java,
--    mas persistido no banco para análise histórica
-- ============================================================
CREATE TABLE IF NOT EXISTS mensagens_barramento (
    id              BIGSERIAL    PRIMARY KEY,
    recebido_em     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    topico          VARCHAR(200) NOT NULL,   -- Tópico MQTT completo (ex: avionica/sensores/voo)
    payload_json    JSONB,                   -- Payload completo como JSON estruturado
    tamanho_bytes   INTEGER                  -- Tamanho original do payload em bytes
);

-- ============================================================
-- ÍNDICES — Otimizam consultas frequentes
-- ============================================================

-- Índices de tempo (ordenação DESC para buscar o mais recente)
CREATE INDEX IF NOT EXISTS idx_telemetria_voo_tempo       ON telemetria_voo       (recebido_em DESC);
CREATE INDEX IF NOT EXISTS idx_telemetria_freios_tempo    ON telemetria_freios    (recebido_em DESC);
CREATE INDEX IF NOT EXISTS idx_telemetria_radar_tempo     ON telemetria_radar     (recebido_em DESC);
CREATE INDEX IF NOT EXISTS idx_telemetria_waic_tempo      ON telemetria_waic      (recebido_em DESC);
CREATE INDEX IF NOT EXISTS idx_telemetria_nav_tempo       ON telemetria_navegacao (recebido_em DESC);

-- Índices de alertas
CREATE INDEX IF NOT EXISTS idx_alertas_tempo              ON alertas              (registrado_em DESC);
CREATE INDEX IF NOT EXISTS idx_alertas_severidade         ON alertas              (severidade);
CREATE INDEX IF NOT EXISTS idx_alertas_nao_resolvidos     ON alertas              (resolvido) WHERE resolvido = FALSE;

-- Índices de barramento MQTT
CREATE INDEX IF NOT EXISTS idx_mensagens_topico           ON mensagens_barramento (topico);
CREATE INDEX IF NOT EXISTS idx_mensagens_tempo            ON mensagens_barramento (recebido_em DESC);
CREATE INDEX IF NOT EXISTS idx_mensagens_payload          ON mensagens_barramento USING GIN (payload_json);

-- Índice de rota ativa
CREATE INDEX IF NOT EXISTS idx_rotas_ativa                ON rotas_fms            (ativa) WHERE ativa = TRUE;

-- ============================================================
-- COMENTÁRIOS DE DOCUMENTAÇÃO
-- ============================================================
COMMENT ON TABLE telemetria_voo        IS 'Dados dos sensores gerais de voo via MQTT (tópico: avionica/sensores/voo)';
COMMENT ON TABLE telemetria_freios     IS 'Dados do sensor de freios hidráulicos (tópico: avionica/sensores/freios)';
COMMENT ON TABLE telemetria_radar      IS 'Dados do radar externo e meteorologia (tópico: avionica/radar)';
COMMENT ON TABLE telemetria_waic       IS 'Sensores sem fio WAIC nos motores e asas (tópico: avionica/sensores/waic)';
COMMENT ON TABLE telemetria_navegacao  IS 'Dados do computador de navegação (tópico: avionica/navegacao)';
COMMENT ON TABLE rotas_fms             IS 'Rotas calculadas pelo Flight Management System distribuído';
COMMENT ON TABLE alertas               IS 'Alertas e falhas do sistema distribuído aviônico';
COMMENT ON TABLE eventos_anti_ice      IS 'Eventos do sistema autônomo anti-gelo (tópico: avionica/sistemas/anti_ice)';
COMMENT ON TABLE mensagens_barramento  IS 'Log histórico de todas as mensagens do barramento MQTT aviônico';
```

---

## 🧪 Dados de Teste — Opcional

Para inserir dados de teste e validar as tabelas:

```sql
-- Inserir uma leitura de voo simulada
INSERT INTO telemetria_voo (combustivel_pct, altitude_ft, estabilizador_graus, pressao_cabine_psi, velocidade_mach, origem)
VALUES (87.50, 35000, -1.2, 11.02, 0.802, 'Sensores_Gerais_Voo');

-- Inserir um alerta crítico de overspeed
INSERT INTO alertas (tipo, descricao, severidade, origem)
VALUES ('OVERSPEED', 'Velocidade acima do limite MMO detectada pelo computador de automação', 'CRITICAL', 'computador_automacao');

-- Inserir rota do FMS (São Paulo → Londres)
INSERT INTO rotas_fms (icao_origem, icao_destino, rota_texto, distancia_nm, eta_minutos)
VALUES ('SBGR', 'EGLL', 'SBGR → EGLL', 5412.3, 672);

-- Verificar registros
SELECT * FROM telemetria_voo     ORDER BY recebido_em DESC LIMIT 5;
SELECT * FROM alertas            WHERE resolvido = FALSE;
SELECT * FROM rotas_fms          WHERE ativa = TRUE;
```

---

## 🔄 Rollback — Remover Todas as Tabelas

> ⚠️ **Use SOMENTE em ambiente de desenvolvimento!**

```sql
DROP TABLE IF EXISTS mensagens_barramento  CASCADE;
DROP TABLE IF EXISTS eventos_anti_ice      CASCADE;
DROP TABLE IF EXISTS alertas               CASCADE;
DROP TABLE IF EXISTS rotas_fms             CASCADE;
DROP TABLE IF EXISTS telemetria_navegacao  CASCADE;
DROP TABLE IF EXISTS telemetria_waic       CASCADE;
DROP TABLE IF EXISTS telemetria_radar      CASCADE;
DROP TABLE IF EXISTS telemetria_freios     CASCADE;
DROP TABLE IF EXISTS telemetria_voo        CASCADE;
```

---

## 🐳 Troubleshooting com Docker

| Problema | Solução |
|---|---|
| `container not healthy` | Execute `docker compose logs postgres` para ver o erro |
| `password authentication failed` | Verifique o `.env`. Destrua o volume e recrie: `docker compose down -v && docker compose up -d postgres` |
| `schema.sql: no such file` | Confirme que executou `docker cp` com o caminho correto |
| `table already exists` | O DDL usa `CREATE TABLE IF NOT EXISTS` — é seguro re-executar |
| `port 5432 already in use` | Outro PostgreSQL local está rodando. Pare-o com `net stop postgresql` ou mude a porta no `docker-compose.yml` |
