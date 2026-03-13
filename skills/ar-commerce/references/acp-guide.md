# ACP (Agent Commerce Protocol) Implementation Guide

Authors: OpenAI + Stripe
Spec version: 2026-01-30
Status: Production (live in ChatGPT Shopping)

## Overview

ACP defines a REST protocol for agent-initiated commerce. An agent discovers
a merchant's ACP endpoint, creates a checkout session, adds items, and completes
payment using a Delegated Payment Token (DPT) issued by Stripe.

## 5 REST Endpoints

All endpoints operate on the `checkout_sessions` resource.

### 1. POST /v1/checkout_sessions — Create Session

Creates a new checkout session for an agent-initiated purchase.

```json
{
  "client_reference_id": "agent-session-abc123",
  "currency": "usd",
  "line_items": [
    {
      "price_data": {
        "currency": "usd",
        "product_data": {
          "name": "Wireless Headphones Pro",
          "description": "Noise-cancelling, 40hr battery",
          "images": ["https://example.com/headphones.jpg"],
          "metadata": { "sku": "WHP-001" }
        },
        "unit_amount": 14999
      },
      "quantity": 1
    }
  ],
  "shipping_options": [
    {
      "shipping_rate_data": {
        "display_name": "Standard Shipping",
        "type": "fixed_amount",
        "fixed_amount": { "amount": 599, "currency": "usd" },
        "delivery_estimate": {
          "minimum": {"unit": "business_day", "value": 3},
          "maximum": {"unit": "business_day", "value": 5}
        }
      }
    }
  ]
}
```

### 2. GET /v1/checkout_sessions/{id} — Retrieve Session

Returns current session state including status, amounts, customer details.

### 3. POST /v1/checkout_sessions/{id} — Update Session

Updates session with customer details, shipping selection, or additional items.

### 4. POST /v1/checkout_sessions/{id}/complete — Complete Session

Completes checkout with payment via Delegated Payment Token:
```json
{
  "payment_details": {
    "type": "delegated_payment_token",
    "token": "dpt_live_xyz789",
    "provider": "stripe"
  }
}
```

### 5. POST /v1/checkout_sessions/{id}/cancel — Cancel Session

Cancels an incomplete session. Accepts optional `reason` field.

## State Machine

```
incomplete -> not_ready_for_payment -> ready_for_payment -> completed
                                                         -> canceled
```

| From | To | Trigger |
|------|----|---------|
| (none) | incomplete | POST create |
| incomplete | not_ready_for_payment | Update with partial data |
| incomplete | ready_for_payment | Update with complete data |
| not_ready_for_payment | ready_for_payment | Update remaining fields |
| ready_for_payment | completed | POST /complete |
| any (non-terminal) | canceled | POST /cancel |

## Delegated Payment Token (DPT) Flow

DPT is how agents pay on behalf of users without handling card details.

### 4-Step Flow

1. **User authorizes agent** — Links payment method to agent platform
2. **Agent requests DPT** — Scoped, one-time token from Stripe:
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
3. **Stripe issues DPT** — One-time, amount-scoped, merchant-scoped token
4. **Agent presents DPT to merchant** — In the /complete request

### DPT Security Properties

- One-time use (invalidated after payment)
- Amount-scoped (cannot exceed `amount_max`)
- Merchant-scoped (only specified merchant can process)
- Time-limited (expires after `expires_in` seconds)
- No card details exposed to agent

## Required Headers

| Header | Purpose |
|--------|---------|
| Authorization | Bearer token for API authentication |
| Idempotency-Key | Prevents duplicate operations (24h validity) |
| ACP-Version | API version (e.g., "2026-01-30") |
| Content-Type | application/json |

## HMAC SHA256 Webhook Signatures

Merchants sign webhook payloads:
```
ACP-Signature: t=1706644800,v1=5257a869e7ecebeda32affa62cdca3fa51c...
```

Verification:
```python
import hmac, hashlib

def verify_acp_signature(payload: bytes, header: str, secret: str) -> bool:
    parts = dict(p.split("=", 1) for p in header.split(","))
    signed_payload = f"{parts['t']}.{payload.decode()}"
    expected = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(parts["v1"], expected)
```

## Error Responses

| HTTP Status | Error Code | Meaning |
|------------|------------|---------|
| 400 | invalid_request_error | Missing or invalid parameters |
| 401 | authentication_error | Invalid API key |
| 402 | payment_error | Payment failed |
| 404 | not_found | Session does not exist |
| 409 | state_conflict | Invalid state transition |
| 429 | rate_limit_error | Too many requests |

## Stripe Integration Checklist

1. Create Stripe account and get API keys
2. Enable ACP in Stripe Dashboard (Settings > Agent Commerce)
3. Configure webhook endpoint for order notifications
4. Set up DPT support (requires Stripe Connect for multi-merchant)
5. Test with `sk_test_` keys before going live
6. Set amount ceiling for agent purchases (safety limit)

## Fee Structure

- Stripe processing: 2.9% + $0.30 per transaction
- ACP protocol fee: 4% (paid to OpenAI/Stripe infrastructure)
- Total: ~6.9% + $0.30 per agent transaction
