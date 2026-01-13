"""Models e funções de acesso ao banco de dados."""
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from .schema import (
    SQL_INSERT_LINK,
    SQL_INSERT_RUN_START,
    SQL_INSERT_SENT_MESSAGE,
    SQL_SELECT_DB_STATS,
    SQL_SELECT_LAST_RUN,
    SQL_SELECT_LINK_BY_ORIGIN,
    SQL_SELECT_RUNS_STATS,
    SQL_SELECT_SENT_RECENT,
    SQL_SELECT_SETTINGS_BY_KEY,
    SQL_UPSERT_PRODUCT_SEEN,
    SQL_UPSERT_SETTING,
    SQL_UPDATE_LINK_LAST_USED,
    SQL_UPDATE_RUN_END,
    SQL_VACUUM,
    get_connection,
)


@dataclass
class ProductSeen:
    """Produto já visto."""

    item_id: int
    first_seen_at: str
    last_seen_at: str
    last_price_min: Optional[float] = None
    last_discount_rate: Optional[int] = None
    last_commission: Optional[float] = None
    last_commission_rate: Optional[float] = None
    last_score: Optional[float] = None
    raw_json: Optional[str] = None


@dataclass
class Link:
    """Short link gerado."""

    id: int
    origin_url: str
    short_link: str
    sub_ids_json: str
    created_at: str
    last_used_at: Optional[str] = None


@dataclass
class SentMessage:
    """Mensagem enviada."""

    id: int
    item_id: int
    group_id: str
    short_link: str
    sent_at: str
    batch_id: Optional[str] = None


@dataclass
class Run:
    """Execução de curadoria."""

    id: int
    run_type: str
    started_at: str
    ended_at: Optional[str] = None
    items_fetched: int = 0
    items_approved: int = 0
    items_sent: int = 0
    error_summary: Optional[str] = None
    success: bool = True


