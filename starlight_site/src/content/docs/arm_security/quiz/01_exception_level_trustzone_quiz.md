---
title: "Quiz — Module 01: Exception Level & TrustZone"
---

[← Module 01 본문으로 돌아가기](../../01_exception_level_trustzone/)

---

## Q1. (Remember)

ARMv8의 4-level Exception Level과 각 level의 표준 사용처를 답하세요.

<details>
<summary>정답 / 해설</summary>

- **EL0**: User space (application)
- **EL1**: Kernel / OS
- **EL2**: Hypervisor (가상화)
- **EL3**: Secure Monitor (TrustZone EL3 secure)

ARMv8는 권한(privilege)을 4단계 수직 계층으로 정의하며, 번호가 올라갈수록 더 높은 특권을 가진다. EL0는 일반 앱이 실행되는 최소 권한 영역이고, EL1은 OS 커널처럼 메모리·인터럽트를 직접 관리할 수 있다. EL2는 여러 게스트 OS를 동시에 격리하는 하이퍼바이저가, EL3는 Secure World 전체를 중재하는 Secure Monitor가 위치한다. 이 4단계를 외울 때는 "앱→커널→하이퍼바이저→보안감시자" 순서로 기억하면 된다.

</details>
## Q2. (Understand)

Exception Level (수직)과 TrustZone (수평)의 차이는?

<details>
<summary>정답 / 해설</summary>

- **EL**: 권한 계층 — privileged code(EL3)가 less privileged(EL0)를 invoke
- **TrustZone**: World 분리 — Secure World 자원은 Non-Secure World에서 access 불가

합치면 4 EL × 2 World = 8 mode (실제 의미 있는 조합은 그 중 일부).

EL은 "위아래(수직)" 개념으로, 낮은 EL이 높은 EL에게 서비스를 요청하는 호출 구조다. TrustZone은 "좌우(수평)" 개념으로, 같은 EL1이라도 Secure 쪽과 Non-Secure 쪽은 서로의 메모리와 자원에 접근할 수 없다. 두 축이 독립적이기 때문에 EL1 Non-Secure 커널이 루트킷에 장악되더라도 EL1 Secure 영역은 NS bit 차단으로 보호된다. 즉 EL은 "누가 더 강한 권한인가", TrustZone은 "어느 World에 속하는가"를 각각 별도로 통제한다.

</details>
## Q3. (Apply)

NS bit가 1인 instruction이 secure 메모리 영역에 access하면?

<details>
<summary>정답 / 해설</summary>

**TZASC가 차단**. Bus error 발생 (또는 abort exception). 이로 인해 Non-Secure World가 secure 자원을 직접 read/write 불가. World switch 후 Secure World context에서만 access 가능.

NS=1인 요청이 버스에 실리는 순간, 버스 경로 중간에 위치한 TZASC(TrustZone Address Space Controller)가 목적 주소가 Secure 영역인지 확인한다. Secure 영역으로 설정된 주소라면 TZASC는 해당 트랜잭션을 즉시 거절하고 bus error(abort)를 발생시켜 요청자에게 exception으로 되돌린다. 이 하드웨어 차단이 없다면 SW 버그 하나로 Non-Secure 커널이 Secure World의 키나 비밀 데이터를 직접 읽어낼 수 있기 때문에, TZASC는 TrustZone의 소프트웨어 격리를 하드웨어 수준에서 강제하는 필수 장치다.

</details>
## Q4. (Analyze)

EL3가 항상 Secure인 이유는?

<details>
<summary>정답 / 해설</summary>

EL3는 Secure Monitor 영역. Non-Secure World가 EL3 자원에 access하면 모든 보안 모델 무용. 따라서 spec상 **EL3 = Secure 강제**, NS=1로 EL3 진입 자체 불가.

EL3는 World switch를 담당하는 Secure Monitor가 상주하는 유일한 영역이다. 만약 EL3가 Non-Secure로도 동작할 수 있다면, NS World의 코드가 EL3 권한을 획득해 TZASC·TZPC 등 보안 경계 설정을 마음대로 바꿀 수 있어 TrustZone 전체가 무력화된다. ARMv8 spec은 이를 막기 위해 EL3 진입 시 항상 Secure 상태(NS=0)를 강제하도록 아키텍처 수준에서 정의하고 있다. 즉 "EL3 = Secure"는 설정이 아닌 하드웨어 불변 규칙이다.

</details>
## Q5. (Evaluate)

다음 중 TrustZone이 보호 못 하는 위협은?

- [ ] A. Non-Secure kernel rootkit이 secure 메모리 read 시도
- [ ] B. Cache side-channel attack via Spectre/Meltdown
- [ ] C. JTAG로 secure register dump 시도
- [ ] D. Non-secure user app이 secure peripheral 접근

<details>
<summary>정답 / 해설</summary>

**B**. TrustZone은 architectural 격리지만 cache는 공유. Spectre/Meltdown은 speculative execution + cache side-channel로 secure data leak 가능. **방어**: cache flush at world switch, constant-time crypto, 또는 secure enclave (전용 cache).

TrustZone의 NS bit 격리는 메모리 주소 접근 경로를 차단하지만, CPU 캐시는 Secure World와 Non-Secure World가 물리적으로 공유하는 자원이다. Spectre/Meltdown 류의 공격은 투기적 실행(speculative execution) 중 비밀 데이터를 캐시에 로드한 뒤, 캐시 타이밍 차이를 관찰해 그 값을 추론하므로 NS bit 검사를 우회한다. A(NS rootkit의 secure 메모리 직접 접근)는 TZASC가 차단하고, C(JTAG dump)는 JTAG 비활성화 또는 Debug Authentication으로 막을 수 있으며, D(NS app의 secure peripheral 접근)는 TZPC가 차단한다. B만이 아키텍처 경계 밖의 물리 자원인 캐시를 악용하는 공격이기 때문에 TrustZone 단독으로는 방어할 수 없다.

</details>
