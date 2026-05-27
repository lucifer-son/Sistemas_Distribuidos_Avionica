# 📋 Análise do Backend — Sistema Distribuído de Aviônica

> **Documento de análise técnica, estado atual e roadmap de implementação**
> Última atualização: maio de 2026 | Projeto: Gateway Tolerante a Falhas AFDX/WAIC

---

## 1. Estado Atual — O que já está funcionando ✅

### 1.1 Estrutura do Projeto (pós-refatoração e correções)

```
backend/
├── build.gradle                          ✅ Source set configurado corretamente
├── Dockerfile                            ✅ Multi-stage build (JDK 25 → JRE 25)
└── src/
    └── main/
        ├── avionica/                     ✅ Source root correto (srcDirs = ['src/main'])
        │   ├── AvionicaBackendApplication.java   package avionica
        │   ├── api/
        │   │   ├── AircraftDataController.java   package avionica.api
        │   │   └── HealthController.java         package avionica.api
        │   ├── config/
        │   │   ├── CorsConfig.java               package avionica.config
        │   │   └── StartupLogger.java            package avionica.config
        │   └── telemetry/                        ✅ pasta = package (inglês)
        │       ├── AircraftDataSnapshot.java     package avionica.telemetry
        │       ├── AircraftMessage.java          package avionica.telemetry
        │       └── AircraftTelemetryService.java ✅ nome correto (sem typo)
        └── resources/
            └── application.yml                  ✅ logging aponta para avionica
```

### 1.2 Correções Aplicadas (histórico)

| Problema | Como foi resolvido |
|----------------------------------------------------|--------------------------------------------------------------------------|
| Arquivos fora do source set (`src/main/avionica/`) | `sourceSets { main { java { srcDirs = ['src/main'] }}}` no `build.gradle` |
| Package `br.edu.avionica` ≠ diretório `avionica/`   | Todos os packages alterados para `avionica.*`                             |
| Pasta `telemetria/` ≠ `package telemetry`          | Pasta renomeada para `telemetry/`                                        |
| Typo `AircrafTelemetriaServiso`                    | Classe e arquivo renomeados para `AircraftTelemetryService`              |
| `application.yml` com logger antigo                | `br.edu.avionica: INFO` → `avionica: INFO`                               |
| **Resultado:** `gradlew compileJava` → **BUILD SUCCESSFUL** ✅ |                                                                          |

---

## 2. Arquitetura Atual — O que existe e o que faz

### 2.1 Diagrama de fluxo de dados atual

```
[Vue.js Frontend :5173]
         │
         │  HTTP GET /api/aircraft-data  (polling manual)
         ▼
[Spring Boot Backend :8080]
         │
         │  MQTT Subscribe avionica/#
         ▼
[Eclipse Mosquitto :1883]
         │
         ├──────────────────┬──────────────────┬──────────────────┐
         ▼                  ▼                  ▼                  ▼
  [sensor-flight]    [sensor-brake]       [radar]          [waic-leader]
  (Python — 1s)      (Python — 3s)    (Python — 3s)      (Python — 2s)
         │
         ├──────────────────┬──────────────────┐
         ▼                  ▼                  ▼
 [navigation-comp]  [automation-comp]      [fms-api]
  (Python — 3s)      (Python — evento)  (Python — 2s)

[PostgreSQL :5432]  ← conectado pelo Spring, mas SEM TABELAS criadas
[Kafka :9092]       ← no ar, mas SEM produtores/consumidores no backend
```

### 2.2 Endpoints REST disponíveis

| Endpoint | Método | O que retorna |
|---|---|---|
| `/api/health` | GET | `{"status":"UP","service":"backend-gateway","timestamp":"..."}` |
| `/api/modules` | GET | Lista de módulos com status (hardcoded) |
| `/api/aircraft-data` | GET | Snapshot da telemetria atual (dados em memória) |
| `/actuator/health` | GET | Health check do Spring Actuator |
| `/actuator/info` | GET | Info da aplicação |

