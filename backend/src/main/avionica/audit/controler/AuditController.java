package avionica.audit.controler;

import avionica.audit.dto.CausalityReportDto;
import avionica.audit.dto.TableDataDto;
import avionica.audit.dto.TableInfoDto;
import avionica.audit.service.AuditService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/audit")
public class AuditController {

    private final AuditService auditService;

    public AuditController(AuditService auditService) {
        this.auditService = auditService;
    }

    /**
     * Endpoint para listar as tabelas aviônicas e seus respectivos tamanhos.
     */
    @GetMapping("/tables")
    public ResponseEntity<?> getTables() {
        try {
            List<TableInfoDto> tables = auditService.listTables();
            return ResponseEntity.ok(Map.of("success", true, "tables", tables));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("success", false, "error", e.getMessage()));
        }
    }

    /**
     * Endpoint para consultar dados de uma tabela específica, aplicando filtros e limite.
     */
    @GetMapping("/tables/{tableName}")
    public ResponseEntity<?> getTableData(
            @PathVariable String tableName,
            @RequestParam(required = false) String search,
            @RequestParam(defaultValue = "50") int limit,
            @RequestParam(required = false) String startDate,
            @RequestParam(required = false) String endDate
    ) {
        try {
            TableDataDto data = auditService.getTableData(tableName, search, limit, startDate, endDate);
            return ResponseEntity.ok(data);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("success", false, "error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("success", false, "error", e.getMessage()));
        }
    }

    /**
     * Endpoint administrativo para limpar (TRUNCATE) uma tabela específica.
     */
    @PostMapping("/tables/{tableName}/truncate")
    public ResponseEntity<?> truncateTable(@PathVariable String tableName) {
        try {
            auditService.truncateTable(tableName);
            return ResponseEntity.ok(Map.of("success", true, "message", "Tabela " + tableName + " limpa com sucesso"));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("success", false, "error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("success", false, "error", e.getMessage()));
        }
    }

    /**
     * Endpoint para rodar a auditoria de causalidade (Lamport) em tempo real.
     */
    @GetMapping("/causality")
    public ResponseEntity<?> getCausalityReport() {
        try {
            CausalityReportDto report = auditService.auditCausality();
            return ResponseEntity.ok(report);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("success", false, "error", e.getMessage()));
        }
    }
}
