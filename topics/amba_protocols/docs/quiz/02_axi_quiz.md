# Quiz — Module 02: AXI

[← Module 02 본문으로 돌아가기](../02_axi.md)

---

## Q1. (Remember)

AXI의 5채널을 모두 나열하고, 각 채널의 데이터 흐름 방향을 답하세요.

??? answer "정답 / 해설"
    - **AW** (Write Address) — Master → Slave
    - **W** (Write Data) — Master → Slave
    - **B** (Write Response) — Slave → Master
    - **AR** (Read Address) — Master → Slave
    - **R** (Read Data + Response) — Slave → Master

    Read 3채널, Write 3채널 (B와 AW/W 분리). 각 채널이 독립적이라 full-duplex 가능.

    AXI가 5개 채널을 독립적으로 분리한 이유는 각각의 흐름이 서로 다른 속도로 진행될 수 있기 때문입니다. 예를 들어 Write Address(AW)는 빠르게 발행되더라도 Write Data(W)가 아직 준비 중이면 W 채널만 stall하면 되고, 나머지 채널은 계속 동작합니다. 이 덕분에 Read와 Write가 동시에 진행되는 full-duplex 동작이 가능하며, 여러 트랜잭션이 겹치는 outstanding 전송도 지원됩니다.

## Q2. (Understand)

VALID/READY 핸드셰이크에서 다음 중 **데드락을 유발하는** 패턴은?

- [ ] A. Source가 VALID를 올린 후 READY 기다림
- [ ] B. Source가 "READY가 1이 될 때까지 VALID를 0으로 유지"
- [ ] C. Sink가 READY를 자유롭게 올렸다 내림
- [ ] D. Source가 VALID=1 상태에서 데이터 신호 유지

??? answer "정답 / 해설"
    **B**. AXI 사양은 "VALID는 READY와 무관하게 올려야 한다"고 명시. Source가 READY를 기다리고 Sink가 VALID를 기다리면 영원히 대기 → 데드락. **A**는 정상 (VALID 올린 후 READY 기다리는 건 OK).

    B가 데드락을 유발하는 이유는 "Source는 READY=1을 확인하기 전까지 VALID를 올리지 않겠다"고 기다리고, 동시에 "Sink는 VALID=1이 올 때까지 READY를 올리지 않겠다"고 기다리는 교착 상태가 되기 때문입니다. AXI 사양(IHI0022)은 이 문제를 방지하기 위해 Source가 READY와 완전히 무관하게 먼저 VALID를 올릴 것을 강제합니다. A는 VALID를 먼저 올린 뒤 READY를 기다리는 올바른 패턴이고, C와 D는 정상적인 동작입니다.

## Q3. (Apply)

AXI4 INCR burst, AxLEN=15, AxSIZE=3'b011 (8 bytes/beat) 일 때 총 전송 바이트 수는?

??? answer "정답 / 해설"
    AxLEN은 N-1 인코딩이므로 beat 수 = 15 + 1 = **16 beats**. 총 = 16 × 8 = **128 bytes**.

    AXI4에서 AxLEN 필드는 "실제 beat 수 − 1"로 인코딩됩니다. 따라서 AxLEN=15는 16 beat를 의미합니다. 각 beat의 폭은 AxSIZE=3'b011으로, 2^3 = 8 bytes입니다. 곱하면 16 × 8 = 128 bytes가 됩니다. 흔히 하는 실수는 AxLEN 값을 그대로 beat 수로 읽어 15 × 8 = 120 bytes로 계산하는 것인데, AXI4의 N-1 인코딩 규칙을 반드시 적용해야 합니다.

## Q4. (Analyze)

Master가 ID=0,1,2 순서로 AR을 발행했는데 Slave가 ID=2,0,1 순서로 R을 응답했다. AXI 사양 위반인가?

??? answer "정답 / 해설"
    **위반 아님**. AXI는 같은 ID 내 in-order, ID 간 OoO 허용. ID=0,1,2가 모두 다르므로 응답 순서가 자유. 단, 만약 Master가 같은 ID로 ID=0, ID=0 두 번 발행했다면 두 응답은 발행 순서대로 와야 함. Scoreboard도 per-ID 큐로 매칭해야 정확.

    AXI의 ordering 규칙은 "같은 ID를 가진 트랜잭션끼리는 발행 순서대로 응답해야 하지만, 서로 다른 ID 사이에는 순서 제약이 없다"입니다. ID=0, ID=1, ID=2는 모두 다른 ID이므로 슬레이브가 ID=2 → ID=0 → ID=1 순서로 응답해도 전혀 사양 위반이 아닙니다. 이 덕분에 슬레이브는 처리가 빠른 트랜잭션을 먼저 돌려줄 수 있고, 시스템 처리량이 높아집니다. 검증 관점에서는 Scoreboard가 단순한 FIFO 큐로 응답을 매칭하면 틀릴 수 있으므로, 반드시 ID별로 독립된 큐를 유지해야 합니다.

## Q5. (Evaluate)

다음 중 Modifiable=0 (AxCACHE[1]=0) 트랜잭션에 대해 Interconnect가 **할 수 없는** 동작은?

- [ ] A. 그대로 통과시키기
- [ ] B. Slave 측에서 응답 받기
- [ ] C. 두 개의 작은 트랜잭션으로 분할하기
- [ ] D. 캐시 hit 시 응답하기

??? answer "정답 / 해설"
    **C**. Modifiable=0이면 Interconnect가 분할/병합/재정렬 불가. Device 메모리 영역(레지스터)에 필수 — 같은 주소에 두 번 access를 한 번으로 합치면 hardware register의 W1C 등 동작이 깨짐.

    AxCACHE[1]=0(Modifiable=0)은 인터커넥트가 트랜잭션의 속성을 임의로 바꾸는 것을 금지합니다. C처럼 트랜잭션을 두 개로 분할하는 것은 "하나의 요청"을 "두 개의 요청"으로 변형하는 행위이므로 명백히 Modifiable=0 위반입니다. 이것이 특히 중요한 이유는 하드웨어 레지스터에는 "읽으면 클리어(R/C)", "1을 쓰면 클리어(W1C)" 같은 부수 효과(side-effect) 동작이 있어서, 같은 주소에 대한 접근 횟수나 크기가 달라지면 의도와 다른 레지스터 상태가 만들어지기 때문입니다. A(그대로 통과)와 B(응답 수신)는 허용 동작이고, D(캐시 hit 응답)는 Modifiable이 아닌 Cacheable 속성과 관련된 별개의 개념입니다.
