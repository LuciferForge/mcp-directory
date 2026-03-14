# MCP Server Directory

The largest index of Model Context Protocol (MCP) servers on GitHub. 1,600+ servers scraped, categorized, and searchable.

## Quick Start

```bash
# Install deps
python3 -m pip install requests

# Scrape GitHub for MCP servers (takes ~2 min)
python3 mcp_directory.py scrape

# Browse
python3 mcp_directory.py stats           # Category breakdown
python3 mcp_directory.py top             # Top servers by stars
python3 mcp_directory.py search slack    # Search by keyword
python3 mcp_directory.py category Database  # List by category
python3 mcp_directory.py export          # Export as JSON
```

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
| Communication | 22 | — |
| File System | 15 | — |

**Languages:** Python (570), TypeScript (548), JavaScript (121), Go (103), Rust (51)

## Data

- `mcp_directory.json` — Full dataset (all servers with metadata)
- `mcp_by_category.json` — Grouped by category

## How It Works

The scraper searches GitHub using 11 different queries targeting MCP server repos:
- Repo names containing `mcp-server` or `mcp_server`
- Topics: `mcp-server`, `model-context-protocol`
- Code references to `FastMCP`, `@modelcontextprotocol/sdk`
- Description matches

Each repo is auto-categorized based on name, description, and topics into 13 categories.

## License

MIT

---

Built by [LuciferForge](https://github.com/LuciferForge)
