# CDU-07: Exportação de Auditoria da Caixa Preta

## 1. Descrição
Permite a extração dos registos brutos e consolidados da aeronave gerados pelo módulo Read-Only da "Caixa Preta". Essencial para análises pós-voo ou em caso de simulação de acidentes.

## 2. Atores
- **Utilizador:** Auditor de voo ou Engenheiro de Manutenção.
- **Módulo de Auditoria (`caixa_preta.py`):** Módulo passivo que grava tudo em ficheiros de baixo nível.

## 3. Pré-condições
- Existência de dados de telemetria já consolidados no PostgreSQL e persistidos pelos nós de auditoria.

## 4. Fluxo Principal
1. O utilizador acede ao ecrã **"Caixa Preta / Auditoria"** no Frontend.
2. O utilizador clica no botão **"Gerar Relatório de Voo (FDR)"**.
3. O Frontend dispara uma requisição de relatório para o Backend Spring Boot.
4. O Backend varre o PostgreSQL agregando todos os registos críticos, avisos, injeções de falha e leituras de sensores ocorridas na sessão atual.
5. O Backend empacota os dados e devolve-os no formato `.CSV` ou `.PDF`.
6. O navegador do utilizador inicia o download do ficheiro de auditoria.

## 5. Fluxos Alternativos
- **5a. Limpeza da Caixa Preta:**
  1. Após exportar com sucesso, um administrador com privilégios seleciona a opção "Puxar Data Recorder e Limpar Sessão".
  2. O backend confirma a exportação e limpa a base de dados (tabelas de sessão temporárias) para um novo ensaio de voo.

## 6. Pós-condições
- Um ficheiro imutável e estruturado fica disponível na máquina local do utilizador para análise formal dos tempos e comportamentos do sistema.
