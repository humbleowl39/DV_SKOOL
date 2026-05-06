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
    **B**. Agent로 묶여야 할 driver/monitor/sequencer를 env가 직접 보유하면 재사용 불가, Active/Passive 분리 안 됨.

## Q2. (Understand)

"Monitor에서 sequence 시작" 안티패턴이 잘못된 이유를 책임 분리 관점에서 설명하세요.

??? answer "정답 / 해설"
    Monitor의 책임은 **관찰**입니다. Sequence 시작은 **자극 인가 결정**으로 test 또는 virtual sequence의 책임. Monitor가 sequence를 시작하면 (1) 관찰과 자극이 한 곳에 섞여 디버그 어려움, (2) Passive Agent 모드에서 monitor만 살아있을 때 의도치 않게 자극이 발생, (3) test가 환경의 동작을 통제할 수 없게 됨.

## Q3. (Apply)

다음 코드에서 안티패턴을 한 줄로 수정하세요.
```systemverilog
function void connect_phase(uvm_phase phase);
  drv.vif = top_vif;  // 직접 핸들 대입
endfunction
```

??? answer "정답 / 해설"
    `top` 모듈에서 `uvm_config_db#(virtual apb_if)::set(null, "uvm_test_top.env.agent.*", "vif", top_vif);`로 등록하고, driver의 `build_phase`에서 `uvm_config_db#(virtual apb_if)::get(this, "", "vif", vif);`로 받기.

## Q4. (Analyze)

Sequencer Hierarchy 패턴(virtual sequencer가 sub-sequencer 핸들을 보유)의 가장 큰 이점은?

- [ ] A. 메모리 절약
- [ ] B. virtual sequence가 `p_sequencer.apb_sqr`처럼 깔끔하게 sub-sequencer에 접근해 multi-agent 시나리오를 한 곳에서 조율
- [ ] C. 컴파일 속도 향상
- [ ] D. Phase 자동 동기화

??? answer "정답 / 해설"
    **B**. virtual sequencer 없이 multi-agent를 조율하려면 매번 env에서 sequencer 핸들을 끌어오는 보일러플레이트가 반복됩니다. virtual sequencer 패턴이 이 부분을 표준화.

## Q5. (Create)

새 SoC IP의 검증을 from scratch로 시작합니다. **smoke test 통과까지 최소 5단계**의 의존 순서를 답하세요.

??? answer "정답 / 해설"
    1. **Interface SV 작성** — DUT 포트 매핑, clocking block, modport
    2. **Sequence Item** — 트랜잭션 필드와 기본 constraint
    3. **최소 Agent** — Driver 시그널 인가만, Monitor sample만
    4. **Top + Test 1개** — build → connect → reset → 1 transaction
    5. **Smoke test 실행** — 1 트랜잭션 인가/캡처 확인, log 검증
