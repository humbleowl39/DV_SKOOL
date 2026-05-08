#!/usr/bin/env python3
"""Glossary audit for DV_SKOOL topics.

Per topic:
  - Parse glossary.md `### <Term>` headings -> known terms (acronym + full name).
  - Scan chapter files (01_*.md ... NN_*.md) for acronym candidates.
  - Compute set differences:
      MISSING        : appears in body, not in glossary
      LINK_ABSENT    : in body AND glossary, but body has no link to glossary
      ORPHAN         : in glossary, never appears in body chapters
  - Emit per_topic/<id>.md and feed SUMMARY aggregator.
"""
from __future__ import annotations

import re
import sys
import json
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path("/home/jaehyeok.lee/PRATICE/DV_SKOOL/topics")
OUT = Path("/home/jaehyeok.lee/PRATICE/DV_SKOOL/20260508_135724_dvskool_GLOSSARY_AUDIT")

# Generic English / markdown / shell stopwords (case-sensitive UPPER).
STOPWORDS = {
    "I", "A", "AN", "THE", "TO", "OF", "IN", "ON", "AT", "BY", "IS", "AS",
    "OR", "AND", "NOT", "IF", "BUT", "FOR", "WITH", "FROM", "INTO", "ALL", "ANY",
    "OK", "YES", "NO", "ON", "OFF", "UP", "DOWN", "OUT", "NEW", "OLD",
    "ETC", "VS", "VIA", "TBD", "TODO", "FIXME", "NOTE", "WARN", "INFO", "DEBUG",
    "API", "URL",  # too generic; let topics opt-in if needed
    "MD", "PDF", "HTML", "CSS", "PNG", "JPG", "SVG", "TXT", "CSV", "TSV",
    "GIT", "GH", "PR", "MR", "CI", "CD",
    "ASCII", "UTF", "USB",  # rarely topic-specific
    "ENGLISH", "KOREAN",
    "TBA", "FAQ",
    # Markdown / RST headings sometimes use single letters
    "X", "Y", "Z",
    # Misc (often appear standalone in tables / numerics)
    "N", "M", "K",
    # Site-wide meta markers used in DV_SKOOL chapter snippets
    "SKOOL", "CH", "CTX", "TOC", "START", "END",
    # Common English words that happen to be all-caps in text (READ/WRITE belong here for non-RDMA topics)
    "FILE", "DIR", "PATH", "ENV", "USER", "OS",
    # Cross-references / labels frequently appearing standalone
    "REF", "FIG", "TBL", "EQ", "SEC",
}

# Acronym pattern: starts with uppercase letter, length 2-10, may have digits and underscore.
ACRONYM_RE = re.compile(r"\b([A-Z][A-Z0-9_]{1,9})\b")
# Parenthetical acronym e.g. "(BTH)" or "(BTH/RC)"
PAREN_ACR_RE = re.compile(r"\(([A-Z][A-Z0-9/_-]{1,19})\)")

# Glossary heading: ### Term  (capture full string, then derive primary acronym)
GLOSS_HEAD_RE = re.compile(r"^###\s+(.+?)\s*$")
# Inside a glossary heading, common pattern: "BTH (Base Transport Header)"
HEAD_ACR_RE = re.compile(r"^([A-Z][A-Z0-9_/]{0,19})\s*(?:\(|$)")

# Code fence detection (line-level state machine).
FENCE_RE = re.compile(r"^\s*```")

# Inline-link to glossary heuristic: any link whose target matches glossary.md
LINK_RE = re.compile(r"\]\(([^)]+)\)")


def strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks, HTML comments, and inline code."""
    # remove HTML comments first (multiline, often span lines for snippets)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    out = []
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # strip inline code spans
        line = re.sub(r"`[^`]*`", "", line)
        # strip image/link target URLs (their anchors mustn't pollute extraction)
        line = re.sub(r"\]\([^)]*\)", "]", line)
        out.append(line)
    return "\n".join(out)


def parse_glossary(path: Path) -> dict:
    """Return {primary_term: {'heading': str, 'aliases': set}}."""
    if not path.exists():
        return {}
    terms = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = GLOSS_HEAD_RE.match(raw)
        if not m:
            continue
        heading = m.group(1).strip()
        # primary token (acronym or first word)
        tok = HEAD_ACR_RE.match(heading)
        if tok:
            primary = tok.group(1)
        else:
            primary = heading.split()[0]
        aliases = set()
        # also collect everything inside parens as alias acronyms
        for pm in PAREN_ACR_RE.findall(heading):
            for sub in re.split(r"[/_-]", pm):
                if sub.isupper() and len(sub) >= 2:
                    aliases.add(sub)
        # primary itself
        aliases.add(primary)
        # if primary is camel/PascalCase term, also record uppercase form? skip — body match uses exact case for non-acronym terms
        terms[primary] = {"heading": heading, "aliases": aliases}
    return terms


def extract_body_acronyms(chapter_files: list[Path]) -> dict:
    """Return {acronym: [(file_stem, line_no, line_text)]}."""
    found = defaultdict(list)
    for f in chapter_files:
        text = f.read_text(encoding="utf-8")
        clean = strip_code_blocks(text)
        for ln_no, line in enumerate(clean.splitlines(), 1):
            # also check body even outside code fence; tables included.
            for acr in set(ACRONYM_RE.findall(line)) | set(PAREN_ACR_RE.findall(line)):
                # PAREN can contain "/", split
                for token in re.split(r"[/_-]", acr):
                    if not token or not token[0].isalpha():
                        continue
                    if token in STOPWORDS:
                        continue
                    if not re.fullmatch(r"[A-Z][A-Z0-9]{1,9}", token):
                        continue
                    found[token].append((f.stem, ln_no, line.strip()[:120]))
    return found


def find_glossary_links(chapter_files: list[Path]) -> set:
    """Return set of acronyms that appear in body AS markdown links pointing at glossary.md."""
    linked = set()
    anchor_re = re.compile(r"glossary\.md(?:#([a-z0-9-]+))?")
    for f in chapter_files:
        text = f.read_text(encoding="utf-8")
        for m in LINK_RE.finditer(text):
            target = m.group(1)
            am = anchor_re.search(target)
            if am and am.group(1):
                anchor = am.group(1).upper().replace("-", "")
                linked.add(anchor)
    return linked


def audit_topic(topic_dir: Path) -> dict:
    docs = topic_dir / "docs"
    if not docs.exists():
        return None
    glossary = parse_glossary(docs / "glossary.md")
    chapter_files = sorted(
        f for f in docs.glob("*.md")
        if f.name not in ("glossary.md", "index.md", "_legacy_overview.md")
        and re.match(r"^\d+_", f.name)
    )
    body_acr = extract_body_acronyms(chapter_files)
    body_set = set(body_acr.keys())
    gloss_set = set()
    for k, v in glossary.items():
        gloss_set |= v["aliases"]

    linked = find_glossary_links(chapter_files)
    missing = sorted(body_set - gloss_set)
    linkless = sorted((body_set & gloss_set) - linked)
    orphan = sorted(gloss_set - body_set - {"X", "Y", "Z"})

    # Frequency-rank missing
    missing_ranked = sorted(
        missing,
        key=lambda t: (-len(body_acr[t]), t),
    )
    return {
        "topic": topic_dir.name,
        "chapters": [f.name for f in chapter_files],
        "glossary_count": len(glossary),
        "body_acr_count": len(body_set),
        "missing": missing_ranked,
        "missing_locations": {t: body_acr[t][:5] for t in missing_ranked},
        "missing_freq": {t: len(body_acr[t]) for t in missing_ranked},
        "linkless": linkless,
        "linkless_freq": {t: len(body_acr[t]) for t in linkless},
        "orphan": orphan,
    }


def write_per_topic(report: dict):
    p = OUT / "per_topic" / f"{report['topic']}.md"
    lines = [
        f"# Glossary Audit — {report['topic']}",
        "",
        f"- Glossary entries: **{report['glossary_count']}**",
        f"- Distinct body acronyms: **{report['body_acr_count']}**",
        f"- Missing (HIGH): **{len(report['missing'])}**",
        f"- Linkless (MED): **{len(report['linkless'])}**",
        f"- Orphan (LOW): **{len(report['orphan'])}**",
        "",
        "## Chapters scanned",
    ]
    for c in report["chapters"]:
        lines.append(f"- `{c}`")
    lines.append("")
    lines.append("## MISSING — body 등장, glossary 미등록 (HIGH)")
    if not report["missing"]:
        lines.append("(없음)")
    else:
        lines.append("")
        lines.append("| Term | Freq | First locations |")
        lines.append("|---|---|---|")
        for t in report["missing"]:
            freq = report["missing_freq"][t]
            locs = report["missing_locations"][t]
            loc_str = "<br>".join(f"`{f}:{ln}`" for f, ln, _ in locs)
            lines.append(f"| **{t}** | {freq} | {loc_str} |")
    lines.append("")
    lines.append("## LINKLESS — glossary 존재, body 링크 미설정 (MED)")
    if not report["linkless"]:
        lines.append("(없음)")
    else:
        lines.append("")
        lines.append("| Term | Body Freq |")
        lines.append("|---|---|")
        for t in report["linkless"]:
            lines.append(f"| {t} | {report['linkless_freq'][t]} |")
    lines.append("")
    lines.append("## ORPHAN — glossary 등록, body 미등장 (LOW)")
    if not report["orphan"]:
        lines.append("(없음)")
    else:
        lines.append("")
        lines.append(", ".join(f"`{t}`" for t in report["orphan"]))
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(reports: list, ko: bool = False):
    name = "SUMMARY_ko.md" if ko else "SUMMARY.md"
    p = OUT / name
    if ko:
        title = "# DV_SKOOL 학습자료 용어집 점검 — 종합 리포트"
        intro = (
            "각 토픽 본문에서 등장하는 약어를 추출해 glossary.md 와 비교했습니다.\n\n"
            "- **MISSING (HIGH)**: 본문에 등장했지만 glossary 에 없음 → 신규 항목 추가 필요\n"
            "- **LINKLESS (MED)**: glossary 에 있지만 본문에서 글로서리 링크 부재 → cross-link 삽입 권고\n"
            "- **ORPHAN (LOW)**: glossary 에 있지만 본문 어디에도 안 나옴 → 사장(死藏) 항목, 검토 권고\n\n"
            "- **Priority 점수**: `MISSING*3 + LINKLESS*1` (본문 사용성 영향 가중)\n"
        )
        cols = "| 토픽 | Glossary | Body 약어 | MISSING (HIGH) | LINKLESS (MED) | ORPHAN (LOW) | Priority |"
    else:
        title = "# DV_SKOOL Glossary Audit — Summary"
        intro = (
            "Acronyms extracted from each topic's chapter bodies were compared against `docs/glossary.md`.\n\n"
            "- **MISSING (HIGH)**: appears in body, not in glossary → add entry.\n"
            "- **LINKLESS (MED)**: in both, but body lacks anchor link → insert cross-link.\n"
            "- **ORPHAN (LOW)**: in glossary, never used in body → review for retirement.\n\n"
            "- **Priority score**: `MISSING*3 + LINKLESS*1`.\n"
        )
        cols = "| Topic | Glossary | Body Acr | MISSING (HIGH) | LINKLESS (MED) | ORPHAN (LOW) | Priority |"

    rows = []
    for r in reports:
        prio = len(r["missing"]) * 3 + len(r["linkless"])
        rows.append((prio, r))
    rows.sort(key=lambda x: -x[0])

    out = [title, "", intro, "", cols, "|---|---|---|---|---|---|---|"]
    for prio, r in rows:
        out.append(
            f"| [{r['topic']}](per_topic/{r['topic']}.md) "
            f"| {r['glossary_count']} | {r['body_acr_count']} "
            f"| **{len(r['missing'])}** | {len(r['linkless'])} "
            f"| {len(r['orphan'])} | {prio} |"
        )

    out.append("")
    out.append("## Top MISSING terms (across all topics)")
    out.append("")
    counter = Counter()
    where = defaultdict(list)
    for r in reports:
        for t in r["missing"]:
            counter[t] += r["missing_freq"][t]
            where[t].append(r["topic"])
    out.append("| Term | Total Freq | Topics |")
    out.append("|---|---|---|")
    for t, freq in counter.most_common(40):
        topics = ", ".join(where[t])
        out.append(f"| **{t}** | {freq} | {topics} |")
    out.append("")
    out.append("## How to read")
    out.append("")
    if ko:
        out.append("- Phase 2 진행 시 Priority 상위부터 batch 처리 권장.")
        out.append("- MISSING 후보는 false positive(코드 식별자, 일반 약어) 가 일부 섞여있을 수 있음 — 토픽별 상세 리포트(per_topic/) 의 등장 위치 확인 후 선별.")
        out.append("- ORPHAN 은 즉시 삭제하지 말고, 본문에서 의도적으로 안 쓴 항목인지 검토.")
    else:
        out.append("- Process Phase 2 in batches starting from top Priority.")
        out.append("- MISSING list may contain false positives (code identifiers, generic acronyms) — vet via per_topic/<id>.md location pointers.")
        out.append("- Don't delete ORPHANs blindly; some may be intentionally referenced from related topics.")

    p.write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    reports = []
    for topic_dir in sorted(ROOT.iterdir()):
        if not topic_dir.is_dir():
            continue
        if topic_dir.name.startswith("_") or topic_dir.name.startswith("."):
            continue
        r = audit_topic(topic_dir)
        if r is None:
            continue
        write_per_topic(r)
        reports.append(r)
        print(f"  {topic_dir.name:30s}  gloss={r['glossary_count']:3d}  body={r['body_acr_count']:3d}  miss={len(r['missing']):3d}  linkless={len(r['linkless']):3d}  orphan={len(r['orphan']):3d}")
    write_summary(reports, ko=False)
    write_summary(reports, ko=True)
    # Raw extraction
    raw = OUT / "data" / "extraction.json"
    raw.write_text(json.dumps([{
        "topic": r["topic"],
        "glossary_count": r["glossary_count"],
        "missing": r["missing"],
        "missing_freq": r["missing_freq"],
        "linkless": r["linkless"],
        "orphan": r["orphan"],
    } for r in reports], indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReports: {OUT}")


if __name__ == "__main__":
    main()
