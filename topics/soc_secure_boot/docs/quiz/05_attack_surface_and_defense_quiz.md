# Quiz — Module 05: Attack Surface & Defense

[← Module 05 본문으로 돌아가기](../05_attack_surface_and_defense.md)

---

## Q1. (Remember)

Secure Boot의 5가지 주요 공격 카테고리는?

??? answer "정답 / 해설"
    1. **Fault Injection (FI)**: 글리치, 레이저 등 물리 공격
    2. **Side-Channel**: 전력/EM/timing 측정
    3. **Rollback**: 이전 vulnerable version 강제
    4. **TOCTOU (Time-of-Check to Time-of-Use)**: 검증 후 이미지 변조
    5. **JTAG**: debug port 활성화 시도

## Q2. (Understand)

다층 방어가 single layer보다 효과적인 이유는?

??? answer "정답 / 해설"
    Single layer는 한 침해 = 전체 보안 무용. 다층은 각 layer가 독립적 → attacker가 모든 layer를 우회해야 침투. 다층 방어:
    - **HW layer**: glitch detector, anti-tamper mesh
    - **SW layer**: 이중 검증, anti-rollback
    - **설계 layer**: key hierarchy, crypto agility

    Cost of attack ↑↑ → 합리적 attacker 차단.

## Q3. (Apply)

Glitchy Descriptor (iPhone bootloader bypass) 공격을 차단하려면?

??? answer "정답 / 해설"
    원리: clock/voltage 글리치로 verification instruction 한 cycle 건너뛰게 함 → 검증 우회.

    **방어**:
    1. **Glitch detector**: 클럭/전압 anomaly HW로 monitor → 감지 시 reset/halt
    2. **Double verification**: 같은 검증을 두 번 (서로 다른 시점) — 둘 다 우회 어려움
    3. **Random delays**: glitch 시점 예측 어렵게
    4. **Constant-time crypto**: timing-based glitch 효과 ↓

## Q4. (Analyze)

Side-channel attack 방어의 핵심 원칙은?

??? answer "정답 / 해설"
    - **Constant-time**: 모든 input에 동일 시간 (data-dependent branch 금지)
    - **Constant-power**: 모든 input에 동일 power consumption (Differential Power Analysis 방지)
    - **Masking**: 중간 결과를 random mask와 XOR → 측정값에서 실제 값 추출 어려움
    - **Blinding**: input에 random factor 추가 후 결과에서 제거

    하드웨어 + 소프트웨어 모두 적용 필요.

## Q5. (Evaluate)

다음 공격 중 Production 환경에서 가장 위협적인 것은?

- [ ] A. Lab 기반 fault injection (전압 글리치)
- [ ] B. 원격 rollback 공격 (서버에 old firmware 설치)
- [ ] C. 레이저 fault injection
- [ ] D. Side-channel via 전력 측정

??? answer "정답 / 해설"
    **B**. 원격 + 비물리적 = scalable. 수백만 device 동시 공격 가능. 이미 Mirai botnet 등 실제 사례. 

    A/C/D는 물리 access 필요 → high-value target에만 가치. B는 commodity device에도 위협.

    방어: anti-rollback OTP counter는 거의 모든 보안 chip이 구현하는 이유.
