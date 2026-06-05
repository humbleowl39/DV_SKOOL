---
title: "02 — Side-effect & 메모리 배리어"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Differentiate** I/O 레지스터 접근의 side-effect가 일반 메모리 접근과 무엇이 다른지 구분할 수 있다.
- **Explain** CPU/컴파일러의 캐싱과 재정렬이 왜 RAM에는 안전하지만 I/O 의미를 깨뜨리는지 설명할 수 있다.
- **Apply** `barrier()` / `rmb()` / `wmb()` / `mb()` 네 가지 배리어를 디바이스 접근 순서가 중요한 위치에 올바르게 배치할 수 있다.
- **Differentiate** "uncached 매핑"이 막는 문제와 "메모리 배리어"가 막는 문제가 서로 다른 층위임을 구분할 수 있다.
:::
:::note[사전 지식]
- [01 — 디바이스 레지스터 & MMIO/PMIO](../01_registers_mmio_pmio/)
- 캐시·out-of-order 실행의 존재 (정확한 동작까지는 불필요)
:::
---

## 1. Why care? — 디스크립터를 준비하기도 전에 도어벨이 울렸다

### 1.1 시나리오 — write 두 개의 순서가 뒤집힌다

NIC 드라이버가 패킷을 보내는 전형적 코드입니다. DRAM에 디스크립터를 채우고, 그다음 디바이스의 도어벨 레지스터에 tail 포인터를 써서 "새 일감이 있다"고 알립니다.

```c
desc->addr = dma_addr;      /* (1) 디스크립터 DRAM에 기록 */
desc->len  = pkt_len;       /* (2) */
writel(tail, regs + DOORBELL);  /* (3) 도어벨 — "준비됐다" */
```

소스 코드 순서로는 (1)(2)가 (3)보다 먼저입니다. 그러나 CPU와 컴파일러는 성능을 위해 메모리 연산을 자유롭게 재정렬합니다. (3)의 도어벨 write가 (1)(2)보다 *먼저* 디바이스에 도달하면, 디바이스는 아직 쓰레기가 든 디스크립터를 읽어 잘못된 주소로 DMA를 일으킵니다. RAM끼리였다면 재정렬돼도 결과가 같지만, 도어벨에는 "디바이스를 깨운다"는 **side-effect**가 있어 순서가 의미를 갖습니다.

이것이 이 장의 핵심입니다. **I/O 레지스터는 메모리처럼 생겼지만 부작용이 있고, 그래서 CPU·컴파일러의 평범한 최적화가 디바이스 동작을 깨뜨립니다.**

### 1.2 side-effect의 정의

> "*The main difference between I/O registers and RAM is that I/O operations have side effects, while memory operations have none: the only effect of a memory write is storing a value to a location, and a memory read returns the last value written there.*" — LDD3 §I/O Registers and Conventional Memory (p.236)

메모리 write의 유일한 효과는 값 저장이고, read는 마지막으로 쓴 값을 돌려줄 뿐입니다. 반면 I/O는 read가 FIFO를 pop하거나 status를 클리어하고, write가 동작을 트리거합니다. 그래서 "값이 같으니 read를 생략하자", "순서를 바꿔도 결과가 같으니 재정렬하자" 같은 최적화가 *틀린* 전제가 됩니다.

---

## 2. Intuition — 두 종류의 위험, 한 장 그림

:::tip[💡 한 줄 비유]
**캐싱 문제** ≈ **메모를 복사해 책상에 붙여두고 그것만 보는 것**. 디바이스(상사)가 원본을 바꿔도 내 책상의 복사본은 그대로라, 나는 옛 정보를 계속 봅니다(stale read). 해법: 복사 금지 = uncached.<br>
**재정렬 문제** ≈ **할 일 목록을 효율 순서로 멋대로 바꿔 처리하는 것**. "재료 준비 → 요리 시작"인데 순서를 바꿔 빈 냄비에 불을 켭니다. 해법: "이 줄을 넘기 전에 위는 끝내라"는 칸막이 = memory barrier.
:::

### 한 장 그림 — 두 위험과 두 방어

