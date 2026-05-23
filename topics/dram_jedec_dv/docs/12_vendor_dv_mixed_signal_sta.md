# Ch12. DRAM Vendor 설계검증 — Mixed-Signal · STA · Custom Circuit · DFT

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">CH 12</span>
</div>

!!! tip "이 챕터의 위치"
    Ch01~Ch11은 *시스템 측 DV* (controller IP / SoC) 관점이었습니다.
    Ch12는 **DRAM vendor 측 (Samsung / SK Hynix / Micron) 설계검증 관점**으로 확장합니다.
    같은 spec, *다른 추상화 수준* — circuit-level + RTL-level + STA + DFT가 모두 등장합니다.
    SK Hynix DRAM 설계검증 직무 JD (Logic / Timing / Quality 3축) 와 정렬.

## 🎯 Learning Objectives

- **Distinguish**: 시스템 DV (controller) 와 DRAM vendor 설계검증의 *검증 대상·도구·추상화* 차이를 구별한다.
- **Describe**: DRAM 내부 핵심 Custom 회로 (Sense Amp, SWE, X-DEC/Y-DEC) 의 동작과 *검증 challenge*를 서술한다.
- **Apply**: Analog & Digital Mixed Simulation (Hspice/PrimeSim/Spectre) 워크플로우를 적용한다.
- **Design**: Static Timing Analysis (STA) sign-off 흐름을 설계한다.
- **Trace**: Antifuse 기반 row repair 시퀀스를 회로 단위로 추적한다.

## Prerequisites

- Ch01~Ch11 (시스템 DV 관점 전체)
- 트랜지스터 동작 기초 (NMOS/PMOS, threshold, leakage)
- SystemVerilog + Verilog AMS 기초
- SDC (Synopsys Design Constraints) 기초

---

## 1. DRAM 설계검증의 3축 — Logic / Timing / Quality

> SK Hynix 설계검증 직무 JD 인용: "Computing, Mobile, Graphics, HBM 등 전 제품 군을 아우르며, **Logic/Timing/Quality 검증을 위한 고유 기술 개발**을 주도하고 있습니다."

### 1.1 3축의 의미

| 축 | 무엇을 검증 | 주된 도구 |
|---|---|---|
| **Logic** | 명령 시퀀스, MR, refresh, training, ECC, PPR 등 *프로토콜* | System Verilog + UVM-lite, *In-house verification framework* |
| **Timing** | Setup/hold, 회로 path delay, clock skew, DQS 정렬 | **STA (PrimeTime), Hspice/PrimeSim** |
| **Quality** | Sign-off (LVS/DRC/EM/IR), retention, refresh efficiency, repair yield | LVS/DRC, IR-drop, Reliability sim |

→ **Logic** 축이 Ch01~Ch11 의 내용과 정확히 매칭. **Timing**과 **Quality**가 Ch12에서 보강하는 영역.

### 1.2 시스템 DV ↔ Vendor DV 매핑

| Spec 항목 | 시스템 DV (Ch01~11) | Vendor DV (이번 챕터) |
|---|---|---|
| WR/RD command | UVM driver → controller → DRAM model | DRAM 내부 *pipeline + sense amp + write driver* 회로 검증 |
| MRS | RAL `ral.MR0.write()` | MR latch *circuit*, MR access path *delay* |
| Refresh | tREFI 발급, RFM 명령 | *Refresh counter circuit*, row sequencer FSM, *internal tRFC budget* |
| Antifuse (PPR) | Guard key sequence + tPGM 대기 | **e-fuse blow circuit**, redundancy mux, fail bit map scan |
| Training | MR3 WL offset write | **DQS path delay tuning** (Hspice mixed-sim), CTLE 회로 |
| ECC (Transparency) | Force bit flip + MR20 read | **ECC encoder/decoder circuit**, parity tree, redundant DQ |
| Timing (tRCD/tRP/tFAW) | SVA 위반 catch | **STA sign-off** of internal row path, FAW current limit |

→ *같은 spec*을 vendor는 *회로/timing 단위*에서, 시스템은 *transaction 단위*에서 검증.

---

## 2. DRAM 내부 Custom 회로 — 검증 관점

