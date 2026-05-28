# 🗺️ Plano 03 — O Que Falta: Visão Global do Projeto

> **Sistema:** Gateway Tolerante a Falhas para Redes Aviônicas Híbridas (AFDX/WAIC)  
> **Data da análise:** Maio de 2026  
> **Análise feita sobre:** backend (Spring Boot 4 / Java 25), frontend (Vue 3 / Vite), API Python (MQTT), infra (Docker Compose), banco (PostgreSQL 17 + Kafka)

---

## 📊 Resumo Executivo do Estado Atual

| Camada | O que existe | Status |
|---|---|---|
| **Backend** | Spring Boot com JDBC, MQTT listener, 2 controllers REST | 🟡 Parcial |
| **Frontend** | Vue 3 com dashboard de telemetria, polling a cada 2s | 🟡 Parcial |
| **API Python** | 10+ microsserviços simulando sensores via MQTT | 🟡 Parcial |
| **Banco de Dados** | PostgreSQL no Docker, sem schema DDL, sem persistência | 🔴 Ausente |
| **Kafka** | Configurado no Docker Compose, sem uso no código | 🔴 Ausente |
| **Infra** | Docker Compose funcional com todos os serviços | 🟢 Funcional |
| **Autenticação** | Nenhuma | 🔴 Ausente |
| **Testes** | Nenhum teste escrito | 🔴 Ausente |

---

## 🔴 BACKEND — O que falta

### 1. Persistência no Banco (Crítico)

O backend **não persiste nada** no PostgreSQL. Toda telemetria existe apenas em memória (a fila `recentMessages` com 30 itens). Se o container reiniciar, tudo se perde.

**O que implementar:**
- [ ] Aplicar o schema DDL do Plano 01
- [ ] Migrar de `spring-boot-starter-jdbc` para `spring-boot-starter-data-jpa`
- [ ] Criar as entidades JPA (conforme Plano 02)
- [ ] Criar os repositories Spring Data
- [ ] Criar `TelemetriaPersistenceService` para salvar mensagens MQTT no banco
- [ ] Integrar o service no `AircraftTelemetryService.messageArrived()`

---

### 2. Uso do Apache Kafka (Crítico)

O Kafka está no Docker Compose e nas dependências do `build.gradle`, mas **não há nenhum producer nem consumer** implementado no código Java.

**O que implementar:**
- [ ] Criar `KafkaConfig.java` com `ProducerFactory` e `KafkaTemplate` configurados
- [ ] Criar `TelemetriaKafkaProducer.java` — publicar cada mensagem MQTT recebida num tópico Kafka (ex: `avionica.telemetria.voo`, `avionica.alertas`)
- [ ] Criar `AlertaKafkaConsumer.java` — consumir do tópico de alertas e persistir no banco
- [ ] Definir tópicos Kafka no `application.yml`
- [ ] Justificativa: Kafka garante o desacoplamento e a resiliência entre os serviços — mensagens não são perdidas se o banco estiver temporariamente indisponível

---

### 3. Endpoints REST Faltando

Atualmente existem apenas 2 endpoints:
- `GET /api/health`
- `GET /api/aircraft-data`

**O que criar:**

| Endpoint | Método | Descrição |
|---|---|---|
| `/api/alertas` | GET | Lista alertas ativos (não resolvidos) |
| `/api/alertas/{id}/resolver` | PATCH | Marca alerta como resolvido |
| `/api/alertas/criticos` | GET | Lista apenas alertas CRITICAL |
| `/api/telemetria/voo` | GET | Histórico paginado de telemetria de voo |
| `/api/telemetria/radar` | GET | Histórico paginado de radar |
| `/api/rotas` | GET | Rota FMS ativa |
| `/api/rotas` | POST | Cadastra nova rota (enviar MQTT para FMS) |
| `/api/comandos/velocidade` | POST | Envia comando de velocidade para os sensores |
| `/api/comandos/rota` | POST | Envia comando de rota para o FMS |
| `/api/modulos` | GET | Já existe — retornar status real dos módulos |

