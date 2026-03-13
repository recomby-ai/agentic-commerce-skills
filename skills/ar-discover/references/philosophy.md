# Discovery Philosophy: Why Being Found by AI Agents Matters

## The Shift

The web was built for browsers. Humans type URLs, click links, read pages.
AI agents don't work this way. They need structured, machine-parseable
declarations of who you are and what you can do — delivered in as few
HTTP requests as possible.

If an agent can't understand your business in 3 requests or fewer,
it moves on to a competitor who made it easy.

## Two Layers of Discovery

### Layer 1: Identity (llms.txt)

llms.txt is the simplest possible answer to "who are you?"

A plain text file at your domain root. Any LLM can read it with zero
parsing overhead. No schema validation, no API keys, no authentication.
Just: name, offering, contact.

This is the minimum viable discovery. Every business should have one.
It takes 10 minutes to create.

**Who reads it:** ChatGPT, Claude, Perplexity, Gemini, any LLM-based agent.

### Layer 2: Capability (agents.json)

agents.json answers "what can I do with your API?"

It declares executable workflows: sequences of API calls an agent can
perform to accomplish business tasks. Built on top of OpenAPI, it bridges
the gap between "here are our endpoints" and "here is how to actually
buy something from us."

This layer only matters if you have an API. If you don't, skip it.

**Who reads it:** Agentic frameworks, autonomous agents, commerce agents.

## The 3-Request Test

After deploying discovery files, verify with this mental model:

1. `GET /llms.txt` — Agent knows who you are and what you do
2. `GET /.well-known/agents.json` — Agent knows which API calls to make
3. First API call — Agent starts executing a workflow

If an agent needs more than 3 requests to understand your business and
begin interacting with it, your discovery setup is too complex.

## What Discovery Is NOT

**Not marketing.** Agents don't care about your founding story, press
mentions, or awards. They want facts: what you sell, what it costs,
how to buy it programmatically.

**Not documentation.** Full API docs belong in your developer portal.
Discovery files are the index card, not the encyclopedia.

**Not a replacement for good APIs.** Discovery files point agents to
your API. If the API itself is broken, discovery won't help.

## Priority Order

1. **llms.txt** — Essential. 10 minutes. Every LLM reads it.
2. **Schema.org JSON-LD** — High. 30 minutes. Search + AI agents.
3. **agents.json** — Medium. 1-2 hours. Requires API.
4. **A2A Agent Card** — Lower. For agent-to-agent communication.

Start with llms.txt. Add layers as your infrastructure matures.

## The Discovery Lifecycle

**Week 1:** Deploy llms.txt. Check server logs for bot traffic.
**Month 1:** Add agents.json if you have stable API endpoints.
**Quarter 1:** Monitor which agents are consuming your files. Iterate.

Discovery is not a one-time deploy. As your services change, your
discovery files must change too. Version control them alongside your
codebase. Review them quarterly.

## When NOT to Bother

- **Internal tools**: Not meant to be found. Skip discovery.
- **Personal blogs**: llms.txt alone is enough.
- **Shopify stores**: Shopify handles commerce. Just add llms.txt for brand visibility.
- **Pre-API startups**: llms.txt only. Add agents.json when endpoints stabilize.

## The Bottom Line

AI agents are the new browsers. They'll bring you customers — if they
can find you. Discovery files are the front door. Make sure yours is open.
