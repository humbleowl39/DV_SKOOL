---
title: "Quiz — Module 04: I/O Virtualization"
---

[← Module 04 본문으로 돌아가기](../../04_io_virtualization/)

---

## Q1. (Remember)

I/O 가상화 3가지 모델은?

<details>
<summary>정답 / 해설</summary>

1. **Emulation** — Hypervisor가 device 시뮬
2. **Paravirtualization (virtio)** — Guest driver + hypervisor 공유 ring
3. **Passthrough (SR-IOV/VFIO)** — Device 직접 VM 할당

이 세 모델은 "hypervisor 개입 정도"와 "성능" 사이의 트레이드오프를 따라 배열됩니다. Emulation은 hypervisor가 모든 IO 요청을 소프트웨어로 처리하므로 호환성이 가장 높지만 성능이 가장 낮습니다. Virtio는 guest와 hypervisor가 공유 vring을 통해 직접 통신해 IO 경로의 오버헤드를 줄이며 범용적으로 사용됩니다. Passthrough는 hypervisor를 완전히 우회해 device를 VM에 직접 붙이므로 성능은 bare metal에 가깝지만, 격리와 live migration이 어려워집니다.

</details>
## Q2. (Understand)

SR-IOV의 PF와 VF 차이는?

<details>
<summary>정답 / 해설</summary>

- **PF (Physical Function)**: Full-featured PCIe device. Driver가 모든 기능 사용. Host가 보유.
- **VF (Virtual Function)**: Lightweight 변형. PF 자원의 일부 (queue, MMIO BAR 등)를 가지고 VM에 할당. 주요 fast-path만 직접 access.

예: SR-IOV NIC → 1 PF (host) + 8 VF (8 VM 각각).

PF와 VF의 관계는 "원본과 경량 복제"로 이해하면 쉽습니다. PF는 device 설정·초기화·전체 제어를 담당하고 보통 host(hypervisor)가 소유합니다. VF는 PF가 만들어낸 가상 인스턴스로, 데이터 전송에 필요한 최소한의 자원(TX/RX queue, MMIO BAR 일부)만 가지고 있습니다. 이 구조 덕분에 한 물리 NIC이 여러 VM에 동시에 near-native 성능의 네트워크를 제공할 수 있으며, 각 VF는 IOMMU를 통해 서로 격리됩니다.

</details>
## Q3. (Apply)

다음 시나리오에 적합한 모델은?

| 시나리오 | 적합 모델 |
|----------|----------|
| (a) 100Gbps NIC for HPC VM | ? |
| (b) Legacy DOS VM | ? |
| (c) Generic VM with throughput needs | ? |
| (d) GPU compute (CUDA) | ? |

<details>
<summary>정답 / 해설</summary>

- (a) **Passthrough (SR-IOV)** — line rate 필요
- (b) **Emulation** — DOS는 modern driver 없음
- (c) **virtio** — 호환성 + 성능 균형
- (d) **Passthrough (VFIO)** — GPU는 보통 1 VM에 전용

각 선택의 이유를 연결해 보면 패턴이 보입니다. (a)는 100Gbps line-rate가 요구되므로 소프트웨어 IO 경로를 완전히 배제해야 하고, SR-IOV NIC의 VF를 VM에 직접 붙이는 것만이 그 요구를 충족합니다. (b)의 레거시 DOS는 virtio 드라이버를 설치할 방법이 없으므로, hypervisor가 DOS 시절 하드웨어(예: ISA 버스 장치)를 소프트웨어로 에뮬레이션해야 합니다. (c)는 특별히 극단적인 성능 요구가 없으므로 범용성과 성능을 모두 갖춘 virtio가 최적이고, (d)의 CUDA GPU는 드라이버와 펌웨어가 물리 하드웨어 상태를 직접 관리하기 때문에 에뮬레이션이나 분할 없이 1:1 passthrough만 지원됩니다.

</details>
## Q4. (Analyze)

Passthrough 환경에서 IOMMU 없으면 어떤 위험이 있는가?

<details>
<summary>정답 / 해설</summary>

Device가 DMA로 host 메모리 무제한 access 가능. VM에 할당된 device가 compromise되면:
1. Hypervisor 메모리 read → host secret leak
2. Hypervisor 메모리 write → host kernel compromise
3. 다른 VM 메모리 access → cross-tenant attack

IOMMU가 device의 DMA를 가상 주소로 격리해 위 모두 차단.

