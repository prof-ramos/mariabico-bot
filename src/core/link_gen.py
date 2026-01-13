"""Geração de short links rastreáveis."""

from datetime import datetime

from src.database import Database
from src.shopee import ShopeeClient
from src.utils.logger import get_logger

logger = get_logger("mariabicobot", "link_gen")


import re


def _sanitize(text: str) -> str:
    """Remove caracteres especiais, mantendo apenas alfanuméricos."""
    # Remove acentos e caracteres especiais
    return re.sub(r"[^a-zA-Z0-9]", "", text)


def build_sub_ids(
    campaign_type: str,
    group_hash: str,
    timestamp: str | None = None,
    tag: str = "",
) -> list[str]:
    """Constrói lista de subIds padronizados.

    Formato: [tg, grupo{hash}, {campaign_type}, {timestamp}, {tag}]

    Args:
        campaign_type: Tipo de campanha ("curadoria" ou "manual")
        group_hash: Hash curto do group_id
        timestamp: Timestamp YYYYMMDDHHMM (gera automaticamente se None)
        tag: Tag opcional (keyword ou categoria)

    Returns:
        Lista com até 5 subIds
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M")

    # Sanitiza todos os campos para evitar erro "invalid sub id"
    sub_ids = [
        "tg",
        _sanitize(f"grupo{group_hash}"),
        _sanitize(campaign_type),
        _sanitize(timestamp),
    ]

    if tag:
        # Trunca tag e sanitiza
        clean_tag = _sanitize(tag)[:20]  # Limite conservador de 20 chars
        if clean_tag:
            sub_ids.append(clean_tag)

    return sub_ids[:5]  # Max 5 subIds


class LinkGenerator:
    """Gerencia geração de short links."""

    def __init__(self, shopee_client: ShopeeClient, db: Database, group_hash: str):
        """Inicializa o gerador de links.

        Args:
            shopee_client: Cliente da API Shopee
            db: Instância do banco de dados
            group_hash: Hash curto do group_id
        """
        self.shopee = shopee_client
        self.db = db
        self.group_hash = group_hash

    async def generate(
        self,
        origin_url: str,
        campaign_type: str = "curadoria",
        tag: str = "",
    ) -> str:
        """Gera ou recupera um short link rastreável.

        Args:
            origin_url: URL original do produto
            campaign_type: Tipo de campanha ("curadoria" ou "manual")
            tag: Tag opcional para rastreamento

        Returns:
            Short link (ex: https://shope.ee/abc123)

        Raises:
            ShopeeAPIError: Em caso de erro na API Shopee
        """
        # Verifica cache primeiro
        cached = self.db.get_cached_link(origin_url)
        if cached:
            logger.debug(f"Link em cache encontrado para {origin_url[:50]}...")
            return cached.short_link

        # Gera subIds
        sub_ids = build_sub_ids(campaign_type, self.group_hash, tag=tag)

        # Chama API
        logger.info(
            f"Gerando short link para {origin_url[:50]}... com sub_ids={sub_ids}"
        )
        short_link = await self.shopee.generate_short_link(origin_url, sub_ids)

        # Salva no cache
        self.db.get_or_create_link(origin_url, short_link, sub_ids)

        return short_link

    async def generate_batch(
        self,
        products: list[dict],
        campaign_type: str = "curadoria",
    ) -> list[dict]:
        """Gera short links para um lote de produtos.

        Args:
            products: Lista de produtos (será modificada in-place)
            campaign_type: Tipo de campanha

        Returns:
            Mesma lista com campo 'shortLink' adicionado
        """
        for product in products:
            origin_url = product.get("originUrl")
            if not origin_url:
                logger.warning(f"Produto {product.get('itemId')} sem originUrl")
                continue

            # Usa keyword como tag
            tag = product.get("keyword", "")

            try:
                short_link = await self.generate(origin_url, campaign_type, tag)
                product["shortLink"] = short_link
            except Exception as e:
                logger.error(
                    f"Erro ao gerar link para produto {product.get('itemId')}: {e}"
                )
                product["shortLink"] = origin_url  # Fallback

        return products
