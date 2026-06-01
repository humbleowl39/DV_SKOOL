# Quiz — Module 02: CPU Virtualization

[← Module 02 본문으로 돌아가기](../02_cpu_virtualization.md)

---

## Q1. (Remember)

Trap-and-emulate 메커니즘의 3단계는?

??? answer "정답 / 해설"
    1. **Trap**: Guest의 privileged instruction 실행 → CPU exception
    2. **Emulate**: Hypervisor가 instruction을 안전하게 emulate
    3. **Resume**: Guest로 control return (PC 다음 instruction)

    이 세 단계의 핵심은 guest가 "자신이 직접 실행했다"고 착각하도록 만드는 투명성입니다. Trap 단계에서 CPU는 제어권을 hypervisor로 넘기고, hypervisor는 해당 instruction이 실제로 실행된 것과 동일한 부작용을 소프트웨어로 재현(emulate)합니다. Resume 단계에서 guest의 PC는 해당 instruction 바로 다음을 가리키므로, guest 입장에서는 그냥 instruction 하나가 실행된 것처럼 보입니다. 이 투명성이 깨지면 guest OS가 비정상 동작하거나 보안 경계가 무너집니다.

## Q2. (Understand)

VT-x의 root mode와 non-root mode 차이는?

??? answer "정답 / 해설"
    - **Root mode**: Hypervisor 실행 모드. 모든 instruction 정상 실행.
    - **Non-root mode**: Guest 실행 모드. Sensitive instruction은 VMEXIT 발생 → root mode로 전환.
    
    이 분리로 hypervisor가 guest의 행동을 모니터/제어.

    VT-x 이전에는 ring 0~3 privilege level만 있어서 hypervisor와 guest OS가 같은 ring을 경쟁해야 했고, 이것이 "ring deprivileging" 문제를 만들었습니다. VT-x는 여기에 root/non-root라는 직교 차원을 추가해 hypervisor는 항상 root mode에, guest는 항상 non-root mode에 위치하도록 명확히 분리했습니다. Non-root mode에서 sensitive instruction이 실행되면 VMEXIT가 자동으로 root mode로 전환하므로, hypervisor 코드 없이도 CPU 하드웨어 자체가 제어권 이전을 보장합니다.

## Q3. (Apply)

다음 instruction 중 sensitive (trap 발생)인 것은?

- [ ] A. ADD r1, r2, r3
- [ ] B. MOV CR3, rax (page table base 변경)
- [ ] C. MOV rax, [memory]
- [ ] D. CALL function

??? answer "정답 / 해설"
    **B**. CR3는 page table base register, kernel-only. Guest가 직접 변경하면 host의 page table이 변경될 위험 → trap to hypervisor.

    A/C/D는 일반 instruction → 그대로 실행 (HW가 직접 수행).

    정답이 B인 이유는 CR3이 현재 실행 중인 address space 전체를 결정하는 레지스터이기 때문입니다. Guest가 CR3를 자유롭게 변경할 수 있다면 hypervisor나 다른 VM의 page table을 가리키도록 바꿔 메모리 격리 전체를 무력화할 수 있습니다. A(ADD), C(메모리 읽기), D(CALL)는 user/kernel 권한 구분 없이 누구나 실행할 수 있는 unprivileged instruction이므로 trap이 발생하지 않습니다. Sensitive instruction의 기준은 "실행하면 시스템 전체 상태를 바꿀 수 있는가"입니다.

## Q4. (Analyze)

Para-virtualization과 HW-assisted의 trade-off는?

??? answer "정답 / 해설"
    - **Para-virt**: guest OS 수정 (xenoLinux). 성능 최적화 가능 + sensitive instruction 회피. 단점: guest source 수정 필요, Linux 외 OS는 어려움.
    - **HW-assisted**: 모든 unmodified guest 지원 (Windows, BSD 등). 성능은 trap overhead로 약간 ↓. **현재 표준**.

    Para-virtualization의 핵심 아이디어는 guest OS가 "나는 가상 환경에서 실행된다"는 사실을 알고 hypercall로 hypervisor에 직접 협력 요청하는 것입니다. 이렇게 하면 trap-and-emulate 비용을 줄일 수 있지만, OS 소스 수정이 필수이므로 Windows처럼 소스를 공개하지 않는 OS에는 적용이 불가능합니다. HW-assisted는 OS 수정 없이 모든 기존 OS를 그대로 실행할 수 있다는 결정적 이점이 있어, 현재는 HW-assisted가 표준이고 para-virt는 성능이 극히 민감한 일부 IO 경로에서만 보조적으로 사용됩니다.

## Q5. (Evaluate)

VMCS의 가장 중요한 책임은?

??? answer "정답 / 해설"
    **vCPU state 격리 + VMEXIT cause 기록**. VMEXIT 시 hypervisor가 VMCS의 exit reason field로 어떤 instruction이 trap을 일으켰는지 알 수 있음 → 적절한 emulate 코드 호출. State 격리도 중요 (guest와 host register 자동 swap).

    VMCS가 없다면 VMEXIT가 발생할 때마다 hypervisor는 "어떤 이유로 trap이 왔는가"를 소프트웨어로 직접 추론해야 하고, guest의 모든 레지스터 상태도 수동으로 저장·복원해야 합니다. VMCS는 이 두 작업을 하드웨어가 자동으로 처리하도록 지원하는 자료구조입니다. exit reason 필드를 읽으면 CR3 변경인지, I/O 접근인지, HLT 실행인지 즉시 알 수 있으므로 hypervisor가 올바른 에뮬레이션 핸들러를 바로 호출할 수 있습니다. 결국 VMCS는 trap-and-emulate 메커니즘의 효율성과 정확성을 보장하는 핵심 인프라입니다.
