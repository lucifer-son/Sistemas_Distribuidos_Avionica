# 🔧 Plano 07 — Backend Completo: Implementação passo a passo

> **Base:** Plano 02 (JPA/Spring Boot) expandido com todos os detalhes de execução  
> **Sistema:** Gateway Tolerante a Falhas — Redes Aviônicas Híbridas (AFDX/WAIC)  
> **Stack:** Spring Boot 4.x · Java 25 · Spring Data JPA · Hibernate 6 · PostgreSQL 17  
> **Estado atual:** `spring-boot-starter-jdbc` · 2 controllers · sem persistência · sem testes

---

## 📌 Dependências entre os passos

```
Passo 1 → Passo 2 → Passo 3 ─┬─► Passo 4 (Entities)
                               ├─► Passo 5 (Repositories)
                               └─► Passo 6 (Services)
                                        │
                               Passo 7 ─┘ (Integração MQTT)
                               Passo 8    (Controllers REST)
                               Passo 9    (Comandos)
                               Passo 10   (Tratamento de Erros)
                               Passo 11   (Testes)
```

> ⚠️ **Pré-requisito obrigatório:** O schema DDL do **Plano 01** (`infra/db/schema.sql`) deve estar aplicado no PostgreSQL antes de subir o backend. O Hibernate usará `ddl-auto: validate` e vai rejeitar a inicialização se as tabelas não existirem.

---

## 📦 Passo 1 — Atualizar `build.gradle`

**Arquivo:** [`build.gradle`](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/build.gradle)

Remover o JDBC puro e adicionar JPA, Validation e Spring Security (para auth futura):

```groovy
plugins {
    id 'java'
    id 'org.springframework.boot' version '4.0.6'
    id 'io.spring.dependency-management' version '1.1.7'
}

group = 'br.edu.avionica'
version = '0.1.0'

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(25)
    }
}

sourceSets {
    main {
        java {
            srcDirs = ['src/main']
        }
        resources {
            srcDirs = ['src/main/resources']
        }
    }
}

dependencies {
    // ─── WEB ───────────────────────────────────────────────────
    implementation 'org.springframework.boot:spring-boot-starter-webmvc'
    implementation 'org.springframework.boot:spring-boot-starter-actuator'

    // ─── PERSISTÊNCIA (substitui spring-boot-starter-jdbc) ─────
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    implementation 'org.springframework.boot:spring-boot-starter-validation'
    runtimeOnly    'org.postgresql:postgresql'

    // ─── MENSAGERIA ─────────────────────────────────────────────
    implementation 'org.springframework.kafka:spring-kafka'
    implementation 'org.eclipse.paho:org.eclipse.paho.client.mqttv3:1.2.5'

    // ─── UTILITÁRIOS ────────────────────────────────────────────
    implementation 'org.json:json:20240303'

    // ─── TESTES ─────────────────────────────────────────────────
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.kafka:spring-kafka-test'
}

tasks.named('test') {
    useJUnitPlatform()
}
```

---

## ⚙️ Passo 2 — Reescrever `application.yml`

**Arquivo:** [`application.yml`](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/src/main/resources/application.yml)

```yaml
server:
  port: ${SERVER_PORT:8080}

spring:
  application:
    name: backend-gateway
  main:
    banner-mode: "off"

  # ─── BANCO DE DADOS ──────────────────────────────────────────
  datasource:
    url: ${SPRING_DATASOURCE_URL:jdbc:postgresql://localhost:5432/avionica}
    username: ${SPRING_DATASOURCE_USERNAME:avionica}
    password: ${SPRING_DATASOURCE_PASSWORD:avionica_dev}
    driver-class-name: org.postgresql.Driver
    hikari:
      maximum-pool-size: 10        # máximo de conexões simultâneas
      minimum-idle: 2              # mínimo de conexões mantidas abertas
      connection-timeout: 20000    # 20s para obter conexão antes de erro

  # ─── JPA / HIBERNATE ─────────────────────────────────────────
  jpa:
    hibernate:
      # validate: verifica se as entidades batem com o banco
      # NUNCA use create/create-drop em produção
      ddl-auto: validate
    show-sql: false
    open-in-view: false            # desabilitar OSIV é boa prática
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        format_sql: true
        jdbc:
          time_zone: UTC           # consistência com TIMESTAMPTZ do PostgreSQL

  # ─── KAFKA ───────────────────────────────────────────────────
  kafka:
    bootstrap-servers: ${KAFKA_BOOTSTRAP_SERVERS:localhost:9092}

# ─── CONFIGURAÇÕES CUSTOMIZADAS ──────────────────────────────
app:
  kafka:
    bootstrap-servers: ${KAFKA_BOOTSTRAP_SERVERS:localhost:9092}
    topics:
      telemetria-voo:    avionica.telemetria.voo
      telemetria-freios: avionica.telemetria.freios
      telemetria-radar:  avionica.telemetria.radar
      telemetria-waic:   avionica.telemetria.waic
      alertas:           avionica.alertas
      comandos:          avionica.comandos
  mqtt:
    broker-url:    ${MQTT_BROKER_URL:tcp://localhost:1883}
    topic-filter:  ${MQTT_TOPIC_FILTER:avionica/#}
  telemetria:
    historico-max-registros: 500   # limite por consulta de histórico

# ─── ACTUATOR ────────────────────────────────────────────────
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics

# ─── LOGGING ─────────────────────────────────────────────────
logging:
  level:
    root: WARN
    avionica: INFO
    org.hibernate.SQL: WARN        # mude para DEBUG para ver queries
```

---

## 🏗️ Passo 3 — Estrutura de Pacotes Final

