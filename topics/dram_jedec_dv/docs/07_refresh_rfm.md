# Ch07. Refresh·tREFI/tRFC·Refresh Management (RFM)

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="./"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">CH 07</span>
</div>

## 🎯 Learning Objectives

- **Explain**: Refresh가 필요한 물리적 이유(cap leakage)와 destructive read의 관계를 설명한다.
- **Calculate**: tREFI=7.8us, tRFC=350ns 일 때 refresh가 차지하는 bandwidth overhead를 계산한다.
- **Distinguish**: DDR5 RFM, LPDDR5 ARFM, LPDDR5 DRFM의 차이를 구별한다.
- **Design**: Rowhammer 시나리오 stim sequence와 RFM coverage를 설계한다.

## Prerequisites

- [Ch06. Timing·Preamble·Postamble](06_timing_preamble.md)
- DRAM cell 동작 (Ch01 §2)

## 1. Refresh의 본질 — 왜 필요한가

DRAM cell의 capacitor는 *시간이 지나면 charge가 leak*. 일정 시간(예: 64ms) 안에 *모든 row를 한 번씩 ACT-PRE* 해주지 않으면 데이터가 손실됩니다.

이 *주기적 ACT-PRE*가 **Refresh**입니다. DRAM controller가 명령(REF)을 발급하면 DRAM 내부에서 *자동으로 next row를 refresh*. controller는 *몇 번째 row*인지 알 필요 없습니다 (internal counter).

### 1.1 핵심 timing — tREFI / tRFC

- **tREFI** (Refresh Interval): 평균 REF 명령 간격 (일반 7.8us @ normal temp)
- **tRFC** (Refresh Cycle): REF → 다음 명령 가능까지 (예: 350ns)

```
시간:    0 ─────── 7.8us ─────── 15.6us ─────── 23.4us
명령:    REF        REF           REF            REF
        ▲          ▲             ▲              ▲
        │←─tRFC──→│ idle/traffic │
        350ns      7.45us
```

### 1.2 Refresh Bandwidth Overhead

Refresh가 차지하는 시간 비율 = `tRFC / tREFI` = `350ns / 7800ns` ≈ **4.5%**

- Normal temp: ~4.5%
- Extended temp (95°C, tREFI 절반=3.9us): ~9%
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

## 3. DDR5 의 Refresh — RFM의 등장

> 출처: JESD79-5C.01 v1.31 §3.5.6 (MR4), §3.5.59 (MR58), §3.5.60 (MR59)

DDR5는 *기본 Auto Refresh* + *Refresh Management (RFM)* 의 두 단계 구조입니다.

### 3.1 RFM이란

**Refresh Management** — controller가 *RAA (Rolling Accumulated ACT) counter* 를 추적해 *특정 row가 너무 자주 ACT 되었을 때*  *RFM 명령*을 발급하여 그 row 주변의 *위협받는 row*를 refresh 합니다.

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

**Rowhammer**: 어떤 row(*aggressor*)를 *매우 빠른 주기로 반복 ACT* 하면, *인접한 row(victim)*의 cell capacitor가 *지속적인 전기적 결합*으로 *bit flip*. 보안 공격 벡터 가능.

DDR4 시절에는 *target row refresh (TRR)* 가 제조사 단위로 구현되었지만 표준화되지 않았음. DDR5에서 *RFM*으로 표준화.

### 3.3 RFM 관련 MR

- **MR58 (Refresh Management)**: RFM enable, threshold 설정
- **MR59 (DRFM, ARFM, RFM RAA Counter)**: RAA counter 동작 모드
- **MR60 (Partial Array Self Refresh)**: PASR 모드 — 일부 영역만 self refresh

### 3.4 RAA Counter 동작

- 각 ACT가 RAA counter 증가
- counter가 threshold 도달 → controller가 RFM 명령 발급
- RFM 발급 후 counter 일부 감소
- counter overflow 방지를 위해 *RAA Maximum* 도 정의됨

---

## 4. LPDDR4 Refresh

> 출처: JESD209-4E §4.19

### 4.1 LPDDR4 의 두 가지 refresh

