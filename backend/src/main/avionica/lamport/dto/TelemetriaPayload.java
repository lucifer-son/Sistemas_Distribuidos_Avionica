package avionica.lamport.dto;

import lombok.Builder;

@Builder
public record TelemetriaPayload(
    String origem,
    long logical_clock,
    String callsign,
    Object dados
) {
}
