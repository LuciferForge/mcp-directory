# Protodex — The MCP Server Index

**[protodex.io](http://protodex.io)** — Search 1,629+ Model Context Protocol servers. Find the right MCP server for Claude, Cursor, and AI agents.

[![Servers](https://img.shields.io/badge/servers-1%2C629-8B5CF6)](http://protodex.io)
[![Categories](https://img.shields.io/badge/categories-13-22C55E)](http://protodex.io/categories.html)
[![Languages](https://img.shields.io/badge/languages-31-3B82F6)](http://protodex.io)
[![Updated](https://img.shields.io/badge/updated-weekly-EAB308)](http://protodex.io)

## Browse at [protodex.io](http://protodex.io)

- Instant search across all 1,629 servers
- 13 categories: AI/LLM, Database, API Integration, Security, DevOps, and more
- Individual pages for every server with metadata, tools, and related servers
- Ranked by GitHub stars so you find battle-tested tools first
- Updated weekly via automated GitHub scraper

## What's Indexed

| Category | Servers | Top Repo |
|----------|---------|----------|
| AI/LLM | 779 | gemini-cli (97K stars) |
| Code/Dev Tools | 180 | — |
| API Integration | 102 | n8n (179K stars) |
| Memory/Knowledge | 97 | modelcontextprotocol/servers (81K) |
| Database | 75 | — |
| Browser/Web | 46 | Scrapling (29K) |
| Security | 44 | — |
| Search | 43 | — |
| DevOps | 41 | — |
| Data/Analytics | 27 | — |
| Communication | 22 | — |
| File System | 15 | — |
| Other | 158 | — |

**Languages:** Python (570), TypeScript (548), JavaScript (121), Go (103), Rust (51), C# (25), Java (22), and 24 more.

## Run the Scraper Yourself

```bash
python3 -m pip install requests

# Scrape GitHub for MCP servers (~2 min)
python3 mcp_directory.py scrape

# Browse
python3 mcp_directory.py stats           # Category breakdown
python3 mcp_directory.py top             # Top servers by stars
python3 mcp_directory.py search slack    # Search by keyword
python3 mcp_directory.py category Database  # List by category
python3 mcp_directory.py export          # Export as JSON
```

## Build the Website

```bash
python3 build_site.py    # Generates all 1,647 HTML pages into docs/
```

The static site is served via GitHub Pages at [protodex.io](http://protodex.io).

## Data

- `mcp_directory.json` — Full dataset (all servers with metadata)
- `mcp_by_category.json` — Grouped by category
- `mcp_directory.db` — SQLite database

## How It Works

The scraper searches GitHub using 11 different queries targeting MCP server repos:
- Repo names containing `mcp-server` or `mcp_server`
- Topics: `mcp-server`, `model-context-protocol`
- Code references to `FastMCP`, `@modelcontextprotocol/sdk`
- Description matches

Each repo is auto-categorized into 13 categories based on name, description, and topics.

## Submit a Server

- [Submit via GitHub Issue](https://github.com/LuciferForge/mcp-directory/issues/new?title=Add+server:+[repo-name]&body=Repository+URL:+%0A%0ACategory:+%0A%0ABrief+description:+)
- [Request a server](https://github.com/LuciferForge/mcp-directory/discussions/new?category=ideas) you'd like to see indexed

## License

MIT

---

Built by [LuciferForge](https://github.com/LuciferForge) | [protodex.io](http://protodex.io)
