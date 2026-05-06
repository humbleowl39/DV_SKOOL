#!/usr/bin/env python3
"""
Build MkDocs topic sites from learn_practice/ — v2 (학습 사이트화).

Per topic:
- Copy non-PLAN .md files into topics/<slug>/docs/
- Rename 00_overview_*.md → _legacy_overview.md (preserved as appendix)
- Generate course-home index.md (with module cards, learning path)
- Inject per-chapter meta block (reading time + level badge) after H1
- Append per-chapter footer (Next/Prev nav)
- Generate glossary.md skeleton
- Generate quiz/index.md skeleton + per-chapter quiz placeholder
- Copy stylesheets/extra.css
- Embed *.sv into *_explained.md (bigtech_algorithm only)
- Generate enhanced mkdocs.yml (extra_css, tags plugin, more features)

UVM topic: structural scaffolding only (deep content overrides applied separately).
"""
from __future__ import annotations
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "learn_practice"
DST = ROOT / "DV_SKOOL" / "topics"
TEMPLATES = Path(__file__).resolve().parent / "templates"

# (source_dir_name, slug, site_name, site_description, level, prereqs)
TOPICS = [
    ("uvm_ko", "uvm",
     "UVM",
     "Universal Verification Methodology — 아키텍처, phase, agent, sequence, factory, TLM, coverage",
     "advanced",
     "SystemVerilog 객체지향 (class, virtual, randomize), 시뮬레이터 사용 경험"),
    ("amba_protocols_ko", "amba_protocols",
     "AMBA Protocols",
     "ARM AMBA — APB, AHB, AXI, AXI-Stream 프로토콜",
     "intermediate",
     "디지털 회로 기본, 클럭 도메인, 핸드셰이크 개념"),
    ("formal_verification_ko", "formal_verification",
     "Formal Verification",
     "정형 검증 — SVA, JasperGold, 검증 전략",
     "advanced",
     "SystemVerilog, 시뮬레이션 기반 검증 경험, 명제 논리 기본"),
    ("mmu_ko", "mmu",
     "MMU",
     "Memory Management Unit — 페이지 테이블, TLB, IOMMU/SMMU, 성능 분석, DV 방법론",
     "advanced",
     "CPU 아키텍처(가상/물리 주소), 캐시 계층, OS 메모리 관리 기초"),
    ("dram_ddr_ko", "dram_ddr",
     "DRAM / DDR",
     "DRAM 기본, 메모리 컨트롤러, PHY, DDR DV 방법론",
     "intermediate",
     "디지털 회로, 클럭/타이밍 기본, SoC 메모리 서브시스템 개요"),
    ("ufs_hci_ko", "ufs_hci",
     "UFS HCI",
     "Universal Flash Storage — 프로토콜 스택, HCI 아키텍처, UPIU command flow",
     "advanced",
     "스토리지 프로토콜 일반, SoC 인터커넥트, AXI/AHB"),
    ("ethernet_dcmac_ko", "ethernet_dcmac",
     "Ethernet DCMAC",
     "Ethernet 기본, DCMAC 아키텍처, DV 방법론",
     "advanced",
     "OSI 모델, MAC/PHY 분리 개념, 네트워크 패킷 구조"),
    ("toe_ko", "toe",
     "TOE",
     "TCP/IP Offload Engine — 아키텍처, 핵심 기능, DV 방법론",
     "advanced",
     "TCP/IP 스택 기본, NIC 동작 원리, AMBA 인터커넥트"),
    ("soc_integration_cctv_ko", "soc_integration_cctv",
     "SoC Integration (CCTV)",
     "SoC top integration — 공통 task, TB top, AI 활용 (CCTV 케이스)",
     "advanced",
     "UVM, AMBA, SoC top 디자인 흐름"),
    ("soc_secure_boot_ko", "soc_secure_boot",
     "SoC Secure Boot",
     "Hardware Root of Trust, chain of trust, crypto, attack surface, BootROM DV",
     "advanced",
     "암호 기본(해시/서명), 부트 시퀀스 개념, 키 관리"),
    ("arm_security_ko", "arm_security",
     "ARM Security",
     "Exception Level, TrustZone, secure enclave, TEE, secure boot 연계",
     "advanced",
     "ARMv8-A 아키텍처 기초, 권한 모델, secure boot 개요"),
    ("virtualization_ko", "virtualization",
     "Virtualization",
     "CPU/메모리/IO 가상화, 하이퍼바이저, 컨테이너, modern virt",
     "intermediate",
     "OS 기본, 가상메모리/페이지테이블, 인터럽트/예외"),
    ("automotive_cybersecurity_ko", "automotive_cybersecurity",
     "Automotive Cybersecurity",
     "CAN bus, automotive SoC 보안, Tesla FSD case study, attack surface & defense",
     "intermediate",
     "임베디드 SoC 기초, 네트워크 보안 개념"),
    ("ai_engineering_ko", "ai_engineering",
     "AI Engineering",
     "LLM 기본, 프롬프트 엔지니어링, RAG, agent 아키텍처, DV 적용",
     "intermediate",
     "Python, 머신러닝/딥러닝 개요, API 호출 경험"),
    ("bigtech_algorithm", "bigtech_algorithm",
     "BigTech Algorithm",
     "코딩 인터뷰 — Big-O, 자료구조, 알고리즘 + SystemVerilog 예제",
     "intermediate",
     "프로그래밍 일반, 자료구조 기초"),
]

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


