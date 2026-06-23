package avionica.route.dto;

import lombok.Builder;

@Builder
public record RouteResponse(
    String status,
    String callsign,
    String origem,
    String destino,
    String mensagem
) {}
