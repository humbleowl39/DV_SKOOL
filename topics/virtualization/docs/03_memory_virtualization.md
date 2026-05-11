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
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-stage-1-2-page-table-walk-1-사이클">3. 작은 예 — 2-stage walk 1 사이클</a>
  <a class="page-toc-link" href="#4-일반화-shadow-pt-vs-2-stage-vs-passthrough">4. 일반화 — Shadow PT vs 2-Stage</a>
  <a class="page-toc-link" href="#5-디테일-주소-계층-tlb-huge-page-비교">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Trace** Guest VA → IPA → PA 의 2 단계 변환 흐름을 단계별로 추적할 수 있다.
    - **Distinguish** Shadow Page Table (SW) 과 EPT / NPT / Stage-2 (HW) 를 VM Exit 빈도 + 변환 단계 + 동기화 비용 관점에서 구분할 수 있다.
    - **Apply** Memory ballooning, KSM (Kernel Same-page Merging) 의 동기와 적용 시나리오를 적용할 수 있다.
    - **Justify** 왜 worst-case page walk 가 25 회인지 산식으로 설명할 수 있다.
    - **Identify** Stage 2 가 Stage 1 보다 최적화하기 어려운 구조적 이유를 식별할 수 있다.

!!! info "사전 지식"
    - [MMU 코스](../../mmu/) — page table walk, TLB 의 기본
    - [Module 01](01_virtualization_fundamentals.md), [Module 02](02_cpu_virtualization.md)

---

## 1. Why care? — 이 모듈이 왜 필요한가

가상화 환경의 latency / bandwidth 병목의 _대부분_ 이 메모리 가상화에서 옵니다. 100 Gbps NIC 의 throughput 이 30% 떨어지는 가장 흔한 원인이 Stage-2 TLB miss 의 page walk 비용입니다. AI training 클러스터의 step time 에 ms 단위로 끼어드는 노이즈도 IPA → PA mapping 에서 옵니다.

이 모듈을 건너뛰면 — 왜 huge page 가 가상화에서 _필수_ 인지, 왜 Shadow PT 가 사라지고 EPT 가 표준이 됐는지, 왜 IOMMU 와 CPU MMU 의 Stage-2 가 _같은 자료_ 를 공유하는지 — 모두 외워야 하는 사실이 됩니다. Worked example 의 25 회 산식 + Stage 2 의 locality 분석만 잡으면 나머지는 변형입니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **Memory Virtualization** = **주소록 2 단계 — 게스트가 본 주소 → 실제 호스트 주소** .<br>
    Guest OS 의 page table 도 _가상_ 이고, hypervisor 가 다시 host 물리 주소로 매핑. 결과: 같은 IPA 0x1000 이 VM0 과 VM1 에서 각자 다른 PA 를 가리킬 수 있음.

### 한 장 그림 — 2-Stage Translation

```
   Guest 프로세스        Guest OS              Hypervisor             실제 DRAM
   ─────────────        ─────────              ──────────             ─────────

       VA              VA → IPA                IPA → PA                  PA
                       (Stage 1)               (Stage 2)
                       Guest OS PT             Hypervisor PT
                       TTBR0_EL1               VTTBR_EL2
                       (EL1 관리)               (EL2 관리)
       │                │                       │
       └────────────────┴───────────────────────┴─────────────────────────▶
                                                                    실제 메모리 접근
```

### 왜 이 디자인인가 — Design rationale

세 가지 요구가 동시에 풀려야 했습니다.

1. **각 VM 이 자기가 0x0 부터 시작하는 PA 공간을 갖는 것처럼 느껴야** — Guest OS 가 자기 page table 을 자유롭게 수정.
2. **Hypervisor 가 실제 DRAM 의 어디든 자유롭게 VM 에 할당할 수 있어야** — 메모리 over-commit, dedup, balloning.
3. **Guest 의 PT 변경이 VM Exit 을 만들지 않아야** — Equivalence + Efficiency.

