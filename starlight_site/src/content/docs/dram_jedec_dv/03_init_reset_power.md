---
title: "Ch03. 초기화·Reset·Power 시퀀스"
---

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">CH 03</span>
</div>

## 🎯 Learning Objectives

- **Describe**: DDR5의 power-up initialization 시퀀스 단계를 시간 순서대로 서술한다.
- **Compare**: DDR4 / DDR5 / LPDDR4 / LPDDR5의 power-up sequence 핵심 차이를 비교한다.
- **Apply**: Power-up 시퀀스를 UVM run_phase의 sub-phase로 매핑하여 testbench 시퀀스를 설계한다.
- **Analyze**: Reset/Power-down 시 잘못된 명령이 들어왔을 때 발생할 수 있는 결과를 분석한다.

## Prerequisites

- [Ch02. 패키지·핀아웃·어드레싱](../02_package_pinout_addressing/)
- UVM phase 기본 (build → connect → run → extract → report)

## 1. 왜 초기화가 DV의 첫 단계인가

DRAM은 RTL reset 신호 하나만 low에서 high로 올린다고 동작하는 부품이 아닙니다. 내부의 **DLL**(delay-locked loop, 내부 클럭을 외부 CK에 정확히 정렬시켜 데이터 타이밍을 맞추는 회로), **ZQ calibration**(외부 기준 저항에 맞춰 출력 구동/종단 임피던스를 보정하는 절차) 회로, 각종 analog 경로가 올바른 조건을 갖추어야 비로소 ACT/RD/WR 명령을 수락합니다. 그 조건은 크게 다섯 단계를 순서대로 충족해야 합니다.

1. **Voltage rail이 올바른 순서로 ramp** (Vdd → Vddq → Vpp ...)
2. **RESET_n deasserted + CK 안정화**
3. **Mode Register 프로그래밍** (CL, BL, **Vref**(reference voltage, 입력 신호의 0/1을 가르는 기준 전압) 등)
4. **ZQ Calibration** (output impedance)
5. **Training** (CA/DQ/DQS — Ch08에서 상세)

이 순서를 틀리면 어떻게 될까요? 전압 rail이 잘못된 순서로 올라오면 device가 손상될 수 있고, **CKE**(clock enable, HIGH일 때만 DRAM이 클럭을 받아 명령을 처리하게 하는 제어 신호)가 너무 일찍 HIGH가 되면 DRAM 내부 상태가 미정의 상태가 됩니다. DV 환경에서 이 시퀀스를 잘못 짜면 DRAM 모델이 X를 내거나 조용히 잘못된 데이터를 반환하기도 합니다. 시뮬레이션이 통과하는데 실제 silicon에서 fail이 나는 대표적인 원인이 초기화 시퀀스 오류이므로, testbench의 init sequence는 스펙 §3.3의 Figure 4와 timing 파라미터를 정확히 반영해야 합니다.

---

## 2. DDR4 Power-up Initialization Sequence

> 출처: JESD79-4D §3.3.1

DDR4의 power-up 시퀀스는 전원이 인가된 순간부터 DRAM이 첫 번째 명령을 수락할 준비가 되기까지의 시간 흐름을 정의합니다. 각 단계 사이에 최소 대기 시간이 규정되어 있으며, 이를 어기면 내부 회로가 안정화되지 않은 상태에서 명령을 받게 됩니다.

```
Step  Time          Action
────────────────────────────────────────────────────────────
T0    0             Power applied (Vdd, Vddq, Vpp 동시 또는 Vpp가 먼저)
T1    Tpw_RESET 후  RESET_n LOW (≥200us 유지)
T2    Tpw_RESET 후  RESET_n HIGH
T3    +500us        CKE LOW로 유지 (RESET_n HIGH 이후)
T4    +tXPR         CKE HIGH 가능
T5    +tMRD         첫 MR Write 가능
        MR3 → MR6 → MR5 → MR4 → MR2 → MR1 → MR0
T6    +tDLLK        ZQCL (ZQ Calibration Long) 가능
T7    +tZQinit      Normal operation 가능
```

각 timing 파라미터의 물리적 의미를 이해하면 왜 이 대기가 필요한지 명확해집니다.
- `tXPR` (Exit Reset Period): RESET_n이 HIGH가 된 후 DRAM 내부 회로가 초기 상태로 진입하는 데 걸리는 시간입니다. 이 시간 동안 CKE는 LOW여야 합니다.
- `tDLLK` (DLL Locking Time): DLL이 CK에 lock되는 데 필요한 클럭 수입니다. DLL이 lock되어야 정확한 DQS 타이밍 보장이 가능합니다.
- `tZQinit` (ZQ initial calibration): 첫 ZQ calibration은 짧은 ZQCS와 달리 긴 ZQCL을 사용하며, 완료되어야 출력 드라이버 임피던스가 정확히 교정됩니다.

