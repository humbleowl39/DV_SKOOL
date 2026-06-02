#!/usr/bin/env python3
"""MkDocs(Material) markdown -> Astro Starlight markdown converter.

Transforms:
  1. Strip injected HTML blocks delimited by <!-- DV-SKOOL-*:start --> ... :end -->
  2. First H1 -> frontmatter `title:` (H1 removed from body; Starlight renders title)
  3. `!!! type "Title"` admonition  -> `:::aside[Title]` ... `:::`
  4. `??? answer "Title"` collapsible -> <details><summary>Title</summary>...</details>
  5. ```d2 fences kept as-is (astro-d2 handles them)
"""
import re
import sys
import pathlib

# MkDocs admonition type -> Starlight aside type (only note/tip/caution/danger exist)
ASIDE_MAP = {
    "note": "note", "info": "note", "abstract": "note", "objective": "tip",
    "tip": "tip", "hint": "tip", "success": "tip", "question": "tip", "example": "tip",
    "warning": "caution", "caution": "caution", "attention": "caution",
    "danger": "danger", "error": "danger", "failure": "danger", "bug": "danger",
}

# title = everything after the opening quote to EOL (handles embedded and
# unclosed quotes); a trailing closing quote is stripped in handling.
ADM_RE = re.compile(r'^(!!!|\?\?\?)\+?\s+([A-Za-z]+)(?:\s+"(.*))?\s*$')
H1_RE = re.compile(r'^#\s+(.*\S)\s*$')


def strip_dvskool_blocks(text: str) -> str:
    # remove <!-- DV-SKOOL-XXX:start --> ... <!-- DV-SKOOL-XXX:end --> (inclusive)
    text = re.sub(
        r'[ \t]*<!--\s*DV-SKOOL-[A-Z0-9\-]+:start\s*-->.*?<!--\s*DV-SKOOL-[A-Z0-9\-]+:end\s*-->[ \t]*\n?',
        '', text, flags=re.DOTALL)
    # remove MkDocs pymdownx.snippets include lines (e.g. --8<-- "abbreviations.md")
    text = re.sub(r'(?m)^[ \t]*--8<--.*\n?', '', text)
    # links to underscore-prefixed targets (e.g. _legacy_overview.md) point to
    # files Astro ignores -> drop the link, keep the text
    text = re.sub(r'\[([^\]]*)\]\((?:\.?/)?_[^)]*\)', r'\1', text)
    return text


def dedent(line: str) -> str:
    if line.startswith("    "):
        return line[4:]
    if line.startswith("\t"):
        return line[1:]
    return line


def collect_block(lines, start):
    """Collect indented (4-space/tab) content following an admonition header.
    Returns (content_lines_dedented, next_index)."""
    content = []
    i = start
    pending_blanks = 0
    while i < len(lines):
        ln = lines[i]
        if ln.strip() == "":
            pending_blanks += 1
            i += 1
            continue
        if ln.startswith("    ") or ln.startswith("\t"):
            content.extend([""] * pending_blanks)
            pending_blanks = 0
            content.append(dedent(ln))
            i += 1
            continue
        break  # non-indented, non-blank -> block ends
    return content, i


def transform(lines):
    """Process admonitions/collapsibles in a list of lines, recursively for
    nested blocks. Returns transformed list of lines."""
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        m = ADM_RE.match(line)
        if m:
            marker, atype, atitle = m.group(1), m.group(2).lower(), m.group(3)
            if atitle is not None:
                atitle = atitle.rstrip()
                if atitle.endswith('"'):
                    atitle = atitle[:-1]
                # `]` would terminate the Starlight aside title `:::type[...]`
                atitle = atitle.replace(']', ')')
            content, j = collect_block(lines, i + 1)
            while content and content[-1] == "":
                content.pop()
            content = transform(content)  # recurse into nested blocks
            if marker == "???":  # collapsible -> <details> (HTML)
                summary = atitle if atitle else atype.capitalize()
                out.append("<details>")
                out.append(f"<summary>{summary}</summary>")
                out.append("")
                out.extend(content)
                out.append("")
                out.append("</details>")
            else:  # !!! -> Starlight aside
                aside = ASIDE_MAP.get(atype, "note")
                out.append(f":::{aside}[{atitle}]" if atitle else f":::{aside}")
                out.extend(content)
                out.append(":::")
            i = j
            continue
        out.append(line)
        i += 1
    return out


def convert(text: str, fallback_title: str):
    text = strip_dvskool_blocks(text)
    lines = text.split("\n")
    # Extract first H1 as title (remove from body)
    title = None
    body_lines = []
    for idx, line in enumerate(lines):
        if title is None:
            m = H1_RE.match(line)
            if m:
                title = m.group(1).strip()
                # skip one trailing blank line after H1
                continue
        body_lines.append(line)
    # drop a leading blank left by removed H1
    while body_lines and body_lines[0].strip() == "":
        body_lines.pop(0)

    out = transform(body_lines)

    if title is None:
        title = fallback_title
    # Escape double quotes in title for YAML
    safe_title = title.replace('"', '\\"')
    body = "\n".join(out).strip("\n") + "\n"
    front = f'---\ntitle: "{safe_title}"\n---\n\n'
    return front + body


def main():
    src = pathlib.Path(sys.argv[1])
    dst = pathlib.Path(sys.argv[2])
    fallback = src.stem
    out = convert(src.read_text(encoding="utf-8"), fallback)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(out, encoding="utf-8")
    print(f"  {src.name} -> {dst}")


if __name__ == "__main__":
    main()
