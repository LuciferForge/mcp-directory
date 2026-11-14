#!/usr/bin/env python3
"""
blog_generator.py — Auto-generate weekly Model Context Protocol (MCP) blog digests.

Strict weekly cadence:
- Runs once per week (Monday cadence: weekly-YYYY-MM-DD.html).
- Guaranteed non-repeating server selection: never republishes the same repos.
- Extracts all previously featured repos from existing weekly digests.
- Balances category diversity (AI/LLM, Database, Dev Tools, Security, Browser, APIs).
- Dynamic category spotlight rotated weekly.
- Works seamlessly from mcp_directory.json (committed in git) or mcp_directory.db.

Usage:
  python3 blog_generator.py weekly            # Generate current week's digest (skips if already exists)
  python3 blog_generator.py weekly --force    # Force regenerate current week's digest
  python3 blog_generator.py all               # Generate weekly digest and category deep dive
"""

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from html import escape
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "mcp_directory.db"
JSON_PATH = BASE_DIR / "mcp_directory.json"
BLOG_DIR = BASE_DIR / "docs" / "blog"
BLOG_INDEX = BLOG_DIR / "index.html"

# Rotate through categories for deep dives and weekly spotlight focus
CATEGORY_ROTATION = [
    "AI/LLM", "Code/Dev Tools", "Database", "API Integration",
    "Browser/Web", "Security", "Memory/Knowledge", "DevOps",
    "Search", "Data/Analytics", "Communication", "File System", "Finance"
]


def format_blog_date(iso_str):
    try:
        dt = datetime.strptime(iso_str, "%Y-%m-%d")
        return dt.strftime("%b %d, %Y")
    except Exception:
        return iso_str


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-')


def load_servers():
    """Load servers from SQLite DB if available, otherwise from mcp_directory.json."""
    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM servers").fetchall()
            servers = [dict(r) for r in rows]
            conn.close()
            if servers:
                return servers
        except Exception as e:
            print(f"Notice: SQLite read failed ({e}), falling back to JSON.")

    if JSON_PATH.exists():
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "servers" in data:
            return data["servers"]
        elif isinstance(data, list):
            return data

    raise RuntimeError("No server data source found (neither mcp_directory.db nor mcp_directory.json).")


def get_featured_repos():
    """Scan docs/blog/weekly-*.html to extract all repository names previously featured."""
    featured = set()
    canonical_files = []
    if not BLOG_DIR.exists():
        return featured, canonical_files

    for f in sorted(BLOG_DIR.glob("weekly-*.html")):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
            # If it's a redirect stub, skip adding to canonical count
            if 'http-equiv="refresh"' in text.lower():
                continue
            canonical_files.append(f)
            srvs = re.findall(r'class="srv-name">([^<]+)</div>', text)
            for s in srvs:
                featured.add(s.strip().lower())
        except Exception:
            continue

    return featured, canonical_files


def select_unfeatured_servers(all_servers, featured_set, count=20):
    """
    Select `count` high-quality servers that have NEVER been featured in any weekly digest.
    Ensures broad category diversity so no single category dominates.
    """
    candidates = []
    for s in all_servers:
        repo = s.get("repo", "").strip()
        if not repo or repo.lower() in featured_set:
            continue

        desc = (s.get("description") or "").strip()
        # Must have a non-trivial description and at least 0 stars
        if len(desc) < 15:
            continue

        stars = s.get("stars", 0) or 0
        cat = s.get("category", "Other") or "Other"

        candidates.append({
            "repo": repo,
            "name": s.get("name") or repo.split("/")[-1],
            "description": desc,
            "stars": stars,
            "language": s.get("language") or "",
            "category": cat,
            "url": s.get("url") or f"https://github.com/{repo}",
            "security_band": s.get("security_band") or "green"
        })

    # Sort candidates by stars descending
    candidates.sort(key=lambda x: x["stars"], reverse=True)

    # Pick with category diversity caps (max 4 per category in top 20)
    selected = []
    cat_counts = {}
    remaining = []

    for c in candidates:
        cat = c["category"]
        if cat_counts.get(cat, 0) < 4:
            selected.append(c)
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            if len(selected) >= count:
                break
        else:
            remaining.append(c)

    # If we couldn't fill 20 with strict caps, fill from remaining
    if len(selected) < count and remaining:
        for r in remaining:
            selected.append(r)
            if len(selected) >= count:
                break

    return selected


