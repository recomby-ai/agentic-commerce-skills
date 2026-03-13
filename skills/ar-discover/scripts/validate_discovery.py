#!/usr/bin/env python3
"""Validate agent discovery endpoints on a live URL.

Checks per official specs:
  - llms.txt (llmstxt.org spec): H1 required, blockquote optional, H2 file lists
  - agents.json (wild-card-ai spec v0.1.0): flows[], links optional, OpenAPI-based
  - robots.txt: AI bot User-agent rules (GPTBot, ChatGPT-User, CCBot, etc.)
  - sitemap.xml: standard sitemap protocol
  - .well-known/agent.json (A2A protocol): agent card per a2a-protocol.org spec

Usage:
    python validate_discovery.py --url https://example.com
    python validate_discovery.py --url https://example.com --json
    python validate_discovery.py --url https://example.com --verbose
"""

import argparse
import json
import re
import sys

try:
    import requests
except ImportError:
    print("ERROR: 'requests' required. pip install requests", file=sys.stderr)
    sys.exit(1)

HEADERS = {"User-Agent": "ar-discover/1.0 validator"}
TIMEOUT = 12

# AI bot User-Agent strings commonly found in robots.txt
AI_BOTS = [
    "GPTBot", "ChatGPT-User", "Google-Extended", "anthropic-ai",
    "Claude-Web", "CCBot", "PerplexityBot", "Bytespider",
    "cohere-ai", "Applebot-Extended",
]


class Result:
    def __init__(self):
        self.checks = []

    def add(self, target, check, status, message=""):
        self.checks.append({
            "target": target, "check": check,
            "status": status, "message": message,
        })

    @property
    def passed(self):
        return sum(1 for c in self.checks if c["status"] == "PASS")

    @property
    def failed(self):
        return sum(1 for c in self.checks if c["status"] == "FAIL")

    @property
    def warnings(self):
        return sum(1 for c in self.checks if c["status"] == "WARN")

    @property
    def infos(self):
        return sum(1 for c in self.checks if c["status"] == "INFO")

    def to_dict(self):
        return {
            "checks": self.checks,
            "summary": {
                "total": len(self.checks), "passed": self.passed,
                "failed": self.failed, "warnings": self.warnings,
                "info": self.infos,
            },
        }

    def print_report(self, verbose=False):
        icons = {"PASS": "+", "FAIL": "x", "WARN": "!", "INFO": "i"}
        for c in self.checks:
            icon = icons.get(c["status"], "?")
            line = f"  [{icon}] {c['target']}: {c['check']}"
            if c["message"]:
                line += f" -- {c['message']}"
            print(line)
        print()
        print(f"Result: {self.passed}/{len(self.checks)} passed, "
              f"{self.failed} failed, {self.warnings} warnings")


def fetch(url):
    """GET url -> (status_code|None, headers_dict, text_or_error)."""
    try:
        resp = requests.get(url, timeout=TIMEOUT, allow_redirects=True,
                            headers=HEADERS)
        return resp.status_code, dict(resp.headers), resp.text
    except requests.RequestException as e:
        return None, {}, str(e)


# ---- llms.txt (spec: llmstxt.org) ----

