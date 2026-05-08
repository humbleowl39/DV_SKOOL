#!/usr/bin/env python3
"""ORPHAN 리포트: glossary 에 정의됐지만 본문에 없는 항목 분석."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path("/home/jaehyeok.lee/PRATICE/DV_SKOOL")
AUDIT = ROOT / "20260508_135724_dvskool_GLOSSARY_AUDIT"


def main():
    data = json.loads((AUDIT / "data" / "extraction.json").read_text(encoding="utf-8"))
    # cross-topic ORPHAN matrix: which orphan term appears in another topic?
    body_terms_by_topic = {}
    for entry in data:
        # We only have missing/orphan/linkless extracted; for cross-check,
        # body terms = (missing + linkless). Linkless = body ∩ glossary; missing = body - glossary.
        # body terms ≈ missing ∪ linkless. ORPHAN = glossary - body of own topic.
        body_terms_by_topic[entry["topic"]] = set(entry.get("missing", [])) | set(entry.get("linkless", []))

    cross_use = defaultdict(set)  # orphan_term -> set(other_topics_where_used)
    for entry in data:
        t = entry["topic"]
        for orphan in entry["orphan"]:
            for other_t, terms in body_terms_by_topic.items():
                if other_t == t:
                    continue
                if orphan in terms:
                    cross_use[(t, orphan)].add(other_t)

    out = ["# ORPHAN Review Report (Phase 3)", ""]
    out.append("Glossary 에 정의되어 있으나 해당 토픽 본문에서 단 한 번도 등장하지 않은 항목.")
    out.append("")
    out.append("- **사용 (다른 토픽)**: 다른 토픽 본문에서는 등장 — 공유 abbr 후보 또는 cross-topic reference")
    out.append("- **사장**: 어떤 토픽 본문에서도 등장하지 않음 — 폐지 또는 본문 보강 후보")
    out.append("")
    out.append("자동 삭제 금지. 검토 후 결정.")
    out.append("")

    rows = []
    for entry in data:
        if not entry["orphan"]:
            continue
        rows.append((len(entry["orphan"]), entry))
    rows.sort(key=lambda x: -x[0])

    out.append("## 토픽별 요약")
    out.append("")
    out.append("| Topic | Glossary 총 | ORPHAN 수 | ORPHAN 비율 |")
    out.append("|---|---|---|---|")
    for cnt, e in rows:
        ratio = cnt / e["glossary_count"] if e["glossary_count"] else 0
        out.append(f"| [{e['topic']}](#{e['topic']}) | {e['glossary_count']} | {cnt} | {ratio*100:.0f}% |")
    out.append("")

    for cnt, e in rows:
        t = e["topic"]
        out.append(f"## {t}")
        out.append("")
        out.append("| Term | 다른 토픽 사용 | 분류 |")
        out.append("|---|---|---|")
        for orph in e["orphan"]:
            others = sorted(cross_use.get((t, orph), set()))
            if others:
                cls = "사용 (다른 토픽)"
                others_str = ", ".join(others)
            else:
                cls = "사장"
                others_str = "—"
            out.append(f"| `{orph}` | {others_str} | {cls} |")
        out.append("")

    p = AUDIT / "ORPHAN_REPORT.md"
    p.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote: {p}")


if __name__ == "__main__":
    main()
