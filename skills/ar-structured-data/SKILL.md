---
name: ar-structured-data
description: >
  Makes a website understandable by AI agents. Audits existing structured data,
  generates Schema.org JSON-LD markup, and validates against Google Search
  Central requirements. Use when a site needs structured data so AI agents
  can parse its products, services, or content.
argument-hint: [url]
allowed-tools: Bash, Read, Grep, Glob, Write, Edit
---

# ar-structured-data — Make agents understand you

## Before you start

1. Read [philosophy.md](references/philosophy.md) — why structured data matters for agents
2. Read [schema-types-guide.md](references/schema-types-guide.md) — which Schema.org types to use
3. Read [ecommerce-schema.md](references/ecommerce-schema.md) — e-commerce specific patterns
4. Check [cases/](references/cases/) — someone may have solved this for the same stack

## Step 1: Search for latest specs

Before generating any markup, search the web to confirm current requirements:
- Search `Google Search Central structured data requirements` — confirm required properties per type
- Search `schema.org Product` (or whatever type you need) — confirm current property definitions
- Search `JSON-LD best practices 2026` — confirm current recommendations

Do NOT rely on your training data or even the references here — Google updates requirements regularly.

## Step 2: Audit existing structured data

Scan the target site to see what's already there:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/audit_structured_data.py --url $ARGUMENTS
```

This reports: JSON-LD blocks found, types detected, missing properties, gaps.

## Step 3: Determine what's needed

Based on the audit and page content, decide which Schema.org types to add:

| Page type | Schema.org type | Key properties |
|-----------|----------------|----------------|
| Homepage | Organization | name, url, logo, description, contactPoint |
| Product page | Product | name, description, image, offers (price, currency, availability) |
| Service page | Service | name, description, provider, areaServed |
| Blog/article | Article | headline, author, datePublished, image |
| FAQ page | FAQPage | mainEntity → Question → acceptedAnswer |
| Local business | LocalBusiness | name, address, telephone, openingHours, geo |
| About page | AboutPage + Organization | foundingDate, founders, numberOfEmployees |

## Step 4: Generate JSON-LD

For each page that needs structured data, generate a `<script type="application/ld+json">` block:

- Always set `@context` to `https://schema.org`
- Always set `@type` to the correct type
- Fill ALL required properties per Google Search Central:
  - Product: name + one of (review, aggregateRating, offers)
  - Offer: price (required), priceCurrency (recommended)
  - Organization: name, url (recommended, no required per Google)
- Fill recommended properties where data is available
- Use proper data types (ISO 8601 dates, full URLs for images)

## Step 5: Add OpenGraph meta tags

If missing, add OG tags to page `<head>`:

```html
<meta property="og:title" content="..." />
<meta property="og:description" content="..." />
<meta property="og:image" content="..." />
<meta property="og:url" content="..." />
<meta property="og:type" content="website" />
```

## Step 6: Validate

Validate generated JSON-LD against spec:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/validate_schema.py --file output.json
```

- Exit code 0 = all required properties present → done
- Exit code 1 = missing required properties → fix and re-validate
- Repeat until all checks pass

## Step 7: Write back

If you learned something useful, add a case to `references/cases/` using [_template.md](references/cases/_template.md). Especially:

- Which types gave the most value for AI agents
- Platform-specific ways to inject JSON-LD (Shopify Liquid, WordPress plugins, Next.js Head)
- Common validation errors and fixes

## References

- [philosophy.md](references/philosophy.md) — why structured data matters
- [schema-types-guide.md](references/schema-types-guide.md) — types and properties reference
- [ecommerce-schema.md](references/ecommerce-schema.md) — e-commerce patterns
- [cases/](references/cases/) — real-world implementation cases
