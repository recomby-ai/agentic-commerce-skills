# Payment Protocols

How agents handle money -- authorization, tokenization, and settlement.

---

## AP2

**What:** An open, payment-agnostic protocol for agents to complete transactions via cards, bank transfers, or stablecoins | **By:** Google | **Status:** Active, backed by Visa, Mastercard, PayPal, Coinbase, Amex
**Spec:** [ap2-protocol.org](https://ap2-protocol.org/) | **GitHub:** Part of [UCP ecosystem](https://developers.google.com/merchant/ucp)

- Payment-method agnostic: supports cards, bank transfers, wallets, and stablecoins
- Uses cryptographic user mandates to prove consent -- agents cannot spend without explicit permission
- Designed as an extension to A2A and MCP protocols
- Backers include Mastercard, PayPal, American Express, Coinbase, Salesforce, Shopify, Cloudflare, Etsy
- Part of Google's UCP stack: UCP (commerce) + AP2 (payments) + A2A (communication)

---

## Stripe SPT

**What:** Shared Payment Tokens that let agents initiate payments using a buyer's stored payment method without exposing credentials | **By:** Stripe | **Status:** Active, expanding to BNPL and card network tokens (2026)
**Spec:** [docs.stripe.com/agentic-commerce/concepts/shared-payment-tokens](https://docs.stripe.com/agentic-commerce/concepts/shared-payment-tokens) | **Docs:** [docs.stripe.com/agentic-commerce](https://docs.stripe.com/agentic-commerce/concepts)

- Agents receive a scoped token from the buyer -- no raw card numbers or credentials exposed
- Sellers can limit tokens by time, amount, or usage count; revoke at any time via webhook
- Compatible with Mastercard Agent Pay and Visa Intelligent Commerce network tokens
- BNPL expansion: Affirm and Klarna support added (March 2026)
- Powers ACP (Agentic Commerce Protocol) checkout flow in ChatGPT
- Stripe began supporting x402 USDC payments on Base chain (Feb 2026)

---

## PayPal Agent Toolkit

**What:** A developer toolkit and payment solution for integrating PayPal into AI agent workflows | **By:** PayPal | **Status:** Active, "Agent Ready" launching early 2026
**Spec:** [paypal.ai](https://paypal.ai/) | **GitHub:** [paypal/agent-toolkit](https://github.com/paypal/agent-toolkit)

- SDK for agents to manage payments, invoices, disputes, subscriptions, and shipment tracking
- Compatible with MCP servers and Vercel AI SDK; TypeScript first, Python coming soon
- **Agent Ready**: instant agentic payments for existing PayPal merchants -- no additional integration needed
- **Store Sync**: makes merchant product data discoverable in AI channels with order fulfillment routing
- Supports AP2 (Agent Payments Protocol) as an open standard for agent-driven transactions
- Built-in fraud detection, buyer protection, and dispute resolution carry over from PayPal's existing infrastructure

---

## Visa TAP

**What:** A cryptographic protocol for AI agents to prove identity and authorization to merchants during checkout | **By:** Visa + Cloudflare | **Status:** Active, pilots in APAC and Europe starting early 2026
**Spec:** [developer.visa.com/capabilities/trusted-agent-protocol](https://developer.visa.com/capabilities/trusted-agent-protocol) | **GitHub:** [visa/trusted-agent-protocol](https://github.com/visa/trusted-agent-protocol)

- Every agent request is cryptographically signed and locked to a specific merchant URL and page
- Three data layers: Agent Intent (trusted agent identification), Consumer Recognition (existing account check), Payment Information (preferred checkout method)
- Distinguishes legitimate AI agents from malicious bots at the merchant endpoint
- Aligns with OpenAI's ACP and Coinbase's x402 standards
- 100+ partners worldwide; 30+ building in VIC sandbox; 20+ agents integrating directly
- Developed in collaboration with Cloudflare for edge-level verification

---

## x402

**What:** An HTTP-native protocol that uses the 402 "Payment Required" status code for instant stablecoin micropayments | **By:** Coinbase + Cloudflare | **Status:** Active, x402 Foundation established, 15M+ transactions
**Spec:** [x402.org](https://www.x402.org/) | **GitHub:** [coinbase/x402](https://github.com/coinbase/x402)

- Server returns HTTP 402 with payment instructions; client sends signed payment in header; server verifies and settles
- Supports USDC and USDT on EVM chains and Solana -- no accounts, sessions, or complex auth needed
- TypeScript and Go SDKs available; CAIP-2 network identifiers for multi-chain support
- Designed for API monetization, content access, and agent-to-agent micropayments
- 15M+ transactions across all projects; Stripe began using x402 for USDC on Base (Feb 2026)
- Ideal for agent economies where pay-per-call is more natural than subscriptions
