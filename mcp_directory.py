#!/usr/bin/env python3
"""
MCP Server Directory — CLI Interface
Search, browse, and export the MCP server registry.

Usage:
    python3 mcp_directory.py scrape          # Scrape GitHub for MCP servers
    python3 mcp_directory.py list            # List all indexed servers
    python3 mcp_directory.py search <query>  # Search by keyword
    python3 mcp_directory.py stats           # Show category breakdown
    python3 mcp_directory.py export          # Export as JSON
    python3 mcp_directory.py top [n]         # Top N by stars (default 20)
    python3 mcp_directory.py category <name> # List servers in a category
"""

import sys
import json
import sqlite3
from datetime import datetime

DB_PATH = "/Users/apple/Documents/LuciferForge/mcp-directory/mcp_directory.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def cmd_scrape():
    from scraper import scrape
    print("Starting MCP Server Directory scrape...")
    print("=" * 60)
    count = scrape(fetch_readmes=True, readme_batch_size=80)
    print(f"\nDone. Added {count} servers.")
    # Show stats after scrape
    print()
    cmd_stats()


def cmd_list():
    conn = get_db()
    rows = conn.execute(
        "SELECT repo, stars, category, language, description FROM servers ORDER BY stars DESC"
    ).fetchall()

    if not rows:
        print("No servers indexed. Run: python3 mcp_directory.py scrape")
        return

    print(f"{'Repo':<45} {'Stars':>6}  {'Category':<20} {'Lang':<12} Description")
    print("-" * 130)
    for r in rows:
        desc = (r["description"] or "")[:40]
        print(f"{r['repo']:<45} {r['stars']:>6}  {r['category']:<20} {(r['language'] or ''):.<12} {desc}")

    print(f"\nTotal: {len(rows)} servers")


def cmd_search(query):
    conn = get_db()
    like = f"%{query}%"
    rows = conn.execute("""
        SELECT repo, stars, category, language, description, tools
        FROM servers
        WHERE repo LIKE ? OR description LIKE ? OR tools LIKE ?
           OR category LIKE ? OR topics LIKE ? OR readme_excerpt LIKE ?
        ORDER BY stars DESC
    """, (like, like, like, like, like, like)).fetchall()

    if not rows:
        print(f"No results for '{query}'")
        return

    print(f"Search results for '{query}': {len(rows)} matches\n")
    print(f"{'Repo':<45} {'Stars':>6}  {'Category':<20} Description")
    print("-" * 120)
    for r in rows:
        desc = (r["description"] or "")[:45]
        print(f"{r['repo']:<45} {r['stars']:>6}  {r['category']:<20} {desc}")

    # Show tools if any
    tools_found = [(r["repo"], r["tools"]) for r in rows if r["tools"]]
    if tools_found:
        print(f"\nTools found in matching servers:")
        for repo, tools in tools_found[:10]:
            print(f"  {repo}: {tools}")


def cmd_stats():
    conn = get_db()

    total = conn.execute("SELECT COUNT(*) FROM servers").fetchone()[0]
    if total == 0:
        print("No servers indexed.")
        return

    print(f"MCP Server Directory — {total} servers indexed")
    print("=" * 50)

    # Category breakdown
    cats = conn.execute("""
        SELECT category, COUNT(*) as cnt, SUM(stars) as total_stars,
               ROUND(AVG(stars), 1) as avg_stars
        FROM servers
        GROUP BY category
        ORDER BY cnt DESC
    """).fetchall()

    print(f"\n{'Category':<25} {'Count':>6} {'Total Stars':>12} {'Avg Stars':>10}")
    print("-" * 55)
    for c in cats:
        print(f"{c['category']:<25} {c['cnt']:>6} {c['total_stars']:>12} {c['avg_stars']:>10}")

    # Language breakdown
    print(f"\nTop Languages:")
    langs = conn.execute("""
        SELECT language, COUNT(*) as cnt
        FROM servers WHERE language IS NOT NULL AND language != ''
        GROUP BY language ORDER BY cnt DESC LIMIT 10
    """).fetchall()
    for l in langs:
        print(f"  {l['language']:<20} {l['cnt']:>4} servers")

    # Top 10 by stars
    print(f"\nTop 10 by Stars:")
    top = conn.execute("""
        SELECT repo, stars, category FROM servers ORDER BY stars DESC LIMIT 10
    """).fetchall()
    for i, r in enumerate(top, 1):
        print(f"  {i:>2}. {r['repo']:<45} {r['stars']:>6} stars  [{r['category']}]")

    # Age stats
    newest = conn.execute(
        "SELECT repo, last_updated FROM servers ORDER BY last_updated DESC LIMIT 1"
    ).fetchone()
    oldest = conn.execute(
        "SELECT repo, last_updated FROM servers ORDER BY last_updated ASC LIMIT 1"
    ).fetchone()
    if newest and oldest:
        print(f"\nMost recently updated: {newest['repo']} ({newest['last_updated'][:10]})")
        print(f"Oldest update: {oldest['repo']} ({oldest['last_updated'][:10]})")

    # Servers with tools extracted
    with_tools = conn.execute(
        "SELECT COUNT(*) FROM servers WHERE tools IS NOT NULL AND tools != ''"
    ).fetchone()[0]
    print(f"\nServers with tools extracted: {with_tools}/{total}")


