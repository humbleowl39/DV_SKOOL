# Quiz — Module 13: Background & Industry Research

[← Module 13 본문으로 돌아가기](../13_background_research.md)

---

## Q1. (Remember)

사내 Paper Study 가 다루는 주요 3 축은?

??? answer "정답 / 해설"
    1. AI Training (RDMA + DL) — RDMA 가 training step time 에 미치는 영향, in-network reduction.
    2. MultiPathing — multi-path RDMA 알고리즘, packet spraying 한계.
    3. AI-RNIC 동향 — 산업 백서 / 동향 정리.

## Q2. (Understand)

Falcon · Programmable CC · ECE 가 각각 해결하려는 문제를 한 문장으로 적어라.

??? answer "정답 / 해설"
    - **Falcon (Google)** — RoCEv2 의 *PFC + DCQCN + RC* 스택을 hardware reliable transport 로 통합 추상화.
    - **Programmable CC** — 송신측 CC 알고리즘을 firmware/HW 인터페이스로 swap 가능하게 만들어 deployment 별 algorithm 선택을 단순화.
    - **ECE** — RDMA-CM 핸드셰이크에서 양 단의 확장 기능 (MPE, atomic write, multipath 등) 을 협상.

## Q3. (Apply)

논문 *"Challenging the Need for Packet Spraying in Large-Scale Distributed Training"* 의 결론이 사내 검증 시나리오 설계에 주는 시사점은?

??? answer "정답 / 해설"
    Packet spraying 이 **항상 이득은 아니라**는 결론. 사내 검증에서는:
    - AR (Adaptive Routing) 시나리오를 *기본* 으로 두지 않고 **별도 시나리오 군** 으로 분리.
    - Spraying 활성/비활성 두 모드의 throughput 과 OOO 비율을 비교 검증.

## Q4. (Analyze)

Multi-path RDMA 가 IB / RC 의 strict in-order 가정에 미치는 영향을 분석하고, 사내 IP 가 이를 어떻게 처리하는지 답하라.

??? answer "정답 / 해설"
    Multi-path 는 path 간 latency 차이로 같은 QP 의 packet 이 OOO 도착 가능 → 표준 Go-Back-N 하에서 NAK 폭주 / throughput 붕괴.
    사내 IP 처리:
    - `m_sack_info` (152-bit) 로 selective ACK 비트맵 노출.
    - `cc_module` 이 multi-path 신호 (예: per-path RTT) 입력으로 받음.
    - 검증은 *AR mode* 라는 별도 시나리오 군으로 분리해 strict-order assertion 을 비활성.

## Q5. (Evaluate)

"산업이 그렇게 하니까" 가 spec 우선의 이유가 될 수 있는가? 사내 검증 자산의 truth 는 무엇인가?

??? answer "정답 / 해설"
    아니오. 검증의 1차 truth 는 **spec (IB / RoCEv2 / UEC) + 사내 design 결정**. 산업 트렌드는 *우선순위 결정* 과 *향후 방향 정렬* 에 사용하되, 검증 단정의 근거가 될 수 없다.
    Paper / 경쟁사 자료가 검증에 들어올 때는 항상 **사내 IP capability 와의 매핑 표** 를 먼저 만든 뒤 시나리오로 옮긴다.
