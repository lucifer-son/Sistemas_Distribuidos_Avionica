package avionica.telemetry.model;

import lombok.Builder;
import java.time.Instant;
import java.util.Map;

@Builder
public record AircraftMessage(
    String topic,
    Instant receivedAt,
    Map<String, Object> payload
) {
}
