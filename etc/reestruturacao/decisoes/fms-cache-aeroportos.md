# Decisão técnica: cache local de aeroportos do FMS

## Contexto

O FMS precisa obter as coordenadas do aeroporto de origem e do aeroporto de destino para calcular a distância e o ETA da rota.

A fonte principal continua sendo a API externa de aeroportos. Entretanto, o FMS deve continuar operando quando houver:

- indisponibilidade da API;
- ausência temporária de internet;
- timeout;
- limite de requisições;
- reinicialização de outros serviços do sistema.

As rotas calculadas continuam sendo publicadas como eventos e persistidas pelo backend no banco principal. O cache descrito neste documento guarda somente dados de referência dos aeroportos.

## Comparação das alternativas

| Alternativa | Vantagens | Limitações |
|---|---|---|
| JSON estático | Simples, legível e funciona sem servidor | Atualização manual, sem upsert, sem controle de data e hora e com baixa flexibilidade para consultas |
| H2 em memória | Estrutura relacional e consultas SQL | O FMS é Python, o H2 é orientado ao ecossistema Java/JDBC e os dados em memória são perdidos ao encerrar o processo |
| SQLite persistente | Integrado à biblioteca padrão do Python, não exige servidor separado, suporta SQL, chave primária, timestamps e upsert | É um cache local e não substitui o PostgreSQL do backend |

## Decisão

Foi escolhido o SQLite persistente como cache local do FMS.

O código ICAO é a chave primária da tabela. Quando a API retorna os dados de um aeroporto, o FMS executa um upsert:

- se o ICAO ainda não existe, o registro é inserido;
- se o ICAO já existe, coordenadas, nome, cidade, fonte e data de atualização são substituídos;
- a data do último acesso também é registrada.

A aplicação cria automaticamente o banco e a tabela na primeira execução.

## Estrutura da tabela

```sql
CREATE TABLE aeroportos_cache (
    icao TEXT PRIMARY KEY,
    nome TEXT,
    cidade TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    fonte TEXT NOT NULL,
    atualizado_em TEXT NOT NULL,
    ultimo_acesso_em TEXT
);
```

## Fluxo normal

```text
Solicitação de rota
        ↓
FMS consulta a API externa
        ↓
API retorna coordenadas
        ↓
FMS insere ou atualiza o cache SQLite
        ↓
FMS calcula distância e ETA
        ↓
Evento da rota é publicado
        ↓
Backend persiste a rota no banco principal
```

## Fluxo de fallback

```text
Solicitação de rota
        ↓
API indisponível ou sem chave
        ↓
FMS consulta o cache SQLite pelo ICAO
        ↓
FMS calcula distância e ETA
        ↓
Status OFFLINE_FALLBACK
        ↓
Evento da rota é publicado normalmente
```

## Separação de responsabilidades

O cache SQLite não armazena o histórico das rotas e não substitui o PostgreSQL.

- SQLite: coordenadas e dados de referência necessários para o FMS continuar operando.
- Kafka/MQTT: transporte dos eventos distribuídos.
- Backend/PostgreSQL: persistência oficial das rotas calculadas.

O cache não deve ser apagado depois que uma rota é persistida, porque as coordenadas dos aeroportos são reutilizáveis por outras solicitações. A atualização ocorre por ICAO e timestamp, evitando duplicidade.

## Inicialização sem API

Para evitar que uma primeira execução offline deixe o FMS sem nenhuma referência, o cache recebe uma pequena semente de aeroportos usados na demonstração. Esses registros são inseridos com `INSERT OR IGNORE`.

Quando a API retorna dados reais, o upsert substitui automaticamente a semente daquele ICAO e registra a nova data de atualização.

## Persistência no Docker

O arquivo SQLite é criado em:

```text
/app/data/fms_cache.db
```

O serviço `fms-api` deve utilizar um volume nomeado para manter o cache quando o contêiner for recriado.

## Resultado esperado

A solução mantém a API como fonte principal, elimina a manutenção manual do JSON e adiciona:

- atualização automática;
- prevenção de duplicidades pela chave ICAO;
- data e hora de atualização;
- último acesso;
- persistência local;
- fallback após falhas da API;
- independência do banco principal para leitura de coordenadas.
