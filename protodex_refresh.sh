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

# 4. Build static site
log "Step 4: Building site..."
$PYTHON build_site.py >> "$LOG" 2>&1
PAGE_COUNT=$(find docs -name "*.html" | wc -l | tr -d ' ')
log "  Generated: $PAGE_COUNT HTML pages"

# 5. Git commit + push (only if there are changes)
log "Step 5: Git push..."
git add -A docs/ mcp_directory.json mcp_directory.db 2>> "$LOG"
CHANGES=$(git diff --cached --stat 2>/dev/null | tail -1)
if [ -n "$CHANGES" ]; then
    git commit -m "Auto-refresh: $NEW_COUNT servers indexed on $(date '+%Y-%m-%d')

Co-Authored-By: Protodex Bot <noreply@protodex.io>" >> "$LOG" 2>&1
    GIT_SSH_COMMAND="ssh -i ~/.ssh/id_luciferforge -p 443 -o StrictHostKeyChecking=no" git push origin master >> "$LOG" 2>&1
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
