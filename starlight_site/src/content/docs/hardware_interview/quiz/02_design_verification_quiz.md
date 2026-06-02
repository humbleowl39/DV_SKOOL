---
title: "Quiz — Unit 2: Design Verification"
---

[← Unit 2 본문으로 돌아가기](../../02_design_verification/)

---

## Q1. (Remember)

UVM phase 중 자식 component 인스턴스를 *생성* 하는 phase 와 그 실행 방향은?

- [ ] A. `build_phase`, top-down
- [ ] B. `connect_phase`, bottom-up
- [ ] C. `run_phase`, parallel
- [ ] D. `start_of_simulation_phase`, parallel

<details>
<summary>정답 / 해설</summary>

**A**. `build_phase`는 top-down으로 실행된다. 부모 컴포넌트가 먼저 인스턴스를 생성해야 자식 컴포넌트가 존재할 수 있으므로 위에서 아래로 진행되는 것이 논리적이다. B의 `connect_phase`는 반대로 bottom-up인데, 자식의 포트가 먼저 존재해야 부모가 그 포트에 연결할 수 있기 때문이다. C의 `run_phase`는 모든 컴포넌트에서 병렬로 실행되는 시간 소비 phase로 인스턴스 생성과 관계없다. D의 `start_of_simulation_phase`는 run_phase 이전에 시뮬레이션 초기화 목적으로 쓰이는 phase다.

</details>
## Q2. (Understand)

`uvm_object` 와 `uvm_component` 의 핵심 차이 2가지?

<details>
<summary>정답 / 해설</summary>

1. **Phase 보유 여부** — `uvm_component`는 `build_phase`, `connect_phase`, `run_phase` 등 UVM phase를 자동으로 실행받고, phase 종료 전까지 시뮬레이터가 소멸시키지 않는다. `uvm_object`는 phase가 없으며 생성 후 GC(garbage collect) 대상이다.
2. **계층 트리** — `uvm_component`는 `parent` 인자를 통해 env → agent → driver 같은 계층 트리에 위치하며, 이 트리가 config_db 경로와 factory lookup의 기준이 된다. `uvm_object`는 트리 밖에서 자유롭게 생성·소멸되며 sequence item, transaction, configuration object 등에 사용된다. 면접에서 "sequence는 왜 component가 아니냐"고 물으면 "sequence는 run_phase 중 동적으로 생성/소멸되고 시뮬 내내 유지될 필요가 없기 때문"이라고 답할 수 있어야 한다.

</details>
## Q3. (Apply)

다음 constraint 의 동작을 설명하라.
```systemverilog
constraint c_dist {
  kind dist { READ := 70, WRITE := 30 };
}
```

<details>
<summary>정답 / 해설</summary>

`kind`가 무작위 생성될 때 약 70% 확률로 `READ`, 30% 확률로 `WRITE`를 갖도록 가중치 분포를 부여한다. `:=`는 *개별 값마다 가중치*를 고정 지정하는 연산자다. 만약 `:/`를 쓰면 그 구간 전체에 가중치를 균등 배분하므로, 값이 많은 구간일수록 값 하나당 가중치가 작아진다. 이 constraint를 그냥 `rand` 없이 0 / 1 이진으로 둔다면 50/50이 되므로, 실제 트래픽 비율을 모델링할 때는 반드시 `dist`로 가중치를 명시해야 의미 있는 커버리지 자극이 된다.

</details>
## Q4. (Analyze)

SVA `valid |-> ready` 가 *vacuous pass* 하는 경우는?

<details>
<summary>정답 / 해설</summary>

논리 임플리케이션 `p |-> q`는 antecedent `p`가 false이면 q의 참·거짓에 무관하게 항상 true로 평가된다. `valid`가 시뮬레이션 전체에서 한 번도 1이 되지 않으면 antecedent가 항상 false이므로 SVA는 위반 없이 "pass"를 보고하지만, 실제로는 아무 검증도 이루어지지 않은 것이다. 이것이 *vacuous pass*다. 해결책은 짝을 이루는 `cover property (@(posedge clk) valid)`를 반드시 추가하여 valid가 실제로 발생했는지 별도로 확인하는 것이다. assert property가 pass라는 사실만으로는 충분하지 않으며, cover property의 hit 수가 0이면 그 assertion은 아무것도 검증하지 않은 셈이다.

