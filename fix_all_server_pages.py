"""Refined converter script for remaining 24 edge-case server pages."""

import glob
import os
import re

SITE_DIR = "/Users/apple/Documents/LuciferForge/mcp-directory/docs"

def convert_html_content(content: str) -> str:
    # Split head and body to avoid touching JSON-LD or meta tags in head
    head = ""
    body = content
    if "</head>" in content:
        parts = content.split("</head>", 1)
        head = parts[0] + "</head>"
        body = parts[1]

    # Fix broken link tags like [label</a>](url) -> <a href="url"...>label</a>
    body = re.sub(r'\[([^\]<>]+)</a>\]\((https?://[^\)]+)\)', r'<a href="\2" target="_blank" rel="noopener" style="color:var(--accent)">\1</a>', body)
    
    # Standard markdown links [label](url) where label has no HTML tags
    body = re.sub(r'\[([^\]<>]+)\]\((https?://[^\)]+)\)', r'<a href="\2" target="_blank" rel="noopener" style="color:var(--accent)">\1</a>', body)

    # Standard markdown bold **text** in body only
    body = re.sub(r'\*\*([^\*\n<>]+)\*\*', r'<strong>\1</strong>', body)

    return head + body

def process_batch():
    files = glob.glob(os.path.join(SITE_DIR, "**", "*.html"), recursive=True)
    fixed_count = 0
    for fpath in files:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            old_c = f.read()

        new_c = convert_html_content(old_c)
        if old_c != new_c:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(new_c)
            fixed_count += 1

    print(f"Refined batch completed! Fixed {fixed_count} edge-case HTML pages.")

if __name__ == "__main__":
    process_batch()