---

### 4. CORS e Segurança

O `CorsConfig.java` existe mas provavelmente está com `allowedOrigins("*")`. Em produção:

- [ ] Configurar CORS para aceitar apenas o domínio do frontend
- [ ] Adicionar Spring Security com JWT ou API Key para os endpoints sensíveis (comandos)
- [ ] Adicionar rate limiting para prevenir sobrecarga

---

### 5. Tratamento de Erros e Validação

- [ ] Criar `@ControllerAdvice` global para retornar erros HTTP padronizados (JSON)
- [ ] Adicionar `@Valid` + Bean Validation nos endpoints POST
- [ ] Logar erros de persistência sem derrubar o serviço MQTT

---

### 6. Configuração de `@EnableAsync`

O service de persistência usará `@Async` para não bloquear callbacks MQTT. Falta:

- [ ] Adicionar `@EnableAsync` na `AvionicaBackendApplication`
- [ ] Criar `AsyncConfig.java` com `ThreadPoolTaskExecutor` configurado (tamanho do pool, fila, nome das threads)

---

## 🟡 FRONTEND — O que falta

### 1. Visual — Design Básico

O frontend usa **Bootstrap via CDN** com layout minimalista. O design atual é funcional mas não representa um sistema aviônico de missão crítica.

**O que melhorar:**
- [ ] Substituir Bootstrap genérico por design system próprio (dark mode, cores inspiradas em HUDs de aeronaves)
- [ ] Usar Google Fonts (ex: `Inter` ou `JetBrains Mono` para os dados numéricos)
- [ ] Adicionar indicadores visuais animados (gauge de altitude, velocímetro de Mach, barra de combustível)
- [ ] Aplicar glassmorphism no painel principal
- [ ] Adicionar micro-animações quando um valor muda (highlight por 1 segundo)

---

### 2. Página de Alertas

Não existe nenhuma tela de alertas no frontend. Os dados de alertas chegam no `AircraftDataSnapshot` mas sem UI dedicada.

**O que criar:**
- [ ] Componente `AlertPanel.vue` — lista de alertas com badge de severidade colorido
- [ ] Badge contador de alertas críticos na navbar
- [ ] Modal para detalhar e resolver um alerta
- [ ] Animação de pulsação vermelha quando há alertas CRITICAL ativos

---

### 3. Página de Rotas FMS

Não existe visualização de rota no frontend.

**O que criar:**
- [ ] Componente `RotaFmsPanel.vue` — exibe origem, destino, distância, ETA
- [ ] Formulário para enviar nova rota (ICAO origem + destino)
- [ ] Integração com `POST /api/comandos/rota`

---

### 4. Comandos Interativos do Cockpit

O frontend só lê dados. O sistema tem tópicos MQTT de comando (`avionica/comandos/velocidade`, `avionica/comandos/rota`) mas o frontend não pode enviar comandos ainda.

**O que criar:**
- [ ] Componente `CockpitControls.vue` — painel de controle com:
  - Slider de velocidade Mach (0.70 → 0.90)
  - Input de rota (ICAO origem/destino)
  - Botão de ativar/desativar piloto automático
- [ ] Integração com os novos endpoints REST de comandos no backend

---

### 5. Histórico e Gráficos

O frontend só mostra o valor mais recente de cada sensor. Não há gráficos históricos.

**O que criar:**
- [ ] Integrar uma biblioteca de gráficos (recomendado: `Chart.js` via `vue-chartjs` ou `ApexCharts`)
- [ ] Gráfico de linha de `altitude_ft` vs tempo (últimas 50 leituras)
- [ ] Gráfico de linha de `combustivel_pct` vs tempo (tendência de consumo)
- [ ] Gráfico de linha de `velocidade_mach` vs tempo

---

### 6. Indicadores de Saúde dos Módulos

O endpoint `GET /api/modules` já existe no backend, mas o frontend não usa esses dados.