답이 **Stage 1 / Stage 2 의 _분리된_ page table** 입니다. Stage 1 은 Guest OS 가 자유롭게, Stage 2 는 Hypervisor 가 별도로. HW 의 MMU 가 둘을 _자동으로_ 합쳐서 walk 합니다 (Shadow PT 시대의 SW sync 가 사라짐).

---

## 3. 작은 예 — Stage-1 + Stage-2 page table walk 1 사이클

가장 단순한 시나리오. Guest VM 의 user-space 에서 `mov rax, [0x4_2000]` 한 줄. 이 한 번의 메모리 접근이 어떻게 2-stage walk 가 되고 worst-case 25 회 메모리 접근까지 갈 수 있는지 단계별로.

가정: 4-level page table (L0 / L1 / L2 / L3), 4 KB page, TLB miss.

```
                ┌─── Guest user 코드 ───┐
                │  mov rax, [0x4_2000] │  ← Guest VA = 0x4_2000
                └───────────┬───────────┘
                            │
   ┌────────────────────────┴──────────────────────────────────┐
   │ MMU (HW) — 2-stage walk                                   │
   │                                                           │
   │ Step A: Stage-1 walk 시작                                 │
   │   guest TTBR0 = IPA 0xA_0000  (L0 table 의 IPA)           │
   │      ┌── 이 IPA 도 변환 필요 ──┐                          │
   │      │ Stage-2 walk for 0xA_0000 (4 회)                  │
   │      │   → PA 0x10_0000 의 L0 table                       │
   │      └──────────────────────────┘                         │
   │   L0 entry 읽기 → IPA 0xB_0000 (L1 table)                 │
   │      ┌── Stage-2 walk for 0xB_0000 (4 회)                 │
   │      │   → PA 0x11_0000                                   │
   │      └──────────────────────────┘                         │
   │   L1 → IPA 0xC_0000 → Stage-2 (4 회) → PA 0x12_0000       │
   │   L2 → IPA 0xD_0000 → Stage-2 (4 회) → PA 0x13_0000       │
   │   L3 → final IPA 0xE_2000  ⭐                             │
   │                                                           │
   │ Step B: 최종 IPA → PA                                     │
   │   Stage-2 walk for 0xE_2000 (4 회) → PA 0x14_2000         │
   │                                                           │
   │ Step C: 실제 메모리 read at PA 0x14_2000  → rax 로 로드   │
   └───────────────────────────────────────────────────────────┘
```

| Step | 무엇이 | 메모리 접근 횟수 | 누계 |
|---|---|---|---|
| A1 | TTBR0 의 IPA → PA 변환 (Stage-2 walk: L0/L1/L2/L3 = 4 회) | 4 | 4 |
| A2 | Stage-1 L0 entry 읽기 | 1 | 5 |
| A3 | L0 entry 의 IPA → PA 변환 (Stage-2 walk) | 4 | 9 |
| A4 | Stage-1 L1 entry 읽기 | 1 | 10 |
| A5 | L1 entry 의 IPA → PA 변환 (Stage-2 walk) | 4 | 14 |
| A6 | Stage-1 L2 entry 읽기 | 1 | 15 |
| A7 | L2 entry 의 IPA → PA 변환 (Stage-2 walk) | 4 | 19 |
| A8 | Stage-1 L3 entry 읽기 | 1 | 20 |
| B | 최종 IPA → PA 변환 (Stage-2 walk) | 4 | 24 |
| C | 실제 데이터 읽기 | 1 | **25** |

**산식**: 5 (Stage-1 의 5 번 IPA 참조: L0 base + L0/L1/L2/L3 walk + final) × 5 (각 Stage-2 walk: 4 + 1) = **25 회**.