### 2.3 Como o serviço de telemetria funciona hoje

```
@PostConstruct → conecta ao MQTT → subscribe("avionica/#")
                                           │
                    ┌──────────────────────▼────────────────────────┐
                    │         messageArrived(topic, message)         │
                    │                                                │
                    │  latestByTopic.put(topic, message)            │
                    │     ConcurrentHashMap — última por tópico     │
                    │                                                │
                    │  recentMessages.addLast(message)              │
                    │     ArrayDeque — limitada a 30 mensagens      │
                    └────────────────────────────────────────────────┘
                                           │
              GET /api/aircraft-data → snapshot()
                    │
                    └── lê latestByTopic para cada tópico fixo
                        monta e retorna AircraftDataSnapshot (record Java)
```

**Pontos positivos da implementação atual:**
- `ConcurrentHashMap` garante thread-safety na leitura/escrita concorrente ✅
- `synchronized(recentMessages)` protege a fila de mensagens ✅
- `setAutomaticReconnect(true)` reconecta automaticamente ao MQTT ✅
- `connectComplete()` re-faz o subscribe após reconexão ✅
- Falha silenciosa no MQTT — API continua no ar sem telemetria ✅

---

## 3. O que está FALTANDO implementar

Esta seção detalha **cada funcionalidade ausente**, porque ela é necessária, e como implementar.

---

### 🔴 3.1 Persistência no PostgreSQL — NENHUM dado é salvo

**Situação atual:** O Spring conecta ao banco, mas não há tabelas, migrations ou queries. Se o backend reiniciar, toda a telemetria em memória é perdida.

**O que precisa ser criado:**

#### Arquivo de schema SQL
Criar `src/main/resources/schema.sql` (Spring JDBC executa automaticamente se configurado):

```text
CREATE TABLE IF NOT EXISTS telemetry_events (
    id          BIGSERIAL    PRIMARY KEY,
    topic       VARCHAR(200) NOT NULL,
    source      VARCHAR(100),
    payload     TEXT         NOT NULL,
    received_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS routes (
    id              BIGSERIAL    PRIMARY KEY,
    origin_icao     VARCHAR(10)  NOT NULL,
    destination_icao VARCHAR(10) NOT NULL,
    distance_nm     NUMERIC(8,2),
    eta_minutes     INTEGER,
    status          VARCHAR(50)  NOT NULL DEFAULT 'PENDING',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system_events (
    id          BIGSERIAL    PRIMARY KEY,
    module_name VARCHAR(100) NOT NULL,
    severity    VARCHAR(20)  NOT NULL,
    message     TEXT         NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```

#### Ativar execução automática no `application.yml`
```yaml
spring:
  sql:
    init:
      mode: always   # executa schema.sql ao subir
```

#### Persistir no serviço de telemetria
Em `AircraftTelemetryService.java`, injetar `JdbcTemplate` e salvar cada mensagem MQTT:

```text
// Adicionar ao AircraftTelemetryService:
private final JdbcTemplate jdbc;

public AircraftTelemetryService(
    @Value("${app.mqtt.broker-url}") String brokerUrl,
    @Value("${app.mqtt.topic-filter}") String topicFilter,
    JdbcTemplate jdbc
) {
    this.brokerUrl = brokerUrl;
    this.topicFilter = topicFilter;
    this.jdbc = jdbc;
}

// No método messageArrived(), após salvar em memória:
try {
    jdbc.update(
        "INSERT INTO telemetry_events (topic, payload) VALUES (?, ?)",
        topic, rawPayload
    );
} catch (Exception e) {
    logger.warn("Falha ao persistir telemetria no banco: {}", e.getMessage());
}
```

#### Novo endpoint para histórico
```text
// Novo método em AircraftDataController ou novo controller:
@GetMapping("/api/telemetry/history")
public List<Map<String, Object>> history(
    @RequestParam(defaultValue = "100") int limit
) {
    return jdbc.queryForList(
        "SELECT topic, payload, received_at FROM telemetry_events ORDER BY received_at DESC LIMIT ?",
        limit
    );
}
```

