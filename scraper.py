"""
MCP Server Directory — GitHub Scraper
Scrapes GitHub for public MCP servers, indexes them in SQLite.
"""

import json
import subprocess
import sqlite3
import time
import re
from datetime import datetime, timezone


GH = "/usr/local/bin/gh"
DB_PATH = "/Users/apple/Documents/LuciferForge/mcp-directory/mcp_directory.db"

# Search queries to find MCP servers
SEARCH_QUERIES = [
    # High-signal: repo name contains mcp-server
    {"q": "mcp-server in:name", "sort": "stars", "label": "name:mcp-server"},
    # Topic-based
    {"q": "topic:mcp-server", "sort": "stars", "label": "topic:mcp-server"},
    {"q": "topic:model-context-protocol", "sort": "stars", "label": "topic:model-context-protocol"},
    # Description mentions
    {"q": "\"mcp server\" in:description", "sort": "stars", "label": "desc:mcp-server"},
    {"q": "\"model context protocol\" in:description", "sort": "stars", "label": "desc:model-context-protocol"},
    # Org repos
    {"q": "org:modelcontextprotocol", "sort": "stars", "label": "org:modelcontextprotocol"},
    # SDK users (code search won't work via search/repositories, so use name/desc)
    {"q": "mcp server in:name,description language:python", "sort": "stars", "label": "python-mcp"},
    {"q": "mcp server in:name,description language:typescript", "sort": "stars", "label": "ts-mcp"},
    # FastMCP-based servers
    {"q": "fastmcp in:name,description,readme", "sort": "stars", "label": "fastmcp"},
    # Additional patterns
    {"q": "mcp-server in:name,description fork:false", "sort": "updated", "label": "mcp-server-updated"},
    {"q": "\"mcp\" \"server\" \"tools\" in:readme topic:mcp", "sort": "stars", "label": "mcp-tools-readme"},
    # Sort by recently updated to catch NEW servers (not just popular ones)
    {"q": "mcp-server in:name", "sort": "updated", "label": "name:mcp-server-recent"},
    {"q": "mcp server in:description", "sort": "updated", "label": "desc:mcp-recent"},
    # Language-specific (Go, Rust, Java — growing MCP ecosystems)
    {"q": "mcp server in:name,description language:go", "sort": "stars", "label": "go-mcp"},
    {"q": "mcp server in:name,description language:rust", "sort": "stars", "label": "rust-mcp"},
    {"q": "mcp server in:name,description language:java", "sort": "stars", "label": "java-mcp"},
    {"q": "mcp server in:name,description language:csharp", "sort": "stars", "label": "csharp-mcp"},
    # MCP SDK patterns
    {"q": "\"@modelcontextprotocol/sdk\" in:readme", "sort": "stars", "label": "sdk-ts"},
    {"q": "\"mcp.server\" in:readme language:python", "sort": "stars", "label": "sdk-py"},
    # Created date filters (catch newer servers)
    {"q": "mcp-server in:name created:>2026-03-01", "sort": "stars", "label": "new-march"},
    {"q": "mcp-server in:name created:>2026-04-01", "sort": "stars", "label": "new-april"},
    # Alternate naming patterns
    {"q": "\"mcp-tool\" in:name", "sort": "stars", "label": "name:mcp-tool"},
    {"q": "\"mcp_server\" in:name", "sort": "stars", "label": "name:mcp_server"},
    {"q": "\"mcpserver\" in:name", "sort": "stars", "label": "name:mcpserver"},
]

