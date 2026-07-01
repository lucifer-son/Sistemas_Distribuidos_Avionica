const express = require('express');
const { Pool } = require('pg');
const path = require('path');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 8081;

// Configuração da conexão com o PostgreSQL
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432', 10),
  database: process.env.DB_NAME || 'avionica',
  user: process.env.DB_USER || 'avionica',
  password: process.env.DB_PASS || 'avionica_dev',
});

// Middleware para habilitar CORS (essencial para integração com o frontend)
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, PATCH, DELETE');
  res.setHeader('Access-Control-Allow-Headers', 'X-Requested-With,content-type');
  res.setHeader('Access-Control-Allow-Credentials', true);
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Mapeamento das tabelas de aviônica e suas respectivas colunas de data/hora
const TABLE_METADATA = {
  telemetria_voo: { name: 'Telemetria de Voo', timeCol: 'recebido_em' },
  telemetria_freios: { name: 'Telemetria de Freios', timeCol: 'recebido_em' },
  telemetria_radar: { name: 'Telemetria de Radar', timeCol: 'recebido_em' },
  telemetria_waic: { name: 'Telemetria WAIC', timeCol: 'recebido_em' },
  telemetria_navegacao: { name: 'Computador de Navegação', timeCol: 'recebido_em' },
  rotas_fms: { name: 'Rotas do FMS', timeCol: 'registrado_em' },
  alertas: { name: 'Alertas e Falhas', timeCol: 'registrado_em' },
  eventos_anti_ice: { name: 'Eventos de Anti-Ice', timeCol: 'registrado_em' },
  mensagens_barramento: { name: 'Log do Barramento MQTT', timeCol: 'recebido_em' },
  aeronaves: { name: 'Aeronaves Cadastradas', timeCol: 'ultima_atualizacao' },
  telemetria_ordenada: { name: 'Telemetria Ordenada (Lamport)', timeCol: 'recebido_em' }
};

// 1. Listar tabelas e contagem de registros (Auditoria de Persistência)
app.get('/api/tables', async (req, res) => {
  try {
    const list = [];
    for (const tableName of Object.keys(TABLE_METADATA)) {
      const countRes = await pool.query(`SELECT COUNT(*) FROM ${tableName}`);
      list.push({
        id: tableName,
        displayName: TABLE_METADATA[tableName].name,
        rowCount: parseInt(countRes.rows[0].count, 10)
      });
    }
    res.json({ success: true, tables: list });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 2. Buscar registros de uma tabela com filtros, limite e busca global
app.get('/api/tables/:tableName', async (req, res) => {
  const { tableName } = req.params;
  const metadata = TABLE_METADATA[tableName];
  if (!metadata) {
    return res.status(404).json({ success: false, error: 'Tabela não encontrada no sistema' });
  }

  const { search, limit = 50, startDate, endDate } = req.query;
  const parsedLimit = Math.min(parseInt(limit, 10) || 50, 500);
  const timeCol = metadata.timeCol;

  let queryText = `SELECT * FROM ${tableName}`;
  const queryParams = [];
  const conditions = [];

  // Filtros temporais
  if (startDate) {
    queryParams.push(new Date(startDate));
    conditions.push(`${timeCol} >= $${queryParams.length}`);
  }
  if (endDate) {
    queryParams.push(new Date(endDate));
    conditions.push(`${timeCol} <= $${queryParams.length}`);
  }

  // Filtro de busca textual global (ROW_TO_JSON converte a linha em string para buscar em qualquer coluna)
  if (search) {
    queryParams.push(`%${search}%`);
    conditions.push(`ROW_TO_JSON(${tableName})::text ILIKE $${queryParams.length}`);
  }

  if (conditions.length > 0) {
    queryText += ` WHERE ${conditions.join(' AND ')}`;
  }

  // Ordenação (mais recente primeiro)
  queryText += ` ORDER BY ${timeCol} DESC`;

  // Limite de registros
  queryParams.push(parsedLimit);
  queryText += ` LIMIT $${queryParams.length}`;

  try {
    const result = await pool.query(queryText, queryParams);
    res.json({
      success: true,
      tableName,
      columns: result.fields.map(f => f.name),
      rows: result.rows
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 3. Limpar (TRUNCATE) uma tabela (Apenas dados de simulação/teste)
app.post('/api/tables/:tableName/truncate', async (req, res) => {
  const { tableName } = req.params;
  if (!TABLE_METADATA[tableName]) {
    return res.status(404).json({ success: false, error: 'Tabela não encontrada no sistema' });
  }

  try {
    await pool.query(`TRUNCATE TABLE ${tableName} RESTART IDENTITY CASCADE`);
    res.json({ success: true, message: `Tabela ${tableName} limpa com sucesso` });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 4. 🔥 ALGORITMO DISTRIBUÍDO: Auditoria de Consistência Causal e Integridade (Lamport)
// Corrigido para ordenar por recebido_em ASC para detecção correta de inversão causal
app.get('/api/audit/causality', async (req, res) => {
  try {
    const query = `
      SELECT sensor_origem, logical_clock, recebido_em
      FROM telemetria_ordenada
      ORDER BY sensor_origem, recebido_em ASC
    `;
    const dbRes = await pool.query(query);
    const records = dbRes.rows;

    const auditBySensor = {};
    let totalAnomalias = 0;
    let totalPerdas = 0;

    records.forEach((record) => {
      const { sensor_origem, logical_clock, recebido_em } = record;
      const clock = parseInt(logical_clock, 10);
      const time = new Date(recebido_em).getTime();

      if (!auditBySensor[sensor_origem]) {
        auditBySensor[sensor_origem] = {
          sensor: sensor_origem,
          totalMensagens: 0,
          ultimoClock: clock,
          ultimoTime: time,
          anomaliasCausais: 0, 
          mensagensPerdidas: 0, 
        };
      }

      const sensorData = auditBySensor[sensor_origem];
      sensorData.totalMensagens++;

      if (sensorData.totalMensagens > 1) {
        // Detecta inversão causal (clock lógico regressivo em relação ao tempo de recebimento)
        if (clock <= sensorData.ultimoClock) {
          sensorData.anomaliasCausais++;
          totalAnomalias++;
        }

        // Detecta gaps lógicos (mensagem perdida)
        const gap = clock - sensorData.ultimoClock;
        if (gap > 1) {
          const perdidos = gap - 1;
          sensorData.mensagensPerdidas += perdidos;
          totalPerdas += perdidos;
        }
      }

      sensorData.ultimoClock = clock;
      sensorData.ultimoTime = time;
    });

    res.json({
      success: true,
      timestamp: new Date(),
      metricasGlobais: {
        totalSensoresAuditados: Object.keys(auditBySensor).length,
        totalAnomaliasCausais: totalAnomalias,
        totalMensagensPerdidas: totalPerdas,
        statusIntegridade: totalAnomalias === 0 && totalPerdas === 0 ? 'CONCORDANTE' : 'DEGRADADO'
      },
      sensores: Object.values(auditBySensor),
      pontos: records // Adicionado pontos para plotagem no frontend
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 5. 🌐 MÉTRICAS DO POOL TCP (Postgres Pool)
app.get('/api/audit/pool-stats', (req, res) => {
  try {
    res.json({
      success: true,
      totalCount: pool.totalCount,
      idleCount: pool.idleCount,
      waitingCount: pool.waitingCount
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Fallback para SPA (se necessário, embora seja uma página única)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(port, () => {
  console.log(`📡 DB Audit Engine ativo na porta ${port}`);
});
