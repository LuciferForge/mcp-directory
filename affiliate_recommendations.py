"""affiliate_recommendations.py — contextual affiliate recommendations for protodex.io MCP server pages.

Returns an HTML snippet to inject into each server detail page based on the server's category.

CONFIG: edit /Users/apple/Documents/LuciferForge/mcp-directory/affiliate_links.json
        when you have actual affiliate codes from each program. Until then, links go to
        each program's homepage WITHOUT a referral code (you keep the traffic but
        don't earn commissions until codes are filled in).

USAGE in build_site.py:
    from affiliate_recommendations import affiliate_sidebar_html
    ...
    sidebar = affiliate_sidebar_html(server)
    html += sidebar  # inject after topics_section, before related_html
"""
from __future__ import annotations
import json
from pathlib import Path
from html import escape

CONFIG_PATH = Path(__file__).parent / "affiliate_links.json"

# Default config (placeholder — overridden by affiliate_links.json if it exists)
DEFAULT_CONFIG = {
    "_note": "Replace each url with your actual affiliate URL once signed up. Without a referral code, link sends traffic but earns $0.",
    "mongodb": {
        "name": "MongoDB Atlas",
        "url": "https://www.mongodb.com/cloud/atlas/register",
        "blurb": "Cloud DB for your MCP server's data. Free tier covers most prototypes.",
        "category_match": ["Database", "data", "Search & Knowledge"],
    },
    "digitalocean": {
        "name": "DigitalOcean",
        "url": "https://www.digitalocean.com/",
        "blurb": "Deploy your MCP server on a $6/mo droplet. New users get $200 credit.",
        "category_match": ["Cloud Platforms", "Infrastructure", "DevOps"],
    },
    "linode": {
        "name": "Linode (Akamai)",
        "url": "https://www.linode.com/",
        "blurb": "Alternative to DigitalOcean. $5/mo plans, $100 credit for new accounts.",
        "category_match": ["Cloud Platforms", "Infrastructure", "DevOps"],
    },
    "hostinger": {
        "name": "Hostinger",
        "url": "https://www.hostinger.com/",
        "blurb": "Cheap hosting + free domain for your MCP server's landing page.",
        "category_match": ["Cloud Platforms", "Infrastructure"],
    },
    "notion": {
        "name": "Notion",
        "url": "https://www.notion.com/",
        "blurb": "Plug your Claude into your team's Notion workspace.",
        "category_match": ["Productivity", "Knowledge", "Communication"],
    },
    "jetbrains": {
        "name": "JetBrains All Products Pack",
        "url": "https://www.jetbrains.com/store/",
        "blurb": "IDEs + AI assistant. The dev tools your MCP server author probably uses.",
        "category_match": ["Developer Tools", "AI/LLM"],
    },
    "cloudflare": {
        "name": "Cloudflare Workers + R2",
        "url": "https://www.cloudflare.com/products/workers/",
        "blurb": "Edge-deploy your MCP server globally. Generous free tier.",
        "category_match": ["Cloud Platforms", "Infrastructure", "DevOps"],
    },
    "razorpay": {
        "name": "Razorpay (India)",
        "url": "https://razorpay.com/",
        "blurb": "Charge your MCP customers in INR. India-focused payment gateway.",
        "category_match": ["Finance", "Payments", "Commerce"],
    },
    "polar": {
        "name": "Polar.sh",
        "url": "https://polar.sh/",
        "blurb": "Charge subscriptions for your MCP server. License keys auto-issued.",
        "category_match": ["Finance", "Payments", "Developer Tools"],
    },
    "webflow": {
        "name": "Webflow",
        "url": "https://webflow.com/",
        "blurb": "Build a marketing site for your MCP server without writing CSS.",
        "category_match": ["Productivity", "Design"],
    },
}


def _load_config() -> dict:
    """Load config from JSON file if exists, else use defaults."""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return DEFAULT_CONFIG


def _matches_category(prog: dict, server_category: str, server_topics: list[str]) -> bool:
    """Return True if this affiliate program is relevant for this server."""
    matches = prog.get("category_match", [])
    cat_lower = (server_category or "").lower()
    topics_lower = [t.lower() for t in (server_topics or [])]
    for m in matches:
        ml = m.lower()
        if ml in cat_lower:
            return True
        for t in topics_lower:
            if ml in t:
                return True
    return False


