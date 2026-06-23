package avionica.aircraft.dto;

import lombok.Builder;

@Builder
public record AircraftRequest(
    String callsign,
    String modelo,
    Integer capacidade_combustivel,
    Integer velocidade_cruzeiro
) {}
