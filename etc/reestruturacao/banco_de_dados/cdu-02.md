# CDU-02: Filtros e Consultas Básicas

## Definições/Regras

- A URL da tela será `/tabela/{nome_da_tabela}`.

## Fluxo principal

1. O usuário acessa a tela de visualização de dados de uma tabela após selecioná-la no [cdu-01](cdu-01.md).

2. O sistema exibirá uma tabela em formato de grade (grid) contendo as colunas reais correspondentes no PostgreSQL.

3. Acima da grade de dados, haverá filtros rápidos de pesquisa:
    - Campo de busca textual (para pesquisar no conteúdo/payload).
    - Filtro de data/hora inicial e final.
    - Seletor de limite de resultados (ex: mostrar os últimos 50, 100 ou 500 registros).

4. Ao alterar os filtros ou clicar no botão **"Filtrar"**, a aplicação realiza uma query correspondente no PostgreSQL e atualiza a grade com os novos resultados.

5. A tela contará com um botão **"Limpar Tabela"** (que executa um comando `TRUNCATE` ou similar para limpar dados de teste do banco de dados) e um botão **"Voltar"** para retornar ao menu principal das tabelas.
