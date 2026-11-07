"""track_sales.py — Automated Gumroad Sales Tracker & Fulfillment Pipeline for Protodex.io

Usage:
    python track_sales.py          # Checks recent sales, records to sales_ledger.json, and auto-actions orders
    python track_sales.py --loop   # Runs continuously every 15 minutes
"""
import sys
import os
import json
import time
from datetime import datetime, timedelta, timezone
import urllib.request
import urllib.parse

sys.stdout.reconfigure(encoding='utf-8')

GUMROAD_TOKEN = "mYyVRrUmgHcLLSfSeVvaVp0jaKEsVPnShjU33vD_nbg"
PROTODEX_DIR = os.path.dirname(os.path.abspath(__file__))
LEDGER_FILE = os.path.join(PROTODEX_DIR, "sales_ledger.json")
SPONSORS_FILE = os.path.join(PROTODEX_DIR, "sponsored_servers.json")

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

def check_and_process_sales():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Polling Gumroad API for sales...")
    url = f"https://api.gumroad.com/v2/sales?access_token={GUMROAD_TOKEN}"
    req = urllib.request.Request(url, headers={"User-Agent": "ProtodexSalesTracker/1.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            sales = data.get("sales", [])
    except Exception as e:
        print(f"Error checking sales: {e}")
        return

    ledger = load_ledger()
    processed_ids = set(ledger.get("processed_sales", []))
    new_sales = [s for s in sales if s.get("id") not in processed_ids]

    if not new_sales:
        print(f"No new sales. Total historical sales tracked: {len(processed_ids)}")
        return

    print(f"🎉 FOUND {len(new_sales)} NEW SALE(S)!")
    for sale in new_sales:
        sale_id = sale.get("id")
        prod_name = sale.get("product_name", "Unknown Product")
        price = sale.get("price", 0) / 100.0
        email = sale.get("email", "buyer")
        created_at = sale.get("created_at", "")
        custom_fields = sale.get("custom_fields", {})

        print(f"\n--- New Sale: {sale_id} ---")
        print(f"  Product: {prod_name} (${price:.2f})")
        print(f"  Buyer:   {email}")
        print(f"  Time:    {created_at}")

        # Action: Check if it is a Promote Server sale
        if "Featured Server Placement" in prod_name or "sponsor_mcp" in str(sale.get("permalink", "")):
            slug = custom_fields.get("Server Slug") or custom_fields.get("server_slug") or ""
            print(f"  ⚡ ACTION REQUIRED: Promote Server Sale! Slug requested: '{slug}'")
            if slug:
                # Add to sponsored_servers.json
                sponsors = []
                if os.path.exists(SPONSORS_FILE):
                    try:
                        with open(SPONSORS_FILE, 'r', encoding='utf-8') as sf:
                            sponsors = json.load(sf)
                    except Exception:
                        sponsors = []
                
                exp_date = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
                new_entry = {
                    "server_slug": slug.strip(),
                    "name": slug.strip(),
                    "sponsor_label": "Featured Sponsor",
                    "expires_at": exp_date,
                    "buyer_email": email,
                    "sale_id": sale_id
                }
                sponsors.append(new_entry)
                with open(SPONSORS_FILE, 'w', encoding='utf-8') as sf:
                    json.dump(sponsors, sf, indent=2)
                print(f"  ✅ Added '{slug}' to sponsored_servers.json (active until {exp_date})")
                print("  👉 Run 'python build_site.py' and 'git push' to deploy live!")
            else:
                print(f"  ⚠️ Warning: Buyer did not enter a server slug. Reach out to {email} to ask for their server repo URL.")
        else:
            print("  📦 Digital Download Product: Delivered automatically via Gumroad receipt (No manual action needed).")

        processed_ids.add(sale_id)

    ledger["processed_sales"] = list(processed_ids)
    save_ledger(ledger)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--loop':
        print("Starting continuous sales polling daemon (every 15 min)...")
        while True:
            check_and_process_sales()
            time.sleep(900)
    else:
        check_and_process_sales()
