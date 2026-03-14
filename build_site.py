#!/usr/bin/env python3
"""
Protodex.io — Static site generator for MCP Server Directory.
Reads mcp_directory.json → generates full static site into site/ directory.
"""

import json
import os
import re
import math
from datetime import datetime
from html import escape
from urllib.parse import quote

SITE_DIR = os.path.join(os.path.dirname(__file__), "docs")
DATA_FILE = os.path.join(os.path.dirname(__file__), "mcp_directory.json")
DOMAIN = "protodex.io"
SITE_URL = f"https://{DOMAIN}"
SITE_NAME = "Protodex"
SITE_TAGLINE = "The MCP Server Index"
SITE_DESCRIPTION = "Discover {total} Model Context Protocol (MCP) servers. Search, browse by category, and find the right MCP server for Claude, Cursor, and AI agents."

# Category metadata for SEO intros
CATEGORY_META = {
    "AI/LLM": {
        "slug": "ai-llm",
        "icon": "🤖",
        "description": "MCP servers for AI model integration, LLM orchestration, prompt management, and agent frameworks.",
        "color": "#8B5CF6"
    },
    "Code/Dev Tools": {
        "slug": "code-dev-tools",
        "icon": "💻",
        "description": "MCP servers for code analysis, development workflows, IDE integration, and developer productivity.",
        "color": "#3B82F6"
    },
    "API Integration": {
        "slug": "api-integration",
        "icon": "🔌",
        "description": "MCP servers that connect to third-party APIs, webhooks, and external services.",
        "color": "#10B981"
    },
    "Memory/Knowledge": {
        "slug": "memory-knowledge",
        "icon": "🧠",
        "description": "MCP servers for knowledge management, vector stores, memory persistence, and RAG systems.",
        "color": "#F59E0B"
    },
    "Database": {
        "slug": "database",
        "icon": "🗄️",
        "description": "MCP servers for database connectivity — PostgreSQL, MySQL, SQLite, MongoDB, Redis, and more.",
        "color": "#EF4444"
    },
    "Browser/Web": {
        "slug": "browser-web",
        "icon": "🌐",
        "description": "MCP servers for web scraping, browser automation, and web content extraction.",
        "color": "#06B6D4"
    },
    "Security": {
        "slug": "security",
        "icon": "🔒",
        "description": "MCP servers for security scanning, vulnerability detection, and safety guardrails.",
        "color": "#DC2626"
    },
    "Search": {
        "slug": "search",
        "icon": "🔍",
        "description": "MCP servers for web search, semantic search, and information retrieval.",
        "color": "#7C3AED"
    },
    "DevOps": {
        "slug": "devops",
        "icon": "⚙️",
        "description": "MCP servers for CI/CD, infrastructure management, monitoring, and deployment automation.",
        "color": "#059669"
    },
    "Communication": {
        "slug": "communication",
        "icon": "💬",
        "description": "MCP servers for Slack, email, Discord, and other messaging platforms.",
        "color": "#2563EB"
    },
    "File System": {
        "slug": "file-system",
        "icon": "📁",
        "description": "MCP servers for local and cloud file management, S3, Google Drive, and storage services.",
        "color": "#D97706"
    },
    "Data/Analytics": {
        "slug": "data-analytics",
        "icon": "📊",
        "description": "MCP servers for data processing, analytics, visualization, and business intelligence.",
        "color": "#EC4899"
    },
    "Other": {
        "slug": "other",
        "icon": "📦",
        "description": "MCP servers that don't fit neatly into other categories — utilities, experiments, and niche tools.",
        "color": "#6B7280"
    },
}


GITHUB_EMOJIS = {
    ":robot:": "", ":star:": "", ":fire:": "", ":rocket:": "",
    ":sparkles:": "", ":zap:": "", ":bulb:": "", ":gear:": "",
    ":lock:": "", ":key:": "", ":shield:": "", ":warning:": "",
    ":check:": "", ":white_check_mark:": "", ":heavy_check_mark:": "",
    ":x:": "", ":boom:": "", ":tada:": "", ":eyes:": "",
    ":memo:": "", ":pencil:": "", ":book:": "", ":books:": "",
    ":hammer:": "", ":wrench:": "", ":nut_and_bolt:": "",
    ":globe_with_meridians:": "", ":earth_americas:": "",
    ":earth_asia:": "", ":earth_africa:": "",
    ":computer:": "", ":desktop_computer:": "", ":laptop:": "",
    ":iphone:": "", ":phone:": "",
    ":package:": "", ":inbox_tray:": "", ":outbox_tray:": "",
    ":link:": "", ":chains:": "", ":mag:": "", ":mag_right:": "",
    ":chart_with_upwards_trend:": "", ":bar_chart:": "",
    ":cloud:": "", ":thunder_cloud_and_rain:": "",
    ":snake:": "", ":crab:": "", ":whale:": "", ":elephant:": "",
    ":bug:": "", ":ant:": "", ":bee:": "",
    ":arrow_right:": "", ":arrow_left:": "", ":arrow_up:": "", ":arrow_down:": "",
    ":point_right:": "", ":point_left:": "",
    ":heart:": "", ":blue_heart:": "", ":green_heart:": "", ":purple_heart:": "",
    ":hammer_and_wrench:": "", ":toolbox:": "",
    ":clipboard:": "", ":pushpin:": "", ":round_pushpin:": "",
    ":light_bulb:": "", ":electric_plug:": "",
    ":floppy_disk:": "", ":file_folder:": "", ":open_file_folder:": "",
    ":speech_balloon:": "", ":thought_balloon:": "",
    ":brain:": "", ":dna:": "",
    ":satellite:": "", ":telescope:": "",
    ":test_tube:": "", ":microscope:": "",
    ":art:": "", ":paintbrush:": "", ":crayon:": "",
    ":musical_note:": "", ":headphones:": "",
    ":video_camera:": "", ":camera:": "",
    ":mailbox:": "", ":email:": "", ":envelope:": "",
    ":calendar:": "", ":clock1:": "", ":hourglass:": "",
    ":trophy:": "", ":medal:": "", ":crown:": "",
    ":moneybag:": "", ":dollar:": "", ":credit_card:": "",
    ":page_facing_up:": "", ":scroll:": "",
    ":construction:": "", ":triangular_flag_on_post:": "",
}

