# Plano de Reestruturação do Sistema Distribuido de Aviônica

## 1. Objetivo

Este documento descreve o plano de evolucao do projeto de aviônica distribuida para atender aos requisitos da disciplina de Sistemas distribuídos e Análise de Desempenho.

A proposta e transformar o projeto atual em uma aplicação distribuida completa, com módulos independentes, comunicação assíncrona por mensagens, persistência em banco de dados, backend web, frontend web e execução em containers.

## 2. Requisitos da Disciplina

O professor solicitou que o sistema tenha:

- Um sistema distribuido de escolha da equipe.
- Pelo menos dois módulos distribuídos por integrante da equipe.
- Caso seja feito individualmente, pelo menos três módulos.
- Interface gráfica para permitir que o usuário acesse todas as funcionalidades do sistema.
- Opcionalmente, middleware orientado a mensagens, como Kafka ou RabbitMQ.
- Opcionalmente, execução em containers, como Docker ou Kubernetes.

Como o grupo possui 9 pessoas, o sistema devera ter pelo menos 18 módulos distribuídos para a avaliacao.

Observação importante: PostgreSQL, Kafka, Zookeeper e outros componentes de infraestrutura ajudam o sistema a funcionar, mas nao serão considerados módulos desenvolvidos pela equipe. Portanto, eles nao entram na contagem dos 18 módulos.

## 3. Tema do Sistema

O sistema sera uma plataforma distribuida de monitoramento e gerenciamento aviônico.

A aplicacao devera simular uma arquitetura de aeronave na qual diferentes processos independentes publicam, processam e consomem dados de voo, sensores e planejamento de rota.

O usuario acessara uma interface web para:

- Consultar dados de voo.
- Informar origem e destino de uma rota.
- Visualizar calculos do FMS.
- Acompanhar eventos publicados pelos modulos distribuídos.
- Consultar histórico persistido no banco de dados.
- Verificar o estado dos módulos do sistema.

## 4. Arquitetura Proposta

A nova arquitetura sera composta por módulos de aplicação, middleware e infraestrutura.

### 4.1 Módulos que contam para a avaliação

Aqui estão os modulos desenvolvidos pela equipe. A proposta abaixo possui 20 modulos, deixando uma margem acima do minimo de 18 exigido para 9 integrantes.

| Modulo | Tecnologia | Responsabilidade | Conta como módulo distribuído (?) |
| --- | --- | --- | --- |
| 1. Frontend Web | Vue.js + Bootstrap | Interface gráfica para acesso dos usuários | Sim |
| 2. API Gateway / Backend Principal | Java 25 + Spring Boot | API REST, validações, entrada principal do sistema | Sim |
| 3. Servico de Rotas | Java 25 + Spring Boot | Gerenciar solicitações e histórico de rotas | Sim |
| 4. Servico de Telemetria | Java 25 + Spring Boot | Receber, consolidar e consultar dados de telemetria | Sim |
| 5. Servico de Eventos | Java 25 + Spring Boot | Registrar eventos técnicos e operacionais do sistema | Sim |
| 6. Servico de Status dos Módulos | Java 25 + Spring Boot | Monitorar disponibilidade dos processos distribuídos | Sim |
| 7. FMS API | Python + Docker | Calcular rota, distancia e ETA usando API externa | Sim |
| 8. Sensor de Velocidade | Python + Docker | Publicar velocidade e Mach simulados | Sim |
| 9. Sensor de Altitude | Python + Docker | Publicar altitude e variação vertical | Sim |
| 10. Sensor de Atitude | Python + Docker | Publicar pitch, roll e yaw | Sim |
| 11. Sensor de Combustível | Python + Docker | Publicar nível e consumo estimado de combustível | Sim |
| 12. Sensor de Freio | Python + Docker | Publicar estado do sistema de freios | Sim |
| 13. Radar Externo | Python + Docker | Simular deteccao de trafego ou objetos externos | Sim |
| 14. Computador de Navegação | Python + Docker | Processar informações de navegação e posição | Sim |
| 15. Computador de Voo | Python + Docker | Consolidar dados críticos de voo | Sim |
| 16. Servico de Alertas | Java 25 + Spring Boot | Gerar alertas a partir de eventos e telemetria | Sim |
| 17. Servico de Auditoria | Java 25 + Spring Boot | Registrar ações do usuário e decisões do sistema | Sim |
| 18. Servico de Relatórios | Java 25 + Spring Boot | Gerar consultas e relatorios operacionais | Sim |
| 19. Simulador de Piloto/CDU | Python ou Java + Docker | Simular comandos de rota e operacoes do piloto | Sim |
| 20. Servico de Notificações | Java 25 + Spring Boot | Enviar notificações internas para a interface | Sim |

