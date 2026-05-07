# Module 03 — Memory Virtualization

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🪟</span>
    <span class="chapter-back-text">Virtualization</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 03</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#왜-메모리-가상화가-필요한가">왜 메모리 가상화가 필요한가?</a>
  <a class="page-toc-link" href="#주소-변환-계층-구조">주소 변환 계층 구조</a>
  <a class="page-toc-link" href="#방법-1-shadow-page-table-sw-방식">방법 1: Shadow Page Table (SW 방식)</a>
  <a class="page-toc-link" href="#방법-2-2-stage-translation-hw-방식">방법 2: 2-Stage Translation (HW 방식)</a>
  <a class="page-toc-link" href="#stage-1-vs-stage-2-최적화-비교">Stage 1 vs Stage 2 최적화 비교</a>
  <a class="page-toc-link" href="#huge-page로-tlb-효율-개선">Huge Page로 TLB 효율 개선</a>
  <a class="page-toc-link" href="#메모리-가상화-방식-비교-요약">메모리 가상화 방식 비교 요약</a>
  <a class="page-toc-link" href="#qa">Q&A</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Trace** VA → IPA → PA 2단계 변환 흐름
    - **Distinguish** Shadow Page Table (SW) vs EPT/NPT/Stage-2 (HW)
    - **Apply** Memory ballooning, KSM (Kernel Same-page Merging)
    - **Identify** 메모리 가상화의 성능 영향

!!! info "사전 지식"
    - [MMU 코스](../../mmu/) (page table walk, TLB)
    - [Module 01-02](01_virtualization_fundamentals.md)

!!! tip "💡 이해를 위한 비유"
    **Memory Virtualization** ≈ **주소록 2-단계 — guest 가 본 주소 → host 실제 주소 (Stage 1 + Stage 2)**

    Guest 의 page table 도 가상이고, hypervisor 가 다시 host 물리 주소로 매핑. EPT (Intel) / NPT (AMD) / Stage 2 (ARM).

---

## 핵심 개념
**메모리 가상화 = VM마다 독립된 물리 메모리 공간이 있다는 환상을 제공하면서, 실제로는 하이퍼바이저가 물리 메모리를 분할/관리하는 것. 핵심 과제는 VA→IPA→PA 2단계 주소 변환의 성능 오버헤드 최소화.**

!!! danger "❓ 흔한 오해"
    **오해**: Stage 2 가 켜지면 guest 가 자동으로 격리된다

    **실제**: Stage 2 가 켜져도 hypervisor 가 page table 잘못 채우면 cross-VM access 가능. 격리 = HW + SW 정책 정확성.

    **왜 헷갈리는가**: "기능 켜짐 = 안전" 의 직관. 정책 SW 가 critical.
---

## 왜 메모리 가상화가 필요한가?

### Bare Metal에서의 메모리 관리

```
OS가 물리 메모리를 직접 관리:

  VA ──[Page Table]──> PA
  (OS가 소유)          (실제 DRAM)

  OS는 전체 물리 메모리를 알고 있음
  → VA→PA 변환만 하면 됨 (1단계)
```

### 가상화 환경에서의 문제

```
VM0의 Guest OS: "나는 4GB 물리 메모리를 갖고 있다"
VM1의 Guest OS: "나도 4GB 물리 메모리를 갖고 있다"
실제 물리 DRAM: 8GB

문제:
  - 두 Guest OS 모두 자기가 PA 0x0~0xFFFFFFFF을 소유한다고 생각
  - 하지만 같은 물리 주소를 두 VM이 쓰면 데이터 충돌
  - Guest OS가 직접 페이지 테이블을 관리하면 → 다른 VM 메모리 접근 가능

해결: Guest OS가 보는 "물리 주소"는 가짜 (IPA)
      실제 PA로의 변환은 Hypervisor가 담당
```

---

## 주소 변환 계층 구조

