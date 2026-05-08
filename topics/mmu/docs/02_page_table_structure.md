# Module 02 — Page Table Structure

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🧭</span>
    <span class="chapter-back-text">MMU</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 02</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#왜-multi-level인가">왜 Multi-level인가?</a>
  <a class="page-toc-link" href="#armv8-4-level-page-table-4kb-granule">ARMv8 4-Level Page Table (4KB Granule)</a>
  <a class="page-toc-link" href="#page-table-entry-pte-구조-armv8">Page Table Entry (PTE) 구조 — ARMv8</a>
  <a class="page-toc-link" href="#page-walk-cache-pwc-walk-비용-절감">Page Walk Cache (PWC) — Walk 비용 절감</a>
  <a class="page-toc-link" href="#contiguous-bit-tlb-효율-향상">Contiguous Bit — TLB 효율 향상</a>
  <a class="page-toc-link" href="#copy-on-write-cow-메커니즘">Copy-on-Write (COW) 메커니즘</a>
  <a class="page-toc-link" href="#risc-v-page-table-비교-sv39-sv48">RISC-V Page Table 비교 — Sv39 / Sv48</a>
  <a class="page-toc-link" href="#asid-address-space-identifier">ASID (Address Space Identifier)</a>
  <a class="page-toc-link" href="#vmid-virtual-machine-identifier-가상화">VMID (Virtual Machine Identifier) — 가상화</a>
  <a class="page-toc-link" href="#page-table-walk의-성능-비용">Page Table Walk의 성능 비용</a>
  <a class="page-toc-link" href="#dv-관점-page-table-검증-포인트">DV 관점 — Page Table 검증 포인트</a>
  <a class="page-toc-link" href="#qa">Q&A</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Explain** Single-level page table의 메모리 비용 문제와 Multi-level이 이를 해결하는 원리를 설명할 수 있다.
    - **Walk** 64-bit VA를 ARMv8 4-level translation으로 단계별 추적해 PA를 도출할 수 있다.
    - **Distinguish** 4KB / 16KB / 64KB granule과 각 granule별 page level 깊이/주소 비트 분할을 식별할 수 있다.
    - **Apply** Block descriptor(Huge page)와 Table descriptor의 차이를 시나리오에 매핑할 수 있다.
    - **Describe** Page Walk Cache (PWC)가 어떻게 walk 비용을 줄이는지 설명할 수 있다.

!!! info "사전 지식"
    - [Module 01](01_mmu_fundamentals.md) (VA→PA 변환 개념)
    - 이진/16진 비트 마스킹, 인덱스 추출

## 왜 이 모듈이 중요한가

**Page Table walk은 MMU 성능의 핵심 비용**입니다. 4-level walk은 4번의 메모리 access가 발생하므로 cache miss 시 latency가 크게 늘어납니다. **PWC, Huge page, ASID 활용**이 walk 비용을 줄이는 표준 기법이며, 검증에서는 multi-level walk을 정확히 trace하는 능력이 필수입니다.

!!! tip "💡 이해를 위한 비유"
    **다단계 Page Table** ≈ **도서관 색인 (대분류 → 중분류 → 소분류 → 책 위치)**

    L4 → L3 → L2 → L1 단계로 좁혀가며 최종 page 위치 도달. 각 단계 entry 가 다음 table 의 base 주소를 담고 있어 sparse 한 주소 공간을 효율적으로 표현.

---

## 핵심 개념
**Page Table = VPN → PPN 매핑을 저장하는 메모리 내 자료구조. 단일 레벨은 메모리 낭비가 심하므로 Multi-level로 계층화하여 필요한 영역만 할당한다.**

!!! danger "❓ 흔한 오해"
    **오해**: Page table walk 는 1번의 메모리 read 다

    **실제**: 4-level page table = 최대 4번의 메모리 read (각 level 의 table 이 메모리에 있으므로). TLB miss 시 비용이 큰 이유.

    **왜 헷갈리는가**: L1 → 데이터 의 1-단계 매핑 직관 때문에 — 실제로는 multi-level 이 hierarchy 마다 메모리 access 추가.
