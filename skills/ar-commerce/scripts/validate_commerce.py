#!/usr/bin/env python3
"""Scan a URL for commerce protocol support and agent-readiness signals.

Checks for UCP manifests (Google spec), ACP indicators (OpenAI/Stripe),
product structured data (Schema.org), API specs, and shopping meta tags.

Validation rules sourced from:
- UCP: developers.google.com/merchant/ucp/guides/ucp-profile
- ACP: developers.openai.com/commerce/specs/checkout/
- Schema.org: schema.org/Product, Google Rich Results requirements
- x402: docs.x402.org, github.com/coinbase/x402

Usage:
    python validate_commerce.py --url https://shopify.com
    python validate_commerce.py --url https://amazon.com --json
    python validate_commerce.py --url https://stripe.com --verbose
"""

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests

UA = "AgentReady-CommerceValidator/1.0 (compatibility check)"
TIMEOUT = 15

# --- Official UCP spec (Google, version 2026-01-23) ---
# Top-level: {"ucp": {...}, "signing_keys": [...]}
# ucp must contain: version, services, capabilities
# payment_handlers recommended
UCP_REQUIRED = ["version", "services", "capabilities"]
UCP_SERVICE_FIELDS = ["version", "transport", "endpoint"]
UCP_CAP_FIELDS = ["version", "spec", "schema"]

# --- Schema.org Product: Google requires name + one of (review, aggregateRating, offers) ---
# Recommended: image, description, brand, sku, gtin/mpn
PRODUCT_RECOMMENDED = ["name", "image", "description", "brand", "sku", "offers"]


class PageParser(HTMLParser):
    """Extract structured data, meta tags, script srcs, and link rels."""

    def __init__(self):
        super().__init__()
        self.meta_tags = []
        self.script_srcs = []
        self.script_contents = []
        self.link_rels = []
        self.json_ld_blocks = []
        self._in_script = False
        self._script_type = ""
        self._buf = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "meta":
            self.meta_tags.append(d)
        elif tag == "script":
            src = d.get("src", "")
            if src:
                self.script_srcs.append(src)
            self._script_type = d.get("type", "")
            self._in_script = True
            self._buf = []
        elif tag == "link":
            self.link_rels.append(d)

    def handle_data(self, data):
        if self._in_script:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._in_script:
            content = "".join(self._buf)
            self.script_contents.append(content)
            if self._script_type == "application/ld+json" and content.strip():
                try:
                    self.json_ld_blocks.append(json.loads(content))
                except (json.JSONDecodeError, ValueError):
                    pass
            self._in_script = False


