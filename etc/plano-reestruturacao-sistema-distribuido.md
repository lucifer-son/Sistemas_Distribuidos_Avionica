# Plano de Reestruturacao do Sistema Distribuido de Avionica

## 1. Objetivo

Este documento descreve o plano de evolucao do projeto de avionica distribuida para atender aos requisitos da disciplina de Sistemas Distribuidos.

A proposta e transformar o projeto atual em uma aplicacao distribuida completa, com modulos independentes, comunicacao assíncrona por mensagens, persistencia em banco de dados, backend web, frontend web e execucao em containers.

## 2. Requisitos da Disciplina

O professor solicitou que o sistema tenha:

- Um sistema distribuido de escolha da equipe.
- Pelo menos dois modulos distribuidos por integrante da equipe.
- Caso seja feito individualmente, pelo menos tres modulos.
- Interface grafica para permitir que o usuario acesse todas as funcionalidades do sistema.
- Opcionalmente, middleware orientado a mensagens, como Kafka ou RabbitMQ.
- Opcionalmente, execucao em containers, como Docker ou Kubernetes.

Como o grupo possui 9 pessoas, o sistema devera ter pelo menos 18 modulos distribuidos que contem para a avaliacao.

Observacao importante: PostgreSQL, Kafka, Zookeeper e outros componentes de infraestrutura ajudam o sistema a funcionar, mas nao serao considerados modulos desenvolvidos pela equipe. Portanto, eles nao entram na contagem dos 18 modulos.

## 3. Tema do Sistema

O sistema sera uma plataforma distribuida de monitoramento e gerenciamento avionico.

A aplicacao devera simular uma arquitetura de aeronave na qual diferentes processos independentes publicam, processam e consomem dados de voo, sensores e planejamento de rota.

O usuario acessara uma interface web para:

- Consultar dados de voo.
- Informar origem e destino de uma rota.
- Visualizar calculos do FMS.
- Acompanhar eventos publicados pelos modulos distribuidos.
- Consultar historico persistido no banco de dados.
- Verificar o estado dos modulos do sistema.

## 4. Arquitetura Proposta

A nova arquitetura sera composta por modulos de aplicacao, middleware e infraestrutura.

### 4.1 Modulos que contam para a avaliacao

Estes sao os modulos desenvolvidos pela equipe. A proposta abaixo possui 20 modulos, deixando uma margem acima do minimo de 18 exigido para 9 integrantes.

| Modulo | Tecnologia | Responsabilidade | Conta como modulo distribuido |
| --- | --- | --- | --- |
| 1. Frontend Web | Vue.js + Bootstrap | Interface grafica para acesso dos usuarios | Sim |
| 2. API Gateway / Backend Principal | Java 25 + Spring Boot | API REST, validacoes, entrada principal do sistema | Sim |
| 3. Servico de Rotas | Java 25 + Spring Boot | Gerenciar solicitacoes e historico de rotas | Sim |
| 4. Servico de Telemetria | Java 25 + Spring Boot | Receber, consolidar e consultar dados de telemetria | Sim |
| 5. Servico de Eventos | Java 25 + Spring Boot | Registrar eventos tecnicos e operacionais do sistema | Sim |
| 6. Servico de Status dos Modulos | Java 25 + Spring Boot | Monitorar disponibilidade dos processos distribuidos | Sim |
| 7. FMS API | Python + Docker | Calcular rota, distancia e ETA usando API externa | Sim |
| 8. Sensor de Velocidade | Python + Docker | Publicar velocidade e Mach simulados | Sim |
| 9. Sensor de Altitude | Python + Docker | Publicar altitude e variacao vertical | Sim |
| 10. Sensor de Atitude | Python + Docker | Publicar pitch, roll e yaw | Sim |
| 11. Sensor de Combustivel | Python + Docker | Publicar nivel e consumo estimado de combustivel | Sim |
| 12. Sensor de Freio | Python + Docker | Publicar estado do sistema de freios | Sim |
| 13. Radar Externo | Python + Docker | Simular deteccao de trafego ou objetos externos | Sim |
| 14. Computador de Navegacao | Python + Docker | Processar informacoes de navegacao e posicao | Sim |
| 15. Computador de Voo | Python + Docker | Consolidar dados criticos de voo | Sim |
| 16. Servico de Alertas | Java 25 + Spring Boot | Gerar alertas a partir de eventos e telemetria | Sim |
| 17. Servico de Auditoria | Java 25 + Spring Boot | Registrar acoes do usuario e decisoes do sistema | Sim |
| 18. Servico de Relatorios | Java 25 + Spring Boot | Gerar consultas e relatorios operacionais | Sim |
| 19. Simulador de Piloto/CDU | Python ou Java + Docker | Simular comandos de rota e operacoes do piloto | Sim |
| 20. Servico de Notificacoes | Java 25 + Spring Boot | Enviar notificacoes internas para a interface | Sim |

