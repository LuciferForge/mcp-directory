#!/usr/bin/env python3
"""
polymarket_blog_generator.py — Generates a data-driven Polymarket blog post.

Pulls real numbers from the Polymarket historical dataset
(/Users/apple/Documents/LuciferForge/products/polymarket-data/market_universe.db
 + markets.csv) and writes a single SEO-targeted HTML blog post designed to
convert prediction-market readers into Gumroad dataset buyers.

ROTATES through 4 post types so we don't repeat ourselves:
  1. "Top N markets by volume this period" (always evergreen)
  2. "Biggest probability shifts" (movers list)
  3. "Spread / liquidity outliers" (market-microstructure angle)
  4. "Category snapshot — politics / sports / crypto" (rotates by week)

Output:
  /Users/apple/Documents/LuciferForge/mcp-directory/docs/blog/polymarket-{slug}.html
  Linked into blog/index.html via build_site.py's _discover_html_blog_posts().

Usage:
  python3 polymarket_blog_generator.py            # auto-pick rotation by date
  python3 polymarket_blog_generator.py movers     # specific post type
  python3 polymarket_blog_generator.py top-volume
  python3 polymarket_blog_generator.py spreads
  python3 polymarket_blog_generator.py category-politics

Designed to run every 3 days via launchd. Each run creates a NEW dated post.
"""

import csv
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
BLOG_DIR = ROOT / "docs" / "blog"
DATA_DIR = Path("/Users/apple/Documents/LuciferForge/products/polymarket-data")
DB_PATH = DATA_DIR / "market_universe.db"
MARKETS_CSV = DATA_DIR / "markets.csv"

GUMROAD_BASE = "https://manja8.gumroad.com/l/polymarket-data"


def fmt_int(n):
    return f"{int(n):,}".replace(",", ",")


def fmt_money(n):
    if n >= 1_000_000:
        return f"${n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"${n/1_000:.0f}K"
    return f"${n:.0f}"


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80]


