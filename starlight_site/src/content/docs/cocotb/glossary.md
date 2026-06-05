---
title: "cocotb 용어집"
---

이 페이지는 본 코스에서 사용되는 cocotb 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

:::tip[검색 활용]
상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.
:::
---

## C — cocotb / Cosimulation / Coroutine / Coverage

### cocotb

**Definition.** 테스트를 Python으로 작성하고 DUT는 Verilog/SystemVerilog/VHDL로 유지하는 coroutine 기반 cosimulation 검증 프레임워크.

**Source.** `cocotb_note.md` "What Is CocoTB"; cocotb 공식 문서.

**Related.** Cosimulation, Coroutine, VPI, UVM.

**Example.** OpenTitan, Western Digital, Tenstorrent 등이 실제 검증 플로우에 cocotb를 사용한다.

**See also.** [Module 01 — cocotb란 무엇인가](../01_what_is_cocotb/)

### Cosimulation

**Definition.** 시뮬레이터 외부의 프로세스가 표준 인터페이스를 통해 시뮬레이터 내부의 DUT를 함께 구동하는 실행 방식.

**Source.** `cocotb_note.md` "How It Works — Cosimulation Architecture".

**Related.** VPI, cocotb, Simulator Independence.

**Example.** Python 프로세스(cocotb)가 VPI로 HDL 시뮬레이터를 제어하여 그 안의 RTL을 검증한다.

**See also.** [Module 02 — Coroutine & Cosimulation](../02_coroutine_cosimulation/)

### Coroutine

**Definition.** `await` 지점에서 실행을 중단하고 이벤트 발생 시 그 지점부터 재개할 수 있는, `async def`로 정의된 함수.

**Source.** `cocotb_note.md` "async def → defines a coroutine"; cocotb 공식 문서.

**Related.** await, Trigger, start_soon, Cooperative Scheduling.

**Example.**
```python
async def drive(dut, item):
    dut.valid.value = 1
    await RisingEdge(dut.clk)   # 여기서 중단 → edge에 재개
```

**See also.** [Module 02 — Coroutine & Cosimulation](../02_coroutine_cosimulation/)

### Coverage (cocotb)

**Definition.** cocotb 환경에서 외부 `cocotb-coverage` 라이브러리를 통해 제공되는 functional coverage 수집 기능.

**Source.** `cocotb_note.md` Structural Mapping, Pros and Cons("coverage support weaker — relies on external libraries").

**Related.** cocotb-coverage, UVM covergroup, RAL.

**Example.** UVM은 covergroup을 언어 표준으로 제공하지만 cocotb는 cocotb-coverage 외부 라이브러리에 의존한다.

**See also.** [Module 01 §5.3](../01_what_is_cocotb/)

---

## A — await

### await

**Definition.** coroutine 실행을 중단하고 시뮬레이터에 재개 콜백을 등록한 뒤 제어를 양보하는 Python 키워드.

**Source.** `cocotb_note.md` "await RisingEdge(dut.clk) → registers a callback ... suspends Python; simulator resumes it on event".

**Related.** Coroutine, Trigger, RisingEdge.

**Example.** `await RisingEdge(dut.clk)`는 다음 rising edge까지 Python을 멈추고 시뮬레이션 시간을 진행시킨다.

**See also.** [Module 02 §2](../02_coroutine_cosimulation/)

---

## D — Direct Call Model / DUT

### Direct Call Model

**Definition.** sequence가 driver의 메서드를 중간 sequencer handshake 없이 직접 호출하는 cocotb의 자극 전달 방식.

**Source.** `cocotb_note.md` "CocoTB uses a direct call model ... the entire get_next_item/item_done boilerplate disappears".

**Related.** Sequence, Driver, Sequencer Push Model(UVM).

**Example.** `await drive(dut, item)` 한 줄이 UVM의 start_item/finish_item + get_next_item/item_done을 대신한다.

**See also.** [Module 02 §4.1](../02_coroutine_cosimulation/)

### DUT

