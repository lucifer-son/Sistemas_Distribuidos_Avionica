<template>
  <main class="app-shell pb-5">
    <nav class="navbar navbar-expand-lg border-bottom">
      <div class="container-fluid px-4">
        <div>
          <span class="navbar-brand fw-semibold text-white mono">AVIONICA_DISTRIBUIDA v2.0</span>
          <span class="text-secondary small ms-2 mono d-none d-md-inline">| Glass Cockpit Edition</span>
        </div>
        <div class="d-flex align-items-center gap-3">
          <span class="badge status-badge" :class="health?.status === 'UP' ? 'green' : 'red'">
            Gateway: {{ health?.status || 'OFFLINE' }}
          </span>
          <button class="btn btn-sm btn-outline-light" type="button" @click="loadAll">
            Sincronizar
          </button>
        </div>
      </div>
    </nav>

    <header class="container-fluid px-4 pt-4">
      <ul class="nav nav-pills gap-2 border-bottom border-secondary pb-3 mb-4">
        <li class="nav-item">
          <button class="nav-link" :class="{ active: activeTab === 'sgca' }" @click="activeTab = 'sgca'">
            SGCA Cockpit
          </button>
        </li>
        <li class="nav-item">
          <button class="nav-link" :class="{ active: activeTab === 'torre' }" @click="activeTab = 'torre'">
            Torre de Comando
          </button>
        </li>
        <li class="nav-item">
          <button class="nav-link" :class="{ active: activeTab === 'kafka' }" @click="activeTab = 'kafka'">
            Monitor do Kafka
          </button>
        </li>
        <li class="nav-item">
          <button class="nav-link" :class="{ active: activeTab === 'banco' }" @click="activeTab = 'banco'">
            Visualizador de BD
          </button>
        </li>
      </ul>

      <div v-if="error" class="alert alert-danger mb-4 d-flex justify-content-between align-items-center" role="alert">
        <span>{{ error }}</span>
        <button type="button" class="btn-close btn-close-white" @click="error = ''"></button>
      </div>
    </header>

    <!-- TAB 1: SGCA COCKPIT -->
    <section v-if="activeTab === 'sgca'" class="container-fluid px-4">
      <!-- Painel de Inicialização de Simulação -->
      <div class="panel mb-4">
        <h2 class="h5 mb-3 text-white">Controle de Voo e Simulação</h2>
        
        <div class="row g-3 align-items-end">
          <div class="col-12 col-md-3">
            <label class="form-label text-secondary small">Selecionar Aeronave Ativa</label>
            <select v-model="simCallsign" class="form-select" :disabled="isFlightActive">
              <option value="">-- Escolha a Aeronave --</option>
              <option v-for="ac in aircraftList" :key="ac.callsign" :value="ac.callsign">
                {{ ac.callsign }} ({{ ac.modelo }}) - {{ ac.status }}
              </option>
            </select>
          </div>
          
          <div class="col-12 col-md-3">
            <label class="form-label text-secondary small">Aeroporto de Origem (ICAO)</label>
            <input v-model="simOrigin" type="text" class="form-control" placeholder="Ex: SBGR" maxlength="4" :disabled="isFlightActive">
          </div>

          <div class="col-12 col-md-3">
            <label class="form-label text-secondary small">Aeroporto de Destino (ICAO)</label>
            <input v-model="simDestination" type="text" class="form-control" placeholder="Ex: SBRJ" maxlength="4" :disabled="isFlightActive">
          </div>

          <div class="col-12 col-md-3">
            <button v-if="!isFlightActive" class="btn btn-primary w-100" @click="startSimulation" :disabled="!simCallsign || !simOrigin || !simDestination">
              Decolar / Simular Voo
            </button>
            <button v-else class="btn btn-danger w-100" @click="stopSimulation">
              Encerrar Simulação
            </button>
          </div>
        </div>

        <div v-if="isFlightActive" class="mt-3 text-info small mono">
          ✈️ Voando com {{ activeAircraft?.callsign }} | Origem: {{ activeRoute?.icao_origem }} | Destino: {{ activeRoute?.icao_destino }} | Status Rota: {{ activeRoute?.rota_texto }}
        </div>
      </div>

      <div class="row g-3 mb-4">
        <DataCard title="Voo" subtitle="avionica/sensores/voo" :items="flightItems" />
        <DataCard title="Freios" subtitle="avionica/sensores/freios" :items="brakeItems" />
        <DataCard title="Radar Climático" subtitle="avionica/radar" :items="radarItems" />
        <DataCard title="FMS API" subtitle="avionica/fms/dados" :items="fmsItems" />
        <DataCard title="Computador Navegação" subtitle="avionica/navegacao" :items="navigationItems" />
        <DataCard title="Líder WAIC (Motor)" subtitle="avionica/sensores/waic" :items="waicItems" />
        <DataCard title="Anti-Ice (Autônomo)" subtitle="avionica/sistemas/anti_ice" :items="antiIceItems" />
        <DataCard title="Sistema de Alertas" subtitle="avionica/comandos/falhas" :items="alertItems" />
      </div>

      <div class="panel">
        <h2 class="h5 mb-3 text-white">Mensagens Recentes do Barramento MQTT</h2>
        <div class="table-responsive">
          <table class="table align-middle mb-0">
            <thead>
              <tr>
                <th>Horário</th>
                <th>Tópico</th>
                <th>Payload</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="message in rawMessages" :key="`${message.topic}-${message.receivedAt}`">
                <td class="text-nowrap small mono">{{ formatTime(message.receivedAt) }}</td>
                <td class="text-nowrap fw-medium mono">{{ message.topic }}</td>
                <td>
                  <code class="payload">{{ JSON.stringify(message.payload) }}</code>
                </td>
              </tr>
              <tr v-if="rawMessages.length === 0">
                <td colspan="3" class="text-secondary small">
                  Nenhuma mensagem recebida ainda. Ligue os sensores Python para popular o barramento.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 2: TORRE DE COMANDO -->
    <section v-if="activeTab === 'torre'" class="container-fluid px-4">
      <div class="row g-4">
        <div class="col-12 col-lg-4">
          <div class="panel">
            <h2 class="h5 mb-3 text-white">Novo Cadastro de Aeronave</h2>
            <form @submit.prevent="createAircraft">
              <div class="mb-3">
                <label class="form-label text-secondary small">Prefixo / Callsign</label>
                <input v-model="newCallsign" type="text" class="form-control" placeholder="Ex: PR-AAA" required>
              </div>
              <div class="mb-3">
                <label class="form-label text-secondary small">Modelo</label>
                <input v-model="newModelo" type="text" class="form-control" placeholder="Ex: Boeing 737" required>
              </div>
              <div class="mb-3">
                <label class="form-label text-secondary small">Capacidade de Combustível (Litros)</label>
                <input v-model.number="newFuel" type="number" class="form-control" placeholder="Ex: 26020" required>
              </div>
              <div class="mb-3">
                <label class="form-label text-secondary small">Velocidade de Cruzeiro (Nós)</label>
                <input v-model.number="newSpeed" type="number" class="form-control" placeholder="Ex: 450" required>
              </div>
              <button type="submit" class="btn btn-primary w-100">
                Registrar na Torre
              </button>
            </form>
          </div>
        </div>

        <div class="col-12 col-lg-8">
          <div class="panel">
            <h2 class="h5 mb-3 text-white">Aeronaves no Ecossistema</h2>
            <div class="table-responsive">
              <table class="table align-middle">
                <thead>
                  <tr>
                    <th>Callsign</th>
                    <th>Modelo</th>
                    <th>Capacidade Comb.</th>
                    <th>V. Cruzeiro</th>
                    <th>Status</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="ac in aircraftList" :key="ac.callsign">
                    <td class="fw-bold mono">{{ ac.callsign }}</td>
                    <td>{{ ac.modelo }}</td>
                    <td>{{ ac.capacidade_combustivel }} L</td>
                    <td>{{ ac.velocidade_cruzeiro }} kt</td>
                    <td>
                      <span class="status-badge" :class="ac.status === 'Em Voo' ? 'green' : ac.status === 'Em Preparacao' ? 'amber' : 'red'">
                        {{ ac.status }}
                      </span>
                    </td>
                    <td>
                      <button class="btn btn-sm btn-outline-danger" @click="deleteAircraft(ac.callsign)" :disabled="ac.status === 'Em Voo'">
                        Excluir
                      </button>
                    </td>
                  </tr>
                  <tr v-if="aircraftList.length === 0">
                    <td colspan="6" class="text-secondary small text-center py-4">
                      Nenhuma aeronave registrada. Cadastre uma acima para iniciar.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 3: MONITOR DO KAFKA -->
    <section v-if="activeTab === 'kafka'" class="container-fluid px-4">
      <div class="panel mb-4">
        <h2 class="h5 text-white mb-2">Monitoramento do Barramento Kafka</h2>
        <p class="text-secondary small mb-4">Módulo de Integrante 3 (João Lucas Cosme / Ana Luisa). Visualização das mensagens que transitam nos tópicos.</p>

        <div class="row g-4">
          <div class="col-12 col-md-4">
            <div class="panel bg-dark">
              <h3 class="h6 text-white mb-3">Tópicos Ativos</h3>
              <ul class="list-group list-group-flush">
                <li class="list-group-item bg-transparent text-secondary d-flex justify-content-between">
                  <span>avionica.route.requested</span>
                  <span class="badge bg-secondary mono">Ativo</span>
                </li>
                <li class="list-group-item bg-transparent text-secondary d-flex justify-content-between">
                  <span>avionica.route.calculated</span>
                  <span class="badge bg-secondary mono">Ativo</span>
                </li>
                <li class="list-group-item bg-transparent text-secondary d-flex justify-content-between">
                  <span>avionica.simulation.ended</span>
                  <span class="badge bg-secondary mono">Ativo</span>
                </li>
              </ul>
            </div>
          </div>

          <div class="col-12 col-md-8">
            <div class="panel bg-dark">
              <h3 class="h6 text-white mb-3">Fluxo de Eventos em Tempo Real</h3>
              <div class="mono p-3 bg-black rounded border border-secondary text-success" style="height: 200px; overflow-y: auto;">
                <p v-for="ev in kafkaEvents" :key="ev.ts" class="mb-1 small">
                  [{{ ev.ts }}] TOPIC: {{ ev.topic }} -> {{ ev.payload }}
                </p>
                <p v-if="kafkaEvents.length === 0" class="text-secondary small">
                  Aguardando eventos no barramento...
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 4: VISUALIZADOR DE BD -->
    <section v-if="activeTab === 'banco'" class="container-fluid px-4">
      <DbVisualizer :api-base-url="auditEngineUrl" />
    </section>
  </main>
