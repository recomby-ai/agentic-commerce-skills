# llms.txt — Format, Strategy, and Implementation Guide

## What is llms.txt?

llms.txt is a plain-text file at your domain root (`/llms.txt`) that tells
LLM-based AI agents about your business. Proposed by Jeremy Howard in
September 2024, it uses Markdown formatting so any LLM can parse it natively.

Think of it as robots.txt for AI comprehension — instead of controlling
crawler access, it provides understanding.

**Spec source:** https://llmstxt.org

## File Locations

| File | Purpose | Size target |
|------|---------|-------------|
| `/llms.txt` | Concise summary | Under 500 words |
| `/llms-full.txt` | Extended profile with details, FAQ, pricing | Under 3000 words |

An agent reads `llms.txt` first. If it needs more detail, it reads
`llms-full.txt`. Most agents only ever read the short version.

## Format Specification

### Required Elements

Only one element is strictly required:

```markdown
# Project or Business Name
```

The H1 heading with your name. Everything else is optional but recommended.

### Recommended Structure

```markdown
# Brand Name

> One-line tagline or description.

Brief description paragraph. 2-3 sentences. What you do, who you serve.

## Docs

- [API Reference](https://docs.example.com/api): REST API documentation
- [Getting Started](https://docs.example.com/start): Quick start guide

## Optional

- [Blog](https://example.com/blog): Company blog
- [Changelog](https://example.com/changelog): Release notes
```

### Structural Rules

1. **H1 heading** — Required. Your business or project name.
2. **Blockquote** (`> text`) — Optional. One sentence summary with key context.
3. **Body paragraphs** — Optional. Plain language, no marketing fluff.
4. **H2 sections** — Group links by category (Docs, Examples, Optional).
5. **Link lists** — Format: `- [Name](URL): Description`
6. **Optional section** — H2 titled "Optional" for secondary resources.

### What NOT to Include

- HTML tags or JavaScript
- Images, media embeds, or tracking pixels
- Marketing superlatives ("world-class", "industry-leading")
- Company history or founding stories
- Legal boilerplate (link to it instead)
- Raw JSON (use agents.json for structured data)

## Content Strategy

### The 5-Second Rule

An AI agent should understand your business within 5 seconds of reading
your llms.txt. Structure it as:

1. **Identity**: Company name and what you do
2. **Value**: What problem you solve and for whom
3. **Action**: How to learn more or get started

### Content Priority

**Always include:**
- Company/product name
- Core offering (1-2 sentences)
- Primary links (website, docs, API)

**Include if applicable:**
- Service list with one-line descriptions
- Pricing summary
- Contact method
- API documentation link

**Put in llms-full.txt:**
- Detailed service descriptions
- FAQ (5-10 common questions)
- Full pricing tiers
- Technical specifications
- Integration details

## Examples

### SaaS Product (GOOD)

```markdown
# DataFlow

> ETL pipeline builder for modern data teams.

DataFlow lets data engineers build, test, and deploy ETL pipelines
with a visual editor. Connect 200+ data sources, transform with SQL
or Python, and load into any warehouse.

## Docs

- [API Reference](https://docs.dataflow.io/api): REST API for pipeline management
- [Connectors](https://docs.dataflow.io/connectors): List of 200+ supported sources
- [Getting Started](https://docs.dataflow.io/start): 5-minute quick start

## Optional

- [Blog](https://dataflow.io/blog): Engineering blog
- [Status](https://status.dataflow.io): System status page
```

### Professional Services (GOOD)

```markdown
# Recomby.ai

> AI-powered GEO optimization for businesses.

Recomby.ai helps businesses get recommended by AI assistants like
ChatGPT, Claude, and Perplexity. We analyze how AI models perceive
your brand and optimize your content for generative engine visibility.

## Docs

- [Services](https://recomby.ai/services): GEO audit, content, monitoring, strategy
- [Contact](https://recomby.ai/contact): Get in touch

## Optional

- [Blog](https://recomby.ai/blog): GEO insights and case studies
```

### Marketing Fluff (BAD)

```markdown
# Welcome to InnovateTech Solutions — Transforming the Future!

At InnovateTech, we are passionate about delivering world-class,
cutting-edge solutions that empower businesses to thrive...
Founded in 2015 by visionary entrepreneurs...
```

**Why it fails:** No actionable info. Marketing noise wastes context window.

## Serving Configuration

### HTTP Headers

```
Content-Type: text/plain; charset=utf-8
Access-Control-Allow-Origin: *
Cache-Control: public, max-age=86400
```

### nginx

```nginx
location = /llms.txt {
    add_header Content-Type "text/plain; charset=utf-8";
    add_header Access-Control-Allow-Origin "*";
    add_header Cache-Control "public, max-age=86400";
}
```

### Vercel (vercel.json)

```json
{
  "headers": [
    {
      "source": "/llms(.*)txt",
      "headers": [
        {"key": "Content-Type", "value": "text/plain; charset=utf-8"},
        {"key": "Access-Control-Allow-Origin", "value": "*"}
      ]
    }
  ]
}
```

## Measuring Effectiveness

Check server logs for requests to `/llms.txt`. Common bot user-agents:

| Bot | Operator |
|-----|----------|
| `GPTBot` | OpenAI |
| `ClaudeBot` | Anthropic |
| `PerplexityBot` | Perplexity |
| `Google-Extended` | Google AI |

If you see traffic from these bots, your llms.txt is being read.

## Validation Checklist

- [ ] H1 heading present with business name
- [ ] Under 500 words (short version)
- [ ] No HTML, JavaScript, or tracking
- [ ] No marketing fluff
- [ ] Links use `[Name](URL)` format
- [ ] Served with correct Content-Type
- [ ] CORS header allows cross-origin access
- [ ] File accessible at domain root (`/llms.txt`)

## Update Frequency

Update when: services change, pricing changes, contact info changes,
new API endpoints launch.

No need to update for: minor website copy changes, blog posts,
team changes.

Version control llms.txt alongside your codebase.
