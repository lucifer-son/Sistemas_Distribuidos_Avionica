# Regra geral do Painel de Monitoramento do Kafka

- O sistema fornecerá uma interface gráfica para que os usuários e desenvolvedores visualizem o tráfego de mensagens no barramento de eventos.
- A aplicação rodará em uma porta dedicada (ex: `localhost:9000`), permitindo verificar a integridade da comunicação assíncrona.
- Este painel ajudará na depuração dos sensores (produtores) e do backend (consumidor), exibindo o tráfego em tempo real.
- Não haverá controle de acesso inicial (sem login/bloqueios), visando a facilidade de uso em apresentações acadêmicas.
