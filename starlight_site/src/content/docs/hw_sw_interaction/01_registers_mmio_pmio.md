---
title: "01 — 디바이스 레지스터 & MMIO / PMIO"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** 디바이스 레지스터가 무엇이며, control / status / interrupt / data / pointer 다섯 분류가 각각 어떤 일을 하는지 설명할 수 있다.
- **Differentiate** MMIO(통합 주소 공간)와 PMIO(격리 I/O, `in`/`out`)가 CPU 주소 공간을 다루는 방식을 핸드셰이크·명령어 관점에서 구분할 수 있다.
- **Explain** 메모리 맵에 왜 "구멍(hole)"이 필요한지, 그리고 그 구멍이 RTL의 주소 디코더와 어떻게 대응되는지 설명할 수 있다.
- **Evaluate** 현대 시스템(x86/PCI)에서 MMIO가 PMIO보다 선호되는 이유를 명령어 인코딩·성능 근거로 평가할 수 있다.
:::
:::note[사전 지식]
- CPU의 load/store 명령과 주소 공간 개념
- 레지스터/메모리-맵 IO 기본 (오프셋, access policy) — [UVM RAL](../../uvm/07_register_layer_ral/)
- 버스 트랜잭션 한 개의 구조 (addr/data/read·write) — [AMBA](../../amba_protocols/)
:::
---

## 1. Why care? — 드라이버가 두드리는 첫 번째 접점

### 1.1 시나리오 — "레지스터 맵을 받았는데, 이게 메모리인가 아닌가?"

새 가속기 IP의 드라이버를 처음 작성한다고 합시다. 스펙에는 `CTRL`은 오프셋 `0x00`, `STATUS`는 `0x04`, `DATA_IN`은 `0x08`이라고 적혀 있습니다. 드라이버 개발자는 곧장 묻습니다. "이 주소에 그냥 포인터로 접근하면 되나, 아니면 특별한 명령이 필요한가? CPU 입장에서 이건 메모리인가 I/O인가?"

이 질문의 답이 곧 디바이스의 프로그래밍 모델의 절반입니다. 답이 **MMIO**라면 평범한 load/store로 접근하되 그 영역을 uncached로 매핑해야 하고, **PMIO**라면 x86의 `in`/`out` 같은 전용 명령을 써야 합니다. 검증 엔지니어에게도 똑같이 중요합니다. RTL의 주소 디코더가 이 오프셋들을 받아 올바른 레지스터를 선택하는지, 정의되지 않은 오프셋에 접근하면 어떻게 응답하는지가 전부 이 프로그래밍 모델 위에서 결정됩니다.

> "*Every peripheral device is controlled by writing and reading its registers. Most of the time a device has several registers, and they are accessed at consecutive addresses, either in the memory address space or in the I/O address space.*" — LDD3 §I/O Ports and I/O Memory (p.235)

### 1.2 디바이스 레지스터란 무엇인가

**디바이스 레지스터**는 소프트웨어에게 고정된 버스 주소로 노출된, 하드웨어가 들고 있는 저장 위치입니다. 기능에 따라 다섯 부류로 나뉩니다.

| 분류 | 목적 | 예 |
|------|------|----|
| **Control** | 디바이스 동작을 설정하거나 트리거. write에 side-effect가 있음 | `START`, `ENABLE`, `MODE` |
| **Status** | 디바이스 상태 보고. read가 비트를 클리어하거나(read-to-clear) volatile | `BUSY`, `READY`, `ERROR_CODE` |
| **Interrupt** | 인터럽트 소스 enable/mask/acknowledge | `INT_ENABLE`, `INT_STATUS`, `INT_CLEAR` |
| **Data** | 디바이스 안팎으로 데이터 이동 | `DATA_IN`, `DATA_OUT`, FIFO 포트 |
| **Address / pointer** | 디바이스를 DRAM 위치로 가리킴(DMA 디스크립터, 큐 베이스, 도어벨 타깃) | `DESC_BASE_ADDR`, `QUEUE_HEAD` |