```
┌────────────────────────────────────────────────┐
│                 Guest 프로세스                   │
│  VA (Virtual Address)                           │
│  각 프로세스가 보는 주소                          │
└────────────┬───────────────────────────────────┘
             │ Stage 1 Translation
             │ (Guest OS의 Page Table, EL1 관리)
             ▼
┌────────────────────────────────────────────────┐
│              Guest OS                           │
│  IPA (Intermediate Physical Address)            │
│  Guest OS가 "물리 주소"라고 믿는 주소             │
│  실제로는 Hypervisor가 만든 가상의 물리 공간      │
└────────────┬───────────────────────────────────┘
             │ Stage 2 Translation
             │ (Hypervisor의 Page Table, EL2 관리)
             ▼
┌────────────────────────────────────────────────┐
│           실제 하드웨어                          │
│  PA (Physical Address)                          │
│  실제 DRAM 주소                                  │
└────────────────────────────────────────────────┘
```

### 각 주체의 역할

| 주체 | 관리하는 변환 | 알고 있는 것 | 모르는 것 |
|------|-------------|------------|----------|
| **Guest OS** (EL1) | VA → IPA | 자기 VM의 가상 메모리 레이아웃 | IPA가 실제 PA가 아닌 것 |
| **Hypervisor** (EL2) | IPA → PA | 전체 물리 메모리 레이아웃 + 모든 VM의 IPA 매핑 | Guest 프로세스의 VA (관여 안 함) |

---

## 방법 1: Shadow Page Table (SW 방식)

### 개념

Hypervisor가 VA→PA를 직접 변환하는 "그림자" 페이지 테이블을 유지:

```
Guest OS의 PT     Shadow PT        실제 사용
(VA → IPA)        (VA → PA)
┌──────────┐     ┌──────────┐
│VA:0x1000 │     │VA:0x1000 │
│→IPA:0x5000│    │→ PA:0xA000│ ◄── MMU가 실제로 사용하는 것
├──────────┤     ├──────────┤
│VA:0x2000 │     │VA:0x2000 │
│→IPA:0x6000│    │→ PA:0xB000│
└──────────┘     └──────────┘
                      ▲
                      │
                 Hypervisor가
                 Guest PT 변경 시마다
                 Shadow PT를 동기화
```

### 동작 원리

1. Guest OS가 자기 Page Table(VA→IPA) 수정 시도
2. Hypervisor가 **trap** (CR3/TTBR 쓰기 감지)
3. Guest PT의 IPA를 실제 PA로 변환하여 Shadow PT 업데이트
4. **MMU에는 Shadow PT를 로드** — HW는 VA→PA 1단계 변환만 수행

### 성능 문제

```
Guest OS가 Page Table을 수정할 때마다:
  1. VM Exit (trap) 발생                    ← 수천 사이클
  2. Hypervisor가 Guest PT 읽기             ← 메모리 접근
  3. IPA → PA 변환                          ← 메모리 접근
  4. Shadow PT 업데이트                     ← 메모리 접근
  5. VM Entry (Guest 복귀)                  ← 수천 사이클

컨텍스트 스위치마다 발생 (프로세스 전환 = PT 교체)
→ 프로세스가 많은 워크로드에서 심각한 오버헤드
```

| 장점 | 단점 |
|------|------|
| MMU는 1단계 변환만 (성능 좋음) | Guest PT 변경마다 VM Exit |
| HW 지원 불필요 | Hypervisor 복잡도 높음 |
| | 메모리 추가 사용 (Shadow PT 공간) |

---

## 방법 2: 2-Stage Translation (HW 방식)

### 개념 (EPT / ARM Stage 1+2)

HW가 2단계 변환을 직접 수행. Shadow PT 불필요:

```
MMU가 자동으로 2단계 수행:

  VA ──[Stage 1 PT]──> IPA ──[Stage 2 PT]──> PA
       (Guest OS 관리)        (Hypervisor 관리)

  Guest OS는 자기 PT를 자유롭게 수정 가능
  → VM Exit 불필요! (Hypervisor trap 없음)
  → Hypervisor는 Stage 2 PT만 관리
```

### Page Table Walk 과정 (4-Level PT 기준)

```
VA가 주어지면:

Stage 1 Walk (Guest OS의 PT):
  TTBR(EL1) → L0 table → L1 table → L2 table → L3 table → IPA

  하지만! 각 테이블 주소도 IPA이므로 Stage 2 변환 필요:

Stage 1 + Stage 2 Combined Walk:
  TTBR(EL1)의 IPA를 PA로 변환 (Stage 2)
    → L0 table 읽기
  L0 entry의 IPA를 PA로 변환 (Stage 2)
    → L1 table 읽기
  L1 entry의 IPA를 PA로 변환 (Stage 2)
    → L2 table 읽기
  L2 entry의 IPA를 PA로 변환 (Stage 2)
    → L3 table 읽기
  최종 IPA를 PA로 변환 (Stage 2)
    → 최종 PA 획득
```

