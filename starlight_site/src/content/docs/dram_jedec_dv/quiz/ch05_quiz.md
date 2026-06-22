---
title: "Ch05 퀴즈 — Command·Truth Table·Burst Operation"
---

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> 퀴즈 인덱스</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">CH 05</span>
</div>

## 객관식

:::tip[Q1. DRAM의 핵심 명령 7가지에 *포함되지 않는* 것은? `(Remember)`]
- A. ACT
- B. PRE
- C. CMP (Compare)
- D. REF
:::
<details>
<summary>정답: C</summary>

**Why**: CMP(Compare)는 DRAM 명령 집합에 존재하지 않습니다. DRAM의 핵심 명령 7가지는 ACT(Activate), RD(Read), WR(Write), PRE(Precharge), REF(Refresh), MRW(Mode Register Write), MRR(Mode Register Read)입니다. A·B·D는 모두 이 목록에 실제로 존재하는 명령이므로 오답입니다. DV 관점에서 이 7가지 명령에 대한 발급 가능/불가능 상태를 bank FSM과 함께 모델링하는 것이 command coverage의 기초입니다. (Ch05 §1.1)

</details>
:::tip[Q2. LPDDR5의 BL16 burst가 LPDDR4의 BL16 대비 동일 beat 수를 전송할 때, 같은 데이터 속도라면 *burst 시간*은? `(Apply)`]
- A. 2배 길음
- B. 절반
- C. 거의 같음 (beat 수가 같으므로)
- D. 4배
:::
<details>
<summary>정답: C</summary>

**Why**: LPDDR5와 LPDDR4 모두 prefetch 16n / BL16이므로 한 burst의 beat 수(16 beat)가 같습니다. 같은 데이터 전송 속도라면 burst 지속 시간도 같습니다. LPDDR5의 핵심 차이는 burst 길이가 아니라 데이터가 고속 **WCK** 도메인에서 전송된다는 점과, BL32 옵션이 추가됐다는 점입니다. A(2배)·B(절반)·D(4배)는 모두 beat 수가 동일하다는 사실과 맞지 않습니다. 참고로 LPDDR5에서 WCK 주파수를 올리면 같은 BL16이라도 절대 시간이 짧아집니다(DVFSC gear 의존). DV에서 BL과 WCK gear를 혼동하면 DQ sample window를 잘못 잡습니다. (Ch05 §3.2)

</details>
:::tip[Q3. BL32를 사용하는 *권장 시나리오*는? `(Evaluate)`]
- A. Frequent bank switching
- B. Latency-sensitive workload
- C. Large sequential DMA copy
- D. Random access pattern
:::
<details>
<summary>정답: C</summary>

**Why**: BL32는 한 번에 더 많은 데이터를 연속으로 전송하므로 대형 순차 DMA copy처럼 긴 연속 접근에 유리합니다. BL32가 도중에 interrupt될 수 없는 구조이기 때문에, A(잦은 bank 전환)나 D(랜덤 접근)처럼 짧고 자주 바뀌는 패턴에서는 오히려 레이턴시를 높이므로 BL16이 낫습니다. B(레이턴시 민감)도 마찬가지로 burst가 길면 첫 바이트 이후 대기가 생기므로 BL32는 부적합합니다. DV에서 BL32 시나리오는 반드시 coverage에 포함해야 하지만, 그 시나리오가 현실적인 workload에 맞는지도 확인해야 합니다. (Ch05 §3.3)

</details>
:::tip[Q4. DDR5 monitor가 *2-cycle command를 reconstruct* 할 때 핵심 신호는? `(Understand)`]
- A. CK_t/c rising edge만
- B. CS_n의 2 cycles 윈도우 패턴
- C. ACT_n 신호
- D. ALERT_n
:::
<details>
<summary>정답: B</summary>

**Why**: DDR5 2-cycle command를 reconstruct하려면 CS_n이 2 cycles 연속 LOW인 패턴을 감지해야 합니다. 이것이 monitor가 "지금 2-cycle 명령이 진행 중"임을 판단하는 유일한 시그너처입니다. A(CK rising edge만)는 명령 경계를 잡지 못합니다. C(ACT_n 신호)는 DDR4의 핀 신호로 DDR5에는 존재하지 않으며 명령 정보가 CA 버스에 인코딩되어 있습니다. D(ALERT_n)는 error 응답 신호로 명령 디코딩과 무관합니다. CS_n 패턴을 정확히 추적하지 않으면 monitor가 2-cycle 명령의 두 번째 cycle을 별개의 명령으로 잘못 해석할 수 있습니다. (참고 — LPDDR5는 CA[6:0]를 여러 CK cycle에 걸쳐 single-ended로 인코딩하므로 명령 경계 판정 로직이 DDR5와 다르며, CA 버스 정렬을 위해 CBT가 필수입니다.) (Ch05 §2.2)

