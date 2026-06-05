---
title: "Quiz — Module 06: 보호·보안"
---

[← Module 06 본문으로 돌아가기](../../06_protection_security/)

---

## Q1. (Remember)

다음 중 "security 가 지키려는 목표"와 "protection 메커니즘"의 관계를 올바르게 짝지은 것은?

- [ ] A. security 는 메커니즘, protection 은 목표
- [ ] B. security 는 목표, protection 은 그 목표를 떠받치는 메커니즘
- [ ] C. 둘은 완전히 같은 말
- [ ] D. protection 은 네트워크 전용, security 는 OS 전용

<details>
<summary>정답 / 해설</summary>

**B**. security 는 *목표*(자원이 의도대로만 쓰이고 접근되는 상태)이고, protection 은 그 목표를 떠받치는 *메커니즘*(ring·domain·access matrix 등)입니다(§16.1). 우리가 검증하는 것은 대개 protection 메커니즘이고, 그것이 막아야 할 security 위반은 spec 이 정의합니다.

</details>
## Q2. (Understand)

least privilege 원칙이 침해 피해를 어떻게 제한하는지, compartmentalization·defense in depth 와 함께 설명하라.

<details>
<summary>정답 / 해설</summary>

(§17.2) **least privilege** 는 프로그램·사용자·시스템에 맡은 일에 *딱 필요한 만큼*의 권한만 줍니다. 그래서 악성 코드가 한 곳을 뚫어도 그 컴포넌트의 권한 범위로만 피해가 제한됩니다. **compartmentalization** 은 각 구성요소를 개별 권한으로 가둬 침해가 옆으로 번지지 못하게 하고, **defense in depth** 는 한 겹이 뚫려도 다음 겹이 막도록 방어를 여러 층으로 둡니다. 세 가지가 함께 "한 곳 침해 = 전체 붕괴"를 막습니다.

</details>
## Q3. (Apply)

access matrix 에서 행은 domain, 열은 object 다. 어느 device 의 domain D2 가 메모리 영역 X 에는 read/write, 프린터에는 접근 불가여야 한다. 이를 행렬 칸으로 표현하라.

<details>
<summary>정답 / 해설</summary>

(§17.5) access matrix 의 `access(i,j)` 는 domain Dᵢ가 object Oⱼ에 할 수 있는 연산 집합입니다.
- `access(D2, MemRegionX)` = `{read, write}`
- `access(D2, Printer)` = `{}` (빈 집합 → 접근 불가)
즉 D2 행에서 MemRegionX 열만 `{read, write}` 로 채우고 나머지 열(Printer 등)은 비워 둡니다. 이것이 "이 device 는 영역 X 만 읽고 쓸 수 있다"는 정책의 표현이며, IOMMU 의 per-device page table 이 이 행을 하드웨어로 인코딩합니다.

</details>
## Q4. (Apply)

ARMv8 의 네 exception level 을 권한 순으로 나열하고, M01 의 dual-mode 가 ring/EL 모델에서 어디에 해당하는지 말하라.

<details>
<summary>정답 / 해설</summary>

(§17.3) ARMv8 의 네 exception level(권한 낮음→높음): **EL0(user) → EL1(kernel) → EL2(hypervisor) → EL3(secure monitor)**. M01 의 dual-mode(user/kernel)는 이 모델에서 가장 단순한 두 단계인 **EL0(user) + EL1(kernel)** 에 해당합니다. Intel 에서는 user=ring 3, kernel=ring 0 이고 가상화용 hypervisor=ring -1 이 EL2 에 대응합니다 — dual-mode 는 ring 의 가장 단순한 두 단계입니다.

</details>
## Q5. (Analyze)

ring 사이를 "정해진 gate(syscall)/trap/interrupt 진입점으로만" 넘게 강제하지 않고 임의 점프를 허용하면 어떤 보안 문제가 생기는지 분석하라.

<details>
<summary>정답 / 해설</summary>

(§17.3) ring 사이를 임의 점프 가능하게 하면, 낮은 ring(user)이 높은 ring(kernel) 코드의 *임의 지점*으로 뛰어들 수 있습니다. 그러면 kernel 진입부의 권한 검사·인자 검증·setup 코드를 *건너뛰고* 위험한 지점에 바로 들어가 높은 ring 의 무결성이 무너집니다 — 이것이 privilege escalation 의 전형입니다. 정해진 gate(예: Intel `syscall`)와 *미리 정해진 진입점*으로만 올라가게 하면, 그 진입점에서 검증을 강제할 수 있어 무결성이 지켜집니다(M01 의 "system call 이 유일한 통로"의 일반화).

</details>
## Q6. (Design)

여러 device 가 한 시스템 메모리를 공유하는 SoC 에서, 각 device 가 자기 버퍼만 접근하도록 IOMMU 격리 정책을 설계하라. least privilege·access matrix·M03 의 보호 비트를 활용하라.

<details>
<summary>정답 / 해설</summary>

설계(§17.4–17.5, §17.2, M03 §9.3.3):
1. **각 device = 하나의 domain.** access matrix 의 한 행 = 그 device 가 접근 가능한 메모리 object 와 권한.
2. **IOMMU per-device page table** 이 그 행을 인코딩 — device 가 낸 주소를 번역하되, 자기 domain 에 매핑된 영역만 valid 로 두고 나머지는 invalid.
3. **least privilege/need-to-know 적용**: 각 device 에 *자기 버퍼만* 매핑하고 나머지는 unmapped → 침해 시 피해가 그 버퍼로 제한.
4. **보호 비트**: 읽기 전용 버퍼는 protection bit 을 read-only 로, 합법 영역 밖 접근은 valid-invalid bit 으로 차단/fault(M03 와 동일 원리).
- **검증 포인트(DV)**: device 가 자기 domain 밖 주소를 내면 IOMMU 가 fault 를 내고 접근을 막는지(privilege escalation 차단)를 직접 테스트 — silent pass 가 보안 구멍.

</details>