```c
/* HW MMU 가 묵묵히 하는 일 — pseudo-C 로 옮긴 모습. */
pa_t walk_2stage(va_t va, ttbr_t guest_ttbr_ipa, vttbr_t hyp_vttbr_pa) {
    pa_t   l0_pa = stage2_walk(guest_ttbr_ipa, hyp_vttbr_pa);  /* 4 access */
    ipa_t  l0_ipa = mem_read(l0_pa + idx0(va));                /* 1 access */
    pa_t   l1_pa = stage2_walk(l0_ipa, hyp_vttbr_pa);          /* 4 access */
    ipa_t  l1_ipa = mem_read(l1_pa + idx1(va));                /* 1 */
    pa_t   l2_pa = stage2_walk(l1_ipa, hyp_vttbr_pa);          /* 4 */
    ipa_t  l2_ipa = mem_read(l2_pa + idx2(va));                /* 1 */
    pa_t   l3_pa = stage2_walk(l2_ipa, hyp_vttbr_pa);          /* 4 */
    ipa_t  data_ipa = mem_read(l3_pa + idx3(va));              /* 1 */
    pa_t   data_pa = stage2_walk(data_ipa, hyp_vttbr_pa);      /* 4 */
    return data_pa;                                             /* + 1 final read */
}
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) Bare metal 의 5 회가 가상화에서 25 회 — 5 배 worst-case.** 실제로는 TLB hit + Page Walk Cache (PWC) 로 훨씬 적게 가지만, miss 시 이 cliff 가 _존재한다_ 는 게 huge page 의 동기.<br>
    **(2) Stage-1 의 _각 entry_ 가 IPA 라는 게 핵심** — 그래서 Stage-1 walk 의 _모든 단계마다_ Stage-2 가 끼어듭니다. Stage-1 만 4 회가 아니라 _5 × Stage-2_ 가 됩니다.

---

## 4. 일반화 — Shadow PT vs 2-Stage vs Passthrough

§3 의 25 회 cliff 를 어떻게 줄이느냐에 따라 3 가지 길이 갈립니다.

### 4.1 한 장 비교

| 방식 | 변환 단계 | VM Exit 빈도 | TLB miss 비용 | 시기 |
|---|---|---|---|---|
| **Shadow PT (SW)** | 1 단계 (VA → PA) | **높음** (PT 수정마다) | 낮음 (1-stage walk) | VT-x 이전 |
| **2-Stage (HW)** | 2 단계 (VA → IPA → PA) | 낮음 (Stage 2 만 관리) | **높음** (worst 25 회) | EPT / NPT / Stage-2 — 표준 |
| **Pass-through + Huge Page** | 2 단계 (but 거의 1:1 / huge mapping) | 최소 | 낮음 (huge page 가 walk 깊이 단축) | 고성능 I/O (NIC, GPU) |

### 4.2 핵심 trade-off — 변환 단계 vs VM Exit

```
Shadow PT 가 더 빠를 거 같지만 (1-stage)
  ────────────────────────────────────────
  Guest 가 PT 를 수정할 때마다 VM Exit 발생
  → PT 수정이 잦은 워크로드 (멀티프로세스, fork, mmap) 에서 폭발
  → 누적된 VM Exit 비용이 25 회 walk 보다 크다

2-Stage 는 worst-case walk 가 25 회지만
  ────────────────────────────────────
  Guest 가 PT 를 _자유롭게_ 수정 (VM Exit 없음)
  → 평균적으로 훨씬 빠름
  → TLB + PWC 가 cliff 를 평탄화
