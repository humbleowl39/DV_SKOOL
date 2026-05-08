# Module 12 — Debug Cheatsheet

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🧪</span>
    <span class="chapter-back-text">RDMA Verification</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 12</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-에러-id--모듈--첫-액션">1. 에러 ID → 모듈 → 첫 액션</a>
  <a class="page-toc-link" href="#2-h2c--c2h-qid-한-줄-표">2. QID 한 줄 표</a>
  <a class="page-toc-link" href="#3-static-flag-한-줄-표-module-06">3. Static Flag 한 줄 표</a>
  <a class="page-toc-link" href="#4-errqp-흐름-한-장-그림">4. ErrQP 흐름</a>
  <a class="page-toc-link" href="#5-5단계-디버그-절차-모듈-89101112-공통">5. 5단계 디버그 절차</a>
  <a class="page-toc-link" href="#6-빠른-검색-키워드-runlog">6. 빠른 검색 키워드</a>
  <a class="page-toc-link" href="#7-의도된-에러-시나리오-시퀀스--미니-템플릿">7. 의도된 에러 시퀀스 템플릿</a>
  <a class="page-toc-link" href="#8-컴포넌트--ap--subscriber-한-장-그림">8. AP Subscriber 한 장 그림</a>
  <a class="page-toc-link" href="#9-다음에-어디로-가나">9. 다음에 어디로 가나</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈은 cheatsheet 입니다 — 시뮬 실패 시 한 페이지 안에서 어디로 갈지 결정.

    - **Lookup** 에러 ID → 모듈 → 첫 액션
    - **Recall** QID, static flag, 5단계 디버그 절차

!!! info "사용 시나리오"
    - 시뮬 fail 직후 5분 내에 어느 모듈로 갈지 결정 (§1, §6)
    - QID / static flag / AP topology 가 헷갈릴 때 빠른 참조 (§2, §3, §8)
    - 의도된 에러 시퀀스 작성 시 보일러플레이트 복사 (§7)

## 1. 에러 ID → 모듈 → 첫 액션

| 에러 ID prefix | 컴포넌트 | 모듈 | 첫 액션 |
|--------------|---------|-----|--------|
| `E-DRV-TBERR-0001/0002` | `vrdma_driver` | [M09](09_debug_cq_poll_timeout.md) | QID 14–17 fetch 여부 확인 |
| `F-CQHDL-TBERR-0003` | `vrdma_cq_handler` | [M11](11_debug_unexpected_err_cqe.md) | `wc_status` 가 RETRY 계열인지 분류 |
| `E-SB-MATCH-*` | `vrdma_1/2side/imm_compare` | [M08](08_debug_data_integrity.md) | 첫 mismatch byte 위치 → page/SGE/MR boundary 비교 |
| `F-C2H-MATCH-0001/0002` | `vrdma_c2h_tracker` | [M10](10_debug_c2h_tracker.md) | `W-C2H-MATCH-*` unprocessed PA 리스트 캡처 |
| `E-C2H-MATCH-0001` | `vrdma_c2h_tracker` | [M10](10_debug_c2h_tracker.md) | RC vs OPS/SR — ordering 규칙 분기 |
| `F-C2H-MATCH-0003/0004/0005` | `vrdma_c2h_tracker` | [M10](10_debug_c2h_tracker.md) | DUT 가 expected 보다 더 많이 썼나 / addr 맞나 |
| `E-C2H-FLOW-*`, `E-C2H-CFG-*`, `F-C2H-TBERR-*` | `vrdma_c2h_tracker` | [M06](06_error_handling_path.md) | `RDMAQPDestroy(.err)` / lifecycle 오류 |

## 2. H2C / C2H QID 한 줄 표

| 방향 | QID | 용도 |
|------|-----|-----|
| H2C | 8 | Requester payload fetch (REQ) |
| H2C | 9 | Responder payload fetch (RSP) |
| H2C | 10–13 | Recv WQE fetch (4ch) |
| H2C | 14–17 | Cmd WQE fetch (4ch) |
| H2C | 18 | Control WQE fetch |
| H2C | 20 | Page Table Miss fetch |
| C2H | 8–9 | Responder data write (2ch) |
| C2H | 10–11 | CQE write (2ch) |
| C2H | 12–13 | Zero init write (2ch) |
| C2H | 14 | CC notify |

> 정의: `lib/base/def/vrdma_defs.svh:75-88`

## 3. Static Flag 한 줄 표 (Module 06)

