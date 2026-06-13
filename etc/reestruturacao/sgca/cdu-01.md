# CDU-01: Visão Geral do Painel Inicial SGCA (Simulador Glass Cockpit da Aeronave)

## Definições/Regras

- `SGCA`: Nome da aplicação
- A aplicação `SGCA` rodara na porta 5173:5173

## Fluxo principal

1. O usuario acessa acessa o `painel` inicial pelo `/painel`.

2. O `painel` contera os seguintes componentes:

    - `Menu` superior, que atraves dele o usaurio podera fazer a navegação pelo sistema. Nele terar `Inicio`, `Simulação`.
    - Em baixo do `Menu` terar um card com um texto explicando sobre o sistema e um botão `Iniciar simulação`.

    2.1 - Se o usuario clicar em `Iniciar simulação` o sistema redirecionar o usuario para a tela de `simulação` atraves do `/simulacao`.

3. Se o usuario clicar em `Inicio` pelo menu, o sistema redirecionala para a tela de inicio pelo `/painel`. 

4. Se o usuario clicar em `Simulação` pelo menu, o sistema redireciona para a tela de simulação pelo `/simulacao`.