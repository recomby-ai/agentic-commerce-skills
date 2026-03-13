# Identity Protocols

How agents prove who they are, who sent them, and what they're allowed to do.

---

## OAuth 2.0 Agent Extensions

**What:** IETF Internet-Drafts extending OAuth 2.0/2.1 to support AI agent delegation and authorization | **By:** Multiple authors via IETF | **Status:** Draft stage, multiple competing proposals (2025-2026)
**Spec:** [datatracker.ietf.org/doc/html/draft-oauth-ai-agents-on-behalf-of-user-02](https://datatracker.ietf.org/doc/html/draft-oauth-ai-agents-on-behalf-of-user-02) | **Related:** [AAuth draft](https://www.ietf.org/archive/id/draft-rosenberg-oauth-aauth-00.html)

- **On-Behalf-Of User**: adds `requested_actor` parameter so agents can obtain scoped tokens to act for a user
- **AAuth (Agentic Authorization)**: OAuth 2.1 extension defining an Agent Authorization Grant type
- **Authorization on Target**: adds `target_id` for granular per-resource permission management
- MCP's auth layer already uses OAuth 2.1 -- these drafts extend it for multi-agent delegation chains
- No single draft has reached consensus yet; expect consolidation through 2026
- RFC 9700 (OAuth 2.0 Security BCP, Jan 2025) provides the security baseline all drafts build on

---

## DID

**What:** A W3C standard for self-sovereign, cryptographically verifiable identifiers that work without a central registry | **By:** W3C | **Status:** v1.0 Recommendation (July 2022), v1.1 Candidate Recommendation (March 2026)
**Spec:** [w3.org/TR/did-1.1](https://www.w3.org/TR/did-1.1/) | **GitHub:** [w3c/did-core](https://github.com/w3c/did-core)

- DIDs are URIs (`did:method:identifier`) that resolve to DID Documents containing public keys and service endpoints
- No central authority -- identity is anchored on blockchains, IPFS, or other decentralized systems
- v1.1 changes: consolidated media type to `application/did`, new JSON-LD context, resolution spec split out
- Used by ANP (Agent Network Protocol) as the identity layer for agent authentication
- Research papers propose combining DIDs + Verifiable Credentials for agent trust establishment
- Comment deadline for v1.1: April 5, 2026; Recommendation expected mid-2026

---

## OIDC-A

**What:** An extension to OpenID Connect for representing, authenticating, and authorizing LLM-based agents | **By:** Subramanya Nagabhushanaradhya | **Status:** Proposal, arXiv paper (Sep 2025)
**Spec:** [arxiv.org/abs/2509.25974](https://arxiv.org/abs/2509.25974) | **GitHub:** [subramanya1997/oidc-a](https://github.com/subramanya1997/oidc-a)

- Extends OIDC Core 1.0 with agent-specific claims, endpoints, and delegation chain representation
- Defines agent attestation flow: client registration with agent metadata, auth requests with agent scope, ID tokens with agent claims
- Supports capability-based authorization -- agents get scoped permissions based on their attributes
- Builds on existing OIDC infrastructure that millions of applications already use
- Early-stage proposal -- not yet adopted by OpenID Foundation or any standards body
- Addresses a real gap: how to issue verifiable identity tokens specifically for AI agents, not just humans
