---
title: "Module 03 — RVFI & RVVI"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Describe** RVFI 가 코어 retire 시점에 노출하는 신호 집합과 각 신호가 무슨 architectural 정보를 담는지 기술할 수 있다.
- **Differentiate** RVFI(코어가 노출하는 retire 신호 인터페이스) 와 RVVI(DV 서브시스템 통합 표준) 의 역할 경계를 구분할 수 있다.
- **Trace** retire monitor 가 RVFI 신호를 샘플해 retire transaction 으로 변환하는 흐름을 추적할 수 있다.
- **Apply** 같은 RVFI 신호가 시뮬레이션 monitor 와 형식 검증(riscv-formal) 양쪽에서 어떻게 재사용되는지 적용 사례로 설명할 수 있다.
- **Evaluate** 검증용 트레이스 인터페이스를 표준화(RVVI)했을 때 서로 다른 코어·ISS 를 같은 하네스에 꽂는 이점을 평가할 수 있다.
:::
:::note[사전 지식]
- [Module 02 — Step-and-Compare Lockstep](../02_step_and_compare/) — retire 시점 비교가 필요로 하는 정보
- [UVM M02](../../uvm/02_agent_driver_monitor/) — monitor 가 신호를 트랜잭션으로 변환하는 패턴
- [Computer Architecture M03](../../computer_architecture/03_ooo_branch_prediction/) — retire/commit
:::
---

## 1. Why care? — 비교는 알겠는데, 그 정보는 코어 밖으로 어떻게 나오나

### 1.1 시나리오 — 코어 내부를 헤집는 monitor

[M02 의 step-and-compare](../02_step_and_compare/) 는 "retire 한 명령의 PC·rd·CSR 변화를 본다"고 했습니다. 그런데 그 정보를 어디서 가져올까요? 표준 인터페이스가 없으면, 검증팀은 코어마다 내부 신호를 찾아 헤맵니다.

```systemverilog
// 표준 인터페이스 없이 — 코어 내부 신호를 직접 더듬는 monitor (안티패턴)
assign retired_pc = dut.u_core.u_wb_stage.r_pc_q;        // 코어마다 경로 다름
assign retired_rd = dut.u_core.u_rf.wr_addr_int;          // 리비전마다 이름 바뀜
assign retired_val= dut.u_core.u_rf.wr_data_pipe3_masked; // 추측 포함? 확신 못함
```

이 방식은 코어가 바뀌거나 RTL 리비전이 올라가면 즉시 깨지고, "이 값이 _retire 된_ 값이 맞는지"조차 확신하기 어렵습니다. RVFI 는 이 문제를 **코어가 검증용으로 _표준화된_ retire 신호를 직접 내보내게** 해서 없앱니다.

```systemverilog
// RVFI — 코어가 검증용으로 약속한 신호. 코어가 달라도 이름이 같다
assign retired_pc  = rvfi_pc_rdata;    // 이 사이클에 retire 된 명령의 PC
assign retired_rd  = rvfi_rd_addr;     // 기록한 레지스터 번호 (없으면 0)
assign retired_val = rvfi_rd_wdata;    // 기록한 값 (architectural, 추측 아님)
// rvfi_valid 가 1 인 사이클 = 정확히 한 명령이 retire 된 사이클
```

### 1.2 두 인터페이스, 두 계층

이 모듈은 두 가지를 구분합니다. **RVFI** 는 _코어 한 개_ 가 노출하는 retire 신호 인터페이스 — "이 명령이 무엇을 했나"를 알려줍니다. **RVVI** 는 그 위에서 _DV 서브시스템 전체_(코어 + reference model + 트레이스 비교)를 묶는 통합 표준 — "서로 다른 코어·ISS 를 같은 하네스에 꽂게" 합니다. 이 모듈을 건너뛰면 monitor 가 코어 내부에 결합돼 재사용성을 잃고, 시뮬레이션과 형식 검증이 _다른_ 신호를 봐서 두 흐름이 갈라집니다.

---

## 2. Intuition — 코어가 내미는 영수증, 그리고 표준 콘센트

