# Unit 2: CPU 가상화

<div class="learning-meta">
  <span class="meta-badge meta-time">⏱ 12분</span>
  <span class="meta-badge meta-level-intermediate">📊 Intermediate</span>
</div>

## 핵심 개념
**CPU 가상화 = Guest OS의 특권 명령어를 안전하게 처리하면서, 일반 명령어는 HW에서 직접 실행하여 성능을 유지하는 것. SW 방식(Binary Translation)에서 HW 지원(VT-x, ARM EL2)으로 발전했다.**

---

## x86 Protection Ring

CPU는 권한 수준을 Ring(보호 링)으로 구분한다:

```
┌─────────────────────────────────────┐
│           Ring 3 (User)             │  ← 일반 애플리케이션
│      ┌───────────────────┐          │
│      │   Ring 0 (Kernel) │          │  ← OS 커널 (최고 권한)
│      └───────────────────┘          │
└─────────────────────────────────────┘
```

- **Ring 0**: 모든 HW 자원 접근 가능 (특권 명령어 실행 가능)
- **Ring 3**: 제한된 권한 (특권 명령어 실행 시 → 예외 발생, OS가 처리)
- **Ring 1, 2**: x86 스펙에 존재하지만 현대 OS는 사용하지 않음

**핵심**: OS는 Ring 0에서 동작한다고 가정하고 설계되었다. → 가상화 시 Guest OS도 Ring 0을 요구하는데, Hypervisor도 Ring 0이 필요 → **충돌 발생**.

---

## CPU 가상화의 과제

Guest OS는 원래 bare metal에서 동작하도록 설계되었다. 즉, 자기가 가장 높은 권한을 갖고 있다고 가정한다:

```
Guest OS가 하려는 것:
  1. 페이지 테이블 설정 (CR3/TTBR 레지스터 쓰기)
  2. 인터럽트 활성화/비활성화
  3. I/O 포트 접근
  4. CPU 모드 전환

문제: 이 모든 것을 Guest OS가 직접 하면
  → 다른 VM의 메모리를 건드릴 수 있음
  → 하이퍼바이저의 제어권을 빼앗을 수 있음
  → VM 간 격리 붕괴
```

**해결**: Guest OS의 특권 명령어를 Hypervisor가 가로채서(trap) 대신 처리(emulate)한다.

---

## 방법 1: Binary Translation (SW 방식)

### 개념

VT-x 이전, VMware가 x86의 "Non-privileged Sensitive" 명령어 문제를 해결한 방법:

```
Guest OS 코드 (원본)              변환된 코드 (실행되는 것)
┌─────────────────┐             ┌─────────────────────┐
│ MOV EAX, 5      │ ────────→  │ MOV EAX, 5          │  (그대로)
│ ADD EBX, EAX    │ ────────→  │ ADD EBX, EAX        │  (그대로)
│ POPF            │ ────────→  │ CALL vmm_popf_handler│ (치환!)
│ CLI             │ ────────→  │ CALL vmm_cli_handler │ (치환!)
│ MOV ECX, 10     │ ────────→  │ MOV ECX, 10         │  (그대로)
└─────────────────┘             └─────────────────────┘
```

### 동작 원리

1. **Guest 코드 블록을 스캔** — 실행 전에 코드를 분석
2. **Sensitive 명령어를 발견하면 치환** — Hypervisor의 핸들러 호출로 대체
3. **나머지 명령어는 그대로** — HW에서 직접 실행 (효율성 유지)
4. **변환 결과를 캐시** — 같은 코드 블록 재실행 시 재변환 불필요

### 장단점

| 장점 | 단점 |
|------|------|
| HW 지원 없이 동작 | 변환 오버헤드 (첫 실행 시) |
| Guest OS 수정 불필요 | 구현 복잡도 높음 |
| Non-privileged Sensitive 해결 | 자기 수정 코드(self-modifying code) 처리 어려움 |

---

## 방법 2: Para-virtualization (Guest OS 수정)

### 개념

Guest OS 커널을 수정하여, 특권 명령어 대신 **Hypervisor API(Hypercall)**를 직접 호출:

```
[ Full Virtualization ]          [ Para-virtualization ]

Guest OS:                        Guest OS (수정됨):
  MOV CR3, EAX  ← 특권 명령어      hypercall(SET_PAGE_TABLE, addr)
      │                                  │
      ▼ trap                             ▼ 직접 호출 (trap 없음)
  Hypervisor                         Hypervisor
  "CR3 쓰기를 에뮬레이션"            "Page table 설정 요청 처리"
```

### 대표 사례: Xen

