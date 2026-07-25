"""B2B Sponsored Server Placement Engine for Protodex.io."""

import os
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Set

LICENSE_DB_PATH = str(Path(__file__).parent.parent / "products" / "polymarket-api" / "license_keys.db")

def get_active_sponsored_servers(db_path: str = LICENSE_DB_PATH) -> Set[str]:
    """Query license_keys.db for active sponsored server slugs (expires_ts > current timestamp)."""
    if not os.path.exists(db_path):
        return set()

    conn = sqlite3.connect(db_path)
    now = int(time.time())
    try:
        rows = conn.execute(
            "SELECT server_slug FROM sponsored_servers WHERE expires_ts > ?", (now,)
        ).fetchall()
        return {r[0].lower().strip() for r in rows if r[0]}
    except Exception as e:
        print(f"[sponsor_intake] DB query warning: {e}")
        return set()
    finally:
        conn.close()

def render_featured_badge_html() -> str:
    """Render styled Featured badge HTML for sponsored cards."""
    return '<span class="featured-badge" style="background:linear-gradient(135deg,#7B61FF,#2DD9E0);color:#000;font-size:0.7rem;font-weight:800;padding:2px 8px;border-radius:4px;text-transform:uppercase;margin-left:8px;display:inline-block">★ Featured</span>'

if __name__ == "__main__":
    active = get_active_sponsored_servers()
    print(f"[sponsor_intake] Active sponsored server count: {len(active)}")
    for slug in active:
        print(f"  - {slug}")
