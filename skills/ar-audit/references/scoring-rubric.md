# Scoring Rubric

6 dimensions, 100 points total. Each dimension contains specific check items
with defined scoring criteria and thresholds.

---

## Dimension Weights

| Dimension | Weight | Max Points | Why This Weight |
|-----------|--------|------------|-----------------|
| Discovery | 20% | 20 | Foundation — agents must find you first |
| Readability | 15% | 15 | Content must be machine-parseable |
| Data Quality | 20% | 20 | Structured data drives agent decisions |
| MCP/API | 20% | 20 | Programmatic access enables transactions |
| Commerce | 15% | 15 | ACP/UCP enable actual purchases |
| Payment | 10% | 10 | Payment readiness completes the loop |

---

## Dimension 1: Discovery (20 points)

How easily can AI agents discover this business?

| Check Item | Max Points | Scoring |
|-----------|------------|---------|
| llms.txt exists at /llms.txt | 4 | 0 or 4 (binary) |
| llms.txt has structured sections | 1 | 0 or 1 |
| agents.json exists and valid | 4 | 0-4 (0=missing, 2=exists but invalid, 4=valid) |
| A2A agent card at /.well-known/agent.json | 3 | 0 or 3 |
| /.well-known/ucp exists | 3 | 0 or 3 |
| robots.txt allows AI bots | 3 | 0-3 (0=blocks all, 1=blocks some, 3=allows key bots) |
| sitemap.xml exists and fresh (<30 days) | 2 | 0-2 (0=missing, 1=stale, 2=fresh) |

**Key AI bots for robots.txt scoring:**
- Must allow: GPTBot, Google-Extended, ClaudeBot (1 point each)
- Optional: PerplexityBot, Comet-Crawler (no penalty)

---

## Dimension 2: Readability (15 points)

Can agents parse and understand the site content?

| Check Item | Max Points | Scoring |
|-----------|------------|---------|
| Schema.org JSON-LD present | 4 | 0 or 4 |
| Schema.org uses correct @type | 2 | 0-2 (appropriate type for business) |
| Heading hierarchy (H1 > H2 > H3) | 2 | 0-2 (0=broken, 1=partial, 2=correct) |
| Meta title present and descriptive | 2 | 0-2 (0=missing, 1=generic, 2=descriptive) |
| Meta description present | 1 | 0 or 1 |
| Open Graph tags present | 2 | 0-2 (0=missing, 1=partial, 2=complete) |
| Canonical URL set | 1 | 0 or 1 |
| Language attribute on HTML | 1 | 0 or 1 |

**Heading hierarchy rules:**
- Exactly one H1 per page
- H2s follow H1, H3s follow H2s (no skipping levels)
- Deduct 1 point per violation, minimum 0

---

## Dimension 3: Data Quality (20 points)

How complete and accurate is the structured data?

| Check Item | Max Points | Scoring |
|-----------|------------|---------|
| JSON-LD items found (Product/Service/Organization) | 4 | 0-4 (0=none, 2=few, 4=comprehensive) |
| Required field fill rate >= 80% | 8 | 0-8 (proportional to fill rate) |
| Price in correct format (amount + currency) | 3 | 0-3 |
| Availability uses Schema.org enum | 2 | 0-2 |
| Description length >= 50 chars | 2 | 0-2 |
| Image URLs present and reachable | 1 | 0-1 |

**Fill rate calculation:**

Required fields per Product: name, price, priceCurrency, availability,
description, image

```
fill_rate = sum(filled_required_fields) / (num_items * num_required_fields) * 100
```

**Fill rate scoring:**
- 0-49%: 0 points
- 50-59%: 2 points
- 60-69%: 3 points
- 70-79%: 4 points
- 80-89%: 6 points
- 90-100%: 8 points

---

## Dimension 4: MCP/API (20 points)

Does the site expose programmatic interfaces for agents?

| Check Item | Max Points | Scoring |
|-----------|------------|---------|
| API or MCP endpoint responds | 5 | 0 or 5 |
| Endpoint returns structured data | 3 | 0-3 |
| OpenAPI / tool descriptions present | 3 | 0-3 |
| Response time < 2s | 4 | 0-4 (4=<500ms, 3=<1s, 2=<2s, 1=<5s, 0=>5s) |
| Error responses are structured JSON | 2 | 0-2 |
| API documentation accessible | 2 | 0 or 2 |
| CORS configured for agent access | 1 | 0 or 1 |

**MCP endpoint detection order:**
1. Check llms.txt, agents.json, or /.well-known/ucp for MCP URL
2. Try common paths: /mcp, /sse, /mcp/sse, /api
3. Check for OpenAPI spec at /openapi.json, /swagger.json, /api/docs

---

## Dimension 5: Commerce (15 points)

Can agents initiate and complete purchases?

| Check Item | Max Points | Scoring |
|-----------|------------|---------|
| Commerce-related Schema.org present | 4 | 0-4 (Product/Offer/Service with pricing) |
| Product feed accessible (Google Merchant / similar) | 3 | 0-3 |
| UCP /.well-known/ucp manifest present | 3 | 0-3 (0=missing, 1=invalid, 3=valid) |
| ACP or checkout endpoint responds | 3 | 0-3 |
| Shopping-related capabilities declared | 2 | 0-2 |

---

## Dimension 6: Payment (10 points)

Is the site ready to accept agent-initiated payments?

| Check Item | Max Points | Scoring |
|-----------|------------|---------|
| Payment provider integration detected | 3 | 0-3 (Stripe, PayPal, etc.) |
| Delegated Payment Token support | 3 | 0-3 |
| x402 endpoint responds | 2 | 0-2 |
| Payment method Schema.org present | 2 | 0-2 |

**Note:** Payment is scored leniently because most sites do not have agent
payment protocols yet. The audit identifies which payment path to implement.

---

## Thresholds and Grades

| Total Score | Grade | Meaning |
|------------|-------|---------|
| 90-100 | A | Agent-ready, fully operational |
| 75-89 | B | Good foundation, minor gaps |
| 60-74 | C | Partially ready, significant gaps |
| 40-59 | D | Early stage, major work needed |
| 0-39 | F | Not agent-ready |

### Per-Dimension Health Indicators

| Dimension | Green | Yellow | Red |
|-----------|-------|--------|-----|
| Discovery | >= 16 | 8-15 | < 8 |
| Readability | >= 12 | 6-11 | < 6 |
| Data Quality | >= 16 | 8-15 | < 8 |
| MCP/API | >= 16 | 8-15 | < 8 |
| Commerce | >= 12 | 6-11 | < 6 |
| Payment | >= 8 | 4-7 | < 4 |

---

## Improvement Path Mapping

| Gap Found | Recommended ar-* Skill | Expected Impact |
|-----------|----------------------|-----------------|
| No llms.txt / agents.json | **ar-discover** | +5 to +12 Discovery |
| Poor Schema.org / missing JSON-LD | **ar-structured-data** | +8 to +15 Data Quality |
| No agent auth / identity | **ar-identity** | +3 to +8 Discovery/MCP |
| No product feeds / commerce | **ar-commerce** | +8 to +15 Commerce |
| No payment integration | **ar-payments** | +5 to +10 Payment |

---

## Key Differences from SEO Audits

1. No keyword analysis (agents do not search by keywords)
2. No backlink analysis (agents do not use PageRank)
3. MCP/API is a first-class dimension (not in any SEO audit)
4. Commerce protocols are scored (unique to agent readiness)
5. Payment readiness is scored (unique to agent commerce)
6. Discovery focuses on agent-specific files, not search engine indexing
