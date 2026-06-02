---
title: "Ch08. Training — CA / DQ / DQS / Read DQ Calibration"
---

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">CH 08</span>
</div>

## 🎯 Learning Objectives

- **Describe**: Training이 high-speed DRAM signaling에서 *왜* 필요한지를 sampling timing/eye-opening 관점에서 서술한다.
- **Compare**: DDR4 Write Leveling / MPR-based training vs DDR5 DQS Training (MR3) vs LPDDR5 CBT Mode1/2 + WCK2CK Leveling 의 절차를 비교한다.
- **Trace**: LPDDR5 CBT Mode1 시퀀스를 cycle-level로 추적한다.
- **Design**: Training failure injection 시나리오와 coverage를 설계한다.

## Prerequisites

- [Ch07. Refresh·RFM](../07_refresh_rfm/)
- 디지털 신호 무결성 기초 (eye diagram, jitter, ISI)

## 1. 왜 training이 필요한가

DDR4-3200(1.6GHz)부터 DDR5-8400(4.2GHz), LPDDR5-9600(4.8GHz)까지 신호 속도가 크게 높아졌습니다. 신호 속도가 빨라지면 eye diagram의 가로 폭(timing margin)과 세로 폭(voltage margin)이 모두 좁아집니다. 고정된 sampling 타이밍을 사용하면 어떤 보드에서는 eye의 가장자리를 sample하게 되어 비트 오류가 발생할 수 있습니다.

문제를 더 복잡하게 만드는 것은 시스템마다 조건이 다르다는 점입니다. PCB trace 길이는 보드 설계에 따라 다르고, 동작 온도와 전원 전압도 시간에 따라 변합니다. 제조 편차도 있어서 동일 lot의 device라도 내부 지연 특성이 조금씩 다릅니다. 결국 "최적의 sampling 타이밍"은 시스템마다, 심지어 같은 시스템 내 핀마다 다릅니다.

Training은 이 문제를 초기화 시에 해결합니다. 알려진 패턴을 주고받으면서 최적의 sampling 포인트, Vref, duty cycle, equalizer 계수를 찾아 MR에 기록합니다. training이 완료되면 그 값이 normal operation 동안 적용됩니다.

```
이상적 eye opening:
        ┌─────data─────┐
        │              │
        │              │
        └──────────────┘
        ↑              ↑
       너무 빠름      너무 늦음
            ▲
        최적 sampling point ← training이 찾는 것
```

---

## 2. DDR4 Training — 기준점

> 출처: JESD79-4D §4.7 (Write Leveling), §4.10 (MPR), §4.13 (DQ Vref Training)

### 2.1 Write Leveling (§4.7)

목적: DQS와 CK 의 *정렬* 맞추기 (DRAM 입장에서 DQS edge가 CK edge와 정확히 align되도록).

```
Procedure:
1. controller가 WR Leveling mode 진입 (MR1 enable)
2. controller가 DQS toggle (다양한 delay로)
3. DRAM이 *현재 CK 시점의 DQS 값*을 DQ에 출력
4. controller가 DQ를 읽고 0→1 transition 시점 = DQS-CK 정렬점
5. controller가 delay 값 저장 + WR Leveling mode 종료
```

### 2.2 MPR-based DQ Training (§4.10)

DDR4는 *Multi-Purpose Register (MPR)* 라는 *내부 고정 패턴*을 두고, RD 명령으로 이 패턴을 읽어 DQ sampling 을 calibration.

### 2.3 DQ Vref Training (§4.13)

DQ receiver의 *reference voltage*를 sweep해 *eye opening*을 최대화. MR6 + VrefDQ 비트.

---

## 3. DDR5 Training — 더 정교해짐

> 출처: JESD79-5C.01 v1.31 §3.5.4 (MR3 DQS), §3.5.27~3.5.33 (MR25~MR31 Read Training)

### 3.1 DQS Training (MR3)

DDR5는 MR3에 *DQS Training Mode*를 두어:
- DQS edge 위치 sweep
- DQS preamble 패턴 confirm
- Per-byte DQS 정렬

### 3.2 Read Training Mode (MR25~MR31)

- **MR25**: Read Training Mode Settings
- **MR26, MR27**: Read Pattern Data0/Data1 / LFSR0/LFSR1
- **MR28, MR29**: Read Pattern Invert (DQL / DQU)
- **MR30**: Read LFSR Assignments
- **MR31**: Read Training Pattern Address

DRAM이 *내부 LFSR* 또는 *고정 pattern*을 DQ에 출력해 controller가 *eye opening*을 찾도록.

### 3.3 DCA (Duty Cycle Adjuster) Training

> 출처: JESD79-5C.01 §3.5.45~3.5.121 (MR42~MR254 DCA)

