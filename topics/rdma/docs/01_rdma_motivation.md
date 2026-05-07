# Module 01 — RDMA 동기와 핵심 모델

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Explain** 왜 RDMA 가 만들어졌는지 — TCP/IP 의 한계, kernel 경유 비용 — 을 설명할 수 있다.
    - **Distinguish** "DMA" 와 "RDMA" 의 차이를 단어 수준이 아니라 데이터 흐름 관점에서 구분할 수 있다.
    - **Compare** RDMA 의 세 가지 변형 — InfiniBand, iWARP, RoCEv1/v2 — 의 계보와 사용 영역을 비교한다.
    - **Identify** Verbs API 의 핵심 객체 (PD, MR, QP, CQ, WQE) 와 각자의 역할을 식별한다.

!!! info "사전 지식"
    - TCP/IP 송수신 흐름 (sk_buff, copy_to/from_user, NIC interrupt)
    - DMA, PCIe 의 memory-mapped IO

## 왜 이 모듈이 중요한가

**RDMA 는 "네트워크" 라기보다 "원격 메모리" 모델**입니다. TCP/IP 는 "메시지를 OS 에 맡겨서 보내고, OS 가 받아서 user 한테 다시 복사" 하는 모델인 반면, RDMA 는 "원격 노드의 메모리 주소를 알고 직접 읽고/쓴다" 라는 가정에서 출발합니다. 모든 RDMA 검증/설계 결정은 이 가정에서 파생되므로, 다른 모듈로 넘어가기 전에 이 가정의 의미를 정확히 잡아야 합니다.

!!! tip "💡 이해를 위한 비유"
    **RDMA** ≈ **공유 우편함 (mailbox) + DMA**

    TCP/IP 는 "택배 보내기" 입니다 — 보내는 쪽이 박스에 넣고(`copy_from_user`), 우체국(kernel/NIC)이 받아 운반하고, 받는 쪽 우체국에서 풀어 다시 옮겨 담아 사용자에게(`copy_to_user`) 줍니다. RDMA 는 "각자 책상 위 메모리 한 영역을 미리 등록해 두고(MR) 그 주소를 상대에게 알려준 다음, 직접 가져다 쓰는 모델" 입니다. 우체국 단계가 없어 latency 와 CPU cycle 이 모두 줄어듭니다.

## 핵심 개념

**RDMA = Remote Direct Memory Access. 송수신 양쪽 NIC (HCA, RNIC) 가 host CPU 를 거치지 않고 원격 노드의 사전 등록된 메모리 영역을 직접 읽고/쓰는 통신 모델. Kernel bypass + Zero-copy + Transport offload 세 축을 동시에 달성.**

!!! danger "❓ 흔한 오해"
    **오해**: "RDMA 는 빠른 TCP" 다.

    **실제**: RDMA 는 transport semantics 가 아예 다릅니다 — TCP 는 byte stream + 양 끝의 user-space socket 이지만, RDMA 는 message + 원격 메모리 주소 (R_Key + virtual address) 모델입니다. RC service 는 신뢰성 있는 message 전달을 보장하지만, 이건 TCP 의 reliability 와 다른 mechanism (ACK/NAK + PSN + retry on HCA) 으로 구현됩니다.

    **왜 헷갈리는가**: "high-performance networking" 이라는 카테고리에 같이 묶이고, 실제로 RoCEv2 는 IP/UDP 위에 올라가기 때문.

---

## 1. TCP/IP 가 가진 세 가지 비용

```
                Application
                    |
                    | (1) copy_from_user  ← CPU cycle
                    v
                 Socket buffer
                    |
                    | (2) Protocol stack (TCP/IP, checksum, retransmit timers)
                    v                      ← CPU cycle + cache pollution
                    NIC
                    |
              ── Network ──
                    |
                    NIC
                    |                      ← Interrupt → ksoftirqd
                    v
                 Socket buffer
                    |
                    | (3) copy_to_user    ← CPU cycle
                    v
                Application
```

| 비용 | 발생 위치 | RDMA 의 해결 |
|------|----------|-------------|
| **(1) Send-side memcpy** | `copy_from_user` | Memory Registration → NIC 가 사용자 메모리 직접 read |
| **(2) Stack processing** | TCP segment, retransmit timer, congestion control 모두 SW | Transport offload → HCA hardware 가 PSN/ACK/NAK 처리 |
| **(3) Recv-side memcpy + interrupt** | `copy_to_user`, IRQ → softirq → 스케줄링 | Zero-copy 직접 DMA, polling completion (선택) |