def clean_github_emojis(text):
    """Replace GitHub emoji shortcodes with unicode or remove them."""
    if not text or ':' not in text:
        return text
    import re
    def replace_emoji(match):
        code = match.group(0)
        return GITHUB_EMOJIS.get(code, '')
    return re.sub(r':[a-z0-9_]+:', replace_emoji, text)


def slugify(text):
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def format_stars(stars):
    """Format star count: 1234 -> 1.2K, 12345 -> 12.3K"""
    if stars >= 1000:
        return f"{stars/1000:.1f}K"
    return str(stars)


def truncate(text, length=155):
    """Truncate text for meta descriptions."""
    if not text:
        return ""
    if len(text) <= length:
        return text
    return text[:length-3].rsplit(' ', 1)[0] + "..."


def time_ago(date_str):
    """Convert ISO date to relative time."""
    if not date_str:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        delta = now - dt
        if delta.days > 365:
            return f"{delta.days // 365}y ago"
        if delta.days > 30:
            return f"{delta.days // 30}mo ago"
        if delta.days > 0:
            return f"{delta.days}d ago"
        return "today"
    except Exception:
        return "Unknown"


def lang_color(lang):
    """GitHub-style language colors."""
    colors = {
        "Python": "#3572A5", "TypeScript": "#3178C6", "JavaScript": "#F7DF1E",
        "Go": "#00ADD8", "Rust": "#DEA584", "C#": "#178600", "Java": "#B07219",
        "C++": "#F34B7D", "PHP": "#4F5D95", "Swift": "#F05138", "Ruby": "#701516",
        "Kotlin": "#A97BFF", "Dart": "#00B4AB", "Shell": "#89E051",
    }
    return colors.get(lang, "#6B7280")


# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────