def check_llms_txt(base, result, verbose):
    """Validate per llmstxt.org spec:
    - REQUIRED: H1 with project/site name (the ONLY required element)
    - OPTIONAL: blockquote summary, descriptive paragraphs/lists (no headings),
                H2 file-list sections with [name](url) : notes format
    - H2 "Optional" section = special meaning (skippable URLs)
    - No headings deeper than H2
    """
    url = base + "/llms.txt"
    status, headers, body = fetch(url)
    if status is None:
        result.add("llms.txt", "accessible", "FAIL", f"Connection error: {body}")
        return
    if status == 404:
        result.add("llms.txt", "accessible", "WARN", "Not found (404)")
        return
    if status != 200:
        result.add("llms.txt", "accessible", "FAIL", f"HTTP {status}")
        return
    result.add("llms.txt", "accessible", "PASS", f"{len(body)} bytes")

    lines = body.split("\n")

    # REQUIRED per spec: H1 heading (the ONLY required element)
    h1_lines = [l for l in lines if re.match(r"^# (?!#)", l)]
    if h1_lines:
        result.add("llms.txt", "H1 heading (REQUIRED per llmstxt.org)", "PASS",
                    h1_lines[0][:80])
    else:
        result.add("llms.txt", "H1 heading (REQUIRED per llmstxt.org)", "FAIL",
                    "Missing '# Name' -- the only required element per spec")

    # OPTIONAL: blockquote summary
    has_bq = any(l.strip().startswith("> ") for l in lines)
    if has_bq:
        result.add("llms.txt", "blockquote summary (optional per spec)", "PASS")
    else:
        result.add("llms.txt", "blockquote summary (optional per spec)", "WARN",
                    "No '> summary' blockquote found")

    # Spec: no headings deeper than H2
    deep_headings = [l for l in lines if re.match(r"^#{3,}\s", l)]
    if deep_headings:
        result.add("llms.txt", "heading depth (spec: H1 and H2 only)", "WARN",
                    f"Found {len(deep_headings)} headings deeper than H2")
    else:
        result.add("llms.txt", "heading depth (spec: H1 and H2 only)", "PASS")

    # H2 file-list sections
    h2_sections = [l for l in lines if re.match(r"^## ", l)]
    if h2_sections:
        section_names = [l[3:].strip() for l in h2_sections]
        result.add("llms.txt", "H2 file-list sections", "PASS",
                    f"{len(h2_sections)}: {', '.join(section_names[:5])}")
        # Spec: "Optional" section has special meaning
        if "Optional" in section_names:
            result.add("llms.txt", "'Optional' section (spec: skippable URLs)", "INFO",
                        "Present -- URLs here can be skipped for shorter context")
    else:
        result.add("llms.txt", "H2 file-list sections", "INFO",
                    "No H2 sections (optional per spec)")

    # File list format per spec: [name](url) : notes
    md_links = re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", body)
    if md_links:
        result.add("llms.txt", "markdown links in file lists", "PASS",
                    f"{len(md_links)} links")

    # Community best practice: keep index under ~500 words / 3000 tokens
    wc = len(body.split())
    if wc > 500:
        result.add("llms.txt", "conciseness (best practice: <500 words)", "WARN",
                    f"{wc} words")
    else:
        result.add("llms.txt", "conciseness (best practice: <500 words)", "PASS",
                    f"{wc} words")

    # Content-type
    ct = headers.get("Content-Type", headers.get("content-type", ""))
    if "text/plain" in ct or "text/markdown" in ct:
        result.add("llms.txt", "content-type", "PASS", ct.split(";")[0])
    else:
        result.add("llms.txt", "content-type", "INFO",
                    f"Got '{ct}' -- text/plain recommended")


# ---- agents.json (spec: wild-card-ai/agents-json v0.1.0) ----

