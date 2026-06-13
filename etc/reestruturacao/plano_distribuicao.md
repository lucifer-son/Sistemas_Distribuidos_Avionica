# Plano de Distribuição de Módulos Reestruturado (9 Participantes)

Este documento apresenta a nova distribuição de módulos do sistema após a reestruturação das regras de negócio em CDUs. Cada integrante será responsável por desenvolver pelo menos **dois módulos (processos) distribuídos**, totalizando os **18 módulos** necessários para atender aos requisitos da disciplina.

---

## Módulos de Interface Gráfica / Localhosts (5 Módulos)

Estes módulos possuem interfaces gráficas próprias que rodam em portas locais (localhost) e contam como processos separados na contagem da disciplina:

| # | Módulo | Tecnologia | Porta | Responsabilidade |
|---|---|---|---|---|
| 1 | **SGCA (Cockpit Simulator)** | Vue.js | `5173` | Interface principal do cockpit, exibindo o dashboard de voo e permitindo simular rotas. |
| 2 | **Painel do Kafka (Localhost)** | Node.js / Python | `9000` | Interface para visualizar as mensagens trafegando pelos tópicos do Kafka em tempo real. |
| 3 | **Visualizador do Banco de Dados** | Node.js / Python | `8081` | Interface web para consultar e buscar dados diretamente nas tabelas do PostgreSQL. |
| 4 | **Torre de Comando** | Node.js / Python | `8082` | Interface e API para criar, listar e gerenciar as aeronaves que serão simuladas no SGCA. |
| 5 | **Backend Gateway / Central** | Java / Spring Boot | `8080` | Ponto de entrada de APIs REST, orquestração e consumo/produção de mensagens no Kafka. |

---

## Módulos de Simulação e Telemetria (13 Módulos)

Estes módulos rodam de forma independente (em containers ou processos Python separados) gerando e processando dados para o barramento Kafka:

| # | Módulo | Tecnologia | Tipo | Responsabilidade |
|---|---|---|---|---|
| 6 | **FMS de Planejamento de Rotas** | Python | Event-driven | Recebe solicitações do backend, calcula distâncias e ETAs via API e publica respostas. |
| 7 | **Sensor de Velocidade** | Python | Produtor | Publica dados periódicos de velocidade e Mach. |
| 8 | **Sensor de Altitude** | Python | Produtor | Publica dados periódicos de altitude da aeronave. |
| 9 | **Sensor de Atitude** | Python | Produtor | Publica dados de pitch, roll e yaw (giroscópio). |
| 10| **Sensor de Combustível** | Python | Produtor | Publica dados de quantidade de combustível e fluxo de consumo. |
| 11| **Sensor de Freios** | Python | Produtor | Publica dados de pressão hidráulica do sistema de freios. |
| 12| **Radar Externo e Clima** | Python | Produtor | Simula detecção de nuvens e velocidade do vento. |
| 13| **Computador de Navegação** | Python | Consumidor/Produtor | Monitora o progresso de rota ativa com base nas coordenadas. |
| 14| **Computador de Automação / Anti-Ice**| Python | Consumidor/Produtor | Monitora sensor de clima e aciona automaticamente o degelo. |
| 15| **Líder WAIC (Dados do Motor)** | Python | Produtor | Coleta e publica temperatura e pressão consolidadas do motor. |
| 16| **Caixa Preta (Flight Data Recorder)**| Python | Consumidor | Escuta eventos críticos do sistema e armazena em logs isolados. |
| 17| **Sistema de Alertas Sonoros/Visuais**| Python / Java | Consumidor | Consome mensagens do Kafka para disparar alertas no painel CAS. |
| 18| **Injetor de Falhas / Simulador Piloto**| Python | Produtor | Simula comandos de pilotagem e falhas de sensores para teste. |

---

## Sugestão de Divisão por Integrante

Cada integrante do grupo assume a liderança e desenvolvimento de **dois módulos**:

| Integrante | Módulo 1 (Interface/Processo Central) | Módulo 2 (Sensor/Simulador/Auxiliar) |
|---|---|---|
| **Integrante 1** | Módulo 1: SGCA (Cockpit Simulator) | Módulo 7: Sensor de Velocidade |
| **Integrante 2** | Módulo 5: Backend Gateway Central | Módulo 8: Sensor de Altitude |
| **Integrante 3** | Módulo 2: Painel do Kafka (Localhost) | Módulo 9: Sensor de Atitude |
| **Integrante 4** | Módulo 3: Visualizador do Banco de Dados | Módulo 10: Sensor de Combustível |
| **Integrante 5** | Módulo 4: Torre de Comando | Módulo 11: Sensor de Freios |
| **Integrante 6** | Módulo 6: FMS de Planejamento de Rotas | Módulo 12: Radar Externo e Clima |
| **Integrante 7** | Módulo 13: Computador de Navegação | Módulo 17: Sistema de Alertas Sonoros/Visuais |
| **Integrante 8** | Módulo 14: Computador de Automação | Módulo 16: Caixa Preta (Flight Data Recorder) |
| **Integrante 9** | Módulo 15: Líder WAIC (Dados do Motor) | Módulo 18: Injetor de Falhas / Simulador Piloto |
