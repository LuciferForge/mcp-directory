"""Unit tests for B2B sponsored server placement engine."""

import os
import sqlite3
import time
import pytest
from sponsor_intake import get_active_sponsored_servers, render_featured_badge_html

def test_get_active_sponsored_servers(tmp_path):
    db_file = tmp_path / "test_license_keys.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("""
        CREATE TABLE sponsored_servers (
            server_slug  TEXT PRIMARY KEY,
            expires_ts   INTEGER NOT NULL
        )
    """)
    now = int(time.time())
    conn.execute("INSERT INTO sponsored_servers VALUES ('active-server-slug', ?)", (now + 86400,))
    conn.execute("INSERT INTO sponsored_servers VALUES ('expired-server-slug', ?)", (now - 3600,))
    conn.commit()
    conn.close()

    active = get_active_sponsored_servers(db_path=str(db_file))
    assert "active-server-slug" in active
    assert "expired-server-slug" not in active

def test_render_featured_badge_html():
    badge = render_featured_badge_html()
    assert "Featured" in badge
    assert "background:linear-gradient" in badge