### 4.2 Infraestrutura que nao conta como modulo

| Componente | Tecnologia | Responsabilidade | Conta como modulo distribuido |
| --- | --- | --- | --- |
| Banco de Dados | PostgreSQL | Persistencia de rotas, eventos, telemetria e auditoria | Nao |
| Broker de Mensagens | Kafka | Comunicacao assíncrona entre modulos | Nao |
| Coordenador Kafka, se necessario | Zookeeper ou KRaft | Coordenacao do cluster Kafka | Nao |
| Docker Compose | Docker | Orquestracao local dos containers | Nao |

Com essa estrutura, o projeto atende ao requisito de 9 integrantes, pois possui 20 modulos de aplicacao planejados, acima dos 18 modulos minimos exigidos.

### 4.3 Divisao Sugerida por Integrante

Cada integrante devera ficar responsavel por pelo menos dois modulos. A divisao abaixo e uma sugestao inicial e pode ser ajustada conforme o conhecimento de cada pessoa.

| Integrante | Modulo 1 | Modulo 2 |
| --- | --- | --- |
| Integrante 1 | Frontend Web | Servico de Notificacoes |
| Integrante 2 | API Gateway / Backend Principal | Servico de Status dos Modulos |
| Integrante 3 | Servico de Rotas | FMS API |
| Integrante 4 | Servico de Telemetria | Sensor de Velocidade |
| Integrante 5 | Servico de Eventos | Sensor de Altitude |
| Integrante 6 | Servico de Alertas | Sensor de Atitude |
| Integrante 7 | Servico de Auditoria | Sensor de Combustivel |
| Integrante 8 | Servico de Relatorios | Radar Externo |
| Integrante 9 | Computador de Navegacao | Computador de Voo |

O modulo `Sensor de Freio` e o `Simulador de Piloto/CDU` ficam como modulos extras para reforcar a demonstracao e dar margem caso algum modulo seja simplificado durante o desenvolvimento.

## 5. Visao Geral do Fluxo

1. O usuario acessa o frontend Vue.js.
2. O frontend chama o backend Spring Boot por API REST.
3. O backend registra solicitacoes e consulta dados no PostgreSQL.
4. Para operacoes assíncronas, o backend publica eventos no Kafka.
5. Os sensores Python publicam telemetria em topicos Kafka.
6. O FMS Python consome ou recebe solicitacoes de rota, consulta a API externa e calcula distancia/ETA.
7. O FMS publica o resultado no Kafka ou responde ao backend.
8. Servicos Java especializados consomem eventos, aplicam regras e persistem os dados necessarios.
9. O frontend atualiza a tela com os dados processados.

## 6. Comunicacao Entre Modulos

### 6.1 REST

Sera usada para comunicacao direta entre frontend e backend.

Endpoints previstos:

- `GET /api/health`: verificar status do backend.
- `GET /api/modules`: listar status dos modulos distribuidos.
- `POST /api/routes`: solicitar uma nova rota.
- `GET /api/routes`: listar rotas calculadas.
- `GET /api/routes/{id}`: consultar detalhes de uma rota.
- `GET /api/events`: listar eventos do sistema.
- `GET /api/telemetry/latest`: consultar telemetria mais recente.

### 6.2 Kafka

Sera usado para comunicacao orientada a mensagens entre backend, FMS e modulos de sensores.

Topicos previstos:

