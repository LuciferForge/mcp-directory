#!/usr/bin/env python3
"""
Protodex Phase 1 — MCP Server Scraper
Finds ALL MCP servers on GitHub from multiple sources, deduplicates, categorizes.
Outputs all_servers.json for Protodex ingestion + security scoring.

Sources:
  1. GitHub topic search (mcp-server, mcp, model-context-protocol, modelcontextprotocol)
  2. GitHub code search (mcp.json, @modelcontextprotocol/sdk)
  3. awesome-mcp-servers README parse
  4. mcp-servers-hub README parse

Usage:
  python3 scrape_mcp_servers.py
"""

import json
import subprocess
import time
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

GH = "/usr/local/bin/gh"
OUT_DIR = Path(__file__).parent
OUT_FILE = OUT_DIR / "all_servers.json"
EXISTING_JSON = Path("/Users/apple/Documents/LuciferForge/mcp-directory/mcp_directory.json")

# Rate limit: 2s between search pages
SEARCH_DELAY = 2.5

# ---------- Category Detection ----------

CATEGORY_RULES = [
    ("Database", [
        "postgres", "postgresql", "mysql", "sqlite", "mongodb", "mongo", "redis",
        "database", "supabase", "prisma", "drizzle", "sql", "dynamodb", "fauna",
        "neo4j", "airtable", "notion-database", "firestore", "couchdb",
        "mariadb", "clickhouse", "cassandra", "timescale", "planetscale", "duckdb",
        "turso", "neon",
    ]),
    ("File System", [
        "filesystem", "file-system", "file system", "directory",
        "local files", "file manager", "fs ", "gdrive",
        "google drive", "dropbox", "s3", "storage", "blob", "onedrive",
    ]),
    ("AI/LLM", [
        "embedding", "llm", "openai", "anthropic", "claude", "gpt", "gemini",
        "ollama", "hugging", "vector", "rag", "langchain", "llamaindex",
        "ai model", "artificial intelligence", "machine learning", "transformer",
        "stable diffusion", "midjourney", "replicate", "groq", "mistral",
        "perplexity", "cohere", "vertex",
    ]),
    ("Search", [
        "search", "brave", "serpapi", "google search", "bing", "duckduckgo",
        "knowledge base", "web search", "tavily", "exa ", "you.com",
    ]),
    ("DevOps", [
        "docker", "kubernetes", "k8s", "terraform", "ansible", "ci/cd", "cicd",
        "jenkins", "github actions", "monitoring", "prometheus", "grafana",
        "cloudflare", "aws", "azure", "gcp", "vercel", "netlify", "railway",
        "fly.io", "render", "heroku", "sentry", "datadog", "pagerduty",
    ]),
    ("Security", [
        "security", "auth", "authentication", "vault", "secret", "encrypt",
        "firewall", "vulnerability", "pentest", "audit", "compliance",
        "oauth", "saml", "jwt", "certificate",
    ]),
    ("Communication", [
        "email", "smtp", "imap", "chat", "notification", "sms", "twilio",
        "sendgrid", "mailgun", "discord", "telegram", "whatsapp", "teams",
        "matrix", "signal", "pushover", "ntfy", "slack",
    ]),
    ("API Integration", [
        "github", "jira", "confluence", "trello", "asana", "linear",
        "stripe", "shopify", "salesforce", "hubspot", "zendesk", "intercom",
        "twitch", "spotify", "twitter", "x.com", "reddit", "youtube",
        "google maps", "weather", "calendar", "google calendar", "outlook",
        "todoist", "clickup", "monday", "figma", "canva", "zapier",
        "webhook", "rest api", "api", "integration",
    ]),
    ("Browser/Web", [
        "browser", "puppeteer", "playwright", "selenium", "scrape", "scraping",
        "chromium", "headless", "crawl", "crawler",
    ]),
    ("Code/Dev Tools", [
        "git ", "linter", "formatter", "debug", "test", "lint",
        "prettier", "eslint", "compiler", "ide", "editor", "vscode",
        "intellij", "jupyter", "notebook", "repl", "sandbox", "exec",
        "terminal", "shell", "command", "cli", "code",
    ]),
    ("Data/Analytics", [
        "analytics", "data", "csv", "excel", "spreadsheet", "chart",
        "visualization", "dashboard", "report", "metrics", "bigquery",
        "snowflake", "dbt", "tableau", "powerbi", "pandas",
    ]),
    ("Memory/Knowledge", [
        "memory", "knowledge", "context", "notes", "obsidian", "roam",
        "markdown", "wiki", "documentation", "docs",
    ]),
    ("Finance", [
        "finance", "trading", "crypto", "bitcoin", "ethereum", "defi",
        "stock", "market", "payment", "invoice", "accounting", "banking",
    ]),
    ("Media", [
        "image", "video", "audio", "music", "photo", "camera",
        "media", "ffmpeg", "youtube", "podcast", "transcri",
    ]),
]


