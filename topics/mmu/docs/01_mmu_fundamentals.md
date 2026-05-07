# Unit 1: MMU 기본 개념 및 주소 변환

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

## 핵심 개념
**MMU = Virtual Address를 Physical Address로 변환하고, 접근 권한을 검사하는 HW 블록. 프로세스 격리, 메모리 보호, 물리 메모리 추상화의 핵심.**

---

## 왜 가상 주소가 필요한가?

### 가상 주소 없는 세계의 문제

```
물리 주소 직접 사용 시:

  Process A: 0x1000 ~ 0x2000 사용
  Process B: 0x1000 ~ 0x2000 사용 → 충돌!

  문제 1: 프로세스 간 주소 충돌
  문제 2: Process A가 Process B 메모리 직접 접근 가능 → 보안 위험
  문제 3: 물리 메모리 연속 배치 필요 → 메모리 단편화
  문제 4: 프로세스마다 사용 가능 메모리가 물리 크기에 제한
```

### 가상 주소가 해결하는 것

| 문제 | 가상 주소의 해결 |
|------|----------------|
| 주소 충돌 | 각 프로세스가 독립적 가상 주소 공간 보유 |
| 메모리 보호 | Page 단위 접근 권한 (R/W/X) 검사 |
| 메모리 단편화 | 가상으로 연속, 물리로 불연속 가능 |
| 메모리 크기 제한 | Swap으로 물리 메모리 이상의 공간 사용 가능 |
| 보안 격리 | Process A가 Process B의 물리 주소를 알 수 없음 |

---

## 주소 변환의 기본 원리

### Page 기반 변환

```
가상 주소 (예: 48-bit VA, 4KB Page)
+------------------+------------------+
|  Virtual Page No. |  Page Offset     |
|  (VPN, 36-bit)   |  (12-bit)        |
+--------+---------+--------+---------+
         |                   |
         v                   |
  +-------------+            |
  | Page Table  |            |
  | VPN → PPN   |            |  (Offset은 변환 없이 그대로)
  +------+------+            |
         |                   |
         v                   v
+------------------+------------------+
| Physical Page No.|  Page Offset     |
| (PPN)            |  (12-bit)        |
+------------------+------------------+
         물리 주소
```

**핵심**: VPN(Virtual Page Number)만 변환하고, Page Offset(하위 12bit)은 그대로 통과한다.

### Page 크기와 Offset 관계

| Page 크기 | Offset 비트 | 용도 |
|----------|-----------|------|
| 4 KB | 12 bit | 가장 일반적 (일반 OS) |
| 16 KB | 14 bit | ARM 일부 (iOS 등) |
| 64 KB | 16 bit | HPC, 대형 메모리 |
| 2 MB (Huge Page) | 21 bit | 대용량 연속 매핑 |
| 1 GB (Giga Page) | 30 bit | 서버, HW 가속기 |

**면접 포인트**: Page 크기가 클수록 TLB 하나의 엔트리가 커버하는 범위가 넓어져 TLB Miss가 줄어든다. 그러나 내부 단편화(Internal Fragmentation)가 증가한다.

---

## MMU의 핵심 기능 3가지

### 1. 주소 변환 (Address Translation)

```
VA → PA 매핑:
  VA 0x0000_1000 → PA 0x8000_1000  (Process A)
  VA 0x0000_1000 → PA 0xA000_1000  (Process B)
  → 같은 VA가 다른 PA로 매핑 가능 = 프로세스 격리
```

### 2. 접근 권한 검사 (Permission Check)

```
Page Table Entry (PTE)에 포함된 권한 비트:

  +---+---+---+-----+--------+-------+--------+
  | V | R | W | X   | User   | Global| Dirty  |
  +---+---+---+-----+--------+-------+--------+
  | 1 | 1 | 0 | 1   | 1      | 0     | 0      |
  +---+---+---+-----+--------+-------+--------+

  V = Valid (유효한 매핑 여부)
  R = Read 허용
  W = Write 허용
  X = Execute 허용
  User = User mode 접근 허용
  Global = 컨텍스트 스위치 시 TLB flush 제외

  위반 시 → Page Fault (Exception) 발생
```

