# Curriculum Chapter Template v1 (LOCKED — pilot 승인됨)

**Use this template for every chapter rewrite in DV-SKOOL.**
Pilot exemplars: `topics/rdma/docs/01_rdma_motivation.md`, `topics/rdma/docs/02_ib_protocol_stack.md`.

## 머리말 (변경 금지)

```markdown
# Module NN — <Title>

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="<category>">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon"><emoji>(기존 그대로)</emoji></span>
    <span class="chapter-back-text"><Topic Display Name></span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module NN</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-...">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-...">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-...">3. 작은 예</a>
  <a class="page-toc-link" href="#4-일반화-...">4. 일반화</a>
  <a class="page-toc-link" href="#5-디테일-...">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + 디버그</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **<Bloom verb>** ...
    - **<Bloom verb>** ...
    - **<Bloom verb>** ...
    - **<Bloom verb>** ...
    (3~5개. Bloom verb 강제: define/explain/distinguish/identify/trace/apply/decompose/justify/compare/design/evaluate)

!!! info "사전 지식"
    - 이전 모듈 링크
    - 도메인 prerequisite
```

## 본문 7단계 (필수)

### 1. Why care? — 이 모듈이 왜 필요한가
- 3~5줄.
- "이걸 모르면 무엇이 안 풀리는지" + "이후 어디에 다시 쓰이는지" 명시.
- 추상적 "중요하다" 금지 — 구체적 결과로 진술.

### 2. Intuition — 비유와 한 장 그림
- `!!! tip "💡 한 줄 비유"` admonition 1개.
- 비유는 일상/엔지니어링 (mailbox, 우편물, 도서관, 책상, 사서 ...).
- ASCII 또는 Mermaid 다이어그램 1장 — 전체 구조 한 눈에.
- "왜 이렇게 설계됐는가" 한 단락 (design rationale). 표로 도망가지 않기.

### 3. 작은 예 — Worked Example
- 가장 단순한 시나리오 1개를 step-by-step.
- ASCII 그림 + step 표 (id / 누가 / 무엇을 / 왜) + 필요 시 코드.
- 마지막에 `!!! note "여기서 잡아야 할 두 가지"` — 핵심 takeaway 2~3개.
- 디버그 챕터의 경우: worked example = "실제 fail log → root cause → fix" 의 1 cycle.

### 4. 일반화 — 개념 정형화
- §3 의 작은 예에서 추출한 개념을 일반화.
- 변형/edge case 의 분기 설명.
- (필요 시) FSM 또는 시퀀스 다이어그램.
- (필요 시) 객체/엔티티 관계 다이어그램.

### 5. 디테일 — 표, 필드, 규칙, 코드, Confluence 보강
- 기존 본문의 모든 표/spec 인용/Confluence admonition 을 **삭제 없이** §5 의 sub-section 으로 이전.
- 사내 정책/Confluence 보강은 `!!! note "Internal (Confluence: <title>, id=<id>)"` 형식 보존.
- 비트맵/필드 ASCII 그림 보존.
- 코드 예시 (SystemVerilog/UVM/C/Python) 보존.

### 6. 흔한 오해 와 DV 디버그 체크리스트
- **흔한 오해**: 3~5개. 각 오해는 `!!! danger "❓ 오해 N — '...'"` 으로.
  - 본문 형식: **실제** + **왜 헷갈리는가**.
- **DV 디버그 체크리스트**: 표 형식 (증상 / 1차 의심 / 어디 보나).
  - 챕터 내용으로 마주칠 첫 실패들을 6~8개.

### 7. 핵심 정리 (Key Takeaways) + 다음 모듈
- bullet 5개 이내 — 외워야 할 가장 중요한 사실만.
- `!!! warning "실무 주의점"` (선택) — pitfalls / gotchas.
- 다음 모듈 링크 + 퀴즈 링크.

## 푸터 (변경 금지)

```markdown
--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"   (해당 토픽에 있을 때만)
```

## 보강 정책 (필수 준수)

- **정보 보존**: 기존 표/spec 인용/Confluence admonition 한 줄도 누락 금지. 위치만 §5 로 이동.
- **약어**: 챕터 첫 등장 시 풀어 쓰기 (예: "LRH (Local Route Header)"). `abbreviations.md` 가 자동 hover 처리.
- **그림**: 기존 ASCII 보존 + §2 의 한 장 그림은 신규 작성 (또는 기존 그림 재구성).
- **분량**: 기존 대비 +30~50% 가 정상. 너무 길어지면 §5 의 표를 슬림화 (단, 정보 손실 금지).
- **언어**: 한국어 본문 + 코드/spec 인용/약어는 영어. 기존 admonition 제목 (`!!! quote "Spec 인용"` 등) 은 그대로.
- **퀴즈/glossary 미터치**: 본문만 손댐.

## 검증 체크리스트 (각 챕터 완료 후)

- [ ] 7단계 헤딩이 모두 있는가
- [ ] 각 단계의 형식이 위 명세대로인가
- [ ] 기존 본문의 모든 표/Confluence admonition/spec 인용이 살아 있는가 (diff 비교)
- [ ] §3 worked example 이 신규 작성됐는가
- [ ] §6 디버그 체크리스트가 신규 작성됐는가 (혹은 챕터 성격에 맞게 흔한 오해 5개로 대체)
- [ ] CH-CTX, CH-TOC 마커 보존
- [ ] 푸터 (`abbreviations.md`) 보존
- [ ] mkdocs strict build 통과 (그룹 단위 또는 토픽 단위)

## 챕터 성격별 §3, §6 변형 가이드

| 챕터 성격 | §3 worked example | §6 디버그 체크리스트 |
|---|---|---|
| **개념 / 동기 (motivation)** | 가장 단순한 1 사이클 추적 (예: 1 KB WRITE) | 초기 증상 6~8개 |
| **프로토콜 / 패킷 포맷** | 패킷 한 개의 1-hop 추적 (어떤 필드가 read/rewrite/preserve) | 헤더-필드 실패 패턴 |
| **TB 구조 / 컴포넌트** | 한 transaction 이 driver→DUT→monitor→scoreboard 흐르는 path | "이 에러가 어디서 나오는가" prefix 매핑 |
| **디버그 케이스** | 실제 fail log + waveform → root cause → fix 1 cycle | 같은 증상의 다른 원인 | (또는 "다음 디버그 케이스로 넘어가는 신호") |
| **레퍼런스 / quick card** | 표 1개로 자주 쓰는 시나리오 | "이 카드를 봐야 할 때" |
| **research / background** | 기존 자료에서 가장 흥미로운 finding 1개 deep-dive | (선택) "이 자료의 한계" |

## 비고
- 이 템플릿은 사용자 승인된 RDMA Module 01, 02 의 형식을 추출한 것.
- 변경 필요 시: 사용자 재승인 후 v2 로 업데이트.
