# Module 01 — Virtualization Fundamentals

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🪟</span>
    <span class="chapter-back-text">Virtualization</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 01</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#왜-가상화가-필요한가">왜 가상화가 필요한가?</a>
  <a class="page-toc-link" href="#가상화의-핵심-원리-추상화-계층">가상화의 핵심 원리: 추상화 계층</a>
  <a class="page-toc-link" href="#가상화의-3대-요소">가상화의 3대 요소</a>
  <a class="page-toc-link" href="#popek-goldberg-가상화-조건-1974">Popek-Goldberg 가상화 조건 (1974)</a>
  <a class="page-toc-link" href="#특권-명령어와-trap">특권 명령어와 Trap</a>
  <a class="page-toc-link" href="#가상화의-역사-간략">가상화의 역사 (간략)</a>
  <a class="page-toc-link" href="#qa">Q&A</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Define** 가상화의 정의와 동기 (격리, 효율, multi-tenant) 설명
    - **Distinguish** Full / Para / HW-assisted virtualization
    - **Identify** Virtualization 적합/부적합 시나리오

!!! info "사전 지식"
    - OS 기본 (process, kernel/user mode)
    - CPU 권한 모드

!!! tip "💡 이해를 위한 비유"
    **Virtualization** ≈ **호텔 객실 (각 손님이 다른 OS 같은 환경)**

    한 hardware 위에 여러 guest OS 가 마치 각자 hardware 를 갖는 것처럼 동작. hypervisor = 호텔 매니저.

---

## 핵심 개념
**가상화 = 물리 하드웨어 자원을 추상화하여, 하나의 물리 머신 위에 여러 독립된 실행 환경(VM)을 만드는 기술. CPU, 메모리, I/O를 소프트웨어로 분할/공유/격리한다.**

!!! danger "❓ 흔한 오해"
    **오해**: Virtualization = software 만의 영역

    **실제**: Modern virtualization 은 HW assist (Intel VT-x, AMD-V, ARM EL2) 가 핵심. SW 만으로는 trap-and-emulate overhead 가 ↑.

    **왜 헷갈리는가**: "virtual = soft" 라는 명칭 직관. 실제로는 HW + SW 협업.
---

## 왜 가상화가 필요한가?

### 가상화 없는 세계의 문제

```
물리 서버 1대 = OS 1개 = 서비스 1개

  서버 A: 웹 서버 (CPU 사용률 10%)
  서버 B: DB 서버 (CPU 사용률 15%)
  서버 C: 메일 서버 (CPU 사용률 5%)

  → 3대 서버 평균 사용률: 10% (나머지 90%는 낭비)
  → 서비스마다 물리 서버 구매 필요
  → 서버 간 격리는 되지만, 비용이 선형 증가
```

### 가상화가 해결하는 것

| 문제 | 가상화의 해결 |
|------|-------------|
| 낮은 자원 활용률 | 하나의 물리 머신에 여러 VM → 활용률 60~80%로 향상 |
| 서버 과다 | VM 통합(consolidation)으로 물리 서버 수 감소 |
| 격리 부재 | VM 간 메모리/프로세스 완전 격리 |
| 환경 의존성 | 각 VM이 독립 OS → 서로 다른 환경 공존 |
| 복구 어려움 | VM 스냅샷/마이그레이션으로 빠른 복구/이동 |
| 개발/테스트 | 동일 HW에서 여러 OS/환경 즉시 생성 |

---

## 가상화의 핵심 원리: 추상화 계층

### 일반 시스템 vs 가상화 시스템

```
[ 일반 시스템 ]                  [ 가상화 시스템 ]

  Application                     App A    App B    App C
      │                            │        │        │
      │                           OS A     OS B     OS C   (Guest OS)
      │                            │        │        │
      OS                          ─┴────────┴────────┴─
      │                           Hypervisor (VMM)
      │                                │
   Hardware                        Hardware
```

**핵심**: Hypervisor가 HW와 Guest OS 사이에 위치하여:
1. **HW 자원을 분할** — 각 VM에 CPU 코어, 메모리, I/O 할당
2. **접근을 중재** — Guest OS의 특권 명령어를 가로채서 처리
3. **격리를 보장** — VM A가 VM B의 메모리에 접근 불가

---

## 가상화의 3대 요소

하드웨어는 크게 3가지 자원으로 구성되고, 각각 다른 방식으로 가상화된다:

