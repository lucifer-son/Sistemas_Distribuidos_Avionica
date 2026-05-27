# 📋 Análise do Backend — Sistema Distribuído de Aviônica

> **Documento de análise técnica e sugestões de melhoria**
> Atualizado após refatoração de maio de 2026 | Projeto: Gateway Tolerante a Falhas AFDX/WAIC

---

## 🔄 O que Mudou na Refatoração

A refatoração moveu os arquivos Java de:

```
src/main/java/br/edu/avionica/   ← estrutura Maven/Gradle padrão
```

Para:

```
src/main/avionica/               ← estrutura customizada
```

> [!CAUTION]
> **Esta mudança quebra a compilação do projeto!**
> O Gradle espera que o código-fonte Java esteja em `src/main/java/`. A pasta `src/main/avionica/` não é reconhecida pelo Gradle como source set padrão. O `gradlew build` vai compilar sem nenhum arquivo e gerar um JAR vazio.

### Comparativo Antes × Depois

| Aspecto                       | Antes (original)                            | Depois (refatorado)                          |
|-------------------------------|---------------------------------------------|----------------------------------------------|
| Localização dos arquivos      | `src/main/java/br/edu/avionica/`            | `src/main/avionica/`                         |
| Diretório source padrão Gradle | ✅ Correto (`src/main/java`)                | ❌ Incorreto (`src/main/avionica`)            |
| Declaração `package`          | `package br.edu.avionica.*`                 | `package br.edu.avionica.*` (inalterado)     |
| Código dos arquivos           | Inalterado                                  | Inalterado (apenas movido de pasta)          |
| Typo no nome da classe        | `AircrafTelemetriaServiso` ❌               | `AircrafTelemetriaServiso` ❌ (ainda existe) |
| Conflito pacote vs. diretório | `telemetry` ≠ `telemetria` ❌              | `telemetry` ≠ `telemetria` ❌ (ainda existe) |

---

## 1. Visão Geral da Arquitetura Atual

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Vue.js)                       │
│                  Porta 5173 — Interface Web                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP REST (polling)
┌──────────────────────────▼──────────────────────────────────┐
│              BACKEND-GATEWAY (Spring Boot 4 + Java 25)       │
│               Porta 8080 — API REST + MQTT Client            │
└────────┬──────────────────────────────────────┬─────────────┘
         │ JDBC (conecta, mas não persiste)      │ MQTT Subscribe
┌────────▼────────┐                  ┌───────────▼────────────┐
│   PostgreSQL 17  │                  │   Mosquitto MQTT Broker │
│  Porta 5432      │                  │   Porta 1883            │
└─────────────────┘                  └───────────┬─────────────┘
                                                  │ MQTT Publish
                    ┌────────────────────┬─────────┴──────────┬────────────────────┐
                    │                    │                     │                    │
          ┌─────────▼──────┐  ┌──────────▼──────┐  ┌─────────▼─────┐  ┌──────────▼──────┐
          │  sensor-flight  │  │  sensor-brake   │  │    radar      │  │  navigation-    │
          │  (Python)       │  │  (Python)       │  │  (Python)     │  │  computer (Py)  │
          └────────────────┘  └─────────────────┘  └───────────────┘  └─────────────────┘
                    │
          ┌─────────▼──────┐  ┌─────────────────┐  ┌───────────────┐
          │ automation-    │  │  waic-leader    │  │   fms-api     │
          │ computer (Py)  │  │  (Python)       │  │  (Python)     │
          └────────────────┘  └─────────────────┘  └───────────────┘

         [Apache Kafka 4.1.1 — no ar, mas sem produtores/consumidores no backend]
```

---

## 2. Problema Crítico Introduzido pela Refatoração

### 2.1 ❌ Diretório Fora do Source Set Padrão do Gradle

O Gradle (e o Maven) em projetos Java seguem a **convenção sobre configuração**: o código-fonte Java **deve** estar em `src/main/java/`. O Gradle procura classes para compilar exatamente neste caminho.

**Estrutura atual (incorreta):**
```
backend/
└── src/
    └── main/
        ├── avionica/          ← ❌ Gradle NÃO compila arquivos aqui
        │   ├── api/
        │   ├── config/
        │   └── telemetria/
        └── resources/
            └── application.yml
