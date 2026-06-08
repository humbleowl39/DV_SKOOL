---
title: "Quiz — Module 01: 개요 & ISA"
---

[← Module 01 본문으로 돌아가기](../../01_overview_isa/)

---

## Q1. (Remember)

AArch64(A64) 명령 인코딩의 길이로 옳은 것은?

- [ ] A. 1 ~ 15 byte 가변 길이
- [ ] B. 32-bit 고정 길이
- [ ] C. 16-bit 고정 길이
- [ ] D. 64-bit 고정 길이

<details>
<summary>정답 / 해설</summary>

**B**. A64 명령은 모두 32-bit 고정 길이라 다음 명령 시작 위치를 항상 PC+4 로 알 수 있어 frontend 디코드가 단순합니다. A 는 x86-64 의 가변 길이, C 는 AArch32 의 Thumb-2(16/32 혼합) 또는 RISC-V `C` 확장의 16-bit 와 혼동, D 는 레지스터 폭(64-bit)을 명령 길이로 착각한 오답입니다.

</details>
## Q2. (Understand)

ARM 프로파일 중 "MMU 가 없고 Thumb-2 전용이라 64-bit AArch64 바이너리를 실행할 수 없는" 것은?

- [ ] A. Cortex-A (Application)
- [ ] B. Neoverse (Infrastructure)
- [ ] C. Cortex-M (Microcontroller)
- [ ] D. Cortex-R (Real-time)

<details>
<summary>정답 / 해설</summary>

**C**. Cortex-M 은 초저전력 MCU 프로파일로 Thumb-2 전용에 MMU 가 없어 AArch64 ELF 를 아예 실행하지 못합니다. A(Cortex-A)와 B(Neoverse)는 MMU 를 갖춘 AArch64 application/infrastructure 프로파일이고, D(Cortex-R)는 결정론적 실시간용으로 보통 MPU 기반입니다. "같은 ARM 인데 펌웨어가 부팅조차 안 된다" 의 단골 원인이 이 프로파일 불일치입니다.

</details>
## Q3. (Apply)

C 의 `c = a + b` 를 AArch64 로 구현할 때, x86 의 `add eax, [b]` 같은 "메모리 피연산자 직접 연산" 이 불가능한 이유와 ARM 의 처리 방식은?

- [ ] A. ARM 은 덧셈 명령이 없다
- [ ] B. load-store 아키텍처라 메모리는 LDR/STR 로만 접근하고 연산은 register↔register — load 후 add 로 분리
- [ ] C. ARM 은 메모리 연산을 두 배 빠르게 한다
- [ ] D. ARM 은 a, b 를 항상 스택에서 더한다

<details>
<summary>정답 / 해설</summary>

**B**. ARM 은 load-store RISC 라 ALU 연산의 피연산자는 반드시 레지스터여야 합니다. 따라서 `ldr w0,[x_a]` / `ldr w1,[x_b]` 로 적재한 뒤 `add w2,w0,w1`, `str w2,[x_c]` 로 분리됩니다. 이 분리가 디코더를 단순화하고 파이프라인의 MEM/EX 단계를 깔끔히 나눕니다. A/C/D 는 ISA 원칙과 무관한 오답입니다.

</details>
## Q4. (Apply)

검증 중 어떤 LSE atomic 명령(`LDADD` 등)이 illegal instruction 으로 트랩했다. 가장 먼저 확인할 것은?

- [ ] A. 스택 정렬
- [ ] B. 코어의 ISA 버전이 ARMv8.1+ 인지 (LSE 요구 버전)
- [ ] C. 인터럽트 마스크
- [ ] D. 캐시 활성화 여부

<details>
<summary>정답 / 해설</summary>

**B**. LSE(Large System Extensions)는 ARMv8.1 부터 추가된 확장이라, ARMv8.0 코어에서 `LDADD`/`CAS` 같은 LSE 명령을 쓰면 illegal instruction 으로 트랩합니다. 명령이 illegal 로 트랩하면 코어의 ISA 버전과 명령이 요구하는 버전을 대조하는 것이 첫 단계입니다(SVE/SVE2 는 ARMv9). A/C/D 는 illegal instruction 의 원인과 무관합니다.

</details>
## Q5. (Analyze)

"in-order Cortex-A53 과 wide OoO Neoverse V2 는 같은 AArch64 라서 검증을 한 번만 하면 된다" 는 주장의 문제를 분석하라.

<details>
<summary>정답 / 해설</summary>

ISA **계약** 은 같지만 **마이크로아키텍처** 가 전혀 다릅니다. 명령 의미·레지스터·메모리 모델의 *아키텍처적 보장* 은 동일해 기능 정확성 테스트는 상당 부분 공유할 수 있습니다. 그러나 A53 은 in-order, V2 는 wide OoO 라 타이밍, 명령 재정렬의 *가시성*, 캐시 동작, 분기 예측이 달라 *성능* 과 *코너 케이스* — 특히 weak memory 의 관측 순서 — 가 다르게 나타납니다. 따라서 기능 검증은 공유하되, 타이밍/ordering/마이크로아키텍처 의존 시나리오는 코어별로 재검증해야 합니다. "한 번만" 은 위험한 단순화입니다.

</details>
## Q6. (Evaluate)

세 ISA 비교 표에서 "메모리 모델" 행을 보면 ARM/RISC-V 는 weakly-ordered, x86-64 는 TSO 다. 검증 환경 설계 시 ARM 의 weak memory 가 x86 대비 어떤 추가 부담을 주는지 평가하라.

<details>
<summary>정답 / 해설</summary>

ARM 의 weak memory 는 검증에서 **재정렬 가능 공간이 훨씬 넓다** 는 부담을 줍니다. x86 TSO 는 store→load 재정렬만 허용하므로 lock-free 코드가 대체로 "그냥 동작" 하지만, ARM 은 load→load, load→store, store→store 까지 재정렬·병합·추측 실행이 가능합니다. 따라서 (1) 공유 변수 핸드오프마다 배리어(DMB/LDAR/STLR) 누락을 검출하는 시나리오가 필요하고, (2) "대부분 통과, 드물게 실패" 하는 비결정적 ordering 버그를 재현할 stress/interleaving 테스트가 필요하며, (3) monitor/scoreboard 가 program order 가 아닌 *관측 가능한 순서 집합* 을 기준으로 판정해야 합니다. 즉 x86 에서 통과하던 코드가 ARM 에서 깨지는 케이스를 의도적으로 만들어야 하므로 검증 공간과 체크 정밀도가 모두 커집니다. (배리어 세부는 M04 에서 다룹니다.)

</details>
