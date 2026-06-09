---
title: "Ch06. Timing 파라미터·Preamble·Postamble"
---

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

- [Ch05. Command·Truth Table·Burst](../05_commands_burst/)
- 동기식 회로의 setup/hold, clock cycle 개념

## 1. 왜 timing 파라미터가 DV의 절반인가

DRAM 검증의 절반은 protocol, 나머지 절반은 timing입니다. Protocol은 어떤 명령을 어떤 순서로 발급해야 하는지를 다루고, timing은 명령 사이에 얼마나 기다려야 하는지를 다룹니다. 두 가지 모두 spec violation이지만 동작하는 방식이 다릅니다. protocol 위반은 대부분 즉각적인 오동작으로 드러나지만, timing 위반은 cell이 충분히 precharge되지 않은 상태에서 다음 row를 열거나 write가 완전히 반영되기 전에 PRE를 내리는 등 subtle한 데이터 손상을 유발합니다.

상용 메모리 controller IP에서 발견되는 대부분의 silicon bug는 timing corner, 특히 speed bin 경계나 back-to-back 명령의 latency에서 발생합니다. DV의 timing checker가 느슨하면, 예를 들어 `tRCD-1`도 통과시키는 SVA를 작성하면, 시뮬레이션은 깨끗하게 통과하지만 silicon에서 간헐적 fail이 나타납니다. timing checker를 spec 수치와 정확하게 일치시키는 것이 중요한 이유입니다.

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

(Refresh 상세는 [Ch07](../07_refresh_rfm/))

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

:::note[tRAS 의 하한은 cell restore 시간에서 나온다]
위 그림에서 tRAS 는 "ACT 후 같은 bank 의 PRE 까지 최소 active 시간" 이라는 _규칙_ 으로 보이지만, 그 최소값은 셀 물리에서 나옵니다. Ch01 에서 보았듯 read 는 destructive — ACT 로 word-line 을 열면 셀 전하가 bit-line 으로 흩어지고, sense amplifier 가 그 값을 latch 한 뒤 같은 word-line 이 열려 있는 동안 셀 capacitor 에 원래 값을 **되써넣습니다(restore)**. 이 restore 가 capacitor 를 다음 refresh 까지 버틸 만큼 충분히 충전하는 데에는 물리적 시간이 걸립니다. 만약 restore 가 끝나기 전에 PRE 로 word-line 을 닫아 버리면 셀에 _덜 충전된_ 약한 전하만 남아, 누설로 인해 데이터를 일찍 잃을 위험이 생깁니다. 그래서 ACT→PRE 사이에 "restore 완료 보장 시간" 인 tRAS 가 하한으로 강제되는 것입니다 — tRAS 는 임의의 숫자가 아니라 sense amp 가 cell 을 다시 채우는 데 필요한 시간입니다.
:::

---

## 3. DDR5 의 timing 변화 — 무엇이 달라졌나

> 출처: JESD79-5C.01 v1.31 §3.5 (MR), §4 (Command operation)

### 3.1 DDR4 vs DDR5 — 동일 절대 시간, 다른 nCK 수

DDR5는 tCK가 짧으므로 (예: 8400 MT/s → tCK ≈ 0.238ns), 셀이나 bit-line의 물리적 동작 시간은 DDR4와 크게 다르지 않은데도 nCK 수로 표현하면 값이 훨씬 커집니다. 이는 직관에 반하는 결과입니다. "DDR5가 더 빠른데 왜 tRCD가 더 많은 클럭인가?"라는 질문이 나오는 이유입니다. 답은 간단합니다. cell이 활성화되는 데 걸리는 물리적 시간(ns)은 비슷하지만, 1 클럭의 길이가 절반으로 줄었으므로 같은 절대 시간을 표현하는 데 두 배의 클럭 수가 필요한 것입니다.

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

DRAM이 RD 응답을 보낼 때, DQS_t/c는 burst 시작 전에 정해진 패턴을 먼저 보여줍니다. host receiver는 이 preamble 패턴을 감지하고 자신의 sampling timing을 잡습니다. preamble이 없으면 receiver는 burst의 첫 bit가 언제 시작되는지 알 수 없어 데이터를 놓칩니다. 고속 신호에서는 eye가 좁아지므로, sampling timing을 더 정확히 잡기 위해 preamble을 길게 설정하기도 합니다.

