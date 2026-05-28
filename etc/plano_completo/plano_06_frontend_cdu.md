# 🖥️ Plano 06 — Frontend: Estado Atual, Casos de Uso e Roadmap

> **Sistema:** Gateway Tolerante a Falhas para Redes Aviônicas Híbridas (AFDX/WAIC)  
> **Frontend atual:** Vue 3 + Vite + Bootstrap 5 + Axios  
> **Tecnologia final:** A decidir — Vue 3 / React 19 / Angular 19  
> **Data da análise:** Maio de 2026

---

## 📊 Estado Atual do Frontend

### O que existe hoje

O frontend atual é uma **única página** (`App.vue`) com:
- 1 navbar com badge de status do backend
- 8 cards de dados (`DataCard.vue`) exibindo o último valor de cada tópico MQTT
- 1 tabela de mensagens brutas do barramento
- Polling HTTP a cada 2 segundos via `setInterval`
- Bootstrap 5 para estilização
- 55 linhas de CSS próprio (fundo cinza claro, cards brancos)

### O que falta

| Funcionalidade | Status |
|---|---|
| Alertas com severidade visual | ❌ Ausente |
| Painel de comandos (velocidade, proa, rota) | ❌ Ausente |
| Gráficos históricos de telemetria | ❌ Ausente |
| Saúde dos módulos Docker | ❌ Ausente |
| Autenticação/autorização | ❌ Ausente |
| Tempo real via WebSocket/SSE | ❌ Ausente (usa polling) |
| Múltiplas telas / roteamento | ❌ Ausente |
| Design sistema aviônico (dark mode, HUD) | ❌ Ausente |
| Responsividade testada | ❌ Não validada |

---

## ⚖️ Comparativo de Tecnologia: Vue vs React vs Angular

> **Resumo da recomendação:** Para este projeto, **Vue 3** ou **React 19** são as escolhas mais práticas. Angular tem overhead de configuração desnecessário para o escopo atual.

| Critério | Vue 3 | React 19 | Angular 19 |
|---|---|---|---|
| **Curva de aprendizado** | 🟢 Baixa | 🟡 Média | 🔴 Alta |
| **Já instalado no projeto** | ✅ Sim | ❌ Não | ❌ Não |
| **Tamanho do bundle** | 🟢 ~34KB | 🟡 ~45KB | 🔴 ~130KB |
| **Velocidade de setup** | 🟢 Rápido | 🟢 Rápido | 🔴 Lento |
| **Ecosistema de gráficos** | Chart.js / ApexCharts | Recharts / Victory | ngx-charts |
| **TypeScript nativo** | Opcional (suporta bem) | Opcional | Obrigatório |
| **Gerenciamento de estado** | Pinia | Zustand / Redux | NgRx / Services |
| **WebSocket/SSE** | Composition API | Hooks | RxJS (nativo) |
| **Mercado de trabalho BR** | 🟡 Médio | 🟢 Alto | 🟡 Médio |
| **Adequado para dashboards** | 🟢 Excelente | 🟢 Excelente | 🟢 Bom |

### 🗳️ Orientação para a decisão

- **Escolha Vue 3** se a equipe já tem familiaridade com Vue ou prioriza velocidade de desenvolvimento
- **Escolha React 19** se a equipe visa empregabilidade no mercado ou quer o maior ecossistema de componentes
- **Escolha Angular 19** apenas se a equipe já trabalha com Angular e quer o RxJS nativo para WebSocket

> **Independente da escolha:** Os Casos de Uso, a arquitetura de telas e os requisitos funcionais descritos neste plano se aplicam igualmente às 3 tecnologias.

---

## 👤 Perfis de Usuário (Atores)

Antes dos casos de uso, é fundamental definir quem usa o sistema:

| Ator | Papel | O que pode fazer |
|---|---|---|
| **Operador de Voo** | Monitora a aeronave em tempo real | Visualizar telemetria, receber alertas, acompanhar rota |
| **Controlador** | Envia comandos para a aeronave | Tudo do Operador + enviar comandos de velocidade, proa, rota |
| **Instrutor** | Testa o sistema com falhas simuladas | Tudo do Controlador + injetar falhas (TCAS, EGPWS, motor) |
| **Administrador** | Gerencia a infraestrutura | Tudo dos outros + ver saúde dos módulos Docker |

---

## 📋 Casos de Uso (CDU)

> Cada caso de uso descreve **o que o usuário faz passo a passo** na interface.

---

### CDU-01 — Visualizar Painel de Telemetria em Tempo Real

**Ator:** Operador de Voo  
**Pré-condição:** Sistema com containers Docker rodando; backend e sensores ativos  
**Pós-condição:** Operador vê os dados atualizados da aeronave  

**Fluxo principal:**
1. Operador acessa a URL do sistema (`http://localhost:5173`)
2. O sistema exibe a tela de dashboard principal
3. O sistema conecta automaticamente via WebSocket (ou polling SSE) ao backend
4. O painel exibe cards de telemetria para: **Voo**, **Freios**, **Radar**, **FMS**, **Navegação**, **Motor WAIC**, **Anti-Ice**, **Alertas**
5. Cada card atualiza seu valor automaticamente ao receber nova leitura
6. O operador visualiza altitude, velocidade Mach, combustível, proa, ETA e demais métricas
7. Um indicador de tempo mostra quando foi a última atualização recebida

**Fluxo alternativo — backend offline:**
- 3a. O sistema não consegue conectar ao backend
- 3b. O sistema exibe um banner "Backend offline — tentando reconectar..."
- 3c. O sistema tenta reconectar automaticamente a cada 5 segundos
- 3d. Quando o backend voltar, o banner some e os dados são carregados

**Fluxo alternativo — sensor sem dados:**
- 5a. Um tópico MQTT não enviou dados nos últimos 10 segundos
- 5b. O card correspondente exibe "Aguardando dados..." com indicador de inatividade

---

### CDU-02 — Visualizar e Gerenciar Alertas

**Ator:** Operador de Voo  
**Pré-condição:** Sistema operacional; ao menos um alerta foi gerado  
**Pós-condição:** Operador viu e reconheceu os alertas ativos  

**Fluxo principal:**
1. Operador clica na aba **"Alertas"** na barra de navegação lateral
2. O sistema exibe a tela de alertas com lista de alertas ativos (não resolvidos)
3. Cada alerta exibe: **tipo**, **descrição**, **severidade** (badge colorido: INFO=azul, WARNING=amarelo, CRITICAL=vermelho piscante), **horário** e **origem**
4. O contador de alertas críticos fica visível na navbar em todas as telas
5. Operador clica em um alerta para ver os detalhes em um modal
6. Operador clica em **"Reconhecer Alerta"** para marcá-lo como resolvido
7. O sistema chama `PATCH /api/alertas/{id}/resolver`
8. O alerta sai da lista de ativos e vai para o histórico

**Fluxo alternativo — novo alerta CRITICAL chega:**
- 4a. Enquanto o operador está em qualquer tela, chega um alerta CRITICAL
- 4b. O sistema exibe um toast de notificação na parte superior da tela
- 4c. O badge contador na navbar pisca em vermelho
- 4d. O operador pode clicar no toast para ir direto à tela de alertas

**Regras de negócio:**
- Alertas `CRITICAL` não podem ser resolvidos sem confirmação (modal de confirmação adicional)
- O sistema deve emitir um som de alerta (beep) quando chegar um `CRITICAL`
- Alertas resolvidos ficam disponíveis na aba "Histórico" com filtros por data

---

### CDU-03 — Visualizar Histórico Gráfico de Telemetria

**Ator:** Operador de Voo  
**Pré-condição:** Banco de dados com registros de telemetria (Plano 01 + 02 implementados)  
**Pós-condição:** Operador visualizou a tendência de um sensor ao longo do tempo  