DDR5는 *clock duty cycle*까지 training. 고속 신호에서 duty가 50%가 아니면 *eye가 비대칭*.

- MR42~MR48: DCA Types Supported, DCA Settings
- MR103~MR254: per-DQ DCA + Vref offset

### 3.4 DDR5 training step-by-step (개념)

```
1. CS Training      → CS_n 신호 정렬 (MR13 CS Geardown)
2. CA Training      → CA[6:0] 신호 정렬 (PDA + MR write)
3. DQS Preamble Cfg → MR8 (Preamble 길이)
4. Write Leveling   → DDR4와 유사한 패턴, MR7 사용
5. Read Training    → MR25~MR31 활용
6. DQ Vref Calib    → MR10 (VrefDQ)
7. CA Vref Calib    → MR11 (VrefCA)
8. CS Vref Calib    → MR12 (VrefCS)
9. DCA Settings     → MR42~MR48
10. DFE Training    → MR21, MR70~MR75, MR111~MR116
```

---

## 4. LPDDR4 Training

> 출처: JESD209-4E §4.26~4.34

LPDDR4 training은 *Command Bus Training (CBT)* 가 핵심입니다.

### 4.1 CBT (Command Bus Training) — §4.28

CA 신호 정렬을 위한 training:
- **CBT for x16 mode**: 16-bit data 모드
- **CBT for Byte (x8) Mode**: byte 모드

CBT 동안 *임시 패턴*을 CA에 보내고 DRAM이 DQ로 capture pattern을 출력. controller가 *비교*해 정렬 보정.

### 4.2 LPDDR4 의 training 흐름

1. ZQ Calibration (§4.38)
2. VREF Current Generator (VRCG, §4.25)
3. CA VREF Training (§4.26)
4. DQ VREF Training (§4.27)
5. CBT (§4.28)
6. Frequency Set Point change (§4.29)
7. Write Leveling (§4.30)
8. RD DQ Calibration (§4.31)
9. DQS-DQ Training (§4.32)
10. DQS Interval Oscillator (§4.33)
11. READ Preamble Training (§4.34)

---

## 5. LPDDR5 Training — WCK 도입으로 한층 복잡

> 출처: JESD209-5C §4.2

LPDDR5의 *WCK* 클럭이 *CK와 분리*되었으므로, WCK 관련 training 단계가 *대거 추가*됩니다.

### 5.1 LPDDR5 training 흐름

LPDDR5 training은 WCK가 추가되면서 DDR4/DDR5보다 훨씬 복잡해졌습니다. CK와 WCK를 각각 정렬해야 하고, DVFS 지원으로 인해 주파수 변경 시 일부 단계를 반복해야 하기도 합니다.

```
1. ZQ Calibration (§4.2.1)
   - Background calibration / Command-based calibration
2. CBT Mode1 (§4.2.2.2) — 첫 단계
3. CBT Mode1 with DVFSQ (§4.2.2.3)
4. CBT Mode2 (§4.2.2.4) — 더 정교한 보정
5. CBT Mode2 with DVFSQ (§4.2.2.5)
6. CA VREF Training (§4.2.3)
7. DQ VREF Training (§4.2.4)
8. WCK2CK Leveling (§4.2.5) — WCK ↔ CK 정렬
9. Duty Cycle Adjuster (DCA) Training (§4.2.6)
10. Read DCA (§4.2.7)
11. Duty Cycle Monitor (DCM) (§4.2.8)
12. READ DQ Calibration (§4.2.9)
13. WCK-DQ Training (§4.2.10)
14. RDQS Toggle Mode / Enhanced RDQS Training (§4.2.11, §4.2.12)
15. Read/Write-based WCK-RDQS_t Training (§4.2.13)
16. Rx Offset Calibration (§4.2.14)
```

이 16개 이상의 단계가 모두 정상 동작해야 normal traffic이 가능합니다. 어느 한 단계라도 fail이면 데이터 corruption이나 DRAM 미응답이 발생합니다. 단계 사이에 의존 관계가 있어서(예: WCK2CK leveling은 CBT가 완료되어야 진행 가능), 어느 단계에서 실패했는지를 FSM으로 추적하는 것이 DV 설계에서 핵심입니다.

### 5.2 CBT Mode1 — 핵심 절차

> JESD209-5C §4.2.2.2

LPDDR5 CBT Mode1 은:
1. Controller가 CBT 모드 진입 명령 발급
2. Three Physical MR 사용 — *임시 MR write*
3. Controller가 CA에 *알려진 패턴* 전송
4. DRAM이 *capture 결과*를 DQ에 출력
5. Controller가 비교 → 보정 → 반복
6. CBT 종료 명령

### 5.3 WCK2CK Leveling (§4.2.5)

