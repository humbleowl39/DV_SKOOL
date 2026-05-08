#!/usr/bin/env python3
"""Fetch each page body, convert to markdown via pandoc, save to pages/<id>.md."""
import json
import os
import subprocess
import sys
import time
import urllib.request
import base64
import re

SITE = os.environ["ATLASSIAN_SITE"]
EMAIL = os.environ["ATLASSIAN_EMAIL"]
TOKEN = os.environ["ATLASSIAN_API_TOKEN"]
AUTH = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
BASE = f"https://{SITE}/wiki/rest/api"


def api_get(path):
    req = urllib.request.Request(f"{BASE}{path}", headers={"Authorization": f"Basic {AUTH}"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def html_to_md(html: str) -> str:
    # Strip Confluence-only macros that pandoc chokes on
    # ac:structured-macro, ac:rich-text-body, ri:user, etc.
    html = re.sub(r'<ac:[^>]*?/>', '', html)
    html = re.sub(r'<ac:[^>]*>', '<div>', html)
    html = re.sub(r'</ac:[^>]*>', '</div>', html)
    html = re.sub(r'<ri:[^>]*?/?>', '', html)
    html = re.sub(r'</ri:[^>]*>', '', html)
    # wrap in basic html
    full = f"<html><body>{html}</body></html>"
    p = subprocess.run(
        ["pandoc", "-f", "html", "-t", "gfm", "--wrap=none"],
        input=full, capture_output=True, text=True, timeout=30
    )
    if p.returncode != 0:
        return f"<!-- pandoc failed: {p.stderr[:200]} -->\n\n{html[:5000]}"
    md = p.stdout
    # collapse excessive blank lines
    md = re.sub(r'\n{3,}', '\n\n', md)
    return md.strip()


def main():
    tree = json.load(open("tree.json"))
    out_dir = "pages"
    os.makedirs(out_dir, exist_ok=True)

    skip_ids = set()
    for arg in sys.argv[1:]:
        if arg.startswith("--skip="):
            skip_ids.update(arg.split("=")[1].split(","))

    items = sorted(tree.values(), key=lambda x: int(x["id"]))
    total = len(items)
    for i, page in enumerate(items, 1):
        pid = page["id"]
        if pid in skip_ids:
            continue
        out_path = f"{out_dir}/{pid}.md"
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            continue
        try:
            d = api_get(f"/content/{pid}?expand=body.storage")
            html = d.get("body", {}).get("storage", {}).get("value", "") or ""
            md = html_to_md(html) if html else "<!-- empty body -->"
            with open(out_path, "w") as f:
                f.write(f"# {page['title']}\n\n")
                f.write(f"<!-- id={pid} parent={page['parent']} -->\n\n")
                f.write(md)
                f.write("\n")
            print(f"[{i}/{total}] {pid} {page['title'][:60]}", flush=True)
        except Exception as e:
            print(f"[{i}/{total}] ERR {pid}: {e}", file=sys.stderr, flush=True)
        time.sleep(0.05)


if __name__ == "__main__":
    main()