**Fluxo principal:**
1. Operador clica na aba **"Histórico"** na barra de navegação
2. O sistema exibe a tela de histórico com seletor de sensor e intervalo de tempo
3. Operador seleciona o sensor desejado (ex: **Combustível**, **Altitude**, **Mach**)
4. Operador seleciona o intervalo de tempo: Últimos 5min / 15min / 1h / 24h
5. O sistema consulta `GET /api/telemetria/voo?from=...&to=...`
6. O sistema renderiza um gráfico de linha com os valores no eixo Y e o tempo no eixo X
7. Operador passa o mouse sobre o gráfico e vê o valor exato no tooltip
8. Operador pode baixar os dados como CSV clicando em **"Exportar"**

**Fluxo alternativo — sem dados no intervalo:**
- 6a. Nenhum dado foi encontrado no período selecionado
- 6b. O sistema exibe: "Nenhum dado registrado neste período. Selecione outro intervalo."

---

### CDU-04 — Definir Rota no FMS (Flight Management System)

**Ator:** Controlador  
**Pré-condição:** Sistema operacional; FMS distribuído ativo (`fms_distribuido.py`)  
**Pós-condição:** Nova rota calculada e transmitida para o sistema  

**Fluxo principal:**
1. Controlador acessa a aba **"FMS / Rota"**
2. O sistema exibe o painel FMS com a rota atual (origem, destino, distância, ETA)
3. Controlador preenche o campo **"Aeroporto de Origem"** com o código ICAO (ex: `SBGR`)
4. Controlador preenche o campo **"Aeroporto de Destino"** com o código ICAO (ex: `EGLL`)
5. O sistema valida os campos: aceita apenas 4 letras maiúsculas
6. Controlador clica em **"Calcular Rota"**
7. O sistema chama `POST /api/comandos/rota` com `{ "origem": "SBGR", "destino": "EGLL" }`
8. O backend publica no tópico MQTT `avionica/comandos/rota`
9. O `fms_distribuido.py` recebe o comando, consulta a API Ninjas e calcula a rota
10. O card de FMS na tela atualiza com a nova rota, distância e ETA

**Fluxo alternativo — ICAO inválido:**
- 5a. Controlador digita um código ICAO inexistente (ex: `XXXX`)
- 5b. O backend retorna erro após tentar a API Ninjas
- 5c. O sistema exibe: "Aeroporto não encontrado. Verifique o código ICAO e tente novamente."

**Fluxo alternativo — sem FMS_API_KEY:**
- 9a. A API Ninjas retorna erro por chave inválida ou ausente
- 9b. O sistema exibe: "FMS sem conexão com API externa. Usando banco de aeroportos local."
- 9c. Se o ICAO estiver no banco local (SBGR, EGLL, KJFK, etc.), a rota é calculada normalmente

---

### CDU-05 — Controlar Velocidade da Aeronave (Autothrottle)

**Ator:** Controlador  
**Pré-condição:** Sensores de voo ativos (`sensores_voo.py`); controlador autenticado  
**Pós-condição:** Comando de velocidade transmitido; sensor aplica novo Mach após 3 segundos  

**Fluxo principal:**
1. Controlador acessa o painel de **"Comandos"** (aba dedicada ou seção no dashboard)
2. O sistema exibe o controle de velocidade com o valor Mach atual (ex: `0.80 Mach`)
3. Controlador visualiza um slider de velocidade com range de `0.40` a `1.00` Mach
4. Controlador move o slider para a velocidade desejada (ex: `0.85 Mach`)
5. O valor alvo é exibido em destaque: `TARGET: 0.85 M`
6. Controlador clica em **"Enviar Comando"** (ou confirma automaticamente após 1s de inatividade no slider)
7. O sistema exibe confirmação: "Comando enviado. Aguardando resposta dos motores (~3s)..."
8. O sistema chama `POST /api/comandos/velocidade` com `{ "nova_velocidade": 0.85 }`
9. Após ~3 segundos, o card de Voo atualiza mostrando o Mach real se aproximando de `0.85`
10. O sistema confirma: "Velocidade atualizada para 0.85 Mach"

