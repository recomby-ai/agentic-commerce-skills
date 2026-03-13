#!/usr/bin/env python3
"""Validate a JSON-LD snippet against Schema.org type requirements.

Property requirements sourced from Google Search Central documentation
(developers.google.com/search/docs/appearance/structured-data/).
Accepts a file path or reads from stdin.

Usage:
    python validate_schema.py --file schema.json
    python validate_schema.py --file schema.jsonld --json
    cat schema.json | python validate_schema.py
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Schema.org type requirements per Google Search Central documentation
# (developers.google.com/search/docs/appearance/structured-data/)
#
# "required" = Google says required for rich results eligibility
# "recommended" = Google says recommended for better rich results
# Types without Google-specific docs use schema.org definitions (marked)
# ---------------------------------------------------------------------------

TYPE_REQUIREMENTS = {
    # Google: no required properties; all recommended
    # Source: developers.google.com/search/docs/appearance/structured-data/organization
    "Organization": {
        "required": [],
        "recommended": ["name", "url", "logo", "description", "sameAs",
                         "contactPoint", "address"],
        "source": "Google Search Central",
    },
    # Google: name and url recommended
    "WebSite": {
        "required": [],
        "recommended": ["name", "url", "publisher", "potentialAction"],
        "source": "Google Search Central",
    },
    # Google: name required + one of (review, aggregateRating, offers)
    # Source: developers.google.com/search/docs/appearance/structured-data/product-snippet
    "Product": {
        "required": ["name"],
        "required_one_of": ["review", "aggregateRating", "offers"],
        "recommended": ["image", "description", "brand", "sku", "mpn"],
        "source": "Google Search Central",
    },
    # No Google-specific page; uses schema.org definition
    "Service": {
        "required": ["name"],
        "recommended": ["description", "provider", "offers", "serviceType", "areaServed"],
        "source": "schema.org",
    },
    # Google: name, address required
    # Source: developers.google.com/search/docs/appearance/structured-data/local-business
    "LocalBusiness": {
        "required": ["name", "address"],
        "recommended": ["telephone", "openingHoursSpecification", "geo", "image",
                         "priceRange", "url"],
        "source": "Google Search Central",
    },
    # Google: mainEntity required
    # Source: developers.google.com/search/docs/appearance/structured-data/faqpage
    "FAQPage": {
        "required": ["mainEntity"],
        "recommended": [],
        "source": "Google Search Central",
    },
    # Google: price required; priceCurrency recommended
    # Source: developers.google.com/search/docs/appearance/structured-data/product-snippet
    "Offer": {
        "required": ["price"],
        "recommended": ["priceCurrency", "availability", "url", "priceValidUntil"],
        "source": "Google Search Central",
    },
    # Google: lowPrice, priceCurrency required
    "AggregateOffer": {
        "required": ["lowPrice", "priceCurrency"],
        "recommended": ["highPrice", "offerCount"],
        "source": "Google Search Central",
    },
    # Google: name required, offers recommended
    # Source: developers.google.com/search/docs/appearance/structured-data/software-app
    "SoftwareApplication": {
        "required": ["name"],
        "recommended": ["applicationCategory", "operatingSystem", "offers",
                         "aggregateRating"],
        "source": "Google Search Central",
    },
    # Google: itemListElement required
    "BreadcrumbList": {
        "required": ["itemListElement"],
        "recommended": [],
        "source": "Google Search Central",
    },
    # Google: headline required
    # Source: developers.google.com/search/docs/appearance/structured-data/article
    "Article": {
        "required": ["headline"],
        "recommended": ["author", "datePublished", "image", "publisher",
                         "dateModified"],
        "source": "Google Search Central",
    },
    # Google: author, reviewRating recommended; itemReviewed required for standalone
    # Source: developers.google.com/search/docs/appearance/structured-data/review-snippet
    "Review": {
        "required": [],
        "recommended": ["reviewRating", "author", "datePublished", "reviewBody",
                         "itemReviewed"],
        "source": "Google Search Central",
    },
    # Google: ratingValue required
    "AggregateRating": {
        "required": ["ratingValue"],
        "recommended": ["reviewCount", "bestRating", "ratingCount"],
        "source": "Google Search Central",
    },
    # Used inside FAQPage
    "Question": {
        "required": ["name", "acceptedAnswer"],
        "recommended": [],
        "source": "Google Search Central",
    },
    "Answer": {
        "required": ["text"],
        "recommended": [],
        "source": "Google Search Central",
    },
    # schema.org definitions (no Google-specific page)
    "Person": {
        "required": ["name"],
        "recommended": ["url", "image", "jobTitle", "sameAs"],
        "source": "schema.org",
    },
    # Google: name, startDate, location required
    # Source: developers.google.com/search/docs/appearance/structured-data/event
    "Event": {
        "required": ["name", "startDate", "location"],
        "recommended": ["endDate", "description", "offers", "image",
                         "performer", "organizer"],
        "source": "Google Search Central",
    },
    # Google: name, uploadDate required (for Video rich results)
    # Source: developers.google.com/search/docs/appearance/structured-data/video
    "VideoObject": {
        "required": ["name", "uploadDate", "thumbnailUrl"],
        "recommended": ["description", "contentUrl", "duration", "embedUrl"],
        "source": "Google Search Central",
    },
}

VALID_CONTEXTS = {
    "https://schema.org", "http://schema.org",
    "https://schema.org/", "http://schema.org/",
}


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------

class Result:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def note(self, msg):
        self.info.append(msg)

    @property
    def valid(self):
        return len(self.errors) == 0

    def to_dict(self):
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
        }


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

def validate_jsonld(data, result, path="root"):
    """Validate a JSON-LD object recursively."""

    # Check @context at root
    if path == "root":
        ctx = data.get("@context", "")
        if not ctx:
            result.error("Missing @context")
        elif ctx not in VALID_CONTEXTS:
            result.error(f"Invalid @context: '{ctx}' (use 'https://schema.org')")
        else:
            result.note(f"@context: {ctx}")

    # Handle @graph
    if "@graph" in data:
        graph = data["@graph"]
        if not isinstance(graph, list):
            result.error("@graph must be an array")
            return
        result.note(f"@graph with {len(graph)} entities")
        for i, item in enumerate(graph):
            validate_jsonld(item, result, f"@graph[{i}]")
        return

    # Check @type
    schema_type = data.get("@type", "")
    if not schema_type:
        result.error(f"{path}: Missing @type")
        return

    # Handle array types (e.g. ["Organization", "LocalBusiness"])
    if isinstance(schema_type, list):
        schema_type = schema_type[0] if schema_type else ""
        result.note(f"{path}: @type = {data['@type']} (using first)")

    result.note(f"{path}: @type = {schema_type}")

    reqs = TYPE_REQUIREMENTS.get(schema_type)
    if reqs:
        source = reqs.get("source", "schema.org")
        for field in reqs["required"]:
            if field not in data:
                result.error(f"{path} ({schema_type}): Missing required '{field}'"
                             f" [per {source}]")
            elif _is_empty(data[field]):
                result.error(f"{path} ({schema_type}): '{field}' is empty"
                             f" [per {source}]")

        # Handle "required_one_of" (e.g. Product needs one of review/aggregateRating/offers)
        one_of = reqs.get("required_one_of", [])
        if one_of:
            has_any = [f for f in one_of if f in data and not _is_empty(data[f])]
            if not has_any:
                result.error(f"{path} ({schema_type}): Must include at least one of"
                             f" {', '.join(one_of)} [per {source}]")
            else:
                result.note(f"{path} ({schema_type}): Has {', '.join(has_any)}"
                            f" (one of {', '.join(one_of)} required)")

        for field in reqs["recommended"]:
            if field not in data:
                result.warn(f"{path} ({schema_type}): Missing recommended '{field}'"
                            f" [per {source}]")
    else:
        result.warn(f"{path}: Type '{schema_type}' not in our validation rules"
                    " -- check schema.org/{type} for properties")

    # Type-specific checks
    if schema_type == "Offer":
        price = data.get("price", "")
        if price and isinstance(price, str) and not re.match(r"^\d+(\.\d{1,2})?$", price):
            result.warn(f"{path}: price '{price}' should be numeric (e.g. '49.99')")
        cur = data.get("priceCurrency", "")
        if cur and len(cur) != 3:
            result.error(f"{path}: priceCurrency must be 3-letter ISO 4217")

    if schema_type in ("AggregateRating", "Rating"):
        rv = data.get("ratingValue")
        if rv is not None:
            try:
                val = float(rv)
                best = float(data.get("bestRating", 5))
                if val > best:
                    result.error(f"{path}: ratingValue ({val}) > bestRating ({best})")
                if val < 0:
                    result.error(f"{path}: ratingValue negative")
            except (ValueError, TypeError):
                result.error(f"{path}: ratingValue must be numeric")

    # Recurse into nested typed objects
    for key, value in data.items():
        if key.startswith("@"):
            continue
        if isinstance(value, dict) and "@type" in value:
            validate_jsonld(value, result, f"{path}.{key}")
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict) and "@type" in item:
                    validate_jsonld(item, result, f"{path}.{key}[{i}]")


def _is_empty(value):
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False


# ---------------------------------------------------------------------------
# Input loading
# ---------------------------------------------------------------------------

def load_input(file_path):
    """Load JSON-LD from file path."""
    path = Path(file_path)
    if not path.exists():
        print(f"ERROR: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8")

    # Handle HTML files with embedded JSON-LD
    if path.suffix in (".html", ".htm"):
        matches = re.findall(
            r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>',
            text, re.DOTALL
        )
        if not matches:
            print("ERROR: No JSON-LD found in HTML file", file=sys.stderr)
            sys.exit(1)
        if len(matches) == 1:
            return json.loads(matches[0])
        return {"@context": "https://schema.org",
                "@graph": [json.loads(m) for m in matches]}

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate Schema.org JSON-LD structured data")
    parser.add_argument("--file", "-f", default=None,
                        help="Path to .json or .jsonld file")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output results as JSON")
    args = parser.parse_args()

    # Read from file or stdin
    if args.file:
        data = load_input(args.file)
    elif not sys.stdin.isatty():
        raw = sys.stdin.read()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON from stdin: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        print("\nERROR: Specify --file or pipe JSON to stdin", file=sys.stderr)
        sys.exit(1)

    result = Result()
    validate_jsonld(data, result)

    if args.json_output:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if result.errors:
            print("ERRORS:")
            for e in result.errors:
                print(f"  [x] {e}")
        if result.warnings:
            print("WARNINGS:")
            for w in result.warnings:
                print(f"  [!] {w}")
        if result.info:
            print("INFO:")
            for i in result.info:
                print(f"  [+] {i}")
        print()
        if result.valid:
            print(f"VALID ({len(result.warnings)} warnings)")
        else:
            print(f"INVALID ({len(result.errors)} errors, {len(result.warnings)} warnings)")

    sys.exit(0 if result.valid else 1)


if __name__ == "__main__":
    main()