**Definition.** Verilog/SystemVerilog/VHDL로 작성되어 시뮬레이터 내부에서 실행되는 검증 대상 설계.

**Source.** `cocotb_note.md` "the DUT stays in Verilog/SystemVerilog/VHDL".

**Related.** Cosimulation, RTL, Simulator.

**Example.** cocotb에서 `dut`는 시뮬레이터 안 RTL의 핸들이며 Python은 그 신호를 read/write한다.

**See also.** [Module 01 §3](../01_what_is_cocotb/)

---

## S — Simulator Independence / start_soon

### Simulator Independence

**Definition.** VPI 표준만 사용하여 동일한 Python 테스트 코드가 모든 VPI 지원 시뮬레이터에서 변경 없이 동작하는 cocotb의 특성.

**Source.** `cocotb_note.md` "Simulator independence: ... the same Python code runs unchanged across all simulators".

**Related.** VPI, Cosimulation, Verilator, Icarus.

**Example.** 같은 cocotb 코드를 무료 Verilator로 CI에서 돌리고 상용 VCS로 회귀할 수 있다.

**See also.** [Module 02 §5.3](../02_coroutine_cosimulation/)

### start_soon

**Definition.** coroutine을 백그라운드로 기동하여 협력적 스케줄러 위에서 실행시키는 cocotb 함수.

**Source.** cocotb 공식 문서; 본 코스 Module 02 매핑(UVM fork에 대응).

**Related.** Coroutine, Cooperative Scheduling, fork(UVM).

**Example.** `cocotb.start_soon(monitor(dut, ap))`로 monitor coroutine을 띄워 둔 뒤 자극을 인가한다.

**See also.** [Module 02 §3](../02_coroutine_cosimulation/)

---

## V — VPI

### VPI

**Definition.** 외부 프로그램이 HDL 시뮬레이터의 신호와 이벤트에 접근할 수 있게 하는 IEEE 표준 절차적 인터페이스.

**Source.** `cocotb_note.md` "controlling it via the VPI interface (cosimulation)"; IEEE 1800-2017 §VPI.

**Related.** Cosimulation, Simulator Independence, cocotb.

**Example.** cocotb의 Python 프로세스는 VPI를 통해 시뮬레이터를 제어하므로 simulator-independent하다.

**See also.** [Module 02 §2](../02_coroutine_cosimulation/)

---

## U — UVM (비교 기준)

### UVM (비교 기준)

**Definition.** SystemVerilog로 작성되어 시뮬레이션 내부에서 동작하는 IEEE 1800.2 표준 검증 방법론으로, 본 코스에서 cocotb의 비교 baseline으로 쓰인다.

**Source.** `cocotb_note.md` UVM vs CocoTB 비교 표; UVM 1.2 Reference Manual.

**Related.** cocotb, Direct Call Model, Sequencer Push Model.

**Example.** cocotb의 `@cocotb.test()`는 UVM의 `uvm_test` + `run_test()`에 대응한다.

**See also.** [UVM 코스](../../uvm/)

---

## 추가 약어

| 약어 | 풀네임 | 한 줄 의미 |
|------|--------|-----------|
| **cocotb** | COroutine-based COsimulation TestBench | Python 기반 cosimulation 검증 프레임워크 |
| **VPI** | Verilog Procedural Interface | 외부 프로세스가 시뮬레이터를 제어하는 IEEE 표준 통로 |
| **DUT** | Device Under Test | 검증 대상 RTL 설계 |
| **PoC** | Proof of Concept | 개념 검증용 빠른 프로토타입 |
| **CI** | Continuous Integration | 자동 빌드·테스트 파이프라인 |
| **VIP** | Verification IP | 재사용 가능한 검증 컴포넌트 묶음 (AXI/PCIe/DDR 등) |
| **RAL** | Register Abstraction Layer | 레지스터 이름 기반 접근 계층 (cocotb는 외부 lib 필요) |
| **FOSSi** | Free and Open Source Silicon | cocotb를 관장하는 오픈소스 실리콘 재단 |
