# CDU-02: Monitoramento e Lista de Aeronaves Ativas

## Definições/Regras

- URL da tela: `http://localhost:8082/aeronaves`.

## Fluxo principal

1. O usuário acessa a lista de aeronaves ativas pela URL ou após salvar uma nova aeronave no [cdu-01](cdu-01.md).

2. A tela exibirá todas as aeronaves cadastradas no ecossistema de simulação, com as seguintes colunas de dados:
    - **Prefixo/Callsign**
    - **Modelo**
    - **Status Atual**: `No Pátio` (On Ground), `Em Voo` (In Flight), `Offline` (Simulador inativo).
    - **Última Atualização**: Timestamp do último ping recebido dos sensores de voo.

3. O sistema atualiza dinamicamente o status e a última atualização ao receber pings/heartbeats de voo via Kafka.

4. O usuário poderá:
    - Selecionar uma aeronave e clicar em **"Excluir"** (para removê-la do ecossistema, o que não será permitido se o status for `Em Voo`).
    - Obter o código Callsign de uma aeronave no pátio para informá-lo na tela de simulação do SGCA ([cdu-02 do SGCA](../sgca/cdu-02.md)).