class Database:
    """Interface para acessar o banco de dados."""

    def __init__(self, db_path: str):
        """Inicializa a conexão com o banco.

        Args:
            db_path: Caminho para o arquivo SQLite
        """
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> sqlite3.Connection:
        """Retorna a conexão (lazy initialization)."""
        if self._conn is None:
            self._conn = get_connection(self.db_path)
        return self._conn

    def close(self) -> None:
        """Fecha a conexão com o banco."""
        if self._conn:
            self._conn.close()
            self._conn = None

    # Settings
    def get_setting(self, key: str) -> Optional[str]:
        """Retorna uma configuração.

        Args:
            key: Chave da configuração

        Returns:
            Valor da configuração ou None
        """
        cursor = self.conn.execute(SQL_SELECT_SETTINGS_BY_KEY, (key,))
        row = cursor.fetchone()
        return row["value"] if row else None

    def set_setting(self, key: str, value: Any) -> None:
        """Define uma configuração.

        Args:
            key: Chave da configuração
            value: Valor (será convertido para string JSON)
        """
        json_value = json.dumps(value) if not isinstance(value, str) else value
        self.conn.execute(SQL_UPSERT_SETTING, (key, json_value))
        self.conn.commit()

    # Products Seen
    def upsert_product(self, product: dict) -> None:
        """Insere ou atualiza um produto visto.

        Args:
            product: Dicionário com dados do produto
        """
        self.conn.execute(
            SQL_UPSERT_PRODUCT_SEEN,
            (
                product["itemId"],
                product.get("first_seen_at", datetime.now().isoformat()),
                datetime.now().isoformat(),
                product.get("priceMin"),
                product.get("priceDiscountRate"),
                product.get("commission"),
                product.get("commissionRate"),
                product.get("score"),
                json.dumps(product),
            ),
        )
        self.conn.commit()

    def get_product(self, item_id: int) -> Optional[ProductSeen]:
        """Retorna um produto visto.

        Args:
            item_id: ID do produto

        Returns:
            ProductSeen ou None
        """
        cursor = self.conn.execute("SELECT * FROM products_seen WHERE item_id = ?", (item_id,))
        row = cursor.fetchone()
        if row:
            return ProductSeen(**row)
        return None

    # Links
    def get_cached_link(self, origin_url: str) -> Optional[Link]:
        """Retorna um link em cache (se válido).

        Args:
            origin_url: URL original

        Returns:
            Link em cache ou None
        """
        cursor = self.conn.execute(SQL_SELECT_LINK_BY_ORIGIN, (origin_url,))
        row = cursor.fetchone()
        if row:
            return Link(**row)
        return None

    def create_link(self, origin_url: str, short_link: str, sub_ids: list) -> Link:
        """Cria um novo short link.

        Args:
            origin_url: URL original
            short_link: Short link gerado
            sub_ids: Lista de subIds

        Returns:
            Link criado
        """
        cursor = self.conn.execute(
            SQL_INSERT_LINK,
            (origin_url, short_link, json.dumps(sub_ids)),
        )
        row = cursor.fetchone()
        self.conn.commit()
        return Link(**row)

    def update_link_used(self, link_id: int) -> None:
        """Atualiza o last_used_at de um link.

        Args:
            link_id: ID do link
        """
        self.conn.execute(SQL_UPDATE_LINK_LAST_USED, (link_id,))
        self.conn.commit()

    def get_or_create_link(self, origin_url: str, short_link: str, sub_ids: list) -> Link:
        """Retorna link em cache ou cria novo.

        Args:
            origin_url: URL original
            short_link: Short link gerado
            sub_ids: Lista de subIds

        Returns:
            Link existente ou novo
        """
        cached = self.get_cached_link(origin_url)
        if cached:
            self.update_link_used(cached.id)
            return cached
        return self.create_link(origin_url, short_link, sub_ids)

    # Sent Messages
    def was_sent_recently(self, item_id: int, group_id: str, days: int = 7) -> bool:
        """Verifica se produto foi enviado recentemente.

        Args:
            item_id: ID do produto
            group_id: ID do grupo
            days: Dias para verificar (default 7)

        Returns:
            True se foi enviado recentemente
        """
        sql = SQL_SELECT_SENT_RECENT.format(days=days)
        cursor = self.conn.execute(sql, (item_id, group_id))
        row = cursor.fetchone()
        return row["count"] > 0

    def mark_as_sent(self, item_id: int, group_id: str, short_link: str, batch_id: str) -> None:
        """Marca produto como enviado.

        Args:
            item_id: ID do produto
            group_id: ID do grupo
            short_link: Short link usado
            batch_id: ID do batch
        """
        self.conn.execute(SQL_INSERT_SENT_MESSAGE, (item_id, group_id, short_link, batch_id))
        self.conn.commit()

    # Runs
    def start_run(self, run_type: str) -> int:
        """Inicia uma execução.

        Args:
            run_type: Tipo de execução ("scheduled" ou "manual")

        Returns:
            ID da execução
        """
        cursor = self.conn.execute(SQL_INSERT_RUN_START, (run_type,))
        row = cursor.fetchone()
        self.conn.commit()
        return row["id"]

    def end_run(
        self,
        run_id: int,
        items_fetched: int,
        items_approved: int,
        items_sent: int,
        error_summary: Optional[str] = None,
        success: bool = True,
    ) -> None:
        """Finaliza uma execução.

        Args:
            run_id: ID da execução
            items_fetched: Itens buscados
            items_approved: Itens aprovados
            items_sent: Itens enviados
            error_summary: Resumo de erros
            success: Se a execução foi bem-sucedida
        """
        self.conn.execute(
            SQL_UPDATE_RUN_END,
            (
                items_fetched,
                items_approved,
                items_sent,
                error_summary,
                success,
                run_id,
            ),
        )
        self.conn.commit()

    def get_last_run(self) -> Optional[Run]:
        """Retorna a última execução.

        Returns:
            Run ou None
        """
        cursor = self.conn.execute(SQL_SELECT_LAST_RUN)
        row = cursor.fetchone()
        if row:
            return Run(**row)
        return None

    def get_stats(self) -> dict:
        """Retorna estatísticas gerais.

        Returns:
            Dicionário com estatísticas
        """
        cursor = self.conn.execute(SQL_SELECT_RUNS_STATS)
        runs_row = cursor.fetchone()

        cursor = self.conn.execute(SQL_SELECT_DB_STATS)
        db_row = cursor.fetchone()

        return {
            "total_runs": runs_row["total_runs"] or 0,
            "total_fetched": runs_row["total_fetched"] or 0,
            "total_approved": runs_row["total_approved"] or 0,
            "total_sent": runs_row["total_sent"] or 0,
            "unique_products": db_row["unique_products"] or 0,
            "total_links": db_row["total_links"] or 0,
            "total_sent_messages": db_row["total_sent"] or 0,
        }

    def vacuum(self) -> None:
        """Executa VACUUM para otimizar o banco."""
        self.conn.execute(SQL_VACUUM)
        self.conn.commit()
