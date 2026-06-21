package avionica.lamport.model;

import java.time.Instant;

/**
 * Representa uma mensagem de telemetria processada pelo relógio lógico de Lamport,
 * pronta para persistência em ordem causal no PostgreSQL.
 */
public record TelemetriaOrdenada(
    String topicoKafka,
    String sensorOrigem,
    long logicalClock,
    String payloadJson,
    String callsign,
    Instant recebidoEm
) {
}