def estimate_reading_time(text: str) -> int:
    """
    Reading time in minutes (Korean-heavy mixed content).
    Korean: ~500 chars/min. English: ~200 words/min.
    Heuristic: chars/500 ≈ minutes (Korean-dominant).
    """
    # Strip code blocks (read-faster, count half)
    code_blocks = re.findall(r"```.*?```", text, flags=re.DOTALL)
    code_chars = sum(len(b) for b in code_blocks)
    text_no_code = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    chars = len(text_no_code)
    # Korean ~500 cpm, code ~ count half-weight
    minutes = chars / 500 + code_chars / 1000
    return max(3, round(minutes))


def normalize_title(s: str) -> str:
    """Strip 'Unit N:' / leading numbers etc for shorter card display."""
    s = re.sub(r"^Unit\s+\d+\s*[:.\-]\s*", "", s)
    s = re.sub(r"^\d+\.\s*", "", s)
    return s.strip()


# ============================================================
# Per-chapter content transforms
# ============================================================

META_RE = re.compile(r'<div class="learning-meta">.*?</div>\n*', re.DOTALL)
NAV_RE = re.compile(r'<div class="chapter-nav">.*?</div>\n*', re.DOTALL)


def inject_chapter_meta(md_text: str, level: str) -> str:
    """Insert <div class="learning-meta"> right after H1."""
    # Remove old meta block if present
    md_text = META_RE.sub("", md_text)

    level_label = {"beginner": "Beginner", "intermediate": "Intermediate", "advanced": "Advanced"}[level]
    meta_html = (
        f'<div class="learning-meta">\n'
        f'  <span class="meta-badge meta-level-{level}">📊 {level_label}</span>\n'
        f'</div>\n\n'
    )

    # Find H1 and insert after
    lines = md_text.splitlines(keepends=True)
    out = []
    inserted = False
    for i, line in enumerate(lines):
        out.append(line)
        if not inserted and re.match(r"^#\s+\S", line):
            # Skip blank lines after H1, then insert
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                out.append(lines[j])
                j += 1
            out.append(meta_html)
            # Restore the rest
            out.extend(lines[j:])
            inserted = True
            break
    return "".join(out) if inserted else (meta_html + md_text)


def chapter_to_dir_href(href: str) -> str:
    """
    Convert filename-based href used inside chapter pages to a directory URL
    that's relative to the chapter's rendered location.

    With MkDocs use_directory_urls=true, a chapter file `01_foo.md` is served
    at `/<topic>/01_foo/`. Sibling links must therefore go up one level:
        index.md         → ../
        quiz/index.md    → ../quiz/
        02_bar.md        → ../02_bar/
    """
    if href == "index.md":
        return "../"
    if href == "quiz/index.md":
        return "../quiz/"
    if href.endswith(".md"):
        return "../" + href[:-3] + "/"
    return href


def append_chapter_nav(md_text: str, prev: tuple[str, str] | None, next_: tuple[str, str] | None) -> str:
    """Append <div class="chapter-nav"> with Prev/Next links."""
    md_text = NAV_RE.sub("", md_text).rstrip() + "\n"

    if not prev and not next_:
        return md_text

    parts = ['\n<div class="chapter-nav">\n']
    if prev:
        title, href = prev
        parts.append(
            f'  <a class="nav-prev" href="{chapter_to_dir_href(href)}">\n'
            f'    <div class="nav-label">◀ 이전</div>\n'
            f'    <div class="nav-title">{title}</div>\n'
            f'  </a>\n'
        )
    if next_:
        title, href = next_
        parts.append(
            f'  <a class="nav-next" href="{chapter_to_dir_href(href)}">\n'
            f'    <div class="nav-label">다음 ▶</div>\n'
            f'    <div class="nav-title">{title}</div>\n'
            f'  </a>\n'
        )
    parts.append('</div>\n')
    return md_text + "".join(parts)


