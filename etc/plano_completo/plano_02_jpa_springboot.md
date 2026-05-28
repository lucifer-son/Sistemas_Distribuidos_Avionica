# 🗄️ Plano 02 — JPA com Spring Boot: Camada de Persistência

> **Sistema:** Gateway Tolerante a Falhas para Redes Aviônicas Híbridas (AFDX/WAIC)  
> **Framework:** Spring Boot 4.x + Spring Data JPA + Hibernate  
> **Banco:** PostgreSQL 17  
> **Linguagem:** Java 25

---

## 🧠 Visão Geral

Atualmente o backend usa **`spring-boot-starter-jdbc`** (JDBC puro). A migração para **Spring Data JPA** vai trazer:

- Entities mapeadas diretamente para as tabelas do banco
- Repositories com CRUD automático (sem SQL manual)
- Queries derivadas por nome de método (`findByRecebidoEmAfter`, `findBySeveridade`, etc.)
- Integração com o Spring para injeção de dependência sem boilerplate

---

## 📦 Passo 1 — Atualizar Dependências no `build.gradle`

Substitua `spring-boot-starter-jdbc` por `spring-boot-starter-data-jpa`:

```groovy
// build.gradle
dependencies {
    // REMOVER esta linha:
    // implementation 'org.springframework.boot:spring-boot-starter-jdbc'

    // ADICIONAR estas linhas:
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    implementation 'org.springframework.boot:spring-boot-starter-validation' // Para @NotNull, @Size, etc.

    // Manter estas:
    implementation 'org.springframework.boot:spring-boot-starter-actuator'
    implementation 'org.springframework.boot:spring-boot-starter-webmvc'
    implementation 'org.springframework.kafka:spring-kafka'
    implementation 'org.eclipse.paho:org.eclipse.paho.client.mqttv3:1.2.5'
    implementation 'org.json:json:20240303'
    runtimeOnly    'org.postgresql:postgresql'
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
}
```

---

## ⚙️ Passo 2 — Configurar `application.yml`

Adicione as configurações JPA na seção `spring`:

```yaml
# application.yml
server:
  port: ${SERVER_PORT:8080}

spring:
  application:
    name: backend-gateway
  main:
    banner-mode: "off"

  datasource:
    url: ${SPRING_DATASOURCE_URL:jdbc:postgresql://localhost:5432/avionica}
    username: ${SPRING_DATASOURCE_USERNAME:avionica}
    password: ${SPRING_DATASOURCE_PASSWORD:avionica_dev}
    driver-class-name: org.postgresql.Driver

  jpa:
    hibernate:
      ddl-auto: validate         # validate: só valida, não cria/altera tabelas (DDL manual via schema.sql)
    show-sql: false              # true apenas em dev para depurar queries SQL
    open-in-view: false          # Boa prática: desabilitar Open Session in View
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        format_sql: true
        jdbc:
          time_zone: UTC         # Garante consistência de timezone com TIMESTAMPTZ

  kafka:
    bootstrap-servers: ${KAFKA_BOOTSTRAP_SERVERS:localhost:9092}

app:
  kafka:
    bootstrap-servers: ${KAFKA_BOOTSTRAP_SERVERS:localhost:9092}
  mqtt:
    broker-url: ${MQTT_BROKER_URL:tcp://localhost:1883}
    topic-filter: ${MQTT_TOPIC_FILTER:avionica/#}

management:
  endpoints:
    web:
      exposure:
        include: health,info

logging:
  level:
    root: WARN
    avionica: INFO
    org.hibernate.SQL: WARN       # Mude para DEBUG temporariamente para ver queries
```

> **Nota sobre `ddl-auto: validate`:** Como usamos o `schema.sql` manual (Plano 01), configuramos o Hibernate apenas para **validar** se as entidades batem com o banco — ele nunca criará nem modificará tabelas.

---

## 🏗️ Passo 3 — Estrutura de Pacotes Proposta

