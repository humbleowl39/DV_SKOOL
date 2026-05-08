# Plan: 전 토픽 학습자료 용어집 점검 및 정비

## Objective
DV_SKOOL/topics/* 18개 학습자료의 glossary 상태를 점검해 (1) 본문↔용어집 동기화 누락, (2) 본문 cross-link 부재, (3) MkDocs Material 약어 툴팁 미설정을 일괄적으로 식별·정비한다.

작업은 **2-phase**: 먼저 전 토픽 누락 리포트(read-only)만 산출 → 사용자 검토 → 정비 일괄 적용.

## Context
- 대상 토픽 (18): ai_engineering, amba_protocols, arm_security, automotive_cybersecurity, bigtech_algorithm, dram_ddr, ethernet_dcmac, formal_verification, mmu, pcie, rdma, rdma_verification, soc_integration_cctv, soc_secure_boot, toe, ufs_hci, uvm, virtualization
- 모든 토픽: `topics/<id>/docs/glossary.md` 존재. ISO 11179 형식 (Definition / Source / Related / Example / See also).
- 항목 수 격차 큼: rdma=70, pcie=43 / amba_protocols=9, toe=9, ethernet_dcmac=10.
- **본문→glossary 링크 거의 0** (RDMA, PCIe 모든 챕터에서 grep "glossary" 결과 0~1).
- RDMA는 최근 챕터 10~13 신규(UltraEthernet, GpuBoost, FPGA Proto, Background research) — glossary 동기화 미확인.
- mkdocs.yml에 `pymdownx.snippets`/`abbr` 마크다운 확장 적용 여부 토픽별로 상이.

## Phase 1 — Audit (read-only, 산출물: 리포트)

출력 디렉토리: `20260508_135724_dvskool_GLOSSARY_AUDIT/`
파일 구조:
```
GLOSSARY_AUDIT/
├── SUMMARY.md            # 18 토픽 한눈 표 (우선순위 산정)
├── SUMMARY_ko.md         # 한글 버전
├── per_topic/
│   ├── rdma.md           # 누락 용어 + 본문 등장 위치 (file:line)
│   ├── pcie.md
│   └── ... (18개)
└── data/
    └── extraction.tsv    # 원시 데이터 (raw extraction)
```

### Step 1: 본문 용어 후보 추출 (per topic)
- 정규식: 대문자 약어 (`\b[A-Z]{2,}[0-9]?\b`), 괄호 약어 (`(XYZ)` 패턴), 백틱 인라인 코드, **bold** 표시 용어
- 노이즈 제거: 일반 대문자(I, A, OK, NO, TBD 등 stopword), 코드 블록 내부 식별자
- 출력: `<term, frequency, first_appearance: chapter:line>` 튜플

### Step 2: glossary 항목 파싱
- `### <Term>` 헤더 추출
- 헤더 명에서 약어 / full name 분리 (예: "BTH (Base Transport Header)" → 약어 "BTH", 전체 "Base Transport Header")

### Step 3: 차집합 → 누락 용어 식별
- 본문 등장 ∧ ¬glossary 존재 = 누락 (priority: HIGH)
- glossary 존재 ∧ ¬본문 등장 = 사장(死藏) 항목 (priority: LOW, 검토 권고만)
- 본문 등장 ∧ glossary 존재 ∧ 본문에 anchor 링크 부재 = 링크 미설정 (priority: MED)

### Step 4: SUMMARY 표 생성
| Topic | Glossary 항목 | 본문 약어 종류 | 누락 (HIGH) | 링크 미설정 (MED) | 사장 항목 | 우선순위 |
| ... |

### Step 5: 토픽별 상세 리포트 (per_topic/<id>.md)
- 누락 용어 → 본문 등장 위치 + 추정 정의(IBTA/spec 단서가 본문에 있다면)
- 링크 미설정 용어 → 첫 등장 위치 (자동 patch 후보)
- mkdocs.yml의 abbr 확장 활성화 여부

### Step 6: 한글 버전(`*_ko.md`)
- `language.md` 규칙에 따라 SUMMARY는 영/한 양쪽

## Phase 2 — Remediation (Phase 1 검토 후 별도 승인)

Phase 1 SUMMARY 검토 → 사용자 승인 → 다음을 일괄 적용:
1. 누락 용어 → glossary.md 신규 항목 추가 (ISO 11179 형식, Source 인용 포함)
2. 본문 첫 등장 시 `[BTH](glossary.md#bth)` 형식 inline 링크 자동 삽입
3. (선택) MkDocs abbr 확장 활성화 + `docs/_glossary_abbr.md` 생성 → 호버 툴팁 UX
4. 토픽별 `mkdocs build --strict` 통과 검증
5. 한글 버전 `glossary 색인_ko` 동기화

Phase 2는 토픽 수가 많으므로 우선순위 상위(누락 HIGH > 5건)부터 batch 처리 권장.

## Steps (Phase 1 실행)

- [ ] Step 1: 출력 디렉토리 생성, 추출 스크립트 작성 (Python)
- [ ] Step 2: 18 토픽 본문 용어 후보 추출 (대문자 약어 + 괄호 약어)
- [ ] Step 3: 18 토픽 glossary 파싱
- [ ] Step 4: 차집합 계산 → 토픽별 누락/링크미설정/사장 분류
- [ ] Step 5: SUMMARY.md 표 + 우선순위 산출
- [ ] Step 6: 토픽별 per_topic/<id>.md 작성 (누락 용어 + 등장 위치)
- [ ] Step 7: SUMMARY_ko.md 생성
- [ ] Step 8: 사용자 검토 요청 → Phase 2 승인 시 별도 plan으로 분리

## Success Criteria

Phase 1:
- SUMMARY.md에서 18 토픽 모두에 대한 (누락/링크미설정/사장) 카운트가 표로 출력
- per_topic/<id>.md에서 각 누락 용어가 `<term> @ <chapter>:<line>` 형식으로 위치 명시
- 외부 spec 인용 가능한 용어는 추정 Source(IBTA, IEEE 1800, ARM IHI 등) 후보 표기
- 한글 버전 동봉

Phase 2 (별도 plan에서 정의):
- glossary 누락 HIGH = 0
- 본문→glossary 링크 신규 삽입 건수 보고
- 모든 정비 토픽 `mkdocs build --strict` 통과

## Risks / Open Questions

1. **대문자 약어 추출 노이즈** — `OK`, `TBD`, `I/O`, `UI`, 식별자 등 false positive 다수 예상. stopword 리스트로 1차 필터, 사용자 검토에서 추가 정제.
2. **신규 용어의 정의 문장 추정** — Phase 2에서 spec 인용/추론을 명시. 추론 항목은 `**(추론)**` 표기.
3. **링크 자동 삽입 시 코드 블록·테이블 내부 처리** — Phase 2에서 마크다운 파서 기반 안전 변환 (raw regex 회피).
4. **abbr 툴팁 UX 충돌** — 일부 토픽은 abbr 미사용이 일관됨. 토픽별 옵션으로 결정.
5. **rdma_verification glossary 32개 중 일부 미완성** — 정의 문장 결측 점검 포함 (Phase 1 step 3에서 별도 플래그).

## Execution Notes

- Phase 1은 read-only — 원본 토픽 파일 수정 없음.
- 추출 스크립트는 `data/` 산출 후 폐기 가능 (재현성 위해 스크립트는 출력 디렉토리에 보존).
- 리포트 산출 후 사용자에게 우선순위 상위 3-5개 토픽 추천하여 Phase 2 batch 진입.

## Outcome (2026-05-08)

- Phase 1 완료: 18 토픽 audit 산출 (`SUMMARY.md`, `per_topic/`, `data/extraction.json`).
- Phase 2 plan: `20260508_150810_glossary_remediation_PLAN.md` (C안: 공유 abbr + 5 토픽 정비).
- Phase 2 결과: `PHASE2_FINAL.md` 참조.
  - 공유 abbr (34개) + 5 토픽 인프라 + 토픽별 abbr 36개 + glossary stub 36개 추가.
  - 5 토픽 strict build 모두 OK.
  - Manual-review 잔여 664건 — 토픽별 `_remediation.md` 참조.
