package avionica.lamport.service;

import avionica.lamport.model.TelemetriaOrdenada;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.atomic.AtomicLong;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class LamportConsumerService {
    private static final Logger logger = LoggerFactory.getLogger(LamportConsumerService.class);

    private final AtomicLong localClock = new AtomicLong(0);
    private final JdbcTemplate jdbc;

    public LamportConsumerService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    /**
     * Processa uma mensagem recebida do Kafka.
     * Regra: Clock_local = max(Clock_local, Clock_mensagem) + 1.
     */
    public void processar(String topico, String mensagemJson) {
        try {
            String payloadJson = normalizarJson(mensagemJson);
            JSONObject json = new JSONObject(payloadJson);
            Map<String, Object> payload = json.toMap();

            long clockMensagem = extrairLong(
                payload,
                0L,
                "logical_clock",
                "logicalClock",
                "lamport_clock",
                "lamportClock"
            );

            long clockConsolidado = localClock.updateAndGet(
                clockLocal -> Math.max(clockLocal, clockMensagem) + 1
            );

            String sensorOrigem = extrairTexto(
                payload,
                "desconhecido",
                "origem",
                "module_id",
                "moduleId",
                "source",
                "node_id",
                "nodeId"
            );

            String callsign = extrairTexto(
                payload,
                null,
                "callsign",
                "callSign",
                "aircraft",
                "aircraft_id"
            );

            TelemetriaOrdenada entrada = new TelemetriaOrdenada(
                topico,
                sensorOrigem,
                clockConsolidado,
                payloadJson,
                callsign,
                Instant.now()
            );

            gravar(entrada);

            logger.info(
                "[Lamport] topico={} | clock_mensagem={} | clock_local={} | origem={}",
                topico,
                clockMensagem,
                clockConsolidado,
                sensorOrigem
            );
        } catch (Exception e) {
            logger.warn("[Lamport] Erro ao processar mensagem do tópico {}: {}", topico, e.getMessage());
        }
    }

    private void gravar(TelemetriaOrdenada t) {
        jdbc.update(
                "INSERT INTO telemetria_ordenada " +
                        "(topico_kafka, sensor_origem, logical_clock, payload_json, callsign) " +
                        "VALUES (?, ?, ?, CAST(? AS jsonb), ?)",
                t.topicoKafka(),
                t.sensorOrigem(),
                t.logicalClock(),
                t.payloadJson(),
                t.callsign()
        );
    }

    public long getLocalClock() {
        return localClock.get();
    }

    public Map<String, Object> estadoLamport() {
        return Map.of(
            "local_clock", localClock.get(),
            "timestamp", Instant.now().toString()
        );
    }

    private String normalizarJson(String mensagemJson) {
        if (mensagemJson == null || mensagemJson.isBlank()) {
            return new JSONObject(Map.of("raw", "")).toString();
        }

        try {
            return new JSONObject(mensagemJson).toString();
        } catch (Exception e) {
            return new JSONObject(Map.of("raw", mensagemJson)).toString();
        }
    }

    private long extrairLong(Object atual, long padrao, String... chaves) {
        if (atual instanceof Map<?, ?> mapa) {
            for (String chave : chaves) {
                Object valor = mapa.get(chave);
                Long numero = converterLong(valor);
                if (numero != null) {
                    return numero;
                }
            }

            for (Object valor : mapa.values()) {
                long encontrado = extrairLong(valor, Long.MIN_VALUE, chaves);
                if (encontrado != Long.MIN_VALUE) {
                    return encontrado;
                }
            }
        }

        return padrao;
    }

    private Long converterLong(Object valor) {
        if (valor instanceof Number numero) {
            return numero.longValue();
        }

        if (valor instanceof String texto) {
            try {
                return Long.parseLong(texto.trim());
            } catch (NumberFormatException ignored) {
                return null;
            }
        }

        return null;
    }

    private String extrairTexto(Object atual, String padrao, String... chaves) {
        if (atual instanceof Map<?, ?> mapa) {
            for (String chave : chaves) {
                Object valor = mapa.get(chave);
                if (valor instanceof String texto && !texto.isBlank()) {
                    return texto;
                }

                if (valor instanceof Number numero) {
                    return String.valueOf(numero);
                }
            }

            for (Object valor : mapa.values()) {
                String encontrado = extrairTexto(valor, null, chaves);
                if (encontrado != null && !encontrado.isBlank()) {
                    return encontrado;
                }
            }
        }

        return padrao;
    }
}
