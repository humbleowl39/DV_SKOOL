# Quiz — Module 03: Secure Boot Connection

[← Module 03 본문으로 돌아가기](../03_secure_boot_connection.md)

---

## Q1. (Remember)

ARM Trusted Firmware의 BL31이 거주하는 EL과 책임은?

??? answer "정답 / 해설"
    **EL3 (Secure Monitor)** 영구 거주. 책임:
    1. World switch 시 register save/restore
    2. SMC handler routing
    3. PSCI (Power State Coordination Interface) 처리
    4. SoC-level security policy enforcement

## Q2. (Understand)

Verified Boot와 Architecture Enforcement (EL/TrustZone)가 보완 관계인 이유는?

??? answer "정답 / 해설"
    - **Verified Boot 단독**: 정상 image지만 EL/TrustZone 무용 → 일단 부팅 후 NS context가 secure 자원 access 가능
    - **Architecture 단독**: 권한 정확하지만 image 위변조 → 공격자가 EL3에 자기 코드 실행
    - **둘 다 필요**: image 검증 (verified) + 실행 환경 격리 (architecture). 어느 하나만 있으면 우회 가능.

## Q3. (Apply)

Boot 단계와 EL을 매핑하세요.

| 단계 | EL | World |
|------|----|----|
| BootROM | ? | ? |
| BL2 | ? | ? |
| BL31 | ? | ? |
| BL33 (U-Boot) | ? | ? |
| Linux kernel | ? | ? |

??? answer "정답 / 해설"
    | 단계 | EL | World |
    |------|----|----|
    | BootROM | EL3 | Secure |
    | BL2 | EL3 | Secure |
    | BL31 | EL3 | Secure (영구 거주) |
    | BL33 (U-Boot) | EL2 또는 EL1 | Non-Secure |
    | Linux kernel | EL1 | Non-Secure |

## Q4. (Analyze)

BL2가 BL31과 BL33을 모두 검증한 후 jump하는 이유는?

??? answer "정답 / 해설"
    BL31 (EL3 secure) → BL33 (EL1 non-secure). BL2는 둘 다 BL2의 원본 trust로부터 검증. 만약 BL2가 BL31만 검증하고 BL33은 BL31이 검증하게 하면:
    - BL31의 검증 로직 자체가 vulnerable이면 BL33 침해 가능
    - 검증 로직이 두 곳에 분산 (consistency 위험)
    
    BL2가 한꺼번에 검증 → trust source 단일화 + BL31의 조작 영역 축소.

## Q5. (Evaluate)

Production silicon에서 Verified Boot 누락 + Architecture만 있으면 어떤 공격이 가능한가?

??? answer "정답 / 해설"
    **공격자 image로 BootROM 후 단계 교체**. Image 검증 없이 실행되므로:
    1. 공격자가 BL2에 자기 코드 삽입 → BL2가 EL3에서 실행
    2. EL3 권한으로 모든 secure 자원 access 가능
    3. Architecture (EL/TrustZone)는 그대로지만 EL3 자체가 공격자 손에
    
    결과: 모든 보안 무용. Verified Boot가 chain의 출발점인 이유.
