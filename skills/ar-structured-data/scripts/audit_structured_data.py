#!/usr/bin/env python3
"""Audit structured data on a live URL.

Fetches the page, finds all JSON-LD blocks and microdata, reports types,
completeness, and issues. Suggests what should be there if nothing found.

Usage:
    python audit_structured_data.py --url https://example.com
    python audit_structured_data.py --url https://example.com --json
    python audit_structured_data.py --url https://example.com --verbose
"""

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("ERROR: 'requests' required. pip install requests", file=sys.stderr)
    sys.exit(1)

HEADERS = {"User-Agent": "ar-structured-data/1.0 auditor"}
TIMEOUT = 15


# ---------------------------------------------------------------------------
# HTML parser
# ---------------------------------------------------------------------------

class SDExtractor(HTMLParser):
    """Extract JSON-LD blocks, microdata, and page metadata from HTML."""

    def __init__(self):
        super().__init__()
        self.jsonld_blocks = []
        self.microdata_types = []
        self.title = ""
        self.meta = {}
        self._in_jsonld = False
        self._jsonld_buf = []
        self._in_title = False
        self._title_buf = []

    def handle_starttag(self, tag, attrs):
        ad = dict(attrs)
        if tag == "script" and ad.get("type") == "application/ld+json":
            self._in_jsonld = True
            self._jsonld_buf = []
        elif tag == "title":
            self._in_title = True
            self._title_buf = []
        elif tag == "meta":
            name = ad.get("name", ad.get("property", "")).lower()
            content = ad.get("content", "")
            if name and content:
                self.meta[name] = content

        itemtype = ad.get("itemtype", "")
        if itemtype:
            self.microdata_types.append(itemtype)

    def handle_endtag(self, tag):
        if tag == "script" and self._in_jsonld:
            self._in_jsonld = False
            raw = "".join(self._jsonld_buf)
            try:
                self.jsonld_blocks.append(json.loads(raw))
            except (json.JSONDecodeError, ValueError):
                self.jsonld_blocks.append({"_parse_error": raw[:200]})
        elif tag == "title" and self._in_title:
            self._in_title = False
            self.title = "".join(self._title_buf).strip()

    def handle_data(self, data):
        if self._in_jsonld:
            self._jsonld_buf.append(data)
        elif self._in_title:
            self._title_buf.append(data)


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

TYPE_KEY_PROPS = {
    "Organization": ["name", "url", "logo", "description", "sameAs"],
    "WebSite": ["name", "url", "publisher"],
    "Product": ["name", "description", "image", "offers", "brand"],
    "Service": ["name", "description", "provider", "offers"],
    "LocalBusiness": ["name", "address", "telephone", "geo"],
    "FAQPage": ["mainEntity"],
    "SoftwareApplication": ["name", "applicationCategory", "offers"],
    "Article": ["headline", "author", "datePublished", "image"],
    "BreadcrumbList": ["itemListElement"],
    "Offer": ["price", "priceCurrency", "availability"],
    "AggregateRating": ["ratingValue", "reviewCount"],
    "Review": ["reviewRating", "author"],
    "Person": ["name", "url"],
    "VideoObject": ["name", "uploadDate", "thumbnailUrl"],
    "WebPage": ["name", "url"],
    "SearchAction": ["target", "query-input"],
}

RECOMMENDED_FOR_PAGE = {
    "homepage": ["Organization", "WebSite"],
    "product": ["Product", "BreadcrumbList"],
    "service": ["Service", "Organization"],
    "blog": ["Article", "BreadcrumbList"],
    "faq": ["FAQPage"],
    "saas": ["SoftwareApplication", "Organization", "WebSite"],
}


def flatten_entities(data):
    """Flatten JSON-LD into individual entities."""
    out = []
    if isinstance(data, list):
        for item in data:
            out.extend(flatten_entities(item))
    elif isinstance(data, dict):
        if "@graph" in data:
            for item in data["@graph"]:
                out.extend(flatten_entities(item))
        else:
            out.append(data)
            for key, val in data.items():
                if key.startswith("@"):
                    continue
                if isinstance(val, dict) and "@type" in val:
                    out.append(val)
                elif isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict) and "@type" in item:
                            out.append(item)
    return out


