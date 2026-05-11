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
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-cheatsheet--한-페이지-결정-카드">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-자주-쓰는-시나리오-표--이-카드를-봐야-할-때">3. 작은 예 — 자주 쓰는 시나리오</a>
  <a class="page-toc-link" href="#4-일반화-cheatsheet-9-섹션">4. 일반화 — Cheatsheet 9 섹션</a>
  <a class="page-toc-link" href="#5-디테일-9-섹션-본문">5. 디테일 — 9 섹션 본문</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-디버그-체크리스트">6. 흔한 오해 + 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈은 cheatsheet 입니다 — 시뮬 실패 시 한 페이지 안에서 어디로 갈지 결정.

    - **Lookup** 에러 ID 를 보고 5 분 안에 어느 모듈 (M08–M11) 로 갈지 찾을 수 있다.
    - **Recall** QID / static flag / 5 단계 디버그 절차 / AP topology 를 기억하지 않고 즉시 참조할 수 있다.
    - **Apply** 의도된 에러 시퀀스 보일러플레이트를 복사해 새 테스트에 적용할 수 있다.

!!! info "사용 시나리오"
    - 시뮬 fail 직후 5 분 내에 어느 모듈로 갈지 결정 (§5.1, §5.6)
    - QID / static flag / AP topology 가 헷갈릴 때 빠른 참조 (§5.2, §5.3, §5.8)
    - 의도된 에러 시퀀스 작성 시 보일러플레이트 복사 (§5.7)

---

## 1. Why care? — 이 모듈이 왜 필요한가

M08–M11 은 4 대 디버그 케이스를 _각각_ 다룹니다. 그런데 실제 시뮬 fail 이 나면 (1) 어느 케이스인지 모르는 상태에서 (2) 5 분 안에 어느 모듈을 펼칠지 결정해야 합니다. M08–M11 을 매번 처음부터 다시 읽을 수는 없죠.

이 모듈은 그 5 분을 위한 **한 페이지 검색 카드** 입니다. 에러 ID prefix → 컴포넌트 → 모듈 → 첫 액션 의 4 단 매핑, QID 한 줄 표, static flag 한 줄 표, 5 단계 디버그 절차, 그리고 의도된 에러 시퀀스 보일러플레이트까지 — 모두 한 페이지 안에 들어가도록 압축되어 있습니다. M08–M11 의 "어디로 가나" 부분만 따로 분리한 셈입니다.

이 모듈을 건너뛰면 시뮬 fail 마다 M08, M09, M10, M11 을 차례로 펴서 "어느 케이스지?" 를 매번 처음부터 푸느라 시간을 낭비합니다. cheatsheet 의 §5.1 한 표만 외우면 트리아지 시간이 5 분 → 30 초로 줄어듭니다.

---

## 2. Intuition — Cheatsheet = 한 페이지 결정 카드

!!! tip "💡 한 줄 비유"
    응급실의 **트리아지 카드**. 환자 (시뮬 fail) 가 들어오면 의사 (디버거) 는 카드 한 장으로 (1) 어느 과 (M08/09/10/11) 로 보낼지, (2) 첫 처치 (첫 액션) 가 뭔지, (3) 모니터링 장비 (QID, static flag, AP) 가 어디 있는지 — 모두 한 페이지에서 결정. 카드를 못 외워도 되지만, _카드의 존재_ 와 _어느 칸을 먼저 보는지_ 는 외워야.

### 한 장 그림 — 시뮬 fail → 30 초 트리아지

```
                       시뮬 fail (run.log 에 ERROR/FATAL)
                                  │
                                  ▼
                ┌──── §5.6 의 grep 한 줄 ────┐
                │  grep -nE "(UVM_FATAL|UVM_ERROR|F-|E-)" run.log | head -5  │
                └──── 첫 에러 ID 추출 ────┘
                                  │
                                  ▼
                ┌──── §5.1 의 매핑 표 ────┐
                │   에러 ID prefix → 모듈 → 첫 액션                          │
                │                                                            │
                │   E-DRV-TBERR    → M09  → QID 14–17 fetch 여부            │
                │   F-CQHDL-TBERR  → M11  → wc_status RETRY 분류            │
                │   E-SB-MATCH     → M08  → 첫 mismatch byte 위치            │
                │   F-C2H-MATCH    → M10  → W-C2H-MATCH-* unprocessed PA    │
                │   E-C2H-MATCH    → M10  → RC vs OPS/SR ordering 분기      │
                │   F-C2H-MATCH-3/4/5 → M10  → DUT len vs expected size    │
                │   E-C2H-FLOW/CFG  → M06  → RDMAQPDestroy(.err) lifecycle │
                └────────────────────────┘
                                  │
                                  ▼
              ┌── §5.5 의 5 단계 디버그 절차 ──┐
              │  1. 에러 로그 ID/qp/size 추출    │
              │  2. TB SW 엔티티 정합성          │
              │  3. HW QID 매트릭스 (M07)        │
              │  4. DUT 내부 fsdb                 │
              │  5. MR/SGE/page boundary          │
              └─────────────────────────────────┘
```