def check_agents_json(base, result, verbose):
    """Validate per agents.json spec v0.1.0 (github.com/wild-card-ai/agents-json):
    - Built on OpenAPI standard
    - Core structure: flows[] (contracts for series of API calls)
    - Flows contain steps referencing OpenAPI operations
    - Links describe how actions stitch together
    """
    url = base + "/agents.json"
    status, headers, body = fetch(url)
    if status is None:
        result.add("agents.json", "accessible", "FAIL", f"Connection error: {body}")
        return
    if status == 404:
        result.add("agents.json", "accessible", "WARN", "Not found (404)")
        return
    if status != 200:
        result.add("agents.json", "accessible", "FAIL", f"HTTP {status}")
        return
    result.add("agents.json", "accessible", "PASS")

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        result.add("agents.json", "valid JSON", "FAIL", str(e))
        return
    result.add("agents.json", "valid JSON", "PASS")

    # flows[] -- core concept per spec: contracts for API call sequences
    if "flows" in data and isinstance(data["flows"], list):
        result.add("agents.json", "flows (spec: API call contracts)", "PASS",
                    f"{len(data['flows'])} flows")
        for i, flow in enumerate(data["flows"][:5]):
            if "id" not in flow and "name" not in flow:
                result.add("agents.json", f"flow[{i}] identifier", "WARN",
                            "Flow missing 'id' or 'name'")
            if "steps" in flow and isinstance(flow["steps"], list):
                if verbose:
                    result.add("agents.json", f"flow[{i}] steps", "PASS",
                                f"{len(flow['steps'])} steps")
    else:
        result.add("agents.json", "flows (spec: API call contracts)", "FAIL",
                    "Missing or invalid 'flows' array -- core spec requirement")

    # links -- optional, describe action connections
    if "links" in data:
        result.add("agents.json", "links (action stitching)", "PASS",
                    f"{len(data['links'])} links")

    # sources -- references to OpenAPI specs
    if "sources" in data and isinstance(data["sources"], list):
        result.add("agents.json", "sources (OpenAPI refs)", "PASS",
                    f"{len(data['sources'])} sources")

    if "version" in data:
        result.add("agents.json", "version", "PASS", data["version"])


# ---- robots.txt (RFC 9309) ----

def check_robots_txt(base, result, verbose):
    """Check for AI bot rules per standard robots.txt spec."""
    url = base + "/robots.txt"
    status, headers, body = fetch(url)
    if status is None:
        result.add("robots.txt", "accessible", "FAIL", f"Connection error: {body}")
        return
    if status == 404:
        result.add("robots.txt", "accessible", "WARN", "Not found (404)")
        return
    if status != 200:
        result.add("robots.txt", "accessible", "FAIL", f"HTTP {status}")
        return
    result.add("robots.txt", "accessible", "PASS")

    body_lower = body.lower()
    found_bots = []
    blocked_bots = []

    for bot in AI_BOTS:
        if bot.lower() in body_lower:
            found_bots.append(bot)
            # Parse the rules block for this User-agent
            pattern = re.compile(
                r"user-agent:\s*" + re.escape(bot.lower()) +
                r"\s*\n((?:(?!user-agent:).)*)",
                re.DOTALL
            )
            match = pattern.search(body_lower)
            if match:
                block = match.group(1)
                # Full site block: "Disallow: /" on its own line
                if re.search(r"disallow:\s*/\s*$", block, re.M):
                    blocked_bots.append(bot)

    if found_bots:
        result.add("robots.txt", "AI bot rules", "PASS",
                    f"Rules for: {', '.join(found_bots)}")
        if blocked_bots:
            result.add("robots.txt", "AI bots blocked", "WARN",
                        f"Fully blocked: {', '.join(blocked_bots)}")
        else:
            result.add("robots.txt", "AI bots allowed", "PASS",
                        "No AI bots fully blocked")
    else:
        result.add("robots.txt", "AI bot rules", "INFO",
                    "No specific AI bot User-agent rules found")

    # Sitemap directive
    if "sitemap:" in body_lower:
        sitemaps = re.findall(r"sitemap:\s*(https?://\S+)", body, re.I)
        result.add("robots.txt", "Sitemap directive", "PASS",
                    sitemaps[0][:80] if sitemaps else "found")
    else:
        result.add("robots.txt", "Sitemap directive", "INFO",
                    "No Sitemap directive")


# ---- sitemap.xml (sitemaps.org protocol) ----