```d2
direction: down

SRC: "**소스 코드**\ndesc 기록 → 도어벨 write"

C1: "**위험 1: 캐싱**\nread가 캐시에서 stale 값\nwrite가 캐시에 머물러 디바이스 미도달" { style.fill: "#f5b7b1" }
C2: "**위험 2: 재정렬**\n컴파일러/CPU가 순서 변경\n도어벨이 디스크립터보다 먼저 도달" { style.fill: "#f5b7b1" }

D1: "**방어 1: uncached 매핑**\nioremap → 캐시 우회\n모든 접근이 디바이스에 직접" { style.fill: "#abebc6" }
D2: "**방어 2: 메모리 배리어**\nwmb() 등으로 순서 고정\n'이 지점 전 write 먼저 완료'" { style.fill: "#abebc6" }

SRC -> C1
SRC -> C2
C1 -> D1: "막음"
C2 -> D2: "막음"
```

두 위험은 **서로 다른 층위**입니다. uncached는 "디바이스에 *닿느냐*"를, 배리어는 "닿는 *순서*"를 다룹니다. uncached로 매핑해도 컴파일러/CPU가 두 write의 순서를 바꾸는 것은 여전히 막아야 하므로, 둘 다 필요합니다.

---

## 3. 작은 예 — 도어벨 시퀀스를 올바르게 만들기

### 단계별 다이어그램

```d2
direction: down

S1: "**① 디스크립터 write**\ndesc->addr, desc->len\n(DRAM, cacheable)"
S2: "**② wmb()**\nwrite barrier\n위의 write들이 *먼저* 가시화되도록 보장"
S3: "**③ 도어벨 write**\nwritel(tail, DOORBELL)\n(MMIO, uncached)"
S4: "**④ 디바이스가 도어벨 관찰**\n이제 디스크립터는 *반드시* 유효\n→ 안전하게 DMA"
S1 -> S2 -> S3 -> S4
```

### 단계별 의미

| 단계 | 무엇 | 왜 |
|------|------|----|
| ① | 디스크립터를 DRAM에 기록 | 디바이스가 읽을 일감 준비 |
| ② | `wmb()` write barrier | ① write들이 ③보다 *먼저* 완료·가시화되도록 강제. 없으면 재정렬 가능 |
| ③ | 도어벨 레지스터 write(uncached MMIO) | 디바이스 깨우기 — side-effect 있는 write |
| ④ | 디바이스가 도어벨 보고 디스크립터 소비 | ②가 있었으므로 디스크립터는 유효 보장 |

### 코드로 보기

```c
/* 잘못된 버전 — 배리어 없음 */
desc->addr = dma_addr;
desc->len  = pkt_len;
writel(tail, regs + DOORBELL);   /* 재정렬되면 디바이스가 쓰레기 디스크립터를 읽음 */

/* 올바른 버전 — write barrier로 순서 고정 */
desc->addr = dma_addr;
desc->len  = pkt_len;
wmb();                           /* 위 write들이 도어벨보다 먼저 가시화 */
writel(tail, regs + DOORBELL);

/* 읽기 쪽 예 — status를 읽고 그 후 데이터를 읽어야 할 때 */
u32 st = readl(regs + STATUS);
rmb();                           /* status read가 data read보다 먼저 완료 */
u32 data = readl(regs + DATA);
```

:::note[여기서 잡아야 할 두 가지]
**(1) uncached 매핑만으로는 *순서*가 보장되지 않습니다.** uncached는 캐시를 우회해 디바이스에 닿게 할 뿐, 컴파일러/CPU가 두 연산의 순서를 바꾸는 것은 배리어가 막습니다.<br>
**(2) 배리어는 "방향"이 있습니다.** `wmb()`는 write끼리, `rmb()`는 read끼리, `mb()`는 모두의 순서를 고정합니다. 잘못된 종류를 쓰면 보호하려던 순서가 안 지켜집니다.
:::

---

## 4. 일반화 — 캐싱·재정렬과 네 가지 배리어

### 4.1 왜 RAM에는 안전하고 I/O에는 위험한가

