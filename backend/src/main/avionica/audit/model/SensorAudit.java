package avionica.audit.model;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class SensorAudit {
    private String sensor;
    private long totalMensagens;
    private long ultimoClock;
    private long ultimoTime;
    private long anomaliasCausais;
    private long mensagensPerdidas;

    public SensorAudit(String sensor, long clock, long time) {
        this.sensor = sensor;
        this.totalMensagens = 1;
        this.ultimoClock = clock;
        this.ultimoTime = time;
        this.anomaliasCausais = 0;
        this.mensagensPerdidas = 0;
    }

    public void incrementMensagens() {
        this.totalMensagens++;
    }

    public void incrementAnomalias() {
        this.anomaliasCausais++;
    }

    public void addMensagensPerdidas(long count) {
        this.mensagensPerdidas += count;
    }
}