### 2.1 핵심 Core IP

> SK Hynix Physical Design JD 인용: "주요 업무는 DRAM **Sense Amp, SWE, X-DEC/Y-DEC** 등 핵심 Core IP 개발을 포함하여..."

| Block | 약자 | 역할 | 검증 포인트 |
|---|---|---|---|
| **Sense Amplifier** | SA | bit-line의 미세 charge 차이를 logic level로 증폭 | sensing margin, restore time, mismatch |
| **Sub-Word-line Driver** | SWE / SWD | row decoder 출력을 *Word-line voltage* (VPP) 로 boosting | timing skew across row, leakage |
| **X-Decoder** | X-DEC | row address → word-line activation | propagation delay, decoder error |
| **Y-Decoder** | Y-DEC | column address → column select | propagation delay, column mux fault |
| **Row Buffer** | RB | sense amp output을 임시 보관 | data retention until PRE |
| **Column Mux** | YMUX | 활성 row의 column 중 선택 | path delay, leakage |
| **Write Driver** | WD | DQ data → bit-line force | drive strength, simultaneous switching |
| **DQ I/O** | — | external DQ pin과 internal data path 연결 | preamble/postamble, ODT 영향 |
| **Refresh Counter** | RC | refresh row sequencer | counter overflow, refresh efficiency |
| **Antifuse Block** | AF | row repair용 fuse 영역 | fusing voltage/time, redundancy mapping |

### 2.2 Sense Amp 동작 — 검증 challenge

DRAM cell의 charge는 *수십 fF capacitor*에 저장 (~10~20 mV swing). Sense amp는 이를 *full rail (1.1V)*로 증폭:

```
Word-line ▲ 활성화
                │
cell C_S = ~25 fF (typical)
                │
bit-line (BL)   ──────┬──── BLB (bit-line bar, reference)
                      │
                  Sense Amp
                      │
                  ▼  ▼
              latch output (D / DB)
```

**시간 흐름**:
1. **Precharge phase** (PRE state): BL=BLB=VBLP (~VDD/2)
2. **Activate phase** (ACT cmd): word-line → HIGH → cell capacitor가 BL과 sharing → ΔV ≈ ±10mV 발생
3. **Sensing phase** (sense amp enable): 정/부귀환 latch가 ΔV를 *full rail*로 증폭
4. **Restore phase**: cell capacitor에 *원래 charge* 복원 (destructive read 보상)
5. **Precharge phase**: BL/BLB를 다시 VBLP로

**검증 challenge**:
- **Sensing margin**: process corner (SS, TT, FF), voltage (0.95V~1.21V), temperature (-40°C~95°C) 모두에서 *ΔV 충분*한가
- **Restore time**: tRAS 이상 active 유지 시 *charge 완전 복원*되는가
- **Mismatch**: BL/BLB 간 capacitance/resistance mismatch가 sensing fail 유발 가능
- **Coupling**: 인접 BL의 switching이 *target BL noise*로 (Rowhammer 회로 측 근원)

### 2.3 SWE 회로 — VPP boosting

Word-line은 VDD가 아닌 *VPP* (DDR5 기준 1.8V) 로 driven. NMOS access TR의 *full-on*을 보장하기 위함.

- Charge pump가 VPP 생성 (Ch에 별도 챕터 가능)
- SWE는 row 선택 시 VPP로 word-line 구동
- *Leakage at off-state*가 retention 영향

**검증**: VPP droop simulation, SWE의 *delay across row* (가까운 cell vs 먼 cell), leakage 측정.

---

## 3. Analog & Digital Mixed Simulation

> JD 요구 역량 인용: "**Analog & Digital Mixed Simulation 및 설계 검증**"
> 도구: Hspice, PrimeSim, Spectre, Csim

### 3.1 왜 Mixed-Signal 인가

DRAM은 *digital 신호로 명령 받지만 cell 동작은 analog* (charge sharing). 검증에는 두 추상화가 *동시에* 필요:

| 영역 | 시뮬레이션 종류 |
|---|---|
| Command decoder, MR latch, FSM | **Digital** (Verilog/SystemVerilog) — RTL simulator |
| Sense Amp, BL/WL, Write Driver | **Analog** (Hspice) — transistor netlist |
| 통합 (controller→cmd→cell access) | **Mixed-Signal Co-simulation** |

