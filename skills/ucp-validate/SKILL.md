---
name: ucp-validate
description: >
  End-to-end validation of a merchant's UCP integration.
  Tests profile schema, capability negotiation, catalog search/lookup,
  checkout lifecycle, and payment handler declaration. Outputs a
  PASS/FAIL compliance report with 40+ checks. Use after deployment
  to verify the integration works correctly.
argument-hint: "[merchant website URL]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch
---

# UCP Validate — Integration Compliance Tester

Run 40+ validation checks against a deployed UCP integration and produce a compliance report.

## Prerequisites
- Merchant must have `/.well-known/ucp` deployed
- Python 3.10+ with requests, jsonschema

## Step 1: Profile Validation (Checks 1-12)

Fetch `{merchant_url}/.well-known/ucp` and validate:

| # | Check | Rule | Severity |
|---|-------|------|----------|
| 1 | Profile exists | GET returns 200 with JSON content-type | CRITICAL |
| 2 | Valid JSON | Response parses as JSON | CRITICAL |
| 3 | Has `ucp` root key | Top-level object contains `ucp` | CRITICAL |
| 4 | Version format | `ucp.version` matches `YYYY-MM-DD` | CRITICAL |
| 5 | Has services | `ucp.services` is non-empty object | CRITICAL |
| 6 | Service transport | Each service entry has valid `transport` (rest\|mcp\|a2a\|embedded) | ERROR |
| 7 | Service endpoint | Each rest/mcp/a2a service has `endpoint` URL | ERROR |
| 8 | Has capabilities | `ucp.capabilities` is non-empty object | WARNING |
| 9 | Capability naming | All capability names follow `{reverse-domain}.{service}.{capability}` | ERROR |
| 10 | Capability version | Each capability has `version` in YYYY-MM-DD format | ERROR |
| 11 | Has payment_handlers | `ucp.payment_handlers` is non-empty object | ERROR |
| 12 | Payment handler fields | Each handler has `id`, `version`, `available_instruments` | ERROR |

### Step 1 Gate Check
If checks 1-5 all FAIL → abort remaining checks, report "Profile not UCP-compliant."

## Step 2: Namespace & Spec URL Validation (Checks 13-18)

| # | Check | Rule | Severity |
|---|-------|------|----------|
| 13 | Spec URL binding | `spec` URL origin matches namespace authority | ERROR |
| 14 | Schema URL binding | `schema` URL origin matches namespace authority | ERROR |
| 15 | Spec URL reachable | GET `spec` URL returns 200 | WARNING |
| 16 | Schema URL reachable | GET `schema` URL returns 200 | WARNING |
| 17 | No dev.ucp.* misuse | Vendor does not declare `dev.ucp.*` capabilities without matching spec URLs | ERROR |
| 18 | Extension `extends` valid | Every extension's `extends` field references a declared capability | ERROR |

**Spec URL binding rule:**
- `dev.ucp.*` → spec must be at `https://ucp.dev/...`
- `com.example.*` → spec must be at `https://example.com/...`
- Match is on origin (scheme + host), not full path

## Step 3: Catalog Validation (Checks 19-27)

If `dev.ucp.shopping.catalog.search` or `dev.ucp.shopping.catalog.lookup` is declared:

| # | Check | Rule | Severity |
|---|-------|------|----------|
| 19 | Search endpoint responds | POST to catalog search returns 200 | ERROR |
| 20 | Search response has `products` | Response contains `products` array | ERROR |
| 21 | Products have required fields | Each product has `id`, `title`, `description`, `price_range`, `variants` | ERROR |
| 22 | Variants have required fields | Each variant has `id`, `title`, `description`, `price` | ERROR |
| 23 | Price format correct | `price.amount` is integer (minor units), `price.currency` is ISO 4217 | ERROR |
| 24 | At least 1 variant per product | `variants` array is non-empty | ERROR |
| 25 | Lookup endpoint responds | POST to catalog lookup with valid ID returns 200 | ERROR |
| 26 | Lookup returns matching product | Response product ID matches requested ID | ERROR |
| 27 | Pagination works | If >10 products, pagination token returns next page | WARNING |

## Step 4: Checkout Validation (Checks 28-37)

If `dev.ucp.shopping.checkout` is declared:

| # | Check | Rule | Severity |
|---|-------|------|----------|
| 28 | Create session | POST create with valid line_item returns 200 | ERROR |
| 29 | Session has required fields | Response has `id`, `status`, `line_items`, `currency`, `totals` | ERROR |
| 30 | Status is `incomplete` | Initial status is `incomplete` | ERROR |
| 31 | Totals structure | Has exactly 1 `subtotal` and 1 `total` entry | ERROR |
| 32 | Discount amounts negative | Any `discount`/`items_discount` total has amount < 0 | ERROR |
| 33 | Non-discount amounts non-negative | All other total types have amount >= 0 | ERROR |
| 34 | Update session | POST update with modified quantity returns 200 | ERROR |
| 35 | Totals recalculated | After update, totals reflect new quantity | WARNING |
| 36 | Links present | Response has `links` with `privacy_policy` and `terms_of_service` | WARNING |
| 37 | Cancel session | If supported, cancel returns appropriate status | WARNING |

> **HARD RULE — Never call checkout complete.** Validation must NOT trigger real payments. Only test create, update, retrieve, and cancel. If the merchant has a sandbox/test mode, note it in the report but still do not complete.

## Step 5: Capability Negotiation Validation (Checks 38-42)

| # | Check | Rule | Severity |
|---|-------|------|----------|
| 38 | UCP response header | Checkout response includes `ucp` metadata with active capabilities | ERROR |
| 39 | Capability intersection | Response capabilities are subset of profile capabilities | ERROR |
| 40 | Orphan extension pruning | No extension in response whose parent is missing | ERROR |
| 41 | Version compatibility | Response capability versions match or are compatible with profile | WARNING |
| 42 | Payment handler in response | Checkout response includes at least one payment_handler | ERROR |

## Step 6: Generate Compliance Report

Save to `store/clients/{client_name}/validation-report.md`:

```markdown
# UCP Compliance Report — {merchant_name}

**URL:** {url}
**Date:** {date}
**Spec Version Tested:** 2026-01-23
**Result:** {PASS|FAIL} ({passed}/{total} checks passed)

## Summary
- CRITICAL: {count} passed / {count} total
- ERROR: {count} passed / {count} total
- WARNING: {count} passed / {count} total

## Results

### Profile (Checks 1-12)
| # | Check | Result | Detail |
|---|-------|--------|--------|
| 1 | Profile exists | PASS/FAIL | {detail} |
...

### Namespace (Checks 13-18)
...

### Catalog (Checks 19-27)
...

### Checkout (Checks 28-37)
...

### Negotiation (Checks 38-42)
...

## Failed Checks — Fix Guide
{For each FAIL, explain what's wrong and how to fix it}
```

**Passing criteria:**
- **PASS**: All CRITICAL pass + all ERROR pass (warnings can fail)
- **CONDITIONAL PASS**: All CRITICAL pass + some ERROR fail
- **FAIL**: Any CRITICAL fails

## Scripts

| Script | Purpose | Dependencies |
|--------|---------|-------------|
| `validate_ucp.py` | Main validation runner | requests, jsonschema, json, re, sys |

## Collaboration

```
ucp-validate (this skill)
    │
    ├── inputs ← deployed merchant URL
    │
    ├── outputs → store/clients/{name}/validation-report.md
    │
    └── used after → ucp-checkout (post-deployment verification)
```
