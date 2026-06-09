---
title: "Unit 3 — Embedded Systems / Firmware"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Design** thermostat / battery charger 같은 작은 임베디드 시스템의 sensor → MCU → actuator 데이터 플로우를 설계한다.
- **Compare** I2C / SPI / UART / CAN 의 핀 수, 속도, multi-master 지원, 노이즈 면역성을 비교한다.
- **Implement** circular buffer, linked list, bit manipulation 등 임베디드 빈출 자료구조 / 비트연산을 C 로 작성한다.
- **Distinguish** process / thread / context switch / mutex / semaphore / atomic 의 차이를 설명한다.
- **Apply** `volatile`, linker script, `memcpy` vs `memmove`, custom `malloc` 같은 메모리 관련 코드를 정확히 작성한다.
- **Explain** 캐시 hit/miss, locality, replacement policy, write-through vs write-back, MESI 의 임베디드 영향을 설명한다.
:::
:::note[사전 지식]
- C 언어 (포인터, struct, 함수 포인터)
- 컴퓨터 구조 기본 (CPU, 메모리, 캐시)
- 운영체제 기본 (process, scheduling)
:::
---

## 1. 시스템 설계 — 인터뷰 빈출 시나리오

이 모듈의 무대는 **MCU**(Microcontroller Unit, CPU·메모리·주변장치를 한 칩에 담은 소형 제어용 프로세서)가 **sensor**(센서, 물리량을 전기 신호로 읽는 입력 소자)에서 값을 읽어 **actuator**(액추에이터, 모터·릴레이처럼 실제 물리 동작을 일으키는 출력 소자)를 제어하는 임베디드 시스템입니다. 펌웨어는 이 칩 위에서 도는 저수준 소프트웨어를 말합니다.

### 1.1 Thermostat 설계

**요구**: 실내 온도를 ±0.5°C 로 유지.

```d2
direction: down
Temp sensor -> MCU: I2C
MCU -> Heater relay: PWM
MCU -> Display: UART
MCU -> Button input: "GPIO + IRQ"
```

위 그림의 연결 수단을 한 줄로 풀면: **I2C**(2선 저속 직렬 버스), **PWM**(Pulse-Width Modulation, 펄스의 켜진 시간 비율로 평균 출력 세기를 조절 — 릴레이/모터 제어에 사용), **UART**(시작/정지 비트로 보내는 직렬 통신), **GPIO**(General-Purpose I/O, 소프트웨어로 0/1을 읽고 쓰는 범용 디지털 핀), **IRQ**(Interrupt Request, 이벤트가 생기면 CPU의 현재 실행을 멈추고 처리 루틴으로 점프하게 하는 인터럽트 요청)입니다.

**설계 포인트** (인터뷰 답변 시 다루어야 할 것):

1. **Sample rate** — 너무 빠르면 power 낭비, 너무 느리면 oscillation. 1~5초 주기.
2. **Filter** — sensor noise 제거. Moving average 또는 IIR low-pass(저주파만 통과시켜 잡음을 깎는 필터).
3. **Hysteresis** — (히스테리시스, 켤 때와 끌 때의 기준값을 일부러 다르게 둬 잦은 토글을 막는 것) heater on / off threshold 차이 (예: 22°C 에서 on, 22.5°C 에서 off). *Bang-bang*(켜짐/꺼짐 둘 뿐인 단순 제어) 제어의 chattering(기준 근처에서 빠르게 깜빡이는 현상) 방지.
4. **PID 또는 PWM duty cycle** — 비례 제어 시 PID(Proportional-Integral-Derivative, 오차의 현재·누적·변화율을 합쳐 부드럽게 목표에 맞추는 제어), 단순 on/off 면 hysteresis. duty cycle은 PWM에서 켜진 시간의 비율.
5. **Watchdog** — (워치독, 일정 시간 안에 펌웨어가 "살아있다" 신호를 안 주면 자동으로 리셋하는 감시 타이머) sensor stuck 또는 firmware hang 감지.
6. **Failsafe** — 통신 끊기면 heater OFF (open-circuit safe).

### 1.2 RTOS vs Bare-metal

