# Ch04. Mode Register 깊이 분석

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">CH 04</span>
</div>

## 🎯 Learning Objectives

- **Classify**: DDR5의 MR0~MR254를 기능 카테고리로 분류한다.
- **Decompose**: DDR5 MR4(Refresh Settings)의 비트 필드를 분해하고 각 필드의 의미를 설명한다.
- **Apply**: UVM RAL을 사용해 MR 레지스터 모델을 작성하고 mirrored value를 update하는 패턴을 구현한다.
- **Evaluate**: 어떤 MR 변경은 *재초기화 없이* 가능하고 어떤 것은 *재초기화 필요*한지 판단한다.

## Prerequisites

- [Ch03. 초기화·Reset·Power 시퀀스](03_init_reset_power.md)
- UVM RAL(Register Abstraction Layer) 기본 (uvm_reg, uvm_reg_field, uvm_reg_block, ral_model)

## 1. Mode Register란 무엇인가

Mode Register(MR)는 DRAM 동작을 런타임에 설정하기 위한 제어 레지스터입니다. CL(CAS Latency)을 얼마로 할 것인지, BL(Burst Length)은 16인지 32인지, ODT 임피던스는 어떤 값으로 할 것인지, training 모드에 진입할 것인지 — DRAM의 모든 가변 동작이 MR에 기록된 값에 의해 결정됩니다. DRAM은 power-on 시 default 값으로 시작하고, controller가 MR을 write하면서 시스템 요구에 맞는 설정을 구성합니다.

DDR4는 MR0~MR6 (7개)로 충분했지만, DDR5는 **MR0~MR254** (이론상)까지 확장되었습니다. 2-cycle command, per-DQ DFE 계수, DCA 설정, Rowhammer 대응 RFM 임계치 등 DDR5가 새로 도입한 기능들이 모두 MR로 제어되기 때문입니다. DV 엔지니어 입장에서 250개를 모두 외울 수는 없고, 카테고리로 묶어 필요할 때 정확히 찾는 능력이 중요합니다.

### 1.1 MR 접근 명령

| 명령 | DDR4 | DDR5 | LPDDR4 | LPDDR5 |
|---|---|---|---|---|
| MR Write | MRS | **MRW** | MRW | MRW |
| MR Read | MPR-based (간접) | **MRR** (직접) | MRR | MRR |

DDR5부터 MRR(Mode Register Read)이 직접 명령으로 지원됩니다. DDR4는 MPR(Multi-Purpose Register)을 통해 우회해야 했는데, MR 내용을 DQ로 직접 읽어내는 경로가 없었기 때문입니다. DDR5에서 MRR이 독립 명령으로 추가된 덕분에, controller는 현재 MR 값을 직접 readback하고 RAL(Register Abstraction Layer)의 mirror value와 비교 검증할 수 있게 되었습니다.

---

## 2. DDR5 Mode Register 카테고리 — 250+ 개를 어떻게 정리하나

> 출처: JESD79-5C.01 v1.31 §3.5

MR을 번호 순서대로 외우는 것은 비효율적입니다. 기능별 카테고리로 묶어두면, "DFE 설정이 어디 있더라?" 하는 상황에서 즉시 MR111~MR116 구간을 떠올릴 수 있습니다. 이 검색 능력이 실무에서 스펙을 빠르게 참조하는 핵심 역량입니다.

### 2.1 카테고리별 분류 표

| 카테고리 | MR 번호 | 목적 |
|---|---|---|
| **기본 동작** | MR0, MR2 | BL, CL, Functional Modes |
| **PDA / Training Mode** | MR1, MR3, MR25~MR31 | PDA Mode, DQS Training, Read Training |
| **Refresh** | MR4, MR58, MR59, MR60 | Refresh Settings, RFM, DRFM/ARFM, PASR |
| **IO 설정** | MR5, MR6, MR7 | IO Settings, Write Recovery, Write Leveling |
| **Preamble/Postamble** | MR8 | Read/Write preamble length |
| **Vref Calibration** | MR10, MR11, MR12 | VrefDQ, VrefCA, VrefCS |
| **Clock/CS** | MR13 | SRX, CS Geardown, tCCD_L, tDLLK |
| **ECC (Transparency)** | MR14, MR15, MR16~MR20 | ECC config, threshold, error report |
| **Rx CTLE / MBIST** | MR21, MR22, MR23, MR24 | Receiver equalizer, BIST, PPR Guard Key |
| **ODT** | MR32~MR40 | RTT_PARK/WR/NOM, ODTL offset |
| **DCA (Duty Cycle Adjuster)** | MR42~MR48 | DCA settings (group) |
| **CRC / Loopback** | MR50, MR51, MR52, MR53 | Write CRC, threshold, loopback |
| **hPPR** | MR54~MR57 | hPPR Resources |
| **Vendor / Scratch** | MR62, MR63 | Vendor-specific, scratch pad |
| **NVRAM / Serial** | MR64~MR69 | Serial number, NVRAM paging |
| **DFE** | MR70~MR75, MR111~MR116 | Decision Feedback Equalization (global + per-tap) |
| **DCA per-DQ** | MR103~MR254 | DQ별 DCA 설정 (DQL/DQU × 8 = 16 lanes, 각 several MRs) |
| **Vendor Specified** | MR62 | Vendor 자유 영역 |
| **Misc** | MR9 (Writeback Suppression), MR61 (Output Driver Test) | 특수 모드 |