CPU와 컴파일러는 속도를 위해 메모리 연산을 공격적으로 캐싱하고 재정렬합니다. RAM에서는 두 동작 모두 안전합니다 — 최종적으로 같은 값이 같은 위치에 있으면 그만이기 때문입니다. 그러나 I/O에서는 두 가지 방식으로 깨집니다 (Wikipedia MMIO/PMIO; LDD3 p.236):

- **컴파일러가 write를 레지스터로 최적화**해 버리면 디바이스는 그 write를 영영 관찰하지 못합니다.
- **CPU/컴파일러가 순서를 바꾸면** 디바이스가 소스 코드와 다른 순서로 write를 관찰합니다.

### 4.2 두 방어의 분리

| 방어 | 막는 것 | Linux에서 | RTL/검증 관점 |
|------|---------|-----------|----------------|
| **uncached 매핑** | 캐싱(stale read, 미도달 write) | `ioremap()` 등이 강제 — "*already configured ... to disable any hardware cache when accessing I/O regions*" (LDD3 p.237) | 디바이스에 *닿는지* |
| **memory barrier** | 재정렬(순서 뒤바뀜) | `barrier`/`rmb`/`wmb`/`mb` | 닿는 *순서* |

### 4.3 네 가지 배리어(LDD3 기준)

LDD3는 Linux의 네(+1) 배리어를 듭니다 (LDD3 §I/O Ports and I/O Memory, p.237):

| 배리어 | 범위 | 막는 것 |
|--------|------|---------|
| `barrier()` | **컴파일러만** | 컴파일러의 재정렬(레지스터 캐싱 포함). CPU 재정렬은 못 막음 |
| `rmb()` | read | 배리어 앞의 read가 뒤의 read보다 먼저 완료 |
| `wmb()` | write | 배리어 앞의 write가 뒤의 write보다 먼저 완료 |
| `mb()` | read+write(full) | 앞의 모든 메모리 연산이 뒤보다 먼저 완료 |

추가로 `read_barrier_depends()`가 데이터 의존 read 순서를 위해 존재합니다. 핵심 직관: **`barrier()`는 컴파일러만, `rmb/wmb/mb`는 CPU(+컴파일러)까지** 막습니다. 디바이스가 관련된 순서에는 보통 `rmb/wmb/mb`가 필요합니다.

---

## 5. 디테일 — 어디에 어떤 배리어를, 그리고 DV로의 환산

### 5.1 배리어 배치 규칙(직관)

- **두 write의 순서가 디바이스에 보여야 한다** → 두 write 사이에 `wmb()`. (디스크립터 → 도어벨)
- **read한 값에 따라 다음 read가 의미를 갖는다** → 두 read 사이에 `rmb()`. (status 확인 후 data 읽기)
- **write 후 그 효과를 read로 확인해야 한다(서로 다른 방향)** → `mb()`. (control write → status readback)
- **순수 컴파일러 재정렬만 막으면 된다(같은 코어, 캐시 일관)** → `barrier()`.

### 5.2 DV 관점 — 순서/side-effect를 레지스터·드라이버 레벨에서 검증

배리어는 소프트웨어 구문이지만, *그 배리어가 보호하려는 순서 규칙*은 RTL 동작이자 검증 대상입니다.

| 검증 대상 | 무엇을 확인 | 어떻게 |
|-----------|-------------|--------|
| read side-effect | clear-on-read / FIFO-pop status가 read마다 올바르게 갱신 | directed read 2회 → 두 번째 값 변화 확인. RAL `peek`(흉내 없음) vs frontdoor read(흉내) 비교 |
| write side-effect | control write가 의도한 동작만 트리거(W1C가 옆 비트 안 건드림) | write 후 status/동작 관찰, 인접 필드 불변 확인 |
| 순서 의존(디스크립터→도어벨) | 도어벨이 울린 *시점에* 디스크립터가 유효한가 | 시퀀스에서 디스크립터 write → 도어벨 write 순서로 자극, scoreboard가 디바이스가 읽은 디스크립터 내용 검증 |
| uncached 가정 | DUT가 write를 즉시 반영하는가(버퍼링 지연 없음) | back-to-back write/read로 latency·순서 관찰 |

