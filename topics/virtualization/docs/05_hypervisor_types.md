# Module 05 — Hypervisor Types

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🪟</span>
    <span class="chapter-back-text">Virtualization</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 05</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#type-1-bare-metal-hypervisor">Type 1: Bare Metal Hypervisor</a>
  <a class="page-toc-link" href="#type-2-hosted-hypervisor">Type 2: Hosted Hypervisor</a>
  <a class="page-toc-link" href="#type-1-vs-type-2-비교">Type 1 vs Type 2 비교</a>
  <a class="page-toc-link" href="#경계를-넘는-구현-kvm">경계를 넘는 구현: KVM</a>
  <a class="page-toc-link" href="#xen-아키텍처">Xen 아키텍처</a>
  <a class="page-toc-link" href="#hypervisor-선택-가이드">Hypervisor 선택 가이드</a>
  <a class="page-toc-link" href="#qa">Q&A</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Distinguish** Type 1 (Bare Metal) vs Type 2 (Hosted) hypervisor
    - **Identify** 주요 hypervisor의 분류 (KVM, Xen, Hyper-V, VMware ESXi/Workstation, VirtualBox)
    - **Compare** 각 hypervisor의 architecture trade-off
    - **Decide** 시나리오에 따른 hypervisor 선택

!!! info "사전 지식"
    - [Module 01-04](01_virtualization_fundamentals.md)

!!! tip "💡 이해를 위한 비유"
    **Type 1 vs Type 2** ≈ **Type 1 = HW 위 직접 깔린 식당 (ESXi, Xen) / Type 2 = OS 위 앱 (VMware Workstation)**

    Type 1 은 HW 위 직접 + 자체 kernel, Type 2 는 host OS 위에 application 으로. KVM 은 hybrid (Linux kernel module + HW assist).

---

## 핵심 개념
**Hypervisor는 HW 자원을 VM에 분배/격리하는 소프트웨어. Type 1(Bare Metal)과 Type 2(Hosted)로 나뉘며, 실제 구현(KVM, Xen, VMware)은 이 분류의 경계를 넘나든다.**

!!! danger "❓ 흔한 오해"
    **오해**: KVM 은 Type 1 이다

    **실제**: KVM 은 Linux kernel module — 엄밀히는 Type 2 구조이지만 HW assist 활용으로 Type 1 같은 성능. 분류는 학술적 논쟁.

    **왜 헷갈리는가**: 성능이 Type 1 급이라 "=Type 1" 으로 단순화. spec 상은 Type 2.
---

## Type 1: Bare Metal Hypervisor

### 구조

Hypervisor가 **HW 위에 직접** 설치. Host OS 없음:

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│   VM0    │  │   VM1    │  │   VM2    │
│ Guest OS │  │ Guest OS │  │ Guest OS │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │              │              │
─────┴──────────────┴──────────────┴─────
              Hypervisor
              (HW 위에 직접)
─────────────────────────────────────────
              Hardware
```

### 특징

| 항목 | 설명 |
|------|------|
| 성능 | Host OS 계층 없음 → 오버헤드 최소 |
| 보안 | 공격 표면 작음 (Hypervisor만 존재) |
| 용도 | 데이터센터, 클라우드, 서버 가상화 |
| 관리 | 별도 관리 콘솔 필요 (일반 OS가 아니므로) |

### 대표 구현

| 이름 | 개발 | 특징 |
|------|------|------|
| **VMware ESXi** | VMware | 상용, 엔터프라이즈 표준 |
| **Xen** | Linux Foundation | 오픈소스, AWS EC2 초기 기반 |
| **Microsoft Hyper-V** | Microsoft | Windows Server 내장 |

---

## Type 2: Hosted Hypervisor

### 구조

일반 OS(Host OS) **위에** Hypervisor가 애플리케이션처럼 동작:

```
┌──────────┐  ┌──────────┐
│   VM0    │  │   VM1    │
│ Guest OS │  │ Guest OS │
└────┬─────┘  └────┬─────┘
     │              │
─────┴──────────────┴──────
       Hypervisor
       (Host OS 위의 앱)
───────────────────────────
        Host OS
       (Linux, Windows, macOS)
───────────────────────────
        Hardware