| Topico | Produtor | Consumidor | Finalidade |
| --- | --- | --- | --- |
| `avionica.route.requested` | Backend | FMS Python | Solicitar calculo de rota |
| `avionica.route.calculated` | FMS Python | Backend | Retornar rota calculada |
| `avionica.telemetry.speed` | Sensor de Velocidade | Servico de Telemetria | Enviar velocidade e Mach |
| `avionica.telemetry.altitude` | Sensor de Altitude | Servico de Telemetria | Enviar altitude |
| `avionica.telemetry.attitude` | Sensor de Atitude | Servico de Telemetria | Enviar atitude da aeronave |
| `avionica.telemetry.fuel` | Sensor de Combustivel | Servico de Telemetria e Alertas | Enviar dados de combustivel |
| `avionica.telemetry.brake` | Sensor de Freio | Servico de Telemetria e Alertas | Enviar estado dos freios |
| `avionica.telemetry.radar` | Radar Externo | Servico de Telemetria e Alertas | Enviar dados de radar |
| `avionica.flight.computer` | Computador de Voo | Backend e Servico de Eventos | Enviar consolidacao de voo |
| `avionica.navigation.computer` | Computador de Navegacao | Backend e FMS | Enviar dados de navegacao |
| `avionica.alert.generated` | Servico de Alertas | Backend e Frontend | Informar alertas gerados |
| `avionica.system.events` | Todos os modulos | Servico de Eventos | Registrar eventos gerais |
| `avionica.module.health` | Todos os modulos | Servico de Status dos Modulos | Informar status dos modulos |

## 7. Banco de Dados PostgreSQL

O PostgreSQL sera responsavel por armazenar dados historicos e permitir consulta pela interface web.

Importante: o banco de dados nao conta como modulo distribuido para a avaliacao. Ele sera tratado como infraestrutura de persistencia.

Tabelas previstas:

### 7.1 `routes`

Armazena rotas solicitadas e calculadas.

Campos previstos:

- `id`
- `origin_icao`
- `destination_icao`
- `distance_nm`
- `eta_minutes`
- `status`
- `created_at`
- `updated_at`

### 7.2 `telemetry_events`

Armazena dados de sensores e telemetria.

Campos previstos:

- `id`
- `source_module`
- `event_type`
- `payload`
- `created_at`

### 7.3 `system_events`

Armazena eventos relevantes do sistema.

Campos previstos:

- `id`
- `module_name`
- `severity`
- `message`
- `payload`
- `created_at`

### 7.4 `module_status`

Armazena o ultimo estado conhecido de cada modulo.

Campos previstos:

- `id`
- `module_name`
- `status`
- `last_seen_at`
- `details`

## 8. Backend Java 25 com Spring Boot

O backend sera o ponto central da aplicacao.

Responsabilidades:

- Expor API REST para o frontend.
- Persistir dados no PostgreSQL.
- Publicar e consumir mensagens do Kafka.
- Orquestrar solicitacoes de rota.
- Agregar dados vindos dos modulos Python.
- Disponibilizar status dos modulos.
- Servir como camada de seguranca e validacao das entradas do usuario.

Dependencias previstas:

- Spring Web
- Spring Data JPA
- PostgreSQL Driver
- Spring for Apache Kafka
- Spring Validation
- Spring Boot Actuator

Gerenciamento de dependencias:

- O backend sera gerenciado pelo Gradle Wrapper, usando `gradlew`.
- O repositorio devera versionar `gradlew`, `gradlew.bat`, `settings.gradle`, `build.gradle` ou `build.gradle.kts`.
- Cada modulo Java podera ter seu proprio `build.gradle` ou participar de um projeto Gradle multi-module.
- O uso do Gradle Wrapper evita que todos os integrantes precisem instalar a mesma versao do Gradle manualmente.

Observacao: antes de iniciar a implementacao, sera necessario validar a compatibilidade da versao escolhida do Spring Boot com Java 25. Se houver incompatibilidade, o plano B sera usar a versao LTS de Java suportada oficialmente pelo Spring Boot adotado.

## 9. Frontend Vue.js com Bootstrap

O frontend sera a interface grafica obrigatoria do projeto.

Telas previstas:

- Dashboard principal.
- Tela de planejamento de rota.
- Tela de historico de rotas.
- Tela de telemetria.
- Tela de eventos do sistema.
- Tela de status dos modulos.

Funcionalidades previstas:

- Formulario para informar ICAO de origem e destino.
- Visualizacao do resultado da rota.
- Listagem de eventos em tempo quase real.
- Cards ou tabelas para status dos modulos.
- Indicadores de disponibilidade do backend, FMS, Kafka e banco.

Tecnologias:

- Vue.js
- Bootstrap
- Axios ou Fetch API
- Vue Router
- Node.js
- npm

Gerenciamento de dependencias:

- O frontend sera gerenciado por Node.js e npm.
- O projeto devera versionar `package.json` e `package-lock.json`.
- O comando `npm install` sera usado para instalar dependencias.
- O comando `npm run dev` sera usado durante desenvolvimento local.
- O comando `npm run build` sera usado para gerar a versao final do frontend.