### 4.2 Infraestrutura que nao conta como módulo

| Componente | Tecnologia | Responsabilidade | Conta como módulo distribuído |
| --- | --- | --- | --- |
| Banco de Dados | PostgreSQL | Persistencia de rotas, eventos, telemetria e auditoria | Não |
| Broker de Mensagens | Kafka | Comunicacao assíncrona entre módulos | Não |
| Coordenador Kafka, se necessario | Zookeeper ou KRaft | Coordenacao do cluster Kafka | Não |
| Docker Compose | Docker | Orquestracao local dos containers | Não |

Com essa estrutura, o projeto atende ao requisito de 9 integrantes, pois possui 20 módulos de aplicação planejados, acima dos 18 módulos minímos exigidos.

### 4.3 Divisao Sugerida por Integrante

Cada integrante devera ficar responsavel por pelo menos dois módulos. A divisão abaixo é uma sugestao inicial e pode ser ajustada conforme o conhecimento de cada integrante.

| Integrante | Módulo 1 | Módulo 2 |
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

O modulo `Sensor de Freio` e o `Simulador de Piloto/CDU` ficam como módulos extras para reforçar a demonstração e dar margem caso algum módulo seja simplificado durante o desenvolvimento.

## 5. Visao Geral do Fluxo

1. O usuário acessa o frontend Vue.js.
2. O frontend chama o backend Spring Boot por API REST.
3. O backend registra solicitacoes e consulta dados no PostgreSQL.
4. Para operacoes assíncronas, o backend publica eventos no Kafka.
5. Os sensores Python publicam telemetria em tópicos Kafka.
6. O FMS Python consome ou recebe solicitacoes de rota, consulta a API externa e calcula distancia/ETA.
7. O FMS publica o resultado no Kafka ou responde ao backend.
8. Serviços Java especializados consomem eventos, aplicam regras e persistem os dados necessários.
9. O frontend atualiza a tela com os dados processados.

## 6. Comunicação Entre Módulos

### 6.1 REST

Será usada para comunicação direta entre frontend e backend.

Endpoints previstos:

- `GET /api/health`: verificar status do backend.
- `GET /api/modules`: listar status dos módulos distribuídos.
- `POST /api/routes`: solicitar uma nova rota.
- `GET /api/routes`: listar rotas calculadas.
- `GET /api/routes/{id}`: consultar detalhes de uma rota.
- `GET /api/events`: listar eventos do sistema.
- `GET /api/telemetry/latest`: consultar telemetria mais recente.

### 6.2 Kafka

Será usado para comunicaçao orientada a mensagens entre backend, FMS e módulos de sensores.

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

O PostgreSQL sera responsavel por armazenar dados históricos e permitir consulta pela interface web.

Importante: o banco de dados não conta como módulo distribuido para a avaliação. Ele será tratado como infraestrutura de persistência.

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

Armazena o ultimo estado conhecido de cada módulo.

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

Gerenciamento de dependências:

- O backend sera gerenciado pelo Gradle Wrapper, usando `gradlew`.
- O repositório devera versionar `gradlew`, `gradlew.bat`, `settings.gradle`, `build.gradle` ou `build.gradle.kts`.
- Cada módulo Java podera ter seu proprio `build.gradle` ou participar de um projeto Gradle multi-module.
- O uso do Gradle Wrapper evita que todos os integrantes precisem instalar a mesma versao do Gradle manualmente.

Observaçao: antes de iniciar a implementação, será necessário validar a compatibilidade da versão escolhida do Spring Boot com Java 25. Se houver incompatibilidade, o plano B sera usar a versao LTS de Java suportada oficialmente pelo Spring Boot adotado.

## 9. Frontend Vue.js com Bootstrap

O frontend sera a interface gráfica obrigatória do projeto.

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
- O comando `npm install` será usado para instalar dependencias.
- O comando `npm run dev` será usado durante desenvolvimento local.
- O comando `npm run build` sera usado para gerar a versao final do frontend.

## 10. FMS API em Python

O modulo FMS atual sera preservado, mas reestruturado para funcionar como um processo distribuido em container.

Responsabilidades:

