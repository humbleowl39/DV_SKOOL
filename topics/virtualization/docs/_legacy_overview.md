# Virtualization — 개요 및 컨셉 맵

## 학습 플랜
- **레벨**: Beginner → Intermediate (시스템 아키텍처 이해, HW/SW 가상화 전반)
- **목표**: 가상화의 핵심 원리를 이해하고, Strict System vs Hypervisor Pass-through의 트레이드오프를 설명할 수 있는 수준

## 핵심 용어집 (Glossary)

### 기본 개념

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **VM** | Virtual Machine | 하드웨어를 소프트웨어로 추상화한 가상 컴퓨터 |
| **VMM** | Virtual Machine Monitor | = Hypervisor. VM을 생성/관리하는 소프트웨어 |
| **Hypervisor** | — | HW 자원을 VM에 분배/관리하는 특권 소프트웨어 |
| **Guest** | — | VM 위에서 동작하는 OS |
| **Host** | — | 하이퍼바이저가 동작하는 물리 머신 또는 OS |
| **Bare Metal** | — | OS/하이퍼바이저 없이 HW 위에서 직접 실행하는 방식 |

### ARM Exception Levels

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **EL0** | Exception Level 0 | User-space 애플리케이션 (비특권) |
| **EL1** | Exception Level 1 | OS 커널 (각 VM의 Guest OS) |
| **EL2** | Exception Level 2 | Hypervisor (최상위 가상화 관리) |
| **EL3** | Exception Level 3 | Secure Monitor (TrustZone) |
| **SVC** | SuperVisor Call | EL0 → EL1 전환 (시스템 콜) |
| **HVC** | HyperVisor Call | EL1 → EL2 전환 (하이퍼바이저 호출) |
| **SMC** | Secure Monitor Call | EL1/EL2 → EL3 전환 |

### 메모리 가상화

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **VA** | Virtual Address | 프로세스가 사용하는 가상 주소 |
| **IPA** | Intermediate Physical Address | VM이 보는 "가짜 물리 주소" (Stage1 결과) |
| **PA** | Physical Address | 실제 DRAM 물리 주소 |
| **EPT** | Extended Page Table | Intel의 2-stage translation HW 지원 |
| **NPT** | Nested Page Table | AMD의 2-stage translation HW 지원 |
| **SLAT** | Second Level Address Translation | 2-stage translation의 일반 명칭 |

### I/O 가상화

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **SR-IOV** | Single Root I/O Virtualization | 하나의 PCIe 디바이스를 여러 VF로 분할하는 스펙 |
| **PF** | Physical Function | SR-IOV에서 실제 물리 디바이스 기능 |
| **VF** | Virtual Function | SR-IOV에서 생성된 경량 가상 디바이스 |
| **VFIO** | Virtual Function I/O | Linux에서 디바이스를 VM에 직접 할당하는 프레임워크 |
| **VirtIO** | Virtual I/O | 게스트-호스트 간 표준화된 가상 I/O 인터페이스 |
| **DPDK** | Data Plane Development Kit | User-space에서 커널 bypass 패킷 처리 라이브러리 |
| **IOMMU** | IO Memory Management Unit | DMA 디바이스용 주소 변환/격리 HW |
| **SMMU** | System MMU | ARM 표준 IOMMU |

### 컨테이너

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **Container** | — | OS 커널 공유, 프로세스 수준 격리 (VM보다 경량) |
| **Namespace** | — | 프로세스 별 리소스 뷰 격리 (PID, Network, Mount 등) |
| **cgroup** | Control Group | 프로세스 그룹별 리소스 사용량 제한 |

---

## 컨셉 맵

```
                     ┌─────────────────────────────┐
                     │       Virtualization         │
                     └──────────┬──────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
    ┌─────▼─────┐        ┌─────▼─────┐        ┌─────▼─────┐
    │    CPU     │        │  Memory   │        │    I/O    │
    │Virtualization│      │Virtualization│     │Virtualization│
    └─────┬─────┘        └─────┬─────┘        └─────┬─────┘
          │                     │                     │
    ┌─────▼─────┐        ┌─────▼─────┐        ┌─────▼─────┐
    │Trap &     │        │Shadow PT  │        │Emulation  │
    │Emulate    │        │(SW)       │        │(SW)       │
    │           │        │           │        │           │
    │HW Assist  │        │2-Stage    │        │Paravirtual│
    │(VT-x,ARM) │       │Translation│        │(VirtIO)   │
    │           │        │(EPT/NPT)  │        │           │
    │           │        │           │        │Passthrough │
    │           │        │           │        │(SR-IOV,   │
    └───────────┘        └───────────┘        │VFIO,DPDK) │
                                              └───────────┘
                                                    │
                              ┌──────────────────────┤
                              │                      │
                      ┌───────▼───────┐     ┌───────▼───────┐
                      │Strict System  │     │Pass-through   │
                      │(모든 접근 중재) │     │System         │
                      │보안↑ 성능↓    │     │(HW 직접 접근)  │
                      │               │     │보안↓ 성능↑    │
                      └───────────────┘     └───────────────┘
```

---

## 유닛 구성

| Unit | 주제 | 핵심 질문 |
|------|------|----------|
| 01 | 가상화 기본 개념 | 왜 가상화가 필요하고, 어떤 문제를 해결하는가? |
| 01a | 시스템 아키텍처 진화 | HW only → 가상화까지, 각 단계에서 무엇이 추가되었고 왜? |
| 02 | CPU 가상화 | CPU 명령어를 어떻게 가상화하고, HW가 어떻게 지원하는가? |
| 03 | 메모리 가상화 | 2-stage translation은 왜 필요하고, 성능 영향은? |
| 04 | I/O 가상화 | I/O를 가상화하는 3가지 방식과 각각의 트레이드오프는? |
| 05 | Hypervisor 유형 | Type 1 vs Type 2의 차이, 실제 사례는? |
| 06 | Strict System vs Pass-through | 보안과 성능의 트레이드오프를 어떻게 해결하는가? |
| 07 | 컨테이너와 현대 가상화 | VM vs Container, 그리고 최신 트렌드는? |
| 08 | Quick Reference Card | 전체 요약 및 면접 대비 |

> Unit 01a는 DV TechForum #54 기반, Unit 06은 TechForum #55 기반.

---

## 이력서 연결 포인트

| 이력서 항목 | 관련 Unit | 면접 시 활용 |
|------------|----------|-------------|
| IOMMU/SMMU DV 경험 | Unit 01a, 04, 06 | IOMMU가 가상화의 전제 조건인 이유, AxUSER/StreamID 역할, DMA 격리 |
| HW 가속기용 MMU 검증 | Unit 03, 06 | 2-stage translation 25회 접근 오버헤드, Stage 2 locality 문제, Huge Page 최적화 |
| AXI 프로토콜 VIP 개발 | Unit 01a | AxUSER 신호가 IOMMU 2-stage에서 VM identity 제공하는 메커니즘 |
| 시스템 아키텍처 이해 | Unit 01, 01a | HW only → 가상화까지 진화 과정, Popek-Goldberg 조건과 HW 지원 |
| SR-IOV / PCIe DV | Unit 04, 06 | PF/VF 역할 차이, VirtIO vs Pass-through 트레이드오프 |
| 클라우드/서버 환경 지식 | Unit 05, 06, 07 | KVM/Xen 구조 차이, Nitro의 HW 기반 보안 모델, Firecracker 마이크로VM |
