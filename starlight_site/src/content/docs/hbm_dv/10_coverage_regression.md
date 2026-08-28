---
title: "Ch10 — Coverage Closure & Regression"
---

:::tip[학습 목표]
이 챕터를 마치면:

- **Derive** V-Plan의 coverage 항목으로부터 covergroup과 bin을 도출할 수 있다.
- **Implement** 동시 활성 조합과 상태 전이를 측정하는 커버리지 모델을 구현할 수 있다.
- **Design** 구성 변경에도 무력화되지 않는 bin 정의를 설계할 수 있다.
- **Evaluate** exclusion·waiver의 정당성을 판단하고 sign-off 기준을 적용할 수 있다.
:::

:::note[사전 지식]
- [Ch09 — Assertion · Protocol Checker](../09_assertion_checker/): *"cover가 비면 미측정"* — 이 챕터가 이어받습니다
- [Ch07 — V-Plan & 검증 프로세스](../07_vplan_process/): coverage 수단을 가진 항목들
- [HBM 아키텍처 Ch04](../../hbm/04_channels_addressing/): 채널 인덱스 bin이 순차 접근으로도 100%가 되는 문제
:::

---

## 1. Why care? — 100%가 되면 검증이 끝나는가

커버리지가 91%입니다. 남은 9%를 채우려고 시나리오를 추가합니다. 2주 뒤 94%. 또 추가합니다. 96%.

숫자가 올라가니 진척이 있어 보입니다. 그런데 이 과정에서 아무도 묻지 않은 질문이 둘 있습니다.

**첫째, 이 100%는 무엇의 100%입니까?**

선행 코스와 Ch04에서 반복한 원리입니다 — *모델에 없는 항목은 0%로 잡히는 것이 아니라 아예 집계되지 않습니다.* 커버리지 모델에 동시 활성 조합 bin이 없다면, 그 축은 100%에도 포함되지 않습니다.

**둘째, 올라간 4%는 무엇이었습니까?**

커버리지를 목표로 삼고 시나리오를 추가하면 **채우기 쉬운 bin부터** 채워집니다. 주소 범위를 넓히고 버스트 길이를 다양화하면 숫자가 빨리 오릅니다. 그런데 그것이 **위험이 큰 영역이었는지는 별개**입니다. 숫자는 올랐지만 실제 위험은 그대로일 수 있습니다.

Ch09에서 이미 이 문제의 축소판을 봤습니다. `c_ca_share_exercised`가 0%였는데 assertion 리포트는 "전부 통과"였습니다. 커버리지 전체에서도 같은 일이 일어납니다.

이 챕터는 **커버리지를 숫자가 아니라 모델로 다루는 방법**과, 그 모델을 회귀로 채우고 sign-off까지 가져가는 운영을 다룹니다.

---

## 2. 직관 — 커버리지 모델은 V-Plan에서 나온다

### 순진한 시도 1 — 숫자를 목표로 삼는다

"이번 분기 목표 95%"를 정하고 그것을 향해 갑니다. 명확하고 추적하기 쉽습니다.

**어디서 막히나?** 두 가지가 동시에 일어납니다. **모델이 불완전하면 100%도 불완전**하고, **채우기 쉬운 것부터 채워져** 숫자와 위험 감소가 비례하지 않습니다. 그리고 도달 불가능한 bin이 하나라도 있으면 **100%에 영원히 도달하지 못합니다.**

### 순진한 시도 2 — 모든 신호와 조합을 bin으로

빠짐없이 측정하면 누락이 없습니다.

**어디서 막히나?** 조합이 폭발합니다. 선행 코스 Ch04에서 계산했듯 채널 16개의 활성 조합만 2¹⁶이고, 여기에 뱅크·상태·커맨드가 곱해집니다. 그리고 **의미 없는 bin**이 대량 생기면 리포트를 읽을 수 없게 되고, 결국 아무도 보지 않습니다.

### 일반화 — Bin은 신호가 아니라 검증 항목에서 나온다

