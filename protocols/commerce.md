# Commerce Protocols

How agents browse, compare, and purchase products on behalf of users.

---

## ACP

**What:** An open standard for AI agents to discover products, negotiate terms, and complete purchases | **By:** OpenAI + Stripe | **Status:** Active, Apache 2.0, powering ChatGPT Instant Checkout
**Spec:** [developers.openai.com/commerce](https://developers.openai.com/commerce/guides/get-started/) | **GitHub:** [agentic-commerce-protocol/agentic-commerce-protocol](https://github.com/agentic-commerce-protocol/agentic-commerce-protocol)

- Defines the full purchase flow: product discovery, pricing, cart, checkout, fulfillment, and returns
- Merchants remain the merchant of record -- they control pricing, presentation, and fulfillment
- Build once, distribute to any ACP-compatible agent (ChatGPT, and others as they adopt)
- Already live: US ChatGPT users can buy from Etsy and 1M+ Shopify merchants via Instant Checkout
- Spec releases: initial (Sep 2025), fulfillment (Dec 2025), capability negotiation (Jan 2026), extensions + discounts (Jan 2026)
- Works with any commerce backend and payment provider -- not locked to Stripe

---

## UCP

**What:** An open protocol for AI agents to discover products, manage carts, and complete checkout across merchants | **By:** Google + Shopify | **Status:** Active, rolling out on Google Search AI Mode and Gemini
**Spec:** [developers.google.com/merchant/ucp](https://developers.google.com/merchant/ucp) | **GitHub:** [google/ucp](https://github.com/nichochar/ucp) (community reference)

- Establishes common primitives: product discovery, inventory, cart, checkout, and fulfillment
- `ucp.json` manifest acts as a store "passport" -- broadcasts capabilities to any compliant agent
- Multi-transport: supports REST, MCP, A2A, and AP2 as underlying protocols
- Backed by 20+ partners: Shopify, Etsy, Wayfair, Target, Walmart, Best Buy, Visa, Mastercard, Stripe, Adyen
- Shopify merchants get native selling on Google Search AI Mode and Gemini app
- Announced Jan 2025 at NRF by Sundar Pichai; open-source under Apache 2.0

### ACP vs UCP

| | ACP | UCP |
|---|-----|-----|
| **Led by** | OpenAI + Stripe | Google + Shopify |
| **First surface** | ChatGPT Instant Checkout | Google AI Mode, Gemini |
| **Payment layer** | Stripe SPT | AP2 (multi-provider) |
| **Transport** | REST | REST, MCP, A2A, AP2 |
| **Merchant reach** | Shopify, Etsy | Shopify, Walmart, Target, 20+ |

Both are Apache 2.0, open-source, and merchant-centric. Expect convergence as both mature.
