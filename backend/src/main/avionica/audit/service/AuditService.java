package avionica.audit.service;

import avionica.audit.dto.CausalityReportDto;
import avionica.audit.dto.SensorAuditDto;
import avionica.audit.dto.TableDataDto;
import avionica.audit.dto.TableInfoDto;
import avionica.audit.model.SensorAudit;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.rowset.SqlRowSet;
import org.springframework.jdbc.support.rowset.SqlRowSetMetaData;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.OffsetDateTime;
import java.util.*;

@Service
public class AuditService {

    private final JdbcTemplate jdbc;

    private static class TableMetadata {
        final String displayName;
        final String timeCol;

        TableMetadata(String displayName, String timeCol) {
            this.displayName = displayName;
            this.timeCol = timeCol;
        }
    }

    private static final Map<String, TableMetadata> TABLE_METADATA = Map.ofEntries(
        Map.entry("telemetria_voo", new TableMetadata("Telemetria de Voo", "recebido_em")),
        Map.entry("telemetria_freios", new TableMetadata("Telemetria de Freios", "recebido_em")),
        Map.entry("telemetria_radar", new TableMetadata("Telemetria de Radar", "recebido_em")),
        Map.entry("telemetria_waic", new TableMetadata("Telemetria WAIC", "recebido_em")),
        Map.entry("telemetria_navegacao", new TableMetadata("Computador de Navegação", "recebido_em")),
        Map.entry("rotas_fms", new TableMetadata("Rotas do FMS", "registrado_em")),
        Map.entry("alertas", new TableMetadata("Alertas e Falhas", "registrado_em")),
        Map.entry("eventos_anti_ice", new TableMetadata("Eventos de Anti-Ice", "registrado_em")),
        Map.entry("mensagens_barramento", new TableMetadata("Log do Barramento MQTT", "recebido_em")),
        Map.entry("aeronaves", new TableMetadata("Aeronaves Cadastradas", "ultima_atualizacao")),
        Map.entry("telemetria_ordenada", new TableMetadata("Telemetria Ordenada (Lamport)", "recebido_em"))
    );

    public AuditService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    /**
     * Lista todas as tabelas aviônicas cadastradas com seu respectivo volume de registros.
     */
    public List<TableInfoDto> listTables() {
        List<TableInfoDto> list = new ArrayList<>();
        List<String> sortedKeys = new ArrayList<>(TABLE_METADATA.keySet());
        Collections.sort(sortedKeys);

        for (String tableName : sortedKeys) {
            TableMetadata meta = TABLE_METADATA.get(tableName);
            try {
                Long count = jdbc.queryForObject("SELECT COUNT(*) FROM " + tableName, Long.class);
                list.add(TableInfoDto.builder()
                    .id(tableName)
                    .displayName(meta.displayName)
                    .rowCount(count != null ? count : 0L)
                    .build());
            } catch (Exception e) {
                list.add(TableInfoDto.builder()
                    .id(tableName)
                    .displayName(meta.displayName)
                    .rowCount(0L)
                    .build());
            }
        }
        return list;
    }

    /**
     * Retorna os registros de uma tabela específica com filtros temporais, busca textual global e limites.
     */
    public TableDataDto getTableData(String tableName, String search, int limit, String startDate, String endDate) {
        TableMetadata meta = TABLE_METADATA.get(tableName);
        if (meta == null) {
            throw new IllegalArgumentException("Tabela não encontrada no sistema de auditoria: " + tableName);
        }

        String timeCol = meta.timeCol;
        int parsedLimit = Math.min(Math.max(1, limit), 500);

        StringBuilder queryBuilder = new StringBuilder("SELECT * FROM ").append(tableName);
        List<Object> queryParams = new ArrayList<>();
        List<String> conditions = new ArrayList<>();

        if (startDate != null && !startDate.isBlank()) {
            try {
                OffsetDateTime start = OffsetDateTime.parse(startDate);
                queryParams.add(start);
                conditions.add(timeCol + " >= ?");
            } catch (Exception e) {
                try {
                    Instant start = Instant.parse(startDate);
                    queryParams.add(start);
                    conditions.add(timeCol + " >= ?");
                } catch (Exception e2) {
                    throw new IllegalArgumentException("Formato de data inválido para startDate: " + startDate);
                }
            }
        }

        if (endDate != null && !endDate.isBlank()) {
            try {
                OffsetDateTime end = OffsetDateTime.parse(endDate);
                queryParams.add(end);
                conditions.add(timeCol + " <= ?");
            } catch (Exception e) {
                try {
                    Instant end = Instant.parse(endDate);
                    queryParams.add(end);
                    conditions.add(timeCol + " <= ?");
                } catch (Exception e2) {
                    throw new IllegalArgumentException("Formato de data inválido para endDate: " + endDate);
                }
            }
        }

        if (search != null && !search.isBlank()) {
            queryParams.add("%" + search + "%");
            conditions.add("ROW_TO_JSON(" + tableName + ")::text ILIKE ?");
        }

        if (!conditions.isEmpty()) {
            queryBuilder.append(" WHERE ").append(String.join(" AND ", conditions));
        }

        queryBuilder.append(" ORDER BY ").append(timeCol).append(" DESC");
        queryBuilder.append(" LIMIT ?");
        queryParams.add(parsedLimit);

        try {
            SqlRowSet rowSet = jdbc.queryForRowSet(queryBuilder.toString(), queryParams.toArray());
            SqlRowSetMetaData metaData = rowSet.getMetaData();
            int columnCount = metaData.getColumnCount();
            List<String> columns = new ArrayList<>();
            for (int i = 1; i <= columnCount; i++) {
                columns.add(metaData.getColumnName(i));
            }

            List<Map<String, Object>> rows = new ArrayList<>();
            while (rowSet.next()) {
                Map<String, Object> row = new LinkedHashMap<>();
                for (String col : columns) {
                    row.put(col, rowSet.getObject(col));
                }
                rows.add(row);
            }

            return TableDataDto.builder()
                .success(true)
                .tableName(tableName)
                .columns(columns)
                .rows(rows)
                .build();
        } catch (Exception e) {
            throw new RuntimeException("Erro ao consultar dados da tabela " + tableName + ": " + e.getMessage());
        }
    }

