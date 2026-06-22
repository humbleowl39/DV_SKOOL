---
title: "Ch07. Refresh·tREFI/tRFC·Refresh Management (RFM)"
---

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">CH 07</span>
</div>

## 🎯 Learning Objectives

- **Explain**: Refresh가 필요한 물리적 이유(cap leakage)와 destructive read의 관계를 설명한다.
- **Calculate**: tREFI=7.8us, tRFC=350ns 일 때 refresh가 차지하는 bandwidth overhead를 계산한다.
- **Distinguish**: refresh 입자(LPDDR5 per-bank, DDR5 same-bank REFsb, DDR4 all-bank)와 row-hammer 관리(DDR5 RFM, LPDDR5 ARFM/DRFM)의 차이를 구별하고, PASR가 LPDDR 고유(DDR5에 없음)임을 설명한다.
- **Design**: Rowhammer 시나리오 stim sequence와 RFM coverage를 설계한다.

## Prerequisites

- [Ch06. Timing·Preamble·Postamble](../06_timing_preamble/)
- DRAM cell 동작 (Ch01 §2)

## 1. Refresh의 본질 — 왜 필요한가

Ch01에서 살펴보았듯이 DRAM cell은 capacitor에 charge를 저장하는 1T1C 구조입니다. capacitor는 완전히 절연되어 있지 않아서 시간이 지나면 charge가 조금씩 leakage됩니다. 이 leakage를 방치하면 0과 1을 구분하는 전압 차이가 사라져 데이터가 손실됩니다. 일반 온도(85°C 이하)에서 64ms, 고온(85°C 초과)에서는 32ms 안에 모든 row를 한 번씩 재충전해야 합니다.

이 주기적 재충전 동작이 **Refresh**입니다. DRAM controller가 REF 명령을 발급하면 DRAM 내부 refresh counter가 다음 row를 선택하고 내부적으로 ACT-PRE 시퀀스를 수행합니다. controller는 몇 번째 row가 refresh되는지 알 필요 없고, 단지 정해진 간격 안에 REF를 발급하면 됩니다.

> **이 챕터의 주축은 LPDDR5**입니다. LPDDR5의 refresh는 **per-bank refresh**(REFpb로 한 bank만 refresh, 나머지 bank는 동시 사용)와 **PASR(Partial Array Self-Refresh)**를 중심으로 하며, PASR는 *LPDDR 계열 고유* 기능으로 **DDR5에는 없습니다**(DDR5에서는 deprecated — §10.6 참조). DDR5는 same-bank refresh(REFsb), DDR4는 all-bank refresh가 기본입니다. 아래에서는 LPDDR5를 기준으로 설명하고 DDR5/DDR4를 비교로 곁들입니다. row-hammer 대응(RFM/DRFM/ARFM)은 세대 공통 주제로 별도 절에서 다룹니다.

### 1.1 핵심 timing — tREFI / tRFC

- **tREFI** (Refresh Interval): **REF 명령의 평균 발급 간격**. LPDDR5/DDR5 = 3.9μs, DDR4 = 7.8μs @ normal temp. (단위: ns)
- **tRFC** (Refresh Cycle): REF → 다음 명령 가능까지. **density 의존**이라 단일 고정값이 아님 (예시로 350ns 가정). (단위: ns)

```
(LPDDR5/DDR5, tREFI=3.9us 기준)
시간:    0 ─────── 3.9us ─────── 7.8us ─────── 11.7us
명령:    REF        REF           REF            REF
        ▲          ▲             ▲              ▲
        │←─tRFC──→│ idle/traffic │
        ~350ns     ~3.55us
(DDR4는 tREFI=7.8us — REF 간격이 2배 넓음)
```

### 1.2 Refresh Bandwidth Overhead

Refresh가 차지하는 시간 비율 = `tRFC / tREFI`. LPDDR5/DDR5(tREFI=3.9μs)는 DDR4(7.8μs)보다 REF가 2배 자주 발급되므로 overhead가 그만큼 큽니다. tRFC는 density 의존이라 아래 수치는 *예시 가정*(tRFC≈350ns)입니다:

- DDR4 (tREFI=7.8μs): `350 / 7800` ≈ **4.5%**
- LPDDR5/DDR5 (tREFI=3.9μs): `350 / 3900` ≈ **9%**
- Extended temp에서 tREFI가 다시 절반으로 떨어지면 overhead는 더 커짐
- Refresh granularity가 fine할수록 (FGR) overhead 패턴이 달라짐

---

## 2. DDR4 의 Refresh — FGR 도입

> 출처: JESD79-4D §4.8, §4.9

### 2.1 Auto Refresh (REF 명령)

- All-bank refresh: 한 번의 REF가 *모든 bank의 한 row* refresh
- tREFI 마다 발급 권장 (또는 deferred 8 REF까지 허용)

### 2.2 Fine Granularity Refresh (FGR)

DDR4 신규 — *1x / 2x / 4x* mode 선택 (MR3):

| FGR Mode | tREFI | tRFC | 비고 |
|---|---|---|---|
| 1x | 7.8us | tRFC1 (긴) | 표준 |
| 2x | 3.9us | tRFC2 (짧음) | 더 자주, 각 REF는 더 짧음 |
| 4x | 1.95us | tRFC4 (더 짧음) | 매우 자주, latency 최적화 |

