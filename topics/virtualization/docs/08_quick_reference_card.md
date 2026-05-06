# Unit 8: Quick Reference Card

## 시스템 아키텍처 진화 (TechForum #54)

```
HW Only → Processor(FW) → +HW Accel → +OS(ARM-M)+MPU → +MMU(ARM-A) → +IOMMU+PEs+LLC → Virtualization
 고정      프로그래머블     하이브리드    자원 관리        가상 주소      확장 가능         VM 격리
 기능      저성능          고성능        메모리 보호       범용 OS       디바이스 격리      HW 지원
```

| 전환점 | 추가된 것 | 해결한 문제 |
|--------|---------|-----------|
| 1→2 | Processor | 프로그래밍 유연성 |
| 2→3 | HW Accelerator | 연산 성능 |
| 3→4 | OS, MPU, DRAM | 자원 관리, 메모리 보호 |
| 4→5 | MMU, Cache (ARM-A) | 가상 주소, 범용 OS |
| **5→6** | **IOMMU**, PEs, LLC, Coherency | **디바이스 격리 — 가상화의 전제 조건** |
| 6→7 | Hypervisor, PF/VF, 2-stage | VM 격리 + 성능 유지 |

---

## 가상화 한 장 요약

```
                    가상화 = HW 추상화 + 자원 분할 + 격리
                    
┌─────────────────────────────────────────────────────────────┐
│                    3대 가상화 요소                             │
├──────────────────┬──────────────────┬───────────────────────┤
│   CPU 가상화      │  메모리 가상화    │   I/O 가상화           │
├──────────────────┼──────────────────┼───────────────────────┤
│ Trap & Emulate   │ Shadow PT (SW)   │ Emulation (SW)        │
│ Binary Trans.(SW)│ 2-Stage (HW)     │ VirtIO (준가상화)      │
│ VT-x / ARM EL2  │ EPT / Stage 1+2  │ Pass-through (HW)     │
│ (HW)            │                  │ SR-IOV                │
└──────────────────┴──────────────────┴───────────────────────┘
```

---

## ARM Exception Level

```
EL0 ─── User App      ──── SVC ────┐
                                     ▼
EL1 ─── Guest OS      ──── HVC ────┐
                                     ▼
EL2 ─── Hypervisor     ──── SMC ────┐
                                     ▼
EL3 ─── Secure Monitor (TrustZone)
```

---

## 주소 변환 경로

```
Bare Metal:  VA ──[1-Stage]──> PA              (최대 5회 메모리 접근)
가상화:      VA ──[Stage1]──> IPA ──[Stage2]──> PA  (최대 25회 메모리 접근)
```

| 단계 | 관리 | 최적화 |
|------|------|--------|
| Stage 1 (VA→IPA) | Guest OS (EL1) | 가능 (prefetch, 캐시) |
| Stage 2 (IPA→PA) | Hypervisor (EL2) | 어려움 (낮은 locality) — **핵심 병목** |

---

## I/O 가상화 스펙트럼

```
성능   낮음 ◄──────────────────────────────────────► 높음
격리   높음 ◄──────────────────────────────────────► 낮음

  Emulation      VirtIO        SR-IOV      Pass-through
  (10~30%)      (50~80%)      (90~98%)     (95~100%)
  수정 불필요    드라이버 필요   HW 필요      1:1 전용
  공유 가능      공유 가능      VF 공유      공유 불가
```

---

## Hypervisor 유형

| | Type 1 (Bare Metal) | Type 2 (Hosted) | KVM (하이브리드) |
|--|---------------------|-----------------|-----------------|
| 구조 | HW → Hypervisor → VM | HW → Host OS → Hypervisor → VM | HW → Linux+KVM → VM |
| 예시 | ESXi, Xen, Hyper-V | VirtualBox, VMware Workstation | KVM + QEMU |
| 용도 | 프로덕션 서버 | 개발/데스크탑 | 클라우드 (범용) |

---

## Strict System vs Pass-through

| | Strict | Pass-through |
|--|--------|-------------|
| 원칙 | 모든 HW 접근 Hypervisor 경유 | 특정 디바이스에 VM 직접 접근 |
| Context Switch | 4회/I/O (EL0↔EL1↔EL2) | 2회/I/O (EL0↔EL1) |
| 메모리 | 2-stage 전체 적용 | Huge Page로 최소화 |
| 보안 | SW 중재 (강함) | HW 격리 (IOMMU 의존) |
| 성능 | 오버헤드 큼 | Bare metal 수준 |