```
src/main/
├── avionica/
│   ├── AvionicaBackendApplication.java  ← já existe
│   ├── api/
│   │   ├── AircraftDataController.java  ← já existe
│   │   ├── HealthController.java        ← já existe
│   │   ├── AlertaController.java        ← NOVO
│   │   └── RotaFmsController.java       ← NOVO
│   ├── config/
│   │   ├── CorsConfig.java              ← já existe
│   │   └── StartupLogger.java           ← já existe
│   ├── telemetry/
│   │   ├── AircraftMessage.java         ← já existe
│   │   ├── AircraftDataSnapshot.java    ← já existe
│   │   └── AircraftTelemetryService.java ← já existe (integração c/ JPA)
│   └── persistence/                     ← PACOTE NOVO (JPA)
│       ├── entity/
│       │   ├── TelemetriaVoo.java
│       │   ├── TelemetriaFreios.java
│       │   ├── TelemetriaRadar.java
│       │   ├── TelemetriaWaic.java
│       │   ├── TelemetriaNavegacao.java
│       │   ├── RotaFms.java
│       │   ├── Alerta.java
│       │   ├── EventoAntiIce.java
│       │   └── MensagemBarramento.java
│       ├── repository/
│       │   ├── TelemetriaVooRepository.java
│       │   ├── TelemetriaFreiosRepository.java
│       │   ├── TelemetriaRadarRepository.java
│       │   ├── TelemetriaWaicRepository.java
│       │   ├── TelemetriaNavegacaoRepository.java
│       │   ├── RotaFmsRepository.java
│       │   ├── AlertaRepository.java
│       │   ├── EventoAntiIceRepository.java
│       │   └── MensagemBarramentoRepository.java
│       └── service/
│           ├── TelemetriaPersistenceService.java
│           ├── AlertaService.java
│           └── RotaFmsService.java
```

---

## 📄 Passo 4 — Criar as Entidades JPA

### 4.1 — `TelemetriaVoo.java`

```java
package avionica.persistence.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "telemetria_voo")
public class TelemetriaVoo {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "recebido_em", nullable = false, updatable = false)
    private Instant recebidoEm = Instant.now();

    @Column(name = "combustivel_pct", precision = 5, scale = 2)
    private BigDecimal combustivelPct;

    @Column(name = "altitude_ft")
    private Integer altitudeFt;

    @Column(name = "estabilizador_graus", precision = 4, scale = 1)
    private BigDecimal estabilizadorGraus;

    @Column(name = "pressao_cabine_psi", precision = 5, scale = 2)
    private BigDecimal pressaoCabinePsi;

    @Column(name = "velocidade_mach", precision = 5, scale = 3)
    private BigDecimal velocidadeMach;

    @Column(name = "origem", length = 100)
    private String origem;

    // Construtor padrão obrigatório para o JPA
    public TelemetriaVoo() {}

    // Getters e Setters
    public UUID getId() { return id; }
    public Instant getRecebidoEm() { return recebidoEm; }
    public BigDecimal getCombustivelPct() { return combustivelPct; }
    public void setCombustivelPct(BigDecimal v) { this.combustivelPct = v; }
    public Integer getAltitudeFt() { return altitudeFt; }
    public void setAltitudeFt(Integer v) { this.altitudeFt = v; }
    public BigDecimal getEstabilizadorGraus() { return estabilizadorGraus; }
    public void setEstabilizadorGraus(BigDecimal v) { this.estabilizadorGraus = v; }
    public BigDecimal getPressaoCabinePsi() { return pressaoCabinePsi; }
    public void setPressaoCabinePsi(BigDecimal v) { this.pressaoCabinePsi = v; }
    public BigDecimal getVelocidadeMach() { return velocidadeMach; }
    public void setVelocidadeMach(BigDecimal v) { this.velocidadeMach = v; }
    public String getOrigem() { return origem; }
    public void setOrigem(String v) { this.origem = v; }
}
```

