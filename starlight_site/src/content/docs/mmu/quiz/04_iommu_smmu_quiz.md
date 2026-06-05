---
title: "Quiz — Module 04: IOMMU / SMMU"
---

[← Module 04 본문으로 돌아가기](../../04_iommu_smmu/)

---

## Q1. (Remember)

가상화 환경에서 Stage 1과 Stage 2 translation은 각각 누가 관리하고 무엇을 변환하는가?

<details>
<summary>정답 / 해설</summary>

- **Stage 1**: **OS**가 관리, **VA → IPA** 변환 (guest OS 관점에서 "물리" 주소)
- **Stage 2**: **Hypervisor**가 관리, **IPA → PA** 변환 (실제 하드웨어 주소)

전체 흐름: VA → (Stage 1, OS) → IPA → (Stage 2, hypervisor) → PA

두 단계를 분리한 이유는 게스트 OS와 하이퍼바이저가 각자의 신뢰 도메인을 독립적으로 관리하기 위해서입니다. 게스트 OS는 자신이 관리하는 VA→IPA 매핑만 알면 되고, 실제 물리 메모리 레이아웃을 알 필요가 없습니다. 하이퍼바이저는 여러 VM이 물리 메모리를 공유하도록 IPA→PA 매핑을 통해 각 VM의 메모리 영역을 격리합니다. 이 이중 구조 덕분에 VM 마이그레이션 시 하이퍼바이저가 Stage 2 매핑만 갱신하면 되고, 게스트 OS의 Stage 1 page table은 변경 없이 유지됩니다.

</details>
## Q2. (Understand)

IOMMU 없는 SoC가 보안상 위험한 이유는?

<details>
<summary>정답 / 해설</summary>

DMA 마스터(GPU/USB/NIC/DMA controller)는 IOMMU 없이는 PA로 시스템 메모리에 직접 access 가능. 단일 device가 compromise되면 (firmware bug, supply chain attack 등):
- 커널 메모리 read/write 가능 → root escalation
- 다른 process 메모리 침해 → privacy leak
- 무한 DMA로 시스템 hang

IOMMU는 device를 가상 주소 공간에 격리해 위 공격을 차단.

위험의 본질은 CPU MMU가 CPU 명령어만 보호하지, DMA 트랜잭션은 감시하지 않는다는 구조적 공백에 있습니다. 예를 들어 악성 USB 펌웨어가 DMA 주소로 커널 PA를 직접 지정하면, CPU MMU가 아무리 잘 설정되어 있어도 그 DMA는 메모리 버스를 통해 바로 실행됩니다. IOMMU는 이 DMA 주소가 해당 디바이스에게 허용된 IOVA(I/O Virtual Address) 범위 내인지를 검사하여, 범위 밖이면 트랜잭션 자체를 차단합니다.

</details>
## Q3. (Apply)

같은 SoC에 GPU(StreamID=10)와 NIC(StreamID=20)이 있을 때, 둘이 격리되는 메커니즘을 설명하세요.

<details>
<summary>정답 / 해설</summary>

SMMU가 StreamID별 별도 **Context Descriptor (CD)**를 보유:
- StreamID=10 → GPU의 page table base + ASID
- StreamID=20 → NIC의 page table base + ASID

GPU가 transaction을 발행하면 SMMU는 StreamID로 CD lookup → GPU page table로 변환. NIC도 동일하게 자기 page table만 사용. 둘은 같은 PA를 가질 수 없음(Stage 2 또는 별도 IPA 영역).

격리가 성립하는 이유는 각 디바이스가 자신의 CD에 등록된 page table 외에는 다른 디바이스의 page table로 walk를 진행할 방법이 없기 때문입니다. GPU(StreamID=10)가 어떤 주소를 발행하든 SMMU는 반드시 StreamID=10에 연결된 CD의 page table base로 lookup합니다. NIC의 IOVA 공간과 GPU의 IOVA 공간은 물리적으로는 다른 page table에 존재하므로, GPU가 NIC의 IOVA를 알더라도 그 주소로 NIC의 메모리 영역에 접근할 수 없습니다.

</details>
## Q4. (Analyze)

SVM(Shared Virtual Memory)의 동작에 ATS와 PRI가 각각 어떤 역할을 하는가?

<details>
<summary>정답 / 해설</summary>

- **ATS (Address Translation Services)**: device가 IOMMU에 사전 변환 요청 → device-side TLB(Device TLB)에 PA 캐싱. 이후 transaction은 device가 변환된 PA를 직접 사용 → IOMMU 우회 가능 → 성능 ↑.
- **PRI (Page Request Interface)**: device가 page fault 발생 시 OS에 협력 요청. 일반 device는 fault 처리 못 하지만 PRI로 OS가 페이지 할당 후 device 재시도 알림. SVM의 demand paging 가능하게 함.

ATS와 PRI는 SVM의 서로 다른 문제를 해결합니다. ATS는 성능 문제를 다루는데, 매 DMA 트랜잭션마다 IOMMU에서 변환을 거치는 대신 디바이스 내부에 변환 결과를 캐싱해 반복 접근의 오버헤드를 줄입니다. PRI는 신뢰성 문제를 다루는데, SVM에서는 CPU와 디바이스가 같은 페이지를 사용하므로 디바이스가 아직 물리 메모리에 없는 페이지에 접근할 수 있습니다. PRI 없이는 이 fault가 디바이스를 영구 차단하지만, PRI를 통해 OS에 페이지 요청을 전달하고 응답을 기다린 후 재시도함으로써 demand paging의 이점을 디바이스까지 확장합니다.