def analyze_entity(entity):
    schema_type = entity.get("@type", "Unknown")
    if isinstance(schema_type, list):
        schema_type = schema_type[0] if schema_type else "Unknown"
    props = [k for k in entity.keys() if not k.startswith("@")]
    key_props = TYPE_KEY_PROPS.get(schema_type, [])
    present = [p for p in key_props if p in entity]
    missing = [p for p in key_props if p not in entity]
    issues = []

    # Check for empty values in present props
    for p in present:
        v = entity[p]
        if v is None or (isinstance(v, str) and not v.strip()):
            issues.append(f"'{p}' is empty")
        if isinstance(v, list) and len(v) == 0:
            issues.append(f"'{p}' is empty array")

    return {
        "type": schema_type,
        "id": entity.get("@id", ""),
        "properties": len(props),
        "completeness": f"{len(present)}/{len(key_props)}" if key_props else "N/A",
        "present": present,
        "missing": missing,
        "issues": issues,
    }


def guess_page_type(url, title, meta):
    path = urlparse(url).path.lower()
    text = (title + " " + path + " " + meta.get("description", "")).lower()
    if path in ("/", "") or path.endswith("/index"):
        return "homepage"
    if any(w in text for w in ("product", "buy", "shop", "price")):
        return "product"
    if any(w in text for w in ("faq", "frequently asked")):
        return "faq"
    if any(w in text for w in ("blog", "article", "post")):
        return "blog"
    if any(w in text for w in ("service", "consulting")):
        return "service"
    if any(w in text for w in ("app", "software", "saas", "platform")):
        return "saas"
    return "homepage"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Audit structured data on a webpage")
    parser.add_argument("--url", required=True, help="URL to audit")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output results as JSON")
    parser.add_argument("--verbose", action="store_true",
                        help="Show detailed property lists")
    args = parser.parse_args()

    url = args.url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Fetch
    try:
        resp = requests.get(url, timeout=TIMEOUT, allow_redirects=True,
                            headers=HEADERS)
        resp.raise_for_status()
    except Exception as e:
        print(f"ERROR: Failed to fetch {url}: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse
    ext = SDExtractor()
    ext.feed(resp.text)

    # Flatten and analyze
    all_entities = []
    for block in ext.jsonld_blocks:
        all_entities.extend(flatten_entities(block))

    analyzed = [analyze_entity(e) for e in all_entities if "_parse_error" not in e]
    parse_errors = [e for e in ext.jsonld_blocks if "_parse_error" in e]
    found_types = {a["type"] for a in analyzed}

    # Page type guess and suggestions
    page_type = guess_page_type(url, ext.title, ext.meta)
    recommended = RECOMMENDED_FOR_PAGE.get(page_type, ["Organization"])
    suggestions = [f"Add {t} schema (recommended for {page_type} pages)"
                   for t in recommended if t not in found_types]
    if "Organization" not in found_types and "Organization" not in recommended:
        suggestions.append("Add Organization schema (foundational for all sites)")

    report = {
        "url": url,
        "title": ext.title,
        "jsonld_blocks": len(ext.jsonld_blocks),
        "parse_errors": len(parse_errors),
        "entities": analyzed,
        "types_found": sorted(found_types),
        "microdata_types": ext.microdata_types,
        "page_type_guess": page_type,
        "suggestions": suggestions,
    }

    if args.json_output:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Structured Data Audit: {url}")
        print(f"Page title: {ext.title}")
        print(f"JSON-LD blocks: {report['jsonld_blocks']}")
        if parse_errors:
            print(f"Parse errors: {len(parse_errors)}")
        print(f"Types found: {', '.join(report['types_found']) or 'None'}")
        if ext.microdata_types:
            print(f"Microdata: {', '.join(ext.microdata_types)}")
        print()

        if not analyzed:
            print("No structured data found on this page.")
        else:
            for ent in analyzed:
                print(f"  [{ent['type']}]")
                if ent["id"]:
                    print(f"    @id: {ent['id']}")
                print(f"    Properties: {ent['properties']}, Completeness: {ent['completeness']}")
                if args.verbose and ent["present"]:
                    print(f"    Present: {', '.join(ent['present'])}")
                if ent["missing"]:
                    print(f"    Missing: {', '.join(ent['missing'])}")
                if ent["issues"]:
                    for issue in ent["issues"]:
                        print(f"    [!] {issue}")
                print()

        if suggestions:
            print("Suggestions:")
            for s in suggestions:
                print(f"  - {s}")
        print()


if __name__ == "__main__":
    main()