### 4.2 — `Alerta.java` (com Enum de severidade)

```java
package avionica.persistence.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "alertas")
public class Alerta {

    public enum Severidade { INFO, WARNING, CRITICAL }

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "registrado_em", nullable = false, updatable = false)
    private Instant registradoEm = Instant.now();

    @NotNull
    @Column(name = "tipo", nullable = false, length = 100)
    private String tipo;

    @Column(name = "descricao", columnDefinition = "TEXT")
    private String descricao;

    @Enumerated(EnumType.STRING)
    @Column(name = "severidade", nullable = false, length = 20)
    private Severidade severidade = Severidade.INFO;

    @Column(name = "origem", length = 100)
    private String origem;

    @Column(name = "resolvido", nullable = false)
    private boolean resolvido = false;

    @Column(name = "resolvido_em")
    private Instant resolvidoEm;

    public Alerta() {}

    // Getters e Setters
    public UUID getId() { return id; }
    public Instant getRegistradoEm() { return registradoEm; }
    public String getTipo() { return tipo; }
    public void setTipo(String tipo) { this.tipo = tipo; }
    public String getDescricao() { return descricao; }
    public void setDescricao(String descricao) { this.descricao = descricao; }
    public Severidade getSeveridade() { return severidade; }
    public void setSeveridade(Severidade severidade) { this.severidade = severidade; }
    public String getOrigem() { return origem; }
    public void setOrigem(String origem) { this.origem = origem; }
    public boolean isResolvido() { return resolvido; }
    public void setResolvido(boolean resolvido) { this.resolvido = resolvido; }
    public Instant getResolvidoEm() { return resolvidoEm; }
    public void setResolvidoEm(Instant resolvidoEm) { this.resolvidoEm = resolvidoEm; }
}
```

### 4.3 — `RotaFms.java`

```java
package avionica.persistence.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "rotas_fms")
public class RotaFms {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "registrado_em", nullable = false, updatable = false)
    private Instant registradoEm = Instant.now();

    @Column(name = "icao_origem", length = 4, columnDefinition = "CHAR(4)")
    private String icaoOrigem;

    @Column(name = "icao_destino", length = 4, columnDefinition = "CHAR(4)")
    private String icaoDestino;

    @Column(name = "rota_texto", length = 200)
    private String rotaTexto;

    @Column(name = "distancia_nm", precision = 8, scale = 1)
    private BigDecimal distanciaNm;

    @Column(name = "eta_minutos")
    private Integer etaMinutos;

    @Column(name = "ativa", nullable = false)
    private boolean ativa = true;

    public RotaFms() {}

    // Getters e Setters
    public UUID getId() { return id; }
    public Instant getRegistradoEm() { return registradoEm; }
    public String getIcaoOrigem() { return icaoOrigem; }
    public void setIcaoOrigem(String v) { this.icaoOrigem = v; }
    public String getIcaoDestino() { return icaoDestino; }
    public void setIcaoDestino(String v) { this.icaoDestino = v; }
    public String getRotaTexto() { return rotaTexto; }
    public void setRotaTexto(String v) { this.rotaTexto = v; }
    public BigDecimal getDistanciaNm() { return distanciaNm; }
    public void setDistanciaNm(BigDecimal v) { this.distanciaNm = v; }
    public Integer getEtaMinutos() { return etaMinutos; }
    public void setEtaMinutos(Integer v) { this.etaMinutos = v; }
    public boolean isAtiva() { return ativa; }
    public void setAtiva(boolean v) { this.ativa = v; }
}
```

### 4.4 — `MensagemBarramento.java` (com JSONB)