**Regras de negócio:**
- O botão "Enviar Comando" só fica habilitado se o novo valor for diferente do atual
- Confirmação adicional se a variação for maior que 0.10 Mach (mudança abrupta)
- O sistema registra o horário e o valor de cada comando enviado (log de ações)

---

### CDU-06 — Ajustar Proa (Heading) da Aeronave

**Ator:** Controlador  
**Pré-condição:** Computador de navegação ativo; backend operacional  
**Pós-condição:** Novo heading transmitido ao `computador_navegacao.py`  

**Fluxo principal:**
1. Controlador acessa o painel de **"Comandos"**
2. O sistema exibe a proa atual com a bússola digital (indicador circular) — ex: `270°`
3. Controlador vê os controles de proa: botões `◄ 5°` / `◄ 1°` / `1° ►` / `5° ►`
4. Controlador clica em `1° ►` para aumentar 1 grau por vez
5. O valor alvo é atualizado em tempo real: `SEL: 271°`
6. Controlador clica em **"Confirmar Proa"**
7. O sistema chama `POST /api/comandos/proa` com `{ "nova_proa": 271 }`
8. O backend publica em `avionica/comandos/proa`
9. O card de Navegação atualiza com a nova proa recebida do `computador_navegacao.py`

---

### CDU-07 — Injetar Falha (Painel do Instrutor)

**Ator:** Instrutor  
**Pré-condição:** Instrutor autenticado com papel "INSTRUTOR"; sistema rodando  
**Pós-condição:** Falha simulada transmitida e visível nos alertas  

**Fluxo principal:**
1. Instrutor acessa a aba **"Painel do Instrutor"** (visível apenas para o papel INSTRUTOR)
2. O sistema exibe o painel com os botões de injeção de falha:
   - **"Simular Tráfego (TCAS)"** — alerta de tráfego aéreo
   - **"Simular Terreno (EGPWS)"** — alerta de colisão com terreno
   - **"Falha no Motor"** — falha catastrófica de motor
   - **"Sabotagem Sensor B (Falha Bizantina)"** — corrompe o sensor B do TMR
3. Instrutor clica em **"Falha no Motor"**
4. O sistema exibe modal de confirmação: "Tem certeza? Isso gerará um alerta CRITICAL no sistema."
5. Instrutor confirma clicando em **"Confirmar Injeção"**
6. O sistema chama `POST /api/comandos/falhas` com `{ "tipo": "motor" }`
7. O backend publica em `avionica/comandos/falhas`
8. O `injetor_falhas.py` recebe e propaga a falha
9. Um alerta CRITICAL aparece instantaneamente na tela de alertas
10. A navbar pisca em vermelho com o contador de alertas críticos

**Fluxo alternativo — Sabotagem Byzantina:**
- 3a. Instrutor clica em "Sabotagem Sensor B"
- 3b. O sistema publica em `avionica/comandos/falhas/sensor_B`
- 3c. O `sensor_motor.py` instância B começa a publicar `pressao: 0.0`
- 3d. O `consenso_motor.py` detecta o valor discrepante e gera log de "Falha Bizantina detectada"
- 3e. No painel do instrutor, uma mensagem confirma: "Sensor B corrompido. Monitor do TMR ativo."

---

### CDU-08 — Monitorar Saúde dos Módulos do Sistema

**Ator:** Administrador  
**Pré-condição:** Backend operacional com endpoint `/api/modules`  
**Pós-condição:** Administrador visualizou o status de todos os containers  

**Fluxo principal:**
1. Administrador acessa a aba **"Infraestrutura"**
2. O sistema chama `GET /api/modules`
3. O sistema exibe um grid de módulos com badges de status:
   - 🟢 **UP** — container rodando e respondendo
   - 🟡 **PLANNED** — módulo previsto mas não implementado
   - ⚪ **INFRASTRUCTURE** — serviço de infraestrutura (Kafka, PostgreSQL)
   - 🔴 **DOWN** — container parou inesperadamente