### 왜 이 디자인인가 — Design rationale

세 가지가 동시에 풀려야 했습니다.

1. **검색 속도** — fail 후 첫 30 초가 가장 중요. M08–M11 을 일일이 읽지 않고 한 페이지에서 결정.
2. **재사용성** — QID, static flag, AP 의 핵심 표가 M07/M04/M06 에 흩어져 있어 매번 다른 모듈을 펴야. cheatsheet 가 _요약본_ 으로 한 곳에 모음.
3. **보일러플레이트** — 의도된 에러 시퀀스의 4 단계 구조가 매 테스트마다 반복 — 복사·붙여넣기 가능한 미니 템플릿 제공.

이 세 요구의 교집합이 9 섹션 한 페이지 cheatsheet 입니다.

---

## 3. 작은 예 — 자주 쓰는 시나리오 + 이 카드를 봐야 할 때

### 자주 쓰는 시나리오 (한 줄 결정 표)

| 시나리오 | 첫 카드 | 첫 액션 |
|---------|--------|--------|
| 시뮬이 5 ms 만에 fatal — `F-CQHDL-TBERR-0003` | §5.1 → M11 | `wc_status` RETRY (12/13) 인지부터 |
| Scoreboard mismatch — `E-SB-MATCH-*` | §5.1 → M08 | 첫 mismatch byte 위치 → page/SGE/MR boundary |
| CQ poll 후 timeout — `E-DRV-TBERR-0001` | §5.1 → M09 | QID 14–17 fetch 여부 (`grep "qid=14"` fsdb) |
| C2H PA 매칭 fatal — `F-C2H-MATCH-0002` | §5.1 → M10 | `W-C2H-MATCH-0001` unprocessed PA 캡처 |
| RC QP 인데 ordering violation — `E-C2H-MATCH-0001` | §5.1 → M10 | DUT RC reorder logic |
| Error injection 테스트 작성 중 | §5.7 미니 템플릿 | per-cmd `expected_error=1` |
| QID 가 H2C 인지 C2H 인지 헷갈림 | §5.2 한 줄 표 | 방향 + QID 매트릭스 |
| 컴포넌트의 AP 가 어디로 가는지 모름 | §5.8 AP topology | issued_wqe_ap / completed_wqe_ap / cqe_ap |
| 에러 후 cascade 정리 흐름 헷갈림 | §5.4 ErrQP 한 장 그림 | `RDMAQPDestroy(.err)` 부터 |
| 로그에서 첫 에러 못 찾겠음 | §5.6 grep 키워드 | `head -5` |

### 이 카드를 봐야 할 때 (trigger)

| 신호 | 의미 | 어디로 |
|------|------|--------|
| run.log 에 새 에러 ID 가 보임 | 어느 모듈인지 모름 | §5.1 |
| fsdb 에서 QID 신호를 보고 있음 | QID 의 용도 까먹음 | §5.2 |
| `err_enabled = 1` 설정 코드 봄 | 어느 컴포넌트의 flag 인지 | §5.3 |
| `RDMAQPDestroy(.err)` 호출 | 후속 정리 흐름 | §5.4 |
| "어디부터 디버그하지?" | 절차 까먹음 | §5.5 |
| run.log 가 수 만 줄 | 어떤 키워드로 grep? | §5.6 |
| Error injection test 작성 | 보일러플레이트 | §5.7 |
| Scoreboard / tracker 가 어느 AP 구독? | Topology 까먹음 | §5.8 |
| 디버그 후 어디로 가나? | 다음 학습 경로 | §5.9 |

!!! note "여기서 잡아야 할 두 가지"
    **(1) Cheatsheet 의 첫 표 (§5.1) 가 가장 빈도 높음** — 시뮬 fail 의 80 % 가 이 표 한 줄로 30 초 트리아지 끝남.<br>
    **(2) 보일러플레이트 (§5.7) 는 복사 후 _per-cmd_ promote 만 확인** — 시퀀스 전체에 `expected_error=1` 걸리는 실수가 가장 흔한 false-negative.

---

## 4. 일반화 — Cheatsheet 9 섹션

