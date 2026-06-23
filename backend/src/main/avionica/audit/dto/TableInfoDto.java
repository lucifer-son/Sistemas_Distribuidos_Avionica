package avionica.audit.dto;

import lombok.Builder;

@Builder
public record TableInfoDto(
    String id,
    String displayName,
    long rowCount
) {
}