def check_sitemap(base, result, verbose):
    url = base + "/sitemap.xml"
    status, headers, body = fetch(url)
    if status is None:
        result.add("sitemap.xml", "accessible", "FAIL", f"Connection error: {body}")
        return
    if status == 404:
        result.add("sitemap.xml", "accessible", "WARN", "Not found (404)")
        return
    if status != 200:
        result.add("sitemap.xml", "accessible", "FAIL", f"HTTP {status}")
        return

    if "<urlset" in body or "<sitemapindex" in body:
        url_count = body.count("<loc>")
        result.add("sitemap.xml", "accessible", "PASS",
                    f"Valid XML sitemap, {url_count} URLs")
    else:
        result.add("sitemap.xml", "accessible", "WARN",
                    "HTTP 200 but not a standard XML sitemap")


# ---- .well-known/agent.json (A2A protocol, a2a-protocol.org) ----

def check_agent_card(base, result, verbose):
    """Validate per A2A protocol spec (a2a-protocol.org):
    REQUIRED: name, description, url, version, capabilities,
              defaultInputModes, defaultOutputModes, skills
    OPTIONAL: provider, iconUrl, documentationUrl, securitySchemes, security
    """
    url = base + "/.well-known/agent.json"
    status, headers, body = fetch(url)
    if status is None:
        result.add("agent.json (A2A)", "accessible", "FAIL",
                    f"Connection error: {body}")
        return
    if status == 404:
        result.add("agent.json (A2A)", "accessible", "WARN", "Not found (404)")
        return
    if status != 200:
        result.add("agent.json (A2A)", "accessible", "FAIL", f"HTTP {status}")
        return
    result.add("agent.json (A2A)", "accessible", "PASS")

    try:
        card = json.loads(body)
    except json.JSONDecodeError as e:
        result.add("agent.json (A2A)", "valid JSON", "FAIL", str(e))
        return
    result.add("agent.json (A2A)", "valid JSON", "PASS")

    # REQUIRED fields per A2A spec
    required_fields = ["name", "description", "url", "version", "skills"]
    for field in required_fields:
        if field in card:
            val = card[field]
            if field == "skills" and isinstance(val, list):
                result.add("agent.json (A2A)", f"{field} (REQUIRED per A2A spec)",
                            "PASS", f"{len(val)} skills")
            else:
                result.add("agent.json (A2A)", f"{field} (REQUIRED per A2A spec)",
                            "PASS", str(val)[:60])
        else:
            result.add("agent.json (A2A)", f"{field} (REQUIRED per A2A spec)", "FAIL",
                        "Missing -- required per A2A protocol spec")

    # REQUIRED per spec but less critical for basic agent cards
    for field in ["capabilities", "defaultInputModes", "defaultOutputModes"]:
        if field in card:
            result.add("agent.json (A2A)", f"{field} (REQUIRED per A2A spec)", "PASS")
        else:
            result.add("agent.json (A2A)", f"{field} (REQUIRED per A2A spec)", "WARN",
                        "Missing -- required per A2A spec")

    # OPTIONAL but recommended
    if "securitySchemes" in card or "security" in card:
        result.add("agent.json (A2A)", "authentication config (recommended)", "PASS")
    else:
        result.add("agent.json (A2A)", "authentication config (recommended)", "INFO",
                    "No securitySchemes -- not recommended for production")


# ---- main ----

def main():
    parser = argparse.ArgumentParser(
        description="Validate agent discovery endpoints on a live URL "
                    "(checks per llmstxt.org, agents.json, A2A, robots.txt specs)")
    parser.add_argument("--url", required=True,
                        help="Base URL to check (e.g. https://example.com)")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output results as JSON")
    parser.add_argument("--verbose", action="store_true",
                        help="Show extra detail per check")
    args = parser.parse_args()

    url = args.url.rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    result = Result()

    if not args.json_output:
        print(f"Checking discovery endpoints: {url}\n")

    check_llms_txt(url, result, args.verbose)
    check_agents_json(url, result, args.verbose)
    check_robots_txt(url, result, args.verbose)
    check_sitemap(url, result, args.verbose)
    check_agent_card(url, result, args.verbose)

    if args.json_output:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        result.print_report(verbose=args.verbose)

    sys.exit(1 if result.failed > 0 else 0)


if __name__ == "__main__":
    main()
