# Agent Payment Landscape

## The Problem

Traditional payment flows assume a human clicking buttons. Agent commerce
needs programmatic payment authorization without exposing card details to
AI systems. Three solutions have emerged, each from a different part of
the financial stack.

## Three Payment Protocols

### 1. Stripe SPT (Payment Layer)
- **Who:** Stripe (via ACP partnership with OpenAI)
- **What:** Delegated Payment Tokens — scoped, one-time tokens for agent purchases
- **Model:** Agent requests token from Stripe, presents to merchant
- **Best for:** E-commerce checkout, high-value transactions, Stripe merchants
- **Fees:** 2.9% + $0.30 (Stripe) + 4% (ACP protocol) = ~6.9% + $0.30
- **Settlement:** 2-7 business days (standard Stripe)

### 2. x402 (Protocol Layer)
- **Who:** Coinbase
- **What:** HTTP 402 Payment Required as native web payment
- **Model:** Request -> 402 -> pay USDC -> retry with proof -> access
- **Best for:** API monetization, micropayments, per-request pricing
- **Fees:** Gas only (<$0.01 on Base L2)
- **Settlement:** ~2 seconds (Base L2 blockchain)
- **Stats:** 100M+ transactions, $24M+ volume, 5.6k GitHub stars

### 3. Visa AP2 (Network Layer)
- **Who:** Visa (with Worldpay, Adyen, Stripe as acquirers)
- **What:** Mandate-based payment authorization for agents
- **Model:** User creates mandate (spending rules) -> agent operates within rules
- **Best for:** Recurring purchases, enterprise, high-trust scenarios
- **Fees:** Standard card processing rates
- **Settlement:** Real-time via Visa Direct Commerce

## When to Use Which

| Scenario | Recommended Protocol |
|----------|---------------------|
| E-commerce checkout (one-time purchase) | Stripe SPT |
| API pay-per-query ($0.001 - $1 range) | x402 |
| Subscription/recurring agent purchases | Visa AP2 |
| Agent tool monetization (MCP tools) | x402 |
| High-value transactions (>$100) | Stripe SPT or AP2 |
| Crypto-native / DeFi audience | x402 |
| Enterprise with existing card rails | Visa AP2 |
| Maximum simplicity (1 line of code) | x402 |

## Security Comparison

| Property | Stripe SPT | x402 | Visa AP2 |
|----------|-----------|------|----------|
| Agent sees card details | No | N/A (USDC) | No |
| Scoped to merchant | Yes | N/A | Yes (mandate) |
| Amount-limited | Yes (per token) | Yes (per request) | Yes (per mandate) |
| Time-limited | Yes (expires) | Yes (nonce) | Yes (mandate period) |
| Chargebacks | Yes | No (blockchain) | Yes (special category) |
| KYC required | Full (Stripe) | Wallet only | Full (Visa) |

## Implementation Effort

| Protocol | Merchant Effort | Agent Effort |
|----------|----------------|--------------|
| Stripe SPT | Medium (Stripe setup + ACP endpoints) | Low (Stripe SDK) |
| x402 | Low (1 middleware line) | Low (auto-pay library) |
| Visa AP2 | Medium (acquirer setup) | High (certification required) |

## The Convergence Thesis

These three protocols will likely converge:
- Stripe is adding x402-style micropayments
- Coinbase is adding fiat on-ramps to x402
- Visa AP2 mandates could authorize Stripe SPT token creation
- UCP's payment_handler already supports multiple providers

Smart merchants prepare for convergence by abstracting their payment layer
behind a common interface that can route to any protocol.

## Key Decision: Start with One

For most businesses starting with agent commerce:
1. **Already on Stripe?** Start with Stripe SPT (works with ACP)
2. **Selling API access or digital goods?** Start with x402
3. **Enterprise with card network relationships?** Wait for AP2 GA

Add the second protocol once the first is generating revenue.