### 3.2 Tool 체인

| Tool | 용도 | 시뮬레이션 종류 |
|---|---|---|
| **Hspice** | Pure analog transistor sim, golden reference | SPICE (slow, accurate) |
| **PrimeSim** (Synopsys) | Fast SPICE — 전체 chip block 가능 | FastSPICE |
| **Spectre** (Cadence) | Cadence flow의 SPICE | SPICE |
| **PrimeSim HSPICE** | high-accuracy mode | SPICE |
| **Csim** | SK Hynix 또는 vendor in-house SPICE-like tool *(추론)* | Custom |
| **Verilog-AMS / SystemVerilog Real Number Modeling (RNM)** | Mixed-Signal bridge | digital + analog interconnect |

### 3.3 Real Number Modeling (RNM) 패턴

RNM = analog 신호를 *digital simulator에서 real number*로 표현. SPICE보다 *훨씬 빠른* mixed-sim 가능.

```systemverilog
// RNM 예시 — Sense Amp을 *behavioral analog model*로
module sense_amp_rnm (
    input  real bl,         // bit-line voltage (analog)
    input  real blb,        // bit-line bar
    input        sa_en,     // sense amp enable (digital)
    output real d_out,
    output real db_out
);
    real vdd = 1.1;
    real vss = 0.0;

    always @(sa_en) begin
        if (sa_en) begin
            // 정/부귀환 latch 동작 — full rail로 증폭
            if (bl > blb) begin
                d_out  = vdd;
                db_out = vss;
            end else begin
                d_out  = vss;
                db_out = vdd;
            end
        end else begin
            // Precharge
            d_out  = vdd / 2.0;
            db_out = vdd / 2.0;
        end
    end
endmodule
```

→ SPICE 보다 *1000배 빠른* 시뮬레이션. *digital cmd → analog cell → digital output* full flow를 *RNM bridge*로 verify.

### 3.4 Corner Simulation

DRAM은 *전 공정 corner / 전 전압 / 전 온도*에서 spec 만족해야 함:

| Corner | 의미 |
|---|---|
| **PVT** | Process × Voltage × Temperature |
| **Process**: SS (Slow-Slow), TT (Typical), FF (Fast-Fast), SF, FS | 트랜지스터 변이 |
| **Voltage**: VDD min/typ/max | 1.045V ~ 1.155V (DDR5의 ±5%) |
| **Temperature**: -40°C ~ 105°C | 자동차/extended grade |

총 corner 수 = 5 (process) × 3 (voltage) × 3 (temperature) = **45 corners**.

→ DV는 *각 corner마다* sense amp sensing margin, write driver strength, refresh retention 모두 검증.

```
# Hspice 예: 45 corner sweep
.OPTION POST
.PARAM voltage_corner = {1.045, 1.1, 1.155}
.PARAM proc_corner = "SS,TT,FF,SF,FS"
.PARAM temp_corner = {-40, 25, 105}

.STEP PARAM voltage_corner
.STEP PARAM temp_corner
.LIB 'corner.lib' proc_corner

* ... DRAM block instance ...
* ... ACT/RD stimulus ...

.MEASURE TRAN sense_margin
+   FIND v(bl) - v(blb)
+   AT='time_at_sense_enable'
```

### 3.5 검증 시나리오 — 시스템 cmd ↔ 회로 응답

**예: WR command → cell write 시퀀스**

```
[Digital RTL]  controller → WR cmd on CA[13:0]
       │
       ▼
[Digital] command decoder → BL/WL control signal
       │
       ▼   (RNM bridge)
[Analog Hspice] write driver → BL force HIGH/LOW
       │
       ▼
[Analog] cell access transistor → cap charge update
       │
       ▼
[Analog→Digital] sense amp restore → cell stable
```

각 단계마다 *spec timing 안에 있는지* + *signal level이 spec 안인지* 검증.

---

## 4. Static Timing Analysis (STA)

> JD 요구: "**Static Timing Analysis 검증**"
> Tool: PrimeTime (Synopsys), Tempus (Cadence)

