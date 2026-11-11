"""track_sales.py — Automated Gumroad Sales Tracker & Fulfillment Pipeline for Protodex.io

Usage:
    python track_sales.py          # Checks recent sales, records to sales_ledger.json, and auto-actions orders
    python track_sales.py --loop   # Runs continuously every 15 minutes
"""
import sys
import os
import re
import json
import time
import urllib.error
from datetime import datetime, timedelta, timezone
import urllib.request
import urllib.parse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as ef:
                for line in ef:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except Exception:
            pass


_load_dotenv()

GUMROAD_TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN", "")
PROTODEX_DIR = os.path.dirname(os.path.abspath(__file__))
LEDGER_FILE = os.path.join(PROTODEX_DIR, "sales_ledger.json")
SPONSORS_FILE = os.path.join(PROTODEX_DIR, "sponsored_servers.json")
DIRECTORY_FILE = os.path.join(PROTODEX_DIR, "mcp_directory.json")


def normalize_server_slug(raw_slug):
    """Normalize repo URL, owner/repo, or slug into canonical owner-repo slug."""
    s = (raw_slug or "").strip()
    repo_part = ""
    m = re.match(r"^(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", s, re.I)
    if m:
        repo_part = m.group(1)
    elif "/" in s and " " not in s:
        repo_part = s
    if repo_part:
        if repo_part.lower().endswith(".git"):
            repo_part = repo_part[:-4]
        s = repo_part.replace("/", "-")
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s).strip("-")
    return s, repo_part


def _lookup_server_meta(slug, repo_hint):
    """Resolve display metadata from mcp_directory.json if already indexed."""
    if not os.path.exists(DIRECTORY_FILE):
        return None
    try:
        with open(DIRECTORY_FILE, "r", encoding="utf-8") as df:
            servers = json.load(df).get("servers", [])
        for srv in servers:
            r = srv.get("repo", "")
            r_slug = re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", r.replace("/", "-").lower().strip())).strip("-")
            if r_slug == slug or (repo_hint and r.lower() == repo_hint.lower()):
                return srv
    except Exception:
        pass
    return None

def load_ledger():
    if os.path.exists(LEDGER_FILE):
        try:
            with open(LEDGER_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"processed_sales": []}
    return {"processed_sales": []}

def save_ledger(ledger):
    with open(LEDGER_FILE, 'w', encoding='utf-8') as f:
        json.dump(ledger, f, indent=2)

