# Agentic Commerce Skills

AI agent skills for onboarding merchants to [UCP (Universal Commerce Protocol)](https://github.com/Universal-Commerce-Protocol/ucp) — the open standard by Google, Shopify, and 20+ partners that lets AI agents discover and transact with businesses.

## What This Does

These skills turn an AI agent into a UCP integration specialist. Give it a merchant's website URL, and it will:

1. **Audit** the site for UCP readiness (structured data, payment providers, APIs)
2. **Generate** a `/.well-known/ucp` business profile
3. **Map** product catalogs to UCP schema format
4. **Scaffold** checkout API code from official samples
5. **Validate** the integration against official tools

```
Merchant URL → audit → profile → catalog → checkout → validate → Live on UCP
```

## Skills

| Skill | What It Does | Script |
|-------|-------------|--------|
| **ucp-audit** | Scans a website, scores UCP readiness 0-100, identifies reusable assets and gaps | `audit_site.py` |
| **ucp-profile** | Generates `/.well-known/ucp` business profile JSON with correct capabilities and payment handlers | `generate_profile.py` |
| **ucp-catalog** | Maps Shopify / WooCommerce / CSV product data to UCP catalog schema (minor units, variants, media) | `map_catalog.py` |
| **ucp-checkout** | Guides setup of checkout API based on [official UCP samples](https://github.com/Universal-Commerce-Protocol/samples) | SKILL.md |
| **ucp-validate** | Validates profile structure + spec URL reachability, recommends official `ucp-schema` CLI for deep validation | `validate_ucp.py` |

## Quick Start

```bash
pip install requests beautifulsoup4 jsonschema

# 1. Audit a site
python skills/ucp-audit/scripts/audit_site.py https://allbirds.com

# 2. Generate a profile
python skills/ucp-profile/scripts/generate_profile.py \
  --domain example.com --name "My Store" --payment stripe --transport rest

# 3. Map product catalog
python skills/ucp-catalog/scripts/map_catalog.py \
  --source shopify --url https://allbirds.com --currency USD

# 4. Validate integration
python skills/ucp-validate/scripts/validate_ucp.py https://allbirds.com
```

## Tested Against Real Sites

| Site | Audit Score | Validate | Notes |
|------|------------|----------|-------|
| allbirds.com | 65/100 | PASS 11/11 | Shopify, MCP transport |
| glossier.com | 90/100 | PASS 11/11 | Shopify, MCP transport |
| puddingheroes.com | 5/100 | FAIL 16/42 | Non-standard format, correctly flagged |

## How Validation Works

We don't reinvent the wheel. Validation references official tools:

| Layer | Tool | Source |
|-------|------|--------|
| Profile structure | Our `validate_ucp.py` | Checks required fields, namespace rules, URL reachability |
| Full schema validation | [`ucp-schema`](https://github.com/Universal-Commerce-Protocol/ucp-schema) | Official Rust CLI: `cargo install ucp-schema` |
| Checkout behavior | [`conformance`](https://github.com/Universal-Commerce-Protocol/conformance) | Official test suite (12 Python test files) |
| External discovery | [UCPchecker.com](https://ucpchecker.com) | Community validator (2,800+ merchants monitored) |

## UCP Protocol Overview

UCP lets AI agents (Gemini, ChatGPT, Claude, etc.) discover and purchase from merchants through a standard protocol:

```
AI Agent                          Merchant
   │                                 │
   ├── GET /.well-known/ucp ────────►│  Discovery
   │◄── capabilities + payment ──────┤
   │                                 │
   ├── POST /catalog/search ────────►│  Product Search
   │◄── products[] ──────────────────┤
   │                                 │
   ├── POST /checkout (create) ─────►│  Checkout
   │◄── session {id, totals} ────────┤
   │                                 │
   ├── POST /checkout (complete) ───►│  Payment
   │◄── order confirmation ──────────┤
```

**Key specs:**
- [UCP Specification](https://github.com/Universal-Commerce-Protocol/ucp)
- [Official Samples](https://github.com/Universal-Commerce-Protocol/samples) (Python/FastAPI + Node.js/Hono)
- [Official Python SDK](https://github.com/Universal-Commerce-Protocol/python-sdk)

## Project Structure

```
skills/
├── ucp-audit/
│   ├── SKILL.md                    # Agent instructions
│   └── scripts/audit_site.py       # Website scanner
├── ucp-profile/
│   ├── SKILL.md
│   └── scripts/generate_profile.py # Profile generator
├── ucp-catalog/
│   ├── SKILL.md
│   └── scripts/map_catalog.py      # Catalog mapper (Shopify/CSV/JSON)
├── ucp-checkout/
│   └── SKILL.md                    # References official samples
└── ucp-validate/
    ├── SKILL.md
    └── scripts/validate_ucp.py     # Validation orchestrator
```

## Using with AI Agents

Each `SKILL.md` is designed to be read by an AI agent (Claude, GPT, etc.) as a step-by-step instruction manual. The agent reads the skill, runs the scripts, and produces the deliverables.

**For NanoClaw / OpenClaw users:** Copy the `skills/` directory into your agent's skill path.

**For Claude Code users:** Point Claude at a SKILL.md and give it a merchant URL.

## Security

UCP has built-in security mechanisms that merchants should implement:

- **Message Signatures** (RFC 9421) — ECDSA signing of all requests/responses
- **AP2 Mandates** — Cryptographic proof of user purchase authorization (SD-JWT)
- **Signals** — Platform-observed environment data for fraud prevention
- **Buyer Consent** — GDPR/CCPA consent transmission

See the [UCP Security spec](https://github.com/Universal-Commerce-Protocol/ucp/blob/main/docs/specification/signatures.md) for implementation details.

## Contributing

1. Fork the repo
2. Add or improve a skill
3. Test against a real merchant site
4. Submit a PR with test results

## License

[MIT](LICENSE)
