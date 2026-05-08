# Plan: RDMA 학습 자료 Confluence-기반 업데이트

## Objective
DV_SKOOL `topics/rdma/` 의 9개 모듈 + glossary + quiz 를, Confluence space `RT` (RDMA Team Home, root id=7012616) 의 24개 top-level 페이지 + 그 하위 트리 내용으로 **보강(augment)** 하고, Confluence-only 주제는 **신규 모듈(M10+)** 로 추가한다. 내부 결정/구현 정보는 admonition 으로 명시하고 출처(페이지 제목)를 단다.

## Source
- Root: Confluence space `RT` page id=7012616 (RDMA Team Home)
- 24 top-level children:
  - Welcome!, Latest GPUBoost Specification, FPGA Prototyping 101,
  - RDMA protocol details, RDMA Supporting materials, RDMA IP architecture,
  - Other materials, Congestion Control (CC), AI Servers,
  - Infiniband Spec Comparison v1.7 w v1.4, Verification, Manual,
  - Ultraethernet, Paper Study, On-going issue tracking, Fifo optimization,
  - 흩어져 있는 정보 정리, Debug register 정리, [SKRP-371] module list,
  - Coverage define, 11/10 TODO, RDMA for NRT, Bitfile status, 2026 Q2 Action items
- 모든 sub-tree 포함 (사용자 결정)

## Target
- `topics/rdma/docs/01..09_*.md` — 보강
- `topics/rdma/docs/glossary.md` — 내부 용어/약어 추가
- `topics/rdma/docs/quiz/*.md` — 신규 항목 추가
- `topics/rdma/docs/` 하에 신규 모듈 (필요 시):
  - `M10` Ultraethernet (UEC) 비교
  - `M11` GPUBoost / RDMA-IP 아키텍처 (HW 관점)
  - `M12` FPGA Prototyping & Manual (실무 운영)
- `topics/rdma/mkdocs.yml` — nav 갱신
- `landing/index.html` — 카드 설명 보강 (선택)

## Work Directory
`20260507_180000_rdma_topic_CONFLUENCE_UPDATE/`
- `tree.json` — 페이지 트리 (id, title, parent)
- `pages/<id>.md` — 페이지 본문 (HTML→markdown)
- `mapping.md` — 페이지 → 모듈 매핑 표
- `coverage.md` — 어떤 페이지가 어디에 반영되었는지 추적

## Steps
- [x] S1 — 24개 top-level + 전 sub-tree 크롤 → `tree.json` (127 페이지)
- [x] S2 — 모든 페이지 본문 fetch & markdown 변환 → `pages/<id>.md` (127 파일, ~904 KB)
- [x] S3 — 페이지 → 모듈 매핑표 작성 (`mapping.md`)
- [x] S4 — M01..M09 보강: 9 모듈에 Internal note admonition + 신규 절 추가
- [x] S5 — glossary.md Appendix A/B/C 추가 (30+ 신규 용어)
- [x] S6 — 신규 모듈 M10 (UEC), M11 (GPUBoost/RDMA-IP), M12 (FPGA Proto/Manuals), M13 (Background) 작성
- [x] S7 — quiz 4 신규 + 5 보강 (M02, M07, M08)
- [x] S8 — `mkdocs.yml` nav · index.md · landing card 모두 갱신 (9→13 챕터)
- [x] S9 — `mkdocs build --strict` PASS (1.18 s, exit 0)
- [x] S10 — `CHANGE_REPORT.md` 작성

## Quality Gates
- 내부 정보는 반드시 `!!! note "Internal (Confluence: <page title>)"` 안에 둠
- 모든 신규 학습 목표는 Bloom 동사로 시작
- 모든 사실 주장은 IB Spec C-rule 또는 Confluence 페이지 제목/id 인용
- glossary 신규 항목은 ISO 11179 (정의=한 문장, 예시 분리)
- Mermaid 라벨 영어, 캡션 한국어 + 영어 가능
- mkdocs build 통과 (가능 한 경우)

## Risks
- 페이지 수 폭증 시 토큰 비용 — 본문은 로컬 파일로 캐싱하고 grep/Read 로 처리
- HTML→텍스트 변환 시 표/이미지 손실 — 표는 별도 파싱 시도, 이미지는 메타만 기록
- 한국어 페이지 제목 "흩어져 있는 정보 정리" 등 정리되지 않은 노트는 발췌 후 적절 모듈에 흡수
- 운영성 페이지(TODO, Action items, Bitfile status, On-going issue) 는 학습 자료에 부적합 → S2 단계에서 본문은 fetch 하되 매핑 단계에서 제외 처리

## Execution Order
S1 → S2(병렬 가능, 일괄 스크립트) → S3(사람 판단) → S4..S6(보강/신규) → S7(quiz) → S8(nav) → S9(build) → S10(report)
