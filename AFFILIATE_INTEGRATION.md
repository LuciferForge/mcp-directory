# Affiliate Integration — protodex.io

**Status:** Code written and ready. Pending your signups to actually earn commission.

**Files added:**
- `affiliate_recommendations.py` — pluggable module
- `affiliate_links.json` — config (placeholder URLs, swap in your real referral links)

---

## How it works

### Per-server affiliate sidebar
On every MCP server detail page (e.g., `protodex.io/servers/<slug>.html`), an "Recommended infrastructure for this MCP server" sidebar shows up to 3 contextually-relevant affiliate links based on the server's category.

For example:
- A **MongoDB-themed** MCP server → shows MongoDB Atlas + DigitalOcean (deploy) + Hostinger
- A **Slack-adjacent** MCP server → shows Notion + JetBrains
- A **payment** MCP server → shows Razorpay + Polar.sh

### Standalone /recommended page
A clean curated page with all 10 affiliate programs, ranked by category match. Linkable from header nav.

---

## To activate (your one-time signups)

Sign up to each affiliate program in this order (highest EV first):

1. **MongoDB Atlas Cloud Bonus Program** — $200 per qualifying signup
   https://www.mongodb.com/community/champions/program/cloud-bonus
2. **DigitalOcean** — $25 + $200 user credit
   https://www.digitalocean.com/referral-program
3. **Notion** — $30 first sale + recurring
   https://www.notion.com/affiliates (or via Impact)
4. **Hostinger** — 60% first month
   https://www.hostinger.com/affiliates
5. **Linode (Akamai)** — $25 + $100 credit
   https://www.linode.com/lp/refer-a-friend/
6. **JetBrains** — 15% first year
   https://www.jetbrains.com/store/affiliates/
7. **Webflow** — $200 per Site signup
   https://webflow.com/affiliates
8. **Razorpay** — ₹500 per merchant (India)
   https://razorpay.com/affiliate-program/
9. **Polar.sh** — referral credit
   https://polar.sh/dashboard
10. **Cloudflare Partners** (slower approval)
    https://www.cloudflare.com/partners/

Each program gives you a unique referral URL like `https://www.mongodb.com/cloud/atlas/register?affiliate=YOURCODE`.

Drop each URL into the corresponding entry in `affiliate_links.json`. Example:

```json
{
  "mongodb": {
    "url": "https://www.mongodb.com/cloud/atlas/register?affiliate=AB12345"
  },
  ...
}
```

---

## To wire into the existing site

Edit `mcp-directory/build_site.py`:

**Step 1 — add import at top of file (~line 10):**
```python
from affiliate_recommendations import affiliate_sidebar_html, affiliate_recommendations_css, recommended_page_html
```

**Step 2 — add CSS to global stylesheet** (search for the `<style>` block near `:root` definitions, ~line 540, append):
```python
+ affiliate_recommendations_css()
```

Or simpler: paste the contents of `affiliate_recommendations_css()` directly into the existing stylesheet section.

**Step 3 — inject sidebar into per-server pages** (in `build_server_page` function, ~line 1907):

Before the `related_html` injection, add:
```python
    affiliate_html = affiliate_sidebar_html(server)
```

And in the f-string template right before `{related_html}`:
```html
    {affiliate_html}
    {related_html}
```

**Step 4 — add /recommended page** (in `main()` function near the other build_* calls):
```python
    write("docs/recommended.html",
          html_head("Recommended for MCP builders", "Curated infra + tooling for MCP server builders.", "/recommended.html") +
          html_header() +
          recommended_page_html() +
          html_footer())
```

**Step 5 — add nav link** in `html_header()` to surface /recommended:
```html
<a href="/recommended.html">Recommended</a>
```

**Step 6 — rebuild the site:**
```bash
cd /Users/apple/Documents/LuciferForge/mcp-directory
python3 build_site.py
git add docs/ affiliate_recommendations.py affiliate_links.json
git commit -m "Add affiliate recommendations sidebar + /recommended page"
git push origin master
```

GitHub Pages will rebuild automatically.

---

## What I'll do once you sign up

Once you drop me the affiliate URLs:

1. **Update `affiliate_links.json`** with real URLs (1 min)
2. **Wire into `build_site.py`** and rebuild (15 min)
3. **Push + verify deploy** (5 min)
4. **Track clicks via Google Analytics / SimpleAnalytics** (already on protodex.io)
5. **Daily Telegram alert when commission is earned** (write a small puller script per program where APIs exist)

---

## Realistic conversion model

protodex.io's MCP server detail pages are the highest-traffic pages on the site (people land via Google searches like "best MongoDB MCP server"). Conversion math:

- Assume 500 server-page visits/day across 5,800 server pages
- 1% of visitors notice the affiliate sidebar (5 clicks/day)
- 1% of clicks convert to a paid signup somewhere (1.5 conversions/month)
- Mix of payouts: avg $50-80 commission per conversion

**Realistic month-1 commission: $75-$240**
**Month 3 (after content + traffic ramp): $200-$700/mo**

Compounds with traffic. Once integrated, the work I did this week earns money in month 6 too.

---

## What this does NOT do (intentionally)

- **No cookies/tracking pixels of our own.** Affiliate programs handle their own attribution. We just send the click.
- **No "sponsored content" without disclosure.** Every affiliate link is marked `rel="nofollow sponsored"` per FTC + Google guidelines.
- **No interference with the actual MCP server discovery.** Sidebars are below the fold, soft-styled, never disrupt the user finding the server they came for.

If a user complains the recommendations feel intrusive, we can tone them down (smaller, more contextual, fewer per page).