```

이 trade-off 의 균형점이 워크로드별로 다르고, 그래서 huge page / NUMA-aware allocation / Pass-through 같은 추가 도구가 동시에 쓰입니다.

### 4.3 누가 무엇을 관리하나

| 주체 | 관리하는 변환 | 알고 있는 것 | 모르는 것 |
|------|-------------|------------|----------|
| **Guest OS** (EL1) | VA → IPA (Stage 1) | 자기 VM 의 가상 메모리 레이아웃 | IPA 가 실제 PA 가 아니라는 것 |
| **Hypervisor** (EL2) | IPA → PA (Stage 2) | 전체 물리 메모리 + 모든 VM 의 IPA 매핑 | Guest 프로세스의 VA |

이 분리가 곧 가상화의 격리 모델이고, 깨지는 순간 보안 / 격리도 깨집니다.

---

## 5. 디테일 — 주소 계층, TLB, Huge Page, 비교

### 5.1 왜 메모리 가상화가 필요한가

#### Bare Metal 에서의 메모리 관리

```
OS 가 물리 메모리를 직접 관리:

  VA ──[Page Table]──> PA
  (OS 가 소유)          (실제 DRAM)

  OS 는 전체 물리 메모리를 알고 있음
  → VA → PA 변환만 하면 됨 (1 단계)
```

#### 가상화 환경에서의 문제

```
VM0 의 Guest OS: "나는 4GB 물리 메모리를 갖고 있다"
VM1 의 Guest OS: "나도 4GB 물리 메모리를 갖고 있다"
실제 물리 DRAM: 8GB

문제:
  - 두 Guest OS 모두 자기가 PA 0x0~0xFFFFFFFF 을 소유한다고 생각
  - 하지만 같은 물리 주소를 두 VM 이 쓰면 데이터 충돌
  - Guest OS 가 직접 페이지 테이블을 관리하면 → 다른 VM 메모리 접근 가능

해결: Guest OS 가 보는 "물리 주소" 는 가짜 (IPA)
      실제 PA 로의 변환은 Hypervisor 가 담당
```

### 5.2 주소 변환 계층 구조

```
┌────────────────────────────────────────────────┐
│                 Guest 프로세스                   │
│  VA (Virtual Address)                           │
│  각 프로세스가 보는 주소                          │
└────────────┬───────────────────────────────────┘
             │ Stage 1 Translation
             │ (Guest OS 의 Page Table, EL1 관리)
             ▼
┌────────────────────────────────────────────────┐
│              Guest OS                           │
│  IPA (Intermediate Physical Address)            │
│  Guest OS 가 "물리 주소" 라고 믿는 주소           │
│  실제로는 Hypervisor 가 만든 가상의 물리 공간      │
└────────────┬───────────────────────────────────┘
             │ Stage 2 Translation
             │ (Hypervisor 의 Page Table, EL2 관리)
             ▼
┌────────────────────────────────────────────────┐
│           실제 하드웨어                          │
│  PA (Physical Address)                          │
│  실제 DRAM 주소                                  │
└────────────────────────────────────────────────┘
```

### 5.3 방법 1: Shadow Page Table (SW 방식)

#### 개념

Hypervisor 가 VA → PA 를 직접 변환하는 "그림자" 페이지 테이블을 유지.

```
Guest OS 의 PT     Shadow PT        실제 사용
(VA → IPA)        (VA → PA)
┌──────────┐     ┌──────────┐
│VA:0x1000 │     │VA:0x1000 │
│→IPA:0x5000│    │→ PA:0xA000│ ◄── MMU 가 실제로 사용하는 것
├──────────┤     ├──────────┤
│VA:0x2000 │     │VA:0x2000 │
│→IPA:0x6000│    │→ PA:0xB000│
└──────────┘     └──────────┘
                      ▲
                      │
                 Hypervisor 가
                 Guest PT 변경 시마다
                 Shadow PT 를 동기화
