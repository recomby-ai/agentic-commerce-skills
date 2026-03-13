---
name: ar-commerce
description: >
  Makes a website transactable by AI agents. Implements ACP (OpenAI+Stripe)
  checkout sessions and/or UCP (Google+Shopify) commerce manifests so agents
  can browse products and place orders. Use when a site needs to accept
  purchases from AI agents.
argument-hint: [url]
allowed-tools: Bash, Read, Grep, Glob, Write, Edit
---

# ar-commerce — Make agents buy from you

## Before you start

1. Read [philosophy.md](references/philosophy.md) — why agentic commerce matters
2. Read [acp-guide.md](references/acp-guide.md) — ACP protocol (OpenAI + Stripe)
3. Read [ucp-guide.md](references/ucp-guide.md) — UCP protocol (Google + Shopify)
4. Read [dual-protocol.md](references/dual-protocol.md) — supporting both simultaneously
5. Check [cases/](references/cases/) — someone may have solved this for the same stack

## Step 1: Search for latest specs

Before implementing any commerce protocol, search the web for current specs:
- Search `OpenAI ACP Agent Commerce Protocol spec` — confirm checkout session endpoints and DPT format
- Search `Google UCP Unified Commerce Protocol spec` — confirm manifest schema and capabilities
- Search `agenticcommerce.dev` — confirm ACP latest version
- Search `developers.google.com merchant ucp` — confirm UCP latest version

Do NOT rely on your training data or even the references here — these protocols are actively evolving.

## Step 2: Assess current state

Run the validator to see what commerce protocols the site already supports:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/validate_commerce.py --url $ARGUMENTS
```

## Step 3: Add Product structured data

If not already present, add Schema.org Product/Offer JSON-LD for each product page:

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Product Name",
  "description": "...",
  "image": "https://...",
  "offers": {
    "@type": "Offer",
    "price": "29.99",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock",
    "url": "https://..."
  }
}
```

This is the foundation — both ACP and UCP need product data to work.

## Step 4: Implement UCP manifest

Create `/.well-known/ucp` manifest per Google UCP spec:

- Top-level `ucp` object with `version` (e.g. "0.1.0")
- `services[]` listing available capabilities
- Capabilities use reverse-domain naming: `dev.ucp.shopping.product.search`, `.product.details`, `.cart.create`, `.checkout`
- `payment_handlers` specifying accepted payment methods
- `signing_keys` in JWK format (EC P-256, ES256) for manifest integrity

Shopify stores: UCP is auto-enabled at `/.well-known/ucp`. Verify it's accessible.

## Step 5: Implement ACP checkout

Set up ACP checkout per OpenAI + Stripe spec:

- Integrate Stripe.js and create checkout session endpoints
- Implement 5 REST endpoints on `checkout_sessions`:
  1. `POST /v1/checkout_sessions` — create
  2. `GET /v1/checkout_sessions/{id}` — retrieve
  3. `POST /v1/checkout_sessions/{id}` — update
  4. `POST /v1/checkout_sessions/{id}/complete` — complete with DPT
  5. `POST /v1/checkout_sessions/{id}/cancel` — cancel
- Session state machine: incomplete → not_ready_for_payment → ready_for_payment → completed/canceled
- Implement Delegated Payment Token (DPT) handling — one-time use, amount-scoped, merchant-scoped

## Step 6: Validate

Re-run the validator:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/validate_commerce.py --url $ARGUMENTS
```

- Exit code 0 = commerce protocols detected and valid → done
- Exit code 1 = issues found → fix and re-validate
- Repeat until all checks pass

## Step 7: Write back

Add a case to `references/cases/` using [_template.md](references/cases/_template.md). Especially:

- Which protocol was easier to implement for your stack
- Gotchas with DPT token handling or UCP manifest signing
- How you handled the dual-protocol setup

## References

- [philosophy.md](references/philosophy.md) — market data, strategic context
- [acp-guide.md](references/acp-guide.md) — ACP endpoints, DPT flow, Stripe integration
- [ucp-guide.md](references/ucp-guide.md) — UCP manifest, capabilities, transports
- [dual-protocol.md](references/dual-protocol.md) — supporting both protocols
- [cases/](references/cases/) — real-world commerce cases
