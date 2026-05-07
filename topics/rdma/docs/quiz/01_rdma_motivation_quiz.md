# Quiz — Module 01: RDMA 동기와 핵심 모델

[← Module 01 본문으로 돌아가기](../01_rdma_motivation.md)

---

## Q1. (Remember)

RDMA 의 세 가지 핵심 성능 축은?

??? answer "정답 / 해설"
    1. **Kernel bypass** — OS / socket layer 거치지 않음
    2. **Zero-copy** — `copy_from_user` / `copy_to_user` 없음
    3. **Transport offload** — PSN / ACK / NAK / retry 를 HW (HCA) 가 처리

## Q2. (Understand)

DMA 와 RDMA 의 한 줄 차이는?

??? answer "정답 / 해설"
    DMA = "내 메모리 ↔ 내 디바이스" (CPU 우회).
    RDMA = "내 메모리 ↔ **원격** 메모리" (양 끝의 NIC 가 동시에 DMA 수행, 사전 등록된 R_Key + IOVA 로 원격 영역 식별).

## Q3. (Apply)

다음 워크로드 중 RDMA 가 가장 큰 이득을 주는 것은? (선택)

a) WAN HTTP 요청
b) AI training all-to-all
c) 단일 노드 배치 분석
d) 세션 짧은 일반 웹 트래픽

??? answer "정답 / 해설"
    **b**. 작은 message + 반복 + 짧은 latency 가 RDMA 의 sweet spot. WAN(a) 은 RDMA reliability 가 LAN/DC 가정이라 부적합, 단일 노드(c) 는 RDMA 자체 의미 없음, 짧은 세션(d) 은 connection setup 비용 대비 이득 적음.

## Q4. (Analyze)

"RDMA 빠르다" 가 정확히 무엇을 의미하는지 두 축으로 분석하라.

??? answer "정답 / 해설"
    - **Latency**: TCP/IP ~ 10-15 us → RDMA ~ 1-3 us (kernel bypass 효과 큼)
    - **CPU 사용률**: 같은 throughput 에서 5-10× 적은 CPU cycle (zero-copy + offload)

    Throughput 만 보면 100Gbps 라인레이트는 TCP 도 채울 수 있음 — 차별점은 **tail latency 와 CPU efficiency**.

## Q5. (Evaluate)

Verbs 객체 PD / MR / QP / CQ / WQE / WC 중에서 "보호 경계" 역할을 하는 것은? 그 결정이 왜 다른 객체가 아니어야 하는가?

??? answer "정답 / 해설"
    **PD (Protection Domain)**.

    - MR 은 영역 자체 + access flag, key 의 묶음.
    - QP 는 endpoint.
    - 두 객체는 PD 를 통해 **그룹화** 되어, 다른 PD 의 MR 을 다른 PD 의 QP 가 access 하면 거부.
    - PD 가 없으면 모든 MR 이 모든 QP 에 노출되어 multi-tenant 환경에서 isolation 불가.

    → "보호 경계" 와 "객체 자체" 의 책임 분리가 깔끔한 설계.
