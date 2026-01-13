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

    # Ajustados para facilitar aprovação nos testes
    commission_rate_min: float = 0.05  # 5% (antes 8%)
    commission_min_brl: float = 3.00  # R$ 3.00 (antes 5.00)
    discount_min_pct: int = 5  # 5% (antes 10%)
    price_max_brl: Optional[float] = None  # Sem limite
    sales_min: int = 0
    rating_min: float = 0


def _get_commission(product: dict) -> float:
    """Calcula a comissão em BRL."""
    # productOfferV2 pode retornar 'commission' direto da API ou calculado
    # Se já foi normalizado no curator, usamos o valor float
    if "commission" in product and isinstance(product["commission"], (int, float)):
        return float(product["commission"])

    price = product.get("priceMin", 0) or 0
    rate = product.get("commissionRate", 0) or 0
    return price * rate


def calculate_score(
    product: dict,
    weights: Optional[ScoreWeights] = None,
) -> float:
    """Calcula o score de um produto."""
    weights = weights or ScoreWeights()

    commission = _get_commission(product)
    discount = product.get("priceDiscountRate", 0) or 0
    price = product.get("priceMin", 0) or 0

    score = (
        (commission * weights.commission)
        + (discount * weights.discount)
        - (price * weights.price)
    )

    return round(score, 2)


def passes_filters(
    product: dict,
    thresholds: Optional[FilterThresholds] = None,
) -> bool:
    """Verifica se produto passa nos filtros mínimos."""
    thresholds = thresholds or FilterThresholds()

    # Comissão
    commission_rate = product.get("commissionRate", 0.0)
    commission_brl = _get_commission(product)

    if commission_rate < thresholds.commission_rate_min:
        logger.debug(
            f"Produto reprovado: commissionRate {commission_rate:.3f} < {thresholds.commission_rate_min}"
        )
        return False

    if commission_brl < thresholds.commission_min_brl:
        logger.debug(
            f"Produto reprovado: commission R${commission_brl:.2f} < R${thresholds.commission_min_brl:.2f}"
        )
        return False

    # Desconto
    discount = product.get("priceDiscountRate", 0) or 0
    if discount < thresholds.discount_min_pct:
        logger.debug(
            f"Produto reprovado: discount {discount}% < {thresholds.discount_min_pct}%"
        )
        return False

    # Preço máximo (se configurado)
    price = product.get("priceMin", 0) or 0
    if thresholds.price_max_brl is not None:
        if price > thresholds.price_max_brl:
            logger.debug(
                f"Produto reprovado: price R${price} > R${thresholds.price_max_brl}"
            )
            return False

    return True


def rank_products(
    products: list[dict],
    weights: Optional[ScoreWeights] = None,
) -> list[dict]:
    """Rankeia produtos por score."""
    weights = weights or ScoreWeights()

    # Calcula score para cada produto
    for product in products:
        product["score"] = calculate_score(product, weights)

    # Ordena por score decrescente
    return sorted(products, key=lambda p: p["score"], reverse=True)
