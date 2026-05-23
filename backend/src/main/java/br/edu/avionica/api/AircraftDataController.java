package br.edu.avionica.api;

import br.edu.avionica.telemetry.AircraftDataSnapshot;
import br.edu.avionica.telemetry.AircraftTelemetryService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/aircraft-data")
public class AircraftDataController {
    private final AircraftTelemetryService telemetryService;

    public AircraftDataController(AircraftTelemetryService telemetryService) {
        this.telemetryService = telemetryService;
    }

    @GetMapping
    public AircraftDataSnapshot latest() {
        return telemetryService.snapshot();
    }
}
