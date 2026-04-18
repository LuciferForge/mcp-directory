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

# 5. Send Telegram notification
$PYTHON -c "
import requests
requests.post(
    'https://api.telegram.org/bot8688584707:AAEnTSICG1Vgkn_0i1DTt-L0we3GAy-Jp7A/sendMessage',
    json={'chat_id': '257190241', 'text': '🔄 Protodex refreshed: $NEW_COUNT servers, $PAGE_COUNT pages. https://protodex.io', 'parse_mode': 'HTML'},
    timeout=10
)" >> "$LOG" 2>&1 || true

log "=== Protodex refresh complete ==="
