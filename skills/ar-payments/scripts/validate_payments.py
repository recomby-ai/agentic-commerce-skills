#!/usr/bin/env python3
"""Scan a URL for payment infrastructure and agent-payment readiness.

Checks for Stripe.js, PayPal SDK, x402 protocol support, payment meta
tags, /.well-known/pay, and Apple Pay/Google Pay domain verification.

Validation rules sourced from:
- x402: docs.x402.org, github.com/coinbase/x402 (v2 headers)
- Stripe: stripe.com/docs (js.stripe.com detection)
- Apple Pay: developer.apple.com (domain verification file)
- PayPal: developer.paypal.com/sdk

Usage:
    python validate_payments.py --url https://shopify.com
    python validate_payments.py --url https://stripe.com --json
    python validate_payments.py --url https://amazon.com --verbose
"""

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests

UA = "AgentReady-PaymentValidator/1.0 (compatibility check)"
TIMEOUT = 15

# x402 headers per spec (github.com/coinbase/x402)
# v2: PAYMENT-REQUIRED (server 402), PAYMENT-SIGNATURE (client), PAYMENT-RESPONSE (server)
# v1 (legacy): X-PAYMENT (client), X-PAYMENT-RESPONSE (server)
X402_SERVER_HEADERS = ["payment-required", "x-payment-response",
                       "payment-response"]
X402_LEGACY_HEADERS = ["x-payment", "x-payment-amount", "x-payment-currency",
                       "x-payment-address"]


class PageParser(HTMLParser):
    """Extract script sources, meta tags, and link elements."""

    def __init__(self):
        super().__init__()
        self.meta_tags = []
        self.script_srcs = []
        self.script_contents = []
        self.link_rels = []
        self._in_script = False
        self._buf = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "meta":
            self.meta_tags.append(d)
        elif tag == "script":
            src = d.get("src", "")
            if src:
                self.script_srcs.append(src)
            self._in_script = True
            self._buf = []
        elif tag == "link":
            self.link_rels.append(d)

    def handle_data(self, data):
        if self._in_script:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._in_script:
            self.script_contents.append("".join(self._buf))
            self._in_script = False


def fetch(url, method="GET"):
    """HTTP request with standard headers."""
    headers = {"User-Agent": UA, "Accept": "*/*"}
    try:
        fn = requests.head if method == "HEAD" else requests.get
        return fn(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException:
        return None


def check_stripe(parser, html, results):
    """Detect Stripe.js (js.stripe.com/v3).

    Stripe.js is required for ACP/SPT agent payments.
    Detection: script tags, inline references, publishable key meta tags.
    """
    scripts = [s for s in parser.script_srcs if "js.stripe.com" in s]

    inline = False
    for content in parser.script_contents:
        if "Stripe(" in content or "loadStripe" in content:
            inline = True
            break

    pk_found = False
    for meta in parser.meta_tags:
        content = meta.get("content", "")
        if content.startswith("pk_live_") or content.startswith("pk_test_"):
            pk_found = True
            break

    detected = bool(scripts or inline or pk_found)
    results["stripe"] = {
        "detected": detected,
        "scripts": scripts,
        "inline_references": inline,
        "publishable_key_in_meta": pk_found,
    }


def check_paypal(parser, results):
    """Detect PayPal SDK (paypal.com/sdk or paypalobjects.com).

    Ref: developer.paypal.com/sdk/js/reference
    """
    scripts = [s for s in parser.script_srcs
               if "paypal.com/sdk" in s or "paypalobjects.com" in s]

    inline = False
    for content in parser.script_contents:
        lower = content.lower()
        if "paypal" in lower and ("buttons" in lower or "sdk" in lower):
            inline = True
            break

    results["paypal"] = {
        "detected": bool(scripts or inline),
        "scripts": scripts,
        "inline_references": inline,
    }


def check_x402(base_url, results):
    """Check for x402 payment protocol support.

    Spec: docs.x402.org, github.com/coinbase/x402
    Flow: Server returns 402 + PAYMENT-REQUIRED header (base64 PaymentRequired obj)
    Client retries with PAYMENT-SIGNATURE header
    Server confirms with PAYMENT-RESPONSE header

    We check both the main URL and common API paths for 402 responses.
    """
    all_headers_found = {}
    has_402 = False
    checked_urls = []

    for path in ["", "/api/v1", "/v1", "/api"]:
        url = urljoin(base_url, path) if path else base_url
        resp = fetch(url, method="HEAD")
        if not resp:
            continue
        checked_urls.append({"path": path or "/", "status": resp.status_code})

        if resp.status_code == 402:
            has_402 = True
            for h in resp.headers:
                h_lower = h.lower()
                if h_lower in X402_SERVER_HEADERS or h_lower in X402_LEGACY_HEADERS:
                    all_headers_found[h] = resp.headers[h][:100]
            break

        for h in resp.headers:
            h_lower = h.lower()
            if h_lower in X402_SERVER_HEADERS or h_lower in X402_LEGACY_HEADERS:
                all_headers_found[h] = resp.headers[h][:100]

    results["x402"] = {
        "detected": has_402 or bool(all_headers_found),
        "has_402_response": has_402,
        "x402_headers": all_headers_found,
        "paths_checked": checked_urls,
    }


def check_payment_meta(parser, results):
    """Check for payment-related meta tags."""
    tags = []
    keywords = ("payment", "price", "currency", "checkout",
                "product:price", "product:availability", "og:price")

    for meta in parser.meta_tags:
        prop = meta.get("property", "") or meta.get("name", "")
        if not prop:
            continue
        for kw in keywords:
            if kw in prop.lower():
                tags.append({
                    "property": prop,
                    "content": meta.get("content", "")[:100]
                })
                break

    results["payment_meta"] = {
        "detected": len(tags) > 0,
        "tags": tags,
    }


def check_wellknown_pay(base_url, results):
    """Check /.well-known/pay endpoint."""
    url = urljoin(base_url, "/.well-known/pay")
    resp = fetch(url)
    found = resp is not None and resp.status_code == 200
    r = {"detected": found, "url": url}
    if found:
        try:
            r["data"] = resp.json()
        except (json.JSONDecodeError, ValueError):
            r["content_type"] = resp.headers.get("content-type", "unknown")
    results["wellknown_pay"] = r


def check_apple_pay(base_url, results):
    """Check Apple Pay domain verification file.

    Per Apple docs: developer.apple.com/documentation/applepaywebmerchantregistrationapi/
    File must be at /.well-known/apple-developer-merchantid-domain-association
    Must NOT redirect (no 3xx). Must be served as binary/octet-stream.
    """
    path = "/.well-known/apple-developer-merchantid-domain-association"
    url = urljoin(base_url, path)

    headers = {"User-Agent": UA}
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT,
                            allow_redirects=False)
    except requests.RequestException:
        results["apple_pay"] = {"detected": False, "error": "connection_failed"}
        return

    if resp.status_code == 200:
        ct = resp.headers.get("content-type", "").lower()
        results["apple_pay"] = {
            "detected": True,
            "url": url,
            "content_type": ct,
            "size_bytes": len(resp.content),
            "spec_compliant": True,
        }
    elif 300 <= resp.status_code < 400:
        results["apple_pay"] = {
            "detected": False,
            "note": f"File redirects (HTTP {resp.status_code}) -- Apple does not allow redirects",
        }
    else:
        results["apple_pay"] = {
            "detected": False,
            "status": resp.status_code,
        }


