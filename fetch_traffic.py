import os
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta

def load_dotenv():
    candidates = [
        r"C:\Users\ManjunathG\Documents\Clawd\.env",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        r"C:\Users\ManjunathG\.gemini\antigravity\scratch\protodex-revamp\.env",
        r"C:\Users\ManjunathG\.env",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            except Exception:
                pass

load_dotenv()

API_KEY = os.environ.get("SIMPLE_ANALYTICS_API_KEY") or os.environ.get("SIMPLEANALYTICS_API_KEY")

if not API_KEY:
    print("ERROR: SIMPLE_ANALYTICS_API_KEY is not set.")
    sys.exit(1)

print("Key loaded successfully! Length:", len(API_KEY))
print("Querying Simple Analytics API for protodex.io...")

# Try query
url = "https://simpleanalytics.com/protodex.io.json?version=5&fields=histogram,pages,referrers,utm_sources,countries,pageviews,visitors"

req = urllib.request.Request(
    url,
    headers={
        "Api-Key": API_KEY,
        "User-Agent": "ProtodexTrafficReporter/1.0"
    }
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.load(resp)
        print("API Response received successfully!")
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode('utf-8', errors='ignore')}")
    # Also test with api_key in query or user_id
    sys.exit(1)
except Exception as e:
    print(f"Connection Error: {e}")
    sys.exit(1)

os.makedirs("scratch", exist_ok=True)
with open("scratch/traffic_report_raw.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("\n" + "=" * 60)
print(f"📊 PROTODEX.IO TRAFFIC TELEMETRY (Last 30 Days)")
print("=" * 60)
print(f"Total Pageviews: {data.get('pageviews')}")
print(f"Total Visitors:  {data.get('visitors')}")

print("\n🌍 TOP REFERRERS / TRAFFIC SOURCES:")
referrers = data.get("referrers", [])
if referrers:
    for r in referrers[:20]:
        val = r.get("value") or r.get("referrer") or "Direct / None"
        pv = r.get("pageviews", 0)
        vis = r.get("visitors", 0)
        print(f"  * {val:<35} | {pv:>6} views | {vis:>6} visitors")
else:
    print("  (No referrer data recorded)")

print("\n📄 TOP PAGES & VISITED REPOSITORIES:")
pages = data.get("pages", [])
if pages:
    for p in pages[:35]:
        val = p.get("value") or p.get("page") or "/"
        pv = p.get("pageviews", 0)
        vis = p.get("visitors", 0)
        print(f"  * {val:<45} | {pv:>6} views | {vis:>6} visitors")
else:
    print("  (No page data recorded)")

print("\n🌐 TOP COUNTRIES:")
countries = data.get("countries", [])
if countries:
    for c in countries[:15]:
        val = c.get("value") or c.get("country") or "Unknown"
        pv = c.get("pageviews", 0)
        vis = c.get("visitors", 0)
        print(f"  * {val:<30} | {pv:>6} views | {vis:>6} visitors")

print("\nSaved raw data to scratch/traffic_report_raw.json")