CSS = """
:root {
    --bg: #09090b;
    --bg-card: #131316;
    --bg-card-hover: #1a1a1f;
    --bg-hover: #18181b;
    --border: #27272a;
    --border-hover: #3f3f46;
    --text: #fafafa;
    --text-muted: #a1a1aa;
    --text-dim: #71717a;
    --accent: #8B5CF6;
    --accent-hover: #7C3AED;
    --accent-glow: rgba(139, 92, 246, 0.15);
    --accent-soft: rgba(139, 92, 246, 0.08);
    --green: #22C55E;
    --yellow: #FACC15;
    --blue: #60A5FA;
    --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    --mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
    --radius: 10px;
    --radius-lg: 16px;
    --max-w: 1200px;
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
    --shadow-lg: 0 16px 48px rgba(0,0,0,0.5);
}

* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; }

body {
    font-family: var(--font);
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

a { color: var(--accent); text-decoration: none; transition: color 0.15s; }
a:hover { color: var(--accent-hover); }

.container { max-width: var(--max-w); margin: 0 auto; padding: 0 24px; }

/* Header */
header {
    border-bottom: 1px solid var(--border);
    padding: 14px 0;
    position: sticky;
    top: 0;
    background: rgba(9, 9, 11, 0.85);
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    z-index: 100;
}
header .container {
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.logo {
    font-size: 1.3rem;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -0.5px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.logo-icon {
    width: 28px;
    height: 28px;
    background: linear-gradient(135deg, var(--accent), #EC4899);
    border-radius: 7px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    color: #fff;
}
.logo span { color: var(--accent); }
.logo:hover { text-decoration: none; color: var(--text); }
nav { display: flex; gap: 8px; align-items: center; }
nav a {
    color: var(--text-muted);
    font-size: 0.875rem;
    font-weight: 500;
    padding: 6px 14px;
    border-radius: 6px;
    transition: all 0.15s;
}
nav a:hover { color: var(--text); background: var(--bg-hover); text-decoration: none; }
nav a.nav-cta {
    background: var(--accent);
    color: #fff;
    font-weight: 600;
}
nav a.nav-cta:hover { background: var(--accent-hover); }

/* Hero */
.hero {
    text-align: center;
    padding: 100px 0 48px;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -200px;
    left: 50%;
    transform: translateX(-50%);
    width: 800px;
    height: 600px;
    background: radial-gradient(ellipse at center, rgba(139, 92, 246, 0.12) 0%, rgba(139, 92, 246, 0.04) 40%, transparent 70%);
    pointer-events: none;
}
.hero::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: radial-gradient(rgba(139, 92, 246, 0.07) 1px, transparent 1px);
    background-size: 24px 24px;
    pointer-events: none;
    mask-image: radial-gradient(ellipse at center, black 30%, transparent 70%);
    -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 70%);
}
.hero-content { position: relative; z-index: 1; }
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 16px;
    background: var(--accent-soft);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 100px;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--accent);
    margin-bottom: 24px;
    letter-spacing: 0.02em;
}
.hero-badge .pulse {
    width: 6px;
    height: 6px;
    background: var(--green);
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }
    50% { opacity: 0.8; box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
}
.hero h1 {
    font-size: 3.5rem;
    font-weight: 900;
    letter-spacing: -2px;
    margin-bottom: 20px;
    line-height: 1.05;
    max-width: 700px;
    margin-left: auto;
    margin-right: auto;
}
.hero h1 .gradient {
    background: linear-gradient(135deg, var(--accent) 0%, #EC4899 50%, var(--accent) 100%);
    background-size: 200% 200%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gradient-shift 6s ease-in-out infinite;
}
@keyframes gradient-shift {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}
.hero p {
    font-size: 1.15rem;
    color: var(--text-muted);
    max-width: 540px;
    margin: 0 auto 36px;
    line-height: 1.7;
}
.hero-sub {
    font-size: 0.85rem;
    color: var(--text-dim);
    margin-top: 16px;
    display: flex;
    justify-content: center;
    gap: 20px;
    flex-wrap: wrap;
}
.hero-sub span {
    display: flex;
    align-items: center;
    gap: 5px;
}

/* Search */
.search-wrap {
    max-width: 580px;
    margin: 0 auto;
    position: relative;
}
.search-wrap input {
    width: 100%;
    padding: 16px 20px 16px 48px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    color: var(--text);
    font-size: 1rem;
    font-weight: 500;
    outline: none;
    transition: all 0.2s;
    box-shadow: var(--shadow-sm), 0 0 0 0 var(--accent-glow);
}
.search-wrap input:focus {
    border-color: var(--accent);
    box-shadow: var(--shadow-md), 0 0 0 4px var(--accent-glow);
}
.search-wrap input::placeholder { color: var(--text-dim); font-weight: 400; }
.search-icon {
    position: absolute;
    left: 18px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-dim);
    font-size: 1rem;
    pointer-events: none;
}
.search-results {
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    right: 0;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    max-height: 420px;
    overflow-y: auto;
    display: none;
    z-index: 200;
    box-shadow: var(--shadow-lg);
}
.search-results.active { display: block; }
.search-result-item {
    padding: 14px 18px;
    border-bottom: 1px solid var(--border);
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: background 0.1s;
}
.search-result-item:hover { background: var(--bg-card-hover); text-decoration: none; }
.search-result-item:first-child { border-radius: var(--radius-lg) var(--radius-lg) 0 0; }
.search-result-item:last-child { border-bottom: none; border-radius: 0 0 var(--radius-lg) var(--radius-lg); }
.search-result-name { font-weight: 600; font-size: 0.95rem; color: var(--text); }
.search-result-desc { color: var(--text-dim); font-size: 0.8rem; margin-top: 3px; }
.search-result-meta { color: var(--text-dim); font-size: 0.8rem; white-space: nowrap; margin-left: 16px; }

/* Stats bar */
.stats-bar {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-bottom: 72px;
    flex-wrap: wrap;
    padding: 0 20px;
}
.stat {
    text-align: center;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 32px;
    min-width: 150px;
    transition: all 0.2s;
}
.stat:hover { border-color: var(--border-hover); transform: translateY(-1px); }
.stat-num {
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -1px;
    line-height: 1.2;
}
.stat-label {
    font-size: 0.75rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    margin-top: 2px;
}

/* Value props */
.value-props {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 72px;
}
.value-prop {
    text-align: center;
    padding: 32px 24px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    transition: all 0.2s;
}
.value-prop:hover { border-color: var(--border-hover); text-decoration: none; transform: translateY(-2px); box-shadow: var(--shadow-md); }
a.value-prop { color: inherit; }
.value-prop-icon {
    font-size: 1.8rem;
    margin-bottom: 12px;
}
.value-prop h3 {
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 6px;
}
.value-prop p {
    font-size: 0.85rem;
    color: var(--text-muted);
    line-height: 1.5;
}

/* Section titles */
.section-title {
    font-size: 1.5rem;
    font-weight: 800;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
}
.section-subtitle {
    color: var(--text-muted);
    font-size: 0.9rem;
    margin-bottom: 28px;
}

/* Category grid */
.cat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
    margin-bottom: 72px;
}
.cat-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
    gap: 8px;
    position: relative;
    overflow: hidden;
}
.cat-card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    border-radius: 3px 0 0 3px;
    opacity: 0;
    transition: opacity 0.2s;
}
.cat-card:hover {
    border-color: var(--border-hover);
    background: var(--bg-card-hover);
    text-decoration: none;
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
.cat-card:hover::before { opacity: 1; }
.cat-icon { font-size: 1.5rem; }
.cat-name { font-weight: 700; color: var(--text); font-size: 0.9rem; }
.cat-count { color: var(--text-dim); font-size: 0.8rem; font-weight: 500; }

/* Server cards (grid) */
.server-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 14px;
    margin-bottom: 60px;
}
.server-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.server-card:hover {
    border-color: var(--border-hover);
    background: var(--bg-card-hover);
    text-decoration: none;
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
.server-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
}
.server-card-name {
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--text);
    word-break: break-word;
}
.server-card-stars {
    display: flex;
    align-items: center;
    gap: 4px;
    color: var(--yellow);
    font-size: 0.85rem;
    white-space: nowrap;
    font-weight: 600;
}
.server-card-desc {
    color: var(--text-muted);
    font-size: 0.84rem;
    line-height: 1.55;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.server-card-footer {
    display: flex;
    gap: 6px;
    align-items: center;
    margin-top: auto;
    flex-wrap: wrap;
}
.tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    background: var(--accent-soft);
    color: var(--accent);
    border: 1px solid rgba(139, 92, 246, 0.15);
    letter-spacing: 0.01em;
}
.tag-lang {
    background: rgba(96, 165, 250, 0.08);
    color: var(--blue);
    border-color: rgba(96, 165, 250, 0.15);
}
.lang-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
}

/* Server table (category pages) */
.server-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 40px;
}
.server-table th {
    text-align: left;
    padding: 12px 16px;
    border-bottom: 2px solid var(--border);
    color: var(--text-dim);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
}
.server-table td {
    padding: 14px 16px;
    border-bottom: 1px solid var(--border);
    font-size: 0.9rem;
}
.server-table tr { transition: background 0.1s; }
.server-table tr:hover { background: var(--bg-hover); }
.server-table .name-cell a { font-weight: 600; }
.server-table .desc-cell {
    color: var(--text-muted);
    max-width: 400px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 0.85rem;
}
.server-table .stars-cell {
    color: var(--yellow);
    white-space: nowrap;
    font-weight: 600;
}
.server-table .lang-cell { white-space: nowrap; }

/* Server detail page */
.server-detail { padding: 48px 0; }
.breadcrumb {
    font-size: 0.85rem;
    color: var(--text-dim);
    margin-bottom: 28px;
    font-weight: 500;
}
.breadcrumb a { color: var(--text-muted); }
.breadcrumb a:hover { color: var(--text); }
.detail-header { margin-bottom: 8px; }
.detail-title {
    font-size: 2.2rem;
    font-weight: 900;
    letter-spacing: -1.5px;
    margin-bottom: 8px;
    word-break: break-word;
}
.detail-repo {
    font-size: 0.9rem;
    color: var(--text-dim);
    font-family: var(--mono);
    font-weight: 500;
}
.detail-meta {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    margin: 24px 0 32px;
    padding: 16px 20px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
}
.meta-item {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--text-muted);
    font-size: 0.9rem;
    font-weight: 500;
}
.detail-desc {
    font-size: 1.05rem;
    line-height: 1.75;
    color: var(--text-muted);
    margin-bottom: 32px;
    max-width: 700px;
}
.detail-section {
    margin-bottom: 32px;
}
.detail-section h2 {
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 14px;
    color: var(--text);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 0.85rem;
}
.detail-readme {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    color: var(--text-muted);
    font-size: 0.88rem;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
}
.detail-tools {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}
.tool-tag {
    padding: 6px 14px;
    background: rgba(34, 197, 94, 0.08);
    border: 1px solid rgba(34, 197, 94, 0.15);
    color: var(--green);
    border-radius: 6px;
    font-size: 0.8rem;
    font-family: var(--mono);
    font-weight: 500;
}
.detail-sidebar {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 32px;
}
.sidebar-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
}
.sidebar-card-label {
    font-size: 0.7rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
    margin-bottom: 6px;
}
.sidebar-card-value {
    font-size: 1.3rem;
    font-weight: 800;
}
.btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 12px 28px;
    background: var(--accent);
    color: #fff;
    border-radius: var(--radius);
    font-weight: 600;
    font-size: 0.95rem;
    transition: all 0.2s;
    box-shadow: 0 2px 8px rgba(139, 92, 246, 0.25);
}
.btn:hover {
    background: var(--accent-hover);
    text-decoration: none;
    color: #fff;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(139, 92, 246, 0.35);
}
.btn-outline {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text);
    box-shadow: none;
}
.btn-outline:hover {
    border-color: var(--accent);
    color: var(--accent);
    box-shadow: none;
    background: var(--accent-soft);
}

.related-servers { margin-bottom: 60px; }

/* Popular search chips */
.search-chips {
    display: flex;
    justify-content: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 16px;
}
.search-chips span.chips-label {
    color: var(--text-dim);
    font-size: 0.8rem;
    font-weight: 500;
    display: flex;
    align-items: center;
}
.chip {
    padding: 5px 14px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 100px;
    font-size: 0.8rem;
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.15s;
    font-weight: 500;
}
.chip:hover {
    border-color: var(--accent);
    color: var(--accent);
    background: var(--accent-soft);
    text-decoration: none;
}

/* Use case cards */
.use-cases {
    margin-bottom: 72px;
}
.use-case-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
}
.use-case {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 28px 24px;
    transition: all 0.2s;
    display: block;
}
.use-case:hover {
    border-color: var(--border-hover);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    text-decoration: none;
}
.use-case-scenario {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 10px;
}
.use-case-query {
    display: flex;
    align-items: center;
    gap: 10px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 14px;
    font-family: var(--mono);
    font-size: 0.85rem;
    color: var(--text);
    font-weight: 500;
}
.use-case-query svg { color: var(--text-dim); flex-shrink: 0; }
.use-case-result {
    font-size: 0.85rem;
    color: var(--text-muted);
    line-height: 1.6;
}
.use-case-result strong { color: var(--accent); font-weight: 600; }
.use-case-arrow {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 14px;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--accent);
}

/* Language pills row */
.lang-row {
    display: flex;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 72px;
}
.lang-pill {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 100px;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text-muted);
    transition: all 0.15s;
}
.lang-pill:hover {
    border-color: var(--border-hover);
    color: var(--text);
    text-decoration: none;
    transform: translateY(-1px);
}
.lang-pill .lang-dot { width: 10px; height: 10px; }

/* Footer */
footer {
    border-top: 1px solid var(--border);
    padding: 48px 0;
    margin-top: 40px;
}
.footer-inner {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 40px;
    flex-wrap: wrap;
}
.footer-brand {
    max-width: 300px;
}
.footer-brand .logo { margin-bottom: 12px; }
.footer-brand p { color: var(--text-dim); font-size: 0.85rem; line-height: 1.6; }
.footer-links { display: flex; gap: 48px; }
.footer-col h4 {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin-bottom: 12px;
}
.footer-col a {
    display: block;
    color: var(--text-dim);
    font-size: 0.85rem;
    padding: 3px 0;
    transition: color 0.15s;
}
.footer-col a:hover { color: var(--text); text-decoration: none; }
.footer-bottom {
    border-top: 1px solid var(--border);
    margin-top: 32px;
    padding-top: 24px;
    text-align: center;
    color: var(--text-dim);
    font-size: 0.8rem;
}

/* Responsive */
@media (max-width: 768px) {
    .hero { padding: 60px 0 36px; }
    .hero h1 { font-size: 2.2rem; letter-spacing: -1px; }
    .hero p { font-size: 1rem; }
    .stats-bar { gap: 8px; }
    .stat { padding: 16px 20px; min-width: 120px; }
    .stat-num { font-size: 1.4rem; }
    .value-props { grid-template-columns: 1fr; gap: 12px; }
    .server-grid { grid-template-columns: 1fr; }
    .cat-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }
    .detail-sidebar { grid-template-columns: 1fr; }
    .detail-title { font-size: 1.6rem; }
    nav { gap: 4px; }
    nav a { padding: 6px 10px; font-size: 0.8rem; }
    .server-table { font-size: 0.8rem; }
    .server-table .desc-cell { max-width: 200px; }
    .footer-links { gap: 32px; }
    .footer-inner { flex-direction: column; }
    .hero-sub { gap: 12px; }
}

/* Page header (category/other pages) */
.page-header {
    padding: 56px 0 36px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 40px;
    position: relative;
}
.page-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(180deg, rgba(139, 92, 246, 0.03) 0%, transparent 100%);
    pointer-events: none;
}
.page-header h1 {
    font-size: 2rem;
    font-weight: 900;
    letter-spacing: -1px;
    margin-bottom: 8px;
    position: relative;
}
.page-header p {
    color: var(--text-muted);
    font-size: 1rem;
    max-width: 600px;
    position: relative;
}

/* Submit page */
.submit-content {
    max-width: 700px;
    margin: 0 auto;
    padding: 40px 0 80px;
}
.submit-content h2 { margin-bottom: 16px; font-weight: 700; }
.submit-content p { color: var(--text-muted); margin-bottom: 24px; line-height: 1.7; }
.submit-content ol {
    color: var(--text-muted);
    padding-left: 24px;
    margin-bottom: 32px;
}
.submit-content li { margin-bottom: 10px; line-height: 1.6; }
"""


