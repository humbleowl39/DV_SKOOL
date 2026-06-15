---
title: "Quiz — 05: CPU DV 방법론"
---

05장의 핵심 — UVM 의 CPU 매핑, step-and-compare, divergence 분류, coverage closure, formal — 을 점검합니다. 정답은 펼치면 보입니다.

[← 05장 본문으로 돌아가기](../../05_cpu_dv_methodology/)

---

## Q1. (Remember)

`uvm_component` 와 `uvm_object` 를 생성할 때 factory 매크로와 생성 인자가 어떻게 다른가?

- [ ] A. component: `uvm_object_utils`, name 만 / object: `uvm_component_utils`, name+parent
- [ ] B. component: `uvm_component_utils`, name+parent / object: `uvm_object_utils`, name 만
- [ ] C. 둘 다 `uvm_component_utils`, 둘 다 name+parent
- [ ] D. 둘 다 name 만 필요하고 매크로 차이는 없다

<details>
<summary>정답 / 해설</summary>

**B**. component 는 phase 를 갖고 계층 트리에 한 번 만들어지는 정적 구조물이므로 *부모*를 알아야 트리에 자리잡는다 — 그래서 `uvm_component_utils` 로 등록하고 생성 시 name+parent 가 필요하다. object 는 런타임에 자유롭게 생멸하는 동적 데이터(sequence/item/config)라 트리 위치가 없으므로 `uvm_object_utils`, name 만으로 생성한다. A 는 둘을 뒤바꿨고, C·D 는 생애주기 차이를 무시한 오답이다. 핵심은 매크로 암기가 아니라 "component=빌드 시 트리로 한 번, object=자극마다 생멸"이라는 생애주기.

</details>

## Q2. (Understand)

CPU 검증이 AXI 브리지 같은 프로토콜 블록 검증과 근본적으로 다른 점을 "정답의 출처" 관점에서 한 문장으로 설명하라.

<details>
<summary>정답 / 해설</summary>

프로토콜 블록은 스코어보드가 *프로토콜 규칙*으로 예상값을 계산할 수 있어 사람이 reference model 을 짜지만, CPU 는 명령·상태의 조합이 천문학적이라 사람이 정답을 못 짜므로 **ISA 를 구현한 ISS 를 golden reference 로 강제**하고 명령 단위 step-and-compare 로 비교한다. 즉 차이의 본질은 "정답을 *사람이 계산*하느냐 vs *ISS 가 산출*하느냐"이며, 이는 CPU 의 방대한 상태 공간에서 비롯된다.

</details>

## Q3. (Apply)

step-and-compare scoreboard 가 RTL retire 정보(actual)와 ISS 결과(expected)를 비교하다 불일치를 만났다. 코드에서 어떻게 처리해야 하며, 왜 그렇게 해야 하는가?

<details>
<summary>정답 / 해설</summary>

**첫 divergence 에서 즉시 `uvm_error` 로 flag 하고, 그 이후 비교가 cascading 되지 않도록 멈추거나 명확히 표시해야 한다.**

```systemverilog
if (it.rd_addr !== e_rd || it.rd_wdata !== e_wdata) begin
  `uvm_error("DIVERGE",
    $sformatf("First divergence @pc=%h: RTL rd[%0d]=%h, ISS=%h",
              it.pc, it.rd_addr, it.rd_wdata, e_wdata))
  // 환경 차원에서 종료/표시 → 이후 cascading 비교 차단