---

## 왜 Multi-level인가?

### 단일 레벨 Page Table의 문제

```
48-bit VA, 4KB Page의 경우:

  VPN = 48 - 12 = 36 bit
  Page Table 엔트리 수 = 2^36 = 약 687억 개
  PTE 크기 = 8 bytes
  Page Table 크기 = 687억 × 8 = 512 GB !

  → 프로세스 하나당 512 GB의 Page Table? 불가능.
```

### Multi-level로 해결

```
핵심 관찰:
  대부분의 프로세스는 전체 주소 공간의 극히 일부만 사용한다.
  → 사용하지 않는 영역의 하위 테이블을 할당하지 않으면 메모리 절약

  4-level Page Table (x86-64, ARMv8 4KB granule):
    Level 0: 512 entries → 각 엔트리가 512GB 영역 커버
    Level 1: 512 entries → 각 엔트리가 1GB 영역 커버
    Level 2: 512 entries → 각 엔트리가 2MB 영역 커버
    Level 3: 512 entries → 각 엔트리가 4KB 영역 커버 (최종 PPN)

  각 테이블 크기 = 512 × 8B = 4KB = 정확히 1 Page
```

---

## ARMv8 4-Level Page Table (4KB Granule)

### 주소 분해

```
48-bit Virtual Address:

 63    48 47   39 38   30 29   21 20   12 11       0
+--------+-------+-------+-------+-------+----------+
| Sign   |  L0   |  L1   |  L2   |  L3   |  Offset  |
| Ext    | Index | Index | Index | Index | (12-bit) |
| (16bit)| (9bit)| (9bit)| (9bit)| (9bit)|          |
+--------+-------+-------+-------+-------+----------+
              |       |       |       |
              v       v       v       v
           Level 0  Level 1  Level 2  Level 3
           Table    Table    Table    Table
```

### Page Walk 과정 (4단계)

```
TTBR (Translation Table Base Register)
  |  Level 0 테이블의 물리 주소
  v
+--Level 0 Table--+
| Entry[L0 Index] |--→ Level 1 테이블의 물리 주소
+-----------------+
  |
  v
+--Level 1 Table--+
| Entry[L1 Index] |--→ Level 2 테이블의 물리 주소
+-----------------+    또는 1GB Block (Block Descriptor)
  |
  v
+--Level 2 Table--+
| Entry[L2 Index] |--→ Level 3 테이블의 물리 주소
+-----------------+    또는 2MB Block (Block Descriptor)
  |
  v
+--Level 3 Table--+
| Entry[L3 Index] |--→ 4KB Page의 물리 주소 (PPN)
+-----------------+

총 4번의 메모리 접근 필요!
→ 이것이 TLB가 필수적인 이유
```

### Block Descriptor — 중간 레벨에서 바로 매핑

```
Level 1에서 Block Descriptor:
  1GB 블록을 하나의 엔트리로 직접 매핑
  → Level 2, 3 테이블 불필요
  → 대용량 연속 매핑에 유리 (MMIO, 프레임버퍼 등)

Level 2에서 Block Descriptor:
  2MB 블록을 하나의 엔트리로 직접 매핑
  → Huge Page (Linux에서 THP, Transparent Huge Pages)
```

---

## Page Table Entry (PTE) 구조 — ARMv8

### Level 3 Page Descriptor (4KB)

```
 63    52 51   48 47          12 11  10  9  8  7  6  5  4  2  1  0
+--------+------+--------------+-----+--+--+--+--+--+--+-----+--+
|Upper   | Res  | Output Addr  | nG  |AF|SH|AP|NS|AI|  |Type | V|
|Attrs   |      | (PPN)        |     |  |  |  |  |  |  | =11 | =1|
+--------+------+--------------+-----+--+--+--+--+--+--+-----+--+
```

### 주요 필드

