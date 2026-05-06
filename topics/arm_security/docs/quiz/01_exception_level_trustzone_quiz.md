# Quiz — Module 01: Exception Level & TrustZone

[← Module 01 본문으로 돌아가기](../01_exception_level_trustzone.md)

---

## Q1. (Remember)

ARMv8의 4-level Exception Level과 각 level의 표준 사용처를 답하세요.

??? answer "정답 / 해설"
    - **EL0**: User space (application)
    - **EL1**: Kernel / OS
    - **EL2**: Hypervisor (가상화)
    - **EL3**: Secure Monitor (TrustZone EL3 secure)

## Q2. (Understand)

Exception Level (수직)과 TrustZone (수평)의 차이는?

??? answer "정답 / 해설"
    - **EL**: 권한 계층 — privileged code(EL3)가 less privileged(EL0)를 invoke
    - **TrustZone**: World 분리 — Secure World 자원은 Non-Secure World에서 access 불가
    
    합치면 4 EL × 2 World = 8 mode (실제 의미 있는 조합은 그 중 일부).

## Q3. (Apply)

NS bit가 1인 instruction이 secure 메모리 영역에 access하면?

??? answer "정답 / 해설"
    **TZASC가 차단**. Bus error 발생 (또는 abort exception). 이로 인해 Non-Secure World가 secure 자원을 직접 read/write 불가. World switch 후 Secure World context에서만 access 가능.

## Q4. (Analyze)

EL3가 항상 Secure인 이유는?

??? answer "정답 / 해설"
    EL3는 Secure Monitor 영역. Non-Secure World가 EL3 자원에 access하면 모든 보안 모델 무용. 따라서 spec상 **EL3 = Secure 강제**, NS=1로 EL3 진입 자체 불가.

## Q5. (Evaluate)

다음 중 TrustZone이 보호 못 하는 위협은?

- [ ] A. Non-Secure kernel rootkit이 secure 메모리 read 시도
- [ ] B. Cache side-channel attack via Spectre/Meltdown
- [ ] C. JTAG로 secure register dump 시도
- [ ] D. Non-secure user app이 secure peripheral 접근

??? answer "정답 / 해설"
    **B**. TrustZone은 architectural 격리지만 cache는 공유. Spectre/Meltdown은 speculative execution + cache side-channel로 secure data leak 가능. **방어**: cache flush at world switch, constant-time crypto, 또는 secure enclave (전용 cache).