# ─────────────────────────────────────────────
# HTML Components
# ─────────────────────────────────────────────

def html_head(title, description, canonical_path="/", extra_head=""):
    canonical = f"{SITE_URL}{canonical_path}"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)}</title>
    <meta name="description" content="{escape(truncate(description, 155))}">
    <meta property="og:title" content="{escape(title)}">
    <meta property="og:description" content="{escape(truncate(description, 155))}">
    <meta property="og:url" content="{escape(canonical)}">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="{SITE_NAME}">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{escape(title)}">
    <meta name="twitter:description" content="{escape(truncate(description, 155))}">
    <link rel="canonical" href="{escape(canonical)}">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self';">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚡</text></svg>">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>{CSS}</style>
    {extra_head}
</head>
<body>
"""


def html_header(current=""):
    return f"""
<header>
    <div class="container">
        <a href="/" class="logo">
            <div class="logo-icon">P</div>
            <span>Proto</span>dex
        </a>
        <nav>
            <a href="/">Explore</a>
            <a href="/categories.html">Categories</a>
            <a href="https://github.com/LuciferForge/mcp-directory" target="_blank" rel="noopener">GitHub</a>
            <a href="/submit.html" class="nav-cta">Submit Server</a>
        </nav>
    </div>
</header>
"""


def html_footer():
    year = datetime.now().year
    return f"""
