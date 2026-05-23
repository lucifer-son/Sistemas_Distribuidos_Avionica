# Como Rodar o Projeto Apos Clonar o Repositorio

Este guia descreve o passo a passo para preparar e executar a primeira versao distribuida do projeto de avionica.

## 1. Pre-requisitos

Antes de rodar o projeto, a maquina precisa ter:

- Git
- Docker Desktop
- Java 25
- Node.js
- npm
- Python 3

Observacao sobre Gradle: nao e necessario instalar o Gradle manualmente. O projeto usa Gradle Wrapper, ou seja, os arquivos `backend/gradlew` e `backend/gradlew.bat` ficam versionados no repositorio e baixam a versao correta do Gradle automaticamente na primeira execucao.

### 1.1 Instalacao no Windows com Chocolatey

O Chocolatey e um gerenciador de pacotes para Windows. Com ele, da para instalar Git, Java, Node.js, Python e outras ferramentas usando comandos no terminal.

Passo a passo simples:

1. Abra o menu iniciar.
2. Pesquise por `PowerShell`.
3. Clique com o botao direito.
4. Escolha `Executar como administrador`.
5. Copie e cole o comando abaixo:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

Depois que terminar:

1. Feche o PowerShell.
2. Abra o PowerShell novamente.
3. Rode:

```powershell
choco --version
```

Se aparecer uma versao, o Chocolatey foi instalado corretamente.

Agora instale os pre-requisitos do projeto:

```powershell
choco install git -y
choco install docker-desktop -y
choco install openjdk --version=25.0.1 -y
choco install nodejs-lts -y
choco install python -y
```

Depois da instalacao, reinicie o terminal. No caso do Docker Desktop, abra o aplicativo pelo menu iniciar e aguarde ele ficar ativo.

Se o pacote `openjdk` nao oferecer Java 25 na sua maquina, instale Java 25 manualmente e confirme com `java --version`.

### 1.2 Validar instalacoes

Na raiz do projeto, rode:

```bash
git --version
docker --version
docker compose version
java --version
node --version
npm --version
python --version
```

Valide tambem o Gradle Wrapper do projeto:

```powershell
cd backend
.\gradlew.bat --version
cd ..
```

No Linux/macOS:

```bash
cd backend
./gradlew --version
cd ..
```

Se esse comando funcionar, o Gradle Wrapper esta pronto para gerenciar as dependencias do backend.

## 2. Clonar o Repositorio

```bash
git clone <url-do-repositorio>
cd Sistemas_Distribuidos_Avionica
```

## 3. Configurar Variaveis de Ambiente

Copie o arquivo de exemplo:

```bash
copy .env.example .env
```

No Linux/macOS:

```bash
cp .env.example .env
```

Abra o arquivo `.env` e configure a chave do FMS:

```env
FMS_API_KEY=sua_chave_da_api_aqui
```

