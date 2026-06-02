#!/usr/bin/env python3
"""Convert a topic's index.md (with MkDocs-era widget HTML) into a clean
Starlight index.mdx that lists chapters as a native <CardGrid> of <LinkCard>.

- Keeps intro prose (왜/학습목표/사전지식/참조자료 etc.)
- Strips widget div blocks (concept-dag, module-grid, course-grid, path-chain,
  course-header) and their now-orphaned headings (개념 맵 / 학습 모듈 / 모듈 흐름)
- Builds the module CardGrid from the actual chapter files (sorted), using each
  chapter's frontmatter title
- Adds a 코스 자료 CardGrid for glossary / quiz when present
"""
import re
import sys
import pathlib

WIDGET_CLASSES = ("concept-dag", "module-grid", "course-grid", "path-chain",
                  "course-header", "module-card", "topic-hero")
# headings that only introduced a widget / are replaced by our CardGrid
DROP_HEADINGS = ("개념 맵", "학습 모듈", "모듈 흐름", "학습 경로", "개념 의존성")


def split_frontmatter(text):
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', text, re.DOTALL)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        mm = re.match(r'^(\w+):\s*(.*)$', line)
        if mm:
            fm[mm.group(1)] = mm.group(2).strip().strip('"')
    return fm, m.group(2)


def remove_widget_blocks(body):
    lines = body.split("\n")
    out, i = [], 0
    opener = re.compile(r'^\s*<div\s+class="([^"]*)"')
    while i < len(lines):
        ln = lines[i]
        m = opener.match(ln)
        if m and any(c in m.group(1).split() or c in m.group(1) for c in WIDGET_CLASSES):
            depth = ln.count("<div") - ln.count("</div>")
            i += 1
            while i < len(lines) and depth > 0:
                depth += lines[i].count("<div") - lines[i].count("</div>")
                i += 1
            continue
        out.append(ln)
        i += 1
    return "\n".join(out)


def drop_orphan_headings(body):
    lines = body.split("\n")
    out = []
    for ln in lines:
        if re.match(r'^#{1,4}\s', ln) and any(h in ln for h in DROP_HEADINGS):
            continue
        out.append(ln)
    return "\n".join(out)


def collapse_blanks(body):
    body = re.sub(r'\n{3,}', '\n\n', body)
    return body.strip("\n")


def chapter_cards(topic_dir):
    files = sorted(p for p in topic_dir.glob("*.md")
                   if p.name not in ("index.md", "glossary.md")
                   and not p.name.startswith("_"))
    cards = []
    for p in files:
        fm, _ = split_frontmatter(p.read_text(encoding="utf-8"))
        title = fm.get("title", p.stem)
        slug = p.stem
        cards.append(f'\t<LinkCard title="{title}" href="./{slug}/" />')
    return cards


def resource_cards(topic_dir):
    cards = []
    if (topic_dir / "glossary.md").exists():
        cards.append('\t<LinkCard title="용어집 (Glossary)" href="./glossary/" description="핵심 용어 정의" />')
    if (topic_dir / "quiz" / "index.md").exists():
        cards.append('\t<LinkCard title="퀴즈 (Quizzes)" href="./quiz/" description="챕터별 이해도 점검" />')
    return cards


def main():
    topic_dir = pathlib.Path(sys.argv[1])
    idx = topic_dir / "index.md"
    fm, body = split_frontmatter(idx.read_text(encoding="utf-8"))

    body = remove_widget_blocks(body)
    body = drop_orphan_headings(body)
    body = collapse_blanks(body)

    # module CardGrid
    cards = chapter_cards(topic_dir)
    module_block = "## 학습 모듈\n\n<CardGrid>\n" + "\n".join(cards) + "\n</CardGrid>"
    res = resource_cards(topic_dir)
    if res:
        module_block += "\n\n## 코스 자료\n\n<CardGrid>\n" + "\n".join(res) + "\n</CardGrid>"

    # insert before the first references/related heading, else append
    ref_re = re.compile(r'(?m)^#{1,4}\s.*(참조|참고|관련 자료|관련자료|reference|Reference)')
    m = ref_re.search(body)
    if m:
        body = body[:m.start()] + module_block + "\n\n" + body[m.start():]
    else:
        body = body + "\n\n" + module_block

    title = fm.get("title", topic_dir.name)
    desc = fm.get("description", "")
    front = f'---\ntitle: "{title}"\n'
    if desc:
        front += f'description: "{desc}"\n'
    front += '---\n\n'
    front += "import { CardGrid, LinkCard } from '@astrojs/starlight/components';\n\n"

    out = front + body.strip("\n") + "\n"
    (topic_dir / "index.mdx").write_text(out, encoding="utf-8")
    idx.unlink()
    print(f"  {topic_dir.name}: {len(cards)} chapters, {len(res)} resources -> index.mdx")


if __name__ == "__main__":
    main()
