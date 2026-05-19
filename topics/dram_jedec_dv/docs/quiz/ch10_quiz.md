# Ch10 퀴즈 — DV Methodology 통합

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="./"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> 퀴즈 인덱스</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">CH 10</span>
</div>

## 객관식

!!! question "Q1. Memory reference model의 *권장 전략*은? `(Evaluate)`"
    - A. Cycle-accurate full timing
    - B. Functional (mem[addr]=data) + 별도 SVA timing checker
    - C. Hybrid
    - D. SystemC TLM 만 사용

??? answer "정답: B"
    **Why**: Cycle-accurate은 *느리고 controller IP timing model에 의존*. Functional + SVA 분리가 *빠르고 깔끔*. (Ch10 §2.1)

!!! question "Q2. Coverage 6 카테고리에 *포함되지 않는* 것은? `(Remember)`"
    - A. Command
    - B. Timing
    - C. *Layout (physical floorplan)*
    - D. Training

??? answer "정답: C"
    **Why**: Layout/floorplan은 physical design 영역 — DRAM 검증 coverage에는 포함 X. 6 카테고리는 command/timing/MR/training/refresh/ECC. (Ch10 §3)

!!! question "Q3. SVA `bind` 의 *주 이점*은? `(Understand)`"
    - A. 실행 속도 향상
    - B. RTL 소스 *수정 없이* checker 부착
    - C. Coverage 자동 생성
    - D. 시뮬레이션 라이센스 절약

??? answer "정답: B"
    **Why**: bind는 elaboration 시점에 모듈을 부착 — RTL 자체는 *변경 안 됨*. checker 추가/제거가 깔끔. (Ch10 §4.4)

!!! question "Q4. 3-Tier regression의 *Tier 2 단계*는? `(Remember)`"
    - A. Smoke directed (seed=0)
    - B. Constrained-random (100 seeds × multiple tests)
    - C. Coverage hole directed
    - D. FPGA emulation

??? answer "정답: B"
    **Why**: Tier 1 = smoke, Tier 2 = constrained-random, Tier 3 = hole filling. (Ch10 §5.1)

## 단답형

!!! question "Q5. *SVA 3 분류* (timing / command order / training)에 각각 한 예씩 들라. `(Apply)`"

??? answer "예시 답안"
    - **Timing**: `a_trcd` — ACT 후 tRCD 미만 cycle에 RD/WR 발급 시 fail
    - **Command order**: `a_act_after_act_needs_pre` — 같은 bank 에 PRE 없이 ACT 두 번 fail
    - **Training protocol**: `a_no_traffic_during_wck2ck` — WCK2CK Leveling 동안 RD/WR 발급 시 fail
    (Ch10 §4)

!!! question "Q6. *Coverage weighting* 이 organization에 따라 다를 수 있는 이유는? `(Evaluate)`"

??? answer "예시 답안"
    - Sign-off goal이 *조직마다 다름* — 일부는 *high availability* (ECC weight 높음), 일부는 *low latency* (timing weight 높음)
    - 과거 *silicon escape* 경험 — 특정 카테고리에서 escape 발생했다면 *그 카테고리 weight 상향*
    - 시장 segment — 모바일 vs 서버 vs 자동차 — 각자 priority 다름
    - Project schedule — coverage closure 일정에 따라 *우선순위 조정*
    (Ch10 §3.7)

## 대표 문제

!!! question "Q7. 검증 환경에서 controller가 *tRCD-1 cycles 만에 RD 발급*했는데 DRAM model이 *invalid data 반환*. *시뮬레이션은 pass*하지만 silicon에서 fail. 어떻게 *각 컴포넌트의 책임을 재분배*해서 이런 false pass를 막을 수 있는가? `(Analyze, Evaluate)`"

???+ answer "풀이 (책임 재분배 + 개선안)"

    **Step 1 — 현재 상태의 책임 분석**

    | 컴포넌트 | 현재 동작 | 문제 |
    |---|---|---|
    | DRAM model | RD 수락 + invalid data 반환 | *너무 관대* |
    | Monitor | RD transaction publish | timing 검증 X (capture만) |
    | Scoreboard | invalid data를 *write data와 비교* | 우연히 일치하면 *false pass* |
    | SVA | tRCD 위반 catch | *제대로 작성되었으면* fail. 누락 시 못 잡음 |
    | Reference model | bank state 추적 | timing X |

    **Step 2 — 개선된 책임 분배**

    1. **SVA timing checker** (1차 방어선)
       - `a_trcd` assertion이 *반드시* 작성됨
       - RD 명령 발급 시점이 ACT + tRCD 미만이면 *즉시 uvm_error*
       - bind 모듈로 RTL에 부착 → 환경에 따라 enable/disable

    2. **DRAM model** (2차 방어선)
       - Timing 위반 *수락 거부* — *X data*를 반환 (또는 명령 ignore)
       - UVM_WARNING 출력 — fail은 *SVA가 1차*, model은 *증거 보조*

    3. **Scoreboard** (3차 방어선)
       - RD data가 X 면 *비교 skip + warning*
       - data가 X도 아니고 *불일치*면 uvm_error
       - *valid data only* 검증

    4. **Reference model**
       - 그대로 — functional 만

    5. **Monitor**
       - 그대로 — capture 만 (timing은 SVA의 책임)

    **Step 3 — 개선된 검증 시퀀스**

    1. Driver가 tRCD-1 cycle에 의도적으로 RD 발급 (테스트)
    2. SVA `a_trcd` 즉시 fail → uvm_error → simulation fail 표시
    3. DRAM model이 *X data* 반환
    4. Scoreboard가 X 보고 *비교 skip*
    5. 시뮬레이션이 *명확한 fail 메시지*로 종료
    6. Log 분석: 정확한 cycle + 위반된 timing parameter

    **Step 4 — 시스템적 보완**

    1. **SVA 작성 완전성 검토**: Ch06의 핵심 timing 9개 모두 SVA 작성. Code review checklist에 *모든 timing parameter에 대한 SVA 존재*.
    2. **DRAM model strict mode**: model에 `STRICT_TIMING_CHECK = 1` flag. enabled 시 위반을 *수락 거부*.
    3. **Scoreboard X handling**: `===` 비교 + X 발생 시 *반드시 warning*. 조용히 통과 방지.
    4. **Coverage hole 모니터링**: `timing_corner_cg.cx_param_gap[tRCD][min_spec]` bin이 *반드시 hit* — directed test로 보장.
    5. **Regression seed log**: SVA fail 시 *seed 영구 기록* → 매 회귀에 추가. 같은 bug 재발 방지.

    **DV 시사점**
    - "테스트가 통과한다" 와 "버그가 없다" 는 *다르다*. SVA가 *없으면* false pass 가능.
    - 각 컴포넌트가 *자기 영역*을 책임지고, *경계*에서 명시적 검증 (Defense in depth).
    - Silicon escape의 90%가 *DV의 coverage hole + 부족한 SVA* 에서 발생 — 책임 분배 자체를 *시스템 수준*에서 검토.

---

<div class="chapter-nav">
  <a class="nav-prev" href="ch09_quiz/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch09 퀴즈</div>
  </a>
  <a class="nav-next" href="ch11_quiz/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch11 퀴즈</div>
  </a>
</div>
