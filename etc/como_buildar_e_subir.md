# 🛠️ Como Buildar e Subir o Projeto

> Guia passo a passo para compilar, buildar e executar todos os serviços do sistema aviônico distribuído via Docker.

---

## 📋 Pré-requisitos

Antes de qualquer coisa, verifique se você tem instalado:

| Ferramenta | Versão mínima | Verificar com          |
|------------|---------------|------------------------|
| Docker Desktop | 24+       | `docker --version`     |
| Docker Compose | v2+       | `docker compose version` |
| Java JDK   | 25            | `java --version`       |
| Git        | qualquer      | `git --version`        |

> [!IMPORTANT]
> O **Docker Desktop precisa estar rodando** antes de qualquer comando abaixo.
> Para verificar: abra o Docker Desktop e aguarde o ícone na bandeja ficar verde.

---

## 1️⃣ Preparar o `.env`

O projeto usa um arquivo `.env` na raiz para configurar senhas e URLs.
Ele **não é versionado no Git** por segurança. Você precisa criá-lo uma vez:

```powershell
# Na raiz do projeto:
Copy-Item .env.example .env
```

O `.env` gerado já vem com valores padrão que funcionam localmente.
**Não é necessário alterar nada para rodar localmente**, exceto o `FMS_API_KEY` se quiser usar o cálculo real de rotas:

```
# Conteúdo do .env (valores padrão — funcionam sem alterar)
POSTGRES_DB=avionica
POSTGRES_USER=avionica
POSTGRES_PASSWORD=avionica_dev
SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/avionica
SPRING_DATASOURCE_USERNAME=avionica
SPRING_DATASOURCE_PASSWORD=avionica_dev
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
MQTT_BROKER=mqtt-broker
MQTT_PORT=1883
FMS_API_KEY=coloque_sua_chave_aqui   ← opcional: chave da API Ninjas para calcular rotas reais
```

---

## 2️⃣ Build Manual do Backend (opcional, para verificar antes do Docker)

Se quiser compilar o backend Java **localmente** antes de subir os containers:

```powershell
# Entrar na pasta do backend
cd backend

# Compilar (verifica se o código tem erros)
.\gradlew.bat compileJava --no-daemon

# Gerar o JAR final (usado pelo Dockerfile)
.\gradlew.bat bootJar --no-daemon

# Voltar para a raiz
cd ..
```

### ✅ O que você deve ver ao compilar (`compileJava`)

```
> Task :compileJava

BUILD SUCCESSFUL in Xs
1 actionable task: 1 executed
```

> [!NOTE]
> Na **primeira execução**, o Gradle vai baixar todas as dependências (Spring Boot, Kafka, MQTT, etc).
> Isso pode levar **2 a 5 minutos** dependendo da internet. As próximas execuções são instantâneas.

### ✅ O que você deve ver ao gerar o JAR (`bootJar`)

```
> Task :compileJava
> Task :processResources
> Task :classes
> Task :bootJar

BUILD SUCCESSFUL in Xs
4 actionable tasks: 4 executed
```

O arquivo JAR é gerado em:
```
backend/build/libs/avionica-backend-0.1.0.jar
```

### ❌ O que indica erro

```
FAILURE: Build failed with an exception.
* What went wrong:
  Compilation failed; see the compiler output below.
  error: cannot find symbol
```

Causas comuns:
- Java 25 não instalado → verificar com `java --version`
- Arquivo `.java` com nome diferente da classe pública dentro dele
- Import apontando para classe inexistente

---

## 3️⃣ Subir tudo com Docker Compose

Este é o **comando principal** para subir o sistema completo:

```powershell
# Na raiz do projeto (onde está o docker-compose.yml):
docker compose up --build
```

O `--build` força o Docker a recompilar as imagens. Use sempre na primeira vez ou após alterar código.

Para rodar **em segundo plano** (sem travar o terminal):

```powershell
docker compose up --build -d
```

