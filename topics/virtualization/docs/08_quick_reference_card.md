# Module 08 — Quick Reference Card

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🪟</span>
    <span class="chapter-back-text">Virtualization</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">★ Quick Reference</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-카드를-왜-쓰는가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-이-카드를-펼쳐야-할-3-시나리오">3. 작은 예 — 이 카드를 펼쳐야 할 3 시나리오</a>
  <a class="page-toc-link" href="#4-일반화-한-장-요약-과-트레이드오프-축">4. 일반화 — 한 장 요약</a>
  <a class="page-toc-link" href="#5-디테일-역사-주소-변환-io-스펙트럼-약어-체크리스트">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 카드를 끝까지 보면:

    - **Recall** 가상화 3 대 요소 (CPU / Memory / I/O) 와 각각의 SW→HW 진화 흐름을 즉시 회상한다.
    - **Apply** 면접/실무 질문에 11 개의 골든 룰 패턴으로 답한다.
    - **Identify** 시나리오 (production cloud / 데스크탑 / FaaS / multi-tenant) 에 맞는 가상화 모델을 식별한다.
    - **Justify** 트레이드오프 (성능 vs 격리, 공유 vs 전용) 의 _양면_ 을 항상 함께 정당화한다.
    - **Compare** VM / Container / MicroVM / Process 의 격리 boundary 와 startup 속도를 비교한다.

!!! info "사전 지식"
    - [Module 01-07](01_virtualization_fundamentals.md) — 모든 본문 모듈을 한 번씩 읽었을 것

---

## 1. Why care? — 이 카드를 왜 쓰는가

이 카드는 **개념 학습용이 아니라 _즉시 참조용_** 입니다. 면접에서 "가상화 트레이드오프 설명해보세요" 라는 한 줄 질문이 떨어졌을 때 _Module 01 부터 다시 읽을 시간이 없으므로_, 그 자리에서 **3 대 요소 → SW/HW 축 → 25 회 walk → IOMMU 격리** 의 흐름이 _한 호흡에_ 나와야 합니다. 또는 실무에서 "이 워크로드는 SR-IOV 가 맞나요 VirtIO 가 맞나요?" 같은 결정이 _10 분 안에_ 필요할 때, 트레이드오프 표 한 장이 정답을 빠르게 좁혀 줍니다.

이 카드를 안 펼치면 _면접 대답이 헤매고_, _실무 결정이 길어지고_, _Confluence 페이지를 5 개씩 열어야_ 합니다. 반대로 _한 번 외워두면_ 평생 씁니다 — 가상화의 도메인 어휘는 25 년간 거의 변하지 않았고, 새 기술 (Nitro, Firecracker, DPU) 도 _같은 축의 새 점_ 일 뿐입니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **Virtualization 마스터 = trade-off 의 모든 축 인지** ≈ **건축가** — 객실 / 침대 / 호텔 / 도시의 모든 옵션의 장단을 꿰뚫음.<br>
    VM / Container / microVM / process / bare-metal 의 _격리 / 성능 / density / migration / 보안_ trade-off 를 즉시 그리는 것이 마스터.

### 한 장 그림 — 가상화 = HW 추상화 + 자원 분할 + 격리

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

  3 개 column 모두 _SW → HW 지원_ 으로 진화했다는 공통 흐름이 있다.
  새 기술 (Nitro, DPU) 도 같은 column 의 _아래쪽 (HW 쪽)_ 에 한 점이 추가될 뿐.
```

### 왜 이렇게 설계됐는가 — Design rationale

이 카드의 모든 표는 **한 가지 원칙** 으로 구성됐습니다 — _개념 1 개당 1 표_, _표 1 개당 trade-off 의 _양쪽_ 모두 보이기_. 왜냐하면 면접/실무에서 가장 흔한 실수가 _"X 가 좋다"_ 라는 한 면만 보고 _"Y 의 비용"_ 을 못 말하는 것이기 때문입니다. 예: "SR-IOV 가 빠르다" → 못 한 말: "device share 불가, live migration 어려움". 이 카드의 모든 row 는 _두 칼럼_ 으로 그려져 있고, _한 칼럼만 인용하면 답이 _틀린_ 것_ 입니다.

---

## 3. 작은 예 — 이 카드를 펼쳐야 할 3 시나리오

가장 자주 마주칠 _3 가지 상황_ 과 _어느 표를 펼쳐야 하는지_ 의 trigger 매핑:

### 시나리오 A — "면접에서 가상화 질문이 떨어졌다"

```
면접관: "가상화의 3 대 요소를 설명해보세요."
        │
        ▼
   ▶ §5.2 [가상화 한 장 요약] 표 펼침
   ▶ §5.10 [면접 골든 룰] 의 골든 룰 1 + 2 (3대 요소 + Popek-Goldberg)
        │
        ▼
   답변 흐름:
   "CPU 가상화 (특권 명령어 trap + 인터럽트), 메모리 가상화 (VA→IPA→PA 2-stage),
    I/O 가상화 (에뮬레이션→VirtIO→SR-IOV→Pass-through). 세 column 모두
    SW → HW 지원으로 진화한 공통 흐름이 있다. Popek-Goldberg 3 조건 중
    효율성이 실용적 핵심 제약."
