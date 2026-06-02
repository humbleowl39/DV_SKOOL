#!/usr/bin/env python3
"""Pre-deploy QC for the Starlight site. Checks dist + source content."""
import re, pathlib, html, sys
from urllib.parse import urljoin, urldefrag

DIST = pathlib.Path("dist")
SRC = pathlib.Path("src/content/docs")
issues = {}
def add(cat, msg): issues.setdefault(cat, []).append(msg)

# ---------- 1. Internal link integrity (page-level) ----------
htmls = list(DIST.rglob("*.html"))
def url_to_path(u):
    """Map a site URL path to expected dist file(s)."""
    u = u.split("?")[0]
    if u.endswith("/"):
        return [DIST / (u.lstrip("/") + "index.html")]
    # could be /x  -> /x/index.html or /x.html
    return [DIST / (u.lstrip("/") + "/index.html"), DIST / (u.lstrip("/") + ".html"), DIST / u.lstrip("/")]

link_re = re.compile(r'(?:href|src)="([^"]+)"')
checked = brokenlinks = 0
for hp in htmls:
    page_url = "/" + str(hp.relative_to(DIST)).replace("\\", "/")
    page_url = page_url.replace("/index.html", "/")
    base_dir = page_url if page_url.endswith("/") else page_url.rsplit("/", 1)[0] + "/"
    txt = hp.read_text(encoding="utf-8", errors="ignore")
    for raw in link_re.findall(txt):
        u = html.unescape(raw)
        if u.startswith(("http://", "https://", "mailto:", "data:", "tel:", "//", "#", "javascript:")):
            continue
        u, _frag = urldefrag(u)
        if not u:
            continue
        # resolve relative against page
        if not u.startswith("/"):
            u = urljoin(base_dir, u)
        # only check internal app pages and local assets
        checked += 1
        cands = url_to_path(u)
        if not any(c.exists() for c in cands):
            brokenlinks += 1
            add("broken_links", f"{page_url}  ->  {raw}")

# ---------- 2. D2 diagram image integrity ----------
missing_d2 = 0
for hp in htmls:
    txt = hp.read_text(encoding="utf-8", errors="ignore")
    for src in re.findall(r'<img[^>]+src="(/d2/[^"]+)"', txt):
        f = DIST / src.lstrip("/")
        if not f.exists():
            missing_d2 += 1
            add("missing_d2", f"{hp.relative_to(DIST)} -> {src}")

# ---------- 3. Source lint: leftover MkDocs / pymdownx syntax ----------
md_files = list(SRC.rglob("*.md")) + list(SRC.rglob("*.mdx"))
patterns = {
    "admonition_!!!": re.compile(r'(?m)^[ \t]*(?:!!!|\?\?\?)[ +]'),
    "snippet_--8<--": re.compile(r'--8<--'),
    "dvskool_comment": re.compile(r'DV-SKOOL'),
    "leftover_widget_div": re.compile(r'class="(concept-dag|module-grid|course-grid|path-chain|topic-hero)'),
    "pymdownx_tab(=== \")": re.compile(r'(?m)^[ \t]*=== "'),
    "attr_list_{:": re.compile(r'\]\{:'),
    "toc_marker_[TOC]": re.compile(r'\[TOC\]'),
}
for f in md_files:
    t = f.read_text(encoding="utf-8", errors="ignore")
    rel = f.relative_to(SRC)
    for name, pat in patterns.items():
        n = len(pat.findall(t))
        if n:
            add("source_lint", f"{rel}: {name} x{n}")

# ---------- 4. Frontmatter title presence ----------
for f in md_files:
    t = f.read_text(encoding="utf-8", errors="ignore")
    m = re.match(r'^---\n(.*?)\n---', t, re.DOTALL)
    if not m or not re.search(r'(?m)^title:\s*\S', m.group(1)):
        add("no_title", str(f.relative_to(SRC)))

# ---------- 5. Code fence languages that fell back ----------
langs = {}
for f in md_files:
    for lg in re.findall(r'(?m)^```([a-zA-Z][\w+-]*)', f.read_text(encoding="utf-8", errors="ignore")):
        langs[lg] = langs.get(lg, 0) + 1

# ---------- Report ----------
print("="*60)
print(f"HTML pages: {len(htmls)} | internal links checked: {checked}")
print(f"BROKEN LINKS: {brokenlinks} | MISSING D2 IMG: {missing_d2}")
print("="*60)
for cat in ("broken_links", "missing_d2", "source_lint", "no_title"):
    items = issues.get(cat, [])
    print(f"\n### {cat}: {len(items)}")
    for x in items[:40]:
        print("  -", x)
    if len(items) > 40:
        print(f"  ... +{len(items)-40} more")
print("\n### code fence languages:", dict(sorted(langs.items(), key=lambda x:-x[1])))
print("\nTOTAL ISSUE CATEGORIES:", {k: len(v) for k, v in issues.items()})
