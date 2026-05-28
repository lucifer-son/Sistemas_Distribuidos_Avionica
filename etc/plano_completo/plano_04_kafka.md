# ⚡ Plano 04 — Apache Kafka: Por que, Como e o Impacto no Sistema Aviônico

> **Sistema:** Gateway Tolerante a Falhas para Redes Aviônicas Híbridas (AFDX/WAIC)  
> **Dependência já declarada:** `spring-kafka` no `build.gradle`  
> **Kafka já no Docker:** `apache/kafka:4.1.1` no `docker-compose.yml`  
> **Problema:** Kafka está configurado mas **zero código Java usa ele ainda**

---

## 🔍 Por que o Kafka é importante neste projeto específico?

Para responder isso precisamos olhar para o que o código atual realmente faz.

### O problema do `AircraftTelemetryService.java` hoje

```
[Sensor Python] → MQTT → [messageArrived()] → latestByTopic (Map em memória)
                                             → recentMessages (Deque com 30 itens)
```

Isso parece simples, mas esconde **três falhas críticas** para um sistema aviônico:

---

### ❌ Falha 1 — O callback MQTT faz trabalho demais (acoplamento direto)

Hoje o método `messageArrived()` é chamado diretamente pela thread do MQTT. Se amanhã você adicionar persistência no banco, o fluxo vira:

```
[messageArrived()] → salvar no banco → (banco lento ou fora do ar) → bloqueia a thread MQTT
                                                                    → próxima mensagem do sensor atrasa
                                                                    → dados de voo se perdem
```

Em aviação, **perder dados de altitude ou combustível por causa de uma lentidão no banco é inaceitável**.

---

### ❌ Falha 2 — A fila de 30 mensagens em memória é frágil

```java
// AircraftTelemetryService.java — linha 41
private final Deque<AircraftMessage> recentMessages = new ArrayDeque<>();

// linha 126
while (recentMessages.size() > 30) {
    recentMessages.removeFirst(); // ← mensagem jogada fora para sempre
}
```

Se o container `backend-gateway` reiniciar — por atualização, por crash, por OOM — **todas as 30 mensagens somem**. Não há histórico. Não há possibilidade de reprocessar.

---

### ❌ Falha 3 — Apenas um consumidor pode existir

Se você quiser que:
- o serviço de **persistência** salve no banco
- o serviço de **alertas** analise anomalias em tempo real
- um **serviço de auditoria** (caixa preta) registre eventos críticos
- um **serviço de analytics** calcule médias de combustível

...todos precisam consumir a mesma mensagem MQTT. Hoje é impossível — há um único `messageArrived()` e você teria que colocar toda essa lógica dentro dele, criando um monolito disfarçado de microsserviço.

---

### ✅ O que o Kafka resolve

O Kafka funciona como um **barramento durável e distribuído**. Ele transforma o fluxo em:

```
[Sensor Python]
      ↓ MQTT
[messageArrived()]  →  KafkaProducer  →  [Tópico Kafka: avionica.telemetria.voo]
                                                  ↓               ↓               ↓
                                         [Consumer: DB]  [Consumer: Alertas]  [Consumer: Auditoria]
```

Cada consumer lê no seu próprio ritmo. Se o banco estiver lento, **o Kafka segura a mensagem** — ela não se perde. Se você adicionar um novo consumer no futuro, ele pode ler **desde o início** (replay).

---

