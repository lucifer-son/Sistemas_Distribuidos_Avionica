# CDU-01: Cadastro e Criação de Aeronaves

## Definições/Regras

- A aplicação rodará em `http://localhost:8082`.
- O código da aeronave (Callsign/Prefixo) deve ser exclusivo e conter entre 4 e 8 caracteres alfanuméricos (ex: `PR-AAA`, `VARIG101`).

## Fluxo principal

1. O usuário acessa a Torre de Comando em `http://localhost:8082` e seleciona a opção **"Nova Aeronave"**.

2. O sistema exibe um formulário de cadastro com os seguintes campos:
    - **Código de Registro (Callsign/Prefixo)** (ex: `PR-AAA`)
    - **Modelo da Aeronave** (ex: `Boeing 737`, `Airbus A320`, `Embraer 190`)
    - **Capacidade Máxima de Combustível** (litros)
    - **Velocidade de Cruzeiro Recomendada** (nós)

3. O usuário insere as informações e clica em **"Salvar"**.

4. O sistema valida os dados:
    - Garante que o callsign não está duplicado.
    - Persiste os dados da aeronave no banco de dados.
    - Publica um evento de notificação no Kafka (ex: no tópico `avionica.aircraft.created`) para avisar o sistema e os simuladores de que uma nova aeronave está pronta para uso.

5. O usuário recebe a confirmação de criação da aeronave e é redirecionado para a lista de aeronaves ativas em `http://localhost:8082/aeronaves`.
