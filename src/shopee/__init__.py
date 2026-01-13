"""Cliente Shopee Affiliate API."""
from .client import ShopeeAPIError, ShopeeClient
from .queries import (
    GENERATE_SHORT_LINK_QUERY,
    PRODUCT_OFFER_V2_QUERY,
    build_product_offer_variables,
    build_short_link_variables,
)

__all__ = [
    "ShopeeClient",
    "ShopeeAPIError",
    "PRODUCT_OFFER_V2_QUERY",
    "GENERATE_SHORT_LINK_QUERY",
    "build_product_offer_variables",
    "build_short_link_variables",
]