### 2.3 Temperature Controlled Refresh

- Normal temp (≤85°C): tREFI = 7.8us
- Extended temp (>85°C, ≤95°C): tREFI = 3.9us (절반)

DV 시사점: temperature mode 전환이 *MR4에 의해* 명시되어야 함. controller는 temperature sensor 입력에 따라 *동적으로* MR4 update.

---

## 3. DDR5 의 Refresh (비교) — Same-Bank Refresh + RFM의 등장

> 출처: JESD79-5C.01 v1.31 §3.5.6 (MR4), §3.5.59 (MR58), §3.5.60 (MR59)

LPDDR5와의 비교 축으로 서버/PC용 DDR5를 봅니다. DDR5는 *기본 Auto Refresh* + *Refresh Management (RFM)* 의 두 단계 구조입니다. refresh 입자 측면에서 **DDR5는 same-bank refresh(REFsb)** — REF 명령이 모든 bank group에서 *같은 번호의 bank*를 refresh하는 방식이 추가되어, LPDDR의 per-bank refresh와 DDR4의 all-bank refresh 사이의 중간 입자에 해당합니다. PASR는 DDR5에 없습니다(§10.6 deprecated).

### 3.1 RFM이란

**Refresh Management** — controller가 RAA(Rolling Accumulated ACT) counter를 추적해, 특정 row가 너무 자주 ACT 된 것이 누적되면 RFM 명령을 발급하여 그 row 주변의 위협받는 row를 refresh합니다. 기존 Auto Refresh가 "모든 row를 균등하게 주기적으로 refresh"하는 방식이라면, RFM은 "많이 접근되는 row 주변을 추가로 집중 refresh"하는 방식입니다. 일반 refresh만으로는 Rowhammer 위협을 막기 어렵다는 인식에서 DDR5에 표준으로 추가된 기능입니다.

```
RAA threshold (예: 800)
                                   ▲
RAA counter: ──────────────────────┤
                                   │
                                  발급
                                  ↓
controller: ACT ACT ACT ... ACT [RFM 명령] ACT ACT ...
                                  ▲
                                  RAA counter reset
```

### 3.2 RFM의 동기 — Rowhammer 대응

Rowhammer는 반도체 물리 특성에서 비롯된 취약점입니다. 어떤 row(aggressor)를 매우 빠른 주기로 반복 ACT하면, 그 row의 word-line 스위칭이 인접한 row(victim)의 cell capacitor에 전기적 간섭을 일으킵니다. 이 간섭이 충분히 누적되면 victim row의 일부 bit가 flip될 수 있습니다. 구체적으로는, aggressor word-line 이 반복적으로 올랐다 내릴 때 생기는 전계 변동과 기판 누설이 인접 victim cell 의 저장 전하를 조금씩 _빼앗는_ 방향으로 작용해, '1'(충전 상태)로 저장돼 있던 cell 이 충전을 잃고 '0' 으로 뒤집히는 식으로 나타납니다 — 즉 다음 refresh 가 와서 전하를 보충하기 전에 마진이 무너지는 것입니다. 단순 데이터 손상을 넘어 보안 공격 벡터로도 활용될 수 있다는 점에서 2014년 학계 논문 이후 메모리 업계가 심각하게 대응하기 시작했습니다.

DDR4 시절에는 TRR(Target Row Refresh)라는 이름으로 각 제조사가 자체적으로 대응했지만 표준화되지 않았습니다. DDR5에서 RFM으로 공식 표준화되면서, controller 측이 RAA counter를 추적하고 threshold 도달 시 RFM 명령을 발급하는 책임을 명확히 가지게 되었습니다.

### 3.3 RFM 관련 MR

- **MR58 (Refresh Management)**: RFM enable, threshold 설정
- **MR59 (DRFM, ARFM, RFM RAA Counter)**: RAA counter 동작 모드
- **MR60 (Partial Array Self Refresh)**: PASR 모드 — 일부 영역만 self refresh

### 3.4 RAA Counter 동작

RAA counter는 controller가 내부적으로 추적하는 누적 ACT 카운터입니다. ACT 명령이 발급될 때마다 counter가 증가하고, REF 명령이 발급될 때 counter가 감소합니다. _왜 ACT 는 올리고 REF 는 내리는가_ — RAA counter 가 측정하려는 것은 "아직 해소되지 않은 disturbance 의 양" 이기 때문입니다. ACT 는 Rowhammer 의 원인 그 자체입니다 — word-line 을 한 번 켤 때마다 인접 row 에 교란이 _쌓이므로_, ACT 마다 counter 를 올리면 누적된 교란량을 근사하게 됩니다. 반대로 REF 는 victim cell 들의 전하를 다시 채워 그동안 쌓인 교란을 _되돌려 놓는_ 동작이므로, REF 가 일어날 때 counter 를 내리면 "방금 해소된 교란만큼" 을 빼는 셈이 됩니다. 따라서 ACT(+)와 REF(−)의 차감 결과인 counter 값은 _아직 refresh 로 씻어내지 못한 순(net) disturbance_ 를 추정하는 지표가 되고, 이 값이 임계치를 넘으면 추가 refresh(RFM)로 따라잡아야 한다는 신호가 되는 것입니다. counter가 RAAIMT(Initial Management Threshold)에 도달하면 controller는 RFM 명령을 발급할 의무가 생깁니다. RFM 발급 후 counter는 부분적으로 감소합니다. 만약 controller가 RAAIMT 도달 후에도 RFM을 발급하지 않으면 counter가 계속 올라가 RAAMMT(Maximum Management Threshold)에 도달하는데, 이 시점이 되면 DRAM의 Rowhammer 보호가 더 이상 보장되지 않는 spec violation 상태가 됩니다.

