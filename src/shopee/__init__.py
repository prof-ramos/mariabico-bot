"""Cliente Shopee Affiliate API."""

from .client import ShopeeAPIError, ShopeeClient
from .queries import (
    PRODUCT_OFFER_V2_QUERY,
    build_product_offer_variables,
    get_short_link_query,
)

__all__ = [
    "ShopeeClient",
    "ShopeeAPIError",
    "PRODUCT_OFFER_V2_QUERY",
    "build_product_offer_variables",
    "get_short_link_query",
]
