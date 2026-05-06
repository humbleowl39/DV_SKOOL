#!/usr/bin/env python3
"""
Build MkDocs topic sites from learn_practice/.

For each topic:
- Copy non-PLAN .md files into topics/<slug>/docs/
- Rename 00_overview_*.md to index.md
- For bigtech_algorithm: embed *.sv into corresponding *_explained.md
- Generate topics/<slug>/mkdocs.yml with nav extracted from H1 titles
"""
from __future__ import annotations
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "learn_practice"
DST = ROOT / "DV_SKOOL" / "topics"

# (source_dir_name, slug, site_name, site_description)
TOPICS = [
    ("uvm_ko", "uvm",
     "UVM",
     "Universal Verification Methodology — 아키텍처, phase, agent, sequence, factory, TLM, coverage"),
    ("amba_protocols_ko", "amba_protocols",
     "AMBA Protocols",
     "ARM AMBA — APB, AHB, AXI, AXI-Stream 프로토콜"),
    ("formal_verification_ko", "formal_verification",
     "Formal Verification",
     "정형 검증 — SVA, JasperGold, 검증 전략"),
    ("mmu_ko", "mmu",
     "MMU",
     "Memory Management Unit — 페이지 테이블, TLB, IOMMU/SMMU, 성능 분석, DV 방법론"),
    ("dram_ddr_ko", "dram_ddr",
     "DRAM / DDR",
     "DRAM 기본, 메모리 컨트롤러, PHY, DDR DV 방법론"),
    ("ufs_hci_ko", "ufs_hci",
     "UFS HCI",
     "Universal Flash Storage — 프로토콜 스택, HCI 아키텍처, UPIU command flow"),
    ("ethernet_dcmac_ko", "ethernet_dcmac",
     "Ethernet DCMAC",
     "Ethernet 기본, DCMAC 아키텍처, DV 방법론"),
    ("toe_ko", "toe",
     "TOE",
     "TCP/IP Offload Engine — 아키텍처, 핵심 기능, DV 방법론"),
    ("soc_integration_cctv_ko", "soc_integration_cctv",
     "SoC Integration (CCTV)",
     "SoC top integration — 공통 task, TB top, AI 활용 (CCTV 케이스)"),
    ("soc_secure_boot_ko", "soc_secure_boot",
     "SoC Secure Boot",
     "Hardware Root of Trust, chain of trust, crypto, attack surface, BootROM DV"),
    ("arm_security_ko", "arm_security",
     "ARM Security",
     "Exception Level, TrustZone, secure enclave, TEE, secure boot 연계"),
    ("virtualization_ko", "virtualization",
     "Virtualization",
     "CPU/메모리/IO 가상화, 하이퍼바이저, 컨테이너, modern virt"),
    ("automotive_cybersecurity_ko", "automotive_cybersecurity",
     "Automotive Cybersecurity",
     "CAN bus, automotive SoC 보안, Tesla FSD case study, attack surface & defense"),
    ("ai_engineering_ko", "ai_engineering",
     "AI Engineering",
     "LLM 기본, 프롬프트 엔지니어링, RAG, agent 아키텍처, DV 적용"),
    ("bigtech_algorithm", "bigtech_algorithm",
     "BigTech Algorithm",
     "코딩 인터뷰 — Big-O, 자료구조, 알고리즘 + SystemVerilog 예제"),
]

# Files to exclude (improvement plans, etc.)
EXCLUDE_PATTERNS = [
    re.compile(r"^\d{8}_.*PLAN.*\.md$", re.IGNORECASE),
    re.compile(r"^\d{8}_.*IMPROVE.*\.md$", re.IGNORECASE),
    re.compile(r"^\d{8}_.*improvement.*\.md$", re.IGNORECASE),
    re.compile(r"^\d{8}_.*CONTENT.*\.md$", re.IGNORECASE),
    re.compile(r"^\d{8}_.*content_improvement.*\.md$", re.IGNORECASE),
]


def is_excluded(name: str) -> bool:
    return any(p.match(name) for p in EXCLUDE_PATTERNS)