## 🏗️ Arquitetura com Kafka no Projeto

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AERONAVE (Simulada)                          │
│  sensores_voo.py  sensor_freio.py  radar_externo.py  lider_waic.py  │
└────────────────────────────┬────────────────────────────────────────┘
                             │ MQTT (QoS 1)
                             ▼
                    ┌────────────────┐
                    │ Eclipse Mosquitto│  (mqtt-broker)
                    └────────┬───────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │   AircraftTelemetryService   │  ← já existe
              │   (MQTT Listener / Gateway)  │
              │                              │
              │  messageArrived()            │
              │     → atualiza memória       │
              │     → KafkaProducer.send()   │  ← NOVO
              └──────────────┬───────────────┘
                             │
                    ┌────────▼────────┐
                    │  Apache Kafka   │  (já no Docker)
                    │                 │
                    │ avionica.voo    │ ← topic
                    │ avionica.freios │ ← topic
                    │ avionica.radar  │ ← topic
                    │ avionica.waic   │ ← topic
                    │ avionica.alertas│ ← topic
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────────┐
          │                  │                       │
          ▼                  ▼                       ▼
 ┌─────────────────┐ ┌──────────────┐  ┌───────────────────────┐
 │ Consumer: DB    │ │ Consumer:    │  │ Consumer: Caixa Preta  │
 │ Persiste tudo   │ │ Alertas      │  │ (caixa_preta.py futuro)│
 │ no PostgreSQL   │ │ Analisa e    │  │ Auditoria imutável     │
 │                 │ │ dispara      │  │                        │
 └────────┬────────┘ │ notificações │  └────────────────────────┘
          │          └──────────────┘
          ▼
   ┌─────────────┐
   │ PostgreSQL  │  (avionica_postgres)
   │             │
   │ telemetria  │
   │ alertas     │
   └─────────────┘
```

---

## 💥 Impacto Real no Sistema — Comparativo

| Cenário | Sem Kafka (hoje) | Com Kafka |
|---|---|---|
| **Banco fora do ar por 30s** | Mensagens dos sensores são descartadas após 30 na fila | Kafka retém todas as mensagens; quando o banco volta, o consumer processa o acumulado |
| **Backend reinicia (crash/deploy)** | Fila de 30 mensagens em memória é destruída | Kafka persiste as mensagens no disco; o consumer retoma de onde parou |
| **Novo serviço de analytics** | Exige modificar `messageArrived()` e adicionar lógica | Cria um novo consumer group independente sem tocar no código existente |
| **Investigação de incidente** | Impossível — não há histórico além das últimas 30 msgs | Replay: leia todas as mensagens do tópico desde o início |
| **Pico de dados (10 sensores simultaneamente)** | A thread MQTT processa tudo sincrona e sequencialmente | Kafka absorve o pico; consumers processam em paralelo no seu ritmo |
| **Sensor de falha envia alertas em rajada** | Pode causar stack overflow ou delay visível na telemetria | Alertas vão para um tópico dedicado, processados por consumer isolado |

---

## 📦 Implementação Passo a Passo

### Passo 1 — Configurar os Tópicos Kafka no `application.yml`

Adicione a seção `app.kafka.topics` no `application.yml`:

```yaml
# application.yml — seção app já existe, adicione os tópicos:
app:
  kafka:
    bootstrap-servers: ${KAFKA_BOOTSTRAP_SERVERS:localhost:9092}
    topics:
      telemetria-voo:     avionica.telemetria.voo
      telemetria-freios:  avionica.telemetria.freios
      telemetria-radar:   avionica.telemetria.radar
      telemetria-waic:    avionica.telemetria.waic
      telemetria-nav:     avionica.telemetria.navegacao
      alertas:            avionica.alertas
      comandos:           avionica.comandos
```

---

### Passo 2 — Criar `KafkaConfig.java`

```java
// src/main/avionica/config/KafkaConfig.java
package avionica.config;

import org.apache.kafka.clients.admin.NewTopic;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.kafka.common.serialization.StringSerializer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.config.TopicBuilder;
import org.springframework.kafka.core.*;

import java.util.HashMap;
import java.util.Map;

@Configuration
public class KafkaConfig {

    @Value("${app.kafka.bootstrap-servers}")
    private String bootstrapServers;

    // ─────────────────────────────────────────
    // PRODUCER — Configuração do publicador
    // ─────────────────────────────────────────

    @Bean
    public ProducerFactory<String, String> producerFactory() {
        Map<String, Object> config = new HashMap<>();
        config.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        config.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        config.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class);

        // Garante que a mensagem só é confirmada quando TODOS os replicas receberam
        // (importante para dados críticos de aviação)
        config.put(ProducerConfig.ACKS_CONFIG, "all");