### 3. 캐시 속성 제어 (Memory Attributes)

| 속성 | 의미 | 용도 |
|------|------|------|
| Cacheable | 캐시에 저장 가능 | 일반 DRAM |
| Non-cacheable | 캐시 우회 | MMIO, Device 레지스터 |
| Write-back | 캐시에 쓰고 나중에 메모리 반영 | 성능 우선 |
| Write-through | 캐시와 메모리에 동시 쓰기 | 일관성 우선 |
| Device | 순서 보장, 캐시 불가 | HW 레지스터 |

---

## MMU Enable / Disable

```
SCTLR_EL1.M (bit[0]) — MMU 활성화 제어:

  M = 0 (MMU Disabled):
    모든 VA가 그대로 PA로 통과 (Identity Mapping)
    TLB 사용 안 함, Page Walk 없음
    캐시 속성: 기본값 (Device-nGnRnE 또는 구현 정의)

    사용 시점:
    - 부트 초기 (OS 로드 전)
    - Firmware / Bootloader 단계
    - Page Table이 아직 설정되지 않은 상태

  M = 1 (MMU Enabled):
    모든 VA가 Page Table 기반으로 변환
    TLB 활성화, Page Walk Engine 동작

MMU 활성화 순서 (부트 시):
  1. Page Table 구성 (메모리에 PTE 배치)
  2. TTBR0_EL1 / TTBR1_EL1에 Table Base 주소 설정
  3. TCR_EL1에 VA 크기, Granule, 캐시 속성 설정
  4. MAIR_EL1에 메모리 속성 정의
  5. SCTLR_EL1.M = 1 (MMU Enable)
  6. ISB (파이프라인 플러시 — 이후 명령어부터 변환 적용)

주의: Enable 직후의 첫 명령어도 변환됨
→ Enable 전에 현재 실행 중인 코드 영역의 Identity Mapping 필수
   (VA = PA인 매핑이 있어야 Enable 후에도 실행 계속)
```

---

## Translation Regime — 누가, 어디서 변환하는가

```
ARMv8에서 Exception Level별 Translation Regime:

  +--------+------------------+-------------------+
  | EL     | Translation      | Page Table 관리   |
  +--------+------------------+-------------------+
  | EL0/1  | Stage 1:         | OS 커널            |
  |        | VA → PA (또는 IPA)|                   |
  +--------+------------------+-------------------+
  | EL2    | Stage 2:         | Hypervisor         |
  |        | IPA → PA         |                    |
  |        | (가상화 시)       |                    |
  +--------+------------------+-------------------+
  | EL3    | Secure Monitor   | Secure Firmware    |
  |        | (별도 Translation)|                   |
  +--------+------------------+-------------------+

핵심:
  - EL0 (User) + EL1 (Kernel): 같은 Stage 1 Translation 공유
    → TTBR0_EL1 = User 공간, TTBR1_EL1 = Kernel 공간
  - EL2 (Hypervisor): Guest OS의 IPA를 실제 PA로 변환
  - 각 Regime은 독립적인 Page Table + TLB 공간을 가짐
```

---

## Secure vs Non-secure — TrustZone과 MMU

```
ARM TrustZone: Secure World와 Normal World 분리

  +---Normal World---+     +---Secure World---+
  | Normal OS        |     | Trusted OS       |
  | (Android/Linux)  |     | (OP-TEE 등)      |
  |                  |     |                  |
  | Normal MMU       |     | Secure MMU       |
  | (TTBR_EL1)      |     | (TTBR_EL1_S)    |
  +------------------+     +------------------+

  물리 주소 공간도 분리:
  - NS (Non-Secure) 비트: PTE[5]
  - NS=0 → Secure 물리 메모리 접근 가능
  - NS=1 → Non-secure 물리 메모리만 접근 가능

  보안 경계:
  - Normal World에서 Secure 메모리 접근 시도 → Bus Error / Slave Error
  - TrustZone Address Space Controller (TZASC)가 물리 주소 수준에서 차단

DV 관점:
  - Secure → Non-secure 전환 시 TLB 상태 관리 검증
  - NS bit가 잘못 설정된 PTE로 Secure 메모리 접근 시도 → 차단 확인
  - World 전환 시 TLB Flush 범위 검증 (Secure TLB와 Normal TLB 독립성)
```

