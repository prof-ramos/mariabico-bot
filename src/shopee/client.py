"""Cliente HTTP para Shopee Affiliate API."""
import asyncio
from typing import Any

import httpx

from .auth import get_auth_headers
from .queries import (
    GENERATE_SHORT_LINK_QUERY,
    PRODUCT_OFFER_V2_QUERY,
    build_product_offer_variables,
    build_short_link_variables,
)

# Endpoint da API Shopee
SHOPEE_API_URL = "https://open-api.affiliate.shopee.com.br/graphql"

# Timeout padrão (segundos)
DEFAULT_TIMEOUT = 10.0

# Máximo de tentativas
MAX_RETRIES = 3

# Delays para retry (segundos)
RETRY_DELAYS = [1.0, 2.0, 4.0]


class ShopeeAPIError(Exception):
    """Erro na API Shopee."""

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.code = code


class ShopeeClient:
    """Cliente para Shopee Affiliate API."""

    def __init__(self, app_id: str, secret: str):
        """Inicializa o cliente.

        Args:
            app_id: App ID da Shopee
            secret: Secret key da Shopee
        """
        self.app_id = app_id
        self.secret = secret
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Retorna o cliente HTTP (lazy initialization)."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)
        return self._client

    async def close(self) -> None:
        """Fecha o cliente HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(self, query: str, variables: dict) -> dict:
        """Faz uma requisição GraphQL com retry.

        Args:
            query: Query GraphQL
            variables: Variáveis da query

        Returns:
            Resposta da API como dicionário

        Raises:
            ShopeeAPIError: Em caso de erro na API
        """
        payload = {"query": query, "variables": variables}
        headers = get_auth_headers(self.app_id, self.secret, query)

        last_error = None

        for attempt, delay in enumerate(RETRY_DELAYS):
            try:
                response = await self.client.post(
                    SHOPEE_API_URL,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

                data = response.json()

                # Verifica erros da API
                if "errors" in data:
                    error = data["errors"][0]
                    raise ShopeeAPIError(error.get("message", "Unknown API error"), error.get("code"))

                return data

            except (httpx.HTTPError, ShopeeAPIError) as e:
                last_error = e
                if attempt < len(RETRY_DELAYS) - 1:
                    await asyncio.sleep(delay)

        raise last_error or ShopeeAPIError("Max retries exceeded")

    async def search_products(
        self,
        keywords: list[str],
        limit: int = 50,
        page: int = 1,
        categories: list[int] | None = None,
        list_type: str = "hot",
    ) -> list[dict]:
        """Busca produtos via productOfferV2.

        Args:
            keywords: Lista de keywords para buscar
            limit: Limite de itens por página (max 50)
            page: Número da página
            categories: Lista de IDs de categorias (opcional)
            list_type: Tipo de lista ("hot", "new", etc)

        Returns:
            Lista de produtos (dicionários)

        Raises:
            ShopeeAPIError: Em caso de erro na API
        """
        variables = build_product_offer_variables(keywords, limit, page, categories, list_type)
        data = await self._request(PRODUCT_OFFER_V2_QUERY, variables)

        nodes = data["data"]["productOfferV2"]["nodes"]
        return nodes

    async def generate_short_link(
        self,
        origin_url: str,
        sub_ids: list[str],
    ) -> str:
        """Gera um short link rastreável.

        Args:
            origin_url: URL original do produto Shopee
            sub_ids: Lista de subIds para rastreamento (max 5)

        Returns:
            Short link (ex: https://shope.ee/abc123)

        Raises:
            ShopeeAPIError: Em caso de erro na API
        """
        variables = build_short_link_variables(origin_url, sub_ids)
        data = await self._request(GENERATE_SHORT_LINK_QUERY, variables)

        result = data["data"]["generateShortLink"]

        # Verifica erro na mutation
        if result.get("error"):
            error = result["error"]
            raise ShopeeAPIError(error["message"], error["code"])

        return result["shortLink"]