**결과**: 100Gbps 링크에서 TCP/IP 는 **~10-15 us** RTT, RDMA 는 **~1-3 us** RTT. CPU 사용률은 보통 **5-10× 차이**.

---

## 2. DMA vs RDMA — 한 글자 차이의 의미

!!! note "정의 (ISO 11179 형식)"
    - **DMA**: CPU 의 직접 개입 없이 디바이스가 호스트 메모리를 직접 read/write 하는 메커니즘.
    - **RDMA**: 네트워크의 양 끝에서 DMA 가 동시에 일어나, **원격** 노드의 메모리를 read/write 하는 메커니즘.

```
    Local DMA                   RDMA
   ─────────────────         ─────────────────────────────────
   CPU                       CPU₁                    CPU₂
    │                         │                       │
   memory ←── DMA ── disk     mem₁ ← DMA ─ HCA₁ ↔ HCA₂ ─ DMA → mem₂
                                 (R_Key + VA 가 mem₂ 의 일부 영역을 가리킴)
```

**핵심**: RDMA 는 "원격 노드의 메모리 주소" 를 (1) 사전 등록(Memory Registration) 하고, (2) 그 주소를 보호 키 (R_Key) 와 함께 노출하고, (3) 양 끝의 NIC 가 그 주소를 인식해 DMA 를 수행하는 모델.

---

## 3. RDMA 의 세 가지 변형 — IB / iWARP / RoCE

```
                            ┌──────────── RDMA 패밀리 ─────────────┐
                            │                                       │
   InfiniBand (IB)        iWARP                  RoCE (v1, v2)
   ────────────────       ──────────────────     ──────────────────────────
   IB Link/Net Layer      TCP/IP 위에 RDMA       Ethernet 위에 RDMA
   IB SerDes (1x..12x)    표준 IP 인프라         RoCEv1: Eth L2 직결
                          느림 (TCP overhead)    RoCEv2: IP/UDP(4791)/BTH
   HPC, 전용 Fabric       Long-distance, WAN     데이터센터 표준
   IBTA Vol1 spec         IETF spec              IBTA Annex A16/A17
```

| 항목 | InfiniBand | iWARP | RoCEv1 | RoCEv2 |
|------|-----------|-------|--------|--------|
| L1/L2 | IB SerDes + Link | Ethernet | Ethernet (L2) | Ethernet (L2) |
| L3 | IB Network (GRH) | IP | (없음 — L2 only) | IPv4 / IPv6 |
| L4 | IB Transport (BTH) | TCP + DDP/RDMAP | BTH | UDP(4791) + BTH |
| 라우팅 | IB Subnet Manager | Standard IP routing | 같은 broadcast domain 내 | Standard IP routing |
| 설치 환경 | HPC, AI 클러스터 | 일반 IP 망 | 단일 L2 도메인 | 데이터센터 일반 |
| 성능 | 가장 좋음 (~600ns) | TCP 오버헤드 | IB와 유사 | IB와 거의 동등 |

**오늘 (2026)**: 데이터센터/하이퍼스케일러는 거의 **RoCEv2**, HPC/AI 트레이닝 팜은 여전히 **InfiniBand**, iWARP 는 사실상 레거시.

!!! quote "Spec 인용"
    "RoCEv2 packets share the same Base Transport Header (BTH) and Extended Transport Headers (xTH) used in InfiniBand transport. The IB Network Layer (GRH) is replaced with the IP header." — IBTA, *Annex A17 RoCEv2*, §A17.4

---

## 4. Verbs API — RDMA 의 사용자 인터페이스

```
                    User application
                          │
                          ▼
              ┌────────────────────────┐
              │   libibverbs (Verbs)    │   ← OFED user-space lib
              └────────────────────────┘
                          │
                          ▼ ioctl/uverbs
              ┌────────────────────────┐
              │   ib_uverbs / rdma_cm   │   ← kernel module
              └────────────────────────┘
                          │ MMIO + DMA
                          ▼
                       HCA / RNIC
```

핵심 객체 6 가지:

<div class="parallel-grid">
<div>

**PD (Protection Domain)**
모든 객체의 보호 경계. PD 가 다른 MR/QP 끼리는 cross-access 불가.
</div>
<div>

**MR (Memory Region)**
NIC 가 DMA 가능한 메모리 영역 + access flag (Local Read/Write, Remote Read/Write/Atomic).
</div>
<div>