### 4.1 STA 본질

**Dynamic simulation은 vector 의존**. STA는 *모든 path를 정적으로* 분석 — *vector 없이* setup/hold 모두 cover.

```
Flip-Flop A ─── combinational logic ─── Flip-Flop B
   ↑                                          ↑
   CLK (source)                          CLK (capture)

Setup: data가 next CLK edge 이전에 도착해야 함
        T_clk - T_clk_skew ≥ T_FF_clk_to_Q + T_logic + T_setup

Hold: data가 *현재* CLK edge 이후 충분히 유지되어야 함
        T_FF_clk_to_Q + T_logic ≥ T_hold + T_clk_skew
```

### 4.2 DRAM-specific STA challenges

| Challenge | 설명 |
|---|---|
| **Distributed clock** | DRAM은 *fly-by* 또는 *tree*로 CK 분배 — 각 cell array마다 skew |
| **DQS recovery** | DQS는 *non-continuous* — preamble pattern으로 sample timing 재구축 |
| **Multi-cycle path** | 2-cycle command, MRR burst path는 *multi-cycle constraint* 적용 |
| **CDC (Clock Domain Crossing)** | CK (command) vs WCK (data, LPDDR5) vs internal core clock |
| **VPP boosted path** | word-line driver는 *VDD가 아닌 VPP* — 별도 timing arc |

### 4.3 SDC Constraint 예시 (DRAM-specific)

```tcl
# DRAM internal STA용 SDC
# 출처 인용: 본 자료는 학습용 — 실제 vendor SDC는 별도

# === Primary Clocks ===
create_clock -name CK_t  -period 0.3125 [get_ports CK_t]   ;# DDR5-6400, 3.2 GHz
create_clock -name CK_c  -period 0.3125 [get_ports CK_c] -waveform {0.156 0.3125}
# DQS는 source-synchronous, virtual clock으로 modeling
create_clock -name DQS_t -period 0.3125 -waveform {0 0.156}

# === Clock Uncertainty ===
set_clock_uncertainty -setup 0.020 [get_clocks CK_t]
set_clock_uncertainty -hold  0.010 [get_clocks CK_t]

# === Multi-cycle Path (2-cycle command) ===
set_multicycle_path 2 -setup -from [get_ports CA*] -to [get_pins cmd_decoder/*]
set_multicycle_path 1 -hold  -from [get_ports CA*] -to [get_pins cmd_decoder/*]

# === Input/Output Delay ===
set_input_delay  -clock CK_t -max 0.080 [get_ports CA*]
set_input_delay  -clock CK_t -min 0.010 [get_ports CA*]
set_output_delay -clock DQS_t -max 0.060 [get_ports DQ*]
set_output_delay -clock DQS_t -min 0.020 [get_ports DQ*]

# === False Paths ===
set_false_path -from [get_ports RESET_n]    ;# async reset
set_false_path -from [get_ports TEN]         ;# test mode pin

# === CDC ===
set_false_path -from [get_clocks core_clk] -to [get_clocks io_clk]
# 또는 명시적 synchronizer 사용:
# set_max_delay -from [get_clocks core_clk] -to [get_clocks io_clk] 0.6
```

### 4.4 Sign-off Corners

| Corner | Process | Voltage | Temp | Purpose |
|---|---|---|---|---|
| Setup worst | SS | min | max | 가장 slow — setup 어려움 |
| Hold worst | FF | max | min | 가장 fast — hold 어려움 |
| Cross-corner | SF | typ | typ | NMOS slow + PMOS fast |
| Cross-corner | FS | typ | typ | NMOS fast + PMOS slow |

→ 4가지 corner *모두* STA 통과해야 sign-off.

### 4.5 DRAM 특화 STA 시나리오

**ACT → RD path STA**:
```
CA[13:0] (CK posedge sampled)
       │
       ▼
Command Decoder (Logic delay)
       │
       ▼
Row Decoder (X-DEC)
       │
       ▼
Word-line Driver (SWE, VPP boosted)
       │
       ▼
Cell access → Sense Amp activation
       │
       ▼
Column Decoder (Y-DEC)
       │
       ▼
Data path → DQ driver
       │
       ▼
DQ output (DQS aligned)
```