이 분류는 외워야 할 목록이 아니라 **검증의 골격**입니다. control 레지스터는 write side-effect를, status는 read side-effect를, interrupt 레지스터는 acknowledge 핸드셰이크를, pointer 레지스터는 DMA 주소 정합성을 각각 검증해야 한다는 신호이기 때문입니다.

---

## 2. Intuition — 두 가지 우편함, 한 장 그림

:::tip[💡 한 줄 비유]
**MMIO** ≈ **집 안의 같은 복도에 있는 우편함**. RAM이든 디바이스든 모두 같은 주소 복도(unified address space)에 번호를 달고 줄지어 있어, 평범한 load/store(편지 넣기/꺼내기)로 닿습니다.<br>
**PMIO** ≈ **별관에 따로 있는 우편함**. 디바이스 전용 별도 주소 공간에 있어, 그곳에 가려면 `in`/`out`이라는 전용 출입증(특수 명령)이 필요합니다.
:::

### 한 장 그림 — CPU가 두 주소 공간을 보는 방식

```d2
direction: right

CPU: "**CPU**\nload/store\n(공통 명령)" {
  IN: "in/out\n(전용 명령)"
}

MEMSPACE: "**통합 주소 공간 (MMIO)**" {
  RAM: "RAM\n0x0000_0000 ~"
  HOLE: "I/O hole\n디바이스 레지스터 매핑\n(DRAM 불가)" { style.fill: "#f9e79f" }
}

IOSPACE: "**격리 I/O 공간 (PMIO)**\nport 0x00 ~ 0xFFFF" { style.fill: "#aed6f1" }

DEV: "**Device**\n주소 버스 감시\n자기 주소에 응답"

CPU -> RAM: "load/store"
CPU -> HOLE: "load/store (uncached)"
CPU.IN -> IOSPACE: "in/out (EAX, port)"
HOLE -> DEV: "주소 디코드"
IOSPACE -> DEV: "주소 디코드"
```

핵심은 **디바이스가 주소 버스를 감시하다가 자기에게 할당된 주소가 보이면 데이터 버스로 응답한다**는 점입니다. LDD3의 표현대로 레지스터와 일반 메모리는 하드웨어 레벨에서 같은 메커니즘으로 접근됩니다 — "*both of them are accessed by asserting electrical signals on the address bus and control bus ... and by reading from or writing to the data bus*" (LDD3 §I/O Ports and I/O Memory, p.236). 차이는 *주소가 어느 공간에 있느냐*와 *접근에 부작용이 있느냐*(2장 주제)뿐입니다.

---

## 3. 작은 예 — 같은 STATUS 레지스터를 MMIO와 PMIO로 읽기

가장 단순한 시나리오. 디바이스의 `STATUS` 레지스터(BUSY 비트)를 읽는 동일한 동작을, MMIO와 PMIO 두 방식으로 비교합니다.

### 단계별 다이어그램

```d2
direction: down

MMIO: "**MMIO 읽기**" {
  direction: down
  A1: "① ioremap(0xFED0_0004) → ptr"
  A2: "② v = readl(ptr)\n→ 평범한 load 명령"
  A3: "③ 디바이스가 주소 0xFED0_0004 디코드\n→ STATUS 값을 데이터 버스로"
  A1 -> A2 -> A3
}

PMIO: "**PMIO 읽기**" {
  direction: down
  B1: "① port = 0x04 (I/O 공간)"
  B2: "② v = inl(0x04)\n→ 전용 in 명령 (EAX ← port)"
  B3: "③ 디바이스가 I/O 공간 port 0x04 디코드\n→ STATUS 값을 데이터 버스로"
  B1 -> B2 -> B3
}
```

### 단계별 의미

