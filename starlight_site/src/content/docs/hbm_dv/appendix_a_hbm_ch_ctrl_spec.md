---
title: "부록 A — hbm_ch_ctrl 스펙"
---

:::caution[교육용 가상 IP입니다]
`hbm_ch_ctrl`은 **이 코스가 학습을 위해 정의한 가상 IP**이며, 실제 제조사의 내부 설계가 아닙니다.
다만 그 구조적 성질 — CA 버스를 공유하는 pseudo-channel, 분리된 row/column 커맨드 흐름, mode register, 오류 검출·보고, 테스트 모드 — 은 [선행 코스](../../hbm/)에서 공개 자료로 근거를 확보한 실제 HBM의 특성을 반영했습니다.

**스펙을 우리가 직접 쓰기 때문에** *"스펙에서 검증 항목을 도출하는"* 과정 전체를 보여줄 수 있습니다. 이것이 직무 기술서의 우대사항 *"Spec 기반 Custom UVM Agent A-to-Z 개발"* 이 요구하는 바로 그 작업입니다.
:::

이 문서는 관통 사례의 **단일 진실 공급원(single source of truth)** 입니다. Ch03 이후의 모든 챕터가 여기 정의된 신호명·필드명·규칙을 그대로 인용합니다. 챕터와 이 문서가 어긋나 보이면 **이 문서가 옳습니다.**

---

## A.1 개요

`hbm_ch_ctrl`은 HBM base die 안에서 **하나의 채널**(pseudo-channel 2개)을 담당하는 컨트롤러입니다. 상위 로직으로부터 읽기/쓰기 요청을 받아 DRAM 커맨드로 변환·스케줄링하고, 채널 상태와 오류를 보고합니다.

```d2
direction: right

HOST: "상위 로직 / 호스트 측" { style.fill: "#ffe0b2"; style.font-color: "#0A0F25" }

DUT: "hbm_ch_ctrl (DUT)" {
  style.fill: "#bbdefb"
  style.font-color: "#0A0F25"
  sched: "요청 큐 · 스케줄러\n뱅크 상태 추적"
  arb: "CA 중재\n(pseudo-channel 공유)"
  csr: "CSR (Mode Register)"
  err: "오류 검출 · 보고"
}

DRAM: "DRAM (core die)\n— 검증 환경에서는 모델" { style.fill: "#f5f5f5"; style.font-color: "#0A0F25" }

HOST -> DUT: "CCI\n비표준 제어 인터페이스\n(상용 VIP 없음 → Custom Agent 대상)"
DUT -> DRAM: "DCMD\nrow / column 커맨드 (분리)\n+ DQ 데이터"
```

**세 인터페이스**

| 이름 | 방향 | 역할 | 검증 도구 |
|---|---|---|---|
| **CCI** (Channel Control Interface) | 호스트 → DUT | 읽기/쓰기 요청, CSR 접근 | ⚠️ **비표준 → Custom UVM Agent 자체 개발** |
| **DCMD** (DRAM Command Interface) | DUT → DRAM | row/column 커맨드, DQ 데이터 | Monitor + DRAM behavioral model |
| **CSR** | CCI를 통해 접근 | 동작 설정과 상태 조회 | RAL 또는 직접 시퀀스 |

## A.2 파라미터

구성값은 전부 파라미터입니다. 선행 코스 21항목 **#8(구성값 전면 파라미터화)** 에 대응합니다.

| 파라미터 | 기본값 | 설명 |
|---|---|---|
| `NUM_PC` | 2 | pseudo-channel 개수 |
| `NUM_BANK` | 16 | pseudo-channel당 뱅크 수 |
| `DATA_W` | 32 | 데이터 폭 (bit) — HBM3의 pseudo-channel 폭과 정합 |
| `ADDR_W` | 34 | 바이트 주소 폭 |
| `ID_W` | 4 | 트랜잭션 ID 폭 (최대 미해결 요청 수 = 2^`ID_W`) |
| `ROW_W` | 16 | row 주소 폭 |
| `COL_W` | 10 | column 주소 폭 |
| `MAX_LEN` | 16 | 최대 버스트 beat 수 |

## A.3 클럭과 리셋

