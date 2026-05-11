# Module 01 — RDMA 동기와 핵심 모델

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">⚡</span>
    <span class="chapter-back-text">RDMA</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 01</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-1-kb-rdma-write-를-step-by-step-으로-따라가기">3. 작은 예 — 1 KB WRITE 따라가기</a>
  <a class="page-toc-link" href="#4-일반화-세-가지-축과-6-객체">4. 일반화 — 세 축 + 6 객체</a>
  <a class="page-toc-link" href="#5-디테일-스택-변형-api-워크로드">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Explain** TCP/IP 가 가진 세 가지 비용 (memcpy / stack / interrupt) 을 RDMA 가 어떻게 제거하는지 설명할 수 있다.
    - **Distinguish** "DMA" 와 "RDMA" 를 단어가 아니라 **데이터 흐름** 관점에서 구분할 수 있다.
    - **Trace** 1 KB RDMA WRITE 한 번을 8단계로 끝까지 추적할 수 있다.
    - **Identify** Verbs 6 객체 (PD, MR, QP, CQ, WQE, WC) 의 역할과 협력 관계를 식별한다.
    - **Compare** IB / iWARP / RoCEv1 / RoCEv2 의 계보와 사용 영역을 비교한다.

!!! info "사전 지식"
    - TCP/IP 송수신 흐름 (sk_buff, copy_to/from_user, NIC interrupt)
    - DMA, PCIe 의 memory-mapped IO

---

## 1. Why care? — 이 모듈이 왜 필요한가

이후 모든 RDMA 모듈은 한 가정에서 출발합니다 — **"네트워크의 양 끝 NIC 가 host CPU 를 거치지 않고 상대 노드의 메모리를 직접 읽고/쓴다"**. IB 패킷 헤더가 왜 그렇게 생겼는지, RC service 가 왜 PSN/ACK 를 hardware 로 처리하는지, DV TB 가 왜 host memory 와 MMU 까지 모델링해야 하는지 — 전부 이 한 가정의 파생입니다.

이 모듈을 건너뛰면 이후의 모든 spec/패킷/검증 결정이 "그냥 외워야 하는 규칙" 으로 보입니다. 반대로 이 가정을 정확히 잡고 나면, 디테일을 만날 때마다 **"아, 이게 zero-copy 를 위한 거구나"** 처럼 _이유_ 가 보입니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **TCP/IP** = 택배 회사. 박스에 담아(`copy_from_user`) 우체국(kernel/NIC)에 맡기고, 받는 쪽 우체국이 풀어서 다시 옮겨담아(`copy_to_user`) 사용자에게 줌.<br>
    **RDMA** = 두 사무실이 _같은 캐비넷에 한 서랍씩 공유_ 하는 모델. 미리 "여기가 네 서랍이야" 라고 등록(MR)해 두면 상대가 우체국 거치지 않고 직접 쓰고 빠짐.

### 한 장 그림 — TCP path vs RDMA path

```
              TCP/IP (3 copies + interrupt)              RDMA (0 copies, no IRQ)
              ─────────────────────────────              ────────────────────────
   App ──▶ user buf                                App ──▶ user buf (= MR)
            │ copy_from_user  ●                              │
            ▼                                                ▼
         socket buf                                      (등록만 해 두면 끝)
            │ TCP/IP stack    ●                              │
            ▼                                                ▼ MMIO doorbell
           NIC ──▶ wire ──▶ NIC                            HCA ─DMA→ wire
                                                            │         │
                                                            │         ▼
                                                          DMA       HCA
                                                            ▼         │
                                                          peer MR ◀──┘ (rkey 검증 후 직접 write)
            ▲                                                         (peer CPU 안 깨움)
            │ copy_to_user    ●
         socket buf
            │ ksoftirqd       ●
            ▼
           App
       ● = CPU cycle / cache pollution
```

세 개의 빨간 원이 RDMA 에서는 모두 사라지고, 대신 **HCA hardware** 가 PSN, ACK, 재전송, 무결성 검사를 처리합니다.

### 왜 이렇게 설계됐는가 — Design rationale