# ============================================================
# Course-home index.md
# ============================================================

def make_course_home(
    site_name: str,
    site_desc: str,
    level: str,
    prereqs: str,
    chapters: list[dict],
    has_legacy_overview: bool,
) -> str:
    level_label = {"beginner": "초급", "intermediate": "중급", "advanced": "심화"}[level]

    cards_html = '<div class="course-grid">\n'
    for i, c in enumerate(chapters, 1):
        # MkDocs use_directory_urls=true → strip .md, append /
        href_dir = c["href"][:-3] + "/" if c["href"].endswith(".md") else c["href"]
        cards_html += (
            f'  <a class="course-card" href="{href_dir}">\n'
            f'    <div class="course-card-num">Module {i:02d}</div>\n'
            f'    <div class="course-card-title">{c["title"]}</div>\n'
            f'  </a>\n'
        )
    cards_html += '</div>\n'

    legacy_link = ""
    if has_legacy_overview:
        legacy_link = (
            "\n## 개요 & 컨셉 맵\n\n"
            "코스 전체의 컨셉 맵과 깊이 있는 개요는 다음 문서를 참고하세요:\n\n"
            "→ [**코스 개요 & 컨셉 맵**](_legacy_overview.md)\n"
        )

    return f"""# {site_name}

{site_desc}

<div class="course-header">
  <div class="course-stats">
    <div class="stat-item"><strong>{len(chapters)}</strong>개 모듈</div>
    <div class="stat-item"><strong>{level_label}</strong> 난이도</div>
  </div>
</div>

## 사전 지식

{prereqs}

## 학습 모듈

{cards_html}

## 관련 자료

- 📚 [**용어집 (Glossary)**](glossary.md) — 핵심 용어 정의 및 교차 참조
- 📝 [**퀴즈 (Quizzes)**](quiz/index.md) — 챕터별 이해도 점검
{legacy_link}
"""


# ============================================================
# Glossary skeleton
# ============================================================

def make_glossary_skeleton(site_name: str, slug: str) -> str:
    return f"""# {site_name} 용어집

이 페이지는 **{site_name}** 코스에서 사용되는 핵심 용어의 정의 모음입니다. 각 항목은 ISO 11179 형식을 따릅니다 (Definition / Source / Related / Example / See also).

!!! tip "검색 활용"
    상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.

---

## 사용 안내

- **Definition** — 용어가 *무엇인지*를 한 문장으로 정의
- **Source** — 정의의 출처 (스펙 문서, 본 코스의 챕터, 일반적 관용 표현 등)
- **Related** — 함께 알아두면 좋은 인접 용어
- **Example** — 짧은 사용 예 (코드 / 시나리오)
- **See also** — 본 코스 내 관련 챕터 링크

---

## 용어 (Terms)

> 본 토픽의 글로서리는 점진적으로 보강됩니다. 본문 챕터 내 강조된 용어들이 우선 등재됩니다.

"""


# ============================================================
# Quiz skeleton
# ============================================================

def make_quiz_index(site_name: str, chapters: list[dict]) -> str:
    out = [f"# {site_name} 퀴즈\n\n"]
    out.append(
        "각 챕터의 핵심 개념 이해도를 확인합니다. Bloom's Taxonomy 분포를 적용해 "
        "**암기/이해/적용/분석/평가** 수준의 문항이 섞여 있습니다.\n\n"
    )
    out.append("## 챕터별 퀴즈\n\n")
    for i, c in enumerate(chapters, 1):
        # Quiz file uses chapter number from filename, fallback to index
        quiz_name = c.get("quiz_filename", f"{i:02d}_quiz.md")
        out.append(f"- **Module {i:02d}** — [{c['title']}]({quiz_name})\n")
    out.append("\n## 사용법\n\n")
    out.append(
        "1. 챕터 본문을 학습한 후 해당 모듈의 퀴즈 페이지로 이동\n"
        "2. 정답을 머릿속으로 정한 뒤 **\"정답 / 해설\"** 영역을 펼쳐 확인\n"
        "3. 틀린 문항은 본문 해당 절을 다시 학습\n"
    )
    return "".join(out)