```

### 시나리오 B — "이 워크로드에 어느 가상화 모델?"

```
실무: "100 Gbps NIC 가 붙은 서버에 VM 10 개를 띄워야 합니다. SR-IOV? VirtIO?"
        │
        ▼
   ▶ §5.5 [I/O 가상화 스펙트럼] 표 펼침
   ▶ §5.7 [Strict vs Pass-through] 비교 표
   ▶ §5.13 [성능 최적화 체크리스트] 의 I/O 줄들
        │
        ▼
   결정:
   "100 Gbps line rate 가 필요 → SR-IOV VF passthrough.
    단, 격리 = IOMMU 의존이므로 VT-d 확인 + ACS isolation +
    Posted Interrupt + Huge Page 까지 같이 설정해야 실 성능 나옴.
    Live migration 이 필수면 vDPA 또는 hybrid (관리 NIC = virtio + 데이터 = SR-IOV)."
```

### 시나리오 C — "성능 저하 디버그 — 30% 느린데 baseline 이 없다"

```
실무: "VM 도입 후 throughput 이 30% 떨어졌는데 원인 모르겠음."
        │
        ▼
   ▶ §5.13 [성능 최적화 체크리스트] 펼침
   ▶ §6 [흔한 실수와 올바른 답변] 중 "가상화 = 성능 손해만" row
   ▶ §6 [DV 디버그 체크리스트] 의 baseline / VM Exit 측정 row
        │
        ▼
   순서:
   1. baseline 확보: bare-metal vs VM 의 cyclictest / fio / netperf
   2. exit 분포: `perf kvm stat` exits/sec, exit reason 분포
   3. EPT walk: TLB miss ratio
   4. virtio ring 부족 / vhost backend 비활성 / IRQ steal time
   원인 후보를 _숫자로_ 좁힌 다음 한 곳에 집중.
```

### Trigger 표 — 빠른 라우팅

| 입력 신호 | 펼칠 섹션 |
|---|---|
| "3 대 요소", "가상화 정의" | §5.2 가상화 한 장 요약 |
| "Type 1 / Type 2 / KVM 분류" | §5.6 Hypervisor 유형 |
| "ARM EL0/1/2/3", "VHE" | §5.3 ARM Exception Level |
| "VA→IPA→PA", "25 회 walk", "EPT/NPT" | §5.4 주소 변환 경로 |
| "VirtIO vs SR-IOV", "I/O 성능 트레이드오프" | §5.5 I/O 스펙트럼 |
| "Strict vs Passthrough", "context switch 4 vs 2" | §5.7 Strict vs Pass-through |
| "VM / Container / MicroVM 선택" | §5.8 VM vs Container vs MicroVM |
| 면접 질문 일반 | §5.10 면접 골든 룰 + §6 흔한 실수 |
| 이력서 prep | §5.14 이력서 연결 포인트 |
| 성능 튜닝 | §5.13 성능 최적화 체크리스트 |

!!! note "여기서 잡아야 할 두 가지"
    **(1) 카드는 _참조용_ 이지 _학습용_ 이 아님** — Module 01-07 을 한 번도 안 읽고 이 카드만 봐서는 깊이 답할 수 없습니다. 본문을 읽은 _후_ 인덱스로만 사용하세요.<br>
    **(2) Trigger 표가 _첫 30 초_ 를 결정** — 면접/실무에서 "어느 표를 펼칠 것인가" 의 결정이 _답의 절반_. 잘못된 표를 펼치면 답도 빗나갑니다.

---

## 4. 일반화 — 한 장 요약 과 트레이드오프 축

### 4.1 모든 트레이드오프의 _공통 축_

가상화 전체에서 등장하는 _서로 다른 표_ 들은 사실 **같은 4 개의 축** 의 다른 단면입니다:

```
                  격리 강도
                     ▲
                     │
   ┌─────────────────┼─────────────────┐
   │                 │                  │
   │ VM       MicroVM│ Container Process│
   │  ●         ●    │    ●        ●   │── density (서버당)
   │                 │                  │
   ├─────────────────┼─────────────────┤
   │ Strict          │  Pass-through    │
   │  ●              │       ●          │── I/O hop 수
   │                 │                  │
   ├─────────────────┼─────────────────┤
   │ Emulation       │  SR-IOV / VFIO   │
   │  ●              │       ●          │── 성능 (% of bare-metal)
   │                 │                  │
   ├─────────────────┼─────────────────┤
   │ Shadow PT       │  EPT/Stage-2 HW  │
   │  ●              │       ●          │── 메모리 변환 비용
   │                 │                  │
   └─────────────────┴─────────────────┘
                     │
                     ▼
                  성능 우선
