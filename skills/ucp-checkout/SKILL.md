---
name: ucp-checkout
description: >
  Generates deployable checkout API code for a merchant's UCP integration.
  Supports Node.js (Express), Python (FastAPI), and PHP (Laravel) templates.
  Implements capability negotiation, session management, line item building,
  totals calculation, and payment handler integration.
  Use after ucp-profile and ucp-catalog are complete.
argument-hint: "[client name] [stack: node|python|php]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UCP Checkout API Generator

Generate a deployable checkout API that implements UCP shopping capabilities.

## Prerequisites
- `store/clients/{client_name}/ucp-profile.json` must exist (from ucp-profile)
- `store/clients/{client_name}/catalog.json` must exist (from ucp-catalog)
- Merchant must specify: tech stack, hosting environment, payment provider credentials

## Step 1: Select Template

| Stack | Framework | Why |
|-------|-----------|-----|
| `node` | Express.js | Most common for Shopify ecosystem |
| `python` | FastAPI | Best for data-heavy catalogs, async support |
| `php` | Laravel | Most common for WooCommerce ecosystem |

## Step 2: Generate Project Structure

### Node.js (Express)
```
ucp-server/
├── package.json
├── .env.example
├── src/
│   ├── index.js              — Server entry, routes
│   ├── middleware/
│   │   └── ucp-negotiation.js — Capability negotiation
│   ├── routes/
│   │   ├── checkout.js       — create/update/retrieve/complete/cancel
│   │   ├── catalog.js        — search/lookup
│   │   └── well-known.js     — /.well-known/ucp static serve
│   ├── services/
│   │   ├── session-store.js  — In-memory session (swap for Redis in prod)
│   │   ├── catalog-service.js — Product data access
│   │   ├── totals.js         — Price calculation engine
│   │   └── payment.js        — Payment handler integration
│   └── schemas/
│       └── ucp-profile.json  — The merchant's profile (from ucp-profile skill)
└── README.md
```

### Python (FastAPI)
```
ucp-server/
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py               — FastAPI app, routes
│   ├── middleware/
│   │   └── negotiation.py
│   ├── routers/
│   │   ├── checkout.py
│   │   ├── catalog.py
│   │   └── well_known.py
│   ├── services/
│   │   ├── session_store.py
│   │   ├── catalog_service.py
│   │   ├── totals.py
│   │   └── payment.py
│   └── schemas/
│       └── ucp_profile.json
└── README.md
```

## Step 3: Implement Core Logic

### 3.1 Capability Negotiation

Every checkout response must include `ucp` metadata with active capabilities:

```python
def negotiate(platform_profile, business_profile):
    """Compute capability intersection between platform and business."""
    platform_caps = set(platform_profile.get("capabilities", {}).keys())
    business_caps = set(business_profile["capabilities"].keys())
    active = platform_caps & business_caps

    # Prune orphaned extensions
    for cap_name, cap_def in business_profile["capabilities"].items():
        if "extends" in cap_def[0]:
            parent = cap_def[0]["extends"]
            if parent not in active:
                active.discard(cap_name)

    return {name: business_profile["capabilities"][name] for name in active}
```

### 3.2 Checkout Session Lifecycle

```
POST /ucp/v1/checkout          → create session
    → status: "incomplete"
    → returns: id, line_items, totals, status, links

POST /ucp/v1/checkout/{id}     → update session
    → recalculate totals
    → status remains "incomplete" or moves to "requires_escalation"

GET  /ucp/v1/checkout/{id}     → retrieve session
    → return current state

POST /ucp/v1/checkout/{id}/complete  → complete session
    → validate payment instrument
    → charge via payment handler
    → status: "complete_in_progress" → "completed"

POST /ucp/v1/checkout/{id}/cancel    → cancel session
    → status: "canceled"
```

### 3.3 Totals Calculation

```python
def calculate_totals(line_items, discounts=None, fulfillment=None, tax_rate=0):
    subtotal = sum(item["item"]["price"]["amount"] * item["quantity"] for item in line_items)

    totals = [
        {"type": "subtotal", "amount": subtotal}
    ]

    if discounts:
        discount_amount = calculate_discounts(discounts, subtotal)
        totals.append({"type": "discount", "amount": -abs(discount_amount)})
        subtotal -= abs(discount_amount)

    if fulfillment:
        shipping = fulfillment["cost"]["amount"]
        totals.append({"type": "fulfillment", "amount": shipping})
        subtotal += shipping

    if tax_rate > 0:
        tax = round(subtotal * tax_rate)
        totals.append({"type": "tax", "amount": tax})
        subtotal += tax

    totals.append({"type": "total", "amount": subtotal})
    return totals
```

> **HARD RULE — Totals must always contain exactly one `subtotal` and one `total`.** Discount amounts must be negative. All other amounts must be >= 0. Amounts are integers in minor units.

### 3.4 Line Items from Catalog

```python
def build_line_item(product_id, variant_id, quantity, catalog):
    product = catalog.find_product(product_id)
    variant = catalog.find_variant(product_id, variant_id)
    return {
        "id": f"li_{variant_id}",
        "item": {
            "id": variant_id,
            "title": variant["title"],
            "price": variant["price"]
        },
        "quantity": quantity,
        "totals": [
            {"type": "subtotal", "amount": variant["price"]["amount"] * quantity},
            {"type": "total", "amount": variant["price"]["amount"] * quantity}
        ]
    }
```

### 3.5 Response Structure

Every checkout response must include:

```json
{
  "ucp": {
    "version": "2026-01-23",
    "capabilities": {},
    "payment_handlers": {}
  },
  "id": "session_xxx",
  "status": "incomplete",
  "currency": "USD",
  "line_items": [],
  "totals": [
    {"type": "subtotal", "amount": 2999, "display_text": "$29.99"},
    {"type": "total", "amount": 2999, "display_text": "$29.99"}
  ],
  "links": [
    {"type": "privacy_policy", "url": "https://example.com/privacy"},
    {"type": "terms_of_service", "url": "https://example.com/tos"}
  ]
}
```

## Step 4: Generate .env Template

```
# UCP Server Configuration
PORT=3000
MERCHANT_DOMAIN=example.com

# Payment Provider (Stripe example)
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx

# Product Data Source
CATALOG_SOURCE=shopify
SHOPIFY_STORE_URL=https://example.myshopify.com

# Session Storage (production)
REDIS_URL=redis://localhost:6379
```

## Step 5: Output

Save to `store/clients/{client_name}/`:
- `ucp-server/` — complete deployable project
- `api-docs.md` — endpoint documentation
- `deploy-guide.md` — hosting instructions (Vercel, Railway, VPS)

## Scripts

| Script | Purpose | Dependencies |
|--------|---------|-------------|
| `generate_api.py` | Code generator using Jinja2 templates | jinja2, json |

## Templates

Located in `templates/`:
- `node/` — Express.js project template
- `python/` — FastAPI project template
- `php/` — Laravel project template

## Collaboration

```
ucp-profile → (ucp-profile.json) ──┐
                                    ├── ucp-checkout (this skill)
ucp-catalog → (catalog.json) ──────┘         │
                                              ├── outputs → ucp-server/ (deployable code)
                                              ├── outputs → api-docs.md
                                              ├── outputs → deploy-guide.md
                                              │
                                              └── verified by → ucp-validate
```