end
```

이유: 첫 불일치 명령의 잘못된 결과가 이후 모든 명령의 입력을 오염시켜 수천 개가 mismatch 로 찍히면 어느 것이 *원인*인지 구분할 수 없게 된다. 첫 divergence 하나만이 root cause 이므로 거기서 멈춰야 디버그가 며칠에서 분 단위로 줄어든다 — DV 의 "first error 를 찾아라" 원칙. (`$display`/`$finish` 가 아니라 `uvm_error` 로 보고하는 것도 포인트.)

</details>

## Q4. (Apply)

랜덤 명령 생성기(ISG)를 설계할 때 반드시 보장해야 하는 4가지 속성을 들고, 각각이 왜 필요한지 한 줄로 답하라.

<details>
<summary>정답 / 해설</summary>

1. **legality(합법성)** — illegal 명령을 걸러내거나 *의도적으로* 주입; 안 그러면 의미 없는 trap 만 양산되거나 예외 경로를 못 친다.
2. **termination(종료성)** — 분기 거리 제한·루프 카운터·최대 명령 수로 무한루프 방지; 안 그러면 테스트가 끝나지 않는다.
3. **interesting-sequence biasing(흥미로운 편향)** — 의존 체인·분기 밀도·메모리 충돌·예외 유발 쪽으로 constraint 가 향하게; 순수 랜덤은 대부분 지루한 nop 류라 corner 를 못 친다.
4. **reproducibility(재현성)** — seed 로 같은 stream 재생성; 안 그러면 발견한 버그를 디버그·회귀에서 재현할 수 없다.

핵심 통찰: "순수 랜덤은 지루한 nop 류 — constraint 로 corner 를 *향하게* 한다."

</details>

## Q5. (Analyze)

긴 회귀에서 "인터럽트가 발생하는 *모든* 테스트가 인터럽트 직후부터 일관되게 발산"한다. RTL 버그라고 단정하기 전에 무엇을 먼저 의심하고, 그 판단 근거는 무엇인가?

<details>
<summary>정답 / 해설</summary>

**먼저 TB 의 인터럽트 동기화 누락(비결정 요소 동기화)을 의심해야 한다.**

판단 근거는 *패턴*이다. 특정 RTL 명령 버그는 보통 특정 명령·정렬에서만 *산발적·국소적*으로 재현된다. 반면 "인터럽트가 있는 *모든* 테스트가 *일관되게*" 발산하는 것은 *체계적* 징후로, 비결정 요소를 RTL→ISS 로 전달하는 결선이 통째로 빠졌을 때 나타난다. 비동기 인터럽트는 RTL 이 *어느 아키텍처 retire 경계*에서 받았는지를 ISS 에 알려야 ISS 도 같은 경계에서 trap 하는데, 이 전달(`rvfi_intr` 류)이 누락되면 ISS 와 RTL 이 *다른 명령*에서 trap 해 그 시점부터 전부 어긋난다. 확인: retire 정보의 인터럽트 플래그가 ISS step 에 반영되는지. 고친 뒤에도 특정 명령에서만 남으면 그때 DUT 버그로 escalate. (산발=DUT, 체계=TB 의 휴리스틱.)

</details>

## Q6. (Evaluate)

한 동료가 "비동기 인터럽트를 ISS 와 RTL *양쪽에 똑같은 사이클*에 주입하면 동기화 문제가 해결된다"고 제안한다. 이 제안을 평가하라.

<details>
<summary>정답 / 해설</summary>

**틀렸다 — *같은 사이클*은 OoO·추측 실행 때문에 *같은 아키텍처 명령 경계*가 아니기 때문이다.** ISS 는 타이밍을 모델링하지 않고 명령을 in-order 로 retire 하지만, RTL 은 같은 사이클에 여러 명령이 서로 다른 단계(추측 포함)에 흩어져 있다. 따라서 "사이클 N 에 인터럽트"라는 기준은 RTL 에서 *어느 명령이 실제로 trap 을 take 하는 경계*인지와 일치하지 않아, ISS 와 RTL 이 서로 다른 명령에서 trap 하게 된다. 올바른 방법은 RTL 이 인터럽트를 take 한 *retire(아키텍처) 경계*를 ISS 에 알려 같은 경계에서 trap 시키는 synchronized injection 이다. 이 "사이클이 아니라 아키텍처 경계" 인지가 시니어 신호다.

</details>

## Q7. (Evaluate)

coverage 리포트에 한 ROB-full 관련 bin 이 회귀를 수백 번 돌려도 안 닫힌다. "시드를 10배로 늘리자"는 제안과 비교해, 더 나은 closure 전략을 우선순위와 함께 정당화하라.

<details>
<summary>정답 / 해설</summary>

**"시드 10배"는 비효율적 오답이다 — 랜덤이 이미 못 닿는 좁은 corner 라면 양을 늘려도 같은 분포를 반복할 뿐이다.** 더 나은 순서:

1. **reachability 분석** — 그 ROB-full 상태가 설계상 *도달 가능*한가. unreachable 이면 waive 근거를 문서화하고 exclude(왜 도달 불가능한지 주석으로 정당화).
2. **directed stimulus / constraint 조정** — ROB 를 채우는 *긴 의존 체인 + 느린 명령(예: 미해결 load)* 을 방향성 자극으로 유도하거나, ISG constraint 를 그쪽으로 강화.
3. **force / whitebox** — 문서화된 TB 문맥에서 내부 상태를 force 로 직접 유도.
4. **formal** — 시뮬로 닿기 힘든 깊은 상태면 formal 로 도달성 자체를 증명.
5. **vplan 재평가** — 애초에 진짜 필요한 bin 인지 검증 계획과 대조.

정당화: coverage hole 은 미검증 리스크지만, 닫는 수단은 *양(더 많은 랜덤)*이 아니라 *방향(타깃 자극)*과 *증명(formal)*이다. 무작정 시드를 늘리면 회귀 시간만 먹고 hole 은 그대로다.

</details>
