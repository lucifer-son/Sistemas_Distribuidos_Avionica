package br.edu.avionica.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

@Component
public class StartupLogger {
    private static final Logger logger = LoggerFactory.getLogger(StartupLogger.class);

    @EventListener(ApplicationReadyEvent.class)
    public void onApplicationReady() {
        logger.info("Backend Gateway pronto em http://localhost:8080");
        logger.info("Health check disponivel em /api/health");
        logger.info("Lista de modulos disponivel em /api/modules");
    }
}
