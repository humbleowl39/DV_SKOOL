---
title: "Module 05 — Hypervisor Types"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Distinguish** Type 1 (Bare Metal) 과 Type 2 (Hosted) hypervisor 를 부팅 순서와 trap 경로 관점에서 구분할 수 있다.
- **Identify** ESXi / Xen / Hyper-V / KVM / VirtualBox / VMware Workstation 의 분류와 hybrid 위치를 식별한다.
- **Trace** 같은 VM 생성 요청이 Type 1 과 Type 2 에서 각각 어떤 경로로 처리되는지 단계별로 추적한다.
- **Compare** KVM 과 Xen 의 architecture trade-off (kernel 통합 vs Dom0 분리) 를 비교한다.
- **Justify** 시나리오 (production cloud / 개발 데스크탑 / 임베디드) 에 따른 hypervisor 선택을 정당화한다.
:::
:::note[사전 지식]
- [Module 01](../01_virtualization_fundamentals/) — Hypervisor / trap / VM Exit 의 의미
- [Module 02-04](../02_cpu_virtualization/) — VT-x, EPT, I/O 가상화 메커니즘
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — 같은 KVM 이 _Type 1 또는 Type 2_?

Hypervisor 를 선택할 때 가장 먼저 마주치는 질문은 "Type 1 인가 Type 2 인가" 입니다. VMware ESXi 는 bare metal 위에 직접 설치되는 Type 1, VirtualBox 는 host OS 위에서 애플리케이션처럼 동작하는 Type 2 입니다. Hyper-V 는 Windows Server 가 _management partition_ 역할을 하지만 hypervisor 가 먼저 부팅되므로 Type 1 로 분류합니다.

KVM 은 이 분류의 경계를 흐립니다. Linux kernel module 형태로 host OS 위에서 동작한다는 점에서는 Type 2 처럼 보이지만, KVM 모듈이 로드되는 순간 Linux kernel 자체가 VMX root mode 로 진입하여 hypervisor 역할을 직접 수행합니다. 결과적으로 구조는 Type 2 이지만 trap 경로는 Type 1 과 동일합니다. 이것이 **Hybrid** 라고 불리는 이유입니다.

분류가 실용적으로 중요한 이유는 세 가지입니다. 첫째, VM Exit handler 의 위치가 다릅니다. Type 1 은 bare metal hypervisor 가 직접 처리하고, Type 2 는 host OS 를 경유하므로 latency 차이가 큽니다. 둘째, driver 접근 방식이 다릅니다. Type 1 은 자체 driver 를 내장해야 하고, Type 2 는 host OS 의 driver 를 재사용합니다. 셋째, 부팅 순서가 다릅니다. Type 1 은 부팅 직후 hypervisor 가 자리를 잡고, Type 2 는 host OS 가 먼저 올라온 뒤 hypervisor 앱이 시작됩니다.

같은 "가상화" 라는 말 아래에 ESXi · Xen · KVM · Hyper-V · VirtualBox · VMware Workstation 이 모두 들어 있지만, 각자 **부팅 순서가 다르고 trap 의 종착지가 다릅니다**. 어떤 hypervisor 가 host OS 위에 앉는지 아니면 bare metal 위에 앉는지를 모르면, 같은 증상 (`KVM: entry failed`, `vmx_vmexit_handler` panic 등) 이 어디서 났는지 한 줄도 추적할 수 없습니다.

이 모듈을 건너뛰면 이후 모듈 (Strict vs Passthrough, MicroVM, Live Migration) 에서 "이건 ESXi 에선 가능하지만 KVM 에선 다른 path" 같은 문장이 그냥 외워야 하는 명제가 됩니다. 반대로 Type 1 / Type 2 / Hybrid 의 세 개 box 와 그 경계만 잡으면, **새 hypervisor 가 나와도 box 위치만 찍으면 trap 경로 · driver 위치 · 보안 표면을 즉시 그릴 수 있습니다**.

---

## 2. Intuition — 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**Type 1** = HW 위에 **직접 깔린 식당** — 자체 주방, 자체 종업원, 손님(VM)만 받음.<br>
**Type 2** = 일반 건물에 **세입자로 입주한 식당** — 건물주(host OS) 의 전기/수도/엘리베이터를 빌려 씀.<br>
**KVM (hybrid)** = 건물주가 _직접_ 식당을 운영 — 건물 = 식당. 외부에서 보면 입주자(Type 2) 같지만 실제로는 같은 사람.
:::
### 한 장 그림 — 세 구조의 부팅 순서

