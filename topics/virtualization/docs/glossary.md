# Virtualization 용어집

핵심 용어 ISO 11179 형식 정의.

---

## C — Container / cgroup

### Container

**Definition.** Host OS kernel을 공유하면서 namespace + cgroup으로 process 수준 격리를 제공하는 경량 가상화.

**Source.** Linux Container (LXC), Docker.

**Related.** namespace, cgroup, image.

### cgroup (Control Group)

**Definition.** Linux의 자원 (CPU/메모리/IO) 사용 한도 + 우선순위를 group 단위로 강제하는 메커니즘.

**Source.** Linux kernel.

**See also.** [Module 07](07_containers_and_modern.md)

---

## E — EPT / NPT

### EPT (Extended Page Tables)

**Definition.** Intel VT-x의 stage-2 페이지 테이블로, IPA → PA 변환을 HW가 자동 수행.

**Source.** Intel SDM.

**Related.** Stage-2, NPT (AMD), Shadow PT.

**See also.** [Module 03](03_memory_virtualization.md)

### NPT (Nested Page Tables)

**Definition.** AMD-V의 EPT 등가물. 동일 기능, 다른 명칭.

**Source.** AMD architecture manuals.

---

## H — Hypervisor

### Hypervisor (Type 1 / Type 2)

**Definition.** HW 자원을 VM에 분배/격리하는 소프트웨어. Type 1은 bare metal, Type 2는 host OS 위.

**Source.** Virtualization architectures.

**Examples.** Type 1: VMware ESXi, Xen, Hyper-V. Type 2: VirtualBox, VMware Workstation.

**See also.** [Module 05](05_hypervisor_types.md)

---

## K — KVM / KSM

### KVM (Kernel-based Virtual Machine)

**Definition.** Linux kernel module로 구현된 hypervisor. QEMU와 함께 사용. Type 2이지만 Type 1처럼 동작.

**Source.** Linux kernel.

**Related.** QEMU, vCPU.

### KSM (Kernel Same-page Merging)

**Definition.** 같은 내용의 메모리 페이지를 VM 간 공유하여 메모리 사용량을 줄이는 deduplication 기법.

**Source.** Linux kernel.

**See also.** [Module 03](03_memory_virtualization.md)

---

## N — Namespace

### Linux Namespace

**Definition.** Container의 자원 격리 메커니즘 — PID, NET, MNT, UTS, USER, IPC, CGROUP namespace 등.

**Source.** Linux kernel.

**See also.** [Module 07](07_containers_and_modern.md)

---

## S — SR-IOV / Shadow PT

### SR-IOV (Single Root I/O Virtualization)

**Definition.** PCIe spec의 device 가상화 기능으로, 1 PF + N VF로 분할해 각 VF를 VM에 할당.

**Source.** PCIe SR-IOV spec.

**Related.** PF (Physical Function), VF (Virtual Function), VFIO.

**See also.** [Module 04](04_io_virtualization.md)

### Shadow Page Table

**Definition.** Hypervisor가 VA→PA 매핑을 직접 관리하는 별도 페이지 테이블 (구식 SW 방식).

**Source.** Virtualization literature.

**Related.** EPT/NPT (HW 방식이 대체).

---

## T — Trap-and-emulate

### Trap-and-emulate

**Definition.** Privileged instruction 실행 시 trap → hypervisor가 emulate → resume하는 가상화 메커니즘.

**Source.** Virtualization literature.

**Related.** VT-x VMEXIT, sensitive instruction.

**See also.** [Module 02](02_cpu_virtualization.md)

---

## V — VT-x / VMCS / virtio / VFIO

### VT-x

**Definition.** Intel의 HW-assisted virtualization extension으로, root mode (hypervisor) + non-root mode (guest) 분리.

**Source.** Intel SDM.

**Related.** VMCS, VMEXIT, AMD-V (등가).

### VMCS (Virtual Machine Control Structure)

**Definition.** vCPU의 state를 저장하는 자료구조. GP register, control register, exit reason 등.

**Source.** Intel SDM.

**Related.** VMCB (AMD), vCPU.

### virtio

**Definition.** Para-virtualized device의 표준 — guest driver와 hypervisor가 vring + queue로 효율적 통신.

**Source.** virtio specification (OASIS).

**Related.** vring, vhost.

**See also.** [Module 04](04_io_virtualization.md)

### VFIO (Virtual Function I/O)

**Definition.** Linux의 user-space device access framework. IOMMU 기반 직접 device passthrough.

**Source.** Linux kernel.

**Related.** SR-IOV, IOMMU.

**See also.** [Module 04](04_io_virtualization.md)

---

## 추가 약어

| 약어 | 풀네임 | 의미 |
|------|--------|------|
| **VM** | Virtual Machine | 가상 머신 |
| **VMM** | Virtual Machine Monitor | hypervisor 동의어 |
| **vCPU** | Virtual CPU | VM 관점의 CPU |
| **PF / VF** | Physical / Virtual Function | SR-IOV 분할 |
| **microVM** | — | 빠른 startup + VM 격리 (Firecracker) |
| **Stage 2** | — | ARM의 IPA→PA 변환 |
| **Pod** | Kubernetes Pod | 컨테이너 묶음 단위 |
| **OCI** | Open Container Initiative | 컨테이너 표준 |
