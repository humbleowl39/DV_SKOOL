---
title: "Module 01 — OS 개요: 서비스 · Dual-Mode · System Call"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** OS가 하는 두 부류의 일(사용자를 돕는 서비스 vs 시스템 효율을 위한 자원 관리)을 설명할 수 있다.
- **Differentiate** user mode 와 kernel mode 를, mode bit 과 privileged instruction 의 관점에서 구분할 수 있다.
- **Trace** 사용자 프로그램이 system call 을 걸어 kernel 로 진입했다가 복귀하는 경로를 단계별로 추적할 수 있다.
- **Explain** privileged instruction 을 user mode 에서 시도했을 때 하드웨어가 OS 로 trap 하는 이유를 설명할 수 있다.
- **Differentiate** monolithic / microkernel / modules / hybrid kernel 구조의 trade-off 를 비교할 수 있다.
:::
:::note[사전 지식]
- C 언어의 함수 호출 / 라이브러리 개념
- CPU register, instruction 실행 흐름, interrupt 의 막연한 개념
- (출처) Silberschatz, *Operating System Concepts* 10th ed., Ch.1–2
:::
---

## 1. Why care? — DUT 의 "정상"과 "버그"는 OS 의 기대에서 갈린다

검증 엔지니어가 어떤 IP 의 레지스터에 값을 쓰고 결과를 관찰할 때, 그 "기대값"은 결국 OS 가 그 하드웨어를 *어떻게 쓸 작정인가*에서 나옵니다. 예를 들어 어떤 control register 는 반드시 kernel mode 에서만 쓸 수 있어야 하고, user 프로그램이 그것을 건드리려 하면 하드웨어가 막아야 합니다. 만약 DUT 가 user mode 의 접근을 그냥 통과시킨다면, 단위 테스트는 PASS 로 보여도 그것은 보안 구멍입니다.

OS 가 하드웨어 위에서 무엇을 하고, user 와 kernel 의 경계를 어디에 긋고, 프로그램이 OS 에 무엇을 어떻게 요청하는지를 모르면, 우리가 검증하는 mode bit·privileged 동작·trap 경로가 "왜 그렇게 설계됐는지"를 설명할 수 없습니다. 이 모듈은 그 *틀* — kernel 과 그것에 접근하는 유일한 통로인 system call — 을 잡습니다. 나머지 모듈(프로세스·메모리·I/O·동기화·보호)은 모두 이 틀의 한 부분을 확대한 것입니다.

---

## 2. Intuition — 한 줄 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**Dual-mode** ≈ **은행 창구의 방탄 유리**.<br>
손님(user program)은 직접 금고(하드웨어 자원)에 손대지 못하고, 작은 창구 구멍(system call)으로 "이걸 해 달라"고 요청서를 밀어 넣습니다. 창구 안쪽(kernel mode)의 직원만 금고를 열 수 있고, 요청서가 올바른지 매번 확인합니다.
:::
### 한 장 그림 — user 가 OS 에 요청하는 유일한 통로

```d2
direction: down

APP: "**User Program**\n(user mode, mode bit=1)\nlibc/glibc API 호출"
SCI: "**System-Call Interface**\n호출 번호로 테이블 조회"
TRAP: "**trap**\n(software interrupt)\nmode bit → kernel(0)"
KERN: "**Kernel**\n(kernel mode, mode bit=0)\nservice routine 실행\nprivileged instruction 허용"
HW: "**Hardware**\nI/O · timer · interrupt 제어"

APP -> SCI: "API (POSIX/Win32)"
SCI -> TRAP: "syscall 번호"
TRAP -> KERN: "interrupt vector 진입점"
KERN -> HW: "privileged instruction"
KERN -> APP: "return, mode bit → user(1)"
```

### 왜 이 디자인인가 — Design rationale

OS 와 사용자 프로그램이 같은 하드웨어를 공유하므로, 잘못되거나 악의적인 프로그램이 OS 나 다른 프로그램을 망치지 못하게 막아야 합니다. 이 요구가 세 가지 설계 결정으로 이어집니다. 첫째, 실행 모드를 하드웨어가 구분하도록 **mode bit** 을 둡니다(kernel=0, user=1). 둘째, 해를 끼칠 수 있는 명령을 **privileged instruction** 으로 지정해 kernel mode 에서만 허용합니다. 셋째, user 가 OS 의 일을 요청하는 유일한 통로를 **system call(trap)** 하나로 좁혀, 그 진입점에서 인자 검증을 강제합니다.