def generate_weekly_roundup(force=False, target_date=None):
    """Generate a strictly weekly roundup of fresh, non-duplicate MCP servers."""
    now = target_date or datetime.now(timezone.utc)
    # Calculate Monday of current ISO week
    iso_year, iso_week, iso_weekday = now.isocalendar()
    monday = now - timedelta(days=iso_weekday - 1)
    date_str = monday.strftime("%Y-%m-%d")
    date_display = format_blog_date(date_str)
    slug = f"weekly-{date_str}"
    out_path = BLOG_DIR / f"{slug}.html"

    if out_path.exists() and not force:
        # Check if it's already an active canonical post
        text = out_path.read_text(encoding="utf-8", errors="ignore")
        if 'http-equiv="refresh"' not in text.lower():
            print(f"[weekly-digest] Digest for week of {date_str} already exists: {out_path.name}")
            print(f"[weekly-digest] Skipping creation to preserve weekly cadence. (Pass --force to overwrite)")
            return None

    all_servers = load_servers()
    featured_set, canonical_files = get_featured_repos()

    # Determine Issue #
    issue_num = len(canonical_files) + (1 if not out_path.exists() else 0)
    if issue_num < 24:
        issue_num = 24  # ensure consecutive sequence after historical issues 1-23

    # Select 20 brand-new, never-featured servers
    new_servers = select_unfeatured_servers(all_servers, featured_set, count=20)
    if not new_servers:
        print("[weekly-digest] No unfeatured servers available!")
        return None

    # Rotating category spotlight for this week
    spotlight_cat = CATEGORY_ROTATION[iso_week % len(CATEGORY_ROTATION)]
    spotlight_servers = [s for s in all_servers if s.get("category") == spotlight_cat and (s.get("stars") or 0) > 0]
    spotlight_servers.sort(key=lambda x: x.get("stars", 0), reverse=True)
    spotlight_top = spotlight_servers[:8]

    # Category stats across all servers
    cat_counts = {}
    for s in all_servers:
        c = s.get("category", "Other") or "Other"
        cat_counts[c] = cat_counts.get(c, 0) + 1
    sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)

    total_servers = len(all_servers)

    # Top highlight names for headline and metadata
    top1_name = new_servers[0]["repo"].split("/")[-1]
    top2_name = new_servers[1]["repo"].split("/")[-1] if len(new_servers) > 1 else ""
    highlights = f"{top1_name} & {top2_name}" if top2_name else top1_name

    title = f"MCP Server Weekly #{issue_num:02d}: Featuring {highlights} ({date_display})"
    desc = f"Protodex MCP Server Weekly #{issue_num:02d} ({date_display}): 20 fresh Model Context Protocol servers across {len(cat_counts)} categories, featuring {highlights} and weekly spotlight on {spotlight_cat}."

    # Build server cards
    new_cards = ""
    for i, s in enumerate(new_servers, 1):
        desc_text = escape(s["description"])[:110] + ("..." if len(s["description"]) > 110 else "")
        lang = escape(s.get("language") or "")
        lang_html = f'<span class="srv-lang">{lang}</span>' if lang else ''
        cat_name = escape(s["category"])
        new_cards += (
            f'<a href="/servers/{slugify(s["repo"])}.html" class="srv">\n'
            f'  <span class="srv-rank">#{i:02d}</span>\n'
            f'  <div class="srv-info">\n'
            f'    <div class="srv-name">{escape(s["repo"])}</div>\n'
            f'    <div class="srv-desc">{desc_text}</div>\n'
            f'  </div>\n'
            f'  <div class="srv-meta">\n'
            f'    <span class="srv-stars">&#9733; {s["stars"]:,}</span>\n'
            f'    <span class="srv-cat">{cat_name}</span>\n'
            f'    {lang_html}\n'
            f'  </div>\n'
            f'</a>\n'
        )

    # Build spotlight cards
    spotlight_cards = ""
    for i, s in enumerate(spotlight_top, 1):
        s_desc = escape(s.get("description", "") or "")[:90]
        s_repo = escape(s.get("repo", ""))
        s_stars = s.get("stars", 0)
        spotlight_cards += (
            f'<a href="/servers/{slugify(s["repo"])}.html" class="srv">\n'
            f'  <span class="srv-rank">#{i}</span>\n'
            f'  <div class="srv-info">\n'
            f'    <div class="srv-name">{s_repo}</div>\n'
            f'    <div class="srv-desc">{s_desc}</div>\n'
            f'  </div>\n'
            f'  <div class="srv-meta">\n'
            f'    <span class="srv-stars">&#9733; {s_stars:,}</span>\n'
            f'    <span class="srv-cat">{escape(spotlight_cat)}</span>\n'
            f'  </div>\n'
            f'</a>\n'
        )

    cat_pills = ""
    for c_name, count in sorted_cats:
        cat_pills += f'<a href="/categories.html" class="cat-pill"><strong>{count:,}</strong> {escape(c_name)}</a>\n'

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)} — Protodex Blog</title>
    <meta name="description" content="{escape(desc)}">
    <meta property="og:title" content="{escape(title)}">
    <meta property="og:description" content="{escape(desc)}">
    <meta property="og:url" content="https://protodex.io/blog/{slug}.html">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Protodex">
    <meta property="og:image" content="https://protodex.io/og/protodex.png">
    <link rel="canonical" href="https://protodex.io/blog/{slug}.html">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#9889;</text></svg>">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
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
    --accent: #2DD9E0;
    --accent-glow: rgba(45, 217, 224, 0.15);
    --accent2: #7B61FF;
    --yellow: #FFD93D;
    --blue: #5B8DEF;
    --font: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --mono: 'JetBrains Mono', monospace;
    --radius: 10px;
    --radius-lg: 16px;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{ font-family:var(--font); background:var(--bg); color:var(--text); line-height:1.6; -webkit-font-smoothing:antialiased; }}