100 Gbps 라인레이트에서는 패킷 1개 도착 간격이 **~80 ns** 입니다. CPU 가 인터럽트 받고 컨텍스트 전환만 해도 수백 ns. 즉 **CPU 가 끼는 한 라인레이트를 못 채웁니다**. 그래서 RDMA 의 세 축 — **kernel bypass + zero-copy + transport offload** — 는 동시에 만족돼야 의미가 있고, 셋 중 하나라도 빠지면 전체가 의미를 잃습니다. 이 세 축이 곧 IB/RoCE 패킷 포맷, Verbs API 디자인, 검증 환경의 구조를 결정합니다.

---

## 3. 작은 예 — 1 KB RDMA WRITE 를 step by step 으로 따라가기

가장 단순한 시나리오. 노드 **A** 가 노드 **B** 의 메모리에 **1 KB** 를 RDMA WRITE 합니다.

```
   ┌─── Node A ───┐                                         ┌─── Node B ───┐
   │              │                                         │              │
   │  app + lbuf  │                                         │  app + rbuf  │
   │       │      │                                         │       │      │
   │       ▼      │  ②  rbuf 의 (remote_va, rkey) 전달      │       │      │
   │  HCA_A ◀═════│════════ out-of-band (RDMA-CM/TCP) ══════│════▶ HCA_B   │
   │       │      │                                         │       │      │
   │       │ ③ post_send WQE                                │       │      │
   │       ▼ ④ DMA read lbuf                                │       │      │
   │      pkt ════════════════ wire ════════════════════════│════▶ pkt     │
   │              │                       BTH+RETH+payload  │       │ ⑤    │
   │              │                                         │       ▼      │
   │              │                                         │  rkey verify │
   │              │                                         │       │ ⑥    │
   │              │                                         │       ▼ DMA write
   │              │                                         │     rbuf     │
   │              │            ⑦  ACK packet               │       │      │
   │  HCA_A ◀═════│═════════════════════════════════════════│═══════┘      │
   │       │ ⑧ CQE 생성                                     │              │
   │   poll_cq    │                                         │  (CPU 안 깨움)│
   └──────────────┘                                         └──────────────┘
```

| Step | 누가 | 무엇을 | 의미 |
|---|---|---|---|
| ① | B 의 app | `ibv_reg_mr(rbuf, len, R/W)` 로 rbuf 등록 | NIC 가 DMA 가능하게 핀(pinning) + rkey 발급 |
| ② | B → A | (remote_va, rkey) 를 out-of-band 로 알려줌 | RDMA 자체는 채널이 없음 — 보통 RDMA-CM(over TCP) 또는 sockets |
| ③ | A 의 app | SQ 에 WRITE WQE post (`ibv_post_send`) | 단순히 도어벨 MMIO 1번 — kernel 안 거침 |
| ④ | HCA_A | lbuf 에서 1 KB DMA read | A 의 CPU 는 이미 다른 일 하고 있음 (zero-copy) |
| ⑤ | HCA_B | rkey 와 length 검증 | 실패 시 NAK → CQE error |
| ⑥ | HCA_B | rbuf 에 1 KB DMA write | B 의 **CPU 한 번도 안 깨움** ⭐ |
| ⑦ | HCA_B → HCA_A | ACK 패킷 송신 | RC service 의 reliability — hardware 가 보장 |
| ⑧ | HCA_A | CQ 에 WC 삽입 | A 의 app 이 `ibv_poll_cq` 로 회수 |