CPU의 MMU가 process가 접근할 수 있는 메모리를 제한하듯, IOMMU는 device가 DMA로 접근할 수 있는 물리 주소 범위를 제한합니다. IOMMU 없이 device를 VM에 passthrough하면 그 device는 물리 주소 공간 전체에 DMA 쓰기가 가능하므로, device 펌웨어 취약점 하나가 hypervisor 커널을 덮어쓰거나 옆 VM의 메모리를 읽는 것으로 이어질 수 있습니다. 이것이 IOMMU 지원 여부가 passthrough 환경의 필수 보안 요건인 이유입니다.

</details>
## Q5. (Evaluate)

Modern data center에서 모든 device를 passthrough 하지 않는 이유는?

<details>
<summary>정답 / 해설</summary>

1. **Resource ratio**: SR-IOV VF는 한정 (e.g., 8-128). 수천 VM 호스팅 어려움.
2. **Live migration**: passthrough device는 migration 어려움 (state in HW).
3. **격리 trade-off**: passthrough는 IOMMU 의존이라 IOMMU bug = 전체 보안 risk.
4. **Density**: virtio는 software로 무한 multiplex 가능.

Hybrid 접근이 최적 — performance-critical만 passthrough.

Passthrough를 전체에 적용하지 않는 가장 실질적 이유는 VF 수의 상한과 live migration 불가입니다. 한 물리 NIC이 제공하는 VF는 수십~수백 개에 불과하지만, 데이터센터 한 대 rack의 VM 수는 그보다 훨씬 많습니다. 또한 passthrough된 device는 내부 상태가 하드웨어에 있기 때문에 VM을 다른 물리 호스트로 이동하는 live migration이 불가능해지고, 이는 클라우드의 무중단 운영 모델과 충돌합니다. 따라서 성능이 결정적으로 중요한 워크로드만 passthrough를 할당하고, 나머지는 소프트웨어로 무한히 multiplex할 수 있는 virtio를 사용하는 hybrid 전략이 현실적입니다.

</details>
## Q6. (Apply)

split ring virtqueue에서 device가 "처리할 새 작업이 있는지"를 판정하는 조건은?

- [ ] A. `used_idx != last_used_idx`
- [ ] B. `avail_idx != last_avail_idx`
- [ ] C. descriptor table의 `flags`에 NEXT 비트가 있을 때
- [ ] D. doorbell 레지스터 값이 0이 아닐 때

<details>
<summary>정답 / 해설</summary>

**B**. available ring은 driver→device 방향의 작업 지시함입니다. driver가 descriptor를 올릴 때마다 `avail_idx`를 증가시키고, device는 자기 내부의 `last_avail_idx`까지 읽었습니다. 따라서 `avail_idx != last_avail_idx`이면 device 입장에서 아직 안 읽은 새 작업이 남았다는 뜻입니다. 실제 슬롯은 `idx % Q`로 계산하며 index는 wrap하지 않고 단조 증가하므로, 별도의 empty/full flag 없이 이 비교만으로 판정합니다. A(`used_idx != last_used_idx`)는 반대 방향 — driver가 회수할 완료 항목이 있는지를 보는 조건입니다. C와 D는 작업 유무 판정과 무관합니다.

</details>
## Q7. (Analyze)

x86 host에서는 정상 동작하던 virtio-net driver를 ARM 기반 SmartNIC backend와 함께 쓰니 device가 descriptor의 옛 내용을 읽는 버그가 발생한다. 가장 가능성 높은 원인은?

<details>
<summary>정답 / 해설</summary>

**Memory barrier 순서 누락**입니다. ARM, RISC-V 같은 weak-memory 아키텍처는 CPU가 store 순서를 재배열할 수 있어, driver가 descriptor 내용을 쓰는 store와 `avail_idx++` store의 순서가 device 관점에서 뒤바뀔 수 있습니다. 그러면 device가 증가된 `avail_idx`를 먼저 관측하고도 descriptor는 아직 갱신되지 않은 옛 값을 읽습니다. 올바른 순서는 (1) descriptor write → wmb, (2) `avail_idx++` → wmb, (3) doorbell kick입니다. x86은 strong memory model이라 barrier가 없어도 우연히 올바른 순서가 유지되어 버그가 드러나지 않다가, ARM으로 backend를 옮기면 비로소 노출되는 전형적인 케이스입니다. 해결책은 driver가 spec이 요구하는 wmb를 각 단계 사이에 삽입했는지 검증하는 것입니다.

</details>
