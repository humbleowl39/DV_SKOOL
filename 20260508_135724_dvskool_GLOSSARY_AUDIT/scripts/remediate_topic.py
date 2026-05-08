#!/usr/bin/env python3
"""Per-topic remediation: classify MISSING, extract full-names, add abbr + glossary stub.

Pipeline:
  1. Read MISSING list from per_topic/<topic>.md (already produced by audit.py).
  2. auto-classify into auto-keep / auto-drop / manual-review:
       - auto-drop : English word stoplist (FIRST/LAST/ONLY/APPLICABLE/etc.) UNLESS the
         topic whitelists it as a keyword (e.g. RDMA opcodes).
       - auto-keep : freq >= 5  AND  length >= 3  AND  alphanumeric only  AND  not in shared abbr.
       - manual-review : everything else (low-freq, length-2, mixed digits-only, etc.).
  3. For each auto-keep term, scan body for `TERM (Full Name)` pattern; capture full name.
     Fallback: if no parenthetical form, term is moved to manual-review.
  4. Write topics/<topic>/docs/_inc/topic_abbr.md (abbr definitions) and append include
     line to chapters (idempotent, after shared abbr include).
  5. Append ISO 11179 stub entries to topics/<topic>/docs/glossary.md (with
     **(자동 추출)** marker and Source.= 추론, requires verification).
  6. Run mkdocs build --strict, report.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path("/home/jaehyeok.lee/PRATICE/DV_SKOOL")
AUDIT = ROOT / "20260508_135724_dvskool_GLOSSARY_AUDIT"
SHARED_ABBR_FILE = ROOT / "topics" / "_shared" / "abbreviations.md"

# Acronyms already defined in shared file — never re-add at topic level.
SHARED_ABBR_TERMS = set()
for line in SHARED_ABBR_FILE.read_text(encoding="utf-8").splitlines():
    m = re.match(r"\*\[([A-Z][A-Z0-9_]*)\]:", line)
    if m:
        SHARED_ABBR_TERMS.add(m.group(1))

# English words that look like acronyms but aren't.
ENGLISH_WORD_DROP = {
    "FIRST", "LAST", "MIDDLE", "ONLY", "READ", "WRITE", "SEND", "RECV",
    "APPLICABLE", "AS", "OK", "FAIL", "PASS", "TRUE", "FALSE", "NULL", "NONE",
    "DEFAULT", "NEW", "OLD", "AUTO", "DONE", "ENDIAN",
    "MOVE", "COPY", "CAS", "ADD", "SUB", "MUL", "DIV",
    "VALID", "READY", "ERROR", "WARN", "DEBUG", "TRACE",
    "IDLE", "BUSY", "WAIT", "POLL", "STOP", "START", "RUN", "EXIT", "INIT",
    "TBA", "TOC", "FAQ", "TBD",
}

# Topic-specific whitelist: even if word matches ENGLISH_WORD_DROP, keep if listed here.
TOPIC_WHITELIST = {
    "rdma": {"READ", "WRITE", "SEND", "RECV", "FIRST", "LAST", "MIDDLE", "ONLY", "CAS"},
    "pcie": {},
    "amba_protocols": {"VALID", "READY"},
    "soc_secure_boot": {},
    "ufs_hci": {},
}

PAREN_FULL_RE = lambda acr: re.compile(
    rf"\b{re.escape(acr)}\s*\(\s*([A-Z][A-Za-z0-9 ,/\-]{{2,80}})\s*\)"
)

GLOSS_HEAD_ANY = re.compile(r"^### ", re.MULTILINE)


def load_extraction(topic: str) -> dict:
    data = json.loads((AUDIT / "data" / "extraction.json").read_text(encoding="utf-8"))
    for entry in data:
        if entry["topic"] == topic:
            return entry
    raise KeyError(topic)


def chapter_files(topic: str) -> list[Path]:
    docs = ROOT / "topics" / topic / "docs"
    return sorted(
        f for f in docs.glob("*.md")
        if f.name not in ("glossary.md",) and not f.name.startswith("_")
    ) + [f for f in docs.glob("_legacy_overview.md")]


def extract_full_name(term: str, chapters: list[Path]) -> str | None:
    """Search chapters for `TERM (Full Name)` pattern; return first match."""
    rx = PAREN_FULL_RE(term)
    for f in chapters:
        text = f.read_text(encoding="utf-8")
        m = rx.search(text)
        if m:
            full = m.group(1).strip().rstrip(",").strip()
            # sanity: not too short, not obviously another acronym only
            if len(full) >= 3 and not full.isupper():
                return full
            if len(full) >= 5:
                return full
    return None


def first_location(term: str, chapters: list[Path]) -> tuple[str, int] | None:
    rx = re.compile(rf"\b{re.escape(term)}\b")
    for f in chapters:
        for ln_no, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if rx.search(line):
                return (f.stem, ln_no)
    return None


def classify(topic: str, missing: list[str], freq: dict[str, int]) -> dict:
    out = {"auto_keep": [], "auto_drop": [], "manual_review": []}
    whitelist = TOPIC_WHITELIST.get(topic, set())
    for t in missing:
        f = freq.get(t, 0)
        if t in SHARED_ABBR_TERMS:
            out["auto_drop"].append((t, f, "in shared abbr"))
            continue
        if t in ENGLISH_WORD_DROP and t not in whitelist:
            out["auto_drop"].append((t, f, "english word"))
            continue
        if not re.fullmatch(r"[A-Z][A-Z0-9]+", t):
            out["manual_review"].append((t, f, "non-alphanumeric"))
            continue
        if f >= 5 and len(t) >= 3:
            out["auto_keep"].append((t, f, "freq>=5 len>=3"))
        else:
            out["manual_review"].append((t, f, f"freq={f} len={len(t)}"))
    return out


def write_topic_abbr(topic: str, kept: list[tuple], full_names: dict[str, str]):
    """Write topic-specific abbreviations file as docs/_inc/topic_abbr.md."""
    inc_dir = ROOT / "topics" / topic / "docs" / "_inc"
    inc_dir.mkdir(parents=True, exist_ok=True)
    p = inc_dir / "topic_abbr.md"
    lines = [
        "<!-- Topic-specific abbreviations (auto-generated by glossary audit Phase 2). -->",
        "<!-- Manual review항목은 아직 포함되지 않았으며, 추가 정의 필요 시 직접 등록하세요. -->",
        "",
    ]
    for term, freq, _ in kept:
        full = full_names.get(term)
        if full is None:
            continue
        lines.append(f"*[{term}]: {full}")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def append_topic_abbr_include(topic: str):
    """Append `--8<-- "_inc/topic_abbr.md"` to every chapter (after shared include)."""
    line = '--8<-- "_inc/topic_abbr.md"'
    for f in chapter_files(topic) + [ROOT / "topics" / topic / "docs" / "index.md"]:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        if line in text:
            continue
        if not text.endswith("\n"):
            text += "\n"
        text += line + "\n"
        f.write_text(text, encoding="utf-8")


def append_glossary_stubs(topic: str, kept: list[tuple], full_names: dict[str, str], freq: dict[str, int], chapters: list[Path]):
    """Append ISO 11179 stub entries to glossary.md under '## Auto-extracted (검수 필요)'."""
    g = ROOT / "topics" / topic / "docs" / "glossary.md"
    text = g.read_text(encoding="utf-8")

    # Don't add if already exists for that term
    existing_heads = set()
    for m in re.finditer(r"^###\s+([A-Z][A-Z0-9_]+)", text, re.MULTILINE):
        existing_heads.add(m.group(1))

    new_entries = []
    for term, fr, _ in kept:
        if term in existing_heads:
            continue
        full = full_names.get(term)
        if full is None:
            continue
        loc = first_location(term, chapters)
        loc_str = f"`{loc[0]}.md:{loc[1]}`" if loc else "(미상)"
        new_entries.append((term, full, fr, loc_str))

    if not new_entries:
        return 0

    # avoid duplicating the section header on re-run
    section_marker = "## Auto-extracted (검수 필요)"
    if section_marker not in text:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n---\n\n"
        text += section_marker + "\n\n"
        text += "아래 항목은 본문에서 자동 추출된 약어로, 정의 문장은 추정값입니다. 사용자 검수 후 ISO 11179 정식 형식으로 다듬어 주세요.\n\n"

    block = []
    for term, full, fr, loc_str in new_entries:
        block.append(f"### {term} ({full})\n")
        block.append(f"**Definition.** {full}. **(자동 추출, 검수 필요)**\n")
        block.append(f"**Source.** 본문 문맥(추론) — 첫 등장 {loc_str}.\n")
        block.append(f"**Related.** (검수 시 보강)\n")
        block.append(f"**Example.** (검수 시 보강)\n")
        block.append("")
    text += "\n".join(block) + "\n"
    g.write_text(text, encoding="utf-8")
    return len(new_entries)


def run_strict_build(topic: str) -> tuple[bool, str]:
    cwd = ROOT / "topics" / topic
    proc = subprocess.run(
        ["mkdocs", "build", "--strict"],
        cwd=cwd, capture_output=True, text=True,
    )
    return proc.returncode == 0, "\n".join((proc.stdout + proc.stderr).splitlines()[-15:])


def remediate(topic: str) -> dict:
    print(f"\n=== {topic} ===")
    e = load_extraction(topic)
    classification = classify(topic, e["missing"], e["missing_freq"])
    print(f"  auto_keep: {len(classification['auto_keep'])}, "
          f"auto_drop: {len(classification['auto_drop'])}, "
          f"manual_review: {len(classification['manual_review'])}")

    chapters = chapter_files(topic)
    full_names = {}
    no_full_name = []
    for term, fr, _ in classification["auto_keep"]:
        full = extract_full_name(term, chapters)
        if full:
            full_names[term] = full
        else:
            no_full_name.append((term, fr))

    # demote auto_keep without full name -> manual_review
    classification["auto_keep"] = [t for t in classification["auto_keep"] if t[0] in full_names]
    for term, fr in no_full_name:
        classification["manual_review"].append((term, fr, "no parenthetical full name in body"))

    print(f"  full name extracted: {len(full_names)}")
    print(f"  -> manual_review (no full name): {len(no_full_name)}")

    abbr_path = write_topic_abbr(topic, classification["auto_keep"], full_names)
    print(f"  topic abbr file: {abbr_path}")
    append_topic_abbr_include(topic)
    added = append_glossary_stubs(topic, classification["auto_keep"], full_names, e["missing_freq"], chapters)
    print(f"  glossary stubs added: {added}")

    ok, tail = run_strict_build(topic)
    print(f"  strict build: {'OK' if ok else 'FAIL'}")
    if not ok:
        print(tail)

    # Write per-topic remediation report
    rep = AUDIT / "per_topic" / f"{topic}_remediation.md"
    lines = [
        f"# Remediation — {topic}",
        "",
        f"- auto-keep (added): {len(classification['auto_keep'])}",
        f"- auto-drop: {len(classification['auto_drop'])}",
        f"- manual-review: {len(classification['manual_review'])}",
        "",
        "## Auto-keep (added to abbr + glossary stub)",
        "",
        "| Term | Freq | Full name (extracted) |",
        "|---|---|---|",
    ]
    for term, fr, _ in classification["auto_keep"]:
        lines.append(f"| **{term}** | {fr} | {full_names[term]} |")
    lines.append("")
    lines.append("## Auto-drop")
    lines.append("")
    lines.append("| Term | Freq | Reason |")
    lines.append("|---|---|---|")
    for t, fr, why in classification["auto_drop"]:
        lines.append(f"| {t} | {fr} | {why} |")
    lines.append("")
    lines.append("## Manual-review (need user decision)")
    lines.append("")
    lines.append("| Term | Freq | Reason |")
    lines.append("|---|---|---|")
    for t, fr, why in classification["manual_review"]:
        lines.append(f"| {t} | {fr} | {why} |")
    rep.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {"topic": topic, "ok": ok, **{k: len(v) for k, v in classification.items()},
            "abbr_added": len(full_names), "glossary_stubs_added": added}


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    topics = ["rdma", "pcie", "amba_protocols", "soc_secure_boot", "ufs_hci"] if target == "all" else [target]
    summary = []
    for t in topics:
        summary.append(remediate(t))
    print("\n=== SUMMARY ===")
    print(f"{'topic':<22}{'auto_keep':>10}{'auto_drop':>11}{'manual':>9}{'abbr':>6}{'gloss':>7}{'build':>8}")
    for s in summary:
        print(f"{s['topic']:<22}{s['auto_keep']:>10}{s['auto_drop']:>11}{s['manual_review']:>9}"
              f"{s['abbr_added']:>6}{s['glossary_stubs_added']:>7}{('OK' if s['ok'] else 'FAIL'):>8}")


if __name__ == "__main__":
    main()