---

## 3. 작은 예 — `read()` 한 번이 kernel 을 거쳐 돌아오는 과정

C 프로그램이 파일에서 데이터를 읽는 가장 단순한 시나리오를 따라가 봅시다. 개발자는 system call 을 직접 부르지 않고 라이브러리 함수를 부르며, 그 사이를 system-call interface 가 잇습니다.

```c
// user mode 에서 실행
ssize_t n = read(fd, buf, 100);   // libc 래퍼 호출
```

### 단계별 다이어그램

```d2
direction: right

U: "① user: read() 호출\n(libc 래퍼)" 
SCI: "② system-call interface\nread 번호로 테이블 조회"
T: "③ trap → kernel mode\nmode bit 0"
K: "④ kernel: sys_read\n인자 검증 후 I/O 수행"
R: "⑤ return\nmode bit 1, 결과 n"

U -> SCI -> T -> K -> R
```

### 단계별 의미

| Step | 어디서 | 무엇을 | 왜 |
|---|---|---|---|
| ① | user mode | `read()` libc 래퍼 호출 | 개발자는 API 만 안다 (Ch.2.3.2) |
| ② | system-call interface | read 에 매긴 번호로 테이블 조회 | 어떤 kernel 루틴인지 결정 (Ch.2.3.2) |
| ③ | 하드웨어 | trap(software interrupt), mode bit → 0 | kernel 이 제어를 쥘 때는 늘 kernel mode (Ch.1.4.2) |
| ④ | kernel mode | 호출 종류·인자 검증 후 수행 | 잘못된 인자가 OS 를 망치지 못하게 |
| ⑤ | 하드웨어 | return-from-trap, mode bit → 1 | user 로 안전하게 복귀 |

:::note[여기서 잡아야 할 두 가지]
**(1) user 코드는 절대 직접 하드웨어를 만지지 않는다.** 모든 요청은 trap 을 통해 kernel 로 들어가고, kernel mode 에서만 privileged instruction(I/O 제어·timer·interrupt 관리)이 실행됩니다.<br>
**(2) 인자는 register, 메모리 block, 또는 stack 으로 전달**됩니다(Ch.2.3.2). DV 관점에서 이 "인자 전달 약속"이 곧 우리가 검증하는 레지스터/메모리 인터페이스의 원형입니다.
:::
---

## 4. 일반화 — OS 의 두 부류 일과, 모드 확장

### 4.1 OS 가 하는 일 (Ch.2.1)

OS 는 hardware 위에서 두 부류의 일을 합니다. 하나는 *사용자를 돕는* 서비스이고, 다른 하나는 *시스템 자체의 효율*을 위한 자원 관리입니다. 요약하면 OS 는 **자원 관리자(resource manager)** 이자 **하드웨어 추상화 계층(hardware abstraction layer)** 입니다.

| 분류 | 서비스 | DV/HW 관점 연결 |
|------|--------|----------------|
| 사용자 지원 | user interface (GUI/CLI) | — |
| 사용자 지원 | program execution | M02 process/스케줄링 |
| 사용자 지원 | I/O operations | M04 MMIO/interrupt/DMA |
| 사용자 지원 | file-system manipulation | M04 mass storage |
| 사용자 지원 | communication (shared memory / message passing) | M05 동기화 |
| 사용자 지원 | error detection | M04 ECC, RAS |
| 시스템 효율 | resource allocation (CPU/메모리/저장) | M02·M03 |
| 시스템 효율 | accounting | — |
| 시스템 효율 | protection & security | M06 ring/access matrix |

### 4.2 모드는 둘을 넘어 확장된다 (Ch.1.4.2)

가장 단순한 dual-mode 는 user/kernel 둘뿐이지만, 실제 아키텍처는 더 잘게 나눕니다. Intel 은 네 개의 **protection ring**(ring 0 = kernel, ring 3 = user)을 두고, ARMv8 은 일곱 모드를 가지며, 가상화를 지원하는 CPU 는 VMM(virtual machine manager)을 위한 별도 모드를 둡니다. 이 ring 모델은 M06 에서 일반화해 다시 다룹니다 — dual-mode 는 ring 모델의 가장 단순한 두 단계입니다.

```d2
direction: right
U: "user mode\n(mode bit=1, ring 3)"
K: "kernel mode\n(mode bit=0, ring 0)"
U -> K: "trap / interrupt / system call"
K -> U: "return (mode bit → user)"
```

