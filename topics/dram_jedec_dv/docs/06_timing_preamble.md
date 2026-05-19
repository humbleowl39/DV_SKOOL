# Ch06. Timing 파라미터·Preamble·Postamble

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">CH 06</span>
</div>

## 🎯 Learning Objectives

- **Recall**: 핵심 DRAM timing 파라미터 (tRCD, tRP, tRAS, tRC, tCCD_L/S, tFAW, tWTR, tRTP, tRFC) 의 의미를 회상한다.
- **Calculate**: ACT→RD 시퀀스의 cycle 수를 timing 파라미터로부터 계산한다.
- **Differentiate**: Read preamble과 Write preamble의 역할 차이를 구별한다.
- **Construct**: tRCD / tRP / tFAW 위반을 catch하는 SVA를 구성한다.

## Prerequisites

- [Ch05. Command·Truth Table·Burst](05_commands_burst.md)
- 동기식 회로의 setup/hold, clock cycle 개념

## 1. 왜 timing 파라미터가 DV의 절반인가

DRAM 검증의 *절반은 protocol*, *나머지 절반은 timing*입니다. Protocol은 *명령의 의미*를 검증하고, timing은 *명령이 *언제* 발급될 수 있는지*를 검증합니다.

상용 메모리 controller IP에서 발견되는 *대부분의 silicon bug*는 timing corner — 특히 *speed bin 경계*나 *back-to-back 명령의 latency* 에서 발생합니다. DV의 timing checker가 *느슨하면* (예: `tRCD-1` 도 통과시키면) silicon에서 *간헐적 fail*이 발생합니다.

---

## 2. 핵심 Timing 파라미터 — 9가지

### 2.1 Intra-bank (같은 bank 안에서)

| 파라미터 | 의미 | 단위 |
|---|---|---|
| `tRCD` | ACT → RD/WR 가능 시점 (Row-to-Column Delay) | nCK |
| `tRP` | PRE → 다음 ACT 가능 시점 (Row Precharge) | nCK |
| `tRAS` | ACT → 같은 bank PRE 까지 최소 active 시간 | nCK |
| `tRC` | ACT → 같은 bank 의 다음 ACT (= tRAS + tRP) | nCK |
| `tWR` | Write 종료 → PRE 가능 시점 (Write Recovery) | nCK |
| `tRTP` | RD 종료 → PRE 가능 시점 (Read to Precharge) | nCK |

### 2.2 Inter-bank (다른 bank 간)

| 파라미터 | 의미 |
|---|---|
| `tRRD_S` | ACT → 다른 BG의 ACT (Short) |
| `tRRD_L` | ACT → 같은 BG 다른 bank의 ACT (Long) |
| `tFAW` | 4 ACT in 같은 rank 의 시간 윈도우 (Four Activate Window) |
| `tCCD_S` | CAS → CAS 다른 BG (Short) |
| `tCCD_L` | CAS → CAS 같은 BG (Long) |
| `tCCD_L_WR` | Write 의 tCCD_L (DDR5+) |
| `tCCD_L_WR2` | Write→Write 의 별도 tCCD_L (DDR5+) |
| `tWTR_S` / `tWTR_L` | Write→Read transition (Short / Long) |

### 2.3 Refresh

| 파라미터 | 의미 |
|---|---|
| `tREFI` | Refresh 평균 간격 (보통 7.8us @ normal temp) |
| `tRFC` | REF → 다음 명령 가능 시점 (Refresh Completion) |

(Refresh 상세는 [Ch07](07_refresh_rfm.md))

### 2.4 핵심 의미를 한 그림으로

```
                            ┌──── tRC ────────────────────┐
              ┌── tRAS ──┐       │
              ▼          │       ▼
  ──ACT──────RD/WR───────PRE────────ACT──────  (같은 bank)
  ▲   │       ▲   │       ▲
  └tRCD┘      └tRTP┘     └tRP┘
              또는 tWR (WR 후 PRE)

  ──ACT──────tRRD_L───ACT── (같은 BG 다른 bank)
  ──ACT──────tRRD_S───ACT── (다른 BG)

  4 ACT in tFAW window
```