```
src/main/
└── avionica/
    ├── AvionicaBackendApplication.java    ← modificar (adicionar @EnableAsync)
    │
    ├── api/                               ← Controllers REST
    │   ├── AircraftDataController.java    ← já existe (manter)
    │   ├── HealthController.java          ← já existe (manter)
    │   ├── AlertaController.java          ← CRIAR
    │   ├── TelemetriaController.java      ← CRIAR (histórico paginado)
    │   ├── RotaFmsController.java         ← CRIAR
    │   └── ComandoController.java         ← CRIAR (velocidade, proa, falhas)
    │
    ├── config/                            ← Configurações Spring
    │   ├── CorsConfig.java                ← já existe (manter/ajustar)
    │   ├── StartupLogger.java             ← já existe (manter)
    │   ├── AsyncConfig.java               ← CRIAR (thread pool para @Async)
    │   └── GlobalExceptionHandler.java    ← CRIAR (@ControllerAdvice)
    │
    ├── telemetry/                         ← Lógica MQTT em memória (já existe)
    │   ├── AircraftMessage.java           ← manter
    │   ├── AircraftDataSnapshot.java      ← manter
    │   └── AircraftTelemetryService.java  ← modificar (injetar KafkaProducer)
    │
    └── persistence/                       ← CRIAR — tudo novo
        ├── entity/
        │   ├── TelemetriaVoo.java
        │   ├── TelemetriaFreios.java
        │   ├── TelemetriaRadar.java
        │   ├── TelemetriaWaic.java
        │   ├── TelemetriaNavegacao.java
        │   ├── RotaFms.java
        │   ├── Alerta.java
        │   ├── EventoAntiIce.java
        │   └── MensagemBarramento.java
        ├── repository/
        │   ├── TelemetriaVooRepository.java
        │   ├── TelemetriaFreiosRepository.java
        │   ├── TelemetriaRadarRepository.java
        │   ├── TelemetriaWaicRepository.java
        │   ├── TelemetriaNavegacaoRepository.java
        │   ├── RotaFmsRepository.java
        │   ├── AlertaRepository.java
        │   ├── EventoAntiIceRepository.java
        │   └── MensagemBarramentoRepository.java
        └── service/
            ├── TelemetriaPersistenceService.java
            ├── AlertaService.java
            └── RotaFmsService.java
```

---

## 📄 Passo 4 — Entidades JPA

> As entidades completas estão no **Plano 02**. Este passo lista as que faltam ser criadas além das do Plano 02.

### 4.1 — Entidades já detalhadas no Plano 02

- `TelemetriaVoo.java` — campos: combustivel_pct, altitude_ft, estabilizador_graus, pressao_cabine_psi, velocidade_mach
- `Alerta.java` — enum Severidade (INFO/WARNING/CRITICAL), campos: tipo, descricao, resolvido, resolvido_em
- `RotaFms.java` — campos: icao_origem, icao_destino, rota_texto, distancia_nm, eta_minutos, ativa
- `MensagemBarramento.java` — coluna JSONB com `@JdbcTypeCode(SqlTypes.JSON)`

### 4.2 — `TelemetriaFreios.java` ← faltou no Plano 02

```java
package avionica.persistence.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "telemetria_freios")
public class TelemetriaFreios {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "recebido_em", nullable = false, updatable = false)
    private Instant recebidoEm = Instant.now();

    @Column(name = "pressao_psi", precision = 7, scale = 2)
    private BigDecimal pressaoPsi;

    @Column(name = "origem", length = 100)
    private String origem;

    public TelemetriaFreios() {}

    public UUID getId() { return id; }
    public Instant getRecebidoEm() { return recebidoEm; }
    public BigDecimal getPressaoPsi() { return pressaoPsi; }
    public void setPressaoPsi(BigDecimal v) { this.pressaoPsi = v; }
    public String getOrigem() { return origem; }
    public void setOrigem(String v) { this.origem = v; }
}
```

### 4.3 — `TelemetriaRadar.java`

```java
package avionica.persistence.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "telemetria_radar")
public class TelemetriaRadar {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "recebido_em", nullable = false, updatable = false)
    private Instant recebidoEm = Instant.now();

    @Column(name = "vento_knots", precision = 6, scale = 1)
    private BigDecimal ventoKnots;

    @Column(name = "turbulencia", length = 50)
    private String turbulencia;

    @Column(name = "radar_clima", length = 100)
    private String radarClima;

    @Column(name = "temp_externa_c", precision = 5, scale = 1)
    private BigDecimal tempExternaC;

    @Column(name = "qnh_hpa", precision = 6, scale = 1)
    private BigDecimal qnhHpa;

    @Column(name = "atc_msg", columnDefinition = "TEXT")
    private String atcMsg;

    @Column(name = "origem", length = 100)
    private String origem;

    public TelemetriaRadar() {}

    public UUID getId() { return id; }
    public Instant getRecebidoEm() { return recebidoEm; }
    public BigDecimal getVentoKnots() { return ventoKnots; }
    public void setVentoKnots(BigDecimal v) { this.ventoKnots = v; }
    public String getTurbulencia() { return turbulencia; }
    public void setTurbulencia(String v) { this.turbulencia = v; }
    public String getRadarClima() { return radarClima; }
    public void setRadarClima(String v) { this.radarClima = v; }
    public BigDecimal getTempExternaC() { return tempExternaC; }
    public void setTempExternaC(BigDecimal v) { this.tempExternaC = v; }
    public BigDecimal getQnhHpa() { return qnhHpa; }
    public void setQnhHpa(BigDecimal v) { this.qnhHpa = v; }
    public String getAtcMsg() { return atcMsg; }
    public void setAtcMsg(String v) { this.atcMsg = v; }
    public String getOrigem() { return origem; }
    public void setOrigem(String v) { this.origem = v; }
}
```

### 4.4 — `TelemetriaWaic.java`

