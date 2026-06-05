---
title: "DPU 용어집"
---

이 페이지는 본 코스에서 사용되는 DPU / SmartNIC 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

:::tip[검색 활용]
상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.
:::
---

## B — Bare Metal Service

### Bare Metal Service

**Definition.** 호스트에 하이퍼바이저를 두지 않고 DPU가 관리형 네트워크·스토리지를 제공해 물리 서버를 클라우드처럼 운영하게 하는 가상화 오프로드 형태.

**Source.** `common/dpu_spec.md` §5 (주요 활용 사례).

**Related.** Virtualization Offload, Isolation, Hypervisor.

**Example.** 호스트 OS에 하이퍼바이저 없이도 DPU가 가상 스토리지와 네트워크를 제공해, 테넌트가 물리 서버를 전용으로 쓰면서도 관리형 인프라를 받습니다.

**See also.** [Module 02 — 오프로드 도메인](../02_offload_domains/)

---

## C — Control Path / Compute-Storage-Networking

### Control Path

**Definition.** 정책 결정·관리·격리처럼 "누가 무엇에 접근하는가"를 다루는 처리 경로로, DPU에서 주로 프로그래머블 코어 위 소프트웨어가 담당한다.

**Source.** `common/dpu_spec.md` §6 (데이터 패스/제어 패스 프로그래밍 범위), 본 코스 분류.

**Related.** Data Path, Programmable Core, Offload.

**Example.** 테넌트 격리 정책이나 트래픽 정책 결정은 데이터 패스 가속기가 아니라 제어 패스의 코어 소프트웨어가 수행합니다.

**See also.** [Module 02](../02_offload_domains/)

### Compute / Storage / Networking 관점

**Definition.** 컴퓨터 시스템을 계산(CPU·GPU), 저장(메모리·SSD), 통신(NIC·스위치) 세 축으로 나누어 보는 관점으로, DPU는 통신 축이 고속·프로그래머블해지는 과정에서 등장한 장치다.

**Source.** `common/dpu_spec.md` §1.1.

**Related.** DPU, NIC, GPU.

**Example.** AI 워크로드에서 여러 서버·GPU·스토리지를 잇는 데이터 이동 경로(통신 축)가 병목이 되며, DPU가 이 축의 작업을 가속합니다.

**See also.** [Module 01 — DPU란 무엇인가](../01_what_is_dpu/)

---

## D — Data Path / Datacenter Tax / DMA / DPU

### Data Path

**Definition.** 패킷 분류·전달, DMA, NVMe-oF, 암호화처럼 데이터가 흐르는 처리 경로로, DPU에서 주로 전용 데이터 패스 엔진과 가속기가 담당한다.

**Source.** `common/dpu_spec.md` §3 (데이터 패스 처리 엔진).

**Related.** Control Path, Accelerator, DMA.

**Example.** 들어온 패킷을 분류·전달하고 호스트 메모리로 DMA하는 작업은 데이터 패스 엔진이 가속합니다.

**See also.** [Module 02](../02_offload_domains/)

### Datacenter Tax

**Definition.** 서버와 데이터가 늘어날수록 호스트 CPU가 네트워킹·스토리지·보안·가상화 같은 인프라 작업에 점점 더 많은 자원을 쓰게 되는 비용. *(common DPU usage — spec은 동일 현상을 §1에서 설명)*

**Source.** `common/dpu_spec.md` §1 (DPU가 필요한 이유), 일반 업계 용어.

**Related.** Offload, CPU 자원 확보.

**Example.** 64코어 서버에서 다수 코어가 vSwitch·NVMe-oF·암호화 같은 인프라 처리에 묶여 애플리케이션에 쓰이지 못하는 상황.

**See also.** [Module 01](../01_what_is_dpu/)

### DMA (Direct Memory Access)

**Definition.** CPU의 직접 개입 없이 디바이스가 메모리에 데이터를 읽고 쓰는 전송 방식으로, DPU 데이터 패스 엔진의 핵심 기능 중 하나.

**Source.** `common/dpu_spec.md` §3 (데이터 패스 처리 엔진: DMA), `common/iommu.md` (Related).

**Related.** Data Path, Host Interface, IOMMU.

**Example.** 원격 스토리지에서 받은 데이터를 DPU가 호스트 CPU 개입을 최소화하며 VM 메모리로 직접 전달합니다.

**See also.** [Module 03 — DV 연관](../03_dpu_in_datacenter_and_dv/)

### DPU (Data Processing Unit)

**Definition.** 네트워킹·스토리지·보안 같은 데이터센터 인프라 작업을 호스트 CPU에서 분리해 처리하는, 고속 NIC·프로그래머블 코어·메모리·데이터 패스 가속기를 통합한 프로그래머블 프로세서.

**Source.** `common/dpu_spec.md` Overview, §3.

**Related.** SmartNIC, NIC, IPU, Offload, Host Interface.

**Example.**
```
구성요소: 고속 네트워크 인터페이스 + 프로그래머블 코어/메모리
        + PCIe 호스트 인터페이스 + 데이터 패스 엔진 + 전용 가속기
```

**See also.** [Module 01](../01_what_is_dpu/)

---

## H — Host Interface

### Host Interface