| 신호 | 설명 |
|---|---|
| `clk` | 단일 클럭. 모든 인터페이스가 동기 |
| `rst_n` | 비동기 assert, 동기 deassert. **active low** |

리셋 해제 직후 `MR_CTRL.EN = 0`입니다. **`EN`을 1로 쓰기 전의 모든 데이터 요청은 거부**되며 `INTERNAL_ERR`로 응답합니다.

## A.4 CCI — Channel Control Interface

비표준 인터페이스입니다. **상용 VIP가 존재하지 않으므로 Custom UVM Agent를 직접 만들어야 합니다** (Ch03).

세 개의 독립 채널로 구성되며, 각 채널은 `valid` / `ready` 핸드셰이크를 사용합니다.

### A.4.1 요청 채널 (호스트 → DUT)

| 신호 | 폭 | 설명 |
|---|---|---|
| `cci_req_valid` | 1 | 요청 유효 |
| `cci_req_ready` | 1 | DUT 수락 가능 |
| `cci_req_op` | 2 | `0`=READ, `1`=WRITE, `2`=CSR_WRITE, `3`=CSR_READ |
| `cci_req_pc` | 1 | pseudo-channel 선택 (0 / 1) |
| `cci_req_addr` | `ADDR_W` | 바이트 주소. CSR 접근 시 하위 8비트가 레지스터 오프셋 |
| `cci_req_len` | 4 | 버스트 beat 수 − 1 (0이면 1 beat) |
| `cci_req_id` | `ID_W` | 트랜잭션 ID |
| `cci_req_par` | 1 | 위 필드 전체에 대한 **홀수 패리티** |

### A.4.2 쓰기 데이터 채널 (호스트 → DUT)

| 신호 | 폭 | 설명 |
|---|---|---|
| `cci_wd_valid` / `cci_wd_ready` | 1 | 핸드셰이크 |
| `cci_wd_data` | `DATA_W` | 쓰기 데이터 |
| `cci_wd_last` | 1 | 버스트 마지막 beat |
| `cci_wd_par` | 1 | `cci_wd_data`에 대한 홀수 패리티 |

### A.4.3 응답 채널 (DUT → 호스트)

| 신호 | 폭 | 설명 |
|---|---|---|
| `cci_rsp_valid` / `cci_rsp_ready` | 1 | 핸드셰이크 |
| `cci_rsp_id` | `ID_W` | 대응하는 요청의 ID |
| `cci_rsp_data` | `DATA_W` | 읽기 데이터 (WRITE 응답에서는 무의미) |
| `cci_rsp_last` | 1 | 버스트 마지막 beat |
| `cci_rsp_err` | 2 | `0`=OK, `1`=PARITY_ERR, `2`=ADDR_ERR, `3`=INTERNAL_ERR |

### A.4.4 SystemVerilog 인터페이스 선언

```systemverilog
interface hbm_ch_ctrl_cci_if #(
  parameter int DATA_W = 32,
  parameter int ADDR_W = 34,
  parameter int ID_W   = 4
) (input logic clk, input logic rst_n);

  // 요청 채널
  logic              req_valid, req_ready;
  logic [1:0]        req_op;
  logic              req_pc;
  logic [ADDR_W-1:0] req_addr;
  logic [3:0]        req_len;
  logic [ID_W-1:0]   req_id;
  logic              req_par;

  // 쓰기 데이터 채널
  logic              wd_valid, wd_ready;
  logic [DATA_W-1:0] wd_data;
  logic              wd_last, wd_par;

  // 응답 채널
  logic              rsp_valid, rsp_ready;
  logic [ID_W-1:0]   rsp_id;
  logic [DATA_W-1:0] rsp_data;
  logic              rsp_last;
  logic [1:0]        rsp_err;

  clocking drv_cb @(posedge clk);
    output req_valid, req_op, req_pc, req_addr, req_len, req_id, req_par;
    input  req_ready;
    output wd_valid, wd_data, wd_last, wd_par;
    input  wd_ready;
    output rsp_ready;
    input  rsp_valid, rsp_id, rsp_data, rsp_last, rsp_err;
  endclocking

  clocking mon_cb @(posedge clk);
    input req_valid, req_ready, req_op, req_pc, req_addr, req_len, req_id, req_par;
    input wd_valid, wd_ready, wd_data, wd_last, wd_par;
    input rsp_valid, rsp_ready, rsp_id, rsp_data, rsp_last, rsp_err;
  endclocking

  modport DRV (clocking drv_cb, input clk, rst_n);
  modport MON (clocking mon_cb, input clk, rst_n);
endinterface
```