def make_quiz_placeholder(chapter_title: str, chapter_filename: str) -> str:
    return f"""# Quiz: {chapter_title}

!!! info "준비 중"
    이 챕터의 퀴즈는 콘텐츠 보강 단계에서 추가됩니다. 우선은 본문의 핵심 개념을 직접 정리해보는 방식으로 학습 효과를 점검하세요.

---

## 자가 점검 질문 (Self-Check)

본문을 학습한 후 다음 질문에 직접 답해보세요:

1. 이 챕터의 한 줄 핵심 메시지를 적어보세요.
2. 본문에서 가장 중요하다고 느낀 다이어그램/표 하나를 선택하고, 그것이 왜 중요한지 한 문단으로 설명해보세요.
3. 본문에서 다룬 패턴/메커니즘 중 하나를 골라, 실무에서 적용할 수 있는 시나리오를 하나 떠올려 보세요.

??? tip "학습 효과를 높이려면"
    - 답을 적은 후 본문과 비교해 보강할 부분 찾기
    - 암기보다 **이유**를 설명할 수 있는지 확인
    - 동료에게 5분 안에 설명할 수 있는지 시뮬레이션

---

[← 챕터 본문으로 돌아가기](../{chapter_filename})
"""


# ============================================================
# mkdocs.yml v2
# ============================================================

def make_mkdocs_yml(slug: str, site_name: str, site_desc: str, nav_entries: list[tuple[str, str]],
                    has_legacy: bool, has_glossary: bool, has_quiz: bool) -> str:
    nav_yaml = ""
    nav_yaml += '  - "코스 홈": index.md\n'
    nav_yaml += '  - "학습 모듈":\n'
    for title, fname in nav_entries:
        if fname == "index.md" or fname == "_legacy_overview.md":
            continue
        nav_yaml += f'      - "{title}": {fname}\n'
    if has_legacy:
        nav_yaml += '  - "코스 개요": _legacy_overview.md\n'
    if has_glossary:
        nav_yaml += '  - "용어집": glossary.md\n'
    if has_quiz:
        nav_yaml += '  - "퀴즈":\n'
        nav_yaml += '      - "퀴즈 인덱스": quiz/index.md\n'

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
    - navigation.sections
    - navigation.top
    - navigation.indexes
    - navigation.footer
    - toc.follow
    - search.suggest
    - search.highlight
    - search.share
    - content.code.copy
    - content.code.annotate
    - content.tabs.link
    - content.tooltips
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

extra_css:
  - stylesheets/extra.css

plugins:
  - search:
      lang:
        - en
        - ko
  - tags

nav:
{nav_yaml}
markdown_extensions:
  - abbr
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


# ============================================================
# bigtech_algorithm: SV embedding
# ============================================================

def embed_sv_files(src_dir: Path, dst_docs: Path) -> None:
    for sv_file in sorted(src_dir.glob("*.sv")):
        stem = sv_file.stem
        md_target = dst_docs / f"{stem}_explained.md"
        if not md_target.exists():
            continue
        sv_content = sv_file.read_text(encoding="utf-8")
        appendix_marker = "## 부록: SystemVerilog 예제 코드"
        existing = md_target.read_text(encoding="utf-8")
        if appendix_marker in existing:
            continue  # already embedded (idempotent)
        appendix = (
            "\n\n---\n\n"
            f"{appendix_marker}\n\n"
            f"원본 파일: `{sv_file.name}`\n\n"
            "```systemverilog\n"
            f"{sv_content}\n"
            "```\n"
        )
        md_target.write_text(existing + appendix, encoding="utf-8")


# ============================================================
# Main per-topic build
# ============================================================

