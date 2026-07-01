<template>
  <div class="db-visualizer-component">
    <div class="panel mb-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h2 class="h5 text-white mb-1">Visualizador & Auditor Causal de Banco de Dados</h2>
          <p class="text-secondary small mb-0">Consulte logs de telemetria e audite a consistência lógica de Lamport no PostgreSQL.</p>
        </div>
        
        <div class="d-flex align-items-center gap-3">
          <div class="form-check form-switch text-secondary small mono">
            <input 
              v-model="autoRefresh" 
              class="form-check-input" 
              type="checkbox" 
              id="flexSwitchAutoRefresh"
              @change="toggleAutoRefresh"
            >
            <label class="form-check-label text-secondary" for="flexSwitchAutoRefresh">Auto-Update (3s)</label>
          </div>
          
          <button 
            @click="reloadData" 
            class="btn btn-sm btn-outline-light d-flex align-items-center gap-1"
            :disabled="loading"
          >
            <span>🔄</span> Atualizar
          </button>
        </div>
      </div>

      <!-- Menu de Abas Internas -->
      <ul class="nav nav-tabs border-secondary mb-4">
        <li class="nav-item">
          <button 
            class="nav-link text-white py-2 px-3 border-secondary" 
            :class="{ active: subTab === 'tables', 'bg-dark': subTab === 'tables' }" 
            @click="subTab = 'tables'"
          >
            📁 Tabelas (Volumetria)
          </button>
        </li>
        <li class="nav-item">
          <button 
            class="nav-link text-white py-2 px-3 border-secondary" 
            :class="{ active: subTab === 'explorer', 'bg-dark': subTab === 'explorer' }" 
            @click="subTab = 'explorer'"
          >
            🔍 Explorador de Registros
          </button>
        </li>
        <li class="nav-item">
          <button 
            class="nav-link text-white py-2 px-3 border-secondary" 
            :class="{ active: subTab === 'causality', 'bg-dark': subTab === 'causality' }" 
            @click="subTab = 'causality'"
          >
            ⚖️ Auditoria Causal (Lamport)
          </button>
        </li>
      </ul>

      <!-- Notificação de Erro / Sucesso local -->
      <div v-if="localNotification" class="alert py-2 px-3 mb-4 d-flex justify-content-between align-items-center text-xs" :class="localNotification.type === 'error' ? 'alert-danger' : 'alert-success'">
        <span>{{ localNotification.text }}</span>
        <button type="button" class="btn-close btn-close-white" @click="localNotification = null"></button>
      </div>

      <!-- SUBTAB 1: TABELAS -->
      <div v-if="subTab === 'tables'">
        <!-- Barra de métricas TCP do PostgreSQL -->
        <div v-if="poolStats" class="card bg-dark border-secondary p-3 mb-4">
          <div class="row g-3 align-items-center text-xs mono">
            <div class="col-12 col-md-3 text-secondary text-uppercase fw-semibold">
              Métricas do Pool TCP:
            </div>
            <div class="col-4 col-md-3">
              <span class="text-secondary">Conexões Totais: </span>
              <span class="text-info fw-bold">{{ poolStats.totalCount }}</span>
            </div>
            <div class="col-4 col-md-3">
              <span class="text-secondary">Conexões Ociosas: </span>
              <span class="text-success fw-bold">{{ poolStats.idleCount }}</span>
            </div>
            <div class="col-4 col-md-3">
              <span class="text-secondary">Aguardando na Fila: </span>
              <span class="text-warning fw-bold">{{ poolStats.waitingCount }}</span>
            </div>
          </div>
        </div>

        <div class="row g-3">
          <div v-for="table in tables" :key="table.id" class="col-12 col-md-4 col-lg-3">
            <div class="card bg-dark border-secondary p-3 h-100 d-flex flex-column justify-content-between">
              <div>
                <div class="text-secondary small text-uppercase fw-semibold mb-1">{{ table.id }}</div>
                <h3 class="h6 text-white fw-bold mb-3">{{ table.displayName }}</h3>
              </div>
              
              <div class="d-flex justify-content-between align-items-baseline mt-auto pt-2 border-top border-secondary">
                <div>
                  <span class="mono fs-4 fw-bold text-info">{{ table.rowCount }}</span>
                  <span class="text-secondary small ms-1">rows</span>
                </div>
                
                <div class="d-flex gap-2">
                  <button 
                    @click="selectTable(table.id)" 
                    class="btn btn-xs btn-outline-info py-1 px-2"
                    title="Explorar registros"
                  >
                    🔍
                  </button>
                  <button 
                    @click="confirmTruncate(table.id)" 
                    class="btn btn-xs btn-outline-danger py-1 px-2" 
                    title="Limpar tabela"
                    :disabled="table.rowCount === 0"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- SUBTAB 2: EXPLORADOR DE DADOS -->
      <div v-if="subTab === 'explorer'">
        <!-- Filtros do Explorador -->
        <div class="row g-3 mb-4 bg-dark/40 p-3 rounded border border-secondary align-items-end">
          <div class="col-12 col-md-3">
            <label class="form-label text-secondary small">Tabela para Consulta</label>
            <select v-model="selectedTable" class="form-select bg-dark text-white border-secondary" @change="fetchTableData">
              <option value="">-- Selecione a Tabela --</option>
              <option v-for="t in tables" :key="t.id" :value="t.id">
                {{ t.displayName }} ({{ t.id }})
              </option>
            </select>
          </div>

          <div class="col-12 col-md-3">
            <label class="form-label text-secondary small">Buscar no Payload</label>
            <input 
              v-model="filters.search" 
              type="text" 
              class="form-control bg-dark text-white border-secondary" 
              placeholder="Pesquisar..."
              @keyup.enter="fetchTableData"
            >
          </div>

          <div class="col-12 col-md-2">
            <label class="form-label text-secondary small">Data Inicial</label>
            <input 
              v-model="filters.startDate" 
              type="datetime-local" 
              class="form-control bg-dark text-white border-secondary"
            >
          </div>

          <div class="col-12 col-md-2">
            <label class="form-label text-secondary small">Data Final</label>
            <input 
              v-model="filters.endDate" 
              type="datetime-local" 
              class="form-control bg-dark text-white border-secondary"
            >
          </div>

          <div class="col-12 col-md-2 d-flex gap-2">
            <button @click="fetchTableData" class="btn btn-info w-100" :disabled="!selectedTable || loading">
              Filtrar
            </button>
            <button @click="clearFilters" class="btn btn-outline-secondary" :disabled="!selectedTable">
              ❌
            </button>
          </div>
        </div>

        <!-- Tabela de Registros Dinâmica -->
        <div v-if="selectedTable" class="table-responsive">
          <div v-if="loading" class="text-center py-4 text-info mono">
            ⏳ Carregando registros...
          </div>
          
          <table v-else class="table align-middle text-xs">
            <thead>
              <tr class="text-secondary border-secondary">
                <th v-for="col in tableData.columns" :key="col" class="mono py-2">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in tableData.rows" :key="idx" class="border-secondary hover-row">
                <td v-for="col in tableData.columns" :key="col" class="mono py-2 text-white">
                  <!-- Renderiza payloads grandes com truncate e formatacao JSON -->
                  <template v-if="col === 'payload_json' || col === 'payload'">
                    <span class="d-inline-block text-truncate text-secondary" style="max-width: 40rem;" :title="JSON.stringify(row[col])">
                      {{ typeof row[col] === 'string' ? row[col] : JSON.stringify(row[col]) }}
                    </span>
                  </template>
                  <template v-else-if="col === 'logical_clock' || col === 'logicalClock'">
                    <span class="fw-bold text-info">{{ row[col] }}</span>
                  </template>
                  <template v-else>
                    {{ row[col] }}
                  </template>
                </td>
              </tr>
              <tr v-if="tableData.rows.length === 0">
                <td :colspan="tableData.columns.length || 1" class="text-secondary text-center py-4">
                  Nenhum registro encontrado com os filtros selecionados.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div v-else class="text-secondary text-center py-4">
          Selecione uma tabela acima para explorar os registros persistidos.
        </div>
      </div>

      <!-- SUBTAB 3: AUDITORIA CAUSAL -->
      <div v-if="subTab === 'causality'">
        <div class="row g-3 mb-4">
          <!-- Metricas Globais -->
          <div class="col-12 col-lg-8">
            <div class="card bg-dark border-secondary p-4 h-100">
              <h3 class="h6 text-white fw-bold mb-3 border-bottom border-secondary pb-2">Diagnóstico de Integridade Geral</h3>
              
              <div v-if="causalityReport" class="row g-3 text-center">
                <div class="col-12 col-md-3">
                  <div class="text-secondary small mb-1">Status Causal</div>
                  <div class="badge p-2 fs-6 w-100" :class="causalityReport.metricasGlobais.statusIntegridade === 'CONCORDANTE' ? 'bg-success' : 'bg-warning'">
                    {{ causalityReport.metricasGlobais.statusIntegridade }}
                  </div>
                </div>
                <div class="col-12 col-md-3">
                  <div class="text-secondary small mb-1">Causas Fora de Ordem</div>
                  <div class="fs-3 fw-bold mono" :class="causalityReport.metricasGlobais.totalAnomaliasCausais > 0 ? 'text-danger' : 'text-success'">
                    {{ causalityReport.metricasGlobais.totalAnomaliasCausais }}
                  </div>
                </div>
                <div class="col-12 col-md-3">
                  <div class="text-secondary small mb-1">Mensagens Perdidas (Gaps)</div>
                  <div class="fs-3 fw-bold mono text-warning">
                    {{ causalityReport.metricasGlobais.totalMensagensPerdidas }}
                  </div>
                </div>
                <div class="col-12 col-md-3">
                  <div class="text-secondary small mb-1">Sensores Auditados</div>
                  <div class="fs-3 fw-bold mono text-info">
                    {{ causalityReport.metricasGlobais.totalSensoresAuditados }}
                  </div>
                </div>
              </div>
              <div v-else class="text-secondary py-4 text-center">
                Auditoria não executada. Clique em "Atualizar" para rodar o algoritmo de Lamport.
              </div>
            </div>
          </div>

          <!-- Explicação do Algoritmo -->
          <div class="col-12 col-lg-4">
            <div class="card bg-dark border-secondary p-4 h-100 text-xs">
              <h3 class="h6 text-white fw-bold mb-2">Defesa Acadêmica</h3>
              <p class="text-secondary">O **Causal Consistency Auditor** analisa a tabela de telemetria ordenada e verifica:</p>
              <ul class="text-secondary ps-3 mb-0">
                <li class="mb-1"><strong class="text-white">Anomalias causais:</strong> Se um clock lógico menor chega após um clock maior fisicamente (violação do relógio de Lamport).</li>
                <li><strong class="text-white">Gaps lógicos:</strong> Saltos sequenciais nos relógios de cada sensor, indicando perda de mensagens no barramento MQTT/Kafka.</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Tabela por Sensor -->
        <div v-if="causalityReport" class="table-responsive">
          <h4 class="h6 text-white fw-bold mb-3">Auditoria por Sensor e Origem</h4>
          <table class="table align-middle text-xs">
            <thead>
              <tr class="text-secondary border-secondary">
                <th class="py-2">Sensor de Origem</th>
                <th class="py-2">Total Mensagens</th>
                <th class="py-2">Último Relógio de Lamport</th>
                <th class="py-2">Último Timestamp Físico</th>
                <th class="py-2">Anomalias Causais (Rede)</th>
                <th class="py-2">Mensagens Perdidas (Gaps)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="sensor in causalityReport.sensores" :key="sensor.sensor" class="border-secondary hover-row text-white">
                <td class="mono fw-bold text-info">{{ sensor.sensor }}</td>
                <td class="mono">{{ sensor.totalMensagens }}</td>
                <td class="mono text-info fw-bold">{{ sensor.ultimoClock }}</td>
                <td class="mono small">{{ formatTimestamp(sensor.ultimoTime) }}</td>
                <td class="mono fw-bold" :class="sensor.anomaliasCausais > 0 ? 'text-danger' : 'text-secondary'">
                  {{ sensor.anomaliasCausais }}
                </td>
                <td class="mono fw-bold text-warning">{{ sensor.mensagensPerdidas }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Gráfico Causal de Lamport -->
        <div v-if="causalityReport" class="card bg-dark border-secondary p-4 mt-4">
          <h4 class="h6 text-white fw-bold mb-3">Gráfico Causal de Lamport (Relógio Lógico vs Tempo Físico de Recebimento)</h4>
          <div style="position: relative; height: 350px; width: 100%;">
            <canvas id="causalityChart"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import axios from 'axios';
import { onMounted, onUnmounted, ref, watch, nextTick } from 'vue';

const props = defineProps({
  apiBaseUrl: {
    type: String,
    required: true
  }
});

// Abas e controle de carregamento
const subTab = ref('tables');
const loading = ref(false);
const autoRefresh = ref(false);
const localNotification = ref(null);
let refreshTimer = null;
let causalityChartInstance = null;

// Dados das APIS
const tables = ref([]);
const selectedTable = ref('');
const tableData = ref({ columns: [], rows: [] });
const causalityReport = ref(null);
const poolStats = ref(null);

const filters = ref({
  search: '',
  limit: 50,
  startDate: '',
  endDate: ''
});

const showNotification = (text, type = 'success') => {
  localNotification.value = { text, type };
  setTimeout(() => {
    localNotification.value = null;
  }, 4000);
};

const fetchTables = async () => {
  try {
    const res = await axios.get(`${props.apiBaseUrl}/api/audit/tables`);
    if (res.data.success) {
      tables.value = res.data.tables;
    }
  } catch (err) {
    showNotification('Falha ao se conectar com as tabelas de auditoria.', 'error');
  }
};

const fetchCausalityReport = async () => {
  try {
    const res = await axios.get(`${props.apiBaseUrl}/api/audit/causality`);
    if (res.data.success || res.status === 200) {
      causalityReport.value = res.data;
      nextTick(() => {
        if (res.data.pontos && subTab.value === 'causality') {
          updateChart(res.data.pontos);
        }
      });
    }
  } catch (err) {
    console.error('Falha ao buscar auditoria de Lamport:', err);
  }
};

const fetchPoolStats = async () => {
  try {
    const res = await axios.get(`${props.apiBaseUrl}/api/audit/pool-stats`);
    if (res.data.success) {
      poolStats.value = res.data;
    }
  } catch (err) {
    console.error('Falha ao buscar métricas do pool TCP:', err);
  }
};

const updateChart = (pontos) => {
  const canvas = document.getElementById('causalityChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  // Agrupa os pontos por sensor de origem
  const groups = {};
  pontos.forEach(p => {
    if (!groups[p.sensor_origem]) {
      groups[p.sensor_origem] = [];
    }
    groups[p.sensor_origem].push(p);
  });

  const colors = ['#0dcaf0', '#198754', '#ffc107', '#fd7e14', '#dc3545', '#6f42c1'];
  let colorIdx = 0;

  const datasets = Object.keys(groups).map(sensor => {
    const data = groups[sensor].map(p => ({
      x: new Date(p.recebido_em).toLocaleTimeString('pt-BR'),
      y: parseInt(p.logical_clock, 10)
    }));

    const color = colors[colorIdx % colors.length];
    colorIdx++;

    return {
      label: sensor,
      data: data,
      borderColor: color,
      backgroundColor: color + '22',
      borderWidth: 2,
      tension: 0.1,
      fill: false
    };
  });

  if (causalityChartInstance) {
    causalityChartInstance.destroy();
  }

  // Cria a instância do Chart.js
  causalityChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#fff' }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.1)' },
          ticks: { color: '#fff' }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.1)' },
          ticks: { color: '#fff' },
          title: {
            display: true,
            text: 'Relógio Lógico (Lamport)',
            color: '#fff'
          }
        }
      }
    }
  });
};

