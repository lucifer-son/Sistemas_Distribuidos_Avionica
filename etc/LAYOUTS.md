# Layouts do Front-End - Aviônica Distribuída (Glass Cockpit Edition)

Este diretório contém as especificações visuais para o desenvolvimento do front-end do sistema de aviônica distribuída. Todos os layouts seguem uma estética profissional de **Glass Cockpit**, utilizando um tema escuro de alto contraste, tipografia monoespaçada e indicadores de precisão.

## Arquivos de Layout (SVG)

1.  **[PFD - Dashboard Principal](layouts/dashboard.svg)**: Primary Flight Display. Contém o horizonte artificial, fitas de velocidade (Airspeed) e altitude, indicadores de proa (Heading) e status de sistemas críticos (Motores, Combustível, Trem de Pouso).
2.  **[MFD - FMS & Navegação](layouts/fms.svg)**: Multi-Function Display. Focado no gerenciamento de voo, com planejamento de rota, mapa interativo em arco e histórico de voos.
3.  **[SYS - Status dos Módulos](layouts/status-modulos.svg)**: System Display. Painel de diagnóstico do sistema distribuído, com visualização da topologia do barramento Kafka, monitoramento de latência dos módulos e gráficos de tendência de recursos (CPU e Tráfego).

## Guia de Estilo Profissional

*   **Paleta de Cores**: 
    *   Fundo: `#0A0B0C` (Preto profundo) / `#1C1E20` (Cinza escuro)
    *   Verde Neon: `#00FF41` (Status Normal / Ativo)
    *   Magenta: `#FF00FF` (Traçado de Rota Ativa)
    *   Ciano/Azul: `#00BFFF` (Dados de Navegação / GPS)
    *   Âmbar/Amarelo: `#FFC107` (Alertas de Cuidado / Advisory)
    *   Vermelho: `#DC3545` (Alertas Críticos / Offline)
*   **Tipografia**: Utilizar fontes monoespaçadas (JetBrains Mono, Roboto Mono ou Courier) para manter o alinhamento de dados numéricos.

## Funcionalidades Planejadas

### PFD (Dashboard)
*   Horizonte artificial animado com dados de Pitch/Roll.
*   Fitas deslizantes para Altitude e Velocidade.
*   Crew Alerting System (CAS) na lateral direita para notificações rápidas.

### MFD (FMS)
*   Mapa em modo ARC com bússola.
*   Cálculo de rota via barramento de eventos (Kafka).
*   Console de comando FMS com log de execução.

### SYS (Status)
*   Visualização gráfica da topologia do sistema.
*   Monitoramento de latência fim-a-fim entre os módulos distribuídos.
*   Diagnóstico de infraestrutura (Banco de Dados e Broker de Mensagens).
