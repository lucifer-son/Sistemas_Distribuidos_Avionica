package avionica.api;

import avionica.lamport.dto.TelemetriaOrdenadaDto;
import avionica.lamport.service.LamportConsumerService;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class LamportController {
    private final JdbcTemplate jdbc;
    private final LamportConsumerService lamportService;

    public LamportController(JdbcTemplate jdbc, LamportConsumerService lamportService) {
        this.jdbc = jdbc;
        this.lamportService = lamportService;
    }

    @GetMapping("/lamport-clock")
    public Map<String, Object> getLamportClock() {
        return lamportService.estadoLamport();
    }

    @GetMapping("/telemetria-ordenada")
    public List<TelemetriaOrdenadaDto> listarTelemetriaOrdenada(@RequestParam(defaultValue = "50") int limite) {
        int limiteSeguro = Math.max(1, Math.min(limite, 200));

        return jdbc.query(
            "SELECT id, recebido_em, topico_kafka, sensor_origem, logical_clock, payload_json::text AS payload_json, callsign " +
            "FROM telemetria_ordenada " +
            "ORDER BY logical_clock DESC, recebido_em DESC " +
            "LIMIT ?",
            this::mapear,
            limiteSeguro
        );
    }

    private TelemetriaOrdenadaDto mapear(ResultSet rs, int rowNum) throws SQLException {
        return new TelemetriaOrdenadaDto(
            rs.getLong("id"),
            rs.getObject("recebido_em", OffsetDateTime.class),
            rs.getString("topico_kafka"),
            rs.getString("sensor_origem"),
            rs.getLong("logical_clock"),
            rs.getString("payload_json"),
            rs.getString("callsign")
        );
    }
}
