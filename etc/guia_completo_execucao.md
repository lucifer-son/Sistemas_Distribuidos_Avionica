# 🚀 Guia Completo: Como Rodar, Buildar e Subir o Projeto

Este guia une o passo a passo para preparar, compilar e executar todos os serviços do sistema aviônico distribuído via Docker, desde a clonagem do repositório até a criação do banco de dados.

---

## 📋 1. Pré-requisitos

Antes de rodar o projeto, a máquina precisa ter:

- Git
- Docker Desktop (versão 24+)
- Docker Compose (v2+)
- Java JDK 25
- Node.js (LTS) e npm
- Python 3.11+

> [!IMPORTANT]
> O **Docker Desktop precisa estar rodando** antes de executar qualquer comando do Docker abaixo.
> Para verificar: abra o Docker Desktop e aguarde o ícone ficar ativo/verde.

### 1.1 Instalação no Windows (Recomendado via Chocolatey)

Se você utiliza o Windows, o [Chocolatey](https://chocolatey.org/) facilita muito a instalação de todos os requisitos de uma vez.

**Passo 1: Instalar o próprio Chocolatey (se você ainda não tiver)**
Abra o **PowerShell como Administrador** e rode o comando abaixo:
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```
Depois que o comando terminar, feche a tela e abra o **PowerShell como Administrador novamente**. Para validar se o Choco instalou corretamente, digite:
```powershell
choco --version
```

**Passo 2: Utilizar o Choco para instalar os pré-requisitos do projeto**
Com o Choco funcionando, rode os seguintes comandos no terminal para que ele instale o Git, Docker, Java, Node e Python:
```powershell
choco install git -y
choco install docker-desktop -y
choco install openjdk --version=25.0.1 -y
choco install nodejs-lts -y
choco install python -y
```

Após instalar tudo, feche o PowerShell e abra o terminal de sua preferência. Valide as instalações executando:
```bash
git --version
docker --version
docker compose version
java --version
node --version
python --version
```

*(O projeto usa o Gradle Wrapper, então você não precisa instalar o Gradle manualmente).*

---

## 📥 2. Clonar o Repositório

```bash
git clone <url-do-repositorio>
cd Sistemas_Distribuidos_Avionica
```

### 2.1 Configuração da IDE (IntelliJ ou VS Code)

#### 🔸 Se você usa IntelliJ IDEA:
Se o IntelliJ não reconhecer o código Java logo de cara, siga este passo:
1. No painel de arquivos da IDE, navegue até a pasta `backend/`.
2. Clique com o **botão direito** em cima do arquivo `C:\projetos\Sistemas_Distribuidos_Avionica\backend\settings.gradle` (ou `build.gradle`).
3. Selecione a opção **"Link Gradle Project"** (ou "Add as Gradle Project").
4. Aguarde a IDE baixar as dependências e sincronizar as pastas corretamente.

#### 🔸 Se você usa VS Code:
Para que o VS Code reconheça o backend Java e o Gradle corretamente:
1. Instale a extensão **Extension Pack for Java** (fornecida pela Microsoft).
2. Abra a pasta raiz do projeto (`Sistemas_Distribuidos_Avionica`) no VS Code.
3. Normalmente, um aviso aparecerá no canto inferior direito dizendo _"Importing Gradle project"_. Se perguntar se deseja importar, clique em **"Yes"** (ou "Always allow").
4. Caso o Java ainda não seja reconhecido, tente abrir diretamente a pasta `C:\projetos\Sistemas_Distribuidos_Avionica\backend` em uma nova janela do VS Code para forçar o carregamento focado no Gradle.

---

## ⚙️ 3. Configurar Variáveis de Ambiente

O projeto usa um arquivo `.env` na raiz para configurar senhas e URLs. Ele **não é versionado no Git** por segurança.

```powershell
# No Windows:
copy .env.example .env

# No Linux/macOS:
cp .env.example .env
```

O `.env` gerado já vem com valores padrão que funcionam localmente para rodar o PostgreSQL, Kafka e MQTT.
**Não é necessário alterar nada para rodar localmente**, exceto o `FMS_API_KEY` se quiser usar o cálculo real de rotas (da API Ninjas).

---

## 🛠️ 4. Validar o Código (Opcional, mas recomendado)

Para garantir que tudo está ok antes de colocar no Docker, você pode compilar localmente:

### 4.1 Backend (Java)
```powershell
cd backend
# Compilar e gerar o JAR
.\gradlew.bat build --no-daemon
cd ..
```
*(No Linux/macOS use `./gradlew build`)*

### 4.2 Frontend (Vue.js)
```powershell
cd frontend
npm ci
npm run build
cd ..
```

### 4.3 Python (Sensores e FMS)
```powershell
python -m compileall Software_Aviao
```

---

## 🐳 5. Subir a Aplicação com Docker Compose

Este é o comando principal para subir o sistema completo (11 serviços, incluindo banco de dados, frontend, backend, Kafka, MQTT e módulos Python):

```powershell
# Na raiz do projeto:
docker compose up --build
```
> O `--build` força o Docker a recompilar as imagens.

Para rodar em **segundo plano** (sem travar o terminal):
```powershell
docker compose up --build -d
```

> [!NOTE]
> Na **primeira execução**, o Docker pode levar de 5 a 10 minutos baixando dependências e compilando as imagens (especialmente o Backend e o Frontend).

---

## 🗄️ 6. Subir o Schema de Banco de Dados (`schema.sql`) no Docker

Com os containers rodando, é necessário criar as tabelas no PostgreSQL. O arquivo de esquema do banco de dados encontra-se em `infra/db/schema.sql`.

Para aplicar este esquema diretamente no container do banco de dados (`avionica_postgres`), execute o seguinte comando na raiz do projeto:

No **PowerShell** (o padrão no Windows), o operador `<` não é suportado diretamente. O comando correto é ler o arquivo primeiro e enviá-lo para o Docker através de um "pipe" (`|`):

```powershell
Get-Content infra\db\schema.sql | docker exec -i avionica_postgres psql -U avionica -d avionica
```

*(Se você estiver usando **Linux, macOS ou o Prompt de Comando/CMD** tradicional do Windows, você pode usar o redirecionamento clássico:*
```bash
docker exec -i avionica_postgres psql -U avionica -d avionica < infra/db/schema.sql
```
*)*

**Explicação do comando:**
- `docker exec -i avionica_postgres`: Executa um comando interativo no container do banco de dados.
- `psql -U avionica -d avionica`: Chama o utilitário PostgreSQL logando com o usuário `avionica` no banco de dados `avionica`.
- `Get-Content` (ou `<`): Lê o arquivo SQL local e injeta o seu conteúdo para ser executado dentro do banco.

---

## 🌐 7. Acessar os Serviços

Após subir e configurar o banco, abra os endereços no navegador para validar:

| Serviço/Interface | URL de Acesso | O que deve aparecer |
|-------------------|---------------|---------------------|
| **Frontend Web** | `http://localhost:5173` | Interface visual (Vue.js) do projeto |
| **Backend Health** | `http://localhost:8080/api/health` | Status UP indicando saúde do gateway |
| **Lista de Módulos**| `http://localhost:8080/api/modules` | JSON listando todos os módulos |
| **Dados Aviônicos**| `http://localhost:8080/api/aircraft-data` | Telemetria (JSON) em tempo real |
| **PostgreSQL** | `localhost:5432` | Conexão para ferramentas de banco (DBeaver, pgAdmin) |
| **MQTT Broker** | `localhost:1883` | Conexão para clientes MQTT |

---

## 🔎 8. Comandos Úteis do Dia a Dia

```powershell
# Ver status de todos os containers
docker compose ps

# Ver logs de um serviço específico em tempo real
docker compose logs -f backend-gateway
docker compose logs -f frontend
docker compose logs -f fms-api

# Parar tudo (sem apagar os dados do banco)
docker compose stop

# Parar e remover os containers (mantém volumes)
docker compose down

# Parar, remover containers E apagar todos os dados do banco (Limpeza total)
docker compose down -v
```

### Rebuild Rápido (Se você alterar código)
- **Backend:** `docker compose up --build backend-gateway`
- **Sensores Python:** `docker compose up --build sensor-flight`
- **Frontend:** Possui hot-reload, não precisa recompilar a menos que mude o `package.json`!

---

## ❌ 9. Problemas Comuns e Soluções

### Kafka mostra `InvalidReceiveException`
Significa que você tentou acessar `http://localhost:9092` pelo navegador. O Kafka usa um protocolo próprio, não abra essa porta no navegador.

### Backend não conecta ao MQTT (`Nao foi possivel conectar ao MQTT`)
Na primeira vez, o backend sobe mais rápido que o MQTT. Ele tem reconexão automática, aguarde de 10 a 15 segundos que a conexão será reestabelecida.

### Frontend acusa erro de binding nativo (Rolldown/Vite)
Se acontecer um erro tipo `Cannot find native binding` no Linux/Docker de algo instalado no Windows, recrie o container limpo:
```powershell
docker compose build --no-cache frontend
docker compose up -d frontend
```
