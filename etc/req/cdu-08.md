# CDU-08: Health Check e Topologia de Rede (Microsserviços)

## 1. Descrição
Monitoriza e exibe a "saúde" da própria arquitetura de software, garantindo que nenhum produtor, consumidor ou infraestrutura base (Kafka/PostgreSQL) caiu silenciosamente.

## 2. Atores
- **Utilizador:** Administrador do Sistema / Desenvolvedor.

## 3. Pré-condições
- A aplicação principal está a correr. Todos os contentores Docker (base de dados, Kafka, frontend, backend) devem estar operacionais.

## 4. Fluxo Principal
1. O utilizador acede ao separador **"Estado da Rede / Health Check"**.
2. O Vue renderiza um mapa lógico ou uma lista com os nós do sistema:
   - Barramento Kafka
   - PostgreSQL
   - Backend Spring Boot
   - Produtor FMS
   - Produtor Motor A, B, C
   - Gateway WAIC
3. O Backend fornece estas informações através de um *endpoint* dedicado (ex: Spring Boot Actuator ou uma tabela própria de *heartbeats* dos sensores).
4. O sistema exibe um marcador verde ("UP") ou vermelho ("DOWN") ao lado de cada módulo, além da latência (ping temporal) da sua última mensagem publicada.

## 5. Fluxos Alternativos
- **5a. Queda de um Componente Crítico:**
  1. O nó do PostgreSQL fica inoperante ou o broker Kafka cai.
  2. O Frontend deteta a falta de respostas de health check do Backend.
  3. O ecrã bloqueia funcionalidades que dependem de dados em tempo real e exibe um modal central a indicar perda catastrófica de comunicação de rede.

## 6. Pós-condições
- Transparência total sobre a infraestrutura distribuída, permitindo o reinício rápido de processos bloqueados sem necessidade de abrir terminais Docker no servidor.
