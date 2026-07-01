# ✈️ Sistemas Distribuídos para um Sistema de Aviônica (Aviação Eletrônica)

Repositório acadêmico para implementação, simulação e análise de um **gateway tolerante a falhas para redes aviônicas híbridas AFDX/WAIC**.

O projeto integra microsserviços distribuídos, sensores simulados, comunicação por MQTT/Kafka, persistência em PostgreSQL, backend em Java/Spring Boot, frontend em Vue/Vite, simulação de rede no OMNeT++/INET e mecanismos de tolerância a falhas para ambientes críticos.

---

## 📌 Visão Geral

O objetivo deste projeto é representar uma arquitetura aviônica distribuída capaz de integrar sensores físicos, sensores sem fio WAIC, barramento determinístico AFDX, processamento distribuído e módulos de decisão embarcada.

A proposta explora três dimensões principais:

1. **Protótipo funcional distribuído**

   * Sensores simulados.
   * Broker MQTT.
   * Kafka para telemetria e eventos.
   * Backend de gateway.
   * Frontend de visualização.
   * Banco de dados PostgreSQL.

2. **Tolerância a falhas**

   * Motores redundantes.
   * Consenso por TMR.
   * Injeção de falhas.
   * Registro de eventos.
   * Separação entre sensores, processadores e atuadores.

3. **Simulação e validação**

   * Topologia aviônica no OMNeT++/INET.
   * Modelagem de rede híbrida AFDX/WAIC.
   * Avaliação de métricas como latência, vazão, perda de pacotes e atraso fim a fim.

---

## 🧠 Contexto do Projeto

Em sistemas aviônicos modernos, a comunicação entre sensores, computadores de voo e atuadores precisa cumprir requisitos rigorosos de confiabilidade, previsibilidade e tolerância a falhas.

A arquitetura proposta combina:

* **AFDX**: rede cabeada determinística usada em comunicação crítica.
* **WAIC**: comunicação sem fio interna à aeronave, voltada principalmente a sensores distribuídos.
* **MQTT**: middleware leve baseado em publicação/assinatura.
* **Kafka**: barramento de eventos para telemetria, persistência lógica e integração distribuída.
* **PostgreSQL**: armazenamento estruturado dos eventos e estados.
* **Docker Compose**: orquestração dos serviços do ambiente.

---

## 🏗️ Arquitetura Geral

A arquitetura do sistema pode ser entendida em camadas:

```text
Sensores físicos / WAIC
        ↓
MQTT Broker / Kafka
        ↓
Backend Gateway / Processadores Distribuídos
        ↓
Banco de Dados / Visualizador / Frontend
        ↓
Computador de Voo / Atuadores / Caixa Preta
```

Principais fluxos:

```text
Sensores de voo        → MQTT → Backend/FMS
Sensor de freio        → Kafka → Backend/telemetria
Motores A, B e C       → Kafka → Consenso/TMR
Radar externo          → MQTT → Automação/FADEC
Gateway backend        → PostgreSQL / Frontend
OMNeT++                → Simulação da topologia AFDX/WAIC
```

---

## 📁 Estrutura do Repositório

```text
.
├── Software_Aviao/          # Módulos Python da aeronave, sensores, motores e injetores
├── backend/                 # Backend Java/Spring Boot e serviços auxiliares
├── db-visualizer/           # Visualizador/auditor do banco PostgreSQL
├── etc/                     # Arquivos auxiliares do projeto
├── frontend/                # Interface web Vue/Vite
├── infra/                   # Configurações de infraestrutura, como Mosquitto
├── .env.example             # Exemplo de variáveis de ambiente
├── docker-compose.yml       # Orquestração principal dos serviços
├── Topologia.ned            # Topologia da simulação OMNeT++/INET
├── omnetpp.ini              # Configuração da simulação OMNeT++
├── package.json             # Dependências auxiliares do projeto
└── README.md                # Documentação principal
```

---

## ⚙️ Tecnologias Utilizadas

| Camada                         | Tecnologias                           |
| ------------------------------ | ------------------------------------- |
| Sensores e simulação embarcada | Python                                |
| Backend                        | Java, Spring Boot, Gradle             |
| Frontend                       | Vue 3, Vite, Bootstrap, Axios         |
| Banco de dados                 | PostgreSQL                            |
| Mensageria                     | MQTT, Eclipse Mosquitto, Apache Kafka |
| Orquestração                   | Docker, Docker Compose                |
| Simulação de rede              | OMNeT++, INET Framework               |
| Visualização de banco          | Node.js, Express, PostgreSQL client   |
| Modelagem e Desempenho         | Mercury Tool                          |

---

## 🧩 Principais Módulos

### 1. Software da Aeronave

Local:

```text
Software_Aviao/
```

Contém os módulos Python responsáveis pela simulação de sensores, motores, comunicação e lógica distribuída da aeronave.

Exemplos de serviços executados via Docker Compose:

* `fms-api`
* `sensor-flight`
* `sensor-brake`
* `radar`
* `navigation-computer`
* `automation-computer`
* `waic-leader`
* `motor-a`
* `motor-b`
* `motor-c`
* `injetor-kafka`
* `mqtt-kafka-bridge`
* `kafka-telemetry-consumer`

---

### 2. Backend Gateway

Local:

```text
backend/
```

Responsável por processar eventos, integrar telemetria, comunicar-se com Kafka/MQTT e expor APIs para o frontend.

O backend utiliza:

* Spring Boot
* Spring Web
* Spring Data JPA
* Spring Kafka
* PostgreSQL
* Cliente MQTT Eclipse Paho

Serviços relacionados:

* `backend-gateway`
* `kafka-stream-gateway`
* `aerocontrol-dispatcher`

---

### 3. Frontend

Local:

```text
frontend/
```

Interface web para acompanhamento visual do sistema.

Tecnologias:

* Vue 3
* Vite
* Bootstrap
* Axios
* Vue Router

Porta padrão:

```text
http://localhost:5173
```

---

### 4. Visualizador do Banco

Local:

```text
db-visualizer/
```

Serviço Node.js/Express usado para visualizar ou auditar dados armazenados no PostgreSQL.

Porta padrão:

```text
http://localhost:8081
```

---

### 5. Simulação OMNeT++/INET

Arquivos principais:

```text
Topologia.ned
omnetpp.ini
```

A simulação representa uma arquitetura aviônica com:

* sensores redundantes;
* sensores WAIC;
* switches TSN/AFDX;
* pontos de acesso sem fio;
* broker MQTT;
* computador de voo;
* módulo de consenso;
* automação FADEC;
* atuador;
* caixa preta.

Métricas previstas:

* atraso fim a fim;
* contagem de pacotes recebidos;
* histograma de atraso;
* tráfego crítico e não crítico;
* comportamento de canais redundantes.

---

## 🔐 Variáveis de Ambiente

Antes de executar o projeto, crie o arquivo `.env` a partir do exemplo:

```bash
cp .env.example .env
```

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Exemplo de configuração:

```env
POSTGRES_DB=avionica
POSTGRES_USER=avionica
POSTGRES_PASSWORD=avionica_dev

SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/avionica
SPRING_DATASOURCE_USERNAME=avionica
SPRING_DATASOURCE_PASSWORD=avionica_dev

KAFKA_BOOTSTRAP_SERVERS=kafka:9092
MQTT_BROKER=mqtt-broker
MQTT_PORT=1883

FMS_API_KEY=coloque_sua_chave_aqui
```

> **Importante:** não envie chaves reais, senhas privadas ou tokens de API para o GitHub.

---

## ▶️ Como Executar

### 1. Clonar o repositório

```bash
git clone https://github.com/lucifer-son/Sistemas_Distribuidos_Avionica.git
cd Sistemas_Distribuidos_Avionica
```

---

### 2. Criar o arquivo de ambiente

```bash
cp .env.example .env
```

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

---

### 3. Subir os serviços com Docker Compose

```bash
docker compose up --build
```

Ou, em versões antigas do Docker Compose:

```bash
docker-compose up --build
```

---

### 4. Acessar os serviços

| Serviço                | URL / Porta             |
| ---------------------- | ----------------------- |
| Frontend               | `http://localhost:5173` |
| Backend Gateway        | `http://localhost:8080` |
| Visualizador do Banco  | `http://localhost:8081` |
| Kafka Stream Gateway   | `http://localhost:9000` |
| AeroControl Dispatcher | `http://localhost:8082` |
| PostgreSQL             | `localhost:5432`        |
| MQTT Broker            | `localhost:1883`        |

---

## 🧪 Testes e Verificações

### Verificar containers ativos

```bash
docker compose ps
```

---

### Ver logs gerais

```bash
docker compose logs -f
```

---

### Ver logs de um serviço específico

```bash
docker compose logs -f backend-gateway
```

Exemplos:

```bash
docker compose logs -f mqtt-broker
docker compose logs -f kafka
docker compose logs -f motor-a
docker compose logs -f sensor-brake
docker compose logs -f frontend
```

---

### Parar os serviços

```bash
docker compose down
```

---

### Parar e remover volumes

Use este comando apenas se quiser apagar os dados persistidos no PostgreSQL:

```bash
docker compose down -v
```

---

## 📡 Comunicação e Tópicos

O projeto utiliza comunicação por tópicos para desacoplar sensores, processadores e consumidores.

Exemplos de categorias de tópicos:

```text
avionica/#
avionica.telemetry.brakes
avionica.mutex.brakes.request
avionica.mutex.brakes.grant
avionica.mutex.brakes.release
```


Tabela:

| Tópico                          | Tecnologia | Produtor             | Consumidor           | Descrição                              |
| ------------------------------- | ---------- | -------------------- | -------------------- | -------------------------------------- |
| `avionica/#`                    | MQTT       | Sensores             | Bridge MQTT-Kafka    | Filtro geral de mensagens aviônicas    |
| `avionica.telemetry.brakes`     | Kafka      | Sensor de freio      | Backend/consumidor   | Telemetria do sistema de freios        |
| `avionica.mutex.brakes.request` | Kafka      | Sensor de freio      | Controle distribuído | Solicitação de acesso à região crítica |
| `avionica.mutex.brakes.grant`   | Kafka      | Controle distribuído | Sensor de freio      | Concessão de acesso                    |
| `avionica.mutex.brakes.release` | Kafka      | Sensor de freio      | Controle distribuído | Liberação da região crítica            |

---

## 🛡️ Tolerância a Falhas

O projeto contempla mecanismos de robustez voltados a sistemas críticos:

* redundância de motores;
* votação por TMR;
* descarte de leituras divergentes;
* injeção de falhas via Kafka;
* separação entre módulos produtores e consumidores;
* caixa preta para registro passivo;
* canais redundantes AFDX/WAIC na simulação.

Fluxo conceitual do TMR:

```text
Motor A ┐
Motor B ├──> Votador / Consenso ──> Dado validado
Motor C ┘
```

Em caso de divergência, a leitura suspeita pode ser descartada ou marcada como falha, preservando o estado consolidado do sistema.

---

## 🧭 Simulação no OMNeT++

Para abrir a simulação:

1. Abra o OMNeT++.
2. Importe o projeto.
3. Garanta que o INET Framework esteja instalado e referenciado.
4. Abra o arquivo `Topologia.ned`.
5. Execute a configuração definida em `omnetpp.ini`.

Arquivos principais:

```text
Topologia.ned
omnetpp.ini
```

A simulação está configurada para representar o tráfego entre sensores, switches, canais redundantes, rede sem fio WAIC, broker MQTT, computador de voo, consenso e atuadores.

---

## 📊 Métricas de Interesse

As principais métricas observadas no projeto são:

| Métrica                       | Objetivo                                           |
| ----------------------------- | -------------------------------------------------- |
| Latência fim a fim            | Avaliar atraso entre sensores e computador de voo  |
| Vazão                         | Medir capacidade de tráfego da arquitetura         |
| Perda de pacotes              | Identificar impacto de sobrecarga ou interferência |
| Jitter                        | Avaliar variação temporal da entrega               |
| Contagem de pacotes recebidos | Verificar integridade do fluxo                     |
| Tempo de resposta do consenso | Avaliar impacto do TMR                             |
| Persistência de eventos       | Validar registro no banco/caixa preta              |

---

---

## ✅ Status Atual

| Item                            | Status                    |
| ------------------------------- | ------------------------- |
| Orquestração com Docker Compose | Em desenvolvimento        |
| Broker MQTT                     | Implementado              |
| Kafka                           | Implementado              |
| PostgreSQL                      | Implementado              |
| Backend Gateway                 | Em desenvolvimento        |
| Frontend Vue/Vite               | Em desenvolvimento        |
| Visualizador de banco           | Implementado/experimental |
| Sensores simulados              | Em Implementação          |
| Motores redundantes             | Implementado              |
| Injetor de falhas               | Em desenvolvimento        |
| Simulação OMNeT++               | Em Atualização            |
| Documentação técnica            | Em atualização            |

---

## 🧯 Solução de Problemas

### Porta já está em uso

Verifique qual processo está usando a porta:

```bash
docker compose ps
```

Depois pare os serviços:

```bash
docker compose down
```

---

### Banco não inicializa

Remova os volumes e suba novamente:

```bash
docker compose down -v
docker compose up --build
```

---

### Frontend não acessa o backend

Verifique se o backend está ativo:

```bash
docker compose logs -f backend-gateway
```

Confirme também se a variável abaixo está correta:

```env
VITE_API_BASE_URL=http://localhost:8080
```

---

### Kafka demora a iniciar

Aguarde a inicialização completa e confira os logs:

```bash
docker compose logs -f kafka
```

---

## 📚 Referências Técnicas

* ARINC 664 / AFDX
* WAIC — Wireless Avionics Intra-Communications
* MQTT — Message Queuing Telemetry Transport
* Apache Kafka
* Docker Compose
* OMNeT++
* INET Framework
* Redes de Petri
* Sistemas Distribuídos
* Sistemas Críticos de Tempo Real

---

## 👥 Autoria

Projeto desenvolvido para fins acadêmicos na área de **Sistemas Distribuídos, Redes de Computadores e Análise de Desempenho**.

Autore:

```text
Rafael Melo
João Lucas Ribeiro
Mariana Oliveira
Nickollas Vital
João Lucas Cosme
Alisson Xavier
Ana Luisa Vieira
Rafaelly Cristine

```

---

## 📄 Licença

Este repositório ainda não possui uma licença definida.