**O que criar:**
- [ ] Componente `ModuleHealthGrid.vue` — grade com status de cada módulo Docker
- [ ] Indicadores coloridos: verde (UP), amarelo (PLANNED), cinza (INFRASTRUCTURE)
- [ ] Atualização automática dos status

---

### 7. Reconexão e Estado de Rede

O frontend faz polling a cada 2 segundos via Axios, mas sem feedback visual quando há falha de rede.

**O que melhorar:**
- [ ] Indicador de "Tentando reconectar..." com spinner quando o backend está offline
- [ ] Substituir polling por **Server-Sent Events (SSE)** ou **WebSocket** para push em tempo real
- [ ] Toast notification quando a conexão é restaurada

---

### 8. Responsividade Mobile

O layout atual usa Bootstrap grid mas não foi testado em telas menores.

- [ ] Testar e ajustar layout em mobile (375px)
- [ ] Navbar colapsável em telas pequenas
- [ ] Cards de telemetria em scroll vertical em mobile

---

## 🐍 API PYTHON — O que falta

### 1. Módulos Não Integrados ao Docker

Os seguintes arquivos Python existem mas **não estão no `docker-compose.yml`**:

| Arquivo | Função | Status |
|---|---|---|
| `caixa_preta.py` | Registra eventos no barramento | ❌ Não no compose |
| `consenso_motor.py` | TMR — votador triplo | ❌ Não no compose |
| `injetor_falhas.py` | Injeta falhas simuladas | ❌ Não no compose |
| `sensor_cabo.py` | Sensor via cabo (AFDX) | ❌ Não no compose |
| `sensor_motor.py` | Sensor do motor | ❌ Não no compose |
| `sistema_alertas.py` | Gera alertas automáticos | ❌ Não no compose |
| `computador_voo.py` | Computador de voo completo | ❌ Não no compose |

**O que fazer:**
- [ ] Adicionar os serviços faltantes no `docker-compose.yml`
- [ ] Verificar dependências entre eles (ex: `consenso_motor` depende de `sensor_motor`)
- [ ] Definir quais são de execução contínua e quais são one-shot (ex: `injetor_falhas`)

---

### 2. `fms_distribuido.py` — FMS_API_KEY Não Configurada

O FMS usa a API Ninjas para buscar coordenadas de aeroportos. Se `FMS_API_KEY` estiver vazia, ele não calcula rotas.

**O que fazer:**
- [ ] Adicionar `FMS_API_KEY` válida no `.env`
- [ ] Criar fallback com banco de coordenadas locais (SBGR, EGLL, KJFK, LEMD, SBGL) para funcionar sem API externa
- [ ] Adicionar tratamento de erro com retry quando a API externa falha

---

### 3. Qualidade e Robustez do Código Python

- [ ] Substituir `except: pass` por tratamento de erro explícito (todos os arquivos Python usam isso)
- [ ] Adicionar `logging` estruturado (JSON) em vez de `print()` para integração com sistemas de observabilidade
- [ ] Definir `requirements.txt` ou `pyproject.toml` com versões fixas das dependências
- [ ] Adicionar `healthcheck` nos containers Python no `docker-compose.yml`

---

### 4. Protocolo MQTT — QoS e Persistência

Atualmente todos os sensores publicam com **QoS 0** (fire and forget). Em um sistema de aviação crítico:

- [ ] Migrar alertas e falhas para **QoS 2** (exactly once) no MQTT
- [ ] Migrar telemetria de voo para **QoS 1** (at least once)
- [ ] Configurar `retained=True` nos tópicos de status atual dos sensores
- [ ] Configurar `clean_session=False` nos subscribers críticos

---

### 5. `computador_voo.py` — Arquivo Grande Não Integrado

O arquivo `computador_voo.py` tem 19.860 bytes — é o maior do projeto — mas não está no `docker-compose.yml` nem referenciado em nenhum lugar.

- [ ] Analisar o que este arquivo faz e integrá-lo à arquitetura
- [ ] Verificar sobreposição com `sensores_voo.py` e `computador_automacao.py`

