"""Deduplicação de produtos já enviados."""
from src.database import Database
from src.utils.logger import get_logger

logger = get_logger("mariabicobot", "deduplicator")


class Deduplicator:
    """Gerencia deduplicação de produtos."""

    def __init__(self, db: Database, dedup_days: int = 7):
        """Inicializa o deduplicador.

        Args:
            db: Instância do banco de dados
            dedup_days: Dias para considerar duplicata (default 7)
        """
        self.db = db
        self.dedup_days = dedup_days

    def is_duplicate(self, item_id: int, group_id: str) -> bool:
        """Verifica se produto já foi enviado recentemente.

        Args:
            item_id: ID do produto Shopee
            group_id: ID do grupo Telegram

        Returns:
            True se foi enviado nos últimos dedup_days
        """
        was_sent = self.db.was_sent_recently(item_id, group_id, self.dedup_days)
        if was_sent:
            logger.debug(f"Produto {item_id} já enviado nos últimos {self.dedup_days} dias")
        return was_sent

    def filter_duplicates(self, products: list[dict], group_id: str) -> list[dict]:
        """Remove produtos já enviados recentemente.

        Args:
            products: Lista de produtos
            group_id: ID do grupo Telegram

        Returns:
            Lista de produtos não duplicados
        """
        filtered = []
        duplicates = 0

        for product in products:
            item_id = product.get("itemId")
            if not item_id:
                continue

            if self.is_duplicate(item_id, group_id):
                duplicates += 1
                continue

            filtered.append(product)

        logger.info(
            f"Deduplicação: {duplicates} duplicatas removidas, {len(filtered)} únicos restantes"
        )
        return filtered

    def mark_sent(self, item_id: int, group_id: str, short_link: str, batch_id: str) -> None:
        """Marca produto como enviado.

        Args:
            item_id: ID do produto Shopee
            group_id: ID do grupo Telegram
            short_link: Short link usado
            batch_id: ID do batch de envio
        """
        self.db.mark_as_sent(item_id, group_id, short_link, batch_id)