```java
package avionica.persistence.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "telemetria_waic")
public class TelemetriaWaic {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "recebido_em", nullable = false, updatable = false)
    private Instant recebidoEm = Instant.now();

    @Column(name = "pressao_motor", precision = 7, scale = 2)
    private BigDecimal pressaoMotor;

    @Column(name = "temperatura_c", precision = 6, scale = 1)
    private BigDecimal temperaturaC;

    @Column(name = "origem", length = 100)
    private String origem;

    public TelemetriaWaic() {}

    public UUID getId() { return id; }
    public Instant getRecebidoEm() { return recebidoEm; }
    public BigDecimal getPressaoMotor() { return pressaoMotor; }
    public void setPressaoMotor(BigDecimal v) { this.pressaoMotor = v; }
    public BigDecimal getTemperaturaC() { return temperaturaC; }
    public void setTemperaturaC(BigDecimal v) { this.temperaturaC = v; }
    public String getOrigem() { return origem; }
    public void setOrigem(String v) { this.origem = v; }
}
```

### 4.5 — `TelemetriaNavegacao.java`

```java
package avionica.persistence.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "telemetria_navegacao")
public class TelemetriaNavegacao {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "recebido_em", nullable = false, updatable = false)
    private Instant recebidoEm = Instant.now();

    @Column(name = "proa_graus", precision = 5, scale = 1)
    private BigDecimal proaGraus;

    @Column(name = "vs_fpm")
    private Integer vsFpm;

    @Column(name = "piloto_automatico")
    private Boolean pilotoAutomatico;

    @Column(name = "waypoint_ativo", length = 100)
    private String waypointAtivo;

    @Column(name = "eta_minutos")
    private Integer etaMinutos;

    @Column(name = "origem", length = 100)
    private String origem;

    public TelemetriaNavegacao() {}

    public UUID getId() { return id; }
    public Instant getRecebidoEm() { return recebidoEm; }
    public BigDecimal getProaGraus() { return proaGraus; }
    public void setProaGraus(BigDecimal v) { this.proaGraus = v; }
    public Integer getVsFpm() { return vsFpm; }
    public void setVsFpm(Integer v) { this.vsFpm = v; }
    public Boolean getPilotoAutomatico() { return pilotoAutomatico; }
    public void setPilotoAutomatico(Boolean v) { this.pilotoAutomatico = v; }
    public String getWaypointAtivo() { return waypointAtivo; }
    public void setWaypointAtivo(String v) { this.waypointAtivo = v; }
    public Integer getEtaMinutos() { return etaMinutos; }
    public void setEtaMinutos(Integer v) { this.etaMinutos = v; }
    public String getOrigem() { return origem; }
    public void setOrigem(String v) { this.origem = v; }
}
```

### 4.6 — `EventoAntiIce.java`

```java
package avionica.persistence.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "eventos_anti_ice")
public class EventoAntiIce {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "registrado_em", nullable = false, updatable = false)
    private Instant registradoEm = Instant.now();

    @Column(name = "status", length = 50)
    private String status;

    @Column(name = "mensagem", columnDefinition = "TEXT")
    private String mensagem;

    @Column(name = "temperatura_c", precision = 5, scale = 1)
    private BigDecimal temperaturaC;

    @Column(name = "origem", length = 100)
    private String origem;

    public EventoAntiIce() {}

    public UUID getId() { return id; }
    public Instant getRegistradoEm() { return registradoEm; }
    public String getStatus() { return status; }
    public void setStatus(String v) { this.status = v; }
    public String getMensagem() { return mensagem; }
    public void setMensagem(String v) { this.mensagem = v; }
    public BigDecimal getTemperaturaC() { return temperaturaC; }
    public void setTemperaturaC(BigDecimal v) { this.temperaturaC = v; }
    public String getOrigem() { return origem; }
    public void setOrigem(String v) { this.origem = v; }
}
```

---

## 📚 Passo 5 — Repositories

> `AlertaRepository`, `RotaFmsRepository`, `TelemetriaVooRepository` e `MensagemBarramentoRepository` estão completos no Plano 02. Abaixo os repositories restantes.

### `TelemetriaFreiosRepository.java`

```java
package avionica.persistence.repository;

import avionica.persistence.entity.TelemetriaFreios;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Repository
public interface TelemetriaFreiosRepository extends JpaRepository<TelemetriaFreios, UUID> {
    List<TelemetriaFreios> findAllByOrderByRecebidoEmDesc(Pageable pageable);
    List<TelemetriaFreios> findByRecebidoEmAfterOrderByRecebidoEmAsc(Instant desde);
}
```

### `TelemetriaRadarRepository.java`

```java
package avionica.persistence.repository;

import avionica.persistence.entity.TelemetriaRadar;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Repository
public interface TelemetriaRadarRepository extends JpaRepository<TelemetriaRadar, UUID> {
    List<TelemetriaRadar> findAllByOrderByRecebidoEmDesc(Pageable pageable);
    List<TelemetriaRadar> findByRecebidoEmAfterOrderByRecebidoEmAsc(Instant desde);
    // Consulta especial: todas as ocorrências de tempestade
    List<TelemetriaRadar> findByRadarClimaContainingIgnoreCaseOrderByRecebidoEmDesc(
        String clima, Pageable pageable
    );
}
```

### `TelemetriaWaicRepository.java`

```java
package avionica.persistence.repository;

import avionica.persistence.entity.TelemetriaWaic;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Repository
public interface TelemetriaWaicRepository extends JpaRepository<TelemetriaWaic, UUID> {
    List<TelemetriaWaic> findAllByOrderByRecebidoEmDesc(Pageable pageable);
    List<TelemetriaWaic> findByRecebidoEmAfterOrderByRecebidoEmAsc(Instant desde);
}
```

### `TelemetriaNavegacaoRepository.java`

