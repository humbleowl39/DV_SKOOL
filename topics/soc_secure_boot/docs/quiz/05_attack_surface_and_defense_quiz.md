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

    이 5가지가 서로 다른 공격 레이어를 커버한다는 점을 이해하는 것이 중요합니다. FI와 Side-Channel은 물리적 접근이 필요한 하드웨어 공격입니다. Rollback은 소프트웨어/펌웨어 수준의 프로토콜 공격으로 원격으로도 가능합니다. TOCTOU는 검증과 실행 사이의 타이밍 레이스를 노리는 구현 취약점입니다. JTAG는 디버그 인터페이스를 통한 직접 메모리 접근 공격입니다. 각 공격이 다른 레이어를 노리므로, 어느 한 방어 기법만으로는 전체를 막을 수 없고 다층 방어가 필수적입니다.

## Q2. (Understand)

다층 방어가 single layer보다 효과적인 이유는?

??? answer "정답 / 해설"
    Single layer는 한 침해 = 전체 보안 무용. 다층은 각 layer가 독립적 → attacker가 모든 layer를 우회해야 침투. 다층 방어:
    - **HW layer**: glitch detector, anti-tamper mesh
    - **SW layer**: 이중 검증, anti-rollback
    - **설계 layer**: key hierarchy, crypto agility

    Cost of attack ↑↑ → 합리적 attacker 차단.

    다층 방어의 효과가 단순 덧셈이 아닌 이유를 생각해 봅시다. 각 레이어를 우회할 확률이 P₁, P₂, P₃라면, 공격 성공 확률은 P₁ × P₂ × P₃로 곱셈적으로 감소합니다. 또한 각 레이어는 서로 다른 종류의 공격을 막으므로, HW glitch detector를 우회했다고 해도 SW 이중 검증이라는 별도의 장벽을 다시 넘어야 합니다. 보안의 목표는 공격을 완전히 불가능하게 만드는 것이 아니라, 공격 비용이 얻을 수 있는 이익보다 크게 만드는 것입니다.

## Q3. (Apply)

Glitchy Descriptor (iPhone bootloader bypass) 공격을 차단하려면?

??? answer "정답 / 해설"
    원리: clock/voltage 글리치로 verification instruction 한 cycle 건너뛰게 함 → 검증 우회.

    **방어**:
    1. **Glitch detector**: 클럭/전압 anomaly HW로 monitor → 감지 시 reset/halt
    2. **Double verification**: 같은 검증을 두 번 (서로 다른 시점) — 둘 다 우회 어려움
    3. **Random delays**: glitch 시점 예측 어렵게
    4. **Constant-time crypto**: timing-based glitch 효과 ↓

    Glitch 공격의 핵심 원리는 "검증 결과를 저장하는 레지스터 또는 분기 명령어 한 사이클만 틀어도 전체 검증을 우회할 수 있다"는 것입니다. 이를 막기 위한 Double verification의 논리는 단순합니다. 두 번의 검증이 서로 다른 시점에 수행되면, 공격자는 두 번 모두 정확한 타이밍에 글리치를 넣어야 하며 그 두 타이밍을 예측하기 어렵게 만들면 공격 성공 확률이 급격히 낮아집니다. Random delay는 그 예측 자체를 방해하는 역할입니다.

## Q4. (Analyze)

Side-channel attack 방어의 핵심 원칙은?

??? answer "정답 / 해설"
    - **Constant-time**: 모든 input에 동일 시간 (data-dependent branch 금지)
    - **Constant-power**: 모든 input에 동일 power consumption (Differential Power Analysis 방지)
    - **Masking**: 중간 결과를 random mask와 XOR → 측정값에서 실제 값 추출 어려움
    - **Blinding**: input에 random factor 추가 후 결과에서 제거

    하드웨어 + 소프트웨어 모두 적용 필요.

    Side-channel 방어의 근본 원칙은 "외부 관찰자가 측정하는 물리량(시간, 전력, EM)이 비밀 데이터와 통계적 상관관계를 가지지 않아야 한다"는 것입니다. 예를 들어 RSA 연산에서 지수 비트가 1이냐 0이냐에 따라 분기가 달라지면, 그 분기가 소비하는 전력 패턴으로 키를 역산할 수 있습니다(Simple/Differential Power Analysis). Constant-time/power는 그 상관관계 자체를 없애고, Masking과 Blinding은 측정값에 random noise를 더해 통계적 추출을 어렵게 만드는 보완적 기법입니다.

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

    A(Lab 기반 fault injection)와 C(레이저 FI)가 기술적으로 강력하지만 production 환경에서 덜 위협적인 이유는 공격 비용과 확장성 때문입니다. 물리적 공격은 기기 한 대에 수백만 원에서 수억 원의 장비와 고도의 기술이 필요하므로, 국가 기관이나 고가 target에만 경제적으로 타당합니다. 반면 B(원격 rollback)는 스크립트 하나로 취약한 firmware를 가진 수백만 대의 기기를 동시에 공격할 수 있어, commodity IoT 기기나 소비자 전자제품에 현실적인 위협입니다. D(Side-channel)도 물리 접근이 필요하므로 B보다 확장성이 낮습니다.
