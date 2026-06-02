---
title: "Quiz — Unit 3: Embedded / Firmware"
---

[← Unit 3 본문으로 돌아가기](../../03_embedded_firmware/)

---

## Q1. (Remember)

`volatile` 키워드는 컴파일러에게 무엇을 강제하는가?

<details>
<summary>정답 / 해설</summary>

컴파일러에게 해당 변수는 외부 요인(하드웨어 레지스터, ISR, DMA 등)에 의해 언제든지 변경될 수 있음을 알려, 레지스터 캐싱·dead store elimination·루프 호이스팅 같은 최적화를 적용하지 않도록 강제한다. 이로써 컴파일러는 매번 메모리 주소에서 실제로 읽어야 한다. `volatile`이 없으면 컴파일러는 "변수가 코드 흐름 내에서 변하지 않는다"고 판단해 읽기를 생략하거나 이전에 레지스터에 올려둔 값을 재사용할 수 있고, 그 결과 메모리 맵 I/O 레지스터 값이나 ISR이 기록한 값을 main loop가 보지 못하는 버그가 생긴다.

</details>
## Q2. (Understand)

I2C 와 SPI 의 가장 큰 *구조적* 차이 3가지를 짧게 답하라.

<details>
<summary>정답 / 해설</summary>

1. **핀 수** — I2C는 SDA+SCL 2선 버스로 모든 device가 공유한다. SPI는 SCLK+MOSI+MISO 공통선에 slave마다 개별 CS 핀이 필요해 slave가 많을수록 핀이 늘어난다.
2. **Master 수** — I2C는 multi-master arbitration(START 충돌 감지)을 프로토콜 레벨에서 지원한다. SPI는 single-master 구조이며 multi-master는 별도 중재 로직이 필요하다.
3. **속도** — I2C는 표준 100kbps, 고속 3.4Mbps가 상한이다. SPI는 클럭 주파수 제약이 상대적으로 낮아 수십~수백 MHz도 가능하다.
4. 추가: I2C는 open-drain 버스라 pull-up 저항이 필수이며, SPI는 push-pull 드라이브로 full-duplex 통신이 가능하다. 면접에서는 "언제 무엇을 선택하느냐"까지 연결하는 것이 좋다 — slave가 많고 저속이면 I2C, 고속 단일 slave면 SPI.

</details>
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

<details>
<summary>정답 / 해설</summary>

`sensor_val`이 32비트라도 하드웨어 아키텍처나 컴파일러에 따라 단일 로드가 atomic으로 보장되지 않을 수 있다. 더 중요한 문제는 `main`이 `v = sensor_val`로 읽는 도중에 timer ISR이 끼어들어 `sensor_val`을 갱신하면, `main`이 갱신 전 값을 읽게 된다는 점이다. 이 경우 `v + offset`이 잘못된 값을 기반으로 계산되어 `alarm()`이 오작동할 수 있다.

**수정**: critical section.
```c
int v;
__disable_irq();
v = sensor_val;
__enable_irq();
```
인터럽트 비활성화 구간을 최소화해야 시스템 응답성을 유지할 수 있다. 더 긴 데이터(예: 64비트 타임스탬프, 구조체)라면 double-buffering + 완료 플래그 패턴으로 ISR이 버퍼에 쓰고 main이 플래그 확인 후 복사하는 방식이 더 적합하다.

</details>
## Q4. (Analyze)

`memcpy` 와 `memmove` 중 *영역 overlap* 이 있을 때 안전한 것은? 이유는?

<details>
<summary>정답 / 해설</summary>

**memmove**. `memmove`는 내부적으로 `dst < src`이면 앞에서부터(low address → high) 복사하고, `dst > src`이면 뒤에서부터(high → low) 복사함으로써 소스 데이터가 복사 도중에 덮어씌워지는 것을 방지한다. `memcpy`는 소스와 목적지가 겹치지 않는다고 가정하고 항상 한 방향으로만 복사하므로, overlap 상황에서는 undefined behavior(UB)가 된다. 실제로 많은 최신 컴파일러와 라이브러리에서 `memcpy`가 `memmove`처럼 동작하기도 하지만, C 표준은 overlap된 `memcpy`를 UB로 명시하므로 이식성과 정확성을 위해 overlap 가능성이 있으면 반드시 `memmove`를 사용해야 한다.

</details>
## Q5. (Apply)

Circular buffer 의 `head == tail` 이 *empty* 인지 *full* 인지 구분하는 두 가지 방법은?

<details>
<summary>정답 / 해설</summary>