| 섹션 | 무엇 | 언제 보나 |
|------|------|---------|
| §5.1 | 에러 ID → 모듈 → 첫 액션 매핑 표 | 새 에러 ID 발견 시 가장 먼저 |
| §5.2 | H2C / C2H QID 한 줄 표 | fsdb 의 QID 해석 |
| §5.3 | Static flag 한 줄 표 | err_enabled / turn_off 등 |
| §5.4 | ErrQP 흐름 한 장 그림 | `RDMAQPDestroy(.err)` 후 cascade |
| §5.5 | 5 단계 디버그 절차 (M08–M11 공통) | 어디부터 보나 헷갈릴 때 |
| §5.6 | 빠른 검색 키워드 (run.log) | grep 보일러플레이트 |
| §5.7 | 의도된 에러 시퀀스 미니 템플릿 | error injection test 작성 |
| §5.8 | 컴포넌트 → AP → Subscriber 한 장 그림 | AP topology 파악 |
| §5.9 | 다음에 어디로 가나 | 디버그 후 학습 경로 |

---

## 5. 디테일 — 9 섹션 본문

### 5.1 에러 ID → 모듈 → 첫 액션

| 에러 ID prefix | 컴포넌트 | 모듈 | 첫 액션 |
|--------------|---------|-----|--------|
| `E-DRV-TBERR-0001/0002` | `vrdma_driver` | [M09](09_debug_cq_poll_timeout.md) | QID 14–17 fetch 여부 확인 |
| `F-CQHDL-TBERR-0003` | `vrdma_cq_handler` | [M11](11_debug_unexpected_err_cqe.md) | `wc_status` 가 RETRY 계열인지 분류 |
| `E-SB-MATCH-*` | `vrdma_1/2side/imm_compare` | [M08](08_debug_data_integrity.md) | 첫 mismatch byte 위치 → page/SGE/MR boundary 비교 |
| `F-C2H-MATCH-0001/0002` | `vrdma_c2h_tracker` | [M10](10_debug_c2h_tracker.md) | `W-C2H-MATCH-*` unprocessed PA 리스트 캡처 |
| `E-C2H-MATCH-0001` | `vrdma_c2h_tracker` | [M10](10_debug_c2h_tracker.md) | RC vs OPS/SR — ordering 규칙 분기 |
| `F-C2H-MATCH-0003/0004/0005` | `vrdma_c2h_tracker` | [M10](10_debug_c2h_tracker.md) | DUT 가 expected 보다 더 많이 썼나 / addr 맞나 |
| `E-C2H-FLOW-*`, `E-C2H-CFG-*`, `F-C2H-TBERR-*` | `vrdma_c2h_tracker` | [M06](06_error_handling_path.md) | `RDMAQPDestroy(.err)` / lifecycle 오류 |

### 5.2 H2C / C2H QID 한 줄 표

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
> 자세히: [Module 07 — H2C/C2H QID Reference](07_h2c_c2h_qid_map.md)

### 5.3 Static Flag 한 줄 표 (Module 06)

| Flag | Default | 효과 |
|------|---------|------|
| `vrdma_1side_compare::err_enabled` | 0 | 1side compare flushQP on every QP deregister |
| `vrdma_2side_compare::err_enabled` | 0 | 2side compare 동일 |
| `vrdma_imm_compare::err_enabled` | 0 | imm compare 동일 |
| `vrdma_c2h_tracker::err_enabled` | 0 | c2h tracker — 매칭 실패 skip + deregister 에러 등록 |
| `vrdma_cq_handler::enable_error_cq_poll` | 1 | Error CQ 백그라운드 폴링 on/off |
| `vrdma_pkt_base_monitor::turn_off` | 0 | 패킷 모니터 on/off |

### 5.4 ErrQP 흐름 한 장 그림

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

### 5.5 5 단계 디버그 절차 (모듈 8/9/10/11 공통)

| Step | 무엇을 보나 |
|------|-----------|
| 1 | 에러 로그에서 ID, 컴포넌트, qp_num, transfer_size 추출 |
| 2 | TB SW 엔티티 (MR / QP / IOVA / page table) 정합성 — 의도된 시나리오인지 |
| 3 | HW 인터페이스 (H2C / C2H QID matrix) — 어느 단계에서 끊겼는지 |
| 4 | DUT 내부 datapath / FSM (fsdb) — 신호 추적 |
| 5 | MR / SGE / page boundary — 경계와 mismatch 위치 매핑 |

### 5.6 빠른 검색 키워드 (run.log)

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

### 5.7 의도된 에러 시나리오 시퀀스 — 미니 템플릿

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

### 5.8 컴포넌트 → AP → Subscriber 한 장 그림

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