---

## 4️⃣ O que acontece durante o `docker compose up --build`

O Docker vai construir e subir **11 serviços** em ordem. Veja o que esperar em cada etapa:

### Etapa 1 — Build da imagem do Backend (mais demorada)

```
 => [backend-gateway] FROM eclipse-temurin:25-jdk AS build
 => [backend-gateway] COPY gradlew gradlew.bat settings.gradle build.gradle ./
 => [backend-gateway] COPY src ./src
 => [backend-gateway] RUN chmod +x gradlew && ./gradlew bootJar --no-daemon
```

O Docker compila o projeto Java **dentro do container** (usando a imagem do JDK 25).
Isso pode levar **3 a 8 minutos** na primeira vez (baixa dependências + compila).

**O que você vai ver durante o build Java dentro do Docker:**
```
Downloading https://services.gradle.org/distributions/gradle-X.X-bin.zip
...
> Task :compileJava
> Task :bootJar

BUILD SUCCESSFUL in Xs
```

### Etapa 2 — Build da imagem do Frontend

```
 => [frontend] FROM node:25-alpine
 => [frontend] RUN npm ci --include=optional
 => [frontend] COPY . .
```

Instala as dependências Node.js e prepara o servidor Vite.
Leva **1 a 3 minutos** na primeira vez.

### Etapa 3 — Build das imagens Python

```
 => [fms-api] FROM python:3.11-slim
 => [fms-api] RUN pip install paho-mqtt requests
 => [fms-api] COPY *.py ./
```

Instala `paho-mqtt` e `requests`. Todos os 7 módulos Python compartilham o mesmo Dockerfile.

### Etapa 4 — Subida dos serviços (após o build)

Os containers sobem na ordem definida pelo `depends_on`:

```
✔ Container avionica_postgres          Started
✔ Container avionica_kafka             Started
✔ Container avionica_mqtt_broker       Started
✔ Container avionica_backend_gateway   Started    ← aguarda postgres estar healthy
✔ Container avionica_frontend          Started    ← aguarda backend
✔ Container avionica_fms_api           Started
✔ Container avionica_sensor_flight     Started
✔ Container avionica_sensor_brake      Started
✔ Container avionica_radar             Started
✔ Container avionica_navigation_computer Started
✔ Container avionica_automation_computer Started
✔ Container avionica_waic_leader        Started
```

---

## 5️⃣ O que você deve ver nos logs após subir

Quando todos os containers estiverem no ar, os logs mostram o seguinte (misturado):

### Backend Gateway (Spring Boot)
```
avionica_backend_gateway  |  :: Spring Boot ::  (v4.0.x)
avionica_backend_gateway  | Backend Gateway pronto em http://localhost:8080
avionica_backend_gateway  | Health check disponivel em /api/health
avionica_backend_gateway  | Lista de modulos disponivel em /api/modules
avionica_backend_gateway  | Assinando telemetria MQTT em tcp://mqtt-broker:1883 no topico avionica/#
avionica_backend_gateway  | Conectado ao MQTT tcp://mqtt-broker:1883. Topico ativo: avionica/#
```

### Sensores Python (publicando telemetria)
```
avionica_sensor_flight    | 📡 Enviando Telemetria -> Combustível: 99.98% | Mach: 0.801
avionica_sensor_flight    | 📡 Enviando Telemetria -> Combustível: 99.97% | Mach: 0.800
avionica_sensor_brake     | [Canal A] Enviado ID: a3f2c1d4... | Pressão: 87.3 psi
avionica_sensor_brake     | [Canal B] Enviado ID: a3f2c1d4... (Cópia Redundante de Segurança)
avionica_radar            | (publica a cada 3s — sem log visível por padrão)
avionica_waic_leader      | 📡 Pacote WAIC Enviado! Motor: 221.4 psi | Temp: 97.2 °C
avionica_navigation_computer | 📍 Navegação | Proa: 271° | Rumo a: ROTA_OCEANICA
```

