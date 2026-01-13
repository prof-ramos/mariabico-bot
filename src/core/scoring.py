"""Algoritmo de score para rankeamento de produtos."""
from dataclasses import dataclass
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger("mariabicobot", "scoring")


@dataclass
class ScoreWeights:
    """Pesos para cálculo do score."""

    commission: float = 1.0
    discount: float = 0.5
    price: float = 0.02


@dataclass
class FilterThresholds:
    """Thresholds mínimos para filtragem."""

    commission_rate_min: float = 0.08  # 8%
    commission_min_brl: float = 8.00
    discount_min_pct: int = 15  # 15%
    price_max_brl: Optional[float] = None  # Sem limite por padrão
    sales_min: int = 50
    rating_min: float = 4.7


def calculate_score(
    product: dict,
    weights: Optional[ScoreWeights] = None,
) -> float:
    """Calcula o score de um produto.

    Score = (commission * w1) + (discount * w2) - (price * w3)

    Args:
        product: Dicionário com dados do produto
        weights: Pesos para cálculo (usa defaults se não fornecido)

    Returns:
        Score calculado
    """
    weights = weights or ScoreWeights()

    commission = product.get("commission", 0) or 0
    discount = product.get("priceDiscountRate", 0) or 0
    price = product.get("priceMin", 0) or 0

    score = (commission * weights.commission) + (discount * weights.discount) - (
        price * weights.price
    )

    return round(score, 2)


def passes_filters(
    product: dict,
    thresholds: Optional[FilterThresholds] = None,
) -> bool:
    """Verifica se produto passa nos filtros mínimos.

    Args:
        product: Dicionário com dados do produto
        thresholds: Thresholds para filtragem (usa defaults se não fornecido)

    Returns:
        True se passa nos filtros
    """
    thresholds = thresholds or FilterThresholds()

    # Comissão
    commission_rate = product.get("commissionRate", 0) or 0
    commission_brl = product.get("commission", 0) or 0

    if commission_rate < thresholds.commission_rate_min:
        logger.debug(
            f"Produto {product.get('itemId')} reprovado: commissionRate {commission_rate} < {thresholds.commission_rate_min}"
        )
        return False

    if commission_brl < thresholds.commission_min_brl:
        logger.debug(
            f"Produto {product.get('itemId')} reprovado: commission R${commission_brl} < R${thresholds.commission_min_brl}"
        )
        return False

    # Desconto
    discount = product.get("priceDiscountRate", 0) or 0
    if discount < thresholds.discount_min_pct:
        logger.debug(
            f"Produto {product.get('itemId')} reprovado: discount {discount}% < {thresholds.discount_min_pct}%"
        )
        return False

    # Preço máximo (se configurado)
    if thresholds.price_max_brl is not None:
        price = product.get("priceMin", 0) or 0
        if price > thresholds.price_max_brl:
            logger.debug(
                f"Produto {product.get('itemId')} reprovado: price R${price} > R${thresholds.price_max_brl}"
            )
            return False

    # Vendas (se disponível)
    if thresholds.sales_min > 0:
        sales = product.get("sales", 0) or 0
        if sales < thresholds.sales_min:
            logger.debug(
                f"Produto {product.get('itemId')} reprovado: sales {sales} < {thresholds.sales_min}"
            )
            return False

    # Rating (se disponível)
    if thresholds.rating_min > 0:
        rating = product.get("rating", 0) or 0
        if rating < thresholds.rating_min:
            logger.debug(
                f"Produto {product.get('itemId')} reprovado: rating {rating} < {thresholds.rating_min}"
            )
            return False

    return True


def rank_products(
    products: list[dict],
    weights: Optional[ScoreWeights] = None,
) -> list[dict]:
    """Rankeia produtos por score.

    Args:
        products: Lista de produtos
        weights: Pesos para cálculo do score

    Returns:
        Lista de produtos ordenados por score (decrescente)
        com campo 'score' adicionado
    """
    weights = weights or ScoreWeights()

    # Calcula score para cada produto
    for product in products:
        product["score"] = calculate_score(product, weights)

    # Ordena por score decrescente
    return sorted(products, key=lambda p: p["score"], reverse=True)
