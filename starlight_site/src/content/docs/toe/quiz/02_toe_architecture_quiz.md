---
title: "Quiz — Module 02: TOE Architecture"
---

[← Module 02 본문으로 돌아가기](../../02_toe_architecture/)

---

## Q1. (Remember)

TOE Connection Table의 key는?

<details>
<summary>정답 / 해설</summary>

**4-tuple**: source IP + source port + destination IP + destination port. 또는 이 4 필드의 hash.

Connection Table은 이 4-tuple로 특정 TCP 연결을 전 세계적으로 유일하게 식별한다. 같은 목적지 서버에 두 클라이언트가 동시에 접속해도 source port가 다르면 서로 다른 행(entry)으로 분리된다. HW에서는 이 4개 필드를 직접 비교하는 대신 해시값을 먼저 계산해 테이블 인덱스로 쓰고, 충돌(collision) 시 체이닝으로 구분하는 방식이 일반적이다.

</details>
## Q2. (Understand)

TX/RX path를 분리하는 이유는?

<details>
<summary>정답 / 해설</summary>

Full-duplex 동작 + 독립 pipeline → 한 방향 stall이 다른 방향에 영향 없음. 100Gbps 양방향 동시 처리 위해 필수.

Ethernet은 원래 full-duplex이므로 TX와 RX는 동시에, 그리고 독립적으로 진행된다. 만약 두 경로가 하나의 파이프라인을 공유한다면 RX의 재조립 버퍼가 차거나 TX의 혼잡 제어가 back-pressure를 걸 때 반대 방향 트래픽도 함께 멈춰 버린다. 분리된 파이프라인은 이 결합을 끊어 각 방향이 자신의 스케줄에 따라 독립적으로 처리되도록 보장하며, 이는 100 Gbps 양방향 동시 달성의 선결 조건이다.

</details>
## Q3. (Apply)

TOE가 1M concurrent connection을 지원할 때, 어떻게 메모리 hierarchy를 구성?

<details>
<summary>정답 / 해설</summary>

- **Active connection** (수천): on-chip SRAM (1-cycle access)
- **Idle connection** (수십만~수백만): off-chip DRAM (latency 큼)
- **LRU eviction**: SRAM에서 idle된 connection은 DRAM으로 이동
- **Hash-based lookup**: 4-tuple hash → SRAM lookup, miss면 DRAM fetch

1M connection을 모두 SRAM에 올리는 것은 칩 면적 비용이 너무 크므로 현실적이지 않다. 핵심 통찰은 어느 시점이든 실제로 패킷을 교환하는 "활성" 연결은 전체의 극히 일부라는 점이다. 그래서 최근 접근된 수천 개만 SRAM 캐시에 유지하고 나머지는 DRAM에 두면 평균 look-up 지연을 낮게 유지할 수 있다. DRAM fetch가 발생하면 수십~수백 ns의 지연이 생기지만, 이 연결이 오랫동안 패킷을 보내지 않았다면 그 지연은 허용 가능하다.

</details>
## Q4. (Analyze)

Stateless offload (TSO/LRO)와 stateful offload의 검증 난이도 차이는?

<details>
<summary>정답 / 해설</summary>

- **Stateless**: 패킷 단위 transformation. 입력 → 출력 단순 mapping. 검증 비교적 쉬움.
- **Stateful**: state machine, retransmission timer, ordering buffer 등 시간/순서 의존. 검증이 시뮬 시간 + corner case 폭발.

Stateless offload는 각 패킷이 독립적이어서 "입력 패킷을 주면 출력 패킷이 나온다"는 단순 변환 모델로 검증할 수 있다. 이전 패킷이 어떻게 처리됐는지 기억할 필요가 없으므로 reference model 작성도 쉽다. 반면 Stateful offload는 과거 패킷 이력, 타이머 만료, 윈도우 크기 변화, 재전송 여부 등이 모두 얽혀 있어 같은 패킷이 와도 이전 상태에 따라 다르게 처리된다. 이 때문에 state × event 조합이 폭발적으로 늘어나고, 특히 타이머 기반 동작(RTO)은 시뮬레이션 시간이 크게 길어진다.

</details>
## Q5. (Evaluate)

다음 중 TOE의 silent corruption 위험이 가장 큰 시나리오는?

- [ ] A. Connection table SRAM bit flip
- [ ] B. Packet drop count overflow
- [ ] C. RTO 5% 더 늦게
- [ ] D. RSS hash distribution 균등하지 않음

<details>
<summary>정답 / 해설</summary>

**A**. SRAM bit flip이 connection state field에 발생하면 잘못된 state로 transition → 이미 close된 connection이 다시 ESTABLISHED라고 판단 등 → 데이터 corruption 가능. ECC가 없으면 catch 불가. C/D는 성능, B는 logging.

SRAM bit flip이 위험한 이유는 오류가 발생했다는 신호 자체가 없기 때문이다. ECC 없이 connection state 필드의 비트 하나가 뒤집히면 TOE는 잘못된 state를 완전히 정상인 것으로 여기고 잘못된 패킷을 생성하거나 수신 데이터를 엉뚱한 연결로 라우팅한다. 반면 B(카운터 오버플로)는 통계가 잘못될 뿐 데이터 흐름은 멀쩡하고, C(RTO 지연)와 D(RSS 불균등)는 성능 문제이지 데이터 무결성 문제가 아니므로 silent corruption으로 분류되지 않는다.

</details>