임베디드 시스템을 설계할 때 가장 먼저 결정해야 하는 구조적 선택이 RTOS(Real-Time Operating System, 실시간 운영체제 — task 스케줄링과 예측 가능한 응답 시간을 제공하는 소형 OS) 사용 여부, 즉 RTOS냐 bare-metal(베어메탈, OS 없이 `main()`의 무한 루프와 인터럽트만으로 도는 방식)이냐입니다. 단일 제어 루프만 필요하고 코드가 수 KB 수준이라면 bare-metal 이 단순하고 예측 가능합니다. 하지만 센서 읽기, 통신 처리, UI 갱신을 *동시에* 처리해야 하는 복잡한 시스템에서는 bare-metal 의 `while(1)` 루프가 점점 분기로 얽히고, 우선순위가 다른 작업들을 직접 관리해야 하는 부담이 생깁니다. 이때 RTOS 의 스케줄러와 task 추상화가 큰 역할을 합니다.

| 항목 | Bare-metal | RTOS (FreeRTOS, Zephyr) |
|------|------------|-------------------------|
| 구조 | `main()` 안에 while(1) + ISR | Task + Scheduler |
| 우선순위 | 인터럽트만 가짐 | Task priority + preemption |
| 동기화 | volatile + IRQ disable | Mutex, semaphore, queue |
| 메모리 | Static / linker 영역 | + heap (RTOS 가 관리) |
| 디버그 | 단순 | Task stack 추적 필요 |
| 사용 시기 | < 5 KB code, 단일 control loop | 다중 동시 작업, 통신 + 제어 |

표의 용어: **ISR**(Interrupt Service Routine, 인터럽트가 발생했을 때 실행되는 처리 함수), **Task**(RTOS에서 독립적으로 스케줄되는 실행 단위), **Scheduler**(어떤 task를 언제 CPU에 올릴지 정하는 RTOS 핵심), **preemption**(선점 — 더 높은 우선순위 task가 실행 중인 낮은 task를 중간에 밀어내고 CPU를 차지), **heap**(실행 중 동적으로 메모리를 빌리는 영역)이 핵심입니다.

---

## 2. Protocols & Interconnects — 임베디드 관점

| Protocol | 핀 수 | 속도 | Multi-master | 노이즈 | 거리 |
|----------|-------|------|--------------|--------|------|
| **I2C** | 2 (SDA, SCL) | 100K ~ 3.4M bps | ✅ (arbitration) | 약함 (open-drain) | < 1m |
| **SPI** | 4+ (SCLK, MOSI, MISO, CS) | 수십 MHz | ❌ (single master) | 강함 (push-pull) | < 30cm |
| **UART** | 2 (TX, RX) | ~ 3 Mbps | ❌ | 중간 | 거리 한계 짧음 |
| **CAN** | 2 (CAN_H, CAN_L) | 1 Mbps (CAN-FD: 8 Mbps) | ✅ (priority arbitration) | **매우 강함** (differential) | 자동차 전체 |
| **RS-485** | 2 (differential) | ~ 10 Mbps | half-duplex multi-drop | 강함 | 1200m |

표에서 처음 나오는 용어: **SPI**(4선 고속 직렬 버스), **CAN**(Controller Area Network, 차량용 다중 노드 버스 — 노이즈에 강함), **RS-485**(긴 거리 다중 드롭용 차동 직렬 규격), **multi-master**(버스를 주도할 수 있는 주체가 둘 이상), **differential**(differential signaling, 두 선의 전압 차로 1비트를 전하는 방식 — 공통 잡음이 상쇄돼 노이즈에 강함), **half-duplex**(한 번에 한 방향씩만 송수신)입니다.

### 2.1 I2C — 가장 자주 묻는 디테일

- **Open-drain** — (출력이 LOW로 끌어내리거나 아예 놓아버리는(하이임피던스) 두 상태뿐이라, 여러 장치가 한 선을 공유해도 충돌 없이 LOW가 우선되는 구조) 외부 pull-up 필수. 두 master 가 동시에 SDA 잡으면 *둘 다 LOW 가 우선* → arbitration 가능.
- **START / STOP** — `SDA falling while SCL high` = START, `SDA rising while SCL high` = STOP.
- **ACK / NACK** — 9 번째 클럭에 receiver 가 SDA 를 LOW 로 → ACK.
- **Clock stretching** — slave 가 SCL 을 LOW 로 잡아 master 에 backpressure(받는 쪽이 아직 못 받으니 보내는 쪽을 멈추게 하는 역압).

