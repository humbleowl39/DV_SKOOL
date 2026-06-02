#!/usr/bin/env python3
"""Remap stale cross-page heading anchors (both markdown ](rel#frag) and HTML
href="rel#frag") to actual Starlight heading IDs. Exact norm match, then fuzzy;
if no confident match, drop the anchor (land on page top)."""
import re, os, pathlib, difflib
from urllib.parse import unquote

DOCS = pathlib.Path("src/content/docs").resolve()
DIST = pathlib.Path("dist")

def norm(s):
    return re.sub(r'[^0-9a-z가-힣]+', '', unquote(s).lower())

page_ids = {}
for hp in DIST.rglob("*.html"):
    url = str(hp.relative_to(DIST)).replace("\\", "/").replace("index.html", "")
    ids = re.findall(r'<h[1-6][^>]*\sid="([^"]+)"', hp.read_text(encoding="utf-8", errors="ignore"))
    nm = {}
    for i in ids:
        nm.setdefault(norm(i), i)
    page_ids[url] = nm

def url_segs(rel):
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "index":
        parts = parts[:-1]
    return parts

# markdown link, or html href
MD = re.compile(r'\]\((\.{1,2}/[^)\s#]*/)#([^)\s]+)\)')
HREF = re.compile(r'href="(\.{1,2}/[^"#]*/)#([^"]+)"')

stats = {"exact": 0, "fuzzy": 0, "stripped": 0, "nopage": 0}

def remap(src_dir, relpath, anchor, md=True):
    tgt = os.path.normpath(os.path.join(src_dir, relpath)).replace(os.sep, "/")
    tgt = "" if tgt == "." else tgt + "/"
    ids = page_ids.get(tgt)
    if ids is None:
        stats["nopage"] += 1
        return None  # leave as-is
    if anchor in ids.values():
        return anchor
    key = norm(anchor)
    if key in ids:
        stats["exact"] += 1
        return ids[key]
    cand = difflib.get_close_matches(key, list(ids.keys()), n=1, cutoff=0.78)
    if cand:
        stats["fuzzy"] += 1
        return ids[cand[0]]
    stats["stripped"] += 1
    return ""  # drop anchor

for f in list(DOCS.rglob("*.md")) + list(DOCS.rglob("*.mdx")):
    src_dir = "/".join(url_segs(f.resolve().relative_to(DOCS)))
    t = f.read_text(encoding="utf-8")

    def md_repl(m):
        new = remap(src_dir, m.group(1), m.group(2), md=True)
        if new is None:
            return m.group(0)
        return f']({m.group(1)})' if new == "" else f']({m.group(1)}#{new})'

    def href_repl(m):
        new = remap(src_dir, m.group(1), m.group(2), md=False)
        if new is None:
            return m.group(0)
        return f'href="{m.group(1)}"' if new == "" else f'href="{m.group(1)}#{new}"'

    nt = MD.sub(md_repl, t)
    nt = HREF.sub(href_repl, nt)
    if nt != t:
        f.write_text(nt, encoding="utf-8")

print("anchor remap stats:", stats)
