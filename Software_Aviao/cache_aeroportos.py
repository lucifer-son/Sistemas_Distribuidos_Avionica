import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


CAMINHO_PADRAO_CACHE = (
        Path(__file__).resolve().parent
        / "data"
        / "fms_cache.db"
)


AEROPORTOS_SEMENTE: tuple[dict[str, Any], ...] = (
    {
        "icao": "SBRF",
        "nome": "Aeroporto Internacional do Recife",
        "cidade": "Recife",
        "latitude": -8.12649,
        "longitude": -34.9236,
    },
    {
        "icao": "SBSV",
        "nome": "Aeroporto Internacional de Salvador",
        "cidade": "Salvador",
        "latitude": -12.9086,
        "longitude": -38.3225,
    },
    {
        "icao": "SBFZ",
        "nome": "Aeroporto Internacional de Fortaleza",
        "cidade": "Fortaleza",
        "latitude": -3.77628,
        "longitude": -38.5326,
    },
    {
        "icao": "SBBR",
        "nome": "Aeroporto Internacional de Brasília",
        "cidade": "Brasília",
        "latitude": -15.8697,
        "longitude": -47.9208,
    },
    {
        "icao": "SBCF",
        "nome": "Aeroporto Internacional de Confins",
        "cidade": "Belo Horizonte",
        "latitude": -19.6337,
        "longitude": -43.9689,
    },
    {
        "icao": "SBGL",
        "nome": "Aeroporto Internacional do Galeão",
        "cidade": "Rio de Janeiro",
        "latitude": -22.809,
        "longitude": -43.2506,
    },
    {
        "icao": "SBRJ",
        "nome": "Aeroporto Santos Dumont",
        "cidade": "Rio de Janeiro",
        "latitude": -22.9105,
        "longitude": -43.1631,
    },
    {
        "icao": "SBGR",
        "nome": "Aeroporto Internacional de Guarulhos",
        "cidade": "São Paulo",
        "latitude": -23.4356,
        "longitude": -46.4731,
    },
    {
        "icao": "SBSP",
        "nome": "Aeroporto de Congonhas",
        "cidade": "São Paulo",
        "latitude": -23.6261,
        "longitude": -46.6564,
    },
    {
        "icao": "SBKP",
        "nome": "Aeroporto Internacional de Viracopos",
        "cidade": "Campinas",
        "latitude": -23.0074,
        "longitude": -47.1345,
    },
    {
        "icao": "SBCT",
        "nome": "Aeroporto Internacional de Curitiba",
        "cidade": "Curitiba",
        "latitude": -25.5285,
        "longitude": -49.1758,
    },
    {
        "icao": "SBPA",
        "nome": "Aeroporto Internacional de Porto Alegre",
        "cidade": "Porto Alegre",
        "latitude": -29.9944,
        "longitude": -51.1714,
    },
)


class CacheAeroportosSQLite:
    def __init__(self, caminho_banco: str | Path | None = None):
        caminho_configurado = caminho_banco or os.getenv("FMS_CACHE_DB")

        self.caminho_banco = Path(
            caminho_configurado or CAMINHO_PADRAO_CACHE
        ).expanduser().resolve()

        self.caminho_banco.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.criar_estrutura()
        self.inserir_sementes_iniciais()

    @staticmethod
    def agora_utc() -> str:
        return datetime.now(timezone.utc).isoformat()

    @contextmanager
    def conectar(self) -> Iterator[sqlite3.Connection]:
        conexao = sqlite3.connect(
            self.caminho_banco,
            timeout=5.0
        )
        conexao.row_factory = sqlite3.Row

        try:
            yield conexao
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise
        finally:
            conexao.close()

    def criar_estrutura(self) -> None:
        with self.conectar() as conexao:
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS aeroportos_cache (
                                                                icao TEXT PRIMARY KEY,
                                                                nome TEXT,
                                                                cidade TEXT,
                                                                latitude REAL NOT NULL,
                                                                longitude REAL NOT NULL,
                                                                fonte TEXT NOT NULL,
                                                                atualizado_em TEXT NOT NULL,
                                                                ultimo_acesso_em TEXT
                )
                """
            )

    def inserir_sementes_iniciais(self) -> None:
        timestamp = self.agora_utc()

        with self.conectar() as conexao:
            conexao.executemany(
                """
                INSERT OR IGNORE INTO aeroportos_cache (
                    icao,
                    nome,
                    cidade,
                    latitude,
                    longitude,
                    fonte,
                    atualizado_em,
                    ultimo_acesso_em
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        aeroporto["icao"],
                        aeroporto["nome"],
                        aeroporto["cidade"],
                        aeroporto["latitude"],
                        aeroporto["longitude"],
                        "SEMENTE_LOCAL",
                        timestamp,
                        None,
                    )
                    for aeroporto in AEROPORTOS_SEMENTE
                ],
            )

    def salvar_ou_atualizar(
            self,
            *,
            icao: str,
            latitude: float,
            longitude: float,
            nome: str | None = None,
            cidade: str | None = None,
            fonte: str = "API_EXTERNA",
    ) -> None:
        codigo = icao.strip().upper()
        timestamp = self.agora_utc()

        with self.conectar() as conexao:
            conexao.execute(
                """
                INSERT INTO aeroportos_cache (
                    icao,
                    nome,
                    cidade,
                    latitude,
                    longitude,
                    fonte,
                    atualizado_em,
                    ultimo_acesso_em
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(icao) DO UPDATE SET
                    nome = excluded.nome,
                                             cidade = excluded.cidade,
                                             latitude = excluded.latitude,
                                             longitude = excluded.longitude,
                                             fonte = excluded.fonte,
                                             atualizado_em = excluded.atualizado_em
                """,
                (
                    codigo,
                    nome,
                    cidade,
                    float(latitude),
                    float(longitude),
                    fonte,
                    timestamp,
                    timestamp,
                ),
            )

    def buscar(self, icao: str) -> dict[str, Any] | None:
        codigo = icao.strip().upper()
        timestamp = self.agora_utc()

        with self.conectar() as conexao:
            registro = conexao.execute(
                """
                SELECT
                    icao,
                    nome,
                    cidade,
                    latitude,
                    longitude,
                    fonte,
                    atualizado_em,
                    ultimo_acesso_em
                FROM aeroportos_cache
                WHERE icao = ?
                """,
                (codigo,),
            ).fetchone()

            if registro is None:
                return None

            conexao.execute(
                """
                UPDATE aeroportos_cache
                SET ultimo_acesso_em = ?
                WHERE icao = ?
                """,
                (timestamp, codigo),
            )

        return dict(registro)

    def quantidade(self) -> int:
        with self.conectar() as conexao:
            registro = conexao.execute(
                "SELECT COUNT(*) AS total FROM aeroportos_cache"
            ).fetchone()

        return int(registro["total"])