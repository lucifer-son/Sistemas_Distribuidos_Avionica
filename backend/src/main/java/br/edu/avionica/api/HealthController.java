package br.edu.avionica.api;

import java.time.Instant;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class HealthController {
    private final String kafkaBootstrapServers;

    public HealthController(@Value("${app.kafka.bootstrap-servers}") String kafkaBootstrapServers) {
        this.kafkaBootstrapServers = kafkaBootstrapServers;
    }

    @GetMapping("/health")
    public Map<String, Object> health() {
        return Map.of(
            "status", "UP",
            "service", "backend-gateway",
            "timestamp", Instant.now().toString()
        );
    }

    @GetMapping("/modules")
    public List<Map<String, Object>> modules() {
        return List.of(
            module("frontend", "Vue.js", "PLANNED"),
            module("backend-gateway", "Spring Boot", "UP"),
            module("postgres", "PostgreSQL", "INFRASTRUCTURE"),
            module("kafka", "Apache Kafka", "INFRASTRUCTURE", kafkaBootstrapServers),
            module("mqtt-broker", "Eclipse Mosquitto", "TEMPORARY_INFRASTRUCTURE"),
            module("fms-api", "Python", "PLANNED"),
            module("sensor-flight", "Python", "PLANNED"),
            module("sensor-brake", "Python", "PLANNED"),
            module("radar", "Python", "PLANNED"),
            module("navigation-computer", "Python", "PLANNED"),
            module("automation-computer", "Python", "PLANNED"),
            module("waic-leader", "Python", "PLANNED")
        );
    }

    private Map<String, Object> module(String name, String technology, String status) {
        return Map.of(
            "name", name,
            "technology", technology,
            "status", status
        );
    }

    private Map<String, Object> module(String name, String technology, String status, String details) {
        return Map.of(
            "name", name,
            "technology", technology,
            "status", status,
            "details", details
        );
    }
}