<footer>
    <div class="container">
        <div class="footer-inner">
            <div class="footer-brand">
                <a href="/" class="logo">
                    <div class="logo-icon">P</div>
                    <span>Proto</span>dex
                </a>
                <p>The largest index of MCP servers. Helping developers find the right tools for AI-powered workflows.</p>
            </div>
            <div class="footer-links">
                <div class="footer-col">
                    <h4>Directory</h4>
                    <a href="/">Explore Servers</a>
                    <a href="/categories.html">Categories</a>
                    <a href="/submit.html">Submit a Server</a>
                </div>
                <div class="footer-col">
                    <h4>Project</h4>
                    <a href="https://github.com/LuciferForge/mcp-directory" target="_blank" rel="noopener">GitHub</a>
                    <a href="https://github.com/LuciferForge" target="_blank" rel="noopener">LuciferForge</a>
                </div>
            </div>
        </div>
        <div class="footer-bottom">
            &copy; {year} {SITE_NAME}. Open source. Updated weekly from GitHub.
        </div>
    </div>
</footer>
</body>
</html>
"""


def server_card_html(server):
    slug = slugify(server["repo"].replace("/", "-"))
    desc = escape(truncate(clean_github_emojis(server.get("description") or "No description"), 120))
    stars = format_stars(server.get("stars", 0))
    lang = server.get("language", "")
    cat = server.get("category", "Other")
    cat_meta = CATEGORY_META.get(cat, CATEGORY_META["Other"])

    lang_html = ""
    if lang:
        lc = lang_color(lang)
        lang_html = f'<span class="tag tag-lang"><span class="lang-dot" style="background:{lc}"></span>{escape(lang)}</span>'

    return f"""
    <a href="/servers/{slug}.html" class="server-card">
        <div class="server-card-header">
            <span class="server-card-name">{escape(server["name"])}</span>
            <span class="server-card-stars">★ {stars}</span>
        </div>
        <div class="server-card-desc">{desc}</div>
        <div class="server-card-footer">
            <span class="tag">{cat_meta['icon']} {escape(cat)}</span>
            {lang_html}
        </div>
    </a>"""


def server_row_html(server, rank=None):
    slug = slugify(server["repo"].replace("/", "-"))
    name = escape(server["name"])
    desc = escape(truncate(clean_github_emojis(server.get("description") or ""), 80))
    stars = format_stars(server.get("stars", 0))
    lang = server.get("language", "")
    updated = time_ago(server.get("last_updated"))

    lang_html = ""
    if lang:
        lc = lang_color(lang)
        lang_html = f'<span class="lang-dot" style="background:{lc}"></span> {escape(lang)}'

    rank_html = f'<td style="color:var(--text-dim)">{rank}</td>' if rank else ""

    return f"""
    <tr>
        {rank_html}
        <td class="name-cell"><a href="/servers/{slug}.html">{name}</a></td>
        <td class="desc-cell">{desc}</td>
        <td class="stars-cell">★ {stars}</td>
        <td class="lang-cell">{lang_html}</td>
        <td style="color:var(--text-dim)">{updated}</td>
    </tr>"""


# ─────────────────────────────────────────────
# Page Generators
# ─────────────────────────────────────────────

def build_home(servers, categories):
    total = len(servers)
    total_stars = sum(s.get("stars", 0) for s in servers)
    langs = len(set(s["language"] for s in servers if s.get("language")))
    top_servers = sorted(servers, key=lambda s: s.get("stars", 0), reverse=True)[:12]

    title = f"{SITE_NAME} — Discover {total}+ MCP Servers for AI Agents"
    desc = SITE_DESCRIPTION.format(total=total)

    # Category cards
    cat_cards = ""
    for cat_name, count in sorted(categories.items(), key=lambda x: -x[1]):
        meta = CATEGORY_META.get(cat_name, CATEGORY_META["Other"])
        cat_cards += f"""
        <a href="/category/{meta['slug']}.html" class="cat-card" style="--cat-color:{meta['color']}">
            <style>.cat-card[style*="{meta['color']}"]::before {{ background: {meta['color']}; }}</style>
            <span class="cat-icon">{meta['icon']}</span>
            <span class="cat-name">{escape(cat_name)}</span>
            <span class="cat-count">{count} servers</span>
        </a>"""

    # Featured server cards
    featured = ""
    for s in top_servers:
        featured += server_card_html(s)

    # Search index script
    search_script = """
<script src="https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.min.js"></script>
<script>
let fuse, searchData;
fetch('/search-index.json')
    .then(r => r.json())
    .then(data => {
        searchData = data;
        fuse = new Fuse(data, {
            keys: [{name: 'n', weight: 3}, {name: 'd', weight: 1}, {name: 'r', weight: 2}],
            threshold: 0.3,
            limit: 10
        });
    });

const input = document.getElementById('search-input');
const results = document.getElementById('search-results');

input.addEventListener('input', function() {
    const q = this.value.trim();
    if (q.length < 2 || !fuse) {
        results.classList.remove('active');
        return;
    }
    const hits = fuse.search(q, {limit: 8});
    if (hits.length === 0) {
        results.innerHTML = '<div style="padding:16px;color:var(--text-dim)">No servers found</div>';
        results.classList.add('active');
        return;
    }
    results.innerHTML = hits.map(h => {
        const s = h.item;
        return `<a href="/servers/${s.s}.html" class="search-result-item">
            <div>
                <div class="search-result-name">${s.n}</div>
                <div class="search-result-desc">${(s.d||'').substring(0,80)}</div>
            </div>
            <span class="search-result-meta">★ ${s.st} · ${s.l||''}</span>
        </a>`;
    }).join('');
    results.classList.add('active');
});

input.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        results.classList.remove('active');
        this.blur();
    }
});