:::note[mode bit 이 _하드웨어로_ 강제되는 물리적 기전 — decode 단계의 게이팅]
"하드웨어가 강제한다" 는 말의 실체는 CPU 파이프라인의 **instruction decode(명령 해독) 단계** 에 있습니다. CPU 가 명령을 fetch 한 뒤 decode 하는 그 순간, decoder 는 그 opcode 가 _privileged 부류인지_ 를 식별하고, 동시에 현재 실행 모드를 나타내는 **mode bit(또는 current privilege level 레지스터)** 을 읽습니다. 이 둘을 작은 조합 논리가 비교합니다 — 대략 `(privileged_opcode == 1) AND (mode_bit == user)` 가 참이면, 그 명령을 실행 유닛으로 보내는 대신 **exception/trap 을 raise** 하도록 datapath 가 분기합니다.

핵심은 이 검사가 _소프트웨어 한 줄도 거치지 않고_ 매 명령의 decode 와 _같은 cycle_ 에 하드웨어 회로로 일어난다는 점입니다 — 그래서 user 코드가 아무리 빨라도, 무엇을 끼워 넣어도 이 게이트를 우회할 수 없습니다(흔한 오해 1). DV 관점에서 이 "privileged opcode × mode bit → trap" 게이팅 로직이 바로 우리가 검증해야 할 _대상 회로_ 입니다: privileged 명령을 user mode 로 주입했을 때 실행 유닛에 도달하지 _못하고_ 정확한 exception 이 뜨는지를 봐야 합니다.
:::

### 4.3 System call 의 여섯 갈래 (Ch.2.3.3)

system call 은 크게 여섯 갈래입니다: **process control**, **file management**, **device management**, **information maintenance**, **communication**, **protection**. device management 갈래가 우리가 검증하는 컨트롤러의 OS 측 진입점에 해당합니다.

---

## 5. 디테일 — Kernel 구조의 네 가지 방식 (Ch.2.8)

거대한 OS 는 모듈로 나눠 설계하며, kernel 을 엮는 방식이 여럿입니다. 각 방식은 성능과 확장성·안전성 사이의 trade-off 입니다.

| 구조 | 핵심 | 장점 | 단점 | 예 |
|------|------|------|------|----|
| **Monolithic** | kernel 전부를 하나의 주소공간에 | system-call 오버헤드 적어 빠름 | 확장 어려움 | UNIX·Linux·Windows 의 흔적 |
| **Layered** | layer 0(hardware)~N(UI) 층층이, 각 층은 아래 층만 사용 | 디버깅 쉬움 | 여러 층 경유 오버헤드 | — |
| **Microkernel** | 꼭 필요한 것만 kernel, 나머지는 user space + message passing | 안전·이식적 | 메시지 복사·context switch 오버헤드 | Mach, Darwin(macOS/iOS), QNX |
| **Modules (LKM)** | 핵심만 kernel, 나머지는 실행 중 동적 링크 | 유연 | — | Linux·macOS·Solaris·Windows |

실제 시스템은 대개 이들을 섞은 **hybrid** 입니다. 예컨대 Linux 는 성능을 위해 monolithic 이면서도 LKM(loadable kernel module)으로 modular 합니다. DV 관점에서 의미 있는 점은, 우리가 작성하는 device driver 가 보통 LKM 으로 들어가며, microkernel 에서는 driver 가 user space 에서 message passing 으로 동작한다는 차이입니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'user 프로그램도 빠르면 직접 하드웨어를 만질 수 있다']
**실제**: user mode 에서 privileged instruction(I/O 제어·timer·interrupt 관리)을 시도하면 하드웨어가 *실행하지 않고* OS 로 trap 합니다(Ch.1.4.2). 속도와 무관하게, 경계는 mode bit 으로 하드웨어가 강제합니다.<br>
**왜 헷갈리는가**: 응용 코드가 메모리에 직접 load/store 하는 것처럼 보여서 — 그러나 그 주소는 이미 OS 가 허용한 영역으로 한정돼 있습니다(M03).
:::
:::danger[❓ 오해 2 — 'system call 과 일반 함수 호출은 거의 같다']
**실제**: 일반 함수 호출은 같은 mode 안에서의 점프이지만, system call 은 **trap 을 걸어 mode bit 을 바꾸고** interrupt vector 의 진입점으로 들어갑니다(Ch.1.4.2). 그래서 비용이 훨씬 크고, 그 경계에서 인자 검증이 일어납니다.<br>
**왜 헷갈리는가**: 개발자가 보기엔 똑같이 `read()` 처럼 부르기 때문 — libc 래퍼가 trap 을 가립니다.
:::