### FMS
```
avionica_fms_api          | 💻 FMS Conectado à Rede Aviônica.
```

### PostgreSQL
```
avionica_postgres         | database system is ready to accept connections
```

### Kafka
```
avionica_kafka            | Kafka Server started
```

---

## 6️⃣ Como verificar se está tudo funcionando

Após subir, abra os seguintes endereços no navegador:

| Endereço | O que deve aparecer |
|----------|---------------------|
| `http://localhost:5173` | Interface web Vue.js do projeto |
| `http://localhost:8080/api/health` | JSON: `{"status":"UP","service":"backend-gateway","timestamp":"..."}` |
| `http://localhost:8080/api/modules` | JSON com lista de todos os módulos |
| `http://localhost:8080/api/aircraft-data` | JSON com telemetria em tempo real dos sensores |

### Exemplo do retorno de `/api/aircraft-data` (quando os sensores estão ativos):

```json
{
  "updatedAt": "2026-05-27T02:00:00Z",
  "flight": {
    "combustivel_pct": 99.87,
    "altitude_ft": 34950,
    "velocidade_mach": 0.801
  },
  "brakes": {
    "pressao": 87.3
  },
  "radar": {
    "vento_knots": 23,
    "radar_clima": "CÉU LIMPO",
    "temp_externa_c": 12
  },
  "waic": {
    "pressao_motor": 218.5,
    "temperatura": 99.1
  },
  "rawMessages": [ "..." ]
}
```

---

## 7️⃣ Comandos Úteis do dia a dia

```powershell
# Ver logs de um serviço específico (em tempo real)
docker compose logs -f backend-gateway
docker compose logs -f sensor-flight
docker compose logs -f fms-api

# Ver status de todos os containers
docker compose ps

# Parar tudo (sem apagar dados)
docker compose stop

# Parar e remover os containers (mantém volumes/dados do banco)
docker compose down

# Parar, remover containers E apagar os dados do banco
docker compose down -v

# Recompilar apenas um serviço específico (ex: após alterar o backend)
docker compose up --build backend-gateway

# Recompilar apenas os módulos Python
docker compose up --build fms-api sensor-flight sensor-brake
```

---

## 8️⃣ Fluxo completo de rebuild após alterar código

### Se alterou o backend Java:
```powershell
# 1. Verificar se compila localmente primeiro (mais rápido que esperar o Docker)
cd backend
.\gradlew.bat compileJava --no-daemon
cd ..

# 2. Recompilar a imagem e reiniciar o container
docker compose up --build backend-gateway
```

### Se alterou um módulo Python:
```powershell
# Recompilar apenas o serviço alterado
docker compose up --build sensor-flight   # ou fms-api, sensor-brake, etc.
```

### Se alterou o frontend (Vue.js):
```powershell
# O frontend usa hot-reload via volume bind-mount — não precisa rebuildar!
# As alterações em frontend/src/ aparecem automaticamente no navegador.
# Só precisa rebuildar se alterar o package.json:
docker compose up --build frontend
```

---

## 9️⃣ Problemas Comuns e Soluções

### ❌ `Error: No such container` ou containers não sobem

```powershell
# Verificar se o Docker está rodando
docker info

# Forçar remoção de containers antigos e subir do zero
docker compose down
docker compose up --build
```

---

### ❌ Backend não conecta ao MQTT (`Nao foi possivel conectar ao MQTT`)

O backend tentou conectar ao MQTT antes do broker estar pronto. Isso é esperado na **primeira vez** — o backend tem reconexão automática. Aguarde 10–15 segundos e verifique os logs novamente:

```powershell
docker compose logs -f backend-gateway
```

Você deve ver depois:
```
Conectado ao MQTT tcp://mqtt-broker:1883. Topico ativo: avionica/#
```

---

### ❌ Backend falhou com `BUILD FAILED` dentro do Docker

