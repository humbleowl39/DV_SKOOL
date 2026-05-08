# Plan: Glossary Remediation (Phase 2 — C안: 공유 abbr + 5 토픽 정비)

## Objective
Phase 1 audit 결과를 기반으로:
1. **A: 사이트 공통 용어를 abbr 형식의 공유 파일로 정의** — 모든 토픽이 호버 툴팁으로 즉시 사용 가능
2. **B: 우선순위 상위 5 토픽(rdma / amba_protocols / pcie / soc_secure_boot / ufs_hci)** glossary 누락 항목 추가 + 본문 첫 등장 시 anchor 링크 자동 삽입

## Context (확인 완료)
- 각 토픽은 **독립 mkdocs site** (사이트 별 build, 토픽 간 cross-link 불가).
- 모든 토픽 mkdocs.yml 에 `abbr` + `pymdownx.snippets` 확장 **이미 활성화**.
- `abbr` 정의 (`*[BTH]: Base Transport Header`) 만 있으면 호버 툴팁 자동 작동.
- `snippets` 로 외부 파일 include 가능 — 단, 토픽이 독립이므로 **공유 파일을 각 토픽 docs/_inc/ 에 복제**하거나 **snippets base_path** 로 cross-topic 참조 필요. 후자가 단일 소스(SSOT) 유지 측면 우수.

## Strategy

### A. 공유 Abbr (사이트 공통 용어)
- **위치**: `topics/_shared/abbreviations.md` (mkdocs build 대상 외, 순수 abbr 정의 파일)
- **포함 후보**: DV, HW, SW, CPU, DMA, MMU, TB, DUT, UVM, AXI, IP, OS, GPU, DRAM, FPGA, HLS, NIC, ID, IO, IRQ, FSM, RAL, SVA, AI, VM, ACK, NAK, TX, RX, CRC, TCP, UDP, MTU, IB
- 약 30개. 각 항목 1 줄 abbr 정의 (`*[CPU]: Central Processing Unit`).
- **활성화 방식**: 각 토픽 mkdocs.yml 에 `pymdownx.snippets.base_path` 추가 → 챕터 본문 끝(또는 별도 hook)에서 `--8<-- "../../_shared/abbreviations.md"` 한 줄 include.
  - 또는 더 간단하게: **각 토픽 docs/_inc/abbreviations.md 에 복제**, mkdocs.yml `extra: ` 로 자동 append (혹은 챕터에서 1 줄 include).
  - 최종 방식은 PoC 후 결정. 1순위는 snippets base_path (DRY), 2순위는 복제.
- **호버 UX**: 본문 어디서든 `BTH`, `CPU` 등 등장 시 점선 밑줄 + 호버 툴팁.

### B. 토픽 정비 (우선순위 상위 5)

토픽 순서: **rdma → pcie → amba_protocols → soc_secure_boot → ufs_hci**

각 토픽에 대해:
1. **MISSING vetting** (반자동)
   - per_topic 리포트의 MISSING 목록을 frequency 기준 정렬
   - 자동 분류:
     - **Auto-keep**: freq ≥ 5 AND 토큰 길이 ≥ 3 AND 영어 일반어 stopword 미포함 → 추가 후보
     - **Auto-drop**: 영어 일반어(APPLICABLE, FIRST, LAST 같은 RDMA 옵코드 후보 제외 룰), 1글자 + 숫자
     - **Manual review**: 그 외
   - 사용자에게 vetting 표 제시 → 승인된 항목만 glossary 추가
2. **Glossary 항목 작성** (ISO 11179 형식)
   - 자동 생성 시도: 본문 첫 등장 위치의 문맥(주변 50자)에서 정의 후보 추출
   - 추정 항목은 `**Source.** (추론, 검증 필요)` 표기
   - 확실한 spec 인용 가능 항목은 spec 명 (IBTA / IB Spec 1.7 / PCIe Base 6.0 / ARM IHI / IEEE 802.3 등) 자동 입력
3. **본문 첫 등장 시 anchor 링크 삽입**
   - 챕터 파일 순서대로(`01_*.md`, `02_*.md`, ...) 스캔
   - 약어가 첫 등장하는 위치(코드 블록·주석·이미 링크 안 제외)에서 `BTH` → `[BTH](../glossary.md#bth)` 변환
   - 같은 챕터 내 두 번째 등장부터는 abbr 툴팁만 작동 (링크 도배 방지)
