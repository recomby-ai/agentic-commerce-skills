---
name: ar-identity
description: >
  Sets up agent identity and authentication endpoints. Configures OAuth 2.0
  for AI agents, deploys A2A agent cards, and sets up OpenID Connect discovery.
  Validates against RFC 8414, OIDC Discovery 1.0, and A2A protocol specs.
  Use when a site needs to authenticate AI agents or expose machine-readable
  identity information.
argument-hint: [url]
allowed-tools: Bash, Read, Grep, Glob, Write, Edit
---

# ar-identity — Make agents authenticate

## Before you start

1. Read [philosophy.md](references/philosophy.md) — why agent identity matters
2. Read [oauth-agent-guide.md](references/oauth-agent-guide.md) — OAuth 2.0 for AI agents
3. Check [cases/](references/cases/) — someone may have solved this for the same stack

## Step 1: Search for latest specs

Before configuring any identity endpoints, search the web for current specs:
- Search `RFC 8414 OAuth authorization server metadata` — confirm required fields
- Search `OpenID Connect Discovery 1.0` — confirm required OIDC fields
- Search `a2a-protocol.org agent card spec` — confirm required agent card fields
- Search `OAuth 2.0 for AI agents` — confirm latest extensions and best practices

Do NOT rely on your training data or even the references here — auth specs evolve.

## Step 2: Assess current state

Run the validator to see what identity endpoints exist:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/validate_identity.py --url $ARGUMENTS
```

## Step 3: Deploy A2A agent card

Create `/.well-known/agent.json` per a2a-protocol.org spec:

```json
{
  "name": "Your Service Agent",
  "description": "What this agent/service does",
  "url": "https://example.com",
  "version": "1.0.0",
  "capabilities": {
    "streaming": false,
    "pushNotifications": false
  },
  "skills": [
    {
      "id": "product-search",
      "name": "Product Search",
      "description": "Search products by keyword"
    }
  ],
  "defaultInputModes": ["text/plain"],
  "defaultOutputModes": ["application/json"]
}
```

Required fields: name, description, url, version, capabilities, skills, defaultInputModes, defaultOutputModes.

## Step 4: Configure OAuth 2.0 for agents

Set up OAuth 2.0 with agent-specific considerations:

- **Client Credentials flow** — for server-to-server agent auth (most common)
- **Authorization Code + PKCE** — for agents acting on behalf of users
- Register agent-specific OAuth scopes (e.g., `agent:read`, `agent:order`)
- Include agent metadata in token requests (agent name, version, capabilities)

Deploy OAuth metadata at `/.well-known/oauth-authorization-server` per RFC 8414:
- Required: `issuer`, `response_types_supported`
- Required (if grants supported): `token_endpoint`
- Recommended: `scopes_supported`, `grant_types_supported`

## Step 5: Set up OpenID Connect Discovery (if applicable)

If using OIDC, deploy `/.well-known/openid-configuration` with 7 required fields:
- `issuer`, `authorization_endpoint`, `token_endpoint`, `jwks_uri`
- `response_types_supported`, `subject_types_supported`
- `id_token_signing_alg_values_supported`

## Step 6: Configure CORS

Ensure token endpoints are accessible to agent clients:

```
Access-Control-Allow-Origin: *  (or specific agent domains)
Access-Control-Allow-Methods: POST, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type
```

## Step 7: Validate

Re-run the validator:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/validate_identity.py --url $ARGUMENTS
```

- Exit code 0 = identity endpoints valid → done
- Exit code 1 = issues found → fix and re-validate
- Repeat until all checks pass

## Step 8: Write back

Add a case to `references/cases/` using [_template.md](references/cases/_template.md). Especially:

- CORS issues with token endpoints
- Agent-specific scope design decisions
- OAuth flow choice rationale

## References

- [philosophy.md](references/philosophy.md) — trust, attribution, access control
- [oauth-agent-guide.md](references/oauth-agent-guide.md) — OAuth flows, scoping, metadata
- [cases/](references/cases/) — real-world identity implementation cases