O build Java falhou dentro do container. Para ver o erro completo:

```powershell
# Rodar o build isolado com output completo
docker compose build --no-cache backend-gateway
```

Verifique também localmente:
```powershell
cd backend
.\gradlew.bat bootJar --no-daemon
```

---

### ❌ `/api/aircraft-data` retorna campos vazios (`{}`)

Os sensores Python ainda não publicaram dados. Aguarde 5–10 segundos e recarregue.
Verifique se os sensores estão no ar:

```powershell
docker compose ps
# Todos devem mostrar "running" ou "Up"
```

---

### ❌ Porta 5432, 8080 ou 1883 já em uso

Outro processo está usando a porta. Solução:

```powershell
# Descobrir qual processo usa a porta (ex: 8080)
netstat -ano | findstr :8080

# Matar o processo pelo PID encontrado
taskkill /PID <numero_do_pid> /F
```

Ou altere a porta no `docker-compose.yml`:
```yaml
ports:
  - "8081:8080"   # Muda de 8080 para 8081 no host
```

---

### ❌ IntelliJ: `@Service`, `@RestController` ou imports em vermelho / `Cannot find declaration to go to` ao clicar

**Causa:**
O IntelliJ abriu a pasta raiz do projeto completo (`Sistemas_Distribuidos_Avionica`), mas não sincronizou o subdiretório `backend` como um projeto Gradle. Por conta disso, a IDE não reconhece o código-fonte Java nem baixa as dependências do Spring Boot e outras bibliotecas.

**Como resolver:**
1. No IntelliJ, abra a aba lateral do **Gradle** (geralmente localizada no canto direito da tela).
2. Clique no ícone de **+** (ou "Add Gradle Project").
3. Selecione o arquivo `backend/build.gradle` na árvore de arquivos.
4. Aguarde o IntelliJ sincronizar o projeto (você verá uma barra de progresso no canto inferior direito baixando os JARs).
5. *Alternativa:* Se preferir trabalhar apenas no Java, vá em `File -> Open` no IntelliJ e abra diretamente a pasta `backend/` como a raiz do projeto.

**Como saber se deu certo:**
- A pasta `src/main/avionica` ficará na cor **azul** (indicando que é reconhecida como Source Root).
- As anotações `@Service`, `@RestController` e os imports deixarão de ficar vermelhos.
- Ao segurar a tecla `Ctrl` e clicar sobre uma anotação como `@Service`, o IntelliJ irá navegar com sucesso para a declaração da classe.

---

## 🗂️ Resumo dos Serviços e Portas

| Serviço                    | Container                        | Porta no Host | Tecnologia        |
|----------------------------|----------------------------------|---------------|-------------------|
| Frontend                   | `avionica_frontend`              | **5173**      | Vue.js + Vite     |
| Backend Gateway            | `avionica_backend_gateway`       | **8080**      | Spring Boot       |
| PostgreSQL                 | `avionica_postgres`              | 5432          | PostgreSQL 17     |
| Kafka                      | `avionica_kafka`                 | 9092          | Apache Kafka 4    |
| MQTT Broker                | `avionica_mqtt_broker`           | **1883**      | Mosquitto 2       |
| FMS API                    | `avionica_fms_api`               | —             | Python 3.11       |
| Sensor de Voo              | `avionica_sensor_flight`         | —             | Python 3.11       |
| Sensor de Freio            | `avionica_sensor_brake`          | —             | Python 3.11       |
| Radar                      | `avionica_radar`                 | —             | Python 3.11       |
| Computador de Navegação    | `avionica_navigation_computer`   | —             | Python 3.11       |
| Computador de Automação    | `avionica_automation_computer`   | —             | Python 3.11       |
| Líder WAIC                 | `avionica_waic_leader`           | —             | Python 3.11       |

> Portas em **negrito** são acessíveis diretamente pelo navegador ou ferramentas externas.