### 2.2 SPI 의 Mode 4가지

SPI는 클럭 극성과 위상 두 설정의 조합으로 4가지 mode를 가집니다. **CPOL**(Clock Polarity, 클럭이 쉴 때 HIGH인가 LOW인가), **CPHA**(Clock Phase, 데이터를 첫 엣지에서 샘플하는가 두 번째 엣지에서 샘플하는가)입니다.

| Mode | CPOL | CPHA | Description |
|------|------|------|-------------|
| 0 | 0 | 0 | Clock idle low, sample on rising |
| 1 | 0 | 1 | Clock idle low, sample on falling |
| 2 | 1 | 0 | Clock idle high, sample on falling |
| 3 | 1 | 1 | Clock idle high, sample on rising |

**Master / Slave 가 같은 mode 가 아니면 항상 데이터 오류** — datasheet 첫 확인 사항.

### 2.3 CAN — 자동차에서 왜 쓰는가

- **Differential signaling** — 노이즈 면역 (전기적 충격이 양 wire 에 동일 영향 → 차분 제거).
- **Priority arbitration** — ID 가 작을수록 우선. 충돌 시 dominant(0) 가 recessive(1) 를 덮어 자연스럽게 winner 결정.
- **Broadcast** — 모든 노드가 모든 메시지를 받음. 노드 추가/제거가 토폴로지 변경 없음.

---

## 3. 임베디드 C — 자주 묻는 코딩

### 3.1 Bit Manipulation 1줄 정리

```c
// Set bit n
x |= (1U << n);

// Clear bit n
x &= ~(1U << n);

// Toggle bit n
x ^= (1U << n);

// Test bit n
if (x & (1U << n)) { ... }

// Count bits set (Brian Kernighan)
int count = 0;
while (x) { count++; x &= (x - 1); }

// Reverse bits in a byte
uint8_t rev(uint8_t b) {
    b = (b & 0xF0) >> 4 | (b & 0x0F) << 4;
    b = (b & 0xCC) >> 2 | (b & 0x33) << 2;
    b = (b & 0xAA) >> 1 | (b & 0x55) << 1;
    return b;
}
```

### 3.2 Circular Buffer

**Circular buffer**(원형 버퍼 — 고정 크기 배열의 끝과 처음을 이어 붙여 read/write 위치만 돌려쓰는 FIFO 큐; ring buffer라고도 함)는 스트리밍 데이터 임시 저장의 단골입니다.

```c
typedef struct {
    uint8_t *buf;
    size_t   size;
    size_t   head;   // write index
    size_t   tail;   // read index
    bool     full;
} cbuf_t;

bool cbuf_put(cbuf_t *c, uint8_t v) {
    if (c->full) return false;
    c->buf[c->head] = v;
    c->head = (c->head + 1) % c->size;
    c->full = (c->head == c->tail);
    return true;
}

bool cbuf_get(cbuf_t *c, uint8_t *out) {
    if (!c->full && c->head == c->tail) return false;
    *out = c->buf[c->tail];
    c->tail = (c->tail + 1) % c->size;
    c->full = false;
    return true;
}
```

**디테일**: `head == tail` 이 *empty* 인지 *full* 인지 모호 → `full` 플래그 따로. 또는 capacity 를 size-1 로 한정.

### 3.3 Endianness

```c
// Big-endian (MSB first): 0x12345678 → [0x12, 0x34, 0x56, 0x78]
// Little-endian (LSB first): 0x12345678 → [0x78, 0x56, 0x34, 0x12]

bool is_little_endian(void) {
    uint16_t x = 1;
    return *(uint8_t*)&x == 1;
}

// Byte swap
uint32_t bswap32(uint32_t x) {
    return ((x & 0xFF000000) >> 24) |
           ((x & 0x00FF0000) >>  8) |
           ((x & 0x0000FF00) <<  8) |
           ((x & 0x000000FF) << 24);
}
```

**네트워크는 항상 big-endian** (network byte order). `htonl()` / `ntohl()` 사용.

---

## 4. Concurrency & Synchronization