> 위는 *분류*이지 *전수*가 아닙니다. MR 번호 일부는 RFU(Reserved For Future Use)이며, 변경은 JEDEC revision마다 검토 필요합니다.

### 2.2 자주 마주치는 MR — DV 우선순위 Top 10

| 우선순위 | MR | 이유 |
|---|---|---|
| 1 | MR0 (BL, CL) | 모든 RD/WR timing의 기본 |
| 2 | MR2 (Functional Modes) | DLL on/off, Test mode 등 |
| 3 | MR4 (Refresh Settings) | refresh rate, RFM enable, temp range |
| 4 | MR5 (IO Settings) | Output drive strength, ODT range |
| 5 | MR8 (Preamble/Postamble) | Read/Write preamble — 잘못되면 sampling fail |
| 6 | MR13 (SRX, CS Geardown, tCCD_L) | CS training과 직결 |
| 7 | MR14, MR15 (Transparency ECC) | ECC enable, threshold |
| 8 | MR21 (Rx CTLE) | DDR5 receiver equalizer |
| 9 | MR58 (Refresh Management) | RFM enable, RAA threshold |
| 10 | MR59 (DRFM/ARFM RAA Counter) | RAA tracking |

---

## 3. DDR5 MR 비트 디코드 — MR4 (Refresh Settings) 예시

> 출처: JESD79-5C.01 §3.5.6

### 3.1 MR4 비트 필드 (개념)

| 비트 | 필드 | 값/의미 |
|---|---|---|
| OP[7:5] | tREFI Mode | 0=fixed 7.8us, 다른 값=variable |
| OP[4:3] | Refresh Trfc Mode | Standard / 2x mode |
| OP[2:0] | Refresh Range | Normal / Extended Temp |

> 정확한 비트 매핑은 JEDEC 스펙 원문을 *반드시* 확인하세요. 본 자료의 표는 *학습용 모형*이며 실제 비트 매핑과 다를 수 있습니다 *(추론)*.

### 3.2 MR4 의 *어떤 비트를 바꾸면 어떤 효과*가 나는가

- `tREFI Mode = fixed` → controller가 정확히 7.8us 간격으로 REF 발급
- `tREFI Mode = variable` → controller가 8 REF를 *deferred* 가능 (FGR-like)
- `Refresh Range = Extended` → 95°C까지 동작, 단 tREFI 절반 (3.9us)

이런 *조합*이 *coverage cross point*가 됩니다.

---

## 4. RAL (Register Abstraction Layer) 모델링

### 4.1 왜 RAL이 필요한가

MR을 일일이 직접 MRW/MRR 명령으로 접근하는 방식으로만 testbench를 짜면, 여러 문제가 누적됩니다. 우선 backdoor access가 없으니 시뮬레이션 속도가 느려집니다. 더 심각한 것은 mirror value를 코드 안에서 추적할 방법이 없다는 점인데, 결국 "현재 MR0의 BL 설정이 뭐지?" 하는 질문에 직접 MRR을 발급해야만 답을 얻을 수 있게 됩니다. 또한 power-on reset 직후 default 값이 맞는지 자동 검증하거나, write 후 readback이 일치하는지 consistency 검사를 체계적으로 수행하기도 어렵습니다.

RAL을 쓰면 register model 객체가 DRAM 내부 MR과 동기화된 mirror를 유지하며, frontdoor/backdoor 전환, reset value 검증, write consistency 확인이 모두 깔끔하게 처리됩니다.

### 4.2 UVM RAL skeleton