```

#### 동작 원리

1. Guest OS 가 자기 Page Table (VA → IPA) 수정 시도
2. Hypervisor 가 **trap** (CR3 / TTBR 쓰기 감지)
3. Guest PT 의 IPA 를 실제 PA 로 변환하여 Shadow PT 업데이트
4. **MMU 에는 Shadow PT 를 로드** — HW 는 VA → PA 1 단계 변환만 수행

#### 성능 문제

```
Guest OS 가 Page Table 을 수정할 때마다:
  1. VM Exit (trap) 발생                    ← 수천 사이클
  2. Hypervisor 가 Guest PT 읽기             ← 메모리 접근
  3. IPA → PA 변환                          ← 메모리 접근
  4. Shadow PT 업데이트                     ← 메모리 접근
  5. VM Entry (Guest 복귀)                  ← 수천 사이클

컨텍스트 스위치마다 발생 (프로세스 전환 = PT 교체)
→ 프로세스가 많은 워크로드에서 심각한 오버헤드
```

| 장점 | 단점 |
|------|------|
| MMU 는 1 단계 변환만 (성능 좋음) | Guest PT 변경마다 VM Exit |
| HW 지원 불필요 | Hypervisor 복잡도 높음 |
| | 메모리 추가 사용 (Shadow PT 공간) |

### 5.4 방법 2: 2-Stage Translation (HW 방식)

#### 개념 (EPT / ARM Stage 1+2)

HW 가 2 단계 변환을 직접 수행. Shadow PT 불필요.

```
MMU 가 자동으로 2 단계 수행:

  VA ──[Stage 1 PT]──> IPA ──[Stage 2 PT]──> PA
       (Guest OS 관리)        (Hypervisor 관리)

  Guest OS 는 자기 PT 를 자유롭게 수정 가능
  → VM Exit 불필요! (Hypervisor trap 없음)
  → Hypervisor 는 Stage 2 PT 만 관리
```

#### Page Table Walk 과정 (4-Level PT 기준)

```
VA 가 주어지면:

Stage 1 Walk (Guest OS 의 PT):
  TTBR(EL1) → L0 table → L1 table → L2 table → L3 table → IPA

  하지만! 각 테이블 주소도 IPA 이므로 Stage 2 변환 필요:

Stage 1 + Stage 2 Combined Walk:
  TTBR(EL1) 의 IPA 를 PA 로 변환 (Stage 2)
    → L0 table 읽기
  L0 entry 의 IPA 를 PA 로 변환 (Stage 2)
    → L1 table 읽기
  L1 entry 의 IPA 를 PA 로 변환 (Stage 2)
    → L2 table 읽기
  L2 entry 의 IPA 를 PA 로 변환 (Stage 2)
    → L3 table 읽기
  최종 IPA 를 PA 로 변환 (Stage 2)
    → 최종 PA 획득
```

#### Worst-Case 메모리 접근 횟수

§3 의 산식 그대로:

```
4-level Stage 1 + 4-level Stage 2:

Stage 1 의 각 레벨 접근 시 Stage 2 walk 필요:
  Stage 1 L0 접근: Stage 2 walk (최대 4 회) + 1 회 = 5 회
  Stage 1 L1 접근: Stage 2 walk (최대 4 회) + 1 회 = 5 회
  Stage 1 L2 접근: Stage 2 walk (최대 4 회) + 1 회 = 5 회
  Stage 1 L3 접근: Stage 2 walk (최대 4 회) + 1 회 = 5 회
  최종 데이터 접근: Stage 2 walk (최대 4 회) + 1 회 = 5 회

최악의 경우: 5 × 5 = 25 회 메모리 접근! (Bare Metal 은 5 회)
```

#### TLB 가 핵심인 이유

```
TLB Hit:  VA → PA 즉시 변환 (1 cycle)
TLB Miss: 최대 25 회 메모리 접근 (수백 cycle)

