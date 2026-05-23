<template>
  <main class="app-shell">
    <nav class="navbar navbar-expand-lg border-bottom bg-white">
      <div class="container-fluid px-4">
        <span class="navbar-brand fw-semibold">Avionica Distribuida</span>
        <span class="badge text-bg-dark">Primeira execucao</span>
      </div>
    </nav>

    <section class="container-fluid px-4 py-4">
      <div class="row g-3 align-items-stretch">
        <div class="col-12 col-xl-4">
          <div class="panel h-100">
            <div class="d-flex justify-content-between align-items-start gap-3">
              <div>
                <p class="text-uppercase text-secondary small mb-1">Backend</p>
                <h1 class="h4 mb-2">Gateway Spring Boot</h1>
              </div>
              <span class="status-dot" :class="{ online: health?.status === 'UP' }"></span>
            </div>

            <p class="mb-3 text-secondary">
              {{ healthMessage }}
            </p>

            <button class="btn btn-primary" type="button" @click="loadData">
              Atualizar status
            </button>
          </div>
        </div>

        <div class="col-12 col-xl-8">
          <div class="panel h-100">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h2 class="h5 mb-0">Modulos iniciais</h2>
              <span class="text-secondary small">{{ modules.length }} itens</span>
            </div>

            <div class="table-responsive">
              <table class="table align-middle mb-0">
                <thead>
                  <tr>
                    <th>Modulo</th>
                    <th>Tecnologia</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="module in modules" :key="module.name">
                    <td class="fw-medium">{{ module.name }}</td>
                    <td>{{ module.technology }}</td>
                    <td>
                      <span class="badge" :class="statusClass(module.status)">
                        {{ module.status }}
                      </span>
                    </td>
                  </tr>
                  <tr v-if="modules.length === 0">
                    <td colspan="3" class="text-secondary">Nenhum modulo carregado ainda.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
import axios from 'axios';
import { computed, onMounted, ref } from 'vue';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
const health = ref(null);
const modules = ref([]);
const error = ref('');

const healthMessage = computed(() => {
  if (error.value) {
    return error.value;
  }

  if (!health.value) {
    return 'Aguardando a primeira consulta ao backend.';
  }

  return `Servico ${health.value.service} respondeu ${health.value.status} em ${health.value.timestamp}.`;
});

function statusClass(status) {
  if (status === 'UP') {
    return 'text-bg-success';
  }

  if (status === 'INFRASTRUCTURE' || status === 'TEMPORARY_INFRASTRUCTURE') {
    return 'text-bg-secondary';
  }

  return 'text-bg-warning';
}

async function loadData() {
  error.value = '';

  try {
    const [healthResponse, modulesResponse] = await Promise.all([
      axios.get(`${apiBaseUrl}/api/health`),
      axios.get(`${apiBaseUrl}/api/modules`)
    ]);

    health.value = healthResponse.data;
    modules.value = modulesResponse.data;
  } catch (requestError) {
    error.value = 'Nao foi possivel conectar ao backend. Verifique se o container backend-gateway esta ativo.';
  }
}

onMounted(loadData);
</script>
