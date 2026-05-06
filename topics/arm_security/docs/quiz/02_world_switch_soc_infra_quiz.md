# Quiz — Module 02: World Switch & SoC Security Infra

[← Module 02 본문으로 돌아가기](../02_world_switch_soc_infra.md)

---

## Q1. (Remember)

World switch에 사용되는 instruction과 진입 EL은?

??? answer "정답 / 해설"
    **SMC (Secure Monitor Call)** instruction → trap to **EL3** → Secure Monitor가 처리.

## Q2. (Understand)

World switch 시 register isolation이 왜 중요한가?

??? answer "정답 / 해설"
    Secure World register에 비밀 (key, sensitive data)가 있을 수 있음. World switch 시 secure register 값을 그대로 두고 Non-Secure로 전환하면 NS context에서 register read 가능 → leak. 

    Secure Monitor가 모든 register를 secure 메모리에 save → 새 world context restore. 이 격리가 깨지면 모든 TrustZone 보안 무용.

## Q3. (Apply)

SoC의 DRAM 32GB 중 1GB를 secure 영역으로 만들려면?

??? answer "정답 / 해설"
    **TZASC region 설정**: TZASC register에 secure region 시작 주소 + 크기 설정. Region permission을 secure-only로. 모든 DRAM access는 TZASC 통과 → NS=1 access면 차단. 보통 firmware boot 시 설정.

## Q4. (Analyze)

Peripheral A (UART)와 Peripheral B (Crypto engine)을 각각 NS와 Secure로 만들려면?

??? answer "정답 / 해설"
    **TZPC 설정**:
    - UART → NS=1 허용 (둘 다 access 가능)
    - Crypto engine → Secure=1만 (NS access 차단)
    
    Crypto는 secure key 처리하므로 NS context에서 직접 access 금지. Crypto 사용은 SMC를 통해 Secure World에 위임.

## Q5. (Evaluate)

다음 중 TZASC bypass 공격에 가장 효과적인 방어는?

- [ ] A. NS bit 검증 강화
- [ ] B. ECC 적용
- [ ] C. DMA 마스터에 sysMMU StreamID 적용
- [ ] D. JTAG 비활성화

??? answer "정답 / 해설"
    **C**. CPU는 NS bit으로 보호되지만 DMA 마스터 (GPU/NIC)는 sysMMU 우회 시 secure 메모리 직접 access 가능. **sysMMU StreamID + Stage 2** 적용으로 모든 device의 메모리 access를 가상 주소 기반 격리. ARM SMMU의 핵심 가치.
