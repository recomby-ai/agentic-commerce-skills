# Visa AP2 (Agent Payment Protocol v2) Guide

Author: Visa
Status: Pilot program (2025-Q4), expanding 2026
Partners: Worldpay, Adyen, Stripe, major banks

## Overview

AP2 is Visa's protocol for authorizing agents to make payments on behalf of
cardholders. It introduces "mandates" — pre-defined rules that govern what
an agent can spend, when, and with whom. Unlike DPT (one-time tokens),
mandates are persistent authorization grants.

## 3 Mandate Types

### 1. Pre-authorized Mandate (Recurring)

Agent can make regular payments within defined limits.

**Use case:** Subscription management, recurring purchases, auto-reorder.

```json
{
  "mandate_type": "pre_authorized",
  "mandate_id": "mdt_recurring_001",
  "cardholder_id": "ch_abc123",
  "agent_id": "agent_shopping_bot",
  "authorization": {
    "max_amount_per_transaction": 5000,
    "max_amount_per_period": 50000,
    "period": "monthly",
    "currency": "usd",
    "allowed_mccs": ["5411", "5412", "5499"],
    "start_date": "2026-01-01",
    "end_date": "2026-12-31"
  },
  "notification": {
    "notify_on": ["transaction_completed", "limit_approaching"],
    "channel": "push",
    "threshold_percent": 80
  }
}
```

### 2. Conditional Mandate (Rule-based)

Agent can pay only when specific conditions are met.

**Use case:** Price-triggered buying, deal sniping, restocking.

```json
{
  "mandate_type": "conditional",
  "mandate_id": "mdt_conditional_001",
  "conditions": [
    {
      "type": "price_threshold",
      "product_category": "electronics",
      "max_price": 30000,
      "comparison": "less_than_or_equal"
    },
    {
      "type": "time_window",
      "allowed_hours": {"start": 9, "end": 21},
      "timezone": "America/New_York"
    }
  ],
  "authorization": {
    "max_amount_per_transaction": 30000,
    "max_transactions_per_day": 3,
    "require_confirmation_above": 15000
  }
}
```

Conditions are evaluated by Visa's authorization network, not by the agent.

### 3. Delegated Mandate (One-time)

Agent authorized for a single transaction with specific parameters.

**Use case:** Agent-assisted purchase ("buy this for me").

```json
{
  "mandate_type": "delegated",
  "mandate_id": "mdt_delegated_001",
  "authorization": {
    "max_amount": 15598,
    "currency": "usd",
    "merchant_id": "merch_store",
    "expires_at": "2026-02-01T12:00:00Z"
  },
  "requires_cardholder_confirmation": true,
  "confirmation_method": "push_notification"
}
```

## VDC (Visa Direct Commerce)

VDC is the payment rail that AP2 mandates authorize.

```
Agent -> Agent Platform -> Visa AP2 -> Issuer -> Cardholder Confirmation
                              |
                         VDC Payment Rail
                              |
                         Acquirer -> Merchant
```

### VDC vs Traditional Card Authorization

| Aspect | VDC | Traditional |
|--------|-----|------------|
| Direction | Push (to merchant) | Pull (from cardholder) |
| Speed | Real-time | 1-3 days settlement |
| Authorization | Mandate-based | Per-transaction |
| Disputes | Agent dispute category | Standard chargeback |

## W3C PaymentRequest Integration

AP2 extends the W3C PaymentRequest API for agent-initiated payments:

```javascript
const request = new PaymentRequest(
  [{
    supportedMethods: 'https://pay.visa.com/ap2',
    data: {
      mandate_id: 'mdt_delegated_001',
      agent_id: 'agent_shopping_assistant',
      mandate_type: 'delegated'
    }
  }],
  {
    total: {
      label: 'Purchase',
      amount: { currency: 'USD', value: '155.98' }
    }
  }
);

// May complete without user interaction if mandate allows
const response = await request.show();
```

## Agent Card Payment Extension

AP2 adds payment capabilities to A2A agent cards:

```json
{
  "payment_capabilities": {
    "ap2": {
      "supported_mandate_types": ["pre_authorized", "conditional", "delegated"],
      "supported_networks": ["visa", "mastercard"],
      "supported_currencies": ["usd", "eur", "gbp"],
      "certification_id": "ap2_cert_abc123"
    }
  }
}
```

## Agent Certification

Visa requires agent certification before using AP2:
1. **Registration** — Register with Visa Developer Platform
2. **Testing** — Pass automated test suite
3. **Security review** — Key management and data handling review
4. **Certification** — Receive `certification_id` (valid 1 year)
5. **Monitoring** — Visa monitors transaction patterns

## Implementation for Merchants

1. **Accept VDC payments** — Work with acquirer to enable Visa Direct Commerce
2. **Publish agent card** — Add `payment_capabilities` to A2A agent card
3. **Implement mandate validation** — Verify mandate parameters per transaction
4. **Handle agent metadata** — Store agent_id and mandate_id with orders
5. **Set up reporting** — Track agent-sourced revenue separately

## Implementation for Agents

1. **Get certified** — Register and certify with Visa
2. **Support mandates** — Build UI for cardholder mandate creation
3. **Handle confirmations** — Implement confirmation flows
4. **Report transactions** — Include mandate metadata in all requests

## Current Status and Timeline

- **2025-Q4:** Pilot program with select partners
- **2026-H1:** Expanding to more merchants and agent platforms
- **2026-H2:** Expected general availability
- **Requirement:** Acquirer support (Worldpay, Adyen, Stripe participating)

## AP2 vs Stripe SPT

| Feature | AP2 | Stripe SPT |
|---------|-----|-----------|
| Authorization model | Persistent mandates | One-time tokens |
| Network | Visa (any acquirer) | Stripe only |
| Recurring support | Native (pre-authorized) | Must request new DPT |
| Certification | Required | Not required |
| Maturity | Pilot | Production |
| Best for | Enterprise, recurring | E-commerce checkout |