---

## MMU가 SoC에서 위치하는 곳

```
+------------------------------------------------------------------+
|                           SoC                                     |
|                                                                   |
|  +-------+    +-----+                                             |
|  | CPU   +--->| MMU +---> Memory Controller ---> DRAM             |
|  +-------+    +-----+                                             |
|                                                                   |
|  +--------+   +-------+                                           |
|  | GPU    +-->| SMMU  +---> Memory Controller ---> DRAM           |
|  +--------+   +-------+                                           |
|                                                                   |
|  +--------+   +-------+                                           |
|  | DMA    +-->| IOMMU +---> Memory Controller ---> DRAM           |
|  +--------+   +-------+                                           |
|                                                                   |
|  +--------+   +-------+                                           |
|  | NIC/   +-->| sysMMU+---> Memory Controller ---> DRAM           |
|  | Accel  |   +-------+                                           |
|  +--------+                                                       |
+------------------------------------------------------------------+

CPU → MMU (CPU 전용, 보통 CPU 내부)
GPU/DMA/가속기 → SMMU / IOMMU / sysMMU (디바이스용)
```

**SoC에서 MMU가 중요한 이유**: HW 가속기(NPU, GPU, DMA)가 직접 메모리에 접근할 때, 가상 주소를 사용해야 OS의 메모리 관리 체계와 일관성을 유지하고, 잘못된 접근으로부터 시스템을 보호할 수 있다.

---

## CPU MMU vs IOMMU/SMMU 비교

| 항목 | CPU MMU | IOMMU / SMMU |
|------|---------|-------------|
| 위치 | CPU 내부 | Bus Fabric / 독립 IP |
| 사용자 | CPU 코어 | GPU, DMA, NIC, 가속기 |
| Page Table 관리 | OS 커널 | OS 커널 (IOMMU 드라이버) |
| 주요 목적 | 프로세스 격리 | 디바이스 격리 + DMA 보호 |
| TLB | CPU 전용 TLB | IOTLB (디바이스용) |
| 성능 요구 | 매우 높음 (매 명령어마다) | 높음 (DMA 트래픽 의존) |
| 가상화 지원 | Stage 2 (EL2) | Stage 2 (Hypervisor) |

---

## Page Fault — 변환 실패 처리

### Page Fault 유형

| 유형 | 원인 | 처리 |
|------|------|------|
| Invalid (매핑 없음) | PTE의 Valid 비트 = 0 | OS가 페이지 할당 후 매핑 |
| Permission (권한 위반) | Write 시도 but W=0 | Segfault 또는 COW (Copy-on-Write) |
| Not Present (스왑) | 물리 메모리에 없음 (디스크로 스왑됨) | 디스크에서 읽어 복원 |

### Page Fault 처리 흐름

```
1. CPU가 VA 접근 시도
2. MMU: TLB Miss → Page Walk → PTE 없거나 권한 위반
3. MMU → CPU에 Page Fault Exception 전달
4. CPU: OS의 Page Fault Handler 호출
5. Handler: 원인 분석 → 페이지 할당/로드/권한 업데이트
6. Handler 완료 → CPU가 원래 명령어 재실행
7. MMU: 이번에는 정상 변환 성공
```

**DV 관점**: Page Fault 발생 → Exception → Handler → 재실행의 전체 흐름이 올바르게 동작하는지, 특히 Fault 발생 시 MMU 상태(TLB, Page Walk Engine)가 정확히 유지되는지 검증해야 한다.

---

## Q&A

**Q: MMU의 핵심 기능 3가지는?**
> "주소 변환(VA→PA), 접근 권한 검사(R/W/X, User/Kernel), 캐시 속성 제어(Cacheable/Device). 주소 변환은 Page 단위로 수행되며, VPN만 변환하고 Offset은 그대로 통과한다."

