---
title: "Module 04 — UVM 코어 검증 환경"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Describe** CPU 코어 검증용 UVM 환경이 retire monitor·reference-model predictor·step-and-compare scoreboard·coverage 로 어떻게 구성되는지 기술할 수 있다.
- **Differentiate** retire monitor(코어가 무엇을 했나 관찰)와 predictor(reference model 이 무엇을 해야 했나 산출)의 역할을, 그리고 둘을 잇는 scoreboard 의 책임을 구분할 수 있다.
- **Apply** RVFI/RVVI([M03](../03_rvfi_rvvi/))로 노출된 retire 정보를 analysis port 로 받아 DPI-C ISS 와 대조하는 컴포넌트 골격을 적용할 수 있다.
- **Trace** 한 명령의 retire 가 monitor → predictor(ISS step) → scoreboard 비교 → coverage sample 로 흐르는 경로를 단계별로 추적할 수 있다.
- **Evaluate** ISS 를 DPI-C predictor 로 환경에 통합할 때 동기화·재사용성·정답 신뢰도 측면의 설계 선택을 평가할 수 있다.
:::
:::note[사전 지식]
- [M02 Step-and-Compare](../02_step_and_compare/), [M03 RVFI/RVVI](../03_rvfi_rvvi/)
- UVM 환경 구성 — [UVM M02 Agent/Driver/Monitor](../../uvm/02_agent_driver_monitor/), [UVM M05 TLM/Scoreboard/Coverage](../../uvm/05_tlm_scoreboard_coverage/)
- CSR 의 레지스터 모델 — [UVM M07 RAL](../../uvm/07_register_layer_ral/)
:::
---

## 1. Why care? — 메커니즘은 알겠는데, 그걸 _하나의 환경_ 으로 어떻게 조립하나

### 1.1 시나리오 — 흩어진 조각들

지금까지 우리는 조각을 모았습니다. [M02](../02_step_and_compare/)는 "retire 시점에 ISS 와 architectural state 를 비교한다"는 _메커니즘_ 을, [M03](../03_rvfi_rvvi/)는 "retire 정보가 RVFI 라는 _표준 신호_ 로 코어 밖에 나온다"는 _인터페이스_ 를, [M05](../05_riscv_dv_stimulus/)는 "제약 랜덤 ISG 가 자극을 만든다"는 _자극원_ 을 다룹니다. 그런데 이 조각들을 _어떻게 하나의 재사용 가능한 검증 환경으로 묶는가_ 는 아직 비어 있습니다.

조각만 있고 조립 규약이 없으면, 검증팀은 매번 ad-hoc 스크립트로 "RVFI 신호를 읽어 C 모델 함수를 호출하고 비교"하는 코드를 새로 짭니다. 이런 코드는 재사용 불가능하고, coverage·factory override·config 같은 검증 인프라의 이점을 전혀 못 누립니다.

### 1.2 해법 — UVM 컴포넌트로 역할을 분리한다

해법은 각 조각을 _UVM 컴포넌트_ 로 만들어 책임을 분리하는 것입니다. retire 정보 관찰은 **monitor**, reference model 산출은 **predictor**, 둘의 대조는 **scoreboard**, 검증 완전성 측정은 **coverage** 가 맡습니다. 이들을 하나의 **env** 가 조립하고, monitor 의 analysis port 가 1:N 으로 fan-out 해 predictor·scoreboard·coverage 를 동시에 먹입니다([UVM M05 의 broadcast 패턴](../../uvm/05_tlm_scoreboard_coverage/)).

이 모듈을 건너뛰면 [M02](../02_step_and_compare/)의 메커니즘과 [M03](../03_rvfi_rvvi/)의 인터페이스는 알지만 _재사용 가능한 환경으로 조립할 줄 모르는_ 상태에 머물고, 매 프로젝트마다 검증 인프라를 처음부터 다시 짜게 됩니다.

:::note[RISC-V 를 러닝 예제로 쓰지만 ARM 코어에도 동일]
이 모듈은 RVFI/ISS(Spike)를 구체 예제로 씁니다. 그러나 "retire 인터페이스를 monitor 로 관찰 → reference model predictor 와 scoreboard 로 대조"라는 _UVM 환경 구조_ 는 ISA 와 무관합니다. ARM 코어라면 retire/commit 인터페이스와 ARM 용 reference model 로 _같은 컴포넌트 골격_ 을 그대로 적용합니다.(외부 표준 지식)
:::

---

## 2. Intuition — 한 줄 비유, 한 장 그림

:::tip[💡 한 줄 비유]
**CPU UVM 환경** ≈ **경기 심판진**.<br>
**monitor** 는 선수(코어)가 _무엇을 했는지_ 기록하는 _기록원_, **predictor**(reference model)는 규칙서(ISA)를 보고 _무엇을 했어야 했는지_ 말하는 _규칙 심판_, **scoreboard** 는 둘을 맞대보고 _판정_ 하는 _주심_, **coverage** 는 "경기에서 어떤 상황들이 실제로 일어났나"를 세는 _기록 통계_ 입니다. 심판진 각자가 한 가지 책임만 지므로, 선수(코어)가 바뀌어도 심판진 구조는 그대로 재사용됩니다.
:::