---

## 4. LPDDR4 Refresh

> 출처: JESD209-4E §4.19

### 4.1 LPDDR4 의 두 가지 refresh

- **All-Bank Refresh**: REF 명령 → 모든 bank 동시 refresh
- **Per-Bank Refresh**: REFpb 명령 → 한 bank만 refresh (다른 bank는 동시에 사용 가능)

### 4.2 Refresh Management Command (LPDDR4 §4.47)

LPDDR4-E (revision E) 에서 *Refresh Management Command*가 추가되었습니다 — DDR5의 RFM과 유사 개념의 *조상*. controller가 추적한 hot row 정보에 따라 발급.

---

## 5. LPDDR5 Refresh (주축) — Per-Bank / PASR / ARFM / DRFM

> 출처: JESD209-5C §7.5, §7.7.5, §7.7.6

LPDDR5 refresh의 두 축은 **(1) per-bank refresh + PASR**(전력·부분배열 관리)와 **(2) ARFM/DRFM**(row-hammer 정밀 대응)입니다. 특히 PASR는 *LPDDR 계열 고유*로 DDR5에는 없으며(모바일 전력 관리 목적), LPDDR5 refresh의 정체성에 해당합니다. LPDDR5는 refresh management를 *더 정교하게* 분리합니다:

### 5.1 Optimized Refresh (§7.5.3)

기본 REF의 진화 — *전력 효율*과 *latency*를 모두 고려해 controller가 *적응적*으로 refresh 발급.

### 5.2 ARFM (Adaptive Refresh Management)

> JESD209-5C §7.7.6.1

DRAM이 *내부 monitor*로 *어떤 row*가 hot인지 추적하고, controller에게 *적응적*으로 refresh 필요성을 알림. controller는 ARFM 명령으로 응답.

### 5.3 DRFM (Directed Refresh Management)

> JESD209-5C §7.7.6.2

Controller가 *명시적*으로 *특정 row*를 refresh하라고 *지정*. 더 정밀한 control이지만, controller가 *정확한 위치*를 알아야 함.

### 5.4 ARFM vs DRFM 비교

| 항목 | ARFM (Adaptive) | DRFM (Directed) |
|---|---|---|
| 주체 | DRAM이 hint, controller가 발급 | Controller가 단독 결정 |
| 정밀도 | Coarse (영역 단위) | Fine (row 단위) |
| Overhead | 낮음 | 높음 (정확한 추적 필요) |
| Rowhammer 대응 | 일반적 | 정밀 |

### 5.5 PASR / PARC (Partial Array Self Refresh / Partial Array Refresh Control) — LPDDR 고유

> JESD209-5C §7.5.5, §7.5.6

**PASR는 LPDDR 계열 고유 기능으로 DDR5에는 존재하지 않습니다** (DDR5 MR60의 PASR는 v1.30부터 deprecated — §10.6 참조). 모바일 SoC는 사용 중인 메모리 영역이 작을 때가 많아, 쓰지 않는 영역의 refresh를 끄면 self-refresh 전력을 크게 줄일 수 있습니다 — 이것이 PASR의 동기이며 LPDDR refresh의 정체성입니다.

- **PASR**: Self Refresh 중 *일부 영역(segment/bank)만* refresh. 나머지는 *데이터 손실* 허용 — 메모리 사용량이 적을 때 전력 절약.
- **PARC**: PASR의 segment masking을 *fine-grained*로 제어.
- DV 함의: PASR enable 시 *masking된 영역*에 대한 read는 데이터 무결성이 보장되지 않으므로, scoreboard가 *active segment*만 비교하도록 PASR 설정을 추적해야 합니다.

### 5.6 Data Copy Low Power Function (§7.7.2) — 참고 (refresh 아님, 저전력 인코딩)

PASR가 *refresh* 전력을 줄인다면, **Data Copy**는 *전송(IO)* 전력을 줄이는 별도의 LPDDR5 고유 저전력 기능입니다(JESD209-5C §7.7.2, MR21). 8-Byte 데이터 안에서 같은 패턴이 반복되면 **reference data만 한 DQ link**(lower byte=DQ0, upper byte=DQ8)로 전송하여 IO/core 전력(IDD4W/R)을 절감합니다 — DBI와 유사한 결이며, **"행간 메모리 복사 엔진"이 아닙니다**. Write/Read 각각 MR21로 enable하고, Read Data Copy 활성 시 Read latency가 늘 수 있습니다.

- DV 함의: Data Copy enable 시 monitor/scoreboard는 DQ link의 reference-data 인코딩을 디코딩해 실제 데이터로 복원·비교해야 하며, Read Data Copy의 추가 latency를 timing 모델에 반영해야 합니다.

