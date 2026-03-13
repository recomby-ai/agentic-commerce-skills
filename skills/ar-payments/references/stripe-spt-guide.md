# Stripe SPT (Stripe Payment Tokens) Guide

## Overview

Stripe Payment Tokens (SPT), also called Delegated Payment Tokens (DPT),
allow agents to pay on behalf of users without handling card details. The
token is scoped to a specific merchant, amount ceiling, and time window.

## How DPT Works

### 4-Step Flow

```
User                 Agent                Stripe               Merchant
  |                    |                    |                    |
  |-- Link card ------>|                    |                    |
  |                    |-- Request DPT ---->|                    |
  |                    |                    |-- Issue token ---->|
  |                    |<--- dpt_xyz789 ----|                    |
  |                    |                    |                    |
  |                    |--- /complete ------|-------------------->|
  |                    |    (with DPT)      |                    |
  |                    |                    |<-- Process payment |
  |                    |<--- Order confirmed -------------------|
```

### Step 1: User Authorizes Agent

User links payment method to agent platform (e.g., adds card to ChatGPT).
This creates a Stripe Customer with a saved PaymentMethod.

### Step 2: Agent Requests DPT

```json
POST /v1/delegated_payment_tokens
{
  "customer": "cus_abc123",
  "scope": {
    "merchant": "acct_merchant123",
    "amount_max": 20000,
    "currency": "usd",
    "expires_in": 3600
  }
}
```

### Step 3: Stripe Issues DPT

```json
{
  "id": "dpt_live_xyz789",
  "object": "delegated_payment_token",
  "scope": {
    "merchant": "acct_merchant123",
    "amount_max": 20000,
    "currency": "usd"
  },
  "expires_at": 1706648400,
  "livemode": true
}
```

### Step 4: Agent Presents DPT to Merchant

Included in the ACP `/complete` request:
```json
{
  "payment_details": {
    "type": "delegated_payment_token",
    "token": "dpt_live_xyz789",
    "provider": "stripe"
  }
}
```

## DPT Security Properties

- **One-time use** — Invalidated after successful payment
- **Amount-scoped** — Cannot charge more than `amount_max`
- **Merchant-scoped** — Only the specified merchant can process
- **Time-limited** — Expires after `expires_in` seconds
- **No card details** — Agent never sees card numbers

## Stripe Integration Steps

### 1. Stripe Account Setup

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login and get API keys
stripe login
stripe config --list
```

### 2. Enable Agent Commerce

In Stripe Dashboard:
- Settings > Agent Commerce > Enable
- Configure allowed agent platforms
- Set default amount ceiling

### 3. Server-Side Configuration

Required environment variables:
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_CONNECT_ACCOUNT=acct_...  # If using Connect
```

### 4. Webhook Setup

Listen for these events:
- `checkout_session.completed` — Order confirmed
- `payment_intent.succeeded` — Payment captured
- `payment_intent.payment_failed` — Payment failed
- `charge.dispute.created` — Dispute filed

### 5. Test Mode

Always start with test keys:
- `sk_test_` for server-side
- `pk_test_` for client-side (if applicable)
- Use Stripe test card numbers (4242424242424242)

## Amount Ceiling Pattern

Safety limit to prevent runaway agent spending:

```python
AMOUNT_CEILING = Decimal(os.getenv("CHECKOUT_AMOUNT_CEILING", "500.00"))

# In /complete handler:
if total > AMOUNT_CEILING:
    raise HTTPException(422, detail={
        "error": {
            "code": "amount_ceiling_exceeded",
            "message": f"Total ${total} exceeds ceiling ${AMOUNT_CEILING}. "
                       "Requires human approval."
        }
    })
```

## Stripe Agent Toolkit

Stripe provides an official SDK for agent commerce:
- Repo: https://github.com/stripe/stripe-agent-toolkit (1.3k stars)
- Supports: MCP server, LangChain, CrewAI integrations
- Features: Create payment links, manage customers, process refunds

## Fee Structure

| Component | Fee |
|-----------|-----|
| Stripe processing | 2.9% + $0.30 |
| ACP protocol fee | 4% |
| **Total per transaction** | **~6.9% + $0.30** |

For a $100 purchase: $6.90 + $0.30 = $7.20 in fees.

## Common Issues

1. **DPT expired** — Tokens have short TTL. Request a new one close to checkout.
2. **Amount mismatch** — Token `amount_max` must be >= session total.
3. **Wrong merchant** — DPT is merchant-scoped. Verify Stripe account ID.
4. **Test vs live** — `sk_test_` keys create test DPTs. Don't mix modes.
5. **Idempotency** — Always send `Idempotency-Key` on POST requests.