**QP (Queue Pair)**
Send Queue + Receive Queue. 한 QP 가 한 endpoint. RC/UC/UD/XRC 중 하나의 service type.
</div>
<div>

**CQ (Completion Queue)**
완료 통지 큐. WC (Work Completion) 가 들어옴 — 사용자는 `ibv_poll_cq()` 로 polling.
</div>
<div>

**WQE (Work Queue Element)**
하나의 RDMA operation (SEND/WRITE/READ/ATOMIC) 의 디스크립터. SQ/RQ 에 enqueue.
</div>
<div>

**WC (Work Completion)**
WQE 처리 결과 (status, byte count, opcode, source QP 등). CQ 에서 polling.
</div>
</div>

```c
// 단순화된 예시: 1 KB 를 원격 노드의 buf 에 RDMA WRITE
struct ibv_send_wr wr;
struct ibv_sge sge;

sge.addr   = (uintptr_t)local_buf;
sge.length = 1024;
sge.lkey   = local_mr->lkey;            // 로컬 보호 키

wr.opcode             = IBV_WR_RDMA_WRITE;
wr.sg_list            = &sge;
wr.num_sge            = 1;
wr.wr.rdma.remote_addr = remote_va;     // 원격 등록 주소
wr.wr.rdma.rkey        = remote_rkey;   // 원격 보호 키

ibv_post_send(qp, &wr, &bad_wr);
ibv_poll_cq(cq, 1, &wc);                // 완료 polling
```

---

## 5. RDMA 가 어울리는 워크로드 / 어울리지 않는 워크로드

| 워크로드 | RDMA 적합성 | 이유 |
|---------|------------|------|
| **HPC MPI Allreduce** | ★★★★★ | 작은 latency, 반복 패턴, 동기 |
| **AI training all-to-all** | ★★★★★ | 동일 |
| **분산 KV (Memcached, Redis-like)** | ★★★★ | Small message, 짧은 latency |
| **분산 storage (NVMe-oF)** | ★★★★★ | Block 크기 transfer, kernel bypass 효과 큼 |
| **일반 웹 서비스 (HTTP)** | ★★ | RDMA 의 setup 비용이 connection 짧은 워크로드에 비해 큼 |
| **WAN (대륙간)** | ★ | RDMA reliability 는 LAN/DC 가정 |

---

## 6. RDMA 검증 (DV) 의 출발점

검증자 관점에서 이 모듈의 take-away:

1. **DUT 는 host CPU 를 거치지 않는다** — 그래서 host 메모리 모델, MMU/IOMMU, PCIe BAR mapping 까지 TB 가 시뮬레이트해야 한다.
2. **Connection setup 은 control path, data 는 data path** — RDMA-CM (over TCP) vs RDMA verb 의 차이를 TB 환경에서도 분리.
3. **Protection 위반은 silent corruption 이 아니라 명확한 error event** — R_Key/L_Key 검증 실패 → CQE error → 검증 가능한 신호.
4. **RC service 는 transport reliability 를 hardware 가 보장** — 즉 TB 의 scoreboard 가 PSN, ACK, retry 까지 모델링해야 한다.

---

## 핵심 정리 (Key Takeaways)

- RDMA = kernel bypass + zero-copy + transport offload 세 축의 결합.
- DMA 가 "내 메모리 ↔ 내 디바이스" 라면 RDMA 는 "내 메모리 ↔ 원격 메모리".
- IB / iWARP / RoCE(v1, v2) 는 같은 Verbs API 를 공유하지만 L1-L4 가 다름.
- Verbs 6 객체 (PD/MR/QP/CQ/WQE/WC) 는 이후 모든 모듈의 어휘.
- 검증 관점: host CPU 가 빠지므로 **TB 가 host memory + MMU + PCIe 까지 모델링** 해야 한다.

!!! warning "실무 주의점"
    - "RDMA 빠르다" 는 latency 이지 throughput 이 아니다 — TCP/IP 도 100Gbps 라인레이트는 잘 채운다. 차별점은 **CPU 점유율** 과 **tail latency**.
    - RDMA-CM 은 RDMA 가 아니다 — RDMA-CM 자체는 TCP 위에서 동작하는 "RDMA connection 만들기" 프로토콜. 헷갈리지 말 것.
    - 보안: R_Key 가 노출되면 원격 노드가 임의 메모리에 RDMA WRITE 가능 → MR 의 access flag 와 PD 격리는 spec 가 아닌 구현 책임.

---

## 다음 모듈

→ [Module 02 — InfiniBand 프로토콜 스택](02_ib_protocol_stack.md)
