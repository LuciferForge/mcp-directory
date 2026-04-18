#!/usr/bin/env python3
"""
blog_generator.py — Auto-generate weekly blog posts from Protodex data.

Queries the MCP directory DB for trending/new servers, generates
SEO-optimized blog posts, and adds them to the static site.

Content types:
  1. "Weekly Roundup" — new servers this week, trending by stars
  2. "Category Deep Dive" — rotate through categories
  3. "Server Spotlight" — deep dive on a high-star server

Runs as part of the Monday refresh pipeline.

Usage:
  python3 blog_generator.py weekly    # Generate weekly roundup
  python3 blog_generator.py spotlight # Generate server spotlight
  python3 blog_generator.py all       # Generate all post types
"""

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from html import escape
from pathlib import Path

DB_PATH = Path(__file__).parent / "mcp_directory.db"
BLOG_DIR = Path(__file__).parent / "docs" / "blog"
BLOG_INDEX = BLOG_DIR / "index.html"
TEMPLATE_DIR = Path(__file__).parent / "docs"

# Rotate through categories for deep dives
CATEGORY_ROTATION = [
    "AI/LLM", "Code/Dev Tools", "Database", "API Integration",
    "Browser/Web", "Security", "Memory/Knowledge", "DevOps",
    "Search", "Data/Analytics", "Communication", "File System",
]


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def read_template():
    """Read the blog index for the HTML template (header/footer/styles)."""
    existing = (BLOG_DIR / "blog-mcp-database-guide.html").read_text()
    # Extract everything before <main and after </main>
    parts = existing.split('<main')
    header = parts[0] if len(parts) > 1 else ""
    footer_parts = existing.split('</main>')
    footer = footer_parts[-1] if len(footer_parts) > 1 else ""
    return header, footer


