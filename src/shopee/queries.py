"""Queries GraphQL da Shopee Affiliate API."""

import json

# Query para buscar produtos (productOfferV2)
# Mantemos variáveis aqui pois types básicos (String, Int) são conhecidos e funcionaram
PRODUCT_OFFER_V2_QUERY = """
query ($keyword: String, $sortType: Int, $page: Int, $limit: Int) {
  productOfferV2(keyword: $keyword, sortType: $sortType, page: $page, limit: $limit) {
    nodes {
      itemId
      productName
      productLink
      priceMin
      priceDiscountRate
      commissionRate
      commission
      sales
      ratingStar
      imageUrl
      offerLink
    }
    pageInfo {
      page
      limit
      hasNextPage
    }
  }
}
"""


def build_product_offer_variables(
    keywords: list[str],
    limit: int = 50,
    page: int = 1,
    categories: list[int] | None = None,
    sort_type: int = 2,
) -> dict:
    """Constrói variáveis para query productOfferV2."""
    keyword_str = " ".join(keywords) if isinstance(keywords, list) else keywords

    return {
        "keyword": keyword_str,
        "sortType": sort_type,
        "page": page,
        "limit": limit,
    }


def get_short_link_query(origin_url: str, sub_ids: list[str]) -> str:
    """Gera a mutation generateShortLink com argumentos inline.

    Isso evita erros de "Unknown Type" para o input object, já que a documentação
    não deixa claro se o type é GenerateShortLinkRequest ou GenerateShortLinkInput.
    """
    # Garante que inputs sejam strings JSON válidas
    url_json = json.dumps(origin_url)
    sub_ids_json = json.dumps(sub_ids[:5])

    # Monta a mutation com input object literal
    return f"""
    mutation {{
      generateShortLink(input: {{
        originUrl: {url_json},
        subIds: {sub_ids_json}
      }}) {{
        shortLink
      }}
    }}
    """
