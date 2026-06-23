package avionica.lamport.model;

import lombok.Builder;
import java.time.Instant;

@Builder
public record TelemetriaOrdenada(
    String topicoKafka,
    String sensorOrigem,
    long logicalClock,
    String payloadJson,
    String callsign,
    Instant recebidoEm
) {
}
