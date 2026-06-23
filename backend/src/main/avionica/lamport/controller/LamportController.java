package avionica.lamport.controller;

import avionica.lamport.dto.TelemetriaOrdenadaDto;
import avionica.lamport.service.LamportConsumerService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class LamportController {
    private final LamportConsumerService lamportService;

    public LamportController(LamportConsumerService lamportService) {
        this.lamportService = lamportService;
    }

    @GetMapping("/lamport-clock")
    public Map<String, Object> getLamportClock() {
        return lamportService.estadoLamport();
    }

    @GetMapping("/telemetria-ordenada")
    public List<TelemetriaOrdenadaDto> listarTelemetriaOrdenada(@RequestParam(defaultValue = "50") int limite) {
        return lamportService.listarTelemetriaOrdenada(limite);
    }
}
