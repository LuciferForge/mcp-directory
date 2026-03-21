#!/usr/bin/env python3
"""
Merge scraped MCP server data into the existing mcp_directory.json.
- Deduplicates by normalized repo identifier
- Enriches existing entries with security_score and security_band
- Adds new entries in the current format
"""

import json
import os
from datetime import datetime, timezone

DIR = os.path.dirname(os.path.abspath(__file__))
CURRENT_FILE = os.path.join(DIR, "mcp_directory.json")
SCRAPED_FILE = os.path.join(DIR, "scraper", "all_servers_scored.json")
OUTPUT_FILE = os.path.join(DIR, "mcp_directory.json")


def normalize_repo(repo_str):
    """Strip https://github.com/ and trailing slashes/.git to get owner/name."""
    r = repo_str.strip()
    for prefix in ["https://github.com/", "http://github.com/", "github.com/"]:
        if r.lower().startswith(prefix):
            r = r[len(prefix):]
    r = r.rstrip("/")
    if r.endswith(".git"):
        r = r[:-4]
    return r.lower()


def main():
    # Load current
    with open(CURRENT_FILE) as f:
        current_data = json.load(f)
    current_servers = current_data["servers"]
    print(f"Current: {len(current_servers)} servers")

    # Load scraped
    with open(SCRAPED_FILE) as f:
        scraped_data = json.load(f)
    scraped_servers = scraped_data["servers"]
    print(f"Scraped: {len(scraped_servers)} servers")

    # Index current by normalized repo
    current_by_repo = {}
    max_id = 0
    for s in current_servers:
        repo_norm = normalize_repo(s.get("repo", ""))
        current_by_repo[repo_norm] = s
        if s.get("id", 0) > max_id:
            max_id = s["id"]

    # Index scraped by normalized repo
    scraped_by_repo = {}
    for s in scraped_servers:
        repo_norm = normalize_repo(s.get("repo_url", ""))
        if repo_norm:
            scraped_by_repo[repo_norm] = s

    enriched = 0
    new_count = 0
    next_id = max_id + 1

    # Enrich existing entries
    for repo_norm, current_s in current_by_repo.items():
        if repo_norm in scraped_by_repo:
            scraped_s = scraped_by_repo[repo_norm]
            # Add security data
            if "security_score" in scraped_s:
                current_s["security_score"] = scraped_s["security_score"]
            if "security_band" in scraped_s:
                current_s["security_band"] = scraped_s["security_band"]
            # Use higher star count
            if scraped_s.get("stars", 0) > current_s.get("stars", 0):
                current_s["stars"] = scraped_s["stars"]
            enriched += 1

    # Add new entries
    new_servers = []
    for repo_norm, scraped_s in scraped_by_repo.items():
        if repo_norm in current_by_repo:
            continue  # Already exists

        # Skip archived repos
        if scraped_s.get("archived", False):
            continue

        repo_id = normalize_repo(scraped_s.get("repo_url", ""))
        # Reconstruct owner/name with original casing
        repo_url = scraped_s.get("repo_url", "")
        repo_path = repo_url
        for prefix in ["https://github.com/", "http://github.com/"]:
            if repo_path.startswith(prefix):
                repo_path = repo_path[len(prefix):]
        repo_path = repo_path.rstrip("/")
        if repo_path.endswith(".git"):
            repo_path = repo_path[:-4]

        # Convert topics from array to comma-separated string
        topics_raw = scraped_s.get("topics", [])
        if isinstance(topics_raw, list):
            topics_str = ",".join(topics_raw)
        else:
            topics_str = str(topics_raw) if topics_raw else ""

        new_entry = {
            "id": next_id,
            "repo": repo_path,
            "name": scraped_s.get("name", repo_path.split("/")[-1] if "/" in repo_path else repo_path),
            "description": scraped_s.get("description", ""),
            "stars": scraped_s.get("stars", 0),
            "language": scraped_s.get("language", ""),
            "topics": topics_str,
            "tools": "",
            "category": scraped_s.get("category", "Other"),
            "last_updated": scraped_s.get("last_pushed", ""),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "readme_excerpt": "",
            "url": repo_url,
        }

        # Add security data
        if "security_score" in scraped_s:
            new_entry["security_score"] = scraped_s["security_score"]
        if "security_band" in scraped_s:
            new_entry["security_band"] = scraped_s["security_band"]

        new_servers.append(new_entry)
        next_id += 1
        new_count += 1

    # Merge: current + new
    all_servers = current_servers + new_servers

    # Sort by stars descending
    all_servers.sort(key=lambda s: s.get("stars", 0), reverse=True)

    total = len(all_servers)
    print(f"\nResults:")
    print(f"  Existing (enriched with security): {enriched}")
    print(f"  New servers added: {new_count}")
    print(f"  Total: {total}")

    # Count security bands
    bands = {"green": 0, "yellow": 0, "red": 0, "none": 0}
    for s in all_servers:
        band = s.get("security_band", "")
        if band in bands:
            bands[band] += 1
        else:
            bands["none"] += 1
    print(f"\nSecurity bands:")
    print(f"  Green (secure): {bands['green']}")
    print(f"  Yellow (review): {bands['yellow']}")
    print(f"  Red (risk): {bands['red']}")
    print(f"  No score: {bands['none']}")

    # Write output
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_servers": total,
        "servers": all_servers,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nWritten to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
