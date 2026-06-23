package avionica.lamport.dto;

import lombok.Builder;
import java.time.OffsetDateTime;

@Builder
public record TelemetriaOrdenadaDto(
    Long id,
    OffsetDateTime recebidoEm,
    String topicoKafka,
    String sensorOrigem,
    Long logicalClock,
    String payloadJson,
    String callsign
) {
}
