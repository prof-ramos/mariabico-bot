# Fix Shopee API Integration and Signature

I've analyzed the issues with the Shopee Affiliate API integration. The "Invalid Signature" and
"Unknown type" errors are due to a mismatch between our implementation and the actual API
expectations as documented in Context7.

## User Review Required

> [!IMPORTANT] This plan changes the GraphQL queries and field names used for Shopee products. This
> is necessary because the previous "ProductSearchRequest" type was not recognized by the API.

## Proposed Changes

### Shopee Client & Authentication

#### [MODIFY] [src/shopee/auth.py](file:///Users/gabrielramos/mariabico-bot/src/shopee/auth.py)

- Ensure the signature is calculated using the full JSON payload.

#### [MODIFY] [src/shopee/client.py](file:///Users/gabrielramos/mariabico-bot/src/shopee/client.py)

- Use a consistent JSON serialization (minified, sorted) for both the signature and the request
  body.
- Update `search_products` and `generate_short_link` to handle the new field names.

#### [MODIFY] [src/shopee/queries.py](file:///Users/gabrielramos/mariabico-bot/src/shopee/queries.py)

- Switch from `productOfferV2` to `shopeeOfferV2`.
- Remove the `ProductSearchRequest` input type and use direct arguments.
- Update fields to match the `ShopeeOfferV2` schema: `offerName`, `offerLink`, `commissionRate`,
  etc.

### Core Logic

#### [MODIFY] [src/core/curator.py](file:///Users/gabrielramos/mariabico-bot/src/core/curator.py)

- Update product field mapping to handle new API fields.
- Fix keyword assignment logic.

#### [MODIFY] [src/core/scoring.py](file:///Users/gabrielramos/mariabico-bot/src/core/scoring.py)

- Update `passes_filters` and `calculate_score` to handle field names and type conversions (e.g.,
  `commissionRate` from string to float).

## Verification Plan

### Automated Tests

- `uv run python scripts/test_telegram.py`

### Manual Verification

1. **Bot Start**: Verify that `/start` in private chat works.
2. **Curadoria Agora**: Press the button and verify:
   - Bot logs show successful product fetch (no 10020 or Unknown Type errors).
   - Bot sends the consolidated message to the target group.
3. **Link Conversion**: Send a Shopee link in private chat and verify it generates a short link.