```
   Type 1 (Bare Metal)         Type 2 (Hosted)              KVM (Hybrid)
   ────────────────────        ───────────────────────      ───────────────────────
   ┌─ Power ON                 ┌─ Power ON                  ┌─ Power ON
   │                           │                            │
   │ ┌──────────────┐          │ ┌──────────────┐           │ ┌──────────────┐
   │ │   ESXi /     │          │ │  Linux /     │           │ │  Linux       │
   │ │   Xen /      │          │ │  Windows /   │           │ │  + KVM 모듈  │  ⭐
   │ │   Hyper-V    │          │ │  macOS       │           │ │  (= kernel)  │
   │ │  (= kernel)  │          │ └──────┬───────┘           │ └──────┬───────┘
   │ └──────┬───────┘          │        │ (사용자 로그인)    │        │ /dev/kvm
   │        │                  │        │                   │        │
   │     [VM 1] [VM 2] ...     │  ┌───────────────┐         │   ┌────────┐
   │                           │  │ VirtualBox /  │         │   │ QEMU   │ (user app)
   │                           │  │ VMware WS     │  ← app  │   └────┬───┘
   │                           │  └──────┬────────┘         │        │ ioctl
   │                           │         │                  │        │
   │                           │      [VM 1] [VM 2]         │     [VM 1]
   │
   │ trap 종착지: hypervisor   │ trap 종착지: 두 단계         │ trap 종착지: kernel
   │ (직접)                     │ (hypervisor app → host OS) │ (직접, 1 단계)
```

세 구조의 차이는 **"VM 의 특권 명령 trap 이 어디로 가는가"** 한 문장으로 요약됩니다.

- **Type 1**: HW → hypervisor (직접).
- **Type 2**: HW → host OS → user-space hypervisor 앱. (2 단계 경유)
- **KVM**: HW → kernel 안의 KVM 모듈 (직접). Type 2 모양인데 Type 1 경로.

### 왜 이렇게 설계됐는가 — Design rationale

원래 Popek-Goldberg 의 그림은 hypervisor 가 **kernel 위치** 에 있어야 했습니다 (특권 명령 trap 을 받으려면 _가장 높은 권한 mode_ 에 있어야 하므로). 하지만 1990 년대 후반 VMware 가 x86 에서 시작했을 때 **이미 Windows 가 host OS 로 깔려 있는 PC 에 가상화를 팔아야** 했기에 "host OS 위의 app 으로 hypervisor 를 띄우는" Type 2 모델이 발명됐습니다. 그 후 데이터센터 표준이 정해지면서 **bare metal 위에 hypervisor 만 깔리는 Type 1** 이 production 으로 자리잡고, Linux 진영은 "_Linux kernel 자체가 hypervisor 가 되면 둘의 장점을 다 가진다_" 는 통찰로 **KVM** 을 만들었습니다 — 이게 hybrid 가 생긴 이유. 즉 세 box 는 _이론_ 이 아니라 _시장과 OS 생태계_ 가 만든 결과입니다.

---

## 3. 작은 예 — Type 1 과 Type 2 에서 VM 하나가 부팅되는 과정

가장 단순한 시나리오. **같은 사용자가 "VM 한 개 만들어 부팅"** 을 요청했을 때 ESXi (Type 1) 와 VirtualBox (Type 2), 그리고 KVM (hybrid) 에서 각각 어떤 path 로 처리되는지 비교합니다.

```
    ① VM Create 요청
    ──────────────────
       │   ┌─────────────┐
       ├──▶│ Type 1: ESXi│   vSphere Client → ESXi 의 자체 management daemon (`hostd`)
       │   └─────┬───────┘     → ESXi kernel(vmkernel)이 직접 vCPU/메모리/EPT 자원 할당
       │         │
       │         │   ② vCPU 생성, EPT 매핑, BAR 매핑 모두 vmkernel 내부에서 완료
       │         │   ③ VMCS 초기화, VM-Entry → Guest BIOS 실행
       │         ▼
       │      [Guest VM 부팅 — bare metal 처럼 빠름]
       │      trap → vmkernel 1 step → emulate → VM-Entry
       │
       │   ┌─────────────┐
       ├──▶│ Type 2: VBox│   GUI/CLI → VirtualBox app (user-space)
       │   └─────┬───────┘     → VirtualBox 가 host OS 의 syscall 로 메모리/디스크 요청
       │         │
       │         │   ② host kernel 드라이버 (`vboxdrv`) 로 VT-x 진입
       │         │   ③ VMM (VirtualBox 내부) 이 VMCS 셋업, VM-Entry
       │         ▼
       │      [Guest VM 부팅 — host OS 가 스케줄 지연/캐시 압박 영향 받음]
       │      trap → vboxdrv → VirtualBox app → host OS scheduler → 다시 ioctl → VM-Entry
       │
       │   ┌─────────────┐
       └──▶│ Hybrid: KVM │   libvirt/virsh → QEMU 프로세스 (user-space)
           └─────┬───────┘     → QEMU 가 `/dev/kvm` 의 `KVM_RUN` ioctl 호출
                 │
                 │   ② KVM 커널 모듈이 VT-x VM-Entry 직접 실행 (kernel-mode)
                 │   ③ VM Exit 이 일어나면 KVM 이 분기 — 단순 명령은 kernel 안에서 처리
                 │      디바이스 emulation 이면 QEMU 로 회수 (`KVM_EXIT_IO` 등)
                 ▼
           [Guest VM 부팅 — Type 1 에 근접한 path, device emulation 만 user space]
           trap → KVM kernel module (1 step) → 분기 → 가벼우면 즉시 VM-Entry
```

