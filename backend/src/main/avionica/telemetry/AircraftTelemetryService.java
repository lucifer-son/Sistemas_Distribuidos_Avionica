package avionica.telemetry;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Deque;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallbackExtended;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class AircraftTelemetryService implements MqttCallbackExtended {
    private static final Logger logger = LoggerFactory.getLogger(AircraftTelemetryService.class);

    private final String brokerUrl;
    private final String topicFilter;
    private final Map<String, AircraftMessage> latestByTopic = new ConcurrentHashMap<>();
    private final Deque<AircraftMessage> recentMessages = new ArrayDeque<>();
    private MqttClient client;

    public AircraftTelemetryService(
        @Value("${app.mqtt.broker-url}") String brokerUrl,
        @Value("${app.mqtt.topic-filter}") String topicFilter
    ) {
        this.brokerUrl = brokerUrl;
        this.topicFilter = topicFilter;
    }

    @PostConstruct
    public void start() {
        try {
            client = new MqttClient(brokerUrl, "backend-gateway-" + UUID.randomUUID());
            client.setCallback(this);

            MqttConnectOptions options = new MqttConnectOptions();
            options.setAutomaticReconnect(true);
            options.setCleanSession(true);
            options.setConnectionTimeout(5);

            client.connect(options);
            client.subscribe(topicFilter);
            logger.info("Assinando telemetria MQTT em {} no topico {}", brokerUrl, topicFilter);
        } catch (MqttException exception) {
            logger.warn("Nao foi possivel conectar ao MQTT em {}. A API continuara ativa sem telemetria ao vivo.", brokerUrl);
        }
    }

    @PreDestroy
    public void stop() throws MqttException {
        if (client != null && client.isConnected()) {
            client.disconnect();
        }
    }

    public AircraftDataSnapshot snapshot() {
        List<AircraftMessage> messages;

        synchronized (recentMessages) {
            messages = new ArrayList<>(recentMessages);
        }

        Collections.reverse(messages);

        return new AircraftDataSnapshot(
            Instant.now(),
            dataFrom("avionica/sensores/voo"),
            dataFrom("avionica/sensores/freios"),
            dataFrom("avionica/radar"),
            dataFrom("avionica/fms/dados"),
            dataFrom("avionica/navegacao"),
            dataFrom("avionica/sensores/waic"),
            payloadFrom("avionica/sistemas/anti_ice"),
            payloadFrom("avionica/comandos/falhas"),
            messages
        );
    }

    @Override
    public void connectComplete(boolean reconnect, String serverURI) {
        try {
            client.subscribe(topicFilter);
            logger.info("Conectado ao MQTT {}. Topico ativo: {}", serverURI, topicFilter);
        } catch (MqttException exception) {
            logger.warn("Falha ao reassinar topico MQTT {}", topicFilter);
        }
    }

    @Override
    public void connectionLost(Throwable cause) {
        logger.warn("Conexao MQTT perdida. Tentando reconectar automaticamente.");
    }

    @Override
    public void messageArrived(String topic, MqttMessage mqttMessage) {
        Map<String, Object> payload = parsePayload(mqttMessage);
        AircraftMessage message = new AircraftMessage(topic, Instant.now(), payload);

        latestByTopic.put(topic, message);

        synchronized (recentMessages) {
            recentMessages.addLast(message);
            while (recentMessages.size() > 30) {
                recentMessages.removeFirst();
            }
        }
    }

    @Override
    public void deliveryComplete(IMqttDeliveryToken token) {
    }

    private Map<String, Object> dataFrom(String topic) {
        Map<String, Object> payload = payloadFrom(topic);
        Object data = payload.get("dados");

        if (data instanceof Map<?, ?> map) {
            return normalizeMap(map);
        }

        return payload;
    }

    private Map<String, Object> payloadFrom(String topic) {
        AircraftMessage message = latestByTopic.get(topic);

        if (message == null) {
            return Map.of();
        }

        return message.payload();
    }

    private Map<String, Object> parsePayload(MqttMessage mqttMessage) {
        String rawPayload = new String(mqttMessage.getPayload(), StandardCharsets.UTF_8);

        try {
            return new JSONObject(rawPayload).toMap();
        } catch (Exception exception) {
            return Map.of("raw", rawPayload);
        }
    }

    private Map<String, Object> normalizeMap(Map<?, ?> source) {
        Map<String, Object> normalized = new LinkedHashMap<>();

        source.forEach((key, value) -> normalized.put(String.valueOf(key), value));
        return normalized;
    }
}