> **커버리지 모델은 V-Plan의 coverage 수단 항목을 bin으로 옮긴 것이다.**
> 신호를 나열해서 만드는 것이 아니라, **"이것이 다양하게 발생했는가"를 물어야 할 항목**에서 도출한다.

Ch07의 V-Plan을 다시 보면 coverage 수단을 가진 행들이 있었습니다.

| V-Plan 행 | 물어야 할 질문 | Bin 설계 |
|---|---|---|
| C-01 동시 활성 채널 조합 | 얼마나 많은 채널이 **동시에** 활성이었나 | 동시 활성 수 + pc 동시 요청 |
| C-02 `SCHED_MODE` 3종 사용 | 세 모드가 **모두** 사용됐나 | 설정값 coverpoint |
| C-03 테스트 모드 전이 전수 | 진입·복귀 경로를 **모두** 밟았나 | **transition bin** |
| (Ch09) assertion 전제 | 각 규칙이 **자극됐나** | cover property |

**이 표가 커버리지 모델의 설계도입니다.** 신호 목록이 아니라 질문 목록에서 시작합니다.

---

## 3. 작은 예 — 세 가지 커버리지 모델

### 3.1 동시 활성 조합 — #1

선행 코스 Ch04의 문제입니다.

> `channel_id` bin 16개는 **차례로** 접근해도 전부 채워진다.

필요한 것은 **동시성 자체를 축으로 삼는 것**입니다. 그러려면 두 가지를 정해야 합니다 — **무엇을 세고, 언제 샘플링하는가.**

```systemverilog
class concurrency_coverage extends uvm_component;
  `uvm_component_utils(concurrency_coverage)

  hbm_dv_cfg cfg;

  // 현재 미해결 요청이 있는 채널·pc 집합 (monitor가 갱신)
  protected bit active_ch [];
  protected bit active_pc [2];

  protected int unsigned n_active_ch;
  protected bit          both_pc_busy;

  // 구성값을 인자로 받는 covergroup — #6 대응
  covergroup cg_concurrency (int unsigned num_ch) ;
    option.per_instance = 1;

    // 동시에 활성인 채널 수 — 순차 접근이면 항상 1
    cp_n_active : coverpoint n_active_ch {
      bins idle     = {0};
      bins single   = {1};
      bins few      = {[2:3]};
      bins many     = {[4:7]};
      bins most     = {[8:15]};
      bins all      = {[16:$]};
      illegal_bins over = {[64:$]};   // 물리적으로 불가능한 값
    }

    // 같은 채널의 두 pseudo-channel이 동시에 요청 — 스펙 R3의 자극 조건
    cp_both_pc : coverpoint both_pc_busy {
      bins pc_single = {0};
      bins pc_both   = {1};
    }

    // 교차 — "많은 채널이 활성인 동안 pc도 동시" 가 진짜 부하 상황
    x_load : cross cp_n_active, cp_both_pc {
      ignore_bins trivial = binsof(cp_n_active) intersect {0};
    }
  endgroup

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(hbm_dv_cfg)::get(this, "", "cfg", cfg))
      `uvm_fatal("COV", "hbm_dv_cfg를 찾을 수 없습니다")
    active_ch = new[cfg.num_channel];
    cg_concurrency = new(cfg.num_channel);     // 구성값 주입
  endfunction

  // 요청이 발행되는 시점에 현재 동시 상태를 샘플
  function void sample_on_request();
    n_active_ch  = count_active_channels();
    both_pc_busy = active_pc[0] && active_pc[1];
    cg_concurrency.sample();
  endfunction
endclass
```

**두 가지 설계 판단**

**① 언제 샘플링하는가** — 동시성은 **상태**이므로 매 사이클 샘플링할 수도 있습니다. 그러나 그러면 유휴 구간이 대량으로 집계되어 분포가 왜곡됩니다. **요청이 발행되는 시점**에 샘플하면 *"요청이 일어날 때 얼마나 붐볐는가"* 가 측정됩니다.