| 단계 | MMIO | PMIO |
|------|------|------|
| 주소 확보 | 물리 MMIO 주소를 가상 주소로 매핑(`ioremap`) | I/O 포트 번호를 그대로 사용 |
| 접근 명령 | 일반 load/store 계열(`readl`/`writel`) | 전용 `in`/`out` 계열(`inl`/`outl`) |
| 사용 가능한 레지스터 | **모든** 범용 레지스터로 주소 지정 가능 | 포트 번호는 immediate 또는 `DX`, 데이터는 `EAX`로 제한 |
| 디코더 | 메모리 주소 디코더가 hole 범위를 디바이스로 라우팅 | 별도 I/O 디코더 / "I/O" 핀 또는 전용 버스 |

### 코드로 보기

```c
/* --- MMIO 방식 (Linux 드라이버 관용구) --- */
void __iomem *regs = ioremap(0xFED00000, 0x1000); /* uncached로 매핑됨 */
u32 status = readl(regs + 0x04);                  /* STATUS = 평범한 load */
if (status & STATUS_BUSY) { /* ... */ }

/* --- PMIO 방식 (x86 전용 명령) --- */
u32 status_p = inl(0x04);                         /* in 명령, EAX ← port 0x04 */
if (status_p & STATUS_BUSY) { /* ... */ }
```

:::note[여기서 잡아야 할 두 가지]
**(1) 동작(상태 비트 읽기)은 같지만 *접근 경로*가 다릅니다.** MMIO는 주소 공간을 RAM과 공유하므로 일반 명령이 그대로 통하고, PMIO는 별도 공간이라 전용 명령이 필요합니다.<br>
**(2) MMIO의 `ioremap`은 그냥 주소 변환이 아니라 그 영역을 *uncached*로 만드는 일까지 합니다.** 왜 반드시 그래야 하는지가 2장의 주제입니다.
:::

---

## 4. 일반화 — MMIO vs PMIO, 그리고 왜 MMIO가 이겼나

### 4.1 두 방식의 정의와 장단점

**MMIO**는 "*uses a unified address space to address both main memory and I/O devices*"입니다 (Wikipedia, MMIO/PMIO). 디바이스 레지스터를 주소 값에 매핑하고, 표준 CPU load/store가 그것을 닿습니다. 그 자리를 비워두기 위해 물리 메모리 맵에는 **구멍(hole)** 이 생깁니다 — 특정 주소 범위가 디바이스용으로 예약되어 DRAM이 그 자리를 채울 수 없습니다.

**PMIO**는 "*uses specialized CPU instructions designed specifically for I/O operations, such as `in` and `out` instructions on x86*"입니다. 이 명령들은 `EAX`와 I/O 포트 주소 사이에서 1·2·4바이트를 옮기며, 디바이스는 별도 주소 공간(*isolated I/O*)에 존재합니다.

| 측면 | MMIO | PMIO |
|------|------|------|
| 주소 공간 | RAM과 통합 | 별도(격리) I/O 공간 |
| 접근 명령 | 일반 load/store | 전용 `in`/`out` |
| CPU 복잡도 | 낮음(별도 I/O 명령셋 불필요 — RISC 친화) | I/O 명령셋·핀/버스 추가 필요 |
| 사용 레지스터 | 모든 addressing mode·GPR 가능, ALU가 레지스터 직접 연산 | `EAX`/immediate·`DX`로 제한 |
| 메모리 경합 | 메모리 버스 공유 | 전용 버스로 경합 회피 가능 |
| 폭(width) | CPU 워드 폭까지 | x86-64에서도 32비트 cap (AMD가 `in`/`out`을 64비트로 확장 안 함) |

### 4.2 왜 MMIO가 지배적인가