def check_google_pay(base_url, parser, html, results):
    """Check for Google Pay indicators.

    Google Pay has no single verification file. Detection via:
    - pay.google.com script references
    - Google Pay button markup / API calls
    """
    gp_scripts = [s for s in parser.script_srcs if "pay.google.com" in s]
    gp_inline = bool(re.search(r'google[_\-]?pay|gpay', html, re.IGNORECASE))

    results["google_pay"] = {
        "detected": bool(gp_scripts or gp_inline),
        "scripts": gp_scripts,
        "inline_references": gp_inline,
    }


def check_other_providers(parser, html, results):
    """Detect other payment providers via script sources and HTML patterns."""
    providers = {}
    patterns = {
        "Square": [r"squareup\.com", r"square\.js"],
        "Adyen": [r"adyen\.com", r"adyen-checkout"],
        "Braintree": [r"braintreegateway\.com", r"braintree-web"],
        "Klarna": [r"klarna\.com", r"klarna-payments"],
        "Afterpay": [r"afterpay\.com", r"afterpay\.js"],
        "Shop Pay": [r"shop-pay", r"shopify.*payment"],
        "Amazon Pay": [r"amazonpay", r"amazon.*pay.*sdk"],
    }

    combined = " ".join(parser.script_srcs).lower() + " " + html[:50000].lower()

    for name, pats in patterns.items():
        for pat in pats:
            if re.search(pat, combined):
                providers[name] = True
                break

    results["other_providers"] = {
        "detected": len(providers) > 0,
        "providers": list(providers.keys()),
    }


