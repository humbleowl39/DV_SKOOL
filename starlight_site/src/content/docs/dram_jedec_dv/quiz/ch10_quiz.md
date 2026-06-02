---
title: "Ch10 퀴즈 — DV Methodology 통합"
---

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> 퀴즈 인덱스</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">CH 10</span>
</div>

## 객관식

:::tip[Q1. Memory reference model의 *권장 전략*은? `(Evaluate)`]
- A. Cycle-accurate full timing
- B. Functional (mem[addr]=data) + 별도 SVA timing checker
- C. Hybrid
- D. SystemC TLM 만 사용
:::
<details>
<summary>정답: B</summary>

**Why**: Functional reference model(mem[addr]=data 수준)에 별도 SVA timing checker를 조합하는 방식이 최적입니다. Cycle-accurate 방식(A)은 시뮬레이션이 느려지고 컨트롤러의 timing model에 의존도가 높아져 false fail 가능성이 생깁니다. Hybrid(C)는 명확한 정의가 없으며 두 방식의 단점을 모두 가질 수 있습니다. SystemC TLM만 사용(D)하면 cycle 단위 timing 검증이 불가능합니다. B가 좋은 이유는 functional model은 빠른 시뮬레이션과 명확한 expected value 계산을 담당하고, timing 검증은 SVA가 독립적으로 처리하기 때문에 각 컴포넌트의 책임이 분리됩니다. (Ch10 §2.1)

</details>
:::tip[Q2. Coverage 6 카테고리에 *포함되지 않는* 것은? `(Remember)`]
- A. Command
- B. Timing
- C. *Layout (physical floorplan)*
- D. Training
:::
<details>
<summary>정답: C</summary>

**Why**: Layout(physical floorplan)은 physical design 팀의 영역으로 DV coverage에 포함되지 않습니다. DV coverage의 6 카테고리는 command·timing·MR·training·refresh·ECC이며, 이는 모두 프로토콜 동작 및 기능적 검증 대상입니다. A(command), B(timing), D(training)은 모두 6 카테고리에 실제로 포함됩니다. 물리적 레이아웃은 DRC/LVS 같은 별개의 물리 검증 플로우로 다루므로 functional DV coverage에 넣으면 혼선이 생깁니다. (Ch10 §3)

</details>
:::tip[Q3. SVA `bind` 의 *주 이점*은? `(Understand)`]
- A. 실행 속도 향상
- B. RTL 소스 *수정 없이* checker 부착
- C. Coverage 자동 생성
- D. 시뮬레이션 라이센스 절약
:::
<details>
<summary>정답: B</summary>

**Why**: SVA bind의 핵심 가치는 RTL 소스 파일을 한 줄도 수정하지 않고 assertion checker를 elaboration 시점에 부착할 수 있다는 점입니다. A(속도 향상)는 bind와 직접 관련이 없으며 오히려 checker 추가로 시뮬레이션이 약간 느려질 수 있습니다. C(coverage 자동 생성)는 bind가 제공하는 기능이 아니라 covergroup을 작성해야 하는 별개의 작업입니다. D(라이센스 절약)도 bind와 무관합니다. RTL을 수정하지 않아도 된다는 점은 IP 재사용과 PDK 제약이 있는 환경에서 매우 중요하며, checker를 제거할 때도 RTL을 건드리지 않고 bind 파일만 제외하면 됩니다. (Ch10 §4.4)

</details>
:::tip[Q4. 3-Tier regression의 *Tier 2 단계*는? `(Remember)`]
- A. Smoke directed (seed=0)
- B. Constrained-random (100 seeds × multiple tests)
- C. Coverage hole directed
- D. FPGA emulation
:::
<details>
<summary>정답: B</summary>

**Why**: 3-Tier regression에서 Tier 1은 smoke directed(seed=0으로 기본 동작 확인), Tier 2는 constrained-random(100 seeds × 여러 테스트로 코너 케이스 탐색), Tier 3은 coverage hole directed(남은 구멍을 겨냥한 직접 테스트)입니다. A(smoke directed)는 Tier 1, C(coverage hole directed)는 Tier 3, D(FPGA emulation)은 regression tier와 별개의 플랫폼 개념입니다. Tier 2가 constrained-random인 이유는 Tier 1의 기본 경로가 통과된 후 다양한 시드로 예상치 못한 조합을 찾아내는 단계이기 때문입니다. (Ch10 §5.1)

</details>
## 단답형

:::tip[Q5. *SVA 3 분류* (timing / command order / training)에 각각 한 예씩 들라. `(Apply)`]
:::
<details>
<summary>예시 답안</summary>

- **Timing**: `a_trcd` — ACT 후 tRCD 미만 cycle에 RD/WR 발급 시 fail
- **Command order**: `a_act_after_act_needs_pre` — 같은 bank 에 PRE 없이 ACT 두 번 fail
- **Training protocol**: `a_no_traffic_during_wck2ck` — WCK2CK Leveling 동안 RD/WR 발급 시 fail
(Ch10 §4)

</details>
:::tip[Q6. *Coverage weighting* 이 organization에 따라 다를 수 있는 이유는? `(Evaluate)`]
:::
<details>
<summary>예시 답안</summary>

- Sign-off goal이 *조직마다 다름* — 일부는 *high availability* (ECC weight 높음), 일부는 *low latency* (timing weight 높음)
- 과거 *silicon escape* 경험 — 특정 카테고리에서 escape 발생했다면 *그 카테고리 weight 상향*
- 시장 segment — 모바일 vs 서버 vs 자동차 — 각자 priority 다름
- Project schedule — coverage closure 일정에 따라 *우선순위 조정*
(Ch10 §3.7)

</details>
## 대표 문제

:::tip[Q7. 검증 환경에서 controller가 *tRCD-1 cycles 만에 RD 발급*했는데 DRAM model이 *invalid data 반환*. *시뮬레이션은 pass*하지만 silicon에서 fail. 어떻게 *각 컴포넌트의 책임을 재분배*해서 이런 false pass를 막을 수 있는가? `(Analyze, Evaluate)`]
:::
<details>
<summary>풀이 (책임 재분배 + 개선안)</summary>


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

</details>
---

