# Plan: 전체 학습 자료 본문 재구성 — "쉽게 + 깊이 있게"

## Objective
DV-SKOOL 의 19개 토픽 / ~134개 챕터 전부의 본문을 **고정된 7단계 학습 흐름**으로 재구성하고, 동시에 내용 깊이를 보강한다. 정보 손실 0, 가독성과 직관 대폭 강화.

## Context
- 현재 토픽 트리: `topics/<topic>/docs/NN_*.md` (각 토픽이 독립 mkdocs 사이트)
- 챕터 수 (총 134):
  - RDMA(13), RDMA DV(12), virtualization(9), pcie(9), ai_engineering(8),
    uvm(7), soc_secure_boot(7), mmu(7), bigtech_algorithm(7),
    ufs_hci(5), toe(5), dram_ddr(5), automotive_cybersecurity(5), arm_security(5),
    soc_integration_cctv(4), formal_verification(4), ethernet_dcmac(4), amba_protocols(4)
- 진단된 문제점 (RDMA Module 02, RDMA-DV Module 02 sample 분석):
  - 표 위주 서술 → 빠른 reference 는 좋지만 **첫 학습** 에는 abrupt
  - 약어 폭격 (LRH/GRH/BTH/xTH/ICRC/VCRC...) — gradual scaffolding 부족
  - 비유/오해/핵심정리 admonition 은 이미 있음 — 그러나 **본문 흐름** 자체가 detail-first
  - "왜 이 설계가 이렇게 됐는가" (rationale) 가 표 각주에 묻혀 있음
  - 작은 worked example 부족 — 한 패킷/한 트랜잭션의 step-by-step trace 없음

## Target 챕터 구조 (고정 템플릿 v1)

```markdown
# Module NN — <Title>

<chapter context + page TOC>  ← 기존 인프라 그대로 유지

!!! objective "학습 목표"
    Bloom verb 4개 (기존)

!!! info "사전 지식"
    (기존)

## 1. Why care? — 이 모듈이 왜 필요한가
- 한 문단(3~5줄)으로 "이걸 모르면 무엇이 안 풀리는지"
- 이전 모듈과의 연결 (학습 흐름)

## 2. Intuition — 비유와 한 장 그림
- 일상 / 엔지니어링 비유 (mailbox, 우편물, 도서관 ...)
- ASCII 또는 Mermaid 다이어그램 1장 (전체 구조 한 눈에)
- "왜 이렇게 생겼는가" — design rationale 한 단락

## 3. 작은 예 1개 — Worked Example
- 가장 단순한 시나리오 1개를 step-by-step 로 추적
- 각 step 옆에 "지금 일어나는 일" 한 줄 주석
- 코드/패킷/시그널 등 구체 artifact 표시

## 4. 일반화 — 개념 정형화
- 작은 예에서 추출한 개념을 일반화
- 변형/edge case 의 분기 설명
- (필요 시) FSM/시퀀스 다이어그램

## 5. 디테일 — 표/필드/규칙
- 모든 헤더/필드/리소스/메서드 표 (기존 detail 보존)
- spec 인용은 기존대로 admonition 으로
- Confluence 보강 섹션 그대로 유지

## 6. 흔한 오해 / 디버그 체크리스트
- "오해 → 실제 → 왜 헷갈리는가" 3단 구조 (기존 형식 확장)
- DV 관점 디버그 체크리스트 (이 챕터 내용으로 마주칠 실패 패턴)

## 7. 핵심 정리 + 다음 모듈
- 5개 이내 bullet — 외워야 할 가장 중요한 사실만
- 다음 모듈 링크 + 퀴즈 링크
```

### 보강 정책
- **정보 보존**: 기존 표/spec 인용/Confluence 보강 그 어떤 것도 삭제 금지. §5 로 이전.
- **내용 추가**: §3 worked example 은 거의 모든 챕터에 신규로 작성. §6 의 디버그 체크리스트도 신규.
- **그림 추가**: 기존 ASCII 보존 + Mermaid 1장 추가 (§2 또는 §4)
- **약어**: 챕터 첫 등장 시 풀어 쓰기 + abbreviations.md 활용 (이미 인프라 존재)

## 단계별 진행

### Phase 0 — Pilot (사용자 승인 후 즉시 착수)
- 대상: RDMA Module 01, 02 두 챕터만
- 산출: 7단계 템플릿 적용 결과 + worked example + Mermaid
- 게이트: **사용자 리뷰 → 템플릿 확정**. 여기서 톤/길이/depth 가 OK 사인 받기 전에는 다른 챕터로 안 넘어감.
- 예상 산출물 길이: 챕터당 기존 대비 +30~50% (worked example + 디버그 체크리스트 추가분)

### Phase 1 — RDMA (13 챕터)
- 순서: 01(Pilot) → 02(Pilot) → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11 → 12 → 13
- 마일스톤: 5/13 마다 사용자 중간 리뷰
- mkdocs strict build 통과 확인

### Phase 2 — RDMA DV (12 챕터)
- 순서: 01 → 02 → 03 → 04 → 05 → 06 → 07 (debug case 시작) → 08 → 09 → 10 → 11 → 12
- 디버그 케이스 챕터 (07~11): worked example = "실제 fail log → root cause → fix" 흐름. 기존 자료가 이미 디버그 케이스 형식이라 §3/§6 정렬이 자연스러움.

