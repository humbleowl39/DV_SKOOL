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

## Q2. (Recall)

SVC / HVC / SMC instruction의 진입 EL?

??? answer "정답 / 해설"
    - **SVC (Supervisor Call)**: EL0 → EL1 (syscall)
    - **HVC (Hypervisor Call)**: EL1 → EL2 (hypervisor service)
    - **SMC (Secure Monitor Call)**: any → EL3 (world switch)

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

## Q4. (Apply)

EL3 secure monitor (BL31)이 영구 거주하는 이유는?

??? answer "정답 / 해설"
    World switch가 빈번 (예: SMC call). 매번 BL31 load하면 overhead 큼. 영구 거주로:
    1. Register save/restore 즉시 실행
    2. SMC handler routing 빠름
    3. PSCI (CPU power on/off) 처리 가능
    
    BL31은 EL3 secure 메모리에 거주 → NS World가 직접 modify 불가.

## Q5. (Evaluate)

다음 중 ARM 기반 SoC의 가장 critical한 보안 결함은?

- [ ] A. EL3 영구 거주 BL31에 buffer overflow
- [ ] B. TZASC 설정 leak (boot 후 NS가 secure region 추가 가능)
- [ ] C. GIC group routing 오류
- [ ] D. SMC handler에서 input validation 부족

??? answer "정답 / 해설"
    **A**. BL31은 EL3 영구 거주 + 가장 privileged. Compromise 시 모든 보안 무용. SoC silicon revision 또는 firmware update만 fix 가능. B는 boot 단계 issue로 mitigation 가능, C는 인터럽트 routing fix, D는 BL31 자체에 문제는 아님. BL31 코드 자체의 결함이 가장 광범위한 영향.
