# Ch04 퀴즈 — Mode Register 깊이 분석

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="./"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> 퀴즈 인덱스</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">CH 04</span>
</div>

## 객관식

!!! question "Q1. DDR5의 MR 영역 크기는? `(Remember)`"
    - A. MR0~MR6 (7개)
    - B. MR0~MR15 (16개)
    - C. MR0~MR63 (64개)
    - D. MR0~MR254 (255개)

??? answer "정답: D"
    **Why**: DDR5는 MR 공간이 *최대 MR254*까지 확장. DDR4는 MR0~MR6 (7개)였음. DCA per-DQ + DFE per-tap 으로 영역이 커짐. (Ch04 §1)

!!! question "Q2. MRR (Mode Register Read)이 *직접 명령*으로 지원되기 시작한 표준은? `(Remember)`"
    - A. DDR3
    - B. DDR4
    - C. DDR5
    - D. LPDDR4

??? answer "정답: C (DDR5)"
    **Why**: DDR4는 MPR(Multi-Purpose Register)을 통한 *간접* 방식. DDR5부터 *MRR이 직접 명령*. LPDDR4/5는 MRR을 가짐. (Ch04 §1.1)

!!! question "Q3. RFM 관련 MR로 옳은 것을 모두 고르시오. `(Remember)`"
    - A. MR58 (Refresh Management)
    - B. MR59 (DRFM, ARFM, RFM RAA Counter)
    - C. MR60 (Partial Array Self Refresh)
    - D. MR4 (Refresh Settings)

??? answer "정답: A, B, C, D"
    **Why**: 모두 refresh 관련. MR4가 기본 refresh, MR58~60이 RFM/DRFM/PASR. (Ch04 §2.2)

!!! question "Q4. *Init-only* MR을 *런타임에 변경*하려는 시도에 대한 적절한 대응은? `(Evaluate)`"
    - A. DRAM이 무시하므로 SVA 불필요
    - B. SVA로 즉시 catch — assertion fail
    - C. controller가 자동으로 reset
    - D. Warning만 출력

??? answer "정답: B"
    **Why**: init-only MR (예: MR3, MR13)을 runtime에 변경하면 *spec violation*. 시뮬레이션은 *통과*할 수 있지만 silicon 동작 미정의. SVA로 *즉시* catch해야 함. (Ch04 §5.2)

## 단답형

!!! question "Q5. UVM RAL을 DRAM MR에 적용했을 때 얻는 *3가지 이점*을 들어라. `(Apply)`"

??? answer "예시 답안"
    1. **Mirror value 자동 추적** — 코드에서 *직접* `ral.MR0.cl.get()` 같이 현재 값 조회 가능
    2. **Frontdoor/Backdoor 분리** — 일반 검증은 frontdoor, 빠른 setup은 backdoor
    3. **Built-in sequences** — `uvm_reg_hw_reset_seq`, `uvm_reg_bit_bash_seq` 등 자동 verification 시퀀스 활용 (단, MR이 일반 register와 다르므로 일부는 custom)
    4. (추가) Coverage 자동 적용 — `add_coverage(UVM_CVR_ALL)` (Ch04 §4.1, §4.2)

!!! question "Q6. MR access coverage를 작성할 때 *카테고리화*가 왜 중요한가? `(Analyze)`"

??? answer "예시 답안"
    - MR이 *250+개*이므로 *각 MR 1개씩* bin을 만들면 cover 보고가 폭발
    - 우선순위 카테고리(basic/ecc/odt/dca/refresh/dfe/...)로 묶으면 *의미 있는 측정* 가능
    - 카테고리 cross로 *기능적 통합*을 검증: 예) `cp_mr.refresh × cp_rw.write` — 모든 refresh MR이 *적어도 한 번 write* 되었는지 (Ch04 §4.4)

## 대표 문제

!!! question "Q7. DDR5 controller가 MR4=8'b001_01_010 을 MRW 한 직후, *후속 RD/WR이 normal temp에서는 정상*이지만 *extended temp에서 timing violation*이 발생한다면 root cause는 무엇이고 어떻게 추적하는가? `(Analyze, Evaluate)`"

???+ answer "풀이 (debug 사고 + 검증 보완)"

    **Step 1 — MR4 비트 해석** (Ch04 §3.1 표 기준, *학습용 모형*)
    - OP[2:0]=010 → Refresh Range 의 *어떤 모드* — extended temp일 가능성
    - OP[4:3]=01 → tRFC Mode 1
    - OP[7:5]=001 → tREFI mode (variable)

    **Step 2 — Symptom 분석**
    - Normal temp에서 OK → MR4 자체는 *문자 그대로* 적용됨
    - Extended temp에서 fail → tREFI를 *절반*으로 줄였어야 하는데 줄이지 않음
    - → Controller의 *temperature sensor 입력 처리*에 문제?
    - → 또는 *MR4의 refresh_range 비트*를 controller가 *읽지 않음*?

    **Step 3 — 추적 절차**
    1. RAL backdoor로 `ral.MR4.refresh_range.get()` → DRAM internal value 일치 확인
    2. Controller RTL의 *MR4 refresh_range 필드* 디코드 신호 trace → temperature mode 전환 시점에 *실제로 변경*되는지
    3. Refresh interval logic의 *count_target*이 normal vs extended에서 *다르게 설정*되는지
    4. timing checker 자체가 *temperature-aware*인지 (단순히 7.8us 고정이면 false fail)

    **Step 4 — 가능 root cause**
    - Controller가 MR4 의 refresh_range 비트를 *디코드는 하지만 적용 안 함*
    - Or 적용은 하지만 *temperature transition 시점 race*
    - Or DRAM model의 timing이 extended temp에서 *더 엄격*하게 평가됨
    - Or testbench의 timing checker가 *spec과 다른* 임계치

    **Step 5 — 검증 보완**
    1. directed test `test_mr4_extended_temp_walk`: MR4를 normal → extended로 전환 후 *refresh interval 측정*. 절반이 되는지 확인.
    2. covergroup `refresh_range_cg`: normal_temp / extended_temp 각각 bin
    3. SVA `a_trefi_extended_temp`: refresh_range == extended일 때 *tREFI가 절반*인지 동적 평가
    4. directed test `test_mr4_race_condition`: temperature transition 직전/직후에 *refresh 발급* — race 검출

    **DV 시사점**
    - MR이 *동작 모드를 바꾸는* 경우 (이 사례), MR 자체의 write/read 검증만으로는 부족
    - *MR 값에 따른 후속 동작*까지 *별도 시나리오*로 검증해야 함
    - "MR mirror = DRAM internal" 확인은 *필요조건*이지 *충분조건*이 아님

---

<div class="chapter-nav">
  <a class="nav-prev" href="ch03_quiz/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch03 퀴즈</div>
  </a>
  <a class="nav-next" href="ch05_quiz/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch05 퀴즈</div>
  </a>
</div>
