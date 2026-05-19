# Ch06 퀴즈 — Timing·Preamble·Postamble

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="./"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> 퀴즈 인덱스</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">CH 06</span>
</div>

## 객관식

!!! question "Q1. tRCD 는 무엇을 의미하는가? `(Remember)`"
    - A. RD → CL의 latency
    - B. ACT → 첫 RD/WR 가능 시점까지의 최소 cycle 수
    - C. Refresh interval
    - D. PRE → ACT 시간

??? answer "정답: B"
    **Why**: Row-to-Column Delay. ACT 후 row buffer activation에 필요한 시간. (Ch06 §2.1)

!!! question "Q2. tFAW 의 sliding window 안에 *최대 발급 가능한 ACT* 수는? `(Remember)`"
    - A. 1
    - B. 2
    - C. 4
    - D. 8

??? answer "정답: C"
    **Why**: 'Four' Activate Window — 4 ACT 까지만 한 윈도우 안에 허용. 피크 전류 제한. (Ch06 §2.2)

!!! question "Q3. DDR5의 *Preamble 길이*가 DDR4 대비 일반적으로 *길어진* 이유는? `(Understand)`"
    - A. 데이터 보안
    - B. High-speed signaling에서 수신측 sampling 정확도 확보
    - C. Bandwidth 절약
    - D. ECC 강화

??? answer "정답: B"
    **Why**: 데이터 속도가 빨라지면 *수신측이 sample timing 잡기 어려움* — 더 긴 preamble로 *training 마진* 확보. (Ch06 §4)

!!! question "Q4. *Same BG* 의 CAS-to-CAS 제약은? `(Remember)`"
    - A. tCCD_S
    - B. tCCD_L
    - C. tRCD
    - D. tRRD_L

??? answer "정답: B"
    **Why**: tCCD_L (Long) 가 *같은 BG*, tCCD_S (Short) 가 *다른 BG*. (Ch06 §2.2)

## 단답형

!!! question "Q5. tFAW assertion을 *sliding window*로 구현하는 이유와 단순 카운터로는 부족한 이유? `(Apply)`"

??? answer "예시 답안"
    - 단순 카운터: "4 ACT 까지" 라는 *총수* 만 검증 — *언제* 4번이 발급되었는지 무관
    - Sliding window: *특정 시점 기준 이전 tFAW 윈도우 안*에 4개 초과면 fail
    - 예: ACT 4번이 *각각 5us 간격*으로 발급되면 OK이지만, ACT 4번이 *연속 10ns 안에* 모이면 fail
    - 구현: timestamp queue + 윈도우 밖 항목 제거 + 큐 사이즈 > 4 → error (Ch06 §5.2)

!!! question "Q6. Preamble pattern을 *monitor가 검증*해야 하는 이유는? `(Analyze)`"

??? answer "예시 답안"
    - Preamble 패턴 (예: 2 tCK = `0→1→0→1`) 자체가 *spec 규정*
    - DRAM이 *spec과 다른 패턴*을 보내면 *receiver의 sample timing 락 fail* 가능성
    - Monitor는 *transactional capture*만 하지 말고 *signal-level pattern*도 검증해야 *low-level bug catch* 가능
    - 일반적인 SVA로 *bit pattern* 시퀀스 표현 — Ch06 §4.4 예제 (Ch06 §4.4)

## 대표 문제

!!! question "Q7. DDR5-6400, tCK=0.3125ns, tRCD=28 nCK, CL=46 nCK, BL=16. *4 banks 에 back-to-back ACT-RD 시퀀스*를 발급할 때, tFAW=13 ns 가정. 시퀀스가 *spec 안*에 들어가도록 *최소 시간*에 모두 끝나려면 어떻게 schedule해야 하는가? `(Apply, Evaluate)`"

???+ answer "풀이 (multi-bank scheduling dry-run)"

    **Step 1 — 기본 가정**
    - 4 banks → bank 0, 1, 2, 3 (가정: 다른 BG 2개 + 다른 BA 2개 조합)
    - Back-to-back ACT-RD가 필요 → 각 bank에 ACT 후 RD

    **Step 2 — 다른 BG로 분산해 tRRD_S/tCCD_S 활용**
    - ACT-ACT 다른 BG: tRRD_S 적용 — 보통 tRRD_S < tRRD_L
    - 4 ACTs 가 모두 다른 BG라면? DDR5는 8 BG라 가능 → tRRD_S 만 적용
    - 그러나 *tFAW = 13 ns* 제약이 더 강함

    **Step 3 — tFAW 가 binding 제약**

    가정: tRRD_S = 4 nCK (= 1.25 ns). 4 ACT를 *최대 빨리* 발급하면:
    - ACT 0 at t=0
    - ACT 1 at t=1.25 ns
    - ACT 2 at t=2.5 ns
    - ACT 3 at t=3.75 ns
    - 모두 *3.75 ns* 안에 — tFAW(13 ns) 안에 들어감 → OK

    그러나 tFAW=13ns 라면 5번째 ACT는 *t=13 ns 이후*에 발급 가능 (sliding window 기준).

    **Step 4 — Cycle dry-run**

    | nCK | 시간(ns) | 이벤트 |
    |---|---|---|
    | 0 | 0.0 | ACT bank0 (BG0,BA0) 발급 |
    | 4 | 1.25 | ACT bank1 (BG1,BA0) 발급 (tRRD_S 후) |
    | 8 | 2.5 | ACT bank2 (BG2,BA0) 발급 |
    | 12 | 3.75 | ACT bank3 (BG3,BA0) 발급 |
    | 28 | 8.75 | bank0 의 RD 가능 (tRCD=28) |
    | 32 | 10.0 | bank1 의 RD |
    | 36 | 11.25 | bank2 의 RD |
    | 40 | 12.5 | bank3 의 RD |
    | 28+46 = 74 | 23.125 | bank0 의 데이터 도착 시작 |

    **Step 5 — DV 검증 포인트**
    1. SVA `a_trrd_s`: 다른 BG 간 ACT-ACT 가 tRRD_S 이상 보장
    2. SVA `a_tfaw`: 4 ACT가 13 ns 윈도우 안에 들어가는지 (만약 5번째가 들어가면 fail)
    3. SVA `a_tccd_s`: 다른 BG 간 RD-RD가 tCCD_S 이상
    4. covergroup `multi_bank_scheduling_cg`: bank-parallel 사용 정도 (몇 개 bank를 동시에 활성화하는가)
    5. directed test `test_max_parallel_banks`: 4 banks를 최대 빨리 활성화 시도 → 모든 SVA pass + scoreboard 데이터 정합성

    **DV 함의**
    - 단순 single-bank traffic만 검증하면 bank 병렬성 검증 불가 → coverage hole
    - tFAW는 *peak 전류 보호 메커니즘* — silicon에서 power integrity와 직결. 위반 시 전압 droop → 데이터 corruption
    - tFAW 위반 + 정상 read 데이터 = false pass — silicon 에서 *간헐적*으로 fail. SVA가 *유일한 방어선*.

---

<div class="chapter-nav">
  <a class="nav-prev" href="ch05_quiz/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch05 퀴즈</div>
  </a>
  <a class="nav-next" href="ch07_quiz/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch07 퀴즈</div>
  </a>
</div>