현대 x86(IA-32 / x86-64)에서 MMIO가 선호되는 이유는 본질적으로 **명령어 인코딩의 자유도와 속도**입니다. port-I/O 명령은 `EAX`와 immediate/`DX`로 제한되는 반면, *어떤* 범용 레지스터든 MMIO 주소를 지정할 수 있어 명령 수가 줄고 실행이 빠릅니다. AMD는 x86-64에서 `in`/`out`을 64비트로 확장하지 않아 포트 전송은 32비트에 갇혀 있습니다 (Wikipedia, MMIO/PMIO).

PCI 디바이스도 거의 항상 MMIO를 택합니다. LDD3는 이렇게 정리합니다 — "*most PCI devices map registers into a memory address region. This I/O memory approach is generally preferred, because it doesn't require the use of special-purpose processor instructions; CPU cores access memory much more efficiently, and the compiler has much more freedom in register allocation and addressing-mode selection*" (LDD3 §I/O Ports and I/O Memory, p.236).

### 4.3 레지스터 맵을 *어떻게* 작성하는가는 별개의 관심사

레지스터가 *무엇인지*(이 페이지)와, 블록 계층·이름·reset 값·access type를 *어떻게 문서화·생성하는지*는 다른 층위의 문제입니다. 후자는 조직별 컨벤션(레지스터 맵 작성 가이드라인)의 영역이며, 검증 자동화에서는 IP-XACT/스프레드시트에서 RAL 모델을 생성하는 흐름으로 연결됩니다.

---

## 5. 디테일 — hole, BAR, 그리고 DV로의 환산

### 5.1 메모리 hole과 주소 디코더

MMIO가 성립하려면 물리 주소 맵의 일부가 DRAM이 아니라 디바이스로 라우팅되어야 합니다. 이 hole의 위치와 크기를 PCI/PCIe에서는 **BAR(Base Address Register)** 가 정합니다 — 디바이스가 자기 레지스터 영역의 크기를 광고하면, 펌웨어/OS가 충돌하지 않는 물리 주소를 할당해 BAR에 적습니다.

**그런데 "크기를 광고하고 OS가 할당한다"는 _어떻게_ 일어나나 — config space와 enumeration.** PCI/PCIe 디바이스는 BAR 같은 핵심 레지스터를 일반 MMIO와는 _별개_ 인 **configuration space**라는 표준화된 작은 영역에 둡니다. config space의 앞쪽에는 어느 디바이스에나 같은 위치에 놓인 표준 헤더가 있습니다 — vendor ID·device ID(누가 만든 무슨 디바이스인지), class code(종류), 그리고 BAR들입니다. OS는 부팅 시 버스를 훑어(**enumeration**) 각 위치의 vendor ID를 읽어 디바이스 존재를 발견하고, class/device ID로 드라이버를 매칭합니다.

BAR의 _크기 probe_ 메커니즘이 특히 영리합니다. 디바이스는 BAR에 "내 영역은 몇 비트가 주소에 쓰이는가"를 _하위 비트를 0으로 고정(read-only)_ 하는 방식으로 인코딩해 둡니다. OS는 (1) BAR에 **all-1(0xFFFFFFFF)** 을 쓰고, (2) 다시 읽습니다. 디바이스는 _자기 크기에 해당하는 하위 비트들_ 을 0으로 강제해 돌려주므로, OS는 "돌아온 값에서 가장 낮은 1비트의 위치"로 영역 크기를 역산합니다(예: 하위 12비트가 0이면 4KB). 그 크기만큼 빈 물리 주소를 찾아 _진짜_ base를 BAR에 다시 씁니다. 이것이 §1의 "크기 광고 → OS가 할당"의 실제 절차입니다 — 디바이스는 _크기만_ 정하고 _위치는_ OS가 정하는 협상입니다. (검증에서는 이 probe write-all-1 → read-back → base write 시퀀스가 올바른 mask/크기를 내는지가 BAR 검증의 핵심입니다.)

