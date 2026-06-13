# Regra geral da Torre de Comando

- O sistema `Torre de Comando` será o ponto de partida do ciclo de vida das aeronaves no simulador.
- Sua principal responsabilidade é permitir a criação, configuração e registro de aeronaves ativas no sistema.
- A Torre de Comando fornecerá uma API REST e/ou interface gráfica própria (ex: `localhost:8082`) para gerenciar essas aeronaves.
- Sem o registro de uma aeronave na Torre de Comando, não será possível realizar simulações de voo ou telemetria no SGCA.