watch(subTab, (newTab) => {
  if (newTab === 'causality' && causalityReport.value && causalityReport.value.pontos) {
    nextTick(() => {
      updateChart(causalityReport.value.pontos);
    });
  }
});

const fetchTableData = async () => {
  if (!selectedTable.value) return;
  loading.value = true;
  try {
    const queryParams = {
      limit: filters.value.limit,
      search: filters.value.search || undefined,
      startDate: filters.value.startDate || undefined,
      endDate: filters.value.endDate || undefined
    };

    const res = await axios.get(`${props.apiBaseUrl}/api/audit/tables/${selectedTable.value}`, {
      params: queryParams
    });
    if (res.data.success) {
      tableData.value = {
        columns: res.data.columns,
        rows: res.data.rows
      };
    }
  } catch (err) {
    showNotification('Falha ao consultar os registros da tabela.', 'error');
  } finally {
    loading.value = false;
  }
};

const selectTable = (tableName) => {
  selectedTable.value = tableName;
  subTab.value = 'explorer';
  clearFilters();
  fetchTableData();
};

const confirmTruncate = async (tableName) => {
  const confirm = window.confirm(`ATENÇÃO! Você tem certeza que deseja LIMPAR TODOS OS DADOS da tabela "${tableName}"?\nEssa ação é irreversível.`);
  if (!confirm) return;

  try {
    const res = await axios.post(`${props.apiBaseUrl}/api/audit/tables/${tableName}/truncate`);
    if (res.data.success) {
      showNotification(`A tabela ${tableName} foi esvaziada com sucesso!`);
      if (selectedTable.value === tableName) {
        fetchTableData();
      }
      fetchTables();
      fetchCausalityReport();
    }
  } catch (err) {
    showNotification(`Falha ao limpar dados da tabela ${tableName}.`, 'error');
  }
};

const clearFilters = () => {
  filters.value = {
    search: '',
    limit: 50,
    startDate: '',
    endDate: ''
  };
  if (selectedTable.value) {
    fetchTableData();
  }
};

const formatTimestamp = (timeMs) => {
  if (!timeMs) return '-';
  return new Date(timeMs).toLocaleString('pt-BR');
};

const reloadData = async () => {
  loading.value = true;
  await Promise.all([
    fetchTables(),
    fetchCausalityReport(),
    fetchPoolStats()
  ]);
  if (selectedTable.value) {
    await fetchTableData();
  }
  loading.value = false;
};

const toggleAutoRefresh = () => {
  if (autoRefresh.value) {
    refreshTimer = window.setInterval(reloadData, 3000);
  } else {
    if (refreshTimer) {
      window.clearInterval(refreshTimer);
      refreshTimer = null;
    }
  }
};

onMounted(() => {
  reloadData();
});

onUnmounted(() => {
  if (refreshTimer) {
    window.clearInterval(refreshTimer);
  }
});
</script>

<style scoped>
.btn-xs {
  padding: 0.15rem 0.4rem;
  font-size: 0.75rem;
}
.hover-row:hover {
  background-color: rgba(255, 255, 255, 0.03);
}
</style>