</template>

<script setup>
import axios from 'axios';
import { computed, onMounted, onUnmounted, ref } from 'vue';
import DataCard from './components/DataCard.vue';
import DbVisualizer from './components/DbVisualizer.vue';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
const dispatcherUrl = 'http://localhost:8082';
const kafkaGatewayUrl = 'http://localhost:9000';
const auditEngineUrl = 'http://localhost:8081';

// Estados Gerais
const activeTab = ref('sgca');
const health = ref(null);
const aircraftData = ref({});
const aircraftList = ref([]);
const routeList = ref([]);
const error = ref('');
let refreshTimer;
let kafkaEventSource = null;

// Inputs Simulação
const simCallsign = ref('');
const simOrigin = ref('');
const simDestination = ref('');

// Inputs Cadastro
const newCallsign = ref('');
const newModelo = ref('');
const newFuel = ref(25000);
const newSpeed = ref(450);

// Eventos Kafka Simulação
const kafkaEvents = ref([]);

// Computeds Telemetria
const rawMessages = computed(() => aircraftData.value.rawMessages || []);
const flightItems = computed(() => toItems(aircraftData.value.flight, fieldLabels.flight));
const brakeItems = computed(() => toItems(aircraftData.value.brakes, fieldLabels.brakes));
const radarItems = computed(() => toItems(aircraftData.value.radar, fieldLabels.radar));
const fmsItems = computed(() => toItems(aircraftData.value.fms, fieldLabels.fms));
const navigationItems = computed(() => toItems(aircraftData.value.navigation, fieldLabels.navigation));
const waicItems = computed(() => toItems(aircraftData.value.waic, fieldLabels.waic));
const antiIceItems = computed(() => toItems(aircraftData.value.antiIce, fieldLabels.antiIce));
const alertItems = computed(() => toItems(aircraftData.value.alerts, fieldLabels.alerts));

