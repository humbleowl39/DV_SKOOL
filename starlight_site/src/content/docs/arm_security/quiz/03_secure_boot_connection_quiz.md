---
title: "Quiz — Module 03: Secure Boot Connection"
---

[← Module 03 본문으로 돌아가기](../../03_secure_boot_connection/)

---

## Q1. (Remember)

ARM Trusted Firmware의 BL31이 거주하는 EL과 책임은?

<details>
<summary>정답 / 해설</summary>

**EL3 (Secure Monitor)** 영구 거주. 책임:
1. World switch 시 register save/restore
2. SMC handler routing
3. PSCI (Power State Coordination Interface) 처리
4. SoC-level security policy enforcement

BL31이 EL3에 영구 거주하는 이유는 World switch가 런타임 중 반복적으로 발생하기 때문이다. 매번 BL31을 메모리에 다시 로드한다면 World switch마다 큰 지연이 생긴다. BL31은 EL3 Secure 메모리에 상주하면서 SMC 호출이 들어올 때마다 즉시 레지스터 context를 교체하고 PSCI를 통해 CPU 전원 상태(온/오프, 핫플러그)를 조율한다. Non-Secure World는 BL31이 거주하는 EL3 메모리에 직접 쓰기 접근이 불가능하므로, BL31 코드 자체가 런타임 변조로부터 보호된다.

</details>
## Q2. (Understand)

Verified Boot와 Architecture Enforcement (EL/TrustZone)가 보완 관계인 이유는?

<details>
<summary>정답 / 해설</summary>

- **Verified Boot 단독**: 정상 image지만 EL/TrustZone 무용 → 일단 부팅 후 NS context가 secure 자원 access 가능
- **Architecture 단독**: 권한 정확하지만 image 위변조 → 공격자가 EL3에 자기 코드 실행
- **둘 다 필요**: image 검증 (verified) + 실행 환경 격리 (architecture). 어느 하나만 있으면 우회 가능.

Verified Boot는 "올바른 코드가 실행되고 있는가"를 보장하고, EL/TrustZone 아키텍처는 "실행 중 코드가 정해진 권한 경계 안에서만 동작하는가"를 보장한다. 둘은 서로 다른 위협을 막는 상호 보완 관계다. Verified Boot 없이 아키텍처만 있으면 공격자가 EL3용 Secure Monitor 이미지를 악성 코드로 교체해 부팅시킬 수 있고, 일단 EL3에서 자신의 코드가 실행되면 TZASC·TZPC 설정을 모두 재작성할 수 있다. 반대로 아키텍처 없이 Verified Boot만 있으면 이미지는 진본이지만 런타임에 권한 경계가 없어 NS 코드가 Secure 자원에 자유롭게 접근할 수 있다.

</details>
## Q3. (Apply)

Boot 단계와 EL을 매핑하세요.

| 단계 | EL | World |
|------|----|----|
| BootROM | ? | ? |
| BL2 | ? | ? |
| BL31 | ? | ? |
| BL33 (U-Boot) | ? | ? |
| Linux kernel | ? | ? |

<details>
<summary>정답 / 해설</summary>

| 단계 | EL | World |
|------|----|----|
| BootROM | EL3 | Secure |
| BL2 | EL3 | Secure |
| BL31 | EL3 | Secure (영구 거주) |
| BL33 (U-Boot) | EL2 또는 EL1 | Non-Secure |
| Linux kernel | EL1 | Non-Secure |

부팅 초기는 전적으로 EL3 Secure에서 시작된다. BootROM은 칩 내부에 구워진 최초의 신뢰 앵커(Root of Trust)로, 그 누구도 수정할 수 없어야 한다. BL2도 EL3 Secure에서 실행되면서 이후 단계를 검증하고, BL31이 Secure Monitor로 영구 정착한다. BL33(U-Boot)부터는 Non-Secure 세계로 전환되어 일반 부트로더와 OS 초기화가 이루어진다. Linux 커널은 EL1에서 동작하며, 이 시점부터는 EL3의 BL31이 SMC를 통해 World switch 요청만 중재하는 체계가 확립된다. 각 단계가 다음 단계를 검증하는 연쇄(chain of trust) 구조이기 때문에, EL이 높을수록 부팅 초기에 배치된다.

</details>
## Q4. (Analyze)

BL2가 BL31과 BL33을 모두 검증한 후 jump하는 이유는?

<details>
<summary>정답 / 해설</summary>

BL31 (EL3 secure) → BL33 (EL1 non-secure). BL2는 둘 다 BL2의 원본 trust로부터 검증. 만약 BL2가 BL31만 검증하고 BL33은 BL31이 검증하게 하면:
- BL31의 검증 로직 자체가 vulnerable이면 BL33 침해 가능
- 검증 로직이 두 곳에 분산 (consistency 위험)

BL2가 한꺼번에 검증 → trust source 단일화 + BL31의 조작 영역 축소.

Chain of Trust의 핵심 원칙은 "신뢰는 위임되지 않는다"는 것이다. BL2가 BL31에게 BL33 검증을 위임하면, BL31의 코드 크기와 복잡도가 커지고 그만큼 취약점 노출 면적(attack surface)이 증가한다. BL31은 World switch와 SMC routing 같은 최소한의 역할만 담당하는 것이 보안상 유리하다. BL2가 BL31과 BL33을 모두 같은 시점·같은 신뢰 체계 아래에서 검증함으로써 검증 로직이 단일 장소에 집중되어 감사(audit)가 용이하고 BL31의 역할 범위도 최소화된다.

</details>
## Q5. (Evaluate)

Production silicon에서 Verified Boot 누락 + Architecture만 있으면 어떤 공격이 가능한가?

<details>
<summary>정답 / 해설</summary>

**공격자 image로 BootROM 후 단계 교체**. Image 검증 없이 실행되므로:
1. 공격자가 BL2에 자기 코드 삽입 → BL2가 EL3에서 실행
2. EL3 권한으로 모든 secure 자원 access 가능
3. Architecture (EL/TrustZone)는 그대로지만 EL3 자체가 공격자 손에

결과: 모든 보안 무용. Verified Boot가 chain의 출발점인 이유.

Verified Boot가 없다면 플래시 메모리에 저장된 BL2 이미지를 공격자가 물리적 접근 또는 펌웨어 취약점을 이용해 교체할 수 있다. 교체된 BL2는 EL3 Secure 환경에서 실행되므로, TZASC를 재설정해 Secure 영역을 Non-Secure로 바꾸거나 Secure Monitor 자체를 악성 코드로 교체하는 모든 행위가 가능해진다. EL/TrustZone 아키텍처는 코드가 무엇인지 검증하지 않고 "지금 실행 중인 코드가 어떤 EL·World에 있는가"만 관리하므로, 공격자 코드도 EL3에서 실행되는 순간 합법적 Secure Monitor와 동일한 권한을 갖는다. Verified Boot는 이 공격의 진입점 자체를 차단하는 선제적 방어막이다.

</details>