def cmd_top(n=20):
    conn = get_db()
    rows = conn.execute("""
        SELECT repo, stars, category, language, description
        FROM servers ORDER BY stars DESC LIMIT ?
    """, (n,)).fetchall()

    print(f"Top {n} MCP Servers by Stars\n")
    for i, r in enumerate(rows, 1):
        desc = (r["description"] or "")[:60]
        print(f"{i:>3}. {r['repo']:<45} {r['stars']:>6} stars")
        print(f"     [{r['category']}] [{r['language'] or 'N/A'}] {desc}")


def cmd_category(name):
    conn = get_db()
    rows = conn.execute("""
        SELECT repo, stars, language, description, tools
        FROM servers WHERE LOWER(category) = LOWER(?)
        ORDER BY stars DESC
    """, (name,)).fetchall()

    if not rows:
        # Try partial match
        rows = conn.execute("""
            SELECT repo, stars, language, description, tools
            FROM servers WHERE LOWER(category) LIKE LOWER(?)
            ORDER BY stars DESC
        """, (f"%{name}%",)).fetchall()

    if not rows:
        print(f"No servers in category '{name}'")
        cats = conn.execute("SELECT DISTINCT category FROM servers ORDER BY category").fetchall()
        print(f"Available categories: {', '.join(c['category'] for c in cats)}")
        return

    print(f"Category: {name} — {len(rows)} servers\n")
    print(f"{'Repo':<45} {'Stars':>6}  {'Lang':<12} Description")
    print("-" * 110)
    for r in rows:
        desc = (r["description"] or "")[:45]
        print(f"{r['repo']:<45} {r['stars']:>6}  {(r['language'] or ''):.<12} {desc}")


def cmd_export():
    conn = get_db()
    rows = conn.execute("SELECT * FROM servers ORDER BY stars DESC").fetchall()

    data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_servers": len(rows),
        "servers": [dict(r) for r in rows],
    }

    out_path = "/Users/apple/Documents/LuciferForge/mcp-directory/mcp_directory.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    print(f"Exported {len(rows)} servers to {out_path}")

    # Also export category summary
    cats = {}
    for r in rows:
        cat = dict(r)["category"]
        if cat not in cats:
            cats[cat] = []
        cats[cat].append({
            "repo": dict(r)["repo"],
            "stars": dict(r)["stars"],
            "description": dict(r)["description"],
            "url": dict(r)["url"],
        })

    cat_path = "/Users/apple/Documents/LuciferForge/mcp-directory/mcp_by_category.json"
    with open(cat_path, "w") as f:
        json.dump(cats, f, indent=2)
    print(f"Exported category index to {cat_path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "scrape":
        cmd_scrape()
    elif cmd == "list":
        cmd_list()
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: python3 mcp_directory.py search <query>")
            return
        cmd_search(" ".join(sys.argv[2:]))
    elif cmd == "stats":
        cmd_stats()
    elif cmd == "top":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        cmd_top(n)
    elif cmd == "category":
        if len(sys.argv) < 3:
            print("Usage: python3 mcp_directory.py category <name>")
            return
        cmd_category(" ".join(sys.argv[2:]))
    elif cmd == "export":
        cmd_export()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
