#!/usr/bin/env python3
"""
Gumroad Complete Sales & Products Auditor:
Queries live Gumroad API using cursor pagination to inspect ALL published products, sales history, and conversion metrics.
"""

import requests
import json

GUMROAD_TOKEN = "mYyVRrUmgHcLLSfSeVvaVp0jaKEsVPnShjU33vD_nbg"

def audit_gumroad():
    print("=== GUMROAD LIVE SALES & PRODUCTS AUDIT ===")
    
    # 1. Fetch Sales
    r_sales = requests.get("https://api.gumroad.com/v2/sales", params={"access_token": GUMROAD_TOKEN})
    print(f"1. Sales API Status: {r_sales.status_code}")
    if r_sales.status_code == 200:
        sales = r_sales.json().get("sales", [])
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
    else:
        print(f"   ❌ Error fetching sales: {r_sales.text}")

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
