#!/usr/bin/env python3
"""
audit_full.py -- Comprehensive agent-readiness audit across 6 dimensions.

Fetches a real URL and runs all checks: Discovery, Readability, Data Quality,
MCP/API, Commerce, Payment. Every check makes real HTTP requests.

Usage:
  python audit_full.py --url https://example.com
  python audit_full.py --url https://example.com --json
  python audit_full.py --url https://example.com --json > report.json
  python audit_full.py --url https://example.com --verbose
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

try:
    import requests
except ImportError:
    print("Error: 'requests' required. pip install requests", file=sys.stderr)
    sys.exit(1)

VERSION = "2.0.0"
UA = f"ar-audit/{VERSION}"
TIMEOUT = 12

GRADE_THRESHOLDS = [(90, "A"), (75, "B"), (60, "C"), (40, "D"), (0, "F")]

# AI bots whose crawl access we check in robots.txt
AI_BOTS = ["GPTBot", "Google-Extended", "ClaudeBot"]

# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------
_cache: dict = {}


def fetch(url: str, timeout: int = TIMEOUT) -> dict:
    if url in _cache:
        return _cache[url]
    try:
        t0 = time.time()
        r = requests.get(url, timeout=timeout, allow_redirects=True,
                         headers={"User-Agent": UA})
        result = {"status": r.status_code, "body": r.text[:200_000],
                  "headers": dict(r.headers), "time": round(time.time() - t0, 3)}
    except Exception as e:
        result = {"status": 0, "body": "", "headers": {}, "time": 0, "error": str(e)}
    _cache[url] = result
    return result


def get(base: str, path: str) -> dict:
    return fetch(urljoin(base, path))


def chk(name, pts, mx, status, detail):
    return {"name": name, "points": pts, "max": mx, "status": status, "detail": detail}


def grade_of(score):
    for t, g in GRADE_THRESHOLDS:
        if score >= t:
            return g
    return "F"


# --------------------------------------------------------------------------
# 1. Discovery  (20 pts)
# --------------------------------------------------------------------------
def audit_discovery(base, verbose):
    checks = []

    # 1a  llms.txt  (5 pts) -- spec: llmstxt.org
    #   Required: H1 title. Optional: blockquote summary, H2 file-list sections
    d = get(base, "/llms.txt")
    found = d["status"] == 200 and len(d["body"].strip()) > 10
    pts = 0; parts = []
    if found:
        body = d["body"]
        has_h1 = bool(re.search(r"^#\s+.+", body, re.MULTILINE))
        has_h2 = bool(re.search(r"^##\s+.+", body, re.MULTILINE))
        has_bq = bool(re.search(r"^>\s+.+", body, re.MULTILINE))
        has_links = bool(re.search(r"\[.+?\]\(.+?\)", body))
        if has_h1:
            pts = 3; parts.append("has H1 (required)")
        if has_h2 and has_links:
            pts += 1; parts.append("has H2 file-list sections")
        if has_bq:
            pts += 1; parts.append("has blockquote summary")
        if not has_h1:
            pts = 1; parts = ["found but missing required H1 per llmstxt.org spec"]
    else:
        parts.append("Missing -- see llmstxt.org")
    checks.append(chk("llms.txt", pts, 5,
                       "pass" if pts >= 4 else ("partial" if pts else "fail"),
                       "; ".join(parts)))

    # 1b  agents.json  (5 pts)
    d = get(base, "/agents.json")
    pts = 0; detail = "Missing"
    if d["status"] == 200:
        try:
            aj = json.loads(d["body"])
            if isinstance(aj, dict):
                known = {"version", "flows", "endpoints", "capabilities", "name", "agents"}
                overlap = known & set(aj.keys())
                if overlap:
                    pts = 5; detail = f"Valid, fields: {', '.join(sorted(overlap))}"
                else:
                    pts = 2; detail = f"Valid JSON but no recognised fields (has: {', '.join(list(aj.keys())[:5])})"
            elif isinstance(aj, list):
                pts = 3; detail = f"Valid JSON array with {len(aj)} entries"
            else:
                pts = 1; detail = "Unexpected JSON type"
        except json.JSONDecodeError:
            pts = 1; detail = "Endpoint exists but invalid JSON"
    checks.append(chk("agents.json", pts, 5,
                       "pass" if pts >= 4 else ("partial" if pts else "fail"), detail))

    # 1c  robots.txt AI bot rules  (3 pts) -- RFC 9309
    d = get(base, "/robots.txt")
    if d["status"] != 200 or not d["body"].strip():
        pts = 3; detail = "No robots.txt -- all bots allowed by default"
    else:
        body = d["body"]
        allowed = []
        for bot in AI_BOTS:
            if not _bot_blocked(body, bot):
                allowed.append(bot)
        pts = min(len(allowed), 3)
        detail = f"Allowed: {', '.join(allowed) or 'none of GPTBot/Google-Extended/ClaudeBot'}"
    checks.append(chk("robots.txt AI rules", pts, 3,
                       "pass" if pts == 3 else ("partial" if pts else "fail"), detail))

    # 1d  sitemap.xml  (3 pts)
    d = get(base, "/sitemap.xml")
    pts = 0; detail = "Missing"
    if d["status"] == 200 and ("<urlset" in d["body"] or "<sitemapindex" in d["body"]):
        url_count = d["body"].count("<loc>")
        dates = re.findall(r"<lastmod>([^<]+)</lastmod>", d["body"])
        if dates:
            try:
                latest = max(dates)
                age = (datetime.now(timezone.utc) -
                       datetime.fromisoformat(latest.replace("Z", "+00:00"))).days
                if age <= 30:
                    pts = 3; detail = f"Fresh ({url_count} URLs, updated {age}d ago)"
                else:
                    pts = 2; detail = f"Stale ({url_count} URLs, last update {age}d ago)"
            except (ValueError, TypeError):
                pts = 2; detail = f"Present ({url_count} URLs, dates unparseable)"
        else:
            pts = 2; detail = f"Present ({url_count} URLs, no lastmod)"
    checks.append(chk("sitemap.xml", pts, 3,
                       "pass" if pts == 3 else ("partial" if pts else "fail"), detail))

    # 1e  .well-known/agent.json  (4 pts) -- A2A protocol spec
    #   Required: name, url, capabilities, skills
    d = get(base, "/.well-known/agent.json")
    pts = 0; detail = "Missing"
    if d["status"] == 200:
        try:
            card = json.loads(d["body"])
            if not isinstance(card, dict):
                pts = 1; detail = "Valid JSON but not an object"
            else:
                a2a_req = {"name", "url", "capabilities", "skills"}
                present = a2a_req & set(card.keys())
                if len(present) >= 3:
                    pts = 4; detail = f"A2A card: {card.get('name','?')}, fields: {', '.join(sorted(present))}"
                elif "name" in present:
                    pts = 2; detail = f"Partial: name={card['name']}, missing {a2a_req - present}"
                else:
                    pts = 1; detail = "JSON but missing A2A fields (name, url, capabilities, skills)"
        except json.JSONDecodeError:
            pts = 1; detail = "Endpoint exists but invalid JSON"
    checks.append(chk(".well-known/agent.json (A2A)", pts, 4,
                       "pass" if pts >= 3 else ("partial" if pts else "fail"), detail))

    score = sum(c["points"] for c in checks)
    if verbose:
        _log("Discovery", score, 20, checks)
    return {"score": score, "max": 20, "checks": checks}


def _bot_blocked(robots_body, bot_name):
    """Check if bot is blocked per RFC 9309 robots.txt rules."""
    pat = rf"User-agent:\s*{re.escape(bot_name)}\s*\n((?:(?:Allow|Disallow|Crawl-delay|Sitemap):.*\n?)*)"
    section = re.search(pat, robots_body, re.IGNORECASE)
    if section:
        rules = section.group(1)
        if re.search(r"Disallow:\s*/\s*$", rules, re.MULTILINE):
            if re.search(r"Allow:\s*/\s*$", rules, re.MULTILINE):
                return False
            return True
        return False
    wildcard = re.search(
        r"User-agent:\s*\*\s*\n((?:(?:Allow|Disallow|Crawl-delay|Sitemap):.*\n?)*)",
        robots_body, re.IGNORECASE)
    if wildcard and re.search(r"Disallow:\s*/\s*$", wildcard.group(1), re.MULTILINE):
        return True
    return False


# --------------------------------------------------------------------------
# 2. Readability  (15 pts)
# --------------------------------------------------------------------------
def audit_readability(base, verbose, html=""):
    if not html:
        html = get(base, "/").get("body", "")
    checks = []

    # 2a  title + meta description  (3 pts)
    title_m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    desc_m = (re.search(r'<meta\s[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html, re.IGNORECASE)
              or re.search(r'<meta\s[^>]*content=["\']([^"\']*)["\'][^>]*name=["\']description["\']', html, re.IGNORECASE))
    has_t = bool(title_m and len(title_m.group(1).strip()) > 5)
    has_d = bool(desc_m and len(desc_m.group(1).strip()) > 10)
    pts = (2 if has_t else 0) + (1 if has_d else 0)
    parts = []
    if has_t: parts.append(f'title="{title_m.group(1).strip()[:60]}"')
    else: parts.append("title missing/too short")
    parts.append("meta description present" if has_d else "meta description missing")
    checks.append(chk("title + meta description", pts, 3,
                       "pass" if pts == 3 else ("partial" if pts else "fail"), "; ".join(parts)))

    # 2b  heading hierarchy  (3 pts)
    headings = re.findall(r"<h([1-6])[^>]*>", html, re.IGNORECASE)
    levels = [int(h) for h in headings]
    violations = 0
    if levels.count(1) != 1:
        violations += 1
    for i in range(1, len(levels)):
        if levels[i] > levels[i-1] + 1:
            violations += 1
    pts = max(0, 3 - violations)
    checks.append(chk("heading hierarchy", pts, 3,
                       "pass" if pts == 3 else ("partial" if pts else "fail"),
                       f"{len(headings)} headings, {levels.count(1)} h1, {violations} violations"))

    # 2c  semantic HTML  (3 pts)
    sem = ["main", "article", "nav", "section", "aside", "header", "footer"]
    found = [t for t in sem if re.search(rf"<{t}[\s>]", html, re.IGNORECASE)]
    pts = min(len(found), 3)
    checks.append(chk("semantic HTML", pts, 3,
                       "pass" if pts == 3 else ("partial" if pts else "fail"),
                       f"Found: {', '.join(found) or 'none'}"))

    # 2d  content-to-HTML ratio  (3 pts)
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    ratio = len(text) / max(len(html), 1) * 100
    pts = 3 if ratio >= 25 else (2 if ratio >= 15 else (1 if ratio >= 5 else 0))
    checks.append(chk("content-to-HTML ratio", pts, 3,
                       "pass" if pts == 3 else ("partial" if pts else "fail"),
                       f"{ratio:.1f}% text"))

    # 2e  lang attribute  (3 pts)
    lang_m = re.search(r'<html[^>]+lang=["\']([^"\']+)["\']', html, re.IGNORECASE)
    pts = 3 if lang_m else 0
    checks.append(chk("language attribute", pts, 3,
                       "pass" if pts else "fail",
                       f'lang="{lang_m.group(1)}"' if lang_m else "Missing lang on <html>"))

    score = sum(c["points"] for c in checks)
    if verbose:
        _log("Readability", score, 15, checks)
    return {"score": score, "max": 15, "checks": checks}


# --------------------------------------------------------------------------
# 3. Data Quality  (20 pts)
# --------------------------------------------------------------------------
def audit_data_quality(base, verbose, html=""):
    if not html:
        html = get(base, "/").get("body", "")
    checks = []

    ld_blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE)
    items = []; all_types = []
    for block in ld_blocks:
        try:
            data = json.loads(block)
            for item in (data if isinstance(data, list) else [data]):
                if not isinstance(item, dict): continue
                _collect(item, items, all_types)
                for gi in item.get("@graph", []):
                    if isinstance(gi, dict):
                        _collect(gi, items, all_types)
        except json.JSONDecodeError:
            pass

    # 3a  JSON-LD present  (5 pts)
    pts = 5 if ld_blocks else 0
    checks.append(chk("JSON-LD structured data", pts, 5,
                       "pass" if pts else "fail", f"{len(ld_blocks)} block(s)"))

    # 3b  Schema.org types  (5 pts)
    unique = list(set(all_types))
    pts = min(len(unique) * 2, 5)
    checks.append(chk("Schema.org types", pts, 5,
                       "pass" if pts >= 4 else ("partial" if pts else "fail"),
                       f"Types: {', '.join(unique[:8]) or 'none'}"))

    # 3c  Required properties  (5 pts) -- per schema.org type definitions
    REQUIRED = {
        "Organization": ["name", "url"],
        "LocalBusiness": ["name", "address"],
        "Product": ["name", "offers"],
        "Service": ["name", "provider"],
        "Article": ["headline", "author", "datePublished"],
        "WebSite": ["name", "url"],
        "WebPage": ["name", "url"],
        "BreadcrumbList": ["itemListElement"],
        "FAQPage": ["mainEntity"],
        "Event": ["name", "startDate", "location"],
        "Person": ["name"],
        "ItemList": ["itemListElement"],
    }
    scores_list = []
    for item in items:
        t = item.get("@type", "")
        if isinstance(t, list): t = t[0] if t else ""
        req = REQUIRED.get(t)
        if req:
            filled = sum(1 for f in req if item.get(f))
            scores_list.append(filled / len(req))
    if scores_list:
        avg = sum(scores_list) / len(scores_list)
        pts = round(avg * 5)
        detail = f"{int(avg*100)}% required fields across {len(scores_list)} typed items"
    else:
        pts = 0; detail = "No recognisable typed items"
    checks.append(chk("required properties", pts, 5,
                       "pass" if pts >= 4 else ("partial" if pts else "fail"), detail))

    # 3d  OpenGraph / social meta  (5 pts)
    og = set(re.findall(r'<meta\s[^>]*property=["\']og:(\w+)["\']', html, re.IGNORECASE))
    tw = set(re.findall(r'<meta\s[^>]*name=["\']twitter:(\w+)["\']', html, re.IGNORECASE))
    n = len(og) + len(tw)
    pts = 5 if n >= 6 else (4 if n >= 4 else (2 if n >= 2 else (1 if n else 0)))
    parts = []
    if og: parts.append(f"og: {', '.join(sorted(og)[:5])}")
    if tw: parts.append(f"twitter: {', '.join(sorted(tw)[:5])}")
    checks.append(chk("OpenGraph / meta tags", pts, 5,
                       "pass" if pts >= 4 else ("partial" if pts else "fail"),
                       "; ".join(parts) if parts else "None"))

    score = sum(c["points"] for c in checks)
    if verbose:
        _log("Data Quality", score, 20, checks)
    return {"score": score, "max": 20, "checks": checks}


def _collect(item, items_list, types_list):
    items_list.append(item)
    t = item.get("@type")
    if t:
        (types_list.extend if isinstance(t, list) else types_list.append)(t)


# --------------------------------------------------------------------------
# 4. MCP / API  (20 pts)
# --------------------------------------------------------------------------
def audit_mcp_api(base, verbose):
    checks = []
    html = get(base, "/").get("body", "")

    # 4a  API documentation  (5 pts)
    doc_paths = ["/api/docs", "/docs/api", "/docs", "/developer",
                 "/api-docs", "/swagger-ui", "/redoc"]
    doc_found = False; doc_path = ""
    for p in doc_paths:
        d = get(base, p)
        if d["status"] == 200 and len(d["body"]) > 200:
            doc_found = True; doc_path = p; break
    html_link = bool(re.search(r'href=["\'][^"\']*(/api|/developer|/docs)["\']', html, re.IGNORECASE))
    pts = 5 if doc_found else (2 if html_link else 0)
    checks.append(chk("API documentation", pts, 5,
                       "pass" if pts >= 4 else ("partial" if pts else "fail"),
                       f"Found at {doc_path}" if doc_found else ("API link in HTML" if html_link else "Not found")))

    # 4b  OpenAPI / Swagger spec  (5 pts)
    spec_paths = ["/openapi.json", "/openapi.yaml", "/swagger.json",
                  "/api/openapi.json", "/api/swagger.json"]
    spec_found = False; spec_path = ""
    for p in spec_paths:
        d = get(base, p)
        if d["status"] == 200:
            body = d["body"]
            try:
                s = json.loads(body)
                if any(k in s for k in ("openapi", "swagger", "paths")):
                    spec_found = True; spec_path = p; break
            except (json.JSONDecodeError, ValueError):
                if "openapi:" in body or "swagger:" in body:
                    spec_found = True; spec_path = p; break
    pts = 5 if spec_found else 0
    checks.append(chk("OpenAPI/Swagger spec", pts, 5,
                       "pass" if spec_found else "fail",
                       f"Found at {spec_path}" if spec_found else "Not found"))

    # 4c  API endpoint / link rel=api  (5 pts)
    api_link = bool(re.search(r'<link[^>]+rel=["\']api["\']', html, re.IGNORECASE))
    api_endpoint = False
    for p in ["/api", "/api/v1", "/api/v2", "/graphql", "/mcp", "/mcp/sse"]:
        d = get(base, p)
        if d["status"] in (200, 401, 403):
            api_endpoint = True; break
    pts = 0; dp = []
    if api_link: pts += 3; dp.append("link rel=api in HTML")
    if api_endpoint: pts += 2; dp.append("API endpoint responds")
    pts = min(pts, 5)
    checks.append(chk("API link / endpoint", pts, 5,
                       "pass" if pts >= 4 else ("partial" if pts else "fail"),
                       "; ".join(dp) if dp else "No API links or endpoints"))

    # 4d  CORS headers  (5 pts)
    cors = False; cors_val = ""
    for resp in _cache.values():
        hl = {k.lower(): v for k, v in resp.get("headers", {}).items()}
        if "access-control-allow-origin" in hl:
            cors = True; cors_val = hl["access-control-allow-origin"]; break
    if not cors:
        try:
            r = requests.options(urljoin(base, "/api"), timeout=TIMEOUT,
                                 headers={"User-Agent": UA, "Origin": "https://example.com",
                                          "Access-Control-Request-Method": "GET"})
            for k in r.headers:
                if k.lower() == "access-control-allow-origin":
                    cors = True; cors_val = r.headers[k]; break
        except Exception:
            pass
    pts = 5 if cors else 0
    checks.append(chk("CORS headers", pts, 5,
                       "pass" if cors else "fail",
                       f"ACAO: {cors_val}" if cors else "Not found"))

    score = sum(c["points"] for c in checks)
    if verbose:
        _log("MCP/API", score, 20, checks)
    return {"score": score, "max": 20, "checks": checks}


# --------------------------------------------------------------------------
# 5. Commerce  (15 pts)
# --------------------------------------------------------------------------
def audit_commerce(base, verbose, html=""):
    if not html:
        html = get(base, "/").get("body", "")
    checks = []

    # 5a  UCP manifest  (5 pts) -- Google UCP spec at ucp.dev
    #   Profile at /.well-known/ucp must have: version, services, capabilities
    d = get(base, "/.well-known/ucp")
    pts = 0; detail = "Missing"
    if d["status"] == 200:
        try:
            ucp = json.loads(d["body"])
            if not isinstance(ucp, dict):
                pts = 1; detail = "JSON but not an object"
            else:
                inner = ucp.get("ucp", ucp)
                has_svc = "services" in inner
                has_cap = "capabilities" in inner
                has_ver = "version" in inner
                if has_svc and has_cap:
                    pts = 5; detail = "Valid UCP profile (services + capabilities)"
                elif has_ver or has_svc or has_cap:
                    pts = 3; detail = f"Partial UCP (svc={has_svc}, cap={has_cap}, ver={has_ver})"
                else:
                    pts = 1; detail = "JSON at .well-known/ucp but no UCP fields"
        except json.JSONDecodeError:
            pts = 1; detail = "Endpoint exists but invalid JSON"
    checks.append(chk("UCP manifest (.well-known/ucp)", pts, 5,
                       "pass" if pts >= 4 else ("partial" if pts else "fail"), detail))

    # 5b  ACP / checkout endpoint  (5 pts) -- OpenAI/Stripe ACP spec
    #   Primary: POST /checkout_sessions
    acp_paths = ["/checkout_sessions", "/api/checkout_sessions",
                 "/acp/checkout_sessions", "/acp",
                 "/checkout/api", "/api/checkout", "/api/cart"]
    acp_found = False; acp_path = ""; acp_status = 0
    for p in acp_paths:
        d = get(base, p)
        if d["status"] in (200, 401, 403, 405, 422):
            acp_found = True; acp_path = p; acp_status = d["status"]; break
    pts = 5 if acp_found else 0
    checks.append(chk("ACP/checkout endpoint", pts, 5,
                       "pass" if acp_found else "fail",
                       f"Found at {acp_path} (HTTP {acp_status})" if acp_found else "No ACP checkout endpoint"))

    # 5c  Product structured data  (5 pts) -- Schema.org Product/Offer/Service
    ld_blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE)
    commerce_types = []
    for block in ld_blocks:
        try:
            data = json.loads(block)
            for item in (data if isinstance(data, list) else [data]):
                if not isinstance(item, dict): continue
                _check_commerce(item, commerce_types)
                for gi in item.get("@graph", []):
                    if isinstance(gi, dict):
                        _check_commerce(gi, commerce_types)
        except json.JSONDecodeError:
            pass
    pts = min(len(commerce_types) * 2, 5)
    checks.append(chk("product structured data", pts, 5,
                       "pass" if pts >= 4 else ("partial" if pts else "fail"),
                       f"Commerce types: {', '.join(commerce_types) or 'none'}"))

    score = sum(c["points"] for c in checks)
    if verbose:
        _log("Commerce", score, 15, checks)
    return {"score": score, "max": 15, "checks": checks}


def _check_commerce(item, out):
    t = item.get("@type", "")
    if t in ("Product", "Service", "Offer", "ItemList", "OfferCatalog") or item.get("offers"):
        out.append(t or "has-offers")


# --------------------------------------------------------------------------
# 6. Payment  (10 pts)
# --------------------------------------------------------------------------
def audit_payment(base, verbose, html=""):
    if not html:
        html = get(base, "/").get("body", "")
    checks = []

    # 6a  Payment SDK  (4 pts)
    providers = {
        "Stripe": r"stripe\.com|js\.stripe\.com|pk_live_|pk_test_",
        "PayPal": r"paypal\.com/sdk|paypalobjects\.com",
        "Square": r"squareup\.com|squarecdn\.com",
        "Adyen": r"adyen\.com|adyen-checkout",
        "Braintree": r"braintreegateway\.com",
    }
    detected = [n for n, p in providers.items() if re.search(p, html, re.IGNORECASE)]
    pts = 4 if detected else 0
    checks.append(chk("payment SDK", pts, 4,
                       "pass" if detected else "fail",
                       f"Detected: {', '.join(detected)}" if detected else "None detected"))

    # 6b  x402 / payment headers  (3 pts)
    x402 = False; pay_hdr = False
    for p in ["/premium", "/pro", "/paid"]:
        d = get(base, p)
        if d["status"] == 402: x402 = True; break
        if any("payment" in k.lower() for k in d.get("headers", {})):
            pay_hdr = True
    d = get(base, "/.well-known/payment")
    if d["status"] == 200: pay_hdr = True
    pts = 3 if x402 else (2 if pay_hdr else 0)
    dp = []
    if x402: dp.append("402 response found")
    if pay_hdr: dp.append("payment endpoint/headers")
    checks.append(chk("x402 / payment headers", pts, 3,
                       "pass" if pts == 3 else ("partial" if pts else "fail"),
                       "; ".join(dp) if dp else "None found"))

    # 6c  Apple/Google Pay  (3 pts)
    wallets = []
    if re.search(r"apple-pay|applepay|ApplePaySession", html, re.IGNORECASE):
        wallets.append("Apple Pay")
    if re.search(r"google-pay|googlepay|payments\.google\.com", html, re.IGNORECASE):
        wallets.append("Google Pay")
    d = get(base, "/.well-known/apple-developer-merchantid-domain-association")
    if d["status"] == 200 and len(d["body"]) > 10 and "Apple Pay" not in wallets:
        wallets.append("Apple Pay")
    pts = min(len(wallets) * 2, 3)
    checks.append(chk("Apple/Google Pay", pts, 3,
                       "pass" if pts >= 2 else ("partial" if pts else "fail"),
                       f"Detected: {', '.join(wallets)}" if wallets else "None"))

    score = sum(c["points"] for c in checks)
    if verbose:
        _log("Payment", score, 10, checks)
    return {"score": score, "max": 10, "checks": checks}


# --------------------------------------------------------------------------
# Logging / formatting
# --------------------------------------------------------------------------
def _log(name, score, mx, checks):
    print(f"  [{name}] {score}/{mx}", file=sys.stderr)
    for c in checks:
        sym = {"pass": "+", "partial": "~", "fail": "-"}.get(c["status"], "?")
        print(f"    [{sym}] {c['name']}: {c['points']}/{c['max']} -- {c['detail']}", file=sys.stderr)


def format_human(report):
    lines = [f"Agent-Readiness Audit: {report['url']}",
             f"Date: {report['timestamp'][:10]}",
             f"Grade: {report['grade']}  Score: {report['total_score']}/{report['total_max']}", ""]
    labels = {"discovery": "Discovery", "readability": "Readability",
              "data_quality": "Data Quality", "mcp_api": "MCP/API",
              "commerce": "Commerce", "payment": "Payment"}
    for key in labels:
        dim = report["dimensions"][key]
        pct = int(dim["score"] / dim["max"] * 100) if dim["max"] else 0
        w = 20; filled = int(pct / 100 * w)
        bar = "\u2588" * filled + "\u2591" * (w - filled)
        lines.append(f"  {labels[key]:<14} {bar} {dim['score']:>2}/{dim['max']} ({pct:>3}%)")
        for c in dim["checks"]:
            sym = {"pass": "+", "partial": "~", "fail": "-"}.get(c["status"], "?")
            lines.append(f"    [{sym}] {c['name']}: {c['points']}/{c['max']} -- {c['detail']}")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def run_audit(url, verbose=False):
    base = url.rstrip("/") + "/"
    if verbose:
        print(f"ar-audit v{VERSION} -- {base}\n", file=sys.stderr)

    homepage = get(base, "/")
    html = homepage["body"] if homepage["status"] == 200 else ""

    if verbose:
        print("[1/6] Discovery...", file=sys.stderr)
    d1 = audit_discovery(base, verbose)
    if verbose:
        print("[2/6] Readability...", file=sys.stderr)
    d2 = audit_readability(base, verbose, html)
    if verbose:
        print("[3/6] Data Quality...", file=sys.stderr)
    d3 = audit_data_quality(base, verbose, html)
    if verbose:
        print("[4/6] MCP/API...", file=sys.stderr)
    d4 = audit_mcp_api(base, verbose)
    if verbose:
        print("[5/6] Commerce...", file=sys.stderr)
    d5 = audit_commerce(base, verbose, html)
    if verbose:
        print("[6/6] Payment...", file=sys.stderr)
    d6 = audit_payment(base, verbose, html)

    dims = {"discovery": d1, "readability": d2, "data_quality": d3,
            "mcp_api": d4, "commerce": d5, "payment": d6}
    total = sum(d["score"] for d in dims.values())
    total_max = sum(d["max"] for d in dims.values())

    if verbose:
        print(f"\n{'='*40}\nTOTAL: {total}/{total_max} (Grade: {grade_of(total)})\n{'='*40}",
              file=sys.stderr)

    return {"url": url, "timestamp": datetime.now(timezone.utc).isoformat(),
            "dimensions": dims, "total_score": total, "total_max": total_max,
            "grade": grade_of(total)}


def main():
    ap = argparse.ArgumentParser(description="Agent-readiness audit (6 dimensions, 100 pts)")
    ap.add_argument("--url", required=True, help="URL to audit")
    ap.add_argument("--json", action="store_true", help="JSON to stdout")
    ap.add_argument("--output", help="Save JSON to file")
    ap.add_argument("--verbose", action="store_true", help="Progress to stderr")
    args = ap.parse_args()

    url = args.url
    if not urlparse(url).scheme:
        url = f"https://{url}"

    report = run_audit(url, verbose=args.verbose)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        if not args.json:
            print(f"Saved to: {args.output}", file=sys.stderr)

    if args.json:
        print(json.dumps(report, indent=2))
    elif not args.output:
        print(format_human(report))

    return 0


if __name__ == "__main__":
    sys.exit(main())
