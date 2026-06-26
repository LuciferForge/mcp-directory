"""Featured-listings outreach engine.

Strategy:
  1. Pull top ~150 sweet-spot commercial MCP server candidates from mcp_directory.db
     (30-600 stars = scrappy enough to need visibility, established enough to pay)
  2. For each, hit GitHub API:
     - owner profile (email, blog, twitter, company)
     - repo metadata (recent activity, has-website, license)
  3. Score commercial-likelihood (has company affiliation, website, license, .com email)
  4. Generate personalized cold-pitch email body
  5. Save CSV: campaigns/featured_outreach_<date>.csv with name, email, repo, score, draft

No auto-sending. CSV is for manual review + paste into Gmail / Hunter / Apollo.

Why no automation: warm-up + deliverability matter. First 5 emails should be hand-sent
from manja316@gmail.com so SPF/DKIM/DMARC reputation builds correctly. Once we have 1
paid customer the case study writes itself for the next 50.
"""
import os
import sqlite3
import json
import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv('/Users/apple/Documents/Zero_fks/.env')

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
DB_PATH      = '/Users/apple/Documents/LuciferForge/mcp-directory/mcp_directory.db'
OUT_DIR      = Path('/Users/apple/Documents/LuciferForge/mcp-directory/campaigns')
OUT_DIR.mkdir(exist_ok=True)

# Try authenticated first; fall back to unauthenticated if 401
HEADERS = {
    'Accept':     'application/vnd.github+json',
    'User-Agent': 'protodex-outreach/1.0'
}
if GITHUB_TOKEN:
    # Validate token quickly — if 401, drop the header
    _test = requests.get('https://api.github.com/user',
                         headers={**HEADERS, 'Authorization': f'Bearer {GITHUB_TOKEN}'},
                         timeout=10)
    if _test.status_code == 200:
        HEADERS['Authorization'] = f'Bearer {GITHUB_TOKEN}'
        print(f'[GH auth] Token valid → 5000 req/hr')
    else:
        print(f'[GH auth] Token returned {_test.status_code} → using unauthenticated 60 req/hr')

# ────────────────────────────────────────────────────────────────────────────
# 1. Candidate selection from local DB
# ────────────────────────────────────────────────────────────────────────────

def pull_candidates(n=150):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT repo, stars, language, category, description, url, last_updated
        FROM servers
        WHERE stars BETWEEN 30 AND 600
          AND description IS NOT NULL
          AND LENGTH(description) > 25
          AND (
            LOWER(description) LIKE '%api%' OR
            LOWER(description) LIKE '%platform%' OR
            LOWER(description) LIKE '%service%' OR
            LOWER(description) LIKE '%database%' OR
            LOWER(description) LIKE '%analytics%' OR
            LOWER(description) LIKE '%trading%' OR
            LOWER(description) LIKE '%payment%' OR
            LOWER(description) LIKE '%saas%' OR
            LOWER(description) LIKE '%integration%' OR
            LOWER(description) LIKE '%enterprise%'
          )
          -- Exclude obvious non-prospects
          AND LOWER(repo) NOT LIKE 'anthropic/%'
          AND LOWER(repo) NOT LIKE 'modelcontextprotocol/%'
          AND LOWER(repo) NOT LIKE '%awesome-%'
        ORDER BY stars DESC
        LIMIT ?
    """, (n,)).fetchall()
    conn.close()
    return [
        dict(repo=r[0], stars=r[1], language=r[2], category=r[3],
             description=r[4], url=r[5], last_updated=r[6])
        for r in rows
    ]


# ────────────────────────────────────────────────────────────────────────────
# 2. GitHub enrichment (owner profile + repo metadata)
# ────────────────────────────────────────────────────────────────────────────

def gh_get(url, tries=2):
    for i in range(tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
            if r.status_code == 403:
                # Rate limited — back off
                time.sleep(15)
                continue
        except Exception:
            time.sleep(2)
    return None


def enrich(cand):
    repo = cand['repo']
    if '/' not in repo:
        return None
    owner, name = repo.split('/', 1)

    # Repo info
    repo_data = gh_get(f'https://api.github.com/repos/{owner}/{name}')
    if not repo_data:
        return None
    cand['homepage']    = (repo_data.get('homepage') or '').strip()
    cand['license']     = (repo_data.get('license') or {}).get('spdx_id') if repo_data.get('license') else None
    cand['has_website'] = bool(cand['homepage'] and cand['homepage'].startswith('http'))
    cand['archived']    = repo_data.get('archived', False)
    cand['pushed_at']   = repo_data.get('pushed_at', '')
    cand['owner_type']  = (repo_data.get('owner') or {}).get('type', 'User')   # User or Organization

    if cand['archived']:
        return None

    # Owner profile
    owner_data = gh_get(f'https://api.github.com/users/{owner}')
    if not owner_data:
        return None
    cand['owner_name']    = owner_data.get('name') or owner
    cand['owner_email']   = (owner_data.get('email') or '').strip()
    cand['owner_blog']    = (owner_data.get('blog') or '').strip()
    cand['owner_twitter'] = (owner_data.get('twitter_username') or '').strip()
    cand['owner_company'] = (owner_data.get('company') or '').strip()
    cand['owner_bio']     = (owner_data.get('bio') or '').strip()
    cand['owner_location']= (owner_data.get('location') or '').strip()
    cand['owner_followers']= owner_data.get('followers', 0)

    return cand


# ────────────────────────────────────────────────────────────────────────────
# 3. Commercial-likelihood score
# ────────────────────────────────────────────────────────────────────────────

def score(c):
    s = 0
    # Has a public email - HUGE for outreach
    if c.get('owner_email'):
        s += 30
    # Org account (vs personal) = likely company with budget
    if c.get('owner_type') == 'Organization':
        s += 20
    # Has website (commercial signal)
    if c.get('has_website'):
        s += 15
        # Bonus if homepage looks like a SaaS (not just docs)
        hp = c['homepage'].lower()
        if any(k in hp for k in ['.io', '.com', '.ai', '.app']) and 'github' not in hp:
            s += 10
    # Star range — 100-400 is the sweet spot
    stars = c.get('stars', 0)
    if 100 <= stars <= 400:
        s += 15
    elif 400 < stars <= 600:
        s += 10
    elif 50 <= stars < 100:
        s += 8
    # Recently active
    pushed = c.get('pushed_at', '')
    if pushed and pushed >= '2025-11':
        s += 10
    # Company affiliation
    if c.get('owner_company'):
        s += 8
    # Twitter handle (means they care about marketing)
    if c.get('owner_twitter'):
        s += 5
    return s


# ────────────────────────────────────────────────────────────────────────────
# 4. Personalized pitch generator
# ────────────────────────────────────────────────────────────────────────────

def draft_email(c):
    """Cold pitch tailored to each MCP server."""
    name_short = (c.get('owner_name') or c['repo'].split('/')[0]).split()[0]
    server_name = c['repo'].split('/')[-1]
    cat = c.get('category') or 'tools'
    stars = c.get('stars', 0)

    # Pull a key phrase from description for personalization
    desc = (c.get('description') or '')[:140]

    subject = f"Featured slot for {server_name} on protodex.io?"

    body = f"""Hi {name_short},

