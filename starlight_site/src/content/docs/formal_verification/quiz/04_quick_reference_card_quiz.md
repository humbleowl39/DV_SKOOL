---
title: "Quiz — Module 04: Formal Quick Reference"
---

[← Module 04 본문으로 돌아가기](../../04_quick_reference_card/)

---

## Q1. (Recall)

다음 SVA 연산자의 의미를 한 줄로:

- `##N`
- `##[1:N]`
- `[*N]`
- `[->N]`
- `throughout`

<details>
<summary>정답 / 해설</summary>

- `##N` — 정확히 N cycle 후
- `##[1:N]` — 1~N cycle 사이 어딘가에서
- `[*N]` — 정확히 N번 연속 발생
- `[->N]` — N번 발생할 때까지 (비연속 가능)
- `throughout` — 표현식이 시퀀스 전체 동안 참 (예: `req throughout (##[1:5] ack)`)

이 연산자들은 시간적 관계를 정밀하게 표현하기 위한 SVA의 핵심 어휘다. `##N`과 `##[1:N]`은 "언제"를 지정하고, `[*N]`과 `[->N]`은 "몇 번"을 지정한다. `[*N]`은 반드시 N 사이클 연속이어야 하지만 `[->N]`은 중간에 false가 끼어도 N번만 true이면 성립하므로, 버스트 신호에는 `[*N]`을, 산발적 이벤트 카운팅에는 `[->N]`을 쓴다. `throughout`는 긴 시퀀스 동안 특정 조건이 항상 유지됨을 보장할 때 쓰여, "req가 1이어야 하는 동안 ack을 기다린다"는 패턴을 간결하게 표현한다. 이 연산자를 혼동하면 timing이 한 사이클 어긋나거나 검증이 의도와 다른 패턴을 잡게 된다.

</details>
## Q2. (Understand)

PROVEN 결과를 받았는데 cover가 UNCOVERED라면 어떻게 해석해야 하는가?

<details>
<summary>정답 / 해설</summary>

**Vacuous Pass 의심**. Property의 antecedent에 도달하지 못한 것 → assert는 검사할 게 없어서 PASS. 사실상 무의미한 증명.

행동: cover가 UNCOVERED인 이유 분석 → assume이 너무 강해 antecedent 차단했는지, 또는 RTL/spec에 모순이 있는지 확인.

이 상황은 Formal 검증에서 가장 조용하고 위험한 실패 패턴이다. 엔진은 정직하게 "위반을 발견하지 못했다"고 보고하지만, 실제로는 검사 조건에 한 번도 진입하지 않았기 때문이다. 진단 순서는 먼저 assume 목록을 검토해 antecedent를 구조적으로 차단하는 assume이 있는지 확인하고, 없다면 RTL에서 해당 상태에 도달하는 경로가 실제로 존재하는지 살펴본다. assume이 원인이라면 일부를 완화하고, RTL이 원인이라면 spec과 대조해 해당 상태가 설계 의도에 있는지 확인한다. 어느 경우든 cover UNCOVERED는 "검증이 완료됐다"는 주장을 지지할 수 없게 만드는 결정적 신호다.

</details>
## Q3. (Apply)

BOUNDED N=20을 받았다. PROVEN으로 만들기 위해 첫 번째로 시도할 기법은?

<details>
<summary>정답 / 해설</summary>

**Cut Point** 또는 **Abstraction** 먼저 — 가장 적은 위험으로 state space를 축소하는 기법.

Blackbox는 그 영역 동작을 검증 안 한 것이므로 sign-off 시 명시 필요. Assume tightening은 over-constraint 위험이 있으므로 마지막 수단.

N=20 BOUNDED는 state space가 20 스텝 이내로 탐색 가능하지만 induction이 수렴하지 못한 상태다. Cut Point는 DUT를 분할해 각 부분의 state space를 독립적으로 줄이는 방법이므로, 전체 구조를 바꾸지 않으면서도 solver 부담을 경감시킨다. Abstraction은 넓은 데이터 폭이나 큰 카운터를 작은 모델로 대체하므로 수렴에 직접 기여한다. 반면 Blackbox를 무분별하게 적용하면 property와 관련된 로직까지 제거해 PROVEN이 soundness를 잃고, Assume tightening은 입력 공간을 좁혀 실제 버그를 놓칠 수 있어 마지막 수단이다.

</details>
## Q4. (Analyze)

다음 두 SVA 중 어느 것이 데이터 캡처가 필요한가?

```systemverilog
// (a)
a1: assert property (req |-> ##5 ack);

// (b)
a2: assert property (write |-> ##[1:10] (read && rdata == wdata));
```

<details>
<summary>정답 / 해설</summary>

**(b)**. write 시점의 wdata를 read 시점에 비교해야 하므로 **Local Variable**이 필요.

수정:
```systemverilog
a2: assert property (
  logic [31:0] saved;
  (write, saved = wdata) |-> ##[1:10] (read && rdata == saved)
);
```

(a)는 `req |-> ##5 ack`처럼 고정 지연만 확인하므로 이전 사이클 값을 저장할 필요가 없다. 반면 (b)는 write 시점의 `wdata` 값을 1~10 사이클 뒤에 `rdata`와 비교해야 하는데, 그 사이에 `wdata`가 변할 수 있으므로 write 시점의 값을 local variable에 캡처해야 한다. local variable이 없으면 `rdata == wdata`는 read 시점의 wdata와 비교하게 되어 타이밍 오류가 있는 DUT도 통과시킬 수 있다. local variable은 SVA에서 시간 간격을 넘어 데이터 의존성을 표현하는 유일한 메커니즘이다.

</details>
## Q5. (Evaluate)

다음 중 Formal이 **가장 강력한** 적용 영역은?

- [ ] A. 1MB SRAM의 모든 셀 read-back
- [ ] B. AXI handshake protocol compliance
- [ ] C. 큰 곱셈기의 출력 정확성
- [ ] D. CPU 실행 trace 검증

<details>
<summary>정답 / 해설</summary>

**B**. Protocol 검증은 작은 control logic + 명확한 spec rule → Formal의 sweet spot.

A: state space 폭발(2^(8M)). C: data path, abstraction 필요. D: 실행 trace는 시뮬레이션 영역.

Formal이 강력한 영역과 약한 영역을 구분하는 기준은 state space 크기와 spec의 명제 표현 가능성이다. B의 AXI handshake는 valid, ready, resp 같은 소수의 제어 신호로 이루어진 유한한 상태 공간을 가지며 "valid가 assert되면 ready가 오기 전까지 변하지 않아야 한다"처럼 명제로 정확히 표현 가능하다. 반면 A는 1MB SRAM의 모든 셀이 독립 상태여서 state space가 폭발적으로 커지고, C의 곱셈기는 데이터 경로 넓이 자체가 문제여서 abstraction 없이는 수렴이 어렵다. D는 CPU 실행 trace처럼 순서 의존적인 동작 검증은 시뮬레이션이나 co-simulation이 더 적합하다.

</details>