WCK가 CK와 정확히 정렬되어야 *CAS WCK2CK Sync 비트*가 의미를 가짐. WCK 주파수는 CK의 2× 또는 4× (CKR 설정에 따라):

```
CK_t:   |‾‾‾‾|____|‾‾‾‾|____|‾‾‾‾|____|
WCK_t:  |‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|     (4× ratio)
         ↑
         정렬 (WCK edge가 CK edge와 정렬되어야 함)
```

### 5.4 DCM (Duty Cycle Monitor) — §4.2.8

WCK clock의 *duty cycle*을 *측정*. 50%에서 벗어나면 DCA로 보정.

---

## 6. DV 적용 — Training FSM Model

training은 *FSM (Finite State Machine)*으로 모델링하면 깔끔.

### 6.1 LPDDR5 Training FSM (개념)

```d2
direction: down

Init: Init
ZQ_Cal: ZQ_Cal
CBT_Mode1: CBT_Mode1
CBT_Mode2: CBT_Mode2
CA_VREF: CA_VREF
DQ_VREF: DQ_VREF
WCK2CK_Lvl: WCK2CK_Lvl
DCA: DCA
Read_Training: Read_Training
Normal: Normal
Training_Fail: Training_Fail

Init -> ZQ_Cal: power_good
ZQ_Cal -> CBT_Mode1: zq_done
CBT_Mode1 -> CBT_Mode2: cbt1_pass
CBT_Mode2 -> CA_VREF: cbt2_pass
CA_VREF -> DQ_VREF: ca_vref_done
DQ_VREF -> WCK2CK_Lvl: dq_vref_done
WCK2CK_Lvl -> DCA: wck_aligned
DCA -> Read_Training: dca_done
Read_Training -> Normal: rd_train_done

Init -> Training_Fail: timeout
ZQ_Cal -> Training_Fail: zq_fail
CBT_Mode1 -> Training_Fail: cbt1_fail
```

### 6.2 Training FSM model (SystemVerilog skeleton)

```systemverilog
typedef enum {
    TR_INIT, TR_ZQ_CAL, TR_CBT_MODE1, TR_CBT_MODE2,
    TR_CA_VREF, TR_DQ_VREF, TR_WCK2CK_LVL, TR_DCA,
    TR_READ_TRAINING, TR_NORMAL, TR_TRAINING_FAIL
} lpddr5_training_state_e;

class lpddr5_training_monitor extends uvm_monitor;
    `uvm_component_utils(lpddr5_training_monitor)

    lpddr5_training_state_e state, next_state;

    // 전이 기록 — coverage 용
    uvm_analysis_port #(lpddr5_training_state_e) state_ap;

    virtual function void next_step(string event_name);
        case (state)
            TR_INIT       : if (event_name == "power_good")  next_state = TR_ZQ_CAL;
            TR_ZQ_CAL     : if (event_name == "zq_done")     next_state = TR_CBT_MODE1;
            TR_CBT_MODE1  : if (event_name == "cbt1_pass")   next_state = TR_CBT_MODE2;
                            else if (event_name == "cbt1_fail") next_state = TR_TRAINING_FAIL;
            // ... 나머지 ...
            default       : ;
        endcase
        if (next_state != state) begin
            `uvm_info("TRAINING_FSM",
                $sformatf("Transition %s → %s on event %s",
                          state.name(), next_state.name(), event_name),
                UVM_MEDIUM)
            state = next_state;
            state_ap.write(state);
        end
    endfunction
endclass
```

### 6.3 Training step coverage

```systemverilog
covergroup training_step_cg with function sample (lpddr5_training_state_e state);
    cp_state: coverpoint state {
        bins zq            = {TR_ZQ_CAL};
        bins cbt_mode1     = {TR_CBT_MODE1};
        bins cbt_mode2     = {TR_CBT_MODE2};
        bins ca_vref       = {TR_CA_VREF};
        bins dq_vref       = {TR_DQ_VREF};
        bins wck2ck_lvl    = {TR_WCK2CK_LVL};
        bins dca           = {TR_DCA};
        bins read_training = {TR_READ_TRAINING};
        bins normal        = {TR_NORMAL};
        bins fail          = {TR_TRAINING_FAIL};
    }
endgroup

// 모든 step이 *적어도 한 번* hit되어야 sign-off 가능
```

---

## 7. DV 적용 — Training Failure Injection

각 training 단계에서 *failure를 의도적으로 주입*해 controller의 recovery를 검증.

### 7.1 Failure injection sequence (예: WCK2CK 실패)