| Step | Type 1 (ESXi) | Type 2 (VirtualBox) | Hybrid (KVM) |
|---|---|---|---|
| ① 요청 진입점 | vSphere → `hostd` | GUI/CLI → VirtualBox app | virsh/libvirt → QEMU 프로세스 |
| ② 자원 할당 | vmkernel 직접 | host OS syscall → kernel driver | QEMU → `ioctl(KVM_CREATE_VM)` |
| ③ VM-Entry 실행 주체 | vmkernel | vboxdrv (kernel) + VirtualBox (user) | KVM 모듈 (kernel) |
| ④ Trap (VM Exit) 처리 | vmkernel 1-step | vboxdrv → app → host OS 영향 | KVM 모듈 1-step (필요 시 QEMU 회수) |
| ⑤ I/O Emulation | vmkernel 내장 | VirtualBox app (user-space) | QEMU (user-space) |
| ⑥ Host OS 스케줄러 영향 | **없음** (자체 스케줄러) | **있음** (Windows/macOS 스케줄러) | **있음** (Linux 스케줄러, 하지만 RT priority 가능) |

```c
/* Hybrid (KVM) 의 핵심 코드 — QEMU 가 vCPU 한 번 돌리는 경로
   trap 이 가벼우면 kernel 안에서 그대로 처리되고, 디바이스 emulation 이 필요하면
   exit reason 과 함께 user-space 로 회수된다. */
int kvm_cpu_exec(CPUState *cpu) {
    struct kvm_run *run = cpu->kvm_run;
    int ret;
    do {
        ret = ioctl(cpu->kvm_fd, KVM_RUN, 0);  /* ← vCPU 실행, VM-Exit 시 복귀 */
        switch (run->exit_reason) {
        case KVM_EXIT_IO:         /* PIO emulation — QEMU 가 처리 */
            kvm_handle_io(run);
            break;
        case KVM_EXIT_MMIO:       /* MMIO emulation — QEMU 가 처리 */
            kvm_handle_mmio(run);
            break;
        case KVM_EXIT_HLT:        /* Guest 가 halt — 다시 ioctl 로 wake-up 대기 */
            break;
        /* 그 외 가벼운 trap (cr3 access, msr 등) 은 kernel 안에서 처리되어
           여기에 안 옴 — 즉 user-space round-trip 0회 */
        }
    } while (!cpu->exit_request);
    return ret;
}
```

:::note[여기서 잡아야 할 두 가지]
**(1) trap 의 종착지가 _hop 수_ 를 결정한다** — Type 1 은 1 hop, Type 2 는 2~3 hop. KVM 은 1 hop (kernel 안) + 선택적 user-space 회수. 100 Gbps NIC 처럼 초당 수십만 exit 이 나는 워크로드에서는 이 hop 수가 throughput 의 _주요 변수_ 입니다.<br>
**(2) host OS 가 있다 = host OS scheduler 가 끼어든다** — Type 2 의 가장 큰 latency 변수. VM 이 CPU 를 받기까지 host OS 의 다른 프로세스와 경쟁합니다. Production 서버에 Type 2 를 안 쓰는 이유.
:::

:::caution[왜 "hop 수 = 비용" 인가 — 한 hop 이 _실제로_ 무엇을 일으키나]
"hop 수가 throughput 변수" 라는 말이 추상적으로 들리지만, hop 한 번이 _물리적으로_ 무엇을 강제하는지를 보면 왜 곧 비용인지가 드러납니다. 각 hop 은 단순한 함수 호출이 아니라 **권한/주소공간 경계를 넘는 전환** 이기 때문입니다.

- **mode/address-space 전환** — Guest(non-root/EL1) → KVM(root/EL2) → user-space QEMU(EL0) 로 hop 할 때마다 권한 레벨이 바뀌고, 특히 user-space 로 나가면 page table(주소공간) 까지 바뀝니다. 전환마다 레지스터 save/restore 와 권한 검사가 따라옵니다(§Module 02 의 VM Exit 비용 분해와 같은 구조).
- **cache / TLB pollution** — 이게 더 큰 간접 비용입니다. hop 의 종착지 코드(host OS scheduler, QEMU device model)가 실행되면 Guest 가 데우던 cache line 과 TLB entry 를 밀어냅니다. 다시 Guest 로 돌아오면 Guest 는 _콜드_ 상태에서 재개되어, hop 자체의 cycle 보다 그 후폭풍(cache/TLB miss 폭증)이 더 비쌀 수 있습니다.

그래서 hop 이 _많을수록_ — Type 2 의 2~3 hop, 또는 Xen 이 I/O 마다 Dom0 를 경유하는 path — 전환 비용과 pollution 이 누적됩니다. 반대로 KVM 이 가벼운 trap 을 kernel 안 1 hop 에서 끝내고 user-space 로 안 나가는 것(§3 의 코드 주석 "user-space round-trip 0회")이 latency 우위의 핵심입니다. "hop 수를 세라" 는 곧 "경계 전환과 cache pollution 지점을 세라" 와 같은 말입니다.
:::
---

