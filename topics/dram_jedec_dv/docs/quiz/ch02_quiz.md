# Ch02 퀴즈 — 패키지·핀아웃·어드레싱

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="index.md"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> 퀴즈 인덱스</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">CH 02</span>
</div>

## 객관식

!!! question "Q1. DDR5 의 Bank Group(BG) 개수는? `(Remember)`"
    - A. 2
    - B. 4
    - C. 8
    - D. 16

??? answer "정답: C"
    **Why**: DDR5는 8 BG. DDR4가 4 BG. (Ch02 §3.4)

!!! question "Q2. DDR5의 2-cycle command 에서 CS_n 의 동작 패턴은? `(Understand)`"
    - A. CS_n LOW 한 cycle만
    - B. CS_n LOW 가 2 cycles 연속
    - C. CS_n HIGH 한 cycle 후 LOW
    - D. CS_n 은 명령과 무관

??? answer "정답: B"
    **Why**: 2-cycle command는 *2 cycles 연속 CS_n LOW*. 1-cycle 명령(NOP/DES)은 cycle 0만 LOW. (Ch02 §3.3 + Ch05 §2.2)

!!! question "Q3. LPDDR4 의 die가 *기본적*으로 가지는 channel 수는? `(Remember)`"
    - A. 1
    - B. 2
    - C. 4
    - D. 8

??? answer "정답: B"
    **Why**: LPDDR4 die는 dual-channel이 기본. 각 channel 16-bit. (Ch02 §4.2)

!!! question "Q4. LPDDR5의 Bank mode 선택지로 옳은 것을 모두 고르시오. `(Remember)`"
    - A. 16 banks mode
    - B. 8 banks mode
    - C. BG mode
    - D. 32 banks mode

??? answer "정답: A, B, C"
    **Why**: LPDDR5는 16B / 8B / BG mode 3가지를 *MR로 선택*. 32B는 없음. (Ch02 §5.2)

## 단답형

!!! question "Q5. BG가 검증에서 중요한 이유를 timing 관점으로 설명하시오. `(Apply)`"

??? answer "예시 답안"
    같은 BG의 명령 간에는 `tCCD_L` (Long) 이, 서로 다른 BG의 명령 간에는 `tCCD_S` (Short) 이 적용. 같은 BG에서 *연속 RD/WR*은 더 긴 대기. DV는 BG-aware command sequencing을 stim에 반영해야 *모든 timing path*를 cover. (Ch02 §2.3)

!!! question "Q6. DDR5 16Gb x8 device의 어드레싱이 BG[2:0]+BA[1:0]+ROW[16:0]+COL[9:0] 일 때 총 cell 수와 cache line 단위로 환산했을 때의 총 cache lines를 계산하시오. (BL16, x8 = 16-byte/burst 가정, cache line = 64B) `(Apply)`"

??? answer "예시 답안"
    - 총 addressable beats: 2^3 × 2^2 × 2^17 × 2^10 = 2^32
    - x8 device에서 BL16 한 access = 16 bytes
    - cache line = 64B = 4× one device burst
    - 따라서 device 한 개로 cache line 환산: 2^32 / 4 = 2^30 = **1G cache lines**
    - 총 cell bit 수: 2^32 × 8 = 32 Gbit (가정상)

    (실제 16Gb device 는 capacity 표기 기준. 위는 *어드레싱 계산* 연습.)

## 대표 문제

!!! question "Q7. controller IP가 BL16 burst를 발급하는데, *실제 cycle-by-cycle DQ 동작*을 추적. DDR5-6400, tCK=0.3125ns, CL=46 nCK. cycle 0에 RD 발급 시 BL16 동안 DQ에 데이터가 valid한 *절대 시간*과 *몇 ns 동안*인지 계산. `(Apply)`"

???+ answer "풀이 (cycle dry-run)"

    **Step 1 — 명령 발급 시점**
    - DDR5 RD는 2-cycle 명령. cycle 0-1에 RD 인코딩 발급
    - 실제 명령 *완료* = cycle 1 끝

    **Step 2 — Data 도착 시점**
    - CL = 46 nCK → 명령 발급 후 46 nCK 후 data
    - 첫 beat = cycle 1 + 46 = cycle 47
    - 절대 시간 = 47 × 0.3125ns = **14.6875 ns**

    **Step 3 — BL16 의 burst 지속 시간**
    - BL16 = 16 beats
    - DDR이므로 each half-clock = 1 beat → 16 beats = 8 nCK = 8 × 0.3125ns = **2.5 ns**

    **Step 4 — Burst 종료 시점**
    - 종료 = 14.6875 + 2.5 = **17.1875 ns**

    **Step 5 — DV 시사점**
    - Monitor의 *DQ sample window* = 14.69ns ~ 17.19ns
    - Preamble은 *RD 명령 후 CL 직전*에 (preamble 길이만큼 더 전에 시작)
    - Postamble은 *17.19ns 이후* 1 nCK 정도
    - SVA: `tCL = 46 nCK` 정확히 — controller가 어떤 cycle에 data를 *기대*하는지 정확히 검증 가능

---

<div class="chapter-nav">
  <a class="nav-prev" href="ch01_quiz.md">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch01 퀴즈</div>
  </a>
  <a class="nav-next" href="ch03_quiz.md">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch03 퀴즈</div>
  </a>
</div>