    /**
     * Esvazia (TRUNCATE) uma tabela específica para fins de simulação e testes.
     */
    public void truncateTable(String tableName) {
        if (!TABLE_METADATA.containsKey(tableName)) {
            throw new IllegalArgumentException("Tabela não encontrada ou acesso não autorizado: " + tableName);
        }
        try {
            jdbc.execute("TRUNCATE TABLE " + tableName + " RESTART IDENTITY CASCADE");
        } catch (Exception e) {
            throw new RuntimeException("Erro ao limpar dados da tabela " + tableName + ": " + e.getMessage());
        }
    }

    /**
     * Executa a auditoria de causalidade e integridade usando o Algoritmo de Lamport.
     */
    public CausalityReportDto auditCausality() {
        try {
            String query = "SELECT sensor_origem, logical_clock, recebido_em " +
                           "FROM telemetria_ordenada " +
                           "ORDER BY sensor_origem, recebido_em ASC";
            SqlRowSet rowSet = jdbc.queryForRowSet(query);

            Map<String, SensorAudit> auditMap = new LinkedHashMap<>();
            long totalAnomalias = 0;
            long totalPerdas = 0;

            while (rowSet.next()) {
                String sensorOrigem = rowSet.getString("sensor_origem");
                long clock = rowSet.getLong("logical_clock");

                OffsetDateTime recebidoEm;
                Object recebidoObj = rowSet.getObject("recebido_em");
                if (recebidoObj instanceof OffsetDateTime odt) {
                    recebidoEm = odt;
                } else if (recebidoObj instanceof java.sql.Timestamp ts) {
                    recebidoEm = ts.toInstant().atOffset(OffsetDateTime.now().getOffset());
                } else if (recebidoObj instanceof Instant inst) {
                    recebidoEm = inst.atOffset(OffsetDateTime.now().getOffset());
                } else {
                    recebidoEm = OffsetDateTime.now();
                }

                long timeMs = recebidoEm.toInstant().toEpochMilli();

                if (!auditMap.containsKey(sensorOrigem)) {
                    auditMap.put(sensorOrigem, new SensorAudit(sensorOrigem, clock, timeMs));
                } else {
                    SensorAudit sensorData = auditMap.get(sensorOrigem);
                    sensorData.incrementMensagens();

                    if (clock <= sensorData.getUltimoClock()) {
                        sensorData.incrementAnomalias();
                        totalAnomalias++;
                    }

                    long gap = clock - sensorData.getUltimoClock();
                    if (gap > 1) {
                        long perdidos = gap - 1;
                        sensorData.addMensagensPerdidas(perdidos);
                        totalPerdas += perdidos;
                    }

                    sensorData.setUltimoClock(clock);
                    sensorData.setUltimoTime(timeMs);
                }
            }

            // Mapeia o modelo mutável para DTOs imutáveis (records com Builder)
            List<SensorAuditDto> sensores = new ArrayList<>();
            for (SensorAudit model : auditMap.values()) {
                sensores.add(SensorAuditDto.builder()
                    .sensor(model.getSensor())
                    .totalMensagens(model.getTotalMensagens())
                    .ultimoClock(model.getUltimoClock())
                    .ultimoTime(model.getUltimoTime())
                    .anomaliasCausais(model.getAnomaliasCausais())
                    .mensagensPerdidas(model.getMensagensPerdidas())
                    .build());
            }

            Map<String, Object> metricasGlobais = Map.of(
                "totalSensoresAuditados", sensores.size(),
                "totalAnomaliasCausais", totalAnomalias,
                "totalMensagensPerdidas", totalPerdas,
                "statusIntegridade", (totalAnomalias == 0 && totalPerdas == 0) ? "CONCORDANTE" : "DEGRADADO"
            );

            return CausalityReportDto.builder()
                .success(true)
                .timestamp(OffsetDateTime.now())
                .metricasGlobais(metricasGlobais)
                .sensores(sensores)
                .build();
        } catch (Exception e) {
            throw new RuntimeException("Erro ao processar auditoria causal: " + e.getMessage());
        }
    }
}