→ TLB Hit Rate 가 가상화 성능의 핵심 결정 요소
→ TLB 크기와 캐싱 전략이 매우 중요
```

### 5.5 Stage 1 vs Stage 2 최적화 비교

TechForum 슬라이드에서 강조한 핵심 포인트.

| 항목 | Stage 1 (VA → IPA) | Stage 2 (IPA → PA) |
|------|-------------------|-------------------|
| 관리 주체 | Guest OS (EL1) | Hypervisor (EL2) |
| 접근 패턴 | 예측 가능 (프로세스별 locality) | 예측 어려움 (VM 간 물리 메모리 분산) |
| 최적화 | Prefetch, 캐시 구조 활용 가능 | **어려움** — 낮은 locality |
| TLB 효과 | 높음 (Working set 이 명확) | **낮음** (VM 간 간섭, 큰 주소 공간) |

```
Stage 2 가 병목인 이유:

  VM0: IPA 0x0000 → PA 0x1_0000  (물리 메모리 앞쪽)
  VM1: IPA 0x0000 → PA 0x8_0000  (물리 메모리 뒤쪽)

  Hypervisor 가 VM 을 배치할 때 물리 메모리가 불연속적
  → Stage 2 PT 의 locality 가 낮음
  → TLB miss 시 page walk 비용이 큼
  → 이것이 latency / bandwidth 민감 시스템의 핵심 병목
```

### 5.6 Huge Page 로 TLB 효율 개선

```
4KB Page:  TLB 1 entry = 4KB 커버
2MB Page:  TLB 1 entry = 2MB 커버  (512 배)
1GB Page:  TLB 1 entry = 1GB 커버  (262144 배)

가상화에서 Huge Page 효과:
  - Stage 2 PT 깊이 감소 (4-level → 2-level for 1GB)
  - TLB miss 시 walk 횟수 감소
  - TechForum 슬라이드 "Huge page allocation (1GB) to HPA" 가 바로 이것
```

#### Huge Page + Pass-through 시나리오

```
STEP 1: Hypervisor 가 1GB Huge Page 를 VM 에 할당
        → Stage 2 변환이 거의 1:1 매핑
        → TLB 1 entry 로 1GB 전체 커버

STEP 2: User-space 앱이 HPA (Huge Page Area) 위에서 직접 동작
        → Stage 1 도 Huge Page 사용 시 TLB pressure 최소화

