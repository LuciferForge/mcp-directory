#!/usr/bin/env python3
"""
protodex_security_scan.py — Scan MCP servers for vulnerabilities using Semgrep.

Replaces the Shannon pipeline (which needed a running instance).
Semgrep does static analysis — just needs source code. Fast, reliable.

Usage:
  python3 protodex_security_scan.py --limit 5           # Scan 5 newest unscanned
  python3 protodex_security_scan.py --force owner/repo   # Scan specific repo
  python3 protodex_security_scan.py --dry-run --limit 3  # Preview without scanning
"""

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

DB_PATH = Path(__file__).parent / "mcp_directory.db"
REPORTS_DIR = Path.home() / "Documents/LuciferForge/bounty-hunting/semgrep-reports"
BOUNTY_DB = Path.home() / "Documents/LuciferForge/bounty-hunting/bounty_analytics.db"
CLONE_DIR = Path("/tmp/semgrep-targets")
SEMGREP = "/Library/Frameworks/Python.framework/Versions/3.10/bin/semgrep"
SCAN_TIMEOUT = 120  # 2 min per repo (semgrep is fast)

def _load_env_file(path):
    """Load KEY=VALUE pairs from a .env file into os.environ (no overwrite)."""
    try:
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass

_load_env_file(Path.home() / "Documents/Zero_fks/.env")

# Secrets come from Zero_fks/.env — never hardcode tokens here.
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    # Add security_scanned column if missing
    try:
        conn.execute("ALTER TABLE servers ADD COLUMN security_scanned INTEGER DEFAULT 0")
        conn.commit()
    except:
        pass
    return conn


def get_unscanned(conn, limit=5):
    return conn.execute(
        """SELECT repo, url, language FROM servers
           WHERE security_scanned = 0
           AND language IN ('Python','TypeScript','JavaScript','Go','Rust')
           AND stars > 5
           ORDER BY stars DESC LIMIT ?""",
        (limit,)
    ).fetchall()


def clone_repo(repo):
    """Download repo as tarball via GitHub API (no git/Xcode needed)."""
    import tarfile, io
    target = CLONE_DIR / repo.replace("/", "--")
    if target.exists():
        subprocess.run(["rm", "-rf", str(target)], check=False)
    target.mkdir(parents=True, exist_ok=True)
    try:
        url = f"https://api.github.com/repos/{repo}/tarball"
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "LuciferForge-Hunter"}
        gh_token = os.environ.get("GITHUB_TOKEN", "")
        if gh_token:
            headers["Authorization"] = f"Bearer {gh_token}"
        r = requests.get(url, headers=headers, timeout=60, stream=True)
        if r.status_code == 401:
            # Token expired/invalid — retry without auth
            headers.pop("Authorization", None)
            r = requests.get(url, headers=headers, timeout=60, stream=True)
        if r.status_code != 200:
            # Tarball failed — try git clone as fallback
            clone_url = f"https://github.com/{repo}.git"
            res = subprocess.run(
                ["git", "clone", "--depth=1", "--quiet", clone_url, str(target)],
                capture_output=True, timeout=120
            )
            if res.returncode != 0:
                print(f"  [skip] Tarball download failed: HTTP {r.status_code}")
                subprocess.run(["rm", "-rf", str(target)], check=False)
                return None
            return target
        buf = io.BytesIO(r.content)
        with tarfile.open(fileobj=buf, mode="r:gz") as tf:
            tf.extractall(path=str(target))
        # GitHub tarballs extract to a subdirectory like owner-repo-sha/
        subdirs = [d for d in target.iterdir() if d.is_dir()]
        if subdirs:
            return subdirs[0]
        return target
    except Exception as e:
        print(f"  [skip] Download error: {e}")
        subprocess.run(["rm", "-rf", str(target)], check=False)
        return None


