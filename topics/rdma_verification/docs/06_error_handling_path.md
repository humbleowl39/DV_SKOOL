# Module 06 — Error Handling Path

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🧪</span>
    <span class="chapter-back-text">RDMA Verification</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 06</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-격리-병동의-3-단계-방벽">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-rdmaqpdestroyerr1-한번이-tb-전체에-퍼지는-궤적">3. 작은 예 — RDMAQPDestroy(.err(1))</a>
  <a class="page-toc-link" href="#4-일반화-3-경로--3-단위-게이트">4. 일반화 — 3 경로 + 3 단위 게이트</a>
  <a class="page-toc-link" href="#5-디테일-경로-별-코드-static-flag-시퀀스-템플릿">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Trace** `RDMASQDestroy(.err(1))` 가 driver→QP→comparator/tracker 를 어떻게 흐르는지 추적할 수 있다.
    - **Distinguish** `cmd.expected_error` (per-cmd) 와 `qp.isErrQP()` (per-QP) 와 static `err_enabled` (per-component, all QP) 의 적용 범위를 구분할 수 있다.
    - **Configure** 의도된 에러 시나리오를 위해 5개 static flag (각 comparator·tracker 의 `err_enabled`, `enable_error_cq_poll`, `turn_off`) 를 설정할 수 있다.
    - **Author** 정상 코드 흐름과 동등한 에러 테스트 시퀀스를 작성할 수 있다.

!!! info "사전 지식"
    - [Module 04 — Analysis Port Topology](04_analysis_port_topology.md) (`completed_wqe_ap` 의 ErrQP 게이트)
    - [Module 05 — Extension 4원칙](05_extension_principles.md) (Stateless 보존)
    - [RDMA Module 04 — QP FSM](../../rdma/04_service_types_qp/) (Reset/Init/RTR/RTS/SQErr/Err)

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _하나의 에러_, _전체 fail_

당신은 _intentional NAK_ 시나리오 작성. 한 QP 에 _rkey violation_ inject → NAK 받음 + WC error 확인.

결과: **시뮬레이션 전체 FATAL**. 다른 _정상_ QP 의 verb 까지 fail.

원인: Scoreboard 가 _하나의 NAK_ 를 _전역 fatal_ 로 처리 → 다른 QP 의 정상 시나리오까지 _abort_.

해법: **에러 격리 (isolation)**:
- **Per-cmd gate**: 이 NAK 는 _expected_, 해당 cmd 만 fail 처리.
- **Per-QP gate**: 다른 QP 는 정상 검증 계속.
- **Per-component gate**: 다른 컴포넌트 (예: receive scoreboard) 는 영향 없음.

3 단위 gate 가 _정밀_ 한 에러 시나리오 검증의 _필수_ 조건.

RDMA 검증에서 "에러 시나리오" 는 정상 시나리오만큼 중요합니다. 그러나 에러 케이스에 다른 정상 검증이 휩쓸려가면 (false positive fatal) 디버깅이 불가능해집니다. RDMA-TB 는 에러를 **격리 (isolate)** 하면서도 **검증 (check)** 하는 정밀한 메커니즘을 가지고 있습니다.

이 모듈을 건너뛰면 에러 테스트 작성 시 "왜 정상 verb 까지 fatal 이 나오는지" 헤맵니다. 3 경로 + 3 단위 게이트 (per-cmd / per-QP / per-component) 를 잡으면 어떤 에러를 어느 단위로 promote 할지 즉시 결정됩니다.

