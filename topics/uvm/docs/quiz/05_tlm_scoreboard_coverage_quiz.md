# Quiz — Module 05: TLM, Scoreboard, Coverage

[← Module 05 본문으로 돌아가기](../05_tlm_scoreboard_coverage.md)

---

## Q1. (Remember)

`uvm_analysis_port`의 fan-out 특성은?

- [ ] A. 1:1 (하나의 구독자에만 전달)
- [ ] B. 1:N broadcast (여러 구독자 각자 처리)
- [ ] C. N:1 aggregation
- [ ] D. blocking get/put

??? answer "정답 / 해설"
    **B**. `uvm_analysis_port`는 `write()` 한 번 호출로 연결된 모든 구독자(Scoreboard, Coverage Subscriber, Logger 등)에게 동일한 트랜잭션 핸들을 전달합니다. 각 구독자는 자신의 `write()` 콜백에서 독립적으로 처리하므로, Monitor 하나로 Scoreboard와 Coverage를 동시에 구동하는 팬아웃 구조가 가능합니다. A(1:1)는 `uvm_blocking_put_port` 같은 포인트-투-포인트 포트의 특성이고, C(N:1)는 여러 포트가 하나의 export에 연결되는 형태이며, D(blocking)는 analysis_port의 특성이 아닙니다.

## Q2. (Understand)

In-order Scoreboard(단일 큐 + pop_front 비교)를 OoO 응답을 가진 AXI 트래픽에 적용하면 무엇이 잘못되는가?

??? answer "정답 / 해설"
    AXI 프로토콜에서 같은 AXI ID 내에서는 응답이 in-order이지만, 서로 다른 ID 간에는 out-of-order 응답이 허용됩니다. 단순 단일 큐 Scoreboard는 expected 큐에 삽입된 순서(ID=0, 1, 2)대로 pop_front해 비교하므로, DUT가 ID=2를 먼저 응답하면 expected queue의 첫 항목(ID=0)과 actual(ID=2)이 불일치해 false error를 발생시킵니다. 올바른 수정 방법은 `expected[int][$]` 형태의 per-ID associative 큐를 사용해, 응답이 오면 해당 ID의 큐 front와만 비교하는 것입니다.

## Q3. (Apply)

Coverage subscriber에서 covergroup 샘플링은 어디서 호출하는 것이 표준인가?

- [ ] A. `build_phase`
- [ ] B. `connect_phase`
- [ ] C. `run_phase`의 `forever` 루프
- [ ] D. `write()` 콜백 안

??? answer "정답 / 해설"
    **D**. Coverage Subscriber에서 covergroup은 Monitor가 트랜잭션을 broadcast할 때, 즉 `write(t)` 콜백이 호출되는 시점에 샘플링해야 합니다. 그래야 "이 트랜잭션이 발생했다"는 사실과 covergroup 샘플이 1:1로 대응됩니다. `build_phase`(A)나 `connect_phase`(B)에서는 아직 트랜잭션이 없어 샘플링이 무의미하고, `run_phase`의 `forever` 루프(C)는 트랜잭션 발생 시점과 polling 시점이 어긋날 수 있어 샘플 손실이 생깁니다.

## Q4. (Analyze)

다음 covergroup의 cross가 만들어내는 bin 수는?
```systemverilog
covergroup cg;
  cp_a: coverpoint x { bins b[] = {[0:3]}; }   // 4 bins
  cp_b: coverpoint y { bins b[] = {[0:1]}; }   // 2 bins
  cross cp_a, cp_b;
endgroup
```

- [ ] A. 6
- [ ] B. 8
- [ ] C. 4
- [ ] D. 1

??? answer "정답 / 해설"
    **B**. `cross`는 두 coverpoint의 bin 집합에 대한 곱집합(Cartesian product)을 생성합니다. `cp_a`가 4개 bin, `cp_b`가 2개 bin이면 cross bin은 4 × 2 = 8개입니다. A(6)은 덧셈 착오이고, C(4)는 cp_a bin 수만 본 오답이며, D(1)는 cross 전체를 하나로 오해한 경우입니다. 참고로 covergroup 전체의 coverage point 수는 cp_a 4 + cp_b 2 + cross 8 = 총 14개입니다.

## Q5. (Evaluate)

Coverage closure 전략으로 가장 효과적인 순서는?

- [ ] A. 시드 다양화 → 타겟 시퀀스 → cross 분석
- [ ] B. cross 분석 → 시드 다양화 → 타겟 시퀀스
- [ ] C. 타겟 시퀀스 → cross 분석 → 시드 다양화
- [ ] D. 위 셋 동시에 처음부터

??? answer "정답 / 해설"
    **A**. Coverage closure는 단계적으로 접근해야 합니다. 먼저 다양한 시드로 랜덤 regression을 돌려 기본적으로 도달 가능한 영역을 채우고, 그 결과 보고서에서 지속적으로 비어있는 bin을 cross 분석으로 찾아냅니다. 그 후에야 해당 bin만을 목표로 하는 constrained sequence를 작성하면 낭비 없이 closure를 달성할 수 있습니다. B처럼 처음부터 cross 분석을 하면 baseline이 없어 어떤 hole이 진짜 어려운 것인지 판단하기 어렵고, C처럼 타겟 시퀀스를 먼저 쓰면 어떤 시나리오가 필요한지 모른 채 작업하게 됩니다.
