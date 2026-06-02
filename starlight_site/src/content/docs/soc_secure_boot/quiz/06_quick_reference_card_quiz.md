---
title: "Quiz — Module 07: Secure Boot Quick Reference"
---

[← Module 07 본문으로 돌아가기](../../06_quick_reference_card/)

---

## Q1. (Recall)

Secure Boot flow의 단계 5개와 각 단계의 1-line 책임?

<details>
<summary>정답 / 해설</summary>

1. **BootROM**: HW RoT, BL1 load + 검증
2. **BL1**: trusted boot init, BL2 load + 검증
3. **BL2**: DRAM init, BL31/BL33 load + 검증
4. **BL31**: EL3 secure monitor, secure/non-secure world 전환
5. **BL33**: U-Boot/non-secure bootloader, kernel load

각 단계를 단순 암기가 아닌 "왜 이 순서인가"로 이해하면 쉽습니다. DRAM이 없는 상태에서 실행할 수 있는 것은 BootROM(on-chip mask ROM)뿐이므로 가장 먼저 실행됩니다. BL2는 DRAM 초기화 책임을 맡아 이후 단계가 DRAM을 쓸 수 있게 준비합니다. BL31이 BL33보다 먼저 설치되는 이유는 EL3 Secure Monitor가 먼저 메모리에 상주해야, 이후 BL33(Non-secure 세계)이 동작할 때 SMC 핸들러가 준비되어 있기 때문입니다.

</details>
## Q2. (Recall)

Secure Boot에 사용되는 핵심 암호 알고리즘 3가지는?

<details>
<summary>정답 / 해설</summary>

- **SHA-256/384**: hash (image 무결성)
- **RSA-2048/4096 또는 ECDSA P-256/384**: 비대칭 서명 (인증성)
- **AES-256**: 대칭 암호 (image 암호화 시)

세 알고리즘이 함께 쓰이는 이유는 각각 다른 보안 속성을 담당하기 때문입니다. SHA-256은 이미지가 변조되지 않았음을 확인(무결성)하지만, 서명 없이는 "누가 만들었는지"를 보장하지 않습니다. RSA 또는 ECDSA 서명은 "이 키를 가진 제조사가 승인한 이미지"임을 보장(인증성)합니다. AES-256은 이미지 내용 자체를 암호화해 스토리지에서 노출되지 않게 하는 기밀성을 담당하며, 모든 Secure Boot 구현이 반드시 image 암호화를 하는 것은 아니지만 IP 보호가 필요한 경우 추가됩니다.

</details>
## Q3. (Apply)

새 SoC에 Secure Boot 도입 시 가장 먼저 결정할 3가지는?

<details>
<summary>정답 / 해설</summary>

1. **Threat model**: production attacker만 vs nation-state까지? — 방어 수준 결정
2. **암호 알고리즘**: RSA vs ECDSA, key size — long-term migration 고려
3. **Boot device priority**: QSPI primary, eMMC secondary 등 fail-over 설계

이 세 가지가 가장 먼저 와야 하는 이유는 모든 후속 결계가 여기에 종속되기 때문입니다. Threat model이 없으면 "어느 정도의 방어가 충분한가"를 판단할 기준이 없고, 결국 과도하게 복잡하거나 반대로 취약한 설계가 됩니다. 알고리즘 선택은 OTP에 저장되는 key hash와 직결되므로 설계 초기에 고정해야 하며, 나중에 바꾸려면 silicon revision이 필요합니다. Boot device priority는 BootROM 코드에 하드코딩되거나 OTP로 고정되므로, 역시 초기 결정이 후속 모든 검증 계획을 결정합니다.

</details>
## Q4. (Apply)

OTP fuse를 production 직전 program할 때 체크리스트는?

<details>
<summary>정답 / 해설</summary>

1. ROTPK hash 정확성 (HSM에서 추출, double-check)
2. Lifecycle state: development → production transition
3. Anti-rollback counter 초기화
4. Debug port (JTAG) disable
5. Secure 설정 enabled (TrustZone, sysMMU)

이 단계에서 실수 = silicon 폐기 또는 보안 취약.

이 체크리스트의 각 항목이 독립적으로 치명적인 이유를 이해해야 합니다. 1번(ROTPK hash 오기입)은 모든 서명 검증을 무력화합니다. 2번(lifecycle 전환 누락)은 기기가 개발 모드로 출하되어 debug 기능이 열린 채로 유통됩니다. 3번(counter 초기화 누락)은 anti-rollback이 동작하지 않아 구버전 이미지 다운그레이드 공격에 노출됩니다. 4번(JTAG 미비활성화)은 누구나 debug 포트로 메모리를 읽고 쓸 수 있게 됩니다. 5번(TrustZone 설정 누락)은 Secure World 격리가 동작하지 않습니다. 모두 OTP로 영구 고정되는 설정이므로, program 전 automated verification이 필수입니다.

</details>
## Q5. (Evaluate)

다음 중 silicon mass production에 가장 위험한 결함은?

- [ ] A. BootROM의 buffer overflow vulnerability
- [ ] B. OTP의 ECC 미적용
- [ ] C. JTAG가 debug에서 production으로 전환 안 됨
- [ ] D. 위 3가지 모두

<details>
<summary>정답 / 해설</summary>

**D**. 모두 silicon revision 또는 field recall 사유.
- A: BootROM은 immutable → revision 외 fix 불가
- B: OTP bit flip → key 변조 silent
- C: production silicon이 debug mode → JTAG attack 가능

Sign-off 직전 모든 항목 verification 절대 필수.

A, B, C 중 하나만 고른 답이 틀린 이유는 각각의 결함이 서로 다른 방식으로 치명적이기 때문입니다. A(BootROM buffer overflow)는 소프트웨어 패치로 수정할 수 없어 silicon을 다시 만들어야 합니다. B(OTP ECC 미적용)는 단일 bit flip이 발생해도 이를 탐지하거나 정정할 수 없어, ROTPK hash가 조용히 손상될 수 있습니다. C(JTAG 미비활성화)는 양산 기기가 개발자 모드로 동작해 물리적 접근만 있으면 누구나 메모리를 조작할 수 있습니다. 세 결함이 모두 field recall 또는 전수 OTP 재program 사유라는 점에서 동등하게 심각합니다.

</details>
