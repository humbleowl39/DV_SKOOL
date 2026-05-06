# Quiz — Module 02: TOE Architecture

[← Module 02 본문으로 돌아가기](../02_toe_architecture.md)

---

## Q1. (Remember)

TOE Connection Table의 key는?

??? answer "정답 / 해설"
    **4-tuple**: source IP + source port + destination IP + destination port. 또는 이 4 필드의 hash.

## Q2. (Understand)

TX/RX path를 분리하는 이유는?

??? answer "정답 / 해설"
    Full-duplex 동작 + 독립 pipeline → 한 방향 stall이 다른 방향에 영향 없음. 100Gbps 양방향 동시 처리 위해 필수.

## Q3. (Apply)

TOE가 1M concurrent connection을 지원할 때, 어떻게 메모리 hierarchy를 구성?

??? answer "정답 / 해설"
    - **Active connection** (수천): on-chip SRAM (1-cycle access)
    - **Idle connection** (수십만~수백만): off-chip DRAM (latency 큼)
    - **LRU eviction**: SRAM에서 idle된 connection은 DRAM으로 이동
    - **Hash-based lookup**: 4-tuple hash → SRAM lookup, miss면 DRAM fetch

## Q4. (Analyze)

Stateless offload (TSO/LRO)와 stateful offload의 검증 난이도 차이는?

??? answer "정답 / 해설"
    - **Stateless**: 패킷 단위 transformation. 입력 → 출력 단순 mapping. 검증 비교적 쉬움.
    - **Stateful**: state machine, retransmission timer, ordering buffer 등 시간/순서 의존. 검증이 시뮬 시간 + corner case 폭발.

## Q5. (Evaluate)

다음 중 TOE의 silent corruption 위험이 가장 큰 시나리오는?

- [ ] A. Connection table SRAM bit flip
- [ ] B. Packet drop count overflow
- [ ] C. RTO 5% 더 늦게
- [ ] D. RSS hash distribution 균등하지 않음

??? answer "정답 / 해설"
    **A**. SRAM bit flip이 connection state field에 발생하면 잘못된 state로 transition → 이미 close된 connection이 다시 ESTABLISHED라고 판단 등 → 데이터 corruption 가능. ECC가 없으면 catch 불가. C/D는 성능, B는 logging.