---

## 🏗️ INFRA — O que falta

### 1. Kafka sem Tópicos e UI

- [ ] Criar tópicos Kafka automaticamente via `kafka-topics.sh` no startup (pode ser um `init-container` no Docker Compose)
- [ ] Adicionar **Kafka UI** (ex: `provectuslabs/kafka-ui`) ao `docker-compose.yml` para desenvolvimento

### 2. Sem Migrations de Banco

Atualmente o schema é manual. Para produção:

- [ ] Adicionar **Flyway** ou **Liquibase** para gerenciar migrations de forma versionada
- [ ] Criar a migration `V1__initial_schema.sql` com o DDL do Plano 01
- [ ] Configurar `spring.flyway.enabled=true` no `application.yml`

### 3. Sem Observabilidade

- [ ] Adicionar **Prometheus** ao `docker-compose.yml` para coletar métricas do Spring Actuator
- [ ] Adicionar **Grafana** com dashboards pré-configurados para telemetria aviônica
- [ ] Adicionar **Loki** para agregação de logs dos containers Python
- [ ] Expor métricas Micrometer no backend (`management.endpoints.web.exposure.include: health,info,prometheus`)

### 4. Sem Rede Docker Isolada

Todos os serviços estão na rede padrão do Docker. Para isolamento correto:

- [ ] Criar redes Docker nomeadas no `docker-compose.yml`:
  - `avionica_mqtt_net` — apenas sensores Python e backend
  - `avionica_backend_net` — backend + banco + kafka
  - `avionica_frontend_net` — frontend + backend

### 5. `.env.example` Desatualizado

O `.env.example` não inclui todas as variáveis necessárias (ex: `FMS_API_KEY`):

- [ ] Atualizar `.env.example` com todas as variáveis
- [ ] Adicionar comentários explicativos para cada variável

---

## 🧪 TESTES — O que falta

Não existe **nenhum** teste escrito no projeto.

### Backend (JUnit 5 + Spring Boot Test)

- [ ] Teste unitário para `AircraftTelemetryService.snapshot()`
- [ ] Teste de integração para `AircraftDataController` com `@WebMvcTest`
- [ ] Teste de repositório JPA com `@DataJpaTest` e banco H2 em memória
- [ ] Teste do `TelemetriaPersistenceService` com mock do repository

### Frontend (Vitest + Vue Test Utils)

- [ ] Teste unitário para o componente `DataCard.vue`
- [ ] Teste da função `toItems()` e `formatValue()` no `App.vue`
- [ ] Teste de snapshot do `App.vue`

### Python (pytest)

- [ ] Testes unitários para `FlightManagementSystem.calcular_distancia()` no `fms_distribuido.py`
- [ ] Testes de integração MQTT com broker em memória (ex: `hbmqtt`)

---

## 📋 Prioridade de Implementação Sugerida

| Prioridade | Item | Impacto |
|---|---|---|
| 🔴 P0 | Aplicar schema DDL (Plano 01) | Sem isso nada persiste |
| 🔴 P0 | Implementar JPA + persistência (Plano 02) | Core da funcionalidade |
| 🔴 P0 | Integrar Kafka (producer/consumer) | Resiliência e desacoplamento |
| 🟠 P1 | Adicionar módulos Python ao Docker Compose | Arquitetura completa |
| 🟠 P1 | Criar endpoints REST de alertas e comandos | Frontend depende disso |
| 🟠 P1 | Criar UI de alertas no frontend | Visibilidade de falhas |
| 🟡 P2 | Adicionar gráficos históricos no frontend | UX de monitoramento |
| 🟡 P2 | Adicionar Flyway para migrations | Produção |
| 🟡 P2 | Adicionar Prometheus + Grafana | Observabilidade |
| 🟢 P3 | Testes unitários e de integração | Qualidade |
| 🟢 P3 | Segurança (JWT/API Key) | Produção |
| 🟢 P3 | Substituir polling por SSE/WebSocket | Performance |
