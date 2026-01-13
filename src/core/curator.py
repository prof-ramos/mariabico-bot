"""Lógica de curadoria de produtos."""
from typing import Optional

from src.core.deduplicator import Deduplicator
from src.core.link_gen import LinkGenerator
from src.core.scoring import FilterThresholds, ScoreWeights, passes_filters, rank_products
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
        weights: Optional[ScoreWeights] = None,
        thresholds: Optional[FilterThresholds] = None,
    ):
        """Inicializa o curador.

        Args:
            shopee_client: Cliente da API Shopee
            db: Instância do banco de dados
            group_id: ID do grupo Telegram
            group_hash: Hash curto do group_id
            top_n: Quantidade de produtos a retornar
            max_pages: Máximo de páginas a buscar
            page_limit: Itens por página
            dedup_days: Dias para deduplicação
            weights: Pesos para cálculo de score
            thresholds: Thresholds para filtragem
        """
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

    async def fetch_products(
        self,
        keywords: list[str],
        categories: Optional[list[int]] = None,
    ) -> list[dict]:
        """Busca produtos na API Shopee.

        Args:
            keywords: Lista de keywords para buscar
            categories: Lista de categorias (opcional)

        Returns:
            Lista de produtos buscados
        """
        all_products = []

        for keyword in keywords:
            logger.info(f"Buscando produtos para keyword: {keyword}")

            for page in range(1, self.max_pages + 1):
                try:
                    products = await self.shopee.search_products(
                        keywords=[keyword],
                        limit=self.page_limit,
                        page=page,
                        categories=categories,
                    )

                    if not products:
                        logger.info(f"Página {page} vazia para keyword '{keyword}'")
                        break

                    # Adiciona keyword aos produtos
                    for p in products:
                        p["keyword"] = keyword

                    all_products.extend(products)
                    logger.info(f"Buscou {len(products)} produtos (página {page})")

                except Exception as e:
                    logger.error(f"Erro ao buscar página {page} para '{keyword}': {e}")

        logger.info(f"Total de produtos buscados: {len(all_products)}")
        return all_products

    def filter_products(self, products: list[dict]) -> tuple[list[dict], dict]:
        """Filtra produtos por thresholds.

        Args:
            products: Lista de produtos

        Returns:
            Tupla (produtos filtrados, estatísticas)
        """
        filtered = []
        stats = {
            "total": len(products),
            "passed_filters": 0,
            "failed_commission": 0,
            "failed_discount": 0,
            "failed_price": 0,
            "failed_sales": 0,
            "failed_rating": 0,
        }

        for product in products:
            if passes_filters(product, self.thresholds):
                filtered.append(product)
                stats["passed_filters"] += 1
            else:
                # Conta qual filtro falhou
                commission_rate = product.get("commissionRate", 0) or 0
                commission_brl = product.get("commission", 0) or 0
                discount = product.get("priceDiscountRate", 0) or 0
                price = product.get("priceMin", 0) or 0
                sales = product.get("sales", 0) or 0
                rating = product.get("rating", 0) or 0

                if commission_rate < self.thresholds.commission_rate_min or commission_brl < self.thresholds.commission_min_brl:
                    stats["failed_commission"] += 1
                elif discount < self.thresholds.discount_min_pct:
                    stats["failed_discount"] += 1
                elif self.thresholds.price_max_brl and price > self.thresholds.price_max_brl:
                    stats["failed_price"] += 1
                elif self.thresholds.sales_min > 0 and sales < self.thresholds.sales_min:
                    stats["failed_sales"] += 1
                elif self.thresholds.rating_min > 0 and rating < self.thresholds.rating_min:
                    stats["failed_rating"] += 1

        logger.info(
            f"Filtragem: {stats['passed_filters']}/{stats['total']} aprovados, "
            f"{stats['failed_commission']} falharam em comissão, "
            f"{stats['failed_discount']} em desconto"
        )

        return filtered, stats

    def deduplicate_products(self, products: list[dict]) -> list[dict]:
        """Remove produtos já enviados recentemente.

        Args:
            products: Lista de produtos

        Returns:
            Lista de produtos não duplicados
        """
        return self.deduplicator.filter_duplicates(products, self.group_id)

    async def generate_links(self, products: list[dict]) -> list[dict]:
        """Gera short links para produtos.

        Args:
            products: Lista de produtos

        Returns:
            Lista com campo 'shortLink' adicionado
        """
        return await self.link_gen.generate_batch(products, campaign_type="curadoria")

    async def curate(
        self,
        keywords: list[str],
        categories: Optional[list[int]] = None,
    ) -> dict:
        """Executa curadoria completa.

        Args:
            keywords: Lista de keywords para buscar
            categories: Lista de categorias (opcional)

        Returns:
            Dicionário com resultados da curadoria:
            - fetched: Total buscado
            - approved: Total aprovado nos filtros
            - after_dedup: Total após deduplicação
            - final: Top N final
            - products: Lista de produtos selecionados
            - stats: Estatísticas detalhadas
        """
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
