# Agent-Readiness Audit Report

**Site:** https://demo-store.example.com
**Date:** 2026-03-10
**Auditor:** ar-audit v1.0.0

---

## Overall Score: 52/100 (Grade: D)

```
Discovery     ████████████████░░░░ 16/20 (80%)
Readability   ██████████░░░░░░░░░░ 10/15 (67%)
Data Quality  ████████████░░░░░░░░ 12/20 (60%)
MCP/API       ██████░░░░░░░░░░░░░░  6/20 (30%)
Commerce      ████████░░░░░░░░░░░░  8/15 (53%)
Payment       ░░░░░░░░░░░░░░░░░░░░  0/10 ( 0%)
─────────────────────────────────────────────
TOTAL                              52/100
```

---

## Dimension Details

### Discovery: 16/20

| Check | Score | Notes |
|-------|-------|-------|
| llms.txt exists | 4/4 | Found at /llms.txt, well-structured with ## sections |
| llms.txt structured | 1/1 | Has Products, API, About sections |
| agents.json | 4/4 | Valid JSON with version and flows |
| A2A agent card | 0/3 | Not found at /.well-known/agent.json |
| UCP manifest | 0/3 | Not found at /.well-known/ucp |
| robots.txt AI bots | 3/3 | GPTBot, Google-Extended, ClaudeBot all allowed |
| sitemap.xml | 2/2 | Present, last modified 3 days ago |

**Health: GREEN.** Strong discovery layer. Deploy agent card and UCP manifest for full score.

### Readability: 10/15

| Check | Score | Notes |
|-------|-------|-------|
| Schema.org JSON-LD | 4/4 | Organization + Product types found |
| Schema.org @type | 2/2 | Product is appropriate for e-commerce |
| Heading hierarchy | 1/2 | H1 present, one H2-to-H4 skip found |
| Meta title | 2/2 | "Demo Store — Premium Electronics" |
| Meta description | 1/1 | Present, 155 characters |
| Open Graph tags | 0/2 | Not found |
| Canonical URL | 1/1 | Set correctly |
| Language attribute | 1/1 | lang="en" |

**Health: YELLOW.** Add Open Graph tags and fix heading hierarchy.

### Data Quality: 12/20

| Check | Score | Notes |
|-------|-------|-------|
| JSON-LD items | 4/4 | 24 Product items found across catalog |
| Fill rate | 4/8 | 72% — below 80% threshold (missing availability on 7 items) |
| Price format | 3/3 | All prices have amount + USD currency |
| Availability enum | 1/2 | 17/24 items use Schema.org enum |
| Description length | 0/2 | Average 38 chars — below 50 char minimum |
| Image URLs | 0/1 | 3 of 24 items have broken image URLs |

**Health: YELLOW.** Fill rate at 72% is close to threshold. Fix availability
on 7 items and extend descriptions to push above 80%.

### MCP/API: 6/20

| Check | Score | Notes |
|-------|-------|-------|
| API endpoint responds | 5/5 | /api/v1 returns 200 with JSON |
| Structured response | 1/3 | Returns data but inconsistent schema |
| OpenAPI / descriptions | 0/3 | No OpenAPI spec found |
| Response time | 0/4 | Average 3.2s (too slow) |
| Error handling | 0/2 | Errors return HTML 500, not structured JSON |
| API documentation | 0/2 | No docs found |
| CORS | 0/1 | No CORS headers |

**Health: RED.** API exists but needs significant work. Add OpenAPI spec,
fix response times, add CORS headers, and return structured errors.

### Commerce: 8/15

| Check | Score | Notes |
|-------|-------|-------|
| Commerce Schema.org | 4/4 | Product/Offer with pricing present |
| Product feed | 4/3 | Google Merchant feed at /feed/products.xml |
| UCP manifest | 0/3 | Not found |
| ACP / checkout endpoint | 0/3 | Not found |
| Shopping capabilities | 0/2 | No capabilities declared |

**Health: YELLOW.** Good product data foundation. Need commerce protocol
endpoints (UCP/ACP) for agent-initiated purchases.

### Payment: 0/10

| Check | Score | Notes |
|-------|-------|-------|
| Payment provider | 0/3 | No Stripe/PayPal integration detected |
| DPT support | 0/3 | Not found |
| x402 endpoint | 0/2 | No 402 response handler |
| Payment Schema.org | 0/2 | No PaymentMethod markup |

**Health: RED.** No agent payment infrastructure. Start with Stripe integration.

---

## Improvement Path

### Priority 1: Run ar-structured-data (Expected: +8 points -> 60/100)

Current gaps:
- Fill rate 72% -> target 90% (+4 points fill rate)
- Fix 7 missing availability fields (+1 point)
- Extend descriptions to 50+ chars (+2 points)
- Fix 3 broken image URLs (+1 point)

**Why first:** Data quality is the foundation for commerce. Agents skip
products with incomplete data. Getting above 80% fill rate unlocks the
data quality bonus.

### Priority 2: Run ar-discover (Expected: +6 points -> 66/100)

Current gaps:
- No A2A agent card -> Deploy /.well-known/agent.json (+3 points)
- No UCP manifest -> Deploy /.well-known/ucp (+3 points)

### Priority 3: Run ar-identity (Expected: +3 points -> 69/100)

Current gaps:
- No OAuth endpoints for agent auth
- API has no CORS headers -> Fix CORS (+1 point)
- Add OpenAPI spec -> Enables agent tool discovery (+2 points)

### Priority 4: Run ar-commerce (Expected: +5 points -> 74/100)

Current gaps:
- No UCP manifest with capabilities (+2 points)
- No ACP checkout endpoint (+3 points)

### Priority 5: Run ar-payments (Expected: +6 points -> 80/100)

Current gaps:
- No payment provider detected (+3 points)
- No payment Schema.org markup (+2 points)
- No x402 handler (+1 point, partial)

---

## Summary

| Metric | Value |
|--------|-------|
| Overall Score | 52/100 |
| Grade | D |
| Strongest Dimension | Discovery (80%) |
| Weakest Dimension | Payment (0%) |
| Biggest Opportunity | Data Quality (+8 pts for fixing fill rate) |
| Estimated Path to Grade C | 2 skills (ar-structured-data + ar-discover) |
| Estimated Path to Grade B | 4 skills (+ ar-identity + ar-commerce) |

---

*Report generated by ar-audit v1.0.0*
*Next recommended audit: after completing Priority 1 and 2*
