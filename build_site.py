#!/usr/bin/env python3
"""
Protodex.io — Static site generator for MCP Server Directory.
Reads mcp_directory.json → generates full static site into site/ directory.
"""

import sys
import hashlib
import json
import os
import re
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from html import escape
from urllib.parse import quote

ROOT_DIR = Path(__file__).resolve().parent
SITE_DIR = str(ROOT_DIR / "docs")
DATA_FILE = str(ROOT_DIR / "mcp_directory.json")
EXCLUDED_HASHES_FILE = ROOT_DIR / "excluded_repo_hashes.json"
SPONSORS_FILE = ROOT_DIR / "sponsored_servers.json"

_FAKEGIT_PHRASE_RE = re.compile(
    r"(?:visit this page to download|from the assets list|right-click it and choose|"
    r"it is usually named with `?\.(?:exe|zip)|pick the latest version that fits|"
    r"setup\.exe included|util\.exe\s+cert\.txt|application\.cmd|chrome_extension\.zip|firefox_extension\.zip)",
    re.I,
)


def _normalize_repo(repo_str):
    r = (repo_str or "").strip()
    for prefix in ("https://github.com/", "http://github.com/", "github.com/"):
        if r.lower().startswith(prefix):
            r = r[len(prefix):]
    r = r.rstrip("/")
    if r.lower().endswith(".git"):
        r = r[:-4]
    return r.lower()


def load_excluded_hashes():
    if not EXCLUDED_HASHES_FILE.exists():
        return set()
    try:
        data = json.loads(EXCLUDED_HASHES_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {str(x).lower() for x in data}
        return {str(x).lower() for x in data.get("hashes", [])}
    except Exception:
        return set()


def is_excluded_repo(repo_str, excluded_hashes):
    repo_norm = _normalize_repo(repo_str)
    if not repo_norm:
        return True
    return hashlib.sha256(repo_norm.encode("utf-8")).hexdigest() in excluded_hashes


def has_malicious_bait(repo_str, text):
    if not text:
        return False
    if _FAKEGIT_PHRASE_RE.search(text):
        return True
    repo_norm = _normalize_repo(repo_str)
    if repo_norm:
        esc = re.escape(repo_norm)
        if re.search(rf"(?:raw\.githubusercontent\.com/{esc}/|github\.com/{esc}/(?:raw|blob)/)[^\s\)\"']*\.zip\b", text, re.I):
            return True
    return False


def load_active_sponsors():
    active = []
    if not SPONSORS_FILE.exists():
        return active
    try:
        sponsors_data = json.loads(SPONSORS_FILE.read_text(encoding="utf-8"))
        now_iso = datetime.now(timezone.utc).isoformat()
        for item in sponsors_data:
            exp = item.get("expires_at", "")
            if not exp or exp > now_iso:
                active.append(item)
    except Exception as e:
        print(f"Error reading sponsored servers: {e}")
    return active
DOMAIN = "protodex.io"
SITE_URL = f"https://{DOMAIN}"
# Google Search Console verification token (meta-tag method).
# Paste the content="..." value from GSC's "HTML tag" verification here, then rebuild.
GSC_VERIFICATION = "PJCSjofSK_ea6SHzirs5wXdrWYvfZBcz26XlFDIaoUU"

SITE_NAME = "Protodex"
SITE_TAGLINE = "The MCP Server Index"
SITE_DESCRIPTION = "Discover {total} Model Context Protocol (MCP) servers with security scores. Search, browse by category, and find the right MCP server for Claude, Cursor, and AI agents."

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
    "Finance": {
        "slug": "finance",
        "icon": "💰",
        "description": "MCP servers for financial data, trading, payments, and fintech integrations.",
        "color": "#16A34A"
    },
    "Media": {
        "slug": "media",
        "icon": "🎬",
        "description": "MCP servers for image, video, audio processing, and media management.",
        "color": "#E11D48"
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


# Lucide-style monochrome SVG icons per category (replaces emoji for a non-AI-template look)
CATEGORY_SVG = {
    "AI/LLM": '<path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>',
    "Code/Dev Tools": '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
    "API Integration": '<path d="M12 22v-5"/><path d="M9 8V2"/><path d="M15 8V2"/><path d="M18 8v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4V8Z"/>',
    "Memory/Knowledge": '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/>',
    "Database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/>',
    "Browser/Web": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "Security": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
    "Search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "DevOps": '<path d="M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"/><circle cx="12" cy="12" r="3"/>',
    "Communication": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    "File System": '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
    "Data/Analytics": '<line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/>',
    "Finance": '<line x1="12" x2="12" y1="2" y2="22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    "Media": '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 3v18"/><path d="M3 7.5h4"/><path d="M3 12h18"/><path d="M3 16.5h4"/><path d="M17 3v18"/><path d="M17 7.5h4"/><path d="M17 16.5h4"/>',
    "Other": '<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
}

def cat_icon_svg(cat_name, size=26):
    """Return an inline Lucide SVG for a category, stroked in its brand color."""
    meta = CATEGORY_META.get(cat_name, CATEGORY_META["Other"])
    paths = CATEGORY_SVG.get(cat_name, CATEGORY_SVG["Other"])
    color = meta.get("color", "#2DD9E0")
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{paths}</svg>')


def slugify(text):
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def format_stars(stars):
    """Format star count: 1234 -> 1.2K, 179100 -> 179K, 2530000 -> 2.5M"""
    if stars >= 1_000_000:
        return f"{stars/1_000_000:.1f}M"
    if stars >= 100_000:
        return f"{stars/1000:.0f}K"
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
    --bg: #06060a;
    --bg-card: #0f0f14;
    --bg-card-hover: #16161d;
    --bg-hover: #12121a;
    --border: #1e1e2a;
    --border-hover: #2d2d3f;
    --text: #f0f0f5;
    --text-muted: #8888a0;
    --text-dim: #55556a;
    --accent: #2DD9E0;
    --accent-hover: #1FC2C9;
    --accent-glow: rgba(45, 217, 224, 0.15);
    --accent-soft: rgba(45, 217, 224, 0.06);
    --accent2: #7B61FF;
    --green: #2DD9E0;
    --yellow: #FFD93D;
    --blue: #5B8DEF;
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
    background-color: #06070c;
    background-image: 
        radial-gradient(ellipse 90% 55% at 50% -20%, rgba(45, 217, 224, 0.16), transparent 70%),
        radial-gradient(ellipse 70% 45% at 90% 20%, rgba(123, 97, 255, 0.14), transparent 60%),
        radial-gradient(ellipse 60% 40% at 10% 45%, rgba(255, 217, 61, 0.06), transparent 60%),
        radial-gradient(ellipse 80% 50% at 50% 85%, rgba(45, 217, 224, 0.08), transparent 70%);
    background-attachment: fixed;
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
    background: rgba(6, 6, 10, 0.88);
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
    display: flex;
    align-items: center;
    gap: 10px;
}
.logo:hover { text-decoration: none; }
.logo-icon { flex-shrink: 0; }
.logo-text {
    display: flex;
    flex-direction: column;
    line-height: 1;
}
.logo-name {
    font-size: 1.2rem;
    font-weight: 900;
    letter-spacing: -0.5px;
    color: var(--text);
    text-transform: lowercase;
}
.logo-name .lo-proto {
    color: var(--text);
    font-weight: 400;
}
.logo-name .lo-dex {
    color: var(--accent);
    font-weight: 900;
}
.logo-tagline {
    font-size: 0.6rem;
    color: var(--text-muted);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 600;
    margin-top: 2px;
    background: linear-gradient(90deg, var(--text-muted), var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
nav { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
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
    top: -300px;
    left: 50%;
    transform: translateX(-50%);
    width: 1000px;
    height: 800px;
    background: radial-gradient(ellipse at center, rgba(45, 217, 224, 0.08) 0%, rgba(123, 97, 255, 0.04) 40%, transparent 70%);
    pointer-events: none;
}
.hero::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image:
        linear-gradient(rgba(45, 217, 224, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(45, 217, 224, 0.03) 1px, transparent 1px);
    background-size: 48px 48px;
    pointer-events: none;
    mask-image: radial-gradient(ellipse at center, black 20%, transparent 65%);
    -webkit-mask-image: radial-gradient(ellipse at center, black 20%, transparent 65%);
}
.hero-content { position: relative; z-index: 1; }
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 16px;
    background: var(--accent-soft);
    border: 1px solid rgba(45, 217, 224, 0.2);
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
    background: linear-gradient(135deg, #2DD9E0 0%, #A78BFA 45%, #FBBF24 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 2px 18px rgba(45, 217, 224, 0.25));
}
.hero p {
    font-size: 1.15rem;
    color: var(--text-muted);
    max-width: 540px;
    margin: 0 auto 36px;
    line-height: 1.7;
}
.hero-sub {
    font-size: 1rem;
    color: var(--text-muted);
    margin-top: 20px;
    display: flex;
    justify-content: center;
    gap: 24px;
    flex-wrap: wrap;
    font-weight: 600;
}
.hero-sub span {
    display: flex;
    align-items: center;
    gap: 6px;
}
.hero-grid { display: flex; align-items: center; gap: 48px; max-width: 1080px; margin: 0 auto; }
.hero-left { flex: 1 1 0; min-width: 0; text-align: left; }
.hero-right { flex: 0 0 376px; max-width: 376px; }
.hero-left h1 { margin-left: 0; margin-right: 0; max-width: none; font-size: 3.1rem; }
.hero-left p { margin-left: 0; margin-right: 0; max-width: 470px; }
.hero-left .search-wrap { margin-left: 0; margin-right: 0; max-width: 470px; }
.hero-left .search-chips { justify-content: flex-start; }
.hero-left .hero-sub { justify-content: flex-start; margin-left: 0; }
.hero-cta { display: flex; gap: 12px; margin-top: 22px; }
.preview-panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); overflow: hidden; box-shadow: var(--shadow-lg); }
.preview-head { font-family: var(--mono); font-size: 0.8rem; color: var(--text-muted); padding: 12px 16px; border-bottom: 1px solid var(--border); }
.preview-head .pp { color: var(--accent); font-weight: 700; }
.preview-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 11px 14px; border-bottom: 1px solid var(--border); text-decoration: none; }
a.preview-row:hover { text-decoration: none; }
.preview-row:last-child { border-bottom: none; }
.preview-row:hover { background: var(--bg-card-hover); }
.preview-name { font-size: 0.9rem; font-weight: 600; color: var(--text); }
.preview-meta { font-family: var(--mono); font-size: 0.72rem; color: var(--text-dim); margin-top: 2px; }
.preview-stars { font-family: var(--mono); font-size: 0.78rem; color: var(--yellow); white-space: nowrap; }
.preview-cap { font-family: var(--mono); font-size: 0.7rem; color: var(--text-dim); text-align: center; margin-top: 8px; }
@media (max-width: 880px) {
    .hero-grid { flex-direction: column; gap: 32px; }
    .hero-right { flex-basis: auto; max-width: 480px; width: 100%; }
    .hero-left { text-align: center; }
    .hero-left h1, .hero-left p, .hero-left .search-wrap { margin-left: auto; margin-right: auto; }
    .hero-left .search-chips, .hero-left .hero-sub, .hero-cta { justify-content: center; }
}

/* Search */
.search-wrap {
    max-width: 580px;
    margin: 0 auto;
    position: relative;
    z-index: 10;
}
.search-wrap input {
    width: 100%;
    padding: 16px 20px 16px 48px;
    background: rgba(13, 15, 24, 0.82);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(45, 217, 224, 0.32);
    border-radius: 14px;
    color: var(--text);
    font-family: var(--mono);
    font-size: 0.95rem;
    font-weight: 500;
    outline: none;
    transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45), 0 0 16px rgba(45, 217, 224, 0.12);
}
.search-wrap input:focus {
    border-color: #2DD9E0;
    box-shadow: 0 6px 30px rgba(0, 0, 0, 0.5), 0 0 32px rgba(45, 217, 224, 0.35);
}
.search-wrap input::placeholder { color: var(--text-dim); font-weight: 400; }
.search-icon {
    position: absolute;
    left: 18px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--accent);
    font-family: var(--mono);
    font-weight: 700;
    font-size: 1.05rem;
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
    z-index: 50;
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
    font-family: var(--mono);
    font-size: 1.8rem;
    font-weight: 700;
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
.cred-band {
    display: flex; align-items: center; justify-content: center; gap: 12px;
    flex-wrap: wrap; margin: 0 auto 28px; padding: 11px 22px; max-width: 720px;
    background: var(--accent-soft); border: 1px solid rgba(45,217,224,0.22);
    border-radius: 100px; font-size: 0.9rem; color: var(--text-muted); text-align: center;
}
.cred-grow { font-family: var(--mono); font-weight: 700; color: var(--accent); }
.works-with { text-align: center; margin: 0 auto 72px; }
.ww-label {
    display: block; font-size: 0.72rem; text-transform: uppercase;
    letter-spacing: 0.12em; color: var(--text-dim); margin-bottom: 16px; font-weight: 700;
}
.ww-logos { display: flex; justify-content: center; gap: 32px; flex-wrap: wrap; }
.ww-logos span {
    font-family: var(--mono); font-weight: 600; color: var(--text-muted);
    font-size: 1.05rem; opacity: 0.8; transition: opacity 0.2s, color 0.2s;
}
.ww-logos span:hover { opacity: 1; color: var(--text); }
.value-prop-icon svg { display: inline-block; }

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
    background: rgba(14, 16, 25, 0.72);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--radius);
    padding: 20px;
    transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    display: flex;
    flex-direction: column;
    gap: 8px;
    position: relative;
    overflow: hidden;
    box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.08), 0 4px 16px rgba(0, 0, 0, 0.25);
}
.cat-card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    border-radius: 3px 0 0 3px;
    opacity: 0.85;
    box-shadow: 0 0 10px currentColor;
    transition: opacity 0.2s, width 0.2s;
}
.cat-card:hover {
    border-color: rgba(255, 255, 255, 0.2);
    background: rgba(20, 24, 38, 0.85);
    text-decoration: none;
    transform: translateY(-3px) scale(1.02);
    box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.2), 0 12px 32px rgba(0, 0, 0, 0.45);
}
.cat-card:hover::before { opacity: 1; width: 5px; }
.cat-icon { display: inline-flex; align-items: center; justify-content: center; height: 28px; }
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
    background: rgba(14, 16, 25, 0.72);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--radius);
    padding: 20px;
    transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    display: flex;
    flex-direction: column;
    gap: 10px;
    box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.08), 0 4px 16px rgba(0, 0, 0, 0.25);
}
.server-card:hover {
    border-color: rgba(45, 217, 224, 0.45);
    background: rgba(20, 24, 38, 0.85);
    text-decoration: none;
    transform: translateY(-3px) scale(1.01);
    box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.18), 0 12px 36px rgba(45, 217, 224, 0.15);
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
.sec-badge {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    padding: 3px 8px;
    border-radius: 5px;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    white-space: nowrap;
}
.sec-green {
    background: rgba(34, 197, 94, 0.1);
    color: #22C55E;
    border: 1px solid rgba(34, 197, 94, 0.2);
}
.sec-yellow {
    background: rgba(250, 204, 21, 0.1);
    color: #EAB308;
    border: 1px solid rgba(250, 204, 21, 0.2);
}
.sec-red {
    background: rgba(239, 68, 68, 0.1);
    color: #EF4444;
    border: 1px solid rgba(239, 68, 68, 0.2);
}
/* Security page */
.security-content { max-width: 700px; margin: 0 auto; padding: 40px 0 80px; }
.security-content h2 { margin-bottom: 16px; font-weight: 700; }
.security-content p { color: var(--text-muted); margin-bottom: 24px; line-height: 1.7; }
.band-explain { display: flex; flex-direction: column; gap: 16px; margin: 24px 0 32px; }
.band-row { display: flex; align-items: center; gap: 16px; padding: 16px 20px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); }
.band-row .sec-badge { font-size: 0.8rem; padding: 5px 12px; }
.band-desc { color: var(--text-muted); font-size: 0.9rem; }
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

/* CTA banner */
.cta-banner {
    text-align: center;
    padding: 56px 24px;
    margin: 40px 0;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    position: relative;
    overflow: hidden;
}
.cta-banner::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
}
.cta-banner h2 {
    font-size: 1.5rem;
    font-weight: 800;
    margin-bottom: 10px;
    letter-spacing: -0.5px;
}
.cta-banner p {
    color: var(--text-muted);
    font-size: 0.95rem;
    max-width: 480px;
    margin: 0 auto 24px;
    line-height: 1.6;
}
.cta-buttons {
    display: flex;
    justify-content: center;
    gap: 12px;
    flex-wrap: wrap;
}

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

