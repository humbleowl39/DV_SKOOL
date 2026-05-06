# Formal Verification 용어집

핵심 용어 ISO 11179 형식 정의.

---

## A — Assertion / Assume / Abstraction

### Assertion (assert)

**Definition.** 설계가 만족해야 하는 명제로, 시뮬레이션에서는 위반 시 에러를, Formal에서는 위반 가능 여부를 증명/반증한다.

**Source.** IEEE 1800 §16, SVA Spec.

**Related.** assume, cover, property.

**Example.**
```systemverilog
ap_handshake: assert property (@(posedge clk) valid |-> ##[1:5] ready);
```

**See also.** [Module 02 — SVA](02_sva.md)

### Assume

**Definition.** Formal Verification에서 입력 신호가 만족한다고 가정하는 제약으로, 실제 환경의 동작을 모델링하여 입력 공간을 제한한다.

**Source.** IEEE 1800 §16.

**Related.** Over-constraint, Sign-off audit.

**Risk.** 너무 강한 assume = false PROVEN. Spec과 1:1 매핑 + 대응 cover 필수.

**See also.** [Module 03](03_jaspergold_and_strategy.md)

### Abstraction

**Definition.** 큰 데이터 폭/카운터 범위를 작은 모델로 대체하여 state space를 축소하는 기법.

**Source.** Formal verification literature.

**Related.** Cut Point, Blackbox.

**Example.** 32-bit counter를 4-bit + saturation으로 abstract하여 동일 동작을 검증.

**See also.** [Module 03](03_jaspergold_and_strategy.md)

---

## B — Blackbox / BOUNDED

### Blackbox

**Definition.** 검증 대상이 아닌 모듈을 unconstrained inputs/outputs로 추상화하여 state space에서 제거하는 기법.

**Source.** JasperGold User Guide.

**Related.** COI (Cone of Influence), Cut Point.

**Example.** Cache controller 검증 시 SRAM 모듈을 blackbox 처리.

**See also.** [Module 03](03_jaspergold_and_strategy.md)

### BOUNDED

**Definition.** Property가 N cycle 내에는 위반되지 않지만 N+1 cycle 이후는 미증명인 Formal 결과.

**Source.** Formal verification result types.

**Related.** PROVEN, CEX (Counterexample), Induction.

**Action.** Convergence 전략 적용 (Cut Point, Abstraction, Assume tightening) → PROVEN으로 전환.

**See also.** [Module 01](01_formal_fundamentals.md)

---

## C — CEX / Cut Point / Cover / Convergence

### CEX (Counterexample)

**Definition.** Formal 엔진이 property 위반을 유발하는 최소 입력 시퀀스로 자동 생성하는 반례.

**Source.** SAT/SMT solver output.

**Related.** Debug, FAILED.

**Use.** RTL 버그 또는 Assume 부족 (false negative)인지 분석.

**See also.** [Module 03](03_jaspergold_and_strategy.md)

### Cut Point

**Definition.** RTL의 특정 신호를 free input으로 만들어 그 이전 영역을 제거하고 이후 영역만 검증하는 기법.

**Source.** JasperGold User Guide.

**Related.** Blackbox, Abstraction.

**Example.** Pipeline의 중간 stage 신호를 cut → stage N 이후만 독립 검증.

**See also.** [Module 03](03_jaspergold_and_strategy.md)

### Cover

**Definition.** 특정 시나리오에 도달 가능한지 확인하는 SVA property로, Vacuous Pass 방지의 표준 기법.

**Source.** IEEE 1800 §16.

**Related.** Assertion, Vacuous Pass.

**Example.** `cp_handshake: cover property (@(posedge clk) valid && ready);`

**See also.** [Module 02](02_sva.md)

### Convergence

**Definition.** Formal 검증이 BOUNDED에서 PROVEN으로 도달하는 과정 또는 그 가능성.

**Source.** Formal verification methodology.

**Related.** State Explosion, Cut Point.

**See also.** [Module 03](03_jaspergold_and_strategy.md)

---

## I — Induction

### Induction

**Definition.** Base case(reset 후)와 Inductive step(N→N+1 cycle)의 두 단계 증명으로 무한 cycle property를 증명하는 수학적 기법.

**Source.** Mathematical induction in formal verification.

**Related.** PROVEN, BOUNDED.

**Note.** Inductive step 실패 시 BOUNDED → invariant 강화 또는 abstraction 필요.

**See also.** [Module 01](01_formal_fundamentals.md)

---

## P — Property / PROVEN

### Property

**Definition.** SVA에서 시간적 관계를 갖는 명제 표현으로, sequence와 implication을 조합해 정의.

**Source.** IEEE 1800 §16.

**Related.** Sequence, Implication, Assert.

**See also.** [Module 02](02_sva.md)

### PROVEN

**Definition.** Property가 reset 후 모든 가능한 입력 시퀀스에 대해 위반되지 않음을 Formal 엔진이 수학적으로 증명한 결과.

**Source.** Formal verification result types.

**Related.** BOUNDED, CEX, Sign-off.

**Caution.** Vacuous PROVEN, Over-constrained PROVEN은 false confidence — cover와 Assume 감사 필수.

**See also.** [Module 01](01_formal_fundamentals.md)

---

## V — Vacuous Pass

### Vacuous Pass

**Definition.** Implication property의 antecedent(전제)가 한 번도 참이 되지 않아 자동으로 PASS하는 의미 없는 통과.

**Source.** SVA semantics.

**Related.** Cover, Antecedent unreachable.

**Detection.** 모든 assert에 대응하는 cover 작성 — UNCOVERED면 vacuous pass.

**See also.** [Module 02](02_sva.md)

---

## 추가 약어

| 약어 | 풀네임 | 의미 |
|------|--------|------|
| **SVA** | SystemVerilog Assertions | SV의 assertion 언어 |
| **PSL** | Property Specification Language | SVA의 선조 격 (현재는 SVA가 표준) |
| **COI** | Cone of Influence | Property가 의존하는 입력 범위 |
| **SAT** | Boolean Satisfiability | Formal 엔진 내부 알고리즘 |
| **SMT** | Satisfiability Modulo Theories | SAT 확장, 산술 연산 지원 |
| **CEX** | Counterexample | 반례 |
| **JG** | JasperGold | Cadence Formal 도구 |
