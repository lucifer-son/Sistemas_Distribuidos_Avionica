package avionica.lamport.dto;

/**
 * DTO de referência para o formato esperado nas mensagens Kafka de telemetria.
 * Todos os sensores devem enviar logical_clock para permitir a ordenação Lamport.
 */
public record TelemetriaPayload(
    String origem,
    long logical_clock,
    String callsign,
    Object dados
) {
}
