# CDU-05: Monitorização de Consenso dos Motores (Algoritmo TMR)

## 1. Descrição
Permite ao utilizador acompanhar, em tempo real, o funcionamento do algoritmo de Tolerância a Falhas (Triple Modular Redundancy - TMR). O ecrã deve demonstrar como o sistema lê dados de três sensores redundantes de um mesmo motor e aplica o Consenso Bizantino para entregar um dado limpo e fiável, mesmo em caso de falhas periféricas.

## 2. Atores
- **Utilizador:** Engenheiro de voo ou piloto que visualiza o painel de redundância.
- **Módulo de Consenso (`consenso_motor.py`):** Microsserviço Python que assina os tópicos dos 3 sensores, calcula a maioria e publica o resultado final.

## 3. Pré-condições
- Os três nós sensores do motor (Canal A, Canal B e Canal C) devem estar a publicar dados no Kafka.
- O Frontend e o Backend devem estar a comunicar normalmente.

## 4. Fluxo Principal
1. O utilizador acede ao separador/menu **"Motores / Redundância TMR"** no Frontend.
2. O sistema exibe um painel contendo três medidores individuais (Sensor A, Sensor B, Sensor C) e um medidor principal destacado (Resultado Consolidado).
3. O Frontend consome do Backend os dados das três leituras brutas e a leitura final validada.
4. O utilizador observa que os três sensores publicam valores idênticos ou com variações mínimas aceitáveis (ex: 800°C, 801°C, 800°C).
5. O painel indica o estado do motor como **"Saudável - Consenso Estabelecido"**.

## 5. Fluxos Alternativos
- **5a. Falha num dos Sensores (Divergência):**
  1. O utilizador (ou o simulador de injeção de falhas) faz com que o Sensor B envie dados ruidosos ou congele (ex: 0°C ou 9999°C).
  2. A interface atualiza o medidor do Sensor B, que fica vermelho (estado "Anómalo").
  3. O algoritmo TMR no barramento descarta o dado do Sensor B e utiliza a média/consenso dos Sensores A e C.
  4. O painel principal (Resultado Consolidado) continua a exibir o valor correto (ex: 800°C), mantendo a integridade da aeronave.
  5. Um aviso de manutenção nível **WARNING** é gerado ("Falha de Sensor Isolada - Votação Maioritária Ativa").

## 6. Pós-condições
- A resiliência do sistema distribuído é garantida e exibida visualmente, provando que falhas simples em nós periféricos não deitam abaixo a leitura central.