_왜 preamble 이 있어야 receiver 가 첫 에지를 잡을 수 있는가_ 는 strobe 가 평소 Hi-Z(idle) 상태라는 데서 나옵니다. DQS 는 burst 가 없을 때 구동되지 않고 종단 저항에 의해 어중간한 전압(또는 Hi-Z)에 떠 있습니다. 이 상태에서 데이터의 첫 비트와 _동시에_ DQS 가 갑자기 토글하기 시작하면, receiver 내부의 strobe 입력 버퍼와 DLL/지연 회로가 안정 상태에 이르기 전이라 그 첫 latching edge 를 놓치거나 잘못된 시점에 잡습니다 — 정지해 있던 시계가 첫 똑딱임을 신뢰할 수 없는 것과 같습니다. preamble 은 실제 데이터가 오기 _전에_ DQS 를 먼저 정해진 패턴으로 토글시켜, receiver 가 (1) "지금부터 strobe 가 온다" 는 것을 인지하고 (2) 입력 버퍼·게이팅 회로를 미리 깨워 안정시킬 시간을 줍니다. 그래서 첫 데이터 비트가 도착할 때는 이미 receiver 가 준비된 상태가 되어 첫 에지부터 정확히 sample 할 수 있는 것입니다.

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
- **DDR5 Read Preamble**: 1 tCK~4 tCK (MR8:OP[2:0]) — high-speed signaling에서 더 긴 preamble이 필요합니다. 5200 MT/s 이상에서는 2 tCK 모드가 지원되지 않고 3 tCK 또는 4 tCK를 써야 합니다.

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

:::tip[Q. DDR5-6400, tCK=0.3125ns, tRCD=28 nCK, CL=46 nCK, BL=16. ACT 명령이 cycle 0에 발급되면, 첫 데이터 비트가 DQ에 나타나는 시점은 몇 ns? RD가 발급되는 가장 빠른 cycle은? 같은 시퀀스를 DDR4-3200 (tCK=0.625ns, tRCD=14 nCK, CL=22 nCK, BL=8) 으로 대조.]
:::
<details>
<summary>풀이 (cycle-by-cycle 계산)</summary>


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

</details>
---

## 8. PDF 정밀 인용 — DDR5 §4.4 Programmable Preamble/Postamble

> 출처: JESD79-5C.01 v1.31 §4.4, Tables 37~38

### 8.1 Read Preamble — MR8:OP[2:0] 인코딩 (정밀)

> §4.4.1 원문 인용:
> "DDR5 supports a programmable read preamble and postamble. **Read Preamble is configured as 1tCK, 2tCK (two unique modes), 3tCK and 4tCK via MR8:OP[2:0]**."

| MR8:OP[2:0] | 모드 | Pattern |
|---|---|---|
| `000B` | **1 tCK** | `10` Pattern |
| `001B` | **2 tCK** | `0010` Pattern |
| `010B` | **2 tCK** (DDR4 Style) | `1110` Pattern |
| `011B` | **3 tCK** | `000010` Pattern |
| `100B` | **4 tCK** | `00001010` Pattern |
| `101B` | Reserved | |
| `110B` | Reserved | |
| `111B` | Reserved | |

**Read Postamble**: 0.5tCK 또는 1.5tCK via **MR8:OP[6]**

### 8.2 Write Preamble — MR8:OP[4:3] 인코딩

> §4.4.2 원문 인용:
> "Write Preamble is configured as **2tCK, 3tCK, and 4tCK via MR8:OP[4:3]**"
> "Write Postamble is configured as **0.5tCK or 1.5tCK via MR8:OP[7]**"

| MR8:OP[4:3] | 모드 |
|---|---|
| `00B` | 2 tCK Write Preamble |
| `01B` | 3 tCK Write Preamble |
| `10B` | 4 tCK Write Preamble |
| `11B` | Reserved |

### 8.3 Table 37 — Preamble/Postamble Timing (DDR5-3200~4800)

> 출처: JESD79-5C.01 §4.4.3 Table 37 (단위: tCK(avg))

