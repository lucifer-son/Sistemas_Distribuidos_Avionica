# Divisao de Modulos do Projeto

## Regra Simples

Para evitar confusao na apresentacao, vamos usar esta regra:

**Modulo distribuido e um processo executavel separado.**

Exemplos de modulo:

- um backend Spring Boot rodando em um container;
- um frontend Vue rodando em um container;
- uma API/simulador de sensor rodando em um processo separado;
- um consumidor Kafka rodando em um processo separado;
- um produtor Kafka rodando em um processo separado.

Nao sao modulos:

- banco de dados;
- Kafka;
- Docker;
- Docker Compose;
- pasta `service`;
- pasta `dto`;
- pasta `model`;
- tela Vue isolada;
- componente Vue isolado;
- metodo, classe ou camada interna de codigo.

## Arquitetura Que Sera Defendida

O sistema tera:

1. APIs/simuladores gerando dados dos sensores.
2. Kafka recebendo esses dados em topicos.
3. Um unico backend Spring Boot consumindo o Kafka e salvando no banco.
4. Um frontend web em Vue consumindo o backend por REST.
5. PostgreSQL armazenando os dados.

Kafka e PostgreSQL sao infraestrutura. Eles ajudam o sistema a funcionar, mas nao contam como modulo da equipe.

## Sobre o Backend

O projeto tera **um unico backend Spring Boot**.

Dentro dele podem existir:

- `controller`;
- `service`;
- `dto`;
- `model`;
- `repository`;
- `KafkaListener`.

Essas partes nao contam como modulos separados, porque todas rodam dentro do mesmo processo do backend.

Portanto:

- backend Spring Boot = 1 modulo;
- `service`, `dto` e `model` = 0 modulo;
- cada consumidor Kafka dentro do mesmo backend = responsabilidade interna, nao processo separado.

Se a equipe quiser contar consumidores Kafka como modulos separados, eles precisam rodar como processos/containers separados do backend principal.

## Sobre o Frontend

O frontend sera web e feito em Vue.js.

O frontend Vue conta como **1 modulo**, porque e a interface grafica do sistema.

As telas Vue, como dashboard, CDU, telemetria, historico e status, sao tarefas internas do frontend. Elas nao devem ser apresentadas como modulos distribuidos separados.

Portanto:

- frontend Vue = 1 modulo;
- tela de dashboard = tarefa interna;
- tela CDU = tarefa interna;
- componente Vue = tarefa interna.

## Divisao de Modulos por Integrante

Como a equipe tem 9 integrantes, o ideal e apresentar 18 processos de aplicacao. A divisao abaixo evita contar banco, Kafka, telas Vue e camadas internas do backend.

| Integrante | Modulo 1 | Modulo 2 |
| --- | --- | --- |
| Gabriela | API Produtora de Telemetria de Voo | API Produtora de Status dos Modulos |
| Rafael | API/FMS de Planejamento de Rotas | API Produtora de Radar e Clima |
| Joao Lucas Cosme | API Produtora de Dados WAIC/Motor | API Injetora de Falhas e Eventos |
| Mariana | Backend Spring Boot unico | Sensor/API Produtora de Telemetria Geral |
| Nickolas | Consumidor Kafka de Persistencia separado | Sensor/API Produtora de Dados de Freio |
| Rafaely | Frontend Vue Web | Caixa Preta / Flight Data Recorder |
| Alison | Computador de Navegacao | Computador de Automacao / Anti-Ice |
| Joao Lucas Ribeiro | Producer/Ponte Kafka dos Sensores | Consumidor Kafka de Telemetria separado |
| Ana Luisa | Consumidor Kafka de Notificacoes separado | Sistema de Alertas Sonoros |

## Lista dos 18 Modulos Que Contam

| Nº | Modulo | Responsavel | Tipo |
| --- | --- | --- | --- |
| 1 | API Produtora de Telemetria de Voo | Gabriela | Produtor Kafka |
| 2 | API Produtora de Status dos Modulos | Gabriela | Produtor Kafka |
| 3 | API/FMS de Planejamento de Rotas | Rafael | Produtor/consumidor Kafka |
| 4 | API Produtora de Radar e Clima | Rafael | Produtor Kafka |
| 5 | API Produtora de Dados WAIC/Motor | Joao Lucas Cosme | Produtor Kafka |
| 6 | API Injetora de Falhas e Eventos | Joao Lucas Cosme | Produtor Kafka |
| 7 | Backend Spring Boot unico | Mariana | Backend REST e consumidor principal |
| 8 | Sensor/API Produtora de Telemetria Geral | Mariana | Produtor Kafka |
| 9 | Consumidor Kafka de Persistencia separado | Nickolas | Consumidor Kafka |
| 10 | Sensor/API Produtora de Dados de Freio | Nickolas | Produtor Kafka |
| 11 | Frontend Vue Web | Rafaely | Interface grafica |
| 12 | Caixa Preta / Flight Data Recorder | Rafaely | Consumidor de eventos |
| 13 | Computador de Navegacao | Alison | Produtor Kafka |
| 14 | Computador de Automacao / Anti-Ice | Alison | Consumidor e produtor Kafka |
| 15 | Producer/Ponte Kafka dos Sensores | Joao Lucas Ribeiro | Ponte de mensagens |
| 16 | Consumidor Kafka de Telemetria separado | Joao Lucas Ribeiro | Consumidor Kafka |
| 17 | Consumidor Kafka de Notificacoes separado | Ana Luisa | Consumidor Kafka |
| 18 | Sistema de Alertas Sonoros | Ana Luisa | Consumidor de eventos |

## Observacao Importante

Se alguns consumidores Kafka forem implementados dentro do backend Spring Boot unico, eles deixam de contar como processos separados. Nesse caso, a equipe deve compensar usando outros processos ja existentes no projeto, como:

- sensores de motor A, B e C;
- consenso TMR do motor;
- radar externo;
- computador de navegacao;
- computador de automacao;
- caixa preta;
- sistema de alertas;
- injetor de falhas.

Para a defesa ficar mais forte, a melhor opcao e subir os modulos contabilizados como containers/processos separados no Docker Compose.