</details>
## 단답형

:::tip[Q5. *legal command after PRE/ACT* assertion이 검증하는 것을 설명하라. `(Apply)`]
:::
<details>
<summary>예시 답안</summary>

- ACT 후 *같은 bank*에 *PRE 없이 또 ACT*는 spec violation
- PRE 후 *tRP* 이내의 ACT는 violation
- 이 assertion 들이 *bank state FSM*과 함께 작동해서 *모든 bank 의 상태*를 추적
- 위반 시 *즉시* uvm_error → debug 시점 명확화 (Ch05 §6)

</details>
:::tip[Q6. Scoreboard의 burst order 계산이 *MR0/MR1 설정에 따라 달라지는* 이유와 검증 함의는? `(Analyze)`]
:::
<details>
<summary>예시 답안</summary>

- DDR5의 burst order는 default *sequential*이지만 *interleaved* 옵션도 있음 (BL16/BL32)
- MR0/MR1에서 mode 선택
- Scoreboard가 단순 `t.col + i` 로 계산하면 *interleaved 모드*에서 *잘못된 expected addr*
- 검증 함의: scoreboard가 *MR mirror value를 추적*하고, burst order *전환* 시 *동작 변경*. RAL의 callback으로 *MR write 시점*에 scoreboard mode update. (Ch05 §7)

</details>
## 대표 문제

:::tip[Q7. 다음 cycle 시퀀스에서 명령이 몇 개 발급되고 각각 무엇인지 추적하라. `(Apply, Analyze)`]

```
Cycle:   0      1      2      3      4      5      6      7      8
CS_n:    LOW    LOW    HIGH   LOW    HIGH   LOW    LOW    HIGH   LOW
CA[6:0]: A0     A1     XX     B0     XX     C0     C1     XX     D0
```"
:::
<details>
<summary>풀이 (cycle-by-cycle monitor reconstruct)</summary>


**Step 1 — CS_n 윈도우 분석**

| Cycle | CS_n | 패턴 분석 |
|---|---|---|
| 0 | LOW | 명령 시작 |
| 1 | LOW | 명령 계속 → cycle 0-1 = **2-cycle 명령 #1** {A0, A1} |
| 2 | HIGH | idle |
| 3 | LOW | 명령 시작 |
| 4 | HIGH | (cycle 3) 이 1-cycle → **1-cycle 명령 #2** {B0} (NOP/DES) |
| 5 | LOW | 명령 시작 |
| 6 | LOW | 명령 계속 → cycle 5-6 = **2-cycle 명령 #3** {C0, C1} |
| 7 | HIGH | idle |
| 8 | LOW | 명령 시작 → 다음 cycle 까지 봐야 함 |

**Step 2 — 결론**
- **3개의 명령 완료**: 2-cycle #1, 1-cycle #2, 2-cycle #3
- **명령 #4**: cycle 8에서 시작했지만 cycle 9의 CS_n을 보기 전까지는 1-cycle인지 2-cycle인지 *미확정*

**Step 3 — Monitor 상태 관리**
- Monitor가 *cycle 9* 의 CS_n까지 보고 *명령 #4*를 emit
- 만약 시뮬레이션 종료 시점이 cycle 8이라면 monitor가 *pending 상태로 종료* → end_of_simulation 에서 *경고*

**Step 4 — DV 적용**
- SVA: `cs_n_low_pattern` — 2 cycles 연속 LOW vs 1 cycle LOW pattern 자체를 cover
- covergroup `cs_n_pattern_cg`:
  - `bin two_cycle_cmd` — 2 cycles LOW
  - `bin one_cycle_cmd` — 1 cycle LOW
  - `bin idle` — HIGH
- 명령 종료 *경계*가 cycle-by-cycle로 잘 reconstruct되는지 directed test

**Step 5 — 함정 (Edge case)**
- 만약 CS_n이 3+ cycles 연속 LOW면? → spec violation (어떤 명령도 3-cycle은 아님). SVA로 catch
- 만약 power-on 직후 첫 cycle이 LOW로 시작? → init phase의 *합법적* 시나리오인지 check

</details>
---