| 필드 | 비트 | 의미 |
|------|------|------|
| V (Valid) | [0] | 유효한 엔트리 여부 |
| Type | [1] | 0=Block, 1=Table/Page |
| AI (AttrIdx) | [4:2] | MAIR 레지스터의 캐시 속성 인덱스 |
| NS | [5] | Non-Secure (TrustZone 관련) |
| AP | [7:6] | Access Permission (RO/RW, EL0/EL1) |
| SH | [9:8] | Shareability (Inner/Outer/Non) |
| AF (Access Flag) | [10] | 접근된 적 있는 페이지인지 (OS 페이지 교체 힌트) |
| nG (not Global) | [11] | ASID 사용 여부 |
| Output Address | [47:12] | 물리 페이지 번호 (PPN) |
| Upper Attrs | [63:52] | XN(Execute-Never), PXN, Contiguous 등 |

### Access Permission (AP) 인코딩

| AP[7:6] | EL1 (Kernel) | EL0 (User) |
|---------|-------------|-----------|
| 00 | RW | No Access |
| 01 | RW | RW |
| 10 | RO | No Access |
| 11 | RO | RO |

---

## Page Walk Cache (PWC) — Walk 비용 절감

```
문제: 4-level Walk = 4번 메모리 접근 (400ns)
관찰: 인접한 VA들은 상위 레벨 PTE를 공유한다

예시:
  VA 0x0000_0000_1000 (Page A)와 VA 0x0000_0000_2000 (Page B)
  → Level 0, 1, 2 인덱스가 동일! Level 3만 다름
  → Level 0~2의 PTE를 캐싱하면 Page B Walk 시 Level 3만 읽으면 됨

Page Walk Cache 구조:
  +--Level 0 Cache--+  +--Level 1 Cache--+  +--Level 2 Cache--+
  | VPN[47:39]→PTE  |  | VPN[47:30]→PTE  |  | VPN[47:21]→PTE  |
  | (~4 entries)    |  | (~8 entries)    |  | (~16 entries)   |
  +----------------+  +----------------+  +----------------+

  Walk 시 각 레벨 캐시 확인:
    Level 0 Hit → 1회 메모리 접근 생략 (3회로 단축)
    Level 0+1 Hit → 2회 생략 (2회로 단축)
    Level 0+1+2 Hit → 3회 생략 (1회로 단축!)

  효과:
    순차 접근 시 PWC Hit Rate 매우 높음 (같은 1GB/2MB 영역 내)
    → 평균 Walk 비용 40~60% 감소
```

**DV 포인트**: PWC의 정확성 검증 — Page Table 변경 후 PWC에 stale 데이터가 남으면 잘못된 PA가 생성될 수 있다. TLB Invalidation 시 PWC도 함께 무효화되는지 확인해야 한다.

---

## Contiguous Bit — TLB 효율 향상

```
ARMv8 Contiguous bit (PTE[52]):
  인접한 16개의 4KB 페이지가 물리적으로도 연속일 때
  → PTE에 Contiguous bit = 1 설정
  → TLB가 16개 PTE를 하나의 엔트리로 통합 (4KB × 16 = 64KB)

  +--TLB Entry (Contiguous)--+
  | VPN range: 0x10~0x1F     |  ← 16개 VA 페이지를 하나로
  | PPN base: 0x80           |
  | Size: 64KB (effective)   |
  +---------------------------+

효과:
  - TLB 엔트리 소모: 16개 → 1개 (16배 절약)
  - 4KB Granule이지만 64KB TLB 커버리지 효과
  - Huge Page(2MB)까지 갈 필요 없이 중간 크기 커버리지

제약:
  - 16개 페이지가 물리적으로 연속이어야 함
  - OS가 적극적으로 연속 할당해야 효과적
  - 일부만 unmap하면 Contiguous 해제 필요

DV 검증:
  - Contiguous 엔트리 내 개별 페이지 접근 시 정확한 PA 계산
  - Contiguous 영역 중간 페이지 unmap → 엔트리 분리 확인
  - Contiguous + non-contiguous 혼합 시 TLB 동작
```

---

## Copy-on-Write (COW) 메커니즘