---

## 6. DV 적용 — Refresh Budget Checker

### 6.1 tREFI 위반 catch

```systemverilog
// REF 명령이 너무 늦게 발급되면 fail
// (deferred 8 REF까지 허용 — 단순 9 tREFI 이상 idle은 spec violation)
time last_ref_time;
int  deferred_ref_count;

always @(posedge clk) begin
    if (cmd == CMD_REF) begin
        time gap = $time - last_ref_time;
        if (gap > 9 * `TREFI_NS) begin
            `uvm_error("REFRESH_BUDGET",
                $sformatf("REF gap %0d ns > 9*tREFI (9 deferred limit)", gap))
        end
        last_ref_time = $time;
    end
end

// 추가: max deferred는 spec마다 다름 — DDR5는 더 늘어남 (확인 필요)
```

### 6.2 RFM 명령 coverage

```systemverilog
covergroup rfm_cg with function sample (
    int raa_counter_value,
    bit rfm_issued
);
    cp_raa: coverpoint raa_counter_value {
        bins below_half     = {[0 : 399]};
        bins approaching    = {[400 : 599]};
        bins near_threshold = {[600 : 799]};
        bins at_threshold   = {800};
        bins overflow_zone  = {[801 : $]};
    }
    cp_rfm: coverpoint rfm_issued {
        bins issued     = {1};
        bins not_issued = {0};
    }
    // RAA가 threshold에 있을 때 RFM이 발급되었는지 cross
    cx_threshold_rfm: cross cp_raa, cp_rfm {
        ignore_bins illegal = binsof(cp_raa.overflow_zone) &&
                              binsof(cp_rfm.not_issued);
        // RAA overflow 인데 RFM 발급 안 됨 = bug
    }
endgroup
```

### 6.3 Refresh budget overhead 측정

```systemverilog
class refresh_budget_monitor extends uvm_monitor;
    `uvm_component_utils(refresh_budget_monitor)

    int ref_count;
    real ref_time_total;  // ns
    real measurement_window;  // ns

    // analysis port from monitor
    uvm_analysis_imp #(ddr5_transaction, refresh_budget_monitor) imp;

    virtual function void write(ddr5_transaction t);
        if (t.cmd == CMD_REF) begin
            ref_count++;
            ref_time_total += `TRFC_NS;
        end
    endfunction

    virtual function void report_phase(uvm_phase phase);
        real overhead_pct = (ref_time_total / measurement_window) * 100.0;
        `uvm_info("REFRESH_BUDGET",
            $sformatf("Refresh count=%0d, overhead=%.2f%%", ref_count, overhead_pct),
            UVM_MEDIUM)
        if (overhead_pct > 10.0)
            `uvm_warning("REFRESH_BUDGET", "Overhead > 10% - investigate")
    endfunction
endclass
```

---

## 7. DV 적용 — Rowhammer 시나리오 stim

### 7.1 Rowhammer aggressor pattern

**stim**(stimulus, DUT를 흔들어 보려고 testbench가 만들어 인가하는 입력 자극)을 설계한다는 뜻입니다. Rowhammer 검증은 *aggressor row*(공격하듯 반복 접근하는 row)를 *매우 빠르게 반복 ACT* 하는 시퀀스를 만드는 것:

```systemverilog
class rowhammer_aggressor_seq extends uvm_sequence #(ddr5_transaction);
    `uvm_object_utils(rowhammer_aggressor_seq)

    rand bit [16:0] aggressor_row;
    rand bit [2:0]  aggressor_bg;
    rand bit [1:0]  aggressor_ba;
    rand int        hammer_count;
    constraint c_hammer { hammer_count inside {[10_000 : 100_000]}; }
        // ACT-PRE 반복 횟수

    virtual task body();
        ddr5_transaction t;
        for (int i = 0; i < hammer_count; i++) begin
            // ACT
            `uvm_do_with(t, {
                t.cmd      == CMD_ACT;
                t.bg       == aggressor_bg;
                t.ba       == aggressor_ba;
                t.row      == aggressor_row;
            })
            // PRE (immediate)
            `uvm_do_with(t, {
                t.cmd      == CMD_PRE;
                t.bg       == aggressor_bg;
                t.ba       == aggressor_ba;
            })
        end
        `uvm_info("ROWHAMMER",
            $sformatf("Hammered row 0x%x %0d times", aggressor_row, hammer_count),
            UVM_MEDIUM)
    endtask
endclass
```

### 7.2 검증 결과 확인

- **DUT가 RFM 명령을 발급하는가?** RAA threshold 도달 시 RFM이 *자동*으로 나와야 함
- **Victim row가 silently 변경되지 않는가?** scoreboard가 *aggressor 주변 row*도 *background traffic*으로 read하면서 data integrity 확인
- **timing이 spec 안에 있는가?** RFM 발급 시점이 *RAA threshold 도달 직후 일정 시간 안*

### 7.3 covergroup — Rowhammer 검증 시나리오

