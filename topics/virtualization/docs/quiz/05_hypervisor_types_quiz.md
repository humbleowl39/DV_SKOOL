# Quiz — Module 05: Hypervisor Types

[← Module 05 본문으로 돌아가기](../05_hypervisor_types.md)

---

## Q1. (Remember)

Type 1 hypervisor 예시 3개와 Type 2 예시 2개는?

??? answer "정답 / 해설"
    - **Type 1**: VMware ESXi, Xen, Hyper-V (Windows Server), Citrix XenServer
    - **Type 2**: VirtualBox, VMware Workstation/Fusion, Parallels (Mac)

## Q2. (Understand)

KVM이 Type 1과 Type 2 사이의 hybrid인 이유는?

??? answer "정답 / 해설"
    - Strictly: Linux kernel 위에 동작 → Type 2
    - 실질: Linux kernel module로 직접 HW 자원 관리 → Type 1처럼 동작 (Linux kernel 자체가 hypervisor 역할)

    KVM + QEMU는 modern data center의 표준 (RHEV, OpenStack, Proxmox).

## Q3. (Apply)

다음 중 production server에 권장되는 것은?

- [ ] A. VirtualBox
- [ ] B. VMware ESXi
- [ ] C. VMware Workstation
- [ ] D. Hyper-V (Windows 10)

??? answer "정답 / 해설"
    **B**. ESXi는 Type 1 + production-grade. C는 desktop, A는 general purpose, D는 desktop Windows. Server-grade Type 1 hypervisor가 production 표준.

## Q4. (Analyze)

Xen의 Dom0 / DomU 구조의 의미는?

??? answer "정답 / 해설"
    - **Dom0** (Domain 0): privileged VM. Hypervisor와 직접 통신. Device driver 보유, 다른 DomU의 IO 중재.
    - **DomU**: unprivileged VM. 일반 사용자 워크로드. Dom0 통해서만 IO.

    이 구조는 **microkernel-like** — hypervisor 자체는 minimal, 모든 device 로직은 Dom0에. ESXi는 monolithic (모든 driver 내장).

## Q5. (Evaluate)

Hypervisor 선택의 결정적 요인 3개는?

??? answer "정답 / 해설"
    1. **워크로드 종류**: Server (Type 1) vs Desktop (Type 2)
    2. **OS 호환성**: Windows guest 다수면 Hyper-V/ESXi가 호환성 높음
    3. **Ecosystem**: K8s/OpenStack 같은 orchestration tool과 통합 (KVM이 가장 통합 잘됨)
    4. **License/cost**: ESXi는 commercial license, KVM은 open source
    5. **Performance**: PCI passthrough/CPU pinning 등 fine control 필요면 KVM이 유연