4. Administrador clica em um módulo para ver detalhes (versão, porta, uptime)
5. O sistema atualiza os status a cada 10 segundos automaticamente

---

### CDU-09 — Visualizar Log do Barramento MQTT

**Ator:** Operador de Voo / Administrador  
**Pré-condição:** Sistema operacional; mensagens sendo recebidas  
**Pós-condição:** Operador analisou as mensagens do barramento  

**Fluxo principal:**
1. Operador acessa a aba **"Barramento MQTT"** (ou seção na tela principal)
2. O sistema exibe uma tabela com as últimas mensagens recebidas
3. Cada linha mostra: horário, tópico MQTT, payload JSON formatado
4. Operador usa o filtro de tópico (dropdown) para ver apenas mensagens de um sensor
5. O operador pode expandir um payload JSON para ver os dados formatados com indentação
6. Operador ativa o modo **"Live"** — novas mensagens aparecem no topo automaticamente
7. Operador desativa o modo Live para "congelar" a lista e analisar uma mensagem

---

### CDU-10 — Autenticar-se no Sistema

**Ator:** Qualquer usuário  
**Pré-condição:** Usuário com credenciais cadastradas  
**Pós-condição:** Usuário autenticado com papel correto e redirecionado ao dashboard  

**Fluxo principal:**
1. Usuário acessa a URL do sistema
2. O sistema detecta que não há sessão ativa e redireciona para `/login`
3. A tela de login exibe campos **"Usuário"** e **"Senha"** com o logo do sistema
4. Usuário preenche as credenciais e clica em **"Entrar"**
5. O sistema chama `POST /api/auth/login`
6. O backend retorna um JWT token
7. O sistema armazena o token e redireciona para `/dashboard`
8. A navbar exibe o nome do usuário e seu papel (badge: OPERADOR / CONTROLADOR / INSTRUTOR / ADMIN)

**Fluxo alternativo — credenciais inválidas:**
- 6a. O backend retorna `401 Unauthorized`
- 6b. O sistema exibe: "Credenciais inválidas. Verifique usuário e senha."
- 6c. O campo de senha é limpo automaticamente

**Regras de negócio:**
- Abas e funcionalidades são exibidas conforme o papel do usuário:
  - OPERADOR: Dashboard, Alertas, Histórico, Barramento
  - CONTROLADOR: tudo do OPERADOR + Comandos, FMS
  - INSTRUTOR: tudo do CONTROLADOR + Painel do Instrutor
  - ADMINISTRADOR: tudo do INSTRUTOR + Infraestrutura

---

## 🗂️ Arquitetura de Telas — Mapa de Navegação

```
/login
  └── (autenticação) ──► /dashboard (tela inicial)

/dashboard
  ├── Navbar fixa com: logo | abas | badge de alertas | usuário
  │
  ├── /dashboard          ← CDU-01: Telemetria em tempo real
  │     ├── Cards de telemetria (8 cards)
  │     ├── Controles rápidos de velocidade e proa (CDU-05, CDU-06)
  │     └── Tabela de barramento (CDU-09)
  │
  ├── /alertas            ← CDU-02: Gerenciamento de alertas
  │     ├── Lista de alertas ativos
  │     ├── Modal de detalhes / resolução
  │     └── Aba histórico com filtros
  │
  ├── /historico          ← CDU-03: Gráficos históricos
  │     ├── Seletor de sensor e período
  │     └── Gráfico de linha + botão exportar CSV
  │
  ├── /comandos           ← CDU-05, CDU-06: Controles da aeronave
  │     ├── Controle de velocidade (slider Mach)
  │     └── Controle de proa (bússola + botões)
  │
  ├── /fms                ← CDU-04: Flight Management System
  │     ├── Rota atual (card)
  │     └── Formulário de nova rota
  │
  ├── /instrutor          ← CDU-07: Injeção de falhas (só INSTRUTOR)
  │     ├── Botões de falha com confirmação
  │     └── Log de falhas injetadas nesta sessão
  │
  └── /infra              ← CDU-08: Saúde dos módulos (só ADMIN)
        └── Grid de módulos Docker com status
```

