---
title: "Quiz — Module 02: World Switch & SoC Security Infra"
---

[← Module 02 본문으로 돌아가기](../../02_world_switch_soc_infra/)

---

## Q1. (Remember)

World switch에 사용되는 instruction과 진입 EL은?

<details>
<summary>정답 / 해설</summary>

**SMC (Secure Monitor Call)** instruction → trap to **EL3** → Secure Monitor가 처리.

World switch는 반드시 가장 높은 특권 레벨인 EL3를 경유해야 한다. 만약 EL1이나 EL2에서 직접 World를 바꿀 수 있다면, 침해된 커널(EL1)이 임의로 Secure World로 진입해 비밀 자산에 접근할 수 있게 된다. SMC는 이 진입점을 EL3 하나로 고정하는 아키텍처 수준의 게이트이며, EL3에 상주하는 Secure Monitor(BL31)가 SMC handler를 통해 요청을 검증하고 context를 교체한다. SVC(EL1), HVC(EL2)는 각각 시스템 콜과 하이퍼바이저 호출을 위한 별도 instruction으로, World 전환 권한이 없다.

</details>
## Q2. (Understand)

World switch 시 register isolation이 왜 중요한가?

<details>
<summary>정답 / 해설</summary>

Secure World register에 비밀 (key, sensitive data)가 있을 수 있음. World switch 시 secure register 값을 그대로 두고 Non-Secure로 전환하면 NS context에서 register read 가능 → leak. 

Secure Monitor가 모든 register를 secure 메모리에 save → 새 world context restore. 이 격리가 깨지면 모든 TrustZone 보안 무용.

CPU 레지스터(범용 레지스터, 시스템 레지스터 포함)는 두 World가 물리적으로 공유하는 자원이다. World switch 직전까지 Secure World의 암호 연산이 x0~x30에 중간값을 보관하고 있었다면, 저장 없이 Non-Secure로 전환하는 순간 그 값이 NS 코드에 그대로 노출된다. Secure Monitor는 ERET 전에 현재 World의 모든 레지스터를 Secure 메모리에 저장하고, 반대 World의 저장된 context를 복원함으로써 레지스터 격리를 유지한다. 이 save/restore 절차가 올바르게 구현되지 않으면 레지스터 누출만으로 암호 키가 NS World에 노출될 수 있다.

</details>
## Q3. (Apply)

SoC의 DRAM 32GB 중 1GB를 secure 영역으로 만들려면?

<details>
<summary>정답 / 해설</summary>

**TZASC region 설정**: TZASC register에 secure region 시작 주소 + 크기 설정. Region permission을 secure-only로. 모든 DRAM access는 TZASC 통과 → NS=1 access면 차단. 보통 firmware boot 시 설정.

TZASC는 DRAM 컨트롤러 앞단(또는 버스 패브릭 내)에 위치해 모든 메모리 트랜잭션을 감시한다. 부팅 시 firmware(보통 BL2)가 TZASC 레지스터에 보안 영역의 시작 주소와 크기, 접근 권한(Secure-only)을 기록하면, 이후 해당 영역에 NS=1 트랜잭션이 도착할 때마다 TZASC가 자동으로 거절한다. 설정을 부팅 이후 NS 코드가 변경하지 못하도록 레지스터를 잠그는 것(lock bit)도 필수이며, 그렇지 않으면 NS 커널이 TZASC를 재설정해 보안 영역을 확장·축소할 수 있다.

</details>
## Q4. (Analyze)

Peripheral A (UART)와 Peripheral B (Crypto engine)을 각각 NS와 Secure로 만들려면?

<details>
<summary>정답 / 해설</summary>

**TZPC 설정**:
- UART → NS=1 허용 (둘 다 access 가능)
- Crypto engine → Secure=1만 (NS access 차단)

Crypto는 secure key 처리하므로 NS context에서 직접 access 금지. Crypto 사용은 SMC를 통해 Secure World에 위임.

TZPC는 DRAM이 아닌 SoC의 peripheral(AHB/APB 연결 IP)별로 Secure/Non-Secure 접근 권한을 설정하는 컨트롤러다. UART는 디버그 출력 등 NS 코드도 사용해야 하므로 NS 접근을 허용하지만, Crypto engine은 Secure World의 키를 직접 다루기 때문에 NS 주소 공간에서 접근 자체를 차단한다. NS 앱이 암호화 서비스가 필요한 경우에는 SMC를 통해 Secure World TEE에 요청하고, TEE가 Crypto engine을 대신 사용해 결과만 돌려주는 위임 구조를 취한다.

</details>
## Q5. (Evaluate)

다음 중 TZASC bypass 공격에 가장 효과적인 방어는?

- [ ] A. NS bit 검증 강화
- [ ] B. ECC 적용
- [ ] C. DMA 마스터에 sysMMU StreamID 적용
- [ ] D. JTAG 비활성화

<details>
<summary>정답 / 해설</summary>

**C**. CPU는 NS bit으로 보호되지만 DMA 마스터 (GPU/NIC)는 sysMMU 우회 시 secure 메모리 직접 access 가능. **sysMMU StreamID + Stage 2** 적용으로 모든 device의 메모리 access를 가상 주소 기반 격리. ARM SMMU의 핵심 가치.

TZASC는 CPU가 발생시키는 트랜잭션의 NS bit을 기반으로 동작하지만, GPU·NIC·USB 같은 DMA 마스터는 CPU를 통하지 않고 버스에 직접 물리 주소를 실어 DRAM에 접근한다. 따라서 TZASC만으로는 이들이 secure 영역을 직접 읽는 시나리오를 막을 수 없다. A(NS bit 검증 강화)는 CPU 경로에만 효과적이고, B(ECC)는 데이터 무결성 기술로 접근 제어와 무관하며, D(JTAG 비활성화)는 디버그 포트 공격 방어로 DMA 경로를 막지 못한다. ARM SMMU의 StreamID 기반 Stage 2 매핑이 각 DMA 마스터를 식별해 접근 가능한 물리 주소 범위를 제한하는 유일한 방어 수단이다.

</details>