# Category keywords mapping
CATEGORY_RULES = [
    ("Database", [
        "postgres", "postgresql", "mysql", "sqlite", "mongodb", "mongo", "redis",
        "database", "supabase", "prisma", "drizzle", "sql", "dynamodb", "fauna",
        "neo4j", "graphql", "airtable", "notion-database", "firestore", "couchdb",
        "mariadb", "clickhouse", "cassandra", "timescale", "planetscale",
    ]),
    ("File System", [
        "filesystem", "file-system", "file system", "files", "directory",
        "local files", "file manager", "file browser", "fs ", "gdrive",
        "google drive", "dropbox", "s3", "storage", "blob",
    ]),
    ("AI/LLM", [
        "embedding", "llm", "openai", "anthropic", "claude", "gpt", "gemini",
        "ollama", "hugging", "vector", "rag", "agent", "langchain", "llamaindex",
        "ai ", "artificial intelligence", "machine learning", "ml ", "transformer",
        "stable diffusion", "midjourney", "replicate", "groq", "mistral",
        "perplexity", "cohere",
    ]),
    ("Search", [
        "search", "brave", "serpapi", "google search", "bing", "duckduckgo",
        "knowledge base", "web search", "scraper", "crawl", "tavily",
        "exa ", "you.com",
    ]),
    ("DevOps", [
        "docker", "kubernetes", "k8s", "terraform", "ansible", "ci/cd", "cicd",
        "jenkins", "github actions", "monitoring", "prometheus", "grafana",
        "cloudflare", "aws", "azure", "gcp", "vercel", "netlify", "railway",
        "fly.io", "render", "heroku", "sentry", "datadog", "pagerduty",
    ]),
    ("Security", [
        "security", "auth", "authentication", "vault", "secret", "encrypt",
        "firewall", "scan", "vulnerability", "pentest", "audit", "compliance",
        "oauth", "saml", "jwt", "certificate",
    ]),
    ("Communication", [
        "email", "smtp", "imap", "chat", "notification", "sms", "twilio",
        "sendgrid", "mailgun", "discord", "telegram", "whatsapp", "teams",
        "matrix", "signal", "pushover", "ntfy",
    ]),
    ("API Integration", [
        "slack", "github", "jira", "confluence", "trello", "asana", "linear",
        "stripe", "shopify", "salesforce", "hubspot", "zendesk", "intercom",
        "twitch", "spotify", "twitter", "x.com", "reddit", "youtube",
        "google maps", "weather", "calendar", "google calendar", "outlook",
        "todoist", "clickup", "monday", "figma", "canva", "zapier",
        "webhook", "rest api", "api", "integration",
    ]),
    ("Browser/Web", [
        "browser", "puppeteer", "playwright", "selenium", "web", "scrape",
        "chromium", "headless", "url", "fetch", "http",
    ]),
    ("Code/Dev Tools", [
        "git ", "code", "linter", "formatter", "debug", "test", "lint",
        "prettier", "eslint", "compiler", "ide", "editor", "vscode",
        "intellij", "jupyter", "notebook", "repl", "sandbox", "exec",
        "terminal", "shell", "command", "cli",
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
]


def init_db():
    """Initialize SQLite database with schema."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY,
            repo TEXT UNIQUE,
            name TEXT,
            description TEXT,
            stars INTEGER,
            language TEXT,
            topics TEXT,
            tools TEXT,
            category TEXT,
            last_updated TEXT,
            scraped_at TEXT,
            readme_excerpt TEXT,
            url TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_servers_category ON servers(category)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_servers_stars ON servers(stars DESC)
    """)
    conn.commit()
    return conn


def gh_api(endpoint, params=None, max_retries=3):
    """Call GitHub API via gh CLI."""
    cmd = [GH, "api", endpoint, "-X", "GET"]
    if params:
        for k, v in params.items():
            cmd.extend(["-f", f"{k}={v}"])

    for attempt in range(max_retries):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                if "rate limit" in result.stderr.lower() or "403" in result.stderr:
                    wait = 60 * (attempt + 1)
                    print(f"  Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                if "422" in result.stderr:
                    # Unprocessable — bad query
                    print(f"  Bad query, skipping: {result.stderr[:100]}")
                    return None
                print(f"  API error: {result.stderr[:200]}")
                return None
            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            print(f"  Timeout on attempt {attempt + 1}")
            time.sleep(5)
        except json.JSONDecodeError:
            print(f"  Invalid JSON response")
            return None
    return None


def search_repos(query_config):
    """Search GitHub repos with a query. Returns list of repo dicts."""
    q = query_config["q"]
    sort = query_config.get("sort", "stars")
    label = query_config.get("label", q)

    all_repos = []
    # Fetch up to 3 pages (300 repos) per query
    for page in range(1, 4):
        print(f"  [{label}] page {page}...")
        data = gh_api("search/repositories", {
            "q": q,
            "per_page": "100",
            "sort": sort,
            "page": str(page),
        })
        if not data or "items" not in data:
            break

        items = data["items"]
        if not items:
            break
        all_repos.extend(items)

        total = data.get("total_count", 0)
        if page * 100 >= total or page * 100 >= 1000:
            break

        # Respect rate limits
        time.sleep(2)

    return all_repos


def fetch_readme(repo_full_name):
    """Fetch README content for a repo."""
    data = gh_api(f"repos/{repo_full_name}/readme")
    if not data:
        return ""

    # README is base64 encoded
    import base64
    content = data.get("content", "")
    if content:
        try:
            decoded = base64.b64decode(content).decode("utf-8", errors="replace")
            return decoded
        except Exception:
            return ""
    return ""


def extract_tools_from_readme(readme_text):
    """Extract MCP tool names from README content."""
    tools = set()

    # Pattern: tool names in backticks or code blocks
    # Common patterns: `tool_name`, @tool("name"), name="tool_name"
    patterns = [
        r'@(?:mcp\.)?tool\(["\']([^"\']+)',           # @tool("name") or @mcp.tool("name")
        r'name\s*[=:]\s*["\']([a-z_][a-z0-9_]*)["\']', # name="tool_name"
        r'`([a-z_][a-z0-9_]*)`\s*[-:]\s',              # `tool_name` - description
        r'\|\s*`([a-z_][a-z0-9_]*)`\s*\|',             # | `tool_name` | in table
        r'#+\s*(?:Tool|Function)s?\s*\n.*?`([a-z_][a-z0-9_]*)`', # Under "Tools" heading
        r'"tools".*?"name"\s*:\s*"([^"]+)"',            # JSON: "name": "tool_name"
    ]

    for pattern in patterns:
        matches = re.findall(pattern, readme_text, re.IGNORECASE | re.DOTALL)
        for m in matches:
            if len(m) > 2 and len(m) < 50 and m not in (
                "name", "tool", "function", "server", "client", "example",
                "install", "build", "test", "run", "start", "stop", "help",
                "true", "false", "none", "null", "string", "number", "boolean",
                "import", "from", "class", "def", "async", "await", "return",
            ):
                tools.add(m)

    return sorted(tools)[:20]  # Cap at 20 tools


def categorize(name, description, topics, readme_excerpt):
    """Auto-categorize a server based on its metadata."""
    text = f"{name} {description} {topics} {readme_excerpt}".lower()

    scores = {}
    for category, keywords in CATEGORY_RULES:
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[category] = score

    if scores:
        return max(scores, key=scores.get)
    return "Other"


def is_mcp_server(repo_data, readme_text=""):
    """Filter: is this actually an MCP server?"""
    name = (repo_data.get("name") or "").lower()
    desc = (repo_data.get("description") or "").lower()
    topics = [t.lower() for t in (repo_data.get("topics") or [])]
    full_name = repo_data.get("full_name", "")

    # Strong signals
    if "mcp-server" in name or "mcp_server" in name:
        return True
    if "mcp-server" in topics or "model-context-protocol" in topics:
        return True
    if full_name.startswith("modelcontextprotocol/"):
        return True

    # Medium signals — need at least 2
    signals = 0
    if "mcp" in name:
        signals += 1
    if "mcp" in desc:
        signals += 1
    if "model context protocol" in desc:
        signals += 2
    if any("mcp" in t for t in topics):
        signals += 1
    if "server" in name or "server" in desc:
        signals += 1
    if readme_text and ("mcp" in readme_text.lower()[:2000]):
        signals += 1

    return signals >= 2


def scrape(fetch_readmes=True, readme_batch_size=50):
    """Main scrape function. Returns count of new servers indexed."""
    conn = init_db()
    seen = set()

    # Load existing repos
    existing = set(row[0] for row in conn.execute("SELECT repo FROM servers").fetchall())
    print(f"Existing entries: {len(existing)}")

    candidates = []

    for qc in SEARCH_QUERIES:
        print(f"\nSearching: {qc['label']}")
        repos = search_repos(qc)
        print(f"  Found {len(repos)} results")

        for r in repos:
            full_name = r.get("full_name", "")
            if full_name in seen:
                continue
            seen.add(full_name)

            if is_mcp_server(r):
                candidates.append(r)

        # Rate limit between queries
        time.sleep(3)

    print(f"\n{'='*60}")
    print(f"Total unique candidates: {len(candidates)}")
    new_candidates = [c for c in candidates if c["full_name"] not in existing]
    print(f"New (not yet in DB): {len(new_candidates)}")

    # Process candidates
    new_count = 0
    total = len(new_candidates)

    for i, repo in enumerate(new_candidates):
        full_name = repo["full_name"]
        name = repo.get("name", "")
        desc = repo.get("description") or ""
        stars = repo.get("stargazers_count", 0)
        language = repo.get("language") or ""
        topics = ",".join(repo.get("topics") or [])
        last_updated = repo.get("updated_at", "")
        url = repo.get("html_url", "")

        readme_text = ""
        tools_str = ""

        if fetch_readmes and i < readme_batch_size:
            if (i + 1) % 10 == 0:
                print(f"  Fetching READMEs... {i+1}/{min(total, readme_batch_size)}")
            readme_text = fetch_readme(full_name)
            if readme_text:
                tools = extract_tools_from_readme(readme_text)
                tools_str = ",".join(tools)
            time.sleep(0.5)  # Rate limit

        # Truncate readme for storage
        readme_excerpt = ""
        if readme_text:
            # Get first meaningful paragraph
            lines = readme_text.split("\n")
            excerpt_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and not stripped.startswith("!") and not stripped.startswith("["):
                    excerpt_lines.append(stripped)
                    if len(" ".join(excerpt_lines)) > 300:
                        break
            readme_excerpt = " ".join(excerpt_lines)[:500]

        category = categorize(name, desc, topics, readme_excerpt)

        try:
            conn.execute("""
                INSERT OR REPLACE INTO servers
                (repo, name, description, stars, language, topics, tools, category,
                 last_updated, scraped_at, readme_excerpt, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                full_name, name, desc, stars, language, topics, tools_str, category,
                last_updated, datetime.now(timezone.utc).isoformat(), readme_excerpt, url,
            ))
            new_count += 1
        except sqlite3.IntegrityError:
            pass

    conn.commit()

    total_in_db = conn.execute("SELECT COUNT(*) FROM servers").fetchone()[0]
    print(f"\nIndexed {new_count} new servers. Total in DB: {total_in_db}")
    conn.close()
    return new_count
