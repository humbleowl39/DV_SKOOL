# Module 03 — TLB

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Diagram** TLB의 구조(set-associative, fully associative, micro-TLB / L1 / L2)와 동작을 그릴 수 있다.
    - **Trace** TLB hit / TLB miss / page walk 흐름과 각 경우의 latency 영향을 추적할 수 있다.
    - **Apply** ASID/VMID tagging이 어떻게 process/VM 간 TLB sharing을 가능하게 하는지 시나리오에 적용할 수 있다.
    - **Decide** 언제 TLB invalidate (TLBI), shootdown이 필요한지 식별할 수 있다.
    - **Distinguish** HW-managed TLB (ARM/x86)와 SW-managed TLB (MIPS) 차이를 설명할 수 있다.

!!! info "사전 지식"
    - [Module 01-02](01_mmu_fundamentals.md) (VA→PA, multi-level walk)
    - 캐시 기본 (associativity, replacement policy)

## 왜 이 모듈이 중요한가

**TLB는 MMU 성능의 90%를 결정**합니다. Page walk이 100+ cycle이면 TLB hit는 1 cycle. **Stale TLB entry는 silent correctness bug**의 흔한 원인 — page table 업데이트 후 invalidate 누락 시 잘못된 PA에 access. 검증에서는 TLB invalidation 시나리오를 빠짐없이 다루는 것이 핵심.

## 핵심 개념
**TLB = 주소 변환 결과(VPN→PPN)를 캐싱하는 고속 하드웨어 캐시. Page Walk의 수백 배 지연을 1사이클로 줄여주는, MMU 성능의 핵심 컴포넌트.**

---

## TLB가 필요한 이유

```
Page Walk 없이 (TLB Hit):
  VA → [TLB: 1 cycle] → PA → 메모리 접근
  총: ~1 cycle + 메모리 접근 시간

Page Walk 필요 (TLB Miss):
  VA → [TLB Miss] → [Level 0: ~100ns] → [Level 1: ~100ns]
    → [Level 2: ~100ns] → [Level 3: ~100ns] → PA
  총: ~400 ns + 메모리 접근 시간

  TLB Hit  ≈ 0.5 ns
  TLB Miss ≈ 400 ns
  → 800배 차이!

  따라서 TLB Miss Ratio 1%만 되어도 성능에 상당한 영향
```

### Effective Memory Access Time 계산

```
T_eff = TLB_Hit_Rate × T_hit + TLB_Miss_Rate × T_miss

예시 (4-level, DDR4):
  T_hit  = 0.5 ns (1 cycle @ 2GHz)
  T_miss = 400 ns (4 × 100ns page walk)

  Hit Rate 99%:  0.99 × 0.5 + 0.01 × 400 = 0.495 + 4.0 = 4.5 ns
  Hit Rate 95%:  0.95 × 0.5 + 0.05 × 400 = 0.475 + 20  = 20.5 ns
  Hit Rate 90%:  0.90 × 0.5 + 0.10 × 400 = 0.45  + 40  = 40.5 ns

  → 99% vs 95%: 4.6배 차이
  → 99% vs 90%: 9배 차이
  → 1%의 Miss Rate 변화가 전체 성능에 막대한 영향
```

---

## TLB 구조

### 기본 TLB 엔트리

```
+------+------+------+------+----+----+----+----+------+-------+
| VMID | ASID | VPN  | PPN  | V  | R  | W  | X  | Attr | Size  |
+------+------+------+------+----+----+----+----+------+-------+
|  3   |  5   | 0x1F | 0x8A | 1  | 1  | 1  | 0  | WB   | 4KB   |
+------+------+------+------+----+----+----+----+------+-------+

V    = Valid
R/W/X = 권한 (Page Table에서 복사)
Attr = 캐시 속성
Size = Page 크기 (4KB/2MB/1GB)
```

### TLB Lookup 과정

```
입력: VMID + ASID + VA

1. VA에서 VPN 추출
2. TLB 전체(Full-associative) 또는 Set(Set-associative)에서 검색:
   - VMID 일치?
   - ASID 일치? (또는 Global 엔트리?)
   - VPN 일치? (Page 크기 고려한 마스킹)
3. 일치하는 Valid 엔트리 발견?
   → Hit:  PPN + 권한 + 속성 즉시 반환
   → Miss: Page Walk Engine에 요청
```

---

## TLB 계층 구조

