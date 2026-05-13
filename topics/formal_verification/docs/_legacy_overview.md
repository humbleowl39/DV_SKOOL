# Formal Verification — 개요 및 컨셉 맵

## 학습 플랜
- **레벨**: Intermediate (Mapping Table IP FV Lead 경험 기반)
- **목표**: Formal의 원리, SVA 작성, JasperGold 활용, 시뮬레이션과의 차이를 논리적으로 설명할 수 있는 수준

## 핵심 용어집 (Glossary)

### 검증 기본 개념

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **Formal** | Formal Verification | 수학적 증명으로 **모든** 가능한 입력/상태에서 속성 검증 |
| **Simulation** | — | 특정 시나리오만 실행하는 샘플링 기반 검증 |
| **Property** | — | 설계가 만족해야 할 시간적 속성 (SVA로 작성) |
| **Counterexample** | — | 속성을 위반하는 구체적 입력 시퀀스 (자동 생성) |

### 결과 상태

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **PROVEN** | — | 모든 가능한 상태에서 Property 성립 (수학적 증명 완료) |
| **FAILED** | — | 위반 발견 → 반례 자동 생성 |
| **BOUNDED** | — | N cycle까지만 증명, 그 이후 미검증 (Induction 미완) |

### 엔진 & 기법

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **SAT** | Boolean Satisfiability | 회로를 Boolean 수식으로 변환하여 풀이 |
| **SMT** | SAT + Theory | SAT에 비트벡터, 산술 등 이론 추가 |
| **Induction** | 수학적 귀납법 | Base Case + Inductive Step으로 무한 cycle 증명 |
| **FPV** | Formal Property Verification | SVA Property를 SAT/SMT로 증명 |
| **LEC** | Logic Equivalence Checking | RTL vs Netlist 동일성 검증 (합성 후) |
| **CON** | Connectivity Verification | SoC 레벨 신호 연결 정확성 검증 |

### SVA 핵심 요소

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **SVA** | SystemVerilog Assertions | 설계 속성을 시간적 관계로 표현하는 선언적 언어 |
| **assert** | — | "이 속성은 항상 참이어야 함" (증명 대상) |
| **assume** | — | "이 속성을 입력 제약으로 가정" (탐색 공간 축소) |
| **cover** | — | "이 시나리오에 도달 가능한가?" (Vacuous Pass 방지) |
| **\|->** | Overlapping Implication | 전제와 같은 cycle에서 결론 시작 |
| **\|=>** | Non-overlapping Implication | 전제 다음 cycle에서 결론 시작 |
| **$rose/$fell** | — | 상승/하강 엣지 감지 |
| **s_eventually** | Strong Eventually | 언젠가 반드시 참이 됨 (Formal 전용, liveness) |

### 상태 공간 축소

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **Blackboxing** | — | 검증 대상 외 서브모듈을 빈 박스로 교체 |
| **Cut Point** | — | 신호를 자유 입력으로 교체하여 독립 검증 |
| **Abstraction** | — | 넓은 데이터/카운터를 좁은 범위로 축소 |
| **COI** | Cone of Influence | Property에 영향을 주는 로직의 범위 |
| **State Explosion** | — | N-bit → 2^N 상태로 탐색 불가능해지는 문제 |
| **Vacuous Pass** | — | 전제(Antecedent)가 한 번도 참이 안 되어 자동 PASS (위험!) |

### 도구 & Sign-off

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **JasperGold** | — | Cadence의 Formal 검증 도구 (FPV, CON, SEQ 앱) |
| **Bind** | — | DUT를 수정하지 않고 외부에서 SVA를 연결하는 비침투적 방식 |
| **Sign-off** | — | PROVEN + COVERED + 문서화 완료 후 검증 종료 선언 |

---

## 컨셉 맵

```d2
direction: down

# unparsed: SPEC["Property Specification<br/>(SVA Assertions)"]
# unparsed: ENG["Formal Verification Engine<br/>- Model Checking<br/>- Bounded / Unbounded<br/>- Counterexample Gen"]
# unparsed: PV["PROVEN<br/>(증명됨)"]
# unparsed: FL["FAILED<br/>(반례)"]
# unparsed: BD["BOUNDED<br/>(제한적 증명)"]
SPEC -> ENG
ENG -> PV
ENG -> FL
ENG -> BD
```

## 학습 단위 (Units)

| # | 단위 | 핵심 질문 |
|---|------|----------|
| 1 | **Formal 기본 개념** | Formal은 시뮬레이션과 무엇이 다르고, 왜 필요한가? |
| 2 | **SVA (SystemVerilog Assertions)** | Property를 어떻게 작성하고, 어떤 패턴이 있는가? |
| 3 | **JasperGold 활용 + DV 전략** | 실무에서 Formal을 어떻게 적용하고, 한계는 무엇인가? |

## 이력서 연결

| 이력서 항목 | 관련 Unit | 면접 시 활용 |
|------------|----------|-------------|
| Mapping Table IP FV Lead | Unit 3 | JasperGold 실무 + 검증 전략 |
| SVA 기술 스킬 | Unit 2 | Assertion 작성 능력 |
| BootROM/HCI 검증에서 SVA 활용 | Unit 2 | 시뮬레이션 + Formal 병행 전략 |


--8<-- "abbreviations.md"