### 2.1 DDR4 MR programming 순서

JESD79-4D §3.3.1 가 명시하는 MR 프로그래밍 순서입니다. 표에 나오는 설정 항목 — **MPR**(multi-purpose register, 정해진 패턴이나 상태를 읽어내는 특수 레지스터), **CWL**(CAS write latency, write 명령부터 데이터를 실어 보내기까지의 클럭 지연), **AL**(additive latency, 명령 처리를 의도적으로 늦춰 버스 활용을 높이는 추가 지연), **RTT_WR**(write 시 적용되는 ODT 종단 저항값)입니다.

| 순서 | MR | 주요 설정 |
|---|---|---|
| 1 | MR3 | MPR (Multi-Purpose Register) 설정 |
| 2 | MR6 | Vref calibration |
| 3 | MR5 | CA Parity, ODT, CRC |
| 4 | MR4 | Refresh modes, Temperature, CAL |
| 5 | MR2 | RTT_WR, LP ASR, CWL |
| 6 | MR1 | DLL enable, Output drive, AL, ODT |
| 7 | MR0 | BL, CL, DLL reset, WR, DLL_off |

_왜 MR 프로그래밍에 순서가 정해져 있는가_ 는 일부 MR 설정이 다른 MR 설정의 _전제 조건_ 이기 때문입니다. Mode Register 들은 서로 독립적인 게 아니라 의존 관계를 가집니다 — 예를 들어 DLL 을 켜고 reset 하는 설정(MR1 의 DLL enable, MR0 의 DLL reset)은 DLL 의 동작을 결정하는데, DLL 은 다른 타이밍(특히 출력 타이밍)의 기준이 되므로 가장 나중에 확정되어야 앞선 설정들이 안정된 상태에서 lock 을 잡습니다. 마찬가지로 Vref training 관련 MR 은 ODT·드라이버 설정이 먼저 자리잡은 뒤라야 올바른 기준 전압을 잡을 수 있습니다. 즉 "A 의 결과 위에서 B 가 동작" 하는 선후 의존이 있어, 순서를 뒤집으면 뒤 설정이 아직 미확정인 앞 설정을 전제로 잘못 계산되어 silicon 에서 비정상 동작이 납니다. 그래서 JEDEC 이 안전한 단일 순서를 못박아 둔 것입니다.

:::tip[DV 적용 — MR 프로그래밍 순서 검증]
Scoreboard에서 controller가 MR을 *위 순서로* 프로그래밍하는지 검증. 순서를 어기면 spec violation이지만 시뮬레이션은 *통과*할 수 있음. directed test로 명시적 검증 필요.
:::
---

## 3. DDR5 Power-up Initialization Sequence

> 출처: JESD79-5C.01 v1.31 §3.3.1

DDR5는 DIMM에 PMIC가 내장되고 channel별 독립 초기화가 가능하다는 점이 DDR4와의 핵심 차이입니다. 이전까지는 마더보드가 전압 생성을 담당했지만, DDR5는 DIMM 위에 PMIC가 올라가서 12V 입력을 받아 1.1V(Vdd), 1.8V(Vpp) 등을 직접 생성합니다. 전원 제어의 책임이 시스템에서 DIMM으로 이동한 셈이므로, 초기화 시퀀스에서도 시스템(controller) 측이 PMIC 상태를 고려해야 합니다.

### 3.1 단계별 개요

```d2
direction: down

SYS: System Power
PMIC: on-DIMM PMIC
DRAM: DDR5 SDRAM
CTRL: Memory Controller

SYS -> PMIC: 12V supply 인가
PMIC -> DRAM: Vdd / Vddq / Vpp ramp (정해진 순서)
CTRL -> DRAM: RESET_n LOW → HIGH
CTRL -> DRAM: CKE LOW → HIGH after tXPR
CTRL -> DRAM: Initial MR Write (특정 MR 우선)
CTRL -> DRAM: ZQCL (ZQ Calibration Long)
CTRL -> DRAM: CA training, DQ training (Ch08)
```

### 3.2 DDR5 특유의 추가 단계

1. **CS Training** — DDR5의 CS 신호는 high-speed signaling이라 별도 training 필요. MR13의 `CS Geardown` 등 설정.
2. **PDA (Per-DRAM Addressability)** — DIMM 위 여러 DRAM device를 *개별적*으로 MR write. MR1[7] 설정 (§3.5.3).
3. **DCA / DFE 초기화** — high-speed signaling 보상. MR42~MR48 (DCA), MR111~MR116 (DFE).

### 3.3 핵심 timing 파라미터 (DDR5)

- `tXPR` — Exit reset from CKE
- `tINIT3` — RESET_n LOW 펄스 폭 ≥ 200us
- `tINIT4` — CKE LOW 유지 (RESET_n HIGH 이후)
- `tINIT5` — MR write 가능 시점
- `tZQCAL` — ZQ Calibration time

