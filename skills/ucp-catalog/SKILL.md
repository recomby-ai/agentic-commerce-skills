---
name: ucp-catalog
description: >
  Maps a merchant's product data to UCP catalog schema format.
  Supports Shopify, WooCommerce, CSV, and web scraping as data sources.
  Outputs UCP-compliant product JSON with field mapping report.
  Use after ucp-audit to convert existing product data.
argument-hint: "[client name] [data source: shopify|woocommerce|csv|url]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch
---

# UCP Catalog Mapper

Extract merchant product data from various sources and transform it into UCP catalog schema format.

## Prerequisites
- `store/clients/{client_name}/audit-report.md` must exist
- For Shopify: store URL (public storefront API)
- For WooCommerce: store URL + API credentials
- For CSV: file path
- For URL: product page URLs to scrape

## Step 1: Connect to Data Source

### Shopify
```python
# Public Storefront API — no auth needed
GET https://{store}.myshopify.com/products.json?limit=250
# Paginate with ?page=2, ?page=3, etc.
```

### WooCommerce
```python
# REST API — needs consumer_key + consumer_secret
GET https://{store}/wp-json/wc/v3/products?per_page=100
# Auth: query param ?consumer_key=ck_xxx&consumer_secret=cs_xxx
```

### CSV
```python
# Expect columns: title, price, description, sku, image_url, category, stock_status
import csv
```

### Web Scraping
```python
# Parse JSON-LD and structured data from product pages
# Fallback: parse HTML for price, title, images
```

## Step 2: Field Mapping

Transform source fields to UCP product schema:

### Product Level (required: id, title, description, price_range, variants)

| UCP Field | Shopify Source | WooCommerce Source | CSV Source |
|-----------|---------------|-------------------|-----------|
| `id` | `id` (string) | `id` (string) | row index or sku |
| `title` | `title` | `name` | `title` |
| `description.plain` | `body_html` (strip tags) | `description` (strip tags) | `description` |
| `price_range.min/max` | min/max of `variants[].price` | `price` / `sale_price` | `price` |
| `url` | `url` or construct from handle | `permalink` | — |
| `categories[]` | `product_type` | `categories[].name` | `category` |
| `media[]` | `images[].src` | `images[].src` | `image_url` |
| `tags[]` | `tags` (split comma) | `tags[].name` | `tags` |

### Variant Level (required: id, title, description, price)

| UCP Field | Shopify Source | WooCommerce Source |
|-----------|---------------|-------------------|
| `id` | `variants[].id` | `variations[].id` |
| `title` | `variants[].title` | `variations[].attributes` joined |
| `description` | inherit from product | inherit from product |
| `price.amount` | `variants[].price` × 100 (to minor units) | `price` × 100 |
| `price.currency` | store currency setting | store currency setting |
| `sku` | `variants[].sku` | `variations[].sku` |
| `availability.available` | `variants[].available` | `stock_status == "instock"` |
| `availability.status` | available ? `in_stock` : `out_of_stock` | `stock_status` |
| `selected_options[]` | `option1/2/3` + `options[]` names | `attributes[]` |

> **HARD RULE — Price conversion to minor units.** UCP prices are integers in minor units (cents). `$29.99` → `2999`. Always verify currency's minor unit factor (most are ×100, JPY is ×1, BHD is ×1000).

## Step 3: Validate Products

For each product, validate against UCP types:

```
✓ id is non-empty string
✓ title is non-empty string
✓ description has at least one of: plain, html, markdown
✓ price_range.min <= price_range.max
✓ price_range.min.amount >= 0
✓ price_range.min.currency is valid ISO 4217
✓ variants is non-empty array (at least 1)
✓ each variant has id, title, description, price
✓ each variant price.amount is integer >= 0
✓ media URLs are valid and accessible (spot check 3)
```

Record validation results per product: PASS / FAIL with details.

## Step 4: Output

Save to `store/clients/{client_name}/`:

### catalog.json
```json
{
  "products": [
    {
      "id": "prod_001",
      "title": "Example Product",
      "description": {"plain": "A great product."},
      "price_range": {
        "min": {"amount": 2999, "currency": "USD"},
        "max": {"amount": 2999, "currency": "USD"}
      },
      "url": "https://example.com/products/example",
      "categories": [{"value": "Electronics", "taxonomy": "merchant"}],
      "media": [{"type": "image", "url": "https://example.com/img/prod_001.jpg"}],
      "variants": [
        {
          "id": "var_001",
          "title": "Default",
          "description": {"plain": "A great product."},
          "price": {"amount": 2999, "currency": "USD"},
          "sku": "EX-001",
          "availability": {"available": true, "status": "in_stock"}
        }
      ]
    }
  ],
  "metadata": {
    "source": "shopify",
    "total_products": 42,
    "total_variants": 87,
    "exported_at": "2026-03-25T12:00:00Z"
  }
}
```

### mapping-report.md
```markdown
# Catalog Mapping Report — {client_name}

**Source:** {platform}
**Products mapped:** {count}
**Variants mapped:** {count}
**Validation:** {passed}/{total} products pass

## Field Coverage
| UCP Field | Mapped | Source Field | Notes |
|-----------|--------|-------------|-------|
| title | ✓ | name | — |
| description | ✓ | description | HTML stripped |
| price | ✓ | price × 100 | Converted to minor units |
| media | ✓ | images[].src | — |
| sku | ✗ | — | Not available in source |

## Issues Found
{list of validation failures or data quality problems}
```

## Scripts

| Script | Purpose | Dependencies |
|--------|---------|-------------|
| `map_catalog.py` | Multi-source catalog mapper | requests, beautifulsoup4, csv, json |

## Collaboration

```
ucp-audit → (audit-report.md) → ucp-catalog (this skill)
                                      │
                                      ├── outputs → catalog.json
                                      ├── outputs → mapping-report.md
                                      │
                                      └── consumed by → ucp-checkout (product data for line items)
```
