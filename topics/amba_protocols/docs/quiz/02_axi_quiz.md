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

## Q2. (Understand)

VALID/READY 핸드셰이크에서 다음 중 **데드락을 유발하는** 패턴은?

- [ ] A. Source가 VALID를 올린 후 READY 기다림
- [ ] B. Source가 "READY가 1이 될 때까지 VALID를 0으로 유지"
- [ ] C. Sink가 READY를 자유롭게 올렸다 내림
- [ ] D. Source가 VALID=1 상태에서 데이터 신호 유지

??? answer "정답 / 해설"
    **B**. AXI 사양은 "VALID는 READY와 무관하게 올려야 한다"고 명시. Source가 READY를 기다리고 Sink가 VALID를 기다리면 영원히 대기 → 데드락. **A**는 정상 (VALID 올린 후 READY 기다리는 건 OK).

## Q3. (Apply)

AXI4 INCR burst, AxLEN=15, AxSIZE=3'b011 (8 bytes/beat) 일 때 총 전송 바이트 수는?

??? answer "정답 / 해설"
    AxLEN은 N-1 인코딩이므로 beat 수 = 15 + 1 = **16 beats**. 총 = 16 × 8 = **128 bytes**.

## Q4. (Analyze)

Master가 ID=0,1,2 순서로 AR을 발행했는데 Slave가 ID=2,0,1 순서로 R을 응답했다. AXI 사양 위반인가?

??? answer "정답 / 해설"
    **위반 아님**. AXI는 같은 ID 내 in-order, ID 간 OoO 허용. ID=0,1,2가 모두 다르므로 응답 순서가 자유. 단, 만약 Master가 같은 ID로 ID=0, ID=0 두 번 발행했다면 두 응답은 발행 순서대로 와야 함. Scoreboard도 per-ID 큐로 매칭해야 정확.

## Q5. (Evaluate)

다음 중 Modifiable=0 (AxCACHE[1]=0) 트랜잭션에 대해 Interconnect가 **할 수 없는** 동작은?

- [ ] A. 그대로 통과시키기
- [ ] B. Slave 측에서 응답 받기
- [ ] C. 두 개의 작은 트랜잭션으로 분할하기
- [ ] D. 캐시 hit 시 응답하기

??? answer "정답 / 해설"
    **C**. Modifiable=0이면 Interconnect가 분할/병합/재정렬 불가. Device 메모리 영역(레지스터)에 필수 — 같은 주소에 두 번 access를 한 번으로 합치면 hardware register의 W1C 등 동작이 깨짐.