이 전체 path가 *CL nCK* 이내에 완료되어야 함 (DDR5-6400 기준 CL=46 → 14.375ns).

STA가 *각 stage delay sum*이 *CL × tCK* 이하인지 정적 분석. corner마다 별도.

---

## 5. Antifuse / Redundancy / PPR — Vendor 회로 측 시각

### 5.1 Antifuse 동작 — circuit view

**Antifuse**: 평소 *open* (고저항), *blow* 시 *short* (저저항)으로 변하는 구조. e-Fuse / Laser Fuse / OTP 등 종류.

```
Normal (un-blown):
    BL ───╫─── (broken, R = G-ohm)
        antifuse

Blown:
    BL ─────── (connected, R < 1k-ohm)
        antifuse
```

DRAM에서 antifuse는 *redundancy mapping*에 사용:
- 각 sub-array마다 *spare row* (redundancy row) 존재
- Fail row 발견 시 *antifuse를 blow*하여 *fail row address → spare row* redirect

### 5.2 PPR Sequence — circuit-level dry-run

> 시스템 측 view (Ch09): MR23 hPPR=1 + WRA 발급 + tPGM 대기

> Vendor circuit view (이 챕터):
> 1. PPR mode enter → DRAM 내부 *high-voltage generator* enable (VPGM ~7~9V)
> 2. Address latch → fail row 주소를 *fuse decoder*에 입력
> 3. Pulse generation → VPGM을 *antifuse gate*에 N us 동안 인가
> 4. Verify → fuse blow 성공 확인 (저항 측정)
> 5. Redundancy mux 활성화 → fail row 접근 시 *spare row*로 redirect
> 6. PPR mode exit → VPGM disable

**검증 challenge**:
- VPGM 정확도 (over-voltage → 인접 fuse 손상)
- Pulse 시간 (too short → fail, too long → spare row 손상)
- Redundancy mux의 propagation delay
- Spare row의 *동일 sensing margin* 보장

### 5.3 Antifuse Block 검증 — Mixed-Signal

```systemverilog
// RNM model of antifuse repair sequence
module antifuse_block_rnm (
    input         ppr_enter,
    input  [16:0] fail_row,
    input         vpgm_enable,
    input  real   vpgm,        // analog VPGM voltage
    output        repair_ok,
    output [16:0] redirect_row // spare row address
);
    real fuse_resistance;
    parameter real VPGM_TYP = 7.5;
    parameter real VPGM_MIN = 7.0;
    parameter real VPGM_MAX = 9.0;
    parameter time TPGM_NS = 1000;  // 1 us typical

    initial fuse_resistance = 1.0e9;   // un-blown = 1G ohm

    always @(posedge vpgm_enable) begin
        if (vpgm >= VPGM_MIN && vpgm <= VPGM_MAX) begin
            #(TPGM_NS);
            fuse_resistance = 500.0;    // blown = 500 ohm
            // log antifuse blow event
            $display("[ANTIFUSE] Row 0x%x blown at t=%t, R=%.1f",
                     fail_row, $time, fuse_resistance);
        end else begin
            $display("[ANTIFUSE_FAIL] VPGM=%.2f out of range [%.1f, %.1f]",
                     vpgm, VPGM_MIN, VPGM_MAX);
        end
    end

    assign repair_ok = (fuse_resistance < 1000.0);
    assign redirect_row = repair_ok ? SPARE_ROW_BASE : fail_row;
endmodule
```

→ vendor 측 검증은 *fuse blow event*를 *시간 단위*로 모델링 + VPGM corner sweep.

---

## 6. DFT / BIST / Test Pattern

### 6.1 MBIST (Memory BIST)

DRAM 내부에 *self-test 로직* 내장. wafer-level 또는 시스템에서 *test pattern 자동 생성 + verify*.

> DDR5 MR23 OP[4]: **MBIST Enable** (SR/W) — "DRAM will automatically write to 0 when MBIST completes."

**MBIST 패턴 종류**:
- **March C-**: row/column 별 sequential write/read 패턴
- **Checker board**: 인접 cell 간 coupling test
- **Walking 1/0**: address line stuck-at fault detect
- **Refresh pattern**: retention test (long pause + read)