### 일반적인 2-Level TLB

```
+-------+     +--------+     +-----------+
| L1 TLB| --> | L2 TLB | --> | Page Walk |
| (μTLB)|     | (Main) |     | Engine    |
+-------+     +--------+     +-----------+

L1 TLB (μTLB):
  - 크기: 32~64 엔트리
  - 구조: Fully-associative
  - 속도: 1 cycle
  - 역할: 가장 빈번한 매핑 캐시

L2 TLB (Main TLB):
  - 크기: 256~2048 엔트리
  - 구조: Set-associative (4~8 way)
  - 속도: 2~4 cycle
  - 역할: L1 Miss 시 백업

Page Walk Engine:
  - L2 Miss 시 메모리에서 Page Table 읽기
  - 결과를 L1, L2에 모두 캐싱
```

### IOTLB (IOMMU/SMMU용)

```
디바이스(GPU, DMA, NIC)의 주소 변환용 TLB:

  +--------+     +--------+     +-----------+
  | Device | --> | IOTLB  | --> | Page Walk |
  | Request|     |        |     | (메모리)  |
  +--------+     +--------+     +-----------+

  특징:
  - StreamID (Device ID)로 디바이스별 구분
  - SubstreamID (PASID)로 프로세스별 구분
  - 디바이스 트래픽 패턴이 CPU와 다름:
    → DMA: 대용량 순차 접근 → Huge Page가 효과적
    → GPU: 불규칙 접근 패턴 → TLB 크기가 중요
```

---

## TLB 설계 — Split vs Unified

```
방식 1: Split TLB (Instruction + Data 분리)
  +--------+     +--------+
  | I-TLB  |     | D-TLB  |     ← L1: 명령어/데이터 독립 접근
  | (48 ent)|     | (64 ent)|
  +----+---+     +----+---+
       |              |
       +------+-------+
              |
         +----+----+
         | L2 TLB  |              ← L2: 통합 (Unified)
         | (1024)  |
         +---------+

  장점: I-Fetch와 D-Access가 동시에 TLB 접근 가능 (병렬성)
  단점: 한쪽만 사용하면 다른 쪽 엔트리 낭비

방식 2: Unified TLB
  +-------------------+
  | Unified TLB       |          ← 명령어/데이터 구분 없이 공유
  | (112 entries)     |
  +-------------------+

  장점: 엔트리 활용 효율 높음
  단점: 동시 접근 시 경쟁 (arbitration 필요)

실무: 대부분 L1 = Split, L2 = Unified 조합 사용
→ DV에서 I-TLB/D-TLB 동시 접근 시나리오 검증 필수
```

---

## TLB 교체 정책 (Replacement Policy)

| 정책 | 원리 | 장단점 |
|------|------|--------|
| LRU (Least Recently Used) | 가장 오래 사용되지 않은 엔트리 교체 | 정확하지만 HW 복잡 |
| Pseudo-LRU | 트리 기반 근사 LRU | HW 간단, 성능 근접 |
| Random | 랜덤 선택 | 가장 간단, 최악 케이스 없음 |
| FIFO | 가장 먼저 들어온 엔트리 교체 | 간단하지만 성능 낮음 |

### Pseudo-LRU 알고리즘 상세 (Tree-based PLRU)

```
4-way Set-Associative TLB의 Pseudo-LRU 예시:

  이진 트리 구조 (3개의 방향 비트):
            B0
           /    \
         B1      B2
        /  \    /  \
      Way0 Way1 Way2 Way3

  비트 의미:
    B0 = 0 → 좌측 방향(Way0/1)이 최근 사용됨 → 교체 대상은 우측(Way2/3)
    B0 = 1 → 우측 방향(Way2/3)이 최근 사용됨 → 교체 대상은 좌측(Way0/1)
    B1, B2도 동일 논리

  접근 시 업데이트:
    Way1 접근 → B0 = 0 (좌측 사용), B1 = 1 (Way1 방향)

  교체 대상 결정:
    B0=0 → 우측으로, B2=0 → Way2 선택
    B0=0 → 우측으로, B2=1 → Way3 선택
    B0=1 → 좌측으로, B1=0 → Way0 선택
    B0=1 → 좌측으로, B1=1 → Way1 선택

  HW 구현:
    - 비트 수 = (Way 수 - 1) = 3비트 (4-way 기준)
    - True LRU는 4-way에서 log₂(4!) ≈ 4.58 → 5비트 필요
    - N-way 증가 시: PLRU = (N-1)비트, True LRU = O(N·log₂N)비트
    → PLRU가 HW 비용 대비 성능이 우수하여 실제 프로세서에서 널리 사용
```

