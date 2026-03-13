---
name: ar-discover
description: >
  Makes a website discoverable by AI agents. Generates llms.txt, agents.json,
  A2A agent card, and configures robots.txt for AI bots. Validates all outputs
  against official specs. Use when a site needs to be found by AI agents like
  ChatGPT, Gemini, Perplexity, or Claude.
argument-hint: [url]
allowed-tools: Bash, Read, Grep, Glob, Write, Edit
---

# ar-discover — Make agents find you

## Before you start

1. Read [philosophy.md](references/philosophy.md) — why discovery matters
2. Read [llms-txt-guide.md](references/llms-txt-guide.md) — llms.txt format per llmstxt.org spec
3. Read [agents-json-guide.md](references/agents-json-guide.md) — agents.json structure
4. Check [cases/](references/cases/) — someone may have solved this for the same stack

## Step 1: Search for latest specs

Before generating anything, search the web for the current version of each spec:
- Search `llmstxt.org spec` — confirm current format requirements
- Search `agents.json spec` — confirm current schema
- Search `a2a-protocol.org agent card` — confirm required fields
- Search `robots.txt AI bots 2026` — confirm current bot names

Do NOT rely on your training data or even the references in this repo — specs change. If what you find online conflicts with the references here, follow the official spec.

## Step 2: Analyze the target site

Fetch the target URL. Identify:
- What the business does (one paragraph)
- Key pages (about, products/services, pricing, docs, contact)
- Whether an API or OpenAPI spec exists
- Current robots.txt content (if any)

## Step 3: Generate llms.txt

Create a `llms.txt` file following the llmstxt.org spec:

- **H1 (required):** Site name and one-line description
- **Blockquote:** Expanded description (2-3 sentences)
- **H2 sections:** Group important URLs by category (Docs, API, Products, etc.)
- Each URL as a markdown link with a brief description
- Keep it focused — only include pages an AI agent would actually need

Place at site root: `https://example.com/llms.txt`

## Step 4: Generate agents.json

If the site has an API or transactional workflows:

- Define flows (search → select → purchase, etc.)
- Each flow has ordered steps mapping to API endpoints
- Include links between steps (data flow)
- Reference OpenAPI spec in sources[] if available

Place at site root: `https://example.com/agents.json`

If no API exists, skip this step.

## Step 5: Configure robots.txt

Add AI bot rules to robots.txt:

```
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: CCBot
Allow: /
```

Adjust Allow/Disallow based on business needs. Reference RFC 9309.

## Step 6: Generate A2A agent card (optional)

If the site offers agent-to-agent services, create `/.well-known/agent.json` per a2a-protocol.org:

- Required fields: name, description, url, version, capabilities, skills
- Required arrays: defaultInputModes, defaultOutputModes

## Step 7: Validate

Run the validate script against the target URL:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/validate_discovery.py --url $ARGUMENTS
```

- Exit code 0 = all PASS → done
- Exit code 1 = failures exist → fix the issues, re-deploy, re-validate
- Repeat until all checks pass

## Step 8: Write back

If you encountered something non-obvious during this implementation, add a case to `references/cases/` using [_template.md](references/cases/_template.md). Especially useful:

- Platform-specific gotchas (Shopify, WordPress, Next.js, etc.)
- Format choices that worked well or poorly
- Validation errors that were tricky to fix

## References

- [philosophy.md](references/philosophy.md) — why discovery matters
- [llms-txt-guide.md](references/llms-txt-guide.md) — llms.txt spec and examples
- [agents-json-guide.md](references/agents-json-guide.md) — agents.json spec and examples
- [cases/](references/cases/) — real-world implementation cases