| Parameter | Symbol | DDR5-3200~3600 (Min) | DDR5-4000~4400 (Min) | DDR5-4800 (Min) |
|---|---|---|---|---|
| 1tCK Read Preamble | `tRPRE1` | **0.900** | — | — |
| 2tCK Read Preamble | `tRPRE2` | **1.800** | 1.800 | 1.800 |
| 2tCK DDR4-style Read Preamble | `tRPRE2_D4` | 1.800 | 1.800 | 1.800 |
| 3tCK Read Preamble | `tRPRE3` | — | **2.700** | 2.700 |
| 4tCK Read Preamble | `tRPRE4` | — | — | — |
| 0.5tCK Read Postamble | `tRPST0.5` | **0.450** | 0.450 | 0.450 |
| 1.5tCK Read Postamble | `tRPST1.5` | **1.200** | 1.200 | 1.200 |
| 2tCK Write Preamble | `tWPRE2` | **1.800** | 1.800 | 1.800 |
| 3tCK Write Preamble | `tWPRE3` | — | 2.700 | 2.700 |
| 4tCK Write Preamble | `tWPRE4` | — | **3.600** | 3.600 |
| 0.5tCK Write Postamble | `tWPST0.5` | **0.45** | 0.45 | 0.45 |
| 1.5tCK Write Postamble | `tWPST1.5` | — | **1.20** | 1.20 |
| DQS high toggle pulse (Write Preamble) | `tDQSH_pre` | 0.395~0.605 | 0.395~0.605 | 0.430~0.570 |
| DQS low toggle pulse (Write Preamble) | `tDQSL_pre` | 0.395~0.605 | 0.395~0.605 | 0.430~0.570 |

### 8.4 Table 38 — Preamble/Postamble Timing (DDR5-5200~8800)

> 출처: JESD79-5C.01 §4.4.3 Table 38

| Parameter | Symbol | DDR5-5200~6400 | DDR5-6800~7200 | DDR5-7600~8800 |
|---|---|---|---|---|
| 2tCK DDR4-style Read Preamble | `tRPRE2_D4` | **2.700** | — | — |
| 3tCK Read Preamble | `tRPRE3` | **2.700** | — | — |
| 4tCK Read Preamble | `tRPRE4` | **3.600** | 3.600 | 3.600 |
| 1.5tCK Read Postamble | `tRPST1.5` | 1.200 | 1.200 | **1.300** |
| 3tCK Write Preamble | `tWPRE3` | 2.700 | — | — |
| 4tCK Write Preamble | `tWPRE4` | 3.600 | 3.600 | 3.600 |
| 1.5tCK Write Postamble | `tWPST1.5` | 1.200 | 1.200 | 1.200 |
| `tDQSH_pre`/`tDQSL_pre` | | 0.430~0.570 | 0.450~0.550 | 0.450~0.550 |

핵심:
- 고속 (DDR5-5200 이상)에서는 **2tCK preamble 미지원** → 3tCK/4tCK 필수
- DDR5-7600 이상에서 tRPST1.5 가 1.300으로 *살짝 증가*
- tDQSH_pre/tDQSL_pre 범위가 *고속에서 좁아짐* — 더 정확한 duty cycle 필요

_왜 고속에서는 2tCK preamble 로는 부족한가_ — preamble 이 receiver 를 깨우는 데 필요한 시간은 _절대 시간(ns)_ 단위인데, tCK 는 속도가 오를수록 짧아지기 때문입니다. 위 §4.1 에서 보았듯 preamble 의 역할은 idle 상태의 strobe 입력 버퍼와 게이팅·DLL 회로가 안정 상태에 도달할 _물리적 시간_ 을 벌어 주는 것입니다. 이 안정화 시간은 회로의 물리 특성이 정하므로 클럭이 빨라진다고 비례해서 줄지 않습니다. 그런데 2tCK preamble 의 길이는 2 × tCK 이므로, 고속에서 tCK 가 절반으로 줄면 그 2tCK 가 가리키는 절대 시간도 절반으로 짧아져 receiver 안정화에 모자라게 됩니다. 그래서 같은 안정화 시간을 확보하려면 더 많은 클럭 — 3tCK 또는 4tCK — 으로 preamble 을 늘려야 하고, 그 결과 5200 MT/s 이상에서는 2tCK 모드가 빠지고 3/4tCK 가 필수가 되는 것입니다.

### 8.5 §4.4.3 — Preamble/Postamble Timing (원문 인용)

> §4.4.3 원문 인용:
> "During Read and Write operations, the input receiver strobe shall be aligned with the DQ according to the Preamble and Postamble settings, and the strobe shall meet the specified timing requirements to guarantee enough timing margin by setting the window for the strobe during the Preamble and Postamble time frame. **When the DRE is enabled, the DQs shall be high for a minimum of 4-UI prior to the first Write data bit to ensure proper DFE synchronization**."

→ **DRE (DQ Reset Enable / DFE Reset)** enabled 시 *4-UI minimum DQ HIGH*. DV는 이 prep 시간을 별도 SVA로 검증.

