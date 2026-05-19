# Ch04. Mode Register 깊이 분석

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="index.md"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
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

Mode Register(MR)는 DRAM 동작을 *런타임에 설정*하기 위한 *제어 레지스터*입니다. CL(CAS Latency), BL(Burst Length), ODT 강도, training 모드 등 DRAM의 모든 가변 동작이 MR로 제어됩니다.

DDR4는 MR0~MR6 (7개)로 충분했지만, DDR5는 **MR0~MR254** (이론상)까지 확장되었습니다 — 그만큼 *설정해야 할 것이 많아진* 것입니다.

### 1.1 MR 접근 명령

| 명령 | DDR4 | DDR5 | LPDDR4 | LPDDR5 |
|---|---|---|---|---|
| MR Write | MRS | **MRW** | MRW | MRW |
| MR Read | MPR-based (간접) | **MRR** (직접) | MRR | MRR |

DDR5부터 *MRR (Mode Register Read)*이 직접 명령으로 지원됩니다. DDR4의 MPR(Multi-Purpose Register)을 통한 우회보다 깔끔합니다.

---

## 2. DDR5 Mode Register 카테고리 — 250+ 개를 어떻게 정리하나

> 출처: JESD79-5C.01 v1.31 §3.5

직접 모든 MR을 외울 수는 없습니다. *카테고리*로 묶어 *필요할 때 정확한 MR을 찾는* 능력이 DV 엔지니어의 실력입니다.

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

MR을 일일이 직접 명령으로 write/read하면:
- backdoor access 불가 → 시뮬레이션 느려짐
- mirror value 추적 불가 → 어떤 MR이 어떤 값인지 코드에서 추적 어려움
- automated check 불가 → reset value 확인, write/read consistency 검증 어려움

RAL을 쓰면 *register model* 객체가 *DRAM 내부 MR과 동기화*되어 위 모든 문제가 해결됩니다.

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

| 분류 | 예시 MR | 비고 |
|---|---|---|
| **Init only** | MR3 (DQS Training), CS Geardown 등 | 재초기화 필요 |
| **Runtime updatable (제약 조건 하)** | MR5 (Output drive), MR8 (preamble) | Self-refresh 또는 PD 진입 후 변경 |
| **Freely updatable** | MR62 (vendor), MR63 (scratch) | 언제든 |
| **Read-only** | MR16~MR20 (error report) | DRAM이 자동 update |

### 5.2 DV 검증 포인트

- **Init-only MR을 런타임에 변경하려는 시도** → SVA로 catch
- **Runtime updatable MR을 적절한 *idle* 상태 없이 변경** → SVA로 catch
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

## 8. 핵심 정리 (Key Takeaways)

- DDR5의 MR은 *MR0~MR254*까지 확장 — 카테고리(기본/ODT/DCA/DFE/ECC 등)로 묶어 이해.
- DDR4는 MRS만, DDR5는 *MRW + MRR* (Read 직접 지원).
- LPDDR5는 CBT용 *3 physical MR* 특수 구조.
- UVM RAL로 MR을 모델링하면 mirror update + 자동 검증이 깔끔.
- MR은 *init-only*, *runtime updatable(제약 하)*, *freely updatable*, *read-only*로 분류. SVA로 위반 catch 필수.
- MR write/read coverage는 *MR 번호 × write/read* cross로 모든 MR이 쓰이는지 확인.

## 9. Further Reading

- 이전: [Ch03. 초기화·Reset·Power](03_init_reset_power.md)
- 다음: [Ch05. Command·Truth Table·Burst Operation](05_commands_burst.md)
- 부록: [JEDEC Spec 빠른 참조](appendix_a_quick_reference.md)
- 퀴즈: [Ch04 퀴즈](quiz/ch04_quiz.md)

<div class="chapter-nav">
  <a class="nav-prev" href="03_init_reset_power.md">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch03. 초기화·Reset·Power</div>
  </a>
  <a class="nav-next" href="05_commands_burst.md">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch05. Command·Burst</div>
  </a>
</div>