### 5.9 다음에 어디로 가나?

- 새 컴포넌트 추가 전: [Module 05 — 4 원칙](05_extension_principles.md) 체크리스트
- 시퀀스 작성 전: [Module 03 — Phase / 시퀀서 라우팅](03_phase_test_flow.md)
- AP 구독 위치: [Module 04 — AP Topology](04_analysis_port_topology.md)
- 에러 게이트 설계: [Module 06 — Error Handling](06_error_handling_path.md)
- QID 디버그: [Module 07 — QID Reference](07_h2c_c2h_qid_map.md)

---

## 6. 흔한 오해 와 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Cheatsheet 는 외워야 한다'"
    **실제**: cheatsheet 의 _존재_ 만 알면 됨. 검색 위치 (§5.1 첫 표, §5.2 QID, §5.7 보일러플레이트) 만 기억하고 매번 펴서 본다는 것 자체가 cheatsheet 의 사용법.<br>
    **왜 헷갈리는가**: 학습 자료라 외우는 것으로 오인.

!!! danger "❓ 오해 2 — '한 페이지에 다 들어가니 M08–M11 안 봐도 됨'"
    **실제**: cheatsheet 는 "어디로 갈지" 결정 카드 — 진짜 디버그는 M08/09/10/11 에서. 첫 액션을 cheatsheet 에서 결정한 뒤, 그 모듈로 들어가 5 단계 디버그 절차를 적용해야.

!!! danger "❓ 오해 3 — 'grep 한 줄로 첫 에러 잡으면 끝'"
    **실제**: `head -5` 가 가르쳐 주는 건 _첫 에러 ID_ 뿐. 그 에러의 root cause 는 §5.1 의 첫 액션 + 해당 모듈의 5 단계 디버그 절차로 추적해야 함. cascading error 가 많은 시뮬일수록 첫 에러 외에는 의미 없음.

!!! danger "❓ 오해 4 — '`expected_error=1` 보일러플레이트 (§5.7) 를 시퀀스 전체에 적용해도 됨'"
    **실제**: per-cmd 게이트. 의도된 에러 verb 1 개에만 켜고 후속 정상 verb 는 꺼야. 전체 적용 = silently false-negative — Module 11 의 가장 위험한 안티패턴.

### 디버그 체크리스트 (Cheatsheet 사용 자체에 대한)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 새 에러 ID 를 매핑표에서 못 찾음 | M08–M11 외 모듈 (M06) | §5.1 의 `E-C2H-FLOW-*` / `E-C2H-CFG-*` 라인 |
| QID 가 매트릭스에 없음 | DUT 측 추가 QID (구현 변경?) | `lib/base/def/vrdma_defs.svh:75-88` 갱신 |
| static flag 가 명시되지 않은 동작 | M06 의 일반 정책 | §5.3 외에 M06 chapter |
| 보일러플레이트 적용 후도 fatal | per-cmd promote 누락 | §5.7 의 1번 — `read_cmd.expected_error = 1` 위치 |
| AP topology 가 다이어그램과 다름 | 신규 컴포넌트 추가됨 | M04 (M05 의 4 원칙 적용) |
| 5 단계 절차 중 어느 단계 막힘 | Step 별 카드 — M07 (QID), M06 (ErrQP) | 해당 모듈로 분기 |

---

## 7. 핵심 정리 (Key Takeaways)

- Cheatsheet 는 _검색 카드_ 이지 학습 자료가 아님 — _존재_ 만 알면 됨.
- §5.1 의 에러 ID → 모듈 → 첫 액션 매핑이 가장 빈도 높음 (fail 의 80 %).
- §5.5 의 5 단계 디버그 절차는 M08–M11 공통 — 첫 액션 후 적용.
- §5.7 의 의도된 에러 보일러플레이트는 per-cmd `expected_error=1` 만 주의.
- §5.9 의 "다음에 어디로" 가 디버그 후 학습 경로 — M05/M03/M04/M06/M07.

!!! warning "실무 주의점"
    - cheatsheet 매핑표에 없는 에러 ID 를 만나면 M06 (lifecycle) 또는 새 모듈을 추가해야 — 매핑표를 갱신.
    - `grep head -5` 의 결과가 cascading error 일 수 있음 — 첫 에러 ID 가 항상 root cause 는 아님.
    - 보일러플레이트 복사 후 randomize constraint 와 cleanup (`RDMAQPDestroy(.err)` + `clearErrorStatus`) 누락이 가장 흔한 실수.

---

[퀴즈 풀어보기 →](quiz/12_debug_cheatsheet_quiz.md)


--8<-- "abbreviations.md"