**Por quê é necessário:** O requisito da disciplina cita "consultar histórico persistido no banco de dados". Sem isso, esse requisito fica zero.

---

### 🔴 3.2 Kafka sem Produtores nem Consumidores

**Situação atual:** O Kafka está configurado em `build.gradle` e `application.yml`, o container sobe, mas o backend não publica nem consome nenhuma mensagem. O Kafka ocupa ~500MB de RAM sem nenhum benefício.

**O que precisa ser criado:**

#### Consumer de telemetria via Kafka
Os módulos Python precisariam publicar também no Kafka (além do MQTT). O backend consumiria do Kafka para garantir que nenhuma mensagem seja perdida durante downtime:

```text
// Criar: src/main/avionica/kafka/TelemetryKafkaConsumer.java
package avionica.kafka;

import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
public class TelemetryKafkaConsumer {

    @KafkaListener(topics = "avionica.telemetry", groupId = "backend-gateway")
    public void onTelemetryMessage(ConsumerRecord<String, String> record) {
        // processar e salvar no banco
        logger.info("Kafka → tópico: {} | payload: {}", record.key(), record.value());
    }
}
```

#### Producer para eventos de rota
Quando o frontend solicitar uma rota, o backend publica no Kafka e o FMS consome:

```text
// Criar: src/main/avionica/kafka/RouteEventProducer.java
package avionica.kafka;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
public class RouteEventProducer {
    private final KafkaTemplate<String, String> kafka;

    public RouteEventProducer(KafkaTemplate<String, String> kafka) {
        this.kafka = kafka;
    }

    public void requestRoute(String origin, String destination) {
        String payload = "{\"origem\":\"" + origin + "\",\"destino\":\"" + destination + "\"}";
        kafka.send("avionica.route.requested", payload);
    }
}
```

**Por quê é necessário:** Kafka é o diferencial de um sistema distribuído real. Com MQTT puro, mensagens enviadas enquanto o backend está offline são perdidas para sempre. O Kafka armazena mensagens por tempo configurável e garante entrega mesmo após reinicialização.

---

### 🔴 3.3 Endpoint de Rotas — Não existe

**Situação atual:** Não há nenhum endpoint `POST /api/routes` ou `GET /api/routes`. O frontend não tem como solicitar uma rota via REST.

**O que precisa ser criado:**

```text
// Criar: src/main/avionica/api/RouteController.java
package avionica.api;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/routes")
public class RouteController {

    private final JdbcTemplate jdbc;

    public RouteController(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    // Solicitar nova rota
    @PostMapping
    public Map<String, Object> requestRoute(@RequestBody Map<String, String> body) {
        String origin = body.get("origin").toUpperCase();
        String destination = body.get("destination").toUpperCase();

        // Salva a solicitação no banco
        jdbc.update(
            "INSERT INTO routes (origin_icao, destination_icao, status) VALUES (?, ?, 'PENDING')",
            origin, destination
        );

        // Publica no MQTT para o FMS Python calcular
        // (ou no Kafka, se implementado)

        return Map.of("status", "PENDING", "origin", origin, "destination", destination);
    }

    // Listar rotas calculadas
    @GetMapping
    public List<Map<String, Object>> listRoutes() {
        return jdbc.queryForList(
            "SELECT * FROM routes ORDER BY created_at DESC LIMIT 50"
        );
    }
}
```

**Por quê é necessário:** Sem este endpoint, o fluxo principal do projeto (usuário solicita rota → FMS calcula → resultado exibido) não existe na camada web.

---

### 🟡 3.4 Health Check Real dos Módulos

**Situação atual:** `GET /api/modules` retorna sempre a mesma lista estática com status `PLANNED` para todos os módulos Python — mesmo quando eles estão rodando.

```text
// Hoje (hardcoded — incorreto):
module("fms-api", "Python", "PLANNED"),       // sempre PLANNED
module("sensor-flight", "Python", "PLANNED"), // sempre PLANNED
```

