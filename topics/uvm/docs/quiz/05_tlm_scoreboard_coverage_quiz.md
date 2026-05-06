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
    **B**. 한 번 connect된 모든 구독자(SB, Coverage, Logger 등)가 같은 트랜잭션을 각자의 `write()` 콜백으로 받음. 비동기/non-blocking.

## Q2. (Understand)

In-order Scoreboard(단일 큐 + pop_front 비교)를 OoO 응답을 가진 AXI 트래픽에 적용하면 무엇이 잘못되는가?

??? answer "정답 / 해설"
    AXI는 같은 ID 내 in-order, ID 간 OoO이 정상입니다. Master가 ID=0,1,2를 보내고 Slave가 ID=2,0,1로 응답하면, expected 큐 head는 0인데 actual로 2가 와서 첫 비교부터 mismatch. 수정: per-ID 큐(associative array `expected[id][$]`)를 두고 응답이 오면 해당 ID 큐의 front와 비교.

## Q3. (Apply)

Coverage subscriber에서 covergroup 샘플링은 어디서 호출하는 것이 표준인가?

- [ ] A. `build_phase`
- [ ] B. `connect_phase`
- [ ] C. `run_phase`의 `forever` 루프
- [ ] D. `write()` 콜백 안

??? answer "정답 / 해설"
    **D**. Monitor가 트랜잭션을 broadcast하면 subscriber의 `write(t)`가 호출됩니다. 거기서 `this.item = t; cg.sample();` 패턴으로 샘플링하면 sampling 시점이 트랜잭션 발생 시점과 정확히 일치.

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
    **B**. cross는 곱집합이므로 4 × 2 = **8개 bin**. cp_a 단독 4 + cp_b 단독 2 + cross 8 = 총 14 coverage points.

## Q5. (Evaluate)

Coverage closure 전략으로 가장 효과적인 순서는?

- [ ] A. 시드 다양화 → 타겟 시퀀스 → cross 분석
- [ ] B. cross 분석 → 시드 다양화 → 타겟 시퀀스
- [ ] C. 타겟 시퀀스 → cross 분석 → 시드 다양화
- [ ] D. 위 셋 동시에 처음부터

??? answer "정답 / 해설"
    **A**. (1) 시드 다양화로 baseline 커버리지 확보 → (2) 비어있는 hole을 cross 분석으로 식별 → (3) 그 hole만 정확히 채우는 타겟 시퀀스. 처음부터 타겟 시퀀스로 가면 baseline이 부족해 hole 식별이 어려움.
