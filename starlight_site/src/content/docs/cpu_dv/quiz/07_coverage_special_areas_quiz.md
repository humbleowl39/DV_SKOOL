---
title: "Quiz — Module 07: ISA Functional Coverage & 특수 검증 영역"
---

[← Module 07 본문으로 돌아가기](../../07_coverage_special_areas/)

---

## Q1. (Remember)

privilege mode 검증에서 "S-mode 에 _도달_ 했다"(단일 coverpoint)보다 버그가 더 잘 숨는, 본체로 봐야 하는 coverage 축은?

- [ ] A. 단일 coverpoint(모드 도달)
- [ ] B. transition bins(모드 전이)
- [ ] C. 명령 종류 coverpoint
- [ ] D. 레지스터 번호 coverpoint

<details>
<summary>정답 / 해설</summary>

**B**. privilege 버그(권한 체크 누락, 잘못된 `mepc`/`MPP` 해석, escalation)는 거의 항상 _전이 순간_ 에 있습니다. 따라서 transition bins(M=>S, S=>U, U=>(trap)=>M 등)와 그 위의 cross(전이 × trap 원인)가 본체이고, 단일 coverpoint(모드 도달, A)는 baseline 에 불과합니다. C·D 는 명령-레벨 coverage 로 privilege 전이와 다른 차원입니다.

</details>

## Q2. (Understand)

memory ordering 검증이 "load 가 맞는 값을 읽었는가"(값 비교)가 _아니라_ 무엇을 보는지, 왜 그런지 설명하라.

<details>
<summary>정답 / 해설</summary>

memory ordering 검증은 _관찰 순서가 메모리 모델(RISC-V RVWMO 등)을 지키는가_ 를 봅니다. 단일 코어 관점의 "맞는 값" 환원으로는 부족한 이유는, 약한 메모리 모델이 load/store 재정렬을 _허용_ 하기 때문에 같은 프로그램이라도 _여러_ 결과가 합법적일 수 있기 때문입니다. 특히 multi-hart 에서는 두 hart 의 발화 순서에 따라 메모리 모델이 정의하는 _허용/금지 결과 집합_ 이 있고, 검증은 _허용되지 않은 결과가 안 나오는지_ 를 봐야 합니다. 그래서 litmus test(정형화된 작은 동시성 패턴)로 순서 시나리오를 만들어 검사하는 것이 표준입니다.

</details>

## Q3. (Apply)

인터럽트 관련 cross coverage 의 한쪽 bin 만 채워진다 — 인터럽트가 항상 load 명령 경계에서만 잡힌다. 무엇을 조정해야 다양한 명령 경계 도착을 커버하는가?

<details>
<summary>정답 / 해설</summary>

**인터럽트 주입 타이밍을 무작위화** 해야 합니다. cross bin 이 한쪽만(load 경계만) 채워진다는 것은 인터럽트 주입 시점이 사실상 고정돼 항상 같은 명령 경계에 도착한다는 신호입니다.
- 인터럽트를 _임의 명령 경계_ 에 도착하도록 주입 타이밍을 랜덤화하고, "interrupt × 명령 타입(load/store/branch/CSR)" cross 와 "interrupt × 파이프라인 상태(stall/flush 중)" cross 를 설계해 도착 시점을 다양화합니다.
- 추가로 중첩(nested) 인터럽트·우선순위·복귀 정확성도 transition 으로 봅니다.
- 인터럽트 버그는 _언제 오느냐_ 가 corner 이므로, "한 번 걸어보면 된다"가 아니라 도착 시점의 다양성이 핵심입니다.

</details>

## Q4. (Apply)

MMU 검증에서 "page fault" bin 이 0 으로 남는다. 자극 생성 측에서 점검·조정할 곳은?

- [ ] A. ISS 를 교체한다
- [ ] B. force-riscv 의 페이지 테이블이 항상 valid/permissive 하게 생성되는지 확인하고, fault 를 유발하는 permission/매핑을 만든다
- [ ] C. step-and-compare 를 끈다
- [ ] D. 명령 분포에서 ALU weight 를 올린다

<details>
<summary>정답 / 해설</summary>

**B**. page fault bin 이 0 이라는 것은 생성된 페이지 테이블이 항상 valid 하고 permission 이 허용적이어서 fault 가 발생할 자극 자체가 없다는 뜻입니다. MMU·페이지 상태 구성에 강한 force-riscv 의 페이지 설정을 조정해, 일부 매핑을 invalid 하게 하거나 permission(R/W/X, U-bit)을 위반하는 접근을 만들어 fault 를 _의도적으로_ 유발해야 합니다. A·C(정답 판정/모델)와 D(명령 분포)는 page fault 발생과 무관합니다.

</details>

## Q5. (Analyze)

어떤 팀이 privilege coverage 로 "M/S/U 모드 각각 한 번 이상 도달"만 측정해 100% 를 보고했다. 이 모델이 놓치는 버그 부류 두 개와, 보강할 coverage 축을 설명하라.

<details>
<summary>정답 / 해설</summary>

단일 도달 coverpoint 는 _전이와 조합_ 을 놓칩니다.
- **놓치는 버그 (1) 전이 정확성**: `mret`/`sret` 가 잘못된 모드로 복귀(MPP 오해석)하거나, U-mode 가 권한 없이 M-mode CSR 를 바꾸는(escalation) 버그. → `cp_trans` transition bins(M=>S, S=>U, U=>(trap)=>M)와 `illegal_bins`(권한 위반 전이)로 보강.
- **놓치는 버그 (2) 원인-전이 조합**: page fault 로 인한 S→M 전이 시 `mcause`/`mepc` 가 틀리는 버그. → `cross cp_cause, cp_trans` 로 "어느 원인이 어느 전이를 유발했나"를 측정.
- 추가로 step-and-compare 가 전이 _순간의 CSR 값_(`mepc`/`mstatus.MPP`)을 ISS 와 대조해야 _값_ 까지 검증됩니다.
- 요지: 모드 _도달_ 은 baseline 일 뿐, privilege 버그는 전이 순간에 살기 때문에 transition + cross + CSR 값 검증이 필요합니다.

</details>

## Q6. (Evaluate)

인터럽트가 임의 명령 경계에 도착하는 시나리오를 검증하는데, 직접 만든 C 모델 reference 가 가끔 DUT 와 어긋난다(어느 쪽이 맞는지 불분명). ImperasDV 같은 상용 reference 로 바꾸는 것이 정당화되는가?

<details>
<summary>정답 / 해설</summary>

**정당화될 가능성이 높습니다 — 단, 먼저 어긋남의 원인을 분류해야 합니다.**
- step-and-compare 의 대전제는 _reference 가 정답_ 이라는 것입니다. 인터럽트는 _비동기·타이밍 민감_ 영역이라, 직접 만든 C 모델이 인터럽트 도착 시점·`mepc` 기록·우선순위 같은 미묘한 spec 을 잘못 해석했을 가능성이 큽니다.
- "어느 쪽이 맞는지 불분명"은 _정답 모델의 신뢰도_ 자체가 흔들린다는 신호이며, 이 상태로는 어떤 mismatch 도 결론 낼 수 없습니다.
- 따라서 상용 검증된 reference(ImperasDV)로 정답의 기준점을 확보하는 것은 합리적입니다 — 비동기 이벤트 모델이 성숙하기 때문입니다.
- 단 맹목적 전환은 금물: 먼저 어긋난 사례 한둘을 RISC-V privileged manual 로 _직접_ 판정해 DUT 버그인지 reference 버그인지 분류하고, reference 버그 비중이 높으면 전환이 정당화됩니다.

</details>
