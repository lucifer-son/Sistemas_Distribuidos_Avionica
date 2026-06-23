package avionica.audit.dto;

import lombok.Builder;

@Builder
public record SensorAuditDto(
    String sensor,
    long totalMensagens,
    long ultimoClock,
    long ultimoTime,
    long anomaliasCausais,
    long mensagensPerdidas
) {
}