```

이 4 축의 _같은 위치_ 에 있는 점들은 _대개 같이 등장_ 합니다 — 예: VM + Strict + Emulation + Shadow PT 가 "원조" production, MicroVM + Pass-through + SR-IOV + EPT 가 "Nitro 시대".

### 4.2 시스템 아키텍처 진화 (TechForum #54)

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

## 5. 디테일 — 역사, 주소 변환, I/O 스펙트럼, 약어, 체크리스트

### 5.1 시스템 아키텍처 진화 (TechForum #54)

(§4.2 와 동일. 참조용으로 다시 표시)

```
HW Only → Processor(FW) → +HW Accel → +OS(ARM-M)+MPU → +MMU(ARM-A) → +IOMMU+PEs+LLC → Virtualization
```

### 5.2 가상화 한 장 요약

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

### 5.3 ARM Exception Level

```
EL0 ─── User App      ──── SVC ────┐
                                     ▼
EL1 ─── Guest OS      ──── HVC ────┐
                                     ▼
EL2 ─── Hypervisor     ──── SMC ────┐
                                     ▼
EL3 ─── Secure Monitor (TrustZone)
```

### 5.4 주소 변환 경로

```
Bare Metal:  VA ──[1-Stage]──> PA              (최대 5회 메모리 접근)
가상화:      VA ──[Stage1]──> IPA ──[Stage2]──> PA  (최대 25회 메모리 접근)
```

| 단계 | 관리 | 최적화 |
|------|------|--------|
| Stage 1 (VA→IPA) | Guest OS (EL1) | 가능 (prefetch, 캐시) |
| Stage 2 (IPA→PA) | Hypervisor (EL2) | 어려움 (낮은 locality) — **핵심 병목** |

### 5.5 I/O 가상화 스펙트럼

```
성능   낮음 ◄──────────────────────────────────────► 높음
격리   높음 ◄──────────────────────────────────────► 낮음

  Emulation      VirtIO        SR-IOV      Pass-through
  (10~30%)      (50~80%)      (90~98%)     (95~100%)
  수정 불필요    드라이버 필요   HW 필요      1:1 전용
  공유 가능      공유 가능      VF 공유      공유 불가