### 8.6 §4.5 — Interamble (원문 인용)

> §4.5 원문 인용:
> "The DQS strobe for the device requires a preamble prior to the first latching edge (the rising edge of DQS_t with data valid), and it requires a postamble after the last latching edge."
>
> "Additionally, the postamble and preamble configured size shall **NOT force the HOST to add command gaps in the command interval just to satisfy postamble or preamble settings**. (i.e., Preamble=4tCK + Postamble=1.5tCK shall NOT force tCCD+5)."
>
> "In Read to Read operations with **tCCD=BL/2, postamble for 1st command and preamble for 2nd command shall disappear** to create consecutive DQS latching edge for seamless burst operations."

핵심:
- **Interamble**: 연속 burst 사이의 *postamble + preamble overlap*
- tCCD=BL/2 (= 8 nCK for BL16) 면 *seamless* — postamble/preamble 사라짐
- tCCD > BL/2 면 *gap* 발생, preamble/postamble 모두 보임
- preamble/postamble 설정이 *additional command gap*을 *강제하지 않음* — RTL 설계 자유도 보장

DV 적용 — 연속 Read 시 interamble 동작 검증:
```systemverilog
// RD-RD interval 별 DQS pattern
typedef enum {INTERAMBLE_SEAMLESS, INTERAMBLE_TOUCH, INTERAMBLE_OVERLAP, INTERAMBLE_GAP} interamble_e;

covergroup interamble_cg with function sample (int tccd_excess, int post_tck, int pre_tck);
    cp_tccd: coverpoint tccd_excess {
        bins seamless     = {0};         // tCCD = BL/2
        bins min_plus_1   = {1};
        bins min_plus_2   = {2};
        bins min_plus_3   = {3};
        bins min_plus_4   = {4};
        bins min_plus_5plus = {[5:$]};
    }
    cp_post: coverpoint post_tck {
        bins p_05 = {1};   // 0.5tCK encoded as 1 (half-tCK)
        bins p_15 = {3};   // 1.5tCK
    }
    cp_pre: coverpoint pre_tck {
        bins p_1 = {1}; bins p_2 = {2}; bins p_3 = {3}; bins p_4 = {4};
    }
    cx: cross cp_tccd, cp_post, cp_pre;
endgroup
```

### 8.7 Preamble pattern 정확 인식 — Monitor SVA

```systemverilog
// 2tCK Read Preamble (DDR5 default) — pattern "0010"
// 출처: JESD79-5C.01 §4.4.1
sequence s_2tck_preamble_pattern;
    (dqs_t == 1'b0) ##1 (dqs_t == 1'b0) ##1 (dqs_t == 1'b1) ##1 (dqs_t == 1'b0);
        // 4 half-cycles = 2 tCK
endsequence

property p_2tck_read_preamble;
    @(posedge half_clk)
    rd_preamble_start |-> s_2tck_preamble_pattern ##1 burst_starts;
endproperty
a_2tck_read_preamble: assert property (p_2tck_read_preamble);

// 1tCK Read Preamble — pattern "10"
sequence s_1tck_preamble_pattern;
    (dqs_t == 1'b1) ##1 (dqs_t == 1'b0);
endsequence

// 3tCK — "000010"
sequence s_3tck_preamble_pattern;
    (dqs_t == 1'b0) ##1 (dqs_t == 1'b0) ##1 (dqs_t == 1'b0) ##1
    (dqs_t == 1'b0) ##1 (dqs_t == 1'b1) ##1 (dqs_t == 1'b0);
endsequence

// 4tCK — "00001010"
sequence s_4tck_preamble_pattern;
    (dqs_t == 1'b0) ##1 (dqs_t == 1'b0) ##1 (dqs_t == 1'b0) ##1 (dqs_t == 1'b0) ##1
    (dqs_t == 1'b1) ##1 (dqs_t == 1'b0) ##1 (dqs_t == 1'b1) ##1 (dqs_t == 1'b0);
endsequence
```

> 위 SVA는 *개념 예시* — 실제로는 DQS_t/DQS_c differential, half-tCK granularity, *positive/negative edge 별도 sampling* 등 시뮬레이터 환경에 맞게 다듬어야 합니다.

### 8.8 MR40:OP[2:0] — Read DQS Offset (정밀 보충)

> §4.4.1 NOTE: "DQS shall have an option to drive early by x-tCK to accommodate different HOST receiver designs as controlled by the Read DQS Offset in MR40:OP[2:0]."