def categorize(name, description, topics_str):
    """Auto-categorize a server based on its metadata."""
    text = f"{name} {description} {topics_str}".lower()
    scores = {}
    for category, keywords in CATEGORY_RULES:
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[category] = score
    if scores:
        return max(scores, key=scores.get)
    return "Other"


# ---------- GitHub API ----------

def gh_api_raw(endpoint, params=None, max_retries=3):
    """Call GitHub API via gh CLI. Returns parsed JSON or None."""
    cmd = [GH, "api", endpoint, "-X", "GET"]
    if params:
        for k, v in params.items():
            cmd.extend(["-f", f"{k}={v}"])

    for attempt in range(max_retries):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                err = result.stderr.lower()
                if "rate limit" in err or "403" in err or "secondary rate" in err:
                    wait = 60 * (attempt + 1)
                    print(f"    Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                if "422" in result.stderr:
                    return None
                if "404" in result.stderr:
                    return None
                print(f"    API error: {result.stderr[:150]}")
                return None
            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            print(f"    Timeout attempt {attempt+1}")
            time.sleep(5)
        except json.JSONDecodeError:
            return None
    return None


def search_repos_paginated(query, sort="stars", max_pages=10, label=""):
    """Search GitHub repos, paginate through results. Returns list of repo items."""
    all_items = []
    for page in range(1, max_pages + 1):
        print(f"  [{label}] page {page}...", end=" ", flush=True)
        data = gh_api_raw("search/repositories", {
            "q": query,
            "per_page": "100",
            "sort": sort,
            "page": str(page),
        })
        if not data or "items" not in data:
            print("(no data)")
            break

        items = data["items"]
        total_count = data.get("total_count", 0)
        print(f"got {len(items)} (total: {total_count})")

        if not items:
            break
        all_items.extend(items)

        # GitHub caps at 1000 results per search
        if page * 100 >= min(total_count, 1000):
            break

        time.sleep(SEARCH_DELAY)

    return all_items


def repo_to_entry(r):
    """Convert a GitHub API repo object to our standard entry dict."""
    topics = r.get("topics") or []
    name = r.get("name", "")
    desc = r.get("description") or ""
    topics_str = ",".join(topics)

    return {
        "name": name,
        "repo_url": r.get("html_url", ""),
        "description": desc,
        "stars": r.get("stargazers_count", 0),
        "language": r.get("language") or "",
        "topics": topics,
        "last_pushed": (r.get("pushed_at") or "")[:10],
        "owner": r.get("owner", {}).get("login", ""),
        "license": (r.get("license") or {}).get("spdx_id", "") if isinstance(r.get("license"), dict) else "",
        "has_mcp_json": False,  # checked later
        "archived": r.get("archived", False),
        "category": categorize(name, desc, topics_str),
        "security_score": None,
        "security_band": None,
        "last_scanned": None,
        "source": [],
    }


# ---------- Source 1: GitHub Topic Search ----------

def scrape_topic_search():
    """Search by topics: mcp-server, mcp, model-context-protocol, modelcontextprotocol."""
    print("\n=== SOURCE 1: GitHub Topic Search ===")
    all_repos = {}

    topic_queries = [
        ("topic:mcp-server", "topic:mcp-server"),
        ("topic:model-context-protocol", "topic:model-context-protocol"),
        ("topic:modelcontextprotocol", "topic:modelcontextprotocol"),
        # mcp topic is too broad — filter to server-like repos
        ("topic:mcp server in:name,description", "topic:mcp+server"),
    ]

    for query, label in topic_queries:
        items = search_repos_paginated(query, sort="stars", max_pages=10, label=label)
        for r in items:
            url = r.get("html_url", "")
            if url and url not in all_repos:
                entry = repo_to_entry(r)
                entry["source"] = ["topic_search"]
                all_repos[url] = entry
            elif url in all_repos:
                if "topic_search" not in all_repos[url]["source"]:
                    all_repos[url]["source"].append("topic_search")
        time.sleep(SEARCH_DELAY)

    # Additional name-based searches
    name_queries = [
        ("mcp-server in:name", "name:mcp-server"),
        ("mcp server in:name,description", "name+desc:mcp-server"),
        ("\"model context protocol\" in:description", "desc:model-context-protocol"),
        ("org:modelcontextprotocol", "org:mcp"),
        ("fastmcp in:name,description", "fastmcp"),
    ]

    for query, label in name_queries:
        items = search_repos_paginated(query, sort="stars", max_pages=5, label=label)
        for r in items:
            url = r.get("html_url", "")
            if url and url not in all_repos:
                entry = repo_to_entry(r)
                entry["source"] = ["topic_search"]
                all_repos[url] = entry
            elif url in all_repos:
                if "topic_search" not in all_repos[url]["source"]:
                    all_repos[url]["source"].append("topic_search")
        time.sleep(SEARCH_DELAY)

    print(f"  Topic search total: {len(all_repos)} unique repos")
    return all_repos


# ---------- Source 2: GitHub Code Search ----------

def scrape_code_search():
    """Search for repos containing MCP config files or SDK references."""
    print("\n=== SOURCE 2: GitHub Code Search ===")
    all_repos = {}

    # Code search uses a different endpoint
    code_queries = [
        ("filename:mcp.json", "file:mcp.json"),
        ("@modelcontextprotocol/sdk in:file", "sdk-ref"),
        ("from mcp.server import Server", "py-mcp-server"),
        ("McpServer in:file extension:ts", "ts-McpServer"),
    ]

    for query, label in code_queries:
        print(f"  [{label}] searching...", end=" ", flush=True)
        data = gh_api_raw("search/code", {
            "q": query,
            "per_page": "100",
        })
        if not data or "items" not in data:
            print("(no data)")
            time.sleep(SEARCH_DELAY)
            continue

        items = data["items"]
        total = data.get("total_count", 0)
        print(f"got {len(items)} (total: {total})")

        # Code search returns file hits — extract repo URLs
        for item in items:
            repo_data = item.get("repository", {})
            url = repo_data.get("html_url", "")
            if not url:
                continue
            if url not in all_repos:
                # Code search repo data is partial — store what we have
                name = repo_data.get("name", "")
                desc = repo_data.get("description") or ""
                all_repos[url] = {
                    "name": name,
                    "repo_url": url,
                    "description": desc,
                    "stars": 0,  # will be enriched later
                    "language": "",
                    "topics": [],
                    "last_pushed": "",
                    "owner": repo_data.get("owner", {}).get("login", ""),
                    "license": "",
                    "has_mcp_json": "mcp.json" in query,
                    "archived": False,
                    "category": categorize(name, desc, ""),
                    "security_score": None,
                    "security_band": None,
                    "last_scanned": None,
                    "source": ["code_search"],
                }
            else:
                if "code_search" not in all_repos[url]["source"]:
                    all_repos[url]["source"].append("code_search")
                if "mcp.json" in query:
                    all_repos[url]["has_mcp_json"] = True

        time.sleep(SEARCH_DELAY)

    print(f"  Code search total: {len(all_repos)} unique repos")
    return all_repos


# ---------- Source 3: awesome-mcp-servers ----------

def scrape_awesome_list():
    """Parse awesome-mcp-servers README for all listed repos."""
    print("\n=== SOURCE 3: awesome-mcp-servers README ===")
    all_repos = {}

    # Fetch README content
    data = gh_api_raw("repos/punkpeye/awesome-mcp-servers/readme")
    if not data:
        print("  Failed to fetch awesome-mcp-servers README")
        return all_repos

    import base64
    content = data.get("content", "")
    try:
        readme = base64.b64decode(content).decode("utf-8", errors="replace")
    except Exception:
        print("  Failed to decode README")
        return all_repos

    # Extract GitHub URLs from README
    gh_urls = re.findall(r'https://github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)', readme)
    unique_repos = list(dict.fromkeys(gh_urls))  # dedupe preserving order

    print(f"  Found {len(unique_repos)} GitHub repo references in README")

    for full_name in unique_repos:
        url = f"https://github.com/{full_name}"
        # Skip non-server repos (the awesome list itself, tools, etc.)
        name = full_name.split("/")[-1].lower()

        all_repos[url] = {
            "name": full_name.split("/")[-1],
            "repo_url": url,
            "description": "",
            "stars": 0,
            "language": "",
            "topics": [],
            "last_pushed": "",
            "owner": full_name.split("/")[0],
            "license": "",
            "has_mcp_json": False,
            "archived": False,
            "category": "Other",
            "security_score": None,
            "security_band": None,
            "last_scanned": None,
            "source": ["awesome_list"],
        }

    print(f"  Awesome list total: {len(all_repos)} unique repos")
    return all_repos


# ---------- Source 4: mcp-servers-hub ----------

def scrape_hub():
    """Parse mcp-servers-hub README for all listed repos."""
    print("\n=== SOURCE 4: mcp-servers-hub README ===")
    all_repos = {}

    data = gh_api_raw("repos/apappascs/mcp-servers-hub/readme")
    if not data:
        print("  Failed to fetch mcp-servers-hub README")
        return all_repos

    import base64
    content = data.get("content", "")
    try:
        readme = base64.b64decode(content).decode("utf-8", errors="replace")
    except Exception:
        print("  Failed to decode README")
        return all_repos

    gh_urls = re.findall(r'https://github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)', readme)
    unique_repos = list(dict.fromkeys(gh_urls))

    print(f"  Found {len(unique_repos)} GitHub repo references in README")

    for full_name in unique_repos:
        url = f"https://github.com/{full_name}"
        all_repos[url] = {
            "name": full_name.split("/")[-1],
            "repo_url": url,
            "description": "",
            "stars": 0,
            "language": "",
            "topics": [],
            "last_pushed": "",
            "owner": full_name.split("/")[0],
            "license": "",
            "has_mcp_json": False,
            "archived": False,
            "category": "Other",
            "security_score": None,
            "security_band": None,
            "last_scanned": None,
            "source": ["hub"],
        }

    print(f"  Hub total: {len(all_repos)} unique repos")
    return all_repos


# ---------- Enrichment ----------

def enrich_partial_entries(servers, batch_size=50):
    """Enrich entries that came from code search / awesome lists with full repo data."""
    to_enrich = [url for url, s in servers.items()
                 if s["stars"] == 0 and s["description"] == ""]

    print(f"\n=== Enriching {len(to_enrich)} partial entries (batch: {batch_size}) ===")

    enriched = 0
    for i, url in enumerate(to_enrich[:batch_size]):
        # Extract owner/repo from URL
        match = re.match(r'https://github\.com/([^/]+/[^/]+)', url)
        if not match:
            continue
        full_name = match.group(1)

        data = gh_api_raw(f"repos/{full_name}")
        if not data:
            time.sleep(0.5)
            continue

        s = servers[url]
        s["description"] = data.get("description") or ""
        s["stars"] = data.get("stargazers_count", 0)
        s["language"] = data.get("language") or ""
        s["topics"] = data.get("topics") or []
        s["last_pushed"] = (data.get("pushed_at") or "")[:10]
        s["license"] = (data.get("license") or {}).get("spdx_id", "") if isinstance(data.get("license"), dict) else ""
        s["archived"] = data.get("archived", False)
        s["has_mcp_json"] = s.get("has_mcp_json", False)  # preserve if already set
        s["category"] = categorize(s["name"], s["description"], ",".join(s["topics"]))
        enriched += 1

        if (i + 1) % 20 == 0:
            print(f"  Enriched {i+1}/{min(len(to_enrich), batch_size)}...")

        time.sleep(0.3)

    print(f"  Enriched {enriched} entries")


# ---------- Filtering ----------

def is_likely_mcp_server(entry):
    """Filter: is this actually an MCP server (not just MCP-adjacent)?"""
    name = entry["name"].lower()
    desc = entry["description"].lower()
    topics = [t.lower() for t in entry["topics"]]
    sources = entry.get("source", [])

    # Strong signals — definitely an MCP server
    if "mcp-server" in name or "mcp_server" in name:
        return True
    if "mcp-server" in topics or "model-context-protocol" in topics or "modelcontextprotocol" in topics:
        return True
    if entry["owner"].lower() == "modelcontextprotocol":
        return True
    if entry.get("has_mcp_json"):
        return True

    # From awesome-list or hub — trust the curation
    if "awesome_list" in sources or "hub" in sources:
        return True

    # From code search — they have MCP SDK references
    if "code_search" in sources:
        return True

    # Medium signals — need multiple
    signals = 0
    if "mcp" in name:
        signals += 1
    if "mcp" in desc or "model context protocol" in desc:
        signals += 1
    if any("mcp" in t for t in topics):
        signals += 1
    if "server" in name or "server" in desc:
        signals += 1

    return signals >= 2


# ---------- Main ----------

def main():
    start_time = time.time()

    # Load existing protodex URLs for comparison
    existing_urls = set()
    if EXISTING_JSON.exists():
        try:
            data = json.load(open(EXISTING_JSON))
            existing_urls = set(s.get("url", "") for s in data.get("servers", []))
            print(f"Loaded {len(existing_urls)} existing Protodex URLs for comparison")
        except Exception as e:
            print(f"Warning: could not load existing data: {e}")

    # Collect from all sources
    source_counts = {}

    topic_repos = scrape_topic_search()
    source_counts["topic_search"] = len(topic_repos)

    code_repos = scrape_code_search()
    source_counts["code_search"] = len(code_repos)

    awesome_repos = scrape_awesome_list()
    source_counts["awesome_list"] = len(awesome_repos)

    hub_repos = scrape_hub()
    source_counts["hub"] = len(hub_repos)

    # Merge all sources, deduplicating on repo_url
    print("\n=== Merging & Deduplicating ===")
    merged = {}

    for source_name, source_dict in [
        ("topic_search", topic_repos),
        ("code_search", code_repos),
        ("awesome_list", awesome_repos),
        ("hub", hub_repos),
    ]:
        for url, entry in source_dict.items():
            # Normalize URL: strip trailing slash, .git, etc.
            clean_url = url.rstrip("/").removesuffix(".git")
            if clean_url in merged:
                # Merge sources
                for src in entry["source"]:
                    if src not in merged[clean_url]["source"]:
                        merged[clean_url]["source"].append(src)
                # Prefer richer data (more stars, has description)
                existing = merged[clean_url]
                if entry["stars"] > existing["stars"]:
                    # Keep better data but preserve merged sources
                    sources = existing["source"]
                    merged[clean_url] = entry
                    merged[clean_url]["source"] = sources
            else:
                merged[clean_url] = entry

    print(f"  Total after merge: {len(merged)}")

    # Enrich partial entries (from awesome-list, code search)
    enrich_partial_entries(merged, batch_size=200)

    # Filter to actual MCP servers
    print("\n=== Filtering to MCP servers ===")
    filtered = {url: entry for url, entry in merged.items() if is_likely_mcp_server(entry)}
    print(f"  After filtering: {len(filtered)} (removed {len(merged) - len(filtered)} non-MCP repos)")

    # Convert to sorted list
    servers = sorted(filtered.values(), key=lambda s: s["stars"], reverse=True)

    # Count new vs existing
    new_urls = set(s["repo_url"] for s in servers) - existing_urls
    new_count = len(new_urls)

    # Category breakdown
    cat_counts = {}
    for s in servers:
        cat_counts[s["category"]] = cat_counts.get(s["category"], 0) + 1

    # Source breakdown (a server can appear in multiple sources)
    src_breakdown = {"topic_search": 0, "code_search": 0, "awesome_list": 0, "hub": 0}
    for s in servers:
        for src in s.get("source", []):
            src_breakdown[src] = src_breakdown.get(src, 0) + 1

    # Save output
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_servers": len(servers),
        "scrape_duration_seconds": round(time.time() - start_time, 1),
        "source_breakdown": src_breakdown,
        "category_breakdown": cat_counts,
        "new_vs_existing": {
            "new": new_count,
            "existing_in_protodex": len(servers) - new_count,
        },
        "servers": servers,
    }

    with open(OUT_FILE, "w") as f:
        json.dump(output, f, indent=2, default=str)

    # Print report
    elapsed = round(time.time() - start_time, 1)
    print(f"\n{'='*60}")
    print(f"SCRAPE COMPLETE — {elapsed}s")
    print(f"{'='*60}")
    print(f"Total unique MCP servers found: {len(servers)}")
    print(f"NEW (not in current Protodex):  {new_count}")
    print(f"\nBy Source:")
    for src, count in sorted(src_breakdown.items(), key=lambda x: -x[1]):
        print(f"  {src:<20} {count:>5}")
    print(f"\nBy Category:")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:<25} {count:>5}")
    print(f"\nSaved to: {OUT_FILE}")

    return servers


if __name__ == "__main__":
    main()