---

## 🧱 Arquitetura de Componentes — Independente de Framework

Esta estrutura se aplica a Vue, React ou Angular (nomes dos arquivos mudam, lógica é a mesma):

```
src/
├── pages/ (ou views/ no Vue, routes/ no Angular)
│   ├── DashboardPage
│   ├── AlertasPage
│   ├── HistoricoPage
│   ├── ComandosPage
│   ├── FmsPage
│   ├── InstrutorPage
│   ├── InfraPage
│   └── LoginPage
│
├── components/
│   ├── layout/
│   │   ├── AppNavbar          ← navbar com abas, badge de alertas, usuário
│   │   └── AppSidebar         ← alternativa: menu lateral
│   │
│   ├── telemetria/
│   │   ├── TelemetriaCard     ← card de dado (substitui DataCard.vue atual)
│   │   ├── TelemetriaGrid     ← grade dos 8 cards
│   │   └── BussoleIndicator   ← bússola digital de proa
│   │
│   ├── alertas/
│   │   ├── AlertaList         ← lista de alertas com badges
│   │   ├── AlertaItem         ← item individual com severidade
│   │   ├── AlertaModal        ← modal de detalhes e resolução
│   │   └── AlertaBadge        ← contador de críticos na navbar
│   │
│   ├── graficos/
│   │   ├── TelemetriaChart    ← gráfico de linha de histórico
│   │   └── ChartControls      ← seletor de sensor e período
│   │
│   ├── comandos/
│   │   ├── VelocidadeControl  ← slider de Mach
│   │   ├── ProaControl        ← botões de proa + bússola
│   │   └── ComandoConfirm     ← modal de confirmação de comando
│   │
│   ├── fms/
│   │   ├── RotaAtualCard      ← exibe rota, distância, ETA
│   │   └── RotaForm           ← formulário ICAO origem/destino
│   │
│   ├── instrutor/
│   │   ├── FalhaButton        ← botão de injeção com confirmação
│   │   └── FalhaLog           ← log de falhas da sessão
│   │
│   └── infra/
│       ├── ModuloGrid         ← grade de módulos Docker
│       └── ModuloCard         ← card de status de um módulo
│
├── services/ (ou api/)
│   ├── telemetriaService      ← GET /api/aircraft-data
│   ├── alertaService          ← GET, PATCH /api/alertas
│   ├── historicoService       ← GET /api/telemetria/*
│   ├── comandoService         ← POST /api/comandos/*
│   ├── fmsService             ← POST /api/comandos/rota
│   └── authService            ← POST /api/auth/login
│
├── store/ (estado global)
│   ├── telemetriaStore        ← dados ao vivo da aeronave
│   ├── alertaStore            ← alertas ativos + contador críticos
│   ├── authStore              ← usuário logado + token JWT
│   └── conexaoStore           ← status da conexão com backend
│
└── utils/
    ├── formatters             ← formatValue(), formatTime() (do App.vue atual)
    ├── unidades               ← mapeamento de unidades por campo
    └── websocket              ← cliente WebSocket/SSE para dados em tempo real
```

---

## 🎨 Diretrizes de Design

### Tema Visual — Aviation Dark Mode
O sistema é usado em ambientes de monitoramento. Dark mode é padrão em cockpits e centros de controle.

```
Paleta de cores sugerida:
  Fundo principal:    #0A0E1A  (azul-escuro profundo)
  Fundo painel:       #111827  (cinza-azulado escuro)
  Borda painel:       #1E2D42  (azul médio)
  Texto primário:     #E2E8F0  (branco suave)
  Texto secundário:   #64748B  (cinza)
  Accent azul:        #3B82F6  (azul elétrico)
  Verde OK:           #10B981  (verde esmeralda)
  Amarelo WARNING:    #F59E0B  (âmbar)
  Vermelho CRITICAL:  #EF4444  (vermelho)
  Cyan dados:         #06B6D4  (cyan — para valores numéricos)

Tipografia:
  UI geral:     Inter (Google Fonts)
  Dados numéricos: JetBrains Mono ou Roboto Mono (monospace para alinhamento)
```