**DV 포인트**: PLRU 검증 시 교체 순서가 True LRU와 정확히 일치하지 않는다. "근사"이므로 특정 접근 패턴에서 LRU와 다른 Way를 교체할 수 있다 — Reference Model도 동일한 PLRU 알고리즘으로 구현해야 한다.

---

## HW-Managed vs SW-Managed TLB

```
HW-Managed TLB (ARM, x86):
  TLB Miss → HW Page Walk Engine이 자동으로 Page Table 탐색
  → SW 개입 없이 TLB 채움
  → OS는 Page Table만 관리하면 됨

  장점: 빠른 Miss 처리 (HW 속도)
  단점: Page Table 형식이 HW에 고정 → 유연성 낮음

SW-Managed TLB (MIPS, SPARC):
  TLB Miss → TLB Miss Exception → OS의 TLB Miss Handler 호출
  → SW가 Page Table 탐색 후 TLB에 직접 채움

  장점: Page Table 형식 자유 (OS가 결정)
  단점: Exception 오버헤드 → Miss 처리 수십~수백 cycle 더 느림

현재 추세:
  ARM, x86, RISC-V 모두 HW-Managed 채택
  → SW-Managed는 거의 사라짐 (임베디드 일부 제외)
```

| 항목 | HW-Managed | SW-Managed |
|------|-----------|-----------|
| Miss 처리 | HW Walk Engine | OS Exception Handler |
| Miss Latency | 수십~수백 cycle | 수백~수천 cycle |
| PT 형식 | HW 고정 | SW 자유 |
| DV 복잡도 | Walk Engine 검증 필요 | Exception 흐름 검증 필요 |
| 대표 ISA | ARM, x86, RISC-V | MIPS, SPARC |

---

## TLB Prefetch / Speculative Walk

```
TLB Prefetch — Miss를 사전에 방지:

방법 1: Sequential Prefetch
  VA = 0x1000 접근 (Hit) → 다음 Page VA = 0x2000도 미리 Walk
  → Sequential DMA 트래픽에 효과적
  → Random 접근에는 무효 (오히려 TLB 오염)

방법 2: Stride Prefetch
  접근 패턴 감지: 0x1000, 0x3000, 0x5000 (stride = 0x2000)
  → 다음 예상: 0x7000을 미리 Walk
  → HW Stride Detector 필요

방법 3: Speculative Walk (Page Walk Cache 활용)
  Page Walk 중 중간 레벨 결과를 캐싱:
    Level 0 결과 → Level 0 Cache에 저장
    Level 1 결과 → Level 1 Cache에 저장

  다음 Walk 시 상위 레벨 캐시 Hit → Walk 단축:
    4-level Walk = 4 mem access
    Level 0,1 캐시 Hit → 2 mem access만 필요 (50% 단축)

  이것이 "Page Walk Cache (PWC)" 또는 "Translation Walk Cache"
```

**면접 포인트**: "TLB Miss Latency를 줄이는 방법?" → (1) TLB 크기 증가, (2) Huge Page, (3) Page Walk Cache로 중간 레벨 캐싱, (4) Prefetch. 이 중 PWC가 가장 실질적이며 대부분의 현대 MMU에 구현되어 있다.

---

## TLB Invalidation (무효화)

### 무효화가 필요한 시점

| 이벤트 | 이유 | 무효화 범위 |
|--------|------|-----------|
| 컨텍스트 스위치 | 다른 프로세스의 매핑 | ASID 기반 선택적 (또는 전체) |
| Page Table 변경 | OS가 매핑 변경 | 변경된 VA 범위 |
| VM 전환 | 다른 VM의 매핑 | VMID 기반 선택적 |
| 권한 변경 | mprotect() 등 | 변경된 VA |
| Unmap | 매핑 제거 | 제거된 VA |

### ARMv8 TLB Invalidation 명령어

```
TLBI ALLE1        // EL1 전체 TLB 무효화
TLBI VAE1, Xt     // 특정 VA의 EL1 엔트리 무효화
TLBI ASIDE1, Xt   // 특정 ASID의 전체 엔트리 무효화
TLBI VMALLE1      // 현재 VMID의 전체 EL1 엔트리 무효화

DSB ISH            // 무효화 완료 보장 (Barrier)
ISB                // 파이프라인 플러시
```