```

**Estrutura correta (padrão Gradle/Maven):**
```
backend/
└── src/
    └── main/
        ├── java/              ← ✅ Gradle compila arquivos aqui
        │   └── br/edu/avionica/
        │       ├── api/
        │       ├── config/
        │       └── telemetria/
        └── resources/
            └── application.yml
```

**Como corrigir:** Mover os arquivos de volta para `src/main/java/br/edu/avionica/` (ou configurar um source set customizado no `build.gradle`).

**Opção alternativa** (se quiser manter a estrutura customizada):
```groovy
// build.gradle — adicionar source set customizado
sourceSets {
    main {
        java {
            srcDirs = ['src/main/avionica']
        }
    }
}
```

> [!WARNING]
> Mesmo com a configuração de source set acima, o `package br.edu.avionica.*` declarado nos arquivos precisa bater com a estrutura de diretórios **dentro** do source set. Atualmente `telemetria/AircraftTelemetriaService.java` declara `package br.edu.avionica.telemetry` (em inglês), mas a pasta é `telemetria` (em português). Isso causará erro de compilação mesmo após corrigir o source set.

---

## 3. Problemas que Continuam Existindo (não resolvidos pela refatoração)

### 3.1 ❌ Conflito entre Nome do Pacote e Nome do Diretório

Todos os arquivos no diretório `telemetria/` declaram:
```java
package br.edu.avionica.telemetry;  // ← "telemetry" em inglês
```

Mas o diretório físico é `telemetria/` (em português). Em Java, o nome do pacote **deve** corresponder exatamente à hierarquia de diretórios. Isso causa:
- Erro de compilação no Gradle
- Confusão para todos os integrantes da equipe

**Escolha e aplique um padrão único:**

| Opção | Diretório               | Declaração package                  |
|-------|-------------------------|-------------------------------------|
| A     | `telemetria/`           | `package br.edu.avionica.telemetria;`|
| B     | `telemetry/`            | `package br.edu.avionica.telemetry;` |

---

### 3.2 ❌ Typo no Nome da Classe de Serviço (persiste desde a versão anterior)

Em [AircraftTelemetriaService.java](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/src/main/avionica/telemetria/AircraftTelemetriaService.java):

```java
// Linha 29 — nome da classe com dois erros:
public class AircrafTelemetriaServiso implements MqttCallbackExtended {
//           ↑ falta "t"       ↑ "Serviso" ≠ "Service"
```

Em [AircraftDataController.java](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/src/main/avionica/api/AircraftDataController.java):

```java
// Linha 4 e 12 — import e uso com nome errado:
import br.edu.avionica.telemetry.AircrafTelemetriaServiso;
private final AircrafTelemetriaServiso  telemetryService;  // note o espaço extra
```

---

### 3.3 ❌ Kafka configurado mas não utilizado

O `application.yml` configura o Kafka em dois lugares:
```yaml
spring:
  kafka:
    bootstrap-servers: ${KAFKA_BOOTSTRAP_SERVERS:localhost:9092}

app:
  kafka:
    bootstrap-servers: ${KAFKA_BOOTSTRAP_SERVERS:localhost:9092}
```

O `build.gradle` tem a dependência:
```groovy
implementation 'org.springframework.kafka:spring-kafka'
```

Mas **não existe nenhum** `@KafkaListener` ou `KafkaTemplate` no código. O Kafka sobe no Docker, ocupa memória e CPU, sem nenhum benefício.

---

### 3.4 ❌ PostgreSQL sem nenhuma tabela ou dado persistido

O `spring-boot-starter-jdbc` está nas dependências e o `application.yml` configura a URL do banco. O Spring conecta com sucesso ao PostgreSQL, mas **não há nenhuma classe de repositório, DAO ou SQL** no projeto. Nenhum dado de telemetria é salvo em disco.

---

### 3.5 ❌ Status dos módulos é hardcoded

O endpoint `GET /api/modules` em [HealthController.java](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/src/main/avionica/api/HealthController.java) retorna sempre a mesma lista estática:

```java
module("fms-api", "Python", "PLANNED"),      // Sempre PLANNED, mesmo rodando
module("sensor-flight", "Python", "PLANNED"), // Sempre PLANNED, mesmo rodando
```

---

## 4. Mapeamento Completo dos Arquivos Atuais

### 4.1 Estrutura de Pacotes Java (pós-refatoração)

```
src/main/avionica/                           ← ⚠️ Fora do source set padrão
├── AvionicaBackendApplication.java          package br.edu.avionica
├── api/
│   ├── AircraftDataController.java          package br.edu.avionica.api
│   └── HealthController.java               package br.edu.avionica.api
├── config/
│   ├── CorsConfig.java                      package br.edu.avionica.config
│   └── StartupLogger.java                  package br.edu.avionica.config
└── telemetria/                              ← ⚠️ diretório em PT, pacote em EN
    ├── AircraftDataSnapshot.java            package br.edu.avionica.telemetry ← ⚠️
    ├── AircraftMessage.java                 package br.edu.avionica.telemetry ← ⚠️
    └── AircraftTelemetriaService.java       package br.edu.avionica.telemetry ← ⚠️
                                             class AircrafTelemetriaServiso    ← ⚠️ typo
```

### 4.2 Responsabilidade de cada Classe

| Arquivo | Função |
|---------|--------|
| [AvionicaBackendApplication.java](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/src/main/avionica/AvionicaBackendApplication.java) | Ponto de entrada Spring Boot (`main`) |
| [AircraftDataController.java](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/src/main/avionica/api/AircraftDataController.java) | `GET /api/aircraft-data` → retorna snapshot de telemetria |
| [HealthController.java](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/src/main/avionica/api/HealthController.java) | `GET /api/health` e `GET /api/modules` (status hardcoded) |
| [CorsConfig.java](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/src/main/avionica/config/CorsConfig.java) | Libera CORS para `localhost:5173` |
| [StartupLogger.java](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/src/main/avionica/config/StartupLogger.java) | Loga URLs úteis ao subir (`@PostConstruct`) |
| [AircraftTelemetriaService.java](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/src/main/avionica/telemetria/AircraftTelemetriaService.java) | Conecta ao MQTT, recebe mensagens, mantém snapshot em memória |
| [AircraftDataSnapshot.java](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/src/main/avionica/telemetria/AircraftDataSnapshot.java) | `record` com os campos de telemetria (voo, freios, radar, FMS…) |
| [AircraftMessage.java](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/src/main/avionica/telemetria/AircraftMessage.java) | `record` com tópico, timestamp e payload de uma mensagem MQTT |

---

## 5. O Serviço de Telemetria — Como Funciona (detalhado)

O [AircraftTelemetriaService.java](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/src/main/avionica/telemetria/AircraftTelemetriaService.java) é o componente mais importante do backend. Ele funciona assim:

```
@PostConstruct start()
       │
       ▼
MqttClient.connect(brokerUrl)
       │
       ▼
client.subscribe("avionica/#")   ← assina TODOS os tópicos aviônicos
       │
       ▼  [ao chegar mensagem]
messageArrived(topic, mqttMessage)
       │
       ├─► latestByTopic.put(topic, message)   ← ConcurrentHashMap (última por tópico)
       │
       └─► recentMessages.addLast(message)     ← ArrayDeque limitada a 30 mensagens
                    synchronized