**O que precisa ser criado:**

Cada módulo Python publica periodicamente em `avionica/health/<nome>`. O backend monitora o tempo da última mensagem:

```text
// Em HealthController.java — substituir a lista hardcoded:
@Autowired
private AircraftTelemetryService telemetry;

@GetMapping("/modules")
public List<Map<String, Object>> modules() {
    return List.of(
        moduleWithCheck("fms-api",             "Python"),
        moduleWithCheck("sensor-flight",       "Python"),
        moduleWithCheck("sensor-brake",        "Python"),
        moduleWithCheck("radar",               "Python"),
        moduleWithCheck("navigation-computer", "Python"),
        moduleWithCheck("automation-computer", "Python"),
        moduleWithCheck("waic-leader",         "Python"),
        module("backend-gateway", "Spring Boot", "UP"),
        module("postgres",        "PostgreSQL",  "INFRASTRUCTURE"),
        module("kafka",           "Apache Kafka","INFRASTRUCTURE", kafkaBootstrapServers),
        module("mqtt-broker",     "Mosquitto",   "INFRASTRUCTURE")
    );
}

private Map<String, Object> moduleWithCheck(String name, String tech) {
    // Verifica se publicou nos últimos 30 segundos
    String heartbeatTopic = "avionica/health/" + name;
    String status = telemetry.isAlive(heartbeatTopic) ? "UP" : "DOWN";
    return module(name, tech, status);
}
```

Adicionar ao `AircraftTelemetryService.java`:
```text
public boolean isAlive(String heartbeatTopic) {
    AircraftMessage last = latestByTopic.get(heartbeatTopic);
    return last != null && last.receivedAt().isAfter(Instant.now().minusSeconds(30));
}
```

Adicionar a cada módulo Python (exemplo `sensores_voo.py`):
```text
# No loop principal, a cada 10 segundos:
cliente.publish("avionica/health/sensor-flight", json.dumps({"ts": time.time()}))
```

**Por quê é necessário:** Demonstrar monitoramento dinâmico é o diferencial mais visual do projeto. Derrubar um container ao vivo e mostrar o status mudando de `UP` para `DOWN` na tela impressiona muito mais do que uma lista estática.

---

### 🟡 3.5 Buffer de Mensagens Muito Pequeno

**Situação atual:** A fila de mensagens recentes está limitada a **30 itens**:

```java
// AircraftTelemetryService.java linha 119
while (recentMessages.size() > 30) {
    recentMessages.removeFirst();
}
```

Com 7 módulos publicando a cada 1–3 segundos, 30 mensagens correspondem a apenas **4–6 segundos** de histórico. Praticamente inútil para visualização.

**O que mudar:**

```yaml
# No application.yml — adicionar:
app:
  telemetry:
    buffer-size: ${TELEMETRY_BUFFER_SIZE:300}
```

```text
// No AircraftTelemetryService.java — usar o valor configurável:
@Value("${app.telemetry.buffer-size:300}")
private int bufferSize;

// E na linha do limite:
while (recentMessages.size() > bufferSize) {
    recentMessages.removeFirst();
}
```

**Por quê é necessário:** 300 mensagens = aproximadamente 5 minutos de histórico em memória, suficiente para exibir um gráfico ou tabela de últimos eventos no frontend sem precisar de banco de dados.

---

### 🟡 3.6 Configuração Duplicada do Kafka no `application.yml`

**Situação atual:** O Kafka aparece **duas vezes** no `application.yml`:

```yaml
spring:
  kafka:
    bootstrap-servers: ${KAFKA_BOOTSTRAP_SERVERS:localhost:9092}   # config Spring oficial

app:
  kafka:
    bootstrap-servers: ${KAFKA_BOOTSTRAP_SERVERS:localhost:9092}   # config custom (só usada no HealthController)
```

**O que mudar:**