def generate_weekly_roundup(conn):
    """Generate a weekly roundup of new and trending MCP servers."""
    today = datetime.now(timezone.utc)
    week_ago = (today - timedelta(days=7)).isoformat()
    date_str = today.strftime("%Y-%m-%d")

    # New servers this week (by scraped_at date)
    new_servers = conn.execute("""
        SELECT repo, name, description, stars, language, category, url
        FROM servers
        WHERE scraped_at > ?
        ORDER BY stars DESC
        LIMIT 20
    """, (week_ago,)).fetchall()

    # Top trending (highest stars overall, as proxy for trending)
    trending = conn.execute("""
        SELECT repo, name, description, stars, language, category, url
        FROM servers
        ORDER BY stars DESC
        LIMIT 10
    """).fetchall()

    # Category stats
    cat_stats = conn.execute("""
        SELECT category, COUNT(*) as cnt
        FROM servers
        GROUP BY category
        ORDER BY cnt DESC
    """).fetchall()

    total = conn.execute("SELECT COUNT(*) FROM servers").fetchone()[0]

    # Build content with card-based design matching protodex.io
    title = f"MCP Server Weekly: {len(new_servers)} New Servers Discovered"
    slug = f"weekly-{date_str}"

    new_cards = ""
    for i, s in enumerate(new_servers[:10], 1):
        desc = escape(s['description'] or 'No description')[:100]
        lang = escape(s['language'] or '')
        lang_html = f'<span class="srv-lang">{lang}</span>' if lang else ''
        new_cards += (
            f'<a href="/servers/{slugify(s["repo"])}.html" class="srv">'
            f'<span class="srv-rank">#{i}</span>'
            f'<div class="srv-info"><div class="srv-name">{escape(s["repo"])}</div>'
            f'<div class="srv-desc">{desc}</div></div>'
            f'<div class="srv-meta"><span class="srv-stars">&#9733; {s["stars"]:,}</span>'
            f'<span class="srv-cat">{escape(s["category"])}</span>{lang_html}</div></a>\n'
        )

    trending_cards = ""
    for i, s in enumerate(trending, 1):
        desc = escape(s['description'] or '')[:90]
        trending_cards += (
            f'<a href="/servers/{slugify(s["repo"])}.html" class="srv">'
            f'<span class="srv-rank">#{i}</span>'
            f'<div class="srv-info"><div class="srv-name">{escape(s["repo"])}</div>'
            f'<div class="srv-desc">{desc}</div></div>'
            f'<div class="srv-meta"><span class="srv-stars">&#9733; {s["stars"]:,}</span>'
            f'<span class="srv-cat">{escape(s["category"])}</span></div></a>\n'
        )

    cat_pills = ""
    for c in cat_stats:
        cat_pills += f'<span class="cat-pill"><strong>{c["cnt"]}</strong> {escape(c["category"])}</span>\n'

    content = f"""
    <div class="post-hero">
        <span class="post-badge"><span class="pulse"></span> Weekly Roundup &#183; {today.strftime('%b %d')}</span>
        <h1 class="post-title"><span class="gradient">{len(new_servers)} New</span> MCP Servers This Week</h1>
        <p class="post-subtitle">Our automated scan of GitHub found {len(new_servers)} new MCP servers.
        The Protodex index now covers {total:,} servers across {len(cat_stats)} categories.</p>
    </div>

    <div class="stats-bar">
        <div class="stat"><div class="stat-value">{total:,}</div><div class="stat-label">Total Servers</div></div>
        <div class="stat"><div class="stat-value">+{len(new_servers)}</div><div class="stat-label">New This Week</div></div>
        <div class="stat"><div class="stat-value">{len(cat_stats)}</div><div class="stat-label">Categories</div></div>
        <div class="stat"><div class="stat-value">{trending[0]['stars']:,}</div><div class="stat-label">Top Stars</div></div>
    </div>

    <div class="post-body">
        <h2>New This Week</h2>
        <p>Servers discovered in the latest GitHub scan, ranked by stars.</p>
        <div class="srv-grid">{new_cards}</div>

        <h2>Top Trending</h2>
        <p>The most-starred MCP servers across the entire index.</p>
        <div class="srv-grid">{trending_cards}</div>

        <h2>By Category</h2>
        <div class="cat-pills">{cat_pills}</div>
        <p><a href="https://protodex.io/categories.html">Browse all categories &#8594;</a></p>

        <div class="cta-card">
            <h3>&#128202; Polymarket Historical Dataset</h3>
            <p>8.9M price points across 9,550 prediction markets. 15-minute snapshots, orderbook depth, 30 days of data. Built by the Protodex team.</p>
            <a href="https://manja8.gumroad.com/l/polymarket-data" target="_blank" class="cta-btn">Get the dataset &#8594;</a>
        </div>
    </div>
    """

    return title, slug, content, date_str


def build_blog_page(title, slug, content, date_str):
    """Build a full HTML page matching the protodex.io design language."""

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)} — Protodex Blog</title>
    <meta name="description" content="{escape(title)}">
    <meta property="og:title" content="{escape(title)}">
    <meta property="og:url" content="https://protodex.io/blog/{slug}.html">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Protodex">
    <link rel="canonical" href="https://protodex.io/blog/{slug}.html">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#9889;</text></svg>">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
