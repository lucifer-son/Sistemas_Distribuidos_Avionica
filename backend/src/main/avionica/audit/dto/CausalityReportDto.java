package avionica.audit.dto;

import lombok.Builder;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

@Builder
public record CausalityReportDto(
    boolean success,
    OffsetDateTime timestamp,
    Map<String, Object> metricasGlobais,
    List<SensorAuditDto> sensores
) {
}
