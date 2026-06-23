package avionica.timesync.model;

import lombok.Builder;

@Builder
public record TimeSyncResponse(
    long server_time_ns,
    long server_time_ms
) {}
