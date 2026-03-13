#!/usr/bin/env python3
"""
score_readiness.py -- Analyze audit JSON from audit_full.py.

Calculates grade (A/B/C/D/F), generates improvement roadmap sorted by
impact (biggest point gaps first), maps each gap to the ar-* skill that
fixes it. Outputs text, markdown, or JSON.

Usage:
  python score_readiness.py --input report.json
  python score_readiness.py --input report.json --format markdown
  python score_readiness.py --input report.json --format json
  cat report.json | python score_readiness.py --input - --format markdown
"""

import argparse
import json
import sys
from datetime import datetime, timezone

GRADE_THRESHOLDS = [(90, "A"), (75, "B"), (60, "C"), (40, "D"), (0, "F")]

DIM_INFO = {
    "discovery":    {"name": "Discovery",    "max": 20, "green": 16, "yellow": 8,
                     "skill": "ar-discover",
                     "fix": "Deploy llms.txt (llmstxt.org), agents.json, A2A agent card, fix robots.txt"},
    "readability":  {"name": "Readability",  "max": 15, "green": 12, "yellow": 6,
                     "skill": "ar-structured-data",
                     "fix": "Add/fix heading hierarchy, semantic HTML, meta tags, lang attribute"},
    "data_quality": {"name": "Data Quality", "max": 20, "green": 16, "yellow": 8,
                     "skill": "ar-structured-data",
                     "fix": "Add JSON-LD structured data, fill required Schema.org properties, add OG tags"},
    "mcp_api":      {"name": "MCP/API",      "max": 20, "green": 16, "yellow": 8,
                     "skill": "ar-identity",
                     "fix": "Add OpenAPI spec, API docs, CORS headers, expose API endpoint"},
    "commerce":     {"name": "Commerce",     "max": 15, "green": 12, "yellow": 6,
                     "skill": "ar-commerce",
                     "fix": "Implement UCP profile (ucp.dev), ACP checkout (agenticcommerce.dev), product schema"},
    "payment":      {"name": "Payment",      "max": 10, "green": 8,  "yellow": 4,
                     "skill": "ar-payments",
                     "fix": "Integrate payment SDK, add wallet pay support"},
}

DIM_ORDER = ["discovery", "readability", "data_quality", "mcp_api", "commerce", "payment"]


def grade_of(score):
    for t, g in GRADE_THRESHOLDS:
        if score >= t:
            return g
    return "F"


def health(score, green, yellow):
    if score >= green: return "GREEN"
    if score >= yellow: return "YELLOW"
    return "RED"


def bar(score, mx, w=20):
    filled = int(score / mx * w) if mx else 0
    return "\u2588" * filled + "\u2591" * (w - filled)


def analyze(audit):
    dims = audit.get("dimensions", {})
    url = audit.get("url", "unknown")

    scored = []
    total = 0; total_max = 0
    for key in DIM_ORDER:
        info = DIM_INFO[key]
        dd = dims.get(key, {})
        sc = dd.get("score", 0)
        mx = dd.get("max", info["max"])
        pct = int(sc / mx * 100) if mx else 0
        gap = mx - sc
        h = health(sc, info["green"], info["yellow"])
        entry = {"key": key, "name": info["name"], "score": sc, "max": mx,
                 "pct": pct, "health": h, "gap": gap, "checks": dd.get("checks", [])}
        if gap > 2:
            entry["rec"] = {"skill": info["skill"], "action": info["fix"], "gain": gap}
        scored.append(entry)
        total += sc; total_max += mx

    # Improvement path sorted by biggest gap first
    improvements = []
    cumulative = total
    for dim in sorted(scored, key=lambda d: -d["gap"]):
        if dim["gap"] <= 2:
            continue
        improvements.append({
            "priority": len(improvements) + 1,
            "dimension": dim["name"],
            "skill": dim["rec"]["skill"],
            "action": dim["rec"]["action"],
            "gain": dim["gap"],
            "before": cumulative,
            "after": cumulative + dim["gap"],
        })
        cumulative += dim["gap"]

    strongest = max(scored, key=lambda d: d["pct"])
    weakest = min(scored, key=lambda d: d["pct"])

    return {
        "url": url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_score": total, "max_score": total_max,
        "grade": grade_of(total),
        "dimensions": scored,
        "improvements": improvements,
        "summary": {
            "strongest": f"{strongest['name']} ({strongest['pct']}%)",
            "weakest": f"{weakest['name']} ({weakest['pct']}%)",
            "projected_score": cumulative,
            "projected_grade": grade_of(cumulative),
        },
    }


