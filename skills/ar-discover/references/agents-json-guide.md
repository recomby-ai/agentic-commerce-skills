# agents.json — Specification, Structure, and Implementation Guide

## What is agents.json?

agents.json is an open specification (v0.1.0) by Wildcard AI that describes
how AI agents should interact with a business's APIs. Built on top of
OpenAPI, it defines executable workflows — sequences of API calls that
accomplish business tasks.

**Spec source:** https://github.com/wild-card-ai/agents-json

**File location:** `/.well-known/agents.json`

## Core Concepts

### agents.json vs. Other Discovery Files

| File | Describes | Audience |
|------|-----------|----------|
| llms.txt | Who you are | Any LLM |
| agents.json | How to use your API | Agentic frameworks |
| A2A agent card | What your agent can do | Other agents |
| Schema.org | Your business for search | Search engines + AI |

agents.json is for businesses with APIs. If you don't have an API,
you don't need agents.json.

## Schema Structure

```json
{
  "version": "0.1.0",
  "info": {
    "title": "Business Name API",
    "description": "What agents can do with this API"
  },
  "sources": [
    {
      "id": "main-api",
      "type": "openapi",
      "url": "https://api.example.com/openapi.json"
    }
  ],
  "flows": [...],
  "links": [...]
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Spec version (currently `"0.1.0"`) |
| `info.title` | string | API/business name |
| `info.description` | string | What agents can accomplish |
| `flows` | array | List of executable workflows |

### Sources

Sources reference API definitions that flows operate against.

```json
{
  "id": "commerce-api",
  "type": "openapi",
  "url": "https://api.example.com/openapi.json"
}
```

Supported types: `openapi`, `graphql`, `grpc`

### Flows

A flow is a sequence of API calls that accomplish a business task.

```json
{
  "id": "search_and_buy",
  "name": "Search and Purchase Product",
  "description": "Find a product by query and complete purchase",
  "steps": [...],
  "inputs": {...},
  "outputs": {...}
}
```

**Flow fields:**
- `id` — Unique identifier (required)
- `name` — Human-readable name (required)
- `description` — What this flow accomplishes; agents match intent here
- `steps` — Ordered array of API operations (required)
- `inputs` — Required/optional inputs from the user or agent
- `outputs` — What the flow produces on completion

### Steps

Each step maps to an API operation from a source.

```json
{
  "id": "search",
  "operation": "searchProducts",
  "source": "commerce-api",
  "parameters": {
    "query": "{{input.search_query}}",
    "limit": 5
  },
  "output": "search_results",
  "requires_confirmation": false
}
```

**Step fields:**
- `id` — Step identifier, referenced in links (required)
- `operation` — Operation ID from OpenAPI source (required)
- `source` — Which source to call (required)
- `parameters` — Parameter mapping with template syntax
- `output` — Variable name for storing response
- `requires_confirmation` — Whether agent should confirm with user first

### Template Syntax

Parameters use double-brace templates:
- `{{input.field}}` — References a flow input
- `{{step_output.field}}` — References a previous step's output
- `{{value | default: fallback}}` — Default values

### Links

Links make data dependencies between steps explicit.

```json
{
  "from": "search.output.products[].id",
  "to": "select.parameters.product_id",
  "description": "Agent selects a product from search results"
}
```

### Flow Inputs and Outputs

```json
"inputs": {
  "search_query": {
    "type": "string",
    "required": true,
    "description": "What to search for"
  },
  "quantity": {
    "type": "integer",
    "required": false,
    "default": 1
  }
},
"outputs": {
  "order_id": "{{checkout.order.id}}",
  "total": "{{checkout.amount_total}}"
}
```

## Common Flow Templates

| Business Type | Suggested Flows |
|--------------|----------------|
| E-commerce | search_products, view_product, add_to_cart, checkout |
| SaaS | check_pricing, create_trial, subscribe, manage_account |
| Booking | check_availability, make_reservation, modify_booking |
| Service | describe_services, get_quote, schedule, check_status |
| Content | search_content, access_content, subscribe |

## Complete Example

```json
{
  "version": "0.1.0",
  "info": {
    "title": "Acme Store API",
    "description": "Agent-consumable product search and purchase"
  },
  "sources": [
    {
      "id": "store-api",
      "type": "openapi",
      "url": "https://api.acme.com/openapi.json"
    }
  ],
  "flows": [
    {
      "id": "search_and_buy",
      "name": "Search and Purchase",
      "description": "Find a product and complete purchase",
      "steps": [
        {
          "id": "search",
          "operation": "searchProducts",
          "source": "store-api",
          "parameters": {"query": "{{input.query}}", "limit": 5},
          "output": "results"
        },
        {
          "id": "add_to_cart",
          "operation": "addToCart",
          "source": "store-api",
          "parameters": {
            "product_id": "{{results.products[0].id}}",
            "quantity": "{{input.quantity | default: 1}}"
          },
          "output": "cart"
        },
        {
          "id": "checkout",
          "operation": "createCheckout",
          "source": "store-api",
          "parameters": {
            "cart_id": "{{cart.id}}",
            "email": "{{input.email}}"
          },
          "output": "order",
          "requires_confirmation": true,
          "confirmation_message": "Complete purchase for {{cart.total}}?"
        }
      ],
      "inputs": {
        "query": {"type": "string", "required": true},
        "quantity": {"type": "integer", "default": 1},
        "email": {"type": "string", "required": true}
      },
      "outputs": {
        "order_id": "{{order.id}}",
        "total": "{{order.total}}"
      }
    }
  ],
  "links": [
    {
      "from": "search.output.products[].id",
      "to": "add_to_cart.parameters.product_id"
    },
    {
      "from": "add_to_cart.output.id",
      "to": "checkout.parameters.cart_id"
    }
  ]
}
```

## Validation Checklist

1. **Schema compliance** — Required fields present, correct types
2. **Source reachability** — Referenced OpenAPI specs are accessible
3. **Operation existence** — All referenced operations exist in sources
4. **Link validity** — All link from/to paths resolve correctly
5. **Input completeness** — All template variables have corresponding inputs
6. **Flow connectivity** — Steps form a valid DAG (no circular dependencies)

## Generating from OpenAPI

The `generate_agents_json.py` script automates generation:

1. Parse OpenAPI spec to extract endpoints
2. Group related endpoints into flows
3. Map parameters using template syntax
4. Generate links between dependent steps
5. Validate output against the agents.json schema

For best results, ensure your OpenAPI spec has:
- Descriptive `operationId` values
- Clear `summary` fields on endpoints
- Well-defined request/response schemas

## Deployment

Place at `/.well-known/agents.json` on your domain.

### nginx

```nginx
location = /.well-known/agents.json {
    add_header Content-Type "application/json; charset=utf-8";
    add_header Access-Control-Allow-Origin "*";
}
```

### Static hosting

Upload to your `.well-known/` directory. Most static hosts (Vercel,
Netlify, Cloudflare Pages) serve `.well-known/` paths automatically.

## Design Principles

1. **Build on OpenAPI** — Don't reinvent endpoint descriptions
2. **Optimize for LLMs** — Descriptions should be clear and unambiguous
3. **Stateless flows** — The calling agent handles orchestration
4. **Minimal API changes** — Should work with existing APIs as-is
