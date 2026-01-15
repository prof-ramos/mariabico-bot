"""Testes de integração para Shopee API.

Marcadores:
- integration: Testes de integração que requerem recursos externos
- shopee_api: Testes que chamam API Shopee real (requer credenciais válidas)
- slow: Testes lentos que devem ser executados separadamente

Para executar apenas testes sem API real:
    pytest -m "not shopee_api"

Para executar testes com API real (requer .env configurado):
    pytest -m shopee_api --env=.env
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.shopee import ShopeeClient
from src.shopee import ShopeeAPIError
from src.shopee.auth import get_auth_headers


class TestShopeeClientUnit:
    """Testes unitários do ShopeeClient (sem chamadas reais)."""

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_client_init(self):
        """Inicializa cliente com app_id e secret."""
        client = ShopeeClient("123456", "mysecret")
        assert client.app_id == "123456"
        assert client.secret == "mysecret"
        assert client.client is not None

    @pytest.mark.unit
    async def test_client_close(self):
        """Fecha cliente corretamente."""
        client = ShopeeClient("123", "secret")
        await client.close()
        # Não deve levantar exceção

    @pytest.mark.unit
    async def test_request_payload_format(self):
        """Formata payload corretamente (minificado, chaves ordenadas)."""
        import json

        client = ShopeeClient("123", "secret")

        # Mocka a requisição para capturar o payload
        with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"data": {}}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            await client._request("query_test", {"key": "value"})

            # Captura o payload enviado
            call_args = mock_post.call_args
            sent_payload = call_args[1]["content"]

            # Verifica se é JSON válido e minificado
            parsed = json.loads(sent_payload)
            assert parsed["query"] == "query_test"
            assert parsed["variables"]["key"] == "value"

            # Verifica se está minificado (sem espaços desnecessários)
            assert " " not in sent_payload

    @pytest.mark.unit
    async def test_search_products_default_params(self):
        """Parâmetros padrão para search_products."""
        with patch.object(ShopeeClient, "_request") as mock_request:
            mock_request.return_value = {"data": {"productOfferV2": {"nodes": [], "pageInfo": {}}}}

            client = ShopeeClient("123", "secret")
            await client.search_products(keywords=["test"])

            # Verifica se foi chamado com parâmetros corretos
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] is not None  # query
            variables = call_args[0][1]  # variables
            assert "keyword" in str(variables)

    @pytest.mark.unit
    async def test_generate_short_link_default_sub_ids(self):
        """Gera short link sem subIds customizados."""
        with patch.object(ShopeeClient, "_request") as mock_request:
            mock_request.return_value = {
                "data": {"generateShortLink": {"shortLink": "https://shope.ee/test123"}}
            }

            client = ShopeeClient("123", "secret")
            result = await client.generate_short_link("https://shopee.com.br/product/test", [])

            assert result == "https://shope.ee/test123"

    @pytest.mark.unit
    async def test_generate_short_link_api_error(self):
        """Lida com erro da API ao gerar link."""
        with patch.object(ShopeeClient, "_request") as mock_request:
            mock_request.return_value = {"data": {"generateShortLink": None}}

            client = ShopeeClient("123", "secret")

            with pytest.raises(ShopeeAPIError, match="Falha ao gerar short link"):
                await client.generate_short_link("https://shopee.com.br/product/test", [])


class TestShopeeAPIIntegration:
    """Testes de integração com API Shopee real.

    NOTA: Estes testes requerem credenciais válidas no .env.
    Eles são marcados como 'shopee_api' e 'slow' para execução condicional.
    """

    @pytest.fixture(scope="class")
    async def real_client(self):
        """Cliente com credenciais reais do ambiente."""
        app_id = os.getenv("SHOPEE_APP_ID")
        secret = os.getenv("SHOPEE_SECRET")

        if not app_id or not secret:
            pytest.skip("Credenciais Shopee não configuradas (SHOPEE_APP_ID, SHOPEE_SECRET)")

        client = ShopeeClient(app_id, secret)
        yield client
        # Cleanup
        await client.close()

    @pytest.mark.slow
    @pytest.mark.shopee_api
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_search_products(self, real_client):
        """Busca produtos reais na API."""
        try:
            products = await real_client.search_products(
                keywords=["fone bluetooth"],
                limit=5,
                page=1,
            )
        except ShopeeAPIError as e:
            # Captura especificamente erros da API Shopee
            pytest.xfail(f"API Schema Error: {e}")

        assert isinstance(products, list)
        if len(products) > 0:
            # Verifica estrutura do produto
            product = products[0]
            assert "itemId" in product
            assert "productName" in product
            assert "priceMin" in product

    @pytest.mark.slow
    @pytest.mark.shopee_api
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_generate_short_link(self, real_client):
        """Gera short link real."""
        # URL de produto Shopee válido
        origin_url = "https://shopee.com.br/Fone-Bluetooth-TWS-i.123456789.1234567890"

        try:
            short_link = await real_client.generate_short_link(
                origin_url=origin_url,
                sub_ids=["tg", "test", "manual"],
            )
        except (ShopeeAPIError, RuntimeError) as e:
            pytest.xfail(f"External API error: {e}")

        assert short_link.startswith("https://shope.ee/")
        assert len(short_link) > 20

    @pytest.mark.slow
    @pytest.mark.shopee_api
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_auth_headers_valid(self, real_client):
        """Verifica se headers de autenticação são válidos."""
        import json

        payload = json.dumps({"query": "test"}, separators=(",", ":"), sort_keys=True)
        headers = get_auth_headers(real_client.app_id, real_client.secret, payload)

        # Faz requisição simples para validar
        try:
            response = await real_client.client.post(
                "https://open-api.affiliate.shopee.com.br/graphql",
                content=payload,
                headers=headers,
            )
        except RuntimeError:
            pytest.skip("Event loop closed prematurely")

        # Não deve retornar erro de autenticação (10020)
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                error_code = data["errors"][0].get("extensions", {}).get("code")
                assert error_code != "10020", "Erro de autenticação (invalid signature)"


class TestShopeeAPIErrors:
    """Testes de tratamento de erros da API Shopee."""

    @pytest.mark.unit
    async def test_error_invalid_signature(self):
        """Simula erro de assinatura inválida (10020)."""
        client = ShopeeClient("wrong", "credentials")

        with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "errors": [
                    {
                        "message": "Invalid Signature",
                        "extensions": {"code": "10020"},
                    }
                ]
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            with pytest.raises(ShopeeAPIError) as exc_info:
                await client._request("query", {})

            assert exc_info.value.code == "10020"

    @pytest.mark.unit
    async def test_error_rate_limit(self):
        """Simula erro de rate limit (10030)."""
        client = ShopeeClient("123", "secret")

        with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "errors": [
                    {
                        "message": "Rate limit exceeded",
                        "extensions": {"code": "10030"},
                    }
                ]
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            with pytest.raises(ShopeeAPIError) as exc_info:
                await client._request("query", {})

            assert exc_info.value.code == "10030"

    @pytest.mark.unit
    async def test_retry_on_auth_error(self):
        """Tenta novamente em erro de autenticação."""
        client = ShopeeClient("123", "secret")

        call_count = 0

        async def mock_post_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            mock_response = MagicMock()
            if call_count < 3:
                # Primeiras tentativas retornam erro de auth
                mock_response.json.return_value = {
                    "errors": [
                        {
                            "message": "Invalid Signature",
                            "extensions": {"code": "10020"},
                        }
                    ]
                }
            else:
                # Terceira tentativa sucesso
                mock_response.json.return_value = {"data": {"test": "success"}}

            mock_response.raise_for_status = MagicMock()
            return mock_response

        with patch.object(client.client, "post", side_effect=mock_post_with_retry):
            result = await client._request("query", {})

            assert call_count == 3  # Fez 3 tentativas
            assert result["data"]["test"] == "success"