def build_topic(
    src_name: str, slug: str, site_name: str, site_desc: str,
    level: str, prereqs: str,
) -> None:
    src_dir = SRC / src_name
    if not src_dir.is_dir():
        print(f"!! source dir not found: {src_dir}")
        return

    dst_dir = DST / slug
    docs_dir = dst_dir / "docs"
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "stylesheets").mkdir(exist_ok=True)
    (docs_dir / "quiz").mkdir(exist_ok=True)

    # --- copy CSS ---
    shutil.copy2(TEMPLATES / "extra.css", docs_dir / "stylesheets" / "extra.css")

    # --- copy & rename source MDs ---
    md_sources = sorted(p for p in src_dir.glob("*.md") if not is_excluded(p.name))
    has_overview = False
    chapter_files: list[Path] = []  # ordered chapter paths in docs/

    for md in md_sources:
        if md.name.startswith("00_overview"):
            target = docs_dir / "_legacy_overview.md"
            shutil.copy2(md, target)
            has_overview = True
        else:
            target = docs_dir / md.name
            shutil.copy2(md, target)
            chapter_files.append(target)

    # bigtech_algorithm: 00_summary.md as overview alias
    if slug == "bigtech_algorithm" and not has_overview:
        # use 00_summary as legacy overview
        summary_path = docs_dir / "00_summary.md"
        if summary_path.exists():
            target = docs_dir / "_legacy_overview.md"
            shutil.move(str(summary_path), str(target))
            has_overview = True
            chapter_files = [c for c in chapter_files if c.name != "00_summary.md"]

    chapter_files.sort(key=lambda p: p.name)

    # --- embed SV files for bigtech_algorithm (BEFORE meta injection) ---
    if slug == "bigtech_algorithm":
        embed_sv_files(src_dir, docs_dir)

    # --- inject per-chapter meta + Next/Prev ---
    chapter_meta: list[dict] = []
    for cf in chapter_files:
        text = cf.read_text(encoding="utf-8")
        h1 = extract_h1(cf) or cf.stem
        time_min = estimate_reading_time(text)
        chapter_meta.append({
            "path": cf,
            "filename": cf.name,
            "title": h1,
            "card_title": normalize_title(h1),
            "time": time_min,
            "href": cf.name,
        })

    # Inject meta and nav
    for i, ch in enumerate(chapter_meta):
        text = ch["path"].read_text(encoding="utf-8")
        text = inject_chapter_meta(text, level)
        prev_ = None
        next_ = None
        if i > 0:
            p = chapter_meta[i - 1]
            prev_ = (p["card_title"], p["href"])
        if i < len(chapter_meta) - 1:
            n = chapter_meta[i + 1]
            next_ = (n["card_title"], n["href"])
        # First chapter prev → course home
        if i == 0:
            prev_ = ("코스 홈", "index.md")
        # Last chapter next → quiz index
        if i == len(chapter_meta) - 1:
            next_ = ("퀴즈로 이동", "quiz/index.md")
        text = append_chapter_nav(text, prev_, next_)
        ch["path"].write_text(text, encoding="utf-8")

    # --- generate course home (index.md) ---
    course_chapters = [
        {"title": ch["card_title"], "href": ch["href"]}
        for ch in chapter_meta
    ]
    index_md = make_course_home(
        site_name, site_desc, level, prereqs,
        course_chapters, has_overview,
    )
    (docs_dir / "index.md").write_text(index_md, encoding="utf-8")

    # --- glossary skeleton ---
    glossary_md = make_glossary_skeleton(site_name, slug)
    (docs_dir / "glossary.md").write_text(glossary_md, encoding="utf-8")

    # --- quiz index + per-chapter placeholder ---
    quiz_chapters = []
    for ch in chapter_meta:
        # 01_foo.md → quiz/01_foo_quiz.md
        stem = Path(ch["filename"]).stem
        quiz_filename = f"{stem}_quiz.md"
        quiz_chapters.append({**ch, "quiz_filename": quiz_filename})

    (docs_dir / "quiz" / "index.md").write_text(
        make_quiz_index(site_name, quiz_chapters), encoding="utf-8"
    )
    for ch in quiz_chapters:
        (docs_dir / "quiz" / ch["quiz_filename"]).write_text(
            make_quiz_placeholder(ch["card_title"], ch["filename"]), encoding="utf-8"
        )

    # --- nav entries for mkdocs.yml ---
    nav_entries: list[tuple[str, str]] = []
    for ch in chapter_meta:
        nav_entries.append((ch["title"], ch["filename"]))

    yml = make_mkdocs_yml(
        slug, site_name, site_desc, nav_entries,
        has_legacy=has_overview, has_glossary=True, has_quiz=True,
    )
    (dst_dir / "mkdocs.yml").write_text(yml, encoding="utf-8")

    print(f"==> {slug}: {len(chapter_meta)} chapters, "
          f"{sum(c['time'] for c in chapter_meta)}m total")


def main() -> None:
    # Topics with hand-crafted deep enhancement — never regenerate.
    SKIP = {"uvm", "amba_protocols", "formal_verification", "mmu", "dram_ddr", "ufs_hci", "ethernet_dcmac", "toe", "soc_integration_cctv", "soc_secure_boot", "arm_security", "virtualization", "automotive_cybersecurity", "ai_engineering"}

    DST.mkdir(parents=True, exist_ok=True)
    for src_name, slug, site_name, site_desc, level, prereqs in TOPICS:
        if slug in SKIP:
            print(f"\n--- Skipping {slug} (hand-crafted, preserved) ---")
            continue
        print(f"\n--- Building {slug} ({src_name}) ---")
        build_topic(src_name, slug, site_name, site_desc, level, prereqs)
    print("\nAll topics built (Phase A structural).")


if __name__ == "__main__":
    main()