:root {{
    --bg: #06060a;
    --bg-card: #0f0f14;
    --bg-card-hover: #16161d;
    --border: #1e1e2a;
    --border-hover: #2d2d3f;
    --text: #f0f0f5;
    --text-muted: #8888a0;
    --text-dim: #55556a;
    --accent: #00d4aa;
    --accent2: #7B61FF;
    --accent-glow: rgba(0, 212, 170, 0.15);
    --yellow: #FFD93D;
    --blue: #5B8DEF;
    --font: 'Inter', -apple-system, system-ui, sans-serif;
    --mono: 'JetBrains Mono', 'SF Mono', monospace;
    --radius: 10px;
    --radius-lg: 16px;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{ font-family:var(--font); background:var(--bg); color:var(--text); line-height:1.6; -webkit-font-smoothing:antialiased; }}
a {{ color:var(--accent); text-decoration:none; }}
a:hover {{ opacity:0.85; }}

/* Nav */
.nav {{ padding:14px 24px; border-bottom:1px solid var(--border); display:flex; align-items:center; gap:20px; position:sticky; top:0; background:rgba(6,6,10,0.92); backdrop-filter:blur(12px); z-index:100; }}
.nav-logo {{ font-weight:800; font-size:1.05rem; color:var(--text); letter-spacing:-0.5px; }}
.nav a {{ color:var(--text-dim); font-size:0.85rem; transition:color 0.15s; }}
.nav a:hover {{ color:var(--text); }}

/* Hero banner */
.post-hero {{ position:relative; padding:64px 24px 48px; text-align:center; overflow:hidden; }}
.post-hero::before {{ content:''; position:absolute; top:0; left:50%; transform:translateX(-50%); width:600px; height:600px; background:radial-gradient(circle, rgba(0,212,170,0.06) 0%, transparent 70%); pointer-events:none; }}
.post-badge {{ display:inline-flex; align-items:center; gap:6px; background:var(--accent-glow); border:1px solid rgba(0,212,170,0.2); border-radius:20px; padding:5px 14px; font-size:0.75rem; font-weight:600; color:var(--accent); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:20px; }}
.post-badge .pulse {{ width:6px; height:6px; border-radius:50%; background:var(--accent); animation:pulse 2s infinite; }}
@keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.4; }} }}
.post-title {{ font-size:2.2rem; font-weight:800; letter-spacing:-1.5px; line-height:1.1; max-width:700px; margin:0 auto 16px; }}
.post-title .gradient {{ background:linear-gradient(135deg, #00d4aa 0%, #7B61FF 50%, #FFD93D 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }}
.post-subtitle {{ color:var(--text-muted); font-size:1rem; max-width:560px; margin:0 auto; line-height:1.6; }}

/* Stats bar */
.stats-bar {{ display:flex; justify-content:center; gap:32px; padding:20px 24px; border-bottom:1px solid var(--border); flex-wrap:wrap; }}
.stat {{ text-align:center; }}
.stat-value {{ font-family:var(--mono); font-size:1.4rem; font-weight:700; color:var(--accent); }}
.stat-label {{ font-size:0.72rem; color:var(--text-dim); text-transform:uppercase; letter-spacing:0.8px; margin-top:2px; }}

/* Content */
.post-body {{ max-width:720px; margin:0 auto; padding:48px 24px; }}
.post-body h2 {{ font-size:1.2rem; font-weight:700; letter-spacing:-0.3px; margin:48px 0 16px; padding-bottom:8px; border-bottom:1px solid var(--border); }}
.post-body h2:first-child {{ margin-top:0; }}
.post-body p {{ color:var(--text-muted); margin-bottom:16px; }}

/* Server cards (not tables) */
.srv-grid {{ display:grid; grid-template-columns:1fr; gap:8px; margin:16px 0 32px; }}
.srv {{ display:flex; align-items:center; gap:14px; padding:12px 16px; background:var(--bg-card); border:1px solid var(--border); border-radius:var(--radius); transition:border-color 0.15s; }}
.srv:hover {{ border-color:var(--border-hover); }}
.srv-rank {{ font-family:var(--mono); font-size:0.8rem; color:var(--text-dim); min-width:24px; }}
.srv-info {{ flex:1; min-width:0; }}
.srv-name {{ font-weight:600; font-size:0.88rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.srv-desc {{ color:var(--text-dim); font-size:0.78rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-top:2px; }}
.srv-meta {{ display:flex; gap:12px; align-items:center; flex-shrink:0; }}
.srv-stars {{ font-family:var(--mono); font-size:0.82rem; color:var(--yellow); }}
.srv-cat {{ font-size:0.7rem; padding:2px 8px; border-radius:10px; background:rgba(123,97,255,0.12); color:var(--accent2); white-space:nowrap; }}
.srv-lang {{ font-size:0.7rem; color:var(--text-dim); }}

/* Category pills */
.cat-pills {{ display:flex; flex-wrap:wrap; gap:8px; margin:16px 0 32px; }}
.cat-pill {{ display:flex; align-items:center; gap:6px; padding:6px 14px; background:var(--bg-card); border:1px solid var(--border); border-radius:20px; font-size:0.8rem; color:var(--text-muted); }}
.cat-pill strong {{ color:var(--text); font-family:var(--mono); }}

/* CTA */
.cta-card {{ margin:40px 0; padding:24px; background:linear-gradient(135deg, rgba(123,97,255,0.08), rgba(0,212,170,0.06)); border:1px solid rgba(123,97,255,0.2); border-radius:var(--radius-lg); }}
.cta-card h3 {{ font-size:1rem; margin-bottom:6px; }}
.cta-card p {{ color:var(--text-muted); font-size:0.88rem; margin-bottom:12px; }}
.cta-btn {{ display:inline-block; background:var(--accent); color:#000; padding:8px 20px; border-radius:20px; font-size:0.82rem; font-weight:600; transition:opacity 0.15s; }}
.cta-btn:hover {{ opacity:0.9; }}

/* Footer */
.post-footer {{ border-top:1px solid var(--border); padding:24px; text-align:center; color:var(--text-dim); font-size:0.78rem; }}
.post-footer a {{ color:var(--accent); }}

@media (max-width:640px) {{
    .post-title {{ font-size:1.5rem; }}
    .stats-bar {{ gap:16px; }}
    .stat-value {{ font-size:1.1rem; }}
    .srv {{ flex-direction:column; align-items:flex-start; gap:8px; }}
    .srv-meta {{ width:100%; }}
}}
    </style>
    <script async defer src="https://scripts.simpleanalyticscdn.com/latest.js"></script>
</head>
<body>
    <nav class="nav">
        <a href="/" class="nav-logo">&#9889; Protodex</a>
        <a href="/blog/">Blog</a>
        <a href="/categories.html">Categories</a>
        <a href="https://github.com/LuciferForge/mcp-directory" target="_blank">GitHub</a>
    </nav>
    {content}
    <footer class="post-footer">
        Data sourced from GitHub. Auto-updated weekly. <a href="https://protodex.io">protodex.io</a> &middot; <a href="https://github.com/LuciferForge/mcp-directory">Source</a>
    </footer>
</body>
</html>"""

    out_path = BLOG_DIR / f"{slug}.html"
    out_path.write_text(page)
    print(f"Generated: {out_path.name}")
    return out_path


def update_blog_index(posts):
    """Add new posts to the blog index page."""
    index = BLOG_INDEX.read_text()

    # Find where to insert new posts (after the opening of the post list)
    # Look for the first blog card
    insert_marker = '<div class="blog-grid"'
    if insert_marker not in index:
        # Try alternate markers
        insert_marker = '<div style="display:grid'
        if insert_marker not in index:
            print("WARNING: Could not find insertion point in blog index")
            return

    new_cards = ""
    for title, slug, date_str in posts:
        new_cards += f"""
        <a href="/blog/{slug}.html" style="display:block;padding:1.2rem;background:var(--bg-card);border:1px solid var(--border);border-radius:10px;text-decoration:none;color:var(--text);transition:border-color 0.2s">
            <div style="color:var(--text-muted);font-size:0.8rem;margin-bottom:0.3rem">{date_str}</div>
            <div style="font-weight:600;font-size:0.95rem;line-height:1.4">{escape(title)}</div>
        </a>
        """

    # Insert after the grid opening tag
    idx = index.find(insert_marker)
    if idx >= 0:
        # Find the end of the opening tag
        tag_end = index.find('>', idx) + 1
        index = index[:tag_end] + new_cards + index[tag_end:]
        BLOG_INDEX.write_text(index)
        print(f"Updated blog index with {len(posts)} new posts")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "weekly"
    conn = get_db()

    posts = []

    if cmd in ("weekly", "all"):
        title, slug, content, date_str = generate_weekly_roundup(conn)
        build_blog_page(title, slug, content, date_str)
        posts.append((title, slug, date_str))

    if posts:
        update_blog_index(posts)

    conn.close()
    print(f"\nDone. {len(posts)} posts generated.")


if __name__ == "__main__":
    main()