```systemverilog
// 파일: ddr5_ral_pkg.sv
// 출처 인용: JESD79-5C.01 §3.5 — MR 정의
package ddr5_ral_pkg;
  import uvm_pkg::*;
  `include "uvm_macros.svh"

  // ==== MR4 — Refresh Settings ====
  class ddr5_reg_MR4 extends uvm_reg;
    `uvm_object_utils(ddr5_reg_MR4)

    rand uvm_reg_field refresh_range;     // OP[2:0]
    rand uvm_reg_field trfc_mode;          // OP[4:3]
    rand uvm_reg_field trefi_mode;         // OP[7:5]

    function new(string name = "ddr5_reg_MR4");
      super.new(name, 8, UVM_NO_COVERAGE);
    endfunction

    virtual function void build();
      refresh_range = uvm_reg_field::type_id::create("refresh_range");
      refresh_range.configure(this, 3, 0, "RW", 0, 3'b000, 1, 1, 0);

      trfc_mode = uvm_reg_field::type_id::create("trfc_mode");
      trfc_mode.configure(this, 2, 3, "RW", 0, 2'b00, 1, 1, 0);

      trefi_mode = uvm_reg_field::type_id::create("trefi_mode");
      trefi_mode.configure(this, 3, 5, "RW", 0, 3'b000, 1, 1, 0);
    endfunction
  endclass

  // ==== MR0 — BL / CL ====
  class ddr5_reg_MR0 extends uvm_reg;
    `uvm_object_utils(ddr5_reg_MR0)
    rand uvm_reg_field bl;
    rand uvm_reg_field cl;
    function new(string name = "ddr5_reg_MR0");
      super.new(name, 8, UVM_NO_COVERAGE);
    endfunction
    virtual function void build();
      bl = uvm_reg_field::type_id::create("bl");
      bl.configure(this, 2, 0, "RW", 0, 2'b00, 1, 1, 0);
      cl = uvm_reg_field::type_id::create("cl");
      cl.configure(this, 6, 2, "RW", 0, 6'd22, 1, 1, 0);
    endfunction
  endclass

  // ==== DDR5 RAL Block ====
  class ddr5_ral_block extends uvm_reg_block;
    `uvm_object_utils(ddr5_ral_block)
    rand ddr5_reg_MR0 MR0;
    rand ddr5_reg_MR4 MR4;
    // ... MR1 ~ MR254 (필요한 것만 build) ...

    function new(string name = "ddr5_ral_block");
      super.new(name, UVM_NO_COVERAGE);
    endfunction

    virtual function void build();
      default_map = create_map("default_map", 0, 1, UVM_LITTLE_ENDIAN, 0);

      MR0 = ddr5_reg_MR0::type_id::create("MR0");
      MR0.configure(this, null, "");
      MR0.build();
      default_map.add_reg(MR0, 8'h00, "RW");

      MR4 = ddr5_reg_MR4::type_id::create("MR4");
      MR4.configure(this, null, "");
      MR4.build();
      default_map.add_reg(MR4, 8'h04, "RW");

      // ... 다른 MR 추가 ...

      lock_model();
    endfunction
  endclass

endpackage
```

### 4.3 MR write/read 시퀀스 (RAL 사용)

```systemverilog
class ddr5_mrw_seq extends uvm_sequence;
    `uvm_object_utils(ddr5_mrw_seq)

    ddr5_ral_block ral;  // 외부 주입

    rand bit [1:0] bl_val;
    rand bit [5:0] cl_val;
    constraint c_legal_cl { cl_val inside {[22:46]}; }
                                    // DDR5 CL range 가정 (speed bin 따라 다름)

    virtual task body();
        uvm_status_e status;
        ral.MR0.bl.set(bl_val);
        ral.MR0.cl.set(cl_val);
        ral.MR0.update(status);   // mirror → DUT 동기화
        if (status != UVM_IS_OK)
            `uvm_error("RAL", $sformatf("MR0 update failed, status=%s", status.name()))

        // Read back으로 verify
        ral.MR0.read(status, .value(), .path(UVM_FRONTDOOR));
        if (ral.MR0.bl.get() != bl_val)
            `uvm_error("RAL_VERIFY", "MR0.bl mismatch after read-back")
    endtask
endclass
```

### 4.4 MR Write/Read coverage

```systemverilog
covergroup mr_access_cg with function sample (
    bit [7:0] mr_num,
    bit       is_write
);
    cp_mr: coverpoint mr_num {
        bins basic[]     = {0, 1, 2, 3, 4, 5, 6, 7, 8};      // 기본 MR
        bins ecc[]       = {14, 15, 16, 17, 18, 19, 20};      // ECC 관련
        bins odt[]       = {32, 33, 34, 35, 36, 37, 38};      // ODT
        bins dca[]       = {42, 43, 44, 45, 46, 47, 48};      // DCA
        bins refresh[]   = {4, 58, 59, 60};                   // Refresh
        bins ppr[]       = {54, 55, 56, 57};                  // hPPR
        bins dfe_global[]= {70, 71, 72, 73, 74, 75, 111, 112, 113, 114, 115, 116};  // DFE
        bins others      = default;
    }
    cp_rw: coverpoint is_write {
        bins write = {1};
        bins read  = {0};
    }
    cx_mr_rw: cross cp_mr, cp_rw;
endgroup
```

---

## 5. *재초기화 필요한* MR vs *런타임 변경 가능한* MR

### 5.1 분류

모든 MR을 아무 때나 변경할 수 있는 것은 아닙니다. 일부 MR은 DRAM 내부 회로가 특정 상태일 때만 안전하게 변경할 수 있고, 잘못된 타이밍에 변경하면 내부 타이밍 경로나 training 결과가 무효화됩니다.

| 분류 | 예시 MR | 비고 |
|---|---|---|
| **Init only** | MR3 (DQS Training), CS Geardown 등 | 재초기화 필요 |
| **Runtime updatable (제약 조건 하)** | MR5 (Output drive), MR8 (preamble) | Self-refresh 또는 PD 진입 후 변경 |
| **Freely updatable** | MR62 (vendor), MR63 (scratch) | 언제든 |
| **Read-only** | MR16~MR20 (error report) | DRAM이 자동 update |

### 5.2 DV 검증 포인트

이 분류는 DV에서 negative testing의 기반이 됩니다. Init-only MR을 runtime에 변경하면 undefined behavior이 발생할 수 있는데 시뮬레이션이 조용히 통과하면 silicon에서 예측 불가능한 동작으로 이어집니다. SVA로 각 MR의 접근 시점 제약을 즉시 검증하고, directed test에서 의도적으로 위반 시퀀스를 발급해 assertion이 이를 catch하는지 확인하는 것이 중요합니다.

- **Init-only MR을 런타임에 변경하려는 시도** → SVA로 catch
- **Runtime updatable MR을 적절한 idle 상태 없이 변경** → SVA로 catch
- **Read-only MR에 write 시도** → DRAM 모델이 무시하는지 확인

```systemverilog
// Init-only MR을 런타임에 write 시도 catch
property p_init_only_mr_runtime;
    @(posedge clk) disable iff (reset_n == 0)
    (cmd == MRW && mr_num inside {3, 13}) |->
        (state == STATE_INIT) || (state == STATE_SELF_REFRESH);
endproperty
a_init_only_mr: assert property (p_init_only_mr_runtime)
    else `uvm_error("ASSERT", $sformatf("MR%0d written in runtime state", mr_num))
```

---

## 6. LPDDR5 의 Three Physical MR — CBT를 위한 특수 구조

> 출처: JESD209-5C §4.2.2.1, §6

LPDDR5는 Command Bus Training(CBT)에서 *3 physical MR*을 사용합니다. CBT 모드에서 *임시*로 활성화되어 DRAM과 host가 CA 신호를 정확히 정렬할 때 사용. 일반 MR과는 *접근 방식*이 다릅니다.

DV는 CBT 시퀀스 동안 *physical MR 접근 vs logical MR 접근*을 구별해서 monitor/scoreboard에 반영해야 합니다 (Ch08에서 다룸).

---

## 7. 대표 문제 — DDR5 MR4 decode dry-run + RAL update

!!! question "Q. DDR5 controller가 MR4=8'b001_01_010 (OP[7:5]=001, OP[4:3]=01, OP[2:0]=010) 을 MRW 하려 한다. (1) 각 필드의 의미를 해석하고 (2) RAL을 통해 이 값을 write하는 코드를 작성하고 (3) 후속 RD/WR이 normal-temp range에서는 정상이지만 extended-temp range에서 timing violation이 생긴다면 어디를 의심해야 하는가?"

???+ answer "풀이 (해석 + RAL 코드 + debug 사고)"

    **Step 1 — 비트 해석** *(추론 — Ch04 §3.1 의 모형 표 기준)*

    - OP[7:5] = 3'b001 → tREFI Mode (variable, 또는 fixed 의 다른 값)
    - OP[4:3] = 2'b01 → Refresh tRFC Mode (Standard 또는 2x 가운데 하나 — 정확한 매핑은 스펙 표 참조)
    - OP[2:0] = 3'b010 → Refresh Range (extended temp 의 일부 — 정확한 매핑은 스펙 표 참조)

    > 실제 비트 매핑은 JESD79-5C.01 §3.5.6 의 OP 표를 보고 확인하세요. 본 풀이는 *해석 방법*을 보여주는 데 목적이 있습니다.

    **Step 2 — RAL을 통한 write 코드**

    ```systemverilog
    uvm_status_e status;
    ral.MR4.trefi_mode.set(3'b001);
    ral.MR4.trfc_mode.set(2'b01);
    ral.MR4.refresh_range.set(3'b010);
    ral.MR4.update(status);  // mirror update → frontdoor MRW 명령 발급
    ```

    **Step 3 — Extended-temp에서 timing violation이라면?**

    Extended temperature range (예: 85~95°C)에서는 *tREFI가 절반*이 되어야 합니다. 만약 controller가 MR4의 refresh_range 비트를 *읽지 않고* 일반 tREFI를 그대로 사용하면, 데이터 유실 위험. timing checker가 *위반*을 catch.

    **의심 순서**:
    1. MR4 mirror value가 update되었는지 RAL `ral.MR4.refresh_range.get()` 확인
    2. Controller RTL이 MR4의 refresh_range 비트를 *실제로* 디코드하는지 (signal trace)
    3. Refresh interval logic이 *동적으로* tREFI를 조정하는지
    4. Timing checker가 *temperature-aware*인지 — 동일 tREFI으로 두 range를 검증하면 false fail/pass

    **DV 보완**:
    - covergroup `refresh_range_cg`에 `normal_temp / extended_temp` 각각 bin
    - directed test: MR4를 extended로 set 후 *고온 시뮬레이션 시나리오*에서 tREFI 절반인지 monitor 측정
    - SVA: `tREFI 위반` assertion — temperature mode에 따라 *동적 threshold*

---

## 8. PDF 정밀 인용 — DDR5 MR 비트 매핑 + MRR/MRW 동작

> 출처: JESD79-5C.01 v1.31 §3.4 (MRR, MRW), §3.5 (Mode Registers), Tables 14~24

### 8.1 DDR5 MR 인코딩 방식의 변화 (§3.5 원문)

> JESD79-5C.01 §3.5 인용:
>
> "With DDR5, the utilization and programming method shall change from the traditional addressing scheme found in DDR3 and DDR4, and **shall move to the method used by LPDDR, where the Mode Register Addresses (MRA) and Payload placed in Op Codes (OP) are all packed in the command bus encoding method**. Please refer to the Command Truth Table 30 for Mode Register Read (MRR) and Mode Register Write (MRW) command protocol."
>
> "For DDR5, the SDRAM shall support **up to 8 MRA's, each with a byte-wide payload. Allowing for up to 256 byte-wide registers**."

핵심:
- MR addressing 방식이 *DDR3/4 스타일* → *LPDDR 스타일* 로 변경
- *8-bit MRA* (Mode Register Address) + *8-bit OP* (Op Code = payload)
- 최대 *256개의 byte-wide MR* 지원 (MR0~MR255 이론상)

### 8.2 MR 비트 정의 규약 (§3.5.1)

> §3.5.1 원문 인용:
> "Each bit in a register byte (MR#) is denoted as **'R'** if it can be read but not written, **'W'** if it can be written but reads shall always produce a ZERO for those specific bits, and **'R/W'** if it can be read and written. Additionally, a DRAM read-only bit combined with a Host write-only bit is denoted as a **'SR/W'** bit. This bit allows the DRAM to return a defined status during a read of that bit (SR = Status Read), independent of what the Host may have written to the bit."

| 비트 종류 | 의미 |
|---|---|
| `R` | Read only — host가 write 시도 시 결과 미정 |
| `W` | Write only — host read는 항상 0 |
| `R/W` | Read/Write 모두 가능 |
| `SR/W` | Read-only (DRAM이 status 반환) + Write-only (host write 가능, but read는 status) |

**RFU (Reserved For Future Use)**:
- *RFU bit*: write 시 host는 0 write 필수. DRAM은 그 bit의 동작을 *보장 X*. read 시 항상 0.
- *RFU MR (entire byte)*: read/write 모두 don't care. 일부 device는 *unsupported* 가능.

**Device-specific MR**:
- x16용 MR이 *x4/x8 device에서는 RFU*로 간주 — don't care.
- 다른 density/config 용 bit field는 host가 write/read 가능하지만 *동작 영향 X*.

### 8.3 Table 24 — DDR5 MR Assignment (MR0~MR7 정확한 비트 매핑)

> 출처: JESD79-5C.01 §3.5.1, Table 24 (정확 인용)

| MR# | OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|---|
| **MR0** | RFU | CAS Latency (RL) [OP6:2] | ← | ← | ← | ← | Burst Length [OP1:0] | ← |
| **MR1** | PDA Select ID [OP7:5] | ← | ← | PDA Enumerate ID [OP4:0] | ← | ← | ← | ← |
| **MR2** | Internal Write Timing | Reserved | Device 15 MPSM | CS Assertion Duration (MPC) | Max Power Saving Mode (MPSM) | 2N Mode | Write Leveling Training | Read Preamble Training |
| **MR3** | Write Leveling Internal Cycle Alignment — Upper Byte [OP7:4] | ← | ← | ← | Write Leveling Internal Cycle Alignment — Lower Byte [OP3:0] | ← | ← | ← |
| **MR4** | TUF | RFU | Wide Range (Optional) | Refresh tRFC Mode | Refresh Interval Rate Indicator | Minimum Refresh Rate [OP2:0] | ← | ← |
| **MR5** | Pull-Down Output Driver Impedance [OP7:5] | ← | ← | DM Enable | TDQS Enable | PODTM Support | Pull-up Output Driver Impedance / Data Output Disable [OP3:0] | ← |
| **MR6** | tRTP [OP7:4] | ← | ← | ← | Write Recovery Time [OP3:0] | ← | ← | ← |
| **MR7** | RFU [OP7:2] | ← | ← | ← | ← | ← | (Optional) Write Leveling Internal +0.5tCK Alignment Offset — Upper Byte | Lower Byte |

> 주의: 위 표의 일부 cell 그룹은 *spec 원본의 merged cell*을 줄 단위로 표현. *실제 비트 폭 (단일 비트 vs 다중 비트)* 은 spec 원본을 확인.

### 8.4 핵심 MR 의 OP 인코딩 (default 값 기반)

> 출처: JESD79-5C.01 §3.3 Table 9 + §3.5.2 (MR0)

**MR0 — CAS Latency (CL) / Burst Length**

| OP[1:0] (Burst Length) | 의미 |
|---|---|
| `00B` (default) | BL16 |
| `01B` | BC8 OTF (optional) |
| `10B` | BL32 (optional) |
| `11B` | BL32 OTF (optional) |

| OP[6:2] (CAS Latency RL) | 값 (DDR5-3200 기준) |
|---|---|
| `00000B` | RL=22 |
| `00001B` | RL=24 |
| `00010B` (default) | **RL=26** |
| `00011B` | RL=28 |
| `00100B` | RL=30 |
| ... | (speed bin에 따라) |

> Default `00010B` = RL=26 @ DDR5-3200. 더 높은 speed bin일수록 RL nCK 값 증가.

**MR6 — Write Recovery Time / tRTP**

| OP[3:0] (WR) | nCK @ DDR5-3200 |
|---|---|
| `0000B` (default) | **48 nCK or 30 ns** |
| ... | (speed bin별) |

| OP[7:4] (tRTP) | nCK @ DDR5-3200 |
|---|---|
| `0000B` (default) | **12 nCK or 7.5 ns** |
| ... | (speed bin별) |

### 8.5 MRR/MRW 동작 — §3.4.1, §3.4.2 원문 인용

> §3.4.1 MRR (원문 인용):
> "The Mode Register Read (MRR) command is used to read configuration and status data from the DDR5-SDRAM registers. The MRR command is initiated with **CS_n and CA[13:0] in the proper state as defined by the Command Truth Table**. The mode register address operands (MA[7:0]) allow the user to select one of **256 registers**. The mode register contents are available **on the second 8 UI's of the burst** and are repeated across all DQ's after the CL following the MRR command."
>
> "DQS is toggled for the duration of the MRR burst. **The MRR has a command burst length 16** regardless of the MR0 setting, the training mode or the mode register address."

> §3.4.2 MRW (원문 인용):
> "The Mode Register Write (MRW) command is used to write configuration data to the mode registers. The MRW command is initiated with CS_n and CA[13:0] in the proper state as defined by the Command Truth Table. The mode register address and the data written to the mode registers is contained in CA[13:0] according to the Command Truth Table. **The MRW command period is defined by tMRW**."
>
> "MRW commands require **all banks to be idle on the DRAM**. For 3DS, MRW commands are broadcast across all logical ranks, requiring all banks to be idle on all logical ranks."

### 8.6 Table 14 — MRR DQ Output Mapping (x4 Device)

> 출처: JESD79-5C.01 §3.4.1, Table 14 인용

| BL | 0~7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|
| DQ0 | 0 | OP0 | OP1 | OP2 | OP3 | OP4 | OP5 | OP6 | OP7 |
| DQ1 | 1 | !OP0 | !OP1 | !OP2 | !OP3 | !OP4 | !OP5 | !OP6 | !OP7 |
| DQ2 | 0 | OP0 | OP1 | OP2 | OP3 | OP4 | OP5 | OP6 | OP7 |
| DQ3 | 1 | !OP0 | !OP1 | !OP2 | !OP3 | !OP4 | !OP5 | !OP6 | !OP7 |

핵심:
- **BL0~7**: marker pattern (짝수 DQ = 0, 홀수 DQ = 1). worst-case data pattern 방지 목적.
- **BL8~15**: MR의 OP[0]~OP[7] 출력
- 홀수 DQ는 *inverted output* — receiver가 differential pair처럼 활용 가능 (signal integrity)
- 출처 인용: "To avoid a potentially worst-case pattern, **every odd DQ bit (represented with !) shall have its contents inverted**."

### 8.7 Table 20 — Mode Register Read/Write AC Timing (정확 수치)

> 출처: JESD79-5C.01 §3.4.4, Table 20

| Parameter | Symbol | Min/Max | Value | Unit |
|---|---|---|---|---|
| Mode Register Read command period | `tMRR` | Min | **max(14ns, 16 nCK)** | nCK |
| MRR Pattern to MRR Pattern Command spacing | `tMRR_p` | Min | **8 nCK** | nCK |
| Mode Register Write command period | `tMRW` | Min | **max(5ns, 8 nCK)** | nCK |
| Mode Register Set command delay | `tMRD` | Min | **max(14ns, 16 nCK)** | nCK |
| DFE Mode Register Write Update Delay Time | `tDFE` | Min | **80 ns** | ns |

> Note 1: MRR and MRW commands require all banks idle.
> Note 2: tDFE applies to MR112~MR248 (DFE registers) — *settling time before a new DFE setting is active*.

### 8.8 Table 22 — MRR/MRW Timing Constraints (DQ ODT Disable)

> 출처: JESD79-5C.01 §3.4.4, Table 22

| From | To | Minimum Delay | Note |
|---|---|---|---|
| MRR | MRR | `tMRR / tMRR_p` | Read Training 시 tMRR_p 적용 |
| MRR | MRW | `CL + BL/2 + max[1, ODTLoff_RD_NT_Offset]` (tCK) | |
| MRR | MPC | `CL + BL/2 + max[1, ODTLoff_RD_NT_Offset]` (tCK) | |
| MRR | VrefCA/VrefCS | `CL + BL/2 + max[1, ODTLoff_RD_NT_Offset]` (tCK) | |
| MRR | Any other valid command | `tMRD` | |
| MRW | MRW | `tMRW` | |
| MRW | Any other valid command | `tMRD` | |
| WRA | MRR/MRW | `CWL + BL/2 + tWR + tRP` | Auto-precharge 후 |
| RDA | MRR/MRW | `tRTP + tRP` | |
| PRE | MRR/MRW | `tRP` | |
| REF | MRR/MRW | `tRFC` | |

!!! tip "DV 적용 — MRR/MRW timing SVA"
    ```systemverilog
    // 출처: JESD79-5C.01 §3.4.4 Table 22
    property p_mrr_to_mrw_delay;
        @(posedge clk)
        (cmd_decoded == CMD_MRR) |->
            ##[CL_NCK + BL/2 + 1 : $]
            first_match(cmd_decoded == CMD_MRW);
    endproperty
    a_mrr_to_mrw: assert property (p_mrr_to_mrw_delay);

    property p_mrw_to_mrw_delay;
        @(posedge clk)
        (cmd_decoded == CMD_MRW) |->
            ##[TMRW_NCK : $]
            first_match(cmd_decoded == CMD_MRW);
    endproperty
    a_mrw_to_mrw: assert property (p_mrw_to_mrw_delay);

    // PRE → MRR 도 tRP 이상 보장
    property p_pre_to_mrr_trp;
        @(posedge clk)
        (cmd_decoded == CMD_PRE) |->
            ##[TRP_NCK : $]
            first_match(cmd_decoded == CMD_MRR);
    endproperty
    a_pre_to_mrr: assert property (p_pre_to_mrr_trp);
    ```

### 8.9 Table 21 — MRR/MRW Truth Table (State 전이)

> 출처: JESD79-5C.01 §3.4.4, Table 21

| Current State (SDRAM) | Command | Intermediate State | Next State |
|---|---|---|---|
| All Banks Idle | MRR | Mode Register Reading (All Banks Idle) | All Banks Idle |
| All Banks Idle | MRW | Mode Register Writing (All Banks Idle) | All Banks Idle |

> Note 1: For 3DS, both MRR and MRW require all banks idle on all logical ranks.

DV 시사점:
- MRR/MRW 는 *idle state*에서만 발급. *active bank가 있는 상태*에서 발급은 *spec violation*.
- 3DS DRAM (Through-Silicon Via stacked) 의 경우 *모든 logical rank*가 idle 해야 함.

```systemverilog
// 출처: Table 21 — MRR/MRW require All Banks Idle
property p_mrr_mrw_only_in_idle;
    @(posedge clk) disable iff (!reset_n)
    (cmd_decoded inside {CMD_MRR, CMD_MRW}) |->
        all_banks_idle();
endproperty
a_mrr_mrw_idle: assert property (p_mrr_mrw_only_in_idle)
    else `uvm_error("SVA_MR", "MRR/MRW issued while bank active")
```

### 8.10 DDR5 MR4 (Refresh Settings) — 정확한 비트 매핑

> 출처: Table 24

| OP | 필드 | 의미 |
|---|---|---|
| OP[7] | **TUF** (Thermal Update Flag) | Status flag — read-only |
| OP[6] | RFU | 0 write |
| OP[5] | **Wide Range (Optional)** | Extended temperature range support |
| OP[4] | **Refresh tRFC Mode** | 0 = standard tRFC, 1 = optional |
| OP[3] | **Refresh Interval Rate Indicator** | 1x vs 0.5x interval |
| OP[2:0] | **Minimum Refresh Rate** | Encoded refresh rate |

> Default = `0000_0000B` (Table 9의 MR4는 별도 표기 없음 — 위 매핑은 Table 24 기반)

**MR4 의 TUF (Thermal Update Flag) 의 의미**: DRAM 내부 온도 상승 등으로 MR4 settings update가 필요할 때 set. DV는 *thermal model* 시뮬레이션 시 TUF 비트가 *정확한 시점에 set/clear*되는지 검증.

```systemverilog
covergroup mr4_cg with function sample (bit [7:0] mr4_val);
    cp_tuf: coverpoint mr4_val[7] {
        bins tuf_clear = {0};
        bins tuf_set   = {1};
    }
    cp_wide_range: coverpoint mr4_val[5] {
        bins normal_range   = {0};
        bins wide_range     = {1};
    }
    cp_trfc_mode: coverpoint mr4_val[4] {
        bins standard = {0};
        bins optional = {1};
    }
    cp_interval_rate: coverpoint mr4_val[3] {
        bins normal_1x  = {0};
        bins half_0p5x  = {1};
    }
    cp_min_refresh: coverpoint mr4_val[2:0] {
        bins all_rates[] = {[0:7]};
    }
endgroup
```

## 9. 핵심 정리 (Key Takeaways)

- DDR5의 MR은 *MR0~MR254*까지 확장. **인코딩 방식이 LPDDR style로 변경** — 8-bit MRA + 8-bit OP가 *command bus에 packed*.
- DDR4는 MRS만, DDR5는 *MRW + MRR* (Read 직접 지원).
- MR 비트는 `R`/`W`/`R/W`/`SR/W` 분류. **RFU는 write 시 0 강제**.
- LPDDR5는 CBT용 *3 physical MR* 특수 구조.
- UVM RAL로 MR을 모델링하면 mirror update + 자동 검증이 깔끔.
- MR은 *init-only*, *runtime updatable(제약 하)*, *freely updatable*, *read-only*로 분류. SVA로 위반 catch 필수.
- **MR0**: OP[1:0]=BL, OP[6:2]=CL. **MR4**: refresh 관련 + TUF flag. **MR6**: tRTP + tWR.
- **MRR burst**: BL16 고정. BL0~7은 marker (0/1), BL8~15가 실제 MR 값. 홀수 DQ는 inverted.
- **MRR/MRW**: All banks idle 필수. tMRR=max(14ns,16nCK), tMRW=max(5ns,8nCK), tMRD=max(14ns,16nCK).
- **DFE MR (MR112~248)**: tDFE = 80ns settling time.
- MR write/read coverage는 *MR 번호 × write/read* cross + *각 핵심 MR의 비트 필드별 cross*.

## 10. Further Reading

- 이전: [Ch03. 초기화·Reset·Power](03_init_reset_power.md)
- 다음: [Ch05. Command·Truth Table·Burst Operation](05_commands_burst.md)
- 부록: [JEDEC Spec 빠른 참조](appendix_a_quick_reference.md)
- 퀴즈: [Ch04 퀴즈](quiz/ch04_quiz.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../03_init_reset_power/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch03. 초기화·Reset·Power</div>
  </a>
  <a class="nav-next" href="../05_commands_burst/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch05. Command·Burst</div>
  </a>
</div>
