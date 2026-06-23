package avionica.route.model;

import lombok.Builder;

@Builder
public record Route(
    String callsign,
    String icaoOrigem,
    String icaoDestino,
    String rotaTexto,
    Double distanciaNm,
    Integer etaMinutos,
    Boolean ativa
) {}
