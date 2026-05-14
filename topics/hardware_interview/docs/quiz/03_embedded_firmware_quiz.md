# Quiz — Unit 3: Embedded / Firmware

[← Unit 3 본문으로 돌아가기](../03_embedded_firmware.md)

---

## Q1. (Remember)

`volatile` 키워드는 컴파일러에게 무엇을 강제하는가?

??? answer "정답 / 해설"
    해당 변수의 *값이 외부 요인으로 변할 수 있다* 고 알려, *최적화 (register caching, dead store elimination 등) 를 금지* 시킴. 매번 메모리에서 다시 읽도록 강제.

## Q2. (Understand)

I2C 와 SPI 의 가장 큰 *구조적* 차이 3가지를 짧게 답하라.

??? answer "정답 / 해설"
    1. **핀 수** — I2C 2 (SDA+SCL), SPI 4+ (SCLK+MOSI+MISO+CS)
    2. **Master 수** — I2C multi-master 가능, SPI single-master
    3. **속도** — I2C 100K~3.4Mbps, SPI 수십 MHz (훨씬 빠름)
    4. *추가*: I2C 는 open-drain (pull-up 필요), SPI 는 push-pull / full-duplex.

## Q3. (Apply)

다음 코드의 *race condition* 을 식별하고 수정하라.
```c
volatile int sensor_val;
void timer_isr(void) { sensor_val = read_adc(); }
void main(void) {
    while (1) {
        int v = sensor_val;
        v = v + offset;
        if (v > THRESHOLD) alarm();
    }
}
```

??? answer "정답 / 해설"
    `sensor_val` 이 32-bit 라면 단일 load 이 atomic 일 수 있지만, *plain int* 가 항상 그렇다는 보장은 없음 (MCU/컴파일러 의존). 더 큰 문제는 **timer_isr 의 read_adc() 가 길면** 가운데 main 이 *이전 값* 사용 가능.

    **수정**: critical section.
    ```c
    int v;
    __disable_irq();
    v = sensor_val;
    __enable_irq();
    ```
    또는 multi-byte 신호라면 *double-buffering* + flag.

## Q4. (Analyze)

`memcpy` 와 `memmove` 중 *영역 overlap* 이 있을 때 안전한 것은? 이유는?

??? answer "정답 / 해설"
    **memmove**. 내부적으로 `dst < src` 면 *앞에서* 복사, `dst > src` 면 *뒤에서* 복사해 자기 자신을 덮어쓰지 않게 한다. `memcpy` 는 overlap 가정 안 함 → UB.

## Q5. (Apply)

Circular buffer 의 `head == tail` 이 *empty* 인지 *full* 인지 구분하는 두 가지 방법은?

??? answer "정답 / 해설"
    1. **`full` flag** — head++ 후 head == tail 이면 full=1, get() 호출 시 full=0.
    2. **capacity = size − 1** — 항상 1 slot 비워둠. head == tail 이면 empty, (head+1)%size == tail 이면 full.

    Trade-off: 첫 번째는 모든 slot 사용 가능, 두 번째는 코드 단순 (flag 없음).

## Q6. (Understand)

Mutex 와 binary semaphore 의 차이는?

??? answer "정답 / 해설"
    - **Mutex** — *소유 개념 있음*. Lock 한 task 만 unlock 가능. Priority inheritance 지원 (RTOS 에서).
    - **Binary semaphore** — *소유 개념 없음*. Take/give 어느 task 든 가능. ISR 에서 signal 용도 적합.

    *공통점*: 0/1 상태.

## Q7. (Evaluate)

CAN 이 자동차에서 RS-485 나 I2C 대신 선택되는 *3가지 이유* 는?

??? answer "정답 / 해설"
    1. **Differential signaling** — 노이즈 면역 (자동차 환경 EMI 매우 강함)
    2. **Priority arbitration** — 충돌 시 ID 작은 메시지 우선 → 결정적 latency
    3. **Broadcast topology** — 모든 노드가 메시지 수신 → 노드 추가/제거 쉬움

    (보너스: error detection 강력, 다중 fault confinement)

## Q8. (Apply)

Write-back 캐시 + DMA 가 같은 메모리 영역을 다룰 때 *cache flush* 와 *cache invalidate* 를 *언제* 호출해야 하는지 설명하라.

??? answer "정답 / 해설"
    1. **DMA write → CPU read** (DMA 가 RAM 에 쓰고 CPU 가 읽음):
       *CPU read 전* 에 **invalidate** — cache 의 stale 데이터 제거 후 RAM 에서 새로 fetch.
    2. **CPU write → DMA read** (CPU 가 쓴 데이터를 DMA 가 RAM 에서 읽음):
       *DMA start 전* 에 **flush** (write-back) — dirty cache line 을 RAM 으로 내려보내 DMA 가 최신값 읽도록.

    Flush 와 invalidate 를 *반대 순서* 로 호출하거나 빼먹으면 데이터 깨짐.
