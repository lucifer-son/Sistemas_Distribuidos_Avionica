package avionica.lamport.dto;

import lombok.Builder;

@Builder
public record TelemetriaPayloadDto(
    String origem,
    long logical_clock,
    String callsign,
    Object dados
) {
}
