# Ch11 퀴즈 — DV 프로젝트 End-to-End

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> 퀴즈 인덱스</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">CH 11</span>
</div>

## 객관식

!!! question "Q1. DDR5 controller IP의 V-Plan에서 *가장 먼저* 정의해야 할 것은? `(Evaluate)`"
    - A. UVM TB 코드
    - B. DUT 정의 + 검증 목표 + Feature→검증 항목 매핑
    - C. SVA assertion
    - D. Coverage closure plan

??? answer "정답: B"
    **Why**: V-Plan은 검증의 지도입니다. 무엇을 검증할지(DUT 정의), 어느 수준까지 검증해야 하는지(검증 목표), 각 feature가 어떤 시나리오로 검증되는지(Feature→검증 항목 매핑)를 먼저 정의해야 합니다. A(UVM TB 코드 먼저)는 목적지 없이 달리는 것과 같습니다. C(SVA assertion 먼저)와 D(coverage closure plan 먼저)는 모두 V-Plan의 결과물이지 시작점이 아닙니다. DUT 정의 없이 TB나 SVA를 작성하면 검증 범위 내외가 불명확해져 쓸모없는 coverage와 누락된 coverage가 동시에 발생합니다. (Ch11 §11.1)

!!! question "Q2. UVM driver 가 DDR5 2-cycle command 발급 시 핵심 동작은? `(Understand)`"
    - A. 1 cycle 동안만 CA[6:0] 전송
    - B. 2 cycles 연속 CS_n LOW + 각 cycle 별 CA[6:0]
    - C. 4 cycles 전송
    - D. CA만 전송, CS_n은 무관

??? answer "정답: B"
    **Why**: DDR5 2-cycle command를 발급하려면 UVM driver가 2 cycles 연속으로 CS_n을 LOW로 유지하면서 각 cycle마다 서로 다른 CA[6:0] 인코딩을 구동해야 합니다. A(1 cycle만 CA 전송)는 명령의 절반만 전달하므로 ADDR이 불완전해집니다. C(4 cycles)는 DDR5 명령 구조에 맞지 않고, D(CS_n 무관)는 CS_n이 명령 경계와 rank 선택을 동시에 정의하므로 틀렸습니다. driver가 두 cycle을 정확히 구동하지 않으면 DRAM과 monitor가 명령을 잘못 해석해 후단 검증이 전부 무너집니다. (Ch11 §11.3.2)

!!! question "Q3. Rowhammer scenario sequence의 *핵심 단계*는? `(Apply)`"
    - A. Random WR 만 발급
    - B. Victim row에 known pattern WR → aggressor row hammer → victim 무결성 read 검증
    - C. PRE 만 반복
    - D. Refresh 명령 burst

??? answer "정답: B"
    **Why**: Rowhammer 시나리오는 먼저 victim row에 known pattern을 써 두고, aggressor row를 반복적으로 hammer(ACT-PRE)한 다음, victim row를 다시 읽어 원본 pattern이 유지되었는지 검증하는 흐름입니다. 이 과정에서 controller가 RAA threshold 도달 시 RFM 명령을 발급해 victim을 보호했는지를 함께 확인합니다. A(random WR만)는 의도적 hammer가 없어 disturbance를 유발하지 못합니다. C(PRE만 반복)는 ACT 없이는 row 활성화가 일어나지 않아 hammer가 성립하지 않습니다. D(refresh burst)는 오히려 disturbance를 완화하므로 공격 시나리오가 아닙니다. (Ch11 §11.5.3)

!!! question "Q4. LPDDR5 변형 적용 시 *추가/변경*되는 컴포넌트로 옳지 *않은* 것은? `(Remember)`"
    - A. WCK_t/c 핀 추가
    - B. CBT 시퀀스 추가
    - C. *Bank Group 4개로 축소*
    - D. Link ECC encoding 모델 추가

??? answer "정답: C"
    **Why**: LPDDR5 변형을 적용할 때 Bank Group이 4개로 "축소"된다는 C는 틀린 설명입니다. LPDDR5는 16 banks·8 banks·BG mode 중 하나를 MR로 선택하는 유연한 구조이지 고정 축소가 아닙니다. A(WCK_t/c 핀 추가)는 LPDDR5의 별도 데이터 클럭 도입에 따른 실제 변경이고, B(CBT 시퀀스 추가)는 LPDDR5의 command bus training 절차이며, D(Link ECC encoding 모델 추가)도 LPDDR5에서 실제로 필요한 컴포넌트이므로 모두 옳습니다. (Ch11 §11.7)

## 단답형

!!! question "Q5. SVA `bind` 모듈을 사용해 protocol checker를 부착할 때 *parameter화*가 중요한 이유는? `(Apply)`"

??? answer "예시 답안"
    - 같은 RTL이라도 *speed bin*에 따라 timing 값이 다름 (DDR5-4800 vs DDR5-6400 의 tRCD nCK 다름)
    - 같은 checker를 *parameter화* → 환경별로 *다른 값* 주입 가능
    - 새 speed grade 추가 시 *parameter 값만 변경* — checker 재작성 불필요
    - LPDDR5처럼 *DVFS 가 동적*인 경우, runtime parameter 변경까지 고려 (Ch11 §11.4)

!!! question "Q6. *Coverage closure*가 *Tier 3 (directed)*에서만 가능한 *그러나 Tier 2*에서는 부족한 이유는? `(Analyze)`"

