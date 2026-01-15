"""Queries GraphQL da Shopee Affiliate API."""

import json

# Query para busca detalhada de produtos
PRODUCT_OFFER_V2_QUERY = """
query ($keyword: String, $page: Int, $limit: Int, $categoryId: Int64, $shopId: Int64, $listType: Int, $sortType: Int) {
  productOfferV2(
    keyword: $keyword
    productCatId: $categoryId
    shopId: $shopId
    matchId: $shopId
    listType: $listType
    sortType: $sortType
    page: $page
    limit: $limit
  ) {
    nodes {
      itemId
      productName
      commissionRate
      commission
      priceMin
      priceMax
      sales
      ratingStar
      imageUrl
      offerLink
      shopName
    }
    pageInfo {
      page
      limit
      hasNextPage
    }
  }
}
"""


# Query para relatórios de conversão
CONVERSION_REPORT_QUERY = """
query ($start: Int64!, $end: Int64!, $page: Int!, $limit: Int!, $scrollId: String) {
  conversionReport(
    purchaseTimeStart: $start
    purchaseTimeEnd: $end
    page: $page
    limit: $limit
    scrollId: $scrollId
  ) {
    nodes {
      orderId
      purchaseTime
      commissionRate
      commissionAmount
      orderStatus
      subIds
      productName
      itemPrice
    }
    pageInfo {
      page
      limit
      hasNextPage
      scrollId
    }
  }
}
"""

# Query para relatórios validados (pagos)
VALIDATED_REPORT_QUERY = """
query ($start: Int64!, $end: Int64!, $page: Int!, $limit: Int!, $scrollId: String) {
  validatedReport(
    purchaseTimeStart: $start
    purchaseTimeEnd: $end
    page: $page
    limit: $limit
    scrollId: $scrollId
  ) {
    nodes {
      orderId
      purchaseTime
      commissionRate
      commissionAmount
      orderStatus
      subIds
      productName
      itemPrice
    }
    pageInfo {
      hasNextPage
      scrollId
    }
  }
}
"""


def build_product_offer_variables(
    keywords: list[str] | str,
    limit: int = 50,
    page: int = 1,
    category_id: int | None = None,
    shop_id: int | None = None,
    list_type: int = 1,
    sort_type: int = 5,
) -> dict:
    """Constrói variáveis para query productOfferV2."""
    keyword_str = " ".join(keywords) if isinstance(keywords, list) else keywords

    variables = {
        "keyword": keyword_str,
        "page": page,
        "limit": limit,
        "listType": list_type,
        "sortType": sort_type,
    }

    if category_id:
        variables["categoryId"] = category_id
    if shop_id:
        variables["shopId"] = shop_id

    return variables


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
