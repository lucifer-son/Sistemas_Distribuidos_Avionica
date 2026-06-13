# CDU-02: Monitor de Mensagens em Tempo Real

## Definições/Regras

- `Visualizador de Tópico`: Exibe o fluxo contínuo de mensagens de um tópico selecionado.
- URL da tela: `http://localhost:9000/topico/{nome_do_topico}`.

## Fluxo principal

1. O usuário acessa a tela de visualização de um tópico específico após selecioná-lo no [cdu-01](cdu-01.md) ou acessando diretamente a URL.

2. A tela exibirá um console/feed com as mensagens que estão transitando pelo tópico em tempo real. Cada linha de mensagem mostrará:
    - **Timestamp**: Data e hora exata em que a mensagem foi recebida no Kafka.
    - **Chave (Key)**: Chave da mensagem (se aplicável).
    - **Partição e Offset**: Identificadores internos da mensagem no Kafka.
    - **Payload (JSON)**: O conteúdo dos dados formatado de forma legível.

3. O console atualizará automaticamente conforme novas mensagens forem publicadas pelos sensores.

4. O usuário terá acesso aos seguintes botões de controle:
    - **Pausar/Retomar**: Permite congelar o fluxo visual de mensagens para análise detalhada do payload.
    - **Limpar Tela**: Limpa as mensagens exibidas no console atual.
    - **Voltar**: Redireciona o usuário para a lista geral de tópicos (`http://localhost:9000`).
