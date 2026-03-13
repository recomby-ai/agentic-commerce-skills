# Supporting Both ACP and UCP

## Why Dual Protocol

ACP captures OpenAI ecosystem traffic (ChatGPT Shopping, GPT agents).
UCP captures Google ecosystem traffic (AI Mode, Shopify integrations).
Together they cover the two largest agent commerce platforms.

## Architecture

```
                    /.well-known/ucp (UCP manifest)
                         |
Agent discovers ─────────┤
                         |
                    /acp/v1/* (ACP endpoints)

UCP Flow:                              ACP Flow:
  Agent reads manifest                   Agent creates checkout session
  Agent calls capability endpoint        Agent updates with items/address
  Agent handles payment per handler      Agent completes with DPT
```

## Shared Backend Pattern

Both protocols can share the same product catalog and order system:

```
UCP capability endpoints ──┐
                           ├──► Shared Product Service ──► Shared Order Service
ACP checkout endpoints ────┘
```

### Shared Components
- Product catalog / inventory
- Order management system
- Customer database
- Webhook/notification system

### Protocol-Specific Components
- ACP: Checkout session state machine, DPT handling, HMAC signing
- UCP: Manifest generation, capability routing, JWK signing

## UCP Manifest Pointing to ACP

UCP's payment_handler can reference your ACP endpoint, creating a bridge:

```json
{
  "payment_handler": {
    "type": "stripe",
    "agent_payment": {
      "enabled": true,
      "delegated_token_supported": true,
      "acp_endpoint": "https://api.example.com/acp/v1"
    }
  }
}
```

This tells UCP-aware agents: "You can also use ACP for checkout."

## Implementation Order

### Option A: ACP First (recommended if using Stripe)
1. Implement 5 ACP endpoints
2. Test with Stripe test keys
3. Generate UCP manifest pointing to same products
4. Add `acp_endpoint` in UCP payment_handler
5. Deploy `/.well-known/ucp`

### Option B: UCP First (recommended if using Shopify)
1. Generate UCP manifest with capabilities
2. Build REST endpoints for each capability
3. Add ACP endpoints wrapping same product/order logic
4. Configure Stripe for DPT support

## URL Structure Recommendation

```
https://api.example.com/
  acp/v1/checkout_sessions          # ACP endpoints
  acp/v1/checkout_sessions/{id}
  acp/v1/checkout_sessions/{id}/complete
  acp/v1/checkout_sessions/{id}/cancel
  ucp/products/search               # UCP capability endpoints
  ucp/products/{id}
  ucp/cart
  ucp/checkout
```

Host `/.well-known/ucp` on your main domain (not the API subdomain).

## Testing Both Protocols

```bash
# Generate and validate ACP config
python scripts/generate_acp_manifest.py --merchant-name "Store" --base-url "https://api.example.com/acp" --output acp.json
python scripts/validate_commerce.py --type acp --file acp.json

# Generate and validate UCP manifest
python scripts/generate_ucp_manifest.py --merchant-name "Store" --merchant-url "https://example.com" --output ucp.json
python scripts/validate_commerce.py --type ucp --file ucp.json
```

## Common Pitfalls

1. **Different product IDs** — Use the same product IDs in both protocols
2. **Inconsistent pricing** — Both protocols must reflect the same prices
3. **Separate inventory** — Both must check the same inventory source
4. **Missing CORS** — UCP endpoints need CORS headers for browser-based agents
5. **Version drift** — Keep both protocol implementations in sync when updating products
