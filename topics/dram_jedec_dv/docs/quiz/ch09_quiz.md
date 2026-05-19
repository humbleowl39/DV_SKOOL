# Ch09 퀴즈 — 신뢰성·ECC·CRC·PPR

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="index.md"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> 퀴즈 인덱스</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">CH 09</span>
</div>

## 객관식

!!! question "Q1. DDR5 *Transparency ECC* 가 보호하는 영역은? `(Understand)`"
    - A. DRAM ↔ Controller 링크
    - B. DRAM 셀 내부 (cap leakage, soft error)
    - C. PCB trace
    - D. 외부 cache

??? answer "정답: B"
    **Why**: DDR5 on-die ECC는 DRAM array 내부의 데이터 정정. 링크 보호는 CRC. (Ch09 §3.1)

!!! question "Q2. LPDDR5 *Link ECC* 가 보호하는 영역은? `(Understand)`"
    - A. DRAM 셀
    - B. DRAM ↔ Controller DQ 링크
    - C. Controller 내부 cache
    - D. Self refresh 동안

??? answer "정답: B"
    **Why**: LPDDR5 Link ECC는 DQ pin 상의 *링크 신호*를 보호. DDR5 transparency ECC와는 *보호 대상 다름*. (Ch09 §4.1)

!!! question "Q3. *hPPR vs sPPR* 의 핵심 차이는? `(Understand)`"
    - A. hPPR은 fast, sPPR은 slow
    - B. hPPR은 *영구 (fuse)*, sPPR은 *power-cycle까지만*
    - C. hPPR은 controller가, sPPR은 DRAM이 발급
    - D. 동일 기능

??? answer "정답: B"
    **Why**: hPPR = hard = fuse 변경 = 영구. sPPR = soft = 일시적. (Ch09 §2.3)

!!! question "Q4. CRC가 *보호하는 데이터*는? `(Remember)`"
    - A. Write data
    - B. Read data
    - C. Both
    - D. Mode register

??? answer "정답: A"
    **Why**: DDR4/DDR5의 CRC는 *Write data*에만 표준화. Read 시에는 별도 보호 메커니즘. (Ch09 §5)

## 단답형

!!! question "Q5. DDR5 Transparency ECC가 *controller에 투명*하다면, controller는 ECC 동작을 *어떻게* 알 수 있나? `(Apply)`"

??? answer "예시 답안"
    - Controller가 *MR read*로 통계 조회 가능
    - MR20 (Error Count) — 누적 error 개수
    - MR16~19 — 가장 많이 에러 발생한 row 주소 + count
    - MR15 — threshold 도달 시 controller 알림 가능
    - 즉 *런타임 처리는 투명* 이지만 *통계는 노출* (Ch09 §3.3)

!!! question "Q6. *Guard Key* 메커니즘이 PPR에 도입된 이유와 DV 검증 방법은? `(Evaluate)`"

??? answer "예시 답안"
    **도입 이유**
    - PPR은 *영구* 동작 (특히 hPPR) — 잘못된 row를 *spare로 redirect* 하면 *복구 불가*
    - 우발적 PPR 명령 (예: 노이즈, soft error로 인한 명령 corruption) 으로 인한 *실수* 방지

    **DV 검증 방법**
    - covergroup `ppr_cg.cx_full` 에 *guard key correct/incorrect* × *PPR pass/fail* cross
    - `ignore_bins illegal_bypass`: guard key incorrect 인데 PPR이 success = bug
    - directed test `test_ppr_guard_key_incorrect`: 의도적으로 잘못된 key 발급 → PPR fail 확인
    - directed test `test_ppr_guard_key_correct`: 정상 key 발급 → PPR success (Ch09 §6.2, §10 풀이)

## 대표 문제

!!! question "Q7. LPDDR5 Link ECC 가 8-bit data + 4-bit parity 의 SECDED 동작이라 가정. data=0xA5, parity=0x6, 전송 후 DRAM이 수신한 값이 *bit 0 flip* 된 상태. (1) ECC가 어떻게 정정하는가? (2) 2-bit flip 시 어떻게 다르게 동작? (3) DBI와 함께 enabled 일 때 *순서* 가 왜 중요한가? `(Analyze, Evaluate)`"

???+ answer "풀이 (Link ECC 동작 + DBI 순서)"

    **(1) Single bit error 정정**

    SECDED 일반 원리 *(추론 — 실제 LPDDR5 매트릭스는 §7.7.8 참조)*:
    - DRAM이 received [data | parity] 에 H matrix 곱해 syndrome 계산
    - syndrome ≠ 0 → 어떤 비트 flip인지 lookup table로 결정
    - bit 0 의 syndrome pattern → bit 0 flip 보정 → 원본 data 복원

    동작:
    - Encoder (controller): data=0xA5 → parity=0x6 (matrix에 의해)
    - Transmission: bit 0 flip → received data=0xA4
    - Decoder (DRAM): syndrome = H × [received_data | received_parity] → bit 0 의 syndrome 패턴 일치 → 정정 → 0xA5 복원
    - DRAM이 *epoch error report*에 single-bit 발생 기록

    **(2) Two bit error 동작**

    - bit 0 + bit 3 동시 flip → received data=0xAD (또는 다른 값)
    - Decoder syndrome 계산 → *어떤 single-bit pattern과도 일치 X* → uncorrectable
    - DRAM이 *uncorrectable detection* — epoch error report에 multi-bit error 기록
    - data는 *정정되지 않은 값 반환* — controller가 *fail 시그널* 받고 system-level recovery 필요

    **(3) DBI 순서 (§7.7.8.6)**

    DBI(Data Bus Inversion)와 Link ECC가 함께 enabled 인 경우:

    **순서 옵션 A: data → ECC → DBI** (controller 측)
    - data → parity 추가 → DBI 적용 → DQ 전송
    - DRAM 측: DQ → DBI 역적용 → ECC decode

    **순서 옵션 B: data → DBI → ECC**
    - data → DBI 적용 → parity는 *DBI 적용 후* data 기준 계산 → 전송
    - DRAM 측: DQ → ECC decode → DBI 역적용

    이 두 순서는 *전혀 다른 parity 값*을 만듭니다. spec이 *어느 한 순서를 강제*. 만약 controller 와 DRAM 이 *다른 순서*로 처리하면:
    - 정상 데이터인데 ECC가 *항상 error 검출* → false positive
    - 또는 ECC가 *진짜 error를 못 봄* → false negative
    - **둘 다 silicon에서 *간헐적이고 추적 어려운 fail*** 발생

    **DV 검증 방법**
    - Scoreboard에서 *spec 순서*로 정확히 모델링 (encoder/decoder 별도 구현)
    - directed test `test_link_ecc_dbi_order` — DBI on/off × ECC on/off 4 가지 조합 검증
    - covergroup `link_ecc_dbi_cg`: 두 feature의 enable 상태 × error injection 결과
    - SVA: controller가 발급하는 parity가 *spec 행렬* 출력과 일치하는지

    **DV 함의**
    - 두 feature가 *독립적*으로 보여도 *상호작용*이 spec에 명시 — 검증 순서를 *정확히* 따라야 함
    - 함정: *single feature 검증*은 통과하는데 *둘 다 enable* 했을 때만 fail — *cross coverage*에서 잡힘
    - LPDDR5 sign-off에 *DBI × ECC × WCK enable 모든 조합* 검증이 권장

---

<div class="chapter-nav">
  <a class="nav-prev" href="ch08_quiz.md">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch08 퀴즈</div>
  </a>
  <a class="nav-next" href="ch10_quiz.md">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch10 퀴즈</div>
  </a>
</div>
