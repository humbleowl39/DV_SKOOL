# Quiz — Module 06: 실무 패턴 & 안티패턴

[← Module 06 본문으로 돌아가기](../06_practical_patterns.md)

---

## Q1. (Remember)

"God Env" 안티패턴의 정의는?

- [ ] A. env가 너무 많은 자식을 가짐
- [ ] B. env가 driver/monitor를 직접 보유해 Agent 캡슐화 원칙을 깨는 것
- [ ] C. test가 env 없이 동작
- [ ] D. env가 Phase를 오버라이드 안 함

??? answer "정답 / 해설"
    **B**. "God Env"는 UVM에서 Agent 캡슐화 원칙을 위반하는 안티패턴입니다. Driver, Monitor, Sequencer는 Agent 안에 묶여야 Active/Passive 전환, 다중 인스턴스화, 프로젝트 간 재사용이 가능합니다. Env가 이들을 직접 보유하면 다른 프로젝트에 Agent 단위로 이식할 수 없고, Active/Passive 모드 분기를 env가 직접 관리해야 하므로 복잡도가 폭발합니다. A(너무 많은 자식)는 문제일 수 있지만 "God Env"의 정의가 아니고, C·D는 이 안티패턴과 무관합니다.

## Q2. (Understand)

"Monitor에서 sequence 시작" 안티패턴이 잘못된 이유를 책임 분리 관점에서 설명하세요.

??? answer "정답 / 해설"
    UVM의 책임 분리 원칙에서 Monitor는 관찰과 트랜잭션 변환만 담당하고, 자극을 인가할지 여부는 Test 또는 Virtual Sequence가 결정합니다. Monitor가 Sequence를 시작하면 세 가지 문제가 생깁니다. 첫째, 관찰과 자극 인가가 한 컴포넌트 안에 혼재되어 "왜 이 트랜잭션이 발생했는가?"를 추적하기 어렵습니다. 둘째, Passive Agent에서도 Monitor는 존재하는데, 이때 Monitor가 Sequence를 시작하면 자극 인가 주체가 없어야 하는 환경에서 DUT가 의도치 않게 구동됩니다. 셋째, Test에서 시나리오 순서를 통제하려 해도 Monitor가 독립적으로 Sequence를 시작하므로 제어권을 잃게 됩니다.

## Q3. (Apply)

다음 코드에서 안티패턴을 한 줄로 수정하세요.
```systemverilog
function void connect_phase(uvm_phase phase);
  drv.vif = top_vif;  // 직접 핸들 대입
endfunction
```

??? answer "정답 / 해설"
    `drv.vif = top_vif;`처럼 핸들을 직접 대입하면 두 컴포넌트가 긴밀하게 결합되어, 컴포넌트 계층이 바뀌거나 재사용될 때 connect_phase 코드를 모두 수정해야 합니다. 올바른 패턴은 `top` 모듈에서 `uvm_config_db#(virtual apb_if)::set(null, "uvm_test_top.env.agent.*", "vif", top_vif);`로 등록하고, driver의 `build_phase`에서 `if (!uvm_config_db#(virtual apb_if)::get(this, "", "vif", vif)) \`uvm_fatal(...)``으로 받는 것입니다. 이렇게 하면 계층 경로만 맞추면 어떤 환경에서도 동일한 driver 코드가 동작합니다.

## Q4. (Analyze)

Sequencer Hierarchy 패턴(virtual sequencer가 sub-sequencer 핸들을 보유)의 가장 큰 이점은?

- [ ] A. 메모리 절약
- [ ] B. virtual sequence가 `p_sequencer.apb_sqr`처럼 깔끔하게 sub-sequencer에 접근해 multi-agent 시나리오를 한 곳에서 조율
- [ ] C. 컴파일 속도 향상
- [ ] D. Phase 자동 동기화

??? answer "정답 / 해설"
    **B**. Virtual Sequencer는 여러 sub-sequencer 핸들(`apb_sqr`, `axi_sqr` 등)을 멤버로 보유합니다. Virtual Sequence에서 `\`uvm_declare_p_sequencer(my_vseqr)`로 타입 있는 `p_sequencer` 핸들을 선언하면 `p_sequencer.apb_sqr.start(seq)`처럼 직접 접근할 수 있어, multi-agent 시나리오를 한 body() 안에서 타이밍까지 조율할 수 있습니다. 이 패턴 없이 Virtual Sequence를 작성하면 env 핸들을 uvm_object 캐스트로 끌어오는 위험한 코드가 반복됩니다. A·C·D는 이 패턴의 실제 이점과 무관합니다.

## Q5. (Create)

새 SoC IP의 검증을 from scratch로 시작합니다. **smoke test 통과까지 최소 5단계**의 의존 순서를 답하세요.

??? answer "정답 / 해설"
    1. **Interface SV 작성** — DUT 포트를 매핑하고 clocking block과 modport를 정의합니다. 이것이 없으면 Driver도 Monitor도 신호에 접근할 수 없습니다.
    2. **Sequence Item 작성** — 트랜잭션 필드와 기본 constraint를 정의합니다. Driver와 Sequence가 주고받는 데이터 계약서에 해당합니다.
    3. **최소 Agent 구현** — Driver는 신호 인가 1건, Monitor는 신호 샘플링 1건만 되는 최소 구현으로 시작합니다.
    4. **Top TB + Test 1개 작성** — build → connect → reset → 1 트랜잭션 인가 흐름이 연결되는 것을 확인합니다.
    5. **Smoke test 실행** — 단일 트랜잭션이 인가되고 Monitor가 캡처하는 log를 확인해, 전체 파이프라인이 끊기지 않았음을 검증합니다.