        // Tenta reenviar até 3 vezes em caso de falha de rede
        config.put(ProducerConfig.RETRIES_CONFIG, 3);

        // Agrupa mensagens em lotes de até 16KB para maior throughput
        config.put(ProducerConfig.BATCH_SIZE_CONFIG, 16384);

        return new DefaultKafkaProducerFactory<>(config);
    }

    @Bean
    public KafkaTemplate<String, String> kafkaTemplate() {
        return new KafkaTemplate<>(producerFactory());
    }

    // ─────────────────────────────────────────
    // CONSUMER — Configuração do consumidor
    // ─────────────────────────────────────────

    @Bean
    public ConsumerFactory<String, String> consumerFactory() {
        Map<String, Object> config = new HashMap<>();
        config.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        config.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        config.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);

        // EARLIEST = lê desde o início do tópico se não há offset salvo
        // Importante para não perder mensagens na primeira execução
        config.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");

        // Desabilita auto-commit: o offset só avança quando o processamento confirmar
        // Garante que uma mensagem não seja marcada como lida antes de ser persistida
        config.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);

        return new DefaultKafkaConsumerFactory<>(config);
    }

    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, String> kafkaListenerContainerFactory() {
        ConcurrentKafkaListenerContainerFactory<String, String> factory =
            new ConcurrentKafkaListenerContainerFactory<>();
        factory.setConsumerFactory(consumerFactory());
        // Commita o offset manualmente após processamento bem-sucedido
        factory.getContainerProperties().setAckMode(
            org.springframework.kafka.listener.ContainerProperties.AckMode.MANUAL_IMMEDIATE
        );
        return factory;
    }

    // ─────────────────────────────────────────
    // TÓPICOS — Criados automaticamente no boot
    // ─────────────────────────────────────────

    @Bean
    public NewTopic topicTelemetriaVoo() {
        return TopicBuilder.name("avionica.telemetria.voo")
            .partitions(3)   // 3 partições = 3 consumers em paralelo possíveis
            .replicas(1)     // 1 réplica (dev). Em prod: 3
            .build();
    }

    @Bean
    public NewTopic topicTelemetriaFreios() {
        return TopicBuilder.name("avionica.telemetria.freios")
            .partitions(1)
            .replicas(1)
            .build();
    }

    @Bean
    public NewTopic topicTelemetriaRadar() {
        return TopicBuilder.name("avionica.telemetria.radar")
            .partitions(1)
            .replicas(1)
            .build();
    }

    @Bean
    public NewTopic topicAlertas() {
        return TopicBuilder.name("avionica.alertas")
            .partitions(1)
            .replicas(1)
            .build();
    }

    @Bean
    public NewTopic topicComandos() {
        return TopicBuilder.name("avionica.comandos")
            .partitions(1)
            .replicas(1)
            .build();
    }
}
```

---

### Passo 3 — Criar `TelemetriaKafkaProducer.java`

Este producer é chamado dentro do `messageArrived()` para publicar cada mensagem MQTT no Kafka:

```java
// src/main/avionica/kafka/TelemetriaKafkaProducer.java
package avionica.kafka;