## A.5 DCMD — DRAM Command Interface

DUT가 DRAM(검증 환경에서는 모델)으로 내보내는 인터페이스입니다. 선행 코스에서 확인한 대로 **row 계열과 column 계열이 분리**되어 병렬 발행이 가능합니다.

### A.5.1 Row 커맨드 채널

| 신호 | 폭 | 설명 |
|---|---|---|
| `row_cmd_valid` | 1 | 유효 |
| `row_cmd` | 2 | `0`=NOP, `1`=ACT, `2`=PRE, `3`=REF |
| `row_pc` | 1 | 대상 pseudo-channel |
| `row_bank` | 4 | 대상 뱅크 |
| `row_addr` | `ROW_W` | row 주소 |

### A.5.2 Column 커맨드 채널

| 신호 | 폭 | 설명 |
|---|---|---|
| `col_cmd_valid` | 1 | 유효 |
| `col_cmd` | 2 | `0`=NOP, `1`=RD, `2`=WR, `3`=예약 |
| `col_pc` | 1 | 대상 pseudo-channel |
| `col_bank` | 4 | 대상 뱅크 |
| `col_addr` | `COL_W` | column 주소 |

### A.5.3 데이터 채널

| 신호 | 폭 | 설명 |
|---|---|---|
| `dq_wr_valid` / `dq_wr_data` | 1 / `DATA_W` | DUT → DRAM |
| `dq_rd_valid` / `dq_rd_data` | 1 / `DATA_W` | DRAM → DUT |

## A.6 동작 규칙 (검증 대상)

여기 나열된 규칙이 **Ch09 assertion의 원본**입니다. 각 규칙에 식별자를 부여합니다.

### A.6.1 핸드셰이크 규칙

| ID | 규칙 |
|---|---|
| **R1** | `valid`가 assert된 후 `ready`가 assert될 때까지 `valid`는 유지되어야 한다 |
| **R2** | `valid`가 assert된 상태에서 `ready`를 기다리는 동안 해당 채널의 payload는 변하지 않아야 한다 |

### A.6.2 CA 공유 규칙 — 이 IP의 핵심

| ID | 규칙 |
|---|---|
| **R3** | `row_cmd_valid`와 `col_cmd_valid`가 같은 사이클에 동시에 1인 경우, `row_pc == col_pc` 여야 한다 |

**왜 이런 규칙인가**: 선행 코스 [Ch04](../../hbm/04_channels_addressing/)에서 확인한 대로 두 pseudo-channel은 **CA 버스를 공유**합니다(semi-independent). row와 column 커맨드 인터페이스는 분리되어 병렬 발행이 가능하지만, **서로 다른 pseudo-channel의 커맨드를 같은 사이클에 CA로 내보낼 수는 없습니다.**

이 규칙이 선행 코스 21항목 **#13(공유 CA 버스의 경합·중재 규칙 검사)** 의 구체적 형태입니다.

### A.6.3 뱅크 상태·타이밍 규칙

각 (pc, bank) 쌍은 **IDLE / ACTIVE** 상태를 가집니다.

| ID | 규칙 |
|---|---|
| **R4** | IDLE 상태의 뱅크에 `RD`/`WR`를 발행해서는 안 된다 (선행 `ACT` 필요) |
| **R5** | ACTIVE 상태의 뱅크에 `ACT`를 다시 발행해서는 안 된다 (선행 `PRE` 필요) |
| **R6** | 같은 뱅크에서 `ACT` → `RD`/`WR` 사이 간격 ≥ `MR_TIMING.tRCD_CYC` 사이클 |
| **R7** | 같은 뱅크에서 `PRE` → `ACT` 사이 간격 ≥ `MR_TIMING.tRP_CYC` 사이클 |
| **R8** | 같은 뱅크에서 `ACT` → `PRE` 사이 간격 ≥ `MR_TIMING.tRAS_CYC` 사이클 |

