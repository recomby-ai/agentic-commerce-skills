# E-Commerce Schema Patterns

## Overview

E-commerce sites need the richest structured data. AI shopping agents
compare products across sites using structured data. The more complete
and accurate your schema, the more likely an agent recommends your product.

This guide covers patterns specific to online stores, marketplaces,
and product catalogs.

## Product Page Pattern

A complete product page should have:

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BreadcrumbList",
      "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://store.com"},
        {"@type": "ListItem", "position": 2, "name": "Electronics", "item": "https://store.com/electronics"},
        {"@type": "ListItem", "position": 3, "name": "Wireless Headphones"}
      ]
    },
    {
      "@type": "Product",
      "@id": "https://store.com/products/wh-100#product",
      "name": "ProSound WH-100 Wireless Headphones",
      "description": "Active noise cancelling wireless headphones with 30-hour battery",
      "image": [
        "https://store.com/images/wh-100-front.jpg",
        "https://store.com/images/wh-100-side.jpg"
      ],
      "sku": "WH-100",
      "gtin13": "0123456789012",
      "brand": {
        "@type": "Brand",
        "name": "ProSound"
      },
      "color": "Black",
      "material": "Aluminum, Memory Foam",
      "weight": {"@type": "QuantitativeValue", "value": "250", "unitCode": "GRM"},
      "offers": {
        "@type": "Offer",
        "url": "https://store.com/products/wh-100",
        "price": "149.99",
        "priceCurrency": "USD",
        "priceValidUntil": "2026-12-31",
        "availability": "https://schema.org/InStock",
        "itemCondition": "https://schema.org/NewCondition",
        "seller": {"@id": "https://store.com/#org"},
        "shippingDetails": {
          "@type": "OfferShippingDetails",
          "shippingRate": {
            "@type": "MonetaryAmount",
            "value": "0",
            "currency": "USD"
          },
          "deliveryTime": {
            "@type": "ShippingDeliveryTime",
            "handlingTime": {"@type": "QuantitativeValue", "minValue": 0, "maxValue": 1, "unitCode": "DAY"},
            "transitTime": {"@type": "QuantitativeValue", "minValue": 3, "maxValue": 5, "unitCode": "DAY"}
          },
          "shippingDestination": {
            "@type": "DefinedRegion",
            "addressCountry": "US"
          }
        },
        "hasMerchantReturnPolicy": {
          "@type": "MerchantReturnPolicy",
          "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
          "merchantReturnDays": 30,
          "returnMethod": "https://schema.org/ReturnByMail"
        }
      },
      "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "4.6",
        "bestRating": "5",
        "reviewCount": "283"
      },
      "review": [
        {
          "@type": "Review",
          "reviewRating": {"@type": "Rating", "ratingValue": "5"},
          "author": {"@type": "Person", "name": "Alex M."},
          "datePublished": "2026-01-15",
          "reviewBody": "Best noise cancelling in this price range."
        }
      ]
    }
  ]
}
```

## Product Variants

For products with size/color variants, use `ProductGroup`:

```json
{
  "@type": "ProductGroup",
  "name": "ProSound WH-100",
  "variesBy": ["https://schema.org/color"],
  "hasVariant": [
    {
      "@type": "Product",
      "name": "ProSound WH-100 - Black",
      "color": "Black",
      "sku": "WH-100-BLK",
      "offers": {"@type": "Offer", "price": "149.99", "priceCurrency": "USD"}
    },
    {
      "@type": "Product",
      "name": "ProSound WH-100 - Silver",
      "color": "Silver",
      "sku": "WH-100-SLV",
      "offers": {"@type": "Offer", "price": "149.99", "priceCurrency": "USD"}
    }
  ]
}
```

## Category / Collection Page

```json
{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "name": "Wireless Headphones",
  "description": "Browse our collection of wireless headphones",
  "url": "https://store.com/electronics/headphones",
  "mainEntity": {
    "@type": "ItemList",
    "numberOfItems": 24,
    "itemListElement": [
      {"@type": "ListItem", "position": 1, "url": "https://store.com/products/wh-100"},
      {"@type": "ListItem", "position": 2, "url": "https://store.com/products/wh-200"},
      {"@type": "ListItem", "position": 3, "url": "https://store.com/products/wh-300"}
    ]
  }
}
```

## Offer Patterns

### Sale Price

```json
{
  "@type": "Offer",
  "price": "99.99",
  "priceCurrency": "USD",
  "priceValidUntil": "2026-03-31",
  "availability": "https://schema.org/InStock"
}
```

### Subscription / SaaS Pricing

```json
{
  "@type": "Offer",
  "price": "49",
  "priceCurrency": "USD",
  "description": "Monthly subscription",
  "eligibleDuration": {"@type": "QuantitativeValue", "value": "1", "unitCode": "MON"}
}
```

### Multiple Price Tiers

```json
{
  "@type": "AggregateOffer",
  "lowPrice": "29",
  "highPrice": "299",
  "priceCurrency": "USD",
  "offerCount": 3,
  "offers": [
    {"@type": "Offer", "name": "Starter", "price": "29", "priceCurrency": "USD"},
    {"@type": "Offer", "name": "Pro", "price": "99", "priceCurrency": "USD"},
    {"@type": "Offer", "name": "Enterprise", "price": "299", "priceCurrency": "USD"}
  ]
}
```

### Out of Stock

```json
{
  "@type": "Offer",
  "price": "149.99",
  "priceCurrency": "USD",
  "availability": "https://schema.org/OutOfStock"
}
```

## Availability Values

| Value | Use When |
|-------|----------|
| `InStock` | Available for immediate purchase |
| `OutOfStock` | Currently unavailable |
| `PreOrder` | Available for pre-order |
| `BackOrder` | Available but delayed shipping |
| `Discontinued` | No longer sold |
| `LimitedAvailability` | Low stock or limited quantities |

## Review Patterns

### Individual Review

```json
{
  "@type": "Review",
  "reviewRating": {
    "@type": "Rating",
    "ratingValue": "4",
    "bestRating": "5",
    "worstRating": "1"
  },
  "author": {"@type": "Person", "name": "Jane D."},
  "datePublished": "2026-02-10",
  "reviewBody": "Great product, fast shipping."
}
```

### Aggregate Rating

```json
{
  "@type": "AggregateRating",
  "ratingValue": "4.5",
  "bestRating": "5",
  "reviewCount": "127",
  "ratingCount": "450"
}
```

## Common Mistakes

1. **Price in schema doesn't match page.** Google may remove rich results.
2. **Fake reviews in structured data.** Can result in manual action penalty.
3. **Using InStock when out of stock.** Frustrates users and agents.
4. **Missing currency on Offer.** Price without currency is meaningless.
5. **No image on Product.** Disqualifies from Google product rich results.
6. **Duplicate Organization blocks.** Use `@id` references instead.

## Checklist for Product Pages

- [ ] Product name matches page title
- [ ] Price matches visible price (including currency)
- [ ] Availability matches actual stock status
- [ ] At least one image URL that resolves
- [ ] SKU or GTIN identifier present
- [ ] Brand linked to Organization via @id
- [ ] Review data matches real reviews
- [ ] BreadcrumbList reflects page hierarchy