import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class TelemetriaKafkaProducer {

    private static final Logger logger = LoggerFactory.getLogger(TelemetriaKafkaProducer.class);

    // Mapeamento: tópico MQTT → tópico Kafka
    // Mantém os nomes dos tópicos Kafka centralizados aqui
    private static final Map<String, String> TOPICO_MQTT_PARA_KAFKA = Map.of(
        "avionica/sensores/voo",    "avionica.telemetria.voo",
        "avionica/sensores/freios", "avionica.telemetria.freios",
        "avionica/radar",           "avionica.telemetria.radar",
        "avionica/sensores/waic",   "avionica.telemetria.waic",
        "avionica/navegacao",       "avionica.telemetria.navegacao",
        "avionica/fms/dados",       "avionica.telemetria.voo",    // FMS vai no mesmo tópico de voo
        "avionica/comandos/falhas", "avionica.alertas",
        "avionica/sistemas/anti_ice", "avionica.alertas"
    );

    private final KafkaTemplate<String, String> kafkaTemplate;

    public TelemetriaKafkaProducer(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    /**
     * Publica uma mensagem no tópico Kafka correspondente ao tópico MQTT.
     *
     * @param topicoMqtt  O tópico MQTT de origem (ex: "avionica/sensores/voo")
     * @param payload     O payload JSON como Map (já parseado pelo AircraftTelemetryService)
     */
    public void publicar(String topicoMqtt, Map<String, Object> payload) {
        String topicoKafka = TOPICO_MQTT_PARA_KAFKA.get(topicoMqtt);

        if (topicoKafka == null) {
            // Tópico não mapeado — ignorar silenciosamente
            logger.debug("Tópico MQTT sem mapeamento Kafka: {}", topicoMqtt);
            return;
        }

        // Enriquece o payload com metadados antes de enviar ao Kafka
        Map<String, Object> mensagemEnriquecida = new java.util.LinkedHashMap<>(payload);
        mensagemEnriquecida.put("_mqtt_topic", topicoMqtt);
        mensagemEnriquecida.put("_kafka_sent_at", java.time.Instant.now().toString());

        String json = new JSONObject(mensagemEnriquecida).toString();

        // A chave de particionamento é o próprio tópico MQTT
        // Garante que mensagens do mesmo sensor sempre vão para a mesma partição (ordenação)
        kafkaTemplate.send(topicoKafka, topicoMqtt, json)
            .whenComplete((result, ex) -> {
                if (ex != null) {
                    logger.error("Falha ao publicar no Kafka [{}]: {}", topicoKafka, ex.getMessage());
                } else {
                    logger.debug("Publicado em Kafka [{}] | partition={} | offset={}",
                        topicoKafka,
                        result.getRecordMetadata().partition(),
                        result.getRecordMetadata().offset()
                    );
                }
            });
    }
}
```

---

### Passo 4 — Integrar o Producer no `AircraftTelemetryService.java`

Apenas **duas modificações** no arquivo existente:

```java
// 1. Adicione o campo (junto com os outros campos, linha ~36):
private final TelemetriaKafkaProducer kafkaProducer;

// 2. Atualize o construtor (substitua o existente):
public AircraftTelemetryService(
    @Value("${app.mqtt.broker-url}") String brokerUrl,
    @Value("${app.mqtt.topic-filter}") String topicFilter,
    TelemetriaKafkaProducer kafkaProducer          // ← NOVO parâmetro
) {
    this.brokerUrl = brokerUrl;
    this.topicFilter = topicFilter;
    this.kafkaProducer = kafkaProducer;            // ← NOVO
}

// 3. No método messageArrived(), adicione a última linha:
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

    kafkaProducer.publicar(topic, payload);  // ← NOVA LINHA — publica no Kafka
}
```

> **Nenhuma outra linha muda.** O Kafka entra como uma camada adicional sem quebrar o comportamento atual.

---

### Passo 5 — Criar `TelemetriaKafkaConsumer.java`

O consumer lê do Kafka e persiste no banco (depois que o JPA do Plano 02 estiver implementado):

```java
// src/main/avionica/kafka/TelemetriaKafkaConsumer.java
package avionica.kafka;