### 6.2 Scan Chain / ATPG

DRAM의 *peripheral 회로* (decoder, latch, FSM) 는 *scan chain* 적용. 외부 ATE에서 *test vector*를 scan in → scan out 으로 fault coverage 측정.

→ vendor DV는 *scan coverage 95%+* sign-off.

### 6.3 mPPR / Hard Repair via MBIST

> DDR5 MR23 OP[3] (mPPR): MBIST를 *trigger*하여 *fail row를 자동 발견 + 자동 hPPR 실행* (optional 기능).

검증:
- MBIST가 *모든 fail row*를 찾는가
- mPPR이 *spare row 부족 시* graceful fail (ALERT_n)
- Repair 후 *MBIST 재실행* 시 fail 없음 확인

---

## 7. Sign-off 체계 — LVS / DRC / EM / IR

### 7.1 Sign-off 체크리스트 (vendor 측)

| Sign-off | 의미 | 도구 |
|---|---|---|
| **LVS** (Layout vs Schematic) | layout이 schematic과 일치 | Calibre LVS, IC Validator |
| **DRC** (Design Rule Check) | layout 규칙 (간격, 폭) 준수 | Calibre DRC |
| **ERC** (Electrical Rule Check) | floating gate, short-to-VDD 등 | Calibre ERC |
| **PERC** (Programmable ERC) | HV gate breakdown 등 안전 | Calibre PERC |
| **EM** (Electromigration) | metal wire current density | RedHawk, Voltus |
| **IR-Drop** | power network voltage drop | RedHawk, Voltus |
| **STA** | timing (위 §4) | PrimeTime |
| **PV** (Physical Verification) | DRC + LVS + ERC + DFM | Calibre |
| **Reliability** | aging, HCI, NBTI | MOSRA, RelXpert |

### 7.2 EDA Tool 체인 — 일반적

```
Schematic (Virtuoso) ─────────────┐
                                   │
                                   ▼
              LVS  ←──────  Layout (Virtuoso XL)
                                   │
                                   ▼
                                  DRC
                                   │
                                   ▼
              Extract (StarRC) → RC netlist
                                   │
                                   ▼
              PrimeSim / Spectre → Post-layout sim
                                   │
                                   ▼
              PrimeTime → STA sign-off
                                   │
                                   ▼
              RedHawk → EM/IR sign-off
                                   │
                                   ▼
                              Tape-out
```

---

## 8. 시스템 DV ↔ Vendor DV 통합 시각

### 8.1 같은 spec, 다른 추상화

| Spec 항목 | 시스템 DV view | Vendor DV view |
|---|---|---|
| tRCD | controller 가 ACT 후 tRCD nCK 이상 대기 (SVA) | ACT cmd가 *internal SA enable*까지 *<tRCD - margin* (STA) |
| MR0 CL=26 | RAL `ral.MR0.cl.set(6'd26)` | CL register *latch circuit* + *programmable delay line* (mixed-sig) |
| Refresh | controller가 tREFI마다 REF 발급 | DRAM 내부 *refresh counter*가 row sequencer 구동 + *VPP/VBLP 안정* |
| PPR | guard key sequence + tPGM 대기 | **VPGM pulse generation + antifuse blow + redundancy mux re-route** |
| ECC | scoreboard data 비교 + MR20 read | **ECC encoder/decoder parity tree circuit + redundant DQ pipeline** |
| Training | MR3 WL offset tuning | **DQS delay line tap programming (analog)** + RNM bridge |
| ALERT_n | CRC mismatch 시 LOW | **Open-drain output driver + pull-up sequence** |
| ZQ Calibration | ZQCL 명령 발급 | **240 Ω external R vs internal R matching circuit** + comparator |

### 8.2 어디서 만나는가 — *Interface 명세*

두 추상화가 만나는 지점은 *DRAM pin interface*. 이 경계는:
- 시스템 측: 핀 신호의 *transaction protocol*
- 벤더 측: 핀 신호의 *electrical compliance* (Vih/Vil, Tsetup/Thold, jitter)

