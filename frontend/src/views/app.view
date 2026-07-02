<template>
  <main class="app-shell pb-5">
    <!-- Navbar Superior -->
    <nav class="navbar navbar-expand-lg navbar-dark border-bottom">
      <div class="container-fluid px-4">
        <!-- Logo (SGCA - CDU-01) -->
        <router-link to="/painel" class="navbar-brand fw-semibold text-white mono d-flex align-items-center gap-2">
          <span>✈️ SGCA</span>
          <span class="text-secondary small ms-2 mono d-none d-md-inline">| Glass Cockpit Edition</span>
        </router-link>

        <!-- Menu de Navegação Superior (CDU-01) -->
        <div class="collapse navbar-collapse show" id="navbarNav">
          <ul class="navbar-nav ms-4 gap-2">
            <li class="nav-item">
              <router-link to="/painel" class="nav-link px-3" active-class="active">
                Início
              </router-link>
            </li>
            <li class="nav-item">
              <router-link to="/simulacao" class="nav-link px-3" active-class="active">
                Simulação
              </router-link>
            </li>
            <!-- Redirecionamentos externos para os outros microssistemas das equipes -->
            <li class="nav-item">
              <a href="http://localhost:8082" target="_blank" class="nav-link px-3">
                Torre de Comando ↗
              </a>
            </li>
            <li class="nav-item">
              <a href="http://localhost:9000" target="_blank" class="nav-link px-3">
                Monitor do Kafka ↗
              </a>
            </li>
            <li class="nav-item">
              <a href="http://localhost:8081" target="_blank" class="nav-link px-3">
                Visualizador de BD ↗
              </a>
            </li>
          </ul>
        </div>

        <!-- Status do Gateway -->
        <div class="d-flex align-items-center gap-3">
          <span class="badge status-badge" :class="health?.status === 'UP' ? 'green' : 'red'">
            Gateway: {{ health?.status || 'OFFLINE' }}
          </span>
          <button class="btn btn-sm btn-outline-light" type="button" @click="checkGatewayHealth">
            ↻ Sincronizar
          </button>
        </div>
      </div>
    </nav>

    <!-- Shell Geral do Roteador -->
    <div class="container-fluid py-4">
      <router-view />
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';

const apiBaseUrl = 'http://localhost:8080';
const health = ref(null);
let healthTimer = null;

async function checkGatewayHealth() {
  try {
    const res = await axios.get(`${apiBaseUrl}/api/health`);
    health.value = res.data;
  } catch (err) {
    health.value = { status: 'OFFLINE' };
  }
}

onMounted(() => {
  checkGatewayHealth();
  healthTimer = setInterval(checkGatewayHealth, 5000);
});

onUnmounted(() => {
  if (healthTimer) clearInterval(healthTimer);
});
</script>

<style>
/* Estilos globais para a navegação do Menu */
.navbar-nav .nav-link {
  color: var(--text-secondary) !important;
  font-weight: 500;
  transition: all 0.2s ease;
  border-radius: 6px;
}

.navbar-nav .nav-link:hover {
  color: var(--text-primary) !important;
  background: rgba(255, 255, 255, 0.05);
}

.navbar-nav .nav-link.active {
  color: var(--neon-cyan) !important;
  background: rgba(0, 210, 255, 0.1) !important;
  border: 1px solid rgba(0, 210, 255, 0.2);
}
</style>