검증 환경 자체에서도 같은 함정이 있습니다. RAL의 `peek/poke`는 side-effect를 *흉내내지 않고* 값을 강제하지만 back-door `read/write`는 frontdoor의 side-effect(clear-on-read 등)를 *재현*합니다 — clear-on-read 필드를 건드리지 않고 보려면 `peek`을 써야 합니다. 이 구분은 [UVM RAL §peek/poke](../../uvm/07_register_layer_ral/)에서 상세합니다.

### 5.3 read-to-clear의 함정 (예)

```c
/* status를 두 번 읽으면 두 번째가 0일 수 있다 — read-to-clear */
u32 s1 = readl(regs + INT_STATUS);  /* 비트들이 set 상태로 읽힘 + 읽는 순간 클리어 */
u32 s2 = readl(regs + INT_STATUS);  /* 이미 클리어됐으면 0 */
/* → "두 번 읽어 비교"는 read side-effect를 무시한 안티패턴 */
```

검증에서는 이 동작이 *스펙대로*인지(read 한 번에 정확히 한 번 클리어, 새 이벤트는 다시 set)를 directed 시나리오로 확인해야 합니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'uncached로 매핑했으니 순서는 자동으로 보장된다']
**실제**: uncached는 캐시를 우회해 디바이스에 *닿게* 할 뿐, 두 연산의 *순서*는 보장하지 않습니다. 컴파일러/CPU 재정렬은 별도로 배리어가 막아야 합니다. uncached와 barrier는 서로 다른 문제의 해법입니다.<br>
**왜 헷갈리는가**: "캐시 끄면 다 해결"이라는 단순 모델 때문에.
:::
:::danger[❓ 오해 2 — 'barrier() 하나면 CPU 재정렬도 막힌다']
**실제**: `barrier()`는 *컴파일러* 재정렬만 막습니다. CPU의 out-of-order/store-buffer 재정렬은 `rmb()`/`wmb()`/`mb()`가 막습니다. 디바이스가 관련된 순서에 `barrier()`만 쓰면 CPU 레벨에서 여전히 뒤집힐 수 있습니다.<br>
**왜 헷갈리는가**: 이름이 "barrier"라 모든 재정렬을 막을 것 같아서.
:::
:::danger[❓ 오해 3 — 'status를 두 번 읽어 비교하면 안전하다']
**실제**: clear-on-read나 FIFO-pop status는 read 자체에 side-effect가 있어, 두 번째 read가 이미 다른 값(보통 0)일 수 있습니다. read는 한 번만 하고 값을 변수에 보관해 쓰는 것이 원칙입니다.<br>
**왜 헷갈리는가**: RAM 변수처럼 "여러 번 읽어도 같다"고 가정해서.
:::
:::danger[❓ 오해 4 — '재정렬은 멀티코어에서만 문제다']
**실제**: 단일 코어에서도 컴파일러 재정렬과 store buffer로 인해 디바이스가 보는 순서가 소스와 달라질 수 있습니다. 디바이스(별도 관찰자)가 끼면 같은 코어여도 배리어가 필요합니다.<br>
**왜 헷갈리는가**: "내 코어 하나면 순차 실행"이라는 인상 때문에.
:::

### DV 디버그 체크리스트 (이 장 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|------|----------|-----------|
| 폴링 루프가 영원히 안 끝남 | MMIO가 cacheable로 매핑 → stale read | 매핑 속성(`ioremap` 여부), DUT가 새 값 즉시 반영하는지 |
| 디바이스가 쓰레기 디스크립터를 DMA | 디스크립터 write가 도어벨보다 늦게 도달(배리어 누락) | 드라이버의 `wmb()` 위치, 자극 시퀀스의 write 순서 |
| status read마다 값이 달라짐 | clear-on-read / FIFO-pop side-effect | 레지스터 access policy(W1C/RC), RAL peek vs read 차이 |
| write가 디바이스에 반영 안 됨 | 컴파일러가 write 최적화/캐시에 머묾 | `volatile`/`writel` 사용, uncached 매핑 |
| 인접 비트가 의도치 않게 바뀜 | byte-enable 미지원 → 전체 RMW로 옆 필드 오염 | adapter byte-enable, field individually_accessible |

---

## 7. 핵심 정리 (Key Takeaways)

