# Unit 3 — Embedded Systems / Firmware

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Design** thermostat / battery charger 같은 작은 임베디드 시스템의 sensor → MCU → actuator 데이터 플로우를 설계한다.
    - **Compare** I2C / SPI / UART / CAN 의 핀 수, 속도, multi-master 지원, 노이즈 면역성을 비교한다.
    - **Implement** circular buffer, linked list, bit manipulation 등 임베디드 빈출 자료구조 / 비트연산을 C 로 작성한다.
    - **Distinguish** process / thread / context switch / mutex / semaphore / atomic 의 차이를 설명한다.
    - **Apply** `volatile`, linker script, `memcpy` vs `memmove`, custom `malloc` 같은 메모리 관련 코드를 정확히 작성한다.
    - **Explain** 캐시 hit/miss, locality, replacement policy, write-through vs write-back, MESI 의 임베디드 영향을 설명한다.

!!! info "사전 지식"
    - C 언어 (포인터, struct, 함수 포인터)
    - 컴퓨터 구조 기본 (CPU, 메모리, 캐시)
    - 운영체제 기본 (process, scheduling)

---

## 1. 시스템 설계 — 인터뷰 빈출 시나리오

### 1.1 Thermostat 설계

**요구**: 실내 온도를 ±0.5°C 로 유지.

```
[Temp sensor] --I2C--> [MCU] --PWM--> [Heater relay]
                         |
                         +--UART--> [Display]
                         |
                         +--Button input (GPIO + IRQ)
```

**설계 포인트** (인터뷰 답변 시 다루어야 할 것):

1. **Sample rate** — 너무 빠르면 power 낭비, 너무 느리면 oscillation. 1~5초 주기.
2. **Filter** — sensor noise 제거. Moving average 또는 IIR low-pass.
3. **Hysteresis** — heater on / off threshold 차이 (예: 22°C 에서 on, 22.5°C 에서 off). *Bang-bang* 제어의 chattering 방지.
4. **PID 또는 PWM duty cycle** — 비례 제어 시 PID, 단순 on/off 면 hysteresis.
5. **Watchdog** — sensor stuck 또는 firmware hang 감지.
6. **Failsafe** — 통신 끊기면 heater OFF (open-circuit safe).

### 1.2 RTOS vs Bare-metal

| 항목 | Bare-metal | RTOS (FreeRTOS, Zephyr) |
|------|------------|-------------------------|
| 구조 | `main()` 안에 while(1) + ISR | Task + Scheduler |
| 우선순위 | 인터럽트만 가짐 | Task priority + preemption |
| 동기화 | volatile + IRQ disable | Mutex, semaphore, queue |
| 메모리 | Static / linker 영역 | + heap (RTOS 가 관리) |
| 디버그 | 단순 | Task stack 추적 필요 |
| 사용 시기 | < 5 KB code, 단일 control loop | 다중 동시 작업, 통신 + 제어 |

---

## 2. Protocols & Interconnects — 임베디드 관점

| Protocol | 핀 수 | 속도 | Multi-master | 노이즈 | 거리 |
|----------|-------|------|--------------|--------|------|
| **I2C** | 2 (SDA, SCL) | 100K ~ 3.4M bps | ✅ (arbitration) | 약함 (open-drain) | < 1m |
| **SPI** | 4+ (SCLK, MOSI, MISO, CS) | 수십 MHz | ❌ (single master) | 강함 (push-pull) | < 30cm |
| **UART** | 2 (TX, RX) | ~ 3 Mbps | ❌ | 중간 | 거리 한계 짧음 |
| **CAN** | 2 (CAN_H, CAN_L) | 1 Mbps (CAN-FD: 8 Mbps) | ✅ (priority arbitration) | **매우 강함** (differential) | 자동차 전체 |
| **RS-485** | 2 (differential) | ~ 10 Mbps | half-duplex multi-drop | 강함 | 1200m |

### 2.1 I2C — 가장 자주 묻는 디테일

- **Open-drain** — 외부 pull-up 필수. 두 master 가 동시에 SDA 잡으면 *둘 다 LOW 가 우선* → arbitration 가능.
- **START / STOP** — `SDA falling while SCL high` = START, `SDA rising while SCL high` = STOP.
- **ACK / NACK** — 9 번째 클럭에 receiver 가 SDA 를 LOW 로 → ACK.
- **Clock stretching** — slave 가 SCL 을 LOW 로 잡아 master 에 backpressure.

### 2.2 SPI 의 Mode 4가지

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

| 항목 | Process | Thread |
|------|---------|--------|
| Address space | 독립 | 공유 |
| Context switch cost | 비쌈 (TLB flush) | 쌈 (PC + registers 만) |
| 통신 | IPC (pipe, socket, shared mem) | 공유 변수 + mutex |
| Crash isolation | 강함 | 약함 (한 thread crash → 모두 죽음) |

### 4.2 Mutex vs Semaphore

- **Mutex** — 0/1 binary, *소유 개념 있음* (lock 한 자만 unlock 가능). 일반적인 critical section 보호.
- **Counting Semaphore** — N 카운트, *소유 개념 없음*. Resource pool 관리, producer-consumer counting.
- **Binary semaphore** — semaphore 의 특수 형태. mutex 와 비슷하지만 *소유* 가 없어 ISR 에서 signal 가능.

