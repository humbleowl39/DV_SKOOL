# Quiz — Module 07: Secure Boot Quick Reference

[← Module 07 본문으로 돌아가기](../06_quick_reference_card.md)

---

## Q1. (Recall)

Secure Boot flow의 단계 5개와 각 단계의 1-line 책임?

??? answer "정답 / 해설"
    1. **BootROM**: HW RoT, BL1 load + 검증
    2. **BL1**: trusted boot init, BL2 load + 검증
    3. **BL2**: DRAM init, BL31/BL33 load + 검증
    4. **BL31**: EL3 secure monitor, secure/non-secure world 전환
    5. **BL33**: U-Boot/non-secure bootloader, kernel load

## Q2. (Recall)

Secure Boot에 사용되는 핵심 암호 알고리즘 3가지는?

??? answer "정답 / 해설"
    - **SHA-256/384**: hash (image 무결성)
    - **RSA-2048/4096 또는 ECDSA P-256/384**: 비대칭 서명 (인증성)
    - **AES-256**: 대칭 암호 (image 암호화 시)

## Q3. (Apply)

새 SoC에 Secure Boot 도입 시 가장 먼저 결정할 3가지는?

??? answer "정답 / 해설"
    1. **Threat model**: production attacker만 vs nation-state까지? — 방어 수준 결정
    2. **암호 알고리즘**: RSA vs ECDSA, key size — long-term migration 고려
    3. **Boot device priority**: QSPI primary, eMMC secondary 등 fail-over 설계

## Q4. (Apply)

OTP fuse를 production 직전 program할 때 체크리스트는?

??? answer "정답 / 해설"
    1. ROTPK hash 정확성 (HSM에서 추출, double-check)
    2. Lifecycle state: development → production transition
    3. Anti-rollback counter 초기화
    4. Debug port (JTAG) disable
    5. Secure 설정 enabled (TrustZone, sysMMU)

    이 단계에서 실수 = silicon 폐기 또는 보안 취약.

## Q5. (Evaluate)

다음 중 silicon mass production에 가장 위험한 결함은?

- [ ] A. BootROM의 buffer overflow vulnerability
- [ ] B. OTP의 ECC 미적용
- [ ] C. JTAG가 debug에서 production으로 전환 안 됨
- [ ] D. 위 3가지 모두

??? answer "정답 / 해설"
    **D**. 모두 silicon revision 또는 field recall 사유.
    - A: BootROM은 immutable → revision 외 fix 불가
    - B: OTP bit flip → key 변조 silent
    - C: production silicon이 debug mode → JTAG attack 가능

    Sign-off 직전 모든 항목 verification 절대 필수.