def check_and_process_sales(raise_on_error=False):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Polling Gumroad API for sales...")
    if not GUMROAD_TOKEN:
        msg = "GUMROAD_ACCESS_TOKEN is not set in environment or .env"
        print(f"Error checking sales: {msg}")
        if raise_on_error:
            raise RuntimeError(msg)
        return 0

    sales = []
    page_key = None
    try:
        while True:
            params = {"access_token": GUMROAD_TOKEN}
            if page_key:
                params["page_key"] = page_key
            url = "https://api.gumroad.com/v2/sales?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={"User-Agent": "ProtodexSalesTracker/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            if not data.get("success", True):
                raise RuntimeError(data.get("message", "Gumroad API returned success=false"))
            batch = data.get("sales", [])
            if not batch:
                break
            sales.extend(batch)
            page_key = data.get("next_page_key")
            if not page_key:
                break
    except Exception as e:
        print(f"Error checking sales: {e}")
        if raise_on_error:
            raise
        return 0

    ledger = load_ledger()
    processed_ids = set(ledger.get("processed_sales", []))
    new_sales = [s for s in sales if s.get("id") not in processed_ids]

    if not new_sales:
        print(f"No new sales. Total historical sales tracked: {len(processed_ids)}")
        return 0

    print(f"🎉 FOUND {len(new_sales)} NEW SALE(S)!")
    for sale in new_sales:
        sale_id = sale.get("id")
        prod_name = sale.get("product_name", "Unknown Product")
        price = sale.get("price", 0) / 100.0
        created_at = sale.get("created_at", "")
        custom_fields = sale.get("custom_fields", {})

        print(f"\n--- New Sale: {sale_id} ---")
        print(f"  Product: {prod_name} (${price:.2f})")
        print(f"  Time:    {created_at}")

        # Action: Check if it is a Promote Server sale
        if "Featured Server Placement" in prod_name or "sponsor_mcp" in str(sale.get("permalink", "")):
            raw_slug = custom_fields.get("Server Slug") or custom_fields.get("server_slug") or ""
            slug, repo_hint = normalize_server_slug(raw_slug)
            print(f"  ⚡ ACTION REQUIRED: Promote Server Sale! Slug normalized: '{slug}'")
            if slug:
                sponsors = []
                if os.path.exists(SPONSORS_FILE):
                    try:
                        with open(SPONSORS_FILE, 'r', encoding='utf-8') as sf:
                            sponsors = json.load(sf)
                    except Exception:
                        sponsors = []

                now_dt = datetime.now(timezone.utc)
                meta = _lookup_server_meta(slug, repo_hint)
                existing = None
                for item in sponsors:
                    item_slug, _ = normalize_server_slug(item.get("server_slug", ""))
                    if item_slug == slug:
                        existing = item
                        break

                if existing:
                    base_dt = now_dt
                    try:
                        cur_exp = existing.get("expires_at", "")
                        if cur_exp:
                            parsed_exp = datetime.fromisoformat(cur_exp.replace("Z", "+00:00"))
                            if parsed_exp > now_dt:
                                base_dt = parsed_exp
                    except Exception:
                        pass
                    exp_date = (base_dt + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
                    existing["server_slug"] = slug
                    existing["expires_at"] = exp_date
                    existing["sale_id"] = sale_id
                    if meta:
                        existing.setdefault("name", meta.get("name", slug))
                        existing.setdefault("repo", meta.get("repo", repo_hint))
                        existing.setdefault("category", meta.get("category", ""))
                        existing.setdefault("language", meta.get("language", ""))
                        existing["stars"] = max(existing.get("stars", 0), meta.get("stars", 0))
                        existing.setdefault("description", meta.get("description", ""))
                    print(f"  ✅ Extended '{slug}' in sponsored_servers.json (active until {exp_date})")
                else:
                    exp_date = (now_dt + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
                    new_entry = {
                        "server_slug": slug,
                        "name": meta.get("name", slug) if meta else slug,
                        "sponsor_label": "Featured Sponsor",
                        "expires_at": exp_date,
                        "sale_id": sale_id,
                    }
                    if meta:
                        new_entry["repo"] = meta.get("repo", "")
                        new_entry["category"] = meta.get("category", "")
                        new_entry["language"] = meta.get("language", "")
                        new_entry["stars"] = meta.get("stars", 0)
                        new_entry["description"] = meta.get("description", "")
                    elif repo_hint:
                        new_entry["repo"] = repo_hint
                    sponsors.append(new_entry)
                    print(f"  ✅ Added '{slug}' to sponsored_servers.json (active until {exp_date})")

                # Ensure no buyer PII is written to public sponsored_servers.json
                for entry in sponsors:
                    entry.pop("buyer_email", None)

                with open(SPONSORS_FILE, 'w', encoding='utf-8') as sf:
                    json.dump(sponsors, sf, indent=2)
                print("  👉 Run 'python build_site.py' and 'git push' to deploy live!")
            else:
                print("  ⚠️ Warning: Buyer did not enter a server slug. Check Gumroad receipt dashboard to follow up.")
        else:
            print("  📦 Digital Download Product: Delivered automatically via Gumroad receipt (No manual action needed).")

        processed_ids.add(sale_id)

    ledger["processed_sales"] = sorted(processed_ids)
    save_ledger(ledger)
    return len(new_sales)

if __name__ == '__main__':
    args = sys.argv[1:]
    build_if_changed = '--build-if-changed' in args

    if '--loop' in args:
        print("Starting continuous sales polling daemon (every 15 min)...")
        while True:
            new_count = check_and_process_sales(raise_on_error=False)
            if new_count and build_if_changed:
                import subprocess
                print("🚀 New sales processed! Rebuilding site...")
                subprocess.run([sys.executable, "build_site.py"], check=True)
            time.sleep(900)
    else:
        try:
            new_count = check_and_process_sales(raise_on_error=True)
        except Exception:
            sys.exit(1)
        if new_count and build_if_changed:
            import subprocess
            print("🚀 New sales processed! Rebuilding site...")
            subprocess.run([sys.executable, "build_site.py"], check=True)