## 4. 일반화 — Hypervisor 분류축과 경계 사례

### 4.1 두 개의 분류축

Hypervisor 를 단순히 "Type 1 / Type 2" 로만 보면 KVM 이 어디 속하는지 답이 안 나옵니다. 실제로는 **두 개의 직교 축** 이 있습니다.

| 축 | 질문 | 가능한 답 |
|---|---|---|
| **A. Host OS 존재** | hypervisor 아래에 별도 일반 OS 가 있는가? | Yes (= "hosted") / No (= "bare metal") |
| **B. Hypervisor 위치** | Hypervisor 코드가 kernel mode 인가 user mode 인가? | Kernel / User-space + Kernel driver |

```
                          A. Host OS 가 있는가?
                          ─────────────────────
                          No                  Yes
                       ┌─────────────────┬────────────────────────┐
B. Hypervisor 코드가  │                 │                        │
   kernel 안에 있는가? │                 │                        │
                Yes   │  ★ Type 1       │  ★ Hybrid (KVM)        │
                      │  ESXi / Xen /   │  Linux kernel = host   │
                      │  Hyper-V        │  KVM 모듈 = hypervisor │
                      │                 │  → 같은 kernel         │
                      ├─────────────────┼────────────────────────┤
                No    │  (이런 조합     │  ★ Type 2              │
                      │   사실상 없음)  │  VirtualBox /          │
                      │                 │  VMware Workstation /  │
                      │                 │  Parallels             │
                      └─────────────────┴────────────────────────┘
```

KVM 이 "Type 1 인가 Type 2 인가" 라는 논쟁은 **A 축 답 (host 있음) 만 보면 Type 2, B 축 답 (kernel 안) 만 보면 Type 1** 인 데서 옵니다. 두 축으로 보면 **별도 칸 — Hybrid** 입니다.

### 4.2 분류 표

| Hypervisor | A. Host OS | B. Kernel 안 | 분류 | 비고 |
|---|---|---|---|---|
| **VMware ESXi** | 없음 (vmkernel 이 자체 OS) | Y | Type 1 | 데이터센터 표준 |
| **Xen** | 없음 (Dom0 는 _관리 VM_) | Y | Type 1 | Dom0 분리 모델 |
| **Microsoft Hyper-V** | "Root partition" 이 있지만 _hypervisor 가 먼저 부팅_ | Y | Type 1 | Windows Server 내장 |
| **KVM** | Linux 있음 | Y (kernel module) | Hybrid | Linux 자체가 hypervisor |
| **VirtualBox** | 있음 (Linux/Win/macOS) | N (user-space + `vboxdrv`) | Type 2 | 데스크탑 표준 |
| **VMware Workstation/Fusion** | 있음 | N | Type 2 | 상용 데스크탑 |
| **Parallels** | macOS | N | Type 2 | Apple Silicon |
| **QEMU 단독 (TCG mode)** | 있음 | N (KVM 없을 때) | Type 2 (emulator) | Full SW emulation |

### 4.3 ARM VHE — 분류를 흐리는 HW 기능

ARMv8.1 의 **VHE (Virtualization Host Extensions)** 는 host OS 가 EL1 대신 **EL2 에서 직접 실행** 되게 합니다. 결과: Linux + KVM 이 ARM 에서 켜질 때 두 가지 모드를 동시에 만족합니다.

```
   pre-VHE                           VHE (v8.1+)
   ─────────────────────             ──────────────────────
   EL2 ─── KVM (얇은 shim)          EL2 ─── Linux + KVM 통째로
            │                                │
            │ trap                            │ trap (얇은 hop)
   EL1 ─── Linux + Guest OS         EL1 ─── Guest OS
   EL0 ─── User App                 EL0 ─── User App

   → KVM 이 _Type 2 처럼_ 보이는 구조      → KVM 이 _Type 1 처럼_ 보이는 구조
                                       → 사실상 두 분류의 차이가 무의미해짐
```

이 때문에 "KVM 은 Type 2 다" 라는 표현은 ARM 진영에서는 거의 안 씁니다. **2026 년 기준 production 시각에서는 "KVM = production-grade hypervisor, hosted 형태로 보이지만 성능과 보안은 bare-metal" 이 정확한 표현입니다.**

:::note[VHE 가 host 의 EL1↔EL2 전환을 _구체적으로_ 어떻게 제거하나 — E2H 비트]
pre-VHE 의 문제는 단순했습니다. host Linux kernel 은 EL1 에서 돌도록 짜여 있는데(시스템 레지스터를 `*_EL1` 이름으로 접근), KVM 의 hypervisor 부분은 EL2 에 있어야 했습니다. 그래서 host 코드가 KVM 을 부를 때마다 EL1→EL2→EL1 전환이 필요했습니다 — host 를 EL2 로 그냥 옮기면 되지 않느냐 싶지만, host kernel 코드는 `*_EL1` 레지스터를 만지므로 EL2 에 올려놓으면 _엉뚱한 레지스터_ 를 건드리게 됩니다.

