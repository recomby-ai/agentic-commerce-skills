# Schema.org Types Guide — Key Types for Agent Commerce

## Format: JSON-LD

All examples use JSON-LD embedded in `<script type="application/ld+json">`.
Google recommends JSON-LD over Microdata or RDFa.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Acme Corp"
}
</script>
```

Multiple JSON-LD blocks per page are valid and encouraged — one per entity.

## Core Types

### Organization

The foundation. Every site should have this on the homepage.

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://example.com/#org",
  "name": "Acme Corp",
  "url": "https://example.com",
  "logo": "https://example.com/logo.png",
  "description": "Cloud analytics platform for SaaS companies",
  "email": "hello@example.com",
  "sameAs": [
    "https://twitter.com/acme",
    "https://linkedin.com/company/acme",
    "https://github.com/acme"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "email": "support@example.com",
    "contactType": "customer support"
  }
}
```

**Required:** `name`
**Recommended:** `url`, `logo`, `description`, `sameAs`, `contactPoint`

### WebSite

Pair with Organization on the homepage.

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "@id": "https://example.com/#website",
  "name": "Acme Corp",
  "url": "https://example.com",
  "publisher": {"@id": "https://example.com/#org"},
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://example.com/search?q={search_term}",
    "query-input": "required name=search_term"
  }
}
```

### Product

For product pages. Each product gets its own block.

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "@id": "https://example.com/products/widget-pro#product",
  "name": "Widget Pro",
  "description": "Professional widget with advanced features",
  "image": "https://example.com/images/widget-pro.jpg",
  "brand": {"@id": "https://example.com/#org"},
  "sku": "WP-001",
  "offers": {
    "@type": "Offer",
    "price": "49.99",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock",
    "url": "https://example.com/products/widget-pro",
    "seller": {"@id": "https://example.com/#org"}
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "reviewCount": "127"
  }
}
```

**Required for Google rich results:** `name`, `offers` or `review`
**Recommended:** `image`, `description`, `sku`, `brand`, `aggregateRating`

### Service

For service businesses without physical products.

```json
{
  "@context": "https://schema.org",
  "@type": "Service",
  "@id": "https://example.com/services/geo-audit#service",
  "name": "GEO Audit",
  "description": "Analyze your brand visibility across AI platforms",
  "provider": {"@id": "https://example.com/#org"},
  "serviceType": "Digital Marketing",
  "areaServed": "Worldwide",
  "offers": {
    "@type": "Offer",
    "price": "499",
    "priceCurrency": "USD",
    "description": "One-time comprehensive audit"
  }
}
```

### LocalBusiness

For businesses with physical locations. Extends Organization.

```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "@id": "https://example.com/#business",
  "name": "Acme Coffee Shop",
  "image": "https://example.com/storefront.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Main St",
    "addressLocality": "Austin",
    "addressRegion": "TX",
    "postalCode": "78701",
    "addressCountry": "US"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": "30.2672",
    "longitude": "-97.7431"
  },
  "telephone": "+1-512-555-0123",
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "opens": "07:00",
      "closes": "19:00"
    }
  ],
  "priceRange": "$$"
}
```

**Required for Google:** `name`, `address`
**Recommended:** `geo`, `telephone`, `openingHoursSpecification`

### FAQPage

High-value for AI extraction. AI agents love FAQ schema.

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is GEO optimization?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "GEO (Generative Engine Optimization) is the practice of optimizing content so AI assistants recommend your business."
      }
    },
    {
      "@type": "Question",
      "name": "How much does it cost?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Plans start at $499/month for basic monitoring."
      }
    }
  ]
}
```

### BreadcrumbList

Navigation context. Helps agents understand page hierarchy.

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com"},
    {"@type": "ListItem", "position": 2, "name": "Products", "item": "https://example.com/products"},
    {"@type": "ListItem", "position": 3, "name": "Widget Pro"}
  ]
}
```

### SoftwareApplication

For SaaS products and apps.

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Acme Analytics",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Web",
  "offers": {
    "@type": "Offer",
    "price": "49",
    "priceCurrency": "USD",
    "description": "Monthly subscription"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "reviewCount": "342"
  }
}
```

## Connecting Entities with @id

Use `@id` to create references between entities across your site:

```json
// Homepage: Organization
{"@type": "Organization", "@id": "https://example.com/#org", "name": "Acme"}

// Product page: references Organization
{"@type": "Product", "brand": {"@id": "https://example.com/#org"}}

// Service page: references Organization
{"@type": "Service", "provider": {"@id": "https://example.com/#org"}}
```

## Validation Requirements

### Google Requirements

- JSON-LD content must match visible page content
- Don't mark up hidden or invisible content
- Don't use structured data to deceive (fake reviews, wrong prices)
- Test with: https://search.google.com/test/rich-results

### Common Errors

| Error | Fix |
|-------|-----|
| Missing required field | Add the field with accurate data |
| Price mismatch | Ensure JSON-LD price matches page price |
| Invalid @type | Check spelling against schema.org |
| Missing @context | Add `"@context": "https://schema.org"` |
| Broken image URL | Verify image exists and is accessible |

## Type Selection Guide

| Business Type | Primary Types |
|--------------|---------------|
| SaaS | Organization, WebSite, SoftwareApplication, FAQPage |
| E-commerce | Organization, Product, Offer, BreadcrumbList |
| Local business | LocalBusiness, FAQPage, BreadcrumbList |
| Service company | Organization, Service, FAQPage |
| Blog/Content | Organization, WebSite, Article, BreadcrumbList |
| Agency | Organization, Service, FAQPage |