```c
// Xen para-virtualized Guest OS (Linux 커널 수정)
// 원래: 직접 페이지 테이블 갱신
//   *pte = new_entry;

// 수정: hypercall로 Xen에 요청
HYPERVISOR_mmu_update(&update, 1, NULL, DOMID_SELF);
```

### 장단점

| 장점 | 단점 |
|------|------|
| trap 오버헤드 없음 (직접 호출) | Guest OS 커널 수정 필요 |
| Binary Translation보다 효율적 | 비공개 OS (Windows) 지원 불가 |
| 인터페이스 최적화 가능 | HW 가상화 등장 후 필요성 감소 |

---

## 방법 3: HW 지원 가상화 (VT-x / ARM VHE)

### Intel VT-x

x86의 가상화 문제를 HW 레벨에서 근본 해결:

```
VT-x 이전:                      VT-x 이후:
┌─────────────┐                 ┌─────────────┐
│ Ring 0: OS  │ ← 여기가 문제    │ VMX root    │ ← Hypervisor
│ Ring 3: App │                 │  (Ring 0)   │
└─────────────┘                 ├─────────────┤
Hypervisor를 어디에 놓을까?      │VMX non-root │ ← Guest OS
(Ring 0은 OS가 점유)            │  (Ring 0)   │   (Ring 0이지만 제한됨)
                                │  (Ring 3)   │ ← Guest App
                                └─────────────┘
```

### 핵심 구조: VMCS (Virtual Machine Control Structure)

```
┌─────────────────────────────────────────┐
│            VMCS (per VM)                │
├─────────────────────────────────────────┤
│ Guest State Area                        │
│   - 레지스터 (RAX, RBX, ..., RIP, RSP) │
│   - CR0, CR3, CR4                       │
│   - IDTR, GDTR                          │
│   - Segment registers                   │
├─────────────────────────────────────────┤
│ Host State Area                         │
│   - Hypervisor 복귀 시 로드할 상태      │
├─────────────────────────────────────────┤
│ VM-Execution Control                    │
│   - 어떤 이벤트에서 VM Exit할지 설정    │
│   - 예: CR3 쓰기, I/O 접근, 인터럽트    │
├─────────────────────────────────────────┤
│ VM-Exit / VM-Entry Control              │
│   - Exit/Entry 시 수행할 동작 설정      │
└─────────────────────────────────────────┘
```

### VM Entry / VM Exit 흐름

```
Hypervisor (VMX root mode)
    │
    │ VMLAUNCH / VMRESUME
    ▼
┌─────────────────────────┐
│ Guest 실행               │
│ (VMX non-root mode)     │
│                          │
│ 일반 명령어 → HW 직접    │
│ 특권 명령어 → VM Exit ──┼──┐
│ 외부 인터럽트 → VM Exit ─┼──┤
│ I/O 접근 → VM Exit ─────┼──┤
└─────────────────────────┘  │
                              │
    ┌─────────────────────────┘
    │
    ▼
Hypervisor가 원인 분석 및 처리
    │
    │ VMRESUME
    ▼
Guest 재개 (exit 지점부터)
```

**성능 포인트**: VM Exit은 비용이 크다 (수백~수천 사이클). Exit 횟수를 최소화하는 것이 성능 핵심.

---

### ARM Exception Level 기반 가상화

ARM은 처음부터 가상화를 고려한 Exception Level 설계:

```
┌─────────────────────────────────────────────┐
│  EL0  │ User Application        (비특권)     │
├───────┤                                      │
│  EL1  │ Guest OS Kernel         (OS 특권)    │
├───────┤                                      │
│  EL2  │ Hypervisor              (가상화 특권) │
├───────┤                                      │
│  EL3  │ Secure Monitor/TrustZone (보안 특권)  │
└─────────────────────────────────────────────┘

전환:
  EL0 → EL1: SVC (SuperVisor Call)    ← 시스템 콜
  EL1 → EL2: HVC (HyperVisor Call)    ← 하이퍼바이저 호출
  EL1/2 → EL3: SMC (Secure Monitor Call) ← TrustZone 전환
```

### ARM vs x86 가상화 비교

| 항목 | x86 (VT-x) | ARM (EL2) |
|------|------------|-----------|
| HW 모드 | VMX root / non-root | EL2 (Hypervisor) / EL1 (Guest) |
| VM 상태 저장 | VMCS (HW 관리) | 메모리 (SW 관리, 유연함) |
| 전환 비용 | VM Exit/Entry (~수천 cycle) | EL 전환 (~수백 cycle, 상대적 경량) |
| 가상화 역사 | 후천적 추가 (2005) | 설계 시 포함 (ARMv7/v8) |
| 2-stage translation | EPT | Stage 1 (EL1) + Stage 2 (EL2) |