**② `x_load` cross가 핵심** — 동시 활성 채널 수만으로는 부족합니다. *"여러 채널이 활성인 **동시에** 같은 채널의 두 pc도 요청 중"* 이 R3(CA 공유 경합)이 실제로 자극되는 상황이며, Ch09의 `c_ca_share_exercised`가 0%였던 이유가 여기서 측정됩니다.

### 3.2 상태 전이 — #18

테스트 모드와 저전력 모드는 **전이 경로**가 검증 대상입니다(스펙 R17~R20). 값이 아니라 **값의 변화 순서**를 봐야 합니다.

```systemverilog
covergroup cg_mode_transition;
  option.per_instance = 1;

  cp_mode : coverpoint mode_state {
    bins s_mission = {MODE_MISSION};
    bins s_pending = {MODE_PENDING};    // REQ=1, ACK 대기 중
    bins s_test    = {MODE_TEST};

    // 전이 — 이것이 이 covergroup의 목적
    bins t_enter_req  = (MODE_MISSION => MODE_PENDING);
    bins t_enter_ack  = (MODE_PENDING => MODE_TEST);
    bins t_exit       = (MODE_TEST    => MODE_MISSION);

    // 전체 왕복을 한 번 이상 — R17~R20 전 과정
    bins t_round_trip = (MODE_MISSION => MODE_PENDING => MODE_TEST => MODE_MISSION);

    // 스펙상 일어나면 안 되는 전이
    illegal_bins t_skip_pending = (MODE_MISSION => MODE_TEST);
  }

  // 진입 요청 시점에 미해결 트랜잭션이 있었는가 — R17의 "완료 후 ACK"를 자극
  cp_pending_txn : coverpoint outstanding_at_req {
    bins none = {0};
    bins some = {[1:3]};
    bins many = {[4:$]};
  }

  x_enter_under_load : cross cp_mode, cp_pending_txn {
    bins enter_busy = binsof(cp_mode.t_enter_req) && binsof(cp_pending_txn.many);
  }
endgroup
```

**`x_enter_under_load`가 의미 있는 부분**입니다. 스펙 R17은 *"미해결 트랜잭션을 모두 완료한 뒤 ACK를 1로 만든다"* 고 규정합니다. 미해결이 0인 상태에서 진입하면 그 규칙이 자극되지 않습니다 — **바쁜 상태에서 진입했는지**를 별도로 측정해야 합니다.

`illegal_bins`도 유용합니다. 스펙상 불가능한 전이가 발생하면 **커버리지 수집 자체가 오류를 보고**하므로, assertion을 하나 더 쓰지 않고도 잡힙니다.

### 3.3 구성 변경에 견디는 Bin — #6

Ch06 마무리 문제의 답입니다.

> 채널이 16 → 32로 늘었는데 bin이 16개 기준이면, 새 채널은 **측정에서 빠지고 커버리지는 100%를 보고**한다.

```systemverilog
// ❌ 위험 — 구성이 바뀌어도 조용히 통과
covergroup cg_channel_bad;
  cp_ch : coverpoint ch_id {
    bins ch[16] = {[0:15]};          // 고정
  }
endgroup

// ✅ 구성값을 참조 — 채널이 늘면 bin도 늘어난다
covergroup cg_channel_good (int unsigned num_ch);
  cp_ch : coverpoint ch_id {
    bins valid[] = {[0:num_ch-1]};                    // 동적
    illegal_bins out_of_range = {[num_ch:$]};         // 범위 밖 접근 검출
  }
endgroup
```

**`illegal_bins out_of_range`가 부가 이득**입니다. 구성값보다 큰 채널 번호가 관측되면 즉시 오류가 나므로, **구성 불일치 자체**가 검출됩니다.