```
COW = fork() 시 물리 메모리 복사를 지연하는 최적화

fork() 전:
  Parent: VA 0x1000 → PA 0x8000 (RW)

fork() 직후:
  Parent: VA 0x1000 → PA 0x8000 (RO로 변경!)
  Child:  VA 0x1000 → PA 0x8000 (RO — 같은 물리 페이지 공유)

  → 물리 메모리 복사 없음! 읽기만 하면 공유 유지

Write 시:
  Parent가 VA 0x1000에 Write 시도
  → PTE가 RO → Permission Fault 발생
  → OS COW Handler:
    1. 새 물리 페이지 할당 (PA 0xC000)
    2. PA 0x8000의 내용을 PA 0xC000에 복사
    3. Parent PTE 업데이트: VA 0x1000 → PA 0xC000 (RW)
    4. TLB Invalidation (stale RO 엔트리 제거)
    5. Write 재실행 → 성공

MMU/TLB 관점:
  - COW = Permission Fault를 의도적으로 활용하는 메커니즘
  - TLB에 RO 엔트리 → Write 시도 → Fault → TLB Invalidation → RW로 재채움
  - DV에서 Permission Fault → 복구 → TLB 상태 변화의 전체 흐름 검증 필요
```

---

## RISC-V Page Table 비교 — Sv39 / Sv48

```
RISC-V는 Sv39 (3-level)과 Sv48 (4-level) 모드 지원:

Sv39 (3-Level, 39-bit VA):
  38    30 29    21 20    12 11       0
  +-------+-------+-------+----------+
  | VPN[2]| VPN[1]| VPN[0]|  Offset  |
  | (9bit)| (9bit)| (9bit)| (12-bit) |
  +-------+-------+-------+----------+
  가상 주소 공간: 512 GB (2^39)
  사용: 임베디드, 소형 시스템

Sv48 (4-Level, 48-bit VA):
  47    39 38    30 29    21 20    12 11       0
  +-------+-------+-------+-------+----------+
  | VPN[3]| VPN[2]| VPN[1]| VPN[0]|  Offset  |
  | (9bit)| (9bit)| (9bit)| (9bit)| (12-bit) |
  +-------+-------+-------+-------+----------+
  가상 주소 공간: 256 TB (2^48)
  사용: 서버, 대형 시스템
```

### ARMv8 vs RISC-V vs x86-64 비교

| 항목 | ARMv8 (AArch64) | RISC-V (Sv48) | x86-64 |
|------|----------------|--------------|--------|
| VA 비트 | 48-bit | 48-bit | 48-bit (57 with LA57) |
| PT 레벨 | 4 (L0~L3) | 4 (L3~L0, 번호 반대) | 4 (PML4→PDP→PD→PT) |
| Granule | 4KB/16KB/64KB | 4KB | 4KB |
| 각 테이블 엔트리 수 | 512 (9-bit index) | 512 (9-bit index) | 512 (9-bit index) |
| PTE 크기 | 8 bytes | 8 bytes | 8 bytes |
| Huge Page | 2MB (L2), 1GB (L1) | 2MB (L1), 1GB (L0) | 2MB (PD), 1GB (PDP) |
| ASID | 8/16-bit | 16-bit | PCID 12-bit |
| 가상화 | Stage 1+2 | 2-stage (G-Stage) | EPT (Extended PT) |
| Table Base Reg | TTBR0/1_EL1 | satp | CR3 |

**면접 포인트**: 세 ISA 모두 구조적으로 유사하다 (512-entry × 4-level × 8B PTE). 차이는 용어와 세부 인코딩이며, 핵심 원리(multi-level walk, TLB caching)는 동일하다. "RISC-V도 다뤄봤느냐" 질문에 "구조는 ARMv8과 거의 동일하며, 검증 방법론은 그대로 적용 가능하다"고 답하면 된다.

---

## ASID (Address Space Identifier)

### 왜 필요한가?

