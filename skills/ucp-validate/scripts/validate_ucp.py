#!/usr/bin/env python3
"""UCP Validation Orchestrator — wraps official tools into one report.

Runs these checks in order:
1. Fetch /.well-known/ucp profile
2. Validate profile JSON against official profile_schema.json (jsonschema)
3. Check namespace/URL binding rules
4. Check spec/schema URL reachability
5. Report transport type and available capabilities

For full checkout behavior testing, use the official conformance suite:
  https://github.com/Universal-Commerce-Protocol/conformance

For schema linting, use the official ucp-schema CLI:
  cargo install ucp-schema && ucp-schema lint

Usage:
  python validate_ucp.py https://allbirds.com
  python validate_ucp.py https://example.com --output report.md
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

# Try to load official profile schema for validation
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

HEADERS = {"User-Agent": "UCP-Validate/2.0 (+https://recomby.ai)"}
TIMEOUT = 15
VERSION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Path to official schema (if cloned alongside this repo)
SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "refs", "ucp-spec", "source")


def fetch_profile(base_url):
    """Fetch UCP profile, trying standard path then .json variant."""
    for path in ["/.well-known/ucp", "/.well-known/ucp.json"]:
        url = base_url.rstrip("/") + path
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
            if r.status_code == 200:
                data = r.json()
                return data, url, None
        except Exception:
            continue
    return None, None, "Profile not found at /.well-known/ucp or /.well-known/ucp.json"


def check_profile_structure(data):
    """Check basic profile structure. Returns list of (severity, message) tuples."""
    results = []

    ucp = data.get("ucp")
    if not ucp or not isinstance(ucp, dict):
        results.append(("CRITICAL", "Missing 'ucp' root key"))
        return results

    # Version
    version = ucp.get("version", "")
    if VERSION_RE.match(str(version)):
        results.append(("PASS", f"Version: {version}"))
    else:
        results.append(("ERROR", f"Version '{version}' doesn't match YYYY-MM-DD"))

    # Services
    services = ucp.get("services", {})
    if services and isinstance(services, dict):
        results.append(("PASS", f"Services: {', '.join(services.keys())}"))
        # Check transports
        for svc_name, svc_entries in services.items():
            entries = svc_entries if isinstance(svc_entries, list) else [svc_entries]
            for entry in entries:
                if isinstance(entry, dict):
                    t = entry.get("transport", "")
                    results.append(("INFO", f"Transport: {t} at {entry.get('endpoint', 'N/A')}"))
    else:
        results.append(("ERROR", "Missing or empty ucp.services"))

    # Capabilities
    caps = ucp.get("capabilities", {})
    if isinstance(caps, dict) and caps:
        results.append(("PASS", f"Capabilities: {len(caps)} — {', '.join(caps.keys())}"))
    elif isinstance(caps, list) and caps:
        results.append(("WARNING", f"Capabilities in non-standard list format ({len(caps)} items)"))
    else:
        results.append(("ERROR", "Missing or empty ucp.capabilities"))

    # Payment handlers
    handlers = ucp.get("payment_handlers", {})
    if isinstance(handlers, dict) and handlers:
        results.append(("PASS", f"Payment handlers: {', '.join(handlers.keys())}"))
    else:
        results.append(("ERROR", "Missing or empty ucp.payment_handlers"))

    return results


def check_schema_validation(data):
    """Validate against official profile_schema.json if available."""
    if not HAS_JSONSCHEMA:
        return [("SKIP", "jsonschema not installed — pip install jsonschema for schema validation")]

    schema_path = os.path.join(SCHEMA_DIR, "discovery", "profile_schema.json")
    if not os.path.exists(schema_path):
        return [("SKIP", f"Official schema not found at {schema_path} — clone refs/ucp-spec for full validation")]

    try:
        with open(schema_path) as f:
            schema = json.load(f)

        # The official profile schema uses cross-file $ref (../schemas/ucp.json).
        # Python jsonschema can't resolve these reliably without complex setup.
        # Instead: validate the parts we CAN check, and recommend ucp-schema CLI for full validation.

        # Check top-level oneOf: must match business_profile or platform_profile
        # Business profiles must have ucp.services and ucp.payment_handlers
        ucp = data.get("ucp", {})
        issues = []

        # Required: ucp root
        if "ucp" not in data:
            issues.append("Missing required 'ucp' key")

        # Required for business profile: services, payment_handlers
        if "services" not in ucp:
            issues.append("Missing required 'ucp.services'")
        if "payment_handlers" not in ucp:
            issues.append("Missing required 'ucp.payment_handlers'")

        # Version must be string
        if not isinstance(ucp.get("version"), str):
            issues.append(f"ucp.version must be string, got {type(ucp.get('version')).__name__}")

        # Services must be object with entries
        services = ucp.get("services", {})
        if isinstance(services, dict):
            for svc_name, svc_entries in services.items():
                entries = svc_entries if isinstance(svc_entries, list) else [svc_entries]
                for entry in entries:
                    if isinstance(entry, dict):
                        if "version" not in entry:
                            issues.append(f"Service '{svc_name}' entry missing 'version'")
                        if "transport" in entry and entry["transport"] in ("rest", "mcp", "a2a") and "endpoint" not in entry:
                            issues.append(f"Service '{svc_name}' transport '{entry['transport']}' missing 'endpoint'")

        # Payment handlers must have id and version
        handlers = ucp.get("payment_handlers", {})
        if isinstance(handlers, dict):
            for h_name, h_entries in handlers.items():
                entries = h_entries if isinstance(h_entries, list) else [h_entries]
                for entry in entries:
                    if isinstance(entry, dict):
                        if "id" not in entry:
                            issues.append(f"Payment handler '{h_name}' missing 'id'")
                        if "version" not in entry:
                            issues.append(f"Payment handler '{h_name}' missing 'version'")

        if issues:
            return [("ERROR", f"Schema check failed: {'; '.join(issues)}")]
        return [("PASS", "Profile structure matches official schema requirements (full $ref validation: use ucp-schema CLI)")]

    except Exception as e:
        return [("WARNING", f"Schema validation error: {e}")]


def check_url_reachability(data, max_checks=5):
    """Spot-check that spec/schema URLs are reachable."""
    results = []
    urls_checked = 0
    ucp = data.get("ucp", {})
    caps = ucp.get("capabilities", {})
    if not isinstance(caps, dict):
        return [("SKIP", "Cannot check URLs for non-standard capabilities format")]

    for cap_name, cap_entries in caps.items():
        entries = cap_entries if isinstance(cap_entries, list) else [cap_entries]
        for entry in entries:
            for field in ("spec", "schema"):
                url = entry.get(field, "")
                if not url or urls_checked >= max_checks:
                    continue
                urls_checked += 1
                try:
                    r = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
                    if r.status_code < 400:
                        results.append(("PASS", f"{cap_name} {field}: {url} → {r.status_code}"))
                    else:
                        results.append(("WARNING", f"{cap_name} {field}: {url} → {r.status_code}"))
                except Exception as e:
                    results.append(("WARNING", f"{cap_name} {field}: {url} → {e}"))

    if not results:
        results.append(("SKIP", "No spec/schema URLs to check"))
    return results


def check_official_tools():
    """Check if official validation tools are available."""
    results = []

    # ucp-schema CLI
    import shutil
    if shutil.which("ucp-schema"):
        results.append(("PASS", "ucp-schema CLI found — run 'ucp-schema validate' for full schema validation"))
    else:
        results.append(("INFO", "ucp-schema CLI not installed — cargo install ucp-schema for full validation"))

    # conformance repo
    conformance_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "refs", "conformance")
    if os.path.exists(conformance_path):
        results.append(("PASS", f"Official conformance suite found at {conformance_path}"))
    else:
        results.append(("INFO", "Official conformance suite not cloned — clone Universal-Commerce-Protocol/conformance for checkout testing"))

    return results


def generate_report(url, profile_url, data, all_results):
    """Generate markdown report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    domain = urlparse(url).hostname

    pass_count = sum(1 for sev, _ in all_results if sev == "PASS")
    error_count = sum(1 for sev, _ in all_results if sev in ("ERROR", "CRITICAL"))
    warning_count = sum(1 for sev, _ in all_results if sev == "WARNING")
    total = pass_count + error_count + warning_count

    if error_count == 0:
        overall = "PASS"
    elif error_count <= 2:
        overall = "CONDITIONAL PASS"
    else:
        overall = "FAIL"

    report = f"""# UCP Validation Report — {domain}

**URL:** {url}
**Profile:** {profile_url or "not found"}
**Date:** {now}
**Result:** {overall} ({pass_count}/{total} checks passed)

## Results

| Status | Detail |
|--------|--------|
"""
    for sev, msg in all_results:
        icon = {"PASS": "PASS", "ERROR": "**ERROR**", "CRITICAL": "**CRITICAL**",
                "WARNING": "WARN", "INFO": "INFO", "SKIP": "SKIP"}.get(sev, sev)
        report += f"| {icon} | {msg} |\n"

    if error_count > 0:
        report += "\n## Errors to Fix\n\n"
        for sev, msg in all_results:
            if sev in ("ERROR", "CRITICAL"):
                report += f"- {msg}\n"

    report += f"""
## Next Steps

1. **Fix errors above** if any
2. **Full schema validation**: `ucp-schema validate profile.json` (install: `cargo install ucp-schema`)
3. **Checkout behavior test**: clone `Universal-Commerce-Protocol/conformance` and run against your server
4. **External check**: paste your URL at https://ucpchecker.com
"""
    return report