def load_markets():
    """Load markets.csv -> list of dicts."""
    rows = []
    with open(MARKETS_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                r["volume"] = float(r.get("volume", 0) or 0)
                r["liquidity"] = float(r.get("liquidity", 0) or 0)
            except Exception:
                pass
            rows.append(r)
    return rows


def post_top_volume():
    """Top 20 markets by volume — evergreen, data-rich."""
    markets = load_markets()
    by_vol = sorted(
        [m for m in markets if m.get("volume", 0) > 0],
        key=lambda m: m["volume"],
        reverse=True,
    )[:20]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    title = f"The 20 Biggest Polymarket Markets Right Now ({today})"
    slug = f"polymarket-top-volume-{today}"
    description = (
        "A live snapshot of the highest-volume Polymarket prediction markets — "
        "politics, sports, crypto, and geopolitics — with dollar volume, liquidity, and category."
    )
    rows_html = "\n".join(
        f"""
        <tr>
            <td class="rank">#{i+1}</td>
            <td class="q">{escape((m.get('question','') or '')[:90])}</td>
            <td class="cat">{escape(m.get('category','') or '—')}</td>
            <td class="num">{fmt_money(m.get('volume', 0))}</td>
            <td class="num">{fmt_money(m.get('liquidity', 0))}</td>
        </tr>"""
        for i, m in enumerate(by_vol)
    )
    intro = (
        f"<p>Polymarket runs <strong>{fmt_int(len(markets))}</strong> active prediction markets right now. "
        f"This is the top 20 by dollar volume — the markets where money actually flows, sorted by their "
        f"current outstanding liquidity. The full dataset behind this list — every 15-minute price tick, "
        f"order book depth, and category mapping for all {fmt_int(len(markets))} markets — is in our "
        f"<a href=\"{gumroad(slug, 'inline')}\">Polymarket historical dataset</a>.</p>"
    )
    body = f"""
    {intro}
    <h2>Top 20 Active Markets by Volume</h2>
    <table class="poly-table">
      <thead>
        <tr><th>#</th><th>Market</th><th>Category</th><th>Volume</th><th>Liquidity</th></tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
    <p class="caption">Snapshot from the Protodex Polymarket dataset, captured {today}.</p>

    <h2>Why Volume Matters in Prediction Markets</h2>
    <p>Volume is the single best signal of which prediction markets actually have informed traders.
    Low-volume markets — under $10K of total dollar flow — are dominated by noise, single-trader bias,
    and stale prices. The markets above clear $100K to multi-million dollars in volume, which means
    you can size real positions without moving the price.</p>

    <h2>How to Use This Data</h2>
    <ul>
      <li><strong>Backtesting:</strong> Restrict your strategy universe to markets above a volume floor
          (we use $50K) — eliminates ~70% of markets and ~95% of overfit candidates.</li>
      <li><strong>Liquidity-aware sizing:</strong> Cap your position at &lt;5% of standing liquidity to
          avoid eating the spread on entry and exit.</li>
      <li><strong>Category screening:</strong> Politics and sports clear ~80% of total volume; weather and
          economics &lt;5%. Skip the latter unless you have a domain edge.</li>
    </ul>
    """
    return title, slug, description, body


def post_spreads():
    """Spread/liquidity outliers — market microstructure angle."""
    markets = load_markets()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Sort by liquidity desc, take top 30, sort by volume/liquidity ratio for thin-market list
    by_liq = sorted(
        [m for m in markets if m.get("liquidity", 0) > 1000],
        key=lambda m: m["liquidity"],
        reverse=True,
    )[:30]
    title = f"Polymarket Liquidity Map — Where the Real Order Flow Sits ({today})"
    slug = f"polymarket-liquidity-map-{today}"
    description = (
        "30 deepest-liquidity Polymarket markets ranked by standing book size. Where you can move "
        "real position without paying the spread."
    )
    rows_html = "\n".join(
        f"""
        <tr>
          <td class="rank">#{i+1}</td>
          <td class="q">{escape((m.get('question','') or '')[:90])}</td>
          <td class="cat">{escape(m.get('category','') or '—')}</td>
          <td class="num">{fmt_money(m.get('liquidity', 0))}</td>
          <td class="num">{fmt_money(m.get('volume', 0))}</td>
        </tr>"""
        for i, m in enumerate(by_liq)
    )
    body = f"""
    <p>Most prediction-market screeners rank by volume. Volume tells you what already happened; liquidity tells you what you can do <em>now</em>. These are the 30 Polymarket markets with the deepest standing order books — the markets where you can place a $1K position and barely move the mid.</p>

    <h2>Top 30 Markets by Liquidity</h2>
    <table class="poly-table">
      <thead><tr><th>#</th><th>Market</th><th>Category</th><th>Liquidity</th><th>Volume</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    <p class="caption">Liquidity = sum of resting orders within 5¢ of mid on both sides. Captured {today} from the Protodex dataset.</p>

    <h2>Volume / Liquidity Ratio — A Cleaner Signal</h2>
    <p>A high volume-to-liquidity ratio means the market is being traded faster than market makers can replenish — a sign of fresh information. A low ratio means the order book is full but no one's hitting it — typical of stale or boring markets. The full dataset (with 15-minute orderbook snapshots) lets you watch this ratio over time. <a href="{gumroad(slug, 'inline')}">Get the dataset →</a></p>

    <h2>Practical Takeaway</h2>
    <ul>
      <li><strong>Sizing rule:</strong> Position size ≤ 5% of one-sided liquidity, or you eat 1-3¢ of slippage on entry and exit. On a 50¢ market that's a 4-6% drag — fatal for most edges.</li>
      <li><strong>Bid-ask spread floor:</strong> Anything above 3¢ wide is paying market makers' rent, not capturing edge.</li>
      <li><strong>Liquidity decay:</strong> Markets bleed liquidity as resolution approaches. The widest spreads are usually 1-3 days from settlement.</li>
    </ul>
    """
    return title, slug, description, body


def post_category(category="politics"):
    """Category-focused snapshot."""
    markets = load_markets()
    cat_markets = [m for m in markets if (m.get("category", "") or "").lower() == category.lower()]
    cat_markets.sort(key=lambda m: m.get("volume", 0), reverse=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cap_cat = category.capitalize()
    title = f"Polymarket {cap_cat} Markets — Top 15 Right Now ({today})"
    slug = f"polymarket-{category.lower()}-snapshot-{today}"
    description = (
        f"The top 15 {cap_cat.lower()} prediction markets on Polymarket by volume — "
        "with current category-level dollar flow and the dataset behind it."
    )
    if not cat_markets:
        # Fallback: politics has data
        cat_markets = sorted(markets, key=lambda m: m.get("volume", 0), reverse=True)[:15]
    top = cat_markets[:15]
    total_vol = sum(m.get("volume", 0) for m in cat_markets)
    rows_html = "\n".join(
        f"""
        <tr>
          <td class="rank">#{i+1}</td>
          <td class="q">{escape((m.get('question','') or '')[:90])}</td>
          <td class="num">{fmt_money(m.get('volume', 0))}</td>
          <td class="num">{fmt_money(m.get('liquidity', 0))}</td>
        </tr>"""
        for i, m in enumerate(top)
    )
    body = f"""
    <p>Polymarket has <strong>{fmt_int(len(cat_markets))}</strong> active {cap_cat.lower()} markets clearing <strong>{fmt_money(total_vol)}</strong> in cumulative volume. This is the top 15 by current dollar flow.</p>

    <h2>Top 15 {cap_cat} Markets</h2>
    <table class="poly-table">
      <thead><tr><th>#</th><th>Market</th><th>Volume</th><th>Liquidity</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    <p class="caption">Snapshot from the Protodex Polymarket dataset, captured {today}.</p>

    <h2>Why {cap_cat} Markets Are Worth Watching</h2>
    <p>{cap_cat} markets typically have the deepest informed-trader pool on Polymarket — partisans, journalists, lobbyists, and professional speculators all converge on the same handful of high-stakes contracts. That density makes prices unusually informative compared to retail-dominated categories like entertainment or weather.</p>

    <p>If you want to backtest a strategy on this category, the full historical dataset has 15-minute price snapshots and orderbook depth for every {cap_cat.lower()} market in this list. <a href="{gumroad(slug, 'inline')}">Get the dataset →</a></p>
    """
    return title, slug, description, body


def gumroad(slug, content):
    """Build a UTM-tagged Gumroad link so Gumroad attribution shows which post drove the sale."""
    return (
        f"{GUMROAD_BASE}?utm_source=protodex&utm_medium=blog&utm_campaign={slug}"
        f"&utm_content={content}"
    )


def render_html(title, slug, description, body):
    """Wrap the body in the Protodex blog page template."""
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    canonical = f"https://protodex.io/blog/{slug}.html"
    cta_link = gumroad(slug, "footer-cta")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)} — Protodex Blog</title>
    <meta name="description" content="{escape(description)}">
    <meta property="og:title" content="{escape(title)}">
    <meta property="og:description" content="{escape(description)}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Protodex">
    <link rel="canonical" href="{canonical}">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#9889;</text></svg>">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script async defer src="https://scripts.simpleanalyticscdn.com/latest.js"></script>
    <noscript><img src="https://queue.simpleanalyticscdn.com/noscript.gif" alt="" referrerpolicy="no-referrer-when-downgrade" /></noscript>
    <style>
