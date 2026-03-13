# Contributing to agent-ready

The most valuable contribution is a **case** — a real-world record of what worked, what didn't, and what was surprising when making a site agent-ready.

Cases are **for agents to read**. When an agent runs a skill, it checks cases first. Your case becomes every future agent's shortcut.

## Submitting a Case

1. Fork the repo
2. Pick the skill your case relates to (e.g., `ar-discover`, `ar-structured-data`)
3. Copy `skills/{skill}/references/cases/_template.md` to a new file in the same directory
4. Name it descriptively: `shopify-llms-txt.md`, `nextjs-jsonld-product.md`, `wordpress-schema-faq.md`
5. Fill in the template
6. Submit a PR

### Case Template

Every case follows this structure (see `_template.md` in any skill's `references/cases/` directory):

```markdown
# {Platform/Stack} — {What you solved}

- **Author:** {your name or agent ID}
- **Date:** YYYY-MM-DD
- **Stack:** {WordPress, Shopify, Next.js, etc.}
- **Protocols:** {llms.txt, Schema.org, ACP, etc.}

## Context
What the site needed and why.

## What Worked
Steps that succeeded, with code snippets.

## What Did NOT Work
Approaches that failed and why.

## Gotchas
Non-obvious issues encountered.

## Verification
How you confirmed it works (which validate script, what output).

## Result
PASS / PARTIAL / FAIL + one-line summary.

## Tags
`wordpress` `llms-txt` `e-commerce`
```

### Case Quality Standards

- **Real implementations only.** No hypothetical or untested cases.
- **Include the gotchas.** The unexpected parts are the most valuable.
- **Be specific.** Name the platform, the exact error, the version.
- **Include verification.** Show which validate script you ran and the result.
- **Keep it concise.** 100-300 words, not a blog post.

## Other Contributions

### Protocol updates
Protocols evolve fast. If a spec changes or a new protocol launches, update the relevant file in `protocols/` with the official source link.

### Reference improvements
Found better documentation or a more accurate guide? Update the relevant `references/*.md` file with a PR.

### Skill improvements
Found a gap in a skill's workflow? Open an issue or PR against the skill's `SKILL.md`.

### New skills
Propose new skills by opening an issue first. A skill needs: clear scope, step-by-step workflow, a validate script, and at least one real case.
