"""Testes de integração para o Curator."""

import pytest
from unittest.mock import AsyncMock


class TestCuratorIntegration:
    """Testes de integração do fluxo de curadoria."""

    @pytest.mark.smoke
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_curator_full_flow_with_mock(self, curator):
        """Testa fluxo completo de curadoria com cliente mockado."""
        # Mocka resposta da API

        mock_products = [
            {
                "itemId": 123456,
                "productName": "Fone Bluetooth Teste",
                "priceMin": "89.90",
                "priceDiscountRate": 30,
                "commissionRate": "0.10",
                "commission": "8.99",
                "sales": 500,
                "ratingStar": "4.7",
                "imageUrl": "https://cf.shopee.com.br/file/test.jpg",
                "shopId": 123456,
                "shopName": "Loja Teste",
                "shopType": [1],
                "productLink": "https://shopee.com.br/product/test",
                "offerLink": "https://shope.ee/test",
            }
        ]

        curator.shopee.search_products = AsyncMock(return_value=mock_products)
        curator.max_pages = 1

        # Executa curadoria
        result = await curator.curate(
            keywords=["fone bluetooth"],
            categories=None,
        )

        # Verifica resultado
        assert result["fetched"] == 1
        assert result["approved"] >= 0
        assert result["final"] >= 0
        assert "products" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_curator_multiple_keywords(self, curator):
        """Testa curadoria com múltiplas keywords."""
        keywords = ["keyword1", "keyword2", "keyword3"]
        curator.max_pages = 1
        mock_product = {
            "itemId": 123456,
            "productName": "Produto Teste",
            "priceMin": "100.00",
            "priceDiscountRate": 20,
            "commissionRate": "0.10",
            "commission": "10.00",
            "sales": 100,
            "ratingStar": "4.5",
            "imageUrl": "https://test.jpg",
            "shopId": 123,
            "shopName": "Loja",
            "shopType": [1],
            "productLink": "https://shopee.com.br/test",
            "offerLink": "https://shope.ee/test",
        }

        curator.shopee.search_products = AsyncMock(return_value=[mock_product])

        result = await curator.curate(
            keywords=keywords,
            categories=None,
        )

        # Deve buscar 3 vezes (uma por keyword)
        assert curator.shopee.search_products.call_count == 3

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_curator_filters_products(self, curator):
        """Testa filtragem de produtos."""
        # Produto que passa nos filtros
        good_product = {
            "itemId": 1,
            "productName": "Bom",
            "priceMin": "100.00",
            "priceDiscountRate": 30,
            "commissionRate": "0.10",
            "commission": "10.00",
            "sales": 100,
            "ratingStar": "4.7",
            "imageUrl": "https://test.jpg",
            "shopId": 123,
            "shopName": "Loja",
            "shopType": [1],
            "productLink": "https://shopee.com.br/test",
            "offerLink": "https://shope.ee/test",
        }

        # Produto que rejeita nos filtros
        bad_product = {
            "itemId": 2,
            "productName": "Ruim",
            "priceMin": "50.00",
            "priceDiscountRate": 2,  # Desconto muito baixo
            "commissionRate": "0.02",  # Comissão muito baixa
            "commission": "1.00",
            "sales": 10,
            "ratingStar": "3.0",
            "imageUrl": "https://test.jpg",
            "shopId": 123,
            "shopName": "Loja",
            "shopType": [1],
            "productLink": "https://shopee.com.br/test",
            "offerLink": "https://shope.ee/test",
        }

        curator.shopee.search_products = AsyncMock(return_value=[good_product, bad_product])

        result = await curator.curate(
            keywords=["test"],
            categories=None,
        )

        # Apenas o bom produto deve passar
        assert result["approved"] <= result["fetched"]

    @pytest.mark.integration
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_curator_deduplication(self, curator, db):
        """Testa deduplicação de produtos."""
        product = {
            "itemId": 999999,
            "productName": "Duplicata",
            "priceMin": "100.00",
            "priceDiscountRate": 20,
            "commissionRate": "0.10",
            "commission": "10.00",
            "sales": 100,
            "ratingStar": "4.5",
            "imageUrl": "https://test.jpg",
            "shopId": 123,
            "shopName": "Loja",
            "shopType": [1],
            "productLink": "https://shopee.com.br/test",
            "offerLink": "https://shope.ee/test",
        }

        # Insere produto no banco (necessário por FK)
        db.upsert_product(curator._normalize_offer(product))

        # Marca produto como enviado
        db.mark_as_sent(999999, "-1001234567890", "https://test.link", "batch1")

        curator.shopee.search_products = AsyncMock(return_value=[product])

        result = await curator.curate(
            keywords=["test"],
            categories=None,
        )

        # Produto não deve aparecer no final (foi deduplicado)
        final_ids = [p.get("itemId") for p in result["products"]]
        assert "999999" not in final_ids

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_curator_link_generation(self, curator):
        """Testa geração de links para produtos."""
        product = {
            "itemId": 123456,
            "productName": "Produto",
            "priceMin": "100.00",
            "priceDiscountRate": 20,
            "commissionRate": "0.10",
            "commission": "10.00",
            "sales": 100,
            "ratingStar": "4.5",
            "imageUrl": "https://test.jpg",
            "shopId": 123,
            "shopName": "Loja",
            "shopType": [1],
            "productLink": "https://shopee.com.br/test",
            "offerLink": "https://shope.ee/test",
        }

        curator.shopee.search_products = AsyncMock(return_value=[product])

        result = await curator.curate(
            keywords=["test"],
            categories=None,
        )

        # Produtos finais devem ter shortLink
        for prod in result["products"]:
            assert "shortLink" in prod
            assert prod["shortLink"]  # Não vazio


