"""Testes unitários para o módulo de scoring.

Marcadores:
- unit: Testes unitários rápidos e isolados
- smoke: Testes críticos que devem sempre passar
"""

import pytest

from src.core.scoring import (
    FilterThresholds,
    ScoreWeights,
    calculate_score,
    passes_filters,
    rank_products,
    _get_commission,
)


class TestScoreWeights:
    """Testes para dataclass ScoreWeights."""

    @pytest.mark.unit
    def test_default_weights(self):
        """Verifica valores padrão dos pesos."""
        weights = ScoreWeights()
        assert weights.commission == 1.0
        assert weights.discount == 0.5
        assert weights.price == 0.02

    @pytest.mark.unit
    def test_custom_weights(self):
        """Cria pesos personalizados."""
        weights = ScoreWeights(commission=2.0, discount=1.0, price=0.05)
        assert weights.commission == 2.0
        assert weights.discount == 1.0
        assert weights.price == 0.05


class TestFilterThresholds:
    """Testes para dataclass FilterThresholds."""

    @pytest.mark.unit
    def test_default_thresholds(self):
        """Verifica valores padrão dos filtros."""
        thresholds = FilterThresholds()
        assert thresholds.commission_rate_min == 0.05
        assert thresholds.commission_min_brl == 3.00
        assert thresholds.discount_min_pct == 5
        assert thresholds.price_max_brl is None
        assert thresholds.sales_min == 0
        assert thresholds.rating_min == 0

    @pytest.mark.unit
    def test_custom_thresholds(self):
        """Cria filtros personalizados."""
        thresholds = FilterThresholds(
            commission_rate_min=0.08,
            commission_min_brl=8.00,
            discount_min_pct=15,
            price_max_brl=250,
            sales_min=50,
            rating_min=4.7,
        )
        assert thresholds.commission_rate_min == 0.08
        assert thresholds.commission_min_brl == 8.00
        assert thresholds.discount_min_pct == 15
        assert thresholds.price_max_brl == 250
        assert thresholds.sales_min == 50
        assert thresholds.rating_min == 4.7


class TestGetCommission:
    """Testes para função auxiliar _get_commission."""

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_commission_from_field(self):
        """Recupera comissão do campo 'commission'."""
        product = {"priceMin": 100, "commissionRate": 0.1, "commission": 10.0}
        assert _get_commission(product) == 10.0

    @pytest.mark.unit
    def test_commission_calculated(self):
        """Calcula comissão quando campo não existe."""
        product = {"priceMin": 100, "commissionRate": 0.1}
        assert _get_commission(product) == 10.0

    @pytest.mark.unit
    def test_commission_zero_values(self):
        """Retorna zero quando campos estão ausentes ou zerados."""
        assert _get_commission({}) == 0
        assert _get_commission({"priceMin": 0, "commissionRate": 0}) == 0

    @pytest.mark.unit
    def test_commission_string_rate(self):
        """Lida com commissionRate como string."""
        # A função _get_commission lida com string, mas se houver "commission"
        # como campo separado, ele retorna isso
        product = {"priceMin": 100, "commissionRate": "0.1", "commission": 10.0}
        assert _get_commission(product) == 10.0

        # Se não tiver commission, calcula
        product2 = {"priceMin": 100, "commissionRate": 0.1}
        assert _get_commission(product2) == 10.0


class TestCalculateScore:
    """Testes para função calculate_score."""

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_calculate_score_basic(self):
        """Testa cálculo básico de score."""
        product = {
            "commission": 10.0,
            "priceDiscountRate": 20,
            "priceMin": 100,
        }
        score = calculate_score(product)
        # score = 10*1.0 + 20*0.5 - 100*0.02 = 10 + 10 - 2 = 18
        assert score == 18.0

    @pytest.mark.unit
    def test_calculate_score_custom_weights(self):
        """Testa cálculo com pesos personalizados."""
        weights = ScoreWeights(commission=2.0, discount=0.3, price=0.01)
        product = {
            "commission": 10.0,
            "priceDiscountRate": 20,
            "priceMin": 100,
        }
        score = calculate_score(product, weights)
        # score = 10*2.0 + 20*0.3 - 100*0.01 = 20 + 6 - 1 = 25
        assert score == 25.0

    @pytest.mark.unit
    def test_calculate_score_rounding(self):
        """Verifica arredondamento para 2 casas decimais."""
        product = {
            "commission": 7.777,
            "priceDiscountRate": 15.555,
            "priceMin": 99.999,
        }
        score = calculate_score(product)
        # Deve retornar valor arredondado
        assert isinstance(score, float)
        # Verifica se tem no máximo 2 casas decimais
        assert round(score * 100) == score * 100


