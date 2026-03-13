# UCP (Universal Commerce Protocol) Implementation Guide

Authors: Google + Shopify
Status: Early specification (2025-06), Shopify production integration live

## Overview

UCP is an open commerce protocol that allows AI agents to discover and transact
with merchants using existing web infrastructure. Unlike ACP, UCP works with any
payment provider and exposes capabilities through a well-known manifest.

## /.well-known/ucp Manifest

Every UCP-enabled site hosts a JSON manifest at `/.well-known/ucp`.

### Core Structure

```json
{
  "ucp_version": "0.1.0",
  "merchant": {
    "name": "Your Store",
    "description": "What you sell",
    "url": "https://yourstore.com",
    "logo": "https://yourstore.com/logo.png",
    "support_email": "support@yourstore.com",
    "legal": {
      "terms_of_service": "https://yourstore.com/tos",
      "privacy_policy": "https://yourstore.com/privacy",
      "refund_policy": "https://yourstore.com/refunds"
    }
  },
  "capabilities": [...],
  "schemas": {...},
  "payment_handler": {...},
  "signing_keys": [...],
  "rate_limits": { "requests_per_minute": 60, "requests_per_day": 10000 }
}
```

## Capability Naming Convention

Reverse-domain notation: `dev.ucp.{domain}.{resource}.{action}`

### Standard Capabilities

| Capability | Description |
|-----------|-------------|
| dev.ucp.shopping.product.search | Search product catalog |
| dev.ucp.shopping.product.details | Get product details |
| dev.ucp.shopping.product.compare | Compare multiple products |
| dev.ucp.shopping.cart.create | Create shopping cart |
| dev.ucp.shopping.cart.update | Update cart items |
| dev.ucp.shopping.checkout | Initiate checkout |
| dev.ucp.shopping.order.status | Check order status |
| dev.ucp.shopping.order.cancel | Cancel an order |
| dev.ucp.shopping.returns.initiate | Start a return |

### Custom Capabilities

Use your own domain prefix:
```
com.yourcompany.service.action
```

## 3 Transport Options

### 1. REST Transport (simplest)
```json
{
  "name": "dev.ucp.shopping.product.search",
  "transport": "rest",
  "endpoint": "https://api.example.com/ucp/products/search",
  "method": "GET",
  "parameters": [
    {"name": "query", "type": "string", "required": true},
    {"name": "limit", "type": "integer", "required": false, "default": 10}
  ]
}
```

### 2. MCP Transport (AI-native)
```json
{
  "name": "dev.ucp.shopping.product.search",
  "transport": "mcp",
  "server_url": "https://mcp.example.com/sse",
  "tool_name": "search_products",
  "transport_type": "streamable_http"
}
```

### 3. A2A Transport (multi-agent)
```json
{
  "name": "dev.ucp.shopping.checkout",
  "transport": "a2a",
  "agent_card_url": "https://example.com/.well-known/agent.json",
  "skill_id": "checkout_agent"
}
```

## Payment Handler Configuration

### Stripe Handler
```json
{
  "payment_handler": {
    "type": "stripe",
    "publishable_key": "pk_live_...",
    "supported_methods": ["card", "google_pay", "apple_pay"],
    "supported_currencies": ["usd", "eur", "gbp"],
    "agent_payment": {
      "enabled": true,
      "delegated_token_supported": true,
      "acp_endpoint": "https://api.example.com/acp/v1"
    }
  }
}
```

### Google Pay Handler
```json
{
  "payment_handler": {
    "type": "google_pay",
    "merchant_id": "BCR2DN4T...",
    "supported_methods": ["google_pay"],
    "agent_payment": { "enabled": true, "ai_mode_integrated": true }
  }
}
```

### Custom Handler
```json
{
  "payment_handler": {
    "type": "custom",
    "checkout_url": "https://example.com/checkout",
    "api_endpoint": "https://api.example.com/payments",
    "documentation": "https://docs.example.com/payments"
  }
}
```

## Signing Keys (EC P-256)

UCP manifests can be signed to prevent tampering using JWK format:
```json
{
  "kid": "key-2026-01",
  "kty": "EC",
  "crv": "P-256",
  "x": "base64url-x-coordinate",
  "y": "base64url-y-coordinate",
  "use": "sig",
  "alg": "ES256"
}
```

Agents verify integrity by checking the `Signature` header on capability
responses using ES256.

## Google AI Mode Integration

1. Googlebot crawls `/.well-known/ucp` during regular crawl cycle
2. AI Mode indexes capabilities and product data
3. User asks to buy something -> AI Mode searches indexed UCP merchants
4. Calls `dev.ucp.shopping.product.search` capability
5. On confirmation, calls `dev.ucp.shopping.checkout`
6. Handles payment via Google Pay

### Shopify Auto-Integration

All Shopify stores get UCP manifest automatically:
- Product catalog exposed via `dev.ucp.shopping.*` capabilities
- Payment via Shopify Payments (Stripe-backed)
- No merchant configuration required

## UCP vs ACP Comparison

| Feature | UCP | ACP |
|---------|-----|-----|
| Discovery | /.well-known/ucp (crawlable) | API registration |
| Fee | None | 4% |
| Payment | Any provider | Stripe only |
| Transport | REST, MCP, A2A | REST only |
| State | Stateless capabilities | Stateful sessions |
| Signing | EC P-256 JWK | HMAC SHA256 |
| Best for | Open ecosystem | Stripe-integrated merchants |

## Implementation Checklist

1. Define your capabilities (what can agents do on your site?)
2. Choose transport(s) — REST is simplest to start
3. Build API endpoints for each capability
4. Configure payment handler
5. Generate and host `/.well-known/ucp` manifest
6. Validate with `validate_commerce.py`
7. Submit to Google Merchant Center for AI Mode indexing
