package avionica.aircraft.model;

import lombok.Builder;
import java.time.Instant;

@Builder
public record Aircraft(
    String callsign,
    String modelo,
    Integer capacidadeCombustivel,
    Integer velocidadeCruzeiro,
    String status,
    Instant ultimaAtualizacao
) {}