RTL 관점에서 이 hole은 곧 **주소 디코더**입니다. 디코더는 들어온 주소가 자기 영역에 속하는지 비교하고, 속하면 어느 레지스터인지 선택합니다. 검증에서 확인할 것은 (1) 할당된 범위 안의 각 오프셋이 올바른 레지스터를 선택하는가, (2) 범위 밖/미정의 오프셋 접근이 정의된 방식으로 응답하는가(에러 응답 또는 0 read)입니다.

**디코더의 우선순위와 overlap 처리.** 실제 시스템에는 디코드 영역이 여럿입니다 — 여러 BAR, 레거시 영역, reserved 영역이 한 주소 버스를 공유합니다. 두 영역의 범위가 _겹치면_ 어느 쪽이 응답할지 모호해지므로, 디코더는 _우선순위_ 를 명시해야 합니다. 보통 (a) 더 구체적인(좁은) 영역이 넓은 영역보다 우선하거나, (b) 고정된 영역 인덱스 순서로 첫 매치가 이기도록 설계합니다. 검증의 핵심은 두 가지입니다: (1) **overlap 자체가 _발생하지 않도록_** BAR 할당이 보장되는가(enumeration이 충돌 없는 base를 주는가), (2) 그럼에도 입력 주소가 _두 영역의 경계_ 나 _겹침_ 에 떨어졌을 때 디코더가 _정확히 하나_ 의 타깃만 선택하고 둘이 동시에 응답(버스 충돌)하거나 둘 다 침묵(hang)하지 않는가. 경계 주소(영역의 첫·마지막 오프셋, 그 ±1)는 디코더 비교 로직의 off-by-one 버그가 잘 나는 곳이라 directed로 반드시 짚습니다.

### 5.2 posted write vs non-posted read — write 후 동작 보장의 함정

MMIO 접근 경로(§3의 load/store)에는 _완료 시점_ 이라는 보이지 않는 차원이 있습니다. PCIe에서 **memory write는 _posted_** 입니다 — 요청자(CPU)가 write를 버스에 내보내면 _완료를 기다리지 않고_ 즉시 다음 일을 합니다. 데이터가 실제로 디바이스에 도착했다는 확인(completion)이 돌아오지 않습니다. 반대로 **memory read는 _non-posted_** 입니다 — read는 반드시 데이터를 담은 completion이 돌아와야 끝나므로, read를 한 시점에는 _그 이전의 모든 것이 디바이스에 도달_ 했음이 보장됩니다.

이 비대칭이 드라이버에 실질적 함정을 만듭니다. "디바이스에 START를 write했으니 이제 디바이스가 동작을 시작했겠지"는 _보장되지 않습니다_ — posted write는 아직 PCIe 패브릭 어딘가에 머물러 있을 수 있습니다. write가 _실제로 디바이스에 닿았음_ 을 보장하려면, 같은 디바이스의 아무 레지스터나 **read-back** 해야 합니다. read는 non-posted라 completion을 기다리고, 그 completion이 돌아왔다는 것은 _앞선 posted write도 이미 디바이스를 통과_ 했다는 뜻이기 때문입니다(같은 경로의 순서 보장). 그래서 드라이버 관용구 "write 후 더미 read-back"은 미신이 아니라 posted/non-posted 의미에서 나온 _순서 강제_ 수단입니다.

이것은 [2장의 메모리 배리어](../02_side_effects_barriers/)와 직결됩니다 — 배리어가 _CPU 내부_ 의 재정렬을 막는다면, read-back은 _버스 패브릭_ 위에서 posted write의 도달을 강제합니다. 둘은 "write의 효과가 _언제_ 보장되는가"라는 같은 문제의 서로 다른 계층입니다.

### 5.3 DV 관점 — 이 장의 내용을 어떻게 검증하나