## 10. FMS API em Python

O modulo FMS atual sera preservado, mas reestruturado para funcionar como um processo distribuido em container.

Responsabilidades:

- Receber solicitacoes de rota.
- Consultar a API externa de aeroportos usando a chave configurada por `.env`.
- Calcular distancia entre aeroportos.
- Calcular ETA estimado.
- Publicar resultado para o backend via Kafka ou endpoint REST.

Melhorias planejadas:

- Remover configuracoes fixas do codigo.
- Usar variaveis de ambiente.
- Padronizar logs.
- Criar tratamento de erro para falha na API externa.
- Criar Dockerfile especifico ou imagem compartilhada para os modulos Python.

## 11. Docker e Infraestrutura

O projeto devera ser executado por `docker-compose`.

Servicos previstos:

- `frontend`
- `backend-gateway`
- `route-service`
- `telemetry-service`
- `event-service`
- `module-status-service`
- `alert-service`
- `audit-service`
- `report-service`
- `notification-service`
- `fms-api`
- `postgres`
- `kafka`
- `zookeeper` ou alternativa exigida pela imagem Kafka escolhida
- `sensor-speed`
- `sensor-altitude`
- `sensor-attitude`
- `sensor-fuel`
- `sensor-brake`
- `sensor-radar`
- `navigation-computer`
- `flight-computer`
- `pilot-cdu-simulator`

Arquivos previstos:

- `docker-compose.yml`
- `.env`
- `.env.example`
- `backend/Dockerfile`
- `backend/gradlew`
- `backend/gradlew.bat`
- `backend/settings.gradle`
- `backend/build.gradle` ou `backend/build.gradle.kts`
- `frontend/Dockerfile`
- `frontend/package.json`
- `frontend/package-lock.json`
- `Software_Aviao/docker/Dockerfile`

Ferramentas de desenvolvimento previstas:

- Node.js: necessario para executar npm e gerenciar o frontend Vue.js.
- npm: necessario para instalar Bootstrap, Vue Router, Axios e demais dependencias do frontend.
- Gradle Wrapper: necessario para build, testes e execucao dos modulos Java/Spring Boot.
- Docker: necessario para subir os modulos como containers.

Variaveis de ambiente previstas:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `SPRING_DATASOURCE_URL`
- `SPRING_DATASOURCE_USERNAME`
- `SPRING_DATASOURCE_PASSWORD`
- `KAFKA_BOOTSTRAP_SERVERS`
- `FMS_API_KEY`

## 12. Estrutura de Pastas Proposta

