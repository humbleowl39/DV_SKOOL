# Quiz — Module 02: CPU Virtualization

[← Module 02 본문으로 돌아가기](../02_cpu_virtualization.md)

---

## Q1. (Remember)

Trap-and-emulate 메커니즘의 3단계는?

??? answer "정답 / 해설"
    1. **Trap**: Guest의 privileged instruction 실행 → CPU exception
    2. **Emulate**: Hypervisor가 instruction을 안전하게 emulate
    3. **Resume**: Guest로 control return (PC 다음 instruction)

## Q2. (Understand)

VT-x의 root mode와 non-root mode 차이는?

??? answer "정답 / 해설"
    - **Root mode**: Hypervisor 실행 모드. 모든 instruction 정상 실행.
    - **Non-root mode**: Guest 실행 모드. Sensitive instruction은 VMEXIT 발생 → root mode로 전환.
    
    이 분리로 hypervisor가 guest의 행동을 모니터/제어.

## Q3. (Apply)

다음 instruction 중 sensitive (trap 발생)인 것은?

- [ ] A. ADD r1, r2, r3
- [ ] B. MOV CR3, rax (page table base 변경)
- [ ] C. MOV rax, [memory]
- [ ] D. CALL function

??? answer "정답 / 해설"
    **B**. CR3는 page table base register, kernel-only. Guest가 직접 변경하면 host의 page table이 변경될 위험 → trap to hypervisor.

    A/C/D는 일반 instruction → 그대로 실행 (HW가 직접 수행).

## Q4. (Analyze)

Para-virtualization과 HW-assisted의 trade-off는?

??? answer "정답 / 해설"
    - **Para-virt**: guest OS 수정 (xenoLinux). 성능 최적화 가능 + sensitive instruction 회피. 단점: guest source 수정 필요, Linux 외 OS는 어려움.
    - **HW-assisted**: 모든 unmodified guest 지원 (Windows, BSD 등). 성능은 trap overhead로 약간 ↓. **현재 표준**.

## Q5. (Evaluate)

VMCS의 가장 중요한 책임은?

??? answer "정답 / 해설"
    **vCPU state 격리 + VMEXIT cause 기록**. VMEXIT 시 hypervisor가 VMCS의 exit reason field로 어떤 instruction이 trap을 일으켰는지 알 수 있음 → 적절한 emulate 코드 호출. State 격리도 중요 (guest와 host register 자동 swap).