document.addEventListener('click', function(e) {
    if (!e.target.closest('.search-wrap')) {
        results.classList.remove('active');
    }
});
</script>
"""

    html = html_head(title, desc, "/")
    html += html_header("home")
    html += f"""
<section class="hero">
    <div class="container hero-content">
        <div class="hero-badge"><span class="pulse"></span> Updated weekly &middot; {total:,} servers indexed</div>
        <h1>Find the right <span class="gradient">MCP server</span> in seconds</h1>
        <p>Stop scrolling through GitHub. Search {total:,}+ Model Context Protocol servers, organized by category, language, and popularity.</p>
        <div class="search-wrap">
            <span class="search-icon">&#128269;</span>
            <input type="text" id="search-input" placeholder="Search servers... e.g. postgres, slack, stripe, browser" autocomplete="off">
            <div id="search-results" class="search-results"></div>
        </div>
        <div class="search-chips">
            <span class="chips-label">Popular:</span>
            <a class="chip" onclick="document.getElementById('search-input').value='postgres';document.getElementById('search-input').dispatchEvent(new Event('input'));return false;" href="#">postgres</a>
            <a class="chip" onclick="document.getElementById('search-input').value='slack';document.getElementById('search-input').dispatchEvent(new Event('input'));return false;" href="#">slack</a>
            <a class="chip" onclick="document.getElementById('search-input').value='github';document.getElementById('search-input').dispatchEvent(new Event('input'));return false;" href="#">github</a>
            <a class="chip" onclick="document.getElementById('search-input').value='browser';document.getElementById('search-input').dispatchEvent(new Event('input'));return false;" href="#">browser</a>
            <a class="chip" onclick="document.getElementById('search-input').value='stripe';document.getElementById('search-input').dispatchEvent(new Event('input'));return false;" href="#">stripe</a>
            <a class="chip" onclick="document.getElementById('search-input').value='memory';document.getElementById('search-input').dispatchEvent(new Event('input'));return false;" href="#">memory</a>
            <a class="chip" onclick="document.getElementById('search-input').value='filesystem';document.getElementById('search-input').dispatchEvent(new Event('input'));return false;" href="#">filesystem</a>
        </div>
        <div class="hero-sub">
            <span><svg width="14" height="14" viewBox="0 0 24 24" fill="var(--yellow)" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg> {format_stars(total_stars)} total stars</span>
            <span><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--blue)" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg> {langs} languages</span>
            <span><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg> {len(categories)} categories</span>
            <span><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> Open source</span>
        </div>
    </div>
</section>

<section class="container">
    <div class="stats-bar">
        <div class="stat">
            <div class="stat-num">{total:,}</div>
            <div class="stat-label">Servers</div>
        </div>
        <div class="stat">
            <div class="stat-num">{len(categories)}</div>
            <div class="stat-label">Categories</div>
        </div>
        <div class="stat">
            <div class="stat-num">{langs}</div>
            <div class="stat-label">Languages</div>
        </div>
        <div class="stat">
            <div class="stat-num">{format_stars(total_stars)}</div>
            <div class="stat-label">Total Stars</div>
        </div>
    </div>
</section>

<section class="container">
    <h2 class="section-title">Browse by Category</h2>
    <p class="section-subtitle">{len(categories)} categories covering every use case from databases to AI agents</p>
    <div class="cat-grid">
        {cat_cards}
    </div>
</section>

<section class="container use-cases">
    <h2 class="section-title">What are you building?</h2>
    <p class="section-subtitle">Search by what you need, find the server that does it</p>
    <div class="use-case-grid">
        <a href="/category/database.html" class="use-case">
            <div class="use-case-scenario">Connecting to a database</div>
            <div class="use-case-query">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                postgres
            </div>
            <div class="use-case-result">Find <strong>75 database servers</strong> &mdash; PostgreSQL, MySQL, MongoDB, Redis, SQLite and more</div>
            <div class="use-case-arrow">Browse database servers &rarr;</div>
        </a>
        <a href="/category/browser-web.html" class="use-case">
            <div class="use-case-scenario">Scraping or automating the web</div>
            <div class="use-case-query">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                browser playwright
            </div>
            <div class="use-case-result">Find <strong>46 browser servers</strong> &mdash; Playwright, Puppeteer, Scrapling, headless Chrome</div>
            <div class="use-case-arrow">Browse web servers &rarr;</div>
        </a>
        <a href="/category/api-integration.html" class="use-case">
            <div class="use-case-scenario">Integrating a third-party API</div>
            <div class="use-case-query">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                slack stripe github
            </div>
            <div class="use-case-result">Find <strong>102 API servers</strong> &mdash; Slack, Stripe, GitHub, Notion, Jira, and dozens more</div>
            <div class="use-case-arrow">Browse API servers &rarr;</div>
        </a>
        <a href="/category/memory-knowledge.html" class="use-case">
            <div class="use-case-scenario">Adding memory to your agent</div>
            <div class="use-case-query">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                memory vector RAG
            </div>
            <div class="use-case-result">Find <strong>97 memory servers</strong> &mdash; vector stores, knowledge graphs, RAG pipelines, embeddings</div>
            <div class="use-case-arrow">Browse memory servers &rarr;</div>
        </a>
    </div>
</section>

<section class="container">
    <div class="lang-row">
        <span style="color:var(--text-dim);font-size:0.82rem;font-weight:500;padding:8px 0;">Filter by language:</span>
        <a href="/category/ai-llm.html" class="lang-pill"><span class="lang-dot" style="background:#3572A5"></span> Python <span style="color:var(--text-dim)">570</span></a>
        <a href="/category/code-dev-tools.html" class="lang-pill"><span class="lang-dot" style="background:#3178C6"></span> TypeScript <span style="color:var(--text-dim)">548</span></a>
        <a href="/category/api-integration.html" class="lang-pill"><span class="lang-dot" style="background:#F7DF1E"></span> JavaScript <span style="color:var(--text-dim)">121</span></a>
        <a href="/category/devops.html" class="lang-pill"><span class="lang-dot" style="background:#00ADD8"></span> Go <span style="color:var(--text-dim)">103</span></a>
        <a href="/category/security.html" class="lang-pill"><span class="lang-dot" style="background:#DEA584"></span> Rust <span style="color:var(--text-dim)">51</span></a>
    </div>
</section>

<section class="container">
    <h2 class="section-title" id="top-servers">Most Popular MCP Servers</h2>
    <p class="section-subtitle">Top servers by GitHub stars across all categories</p>
    <div class="server-grid">
        {featured}
    </div>
