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

    # Build content
    title = f"MCP Server Weekly: {len(new_servers)} New Servers Discovered — {today.strftime('%b %d, %Y')}"
    slug = f"weekly-{date_str}"

    new_rows = ""
    for s in new_servers[:10]:
        desc = escape(s['description'] or '')[:120]
        lang = s['language'] or '—'
        new_rows += f"""
        <tr>
            <td><a href="/servers/{slugify(s['repo'])}.html" style="color:var(--accent)">{escape(s['repo'])}</a></td>
            <td>{s['stars']:,}</td>
            <td>{escape(s['category'])}</td>
            <td>{lang}</td>
            <td>{desc}</td>
        </tr>"""

    trending_rows = ""
    for s in trending:
        desc = escape(s['description'] or '')[:100]
        trending_rows += f"""
        <tr>
            <td><a href="/servers/{slugify(s['repo'])}.html" style="color:var(--accent)">{escape(s['repo'])}</a></td>
            <td>{s['stars']:,}</td>
            <td>{escape(s['category'])}</td>
            <td>{desc}</td>
        </tr>"""

    cat_breakdown = ""
    for c in cat_stats:
        pct = c['cnt'] / total * 100
        cat_breakdown += f"<li><strong>{escape(c['category'])}</strong>: {c['cnt']} servers ({pct:.0f}%)</li>\n"

    content = f"""
    <article style="max-width:800px;margin:0 auto;padding:2rem 1rem">
        <header style="margin-bottom:2rem">
            <div style="color:var(--text-muted);font-size:0.85rem;margin-bottom:0.5rem">{today.strftime('%B %d, %Y')} &middot; Weekly Roundup</div>
            <h1 style="font-size:1.8rem;line-height:1.3;margin-bottom:1rem">{escape(title)}</h1>
            <p style="color:var(--text-muted);font-size:1.05rem;line-height:1.6">
                This week's scan of GitHub found {len(new_servers)} new MCP servers.
                The Protodex index now covers <strong>{total:,} servers</strong> across {len(cat_stats)} categories.
            </p>
        </header>

        <section style="margin-bottom:2.5rem">
            <h2 style="font-size:1.3rem;margin-bottom:1rem">New This Week</h2>
            <div style="overflow-x:auto">
            <table style="width:100%;border-collapse:collapse;font-size:0.85rem">
                <thead>
                    <tr style="border-bottom:1px solid var(--border);text-align:left">
                        <th style="padding:8px">Server</th>
                        <th style="padding:8px">Stars</th>
                        <th style="padding:8px">Category</th>
                        <th style="padding:8px">Language</th>
                        <th style="padding:8px">Description</th>
                    </tr>
                </thead>
                <tbody>{new_rows}</tbody>
            </table>
            </div>
            <p style="color:var(--text-muted);font-size:0.8rem;margin-top:0.5rem">
                <a href="https://protodex.io" style="color:var(--accent)">Browse all {total:,} servers &rarr;</a>
            </p>
        </section>

        <section style="margin-bottom:2.5rem">
            <h2 style="font-size:1.3rem;margin-bottom:1rem">Top Trending</h2>
            <div style="overflow-x:auto">
            <table style="width:100%;border-collapse:collapse;font-size:0.85rem">
                <thead>
                    <tr style="border-bottom:1px solid var(--border);text-align:left">
                        <th style="padding:8px">Server</th>
                        <th style="padding:8px">Stars</th>
                        <th style="padding:8px">Category</th>
                        <th style="padding:8px">Description</th>
                    </tr>
                </thead>
                <tbody>{trending_rows}</tbody>
            </table>
            </div>
        </section>

        <section style="margin-bottom:2.5rem">
            <h2 style="font-size:1.3rem;margin-bottom:1rem">Category Breakdown</h2>
            <ul style="color:var(--text-muted);font-size:0.9rem;line-height:1.8;padding-left:1.2rem">
                {cat_breakdown}
            </ul>
        </section>

        <section style="margin-bottom:2rem;padding:1.2rem;background:var(--bg-card);border:1px solid var(--border);border-radius:10px">
            <h3 style="font-size:1rem;margin-bottom:0.5rem">📊 From the Protodex Team</h3>
            <p style="color:var(--text-muted);font-size:0.9rem;margin-bottom:0.8rem">
                We also maintain a Polymarket historical dataset — 8.9M price points across 9,550 prediction markets.
                Useful for backtesting trading strategies and ML research.
            </p>
            <a href="https://manja8.gumroad.com/l/polymarket-data" target="_blank"
               style="color:var(--accent);font-size:0.85rem;font-weight:500">Get the dataset &rarr;</a>
        </section>

        <footer style="border-top:1px solid var(--border);padding-top:1.5rem;margin-top:2rem">
            <p style="color:var(--text-dim);font-size:0.8rem">
                Data sourced from GitHub via automated scraping. Updated weekly.
                <a href="https://protodex.io" style="color:var(--accent)">protodex.io</a> &middot;
                <a href="https://github.com/LuciferForge/mcp-directory" style="color:var(--accent)">Source code</a>
            </p>
        </footer>
    </article>
    """

    return title, slug, content, date_str


def build_blog_page(title, slug, content, date_str):
    """Build a full HTML page for a blog post."""
    # Read an existing blog post to copy the template
    template_file = BLOG_DIR / "blog-mcp-database-guide.html"
    if not template_file.exists():
        # Fallback: use index.html structure
        template_file = BLOG_DIR / "index.html"

    template = template_file.read_text()

    # Extract header (everything up to <main or first <article or <section class="container">)
    # and footer (everything after </main> or last </section>)
    # Simple approach: replace title and body

    # Build a standalone page
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
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚡</text></svg>">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #06060a; --bg-card: #0f0f14; --border: #1e1e2a;
            --text: #f0f0f5; --text-muted: #8888a0; --text-dim: #55556a;
            --accent: #00d4aa; --font: 'Inter', system-ui, sans-serif;
        }}
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:var(--font); background:var(--bg); color:var(--text); line-height:1.6; }}
        a {{ color:var(--accent); text-decoration:none; }}
        a:hover {{ text-decoration:underline; }}
        table {{ border-collapse:collapse; }}
        td, th {{ padding:8px 12px; border-bottom:1px solid var(--border); }}
        tr:hover {{ background:rgba(255,255,255,0.02); }}
        nav {{ padding:1rem 2rem; border-bottom:1px solid var(--border); display:flex; align-items:center; gap:1rem; }}
        nav a {{ color:var(--text-muted); font-size:0.9rem; }}
    </style>
    <script async defer src="https://scripts.simpleanalyticscdn.com/latest.js"></script>
</head>
<body>
    <nav>
        <a href="/" style="font-weight:700;color:var(--text)">⚡ Protodex</a>
        <a href="/blog/">Blog</a>
        <a href="/categories.html">Categories</a>
    </nav>
    {content}
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
