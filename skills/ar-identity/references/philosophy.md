# Why Agent Identity Matters

Agent identity is the foundation of trust in agent-to-service interactions.
Without it, every agent is anonymous, every request is untrusted, and every
transaction is a liability.

---

## The Anonymous Agent Problem

Today, most AI agents interact with websites the same way a random visitor does:
no credentials, no identity, no accountability. This creates three problems:

### 1. No Trust Signal

When an agent requests your API, you have no way to know:
- Is this a legitimate shopping agent or a scraper?
- Is this agent authorized by the user it claims to represent?
- Can I trust this agent to handle sensitive data (prices, inventory, PII)?

Without identity, your only option is to treat every agent as untrusted. That
means rate limiting, CAPTCHAs, and restricted access — the exact opposite of
what agent commerce needs.

### 2. No Attribution

If an agent places an order, who is responsible? If it returns a product, who
pays the shipping? If it negotiates a price, whose authority does it carry?

Attribution requires identity. Identity requires a verifiable credential that
links an agent to its operator, its user, and its permissions.

### 3. No Access Control

Without identity, you cannot offer tiered access:
- Public agents: read-only catalog access
- Verified agents: can place orders with user authorization
- Trusted partners: can access wholesale pricing, bulk operations

Access control is impossible without knowing who is asking.

---

## The Identity Stack

Agent identity has three layers. Each builds on the previous one.

### Layer 1: Discovery Identity

Machine-readable files that declare who you are:

| File | Purpose | Standard |
|------|---------|----------|
| `/.well-known/agent.json` | A2A agent card — name, capabilities, endpoint | A2A Protocol |
| `/llms.txt` | Human+LLM readable site summary | llms.txt proposal |
| `/agents.json` | Workflow contracts for agent API usage | agents-json spec |

This layer answers: "Who is this service and what does it offer?"

### Layer 2: Authentication Identity

OAuth 2.0 credentials that prove who the agent is:

| Flow | When to use | Trust level |
|------|-------------|-------------|
| Client Credentials | Agent acts as itself (service-to-service) | Service identity |
| Authorization Code + PKCE | Agent acts on behalf of a user | Delegated user identity |
| On-Behalf-Of (IETF draft) | Agent chains delegation across services | Transitive trust |

This layer answers: "Can I verify this agent is who it claims to be?"

### Layer 3: Authorization Identity

Scoped permissions that define what the agent can do:

```
scopes:
  catalog:read      - Browse products and prices
  catalog:write     - Update inventory (partner agents only)
  orders:create     - Place orders (requires user delegation)
  orders:read       - Check order status
  payments:initiate - Start payment flow
```

This layer answers: "What is this agent allowed to do?"

---

## Design Principles

### Principle 1: Identity Should Be Declarative

Agents should not need to reverse-engineer your authentication flow. Declare
your identity endpoints in machine-readable files:

```json
{
  "name": "Example Store Agent Service",
  "provider": { "organization": "Example Inc" },
  "authentication": {
    "type": "oauth2",
    "token_endpoint": "https://auth.example.com/oauth/token",
    "scopes_supported": ["catalog:read", "orders:create"]
  }
}
```

An agent reading this knows exactly how to authenticate without trial and error.

### Principle 2: Start with Client Credentials

Most agent interactions are service-to-service. The client credentials flow is
the simplest and most appropriate:

1. Agent presents its `client_id` and `client_secret`
2. Your auth server issues an access token with defined scopes
3. Agent uses the token for subsequent requests
4. Token expires, agent re-authenticates

No user interaction. No redirect URIs. No browser needed.

### Principle 3: Scope Narrowly, Expand Gradually

Default agent permissions should be minimal:
- Start with read-only catalog access
- Require explicit user delegation for write operations
- Use short-lived tokens (15-60 minutes)
- Audit all agent actions

Trust is earned through consistent, predictable behavior.

### Principle 4: Make Identity Verifiable

Every agent identity claim should be verifiable:
- Client credentials are validated by the auth server
- User delegation is backed by OAuth authorization codes
- Agent cards are hosted on the agent operator's domain (domain = identity)

If an agent claims to be "ShopBot by Example Inc", the agent card at
`example.com/.well-known/agent.json` should confirm this.

---

## Common Mistakes

### Mistake 1: API Keys Instead of OAuth

API keys are shared secrets with no expiration, no scoping, and no rotation
mechanism. They work for prototypes but fail at scale. OAuth provides:
- Token expiration (automatic rotation)
- Scope-based access control
- Standard revocation endpoints
- Audit trails via token introspection

### Mistake 2: No Agent Metadata

Issuing credentials without requiring agent metadata means you cannot
distinguish between agents. Require registration with:
- Agent name and version
- Operator organization
- Contact email
- Intended use case (catalog browsing, order placement, etc.)

### Mistake 3: All-or-Nothing Access

Either full API access or none. Instead, define graduated tiers:
- **Tier 0 (anonymous):** Public data only, rate limited
- **Tier 1 (identified):** Client credentials, read access, higher rate limits
- **Tier 2 (authorized):** User-delegated, read+write, standard limits
- **Tier 3 (trusted):** Partner agreement, bulk operations, custom limits

---

## What ar-identity Does

This skill helps you implement Layers 1 and 2:

1. **Generate OAuth configuration** — Client credentials setup, scope
   definitions, token endpoint configuration
2. **Validate identity endpoints** — Check that your `.well-known/agent.json`,
   OAuth token endpoint, and CORS headers are correctly configured
3. **Provide templates** — Ready-to-deploy agent card and OAuth metadata files

Layer 3 (authorization logic) depends on your application and is outside this
skill's scope. But the configuration generated here gives you the foundation.

---

## Further Reading

- IETF Draft: OAuth 2.0 Extension for AI Agent On-Behalf-Of User Authorization
- A2A Protocol: Agent Discovery and Agent Cards
- MCP OAuth 2.1 Integration (Composio)
- Stytch: Agent-to-Agent OAuth Guide