```

### 5.6 Hypervisor 유형

| | Type 1 (Bare Metal) | Type 2 (Hosted) | KVM (하이브리드) |
|--|---------------------|-----------------|-----------------|
| 구조 | HW → Hypervisor → VM | HW → Host OS → Hypervisor → VM | HW → Linux+KVM → VM |
| 예시 | ESXi, Xen, Hyper-V | VirtualBox, VMware Workstation | KVM + QEMU |
| 용도 | 프로덕션 서버 | 개발/데스크탑 | 클라우드 (범용) |

### 5.7 Strict System vs Pass-through

| | Strict | Pass-through |
|--|--------|-------------|
| 원칙 | 모든 HW 접근 Hypervisor 경유 | 특정 디바이스에 VM 직접 접근 |
| Context Switch | 4회/I/O (EL0↔EL1↔EL2) | 2회/I/O (EL0↔EL1) |
| 메모리 | 2-stage 전체 적용 | Huge Page로 최소화 |
| 보안 | SW 중재 (강함) | HW 격리 (IOMMU 의존) |
| 성능 | 오버헤드 큼 | Bare metal 수준 |

### 5.8 VM vs Container vs MicroVM

| | VM | Container | MicroVM |
|--|-----|-----------|---------|
| 격리 | HW (Hypervisor) | OS (Namespace) | HW (KVM) |
| 부팅 | 초~분 | ms~초 | ~125ms |
| 크기 | GB | MB | ~5MB overhead |
| 보안 | 강함 | 커널 공유 위험 | 강함 |
| 밀도 | 수십/서버 | 수천/서버 | 수천/서버 |
| 용도 | 범용 서버 | 마이크로서비스 | FaaS/서버리스 |

### 5.9 관련 기술 약어 정리

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

### 5.10 면접 골든 룰

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

### 5.11 면접 스토리 흐름 (가상화 지식 활용)

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

### 5.12 이력서 연결 포인트

| 이력서 항목 | 면접 질문 | 핵심 답변 포인트 |
|------------|----------|----------------|
| IOMMU/SMMU DV | "IOMMU가 가상화에서 왜 중요한가?" | DMA 격리 = 가상화 전제 조건, AxUSER→StreamID로 VM identity, 2-stage translation |
| HW 가속기용 MMU | "메모리 가상화의 성능 병목은?" | 25회 최악 접근, Stage 2 locality 낮음, Huge Page + PWC로 완화 |
| AXI VIP 개발 | "AxUSER가 하는 역할은?" | 디바이스 트랜잭션에 VM 정체성 부여, IOMMU가 올바른 PT 선택하는 키 |
| SR-IOV/PCIe DV | "SR-IOV를 검증한 경험은?" | PF/VF 분리, VF 생성/할당/격리, IOMMU와의 연동 |
| 시스템 아키텍처 | "가상화가 필요한 이유는?" | 활용률 10%→60~80%, 격리, 스냅샷/마이그레이션 — Popek-Goldberg 3조건 |
| 클라우드/서버 | "클라우드 가상화 트렌드는?" | SW 중재→HW 보안(IOMMU, Nitro), Pass-through + HW 격리, MicroVM |

### 5.13 성능 최적화 체크리스트

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

!!! warning "실무 주의점 — virtualization overhead 측정 없이 도입 시 30% 성능 저하 인지 못함"
    **현상**: 가상화 도입 후 throughput/latency 가 native 대비 20~30% 저하되었는데, 비교 baseline 이 없어 SLA 위반의 원인을 application 코드로 오진.

    **원인**: VMEXIT, EPT walk, virtio ring copy, IOMMU translation, vCPU steal time 등 가상화 고유 오버헤드가 누적되지만 native 측정값과 직접 비교하지 않으면 정상값으로 오인.

    **점검 포인트**: bare-metal vs VM 의 cyclictest/fio/netperf baseline, `kvm_stat` 의 exits/sec, `perf kvm` 의 hot-path, guest `/proc/stat` 의 steal time, IOMMU translation cache hit rate.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Virtualization 은 항상 overhead 가 있다'"
    **실제**: VT-x + EPT + IOMMU 등 HW assist 로 modern virtualization 의 overhead 는 5-10% 수준입니다. 워크로드별로 _측정 후_ 도입 결정. 단, overhead = 0 이라는 의미가 아니라 _대부분 워크로드에 무시 가능_.<br>
    **왜 헷갈리는가**: 초기 SW-only 시대 (VMware ESX 1.0 등) 의 30%+ overhead 인상이 남아 있어서.

!!! danger "❓ 오해 2 — 'Shadow PT 가 더 좋다 (변환 1 회로 끝나니까)'"
    **실제**: Shadow PT 는 _변환 자체_ 는 빠르지만 _Guest 의 PT 수정마다 VM Exit_ 이 일어나 multi-process workload 에서 _2-Stage HW_ 보다 _확실히 느림_. 그래서 EPT/NPT 가 표준.<br>
    **왜 헷갈리는가**: "변환 횟수 = 성능" 의 단순화. _exit overhead_ 가 _walk 횟수_ 를 압도.

!!! danger "❓ 오해 3 — 'IOMMU 는 보안용이다'"
    **실제**: IOMMU 는 _세 가지 역할_ 을 동시에 합니다 — (1) 보안 (DMA 격리), (2) 주소 변환 (device 가 IOVA 를 사용), (3) **가상화의 _전제 조건_** (passthrough 시 device 가 VM 메모리만 보게 만듦). 한 면만 인용하면 답이 좁아짐.<br>
    **왜 헷갈리는가**: 마케팅 문구가 "secure DMA" 만 강조.

!!! danger "❓ 오해 4 — 'KVM 은 Type 2 이다'"
    **실제**: KVM 은 _구조적으로_ Type 2 모양 (Linux 위 module + QEMU user-space) 이지만 _성능과 동작_ 은 Type 1 에 근접. ARM VHE 이후에는 _HW 관점에서도_ Type 1 과 사실상 동일. **두 축 모델 (host OS 유무 / kernel 위치)** 로 보면 별도 칸 (Hybrid).<br>
    **왜 헷갈리는가**: 학술 분류는 Type 2, 시장은 Type 1 — 둘 중 하나만 인용.

!!! danger "❓ 오해 5 — 'Pass-through 는 보안 약화다'"
    **실제**: _IOMMU 없이는_ 약화이지만 IOMMU + Posted Interrupt + ACS isolation + (Nitro Card 같은 HW) 가 있으면 _SW 중재만큼 강한 격리_ 를 _bare-metal 성능_ 으로 얻습니다. 현대 클라우드의 표준.<br>
    **왜 헷갈리는가**: 10 년 전까지는 사실이었던 명제.

!!! danger "❓ 오해 6 — '가상화 = 성능 손해만'"
    **실제**: 가상화는 _서버 자원 활용률을 10% → 60~80% 로_ 끌어올립니다. 단순 단일 워크로드 성능만 보면 손해처럼 보이지만, _데이터센터 효율_ 관점에서는 _압도적 이득_.<br>
    **왜 헷갈리는가**: 단일 VM 의 throughput 만 비교하는 한 면.

!!! danger "❓ 오해 7 — 'VT-x 이전에는 가상화 불가'"
    **실제**: VMware 가 **Binary Translation (1998)** 으로 SW 우회 — Guest 의 sensitive 명령을 _실행 전 동적으로 trap-able 명령으로 치환_. 복잡/느렸지만 가능했음. VT-x (2005) 가 _근본적 HW 해결_ 을 했을 뿐.<br>
    **왜 헷갈리는가**: "x86 가상화 = VT-x" 라는 단순 매핑.

### DV 디버그 체크리스트 (이 카드가 가장 자주 쓰이는 실패 패턴)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 면접에서 "가상화의 3 대 요소" 답 못함 | 학습 부족 + 카드 인덱스 미숙 | §5.2 가상화 한 장 요약 + §5.10 골든 룰 1 |
| "Shadow PT 가 더 빠르다" 같은 단편적 답 | trade-off 의 _양면_ 인용 누락 | §6 흔한 실수 표 + §5.10 골든 룰 4 |
| 워크로드별 I/O 모델 선택 잘못 | I/O 스펙트럼 미숙지 | §5.5 + §5.7 종합 비교 |
| 가상화 도입 후 30% 저하 미인지 | baseline 측정 없음 | §5.13 + 위 실무 주의점 |
| KVM 의 분류 한쪽만 답 | hybrid 위치 미인지 | §5.6 + §5.10 골든 룰 8 |
| IOMMU 를 "보안용" 으로만 답 | 세 역할 미인지 | §5.10 골든 룰 7 |
| Firecracker = "작은 VM" 으로만 답 | device model 최소화의 본질 누락 | §5.8 + Module 07 §6 오해 5 |
| "Container 는 안전" 으로 일반화 | kernel 공유 boundary 약함 누락 | §5.8 + Module 07 §6 오해 1 |

### 흔한 실수와 올바른 답변

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

## 7. 핵심 정리 (Key Takeaways)

- **3 대 요소**: CPU / Memory / I/O — 모든 column 이 _SW → HW 지원_ 으로 진화한 공통 흐름. 새 기술도 같은 column 의 새 점.
- **Popek-Goldberg 3 조건**: Equivalence / Resource Control / **Efficiency** — 셋 중 _Efficiency_ 가 실용적 핵심 제약.
- **공통 축**: 격리 강도 ↔ 성능 / 공유 ↔ 전용. 표 형태가 달라도 _같은 축의 다른 단면_.
- **IOMMU 의 세 역할**: 보안 + 주소 변환 + **가상화의 _전제 조건_**. 한 면만 인용하면 답이 좁아짐.
- **트레이드오프는 항상 _양면_**: "X 가 좋다" 만 말하면 답이 틀린다. "X 의 이득 + Y 의 비용" 으로 양쪽 모두.

!!! warning "실무 주의점"
    - **카드는 인덱스, 본문은 Module 01-07** — 인덱스만 외우고 본문 안 읽으면 deep dive 가 무너집니다.
    - **trigger 표를 먼저 보고 첫 30 초 결정** — 잘못된 표를 펼치면 답도 빗나갑니다.
    - **양면 인용 강제** — 면접/실무 답변마다 "이득 + 비용" 의 _두 칼럼_ 을 모두 말하세요. 한쪽만 말하면 _즉시 follow-up_ 이 옵니다.

---

## 코스 마무리

[퀴즈](quiz/index.md) · [용어집](glossary.md) · 다음: [MMU](../../mmu/) (메모리 가상화 deep), [ARM Security](../../arm_security/) (EL2 hypervisor).

<div class="chapter-nav">
  <a class="nav-prev" href="../07_containers_and_modern/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">컨테이너와 현대 가상화</div>
  </a>
  <a class="nav-next" href="../quiz/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">퀴즈로 이동</div>
  </a>
</div>


--8<-- "abbreviations.md"