| Flag | Default | 효과 |
|------|---------|------|
| `vrdma_1side_compare::err_enabled` | 0 | 1side compare flushQP on every QP deregister |
| `vrdma_2side_compare::err_enabled` | 0 | 2side compare 동일 |
| `vrdma_imm_compare::err_enabled` | 0 | imm compare 동일 |
| `vrdma_c2h_tracker::err_enabled` | 0 | c2h tracker — 매칭 실패 skip + deregister 에러 등록 |
| `vrdma_cq_handler::enable_error_cq_poll` | 1 | Error CQ 백그라운드 폴링 on/off |
| `vrdma_pkt_base_monitor::turn_off` | 0 | 패킷 모니터 on/off |

## 4. ErrQP 흐름 한 장 그림

```
RDMAQPDestroy(.err(1))
   │
   ├── driver: setErrState(1)
   │     └── 이후 verb 모두 skip (chkSQErrQP)
   │     └── completed_wqe_ap 차단 (isErrQP() 게이트)
   │
   ├── 1side/2side/imm_compare: flushQP(qp)
   │     └── pending write/read/send/recv/imm 큐 삭제
   │
   ├── c2h_tracker: is_err_qp_registered[node][qp] = 1
   │     └── 매칭 실패 시 fatal 대신 skip
   │     └── check_phase 잔존 outstanding 도 fatal 대신 warning
   │
   └── 시퀀서: wc_error_status[qp][0]에 first error 보존
```

## 5. 5단계 디버그 절차 (모듈 8/9/10/11 공통)

| Step | 무엇을 보나 |
|------|-----------|
| 1 | 에러 로그에서 ID, 컴포넌트, qp_num, transfer_size 추출 |
| 2 | TB SW 엔티티 (MR / QP / IOVA / page table) 정합성 — 의도된 시나리오인지 |
| 3 | HW 인터페이스 (H2C / C2H QID matrix) — 어느 단계에서 끊겼는지 |
| 4 | DUT 내부 datapath / FSM (fsdb) — 신호 추적 |
| 5 | MR / SGE / page boundary — 경계와 mismatch 위치 매핑 |

## 6. 빠른 검색 키워드 (run.log)

```bash
# 첫 에러 시점 (cascading 무시)
grep -nE "(UVM_FATAL|UVM_ERROR|F-|E-)" run.log | head -5

# C2H tracker 진단 (fatal 직전)
grep "W-C2H-MATCH-" run.log

# CQ polling 동작 추적
grep -E "Try Count|TAIL POINTER|PHASE" run.log | tail -20

# 에러 CQE wc_status
grep -E "wc_status" run.log | head

# c2h_tracker active 상태 (CQ timeout 분석 시)
grep -E "c2h_tracker.*active" run.log | tail -20

# 에러 ID 범주별 카운트
grep -oE "(E-DRV-|E-SB-|F-CQHDL-|F-C2H-|E-C2H-)[A-Z]+-[0-9]{4}" run.log | sort | uniq -c
```

## 7. 의도된 에러 시나리오 시퀀스 — 미니 템플릿

```systemverilog
// 1. expected error verb
read_cmd.expected_error = 1;
this.start_item(read_cmd, .sequencer(t_seqr));
assert(read_cmd.randomize() with { ... });
this.finish_item(read_cmd);

// 2. single-shot CQ poll
this.RDMACQPoll(.t_seqr(seqr), .cq_num(cq), .try_once(1));

// 3. error 검증
if(t_seqr.wc_error_status[qp].size() > 0) begin
  RDMAWCStatus_t st = t_seqr.wc_error_status[qp][0];
  // assert(st == EXPECTED_STATUS)
end

// 4. cleanup
this.RDMAQPDestroy(.t_seqr(seqr), .qp_num(qp), .err(1));
t_seqr.clearErrorStatus(qp);
```

## 8. 컴포넌트 → AP → Subscriber 한 장 그림

```
vrdma_driver
├── issued_wqe_ap    → *_handler → 1/2side/imm_compare, c2h_tracker
├── completed_wqe_ap → data_scoreboard (단, ErrQP 는 차단)
├── cqe_ap           → 1/2side/imm_compare
├── qp_reg_ap        → all comparator/tracker
└── mr_reg_ap        → c2h_tracker, scoreboard

vrdma_cq_handler
└── cqe_validation_cqe_ap → cqe_validation_checker, cqe_cov_collector
```

## 9. 다음에 어디로 가나?

- 새 컴포넌트 추가 전: [Module 05 — 4원칙](05_extension_principles.md) 체크리스트
- 시퀀스 작성 전: [Module 03 — Phase / 시퀀서 라우팅](03_phase_test_flow.md)
- AP 구독 위치: [Module 04 — AP Topology](04_analysis_port_topology.md)
- 에러 게이트 설계: [Module 06 — Error Handling](06_error_handling_path.md)
- QID 디버그: [Module 07 — QID Reference](07_h2c_c2h_qid_map.md)

[퀴즈 풀어보기 →](quiz/12_debug_cheatsheet_quiz.md)


--8<-- "abbreviations.md"