| 검증 대상 | 무엇을 확인 | 어떻게 |
|-----------|-------------|--------|
| 주소 디코드 | 각 오프셋 → 올바른 레지스터 선택 | RAL `uvm_reg_bit_bash_seq`로 모든 레지스터 RW 토글 |
| 미정의 오프셋 | hole 밖/reserved 접근 시 정의된 응답 | directed write/read + 응답 코드 체크 |
| reset 값 | 전 레지스터 reset 값 일치 | RAL `uvm_reg_hw_reset_seq` |
| access policy | RO에 write 무시, RW 정상 등 | RAL `uvm_reg_access_seq`(frontdoor/backdoor 일치) |

레지스터 검증의 실무 도구(RAL 모델, adapter, 내장 시퀀스)는 [UVM Module 07 — Register Layer](../../uvm/07_register_layer_ral/)에서 본격적으로 다룹니다. 이 장은 그 *대상*이 무엇이고 왜 그렇게 생겼는지를 제공합니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '레지스터는 그냥 메모리니까 포인터로 읽으면 끝이다']
**실제**: 레지스터는 메모리처럼 *보이지만* I/O 동작에는 side-effect가 있고(read가 비트를 클리어, write가 동작을 트리거), 그래서 컴파일러 최적화·캐싱이 의미를 깨뜨립니다. MMIO 영역은 반드시 uncached로 매핑하고 배리어로 순서를 보장해야 합니다 — 2장의 주제.<br>
**왜 헷갈리는가**: 주소로 접근한다는 점이 RAM과 똑같아 보여서.
:::
:::danger[❓ 오해 2 — 'PMIO가 별도 공간이니까 더 빠르고 좋다']
**실제**: 격리된 버스로 메모리 경합을 피하는 장점은 있으나, 현대 x86에서는 명령·레지스터 제약(`EAX`/`DX`, 32비트 cap)으로 MMIO보다 느리고 불편합니다. 그래서 대부분의 PCI 디바이스가 MMIO를 택합니다.<br>
**왜 헷갈리는가**: "전용"이 곧 "고성능"이라는 인상 때문에.
:::
:::danger[❓ 오해 3 — 'MMIO면 메모리 맵에 그냥 끼워 넣으면 된다']
**실제**: 디바이스 영역만큼 물리 메모리 맵에 *구멍*이 생기고 그 자리는 DRAM이 차지할 수 없습니다. 주소 디코더가 그 범위를 디바이스로 라우팅해야 하며, 범위 충돌은 곧 접근 실패입니다.<br>
**왜 헷갈리는가**: "통합 주소 공간"을 "공짜로 합쳐진다"로 오해해서.
:::

### DV 디버그 체크리스트 (이 장 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|------|----------|-----------|
| 특정 오프셋 read/write가 엉뚱한 레지스터에 작용 | 주소 디코더의 오프셋 매핑 오류 | 디코더 비교 로직, RAL map의 오프셋 값 |
| 모든 레지스터 접근이 어긋남(한 칸씩 밀림) | 주소 스케일(byte vs word) 또는 BAR base 불일치 | adapter `addr` 스케일, `create_map` byte-width |
| reset 직후 read 값이 스펙과 다름 | reset 값 오설정 또는 read side-effect | RAL hw_reset_seq, field reset 인자 |
| 미정의 오프셋 접근 시 hang | 디코더가 default 응답을 안 냄 | 디코더의 else 경로, 버스 응답 코드 |
| RO 레지스터에 write가 먹힘 | access policy(RO) 미구현 | field configure access, access_seq |

---

## 7. 핵심 정리 (Key Takeaways)