```text
Sistemas_Distribuidos_Avionica/
├── backend/
│   ├── src/
│   ├── gradlew
│   ├── gradlew.bat
│   ├── settings.gradle
│   ├── build.gradle
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── package-lock.json
│   └── Dockerfile
├── Software_Aviao/
│   ├── fms_distribuido.py
│   ├── sensores_voo.py
│   ├── radar_externo.py
│   ├── computador_navegacao.py
│   ├── computador_voo.py
│   ├── sensor_altitude.py
│   ├── sensor_atitude.py
│   ├── sensor_combustivel.py
│   ├── sensor_freio.py
│   ├── sensor_velocidade.py
│   ├── simulador_piloto_cdu.py
│   └── docker/
├── etc/
│   ├── plano-reestruturacao-sistema-distribuido.md
│   ├── como_rodar.md
│   └── req/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## 13. Etapas de Implementacao

### Etapa 1: Organizacao do Projeto

- Criar estrutura `backend/`.
- Criar estrutura `frontend/`.
- Configurar Node.js e npm para o frontend.
- Configurar Gradle Wrapper para o backend Java/Spring Boot.
- Mover ou revisar arquivos Docker.
- Criar `.env.example`.
- Atualizar README com visao geral da nova arquitetura.

### Etapa 2: Banco de Dados

- Subir PostgreSQL via Docker.
- Criar configuracao inicial do banco.
- Criar entidades principais no backend.
- Criar migrations, preferencialmente com Flyway ou Liquibase.

### Etapa 3: Backend Spring Boot

- Criar projeto Spring Boot principal.
- Definir se os servicos Java serao implementados como projetos Spring Boot separados ou como modulos separados executados em containers independentes.
- Configurar build com `gradlew`.
- Validar comandos `gradlew build` e `gradlew test`.
- Configurar conexao com PostgreSQL.
- Criar endpoints REST.
- Criar camada de servico para rotas, telemetria e eventos.
- Configurar Actuator para health check.

### Etapa 4: Kafka

- Subir Kafka via Docker Compose.
- Criar produtores e consumidores nos servicos Java.
- Adaptar modulos Python para publicar/consumir mensagens.
- Definir formato padrao das mensagens em JSON.

### Etapa 5: FMS Python em Docker

- Adaptar FMS para receber solicitacoes pelo Kafka ou REST.
- Usar `FMS_API_KEY` via `.env`.
- Criar logs claros para demonstracao.
- Publicar resultado da rota no Kafka.

### Etapa 6: Frontend Vue.js

- Criar projeto Vue.
- Instalar dependencias com `npm install`.
- Adicionar Bootstrap.
- Implementar layout principal.
- Criar telas do dashboard, rotas, telemetria, eventos e status.
- Integrar frontend com backend.
- Validar comandos `npm run dev` e `npm run build`.

### Etapa 7: Integracao Final

- Criar `docker-compose.yml` principal.
- Subir todos os servicos juntos.
- Validar se pelo menos 18 modulos de aplicacao estao rodando como processos independentes.
- Validar fluxo completo:
  - usuario solicita rota no frontend;
  - backend publica evento;
  - FMS calcula rota;
  - backend salva no banco;
  - frontend exibe resultado.

### Etapa 8: Documentacao e Apresentacao

- Atualizar `README.md`.
- Atualizar `etc/como_rodar.md`.
- Criar diagrama da arquitetura.
- Criar roteiro de demonstracao.
- Documentar quais 18 ou mais modulos contam para os requisitos da disciplina.

## 14. Criterios de Aceite

O projeto sera considerado pronto quando:

- O sistema possuir pelo menos 18 modulos de aplicacao executando separadamente para atender aos 9 integrantes.
- PostgreSQL, Kafka, Zookeeper e Docker Compose estiverem documentados como infraestrutura, nao como modulos da equipe.
- A interface web permitir acessar as funcionalidades principais.
- O backend conseguir persistir dados no PostgreSQL.
- O FMS Python estiver em container e usando chave por variavel de ambiente.
- O Kafka estiver funcionando como middleware de mensagens.
- O fluxo de solicitacao de rota estiver completo.
- O projeto puder ser executado por Docker Compose.
- A documentacao explicar como rodar e demonstrar o sistema.

## 15. Riscos e Pontos de Atencao

- Compatibilidade entre Java 25 e a versao escolhida do Spring Boot.
- Complexidade extra ao usar Kafka, principalmente em ambiente Docker.
- Tempo de implementacao do frontend completo.
- Padronizacao das versoes de Node.js, npm e Java entre os integrantes.
- Garantir que o Gradle Wrapper seja usado em vez de depender do Gradle instalado localmente.
- Dependencia da API externa usada pelo FMS.
- Necessidade de padronizar mensagens JSON entre Python e Java.
- Garantir que segredos, como `FMS_API_KEY`, nao sejam enviados ao Git.

## 16. Plano B

Caso o prazo fique curto, a prioridade sera:

1. Backend Spring Boot com PostgreSQL.
2. Frontend Vue.js com as telas principais.
3. FMS Python em Docker.
4. Comunicacao inicial por REST.
5. Kafka como evolucao assíncrona se houver tempo suficiente.

Mesmo no plano reduzido, o sistema precisa preservar a contagem minima de 18 modulos para a equipe de 9 pessoas. A reducao deve acontecer no escopo interno de cada modulo, nao na quantidade de processos distribuidos.

Exemplo de reducao aceitavel:

- Manter todos os sensores como processos separados.
- Simplificar telas do frontend.
- Reduzir regras internas dos servicos Java.
- Manter Kafka para eventos principais.
- Evitar funcionalidades avancadas de relatorio, mas manter o servico de relatorios ativo com consultas basicas.

## 17. Entregaveis Esperados

- Codigo-fonte organizado por modulo.
- Frontend com `package.json` e `package-lock.json`.
- Backend com Gradle Wrapper e arquivos de build.
- Docker Compose funcional.
- Frontend web acessivel pelo navegador.
- Backend com API REST documentada.
- FMS Python containerizado.
- PostgreSQL configurado.
- Kafka configurado, se mantido no escopo final.
- Documentacao em Markdown na pasta `etc`.
- README atualizado com instrucoes de execucao.