- **I/O 레지스터 ≠ RAM**: read/write에 side-effect가 있어, "값 같으면 생략·순서 바꿔도 무방"이라는 최적화 전제가 깨진다.
- **두 위험은 서로 다른 층위**: 캐싱(닿느냐) ↔ 재정렬(순서). 각각 uncached 매핑과 memory barrier로 막는다.
- **uncached만으로 순서는 보장되지 않는다** — 배리어가 별도로 필요.
- **네 배리어**: `barrier()`(컴파일러만), `rmb()`(read), `wmb()`(write), `mb()`(full). 디바이스가 끼면 보통 `rmb/wmb/mb`.
- **DV 환산**: read/write side-effect, 순서 의존(디스크립터→도어벨), uncached 가정을 레지스터·드라이버 레벨 directed 시나리오로 검증. RAL `peek`(흉내❌) vs back-door `read`(흉내) 구분이 중요.

:::caution[실무 주의점]
- 디스크립터 준비 → 도어벨 사이에는 *반드시* `wmb()`.
- status는 한 번만 read해 변수에 보관 — clear-on-read를 두 번 읽지 말 것.
- 검증에서 clear-on-read 필드를 *건드리지 않고* 보려면 RAL `peek`(back-door read는 클리어 재현).
:::

### 7.1 자가 점검

:::tip[🤔 Q1 — 배리어 종류 선택 (Bloom: Apply)]
디바이스에 `desc->ready = 1`을 쓴 뒤 도어벨 레지스터에 tail을 쓰는 코드가 있다. 단일 코어 시스템이지만 디바이스가 두 write의 순서를 보장받아야 한다. `barrier()`로 충분한가?
<details>
<summary>정답</summary>

**불충분합니다.** `barrier()`는 컴파일러 재정렬만 막고, CPU의 store buffer/out-of-order로 인한 재정렬은 막지 못합니다. 디바이스(별도 관찰자)가 두 write의 순서를 봐야 하므로, store가 디바이스에 가시화되는 순서를 보장하는 `wmb()`가 필요합니다. 단일 코어여도 디바이스가 끼면 CPU 레벨 배리어가 요구됩니다.

</details>
:::
:::tip[🤔 Q2 — stale read 진단 (Bloom: Analyze)]
드라이버가 STATUS의 DONE 비트를 폴링하는데 디바이스는 분명히 DONE을 세웠음에도 루프가 끝나지 않는다. 캐시·배리어 중 무엇이 원인일 가능성이 높고, 그 이유는?
<details>
<summary>정답</summary>

**캐싱** 쪽이 유력합니다. MMIO 영역이 cacheable로 매핑됐다면 첫 read가 캐시 라인을 채운 뒤 이후 read가 캐시의 stale 값(DONE=0)을 계속 반환해 루프가 끝나지 않습니다. 해법은 영역을 uncached로 매핑(`ioremap`)하는 것. 배리어(재정렬)는 *순서* 문제이지 *같은 주소를 반복 read*하는 폴링에서 stale을 만드는 주범이 아닙니다 — 폴링 stale의 전형적 원인은 캐싱입니다.

</details>
:::

### 7.2 출처

**Internal (HDG)**
- `common/hw_sw_interaction_spec.md` §3.4 (Side Effects, Caching, Memory Barriers)

**External**
- Corbet, Rubini, Kroah-Hartman, *Linux Device Drivers 3rd Ed.* Ch. 9 (§I/O Registers and Conventional Memory, p.236; §I/O Ports and I/O Memory, p.237)
- Wikipedia, *Memory-mapped I/O and port-mapped I/O* (CC-BY-SA 4.0) — caching/reordering hazards
- Hennessy & Patterson, *Computer Architecture: A Quantitative Approach* — 메모리 일관성·재정렬 배경

---

## 다음 모듈

→ [03 — 인터럽트 (level/edge/MSI/doorbell/IPI)](../03_interrupts/): 디바이스가 CPU에 *알리는* 방식. side-effect 있는 status/interrupt 레지스터가 어떻게 acknowledge되는지로 자연스럽게 이어진다.

[퀴즈 풀어보기 →](../quiz/02_side_effects_barriers_quiz/)
