#!/usr/bin/env python3
"""Validate AI agent identity and auth endpoints for a URL.

Checks per official specs:
  - .well-known/openid-configuration (OpenID Connect Discovery 1.0)
  - .well-known/agent.json (A2A protocol, a2a-protocol.org)
  - .well-known/oauth-authorization-server (RFC 8414)
  - CORS headers on discovered endpoints
  - Agent-specific OAuth scopes if metadata found

Usage:
    python validate_identity.py --url https://example.com
    python validate_identity.py --url https://example.com --json
"""

import argparse
import json
import sys
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("ERROR: 'requests' required. pip install requests", file=sys.stderr)
    sys.exit(1)

HEADERS = {"User-Agent": "ar-identity/1.0 validator"}
TIMEOUT = 12


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

    def print_report(self):
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


def fetch(url, method="GET"):
    """Fetch URL -> (status|None, headers_dict, text_or_error)."""
    try:
        if method == "OPTIONS":
            resp = requests.options(url, timeout=TIMEOUT, allow_redirects=True,
                                    headers={**HEADERS,
                                             "Origin": "https://agent.example.com"})
        else:
            resp = requests.get(url, timeout=TIMEOUT, allow_redirects=True,
                                headers=HEADERS)
        return resp.status_code, {k.lower(): v for k, v in resp.headers.items()}, resp.text
    except requests.RequestException as e:
        return None, {}, str(e)


# ---- .well-known/openid-configuration (OpenID Connect Discovery 1.0) ----

def check_openid_config(base, result):
    """Per OpenID Connect Discovery 1.0 spec, REQUIRED response fields:
    issuer, authorization_endpoint, token_endpoint, jwks_uri,
    response_types_supported, subject_types_supported,
    id_token_signing_alg_values_supported
    """
    url = base + "/.well-known/openid-configuration"
    status, headers, body = fetch(url)
    if status is None:
        result.add("openid-config", "accessible", "FAIL",
                    f"Connection error: {body}")
        return None
    if status == 404:
        result.add("openid-config", "accessible", "INFO",
                    "Not found (404) -- optional endpoint")
        return None
    if status != 200:
        result.add("openid-config", "accessible", "WARN", f"HTTP {status}")
        return None
    result.add("openid-config", "accessible", "PASS")

    try:
        config = json.loads(body)
    except json.JSONDecodeError as e:
        result.add("openid-config", "valid JSON", "FAIL", str(e))
        return None
    result.add("openid-config", "valid JSON", "PASS")

    # REQUIRED per OpenID Connect Discovery 1.0
    oidc_required = [
        "issuer", "authorization_endpoint", "token_endpoint",
        "jwks_uri", "response_types_supported", "subject_types_supported",
        "id_token_signing_alg_values_supported",
    ]
    for field in oidc_required:
        if field in config:
            val = config[field]
            display = str(val)[:60] if not isinstance(val, list) else str(val[:3])
            result.add("openid-config", f"{field} (REQUIRED per OIDC spec)",
                        "PASS", display)
        else:
            result.add("openid-config", f"{field} (REQUIRED per OIDC spec)",
                        "FAIL", "Missing")

    # OPTIONAL but useful for agents
    if "scopes_supported" in config:
        scopes = config["scopes_supported"]
        result.add("openid-config", "scopes_supported", "PASS",
                    ", ".join(scopes[:5]))
    if "grant_types_supported" in config:
        grants = config["grant_types_supported"]
        result.add("openid-config", "grant_types_supported", "PASS",
                    ", ".join(grants))
        if "client_credentials" in grants:
            result.add("openid-config", "client_credentials grant", "PASS",
                        "Supports machine-to-machine auth")

    return config


# ---- .well-known/agent.json (A2A protocol spec) ----

def check_agent_card(base, result):
    """Per A2A protocol spec (a2a-protocol.org), REQUIRED fields:
    name, description, url, version, skills,
    capabilities, defaultInputModes, defaultOutputModes
    """
    url = base + "/.well-known/agent.json"
    status, headers, body = fetch(url)
    if status is None:
        result.add("agent.json (A2A)", "accessible", "FAIL",
                    f"Connection error: {body}")
        return
    if status == 404:
        result.add("agent.json (A2A)", "accessible", "INFO",
                    "Not found (404) -- no A2A agent card")
        return
    if status != 200:
        result.add("agent.json (A2A)", "accessible", "WARN", f"HTTP {status}")
        return
    result.add("agent.json (A2A)", "accessible", "PASS")

    try:
        card = json.loads(body)
    except json.JSONDecodeError as e:
        result.add("agent.json (A2A)", "valid JSON", "FAIL", str(e))
        return
    result.add("agent.json (A2A)", "valid JSON", "PASS")

    # REQUIRED per A2A spec
    a2a_required = ["name", "description", "url", "version", "skills"]
    for field in a2a_required:
        if field in card:
            val = card[field]
            if field == "skills" and isinstance(val, list):
                result.add("agent.json (A2A)", f"{field} (REQUIRED per A2A spec)",
                            "PASS", f"{len(val)} skills")
            else:
                result.add("agent.json (A2A)", f"{field} (REQUIRED per A2A spec)",
                            "PASS", str(val)[:60])
        else:
            result.add("agent.json (A2A)", f"{field} (REQUIRED per A2A spec)",
                        "FAIL", "Missing")

    # Also required per spec
    for field in ["capabilities", "defaultInputModes", "defaultOutputModes"]:
        if field in card:
            result.add("agent.json (A2A)", f"{field} (REQUIRED per A2A spec)", "PASS")
        else:
            result.add("agent.json (A2A)", f"{field} (REQUIRED per A2A spec)", "WARN",
                        "Missing")

    # Optional auth config
    if "securitySchemes" in card or "security" in card:
        result.add("agent.json (A2A)", "authentication config", "PASS",
                    "securitySchemes/security defined")
    else:
        result.add("agent.json (A2A)", "authentication config", "INFO",
                    "No auth defined -- not recommended for production (per spec)")

    # Check CORS on agent.json endpoint
    check_cors(url, "agent.json (A2A)", result)


