package avionica.kafka.consumer;

import avionica.lamport.model.TelemetriaOrdenada;
import avionica.lamport.repository.TelemetriaOrdenadaRepository;
import avionica.telemetry.service.AircraftTelemetryService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.concurrent.atomic.AtomicLong;

@Component
public class TelemetriaKafkaConsumer {

    private static final Logger log = LoggerFactory.getLogger(TelemetriaKafkaConsumer.class);

    private final TelemetriaOrdenadaRepository repository;
    private final AircraftTelemetryService telemetryService;
    private final ObjectMapper mapper;
    private final AtomicLong logicalClockLocal = new AtomicLong(0);

    public TelemetriaKafkaConsumer(TelemetriaOrdenadaRepository repository,
                                   AircraftTelemetryService telemetryService,
                                   ObjectMapper mapper) {
        this.repository = repository;
        this.telemetryService = telemetryService;
        this.mapper = mapper;
    }

    @KafkaListener(
        topics = {
            "avionica.telemetry.flight",
            "avionica.telemetry.brakes",
            "avionica.telemetry.radar",
            "avionica.telemetry.waic",
            "avionica.navigation"
        },
        groupId = "lamport-ordered-consumer-group"
    )
    public void consumeTelemetry(
            @Payload String payloadStr,
            @Header("kafka_receivedTopic") String topic) {

        if (!telemetryService.isSimulacaoAtiva()) {
            return;
        }

        try {
            var jsonNode = mapper.readTree(payloadStr);

            long clockMensagem = jsonNode.path("logical_clock").asLong(0);

            long clockLocalAtualizado =
                    logicalClockLocal.updateAndGet(local -> Math.max(local, clockMensagem) + 1);

            String callsign = jsonNode.path("callsign").asText(null);
            if (callsign == null) {
                callsign = jsonNode.path("payload").path("callsign").asText("DESCONHECIDO");
            }

            TelemetriaOrdenada record = TelemetriaOrdenada.builder()
                    .topicoKafka(topic)
                    .sensorOrigem(jsonNode.path("source").asText("UNKNOWN"))
                    .logicalClock(clockLocalAtualizado)
                    .payloadJson(payloadStr)
                    .callsign(callsign)
                    .recebidoEm(Instant.now())
                    .build();

            repository.save(record);

            log.info("[Lamport] topico={} | clock_mensagem={} | clock_local={} | origem={}",
                    topic, clockMensagem, clockLocalAtualizado, record.getSensorOrigem());

        } catch (Exception e) {
            log.error("Erro ao ordenar/persistir telemetria: {}", e.getMessage());
        }
    }
}