```java
package avionica.persistence.repository;

import avionica.persistence.entity.TelemetriaNavegacao;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.UUID;

@Repository
public interface TelemetriaNavegacaoRepository extends JpaRepository<TelemetriaNavegacao, UUID> {
    List<TelemetriaNavegacao> findAllByOrderByRecebidoEmDesc(Pageable pageable);
}
```

### `EventoAntiIceRepository.java`

```java
package avionica.persistence.repository;

import avionica.persistence.entity.EventoAntiIce;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.UUID;

@Repository
public interface EventoAntiIceRepository extends JpaRepository<EventoAntiIce, UUID> {
    List<EventoAntiIce> findAllByOrderByRegistradoEmDesc();
    List<EventoAntiIce> findByStatusOrderByRegistradoEmDesc(String status);
}
```

---

## ⚙️ Passo 6 — Services de Persistência

### 6.1 — `TelemetriaPersistenceService.java` — versão completa

Expande o Plano 02 com todos os tópicos MQTT mapeados:

```java
package avionica.persistence.service;

import avionica.persistence.entity.*;
import avionica.persistence.repository.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.math.BigDecimal;
import java.util.Map;

@Service
public class TelemetriaPersistenceService {

    private static final Logger log = LoggerFactory.getLogger(TelemetriaPersistenceService.class);

    private final MensagemBarramentoRepository barramentoRepo;
    private final TelemetriaVooRepository vooRepo;
    private final TelemetriaFreiosRepository freiosRepo;
    private final TelemetriaRadarRepository radarRepo;
    private final TelemetriaWaicRepository waicRepo;
    private final TelemetriaNavegacaoRepository navRepo;
    private final EventoAntiIceRepository antiIceRepo;
    private final AlertaRepository alertaRepo;

    public TelemetriaPersistenceService(
        MensagemBarramentoRepository barramentoRepo,
        TelemetriaVooRepository vooRepo,
        TelemetriaFreiosRepository freiosRepo,
        TelemetriaRadarRepository radarRepo,
        TelemetriaWaicRepository waicRepo,
        TelemetriaNavegacaoRepository navRepo,
        EventoAntiIceRepository antiIceRepo,
        AlertaRepository alertaRepo
    ) {
        this.barramentoRepo = barramentoRepo;
        this.vooRepo        = vooRepo;
        this.freiosRepo     = freiosRepo;
        this.radarRepo      = radarRepo;
        this.waicRepo       = waicRepo;
        this.navRepo        = navRepo;
        this.antiIceRepo    = antiIceRepo;
        this.alertaRepo     = alertaRepo;
    }

    // @Async → roda em thread separada, não bloqueia o callback MQTT
    @Async("persistenceExecutor")
    @Transactional
    public void persistirMensagem(String topico, Map<String, Object> payload, int tamanhoBytes) {
        try {
            // 1. Sempre salva no log do barramento (auditoria)
            salvarBarramento(topico, payload, tamanhoBytes);

            // 2. Salva na tabela específica conforme o tópico MQTT
            switch (topico) {
                case "avionica/sensores/voo"     -> persistirVoo(payload);
                case "avionica/sensores/freios"  -> persistirFreios(payload);
                case "avionica/radar"            -> persistirRadar(payload);
                case "avionica/sensores/waic"    -> persistirWaic(payload);
                case "avionica/navegacao"        -> persistirNavegacao(payload);
                case "avionica/sistemas/anti_ice"-> persistirAntiIce(payload);
                case "avionica/comandos/falhas"  -> persistirAlerta(payload);
                default -> log.debug("Tópico sem tabela específica: {}", topico);
            }
        } catch (Exception e) {
            log.error("Falha ao persistir mensagem do tópico '{}': {}", topico, e.getMessage(), e);
        }
    }

    // ─── Barramento (log de todas as mensagens) ──────────────────
    private void salvarBarramento(String topico, Map<String, Object> payload, int bytes) {
        MensagemBarramento msg = new MensagemBarramento();
        msg.setTopico(topico);
        msg.setPayloadJson(payload);
        msg.setTamanhoBytes(bytes);
        barramentoRepo.save(msg);
    }

    // ─── Telemetria de Voo ────────────────────────────────────────
    private void persistirVoo(Map<String, Object> payload) {
        Map<?, ?> dados = extrairDados(payload);
        if (dados == null) return;

        TelemetriaVoo e = new TelemetriaVoo();
        e.setCombustivelPct(toBD(dados.get("combustivel_pct")));
        e.setAltitudeFt(toInt(dados.get("altitude_ft")));
        e.setEstabilizadorGraus(toBD(dados.get("estabilizador_graus")));
        e.setPressaoCabinePsi(toBD(dados.get("pressao_cabine_psi")));
        e.setVelocidadeMach(toBD(dados.get("velocidade_mach")));
        e.setOrigem(toStr(payload.get("origem")));
        vooRepo.save(e);
    }

    // ─── Freios ───────────────────────────────────────────────────
    private void persistirFreios(Map<String, Object> payload) {
        Map<?, ?> dados = extrairDados(payload);
        if (dados == null) return;

        TelemetriaFreios e = new TelemetriaFreios();
        e.setPressaoPsi(toBD(dados.get("pressao")));
        e.setOrigem(toStr(payload.get("origem")));
        freiosRepo.save(e);
    }

    // ─── Radar ────────────────────────────────────────────────────
    private void persistirRadar(Map<String, Object> payload) {
        Map<?, ?> dados = extrairDados(payload);
        if (dados == null) return;

        TelemetriaRadar e = new TelemetriaRadar();
        e.setVentoKnots(toBD(dados.get("vento_knots")));
        e.setTurbulencia(toStr(dados.get("turbulencia")));
        e.setRadarClima(toStr(dados.get("radar_clima")));
        e.setTempExternaC(toBD(dados.get("temp_externa_c")));
        e.setQnhHpa(toBD(dados.get("qnh_hpa")));
        e.setAtcMsg(toStr(dados.get("atc_msg")));
        radarRepo.save(e);
    }

    // ─── WAIC ─────────────────────────────────────────────────────
    private void persistirWaic(Map<String, Object> payload) {
        Map<?, ?> dados = extrairDados(payload);
        if (dados == null) return;

        TelemetriaWaic e = new TelemetriaWaic();
        e.setPressaoMotor(toBD(dados.get("pressao_motor")));
        e.setTemperaturaC(toBD(dados.get("temperatura")));
        e.setOrigem(toStr(payload.get("origem")));
        waicRepo.save(e);
    }

    // ─── Navegação ────────────────────────────────────────────────
    private void persistirNavegacao(Map<String, Object> payload) {
        Map<?, ?> dados = extrairDados(payload);
        if (dados == null) return;

        TelemetriaNavegacao e = new TelemetriaNavegacao();
        e.setProaGraus(toBD(dados.get("proa_graus")));
        e.setVsFpm(toInt(dados.get("vs_fpm")));
        e.setWaypointAtivo(toStr(dados.get("waypoint_ativo")));
        e.setEtaMinutos(toInt(dados.get("eta_minutos")));
        Object ap = dados.get("piloto_automatico");
        e.setPilotoAutomatico(ap != null && !ap.toString().isBlank());
        navRepo.save(e);
    }

    // ─── Anti-Ice ────────────────────────────────────────────────
    private void persistirAntiIce(Map<String, Object> payload) {
        EventoAntiIce e = new EventoAntiIce();
        e.setStatus(toStr(payload.get("status")));
        e.setMensagem(toStr(payload.get("msg")));
        antiIceRepo.save(e);
    }

    // ─── Alertas / Falhas ────────────────────────────────────────
    private void persistirAlerta(Map<String, Object> payload) {
        String tipo = toStr(payload.get("tipo"));
        if (tipo == null || tipo.isBlank()) return;

        Alerta e = new Alerta();
        e.setTipo(tipo.toUpperCase());
        e.setDescricao("Alerta gerado pelo barramento MQTT");
        e.setSeveridade(
            tipo.equalsIgnoreCase("motor") ? Alerta.Severidade.CRITICAL : Alerta.Severidade.WARNING
        );
        e.setOrigem("mqtt:avionica/comandos/falhas");
        alertaRepo.save(e);
    }

    // ─── Helpers ──────────────────────────────────────────────────
    @SuppressWarnings("unchecked")
    private Map<?, ?> extrairDados(Map<String, Object> payload) {
        Object dados = payload.get("dados");
        return (dados instanceof Map<?, ?> m) ? m : null;
    }

    private BigDecimal toBD(Object v) {
        if (v == null) return null;
        try { return new BigDecimal(v.toString()); }
        catch (NumberFormatException e) { return null; }
    }

    private Integer toInt(Object v) {
        if (v == null) return null;
        try { return ((Number) v).intValue(); }
        catch (Exception e) { return null; }
    }

    private String toStr(Object v) {
        return v == null ? null : v.toString();
    }
}
```

