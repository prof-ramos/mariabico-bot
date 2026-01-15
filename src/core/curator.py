"""Lógica de curadoria de produtos."""

from src.core.deduplicator import Deduplicator
from src.core.link_gen import LinkGenerator
from src.core.scoring import (
    FilterThresholds,
    ScoreWeights,
    passes_filters,
    rank_products,
)
from src.database import Database
from src.shopee import ShopeeClient
from src.utils.logger import get_logger

logger = get_logger("mariabicobot", "curator")


class Curator:
    """Gerencia curadoria de produtos Shopee."""

    def __init__(
        self,
        shopee_client: ShopeeClient,
        db: Database,
        group_id: str,
        group_hash: str = "default",
        top_n: int = 10,
        max_pages: int = 5,
        page_limit: int = 50,
        dedup_days: int = 7,
        weights: ScoreWeights | None = None,
        thresholds: FilterThresholds | None = None,
    ):
        """Inicializa o curador."""
        self.shopee = shopee_client
        self.db = db
        self.group_id = group_id
        self.group_hash = group_hash
        self.top_n = top_n
        self.max_pages = max_pages
        self.page_limit = page_limit
        self.weights = weights or ScoreWeights()
        self.thresholds = thresholds or FilterThresholds()

        self.deduplicator = Deduplicator(db, dedup_days)
        self.link_gen = LinkGenerator(shopee_client, db, group_hash)

    def _normalize_offer(self, offer: dict, keyword: str = "") -> dict:
        """Normaliza campos da oferta para o padrão do bot."""
        # Campos da API productOfferV2 -> Padrão interno

        name = offer.get("productName", "")
        # priceMin pode vir como string ou número
        price_str = offer.get("priceMin", "0")
        try:
            price = float(price_str)
        except (ValueError, TypeError):
            price = 0.0

        # commissionRate vem como string ou número na productOfferV2
        rate_str = offer.get("commissionRate", "0")
        try:
            # Pode vir como "0.1" ou 0.1
            rate = float(rate_str)
        except (ValueError, TypeError):
            rate = 0.0

        # commission as vezes já vem calculado na API
        commission = offer.get("commission")
        if commission is None:
            commission = price * rate
        else:
            try:
                commission = float(commission)
            except (ValueError, TypeError):
                commission = price * rate

        # Tratar avaliação
        try:
            rating = float(offer.get("ratingStar", "0") or 0)
        except (ValueError, TypeError):
            rating = 0.0

        normalized = {
            "itemId": str(offer.get("itemId", "0")),
            "productName": name,
            "priceMin": price,
            "commissionRate": rate,
            "commission": round(commission, 2),
            "originUrl": offer.get("offerLink", ""),
            "imageUrl": offer.get("imageUrl", ""),
            "rating": rating,
            "keyword": keyword,
        }
        return normalized

    async def fetch_products(
        self,
        keywords: list[str],
        categories: list[int] | None = None,
    ) -> list[dict]:
        """Busca produtos na API Shopee."""
        all_products = []

        for keyword in keywords:
            logger.info(f"Buscando produtos para keyword: {keyword}")

            for page in range(1, self.max_pages + 1):
                try:
                    # Resolve categoria (API aceita uma por vez)
                    cat_id = categories[0] if categories else None

                    offers = await self.shopee.search_products(
                        keywords=[keyword],
                        limit=self.page_limit,
                        page=page,
                        category_id=cat_id,
                    )

                    if not offers:
                        logger.info(f"Página {page} vazia para keyword '{keyword}'")
                        break

                    # Normaliza e adiciona keyword
                    for o in offers:
                        norm = self._normalize_offer(o, keyword)
                        all_products.append(norm)

                    logger.info(f"Buscou {len(offers)} produtos (página {page})")

                except Exception as e:
                    logger.error(f"Erro ao buscar página {page} para '{keyword}': {e}")

        logger.info(f"Total de produtos buscados: {len(all_products)}")
        return all_products

    def filter_products(self, products: list[dict]) -> tuple[list[dict], dict]:
        """Filtra produtos por thresholds."""
        filtered = []
        stats = {
            "total": len(products),
            "passed_filters": 0,
            "failed_commission": 0,
            "failed_discount": 0,
            "failed_price": 0,
        }

        for product in products:
            if passes_filters(product, self.thresholds):
                filtered.append(product)
                stats["passed_filters"] += 1
            else:
                comm = product.get("commission", 0)
                rate = product.get("commissionRate", 0)
                discount = product.get("priceDiscountRate", 0)
                price = product.get("priceMin", 0)

                if (
                    rate < self.thresholds.commission_rate_min
                    or comm < self.thresholds.commission_min_brl
                ):
                    stats["failed_commission"] += 1
                elif discount < self.thresholds.discount_min_pct:
                    stats["failed_discount"] += 1
                elif self.thresholds.price_max_brl and price > self.thresholds.price_max_brl:
                    stats["failed_price"] += 1

        logger.info(
            f"Filtragem: {stats['passed_filters']}/{stats['total']} aprovados, "
            f"{stats['failed_commission']} falharam em comissão, "
            f"{stats['failed_discount']} em desconto"
        )

        return filtered, stats

    def deduplicate_products(self, products: list[dict]) -> list[dict]:
        """Remove produtos já enviados recentemente."""
        return self.deduplicator.filter_duplicates(products, self.group_id)

    async def generate_links(self, products: list[dict]) -> list[dict]:
        """Gera short links para produtos."""
        return await self.link_gen.generate_batch(products, campaign_type="curadoria")

    async def curate(
        self,
        keywords: list[str],
        categories: list[int] | None = None,
    ) -> dict:
        """Executa curadoria completa."""
        # 1. Busca
        logger.info(f"Iniciando curadoria: keywords={keywords}")
        fetched = await self.fetch_products(keywords, categories)

        # 2. Filtra
        filtered, filter_stats = self.filter_products(fetched)

        # 3. Rankeia
        ranked = rank_products(filtered, self.weights)

        # 4. Deduplica
        after_dedup = self.deduplicate_products(ranked)

        # 5. Top N
        final_products = after_dedup[: self.top_n]

        # 6. Gera links
        await self.generate_links(final_products)

        # 7. Salva produtos vistos
        for product in fetched:
            self.db.upsert_product(product)

        result = {
            "fetched": len(fetched),
            "approved": len(filtered),
            "after_dedup": len(after_dedup),
            "final": len(final_products),
            "products": final_products,
            "filter_stats": filter_stats,
        }

        logger.info(
            f"Curadoria concluída: {result['fetched']} buscados, "
            f"{result['approved']} aprovados, {result['final']} finais"
        )

        return result