VHE 는 이를 **레지스터 alias** 로 풉니다. `HCR_EL2` 의 **`E2H` 비트** 를 set 하면, EL2 에서 실행 중인 코드가 `*_EL1` 시스템 레지스터에 접근할 때 HW 가 그것을 _자동으로 EL2 의 대응 레지스터로 재해석(alias)_ 합니다. 즉 host kernel 이 `TTBR0_EL1` 을 만지는 코드를 _한 줄도 고치지 않아도_, EL2 에서 돌면 HW 가 그 접근을 적절한 EL2 컨텍스트로 매핑해 줍니다. 그 결과 host kernel 전체를 _재컴파일 없이_ EL2 에서 그대로 돌릴 수 있고, host↔KVM 호출이 같은 EL2 안의 평범한 호출이 되어 EL1↔EL2 전환이 사라집니다.

주의할 점 — VHE 가 없애는 것은 _host_ 측 전환뿐입니다. Guest 는 여전히 EL1 에서 돌므로 **Guest(EL1) ↔ Hypervisor(EL2) 전환은 그대로 존재** 합니다(§6 오해 참조). VHE 의 이득은 "guest 가 빨라짐" 이 아니라 "host kernel 의 KVM 호출 경로가 짧아짐" 입니다.
:::

---

## 5. 디테일 — Type 1 / Type 2 / KVM / Xen / 선택 가이드

### 5.1 Type 1: Bare Metal Hypervisor

Hypervisor 가 **HW 위에 직접** 설치. Host OS 없음:

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

| 항목 | 설명 |
|------|------|
| 성능 | Host OS 계층 없음 → 오버헤드 최소 |
| 보안 | 공격 표면 작음 (Hypervisor만 존재) |
| 용도 | 데이터센터, 클라우드, 서버 가상화 |
| 관리 | 별도 관리 콘솔 필요 (일반 OS가 아니므로) |

Host OS 계층이 없으니 VM 의 trap 이 Hypervisor 로 _직접_ 도달하고, 공격자가 노릴 수 있는 코드 표면도 Hypervisor 코드로만 한정됩니다. 그 대신 일반 OS 의 드라이버 생태계를 쓸 수 없으므로 자체 드라이버를 내장해야 합니다.

:::note[Type 1 이 _왜_ 자체 driver 를 내장해야 하나 — 그리고 Xen 이 Dom0 로 우회한 이유]
"drivers in hypervisor" 를 사실로만 받아들이면 Xen 의 Dom0 가 왜 존재하는지가 안 보입니다. 근본 인과는 이것입니다 — **Type 1 에는 그 아래에 일반 OS 가 없습니다.**

디바이스 드라이버는 보통 Linux·Windows 같은 범용 OS 커널 _안_ 에서 삽니다. 수천 종의 NIC·NVMe·GPU 드라이버는 모두 그 OS 의 driver model(커널 API, 인터럽트 프레임워크, DMA API)에 맞춰 작성됩니다. Type 2 는 그 OS 가 _아래_ 에 있으니 이 방대한 드라이버 생태계를 _공짜로_ 물려받습니다. 그러나 Type 1 은 HW 위에 hypervisor 만 있고 그 아래 OS 가 없으므로, 어떤 디바이스를 쓰려면 **hypervisor 가 자체 driver model 과 드라이버를 직접 가져야** 합니다. 새 HW 마다 hypervisor 벤더가 드라이버를 새로 포팅해야 한다는 뜻이라, HW 호환성 확보가 Type 1 의 본질적 부담입니다.

**Xen 은 이 부담을 Dom0 로 우회했습니다.** Xen hypervisor 본체는 드라이버를 거의 갖지 않는 얇은 microkernel 로 두고, _Dom0 라는 특권 관리 VM 안에서 통째의 Linux 를 돌려_ 그 Linux 의 드라이버 생태계를 빌려 씁니다(§5.5). 즉 "Type 1 이지만 드라이버는 일반 Linux 것을 쓴다" 가 Dom0 모델의 동기입니다 — 자체 드라이버를 다 만드는 대신, 한 VM 에 Linux 를 넣어 그 드라이버를 재사용한 것입니다. ESXi 는 반대로 vmkernel 안에 자체 드라이버를 직접 내장하는 길을 택했고, 그래서 ESXi 의 HW 호환성 목록(HCL)이 좁고 까다로운 것입니다.
:::

대표 구현:

| 이름 | 개발 | 특징 |
|------|------|------|
| **VMware ESXi** | VMware | 상용, 엔터프라이즈 표준 |
| **Xen** | Linux Foundation | 오픈소스, AWS EC2 초기 기반 |
| **Microsoft Hyper-V** | Microsoft | Windows Server 내장 |