---

## VM vs Container vs MicroVM

| | VM | Container | MicroVM |
|--|-----|-----------|---------|
| 격리 | HW (Hypervisor) | OS (Namespace) | HW (KVM) |
| 부팅 | 초~분 | ms~초 | ~125ms |
| 크기 | GB | MB | ~5MB overhead |
| 보안 | 강함 | 커널 공유 위험 | 강함 |
| 밀도 | 수십/서버 | 수천/서버 | 수천/서버 |
| 용도 | 범용 서버 | 마이크로서비스 | FaaS/서버리스 |

---

## 관련 기술 약어 정리

| 약어 | 풀네임 | 한 줄 설명 |
|------|--------|-----------|
| VM | Virtual Machine | HW 추상화된 가상 컴퓨터 |
| VMM | Virtual Machine Monitor | = Hypervisor |
| VT-x | Virtualization Technology for x86 | Intel CPU 가상화 HW 지원 |
| AMD-V | AMD Virtualization | AMD CPU 가상화 HW 지원 |
| EPT | Extended Page Table | Intel 2-stage translation HW |
| NPT | Nested Page Table | AMD 2-stage translation HW |
| VHE | Virtualization Host Extensions | ARM v8.1+, Host OS가 EL2에서 실행 |
| VMCS | VM Control Structure | VT-x에서 VM 상태 저장 구조체 |
| SR-IOV | Single Root I/O Virtualization | PCIe 디바이스를 VF로 분할 |
| PF | Physical Function | SR-IOV 물리 기능 (전체 관리) |
| VF | Virtual Function | SR-IOV 가상 기능 (경량, VM 할당) |
| VFIO | Virtual Function I/O | Linux 디바이스 pass-through 프레임워크 |
| VirtIO | Virtual I/O | 준가상화 I/O 표준 인터페이스 |
| DPDK | Data Plane Development Kit | 커널 bypass 고성능 패킷 처리 |
| IOMMU | IO MMU | DMA 주소 변환/격리 HW |
| SMMU | System MMU | ARM 표준 IOMMU |
| HPA | Huge Page Area | 대형 페이지 할당 영역 |
| IPA | Intermediate Physical Address | 가상화 중간 물리 주소 |
| KVM | Kernel-based Virtual Machine | Linux 커널 내장 하이퍼바이저 |
| QEMU | Quick Emulator | 오픈소스 에뮬레이터/가상화 |

---

## 성능 최적화 체크리스트

```
□ CPU: HW 가상화 활성화 (VT-x/AMD-V/ARM EL2)
□ CPU: VM Exit 횟수 최소화 (불필요한 trap 제거)
□ Memory: EPT/Stage 2 HW 지원 활성화
□ Memory: Huge Page 사용 (TLB miss 감소)
□ Memory: NUMA-aware 메모리 할당
□ I/O 일반: VirtIO 드라이버 사용 (에뮬레이션 대신)
□ I/O 고성능: SR-IOV VF 할당 (네트워크)
□ I/O 고성능: VFIO pass-through (GPU, NVMe)
□ I/O 극한: DPDK + Huge Page + CPU pinning
□ 인터럽트: Posted Interrupt 활성화
□ CPU pinning: vCPU를 물리 코어에 고정 (NUMA 로컬)
```

---

## 면접 골든 룰

1. **3대 요소**: "CPU, Memory, I/O 가상화 — 모두 SW→HW 지원 진화" 흐름으로 답하라
2. **Popek-Goldberg**: "동등성, 자원 제어, 효율성 — 효율성이 실용적 핵심 제약"
3. **25회 접근**: "5(Stage1 참조) × 5(각각 Stage2 walk) — TLB/PWC로 실제는 훨씬 적다"
4. **Shadow PT vs 2-Stage**: "변환 자체는 Shadow가 빠르지만 VM Exit 오버헤드가 상쇄"
5. **VirtIO**: "Virtqueue batching으로 VM Exit을 I/O 수와 무관하게 일정"
6. **SR-IOV**: "PF = 관리, VF = 데이터 경로 — NIC 1개로 128 VM 지원"
7. **IOMMU**: "디바이스용 MMU — DMA 격리 + 주소 변환 + 가상화 전제 조건" 세 가지를 말하라
8. **KVM 분류**: "구조적 Type 2, 성능 Type 1, VHE 이후 구분 무의미"
9. **Strict vs Pass-through**: "context switch 4회 vs 2회 — HW 보안(IOMMU)이 전제"
10. **Firecracker**: "125ms 부팅 + KVM 격리 + 5MB 오버헤드 — 서버리스의 해법"
11. **트레이드오프**: 성능 vs 격리, 공유 vs 전용 — 항상 양면을 함께 언급하라

