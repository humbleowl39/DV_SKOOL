#!/usr/bin/env python3
"""Apply abbr-tooltip infrastructure to target topics.

Per topic:
  1. Patch mkdocs.yml: change `- pymdownx.snippets` line to a dict with
     base_path: [docs, ../_shared] (idempotent).
  2. Append `--8<-- "abbreviations.md"` to every chapter file (NN_*.md and
     index/_legacy_overview), idempotent.
  3. Run `mkdocs build --strict` and report pass/fail.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/jaehyeok.lee/PRATICE/DV_SKOOL")
TOPICS = [
    # priority 5 (already done)
    "rdma", "pcie", "amba_protocols", "soc_secure_boot", "ufs_hci",
    # remaining 13
    "ai_engineering", "arm_security", "automotive_cybersecurity",
    "bigtech_algorithm", "dram_ddr", "ethernet_dcmac", "formal_verification",
    "mmu", "rdma_verification", "soc_integration_cctv", "toe", "uvm",
    "virtualization",
]

ABBR_INCLUDE_LINE = '--8<-- "abbreviations.md"'
ABBR_INCLUDE_BLOCK = f"\n\n{ABBR_INCLUDE_LINE}\n"

SNIPPETS_PATCHED = """  - pymdownx.snippets:
      base_path:
        - docs
        - ../_shared
      check_paths: true"""

SNIPPETS_BARE_RE = re.compile(r"^  - pymdownx\.snippets\s*$", re.MULTILINE)


def patch_mkdocs_yml(topic: str) -> str:
    p = ROOT / "topics" / topic / "mkdocs.yml"
    text = p.read_text(encoding="utf-8")
    if "../_shared" in text:
        return "skip (already patched)"
    if SNIPPETS_BARE_RE.search(text):
        new = SNIPPETS_BARE_RE.sub(SNIPPETS_PATCHED, text, count=1)
        p.write_text(new, encoding="utf-8")
        return "patched (bare→dict)"
    return "WARN: pymdownx.snippets not found in expected form"


def chapter_files(topic: str) -> list[Path]:
    docs = ROOT / "topics" / topic / "docs"
    files = []
    for f in sorted(docs.glob("*.md")):
        if f.name in ("glossary.md",):
            continue
        # include numeric-prefixed chapters and _legacy_overview, index
        files.append(f)
    return files


def append_include(file: Path) -> str:
    text = file.read_text(encoding="utf-8")
    if ABBR_INCLUDE_LINE in text:
        return "skip"
    # ensure trailing newline, then add include
    if not text.endswith("\n"):
        text += "\n"
    text += ABBR_INCLUDE_BLOCK
    file.write_text(text, encoding="utf-8")
    return "appended"


def run_strict_build(topic: str) -> tuple[bool, str]:
    cwd = ROOT / "topics" / topic
    proc = subprocess.run(
        ["mkdocs", "build", "--strict"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    ok = proc.returncode == 0
    tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-20:])
    return ok, tail


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    topics = TOPICS if target == "all" else [target]
    results = []
    for t in topics:
        print(f"\n=== {t} ===")
        m = patch_mkdocs_yml(t)
        print(f"  mkdocs.yml: {m}")
        for f in chapter_files(t):
            r = append_include(f)
            print(f"  {f.name:40s} {r}")
        ok, tail = run_strict_build(t)
        status = "OK" if ok else "FAIL"
        print(f"  strict build: {status}")
        if not ok:
            print("  --- last 20 lines ---")
            print(tail)
        results.append((t, ok))
    print("\n=== SUMMARY ===")
    for t, ok in results:
        print(f"  {t:25s} {'OK' if ok else 'FAIL'}")


if __name__ == "__main__":
    main()
