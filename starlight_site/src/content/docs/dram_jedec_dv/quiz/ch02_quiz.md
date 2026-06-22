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

**Why**: DDR5는 device당 8 Bank Group을 가집니다(×4/×8 = 8 BG×4 = 32뱅크). DDR4가 4 BG였으므로 두 배로 늘어났습니다. A(2)나 B(4)는 DDR4 이전 세대의 값이고, D(16)는 DDR5 BG 수가 아닙니다. BG 수가 늘어난 이유는 다른 BG로 명령을 분산할 때 더 짧은 tCCD_S 제약을 활용할 수 있어 대역폭 효율이 높아지기 때문입니다. 참고로 LPDDR5는 BG 수가 고정이 아니라 MR로 BG 모드(4 BG×4=16뱅크)/8B 모드(8뱅크)/16B 모드(16뱅크) 중 하나를 선택합니다. DV 관점에서 BG 수를 잘못 알면 tCCD_L과 tCCD_S가 적용되는 경계를 잘못 모델링하여 timing coverage에 구멍이 생깁니다. (Ch02 §3.4)

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
:::tip[Q6. LPDDR5 16Gb x16 die가 BG mode(BG[1:0)+BA[1:0)=16뱅크)로 동작하고 어드레싱이 BG[1:0)+BA[1:0)+ROW[15:0)+COL[9:0) 일 때 총 addressable beat 수와 cache line 단위 환산값을 계산하시오. (BL16, x16 = 32-byte/burst 가정, cache line = 64B) `(Apply)`]
:::
<details>
<summary>예시 답안</summary>

- 총 addressable beats: 2^2 × 2^2 × 2^16 × 2^10 = 2^30
- x16 die에서 BL16 한 access = 32 bytes
- cache line = 64B = 2× one die burst
- 따라서 die 한 개로 cache line 환산: 2^30 / 2 = 2^29 = **512M cache lines**
- 총 cell bit 수: 2^30 × 16 = 16 Gbit (가정상)

(LPDDR5는 BG/8B/16B 모드를 MR로 선택. 위 계산은 BG mode 기준 *어드레싱 계산* 연습이며, 8B/16B 모드에서는 BG 비트가 BA 비트로 재배치됨.)

</details>
## 대표 문제

:::tip[Q7. LPDDR5 controller IP가 BL16 burst를 발급하는데, *실제 DQ 동작*을 추적. WCK:CK=4:1 gear, tWCK=0.3125ns(WCK 기준), CK는 4×느림. CL=46 tCK(여기서 tCK=CK 주기=1.25ns). CK cycle 0에 RD 발급 시 BL16 동안 DQ가 valid한 *절대 시간*과 *몇 ns 동안*인지 계산. `(Apply)`]
:::
<details>
<summary>풀이 (WCK/CK dry-run)</summary>


**Step 1 — 명령 발급 시점**
- LPDDR5 명령은 CK(저속, 차동) 기준으로 발급. RD는 CA[6:0] 다중사이클 인코딩
- 명령 *완료* = RD 인코딩 끝 (CK cycle 0 기준으로 잡음)

**Step 2 — Data 도착 시점**
- CL = 46 tCK(CK 주기) → 명령 발급 후 46 × 1.25ns = **57.5 ns** 후 첫 beat
- (데이터 전송 자체는 고속 WCK 도메인에서 일어남 — CL은 CK 기준으로 카운트)

**Step 3 — BL16 의 burst 지속 시간**
- BL16 = 16 beats, 데이터는 WCK의 양 edge로 전송 (DDR)
- 16 beats = 8 WCK cycle = 8 × 0.3125ns = **2.5 ns**

**Step 4 — Burst 종료 시점**
- 종료 = 57.5 + 2.5 = **60.0 ns**

**Step 5 — DV 시사점**
- Monitor의 *DQ sample window* = 57.5ns ~ 60.0ns, 단 sampling 기준은 **WCK** (CK 아님)
- WCK는 RD 이전에 toggle 시작해야 함 — WCK preamble/CAS-WCK-Sync 구간이 CL 직전에 존재
- gear가 WCK:CK=2:1로 바뀌면 같은 BL16이라도 WCK 주기가 달라져 burst 절대 시간이 변함 → DVFSC gear 전환마다 재계산 + WCK2CK 재정렬
- SVA: WCK가 CK와 정렬(WCK2CK leveling 완료)된 뒤에만 RD data 유효 — gear별로 parameter화

</details>
---