</details>
## Q5. (Evaluate)

IOMMU page fault가 CPU page fault와 다르게 비동기로 처리되는 이유는?

<details>
<summary>정답 / 해설</summary>

- **CPU**: 명령어 실행 중에만 fault 발생 → 명령어 stall + 핸들러 후 재실행. 동기 처리가 자연스러움.
- **IOMMU**: device가 비동기적으로 transaction 발행. fault 시 device를 stall 시키기 어렵고, fault 처리 중에도 다른 device는 계속 동작해야 함. 따라서:
  1. Event Queue에 fault 기록
  2. Interrupt로 OS에 통지
  3. OS가 페이지 할당 후 device에 retry 알림 (PRI 또는 device-specific 메커니즘)

동기 처리는 device 디자인 복잡도 + 성능 손실이 너무 큼.

비동기 처리가 불가피한 근본 이유는 CPU와 디바이스의 실행 모델이 다르기 때문입니다. CPU는 하나의 명령어가 완전히 완료되어야 다음으로 넘어가는 순차 실행 모델이므로, fault 발생 시 그 명령어를 stall하고 핸들러를 실행한 후 재개하는 것이 자연스럽습니다. 반면 DMA 컨트롤러는 수십~수백 개의 트랜잭션을 독립적으로 in-flight 상태로 관리하며, 그 중 하나의 fault를 처리하는 동안 나머지를 멈출 이유가 없습니다. 이런 구조에서 동기 처리를 강제하면 하드웨어 큐 관리와 재시도 메커니즘이 극도로 복잡해지므로, event queue + interrupt 기반 비동기 처리가 현실적인 설계입니다.

</details>

## Q6. (Apply)

어떤 IOVA 범위를 device 에서 unmap 하는 SW 흐름을 작성하려 한다. `TLBI`(또는 `ATC_INV`)만 보내고 `SYNC` 를 빠뜨렸을 때 발생할 수 있는 보안 문제와, 올바른 명령 시퀀스를 설명하세요.

<details>
<summary>정답 / 해설</summary>

`SYNC` 를 빠뜨리면 invalidation 이 device(특히 ATS device 의 ATC)까지 _완료되기 전_ 에 SW 가 다음 단계(물리 페이지 재할당 등)로 진행할 수 있습니다. 그 사이 device 는 여전히 옛 IOVA→PA 매핑을 캐싱하고 있으므로, 이미 해제되어 다른 용도로 재할당된 물리 페이지를 DMA 로 read/write 할 수 있습니다. 즉 **stale IOTLB/ATC entry = freed page 가 DMA 로 reachable** 한 use-after-free 형태의 메모리 침해입니다.

올바른 시퀀스:
```
1. TLBI_*           ← IOTLB 에서 해당 매핑 제거
2. ATC_INV (ATS면)  ← device 의 ATC 에도 Invalidate Request 전송
3. SYNC             ← 위 invalidation 들이 device 까지 완료됐음을 보장하는 fence
4. (SYNC 완료 후에만) 물리 페이지 재할당
```

CPU TLB 는 owner core 가 스스로 비우지만 IOMMU cache 는 공유 자원이라 SW 가 명시적으로 무효화해야 하고, 이 invalidation round-trip 이 unmap latency 의 실체이자 streaming 워크로드의 주요 성능 비용입니다.

</details>

## Q7. (Evaluate)

데이터 경로(DMA read/write) 격리만으로는 IOMMU 의 보안이 완성되지 않는다. interrupt remapping, ACS, vIOMMU(nested), pre-boot DMA protection 이 각각 어떤 공격면을 닫는지 평가하세요.

<details>
<summary>정답 / 해설</summary>

- **Interrupt remapping**: MSI/MSI-X 는 결국 device 의 메모리 write 이므로, 통제 없으면 악성 device 가 임의 vector 를 임의 CPU 에 주입해 권한 상승/DoS 가 가능. Interrupt Remapping Table 이 vector 를 검증·재매핑해 이 injection 경로를 닫는다.
- **ACS (Access Control Services)**: 두 function 이 IOMMU 를 거치지 않고 직접 P2P 통신하면 격리가 무의미. ACS 가 peer-to-peer 라우팅을 통제하며, 그 가능 여부가 Linux IOMMU group(독립 assign 가능한 최소 device 집합) 경계를 결정한다.
- **vIOMMU / nested**: guest 가 자기 IOMMU(Stage 1)를 갖되 그 table walk 자체가 host Stage 2 로 다시 변환되어, passthrough device 를 소유한 VM 도 host/다른 VM 의 PA 에 닿지 못하게 막는다.
- **Pre-boot DMA protection**: IOMMU 가 프로그래밍되기 _전_ 부팅 초기 window 가 Thunderbolt/PCIe evil-maid DMA 에 노출되므로, reset 직후부터 default-deny 상태를 유지해 그 구멍을 닫는다.

종합하면 IOMMU 의 위협 모델은 "버그 있는 device" 를 넘어 "위조 인터럽트, P2P 우회, 신뢰 불가 hypervisor(TDISP), 부팅 초기 노출" 까지 확장되며, 각 기능이 서로 다른 공격면을 담당한다.

</details>