import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class TelemetriaKafkaConsumer {

    private static final Logger logger = LoggerFactory.getLogger(TelemetriaKafkaConsumer.class);

    // Por enquanto: log no console.
    // Após o Plano 02 (JPA), injete os repositories aqui e persista.

    /**
     * Consome o tópico de telemetria de voo.
     * groupId = "gateway-persistence": identifica este consumer como o grupo de persistência.
     * Se você criar outro grupo (ex: "gateway-alertas"), ele lê as mesmas mensagens
     * de forma INDEPENDENTE — cada grupo tem seu próprio offset.
     */
    @KafkaListener(
        topics = "avionica.telemetria.voo",
        groupId = "gateway-persistence",
        containerFactory = "kafkaListenerContainerFactory"
    )
    public void consumirTelemetriaVoo(
        @Payload String mensagemJson,
        @Header(KafkaHeaders.RECEIVED_TOPIC) String topico,
        @Header(KafkaHeaders.RECEIVED_PARTITION) int particao,
        @Header(KafkaHeaders.OFFSET) long offset,
        Acknowledgment ack  // confirmação manual do offset
    ) {
        try {
            Map<String, Object> payload = new JSONObject(mensagemJson).toMap();

            // ─── AQUI: persista no banco quando o JPA estiver pronto ───
            // telemetriaVooRepository.save(mapearParaEntidade(payload));

            logger.info("[KAFKA→DB] Telemetria de voo | tópico={} | partição={} | offset={}",
                topico, particao, offset);

            // Confirma que a mensagem foi processada com sucesso
            // O offset só avança agora — se der erro antes, a mensagem será reprocessada
            ack.acknowledge();

        } catch (Exception e) {
            logger.error("[KAFKA] Erro ao processar telemetria de voo | offset={} | erro={}",
                offset, e.getMessage());
            // NÃO chama ack.acknowledge() → Kafka tentará reenviar esta mensagem
        }
    }

    /**
     * Consome o tópico de alertas.
     * groupId diferente = consumer INDEPENDENTE que lê as mesmas mensagens de avionica.alertas
     */
    @KafkaListener(
        topics = "avionica.alertas",
        groupId = "gateway-alert-processor",
        containerFactory = "kafkaListenerContainerFactory"
    )
    public void consumirAlerta(
        @Payload String mensagemJson,
        @Header(KafkaHeaders.OFFSET) long offset,
        Acknowledgment ack
    ) {
        try {
            Map<String, Object> payload = new JSONObject(mensagemJson).toMap();
            String tipo = String.valueOf(payload.getOrDefault("tipo", "DESCONHECIDO"));

            // ─── AQUI: persistir alerta no banco e disparar notificação ───
            // alertaRepository.save(new Alerta(tipo, ...));

            logger.warn("[KAFKA→ALERTA] Tipo={} | offset={}", tipo, offset);
            ack.acknowledge();

        } catch (Exception e) {
            logger.error("[KAFKA] Erro ao processar alerta: {}", e.getMessage());
        }
    }
}
```

---

### Passo 6 — Consumer de Auditoria (Caixa Preta)

Este consumer demonstra o poder do Kafka: **um segundo grupo lendo os mesmos dados** sem nenhuma modificação no producer:

```java
// src/main/avionica/kafka/AuditoriaKafkaConsumer.java
package avionica.kafka;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Component;

/**
 * Consumer de auditoria — equivale ao caixa_preta.py mas no lado Java.
 * Lê TODOS os tópicos aviônicos e registra tudo para fins de auditoria.
 * Usa um groupId próprio: processa cada mensagem INDEPENDENTEMENTE do TelemetriaKafkaConsumer.
 */
@Component
public class AuditoriaKafkaConsumer {

    private static final Logger logger = LoggerFactory.getLogger(AuditoriaKafkaConsumer.class);

    @KafkaListener(
        topics = {
            "avionica.telemetria.voo",
            "avionica.telemetria.freios",
            "avionica.telemetria.radar",
            "avionica.telemetria.waic",
            "avionica.alertas"
        },
        groupId = "gateway-auditoria",           // ← groupId diferente = offset próprio
        containerFactory = "kafkaListenerContainerFactory"
    )
    public void auditar(
        @Payload String mensagemJson,
        @Header(KafkaHeaders.RECEIVED_TOPIC) String topico,
        @Header(KafkaHeaders.OFFSET) long offset,
        Acknowledgment ack
    ) {
        // Auditoria: registra TUDO independente do que o consumer de persistência fez
        // ─── AQUI: salvar em mensagens_barramento (tabela de auditoria do banco) ───
        logger.info("[AUDITORIA] tópico={} | offset={} | bytes={}",
            topico, offset, mensagemJson.length());
        ack.acknowledge();
    }
}
```

---

## 📊 Diagrama de Fluxo — Antes vs Depois

### Antes (sem Kafka)

```
MQTT ──► messageArrived()
              │
              ├──► Map<latestByTopic>  (1 valor por tópico, em RAM)
              └──► Deque<30 msgs>      (fila curta, em RAM)
                        │
                        └──► GET /api/aircraft-data  (frontend lê a cada 2s)

