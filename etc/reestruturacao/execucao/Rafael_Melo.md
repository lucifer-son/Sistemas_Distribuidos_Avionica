# Tarefas de Execução — João Lucas Cosme

Você é responsável pelo desenvolvimento e integração de **dois módulos distribuídos** com foco em Simulação Física Redundante e Injeção de Falhas para testes de robustez.

---

## Módulo 1: Três Motores Redundantes (Motores A, B, C)

### Objetivo
Fornecer fluxos independentes de dados físicos do motor para testar a resiliência e o consenso no barramento.

### Especificação Técnica
- **Tecnologia:** Python (será executado como 3 instâncias de container separadas usando o mesmo script base, mas parametrizados por variáveis de ambiente: `MOTOR_ID=A`, `MOTOR_ID=B`, `MOTOR_ID=C`).
- **Lógica:**
  1. Cada instância do motor simula leituras de rotações por minuto (RPM), temperatura e pressão do motor.
  2. Adicionar suporte a escutar comandos no tópico `avionica.commands.motor.<id>` (ex: `CORRUPT`).
  3. Se receber o comando `CORRUPT`, a instância simula uma falha física e passa a transmitir dados absurdos (ex: temperatura de 9999°C) para testar o Voter TMR da Gabriela.
- **Produção:**
  - Publicar a telemetria do motor em seus respectivos tópicos: `avionica.telemetry.motor.a`, `avionica.telemetry.motor.b` ou `avionica.telemetry.motor.c`.

---

## Módulo 2: Injetor de Falhas Distribuídas

### Objetivo
Permitir que operadores e avaliadores simulem falhas físicas no sistema distribuído de forma amigável na apresentação acadêmica.

### Especificação Técnica
- **Tecnologia:** Python (CLI / Script de controle).
- **Lógica:**
  1. Fornecer uma interface simples (menu de console ou script automatizado).
  2. Possibilitar o envio de comandos específicos no barramento Kafka/MQTT para forçar falhas:
     - Injetar falha no Motor A, B ou C (envia payload para o motor correspondente entrar em estado degradado).
     - Forçar atraso na rede (provoca latência artificial nas leituras de telemetria).
     - Derrubar computadores (derruba o computador primário para forçar a eleição de líder do Bully).
- **Produção:**
  - Publicar comandos em `avionica.commands.motor.a`, `avionica.commands.motor.b`, `avionica.commands.motor.c` e `avionica.commands.system.faults`.