> Confluence 출처: [Error Handling Path](https://mangoboost.atlassian.net/wiki/spaces/RDMADV/pages/1335525456/Error+Handling+Path)

---

## 2. Intuition — 격리 병동의 3 단계 방벽

!!! tip "💡 한 줄 비유"
    에러 처리 ≈ **병원의 격리 병동**. <br>
    ① 환자 한 명만 격리 (per-cmd `expected_error=1`) — 한 verb 만 에러 예상. <br>
    ② 한 병실 격리 (per-QP `setErrState`) — 그 QP 의 모든 후속 verb 차단. <br>
    ③ 한 층 봉쇄 (per-component `err_enabled=1`) — 해당 comparator/tracker 의 모든 QP 검증 완화. <br>
    더 큰 단위로 갈수록 위험성도 큼 (검증 능력 약화) — 가능한 작은 단위로 격리.

### 한 장 그림 — 3 경로 + 3 단위 게이트

```d2
direction: right

PATHS: "에러 발생 3 경로" {
  direction: down
  P1: "① RDMASQDestroy(.err(1))\n→ driver.setErrState(qp)"
  P2: "② cq_handler 가 에러 CQE 수신\n→ setErrState(qp)"
  P3: "③ monitorErrCQ (백그라운드)\nERR_CQ 폴링 → ②"
}
GATES: "격리 게이트 3 단위" {
  direction: down
  G1: "① per-cmd\nexpected_error\n범위: 1 verb"
  G2: "② per-QP\nisErrQP()\n범위: 그 QP 후속 verb 전부"
  G3: "③ per-component\nerr_enabled\n범위: 모든 QP, 한 컴포넌트"
}
CLEANUP: "격리 후 chained 정리" {
  direction: down
  CL1: "driver: outstanding flush\ncompleted_wqe_ap 차단"
  CL2: "comparator: flushQP()\npending 큐 삭제"
  CL3: "c2h_tracker:\nis_err_qp_registered=1\n매칭 실패 skip"
  CL4: "sequencer:\nwc_error_status[qp]\nfirst error 보존"
}
PATHS -> GATES
GATES -> CLEANUP
```

### 왜 이 디자인인가 — Design rationale

세 가지가 동시에 풀려야 했습니다.

1. **에러 cascading 차단** — 한 에러로 모든 후속 verb 가 false fatal 을 일으키면 디버그 불가 → ErrQP 게이트로 silently skip.
2. **에러도 검증 대상** — 그러나 무조건 skip 하면 에러 자체의 검증이 안 됨 → cqe_validation_checker 는 받음, scoreboard 만 제외.
3. **다양한 격리 단위 필요** — 의도한 1 verb 에러부터 광범위 fault injection 까지 → 3 단위 게이트.

이 세 요구의 교집합이 3 경로 + 3 단위 + chained 정리입니다.

---

## 3. 작은 예 — `RDMAQPDestroy(.err(1))` 한번이 TB 전체에 퍼지는 궤적

가장 단순한 시나리오 — 에러 시나리오 시퀀스가 끝나고 QP 를 명시적으로 에러 destroy.

```d2
shape: sequence_diagram

Test: "test seq"
DRV: "driver"
C1: "1side_compare"
C2: "2side_compare"
CI: "imm_compare"
CT: "c2h_tracker"
SQ: "sequencer"

# Note over Test: T0 — destroy 요청
# Note over DRV: T0+1 — driver.RDMASQDestroy 진입
# Note over DRV: T0+2 — 후속 cmd_X(qp_num=5)
# Note over DRV: T0+3 — CQE 도착 중\ncompleted_wqe_ap 차단
# Note over DRV: T0+4 — deregister chain
# Note over Test: T0+5 — cleanup
Test -> DRV: "RDMAQPDestroy(qp=5, .err(1))"
DRV -> DRV: "destroy_qp.setErrState(1)\nqp[5].state = SQErr\n(per-QP gate ON)"
DRV -> DRV: "chkSQErrQP → isErrQP()==1\nskip + warning" { style.stroke-dash: 4 }
DRV -> C1: "deregisterQP(5)\n→ flushQP(5)"
DRV -> C2: "deregisterQP(5)\n→ flushQP(5)"
DRV -> CI: "deregisterQP(5)\n→ flushQP(5)"
DRV -> CT: "deregisterQP(5)\nis_err_qp_registered[node][5]=1\n(이후 매칭 실패 skip)"
Test -> SQ: "clearErrorStatus(5)\nwc_error_status[5].clear()"
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| T0 | test | `RDMAQPDestroy(.err(1))` | per-QP 게이트 진입 신호 |
| T0+1 | driver | `setErrState(qp)` | qp 의 isErrQP() = 1 |
| T0+2 | driver | 후속 cmd skip + warning | cascading 차단 |
| T0+3 | driver | `completed_wqe_ap` 차단 | scoreboard 정상 완료 카운트에서 제외 |
| T0+4 | comparator/tracker | `flushQP` / `is_err_qp_registered` | 잔존 outstanding 정리 + 지연 도착 흡수 |
| T0+5 | test | `clearErrorStatus(qp)` | 다음 verb 영향 차단 |

!!! note "여기서 잡아야 할 두 가지"
    **(1) `err=1` 한 인자가 5 컴포넌트에 chained 정리 트리거** — driver / 1side / 2side / imm / c2h_tracker. 빠뜨리면 한 컴포넌트만 stale.<br>
    **(2) ErrQP 의 cqe 는 여전히 cqe_validation_checker 가 받음** — 즉 에러 자체는 검증됨. 단지 _정상 완료 카운트_ 에서 빠짐.

---

## 4. 일반화 — 3 경로 + 3 단위 게이트

### 4.1 시작점 — `RDMASQDestroy(.err)` / `RDMAQPDestroy(.err)`

| 파라미터 | 값 | 설명 |
|---------|---|-----|
| `err` | 0 (기본) | 정상 QP destroy — outstanding 잔존 시 fatal |
| `err` | 1 | 에러 QP destroy — outstanding 허용, flush 수행 |

```systemverilog
this.RDMAQPDestroy(.t_seqr(seqr), .qp_num(qp_num), .err(1));
// → 각 comparator/tracker 가 flushQP() 수행
```

### 4.2 적용 범위 비교 — 무엇을 어떤 단위로 끄나?

| 단위 | 메커니즘 | 적용 범위 | 사용 시나리오 |
|------|---------|----------|------------|
| 단일 cmd | `cmd.expected_error = 1` | 한 verb 발행만 | 특정 read 가 RAE 를 받기를 예상할 때 |
| 단일 QP | `qp.setErrState(1)` (자동: SQDestroy.err / 에러 CQE) | 해당 QP 의 모든 후속 verb | 한 QP 에 대한 광범위 에러 테스트 |
| 모든 QP, 한 컴포넌트 | static `err_enabled = 1` | 해당 comparator/tracker 전체 | 실험적 fault injection 시 검증 통째로 완화 |
| 컴포넌트 자체 OFF | `enable_error_cq_poll = 0` / `turn_off = 1` | 해당 컴포넌트 전부 | 에러 CQ / 패킷 모니터 자체를 비활성화 |

---

## 5. 디테일 — 경로 별 코드, static flag, 시퀀스 템플릿

### 5.1 경로 1: Driver → QP Error State

```systemverilog
// vrdma_driver::RDMASQDestroy 어딘가
destroy_qp.setErrState(cmd.err);
// vrdma_driver.svh:530
```

이후 driver 동작:

| 위치 | 분기 | 효과 |
|------|------|-----|
| `EntryPoint → chkSQErrQP(cmd)` | `qp.isErrQP() == 1` 면 skip | 에러 QP 로 가는 모든 후속 command 무시 (warning 로그) |
| `completeOutstanding(cmd)` | `!t_qp.isErrQP()` 일 때만 `completed_wqe_ap.write(cmd)` (`vrdma_driver.svh:1327`) | 에러 QP 의 WQE 는 scoreboard 검증 대상에서 제외 |

> 핵심: 한 번 ErrQP 로 마킹되면 이후 모든 verb 가 silently skip — 에러 cascading 차단

### 5.2 경로 2: CQ Handler → Error CQE

DUT 에서 에러 CQE 발생 시 (예: `IB_WC_REM_ACCESS_ERR`):

```systemverilog
// vrdma_cq_handler.svh:217-223 (개념)
cmd.error_occured = 1;
this.drv.qp[cqe.local_qid].setErrState(1);
```

#### `expected_error` per-cmd 게이트

```systemverilog
// vrdma_cq_handler.svh:233-234
if(cmd.expected_error) begin
  cmd.expected_error = 0;
  ...
end

// :349-350
if(cmd.expected_error) return 0; // early exit if expected error
if(cmd.error_occured)  return 1; // early exit if error occurred
```

이 분기 덕분에:

- 에러를 **예상한** 시퀀스 → `expected_error=1` 설정 → fatal 안 남
- 에러를 **예상하지 못한** 경우 → `F-CQHDL-TBERR-0003` (Module 11)

### 5.3 경로 3: Error CQ 백그라운드 모니터링

`vrdma_cq_handler` 가 `run_phase` 에서 `monitorErrCQ()` 를 백그라운드로 돌립니다.

```systemverilog
// vrdma_cq_handler.svh:16, 80
static bit enable_error_cq_poll = 1;
...
if(enable_error_cq_poll) this.monitorErrCQ();
```

비활성화 패턴:

```systemverilog
class my_test extends rdma_base_test;
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    vrdma_cq_handler::enable_error_cq_poll = 0;
  endfunction
endclass
```

### 5.4 컴포넌트별 에러 시 동작

#### Data Env (Comparators)

| 컴포넌트 | 에러 감지 조건 | 동작 |
|----------|--------------|-----|
| `vrdma_1side_compare` | `qp.isErrQP() \|\| err_enabled` at `deregisterQP` (`:1312`) | `flushQP()` — 해당 QP 의 pending write/read 큐 전체 삭제 |
| `vrdma_2side_compare` | `qp.isErrQP() \|\| err_enabled` (`:697`) | `flushQP()` — 해당 QP 의 send/recv tracker 전체 삭제 |
| `vrdma_imm_compare` | `qp.isErrQP() \|\| err_enabled` (`:433`) | `flushQP()` — 해당 QP 의 send/cqe tracker 전체 삭제 |

#### Static `err_enabled` flag

- `vrdma_1side_compare::err_enabled` (default 0, line 85)
- `vrdma_2side_compare::err_enabled` (default 0, line 101)
- `vrdma_imm_compare::err_enabled`  (default 0, line 99)

```systemverilog
function void build_phase(uvm_phase phase);
  super.build_phase(phase);
  vrdma_1side_compare::err_enabled = 1; // 모든 QP 의 deregister 시 flush
  vrdma_2side_compare::err_enabled = 1;
  vrdma_imm_compare::err_enabled   = 1;
endfunction
```

#### DMA Env (C2H Tracker)

| 조건 | 동작 |
|------|-----|
| `qp.isErrQP() \|\| err_enabled` at `deregisterQP` | `is_err_qp_registered[node][qp] = 1` — 에러 등록 |
| `processC2hTransaction` — QP 매칭 실패 | `is_err_qp_registered.size() > 0` 이면 skip (fatal 대신) |
| `check_phase` — outstanding 잔존 | `qp.isErrQP() \|\| err_enabled` 면 fatal 대신 경고 |

> 코드: `vrdma_c2h_tracker.svh:98, 346, 349`

#### Network Env (Packet Monitors)

| 컴포넌트 | 메서드 | 동작 |
|----------|-------|-----|
| `vrdma_pkt_base_monitor` | `turnOff()` | `turn_off=1` — 패킷 처리 비활성화 |
| `vrdma_pkt_base_monitor` | `turnOn()` | `turn_off=0` — 재활성화 |
| `vrdma_ops_monitor` | (상속) | `turnOff()` 시 OPS 프로토콜 체크 중단 |
| `vrdma_rc_monitor` | (상속) | `turnOff()` 시 RC 프로토콜 체크 중단 |

### 5.5 `vrdma_cfg` 글로벌 체커 제어

| 필드 | 기본값 | 의도 |
|------|-------|-----|
| `has_dma_chk` | YES | DMA 체커 enable/disable |
| `has_packet_chk` | YES | 패킷 체커 enable/disable |
| `has_data_chk` | YES | 데이터 체커 enable/disable |

> 현재는 로그용 (`start_of_simulation_phase` 출력). 향후 체커 조건부 연결에 활용 예정.

### 5.6 Static Flag 요약

| Flag | 위치 | 기본값 | 영향 범위 |
|------|------|-------|----------|
| `vrdma_1side_compare::err_enabled` | data_env | 0 | 1side comparator — 모든 QP deregister 시 flush |
| `vrdma_2side_compare::err_enabled` | data_env | 0 | 2side comparator — 동일 |
| `vrdma_imm_compare::err_enabled` | data_env | 0 | IMM comparator — 동일 |
| `vrdma_c2h_tracker::err_enabled` | dma_env | 0 | C2H tracker — 매칭 실패 skip + deregister 에러 등록 |
| `vrdma_cq_handler::enable_error_cq_poll` | agent | 1 | Error CQ 백그라운드 폴링 on/off |
| `vrdma_pkt_base_monitor::turn_off` | network_env | 0 | 패킷 모니터 on/off |

### 5.7 에러 테스트 시퀀스 작성 패턴

```systemverilog
class err_test_seq extends vrdma_top_sequence;
  // ... factory boilerplate ...

  task body();
    // 1. 정상 등록
    this.RDMAQPCreate(.t_seqr(seqr), .qp_num(qp_num));

    // 2. 에러를 예상한 verb (per-cmd gate)
    vrdma_read_command read_cmd = ...;
    read_cmd.expected_error = 1;
    this.start_item(read_cmd, .sequencer(t_seqr));
    assert(read_cmd.randomize() with { qp_num == qp_num; rkey == bad_key; });
    this.finish_item(read_cmd);

    // 3. CQ poll — 에러 CQE 도 수용 (try_once=1 로 단발 폴링)
    this.RDMACQPoll(.t_seqr(seqr), .cq_num(cq_num), .try_once(1));

    // 4. 에러 발생 검증
    if(t_seqr.wc_error_status[qp_num].size() > 0) begin
      RDMAWCStatus_t status = t_seqr.wc_error_status[qp_num][0];
      `vmg_info("I-TEST", $sformatf("Error status: %s", status.name()), UVM_LOW)
    end

    // 5. 에러 QP 정리 (err=1)
    this.RDMAQPDestroy(.t_seqr(seqr), .qp_num(qp_num), .err(1));
    // → 각 comparator/tracker 의 flushQP()

    // 6. (선택) 에러 큐 클리어 — 다음 verb 의 영향 차단
    t_seqr.clearErrorStatus(qp_num);
  endtask
endclass
```

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — '에러 시나리오는 expected_error 만 켜면 끝'"
    **실제**: per-cmd 게이트는 **그 한 verb** 만. 그 verb 의 에러로 QP 가 ErrState 가 되면 _다음 verb_ 부터는 per-QP 게이트로 자동 skip. 하지만 마지막에 `RDMAQPDestroy(.err(1))` 으로 chained 정리 + `clearErrorStatus` 안 하면 다음 시퀀스로 stale state 가 넘어감.<br>
    **왜 헷갈리는가**: per-cmd 게이트 이름이 가장 직관적이라.

!!! danger "❓ 오해 2 — '`err_enabled = 1` 켜면 모든 게 자동 처리'"
    **실제**: `err_enabled` 는 **per-component, all QP** — 검증 능력이 통째로 약화됨. fault injection 같은 광범위 시나리오에서만. 일반적인 의도된 에러는 per-cmd 또는 per-QP 단위.

!!! danger "❓ 오해 3 — 'ErrQP 인 verb 의 cqe 는 안 본다'"
    **실제**: `cqe_ap` 는 ErrQP 도 broadcast — `cqe_validation_checker` 는 받음. 차단되는 건 `completed_wqe_ap` 만 — 즉 _scoreboard 의 정상 완료 카운트_ 에서만 제외. 에러 자체는 검증됨.

!!! danger "❓ 오해 4 — 'monitorErrCQ 가 fatal 일으키면 코드 버그다'"
    **실제**: `enable_error_cq_poll=1` (default) 인데 의도된 에러 시나리오에서 ERR_CQ 가 채워지면 백그라운드 폴링이 잡아서 fatal. 의도라면 build_phase 에서 끄기.

!!! danger "❓ 오해 5 — 'expected_error=1 만 두면 ERR CQ 안 와도 됨'"
    **실제**: `expected_error` 는 _에러 도착 시_ skip 시키는 게이트일 뿐. ERR CQE 가 안 오면 정상 처리 — TB 가 정상으로 간주. 의도가 "에러 와야 함" 이면 도착 후 `wc_error_status[qp].size() > 0` 으로 검증.

### DV 디버그 체크리스트

| 증상 | 의심 |
|------|------|
| 정상 QP 인데 `flushQP` 호출됨 | `err_enabled = 1` 로 잘못 켜져 있음 |
| 에러 QP destroy 후 c2h_tracker fatal | `err=1` 누락 (`F-C2H-TBERR-0001`) |
| 백그라운드 error CQ 모니터에서 fatal | `enable_error_cq_poll` 끄지 않음 — 의도라면 끄기 |
| 정상 verb 가 silently skip 되는 것처럼 보임 | 이전 verb 가 에러 CQE 를 받아 QP 가 ErrQP 로 전이됨 — `t_seqr.wc_error_status[qp_num]` 확인 |
| `expected_error=1` 인데 fatal | per-cmd 게이트가 `cqe.error_occured` 도착 _전에_ 설정됐는지 (cmd 발행 시점 기준) |
| 다음 시퀀스로 stale 에러 큐 넘어감 | `clearErrorStatus` 누락 |
| 에러 CQE 받았는데 wc_error_status 비어있음 | sequencer 와 cq_handler 의 연결 — 다른 노드의 sequencer 봤을 가능성 |
| ErrQP 정리 후 지연 C2H 도착으로 fatal | `is_err_qp_registered` 가 지연 흡수해야 하는데 미설정 — `err=1` 빠뜨림 |

---

## 7. 핵심 정리 (Key Takeaways)

- 에러 처리는 3-경로 — driver(SQDestroy.err), cq_handler(에러 CQE), 백그라운드 monitorErrCQ.
- 게이트는 3-단위 — per-cmd (`expected_error`), per-QP (`isErrQP`), per-component (`err_enabled` static).
- ErrQP 의 WQE 는 `completed_wqe_ap` 로 전달되지 않아 scoreboard 가 검증 제외.
- `RDMAQPDestroy(.err(1))` 가 모든 횡단 컴포넌트의 `flushQP()` 를 트리거하여 깨끗한 정리.
- 의도된 에러 시나리오에서는 마지막에 `clearErrorStatus(qp)` 로 stale 차단.

!!! warning "실무 주의점"
    - per-component `err_enabled` 는 검증 능력 약화 — fault injection 같은 의도된 광범위 시나리오에만.
    - `expected_error=1` 은 cmd 발행 _전에_ 설정. randomize 후 set 하면 too late.

### 7.1 자가 점검

!!! question "🤔 Q1 — Error gate 선택 (Bloom: Apply)"
    "QP 3 의 _하나의 WRITE_ 가 NAK 받아도 OK" — 어느 gate?

    ??? success "정답"
        **Per-cmd `expected_error=1`** — 특정 cmd 만.

        - Per-QP: QP 3 의 _모든 cmd_ 가 fail 허용 → 너무 광범위.
        - Per-component: 전체 scoreboard 영향 → 광범위.

        Per-cmd 가 _가장 좁은 격리_.

!!! question "🤔 Q2 — Expected error timing (Bloom: Analyze)"
    `expected_error=1` 을 _randomize 후_ 설정. 왜 _too late_?

    ??? success "정답"
        Sequence flow:
        1. `start_item`.
        2. `randomize`.
        3. `finish_item` → driver 가 즉시 발행.

        Driver 가 발행 후 cmd 가 _wire 위_ → DUT 처리 → response → scoreboard. Scoreboard 가 _expected_error_ 안 보고 _fatal_.

        해결: `randomize` 직후 _즉시_ `expected_error = 1`. 또는 randomize constraint 안에 표현.

### 7.2 출처

**Internal (Confluence)**
- `Error Handling Path` (id=1335525456)

---

## 다음 모듈

→ [Module 07 — H2C / C2H QID Reference](07_h2c_c2h_qid_map.md): DMA 인터페이스의 QID 로 어느 서브시스템이 동작했는지 즉시 식별.

[퀴즈 풀어보기 →](quiz/06_error_handling_path_quiz.md)


--8<-- "abbreviations.md"
