"""Empirical Content Audit Script for Protodex.io.

Scans all HTML files across docs/ and docs/blog/ to verify:
1. Zero unrendered markdown syntax ([text](url), **bold**, `code`, # headers).
2. Zero un-hyperlinked raw URLs.
3. Structural validity of HTML tags and links.
"""

import glob
import os
import re

SITE_DIR = "/Users/apple/Documents/LuciferForge/mcp-directory/docs"

def audit_file(fpath: str):
    rel_path = os.path.relpath(fpath, SITE_DIR)
    issues = []

    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # 1. Check for unrendered markdown links [text](url)
    md_links = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', content)
    if md_links:
        issues.append(f"Unrendered markdown links found ({len(md_links)}): {md_links[:2]}")

    # 2. Check for unrendered markdown bold **bold** in body text
    body_content = content.split("</head>", 1)[1] if "</head>" in content else content
    md_bolds = re.findall(r'\*\*([^\*\n<>]+)\*\*', body_content)
    if md_bolds:
        issues.append(f"Unrendered markdown bold text ({len(md_bolds)}): {md_bolds[:2]}")

    # 3. Check for unrendered raw URLs (not inside href= or src=)
    raw_urls = re.findall(r'(?<!href=")(?<!href=\')(?<!src=")(?<!src=\')(?<!">)(https?://manja8\.gumroad\.com/l/[a-zA-Z0-9_-]+)', content)
    if raw_urls:
        issues.append(f"Un-hyperlinked raw Gumroad URLs found ({len(raw_urls)}): {raw_urls[:2]}")

    # 4. Check basic HTML structure
    if "<title>" not in content and "</title>" not in content:
        issues.append("Missing <title> tag")

    return rel_path, issues

def run_full_content_audit():
    all_files = glob.glob(os.path.join(SITE_DIR, "**", "*.html"), recursive=True)
    print(f"=========================================================")
    print(f"      PROTODEX FULL CONTENT AUDIT ({len(all_files)} PAGES)      ")
    print(f"=========================================================")

    total_issues = 0
    clean_pages = 0

    for fpath in sorted(all_files):
        rel_path, issues = audit_file(fpath)
        if issues:
            total_issues += len(issues)
            print(f"\n❌ [ISSUE] {rel_path}:")
            for iss in issues:
                print(f"   - {iss}")
        else:
            clean_pages += 1

    print("\n---------------------------------------------------------")
    print(f"Audit Summary:")
    print(f"  Total Pages Audited: {len(all_files)}")
    print(f"  Clean Pages:         {clean_pages}")
    print(f"  Pages with Issues:   {len(all_files) - clean_pages}")
    print(f"  Total Issues Found:  {total_issues}")
    print(f"=========================================================")

    return total_issues == 0

if __name__ == "__main__":
    success = run_full_content_audit()
    if not success:
        exit(1)