Quick note — I run protodex.io, the directory that indexes 10,500+ MCP servers across categories like {cat}. {server_name} is currently listed there based on our weekly GitHub crawl.

You've got {stars}★ — that's solid traction for an MCP server in this category. But organic ranking in our directory is heavily weighted toward star count + recency, which means newer servers from larger orgs can outrank yours even when {server_name} is the better tool for the job.

We just launched a Featured tier for cases exactly like this:
  • Promoted ($49/mo) — top slot in your category page, Verified badge, custom tagline
  • Featured ($99/mo) — homepage spotlight + 3 categories + inclusion in our monthly Protodex roundup

7-day money-back if it doesn't move the needle. Manual review (we don't take money to feature broken servers — keeps the directory high-signal).

Worth a look? Pricing + 60-second application: https://protodex.io/pricing.html

If not for {server_name}, no worries — you'll stay on the organic listing as always.

— Manjunath
protodex.io · manja316@gmail.com
"""

    return subject, body


# ────────────────────────────────────────────────────────────────────────────
# 5. Pipeline
# ────────────────────────────────────────────────────────────────────────────

def run(n_candidates=150, max_enriched=80):
    print(f"→ Pulling top {n_candidates} candidates from protodex DB…")
    cands = pull_candidates(n_candidates)
    print(f"   Got {len(cands)}.")

    print(f"\n→ Enriching via GitHub API (capped at {max_enriched})…")
    enriched = []
    for i, c in enumerate(cands[:max_enriched], 1):
        e = enrich(c)
        if e:
            e['score'] = score(e)
            enriched.append(e)
        if i % 10 == 0:
            print(f"   {i}/{max_enriched}  ({len(enriched)} enriched successfully)")
        time.sleep(0.3)  # be polite to GH

    print(f"\n→ Scoring + ranking…")
    enriched.sort(key=lambda c: -c['score'])

    contactable = [c for c in enriched if c.get('owner_email')]
    no_email    = [c for c in enriched if not c.get('owner_email')]
    print(f"   {len(contactable)} have public email (direct outreach)")
    print(f"   {len(no_email)} no public email (would need Twitter/site contact)")

    # ────────── Write CSV
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    out_csv = OUT_DIR / f'featured_outreach_{ts}.csv'
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow([
            'rank', 'score', 'owner_name', 'owner_email', 'owner_twitter',
            'owner_company', 'repo', 'stars', 'category', 'homepage',
            'pushed_at', 'subject', 'body'
        ])
        for i, c in enumerate(contactable + no_email, 1):
            subj, body = draft_email(c)
            w.writerow([
                i, c.get('score'), c.get('owner_name', ''), c.get('owner_email', ''),
                c.get('owner_twitter', ''), c.get('owner_company', ''),
                c['repo'], c['stars'], c.get('category', ''), c.get('homepage', ''),
                c.get('pushed_at', ''), subj, body
            ])
    print(f"\n→ Wrote {out_csv}")

    # ────────── Print top 10 for quick eyeballing
    print("\n══════ TOP 10 IMMEDIATELY CONTACTABLE PROSPECTS ══════\n")
    for i, c in enumerate(contactable[:10], 1):
        print(f"{i:>2}. score={c['score']:>3}  {c['repo']:<45} ({c['stars']}★)")
        print(f"    {c.get('owner_name')} <{c['owner_email']}>  | {c.get('owner_company','')[:30]}")
        if c.get('homepage'):
            print(f"    site: {c['homepage'][:80]}")
        print(f"    desc: {(c.get('description') or '')[:100]}")
        print()


if __name__ == '__main__':
    import sys
    # Default to small batch (safe for unauthenticated rate limit).
    # Override with: python featured_outreach.py 80
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    run(n_candidates=max(n*2, 50), max_enriched=n)
