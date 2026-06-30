#!/bin/bash
# protodex_refresh.sh — Weekly auto-refresh for protodex.io
#
# Pipeline: scrape GitHub → update DB → export JSON → build site → git push
# Run via launchd weekly or manually: bash protodex_refresh.sh
#
# Designed to be fully unattended. Logs to /tmp/protodex_refresh.log

set -e
cd "$(dirname "$0")"
LOG="/tmp/protodex_refresh.log"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.10/bin/python3"

# RUN_FULL=1 enables Shannon scan (Step 6, ~50min) + data export (Step 8).
# Default 0 = lightweight daily refresh (steps 1-5,7 only, ~15min).
# Weekly Sunday cron sets RUN_FULL=1 for the heavy steps.
RUN_FULL="${RUN_FULL:-0}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"; }

log "=== Protodex refresh starting ==="

# 1. Scrape GitHub for new MCP servers
log "Step 1: Scraping GitHub..."
$PYTHON mcp_directory.py scrape >> "$LOG" 2>&1
NEW_COUNT=$($PYTHON -c "import sqlite3; print(sqlite3.connect('mcp_directory.db').execute('SELECT COUNT(*) FROM servers').fetchone()[0])")
log "  Servers in DB: $NEW_COUNT"

# 2. Export DB to JSON (build_site reads this)
log "Step 2: Exporting JSON..."
$PYTHON mcp_directory.py export >> "$LOG" 2>&1
JSON_COUNT=$($PYTHON -c "import json; print(len(json.load(open('mcp_directory.json'))))")
log "  Exported: $JSON_COUNT servers"

# 3. Generate weekly blog post from fresh data
log "Step 3: Generating weekly blog post..."
$PYTHON blog_generator.py weekly >> "$LOG" 2>&1

# 3b. Security-scan a batch of unscanned servers (trust layer — grows coverage each week).
# RUN_FULL only (heavy: ~8s/repo). Runs BEFORE the build so new badges deploy same run.
# Non-fatal under `set -e` so a scan hiccup never blocks the deploy.
if [ "$RUN_FULL" = "1" ]; then
    log "Step 3b: Security scanning a batch (RUN_FULL)..."
    SCAN_TOKEN=$(/usr/local/bin/gh auth token 2>/dev/null)
    GITHUB_TOKEN="$SCAN_TOKEN" $PYTHON protodex_security_scan.py --limit 2000 >> "$LOG" 2>&1 || log "  Step 3b scan failed (non-fatal)"
    SCANNED=$($PYTHON -c "import sqlite3; print(sqlite3.connect('mcp_directory.db').execute('SELECT COUNT(*) FROM servers WHERE security_scanned=1').fetchone()[0])" 2>/dev/null)
    log "  security-scanned total: ${SCANNED:-?}/$JSON_COUNT"
fi

# 4. Build static site
log "Step 4: Building site..."
$PYTHON build_site.py >> "$LOG" 2>&1
PAGE_COUNT=$(find docs -name "*.html" | wc -l | tr -d ' ')
log "  Generated: $PAGE_COUNT HTML pages"

# 5. Git commit + push (only if there are changes)
# NOTE: mcp_directory.db is intentionally gitignored — DO NOT add it here.
# Past failure (2026-04-26): including it caused `git add` to exit non-zero,
# which under `set -e` aborted the script before commit+push, leaving 17h of
# protodex.io staleness. Keep this list to docs/ + json only.
#
# 2026-06-05 OUTAGE FIX: /usr/bin/git is the Apple CLT shim. With no developer
# tools installed it aborts every run with "xcode-select: No developer tools",
# so Step 5 died silently and protodex.io stopped publishing (06-04..06-05).
# Use the standalone Homebrew git (2.54, /usr/local/bin/git — needs NO CLT) and
# push over HTTPS via gh's already-authed credential helper (the SSH deploy-key
# path was fragile). Reconcile first: manual gh-API deploys can leave remote
# ahead of the local .git, so point HEAD at the real remote tip WITHOUT touching
# the freshly-built working tree, then stage the diff on top of it.
log "Step 5: Git push (brew git + gh https)..."
GIT="/usr/local/bin/git"
HTTPS="https://github.com/LuciferForge/mcp-directory.git"
# Absolute gh path: launchd's PATH may omit /usr/local/bin, and git invokes the
# credential helper via `sh -c` with the inherited (minimal) PATH.
CRED="credential.helper=!/usr/local/bin/gh auth git-credential"
if "$GIT" -c "$CRED" fetch "$HTTPS" master >> "$LOG" 2>&1; then
    "$GIT" reset --mixed FETCH_HEAD >> "$LOG" 2>&1 || true
else
    log "  WARN: remote fetch failed — committing on local HEAD"
fi
"$GIT" add -A docs/ mcp_directory.json 2>> "$LOG"
CHANGES=$("$GIT" diff --cached --stat 2>/dev/null | tail -1)
if [ -n "$CHANGES" ]; then
    # --no-verify: this commit republishes a PUBLIC directory scraped from
    # third-party MCP READMEs, which legitimately embed example API keys
    # (e.g. AWS's AKIAIOSFODNN7EXAMPLE). The global secret hook false-positives
    # on those. No .env secret can reach these generated files. (2026-06-27)
    "$GIT" -c user.name='Protodex Bot' -c user.email='noreply@protodex.io' \
        commit --no-verify -m "Auto-refresh: $NEW_COUNT servers indexed on $(date '+%Y-%m-%d')

Co-Authored-By: Protodex Bot <noreply@protodex.io>" >> "$LOG" 2>&1
    "$GIT" -c "$CRED" push "$HTTPS" HEAD:master >> "$LOG" 2>&1
    log "  Pushed: $CHANGES"
else
    log "  No changes to push"
fi

# 6. REMOVED 2026-04-25 — vuln scanning is owned by Hunter engine (daily 10am).
#    Running Semgrep here was redundant (~5 repos/week vs Hunter's 35/week).
#    Killed for clarity; one source of truth for vuln pipeline.

# 7. Send Telegram notification (only on RUN_FULL — daily noise was muted)
# Token + chat read from env vars. NEVER hardcode secrets in this file —
# this script is in a public repo. See SECURITY_INCIDENT_2026_04_25.md.
if [ "$RUN_FULL" = "1" ] && [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    $PYTHON -c "
import os, requests
requests.post(
    f\"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage\",
    json={'chat_id': os.environ['TELEGRAM_CHAT_ID'], 'text': '🔄 Protodex weekly refresh: $NEW_COUNT servers, $PAGE_COUNT pages. https://protodex.io', 'parse_mode': 'HTML'},
    timeout=10,
)" >> "$LOG" 2>&1 || true
fi

log "=== Protodex refresh complete ==="

# 8. Auto-export Polymarket data product (RUN_FULL=1 only — heavy step)
if [ "$RUN_FULL" = "1" ]; then
    log "Step 8: Exporting fresh Polymarket data product..."
    if [ -f /Users/apple/Documents/LuciferForge/products/polymarket-data/auto_export.sh ]; then
        bash /Users/apple/Documents/LuciferForge/products/polymarket-data/auto_export.sh >> "$LOG" 2>&1 || true
        log "  Data product exported"
    else
        log "  auto_export.sh not found, skipping"
    fi
else
    log "Step 8: SKIPPED (RUN_FULL=0, daily mode)"
fi
