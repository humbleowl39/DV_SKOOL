---
title: "Quiz — Module 04: Mass Storage·I/O 시스템·DMA"
---

[← Module 04 본문으로 돌아가기](../../04_storage_io_dma/)

---

## Q1. (Remember)

memory-mapped I/O 의 device control register 네 가지에 해당하지 않는 것은?

- [ ] A. data-in
- [ ] B. status
- [ ] C. control
- [ ] D. relocation

<details>
<summary>정답 / 해설</summary>

**D**. device control register 는 보통 data-in(host read), data-out(host write), status(host read, busy/완료/error 표시), control(host write, 명령 시작/mode 변경) 네 가지입니다(§12.2.1). "relocation" 은 MMU 의 주소 번역 register(M03)이지 I/O register 가 아닙니다.

</details>
## Q2. (Understand)

polling(busy-waiting) 한 번이 "값싸다"고 하면서도 문제가 되는 상황을 설명하라.

<details>
<summary>정답 / 해설</summary>

(§12.2.2) 한 번의 polling 은 status register read + status bit 을 logical-AND 로 추출 + 결과 분기, 세 instruction 이면 되는 값싼 일입니다. 문제는 device 가 좀처럼 준비되지 않는데도 CPU 가 그것을 *계속 반복해서* 들여다볼 때입니다 — 그 사이 CPU 가 할 수 있는 다른 일이 밀립니다. 그래서 device 가 준비됐을 때 controller 가 CPU 를 불러주는 interrupt 방식이 더 나은 발상으로 등장합니다.

</details>
## Q3. (Apply)

polling write handshake 에서 host 와 controller 가 두 bit(busy, command-ready)으로 손발을 맞춘다. host 가 명령을 보내는 절차를 순서대로 쓰라.

<details>
<summary>정답 / 해설</summary>

(§12.2.2):
1. host 가 status 의 **busy bit 이 clear** 될 때까지 반복해 읽음(polling).
2. host 가 data-out 에 데이터를 쓰고, command register 의 **command-ready bit 을 set**.
3. controller 가 이를 보고 **busy 를 set** 한 뒤 명령을 실행.
4. controller 가 command-ready 와 error 를 clear 하고, 마지막으로 **busy 를 clear** 해 완료를 알림.
- DV 포인트: busy clear 가 *마지막에* 일어나는 순서가 핵심 — 이 순서 위반이 protocol checker 의 검출 대상.

</details>
## Q4. (Apply)

DMA 로 disk→메모리 대량 전송을 시작할 때, CPU 가 직접 하는 일은 무엇인가?

- [ ] A. byte 를 하나씩 controller register 에 밀어 넣는다
- [ ] B. command block 을 만들고 그 주소만 DMA controller 에 적어준다
- [ ] C. 전송이 끝날 때까지 status bit 을 polling 한다
- [ ] D. 각 byte 마다 interrupt 를 처리한다

<details>
<summary>정답 / 해설</summary>

**B**. CPU 는 메모리에 DMA command block(source/destination 주소, byte 수)을 만들고 그 *주소만* DMA controller 에 적어준 뒤 다른 일로 넘어갑니다(§12.2.4). A 는 programmed I/O(PIO)로 DMA 가 피하려는 바로 그 낭비이고, C·D 는 DMA 의 이점(CPU 해방)을 없앱니다 — 전송 완료는 controller 가 거는 *한 번의* 완료 interrupt 로 통보됩니다.

</details>
## Q5. (Analyze)

SSD 워크로드에서 한 번의 application write 가 실제로는 여러 번의 물리 I/O 로 부풀어 성능이 떨어진다. 원인을 NAND 특성과 연결해 분석하라.

<details>
<summary>정답 / 해설</summary>

(§11.1.2, §11.3) NAND 는 **page 단위로 읽고 쓰지만 덮어쓸 수 없어**, 먼저 여러 page 를 묶은 **block 단위로 erase** 해야 합니다. 유효 데이터를 모아 block 을 비우는 **garbage collection** 이 application 과 무관한 내부 read/write 를 유발합니다. 그래서 한 번의 논리적 write 가 여러 물리 I/O 로 부푸는 **write amplification** 이 발생해 성능을 깎습니다. controller 는 FTL·over-provisioning(여유 공간)·wear leveling 으로 이를 완화하지만 완전히 없애지는 못합니다 — OS 는 이 복잡성을 모른 채 LBA 만 읽고 씁니다.

</details>
## Q6. (Evaluate)

평상시에는 interrupt-driven I/O 가 일반적인데, 초고속 high-throughput 구간에서는 polling 이 함께 쓰이기도 한다. 이 선택을 throughput·CPU 점유 기준으로 평가하라.

<details>
<summary>정답 / 해설</summary>

(§12.2.3) 책은 *"Interrupt-driven I/O is now much more common than polling, with polling being used for high-throughput I/O. Sometimes the two are used together"* 라고 정리합니다.
- **interrupt**: CPU 를 묶지 않아 일반 device 에 적합하지만, 완료마다 context switch + handler dispatch 오버헤드가 듭니다.
- **polling**: 완료가 매우 빈번하고 빠르면, 그 오버헤드를 이벤트 수만큼 곱하는 것보다 status 를 직접 도는(3 instruction) 편이 빠릅니다 — high-throughput 구간에서 유리.
- 평가: "interrupt 가 항상 우월"이 아니라 *부하 의존*이며, driver 가 I/O rate 에 따라 둘을 오가는 것이 최적. I/O 성능 일반 원칙은 context switch·복사를 줄이고 단순 복사를 DMA 로 offload(§12.7).

</details>