As demais variaveis ja possuem valores de desenvolvimento:

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
```

Importante: o arquivo `.env` nao deve ser enviado para o Git.

## 4. Validar o Backend

Entre na pasta do backend:

```bash
cd backend
```

Execute o build pelo Gradle Wrapper:

```bash
.\gradlew.bat build
```

No Linux/macOS:

```bash
./gradlew build
```

Volte para a raiz:

```bash
cd ..
```

## 5. Validar o Frontend

Entre na pasta do frontend:

```bash
cd frontend
```

Instale as dependencias:

```bash
npm ci
```

Gere o build:

```bash
npm run build
```

Volte para a raiz:

```bash
cd ..
```

## 6. Validar os Modulos Python

Na raiz do projeto:

```bash
python -m compileall Software_Aviao
```

Esse comando verifica se os arquivos Python possuem erro de sintaxe.

## 7. Subir a Aplicacao com Docker Compose

Na raiz do projeto:

```bash
docker compose up --build
```

Para rodar em segundo plano:

```bash
docker compose up --build -d
```

Na primeira execucao, o Docker pode demorar porque precisa baixar imagens e construir os containers.

Recomendacao para o dia a dia: use `-d` para deixar os containers em segundo plano e veja apenas os logs do servico que voce quer investigar.

## 8. Acessar os Servicos

Depois que os containers subirem, acesse:

- Frontend Web: http://localhost:5173
- Backend Health Check: http://localhost:8080/api/health
- Lista de Modulos: http://localhost:8080/api/modules
- PostgreSQL: localhost:5432
- Kafka: `kafka:9092`, acessivel internamente pelos containers
- MQTT temporario: localhost:1883

## 9. Verificar Containers e Logs

Listar containers:

```bash
docker compose ps
```

Ver logs de todos os servicos:

```bash
docker compose logs -f
```

Ver logs de um servico especifico:

```bash
docker compose logs -f backend-gateway
docker compose logs -f frontend
docker compose logs -f fms-api
```

Ver apenas as ultimas linhas de log:

```bash
docker compose logs --tail=80 backend-gateway
docker compose logs --tail=80 frontend
docker compose logs --tail=80 kafka
```

Para acompanhar os modulos Python sem misturar com Kafka e PostgreSQL:

```bash
docker compose logs -f fms-api sensor-flight sensor-brake radar
```

## 10. Parar a Aplicacao

Parar os containers:

```bash
docker compose down
```

Parar e apagar os volumes locais, incluindo dados do PostgreSQL:

```bash
docker compose down -v
```

## 11. Fluxo Esperado Nesta Primeira Versao

Nesta primeira execucao, o objetivo e validar que a base distribuida sobe corretamente:

1. PostgreSQL sobe como infraestrutura de banco.
2. Kafka sobe como middleware de mensagens planejado.
3. MQTT local sobe temporariamente para os modulos Python atuais.
4. Backend Spring Boot sobe em `localhost:8080`.
5. Frontend Vue.js sobe em `localhost:5173`.
6. FMS e sensores Python sobem em containers.
7. A tela web consegue consultar `/api/health` e `/api/modules`.

## 12. Problemas Comuns

### Docker nao esta aberto

Abra o Docker Desktop e tente novamente:

```bash
docker compose up --build
```

### Porta ocupada

Se alguma porta estiver em uso, verifique:

- `5173`: frontend
- `8080`: backend
- `5432`: PostgreSQL
- `1883`: MQTT

### Kafka mostra `InvalidReceiveException`

Se aparecer um erro parecido com:

```text
Invalid receive (size = 1195725856 larger than 104857600)
```

isso normalmente significa que alguem tentou acessar o Kafka pelo navegador ou por HTTP, por exemplo `http://localhost:9092`.

Kafka nao usa HTTP na porta `9092`; ele usa protocolo proprio. Portanto, nao abra essa porta no navegador.

Nesta primeira versao, o Kafka fica disponivel apenas dentro da rede Docker pelo endereco:

```text
kafka:9092
```

O backend usa esse endereco automaticamente pela variavel `KAFKA_BOOTSTRAP_SERVERS`.

### Logs muito grandes no terminal

Prefira subir a aplicacao em segundo plano:

```bash
docker compose up --build -d
```

Depois consulte apenas o servico necessario:

```bash
docker compose logs -f backend-gateway
docker compose logs -f frontend
docker compose logs -f fms-api
```

O projeto tambem reduz o ruido padrao de Kafka, Mosquitto, Spring Boot e Python para deixar a primeira execucao mais legivel.

### Gradle demora na primeira execucao

Na primeira vez, o Gradle Wrapper baixa a distribuicao do Gradle e as dependencias do Spring Boot.

### npm mostra vulnerabilidades

O npm pode mostrar alertas de auditoria. Para a primeira execucao, o mais importante e o comando `npm run build` finalizar com sucesso. A correcao de auditoria deve ser analisada separadamente para evitar quebrar versoes do frontend.

### Frontend acusa erro de binding nativo do Vite/Rolldown

Se aparecer erro parecido com `Cannot find native binding` ou `@rolldown/binding-linux-x64-musl`, reconstrua a imagem do frontend sem cache:

```bash
docker compose build --no-cache frontend
docker compose up frontend
```

Esse erro acontece quando dependencias instaladas no Windows sao copiadas indevidamente para dentro do container Linux. O arquivo `frontend/.dockerignore` evita esse problema ignorando `node_modules/`, `dist/` e caches locais.