### Worst-Case 메모리 접근 횟수

```
4-level Stage 1 + 4-level Stage 2:

Stage 1의 각 레벨 접근 시 Stage 2 walk 필요:
  Stage 1 L0 접근: Stage 2 walk (최대 4회) + 1회 = 5회
  Stage 1 L1 접근: Stage 2 walk (최대 4회) + 1회 = 5회
  Stage 1 L2 접근: Stage 2 walk (최대 4회) + 1회 = 5회
  Stage 1 L3 접근: Stage 2 walk (최대 4회) + 1회 = 5회
  최종 데이터 접근: Stage 2 walk (최대 4회) + 1회 = 5회

최악의 경우: 5 × 5 = 25회 메모리 접근! (Bare Metal은 5회)
```

### TLB가 핵심인 이유

```
TLB Hit:  VA → PA 즉시 변환 (1 cycle)
TLB Miss: 최대 25회 메모리 접근 (수백 cycle)

→ TLB Hit Rate가 가상화 성능의 핵심 결정 요소
→ TLB 크기와 캐싱 전략이 매우 중요
```

---

## Stage 1 vs Stage 2 최적화 비교

TechForum 슬라이드에서 강조한 핵심 포인트:

| 항목 | Stage 1 (VA → IPA) | Stage 2 (IPA → PA) |
|------|-------------------|-------------------|
| 관리 주체 | Guest OS (EL1) | Hypervisor (EL2) |
| 접근 패턴 | 예측 가능 (프로세스별 locality) | 예측 어려움 (VM 간 물리 메모리 분산) |
| 최적화 | Prefetch, 캐시 구조 활용 가능 | **어려움** — 낮은 locality |
| TLB 효과 | 높음 (Working set이 명확) | **낮음** (VM 간 간섭, 큰 주소 공간) |

```
Stage 2가 병목인 이유:

  VM0: IPA 0x0000 → PA 0x1_0000  (물리 메모리 앞쪽)
  VM1: IPA 0x0000 → PA 0x8_0000  (물리 메모리 뒤쪽)

  Hypervisor가 VM을 배치할 때 물리 메모리가 불연속적
  → Stage 2 PT의 locality가 낮음
  → TLB miss 시 page walk 비용이 큼
  → 이것이 latency/bandwidth 민감 시스템의 핵심 병목
```

---

## Huge Page로 TLB 효율 개선

```
4KB Page:  TLB 1 entry = 4KB 커버
2MB Page:  TLB 1 entry = 2MB 커버  (512배)
1GB Page:  TLB 1 entry = 1GB 커버  (262144배)

가상화에서 Huge Page 효과:
  - Stage 2 PT 깊이 감소 (4-level → 2-level for 1GB)
  - TLB miss 시 walk 횟수 감소
  - TechForum 슬라이드 "Huge page allocation (1GB) to HPA"가 바로 이것
```

### Huge Page + Pass-through 시나리오

```
STEP 1: Hypervisor가 1GB Huge Page를 VM에 할당
        → Stage 2 변환이 거의 1:1 매핑
        → TLB 1 entry로 1GB 전체 커버

STEP 2: User-space 앱이 HPA (Huge Page Area) 위에서 직접 동작
        → Stage 1도 Huge Page 사용 시 TLB pressure 최소화

효과: 2-stage translation의 최악 시나리오 (25회) 거의 발생 안 함
```

---

## 메모리 가상화 방식 비교 요약

| 항목 | Shadow PT | 2-Stage (EPT/ARM) | Pass-through + Huge Page |
|------|----------|-------------------|-------------------------|
| VM Exit 빈도 | 높음 (PT 수정마다) | 낮음 (Stage 2만 관리) | 최소 |
| MMU 변환 단계 | 1단계 (VA→PA) | 2단계 (VA→IPA→PA) | 2단계 (but 거의 1:1) |
| TLB miss 비용 | 낮음 (1-stage walk) | 높음 (최대 25회) | 낮음 (Huge Page) |
| 구현 복잡도 | 높음 (동기화) | 낮음 (HW 지원) | 중간 (IOMMU 설정) |
| 격리 수준 | 높음 | 높음 | 디바이스 단위 |
| 주 사용처 | 레거시 (VT-x 이전) | 현대 범용 가상화 | 고성능 I/O (NIC, GPU) |

