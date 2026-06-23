package avionica.lamport.model;

import java.time.OffsetDateTime;
import java.time.ZoneOffset;

import org.hibernate.annotations.ColumnTransformer;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "telemetria_ordenada")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TelemetriaOrdenada {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Long id;

    @Column(name = "recebido_em", nullable = false)
    @Builder.Default
    private OffsetDateTime recebidoEm = OffsetDateTime.now(ZoneOffset.UTC);

    @Column(name = "topico_kafka", nullable = false, length = 200)
    private String topicoKafka;

    @Column(name = "sensor_origem", length = 100)
    private String sensorOrigem;

    @Column(name = "logical_clock", nullable = false)
    private Long logicalClock;

    @Column(name = "payload_json", nullable = false, columnDefinition = "jsonb")
    @ColumnTransformer(write = "?::jsonb")
    private String payloadJson;

    @Column(name = "callsign", length = 20)
    private String callsign;

    @PrePersist
    void prePersist() {
        if (recebidoEm == null) {
            recebidoEm = OffsetDateTime.now(ZoneOffset.UTC);
        }
    }
}