Se o Kafka for implementado com `@KafkaListener`, remover `app.kafka` e usar apenas `spring.kafka`.
Atualizar `HealthController` para ler de `spring.kafka.bootstrap-servers`:

```text
// Em HealthController.java — trocar:
public HealthController(@Value("${app.kafka.bootstrap-servers}") String kafkaBootstrapServers)

// Por:
public HealthController(@Value("${spring.kafka.bootstrap-servers}") String kafkaBootstrapServers)
```

**Por quê é necessário:** Evitar confusão sobre qual configuração é a "oficial". Com dois valores, uma mudança no `.env` precisa ser replicada em dois lugares, o que é propenso a erro.

---

### 🟡 3.7 Módulos Java Previstos no Plano que Não Existem

O plano original (`etc/plano-reestruturacao-sistema-distribuido.md`) prevê **8 serviços Java** além do backend-gateway. Nenhum foi implementado:

| Serviço Java Previsto | Package sugerido | Responsabilidade |
|---|---|---|
| Serviço de Rotas | `avionica.routes` | Gerenciar histórico de rotas no banco |
| Serviço de Telemetria | `avionica.telemetry` | Persistir e consultar dados de sensores |
| Serviço de Eventos | `avionica.events` | Registrar eventos técnicos |
| Serviço de Alertas | `avionica.alerts` | Gerar alertas a partir de limites ultrapassados |
| Serviço de Auditoria | `avionica.audit` | Registrar ações do usuário |
| Serviço de Relatórios | `avionica.reports` | Consultas e relatórios operacionais |
| Serviço de Status | `avionica.status` | Monitorar saúde dos módulos |
| Serviço de Notificações | `avionica.notifications` | Enviar notificações ao frontend |

> [!IMPORTANT]
> Para a avaliação da disciplina, o projeto precisa de **18+ módulos independentes** para uma equipe de 9 pessoas. Hoje existem apenas 12 containers (incluindo infraestrutura). Implementar esses serviços Java é essencial para atingir a contagem.

---

### 🟡 3.8 Módulos Python que Faltam (previstos no plano)

| Módulo Python Previsto | Arquivo | Status |
|---|---|---|
| Sensor de Altitude | `sensor_altitude.py` | ❌ Embutido no `sensores_voo.py` |
| Sensor de Atitude (pitch/roll/yaw) | `sensor_atitude.py` | ❌ Não existe |
| Sensor de Combustível | `sensor_combustivel.py` | ❌ Embutido no `sensores_voo.py` |
| Sensor de Velocidade | `sensor_velocidade.py` | ❌ Embutido no `sensores_voo.py` |
| Simulador de Piloto/CDU | `simulador_piloto_cdu.py` | ⚠️ Apenas `injetor_falhas.py` |
| Computador de Voo (containerizado) | `computador_voo.py` | ⚠️ Só roda como desktop (Tkinter) |
| Caixa Preta (FDR) | `caixa_preta.py` | ⚠️ Existe mas não está no docker-compose |

> [!NOTE]
> Separar `sensores_voo.py` em 4 módulos (velocidade, altitude, combustível, atitude) é a forma mais rápida de aumentar a contagem de módulos sem adicionar complexidade — cada sensor vira um container independente.

---

### 🟢 3.9 CORS restrito a localhost

**Situação atual:** O `CorsConfig.java` libera CORS apenas para `localhost:5173`:

```text
.allowedOrigins("http://localhost:5173", "http://127.0.0.1:5173")
```

**O que mudar:** Tornar as origens configuráveis por variável de ambiente para funcionar em ambiente de demonstração/apresentação:

```text
@Configuration
public class CorsConfig implements WebMvcConfigurer {

    @Value("${app.cors.allowed-origins:http://localhost:5173}")
    private String[] allowedOrigins;

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins(allowedOrigins)
            .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
            .allowedHeaders("*");
    }
}
```

```yaml
# application.yml
app:
  cors:
    allowed-origins: ${CORS_ALLOWED_ORIGINS:http://localhost:5173,http://127.0.0.1:5173}
```