Problemas: sincrono, frágil, sem histórico, sem escalabilidade
```

### Depois (com Kafka)

```
MQTT ──► messageArrived()
              │
              ├──► Map<latestByTopic>        (mantido — leitura em tempo real do frontend)
              ├──► Deque<30 msgs>            (mantido — buffer de display)
              └──► KafkaProducer.send()      (NOVO — publicação assíncrona)
                        │
                        ▼
               [Apache Kafka — disco]
                        │
              ┌─────────┼──────────┐
              │         │          │
              ▼         ▼          ▼
        [Consumer:  [Consumer:  [Consumer:
         Persist.    Alertas]    Auditoria]
         → PostgreSQL  → Log      → mensagens_barramento]

Ganhos: assíncrono, durável, reprocessável, multi-consumer, escalável
```

---

## 🧪 Como Verificar que Está Funcionando

### 1. Listar tópicos criados no Kafka

```powershell
# Execute dentro do container Kafka
docker exec -it avionica_kafka /opt/kafka/bin/kafka-topics.sh `
  --bootstrap-server localhost:9092 `
  --list
```

Saída esperada:
```
avionica.alertas
avionica.telemetria.freios
avionica.telemetria.navegacao
avionica.telemetria.radar
avionica.telemetria.voo
avionica.telemetria.waic
avionica.comandos
```

### 2. Monitorar mensagens chegando em tempo real

```powershell
# Lê mensagens do tópico de voo em tempo real (CTRL+C para parar)
docker exec -it avionica_kafka /opt/kafka/bin/kafka-console-consumer.sh `
  --bootstrap-server localhost:9092 `
  --topic avionica.telemetria.voo `
  --from-beginning
```

Saída esperada (enquanto os sensores Python estão rodando):
```json
{"dados": {"combustivel_pct": 87.5, "altitude_ft": 34950, "velocidade_mach": 0.802}, "_mqtt_topic": "avionica/sensores/voo", "_kafka_sent_at": "2026-05-27T20:00:01Z"}
{"dados": {"combustivel_pct": 87.49, "altitude_ft": 35010, "velocidade_mach": 0.801}, "_mqtt_topic": "avionica/sensores/voo", "_kafka_sent_at": "2026-05-27T20:00:02Z"}
```

### 3. Ver status dos consumer groups

```powershell
# Lista os grupos e seu atraso (lag) em relação ao producer
docker exec -it avionica_kafka /opt/kafka/bin/kafka-consumer-groups.sh `
  --bootstrap-server localhost:9092 `
  --describe `
  --group gateway-persistence
```

Saída (LAG = 0 significa que o consumer está em dia):
```
GROUP               TOPIC                    PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
gateway-persistence avionica.telemetria.voo  0          1523            1523            0
gateway-persistence avionica.telemetria.voo  1          1498            1498            0
gateway-persistence avionica.telemetria.voo  2          1501            1501            0
```

---

## ⚠️ Pontos de Atenção

| Item | Detalhe |
|---|---|
| **`acks=all` em produção** | Garante durabilidade máxima. Em dev pode usar `acks=1` para mais velocidade |
| **`enable.auto.commit=false`** | Essencial. Se o banco falhar no meio do processamento, a mensagem é reprocessada. Com auto-commit, seria perdida |
| **`groupId` é a identidade do consumer** | Dois consumers com o mesmo groupId dividem as partições (load balance). Com groupIds diferentes, cada um lê tudo (fan-out) |
| **Partições = paralelismo máximo** | `avionica.telemetria.voo` tem 3 partições → máximo de 3 consumers em paralelo simultâneo |
| **Retenção de mensagens** | Por padrão o Kafka retém mensagens por 7 dias. Configure `log.retention.hours` no docker-compose para o seu caso |
| **Não substitui o banco** | Kafka não é banco de dados. Use-o como canal de transporte; o PostgreSQL continua sendo o armazenamento definitivo |