def extract_h1(path: Path) -> str | None:
    with path.open(encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^#\s+(.+?)\s*$", line)
            if m:
                return m.group(1).strip()
    return None


def short_title(h1: str) -> str:
    """Shorten H1 for nav display."""
    # "Unit N: foo" → "N. foo" (keep)
    # "topic — 개요" or "topic - 개요" → use part after dash
    # otherwise return as-is
    return h1


def make_mkdocs_yml(slug: str, site_name: str, site_desc: str, nav_entries: list[tuple[str, str]]) -> str:
    nav_yaml = "\n".join(f'  - "{title}": {fname}' for title, fname in nav_entries)
    return f"""site_name: {site_name}
site_description: {site_desc}
site_url: https://humbleowl39.github.io/DV_SKOOL/{slug}/

theme:
  name: material
  language: ko
  features:
    - navigation.instant
    - navigation.tracking
    - navigation.tabs
    - navigation.top
    - navigation.expand
    - navigation.indexes
    - toc.follow
    - search.suggest
    - search.highlight
    - content.code.copy
    - content.code.annotate
    - content.tabs.link
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: 다크 모드로 전환
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: 라이트 모드로 전환
  icon:
    repo: fontawesome/brands/github

repo_url: https://github.com/humbleowl39/DV_SKOOL
repo_name: humbleowl39/DV_SKOOL
edit_uri: edit/main/topics/{slug}/docs/

nav:
{nav_yaml}

markdown_extensions:
  - admonition
  - attr_list
  - def_list
  - footnotes
  - md_in_html
  - tables
  - toc:
      permalink: true
      toc_depth: 3
  - pymdownx.details
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.highlight:
      anchor_linenums: true
      line_spans: __span
      pygments_lang_class: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.tasklist:
      custom_checkbox: true
  - pymdownx.tilde
  - pymdownx.caret
  - pymdownx.mark
  - pymdownx.keys
  - pymdownx.smartsymbols
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/humbleowl39/DV_SKOOL
  generator: false

copyright: DV SKOOL — 학습용 자료
"""


def embed_sv_files(src_dir: Path, dst_docs: Path) -> None:
    """For bigtech_algorithm: embed *.sv into corresponding *_explained.md."""
    for sv_file in sorted(src_dir.glob("*.sv")):
        # 01_big_o.sv → 01_big_o_explained.md
        stem = sv_file.stem  # "01_big_o"
        md_target = dst_docs / f"{stem}_explained.md"
        if not md_target.exists():
            print(f"  skip {sv_file.name}: no matching {md_target.name}")
            continue
        sv_content = sv_file.read_text(encoding="utf-8")
        appendix = (
            "\n\n---\n\n"
            "## 부록: SystemVerilog 예제 코드\n\n"
            f"원본 파일: `{sv_file.name}`\n\n"
            "```systemverilog\n"
            f"{sv_content}\n"
            "```\n"
        )
        with md_target.open("a", encoding="utf-8") as f:
            f.write(appendix)
        print(f"  embedded {sv_file.name} → {md_target.name}")


def build_topic(src_name: str, slug: str, site_name: str, site_desc: str) -> None:
    src_dir = SRC / src_name
    if not src_dir.is_dir():
        print(f"!! source dir not found: {src_dir}")
        return

    dst_dir = DST / slug
    docs_dir = dst_dir / "docs"
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Copy MD files
    md_files = sorted(p for p in src_dir.glob("*.md") if not is_excluded(p.name))
    overview_renamed = False
    nav_entries: list[tuple[str, str]] = []

    for md in md_files:
        target_name = "index.md" if md.name.startswith("00_overview") else md.name
        if target_name == "index.md":
            overview_renamed = True
        target = docs_dir / target_name
        shutil.copy2(md, target)

    if not overview_renamed:
        # Synthesize an index.md if there's no 00_overview*
        first_md = md_files[0] if md_files else None
        index = docs_dir / "index.md"
        if not index.exists() and first_md:
            shutil.copy2(first_md, index)

    # Build nav from copied files in order
    for f in sorted(docs_dir.glob("*.md")):
        if f.name == "index.md":
            h1 = extract_h1(f) or "개요"
            nav_entries.insert(0, (h1, "index.md"))
        else:
            h1 = extract_h1(f) or f.stem
            nav_entries.append((h1, f.name))

    # bigtech_algorithm: embed .sv files
    if slug == "bigtech_algorithm":
        embed_sv_files(src_dir, docs_dir)

    # Write mkdocs.yml
    yml = make_mkdocs_yml(slug, site_name, site_desc, nav_entries)
    (dst_dir / "mkdocs.yml").write_text(yml, encoding="utf-8")
    print(f"==> {slug}: {len(nav_entries)} pages")


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)
    for src_name, slug, site_name, site_desc in TOPICS:
        print(f"\n--- Building {slug} ({src_name}) ---")
        build_topic(src_name, slug, site_name, site_desc)
    print("\nAll topics built.")


if __name__ == "__main__":
    main()