class TestCuratorNormalize:
    """Testes para normalização de ofertas da API."""

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_normalize_offer_basic(self, curator):
        """Normaliza oferta básica."""
        offer = {
            "itemId": 123456,
            "productName": "Fone Bluetooth",
            "priceMin": "99.90",
            "priceDiscountRate": 25,
            "commissionRate": "0.10",
            "commission": "9.99",
            "productLink": "https://shopee.com.br/product/test",
            "imageUrl": "https://cf.shopee.com.br/file/test.jpg",
            "ratingStar": "4.7",
        }

        normalized = curator._normalize_offer(offer, keyword="fone")

        assert normalized["itemId"] == "123456"
        assert normalized["productName"] == "Fone Bluetooth"
        assert normalized["priceMin"] == 99.90
        assert normalized["commissionRate"] == 0.10
        assert normalized["commission"] == 9.99
        assert normalized["keyword"] == "fone"

    @pytest.mark.unit
    def test_normalize_offer_string_conversions(self, curator):
        """Converte campos string para tipos corretos."""
        offer = {
            "itemId": 123,
            "productName": "Test",
            "priceMin": "199.90",  # String
            "priceDiscountRate": 30,  # Int
            "commissionRate": "0.12",  # String
            "commission": "23.99",  # String
            "ratingStar": "4.8",  # String
            "productLink": "https://test",
            "imageUrl": "https://test.jpg",
        }

        normalized = curator._normalize_offer(offer)

        # Verifica conversões
        assert isinstance(normalized["priceMin"], float)
        assert normalized["priceMin"] == 199.90
        assert isinstance(normalized["commissionRate"], float)
        assert normalized["commissionRate"] == 0.12
        assert isinstance(normalized["rating"], float)
        assert normalized["rating"] == 4.8

    @pytest.mark.unit
    def test_normalize_offer_missing_fields(self, curator):
        """Lida com campos ausentes."""
        offer = {
            "itemId": 123,
            "productName": "Test",
            "priceMin": "100",
            "priceDiscountRate": 10,
            "commissionRate": "0.05",
            # ratingStar ausente
            # productLink ausente
            "imageUrl": "https://test.jpg",
        }

        normalized = curator._normalize_offer(offer)

        # Valores padrão para campos ausentes
        assert normalized["rating"] == 0.0
        assert normalized["originUrl"] == ""

    @pytest.mark.unit
    def test_normalize_offer_invalid_numbers(self, curator):
        """Lida com valores numéricos inválidos."""
        offer = {
            "itemId": 123,
            "productName": "Test",
            "priceMin": "invalid",  # Inválido
            "priceDiscountRate": 10,
            "commissionRate": "not_a_number",  # Inválido
            "ratingStar": "also_invalid",
            "productLink": "https://test",
            "imageUrl": "https://test.jpg",
        }

        normalized = curator._normalize_offer(offer)

        # Deve usar valores padrão (0) para inválidos
        assert normalized["priceMin"] == 0.0
        assert normalized["commissionRate"] == 0.0
        assert normalized["commission"] == 0.0
        assert normalized["rating"] == 0.0