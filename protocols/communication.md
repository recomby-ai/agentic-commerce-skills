# Communication Protocols

How agents talk to tools, other agents, and user-facing applications.

---

## MCP

**What:** A protocol for connecting AI models to external tools, data sources, and context | **By:** Anthropic (donated to Linux Foundation AAIF, Dec 2025) | **Status:** Active, AAIF founding project, TypeScript SDK v2 expected Q1 2026
**Spec:** [modelcontextprotocol.io](https://modelcontextprotocol.io/) | **GitHub:** [modelcontextprotocol](https://github.com/modelcontextprotocol)

- Standardizes how LLMs connect to tools, databases, APIs, and file systems via a client-server architecture
- JSON-RPC 2.0 over stdio or HTTP with SSE; supports tools, resources, prompts, and sampling
- Nov 2025 spec added async operations, stateless mode, server identity, and official extensions
- AAIF co-founded by Anthropic, OpenAI, and Block; backed by Google, Microsoft, AWS, Cloudflare
- Supported by Claude, ChatGPT, Gemini, Cursor, Windsurf, VS Code, and hundreds of community servers
- Often called "the USB-C of AI" -- the most widely adopted agent protocol as of early 2026

---

## A2A

**What:** An open protocol for agent-to-agent communication and task delegation across frameworks | **By:** Google (now Linux Foundation) | **Status:** v0.3 (July 2025), 150+ partner organizations
**Spec:** [a2a-protocol.org](https://a2a-protocol.org/latest/) | **GitHub:** [a2aproject/A2A](https://github.com/a2aproject/A2A)

- Enables agents from different vendors/frameworks to discover, authenticate, and delegate tasks to each other
- Built on HTTP, SSE, and JSON-RPC 2.0; v0.3 added gRPC support
- Four core capabilities: capability discovery (Agent Cards), task management (lifecycle states), collaboration (context sharing), UX negotiation
- Supports long-running tasks (hours/days) with streaming updates and human-in-the-loop
- Partners include Atlassian, Salesforce, SAP, LangChain, MongoDB, ServiceNow, and 150+ others
- Complementary to MCP: MCP connects models to tools, A2A connects agents to agents

---

## AG-UI

**What:** An event-based protocol for connecting agent backends to frontend user interfaces | **By:** CopilotKit | **Status:** Active, open-source, growing adoption
**Spec:** [docs.ag-ui.com](https://docs.ag-ui.com/) | **GitHub:** [ag-ui-protocol/ag-ui](https://github.com/ag-ui-protocol/ag-ui)

- Streams JSON events (messages, tool calls, state patches, lifecycle signals) over HTTP or binary channel
- Fills the gap between MCP (model-to-tool) and A2A (agent-to-agent) by handling agent-to-user interaction
- Supports real-time streaming, shared state between agent and frontend, frontend tool execution, and custom events
- Integrations with Microsoft Agent Framework, Oracle Agent Spec, Pydantic AI, and others
- Lightweight and transport-agnostic -- works with any agent framework on the backend

---

## ANP

**What:** A three-layer protocol for building open, decentralized agent networks at internet scale | **By:** ANP Open Source Community | **Status:** Technical white paper (July 2025), MIT License
**Spec:** [agent-network-protocol.com](https://agent-network-protocol.com/specs/) | **GitHub:** [agent-network-protocol/AgentNetworkProtocol](https://github.com/agent-network-protocol/AgentNetworkProtocol)

- Three-layer architecture: identity + encrypted comms, meta-protocol negotiation, application protocol
- Uses DIDs (Decentralized Identifiers) for agent identity and cryptographic authentication
- Runs on existing infrastructure (DNS, HTTPS, web servers) -- no new network layer required
- Discovery via capability files hosted at specific URLs; authentication via DID signatures
- IETF Internet-Draft submitted (`draft-zyyhl-agent-networks-framework`)
- Designed for billions of agents; more ambitious in scope than A2A but earlier in adoption
