<template>
  <main class="app-shell">
    <nav class="navbar navbar-expand-lg border-bottom bg-white">
      <div class="container-fluid px-4">
        <div>
          <span class="navbar-brand fw-semibold">Avionica Distribuida</span>
          <span class="text-secondary small">Telemetria em tempo quase real</span>
        </div>
        <div class="d-flex align-items-center gap-3">
          <span class="badge" :class="health?.status === 'UP' ? 'text-bg-success' : 'text-bg-danger'">
            Backend {{ health?.status || 'OFF' }}
          </span>
          <button class="btn btn-sm btn-outline-primary" type="button" @click="loadData">
            Atualizar
          </button>
        </div>
      </div>
    </nav>

    <section class="container-fluid px-4 py-4">
      <div v-if="error" class="alert alert-warning mb-4" role="alert">
        {{ error }}
      </div>

      <div class="row g-3 mb-4">
        <DataCard title="Voo" subtitle="avionica/sensores/voo" :items="flightItems" />
        <DataCard title="Freios" subtitle="avionica/sensores/freios" :items="brakeItems" />
        <DataCard title="Radar" subtitle="avionica/radar" :items="radarItems" />
        <DataCard title="FMS" subtitle="avionica/fms/dados" :items="fmsItems" />
        <DataCard title="Navegacao" subtitle="avionica/navegacao" :items="navigationItems" />
        <DataCard title="Motor WAIC" subtitle="avionica/sensores/waic" :items="waicItems" />
        <DataCard title="Anti-Ice" subtitle="avionica/sistemas/anti_ice" :items="antiIceItems" />
        <DataCard title="Alertas" subtitle="avionica/comandos/falhas" :items="alertItems" />
      </div>

      <div class="panel">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <div>
            <h2 class="h5 mb-1">Mensagens recentes do barramento</h2>
            <p class="text-secondary mb-0 small">Ultimas mensagens MQTT recebidas pelo backend em `avionica/#`.</p>
          </div>
          <span class="text-secondary small">{{ rawMessages.length }} mensagens</span>
        </div>

        <div class="table-responsive">
          <table class="table align-middle mb-0">
            <thead>
              <tr>
                <th>Horario</th>
                <th>Topico</th>
                <th>Payload</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="message in rawMessages" :key="`${message.topic}-${message.receivedAt}`">
                <td class="text-nowrap small">{{ formatTime(message.receivedAt) }}</td>
                <td class="text-nowrap fw-medium">{{ message.topic }}</td>
                <td>
                  <code class="payload">{{ JSON.stringify(message.payload) }}</code>
                </td>
              </tr>
              <tr v-if="rawMessages.length === 0">
                <td colspan="3" class="text-secondary">
                  Nenhuma mensagem recebida ainda. Aguarde os containers Python publicarem telemetria.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
import axios from 'axios';
import { computed, onMounted, onUnmounted, ref } from 'vue';
import DataCard from './components/DataCard.vue';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
const health = ref(null);
const aircraftData = ref({});
const error = ref('');
let refreshTimer;

const rawMessages = computed(() => aircraftData.value.rawMessages || []);
const flightItems = computed(() => toItems(aircraftData.value.flight, fieldLabels.flight));
const brakeItems = computed(() => toItems(aircraftData.value.brakes, fieldLabels.brakes));
const radarItems = computed(() => toItems(aircraftData.value.radar, fieldLabels.radar));
const fmsItems = computed(() => toItems(aircraftData.value.fms, fieldLabels.fms));
const navigationItems = computed(() => toItems(aircraftData.value.navigation, fieldLabels.navigation));
const waicItems = computed(() => toItems(aircraftData.value.waic, fieldLabels.waic));
const antiIceItems = computed(() => toItems(aircraftData.value.antiIce, fieldLabels.antiIce));
const alertItems = computed(() => toItems(aircraftData.value.alerts, fieldLabels.alerts));

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

async function loadData() {
  error.value = '';

  try {
    const [healthResponse, telemetryResponse] = await Promise.all([
      axios.get(`${apiBaseUrl}/api/health`),
      axios.get(`${apiBaseUrl}/api/aircraft-data`)
    ]);

    health.value = healthResponse.data;
    aircraftData.value = telemetryResponse.data;
  } catch (requestError) {
    error.value = 'Nao foi possivel carregar a telemetria. Verifique backend-gateway e mqtt-broker.';
  }
}

onMounted(() => {
  loadData();
  refreshTimer = window.setInterval(loadData, 2000);
});

onUnmounted(() => {
  window.clearInterval(refreshTimer);
});
</script>
