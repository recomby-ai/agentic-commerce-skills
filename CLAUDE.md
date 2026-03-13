# agent-ready — Instructions for AI Agents

This repo contains executable skills for making merchant websites AI-agent-ready.

## Repo Structure

```
protocols/     — Protocol index: 20+ protocols across 6 categories, with official spec links
skills/        — Executable skills (each has SKILL.md with step-by-step instructions)
  ar-discover/         — Make agents find you (llms.txt, agents.json, A2A)
  ar-structured-data/  — Make agents understand you (Schema.org, JSON-LD)
  ar-commerce/         — Make agents buy from you (ACP, UCP)
  ar-payments/         — Make agents pay you (Stripe SPT, x402, AP2)
  ar-identity/         — Make agents authenticate (OAuth, OIDC, A2A agent card)
  ar-audit/            — Score agent-readiness (0-100) with improvement roadmap
```

## How to Use a Skill

1. Read the skill's `SKILL.md` — it has the full workflow
2. Read `references/` files linked in SKILL.md — these are your knowledge base
3. Check `references/cases/` — someone may have solved this for the same stack
4. Follow the steps in SKILL.md to implement the changes
5. Run the validate script to verify — keep fixing until exit code 0
6. If you learned something non-obvious, write a case back to `references/cases/`

## Critical Rules

**Search before generating.** Before creating any file (llms.txt, JSON-LD, manifest, etc.), search the web for the latest official spec. Protocols change fast. Your training data may be outdated. The references in this repo may be outdated. The official spec is the source of truth.

**Validate before declaring done.** Every skill has a validate script. Run it. If it says FAIL, you're not done. Fix the issue and re-validate. The validate scripts check against official specs — they are the quality gate.

**Reference first.** Before starting work, check `references/cases/` for existing solutions. Don't reinvent what's already been solved.

## Skill Inputs

All skills take a **URL** as primary input via `$ARGUMENTS`. Use `${CLAUDE_SKILL_DIR}` to reference scripts and files within the skill directory.

## Output Conventions

- Generated files: output as code blocks with the target filename noted
- Validation results: JSON (with `--json` flag) or human-readable text
- Audit reports: use the scoring format from ar-audit's SKILL.md
- Always note which protocol version/spec a recommendation targets