def fetch(url, method="GET"):
    """HTTP request with standard headers."""
    headers = {"User-Agent": UA, "Accept": "*/*"}
    try:
        fn = requests.head if method == "HEAD" else requests.get
        return fn(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException:
        return None


def check_ucp(base_url, results, verbose):
    """Check /.well-known/ucp per Google UCP spec (2026-01-23).

    Official spec: developers.google.com/merchant/ucp/guides/ucp-profile
    Expected structure: {"ucp": {"version", "services", "capabilities",
    "payment_handlers"}, "signing_keys": [...]}
    """
    url = urljoin(base_url, "/.well-known/ucp")
    resp = fetch(url)
    r = {"found": False, "url": url}

    if not resp or resp.status_code != 200:
        r["status"] = resp.status_code if resp else "connection_error"
        results["ucp"] = r
        return

    r["found"] = True
    try:
        data = resp.json()
    except (json.JSONDecodeError, ValueError):
        r["parse_error"] = "Response is not valid JSON"
        results["ucp"] = r
        return

    # Validate top-level structure per spec
    ucp_obj = data.get("ucp")
    if not isinstance(ucp_obj, dict):
        r["error"] = "Missing top-level 'ucp' object (spec requires {\"ucp\": {...}})"
        results["ucp"] = r
        return

    r["version"] = ucp_obj.get("version", "missing")

    # Check required fields inside ucp object
    missing = [f for f in UCP_REQUIRED if f not in ucp_obj]
    if missing:
        r["missing_required"] = missing

    # Validate services
    services = ucp_obj.get("services", {})
    if isinstance(services, dict):
        r["services"] = list(services.keys())
        if verbose:
            for svc_name, svc_list in services.items():
                if isinstance(svc_list, list):
                    for svc in svc_list:
                        missing_f = [f for f in UCP_SERVICE_FIELDS
                                     if f not in svc]
                        if missing_f:
                            r.setdefault("service_issues", []).append(
                                f"{svc_name}: missing {missing_f}")

    # Validate capabilities
    caps = ucp_obj.get("capabilities", {})
    if isinstance(caps, dict):
        r["capabilities"] = list(caps.keys())

    # Check payment_handlers (recommended)
    ph = ucp_obj.get("payment_handlers", {})
    if isinstance(ph, dict) and ph:
        r["payment_handlers"] = list(ph.keys())
    else:
        r["payment_handlers_missing"] = True

    # Check signing_keys (recommended per spec)
    sk = data.get("signing_keys")
    r["has_signing_keys"] = isinstance(sk, list) and len(sk) > 0

    if verbose:
        r["raw"] = data

    results["ucp"] = r


def check_acp(base_url, html, parser, results, verbose):
    """Check for ACP (OpenAI/Stripe) indicators.

    ACP spec: developers.openai.com/commerce/specs/checkout/
    5 endpoints: POST/GET /checkout_sessions, POST /{id}, /{id}/complete, /{id}/cancel
    Required headers: Authorization, Signature, Idempotency-Key, Request-Id
    No .well-known discovery — detection is via code patterns.
    """
    indicators = []

    # Stripe.js is the payment backbone for ACP
    for src in parser.script_srcs:
        if "js.stripe.com" in src:
            indicators.append(f"Stripe.js: {src}")

    # ACP-specific patterns in HTML/JS
    acp_patterns = [
        (r'checkout[_\-]?sessions?', "checkout_sessions endpoint pattern"),
        (r'/v1/checkout', "Stripe /v1/checkout path"),
        (r'agentic[_\-]?commerce', "agentic commerce reference"),
        (r'delegated[_\-]?payment', "delegated payment token reference"),
        (r'Idempotency-Key', "ACP required header reference"),
    ]
    for pat, label in acp_patterns:
        if re.search(pat, html, re.IGNORECASE):
            indicators.append(label)

    # Stripe meta tags
    for meta in parser.meta_tags:
        name = (meta.get("name", "") + meta.get("property", "")).lower()
        content = meta.get("content", "")
        if "stripe" in name or (content and content.startswith("pk_")):
            indicators.append(f"Stripe meta: {meta.get('name', meta.get('property', ''))}")

    results["acp"] = {
        "detected": len(indicators) > 0,
        "indicators": indicators,
        "note": "ACP has no .well-known discovery; detection is heuristic"
    }


def check_structured_data(parser, results, verbose):
    """Check for Schema.org Product/Offer structured data.

    Per schema.org/Product and Google Rich Results requirements:
    - Product type requires 'name' + one of (review, aggregateRating, offers)
    - Recommended: image, description, brand, sku, gtin/mpn
    """
    products = []
    other_types = []

    for block in parser.json_ld_blocks:
        items = block if isinstance(block, list) else [block]
        for item in items:
            if not isinstance(item, dict):
                continue
            t = item.get("@type", "")
            types = t if isinstance(t, list) else [t]
            for typ in types:
                if typ in ("Product", "Offer", "AggregateOffer"):
                    entry = {"type": typ}
                    if typ == "Product":
                        has_name = bool(item.get("name"))
                        has_review = bool(item.get("review"))
                        has_rating = bool(item.get("aggregateRating"))
                        has_offers = bool(item.get("offers"))
                        entry["name"] = item.get("name", "")[:80]
                        entry["has_name"] = has_name
                        entry["has_required_one_of"] = any([
                            has_review, has_rating, has_offers])
                        present = [f for f in PRODUCT_RECOMMENDED if item.get(f)]
                        missing = [f for f in PRODUCT_RECOMMENDED if not item.get(f)]
                        entry["recommended_present"] = present
                        entry["recommended_missing"] = missing
                    products.append(entry)
                elif typ in ("Organization", "WebSite", "BreadcrumbList",
                             "LocalBusiness", "Store", "ItemList"):
                    other_types.append(typ)

    results["structured_data"] = {
        "has_product": len(products) > 0,
        "products": products[:5] if verbose else len(products),
        "other_types": list(set(other_types)),
    }


def check_api_specs(base_url, parser, results):
    """Check for OpenAPI/API spec links."""
    found = []

    for link in parser.link_rels:
        rel = link.get("rel", "")
        href = link.get("href", "")
        if any(k in rel.lower() for k in ("api", "openapi", "swagger")):
            found.append({"type": "link_rel", "rel": rel, "href": href})

    for path in ["/openapi.json", "/swagger.json", "/api/docs",
                 "/.well-known/openapi"]:
        url = urljoin(base_url, path)
        resp = fetch(url, method="HEAD")
        if resp and resp.status_code < 400:
            found.append({"type": "well_known", "path": path,
                          "status": resp.status_code})

    results["api_specs"] = {
        "has_api": len(found) > 0,
        "found": found,
    }


def check_shopping_meta(parser, results):
    """Check for shopping-related meta tags (Open Graph product extension)."""
    tags = []
    prefixes = ("og:product", "product:", "og:price", "og:availability",
                "og:brand")

    for meta in parser.meta_tags:
        prop = meta.get("property", "") or meta.get("name", "")
        if not prop:
            continue
        for prefix in prefixes:
            if prop.lower().startswith(prefix):
                tags.append({
                    "property": prop,
                    "content": meta.get("content", "")[:100]
                })
                break

    results["shopping_meta"] = {
        "has_shopping": len(tags) > 0,
        "tags": tags,
    }


def print_report(url, results):
    """Print human-readable report."""
    signals = []
    if results["ucp"].get("found"):
        signals.append("UCP manifest")
    if results["acp"]["detected"]:
        signals.append("ACP indicators")
    if results["structured_data"]["has_product"]:
        signals.append("Product Schema.org")
    if results["api_specs"]["has_api"]:
        signals.append("API spec")
    if results["shopping_meta"]["has_shopping"]:
        signals.append("Shopping meta")

    print(f"\n{'=' * 60}")
    print(f"  Commerce Protocol Scan: {url}")
    print(f"  Signals: {len(signals)}/5 detected")
    if signals:
        print(f"  Found: {', '.join(signals)}")
    else:
        print(f"  No commerce protocol signals detected")
    print(f"{'=' * 60}")

    # UCP
    ucp = results["ucp"]
    if ucp.get("found"):
        print(f"\n  [PASS] UCP Manifest (/.well-known/ucp)")
        print(f"    Version: {ucp.get('version', 'unknown')}")
        if ucp.get("services"):
            print(f"    Services: {', '.join(ucp['services'])}")
        if ucp.get("capabilities"):
            print(f"    Capabilities: {', '.join(ucp['capabilities'][:6])}")
        if ucp.get("payment_handlers"):
            print(f"    Payment handlers: {', '.join(ucp['payment_handlers'])}")
        elif ucp.get("payment_handlers_missing"):
            print(f"    [WARN] No payment_handlers declared")
        if not ucp.get("has_signing_keys"):
            print(f"    [WARN] No signing_keys (needed for webhook verification)")
        if ucp.get("missing_required"):
            print(f"    [WARN] Missing required fields: {ucp['missing_required']}")
        if ucp.get("error"):
            print(f"    [FAIL] {ucp['error']}")
    else:
        st = ucp.get("status", "")
        print(f"\n  [FAIL] UCP Manifest: not found (status: {st})")

    # ACP
    acp = results["acp"]
    if acp["detected"]:
        print(f"\n  [PASS] ACP Indicators")
        for ind in acp["indicators"][:6]:
            print(f"    - {ind}")
    else:
        print(f"\n  [FAIL] ACP Indicators: none detected")
    print(f"    Note: {acp['note']}")

    # Structured data
    sd = results["structured_data"]
    if sd["has_product"]:
        print(f"\n  [PASS] Product Structured Data (Schema.org)")
        items = sd.get("products", [])
        if isinstance(items, list):
            for p in items[:3]:
                status = "valid" if p.get("has_required_one_of", True) else "incomplete"
                print(f"    - {p.get('type')}: {p.get('name', 'unnamed')} ({status})")
                if p.get("recommended_missing"):
                    print(f"      Missing recommended: {', '.join(p['recommended_missing'][:4])}")
        else:
            print(f"    {items} product type(s) found")
    else:
        other = sd.get("other_types", [])
        if other:
            print(f"\n  [INFO] Structured Data: {', '.join(other)} (no Product/Offer)")
        else:
            print(f"\n  [FAIL] Product Structured Data: none found")

    # API specs
    api = results["api_specs"]
    if api["has_api"]:
        print(f"\n  [PASS] API Spec")
        for f in api["found"]:
            print(f"    - {f}")
    else:
        print(f"\n  [FAIL] API Spec: none found")

    # Shopping meta
    sm = results["shopping_meta"]
    if sm["has_shopping"]:
        print(f"\n  [PASS] Shopping Meta Tags")
        for t in sm["tags"][:5]:
            print(f"    {t['property']}: {t['content']}")
    else:
        print(f"\n  [FAIL] Shopping Meta Tags: none found")

    # Recommendations
    print(f"\n  Recommendations:")
    if not ucp.get("found"):
        print(f"    - Add /.well-known/ucp for Google AI Mode discovery")
    if not acp["detected"]:
        print(f"    - Integrate ACP for ChatGPT Shopping support")
    if not sd["has_product"]:
        print(f"    - Add Product/Offer JSON-LD for rich results + agent parsing")
    if not sm["has_shopping"]:
        print(f"    - Add og:product meta tags for social/agent discovery")
    if signals:
        print(f"    - {len(signals)} signal(s) found -- review gaps above")
    print()


def main():
    ap = argparse.ArgumentParser(
        description="Scan a URL for commerce protocol support")
    ap.add_argument("--url", required=True, help="URL to scan")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--verbose", action="store_true", help="Extra details")
    args = ap.parse_args()

    url = args.url if args.url.startswith("http") else "https://" + args.url

    resp = fetch(url)
    if not resp:
        print(f"[ERROR] Could not connect to {url}", file=sys.stderr)
        sys.exit(1)
    if resp.status_code >= 400:
        print(f"[ERROR] {url} returned HTTP {resp.status_code}", file=sys.stderr)
        sys.exit(1)

    html = resp.text
    parser = PageParser()
    try:
        parser.feed(html)
    except Exception:
        pass

    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    results = {"url": url, "status": resp.status_code}

    check_ucp(base, results, args.verbose)
    check_acp(base, html, parser, results, args.verbose)
    check_structured_data(parser, results, args.verbose)
    check_api_specs(base, parser, results)
    check_shopping_meta(parser, results)

    if args.json:
        out = dict(results)
        if not args.verbose and "raw" in out.get("ucp", {}):
            del out["ucp"]["raw"]
        print(json.dumps(out, indent=2))
    else:
        print_report(url, results)

    has_any = any([
        results["ucp"].get("found"),
        results["acp"]["detected"],
        results["structured_data"]["has_product"],
        results["api_specs"]["has_api"],
        results["shopping_meta"]["has_shopping"],
    ])
    sys.exit(0 if has_any else 1)


if __name__ == "__main__":
    main()