R6~R8의 기준값이 **CSR 설정값**이라는 점이 중요합니다 — 21항목 **#17(설정과 효과의 분리 검증)** 이 여기서 검증 가능해집니다. 값을 바꾸면 실제 간격이 바뀌어야 합니다.

### A.6.4 응답 규칙

| ID | 규칙 |
|---|---|
| **R9** | `cci_rsp_id`는 아직 완료되지 않은 요청의 `cci_req_id` 중 하나여야 한다 |
| **R10** | 한 트랜잭션의 응답 beat 수는 `cci_req_len + 1`과 같아야 하며, 마지막 beat에서만 `rsp_last`가 1이다 |
| **R11** | 응답은 요청과 **순서가 다를 수 있다**(out-of-order). 단 같은 `id`의 beat들은 순서를 지킨다 |

### A.6.5 오류 규칙

| ID | 규칙 |
|---|---|
| **R12** | `MR_ERR_EN.PAR_CHK_EN = 1`이고 `cci_req_par`가 틀린 요청은 **수행되지 않고** `PARITY_ERR`로 응답한다 |
| **R13** | `MR_ERR_EN.PAR_CHK_EN = 0`이면 패리티를 검사하지 않는다 |
| **R14** | 패리티 오류 발생 시 `MR_ERR_STS.PAR_ERR`이 set되며, **1을 써야 clear된다**(W1C) |
| **R15** | 주소가 유효 범위를 벗어나면 `ADDR_ERR`로 응답한다 |
| **R16** | `MR_CTRL.EN = 0` 상태에서 도착한 READ/WRITE 요청은 `INTERNAL_ERR`로 응답한다 |

R12와 R13의 쌍이 21항목 **#16(에러 주입을 시나리오의 독립 축으로)** 과 **#17(설정 효과)** 을 동시에 만듭니다 — 오류를 주입해야만 검증되고, 그 동작이 설정에 의존합니다.

### A.6.6 테스트 모드 규칙

| ID | 규칙 |
|---|---|
| **R17** | `MR_TEST.TEST_MODE_REQ`에 1을 쓰면, DUT는 **미해결 트랜잭션을 모두 완료한 뒤** `MR_TEST.TEST_MODE_ACK`를 1로 만든다 |
| **R18** | `TEST_MODE_ACK = 1`인 동안 `row_cmd_valid`와 `col_cmd_valid`는 0이어야 한다 |
| **R19** | `TEST_MODE_ACK = 1`인 동안 도착한 READ/WRITE 요청은 `INTERNAL_ERR`로 응답한다 |
| **R20** | `TEST_MODE_REQ`를 0으로 쓰면 `TEST_MODE_ACK`가 0이 되고 mission mode로 복귀한다 |

R17~R20이 21항목 **#18(테스트 모드 상태 전이 커버리지)** 의 대상입니다.

## A.7 CSR (Mode Register) 맵

CCI의 `op = CSR_WRITE / CSR_READ`로 접근합니다. `cci_req_addr[7:0]`이 오프셋입니다.

| 오프셋 | 이름 | 접근 | 필드 |
|---|---|---|---|
| `0x00` | `MR_CTRL` | RW | `[0]` EN · `[1]` AUTO_PRE · `[3:2]` SCHED_MODE |
| `0x04` | `MR_TIMING` | RW | `[7:0]` tRCD_CYC · `[15:8]` tRP_CYC · `[23:16]` tRAS_CYC |
| `0x08` | `MR_ERR_EN` | RW | `[0]` PAR_CHK_EN · `[1]` ADDR_CHK_EN |
| `0x0C` | `MR_ERR_STS` | W1C | `[0]` PAR_ERR · `[1]` ADDR_ERR · `[7:4]` ERR_ID |
| `0x10` | `MR_TEST` | RW/RO | `[0]` TEST_MODE_REQ (RW) · `[1]` TEST_MODE_ACK (RO) |
| `0x14` | `MR_STATUS` | RO | `[0]` IDLE · `[1]` BUSY · `[3:2]` ACTIVE_PC |

**`SCHED_MODE` 값**