</section>
"""
    html += html_footer()
    # Insert search script before </body>
    html = html.replace("</body>", search_script + "</body>")
    return html


def build_categories_index(categories):
    title = f"MCP Server Categories — {SITE_NAME}"
    desc = f"Browse {len(categories)} categories of MCP servers. Find servers for databases, AI, security, DevOps, and more."

    cards = ""
    for cat_name, count in sorted(categories.items(), key=lambda x: -x[1]):
        meta = CATEGORY_META.get(cat_name, CATEGORY_META["Other"])
        cards += f"""
        <a href="/category/{meta['slug']}.html" class="cat-card">
            <span class="cat-icon">{meta['icon']}</span>
            <span class="cat-name">{escape(cat_name)}</span>
            <span class="cat-count">{count} servers</span>
        </a>"""

    html = html_head(title, desc, "/categories.html")
    html += html_header("categories")
    html += f"""
<div class="page-header">
    <div class="container">
        <h1>Categories</h1>
        <p>Browse MCP servers by category</p>
    </div>
</div>
<section class="container">
    <div class="cat-grid" style="margin-top:20px">
        {cards}
    </div>
</section>
"""
    html += html_footer()
    return html


def build_category_page(cat_name, cat_servers):
    meta = CATEGORY_META.get(cat_name, CATEGORY_META["Other"])
    sorted_servers = sorted(cat_servers, key=lambda s: s.get("stars", 0), reverse=True)
    count = len(sorted_servers)

    title = f"{cat_name} MCP Servers — {count} Model Context Protocol Servers | {SITE_NAME}"
    desc = meta["description"]

    rank_header = '<th>#</th>'
    rows = ""
    for i, s in enumerate(sorted_servers, 1):
        rows += server_row_html(s, rank=i)

    html = html_head(title, desc, f"/category/{meta['slug']}.html")
    html += html_header()
    html += f"""
<div class="page-header">
    <div class="container">
        <div class="breadcrumb"><a href="/">Home</a> / <a href="/categories.html">Categories</a> / {escape(cat_name)}</div>
        <h1>{meta['icon']} {escape(cat_name)} MCP Servers</h1>
        <p>{escape(desc)}</p>
    </div>
</div>
<section class="container">
    <p style="color:var(--text-dim);margin-bottom:24px">{count} servers · sorted by GitHub stars</p>
    <div style="overflow-x:auto">
    <table class="server-table">
        <thead>
            <tr>{rank_header}<th>Server</th><th>Description</th><th>Stars</th><th>Language</th><th>Updated</th></tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
    </div>
</section>
"""
    html += html_footer()
    return html


def build_server_page(server, related):
    slug = slugify(server["repo"].replace("/", "-"))
    name = server["name"]
    repo = server["repo"]
    desc = clean_github_emojis(server.get("description") or "An MCP server.")
    stars = server.get("stars", 0)
    lang = server.get("language", "")
    cat = server.get("category", "Other")
    cat_meta = CATEGORY_META.get(cat, CATEGORY_META["Other"])
    url = server.get("url", f"https://github.com/{repo}")
    readme = server.get("readme_excerpt", "")
    tools = server.get("tools", "")
    updated = time_ago(server.get("last_updated"))
    topics = [t.strip() for t in (server.get("topics") or "").split(",") if t.strip()]

    title = f"{name} — {cat} MCP Server | {SITE_NAME}"
    page_desc = f"{desc} — {stars:,} stars on GitHub. Browse on {SITE_NAME}."

    # Structured data
    structured = json.dumps({
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": name,
        "description": desc,
        "url": url,
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Any",
        "programmingLanguage": lang or "Unknown",
    }, indent=2)
    extra_head = f'<script type="application/ld+json">{structured}</script>'

    # Meta cards
    lang_html = ""
    if lang:
        lc = lang_color(lang)
        lang_html = f'<span class="lang-dot" style="background:{lc}"></span> {escape(lang)}'

    # README section
    readme_section = ""
    if readme:
        readme_section = f"""
    <div class="detail-section">
        <h2>README Excerpt</h2>
        <div class="detail-readme">{escape(readme)}</div>
    </div>"""

    # Tools section
    tools_section = ""
    if tools:
        tool_list = [t.strip() for t in tools.split(",") if t.strip()]
        tags = "".join(f'<span class="tool-tag">{escape(t)}</span>' for t in tool_list)
        tools_section = f"""
    <div class="detail-section">
        <h2>Tools ({len(tool_list)})</h2>
        <div class="detail-tools">{tags}</div>
    </div>"""

    # Topics
    topics_section = ""
    if topics:
        tags = "".join(f'<span class="tag">{escape(t)}</span>' for t in topics[:15])
        topics_section = f"""
    <div class="detail-section">
        <h2>Topics</h2>
        <div class="detail-tools">{tags}</div>
    </div>"""

    # Related servers
    related_html = ""
    if related:
        cards = ""
        for r in related[:4]:
            cards += server_card_html(r)
        related_html = f"""
    <div class="related-servers">
        <h2 class="section-title">Related {escape(cat)} Servers</h2>
        <div class="server-grid">{cards}</div>
    </div>"""

    html = html_head(title, page_desc, f"/servers/{slug}.html", extra_head)
    html += html_header()
    html += f"""
<div class="container server-detail">
    <div class="breadcrumb">
        <a href="/">Home</a> / <a href="/category/{cat_meta['slug']}.html">{escape(cat)}</a> / {escape(name)}
    </div>

    <div class="detail-header">
        <h1 class="detail-title">{escape(name)}</h1>
        <div class="detail-repo">{escape(repo)}</div>
    </div>

    <div class="detail-meta">
        <span class="meta-item">★ {stars:,} stars</span>
        <span class="meta-item">{lang_html or 'Unknown language'}</span>
        <span class="meta-item">{cat_meta['icon']} {escape(cat)}</span>
        <span class="meta-item">Updated {updated}</span>
    </div>

    <div class="detail-desc">{escape(desc)}</div>

    <a href="{escape(url)}" target="_blank" rel="noopener" class="btn">
        View on GitHub →
    </a>

    <div style="margin-top:40px">
        {readme_section}
        {tools_section}
        {topics_section}
    </div>

    {related_html}
