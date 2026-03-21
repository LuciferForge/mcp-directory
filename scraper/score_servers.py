#!/usr/bin/env python3
"""
Protodex Phase 1 — Security Score Calculator
Reads all_servers.json, computes a 0-100 security score per server,
assigns Green/Yellow/Red bands, updates the JSON in-place.

Scoring criteria:
  +10  Has README
  +10  Has LICENSE
  +10  Stars > 100 (+5 base, +5 bonus for >1000)
  +10  Pushed in last 30 days (+5 for last 90 days)
  -30  Has known CVE
  +10  Has mcp.json / MCP config
  +5   Language is Python/TypeScript/Rust
  -50  Archived repo

Band assignment:
  Green:  80+
  Yellow: 50-79
  Red:    <50

Usage:
  python3 score_servers.py
"""

import json
import subprocess
import time
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

GH = "/usr/local/bin/gh"
SERVERS_FILE = Path(__file__).parent / "all_servers.json"

# Known CVEs from bounty-hunting database
KNOWN_CVES = {
    "ollama/ollama": ["CVE-2025-63389", "CVE-2025-51471", "CVE-2025-1975", "CVE-2024-7773"],
    "pytorch/serve": ["CVE-2023-43654", "CVE-2025-32434"],
    "run-llama/llama_index": ["CVE-2023-39662", "CVE-2025-1793", "CVE-2025-7647", "CVE-2025-5302"],
    "huggingface/text-generation-inference": ["CVE-2024-3568"],
    "mlflow/mlflow": ["CVE-2023-6831", "CVE-2024-0520", "CVE-2024-1558", "CVE-2024-1560", "CVE-2024-2928", "CVE-2024-3573"],
    "keras-team/keras": ["CVE-2025-1550"],
}

# Mature ecosystem languages
MATURE_LANGS = {"Python", "TypeScript", "Rust", "Go", "Java", "C#"}