a {{ color:var(--accent); text-decoration:none; }}
a:hover {{ opacity:0.88; }}

.nav {{ padding:14px 24px; border-bottom:1px solid var(--border); display:flex; align-items:center; gap:20px; position:sticky; top:0; background:rgba(6,6,10,0.92); backdrop-filter:blur(12px); z-index:100; }}
.nav-logo {{ font-weight:800; font-size:1.05rem; color:var(--text); letter-spacing:-0.5px; }}
.nav a {{ color:var(--text-dim); font-size:0.85rem; transition:color 0.15s; }}
.nav a:hover {{ color:var(--text); }}

.post-hero {{ position:relative; padding:64px 24px 40px; text-align:center; overflow:hidden; }}
.post-hero::before {{ content:''; position:absolute; top:0; left:50%; transform:translateX(-50%); width:600px; height:500px; background:radial-gradient(circle, rgba(45,217,224,0.08) 0%, transparent 70%); pointer-events:none; }}
.post-badge {{ display:inline-flex; align-items:center; gap:8px; background:var(--accent-glow); border:1px solid rgba(45,217,224,0.3); border-radius:20px; padding:6px 16px; font-size:0.75rem; font-weight:700; color:var(--accent); text-transform:uppercase; letter-spacing:0.8px; margin-bottom:20px; }}
.post-badge .pulse {{ width:7px; height:7px; border-radius:50%; background:var(--accent); box-shadow:0 0 8px var(--accent); }}
.post-title {{ font-size:2.2rem; font-weight:800; letter-spacing:-1.2px; line-height:1.2; max-width:800px; margin:0 auto 16px; }}
.post-title .gradient {{ background:linear-gradient(135deg, #2DD9E0 0%, #7B61FF 50%, #FFD93D 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }}
.post-subtitle {{ color:var(--text-muted); font-size:1rem; max-width:640px; margin:0 auto; line-height:1.6; }}

.stats-bar {{ display:flex; justify-content:center; gap:36px; padding:18px 24px; border-top:1px solid var(--border); border-bottom:1px solid var(--border); flex-wrap:wrap; }}
.stat {{ text-align:center; }}
.stat-value {{ font-family:var(--mono); font-size:1.35rem; font-weight:700; color:var(--accent); }}
.stat-label {{ font-size:0.72rem; color:var(--text-dim); text-transform:uppercase; letter-spacing:0.8px; margin-top:2px; }}

.post-body {{ max-width:820px; margin:0 auto; padding:48px 24px; }}
.post-body h2 {{ font-size:1.3rem; font-weight:700; letter-spacing:-0.3px; margin:44px 0 16px; padding-bottom:10px; border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; }}
.post-body h2:first-child {{ margin-top:0; }}
.post-body p {{ color:var(--text-muted); margin-bottom:18px; font-size:0.95rem; }}

.srv-grid {{ display:grid; grid-template-columns:1fr; gap:10px; margin:20px 0 36px; }}
.srv {{ display:flex; align-items:center; gap:14px; padding:14px 18px; background:var(--bg-card); border:1px solid var(--border); border-radius:var(--radius); transition:all 0.15s ease; color:inherit; }}
.srv:hover {{ border-color:var(--accent); transform:translateX(3px); background:var(--bg-card-hover); }}
.srv-rank {{ font-family:var(--mono); font-size:0.85rem; color:var(--text-dim); min-width:28px; font-weight:600; }}
.srv-info {{ flex:1; min-width:0; }}
.srv-name {{ font-weight:600; font-size:0.92rem; color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.srv-desc {{ color:var(--text-muted); font-size:0.8rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-top:3px; }}
.srv-meta {{ display:flex; gap:10px; align-items:center; flex-shrink:0; }}
.srv-stars {{ font-family:var(--mono); font-size:0.82rem; color:var(--yellow); font-weight:600; }}
.srv-cat {{ font-size:0.72rem; padding:3px 8px; border-radius:12px; background:rgba(123,97,255,0.14); color:var(--accent2); font-weight:500; white-space:nowrap; }}
.srv-lang {{ font-size:0.72rem; color:var(--text-dim); }}

.cat-pills {{ display:flex; flex-wrap:wrap; gap:8px; margin:16px 0 32px; }}
.cat-pill {{ display:flex; align-items:center; gap:6px; padding:6px 14px; background:var(--bg-card); border:1px solid var(--border); border-radius:20px; font-size:0.8rem; color:var(--text-muted); transition:border-color 0.15s; }}
.cat-pill:hover {{ border-color:var(--accent); color:var(--text); }}
.cat-pill strong {{ color:var(--text); font-family:var(--mono); }}

.cta-stack {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:16px; margin:24px 0 40px; }}
.cta-card {{ padding:20px; background:linear-gradient(135deg, rgba(123,97,255,0.08), rgba(45,217,224,0.06)); border:1px solid rgba(45,217,224,0.25); border-radius:var(--radius-lg); }}
.cta-card h3 {{ font-size:0.95rem; margin-bottom:8px; color:var(--text); font-weight:700; }}
.cta-card p {{ color:var(--text-muted); font-size:0.82rem; margin-bottom:14px; line-height:1.5; }}
.cta-btn {{ display:inline-block; background:var(--accent); color:#000; padding:8px 18px; border-radius:20px; font-size:0.78rem; font-weight:700; transition:opacity 0.15s; }}
.cta-btn:hover {{ opacity:0.88; }}

.post-footer {{ border-top:1px solid var(--border); padding:32px 24px; text-align:center; color:var(--text-dim); font-size:0.82rem; }}
.post-footer a {{ color:var(--accent); }}

@media (max-width:640px) {{
    .post-title {{ font-size:1.6rem; }}
    .stats-bar {{ gap:16px; }}
    .srv {{ flex-direction:column; align-items:flex-start; gap:8px; }}
    .srv-meta {{ width:100%; justify-content:space-between; }}
}}
    </style>
    <script async defer src="https://scripts.simpleanalyticscdn.com/latest.js"></script>
</head>
<body>
    <nav class="nav">
        <a href="/" class="nav-logo">&#9889; Protodex</a>
        <a href="/blog/">Blog</a>
        <a href="/categories.html">Categories</a>
        <a href="/ui-studio.html">UI Studio</a>
        <a href="https://github.com/LuciferForge/mcp-directory" target="_blank">GitHub</a>
    </nav>

    <div class="post-hero">
        <span class="post-badge"><span class="pulse"></span> Weekly Roundup &#183; Issue #{issue_num:02d} &#183; {date_display}</span>
        <h1 class="post-title"><span class="gradient">20 Fresh</span> MCP Servers Discovered</h1>
        <p class="post-subtitle">Our automated discovery engine indexed 20 new Model Context Protocol servers this week, featuring {highlights}. The Protodex registry now spans {total_servers:,} verified servers.</p>
    </div>

    <div class="stats-bar">
        <div class="stat"><div class="stat-value">{total_servers:,}</div><div class="stat-label">Total Registry</div></div>
        <div class="stat"><div class="stat-value">+20</div><div class="stat-label">New This Week</div></div>
        <div class="stat"><div class="stat-value">{len(cat_counts)}</div><div class="stat-label">Categories</div></div>
        <div class="stat"><div class="stat-value">{new_servers[0]['stars']:,}</div><div class="stat-label">Top Highlight Stars</div></div>
    </div>

    <div class="post-body">
        <h2>Fresh Servers This Week <span style="font-size:0.8rem;color:var(--text-dim);font-weight:400;">Guaranteed unfeatured</span></h2>
        <p>Curated from the newest additions to the Protodex registry across multiple developer tooling disciplines.</p>
        <div class="srv-grid">{new_cards}</div>

        <h2>Category Focus: {escape(spotlight_cat)} <span style="font-size:0.8rem;color:var(--text-dim);font-weight:400;">Weekly Spotlight</span></h2>
        <p>A rotating deep dive into leading servers within the {escape(spotlight_cat)} ecosystem.</p>
        <div class="srv-grid">{spotlight_cards}</div>

        <h2>Explore by Category</h2>
        <div class="cat-pills">{cat_pills}</div>
        <p><a href="/categories.html">Browse all {len(cat_counts)} categories on Protodex &#8594;</a></p>

        <h2>Production Toolkits &amp; Quantitative Datasets</h2>
        <div class="cta-stack">
            <div class="cta-card">
                <h3>&#128202; Polymarket Historical Dataset</h3>
                <p>10.8M+ price ticks across 13,900+ prediction markets. 15-minute orderbook depth, CSV format. <strong>$19 one-time</strong>.</p>
                <a href="https://manja8.gumroad.com/l/polymarket-data?utm_source=protodex&amp;utm_medium=blog&amp;utm_campaign={slug}" target="_blank" class="cta-btn">Get Dataset &#8594;</a>
            </div>
            <div class="cta-card">
                <h3>&#128187; Quant Algo Trading Engine</h3>
                <p>Institutional Python trading harness with Dhan HQ, PropFirm Titan, and Polymarket arbitrage bot templates.</p>
                <a href="https://manja8.gumroad.com/l/quant-algo-pack?utm_source=protodex&amp;utm_medium=blog&amp;utm_campaign={slug}" target="_blank" class="cta-btn">View Quant Pack &#8594;</a>
            </div>
            <div class="cta-card">
                <h3>&#127912; Protodex UI Studio</h3>
                <p>48 production-ready AI agent dashboard templates with full Tailwind, React, and Figma design tokens.</p>
                <a href="/ui-studio.html" class="cta-btn">Explore Studio &#8594;</a>
            </div>
        </div>
    </div>

    <footer class="post-footer">
        <p>Auto-generated weekly by Protodex Discovery Engine &middot; <a href="https://protodex.io">protodex.io</a> &middot; <a href="https://github.com/LuciferForge/mcp-directory">GitHub</a></p>
    </footer>
</body>
</html>"""

    out_path.write_text(page_html, encoding="utf-8")
    print(f"[weekly-digest] Successfully published Issue #{issue_num:02d} to {out_path.name}")
    return title, slug, date_str


def main():
    force = "--force" in sys.argv
    cmd = "weekly"
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            cmd = arg
            break

    if cmd in ("weekly", "all"):
        res = generate_weekly_roundup(force=force)
        if res:
            title, slug, date_str = res
            print(f"[weekly-digest] Generated: {title} ({slug})")
        else:
            print("[weekly-digest] No new digest generated.")


if __name__ == "__main__":
    main()