**Por quê é necessário:** Na apresentação do projeto, o professor pode acessar pelo IP da máquina (ex: `http://192.168.x.x:5173`). O CORS vai bloquear todas as chamadas REST se a origem não estiver na lista.

---

### 🟢 3.10 Sem WebSocket ou SSE — Frontend faz polling

**Situação atual:** O frontend precisa chamar `GET /api/aircraft-data` repetidamente (polling) para atualizar os dados. Isso causa latência artificial e carga desnecessária.

**O que implementar:** Server-Sent Events (SSE) — mais simples que WebSocket, nativo do Spring MVC:

```text
// Criar: src/main/avionica/api/TelemetryStreamController.java
package avionica.api;

import avionica.telemetry.AircraftTelemetryService;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@RestController
public class TelemetryStreamController {

    private final AircraftTelemetryService telemetry;

    public TelemetryStreamController(AircraftTelemetryService telemetry) {
        this.telemetry = telemetry;
    }

    @GetMapping(value = "/api/telemetry/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter stream() {
        SseEmitter emitter = new SseEmitter(Long.MAX_VALUE);
        telemetry.registerEmitter(emitter);
        return emitter;
    }
}
```

**Por quê é necessário:** Com SSE, o browser recebe dados instantaneamente ao chegar do MQTT, sem polling. O dashboard fica verdadeiramente "ao vivo" — muito mais impactante para a apresentação.

---

## 4. Roadmap Priorizado — O que fazer e em que ordem

```
SEMANA ATUAL — Compilação e estrutura
  ✅ Source set Gradle corrigido
  ✅ Packages alinhados (avionica.*)
  ✅ Typos corrigidos
  ✅ Build SUCCESSFUL

PRÓXIMOS PASSOS — Por prioridade de impacto na nota

  🔴 ALTA PRIORIDADE
  ├── [ ] 3.1  Criar schema.sql + tabela telemetry_events
  ├── [ ] 3.1  Persistir mensagens MQTT no PostgreSQL (JdbcTemplate)
  ├── [ ] 3.1  Endpoint GET /api/telemetry/history
  ├── [ ] 3.3  Criar RouteController (POST /api/routes + GET /api/routes)
  └── [ ] 3.8  Separar sensores Python em módulos individuais (altitude, velocidade, combustível, atitude)

  🟡 MÉDIA PRIORIDADE
  ├── [ ] 3.4  Health check real — heartbeat nos módulos Python
  ├── [ ] 3.4  isAlive() no AircraftTelemetryService
  ├── [ ] 3.5  Aumentar buffer para 300 mensagens (configurável)
  ├── [ ] 3.6  Remover duplicação do Kafka no application.yml
  └── [ ] 3.7  Criar ao menos 2–3 serviços Java extras (eventos, alertas, status)

  🟢 BAIXA PRIORIDADE / DIFERENCIAL
  ├── [ ] 3.2  Implementar @KafkaListener e KafkaTemplate
  ├── [ ] 3.9  CORS configurável por variável de ambiente
  └── [ ] 3.10 SSE para telemetria em tempo real
```

---

## 5. Contagem de Módulos — Situação Atual vs. Meta

| # | Módulo | Tecnologia | Container | Conta? |
|---|---|---|---|---|
| 1 | Frontend Web | Vue.js | `avionica_frontend` | ✅ Sim |
| 2 | Backend Gateway | Spring Boot | `avionica_backend_gateway` | ✅ Sim |
| 3 | FMS API | Python | `avionica_fms_api` | ✅ Sim |
| 4 | Sensor de Voo (velocidade+altitude+combustível) | Python | `avionica_sensor_flight` | ⚠️ Conta como 1 |
| 5 | Sensor de Freio | Python | `avionica_sensor_brake` | ✅ Sim |
| 6 | Radar Externo | Python | `avionica_radar` | ✅ Sim |
| 7 | Computador de Navegação | Python | `avionica_navigation_computer` | ✅ Sim |
| 8 | Computador de Automação | Python | `avionica_automation_computer` | ✅ Sim |
| 9 | Líder WAIC | Python | `avionica_waic_leader` | ✅ Sim |
| — | PostgreSQL | Infraestrutura | `avionica_postgres` | ❌ Não conta |
| — | Kafka | Infraestrutura | `avionica_kafka` | ❌ Não conta |
| — | Mosquitto | Infraestrutura | `avionica_mqtt_broker` | ❌ Não conta |