#### trap 이 함수 호출보다 _구체적으로_ 왜 비싼가 — 비용의 분해

일반 함수 호출은 사실상 "return 주소를 stack 에 push 하고 target 으로 점프" 가 거의 전부입니다 — 같은 mode, 같은 주소공간, 같은 권한이라 추가 절차가 없습니다. system call(trap)은 그 위에 다음 비용이 _더_ 얹힙니다:

1. **mode/stack 전환** — user → kernel 로 mode bit 을 바꾸고, user stack 이 아닌 _kernel stack_ 으로 갈아탑니다(user stack 을 kernel 이 신뢰할 수 없으므로). 이 전환 자체가 레지스터 저장과 stack pointer 교체를 수반합니다.
2. **interrupt vector 를 통한 _간접_ 점프** — 함수 호출처럼 컴파일 타임에 고정된 주소로 직접 가는 게 아니라, syscall 번호로 vector/dispatch table 을 한 번 _조회_ 한 뒤 그 진입점으로 갑니다. 이 간접 분기는 직접 호출보다 비싸고 분기 예측에도 불리합니다.
3. **권한·인자 검증** — kernel 은 넘어온 인자(특히 user 가 준 포인터)를 _신뢰하지 않으므로_ 매 진입마다 유효성·권한을 검사합니다. 함수 호출에는 없는 단계입니다.
4. **파이프라인/캐시 영향** — mode 전환은 흔히 파이프라인 동기화를 강제하고, kernel 코드·데이터로 작업셋이 바뀌며 캐시·TLB 가 일부 오염됩니다.

이 네 가지가 합쳐져 trap 은 단순 함수 호출의 수십~수백 배 비용이 됩니다. **이것이 syscall 을 가능한 한 _batch_ 하는(예: `readv`/`writev` 로 여러 I/O 를 한 번에, 또는 버퍼링) 근본 동기** 입니다 — 경계를 넘는 횟수 자체를 줄이는 게 이득이기 때문입니다.
:::danger[❓ 오해 3 — 'monolithic 이 microkernel 보다 무조건 낡았다']
**실제**: monolithic 은 system-call 오버헤드가 적어 빠르고, 그래서 Linux 도 monolithic 을 유지합니다(Ch.2.8). microkernel 은 안전·이식성을 얻는 대신 message passing 오버헤드를 감수합니다 — 둘은 우열이 아니라 trade-off 입니다.<br>
**왜 헷갈리는가**: "더 모듈화 = 더 현대적"이라는 단순화 때문.
:::

#### monolithic 의 오버헤드가 _왜_ 더 적은가 — 서비스 호출 방식의 기전 차이

"오버헤드가 적다" 는 결과 뒤에는 _OS 서비스끼리 어떻게 서로를 부르는가_ 의 기전 차이가 있습니다. **monolithic** 에서는 파일시스템·드라이버·네트워크 스택 같은 서비스가 _모두 같은 kernel 주소공간_ 안에 함께 있습니다. 그래서 한 서비스가 다른 서비스를 호출하는 일은 그냥 **같은 주소공간 안의 함수 호출** 입니다 — 포인터로 데이터를 넘기고 점프하면 끝이라, 추가 복사도 mode 전환도 없습니다.

**microkernel** 에서는 그 서비스들이 _제각각 별도의 user-space 프로세스_ 로 분리돼 있습니다. 따라서 한 서비스가 다른 서비스의 기능을 쓰려면 **message passing** 을 해야 하는데, 이는 (a) 보내는 쪽 주소공간의 데이터를 메시지로 _복사_ 하고, (b) kernel 을 거쳐 받는 쪽으로 전달하며, (c) 그 과정에서 **context switch**(프로세스 전환)가 일어납니다. 즉 monolithic 의 단순 함수 호출 한 번이, microkernel 에서는 _복사 + context switch_ 를 동반하는 IPC 한 라운드로 바뀝니다.