### 4.1 Process vs Thread

**Process**(프로세스 — 독립된 메모리 공간을 가진 실행 단위)와 **Thread**(스레드 — 한 프로세스 안에서 메모리를 공유하며 도는 더 가벼운 실행 단위)의 차이입니다. **Context switch**(문맥 전환 — CPU가 실행 중인 작업을 멈추고 다른 작업으로 갈아탈 때 레지스터 등 상태를 저장·복원하는 동작)의 비용이 둘을 가릅니다.

| 항목 | Process | Thread |
|------|---------|--------|
| Address space | 독립 | 공유 |
| Context switch cost | 비쌈 (TLB(Translation Lookaside Buffer, 가상→물리 주소 변환을 캐싱한 버퍼) flush) | 쌈 (PC + registers 만) |
| 통신 | IPC (Inter-Process Communication; pipe, socket, shared mem) | 공유 변수 + mutex |
| Crash isolation | 강함 | 약함 (한 thread crash → 모두 죽음) |

### 4.2 Mutex vs Semaphore

Mutex 와 semaphore 는 둘 다 "접근 제어"를 하지만 *목적과 소유 개념*에서 근본적으로 다릅니다. **Mutex** 는 lock 을 건 태스크만 unlock 할 수 있는 *소유 개념*을 가지며, 0/1 이진 값으로 하나의 critical section 을 보호하는 데 씁니다. 반면 **Counting Semaphore** 는 소유 개념이 없고 N 카운트를 가지기 때문에 여러 슬롯짜리 resource pool 을 관리하거나 producer-consumer 카운팅에 적합합니다. **Binary semaphore** 는 카운트가 0/1 인 semaphore 의 특수 형태로, 소유가 없으므로 ISR 에서 signal 을 보내고 task 가 wait 하는 패턴에 자주 씁니다. Mutex 를 ISR 에서 사용하면 안 되는 이유가 바로 여기에 있습니다.

### 4.3 Atomic Operations

```c
// GCC built-in
__atomic_fetch_add(&counter, 1, __ATOMIC_SEQ_CST);
__atomic_compare_exchange_n(&x, &expected, new, false, __ATOMIC_SEQ_CST, __ATOMIC_RELAXED);

// C11
atomic_int counter = 0;
atomic_fetch_add(&counter, 1);
```

**왜 atomic?** **atomic operation**(원자적 연산 — 중간에 끼어들 수 없어 "전부 일어나거나 전혀 안 일어난" 것으로 보이는 연산)이 핵심입니다. `counter++` 는 `load - add - store` 3개 명령. Multi-core / preempt 환경에서 race(둘 이상이 같은 데이터를 동시에 건드려 결과가 순서에 좌우되는 경합). **CAS**(compare-and-swap, 기대값과 일치할 때만 새 값으로 바꾸는 원자적 명령) 가 lock-free(잠금 없이도 누군가는 항상 진행하는) 자료구조의 기반.

**CAS 가 _왜_ lock 없이 진행을 보장하나 — "기대값 일치 시에만 교체 + 실패 시 재시도".** CAS 의 동작은 한 번의 atomic 명령으로 "메모리 위치의 현재 값이 _내가 기대한 값(expected)과 같으면_ 새 값으로 바꾸고 성공을 반환, _다르면_ 아무것도 안 하고 실패를 반환" 이다. lock-free 갱신의 전형적 패턴은 이렇다: (1) 현재 값을 읽어 `expected` 로 둔다, (2) 그 값을 바탕으로 새 값을 계산한다, (3) `CAS(&x, expected, new)` 를 시도한다. 만약 그 사이 다른 스레드가 `x` 를 바꿔치웠다면 현재 값이 `expected` 와 달라 CAS 가 _실패_ 하고, 그러면 (1)부터 다시 읽어 _재시도(retry loop)_ 한다. 성공한 스레드만 갱신을 반영하므로 _덮어쓰기로 인한 손실_ 이 원천 차단된다.

