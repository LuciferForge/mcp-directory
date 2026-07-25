"""Fix unrendered markdown links and autolink raw URLs across all blog HTML files."""

import glob
import os
import re

BLOG_DIR = "/Users/apple/Documents/LuciferForge/mcp-directory/docs/blog"

def convert_text_links(content: str) -> str:
    # 1. Convert markdown links: [label](url) -> <a href="url" target="_blank" rel="noopener" style="color:var(--accent);font-weight:600">label</a>
    # Handle bold wrapped markdown links like <strong>[label](url)</strong> or [label](url)
    def repl_md_link(match):
        label = match.group(1)
        url = match.group(2)
        return f'<a href="{url}" target="_blank" rel="noopener" style="color:var(--accent);font-weight:600">{label}</a>'

    content = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', repl_md_link, content)

    # 2. Convert un-hyperlinked raw URLs like " — https://manja8.gumroad.com/l/agyjd" into working links
    def repl_raw_url(match):
        url = match.group(1)
        # Avoid double-wrapping if already part of an <a href="..."> tag
        return f'<a href="{url}" target="_blank" rel="noopener" style="color:var(--accent);font-weight:600">{url}</a>'

    # Match URLs starting with http:// or https:// that are preceded by space, dash, colon or text, not quotes or href=
    content = re.sub(r'(?<!href=")(?<!href=\')(?<!src=")(?<!src=\')(?<!">)(https?://manja8\.gumroad\.com/l/[a-zA-Z0-9_-]+)', repl_raw_url, content)

    return content

def fix_all_blog_pages():
    files = glob.glob(os.path.join(BLOG_DIR, "*.html"))
    fixed_count = 0
    total_replacements = 0

    for fpath in files:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            old_content = f.read()

        new_content = convert_text_links(old_content)

        if old_content != new_content:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(new_content)
            fixed_count += 1
            print(f"Fixed unrendered links in: {os.path.basename(fpath)}")

    print(f"\nSuccessfully converted unrendered links in {fixed_count} blog HTML files!")

if __name__ == "__main__":
    fix_all_blog_pages()