→ **양 측 모두**가 spec의 *동일한 timing/voltage 표*를 reference. 그러나 *check하는 방식*이 다름.

### 8.3 같이 봐야 할 Corner Cases

- **High-speed corner** (DDR5-8400): preamble 4tCK, DFE on, Vref 정밀 — 시스템은 *training fail injection*, 벤더는 *DFE 회로 simulation*
- **Extended temperature** (95~105°C): 시스템은 *MR4 tREFI/2 자동 전환*, 벤더는 *retention curve* 측정
- **3DS stacking**: 시스템은 *CID3:0 addressing*, 벤더는 *TSV signal integrity + thermal*
- **Power-down resume**: 시스템은 *tXP, CKE timing*, 벤더는 *internal charge pump restart*

---

## 9. 대표 문제 — Sense Amp Read dry-run + STA check

!!! question "Q. DDR5-6400 (tCK=0.3125ns), tRCD=28 nCK, CL=46 nCK. ACT(row=0x100, BL_A) 발급 후 RD 동작을 *회로 측 + 시스템 측* 시각으로 끝까지 추적하라. STA setup 위반 가능성도 점검."

???+ answer "풀이 (Mixed-Signal + STA)"

    **시스템 측 (Ch05~06 view)**
    
    ```
    Cycle 0~1: ACT 2-cycle (CA[13:0] = BL_A, ROW=0x100)
    Cycle 2~28: NOP/DES — tRCD 대기
    Cycle 29~30: RD 2-cycle (col=0x40, AP=0)
    Cycle 30+CL = 76: 첫 DQ beat valid (BL16)
    ```

    **벤더 측 (Ch12 view) — 같은 시퀀스의 *내부 동작***

    | 시간 (ns) | Cycle | 내부 동작 |
    |---|---|---|
    | 0.0 | 0 | CK_t rising → CA latch → cmd decoder start |
    | 0.3 | 1 | Decoder output → X-DEC start |
    | 0.5 | 1.5 | X-DEC → SWE drive enable |
    | 1.0 | 3.2 | SWE → word-line VPP boost begin |
    | 1.5 | 4.8 | Word-line HIGH → cell access TR on |
    | 2.0 | 6.4 | Cell charge → BL voltage ΔV (~10mV) |
    | 2.5 | 8.0 | Sense Amp enable → latch begin |
    | 3.5 | 11.2 | SA full-rail (D=VDD, DB=VSS) |
    | 4.0 | 12.8 | Row buffer ready (= **tRCD 만료** spec 8.75ns 보다 *빠름* — margin OK) |
    | 9.0 | 28.8 | RD cmd 발급 가능 (사용자가 이 시점에 RD) |
    | 9.4 | 30 | Y-DEC start |
    | 10.5 | 33.6 | Column mux select |
    | 13.0 | 41.6 | Data path → DQ pad pre-driver |
    | 14.4 | 46.0 | DQ pad drive on, preamble pattern emit |
    | 23.4 | 75 | First valid DQ beat = *CL 만료 시점* |

    **STA check**:
    - Stage 1 (CK → cmd decoder): ~0.3ns (typical) → CL=46 nCK이 SS corner에서도 setup margin 확보
    - Stage 2 (X-DEC + SWE): ~1.5ns → corner *(SS, min V, hot temp)*에서 가장 늦음. *spec tRCD-1ns* 마진 권장
    - Stage 3 (SA → restore): ~2.0ns. *cell capacitance variation* 의존
    - Stage 4 (Y-DEC + path): ~5.0ns 
    - Stage 5 (DQ drive): ~1.5ns

    Total ACT→Data path: ~10ns (typical). Spec: tRCD + CL = 8.75 + 14.375 = 23.125 ns. *margin OK*.

    **위반 가능 시나리오**:
    - *SS corner + 105°C* 에서 SWE delay가 1.5ns → 2.5ns 증가 → tRCD 위반 직전
    - VPP droop (~50mV) 시 word-line boost 부족 → cell access TR이 *완전히 안 켜짐* → BL ΔV 부족 → SA fail
    - Sense amp mismatch (BL/BLB 비대칭) > 5mV → wrong polarity latch

    **검증 보완**:
    - **Mixed-Sig sim** (Hspice/PrimeSim): 45 corner sweep으로 위 시나리오 모두 cover
    - **STA**: PrimeTime로 *모든 setup/hold path* 정적 분석. SDC에 multi-cycle constraint 명시.
    - **In-house tool**: SK Hynix JD 인용 "EDA Tool 뿐만 아니라 In-house Tool 개발 경험" — vendor-specific timing margin analysis tool