       │  [ao chamar GET /api/aircraft-data]
       ▼
snapshot()
       │
       ├─► lê latestByTopic para cada tópico fixo
       │   (sensores/voo, sensores/freios, radar, fms/dados, navegacao, waic, anti_ice, falhas)
       │
       └─► retorna AircraftDataSnapshot (Record imutável)
```

**Detalhes técnicos da implementação:**

| Aspecto | Decisão | Avaliação |
|---|---|---|
| Thread-safety do mapa | `ConcurrentHashMap` | ✅ Correto |
| Thread-safety da fila | `synchronized (recentMessages)` | ✅ Correto |
| Reconexão automática | `setAutomaticReconnect(true)` | ✅ Correto |
| Re-subscribe após reconexão | `connectComplete()` reinscreve | ✅ Correto |
| Tamanho máximo da fila | 30 mensagens | ⚠️ Baixo para demonstração |
| Persistência | Nenhuma — tudo em memória | ❌ Dados perdidos ao reiniciar |
| Client ID | `UUID.randomUUID()` a cada startup | ⚠️ Gera sessões órfãs no broker |

---

## 6. Sugestões de Melhoria (Prioridade Atualizada)

### 🔴 6.1 Corrigir a Localização dos Arquivos (URGENTE — o projeto não compila)

**Problema:** Arquivos em `src/main/avionica/` não são compilados pelo Gradle.

**Solução A — Mover para o local padrão:**
```powershell
# Mover os arquivos para a estrutura correta
New-Item -Path "backend\src\main\java\br\edu\avionica" -ItemType Directory -Force
Move-Item "backend\src\main\avionica\*" "backend\src\main\java\br\edu\avionica\"
```

**Solução B — Configurar source set customizado no `build.gradle`:**
```groovy
// Adicionar ao build.gradle
sourceSets {
    main {
        java {
            srcDirs = ['src/main/avionica']
        }
    }
}
```

**Por quê:** Sem isso, o `gradlew build` gera um JAR sem nenhuma classe. A aplicação não sobe. Este é o problema mais crítico do momento.

---

### 🔴 6.2 Corrigir o Conflito de Pacote vs. Diretório (URGENTE)

**Problema:** Arquivos em `telemetria/` declaram `package br.edu.avionica.telemetry` (inglês).

**Solução:** Escolher e padronizar **uma** nomenclatura. Recomendação: renomear o diretório para `telemetry/` (inglês), alinhando com a convenção do código:

```powershell
Rename-Item "backend\src\main\avionica\telemetria" "telemetry"
# ou, se preferir PT:
# Alterar package em todos os arquivos para br.edu.avionica.telemetria
```

**Por quê:** Em Java, o compilador exige que a hierarquia de diretórios corresponda exatamente ao `package` declarado. A inconsistência atual (diretório `telemetria`, pacote `telemetry`) causa `package does not exist` durante a compilação.

---

### 🔴 6.3 Corrigir o Typo no Nome da Classe (URGENTE)

**Problema:** `AircrafTelemetriaServiso` — dois erros de digitação.

**Correção em [AircraftTelemetriaService.java](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/src/main/avionica/telemetria/AircraftTelemetriaService.java) (linhas 29–30):**
```java
// Antes:
public class AircrafTelemetriaServiso implements MqttCallbackExtended {
    private static final Logger logger = LoggerFactory.getLogger(AircrafTelemetriaServiso.class);

// Depois:
public class AircraftTelemetryService implements MqttCallbackExtended {
    private static final Logger logger = LoggerFactory.getLogger(AircraftTelemetryService.class);
```

**Correção em [AircraftDataController.java](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/src/main/avionica/api/AircraftDataController.java) (linhas 4, 12, 14):**
```java
// Antes:
import br.edu.avionica.telemetry.AircrafTelemetriaServiso;
private final AircrafTelemetriaServiso  telemetryService;
public AircraftDataController(AircrafTelemetriaServiso  telemetryService) {

// Depois:
import br.edu.avionica.telemetry.AircraftTelemetryService;
private final AircraftTelemetryService telemetryService;
public AircraftDataController(AircraftTelemetryService telemetryService) {
```

**Por quê:** Nomes de classe errados poluem o código, dificultam a busca global, quebram o Javadoc e mostram falta de atenção em código destinado à avaliação acadêmica.

---

### 🔴 6.4 Implementar Persistência no PostgreSQL (Alta Prioridade)

**Problema:** O banco está no ar, mas não recebe nenhum dado.

**Melhoria sugerida:** Criar tabela de telemetria e persistir cada mensagem MQTT recebida.

**SQL (criar em `src/main/resources/schema.sql` ou com Flyway):**
```sql
CREATE TABLE IF NOT EXISTS telemetry_events (
    id          BIGSERIAL    PRIMARY KEY,
    topic       VARCHAR(200) NOT NULL,
    source      VARCHAR(100),
    payload     TEXT         NOT NULL,
    received_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_telemetry_topic ON telemetry_events(topic);
CREATE INDEX IF NOT EXISTS idx_telemetry_received ON telemetry_events(received_at DESC);
```

**Java — adicionar ao serviço de telemetria:**
```java
// Injetar JdbcTemplate no AircraftTelemetryService
private final JdbcTemplate jdbc;

// No método messageArrived(), após salvar em memória:
jdbc.update(
    "INSERT INTO telemetry_events (topic, payload) VALUES (?, ?)",
    topic,
    rawPayload
);
```

**Por quê:** Sem persistência, o histórico de telemetria desaparece ao reiniciar o container. O requisito da disciplina menciona explicitamente "consultar histórico persistido no banco de dados". O PostgreSQL já está no ar e configurado — só falta usar.

---

### 🟡 6.5 Integrar Kafka ao Backend (Média-Alta Prioridade)

**Problema:** Kafka está configurado e rodando, mas sem produtores ou consumidores no backend.

**Melhoria sugerida:** Criar um consumer Spring Kafka para os tópicos dos sensores Python:

```java
@Component
public class TelemetryKafkaConsumer {

    @KafkaListener(topics = "avionica.telemetry.flight", groupId = "backend-gateway")
    public void onFlightData(ConsumerRecord<String, String> record) {
        // processar e salvar no banco
    }
}
```

> [!NOTE]
> Para isso funcionar, os módulos Python também precisariam publicar no Kafka (além ou em vez do MQTT). Esta é uma mudança maior, mas alinha com o plano original do projeto.

**Por quê:** O Kafka garante que mensagens sejam **entregues mesmo se o backend estiver offline** (as mensagens ficam no log do Kafka e são reprocessadas ao reconectar). Com MQTT puro, qualquer queda do backend significa perda de dados.

---

### 🟡 6.6 Implementar Health Check Real dos Módulos (Média Prioridade)

**Problema:** `GET /api/modules` retorna status hardcoded.

**Melhoria sugerida:** Cada módulo Python publica em `avionica/health/<nome>` a cada 10 segundos. O backend monitora o tempo da última mensagem:

```java
// Verificar se o módulo publicou nos últimos 30 segundos
public String getModuleStatus(String moduleName) {
    AircraftMessage last = latestByTopic.get("avionica/health/" + moduleName);
    if (last == null) return "UNKNOWN";
    return last.receivedAt().isAfter(Instant.now().minusSeconds(30)) ? "UP" : "DOWN";
}
```

```python
# Adicionar a cada módulo Python (exemplo em sensores_voo.py):
while True:
    cliente.publish(f"avionica/health/sensor-flight", json.dumps({"ts": time.time()}))
    # ... resto do loop
    time.sleep(10)
```

**Por quê:** Demonstrar monitoramento dinâmico ao professor é um diferencial enorme. Com este mecanismo, é possível derrubar um container ao vivo e mostrar o dashboard mudando de `UP` para `DOWN` em tempo real.

---

### 🟡 6.7 Aumentar o Tamanho do Buffer de Mensagens Recentes (Média Prioridade)

**Problema:** A fila `recentMessages` está limitada a 30 mensagens:

```java
// AircraftTelemetriaService.java, linha 119
while (recentMessages.size() > 30) {
    recentMessages.removeFirst();
}
```

Com ~7 módulos publicando a cada 1–3 segundos, 30 mensagens correspondem a apenas **4–10 segundos** de histórico.

**Melhoria:** Aumentar para 200–500 e tornar configurável:

```java
// application.yml
app:
  telemetry:
    buffer-size: ${TELEMETRY_BUFFER_SIZE:200}

// No serviço:
@Value("${app.telemetry.buffer-size:200}")
private int bufferSize;

// No método messageArrived():
while (recentMessages.size() > bufferSize) {
    recentMessages.removeFirst();
}
```

**Por quê:** Um buffer de 10 segundos é insuficiente para qualquer análise ou demonstração significativa. Com 200 mensagens, o frontend pode mostrar um histórico visual dos últimos 3–5 minutos de voo sem precisar de banco de dados.

---

### 🟡 6.8 Remover a Configuração Duplicada do Kafka no `application.yml` (Baixa Esforço)

**Problema:** O Kafka está configurado duas vezes no `application.yml`:

```yaml
spring:
  kafka:
    bootstrap-servers: ${KAFKA_BOOTSTRAP_SERVERS:localhost:9092}  # ← Config Spring padrão

app:
  kafka:
    bootstrap-servers: ${KAFKA_BOOTSTRAP_SERVERS:localhost:9092}  # ← Config customizada (usada no HealthController)
```

**Melhoria:** Se for usar o Kafka via Spring (com `@KafkaListener`), remover a chave `app.kafka` e usar apenas `spring.kafka`. Se não for usar o Kafka, remover as duas e remover a dependência do `build.gradle`:

```groovy
// Remover do build.gradle se Kafka não for implementado:
// implementation 'org.springframework.kafka:spring-kafka'
```

**Por quê:** Configuração duplicada gera confusão sobre qual é a "oficial". O `HealthController` lê `app.kafka.bootstrap-servers` apenas para exibir o endereço na lista de módulos — o Spring Kafka em si não lê essa chave.

---

### 🟢 6.9 Adicionar WebSocket/SSE para Telemetria em Tempo Real (Diferencial)

**Problema:** O frontend faz polling HTTP para buscar dados novos (gera latência e carga desnecessária).

**Melhoria sugerida:** Usar Server-Sent Events (SSE), mais simples que WebSocket e nativo do Spring MVC:

```java
@GetMapping(value = "/api/telemetry/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public SseEmitter streamTelemetry() {
    SseEmitter emitter = new SseEmitter(Long.MAX_VALUE);
    // registrar emitter e enviar quando chegarem novas mensagens MQTT
    return emitter;
}
```

**Por quê:** Com SSE, o browser recebe dados instantaneamente ao chegar do MQTT, sem polling. Isso cria uma experiência de dashboard "ao vivo" muito mais impressionante para a apresentação do projeto.

---

## 7. Resumo das Ações Necessárias

| Prioridade | Ação | Arquivo(s) | Impacto |
|---|---|---|---|
| 🔴 URGENTE | Corrigir localização dos arquivos (`src/main/java/` ou configurar source set) | `build.gradle` | Projeto não compila sem isso |
| 🔴 URGENTE | Corrigir conflito `telemetria/` vs. `package telemetry` | Todos em `telemetria/` | Erro de compilação |
| 🔴 URGENTE | Corrigir typo `AircrafTelemetriaServiso` → `AircraftTelemetryService` | `AircraftTelemetriaService.java`, `AircraftDataController.java` | Qualidade + compilação |
| 🔴 Alta | Persistir telemetria no PostgreSQL | `AircraftTelemetriaService.java` + SQL | Requisito da disciplina |
| 🟡 Média | Integrar Kafka ao backend | Novo `TelemetryKafkaConsumer.java` | Requisito da disciplina |
| 🟡 Média | Health check real dos módulos | `HealthController.java` + módulos Python | Demonstração ao professor |
| 🟡 Média | Aumentar buffer de mensagens para 200+ | `AircraftTelemetriaService.java` | Qualidade da demonstração |
| 🟡 Média | Limpar configuração duplicada do Kafka | `application.yml`, `build.gradle` | Clareza do código |
| 🟢 Baixa | SSE/WebSocket para telemetria em tempo real | Novo controller SSE | Diferencial de UX |

---

## 8. Como Corrigir os Problemas Críticos Rapidamente

### Opção 1 — Mover arquivos de volta para o local padrão

```powershell
# Executar na raiz do projeto
New-Item -ItemType Directory -Force -Path "backend\src\main\java\br\edu\avionica\api"
New-Item -ItemType Directory -Force -Path "backend\src\main\java\br\edu\avionica\config"
New-Item -ItemType Directory -Force -Path "backend\src\main\java\br\edu\avionica\telemetry"

Copy-Item "backend\src\main\avionica\AvionicaBackendApplication.java" `
          "backend\src\main\java\br\edu\avionica\"

Copy-Item "backend\src\main\avionica\api\*" `
          "backend\src\main\java\br\edu\avionica\api\"

Copy-Item "backend\src\main\avionica\config\*" `
          "backend\src\main\java\br\edu\avionica\config\"

Copy-Item "backend\src\main\avionica\telemetria\*" `
          "backend\src\main\java\br\edu\avionica\telemetry\"
```

Depois atualizar as declarações de pacote nos arquivos da pasta `telemetry/` para:
```java
package br.edu.avionica.telemetry;  // já está correto nos arquivos
```

### Opção 2 — Manter a pasta customizada com configuração no Gradle

```groovy
// Adicionar ao backend/build.gradle
sourceSets {
    main {
        java {
            srcDirs = ['src/main/avionica']
        }
        resources {
            srcDirs = ['src/main/resources']
        }
    }
}
```

E renomear `telemetria/` → `telemetry/` para alinhar com os packages declarados.

---

## 9. Referências Técnicas

- [Gradle Java Plugin — Source Sets](https://docs.gradle.org/current/userguide/java_plugin.html#sec:java_project_layout)
- [Spring Boot Kafka Integration](https://docs.spring.io/spring-kafka/reference/)
- [Spring MVC Server-Sent Events](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-async.html#mvc-ann-async-sse)
- [Eclipse Paho MQTT v3 — CleanSession vs Persistent Sessions](https://www.eclipse.org/paho/index.php?page=clients/java/index.php)
- [Flyway + Spring Boot](https://flywaydb.org/documentation/usage/plugins/springboot)
