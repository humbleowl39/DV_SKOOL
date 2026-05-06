# Quiz — Module 01: Virtualization Fundamentals

[← Module 01 본문으로 돌아가기](../01_virtualization_fundamentals.md)

---

## Q1. (Remember)

가상화의 3가지 핵심 동기는?

??? answer "정답 / 해설"
    1. **격리** (Isolation) — 한 VM의 fail이 다른 VM 영향 안 줌
    2. **효율** (Efficiency) — 1 physical → N VM, 자원 공유
    3. **Multi-tenant** — 여러 사용자/조직 동시 호스팅 (cloud)

## Q2. (Understand)

Full / Para / HW-assisted virtualization의 차이는?

??? answer "정답 / 해설"
    - **Full**: HW emulation (모든 instruction software). 호환성 ↑, 성능 매우 ↓.
    - **Para**: Guest OS 수정 + hypercall. 성능 ↑, guest 수정 필요.
    - **HW-assisted**: VT-x/AMD-V/EL2 → CPU가 가상화 root mode 지원. 현재 표준.

## Q3. (Apply)

다음 중 HW-assisted virtualization 없이도 가능한 것은?

- [ ] A. KVM 기반 Linux VM 호스팅
- [ ] B. QEMU 단독 실행 (TCG mode)
- [ ] C. Xen Type 1 hypervisor
- [ ] D. VMware ESXi

??? answer "정답 / 해설"
    **B**. QEMU TCG (Tiny Code Generator) mode는 binary translation으로 다른 ISA 시뮬 가능 (예: x86 host에서 ARM guest). 매우 느림. 나머지는 모두 VT-x/AMD-V/EL2 의존.

## Q4. (Analyze)

가상화가 부적합한 시나리오는?

??? answer "정답 / 해설"
    - **Real-time hard deadline**: hypervisor overhead로 timing guarantee 어려움
    - **Direct HW access (low-level)**: 가상화 layer가 추가되어 latency ↑
    - **Single tenant + 단일 워크로드**: bare metal이 더 효율
    - **DRM hardware enforcement**: hypervisor 사이를 우회 못 하게 보호 어려움

## Q5. (Evaluate)

Multi-tenant cloud (AWS, Azure)가 모든 워크로드에 같은 가상화 사용 안 하는 이유는?

??? answer "정답 / 해설"
    워크로드별 요구사항 다름:
    - **General purpose**: 표준 VM (KVM/Xen)
    - **Lambda/serverless**: microVM (Firecracker, fast startup)
    - **Container service (EKS/AKS)**: container + 일부는 kata-container (격리 강화)
    - **GPU compute**: SR-IOV passthrough (성능)
    
    "한 가지 정답" 없음 — workload-specific.