// Verificações de Voo
const activeAircraft = computed(() => aircraftList.value.find(ac => ac.status === 'Em Voo' || ac.status === 'Em Preparacao'));
const activeRoute = computed(() => routeList.value.find(r => r.ativa === true));
const isFlightActive = computed(() => !!activeAircraft.value);

const fieldLabels = {
  flight: {
    combustivel_pct: 'Combustivel',
    altitude_ft: 'Altitude',
    estabilizador_graus: 'Estabilizador',
    pressao_cabine_psi: 'Pressao cabine',
    velocidade_mach: 'Mach'
  },
  brakes: {
    pressao: 'Pressao'
  },
  radar: {
    vento_knots: 'Vento',
    turbulencia: 'Turbulencia',
    radar_clima: 'Clima',
    temp_externa_c: 'Temp. externa',
    qnh_hpa: 'QNH',
    atc_msg: 'ATC'
  },
  fms: {
    rota_texto: 'Rota',
    distancia_nm: 'Distancia',
    eta_minutos: 'ETA'
  },
  navigation: {
    proa_graus: 'Proa',
    vs_fpm: 'VS',
    piloto_automatico: 'Piloto automatico',
    waypoint_ativo: 'Waypoint',
    eta_minutos: 'ETA'
  },
  waic: {
    pressao_motor: 'Pressao motor',
    temperatura: 'Temperatura'
  },
  antiIce: {
    status: 'Status',
    msg: 'Mensagem'
  },
  alerts: {
    tipo: 'Tipo'
  }
};

