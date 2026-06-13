# CDU-01: Visão Geral dos Tópicos e Estatísticas do Kafka

## Definições/Regras

- `Monitor de Tópicos`: Tela inicial que exibe todos os tópicos criados no broker Kafka.
- A aplicação rodará em `http://localhost:9000`.

## Fluxo principal

1. O usuário acessa a página inicial do monitor do Kafka em `http://localhost:9000`.

2. A tela exibirá uma lista de tópicos ativos, incluindo:
    - Nome do tópico (ex: `avionica.telemetry.speed`, `avionica.route.requested`).
    - Quantidade total de mensagens recebidas desde o início do broker.
    - Status do tópico (Ativo, Sem Atividade).
    - Lista de grupos de consumidores conectados a cada tópico (ex: `backend-gateway`, `alert-service`).

3. Se o usuário clicar no nome de um tópico da lista, o sistema redirecionará para a tela de monitoramento de mensagens em tempo real daquele tópico em `http://localhost:9000/topico/{nome_do_topico}`.
