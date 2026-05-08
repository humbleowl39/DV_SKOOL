#!/usr/bin/env python3
"""Crawl Confluence page tree starting from a root page id."""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import base64

SITE = os.environ["ATLASSIAN_SITE"]
EMAIL = os.environ["ATLASSIAN_EMAIL"]
TOKEN = os.environ["ATLASSIAN_API_TOKEN"]

AUTH = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
BASE = f"https://{SITE}/wiki/rest/api"


def api_get(path):
    req = urllib.request.Request(f"{BASE}{path}", headers={"Authorization": f"Basic {AUTH}"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def list_children(page_id):
    out = []
    start = 0
    while True:
        d = api_get(f"/content/{page_id}/child/page?limit=200&start={start}")
        out.extend(d.get("results", []))
        if d.get("size", 0) < 200:
            break
        start += 200
    return out


def crawl(root_id):
    tree = {}
    queue = [(root_id, None)]
    while queue:
        pid, parent = queue.pop(0)
        try:
            kids = list_children(pid)
        except Exception as e:
            print(f"  ERR list children {pid}: {e}", file=sys.stderr)
            kids = []
        for k in kids:
            kid = k["id"]
            tree[kid] = {"id": kid, "title": k["title"], "parent": pid}
            queue.append((kid, pid))
        time.sleep(0.05)  # be polite
    return tree


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "7012616"
    # also include the root itself
    root_meta = api_get(f"/content/{root}")
    tree = {root: {"id": root, "title": root_meta["title"], "parent": None}}
    tree.update(crawl(root))
    out = sys.argv[2] if len(sys.argv) > 2 else "tree.json"
    with open(out, "w") as f:
        json.dump(tree, f, indent=2, ensure_ascii=False)
    print(f"crawled {len(tree)} pages -> {out}")