이것이 lock 과 결정적으로 다른 점은, CAS 가 실패해도 _블로킹하지 않는다_ 는 것이다. lock 은 보유 스레드가 선점/지연되면 대기자들이 _전부 멈추지만_, CAS 기반에서는 한 스레드의 CAS 가 실패한다는 것은 _다른 스레드가 이미 성공해 시스템이 전진했다_ 는 뜻이다 — 즉 누군가는 항상 진행한다(lock-free 의 progress 보장). 그래서 ISR 처럼 blocking 이 금지된 문맥(§위 4.x)에서 mutex 대신 CAS 기반 lock-free queue 를 쓰는 것이다.

### 4.4 Context Switch — 무엇이 저장되나?

1. **CPU register file** (general purpose, SP(stack pointer, 스택 꼭대기 주소), LR(link register, 함수 복귀 주소), PC(program counter, 다음 실행할 명령 주소))
2. **PSR / CPSR** — (Program/Current Program Status Register, 연산 결과 플래그·현재 모드를 담는 상태 레지스터) flags, mode
3. **FPU register** — FPU(Floating-Point Unit, 소수 연산 전용 회로)를 쓰는 task 라면
4. **(VM(Virtual Memory, 가상 메모리) 사용 시) Page table base register**(가상→물리 변환표의 시작 주소), TLB flush 필요할 수 있음

---

## 5. 메모리 / 드라이버

### 5.1 `volatile` — 컴파일러에게 *최적화 금지*

`volatile`(C/C++ 한정자 — 그 변수는 코드 밖(하드웨어·다른 스레드)에서 언제든 바뀔 수 있으니 컴파일러가 레지스터 캐싱 같은 최적화를 하지 말고 매번 메모리를 읽으라는 지시)은 **memory-mapped I/O**(하드웨어 레지스터를 일반 메모리 주소처럼 읽고 써서 장치를 제어하는 방식)에 필수입니다.

```c
// 하드웨어 레지스터
#define UART_STATUS (*(volatile uint32_t *)0x4000_0008)

while (!(UART_STATUS & TX_READY))  // 매번 메모리 읽기 강제
    ;
```

**volatile 가 필요한 경우** 3가지:
1. 하드웨어 레지스터 (memory-mapped I/O)
2. ISR 와 main 이 공유하는 변수
3. setjmp/longjmp 사용 시 stack 변수

### 5.2 Linker Script — 메모리 영역

**Linker script**(링커 스크립트 — 코드와 데이터를 ROM/RAM의 어느 주소 영역에 배치할지 지정하는 빌드 설정)는 임베디드에서 메모리 맵을 직접 정합니다. 아래 `.text`/`.data`/`.bss` 등을 **section**(섹션, 성격이 같은 코드/데이터를 묶은 단위)이라 부릅니다.

```
.text   : ROM/Flash, 실행 코드
.rodata : ROM, const 데이터
.data   : RAM (Flash 에서 초기값 copy)
.bss    : RAM, 0 으로 초기화
.heap   : RAM, malloc 영역
.stack  : RAM, 스택 (보통 RAM 끝에서 아래로 자람)
```

**Startup code** 가 `.data` 의 초기값을 Flash → RAM 으로 복사, `.bss` 를 0 으로 클리어한 *후에* `main()` 호출.

### 5.3 `memcpy` vs `memmove`

```c
memcpy(dst, src, n);   // 영역이 겹치면 UB (Undefined Behavior)
memmove(dst, src, n);  // 겹쳐도 안전
```

**구현 차이**: `memmove` 는 `dst < src` 이면 앞에서, `dst > src` 이면 뒤에서 복사 → 자기 자신 덮어쓰기 방지.

### 5.4 `malloc` — 임베디드에서 안전한가?

**보통 *피함*** — 이유:
임베디드에서 `malloc` 을 피하는 핵심 이유는 *예측 불가능성*입니다. 반복적인 할당·해제가 누적되면 heap 이 fragmentation 되어 충분한 총량의 메모리가 있어도 큰 chunk 를 요청했을 때 실패할 수 있습니다. 또한 할당 latency 가 호출마다 달라지기 때문에 timing 이 중요한 제어 루프에서 사용하기 어렵고, out-of-memory 발생 시 임베디드 환경에서는 복구 절차가 마땅치 않습니다.

- Fragmentation → 시간이 갈수록 큰 chunk 못 받음
- 결정적이지 않은 latency
- Out-of-memory 시 복구 어려움