이 기전 차이가 바로 trade-off 의 양면입니다 — microkernel 은 서비스를 격리해 한 서비스가 죽어도 kernel 이 안 무너지는 _fault isolation_ 을 얻지만, 그 격리(별도 주소공간)가 곧 복사·전환 비용의 원천입니다. monolithic 은 그 비용을 없앤 대신 모든 서비스가 한 주소공간을 공유해 한 결함이 전체에 번질 수 있습니다.
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| user 접근이 막혀야 할 control register 를 통과시킴 | mode bit/privilege 체크 누락 | DUT 의 access-mode 게이팅 로직, spec 의 privilege 요구 |
| system call 경로에서 인자 검증 없이 수행 | trap handler 의 validation 누락 | kernel 진입점, 인자 전달 방식(register/block/stack) |
| trap 후 mode bit 이 user 로 복귀 안 됨 | return-from-trap 처리 오류 | mode bit 상태 머신 |
| 동일 명령이 mode 따라 다른 결과여야 하는데 동일 | privileged instruction 분류 누락 | spec 의 privileged instruction 목록 |

---

## 7. 핵심 정리 (Key Takeaways)

- **OS = 자원 관리자 + 하드웨어 추상화 계층.** 사용자 지원 서비스와 시스템 효율을 위한 자원 관리, 두 부류의 일을 한다.
- **Dual-mode 가 보호의 토대.** mode bit(kernel=0/user=1)으로 하드웨어가 모드를 구분하고, privileged instruction 은 kernel mode 에서만 허용한다.
- **System call 이 user→kernel 의 유일한 통로.** trap(software interrupt)으로 진입해 인자 검증 후 수행하고 복귀한다. 인자는 register/메모리 block/stack 으로 전달.
- **모드는 확장된다.** dual-mode 는 protection ring(M06)의 가장 단순한 두 단계이며, 가상화는 그보다 높은 ring(-1/EL2)을 둔다.
- **Kernel 구조는 trade-off.** monolithic(빠름) / microkernel(안전·이식) / modules(유연) / hybrid(실제 대부분).

:::caution[실무 주의점]
- DUT 의 어떤 레지스터가 "privileged 전용"인지 spec 에서 먼저 확인하고, user-mode 접근 시 trap/거부되는지 반드시 테스트하세요 — silent pass 가 가장 위험합니다.
- system call 의 인자 전달 방식(register vs 메모리 block)은 우리가 검증하는 command/descriptor 인터페이스 설계와 직결됩니다.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — Privileged instruction trap (Bloom: Analyze)]
user 프로그램이 I/O 제어 명령(privileged)을 직접 실행하려 한다. 하드웨어는 무엇을 하고, 그 결과 제어는 어디로 가는가?
<details>
<summary>정답</summary>

하드웨어가 그 명령을 *실행하지 않고* OS 로 **trap** 을 겁니다(Ch.1.4.2):
- mode bit 이 user(1)이므로 privileged instruction 은 차단되고, 자동으로 kernel mode(0)로 전환되며 OS 의 trap handler 로 점프.
- OS 는 위반을 처리(보통 프로세스 종료 또는 에러 반환).
- 핵심: 이 차단은 *소프트웨어가 아니라 하드웨어*가 mode bit 으로 강제 — DV 에서는 이 게이팅이 DUT 에 제대로 구현됐는지가 검증 포인트.

</details>
:::
:::tip[🤔 Q2 — Kernel 구조 선택 (Bloom: Evaluate)]
실시간 안전성이 최우선인 임베디드 시스템(자동차 등)에서 microkernel 이 선호되는 이유와, 그 대가는?
<details>
<summary>정답</summary>

- **이유**: microkernel 은 꼭 필요한 것만 kernel 에 남기고 driver·서비스를 user space 로 빼므로(Ch.2.8), 한 서비스가 죽어도 kernel 전체가 무너지지 않아 *fault isolation* 과 안전성이 높다(QNX 가 대표). 또 코드가 작아 검증·인증이 쉽다.
- **대가**: 서비스 간 통신이 message passing 이라 메시지 복사 + context switch 오버헤드가 커 성능이 낮아질 수 있다.
- 그래서 범용 고성능 OS(Linux)는 monolithic+LKM hybrid 를 택한다.

</details>
:::
### 7.2 출처

**External**
- Silberschatz, Galvin, Gagne. *Operating System Concepts*, 10th ed., Wiley 2018 — **Ch.1 Introduction**(§1.4.2 dual-mode), **Ch.2 Operating-System Structures**(§2.1 서비스, §2.3 system call, §2.8 kernel 구조)

---

## 다음 모듈

→ [Module 02 — 프로세스 · 스레드 · CPU 스케줄링](../02_process_scheduling/): 이 틀 위에서 "program execution"이 구체적으로 어떻게 process 가 되고, CPU 가 그들 사이를 어떻게 오가는가.

[퀴즈 풀어보기 →](../quiz/01_os_overview_quiz/)
