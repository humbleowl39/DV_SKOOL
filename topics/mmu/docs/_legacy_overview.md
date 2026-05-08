# MMU (Memory Management Unit) — 개요 및 컨셉 맵

## 학습 플랜
- **레벨**: Intermediate → Advanced (MMU IP Lead 실무 경험 기반, 체계적 정리 + 면접 대비)
- **목표**: MMU 내부 동작을 화이트보드에 그리며, 성능 분석과 DV 검증 전략까지 논리적으로 전개할 수 있는 수준

## 핵심 용어집 (Glossary)

### 주소 변환

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **MMU** | Memory Management Unit | 가상 주소(VA)를 물리 주소(PA)로 변환하는 HW |
| **VA** | Virtual Address | CPU/디바이스가 사용하는 가상 주소 |
| **PA** | Physical Address | 실제 메모리(DRAM) 접근 주소 |
| **IPA** | Intermediate Physical Address | 가상화 환경의 중간 주소 (Stage 1 결과, Stage 2 입력) |
| **PT** | Page Table | VA→PA 매핑 정보를 저장하는 메모리 내 계층 구조 |
| **PTE** | Page Table Entry | 한 페이지의 변환 정보 (PPN + 권한 + 캐시 속성) |
| **TLB** | Translation Lookaside Buffer | 주소 변환 결과를 캐싱하는 고속 HW 캐시 (Hit: 1 cycle) |
| **PWC** | Page Walk Cache | 페이지 워크 중간 레벨 PTE를 캐싱하여 메모리 접근 횟수 감소 |

### 식별자 & 태그

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **ASID** | Address Space Identifier | 프로세스별 TLB 엔트리 태그 (컨텍스트 스위치 시 Flush 회피) |
| **VMID** | Virtual Machine Identifier | VM별 TLB 엔트리 태그 |
| **VPN** | Virtual Page Number | VA의 상위 비트 (변환 대상) |
| **PPN** | Physical Page Number | PA의 상위 비트 (변환 결과) |

### 권한 & 속성

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **AP** | Access Permission | PTE 필드: RO/RW × EL0/EL1 조합 |
| **XN** | eXecute Never | 1이면 해당 페이지에서 명령어 실행 금지 |
| **SH** | Shareability | 멀티코어 캐시 일관성 범위 (Inner/Outer/Non) |
| **AF** | Access Flag | 페이지 접근 여부 기록 (OS 페이지 교체 정책 지원) |
| **MAIR** | Memory Attribute Indirection Register | 캐시 속성(WB/WT/Device) 인덱스의 실제 의미 정의 |

### IOMMU / SMMU

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **IOMMU** | IO Memory Management Unit | GPU/DMA 같은 디바이스용 MMU (일반 명칭) |
| **SMMU** | System MMU | ARM 표준 IOMMU (StreamID 기반 디바이스 격리) |
| **IOTLB** | IO TLB | IOMMU 전용 TLB (CPU TLB와 독립) |
| **StreamID** | — | SMMU에서 DMA Master를 식별하는 ID |
| **STE** | Stream Table Entry | 디바이스별 변환 설정 엔트리 |
| **CD** | Context Descriptor | 프로세스별 Page Table 포인터 |

### 핵심 레지스터

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **TTBR** | Translation Table Base Register | Page Table 최상위 테이블의 물리 주소 |
| **TCR** | Translation Control Register | VA 크기, Granule, 캐시 속성 제어 |
| **SCTLR** | System Control Register | MMU Enable/Disable (M 비트) |

### 성능 & 장애

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **PF** | Page Fault | 매핑 없음/권한 위반/스왑 페이지 등으로 인한 예외 |
| **Huge Page** | — | 큰 페이지 (2MB/1GB)로 TLB 효율 향상 (내부 단편화 증가) |
| **COW** | Copy-on-Write | fork() 후 Write 시에만 물리 페이지를 복사하는 최적화 |
| **ISB/DSB** | Instruction/Data Synchronization Barrier | 파이프라인 플러시/메모리 연산 완료 보장 |
| **DMA** | Direct Memory Access | CPU 개입 없이 디바이스가 메모리에 직접 접근 |

---

## 컨셉 맵

```
              +--------------------+
              |  Virtual Address   |
              |  (CPU / Device)    |
              +---------+----------+
                        |
          +-------------+-------------+
          |           MMU             |
          |                           |
          |  +-------+  +---------+  |
          |  |  TLB  |  |Page Walk|  |
          |  |(Cache) |  | Engine  |  |
          |  +---+---+  +----+----+  |
          |      |            |       |
          |   Hit?         Miss →     |
          |      |       Page Table   |
          |      |       Traversal    |
          +------+-------+----+------+
                 |             |
          +------+------+     |
          |   결과 합류  |<----+
          +------+------+
                 |
          +------+------+
          | Physical Addr|
          | + 권한 체크   |
          +------+------+
                 |
      +----------+----------+
      |                     |
  +---+---+            +----+----+
  | Memory |            | Fault   |
  | Access |            | Handler |
  +--------+            +---------+
```

## 학습 단위 (Units)

| # | 단위 | 핵심 질문 |
|---|------|----------|
| 1 | **MMU 기본 개념 및 주소 변환** | 왜 가상 주소가 필요하고, MMU가 어떻게 변환하는가? |
| 2 | **Page Table 구조** | Multi-level Page Table은 어떻게 동작하고, 왜 계층화하는가? |
| 3 | **TLB (Translation Lookaside Buffer)** | 주소 변환 캐시는 어떻게 성능에 영향을 주는가? |
| 4 | **IOMMU / SMMU — SoC에서의 MMU** | 디바이스의 메모리 접근을 왜/어떻게 관리하는가? |
| 5 | **MMU 성능 분석 및 최적화** | TLB Miss Ratio, Latency, Throughput을 어떻게 분석하는가? |
| 6 | **MMU DV 검증 방법론** | UVM 기반으로 MMU를 어떻게 검증하고, 성능까지 검증하는가? |

## 이력서 연결 포인트

| 이력서 항목 | 관련 Unit | 면접 시 활용 |
|------------|----------|-------------|
| Custom "Thin" VIP (AXI-S) | Unit 6 | 상용 VIP 메모리 문제 → 경량화 전략 |
| Dual-Reference Model | Unit 5, 6 | Functional Model + Ideal Performance Model |
| TLB Miss Ratio 분석 | Unit 3, 5 | 성능 병목 발견 → 마이크로아키텍처 분석 |
| AI-Assisted 환경 자동화 | Unit 6 | 스펙 변경 대응 → DAC 2026 제출 |
| TLB 서브모듈 + MMU Top End-to-End | Unit 3, 6 | 계층적 검증 전략 (서브모듈 → Top) |
| Server-grade 성능 요구사항 | Unit 5 | HW 가속기용 MMU 처리량 검증 |


--8<-- "abbreviations.md"