- Receber solicitacoes de rota.
- Consultar a API externa de aeroportos usando a chave configurada por `.env`.
- Calcular distância entre aeroportos.
- Calcular ETA estimado.
- Publicar resultado para o backend via Kafka ou endpoint REST.

Melhorias planejadas:

- Remover configuracoes fixas do codigo.
- Usar variáveis de ambiente.
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

- Node.js: necessário para executar npm e gerenciar o frontend Vue.js.
- npm: necessário para instalar Bootstrap, Vue Router, Axios e demais dependências do frontend.
- Gradle Wrapper: necessário para build, testes e execução dos módulos Java/Spring Boot.
- Docker: necessário para subir os módulos como containers.

Variáveis de ambiente previstas:

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
Sistemas_distribuídos_Avionica/
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

### Etapa 1: Organização do Projeto

- Criar estrutura `backend/`.
- Criar estrutura `frontend/`.
- Configurar Node.js e npm para o frontend.
- Configurar Gradle Wrapper para o backend Java/Spring Boot.
- Mover ou revisar arquivos Docker.
- Criar `.env.example`.
- Atualizar README com visão geral da nova arquitetura.

### Etapa 2: Banco de Dados

- Subir PostgreSQL via Docker.
- Criar configuracao inicial do banco.
- Criar entidades principais no backend.
- Criar migrations, preferencialmente com Flyway ou Liquibase.

### Etapa 3: Backend Spring Boot

- Criar projeto Spring Boot principal.
- Definir se os servicos Java serão implementados como projetos Spring Boot separados ou como módulos separados executados em containers independentes.
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

### Etapa 7: Integracão Final

- Criar `docker-compose.yml` principal.
- Subir todos os servicos juntos.
- Validar se pelo menos 18 módulos de aplicaçao estão rodando como processos independentes.
- Validar fluxo completo:
  - usuário solicita rota no frontend;
  - backend publica evento;
  - FMS calcula rota;
  - backend salva no banco;
  - frontend exibe resultado.

### Etapa 8: Documentacao e Apresentacao

- Atualizar `README.md`.
- Atualizar `etc/como_rodar.md`.
- Criar diagrama da arquitetura.
- Criar roteiro de demonstracao.
- Documentar quais 18 ou mais módulos contam para os requisítos da disciplina.

## 14. Critérios de Aceite

O projeto será considerado pronto quando:

- O sistema possuir pelo menos 18 módulos de aplicação executando separadamente para atender aos 9 integrantes.
- PostgreSQL, Kafka, Zookeeper e Docker Compose estiverem documentados como infraestrutura, nao como módulos da equipe.
- A interface web permitir acessar as funcionalidades principais.
- O backend conseguir persistir dados no PostgreSQL.
- O FMS Python estiver em container e usando chave por variável de ambiente.
- O Kafka estiver funcionando como middleware de mensagens.
- O fluxo de solicitaçao de rota estiver completo.
- O projeto puder ser executado por Docker Compose.
- A documentação explicar como rodar e demonstrar o sistema.

## 15. Riscos e Pontos de Atencao

- Compatibilidade entre Java 25 e a versão escolhida do Spring Boot.
- Complexidade extra ao usar Kafka, principalmente em ambiente Docker.
- Tempo de implementação do frontend completo.
- Padronização das versoes de Node.js, npm e Java entre os integrantes.
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
5. Kafka como evolução assíncrona se houver tempo suficiente.

Mesmo no plano reduzido, o sistema precisa preservar a contagem minima de 18 módulos para a equipe de 9 pessoas. A redução deve acontecer no escopo interno de cada módulo, nao na quantidade de processos distribuídos.

Exemplo de reducao aceitavel:

- Manter todos os sensores como processos separados.
- Simplificar telas do frontend.
- Reduzir regras internas dos servicos Java.
- Manter Kafka para eventos principais.
- Evitar funcionalidades avancadas de relatório, mas manter o serviço de relatórios ativo com consultas básicas.

## 17. Entregaveis Esperados

- Código-fonte organizado por módulo.
- Frontend com `package.json` e `package-lock.json`.
- Backend com Gradle Wrapper e arquivos de build.
- Docker Compose funcional.
- Frontend web acessível pelo navegador.
- Backend com API REST documentada.
- FMS Python containerizado.
- PostgreSQL configurado.
- Kafka configurado, se mantido no escopo final.
- Documentação em Markdown na pasta `etc`.
- README atualizado com instruções de execução.
