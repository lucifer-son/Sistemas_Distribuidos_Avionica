# CDU-01: Visualização de Tabelas e Registros

## Definições/Regras

- `Visualizador de Banco`: Interface web para consulta rápida das tabelas persistidas.
- A aplicação rodará em `http://localhost:8081`.

## Fluxo principal

1. O usuário acessa a aplicação web em `http://localhost:8081`.

2. A página inicial listará as tabelas do sistema de aviônica:
    - `telemetry_events`: Contém dados de telemetria dos sensores.
    - `routes`: Contém o histórico de rotas solicitadas e calculadas.
    - `system_events`: Registra as falhas e logs técnicos do sistema.
    - `module_status`: Guarda o último sinal de vida recebido de cada processo.

3. Ao lado do nome de cada tabela, o sistema exibirá:
    - O número total de linhas/registros salvos.
    - Um botão chamado **"Visualizar Dados"**.

4. Se o usuário clicar em **"Visualizar Dados"**, o sistema carregará uma tabela com as últimas linhas gravadas e redirecionará para `/tabela/{nome_da_tabela}`.
