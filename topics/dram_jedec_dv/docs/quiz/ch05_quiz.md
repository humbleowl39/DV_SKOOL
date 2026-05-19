# Ch05 퀴즈 — Command·Truth Table·Burst Operation

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="./"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> 퀴즈 인덱스</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">CH 05</span>
</div>

## 객관식

!!! question "Q1. DRAM의 핵심 명령 7가지에 *포함되지 않는* 것은? `(Remember)`"
    - A. ACT
    - B. PRE
    - C. CMP (Compare)
    - D. REF

??? answer "정답: C"
    **Why**: CMP는 DRAM 명령에 없음. 7가지는 ACT/RD/WR/PRE/REF/MRW/MRR. (Ch05 §1.1)

!!! question "Q2. DDR5의 BL16 burst가 BL8 (DDR4) 대비 *2배의 데이터*를 전송하는 동안, *burst 시간*은? `(Apply)`"
    - A. 2배 길음
    - B. 절반
    - C. 거의 같음 (tCK가 절반이므로)
    - D. 4배

??? answer "정답: C"
    **Why**: DDR5 tCK ≈ DDR4의 절반 (속도 2배). BL16 = 8 nCK × tCK_DDR5 ≈ BL8 = 4 nCK × tCK_DDR4. 절대 시간 거의 동일. (Ch05 §3.2)

!!! question "Q3. BL32를 사용하는 *권장 시나리오*는? `(Evaluate)`"
    - A. Frequent bank switching
    - B. Latency-sensitive workload
    - C. Large sequential DMA copy
    - D. Random access pattern

??? answer "정답: C"
    **Why**: BL32는 *interrupt 불가*. sequential read에 좋음. random/bank-switching이 잦으면 BL16이 유리. (Ch05 §3.3)

!!! question "Q4. DDR5 monitor가 *2-cycle command를 reconstruct* 할 때 핵심 신호는? `(Understand)`"
    - A. CK_t/c rising edge만
    - B. CS_n의 2 cycles 윈도우 패턴
    - C. ACT_n 신호
    - D. ALERT_n

??? answer "정답: B"
    **Why**: CS_n의 *2 cycles 연속 LOW* 가 2-cycle 명령의 시그너처. ACT_n은 DDR4 신호로 DDR5에는 없음 (인코딩에 포함). (Ch05 §2.2)

## 단답형

!!! question "Q5. *legal command after PRE/ACT* assertion이 검증하는 것을 설명하라. `(Apply)`"

??? answer "예시 답안"
    - ACT 후 *같은 bank*에 *PRE 없이 또 ACT*는 spec violation
    - PRE 후 *tRP* 이내의 ACT는 violation
    - 이 assertion 들이 *bank state FSM*과 함께 작동해서 *모든 bank 의 상태*를 추적
    - 위반 시 *즉시* uvm_error → debug 시점 명확화 (Ch05 §6)

!!! question "Q6. Scoreboard의 burst order 계산이 *MR0/MR1 설정에 따라 달라지는* 이유와 검증 함의는? `(Analyze)`"

??? answer "예시 답안"
    - DDR5의 burst order는 default *sequential*이지만 *interleaved* 옵션도 있음 (BL16/BL32)
    - MR0/MR1에서 mode 선택
    - Scoreboard가 단순 `t.col + i` 로 계산하면 *interleaved 모드*에서 *잘못된 expected addr*
    - 검증 함의: scoreboard가 *MR mirror value를 추적*하고, burst order *전환* 시 *동작 변경*. RAL의 callback으로 *MR write 시점*에 scoreboard mode update. (Ch05 §7)

## 대표 문제

!!! question "Q7. 다음 cycle 시퀀스에서 명령이 몇 개 발급되고 각각 무엇인지 추적하라. `(Apply, Analyze)`

    ```
    Cycle:   0      1      2      3      4      5      6      7      8
    CS_n:    LOW    LOW    HIGH   LOW    HIGH   LOW    LOW    HIGH   LOW
    CA[6:0]: A0     A1     XX     B0     XX     C0     C1     XX     D0
    ```"

???+ answer "풀이 (cycle-by-cycle monitor reconstruct)"

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

---

<div class="chapter-nav">
  <a class="nav-prev" href="ch04_quiz/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch04 퀴즈</div>
  </a>
  <a class="nav-next" href="ch06_quiz/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch06 퀴즈</div>
  </a>
</div>