function toItems(data = {}, labels = {}) {
  return Object.entries(data).map(([key, value]) => ({
    key,
    label: labels[key] || key,
    value: formatValue(key, value)
  }));
}

function formatValue(key, value) {
  if (value === null || value === undefined || value === '') {
    return 'Sem dado';
  }

  const units = {
    combustivel_pct: '%',
    altitude_ft: 'ft',
    estabilizador_graus: 'graus',
    pressao_cabine_psi: 'psi',
    velocidade_mach: 'Mach',
    pressao: 'psi',
    vento_knots: 'kt',
    temp_externa_c: 'C',
    qnh_hpa: 'hPa',
    distancia_nm: 'NM',
    eta_minutos: 'min',
    proa_graus: 'graus',
    vs_fpm: 'fpm',
    pressao_motor: 'psi',
    temperatura: 'C'
  };

  return `${value}${units[key] ? ` ${units[key]}` : ''}`;
}

function formatTime(value) {
  if (!value) {
    return '-';
  }
  return new Date(value).toLocaleTimeString('pt-BR');
}

// Conexão SSE com o Gateway do Kafka (:9000)
function connectToKafkaStream() {
  if (kafkaEventSource) kafkaEventSource.close();

  kafkaEventSource = new EventSource(`${kafkaGatewayUrl}/api/stream`);

  kafkaEventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      kafkaEvents.value.unshift({
        ts: new Date(parseInt(data.timestamp || Date.now(), 10)).toLocaleTimeString('pt-BR'),
        topic: data.topic,
        payload: JSON.stringify(data.value)
      });

      if (kafkaEvents.value.length > 50) {
        kafkaEvents.value.pop();
      }
    } catch (e) {
      console.error('Erro ao processar stream do Kafka:', e);
    }
  };

  kafkaEventSource.onerror = (err) => {
    console.error('Erro na conexão com o Kafka Stream Gateway, tentando reconectar...');
  };
}

