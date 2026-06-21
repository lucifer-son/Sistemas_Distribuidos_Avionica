package avionica.kafka;

import avionica.lamport.service.LamportConsumerService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.stereotype.Component;

@Component
public class TelemetriaKafkaConsumer {
    private static final Logger logger = LoggerFactory.getLogger(TelemetriaKafkaConsumer.class);

    private final LamportConsumerService lamportService;

    public TelemetriaKafkaConsumer(LamportConsumerService lamportService) {
        this.lamportService = lamportService;
    }

    /**
     * Escuta tópicos de telemetria e delega ao serviço de Lamport antes da persistência.
     */
    @KafkaListener(
        topics = {
            "avionica.telemetry.brakes",
            "avionica.telemetry.flight",
            "avionica.telemetry.radar",
            "avionica.telemetry.motor.consolidated",
            "avionica.navigation",
            "avionica.telemetry.waic"
        },
        groupId = "${app.lamport.group-id:lamport-consumer}"
    )
    public void consumir(
        String mensagem,
        @Header(KafkaHeaders.RECEIVED_TOPIC) String topico
    ) {
        logger.debug("[Kafka] Mensagem recebida no tópico {} para persistência Lamport", topico);
        lamportService.processar(topico, mensagem);
    }
}