```c
// Step ③ 의 실제 코드 (A 측). 이 한 번의 post_send 가 ④~⑧ 을 트리거.
struct ibv_send_wr wr = {
    .opcode             = IBV_WR_RDMA_WRITE,
    .sg_list            = &(struct ibv_sge){
        .addr   = (uintptr_t)lbuf,    // 로컬 source
        .length = 1024,
        .lkey   = lmr->lkey,          // 로컬 보호 키
    },
    .num_sge = 1,
    .wr.rdma.remote_addr = remote_va, // ② 에서 받음
    .wr.rdma.rkey        = remote_rkey,
};
ibv_post_send(qp, &wr, &bad_wr);
ibv_poll_cq(cq, 1, &wc);              // ⑧ 까지 끝나면 status=SUCCESS
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) 양 노드의 CPU 가 거의 안 쓰임** — A 는 post_send + poll_cq, B 는 0회. 이게 RDMA 의 본질. <br>
    **(2) "원격 메모리 주소" 가 미리 약속돼야 한다** — RDMA 는 _주소를 알고 직접 쓰는_ 모델. 그래서 connection setup (control path) 과 data 전송 (data path) 이 분리됩니다.

---

## 4. 일반화 — 세 가지 축과 6 객체

### 4.1 RDMA 의 세 축

| 축 | 무엇을 제거 | TCP/IP 와의 차이 |
|---|---|---|
| **Kernel bypass** | Syscall + context switch | post_send 는 user-space MMIO doorbell |
| **Zero-copy** | `copy_from/to_user` | NIC 가 user buffer 에서 직접 DMA (MR pinning 으로 가능) |
| **Transport offload** | TCP stack (PSN, ACK, retransmit, congestion) 의 SW 처리 | HCA hardware 가 RC PSN/ACK/NAK/retry 처리 |

### 4.2 DMA vs RDMA — 한 글자 차이의 의미

!!! note "정의 (ISO 11179)"
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

핵심: RDMA 는 "원격 노드의 메모리 주소" 를 (1) 사전 등록(Memory Registration), (2) 보호 키 (R_Key) 와 함께 노출, (3) 양 끝의 NIC 가 그 주소를 인식해 DMA 를 수행.

### 4.3 Verbs 6 객체 — 협력 관계

```
       PD (Protection Domain) ──── 같은 PD 안에서만 cross-access 허용
        │
        ├── MR (Memory Region) ── DMA 가능 영역 + access flag (lkey/rkey)
        │
        └── QP (Queue Pair) ─────┬── SQ (Send Queue)  ◀── post_send (WQE)
                                 ├── RQ (Recv Queue)  ◀── post_recv (WQE)
                                 └── service type: RC / UC / UD / XRC
                  │
                  └── 완료는 ▶ CQ (Completion Queue) ◀── poll_cq → WC (Work Completion)
```

<div class="parallel-grid">
<div>

**PD (Protection Domain)**<br>
모든 객체의 보호 경계. PD 가 다른 MR/QP 끼리는 cross-access 불가.
</div>
<div>

**MR (Memory Region)**<br>
NIC 가 DMA 가능한 메모리 영역 + access flag (Local Read/Write, Remote Read/Write/Atomic). lkey/rkey 발급.
</div>
<div>

**QP (Queue Pair)**<br>
Send Queue + Receive Queue. 한 QP 가 한 endpoint. RC/UC/UD/XRC 중 한 service type.
</div>
<div>

**CQ (Completion Queue)**<br>
완료 통지 큐. WC 가 들어옴 — `ibv_poll_cq` 로 polling (또는 event 모드).
</div>
<div>

**WQE (Work Queue Element)**<br>
한 RDMA operation (SEND/WRITE/READ/ATOMIC) 의 디스크립터. SQ/RQ 에 enqueue.
</div>
<div>

**WC (Work Completion)**<br>
WQE 처리 결과 (status, byte count, opcode, source QP 등). CQ 에서 polling.
</div>
</div>

이후 모든 모듈에서 이 6개가 등장합니다. 새 약어가 나오면 일단 이 6개 중 하나의 변형/속성인지 확인하세요.

---

## 5. 디테일 — 스택, 변형, API, 워크로드

### 5.1 TCP/IP 가 가진 세 가지 비용 (RDMA 가 제거하는 것)

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

**결과**: 100 Gbps 링크에서 TCP/IP 는 **~10–15 µs** RTT, RDMA 는 **~1–3 µs** RTT. CPU 사용률은 보통 **5–10× 차이**.

### 5.2 RDMA 의 세 가지 변형 — IB / iWARP / RoCE

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
| 성능 | 가장 좋음 (~600 ns) | TCP 오버헤드 | IB와 유사 | IB와 거의 동등 |

**오늘 (2026)**: 데이터센터/하이퍼스케일러는 거의 **RoCEv2**, HPC/AI 트레이닝 팜은 여전히 **InfiniBand**, iWARP 는 사실상 레거시.

!!! quote "Spec 인용"
    "RoCEv2 packets share the same Base Transport Header (BTH) and Extended Transport Headers (xTH) used in InfiniBand transport. The IB Network Layer (GRH) is replaced with the IP header." — IBTA, *Annex A17 RoCEv2*, §A17.4

### 5.3 Verbs API — Control path vs Data path

```
                    User application
                          │
                          ▼
              ┌────────────────────────┐
              │   libibverbs (Verbs)    │   ← OFED user-space lib
              └────────────────────────┘
                          │
                          ▼ ioctl/uverbs (control only)
              ┌────────────────────────┐
              │   ib_uverbs / rdma_cm   │   ← kernel module
              └────────────────────────┘
                          │ MMIO + DMA
                          ▼
                       HCA / RNIC
