# Plan: RDMA TB & Debug 학습 사이트 신설

## Objective
사내 RDMA IP 검증 환경(RDMA-TB)을 학습 자료로 정리. 기존 `topics/rdma`(프로토콜/IBTA 위주)에 추가하지 않고 **별도 topic** `topics/rdma_tb_dv`로 신설.

## Source of Truth
1. Confluence — Testbench Architecture (parent: 1224310992)
   - Overall(1224245459), TOP(1224704136 + Component/Test Flow), Submodule, Flow,
   - Error Handling Path(1335525456), Adding New Components(1333297423)
2. Confluence — Debugging Cases (parent: 1334608001)
   - Data Integrity(1336279137), CQ Poll Timeout(1335853134),
   - C2H Tracker(1335656540), Unexpected Error CQE(1335099464),
   - H2C/C2H QID Reference(1334771791)
3. 코드 — `/home/jaehyeok.lee/RDMA/RDMA-TB/lib/`
   - `lib/base/component/{config,custom_phase,env/{agent,data_env,dma_env,network_env,*},model,pool,test,util}/`
   - `lib/base/def/vrdma_defs.svh:75-88` (QID 정의)
   - `lib/base/object/sequence/{vrdma_top_sequence,vrdma_init_seq}.svh`
   - `lib/ext/test/{error_handling,sanity,...}/`

## Topic Layout — `topics/rdma_verification/`
```
topics/rdma_verification/
  mkdocs.yml                          # site_name: "RDMA Verification"
  docs/
    index.md                          # course home
    01_tb_overview.md                 # Multi-node TB top, env hierarchy
    02_component_hierarchy.md         # lib/base/component 디렉토리 분해
    03_phase_test_flow.md             # UVM phase + sequence 라이프사이클
    04_analysis_port_topology.md      # AP 토폴로지(issued/completed/cqe/qp_reg/mr_reg)
    05_extension_principles.md        # Adding-New-Components 4원칙
    06_error_handling_path.md         # Error path: driver/handler/comparators/c2h_tracker
    07_h2c_c2h_qid_map.md             # H2C/C2H QID 정의 + 디버깅 활용
    08_debug_data_integrity.md        # Case 1: Data mismatch
    09_debug_cq_poll_timeout.md       # Case 2: CQ poll timeout
    10_debug_c2h_tracker.md           # Case 3: C2H tracker error
    11_debug_unexpected_err_cqe.md    # Case 4: Unexpected error CQE
    12_debug_cheatsheet.md            # 통합 디버그 cheatsheet
    glossary.md                       # 30+ TB 전용 용어 (ISO 11179)
    quiz/
      index.md
      01..12_*_quiz.md                # 챕터별 퀴즈 (Bloom 혼합)
    stylesheets/extra.css             # 기존 rdma topic에서 복사
```

## Style & Quality
- 본문 한국어 + 영문 기술 용어 (기존 `topics/rdma` 스타일과 동일)
- 모든 챕터: Bloom 학습목표 → 핵심 개념 → 코드 walkthrough(`file_path:line` 인용) → 실전 예시 → 퀴즈 링크
- Glossary: ISO 11179 — 단일 문장 정의 + Source + Related + Example + See also
- Confluence 사실은 Confluence 링크, 코드 사실은 `file_path:line_number` 인용
- `mkdocs build --strict` 통과 (orphan 0, broken link 0)

## Steps
- [x] 1. Confluence 11+2 페이지 본문 수집 (raw)
- [x] 2. RDMA-TB 코드 매핑 — 컴포넌트/AP/에러 ID/QID 위치 확인
- [x] 3. Topic scaffold (mkdocs.yml + index.md + stylesheets) — `topics/rdma`를 미러
- [x] 4. 챕터 01~07 (Architecture 계열) 작성
- [x] 5. 챕터 08~11 (Debug Case 계열) 작성
- [x] 6. 챕터 12 (Cheatsheet) 작성
- [x] 7. Glossary 작성 (29 terms)
- [x] 8. 퀴즈 12개 + index 작성
- [x] 9. 랜딩 페이지(`landing/index.html`) 카드 추가 — 네트워크 섹션 안 (기존 rdma 카드 옆)
- [x] 10. `mkdocs build --strict` 검증 — 통과 (INFO only)

## Outcome
- 신규 topic: `topics/rdma_verification/` (12 챕터 + index + glossary + 12 퀴즈 + index)
- 랜딩 카드: 네트워크 섹션 (이스터에그) 안 RDMA 카드 옆
- 토픽 카운트: 17 → 18, 챕터 카운트: 99 → 111
- 기존 `topics/rdma/` 손대지 않음 (이번 세션 git diff 의 rdma/* 변경은 세션 시작 전부터 존재)

## Success Criteria
- 새 topic 사이트가 strict 모드로 빌드됨
- 기존 `topics/rdma` 변경 없음 (검증: git diff topics/rdma/ → empty)
- 12 챕터 + glossary + 12 퀴즈 모두 nav에 등재
- 모든 코드 인용에 `file_path:line` 포함
- 4 debug case 각각 step-by-step + 흔한 원인 표 + 관련 static flag 정리

## Open Questions
- 글로서리/퀴즈 `*_ko.md` 별도 미러까지 만들 것인가? → 기존 `topics/rdma`도 본문이 한국어 단일 파일이라 동일하게 단일 한국어 본문으로 진행 예정 (별도 영문 미러 X)
- 랜딩 카드 위치: 기존 RDMA 카드 옆 (네트워크 이스터에그 섹션 내) vs. 별도 카드

## Risks
- Confluence parent 페이지 일부(Submodule, Overall, Flow 자식)는 본문이 거의 비어 있음(draw.io 이미지 위주) → 코드 기반으로 보강 필요
- Adding-New-Components 4원칙이 매우 추상적 → 실제 코드 사례(stateless `vrdma_top_sequence` + stateful `vrdma_sequencer`)로 그라운딩