```

### 특징

| 항목 | 설명 |
|------|------|
| 성능 | Host OS 계층 추가 → 오버헤드 더 큼 |
| 편의성 | 기존 OS에 설치 가능 (앱처럼) |
| 용도 | 개발/테스트, 데스크탑 가상화 |
| 관리 | Host OS의 도구 그대로 사용 |

### 대표 구현

| 이름 | 개발 | 특징 |
|------|------|------|
| **VirtualBox** | Oracle | 오픈소스, 무료, 크로스 플랫폼 |
| **VMware Workstation** | VMware | 상용, 데스크탑 개발 환경 |
| **Parallels** | Parallels | macOS 전용, Apple Silicon 지원 |
| **QEMU** | 오픈소스 | 에뮬레이터 + 가상화 (KVM과 결합) |

---

## Type 1 vs Type 2 비교

```
[ Type 1 ]                    [ Type 2 ]

  VM    VM    VM               VM    VM
   │     │     │                │     │
   └──┬──┘     │                └──┬──┘
      │        │                   │
  Hypervisor ──┘               Hypervisor
      │                            │
  Hardware                      Host OS
                                   │
                                Hardware

계층 수: 2 (VM → Hypervisor → HW)    3 (VM → Hypervisor → Host OS → HW)
```

| 항목 | Type 1 | Type 2 |
|------|--------|--------|
| HW 접근 | 직접 | Host OS 경유 |
| 성능 | 높음 | 중간 |
| 보안 | 공격 표면 작음 | Host OS 취약점 영향 |
| 설치 | 전용 설치 필요 | 기존 OS에 앱 설치 |
| 드라이버 | Hypervisor 자체에 필요 | Host OS 드라이버 사용 |
| 용도 | 프로덕션 서버 | 개발/테스트/데스크탑 |

---

## 경계를 넘는 구현: KVM

### KVM은 Type 1? Type 2?

**KVM (Kernel-based Virtual Machine)**은 분류가 모호한 대표적 사례:

```
전통적 관점:
  Linux + KVM = Type 2 (Linux가 Host OS)

실제 동작:
  KVM 로드 시 Linux 커널 자체가 Hypervisor가 됨
  → Linux = Host OS + Hypervisor 역할 동시 수행
  → 사실상 Type 1에 가까운 성능

ARM VHE 이후:
  Linux 커널이 EL2에서 직접 실행
  → HW 관점에서 완전히 Type 1
```

### KVM + QEMU 아키텍처

```
┌──────────────────────────────────────────┐
│  User Space                               │
│  ┌──────────┐  ┌──────────┐              │
│  │ QEMU     │  │ QEMU     │              │
│  │ (VM0)    │  │ (VM1)    │  ← 디바이스  │
│  │          │  │          │    에뮬레이션 │
│  └────┬─────┘  └────┬─────┘              │
│       │ ioctl        │ ioctl              │
├───────┼──────────────┼───────────────────┤
│       ▼              ▼    Kernel Space    │
│  ┌─────────────────────────────────┐     │
│  │ KVM Module                      │     │
│  │  - VCPU 스케줄링                │     │
│  │  - 메모리 관리 (EPT/Stage 2)    │  ← │
│  │  - VM Exit 처리                 │     │
│  └────────────┬────────────────────┘     │
│               │                           │
│  Linux Kernel (스케줄러, 메모리, 드라이버) │
├───────────────┼──────────────────────────┤
│               ▼                           │
│           Hardware (VT-x / ARM EL2)       │
└──────────────────────────────────────────┘
```

### 역할 분담

| 컴포넌트 | 역할 |
|---------|------|
| **KVM** (커널 모듈) | CPU 가상화 (VT-x/ARM EL2 활용), 메모리 가상화 (EPT/Stage 2), VM Exit 처리 |
| **QEMU** (유저 프로세스) | 디바이스 에뮬레이션 (NIC, 디스크, VGA...), VM 생성/설정 UI |
| **Linux Kernel** | 프로세스 스케줄링, 메모리 관리, HW 드라이버 |

**핵심**: KVM은 Linux 커널의 강력한 인프라(스케줄러, 드라이버, 메모리 관리)를 그대로 활용하면서, CPU/메모리 가상화만 HW 지원으로 수행. 이것이 KVM이 빠르게 성장한 이유.

---

## Xen 아키텍처

### 구조

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│  Dom0    │  │  DomU 1  │  │  DomU 2  │
│ (특권VM) │  │ (일반VM) │  │ (일반VM) │
│ 관리도구 │  │ Guest OS │  │ Guest OS │
│ 드라이버 │  │          │  │          │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │              │              │
─────┴──────────────┴──────────────┴─────
                Xen Hypervisor
              (HW 위에 직접, Type 1)
─────────────────────────────────────────
                 Hardware
```