:::tip[💡 한 줄 비유]
**RVFI** ≈ **코어가 명령마다 내미는 _영수증_**.<br>
"방금 PC 0x1000 의 ADDI 를 처리했고, x5 에 0x41 을 적었으며, CSR 은 안 건드렸다" — retire 할 때마다 이 영수증(`rvfi_valid` + 내역 신호)을 내밉니다. monitor 는 코어 내부를 뒤질 필요 없이 영수증만 읽습니다.<br>
**RVVI** ≈ **그 영수증을 꽂는 _표준 콘센트_**. 어느 코어든 같은 모양의 콘센트를 쓰면, 같은 비교 하네스(reference model + scoreboard)를 그대로 꽂을 수 있습니다.
:::

### 한 장 그림 — RVFI 신호가 두 검증 흐름으로

```d2
direction: right

CORE: "**RTL 코어**\n(RVFI 구현)\nretire 시 신호 노출"
RVFI: "**RVFI 신호**\nrvfi_valid\nrvfi_pc_rdata/wdata\nrvfi_rd_addr/wdata\nrvfi_mem_addr/rdata/wdata\nrvfi_intr / rvfi_trap"

SIM: "**시뮬레이션 흐름**\nretire monitor →\nscoreboard vs ISS\n(Module 02·04)"
FORMAL: "**형식 검증 흐름**\nriscv-formal\nRVFI ↔ ISA 형식 모델\n(Module 06)"

CORE -> RVFI: "노출"
RVFI -> SIM: "같은 신호 재사용"
RVFI -> FORMAL: "같은 신호 재사용"
```

### 왜 이 구조인가 — Design rationale

세 가지 요구의 교집합입니다.

1. **monitor 가 코어 내부에 결합되면 안 된다** → 코어가 _표준 retire 신호_(RVFI)를 직접 노출. 코어/리비전이 바뀌어도 monitor 코드 불변.
2. **시뮬레이션과 형식 검증이 같은 진실을 봐야 한다** → 둘 다 _같은_ RVFI 신호를 소비. 한 인터페이스가 두 검증 방법론을 통합.
3. **서로 다른 코어·ISS 를 같은 하네스에 꽂고 싶다** → RVVI 가 트레이스·reference-model 연동을 표준화해, 하네스 재사용을 인터페이스 수준에서 보장.

이 세 요구가 곧 **"RVFI(코어 노출 신호) + RVVI(서브시스템 통합 표준)"** 두 계층의 설계 근거입니다.

---

## 3. 작은 예 — 한 명령의 retire 가 RVFI 로 나와 transaction 이 되기까지

가장 단순한 시나리오. ADDI 한 명령이 retire 되면서 RVFI 신호가 한 사이클 valid 가 되고, retire monitor 가 이를 transaction 으로 만드는 과정입니다.

### 단계별 다이어그램

```d2
direction: down

S1: "**① RTL retire**\nADDI x5, x5, 1 이 WB 단계 통과\n→ 이 사이클에 rvfi_valid=1"
S2: "**② RVFI 신호 세팅**\nrvfi_pc_rdata=0x1000\nrvfi_insn=0x00128293\nrvfi_rd_addr=5, rvfi_rd_wdata=0x41\nrvfi_trap=0, rvfi_intr=0"
S3: "**③ retire monitor 샘플**\n@(posedge clk iff rvfi_valid)\n신호들을 retire_item 으로"
S4: "**④ analysis port broadcast**\nap.write(retire_item)\n→ scoreboard / coverage 로 fan-out"

S1 -> S2 -> S3 -> S4
```

### 단계별 의미

| Step | 누가 | 무엇을 | 핵심 |
|---|---|---|---|
| ① | RTL 코어 | retire 사건에 `rvfi_valid=1` 세팅 (1 사이클) | valid=1 사이클 = 명령 1 개 retire |
| ② | RTL 코어 | retire 한 명령의 architectural 정보를 RVFI 신호에 출력 | rd_wdata 는 _추측 아닌_ 확정값 |
| ③ | retire monitor | `rvfi_valid` 에서 신호들을 샘플 → retire_item | 코어 내부 무관, RVFI 만 봄 |
| ④ | analysis port | scoreboard·coverage 로 broadcast | [UVM M05 의 1:N fan-out](../../uvm/05_tlm_scoreboard_coverage/) |

### retire monitor 의 형태