```systemverilog
class lpddr5_wck2ck_fail_inject_seq extends uvm_sequence;
    `uvm_object_utils(lpddr5_wck2ck_fail_inject_seq)

    virtual task body();
        // Step 1: 일반 시퀀스로 ZQ, CBT까지 진행
        do_zq_cal();
        do_cbt_mode1();
        do_cbt_mode2();

        // Step 2: WCK2CK 단계에서 *의도적*으로 WCK delay 큰 값 주입
        `uvm_info("FAIL_INJECT", "Injecting bad WCK delay", UVM_MEDIUM)
        force_wck_delay_excessive();
            // → DRAM model이 *training fail* 응답을 내야 함

        // Step 3: Controller가 recovery 시도하는지 monitor
        wait_for_recovery_attempt();

        // Step 4: 정상 값으로 복귀
        release_wck_delay();

        // Step 5: Training 완료
        do_remaining_training_steps();
    endtask

    extern task force_wck_delay_excessive();
    extern task wait_for_recovery_attempt();
endclass
```

### 7.2 Coverage — failure injection 시나리오

```systemverilog
covergroup training_fail_cg with function sample (
    lpddr5_training_state_e fail_state,
    bit recovered
);
    cp_fail_at: coverpoint fail_state {
        bins zq_fail        = {TR_ZQ_CAL};
        bins cbt1_fail      = {TR_CBT_MODE1};
        bins cbt2_fail      = {TR_CBT_MODE2};
        bins ca_vref_fail   = {TR_CA_VREF};
        bins dq_vref_fail   = {TR_DQ_VREF};
        bins wck_fail       = {TR_WCK2CK_LVL};
        bins dca_fail       = {TR_DCA};
        bins rd_train_fail  = {TR_READ_TRAINING};
    }
    cp_recovery: coverpoint recovered {
        bins yes = {1};
        bins no  = {0};
    }
    cx_fail_recovery: cross cp_fail_at, cp_recovery;
endgroup
```

---

## 8. 대표 문제 — LPDDR5 CBT Mode1 dry-run

:::tip[Q. LPDDR5 controller가 CBT Mode1 진입 후 다음 동작을 한다. 각 cycle별 expected behavior를 추적하고, 어떤 점이 spec violation이 될 수 있는지 분석하라.]

```
Cycle  0: Enter CBT mode (special MR write)
Cycle  1: Three Physical MR write — calibration pattern
Cycle  2-5: Controller sends CA pattern [0xA, 0x5, 0xC, 0x3] on CA[5:0]
Cycle  6-9: DRAM responds — DQ outputs capture result
Cycle 10: Controller compares → decides next iteration
Cycle 11: Exit CBT mode
```
:::
<details>
<summary>풀이 (CBT Mode1 trace + violation 분석)</summary>


**Step 1 — Cycle-by-cycle expected behavior**

| Cycle | Phase | Expected |
|---|---|---|
| 0 | Entry | MR write가 *CBT entry MR* (LPDDR5 §6 참조)로 향함. 잘못된 MR이면 진입 실패 — *조용히 normal 모드 유지*. |
| 1 | Setup | Three Physical MR write — capture pattern (예: 0xAA), invert pattern, control |
| 2-5 | Pattern send | Controller가 CA[5:0]에 알려진 패턴 [0xA, 0x5, 0xC, 0x3] 전송. CA의 *모든 비트*가 toggle되도록 패턴 선택. |
| 6-9 | DRAM response | DRAM이 *capture 결과*를 DQ에 출력. 정상이면 *입력 패턴과 동일*하거나 *defined transform* 결과. |
| 10 | Compare | Controller가 DQ 출력 = expected 인지 비교. mismatch가 *너무 크면* delay 보정 후 retry. |
| 11 | Exit | CBT exit MR write. *normal 모드*로 전환. |

**Step 2 — Spec violation 가능성**

1. **Cycle 0 entry 실패 + 계속 traffic 발급**: CBT entry가 무시되었는데 controller가 *알지 못하고* 일반 RD/WR을 발급 → DRAM이 일반 명령으로 해석 → 잘못된 동작
   - SVA: CBT entry MR 발급 후 *최소 N cycles* 안에 일반 traffic이 발급되지 않아야 함
2. **Cycle 1 의 Three Physical MR 순서 위반**: LPDDR5 §6 의 *순서가 정해진 MR*. 순서 어기면 *training 동작이 정의되지 않음*.
   - DV scoreboard: MR write 순서를 *명시적*으로 검증
3. **Cycle 2-5 의 CA 패턴**: *random*이거나 *too few unique values* 면 calibration 정확도 ↓. 일반적으로 *모든 CA 비트가 toggle*되는 패턴 권장.
   - covergroup `cbt_ca_pattern_cg`: 사용된 CA 패턴의 *unique count* bin