> 정밀 값은 speed bin에 따라 다릅니다 — JESD79-5C.01 의 timing table 참조.

---

## 4. LPDDR4 Power-up Sequence

> 출처: JESD209-4E §3.3

LPDDR4는 DDR4/DDR5와는 다른 전압 구조와 초기화 방식을 사용합니다. 서버 DRAM이 단일 core 전압으로 동작하는 것과 달리, LPDDR4는 core와 periphery를 위한 두 개의 전압 레일을 분리해서 저전력을 실현합니다.

```
Step  Action
─────────────────────────────────────────
T1    Power applied — Vdd1 → Vdd2 → Vddq (정해진 순서)
T2    Reset 활성화 (LPDDR4의 RESET_n)
T3    Reset deassert 후 일정 시간
T4    CKE LOW → HIGH
T5    MRW (Mode Register Write — mode register에 설정값을 쓰는 명령) — initial config
T6    ZQ Calibration
T7    CA / DQ Training (Ch08)
T8    Normal operation
```

### 4.1 LPDDR4의 voltage rail 특징

- **Vdd1**: high voltage (~1.8V) — core. DRAM 셀 어레이와 워드라인 드라이버에 공급됩니다.
- **Vdd2**: low voltage (~1.1V) — periphery. IO 회로와 일부 내부 로직에 공급됩니다.
- **Vddq**: I/O voltage — **LPDDR4 = 1.1V, LPDDR4X = 0.6V**. 외부 DQ 핀의 기준 전압입니다. (LPDDR5는 더 낮은 0.5V로 내려갑니다 — §5.1.)

이 세 전압은 Vdd1이 먼저 ramp되고 그 다음 Vdd2, 마지막으로 Vddq가 올라와야 합니다. 순서를 어기면 device 내부에 비정상적인 전위가 형성되어 damage가 발생할 수 있으므로, controller는 반드시 정해진 순서를 보장해야 합니다. DV에서는 power sequence 시뮬레이션으로 이 순서를 명시적으로 검증하는 것이 중요합니다.

---

## 5. LPDDR5 Power-up Sequence

> 출처: JESD209-5C §4.1

LPDDR5의 결정적 추가는 *Dual VDD2 rail*과 *DVFS sequence*입니다.

### 5.1 Voltage rail 변화

> 이 교재의 *주축은 LPDDR5* 입니다. 아래 전원 구조가 모바일/저전력 DRAM의 기준이며, DDR5(§3)는 서버/PC 비교축, LPDDR4(§4)는 직전 세대 비교축으로 봅니다.

- **VDD1**: 1.8V — high voltage rail.
- **VDD2H**: ≈1.05V — 고주파(고성능) 동작용 main periphery/core rail.
- **VDDQ**: **0.5V** — DQ I/O 기준 전압.
- (저주파 절전 시 VDD2 계열을 낮춰 쓰는 dual-rail 운용도 가능 — 세부 rail 분리는 device/구현 의존 *(추론)*.)

:::note[LPDDR5 전원의 정체성 — SoC-side PMIC (DDR5와 정반대)]
DDR5(§3)는 *DIMM 위에 PMIC*가 올라가 12V를 받아 1.1V/1.8V를 *모듈 내부에서* 생성합니다. **LPDDR5는 정반대**입니다.

- LPDDR5는 **PoP(Package-on-Package)** 으로 SoC 위에 적층되며, **on-package PMIC / DIMM / RCD가 없습니다**.
- 전압은 **SoC-side(외부) PMIC가 생성**해 DRAM에 공급합니다. DRAM은 VDD1(1.8V) / VDD2H(≈1.05V) / VDDQ(0.5V)를 *받기만* 합니다.
- 따라서 **DVFS(전압/주파수 전환)는 SoC가 주도**합니다 — DRAM이 스스로 rail을 만들지 않으므로, FSP 전환은 SoC PMIC가 rail을 조정하고 host가 MR/training을 재정렬하는 *시스템 측 시퀀스*입니다.

DV 시사점: LPDDR5 power-sequence 모델은 *외부 PMIC behavioral model* + *SoC-initiated DVFS 트리거*로 구성해야 하며, DDR5처럼 on-module PMIC 상태를 DRAM 초기화에 끼워 넣어서는 안 됩니다.
:::

### 5.2 Power-up 단계

```
T1    Power applied (정해진 순서: Vdd1 → Vdd2H/L → Vddq)
T2    Reset activate / deactivate
T3    CKE LOW → HIGH
T4    WCK ramp + WCK2CK Leveling (training)
T5    Initial MRW
T6    ZQ Calibration
T7    CA Training (CBT Mode1/Mode2)
T8    DQ Training (Ch08)
T9    Normal operation
```

:::note[LPDDR5 init training — CBT + WCK2CK (DDR5와 무엇이 다른가)]
LPDDR5 초기화의 training 단계는 DDR5와 *구성 자체가* 다릅니다.