# ---- .well-known/oauth-authorization-server (RFC 8414) ----

def check_oauth_as_metadata(base, result):
    """Per RFC 8414, REQUIRED response fields:
    issuer, authorization_endpoint (unless no auth grant types),
    token_endpoint (unless only implicit grant), response_types_supported
    """
    url = base + "/.well-known/oauth-authorization-server"
    status, headers, body = fetch(url)
    if status is None:
        result.add("oauth-as-meta", "accessible", "FAIL",
                    f"Connection error: {body}")
        return None
    if status == 404:
        result.add("oauth-as-meta", "accessible", "INFO",
                    "Not found (404) -- optional per RFC 8414")
        return None
    if status != 200:
        result.add("oauth-as-meta", "accessible", "WARN", f"HTTP {status}")
        return None
    result.add("oauth-as-meta", "accessible", "PASS")

    try:
        meta = json.loads(body)
    except json.JSONDecodeError as e:
        result.add("oauth-as-meta", "valid JSON", "FAIL", str(e))
        return None
    result.add("oauth-as-meta", "valid JSON", "PASS")

    # REQUIRED per RFC 8414
    rfc_required = ["issuer", "response_types_supported"]
    for field in rfc_required:
        if field in meta:
            result.add("oauth-as-meta", f"{field} (REQUIRED per RFC 8414)",
                        "PASS", str(meta[field])[:60])
        else:
            result.add("oauth-as-meta", f"{field} (REQUIRED per RFC 8414)",
                        "FAIL", "Missing")

    # Conditionally required per RFC 8414
    if "token_endpoint" in meta:
        result.add("oauth-as-meta", "token_endpoint (REQUIRED unless implicit-only)",
                    "PASS", meta["token_endpoint"][:80])
    else:
        result.add("oauth-as-meta", "token_endpoint (REQUIRED unless implicit-only)",
                    "WARN", "Missing -- required unless only implicit grant supported")

    if "authorization_endpoint" in meta:
        result.add("oauth-as-meta", "authorization_endpoint", "PASS",
                    meta["authorization_endpoint"][:80])

    # OPTIONAL but useful
    if "grant_types_supported" in meta:
        grants = meta["grant_types_supported"]
        result.add("oauth-as-meta", "grant_types_supported", "PASS",
                    ", ".join(grants))
        if "client_credentials" in grants:
            result.add("oauth-as-meta", "client_credentials grant", "PASS",
                        "M2M auth supported")

    if "scopes_supported" in meta:
        result.add("oauth-as-meta", "scopes_supported", "PASS",
                    ", ".join(meta["scopes_supported"][:5]))

    # Check for agent-specific scopes
    scopes = meta.get("scopes_supported", [])
    agent_scopes = [s for s in scopes if any(
        kw in s.lower() for kw in ["agent", "bot", "machine", "m2m"]
    )]
    if agent_scopes:
        result.add("oauth-as-meta", "agent-specific scopes", "PASS",
                    ", ".join(agent_scopes))

    return meta


# ---- CORS check ----

def check_cors(endpoint_url, target_name, result):
    """Check CORS headers via OPTIONS preflight."""
    status, headers, body = fetch(endpoint_url, method="OPTIONS")
    if status is None:
        result.add(target_name, "CORS preflight", "INFO",
                    f"OPTIONS request failed: {body}")
        return

    acao = headers.get("access-control-allow-origin", "")
    if acao:
        result.add(target_name, "CORS Allow-Origin", "PASS", acao)
    else:
        result.add(target_name, "CORS Allow-Origin", "INFO",
                    "No Access-Control-Allow-Origin header")

    acam = headers.get("access-control-allow-methods", "")
    if acam:
        result.add(target_name, "CORS Allow-Methods", "PASS", acam)


# ---- main ----

def main():
    parser = argparse.ArgumentParser(
        description="Validate agent identity/auth endpoints "
                    "(OIDC, A2A agent card, RFC 8414 OAuth metadata)")
    parser.add_argument("--url", required=True,
                        help="URL to check (e.g. https://example.com)")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output results as JSON")
    args = parser.parse_args()

    url = args.url.rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    result = Result()

    if not args.json_output:
        print(f"Checking identity endpoints: {url}\n")

    # Run all checks
    oidc_config = check_openid_config(url, result)
    check_agent_card(url, result)
    oauth_meta = check_oauth_as_metadata(url, result)

    # If we found a token_endpoint from either discovery doc, check CORS on it
    token_url = None
    if oidc_config and "token_endpoint" in oidc_config:
        token_url = oidc_config["token_endpoint"]
    elif oauth_meta and "token_endpoint" in oauth_meta:
        token_url = oauth_meta["token_endpoint"]
    if token_url:
        result.add("token_endpoint", "discovered", "PASS", token_url[:80])
        check_cors(token_url, "token_endpoint", result)

    if args.json_output:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        result.print_report()

    sys.exit(1 if result.failed > 0 else 0)


if __name__ == "__main__":
    main()