| 값 | 이름 | 동작 |
|---|---|---|
| `0` | IN_ORDER | 요청을 도착 순서대로 처리 |
| `1` | BANK_FIRST | 이미 ACTIVE인 뱅크를 대상으로 하는 요청을 우선 처리 |
| `2` | PC_RR | 두 pseudo-channel을 round-robin으로 번갈아 처리 |
| `3` | — | 예약 |

**리셋값**: `MR_CTRL = 0`, `MR_TIMING = {tRAS:0x10, tRP:0x08, tRCD:0x08}`, `MR_ERR_EN = 0x3`, 나머지 0.

### A.7.1 주소 상수

본문 챕터의 코드 예제는 오프셋을 직접 쓰지 않고 아래 상수를 사용합니다.

```systemverilog
package hbm_ch_ctrl_csr_pkg;
  // 스펙 A.7 — CSR 오프셋 (cci_req_addr[7:0])
  localparam bit [7:0] MR_CTRL_ADDR    = 8'h00;
  localparam bit [7:0] MR_TIMING_ADDR  = 8'h04;
  localparam bit [7:0] MR_ERR_EN_ADDR  = 8'h08;
  localparam bit [7:0] MR_ERR_STS_ADDR = 8'h0C;
  localparam bit [7:0] MR_TEST_ADDR    = 8'h10;
  localparam bit [7:0] MR_STATUS_ADDR  = 8'h14;
endpackage
```

**왜 상수로 두는가**: 오프셋을 코드에 직접 쓰면 스펙 개정 시 **모든 시나리오를 찾아 고쳐야** 합니다. 상수 하나만 바꾸면 되도록 두는 것이, 21항목 **#8(구성값 파라미터화)** 이 레지스터 주소에 적용된 형태입니다.

RAL을 사용하는 경우 이 상수 대신 레지스터 모델의 이름으로 접근합니다 — [UVM 코스 Module 07](../../uvm/) 참고.

`SCHED_MODE`가 21항목 **#17**의 가장 좋은 소재입니다 — 값을 바꾸면 **커맨드 발행 순서가 실제로 달라져야** 하며, 이것은 레지스터 read/write 테스트로는 전혀 확인되지 않습니다.

## A.8 검증 관점 인덱스

이 스펙의 각 부분이 선행 코스 21항목 중 무엇을 다루게 되는지, 그리고 어느 챕터에서 쓰이는지 정리합니다.

| 스펙 항목 | 21항목 | 쓰이는 챕터 |
|---|---|---|
| CCI 비표준 인터페이스 (A.4) | #7, #20 | **Ch03** (Custom Agent), Ch04 (사느냐 만드느냐) |
| 파라미터 (A.2) | #8 | Ch06 (환경 파라미터화) |
| R1·R2 핸드셰이크 (A.6.1) | #3 | Ch09 |
| **R3 CA 공유** (A.6.2) | **#13** | **Ch09** |
| R4·R5 뱅크 상태 (A.6.3) | #14 | Ch09 |
| R6~R8 타이밍 (A.6.3) | #3, #17 | Ch09, Ch08 |
| R9~R11 응답·OoO (A.6.4) | #15 | Ch09 (scoreboard 독립 재현) |
| R12~R16 오류 (A.6.5) | #16, #17 | **Ch08** (에러 주입) |
| R17~R20 테스트 모드 (A.6.6) | #18 | Ch08, **Ch11** |
| `SCHED_MODE` (A.7) | #2, #17 | Ch08 (성능·설정 효과) |
| 주소 → (pc, bank, row, col) 디코드 | **#15** | **Ch09** (scoreboard) |

## A.9 변경 이력

이 문서는 단일 진실 공급원이므로 변경 시 이력을 남깁니다.

| 버전 | 변경 |
|---|---|
| v1.0 | 최초 정의 — CCI/DCMD/CSR, 규칙 R1~R20, 파라미터 8종 |
| v1.1 | A.7.1 주소 상수 추가 — 본문 코드가 사용하는 `MR_*_ADDR` 정의를 스펙에 명시 |

---

**다음**: [Ch01 — 무엇을 검증하는가](../01_what_we_verify/)에서 이 IP를 놓고 DUT 경계를 확정하고, 검증 업무의 한 주기를 훑습니다. 스펙을 실제로 쓰기 시작하는 것은 [Ch03 — Custom UVM Agent A-to-Z](../03_custom_uvm_agent/)입니다.