```java
package avionica.persistence.entity;

import jakarta.persistence.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import java.time.Instant;
import java.util.Map;

@Entity
@Table(name = "mensagens_barramento")
public class MensagemBarramento {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "recebido_em", nullable = false, updatable = false)
    private Instant recebidoEm = Instant.now();

    @Column(name = "topico", nullable = false, length = 200)
    private String topico;

    // Mapeia a coluna JSONB do PostgreSQL para um Map Java
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "payload_json", columnDefinition = "jsonb")
    private Map<String, Object> payloadJson;

    @Column(name = "tamanho_bytes")
    private Integer tamanhoBytes;

    public MensagemBarramento() {}

    // Getters e Setters
    public Long getId() { return id; }
    public Instant getRecebidoEm() { return recebidoEm; }
    public String getTopico() { return topico; }
    public void setTopico(String topico) { this.topico = topico; }
    public Map<String, Object> getPayloadJson() { return payloadJson; }
    public void setPayloadJson(Map<String, Object> payloadJson) { this.payloadJson = payloadJson; }
    public Integer getTamanhoBytes() { return tamanhoBytes; }
    public void setTamanhoBytes(Integer tamanhoBytes) { this.tamanhoBytes = tamanhoBytes; }
}
```

---

## 📚 Passo 5 — Criar os Repositories

### `AlertaRepository.java`

```java
package avionica.persistence.repository;

import avionica.persistence.entity.Alerta;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.UUID;

@Repository
public interface AlertaRepository extends JpaRepository<Alerta, UUID> {

    // Busca todos os alertas não resolvidos, ordenados do mais recente
    List<Alerta> findByResolvidoFalseOrderByRegistradoEmDesc();

    // Busca por severidade
    List<Alerta> findBySeveridadeOrderByRegistradoEmDesc(Alerta.Severidade severidade);

    // Busca alertas críticos não resolvidos
    List<Alerta> findBySeveridadeAndResolvidoFalseOrderByRegistradoEmDesc(Alerta.Severidade severidade);
}
```

### `RotaFmsRepository.java`

```java
package avionica.persistence.repository;

import avionica.persistence.entity.RotaFms;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface RotaFmsRepository extends JpaRepository<RotaFms, UUID> {

    // Retorna a rota atualmente ativa
    Optional<RotaFms> findFirstByAtivaTrue();

    // Todas as rotas ordenadas por data (histórico)
    java.util.List<RotaFms> findAllByOrderByRegistradoEmDesc();
}
```

### `TelemetriaVooRepository.java`

```java
package avionica.persistence.repository;

import avionica.persistence.entity.TelemetriaVoo;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.UUID;

@Repository
public interface TelemetriaVooRepository extends JpaRepository<TelemetriaVoo, UUID> {

    // Busca os N registros mais recentes (usar com Pageable.ofSize(1))
    List<TelemetriaVoo> findAllByOrderByRecebidoEmDesc(Pageable pageable);
}
```

### `MensagemBarramentoRepository.java`

```java
package avionica.persistence.repository;

import avionica.persistence.entity.MensagemBarramento;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface MensagemBarramentoRepository extends JpaRepository<MensagemBarramento, Long> {

    // Busca as últimas mensagens de um tópico específico
    List<MensagemBarramento> findByTopicoOrderByRecebidoEmDesc(String topico, Pageable pageable);

    // Busca as últimas N mensagens de todos os tópicos
    List<MensagemBarramento> findAllByOrderByRecebidoEmDesc(Pageable pageable);
}
```

---

## ⚙️ Passo 6 — Criar o `TelemetriaPersistenceService.java`

Este service recebe as mensagens MQTT processadas e persiste no banco:

```java
package avionica.persistence.service;

import avionica.persistence.entity.MensagemBarramento;
import avionica.persistence.entity.TelemetriaVoo;
import avionica.persistence.repository.MensagemBarramentoRepository;
import avionica.persistence.repository.TelemetriaVooRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.math.BigDecimal;
import java.util.Map;

@Service
public class TelemetriaPersistenceService {

    private static final Logger logger = LoggerFactory.getLogger(TelemetriaPersistenceService.class);

    private final TelemetriaVooRepository vooRepository;
    private final MensagemBarramentoRepository barramentoRepository;

    public TelemetriaPersistenceService(
        TelemetriaVooRepository vooRepository,
        MensagemBarramentoRepository barramentoRepository
    ) {
        this.vooRepository = vooRepository;
        this.barramentoRepository = barramentoRepository;
    }

    // @Async garante que a persistência não bloqueie o callback MQTT
    @Async
    @Transactional
    public void persistirMensagem(String topico, Map<String, Object> payload, int tamanhoBytes) {
        try {
            // 1. Persiste TODAS as mensagens no log do barramento
            MensagemBarramento msg = new MensagemBarramento();
            msg.setTopico(topico);
            msg.setPayloadJson(payload);
            msg.setTamanhoBytes(tamanhoBytes);
            barramentoRepository.save(msg);

            // 2. Persiste na tabela específica conforme o tópico
            switch (topico) {
                case "avionica/sensores/voo" -> persistirTelemetriaVoo(payload);
                // Adicionar outros tópicos aqui (freios, radar, waic, etc.)
                default -> logger.debug("Tópico não mapeado para persistência específica: {}", topico);
            }
        } catch (Exception e) {
            logger.error("Erro ao persistir mensagem do tópico {}: {}", topico, e.getMessage());
        }
    }

    private void persistirTelemetriaVoo(Map<String, Object> payload) {
        Object dadosRaw = payload.get("dados");
        if (!(dadosRaw instanceof Map<?, ?> dados)) return;

        TelemetriaVoo entidade = new TelemetriaVoo();
        entidade.setCombustivelPct(toBigDecimal(dados.get("combustivel_pct")));
        entidade.setAltitudeFt(toInteger(dados.get("altitude_ft")));
        entidade.setEstabilizadorGraus(toBigDecimal(dados.get("estabilizador_graus")));
        entidade.setPressaoCabinePsi(toBigDecimal(dados.get("pressao_cabine_psi")));
        entidade.setVelocidadeMach(toBigDecimal(dados.get("velocidade_mach")));
        entidade.setOrigem(String.valueOf(payload.getOrDefault("origem", "desconhecido")));

        vooRepository.save(entidade);
        logger.debug("Telemetria de voo persistida com sucesso.");
    }

    // Helpers de conversão segura
    private BigDecimal toBigDecimal(Object value) {
        if (value == null) return null;
        try { return new BigDecimal(value.toString()); }
        catch (Exception e) { return null; }
    }

    private Integer toInteger(Object value) {
        if (value == null) return null;
        try { return ((Number) value).intValue(); }
        catch (Exception e) { return null; }
    }
}
```

---

## 🔌 Passo 7 — Integrar com `AircraftTelemetryService.java`

Injete o `TelemetriaPersistenceService` no service MQTT existente e chame `persistirMensagem` no callback:

```java
// Em AircraftTelemetryService.java — adicione o campo e chame no messageArrived()

// Campo a adicionar:
private final TelemetriaPersistenceService persistenceService;

// Construtor atualizado:
public AircraftTelemetryService(
    @Value("${app.mqtt.broker-url}") String brokerUrl,
    @Value("${app.mqtt.topic-filter}") String topicFilter,
    TelemetriaPersistenceService persistenceService   // ← NOVO
) {
    this.brokerUrl = brokerUrl;
    this.topicFilter = topicFilter;
    this.persistenceService = persistenceService;     // ← NOVO
}

// No método messageArrived(), após atualizar o mapa em memória, adicione:
@Override
public void messageArrived(String topic, MqttMessage mqttMessage) {
    Map<String, Object> payload = parsePayload(mqttMessage);
    AircraftMessage message = new AircraftMessage(topic, Instant.now(), payload);

    latestByTopic.put(topic, message);

    synchronized (recentMessages) {
        recentMessages.addLast(message);
        while (recentMessages.size() > 30) {
            recentMessages.removeFirst();
        }
    }

    // ← NOVA LINHA: Persiste no banco de forma assíncrona
    persistenceService.persistirMensagem(topic, payload, mqttMessage.getPayload().length);
}
```

