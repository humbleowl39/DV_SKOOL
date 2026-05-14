# Quiz — Unit 2: Design Verification

[← Unit 2 본문으로 돌아가기](../02_design_verification.md)

---

## Q1. (Remember)

UVM phase 중 자식 component 인스턴스를 *생성* 하는 phase 와 그 실행 방향은?

- [ ] A. `build_phase`, top-down
- [ ] B. `connect_phase`, bottom-up
- [ ] C. `run_phase`, parallel
- [ ] D. `start_of_simulation_phase`, parallel

??? answer "정답 / 해설"
    **A**. `build_phase` 는 top-down (부모 먼저 → 자식). 부모가 자식 instance 를 만들 수 있어야 하므로. `connect_phase` 는 반대로 bottom-up (자식의 port 가 먼저 준비되어야 부모가 연결).

## Q2. (Understand)

`uvm_object` 와 `uvm_component` 의 핵심 차이 2가지?

??? answer "정답 / 해설"
    1. **Phase 보유 여부** — component 는 phase 를 가지고 자동 실행, object 는 phase 없음.
    2. **계층 트리** — component 는 parent/child 트리에 속함, object 는 자유 생성/소멸.
    (보너스: component 는 시뮬 끝까지 존속, object 는 sequence/sequence_item 처럼 동적 생성·소멸)

## Q3. (Apply)

다음 constraint 의 동작을 설명하라.
```systemverilog
constraint c_dist {
  kind dist { READ := 70, WRITE := 30 };
}
```

??? answer "정답 / 해설"
    `kind` 가 무작위 생성 시 약 70% 확률로 `READ`, 30% 확률로 `WRITE` 를 갖도록 가중치 분포. `:=` 는 *각 값에 가중치* 부여, 구간이면 `:/` 사용.

## Q4. (Analyze)

SVA `valid |-> ready` 가 *vacuous pass* 하는 경우는?

??? answer "정답 / 해설"
    `valid` 가 시뮬 전체에서 *한 번도 1 이 되지 않으면* antecedent 가 항상 false → implication 이 trivially 만족 → "위반 검출 못 함 = pass" 로 표기. **해결**: 짝지어 `cover property (valid)` 추가해 *valid 가 실제 발생했는지* 확인.

## Q5. (Apply)

Scoreboard 가 monitor 로부터 transaction 을 자동으로 받는 *TLM 메커니즘* 의 이름은?

??? answer "정답 / 해설"
    **Analysis port / analysis imp** (uvm_analysis_port + uvm_analysis_imp). Monitor 가 `ap.write(tr)` 호출 → 연결된 모든 subscriber 의 `write()` 메서드 자동 호출. 시뮬 시간 소비 없음.

## Q6. (Analyze)

Factory `set_type_override_by_type(base_seq::get_type(), err_seq::get_type())` 의 효과는?

??? answer "정답 / 해설"
    이후 코드의 `base_seq::type_id::create(...)` 모든 호출이 *err_seq* 인스턴스를 반환. Env / agent / sequence 코드를 *전혀 수정하지 않고* test 마다 다른 시퀀스 주입 가능 — UVM 의 핵심 가치.

## Q7. (Evaluate)

Code coverage 99%, Functional coverage 75% — 검증 sign-off 가능한가?

??? answer "정답 / 해설"
    **불가**. Code cov 는 *문법 위생* — 모든 라인이 실행되었다는 뜻일 뿐. Functional cov 75% 는 *25% 의 의도된 시나리오가 검증 안 됨*. Functional hole 분석 + 추가 directed/random test → 100% 또는 정당화된 exclusion 후 sign-off.

## Q8. (Create)

Async FIFO 검증을 위한 *illegal_bins* 가 들어가야 할 covergroup 의 예시 시나리오를 하나 적어라.

??? answer "정답 / 해설"
    `full` 과 `empty` 가 *동시에* 1 이 되는 경우는 *디자인 버그* (capacity ≥ 1 인 FIFO 에서는 절대 발생하면 안 됨).
    ```systemverilog
    cp_state : coverpoint {full, empty} {
      illegal_bins both_full_empty = {2'b11};
    }
    ```
    이 bin 에 한 번이라도 hit 되면 시뮬 자체가 error report 함.
