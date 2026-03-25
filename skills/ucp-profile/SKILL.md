---
name: ucp-profile
description: >
  Generates a complete /.well-known/ucp business profile JSON for a merchant.
  Reads audit report to determine capabilities and payment handlers.
  Outputs deployment-ready JSON plus hosting instructions.
  Use after ucp-audit has produced a readiness report.
argument-hint: "[client name from store/clients/]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UCP Profile Generator

Generate a valid `/.well-known/ucp` business profile JSON based on the merchant's audit report.

## Prerequisites
- `store/clients/{client_name}/audit-report.md` must exist (from ucp-audit)
- Merchant must confirm: business name, domain, supported payment provider(s)

## Step 1: Read Audit Report

1.1. Parse the audit report for:
- `platform` — determines API endpoint patterns
- `payment_providers` — determines payment_handlers section
- `product_fields_available` — determines if catalog capability is viable
- `has_public_api` — determines transport type

1.2. Ask merchant to confirm/provide:
- Legal business name
- Primary domain (for namespace authority)
- Which capabilities they want to support (recommend based on audit)
- Payment provider API keys (for handler config — do NOT store these in profile)

## Step 2: Determine Capabilities

Based on audit results, select applicable capabilities:

| Capability | Include If |
|-----------|-----------|
| `dev.ucp.shopping.checkout` | Always (this is the minimum) |
| `dev.ucp.shopping.catalog.search` | Product data is accessible via API or structured data |
| `dev.ucp.shopping.catalog.lookup` | Same as search (they come as a pair) |
| `dev.ucp.shopping.cart` | Platform supports multi-item cart (Shopify, WooCommerce = yes) |
| `dev.ucp.shopping.fulfillment` | Merchant ships physical products |
| `dev.ucp.shopping.discount` | Merchant supports discount codes |
| `dev.ucp.shopping.order` | Merchant can expose order status via API |

## Step 3: Build Payment Handlers

Map detected payment providers to UCP payment_handler format:

### Stripe
```json
{
  "com.stripe.payment_element": [{
    "id": "stripe_default",
    "version": "2026-01-23",
    "spec": "https://stripe.com/docs/ucp",
    "schema": "https://stripe.com/schemas/ucp/payment_element.json",
    "available_instruments": [
      {"type": "card", "constraints": {"brands": ["visa", "mastercard", "amex"]}},
      {"type": "wallet", "constraints": {"providers": ["apple_pay", "google_pay"]}}
    ],
    "config": {
      "publishable_key_required": true
    }
  }]
}
```

### Adyen
```json
{
  "com.adyen.dropin": [{
    "id": "adyen_default",
    "version": "2026-01-23",
    "spec": "https://adyen.com/docs/ucp",
    "schema": "https://adyen.com/schemas/ucp/dropin.json",
    "available_instruments": [
      {"type": "card", "constraints": {"brands": ["visa", "mastercard", "amex"]}}
    ]
  }]
}
```

> **HARD RULE — Never include API secret keys in the profile.** The profile is public. Only include publishable/public identifiers. Secret keys go in server-side environment variables.

## Step 4: Assemble Profile JSON

Build the complete profile following this structure:

```json
{
  "ucp": {
    "version": "2026-01-23",
    "services": {
      "dev.ucp.shopping": [{
        "version": "2026-01-23",
        "transport": "rest",
        "endpoint": "https://{merchant_domain}/ucp/v1",
        "spec": "https://ucp.dev/specification/shopping",
        "schema": "https://ucp.dev/schemas/shopping/openapi.json"
      }]
    },
    "capabilities": {
      "dev.ucp.shopping.checkout": [{
        "version": "2026-01-23",
        "spec": "https://ucp.dev/specification/shopping/checkout",
        "schema": "https://ucp.dev/schemas/shopping/checkout.json"
      }]
    },
    "payment_handlers": {}
  }
}
```

Fill in:
- `services` — based on transport type (rest for most, mcp if agent-native)
- `capabilities` — from Step 2 selection
- `payment_handlers` — from Step 3

## Step 5: Validate & Output

5.1. Validate the generated profile:
- All required fields present
- Version format YYYY-MM-DD
- Namespace naming convention correct
- Spec/schema URLs use correct origin for namespace
- At least one service, one capability, one payment handler

5.2. Save outputs to `store/clients/{client_name}/`:
- `ucp-profile.json` — the deployable profile
- `deployment-guide.md` — how to host it

### Deployment Guide Content

```markdown
# Deploying Your UCP Profile

## File
Copy `ucp-profile.json` to your web server at:
`{your-domain}/.well-known/ucp`

## Server Configuration

### Nginx
location = /.well-known/ucp {
    default_type application/json;
    alias /path/to/ucp-profile.json;
    add_header Access-Control-Allow-Origin "*";
}

### Apache
<Files "ucp">
    ForceType application/json
    Header set Access-Control-Allow-Origin "*"
</Files>

### Shopify / Hosted Platform
Upload as a static asset or use a proxy worker (Cloudflare Worker / Vercel Edge Function).

## Verification
After deployment, run: ucp-validate {your-domain}
```

## Scripts

| Script | Purpose | Dependencies |
|--------|---------|-------------|
| `generate_profile.py` | Profile builder with validation | json, jsonschema |

## Collaboration

```
ucp-audit → (audit-report.md) → ucp-profile (this skill)
                                      │
                                      ├── outputs → ucp-profile.json
                                      ├── outputs → deployment-guide.md
                                      │
                                      └── consumed by → ucp-checkout (reads profile for API design)
```
