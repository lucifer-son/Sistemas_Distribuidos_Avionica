# ✈️ Gateway Tolerante a Falhas para Redes Aviônicas Híbridas (AFDX/WAIC)

Um projeto completo de modelagem, simulação e implementação de um sistema crítico distribuído para a aviação moderna. Este repositório foca na integração segura entre redes cabeadas determinísticas (**AFDX**) e redes sem fio nas extremidades da aeronave (**WAIC**).

---

## 📌 Visão Geral e Principais Funcionalidades

Nosso sistema atua como o "sistema nervoso" de uma aeronave, lidando com a complexidade de sistemas críticos de tempo real. As principais funcionalidades desenvolvidas incluem:

* **Gateway de Admissão de Tráfego:** Uma ponte tolerante a falhas que recebe dados assíncronos de nós sem fio (WAIC) e os enfileira na rede determinística (AFDX) com rigoroso controle de admissão (evitando congestionamento e respeitando limites de *jitter*).
* **Consenso TMR (Triple Modular Redundancy):** Algoritmo de "Votador Bizantino" implementado no Motor da aeronave. Ele exige a leitura idêntica de pelo menos 3 sensores para validar uma informação, descartando dados corrompidos ou falhas de hardware.
* **Atuação Autônoma (Anti-Gelo):** Microsserviço independente capaz de tomar decisões locais e autônomas em tempo real para a segurança do voo, baseado em leituras de sensores das asas.
* **Caixa Preta Isolada:** Nó arquitetado de forma modular para registrar eventos no barramento de forma passiva e isolada, garantindo integridade e segurança.

---

## 🏗️ Estrutura de Microsserviços e Sensores

A arquitetura do protótipo afasta-se de sistemas monolíticos obsoletos e adota uma abordagem moderna, distribuída e sem servidor:

* **Padrão Publish/Subscribe:** Utilização do protocolo leve **MQTT** para garantir que sensores, atuadores e o FMS (*Flight Management System*) operem de forma totalmente desacoplada.
* **Sensores e Atuadores Simulados:** Nós independentes (sensores de temperatura, pressão, atuadores de motor, sistema anti-gelo) que publicam e assinam tópicos específicos.
* **Orquestração em Docker:** Todos os componentes e o *middleware* de comunicação rodam em contêineres Docker isolados, facilitando a escalabilidade, reprodução e testes do ambiente.

---

## 📐 Modelagem Matemática e Formal

Sistemas de aviação exigem certificação de aeronavegabilidade rigorosa. Para garantir a confiabilidade antes de qualquer linha de código ir para o ar, aplicamos modelagem formal:

* **Redes de Petri Estocásticas (SPN/DSPN):** Utilizamos a ferramenta **PIPE** para modelar matematicamente todos os estados do Gateway, a coreografia autônoma e o fluxo de dados.
* **Prova de Consenso e Sincronização:** Modelagem específica do algoritmo TMR para garantir a confiabilidade sob falha bizantina.
* **Garantia contra Deadlocks:** O modelo matemático comprova formalmente a **ausência de deadlocks lógicos**, garantindo que o sistema nunca ficará "travado" aguardando respostas infinitas, além de validar a sincronização precisa de estados.

---

## 📊 Simulação e Análise de Desempenho

Para validar parâmetros físicos de rede (onde a latência é questão de vida ou morte), criamos uma topologia simulada:

* **Simulador:** OMNeT++ (com framework INET).
* **Métricas Extraídas:** Análise gráfica e quantitativa de tráfego crítico vs. não-crítico, aferindo latência ponta-a-ponta, vazão (*throughput*) e taxa de perda de pacotes sob diferentes cargas de estresse.

---

## 🛠️ Ferramentas Utilizadas

* **Linguagens/Scripts:** Python / C++
* **Middleware:** Eclipse Mosquitto (MQTT Broker)
* **Orquestração:** Docker e Docker Compose
* **Modelagem Formal:** PIPE (Platform Independent Petri Net Editor)
* **Simulação de Redes:** OMNeT++ e INET Framework

---

## 🚀 Como Executar o Projeto

### 1. Protótipo de Microsserviços (Docker)
```bash
# Clone o repositório
git clone [https://github.com/seu-usuario/gateway-afdx-waic.git](https://github.com/seu-usuario/gateway-afdx-waic.git)
cd gateway-afdx-waic/software

# Suba a infraestrutura de rede, o Broker MQTT e os sensores
docker-compose up --build