**대안**:
이런 이유로 임베디드에서는 메모리를 컴파일 타임에 모두 결정하는 *static 할당*을 우선으로 고려합니다. 동적 크기가 필요하다면 *memory pool* — 동일 크기의 chunk 를 N 개 미리 확보해 두는 방식 — 로 fragmentation 을 원천 차단합니다. 크기가 다양하게 필요하면 *buddy allocator* 처럼 2의 제곱 단위 chunk 로 관리해 fragmentation 을 줄이는 대안을 씁니다.

- *Static 할당* — 컴파일 타임에 모든 메모리 결정
- *Memory pool* — 같은 크기 chunk 를 미리 N 개 할당 → fragmentation 없음
- *Buddy allocator* — 2의 제곱 크기 chunk, fragmentation 적음

---

## 6. Cache & Coherency — 펌웨어 관점

**Cache**(캐시 — 자주 쓰는 데이터를 CPU 가까이 두는 작고 빠른 메모리; 느린 RAM 접근을 줄임)에서 찾던 데이터가 있으면 **hit**, 없어서 RAM까지 가야 하면 **miss**입니다. 데이터는 **cache line**(캐시 라인 — 캐시가 RAM에서 한 번에 가져오는 연속 바이트 묶음) 단위로 오갑니다. **Coherency**(일관성 — 여러 코어의 캐시 사본이 같은 주소에 대해 일관된 값을 유지하는 성질)가 멀티코어의 핵심 문제입니다.

### 6.1 Locality

**Locality**(지역성 — 프로그램이 메모리를 무작위가 아니라 특정 패턴으로 접근하는 경향; 캐시가 효과를 보는 근거)가 캐시가 효과를 발휘하는 이유는 프로그램의 접근 패턴이 *locality* 를 갖기 때문입니다. **Temporal locality** 는 방금 접근한 데이터를 곧 다시 접근하는 성질로, loop counter 나 함수 호출 프레임이 대표적입니다. **Spatial locality** 는 인접한 주소를 연달아 접근하는 성질로, 배열 순차 순회가 여기에 해당합니다. 캐시 라인이 한 번 로드될 때 인접 데이터까지 함께 올라오는 이유가 바로 spatial locality 를 활용하기 위해서입니다.

- **Temporal** — 최근 접근 데이터를 곧 다시 접근 (loop counter, function call frame)
- **Spatial** — 인접 주소를 곧 접근 (array iteration)

**임베디드 영향**: `struct of arrays` vs `array of structs`. 한 필드만 자주 쓰면 SoA 가 cache hit 율 높음.

### 6.2 Write-through vs Write-back

| Policy | Write 시 | 장점 | 단점 |
|--------|----------|------|------|
| Write-through | RAM + cache 동시 갱신 | 항상 RAM 이 최신 → coherency 단순 | RAM bandwidth 많이 씀 |
| Write-back | Cache 만 갱신, dirty 비트 set | Bandwidth 절약 | Coherency 복잡, eviction 시 RAM write |

표의 용어: **dirty 비트**(캐시 내용이 RAM보다 새것임을 표시 — 나중에 RAM에 다시 써야 함), **eviction**(자리가 모자라 캐시 라인을 내보내는 것), **DMA**(Direct Memory Access, CPU를 거치지 않고 장치가 메모리에 직접 읽고 쓰는 전송 — 빠르지만 캐시와 어긋날 수 있음)입니다.

**DMA 충돌 흔한 시나리오**: Write-back 캐시 + DMA 가 같은 영역 접근 → cache flush (CPU → RAM) 후 DMA start, 또는 cache invalidate (DMA → CPU 데이터) 후 CPU read.

### 6.3 MESI 의 직관

**MESI**(Modified/Exclusive/Shared/Invalid 네 상태로 각 캐시 라인을 관리해 멀티코어 캐시 일관성을 유지하는 대표 프로토콜) — 각 cache line 은 4 상태:
- **M** (Modified) — dirty, 나만 가짐
- **E** (Exclusive) — clean, 나만 가짐
- **S** (Shared) — clean, 여러 코어 가짐
- **I** (Invalid) — 없음

다른 코어 write 시 *내 S 또는 E* → *I* 로 invalidate.

---

## 7. 샘플 인터뷰 Q&A