**DV 핵심**: TLB Invalidation 후 같은 VA를 접근하면 반드시 TLB Miss가 발생하고 Page Walk가 수행되어야 한다. Stale 엔트리가 남아있으면 보안 취약점이 된다.

---

## TLB Coherency 문제

### 문제: Page Table 변경 시 TLB 불일치

```
시간 순서:

T1: TLB에 VA=0x1000 → PA=0x8000 캐싱됨
T2: OS가 Page Table에서 VA=0x1000의 매핑을 PA=0xA000으로 변경
T3: CPU가 VA=0x1000 접근 → TLB Hit → PA=0x8000 (오래된 값!)
    → Stale Translation!

해결: T2 후에 반드시 TLB Invalidation 수행
     TLBI VAE1, 0x1000; DSB ISH; ISB
     → T3에서 TLB Miss → Page Walk → PA=0xA000 (올바른 값)
```

### 멀티코어 환경에서의 TLB Coherency

```
Core 0: TLB에 VA=0x1000 → PA=0x8000
Core 1: OS가 Page Table 변경 후 자신의 TLB만 Invalidation

→ Core 0의 TLB는 여전히 오래된 값!

해결: Broadcast TLB Invalidation
  TLBI VAE1IS, Xt   // Inner Shareable → 모든 코어에 broadcast
  DSB ISH            // 모든 코어의 완료 보장
```

### TLB Shootdown 프로토콜 (멀티코어 상세)

```
TLB Shootdown = 한 코어가 다른 코어들의 TLB를 원격 무효화하는 프로토콜

x86 방식 (SW Shootdown — IPI 기반):
  1. Core 0: Page Table 변경
  2. Core 0: 자신의 TLB Invalidation
  3. Core 0: 다른 코어들에 IPI (Inter-Processor Interrupt) 전송
  4. Core 1~N: IPI 수신 → TLB Invalidation Handler 실행
  5. Core 1~N: 완료 ACK → Core 0에 응답
  6. Core 0: 모든 ACK 수신 후 진행
  → 코어 수에 비례하여 지연 증가 (scalability 문제)

ARM 방식 (HW Broadcast — TLBI + IS):
  1. Core 0: TLBI VAE1IS, Xt  (HW가 자동으로 모든 코어에 broadcast)
  2. Core 0: DSB ISH           (모든 코어의 무효화 완료 대기)
  3. HW 인터커넥트가 broadcast → 각 코어 TLB 자동 무효화
  → SW 개입 최소 (IPI 불필요), 더 빠름

DV 검증 핵심:
  - Broadcast 후 모든 코어에서 해당 엔트리 무효화 확인
  - DSB ISH 전에 다른 코어가 stale 엔트리 사용하지 않는지 확인
  - Race condition: invalidation 진행 중 같은 VA로 walk 시작 시 처리
```

---

## DV 관점 — TLB 검증 포인트

| 검증 항목 | 시나리오 | 확인 사항 |
|----------|---------|----------|
| TLB Hit | 동일 VA 연속 접근 | 첫 접근은 Walk, 이후 1-cycle 변환 |
| TLB Miss → Walk | 새로운 VA 접근 | Page Walk 수행 후 TLB에 캐싱 |
| TLB Replacement | 엔트리 가득 참 + 새 VA | 교체 정책 정확 동작 |
| TLB Invalidation | Invalidate 후 동일 VA 접근 | 반드시 Miss 발생 → Walk |
| ASID 분리 | 같은 VA, 다른 ASID | 각각 별도 엔트리, 별도 PPN |
| Multi-size | 4KB + 2MB 혼합 | 크기별 VPN 마스킹 정확 |
| Stale Entry | Page Table 변경 후 Invalidation 없이 접근 | **버그**: 잘못된 PA 반환 |
| Concurrent Walk | 동시에 여러 TLB Miss | Walk Engine 병렬 처리 또는 직렬화 정확 |

---

## Q&A

**Q: TLB Miss Ratio가 성능에 미치는 영향은?**
> "TLB Hit은 ~1 cycle, Miss는 4-level Page Walk로 ~수백 ns가 소요된다. 800배 차이이므로 Miss Ratio 1% 변화도 전체 성능에 크게 영향을 미친다. 예를 들어 Hit Rate 99%→95%만 해도 Effective Access Time이 4.5ns→20.5ns로 4.6배 증가한다. 이것이 TLB 크기와 교체 정책이 MMU 설계에서 핵심인 이유다."