- **LPDDR5**: **CBT (Command Bus Training, Mode1/Mode2)** + **WCK2CK Leveling** + DQ/Write/Read training. CA 버스가 CA[6:0] 단일종단 다중사이클이라 CBT가 *필수*이고, 데이터용 WCK가 명령용 CK와 별개 클럭이라 **WCK2CK Leveling**(LPDDR5 고유)으로 둘을 정렬해야 합니다. 4 스펙 중 training 단계가 가장 많습니다.
- **DDR5**: **CA / CS Training** 중심 (+ on-DIMM PMIC/RCD 고려). 단일 CK + DQS 구조라 WCK2CK 같은 단계가 없습니다.
- **DDR4**: Write Leveling 중심.

DV 시사점: LPDDR5 init vseq는 CBT phase(physical MR 접근)와 WCK2CK leveling phase를 *별도 sub-phase*로 모델링해야 하며, gear(DVFSC) 전환 시 WCK:CK 비가 바뀌므로 **WCK2CK 재정렬**이 다시 일어납니다(§5.3).
:::

### 5.3 LPDDR5 특유의 단계 — DVFS 진입

power-up 후 normal op에서 *Dynamic Voltage Frequency Scaling*으로 *Frequency Set Point (FSP)* 를 변경할 수 있음 (§7.6.3). 각 FSP는 *별도의 MR set*을 가짐. DV는 *FSP 전환 시퀀스*가 spec을 준수하는지 검증.

---

## 6. DV 적용 — UVM Phase 매핑

DRAM 초기화 시퀀스는 단계마다 선행 조건이 있는 엄격한 state machine입니다. UVM의 run-time phase는 이 구조와 자연스럽게 매핑됩니다. 전력 인가부터 normal operation까지의 각 단계를 해당 phase에 배치하면, phase 경계가 init 진행의 체크포인트 역할을 하게 됩니다.

### 6.1 권장 매핑

| UVM phase | 역할 |
|---|---|
| `build_phase` | TB 구조 build, config_db 설정 |
| `connect_phase` | TLM port 연결, virtual interface 할당 |
| `end_of_elaboration_phase` | 구조 print, sanity check |
| `start_of_simulation_phase` | initial value 설정 |
| `pre_reset_phase` (run-time) | Voltage rail ramp simulation |
| `reset_phase` | RESET_n LOW |
| `post_reset_phase` | RESET_n HIGH, CKE LOW 유지 |
| `pre_configure_phase` | tXPR 대기, CKE HIGH |
| `configure_phase` | **Initial MR Write 시퀀스** (DDR5: CS training → PDA → MR write) |
| `post_configure_phase` | ZQ Calibration, training 진입 |
| `pre_main_phase` | Training (Ch08) |
| `main_phase` | Normal traffic |
| `post_main_phase` | Cool-down |
| `pre_shutdown_phase` | Self-refresh entry (옵션) |
| `shutdown_phase` | Power-down |

### 6.2 Initial sequence skeleton (DDR5 가정)

```systemverilog
// 출처 인용 위치: JESD79-5C.01 §3.3 (power-up sequence)
class ddr5_init_vseq extends uvm_sequence;
    `uvm_object_utils(ddr5_init_vseq)

    rand int  init_wait_cycles;
    constraint c_wait { init_wait_cycles inside {[200_000 : 250_000]}; }
                                                // tINIT3 ≥ 200us

    virtual task body();
        // Phase 1: RESET pulse
        `uvm_info("INIT", "Asserting RESET_n LOW", UVM_MEDIUM)
        // ... assert RESET signal via interface ...
        #(init_wait_cycles);

        // Phase 2: RESET deassert
        `uvm_info("INIT", "Deasserting RESET_n", UVM_MEDIUM)
        // ... deassert RESET ...

        // Phase 3: CKE LOW → HIGH after tXPR
        `uvm_info("INIT", "Waiting tXPR, then CKE HIGH", UVM_MEDIUM)
        #(`TXPR_NS);

        // Phase 4: CS Training (DDR5-specific)
        do_cs_training();

        // Phase 5: Initial MR Write (specific MR first)
        do_initial_mr_write();

        // Phase 6: ZQ Calibration Long
        do_zqcl();
        #(`TZQINIT_NS);

        // Phase 7: Done
        `uvm_info("INIT", "Init sequence complete", UVM_MEDIUM)
    endtask

    extern task do_cs_training();
    extern task do_initial_mr_write();
    extern task do_zqcl();
endclass
```

### 6.3 Init 시퀀스용 SVA

```systemverilog
// RESET_n LOW 시간이 tINIT3 (200us) 이상이어야 함
// 출처: JESD79-5C.01 §3.3 (tINIT3 minimum)
property p_reset_min_pulse;
    @(posedge clk) disable iff (!power_good)
    $fell(reset_n) |-> ##[0:$] $rose(reset_n) &&
        ($time - $past($time, 1, $fell(reset_n))) >= 200_000_000;  // 200us in ps
endproperty

a_reset_min_pulse: assert property (p_reset_min_pulse)
    else `uvm_error("ASSERT", "RESET_n LOW pulse < tINIT3")