### Dom0 vs DomU

| | Dom0 | DomU |
|--|------|------|
| 역할 | 관리 VM (특권) | 일반 VM (비특권) |
| HW 접근 | 물리 드라이버 보유 | Dom0 또는 pass-through 경유 |
| 기능 | VM 생성/삭제, 디바이스 관리 | 사용자 워크로드 실행 |

---

## Hypervisor 선택 가이드

| 시나리오 | 추천 | 이유 |
|---------|------|------|
| 클라우드 서버 | KVM | Linux 생태계, 성능, 유연성 |
| 엔터프라이즈 | ESXi | 안정성, 관리 도구, 지원 |
| AWS/클라우드 초기 | Xen | 격리 모델, para-virtualization |
| 개발/테스트 | VirtualBox/QEMU | 무료, 쉬운 설치 |
| macOS 데스크탑 | Parallels | Apple Silicon 최적화 |
| 임베디드/자동차 | Xen/Type 1 | 실시간성, 보안 격리 |

---

## Q&A

**Q: KVM은 Type 1인가 Type 2인가?**
> "Type 2 관점에서 KVM은 Linux 커널 모듈이고 QEMU가 유저 프로세스로 VM을 관리한다. Type 1 관점에서는 KVM 로드 시 Linux 자체가 Hypervisor 역할을 수행하고 별도 Host OS 계층이 없다. ARM VHE(ARMv8.1+)에서는 Linux+KVM이 EL2에서 직접 실행되어 HW 관점에서 Type 1 Bare Metal과 동일한 구조가 된다. 결론: 구조적으로 Type 2에 가깝지만 성능은 Type 1에 근접하며, VHE 이후 이 구분 자체가 무의미해졌다."

**Q: Xen에서 Dom0가 필요한 이유는?**
> "Xen Hypervisor는 Micro-kernel 철학으로 CPU 스케줄링, 메모리 관리, VM 격리만 담당하고 디바이스 드라이버나 관리 인터페이스가 없다. Dom0이 담당하는 것: (1) HW 드라이버 — 물리 디바이스 드라이버는 Dom0의 Linux 커널이 보유, (2) VM 관리 — xl 등 도구로 VM 생성/삭제, (3) I/O 중재 — DomU의 I/O를 para-virtualized backend로 처리, (4) 부팅 — Xen 부팅 후 Dom0이 먼저 시작하여 나머지 DomU 생성. Dom0 없이는 디바이스 사용도 VM 생성도 불가능하다."

---
!!! warning "실무 주의점 — KVM dirty bit emulation 누락 시 live migration 데이터 손실"
    **현상**: Live migration 후 destination VM 에서 일부 page 가 source 의 최신 상태와 불일치하여 application 단에서 silent corruption 발생.

    **원인**: EPT/NPT 의 D-bit 또는 PML(Page Modification Logging) 설정이 누락되거나, write-protect fault 기반 dirty tracking 에서 race 로 인해 일부 modified page 가 dirty bitmap 에 누락.

    **점검 포인트**: `KVM_CAP_MANUAL_DIRTY_LOG_PROTECT` 사용 여부, PML buffer flush 시점, migration 마지막 round 의 throttle threshold, post-copy fallback 활성화 여부.

## 핵심 정리

- **Type 1 (Bare Metal)**: HW 위에 직접 hypervisor. 예: VMware ESXi, Xen, Hyper-V (Windows Server). 데이터센터 표준.
- **Type 2 (Hosted)**: Host OS 위에 hypervisor. 예: VirtualBox, VMware Workstation. 데스크톱.
- **KVM**: Linux kernel module + QEMU. 기술적으로 Type 2이지만 Type 1처럼 동작 (kernel = hypervisor).
- **Xen**: Type 1, Dom0 (privileged) + DomU (unprivileged) 구조.
- **선택 기준**: Production server → Type 1, 개발/테스트 → Type 2.

## 다음 단계

- 📝 [**Module 05 퀴즈**](quiz/05_hypervisor_types_quiz.md)
- ➡️ [**Module 06 — Strict vs Passthrough**](06_strict_vs_passthrough.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../04_io_virtualization/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">I/O 가상화</div>
  </a>
  <a class="nav-next" href="../06_strict_vs_passthrough/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Strict System vs Hypervisor Pass-through</div>
  </a>
</div>