**Definition.** DPU와 서버를 연결하는 인터페이스로, 일반적으로 PCIe를 통해 호스트와 DPU 간 요청·데이터를 전달한다.

**Source.** `common/dpu_spec.md` §3 (호스트 인터페이스), `common/pcie_basics_usage.md` (Related).

**Related.** PCIe, DMA, DPU.

**Example.** 호스트가 PCIe를 통해 원격 read 요청을 DPU에 전달하고, DPU는 결과를 DMA로 호스트 메모리에 반환합니다.

**See also.** [Module 03](../03_dpu_in_datacenter_and_dv/)

---

## I — IPU / Isolation

### IPU (Infrastructure Processing Unit)

**Definition.** 일부 벤더가 DPU와 유사한 데이터센터 인프라 오프로드 프로세서를 가리키는 데 사용하는 명칭.

**Source.** `common/dpu_spec.md` Overview, §6.

**Related.** DPU, SmartNIC, Offload.

**Example.** 두 제품이 각각 "DPU"와 "IPU"로 불려도, 비교는 명칭이 아니라 실제 오프로드 기능·프로그래머빌리티로 해야 합니다.

**See also.** [Module 01](../01_what_is_dpu/)

### Isolation (격리)

**Definition.** 인프라 서비스를 호스트 OS 및 테넌트 워크로드와 분리해 상호 간섭과 무단 접근을 막는 DPU의 핵심 동기이자 검증 대상.

**Source.** `common/dpu_spec.md` §1 (격리 강화), §5 (클라우드 인프라 격리).

**Related.** Virtualization Offload, Bare Metal Service, Security Offload.

**Example.** 베어메탈 서비스에서는 하이퍼바이저 없이 DPU가 테넌트를 격리하므로, 격리 위반은 검증이 잡아야 할 심각 결함입니다.

**See also.** [Module 03](../03_dpu_in_datacenter_and_dv/)

---

## N — NIC / NVMe-oF

### NIC (Network Interface Card)

**Definition.** 서버를 네트워크에 연결하며 체크섬·segmentation 같은 제한된 고정 기능 오프로드를 제공하는 네트워크 인터페이스 장치.

**Source.** `common/dpu_spec.md` §2 (NIC/SmartNIC/DPU 비교).

**Related.** SmartNIC, DPU, Offload.

**Example.** 2000년대 NIC가 제공한 체크섬·segmentation 고정 오프로드가 이후 SmartNIC·DPU 진화의 출발점이 되었습니다.

**See also.** [Module 01](../01_what_is_dpu/)

### NVMe-oF (NVMe over Fabrics)

**Definition.** 네트워크 패브릭 너머의 NVMe 스토리지에 접근하게 하는 프로토콜로, DPU 스토리지 오프로드의 대표 기능.

**Source.** `common/dpu_spec.md` §5 (스토리지 오프로드).

**Related.** Storage Offload, Virtual Storage Device, Data Path.

**Example.** DPU가 VM에게 로컬 NVMe처럼 보이는 디바이스를 제공하고, 실제로는 NVMe-oF로 원격 SSD에 접근합니다.

**See also.** [Module 02](../02_offload_domains/) · 개별 코스 [NVMe](../../nvme/)

---

## O — Offload Domain

### Offload Domain

**Definition.** DPU가 호스트에서 가져오는 인프라 작업을 성격에 따라 네트워킹·스토리지·보안·가상화로 나눈 기능 분류.

**Source.** `common/dpu_spec.md` §5 (주요 활용 사례), 본 코스 분류.

**Related.** Data Path, Control Path, Accelerator.

**Example.** NVMe-oF 읽기 한 번이 스토리지·네트워킹·보안·가상화 도메인을 모두 가로지를 수 있습니다.

**See also.** [Module 02](../02_offload_domains/)

---

## S — SmartNIC

### SmartNIC

**Definition.** 패킷 처리 로직을 프로그래밍할 수 있고 네트워크 및 보안 기능 일부를 오프로드하는, 네트워크 처리 중심의 프로그래머블 네트워크 인터페이스 장치.

**Source.** `common/dpu_spec.md` §2 (NIC/SmartNIC/DPU 비교).

**Related.** NIC, DPU, Programmable Offload.

**Example.** FPGA 기반 SmartNIC가 가상 스위칭·패킷 필터링을 프로그래머블하게 처리한 것이 DPU로 이어지는 중간 단계였습니다.

**See also.** [Module 01](../01_what_is_dpu/)

---

## 추가 약어

| 약어 | 풀네임 | 한 줄 의미 |
|------|--------|-----------|
| **DPU** | Data Processing Unit | 인프라 오프로드 프로세서 |
| **IPU** | Infrastructure Processing Unit | DPU 유사 명칭 (벤더별) |
| **NIC** | Network Interface Card | 네트워크 연결 장치 |
| **NVMe-oF** | NVMe over Fabrics | 네트워크 너머 NVMe 접근 |
| **RDMA** | Remote Direct Memory Access | 원격 메모리 직접 접근 |
| **TOE** | TCP Offload Engine | TCP 처리 오프로드 엔진 |
| **DMA** | Direct Memory Access | CPU 개입 없는 메모리 전송 |
