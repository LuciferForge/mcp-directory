#!/usr/bin/env python3
"""
Gumroad Complete Sales & Products Auditor:
Queries live Gumroad API using cursor pagination to inspect ALL published products, sales history, and conversion metrics.
"""

import os
import sys
import requests
import json


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

def audit_gumroad():
    print("=== GUMROAD LIVE SALES & PRODUCTS AUDIT ===")
    if not GUMROAD_TOKEN:
        print("   ❌ Error: GUMROAD_ACCESS_TOKEN is not set in environment or .env")
        sys.exit(1)

    # 1. Fetch ALL Sales via page_key cursor
    sales = []
    sales_status = None
    next_sales_key = None
    while True:
        params = {"access_token": GUMROAD_TOKEN}
        if next_sales_key:
            params["page_key"] = next_sales_key
        r_sales = requests.get("https://api.gumroad.com/v2/sales", params=params, timeout=15)
        sales_status = r_sales.status_code
        if sales_status != 200:
            print(f"1. Sales API Status: {sales_status}")
            print(f"   ❌ Error fetching sales: {r_sales.text}")
            break
        data = r_sales.json()
        batch = data.get("sales", [])
        if not batch:
            break
        sales.extend(batch)
        next_sales_key = data.get("next_page_key")
        if not next_sales_key:
            break

    if sales_status == 200:
        print(f"1. Sales API Status: {sales_status}")
        total_rev = sum(float(s.get("price", 0))/100.0 for s in sales)
        print(f"   • Total Verified Sales Count: {len(sales)}")
        print(f"   • Total Cumulative Revenue: ${total_rev:.2f} USD")
        print("\n   --- RECENT COMPLETED SALES LEDGER ---")
        for idx, s in enumerate(sales, 1):
            pname = s.get("product_name")
            price = float(s.get("price", 0)) / 100.0
            cur = s.get("currency", "usd").upper()
            dt = s.get("created_at")
            email = s.get("email")
            print(f"   • Sale #{idx}: '{pname}' | Price: ${price:.2f} {cur} | Date: {dt} | Buyer: {email}")
        if not sales:
            print("   • No completed sales found in sales ledger.")

    # 2. Fetch ALL Products via page_key cursor
    print("\n2. Published Gumroad Products List (Full Inventory):")
    total_found = 0
    next_page_key = None
    
    while True:
        params = {"access_token": GUMROAD_TOKEN}
        if next_page_key:
            params["page_key"] = next_page_key
            
        r_prods = requests.get("https://api.gumroad.com/v2/products", params=params)
        if r_prods.status_code == 200:
            data = r_prods.json()
            prods = data.get("products", [])
            if not prods:
                break
            for p in prods:
                total_found += 1
                pname = p.get("name")
                price = float(p.get("price", 0)) / 100.0
                sales_cnt = p.get("sales_count", 0)
                rev_usd = float(p.get("sales_usd_cents", 0)) / 100.0
                url = p.get("short_url")
                print(f"   • Product #{total_found}: '{pname}' | Price: ${price:.2f} | Sales: {sales_cnt} | Revenue: ${rev_usd:.2f} | URL: {url}")
            
            next_page_key = data.get("next_page_key")
            if not next_page_key:
                break
        else:
            print(f"   ❌ Error fetching products: {r_prods.text}")
            break

if __name__ == "__main__":
    audit_gumroad()