```
┌──────────────────────────────────────────────┐
│              Virtualization                   │
├──────────────┬──────────────┬────────────────┤
│     CPU      │   Memory     │      I/O       │
│  가상화       │   가상화      │    가상화       │
├──────────────┼──────────────┼────────────────┤
│특권 명령어    │주소 공간      │디바이스 접근    │
│trap/emulate  │2-stage 변환  │emulation /     │
│HW assist     │shadow PT     │passthrough     │
│(VT-x, ARM)  │(EPT, NPT)   │(SR-IOV, VFIO)  │
└──────────────┴──────────────┴────────────────┘
```

| 자원 | 가상화 대상 | 핵심 과제 |
|------|-----------|----------|
| **CPU** | 특권 명령어 실행, 인터럽트 처리 | Guest OS가 직접 HW 제어 못하게 하면서 성능 유지 |
| **Memory** | 주소 변환, 메모리 격리 | VM마다 독립 주소 공간 제공, 변환 오버헤드 최소화 |
| **I/O** | 디바이스 접근, DMA | 디바이스 공유 vs 전용 할당의 트레이드오프 |

---

## Popek-Goldberg 가상화 조건 (1974)

가상화가 올바르게 동작하기 위한 3가지 이론적 조건:

### 1. 동등성 (Equivalence)
> VM에서 실행한 프로그램은 bare metal에서 실행한 것과 동일한 결과를 내야 한다.

```
예외: 타이밍 차이, 자원 가용량 차이는 허용
      (VM은 물리 머신의 일부 자원만 사용하므로)
```

### 2. 자원 제어 (Resource Control)
> Hypervisor는 모든 HW 자원을 완전히 제어해야 한다. Guest OS가 자원을 독점하거나 빼앗을 수 없어야 한다.

```
예: Guest OS가 다른 VM의 메모리를 접근하려 하면
    → Hypervisor가 trap하여 차단
```

### 3. 효율성 (Efficiency)
> 대부분의 Guest 명령어는 Hypervisor 개입 없이 HW에서 직접 실행되어야 한다.

```
예: 일반 산술/논리 연산 (ADD, MUL, AND...)
    → Hypervisor가 매번 가로채면 성능 재앙
    → 특권 명령어만 trap, 나머지는 직접 실행
```

### 왜 중요한가?

| 조건 | 위반 시 |
|------|--------|
| 동등성 | Guest 프로그램이 bare metal과 다른 결과 → 신뢰 불가 |
| 자원 제어 | 악의적 Guest가 다른 VM 메모리 접근 → 보안 붕괴 |
| 효율성 | 모든 명령어를 에뮬레이션 → 성능 100배 이상 저하 |

---

## 특권 명령어와 Trap

### Privileged vs Sensitive Instructions

```
모든 CPU 명령어
├── 일반 명령어 (ADD, SUB, MOV, ...)
│   → 어떤 권한 레벨에서든 실행 가능
│   → Hypervisor 개입 불필요
│
└── Sensitive 명령어 (HW 상태를 변경하거나 읽는 명령어)
    ├── Privileged (특권) 명령어
    │   → 비특권 모드에서 실행 시 자동으로 trap (예외 발생)
    │   → Hypervisor가 catch하여 에뮬레이션
    │   예: MSR (레지스터 쓰기), HLT, ERET
    │
    └── Non-privileged Sensitive 명령어 (문제!)
        → 비특권 모드에서도 trap 없이 실행됨
        → 하지만 HW 상태에 영향을 줌
        → 가상화 어려움 (x86의 역사적 문제)
        예: x86의 POPF, SGDT (VT-x 이전)
```

### Trap-and-Emulate 메커니즘

```
Guest OS (EL1)가 특권 명령어 실행
    │
    ▼ TRAP (하드웨어가 자동으로 예외 발생)
    │
Hypervisor (EL2)가 예외를 받음
    │
    ▼ 명령어를 분석하고 에뮬레이션
    │
    ▼ VM 상태 업데이트
    │
    ▼ ERET (Guest OS로 복귀)
    │
Guest OS 계속 실행 (trap이 일어난 줄 모름)
```

**핵심**: Guest OS는 자기가 직접 HW를 제어한다고 생각하지만, 실제로는 Hypervisor가 대신 처리하고 결과만 돌려준다.

---

## 가상화의 역사 (간략)