효과: 2-stage translation 의 최악 시나리오 (25 회) 거의 발생 안 함
```

### 5.7 메모리 가상화 방식 비교 요약

| 항목 | Shadow PT | 2-Stage (EPT/ARM) | Pass-through + Huge Page |
|------|----------|-------------------|-------------------------|
| VM Exit 빈도 | 높음 (PT 수정마다) | 낮음 (Stage 2 만 관리) | 최소 |
| MMU 변환 단계 | 1 단계 (VA→PA) | 2 단계 (VA→IPA→PA) | 2 단계 (but 거의 1:1) |
| TLB miss 비용 | 낮음 (1-stage walk) | 높음 (최대 25 회) | 낮음 (Huge Page) |
| 구현 복잡도 | 높음 (동기화) | 낮음 (HW 지원) | 중간 (IOMMU 설정) |
| 격리 수준 | 높음 | 높음 | 디바이스 단위 |
| 주 사용처 | 레거시 (VT-x 이전) | 현대 범용 가상화 | 고성능 I/O (NIC, GPU) |

### 5.8 보조 기법 — Ballooning 과 KSM

| 기법 | 무엇을 하나 | 동기 |
|---|---|---|
| **Memory ballooning** | Hypervisor 가 guest balloon driver 에 "메모리 반환 요청" → guest 가 page 를 free → hypervisor 가 회수 | over-commit (전체 VM 의 메모리 합 > 물리 DRAM) |
| **KSM (Kernel Same-page Merging)** | 같은 내용의 page 를 VM 들이 _공유_ — copy-on-write 로 분기 | OS 이미지 / library 같은 _중복 데이터_ deduplication |

둘 다 SW 정책. HW 는 그대로지만 _hypervisor 가 Stage-2 mapping 을 동적으로 바꿔서_ 효과를 만듭니다.

### 5.9 면접 단골 Q&A

**Q: 2-stage translation 에서 최악의 메모리 접근이 25 회인 이유는?**

> "Stage 1 Walk 가 4-level PT (L0~L3) 를 순회하고 최종 데이터 접근까지 5 번의 IPA 를 참조한다. 각 IPA 에 대해 Stage 2 Walk 가 필요하고, Stage 2 도 4-level 이면 각각 최대 5 회 메모리 접근. 따라서 5 × 5 = 25 회. Bare Metal 은 5 회이므로 최악 5 배 오버헤드다. 실제로는 TLB 와 Page Walk Cache 로 대부분 이보다 훨씬 적지만, 이 최악 케이스가 Huge Page 사용의 동기가 된다."

**Q: Shadow Page Table 이 2-Stage 보다 변환은 빠른데, 왜 전체 성능은 나쁠 수 있는가?**

> "Shadow PT 는 VA → PA 1 단계 변환이라 TLB miss 시 walk 자체는 빠르다. 하지만 Guest OS 가 PT 를 수정할 때마다 VM Exit 이 발생하여 Hypervisor 가 Shadow PT 를 동기화해야 한다. VM Exit 비용은 수천 cycle 이며, 멀티프로세스 워크로드에서 CR3 쓰기가 빈번하면 VM Exit 이 폭발적으로 증가한다. 2-Stage 는 TLB miss 시 최대 25 회 접근이지만 PT 수정에 VM Exit 이 발생하지 않는다. 이것이 EPT / ARM Stage 2 가 표준이 된 이유다."

**Q: Stage 2 가 최적화하기 어려운 이유는?**

> "Stage 1 (VA→IPA) 은 Guest OS 가 관리하므로 프로세스별 Working Set 이 명확하고 접근 패턴이 예측 가능해 prefetch 와 캐시가 효과적이다. 반면 Stage 2 (IPA→PA) 는 Hypervisor 가 관리하며, 각 VM 의 IPA 가 물리 메모리에 불연속 매핑되고, VM 생성 / 삭제 / 마이그레이션에 따라 배치가 변한다. 결과적으로 Stage 2 PT 의 spatial locality 가 낮고, VM 수 증가 시 TLB pressure 도 증가한다. 이것이 latency / bandwidth 민감 시스템의 핵심 병목이다."

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Stage 2 가 켜지면 guest 가 자동으로 격리된다'"
    **실제**: Stage 2 가 켜져도 hypervisor 가 page table 을 잘못 채우면 cross-VM access 가능. 격리 = HW + SW 정책 정확성.<br>
    **왜 헷갈리는가**: "기능 켜짐 = 안전" 의 직관. 정책 SW 가 critical.

!!! danger "❓ 오해 2 — 'TLB miss 는 항상 25 회 접근이다'"
    **실제**: 25 회는 worst case. Page Walk Cache (PWC), 부분 TLB hit, huge page 등으로 평균은 훨씬 적다. 그러나 cliff 는 _존재한다_ 는 게 huge page 의 동기.<br>
    **왜 헷갈리는가**: "최악 = 평균" 으로 오해.

!!! danger "❓ 오해 3 — 'IPA = PA 의 별칭이다'"
    **실제**: IPA 는 Guest 가 _PA 라고 믿는 주소_ 이지만, hypervisor 가 어디로든 매핑할 수 있는 _가상_ 공간. 같은 IPA 0x1000 이 VM0 / VM1 에서 다른 PA 를 가리킨다.<br>
    **왜 헷갈리는가**: 이름의 "Physical" 단어.

!!! danger "❓ 오해 4 — 'EPT 와 NPT 는 호환된다'"
    **실제**: 동작은 같지만 자료구조 / VMCS 필드 / fault format 모두 다름. KVM / Xen 이 vendor 분기로 처리.<br>
    **왜 헷갈리는가**: "둘 다 2-stage HW" 라는 추상의 같음.

!!! danger "❓ 오해 5 — 'TLB invalidate 는 한 vCPU 에만 하면 된다'"
    **실제**: ARM `TLBI VMALLE1IS` / Intel `INVEPT` 는 inner-shareable broadcast 가 필요. IPI 가 모든 vCPU / PE 에 도달하지 않으면 일부 코어가 stale entry 사용 → silent corruption.<br>
    **왜 헷갈리는가**: bare metal 의 TLBI 가 local 만으로 충분했던 경험.

### DV 디버그 체크리스트 (Memory 가상화 brings up)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Guest 부팅 직후 page fault 폭주 | Stage-2 PT 의 read 권한 미설정 | VTTBR / EPT pointer, page entry 의 RWX |
| Guest 가 unmap 한 page 의 옛 데이터 read | TLBI broadcast 누락 | `TLBI VMALLE1IS` 발행 시점, ASID/VMID 재할당 |
| 멀티프로세스 워크로드에서 throughput 50% 저하 | Shadow PT 모드로 fall-back? | KVM 의 `mmu_pte_zap` 빈도, EPT enable 여부 |
| `mov rax, [guest_va]` 가 wrong PA 참조 | Stage-2 가 다른 VM 영역으로 매핑 | hypervisor 의 IPA→PA 매핑 표, VMID isolation |
| TLB hit 율 측정 95% 인데 throughput 그대로 | PWC miss 가 25 회 walk 유발 | huge page 적용, `/proc/meminfo` HugePages |
| Live migration 후 silent corruption | dirty bit tracking 누락 | EPT D-bit, PML buffer flush, write-protect race |
| `INVEPT` 호출했는데 stale 매핑 그대로 | INVEPT type (single-context vs all-context) 잘못 | KVM `vmx_flush_tlb` 의 type 인자 |
| Ballooning 후 guest crash | balloon driver 가 hypervisor PT 와 desync | balloon page 의 Stage-2 entry, guest 의 free list |

---

## 7. 핵심 정리 (Key Takeaways)

- **2 단계 변환**: VA (guest virtual) → IPA (guest "physical") → PA (실제 물리). Stage 1 (OS) + Stage 2 (hypervisor).
- **Worst-case 25 회 walk**: 5 × 5 — Stage-1 의 5 번 IPA 참조 × 각 Stage-2 4 + 1.
- **Shadow PT (구식)**: VA→PA 직접, 변환은 빠르나 PT 수정마다 VM Exit → 멀티프로세스에 약함.
- **EPT / NPT / Stage-2 (HW, 표준)**: 2-stage 자동 walk, VM Exit 없음, 대신 worst-case 25 회 cliff.
- **Huge Page = 가상화의 필수 도구**: 4 KB → 2 MB / 1 GB 로 TLB pressure + walk 깊이 모두 감소.
- **KSM / Ballooning**: SW 정책으로 over-commit / dedup. Stage-2 mapping 의 동적 조작.

!!! warning "실무 주의점"
    - **2-stage translation 후 TLB invalidate 누락** 이 silent corruption 1 위 원인 — `TLBI VMALLE1IS` / `INVEPT` 시점, vCPU 마이그레이션 직후 재발행 여부.
    - **Huge page 미적용** 이 성능 병목의 80% — `/proc/meminfo`, `numactl --hardware`, transparent huge page 정책.
    - **Live migration 의 dirty tracking** 은 PML / write-protect / fault 모두 race 가능 — `KVM_CAP_MANUAL_DIRTY_LOG_PROTECT` 와 last round throttle 확인.

---

## 다음 모듈

→ [Module 04 — I/O Virtualization](04_io_virtualization.md): CPU + Memory 의 가상화 모델은 잡았으니, 이제 _디바이스_ 가상화 — Emulation / VirtIO / SR-IOV / Pass-through.

[퀴즈 풀어보기 →](quiz/03_memory_virtualization_quiz.md)

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


--8<-- "abbreviations.md"