```systemverilog
covergroup rowhammer_cg with function sample (
    int hammer_count,
    bit rfm_observed
);
    cp_count: coverpoint hammer_count {
        bins light      = {[1_000 : 9_999]};
        bins medium     = {[10_000 : 49_999]};
        bins heavy      = {[50_000 : 99_999]};
        bins very_heavy = {[100_000 : $]};
    }
    cp_rfm: coverpoint rfm_observed {
        bins yes = {1};
        bins no  = {0};
    }
    cx_count_rfm: cross cp_count, cp_rfm;
endgroup
```

---

## 8. 대표 문제 — tREFI/tRFC overhead + 8 deferred REF dry-run

:::tip[Q1. tREFI=7.8us, tRFC=350ns 일 때 refresh가 차지하는 bandwidth 비율은? Extended temp (tREFI=3.9us, tRFC 동일) 에서는?]
:::
<details>
<summary>풀이</summary>


**Normal temp**
- Overhead = tRFC / tREFI = 350ns / 7800ns = **4.49%**
- 즉 1 second에 약 45ms가 refresh

**Extended temp**
- tREFI 절반: 3900ns
- Overhead = 350 / 3900 = **8.97%**
- 즉 약 9% — 거의 두 배

**DV 시사점**: temperature mode 전환 시 *bandwidth 가용량이 줄어듦*. 만약 SoC가 *최대 bandwidth* 가 필요한 상황이라면 *normal temp 유지를 위한 thermal 시뮬레이션*과 함께 검증.

</details>
:::tip[Q2. controller가 8 REF deferred (즉 다음 8 tREFI 동안 REF 안 발급) 후 burst REF (8회) 를 발급한다. 이 사이의 traffic을 어떻게 schedule해야 하나? deferred limit을 초과하면 어떻게 catch?]
:::
<details>
<summary>풀이 (deferred refresh dry-run)</summary>


**Step 1 — 이상적 burst refresh 스케줄**

| 시간 | 동작 | tREFI 카운트 |
|---|---|---|
| 0 | REF (가장 최근) | 1 |
| 7.8us | (REF 미발급, deferred=1) | 2 |
| 15.6us | (deferred=2) | 3 |
| ... | ... | ... |
| 62.4us | (deferred=8) | 9 |
| 62.4us+ε | REF 8회 burst (각 tRFC=350ns) | 9 |
| 62.4us + 8×350ns = 65.2us | burst 완료 | reset 카운트 |

**Step 2 — 위반 시나리오**

deferred=9 (즉 9 tREFI = 70.2us 동안 미발급) 후에 발급 → spec violation.

**Step 3 — checker 구현 (개념)**

```systemverilog
int deferred_ref;
time last_actual_ref_time;
time tREFI_ns = 7800;  // 7.8us

always @(posedge clk) begin
    // 매 tREFI 마다 *예상* REF가 발급되어야 함
    time elapsed = $time - last_actual_ref_time;
    int expected_count = elapsed / tREFI_ns;

    if (cmd == CMD_REF) begin
        deferred_ref = (deferred_ref + 1) - 1;  // 발급 1, 가상 expected 1 차감
        last_actual_ref_time = $time;
    end

    if (expected_count - actual_refs_in_window > 8)
        `uvm_error("REFRESH_BUDGET", "Deferred REF > 8 — spec violation")
