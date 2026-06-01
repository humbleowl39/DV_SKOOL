# Quiz — Module 05: Hypervisor Types

[← Module 05 본문으로 돌아가기](../05_hypervisor_types.md)

---

## Q1. (Remember)

Type 1 hypervisor 예시 3개와 Type 2 예시 2개는?

??? answer "정답 / 해설"
    - **Type 1**: VMware ESXi, Xen, Hyper-V (Windows Server), Citrix XenServer
    - **Type 2**: VirtualBox, VMware Workstation/Fusion, Parallels (Mac)

    Type 1과 Type 2의 구분은 단순히 제품 목록을 외우는 것이 아니라 "hypervisor 아래에 범용 OS가 있는가"를 판단하는 것입니다. Type 1은 bare metal에서 직접 실행되므로 hypervisor가 HW 자원을 직접 스케줄링하고 드라이버도 직접 보유합니다. Type 2는 Windows나 Linux 같은 host OS 위에 애플리케이션처럼 올라가므로, 모든 HW 접근이 host OS를 경유합니다. 이 경유 비용 때문에 Type 2는 개발·테스트용으로는 편리하지만, 프로덕션 서버에는 Type 1을 사용합니다.

## Q2. (Understand)

KVM이 Type 1과 Type 2 사이의 hybrid인 이유는?

??? answer "정답 / 해설"
    - Strictly: Linux kernel 위에 동작 → Type 2
    - 실질: Linux kernel module로 직접 HW 자원 관리 → Type 1처럼 동작 (Linux kernel 자체가 hypervisor 역할)

    KVM + QEMU는 modern data center의 표준 (RHEV, OpenStack, Proxmox).

    KVM이 hybrid로 불리는 이유는 분류 기준을 어디에 두느냐에 따라 답이 달라지기 때문입니다. 엄격히는 Linux 커널이 있어야 KVM이 동작하므로 "host OS 위의 hypervisor" 즉 Type 2입니다. 그러나 KVM은 Linux 커널 모듈로 통합되어 CPU 가상화(VT-x)와 메모리 관리를 직접 제어하므로, 실질적인 성능과 아키텍처는 bare metal Type 1과 동등합니다. QEMU가 device 에뮬레이션을 담당하고 KVM이 CPU/메모리 가상화를 담당하는 분업 구조가 이 hybrid 특성의 핵심입니다.

## Q3. (Apply)

다음 중 production server에 권장되는 것은?

- [ ] A. VirtualBox
- [ ] B. VMware ESXi
- [ ] C. VMware Workstation
- [ ] D. Hyper-V (Windows 10)

??? answer "정답 / 해설"
    **B**. ESXi는 Type 1 + production-grade. C는 desktop, A는 general purpose, D는 desktop Windows. Server-grade Type 1 hypervisor가 production 표준.

    정답이 B인 이유는 VMware ESXi가 Type 1 hypervisor로 bare metal에서 직접 실행되며 엔터프라이즈 프로덕션 환경의 요건(고가용성, live migration, 중앙 관리)을 모두 갖추고 있기 때문입니다. A의 VirtualBox는 개인 개발 및 학습용으로 설계된 Type 2이고, C의 VMware Workstation 역시 데스크톱 Type 2로 서버 자원 관리 기능이 없습니다. D의 Hyper-V는 Windows 10의 데스크톱 기능이 아닌 Windows Server 버전이 프로덕션 표준입니다.

## Q4. (Analyze)

Xen의 Dom0 / DomU 구조의 의미는?

??? answer "정답 / 해설"
    - **Dom0** (Domain 0): privileged VM. Hypervisor와 직접 통신. Device driver 보유, 다른 DomU의 IO 중재.
    - **DomU**: unprivileged VM. 일반 사용자 워크로드. Dom0 통해서만 IO.

    이 구조는 **microkernel-like** — hypervisor 자체는 minimal, 모든 device 로직은 Dom0에. ESXi는 monolithic (모든 driver 내장).

    Xen의 Dom0/DomU 구조는 "hypervisor를 최대한 작게 유지해 공격 표면을 줄인다"는 설계 철학에서 나온 것입니다. Hypervisor 자체에 device 드라이버를 넣지 않고 Dom0(privileged VM)에 위임함으로써, 드라이버 버그가 hypervisor 전체를 무너뜨리는 위험을 줄입니다. 반면 VMware ESXi는 모든 드라이버와 관리 기능을 hypervisor 안에 통합하는 monolithic 구조를 택해 관리 단순성과 성능을 높이는 대신, hypervisor 코드베이스가 더 크고 복잡해집니다. 이 두 설계는 microkernel vs monolithic kernel 논쟁과 동일한 트레이드오프입니다.

## Q5. (Evaluate)

Hypervisor 선택의 결정적 요인 3개는?

??? answer "정답 / 해설"
    1. **워크로드 종류**: Server (Type 1) vs Desktop (Type 2)
    2. **OS 호환성**: Windows guest 다수면 Hyper-V/ESXi가 호환성 높음
    3. **Ecosystem**: K8s/OpenStack 같은 orchestration tool과 통합 (KVM이 가장 통합 잘됨)
    4. **License/cost**: ESXi는 commercial license, KVM은 open source
    5. **Performance**: PCI passthrough/CPU pinning 등 fine control 필요면 KVM이 유연

    이 요인들은 서로 독립적이지 않고 함께 검토해야 합니다. 예를 들어, 대규모 OpenStack 클라우드를 구축하는 경우 에코시스템 통합(KVM이 압도적)과 라이선스 비용(KVM은 오픈소스)이 동시에 KVM을 가리킵니다. 반면 VMware 중심의 기업 환경에서 Windows 게스트를 대규모로 운영한다면 ESXi의 Windows 호환성과 vSphere 관리 도구가 결정적 이점입니다. "어떤 hypervisor가 최선"이라는 절대 답은 없고, 항상 이 다섯 요인을 현재 환경에 대입해 우선순위를 따져야 합니다.
