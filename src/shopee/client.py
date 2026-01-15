"""Cliente HTTP para Shopee Affiliate API."""

import asyncio
import json

import httpx

from .auth import get_auth_headers
from .queries import (
    CONVERSION_REPORT_QUERY,
    PRODUCT_OFFER_V2_QUERY,
    VALIDATED_REPORT_QUERY,
    build_product_offer_variables,
    get_short_link_query,
)
from src.utils.logger import get_logger

logger = get_logger("mariabicobot", "shopee_client")

SHOPEE_API_URL = "https://open-api.affiliate.shopee.com.br/graphql"
RETRY_DELAYS = [1, 2, 4]


class ShopeeAPIError(Exception):
    """Erro retornado pela API da Shopee."""

    def __init__(self, message: str, code: str = None):
        super().__init__(message)
        self.code = code


class ShopeeClient:
    """Cliente para Shopee Affiliate GraphQL API."""

    def __init__(self, app_id: str, secret: str):
        """Inicializa o cliente.

        Args:
            app_id: App ID da Shopee
            secret: Secret key da Shopee
        """
        self.app_id = app_id
        self.secret = secret
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Fecha a sessão do cliente."""
        await self.client.aclose()

    async def _request(self, query: str, variables: dict = None) -> dict:
        """Executa uma requisição GraphQL."""
        payload_dict = {"query": query, "variables": variables or {}}
        payload_json = json.dumps(payload_dict, separators=(",", ":"), sort_keys=True)

        headers = get_auth_headers(self.app_id, self.secret, payload_json)

        last_error = None

        for attempt, delay in enumerate(RETRY_DELAYS):
            try:
                response = await self.client.post(
                    SHOPEE_API_URL,
                    content=payload_json,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                if "errors" in data:
                    error = data["errors"][0]
                    message = error.get("message", "Erro desconhecido")
                    code = str(error.get("extensions", {}).get("code", ""))

                    # Se for erro de auth, tenta de novo
                    if code == "10020" and attempt < len(RETRY_DELAYS) - 1:
                        logger.warning(
                            f"Erro de autenticação (tentativa {attempt + 1}), tentando novamente..."
                        )
                        continue

                    raise ShopeeAPIError(f"GraphQL Error: {message}", code=code)

                return data

            except (httpx.HTTPError, ShopeeAPIError) as e:
                last_error = e
                logger.warning(f"Erro na requisição (tentativa {attempt + 1}): {e}")
                if attempt < len(RETRY_DELAYS) - 1:
                    await asyncio.sleep(delay)

        raise last_error or ShopeeAPIError("Max retries exceeded")

    async def search_products(
        self,
        keywords: list[str] | str,
        limit: int = 50,
        page: int = 1,
        category_id: int | None = None,
        shop_id: int | None = None,
        list_type: int = 1,
        sort_type: int = 5,
    ) -> list[dict]:
        """Busca produtos via productOfferV2."""
        variables = build_product_offer_variables(
            keywords, limit, page, category_id, shop_id, list_type, sort_type
        )
        data = await self._request(PRODUCT_OFFER_V2_QUERY, variables)

        nodes = data.get("data", {}).get("productOfferV2", {}).get("nodes", [])
        return nodes

    async def get_conversion_report(
        self,
        start_timestamp: int,
        end_timestamp: int,
        page: int = 1,
        limit: int = 500,
        scroll_id: str | None = None,
    ) -> dict:
        """Busca relatório de conversão."""
        variables = {
            "start": start_timestamp,
            "end": end_timestamp,
            "page": page,
            "limit": limit,
        }
        if scroll_id:
            variables["scrollId"] = scroll_id

        return await self._request(CONVERSION_REPORT_QUERY, variables)

    async def get_validated_report(
        self,
        start_timestamp: int,
        end_timestamp: int,
        page: int = 1,
        limit: int = 500,
        scroll_id: str | None = None,
    ) -> dict:
        """Busca relatório de pedidos validados."""
        variables = {
            "start": start_timestamp,
            "end": end_timestamp,
            "page": page,
            "limit": limit,
        }
        if scroll_id:
            variables["scrollId"] = scroll_id

        return await self._request(VALIDATED_REPORT_QUERY, variables)

    async def generate_short_link(
        self,
        origin_url: str,
        sub_ids: list[str],
    ) -> str:
        """Gera um short link rastreável."""
        # Usa query construída dinamicamente para evitar problemas de tipos de input
        query = get_short_link_query(origin_url, sub_ids)

        # Variáveis vazias pois os valores já estão na query string
        data = await self._request(query, variables={})

        result = data.get("data", {}).get("generateShortLink", {})

        if not result or not result.get("shortLink"):
            raise ShopeeAPIError("Falha ao gerar short link: API não retornou o link.")

        return result["shortLink"]