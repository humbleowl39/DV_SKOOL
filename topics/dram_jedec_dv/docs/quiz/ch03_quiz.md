# Ch03 퀴즈 — 초기화·Reset·Power 시퀀스

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="./"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> 퀴즈 인덱스</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">CH 03</span>
</div>

## 객관식

!!! question "Q1. DDR4 의 MR programming 권장 순서는? `(Remember)`"
    - A. MR0 → MR1 → MR2 → MR3 → MR4 → MR5 → MR6
    - B. MR3 → MR6 → MR5 → MR4 → MR2 → MR1 → MR0
    - C. MR6 → MR5 → MR4 → MR3 → MR2 → MR1 → MR0
    - D. 순서 무관

??? answer "정답: B"
    **Why**: JESD79-4D §3.3.1 이 명시하는 순서. 마지막에 MR0 (BL, CL, DLL reset). (Ch03 §2.1)

!!! question "Q2. DDR5 power-up에서 LPDDR4/5와 *다른* 단계는? `(Understand)`"
    - A. RESET_n LOW
    - B. CS Training
    - C. CKE HIGH
    - D. MRW

??? answer "정답: B"
    **Why**: DDR5는 *CS training*이 power-up에 포함 (LPDDR4/5는 별도 CBT). (Ch03 §3.2)

!!! question "Q3. LPDDR5의 dual VDD2 rail (Vdd2H/Vdd2L) 의 도입 이유는? `(Understand)`"
    - A. 보안 강화
    - B. 전력 효율 (DVFS 지원)
    - C. ECC 보호 강화
    - D. PoP 패키지 호환

??? answer "정답: B"
    **Why**: LPDDR5의 DVFS에서 *주파수에 따라 다른 전압*이 필요 — dual rail로 전환 빠름. (Ch03 §5.1)

!!! question "Q4. Power-up 후 CKE=0 상태에서 controller가 MRW를 발급하면? `(Analyze)`"
    - A. 정상 동작
    - B. DRAM이 명령 수락하지만 잘못 해석할 수 있음
    - C. 자동으로 재시도
    - D. ALERT_n 즉시 발생

??? answer "정답: B"
    **Why**: CKE=0 동안 DRAM은 *Power-Down 또는 Self-Refresh* — 일반 명령 수락 안 함. 그러나 *조용히 drop* 되어 시뮬레이션은 *통과*하면서 silicon에서 fail. SVA로 *catch* 필요. (Ch03 §8 풀이)

## 단답형

!!! question "Q5. tINIT3 (RESET_n LOW pulse) 가 일정 시간 이상 필요한 이유는? `(Understand)`"

??? answer "예시 답안"
    Voltage rail이 *충분히 안정*되고 *내부 회로*가 reset된 후 *deassert* 되어야 안정 동작. *최소 200us*는 internal reset 전파 + voltage ramp 완료를 보장하기 위한 spec margin. tINIT3 미만 pulse는 *DRAM이 응답하지 않거나 미정의 동작* 가능. (Ch03 §3.3)

!!! question "Q6. Init sequence를 UVM phase로 매핑할 때, *configure_phase* 에 무엇을 두는가? `(Apply)`"

??? answer "예시 답안"
    - **configure_phase**: Initial MR Write 시퀀스 — DDR5의 경우 *CS training → PDA → 우선순위 MR write*
    - 이 phase에서는 *DRAM이 이미 RESET 후 CKE HIGH* 상태가 보장됨 (pre_configure_phase 에서)
    - 후속 `post_configure_phase`에서 ZQCL + training 진입 (Ch03 §6.1)

## 대표 문제

!!! question "Q7. Controller가 RESET_n=LOW 동안 *MRW 명령을 발급*하는 *코드 버그*가 있다. (1) 시뮬레이션에서 어떤 증상으로 나타날까? (2) 어떻게 root cause를 잡을 수 있는가? (3) SVA로 *prevention*하는 방법? `(Analyze, Evaluate)`"

???+ answer "풀이 (debug 사고 + SVA 작성)"

    **(1) 시뮬레이션 증상**
    - DRAM이 RESET 중 → *어떤 명령도 받지 않음*. MRW도 drop.
    - 시뮬레이션은 *fail 없이 진행* — 다음 *configure_phase* 에서 *유효한* MRW 발급으로 정상 처리될 수 있음
    - 그러나 만약 controller가 "이미 MR이 설정되었다"고 *가정* 하면 → 잘못된 default로 동작 → 후속 traffic에서 *간헐적 fail*

    **(2) Root cause 추적**
    - Symptom: 간헐적 RD/WR mismatch 또는 DRAM 미응답
    - Step 1: log에서 *MRW timestamp* 확인 — 만약 RESET_n LOW 구간에 있으면 *그것이 문제*
    - Step 2: scoreboard에서 *MR mirror value*가 *DRAM internal MR*과 일치하는지 RAL backdoor로 비교 → 만약 mirror만 update되고 DRAM은 *default* 그대로면 *MRW drop* 확인됨
    - Step 3: monitor가 *MRW 발급 시점의 RESET_n 상태*도 capture하도록 보완

    **(3) SVA prevention**
    ```systemverilog
    // 출처: Ch03 §6.3 + Ch10
    property p_no_cmd_during_reset;
        @(posedge clk)
        !(cmd_decoded inside {CMD_DES, CMD_NOP}) |-> reset_n == 1'b1;
    endproperty
    a_no_cmd_during_reset: assert property (p_no_cmd_during_reset)
        else `uvm_error("SVA_INIT",
            $sformatf("Command %s issued during RESET_n LOW", cmd_decoded.name()))
    ```

    **DV 시사점**
    - Init 관련 버그는 *조용히 발생*하는 경우가 많음 — SVA 없으면 *다음 phase의 mismatch* 로만 드러남
    - 매 milestone마다 *init phase trace 검토* 권장
    - covergroup `init_violation_cg` 에 *RESET_n LOW 동안의 명령 발급* bin (0개여야 함)

---

<div class="chapter-nav">
  <a class="nav-prev" href="ch02_quiz/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch02 퀴즈</div>
  </a>
  <a class="nav-next" href="ch04_quiz/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch04 퀴즈</div>
  </a>
</div>
