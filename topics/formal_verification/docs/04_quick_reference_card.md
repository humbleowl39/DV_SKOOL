# Formal Verification — Quick Reference Card

## 한줄 요약
```
Formal = 수학적 전수 검사. SVA로 Property 정의 → Formal Engine이 모든 상태에서 증명(PROVEN) 또는 반례(FAILED) 반환. 시뮬레이션과 상호 보완.
```

---

## 핵심 정리

| 주제 | 핵심 포인트 |
|------|------------|
| Formal vs Sim | Formal=전수검사(증명), Sim=샘플링(시나리오) |
| Engine 원리 | SAT/SMT Solver + Induction(귀납법)으로 증명 |
| 결과 | PROVEN(증명) / FAILED(반례) / BOUNDED(N cycle까지) |
| BOUNDED 원인 | Inductive Step 실패 → Helper/Abstraction/분할로 대응 |
| SVA 3요소 | assert(검증), assume(가정), cover(도달성) |
| Vacuous Pass | Antecedent 미발생 → 자동 PASS → cover로 방지 필수 |
| 적합 대상 | FSM, 프로토콜, FIFO, Arbiter, 보안, Connectivity |
| 한계 | State Explosion → 큰 데이터 경로, 성능 검증 불가 |
| Assume 위험 | 과도 → False PROVEN. Cover로 검증 필수 |
| Convergence | Blackbox → Abstraction → Helper → Assume → 분할 → Bounded 수용 |
| Bind | DUT 수정 없이 SVA 연결 → Formal + Sim 재사용 |
| 도구 | JasperGold (Cadence) — FPV, CON, SEQ, X-Prop |
| Sign-off | PROVEN/BOUNDED + cover COVERED + assume 감사 + COI + 완전성 |

---

## SVA 핵심 연산자 빠른 참조

```
##N           N cycle 지연
##[M:N]       M~N cycle 범위
|->           Overlapping implication (같은 cycle)
|=>           Non-overlapping (다음 cycle)
[*N]          N회 연속 반복
[*M:N]        M~N회 반복
[->N]         N번째 goto 반복
[=N]          N번 비연속 반복
$rose(x)      0→1 전환
$fell(x)      1→0 전환
$stable(x)    값 유지
$past(x,N)    N cycle 전 값
s_eventually  언젠가 참 (Formal only)
throughout    구간 동안 유지
intersect     두 시퀀스 동시 시작+종료

$onehot(x)    정확히 1비트만 1 (FSM one-hot)
$onehot0(x)   최대 1비트만 1 (0 허용)
$countones(x) 1인 비트 수
$isunknown(x) X/Z 포함 여부
```

## 자주 쓰는 SVA 패턴

```systemverilog
// 핸드셰이크: valid 올라가면 ready까지 유지
$rose(valid) |-> valid throughout (##[0:$] ready);

// FIFO Overflow 방지
!(wr_en && full);

// FSM 불법 상태
!(state inside {ILLEGAL_STATES});

// 리셋 후 초기값
$fell(rst) |-> ##1 (out == 0);

// 요청 후 응답 보장
req |-> s_eventually(ack);
```

---

## SVA 함정 체크리스트

```
□ disable iff 누락?          → 리셋 중 위반 보고 방지
□ 리셋 극성 맞는가?          → active-low면 disable iff (!rst_n)
□ |-> vs |=> 맞는가?         → 설계 latency에 맞는 연산자 선택
□ Vacuous Pass 방지 cover?   → 모든 assert에 대응 cover 필수
□ Local variable 필요?       → write/read 데이터 비교 시
□ strong/weak 구분?          → 시뮬레이션에서 완료 보장 필요 시 strong
```

## Convergence 순서

```
BOUNDED → ① Blackbox → ② Abstraction → ③ Helper Assert
        → ④ Assume(최소) → ⑤ Property 분할 → ⑥ Bounded 수용
```

## 면접 골든 룰

1. **Formal = 전수검사**: "시뮬레이션의 샘플링 한계를 수학적 증명으로 보완"
2. **Engine = SAT/SMT + Induction**: "Boolean 수식 → SAT 풀이 + 귀납법으로 무한 cycle 증명"
3. **PROVEN의 의미**: "어떤 입력/상태에서도 성립 — 수학적 보장"
4. **BOUNDED ≠ PROVEN**: "Induction 미완 — Helper/Abstraction으로 Convergence 시도"
5. **Vacuous Pass**: "Antecedent 미발생 → 자동 PASS — cover로 반드시 방지"
6. **State Explosion**: "Formal의 근본 한계 — Blackbox + Abstraction 필수"
7. **Assume 주의**: "과도하면 False PROVEN — Cover로 검증"
8. **병행 전략**: "Formal=제어로직/프로토콜, Sim=데이터경로/성능/대규모"
9. **Sign-off**: "PROVEN + cover COVERED + assume 감사 + 문서화"

---

## 이력서 연결

| 항목 | 면접 질문 | 핵심 답변 |
|------|----------|----------|
| Mapping Table FV Lead | "Formal을 어떻게 적용했나?" | 5가지 핵심 Property 증명 (Hit/Miss 배타, 데이터 무결성 등) |
| JasperGold | "도구 경험은?" | FPV 앱으로 Property Checking, Counterexample 파형 분석 |
| Convergence 경험 | "BOUNDED는 어떻게 해결했나?" | Blackbox + Helper Assert로 Induction 성공시킴 |
| SVA 기술 스킬 | "SVA를 어디에 사용했나?" | Formal(증명) + 시뮬레이션(런타임 체커) 양쪽에서 Bind로 재사용 |
| 검증 품질 | "Vacuous Pass를 어떻게 방지?" | 모든 assert에 대응 cover, assume 감사 프로세스 |

---

## Formal 적용 판단 플로우

```
이 IP/블록에 Formal을 적용할까?

  상태 공간이 관리 가능한가? (레지스터 수, 메모리 크기)
    NO → 시뮬레이션 (또는 Abstraction 후 Formal)
    YES ↓

  기능 명세가 Property로 표현 가능한가?
    NO → 시뮬레이션 (E2E 데이터 비교)
    YES ↓

  시뮬레이션으로 놓치기 쉬운 코너 케이스가 있는가?
    YES → Formal 강력 추천 ✓
    NO → 시뮬레이션으로 충분
```