**그리고 이것만으로는 부족합니다.** 세대 이관 체크리스트(Ch07 #5의 3단계)에 다음을 명시적 항목으로 둡니다.

| 확인 항목 | 방법 |
|---|---|
| bin 정의가 구성값을 참조하는가 | 코드 리뷰 |
| 이관 후 **bin 총 개수가 늘었는가** | 이관 전후 리포트의 bin 수 비교 |
| 새 구성 전용 항목이 추가됐는가 | V-Plan 항목 목록 리뷰 |

**bin 총 개수 비교**가 실용적입니다. 채널이 두 배가 됐는데 bin 수가 그대로라면 무언가 고정되어 있다는 뜻입니다.

:::note[🤔 잠깐 — 이 covergroup의 문제를 찾으세요]
어떤 팀이 동시성 측정을 위해 다음을 작성했습니다.

```systemverilog
covergroup cg_conc;
  cp_ch  : coverpoint current_ch_id  { bins ch[16] = {[0:15]}; }
  cp_pc  : coverpoint current_pc     { bins pc[2]  = {[0:1]};  }
  x_ch_pc: cross cp_ch, cp_pc;
endgroup
// 매 트랜잭션마다 sample() 호출
```

리포트에서 이 covergroup은 **100%**로 나왔습니다. 그런데 Ch09의 `c_ca_share_exercised`는 여전히 **0%** 입니다. 무엇이 문제입니까?

<details>
<summary>정답 / 해설</summary>

**이 covergroup은 동시성을 전혀 측정하지 않습니다. "어느 채널·pc를 접근했는가"만 측정합니다.**

`cross cp_ch, cp_pc`는 32개 조합을 만들지만, 그 조합은 **한 트랜잭션의 속성**입니다 — *"채널 5의 pc 1에 접근한 적이 있다"*. 채널 5와 채널 9가 **동시에** 활성이었는지는 어디에도 없습니다.

**차례로** 32개 조합을 모두 접근하면 100%가 됩니다. 선행 코스 Ch04가 경고한 바로 그 상황이며, cross를 썼다고 해서 동시성이 측정되는 것이 아닙니다.

**왜 `c_ca_share_exercised`가 0%인가**: R3이 자극되려면 `row_cmd_valid && col_cmd_valid`가 **같은 사이클**에 참이어야 합니다. 트랜잭션을 하나씩 순차 처리하면 그 상황이 만들어지지 않습니다. covergroup 100%는 그것과 무관합니다.

**무엇을 고쳐야 하는가**

측정 대상을 **한 트랜잭션의 속성**에서 **그 시점의 시스템 상태**로 바꿔야 합니다.

| 잘못된 축 | 올바른 축 |
|---|---|
| 접근한 채널 id | **동시에 활성인 채널 수** |
| 접근한 pc | **두 pc가 동시에 요청 중인가** |
| id × pc cross | **동시 활성 수 × pc 동시 여부 cross** |

§3.1의 `cg_concurrency`가 그 형태입니다. 샘플링 시점도 함께 바뀝니다 — 트랜잭션 속성은 그 트랜잭션에서, 시스템 상태는 **요청 발행 시점의 전역 상태**에서 수집합니다.

**일반 원리**: **cross는 동시성을 보장하지 않습니다.** cross가 측정하는 것은 *"이 두 값의 조합이 등장했는가"* 이며, 두 값이 **같은 순간에 서로 다른 주체에서** 참이었는지는 별개입니다. 후자를 측정하려면 그 순간의 상태를 하나의 변수로 만들어 coverpoint로 삼아야 합니다.

</details>
:::

### 3.4 Regression 운영

**단일 테스트의 커버리지는 의미가 없습니다.** 그 테스트가 무엇을 쳤는지만 보여 줍니다. 의미 있는 분석은 **회귀 전체의 데이터베이스를 병합(merge)** 한 뒤에 가능합니다.

| 운영 항목 | 규칙 |
|---|---|
| **Merge** | 회귀 전체 DB를 병합해 분석. 단일 테스트 리포트로 판단하지 않는다 |
| **출처 분리** | VIP 커버리지 / DUT 기능 커버리지 / 프로파일별 (Ch04·Ch05) |
| **시드 관리** | 실패 시드를 보관해 재현 가능하게 |
| 실패 분류 | 신규 / 기존 알려진 / 환경 문제로 나눠 집계 |
| 추이 추적 | 주별 커버리지 증가와 **어느 축이 늘었는지** 함께 |

"어느 축이 늘었는지"를 함께 보는 것이 도입부의 두 번째 질문에 대한 답입니다 — 4% 상승이 **쉬운 축**에서 왔는지 **위험한 축**에서 왔는지 구분됩니다.

---

## 4. 일반화 — 목표를 어떻게 잡을 것인가

### 대안 A — 100%를 목표로

가장 명확한 기준입니다.

**왜 그대로는 안 되나**: **도달 불가능한 bin**이 존재합니다. 물리적으로 발생할 수 없는 조합, 특정 구성에서만 유효한 값, 안전 로직 때문에 도달할 수 없는 상태 등입니다. 이들을 그대로 두면 100%에 영원히 도달하지 못하고, 그러면 **목표 자체가 무의미해져 아무도 신경 쓰지 않게 됩니다.**

**올바른 처리**: **exclusion**으로 제외하되 **문서화된 정당화**를 반드시 붙입니다. 그리고 도달 불가 항목의 exclusion은 **설계가 동결된 시점**에 추가합니다 — 설계가 계속 바뀌는 동안 도달 불가를 판정하면, 나중에 설계가 바뀌어 도달 가능해져도 제외된 채로 남습니다.

### 대안 B — 목표를 낮춰 잡는다 (예: 90%)

도달 불가 문제를 우회하는 실용적 방법으로 보입니다.

**왜 안 되나**: **남은 10%가 무엇인지 아무도 모릅니다.** 90%를 채운 시점에 미달인 10%가 사소한 것인지 핵심인지 구분되지 않습니다. 숫자 목표는 **어느 bin이 비었는지**를 감춥니다.

**올바른 처리**: 목표를 **숫자가 아니라 항목으로** 세웁니다.

> *"커버리지 95%"* 가 아니라
> *"모든 coverage 항목이 **충족** 또는 **문서화된 waive** 상태"*

이것이 Ch07의 V-Plan 항목 상태와 그대로 연결됩니다. 숫자는 진척 추이를 보는 참고 지표이고, **판정은 항목 단위**로 합니다.

---

## 5. 디테일 — Coverage 운영에서 실제로 벌어지는 일

### 실패 1 — 숫자 올리기 게임이 된다

목표가 숫자이므로 팀이 숫자를 올리는 데 최적화합니다.

**관측되는 증상**: 커버리지가 꾸준히 오르는데 **버그 발견율은 떨어집니다.** 채우기 쉬운 bin(주소 범위, 버스트 길이, 단순 값 분포)부터 채워지고, 채우기 어려운 bin(동시성, 오류 경로, 모드 전이)은 마지막까지 남습니다. 그런데 **버그는 어려운 쪽에 있습니다.**

**처방**: 커버리지 항목에 **위험도 표시**를 붙이고, 리포트에서 **위험도 높은 항목의 충족 여부를 먼저** 봅니다. 전체 백분율은 그 아래에 둡니다.

### 실패 2 — Exclusion에 근거가 없다

숫자를 맞추려고 미달 항목을 제외하는데, 왜 제외했는지 기록하지 않은 경우입니다.

**관측되는 증상**: 몇 달 뒤 아무도 그 exclusion의 이유를 모릅니다. 설계가 바뀌어 이제는 도달 가능해졌는데도 제외된 채 남고, sign-off 리뷰에서 *"이건 왜 뺐죠"* 에 답할 수 없습니다.

**처방**: **모든 exclusion은 정당화 문서에 묶습니다.** 최소한 다음을 기록합니다.

| 기록 항목 | 예 |
|---|---|
| 제외 대상 | 어느 bin·어느 covergroup |
| 사유 분류 | 도달 불가 / 구성상 무효 / 범위 밖 / 후속 릴리스 이월 |
| 근거 | 왜 그렇게 판단했는가 (설계 근거·스펙 조항) |
| 승인자·일자 | 누가 언제 |
| 재검토 조건 | 설계 변경 시 다시 볼 것인가 |

그리고 **도달 불가 exclusion은 설계 동결 이후**에 추가합니다.

### 실패 3 — 단일 테스트 커버리지로 판단한다

테스트 하나를 돌리고 그 리포트를 보고 판단하는 경우입니다.

**관측되는 증상**: 각 테스트가 자기 영역만 채우므로 개별 리포트는 낮게 나옵니다. 그것을 보고 *"커버리지가 안 오른다"* 고 판단해 불필요한 시나리오를 추가합니다. 반대로 특정 테스트만 보고 *"이 영역은 됐다"* 고 넘어가면, 회귀 전체에서는 그 테스트가 자주 실패해 실제로는 잘 안 돌고 있을 수 있습니다.

**처방**: **회귀 전체를 병합한 DB로만 판단**합니다. 그리고 병합 시 **실패한 테스트의 커버리지를 포함할지** 정책을 정합니다 — 일반적으로 실패한 실행의 커버리지는 신뢰할 수 없으므로 제외하는 편이 안전합니다.

---

## 6. 흔한 오해

| 오해 | 실제 |
|---|---|
| "커버리지 100%면 검증 완료" | **모델이 불완전하면 100%도 불완전**합니다 |
| "cross를 쓰면 동시성이 측정된다" | cross는 **값 조합의 등장**을 봅니다. 동시성은 **그 순간의 상태**를 coverpoint로 만들어야 합니다 |
| "숫자 목표가 명확해서 좋다" | 쉬운 bin부터 채워집니다. **위험도 순으로** 봐야 합니다 |
| "도달 불가 bin은 그냥 두면 된다" | 100%에 도달 못 해 **목표가 무의미해집니다.** exclusion + 정당화 |
| "Exclusion은 나중에 정리하면 된다" | 근거가 사라집니다. **제외하는 그 순간** 기록합니다 |
| "테스트 하나 돌려서 커버리지를 본다" | 단일 실행 리포트는 의미가 약합니다. **회귀 merge** 후 판단 |
| "bin은 한 번 정의하면 된다" | 구성이 바뀌면 **조용히 무력화**됩니다 (#6) |

---

## 🔧 이 문제를 이렇게 푼다

> **닫는 항목: #1 — 동시 활성 채널 조합을 coverage 축으로 / #6 — 세대 이관 시 coverage 모델이 새 구성을 반영하는지 / #18 — 저전력·테스트 모드의 상태 전이 커버리지**

### #1 — 동시성 축

- 측정 대상을 **한 트랜잭션의 속성**이 아니라 **그 시점의 시스템 상태**로 잡는다
- coverpoint: **동시 활성 채널 수** · **같은 채널의 두 pc 동시 요청 여부**
- **cross로 부하 상황을 정의**한다 — *"많은 채널이 활성인 동시에 pc도 동시"*
- 샘플링은 **요청 발행 시점**의 전역 상태에서 (매 사이클이면 유휴가 분포를 왜곡)
- Ch09의 assertion cover(`c_ca_share_exercised`)와 **짝지어 본다** — 이 축이 채워져야 그 cover도 채워진다

### #6 — 구성 변경에 견디는 Bin

- covergroup을 **구성값을 인자로 받는 형태**로 만들고 `bins valid[] = {[0:num-1]}` 처럼 **동적 정의**
- `illegal_bins`로 **범위 밖 값**을 잡아 구성 불일치 자체를 검출
- 세대 이관 체크리스트에 **bin 총 개수 비교**를 넣는다 — 구성이 두 배인데 bin 수가 그대로면 고정된 것
- V-Plan 항목 목록 리뷰에서 **새 구성 전용 항목**이 추가됐는지 확인

### #18 — 상태 전이

- 값이 아니라 **전이(`=>`)** 를 bin으로 정의
- 전 과정 왕복을 **하나의 전이 bin**으로 (R17~R20)
- 스펙상 불가능한 전이는 **`illegal_bins`** — assertion 없이도 검출
- **전이가 일어난 조건**을 cross로 (예: 미해결 트랜잭션이 있는 상태에서 진입 — R17 자극)

### Closure 운영

| 규칙 | 내용 |
|---|---|
| **목표는 숫자가 아니라 항목** | *"모든 coverage 항목이 충족 또는 문서화된 waive"* |
| **위험도 우선 리포트** | 위험도 높은 항목의 충족 여부를 백분율보다 먼저 |
| **Merge 후 판단** | 회귀 전체 DB 병합. 실패 실행의 커버리지는 제외 정책 |
| **출처 분리** | VIP / DUT 기능 / 프로파일별로 나눠 보고 (Ch04·Ch05) |
| **Exclusion에 정당화 필수** | 대상·사유·근거·승인자·재검토 조건 기록 |
| **도달 불가 exclusion은 설계 동결 이후** | 설계가 바뀌면 도달 가능해질 수 있음 |
| **추이와 함께 축을 본다** | 상승분이 어느 축에서 왔는지 |

### Sign-off 판정

Ch07의 게이트에 커버리지 조건을 구체화합니다.

- 모든 coverage 항목이 **충족 또는 승인된 waive**
- **Assertion cover가 모두 충족** (Ch09 — 비어 있으면 그 규칙은 미측정)
- Exclusion 목록이 **전부 정당화 문서에 묶여** 있고 승인됨
- 회귀 병합 DB 기준이며, **출처별로 분리 보고**됨

---

## 7. 핵심 정리

- **커버리지는 숫자가 아니라 모델**이다. 모델이 불완전하면 100%도 불완전하다
- **Bin은 신호가 아니라 V-Plan 항목에서** 도출한다 — "이것이 다양하게 발생했는가"를 물어야 할 항목에서
- **Cross는 동시성을 보장하지 않는다.** 동시성은 **그 순간의 상태**를 coverpoint로 만들어야 측정된다
- 상태 전이는 **전이 bin**으로. 불가능한 전이는 `illegal_bins`로 잡는다
- bin 정의가 **구성값을 참조**해야 세대 이관에서 조용히 무력화되지 않는다. **bin 총 개수 비교**가 실용적 점검
- **숫자 목표는 쉬운 bin부터 채우게 만든다.** 목표는 **항목 단위**로, 리포트는 **위험도 우선**으로
- **Exclusion은 정당화 문서에 묶는다.** 도달 불가 판정은 **설계 동결 이후**에
- 단일 테스트 커버리지로 판단하지 않는다. **회귀 병합 DB**로 판단하고 **출처별로 분리**한다

:::note[🤔 마무리 자가 점검]
Sign-off 리뷰에 다음 자료가 올라왔습니다.

> ```
> 회귀: 12,000 job (병합 DB 기준), 통과율 99.8%
> Functional Coverage: 97.2%
>   - 미달 항목 3개, 전부 exclusion 처리 (사유: "도달 불가")
> Assertion: 24개 전부 PASS
>   - cover 충족 21/24 (미충족: c_ca_share_exercised, c_test_mode_entered, c_lp_exit)
> Code Coverage: 98.1%
> ```
> "커버리지 목표(95%)를 초과 달성했고 assertion도 전부 통과했으므로 sign-off 가능합니다."

이 판단을 평가하세요.

<details>
<summary>정답 / 해설</summary>

**Sign-off 할 수 없습니다. 두 가지 결정적 문제가 있습니다.**

**문제 1 — Assertion cover 3개 미충족 = 규칙 3개 미검증**

`c_ca_share_exercised`, `c_test_mode_entered`, `c_lp_exit`가 비어 있습니다. Ch09에서 확인한 대로 이것은 **해당 assertion들이 vacuous**하다는 뜻입니다.

즉 **"assertion 24개 전부 PASS"는 사실이지만 그중 3개는 일한 적이 없습니다.** 그리고 하필 그 셋이 무엇인지 보면 심각합니다.

- `c_ca_share_exercised` → **스펙 R3(CA 공유 경합)** — 이 IP의 핵심 규칙
- `c_test_mode_entered` → **R17~R20(테스트 모드)** 전체
- `c_lp_exit` → 저전력 복귀 경로

**핵심 규칙 세 갈래가 통째로 미검증**입니다. V-Plan 상태로는 "통과"가 아니라 **"미측정"** 이어야 합니다.

**문제 2 — Exclusion 3개의 사유가 "도달 불가" 한 줄뿐**

정당화가 없습니다. 확인해야 할 것:

- **무엇을 근거로** 도달 불가라고 판정했는가 (설계 근거? 스펙 조항?)
- **언제** 판정했는가 — 설계 동결 이후인가, 아니면 설계가 바뀌는 중에 판정해 지금은 도달 가능해졌는가
- **누가 승인**했는가
- 그 3개가 **무엇인지** — 사소한 값 조합인가, 아니면 위 세 미충족 cover와 관련된 항목인가

마지막이 특히 중요합니다. 만약 exclusion된 3개가 동시성이나 모드 전이 관련이라면, **자극하지 못한 것을 "도달 불가"로 처리한 것**일 수 있습니다. 이 둘은 전혀 다릅니다 — 도달 불가는 설계상 불가능한 것이고, 자극 실패는 **시나리오가 부족한 것**입니다.

**그 밖에 확인할 것**

- **출처 분리**: 97.2%가 VIP 커버리지를 포함한 숫자인지 DUT 기능 커버리지만인지 (Ch04)
- **프로파일 분리**: 12,000 job에 P1·P2가 몇 개인지 (Ch05)
- **위험도**: 미달 3개와 채워진 항목들의 위험도 분포

**결론과 조치**

sign-off를 보류하고 다음을 수행합니다.

1. **미충족 cover 3건에 대한 시나리오를 만든다** — 동시 부하 시나리오(§3.1의 축이 채워지도록), 테스트 모드 진입·복귀, 저전력 복귀. Ch08의 라이브러리에 추가
2. **V-Plan 상태를 정정한다** — R3·R17~R20·저전력 관련 행을 "미측정"으로
3. **Exclusion 3건을 재검토한다** — 정당화 문서를 채우고, 자극 실패를 도달 불가로 오분류하지 않았는지 확인
4. **리포트 형식을 고친다** — 출처별·프로파일별 분리, 위험도 우선 정렬

**교훈**: **97.2%와 "assertion 전부 통과"는 둘 다 사실이면서 동시에 오해를 만듭니다.** 이 코스가 반복해 온 대로, 숫자는 위험의 분포를 감춥니다. cover 3개의 0%가 그 백분율 어디에도 반영되지 않는다는 점이 그 증거입니다.

</details>
:::

**다음 챕터**: [Ch11 — DFT · MBIST · RAS 연계 검증](../11_dft_ras/)에서 마지막 남은 항목을 다룹니다. ECC가 결함을 가리는 문제와 테스트 모드·mission 모드의 경계를 봅니다.

**퀴즈**: [Ch10 퀴즈](../quiz/10_coverage_regression_quiz/)

---

## 참고 자료

- [Verification Methodology (OpenTitan)](https://opentitan.org/book/doc/contributing/dv/methodology/index.html) — 회귀 DB 병합, gap의 이해·waive, exclusion 정당화, 설계 동결 시점
- [Sign-Off Criteria (chipverify)](https://chipverify.com/verification/sign-off-criteria) — 게이트 동시 통과와 문서화된 waive
- [A Coverage-Driven Formal Methodology for Verification Sign-off (DVCon)](https://dvcon-proceedings.org/wp-content/uploads/a-coverage-driven-formal-methodology-for-verification-sign-off.pdf) — sign-off 판정 구조
- [HBM 아키텍처 Ch04 — 채널 · Pseudo-channel](../../hbm/04_channels_addressing/) — 채널 인덱스 bin의 한계
- [HBM 아키텍처 Ch02 — 세대 지형도](../../hbm/02_generations/) — coverage 모델이 조용히 무력화되는 문제
- [UVM 코스 Module 05 — TLM·Scoreboard·Coverage](../../uvm/) — covergroup·bin 문법과 수집 구조

:::caution[운영 규율에 대하여]
exclusion·waiver·sign-off의 구체적 규율은 **조직마다 다릅니다.** 위 내용은 공개 방법론 문서를 근거로 한 일반적 형태이며, 실제 적용 시 소속 조직의 검증 절차와 인증 요구사항을 우선하세요.
:::
