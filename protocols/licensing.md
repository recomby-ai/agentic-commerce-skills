# Licensing Protocols

How publishers define what AI systems can and cannot do with their content.

---

## RSL

**What:** A machine-readable licensing standard that lets publishers define usage terms and pricing for AI crawling and inference | **By:** RSL Standard (co-created by RSS co-creator) | **Status:** v1.0 official spec (Dec 2025), 1500+ endorsing organizations
**Spec:** [rslstandard.org](https://rslstandard.org/) | **GitHub:** [rsl-standard](https://github.com/nichochar/rsl) (community reference)

- Built on RSS format -- extends `robots.txt` yes/no blocking with granular licensing terms
- Usage categories: `ai-all`, `ai-input`, `ai-index` -- publishers control training vs search vs inference separately
- Payment models: pay-per-crawl, pay-per-inference, and a "contribution" option for nonprofits (with Creative Commons)
- Endorsed by Reddit, Yahoo, Quora, Medium, Stack Overflow, The Associated Press, O'Reilly Media
- Infrastructure support from Cloudflare, Akamai, Fastly
- Addresses the core tension: publishers want compensation for AI training data, not just blocking

---

## ai.txt

**What:** A proposed domain-specific language for declaring what kinds of AI interactions a site allows, beyond simple crawl permissions | **By:** Community proposal | **Status:** Early proposal, not yet widely adopted
**Spec:** No formal spec published | **Reference:** [Community discussion](https://dev.to/astro-official/new-ai-web-standards-and-scraping-trends-in-2026-rethinking-robotstxt-3730)

- Goes beyond `robots.txt` URL-level blocking to describe permitted AI actions per content type
- Example: allow summarization of articles but disallow image extraction; permit indexing but block training
- More granular than llms.txt (which guides AI to content) or robots.txt (which blocks crawlers)
- Not yet standardized -- no formal spec body, no official website, no significant adoption
- RSL has emerged as the more mature alternative for the same problem space
- May converge with RSL or remain a niche complement for action-level (vs content-level) permissions
