# CDU-01: Visão Geral do Painel Inicial (Glass Cockpit / Dashboard Principal)

## 1. Descrição
Este caso de uso descreve a inicialização e o comportamento do **Painel Inicial (Dashboard Principal)** da aplicação web (Frontend Vue.js). O painel atua como o *Glass Cockpit* da aeronave, agregando de forma visual e consolidada os dados provenientes de todos os microsserviços distribuídos (Sensores WAIC, Radar, FMS, Consenso de Motores) em um único ecrã de consciência situacional.

## 2. Atores
- **Utilizador:** Piloto, Copiloto ou Mecânico de Voo responsável pela monitorização da aeronave.
- **Backend Spring Boot:** Fornece os dados consolidados via REST/WebSockets.
- **Broker de Mensagens (Kafka):** Barramento por onde transitam os dados em tempo real.

## 3. O Que Deve Conter no Painel Inicial?
Para garantir a segurança e a operação correta da aeronave, o painel inicial deve ser dividido em quadrantes lógicos (inspirados nos sistemas PFD e EICAS da aviação real):

* **Primary Flight Display (PFD - Indicadores de Voo):**
    * **Velocidade (Airspeed):** Exibida em Mach ou Nós (Knots).
    * **Altitude:** Exibida em Pés (ft).
    * **Atitude (Horizonte Artificial):** Dados de *Pitch* (arfagem) e *Roll* (rolagem) vindos dos giroscópios.
* **Engine Indicating and Crew Alerting System (EICAS - Motores e Alertas):**
    * **Status dos Motores (TMR):** Temperatura e Pressão já consolidadas pelo algoritmo do Consenso Bizantino (mostrando o valor validado e não as falhas periféricas).
    * **Nível de Combustível:** Percentagem e fluxo de consumo.
    * **Central de Alertas (Crew Alerting):** Feed de mensagens do sistema (ex: "Sistema Anti-gelo Ativo", "Aviso: Perda de pacote no sensor B").
* **Navegação e Rota (FMS Miniatura):**
    * Aeroporto de Origem e Destino (Códigos ICAO ativos).
    * Progresso da Rota e Tempo Estimado de Chegada (ETA).
* **Sistemas Auxiliares (Radar e Freios):**
    * Pressão Hidráulica dos Freios (PSI).
    * Condições Climáticas externas e aviso de formação de gelo.

## 4. Pré-condições
- A arquitetura base (Docker, PostgreSQL, Kafka, Backend Spring Boot) está inicializada e operacional.
- Os nós produtores (simuladores Python) estão a publicar ativamente telemetria no barramento.

## 5. Fluxo Principal
1. O utilizador acede à raiz da aplicação web (`http://localhost:5173/`).
2. O Frontend Vue.js carrega o layout do **Painel Inicial** com os *widgets* vazios ou em estado de "Carregando".
3. O Frontend estabelece uma conexão contínua com o Backend (via *Server-Sent Events - SSE*, *WebSockets* ou *Polling* otimizado).
4. O Backend consome as mensagens mais recentes dos vários tópicos Kafka (voo, motores, radar) e despacha-as para o Frontend.
5. Os componentes visuais (gráficos, medidores circulares e painéis de texto) são atualizados simultaneamente à medida que os dados fluem.
6. O utilizador obtém uma visão panorâmica e em tempo real da saúde estrutural e da trajetória da aeronave num único ecrã.

## 6. Fluxos Alternativos
- **6a. Indisponibilidade de um Subsistema Isolado:**
  1. O nó do Radar Climático falha ou perde a conexão com o Kafka.
  2. O Backend deteta a falta de dados recentes (timeout) daquele tópico específico.
  3. No Painel Inicial, apenas o quadrante do Radar exibe o estado **"OFFLINE / NO DATA"** ou fica a cinzento.
  4. **Comportamento Crítico:** Os restantes quadrantes (Altitude, Motores, FMS) continuam a atualizar normalmente, provando visualmente a resiliência e o desacoplamento da arquitetura de microsserviços.

## 7. Pós-condições
- O utilizador mantém a consciência situacional contínua. O painel serve como ponto de partida central, permitindo a navegação para ecrãs mais detalhados (ex: Auditoria da Caixa Preta, Injeção de Falhas ou FMS completo) através do menu lateral.