```
컨텍스트 스위치 시 문제:

  Process A: VA 0x1000 → PA 0x8000
  Process B: VA 0x1000 → PA 0xA000

  Process A → B 전환 시:
  방법 1: TLB 전체 Flush → 모든 엔트리 무효화 → 성능 저하
  방법 2: ASID 사용 → TLB 엔트리에 ASID 태그 추가
          → ASID가 다르면 같은 VA도 다른 엔트리로 구분
          → TLB Flush 불필요!
```

### ASID 동작

```
TLB Entry:
  +------+------+------+--------+
  | ASID | VPN  | PPN  | Attrs  |
  +------+------+------+--------+
  |  5   | 0x1  | 0x8  | RW     |  ← Process A
  |  7   | 0x1  | 0xA  | RO     |  ← Process B
  +------+------+------+--------+

  ASID = 5 (Process A) → TLB Hit → PA 0x8000
  ASID = 7 (Process B) → TLB Hit → PA 0xA000
  → 같은 VA 0x1000이지만 다른 PA로 변환
```

---

## VMID (Virtual Machine Identifier) — 가상화

```
가상화 환경 (Stage 2 Translation):

  Guest OS → Stage 1: GVA → GPA (Guest Physical)
                |
                v
  Hypervisor → Stage 2: GPA → HPA (Host Physical)
                        (VMID로 VM 구분)

  TLB Entry (가상화):
    +------+------+------+------+--------+
    | VMID | ASID | VPN  | PPN  | Attrs  |
    +------+------+------+------+--------+

  → VMID + ASID + VPN으로 완전한 주소 식별
```

---

## Page Table Walk의 성능 비용

| 레벨 수 | 메모리 접근 횟수 | 대략적 시간 (DDR4) |
|---------|----------------|-------------------|
| 2-level (32-bit) | 2회 | ~200 ns |
| 3-level | 3회 | ~300 ns |
| 4-level (64-bit) | 4회 | ~400 ns |
| 5-level (57-bit VA) | 5회 | ~500 ns |

**대비**: L1 캐시 접근 = ~1 ns, TLB Hit = ~1 cycle (~0.5 ns)

→ **TLB Miss 시 Page Walk는 TLB Hit 대비 수백 배 느리다** → TLB의 중요성

---

## DV 관점 — Page Table 검증 포인트

| 검증 항목 | 설명 |
|----------|------|
| Multi-level Walk 정확성 | 각 레벨 인덱스 추출 + 다음 테이블 주소 계산 |
| Block Descriptor 처리 | Level 1/2에서 Block인 경우 Walk 조기 종료 |
| Invalid PTE 처리 | Valid=0인 경우 Page Fault 생성 |
| Permission Check | AP 필드 기반 RO/RW × EL0/EL1 조합 |
| ASID 매칭 | 같은 VA, 다른 ASID → 다른 PA 매핑 확인 |
| Attribute 적용 | Cacheable/Non-cacheable/Device 속성 정확 전파 |
| Walk 중 에러 | 중간 레벨 PTE가 Invalid인 경우 → Fault 정확 보고 |

---

## Q&A

**Q: 왜 Page Table을 Multi-level로 설계하는가?**
> "메모리 효율성이다. 48-bit VA, 4KB Page의 단일 레벨 테이블은 512GB가 필요하다. Multi-level(4-level)은 사용하지 않는 주소 범위의 하위 테이블을 할당하지 않으므로, 실제 사용하는 주소 범위에 비례하는 메모리만 소비한다. 각 레벨 테이블은 정확히 1 Page(4KB)로 설계되어 메모리 관리가 간단하다."

**Q: Page Walk는 왜 느린가?**
> "4-level Page Table의 경우 4번의 메모리 접근이 순차적으로 필요하다. DRAM 접근 하나가 ~100ns이므로 ~400ns가 소요된다. TLB Hit이 ~0.5ns인 것과 비교하면 수백 배 차이다. 이것이 TLB의 존재 이유이며, TLB Miss Ratio가 성능에 결정적 영향을 미치는 이유다."