---

## 3. DDR5 의 timing 변화 — 무엇이 달라졌나

> 출처: JESD79-5C.01 v1.31 §3.5 (MR), §4 (Command operation)

### 3.1 DDR4 vs DDR5 — 동일 절대 시간, 다른 nCK 수

DDR5는 tCK가 *짧으므로* (예: 8400 MT/s → tCK ≈ 0.238ns), 같은 *절대* 시간이라도 *nCK 수*는 더 큼:

| 파라미터 | DDR4-3200 (tCK=0.625ns) | DDR5-6400 (tCK=0.3125ns) |
|---|---|---|
| `tRCD` | ~14 nCK (8.75ns) | ~28 nCK (8.75ns) |
| `tRP` | ~14 nCK | ~28 nCK |
| `tCCD_L` | 6 nCK | 8~10 nCK |

> 위 값은 *예시 보간*입니다 (추론). 정확한 값은 speed bin과 product datasheet에 따라 다릅니다.

### 3.2 DDR5 신규 timing — tCCD_L_WR2 등

DDR5는 *Write 연속*에 더 세밀한 timing이 추가되었습니다:

- `tCCD_L_WR` — same-BG Write→Write
- `tCCD_L_WR2` — *조건부* tCCD_L_WR (DDR5의 speed/feature에 따라)

이런 *세밀한 분리*는 DV scoreboard/checker가 *모든 조건*을 일일이 분기해야 함을 의미합니다.

---

## 4. Preamble / Postamble

### 4.1 Read Preamble — host의 DQS 인식

DRAM이 RD 응답을 보낼 때, DQS_t/c는 burst 시작 전에 *정해진 패턴*을 보여줍니다. host receiver가 이 패턴을 보고 *sampling timing*을 잡습니다.

> 출처: JESD79-5C.01 §4.4.1

```
        Read Preamble (예: 2 tCK)        Burst (BL16)         Postamble
        ┌────────────┐                ┌──────────────────┐    ┌──┐
DQS_t   _0─1─0───────|────────────────|D D D D D D D D...|────|──|
                       ▲
                   sampling
                   start
```

- **DDR4 Read Preamble**: 1 tCK 또는 2 tCK (MR4)
- **DDR5 Read Preamble**: 2 tCK 또는 3 tCK (MR8) — *더 길어짐* (high-speed signaling 보상)

### 4.2 Write Preamble — host가 DRAM에 전송

host가 WR 시 DQS를 *burst 전에 정해진 패턴*으로 토글합니다. DRAM receiver가 이를 보고 *DQ sample timing*을 잡음.

| | DDR4 | DDR5 |
|---|---|---|
| Read Preamble (tCK) | 1 또는 2 | **2 또는 3** |
| Write Preamble (tCK) | 1 | **2 또는 3** |

### 4.3 Postamble — burst 마감

Read postamble: DRAM이 burst 종료 후 DQS_t/c를 *Hi-Z* 로 풀어주기 전에 *마지막 toggle* 패턴 1 tCK.

핵심 timing:
- `tWPRE` (Write Preamble) — host가 보장
- `tWPST` (Write Postamble) — host가 보장
- `tRPRE` (Read Preamble) — DRAM이 보장
- `tRPST` (Read Postamble) — DRAM이 보장

### 4.4 DV 함의 — Preamble pattern 검증

monitor가 *preamble 패턴 자체*를 검증해야 함:

```systemverilog
// Read preamble 패턴 검증 (예: 2 tCK preamble = "0 1 0 1")
property p_read_preamble_pattern_2tck;
    @(posedge clk)
    rd_burst_about_to_start |=>
        (dqs_t == 1'b0) ##1 (dqs_t == 1'b1) ##1 (dqs_t == 1'b0) ##1 (dqs_t == 1'b1);
endproperty
a_read_preamble: assert property (p_read_preamble_pattern_2tck);
```

> 위는 *개념 예시*. 실제 sample timing은 DQS_t/c의 *edge*를 보고, half-tCK 단위 sampling이 필요합니다.