---

## 흔한 실수와 올바른 답변

| 실수 | 왜 위험한가 | 올바른 답변 |
|------|-----------|-----------|
| "가상화는 성능 손해만" | 자원 활용률 향상 무시 | "오버헤드 있지만 활용률 10%→60~80%로 향상, HW 지원으로 오버헤드 최소화" |
| "Shadow PT가 더 좋다" | VM Exit 오버헤드 무시 | "변환 자체는 빠르지만 PT 수정마다 VM Exit — 멀티프로세스에서 2-Stage가 유리" |
| "IOMMU는 보안용이다" | 주소 변환/가상화 전제 역할 누락 | "보안 + 주소 변환 + DMA 격리 + 가상화 필수 전제 조건" |
| "컨테이너가 VM보다 좋다" | 보안 트레이드오프 무시 | "속도/밀도는 컨테이너가 우수, 격리/보안은 VM이 우수 — 용도에 따라 선택" |
| "Pass-through는 보안 약화" | HW 기반 보안 무시 | "IOMMU + Nitro Card 등 HW 격리로 보안 유지하면서 pass-through 성능 확보" |
| "VT-x 이전에는 가상화 불가" | Binary Translation 무시 | "BT로 SW 우회 가능했으나 복잡/느림 — VT-x가 HW로 근본 해결" |
| "KVM은 Type 2이다" | 하이브리드 특성 무시 | "구조적 Type 2지만 Linux=Hypervisor, VHE 이후 Type 1과 사실상 동일" |

---

## 이력서 연결 포인트

| 이력서 항목 | 면접 질문 | 핵심 답변 포인트 |
|------------|----------|----------------|
| IOMMU/SMMU DV | "IOMMU가 가상화에서 왜 중요한가?" | DMA 격리 = 가상화 전제 조건, AxUSER→StreamID로 VM identity, 2-stage translation |
| HW 가속기용 MMU | "메모리 가상화의 성능 병목은?" | 25회 최악 접근, Stage 2 locality 낮음, Huge Page + PWC로 완화 |
| AXI VIP 개발 | "AxUSER가 하는 역할은?" | 디바이스 트랜잭션에 VM 정체성 부여, IOMMU가 올바른 PT 선택하는 키 |
| SR-IOV/PCIe DV | "SR-IOV를 검증한 경험은?" | PF/VF 분리, VF 생성/할당/격리, IOMMU와의 연동 |
| 시스템 아키텍처 | "가상화가 필요한 이유는?" | 활용률 10%→60~80%, 격리, 스냅샷/마이그레이션 — Popek-Goldberg 3조건 |
| 클라우드/서버 | "클라우드 가상화 트렌드는?" | SW 중재→HW 보안(IOMMU, Nitro), Pass-through + HW 격리, MicroVM |

---

## 면접 스토리 흐름 (가상화 지식 활용)

```
1. 배경 — 왜 가상화를 알아야 하는가
   "HW 가속기에 IOMMU/SMMU가 필수 → 가상화 환경에서의 디바이스 격리/성능 검증"

2. 기술 깊이 — 핵심 메커니즘
   "2-stage translation(25회 접근), AxUSER→StreamID, IOMMU의 DMA 격리"
   "Strict vs Pass-through — context switch 4회 vs 2회, IOMMU가 보안 전제"

3. 실무 연결 — DV 관점
   "IOMMU 검증: VM별 메모리 격리, DMA fault injection, 2-stage walk 정확성"
   "성능 검증: TLB miss ratio, Stage 2 오버헤드 측정"

4. 트렌드 인식 — 현대 방향
   "AWS Nitro 모델: HW 보안 + Pass-through 성능, Firecracker MicroVM"
   "DPU 오프로드: 네트워크/스토리지 가상화를 전용 HW로 → 검증 대상 확대"
```