class TestPassesFilters:
    """Testes para função passes_filters."""

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_passes_all_filters(self):
        """Produto passa em todos os filtros."""
        product = {
            "commissionRate": 0.10,
            "commission": 10.0,
            "priceDiscountRate": 20,
            "priceMin": 100,
        }
        thresholds = FilterThresholds()
        assert passes_filters(product, thresholds) is True

    @pytest.mark.unit
    def test_fails_commission_rate(self):
        """Falha por taxa de comissão baixa."""
        product = {
            "commissionRate": 0.03,
            "commission": 10.0,
            "priceDiscountRate": 20,
        }
        thresholds = FilterThresholds(commission_rate_min=0.05)
        assert passes_filters(product, thresholds) is False

    @pytest.mark.unit
    def test_fails_commission_brl(self):
        """Falha por valor de comissão baixo."""
        product = {
            "commissionRate": 0.10,
            "commission": 2.0,
            "priceDiscountRate": 20,
        }
        thresholds = FilterThresholds(commission_min_brl=3.00)
        assert passes_filters(product, thresholds) is False

    @pytest.mark.unit
    def test_fails_discount(self):
        """Falha por desconto insuficiente."""
        product = {
            "commissionRate": 0.10,
            "commission": 10.0,
            "priceDiscountRate": 3,
        }
        thresholds = FilterThresholds(discount_min_pct=5)
        assert passes_filters(product, thresholds) is False

    @pytest.mark.unit
    def test_fails_price_max(self):
        """Falha por preço acima do máximo."""
        product = {
            "commissionRate": 0.10,
            "commission": 50.0,
            "priceDiscountRate": 20,
            "priceMin": 300,
        }
        thresholds = FilterThresholds(price_max_brl=250)
        assert passes_filters(product, thresholds) is False

    @pytest.mark.unit
    def test_price_max_none_no_limit(self):
        """Sem preço máximo, não filtra por preço."""
        product = {
            "commissionRate": 0.10,
            "commission": 10.0,
            "priceDiscountRate": 20,
            "priceMin": 9999,
        }
        thresholds = FilterThresholds(price_max_brl=None)
        assert passes_filters(product, thresholds) is True

    @pytest.mark.unit
    def test_default_thresholds(self):
        """Usa thresholds padrão quando não fornecidos."""
        product = {
            "commissionRate": 0.05,
            "commission": 3.00,
            "priceDiscountRate": 5,
        }
        assert passes_filters(product) is True


class TestRankProducts:
    """Testes para função rank_products."""

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_rank_products_sorting(self):
        """Ordena produtos por score decrescente."""
        products = [
            {"commission": 5, "priceDiscountRate": 10, "priceMin": 100},
            {"commission": 20, "priceDiscountRate": 30, "priceMin": 50},
            {"commission": 10, "priceDiscountRate": 20, "priceMin": 75},
        ]
        ranked = rank_products(products)

        # Verifica ordenação por score
        scores = [p["score"] for p in ranked]
        assert scores == sorted(scores, reverse=True)

        # Produto com maior score deve ser primeiro
        assert ranked[0]["commission"] == 20

    @pytest.mark.unit
    def test_rank_products_adds_score_field(self):
        """Adiciona campo 'score' a cada produto."""
        products = [
            {"commission": 10, "priceDiscountRate": 20, "priceMin": 100},
        ]
        ranked = rank_products(products)

        assert "score" in ranked[0]
        assert isinstance(ranked[0]["score"], (int, float))

    @pytest.mark.unit
    def test_rank_products_empty_list(self):
        """Lida com lista vazia."""
        ranked = rank_products([])
        assert ranked == []

    @pytest.mark.unit
    def test_rank_products_custom_weights(self):
        """Usa pesos personalizados no rankeamento."""
        products = [
            {"commission": 10, "priceDiscountRate": 10, "priceMin": 100},
            {"commission": 5, "priceDiscountRate": 50, "priceMin": 50},
        ]
        weights = ScoreWeights(commission=1.0, discount=2.0, price=0.01)
        ranked = rank_products(products, weights)

        # Com desconto tendo peso 2x, segundo produto deve ter maior score
        assert ranked[0]["commission"] == 5

    @pytest.mark.unit
    def test_rank_products_original_modified(self):
        """Verifica que a lista original é modificada."""
        products = [
            {"commission": 10, "priceDiscountRate": 20, "priceMin": 100},
        ]
        rank_products(products)

        # Original ganha campo score
        assert "score" in products[0]