end
```

**Step 4 — DV 적용 보완**

- SVA로 *deferred REF count > 8* 를 catch
- covergroup `refresh_pattern_cg` 에 *back-to-back burst REF* 시나리오 bin
- directed test `test_max_deferred_refresh` : 의도적으로 8 deferred 후 burst, *9 deferred*도 시도해 SVA fail 확인

</details>
---

## 9. 핵심 정리 (Key Takeaways)

- Refresh는 *cap leakage 보상* — destructive read의 ACT 동작을 *주기적으로* 모든 row에 적용.
- tREFI = REF **명령 평균 발급 간격** (LPDDR5/DDR5=3.9μs, DDR4=7.8μs). tRFC는 density 의존(단일 고정값 아님). overhead ≈ tRFC/tREFI ≈ 9% (LPDDR5/DDR5), 4.5% (DDR4).
- **Refresh 입자**: LPDDR5 = per-bank(REFpb) + **PASR**(LPDDR 고유, DDR5에 없음). DDR5 = same-bank(REFsb). DDR4 = all-bank. DDR4 *FGR* (Fine Granularity Refresh): 1x/2x/4x mode.
- DDR5 **RFM** (Refresh Management): RAA counter 추적, 임계치 도달 시 RFM 명령. Rowhammer 표준 대응.
- LPDDR5 **ARFM** (Adaptive) vs **DRFM** (Directed): adaptive는 DRAM hint 기반, directed는 controller 명시.
- **PASR / PARC**: self-refresh 시 일부만 refresh (전력 절약).
- DV 검증 핵심: refresh budget checker, RFM coverage, Rowhammer aggressor stim, RAA threshold cross coverage.

## 10. PDF 정밀 인용 — DDR5 §3.5.59 MR58, §3.5.60 MR59 (RFM)

> 출처: JESD79-5C.01 v1.31 §3.5.59~§3.5.61

### 10.1 MR58 (MA[7:0]=3AH) — Refresh Management 정밀 비트 매핑

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| RAAMMT[2:0] | ← | ← | RAAIMT[3:0] | ← | ← | ← | RFM Required |

| Function | Type | Operand | Data |
|---|---|---|---|
| **RFM Required** | R | OP[0] | `0B`: Refresh Management not required<br>`1B`: Refresh Management required |
| **RAAIMT** (Rolling Accumulated ACT Initial Management Threshold) | R | OP[4:1] | `0000B`-`0011B`: RFU<br>`0100B`: **32 (Normal), 16 (FGR)**<br>`0101B`: **40 (Normal), 20 (FGR)**<br>...<br>`1001B`: **72 (Normal), 36 (FGR)**<br>`1010B`: **80 (Normal), 40 (FGR)**<br>`1011B`-`1111B`: RFU |
| **RAAMMT** (Rolling Accumulated ACT Maximum Management Threshold) | R | OP[7:5] | `000B`-`010B`: RFU<br>`011B`: **3x (Normal), 6x (FGR)**<br>`100B`: **4x (Normal), 8x (FGR)**<br>`101B`: **5x (Normal), 10x (FGR)**<br>`110B`: **6x (Normal), 12x (FGR)**<br>`111B`: RFU |

> NOTE 1: Refresh Management settings are **vendor specific by the MR settings**.
> NOTE 2: Only applicable if **MR58 OP[0]=1** (Refresh Management Required).

핵심 정리:
- **RAAIMT (Initial Threshold)** = host가 *RFM 발급 의무* 가지는 ACT count 임계
- **RAAMMT (Maximum Threshold)** = RAAIMT의 *배수* — 이 값 도달 전 *반드시* RFM 발급 완료. multiplier `3x`~`6x` (Normal mode) 또는 `6x`~`12x` (FGR mode).
- **Normal vs FGR**: Fine Granularity Refresh mode에서는 *2배 더 작은 threshold* (refresh 자주 발생하므로).
- **Refresh Management Required = 0** (MR58 OP[0]=0): RFM 비활성. RFM 명령은 *REF처럼 동작*.
- **Refresh Management Required = 1**: RFM 명령이 *실제 RFM*으로 동작. CA9=H 필수 (Table 30 NOTE 23 참조).

### 10.2 MR59 (MA[7:0]=3BH) — DRFM, ARFM, RFM RAA Counter 정밀 매핑

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| RFM RAA Counter | ← | ARFM | ← | BRC Support Level | Bounded Refresh Configuration | ← | DRFE |

| Function | Type | Operand | Data |
|---|---|---|---|
| **DRFE** (DRFM Enable) | SR/W | OP[0] | Status Read (SR): `0B` = DRFM not implemented (Default), `1B` = DRFM implemented<br>Host Write (W): `0B` = DRFM disable (Default), `1B` = DRFM enable |
| **BRC** (Bounded Refresh Configuration) | R/W | OP[2:1] | `00B`: **BRC 2** (default)<br>`01B`: **BRC 3**<br>`10B`: **BRC 4**<br>`11B`: RFU |
| **BRC Support Level** | R | OP[3] | `0B`: **BRC2, 3, 4** (Default)<br>`1B`: **BRC2 Only** |
| **ARFM** (Adaptive RFM) | R/W | OP[5:4] | `00B`: **Default** — RAAIMT, RAAMMT, RAADEC<br>`01B`: **Level A** — RAAIMT-A, RAAMMT-A, RAADEC-A<br>`10B`: **Level B** — RAAIMT-B, RAAMMT-B, RAADEC-B<br>`11B`: **Level C** — RAAIMT-C, RAAMMT-C, RAADEC-C |
| **RAA Counter Decrement per REF Command** | R | OP[7:6] | `00B`: **RAAIMT** (full decrement)<br>`01B`: **RAAIMT * 0.5** (half decrement)<br>`10B`: RFU<br>`11B`: RFU |

> NOTE 1: Refresh Management settings are **vendor specific** by the MR settings.
> NOTE 2: Only applicable if **MR58 OP[0]=1**.
> NOTE 3: Only applicable if the **DRFM function is supported** (Status Read MR59:OP[0]=1).

### 10.3 핵심 개념 — RAA Counter 동작 의미

DRAM은 *내부적*으로 *각 row의 ACT count*를 추적합니다 (또는 group-level). 추적 단위:

- **RAA (Rolling Accumulated ACT)** counter: ACT 발생 시 *증가*, REF 발생 시 *감소*.
- **Decrement per REF**: MR59:OP[7:6] 설정. `00B`이면 REF 한 번에 *RAAIMT 만큼* counter 감소. `01B`이면 *절반만* 감소 (= RFM 발급 빈도 ↑).
- **RAAIMT 도달 시**: host가 *RFM 발급 의무*. 발급 안 하면 RAA 가 계속 증가해 *RAAMMT 도달 위험*.
- **RAAMMT 도달 시**: spec 위반 — DRAM의 *Rowhammer 보호 보장 X*. silicon에서 *bit flip 가능*.

### 10.4 ARFM (Adaptive RFM) — Level별 동작

ARFM은 *Refresh interval에 따라 threshold가 변경*되는 메커니즘:

| Level | 의미 |
|---|---|
| Default | 기본 RAAIMT/RAAMMT/RAADEC |
| Level A | 조금 더 strict (RAAIMT-A 등) |
| Level B | 더 strict |
| Level C | 가장 strict |

→ Workload가 *Rowhammer-prone* (지속적인 reactivation) 하면 Level B/C로 *상향*. 메모리 controller가 *런타임에 ARFM level 변경* 가능.

### 10.5 DRFM (Directed RFM) — 명시적 row 지정

DRFM enabled (MR59:OP[0]=1) 시:
- Controller가 *target row 주소*를 *DRFM 명령*에 인코딩
- DRAM이 *지정된 row 주변*만 refresh (전체 RFM보다 정밀)

Table 30 (Command Truth Table)의 REFsb/RFMsb 행에서 *CA5*의 "CID3 or DRFM=L" 표기 확인 — DRFM enabled 시 CID3 자리가 *DRFM target 주소*로 활용.

### 10.6 MR60 (PASR) — DEPRECATED 알림

> §3.5.61 원문 인용:
> "**PASR has been deprecated starting with spec working revision 1.90, JESD79-5C-v1.30**. All MR60 bits will behave as RFU on devices that do not support PASR."

→ DDR5 의 PASR는 *공식적으로 deprecated*. 기존 DDR4/LPDDR4 의 PASR과 다름. DV는 *PASR 시나리오 검증*을 *legacy device*에만 적용.

> 본 학습 자료의 §5.5 PASR (이 챕터 위쪽) 는 *LPDDR5의 PASR/PARC* 기준이며 *DDR5에서는 deprecated*임에 유의.

### 10.7 DV 적용 — MR58/MR59 정밀 RAL + RFM coverage

```systemverilog
// 출처: JESD79-5C.01 §3.5.59 MR58, §3.5.60 MR59
class ddr5_reg_MR58 extends uvm_reg;
    `uvm_object_utils(ddr5_reg_MR58)
    rand uvm_reg_field rfm_required;   // OP[0]
    rand uvm_reg_field raaimt;          // OP[4:1]
    rand uvm_reg_field raammt;          // OP[7:5]

    function new(string name = "ddr5_reg_MR58");
        super.new(name, 8, UVM_NO_COVERAGE);
    endfunction
    virtual function void build();
        rfm_required = uvm_reg_field::type_id::create("rfm_required");
        rfm_required.configure(this, 1, 0, "RO", 0, 1'b0, 1, 1, 0);

        raaimt = uvm_reg_field::type_id::create("raaimt");
        raaimt.configure(this, 4, 1, "RO", 0, 4'b0000, 1, 1, 0);

        raammt = uvm_reg_field::type_id::create("raammt");
        raammt.configure(this, 3, 5, "RO", 0, 3'b000, 1, 1, 0);
    endfunction
endclass

class ddr5_reg_MR59 extends uvm_reg;
    `uvm_object_utils(ddr5_reg_MR59)
    rand uvm_reg_field drfe;             // OP[0]
    rand uvm_reg_field brc;               // OP[2:1]
    rand uvm_reg_field brc_support;       // OP[3]
    rand uvm_reg_field arfm;              // OP[5:4]
    rand uvm_reg_field raa_decrement;     // OP[7:6]

    function new(string name = "ddr5_reg_MR59");
        super.new(name, 8, UVM_NO_COVERAGE);
    endfunction
    virtual function void build();
        drfe = uvm_reg_field::type_id::create("drfe");
        drfe.configure(this, 1, 0, "RW", 0, 1'b0, 1, 1, 0);

        brc = uvm_reg_field::type_id::create("brc");
        brc.configure(this, 2, 1, "RW", 0, 2'b00, 1, 1, 0);

        brc_support = uvm_reg_field::type_id::create("brc_support");
        brc_support.configure(this, 1, 3, "RO", 0, 1'b0, 1, 1, 0);

        arfm = uvm_reg_field::type_id::create("arfm");
        arfm.configure(this, 2, 4, "RW", 0, 2'b00, 1, 1, 0);

        raa_decrement = uvm_reg_field::type_id::create("raa_decrement");
        raa_decrement.configure(this, 2, 6, "RO", 0, 2'b00, 1, 1, 0);
    endfunction
endclass

// Coverage — RFM/ARFM/DRFM 모든 조합
covergroup mr58_mr59_cg with function sample (
    bit         rfm_req,
    bit [3:0]   raaimt,
    bit [2:0]   raammt,
    bit         drfe,
    bit [1:0]   arfm
);
    cp_rfm_req: coverpoint rfm_req;
    cp_raaimt: coverpoint raaimt {
        bins valid[] = {[4'b0100 : 4'b1010]};   // 0100B~1010B (defined)
        bins rfu     = default;
    }
    cp_raammt: coverpoint raammt {
        bins valid[] = {[3'b011 : 3'b110]};      // 011B~110B (defined)
        bins rfu     = default;
    }
    cp_drfe: coverpoint drfe;
    cp_arfm: coverpoint arfm {
        bins default_level = {2'b00};
        bins level_a       = {2'b01};
        bins level_b       = {2'b10};
        bins level_c       = {2'b11};
    }
    cx_rfm_drfm: cross cp_rfm_req, cp_drfe;
    cx_arfm_drfe: cross cp_arfm, cp_drfe;
    cx_threshold: cross cp_raaimt, cp_raammt;
endgroup
```

### 10.8 RAAIMT 수치적 의미 — 검증 예시

예: `RAAIMT = 0100B` → 32 (Normal mode), 16 (FGR mode)

- *Normal mode (1x refresh)*: ACT 32회 발생할 때마다 RFM 발급 필요
- *FGR mode (2x/4x refresh)*: ACT 16회 (절반)마다 RFM 발급 필요 — refresh가 더 자주 일어나니까 threshold도 비례 축소

_왜 FGR 에서 threshold 가 절반이 되는가_ 를 인과로 풀면 이렇습니다. Rowhammer 방어의 핵심은 "victim 이 망가지기 전에 refresh 가 와서 전하를 채워 준다" 는 것인데, 이때 위험을 가르는 기준은 _하나의 refresh 주기 안에 한 row 가 몇 번 ACT(=hammer) 되었는가_ 입니다. FGR(2x) 는 refresh 를 두 배 자주 발급하므로 한 refresh 주기(refresh 와 refresh 사이의 시간 창)가 _절반_ 으로 짧아집니다. 같은 트래픽이라도 더 짧아진 그 창 안에서는 aggressor 가 ACT 할 수 있는 횟수가 비례해서 줄어듭니다 — 즉 한 주기당 허용 가능한 안전 ACT 한도가 절반이 됩니다. RAA 임계치(RAAIMT)는 이 "한 refresh 주기당 안전 ACT 한도" 를 반영하는 값이므로, refresh 주기가 절반이 되면 임계치도 절반으로 낮춰야 같은 안전 마진이 유지됩니다. 그래서 FGR mode 의 threshold 가 Normal 의 절반으로 정의되는 것입니다.

만약 `RAAMMT = 100B` (4x)이면 *RAAIMT의 4배* (32 × 4 = 128) 가 max threshold. host는 *RAA가 128에 도달하기 전*에 RFM 발급 완료.

### 10.9 DV 시나리오 — Adaptive RFM Level 전환

```systemverilog
// ARFM Level 전환 시퀀스 — 다양한 traffic 부하에 따른 controller 적응 검증
class ddr5_arfm_level_switch_seq extends uvm_sequence;
    `uvm_object_utils(ddr5_arfm_level_switch_seq)

    virtual task body();
        // 1. Default level로 일반 traffic
        run_traffic_with_arfm(2'b00, /*duration*/1000);

        // 2. Level A로 변경 — heavy reactivation
        do_mr59_write(.arfm(2'b01));
        run_heavy_reactivation_traffic(2000);

        // 3. Level C로 변경 — 가장 strict
        do_mr59_write(.arfm(2'b11));
        run_traffic_with_arfm(2'b11, 2000);

        // 4. Default 복귀
        do_mr59_write(.arfm(2'b00));
        run_traffic_with_arfm(2'b00, 1000);
    endtask
endclass
```

## 11. 핵심 정리 (Key Takeaways)

- Refresh는 *cap leakage 보상* — destructive read의 ACT 동작을 *주기적으로* 모든 row에 적용.
- tREFI = REF **명령 평균 발급 간격** (LPDDR5/DDR5=3.9μs, DDR4=7.8μs). tRFC는 density 의존(단일 고정값 아님). overhead ≈ tRFC/tREFI ≈ 9% (LPDDR5/DDR5), 4.5% (DDR4).
- **Refresh 입자**: LPDDR5 = per-bank(REFpb) + **PASR**(LPDDR 고유, DDR5에 없음). DDR5 = same-bank(REFsb). DDR4 = all-bank. DDR4 *FGR* (Fine Granularity Refresh): 1x/2x/4x mode.
- DDR5 **RFM** (Refresh Management): RAA counter 추적, 임계치 도달 시 RFM 명령. Rowhammer 표준 대응.
- **MR58 정밀**: OP[0] = RFM Required, OP[4:1] = RAAIMT (32~80 Normal / 16~40 FGR), OP[7:5] = RAAMMT multiplier (3x~6x Normal / 6x~12x FGR).
- **MR59 정밀**: OP[0] = DRFE (DRFM Enable, SR/W), OP[2:1] = BRC (Bounded Refresh Config), OP[5:4] = ARFM Level (Default/A/B/C), OP[7:6] = RAA Decrement (full / half).
- **PASR (MR60)**: DDR5에서 **deprecated** since v1.30. LPDDR5의 PASR/PARC만 유효.
- LPDDR5 **ARFM** (Adaptive) vs **DRFM** (Directed): adaptive는 DRAM hint 기반, directed는 controller 명시.
- DV 검증 핵심: refresh budget checker, RFM coverage, Rowhammer aggressor stim, RAA threshold cross coverage + **MR58/MR59 모든 ARFM level 시나리오**.

## 12. Further Reading

- 이전: [Ch06. Timing·Preamble](../06_timing_preamble/)
- 다음: [Ch08. Training](../08_training/)
- 부록 C: [SVA / Coverage 예제 모음](../appendix_c_sva_coverage_examples/)
- 퀴즈: [Ch07 퀴즈](../quiz/ch07_quiz/)
- 외부 자료:
    - Kim et al., "Flipping Bits in Memory Without Accessing Them: An Experimental Study of DRAM Disturbance Errors", ISCA 2014 — Rowhammer 최초 논문
    - JEDEC RFM technical brief (공개 자료)

