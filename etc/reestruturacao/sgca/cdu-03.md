# CDU-03: Tela de seleção de rota

## Fluxo principal

1. Apos o usuario ter feito o passo referente ao [cdu-02](cdu-02.md), ele vera a tela de selecionar rota para aquela silução. Sua url sera chamada de `simulacao/rota`.

2. O usuario vera um formulario com os seguintes campos:

    - `Aeroporto de decolagem`
    - `Aeroporto de destino`
    - Um botão chamado `Simular`

3. Se o usuario clicar em `Simular` o sistema ira redirecionar o usuario para a tela de `simulacao/dashboard/{id_aeronave}_{id_decolagem}_{id_destino}`

4. Do lado do botão `Simular` terar um botão chamado `Voltar`. Se o usuario clicar nele, ele sera redirecionado para a tela de `Simulação`.