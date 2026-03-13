# Holistic Agent-Readiness Philosophy

An audit score of 45/100 is meaningless in isolation. What matters is which
gaps exist, which skill fixes each gap, what order to run them in, and what
the expected score improvement is.

The audit exists to produce an actionable improvement plan, not a vanity number.

---

## Core Principle: Measure What Agents Actually Check

Agents do not care about your meta description quality or keyword density.
They care about:

- **Can I find this site programmatically?** (Discovery)
- **Can I understand the offerings?** (Readability + Data Quality)
- **Can I use the services?** (MCP/API)
- **Can I buy things?** (Commerce + Payment)

Every check item maps to a real agent behavior. If no agent checks for it,
we do not score it.

---

## Why Holistic?

A site with perfect Schema.org markup but no llms.txt is invisible to agents
that start with discovery files. A site with an MCP server but no structured
data gives agents tools without context. A site with ACP checkout but broken
robots.txt blocks agents before they reach the checkout.

The six dimensions form a pipeline. Each layer depends on the ones before it:

```
Discovery → Readability → Data Quality → MCP/API → Commerce → Payment
   "find"      "parse"       "trust"      "use"      "buy"     "pay"
```

Optimizing one layer while ignoring earlier ones produces no value. The audit
reflects this: Discovery is scored first, Payment last.

---

## Scoring Philosophy

### Binary Where Possible, Gradient Where Necessary

- **Binary checks:** llms.txt exists (yes/no), agents.json valid (yes/no),
  MCP endpoint responds (yes/no). Easy to fix, easy to verify.
- **Gradient checks:** Schema.org fill rate (0-100%), response time (0-2s
  scale), data completeness. Show progress over time.

Binary checks dominate Discovery. Gradient checks dominate Data Quality.
This is intentional: discovery is about presence, data is about depth.

### The 80% Data Quality Threshold

The single most important hard threshold in the system.

**Why 80%?** Agents make decisions based on structured data. If a product
catalog has 60% fill rate on critical fields (price, availability, description),
agents will show incomplete information, skip products with missing data, and
prefer competitors with more complete data.

At 80%+ fill rate, agents can confidently present and compare products.
Below 80%, the data is unreliable and agents will deprioritize the merchant.

### Weights Reflect Agent Behavior

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| Discovery (20%) | Highest equal | If agents cannot find you, nothing else matters |
| Data Quality (20%) | Highest equal | Structured data drives agent decisions |
| MCP/API (20%) | Highest equal | Programmatic access enables transactions |
| Readability (15%) | Medium | Important but partially covered by data quality |
| Commerce (15%) | Medium | Only matters after agents can find and understand you |
| Payment (10%) | Lowest | Most sites do not have agent payment yet |

---

## Improvement Path Design

Every audit report must include an improvement path: a sequence of ar-* skills
to run, in order, with expected score impact.

### Path Construction Rules

1. **Fix discovery first** — If agents cannot find you, nothing else matters
2. **Fix data quality second** — Structured data is the foundation
3. **Add identity third** — Authentication enables trusted interactions
4. **Add MCP/API fourth** — Gives agents programmatic access
5. **Add commerce last** — Only matters once agents can find and understand you

### Example Improvement Path

```
Current Score: 35/100 (Grade: F)

Step 1: ar-discover → Add llms.txt, fix robots.txt
  Expected: 35 → 48 (+13 points)

Step 2: ar-structured-data → Add Schema.org Product, fix fill rate
  Expected: 48 → 65 (+17 points)

Step 3: ar-identity → Deploy agent card, configure OAuth
  Expected: 65 → 72 (+7 points)

Step 4: ar-commerce → Set up product feeds, commerce protocols
  Expected: 72 → 87 (+15 points)

Step 5: ar-payments → Add Stripe integration
  Expected: 87 → 95 (+8 points)

Total improvement: 35 → 95 (+60 points)
```

---

## What We Do Not Audit

To keep the audit focused and actionable:

- **SEO metrics** — PageRank, backlinks, keyword rankings (not agent-relevant)
- **Design quality** — Visual design, UX, mobile responsiveness (agents do not see CSS)
- **Content quality** — Writing quality, grammar, tone (out of scope)
- **Human performance** — Page load time for browsers (we only measure API response time)
- **Security posture** — SSL, CORS, CSP headers (important but separate concern; ar-identity covers auth)

---

## GOOD vs BAD Audit Patterns

### GOOD: Actionable Report

```
Discovery: 14/20 — Missing agents.json and A2A agent card
  → Run ar-discover to deploy both (+6 points)
  → Estimated effort: 30 minutes
```

The reader knows exactly what is wrong, what to do, and how long it takes.

### BAD: Vague Report

```
Discovery: 14/20 — Could be improved
  → Consider enhancing your discovery layer
```

No specifics. No skill reference. No effort estimate. Useless.

### GOOD: Contextual Scoring

A service business with no products should not lose points for missing Product
Schema.org. The audit should note "N/A — service business" for product-specific
checks and suggest Service type instead.

### BAD: Rigid Scoring

Penalizing a SaaS company for missing Product JSON-LD when they sell
subscriptions, not physical products. The scoring rubric handles this by
checking for *appropriate* Schema.org types, not just Product.

---

## Competitive Context

The audit is most valuable when compared against competitors. A score of 45/100
might seem bad, but if every competitor scores below 30, you are already the
most agent-ready business in your vertical.

The improvement path should prioritize widening competitive gaps:
- If no competitor has MCP, being first creates a major advantage
- If all competitors have llms.txt, not having one is a critical gap

---

## Self-Evolving Cases

Every real audit teaches something:
- A vertical where certain dimensions matter more
- An edge case the scoring rubric did not anticipate
- A tool or platform that makes implementation easier

Submit cases to `references/cases/` so the next auditor benefits. The audit
is only as good as the real-world experience backing it.