**Q: 왜 가상 메모리가 필요한가?**
> "다섯 가지 이유: (1) 프로세스 격리 — 각 프로세스가 독립적 주소 공간. (2) 메모리 보호 — Page 단위 권한 검사. (3) 단편화 해결 — 가상 연속, 물리 불연속 가능. (4) 물리 크기 초과 사용 — Swap 활용. (5) 보안 — Process A가 B의 물리 주소를 알 수 없음."

**Q: Huge Page의 장단점은?**
> "장점: TLB 엔트리 하나가 커버하는 범위가 넓어져(2MB vs 4KB) TLB Miss가 크게 줄어든다. 서버, HW 가속기처럼 대용량 연속 메모리를 사용하는 경우 성능이 크게 향상된다. 단점: 내부 단편화 — 2MB 중 일부만 사용해도 2MB 전체를 할당해야 한다. 메모리 효율이 떨어질 수 있다."

**Q: MMU Enable 시 주의할 점은?**
> "Enable 직후의 첫 명령어부터 주소 변환이 적용되므로, Enable 전에 현재 실행 중인 코드 영역에 Identity Mapping(VA=PA)이 반드시 있어야 한다. 순서는: Page Table 구성 → TTBR 설정 → TCR/MAIR 설정 → SCTLR.M=1 → ISB(파이프라인 플러시). ISB가 없으면 파이프라인의 이전 명령어가 변환 없이 실행될 수 있다."

**Q: TrustZone 환경에서 MMU의 역할은?**
> "Secure World와 Normal World 각각이 독립적인 Translation Regime을 가진다. PTE의 NS 비트로 Secure/Non-secure 물리 메모리를 구분하며, Normal World에서 Secure 메모리 접근 시도 시 Bus Error로 차단된다. World 전환 시 TLB 관리가 중요한데, Secure TLB와 Normal TLB가 독립적으로 관리되어야 stale 엔트리로 인한 보안 누출을 방지할 수 있다."

---

!!! warning "실무 주의점 — MMU Enable 직후 ISB 누락"
    **현상**: MMU Enable(SCTLR.M=1) 직후 Instruction Fetch가 stale 변환 주소로 실행되어 예기치 않은 Fault 또는 오동작 발생.
    
    **원인**: 파이프라인에 이미 페치된 명령어들이 SCTLR 업데이트 이전 상태로 실행됨. ISB를 삽입하지 않으면 컴파일러/CPU가 명령어 순서를 재배치하여 변환이 활성화되기 전 코드가 실행될 수 있음.
    
    **점검 포인트**: 부트 코드에서 `SCTLR_EL1.M = 1` 설정 직후 `ISB` 명령어 존재 여부 확인. 시뮬레이션 로그에서 MMU Enable 시점 이후 첫 번째 Translation Fault가 Enable 이전 VA 범위를 참조하면 ISB 누락 의심.

## 핵심 정리

- **VA의 3가지 동기**: Process isolation / Memory efficiency (CoW, demand paging) / Fragmentation 해결.
- **VA→PA 변환은 page table walk + TLB caching**: TLB hit이면 1 cycle, miss면 page walk N cycle (N = level 깊이).
- **MMU 위치**: CPU 내장 (Core 단위) vs SoC 레벨 IOMMU/SMMU (DMA 마스터들 보호).
- **PTE 핵심 필드**: PFN(Physical Frame Number) / V(valid) / R/W / U/S(user/supervisor) / ASID / dirty / access.
- **MMU enable 순서**: Page Table 구성 → TTBR 설정 → TCR/MAIR → SCTLR.M=1 → ISB. ISB 누락 시 파이프라인 잔여 명령이 untranslated 실행.

## 다음 단계

- 📝 [**Module 01 퀴즈**](quiz/01_mmu_fundamentals_quiz.md)
- ➡️ [**Module 02 — Page Table Structure**](02_page_table_structure.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">코스 홈</div>
  </a>
  <a class="nav-next" href="../02_page_table_structure/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Page Table 구조</div>
  </a>
</div>
