# Quiz — Module 01: TCP/IP & TOE Concept

[← Module 01 본문으로 돌아가기](../01_tcp_ip_and_toe_concept.md)

---

## Q1. (Remember)

Partial offload와 Full offload의 차이는?

??? answer "정답 / 해설"
    - **Partial**: checksum, TSO/LRO 등 패킷별 단순 작업만 HW에서. State machine은 SW.
    - **Full**: TCP state machine 전체 HW. Connection 관리, retransmission, congestion control 모두.

## Q2. (Understand)

100GbE에서 TOE 없이 host CPU만으로 처리하기 어려운 이유는?

??? answer "정답 / 해설"
    100GbE = ~12.5 GB/s = ~1.5M packets/sec (1500B). Per packet CPU cycle 한도 = ~1000 cycle (3GHz core 기준). TCP/IP 처리는 5000+ cycle 필요 → CPU 1 core가 1.5M pps × 5000 cycle = 7.5 Gcycles/sec → 2.5 cores 필요. 멀티 connection scale에서 CPU 폭증.

## Q3. (Apply)

데이터센터에서 TOE를 가장 적극적으로 활용하는 워크로드는?

??? answer "정답 / 해설"
    - **HPC + AI training**: GPU 간 RDMA (RoCE) 통신
    - **분산 storage**: NVMe over Fabrics
    - **Hyperscale services**: AWS Nitro, Azure SmartNIC — host CPU를 사용자 워크로드에 전적으로
    - **Real-time financial trading**: low-latency

## Q4. (Analyze)

iWARP와 RoCE의 차이와 trade-off는?

??? answer "정답 / 해설"
    - **iWARP**: RDMA over TCP/IP — 일반 IP 네트워크 위에서 동작. TCP의 reliability 활용. 단점: TCP overhead.
    - **RoCE**: RDMA over Converged Ethernet — UDP/IP 또는 raw Ethernet. 낮은 latency, 높은 BW. 단점: lossless network 필요 (PFC).

## Q5. (Evaluate)

TOE를 도입하지 **않을** 합당한 이유는?

??? answer "정답 / 해설"
    1. **HW 복잡도 → 검증 비용**
    2. **Linux kernel 호환성**: TOE는 OS의 TCP stack을 우회 → kernel update 호환성 깨질 수 있음. 그래서 Linux 메인라인은 partial offload만.
    3. **Debugging 어려움**: HW state machine 내부 가시성 ↓
    4. **Low-volume / non-critical**: 낮은 BW 환경에서는 CPU로 충분.
