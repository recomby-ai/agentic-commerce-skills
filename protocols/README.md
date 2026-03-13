# Protocol Landscape

The agentic web is being built on a growing stack of interoperable protocols. Two ecosystems are forming, with several neutral/independent standards bridging the gap.

## Ecosystem Map

| Layer | Google / Open | OpenAI / Anthropic | Neutral / Independent |
|-------|--------------|-------------------|----------------------|
| **Discovery** | [A2A Agent Cards](discovery.md#a2a-agent-cards), [NLWeb](discovery.md#nlweb) | - | [llms.txt](discovery.md#llmstxt), [Schema.org](discovery.md#schemaorg) |
| **Communication** | [A2A](communication.md#a2a), [AG-UI](communication.md#ag-ui) | [MCP](communication.md#mcp) | [ANP](communication.md#anp) |
| **Commerce** | [UCP](commerce.md#ucp) | [ACP](commerce.md#acp) | - |
| **Payments** | [AP2](payments.md#ap2) | [Stripe SPT](payments.md#stripe-spt) | [x402](payments.md#x402), [Visa TAP](payments.md#visa-tap) |
| **Identity** | - | - | [OAuth Agent Ext](identity.md#oauth-20-agent-extensions), [DID](identity.md#did), [OIDC-A](identity.md#oidc-a) |
| **Licensing** | - | - | [RSL](licensing.md#rsl), [ai.txt](licensing.md#aitxt) |

## Two Camps

### Google / Open Ecosystem
Google anchors the open-standard side with **A2A** (agent-to-agent communication), **UCP** (commerce with Shopify), **AP2** (payments), and **NLWeb** (Microsoft, built on Schema.org). These protocols share design principles: HTTP-native, JSON-based, open-source under Apache 2.0, and governed through the Linux Foundation. AG-UI (CopilotKit) bridges agent backends to frontends and aligns with this camp.

### OpenAI / Anthropic Ecosystem
Anthropic's **MCP** (model-context protocol) handles tool/context integration, now donated to the Linux Foundation's Agentic AI Foundation (AAIF). OpenAI co-developed **ACP** with Stripe for commerce, powering Instant Checkout in ChatGPT. Stripe's **Shared Payment Tokens** handle the payment layer.

### Neutral / Independent
Several protocols sit outside either camp:
- **llms.txt** and **Schema.org** -- publisher-side discovery standards
- **x402** (Coinbase) -- HTTP 402 stablecoin micropayments
- **Visa TAP** -- trusted agent identity for card-network commerce
- **OAuth Agent Extensions** and **DID** -- identity/auth standards from IETF and W3C
- **RSL** and **ai.txt** -- content licensing for the AI era

## Convergence Signals

- MCP, A2A, and AGENTS.md all live under the **Linux Foundation AAIF** (Dec 2025)
- UCP explicitly supports MCP, A2A, and AP2 as transport layers
- Visa TAP aligns with ACP and x402
- AP2 backers include Visa, Mastercard, PayPal, Coinbase, and Stripe

## Index

| File | Protocols |
|------|-----------|
| [discovery.md](discovery.md) | llms.txt, A2A Agent Cards, NLWeb, Schema.org |
| [communication.md](communication.md) | MCP, A2A, AG-UI, ANP |
| [commerce.md](commerce.md) | ACP, UCP |
| [payments.md](payments.md) | AP2, Stripe SPT, PayPal Agent Toolkit, x402, Visa TAP |
| [identity.md](identity.md) | OAuth 2.0 Agent Extensions, DID, OIDC-A |
| [licensing.md](licensing.md) | RSL, ai.txt |