4. **Cycle 6-9 의 DRAM response timing**: training mode에서 DQ 출력은 *정해진 latency* (예: 4 cycles 후). controller가 *잘못된 timing*에 sample하면 잘못된 비교.
   - SVA: training mode CA→DQ latency 정확 검증
5. **Cycle 10 의 compare failure 시**: *infinite retry*하면 power-on이 오래 걸리고 timeout fail. controller가 *max retry count*를 두어야 함.
   - timeout assertion + coverage bin

**Step 3 — DV 적용 — CBT 검증의 핵심**

- `cbt_state_cg`: CBT entry/setup/pattern/response/compare/exit *모든 phase* cover
- `cbt_ca_pattern_cg`: CA 패턴 *uniqueness*와 *coverage*
- `cbt_retry_cg`: *retry count* 의 distribution (0, 1, 2-5, 6+)
- directed test `test_cbt_mode1_normal`: 정상 시퀀스
- directed test `test_cbt_mode1_corrupted_response`: DRAM model이 *의도적으로 잘못된* response 반환 → controller가 retry 또는 fail 처리 검증

</details>
---

## 9. PDF 정밀 인용 — DDR5 MR3 (DQS Training) + MR5/MR6

> 출처: JESD79-5C.01 v1.31 §3.5.5 (MR3), §3.5.7 (MR5), §3.5.8 (MR6)

### 9.1 MR3 (MA[7:0]=03H) — DQS Training 정밀 비트 매핑

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| Write Leveling Internal Cycle Alignment — **Upper Byte** [OP7:4] | ← | ← | ← | Write Leveling Internal Cycle Alignment — **Lower Byte** [OP3:0] | ← | ← | ← |

**OP[3:0] (Lower Byte WL Internal Cycle Alignment) — R/W**:

| OP[3:0] | tCK Offset |
|---|---|
| `0000B` | **0 tCK (Default)** |
| `0001B` | -1 tCK |
| `0010B` | -2 tCK |
| `0011B` | -3 tCK |
| `0100B` | -4 tCK |
| `0101B` | -5 tCK |
| `0110B` | -6 tCK |
| `0111B` | -7 tCK (Optional) |
| `1000B` | -8 tCK (Optional) |
| ... | ... |
| `1110B` | -14 tCK (Optional) |
| `1111B` | -15 tCK (Optional) |

**OP[7:4] (Upper Byte WL Internal Cycle Alignment) — R/W**: Same encoding (0 ~ -15 tCK).

> NOTE 1 (인용): "This is set during WL Training, after the host DQS has been aligned to the ideal External WL timings. **The Internal Write Timing is enabled and the WL Internal Timing Alignment is set to ensure the internal Write Enable aligns within tDQS2CK of the external WL Trained location**. When Internal Write Timing is Disabled, the WL Internal Cycle Alignment setting does not change the behavior of the write timings."
>
> NOTE 2: "The DRAM implementation may optionally have the same behavior when the Internal Write Timing is enabled vs disabled. This would mean that the CK and DQS timing paths remain matched internally. The WL Internal Cycle Alignment setting must still support pulling the Internal WL Pulse earlier so that the same WL Training Flow will produce the correct result."
>
> NOTE 3: "Lower Byte WL Internal Cycle Alignment is intended for **x4, x8, and x16 configurations**."
>
> NOTE 4: "Upper Byte WL Internal Cycle Alignment is intended for **x16 configuration only**. Although training of the Lower and Upper Bytes is independent, **contact the DRAM vendor regarding recommendations for setting the WICA values to the same offset**."
>
> NOTE 5: Optional OPcode may be needed for certain speed bins.

핵심 통찰:
- MR3은 **Write Leveling의 결과**를 저장 — Lower Byte (x4/8/16) + Upper Byte (x16 only)
- *Negative offset only* (0 ~ -15 tCK) — *internal WL pulse를 앞당기는* 방향만 지원
- x16 device에서 *Upper/Lower byte 독립 training* 가능하지만 spec은 *동일 offset* 권장
- Internal Write Timing disabled여도 동작은 동일 (Note 2)

### 9.2 MR5 (MA[7:0]=05H) — IO Settings 정밀 비트 매핑

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| Pull-Down Output Driver Impedance [OP7:6] | ← | DM Enable | TDQS Enable | PODTM Support | Pull-up Output Driver Impedance [OP2:1] | ← | Data Output Disable |