**Total atual: 9 módulos de aplicação** (meta para 9 pessoas: **18 módulos**)

**Para atingir 18 módulos, é necessário adicionar:**

| Módulo a criar | Esforço | Como criar |
|---|---|---|
| Sensor de Velocidade | Baixo | Separar de `sensores_voo.py` |
| Sensor de Altitude | Baixo | Separar de `sensores_voo.py` |
| Sensor de Combustível | Baixo | Separar de `sensores_voo.py` |
| Sensor de Atitude (pitch/roll/yaw) | Baixo | Novo arquivo Python |
| Serviço de Rotas (Java) | Médio | `RouteController` + tabela `routes` |
| Serviço de Eventos (Java) | Médio | Controller + tabela `system_events` |
| Serviço de Alertas (Java) | Médio | Regras sobre telemetria (combustível < 20%, pressão < 50 psi) |
| Serviço de Status (Java) | Médio | Health check real com heartbeat |
| Simulador de Piloto/CDU | Baixo | Containerizar `injetor_falhas.py` |

**Com esses 9 adicionais: total = 18 módulos ✅**

---

## 6. Estrutura de Arquivos — Estado Completo

### 6.1 Arquivos existentes hoje

```
backend/src/main/
├── avionica/
│   ├── AvionicaBackendApplication.java   ✅ package avionica
│   ├── api/
│   │   ├── AircraftDataController.java   ✅ GET /api/aircraft-data
│   │   └── HealthController.java         ⚠️ status hardcoded
│   ├── config/
│   │   ├── CorsConfig.java               ⚠️ origem fixa (localhost:5173)
│   │   └── StartupLogger.java            ✅ ok
│   └── telemetry/
│       ├── AircraftDataSnapshot.java     ✅ record imutável
│       ├── AircraftMessage.java          ✅ record imutável
│       └── AircraftTelemetryService.java ✅ MQTT + snapshot em memória
└── resources/
    └── application.yml                   ✅ configurações por variável de ambiente
```

### 6.2 Arquivos que precisam ser criados

```
backend/src/main/
├── avionica/
│   ├── api/
│   │   ├── RouteController.java          ❌ POST/GET /api/routes
│   │   ├── TelemetryHistoryController.java ❌ GET /api/telemetry/history
│   │   └── TelemetryStreamController.java  ❌ GET /api/telemetry/stream (SSE)
│   ├── kafka/
│   │   ├── TelemetryKafkaConsumer.java   ❌ @KafkaListener
│   │   └── RouteEventProducer.java       ❌ KafkaTemplate
│   └── service/
│       ├── RouteService.java             ❌ lógica de negócio das rotas
│       ├── AlertService.java             ❌ regras de alerta
│       └── ModuleStatusService.java      ❌ health check real
└── resources/
    └── schema.sql                        ❌ DDL das tabelas
```

---

## 7. Referências

- [Spring JDBC — JdbcTemplate](https://docs.spring.io/spring-framework/reference/data-access/jdbc/core.html)
- [Spring Kafka — @KafkaListener](https://docs.spring.io/spring-kafka/reference/)
- [Spring MVC — Server-Sent Events](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-async.html#mvc-ann-async-sse)
- [Spring Boot — schema.sql automático](https://docs.spring.io/spring-boot/reference/data/sql.html#data.sql.datasource.initialization)
- [Paho MQTT — MqttCallbackExtended](https://www.eclipse.org/paho/index.php?page=clients/java/index.php)
