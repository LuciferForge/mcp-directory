#!/bin/bash
# Daily Polymarket Data Sales Promotion & SEO Blog Publishing Automation Cron
# Executed daily to generate fresh dataset blog posts, publish Dev.to articles, rebuild protodex.io, push to GitHub, and report to Telegram.

PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/3.10/bin/python3"
MCP_DIR="/Users/apple/Documents/LuciferForge/mcp-directory"

echo "=== EXECUTING DAILY POLYMARKET PROMO & BLOG GENERATION [$(date -u)] ==="

cd "$MCP_DIR" || exit 1

# 1. Run Polymarket SEO Blog Generator
echo "--> Generating fresh Polymarket dataset blog post..."
$PYTHON_BIN polymarket_blog_generator.py

# 2. Publish Daily Promotional Technical Article to Dev.to
echo "--> Publishing promotional technical article to Dev.to via API..."
$PYTHON_BIN publish_devto_polymarket_article.py

# 3. Rebuild protodex.io Site & RSS Feed
echo "--> Rebuilding protodex.io site index and RSS feed..."
$PYTHON_BIN build_site.py

# 4. Commit and Push Updates to GitHub origin master
echo "--> Committing and pushing docs/ updates to GitHub origin master..."
git add docs/
git commit -m "feat(blog): daily automated Polymarket dataset insights post & Dev.to promo [$(date -u +%Y-%m-%d)]"
git push origin master

# 5. Dispatch Telemetry Report to Telegram @JarvinLu_bot
ENV_FILE="/Users/apple/Documents/Zero_fks/.env"
if [ -f "$ENV_FILE" ]; then
  TELEGRAM_BOT_TOKEN=$(grep -E "^TELEGRAM_BOT_TOKEN=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
  TELEGRAM_CHAT_ID=$(grep -E "^TELEGRAM_CHAT_ID=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
fi

if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
  MSG="🚀 *DAILY POLYMARKET DATA SALES PROMOTION EXECUTED*%0A📅 *Date:* \`$(date -u +%Y-%m-%d)\`%0A%0A✅ Fresh SEO dataset blog post generated%0A✅ Dev.to technical article published live%0A✅ protodex.io site index & RSS feed rebuilt%0A✅ GitHub origin master deployed live%0A%0A🌐 *Website:* https://protodex.io/blog/"

  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    -d "text=${MSG}" \
    -d "parse_mode=Markdown" > /dev/null
fi

echo "=== DAILY POLYMARKET PROMO COMPLETE ==="