- **디바이스 레지스터 = 고정 버스 주소에 노출된 하드웨어 저장 위치**. control / status / interrupt / data / pointer 다섯 분류는 곧 검증 골격이다.
- **MMIO = RAM과 통합된 주소 공간 + 일반 load/store**, **PMIO = 별도 I/O 공간 + 전용 `in`/`out`**. 동작은 같아도 접근 경로가 다르다.
- **메모리 hole**: MMIO 영역만큼 물리 맵에 구멍이 생기고, 주소 디코더가 그 범위를 디바이스로 라우팅한다.
- **MMIO가 지배적**인 이유는 명령 인코딩의 자유도·속도(모든 GPR로 주소 지정, ALU 직접 연산)와 PMIO의 제약(`EAX`/`DX`, 32비트 cap). 대부분 PCI 디바이스가 MMIO.
- **레지스터가 *무엇인지*와 *어떻게 문서화/생성하는지*는 별개 관심사** — 후자는 조직 컨벤션 + IP-XACT/RAL 자동화.

:::caution[실무 주의점]
- MMIO 영역은 *반드시* uncached로 매핑 — `ioremap` 계열이 이를 강제(2장 상세).
- PCI는 거의 MMIO. 레거시 호환을 위한 I/O 포트가 있어도 레지스터 본체는 MMIO에 둔다.
- 미정의 오프셋의 응답 정책(에러 vs 0)은 *스펙으로 정해* 검증한다 — "안 쓰니까 상관없다"가 escape를 만든다.
:::

### 7.1 자가 점검

:::tip[🤔 Q1 — MMIO uncached (Bloom: Analyze)]
어떤 드라이버가 MMIO 영역을 평범한 캐시 가능(cacheable) 메모리로 매핑했다. STATUS 레지스터를 폴링하는 루프가 영원히 BUSY로 보인다. 왜인가?
<details>
<summary>정답</summary>

캐시가 걸린 영역에서 첫 read가 캐시 라인을 채우면, 이후 read는 디바이스가 아니라 *캐시*에서 stale 값을 가져옵니다. 디바이스가 BUSY→READY로 바꿔도 CPU는 캐시에 든 옛 BUSY 값을 계속 읽어 루프가 끝나지 않습니다. 해법은 영역을 uncached로 매핑(`ioremap`)하는 것입니다. 이것이 레지스터를 일반 메모리처럼 다루면 안 되는 핵심 이유이고, 2장 side-effect/배리어의 출발점입니다.

</details>
:::
:::tip[🤔 Q2 — MMIO vs PMIO 선택 (Bloom: Evaluate)]
새 PCIe 가속기를 설계하며 레지스터를 MMIO로 노출할지 PMIO로 할지 고민 중이다. 어느 쪽이 합리적이고 그 근거는?
<details>
<summary>정답</summary>

**MMIO**가 합리적입니다. 순수 PCIe 링크에는 I/O 포트 공간 개념이 사실상 없고(PCIe는 메모리/메시지 기반), 대부분의 PCI/PCIe 디바이스가 레지스터를 MMIO로 매핑합니다. 근거: (1) 전용 I/O 명령 불필요 → CPU가 메모리를 훨씬 효율적으로 접근, (2) 컴파일러의 레지스터 할당·addressing mode 자유도, (3) PMIO는 `EAX`/`DX` 제약과 32비트 cap. PMIO의 격리 버스 장점은 현대 시스템에서 이 단점들을 상쇄하지 못합니다.

</details>
:::

### 7.2 출처

**External**
- Wikipedia, *Memory-mapped I/O and port-mapped I/O* (CC-BY-SA 4.0)
- Corbet, Rubini, Kroah-Hartman, *Linux Device Drivers 3rd Ed.* Ch. 9 (§I/O Ports and I/O Memory, p.235–237)
- Patterson & Hennessy, *Computer Organization and Design: The HW/SW Interface* (프로그래밍 모델 일반)

---

## 다음 모듈

→ [02 — Side-effect & 메모리 배리어](../02_side_effects_barriers/): 레지스터가 RAM과 *어떻게 다른지*, 그리고 캐싱·재정렬이 I/O를 깨뜨리는 이유와 그 방어(uncached 매핑 + barrier).

[퀴즈 풀어보기 →](../quiz/01_registers_mmio_pmio_quiz/)
