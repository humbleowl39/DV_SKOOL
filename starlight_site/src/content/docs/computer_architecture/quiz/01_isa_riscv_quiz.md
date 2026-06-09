---
title: "Quiz — Module 01: ISA & RISC-V"
---

[← Module 01 본문으로 돌아가기](../../01_isa_riscv/)

---

## Q1. (Remember)

RISC-V 의 `x0` 레지스터의 특성은?

- [ ] A. 스택 포인터로 예약됨
- [ ] B. hardwired zero — 쓰기는 무시되고 읽으면 항상 0
- [ ] C. 프로그램 카운터(PC)
- [ ] D. 인터럽트 마스크 레지스터

<details>
<summary>정답 / 해설</summary>

**B**. RISC-V 의 `x0` 은 hardwired zero 로, 쓰기를 시도해도 무시되고 읽으면 항상 0 입니다. 이 덕분에 `ADD x5,x6,x0`(=MOV), `BEQ x0,x0,L`(무조건 분기), `ADDI x0,x0,0`(NOP) 같은 관용구가 별도 명령 없이 생깁니다. reference model 이 이 규칙(`rd != 0` 가드)을 빠뜨리면 정상 DUT 를 mismatch 로 신고합니다. A/C/D 는 `x0` 의 역할이 아닙니다.

</details>
## Q2. (Understand)

ISA 가 "하드웨어와 소프트웨어 사이의 계약"이라는 말의 의미는?

<details>
<summary>정답 / 해설</summary>

ISA 는 programmer-visible 상태(레지스터·메모리 모델·특권 레벨), 명령 인코딩, 각 명령의 의미를 _규정_ 하되, 그것을 _어떻게 구현하는지_(파이프라인 깊이·OoO 여부·캐시 구성)는 마이크로아키텍처의 자유로 남깁니다. 소프트웨어(컴파일러)는 계약에 적힌 명령만 사용하고, 하드웨어는 계약에 적힌 의미대로 architectural state 를 보존하기만 하면 됩니다. 그래서 같은 RISC-V 바이너리가 작은 in-order 코어와 거대한 OoO 코어에서 동일한 결과를 냅니다 — 이 추상화가 검증의 골든 레퍼런스(reference model)의 근거가 됩니다.

</details>
## Q3. (Apply)

`ADD x3, x1, x2` 를 reference model 로 구현할 때 반드시 반영해야 할 ISA 규칙은? (load/store 아키텍처 관점)

<details>
<summary>정답 / 해설</summary>

(1) 산술은 _레지스터에서만_ 일어납니다 — `x1`, `x2` 는 레지스터 파일에서 읽고 결과를 레지스터 `x3` 에 씁니다. 메모리 값을 더하려면 먼저 `LOAD` 로 레지스터에 올려야 합니다(load/store 아키텍처). (2) `x3` 이 `x0` 이면 결과를 폐기해야 합니다(`if (rd != 0)`). pseudo code로는 `result = rf[rs1] + rf[rs2]; if (rd != 0) rf[rd] = result;` 입니다. 이 두 규칙을 빠뜨리면 가장 흔한 false mismatch 가 발생합니다.

</details>
## Q4. (Analyze)

"RISC 는 명령 수(IC)가 CISC 보다 많을 수 있는데도 더 빠르다"를 Iron Law 로 분석하면?

- [ ] A. RISC 가 IC 를 줄여서 빠르다
- [ ] B. RISC 가 CPI 와 클럭 주파수에서 얻는 이득이 IC 증가를 상쇄한다
- [ ] C. RISC 는 항상 코드 크기가 작다
- [ ] D. CISC 가 항상 더 느린 클럭을 가진다

<details>
<summary>정답 / 해설</summary>

**B**. CPU Time = IC × CPI × Cycle Time. RISC 는 메모리 연산을 LOAD+OP+STORE 로 분해해 IC 가 오히려 늘 수 있습니다(A·C 오답 — "Reduced"는 코드 길이가 아니라 명령 _복잡도_ 감소). 그러나 고정 길이·단순 형식으로 파이프라인 효율이 높아 CPI 가 1 에 근접하고, hardwired control 로 임계 경로가 짧아 클럭 주파수가 높습니다. 이 두 축의 이득이 IC 증가를 압도해 전체 CPU Time 이 줄어듭니다. D 는 일반화 오류 — x86 도 내부 RISC-like micro-op 으로 높은 주파수를 냅니다.

</details>
## Q5. (Evaluate)

현대 x86 프로세서가 외부적으로는 CISC 명령을 받으면서 내부적으로 RISC-like micro-op 으로 변환하는 설계를 평가하라.

<details>
<summary>정답 / 해설</summary>

이는 두 상충하는 요구의 절충입니다. _외부 계약(ISA)_ 은 수십 년 누적된 x86 바이너리와의 호환성을 위해 CISC 를 유지해야 합니다 — 계약을 바꾸면 기존 소프트웨어가 깨집니다. 반면 _내부 구현_ 은 성능을 위해 파이프라이닝과 OoO 스케줄링이 쉬운 형태여야 하는데, 가변 길이의 복잡한 CISC 명령은 그대로는 파이프라이닝이 어렵습니다. 따라서 프런트엔드에서 CISC 를 고정 형식에 가까운 micro-op 으로 분해해 OoO 백엔드에 넣습니다. 이는 ISA 추상화의 핵심 가치를 보여줍니다 — 계약(무엇)과 구현(어떻게)이 분리되어 있어, 외부 호환성을 깨지 않고 내부를 RISC 화해 성능을 얻을 수 있습니다. trade-off 는 디코드/변환 단계의 복잡도와 전력 증가이지만, 호환성의 경제적 가치가 이를 정당화합니다.

</details>