---

## 5. DV 적용 — Timing Checker SVA

### 5.1 tRCD 위반 catch

```systemverilog
// 같은 bank에서 ACT → RD 사이에 최소 tRCD 클럭이 있어야 함
// 출처: JESD79-5C.01 §3.1 + speed bin table
property p_trcd;
    @(posedge clk) disable iff (!reset_n)
    (cmd == CMD_ACT) |->
        ##[`TRCD_NCK : $]
        first_match(cmd inside {CMD_RD, CMD_WR, CMD_RDA, CMD_WRA} &&
                    (bank == $past(bank)) &&
                    (bg   == $past(bg)));
endproperty
a_trcd: assert property (p_trcd)
    else `uvm_error("ASSERT_TIMING", "tRCD violation: RD/WR too soon after ACT")
```

### 5.2 tFAW 위반 catch — sliding window

```systemverilog
// 4 ACT 명령이 tFAW 윈도우 안에 들어가지 않아야 함 (모든 bank에 대해)
int act_count_window;
time act_timestamps[$];

always @(posedge clk) begin
    if (cmd == CMD_ACT) begin
        // 윈도우 밖 timestamp 제거
        while (act_timestamps.size() > 0 &&
               ($time - act_timestamps[0]) > `TFAW_NS)
            act_timestamps.delete(0);

        act_timestamps.push_back($time);

        if (act_timestamps.size() > 4)
            `uvm_error("ASSERT_TIMING",
                $sformatf("tFAW violation: 5+ ACTs in %0d ns window", `TFAW_NS))
    end
end
```

### 5.3 tCCD_L 위반 catch (same-BG)

```systemverilog
property p_tccd_l_same_bg;
    @(posedge clk)
    (cmd inside {CMD_RD, CMD_WR} && bg_q == bg_p) |->
        ##[`TCCD_L_NCK : $]
        (cmd inside {CMD_RD, CMD_WR});
endproperty
a_tccd_l: assert property (p_tccd_l_same_bg);
```

---

## 6. DV 적용 — Timing Coverage

### 6.1 Corner timing coverage

```systemverilog
covergroup timing_corner_cg with function sample (int gap_cycles, string param_name);
    cp_param: coverpoint param_name {
        bins trcd  = {"tRCD"};
        bins trp   = {"tRP"};
        bins trrd_l = {"tRRD_L"};
        bins trrd_s = {"tRRD_S"};
        bins tccd_l = {"tCCD_L"};
        bins tccd_s = {"tCCD_S"};
    }
    cp_gap: coverpoint gap_cycles {
        bins min_spec = {[1:5]};         // 최소 spec 근접
        bins normal   = {[6:30]};        // 일반 동작
        bins long_idle = {[31:1000]};    // 긴 idle
    }
    cx_param_gap: cross cp_param, cp_gap;
endgroup
```

### 6.2 Preamble length coverage

```systemverilog
covergroup preamble_cg with function sample (int read_preamble_tck, int write_preamble_tck);
    cp_rd_pre: coverpoint read_preamble_tck {
        bins p2 = {2};
        bins p3 = {3};
    }
    cp_wr_pre: coverpoint write_preamble_tck {
        bins p2 = {2};
        bins p3 = {3};
    }
    cx_pre: cross cp_rd_pre, cp_wr_pre;
