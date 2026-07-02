<template>
  <div class="container px-4 py-5 text-center">
    <div class="panel mx-auto py-5" style="max-width: 800px;">
      <span class="fs-1">✈️</span>
      <h1 class="display-5 fw-bold text-white mb-4">SGCA — Simulador Glass Cockpit da Aeronave</h1>
      <p class="lead text-secondary mb-5">
        Bem-vindo ao SGCA. Este sistema simula em tempo real os instrumentos aviônicos distribuídos de uma aeronave comercial, monitorando motores, telemetria de voo, sistemas de freios e radar meteorológico integrados a um barramento de eventos distribuído e tolerante a falhas.
      </p>
      <div class="d-grid gap-2 d-sm-flex justify-content-sm-center">
        <router-link to="/simulacao" class="btn btn-primary btn-lg px-5 gap-3">
          Iniciar Simulação
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
// Sem lógica adicional necessária para a Home
</script>
```

### [SimulationView.vue](file:///C:/projetos/Sistemas_Distribuidos_Avionica/frontend/src/views/SimulationView.vue)

```vue
<template>
  <div class="container px-4 py-5">
    <div class="panel mx-auto p-4" style="max-width: 600px;">
      <h2 class="h4 mb-4 text-white text-center">Selecionar Aeronave para Simulação</h2>
      
      <div v-if="loading" class="text-center py-4 text-secondary mono">
        Carregando aeronaves cadastradas...
      </div>
      
      <div v-else>
        <div class="mb-4">
          <label class="form-label text-secondary small">Código da Aeronave (Callsign)</label>
          <select v-model="selectedCallsign" class="form-select">
            <option value="">-- Escolha uma Aeronave --</option>
            <option v-for="ac in aircraftList" :key="ac.callsign" :value="ac.callsign">
              {{ ac.callsign }} ({{ ac.modelo }}) — {{ ac.status }}
            </option>
          </select>
        </div>

        <div v-if="error" class="alert alert-danger text-xs py-2 px-3 mb-3">
          {{ error }}
        </div>

        <button 
          @click="confirmSelection" 
          class="btn btn-primary w-100" 
          :disabled="!selectedCallsign"
        >
          Selecionar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const apiBaseUrl = 'http://localhost:8080';

const aircraftList = ref([]);
const selectedCallsign = ref('');
const loading = ref(false);
const error = ref('');

async function loadAircraft() {
  loading.value = true;
  error.value = '';
  try {
    const response = await axios.get(`${apiBaseUrl}/api/aircraft`);
    aircraftList.value = response.data;
  } catch (err) {
    error.value = 'Falha ao conectar-se à torre de comando para obter as aeronaves.';
    console.error(err);
  } finally {
    loading.value = false;
  }
}

function confirmSelection() {
  if (selectedCallsign.value) {
    router.push({
      path: '/simulacao/rota',
      query: { callsign: selectedCallsign.value }
    });
  }
}

onMounted(() => {
  loadAircraft();
});
</script>
