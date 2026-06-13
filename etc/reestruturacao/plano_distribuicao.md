# Plano de Distribuição de Módulos Reestruturado (9 Participantes)

Este documento apresenta a nova distribuição de módulos do sistema após a reestruturação baseada em **Algoritmos de Sistemas Distribuídos**. Cada integrante é responsável por desenvolver pelo menos **dois módulos (processos) distribuídos**, totalizando os **18 módulos** exigidos para a disciplina.

---

## Módulos de Interface Gráfica / Localhosts (5 Módulos)

Estes módulos possuem interfaces gráficas ou endpoints REST/SSE próprios e rodam em portas separadas:

| # | Módulo | Tecnologia | Porta | Algoritmo / Responsabilidade Distribuída |
|---|---|---|---|---|
| 1 | **SGCA (Cockpit Simulator)** | Vue.js | `5173` | Interface visual principal. Exibe o estado dos consensos, computadores ativos e latências calculadas. |
| 2 | **Painel do Kafka (Localhost)** | Node.js / Python | `9000` | Interface para depuração e visualização dos payloads JSON trafegados em tempo real no barramento. |
| 3 | **Visualizador de Banco de Dados** | Node.js / Python | `8081` | Interface web para consultar e buscar logs de auditoria persistidos no banco de dados. |
| 4 | **Torre de Comando** | Node.js / Python | `8082` | Cadastro e gerência do ciclo de vida das aeronaves simuladas no sistema aviônico. |
| 5 | **Backend Gateway / Central** | Java / Spring Boot | `8080` | Gateway com suporte a **Circuit Breaker** e comunicação em tempo real via **Server-Sent Events (SSE)**. |

---

## Módulos de Algoritmos, Consenso e Sensores (13 Módulos)

Estes módulos rodam de forma independente (em containers ou processos Python separados) implementando lógica distribuída avançada:

| # | Módulo | Tecnologia | Tipo de Módulo | Algoritmo / Responsabilidade Distribuída |
|---|---|---|---|---|
| 6 | **FMS de Planejamento de Rotas** | Python | Event-driven | Recebe chamadas via Kafka e calcula a rota. Possui **Dijkstra local** como fallback em caso de falha da API externa. |
| 7 | **Detector de Falhas (Heartbeats)**| Python / Java | Monitor | Aplica um detector de falhas baseado em batimentos cardíacos (Heartbeats) para notificar quedas de nós. |
| 8 | **Voter Consensual do Motor** | Python | Centralizador | Executa a votação **Redundância Modular Tripla (TMR)** a partir dos dados consolidados dos motores redundantes. |
| 9 | **Motores Redundantes (A, B, C)** | Python | Produtor triplo | Processos que simulam o motor real (com suporte a injeção de dados corrompidos por Byzantine-like fault). |
| 10| **Servidor de Tempo (Sincronizador)**| Python / Java | Sincronizador | Serviço que coordena a sincronização de tempo compensando o RTT da rede (**Algoritmo de Cristian**). |
| 11| **Persistência Ordenada (Lamport)**| Python / Java | Consumidor | Consome mensagens do Kafka e ordena as inserções no PostgreSQL usando **Lamport Timestamps**. |
| 12| **Sensor de Freios com Lock** | Python | Produtor | Controla a ativação hidráulica usando algoritmo de exclusão mútua distribuída (**Ricart-Agrawala**). |
| 13| **Caixa Preta (FDR Replicada)** | Python | Consumidor | Grava dados persistentes utilizando replicação ativa em dois discos lógicos com quorum. |
| 14| **Computador de Voo Primário** | Python | Computador de Voo | Processador principal com detecção de queda e **Bully Algorithm** integrado para eleição de líder. |
| 15| **Computador de Voo Secundário** | Python | Computador de Voo | Réplica passiva que concorre na eleição (**Bully Algorithm**) para assumir o controle se o Primário falhar. |
| 16| **Radar Climático A (Gossip)** | Python | Radar/Sensor | Simula nuvens e vento, trocando dados climáticos com o Radar B usando **Gossip Protocol**. |
| 17| **Radar Climático B (Gossip)** | Python | Radar/Sensor | Pareia com o Radar A para replicação eventual da malha climática regional. |
| 18| **Injetor de Falhas Distribuídas** | Python | Simulador | Painel interativo para injetar lags de rede, corromper payloads ou desligar containers à força. |

---

## Divisão de Trabalho Sugerida por Integrante

Cada integrante assume a liderança técnica e o desenvolvimento de **dois módulos distribuídos**:

| Integrante | Módulo 1 (Interface/Processo Central) | Módulo 2 (Algoritmo de Sistemas Distribuídos) |
|---|---|---|
| **Gabriela** | Módulo 8: Voter Consensual do Motor (TMR) | Módulo 7: Detector de Falhas (Heartbeats) |
| **Rafael** | Módulo 6: FMS de Planejamento de Rotas (Fallback) | Módulo 16: Radar Climático A (Gossip Protocol) |
| **Joao Lucas C.**| Módulo 9: Motores Redundantes (A, B, C) | Módulo 18: Injetor de Falhas Distribuídas |
| **Mariana** | Módulo 5: Backend Gateway Central (Circuit Breaker) | Módulo 10: Servidor de Sincronização (Alg. de Cristian) |
| **Nickolas** | Módulo 11: Persistência Ordenada (Lamport Timestamps) | Módulo 12: Sensor de Freios (Exclusão Mútua/Ricart-Agrawala) |
| **Rafaely** | Módulo 1: SGCA Cockpit Simulator (Frontend) | Módulo 13: Caixa Preta (FDR Replicada/Master-Slave) |
| **Alison** | Módulo 14: Computador de Voo Primário (Líder) | Módulo 17: Radar Climático B (Gossip Protocol) |
| **Joao Lucas R.**| Módulo 15: Computador de Voo Secundário (Backup) | Módulo 3: Visualizador de Banco de Dados |
| **Ana Luisa** | Módulo 2: Painel do Kafka (Localhost) | Módulo 4: Torre de Comando (Gerenciador de Aeronaves) |
