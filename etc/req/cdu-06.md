# CDU-06: Monitorização de Ações Autónomas (Anti-gelo e TCAS)

## 1. Descrição
Permite ao utilizador visualizar o acionamento autónomo de sistemas críticos baseados em condições externas. O foco não é apenas visualizar a leitura, mas confirmar que a rede reagiu de forma automática (Machine-to-Machine) via barramento Kafka, atuando sem intervenção humana.

## 2. Atores
- **Utilizador:** Piloto a monitorizar o Glass Cockpit (Frontend Vue).
- **Nós Autónomos:** Simuladores (`sensor_clima.py`, `tcas.py`).

## 3. Pré-condições
- O sistema de mensagens está ativo e os módulos autónomos estão ligados ao barramento.

## 4. Fluxo Principal
1. O utilizador está com o ecrã do Dashboard Principal aberto.
2. O simulador de clima (`sensor_clima.py`) capta uma queda drástica de temperatura combinada com humidade (indicativo de formação de gelo).
3. O próprio nó distribuidor publica uma mensagem de comando de atuação no respetivo tópico.
4. O Backend lê essa atuação e guarda na base de dados PostgreSQL.
5. O Frontend recebe a atualização e altera o ícone/indicador do sistema Anti-gelo (Pitot/Asas) de cinzento (Desligado) para verde (Ativo/On).
6. Um pop-up não-intrusivo notifica o piloto: *"Sistema Anti-gelo acionado automaticamente"* (podendo incluir áudio sintético, se configurado).

## 5. Fluxos Alternativos
- **5a. Alerta de Colisão Iminente (TCAS):**
  1. O módulo TCAS identifica tráfego aéreo a cruzar a mesma altitude.
  2. A mensagem sobe ao barramento como evento de severidade máxima.
  3. A interface sobrepõe um alerta visual intermitente no ecrã e indica a manobra evasiva (ex: *PULL UP*).

## 6. Pós-condições
- Fica evidenciado o comportamento de *Publisher/Subscriber* reativo, onde os nós tomam decisões e o backend/frontend atuam apenas como exibidores de estado.
