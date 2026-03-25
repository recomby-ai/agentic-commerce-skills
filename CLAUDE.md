# UCP Onboard Agent

## What This Is
An agent with 5 skills that helps merchants integrate with UCP (Universal Commerce Protocol), making their products discoverable and transactable by AI agents.

## Skill Pipeline
```
ucp-audit → ucp-profile + ucp-catalog → ucp-checkout → ucp-validate
```

## Directory Structure
```
skills/
├── ucp-audit/      — Scan merchant site, output readiness report
├── ucp-profile/    — Generate /.well-known/ucp business profile
├── ucp-catalog/    — Map product data to UCP catalog schema
├── ucp-checkout/   — Generate checkout API code
└── ucp-validate/   — End-to-end integration validation
```

## Conventions
- Each skill has: SKILL.md, references/, scripts/
- Scripts are Python 3.10+, stdlib + requests + beautifulsoup4
- All output files go to store/clients/{client_name}/
- JSON schemas follow UCP spec version 2026-01-23
- Amounts are always in minor units (cents)
- Dates are always RFC 3339

## Key UCP Resources
- Spec: https://github.com/Universal-Commerce-Protocol/ucp
- Docs: https://ucp.dev/documentation/
- Profile schema: source/discovery/profile_schema.json
- Checkout schema: source/schemas/shopping/checkout.json
- Catalog schema: source/schemas/shopping/catalog_search.json