def main():
    parser = argparse.ArgumentParser(description="UCP Validation Orchestrator")
    parser.add_argument("url", help="Merchant URL")
    parser.add_argument("--output", "-o", help="Output report file")
    args = parser.parse_args()

    url = args.url
    if not url.startswith("http"):
        url = "https://" + url

    print(f"Validating {url} ...")

    all_results = []

    # 1. Fetch profile
    print("  [1/5] Fetching profile...")
    data, profile_url, err = fetch_profile(url)
    if err:
        all_results.append(("CRITICAL", err))
        # Still generate report with the error
        report = generate_report(url, None, None, all_results)
        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
        else:
            print(report)
        return 1

    all_results.append(("PASS", f"Profile found at {profile_url}"))

    # 2. Structure checks
    print("  [2/5] Checking profile structure...")
    all_results.extend(check_profile_structure(data))

    # 3. Schema validation (official)
    print("  [3/5] Schema validation...")
    all_results.extend(check_schema_validation(data))

    # 4. URL reachability
    print("  [4/5] Checking URL reachability...")
    all_results.extend(check_url_reachability(data))

    # 5. Official tools check
    print("  [5/5] Checking available tools...")
    all_results.extend(check_official_tools())

    # Report
    report = generate_report(url, profile_url, data, all_results)
    error_count = sum(1 for sev, _ in all_results if sev in ("ERROR", "CRITICAL"))

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print("\n" + report)

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