def scan_repo(repo, clone_dir):
    """Run Semgrep on cloned repo. Returns findings list."""
    report_file = REPORTS_DIR / f"{repo.replace('/', '--')}_{datetime.now().strftime('%Y%m%d')}.json"

    try:
        result = subprocess.run(
            [SEMGREP, "--config=auto", "--severity=WARNING", "--severity=ERROR",
             "--json", "--output", str(report_file), str(clone_dir)],
            capture_output=True, text=True, timeout=SCAN_TIMEOUT,
        )

        if report_file.exists():
            data = json.loads(report_file.read_text())
            findings = data.get("results", [])

            high = [f for f in findings if f.get("extra", {}).get("severity") in ("ERROR",)]
            medium = [f for f in findings if f.get("extra", {}).get("severity") in ("WARNING",)]

            return {
                "total": len(findings),
                "high": len(high),
                "medium": len(medium),
                "findings": findings,
                "report": str(report_file),
            }
        return {"total": 0, "high": 0, "medium": 0, "findings": [], "report": None}

    except subprocess.TimeoutExpired:
        return {"total": 0, "high": 0, "medium": 0, "findings": [], "report": None, "error": "timeout"}
    except Exception as e:
        return {"total": 0, "high": 0, "medium": 0, "findings": [], "report": None, "error": str(e)}


def log_to_bounty_db(repo, findings):
    """Log high-severity findings to bounty_analytics.db."""
    if not BOUNTY_DB.exists():
        return
    conn = sqlite3.connect(str(BOUNTY_DB))
    for f in findings:
        severity = f.get("extra", {}).get("severity", "")
        if severity not in ("ERROR", "WARNING"):
            continue
        check = f.get("check_id", "unknown")
        message = f.get("extra", {}).get("message", "")[:200]
        report_id = f"semgrep-{repo.replace('/', '-')}-{check}"
        try:
            conn.execute(
                """INSERT OR IGNORE INTO reports
                   (report_id, platform, target, vuln_type, title, status, notes, date_submitted)
                   VALUES (?, 'semgrep', ?, ?, ?, 'discovered', ?, ?)""",
                (report_id, repo, check, f"{check}: {message[:80]}", message,
                 datetime.now(timezone.utc).isoformat())
            )
        except:
            pass
    conn.commit()
    conn.close()


def send_alert(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=10,
        )
    except:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--force", type=str, help="Scan specific repo")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    CLONE_DIR.mkdir(parents=True, exist_ok=True)

    conn = get_db()

    if args.force:
        servers = [{"repo": args.force, "url": f"https://github.com/{args.force}", "language": "?"}]
    else:
        servers = get_unscanned(conn, args.limit)

    print(f"[protodex-security-scan] {len(servers)} servers to scan")

    if args.dry_run:
        for s in servers:
            repo = s["repo"] if isinstance(s, dict) else s[0]
            print(f"  [dry-run] Would scan: {repo}")
        return

    total_findings = 0
    high_findings = 0

    for i, s in enumerate(servers, 1):
        repo = s["repo"] if isinstance(s, dict) else s[0]
        print(f"\n[{i}/{len(servers)}] {repo}")

        # Clone
        clone_dir = clone_repo(repo)
        if not clone_dir:
            print(f"  [skip] Clone failed")
            conn.execute("UPDATE servers SET security_scanned = 1 WHERE repo = ?", (repo,))
            conn.commit()
            continue

        # Scan
        result = scan_repo(repo, clone_dir)
        print(f"  Findings: {result['total']} (high={result['high']}, medium={result['medium']})")

        if result["high"] > 0:
            print(f"  HIGH SEVERITY FINDINGS:")
            for f in result["findings"][:5]:
                if f.get("extra", {}).get("severity") == "ERROR":
                    check = f.get("check_id", "?")
                    path = f.get("path", "?")
                    line = f.get("start", {}).get("line", "?")
                    print(f"    [{check}] {path}:{line}")

            # Log and alert
            log_to_bounty_db(repo, result["findings"])
            send_alert(
                f"<b>Security Scan: {repo}</b>\n"
                f"Findings: {result['total']} (high={result['high']})\n"
                f"Report: {result.get('report', 'N/A')}"
            )

        total_findings += result["total"]
        high_findings += result["high"]

        # Mark as scanned + record band (red=high severity, yellow=medium, green=clean)
        band = "red" if result["high"] > 0 else ("yellow" if result["medium"] > 0 else "green")
        conn.execute("UPDATE servers SET security_scanned = 1, security_band = ? WHERE repo = ?", (band, repo))
        conn.commit()

        # Cleanup
        shutil.rmtree(clone_dir, ignore_errors=True)

    print(f"\n[DONE] Scanned {len(servers)} servers | {total_findings} findings | {high_findings} high")
    conn.close()


if __name__ == "__main__":
    main()
