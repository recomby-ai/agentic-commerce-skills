# Discovery Protocols

How agents and AI systems find, understand, and connect to websites and other agents.

---

## llms.txt

**What:** A Markdown file at `/llms.txt` that tells LLMs where a site's most useful content lives | **By:** Jeremy Howard / Answer.AI | **Status:** Community proposal, 780+ adopters, not an official standard
**Spec:** [llmstxt.org](https://llmstxt.org/) | **GitHub:** [llmstxt/llmstxt.org](https://github.com/jxnl/llmstxt)

- Simple Markdown file with H1 header, summary blockquote, and links to key resources
- Adopted by Anthropic, Cloudflare, Vercel, Cursor, Mintlify-hosted docs, and 780+ sites
- Complementary to `robots.txt` -- tells AI systems what to read, not what to avoid
- Google has explicitly stated it does not support llms.txt (Gary Illyes, July 2025)
- Variants include `llms-full.txt` for complete content dumps

---

## A2A Agent Cards

**What:** JSON metadata files that advertise an agent's capabilities, skills, and auth requirements | **By:** Google / A2A Project | **Status:** Part of A2A v0.3 spec (July 2025), Linux Foundation
**Spec:** [a2a-protocol.org](https://a2a-protocol.org/latest/) | **GitHub:** [a2aproject/A2A](https://github.com/a2aproject/A2A)

- JSON document containing agent name, description, version, endpoint URL, supported modalities, and auth schemes
- Serves as a "business card" for agent-to-agent discovery -- clients fetch cards to find the best agent for a task
- v0.3 added signed security cards for cryptographic identity verification
- Hosted at a well-known URL or registered in a directory; discovered via HTTP GET
- Part of the broader A2A protocol -- see [communication.md](communication.md#a2a) for the full protocol

---

## NLWeb

**What:** An open-source protocol that turns any website into an AI-queryable endpoint using Schema.org and MCP | **By:** Microsoft (led by Schema.org creator RV Guha) | **Status:** Open-source, announced Build 2025
**Spec:** [nlweb.ai](https://nlweb.ai/) | **GitHub:** [microsoft/NLWeb](https://github.com/microsoft/NLWeb)

- Builds on existing feeds (RSS, Atom, JSON Feed) plus Schema.org vocabulary -- no new data format needed
- Every NLWeb instance is also an MCP server, making sites discoverable to agents in the MCP ecosystem
- LLM-agnostic: works with any model as the query engine
- Early adopters include Tripadvisor, Eventbrite, Allrecipes, O'Reilly Media, Shopify
- Microsoft CTO Kevin Scott: "Think about it like HTML for the agentic web"

---

## Schema.org

**What:** The web's standard vocabulary for structured data, increasingly critical for AI agent discovery | **By:** Google, Microsoft, Yahoo, Yandex | **Status:** Active, continuously updated
**Spec:** [schema.org](https://schema.org/) | **GitHub:** [schemaorg/schemaorg](https://github.com/schemaorg/schemaorg)

- JSON-LD is the recommended format -- every AI engine tested prefers it over Microdata or RDFa
- Structured data increases AI citations by 30-40% compared to pages without markup
- NLWeb is built entirely on Schema.org vocabulary, making it the de facto foundation for agentic discovery
- Key types for agents: `Organization`, `Product`, `Service`, `WebAPI`, `Action`, `SoftwareApplication`
- Not agent-specific by design, but provides the semantic layer that agent protocols build upon