??? answer "예시 답안"
    - Tier 2 (constrained-random)는 *대부분의 일반적 시나리오*를 cover
    - 그러나 *corner case*는 random으로 *희박* — 예: tRCD 정확히 min_spec 인 경우는 random에서 *거의 발생 안 함*
    - Tier 3은 *남은 hole을 정확히 겨냥* — directed로 specific bin hit
    - 즉, Tier 2 = breadth, Tier 3 = depth. 둘 다 필요. (Ch11 §11.6)

## 대표 문제

!!! question "Q7. DDR5 controller IP 검증의 *Coverage Report* 결과:

    ```
    cmd_cg:        100.0%
    timing_cg:      92.3%   HOLE: cp_gap.min_spec for tCCD_L
    mr_cg:          88.5%   HOLE: cp_mr.dfe_global[71..75]
    refresh_cg:     75.0%   HOLE: cp_raa.near_threshold * cp_rfm.issued
    training_cg:   100.0%
    ecc_cg:         87.5%   HOLE: cp_err.double_bit_detected
    OVERALL: 90.5%  [GOAL: 95%]
    ```

    Tier 3 단계에서 어떤 *directed test*를 작성해 holes를 채울 것인가? 각 hole 마다 *test scenario + 핵심 sample point*를 명시. `(Apply, Evaluate)`"

???+ answer "풀이 (Coverage hole filling plan)"

    **Hole 1: `cp_gap.min_spec for tCCD_L`**

    - Test: `test_tccd_l_min_spec`
    - 시나리오: 같은 BG (예: BG=2) 의 두 bank (BA=0, BA=1) 에 *back-to-back RD* 발급, 사이 gap = tCCD_L 정확히
    - Sample point: `timing_corner_cg.cx_param_gap` 에 `("tCCD_L", min_spec)` bin sample
    - 추가: tCCD_L 의 *경계 직전 (tCCD_L-1)* 도 directed test → SVA fail 확인 (negative test)

    **Hole 2: `cp_mr.dfe_global[71..75]`**

    - Test: `test_dfe_global_walk`
    - 시나리오: Init 후 MR70~MR75 (DFE global settings) 에 *다양한 값 write* → MRR로 readback 확인
    - RAL을 통해: `ral.MR71.set(8'hAA); ral.MR71.update(status);` 반복 (5개 MR 각각)
    - Sample point: `mr_walk_cg` 에 각 MR write event sample
    - 함정: DFE는 *training과 함께 동작* — 정상 training 후에만 enable 가능 — test order 주의

    **Hole 3: `cp_raa.near_threshold * cp_rfm.issued`**

    - Test: `test_rfm_near_threshold`
    - 시나리오: ACT를 *정확히 RAA threshold 직전* (예: 798/800) 까지 발급 후 *마지막 1~2번*의 ACT로 threshold 도달 → controller가 RFM 발급하는지 monitor
    - Sample point: `refresh_cg.cx_raa_rfm` 에 `(near_threshold, issued)` 와 `(at_threshold, issued)` 모두 sample
    - 추가: *overflow_zone* 도 검증 — controller가 *반드시* RFM 발급. `ignore_bins illegal` 도 implicit 검증

    **Hole 4: `cp_err.double_bit_detected`**

    - Test: `test_ecc_double_bit_inject`
    - 시나리오: 알려진 data WR → backdoor로 *2-bit flip* → RD → ECC가 *detect* (correct 못함) 확인
    - Sample point: `ecc_cg` 에 `double_det` bin sample. + MR16~19 (Row Error Max), MR20 (Error Count) update 확인.
    - 추가 시나리오:
      - 2-bit flip이 *정확히 2 bit*인 경우 (single)
      - 3+ bit flip — 일부 ECC는 *detect 못함* — uncorrectable propagation 검증

    **종합 — 추가 회귀 항목**

    1. 위 4개 directed test 추가 후 *Tier 2 regression* 재실행 → coverage 95% 도달 확인
    2. 각 directed test 의 *seed=0*은 영구 회귀 풀에 추가 (deterministic baseline)
    3. *남은 hole*이 있다면 *waive*로 처리 — waive 사유를 verification plan에 명시
    4. Coverage closure report 생성 → V-Plan과 함께 sign-off review에 제출

    **시간 추정**
    - Hole 1: 1 day (test 작성 + 검증)
    - Hole 2: 2 days (DFE training 의존성 + 5 MR walk)
    - Hole 3: 3 days (RAA 추적 + RFM 응답 확인 + threshold tuning)
    - Hole 4: 2 days (ECC inject + multi-bit error report 검증)
    - 총: ~8 days for tier 3 closure

    **DV 시사점**
    - Coverage hole의 *root cause*는 보통 *3가지 중 하나*:
      1. Random stim의 *constraint 부족* → 그 case가 *불가능*하게 random
      2. Bin이 *너무 narrow* (예: min_spec 이 *exact 1 nCK*) — 의도적 directed 필요
      3. *Feature 자체 미사용* — 사용 안 한 feature는 *waive 또는 사용해야*
    - 각 hole 분석 → root cause 파악 → directed test 또는 waive 결정

---

<div class="chapter-nav">
  <a class="nav-prev" href="../ch10_quiz/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch10 퀴즈</div>
  </a>
  <a class="nav-next" href="../../">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">🏠 코스 홈</div>
  </a>
</div>