---

## Q&A

**Q: 2-stage translation에서 최악의 메모리 접근이 25회인 이유는?**
> "Stage 1 Walk가 4-level PT(L0~L3)를 순회하고 최종 데이터 접근까지 5번의 IPA를 참조한다. 각 IPA에 대해 Stage 2 Walk가 필요하고, Stage 2도 4-level이면 각각 최대 5회 메모리 접근. 따라서 5×5 = 25회. Bare Metal은 5회이므로 최악 5배 오버헤드다. 실제로는 TLB와 Page Walk Cache로 대부분 이보다 훨씬 적지만, 이 최악 케이스가 Huge Page 사용의 동기가 된다."

**Q: Shadow Page Table이 2-Stage보다 변환은 빠른데, 왜 전체 성능은 나쁠 수 있는가?**
> "Shadow PT는 VA→PA 1단계 변환이라 TLB miss 시 walk 자체는 빠르다. 하지만 Guest OS가 PT를 수정할 때마다 VM Exit이 발생하여 Hypervisor가 Shadow PT를 동기화해야 한다. VM Exit 비용은 수천 cycle이며, 멀티프로세스 워크로드에서 CR3 쓰기가 빈번하면 VM Exit이 폭발적으로 증가한다. 2-Stage는 TLB miss 시 최대 25회 접근이지만 PT 수정에 VM Exit이 발생하지 않는다. 이것이 EPT/ARM Stage 2가 표준이 된 이유다."

**Q: Stage 2가 최적화하기 어려운 이유는?**
> "Stage 1(VA→IPA)은 Guest OS가 관리하므로 프로세스별 Working Set이 명확하고 접근 패턴이 예측 가능해 prefetch와 캐시가 효과적이다. 반면 Stage 2(IPA→PA)는 Hypervisor가 관리하며, 각 VM의 IPA가 물리 메모리에 불연속 매핑되고, VM 생성/삭제/마이그레이션에 따라 배치가 변한다. 결과적으로 Stage 2 PT의 spatial locality가 낮고, VM 수 증가 시 TLB pressure도 증가한다. 이것이 latency/bandwidth 민감 시스템의 핵심 병목이다."

---
!!! warning "실무 주의점 — 2-stage translation 후 TLB invalidate 누락"
    **현상**: Guest 가 page 를 unmap/remap 했음에도 stale 한 IPA→PA 매핑으로 옛 데이터를 읽거나 잘못된 페이지에 write.

    **원인**: Stage-1 (guest OS) 와 Stage-2 (hypervisor) TLB 가 별도이고, IPI 기반 broadcast TLBI 가 모든 vCPU/PE 에 도달하지 않으면 일부 코어가 옛 entry 를 그대로 사용.

    **점검 포인트**: ARM `TLBI VMALLE1IS` / Intel `INVEPT` 발행 시점, vCPU 마이그레이션 직후 재발행 여부, ASID/VMID 재할당 정책.

## 핵심 정리

- **2단계 변환**: VA (guest virtual) → IPA (guest "physical", OS 관점) → PA (실제 물리). Stage 1 (OS) + Stage 2 (hypervisor).
- **Shadow PT (SW 방식, 구식)**: hypervisor가 VA→PA 직접 매핑하는 별도 page table 유지. Guest PT 변경마다 sync 필요 → 느림.
- **EPT/NPT (Intel/AMD)**, **Stage-2 (ARM)**: HW가 IPA→PA 자동 변환. **현재 표준**.
- **KSM**: 같은 내용의 메모리 페이지를 VM 간 공유 → memory deduplication.
- **Ballooning**: hypervisor가 guest OS에 메모리 반환 요청 (driver 협력).

## 다음 단계

- 📝 [**Module 03 퀴즈**](quiz/03_memory_virtualization_quiz.md)
- ➡️ [**Module 04 — I/O Virtualization**](04_io_virtualization.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../02_cpu_virtualization/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">CPU 가상화</div>
  </a>
  <a class="nav-next" href="../04_io_virtualization/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">I/O 가상화</div>
  </a>
</div>