---

## 10. 시스템 DV 엔지니어가 Vendor DV로 이직 시 학습 우선순위

> SK Hynix DRAM 설계검증 JD 기반 우선순위

| 우선순위 | 학습 항목 | 시간 예상 |
|---|---|---|
| 1 | **Hspice/PrimeSim 기본** — SPICE syntax, transient sim, .MEASURE | 1~2주 |
| 2 | **STA (PrimeTime)** — SDC 작성, setup/hold check, corner sign-off | 2~3주 |
| 3 | **Verilog-AMS / RNM** — mixed-signal bridge | 1주 |
| 4 | **DRAM 내부 회로** — Sense Amp, SWE, X-DEC/Y-DEC, charge pump | 2~3주 |
| 5 | **DFT / MBIST / ATPG 기초** | 1주 |
| 6 | **LVS/DRC/EM-IR sign-off** | 1주 |
| 7 | **Python/Tcl 자동화** — EDA tool driving | 지속 학습 |
| 8 | **DRAM 공정/소자** — leakage, retention, aging | 지속 학습 |

→ Ch01~Ch11 (시스템 DV 관점) + Ch12 (vendor 관점) + 위 8개 학습 항목 = **양쪽 다 이해하는 sweet-spot DV 엔지니어**.

---

## 11. 핵심 정리 (Key Takeaways)

- DRAM 설계검증은 **Logic / Timing / Quality 3축** — Ch01~Ch11이 Logic, Ch12가 Timing + Quality.
- **시스템 DV (controller)** 와 **vendor DV (DRAM die)** 는 *같은 spec, 다른 추상화*. 검증 대상·도구가 다름.
- Vendor 측 핵심 도구: **Hspice / PrimeSim / Spectre** (Mixed-Signal) + **PrimeTime** (STA) + **RNM** (bridge).
- **Sense Amp**: 10~20mV charge → full rail 증폭. corner마다 sensing margin 검증.
- **SWE / VPP**: word-line은 VDD가 아닌 *VPP boosted*. droop simulation 필수.
- **Antifuse**: PPR의 *circuit-level* — VPGM pulse 정확도가 repair yield 결정.
- **STA**: 모든 internal path 정적 setup/hold check + 45 corner sign-off.
- **MBIST**: DRAM 내부 self-test — March C-, Checker board, Walking 1/0 등 패턴.
- **Sign-off**: LVS / DRC / ERC / EM / IR / STA / PV / Reliability — 모두 통과해야 tape-out.
- **Mixed-Sig + RNM** 으로 *DRAM 전체 chip*을 reasonable 시간에 시뮬레이션.
- 시스템 DV 엔지니어가 vendor DV로 이직 시 학습 우선순위: Hspice → STA → RNM → 회로 → DFT → Sign-off → 자동화.

## 12. Further Reading

- 이전: [Ch11. DV 프로젝트 End-to-End](11_dv_project_endtoend.md)
- 부록 A: [JEDEC Spec 빠른 참조](appendix_a_quick_reference.md)
- 부록 B: [Glossary](appendix_b_glossary.md)
- 외부 자료:
    - "DRAM Circuit Design" — Brent Keeth, R. Jacob Baker (회로 측 정수)
    - Synopsys PrimeTime User Guide — STA 표준
    - "CMOS VLSI Design" — Weste & Harris (digital + STA 기초)
    - Cadence Spectre Documentation
    - SPICE syntax tutorial (Hspice / PrimeSim manual)

<div class="chapter-nav">
  <a class="nav-prev" href="../11_dv_project_endtoend/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch11. DV 프로젝트 End-to-End</div>
  </a>
  <a class="nav-next" href="../appendix_a_quick_reference/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">부록 A. Quick Reference</div>
  </a>
</div>