**Q: TLB Invalidation이 왜 중요한가?**
> "Page Table 변경 후 TLB에 남아있는 Stale Entry는 잘못된 물리 주소로 접근하게 만든다 — 데이터 오염이나 보안 취약점으로 이어진다. 특히 멀티코어에서는 한 코어가 변경해도 다른 코어의 TLB에 Stale 엔트리가 남을 수 있으므로, Broadcast Invalidation(TLBI + IS suffix) + Barrier(DSB ISH)가 필수적이다."

**Q: IOTLB와 CPU TLB의 차이점은?**
> "세 가지 차이: (1) 식별자 — CPU TLB는 ASID로 프로세스를 구분하고, IOTLB는 StreamID(디바이스)와 SubstreamID(프로세스)로 구분한다. (2) 트래픽 패턴 — CPU는 명령어 단위 접근, DMA는 대량 순차 접근, GPU는 불규칙 접근이므로 최적 TLB 설계가 다르다. (3) Invalidation — IOTLB Invalidation은 디바이스 DMA가 진행 중일 때 동기화 문제가 더 복잡하다."

**Q: Pseudo-LRU가 True LRU 대신 사용되는 이유는?**
> "HW 비용이다. 4-way TLB에서 True LRU는 접근 순서를 완전히 기록하려면 5비트가 필요하고, N-way에서는 O(N·log₂N)비트로 급증한다. Pseudo-LRU는 이진 트리(N-1비트)로 근사하여, 4-way에서 3비트면 충분하다. 성능은 True LRU의 95% 이상에 근접하면서 HW 면적은 크게 절약된다."

**Q: Page Walk Cache란 무엇이고 왜 중요한가?**
> "Page Walk 중 중간 레벨(Level 0, 1, 2)의 PTE를 캐싱하는 구조다. 4-level Walk은 4번의 메모리 접근이 필요하지만, 상위 레벨이 PWC에 Hit하면 2~3번으로 줄어든다. 같은 가상 주소 범위 내의 여러 페이지는 상위 레벨 PTE를 공유하므로, 연속적인 접근에서 PWC Hit Rate가 높다. TLB Miss 시의 penalty를 50% 이상 줄일 수 있어 현대 MMU에서 필수적이다."

**Q: HW-Managed TLB vs SW-Managed TLB의 차이는?**
> "HW-Managed(ARM, x86, RISC-V)는 TLB Miss 시 HW Walk Engine이 자동으로 Page Table을 탐색하여 TLB를 채운다. SW-Managed(MIPS)는 Miss 시 Exception이 발생하고 OS Handler가 직접 TLB를 채운다. HW 방식이 수십~수백 cycle 더 빠르고, SW 개입이 없어 파이프라인 효율이 좋다. 현재 주류는 HW-Managed이며, DV 관점에서는 Walk Engine의 정확성 검증이 핵심이다."

---

## 핵심 정리

- **TLB는 latency 게임**: hit 1 cycle vs miss + walk 100+ cycle. Hit rate가 IPC를 좌우.
- **계층화**: micro-TLB (L1 cache 옆 4-16 entries) → L1 TLB (수십 entries) → L2 TLB (수천 entries).
- **ASID/VMID**: process/VM 간 TLB 공유 가능. Context switch 시 flush 회피로 cold miss 폭증 방지.
- **TLBI 명령**: ASID-by, VA-by, full flush. context switch / page table 변경 시 필수.
- **TLB shootdown**: Multi-core SMP에서 다른 코어의 TLB도 무효화하는 IPI(inter-processor interrupt) 메커니즘. 비싸므로 batch 처리.
- **HW-managed가 표준**: 검증에서는 walk engine + TLB의 정확성 (특히 invalidation 후 stale 없는지) 핵심.

## 다음 단계

- 📝 [**Module 03 퀴즈**](quiz/03_tlb_quiz.md)
- ➡️ [**Module 04 — IOMMU / SMMU**](04_iommu_smmu.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../02_page_table_structure/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Page Table 구조</div>
  </a>
  <a class="nav-next" href="../04_iommu_smmu/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">IOMMU / SMMU — SoC에서의 MMU</div>
  </a>
</div>
