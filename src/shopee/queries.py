"""Queries GraphQL da Shopee Affiliate API."""

# Query para buscar produtos (productOfferV2)
PRODUCT_OFFER_V2_QUERY = """
query ProductOfferV2($request: ProductSearchRequest!) {
  productOfferV2(request: $request) {
    nodes {
      itemId
      productName
      productLink
      originUrl
      priceMin
      priceMax
      priceDiscountRate
      commission
      commissionRate
      shopName
      sales
      rating
      imageUrl
    }
    pageInfo {
      page
      limit
      hasNextPage
    }
  }
}
"""

# Mutation para gerar short link
GENERATE_SHORT_LINK_QUERY = """
mutation GenerateShortLink($request: GenerateShortLinkRequest!) {
  generateShortLink(request: $request) {
    shortLink
    error {
      code
      message
    }
  }
}
"""


def build_product_offer_variables(
    keywords: list[str],
    limit: int = 50,
    page: int = 1,
    categories: list[int] | None = None,
    list_type: str = "hot",
) -> dict:
    """Constrói variáveis para query productOfferV2.

    Args:
        keywords: Lista de keywords para buscar
        limit: Limite de itens por página
        page: Número da página
        categories: Lista de IDs de categorias (opcional)
        list_type: Tipo de lista ("hot", "new", etc)

    Returns:
        Dicionário com variáveis para a query
    """
    request: dict = {
        "keywords": keywords,
        "limit": limit,
        "page": page,
        "listType": list_type,
    }

    if categories:
        request["productCatId"] = categories

    return {"request": request}


def build_short_link_variables(origin_url: str, sub_ids: list[str]) -> dict:
    """Constrói variáveis para mutation generateShortLink.

    Args:
        origin_url: URL original do produto Shopee
        sub_ids: Lista de subIds para rastreamento (max 5)

    Returns:
        Dicionário com variáveis para a mutation
    """
    return {
        "request": {
            "originUrl": origin_url,
            "subIds": sub_ids[:5],  # Max 5 subIds
        }
    }
