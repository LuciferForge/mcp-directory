# Protodex — The MCP Server Index

**[protodex.io](http://protodex.io)** — Search 18,146+ Model Context Protocol servers. Find the right MCP server for Claude, Cursor, and AI agents.

[![Servers](https://img.shields.io/badge/servers-18%2C146-8B5CF6)](http://protodex.io)
[![Categories](https://img.shields.io/badge/categories-13-22C55E)](http://protodex.io/categories.html)
[![Languages](https://img.shields.io/badge/languages-68-3B82F6)](http://protodex.io)
[![Updated](https://img.shields.io/badge/updated-weekly-EAB308)](http://protodex.io)

## Browse at [protodex.io](http://protodex.io)

- Instant search across all 18,146 servers
- 13 categories: AI/LLM, Database, API Integration, Security, DevOps, and more
- Individual pages for every server with metadata, tools, and related servers
- Ranked by GitHub stars so you find battle-tested tools first
- Updated weekly via automated GitHub scraper

## What's Indexed

| Category | Servers | Top Repo |
|----------|---------|----------|
| AI/LLM | 4,899 | gemini-cli (97K stars) |
| Other | 2,383 | — |
| Code/Dev Tools | 1,185 | — |
| API Integration | 867 | n8n (179K stars) |
| Database | 474 | — |
| Memory/Knowledge | 466 | modelcontextprotocol/servers (81K) |
| Security | 384 | — |
| Browser/Web | 324 | Scrapling (29K) |
| DevOps | 297 | — |
| Search | 235 | — |
| Data/Analytics | 208 | — |
| File System | 177 | — |
| Communication | 128 | — |

**Languages:** Python (3,749), TypeScript (3,431), JavaScript (1,047), Go (784), Rust (603), C# (514), Java (471), and 61 more.

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
python3 build_site.py    # Generates all HTML pages (one per server + category/index pages) into docs/
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
