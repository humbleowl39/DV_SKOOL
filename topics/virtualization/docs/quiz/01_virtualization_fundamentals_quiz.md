# Quiz — Module 01: Virtualization Fundamentals

[← Module 01 본문으로 돌아가기](../01_virtualization_fundamentals.md)

---

## Q1. (Remember)

가상화의 3가지 핵심 동기는?

??? answer "정답 / 해설"
    1. **격리** (Isolation) — 한 VM의 fail이 다른 VM 영향 안 줌
    2. **효율** (Efficiency) — 1 physical → N VM, 자원 공유
    3. **Multi-tenant** — 여러 사용자/조직 동시 호스팅 (cloud)

    이 세 가지 동기는 서로 연결되어 있습니다. 격리가 없으면 한 VM의 오류가 전체 시스템을 불안정하게 만들기 때문에 효율적인 자원 공유 자체가 불가능합니다. 효율이 확보되어야 비로소 물리 서버 1대에 여러 조직의 워크로드를 동시에 올리는 multi-tenant 모델이 성립하며, 이것이 현대 클라우드의 핵심 경제 원리가 됩니다.

## Q2. (Understand)

Full / Para / HW-assisted virtualization의 차이는?

??? answer "정답 / 해설"
    - **Full**: HW emulation (모든 instruction software). 호환성 ↑, 성능 매우 ↓.
    - **Para**: Guest OS 수정 + hypercall. 성능 ↑, guest 수정 필요.
    - **HW-assisted**: VT-x/AMD-V/EL2 → CPU가 가상화 root mode 지원. 현재 표준.

    Full virtualization은 guest OS를 전혀 수정하지 않아도 되므로 호환성이 가장 높지만, 모든 privileged instruction을 소프트웨어로 에뮬레이션하는 비용 때문에 성능이 크게 떨어집니다. Para-virtualization은 guest OS에 hypercall 인터페이스를 추가해 불필요한 trap을 줄이므로 성능이 개선되지만 OS 소스 수정이 필수이고 Windows 같은 폐쇄형 OS에는 적용하기 어렵습니다. HW-assisted는 CPU 자체에 root/non-root 실행 모드를 추가해 이 두 단점을 모두 해소했기 때문에 현재 사실상 표준이 되었습니다.

## Q3. (Apply)

다음 중 HW-assisted virtualization 없이도 가능한 것은?

- [ ] A. KVM 기반 Linux VM 호스팅
- [ ] B. QEMU 단독 실행 (TCG mode)
- [ ] C. Xen Type 1 hypervisor
- [ ] D. VMware ESXi

??? answer "정답 / 해설"
    **B**. QEMU TCG (Tiny Code Generator) mode는 binary translation으로 다른 ISA 시뮬 가능 (예: x86 host에서 ARM guest). 매우 느림. 나머지는 모두 VT-x/AMD-V/EL2 의존.

    정답이 B인 이유는 QEMU의 TCG mode가 HW 가상화 지원 없이 순수 소프트웨어 이진 변환(binary translation)으로 동작하기 때문입니다. A의 KVM은 Linux kernel module로 VT-x/AMD-V를 직접 활용하므로 HW 지원 없이는 실행되지 않습니다. C의 Xen Type 1 역시 bare metal에서 EL2/VT-x를 요구하며, D의 VMware ESXi도 마찬가지입니다. B만이 HW 의존 없이 동작하되 성능을 포기하는 대안입니다.

## Q4. (Analyze)

가상화가 부적합한 시나리오는?

??? answer "정답 / 해설"
    - **Real-time hard deadline**: hypervisor overhead로 timing guarantee 어려움
    - **Direct HW access (low-level)**: 가상화 layer가 추가되어 latency ↑
    - **Single tenant + 단일 워크로드**: bare metal이 더 효율
    - **DRM hardware enforcement**: hypervisor 사이를 우회 못 하게 보호 어려움

    가상화가 부적합한 시나리오들은 공통적으로 "가상화 layer 자체가 문제가 되는 상황"입니다. Real-time 시스템은 hypervisor의 스케줄링 간섭이 worst-case latency를 예측 불가능하게 만들고, 저수준 HW 접근이 필요한 경우에는 가상화 layer가 간접 비용을 추가합니다. Single tenant 워크로드는 격리·효율·multi-tenant라는 가상화의 세 가지 동기를 모두 충족시키지 못하므로 bare metal이 적합합니다.

## Q5. (Evaluate)

Multi-tenant cloud (AWS, Azure)가 모든 워크로드에 같은 가상화 사용 안 하는 이유는?

??? answer "정답 / 해설"
    워크로드별 요구사항 다름:
    - **General purpose**: 표준 VM (KVM/Xen)
    - **Lambda/serverless**: microVM (Firecracker, fast startup)
    - **Container service (EKS/AKS)**: container + 일부는 kata-container (격리 강화)
    - **GPU compute**: SR-IOV passthrough (성능)
    
    "한 가지 정답" 없음 — workload-specific.

    동일한 클라우드 플랫폼 안에서도 워크로드마다 격리·성능·밀도 요구사항이 다르기 때문에 단일 가상화 전략은 최적이 될 수 없습니다. Lambda는 cold start가 수백 ms 이내여야 하므로 전통적 VM의 느린 부팅 대신 microVM을 택하고, GPU 컴퓨팅은 소프트웨어 에뮬레이션 오버헤드 없이 line-rate 성능이 필요하므로 SR-IOV passthrough를 사용합니다. 이처럼 "어떤 가상화를 쓸 것인가"는 항상 해당 워크로드의 주된 제약 조건을 먼저 파악하는 것에서 시작합니다.