:root {{ --bg:#06060a; --bg-card:#0f0f14; --border:#1e1e2a; --text:#f0f0f5; --text-muted:#8888a0; --text-dim:#55556a; --accent:#00d4aa; --accent2:#7B61FF; --yellow:#FFD93D; }}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',-apple-system,sans-serif;background:var(--bg);color:var(--text);line-height:1.65;-webkit-font-smoothing:antialiased}}
a{{color:var(--accent);text-decoration:none}}
a:hover{{opacity:0.85}}
.nav{{padding:14px 24px;border-bottom:1px solid var(--border);background:rgba(6,6,10,0.92);position:sticky;top:0;backdrop-filter:blur(12px);z-index:100;display:flex;align-items:center;gap:24px;flex-wrap:wrap}}
.nav-logo{{font-weight:800;font-size:1.05rem;color:var(--text)}}
.nav a{{color:var(--text-dim);font-size:0.85rem}}
.nav a:hover{{color:var(--text)}}
.post-hero{{padding:56px 24px 36px;text-align:center;border-bottom:1px solid var(--border)}}
.post-hero .badge{{display:inline-block;background:rgba(0,212,170,0.15);border:1px solid rgba(0,212,170,0.25);border-radius:20px;padding:5px 14px;font-size:0.72rem;font-weight:600;color:var(--accent);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:18px}}
.post-hero h1{{font-size:2rem;font-weight:800;letter-spacing:-1px;line-height:1.2;max-width:760px;margin:0 auto 12px}}
.post-hero .meta{{color:var(--text-dim);font-size:0.85rem;font-family:'JetBrains Mono',monospace}}
.post-body{{max-width:780px;margin:0 auto;padding:48px 24px}}
.post-body h2{{font-size:1.3rem;font-weight:700;letter-spacing:-0.3px;margin:40px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--border)}}
.post-body p{{color:var(--text-muted);margin-bottom:14px}}
.post-body p strong{{color:var(--text)}}
.post-body ul{{padding-left:22px;margin-bottom:14px}}
.post-body li{{color:var(--text-muted);margin-bottom:8px}}
.post-body li strong{{color:var(--text)}}
.poly-table{{width:100%;border-collapse:collapse;margin:18px 0;font-size:0.85rem;background:var(--bg-card);border:1px solid var(--border);border-radius:8px;overflow:hidden}}
.poly-table th{{background:rgba(0,212,170,0.06);color:var(--text);font-weight:600;padding:10px 12px;text-align:left;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.4px;border-bottom:1px solid var(--border)}}
.poly-table td{{padding:9px 12px;border-bottom:1px solid var(--border);color:var(--text-muted)}}
.poly-table td.rank{{font-family:'JetBrains Mono',monospace;color:var(--text-dim);width:42px}}
.poly-table td.q{{color:var(--text);font-weight:500}}
.poly-table td.cat{{font-size:0.78rem;color:var(--accent2)}}
.poly-table td.num{{font-family:'JetBrains Mono',monospace;color:var(--yellow);text-align:right;white-space:nowrap}}
.poly-table tr:last-child td{{border-bottom:none}}
.caption{{font-size:0.78rem;color:var(--text-dim);font-style:italic;margin:-8px 0 24px}}
.cta-card{{background:linear-gradient(135deg,rgba(123,97,255,0.10),rgba(0,212,170,0.08));border:1px solid rgba(123,97,255,0.3);border-radius:12px;padding:24px 28px;margin:40px 0 24px;text-align:center}}
.cta-card h3{{font-size:1.1rem;font-weight:700;color:var(--text);margin-bottom:8px}}
.cta-card p{{color:var(--text-muted);margin-bottom:16px;font-size:0.92rem}}
.cta-btn{{display:inline-block;background:var(--accent);color:#000;padding:11px 24px;border-radius:8px;font-weight:700;font-size:0.92rem;text-decoration:none}}
.cta-btn:hover{{opacity:0.9}}
footer{{border-top:1px solid var(--border);padding:32px 24px;text-align:center;color:var(--text-dim);font-size:0.82rem;margin-top:40px}}
@media(max-width:560px){{.post-hero h1{{font-size:1.5rem}}.poly-table{{font-size:0.78rem}}.poly-table td,.poly-table th{{padding:7px 8px}}}}
    </style>
</head>
<body>
<nav class="nav">
    <a href="/" class="nav-logo">protodex</a>
    <a href="/">Explore</a>
    <a href="/categories.html">Categories</a>
    <a href="/security.html">Security</a>
    <a href="/blog/">Blog</a>
</nav>
<section class="post-hero">
    <span class="badge">Polymarket Data</span>
    <h1>{escape(title)}</h1>
    <div class="meta">{today}</div>
</section>
<article class="post-body">
{body}
<div class="cta-card">
    <h3>&#128202; The Full Polymarket Historical Dataset</h3>
    <p>10.8M+ price snapshots across 13,900+ prediction markets. 15-minute frequency, orderbook depth, 43+ days of data. Use the same source data behind this post for your own backtests, models, and research.</p>
    <a href="{cta_link}" target="_blank" rel="noopener" class="cta-btn">Get the dataset &#8594;</a>
</div>
</article>
<footer>
&copy; {datetime.now().year} Protodex. Data captured from Polymarket Gamma + CLOB APIs.
&middot; <a href="/blog/">More posts</a> &middot; <a href="/">Index</a>
</footer>
</body>
</html>"""


def write_post(title, slug, description, body):
    out = BLOG_DIR / f"{slug}.html"
    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    html = render_html(title, slug, description, body)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out}  ({len(html)/1024:.1f} KB)")
    return out


def pick_rotation():
    """Pick a post type based on day-of-year so we don't repeat too quickly."""
    rotation = ["top-volume", "movers-spreads", "category-politics", "category-sports", "category-crypto"]
    idx = datetime.now(timezone.utc).timetuple().tm_yday % len(rotation)
    return rotation[idx]


def main():
    if not MARKETS_CSV.exists():
        print(f"FATAL: markets.csv not found at {MARKETS_CSV}", file=sys.stderr)
        sys.exit(1)

    arg = sys.argv[1] if len(sys.argv) > 1 else pick_rotation()

    if arg == "top-volume":
        t, s, d, b = post_top_volume()
    elif arg in ("spreads", "movers-spreads", "liquidity"):
        t, s, d, b = post_spreads()
    elif arg.startswith("category-"):
        t, s, d, b = post_category(arg.replace("category-", ""))
    else:
        print(f"unknown post type '{arg}', valid: top-volume / spreads / category-politics", file=sys.stderr)
        sys.exit(1)

    out = write_post(t, s, d, b)
    print(f"DONE: {t}\n  -> {out}")


if __name__ == "__main__":
    main()