// APIs Aeronaves
async function loadAircraft() {
  try {
    const response = await axios.get(`${apiBaseUrl}/api/aircraft`);
    aircraftList.value = response.data;
  } catch (err) {
    console.error('Falha ao carregar aeronaves:', err);
  }
}

async function createAircraft() {
  error.value = '';
  try {
    await axios.post(`${dispatcherUrl}/api/dispatcher/aircraft`, {
      callsign: newCallsign.value,
      modelo: newModelo.value,
      capacidade_combustivel: newFuel.value,
      velocidade_cruzeiro: newSpeed.value
    });
    newCallsign.value = '';
    newModelo.value = '';
    await loadAircraft();
  } catch (err) {
    error.value = err.response?.data?.erro || err.response?.data?.error || 'Erro ao registrar aeronave no AeroControl.';
  }
}

async function deleteAircraft(callsign) {
  error.value = '';
  try {
    await axios.delete(`${dispatcherUrl}/api/dispatcher/aircraft/${callsign}`);
    await loadAircraft();
  } catch (err) {
    error.value = err.response?.data?.erro || err.response?.data?.error || 'Erro ao excluir aeronave.';
  }
}

// APIs Rotas & Simulação
async function loadRoutes() {
  try {
    const response = await axios.get(`${apiBaseUrl}/api/routes`);
    routeList.value = response.data;
  } catch (err) {
    console.error('Falha ao carregar rotas:', err);
  }
}

async function startSimulation() {
  error.value = '';
  try {
    // 💡 Chama o endpoint de decolagem complexa que valida clima e computadores de voo
    const response = await axios.post(`${dispatcherUrl}/api/dispatcher/aircraft/${simCallsign.value}/takeoff`);
    
    // Inicia a movimentação chamando a rota no FMS central
    await axios.post(`${apiBaseUrl}/api/routes`, {
      callsign: simCallsign.value,
      origin: simOrigin.value,
      destination: simDestination.value
    });

    await loadAircraft();
    await loadRoutes();
    if (response.data && response.data.message) {
      alert(response.data.message); // Exibe o status do consenso distribuído
    }
  } catch (err) {
    error.value = err.response?.data?.erro || err.response?.data?.error || 'Decolagem Recusada pelo AeroControl.';
  }
}

async function stopSimulation() {
  error.value = '';
  if (!activeAircraft.value) return;
  try {
    await axios.post(`${apiBaseUrl}/api/routes/stop`, {
      callsign: activeAircraft.value.callsign
    });

    simCallsign.value = '';
    simOrigin.value = '';
    simDestination.value = '';

    await loadAircraft();
    await loadRoutes();
  } catch (err) {
    error.value = err.response?.data?.erro || 'Erro ao parar simulacao.';
  }
}

// Carregar Tudo
async function loadAll() {
  error.value = '';
  try {
    const [healthResponse, telemetryResponse] = await Promise.all([
      axios.get(`${apiBaseUrl}/api/health`),
      axios.get(`${apiBaseUrl}/api/aircraft-data`)
    ]);

    health.value = healthResponse.data;
    aircraftData.value = telemetryResponse.data;

    await Promise.all([
      loadAircraft(),
      loadRoutes()
    ]);
  } catch (requestError) {
    error.value = 'Nao foi possivel sincronizar dados. Verifique o backend-gateway.';
  }
}

onMounted(() => {
  loadAll();
  refreshTimer = window.setInterval(loadAll, 2000);
  connectToKafkaStream(); // Inicializa a escuta reativa do Kafka via SSE
});

onUnmounted(() => {
  window.clearInterval(refreshTimer);
  if (kafkaEventSource) kafkaEventSource.close();
});
</script>