### Phase 3 — 나머지 17 토픽 (109 챕터)
- 우선순위 그룹:
  - **A** (DV core, 31): uvm(7), formal_verification(4), amba_protocols(4), pcie(9), mmu(7)
  - **B** (Network/Storage, 19): ethernet_dcmac(4), toe(5), ufs_hci(5), dram_ddr(5)
  - **C** (Security/SoC, 25): soc_secure_boot(7), arm_security(5), automotive_cybersecurity(5), soc_integration_cctv(4), virtualization(9 — 일부)
  - **D** (Specialty, 34): virtualization(나머지), ai_engineering(8), bigtech_algorithm(7)
- 그룹 단위로 진행, 그룹 끝마다 mkdocs strict build + 사용자 리뷰

## Steps
- [x] Step 0 — Pilot 2챕터 (RDMA 01, 02) 재작성 → 사용자 승인 ✓
- [x] Step 1 — RDMA Module 03~13 재작성 (직접) ✓
- [x] Step 2 — RDMA DV Module 01~12 재작성 (sub-agent) ✓
- [x] Step 3 — 그룹 A (uvm + formal + amba + pcie + mmu) 재작성 (sub-agent) ✓
- [x] Step 4 — 그룹 B (ethernet_dcmac + toe + ufs_hci + dram_ddr) 재작성 (sub-agent) ✓
- [x] Step 5 — 그룹 C (security/SoC) 재작성 (sub-agent) ✓
- [x] Step 6 — 그룹 D (specialty) 재작성 (sub-agent) ✓
- [x] Step 7 — 전 토픽 mkdocs strict build ✓ (18/18 PASS)

## 최종 결과 (2026-05-10 close-out)

- **134 / 134 챕터** 모두 7-step 템플릿 적용 완료.
- **18 / 18 토픽** `mkdocs build --strict` PASS (0 error, 0 warning).
- 정보 손실 0 — 모든 기존 표 / spec 인용 / Confluence Internal admonition / ASCII 다이어그램 / 코드 블록 보존, §5 로 재배치.
- 신규 작성: §3 worked example (134 개) + §6 디버그 체크리스트 + 흔한 오해 (chapter 당 3~5 개).
- 분량 증가: 평균 +30~50%.

### 진행 모드 분담

- 사용자 직접 (foreground): RDMA 13 챕터 (pilot 2 + 본문 11).
- Sub-agent (background, edu-author): RDMA-DV 12 + 다른 16 토픽 109 챕터.
- Usage-cap 으로 한 차례 중단 후 재개 — 22 챕터 재위임 (rdma_verification 3, pcie 3, virtualization 4, ai_engineering 2, soc_secure_boot 2, mmu 1, dram_ddr 1, + 직접 RDMA 6).

### Deviations from original plan

- 원안의 중간 리뷰 (5/13) 는 pilot 1회 만 실시. 이후 사용자가 "전부 다 진행해" 로 가속 결정 → 전 챕터 일괄 진행.
- Open-Q 2/3 (Conflu 동기화, 영문 mirror) 는 본 phase 에서 미실시 — 별도 phase 권장.

### Open-Q 후속

- 영문 mirror (`*_ko.md` ↔ `*.md`) 는 별도 phase 필요.
- Conflu 동기화도 별도 phase.
- 신규 챕터의 퀴즈 갱신 (§3 worked example + §6 디버그 체크리스트 반영) 도 follow-up.

## Success Criteria
- 모든 챕터가 7단계 템플릿을 따름
- 기존 표/spec 인용/Confluence 보강 정보가 한 줄도 누락되지 않음 (diff 검토)
- 챕터당 worked example 1개 이상 + 디버그 체크리스트 또는 흔한 오해 1개 이상
- 모든 토픽 `mkdocs build --strict` 통과
- 사용자가 "이제 이해된다" 라고 confirm

## Risks / Open Questions
- **Risk-1 (스케일)**: 134 챕터 × 챕터당 30~60분 작업 → 매우 큰 분량. 한 세션에 전부 처리 불가 → 명시적 단계 + 중간 게이트 필수.
- **Risk-2 (드리프트)**: 후반 챕터로 갈수록 템플릿이 흔들릴 수 있음 → Pilot 결과를 `template_v1.md` 로 저장 + 매 챕터 작성 전 참조.
- **Risk-3 (검증 지연)**: mkdocs strict 가 배치 끝에만 돌아감 → 그룹 단위 build 로 잡기.
- **Open-Q (사용자 결정)**:
  1. Pilot 결과를 보고 템플릿 미세 조정 → 그 후 자동 진행 OK?
  2. 토픽별 진행 후 (1) Conflu/Jira 동기화 같이 할지, (2) 본문만 먼저 갈지?
  3. 영문 mirror (`*_ko.md` ↔ 영문 원본) 유지: 일단 보류 (현재는 한국어 본문만 정비, 영문 mirror 는 별도 phase)?

## Notes
- 기존 `<!-- DV-SKOOL-CH-CTX -->`, `<!-- DV-SKOOL-CH-TOC -->`, `--8<-- "abbreviations.md"` 등 인프라 마커는 모두 보존.
- 글로서리/퀴즈/스타일시트 미터치.
- 변경은 `git` 추적되므로, Phase 끝마다 commit (사용자 승인 후).
