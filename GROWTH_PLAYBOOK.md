# Protodex.io Growth Playbook

## Outreach Emails (copy-paste ready)

### Email 1: Dev.to "Favorite MCP Directories" author
**Subject:** Protodex — MCP directory with per-server security scores

Hi [Author],

Saw your post on favorite MCP directories — great roundup. Thought you might want to check out Protodex (protodex.io).

What makes it different: we run security scans on every listed server and show a Green/Yellow/Red safety rating. We've already submitted 10 vulnerability reports to Huntr and MSRC based on what we found scanning MCP servers — including CVEs in FAISS, TorchServe, and Microsoft's own MCP implementations.

Currently indexing 5,000+ servers across 13 categories with search, language filtering, and "What are you building?" recommendations.

Happy to answer any questions. No pressure — just thought it might be worth a mention if you update the post.

Best,
Lucifer
protodex.io | @gmanjuu

---

### Email 2: Descope "Best MCP Directories" author
**Subject:** Missing from your MCP directories list: security-scored directory

Hi [Author],

Read your "Best MCP Server Directories for Developers" piece. One angle your list doesn't cover: security.

Protodex (protodex.io) is an MCP directory that scores every server on security — has it been maintained? Does it have known CVEs? Is the license clear? We show Green/Yellow/Red badges so devs can avoid risky servers.

We've found real vulnerabilities in MCP servers (submitted to Microsoft MSRC and Huntr) and think the community needs better visibility into which servers are safe to deploy.

Would love to be considered for your next update.

Best,
Lucifer
protodex.io

---

### Email 3: Nordic APIs "7 MCP Registries" author
**Subject:** 8th MCP registry worth checking out

Hi [Author],

Your "7 MCP Registries Worth Checking Out" article is a great resource. Here's #8:

Protodex (protodex.io) — 5,000+ MCP servers with per-server security scoring. We're the only directory that scans for known vulnerabilities and flags risky servers. Built by the team that reported CVEs in FAISS, Microsoft Azure MCP, and TorchServe.

Features: search, 13 categories, language filtering, "What are you building?" recommendations, and security badges.

Happy to provide more details if useful.

Best,
Lucifer
protodex.io

---

## X Thread (post after server count hits 5K)

Thread:

1/ We scanned 5,000+ MCP servers for security vulnerabilities.

Here's what we found (thread):

2/ 36% of MCP servers have NO license file. You're deploying code with unclear legal status into your AI agents.

3/ 12% haven't been updated in 6+ months. Stale dependencies = unpatched vulnerabilities.

4/ We found real CVEs in servers people actually use:
- FAISS: arbitrary file read/write via crafted index files
- TorchServe: SnakeYAML RCE
- Microsoft Azure MCP: SQL injection

All reported and in review.

5/ So we built protodex.io — the MCP directory that actually checks if servers are safe.

Every server gets a Green/Yellow/Red security score based on:
- Known CVEs
- Maintenance status
- License clarity
- Code quality signals

6/ Not just a list. We help you pick:

"What are you building?"
- RAG app → here's your stack
- Agent with tools → these servers are verified
- Database integration → these are safe

7/ Check it out: protodex.io

Search 5,000+ servers, filtered by security, language, and category.

The MCP ecosystem is exploding. Don't deploy servers you haven't checked.

---

## Dev.to Article Draft

**Title:** "We Scanned 5,000 MCP Servers for Security Vulnerabilities — Here's What We Found"

[To be written after scraper completes with real numbers]

Key sections:
1. The MCP ecosystem is growing faster than anyone is checking
2. Our methodology (automated scanning + manual triage)
3. Top findings (anonymized for unreported vulns, named for CVEs)
4. The security score system
5. What developers should check before deploying an MCP server
6. Link to protodex.io

---

## Reddit Comments (r/mcp, r/ClaudeAI, r/ChatGPT)

Reply template for "which MCP servers should I use" threads:

"If you want to filter by safety, protodex.io adds security scoring to every server — Green/Yellow/Red ratings based on known CVEs, maintenance status, and code quality. Helps avoid deploying something that hasn't been updated in a year."

Short, helpful, not spammy. Link to protodex, not a pitch.

---

## SEO Landing Pages Needed

1. `/security` — "MCP Server Security Scores — How We Rate Servers"
2. `/for/rag` — "Best MCP Servers for RAG Applications"
3. `/for/agents` — "Best MCP Servers for AI Agents"
4. `/for/databases` — "Best MCP Servers for Database Integration"
5. `/audit` — "Get Your MCP Server Audited" (service page, $200-500)

Each page: 800-1200 words, targeting specific keywords, linking to relevant server listings.
