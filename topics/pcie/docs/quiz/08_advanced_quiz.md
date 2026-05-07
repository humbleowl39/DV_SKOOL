# Quiz — Module 08: SR-IOV, ATS, P2P, CXL

[← Module 08 본문으로 돌아가기](../08_advanced.md)

---

## Q1. (Remember)

SR-IOV 의 PF 와 VF 의 역할을 한 줄로 비교하라.

??? answer "정답 / 해설"
    - **PF (Physical Function)**: 일반 PCIe device, 전체 device 의 entry, VF 생성/관리/설정.
    - **VF (Virtual Function)**: lightweight, **자기 BDF + BAR + MSI-X**, hypervisor 가 게스트에 직접 패스스루. Configuration register 일부만 지원.

## Q2. (Understand)

ATS Translation Request 와 일반 Memory TLP 의 차이는?

??? answer "정답 / 해설"
    - **ATS Translation Request**: 새로운 TLP 종류, IOMMU 에 IOVA→PA 변환만 요청, payload 없음. Completion 으로 PA 받음.
    - **일반 Memory TLP** (with AT field): TLP 의 AT field 가 "Translated" 면 IOMMU bypass, "Untranslated" 면 IOMMU 변환.

    즉 ATS = "변환 미리 받기" + "이후 TLP 는 변환된 PA 직접 사용".

## Q3. (Apply)

GPU 와 NIC 가 같은 Switch 아래 있는데 P2P 가 동작하지 않는다. 첫 번째로 확인할 것은?

??? answer "정답 / 해설"
    **ACS (Access Control Services) 정책**.

    Switch 의 downstream port 의 ACS bit:

    - **Source Validation**: TLP 의 Requester ID 검증.
    - **P2P Request Redirect**: P2P request 를 RC 로 redirect 강제.
    - **P2P Completion Redirect**: 동일하게 Cpl redirect.

    이 redirect bit 이 켜져 있으면 P2P TLP 가 Switch 안에서 직접 가지 않고 RC 로 올라감 → P2P 효과 없음.

    **Default 정책은 보안상 P2P 차단** — IOMMU 우회 가능성. 명시적 enable 필요. BIOS / OS / Switch firmware 모두에서 확인.

## Q4. (Analyze)

CXL 이 PCIe 와 같은 connector 를 사용하면서도 별도 protocol 인 이유를 분석하라.

??? answer "정답 / 해설"
    **이유**:

    1. **PCIe 는 cache 일관성을 가정 안 함** — Memory write/read 는 host CPU cache 와 별도 path. Accelerator (GPU 등) 가 host memory 를 access 하려면 cache flush + sync 필요.
    2. **CXL 은 cache-coherent**: CXL.cache 가 device 의 cache line 을 host CPU cache 와 일관성 유지. Device 가 마치 CPU core 처럼 host memory 를 cache.
    3. **CXL.mem**: host CPU 가 device-attached memory 를 자기 메모리 같이 access — DDR 모듈 확장의 새 모델.
    4. **PCIe spec 만으로는 위 둘을 표현 불가** → 별도 link layer + transport 필요.

    **공유 PHY 의 가치**: Connector / cable / SerDes 는 공유 → ecosystem 확장 비용 ↓. Alternate Protocol Negotiation 으로 link bring-up 시 PCIe vs CXL 결정.

    → 즉 CXL 은 "PCIe 보다 한 단계 더 강력한 시맨틱이 필요한 use-case (AI accelerator, memory pooling)" 를 위해 PCIe 위에 만든 것.

## Q5. (Evaluate)

"SR-IOV 가 있으면 가상화 overhead 가 0 이다" 는 주장을 평가하라.

??? answer "정답 / 해설"
    **거의 0 이지만 완전 0 은 아님**.

    **0 에 가까운 부분**:

    - VF 가 게스트에 직접 패스스루 → driver 호출 → MMIO ↔ device 직접.
    - DMA 도 IOMMU 가 PASID/IOVA 로 격리 → hypervisor 의 매 transaction 개입 없음.
    - Throughput / latency 가 PF 와 거의 동등 (VM 안에서 line rate 가능).

    **남는 overhead**:

    1. **Interrupt routing**: MSI-X 가 hypervisor → 게스트로 가는 path 에 약간의 latency.
    2. **IOMMU TLB miss**: ATS 가 enabled 되어도 첫 access 는 IOMMU walk 필요.
    3. **Live migration 비호환**: VF 가 직접 패스스루이므로 vMotion 같은 live migration 어려움 (state freeze 어려움) → modern 솔루션은 VFIO migration framework 발전 중.
    4. **자원 한계**: VF 갯수가 silicon 에 의해 제한 → 무한 게스트 OK 아님.
    5. **Capability mismatch**: 일부 game / 특수 IOCTL 은 VF 에서 지원 안 될 수 있음.

    → "거의 0" 이라는 표현이 맞고, 실제 production 환경 (cloud, NFV) 에서 SR-IOV 는 사실상 표준. 단, 그 의미를 "절대 0" 으로 단정은 부정확.