def _utm_link(url: str, campaign: str = "mcp_directory") -> str:
    """Append UTM tracking so we can identify clicks coming from protodex.io."""
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}utm_source=protodex&utm_medium=affiliate&utm_campaign={campaign}"


def affiliate_sidebar_html(server: dict, max_recs: int = 3) -> str:
    """Generate the affiliate recommendations sidebar HTML for a given MCP server detail page.

    Selects up to `max_recs` programs whose category_match overlaps the server's
    category or topics. Returns empty string if no matches (always-empty is fine —
    not every page needs to monetize).
    """
    config = _load_config()
    programs = [(k, v) for k, v in config.items() if not k.startswith("_") and isinstance(v, dict)]

    server_cat = server.get("category", "")
    server_topics = [t.strip() for t in (server.get("topics") or "").split(",") if t.strip()]

    # Score each program by relevance + use a stable order on ties
    matched = [(k, v) for k, v in programs if _matches_category(v, server_cat, server_topics)]
    if not matched:
        return ""

    # Pick top N
    selected = matched[:max_recs]

    items_html = ""
    for key, prog in selected:
        url = _utm_link(prog["url"], campaign=f"mcp_{key}")
        items_html += f"""
        <a href="{escape(url)}" class="aff-card" target="_blank" rel="noopener nofollow sponsored">
            <div class="aff-name">{escape(prog["name"])}</div>
            <div class="aff-blurb">{escape(prog["blurb"])}</div>
        </a>"""

    sidebar = f"""
    <div class="detail-section affiliate-recommendations">
        <h2>Recommended infrastructure for this MCP server</h2>
        <div style="font-size:13px;color:var(--text-muted);margin-bottom:12px">
            Affiliate-supported recommendations. Picked based on this server's category. Using these links costs you nothing extra and helps keep protodex.io free.
        </div>
        <div class="aff-grid">{items_html}
        </div>
    </div>"""
    return sidebar


def affiliate_recommendations_css() -> str:
    """CSS to inject into the page. Keeps styling consistent with the rest of the site."""
    return """
.affiliate-recommendations { margin-top: 24px; }
.aff-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
.aff-card {
    display: block;
    padding: 16px;
    background: var(--bg-card, #0f0f14);
    border: 1px solid var(--border, #1e1e2a);
    border-radius: 10px;
    text-decoration: none;
    color: inherit;
    transition: all 0.15s;
}
.aff-card:hover {
    border-color: var(--accent, #00d4aa);
    transform: translateY(-1px);
}
.aff-name {
    font-weight: 600;
    font-size: 15px;
    color: var(--accent, #00d4aa);
    margin-bottom: 6px;
}
.aff-blurb {
    font-size: 13px;
    color: var(--text-muted, #8888a0);
    line-height: 1.4;
}
"""


def recommended_page_html() -> str:
    """Standalone /recommended page — full curated list of all affiliate programs."""
    config = _load_config()
    programs = [(k, v) for k, v in config.items() if not k.startswith("_") and isinstance(v, dict)]

    rows = ""
    for key, prog in programs:
        url = _utm_link(prog["url"], campaign=f"recommended_{key}")
        cats = ", ".join(prog.get("category_match", []))
        rows += f"""
        <a href="{escape(url)}" class="aff-card" target="_blank" rel="noopener nofollow sponsored">
            <div class="aff-name">{escape(prog["name"])}</div>
            <div class="aff-blurb">{escape(prog["blurb"])}</div>
            <div style="font-size:11px;color:var(--text-dim,#55556a);margin-top:8px">Best for: {escape(cats)}</div>
        </a>"""

    return f"""
<div class="container" style="max-width:900px;padding:32px 24px">
    <h1 style="font-size:36px;letter-spacing:-0.02em;margin-bottom:8px">Recommended for MCP builders</h1>
    <p style="color:var(--text-muted);margin-bottom:24px">
        Curated infrastructure + tooling we recommend for anyone building or running MCP servers.
        Affiliate-supported — using these links costs you nothing extra and helps keep protodex.io free.
    </p>
    <div class="aff-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px">
        {rows}
    </div>
</div>
"""
