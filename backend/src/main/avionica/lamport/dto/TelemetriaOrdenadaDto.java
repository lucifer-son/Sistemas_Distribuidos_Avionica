package avionica.lamport.dto;

import java.time.OffsetDateTime;

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