<details>
<summary>Q1. (Apply) `volatile int x; while (x);` 가 무한 루프지만 다른 곳에서 x = 0 되기를 기다리는 코드인데, `volatile` 없으면?</summary>

컴파일러가 `x` 를 *레지스터에 로드 한 번* 하고 더 이상 읽지 않을 수 있다 → 다른 곳에서 x 가 0 이 되어도 *영원히* 루프. `volatile` 이 매번 메모리 재읽기 강제.

</details>
<details>
<summary>Q2. (Understand) Mutex 를 ISR 에서 쓰면 안 되는 이유?</summary>

Mutex 는 *block* 한다 — ISR 안에서 blocking 은 deadlock 위험 + ISR latency 폭증. 대신 *binary semaphore signal* (non-blocking give) 또는 *lock-free queue* 사용.

</details>
<details>
<summary>Q3. (Analyze) 다음 코드의 버그는?</summary>

```c
char buf[256];
void uart_isr(void) {
    static int idx = 0;
    buf[idx++] = read_uart();
    if (idx == 256) idx = 0;
}
void main(void) {
    process(buf);  // ISR 와 race
}
```
1. `buf` 가 `volatile` 아님 → main 의 `process(buf)` 가 cache 된 값을 봄.
2. `idx` 가 atomic 아니지만 1-byte 라면 보통 OK (조건부, MCU 에 따라). 더 큰 문제는 main 이 ISR 중간 시점의 *반쯤 쓴* buf 를 읽는 race → critical section 보호 필요 (IRQ disable 또는 double buffer).

</details>
<details>
<summary>Q4. (Evaluate) RTOS 에서 priority inversion(우선순위 역전 — 높은 우선순위 task가, 낮은 task가 쥔 mutex를 기다리느라 오히려 중간 우선순위 task에 밀리는 현상) 을 막는 방법?</summary>

**Priority inheritance** — 낮은 우선순위 task 가 mutex 잡고 있을 때, 높은 우선순위 task 가 그 mutex 를 요청하면, 낮은 task 의 priority 를 *임시로 높여* 빨리 끝내게.

**Priority ceiling** — mutex 마다 *최대 가능 priority* 를 미리 설정, mutex 잡은 자는 그 priority 로 즉시 승격.

</details>
<details>
<summary>Q5. (Design) 1 ms 마다 sensor 를 polling 하면서 동시에 UART 명령도 처리하는 임베디드 구조는?</summary>

**Option A — Bare-metal + IRQ**:
- Timer IRQ (1ms) → sensor read + 처리 flag set
- UART IRQ → byte 받기, 줄 단위로 명령 flag set
- Main loop: flag 보고 처리. 둘이 *짧으면* 충분.

**Option B — RTOS**:
- Sensor task (priority 높음) — `vTaskDelayUntil(1ms)` 주기 실행
- UART task — queue 로 byte 받아 처리
- Mutex 또는 queue 로 둘 간 데이터 공유.

Sensor 가 *결정적 timing* 이 필요하면 Bare-metal IRQ, 복잡한 명령 파싱이 많으면 RTOS.

</details>
---

## 8. 핵심 정리 (Key Takeaways)

1. RTOS 는 *결정적 latency + 동시성* 이 필요할 때. 작은 시스템은 bare-metal + IRQ.
2. I2C = 짧고 다중 slave, SPI = 빠르고 단일, CAN = 자동차/노이즈, UART = 디버그.
3. Bit manipulation, circular buffer, endianness 는 *반드시* 외우는 코딩.
4. `volatile` 은 *최적화 금지*, 동시성 *해결책 아님* (atomic / mutex 별도).
5. 임베디드에서 `malloc` 은 *피하고* memory pool 사용.
6. DMA + write-back cache → cache flush/invalidate 필수.

## 9. Further Reading

- *Making Embedded Systems* (Elecia White) — RTOS / driver 디자인
- *The C Programming Language* (K&R) — 임베디드 C 베이스
- ARM Cortex-M Programming Guide — Cortex-M3/M4 에서 IRQ / cache 처리
- FreeRTOS Kernel Reference Manual
- [Unit 3 퀴즈](../quiz/03_embedded_firmware_quiz/) 로 자기 점검
