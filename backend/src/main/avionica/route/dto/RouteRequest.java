package avionica.route.dto;

import lombok.Builder;

@Builder
public record RouteRequest(
    String callsign,
    String origin,
    String destination
) {}
