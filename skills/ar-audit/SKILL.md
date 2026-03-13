---
name: ar-audit
description: >
  Runs a comprehensive agent-readiness audit on any URL. Scores 6 dimensions
  (Discovery, Readability, Data Quality, MCP/API, Commerce, Payment) out of
  100 with a grade and improvement roadmap. Each gap maps to a specific ar-*
  skill for remediation. Use as the starting point before running other skills,
  or to measure progress after improvements.
argument-hint: [url]
allowed-tools: Bash, Read, Grep, Glob
---

# ar-audit — Score your site's agent-readiness

## Before you start

1. Read [philosophy.md](references/philosophy.md) — what we audit and why
2. Read [scoring-rubric.md](references/scoring-rubric.md) — detailed scoring per dimension
3. Read [sample-report.md](references/sample-report.md) — example audit output
4. Check [cases/](references/cases/) — see previous audit results for similar sites

## Step 1: Run the audit

```bash
python ${CLAUDE_SKILL_DIR}/scripts/audit_full.py --url $ARGUMENTS --json --output report.json
```

This checks 6 dimensions against official specs:

| Dimension | Max | What it checks | Spec sources |
|-----------|-----|---------------|--------------|
| Discovery | 20 | llms.txt, agents.json, robots.txt, sitemap, A2A agent card | llmstxt.org, a2a-protocol.org, RFC 9309 |
| Readability | 15 | title/meta, heading hierarchy, semantic HTML, lang | HTML spec |
| Data Quality | 20 | JSON-LD, Schema.org types, required properties, OG tags | Google Search Central, schema.org |
| MCP/API | 20 | API docs, OpenAPI spec, API endpoints, CORS | OpenAPI spec |
| Commerce | 15 | UCP manifest, ACP checkout, product schema | Google UCP, OpenAI ACP |
| Payment | 10 | payment SDK, x402 headers, Apple/Google Pay | Stripe, coinbase/x402 |

## Step 2: Generate improvement roadmap

```bash
python ${CLAUDE_SKILL_DIR}/scripts/score_readiness.py --input report.json --format markdown
```

This outputs: grade (A/B/C/D/F), per-dimension scores with bar chart, and prioritized fix list sorted by impact.

## Step 3: Follow the roadmap

Each gap maps to a specific skill:

| Gap found | Run this skill |
|-----------|---------------|
| No llms.txt / agents.json / A2A agent card | `/ar-discover` |
| Missing JSON-LD / Schema.org / OG tags | `/ar-structured-data` |
| No OAuth / identity endpoints | `/ar-identity` |
| No UCP / ACP / product schema | `/ar-commerce` |
| No payment SDK / wallet pay | `/ar-payments` |

Run the recommended skills to fix gaps, then re-audit to measure improvement.

## Step 4: Re-audit

After running improvement skills, re-audit to verify progress:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/audit_full.py --url $ARGUMENTS --json --output report-v2.json
python ${CLAUDE_SKILL_DIR}/scripts/score_readiness.py --input report-v2.json --format markdown
```

Compare scores. Repeat until the target grade is reached.

## Step 5: Write back

Add a case to `references/cases/` using [_template.md](references/cases/_template.md). Include:

- Starting score and ending score
- Which skills were run and in what order
- Surprises or dimensions that scored differently than expected

## Grading

**A (90+)** / **B (75-89)** / **C (60-74)** / **D (40-59)** / **F (<40)**

Exit code 0 = grade A or B. Exit code 1 = grade C or below.

## References

- [philosophy.md](references/philosophy.md) — audit philosophy and rationale
- [scoring-rubric.md](references/scoring-rubric.md) — detailed rubric with all check items
- [sample-report.md](references/sample-report.md) — example audit output
- [cases/](references/cases/) — real-world audit cases