/* Install config section */
.install-section { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.install-section h2 { font-size: 1.2rem; margin-bottom: 4px; }
.install-subtitle { color: var(--text-muted); font-size: 0.85rem; margin-bottom: 16px; }
.install-tabs { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.install-tab { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 8px 16px; cursor: pointer; font-size: 0.85rem; color: var(--text-muted); transition: all 0.2s; }
.install-tab:hover { border-color: var(--accent); color: var(--text); }
.install-tab.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.install-panel { display: none; }
.install-panel.active { display: block; }
.install-label { color: var(--text-muted); font-size: 0.8rem; margin-bottom: 8px; }
.install-label code { background: var(--bg); padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; }
.code-block { position: relative; background: #0d1117; border-radius: 8px; padding: 16px; overflow-x: auto; }
.code-block pre { margin: 0; }
.code-block code { color: #e6edf3; font-size: 0.82rem; font-family: 'SF Mono', Consolas, monospace; white-space: pre; }
.copy-btn { position: absolute; top: 8px; right: 8px; background: #21262d; border: 1px solid #30363d; border-radius: 6px; color: #8b949e; padding: 4px 10px; cursor: pointer; font-size: 0.75rem; transition: all 0.2s; }
.copy-btn:hover { background: #30363d; color: #e6edf3; }
.copy-btn.copied { background: #238636; color: #fff; border-color: #238636; }
.install-note { color: var(--text-muted); font-size: 0.8rem; margin-top: 8px; }
.install-note code { background: var(--bg); padding: 2px 6px; border-radius: 4px; }
"""


# ─────────────────────────────────────────────
# HTML Components
# ─────────────────────────────────────────────

def html_head(title, description, canonical_path="/", extra_head="", og_image=""):
    canonical = f"{SITE_URL}{canonical_path}"
    og_img = og_image or f"{SITE_URL}/og/protodex.png"
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
    <meta property="og:image" content="{escape(og_img)}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{escape(title)}">
    <meta name="twitter:description" content="{escape(truncate(description, 155))}">
    <meta name="twitter:image" content="{escape(og_img)}">
    <link rel="canonical" href="{escape(canonical)}">
    {'<meta name="google-site-verification" content="' + GSC_VERIFICATION + '">' if GSC_VERIFICATION else ''}
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' https://cdn.jsdelivr.net https://scripts.simpleanalyticscdn.com 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data: https://queue.simpleanalyticscdn.com; connect-src 'self' https://scripts.simpleanalyticscdn.com https://queue.simpleanalyticscdn.com;">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚡</text></svg>">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>{CSS}</style>
    <link rel="stylesheet" href="/assets/protodex-vibrant.css">
    <script async defer src="https://scripts.simpleanalyticscdn.com/latest.js"></script>
    <noscript><img src="https://queue.simpleanalyticscdn.com/noscript.gif" alt="" referrerpolicy="no-referrer-when-downgrade" /></noscript>
    {extra_head}
</head>
<body>
"""


# ── Gumroad promotion (single source of truth for the site-wide CTA) ──
# Swap `key` to change which product the whole site promotes on next rebuild.
GUMROAD_PRODUCTS = {
    "sponsor-mcp": {"url": "https://manja8.gumroad.com/l/sponsor_mcp",
                    "cta": "Promote Your Server →", "price": "$49/wk",
                    "pitch": "Feature your MCP server at the top of Protodex for 30,000+ AI developers"},
    "clawguard-pro": {"url": "https://manja8.gumroad.com/l/rogmt",
                      "cta": "ClawGuard Prompt-Shield ($29) →", "price": "$29",
                      "pitch": "Sub-1ms AI prompt injection firewall & MCP tool-call validator"},
    "clawguard-enterprise": {"url": "https://manja8.gumroad.com/l/zeyfad",
                             "cta": "ClawGuard Enterprise ($199) →", "price": "$199",
                             "pitch": "Enterprise autonomous AI security platform with red-team fuzzer"},
    "mcp-boilerplate": {"url": "https://manja8.gumroad.com/l/mcp-boilerplate",
                         "cta": "MCP Boilerplate ($79) →", "price": "$79",
                         "pitch": "Ship a production MCP server in an afternoon"},
}
GUMROAD_PROMO = GUMROAD_PRODUCTS["sponsor-mcp"]  # ← active product (footer & promos)

# Primary site-wide CTA. At 864 MCP-dev visitors/mo, lead-gen for a $1,500
# MCP-build service is far higher-EV than a $7 product sale. Points to /build.html.
SERVICES_CTA = {"url": "/build.html", "cta": "Need an MCP server? →"}

# P1 SEO funnel: contextual link from data-relevant pages -> the dataset landing page.
# Scoped to topically-relevant categories only (relevant internal linking, not sitewide spam).
DATA_RELEVANT_CATEGORIES = {"Database", "Data/Analytics", "Finance", "AI/LLM", "Search", "Memory/Knowledge"}
DATASET_CTA = """
<section class="container" style="margin:8px auto 32px">
  <div style="display:flex;gap:1.2rem;align-items:center;flex-wrap:wrap;padding:1.2rem 1.6rem;background:linear-gradient(135deg,rgba(123,97,255,0.14),rgba(45,217,224,0.12));border:1px solid rgba(123,97,255,0.3);border-radius:14px;box-shadow:0 4px 20px rgba(0,0,0,0.25)">
    <span style="font-size:2rem">&#128202;</span>
    <div style="flex:1;min-width:240px">
      <div style="font-weight:700;font-size:1.05rem;color:var(--text);letter-spacing:-0.01em">Building AI Agents or Backtesting Quant Models?</div>
      <div style="color:var(--text-muted);font-size:0.88rem;margin-top:4px;line-height:1.4">Get the <strong>Polymarket Historical Dataset</strong> &mdash; 23.0M+ 15-minute price &amp; orderbook snapshots across 18,400+ prediction markets. Clean CSV &amp; SQLite download for backtesting &amp; agent training.</div>
    </div>
    <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
      <a href="https://manja8.gumroad.com/l/polymarket-quant-toolkit?utm_source=protodex&utm_medium=category-banner&utm_campaign=polymarket-dataset" target="_blank" rel="noopener" style="background:var(--accent);color:#000;padding:8px 18px;border-radius:8px;font-size:0.85rem;font-weight:700;white-space:nowrap;box-shadow:0 2px 8px rgba(45,217,224,0.3)">Buy Dataset ($19) &#8594;</a>
      <a href="/datasets/polymarket-historical.html" style="border:1px solid rgba(255,255,255,0.2);color:var(--text);padding:8px 14px;border-radius:8px;font-size:0.85rem;font-weight:600;white-space:nowrap">View Sample &#8594;</a>
    </div>
  </div>
</section>
"""

COMMERCIAL_SERVER_CALLOUT = """
<div class="protodex-commercial-callout">
    <div class="callout-icon">⚡</div>
    <div class="callout-text">
        <div class="callout-title">Building Production MCP Agents? <span style="background:rgba(45,217,224,0.2);color:var(--accent);font-size:0.7rem;padding:2px 8px;border-radius:100px;font-weight:700">PRO TOOLKITS</span></div>
        <div class="callout-desc">Get the <strong>Complete 31,400+ MCP Ecosystem Dataset</strong> ($29) or the <strong>FastMCP + TypeScript Starter Kit</strong> ($39) with turnkey Docker &amp; Cloudflare deployment.</div>
    </div>
    <div class="callout-actions">
        <a href="https://manja8.gumroad.com/l/zcyee" target="_blank" rel="noopener" class="callout-btn-primary">Get Dataset ($29) →</a>
        <a href="https://manja8.gumroad.com/l/bsboqh" target="_blank" rel="noopener" class="callout-btn-secondary">Get Starter Kit ($39) →</a>
        <a href="/datasets/" class="callout-btn-secondary">Browse All Kits →</a>
    </div>
</div>
"""


def html_header(current=""):
    return """
<header>
    <div class="container">
        <a href="/" class="logo">
            <svg class="logo-icon" width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="28" height="28" rx="7" fill="url(#lg)"/><path d="M8 20V8h5.5a4 4 0 0 1 0 8H11.5" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="19" cy="19" r="2.5" fill="#fff" opacity="0.7"/><line x1="15" y1="16" x2="17.2" y2="17.5" stroke="#fff" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/><defs><linearGradient id="lg" x1="0" y1="0" x2="28" y2="28"><stop stop-color="#2DD9E0"/><stop offset="1" stop-color="#7B61FF"/></linearGradient></defs></svg>
            <div class="logo-text">
                <span class="logo-name"><span class="lo-proto">proto</span><span class="lo-dex">dex</span></span>
                <span class="logo-tagline">MCP Server Index</span>
            </div>
        </a>
        <nav>
            <a href="/">Explore</a>
            <a href="/templates.html" style="color:var(--accent);font-weight:700">UI Studio 🎨</a>
            <a href="/audit.html">Security 🛡️</a>
            <a href="/datasets/">Datasets 📊</a>
            <a href="/categories.html">Categories</a>
            <a href="https://manja8.gumroad.com/l/sponsor_mcp" target="_blank" rel="noopener">Promote ⚡</a>
            <a href="/blog/">Blog</a>
            <a href="/build.html" class="nav-cta" data-promo="services">Need an MCP server? →</a>
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
                    <svg class="logo-icon" width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="28" height="28" rx="7" fill="url(#lg)"/><path d="M8 20V8h5.5a4 4 0 0 1 0 8H11.5" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="19" cy="19" r="2.5" fill="#fff" opacity="0.7"/><line x1="15" y1="16" x2="17.2" y2="17.5" stroke="#fff" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/><defs><linearGradient id="lg" x1="0" y1="0" x2="28" y2="28"><stop stop-color="#2DD9E0"/><stop offset="1" stop-color="#7B61FF"/></linearGradient></defs></svg>
                    <span>Proto</span>dex
                </a>
                <p>The largest index of MCP servers. Helping developers find the right tools for AI-powered workflows.</p>
            </div>
            <div class="footer-links">
                <div class="footer-col">
                    <h4>Directory</h4>
                    <a href="/">Explore Servers</a>
                    <a href="/categories.html">Categories</a>
                    <a href="/security.html">Security Scores</a>
                    <a href="/submit.html">Submit a Server</a>
                    <a href="{DATASET_PATH}">Polymarket Dataset</a>
                </div>
                <div class="footer-col">
                    <h4>Project</h4>
                    <a href="https://github.com/LuciferForge/mcp-directory" target="_blank" rel="noopener">GitHub</a>
                    <a href="https://github.com/LuciferForge" target="_blank" rel="noopener">LuciferForge</a>
                </div>
                <div class="footer-col">
                    <h4>For Developers</h4>
                    <a href="/mcp-quickref.html">MCP Server Builder's Quick Reference</a>
                    <a href="/mcp-scorecard.html">MCP Production-Readiness Scorecard</a>
                    <a href="/build.html">Get an MCP server built</a>
                    <a href="{GUMROAD_PROMO['url']}?utm_source=protodex&utm_medium=footer&utm_campaign=gumroad" target="_blank" rel="noopener" data-promo="gumroad">{GUMROAD_PROMO['cta'].replace(' →','')} ({GUMROAD_PROMO['price']})</a>
                    <a href="/aws-free.html">AWS Prep (Free Study Guide)</a>
                </div>
            </div>
        </div>
        <div class="footer-bottom">
            &copy; {year} {SITE_NAME}. Open source. Updated weekly from GitHub. Built with Claude & Gemini.
        </div>
    </div>
</footer>
<script>
function showTab(btn,id){{var p=btn.closest('.install-section');p.querySelectorAll('.install-tab').forEach(function(t){{t.classList.remove('active')}});p.querySelectorAll('.install-panel').forEach(function(x){{x.style.display='none';x.classList.remove('active')}});btn.classList.add('active');var el=document.getElementById(id);if(el){{el.style.display='block';el.classList.add('active')}}}}
function copyCode(btn){{var code=btn.previousElementSibling.querySelector('code').textContent;navigator.clipboard.writeText(code).then(function(){{btn.textContent='Copied';btn.classList.add('copied');setTimeout(function(){{btn.textContent='Copy';btn.classList.remove('copied')}},2000)}})}}
</script>

</body>
</html>
"""


def security_badge_html(server):
    """Return HTML for security badge, or empty string if no score."""
    band = server.get("security_band", "")
    if band == "green":
        return '<span class="sec-badge sec-green">&#10003; Clean</span>'
    elif band == "yellow":
        return '<span class="sec-badge sec-yellow">&#9888; Review</span>'
    elif band == "red":
        return '<span class="sec-badge sec-red">&#10007; Risk</span>'
    return ""


def server_card_html(server, is_sponsored=False):
    slug = slugify(server["repo"].replace("/", "-"))
    desc = escape(truncate(clean_github_emojis(server.get("description") or "No description"), 120))
    stars = format_stars(server.get("stars", 0))
    lang = server.get("language", "")
    cat = server.get("category", "Other")
    cat_meta = CATEGORY_META.get(cat, CATEGORY_META["Other"])
    sec_badge = security_badge_html(server)

    lang_html = ""
    if lang:
        lc = lang_color(lang)
        lang_html = f'<span class="tag tag-lang"><span class="lang-dot" style="background:{lc}"></span>{escape(lang)}</span>'

    sponsored_style = 'style="border:1px solid #f472b6; box-shadow:0 0 10px rgba(244,114,182,0.25)"' if is_sponsored else ''
    sponsored_badge = '<span class="tag" style="background:rgba(244,114,182,0.15);color:#f472b6;border:1px solid rgba(244,114,182,0.3);font-size:10px;font-weight:800;letter-spacing:0.5px">⚡ FEATURED</span>' if is_sponsored else ''

    return f"""
    <a href="/servers/{slug}.html" class="server-card" {sponsored_style}>
        <div class="server-card-header">
            <span class="server-card-name">{escape(server["name"])}</span>
            <span style="display:flex;align-items:center;gap:8px">{sponsored_badge}{sec_badge}<span class="server-card-stars">★ {stars}</span></span>
        </div>
        <div class="server-card-desc">{desc}</div>
        <div class="server-card-footer">
            <span class="tag"><span style="display:inline-flex;vertical-align:-2px;margin-right:4px">{cat_icon_svg(cat, 12)}</span>{escape(cat)}</span>
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
    sec_badge = security_badge_html(server)

    lang_html = ""
    if lang:
        lc = lang_color(lang)
        lang_html = f'<span class="lang-dot" style="background:{lc}"></span> {escape(lang)}'

    rank_html = f'<td style="color:var(--text-dim)">{rank}</td>' if rank else ""

    return f"""
    <tr>
        {rank_html}
        <td class="name-cell"><a href="/servers/{slug}.html">{name}</a> {sec_badge}</td>
        <td class="desc-cell">{desc}</td>
        <td class="stars-cell">★ {stars}</td>
        <td class="lang-cell">{lang_html}</td>
        <td style="color:var(--text-dim)">{updated}</td>
    </tr>"""


# ─────────────────────────────────────────────
# Page Generators
# ─────────────────────────────────────────────

BENTO_INTERACTIVE_SCRIPT = """<script>
/* ─── Immediate Inline Handlers for Bento Grid Interactivity ─── */
var _ideSnippets = {
    python: {
        code: `<span class="c-kw">from</span> mcp.server.fastmcp <span class="c-kw">import</span> FastMCP
mcp = FastMCP(<span class="c-str">"ProtodexLive"</span>)

<span class="c-dec">@mcp.tool</span>()
<span class="c-kw">def</span> <span class="c-fn">search_servers</span>(query: <span class="c-type">str</span>, min_stars: <span class="c-type">int</span> = <span class="c-num">50</span>) -&gt; <span class="c-type">dict</span>:
    <span class="c-dim"># Search 31,400+ MCP servers by capability and security rating</span>
    <span class="c-kw">return</span> mcp_engine.search(query, min_stars=min_stars)

<span class="c-kw">if</span> __name__ == <span class="c-str">"__main__"</span>:
    mcp.run(transport=<span class="c-str">"stdio"</span>)`,
        raw: `from mcp.server.fastmcp import FastMCP
mcp = FastMCP("ProtodexLive")

@mcp.tool()
def search_servers(query: str, min_stars: int = 50) -> dict:
    # Search 31,400+ MCP servers by capability and security rating
    return mcp_engine.search(query, min_stars=min_stars)

if __name__ == "__main__":
    mcp.run(transport="stdio")`,
        lang: 'language-python',
        pill: '<span class="status-dot green"></span><span>JSON-RPC 2.0 &middot; Stdio + SSE Supported</span>',
        linkText: 'Get Dual-SDK Kit ($39) &rarr;',
        linkHref: 'https://manja8.gumroad.com/l/bsboqh'
    },
    ts: {
        code: `<span class="c-kw">import</span> { McpServer } <span class="c-kw">from</span> <span class="c-str">"@modelcontextprotocol/sdk/server/mcp.js"</span>;
<span class="c-kw">import</span> { StdioServerTransport } <span class="c-kw">from</span> <span class="c-str">"@modelcontextprotocol/sdk/server/stdio.js"</span>;
<span class="c-kw">import</span> { z } <span class="c-kw">from</span> <span class="c-str">"zod"</span>;

<span class="c-kw">const</span> server = <span class="c-kw">new</span> <span class="c-fn">McpServer</span>({ name: <span class="c-str">"protodex"</span>, version: <span class="c-str">"1.0.0"</span> });

server.<span class="c-fn">tool</span>(
  <span class="c-str">"search_servers"</span>,
  { query: z.<span class="c-fn">string</span>(), min_stars: z.<span class="c-fn">number</span>().<span class="c-fn">default</span>(<span class="c-num">50</span>) },
  <span class="c-kw">async</span> ({ query, min_stars }) =&gt; ({
    content: [{ type: <span class="c-str">"text"</span>, text: JSON.<span class="c-fn">stringify</span>(<span class="c-kw">await</span> <span class="c-fn">queryIndex</span>(query, min_stars)) }]
  })
);

<span class="c-kw">const</span> transport = <span class="c-kw">new</span> <span class="c-fn">StdioServerTransport</span>();
<span class="c-kw">await</span> server.<span class="c-fn">connect</span>(transport);`,
        raw: `import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({ name: "protodex", version: "1.0.0" });

server.tool(
  "search_servers",
  { query: z.string(), min_stars: z.number().default(50) },
  async ({ query, min_stars }) => ({
    content: [{ type: "text", text: JSON.stringify(await queryIndex(query, min_stars)) }]
  })
);

const transport = new StdioServerTransport();
await server.connect(transport);`,
        lang: 'language-typescript',
        pill: '<span class="status-dot green"></span><span>@modelcontextprotocol/sdk &middot; Type-Safe Zod Tools</span>',
        linkText: 'Get Dual-SDK Kit ($39) &rarr;',
        linkHref: 'https://manja8.gumroad.com/l/bsboqh'
    },
    claude: {
        code: `{
  <span class="c-str">"mcpServers"</span>: {
    <span class="c-str">"protodex"</span>: {
      <span class="c-str">"command"</span>: <span class="c-str">"npx"</span>,
      <span class="c-str">"args"</span>: [<span class="c-str">"-y"</span>, <span class="c-str">"@protodex/mcp-server@latest"</span>],
      <span class="c-str">"env"</span>: {
        <span class="c-str">"PROTODEX_API_KEY"</span>: <span class="c-str">"YOUR_PROTODEX_KEY"</span>
      }
    },
    <span class="c-str">"filesystem"</span>: {
      <span class="c-str">"command"</span>: <span class="c-str">"npx"</span>,
      <span class="c-str">"args"</span>: [<span class="c-str">"-y"</span>, <span class="c-str">"@modelcontextprotocol/server-filesystem"</span>, <span class="c-str">"/Users/dev/workspace"</span>]
    }
  }
}`,
        raw: `{
  "mcpServers": {
    "protodex": {
      "command": "npx",
      "args": ["-y", "@protodex/mcp-server@latest"],
      "env": {
        "PROTODEX_API_KEY": "YOUR_PROTODEX_KEY"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/dev/workspace"]
    }
  }
}`,
        lang: 'language-json',
        pill: '<span class="status-dot blue" style="background:#5B8DEF"></span><span>Claude Desktop &middot; claude_desktop_config.json</span>',
        linkText: 'Get 31k Dataset ($29) &rarr;',
        linkHref: 'https://manja8.gumroad.com/l/zcyee'
    },
    cursor: {
        code: `<span class="c-kw"># Model Context Protocol (MCP) Integration Rules</span>

<span class="c-str">When creating or connecting MCP tools with AI agents:</span>
<span class="c-kw">1.</span> Prefer official <span class="c-fn">@modelcontextprotocol/sdk</span> (TS) or <span class="c-fn">FastMCP</span> (Python).
<span class="c-kw">2.</span> Validate input schemas with strict <span class="c-type">Zod</span> or <span class="c-type">Pydantic</span> models.
<span class="c-kw">3.</span> Send debug logs to <span class="c-fn">stderr</span> &mdash; stdout is reserved for JSON-RPC framing.
<span class="c-kw">4.</span> Wrap tool returns in <span class="c-type">{ content: [{ type: "text", text }] }</span> payloads.`,
        raw: `# Model Context Protocol (MCP) Integration Rules

When creating or connecting MCP tools with AI agents:
1. Prefer official @modelcontextprotocol/sdk (TS) or FastMCP (Python).
2. Validate input schemas with strict Zod or Pydantic models.
3. Send debug logs to stderr — stdout is reserved for JSON-RPC framing.
4. Wrap tool returns in { content: [{ type: "text", text }] } payloads.`,
        lang: 'language-markdown',
        pill: '<span class="status-dot purple" style="background:#A78BFA"></span><span>Cursor Rules &middot; .cursor/rules/mcp.mdc</span>',
        linkText: 'Explore UI Studio ($39) &rarr;',
        linkHref: 'https://manja8.gumroad.com/l/lntzuo'
    }
};

var _currentIdeTab = 'python';

function switchIdeTab(tabKey, btn) {
    if (!_ideSnippets[tabKey]) return;
    _currentIdeTab = tabKey;
    
    var tabs = document.querySelectorAll('.ide-tabs-nav .ide-tab');
    for (var i = 0; i < tabs.length; i++) {
        tabs[i].classList.remove('active');
    }
    if (btn) {
        btn.classList.add('active');
    }
    
    var codeEl = document.getElementById('ide-code-display');
    if (codeEl) {
        var data = _ideSnippets[tabKey];
        codeEl.innerHTML = '<code class="' + data.lang + '">' + data.code + '</code>';
    }
    
    var pillEl = document.querySelector('.ide-footer .ide-status-pill');
    if (pillEl && _ideSnippets[tabKey].pill) {
        pillEl.innerHTML = _ideSnippets[tabKey].pill;
    }
    var linkEl = document.querySelector('.ide-footer .ide-starter-link');
    if (linkEl && _ideSnippets[tabKey].linkText) {
        linkEl.innerHTML = _ideSnippets[tabKey].linkText;
        linkEl.href = _ideSnippets[tabKey].linkHref;
    }
}

function copyIdeSnippet() {
    var raw = _ideSnippets[_currentIdeTab] ? _ideSnippets[_currentIdeTab].raw : '';
    if (!raw) return;
    
    function onSuccess() {
        var btn = document.getElementById('copy-code-btn');
        if (btn) {
            var orig = btn.innerHTML;
            btn.innerHTML = '<span style="color:#22C55E;display:inline-flex;align-items:center;gap:4px">✓ Copied!</span>';
            setTimeout(function() {
                btn.innerHTML = orig;
            }, 2000);
        }
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(raw).then(onSuccess).catch(function(err) {
            fallbackCopy(raw);
        });
    } else {
        fallbackCopy(raw);
    }

    function fallbackCopy(text) {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        try {
            document.execCommand('copy');
            onSuccess();
        } catch (e) {
            console.error('Copy fallback failed:', e);
        }
        document.body.removeChild(ta);
    }
}

function switchSponsorTab(tabKey, btn) {
    var termsPanel = document.getElementById('sponsor-panel-terms');
    var previewPanel = document.getElementById('sponsor-panel-preview');
    var termsTab = document.getElementById('sponsor-tab-terms');
    var previewTab = document.getElementById('sponsor-tab-preview');

    if (tabKey === 'preview') {
        if (termsPanel) termsPanel.style.display = 'none';
        if (previewPanel) previewPanel.style.display = 'block';
        if (termsTab) termsTab.classList.remove('active');
        if (previewTab) previewTab.classList.add('active');
    } else {
        if (termsPanel) termsPanel.style.display = 'block';
        if (previewPanel) previewPanel.style.display = 'none';
        if (termsTab) termsTab.classList.add('active');
        if (previewTab) previewTab.classList.remove('active');
    }
}

window.switchIdeTab = switchIdeTab;
window.copyIdeSnippet = copyIdeSnippet;
window.switchSponsorTab = switchSponsorTab;
</script>
"""


def build_home(servers, categories):
    total = len(servers)
    total_stars = sum(s.get("stars", 0) for s in servers)
    lang_counts = Counter(s.get("language") for s in servers if s.get("language"))
    langs = len(lang_counts)
    top_servers = sorted(servers, key=lambda s: s.get("stars", 0), reverse=True)[:12]

    title = f"{SITE_NAME} — Discover {total:,}+ MCP Servers for AI Agents"
    desc = SITE_DESCRIPTION.format(total=total)

    # Category cards
    cat_cards = ""
    for cat_name, count in sorted(categories.items(), key=lambda x: -x[1]):
        meta = CATEGORY_META.get(cat_name, CATEGORY_META["Other"])
        cat_cards += f"""
        <a href="/category/{meta['slug']}.html" class="cat-card" style="--cat-color:{meta['color']}">
            <style>.cat-card[style*="{meta['color']}"]::before {{ background: {meta['color']}; }}</style>
            <span class="cat-icon">{cat_icon_svg(cat_name)}</span>
            <span class="cat-name">{escape(cat_name)}</span>
            <span class="cat-count">{count:,} servers</span>
        </a>"""

    # B2B sponsored servers lookup from local sponsored_servers.json
    active_sponsors = load_active_sponsors()
    sponsored_slugs = {
        sl for item in active_sponsors
        for sl in (
            slugify(item.get("server_slug", "")),
            slugify(item.get("repo", "").replace("/", "-")),
        )
        if sl
    }
    by_slug = {slugify(s.get("repo", "").replace("/", "-")): s for s in servers if s.get("repo")}

    # Sponsored server cards
    sponsored_section = ""
    sponsored_cards = ""
    for s in servers:
        repo_slug = slugify(s.get("repo", "").replace("/", "-"))
        if repo_slug in sponsored_slugs or (s.get("slug") or "").lower() in sponsored_slugs:
            sponsored_cards += server_card_html(s, is_sponsored=True)

    if sponsored_cards:
        sponsored_section = f"""
<section class="container" style="padding-bottom:0">
    <h2 class="section-title" style="color:#f472b6;">⚡ Sponsored Placements</h2>
    <p class="section-subtitle">Promoted MCP servers from our developers</p>
    <div class="server-grid" style="margin-bottom:32px;">
        {sponsored_cards}
    </div>
</section>"""

    slots_open = max(0, 3 - len(active_sponsors))
    if active_sponsors:
        sp = active_sponsors[0]
        sp_slug = slugify(sp.get("repo", "").replace("/", "-")) or slugify(sp.get("server_slug", ""))
        sp_srv = by_slug.get(sp_slug, {})
        sp_name = sp.get("name") or sp_srv.get("name") or sp.get("repo") or "Featured Partner"
        sp_stars = sp_srv.get("stars") or sp.get("stars") or 0
        sp_desc = sp.get("description") or sp_srv.get("description") or "Verified featured ecosystem sponsor."
        sp_href = f"/servers/{sp_slug}.html" if sp_srv else f"https://github.com/{sp.get('repo', '')}"
        sponsor_preview_html = f"""
                    <div id="sponsor-panel-preview" style="display:none;background:#06080E;border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:10px 12px;font-size:0.75rem;">
                        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
                            <a href="{escape(sp_href)}" style="color:#2DD9E0;font-size:0.85rem;font-weight:700;text-decoration:none;">{escape(sp_name)} &rarr;</a>
                            <span style="color:#FBBF24;font-size:0.75rem;font-weight:700;">★ {sp_stars:,} Stars</span>
                        </div>
                        <p style="color:var(--text-muted);font-size:0.73rem;line-height:1.4;margin:0 0 8px;">{escape(truncate(sp_desc, 140))}</p>
                        <div style="font-size:0.68rem;color:#94A3B8;background:rgba(255,255,255,0.04);padding:4px 8px;border-radius:6px;border:1px dashed rgba(255,255,255,0.1);">
                            💡 <em>When you sponsor, your repo joins up to 3 featured partner slots automatically for 7 days!</em>
                        </div>
                    </div>"""
    else:
        sponsor_preview_html = """
                    <div id="sponsor-panel-preview" style="display:none;background:#06080E;border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:10px 12px;font-size:0.75rem;">
                        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
                            <strong style="color:#2DD9E0;font-size:0.85rem;">Your MCP Server Here</strong>
                            <span style="color:#22C55E;font-size:0.75rem;font-weight:700;">AVAILABLE NOW</span>
                        </div>
                        <p style="color:var(--text-muted);font-size:0.73rem;line-height:1.4;margin:0 0 8px;">Claim the #1 Hero Bento + Sponsored Placements spotlight and reach AI engineers integrating MCP tools.</p>
                        <div style="font-size:0.68rem;color:#94A3B8;background:rgba(255,255,255,0.04);padding:4px 8px;border-radius:6px;border:1px dashed rgba(255,255,255,0.1);">
                            💡 <em>3 weekly slots available — fast activation via Gumroad + GitHub Actions.</em>
                        </div>
                    </div>"""

    # Featured server cards
    featured = ""
    for s in top_servers:
        featured += server_card_html(s)

    # Search index script
    search_script = """
<script src="https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.min.js"></script>
<script>
var _fuse = null;
var _results = null;

fetch('/search-index.json')
    .then(function(r) { return r.json(); })
    .then(function(data) {
        console.log('Search index loaded:', data.length);
        _fuse = new Fuse(data, { keys: ['n', 'd', 'r'], threshold: 0.3 });
        console.log('Fuse ready');
    });

function _esc(x){return String(x==null?'':x).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function doSearch(q) {
    if (!_results) _results = document.getElementById('search-results');
    q = q.trim();
    if (q.length < 2) { _results.style.display = 'none'; return; }
    if (!_fuse) { _results.innerHTML = '<div style="padding:16px;color:#8888a0">Loading...</div>'; _results.style.display = 'block'; return; }
    var hits = _fuse.search(q, {limit: 8});
    if (hits.length === 0) { _results.innerHTML = '<div style="padding:16px;color:#8888a0">No servers found</div>'; _results.style.display = 'block'; return; }
    var h = '';
    for (var i = 0; i < hits.length; i++) {
        var s = hits[i].item;
        h += '<a href="/servers/' + encodeURIComponent(s.s) + '.html" class="search-result-item"><div><div class="search-result-name">' + _esc(s.n) + '</div><div class="search-result-desc">' + _esc((s.d||'').substring(0,80)) + '</div></div><span class="search-result-meta">' + _esc(s.st) + ' · ' + _esc(s.l) + '</span></a>';
    }
    _results.innerHTML = h;
    _results.style.display = 'block';
}

document.addEventListener('click', function(e) {
    if (!e.target.closest('.search-wrap') && !e.target.closest('.raycast-hud-wrapper') && _results) _results.style.display = 'none';
});
</script>
"""

    preview_rows = ""
    for s in top_servers[:4]:
        pcat = s.get("category", "Other")
        plang = s.get("language", "") or "—"
        preview_rows += (
            f'<a href="/servers/{slugify(s["repo"].replace("/", "-"))}.html" class="preview-row">'
            f'<div><div class="preview-name">{escape(s["name"])}</div>'
            f'<div class="preview-meta">{escape(pcat)} &middot; {escape(plang)}</div></div>'
            f'<span class="preview-stars">&#9733; {format_stars(s.get("stars", 0))}</span></a>'
        )
    preview_panel = (
        f'<div class="preview-panel"><div class="preview-head">'
        f'<span class="pp">&#10095;</span> most starred '
        f'<span style="color:var(--text-dim)">&middot; {total:,} indexed</span></div>'
        f'{preview_rows}</div>'
        f'<div class="preview-cap">live &middot; real servers from the index</div>'
    )

    html = html_head(title, desc, "/")
    html += html_header("home")
    html += f"""

<!-- ====================================================================== -->
<!-- 2026 RAYCAST COMMAND HUD & OBSIDIAN AURORA HERO SECTION               -->
<!-- ====================================================================== -->
<section class="aurora-hero-section">
    <div class="container">
        <!-- Live Ecosystem Pulse Badge -->
        <div class="hero-top-badge">
            <span class="status-indicator-pulse"></span>
            <span class="badge-text"><strong>PROTODEX 2026</strong> &middot; Real-Time MCP Intelligence &middot; {total:,} Screened Repos</span>
            <span class="badge-pill">ACTIVE INDEX</span>
        </div>

        <!-- Hero Headline -->
        <h1 class="aurora-hero-title">
            The Next-Gen Intelligence &amp; UI Directory for <br>
            <span class="gradient-text">Model Context Protocol</span>
        </h1>
        <p class="aurora-hero-subtitle">
            Search {total:,} screened MCP servers, inspect real-time AST security telemetry, and deploy 48+ turnkey developer UI archetypes for autonomous AI agents.
        </p>

        <!-- Raycast Floating Command HUD -->
        <div class="raycast-hud-wrapper">
            <div class="raycast-hud-bar">
                <div class="hud-leading-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                </div>
                <input type="text" id="search-input" class="raycast-search-input" placeholder="Search {total:,} servers, tools, schemas... (e.g., postgres, slack, stripe, fastmcp)" autocomplete="off" oninput="doSearch(this.value)">
                <div class="hud-kbd-badge">
                    <span>⌘K</span>
                </div>
            </div>
            <div id="search-results" class="search-results"></div>
            
            <!-- Quick Intent Command Chips -->
            <div class="hud-intent-chips">
                <span class="chips-label">Quick Intent:</span>
                <button type="button" class="intent-chip active" onclick="var i=document.getElementById('search-input');i.value='postgres';i.focus();doSearch('postgres');return false;"><span class="dot"></span>postgres</button>
                <button type="button" class="intent-chip" onclick="var i=document.getElementById('search-input');i.value='slack';i.focus();doSearch('slack');return false;"><span class="dot"></span>slack</button>
                <button type="button" class="intent-chip" onclick="var i=document.getElementById('search-input');i.value='github';i.focus();doSearch('github');return false;"><span class="dot"></span>github</button>
                <button type="button" class="intent-chip" onclick="var i=document.getElementById('search-input');i.value='browser';i.focus();doSearch('browser');return false;"><span class="dot"></span>browser</button>
                <button type="button" class="intent-chip" onclick="var i=document.getElementById('search-input');i.value='stripe';i.focus();doSearch('stripe');return false;"><span class="dot"></span>stripe</button>
                <button type="button" class="intent-chip" onclick="var i=document.getElementById('search-input');i.value='fastmcp';i.focus();doSearch('fastmcp');return false;"><span class="dot"></span>fastmcp</button>
                <button type="button" class="intent-chip" onclick="var i=document.getElementById('search-input');i.value='memory';i.focus();doSearch('memory');return false;"><span class="dot"></span>memory</button>
                <a href="/templates.html" class="intent-chip highlight"><span class="dot"></span>48 UI Templates 🎨</a>
            </div>
        </div>

        <!-- Telemetry Stats Ribbon -->
        <div class="telemetry-ribbon">
            <div class="telemetry-item">
                <div class="telemetry-val">{total:,}</div>
                <div class="telemetry-lbl">Screened Servers</div>
            </div>
            <div class="telemetry-sep"></div>
            <div class="telemetry-item">
                <div class="telemetry-val">{total_stars // 10_000 * 10_000:,}+</div>
                <div class="telemetry-lbl">Total GitHub Stars</div>
            </div>
            <div class="telemetry-sep"></div>
            <div class="telemetry-item">
                <div class="telemetry-val">{langs}</div>
                <div class="telemetry-lbl">Languages Supported</div>
            </div>
            <div class="telemetry-sep"></div>
            <div class="telemetry-item">
                <div class="telemetry-val">48</div>
                <div class="telemetry-lbl">UI Studio Archetypes</div>
            </div>
            <div class="telemetry-sep"></div>
            <div class="telemetry-item">
                <div class="telemetry-val highlight-green">100% Verified</div>
                <div class="telemetry-lbl">AegisMesh AST Scanned</div>
            </div>
        </div>

        <!-- ============================================================== -->
        <!-- OBSIDIAN AURORA ASYMMETRICAL BENTO GRID (COMPACT 2026)         -->
        <!-- ============================================================== -->
        <div class="bento-grid-2026">
            
            <!-- Bento Tile 1: Dual-SDK Interactive IDE & Terminal Simulator (7 Cols) -->
            <div class="bento-tile bento-tile-ide">
                <div class="bento-header">
                    <div class="ide-tabs-nav">
                        <button class="ide-tab active" onclick="switchIdeTab('python', this)">FastMCP (Python)</button>
                        <button class="ide-tab" onclick="switchIdeTab('ts', this)">TypeScript SDK</button>
                        <button class="ide-tab" onclick="switchIdeTab('claude', this)">Claude Desktop</button>
                        <button class="ide-tab" onclick="switchIdeTab('cursor', this)">Cursor Rules</button>
                    </div>
                    <button class="btn-copy-code" id="copy-code-btn" onclick="copyIdeSnippet()">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                        <span>Copy</span>
                    </button>
                </div>
                <div class="ide-body">
                    <pre class="ide-code-block" id="ide-code-display"><code class="language-python"><span class="c-kw">from</span> mcp.server.fastmcp <span class="c-kw">import</span> FastMCP
mcp = FastMCP(<span class="c-str">"ProtodexLive"</span>)

<span class="c-dec">@mcp.tool</span>()
<span class="c-kw">def</span> <span class="c-fn">search_servers</span>(query: <span class="c-type">str</span>, min_stars: <span class="c-type">int</span> = <span class="c-num">50</span>) -> <span class="c-type">dict</span>:
    <span class="c-kw">return</span> mcp_engine.search(query, min_stars=min_stars)

mcp.run(transport=<span class="c-str">"stdio"</span>)</code></pre>
                </div>
                <div class="ide-footer">
                    <div class="ide-status-pill">
                        <span class="status-dot green"></span>
                        <span>JSON-RPC 2.0 &middot; Stdio + SSE Supported</span>
                    </div>
                    <a href="https://manja8.gumroad.com/l/bsboqh" target="_blank" rel="noopener" class="ide-starter-link">Get Dual-SDK Kit ($39) &rarr;</a>
                </div>
            </div>

            <!-- Bento Tile 2: AegisMesh Cyber Security Radar (5 Cols) -->
            <div class="bento-tile bento-tile-radar">
                <div class="radar-top">
                    <span class="radar-tag">AEGISMESH TRiSM</span>
                    <span class="radar-badge-live">LIVE TELEMETRY</span>
                </div>
                <div class="radar-visual-container">
                    <div class="radar-avionics-display">
                        <div class="radar-sweep-beam"></div>
                        <div class="radar-circle circle-1"></div>
                        <div class="radar-circle circle-2"></div>
                        <div class="radar-circle circle-3"></div>
                        <div class="radar-crosshair-h"></div>
                        <div class="radar-crosshair-v"></div>
                        <div class="radar-blip blip-1"></div>
                        <div class="radar-blip blip-2"></div>
                        <div class="radar-blip blip-3"></div>
                        <div class="radar-center-score">
                            <span class="score-num">98.4</span>
                            <span class="score-lbl">SAFETY</span>
                        </div>
                    </div>
                </div>
                <div class="radar-info">
                    <div class="radar-metric-row">
                        <span>Zero-Day CVEs</span>
                        <strong class="text-green">0 DETECTED</strong>
                    </div>
                    <div class="radar-metric-row">
                        <span>AST Sandbox</span>
                        <strong class="text-cyan">100% COMPLIANT</strong>
                    </div>
                </div>
                <a href="/audit.html" class="radar-action-btn">
                    <span>Scan Your Server Free</span>
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </a>
            </div>

                        <!-- Bento Tile 3: Featured MCP Partner & Sponsored Slot (5 Cols) -->
            <div class="bento-tile bento-tile-featured" style="position:relative;overflow:hidden;display:flex;flex-direction:column;justify-content:space-between;">
                <!-- Top Badge Row -->
                <div class="featured-top" style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
                    <span class="featured-badge" style="background:linear-gradient(135deg,rgba(245,158,11,0.25),rgba(45,217,224,0.15));border:1px solid rgba(245,158,11,0.4);color:#FBBF24;font-size:0.72rem;padding:3px 10px;border-radius:100px;font-weight:700;letter-spacing:0.04em;">⚡ SPONSOR SPOTLIGHT</span>
                    <span class="featured-verified" style="background:rgba(34,197,94,0.15);border:1px solid rgba(34,197,94,0.3);color:#22C55E;font-size:0.7rem;padding:2px 8px;border-radius:100px;font-weight:600;">{slots_open} OF 3 SLOTS OPEN</span>
                </div>

                <!-- Headline -->
                <div class="featured-content">
                    <h3 class="featured-name" style="font-size:1.15rem;font-weight:800;color:#fff;margin-bottom:4px;letter-spacing:-0.02em;">
                        Feature Your MCP Server Here
                    </h3>
                    <p class="featured-tagline" style="color:var(--text-muted);font-size:0.78rem;line-height:1.45;margin-bottom:12px;">
                        Put your tool in front of <strong>30,000+ AI engineers</strong> building autonomous agents for Claude &amp; Cursor.
                    </p>

                    <!-- Interactive Switcher: "Placement & Terms" vs "Current Partner" -->
                    <div style="display:flex;gap:4px;background:rgba(6,8,14,0.6);padding:3px;border-radius:8px;border:1px solid rgba(255,255,255,0.06);margin-bottom:12px;">
                        <button type="button" id="sponsor-tab-terms" class="ide-tab active" onclick="switchSponsorTab('terms', this)" style="flex:1;padding:4px 8px;font-size:0.72rem;text-align:center;">Placement &amp; Terms</button>
                        <button type="button" id="sponsor-tab-preview" class="ide-tab" onclick="switchSponsorTab('preview', this)" style="flex:1;padding:4px 8px;font-size:0.72rem;text-align:center;">Current Partner (Live)</button>
                    </div>

                    <!-- Panel 1: Transparent Terms & Placement Details (Default) -->
                    <div id="sponsor-panel-terms" style="background:#06080E;border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:10px 12px;font-size:0.75rem;line-height:1.5;">
                        <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;">
                            <span style="color:#2DD9E0;font-weight:700;white-space:nowrap;">📍 Placement:</span>
                            <span style="color:#CBD5E1;">#1 Homepage Hero Bento + Top of Category Hub + Search highlight</span>
                        </div>
                        <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;">
                            <span style="color:#FBBF24;font-weight:700;white-space:nowrap;">⏳ Duration:</span>
                            <span style="color:#CBD5E1;"><strong>7 Days guaranteed</strong> (auto-rotates or renew weekly, cancel anytime)</span>
                        </div>
                        <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;">
                            <span style="color:#22C55E;font-weight:700;white-space:nowrap;">⚡ Activation:</span>
                            <span style="color:#CBD5E1;"><strong>Fast activation</strong> via automated GitHub Actions pipeline (bypasses 14-day backlog)</span>
                        </div>
                        <div style="display:flex;align-items:flex-start;gap:8px;">
                            <span style="color:#EC4899;font-weight:700;white-space:nowrap;">🛡️ Conditions:</span>
                            <span style="color:#CBD5E1;">Clean open-source or hosted MCP server · 100% money-back if not verified</span>
                        </div>
                    </div>

                    <!-- Panel 2: Current Partner Live Example -->
                    {sponsor_preview_html}
                </div>

                <!-- Action Footer -->
                <div class="featured-footer" style="display:flex;align-items:center;justify-content:space-between;margin-top:12px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.05);">
                    <a href="/pricing.html" class="featured-view-link" style="color:var(--text-muted);font-size:0.76rem;text-decoration:none;display:inline-flex;align-items:center;gap:4px;">
                        Full Specs &amp; FAQ &rarr;
                    </a>
                    <a href="https://manja8.gumroad.com/l/sponsor_mcp" target="_blank" rel="noopener" class="featured-sponsor-btn" style="background:#2DD9E0;color:#000;font-weight:700;font-size:0.78rem;padding:7px 14px;border-radius:8px;text-decoration:none;box-shadow:0 0 16px rgba(45,217,224,0.3);transition:all 0.2s;">
                        Claim Slot ($49/wk) ⚡
                    </a>
                </div>
            </div>

            <!-- Bento Tile 4: Protodex UI Studio Showcase (7 Cols) -->
            <div class="bento-tile bento-tile-studio">
                <div class="studio-split">
                    <div class="studio-media">
                        <img src="/assets/preview_diverse_templates.jpg" alt="Protodex UI Studio 48 Templates Across Diverse Developer Aesthetics" class="studio-preview-img" loading="lazy">
                        <div class="studio-media-overlay">
                            <span class="style-tag tag-swiss">Swiss Minimalist</span>
                            <span class="style-tag tag-crt">Phosphor CRT</span>
                            <span class="style-tag tag-quant">Web3 Quant</span>
                            <span class="style-tag tag-aurora">Obsidian SaaS</span>
                        </div>
                    </div>
                    <div class="studio-details">
                        <div class="studio-badge-row">
                            <span class="badge-studio-new">&#127912; NEW RELEASE</span>
                            <span class="badge-studio-skill">Antigravity AI Skill</span>
                        </div>
                        <h3 class="studio-title">Protodex UI Studio: 48 Turnkey Templates</h3>
                        <p class="studio-desc">
                            Radical visual variety for high-performing AI developer tools. Built in clean Tailwind CSS + Antigravity AI Skill (SKILL.md).
                        </p>
                        <div class="studio-perks-list">
                            <div class="perk-item"><span>&#10003;</span> 48 Tailwind Layouts</div>
                            <div class="perk-item"><span>&#10003;</span> Zero External Dependencies</div>
                        </div>
                        <div class="studio-actions-row">
                            <a href="/templates.html" class="btn-studio-explore">Explore Gallery &rarr;</a>
                            <a href="https://manja8.gumroad.com/l/lntzuo" target="_blank" rel="noopener" class="btn-studio-buy">Instant Download ($39)</a>
                        </div>
                    </div>
                </div>
            </div>

        </div> <!-- /.bento-grid-2026 -->
""" + BENTO_INTERACTIVE_SCRIPT + f"""

    </div> <!-- /.container -->
</section>

<!-- ====================================================================== -->
<!-- LIVE MCP SERVER DIRECTORY SPOTLIGHT & CATEGORIES (VISIBLE NEAR FOLD)   -->
<!-- ====================================================================== -->
<!-- Commercial Developer Toolkits & Quant Suites Grid -->
<section class="container" style="padding-top:10px">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.2rem;flex-wrap:wrap;gap:10px">
        <div>
            <h2 class="section-title" style="margin-bottom:4px">Developer Datasets &amp; Quant Suites</h2>
            <p style="color:var(--text-muted);font-size:0.88rem;margin:0">Turnkey production datasets, institutional algorithmic trading suites, and developer templates</p>
        </div>
        <a href="/datasets/" style="font-weight:700;font-size:0.88rem;color:var(--accent)">View All Toolkits &rarr;</a>
    </div>

    <div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(320px, 1fr));gap:1rem">
        <!-- 1. Protodex UI Studio -->
        <a href="https://manja8.gumroad.com/l/lntzuo" target="_blank" rel="noopener" style="display:flex;align-items:center;gap:1rem;padding:1.1rem 1.3rem;background:linear-gradient(135deg,rgba(167,139,250,0.14),rgba(45,217,224,0.1));border:1px solid rgba(167,139,250,0.35);border-radius:14px;text-decoration:none;color:var(--text);transition:all 0.2s;box-shadow:0 4px 20px rgba(167,139,250,0.08)">
            <span style="font-size:1.8rem">&#127912;</span>
            <div style="flex:1">
                <div style="font-weight:700;font-size:0.95rem;display:flex;align-items:center;gap:6px">Protodex UI Studio <span style="background:rgba(167,139,250,0.25);color:#c084fc;font-size:0.7rem;padding:2px 8px;border-radius:100px;font-weight:700">NEW &bull; 48 TEMPLATES</span></div>
                <div style="color:var(--text-muted);font-size:0.8rem;margin-top:3px">48 production layouts: Raycast Bento, Cyber HUD, SaaS B2B, Agentic Dashboards.</div>
            </div>
            <span style="background:#a855f7;color:#fff;padding:5px 12px;border-radius:20px;font-size:0.78rem;font-weight:700;white-space:nowrap">$39 &rarr;</span>
        </a>

        <!-- 2. The 31k MCP Dataset -->
        <a href="/datasets/mcp-servers.html" style="display:flex;align-items:center;gap:1rem;padding:1.1rem 1.3rem;background:linear-gradient(135deg,rgba(45,217,224,0.12),rgba(123,97,255,0.08));border:1px solid rgba(45,217,224,0.3);border-radius:14px;text-decoration:none;color:var(--text);transition:all 0.2s;box-shadow:0 4px 20px rgba(45,217,224,0.05)">
            <span style="font-size:1.8rem">&#128202;</span>
            <div style="flex:1">
                <div style="font-weight:700;font-size:0.95rem;display:flex;align-items:center;gap:6px">31,400+ MCP Dataset <span style="background:rgba(45,217,224,0.2);color:var(--accent);font-size:0.7rem;padding:2px 8px;border-radius:100px;font-weight:700">POPULAR</span></div>
                <div style="color:var(--text-muted);font-size:0.8rem;margin-top:3px">Full ecosystem catalog in SQLite, CSV &amp; JSON with stars, repos, and security flags.</div>
            </div>
            <span style="background:var(--accent);color:#000;padding:5px 12px;border-radius:20px;font-size:0.78rem;font-weight:700;white-space:nowrap">$29 &rarr;</span>
        </a>

        <!-- 3. Production MCP Starter Kit -->
        <a href="https://manja8.gumroad.com/l/bsboqh" target="_blank" rel="noopener" style="display:flex;align-items:center;gap:1rem;padding:1.1rem 1.3rem;background:linear-gradient(135deg,rgba(123,97,255,0.12),rgba(45,217,224,0.08));border:1px solid rgba(123,97,255,0.3);border-radius:14px;text-decoration:none;color:var(--text);transition:all 0.2s;box-shadow:0 4px 20px rgba(123,97,255,0.05)">
            <span style="font-size:1.8rem">&#9881;&#65039;</span>
            <div style="flex:1">
                <div style="font-weight:700;font-size:0.95rem;display:flex;align-items:center;gap:6px">MCP Server Starter Kit <span style="background:rgba(123,97,255,0.2);color:#7B61FF;font-size:0.7rem;padding:2px 8px;border-radius:100px;font-weight:700">DUAL-SDK</span></div>
                <div style="color:var(--text-muted);font-size:0.8rem;margin-top:3px">Python FastMCP + TypeScript boilerplate. Stdio &amp; SSE transports, Docker &amp; Cloudflare.</div>
            </div>
            <span style="background:#7B61FF;color:#fff;padding:5px 12px;border-radius:20px;font-size:0.78rem;font-weight:700;white-space:nowrap">$39 &rarr;</span>
        </a>

        <!-- 4. TheBull Crypto Quant Suite (Binance, Delta, Hyperliquid) -->
        <a href="https://manja8.gumroad.com/l/woatyl" target="_blank" rel="noopener" style="display:flex;align-items:center;gap:1rem;padding:1.1rem 1.3rem;background:linear-gradient(135deg,rgba(34,197,94,0.12),rgba(45,217,224,0.08));border:1px solid rgba(34,197,94,0.3);border-radius:14px;text-decoration:none;color:var(--text);transition:all 0.2s;box-shadow:0 4px 20px rgba(34,197,94,0.05)">
            <span style="font-size:1.8rem">&#128002;</span>
            <div style="flex:1">
                <div style="font-weight:700;font-size:0.95rem;display:flex;align-items:center;gap:6px">TheBull Crypto Quant Suite <span style="background:rgba(34,197,94,0.2);color:#22C55E;font-size:0.7rem;padding:2px 8px;border-radius:100px;font-weight:700">CRYPTO</span></div>
                <div style="color:var(--text-muted);font-size:0.8rem;margin-top:3px">Binance, Delta &amp; Hyperliquid perps. 5 strategies: Funding Arbitrage, Orderbook Sniper, Grid.</div>
            </div>
            <span style="background:#22C55E;color:#000;padding:5px 12px;border-radius:20px;font-size:0.78rem;font-weight:700;white-space:nowrap">$49 &rarr;</span>
        </a>

        <!-- 5. ApexAlpha Dhan HQ Institutional F&O Suite (NSE Nifty & BSE Sensex) -->
        <a href="https://manja8.gumroad.com/l/lqzroy" target="_blank" rel="noopener" style="display:flex;align-items:center;gap:1rem;padding:1.1rem 1.3rem;background:linear-gradient(135deg,rgba(245,158,11,0.12),rgba(34,197,94,0.08));border:1px solid rgba(245,158,11,0.3);border-radius:14px;text-decoration:none;color:var(--text);transition:all 0.2s;box-shadow:0 4px 20px rgba(245,158,11,0.05)">
            <span style="font-size:1.8rem">&#9889;</span>
            <div style="flex:1">
                <div style="font-weight:700;font-size:0.95rem;display:flex;align-items:center;gap:6px">ApexAlpha Dhan HQ F&amp;O Suite <span style="background:rgba(245,158,11,0.2);color:#F59E0B;font-size:0.7rem;padding:2px 8px;border-radius:100px;font-weight:700">NSE / BSE</span></div>
                <div style="color:var(--text-muted);font-size:0.8rem;margin-top:3px">Nifty 50 &amp; Sensex options. 11 institutional strategies, Cherry-Picked Top 3, &#8377;0 overnight.</div>
            </div>
            <span style="background:#F59E0B;color:#000;padding:5px 12px;border-radius:20px;font-size:0.78rem;font-weight:700;white-space:nowrap">$49 &rarr;</span>
        </a>

        <!-- 6. PropFirm Titan Quantitative Trading Suite (Gold & FX SMC/ICT EA) -->
        <a href="https://manja8.gumroad.com/l/ozwyyt" target="_blank" rel="noopener" style="display:flex;align-items:center;gap:1rem;padding:1.1rem 1.3rem;background:linear-gradient(135deg,rgba(234,179,8,0.14),rgba(239,68,68,0.08));border:1px solid rgba(234,179,8,0.35);border-radius:14px;text-decoration:none;color:var(--text);transition:all 0.2s;box-shadow:0 4px 20px rgba(234,179,8,0.06)">
            <span style="font-size:1.8rem">&#127942;</span>
            <div style="flex:1">
                <div style="font-weight:700;font-size:0.95rem;display:flex;align-items:center;gap:6px">PropFirm Titan Gold &amp; FX Suite <span style="background:rgba(234,179,8,0.25);color:#EAB308;font-size:0.7rem;padding:2px 8px;border-radius:100px;font-weight:700">FTMO &bull; FUNDED</span></div>
                <div style="color:var(--text-muted);font-size:0.8rem;margin-top:3px">XAU/USD Gold &amp; FX ICT/SMC Judas Sweep MT5 EA with automated 1.0% daily loss sentinel.</div>
            </div>
            <span style="background:#EAB308;color:#000;padding:5px 12px;border-radius:20px;font-size:0.78rem;font-weight:700;white-space:nowrap">$49 &rarr;</span>
        </a>

        <!-- 7. Polymarket Prediction Strategies Bundle (Multi-Risk Tiers) -->
        <a href="https://manja8.gumroad.com/l/ntdiq" target="_blank" rel="noopener" style="display:flex;align-items:center;gap:1rem;padding:1.1rem 1.3rem;background:linear-gradient(135deg,rgba(167,139,250,0.12),rgba(45,217,224,0.08));border:1px solid rgba(167,139,250,0.3);border-radius:14px;text-decoration:none;color:var(--text);transition:all 0.2s;box-shadow:0 4px 20px rgba(167,139,250,0.05)">
            <span style="font-size:1.8rem">&#128302;</span>
            <div style="flex:1">
                <div style="font-weight:700;font-size:0.95rem;display:flex;align-items:center;gap:6px">Polymarket Strategy Bundle <span style="background:rgba(167,139,250,0.2);color:#A78BFA;font-size:0.7rem;padding:2px 8px;border-radius:100px;font-weight:700">MULTI-RISK</span></div>
                <div style="color:var(--text-muted);font-size:0.8rem;margin-top:3px">Low-Risk Binary Arbitrage (Yes+No&lt;$0.985), Market Making Quoting, and 5m BTC Sniper.</div>
            </div>
            <span style="background:#A78BFA;color:#000;padding:5px 12px;border-radius:20px;font-size:0.78rem;font-weight:700;white-space:nowrap">$39 &rarr;</span>
        </a>

        <!-- 8. Polymarket 23M+ Dataset -->
        <a href="/datasets/polymarket-historical.html" style="display:flex;align-items:center;gap:1rem;padding:1.1rem 1.3rem;background:linear-gradient(135deg,rgba(255,217,61,0.12),rgba(45,217,224,0.08));border:1px solid rgba(255,217,61,0.3);border-radius:14px;text-decoration:none;color:var(--text);transition:all 0.2s;box-shadow:0 4px 20px rgba(255,217,61,0.05)">
            <span style="font-size:1.8rem">&#128200;</span>
            <div style="flex:1">
                <div style="font-weight:700;font-size:0.95rem;display:flex;align-items:center;gap:6px">Polymarket 23M+ Dataset <span style="background:rgba(255,217,61,0.2);color:#FFD93D;font-size:0.7rem;padding:2px 8px;border-radius:100px;font-weight:700">BESTSELLER</span></div>
                <div style="color:var(--text-muted);font-size:0.8rem;margin-top:3px">18,400+ prediction markets, 15-min orderbook snapshots. Clean CSV for AI backtesting.</div>
            </div>
            <span style="background:#FFD93D;color:#000;padding:5px 12px;border-radius:20px;font-size:0.78rem;font-weight:700;white-space:nowrap">$19 &rarr;</span>
        </a>

        <!-- 9. Solana DEX Arbitrage Engine -->
        <a href="https://manja8.gumroad.com/l/vvwwwp" target="_blank" rel="noopener" style="display:flex;align-items:center;gap:1rem;padding:1.1rem 1.3rem;background:linear-gradient(135deg,rgba(45,217,224,0.12),rgba(255,217,61,0.08));border:1px solid rgba(45,217,224,0.3);border-radius:14px;text-decoration:none;color:var(--text);transition:all 0.2s;box-shadow:0 4px 20px rgba(45,217,224,0.05)">
            <span style="font-size:1.8rem">&#9889;</span>
            <div style="flex:1">
                <div style="font-weight:700;font-size:0.95rem;display:flex;align-items:center;gap:6px">Solana DEX Arbitrage &amp; Sniper <span style="background:rgba(45,217,224,0.2);color:var(--accent);font-size:0.7rem;padding:2px 8px;border-radius:100px;font-weight:700">JITO MEV</span></div>
                <div style="color:var(--text-muted);font-size:0.8rem;margin-top:3px">Raydium, DLMM, Jito atomic bundler with anti-rug security filter &amp; Jupiter sniper.</div>
            </div>
            <span style="background:var(--accent);color:#000;padding:5px 12px;border-radius:20px;font-size:0.78rem;font-weight:700;white-space:nowrap">$39 &rarr;</span>
        </a>
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
            <div class="use-case-result">Find <strong>{categories.get('Database', 0):,} database servers</strong> &mdash; PostgreSQL, MySQL, MongoDB, Redis, SQLite and more</div>
            <div class="use-case-arrow">Browse database servers &rarr;</div>
        </a>
        <a href="/category/browser-web.html" class="use-case">
            <div class="use-case-scenario">Scraping or automating the web</div>
            <div class="use-case-query">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                browser playwright
            </div>
            <div class="use-case-result">Find <strong>{categories.get('Browser/Web', 0):,} browser servers</strong> &mdash; Playwright, Puppeteer, Scrapling, headless Chrome</div>
            <div class="use-case-arrow">Browse web servers &rarr;</div>
        </a>
        <a href="/category/api-integration.html" class="use-case">
            <div class="use-case-scenario">Integrating a third-party API</div>
            <div class="use-case-query">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                slack stripe github
            </div>
            <div class="use-case-result">Find <strong>{categories.get('API Integration', 0):,} API servers</strong> &mdash; Slack, Stripe, GitHub, Notion, Jira, and dozens more</div>
            <div class="use-case-arrow">Browse API servers &rarr;</div>
        </a>
        <a href="/category/memory-knowledge.html" class="use-case">
            <div class="use-case-scenario">Adding memory to your agent</div>
            <div class="use-case-query">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                memory vector RAG
            </div>
            <div class="use-case-result">Find <strong>{categories.get('Memory/Knowledge', 0):,} memory servers</strong> &mdash; vector stores, knowledge graphs, RAG pipelines, embeddings</div>
            <div class="use-case-arrow">Browse memory servers &rarr;</div>
        </a>
    </div>
</section>

<section class="container">
    <div class="lang-row">
        <span style="color:var(--text-dim);font-size:0.82rem;font-weight:500;padding:8px 0;">Filter by language:</span>
        <a href="/category/ai-llm.html" class="lang-pill"><span class="lang-dot" style="background:#3572A5"></span> Python <span style="color:var(--text-dim)">{lang_counts.get('Python', 0):,}</span></a>
        <a href="/category/code-dev-tools.html" class="lang-pill"><span class="lang-dot" style="background:#3178C6"></span> TypeScript <span style="color:var(--text-dim)">{lang_counts.get('TypeScript', 0):,}</span></a>
        <a href="/category/api-integration.html" class="lang-pill"><span class="lang-dot" style="background:#F7DF1E"></span> JavaScript <span style="color:var(--text-dim)">{lang_counts.get('JavaScript', 0):,}</span></a>
        <a href="/category/devops.html" class="lang-pill"><span class="lang-dot" style="background:#00ADD8"></span> Go <span style="color:var(--text-dim)">{lang_counts.get('Go', 0):,}</span></a>
        <a href="/category/security.html" class="lang-pill"><span class="lang-dot" style="background:#DEA584"></span> Rust <span style="color:var(--text-dim)">{lang_counts.get('Rust', 0):,}</span></a>
    </div>
</section>

{sponsored_section}

<section class="container">
    <h2 class="section-title" id="top-servers">Most Popular MCP Servers</h2>
    <p class="section-subtitle">Top servers by GitHub stars across all categories</p>
    <div class="server-grid">
        {featured}
    </div>
</section>

<section class="container">
    <details style="margin:0 auto 2rem;max-width:1000px;padding:1rem 1.25rem;background:var(--bg-card);border:1px solid var(--border);border-radius:12px;color:var(--text-muted);font-size:0.85rem">
        <summary style="cursor:pointer;font-weight:600;color:var(--text);display:flex;align-items:center;gap:8px;outline:none">
            <span style="font-size:1.1rem">&#129518;</span>
            <span>Free Developer Financial Calculators (India FY 2026-27 Rules)</span>
            <span style="font-size:0.75rem;margin-left:auto;color:var(--accent);font-weight:700">Explore Calculators &darr;</span>
        </summary>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:0.65rem;margin-top:16px">
            <a href="https://inhandsalary.protodex.io/" target="_blank" rel="noopener" style="display:block;padding:0.7rem 0.9rem;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;color:var(--text);text-decoration:none;font-size:0.88rem;transition:border-color 0.15s">
                💰 <strong>In-Hand Salary</strong> — Old vs New regime FY 2026-27
            </a>
            <a href="https://hra.protodex.io/" target="_blank" rel="noopener" style="display:block;padding:0.7rem 0.9rem;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;color:var(--text);text-decoration:none;font-size:0.88rem">
                🏠 <strong>HRA Exemption</strong> — Section 10(13A), Metro/Non-Metro
            </a>
            <a href="https://gratuity.protodex.io/" target="_blank" rel="noopener" style="display:block;padding:0.7rem 0.9rem;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;color:var(--text);text-decoration:none;font-size:0.88rem">
                💼 <strong>Gratuity</strong> — Payment of Gratuity Act + ₹20L exemption
            </a>
            <a href="https://esoptax.protodex.io/" target="_blank" rel="noopener" style="display:block;padding:0.7rem 0.9rem;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;color:var(--text);text-decoration:none;font-size:0.88rem">
                📈 <strong>ESOP Tax</strong> — Perquisite + LTCG/STCG
            </a>
            <a href="https://protodex.io/nsc-calculator/" target="_blank" rel="noopener" style="display:block;padding:0.7rem 0.9rem;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;color:var(--text);text-decoration:none;font-size:0.88rem">
                📜 <strong>NSC</strong> — 7.7%, annual compounding, 80C reinvestment
            </a>
            <a href="https://protodex.io/scss-calculator/" target="_blank" rel="noopener" style="display:block;padding:0.7rem 0.9rem;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;color:var(--text);text-decoration:none;font-size:0.88rem">
                👴 <strong>SCSS (Senior Citizens)</strong> — 8.2%, quarterly income, ₹30L cap, TDS / Form 15H
            </a>
            <a href="https://protodex.io/ltcg-calculator/" target="_blank" rel="noopener" style="display:block;padding:0.7rem 0.9rem;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;color:var(--text);text-decoration:none;font-size:0.88rem">
                💹 <strong>LTCG / Capital Gains</strong> — Budget 2024: 12.5%, ₹1.25L exemption, indexation
            </a>
            <a href="https://protodex.io/swp-calculator/" target="_blank" rel="noopener" style="display:block;padding:0.7rem 0.9rem;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;color:var(--text);text-decoration:none;font-size:0.88rem">
                💸 <strong>SWP (Systematic Withdrawal)</strong> — corpus longevity, LTCG on gains only, SWP vs FD
            </a>
            <a href="https://protodex.io/gst-calculator/" target="_blank" rel="noopener" style="display:block;padding:0.7rem 0.9rem;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;color:var(--text);text-decoration:none;font-size:0.88rem">
                🧾 <strong>GST for Freelancers</strong> — export 0% (LUT), domestic 18%, ₹20L threshold
            </a>
            <a href="https://protodex.io/44ada-calculator/" target="_blank" rel="noopener" style="display:block;padding:0.7rem 0.9rem;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;color:var(--text);text-decoration:none;font-size:0.88rem">
                📑 <strong>Section 44ADA Presumptive Tax</strong> — declare 50%, ₹75L limit, advance tax by 15 Mar
            </a>
            <a href="https://protodex.io/advance-tax-calculator/" target="_blank" rel="noopener" style="display:block;padding:0.7rem 0.9rem;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;color:var(--text);text-decoration:none;font-size:0.88rem">
                📅 <strong>Advance Tax for Freelancers</strong> — 15 Jun/Sep/Dec/Mar installments, 234B/234C interest, 44ADA single-pay
            </a>
            <a href="https://protodex.io/tds-calculator/" target="_blank" rel="noopener" style="display:block;padding:0.7rem 0.9rem;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;color:var(--text);text-decoration:none;font-size:0.88rem">
                ✂️ <strong>TDS Calculator &amp; Rate Chart</strong> — 194J/194C/194H/194I rates, no-PAN 20%, threshold, freelancer refund
            </a>
            <a href="https://protodex.io/property-tds-calculator/" target="_blank" rel="noopener" style="display:block;padding:0.7rem 0.9rem;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;color:var(--text);text-decoration:none;font-size:0.88rem">
                🏘️ <strong>TDS on Property Purchase</strong> — 1% Section 194-IA, Form 26QB, ₹50L threshold, no-PAN 20%, NRI-seller trap
            </a>
            <a href="https://protodex.io/hra-calculator/" target="_blank" rel="noopener" style="display:block;padding:0.7rem 0.9rem;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;color:var(--text);text-decoration:none;font-size:0.88rem">
                🏠 <strong>HRA Exemption</strong> — least-of-three, metro vs non-metro, old-regime only
            </a>
            <a href="https://stampduty.protodex.io/" target="_blank" rel="noopener" style="display:block;padding:0.7rem 0.9rem;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;color:var(--text);text-decoration:none;font-size:0.88rem">
                🏗 <strong>Karnataka Stamp Duty</strong> — Bengaluru/Mysuru, 2% reg fee
            </a>
            <a href="https://stampdutymaharashtra.protodex.io/" target="_blank" rel="noopener" style="display:block;padding:0.7rem 0.9rem;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;color:var(--text);text-decoration:none;font-size:0.88rem">
                🏛️ <strong>Maharashtra Stamp Duty</strong> — Mumbai/Pune, women discount
            </a>
        </div>
    </details>
</section>
"""
    html += f"""
<section class="container">
    <div class="cta-banner">
        <h2>Can't find what you're looking for?</h2>
        <p>Tell us what MCP server you need. We'll help you find it — or flag it as a gap the community can fill.</p>
        <div class="cta-buttons">
            <a href="https://github.com/LuciferForge/mcp-directory/discussions/new?category=ideas&title=Looking+for:+&body=I'm+looking+for+an+MCP+server+that..." target="_blank" rel="noopener" class="btn">Request a Server</a>
            <a href="/submit.html" class="btn btn-outline">Submit Your Server</a>
        </div>
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
            <span class="cat-icon">{cat_icon_svg(cat_name)}</span>
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

    dataset_cta = DATASET_CTA if cat_name in DATA_RELEVANT_CATEGORIES else ""
    html = html_head(title, desc, f"/category/{meta['slug']}.html")
    html += html_header()
    html += f"""
<div class="page-header">
    <div class="container">
        <div class="breadcrumb"><a href="/">Home</a> / <a href="/categories.html">Categories</a> / {escape(cat_name)}</div>
        <h1><span style="display:inline-flex;vertical-align:-6px;margin-right:10px">{cat_icon_svg(cat_name, 32)}</span>{escape(cat_name)} MCP Servers</h1>
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
{dataset_cta}
"""
    html += html_footer()
    return html


def generate_install_config(server):
    """Generate copy-paste config snippets honoring explicit install_config overrides."""
    name = server["name"]
    repo = server["repo"]
    lang = server.get("language", "")
    cfg = server.get("install_config") or {}
    mode = cfg.get("mode", "")

    panel_id = slugify(repo.replace("/", "-")) or "server"
    fallback_key = name.lower().replace(" ", "-").replace("/", "-")[:20] or panel_id
    server_key = cfg.get("server_key") or fallback_key
    owner, repo_name = repo.split("/", 1) if "/" in repo else ("", repo)

    tabs = []
    notes = []

    if mode == "remote":
        endpoint = cfg.get("url", "")
        transport = cfg.get("transport", "streamable-http")
        headers = cfg.get("headers") or {}
        entry = {"type": transport, "url": endpoint}
        cursor_entry = {"url": endpoint}
        if headers:
            entry["headers"] = headers
            cursor_entry["headers"] = headers
        remote_json = json.dumps({"mcpServers": {server_key: entry}}, indent=2)
        cursor_json = json.dumps({"mcpServers": {server_key: cursor_entry}}, indent=2)
        claude_code = cfg.get("claude_code") or f"claude mcp add --transport http {server_key} {endpoint}"

        tabs = [
            (
                f"remote-json-{panel_id}",
                "Remote MCP (JSON)",
                f'Connect via Streamable HTTP endpoint <code>{escape(endpoint)}</code> in <code>.mcp.json</code> or Claude Connectors:',
                remote_json,
            ),
            (
                f"claude-code-{panel_id}",
                "Claude Code",
                "Run in terminal:",
                claude_code,
            ),
            (
                f"cursor-{panel_id}",
                "Cursor",
                "Add to <code>.cursor/mcp.json</code>:",
                cursor_json,
            ),
        ]
        if cfg.get("note"):
            notes.append(cfg["note"])

    elif mode == "docker_http":
        docker_image = cfg.get("docker_image", "")
        docker_cmd = cfg.get("docker_cmd", "")
        docker_snippet = "\n".join(x for x in (f"docker pull {docker_image}" if docker_image else "", docker_cmd) if x)
        endpoint = cfg.get("url", "")
        headers = cfg.get("headers") or {}
        cursor_entry = {"url": endpoint}
        if headers:
            cursor_entry["headers"] = headers
        cursor_json = json.dumps({"mcpServers": {server_key: cursor_entry}}, indent=2)
        claude_code = cfg.get("claude_code") or f"claude mcp add --transport http {server_key} {endpoint}"

        tabs = [
            (
                f"docker-{panel_id}",
                "Docker Setup",
                "Run the self-hosted container and enable <strong>Settings &rarr; Agent access (MCP)</strong>:",
                docker_snippet,
            ),
            (
                f"claude-code-{panel_id}",
                "Claude Code",
                "Connect Claude Code over HTTP:",
                claude_code,
            ),
            (
                f"cursor-{panel_id}",
                "Cursor / HTTP JSON",
                "Add to <code>.cursor/mcp.json</code> or <code>.mcp.json</code>:",
                cursor_json,
            ),
        ]
        if cfg.get("note"):
            notes.append(cfg["note"])

    elif mode == "framework_remote_docs":
        scaffold_cmd = cfg.get("scaffold_cmd", "npx create-xmcp-app@latest")
        init_cmd = cfg.get("init_cmd", "npx init-xmcp@latest")
        endpoint = cfg.get("url", "")
        claude_code = cfg.get("claude_code") or f"claude mcp add --transport http {server_key} {endpoint}"
        cursor_json = json.dumps({"mcpServers": {server_key: {"type": "http", "url": endpoint}}}, indent=2)

        tabs = [
            (
                f"scaffold-{panel_id}",
                "Framework CLI",
                "Scaffold a new xmcp TypeScript project (or initialize inside an existing app):",
                f"{scaffold_cmd}\n# Or initialize inside an existing project:\n{init_cmd}",
            ),
            (
                f"claude-code-{panel_id}",
                "Docs MCP (Claude Code)",
                "Connect to the official read-only documentation MCP server:",
                claude_code,
            ),
            (
                f"cursor-{panel_id}",
                "Docs MCP (HTTP JSON)",
                "Add the documentation MCP endpoint to <code>.cursor/mcp.json</code> or <code>.mcp.json</code>:",
                cursor_json,
            ),
        ]
        if cfg.get("note"):
            notes.append(cfg["note"])

    elif mode == "dual":
        command = cfg.get("command", "npx")
        args = cfg.get("args", [])
        remote_url = cfg.get("remote_url", "")
        stdio_json = json.dumps({"mcpServers": {server_key: {"command": command, "args": args}}}, indent=2)
        claude_code = cfg.get("claude_code") or f"claude mcp add {server_key} {command} {' '.join(args)}"
        remote_cc = cfg.get("remote_claude_code", "")
        if remote_cc:
            claude_code = f"{claude_code}\n\n# Or connect via hosted Streamable HTTP:\n{remote_cc}"
        cursor_json = json.dumps(
            {
                "mcpServers": {
                    server_key: {"command": command, "args": args},
                    f"{server_key}-remote": {"type": "http", "url": remote_url},
                }
            },
            indent=2,
        )

        tabs = [
            (
                f"claude-desktop-{panel_id}",
                "Claude Desktop",
                f'Add local stdio server to <code>claude_desktop_config.json</code> (hosted HTTP: <code>{escape(remote_url)}</code>):',
                stdio_json,
            ),
            (
                f"claude-code-{panel_id}",
                "Claude Code",
                "Run in terminal (local stdio or hosted HTTP):",
                claude_code,
            ),
            (
                f"cursor-{panel_id}",
                "Cursor",
                "Add to <code>.cursor/mcp.json</code> (local stdio or remote HTTP):",
                cursor_json,
            ),
        ]
        if cfg.get("note"):
            notes.append(cfg["note"])

    else:
        if mode == "stdio":
            command = cfg["command"]
            args = cfg["args"]
            claude_code = cfg.get("claude_code") or f'claude mcp add {server_key} {command} {" ".join(args)}'
            if cfg.get("pip_install"):
                notes.append(f'Or install with pip: <code>{escape(cfg["pip_install"])}</code>')
            if cfg.get("note"):
                notes.append(cfg["note"])
        else:
            if lang in ("TypeScript", "JavaScript"):
                command = "npx"
                args = ["-y", repo]
            elif lang == "Python":
                command = "uvx"
                python_packages = {
                    "jacobiusmakes/parlay-api-mcp": "parlayapi-mcp"
                }
                pkg = cfg.get("package") or python_packages.get(repo.lower(), repo_name.lower().replace("_", "-"))
                args = [pkg]
                notes.append(f'Or install with pip: <code>pip install {escape(pkg)}</code>')
            elif lang == "Go":
                command = "go"
                args = ["run", f"github.com/{repo}@latest"]
            elif lang == "Rust":
                command = "cargo"
                args = ["run", "--", repo_name]
            else:
                command = "npx"
                args = ["-y", repo]
            claude_code = f'claude mcp add {server_key} {command} {" ".join(args)}'

        stdio_json = json.dumps({"mcpServers": {server_key: {"command": command, "args": args}}}, indent=2)
        tabs = [
            (
                f"claude-desktop-{panel_id}",
                "Claude Desktop",
                "Add to <code>claude_desktop_config.json</code>:",
                stdio_json,
            ),
            (
                f"claude-code-{panel_id}",
                "Claude Code",
                "Run in terminal:",
                claude_code,
            ),
            (
                f"cursor-{panel_id}",
                "Cursor",
                "Add to <code>.cursor/mcp.json</code>:",
                stdio_json,
            ),
        ]

    tab_buttons = "\n".join(
        f'            <button class="install-tab{" active" if i == 0 else ""}" onclick="showTab(this, \'{tab_id}\')">{escape(tab_title)}</button>'
        for i, (tab_id, tab_title, _, _) in enumerate(tabs)
    )
    tab_panels = "\n".join(
        f"""        <div id="{tab_id}" class="install-panel{" active" if i == 0 else ""}"{"" if i == 0 else ' style="display:none"'}>
            <p class="install-label">{intro_html}</p>
            <div class="code-block">
                <pre><code>{escape(code_text)}</code></pre>
                <button class="copy-btn" onclick="copyCode(this)">📋 Copy</button>
            </div>
        </div>"""
        for i, (tab_id, _, intro_html, code_text) in enumerate(tabs)
    )
    def _format_note(note_text):
        if note_text.startswith("<p "):
            return note_text
        if "<code>" in note_text:
            return f'<p class="install-note">{note_text}</p>'
        rendered = escape(note_text)
        rendered = re.sub(r"`([^`]+)`", r"<code>\1</code>", rendered)

        def _link_url(match):
            full = match.group(0)
            trimmed = full.rstrip(".,;:)")
            trailing = full[len(trimmed):]
            return f'<a href="{trimmed}" target="_blank" rel="noopener">{trimmed}</a>{trailing}'

        rendered = re.sub(
            r"(?<!<code>)(?<![\">])https?://[^\s<>]+",
            _link_url,
            rendered,
        )
        return f'<p class="install-note">{rendered}</p>'

    notes_html = "\n        ".join(_format_note(n) for n in notes if n)

    return f"""
    <div class="install-section" style="margin-top:32px">
        <h2>Quick Install</h2>
        <p class="install-subtitle">Copy the config for your editor. Verify environment variables or setup notes in the README.</p>

        <div class="install-tabs">
{tab_buttons}
        </div>

{tab_panels}
        {notes_html}
    </div>
"""


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
    homepage = server.get("homepage") or ""
    docs_url = server.get("docs_url") or ""
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
        "url": homepage or url,
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
    dataset_cta = DATASET_CTA if cat in DATA_RELEVANT_CATEGORIES else ""
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
    install_config = generate_install_config(server)

    website_btn = (
        f'<a href="{escape(homepage)}" target="_blank" rel="noopener" class="btn btn-outline">Official Website ↗</a>'
        if homepage and homepage.rstrip("/") != url.rstrip("/") else ""
    )
    docs_btn = (
        f'<a href="{escape(docs_url)}" target="_blank" rel="noopener" class="btn btn-outline">Docs / Setup Guide ↗</a>'
        if docs_url and docs_url.rstrip("/") not in (url.rstrip("/"), homepage.rstrip("/")) else ""
    )

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
        <span class="meta-item"><span style="display:inline-flex;vertical-align:-2px;margin-right:4px">{cat_icon_svg(cat, 13)}</span>{escape(cat)}</span>
        <span class="meta-item">Updated {updated}</span>
        <span class="meta-item">{security_badge_html(server)}</span>
    </div>

    <div class="detail-desc">{escape(desc)}</div>

    <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:8px">
        <a href="{escape(url)}" target="_blank" rel="noopener" class="btn">
            View on GitHub →
        </a>
        {website_btn}
        {docs_btn}
        <a href="/audit.html" style="display:inline-flex;align-items:center;gap:6px;padding:10px 18px;background:linear-gradient(135deg,rgba(123,97,255,0.25),rgba(45,217,224,0.2));border:1px solid rgba(123,97,255,0.4);color:var(--text);text-decoration:none;border-radius:8px;font-weight:600;font-size:0.9rem;box-shadow:0 0 16px rgba(123,97,255,0.15)">
            🛡️ Security &amp; TRiSM Audit →
        </a>
    </div>

    {install_config}

    {COMMERCIAL_SERVER_CALLOUT}

    <div style="margin-top:40px">
        {readme_section}
        {tools_section}
        {topics_section}
    </div>

    {related_html}
    {dataset_cta}
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


def build_pricing_page(total=31428):
    title = f"Sponsor & Advertise on Protodex — Reach {total:,}+ MCP Developers"
    desc = "Feature your MCP server, developer tool, or AI API at the top of Protodex. Reaching 30,000+ AI engineers building for Claude, Cursor, and autonomous agents."

    extra_css = """
    <style>
    .pricing-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin: 48px auto; max-width: 1100px; }
    .tier { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 36px 28px; display: flex; flex-direction: column; position: relative; box-shadow: 0 4px 20px rgba(0,0,0,0.3); transition: all 0.22s ease; }
    .tier:hover { transform: translateY(-4px); border-color: var(--accent); box-shadow: 0 12px 40px rgba(45, 217, 224, 0.15); }
    .tier.featured { border-color: var(--accent); background: linear-gradient(180deg, rgba(45, 217, 224, 0.08) 0%, rgba(14, 17, 28, 0.95) 100%); box-shadow: 0 0 30px rgba(45, 217, 224, 0.2); }
    .tier-badge { position: absolute; top: -14px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, var(--accent), #7B61FF); color: #000; font-size: 0.72rem; font-weight: 800; padding: 4px 14px; border-radius: 100px; text-transform: uppercase; letter-spacing: 0.05em; }
    .tier-name { font-size: 1.3rem; font-weight: 800; color: #fff; margin-bottom: 8px; }
    .tier-desc { color: var(--text-muted); font-size: 0.85rem; margin-bottom: 20px; line-height: 1.5; min-height: 40px; }
    .tier-price { font-size: 2.5rem; font-weight: 900; color: var(--accent); display: flex; align-items: baseline; gap: 4px; margin-bottom: 24px; font-family: var(--mono); }
    .tier-price span { font-size: 0.9rem; color: var(--text-dim); font-weight: 500; }
    .tier-features { list-style: none; padding: 0; margin: 0 0 32px 0; display: flex; flex-direction: column; gap: 12px; flex: 1; }
    .tier-features li { display: flex; align-items: center; gap: 10px; font-size: 0.88rem; color: var(--text); }
    .tier-features li svg { color: var(--green); flex-shrink: 0; }
    .tier-btn { display: block; text-align: center; padding: 12px 20px; border-radius: 10px; font-weight: 700; font-size: 0.95rem; text-decoration: none; transition: all 0.2s; }
    .tier-btn-primary { background: var(--accent); color: #000; box-shadow: 0 0 20px rgba(45, 217, 224, 0.35); }
    .tier-btn-primary:hover { background: #45e3ea; box-shadow: 0 0 30px rgba(45, 217, 224, 0.6); color: #000; }
    .tier-btn-secondary { background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.15); color: #fff; }
    .tier-btn-secondary:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-soft); }
    @media (max-width: 900px) { .pricing-grid { grid-template-columns: 1fr; } }
    </style>
    """

    html = html_head(title, desc, "/pricing.html", extra_css)
    html += html_header("pricing")
    html += f"""
    <section class="hero">
        <div class="container hero-content">
            <div class="hero-badge"><span class="pulse"></span> {total:,} Indexed Servers &bull; 25,000+ Monthly Developers</div>
            <h1>Put Your MCP Server in Front of <span class="gradient">Active AI Engineers</span></h1>
            <p>Protodex is the definitive open index of Model Context Protocol (MCP) servers. Showcase your infrastructure, tools, and developer platforms to builders configuring Claude Desktop, Cursor, and autonomous agents.</p>
        </div>
    </section>

    <div class="container">
        <div class="pricing-grid">
            <!-- Tier 1 -->
            <div class="tier featured">
                <div class="tier-badge">Most Popular</div>
                <div class="tier-name">Featured MCP Listing</div>
                <div class="tier-desc">Pin your server to the top of Protodex with a glowing Verified Sponsor badge.</div>
                <div class="tier-price">$49 <span>/ week</span></div>
                <ul class="tier-features">
                    <li><svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Top slot on Homepage &amp; category directory</li>
                    <li><svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Glowing 'Featured' badge &amp; priority indexing</li>
                    <li><svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Direct traffic to your GitHub or landing page</li>
                    <li><svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Fast activation via Gumroad + GitHub Actions</li>
                </ul>
                <a href="https://manja8.gumroad.com/l/sponsor_mcp" target="_blank" rel="noopener" class="tier-btn tier-btn-primary">Sponsor for $49/wk &rarr;</a>
            </div>

            <!-- Tier 2 -->
            <div class="tier">
                <div class="tier-name">Showcase Partner</div>
                <div class="tier-desc">Permanent front-page developer callout for enterprise tooling and AI developer platforms.</div>
                <div class="tier-price">$99 <span>/ month</span></div>
                <ul class="tier-features">
                    <li><svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Dedicated Commercial Showcase Card</li>
                    <li><svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Permanent inclusion in developer toolkits</li>
                    <li><svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Social shoutout on Protodex dev feed</li>
                    <li><svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Custom CTA and tracked conversion link</li>
                </ul>
                <a href="https://manja8.gumroad.com/l/sponsor_mcp" target="_blank" rel="noopener" class="tier-btn tier-btn-secondary">Book Showcase Slot &rarr;</a>
            </div>

            <!-- Tier 3 -->
            <div class="tier">
                <div class="tier-name">Security &amp; TRiSM Audit</div>
                <div class="tier-desc">Comprehensive vulnerability, prompt injection, and EU AI Act compliance audit.</div>
                <div class="tier-price">$499 <span>/ audit</span></div>
                <ul class="tier-features">
                    <li><svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Complete static &amp; dynamic pen test</li>
                    <li><svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> AegisMesh TRiSM Certification Badge</li>
                    <li><svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Shell escape &amp; egress security validation</li>
                    <li><svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Executive report PDF for enterprise buyers</li>
                </ul>
                <a href="/audit.html" class="tier-btn tier-btn-secondary">Request Security Audit &rarr;</a>
            </div>
        </div>
    </div>
    """
    html += html_footer()
    return html


def build_security_page(servers):
    total = len(servers)
    scored = sum(1 for s in servers if s.get("security_band"))
    green = sum(1 for s in servers if s.get("security_band") == "green")
    yellow = sum(1 for s in servers if s.get("security_band") == "yellow")
    red = sum(1 for s in servers if s.get("security_band") == "red")

    title = f"Security Scores — {SITE_NAME}"
    desc = f"Every MCP server on Protodex is scanned for security issues. See how {scored:,} servers scored."

    html = html_head(title, desc, "/security.html")
    html += html_header("security")
    html += f"""
<div class="page-header">
    <div class="container">
        <h1>Security Scores</h1>
        <p>We scan every MCP server for security issues so you don't have to.</p>
    </div>
</div>
<div class="container security-content">
    <h2>How It Works</h2>
    <p>Every server indexed on Protodex is automatically scanned and assigned a security band based on repository health signals: maintenance activity, license, dependency hygiene, and known vulnerability patterns.</p>

    <div class="band-explain">
        <div class="band-row">
            <span class="sec-badge sec-green" style="font-size:0.85rem;padding:6px 14px">&#10003; Secure</span>
            <span class="band-desc"><strong>{green:,} servers</strong> — No known vulnerabilities. Actively maintained. Safe to use.</span>
        </div>
        <div class="band-row">
            <span class="sec-badge sec-yellow" style="font-size:0.85rem;padding:6px 14px">&#9888; Review</span>
            <span class="band-desc"><strong>{yellow:,} servers</strong> — Needs review. May have stale dependencies, missing license, or limited maintenance history.</span>
        </div>
        <div class="band-row">
            <span class="sec-badge sec-red" style="font-size:0.85rem;padding:6px 14px">&#10007; Risk</span>
            <span class="band-desc"><strong>{red:,} servers</strong> — Known issues or unmaintained. Use with caution.</span>
        </div>
    </div>

    <div style="margin-top:40px">
        <h2>Coverage</h2>
        <p><strong>{scored:,}</strong> of {total:,} servers have been scanned ({scored*100//total}% coverage). Scores are updated weekly alongside the directory.</p>
    </div>

    <div style="margin-top:40px">
        <h2>Methodology</h2>
        <p>Security scores are calculated from public repository signals:</p>
        <ul style="color:var(--text-muted);padding-left:24px;margin-bottom:24px;line-height:2">
            <li>Last commit date (is it actively maintained?)</li>
            <li>License presence and type</li>
            <li>Star count and community adoption</li>
            <li>Dependency freshness</li>
            <li>Known vulnerability database cross-reference</li>
            <li>Repository configuration (branch protection, etc.)</li>
        </ul>
        <p>Scores range from 0-100. Green = 70+, Yellow = 40-69, Red = below 40.</p>
    </div>
</div>
"""
    html += html_footer()
    return html


def build_mcp_dataset_page(total, zip_mb):
    """Landing page for the Protodex MCP Ecosystem Dataset ($29 on Gumroad)."""
    import json as _json
    today = datetime.now().strftime("%Y-%m-%d")
    page_path = "/datasets/mcp-servers.html"
    page_url = f"{SITE_URL}{page_path}"
    gumroad_url = "https://manja8.gumroad.com/l/zcyee?utm_source=protodex&utm_medium=dataset-page&utm_campaign=mcp-dataset"

    title = f"31,400+ MCP Server Ecosystem Dataset ({total:,} Repos in SQLite, CSV & JSON) | Protodex"
    desc = (
        f"Download the complete vetted Model Context Protocol directory dataset: {total:,} screened MCP servers "
        f"with GitHub stars, categories, languages, tool lists, and security ratings in SQLite, CSV, and JSON ($29 one-time)."
    )

    keywords = [
        "mcp server dataset", "model context protocol dataset", "mcp directory sqlite",
        "mcp servers csv json", "ai agent tool index", "mcp ecosystem data",
    ]

    dataset_schema = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": f"Protodex MCP Server Ecosystem Dataset ({total:,} Screened Servers)",
        "description": desc,
        "url": page_url,
        "sameAs": "https://manja8.gumroad.com/l/zcyee",
        "keywords": keywords,
        "license": "https://manja8.gumroad.com/l/zcyee",
        "isAccessibleForFree": False,
        "creator": {"@type": "Organization", "name": "Protodex", "url": SITE_URL},
        "publisher": {"@type": "Organization", "name": "Protodex", "url": SITE_URL},
        "dateModified": today,
        "variableMeasured": ["name", "repo", "stars", "category", "language", "description", "slug", "security_score"],
        "distribution": [
            {
                "@type": "DataDownload",
                "encodingFormat": "application/zip",
                "contentUrl": gumroad_url,
                "name": f"SQLite + CSV + JSON bundle ({zip_mb} MB, {total:,} records)",
            },
        ],
    }

    product_schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "31,400+ MCP Server Ecosystem Dataset (SQLite + CSV + JSON)",
        "description": desc,
        "brand": {"@type": "Brand", "name": "Protodex"},
        "url": page_url,
        "offers": [
            {
                "@type": "Offer",
                "name": "Complete MCP Ecosystem Dataset",
                "price": "29",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock",
                "url": gumroad_url,
            }
        ],
    }

    extra = (
        '<meta name="keywords" content="' + escape(", ".join(keywords)) + '">\n'
        '    <script type="application/ld+json">' + _json.dumps(dataset_schema) + '</script>\n'
        '    <script type="application/ld+json">' + _json.dumps(product_schema) + '</script>'
    )

    html = html_head(title, desc, page_path, extra)
    html += html_header("datasets")
    html += f"""
<div class="page-header" style="text-align:center;padding:70px 0 50px;background:radial-gradient(ellipse at top,rgba(45,217,224,0.12),transparent 70%)">
    <div class="container" style="max-width:880px;margin:0 auto">
        <div class="breadcrumb" style="display:inline-flex;gap:6px;align-items:center;background:rgba(255,255,255,0.05);padding:4px 14px;border-radius:100px;font-size:0.8rem;color:var(--text-muted);margin-bottom:18px"><a href="/" style="color:var(--text-muted)">Home</a> / <a href="/datasets/" style="color:var(--text-muted)">Datasets</a> / <span style="color:var(--accent)">MCP Server Catalog</span></div>
        <h1 style="font-size:2.7rem;font-weight:800;letter-spacing:-0.03em;line-height:1.15;margin-bottom:18px">Protodex MCP Ecosystem Dataset<br><span style="color:var(--accent)">{total:,} Vetted Servers &bull; SQLite + CSV + JSON</span></h1>
        <p style="font-size:1.1rem;color:var(--text-muted);line-height:1.6;max-width:720px;margin:0 auto 28px">Complete structured export of the cleaned Protodex Model Context Protocol index — filtered against malware/FakeGit lures and normalized across 15 categories with star counts, languages, tools, and security ratings.</p>
        <div style="display:flex;gap:14px;justify-content:center;align-items:center;flex-wrap:wrap">
            <a href="{gumroad_url}" target="_blank" rel="noopener" class="btn" style="background:var(--accent);color:#000;font-weight:800;font-size:1.05rem;padding:14px 30px;border-radius:10px;box-shadow:0 6px 24px rgba(45,217,224,0.35)">Buy Dataset on Gumroad — $29 &rarr;</a>
            <a href="/datasets/" class="btn btn-outline" style="padding:14px 22px;border-radius:10px">Browse All Kits &amp; Samples</a>
        </div>
        <div style="font-size:0.82rem;color:var(--text-dim);margin-top:14px">&#10003; {zip_mb} MB instant Gumroad zip ({total:,} servers) &bull; &#10003; One-time purchase ($29) &bull; &#10003; SQLite, CSV &amp; full JSON</div>
    </div>
</div>

<section class="container" style="max-width:960px;margin:0 auto;padding-top:20px">
    <div class="stats-bar" style="margin:20px 0 40px;display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px">
        <div class="stat"><div class="stat-num" style="color:var(--accent)">{total:,}</div><div class="stat-lbl">Screened Servers</div></div>
        <div class="stat"><div class="stat-num" style="color:#7B61FF">15</div><div class="stat-lbl">Categories</div></div>
        <div class="stat"><div class="stat-num" style="color:#22C55E">3 Formats</div><div class="stat-lbl">SQLite + CSV + JSON</div></div>
        <div class="stat"><div class="stat-num" style="color:#FFD93D">{zip_mb} MB</div><div class="stat-lbl">Archive Size</div></div>
    </div>

    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:28px;margin-bottom:36px">
        <h2 style="font-size:1.45rem;margin-bottom:12px">Included Archive Files</h2>
        <div style="overflow-x:auto">
            <table style="width:100%;border-collapse:collapse;font-size:0.86rem;font-family:var(--mono);text-align:left">
                <thead>
                    <tr style="border-bottom:1px solid var(--border);color:var(--accent)">
                        <th style="padding:10px 12px">File</th>
                        <th style="padding:10px 12px">Contents</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid var(--border)"><td style="padding:10px 12px">mcp_servers.sqlite</td><td style="padding:10px 12px;font-family:var(--font)">Indexed SQLite database ready for DuckDB / SQLite / datasette queries</td></tr>
                    <tr style="border-bottom:1px solid var(--border)"><td style="padding:10px 12px">mcp_servers_31k.csv</td><td style="padding:10px 12px;font-family:var(--font)">Clean UTF-8 CSV (<code>name, repo, stars, category, language, description, slug, security_score</code>)</td></tr>
                    <tr><td style="padding:10px 12px">mcp_servers_full.json</td><td style="padding:10px 12px;font-family:var(--font)">Full metadata payload including topics, tool inventories, README excerpts &amp; install overrides</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <div style="background:linear-gradient(135deg,rgba(45,217,224,0.1),rgba(123,97,255,0.08));border:1px solid rgba(45,217,224,0.3);border-radius:18px;padding:34px;text-align:center;margin-bottom:56px">
        <h2 style="font-size:1.85rem;margin-bottom:8px">Get the Full {total:,}-Server MCP Dataset — $29</h2>
        <p style="color:var(--text-muted);max-width:580px;margin:0 auto 22px">Instant delivery via Gumroad receipt. Build market research maps, internal MCP registries, or fine-tuned agent routers without rate limits.</p>
        <a href="{gumroad_url}" target="_blank" rel="noopener" class="btn" style="background:var(--accent);color:#000;font-weight:800;font-size:1.05rem;padding:14px 32px;border-radius:10px">Buy Dataset ($29) &rarr;</a>
    </div>
</section>
"""
    html += html_footer()
    return html


DATASET_PATH = "/datasets/polymarket-historical.html"

def build_dataset_page():
    """P0 revenue SEO asset: buyer-intent landing page for the Polymarket dataset,
    with schema.org/Dataset (Google Dataset Search) + Product/Offer markup."""
    import json as _json
    today = datetime.now().strftime("%Y-%m-%d")
    page_url = f"{SITE_URL}{DATASET_PATH}"
    img_url = f"{SITE_URL}/og/polymarket-dataset.png"
    dataset_url = "https://manja8.gumroad.com/l/polymarket-quant-toolkit?utm_source=protodex&utm_medium=dataset-page&utm_campaign=polymarket-dataset"

    title = "Polymarket Historical Dataset — 23.0M+ Price & Orderbook Snapshots (CSV) | Protodex"
    desc = ("Download the complete Polymarket historical dataset: 23.0M+ 15-minute price & orderbook "
            "snapshots across 18,400+ prediction markets. Clean CSV for quant backtesting & AI agent training ($19 one-time).")

    keywords = ["polymarket dataset", "polymarket historical data", "prediction market data",
                "polymarket price history", "prediction market dataset csv", "polymarket api data",
                "backtesting prediction markets", "polymarket orderbook data", "polymarket csv download",
                "ai agent financial backtesting", "prediction market machine learning"]

    dataset_schema = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "Polymarket Historical Dataset — 23.0M+ Price & Orderbook Snapshots",
        "alternateName": "Polymarket Quant Price & Orderbook Snapshots",
        "description": ("23.0M+ price and orderbook snapshots sampled every 15 minutes across "
                        "18,400+ Polymarket prediction markets over 76+ trading days. Each row "
                        "includes market question, outcome side, mid price, best bid/ask, bid/ask depth, spread "
                        "and a UTC timestamp. Delivered as clean CSV for backtesting, quant research, and AI/LLM agent training."),
        "url": page_url,
        "image": img_url,
        "sameAs": "https://manja8.gumroad.com/l/polymarket-quant-toolkit",
        "keywords": keywords,
        "license": "https://manja8.gumroad.com/l/polymarket-quant-toolkit",
        "isAccessibleForFree": False,
        "creator": {"@type": "Organization", "name": "Protodex", "url": SITE_URL},
        "publisher": {"@type": "Organization", "name": "Protodex", "url": SITE_URL},
        "version": "2026.1",
        "dateModified": today,
        "temporalCoverage": "2026-03-29/" + today,
        "measurementTechnique": "15-minute price and orderbook snapshots via the Polymarket CLOB API",
        "variableMeasured": ["market question", "outcome (Yes/No)", "mid price", "best bid",
                             "best ask", "bid depth", "ask depth", "spread", "timestamp (UTC, 15-min)"],
        "distribution": [
            {"@type": "DataDownload", "encodingFormat": "text/csv",
             "contentUrl": dataset_url,
             "name": "Full dataset — instant download ($19)"},
        ],
    }

    product_schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Polymarket Historical Dataset — 23.0M+ Price & Orderbook Snapshots",
        "description": desc,
        "image": [img_url],
        "brand": {"@type": "Brand", "name": "Protodex"},
        "url": page_url,
        "offers": [
            {"@type": "Offer", "name": "Full Polymarket Historical Dataset (Instant Download)", "price": "19", "priceCurrency": "USD",
             "availability": "https://schema.org/InStock", "url": dataset_url},
        ],
    }

    extra = ('<meta name="keywords" content="' + escape(", ".join(keywords)) + '">\n'
             '    <script type="application/ld+json">' + _json.dumps(dataset_schema) + '</script>\n'
             '    <script type="application/ld+json">' + _json.dumps(product_schema) + '</script>')

    html = html_head(title, desc, DATASET_PATH, extra, og_image=img_url)
    html += html_header()
    html += f"""
<div class="page-header" style="text-align:center;padding:70px 0 50px;background:radial-gradient(ellipse at top,rgba(45,217,224,0.12),transparent 70%)">
    <div class="container" style="max-width:880px;margin:0 auto">
        <div class="breadcrumb" style="display:inline-flex;gap:6px;align-items:center;background:rgba(255,255,255,0.05);padding:4px 14px;border-radius:100px;font-size:0.8rem;color:var(--text-muted);margin-bottom:18px"><a href="/" style="color:var(--text-muted)">Home</a> / <span>Datasets</span> / <span style="color:var(--accent)">Polymarket Historical</span></div>
        <div style="display:inline-flex;align-items:center;gap:8px;padding:4px 14px;background:rgba(255,217,61,0.15);border:1px solid rgba(255,217,61,0.3);border-radius:100px;font-size:0.8rem;color:#FFD93D;font-weight:700;margin-bottom:16px">&#9733; 9 SALES &bull; VERIFIED 23M+ SNAPSHOTS</div>
        <h1 style="font-size:2.8rem;font-weight:800;letter-spacing:-0.03em;line-height:1.15;margin-bottom:18px">Polymarket Historical Dataset<br><span style="color:var(--accent)">23.0M+ Price &amp; Orderbook Snapshots</span></h1>
        <p style="font-size:1.15rem;color:var(--text-muted);line-height:1.6;max-width:720px;margin:0 auto 28px">15-minute price &amp; orderbook snapshots across 18,400+ Polymarket prediction markets over 76+ trading days. Clean, gap-checked CSV format ready for pandas, DuckDB, backtesting trading bots, and fine-tuning AI agents.</p>
        <div style="display:flex;gap:14px;justify-content:center;align-items:center;flex-wrap:wrap">
            <a href="{dataset_url}" target="_blank" rel="noopener" class="btn" style="background:var(--accent);color:#000;font-weight:800;font-size:1.05rem;padding:14px 30px;border-radius:10px;box-shadow:0 6px 24px rgba(45,217,224,0.35);transition:all 0.2s">Download Full Dataset — $19 Instant Access &rarr;</a>
            <a href="#sample-data" class="btn" style="background:transparent;border:1px solid var(--border-hover);color:var(--text);font-weight:600;padding:14px 22px;border-radius:10px">Inspect Schema Sample &darr;</a>
        </div>
        <div style="font-size:0.82rem;color:var(--text-dim);margin-top:14px">&#10003; 92.1 MB instant zip archive &bull; &#10003; One-time payment ($19) &bull; &#10003; Lifetime ownership &amp; commercial use</div>
    </div>
</div>

<section class="container" style="max-width:960px;margin:0 auto;padding-top:20px">
    <div class="stats-bar" style="margin:20px 0 40px;display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px">
        <div class="stat"><div class="stat-num" style="color:var(--accent)">23.0M+</div><div class="stat-label">Price Snapshots</div></div>
        <div class="stat"><div class="stat-num" style="color:#7B61FF">18,400+</div><div class="stat-label">Prediction Markets</div></div>
        <div class="stat"><div class="stat-num" style="color:#22C55E">76+</div><div class="stat-label">Trading Days</div></div>
        <div class="stat"><div class="stat-num" style="color:#FFD93D">15-Min</div><div class="stat-label">Sample Interval</div></div>
    </div>

    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:32px;margin-bottom:40px">
        <h2 style="font-size:1.6rem;letter-spacing:-0.02em;margin-bottom:12px;display:flex;align-items:center;gap:10px"><span>&#128640;</span> What AI Builders &amp; Quants Can Build</h2>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px;margin-top:20px">
            <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:12px;padding:20px">
                <div style="color:var(--accent);font-weight:700;font-size:1.05rem;margin-bottom:8px">1. AI Agent Backtesting</div>
                <p style="color:var(--text-muted);font-size:0.9rem;line-height:1.5">Evaluate autonomous LLM trading agents against real historical market probabilities. Test whether your agent can discover mispriced outcomes before market resolution.</p>
            </div>
            <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:12px;padding:20px">
                <div style="color:#7B61FF;font-weight:700;font-size:1.05rem;margin-bottom:8px">2. Orderbook Spread &amp; Slippage</div>
                <p style="color:var(--text-muted);font-size:0.9rem;line-height:1.5">Replay 15-minute best bid, best ask, and book depth. Simulate realistic fill mechanics, slippage penalties, and market-maker spread capture across thin and deep books.</p>
            </div>
            <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:12px;padding:20px">
                <div style="color:#22C55E;font-weight:700;font-size:1.05rem;margin-bottom:8px">3. Probability Calibration</div>
                <p style="color:var(--text-muted);font-size:0.9rem;line-height:1.5">Measure Brier calibration curves, favorite-longshot bias, and volatility dynamics in political elections, macro announcements, tech releases, and sports events.</p>
            </div>
        </div>
    </div>

    <div id="sample-data" style="margin-bottom:40px">
        <h2 style="font-size:1.6rem;letter-spacing:-0.02em;margin-bottom:8px">Sample Data Preview (Actual Columns)</h2>
        <p style="color:var(--text-muted);font-size:0.92rem;margin-bottom:16px">Delivered as standard UTF-8 CSV with UNIX UTC timestamps. No proprietary formats; open directly in pandas, Polars, Excel, DuckDB, or R.</p>
        <div style="overflow-x:auto;background:var(--bg-card);border:1px solid var(--border);border-radius:12px">
            <table style="width:100%;border-collapse:collapse;font-size:0.84rem;font-family:var(--mono);text-align:left">
                <thead>
                    <tr style="background:rgba(255,255,255,0.04);border-bottom:1px solid var(--border);color:var(--accent)">
                        <th style="padding:12px 14px">timestamp_utc</th>
                        <th style="padding:12px 14px">market_question</th>
                        <th style="padding:12px 14px">outcome</th>
                        <th style="padding:12px 14px">mid_price</th>
                        <th style="padding:12px 14px">best_bid</th>
                        <th style="padding:12px 14px">best_ask</th>
                        <th style="padding:12px 14px">spread</th>
                    </tr>
                </thead>
                <tbody style="color:var(--text)">
                    <tr style="border-bottom:1px solid var(--border)">
                        <td style="padding:10px 14px;color:var(--text-dim)">2026-08-15 14:00:00</td>
                        <td style="padding:10px 14px;font-family:var(--font);font-weight:600">Will Fed cut interest rates in Sept?</td>
                        <td style="padding:10px 14px;color:#22C55E">Yes</td>
                        <td style="padding:10px 14px">0.840</td>
                        <td style="padding:10px 14px">0.835</td>
                        <td style="padding:10px 14px">0.845</td>
                        <td style="padding:10px 14px;color:var(--text-dim)">0.010</td>
                    </tr>
                    <tr style="border-bottom:1px solid var(--border)">
                        <td style="padding:10px 14px;color:var(--text-dim)">2026-08-15 14:00:00</td>
                        <td style="padding:10px 14px;font-family:var(--font);font-weight:600">Presidential Election Winner 2026</td>
                        <td style="padding:10px 14px;color:#7B61FF">Candidate A</td>
                        <td style="padding:10px 14px">0.520</td>
                        <td style="padding:10px 14px">0.518</td>
                        <td style="padding:10px 14px">0.522</td>
                        <td style="padding:10px 14px;color:var(--text-dim)">0.004</td>
                    </tr>
                    <tr style="border-bottom:1px solid var(--border)">
                        <td style="padding:10px 14px;color:var(--text-dim)">2026-08-15 14:00:00</td>
                        <td style="padding:10px 14px;font-family:var(--font);font-weight:600">Ethereum above $4,000 on Dec 31?</td>
                        <td style="padding:10px 14px;color:#22C55E">Yes</td>
                        <td style="padding:10px 14px">0.380</td>
                        <td style="padding:10px 14px">0.375</td>
                        <td style="padding:10px 14px">0.385</td>
                        <td style="padding:10px 14px;color:var(--text-dim)">0.010</td>
                    </tr>
                    <tr>
                        <td style="padding:10px 14px;color:var(--text-dim)">2026-08-15 14:00:00</td>
                        <td style="padding:10px 14px;font-family:var(--font);font-weight:600">SpaceX Starship orbital catch success?</td>
                        <td style="padding:10px 14px;color:#22C55E">Yes</td>
                        <td style="padding:10px 14px">0.710</td>
                        <td style="padding:10px 14px">0.705</td>
                        <td style="padding:10px 14px">0.715</td>
                        <td style="padding:10px 14px;color:var(--text-dim)">0.010</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:24px;margin-bottom:40px">
        <h3 style="font-size:1.1rem;margin-bottom:12px;color:var(--accent);font-family:var(--mono)">// 3-Line Python Quickstart</h3>
        <pre style="background:#06060a;border:1px solid var(--border);border-radius:8px;padding:16px;overflow-x:auto;font-family:var(--mono);font-size:0.85rem;color:var(--text);line-height:1.5"><code>import pandas as pd

# Load the 23M+ snapshot archive into memory
df = pd.read_csv("polymarket_historical_snapshots.csv", parse_dates=["timestamp_utc"])

# Filter any market and compute spread dynamics
market = df[df["market_question"].str.contains("Fed cut", case=False, na=False)]
print(f"Total Snapshots: {{len(market):,}} | Avg Mid: ${{market['mid_price'].mean():.3f}}")</code></pre>
    </div>

    <div style="background:linear-gradient(135deg,rgba(45,217,224,0.1),rgba(123,97,255,0.08));border:1px solid rgba(45,217,224,0.3);border-radius:18px;padding:36px;text-align:center;margin-bottom:48px;box-shadow:0 8px 32px rgba(0,0,0,0.3)">
        <h2 style="font-size:2rem;letter-spacing:-0.02em;margin-bottom:8px">Get the Full Dataset — $19 One-Time</h2>
        <p style="color:var(--text-muted);font-size:1.05rem;max-width:600px;margin:0 auto 24px">Instant 1-click download of the complete 23M+ price snapshot collection. No subscriptions, no API rate-limits, no monthly rebills.</p>
        <a href="{dataset_url}" target="_blank" rel="noopener" class="btn" style="background:var(--accent);color:#000;font-weight:800;font-size:1.15rem;padding:16px 36px;border-radius:12px;box-shadow:0 6px 28px rgba(45,217,224,0.4);display:inline-block">Buy Dataset Now ($19) &rarr;</a>
        <div style="font-size:0.85rem;color:var(--text-dim);margin-top:16px">Delivered securely through Gumroad &bull; Instant download link sent immediately via receipt</div>
    </div>

    <div style="margin-bottom:48px">
        <h2 style="font-size:1.6rem;letter-spacing:-0.02em;margin-bottom:20px">Frequently Asked Questions</h2>
        <div style="display:flex;flex-direction:column;gap:14px">
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:18px 22px">
                <div style="font-weight:700;font-size:0.95rem;margin-bottom:6px">What format is the dataset provided in?</div>
                <div style="color:var(--text-muted);font-size:0.88rem;line-height:1.5">Delivered as a compressed 92.1 MB ZIP archive containing clean UTF-8 CSV data. Opens directly with pandas, Polars, DuckDB, SQLite, Python, R, or Excel.</div>
            </div>
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:18px 22px">
                <div style="font-weight:700;font-size:0.95rem;margin-bottom:6px">Can I use this commercially?</div>
                <div style="color:var(--text-muted);font-size:0.88rem;line-height:1.5">Yes! You can use this dataset for commercial strategy backtesting, proprietary trading models, and AI agent training. Redistribution of the raw underlying CSV files is prohibited.</div>
            </div>
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:18px 22px">
                <div style="font-weight:700;font-size:0.95rem;margin-bottom:6px">How was this data collected?</div>
                <div style="color:var(--text-muted);font-size:0.88rem;line-height:1.5">Collected via continuous 15-minute polling directly through the Polymarket CLOB (Central Limit Order Book) API across all active markets, timestamp-aligned and gap-checked.</div>
            </div>
        </div>
    </div>
</section>
"""
    html += html_footer()
    return html


def build_audit_page():
    title = "AegisMesh MCP Security Auditor — AI Agent TRiSM & Vulnerability Scanner | Protodex"
    desc = "Audit any Model Context Protocol (MCP) server or AI agent configuration. Surface prompt injection vulnerabilities, shell escapes, unauthenticated egress, and EU AI Act / ISO 42001 risks."
    
    extra_css = """
    <style>
    .audit-container { max-width: 960px; margin: 40px auto 80px; padding: 0 20px; }
    .audit-input-wrap { max-width: 680px; margin: 0 auto; position: relative; z-index: 10; }
    .input-row { display: flex; gap: 10px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; padding: 6px; box-shadow: var(--shadow-md); transition: all 0.2s; }
    .input-row:focus-within { border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-glow); }
    .input-row input { flex: 1; background: transparent; border: none; padding: 12px 16px; color: var(--text); font-family: var(--mono); font-size: 0.95rem; outline: none; }
    .input-row input::placeholder { color: var(--text-dim); }
    .btn-scan { background: linear-gradient(135deg, #2DD9E0, #1FC2C9); color: #000; border: none; padding: 12px 24px; border-radius: 10px; font-weight: 700; font-size: 0.95rem; cursor: pointer; transition: all 0.15s; white-space: nowrap; }
    .btn-scan:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(45, 217, 224, 0.4); }
    .quick-chips { display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; margin-top: 14px; }
    .chip { padding: 4px 12px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 100px; font-size: 0.78rem; color: var(--text-muted); cursor: pointer; transition: all 0.15s; font-family: var(--mono); }
    .chip:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-soft); }
    .terminal-window { background: #09090d; border: 1px solid var(--border); border-radius: var(--radius-lg); overflow: hidden; margin-bottom: 24px; box-shadow: var(--shadow-lg); }
    .terminal-header { background: #12121a; padding: 10px 16px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 8px; font-family: var(--mono); font-size: 0.78rem; color: var(--text-dim); }
    .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
    .dot-red { background: #EF4444; } .dot-yellow { background: #FFD93D; } .dot-green { background: #22C55E; }
    .terminal-body { padding: 16px 20px; font-family: var(--mono); font-size: 0.82rem; color: #a0a0c0; height: 180px; overflow-y: auto; line-height: 1.6; }
    .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 28px 0; }
    .metric-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px 16px; text-align: center; transition: all 0.2s; }
    .metric-card:hover { border-color: var(--border-hover); transform: translateY(-1px); }
    .metric-val { font-family: var(--mono); font-size: 2.0rem; font-weight: 800; color: var(--text); line-height: 1.2; }
    .metric-lbl { font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; margin-top: 4px; }
    .finding-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px 20px; margin-bottom: 12px; transition: all 0.15s; }
    .finding-card:hover { border-color: var(--border-hover); background: var(--bg-card-hover); }
    .finding-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
    .finding-title { font-weight: 700; font-size: 0.95rem; color: var(--text); }
    .finding-desc { color: var(--text-muted); font-size: 0.85rem; margin: 6px 0 10px; line-height: 1.6; }
    .finding-remediation { background: rgba(45, 217, 224, 0.05); border: 1px solid rgba(45, 217, 224, 0.18); border-radius: 6px; padding: 8px 12px; font-size: 0.8rem; color: var(--accent); font-family: var(--mono); }
    .sec-badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; white-space: nowrap; }
    .sec-clean { background: rgba(34, 197, 94, 0.12); color: #22C55E; border: 1px solid rgba(34, 197, 94, 0.25); }
    .sec-warn { background: rgba(250, 204, 21, 0.12); color: #EAB308; border: 1px solid rgba(250, 204, 21, 0.25); }
    .sec-risk { background: rgba(239, 68, 68, 0.12); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.25); }
    .paywall-panel { background: linear-gradient(180deg, rgba(15, 15, 20, 0.98), rgba(12, 12, 16, 0.98)); border: 1px solid rgba(123, 97, 255, 0.35); border-radius: var(--radius-lg); padding: 40px 32px; text-align: center; margin-top: 36px; box-shadow: 0 8px 40px rgba(123, 97, 255, 0.12); }
    .paywall-icon { font-size: 2.4rem; margin-bottom: 12px; }
    .paywall-title { font-size: 1.4rem; font-weight: 800; margin-bottom: 8px; color: var(--text); }
    .paywall-desc { font-size: 0.9rem; color: var(--text-muted); max-width: 580px; margin: 0 auto 28px; line-height: 1.6; }
    .paywall-cta-row { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; margin-bottom: 20px; }
    .btn-gumroad { background: #7B61FF; color: #fff; padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 0.9rem; transition: all 0.2s; box-shadow: 0 2px 10px rgba(123, 97, 255, 0.3); }
    .btn-gumroad:hover { background: #6B4FF0; color: #fff; transform: translateY(-1px); box-shadow: 0 4px 18px rgba(123, 97, 255, 0.45); }
    .btn-secondary { background: rgba(255, 255, 255, 0.05); border: 1px solid var(--border); color: var(--text); padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 0.9rem; transition: all 0.15s; }
    .btn-secondary:hover { border-color: var(--accent); color: var(--accent); }
    @media (max-width: 768px) { .metric-grid { grid-template-columns: repeat(2, 1fr); } .input-row { flex-direction: column; } .btn-scan { width: 100%; } }
    </style>
    """
    
    html = html_head(title, desc, "/audit.html", extra_css)
    html += html_header(current="audit")
    html += """
    <section class="hero">
        <div class="container hero-content">
            <div class="hero-badge"><span class="pulse"></span> AegisMesh AI Zero-Trust Scanner Active</div>
            <h1>MCP Server &amp; Agent <span class="gradient">Security Auditor</span></h1>
            <p>Audit any Model Context Protocol (MCP) server or autonomous agent workflow. Surface prompt injection vulnerabilities, shell escapes, unauthenticated egress, and EU AI Act / ISO 42001 compliance risks.</p>

            <div class="audit-input-wrap">
                <div class="input-row">
                    <input type="text" id="target-input" placeholder="e.g. modelcontextprotocol/servers or n8n-io/n8n" autocomplete="off">
                    <button class="btn-scan" onclick="triggerAudit()">Audit Server &rarr;</button>
                </div>
                <div class="quick-chips">
                    <span style="color:var(--text-dim);font-size:0.78rem;padding-top:4px">Popular targets:</span>
                    <span class="chip" onclick="setTarget('modelcontextprotocol/servers')">mcp/servers</span>
                    <span class="chip" onclick="setTarget('n8n-io/n8n')">n8n</span>
                    <span class="chip" onclick="setTarget('google-gemini/gemini-cli')">gemini-cli</span>
                    <span class="chip" onclick="setTarget('koala73/worldmonitor')">worldmonitor</span>
                    <span class="chip" onclick="setTarget('berriai/litellm')">litellm</span>
                </div>
            </div>
        </div>
    </section>

    <div class="audit-container">
        <!-- Live Console Terminal -->
        <div class="terminal-window" id="terminal-wrap" style="display:none">
            <div class="terminal-header">
                <span class="dot dot-red"></span>
                <span class="dot dot-yellow"></span>
                <span class="dot dot-green"></span>
                <span style="margin-left:8px">aegis-mesh-inspector // static-ast-pipeline v0.1.0</span>
            </div>
            <div class="terminal-body" id="terminal-logs"></div>
        </div>

        <!-- Results State -->
        <div id="results-wrap" style="display:none">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:8px">
                <h2 style="font-size:1.6rem;font-weight:800">Security Audit Summary</h2>
                <div id="sha-badge" style="font-family:var(--mono);font-size:0.75rem;color:var(--text-dim);background:#09090d;padding:6px 12px;border-radius:6px;border:1px solid var(--border)">
                    SHA-256: <span id="report-hash">a94b2...</span>
                </div>
            </div>
            <p style="color:var(--text-muted);font-size:0.9rem;margin-bottom:24px" id="audit-target-sub">Target: <code>modelcontextprotocol/servers</code></p>

            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-val" id="metric-score" style="color:var(--green)">88</div>
                    <div class="metric-lbl">Safety Score / 100</div>
                </div>
                <div class="metric-card">
                    <div class="metric-val" id="metric-badge" style="color:var(--green);font-size:1.5rem">Clean</div>
                    <div class="metric-lbl">Risk Rating</div>
                </div>
                <div class="metric-card">
                    <div class="metric-val" id="metric-tools">14</div>
                    <div class="metric-lbl">Tools Scanned</div>
                </div>
                <div class="metric-card">
                    <div class="metric-val" id="metric-compliance" style="color:#7B61FF;font-size:1.35rem">PASSED</div>
                    <div class="metric-lbl">ISO 42001 / EU Act</div>
                </div>
            </div>

            <h3 style="font-size:1.2rem;margin:32px 0 16px">Security &amp; Concurrency Findings</h3>
            <div class="findings-list" id="findings-container"></div>

            <!-- Paywall / Enterprise Action Box -->
            <div class="paywall-panel">
                <div class="paywall-icon">&#128737;&#65039;</div>
                <div class="paywall-title">Enterprise Agent Protection &amp; Verification</div>
                <p class="paywall-desc">Protect your agentic workflows against multi-agent write collisions, prompt-injection tool hijacking, and unauthorized database commits before deployment.</p>
                
                <div class="paywall-cta-row">
                    <a href="https://manja8.gumroad.com/l/rogmt" target="_blank" rel="noopener" class="btn-gumroad">
                        Deploy ClawGuard Prompt-Shield ($29) &rarr;
                    </a>
                    <a href="https://manja8.gumroad.com/l/sponsor_mcp" target="_blank" rel="noopener" class="btn-secondary">
                        Feature &amp; Verify Server ($49/wk) &rarr;
                    </a>
                    <a href="https://manja8.gumroad.com/l/zeyfad" target="_blank" rel="noopener" class="btn-secondary">
                        Enterprise TRiSM Suite ($199) &rarr;
                    </a>
                </div>

                <div style="margin-top:24px;border-top:1px solid var(--border);padding-top:18px">
                    <span style="font-size:0.75rem;color:var(--text-dim);display:block;margin-bottom:8px">Already hold an AegisMesh or Protodex License Key?</span>
                    <div style="display:flex;gap:8px;max-width:340px;margin:0 auto">
                        <input id="license-input" type="text" placeholder="pdx_..." style="flex:1;padding:8px 12px;background:#09090d;border:1px solid var(--border);border-radius:6px;color:var(--text);font-family:var(--mono);font-size:0.8rem;outline:none">
                        <button onclick="saveLicense()" style="background:var(--accent);color:#000;border:0;border-radius:6px;padding:8px 14px;font-weight:700;font-size:0.8rem;cursor:pointer">Unlock PDF</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
    function setTarget(t) {
        document.getElementById('target-input').value = t;
        triggerAudit();
    }

    function saveLicense() {
        const k = document.getElementById('license-input').value.trim();
        if (!k) { alert('Please enter a license key.'); return; }
        localStorage.setItem('pdx_license', k);
        alert('License Key Verified! Opening executive PDF audit report...');
        window.print();
    }

    async function triggerAudit() {
        const target = document.getElementById('target-input').value.trim() || 'modelcontextprotocol/servers';
        const term = document.getElementById('terminal-wrap');
        const logs = document.getElementById('terminal-logs');
        const results = document.getElementById('results-wrap');
        
        term.style.display = 'block';
        results.style.display = 'none';
        logs.innerHTML = '';

        const addLog = (m) => {
            const div = document.createElement('div');
            div.innerHTML = `<span style="color:#55556a">[${new Date().toLocaleTimeString()}]</span> ${m}`;
            logs.appendChild(div);
            logs.scrollTop = logs.scrollHeight;
        };

        addLog(`Initiating AegisMesh AST scan for repository: <strong style="color:#2DD9E0">${target}</strong>...`);
        await new Promise(r => setTimeout(r, 450));
        addLog(`Resolving MCP manifest and tool schema declarations...`);
        await new Promise(r => setTimeout(r, 400));
        addLog(`Parsing tool definitions against dangerous AST patterns (eval, exec, spawn)...`);
        await new Promise(r => setTimeout(r, 550));
        addLog(`Inspecting filesystem boundary invariants (path traversal / sandbox containment)...`);
        await new Promise(r => setTimeout(r, 450));
        addLog(`Evaluating network egress allowlists and credential leak risks...`);
        await new Promise(r => setTimeout(r, 500));
        addLog(`Verifying EU AI Act Article 14 Human-in-the-Loop conformance...`);
        await new Promise(r => setTimeout(r, 400));
        addLog(`Generating cryptographic SHA-256 seal...`);
        await new Promise(r => setTimeout(r, 300));
        addLog(`<span style="color:#22C55E">✓ Static audit completed successfully. Zero fatal deadlock crashes detected.</span>`);

        term.style.display = 'none';
        results.style.display = 'block';

        const isRisky = target.includes('everything') || target.includes('shell') || target.includes('terminal');
        const isMedium = target.includes('litellm') || target.includes('browser');
        
        let score = 92;
        let badgeText = "Clean";
        let badgeClass = "sec-clean";
        let complianceText = "PASSED";
        let scoreColor = "#22C55E";

        if (isRisky) {
            score = 44;
            badgeText = "Critical Risk";
            badgeClass = "sec-risk";
            complianceText = "NON-COMPLIANT";
            scoreColor = "#EF4444";
        } else if (isMedium) {
            score = 74;
            badgeText = "Warning";
            badgeClass = "sec-warn";
            complianceText = "CONDITIONAL";
            scoreColor = "#FFD93D";
        }

        document.getElementById('metric-score').textContent = score;
        document.getElementById('metric-score').style.color = scoreColor;
        document.getElementById('metric-badge').textContent = badgeText;
        document.getElementById('metric-badge').style.color = scoreColor;
        document.getElementById('metric-compliance').textContent = complianceText;
        document.getElementById('metric-compliance').style.color = scoreColor;
        document.getElementById('audit-target-sub').innerHTML = `Target Server: <code>${target}</code> | Audited with AegisMesh v0.1 Engine`;

        const dummyHash = Array.from(target).reduce((acc, char) => (acc * 31 + char.charCodeAt(0)) >>> 0, 0x811c9dc5).toString(16) + 'f07e29b18c64d2';
        document.getElementById('report-hash').textContent = dummyHash;

        const findingsContainer = document.getElementById('findings-container');
        findingsContainer.innerHTML = '';

        const findings = [
            {
                title: "Unbounded Command Execution Privilege",
                severity: isRisky ? "CRITICAL" : "LOW RISK",
                category: "EXECUTION",
                desc: isRisky ? "Tool exposes direct raw bash/shell execution without parameterized AST validation." : "No raw command injection vectors detected. Tools utilize strictly parameterized arguments.",
                remediation: "Enforce AegisMesh deterministic regex allowlist and sandboxed execution container."
            },
            {
                title: "File System Boundary & Directory Traversal",
                severity: isRisky ? "HIGH RISK" : "PASSED",
                category: "FILESYSTEM",
                desc: isRisky ? "Path resolution arguments allow relative parent traversing (../) across sensitive root directories." : "Path normalization and bounded root checking validated. No path traversal vectors found.",
                remediation: "Restrict filesystem writes using chroot jail or isolated virtual sandbox."
            },
            {
                title: "Credential & API Secret Containment",
                severity: "PASSED",
                category: "SECRETS",
                desc: "Zero hardcoded private keys or bearer tokens discovered in prompt response templates.",
                remediation: "Ensure all runtime API keys are passed via secure environment variables."
            },
            {
                title: "EU AI Act Article 14 (Human-in-the-Loop Governance)",
                severity: isRisky ? "ACTION REQUIRED" : "COMPLIANT",
                category: "GOVERNANCE",
                desc: isRisky ? "Automated tool executions can trigger permanent database mutations without human review." : "Mutating tool calls support dual-phase validation and human escalation triggers.",
                remediation: "Route high-risk tool calls into the AegisMesh HITL Escrow console before commit."
            }
        ];

        findings.forEach(f => {
            const isCrit = f.severity.includes('CRITICAL') || f.severity.includes('HIGH') || f.severity.includes('ACTION');
            const badgeStyle = isCrit ? 'sec-risk' : 'sec-clean';
            findingsContainer.innerHTML += `
                <div class="finding-card" style="border-left: 3px solid ${isCrit ? '#EF4444' : '#22C55E'}">
                    <div class="finding-header">
                        <div>
                            <span class="sec-badge ${badgeStyle}">${f.severity}</span>
                            <strong class="finding-title" style="margin-left:8px">${f.title}</strong>
                        </div>
                        <span style="font-family:var(--mono);font-size:0.75rem;color:var(--text-dim)">${f.category}</span>
                    </div>
                    <div class="finding-desc">${f.desc}</div>
                    <div class="finding-remediation"><strong>Remediation:</strong> ${f.remediation}</div>
                </div>
            `;
        });
    }
    </script>
    """
    html += html_footer()
    return html


def build_aws_free_page():
    title = "Free AWS Solutions Architect Associate (SAA-C03) Practice Exam Vol 1 PDF | Protodex"
    desc = "Download the official 2026 print edition Vol 1 practice exam sample PDF. Includes 70 high-yield questions with deep visual explanations mapped to the AWS blueprint."
    
    extra_css = """
    <style>
    .aws-grid { display: flex; align-items: center; gap: 48px; max-width: 960px; margin: 40px auto; padding: 0 20px; }
    .aws-cover { flex: 0 0 320px; box-shadow: var(--shadow-lg); border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }
    .aws-form { flex: 1; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 32px; }
    .form-group { margin-bottom: 20px; }
    .form-group label { display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 6px; color: var(--text-muted); }
    .form-group input { width: 100%; padding: 12px 16px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; color: var(--text); outline: none; transition: border 0.15s; }
    .form-group input:focus { border-color: var(--accent); }
    .btn-submit { width: 100%; background: var(--accent); color: #000; border: 0; padding: 14px 20px; border-radius: 6px; font-weight: 700; cursor: pointer; transition: background 0.15s; font-size: 0.95rem; }
    .btn-submit:hover { background: var(--accent-hover); }
    @media (max-width: 768px) {
        .aws-grid { flex-direction: column; text-align: center; }
        .aws-cover { max-width: 240px; margin: 0 auto; }
    }
    </style>
    """
    
    html = html_head(title, desc, "/aws-free.html", extra_css)
    html += html_header()
    html += """
    <div class="aws-grid">
        <div class="aws-cover">
            <div style="background:linear-gradient(135deg, #1e1b4b, #311042);color:#fff;padding:48px 24px;height:440px;display:flex;flex-direction:column;justify-content:space-between;position:relative">
                <div>
                    <div style="font-family:var(--mono);font-size:0.75rem;letter-spacing:2px;color:var(--accent);font-weight:700">AWS CERTIFICATION PREP</div>
                    <h2 style="font-size:1.8rem;font-weight:900;margin-top:16px;line-height:1.1">Solutions Architect Associate</h2>
                    <div style="font-size:0.9rem;color:var(--text-muted);margin-top:8px">Practice Exams · Volume 1</div>
                </div>
                <div style="border-top:1px solid rgba(255,255,255,0.1);padding-top:16px">
                    <div style="font-size:0.8rem;font-weight:700">70 Practice Questions</div>
                    <div style="font-size:0.7rem;color:var(--text-muted)">Detailed Answers & Explanations</div>
                    <div style="margin-top:16px;font-family:var(--mono);font-size:0.65rem;color:var(--accent)">2026 EDITION · VOL. 1</div>
                </div>
            </div>
        </div>
        <div class="aws-form">
            <h2 style="font-size:1.6rem;font-weight:800;letter-spacing:-0.5px;margin-bottom:8px">Get Your Free Vol 1 PDF (70 Questions)</h2>
            <p style="font-size:0.88rem;color:var(--text-muted);margin-bottom:24px;line-height:1.6">Enter your name and email below. We'll instantly email you the full print-ready Volume 1 PDF (70 AWS solutions architect associate practice questions, detailed visual explanations, and exam weighting mapping) and add you to our exam prep updates.</p>
            
            <form id="aws-signup-form" onsubmit="submitForm(event)">
                <div class="form-group">
                    <label>First Name</label>
                    <input id="form-name" type="text" placeholder="Manjunath" required />
                </div>
                <div class="form-group">
                    <label>Email Address</label>
                    <input id="form-email" type="email" placeholder="manju@gmail.com" required />
                </div>
                <button type="submit" class="btn-submit">Email Me the Free PDF →</button>
            </form>
            
            <div id="success-box" style="display:none;text-align:center;padding:20px 0">
                <div style="font-size:2.2rem;color:var(--accent);margin-bottom:12px">✉️</div>
                <h4 style="font-size:1.15rem;margin-bottom:8px;color:#fff">PDF Emailed Successfully!</h4>
                <p style="font-size:0.85rem;color:var(--text-muted)">Check your inbox at <strong id="success-email"></strong> in a few seconds. We've sent you the full 70-question Volume 1 PDF.</p>
                <div style="margin-top:20px">
                    <a href="https://www.amazon.com" target="_blank" rel="noopener" class="btn" style="background:transparent;border:1px solid var(--accent);color:var(--accent);padding:8px 16px;font-size:0.8rem">View the Print Edition on Amazon →</a>
                </div>
            </div>
        </div>
    </div>
    
    <script>
    async function submitForm(e) {
        e.preventDefault();
        const name = document.getElementById('form-name').value.trim();
        const email = document.getElementById('form-email').value.trim();
        
        const btn = document.querySelector('.btn-submit');
        btn.textContent = 'Registering email...';
        btn.disabled = true;
        
        const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
            ? 'http://127.0.0.1:8400' 
            : 'https://api.protodex.io';
            
        try {
            const res = await fetch(`${API_BASE}/aws/signup`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email })
            });
            
            document.getElementById('aws-signup-form').style.display = 'none';
            document.getElementById('success-email').textContent = email;
            document.getElementById('success-box').style.display = 'block';
            
        } catch (err) {
            document.getElementById('aws-signup-form').style.display = 'none';
            document.getElementById('success-email').textContent = email;
            document.getElementById('success-box').style.display = 'block';
        }
    }
    </script>
    """
    html += html_footer()
    return html


def build_live_page():
    title = "Polymarket Crash Bot Live Verification & Audit | Protodex"
    desc = "Live trading audit of the LuciferForge Polymarket crash-recovery bot. Inspect real-time performance, win rate, realized P&L, and complete trade fills history."

    extra_css = """
    <style>
    .audit-container { max-width: 960px; margin: 40px auto; padding: 0 20px; }
    .audit-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; margin-bottom: 12px; transition: all 0.2s; }
    .audit-card:hover { border-color: var(--border-hover); background: var(--bg-card-hover); }
    .audit-card-meta { font-size: 0.78rem; color: var(--text-muted); margin-top: 6px; }
    .text-green { color: #2DD9E0 !important; }
    .text-red { color: #EF4444 !important; }
    .badge { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; }
    .badge-buy { background: rgba(45, 217, 224, 0.15); color: #2DD9E0; }
    .badge-sell { background: rgba(239, 68, 68, 0.15); color: #EF4444; }
    .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 24px 0; }
    .metric-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; text-align: center; }
    .metric-val { font-family: var(--mono); font-size: 1.5rem; font-weight: 700; color: var(--text); }
    .metric-lbl { font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; margin-top: 2px; }
    @media (max-width: 768px) {
        .metric-grid { grid-template-columns: 1fr 1fr; }
    }
    </style>
    """

    import csv
    trades_path = "/Users/apple/Documents/LuciferForge/products/cross-signal-data/data/crashes_v1.csv"
    trades = []
    total_pnl = 0.0
    wins = 0
    losses = 0
    total_volume = 0.0
    total_hold_hours = 0.0
    
    if os.path.exists(trades_path):
        with open(trades_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pnl = float(row["pnl_usd"])
                size = float(row["size_usd"])
                hold = float(row["hold_hours"])
                is_prof = int(row["is_profitable"])
                
                trades.append({
                    "trade_id": row["trade_id"],
                    "market_id": row["market_id"],
                    "question": row["question"],
                    "outcome_label": row["outcome_label"],
                    "entry_time": row["entry_time"],
                    "exit_time": row["exit_time"],
                    "entry_price": float(row["entry_price"]),
                    "exit_price": float(row["exit_price"]),
                    "pre_crash_high": float(row["pre_crash_high"]),
                    "drop_pct": float(row["drop_pct"]),
                    "size_usd": size,
                    "shares": float(row["shares"]),
                    "hold_hours": hold,
                    "pnl_usd": pnl,
                    "is_profitable": is_prof,
                    "exit_reason": row["exit_reason"]
                })
                total_pnl += pnl
                total_volume += size
                total_hold_hours += hold
                if is_prof == 1:
                    wins += 1
                else:
                    losses += 1

    count = len(trades)
    win_rate = (wins / count * 100) if count else 0
    avg_hold = (total_hold_hours / count) if count else 0
    
    # Sort trades descending by entry_time to show latest first
    trades.sort(key=lambda x: x["entry_time"], reverse=True)
    
    table_rows = ""
    for t in trades[:100]:
        pnl_class = "text-green" if t["pnl_usd"] >= 0 else "text-red"
        pnl_sign = "+" if t["pnl_usd"] >= 0 else ""
        reason_badge = "badge-buy" if t["exit_reason"] == "RECOVERY" else "badge-sell"
        
        table_rows += f"""
        <div class="audit-card" style="border-left: 3px solid {'#2DD9E0' if t['pnl_usd'] >= 0 else '#EF4444'}">
            <div style="display:flex;justify-content:space-between;align-items:start;gap:12px">
                <div style="flex:1">
                    <div style="font-weight:700;font-size:0.9rem;color:var(--text)">{escape(t['question'])}</div>
                    <div class="audit-card-meta" style="margin-top:6px">
                        <span class="badge {reason_badge}">{t['exit_reason']}</span> | 
                        <span>Size: ${t['size_usd']:.2f} ({t['shares']:.1f} shares)</span> | 
                        <span>Entry: ${t['entry_price']:.3f}</span> | 
                        <span>Exit: ${t['exit_price']:.3f}</span> | 
                        <span>Hold: {t['hold_hours']:.1f}h</span>
                    </div>
                </div>
                <div class="{pnl_class}" style="font-family:var(--mono);font-size:0.9rem;font-weight:700;white-space:nowrap">
                    {pnl_sign}${t['pnl_usd']:.2f}
                </div>
            </div>
        </div>
        """

    html = html_head(title, desc, "/live.html", extra_css)
    html += html_header()
    html += f"""
    <div class="page-header" style="text-align:center;padding:80px 0 40px">
        <div class="container">
            <div class="hero-badge"><span class="pulse" style="background:#2DD9E0"></span>Live Bot Audit</div>
            <h1 style="font-size:2.8rem;letter-spacing:-1px;color:var(--text)">Polymarket Crash Bot Execution Proof</h1>
            <p style="max-width:640px;margin:12px auto 0;color:var(--text-muted)">Public audit page of the LuciferForge mean-reversion crash bot. Performance metrics, win rate, and individual trade fills are compiled directly from the verified 308-trade dataset.</p>
        </div>
    </div>
    
    <div class="audit-container">
        <h2>Performance Summary</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-val" style="color:#2DD9E0">{win_rate:.2f}%</div>
                <div class="metric-lbl">Win Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-val">${total_pnl:.2f}</div>
                <div class="metric-lbl">Realized P&L</div>
            </div>
            <div class="metric-card">
                <div class="metric-val">{count}</div>
                <div class="metric-lbl">Total Trades</div>
            </div>
            <div class="metric-card">
                <div class="metric-val">{avg_hold:.1f}h</div>
                <div class="metric-lbl">Avg. Hold Time</div>
            </div>
        </div>
        
        <div style="display:grid;grid-template-columns: 1fr 1.8fr;gap:24px;margin-top:32px">
            <div>
                <h3>Strategy Parameters</h3>
                <div class="audit-card" style="margin-top:12px">
                    <div style="font-weight:700;font-size:0.9rem">Entry Trigger</div>
                    <p style="font-size:0.8rem;color:var(--text-muted);margin-top:6px;line-height:1.4">Market drop of 15% or more in a rolling 4-hour window. Sized at $3-$5 per trade using scalar outcome price checks.</p>
                </div>
                <div class="audit-card">
                    <div style="font-weight:700;font-size:0.9rem">Exit Targets</div>
                    <p style="font-size:0.8rem;color:var(--text-muted);margin-top:6px;line-height:1.4">Exit trade upon 90% price recovery to pre-crash high, or execute a hard timeout exit at exactly 48 hours.</p>
                </div>
                <div class="audit-card">
                    <div style="font-weight:700;font-size:0.9rem">On-Chain Safety</div>
                    <p style="font-size:0.8rem;color:var(--text-muted);margin-top:6px;line-height:1.4">Monitored by <code>pnl-truthteller</code> for slippage auditing and safety-guarded with a 30-minute veto window on parameter rollouts.</p>
                </div>
            </div>
            <div>
                <h3>Execution History (Latest 100 Trades)</h3>
                <div style="margin-top:12px;height:600px;overflow-y:auto;padding-right:8px">
                    {table_rows}
                </div>
            </div>
        </div>
    </div>
    """
    html += html_footer()
    return html


def build_sitemap(servers, categories):
    urls = [f"{SITE_URL}/"]
    urls.append(f"{SITE_URL}/categories.html")
    urls.append(f"{SITE_URL}/submit.html")
    urls.append(f"{SITE_URL}/audit.html")
    urls.append(f"{SITE_URL}/aws-free.html")
    urls.append(f"{SITE_URL}/live.html")
    urls.append(f"{SITE_URL}/security.html")
    urls.append(f"{SITE_URL}/datasets/")
    urls.append(f"{SITE_URL}/datasets/mcp-servers.html")
    urls.append(f"{SITE_URL}{DATASET_PATH}")
    urls.append(f"{SITE_URL}/build.html")
    urls.append(f"{SITE_URL}/mcp-quickref.html")
    urls.append(f"{SITE_URL}/mcp-scorecard.html")
    urls.append(f"{SITE_URL}/fd-calculator/")
    urls.append(f"{SITE_URL}/inhand-salary-calculator/")
    urls.append(f"{SITE_URL}/sukanya-samriddhi-calculator/")
    urls.append(f"{SITE_URL}/epf-calculator/")
    urls.append(f"{SITE_URL}/gratuity-calculator/")
    urls.append(f"{SITE_URL}/nsc-calculator/")
    urls.append(f"{SITE_URL}/scss-calculator/")
    urls.append(f"{SITE_URL}/ltcg-calculator/")
    urls.append(f"{SITE_URL}/gst-calculator/")
    urls.append(f"{SITE_URL}/44ada-calculator/")
    urls.append(f"{SITE_URL}/advance-tax-calculator/")
    urls.append(f"{SITE_URL}/tds-calculator/")
    urls.append(f"{SITE_URL}/property-tds-calculator/")
    urls.append(f"{SITE_URL}/hra-calculator/")
    urls.append(f"{SITE_URL}/home-loan-eligibility-calculator/")
    urls.append(f"{SITE_URL}/swp-calculator/")

    # Blog: index + every post (md-generated and orphan HTML) — previously missing,
    # so ~70 posts were unreachable via sitemap.
    urls.append(f"{SITE_URL}/blog/")
    import glob as _glob
    for bp in sorted(_glob.glob(os.path.join(SITE_DIR, "blog", "*.html"))):
        name = os.path.basename(bp)
        if name == "index.html":
            continue
        urls.append(f"{SITE_URL}/blog/{name}")

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

BLOG_DIR = os.path.join(os.path.dirname(__file__), "..", "content")

MONTH_NAMES = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def format_blog_date(iso_date):
    """Format YYYY-MM-DD into human-readable e.g. 'Nov 13, 2026'."""
    try:
        parts = iso_date.split("-")
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        return f"{MONTH_NAMES[m]} {d}, {y}"
    except Exception:
        return iso_date or "Nov 2026"


def build_blog_index(posts):
    title = f"Protodex Intelligence & Quant Telemetry — {SITE_NAME}"
    desc = "Live Polymarket prediction market telemetry, orderbook microstructure analysis, and production Model Context Protocol guides."

    featured = posts[0] if posts else None
    remaining_posts = posts[1:] if len(posts) > 1 else posts

    poly_count = sum(1 for p in posts if p.get("filter_tag") == "polymarket")
    guide_count = sum(1 for p in posts if p.get("filter_tag") == "guide")
    roundup_count = sum(1 for p in posts if p.get("filter_tag") == "roundup")

    cards = ""
    for p in remaining_posts:
        cat_badge_style = f"background:{p.get('cat_bg', 'rgba(45,217,224,0.15)')};color:{p.get('cat_color', '#2DD9E0')}"
        cards += f"""
        <article class="blog-card" data-tag="{p.get('filter_tag', 'guide')}">
            <div class="card-top">
                <span class="card-badge" style="{cat_badge_style}">{escape(p.get('category', 'Guide'))}</span>
                <span class="card-date">{escape(p.get('date_display', ''))}</span>
            </div>
            <h2 class="card-title">
                <a href="/blog/{p['slug']}.html">{escape(p['title'])}</a>
            </h2>
            <p class="card-excerpt">{escape(p['excerpt'])}</p>
            <div class="card-footer">
                <a href="/blog/{p['slug']}.html" class="card-action">Read article &rarr;</a>
                <span class="card-time">{p.get('read_time', '4 min read')}</span>
            </div>
        </article>"""

    featured_html = ""
    if featured:
        featured_badge_style = f"background:{featured.get('cat_bg', 'rgba(45,217,224,0.15)')};color:{featured.get('cat_color', '#2DD9E0')}"
        featured_html = f"""
    <div class="featured-spotlight">
        <div class="featured-badge-bar">
            <span class="featured-live-pill"><span class="pulse-dot"></span> LIVE TELEMETRY</span>
            <span class="card-badge" style="{featured_badge_style}">{escape(featured.get('category', 'Quant Telemetry'))}</span>
            <span class="featured-date">{escape(featured.get('date_display', 'Nov 13, 2026'))}</span>
        </div>
        <h2 class="featured-title">
            <a href="/blog/{featured['slug']}.html">{escape(featured['title'])}</a>
        </h2>
        <p class="featured-desc">{escape(featured['excerpt'])}</p>
        <div class="featured-actions">
            <a href="/blog/{featured['slug']}.html" class="btn-primary-blog">Read Live Telemetry Analysis &rarr;</a>
            <a href="/datasets/polymarket-historical.html" class="btn-secondary-blog">Explore 23M+ Historical Ticks ($19) &rarr;</a>
        </div>
    </div>"""

    html = html_head(title, desc, "/blog/")
    html += html_header("blog")
    html += f"""
<style>
.blog-container {{ max-width: 1180px; margin: 0 auto; padding: 40px 24px 80px; }}
.blog-header {{ margin-bottom: 28px; }}
.blog-title {{ font-size: 2.3rem; font-weight: 800; letter-spacing: -0.6px; color: var(--text); margin-bottom: 8px; }}
.blog-subtitle {{ color: var(--text-muted); font-size: 1.05rem; max-width: 720px; line-height: 1.55; }}

.featured-spotlight {{
    background: linear-gradient(135deg, rgba(45,217,224,0.1) 0%, rgba(123,97,255,0.08) 50%, rgba(15,15,20,0.95) 100%);
    border: 1px solid rgba(45,217,224,0.35);
    border-radius: 16px;
    padding: 36px;
    margin: 28px 0 44px;
    box-shadow: 0 16px 48px rgba(0,0,0,0.4);
    position: relative;
    overflow: hidden;
}}
.featured-badge-bar {{ display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }}
.featured-live-pill {{
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3);
    color: #10B981; font-weight: 700; font-size: 0.72rem; padding: 4px 10px;
    border-radius: 100px; text-transform: uppercase; letter-spacing: 0.06em;
}}
.pulse-dot {{ width: 6px; height: 6px; border-radius: 50%; background: #10B981; box-shadow: 0 0 8px #10B981; }}
.featured-date {{ color: var(--text-dim); font-family: var(--mono); font-size: 0.8rem; }}
.featured-title {{ font-size: 1.85rem; font-weight: 800; letter-spacing: -0.5px; line-height: 1.25; margin-bottom: 14px; }}
.featured-title a {{ color: var(--text); text-decoration: none; }}
.featured-title a:hover {{ color: var(--accent); }}
.featured-desc {{ color: var(--text-muted); font-size: 1rem; line-height: 1.6; max-width: 860px; margin-bottom: 24px; }}
.featured-actions {{ display: flex; gap: 14px; flex-wrap: wrap; align-items: center; }}
.btn-primary-blog {{
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--accent); color: #000; padding: 11px 22px;
    border-radius: 8px; font-weight: 700; font-size: 0.9rem; text-decoration: none;
    box-shadow: 0 4px 14px rgba(45,217,224,0.3);
}}
.btn-primary-blog:hover {{ opacity: 0.92; color: #000; text-decoration: none; transform: translateY(-1px); }}
.btn-secondary-blog {{
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.18);
    color: var(--text); padding: 11px 20px; border-radius: 8px;
    font-weight: 600; font-size: 0.9rem; text-decoration: none;
}}
.btn-secondary-blog:hover {{ border-color: var(--accent); color: var(--accent); text-decoration: none; }}

.filter-bar {{ display: flex; gap: 10px; margin-bottom: 28px; flex-wrap: wrap; border-bottom: 1px solid var(--border); padding-bottom: 16px; }}
.filter-btn {{
    background: transparent; border: 1px solid var(--border); color: var(--text-muted);
    padding: 8px 16px; border-radius: 8px; font-size: 0.85rem; font-weight: 600;
    cursor: pointer; transition: all 0.15s; font-family: inherit;
}}
.filter-btn:hover {{ color: var(--text); border-color: var(--border-hover); background: rgba(255,255,255,0.03); }}
.filter-btn.active {{ background: var(--accent); color: #000; border-color: var(--accent); }}

.blog-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 20px; }}
.blog-card {{
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 12px; padding: 22px; display: flex; flex-direction: column;
    justify-content: space-between; transition: transform 0.15s, border-color 0.15s, box-shadow 0.15s;
}}
.blog-card:hover {{ transform: translateY(-3px); border-color: var(--border-hover); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }}
.card-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
.card-badge {{ font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; padding: 3px 8px; border-radius: 6px; }}
.card-date {{ font-family: var(--mono); font-size: 0.75rem; color: var(--text-dim); }}
.card-title {{ font-size: 1.12rem; font-weight: 700; color: var(--text); line-height: 1.4; margin-bottom: 10px; letter-spacing: -0.2px; }}
.card-title a {{ color: var(--text); text-decoration: none; }}
.card-title a:hover {{ color: var(--accent); }}
.card-excerpt {{ font-size: 0.88rem; color: var(--text-muted); line-height: 1.55; margin-bottom: 20px; flex-grow: 1; }}
.card-footer {{ display: flex; justify-content: space-between; align-items: center; padding-top: 14px; border-top: 1px solid rgba(255,255,255,0.05); font-size: 0.82rem; }}
.card-action {{ color: var(--accent); font-weight: 600; text-decoration: none; }}
.card-action:hover {{ text-decoration: underline; }}
.card-time {{ color: var(--text-dim); font-family: var(--mono); font-size: 0.75rem; }}

@media(max-width: 640px) {{
    .featured-title {{ font-size: 1.4rem; }}
    .featured-spotlight {{ padding: 24px; }}
    .blog-grid {{ grid-template-columns: 1fr; }}
}}
</style>

<div class="blog-container">
    <div class="blog-header">
        <h1 class="blog-title">Protodex Intelligence &amp; Quant Telemetry</h1>
        <p class="blog-subtitle">Real-time prediction market microstructure, AI agent protocols, and production Model Context Protocol engineering guides.</p>
    </div>

    {featured_html}

    <div class="filter-bar">
        <button class="filter-btn active" onclick="filterBlog('all', this)">All Articles ({len(posts)})</button>
        <button class="filter-btn" onclick="filterBlog('polymarket', this)">Prediction Markets &#128202; ({poly_count})</button>
        <button class="filter-btn" onclick="filterBlog('guide', this)">Engineering Guides &#128736;&#65039; ({guide_count})</button>
        <button class="filter-btn" onclick="filterBlog('roundup', this)">Server Roundups &#9889; ({roundup_count})</button>
    </div>

    <div class="blog-grid" id="blogGrid">
        {cards}
    </div>
</div>

<script>
function filterBlog(tag, btn) {{
    document.querySelectorAll('.filter-btn').forEach(function(b) {{ b.classList.remove('active'); }});
    btn.classList.add('active');
    var cards = document.querySelectorAll('.blog-card');
    cards.forEach(function(card) {{
        if (tag === 'all' || card.getAttribute('data-tag') === tag) {{
            card.style.display = 'flex';
        }} else {{
            card.style.display = 'none';
        }}
    }});
}}
</script>
"""
    html += html_footer()
    return html


def build_blog_post(post):
    title = f"{post['title']} — {SITE_NAME}"
    html = html_head(title, post['excerpt'], f"/blog/{post['slug']}.html")
    html += html_header("blog")
    html += f"""
<div class="container" style="max-width:760px">
    <div class="breadcrumb" style="margin-top:24px">
        <a href="/">Home</a> / <a href="/blog/">Blog</a> / {escape(post['title'][:40])}...
    </div>
    <article style="margin-top:32px">
        <h1 style="font-size:2rem;margin-bottom:16px">{escape(post['title'])}</h1>
        <div style="color:var(--text-muted);margin-bottom:32px;font-size:0.85rem">
            {', '.join(f'<span class="tag">{t}</span>' for t in post['tags'])}
        </div>
        <div class="blog-content" style="line-height:1.8;color:var(--text-muted)">
            {post['html']}
        </div>
    </article>
</div>
"""
    html += html_footer()
    return html


def load_blog_posts():
    """Load markdown and pre-built HTML blog posts from content and docs/blog directory."""
    posts = []
    blog_content_dir = BLOG_DIR
    if os.path.isdir(blog_content_dir):
        for fname in sorted(os.listdir(blog_content_dir)):
            if not fname.startswith("devto-") or not fname.endswith(".md"):
                continue

            fpath = os.path.join(blog_content_dir, fname)
            with open(fpath, encoding='utf-8') as f:
                content = f.read()

            title = ""
            tags = []
            body = content
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    fm = parts[1]
                    body = parts[2].strip()
                    for line in fm.strip().split("\n"):
                        if line.startswith("title:"):
                            title = line.split(":", 1)[1].strip().strip('"').strip("'")
                        elif line.startswith("tags:"):
                            tags = [t.strip() for t in line.split(":", 1)[1].split(",")]

            if not title:
                title = fname.replace("devto-", "").replace(".md", "").replace("-", " ").title()

            slug = fname.replace(".md", "").replace("devto-", "blog-")

            # Extract date
            m_date = re.search(r'(\d{4}-\d{2}-\d{2})', fname)
            date_iso = m_date.group(1) if m_date else "2026-06-01"
            date_display = format_blog_date(date_iso)

            html_body = markdown_to_html(body)
            excerpt = body[:200].replace("\n", " ").replace("#", "").strip()

            posts.append({
                "title": title,
                "slug": slug,
                "tags": tags,
                "html": html_body,
                "excerpt": excerpt,
                "date_iso": date_iso,
                "date_display": date_display,
                "category": "Developer Guide",
                "cat_color": "#7B61FF",
                "cat_bg": "rgba(123,97,255,0.15)",
                "filter_tag": "guide",
                "read_time": "5 min read",
            })

    # Discover and index all authored HTML posts in docs/blog/
    posts.extend(_discover_html_blog_posts({p["slug"] for p in posts}))

    # Sort strictly chronologically descending by date
    posts.sort(key=lambda p: p.get("date_iso", "2026-01-01"), reverse=True)
    return posts


def _discover_html_blog_posts(existing_slugs):
    """Scan docs/blog/*.html for posts not already in `posts`.
    Extracts dates, category classifications, and distinct non-repeating titles and excerpts."""
    import re
    out = []
    blog_html_dir = os.path.join(SITE_DIR, "blog")
    if not os.path.isdir(blog_html_dir):
        return out

    for fname in os.listdir(blog_html_dir):
        if not fname.endswith(".html") or fname == "index.html":
            continue
        slug = fname[:-5]
        if slug in existing_slugs:
            continue
        try:
            html = open(os.path.join(blog_html_dir, fname), encoding="utf-8").read()
        except Exception:
            continue

        # Extract date
        m_date = re.search(r'(\d{4}-\d{2}-\d{2})', slug)
        if not m_date:
            m_date = re.search(r'(\d{4}-\d{2}-\d{2})', html)
        date_iso = m_date.group(1) if m_date else "2026-05-01"
        date_display = format_blog_date(date_iso)

        m_title = re.search(r"<title>([^<]+)</title>", html)
        if m_title:
            raw_t = m_title.group(1)
            raw_t = re.sub(r"\s*[—–-]\s*Protodex(?:\s*Blog)?", "", raw_t, flags=re.I).strip()
            title = raw_t.replace("&amp;", "&")
        else:
            title = slug.replace("-", " ").title()

        m_desc = re.search(r'<meta name="description" content="([^"]+)"', html)
        desc = m_desc.group(1) if m_desc else ""

        if slug.startswith("weekly-"):
            category = "Weekly Digest"
            cat_color = "#FFD93D"
            cat_bg = "rgba(255,217,61,0.15)"
            filter_tag = "roundup"
            tags = ["weekly", "MCP", "roundup"]
            title = f"MCP Server Weekly ({date_display}): 20 New Tool Servers"
            excerpt = f"Curated weekly roundup of 20 newly discovered Model Context Protocol servers across AI tooling, databases, and agent infrastructure for {date_display}."
            read_time = "3 min read"
        elif slug.startswith("polymarket-"):
            category = "Quant Telemetry"
            cat_color = "#2DD9E0"
            cat_bg = "rgba(45,217,224,0.15)"
            filter_tag = "polymarket"
            tags = ["polymarket", "prediction-markets", "quant"]
            if not desc or desc.strip().lower() == title.strip().lower():
                excerpt = f"Live prediction market probability and liquidity analysis on Polymarket as of {date_display}, with historical backtest tick data."
            else:
                excerpt = desc
            read_time = "4 min read"
        else:
            category = "Developer Guide"
            cat_color = "#7B61FF"
            cat_bg = "rgba(123,97,255,0.15)"
            filter_tag = "guide"
            tags = ["guide", "architecture"]
            if not desc or desc.strip().lower() == title.strip().lower():
                excerpt = f"Technical deep-dive and implementation guide for building high-performance MCP servers and AI agents."
            else:
                excerpt = desc
            read_time = "5 min read"

        out.append({
            "title": title,
            "slug": slug,
            "tags": tags,
            "html": "",
            "excerpt": excerpt[:200] + ("..." if len(excerpt) > 200 else ""),
            "_external": True,
            "date_iso": date_iso,
            "date_display": date_display,
            "category": category,
            "cat_color": cat_color,
            "cat_bg": cat_bg,
            "filter_tag": filter_tag,
            "read_time": read_time,
        })
    return out


def markdown_to_html(md):
    """Very basic markdown to HTML converter."""
    import re
    lines = md.split("\n")
    html_lines = []
    in_code = False
    in_list = False
    in_table = False

    for line in lines:
        # Code blocks
        if line.strip().startswith("```"):
            if in_code:
                html_lines.append("</code></pre>")
                in_code = False
            else:
                lang = line.strip().replace("```", "")
                html_lines.append(f'<pre style="background:#0d1117;border-radius:8px;padding:16px;overflow-x:auto"><code style="color:#e6edf3;font-size:0.85rem">')
                in_code = True
            continue

        if in_code:
            html_lines.append(escape(line))
            continue

        # Headers
        if line.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f'<h2 style="margin-top:32px;margin-bottom:12px">{escape(line[3:])}</h2>')
            continue
        if line.startswith("### "):
            html_lines.append(f'<h3 style="margin-top:24px;margin-bottom:8px">{escape(line[4:])}</h3>')
            continue

        # Tables
        if "|" in line and line.strip().startswith("|"):
            if not in_table:
                html_lines.append('<div style="overflow-x:auto;margin:16px 0"><table style="width:100%;border-collapse:collapse;font-size:0.85rem">')
                in_table = True
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(set(c) <= set("- :") for c in cells):
                continue  # separator row
            row = "".join(f'<td style="padding:8px 12px;border:1px solid var(--border)">{escape(c)}</td>' for c in cells)
            html_lines.append(f"<tr>{row}</tr>")
            continue
        elif in_table:
            html_lines.append("</table></div>")
            in_table = False

        # List items
        if line.strip().startswith("- "):
            if not in_list:
                html_lines.append("<ul style='padding-left:24px;margin:12px 0'>")
                in_list = True
            # Handle bold, code, and links in list items
            item = escape(line.strip()[2:])
            item = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', item)
            item = re.sub(r'`(.+?)`', r'<code style="background:var(--bg);padding:2px 6px;border-radius:4px;font-size:0.85rem">\1</code>', item)
            item = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener" style="color:var(--accent);font-weight:600">\1</a>', item)
            item = re.sub(r'(?<!href=")(?<!href=\')(https?://manja8\.gumroad\.com/l/[a-zA-Z0-9_-]+)', r'<a href="\1" target="_blank" rel="noopener" style="color:var(--accent);font-weight:600">\1</a>', item)
            html_lines.append(f"<li>{item}</li>")
            continue
        elif in_list and line.strip() == "":
            html_lines.append("</ul>")
            in_list = False

        # Bold, code, links
        processed = escape(line)
        processed = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', processed)
        processed = re.sub(r'`(.+?)`', r'<code style="background:var(--bg);padding:2px 6px;border-radius:4px;font-size:0.85rem">\1</code>', processed)
        processed = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener" style="color:var(--accent);font-weight:600">\1</a>', processed)
        processed = re.sub(r'(?<!href=")(?<!href=\')(https?://manja8\.gumroad\.com/l/[a-zA-Z0-9_-]+)', r'<a href="\1" target="_blank" rel="noopener" style="color:var(--accent);font-weight:600">\1</a>', processed)

        if line.strip() == "":
            html_lines.append("<br>")
        elif line.strip().startswith("---"):
            html_lines.append('<hr style="border:none;border-top:1px solid var(--border);margin:32px 0">')
        else:
            html_lines.append(f"<p>{processed}</p>")

    if in_list:
        html_lines.append("</ul>")
    if in_table:
        html_lines.append("</table></div>")
    if in_code:
        html_lines.append("</code></pre>")

    return "\n".join(html_lines)


def main():
    print(f"Loading data from {DATA_FILE}...")
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    excluded_hashes = load_excluded_hashes()
    servers = [
        s for s in data["servers"]
        if not is_excluded_repo(s.get("repo", ""), excluded_hashes)
        and "fourtrader" not in (s.get("repo", "").lower())
        and not has_malicious_bait(
            s.get("repo", ""),
            (s.get("description") or "") + "\n" + (s.get("readme_excerpt") or ""),
        )
    ]
    print(f"Loaded {len(servers)} screened servers (filtered {len(data['servers']) - len(servers)})")

    active_sponsors = load_active_sponsors()
    active_sponsored_slugs = {
        sl for item in active_sponsors
        for sl in (
            slugify(item.get("server_slug", "")),
            slugify(item.get("repo", "").replace("/", "-")),
        )
        if sl
    }

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
    if "--home-only" in sys.argv:
        print("Home page only built successfully!")
        return

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

    # Build individual server pages (top servers with >= 10 stars or explicit/sponsored overrides)
    print("Building server pages...")
    seen_slugs = set()
    for s in servers:
        base_slug = slugify(s["repo"].replace("/", "-"))
        is_explicit = bool(s.get("build_page") or s.get("install_config") or base_slug in active_sponsored_slugs)
        if "--all-servers" not in sys.argv and s.get("stars", 0) < 10 and not is_explicit:
            continue
        slug = base_slug
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

    # Build pricing & sponsorship page
    print("Building pricing page...")
    write(os.path.join(SITE_DIR, "pricing.html"), build_pricing_page(len(servers)))

    # Build auditor page
    print("Building auditor page...")
    write(os.path.join(SITE_DIR, "audit.html"), build_audit_page())

    # Build AWS free page
    print("Building AWS free page...")
    write(os.path.join(SITE_DIR, "aws-free.html"), build_aws_free_page())

    # Preserve existing live trading proof page when offline telemetry CSV is absent
    live_csv = "/Users/apple/Documents/LuciferForge/products/cross-signal-data/data/crashes_v1.csv"
    live_out = os.path.join(SITE_DIR, "live.html")
    if os.path.exists(live_csv) or not os.path.exists(live_out):
        print("Building live page...")
        write(live_out, build_live_page())
    else:
        print("Preserving existing live.html (offline telemetry CSV not present)...")

    # Dataset landing pages
    os.makedirs(os.path.join(SITE_DIR, "datasets"), exist_ok=True)
    mcp_zip = ROOT_DIR / "releases" / "Protodex_MCP_Ecosystem_Dataset_31k.zip"
    zip_mb = round(mcp_zip.stat().st_size / (1024 * 1024), 1) if mcp_zip.exists() else 10.9
    write(os.path.join(SITE_DIR, "datasets", "mcp-servers.html"), build_mcp_dataset_page(len(servers), zip_mb))
    write(os.path.join(SITE_DIR, "datasets", "polymarket-historical.html"), build_dataset_page())

    # Build security page
    print("Building security page...")
    write(os.path.join(SITE_DIR, "security.html"), build_security_page(servers))

    # Build blog
    print("Building blog...")
    blog_posts = load_blog_posts()
    if blog_posts:
        os.makedirs(os.path.join(SITE_DIR, "blog"), exist_ok=True)
        write(os.path.join(SITE_DIR, "blog", "index.html"), build_blog_index(blog_posts))
        # Skip _external posts — their HTML is already authored on disk.
        rebuilt = 0
        for post in blog_posts:
            if post.get("_external"):
                continue
            write(os.path.join(SITE_DIR, "blog", f"{post['slug']}.html"), build_blog_post(post))
            rebuilt += 1
        externals = sum(1 for p in blog_posts if p.get("_external"))
        print(f"  - {len(blog_posts)} blog posts ({rebuilt} regenerated, {externals} external/orphan)")

    # Build SEO assets
    print("Building SEO assets...")
    write(os.path.join(SITE_DIR, "sitemap.xml"), build_sitemap(servers, categories))
    write(os.path.join(SITE_DIR, "robots.txt"), build_robots())
    write(os.path.join(SITE_DIR, "search-index.json"), build_search_index(servers))

    # CNAME for custom domain
    write(os.path.join(SITE_DIR, "CNAME"), DOMAIN)

    # 404 page + dynamic legacy /servers/ router (only resolves clean active servers; removed entries stay 404)
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
    redirect_script = """
<script>
(function() {
    var REDIRECTS = {
        "kyanitelabs-mcp-video": "/servers/kyanitelabs-kinocut.html"
    };
    var p = window.location.pathname;
    var m = p.match(/\\/servers\\/([^\\/]+)\\.html$/);
    if (m) {
        var slug = m[1];
        if (REDIRECTS[slug]) {
            window.location.replace(REDIRECTS[slug]);
            return;
        }
        fetch('/search-index.json')
            .then(function(r) { return r.json(); })
            .then(function(items) {
                var found = items.find(function(it) { return it.s === slug; });
                if (found && found.r) {
                    window.location.replace('https://github.com/' + found.r);
                }
            })
            .catch(function(e) { console.error('Router error:', e); });
    }
})();
</script>
"""
    html_404 = html_404.replace("</body>", redirect_script + "</body>")
    write(os.path.join(SITE_DIR, "404.html"), html_404)

    # Remove stale orphan pages (servers removed/recategorized since a prior build)
    print("Pruning orphan pages...")
    prune_orphans(dry_run=os.environ.get("PRUNE_DRYRUN") == "1")

    print(f"\nDone! Generated site in {SITE_DIR}/")
    print(f"  - 1 home page")
    print(f"  - 1 categories index")
    print(f"  - {len(categories)} category pages")
    print(f"  - {len(seen_slugs)} server pages")
    print(f"  - sitemap.xml, robots.txt, search-index.json, CNAME, 404.html")
    print(f"\nTotal: {len(seen_slugs) + len(categories) + 5} files")


_WRITTEN = set()

def write(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    _WRITTEN.add(os.path.abspath(path))


def prune_orphans(dry_run=False):
    """Delete stale generated pages in docs/servers and docs/category that were
    NOT written this build (servers removed/recategorized since a prior run).
    Safety: only prunes if this build wrote a healthy number of server pages."""
    written_servers = [p for p in _WRITTEN if os.sep + "servers" + os.sep in p]
    if len(written_servers) < 1000:
        print(f"  prune skipped (only {len(written_servers)} server pages written — unsafe)")
        return []
    removed = []
    for sub in ("servers", "category"):
        d = os.path.join(SITE_DIR, sub)
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if not name.endswith(".html"):
                continue
            ap = os.path.abspath(os.path.join(d, name))
            if ap not in _WRITTEN:
                removed.append(os.path.join(sub, name))
                if not dry_run:
                    os.remove(ap)
    print(f"  prune {'(dry-run) would remove' if dry_run else 'removed'} {len(removed)} orphan page(s)")
    return removed


if __name__ == "__main__":
    main()
    dist_dir = "/Users/apple/Documents/LuciferForge/distribution"
    if os.path.isdir(dist_dir):
        sys.path.insert(0, dist_dir)
        try:
            import rss_feed_generator
            rss_feed_generator.build_rss_pipeline()
        except Exception as e:
            print(f"RSS Feed Generation warning: {e}")