</details>
## Q5. (Apply)

Scoreboard 가 monitor 로부터 transaction 을 자동으로 받는 *TLM 메커니즘* 의 이름은?

<details>
<summary>정답 / 해설</summary>

**Analysis port / analysis imp**(`uvm_analysis_port` + `uvm_analysis_imp`)다. monitor가 `ap.write(tr)`를 호출하면 연결된 모든 subscriber(scoreboard, coverage collector 등)의 `write()` 메서드가 즉시 호출되며, 시뮬레이션 시간을 소비하지 않는다. 이는 일반 TLM port/export(blocking/non-blocking)와의 중요한 차이점이다. analysis port는 "broadcast" 모델이라 하나의 monitor가 여러 component에 동시에 데이터를 전달할 수 있고, scoreboard와 coverage collector를 monitor 코드 수정 없이 독립적으로 추가할 수 있다는 것이 핵심 설계 가치다.

</details>
## Q6. (Analyze)

Factory `set_type_override_by_type(base_seq::get_type(), err_seq::get_type())` 의 효과는?

<details>
<summary>정답 / 해설</summary>

이 한 줄 호출 이후 코드 어디서든 `base_seq::type_id::create(...)`를 호출하면 UVM factory가 `base_seq` 대신 `err_seq` 인스턴스를 반환한다. env, agent, sequence 코드를 전혀 수정하지 않고 test 클래스에서 override 한 줄로 에러 주입 시나리오를 주입할 수 있다는 것이 UVM factory의 핵심 가치다. 이것이 가능한 이유는 factory가 type 정보를 런타임에 조회하기 때문이며, `uvm_object_utils` 매크로로 등록된 클래스만 override 대상이 된다. `set_inst_override_by_type`으로 특정 인스턴스 경로만 override하는 더 세밀한 제어도 가능하다.

</details>
## Q7. (Evaluate)

Code coverage 99%, Functional coverage 75% — 검증 sign-off 가능한가?

<details>
<summary>정답 / 해설</summary>

**불가**. Code coverage는 "모든 코드 경로가 한 번은 실행되었다"는 문법적 위생을 보장할 뿐, 의도된 기능 시나리오가 실제로 검증되었음을 의미하지 않는다. Functional coverage 75%는 엔지니어가 사전에 정의한 검증 계획의 25%가 여전히 미검증 상태임을 뜻한다. 이 25%가 코너 케이스, 에러 인젝션, 프로토콜 엣지 조건을 포함할 수 있기 때문에 sign-off는 불가하다. 올바른 절차는 hole 분석으로 미히트 bin을 식별하고 directed 또는 constraint 수정으로 해당 시나리오를 자극한 뒤, 정당화된(waived) exclusion이 있다면 review board 승인을 거쳐 문서화하는 것이다.

</details>
## Q8. (Create)

Async FIFO 검증을 위한 *illegal_bins* 가 들어가야 할 covergroup 의 예시 시나리오를 하나 적어라.

<details>
<summary>정답 / 해설</summary>

`full`과 `empty`가 *동시에* 1인 상태는 capacity ≥ 1인 FIFO에서 물리적으로 불가능한 디자인 버그다. 이 상태를 `illegal_bins`로 선언하면 시뮬레이터가 해당 bin에 한 번이라도 hit될 때 즉시 에러를 보고한다.
```systemverilog
cp_state : coverpoint {full, empty} {
  illegal_bins both_full_empty = {2'b11};
}
```
`illegal_bins`와 일반 `bins`의 차이는 바로 이 자동 에러 트리거에 있다. 일반 bins는 hit 여부를 기록할 뿐이지만 `illegal_bins`는 hit 자체를 violation으로 취급하므로, 전체 시뮬레이션에서 이 상태가 "절대 나오면 안 된다"는 설계 불변 조건을 assertions 없이도 커버리지 모델 안에서 시행할 수 있다.

</details>