</div>
"""
    html += html_footer()
    return html


def build_submit_page():
    title = f"Submit an MCP Server — {SITE_NAME}"
    desc = "Submit your MCP server to be listed on Protodex. We index Model Context Protocol servers for Claude, Cursor, and AI agents."

    html = html_head(title, desc, "/submit.html")
    html += html_header("submit")
    html += f"""
<div class="page-header">
    <div class="container">
        <h1>Submit Your MCP Server</h1>
        <p>Get your server listed on {SITE_NAME} and reach developers building with MCP.</p>
    </div>
</div>
<div class="container submit-content">
    <h2>How It Works</h2>
    <ol>
        <li>Your server must be a public GitHub repository</li>
        <li>It should implement the Model Context Protocol (MCP)</li>
        <li>Submit the GitHub URL below</li>
        <li>We'll review and add it within 7 days</li>
    </ol>

    <h2>Submit via GitHub Issue</h2>
    <p>The fastest way to submit your server:</p>
    <a href="https://github.com/LuciferForge/mcp-directory/issues/new?title=Add+server:+[your-repo-name]&body=Repository+URL:+%0A%0ACategory:+%0A%0ABrief+description:+" target="_blank" rel="noopener" class="btn">
        Submit on GitHub →
    </a>

    <div style="margin-top:40px">
        <h2>Already Listed?</h2>
        <p>If your server is already in our directory and you'd like to update its information, open an issue or pull request on our <a href="https://github.com/LuciferForge/mcp-directory" target="_blank" rel="noopener">GitHub repository</a>.</p>
    </div>
</div>
"""
    html += html_footer()
    return html


def build_sitemap(servers, categories):
    urls = [f"{SITE_URL}/"]
    urls.append(f"{SITE_URL}/categories.html")
    urls.append(f"{SITE_URL}/submit.html")

    for cat_name in categories:
        meta = CATEGORY_META.get(cat_name, CATEGORY_META["Other"])
        urls.append(f"{SITE_URL}/category/{meta['slug']}.html")

    for s in servers:
        slug = slugify(s["repo"].replace("/", "-"))
        urls.append(f"{SITE_URL}/servers/{slug}.html")

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml += f'  <url><loc>{escape(url)}</loc></url>\n'
    xml += '</urlset>'
    return xml


def build_search_index(servers):
    """Lightweight JSON for Fuse.js client-side search."""
    index = []
    for s in servers:
        slug = slugify(s["repo"].replace("/", "-"))
        index.append({
            "s": slug,  # slug
            "n": s["name"],  # name
            "r": s["repo"],  # repo
            "d": truncate(clean_github_emojis(s.get("description") or ""), 100),  # description
            "l": s.get("language", ""),  # language
            "c": s.get("category", ""),  # category
            "st": format_stars(s.get("stars", 0)),  # stars formatted
        })
    return json.dumps(index)


def build_robots():
    return f"""User-agent: *
Allow: /
Sitemap: {SITE_URL}/sitemap.xml
"""


# ─────────────────────────────────────────────
# Main Build
# ─────────────────────────────────────────────

def main():
    print(f"Loading data from {DATA_FILE}...")
    with open(DATA_FILE) as f:
        data = json.load(f)
    servers = data["servers"]
    print(f"Loaded {len(servers)} servers")

    # Group by category
    categories = {}
    for s in servers:
        cat = s.get("category", "Other")
        categories.setdefault(cat, []).append(s)
    cat_counts = {k: len(v) for k, v in categories.items()}

    # Create output directories
    os.makedirs(os.path.join(SITE_DIR, "servers"), exist_ok=True)
    os.makedirs(os.path.join(SITE_DIR, "category"), exist_ok=True)

    # Build home page
    print("Building home page...")
    write(os.path.join(SITE_DIR, "index.html"), build_home(servers, cat_counts))

    # Build categories index
    print("Building categories index...")
    write(os.path.join(SITE_DIR, "categories.html"), build_categories_index(cat_counts))

    # Build category pages
    print("Building category pages...")
    for cat_name, cat_servers in categories.items():
        meta = CATEGORY_META.get(cat_name, CATEGORY_META["Other"])
        write(
            os.path.join(SITE_DIR, "category", f"{meta['slug']}.html"),
            build_category_page(cat_name, cat_servers)
        )

    # Build individual server pages
    print("Building server pages...")
    seen_slugs = set()
    for s in servers:
        slug = slugify(s["repo"].replace("/", "-"))
        if slug in seen_slugs:
            slug = slug + "-" + str(s.get("id", 0))
        seen_slugs.add(slug)

        cat = s.get("category", "Other")
        related = [r for r in categories.get(cat, [])
                    if r["repo"] != s["repo"]]
        related = sorted(related, key=lambda x: x.get("stars", 0), reverse=True)[:4]

        write(
            os.path.join(SITE_DIR, "servers", f"{slug}.html"),
            build_server_page(s, related)
        )

    # Build submit page
    print("Building submit page...")
    write(os.path.join(SITE_DIR, "submit.html"), build_submit_page())

    # Build SEO assets
    print("Building SEO assets...")
    write(os.path.join(SITE_DIR, "sitemap.xml"), build_sitemap(servers, categories))
    write(os.path.join(SITE_DIR, "robots.txt"), build_robots())
    write(os.path.join(SITE_DIR, "search-index.json"), build_search_index(servers))

    # CNAME for custom domain
    write(os.path.join(SITE_DIR, "CNAME"), DOMAIN)

    # 404 page
    html_404 = html_head("Page Not Found — Protodex", "This page doesn't exist.", "/404.html")
    html_404 += html_header()
    html_404 += """
<div class="container" style="text-align:center;padding:80px 0">
    <h1 style="font-size:4rem;margin-bottom:16px">404</h1>
    <p style="color:var(--text-muted);margin-bottom:24px">This page doesn't exist.</p>
    <a href="/" class="btn">Back to Home</a>
</div>
"""
    html_404 += html_footer()
    write(os.path.join(SITE_DIR, "404.html"), html_404)

    print(f"\nDone! Generated site in {SITE_DIR}/")
    print(f"  - 1 home page")
    print(f"  - 1 categories index")
    print(f"  - {len(categories)} category pages")
    print(f"  - {len(seen_slugs)} server pages")
    print(f"  - sitemap.xml, robots.txt, search-index.json, CNAME, 404.html")
    print(f"\nTotal: {len(seen_slugs) + len(categories) + 5} files")


def write(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == "__main__":
    main()