### ARM VHE (Virtualization Host Extensions, v8.1+)

```
VHE 이전:                         VHE 이후:
┌──────────┐                     ┌──────────┐
│EL0: App  │                     │EL0: App  │
│EL1: Guest│                     │EL1: Guest│
│EL2: Hyp  │ ← 별도 코드 필요    │EL2: Host OS + Hypervisor│
│          │                     │          │ ← Host OS가 EL2에서
└──────────┘                     └──────────┘   직접 실행 가능

이점: KVM 같은 Type 2 하이퍼바이저에서
      Host OS (Linux)가 EL2에서 직접 실행
      → EL1↔EL2 전환 오버헤드 감소
```

---

## Context Switching 비용 분석

### Bare Metal에서의 시스템 콜

```
User App (EL0)
    │ SVC (시스템 콜)
    ▼
OS Kernel (EL1)
    │ 처리 완료
    ▼ ERET
User App (EL0)

총 context switch: 2회 (EL0→EL1, EL1→EL0)
```

### 가상화 환경에서의 시스템 콜 (I/O 포함)

```
User App (EL0)
    │ SVC
    ▼
Guest OS (EL1) ─── OS가 I/O 처리 시도
    │ HVC (또는 trap)
    ▼
Hypervisor (EL2) ─── 실제 HW I/O 수행
    │ ERET
    ▼
Guest OS (EL1) ─── I/O 결과 수신
    │ ERET
    ▼
User App (EL0)

총 context switch: 4회 (EL0→1, EL1→2, EL2→1, EL1→0)
```

### 비용 비교

| 시나리오 | Context Switch 횟수 | 추가 비용 |
|---------|-------------------|----------|
| Bare Metal 시스템 콜 | 2 | 없음 |
| 가상화 + I/O | 4 | 2-stage 주소 변환 + 레지스터 저장/복원 |
| 가상화 + 인터럽트 | 4+ | 인터럽트 라우팅 오버헤드 추가 |

**이것이 Hypervisor Pass-through가 필요한 이유**: I/O 경로에서 EL1→EL2 전환을 제거하면 context switch 절반으로 감소.

---

## Q&A

**Q: Binary Translation과 VT-x의 핵심 차이는?**
> "Binary Translation은 Guest 코드를 실행 전에 스캔하여 Sensitive 명령어를 Hypervisor 핸들러 호출로 동적 치환하는 SW 우회 방식이다. VT-x는 VMX non-root 모드를 HW에 추가하여 모든 Sensitive 명령어가 자동으로 VM Exit을 발생시키도록 한 HW 근본 해결이다. BT는 코드 변환 오버헤드와 복잡도가 있지만, VT-x는 코드 변환 없이 Guest OS를 그대로 실행 가능하다."

**Q: Bare Metal 대비 가상화 환경에서 I/O의 context switch 오버헤드는?**
> "Bare Metal 시스템 콜은 EL0→EL1→EL0으로 2회, 가상화 I/O는 EL0→EL1→EL2→EL1→EL0으로 4회 — 2배 차이다. 각 EL 전환마다 레지스터 저장/복원, TLB 처리가 발생하며, 특히 EL1↔EL2는 VMCS 상태 전체 저장/복원으로 수백~수천 cycle이 소요된다. 고빈도 I/O에서 누적 오버헤드가 심각하며, 비결정적 latency로 실시간 deadline 위반 가능. 이것이 Pass-through로 EL2 경유를 제거하려는 동기다."

**Q: Para-virtualization이 HW 가상화 등장 후 줄어든 이유는?**
> "Para-virtualization은 x86의 Non-privileged Sensitive 명령어를 trap할 수 없어서 Guest OS를 수정하여 hypercall로 대체하는 방식이었다. VT-x/ARM EL2가 모든 Sensitive 명령어를 HW에서 자동 trap하므로 Guest OS 수정이 불필요해졌고, 미수정 OS(Windows 포함)도 그대로 실행 가능해졌다. 다만 VirtIO 같은 I/O para-virtualization은 에뮬레이션보다 VM Exit이 적어 여전히 성능 이점이 있어 현재도 널리 사용된다."

<div class="chapter-nav">
  <a class="nav-prev" href="01a_system_architecture_evolution.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Unit 1a: 시스템 아키텍처 진화 — HW Only에서 가상화까지</div>
  </a>
  <a class="nav-next" href="03_memory_virtualization.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">메모리 가상화</div>
  </a>
</div>
