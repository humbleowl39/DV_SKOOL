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

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Trace** `RDMASQDestroy(.err(1))` 가 driver→QP→comparator/tracker 를 어떻게 흐르는지 추적할 수 있다.
    - **Distinguish** `cmd.expected_error` (per-cmd) 와 `qp.isErrQP()` (per-QP) 와 static `err_enabled` (per-component, all QP) 의 적용 범위를 구분할 수 있다.
    - **Configure** 의도된 에러 시나리오를 위해 5개 static flag (각 comparator·tracker 의 `err_enabled`, `enable_error_cq_poll`, `turn_off`)를 설정할 수 있다.
    - **Author** 정상 코드 흐름과 동등한 에러 테스트 시퀀스를 작성할 수 있다.

## 왜 이 모듈이 중요한가
RDMA 검증에서 "에러 시나리오" 는 정상 시나리오만큼 중요합니다. 그러나 에러 케이스에 다른 정상 검증이 휩쓸려가면(false positive fatal) 디버깅이 불가능해집니다. RDMA-TB 는 에러를 **격리(isolate)** 하면서도 **검증(check)** 하는 정밀한 메커니즘을 가지고 있습니다.

> Confluence 출처: [Error Handling Path](https://mangoboost.atlassian.net/wiki/spaces/RDMADV/pages/1335525456/Error+Handling+Path)

## 핵심 개념

### 1. 시작점 — `RDMASQDestroy(err)` / `RDMAQPDestroy(err)`

| 파라미터 | 값 | 설명 |
|---------|---|-----|
| `err` | 0 (기본) | 정상 QP destroy — outstanding 잔존 시 fatal |
| `err` | 1 | 에러 QP destroy — outstanding 허용, flush 수행 |

```systemverilog
this.RDMAQPDestroy(.t_seqr(seqr), .qp_num(qp_num), .err(1));
// → 각 comparator/tracker 가 flushQP() 수행
```

### 2. 경로 1: Driver → QP Error State

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

### 3. 경로 2: CQ Handler → Error CQE

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

### 4. 경로 3: Error CQ 백그라운드 모니터링

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

### 5. 컴포넌트별 에러 시 동작

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

### 6. `vrdma_cfg` 글로벌 체커 제어

| 필드 | 기본값 | 의도 |
|------|-------|-----|
| `has_dma_chk` | YES | DMA 체커 enable/disable |
| `has_packet_chk` | YES | 패킷 체커 enable/disable |
| `has_data_chk` | YES | 데이터 체커 enable/disable |

> 현재는 로그용 (`start_of_simulation_phase` 출력). 향후 체커 조건부 연결에 활용 예정.

## Static Flag 요약

| Flag | 위치 | 기본값 | 영향 범위 |
|------|------|-------|----------|
| `vrdma_1side_compare::err_enabled` | data_env | 0 | 1side comparator — 모든 QP deregister 시 flush |
| `vrdma_2side_compare::err_enabled` | data_env | 0 | 2side comparator — 동일 |
| `vrdma_imm_compare::err_enabled` | data_env | 0 | IMM comparator — 동일 |
| `vrdma_c2h_tracker::err_enabled` | dma_env | 0 | C2H tracker — 매칭 실패 skip + deregister 에러 등록 |
| `vrdma_cq_handler::enable_error_cq_poll` | agent | 1 | Error CQ 백그라운드 폴링 on/off |
| `vrdma_pkt_base_monitor::turn_off` | network_env | 0 | 패킷 모니터 on/off |

## 적용 범위 비교 — 무엇을 어떤 단위로 끄나?

| 단위 | 메커니즘 | 적용 범위 | 사용 시나리오 |
|------|---------|----------|------------|
| 단일 cmd | `cmd.expected_error = 1` | 한 verb 발행만 | 특정 read 가 RAE 를 받기를 예상할 때 |
| 단일 QP | `qp.setErrState(1)` (자동: SQDestroy.err / 에러 CQE) | 해당 QP 의 모든 후속 verb | 한 QP 에 대한 광범위 에러 테스트 |
| 모든 QP, 한 컴포넌트 | static `err_enabled = 1` | 해당 comparator/tracker 전체 | 실험적 fault injection 시 검증 통째로 완화 |
| 컴포넌트 자체 OFF | `enable_error_cq_poll = 0` / `turn_off = 1` | 해당 컴포넌트 전부 | 에러 CQ / 패킷 모니터 자체를 비활성화 |

## 에러 테스트 시퀀스 작성 패턴

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

## 디버깅 지침

| 증상 | 의심 |
|------|------|
| 정상 QP 인데 `flushQP` 호출됨 | `err_enabled = 1` 로 잘못 켜져 있음 |
| 에러 QP destroy 후 c2h_tracker fatal | `err=1` 누락 (`F-C2H-TBERR-0001`) |
| 백그라운드 error CQ 모니터에서 fatal | `enable_error_cq_poll` 끄지 않음 — 의도라면 끄기 |
| 정상 verb 가 silently skip 되는 것처럼 보임 | 이전 verb 가 에러 CQE 를 받아 QP 가 ErrQP 로 전이됨 — `t_seqr.wc_error_status[qp_num]` 확인 |

## 핵심 정리

- 에러 처리는 3-경로 — driver(SQDestroy.err), cq_handler(에러 CQE), 백그라운드 monitorErrCQ
- 게이트는 3-단위 — per-cmd(`expected_error`), per-QP(`isErrQP`), per-component(`err_enabled` static)
- ErrQP 의 WQE 는 `completed_wqe_ap` 로 전달되지 않아 scoreboard 가 검증 제외
- `RDMAQPDestroy(.err(1))` 가 모든 횡단 컴포넌트의 `flushQP()` 를 트리거하여 깨끗한 정리

## 다음 모듈
[Module 07 — H2C / C2H QID Reference](07_h2c_c2h_qid_map.md): DMA 인터페이스의 QID 로 어느 서브시스템이 동작했는지 즉시 식별.

[퀴즈 풀어보기 →](quiz/06_error_handling_path_quiz.md)