endgroup
```

---

## 7. 대표 문제 — ACT → RD timing dry-run

!!! question "Q. DDR5-6400, tCK=0.3125ns, tRCD=28 nCK, CL=46 nCK, BL=16. ACT 명령이 cycle 0에 발급되면, 첫 데이터 비트가 DQ에 나타나는 시점은 몇 ns? RD가 발급되는 가장 빠른 cycle은? 같은 시퀀스를 DDR4-3200 (tCK=0.625ns, tRCD=14 nCK, CL=22 nCK, BL=8) 으로 대조."

???+ answer "풀이 (cycle-by-cycle 계산)"

    **DDR5-6400 계산**

    DDR5의 명령은 2-cycle. 위 문제에서는 *cycle 0에 ACT 발급* 이라 했으므로 cycle 0~1 동안 ACT 전송. cycle 2부터 internal로 row activation 시작 *(추론 — 명령 실행 시점 기준)*.

    가장 빠른 RD 시점은 *tRCD가 만료된 직후*:
    - tRCD = 28 nCK 부터 RD 가능
    - DDR5 RD도 2-cycle 명령이므로 cycle 28~29에 RD 명령 전송 *(가장 빠른 케이스)*

    데이터 도착:
    - RD 명령 완료(cycle 29) + CL=46 nCK = cycle 29 + 46 = cycle 75 부터
    - cycle 75에서 첫 burst beat
    - 절대 시간 = 75 × 0.3125ns = **23.4375 ns**
    - BL16 → 16 beats × 0.15625ns (half tCK) = 2.5ns burst duration
    - Burst 종료: 23.4375 + 2.5 = **25.9375ns**

    **DDR4-3200 대조**

    DDR4 명령은 1-cycle.
    - cycle 0: ACT 발급
    - tRCD = 14 nCK → cycle 14 부터 RD 가능
    - RD 명령 (cycle 14, 1-cycle) + CL=22 nCK
    - 첫 데이터 = cycle 14 + 22 = cycle 36
    - 절대 시간 = 36 × 0.625ns = **22.5 ns**
    - BL8 → 8 beats × 0.3125ns (half tCK) = 2.5ns burst duration
    - Burst 종료: 22.5 + 2.5 = **25 ns**

    **비교 표**

    | | DDR5-6400 | DDR4-3200 |
    |---|---|---|
    | 첫 비트 도착 시간 | 23.44ns | 22.5ns |
    | Burst 종료 | 25.94ns | 25.0ns |
    | Throughput per burst | 16B (×8) = 16B | 8B (×8) = 8B |
    | Per-byte time | 1.625ns/B | 3.125ns/B |

    → DDR5가 *총 시간*은 비슷하지만 *2배의 데이터*를 전송. 이것이 DDR5의 의의.

    **DV 함의**

    1. SVA `tRCD` 위반 catch: cycle 28 이전의 RD는 fail이어야 함
    2. covergroup `timing_corner_cg.cx_param_gap[tRCD][min_spec]` 가 hit되도록 directed test 작성
    3. Scoreboard는 *데이터 도착 시점*을 monitor와 동기화 — *expected_data_cycle = ACT_cycle + tRCD + CL* 계산
    4. Burst 종료 후 *postamble* 가 *적절히* 마감되는지 monitor가 확인

---

## 8. 핵심 정리 (Key Takeaways)

- 핵심 timing 9개를 외워야 함: tRCD/tRP/tRAS/tRC/tWR/tRTP/tRRD_L/S/tFAW/tCCD_L/S.
- DDR5는 *tCK가 짧으므로* 동일 절대 시간에 *더 많은 nCK*. `tCCD_L_WR2` 같은 세분화 timing 추가.
- Preamble은 *DDR5에서 더 길어짐* (2~3 tCK) — high-speed signaling 보상.
- SVA로 *모든* major timing 위반을 catch — tRCD/tRP/tFAW/tCCD_L 가 필수.
- tFAW는 *sliding window* checker로 구현 — 큐에 timestamp 저장 + 4개 초과 시 fail.
- Coverage는 *corner timing bin* (min_spec, normal, long_idle) × 파라미터 cross.
- Burst order는 *MR0/MR1*에 의존 — scoreboard 가 *MR 변경을 추적*.

## 9. Further Reading

- 이전: [Ch05. Command·Burst](05_commands_burst.md)
- 다음: [Ch07. Refresh·tREFI/tRFC·RFM](07_refresh_rfm.md)
- 부록 C: [SVA / Coverage 예제 모음](appendix_c_sva_coverage_examples.md)
- 퀴즈: [Ch06 퀴즈](quiz/ch06_quiz.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../05_commands_burst/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch05. Command·Burst</div>
  </a>
  <a class="nav-next" href="../07_refresh_rfm/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch07. Refresh·RFM</div>
  </a>
</div>
