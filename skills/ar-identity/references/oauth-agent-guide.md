# OAuth 2.0 Extensions for AI Agents

A practical guide to implementing OAuth 2.0 for AI agent authentication.
Covers client credentials flow, token scoping, agent metadata, and the
emerging IETF standards for agent-specific authorization.

---

## Why OAuth for Agents?

AI agents need authentication that is:
- **Non-interactive** — no browser, no human in the loop
- **Scoped** — different agents get different permissions
- **Rotatable** — credentials expire and refresh automatically
- **Auditable** — every token issuance is logged
- **Standard** — works with existing auth infrastructure

OAuth 2.0 (and its successor OAuth 2.1) meets all five requirements.

---

## Flow 1: Client Credentials (Service-to-Service)

The primary flow for agent authentication. The agent authenticates as itself,
not on behalf of a user.

### When to Use

- Agent browses your product catalog
- Agent checks inventory or pricing
- Agent queries your MCP server tools
- Any read-only or service-level operation

### How It Works

```
┌──────────┐                          ┌──────────────┐
│  AI Agent │                          │  Auth Server  │
└─────┬────┘                          └──────┬───────┘
      │                                       │
      │  POST /oauth/token                    │
      │  grant_type=client_credentials        │
      │  client_id=agent_xyz                  │
      │  client_secret=s3cr3t                 │
      │  scope=catalog:read                   │
      │──────────────────────────────────────►│
      │                                       │
      │  200 OK                               │
      │  { access_token: "eyJ...",            │
      │    token_type: "Bearer",              │
      │    expires_in: 3600,                  │
      │    scope: "catalog:read" }            │
      │◄──────────────────────────────────────│
      │                                       │
      │  GET /api/products                    │
      │  Authorization: Bearer eyJ...         │
      │──────────────────────────────────────►│
      │                                       │
```

### Implementation

**Token request:**

```http
POST /oauth/token HTTP/1.1
Host: auth.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=agent_shopbot_v2
&client_secret=whsec_abc123def456
&scope=catalog:read orders:read
```

**Token response:**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "catalog:read orders:read"
}
```

### Best Practices

1. **Short-lived tokens** — 15 to 60 minutes. Agents can re-authenticate.
2. **Scope down** — Request only the scopes needed for the current operation.
3. **Client authentication** — Use `client_secret_post` or `client_secret_basic`.
   For high-security: use `private_key_jwt` (mTLS).
4. **Rate limit per client_id** — Not per IP. Agents may share infrastructure.

---

## Flow 2: Authorization Code + PKCE (User-Delegated)

When an agent acts on behalf of a specific user (e.g., placing an order using
the user's account).

### When to Use

- Agent places an order for a user
- Agent accesses user's order history
- Agent manages user's subscription
- Any operation requiring user consent

### How It Works

```
┌──────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐
│ User │     │  AI Agent │     │  Auth Server  │     │   API    │
└──┬───┘     └─────┬────┘     └──────┬───────┘     └────┬─────┘
   │               │                  │                   │
   │  "Buy this"   │                  │                   │
   │──────────────►│                  │                   │
   │               │                  │                   │
   │  Auth URL     │  /authorize?     │                   │
   │◄──────────────│  client_id=...   │                   │
   │               │  code_challenge  │                   │
   │  Login+Consent│                  │                   │
   │──────────────────────────────────►│                   │
   │               │                  │                   │
   │  Redirect     │  code=abc123     │                   │
   │──────────────►│                  │                   │
   │               │                  │                   │
   │               │  POST /token     │                   │
   │               │  code=abc123     │                   │
   │               │  code_verifier   │                   │
   │               │─────────────────►│                   │
   │               │                  │                   │
   │               │  access_token    │                   │
   │               │◄─────────────────│                   │
   │               │                  │                   │
   │               │  POST /orders    │                   │
   │               │  Bearer token    │                   │
   │               │──────────────────────────────────────►│