### 6.2 — `AlertaService.java`

```java
package avionica.persistence.service;

import avionica.persistence.entity.Alerta;
import avionica.persistence.repository.AlertaRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Service
public class AlertaService {

    private final AlertaRepository alertaRepository;

    public AlertaService(AlertaRepository alertaRepository) {
        this.alertaRepository = alertaRepository;
    }

    public List<Alerta> listarAtivos() {
        return alertaRepository.findByResolvidoFalseOrderByRegistradoEmDesc();
    }

    public List<Alerta> listarCriticos() {
        return alertaRepository.findBySeveridadeAndResolvidoFalseOrderByRegistradoEmDesc(
            Alerta.Severidade.CRITICAL
        );
    }

    @Transactional
    public Alerta resolver(UUID id) {
        Alerta alerta = alertaRepository.findById(id)
            .orElseThrow(() -> new IllegalArgumentException("Alerta não encontrado: " + id));
        alerta.setResolvido(true);
        alerta.setResolvidoEm(Instant.now());
        return alertaRepository.save(alerta);
    }

    @Transactional
    public Alerta criarManual(String tipo, String descricao, Alerta.Severidade severidade, String origem) {
        Alerta alerta = new Alerta();
        alerta.setTipo(tipo);
        alerta.setDescricao(descricao);
        alerta.setSeveridade(severidade);
        alerta.setOrigem(origem);
        return alertaRepository.save(alerta);
    }
}
```

### 6.3 — `RotaFmsService.java`

```java
package avionica.persistence.service;

import avionica.persistence.entity.RotaFms;
import avionica.persistence.repository.RotaFmsRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;
import java.util.Optional;

@Service
public class RotaFmsService {

    private final RotaFmsRepository rotaFmsRepository;

    public RotaFmsService(RotaFmsRepository rotaFmsRepository) {
        this.rotaFmsRepository = rotaFmsRepository;
    }

    public Optional<RotaFms> rotaAtiva() {
        return rotaFmsRepository.findFirstByAtivaTrue();
    }

    public List<RotaFms> historico() {
        return rotaFmsRepository.findAllByOrderByRegistradoEmDesc();
    }

    @Transactional
    public RotaFms registrarNovaRota(String icaoOrigem, String icaoDestino) {
        // Desativa rota anterior
        rotaFmsRepository.findFirstByAtivaTrue()
            .ifPresent(r -> {
                r.setAtiva(false);
                rotaFmsRepository.save(r);
            });

        // Cria nova rota (distância e ETA serão atualizados quando o FMS responder via MQTT)
        RotaFms novaRota = new RotaFms();
        novaRota.setIcaoOrigem(icaoOrigem.toUpperCase());
        novaRota.setIcaoDestino(icaoDestino.toUpperCase());
        novaRota.setRotaTexto(icaoOrigem.toUpperCase() + " → " + icaoDestino.toUpperCase());
        novaRota.setAtiva(true);
        return rotaFmsRepository.save(novaRota);
    }
}
```

