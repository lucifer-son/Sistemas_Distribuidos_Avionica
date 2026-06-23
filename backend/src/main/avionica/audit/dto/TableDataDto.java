package avionica.audit.dto;

import lombok.Builder;
import java.util.List;
import java.util.Map;

@Builder
public record TableDataDto(
    boolean success,
    String tableName,
    List<String> columns,
    List<Map<String, Object>> rows
) {
}