def print_report(url, results):
    """Print human-readable report."""
    methods = []
    if results["stripe"]["detected"]:
        methods.append("Stripe")
    if results["paypal"]["detected"]:
        methods.append("PayPal")
    if results["x402"]["detected"]:
        methods.append("x402")
    if results["apple_pay"]["detected"]:
        methods.append("Apple Pay")
    if results["google_pay"]["detected"]:
        methods.append("Google Pay")
    if results["other_providers"]["detected"]:
        methods.extend(results["other_providers"]["providers"])
    if results["wellknown_pay"]["detected"]:
        methods.append(".well-known/pay")

    # Agent compatibility: Stripe (ACP/SPT) and x402 are agent-native
    agent_score = 0
    if results["stripe"]["detected"]:
        agent_score += 2
    if results["x402"]["detected"]:
        agent_score += 2
    if results["wellknown_pay"]["detected"]:
        agent_score += 2
    if results["paypal"]["detected"]:
        agent_score += 1
    if results["payment_meta"]["detected"]:
        agent_score += 1
    if results["apple_pay"]["detected"]:
        agent_score += 1

    level = "HIGH" if agent_score >= 4 else "MEDIUM" if agent_score >= 2 else "LOW"

    print(f"\n{'=' * 60}")
    print(f"  Payment Infrastructure Scan: {url}")
    print(f"  Payment methods: {len(methods)} detected")
    if methods:
        print(f"  Found: {', '.join(methods)}")
    print(f"  Agent-payment compatibility: {level}")
    print(f"{'=' * 60}")

    # Stripe
    s = results["stripe"]
    if s["detected"]:
        print(f"\n  [PASS] Stripe.js")
        for sc in s["scripts"]:
            print(f"    Script: {sc}")
        if s["inline_references"]:
            print(f"    Inline: Stripe() or loadStripe() found")
        if s["publishable_key_in_meta"]:
            print(f"    Publishable key in meta tag")
    else:
        print(f"\n  [FAIL] Stripe.js: not detected")

    # PayPal
    p = results["paypal"]
    if p["detected"]:
        print(f"\n  [PASS] PayPal SDK")
        for sc in p.get("scripts", []):
            print(f"    Script: {sc}")
    else:
        print(f"\n  [FAIL] PayPal SDK: not detected")

    # x402
    x = results["x402"]
    if x["detected"]:
        print(f"\n  [PASS] x402 Protocol Support")
        if x["has_402_response"]:
            print(f"    HTTP 402 Payment Required received")
        if x["x402_headers"]:
            for h, v in x["x402_headers"].items():
                print(f"    {h}: {v}")
    else:
        print(f"\n  [FAIL] x402: no 402 responses or payment headers")
        if x.get("paths_checked"):
            paths = [f"{p['path']}({p['status']})" for p in x["paths_checked"]]
            print(f"    Checked: {', '.join(paths)}")

    # Payment meta
    pm = results["payment_meta"]
    if pm["detected"]:
        print(f"\n  [PASS] Payment Meta Tags")
        for t in pm["tags"][:5]:
            print(f"    {t['property']}: {t['content']}")
    else:
        print(f"\n  [FAIL] Payment Meta Tags: none found")

    # .well-known/pay
    wk = results["wellknown_pay"]
    if wk["detected"]:
        print(f"\n  [PASS] /.well-known/pay")
    else:
        print(f"\n  [FAIL] /.well-known/pay: not found")

    # Apple Pay
    ap = results["apple_pay"]
    if ap["detected"]:
        print(f"\n  [PASS] Apple Pay domain verification")
        print(f"    Size: {ap.get('size_bytes', '?')} bytes")
        ct = ap.get("content_type", "")
        if "octet-stream" not in ct and ct:
            print(f"    [WARN] Content-Type '{ct}' -- Apple recommends application/octet-stream")
    else:
        note = ap.get("note", "")
        print(f"\n  [FAIL] Apple Pay: no domain verification file")
        if note:
            print(f"    {note}")

    # Google Pay
    gp = results["google_pay"]
    if gp["detected"]:
        print(f"\n  [PASS] Google Pay")
        for sc in gp.get("scripts", []):
            print(f"    Script: {sc}")
    else:
        print(f"\n  [FAIL] Google Pay: not detected")

    # Other
    op = results["other_providers"]
    if op["detected"]:
        print(f"\n  [INFO] Other providers: {', '.join(op['providers'])}")

    # Recommendations
    print(f"\n  Recommendations:")
    if not s["detected"]:
        print(f"    - Add Stripe for ACP/SPT agent payment support")
    if not x["detected"]:
        print(f"    - Consider x402 for API micropayments (pay-per-request)")
    if not wk["detected"]:
        print(f"    - Add /.well-known/pay for payment discovery")
    if not pm["detected"]:
        print(f"    - Add payment meta tags for agent discovery")
    print(f"    - Agent compatibility: {level} ({len(methods)} method(s))")
    print()


def main():
    ap = argparse.ArgumentParser(
        description="Scan a URL for payment infrastructure")
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

    check_stripe(parser, html, results)
    check_paypal(parser, results)
    check_x402(base, results)
    check_payment_meta(parser, results)
    check_wellknown_pay(base, results)
    check_apple_pay(base, results)
    check_google_pay(base, parser, html, results)
    check_other_providers(parser, html, results)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_report(url, results)

    has_any = any([
        results["stripe"]["detected"],
        results["paypal"]["detected"],
        results["x402"]["detected"],
        results["wellknown_pay"]["detected"],
        results["apple_pay"]["detected"],
        results["google_pay"]["detected"],
        results["other_providers"]["detected"],
    ])
    sys.exit(0 if has_any else 1)


if __name__ == "__main__":
    main()
