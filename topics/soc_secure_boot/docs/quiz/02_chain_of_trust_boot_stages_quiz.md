# Quiz — Module 02: Chain of Trust & Boot Stages

[← Module 02 본문으로 돌아가기](../02_chain_of_trust_boot_stages.md)

---

## Q1. (Remember)

ARM Trusted Firmware의 표준 boot 단계 5개를 답하세요.

??? answer "정답 / 해설"
    BootROM → **BL1** (trusted boot init) → **BL2** (DRAM init + BL31/BL33 load) → **BL31** (EL3 secure monitor) → **BL33** (U-Boot/non-secure) → kernel.

## Q2. (Understand)

"Verify-then-execute" 패턴이 왜 중요한가?

??? answer "정답 / 해설"
    Verification 후에야 jump → 미인증 image가 한 instruction이라도 실행되지 않음. Verification 중 fail이면 즉시 halt 또는 fail-safe boot. Execute-then-verify면 이미 공격 코드가 실행 후 검증 → meaningless.

## Q3. (Apply)

Verified Boot vs Measured Boot의 enforcement 차이는?

??? answer "정답 / 해설"
    - **Verified Boot**: 검증 실패 시 boot 차단. 정책이 boot loader에 있음.
    - **Measured Boot**: hash를 TPM PCR에 누적. Boot은 진행, 정책 결정은 OS/사용자가 attestation으로.

    실제 시스템은 둘 다 사용 (Verified로 기본 차단 + Measured로 attestation).

## Q4. (Analyze)

BL2가 침해되면 BL31과 BL33은 어떻게 영향받는가?

??? answer "정답 / 해설"
    BL2가 BL31/BL33을 load + 검증함. BL2 침해 시:
    - BL2의 검증 로직 우회 가능 → 공격자 BL31/BL33 load 가능
    - 따라서 BL31 (EL3 secure monitor) compromise → secure world 전체 침해
    - BL33 compromise → user space 직접 침해

    **Trust 전파의 양면성**: 신뢰가 전파되는 만큼 침해도 전파.

## Q5. (Evaluate)

다음 중 secure boot에서 가장 큰 위험은?

- [ ] A. 첫 단계 (BootROM) 침해
- [ ] B. 중간 단계 (BL2) 침해
- [ ] C. 마지막 단계 (kernel) 침해
- [ ] D. 모든 단계 동등

??? answer "정답 / 해설"
    **A**. BootROM은 trust anchor — 침해되면 그 이후 모든 chain 무용. 다행히 BootROM은 mask ROM이라 fault injection 같은 물리 공격으로만 우회 가능 (변경 불가). B는 그 시점부터의 trust 침해, C는 kernel 자체 침해 (이미 OS context). 첫 단계가 가장 critical.