**Q: ASID가 왜 중요한가?**
> "컨텍스트 스위치 시 TLB 전체 Flush를 피하기 위해서다. ASID 없이는 프로세스 전환마다 TLB를 무효화해야 하므로 전환 직후 모든 접근이 TLB Miss가 되어 성능이 급격히 하락한다. ASID를 TLB 엔트리에 태깅하면 같은 VA도 프로세스별로 구분되어 TLB Flush 없이 전환이 가능하다."

**Q: Page Walk Cache란 무엇이고 어디서 효과적인가?**
> "Page Walk 중 중간 레벨(Level 0~2)의 PTE를 캐싱하는 소형 캐시다. 인접한 VA들은 상위 레벨 PTE를 공유하므로, 순차적 접근에서 PWC Hit Rate가 매우 높다. 4-level Walk이 4번의 메모리 접근이 필요하지만, 상위 3레벨이 PWC에 Hit하면 1번의 접근으로 줄어든다. DMA 같은 순차 트래픽에서 평균 Walk 비용을 40~60% 절감한다."

**Q: Copy-on-Write에서 MMU의 역할은?**
> "COW는 fork() 시 물리 메모리 복사를 지연하는 최적화다. fork() 직후 부모/자식 모두 같은 물리 페이지를 RO로 공유한다. Write 시도 시 MMU가 Permission Fault를 발생시키고, OS의 COW Handler가 새 물리 페이지를 할당·복사한 뒤 PTE를 RW로 업데이트한다. MMU는 Permission Fault를 정확히 감지하고, Handler 후 TLB Invalidation → 재접근 시 새 PTE로 Walk하는 전체 흐름의 정확성이 핵심이다."

---
!!! warning "실무 주의점 — Page Walk 중 Access Flag 미설정으로 반복 Fault"
    **현상**: 처음 접근하는 페이지에서 Permission Fault가 아닌 반복적 Access Flag Fault가 발생하여 OS Handler가 무한 루프에 빠지거나 성능이 급격히 저하됨.
    
    **원인**: ARMv8은 PTE의 AF(Access Flag) 비트가 0이면 Fault를 발생시켜 SW가 명시적으로 AF를 설정하도록 강제함. 페이지 테이블 초기화 시 AF=0으로 세팅하면 해당 페이지에 접근할 때마다 Fault가 반복 발생.
    
    **점검 포인트**: PTE 생성 코드에서 AF 비트(bit[10]) 초기값 확인. Walk 로그에서 동일 VA에 대해 Fault → PTE 업데이트 → 재Fault가 반복되면 AF 누락 의심. `FEAT_HAFDBS`(HW AF 자동 관리) 미지원 환경에서는 SW Handler가 반드시 AF를 set해야 함.

## 핵심 정리

- **Multi-level이 메모리 효율의 핵심**: Single-level은 모든 VA를 위해 page table 통째로 할당 (TB 단위). Multi-level은 사용 중인 영역의 sub-tree만 할당.
- **ARMv8 4-level (4KB granule)**: VA[63:48] sign-extension, [47:39] L0, [38:30] L1, [29:21] L2, [20:12] L3, [11:0] page offset.
- **Granule trade-off**: 4KB = 깊은 walk + fine grain, 64KB = 얕은 walk + coarse grain. 보통 4KB 표준, large dataset은 16KB/64KB.
- **Block descriptor (Huge page)**: 중간 레벨에서 변환 종료 → 2MB / 1GB 매핑. TLB 효율성 ↑.
- **PWC (Page Walk Cache)**: 중간 레벨 PTE 캐싱 → 순차 access의 walk 비용 40-60% 감소.
- **COW**: Write fault → OS가 복사 + PTE 업데이트 + TLB invalidation. MMU는 fault 감지와 후속 walk 정확성 책임.

## 다음 단계

- 📝 [**Module 02 퀴즈**](quiz/02_page_table_structure_quiz.md)
- ➡️ [**Module 03 — TLB**](03_tlb.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../01_mmu_fundamentals/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">MMU 기본 개념 및 주소 변환</div>
  </a>
  <a class="nav-next" href="../03_tlb/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">TLB (Translation Lookaside Buffer)</div>
  </a>
</div>


--8<-- "abbreviations.md"