### 5.2 Type 2: Hosted Hypervisor

일반 OS(Host OS) **위에** Hypervisor 가 애플리케이션처럼 동작:

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

| 항목 | 설명 |
|------|------|
| 성능 | Host OS 계층 추가 → 오버헤드 더 큼 |
| 편의성 | 기존 OS에 설치 가능 (앱처럼) |
| 용도 | 개발/테스트, 데스크탑 가상화 |
| 관리 | Host OS의 도구 그대로 사용 |

Host OS 가 있으니 기존 드라이버와 도구를 그대로 쓸 수 있어 개발자 입장에서 편리합니다. 반면 VM 의 trap 이 host OS 스케줄러를 거쳐 Hypervisor 앱까지 올라오는 경로가 생기므로 지연이 늘어나고, host OS 의 취약점이 VM 에도 영향을 미칩니다. 그래서 production 서버에는 적합하지 않습니다.

대표 구현:

| 이름 | 개발 | 특징 |
|------|------|------|
| **VirtualBox** | Oracle | 오픈소스, 무료, 크로스 플랫폼 |
| **VMware Workstation** | VMware | 상용, 데스크탑 개발 환경 |
| **Parallels** | Parallels | macOS 전용, Apple Silicon 지원 |
| **QEMU** | 오픈소스 | 에뮬레이터 + 가상화 (KVM과 결합) |

### 5.3 Type 1 vs Type 2 비교

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

### 5.4 경계를 넘는 구현: KVM

**KVM (Kernel-based Virtual Machine)** 은 분류가 모호한 대표적 사례:

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

#### KVM + QEMU 아키텍처

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

#### 역할 분담

| 컴포넌트 | 역할 |
|---------|------|
| **KVM** (커널 모듈) | CPU 가상화 (VT-x/ARM EL2 활용), 메모리 가상화 (EPT/Stage 2), VM Exit 처리 |
| **QEMU** (유저 프로세스) | 디바이스 에뮬레이션 (NIC, 디스크, VGA...), VM 생성/설정 UI |
| **Linux Kernel** | 프로세스 스케줄링, 메모리 관리, HW 드라이버 |

KVM 이 빠르게 성장한 이유는 Linux 커널의 강력한 인프라 — 스케줄러, 드라이버, 메모리 관리 — 를 그대로 활용하면서 CPU 와 메모리 가상화만 HW 지원으로 수행하는 구조 덕분입니다. 중복 투자 없이 두 강점을 동시에 취한 설계입니다.

### 5.5 Xen 아키텍처

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

#### Dom0 vs DomU

| | Dom0 | DomU |
|--|------|------|
| 역할 | 관리 VM (특권) | 일반 VM (비특권) |
| HW 접근 | 물리 드라이버 보유 | Dom0 또는 pass-through 경유 |
| 기능 | VM 생성/삭제, 디바이스 관리 | 사용자 워크로드 실행 |

### 5.6 Hypervisor 선택 가이드

| 시나리오 | 추천 | 이유 |
|---------|------|------|
| 클라우드 서버 | KVM | Linux 생태계, 성능, 유연성 |
| 엔터프라이즈 | ESXi | 안정성, 관리 도구, 지원 |
| AWS/클라우드 초기 | Xen | 격리 모델, para-virtualization |
| 개발/테스트 | VirtualBox/QEMU | 무료, 쉬운 설치 |
| macOS 데스크탑 | Parallels | Apple Silicon 최적화 |
| 임베디드/자동차 | Xen/Type 1 | 실시간성, 보안 격리 |

### 5.7 면접 단골 Q&A

**Q: KVM 은 Type 1 인가 Type 2 인가?**

> "Type 2 관점에서 KVM은 Linux 커널 모듈이고 QEMU가 유저 프로세스로 VM을 관리한다. Type 1 관점에서는 KVM 로드 시 Linux 자체가 Hypervisor 역할을 수행하고 별도 Host OS 계층이 없다. ARM VHE(ARMv8.1+)에서는 Linux+KVM이 EL2에서 직접 실행되어 HW 관점에서 Type 1 Bare Metal과 동일한 구조가 된다. 결론: 구조적으로 Type 2에 가깝지만 성능은 Type 1에 근접하며, VHE 이후 이 구분 자체가 무의미해졌다."

**Q: Xen 에서 Dom0 가 필요한 이유는?**

> "Xen Hypervisor는 Micro-kernel 철학으로 CPU 스케줄링, 메모리 관리, VM 격리만 담당하고 디바이스 드라이버나 관리 인터페이스가 없다. Dom0이 담당하는 것: (1) HW 드라이버 — 물리 디바이스 드라이버는 Dom0의 Linux 커널이 보유, (2) VM 관리 — xl 등 도구로 VM 생성/삭제, (3) I/O 중재 — DomU의 I/O를 para-virtualized backend로 처리, (4) 부팅 — Xen 부팅 후 Dom0이 먼저 시작하여 나머지 DomU 생성. Dom0 없이는 디바이스 사용도 VM 생성도 불가능하다."