```

!!! note "Internal (Confluence: RDMA Verbs (basic), id=32178388)"
    실제 host 측 RDMA 스택은 **user-level driver** 와 **kernel-level driver** 두 갈래가 모두 있다.
    user-level driver 는 `libibverbs` 가 RNIC 의 BAR 영역과 직접 통신해 syscall context-switch 를 회피하고, completion 을 polling 방식으로 가져온다 — datapath verbs (`ibv_post_send`, `ibv_poll_cq`) 가 여기에 속한다.
    반면 kernel-level driver 는 자원 할당·매핑·MR pinning 처럼 **권한 / 안전성 검증** 이 필요한 control path verbs (`ibv_open_device`, `ibv_alloc_pd`, `ibv_reg_mr`, `ibv_create_qp`) 를 처리한다.
    두 드라이버는 **기능 차이가 없고**, 같은 verb 가 user-level 에서는 `ibv_*`, kernel-level 에서는 `ib_*` 로 명명된다.
    검증 환경에서도 control path 와 datapath 를 분리하는 이 모델을 그대로 따른다 — TB 의 sequence 는 verb-level 로 작성하고, agent 가 BAR write / mailbox 으로 변환한다.

| Path | 대표 Verb | Kernel 개입 | TB 모델링 |
|------|----------|------------|----------|
| Control | `ibv_open_device` `ibv_alloc_pd` `ibv_reg_mr` `ibv_create_qp` | O (자원·권한) | 초기화 sequence + RAL |
| Data | `ibv_post_send` `ibv_post_recv` `ibv_poll_cq` | X (kernel bypass) | scoreboard + agent |

### 5.4 어울리는 워크로드 / 어울리지 않는 워크로드

| 워크로드 | RDMA 적합성 | 이유 |
|---------|------------|------|
| **HPC MPI Allreduce** | ★★★★★ | 작은 latency, 반복 패턴, 동기 |
| **AI training all-to-all** | ★★★★★ | 동일 |
| **분산 KV (Memcached, Redis-like)** | ★★★★ | Small message, 짧은 latency |
| **분산 storage (NVMe-oF)** | ★★★★★ | Block 크기 transfer, kernel bypass 효과 큼 |
| **일반 웹 서비스 (HTTP)** | ★★ | RDMA 의 setup 비용이 connection 짧은 워크로드에 비해 큼 |
| **WAN (대륙간)** | ★ | RDMA reliability 는 LAN/DC 가정 |

### 5.5 인접 영역 — AI Server, NRT, GPUBoost

!!! note "Internal (Confluence: AI Servers, RDMA for NRT, Latest GPUBoost Specification)"
    사내 RDMA-IP 의 운용 환경은 **AI training / inference 노드** (예: NVIDIA DGX, AMD MI325X) 와 **NRT (Non-RDMA Transport) fallback** 시나리오를 모두 포함한다.

    - **AI Servers** — RCCL/NCCL allreduce, all-to-all, scatter/gather 가 핵심. RDMA-IP 는 GPU peer-memory 를 IOVA 로 노출하기 위해 **MR Large MR 모드** 를 자주 사용한다 (참조: M05).
    - **RDMA for NRT** — RDMA QP 를 사용할 수 없는 경로 (예: CPU-only flow) 를 위해 IP 가 fallback path 를 노출. 검증에서는 두 path 가 **동일 application 시맨틱** 을 보장하는지 비교 scoreboard 로 확인.
    - **GPUBoost spec** — 사내 RNIC 의 외부 spec. opcode·MTU·QP 수 등의 cap 은 spec 에서 직접 인용한다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'RDMA = 빠른 TCP'"
    **실제**: RDMA 는 transport semantics 가 아예 다릅니다. TCP 는 byte stream + 양 끝의 user-space socket. RDMA 는 message + 원격 메모리 주소 (rkey + virtual address) 모델. RC service 의 reliability 도 hardware ACK/NAK + PSN + retry 로 구현되며, TCP 의 reliability 와는 다른 mechanism. **"빠른 TCP" 가 아니라 "원격 메모리 access"** 입니다.<br>
    **왜 헷갈리는가**: "high-performance networking" 카테고리에 같이 묶이고, RoCEv2 가 IP/UDP 위에 올라가서.

!!! danger "❓ 오해 2 — 'RDMA-CM 도 RDMA 다'"
    **실제**: RDMA-CM 자체는 _TCP 위에서 동작하는 "RDMA connection 만들기" 프로토콜_ 입니다. 노드끼리 (rkey, remote_va, QPN) 같은 메타데이터를 교환하는 control path. 데이터는 그 후 RDMA QP 로 갑니다. <br>
    **왜 헷갈리는가**: 이름이 RDMA 로 시작.

!!! danger "❓ 오해 3 — 'RDMA 는 throughput 이 빠른 거다'"
    **실제**: TCP/IP 도 100 Gbps 라인레이트 자체는 잘 채웁니다. RDMA 의 차별점은 **CPU 점유율** 과 **tail latency** 입니다. 1 µs vs 10 µs 는 `p99.9` 에서 큰 차이.<br>
    **왜 헷갈리는가**: 마케팅 자료가 "fast" 만 강조.

!!! danger "❓ 오해 4 — 'rkey 만 알면 안전'"
    **실제**: rkey 가 노출되면 원격 노드가 임의 메모리에 RDMA WRITE 가능 → MR 의 access flag (Local R/W, Remote R/W/Atomic) 와 PD 격리는 **spec 가 아니라 구현 책임**. 검증 시 access flag 위반 시 어떤 CQE 가 떨어지는지 직접 확인.

### DV 디버그 체크리스트 (초기 RDMA 시뮬에서 자주 보는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| CQE status = `WC_LOC_PROT_ERR` | lkey mismatch / 미등록 영역 | MR 의 lkey 와 WQE 의 sg_list lkey 비교 |
| CQE status = `WC_REM_ACCESS_ERR` | rkey mismatch 또는 access flag 위반 | 상대 MR 의 access flag (Remote Write 켜졌나?) |
| CQE 가 안 옴 (timeout) | 도어벨 안 됨 또는 ACK 안 옴 | post_send 후 SQ HW pointer 진행했나, BTH.PSN 시퀀스 |
| Peer CPU 가 깨어남 | SEND 를 WRITE 와 혼동 | WRITE 는 peer CPU 안 깨움. SEND 는 peer 의 RQ WQE 소비 + WC |
| 같은 PD 인데 access 거부 | rkey 가 다른 PD 의 MR | `ibv_reg_mr` 의 PD argument 확인 |
| connection setup 자체가 안 됨 | RDMA-CM (TCP) 경로 문제 | RDMA verb 와 분리해서 디버그 |

이 체크리스트는 이후 모듈에서 더 정교한 형태로 다시 나옵니다. 지금 단계에서는 "RDMA 실패 = CQE error status + (lkey | rkey | PD | PSN | 도어벨) 확인" 만 기억하세요.

---

## 7. 핵심 정리 (Key Takeaways)

- **세 축**: kernel bypass + zero-copy + transport offload — 셋이 동시에 만족돼야 의미가 있다.
- **DMA → RDMA**: "내 메모리 ↔ 내 디바이스" 가 "내 메모리 ↔ 원격 메모리" 로 확장. 그래서 _주소 약속_ (rkey + remote_va) 이 필수.
- **6 객체**: PD / MR / QP / CQ / WQE / WC. 이후 모든 모듈의 어휘.
- **변형 4종**: IB / iWARP / RoCEv1 / RoCEv2. 오늘 데이터센터는 RoCEv2 가 표준, HPC/AI 는 IB 가 강세.
- **DV 관점**: host CPU 가 빠지므로 TB 가 host memory + MMU + PCIe + control/data path 분리까지 모델링해야 한다.

!!! warning "실무 주의점"
    - "RDMA 빠르다" 는 **latency / CPU 점유율**. throughput 만 보면 TCP 도 라인레이트 가능.
    - **RDMA-CM ≠ RDMA**. RDMA-CM 은 TCP 위 connection setup.
    - 보안: rkey 노출 = remote write 가능 → MR access flag 와 PD 격리는 구현 책임.

---

## 다음 모듈

→ [Module 02 — InfiniBand 프로토콜 스택](02_ib_protocol_stack.md): RDMA 의 가정 위에서 IB 가 패킷을 어떻게 그렸는지. LRH/GRH/BTH/xTH 와 ICRC/VCRC 의 분리.

[퀴즈 풀어보기 →](quiz/01_rdma_motivation_quiz.md)

--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