```

### Key Differences for Agents

- **PKCE is mandatory** — Agents may not have secure storage for secrets
- **Narrow scopes** — `orders:create` not `admin:all`
- **Token binding** — Bind tokens to the specific agent instance
- **Consent screen** — Must clearly show agent name, operator, and requested permissions

---

## Flow 3: On-Behalf-Of (IETF Draft)

Emerging standard for multi-hop agent delegation. Agent A calls Agent B,
which calls your API — all traced back to the original user.

### IETF Draft: draft-oauth-ai-agents-on-behalf-of-user

Introduces two new parameters:

| Parameter | Where | Purpose |
|-----------|-------|---------|
| `requested_actor` | Authorization request | Identifies the agent needing delegation |
| `actor_token` | Token request | Authenticates the agent in the delegation chain |

### Token Exchange Flow

```http
POST /oauth/token HTTP/1.1
Host: auth.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:token-exchange
&subject_token=eyJ...user_token...
&subject_token_type=urn:ietf:params:oauth:token-type:access_token
&actor_token=eyJ...agent_token...
&actor_token_type=urn:ietf:params:oauth:token-type:access_token
&scope=orders:create
```

The resulting token carries both the user's identity and the agent's identity,
enabling full audit trails.

### Status

This is an active IETF draft (draft-oauth-ai-agents-on-behalf-of-user-02).
Not yet a standard. Implement if you need multi-agent delegation chains.
Otherwise, client credentials + authorization code cover most use cases.

---

## Agent Metadata in OAuth Registration

When agents register for OAuth credentials, require structured metadata:

### Dynamic Client Registration (RFC 7591)

```json
{
  "client_name": "ShopBot v2.1",
  "client_uri": "https://shopbot.example.com",
  "grant_types": ["client_credentials"],
  "scope": "catalog:read orders:read",
  "token_endpoint_auth_method": "client_secret_post",
  "contacts": ["ops@shopbot.example.com"],

  "agent_metadata": {
    "agent_version": "2.1.0",
    "operator": "ShopBot Inc.",
    "agent_type": "shopping_assistant",
    "capabilities": ["product_search", "price_comparison"],
    "a2a_agent_card": "https://shopbot.example.com/.well-known/agent.json"
  }
}
```

The `agent_metadata` field is not part of the OAuth spec but is a recommended
extension for agent-aware auth servers. It enables:
- Agent-specific rate limits based on `agent_type`
- Capability-based scope validation
- Linking OAuth clients to A2A agent cards

---

## Scope Design for Agent Commerce

### Recommended Scope Hierarchy

```
catalog:read          Read products, prices, categories
catalog:search        Search and filter products
orders:create         Place new orders
orders:read           View order status
orders:cancel         Cancel pending orders
payments:initiate     Start a payment flow
payments:status       Check payment status
inventory:read        Check stock levels
profile:read          Read merchant profile
```

### Scope Mapping to Agent Use Cases

| Agent Use Case | Required Scopes |
|----------------|----------------|
| Price comparison | `catalog:read catalog:search` |
| Shopping assistant | `catalog:read orders:create payments:initiate` |
| Inventory monitor | `catalog:read inventory:read` |
| Order management | `orders:read orders:cancel` |
| Full commerce | `catalog:read orders:create payments:initiate orders:read` |

### Anti-Patterns

- **`admin:all`** — Never grant admin scope to agents
- **`*` wildcard** — Never allow unlimited scope
- **No expiration** — Always set `expires_in` on tokens
- **Scope creep** — Agents should request minimum needed scopes per operation

---

## CORS Configuration for Agent Access

Agents calling your OAuth endpoints from various environments need proper CORS:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: POST, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 86400
```

For the token endpoint specifically:
- Allow `POST` and `OPTIONS`
- Allow `Content-Type: application/x-www-form-urlencoded`
- Allow `Authorization` header (for client_secret_basic)

If your auth server blocks CORS on the token endpoint, server-side agents will
work fine but browser-based agents will fail.

---

## Validating Agent Identity

### Token Introspection (RFC 7662)

Your API server can validate agent tokens:

```http
POST /oauth/introspect HTTP/1.1
Host: auth.example.com
Content-Type: application/x-www-form-urlencoded

token=eyJ...access_token...
```

Response:

```json
{
  "active": true,
  "client_id": "agent_shopbot_v2",
  "scope": "catalog:read",
  "exp": 1711234567,
  "iss": "https://auth.example.com",
  "agent_metadata": {
    "agent_type": "shopping_assistant",
    "operator": "ShopBot Inc."
  }
}
```

### JWT Validation (Local)

If tokens are JWTs, validate locally:
1. Verify signature against auth server's JWKS
2. Check `exp` (expiration) and `iat` (issued at)
3. Verify `iss` (issuer) matches your auth server
4. Check `scope` includes required permissions
5. Optionally check `azp` (authorized party) for client identity

---

## Implementation Checklist

- [ ] Deploy OAuth token endpoint (or use hosted: Auth0, Stytch, Keycloak)
- [ ] Define agent-specific scopes
- [ ] Create agent registration flow (dynamic or manual)
- [ ] Require agent metadata during registration
- [ ] Set token expiration to 15-60 minutes
- [ ] Enable token introspection endpoint
- [ ] Configure CORS on token endpoint
- [ ] Deploy `.well-known/agent.json` linking to OAuth config
- [ ] Test with `validate_identity.py` from this skill
- [ ] Monitor agent token usage and set rate limits per client_id

---

## References

- RFC 6749: OAuth 2.0 Authorization Framework
- RFC 7591: OAuth 2.0 Dynamic Client Registration
- RFC 7662: OAuth 2.0 Token Introspection
- IETF Draft: OAuth 2.0 Extension for AI Agent On-Behalf-Of User Authorization
- IETF Draft: AI Agent Authentication and Authorization (draft-klrc-aiagent-auth)
- A2A Protocol: Agent Discovery and Agent Cards
- MCP Specification: OAuth 2.1 Integration