---

## 🔌 Passo 7 — Modificar `AircraftTelemetryService.java`

**Arquivo existente:** [`AircraftTelemetryService.java`](file:///C:/projetos/Sistemas_Distribuidos_Avionica/backend/src/main/avionica/telemetry/AircraftTelemetryService.java)

Apenas **3 mudanças** no arquivo existente:

```java
// ① Adicionar campo (ao lado dos outros campos, linha ~36):
private final TelemetriaPersistenceService persistenceService;

// ② Atualizar construtor (substituir o construtor existente):
public AircraftTelemetryService(
    @Value("${app.mqtt.broker-url}") String brokerUrl,
    @Value("${app.mqtt.topic-filter}") String topicFilter,
    TelemetriaPersistenceService persistenceService     // ← NOVO
) {
    this.brokerUrl          = brokerUrl;
    this.topicFilter        = topicFilter;
    this.persistenceService = persistenceService;       // ← NOVO
}

// ③ Adicionar 1 linha no final do messageArrived() (antes do fechamento):
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

    // ← ÚNICA LINHA NOVA: persiste no banco de forma assíncrona
    persistenceService.persistirMensagem(topic, payload, mqttMessage.getPayload().length);
}
```

---

## 🌐 Passo 8 — Controllers REST Novos

### 8.1 — `TelemetriaController.java` (histórico paginado)

```java
package avionica.api;

import avionica.persistence.entity.TelemetriaVoo;
import avionica.persistence.repository.TelemetriaVooRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/telemetria")
public class TelemetriaController {

    private final TelemetriaVooRepository vooRepository;

    public TelemetriaController(TelemetriaVooRepository vooRepository) {
        this.vooRepository = vooRepository;
    }

    // GET /api/telemetria/voo?limite=50
    // Retorna os últimos N registros de telemetria de voo
    @GetMapping("/voo")
    public List<TelemetriaVoo> historicVoo(
        @RequestParam(defaultValue = "50") int limite
    ) {
        int max = Math.min(limite, 500); // nunca mais de 500 registros por consulta
        return vooRepository.findAllByOrderByRecebidoEmDesc(PageRequest.of(0, max));
    }
}
```

### 8.2 — `AlertaController.java` (completo — expande o Plano 02)

```java
package avionica.api;

import avionica.persistence.entity.Alerta;
import avionica.persistence.service.AlertaService;
import jakarta.validation.constraints.NotBlank;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/alertas")
public class AlertaController {

    private final AlertaService alertaService;

    public AlertaController(AlertaService alertaService) {
        this.alertaService = alertaService;
    }

    // GET /api/alertas — alertas não resolvidos
    @GetMapping
    public List<Alerta> listarAtivos() {
        return alertaService.listarAtivos();
    }

    // GET /api/alertas/criticos
    @GetMapping("/criticos")
    public List<Alerta> listarCriticos() {
        return alertaService.listarCriticos();
    }

    // PATCH /api/alertas/{id}/resolver
    @PatchMapping("/{id}/resolver")
    public ResponseEntity<Alerta> resolver(@PathVariable UUID id) {
        try {
            return ResponseEntity.ok(alertaService.resolver(id));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }

    // POST /api/alertas — cria alerta manual (uso do Instrutor via frontend)
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Alerta criarManual(@RequestBody CriarAlertaRequest req) {
        return alertaService.criarManual(req.tipo(), req.descricao(),
            Alerta.Severidade.valueOf(req.severidade()), req.origem());
    }

    // DTO de entrada (Record Java — sem boilerplate)
    public record CriarAlertaRequest(
        @NotBlank String tipo,
        String descricao,
        @NotBlank String severidade,
        String origem
    ) {}
}
```

### 8.3 — `ComandoController.java` — publica comandos no MQTT via backend

```java
package avionica.api;

import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/comandos")
public class ComandoController {

    private static final Logger log = LoggerFactory.getLogger(ComandoController.class);

    // Injeta o MqttClient gerenciado pelo AircraftTelemetryService
    // (expor o client via método público ou criar bean dedicado)
    private final MqttClient mqttClient;

    public ComandoController(MqttClient mqttClient) {
        this.mqttClient = mqttClient;
    }

    // POST /api/comandos/velocidade — { "nova_velocidade": 0.85 }
    @PostMapping("/velocidade")
    public ResponseEntity<Map<String, Object>> ajustarVelocidade(
        @RequestBody Map<String, Double> body
    ) {
        Double novaVel = body.get("nova_velocidade");
        if (novaVel == null || novaVel < 0.4 || novaVel > 1.0) {
            return ResponseEntity.badRequest()
                .body(Map.of("erro", "Velocidade deve ser entre 0.40 e 1.00 Mach"));
        }
        publicar("avionica/comandos/velocidade",
            new JSONObject().put("nova_velocidade", novaVel).toString());
        return ResponseEntity.ok(Map.of("status", "Comando enviado", "nova_velocidade", novaVel));
    }

    // POST /api/comandos/proa — { "nova_proa": 271 }
    @PostMapping("/proa")
    public ResponseEntity<Map<String, Object>> ajustarProa(
        @RequestBody Map<String, Integer> body
    ) {
        Integer novaProa = body.get("nova_proa");
        if (novaProa == null) {
            return ResponseEntity.badRequest().body(Map.of("erro", "Campo nova_proa é obrigatório"));
        }
        int proaNormalizada = ((novaProa % 360) + 360) % 360;
        publicar("avionica/comandos/proa",
            new JSONObject().put("nova_proa", proaNormalizada).toString());
        return ResponseEntity.ok(Map.of("status", "Comando enviado", "nova_proa", proaNormalizada));
    }

    // POST /api/comandos/rota — { "origem": "SBGR", "destino": "EGLL" }
    @PostMapping("/rota")
    public ResponseEntity<Map<String, Object>> definirRota(
        @RequestBody Map<String, String> body
    ) {
        String origem  = body.get("origem");
        String destino = body.get("destino");
        if (origem == null || origem.length() != 4 || destino == null || destino.length() != 4) {
            return ResponseEntity.badRequest()
                .body(Map.of("erro", "Códigos ICAO devem ter exatamente 4 caracteres"));
        }
        publicar("avionica/comandos/rota",
            new JSONObject().put("origem", origem.toUpperCase())
                           .put("destino", destino.toUpperCase()).toString());
        return ResponseEntity.ok(Map.of("status", "Rota enviada ao FMS",
            "origem", origem.toUpperCase(), "destino", destino.toUpperCase()));
    }

    // POST /api/comandos/falhas — { "tipo": "motor" | "trafego" | "queda" }
    @PostMapping("/falhas")
    public ResponseEntity<Map<String, Object>> injetarFalha(
        @RequestBody Map<String, String> body
    ) {
        String tipo = body.get("tipo");
        if (tipo == null || tipo.isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("erro", "Campo tipo é obrigatório"));
        }
        publicar("avionica/comandos/falhas", new JSONObject().put("tipo", tipo).toString());
        log.warn("Falha injetada via API: tipo={}", tipo);
        return ResponseEntity.ok(Map.of("status", "Falha injetada", "tipo", tipo));
    }

    private void publicar(String topico, String payload) {
        try {
            MqttMessage msg = new MqttMessage(payload.getBytes());
            msg.setQos(1);
            mqttClient.publish(topico, msg);
        } catch (MqttException e) {
            log.error("Falha ao publicar comando no tópico {}: {}", topico, e.getMessage());
        }
    }
}
```

### 8.4 — `RotaFmsController.java`

```java
package avionica.api;

import avionica.persistence.entity.RotaFms;
import avionica.persistence.service.RotaFmsService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/rotas")
public class RotaFmsController {

    private final RotaFmsService rotaFmsService;

    public RotaFmsController(RotaFmsService rotaFmsService) {
        this.rotaFmsService = rotaFmsService;
    }

    // GET /api/rotas/ativa
    @GetMapping("/ativa")
    public ResponseEntity<RotaFms> rotaAtiva() {
        return rotaFmsService.rotaAtiva()
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.noContent().build());
    }

    // GET /api/rotas — histórico completo
    @GetMapping
    public List<RotaFms> historico() {
        return rotaFmsService.historico();
    }
}
```

---

## ⚠️ Passo 9 — Tratamento Global de Erros

### `GlobalExceptionHandler.java`

```java
package avionica.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.Instant;

// Intercepta todas as exceções não tratadas nos controllers
// e retorna um JSON padronizado (RFC 9457 — Problem Details)
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    // 400 — Argumento inválido (ex: ICAO com tamanho errado)
    @ExceptionHandler(IllegalArgumentException.class)
    public ProblemDetail handleIllegalArgument(IllegalArgumentException ex) {
        log.warn("Requisição inválida: {}", ex.getMessage());
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        problem.setTitle("Requisição inválida");
        problem.setDetail(ex.getMessage());
        problem.setProperty("timestamp", Instant.now());
        return problem;
    }

    // 500 — Erros inesperados
    @ExceptionHandler(Exception.class)
    public ProblemDetail handleGeneric(Exception ex) {
        log.error("Erro interno não tratado: {}", ex.getMessage(), ex);
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.INTERNAL_SERVER_ERROR);
        problem.setTitle("Erro interno do servidor");
        problem.setDetail("Um erro inesperado ocorreu. Verifique os logs do backend.");
        problem.setProperty("timestamp", Instant.now());
        return problem;
    }
}
```

---

## 🧵 Passo 10 — Thread Pool para @Async

### `AsyncConfig.java`

```java
package avionica.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import java.util.concurrent.Executor;

@Configuration
public class AsyncConfig {

    // Pool dedicado para persistência assíncrona
    // Separa threads de persistência das threads do servidor HTTP
    @Bean(name = "persistenceExecutor")
    public Executor persistenceExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(3);      // 3 threads sempre ativas
        executor.setMaxPoolSize(10);      // até 10 threads em pico
        executor.setQueueCapacity(500);   // fila de até 500 tarefas antes de rejeitar
        executor.setThreadNamePrefix("persist-");
        executor.initialize();
        return executor;
    }
}
```

---

## 🚀 Passo 11 — Atualizar `AvionicaBackendApplication.java`

```java
package avionica;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync  // ← habilita @Async no TelemetriaPersistenceService
public class AvionicaBackendApplication {
    public static void main(String[] args) {
        SpringApplication.run(AvionicaBackendApplication.class, args);
    }
}
```

---

## 🧪 Passo 12 — Testes

### 12.1 — Teste de integração do `AlertaController`

```java
// src/test/avionica/api/AlertaControllerTest.java
package avionica.api;

import avionica.persistence.entity.Alerta;
import avionica.persistence.service.AlertaService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(AlertaController.class)
class AlertaControllerTest {

    @Autowired MockMvc mockMvc;
    @MockBean  AlertaService alertaService;

    @Test
    void listarAtivos_deveRetornarListaVazia_quandoNaoHaAlertas() throws Exception {
        when(alertaService.listarAtivos()).thenReturn(List.of());

        mockMvc.perform(get("/api/alertas"))
            .andExpect(status().isOk())
            .andExpect(content().json("[]"));
    }

    @Test
    void listarAtivos_deveRetornarAlertas_quandoExistem() throws Exception {
        Alerta alerta = new Alerta();
        alerta.setTipo("OVERSPEED");
        alerta.setSeveridade(Alerta.Severidade.CRITICAL);

        when(alertaService.listarAtivos()).thenReturn(List.of(alerta));

        mockMvc.perform(get("/api/alertas"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].tipo").value("OVERSPEED"))
            .andExpect(jsonPath("$[0].severidade").value("CRITICAL"));
    }
}
```

### 12.2 — Teste unitário do `TelemetriaPersistenceService`

```java
// src/test/avionica/persistence/service/TelemetriaPersistenceServiceTest.java
package avionica.persistence.service;

import avionica.persistence.repository.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class TelemetriaPersistenceServiceTest {

    @Mock MensagemBarramentoRepository barramentoRepo;
    @Mock TelemetriaVooRepository vooRepo;
    @Mock TelemetriaFreiosRepository freiosRepo;
    @Mock TelemetriaRadarRepository radarRepo;
    @Mock TelemetriaWaicRepository waicRepo;
    @Mock TelemetriaNavegacaoRepository navRepo;
    @Mock EventoAntiIceRepository antiIceRepo;
    @Mock AlertaRepository alertaRepo;

    TelemetriaPersistenceService service;

    @BeforeEach
    void setUp() {
        service = new TelemetriaPersistenceService(
            barramentoRepo, vooRepo, freiosRepo, radarRepo,
            waicRepo, navRepo, antiIceRepo, alertaRepo
        );
    }

    @Test
    void persistirMensagem_deveUsarRepository_quandoTopicoEhVoo() {
        Map<String, Object> payload = Map.of(
            "origem", "Sensores_Gerais_Voo",
            "dados", Map.of(
                "combustivel_pct", 87.5,
                "altitude_ft", 35000,
                "velocidade_mach", 0.802
            )
        );

        service.persistirMensagem("avionica/sensores/voo", payload, 150);

        // Deve salvar no barramento (sempre)
        verify(barramentoRepo, times(1)).save(any());
        // Deve salvar na tabela específica de voo
        verify(vooRepo, times(1)).save(any());
        // Não deve tocar nos outros repositories
        verifyNoInteractions(freiosRepo, radarRepo, alertaRepo);
    }

    @Test
    void persistirMensagem_deveIgnorar_quandoPayloadSemCampoDados() {
        Map<String, Object> payloadSemDados = Map.of("origem", "sensor_x");

        service.persistirMensagem("avionica/sensores/voo", payloadSemDados, 30);

        // Barramento salva sempre
        verify(barramentoRepo, times(1)).save(any());
        // Voo não salva (sem campo "dados")
        verifyNoInteractions(vooRepo);
    }
}
```

---

## 🗺️ Tabela Completa de Endpoints REST

| Método | Endpoint | Descrição | Retorno |
|---|---|---|---|
| `GET` | `/api/health` | Status do backend | `{ "status": "UP" }` |
| `GET` | `/api/modules` | Status dos módulos Docker | `[ { "name": "...", "status": "..." } ]` |
| `GET` | `/api/aircraft-data` | Snapshot atual (em memória) | `AircraftDataSnapshot` |
| `GET` | `/api/telemetria/voo?limite=50` | Histórico paginado de voo | `[ TelemetriaVoo ]` |
| `GET` | `/api/alertas` | Alertas não resolvidos | `[ Alerta ]` |
| `GET` | `/api/alertas/criticos` | Alertas CRITICAL não resolvidos | `[ Alerta ]` |
| `POST` | `/api/alertas` | Cria alerta manual | `Alerta` |
| `PATCH` | `/api/alertas/{id}/resolver` | Resolve um alerta | `Alerta` |
| `GET` | `/api/rotas/ativa` | Rota FMS atual | `RotaFms` ou 204 |
| `GET` | `/api/rotas` | Histórico de rotas | `[ RotaFms ]` |
| `POST` | `/api/comandos/velocidade` | Ajusta autothrottle | `{ "status": "Comando enviado" }` |
| `POST` | `/api/comandos/proa` | Ajusta heading | `{ "status": "Comando enviado" }` |
| `POST` | `/api/comandos/rota` | Define rota no FMS | `{ "status": "Rota enviada ao FMS" }` |
| `POST` | `/api/comandos/falhas` | Injeta falha (Instrutor) | `{ "status": "Falha injetada" }` |

---

## ✅ Checklist de Execução

```
[ ] Passo 1  — build.gradle atualizado (jdbc → jpa, validation adicionada)
[ ] Passo 2  — application.yml com configurações JPA, Hikari e tópicos Kafka
[ ] Passo 3  — diretório persistence/ criado na estrutura de pacotes
[ ] Passo 4  — 9 entidades JPA criadas e anotadas
[ ] Passo 5  — 9 repositories Spring Data criados
[ ] Passo 6  — TelemetriaPersistenceService com todos os 8 tópicos mapeados
[ ] Passo 6  — AlertaService e RotaFmsService criados
[ ] Passo 7  — AircraftTelemetryService modificado (construtor + messageArrived)
[ ] Passo 8  — 4 novos controllers criados (Telemetria, Alerta, Comando, RotaFms)
[ ] Passo 9  — GlobalExceptionHandler criado
[ ] Passo 10 — AsyncConfig criado com pool "persistenceExecutor"
[ ] Passo 11 — @EnableAsync adicionado na AvionicaBackendApplication
[ ] Passo 12 — Schema DDL aplicado no banco (Plano 01 executado)
[ ] Passo 12 — docker compose up -d postgres && docker compose up -d --build backend-gateway
[ ] Verificar — curl http://localhost:8080/api/alertas → retorna []
[ ] Verificar — curl http://localhost:8080/api/aircraft-data → retorna snapshot
[ ] Verificar — SELECT COUNT(*) FROM mensagens_barramento → número cresce a cada 2s
```