### 4.3 Atomic Operations

```c
// GCC built-in
__atomic_fetch_add(&counter, 1, __ATOMIC_SEQ_CST);
__atomic_compare_exchange_n(&x, &expected, new, false, __ATOMIC_SEQ_CST, __ATOMIC_RELAXED);

// C11
atomic_int counter = 0;
atomic_fetch_add(&counter, 1);
```

**왜 atomic?** `counter++` 는 `load - add - store` 3개 명령. Multi-core / preempt 환경에서 race. CAS (compare-and-swap) 가 lock-free 자료구조의 기반.

### 4.4 Context Switch — 무엇이 저장되나?

1. **CPU register file** (general purpose, SP, LR, PC)
2. **PSR / CPSR** — flags, mode
3. **FPU register** — FP 사용 task 라면
4. **(VM 사용 시) Page table base register**, TLB flush 필요할 수 있음

---

## 5. 메모리 / 드라이버

### 5.1 `volatile` — 컴파일러에게 *최적화 금지*

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
- Fragmentation → 시간이 갈수록 큰 chunk 못 받음
- 결정적이지 않은 latency
- Out-of-memory 시 복구 어려움

**대안**:
- *Static 할당* — 컴파일 타임에 모든 메모리 결정
- *Memory pool* — 같은 크기 chunk 를 미리 N 개 할당 → fragmentation 없음
- *Buddy allocator* — 2의 제곱 크기 chunk, fragmentation 적음

---

## 6. Cache & Coherency — 펌웨어 관점

### 6.1 Locality

- **Temporal** — 최근 접근 데이터를 곧 다시 접근 (loop counter, function call frame)
- **Spatial** — 인접 주소를 곧 접근 (array iteration)

**임베디드 영향**: `struct of arrays` vs `array of structs`. 한 필드만 자주 쓰면 SoA 가 cache hit 율 높음.

### 6.2 Write-through vs Write-back

| Policy | Write 시 | 장점 | 단점 |
|--------|----------|------|------|
| Write-through | RAM + cache 동시 갱신 | 항상 RAM 이 최신 → coherency 단순 | RAM bandwidth 많이 씀 |
| Write-back | Cache 만 갱신, dirty 비트 set | Bandwidth 절약 | Coherency 복잡, eviction 시 RAM write |

**DMA 충돌 흔한 시나리오**: Write-back 캐시 + DMA 가 같은 영역 접근 → cache flush (CPU → RAM) 후 DMA start, 또는 cache invalidate (DMA → CPU 데이터) 후 CPU read.

### 6.3 MESI 의 직관

각 cache line 은 4 상태:
- **M** (Modified) — dirty, 나만 가짐
- **E** (Exclusive) — clean, 나만 가짐
- **S** (Shared) — clean, 여러 코어 가짐
- **I** (Invalid) — 없음

다른 코어 write 시 *내 S 또는 E* → *I* 로 invalidate.

---

## 7. 샘플 인터뷰 Q&A

??? question "Q1. (Apply) `volatile int x; while (x);` 가 무한 루프지만 다른 곳에서 x = 0 되기를 기다리는 코드인데, `volatile` 없으면?"
    컴파일러가 `x` 를 *레지스터에 로드 한 번* 하고 더 이상 읽지 않을 수 있다 → 다른 곳에서 x 가 0 이 되어도 *영원히* 루프. `volatile` 이 매번 메모리 재읽기 강제.

??? question "Q2. (Understand) Mutex 를 ISR 에서 쓰면 안 되는 이유?"
    Mutex 는 *block* 한다 — ISR 안에서 blocking 은 deadlock 위험 + ISR latency 폭증. 대신 *binary semaphore signal* (non-blocking give) 또는 *lock-free queue* 사용.

??? question "Q3. (Analyze) 다음 코드의 버그는?"
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

??? question "Q4. (Evaluate) RTOS 에서 priority inversion 을 막는 방법?"
    **Priority inheritance** — 낮은 우선순위 task 가 mutex 잡고 있을 때, 높은 우선순위 task 가 그 mutex 를 요청하면, 낮은 task 의 priority 를 *임시로 높여* 빨리 끝내게.

    **Priority ceiling** — mutex 마다 *최대 가능 priority* 를 미리 설정, mutex 잡은 자는 그 priority 로 즉시 승격.

??? question "Q5. (Design) 1 ms 마다 sensor 를 polling 하면서 동시에 UART 명령도 처리하는 임베디드 구조는?"
    **Option A — Bare-metal + IRQ**:
    - Timer IRQ (1ms) → sensor read + 처리 flag set
    - UART IRQ → byte 받기, 줄 단위로 명령 flag set
    - Main loop: flag 보고 처리. 둘이 *짧으면* 충분.

    **Option B — RTOS**:
    - Sensor task (priority 높음) — `vTaskDelayUntil(1ms)` 주기 실행
    - UART task — queue 로 byte 받아 처리
    - Mutex 또는 queue 로 둘 간 데이터 공유.

    Sensor 가 *결정적 timing* 이 필요하면 Bare-metal IRQ, 복잡한 명령 파싱이 많으면 RTOS.

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
- [Unit 3 퀴즈](quiz/03_embedded_firmware_quiz.md) 로 자기 점검
