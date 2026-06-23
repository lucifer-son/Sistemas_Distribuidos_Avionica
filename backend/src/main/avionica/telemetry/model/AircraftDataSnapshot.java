package avionica.telemetry.model;

import lombok.Builder;
import java.time.Instant;
import java.util.List;
import java.util.Map;

@Builder
public record AircraftDataSnapshot(
    Instant updatedAt,
    Map<String, Object> flight,
    Map<String, Object> brakes,
    Map<String, Object> radar,
    Map<String, Object> fms,
    Map<String, Object> navigation,
    Map<String, Object> waic,
    Map<String, Object> antiIce,
    Map<String, Object> alerts,
    List<AircraftMessage> rawMessages
) {
}