:::caution[실무 주의점 — KVM dirty bit emulation 누락 시 live migration 데이터 손실]
**현상**: Live migration 후 destination VM 에서 일부 page 가 source 의 최신 상태와 불일치하여 application 단에서 silent corruption 발생.

**원인**: EPT/NPT 의 D-bit 또는 PML(Page Modification Logging) 설정이 누락되거나, write-protect fault 기반 dirty tracking 에서 race 로 인해 일부 modified page 가 dirty bitmap 에 누락.

**점검 포인트**: `KVM_CAP_MANUAL_DIRTY_LOG_PROTECT` 사용 여부, PML buffer flush 시점, migration 마지막 round 의 throttle threshold, post-copy fallback 활성화 여부.
:::
---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'KVM 은 Type 1 이다']
**실제**: KVM 은 Linux kernel module — 엄밀히는 Type 2 구조이지만 HW assist 활용으로 Type 1 같은 성능. 분류는 학술적 논쟁이고, **두 축 모델 (host OS 유무 / kernel 위치)** 로 보면 별도 칸 (Hybrid) 입니다.<br>
**왜 헷갈리는가**: 성능이 Type 1 급이라 "= Type 1" 으로 단순화. spec 상은 Type 2 모양.
:::
:::danger[❓ 오해 2 — 'Hyper-V 는 host OS (Windows Server) 위에 깔리니까 Type 2 다']
**실제**: Hyper-V 는 Windows Server 부팅 _전에_ 먼저 부팅되고, **Windows Server 자체가 Hyper-V 의 _root partition_ (관리 VM)** 으로 들어갑니다. Xen 의 Dom0 와 같은 위치. 그래서 Microsoft 도 공식 분류는 Type 1.<br>
**왜 헷갈리는가**: 사용자 UI 에서 "Windows 가 먼저 깔린 것처럼" 보이지만 부팅 순서는 정반대.
:::
:::danger[❓ 오해 3 — 'Type 1 이면 무조건 Type 2 보다 빠르다']
**실제**: VHE 가 켜진 KVM (= Hybrid) 은 ARM 환경에서 ESXi 와 거의 동일한 latency 를 냅니다. 반대로 Type 1 이라도 Xen 처럼 Dom0 를 매번 경유해야 하는 I/O 는 KVM 보다 느릴 수 있습니다. **분류 라벨이 아니라 _trap 경로 hop 수_ 와 _host OS scheduler 개입_ 이 실제 성능 변수.**<br>
**왜 헷갈리는가**: "직접 = 빠름" 의 단순화.
:::
:::danger[❓ 오해 4 — 'Type 2 hypervisor 도 production 에 쓸 수 있다']
**실제**: VirtualBox / VMware Workstation 같은 Type 2 는 _host OS 스케줄러가 vCPU 를 throttle_ 합니다. SLA 가 있는 서비스에서는 jitter 가 통제 불가능. Production 은 Type 1 또는 KVM (Hybrid) 만.<br>
**왜 헷갈리는가**: 데스크탑에서 "잘 돌아가는 것" 을 데이터센터 환경으로 일반화.
:::
:::danger[❓ 오해 5 — 'Xen 과 KVM 은 같은 카테고리 (오픈소스 hypervisor)']
**실제**: 둘은 _카테고리가 다릅니다_. Xen 은 **microkernel + Dom0 driver model** (드라이버는 Dom0 의 Linux 가, hypervisor 자체는 얇음). KVM 은 **monolithic kernel + KVM 모듈** (Linux kernel 통째가 hypervisor). 같은 NIC pass-through 라도 Xen 은 Dom0 의 driver path 를 거치고, KVM 은 host Linux 의 VFIO 를 직접 사용. 디버그 path 가 완전히 다릅니다.<br>
**왜 헷갈리는가**: "Linux + 오픈소스" 라는 외형 공통점.
:::
### DV 디버그 체크리스트 (Hypervisor 분류와 trap 경로 관련 흔한 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 같은 코드가 ESXi 에선 빠른데 VirtualBox 에선 30% 느림 | Host OS 스케줄러 jitter (Type 2 특성) | `vmstat`/`top` host 측 CPU steal, VM 의 `/proc/stat` steal time |
| `KVM_RUN` 이 반환되지 않고 hang | KVM kernel module 안에서 무한 loop (또는 VM-Entry 후 Guest hang) | `dmesg | grep kvm`, `perf kvm stat`, NMI watchdog |
| Hyper-V 설치 후 다른 Type 2 hypervisor (VirtualBox) 가 부팅 실패 | Hyper-V 가 이미 VT-x 점유 — root partition 외 두 번째 hypervisor 불가 | `bcdedit /enum`, Hyper-V Platform 기능 toggle |
| KVM + QEMU 에서 `Could not access KVM kernel module` | `/dev/kvm` 권한 또는 VT-x BIOS 비활성 | `ls -l /dev/kvm`, `lscpu | grep -i virt`, BIOS 설정 |
| Xen 에서 DomU 부팅 안 됨 | Dom0 의 toolstack/xen-blkback 미가동 | `xl list`, `xenstore-ls`, Dom0 의 `dmesg | grep xen` |
| ARM 에서 KVM 성능이 x86 KVM 보다 부진 | VHE 미활성화 (pre-v8.1 또는 firmware 설정) | `dmesg | grep -i vhe`, `/sys/devices/system/cpu/cpu0/regs/identification/midr_el1` |
| Production 에서 "VMware 라고만 들었는데" 동작이 ESXi 와 다름 | 실제 deploy 가 VMware Workstation (Type 2) | `dmidecode -s system-product-name`, 호스트 OS 부팅 여부 |
| VM 부팅은 빠른데 disk IO 가 느림 | Hypervisor 유형에 맞는 driver 모델 불일치 (Xen blkback vs KVM virtio) | `lsmod | grep -E 'xen|virtio'`, Guest 의 `/sys/block/*/device/modalias` |