1. **`full` flag** — head를 advance한 뒤 head == tail이 되면 full 플래그를 1로 설정하고, `get()` 호출 시 0으로 클리어한다. `head == tail`이면 full 플래그를 확인해 empty와 full을 구분한다. 모든 슬롯을 활용할 수 있지만 플래그 관리 로직이 추가된다.
2. **capacity = size − 1** — 항상 1슬롯을 비워둬서 head == tail이면 empty, `(head+1) % size == tail`이면 full로 단순 판정한다. 별도 플래그 없이 포인터 비교만으로 상태를 알 수 있어 코드가 단순하지만, 버퍼 용량이 한 슬롯 줄어드는 대신이다.

Trade-off: ISR 공유 환경에서는 플래그 기반이 atomic 처리를 별도로 요구하므로 코드 단순성 면에서 두 번째 방식이 선호될 때가 많다.

</details>
## Q6. (Understand)

Mutex 와 binary semaphore 의 차이는?

<details>
<summary>정답 / 해설</summary>

Mutex는 *소유 개념*이 있다. lock을 획득한 task만 unlock할 수 있으므로, 다른 task가 실수로 unlock하는 상황이 원천 차단된다. RTOS에서 mutex는 priority inheritance를 지원해 낮은 우선순위 task가 mutex를 잡고 있을 때 중간 우선순위 task에 의한 priority inversion을 방지할 수 있다. Binary semaphore는 *소유 개념이 없어* take와 give를 서로 다른 task(또는 ISR)가 할 수 있다. 이 비대칭 특성 덕분에 "ISR이 완료를 알리고 main task가 기다리는" 이벤트 통지 패턴에 적합하다. 공통점은 두 primitive 모두 0/1 상태를 갖는 이진 잠금 구조라는 것이다. 면접에서는 "공유 자원 보호 → mutex, ISR 시그널링 → binary semaphore"라는 사용 패턴 구분을 반드시 말해야 한다.

</details>
## Q7. (Evaluate)

CAN 이 자동차에서 RS-485 나 I2C 대신 선택되는 *3가지 이유* 는?

<details>
<summary>정답 / 해설</summary>

1. **Differential signaling** — CAN은 CAN_H/CAN_L 두 선의 차동 전압을 사용한다. 자동차 환경의 강한 EMI에서 두 선이 함께 영향을 받으므로 차이 신호가 보존되어 I2C(single-ended)나 RS-485보다 훨씬 높은 노이즈 내성을 갖는다.
2. **Priority arbitration** — 충돌 시 ID 값이 작은(dominant bit이 많은) 메시지가 버스를 획득한다. 이는 중재 자체가 파괴적이지 않아 높은 우선순위 메시지의 지연을 결정론적으로 상한 지을 수 있다 — 안전 크리티컬 신호에 필수적인 특성이다.
3. **Broadcast topology** — 모든 노드가 같은 메시지를 수신하므로 노드 추가·제거 시 배선을 변경할 필요 없이 ID 필터만 조정하면 된다. RS-485의 point-to-point 구성보다 확장성이 우수하다.

추가로 CAN은 7단계 에러 감지(CRC, bit monitoring, frame check 등)와 버스 off 메커니즘으로 결함 노드가 네트워크 전체를 망가뜨리지 않도록 격리한다.

</details>
## Q8. (Apply)

Write-back 캐시 + DMA 가 같은 메모리 영역을 다룰 때 *cache flush* 와 *cache invalidate* 를 *언제* 호출해야 하는지 설명하라.

<details>
<summary>정답 / 해설</summary>

1. **DMA write → CPU read** (DMA가 RAM에 쓰고 CPU가 읽음): CPU read *전에* **invalidate**를 호출한다. 이유는 CPU 캐시에 같은 주소의 stale 데이터가 있을 수 있기 때문이다. invalidate는 캐시 라인을 무효화해 이후 CPU 읽기가 반드시 RAM에서 최신 DMA 결과를 fetch하도록 강제한다.
2. **CPU write → DMA read** (CPU가 쓴 데이터를 DMA가 RAM에서 읽음): DMA start *전에* **flush(write-back)**를 호출한다. write-back 캐시에서는 CPU 쓰기가 캐시에만 반영되고 RAM은 아직 이전 값을 갖는 dirty 상태일 수 있다. flush는 dirty 캐시 라인을 RAM으로 내려써서 DMA가 최신 값을 읽도록 보장한다.

Flush와 invalidate를 반대 순서로 호출하거나 빼먹으면 DMA가 오래된 값을 전송하거나 CPU가 DMA 결과 대신 캐시 stale 값을 읽는 데이터 오염이 발생한다. 이 두 방향의 순서를 각각 정확히 외우는 것이 면접 포인트다.

</details>
