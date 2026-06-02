---
title: "Ch02 퀴즈 — 패키지·핀아웃·어드레싱"
---

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> 퀴즈 인덱스</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">CH 02</span>
</div>

## 객관식

:::tip[Q1. DDR5 의 Bank Group(BG) 개수는? `(Remember)`]
- A. 2
- B. 4
- C. 8
- D. 16
:::
<details>
<summary>정답: C</summary>

**Why**: DDR5는 device당 8 Bank Group을 가집니다. DDR4가 4 BG였으므로 두 배로 늘어났습니다. A(2)나 B(4)는 DDR4 이전 세대의 값이고, D(16)는 실제 존재하지 않는 선택지입니다. BG 수가 늘어난 이유는 다른 BG로 명령을 분산할 때 더 짧은 tCCD_S 제약을 활용할 수 있어 대역폭 효율이 높아지기 때문입니다. DV 관점에서 BG 수를 잘못 알면 tCCD_L과 tCCD_S가 적용되는 경계를 잘못 모델링하여 timing coverage에 구멍이 생깁니다. (Ch02 §3.4)

</details>
:::tip[Q2. DDR5의 2-cycle command 에서 CS_n 의 동작 패턴은? `(Understand)`]
- A. CS_n LOW 한 cycle만
- B. CS_n LOW 가 2 cycles 연속
- C. CS_n HIGH 한 cycle 후 LOW
- D. CS_n 은 명령과 무관
:::
<details>
<summary>정답: B</summary>

**Why**: DDR5의 2-cycle command는 CS_n이 2 cycles 연속 LOW를 유지합니다. 이 패턴이 "2-cycle 명령의 시그너처"이며, monitor는 이것을 보고 두 번째 cycle의 CA[6:0]까지 캡처해야 명령을 완성할 수 있습니다. A(1 cycle LOW)는 NOP/DES 같은 1-cycle 명령의 패턴이고, C는 존재하지 않는 패턴입니다. D는 CS_n이 명령 선택과 무관하다는 잘못된 주장으로, CS_n은 rank 선택과 동시에 명령 경계를 정의하는 핵심 신호입니다. (Ch02 §3.3 + Ch05 §2.2)

</details>
:::tip[Q3. LPDDR4 의 die가 *기본적*으로 가지는 channel 수는? `(Remember)`]
- A. 1
- B. 2
- C. 4
- D. 8
:::
<details>
<summary>정답: B</summary>

**Why**: LPDDR4 die는 기본적으로 dual-channel 구조이며 각 채널은 16-bit 폭을 가집니다. A(1채널)는 LPDDR 이전 세대의 구조이고, C(4채널)나 D(8채널)는 LPDDR4 단일 die 구조에 해당하지 않습니다. 이 dual-channel 구조는 DV에서 중요한데, 두 채널이 독립적으로 동작하므로 각 채널에 대한 독립적인 training·refresh·명령 시퀀스 검증이 필요하고, 채널 간 간섭 시나리오도 coverage에 포함되어야 합니다. (Ch02 §4.2)

</details>
:::tip[Q4. LPDDR5의 Bank mode 선택지로 옳은 것을 모두 고르시오. `(Remember)`]
- A. 16 banks mode
- B. 8 banks mode
- C. BG mode
- D. 32 banks mode
:::
<details>
<summary>정답: A, B, C</summary>

**Why**: LPDDR5는 16 banks mode, 8 banks mode, Bank Group mode의 세 가지 bank 구성 중 하나를 MR로 선택합니다. 32 banks mode(D)는 LPDDR5 스펙에 존재하지 않습니다. 세 가지 mode가 존재하는 이유는 애플리케이션의 접근 패턴과 전력 목표에 따라 최적 구성이 다르기 때문입니다. DV에서는 세 가지 모드 모두를 coverage bin으로 확보해야 하며, 모드 전환 시나리오에서 timing 파라미터가 올바르게 변경되는지도 검증 대상입니다. (Ch02 §5.2)

</details>
## 단답형

:::tip[Q5. BG가 검증에서 중요한 이유를 timing 관점으로 설명하시오. `(Apply)`]
:::
<details>
<summary>예시 답안</summary>

같은 BG의 명령 간에는 `tCCD_L` (Long) 이, 서로 다른 BG의 명령 간에는 `tCCD_S` (Short) 이 적용. 같은 BG에서 *연속 RD/WR*은 더 긴 대기. DV는 BG-aware command sequencing을 stim에 반영해야 *모든 timing path*를 cover. (Ch02 §2.3)

</details>
:::tip[Q6. DDR5 16Gb x8 device의 어드레싱이 BG[2:0)+BA[1:0)+ROW[16:0)+COL[9:0) 일 때 총 cell 수와 cache line 단위로 환산했을 때의 총 cache lines를 계산하시오. (BL16, x8 = 16-byte/burst 가정, cache line = 64B) `(Apply)`]
:::
<details>
<summary>예시 답안</summary>

- 총 addressable beats: 2^3 × 2^2 × 2^17 × 2^10 = 2^32
- x8 device에서 BL16 한 access = 16 bytes
- cache line = 64B = 4× one device burst
- 따라서 device 한 개로 cache line 환산: 2^32 / 4 = 2^30 = **1G cache lines**
- 총 cell bit 수: 2^32 × 8 = 32 Gbit (가정상)

(실제 16Gb device 는 capacity 표기 기준. 위는 *어드레싱 계산* 연습.)

</details>
## 대표 문제

:::tip[Q7. controller IP가 BL16 burst를 발급하는데, *실제 cycle-by-cycle DQ 동작*을 추적. DDR5-6400, tCK=0.3125ns, CL=46 nCK. cycle 0에 RD 발급 시 BL16 동안 DQ에 데이터가 valid한 *절대 시간*과 *몇 ns 동안*인지 계산. `(Apply)`]
:::
<details>
<summary>풀이 (cycle dry-run)</summary>


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

</details>
---

