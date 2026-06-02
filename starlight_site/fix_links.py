#!/usr/bin/env python3
"""Rewrite MkDocs-style relative .md links in generated Starlight content to
relative page URLs (base-safe). Operates in-place on src/content/docs."""
import re, os, pathlib

DOCS = pathlib.Path("src/content/docs").resolve()
LINK_RE = re.compile(r'\]\(([^)\s]*\.md(?:#[^)\s]*)?)\)')


def url_segs(rel):
    """rel: PurePosixPath with .md -> list of URL segments (index dropped)."""
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "index":
        parts = parts[:-1]
    return parts


def fix_file(f):
    src = f.resolve()
    src_rel = src.relative_to(DOCS)
    src_segs = url_segs(src_rel)
    src_dir = "/".join(src_segs) or "."

    def repl(m):
        target = m.group(1)
        path, anchor = (target.split("#", 1) + [""])[:2]
        anchor = ("#" + anchor) if "#" in target else ""
        if not path.endswith(".md"):
            return m.group(0)
        tgt_fs = (src.parent / path).resolve()
        try:
            tgt_rel = tgt_fs.relative_to(DOCS)
        except ValueError:
            return m.group(0)  # outside docs root -> leave
        tgt_segs = url_segs(tgt_rel)
        tgt_dir = "/".join(tgt_segs) or "."
        rel = os.path.relpath(tgt_dir, src_dir).replace(os.sep, "/")
        url = "./" if rel == "." else (rel + "/")
        if not url.startswith("."):
            url = "./" + url
        return f"]({url}{anchor})"

    txt = f.read_text(encoding="utf-8")
    new = LINK_RE.sub(repl, txt)
    if new != txt:
        f.write_text(new, encoding="utf-8")
        return len(LINK_RE.findall(txt))
    return 0


def main():
    files = list(DOCS.rglob("*.md")) + list(DOCS.rglob("*.mdx"))
    total_files = total_links = 0
    for f in files:
        n = fix_file(f)
        if n:
            total_files += 1
            total_links += n
    print(f"rewrote links in {total_files} files ({total_links} md-link occurrences)")


if __name__ == "__main__":
    main()