```

> 위 SVA는 **개념 예시**입니다. 실제 시뮬레이터에서 `$past($time, ...)` 사용 방식은 EDA마다 다르므로 vendor 매뉴얼 확인.

### 6.4 Init 시퀀스용 Coverage

```systemverilog
covergroup init_cg with function sample (
    bit cs_training_done,
    bit pda_done,
    bit zqcl_done,
    int reset_pulse_us
);
    cp_cs_training: coverpoint cs_training_done {
        bins done = {1};
        bins skipped = {0};
    }
    cp_pda: coverpoint pda_done {
        bins done = {1};
        bins skipped = {0};
    }
    cp_zqcl: coverpoint zqcl_done {
        bins done = {1};
        bins skipped = {0};
    }
    cp_reset_pulse: coverpoint reset_pulse_us {
        bins min_spec     = {[200:210]};
        bins normal       = {[211:500]};
        bins long_pulse   = {[501:1000]};
        bins very_long    = {[1001:$]};
    }
endgroup
```

---

## 7. 비교 정리 — 4 스펙 power-up sequence

| 단계 | DDR4 | DDR5 | LPDDR4 | LPDDR5 |
|---|---|---|---|---|
| Voltage rails | Vdd 1.2V, Vddq, Vpp | Vdd 1.1V, Vpp 1.8V (PMIC **on DIMM**) | Vdd1 1.8V, Vdd2 ~1.1V, Vddq (4:1.1V / 4X:0.6V) | VDD1 1.8V, **VDD2H ≈1.05V**, VDDQ **0.5V** |
| PMIC 위치 | 마더보드 | **on-DIMM PMIC** | SoC-side(외부) | **SoC-side(외부), on-package PMIC 없음** |
| Reset 방식 | RESET_n (async) | RESET_n (async) | RESET_n | RESET_n |
| Initial CKE 시점 | tXPR 후 | tXPR 후 | reset deassert 후 | reset deassert 후 |
| CS Training | — | **CS training 필요** | — | — |
| PDA | (제한적) | **MR1[7]** | — | — |
| Clock 분리 | — | per channel | — | **WCK separate** |
| WCK2CK Leveling | — | — | — | **있음** |
| ZQ Calibration | ZQCL | ZQCL | ZQCal | ZQCal |
| Bank mode 선택 | — | — | — | **있음 (16/8/BG)** |

---

## 8. 대표 문제 — DDR5 init 시퀀스 dry-run + UVM phase 매핑

:::tip[Q. 다음 가상 DDR5 시뮬레이션에서 RESET → MR Write → ZQCL → Ready 까지 시퀀스를 UVM phase 단위로 정리하라. tINIT3=200us, tXPR=410ns, tZQinit=1024 nCK, tCK=0.5ns 가정. 잘못된 시점에 MR Write가 들어가면 어떻게 되는지도 분석.]
:::
<details>
<summary>풀이 (UVM phase trace + 위반 분석)</summary>


**Step 1 — 시간/phase 매핑**

| 시간 | UVM phase | Action | 이유 |
|---|---|---|---|
| t=0 | build/connect | TB build, vif 연결 | structural |
| t=0+ | start_of_simulation | initial value | const init |
| t=10ns | pre_reset | power_good=1 | rail ramp 완료 가정 |
| t=10ns | reset | RESET_n=0 | LOW assert |
| t=10ns + 200us = 200.01us | post_reset | RESET_n=1 | LOW 유지 200us |
| t=200.01us + 410ns ≈ 200.42us | pre_configure | CKE=1 | tXPR 후 |
| t=200.42us+ | configure | MR Write 시퀀스 | CS training + PDA + MR |
| t=~201us | post_configure | ZQCL 명령 발급 | normal |
| t=~201us + 512ns | pre_main | training (Ch08) | tZQinit 후 (1024 × 0.5ns = 512ns) |
| t=~202us | main | normal traffic 시작 | 모든 init 완료 |

**Step 2 — 위반 시나리오 분석**

가정: configure phase가 *시작도 전에* (CKE=0 상태에서) MR Write를 발급했다면?

- DRAM은 CKE=0 동안 *명령을 수락하지 않음* (Self-Refresh / Power-Down 상태)
  - _왜 못 받는가_ — CKE(Clock Enable)는 단순한 상태 플래그가 아니라 **내부 클럭을 게이팅하는 스위치**입니다. CKE=0 이면 DRAM 내부의 클럭 버퍼가 차단되어 command decoder·address latch 같은 동기 회로에 클럭 에지가 전달되지 않습니다. 명령은 CK 에지에 맞춰 sample 되어야 디코딩되는데, 그 에지 자체가 회로에 도달하지 않으므로 CA 핀에 무엇이 실려 있든 latch 되지 않고 그냥 흘러갑니다. 즉 CKE=0 은 "명령을 거부" 하는 게 아니라 명령을 _볼 수 있는 클럭 자체를 꺼 둔_ 상태이며, 이것이 power-down/self-refresh 에서 전력을 아끼는 메커니즘이기도 합니다.
- DRAM 모델은 *조용히 명령을 drop* 하거나, *X*를 내부 상태에 전파
- 시뮬레이션은 *계속 진행*되며 후속 RD/WR이 *잘못된 데이터*를 반환
- 결과: scoreboard mismatch가 *몇 us 후*에 발생 — **timestamp가 떨어져 있어 debug 어려움**

**Step 3 — DV 적용**

1. SVA로 *CKE=0 상태에서 MRW 명령이 들어가면 즉시 error*:
   ```systemverilog
   property p_no_mrw_when_cke_low;
       @(posedge clk) (cmd == MRW) |-> (cke == 1'b1);
   endproperty
   a_no_mrw_cke_low: assert property (p_no_mrw_when_cke_low);
   ```
2. covergroup `init_cg` 에 `pda_done`, `cs_training_done` bin
3. directed test `test_init_violation` 로 일부러 잘못된 순서를 발급 → assertion이 catch하는지 확인

</details>
---

## 9. 핵심 정리 (Key Takeaways)

- DRAM은 RTL reset만으로는 동작 불가. Voltage ramp → RESET → CKE → MR Write → ZQCL → Training 의 전체 시퀀스 필요.
- DDR4의 MR programming 순서는 *MR3→6→5→4→2→1→0* (spec 규정).
- DDR5는 *CS training*, *PDA*, *DCA/DFE 초기화*가 추가됨.
- LPDDR4는 *Vdd1→Vdd2→Vddq* 의 정해진 ramp 순서. VDDQ는 LPDDR4=1.1V, LPDDR4X=0.6V.
- **LPDDR5(주축)**: 전압은 *SoC-side(외부) PMIC*가 생성 — DRAM은 VDD1(1.8V)/VDD2H(≈1.05V)/VDDQ(0.5V)를 *받기만* 함. **on-package PMIC/DIMM/RCD 없음** (DDR5의 on-DIMM PMIC와 정반대). DVFS는 *SoC 주도*.
- LPDDR5 init training: **CBT(Mode1/2) + WCK2CK Leveling**(LPDDR5 고유) — DDR5의 CA/CS training과 다른 구성. gear(DVFSC) 전환 시 WCK2CK 재정렬.
- UVM phase 매핑: pre_reset → reset → post_reset → pre_configure → configure → post_configure → main.
- CKE=0 상태에서 MRW 같은 위반은 *조용히* 진행되어 후속에서 mismatch — SVA로 *즉시* catch해야 한다.

## 10. PDF 정밀 인용 — DDR5 §3.3 Power-up Init

> 출처: JESD79-5C.01 v1.31 §3.3, Table 9 (MR Default Settings), Figure 4, Table 10 (Voltage Ramp Conditions)

### 10.1 MR Default Settings (Table 9) — power-up 시 DRAM이 가정하는 값

> 스펙 인용 (§3.3): "For power-up and reset initialization, in order to prevent DRAM from functioning improperly, default values for the following MR settings need to be defined."

| Item | Mode Register | Default Setting | Description |
|---|---|---|---|
| Burst Length | MR0 OP[1:0] | `00B` | **BL16** |
| Read Latency | MR0 OP[6:2] | `00010B` | **RL(CL) = 26 @ DDR5-3200** |
| Write Latency | n/a | WL = RL-2 (CWL=CL-2) | Fixed based on RL(CL) |
| Write Recovery (tWR) | MR6 OP[3:0] | `0000B` | **tWR = 48 nCK @3200, or 30 ns** |
| Read to Precharge Delay (tRTP) | MR6 OP[7:4] | `0000B` | **tRTP = 12 nCK @3200, or 7.5 ns** |
| VrefDQ Value | MR10 | `0010 1101B` | VREF(DQ) Range = **75% of VDDQ** |
| VrefCA Value | MR11 | `0010 1101B` | VREF(CA) Range = **75% of VDDQ** |
| VrefCS Value | MR12 | `0010 1101B` | VREF(CS) Range = **75% of VDDQ** |
| ECS Error Threshold Count (ETC) | MR15 | `011B` | **256** |
| Post Package Repair | MR23 OP[1:0] | `00B` | **hPPR and sPPR Disabled** |
| CK ODT | MR32 OP[2:0] | strap-based | Group A = RTT_OFF=`000B`, Group B = 40 Ω = `111B` |
| CS ODT | MR32 OP[5:3] | strap-based | Group A = RTT_OFF, Group B = 40 Ω |
| CA ODT | MR33 OP[2:0] | strap-based | Group A = RTT_OFF=`000B`, Group B = 80 Ω = `100B` |
| DQS_RTT_PARK | MR33 OP[5:3] | `000B` | **RTT OFF** |
| RTT_PARK | MR34 OP[2:0] | `000B` | **RTT OFF** |
| RTT_WR | MR34 OP[5:3] | `001B` | **240 Ω** |
| RTT_NOM_WR | MR35 OP[2:0] | `011B` | **80 Ω** |
| RTT_NOM_RD | MR35 OP[5:3] | `011B` | **80 Ω** |
| RTT Loopback | MR36 OP[2:0] | `000B` | **RTT OFF** |
| RFM RAAIMT | MR58 OP[4:1] | vendor specific | (Refresh Management) |
| RFM RAAMMT | MR58 OP[7:5] | vendor specific | |
| RFM RAA Counter | MR59 OP[7:6] | vendor specific | |

:::tip[DV 적용 — Default Reset 값 SVA]
Power-on reset 직후 *MR을 readback*해서 위 default와 *일치*하는지 SVA 또는 RAL(register abstraction layer, UVM에서 레지스터를 추상화해 읽기/쓰기/검증하는 모델) verify로 확인.

```systemverilog
// DDR5 init reset value check
task check_default_mr_values();
    uvm_status_e status;
    bit [7:0] read_val;

    ral.MR0.read(status, read_val, UVM_FRONTDOOR);
    if (read_val[1:0] !== 2'b00)
        `uvm_error("MR_DEFAULT", $sformatf("MR0[1:0]=0x%x, expected 0x0 (BL16)", read_val[1:0]))
    if (read_val[6:2] !== 5'b00010)
        `uvm_error("MR_DEFAULT", $sformatf("MR0[6:2]=0x%x, expected 0x2 (CL=26@3200)", read_val[6:2]))

    ral.MR10.read(status, read_val, UVM_FRONTDOOR);
    if (read_val !== 8'b0010_1101)
        `uvm_error("MR_DEFAULT", $sformatf("MR10=0x%x, expected 0x2D (VrefDQ 75%)", read_val))
    // ... MR11, MR12, MR15, MR23, MR32~36 모두 ...
endtask
```
:::
### 10.2 Voltage Ramp Conditions (Table 10)

> 스펙 원문 인용 (§3.3.1 Step 1): "While applying power (after Ta), RESET_n is recommended to be LOW (≤0.2 × VDDQ) and all other inputs may be undefined. The device outputs remain disabled while RESET_n is held LOW. Power supply voltage ramp requirements are provided in Table 10. **VPP shall ramp at the same time or earlier than VDD**."

| After | Application Conditions |
|---|---|
| Ta is reached | **VPP shall be greater than VDD** |

_왜 VPP 가 VDD 보다 먼저(또는 같이) ramp 되고, 항상 VDD 보다 높아야 하는가_ 는 word-line 부스팅의 물리에서 나옵니다. VPP 는 이름 그대로 "pumped" 전압으로, DRAM 코어 전압(VDD)보다 더 높은 전압입니다. 그 이유는 access transistor(NMOS)를 _완전히_ 켜서 셀 capacitor 를 VDD 전체까지 충전하려면, 게이트(word-line)에 VDD + Vth(문턱전압) 이상을 걸어야 하기 때문입니다 — 게이트가 VDD 밖에 안 되면 transistor 의 문턱전압 강하 때문에 셀이 VDD−Vth 까지밖에 안 차서 '1' 마진이 줄어듭니다. 그래서 word-line driver 는 VPP(>VDD)로 구동됩니다. 만약 전원을 켤 때 VDD 가 VPP 보다 먼저 올라와 코어가 살아 있는데 word-line 쪽 고전압이 아직 없는 상태가 되면, 내부 전위 관계가 설계 가정과 어긋나 기생 다이오드가 순방향이 되거나 **latch-up**(전원-접지 간 기생 SCR 도통)이 유발될 수 있습니다. VPP 를 먼저 또는 동시에 올려 항상 가장 높은 rail 로 유지하면 이런 비정상 전위 형성을 막을 수 있어, JEDEC 이 ramp 순서를 규정한 것입니다.

> NOTE 1: Ta is the point when any power supply first reaches 300 mV.
> NOTE 2: Voltage ramp conditions apply between (Ta) and Power-off.
> NOTE 3: Tb is the point at which all supply and reference voltages are within their defined ranges.
> NOTE 4: Power ramp duration (Tb - Ta) shall not exceed tINIT0.

### 10.3 Power-up Initialization Sequence — 단계 인용

> 출처: JESD79-5C.01 §3.3.1, Figure 4

스펙 원문 인용 (§3.3.1 Steps 1~4):

1. *Step 1*: RESET_n LOW (≤0.2 × VDDQ) 로 유지. all other inputs may be undefined. VPP shall ramp at the same time or earlier than VDD.
2. *Step 2*: Voltage ramp 완료 (Tb 시점). RESET_n LOW 유지. DQ, DQS_t, DQS_c, CS_n, CK_t, CK_c, CA 입력 레벨은 VSS~VDDQ 사이.
3. *Step 3*: Tb 부터 RESET_n LOW 유지 *최소 tINIT1 (Tb→Tc)*. 후 HIGH (Tc). RESET_n de-assert *최소 tINIT2 이전*에 CS_n=LOW 설정 필요. 다른 입력은 "Don't Care". DRAM은 RESET_n을 *indefinitely* hold 지원.
4. *Step 4*: RESET_n HIGH (Tc) 후, *최소 tINIT3* 대기 후 CS_n HIGH 가능.

### 10.4 Figure 4 의 Phase 구분 — Power Ramp → Configuration

```
T_a → T_b → T_c → T_d → T_e → T_f → T_g → T_h ...
│ Power │ Reset │ Initialization │ CS_CMOS Registration │ Configuration ...
│ Ramp  │       │                │ & ODT Async Off       │
├──────┤
│tINIT0 (Ta→Tb)
       ├──────┤
       │tINIT1 (Tb→Tc) — RESET_n LOW 최소
              ├──────┤
              │tINIT2 (...) — CS_n LOW 보장 시점
                     ├──────┤
                     │tINIT3 — RESET_n HIGH → CS_n HIGH 가능
                            ├──────┤
                            │tINIT4
                                   ├──────┤
                                   │tINIT5
                                          ├──────┤
                                          │tXPR — DES/NOP 만
                                                 ├──────┤
                                                 │tMRD — MRW 시작
```

여기서 **DES**(deselect, "아무 명령도 아님"을 뜻하는 무동작 명령), **NOP**(no operation, 마찬가지로 아무 일도 하지 않는 명령), **MPC**(multi-purpose command, training 등 특수 동작을 지시하는 명령)를 알아 둡니다. DV 검증 포인트:
- **각 tINIT* timing 위반** SVA로 catch
- **CS_n LOW 보장 시점** (tINIT2 이전) 검증
- **DES/NOP only window** (CKE HIGH 후 ~ first MRW 까지) 동안 다른 명령 금지

```systemverilog
// 출처: JESD79-5C.01 §3.3.1 + Figure 4
// tINIT 단계별 위반 catch
typedef enum {INIT_PHASE_PWR, INIT_PHASE_RST, INIT_PHASE_INIT, INIT_PHASE_CFG, INIT_PHASE_READY} init_phase_e;
init_phase_e init_phase;

property p_no_cmd_during_reset;
    @(posedge clk) (init_phase == INIT_PHASE_RST) |->
        cmd_decoded inside {CMD_DES, CMD_NOP};
endproperty

property p_no_legal_cmd_before_training;
    @(posedge clk) (init_phase == INIT_PHASE_INIT) |->
        cmd_decoded inside {CMD_DES, CMD_NOP, CMD_MPC};
            // MPC for CS/CA training is allowed
endproperty
```

### 10.5 Step 5~10 (§3.3.1 cont'd, Figure 4 NOTES 인용)

> 스펙 NOTES 인용 (Figure 4):
>
> 5. "Prior to ZQcal completion at (Tk), MPC commands shall be Multi-Cycle as described in the MPC command Timings section."
> 6. "From time point (Tk) until (Tl), MPC, VREFCA and VREFCS commands prior to CS and CA training successfully completing, shall be Multi-Cycle (MR2:OP[4]=0) as described in the MPC, VREFCS, and VREFCA timing sections."
> 7. "At time point (Tl), with successful completion of CS and CA training, an MRW command setting MR2:OP[4]=1 is recommended and allows for MPC, VREFCS, VREFCA commands to be **single-cycle, improving training duration**."
> 8. "From time point (Tk) until (Tz), DES commands shall be applied between legal commands (MRR, MRW, MPC, VREFCS, & VREFCA)."
> 9. "Starting at Tl, MRW commands shall be issued to all Mode Registers that require defined settings."

DV 검증 포인트:
- **MR2:OP[4] 전환** (multi-cycle → single-cycle MPC): training 완료 (Tl) 후에만
- **DES 명령 의무**: Tk ~ Tz 사이 legal command 간에 *반드시 DES* 삽입
- **MRW 시퀀스**: defined settings를 위한 MRW가 *Tl 이후* 발급

## 11. Further Reading

- 이전: [Ch02. 패키지·핀아웃·어드레싱](../02_package_pinout_addressing/)
- 다음: [Ch04. Mode Register 깊이 분석](../04_mode_registers/)
- 부록: [JEDEC Spec 빠른 참조](../appendix_a_quick_reference/)
- 퀴즈: [Ch03 퀴즈](../quiz/ch03_quiz/)