### 한 장 그림 — retire 정보가 monitor 에서 N 곳으로

```d2
direction: right

DUT: "**RTL 코어**\n(DUT)\nRVFI/RVVI retire 신호" {
  RVFI: "rvfi_valid\nrvfi_pc/insn\nrvfi_rd_addr/wdata\nrvfi_mem_* / csr"
}
MON: "**retire monitor**\n@(rvfi_valid)\nretire_item 생성\nap.write()"
PRED: "**predictor**\n(reference model)\nDPI-C → ISS 1 step\nexpected_item"
SB: "**scoreboard**\nstep-and-compare\nRTL vs ISS\nfirst-divergence"
COV: "**coverage**\ncovergroup.sample()\n명령·privilege·cross"

DUT -> MON: "RVFI 관찰"
MON -> PRED: "1:N broadcast"
MON -> SB
MON -> COV
PRED -> SB: "expected (ISS)"
```

### 왜 이 구조인가 — Design rationale

세 가지 요구의 교집합입니다.

1. **관찰·정답·판정·측정이 서로 독립적으로 진화해야 한다** → monitor / predictor / scoreboard / coverage 를 분리된 UVM 컴포넌트로. 코어가 바뀌면 monitor 의 RVFI 결선만, ISS 가 바뀌면 predictor 의 DPI 바인딩만 손댄다.
2. **같은 retire stream 을 정답 산출·판정·완전성 측정이 _동시에_ 소비해야 한다** → monitor 의 analysis port 가 1:N fan-out([UVM M05](../../uvm/05_tlm_scoreboard_coverage/)). publisher(monitor)는 누가 듣는지 모른다.
3. **환경은 프로젝트 독립적이어야 한다** → 코어·ISS 의존을 config/factory 로 주입하고, 컴포넌트 자체는 DUT 로직을 모른다([DV 의 reusable TB 원칙](../../uvm/02_agent_driver_monitor/)).

---

## 3. 작은 예 — 한 명령의 retire 가 환경을 한 바퀴 도는 과정

[M02](../02_step_and_compare/)의 ADDI 예제를, 이번엔 _UVM 환경 안에서_ 컴포넌트들이 어떻게 협력하는지로 봅니다.

### 단계별 다이어그램

```d2
direction: down

S1: "**① retire monitor**\n@(rvfi_valid)\nADDI x5,x5,1\nretire_item{pc,insn,rd,wdata} 생성\nap.write(item)"
S2: "**② predictor (ISS)**\nitem.pc 의 명령을\nDPI-C 로 ISS 1 step\nexpected{rd=5, wdata=0x41}"
S3: "**③ scoreboard 비교**\nRTL wdata=0x41\n== ISS wdata=0x41 ✓\n불일치면 first-divergence"
S4: "**④ coverage sample**\ncg.sample(insn, priv, ...)\nADDI bin ↑, cross ↑"
S1 -> S2: "broadcast"
S1 -> S4: "broadcast"
S2 -> S3: "expected"
S1 -> S3: "actual (RTL)"
```

### 단계별 의미

| Step | 누가 | 무엇을 | 핵심 |
|---|---|---|---|
| ① | retire monitor | RVFI 에서 retire_item 샘플, analysis port 로 broadcast | 코어 내부 무관, RVFI 만 본다([M03](../03_rvfi_rvvi/)) |
| ② | predictor | DPI-C 로 ISS 를 _같은 명령_ 한 스텝 진행해 expected 산출 | 정답은 코어가 아니라 reference model([M02](../02_step_and_compare/)) |
| ③ | scoreboard | RTL actual 과 ISS expected 를 retire 단위 비교 | 첫 불일치 즉시 flag(cascading 방지) |
| ④ | coverage | 같은 item 으로 covergroup sample | "발생했는가" 측정([M07](../07_coverage_special_areas/)) |

핵심은 ① 의 한 broadcast 가 _세 갈래_(predictor·scoreboard·coverage)로 동시에 흐른다는 점입니다. scoreboard 는 actual(monitor)과 expected(predictor) _둘 다_ 를 받아 비교하고, coverage 는 actual 만으로 "이 명령·이 상황이 실제로 일어났다"를 셉니다. 결함 발견(scoreboard)과 검증 완전성(coverage)이 _같은 retire stream_ 에서 동시에 동작합니다.

### retire monitor 골격

