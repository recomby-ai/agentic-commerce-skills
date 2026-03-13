# Agentic Commerce Philosophy

## Why This Matters

Agentic commerce is the shift from humans browsing websites to AI agents
transacting on behalf of users. It changes every assumption about e-commerce.

## The Numbers

- **Human conversion rate:** 3-5% (industry average)
- **Agent conversion rate:** 15-30% (early ChatGPT Shopping data)
- **Human cart abandonment:** ~70% (Baymard Institute)
- **Agent cart abandonment:** <5% (programmatic completion)
- **Agent traffic growth:** 1,300% YoY increase in agent-initiated product queries
- **Projection:** 15-20% of e-commerce transactions agent-influenced by 2028

## What's Live in Production (2026)

### ChatGPT Instant Checkout
- Integrated in conversation flow using ACP + Stripe
- User asks "buy me X" -> agent searches, presents, confirms, pays
- Millions in monthly GMV already processing

### Google AI Mode "Buy for Me"
- Reads UCP manifests from `/.well-known/ucp`
- Uses Google Pay for payment
- Auto-discovers Shopify stores (4M+ merchants)

### Shopify Agentic Storefront
- Every Shopify store gets UCP manifest automatically
- Zero-config agent readiness for basic commerce

### Perplexity Buy
- "Buy with Pro" feature, Stripe-backed payment
- Heavy use of Schema.org product data for comparison

## The ForkPoint Case Study

E-commerce site went from $0 to $180K/month in agent-sourced revenue in 90 days:
- Week 1: Schema.org optimization (23% -> 100% product coverage)
- Week 2-3: MCP server deployment on Cloudflare Workers
- Week 4-6: ACP checkout integration
- Week 6-12: Added llms.txt, agents.json, UCP profile
- Key metric: Agent traffic had 8x higher average order value

## Agent-First vs SEO-First Thinking

| SEO Thinking | Agent-First Thinking |
|-------------|---------------------|
| Optimize for keywords | Optimize for intent |
| Build backlinks | Ensure data completeness |
| Write engaging content | Provide structured, machine-parseable data |
| Reduce bounce rate | Ensure transaction capability |
| Page load speed | API response time (<2s) |

## The Compound Effect

Sites implementing the full stack see compound returns:
1. Discovery (llms.txt, Schema.org) -> agents find you
2. Tools (MCP server) -> agents use you
3. Commerce (ACP/UCP) -> agents buy from you
4. Payment (Stripe/x402) -> money moves
5. Monitoring -> continuous optimization

Missing any layer creates a funnel leak. An agent that finds you but can't
buy from you will find a competitor it can buy from.

## Key Metrics to Track

| Metric | Target |
|--------|--------|
| Agent discovery rate | >80% of AI crawlers find your site |
| Schema completeness | >90% of products with full structured data |
| Agent conversion rate | >15% of agent sessions result in purchase |
| Agent revenue share | Growing month-over-month |
| Protocol endpoint uptime | >99.5% |

## Strategic Decision: ACP vs UCP vs Both

**Choose ACP if:** You already use Stripe, want ChatGPT Shopping traffic,
can accept 4% protocol fee, prefer stateful checkout with strong guarantees.

**Choose UCP if:** You use Shopify or want provider flexibility, want Google
AI Mode traffic, prefer zero protocol fees, want MCP/A2A transport options.

**Choose both if:** You want maximum agent coverage. Most businesses should
aim for both within 90 days of starting. The implementation cost of the
second protocol is low once the first is done.
