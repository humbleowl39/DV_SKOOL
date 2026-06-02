---
title: "Quiz — Module 01: TCP/IP & TOE Concept"
---

[← Module 01 본문으로 돌아가기](../../01_tcp_ip_and_toe_concept/)

---

## Q1. (Remember)

Partial offload와 Full offload의 차이는?

<details>
<summary>정답 / 해설</summary>

- **Partial**: checksum, TSO/LRO 등 패킷별 단순 작업만 HW에서. State machine은 SW.
- **Full**: TCP state machine 전체 HW. Connection 관리, retransmission, congestion control 모두.

Partial offload는 패킷 하나를 처리하는 데 필요한 계산만 HW로 넘기며, connection이 어느 state에 있는지는 OS 커널이 계속 관리한다. Full offload는 한 발 더 나아가 SYN 수신부터 TIME_WAIT 만료까지 TCP state machine 전체를 HW가 자율적으로 처리하므로 host CPU가 완전히 해방된다. 결과적으로 Partial은 구현이 단순하고 OS 호환성이 높은 반면, Full은 CPU 절감이 극대화되지만 HW 복잡도와 디버깅 비용이 크게 올라간다.

</details>
## Q2. (Understand)

100GbE에서 TOE 없이 host CPU만으로 처리하기 어려운 이유는?

<details>
<summary>정답 / 해설</summary>

100GbE = ~12.5 GB/s = ~1.5M packets/sec (1500B). Per packet CPU cycle 한도 = ~1000 cycle (3GHz core 기준). TCP/IP 처리는 5000+ cycle 필요 → CPU 1 core가 1.5M pps × 5000 cycle = 7.5 Gcycles/sec → 2.5 cores 필요. 멀티 connection scale에서 CPU 폭증.

핵심은 line-rate에서 패킷 도달 간격이 ~670 ns인데 TCP/IP 처리 한 번에 ~1.7 µs가 필요하다는 불균형이다. CPU 클럭을 높이는 것만으로는 해결되지 않는 이유는 메모리 접근·캐시 miss·인터럽트 오버헤드가 함께 증가하기 때문이다. TOE는 이 처리를 전용 HW 파이프라인으로 넘겨 CPU를 사용자 애플리케이션에 돌려준다.

</details>
## Q3. (Apply)

데이터센터에서 TOE를 가장 적극적으로 활용하는 워크로드는?

<details>
<summary>정답 / 해설</summary>

- **HPC + AI training**: GPU 간 RDMA (RoCE) 통신
- **분산 storage**: NVMe over Fabrics
- **Hyperscale services**: AWS Nitro, Azure SmartNIC — host CPU를 사용자 워크로드에 전적으로
- **Real-time financial trading**: low-latency

TOE 효과가 극대화되는 공통점은 대역폭이 극도로 높거나, 지연이 극도로 낮아야 하거나, host CPU가 TCP/IP 대신 다른 중요한 작업을 해야 하는 세 가지 조건이다. AI training 클러스터에서는 수천 개 GPU가 동시에 그래디언트를 교환하므로 CPU가 병목이 되어서는 안 되고, NVMe-oF 스토리지는 디스크 I/O 경로에서 마이크로초 단위 지연이 쌓여 성능이 뚝 떨어진다. 반면 단순한 웹 서버처럼 연결 수가 적고 CPU 여유가 있는 환경에서는 TOE 도입 효과가 미미하다.

</details>
## Q4. (Analyze)

iWARP와 RoCE의 차이와 trade-off는?

<details>
<summary>정답 / 해설</summary>

- **iWARP**: RDMA over TCP/IP — 일반 IP 네트워크 위에서 동작. TCP의 reliability 활용. 단점: TCP overhead.
- **RoCE**: RDMA over Converged Ethernet — UDP/IP 또는 raw Ethernet. 낮은 latency, 높은 BW. 단점: lossless network 필요 (PFC).

iWARP의 핵심 설계 의도는 "기존 TCP/IP 인프라를 그대로 재사용하면서 RDMA의 zero-copy 이점을 취하자"이다. TCP의 재전송·혼잡제어를 그대로 물려받기 때문에 패킷 손실이 있는 일반 IP 망에서도 동작하지만, TCP 처리 오버헤드가 붙는다. RoCE는 반대로 오버헤드 제거를 최우선으로 하여 Ethernet frame 위에 바로 RDMA verb를 올리므로 지연이 매우 낮다. 대신 패킷 하나라도 drop되면 재전송 메커니즘이 없어 큰 성능 저하가 생기기 때문에, Priority Flow Control로 switch에서 무손실을 보장하는 전용 lossless 패브릭이 필요하다.

</details>
## Q5. (Evaluate)

TOE를 도입하지 **않을** 합당한 이유는?

<details>
<summary>정답 / 해설</summary>

1. **HW 복잡도 → 검증 비용**
2. **Linux kernel 호환성**: TOE는 OS의 TCP stack을 우회 → kernel update 호환성 깨질 수 있음. 그래서 Linux 메인라인은 partial offload만.
3. **Debugging 어려움**: HW state machine 내부 가시성 ↓
4. **Low-volume / non-critical**: 낮은 BW 환경에서는 CPU로 충분.

TOE 도입을 피해야 하는 가장 강력한 근거는 호환성과 관측 가능성이다. Linux 커널은 TCP state machine을 직접 관리한다는 전제로 설계되어 있어, TOE가 이 역할을 가져가면 커널 버전 업그레이드마다 드라이버 재검증이 필요하다. 실제로 Linux 메인라인 커뮤니티가 Full TOE를 거부한 이유가 바로 이 점이다. 또한 HW state machine 내부를 JTAG이나 로그 없이는 볼 수 없으므로, 프로덕션에서 문제가 생겼을 때 원인 파악이 소프트웨어 스택보다 훨씬 어렵다.

</details>