이 체크리스트는 §3 의 부팅 path 가 **어디서 깨질 수 있는지** 의 형식화입니다 — _hop 한 곳이 빠지거나 한 곳이 더 끼면_ 증상이 어떻게 나타나는지의 매핑.

---

## 7. 핵심 정리 (Key Takeaways)

- **Type 1 (Bare Metal)**: HW 위에 직접 hypervisor. ESXi · Xen · Hyper-V. 데이터센터 표준.
- **Type 2 (Hosted)**: Host OS 위에 hypervisor app. VirtualBox · VMware Workstation. 데스크탑.
- **Hybrid (KVM)**: Host OS 가 있지만 hypervisor 가 kernel module — **두 축 모델로 보면 별도 칸**.
- **Xen 의 차별점**: microkernel + Dom0 driver 분리 → 보안 표면 작음, I/O 는 Dom0 경유로 latency.
- **선택 기준**: production cloud → KVM 또는 ESXi, 엔터프라이즈 안정성 → ESXi, 개발 → VirtualBox/QEMU. ARM VHE 이후 KVM vs Type 1 구분은 무의미.

:::caution[실무 주의점]
- **분류 라벨에 휘둘리지 말 것** — trap 경로의 _hop 수_ 와 _host OS scheduler 개입 여부_ 가 실제 성능 변수.
- **Hyper-V 는 Type 1**: Windows Server 부팅 _전_ hypervisor 가 먼저 깔리고, Windows 가 root partition.
- **Type 2 는 production 금지**: jitter 통제 불가, SLA 보장 어려움. 데스크탑/개발 전용.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — KVM 분류 (Bloom: Analyze)]
KVM 은 Type 1 인가 Type 2 인가?
<details>
<summary>정답</summary>

Hybrid — 분류 라벨이 모호한 _가장 좋은_ 예:
- **Type 1 측면**: KVM 모듈이 Linux kernel 내부 → guest 진입 시 user space 거치지 않음 (hypervisor가 kernel mode 에서 직접 실행).
- **Type 2 측면**: Linux 가 _OS_ 로서 깔린 위에 KVM 이 모듈로 로드 → bare-metal hypervisor 가 _아님_.
- 실무 관점: 성능 = Type 1 급, 설치/관리 = Type 2 급 → KVM 이 cloud 의 표준.
- 결론: 분류보다 _trap 경로 hop 수_ 가 실용적 변수.

</details>
:::
:::tip[🤔 Q2 — Type 2 production 금지 (Bloom: Evaluate)]
VirtualBox / VMware Workstation 이 production server 에서 _금지_ 되는 정확한 이유?
<details>
<summary>정답</summary>

Host OS scheduler 가 _hypervisor 위_ 가 아닌 _아래_ → VM 의 시간 보장 깨짐:
- **Jitter**: host 의 다른 user process 가 CPU 점유 시 VM 의 vCPU schedule 지연 → latency-sensitive workload 불가.
- **SLA**: 99.99% 보장 어려움 — host kernel 의 _다른_ 활동에 종속.
- **격리 약화**: host kernel bug 가 모든 VM 에 영향 (Type 1 은 micro-kernel 분리 가능).
- 결론: 데스크탑 (개발/테스트) 에서만 적합. Production 은 KVM / Xen / Hyper-V / ESXi 4 종 중.

</details>
:::
### 7.2 출처

- *KVM: The Linux Virtual Machine Monitor* (OLS 2007)
- VMware *ESXi Architecture* whitepaper
- Microsoft *Hyper-V Architecture* (Type 1 분류 근거)

---

## 다음 모듈

→ [Module 06 — Strict vs Passthrough](../06_strict_vs_passthrough/): 같은 hypervisor 라도 _I/O 를 hypervisor 가 가로채는가 vs VM 이 device 에 직접 닿는가_ 두 모델의 trade-off 와 hybrid 운영.

[퀴즈 풀어보기 →](../quiz/05_hypervisor_types_quiz/)