4. **mkdocs build --strict** 통과 검증
5. **한글 glossary 동기화** — 정의 본문은 이미 한글로 작성되어 있음. 신규 추가 항목도 동일 정책.

## Steps

### A. 공유 abbr 셋업
- [ ] A1. `topics/_shared/abbreviations.md` 생성 (30개 공통 약어 abbr 정의)
- [ ] A2. PoC: rdma 토픽에서 snippets base_path 로 include 시도
  - mkdocs.yml `markdown_extensions:` 의 `pymdownx.snippets` 에 `base_path` 옵션 추가
  - 챕터 1개에 `--8<-- "abbreviations.md"` include
  - `mkdocs build --strict` 통과 확인
- [ ] A3. PoC 성공 시: 17개 나머지 토픽 mkdocs.yml 일괄 업데이트
- [ ] A4. (대체안) PoC 실패 시: 각 토픽 docs/_inc/abbreviations.md 로 복제하는 방식으로 전환

### B. 토픽별 정비 (1 토픽씩 batch)

**B-rdma** (가장 신호 강함, RDMA 신규 챕터 동기화 포함):
- [ ] B-rdma-1. MISSING 271건 자동 분류 → vetting 표 산출
- [ ] B-rdma-2. 사용자 승인 받기 (한 번에 batch)
- [ ] B-rdma-3. 승인 항목 glossary.md 에 ISO 11179 형식으로 추가
- [ ] B-rdma-4. 본문 첫 등장 위치에 anchor 링크 자동 삽입
- [ ] B-rdma-5. `mkdocs build --strict` 통과
- [ ] B-rdma-6. 신규 챕터(10~13) 누락 spot-check

**B-pcie / B-amba_protocols / B-soc_secure_boot / B-ufs_hci** — 동일 절차 반복

### C. 마무리
- [ ] C1. SUMMARY 업데이트 — 각 토픽 정비 전후 카운트 비교
- [ ] C2. Phase 1 plan MD에 Phase 2 deviation 기록
- [ ] C3. 사용자에게 최종 리포트 + 6개 미정비 토픽 후속 작업 권고

## Success Criteria
- A: 5 토픽에서 공유 abbr 활성화 확인 (호버 툴팁 동작), `mkdocs build --strict` 통과
- B: 우선순위 5 토픽의 MISSING(HIGH) 카운트가 vetting 후 0 또는 사용자 명시 잔여 — 각 토픽 strict build 통과
- 본문에서 신규 anchor 링크 삽입 건수 보고
- 자동 처리에 의한 본문 의미 손상 없음 (코드 블록 / 주석 / 기존 링크 보호)

## Risks / Open Questions

1. **snippets base_path cross-topic 참조** — mkdocs-material 의 snippets 동작이 절대 경로/상위 디렉토리 허용하는지 PoC 필요. 안되면 복제로 전환.
2. **본문 자동 patch 안전성** — 코드 블록·테이블·이미 링크된 곳 보호 필수. 마크다운 파서 기반 변환이 regex보다 안전하나 의존성 추가됨. 1차는 보수적 regex (코드 블록·기존 [text](url) 형식 제외) + 사용자 spot-check.
3. **첫 등장 정의 — false definition 리스크** — 본문 컨텍스트로 추정한 정의가 잘못될 수 있음. 추정 항목은 명시적으로 표시(`**(추론)**`)해 사용자가 검수 시 인지 가능하도록.
4. **약어 충돌** — 같은 약어가 토픽마다 다른 의미일 수 있음 (예: `CC` = Congestion Control vs Cache Coherency vs ...). 토픽별 glossary 가 우선, 공유 abbr 는 가장 보편적 의미만.
5. **호버 툴팁이 너무 많으면 시각적 노이즈** — abbr 활성화 후 첫 챕터 1개로 UX 검증 필요.

## Deferred (out of Phase 2 scope)
- ORPHAN 항목 검토 / 정리 (UVM 22/24, rdma_verification 27/32) — 별도 작업
- 6 우선순위 외 토픽 (mmu, virtualization, automotive_cyber, arm_security, toe, dram_ddr, ethernet_dcmac, ai_eng, soc_cctv, formal_verif, uvm, rdma_verification, bigtech_algo)
- abbr 외 advanced 기능 (예: `tooltip:` annotation, content.tooltips 의 inline tooltip)

## Execution Order Recommendation
A1-A4 (공유 abbr 셋업) → B-rdma (가장 큰 신호 + 사용자 최초 지적 토픽) → B-pcie → 나머지 3 토픽