| Function | Type | Operand | Data |
|---|---|---|---|
| **Data Output Disable** | W | OP[0] | `0B`: Normal Operation (Default)<br>`1B`: Outputs Disabled |
| **Pull-up Output Driver Impedance** | R/W | OP[2:1] | `00B`: **RZQ/7 (34 Ω)**<br>`01B`: **RZQ/6 (40 Ω)**<br>`10B`: **RZQ/5 (48 Ω)**<br>`11B`: RFU |
| **Package Output Driver Test Mode Supported (PODTM)** | R | OP[3] | `0B`: Function Not Supported<br>`1B`: Function Supported |
| **TDQS Enable** | R/W | OP[4] | `0B`: Disable (Default)<br>`1B`: Enable |
| **DM Enable** | R/W | OP[5] | `0B`: Disable (Default)<br>`1B`: Enable |
| **Pull-Down Output Driver Impedance** | R/W | OP[7:6] | `00B`: **RZQ/7 (34 Ω)**<br>`01B`: **RZQ/6 (40 Ω)**<br>`10B`: **RZQ/5 (48 Ω)**<br>`11B`: RFU |

> RZQ = External ZQ resistor = 240 Ω. RZQ/7 ≈ 34.3 Ω, RZQ/6 = 40 Ω, RZQ/5 = 48 Ω.

DV 시사점:
- **Output impedance**: 34/40/48 Ω 중 선택 — system signal integrity에 따라 dynamic 설정.
- **TDQS Enable**: **x8 only** (MR5:OP[4]=1). x4/x16 device에서 이 비트 1로 set 시 *spec violation*.
- **DM Enable**: **x8 only** (MR5:OP[5]=1). x4 device에서 이 비트 1로 set 시 *spec violation*.
- TDQS + DM 동시 enable 시 *상호 배타* (TDQS는 DM pin 자리 사용).

```systemverilog
// MR5 검증 — x4 device에서 DM/TDQS 둘 다 disabled 강제
property p_x4_no_dm_tdqs;
    @(posedge clk) (dram_organization == ORG_X4) |->
        (ral.MR5.dm_enable.value == 1'b0) &&
        (ral.MR5.tdqs_enable.value == 1'b0);
endproperty
a_x4_no_dm_tdqs: assert property (p_x4_no_dm_tdqs)
    else `uvm_error("MR5_VIOL", "x4 device must not enable DM or TDQS")
```

### 9.3 MR6 (MA[7:0]=06H) — Write Recovery Time / tRTP 정밀 nCK 값

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| tRTP [OP7:4] | ← | ← | ← | Write Recovery Time [OP3:0] | ← | ← | ← |

**OP[3:0] — Write Recovery Time (Legacy / PRAC)** R/W:

| OP[3:0] | Legacy (nCK) | PRAC (nCK) |
|---|---|---|
| `0000B` | **48** (default) | **16** |
| `0001B` | 54 | 18 |
| `0010B` | 60 | 20 |
| `0011B` | 66 | 22 |
| `0100B` | 72 | 24 |
| `0101B` | 78 | 26 |
| `0110B` | 84 | 28 |
| `0111B` | 90 | 30 |
| `1000B` | 96 | 32 |
| `1001B` | 102 | 34 |
| `1010B` | 108 | 36 |
| `1011B` | 114 | 38 |
| `1100B` | 120 | 40 |
| `1101B` | 126 | 42 |
| `1110B` | 132 | 44 |
| `1111B` | RFU | RFU |

**OP[7:4] — tRTP (Legacy / PRAC)** R/W:

| OP[7:4] | Legacy (nCK) | PRAC (nCK) |
|---|---|---|
| `0000B` | **12** (default) | **8** |
| `0001B` | 14 | 9 |
| `0010B` | 15 | 10 |
| `0011B` | 17 | 11 |
| `0100B` | 18 | 12 |
| `0101B` | 20 | 13 |
| `0110B` | 21 | 14 |
| `0111B` | 23 | 15 |
| `1000B` | 24 | 16 |
| `1001B` | 26 | 17 |
| `1010B` | 27 | 18 |
| `1011B` | 29 | 19 |
| `1100B` | 30 | 20 |
| `1101B` | 32 | 21 |
| `1110B` | 33 | 22 |
| `1111B` | RFU | RFU |

> NOTE 1: tWR,min is defined in the "Timing Parameters" tables (Table 330 - Table 332). Host must operate with MR settings resulting in tCK × MR6:OP[3:0] ≥ tWR,min.
> NOTE 2: tRTP,min is defined in the "Timing Parameters" tables (Table 328 - Table 330). Host must operate with MR settings resulting in tCK × MR6:OP[7:4] ≥ tRTP,min.
> NOTE 3: All nCK conversions require rounding algorithm consideration.

**Legacy vs PRAC**:
- *Legacy*: 기존 DDR5 mode — 더 긴 tWR/tRTP (안전 마진 큼)
- *PRAC (Per Row Activation Counting)*: 더 *aggressive* nCK 값 — high-speed signaling 보상 + RAA counter와 통합 동작. *PRAC mode (MR70~MR75 활성화)* 시 이 값 적용.

DV 시사점:
- Controller가 *MR6 설정과 실제 사용 timing이 일치*하는지 검증
- *MR6 변경* 시 SVA `a_twr` / `a_trtp` 의 threshold도 *동적 update* 필요

```systemverilog
// MR6 값에 따른 dynamic timing check
int twr_nck_current;
int trtp_nck_current;