---

## 🌐 Passo 8 — Criar os Controllers REST de Alertas e Rotas

### `AlertaController.java`

```java
package avionica.api;

import avionica.persistence.entity.Alerta;
import avionica.persistence.repository.AlertaRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/alertas")
public class AlertaController {

    private final AlertaRepository alertaRepository;

    public AlertaController(AlertaRepository alertaRepository) {
        this.alertaRepository = alertaRepository;
    }

    // GET /api/alertas — Todos os alertas não resolvidos
    @GetMapping
    public List<Alerta> listarAtivos() {
        return alertaRepository.findByResolvidoFalseOrderByRegistradoEmDesc();
    }

    // GET /api/alertas/criticos — Alertas críticos não resolvidos
    @GetMapping("/criticos")
    public List<Alerta> listarCriticos() {
        return alertaRepository.findBySeveridadeAndResolvidoFalseOrderByRegistradoEmDesc(Alerta.Severidade.CRITICAL);
    }

    // PATCH /api/alertas/{id}/resolver — Resolve um alerta
    @PatchMapping("/{id}/resolver")
    public ResponseEntity<Alerta> resolver(@PathVariable UUID id) {
        return alertaRepository.findById(id)
            .map(alerta -> {
                alerta.setResolvido(true);
                alerta.setResolvidoEm(Instant.now());
                return ResponseEntity.ok(alertaRepository.save(alerta));
            })
            .orElse(ResponseEntity.notFound().build());
    }
}
```

---

## ✅ Passo 9 — Habilitar Async no Application

Adicione `@EnableAsync` na classe principal para que o `@Async` do `TelemetriaPersistenceService` funcione:

```java
package avionica;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync  // ← NOVO: habilita execução assíncrona dos métodos @Async
public class AvionicaBackendApplication {
    public static void main(String[] args) {
        SpringApplication.run(AvionicaBackendApplication.class, args);
    }
}
```

---

## 🧪 Passo 10 — Verificação e Testes

### Verificar via `psql` após subir o sistema:

```sql
-- As mensagens MQTT devem aparecer aqui em segundos
SELECT topico, recebido_em FROM mensagens_barramento ORDER BY recebido_em DESC LIMIT 10;

-- Telemetria de voo sendo persistida
SELECT combustivel_pct, altitude_ft, velocidade_mach FROM telemetria_voo ORDER BY recebido_em DESC LIMIT 5;
```

### Verificar via cURL os novos endpoints:

```powershell
# Listar alertas ativos
curl http://localhost:8080/api/alertas

# Listar alertas críticos
curl http://localhost:8080/api/alertas/criticos

# Resolver um alerta (substitua o UUID)
curl -X PATCH http://localhost:8080/api/alertas/550e8400-e29b-41d4-a716-446655440000/resolver
```

---

## ⚠️ Pontos de Atenção

| Item | Detalhe |
|---|---|
| **`ddl-auto: validate`** | O Hibernate NÃO cria tabelas. O schema DEVE existir (via Plano 01) antes de subir o app |
| **`@Async` e transações** | O `@Async` faz a persistência em thread separada, não bloqueando o callback MQTT |
| **JSONB e Hibernate 6** | Use `@JdbcTypeCode(SqlTypes.JSON)` para mapear colunas `jsonb` — funciona com Hibernate 6+ |
| **UUID no PostgreSQL** | Use `@GeneratedValue(strategy = GenerationType.UUID)` — suportado nativo no Spring Boot 3+ |
| **Timezone** | Configure `spring.jpa.properties.hibernate.jdbc.time_zone: UTC` para evitar problemas com `TIMESTAMPTZ` |
