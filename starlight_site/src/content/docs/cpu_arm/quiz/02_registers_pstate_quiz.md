---
title: "Quiz — Module 02: 레지스터 & PSTATE"
---

[← Module 02 본문으로 돌아가기](../../02_registers_pstate/)

---

## Q1. (Remember)

AArch64 에서 `XZR`/`WZR`(zero register)의 동작으로 옳은 것은?

- [ ] A. 읽으면 마지막 연산 결과, 쓰면 저장
- [ ] B. 읽으면 항상 0, 쓰면 버려짐(discard)
- [ ] C. 읽으면 0, 쓰면 1 로 고정
- [ ] D. 스택 포인터와 동일

<details>
<summary>정답 / 해설</summary>

**B**. `XZR`/`WZR` 은 읽으면 항상 0 이고 쓰면 버려집니다. 그래서 `cmp x0, xzr`(0 과 비교)나 `str xzr, [x1]`(메모리 0 클리어)을 별도의 "0 적재" 명령 없이 할 수 있고, `mov x2,x3` 가 실제로는 `orr x2, xzr, x3` 로 인코딩되기도 합니다. A/C 는 동작을 잘못 설명했고, D 는 인코딩 번호(31)를 공유할 뿐 명령 문맥에 따라 SP 와 ZR 이 갈리는 것을 혼동한 오답입니다.

</details>
## Q2. (Understand)

PSTATE 의 NZCV 와 DAIF 가 각각 담는 것을 옳게 짝지은 것은?

- [ ] A. NZCV=인터럽트 마스크, DAIF=조건 플래그
- [ ] B. NZCV=조건 플래그, DAIF=인터럽트(Debug/SError/IRQ/FIQ) 마스크
- [ ] C. 둘 다 조건 플래그
- [ ] D. NZCV=현재 EL, DAIF=스택 선택

<details>
<summary>정답 / 해설</summary>

**B**. NZCV 는 Negative/Zero/Carry/oVerflow 조건 플래그로 비교·연산 결과에 따라 갱신되고 조건 분기(`b.eq`, `b.lt`)가 이를 읽습니다. DAIF 는 Debug·SError·IRQ·FIQ 의 인터럽트 마스크로, 비트가 1 이면 해당 인터럽트를 막으며 예외 진입 시 HW 가 자동으로 전부 1 로 세팅합니다. A 는 둘을 뒤집었고, C/D 는 다른 PSTATE 필드(CurrentEL/SPSel)와 혼동한 오답입니다.

</details>
## Q3. (Apply)

함수 프롤로그 `stp x29, x30, [sp, #-16]!` 에서 X30(LR)을 함께 저장하는 이유는?

- [ ] A. X30 은 항상 0 이라 초기화 필요
- [ ] B. 본문에서 다른 함수를 `BL` 로 부르면 X30 이 새 복귀 주소로 덮어써져 원래 복귀 주소를 잃기 때문
- [ ] C. X30 은 스택 포인터라서
- [ ] D. 컴파일러가 항상 모든 레지스터를 저장하라고 요구해서

<details>
<summary>정답 / 해설</summary>

**B**. `X30` 은 LR(Link Register)로 `BL` 이 복귀 주소를 여기 저장합니다. 함수 본문에서 또 다른 함수를 `BL` 로 부르면 X30 이 새 복귀 주소로 덮어써지므로, 프롤로그가 먼저 LR 을 스택에 옮겨 두어야 자신의 복귀 주소를 보존할 수 있습니다. A/C 는 X30 의 역할을 잘못 설명했고, D 는 callee-saved 만 저장하는 실제 규약과 다릅니다.

</details>
## Q4. (Apply)

`MSR sctlr_el1, x0` 로 MMU 활성화 비트를 바꾼 직후 동작이 적용되지 않았다. 무엇을 빠뜨렸나?

- [ ] A. `DMB` — 메모리 순서
- [ ] B. `ISB` — 파이프라인 flush 후 새 컨텍스트로 재-fetch
- [ ] C. `ERET` — EL 복귀
- [ ] D. `SVC` — 시스템 콜

<details>
<summary>정답 / 해설</summary>

**B**. `MSR` 이 SCTLR 을 바꾸는 시점에 **이미 파이프라인에 prefetch 된 다음 명령** 은 옛 SCTLR 상태로 디코드됩니다. `ISB` 가 파이프라인을 비우고 새 컨텍스트(MMU on)로 재-fetch 해야 변경이 적용됩니다. A(DMB)는 메모리 관측 순서용, C(ERET)는 자체 context sync 를 포함하지만 여기선 EL 복귀가 아니고, D(SVC)는 무관합니다. (M04 에서 상세.)

</details>
## Q5. (Analyze)

`X0 = 0xFFFF_0000_DEAD_BEEF`(64-bit 포인터)인 상태에서 누군가 `mov w0, #1` 을 실행했다. 이후 X0 값과 그 원인을 분석하라.

<details>
<summary>정답 / 해설</summary>

이후 `X0 = 0x0000_0000_0000_0001` 이 됩니다. AArch64 의 핵심 규칙은 **W 레지스터(32-bit 뷰)에 쓰면 대응 X 레지스터의 상위 32-bit 가 자동으로 zero-extend(0으로)** 된다는 것입니다. `mov w0, #1` 은 W0 에 1 을 쓰면서 X0 의 상위 `0xFFFF_0000` 을 통째로 0 으로 날립니다. 그래서 64-bit 포인터를 들고 있던 X 에 실수로 W 연산이 끼면 상위 주소가 사라져 잘못된 주소를 참조하는 버그가 됩니다. 검증 단서: 포인터의 상위가 0 이 되는 mismatch 를 보면 해당 레지스터에 `mov w`/`add w` 같은 W 연산이 끼었는지 의심합니다.

</details>
## Q6. (Evaluate)

ELR/SPSR 같은 예외 처리 레지스터가 EL 별로 banked 되지 않고 전 EL 이 하나를 공유한다면 어떤 위험이 생기는지, 그리고 HW banking 이 SW 저장 방식보다 나은 이유를 평가하라.

<details>
<summary>정답 / 해설</summary>

공유 시 **nested 예외에서 복귀 정보가 파괴** 됩니다. 예를 들어 EL1 핸들러 실행 중 EL2 로 trap(hypervisor)이 나면, 공유 ELR 이라면 EL2 진입이 EL1 의 복귀 PC 를 덮어써, EL2 에서 돌아올 때 EL1 이 자기 복귀 주소를 잃습니다. banking 덕분에 `ELR_EL1` 과 `ELR_EL2` 가 별개라 각 EL 이 자기 복귀 정보를 독립 보존합니다. 대안인 "공유 + SW 가 매 진입마다 저장/복원" 도 이론상 가능하지만, 진입마다 SW 코드가 필요해 비용과 버그 위험이 커집니다. HW banking 은 이 정확성을 자동화하므로, nested trap 의 안전성을 SW 가 아닌 HW 가 보장하는 더 견고한 설계입니다.

</details>
