# CDU-04: Tela do Dashboard

## Definições/Regras

- `Dashboard`: Tela de acompanhamento da simulação em tempo real.
- `SSE/WebSockets`: Tecnologia utilizada para receber dados de telemetria sem necessidade de recarregar a página (polling).
- A URL da tela sera `/simulacao/dashboard/{id_aeronave}_{id_decolagem}_{id_destino}`.

## Fluxo principal

1. Após confirmar a rota no [cdu-03](cdu-03.md), o usuário é redirecionado para a tela de Dashboard.

2. O Dashboard exibirá os seguintes componentes visuais em tempo real:
    - **Painel de Altitude e Velocidade**: Indicadores gráficos simulando fitas de altitude (pés) e velocidade (nós/Mach) da aeronave.
    - **Horizonte Artificial (Atitude)**: Representação visual do Pitch (arfagem), Roll (rolagem) e Yaw (proa) da aeronave.
    - **Status de Combustível**: Nível atual do tanque e taxa de consumo estimado.
    - **Status dos Freios**: Pressão hidráulica do sistema de freio.
    - **Radar Climático**: Exibição das condições do tempo e velocidade do vento.
    - **Crew Alerting System (CAS)**: Lista de alertas técnicos e operacionais em tempo real (ex: avisos de gelo, falhas de sensores).
    - **Painel de Rota e ETA**: Exibição da origem, destino, distância restante (NM) e tempo estimado de chegada (ETA).

3. O sistema receberá os dados de telemetria em tempo real através de conexão ativa com o backend (SSE ou WebSockets), que por sua vez consome do Kafka.

4. O usuário poderá clicar no botão **"Encerrar Simulação"** para interromper o voo simulado. O sistema desconectará do fluxo de telemetria e redirecionará o usuário para a tela de `/simulacao`.