| MR40:OP[2:0] | Read DQS Offset |
|---|---|
| `000B` | 0 (no offset, default) |
| `001B` | 1 tCK early |
| `010B` | 2 tCK early |
| `011B` | 3 tCK early |
| ... | (spec 참조) |

→ host receiver design이 *늦은 DQS edge sampling*을 못 하는 경우, DRAM이 DQS를 *미리 driving*. DV는 offset값 별 cover.

### 8.9 §4.4.4 — tWPRE/tRPRE 측정 방법 (원문 인용)

> §4.4.4 원문 인용:
> "tWPRE and tRPRE are measured **from a starting point at VswM HIGH or LOW** (as defined in the table below) **to the differential crossing point of DQS_t/DQS_c corresponding to the first burst bit of data** as the ending point. The method is applicable for all programmable Preamble durations."

**Table 39 — VswM Reference Voltages**

| Measured Parameter | Reference | Unit |
|---|---|---|
| VswM HIGH | VIHdiffDQS | mV |
| VswM LOW | VILdiffDQS | mV |

§4.4.5 — tWPST/tRPST 측정:
> "tWPST and tRPST are measured from a starting point at **the differential crossing point of DQS_t/DQS_c corresponding to the last burst bit of data** to the VswM LOW ending point."

### 8.10 §4.5 Read Interamble Timing Diagrams (개요)

§4.5.1 인용:
> "In Read to Read operations with tCCD=BL/2, postamble for 1st command and preamble for 2nd command shall disappear to create consecutive DQS latching edge for **seamless burst operations**."

| tCCD intervals | DQS pattern between bursts |
|---|---|
| `BL/2` (= 8 nCK for BL16) | Seamless (no postamble/preamble visible) |
| `Min+1` | 1 nCK gap |
| `Min+2` | 2 nCK gap, postamble/preamble *touches* or *overlaps* (config 따라) |
| `Min+3` | 3 nCK gap |
| `Min+4` | 4 nCK gap, full postamble + full preamble visible |
| `Min+5` | 5 nCK gap, *toggles take precedence over static preambles* (overlap 시) |

DV — interamble cover:
- 위 각 spacing 마다 *DQS pattern* 정확히 model
- Scoreboard가 RD burst data를 *interamble 영향 받지 않게* 추출

## 9. 핵심 정리 (Key Takeaways)

- 핵심 timing 9개를 외워야 함: tRCD/tRP/tRAS/tRC/tWR/tRTP/tRRD_L/S/tFAW/tCCD_L/S.
- DDR5는 *tCK가 짧으므로* 동일 절대 시간에 *더 많은 nCK*. `tCCD_L_WR2` 같은 세분화 timing 추가.
- Preamble은 *DDR5에서 더 길어짐* (1tCK/2tCK/3tCK/4tCK 옵션) — **MR8:OP[2:0]** (Read), **MR8:OP[4:3]** (Write) 로 설정. high-speed (5200+ MT/s)는 *2tCK 미지원*, 3tCK/4tCK 필수.
- Postamble: 0.5tCK or 1.5tCK via **MR8:OP[6]** (Read), **MR8:OP[7]** (Write).
- Preamble pattern은 *spec 정의 비트 시퀀스* (1tCK=`10`, 2tCK=`0010`, 3tCK=`000010`, 4tCK=`00001010`) — monitor가 pattern 자체 검증.
- SVA로 *모든* major timing 위반을 catch — tRCD/tRP/tFAW/tCCD_L 가 필수.
- tFAW는 *sliding window* checker로 구현 — 큐에 timestamp 저장 + 4개 초과 시 fail.
- **Interamble** (RD-RD 사이): tCCD=BL/2 면 *seamless* (preamble/postamble 사라짐). 그 외는 spacing별 distinct pattern.
- Coverage는 *corner timing bin* (min_spec, normal, long_idle) × 파라미터 cross + *preamble length × postamble length* cross.
- Burst order는 *MR0/MR1*에 의존 — scoreboard 가 *MR 변경을 추적*.

## 10. Further Reading

- 이전: [Ch05. Command·Burst](../05_commands_burst/)
- 다음: [Ch07. Refresh·tREFI/tRFC·RFM](../07_refresh_rfm/)
- 부록 C: [SVA / Coverage 예제 모음](../appendix_c_sva_coverage_examples/)
- 퀴즈: [Ch06 퀴즈](../quiz/ch06_quiz/)

