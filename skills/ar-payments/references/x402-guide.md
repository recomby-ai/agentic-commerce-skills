# x402 Protocol Guide

HTTP 402 Payment Required — Native Web Micropayments

Repo: https://github.com/coinbase/x402
Stats: 100M+ transactions, $24M+ volume, 5.6k stars
Currency: USDC on Base (Coinbase as facilitator)

## Overview

x402 turns the HTTP 402 status code into a native payment protocol. When a
server requires payment, it responds with 402 and payment instructions. The
client pays inline and retries with proof of payment.

This is the simplest payment model for agents: request -> pay -> access.
No checkout sessions, no state machines, no OAuth flows.

## Flow

```
Agent                          Server                      Facilitator
  |                              |                              |
  | GET /api/premium-data        |                              |
  |----------------------------->|                              |
  |                              |                              |
  | 402 Payment Required         |                              |
  | X-Payment-Amount: 0.01      |                              |
  | X-Payment-Currency: USDC    |                              |
  | X-Payment-Address: 0x...    |                              |
  |<-----------------------------|                              |
  |                              |                              |
  | Create + sign payment        |                              |
  |----------------------------------------------------->       |
  |                              |                              |
  | GET /api/premium-data        |                              |
  | X-Payment: <signed-tx>      |                              |
  |----------------------------->|                              |
  |                              | Verify payment               |
  |                              |----------------------------->|
  |                              |<-----------------------------|
  |                              |                              |
  | 200 OK + data               |                              |
  |<-----------------------------|                              |
```

## 402 Response Headers

| Header | Example | Description |
|--------|---------|-------------|
| X-Payment-Amount | "0.01" | USDC amount |
| X-Payment-Currency | "USDC" | Payment currency |
| X-Payment-Network | "base" | Blockchain network |
| X-Payment-Address | "0x..." | Recipient wallet |
| X-Payment-Facilitator | "https://x402.coinbase.com" | Facilitator URL |
| X-Payment-Description | "API access" | Human-readable description |
| X-Payment-Expiry | "1706648400" | Payment deadline (unix timestamp) |

## Express.js Middleware (@x402/express)

The primary server-side integration. One line to paywall a route:

```javascript
import express from 'express';
import { paymentMiddleware } from '@x402/express';

const app = express();

app.use('/api/premium', paymentMiddleware({
  amount: '0.01',
  currency: 'USDC',
  network: 'base',
  recipient: '0xYourWalletAddress',
  facilitator: { url: 'https://x402.coinbase.com' },
  description: 'Premium API access',
}));

app.get('/api/premium/data', (req, res) => {
  res.json({ data: 'premium content' });
});
```

## Client-Side (@x402/client)

Auto-handles 402 responses:

```javascript
import { x402Client } from '@x402/client';

const client = x402Client({
  wallet: myWallet,
  facilitator: 'https://x402.coinbase.com',
});

// Automatically pays if 402 returned
const response = await client.fetch('https://api.example.com/premium/data');
```

## MCP Integration (@x402/mcp)

Paywall MCP tools with per-invocation pricing:

```javascript
import { createPaymentWrapper } from '@x402/mcp';

const paidTool = createPaymentWrapper({
  amount: '0.05',
  currency: 'USDC',
  network: 'base',
  recipient: '0xYourWallet',
  facilitator: 'https://x402.coinbase.com',
});

mcp.addTool({
  name: 'analyze_competitor',
  description: 'Deep competitor analysis (0.05 USDC)',
  handler: paidTool(async ({ url }) => {
    return await analyzeCompetitor(url);
  }),
});
```

## Pricing Tiers Pattern

```json
{
  "tiers": {
    "free": { "price": "0", "rate_limit": "100/hour" },
    "basic": { "price": "0.01", "rate_limit": "1000/hour" },
    "premium": { "price": "0.10", "rate_limit": "unlimited" }
  },
  "currency": "USDC",
  "network": "base"
}
```

## Why Base L2 + USDC

- **Low fees:** <$0.01 per transaction (vs $5-20 on Ethereum L1)
- **Fast:** 2-second block times
- **Stable:** USDC is 1:1 pegged to USD, no price volatility
- **Coinbase-backed:** Strong institutional trust
- **No chargebacks:** Blockchain finality
- **Micropayment-friendly:** $0.001+ transactions are economical

## x402 vs Traditional Payment

| Aspect | x402 | Stripe | PayPal |
|--------|------|--------|--------|
| Integration effort | 1 middleware line | Full checkout flow | SDK |
| Settlement | 2 seconds | 2-7 business days | 1-3 days |
| Fees | Gas (<$0.01) | 2.9% + $0.30 | 2.9% + $0.30 |
| Chargebacks | None | Yes | Yes |
| Micropayments | Yes ($0.001+) | No (min ~$0.50) | No |
| Agent-native | Yes | Partial (needs DPT) | Partial |

## Network Options

- **base** — Production (Coinbase L2, lowest fees)
- **base-sepolia** — Testnet (free test USDC)
- **ethereum** — Mainnet (high fees, not recommended for micropayments)

## Setup Checklist

1. Get a USDC wallet on Base (Coinbase Wallet, MetaMask, etc.)
2. Install `@x402/express` in your Node.js project
3. Add `paymentMiddleware` to routes you want to paywall
4. Set facilitator URL to `https://x402.coinbase.com`
5. Test with `base-sepolia` testnet first
6. Switch to `base` for production

## Common Issues

1. **Wrong network** — Ensure wallet and config use the same network
2. **Insufficient balance** — Agent wallet needs USDC + ETH for gas
3. **Facilitator down** — x402.coinbase.com is the primary facilitator
4. **CORS** — Add CORS headers if agents call from browser context
5. **Testnet vs mainnet** — Use base-sepolia for development