```systemverilog
// RVFI 를 보는 retire monitor — 코어 내부 경로에 의존하지 않는다 (M03)
class core_retire_monitor extends uvm_monitor;
  `uvm_component_utils(core_retire_monitor)
  virtual rvfi_if vif;
  uvm_analysis_port #(retire_item) ap;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    ap = new("ap", this);
    if (!uvm_config_db#(virtual rvfi_if)::get(this, "", "rvfi_vif", vif))
      `uvm_fatal("NOVIF", "rvfi_vif not set in config_db")
  endfunction

  task run_phase(uvm_phase phase);
    forever begin
      // rvfi_valid 사이클 = 명령 1개 retire (M03)
      @(posedge vif.clk iff vif.rvfi_valid);
      retire_item it = retire_item::type_id::create("it");
      it.order    = vif.rvfi_order;        // 프로그램 순서 (superscalar 정렬용)
      it.pc       = vif.rvfi_pc_rdata;
      it.insn     = vif.rvfi_insn;
      it.rd_addr  = vif.rvfi_rd_addr;
      it.rd_wdata = vif.rvfi_rd_wdata;     // architectural 확정값
      it.trap     = vif.rvfi_trap;
      it.intr     = vif.rvfi_intr;
      ap.write(it);                        // predictor/scoreboard/coverage 로 fan-out
    end
  endtask
endclass
```

### predictor + scoreboard 골격 (DPI-C ISS)

```systemverilog
// ISS 를 DPI-C 로 호출하는 predictor — 정답(expected)을 산출
import "DPI-C" function void iss_step(
  input  longint pc,
  input  int     intr,        // 인터럽트 진입 여부를 ISS 에 전달 (M02 §4.3)
  output byte    rd_addr,
  output longint rd_wdata,
  output longint csr_wdata
);

// scoreboard 는 monitor(actual)와 predictor 결과(expected)를 대조한다.
// 여기서는 predictor 를 scoreboard 안에 합쳐 step-and-compare 를 직접 수행.
class core_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(core_scoreboard)
  uvm_analysis_imp #(retire_item, core_scoreboard) ap_imp;  // monitor 로부터 수신

  function new(string name, uvm_component parent);
    super.new(name, parent);
    ap_imp = new("ap_imp", this);
  endfunction

  // analysis_imp 의 즉시 처리 콜백 (M05 의 analysis_imp 패턴)
  function void write(retire_item it);
    byte    e_rd;
    longint e_wdata, e_csr;
    // predictor: ISS 를 같은 명령으로 1 step 진행 (RTL-driven lockstep, M02)
    iss_step(it.pc, it.intr, e_rd, e_wdata, e_csr);

    // step-and-compare: 첫 divergence 즉시 flag (M02 §5)
    if (it.rd_addr !== e_rd || it.rd_wdata !== e_wdata) begin
      `uvm_error("DIVERGE",
        $sformatf("First divergence @pc=%h order=%0d: RTL rd[%0d]=%h, ISS rd[%0d]=%h",
                  it.pc, it.order, it.rd_addr, it.rd_wdata, e_rd, e_wdata))
      // 이후는 cascading 이므로 더 진행하지 않도록 환경 차원에서 종료/표시
    end
  endfunction
endclass
```

:::note[여기서 잡아야 할 두 가지]
**(1) 컴포넌트는 _DUT 로직을 모른다_.** monitor 는 RVFI 신호만, scoreboard/predictor 는 ISS DPI 인터페이스만 안다. 코어 내부(파이프라인·forwarding)는 어디에도 결선돼 있지 않아 _재사용 가능_ 하다([DV reusable TB 원칙](../../uvm/02_agent_driver_monitor/)).<br>
**(2) predictor 와 scoreboard 는 합칠 수도, 분리할 수도 있다.** 위 예는 ISS step 을 scoreboard 안에서 호출했지만, predictor 를 별도 컴포넌트로 빼 expected_item 을 analysis port 로 보내는 구성도 흔하다 — 그러면 scoreboard 는 순수 _비교기_ 가 되어 더 재사용성이 높아진다.
:::

---

## 4. 일반화 — 환경의 컴포넌트 지도, 자극과의 연결, RAL

### 4.1 컴포넌트 책임 분해

```d2
direction: down

ENV: "**core_env**" {
  AGT: "**core_agent**\n(monitor 중심,\n수동/능동)"
  PRED: "**predictor**\nreference model(ISS)\nexpected 산출"
  SB: "**scoreboard**\nactual vs expected\nstep-and-compare"
  COV: "**coverage collector**\ncovergroup sample"
  RAL: "**CSR RAL model**\n(uvm_reg)\npredict/mirror"
}
```

| 컴포넌트 | 책임 | 무엇에 결선 | 본 코스 |
|---|---|---|---|
| retire monitor | RVFI retire 관찰 → retire_item | RVFI/RVVI 신호 | [M03](../03_rvfi_rvvi/), [UVM M02](../../uvm/02_agent_driver_monitor/) |
| predictor | reference model 로 expected 산출 | ISS(DPI-C) | [M02](../02_step_and_compare/) |
| scoreboard | actual vs expected 대조, first-divergence | predictor·monitor | [M02](../02_step_and_compare/), [UVM M05](../../uvm/05_tlm_scoreboard_coverage/) |
| coverage | covergroup sample | retire_item | [M07](../07_coverage_special_areas/), [UVM M05](../../uvm/05_tlm_scoreboard_coverage/) |
| CSR RAL | CSR mirror/predict | 코어 CSR | [UVM M07 RAL](../../uvm/07_register_layer_ral/) |

각 컴포넌트는 _하나의 책임_ 만 집니다. 이 분리 덕분에 ISS 교체는 predictor 만, 코어 교체는 monitor 결선만, coverage 모델 확장은 coverage collector 만 손대면 됩니다.

### 4.2 자극(M05)·SVA·coverage(M07)와의 연결

```d2
direction: right

ISG: "**ISG (M05)**\nriscv-dv\nELF 생성"
DUT: "**RTL 코어 + UVM env**\nretire monitor\npredictor / scoreboard"
ISS: "**predictor ISS**\n같은 ELF"
COV: "**coverage (M07)**\n명령·privilege·cross"
SVA: "**SVA**\nRVFI 프로토콜\n불변식"

ISG -> DUT: "ELF load & run"
ISG -> ISS: "같은 ELF"
DUT -> COV: "retire stream"
DUT -> SVA: "신호 불변식"
```

환경은 고립돼 있지 않습니다. [M05](../05_riscv_dv_stimulus/)의 제약 랜덤 ISG(instruction stream generator, 명령 스트림 생성기) 가 만든 ELF(컴파일·링크된 실행 파일 포맷 — 코어가 fetch 할 명령·데이터가 담긴 바이너리) 를 RTL 과 predictor ISS 가 _같이_ 실행하고, retire stream 이 scoreboard(판정)와 coverage(완전성, [M07](../07_coverage_special_areas/))로 흐릅니다. SVA 는 RVFI 신호 자체의 프로토콜 불변식(예: `rvfi_valid` 일 때 PC 정렬)을 _상시_ 검사해 monitor 의 가정이 깨지면 즉시 잡습니다. 이 네 가지(자극·비교·coverage·SVA)가 한 환경에서 맞물려 동작합니다.

### 4.3 CSR 와 RAL

코어의 CSR(`mstatus`, `mepc`, `mcause` 등)은 단순 신호가 아니라 _상태를 가진 레지스터_ 입니다. UVM RAL([UVM M07](../../uvm/07_register_layer_ral/))로 CSR 를 `uvm_reg` 모델로 만들면, retire 시 CSR 변화를 RAL 의 `predict()` 로 mirror 에 반영하고 access policy(RO/WARL)를 함께 검증할 수 있습니다. step-and-compare 의 CSR _값_ 비교(predictor ISS)와 RAL 의 _접근 정책_ 검증이 상보적으로 동작합니다 — CSR 의 특수성은 [M07 §4.1](../07_coverage_special_areas/)에서 더 다룹니다.

---

## 5. 디테일 — DPI-C 동기화, superscalar 정렬, 능동/수동 agent

### 5.1 DPI-C predictor 의 동기화 책임

predictor 가 ISS 를 DPI-C 로 호출할 때 핵심은 _RTL-driven lockstep_([M02 §4.1](../02_step_and_compare/))입니다. RTL 이 leader 이고 ISS 가 follower 이므로, monitor 가 retire 한 _그 명령_ 으로 ISS 를 한 스텝 끌고 가야 합니다. 특히 비결정 요소는 retire_item 으로 ISS 에 전달합니다.

| 전달 항목 | 왜 | 어디서 |
|---|---|---|
| `it.intr` (인터럽트 진입) | ISS 가 _같은 명령 경계_ 에서 trap 하게 | [M03 `rvfi_intr`](../03_rvfi_rvvi/) |
| `it.trap` (예외 발생) | trap 경로의 CSR side-effect 동기화 | [M03 `rvfi_trap`](../03_rvfi_rvvi/) |
| 시간 CSR(`mcycle` 등) | ISS 가 RTL 값을 읽어 동기화(직접 비교 안 함) | [M02 §4.3](../02_step_and_compare/) |

이 동기화를 빠뜨리면 인터럽트·예외 직후부터 _체계적으로_ 발산합니다 — 이는 RTL 버그가 아니라 TB 동기화 버그입니다([M02 §5.3](../02_step_and_compare/)).

**DPI-C 호출의 비용과 상태 관리.** 매 retire 마다 `iss_step` 을 한 번씩 부르므로, 긴 회귀(수억 명령)에서는 DPI 경계를 넘는 _호출 자체_ 가 성능에 잡힙니다. 시뮬레이터는 SV↔C 경계에서 인자를 마샬링(복사)하므로, retire 당 호출이 빈번할수록 마샬링 비용이 누적됩니다 — 그래서 인자는 _값이 필요한 것만_ 좁게 넘기고(전체 레지스터 파일을 매번 복사하지 않음), 큰 상태는 C 측에 _남겨두는_ 것이 정석입니다. 즉 **ISS 의 상태(레지스터·메모리·CSR)는 SV 가 아니라 C 측 정적(static) 객체로 유지**되고, SV 는 "한 스텝 진행하라"는 트리거와 비교에 필요한 소수의 출력만 주고받습니다. ISS 핸들을 C 의 static 포인터로 두면 호출 간 상태가 자연히 보존됩니다.

이 구조는 **멀티 코어/멀티 hart**(hardware thread — RISC-V 에서 독립적으로 명령을 실행하는 하드웨어 실행 단위, 각자 architectural state 를 가짐) 에서 중요한 함의를 갖습니다. hart 가 N 개면 ISS _인스턴스_ 도 N 개가 필요하고, 각 retire 가 _어느 hart_ 의 것인지에 따라 해당 인스턴스를 step 시켜야 합니다. 따라서 C 측은 단일 static 이 아니라 hart_id 로 인덱싱되는 인스턴스 배열/맵을 두고, DPI 시그니처에 `hart_id` 를 추가해 올바른 ISS 를 고릅니다. 이를 빠뜨리면 한 hart 의 retire 가 다른 hart 의 ISS 를 진행시켜 발산합니다. (DPI-C 함수의 재진입·자동 변수 의미는 [UVM M06 의 function vs function automatic](../../uvm/06_practical_patterns/) 과 같은 원리 — 호출 간 보존이 필요한 상태는 static, 호출별로 새로 필요한 것은 automatic.)

### 5.2 superscalar 코어 — order 기반 정렬

한 사이클에 여러 명령이 retire 되는 superscalar 코어는 monitor 가 retire port 별로 item 을 만들고, scoreboard 가 `rvfi_order`([M03 §5.1](../03_rvfi_rvvi/))로 _프로그램 순서_ 를 복원한 뒤 ISS 와 비교합니다. ISS 는 본질적으로 in-order 이므로, scoreboard 는 order 로 정렬한 stream 을 ISS step 순서와 맞춰야 합니다.

```d2
direction: right
P0: "retire port 0\norder=N"
P1: "retire port 1\norder=N+1"
SB: "scoreboard\norder 로 정렬"
ISS: "predictor ISS\nin-order step"
P0 -> SB
P1 -> SB
SB -> ISS: "order 순서로"
```

이 패턴은 [UVM M05 의 out-of-order scoreboard(per-key 정렬)](../../uvm/05_tlm_scoreboard_coverage/)와 같은 사고방식입니다 — 도착 순서가 아니라 _논리적 키(order)_ 로 정렬해 비교합니다.

### 5.3 능동(active) vs 수동(passive) — CPU 코어는 대개 수동 관찰

전통적 UVM agent 는 driver 로 DUT 를 _구동_ 합니다. 그러나 CPU 코어 검증에서 자극은 _메모리에 로드된 프로그램(ELF)_ 으로 들어가므로([M05](../05_riscv_dv_stimulus/)), 코어 agent 는 흔히 _수동(passive)_ 으로 retire 만 관찰합니다. 능동 요소는 메모리/버스 응답·인터럽트 주입 쪽에 둡니다. 즉 자극은 ELF + 외부 이벤트(인터럽트·메모리)로 인가하고, monitor 는 그 결과 retire 를 관찰하는 비대칭 구조입니다.

**그러면 "능동 요소"는 구체적으로 어디에 결선되는가.** "자극은 ELF 로"는 _명령 스트림_ 의 출처일 뿐, 코어는 실행 도중 메모리 응답과 인터럽트라는 _두 능동 입력_ 을 더 받습니다.

- **메모리 모델 — backdoor preload vs bus agent.** ELF 의 코드/데이터를 코어가 보게 하는 방법은 두 가지입니다. (a) _backdoor preload_: 시뮬레이션 시작 전 메모리 배열에 ELF 이미지를 직접 써넣어 코어가 즉시 fetch/load 하게 함 — 빠르고 단순하지만 버스 프로토콜·지연·backpressure(수신 측이 아직 못 받을 때 송신을 막아 흐름을 늦추는 역압) 는 검증하지 못합니다. (b) _bus agent_(능동): 코어의 메모리 인터페이스(예: AXI/AHB 류)에 driver 를 붙여 read/write 요청에 _프로토콜대로 응답_ 하고 임의 지연·에러 응답을 주입 — 메모리 서브시스템과 stall 경로까지 자극합니다. 실무에선 코드 영역은 backdoor 로 빠르게, 데이터·MMIO 영역은 bus agent 로 능동 응답하는 혼합 구성이 흔합니다.
- **인터럽트 주입 컴포넌트.** 인터럽트는 ELF 안에 표현되지 않으므로 _별도 능동 컴포넌트_ 가 코어의 인터럽트 입력 핀(예: 외부/타이머/소프트웨어 인터럽트)을 시간/명령 경계 기준으로 assert 합니다. 이 컴포넌트가 인터럽트를 넣은 사실은 [M03 `rvfi_intr`](../03_rvfi_rvvi/) 로 retire 에 표시되어 predictor 가 같은 경계에서 trap 하게 됩니다(§5.1). _언제_ 주입할지(특정 명령이 특정 stage 에 있을 때 등)의 정밀 제어는 [M07 §4.2](../07_coverage_special_areas/) 에서 다룹니다.

정리하면 env 결선은 비대칭입니다: monitor(수동)는 retire 를 _관찰만_, 메모리 bus agent 와 인터럽트 주입기(능동)는 코어에 _응답·이벤트를 인가_, 그리고 두 능동 입력의 효과는 다시 retire stream 으로 관찰되어 predictor 와 동기화됩니다.

### 5.4 predictor 분리형 — scoreboard 를 순수 비교기로

§3 에서는 ISS step 을 scoreboard 안에서 호출했지만, 더 재사용성 높은 구성은 predictor 를 _별도 컴포넌트_ 로 빼는 것입니다.

```d2
direction: right
MON: "retire monitor\nactual_item"
PRED: "predictor\nISS step →\nexpected_item"
SB: "scoreboard\nactual vs expected\n(순수 비교)"
MON -> PRED: "actual"
PRED -> SB: "expected"
MON -> SB: "actual"
```

이렇게 하면 scoreboard 는 reference model 종류(Spike·ImperasDV 등)를 모르고 _두 stream 을 비교만_ 합니다. ISS 를 교체해도 scoreboard 코드는 불변 — predictor 만 바꾸면 됩니다. 이것이 [DV reusable TB 원칙](../../uvm/02_agent_driver_monitor/)의 "scoreboard 는 transaction 레벨에서 비교"를 CPU 환경에 적용한 형태입니다.

### 5.5 분리형 scoreboard 의 큐잉과 timeout

predictor 를 분리(§5.4)하면 actual(monitor)과 expected(predictor)가 _서로 다른 시점_ 에 도착할 수 있습니다 — scoreboard 는 둘을 _매칭_ 해야 합니다. 즉시 호출(§3 합본형)과 달리, 분리형은 도착 순서가 어긋날 수 있으므로 in-order 큐가 필요합니다.

```d2
direction: right
A: "actual queue\n(monitor)"
E: "expected queue\n(predictor)"
M: "**매칭기**\norder 가 같은\n쌍을 비교"
A -> M
E -> M
M -> R: "head 쌍 pop →\ncompare → 다음"
R: "first-divergence\n또는 OK"
```

- **per-key(order) 매칭.** 두 큐를 각각 `rvfi_order` 로 정렬하고, 같은 order 의 쌍이 _둘 다_ 도착했을 때 head 에서 pop 하여 비교합니다([UVM M05 의 per-key out-of-order scoreboard](../../uvm/05_tlm_scoreboard_coverage/) 와 같은 사고). 한쪽만 도착했으면 짝이 올 때까지 큐에 _보류_ 합니다.
- **drain — run_phase 종료 시.** 테스트가 끝나면 두 큐에 _짝 없이 남은_ 항목이 없어야 합니다. `check_phase` 에서 큐가 비었는지 확인하고, 남아 있으면 "actual 은 retire 됐는데 expected 가 없다(또는 그 반대)" — 비교 누락(blind spot)이거나 predictor 가 한 명령을 빠뜨렸다는 신호입니다.
- **timeout — 한쪽이 영영 안 올 때.** RTL 이 hang 하거나 predictor 가 막히면 한 큐가 영원히 짝을 기다립니다. 그래서 "마지막 매칭 이후 일정 시간/사이클 무진전"을 watchdog 으로 감지해 `uvm_error`(또는 fatal)로 종료해야 합니다 — 안 그러면 시뮬레이션이 _조용히_ 끝까지 돌다 타임아웃 없이 PASS 처럼 보이거나, 전체 회귀 시간을 잡아먹습니다. timeout 은 "비교가 _진행되고 있다_"는 liveness 의 최소 보장입니다.

요점: 분리형 scoreboard 는 재사용성을 얻는 대신 _비동기 매칭_ 의 책임(큐잉·drain·timeout)을 떠안습니다. 합본형(§3)은 이 책임이 없는 대신 ISS 가 scoreboard 에 결합됩니다 — 환경 규모와 ISS 교체 빈도에 따라 선택합니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'monitor 가 scoreboard 와 coverage 를 직접 호출해야 한다']
**실제**: monitor 는 `ap.write(item)` 한 번으로 _broadcast_ 만 하고, 누가 듣는지 모릅니다([UVM M05](../../uvm/05_tlm_scoreboard_coverage/)). scoreboard·coverage·predictor 는 _수신자 측_ 에서 connect 합니다. 새 수신자 추가 시 monitor 코드는 불변입니다.<br>
**왜 헷갈리는가**: "데이터를 보낸다 = 받는 쪽을 직접 호출한다"는 절차적 사고 때문 — UVM 은 publisher/subscriber 분리.
:::
:::danger[❓ 오해 2 — 'predictor(ISS)는 monitor 와 독립적으로 먼저 다 돌려두면 된다']
**실제**: RTL-driven lockstep 이므로 ISS 는 RTL 이 _retire 한 명령_ 을 따라 한 스텝씩 가야 합니다([M02 §4.1](../02_step_and_compare/)). 특히 인터럽트 시점을 RTL 이 알려줘야 ISS 도 같은 경계에서 trap 합니다. 미리 다 돌리면 비결정 요소에서 발산합니다.<br>
**왜 헷갈리는가**: "reference 니까 정답을 미리 만들 수 있다"는 착각 — [M02 오해 1](../02_step_and_compare/)과 동일.
:::
:::danger[❓ 오해 3 — 'scoreboard 가 ISS 종류를 알아야 비교할 수 있다']
**실제**: predictor 를 분리하면(§5.4) scoreboard 는 reference model 종류를 모르고 _두 transaction stream 을 비교_ 만 합니다. ISS 교체는 predictor 만 손대면 되고 scoreboard 는 불변입니다.<br>
**왜 헷갈리는가**: 비교와 정답 산출을 한 덩어리로 보기 때문 — 책임 분리하면 재사용성이 올라갑니다.
:::
:::danger[❓ 오해 4 — 'coverage 가 0 이면 scoreboard 가 비교를 안 한 것이다']
**실제**: coverage 와 scoreboard 는 _독립_ 입니다. coverage 0 은 covergroup sample 누락 또는 해당 상황 미발생일 뿐, scoreboard 비교 여부와 무관합니다. 둘 다 같은 ap 에서 받지만 책임이 다릅니다.<br>
**왜 헷갈리는가**: 둘이 같은 stream 을 받으니 한 묶음으로 오해 — 결함 발견(SB)과 완전성 측정(coverage)은 별개.
:::

### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| scoreboard 가 retire 를 하나도 못 받음 | monitor.ap ↔ scoreboard connect 누락, 또는 RVFI 가드 미빌드 | `connect_phase` 의 ap.connect, 코어 RVFI ifdef([M03](../03_rvfi_rvvi/)) |
| 모든 명령이 첫 명령부터 divergence | ISS 초기화(reset/메모리)가 RTL 과 불일치 | predictor 의 ISS init vs RTL reset([M02](../02_step_and_compare/)) |
| 인터럽트 직후부터 체계적 발산 | `it.intr` 를 ISS step 에 전달 안 함 | DPI `iss_step` 의 intr 인자 결선(§5.1) |
| superscalar 에서 순서 뒤섞임 | scoreboard 가 `rvfi_order` 로 정렬 안 함 | scoreboard 의 order 기반 정렬(§5.2) |
| coverage 가 0 인데 비교는 정상 | coverage 의 sample 호출 누락(write 콜백) | coverage collector 의 `cg.sample()` 위치 |
| ISS 교체 후 scoreboard 까지 깨짐 | predictor 와 scoreboard 가 안 분리됨 | predictor 분리 구조로 리팩터(§5.4) |
| DPI-C 호출에서 segfault/오값 | C 함수 시그니처 ↔ SV import 불일치 | `import "DPI-C"` 인자 타입 vs C 정의 |

---

## 7. 핵심 정리 (Key Takeaways)

- **UVM 환경 = 책임 분리된 심판진**: retire monitor(관찰)·predictor(정답 산출)·scoreboard(판정)·coverage(완전성)가 각각 한 책임만 진다.
- **monitor 의 analysis port 가 1:N fan-out**: 한 retire_item 이 predictor·scoreboard·coverage 로 동시에 broadcast([UVM M05](../../uvm/05_tlm_scoreboard_coverage/)). publisher 는 수신자를 모른다.
- **predictor 는 RTL-driven lockstep 으로 ISS 를 끌고 간다**: DPI-C 로 ISS 1 step, 인터럽트·예외 같은 비결정 요소는 retire_item 으로 ISS 에 전달([M02](../02_step_and_compare/)).
- **predictor 분리 = scoreboard 재사용성**: scoreboard 를 순수 비교기로 두면 ISS 교체에도 불변. reusable TB 원칙의 적용.
- **컴포넌트는 DUT 로직을 모른다**: monitor 는 RVFI 만([M03](../03_rvfi_rvvi/)), scoreboard 는 transaction 만 — 코어가 바뀌어도 환경 구조는 그대로.
- **환경은 자극(M05)·coverage(M07)·SVA·RAL 과 맞물린다**: ISG ELF 를 RTL+ISS 가 같이 실행, retire stream 이 판정·완전성으로, CSR 은 RAL 로([UVM M07](../../uvm/07_register_layer_ral/)).

:::caution[실무 주의점]
- ISS 초기화(reset 상태·메모리 이미지)를 RTL 과 정확히 일치 — 안 그러면 첫 명령부터 전부 mismatch.
- 비결정 요소(`intr`/`trap`/시간 CSR)는 retire_item 으로 ISS 에 전달 — 누락 시 인터럽트 직후 체계적 발산은 TB 버그.
- predictor 와 scoreboard 를 분리해 ISS 교체에 대비하라 — 비교기는 reference model 종류를 몰라야 한다.
- DPI-C 시그니처(SV import ↔ C 정의)를 정확히 맞춰라 — 불일치는 오값·segfault 의 단골.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — 컴포넌트 책임 분리 (Bloom: Analyze)]
어떤 팀이 monitor 안에서 직접 ISS 를 호출하고 비교까지 한 뒤 결과를 로그로 남기는 "한 덩어리" 컴포넌트를 만들었다. 이 설계가 재사용성·유지보수 관점에서 무엇을 잃는지, 어떻게 분해해야 하는지 설명하라.
<details>
<summary>정답</summary>

한 덩어리 monitor 는 _관찰·정답 산출·판정·기록_ 네 책임을 한 클래스에 묶어 재사용성을 잃습니다.
- **잃는 것**: (a) 코어를 바꾸면 RVFI 결선뿐 아니라 ISS·비교 코드까지 영향을 받음. (b) ISS 를 교체하면 monitor 전체를 손대야 함. (c) coverage 를 추가하려면 monitor 를 또 고쳐야 함(broadcast 가 없으니). (d) scoreboard 가 transaction 레벨에서 비교한다는 reusable TB 원칙 위배.
- **올바른 분해**: monitor 는 RVFI 만 관찰해 `ap.write(retire_item)` 으로 broadcast. predictor 가 ISS step 으로 expected 산출. scoreboard 가 actual vs expected 를 순수 비교(first-divergence). coverage 가 같은 ap 에서 sample.
- **효과**: 코어 교체는 monitor 결선만, ISS 교체는 predictor 만, coverage 확장은 collector 만 — 각 변경이 _한 컴포넌트_ 에 국한됩니다.

</details>
:::
:::tip[🤔 Q2 — DPI-C predictor 통합 (Bloom: Evaluate)]
ISS 를 DPI-C predictor 로 통합할 때, "ISS 를 시뮬레이션과 무관하게 먼저 전체 실행해 expected trace 를 파일로 떨군 뒤, scoreboard 가 그 파일과 RTL retire 를 비교"하는 방식을 제안받았다. 이 방식을 평가하라.
<details>
<summary>정답</summary>

**비결정 요소(특히 인터럽트) 때문에 일반적으로는 부적절하다 — RTL-driven lockstep 을 깨기 때문이다.**
- 미리 떨군 expected trace 는 _RTL 이 실제로 인터럽트를 어느 명령 경계에서 받았는지_ 를 반영할 수 없습니다([M02 오해 1](../02_step_and_compare/)). ISS 가 RTL 과 다른 명령에서 trap 하면 그 시점부터 trace 가 통째로 어긋납니다.
- 또한 시간 CSR(`mcycle` 등) 구현정의 값도 RTL 실행 중에만 알 수 있어, 사전 trace 는 이를 동기화할 수 없습니다.
- **단, 정당화되는 경우**: 코어가 인터럽트·비결정 요소가 전혀 없는 _완전 결정적_ directed 시나리오(외부 이벤트 없음)라면, 사전 trace 비교가 성능상 이점이 있을 수 있습니다.
- **결론**: 비동기 이벤트가 있는 일반 CPU 검증에서는 DPI-C 로 ISS 를 _retire 와 lockstep_ 으로 끌고 가야 하며, retire_item 으로 인터럽트/예외를 ISS 에 전달해야 합니다. 사전 trace 방식은 결정적 서브셋에 한해 제한적으로만 정당화됩니다.

</details>
:::
### 7.2 출처

**Internal**
- [M02 Step-and-Compare](../02_step_and_compare/) — lockstep 비교 메커니즘, 비결정 동기화
- [M03 RVFI/RVVI](../03_rvfi_rvvi/) — retire monitor 가 보는 신호 인터페이스
- [M05 제약 랜덤 자극](../05_riscv_dv_stimulus/) — 환경에 주입되는 ELF 자극
- [M07 Coverage & 특수 영역](../07_coverage_special_areas/) — coverage 모델, CSR/privilege
- [UVM M02 Agent/Driver/Monitor](../../uvm/02_agent_driver_monitor/) — 비침투 monitor·reusable TB 원칙
- [UVM M05 TLM/Scoreboard/Coverage](../../uvm/05_tlm_scoreboard_coverage/) — analysis port 1:N, OoO scoreboard
- [UVM M07 RAL](../../uvm/07_register_layer_ral/) — CSR 의 레지스터 모델·access policy

**External**
- OpenHW `core-v-verif` — UVM 기반 CORE-V 코어 검증 환경(retire monitor + reference model) (docs.openhwgroup.org)
- Synopsys *ImperasDV* — reference model predictor + step-and-compare 통합 (외부 표준 지식)
- *UVM 1.2 Class Reference* — analysis port/imp, scoreboard, subscriber (외부 표준 지식)
- IEEE 1800 DPI-C — SystemVerilog ↔ C 모델 연동 (외부 표준 지식)

---

## 다음 모듈

→ [Module 05 — 제약 랜덤 명령 생성 (riscv-dv / force-riscv)](../05_riscv_dv_stimulus/): 이 환경에 _무엇을_ 먹일 것인가 — 손으로 못 메우는 명령 조합 공간을 제약 랜덤 ISG 가 어떻게 자동으로 채우는가.

[퀴즈 풀어보기 →](../quiz/04_uvm_core_env_quiz/)
