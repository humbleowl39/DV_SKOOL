# Quiz — Module 04: ARM Security Quick Reference

[← Module 04 본문으로 돌아가기](../04_quick_reference_card.md)

---

## Q1. (Recall)

EL0-EL3 표준 사용처를 한 줄씩.

??? answer "정답 / 해설"
    - **EL0**: User application
    - **EL1**: Kernel / OS
    - **EL2**: Hypervisor (KVM, Xen)
    - **EL3**: Secure Monitor (ARM Trusted Firmware BL31)

    ARMv8의 4단계 Exception Level은 번호가 높을수록 더 많은 시스템 자원에 접근할 수 있는 권한을 부여한다. EL0는 일반 사용자 프로그램이, EL1은 OS 커널이, EL2는 가상화 하이퍼바이저(KVM, Xen 등)가, EL3는 TrustZone의 Security Monitor인 BL31이 위치한다. 이 계층 구조는 각 소프트웨어 계층이 자신보다 높은 EL의 자원에 임의로 접근하지 못하도록 하드웨어가 강제한다.

## Q2. (Recall)

SVC / HVC / SMC instruction의 진입 EL?

??? answer "정답 / 해설"
    - **SVC (Supervisor Call)**: EL0 → EL1 (syscall)
    - **HVC (Hypervisor Call)**: EL1 → EL2 (hypervisor service)
    - **SMC (Secure Monitor Call)**: any → EL3 (world switch)

    세 instruction은 각각 서로 다른 "상위 권한으로 올라가는 게이트"다. SVC는 앱이 OS 커널 서비스를 요청할 때 사용하는 시스템 콜 메커니즘이고, HVC는 게스트 OS가 하이퍼바이저에 자원을 요청할 때 쓴다. SMC는 EL0~EL2 어느 레벨에서도 발행할 수 있으며, 항상 EL3의 Secure Monitor로 trap되어 World switch를 비롯한 가장 높은 권한의 작업을 처리한다. 이 세 instruction을 구분하는 핵심 기준은 "어느 EL로 진입하는가"이며, 진입 EL이 높을수록 더 강력한 시스템 제어권을 가진다.

## Q3. (Apply)

다음 자원을 secure로 만드는 SoC peripheral은?

| 자원 | 사용할 peripheral |
|------|-------------------|
| DRAM 영역 | ? |
| UART/Crypto 같은 IP | ? |
| 인터럽트 | ? |

??? answer "정답 / 해설"
    - DRAM → **TZASC**
    - Peripheral → **TZPC**
    - 인터럽트 → **GIC v3 (Group 0/1 분리)**

    TrustZone 보안 모델은 메모리·peripheral·인터럽트 세 자원 각각에 전용 컨트롤러를 배치한다. TZASC(TrustZone Address Space Controller)는 DRAM 주소 범위를 Secure/Non-Secure로 나누어 트랜잭션을 검사하고, TZPC(TrustZone Protection Controller)는 AHB/APB에 연결된 IP 블록마다 접근 권한을 설정한다. GIC v3는 인터럽트를 Group 0(Secure FIQ)와 Group 1(Non-Secure IRQ)으로 분리해 Secure World로 전달되어야 할 인터럽트가 Non-Secure 컨텍스트에서 처리되지 않도록 보장한다. 이 세 컨트롤러가 협력하여 TrustZone의 하드웨어 격리를 완성한다.

## Q4. (Apply)

EL3 secure monitor (BL31)이 영구 거주하는 이유는?

??? answer "정답 / 해설"
    World switch가 빈번 (예: SMC call). 매번 BL31 load하면 overhead 큼. 영구 거주로:
    1. Register save/restore 즉시 실행
    2. SMC handler routing 빠름
    3. PSCI (CPU power on/off) 처리 가능
    
    BL31은 EL3 secure 메모리에 거주 → NS World가 직접 modify 불가.

    SMC 호출은 TrustZone 기반 시스템에서 DRM 재생·생체인증·암호화 등 다양한 서비스 요청마다 발생하는 빈번한 이벤트다. BL31이 매번 플래시에서 로드되어야 한다면 World switch 지연이 수 밀리초 단위로 쌓여 실시간 응답이 불가능해진다. EL3 Secure 메모리에 영구 거주함으로써 SMC trap 즉시 handler로 진입할 수 있고, 이 메모리 영역은 NS World에서 쓰기 접근이 불가능하므로 런타임 변조도 방지된다. PSCI(전원 관리)와 같이 CPU 온/오프 시점에도 즉시 처리해야 하는 기능도 같은 이유로 BL31이 상시 대기해야 한다.

## Q5. (Evaluate)

다음 중 ARM 기반 SoC의 가장 critical한 보안 결함은?

- [ ] A. EL3 영구 거주 BL31에 buffer overflow
- [ ] B. TZASC 설정 leak (boot 후 NS가 secure region 추가 가능)
- [ ] C. GIC group routing 오류
- [ ] D. SMC handler에서 input validation 부족

??? answer "정답 / 해설"
    **A**. BL31은 EL3 영구 거주 + 가장 privileged. Compromise 시 모든 보안 무용. SoC silicon revision 또는 firmware update만 fix 가능. B는 boot 단계 issue로 mitigation 가능, C는 인터럽트 routing fix, D는 BL31 자체에 문제는 아님. BL31 코드 자체의 결함이 가장 광범위한 영향.

    EL3는 ARMv8에서 가장 높은 특권 레벨이며 BL31은 여기에 영구 거주하므로, BL31에 buffer overflow가 발생하면 공격자는 EL3 코드 실행 권한을 획득한다. 이 순간 TZASC·TZPC 재설정, Secure Monitor 교체, 모든 보안 정책 무력화가 가능해진다. B(TZASC 설정 leak)는 심각하지만 boot 시 lock bit를 적용하거나 ATF 패치로 완화할 수 있고, C(GIC routing 오류)는 인터럽트 전달 경로 문제로 재설정이 가능하며, D(SMC input validation 부족)는 BL31 코드 내 한 함수의 취약점이지 코드 실행 자체를 허용하는 결함은 아니다. BL31 코드 실행 흐름 자체가 탈취되는 A가 영향 범위와 복구 난이도 모두에서 가장 치명적이다.