- **All-Bank Refresh**: REF 명령 → 모든 bank 동시 refresh
- **Per-Bank Refresh**: REFpb 명령 → 한 bank만 refresh (다른 bank는 동시에 사용 가능)

### 4.2 Refresh Management Command (LPDDR4 §4.47)

LPDDR4-E (revision E) 에서 *Refresh Management Command*가 추가되었습니다 — DDR5의 RFM과 유사 개념의 *조상*. controller가 추적한 hot row 정보에 따라 발급.

---

## 5. LPDDR5 Refresh — ARFM / DRFM / Optimized Refresh

> 출처: JESD209-5C §7.5, §7.7.5, §7.7.6

LPDDR5는 refresh management를 *더 정교하게* 분리:

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

### 5.5 PASR / PARC (Partial Array Self Refresh / Partial Array Refresh Control)

> JESD209-5C §7.5.5, §7.5.6

- **PASR**: Self Refresh 중 *일부 영역만* refresh. 나머지는 *데이터 손실* 허용 — 메모리 사용량이 적을 때 전력 절약.
- **PARC**: PASR의 segment masking을 *fine-grained*로 제어.

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

Rowhammer 검증은 *aggressor row*를 *매우 빠르게 반복 ACT* 하는 시퀀스를 만드는 것:

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

!!! question "Q1. tREFI=7.8us, tRFC=350ns 일 때 refresh가 차지하는 bandwidth 비율은? Extended temp (tREFI=3.9us, tRFC 동일) 에서는?"

???+ answer "풀이"

    **Normal temp**
    - Overhead = tRFC / tREFI = 350ns / 7800ns = **4.49%**
    - 즉 1 second에 약 45ms가 refresh

    **Extended temp**
    - tREFI 절반: 3900ns
    - Overhead = 350 / 3900 = **8.97%**
    - 즉 약 9% — 거의 두 배

    **DV 시사점**: temperature mode 전환 시 *bandwidth 가용량이 줄어듦*. 만약 SoC가 *최대 bandwidth* 가 필요한 상황이라면 *normal temp 유지를 위한 thermal 시뮬레이션*과 함께 검증.

!!! question "Q2. controller가 8 REF deferred (즉 다음 8 tREFI 동안 REF 안 발급) 후 burst REF (8회) 를 발급한다. 이 사이의 traffic을 어떻게 schedule해야 하나? deferred limit을 초과하면 어떻게 catch?"

???+ answer "풀이 (deferred refresh dry-run)"

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

---

## 9. 핵심 정리 (Key Takeaways)

- Refresh는 *cap leakage 보상* — destructive read의 ACT 동작을 *주기적으로* 모든 row에 적용.
- tREFI / tRFC 가 핵심 timing — overhead ≈ tRFC/tREFI ≈ 4.5% (normal), 9% (extended temp).
- DDR4 *FGR* (Fine Granularity Refresh): 1x/2x/4x mode.
- DDR5 **RFM** (Refresh Management): RAA counter 추적, 임계치 도달 시 RFM 명령. Rowhammer 표준 대응.
- LPDDR5 **ARFM** (Adaptive) vs **DRFM** (Directed): adaptive는 DRAM hint 기반, directed는 controller 명시.
- **PASR / PARC**: self-refresh 시 일부만 refresh (전력 절약).
- DV 검증 핵심: refresh budget checker, RFM coverage, Rowhammer aggressor stim, RAA threshold cross coverage.

## 10. Further Reading

- 이전: [Ch06. Timing·Preamble](06_timing_preamble.md)
- 다음: [Ch08. Training](08_training.md)
- 부록 C: [SVA / Coverage 예제 모음](appendix_c_sva_coverage_examples.md)
- 퀴즈: [Ch07 퀴즈](quiz/ch07_quiz.md)
- 외부 자료:
    - Kim et al., "Flipping Bits in Memory Without Accessing Them: An Experimental Study of DRAM Disturbance Errors", ISCA 2014 — Rowhammer 최초 논문
    - JEDEC RFM technical brief (공개 자료)

<div class="chapter-nav">
  <a class="nav-prev" href="06_timing_preamble/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch06. Timing·Preamble</div>
  </a>
  <a class="nav-next" href="08_training/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch08. Training</div>
  </a>
</div>