def check_repo_has_file(owner_repo, filename):
    """Check if a repo has a specific file via GitHub API."""
    cmd = [GH, "api", f"repos/{owner_repo}/contents/{filename}", "-X", "GET"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return result.returncode == 0
    except Exception:
        return False


def score_server(server, now, batch_checks=None):
    """Compute security score for a single server entry. Returns (score, details)."""
    score = 0
    details = []

    repo_url = server.get("repo_url", "")
    owner_repo = ""
    if "github.com/" in repo_url:
        parts = repo_url.replace("https://github.com/", "").strip("/").split("/")
        if len(parts) >= 2:
            owner_repo = f"{parts[0]}/{parts[1]}"

    # --- Has README (+10) ---
    has_readme = batch_checks.get(owner_repo, {}).get("readme", False) if batch_checks else False
    if has_readme:
        score += 10
        details.append("+10 README")

    # --- Has LICENSE (+10) ---
    license_val = server.get("license", "")
    if license_val and license_val not in ("", "NOASSERTION"):
        score += 10
        details.append(f"+10 LICENSE ({license_val})")
    elif batch_checks and batch_checks.get(owner_repo, {}).get("license", False):
        score += 10
        details.append("+10 LICENSE (file)")

    # --- Stars (+5 for >100, +10 for >1000) ---
    stars = server.get("stars", 0)
    if stars > 1000:
        score += 10
        details.append(f"+10 stars ({stars})")
    elif stars > 100:
        score += 5
        details.append(f"+5 stars ({stars})")

    # --- Pushed recently (+10 for 30d, +5 for 90d) ---
    last_pushed = server.get("last_pushed", "")
    if last_pushed:
        try:
            pushed_date = datetime.fromisoformat(last_pushed.replace("Z", "+00:00"))
            if not pushed_date.tzinfo:
                pushed_date = pushed_date.replace(tzinfo=timezone.utc)
            days_ago = (now - pushed_date).days
            if days_ago <= 30:
                score += 10
                details.append(f"+10 pushed {days_ago}d ago")
            elif days_ago <= 90:
                score += 5
                details.append(f"+5 pushed {days_ago}d ago")
        except (ValueError, TypeError):
            pass

    # --- Known CVEs (-30) ---
    if owner_repo in KNOWN_CVES and KNOWN_CVES[owner_repo]:
        score -= 30
        cve_count = len(KNOWN_CVES[owner_repo])
        details.append(f"-30 known CVEs ({cve_count})")

    # --- Has MCP config (+10) ---
    if server.get("has_mcp_json"):
        score += 10
        details.append("+10 mcp.json")

    # --- Mature language (+5) ---
    lang = server.get("language", "")
    if lang in MATURE_LANGS:
        score += 5
        details.append(f"+5 lang ({lang})")

    # --- Archived (-50) ---
    if server.get("archived"):
        score -= 50
        details.append("-50 ARCHIVED")

    # --- Description present (+5) ---
    if server.get("description", "").strip():
        score += 5
        details.append("+5 description")

    # --- Topics present (+5) ---
    topics = server.get("topics", [])
    if topics and len(topics) > 0:
        score += 5
        details.append(f"+5 topics ({len(topics)})")

    # --- Multiple sources (+5) ---
    sources = server.get("source", [])
    if len(sources) > 1:
        score += 5
        details.append(f"+5 multi-source ({len(sources)})")

    # Clamp to 0-100
    score = max(0, min(100, score))

    # Band
    if score >= 80:
        band = "Green"
    elif score >= 50:
        band = "Yellow"
    else:
        band = "Red"

    return score, band, details


def batch_check_readmes(servers, sample_size=200):
    """Check README/LICENSE existence for a batch of servers via API."""
    print(f"Checking README/LICENSE for up to {sample_size} servers...")
    checks = {}

    # Prioritize servers with most stars (most visible)
    sorted_servers = sorted(servers, key=lambda s: s.get("stars", 0), reverse=True)

    for i, server in enumerate(sorted_servers[:sample_size]):
        repo_url = server.get("repo_url", "")
        if "github.com/" not in repo_url:
            continue
        parts = repo_url.replace("https://github.com/", "").strip("/").split("/")
        if len(parts) < 2:
            continue
        owner_repo = f"{parts[0]}/{parts[1]}"

        if owner_repo in checks:
            continue

        # Check README
        has_readme = check_repo_has_file(owner_repo, "README.md")
        if not has_readme:
            has_readme = check_repo_has_file(owner_repo, "readme.md")

        checks[owner_repo] = {
            "readme": has_readme,
            "license": bool(server.get("license")),
        }

        if (i + 1) % 50 == 0:
            print(f"  Checked {i+1}/{sample_size}...")

        time.sleep(0.3)

    return checks


def main():
    if not SERVERS_FILE.exists():
        print(f"Error: {SERVERS_FILE} not found. Run scrape_mcp_servers.py first.")
        sys.exit(1)

    with open(SERVERS_FILE) as f:
        data = json.load(f)

    servers = data.get("servers", [])
    print(f"Loaded {len(servers)} servers from {SERVERS_FILE}")

    now = datetime.now(timezone.utc)

    # Batch check READMEs for top servers
    batch_checks = batch_check_readmes(servers, sample_size=min(200, len(servers)))

    # For servers we didn't check, assume README exists if they have stars > 10
    # (nearly all repos with any traction have a README)
    for server in servers:
        repo_url = server.get("repo_url", "")
        if "github.com/" in repo_url:
            parts = repo_url.replace("https://github.com/", "").strip("/").split("/")
            if len(parts) >= 2:
                owner_repo = f"{parts[0]}/{parts[1]}"
                if owner_repo not in batch_checks:
                    # Heuristic: repos with stars almost always have README
                    batch_checks[owner_repo] = {
                        "readme": server.get("stars", 0) > 10,
                        "license": bool(server.get("license")),
                    }

    # Score all servers
    print(f"\nScoring {len(servers)} servers...")
    green = yellow = red = 0
    score_sum = 0

    for server in servers:
        repo_url = server.get("repo_url", "")
        owner_repo = ""
        if "github.com/" in repo_url:
            parts = repo_url.replace("https://github.com/", "").strip("/").split("/")
            if len(parts) >= 2:
                owner_repo = f"{parts[0]}/{parts[1]}"

        sc, band, details = score_server(server, now, batch_checks)
        server["security_score"] = sc
        server["security_band"] = band
        server["last_scanned"] = now.isoformat()
        score_sum += sc

        if band == "Green":
            green += 1
        elif band == "Yellow":
            yellow += 1
        else:
            red += 1

    # Save updated JSON
    data["servers"] = servers
    data["scoring"] = {
        "scored_at": now.isoformat(),
        "green": green,
        "yellow": yellow,
        "red": red,
        "avg_score": round(score_sum / len(servers), 1) if servers else 0,
    }

    with open(SERVERS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

    # Report
    print(f"\n{'='*60}")
    print(f"SECURITY SCORING COMPLETE")
    print(f"{'='*60}")
    print(f"Total scored: {len(servers)}")
    print(f"  Green  (80+):  {green:>5}  ({100*green//len(servers)}%)")
    print(f"  Yellow (50-79): {yellow:>5}  ({100*yellow//len(servers)}%)")
    print(f"  Red    (<50):  {red:>5}  ({100*red//len(servers)}%)")
    print(f"  Average score: {score_sum / len(servers):.1f}")

    # Top 10 highest scores
    top = sorted(servers, key=lambda s: s.get("security_score", 0), reverse=True)[:10]
    print(f"\nTop 10 by Security Score:")
    for i, s in enumerate(top, 1):
        print(f"  {i:>2}. [{s['security_band']}] {s['security_score']:>3}  {s['name']:<35} ({s['stars']} stars)")

    # Bottom 10
    bottom = sorted(servers, key=lambda s: s.get("security_score", 0))[:10]
    print(f"\nBottom 10 by Security Score:")
    for i, s in enumerate(bottom, 1):
        print(f"  {i:>2}. [{s['security_band']}] {s['security_score']:>3}  {s['name']:<35} ({s['stars']} stars)")

    # Known CVE hits
    cve_hits = [s for s in servers if any(
        f"{s['owner']}/{s['name']}" == k for k in KNOWN_CVES if KNOWN_CVES[k]
    )]
    if cve_hits:
        print(f"\nServers with known CVEs ({len(cve_hits)}):")
        for s in cve_hits:
            print(f"  [{s['security_band']}] {s['security_score']:>3}  {s['name']} — {s['repo_url']}")

    print(f"\nUpdated: {SERVERS_FILE}")


if __name__ == "__main__":
    main()
