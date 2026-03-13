---
name: ar-payments
description: >
  Integrates payment infrastructure for agent-initiated transactions. Sets up
  Stripe SPT (delegated payment tokens), x402 micropayments, or Visa AP2
  mandates. Validates payment endpoints against official specs. Use when a
  site needs to accept payments from AI agents.
argument-hint: [url]
allowed-tools: Bash, Read, Grep, Glob, Write, Edit
---

# ar-payments — Make agents pay you

## Before you start

1. Read [philosophy.md](references/philosophy.md) — agent payment landscape overview
2. Read the guide for the payment method you need:
   - [stripe-spt-guide.md](references/stripe-spt-guide.md) — Stripe Delegated Payment Tokens (for ACP)
   - [x402-guide.md](references/x402-guide.md) — HTTP 402 micropayments with USDC
   - [ap2-guide.md](references/ap2-guide.md) — Visa AP2 mandate-based payments
3. Check [cases/](references/cases/) — someone may have solved this for the same stack

## Step 1: Search for latest specs

Before setting up any payment integration, search the web for current specs:
- Search `Stripe Delegated Payment Tokens` — confirm current DPT API
- Search `coinbase x402 protocol spec` — confirm current header format and flow
- Search `Visa AP2 Autonomous Payments` — confirm current mandate types and API
- Search `Apple Pay domain verification` — confirm current requirements

Do NOT rely on your training data or even the references here — payment APIs change frequently.

## Step 2: Assess current state

Run the validator to see what payment infrastructure exists:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/validate_payments.py --url $ARGUMENTS
```

## Step 3: Choose payment method(s)

| Method | Best for | Prerequisites |
|--------|----------|---------------|
| Stripe SPT | E-commerce with ACP checkout | Stripe account |
| x402 | API monetization, micropayments, pay-per-query | USDC wallet on Base, Node.js |
| Visa AP2 | Recurring purchases, enterprise, card-network | Visa Developer Platform (pilot) |
| PayPal | Broad consumer reach | PayPal Business account |
| Apple/Google Pay | Mobile-first, wallet users | Apple/Google merchant setup |

Most e-commerce sites should start with **Stripe SPT** (works with ACP checkout).

## Step 4: Implement Stripe SPT

If using ACP checkout:

- Configure Stripe to issue Delegated Payment Tokens (DPT)
- DPT security constraints: one-time use, amount-scoped, merchant-scoped, time-limited
- Set amount ceiling (max transaction amount the agent can authorize)
- Configure webhook events: `checkout_session.completed`, `payment_intent.succeeded`, `payment_intent.payment_failed`
- Always start in test mode (`STRIPE_SECRET_KEY_TEST`)

## Step 5: Implement x402 (if applicable)

For API/content monetization:

- Install `@x402/express` middleware on your Node.js server
- Configure pricing per endpoint (e.g., `/api/data` = $0.01 per request)
- Server responds with HTTP 402 + payment headers when payment required
- Agent's x402 client handles USDC payment automatically
- For MCP servers: use `createPaymentWrapper()` to wrap tools with per-call pricing

## Step 6: Set up Apple Pay / Google Pay (if applicable)

- Apple Pay: upload domain verification file to `/.well-known/apple-developer-merchantid-domain-association`
- Google Pay: add `pay.google.com` script and configure payment data request
- Both add wallet-based payment as an option alongside card payments

## Step 7: Validate

Re-run the validator:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/validate_payments.py --url $ARGUMENTS
```

- Exit code 0 = payment infrastructure detected → done
- Exit code 1 = issues found → fix and re-validate
- Repeat until all checks pass

## Step 8: Write back

Add a case to `references/cases/` using [_template.md](references/cases/_template.md). Especially:

- Stripe test mode vs live mode gotchas
- x402 pricing strategy that worked
- Apple Pay domain verification issues

## References

- [philosophy.md](references/philosophy.md) — payment landscape overview
- [stripe-spt-guide.md](references/stripe-spt-guide.md) — DPT flow, integration, security
- [x402-guide.md](references/x402-guide.md) — HTTP 402 flow, USDC, middleware setup
- [ap2-guide.md](references/ap2-guide.md) — Visa mandates, certification
- [cases/](references/cases/) — real-world payment integration cases