### Comportamentos de UX obrigatórios

- **Atualização em tempo real:** Valores mudam suavemente com animação CSS `transition: 0.3s`
- **Highlight de mudança:** Quando um valor muda, o campo pisca brevemente em cyan por 1s
- **Status de conexão sempre visível:** Dot colorido na navbar (verde=online, vermelho=offline, amarelo=reconectando)
- **Toast de alertas:** Notificações não-bloqueantes que somem após 5s (exceto CRITICAL)
- **Responsividade:** Funcional em tablet (1024px) e desktop (1440px+); mobile é secundário

---

## 🔌 Comunicação com o Backend

### Situação atual (polling HTTP)
```
Frontend ──── GET /api/aircraft-data ────► Backend
         ◄─── JSON response ──────────────
                  (repete a cada 2s)
```
**Problema:** Polling gera requisições desnecessárias mesmo quando não há dados novos. Em 1 hora são 1.800 requisições.

### Melhorado: Server-Sent Events (SSE) — recomendado
```
Frontend ──── GET /api/events (SSE) ────► Backend
         ◄─── stream de eventos ──────────
              (backend empurra quando há novidade)
```
**Vantagem:** Conexão única, unidirecional, nativa HTTP — sem biblioteca extra.

### Ideal: WebSocket — para sistemas com comandos bidirecionais
```
Frontend ◄──── ws://backend/ws ──────────► Backend
              (bidirecional em tempo real)
```
**Vantagem:** Telemetria chega em push E comandos saem pela mesma conexão.
**Desvantagem:** Mais complexo de implementar no backend (Spring WebSocket ou STOMP).

> **Recomendação:** Implementar SSE primeiro (menor esforço), depois evoluir para WebSocket quando os comandos interativos estiverem prontos.

---

## 📦 Dependências por Framework

### Se Vue 3 (já instalado)
```json
{
  "dependencies": {
    "vue": "^3.5",
    "vue-router": "^4.6",
    "pinia": "^2.2",
    "axios": "^1.7",
    "chart.js": "^4.4",
    "vue-chartjs": "^5.3"
  }
}
```

### Se React 19 (nova instalação)
```json
{
  "dependencies": {
    "react": "^19.0",
    "react-dom": "^19.0",
    "react-router-dom": "^6.26",
    "zustand": "^4.5",
    "axios": "^1.7",
    "recharts": "^2.12"
  }
}
```

### Se Angular 19 (nova instalação)
```json
{
  "dependencies": {
    "@angular/core": "^19.0",
    "@angular/router": "^19.0",
    "@angular/forms": "^19.0",
    "@angular/common": "^19.0",
    "rxjs": "^7.8",
    "ngx-charts": "^20.0"
  }
}
```

---

## 🗓️ Ordem Sugerida de Implementação

| Fase | O que construir | CDUs cobertos |
|---|---|---|
| **Fase 1 — Base** | Design system (cores, tipografia, dark mode) + Navbar + estrutura de rotas | — |
| **Fase 2 — Dashboard** | Grid de telemetria redesenhado + cards animados + status de conexão | CDU-01 |
| **Fase 3 — Alertas** | Tela de alertas + badge na navbar + toast de notificação + resolução | CDU-02 |
| **Fase 4 — Tempo real** | Substituir polling por SSE ou WebSocket | CDU-01, 02 |
| **Fase 5 — Comandos** | Painel de velocidade (slider) + proa (bússola) + FMS (formulário) | CDU-04, 05, 06 |
| **Fase 6 — Histórico** | Gráficos de linha com Chart.js + filtros de período + exportar CSV | CDU-03 |
| **Fase 7 — Auth** | Tela de login + JWT + rotas protegidas + papéis de usuário | CDU-10 |
| **Fase 8 — Avançado** | Painel do Instrutor + tela de infraestrutura + barramento live | CDU-07, 08, 09 |