| 연대 | 사건 | 의미 |
|------|------|------|
| 1960s | IBM CP/CMS | 최초의 가상 머신 — 메인프레임 시분할 |
| 1974 | Popek-Goldberg 논문 | 가상화 이론적 조건 정립 |
| 1998 | VMware 설립 | x86 가상화 상용화 시작 |
| 2003 | Xen 발표 | 오픈소스 Type 1 하이퍼바이저 |
| 2005-06 | Intel VT-x / AMD-V | x86 HW 가상화 지원 → trap 문제 해결 |
| 2007 | KVM 리눅스 합류 | Linux 커널 내장 하이퍼바이저 |
| 2008 | Intel EPT / AMD NPT | 메모리 가상화 HW 지원 → shadow PT 불필요 |
| 2013 | Docker 발표 | 컨테이너 기반 경량 가상화 대중화 |
| 2017+ | ARM VHE (v8.1) | ARM에서 호스트 OS가 EL2에서 직접 실행 |

---

## Q&A

**Q: 가상화의 3대 요소와 각각이 추상화하는 HW 자원은?**
> "CPU 가상화(특권 명령어 trap + 인터럽트 처리), 메모리 가상화(VM별 독립 주소 공간, VA→IPA→PA 2-stage 변환), I/O 가상화(디바이스 접근 공유/격리 — 에뮬레이션, VirtIO, SR-IOV pass-through). 세 요소 모두 SW 방식에서 시작하여 HW 지원(VT-x, EPT, SR-IOV)으로 진화했다는 공통 흐름이 있다."

**Q: Popek-Goldberg 조건 중 '효율성'이 왜 중요한가?**
> "대부분의 Guest 명령어가 Hypervisor 개입 없이 HW에서 직접 실행되어야 한다는 조건이다. 위반 시 ADD, MOV 같은 일반 연산까지 trap하게 되어 성능이 100배 이상 저하된다. 따라서 '특권 명령어만 trap, 나머지는 직접 실행'이 가상화의 핵심 설계 원칙이며, 이것이 Popek-Goldberg 3조건(동등성, 자원 제어, 효율성) 중 실용적으로 가장 큰 제약이다."

**Q: x86에서 VT-x 이전에 가상화가 어려웠던 이유는?**
> "x86에는 POPF, SGDT 같은 'Sensitive하지만 Non-privileged'한 명령어가 있었다. HW 상태를 변경/읽지만 비특권 모드에서 trap 없이 실행되어 Hypervisor가 가로챌 수 없었다. VMware는 Binary Translation(명령어 동적 치환)으로 SW 우회했고, Intel이 VT-x로 VMX non-root 모드를 추가하여 모든 Sensitive 명령어가 자동 VM Exit되도록 HW 근본 해결했다."

---
!!! warning "실무 주의점 — Para-virtualization 드라이버와 Full 가상화 혼용 오판"
    **현상**: KVM 환경에서 Guest OS에 VirtIO 드라이버를 설치했음에도 불구하고 디스크/네트워크 성능이 에뮬레이션과 차이가 없다.
    
    **원인**: Guest OS가 VirtIO 드라이버를 인식하더라도 Hypervisor 측에서 VirtIO backend(vhost-net, vhost-blk)가 활성화되지 않으면 여전히 QEMU user-space를 경유하는 full emulation 경로를 사용한다. 드라이버 설치만으로 para-virtualization이 완성된다고 착각하기 쉽다.
    
    **점검 포인트**: Hypervisor에서 `lspci -k` 결과의 드라이버 항목과 `/sys/bus/virtio/drivers/` 마운트 여부를 동시 확인. vhost 커널 모듈 로드 여부(`lsmod | grep vhost`)도 함께 검증.

## 핵심 정리

- **가상화 = HW 자원 추상화**: 1 physical → N virtual. 격리, 효율, multi-tenant.
- **Full**: HW emulation (느림). 예: QEMU 단독.
- **Para-virtualization**: guest OS 수정 (xenoLinux). HW emulation 회피.
- **HW-assisted**: VT-x/AMD-V, ARM EL2 — CPU가 가상화 지원. **현재 표준**.

## 다음 단계

- 📝 [**Module 01 퀴즈**](quiz/01_virtualization_fundamentals_quiz.md)
- ➡️ [**Module 01A — System Architecture Evolution**](01a_system_architecture_evolution.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">코스 홈</div>
  </a>
  <a class="nav-next" href="../01a_system_architecture_evolution/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Unit 1a: 시스템 아키텍처 진화 — HW Only에서 가상화까지</div>
  </a>
</div>