```systemverilog
// RVFI 신호를 보는 retire monitor — 코어 내부에 의존하지 않는다
class rvfi_monitor extends uvm_monitor;
  `uvm_component_utils(rvfi_monitor)
  virtual rvfi_if vif;                       // RVFI 신호 묶음 인터페이스
  uvm_analysis_port #(retire_item) ap;

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    ap = new("ap", this);
    if (!uvm_config_db#(virtual rvfi_if)::get(this, "", "rvfi_vif", vif))
      `uvm_fatal("NOVIF", "rvfi_vif missing")
  endfunction

  task run_phase(uvm_phase phase);
    forever begin
      // rvfi_valid 가 1 인 사이클 = 정확히 한 명령 retire
      @(posedge vif.clk iff vif.rvfi_valid);
      retire_item it = retire_item::type_id::create("it");
      it.pc       = vif.rvfi_pc_rdata;
      it.insn     = vif.rvfi_insn;
      it.rd_addr  = vif.rvfi_rd_addr;        // 0 이면 레지스터 기록 없음
      it.rd_wdata = vif.rvfi_rd_wdata;       // architectural 확정값
      it.trap     = vif.rvfi_trap;           // 이 명령이 trap 을 일으켰나
      it.intr     = vif.rvfi_intr;           // 인터럽트 진입의 첫 명령인가
      ap.write(it);                          // scoreboard/coverage 로 broadcast
    end
  endtask
endclass
```

핵심: **monitor 는 `dut.u_core.*` 같은 내부 경로를 한 번도 참조하지 않습니다.** RVFI 신호만 보므로, 코어가 in-order 든 OoO 든, 리비전이 올라가든 monitor 코드는 그대로입니다. (위 신호명은 RVFI 사양 기반 — 외부 표준 지식.)

---

## 4. 일반화 — RVFI 신호 분류, RVVI 의 계층, 두 흐름 통합

### 4.1 RVFI 신호 분류 (외부 표준 지식, github.com/YosysHQ/riscv-formal)

| 그룹 | 대표 신호 | 의미 |
|---|---|---|
| **메타데이터** | `rvfi_valid`, `rvfi_order`, `rvfi_insn` | retire 발생 여부, 프로그램 순서 번호, 명령 인코딩 |
| **PC** | `rvfi_pc_rdata`, `rvfi_pc_wdata` | 실행된 명령의 PC, 다음 PC(분기 결과 포함) |
| **레지스터** | `rvfi_rs1/rs2_addr/rdata`, `rvfi_rd_addr/rdata` | 읽은 소스 레지스터, 기록한 목적 레지스터 |
| **메모리** | `rvfi_mem_addr`, `rvfi_mem_rdata/wdata`, `rvfi_mem_rmask/wmask` | load/store 의 주소·데이터·바이트 마스크 |
| **트랩/인터럽트** | `rvfi_trap`, `rvfi_intr`, `rvfi_halt` | 이 명령이 예외를 일으켰나, 인터럽트 진입 첫 명령인가 |
| **모드** | `rvfi_mode`, `rvfi_ixl` | 실행 당시 privilege mode, XLEN |

이 신호 집합은 [M02 가 비교하던 architectural state](../02_step_and_compare/) 와 정확히 대응합니다 — PC, 레지스터, 메모리, CSR/trap. 즉 RVFI 는 step-and-compare 가 필요로 하는 정보를 _표준 형태로_ 노출하는 인터페이스입니다.

### 4.2 RVVI — 서브시스템 통합 계층 (외부 표준 지식, github.com/riscv-verification/RVVI)

RVFI 가 _코어 한 개_ 의 신호라면, RVVI 는 _검증 서브시스템 전체_ 를 묶는 draft open standard 입니다.

```d2
direction: down

CORE: "**RTL 코어**\nRVVI-TRACE 로 retire 정보 출력\n(RVFI 와 유사 역할)"
TRACE: "**RVVI-TRACE**\n표준 트레이스 인터페이스\n어느 코어든 같은 모양"
REF: "**Reference model API**\n표준 연동 (RVVI-VLG/API)\nISS 를 꽂는 약속"
HARNESS: "**비교 하네스**\nstep-and-compare\n코어·ISS 교체 가능"

CORE -> TRACE
TRACE -> HARNESS
REF -> HARNESS
```

| 구분 | RVFI | RVVI |
|---|---|---|
| 범위 | 코어 한 개의 retire 신호 | DV 서브시스템 통합(코어+ISS+비교) |
| 주 사용처 | riscv-formal, retire monitor | step-and-compare 하네스의 코어/ISS 교체성 |
| 형태 | RTL 신호 묶음 | 트레이스 인터페이스 + reference-model 연동 API |
| 표준 상태 | riscv-formal 사실상 표준 | RISC-V 진영 draft open standard |

핵심 구분: **RVFI 는 "코어가 무엇을 했나"를 _노출_ 하고, RVVI 는 그 정보를 가지고 "서로 다른 코어·ISS 를 _같은 하네스에 꽂는_" 통합을 표준화**합니다.

### 4.3 한 인터페이스, 두 검증 흐름

RVFI 의 가장 큰 가치는 _같은 신호_ 가 시뮬레이션과 형식 검증 양쪽에서 재사용된다는 점입니다.

| 흐름 | RVFI 를 어떻게 쓰나 | 본 코스 연결 |
|---|---|---|
| 시뮬레이션 (동적) | retire monitor 가 샘플 → scoreboard 가 ISS 와 비교 | [M04](../04_uvm_core_env/) |
| 형식 검증 (정적) | riscv-formal 이 RVFI ↔ ISA 형식 모델을 명령 단위로 대조 | [M06](../06_riscv_formal/) |

동적·정적 두 흐름이 _같은 진실(RVFI)_ 을 보므로, 한쪽에서 정의한 "올바른 retire 동작"이 다른 쪽에서도 일관됩니다.

---

## 5. 디테일 — valid 의 의미, trap/intr, OoO 코어에서의 RVFI

### 5.1 `rvfi_valid` 와 `rvfi_order` — 명령 1 개의 경계

`rvfi_valid` 가 1 인 사이클이 정확히 _한 명령의 retire_ 를 의미합니다. superscalar 코어는 한 사이클에 여러 명령을 retire 할 수 있으므로, RVFI 는 보통 _채널마다_ 또는 _retire port 마다_ valid 를 둡니다. `rvfi_order` 는 프로그램 순서를 나타내는 단조 증가 번호로, retire 가 여러 포트로 나뉘어도 비교기가 _프로그램 순서_ 를 복원하게 합니다.

```d2
direction: right
C0: "Core retire port 0\nrvfi_valid[0], order=N"
C1: "Core retire port 1\nrvfi_valid[1], order=N+1"
MON: "monitor\norder 로 정렬"
SB: "scoreboard\n프로그램 순서로 ISS 비교"
C0 -> MON
C1 -> MON
MON -> SB: "order 기준 in-order"
```

### 5.2 `rvfi_trap` 과 `rvfi_intr` — 예외 경로의 표시

| 신호 | 1 일 때 의미 | 검증 활용 |
|---|---|---|
| `rvfi_trap` | 이 명령이 trap(예외)을 일으켰다 | 예외 경로 coverage, CSR side-effect 비교 |
| `rvfi_intr` | 이 명령이 인터럽트 핸들러 진입의 첫 명령이다 | 인터럽트 시점을 ISS 에 전달([M02 §4.3](../02_step_and_compare/)) |
| `rvfi_halt` | 이 명령 이후 코어가 정지한다 | 종료 조건 검출 |

특히 `rvfi_intr` 은 [M02 에서 다룬 "비결정 인터럽트 시점의 RTL→ISS 동기화"](../02_step_and_compare/) 를 가능하게 하는 신호입니다 — RTL 이 "이 명령에서 인터럽트로 진입했다"고 알려주면 ISS 도 같은 경계에서 trap 을 산출합니다.

### 5.3 OoO 코어에서의 RVFI — execution 이 아니라 retire 를 노출

OoO 코어는 명령을 순서 없이 execute 하지만, RVFI 는 _retire 시점_ 의 architectural 정보만 노출하도록 약속돼 있습니다. 따라서 `rvfi_rd_wdata` 는 추측 실행 중간값이 아니라 _commit 된 확정값_ 입니다. 이 덕분에 monitor 는 OoO 코어의 복잡한 내부(reservation station, ROB, 추측)를 전혀 몰라도, RVFI 만 보면 [M02 의 retire 시점 비교](../02_step_and_compare/) 를 그대로 할 수 있습니다. RVFI 가 "코어 내부 복잡도를 retire 인터페이스 뒤로 숨기는" 추상화 역할을 하는 셈입니다.

### 5.4 RVFI 는 검증 전용 — 합성에서 제거

RVFI 신호는 _검증을 위해_ 추가된 것이므로, 실제 실리콘 합성 시에는 제거됩니다(보통 `` `ifdef RISCV_FORMAL `` 같은 가드로 감쌈). 즉 RVFI 는 코어의 기능이 아니라 _관찰 가능성(observability)_ 을 위한 보조 출력입니다 — DUT 의 동작을 바꾸지 않고 retire 사건을 밖으로 비추기만 합니다. (이는 [UVM 의 monitor 가 비침투적](../../uvm/02_agent_driver_monitor/)인 것과 같은 철학.)

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'RVFI 신호는 코어의 일반 출력 포트다']
**실제**: RVFI 는 _검증 전용_ observability 신호로, 합성 시 제거됩니다. 코어의 기능적 인터페이스(버스·인터럽트 핀)와 별개이며 DUT 동작을 바꾸지 않습니다.<br>
**왜 헷갈리는가**: RTL 포트로 보여서 기능 포트처럼 느껴지기 때문 — 실제로는 retire 사건을 밖으로 비추는 보조 출력.
:::
:::danger[❓ 오해 2 — 'rvfi_rd_wdata 는 execution 단계의 값일 수 있다']
**실제**: RVFI 는 _retire 시점_ 의 확정값만 노출하도록 약속돼 있습니다. OoO 코어라도 추측 중간값이 아니라 commit 된 값입니다. 그래서 monitor 가 코어 내부를 몰라도 됩니다.<br>
**왜 헷갈리는가**: "신호가 데이터패스에서 나온다 = 추측값이 섞인다" 로 오해하기 때문 — RVFI 의 계약은 retire 값.
:::
:::danger[❓ 오해 3 — 'RVFI 와 RVVI 는 같은 것의 다른 이름이다']
**실제**: RVFI 는 _코어 한 개_ 가 노출하는 retire 신호이고, RVVI 는 그 위에서 _DV 서브시스템 전체_(코어+ISS+비교)를 묶는 통합 표준입니다. 계층이 다릅니다.<br>
**왜 헷갈리는가**: 이름이 비슷하고 둘 다 "verification interface" 라서 — RVFI=신호, RVVI=서브시스템 통합으로 기억.
:::
:::danger[❓ 오해 4 — 'superscalar 코어는 한 사이클에 한 명령만 retire 하니 rvfi_valid 하나면 된다']
**실제**: superscalar 는 한 사이클에 여러 명령을 retire 할 수 있어 retire port 마다 valid 가 필요하고, `rvfi_order` 로 프로그램 순서를 복원해야 합니다.<br>
**왜 헷갈리는가**: 스칼라 코어 경험으로 1 사이클 1 retire 를 가정하기 때문.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| monitor 가 retire 를 하나도 못 봄 | `rvfi_valid` 가 안 토글 / RVFI 가드 미정의 | 코어의 `` `ifdef RISCV_FORMAL `` 빌드 여부 |
| rd_wdata 가 가끔 추측값처럼 보임 | RVFI 노출 시점이 retire 가 아님(코어 RVFI 구현 버그) | 코어의 RVFI 결선이 commit 단에서 나오는지 |
| superscalar 에서 명령 순서가 뒤섞임 | `rvfi_order` 미사용 또는 port 별 valid 누락 | monitor 가 order 로 정렬하는지 |
| 인터럽트 시점이 ISS 와 안 맞음 | `rvfi_intr` 을 ISS 에 전달 안 함 | retire_item.intr → ISS step 반영([M02](../02_step_and_compare/)) |
| 합성에서 RVFI 신호가 남아 면적 증가 | RVFI 가드 미적용 | 합성 스크립트의 define, RVFI ifdef |
| 형식·시뮬이 다른 결론 | 둘이 다른 신호/시점을 봄 | 양쪽이 같은 RVFI 를 소비하는지 |

---

## 7. 핵심 정리 (Key Takeaways)

- **RVFI = 코어가 retire 마다 내미는 _영수증_**: `rvfi_valid` 사이클에 PC·레지스터·메모리·trap 정보를 표준 신호로 노출. monitor 가 코어 내부를 안 뒤져도 됨.
- **RVFI 신호는 retire(commit) 확정값**: OoO 코어라도 추측 중간값이 아닌 commit 된 값을 노출 — 그래서 monitor 가 코어 내부 복잡도와 분리됨.
- **RVVI = 서브시스템 통합 표준**: RVFI 위에서 코어+ISS+비교 하네스를 묶어, 서로 다른 코어·ISS 를 같은 하네스에 꽂게 한다.
- **한 인터페이스, 두 흐름**: 같은 RVFI 신호를 시뮬레이션 monitor 와 형식 검증(riscv-formal) 이 재사용 → 동적·정적이 같은 진실을 본다.
- **검증 전용 observability**: RVFI 는 합성 시 제거되는 비침투적 보조 출력. DUT 동작을 바꾸지 않는다.
- **`rvfi_intr`/`rvfi_trap`** 이 예외·인터럽트 경로를 표시 — [M02 의 비결정 동기화](../02_step_and_compare/)와 예외 coverage 의 입력.

:::caution[실무 주의점]
- RVFI 를 쓰려면 코어가 RVFI 가드(`` `ifdef RISCV_FORMAL `` 등)로 빌드돼야 함 — monitor 가 retire 를 못 보면 여기부터 의심.
- superscalar 는 retire port 별 valid + `rvfi_order` 정렬 필수.
- `rvfi_intr` 을 ISS step 에 반영해야 인터럽트 시점이 lockstep 으로 맞음.
- RVFI 는 retire 값 — execution 중간값을 노출하는 코어 RVFI 구현은 그 자체가 버그.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — RVFI vs 내부 신호 (Bloom: Analyze)]
monitor 가 `dut.u_core.u_rf.wr_data` 같은 코어 내부 신호 대신 RVFI 신호를 보면 무엇이 좋아지고, 무엇을 추가로 신뢰할 수 있게 되는가?
<details>
<summary>정답</summary>

- **재사용성**: 코어 리비전·구현(in-order/OoO)이 바뀌어도 RVFI 신호명·의미는 고정 → monitor 코드 불변. 내부 신호는 리비전마다 이름·경로가 바뀜.
- **의미의 확실성**: RVFI 는 _retire 시점의 확정값_ 을 노출하도록 약속됨 → 그 값이 추측 중간값이 아니라 architectural commit 값임을 신뢰할 수 있음. 내부 신호는 추측이 섞였는지 확신하기 어려움.
- **추상화**: OoO 코어의 ROB·reservation station 을 몰라도 RVFI 만 보면 됨 — 코어 내부 복잡도가 retire 인터페이스 뒤로 숨음.

</details>
:::
:::tip[🤔 Q2 — RVFI/RVVI 역할 (Bloom: Evaluate)]
"우리는 RVFI 만 구현하면 서로 다른 두 코어를 같은 step-and-compare 하네스에 그냥 꽂을 수 있다"는 주장을 평가하라.
<details>
<summary>정답</summary>

**부분적으로만 맞다 — RVFI 는 신호 _노출_ 을 표준화하지만, 하네스 _통합_(코어+ISS+비교 연결)까지 표준화하는 것은 RVVI 의 역할이다.**
- RVFI 가 양쪽 코어에서 같은 모양이면 retire 정보를 _읽는_ 부분은 재사용 가능. 이것만으로도 monitor 는 상당 부분 공유됨.
- 그러나 reference model(ISS) 연동 방식, 트레이스 비교 인터페이스, 코어/ISS 교체 지점은 RVFI 범위 밖. 이를 표준화한 것이 RVVI(RVVI-TRACE + reference-model API).
- 즉 "신호는 RVFI, 서브시스템 통합·교체성은 RVVI" — 두 코어를 _진정으로_ 같은 하네스에 꽂으려면 RVVI 수준의 통합 표준이 함께 있어야 마찰이 없다.

</details>
:::
### 7.2 출처

**Internal**
- [Module 02 — Step-and-Compare Lockstep](../02_step_and_compare/) — RVFI 가 노출하는 정보의 비교 용도
- [UVM M02](../../uvm/02_agent_driver_monitor/) — 비침투적 monitor 패턴
- [UVM M05](../../uvm/05_tlm_scoreboard_coverage/) — analysis port 1:N fan-out

**External**
- YosysHQ *riscv-formal* — RVFI 신호 사양 (github.com/YosysHQ/riscv-formal)
- *RVVI — RISC-V Verification Interface* draft open standard (github.com/riscv-verification/RVVI)
- OpenHW `core-v-verif` — RVFI/RVVI 기반 검증 환경 (docs.openhwgroup.org)

---

## 다음 모듈

→ [Module 04 — UVM 코어 검증 환경](../04_uvm_core_env/): RVFI 를 보는 retire monitor 를 어떻게 scoreboard·golden predictor(DPI-C)·coverage 와 묶어 _하나의 UVM 환경_ 으로 조립하는가.

[퀴즈 풀어보기 →](../quiz/03_rvfi_rvvi_quiz/)