always @(ral.MR6.write_recovery_time.value or ral.MR6.trtp.value or prac_mode) begin
    case (ral.MR6.write_recovery_time.value)
        4'b0000: twr_nck_current = prac_mode ? 16 : 48;
        4'b0001: twr_nck_current = prac_mode ? 18 : 54;
        // ... 모든 case ...
        default: twr_nck_current = 48;
    endcase
    case (ral.MR6.trtp.value)
        4'b0000: trtp_nck_current = prac_mode ? 8 : 12;
        // ... 모든 case ...
        default: trtp_nck_current = 12;
    endcase
end

property p_twr_dynamic;
    @(posedge clk)
    (last_wr_burst_end) |-> ##[twr_nck_current : $] (cmd_decoded == CMD_PRE || cmd_decoded == CMD_PREab);
endproperty
a_twr_dynamic: assert property (p_twr_dynamic);
```

### 9.4 §3.5.6 MR4 — Refresh Settings 정밀 비트 매핑 (보강)

> Ch04 §10.1 의 학습용 모형 대신 *spec 원문 인용*:

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| TUF | RFU | Wide Range (Optional) | Refresh tRFC Mode | Refresh Interval Rate Indicator | Minimum Refresh Rate [OP2:0] | ← | ← |

**OP[2:0] — Minimum Refresh Rate (R)**:

| OP[2:0] | If Wide Range NOT supported (OP[5]=0) | If Wide Range supported (OP[5]=1) |
|---|---|---|
| `000B` | RFU | tREFI x1 (1x), **<75°C** nominal |
| `001B` | tREFI x1 (1x), **<80°C** nominal | tREFI x1 (1x), **75-80°C** nominal |
| `010B` | tREFI x1 (1x), **80-85°C** nominal | tREFI x1 (1x), **80-85°C** nominal |
| `011B` | tREFI /2 (2x), **85-90°C** nominal | tREFI /2 (2x), **85-90°C** nominal |
| `100B` | tREFI /2 (2x), **90-95°C** nominal | tREFI /2 (2x), **90-95°C** nominal |
| `101B` | tREFI /2 (2x), **>95°C** nominal | tREFI /2 (2x), **95-100°C** nominal |
| `110B` | RFU | tREFI /2 (2x), **>100°C** nominal |
| `111B` | RFU | RFU |

**OP[3] — Refresh Interval Rate Indicator (SR/W)**:
- Status Read: `0B`= Not implemented (Default), `1B`= Implemented
- Host Write: `0B`= Disabled (Default), `1B`= Enabled

**OP[4] — Refresh tRFC Mode (R/W)**:
- `0B`= **Normal Refresh Mode (tRFC1)**
- `1B`= **Fine Granularity Refresh Mode (tRFC2)**

**OP[5] — Wide Range (Optional, R)**:
- `0B`= Wide range not supported
- `1B`= Wide range supported (extended temperature)

**OP[7] — TUF (Temperature Update Flag, R)**:
- `0B`= No change in OP[2:0] since last MR4 read (default)
- `1B`= Change in OP[2:0] since last MR4 read

> NOTE 3 (인용): "DRAM vendors must report all of the possible settings over the operating temperature range of the device. Each vendor guarantees that their device will work at any temperature within the range when the system refresh interval follows there guidelines: **Threshold ≤ 85°C: tREFI x1 (1x Refresh Rate) or faster may be used. Threshold > 85°C: tREFI /2 (2x Refresh Rate) or faster is required. Data integrity at thresholds >95°C is not assured regardless of refresh rate**."
>
> NOTE 4: "The **2x Refresh Rate must be provided by the system before the DRAM Tj has gone up by more than 2°C** (Temperature Margin) since the first report out of OP[2:0]=011B. This condition is reset when OP[2:0] is equal to 010B."

DV 시사점 — TUF flag 동작 검증:
```systemverilog
// MR4 TUF 비트는 controller가 *MRR로 읽을 때* OP[2:0] 변경 발생 시 set
// MR4 read 후 TUF는 *clear*되어야 함
property p_tuf_clear_after_read;
    @(posedge clk) (mr4_read_completed) |=> (ral.MR4.tuf.get() == 1'b0);
endproperty
a_tuf_clear: assert property (p_tuf_clear_after_read);

// Temperature transition 시나리오
class ddr5_thermal_transition_seq extends uvm_sequence;
    `uvm_object_utils(ddr5_thermal_transition_seq)

    virtual task body();
        // 80°C → 85°C 천천히 올림. MR4 read해서 변경 감지
        set_dram_temperature(80);
        run_traffic(1000);
        check_mr4_setting();

        set_dram_temperature(86);
        run_traffic(500);
        wait_for_tuf_set();        // TUF=1 detect
        do_mr4_read();              // controller가 MR4 readback
        verify_refresh_rate_transition();  // tREFI/2로 전환 확인
    endtask
endclass
```

### 9.5 Training Step별 정확한 MR 매핑 정리

| Training Step | 사용 MR | 핵심 OP |
|---|---|---|
| CS Training | MR2 OP[4] (CS Assertion Duration MPC), MR13 (CS Geardown) | — |
| CA Training | MR2 OP[4] | — |
| ZQ Calibration | (명령 기반: ZQCS/ZQCL) | — |
| Write Leveling | **MR3** (WL Internal Cycle Alignment Upper/Lower), MR2 OP[1] (WL Training enable), MR7 (WL Internal +0.5tCK Alignment Offset) | OP[3:0]/OP[7:4] |
| Read Preamble Training | MR2 OP[0] (Read Preamble Training), MR8 OP[2:0] (Read Preamble) | — |
| DQ Vref Training | MR10 (VrefDQ Value) | OP[6:0] |
| CA Vref Training | MR11 (VrefCA Value) | OP[6:0] |
| CS Vref Training | MR12 (VrefCS Value) | OP[6:0] |
| Read Training Mode | MR25 (Read Training Mode Settings), MR26~MR31 (Read Pattern Data/Invert/LFSR) | — |
| DCA Training (per DQ) | MR42~MR48 (DCA group), MR103~MR254 (per-DQ DCA + VrefDQ offset) | — |
| DCM (Duty Cycle Monitor) | (LPDDR5 §4.2.8) | — |
| DFE Training | MR21 (Rx CTLE), MR70~MR75 (DFE Global), MR111 (DFE Global Settings), MR112~MR248 (per-DQ DFE Tap1~4 Gain Bias) | — |

> 정확한 MR70~MR75 (PRAC enable), MR111 (Global Enable + Tap-1~4 Enable), MR112~MR248 (Gain Bias Step 0~7, Sign bit) 의 비트 매핑은 JESD79-5C.01 §3.5.71~§3.5.86 참조.

## 10. 핵심 정리 (Key Takeaways)

- High-speed signaling (≥3.2 GT/s)에서 *training은 필수* — sampling timing/Vref/duty/equalizer를 *initial로 calibrate*.
- DDR4 training: Write Leveling + MPR-based DQ training + DQ Vref Training (3가지 핵심).
- DDR5 training: 위 + *CS Training*, *Read Training Mode (MR25~MR31)*, *DCA Training*, *DFE Training*.
- **DDR5 MR3 정밀**: WL Internal Cycle Alignment **Upper Byte (OP[7:4])** + **Lower Byte (OP[3:0])**. *0 ~ -15 tCK negative offset only*. x4/x8은 Lower만, x16은 Upper+Lower 독립 training.
- **MR5 IO Settings**: Pull-up/Pull-Down Output Driver Impedance **RZQ/7 (34Ω), RZQ/6 (40Ω), RZQ/5 (48Ω)** 중 선택. DM Enable / TDQS Enable은 **x8 only**.
- **MR6 정밀 nCK**: tWR Legacy `48~132 nCK` / PRAC `16~44 nCK`. tRTP Legacy `12~33 nCK` / PRAC `8~22 nCK`. **PRAC mode**는 RAA counter와 통합 동작.
- **MR4 Refresh Settings**: Wide Range (OP[5]) 지원 시 95~100°C, >100°C 범위 추가. **TUF (OP[7])**는 temperature change 감지 — MRR로 clear.
- LPDDR4 training: CBT (x16/x8 모드) + CA VREF + DQ VREF + Write Leveling + RD/DQS Training.
- LPDDR5 training: *16+ 단계*. CBT Mode1/2, *WCK2CK Leveling*, *DCA + DCM*, *WCK-DQ Training*.
- DV는 training FSM 을 *모델링*하고, *모든 step coverage* + *failure injection coverage* + *retry timeout* 을 검증.
- Failure injection은 *각 training step* 에서 *의도적*으로 fail을 만들어 *controller recovery*를 검증.

## 11. Further Reading

- 이전: [Ch07. Refresh·RFM](../07_refresh_rfm/)
- 다음: [Ch09. 신뢰성·ECC·CRC·PPR](../09_reliability_ecc_crc/)
- 부록 C: [SVA / Coverage 예제 모음](../appendix_c_sva_coverage_examples/)
- 퀴즈: [Ch08 퀴즈](../quiz/ch08_quiz/)