def fmt_text(r):
    lines = [f"Agent-Readiness Score: {r['url']}",
             f"{'='*50}", "",
             f"Total: {r['total_score']}/{r['max_score']} (Grade: {r['grade']})", ""]
    for d in r["dimensions"]:
        sym = {"GREEN": "+", "YELLOW": "~", "RED": "-"}[d["health"]]
        lines.append(f"  [{sym}] {d['name']:<14} {d['score']:>2}/{d['max']} ({d['pct']:>3}%) {d['health']}")
    lines.extend(["", "Improvement Path:", ""])
    for imp in r["improvements"]:
        lines.append(f"  {imp['priority']}. {imp['skill']}: {imp['action']}")
        lines.append(f"     +{imp['gain']} pts -> {imp['before']} -> {imp['after']}")
        lines.append("")
    s = r["summary"]
    lines.extend(["Summary:",
                   f"  Strongest: {s['strongest']}",
                   f"  Weakest:   {s['weakest']}",
                   f"  Projected: {s['projected_score']}/{r['max_score']} (Grade: {s['projected_grade']})"])
    return "\n".join(lines)


def fmt_markdown(r):
    lines = [f"# Agent-Readiness Score: {r['url']}", "",
             f"**Total: {r['total_score']}/{r['max_score']} (Grade: {r['grade']})**", "",
             "```"]
    for d in r["dimensions"]:
        lines.append(f"{d['name']:<14}{bar(d['score'], d['max'])} {d['score']:>2}/{d['max']} ({d['pct']:>3}%)")
    lines.extend([f"{'─'*45}",
                   f"{'TOTAL':<14}{' '*20} {r['total_score']:>3}/{r['max_score']}",
                   "```", "",
                   "## Health Status", "",
                   "| Dimension | Score | Health | Action |",
                   "|-----------|-------|--------|--------|"])
    for d in r["dimensions"]:
        rec = d.get("rec")
        action = f"Run **{rec['skill']}**: {rec['action']}" if rec else "Good"
        lines.append(f"| {d['name']} | {d['score']}/{d['max']} | {d['health']} | {action} |")

    if r["improvements"]:
        lines.extend(["", "## Improvement Roadmap", "",
                       "Sorted by impact (biggest gaps first):", ""])
        for imp in r["improvements"]:
            lines.append(f"**{imp['priority']}. {imp['skill']}** (+{imp['gain']} pts)")
            lines.append(f"- {imp['action']}")
            lines.append(f"- Score: {imp['before']} -> {imp['after']}")
            lines.append("")

    # Per-dimension check details
    lines.extend(["## Check Details", ""])
    for d in r["dimensions"]:
        if not d["checks"]:
            continue
        lines.append(f"### {d['name']} ({d['score']}/{d['max']})")
        lines.append("")
        lines.append("| Check | Score | Status | Detail |")
        lines.append("|-------|-------|--------|--------|")
        for c in d["checks"]:
            lines.append(f"| {c['name']} | {c['points']}/{c['max']} | {c['status']} | {c['detail']} |")
        lines.append("")

    s = r["summary"]
    lines.extend(["## Summary", "",
                   "| Metric | Value |", "|--------|-------|",
                   f"| Strongest | {s['strongest']} |",
                   f"| Weakest | {s['weakest']} |",
                   f"| Projected (all fixes) | {s['projected_score']}/{r['max_score']} Grade {s['projected_grade']} |"])
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Analyze agent-readiness audit JSON")
    ap.add_argument("--input", required=True, help="Audit JSON file (or - for stdin)")
    ap.add_argument("--format", default="text", choices=["text", "markdown", "json"])
    ap.add_argument("--output", help="Save to file")
    args = ap.parse_args()

    try:
        if args.input == "-":
            audit = json.load(sys.stdin)
        else:
            with open(args.input) as f:
                audit = json.load(f)
    except FileNotFoundError:
        print(f"Error: {args.input} not found", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON: {e}", file=sys.stderr)
        return 1

    result = analyze(audit)

    if args.format == "json":
        out = json.dumps(result, indent=2)
    elif args.format == "markdown":
        out = fmt_markdown(result)
    else:
        out = fmt_text(result)

    if args.output:
        with open(args.output, "w") as f:
            f.write(out)
        print(f"Saved to: {args.output}", file=sys.stderr)
    else:
        print(out)

    return 0


if __name__ == "__main__":
    sys.exit(main())
