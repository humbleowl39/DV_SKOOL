---
title: "Module 01 — RDMA 동기와 핵심 모델"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** TCP/IP 가 가진 세 가지 비용 (memcpy / stack / interrupt) 을 RDMA 가 어떻게 제거하는지 설명할 수 있다.
- **Distinguish** "DMA" 와 "RDMA" 를 단어가 아니라 **데이터 흐름** 관점에서 구분할 수 있다.
- **Trace** 1 KB RDMA WRITE 한 번을 8단계로 끝까지 추적할 수 있다.
- **Identify** Verbs 6 객체 (PD, MR, QP, CQ, WQE, WC) 의 역할과 협력 관계를 식별한다.
- **Compare** IB / iWARP / RoCEv1 / RoCEv2 의 계보와 사용 영역을 비교한다.
:::
:::note[사전 지식]
- TCP/IP 송수신 흐름 (sk_buff, copy_to/from_user, NIC interrupt)
- DMA, PCIe 의 memory-mapped IO
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — 1024-GPU LLM 학습이 통신에서 죽는다

먼저 한 문장으로 정리하면, **RDMA**(Remote Direct Memory Access — 한 노드의 네트워크 카드가 상대 노드의 CPU를 거치지 않고 그 노드의 메모리를 직접 읽고/쓰는 기술)는 "원격 메모리를 내 메모리처럼 직접 건드린다"는 한 가지 발상에서 출발합니다. 이 모듈은 그 발상이 왜 필요한지를 보입니다.

2026년 1월. 우리는 H100 1024 개로 GPT 급 LLM 을 학습합니다. 매 step 마다 **32 GB 의 gradient**(학습에서 모델 가중치를 갱신하기 위해 계산하는 기울기 값 묶음) 를 all-reduce(여러 노드가 각자 가진 값을 모두 더한 뒤 그 합을 모두에게 되돌려주는 집합 통신 연산) 해야 합니다.

**문제**: 한 step 의 compute 시간은 ~600 ms. 그런데 _통신_ 만 잘못 짜면 step 시간이 **2~3 배** 늘어납니다. 측정해 봅시다.

```
   Per-step gradient allreduce, 1024 GPU × 32 GB = 32 TB aggregate
                            ┌─────────────────────────────────────────┐
   TCP/IP over 100 GbE      │ ~ 6.4 s / step    (10× compute time)    │ ← 학습 불가능
   RDMA over 100 GbE        │ ~ 0.4 s / step    (compute 와 겹침)      │
                            └─────────────────────────────────────────┘
   * 출처: NCCL all_reduce_perf, 92% of fabric peak ~ 370 GB/s on 400G fabric.
     [Oracle/Nebius blog, 2025]
```

**왜 이 차이가 나는가?** TCP/IP 는 100 Gbps 라인레이트(line rate — 링크가 물리적으로 낼 수 있는 최대 전송 속도) 를 채우려면 CPU 코어를 **4 ~ 8 개** 통째로 통신 처리에 쓴다 — 그러면 _학습 코드_ 가 돌 수 있는 코어가 그만큼 줄어듭니다. 그리고 매 메시지마다 `copy_from_user`(커널이 사용자 공간 버퍼의 데이터를 커널 버퍼로 복사하는 동작) + 스택 + interrupt 의 누적이 **p99 latency**(요청 100건 중 99번째로 느린 지연 — 평균이 아닌 "느린 꼬리"를 나타내는 지표) 를 폭주시킵니다 (10 µs → 50 µs 의 tail).

### 1.2 그래서 이 모듈을 잡아야 한다

이후 모든 RDMA 모듈은 한 가정에서 출발합니다 — **"네트워크의 양 끝 NIC**(network interface card, 네트워크 카드)** 가 host CPU 를 거치지 않고 상대 노드의 메모리를 직접 읽고/쓴다"**. IB(InfiniBand — RDMA 를 위해 만들어진 전용 네트워크 규격) 패킷 헤더가 왜 그렇게 생겼는지, RC service(Reliable Connection — 1:1 연결에서 패킷 손실 없이 순서대로 전달을 하드웨어가 보장하는 전송 방식) 가 왜 PSN(packet sequence number, 패킷에 매기는 일련번호)/ACK(수신 확인 신호) 를 hardware 로 처리하는지, DV TB(testbench, 검증 환경) 가 왜 host memory 와 MMU(memory management unit, 가상주소를 물리주소로 변환하는 하드웨어) 까지 모델링해야 하는지 — 전부 이 한 가정의 파생입니다.

이 모듈을 건너뛰면 이후의 모든 spec/패킷/검증 결정이 "그냥 외워야 하는 규칙" 으로 보입니다. 반대로 이 가정을 정확히 잡고 나면, 디테일을 만날 때마다 **"아, 이게 zero-copy**(데이터를 중간 버퍼로 복사하지 않고 NIC 가 사용자 메모리에서 곧바로 주고받는 것)** 를 위한 거구나"** 처럼 _이유_ 가 보입니다.

:::tip[🤔 잠깐 — 100 Gbps 에서 패킷 한 개 간격은?]
1500-byte 이더넷 프레임을 100 Gbit/s 로 연속 전송한다고 합시다. 패킷 하나가 도착하는 시간 간격은 약 얼마인가요?

이게 왜 중요한가? CPU 가 인터럽트 받고 context switch 하는 데 **수백 ns** 가 듭니다. 만약 패킷 간격이 그것보다 짧으면?

<details>
<summary>정답</summary>

**약 120 ns** (1500 B × 8 / 100 Gbit/s ≈ 120 ns).

Context switch 가 ~500 ns 이므로, 패킷이 도착할 때마다 CPU 가 깨면 **CPU 가 패킷 도착 속도를 못 따라잡습니다**. → 이게 곧 "interrupt coalescing"(여러 패킷을 모아 인터럽트를 한 번만 발생시켜 부담을 줄이는 기법) 과 "kernel bypass"(통신할 때 운영체제 커널을 거치지 않고 사용자 프로그램이 NIC 와 직접 주고받는 것) 가 동시에 필요한 이유.

</details>
:::
---

## 2. Intuition — 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**TCP/IP** = 택배 회사. 박스에 담아(`copy_from_user`) 우체국(kernel/NIC)에 맡기고, 받는 쪽 우체국이 풀어서 다시 옮겨담아(`copy_to_user`) 사용자에게 줌.<br>
**RDMA** = 두 사무실이 _같은 캐비넷에 한 서랍씩 공유_ 하는 모델. 미리 "여기가 네 서랍이야" 라고 등록(MR — Memory Region, RDMA 에 노출하기로 등록한 메모리 영역)해 두면 상대가 우체국 거치지 않고 직접 쓰고 빠짐.
:::
### 한 장 그림 — TCP path vs RDMA path

```d2
direction: down

TCP: "TCP/IP — 3 copies + interrupt" {
  direction: right
  T1: "App (송신)"
  T2: "user buf"
  T3: "socket buf"
  T4: NIC
  T5: "NIC (수신)"
  T6: "socket buf"
  T7: "App (수신)"
  T1 -> T2
  T2 -> T3: "copy_from_user"
  T3 -> T4: "TCP/IP stack"
  T4 -> T5: "wire"
  T5 -> T6: "IRQ"
  T6 -> T7: "copy_to_user"
}
RDMA: "RDMA — 0 copies, no IRQ" {
  direction: right
  R1: "App (송신)"
  R2: "user buf (MR)"
  R3: HCA
  R4: "HCA (peer)"
  R5: "peer MR"
  R1 -> R2
  R2 -> R3: "doorbell"
  R3 -> R4: "DMA wire"
  R4 -> R5: "DMA write"
}
TCP -> RDMA: { style.opacity: 0.0 }
```

위 그림에서 **HCA**(Host Channel Adapter — RDMA 를 지원하는 NIC 의 IB 표준 명칭; 이더넷판은 RNIC 이라 부른다) 와 **doorbell**(NIC 에게 "새 작업이 큐에 들어왔다"고 알리는 한 번의 쓰기 신호) 이 핵심입니다. 세 개의 복사 단계가 RDMA 에서는 모두 사라지고, 대신 **HCA hardware** 가 PSN, ACK, 재전송, 무결성 검사를 처리합니다.

### 왜 이렇게 설계됐는가 — 순진한 시도가 모두 실패한 결과

RDMA 가 채택한 설계는 _하늘에서 떨어진_ 게 아닙니다. 1990년대~2000년대 초 여러 순진한 시도가 _구체적으로 어디서 막혔는지_ 의 결과물입니다. 세 가지 대표 시도를 따라가 봅시다.

**시도 1 — "TCP/IP 스택을 더 빠르게 만들면?"** (Toe, TCP Offload Engine)
NIC 에 TCP 처리를 일부 offload 하면? → 일부 latency 개선되지만 _user space 까지_ 의 `copy_to_user` 와 socket buffer 가 여전히 존재. CPU jitter 가 사라지지 않음. **결론: socket API 자체가 병목.**

**시도 2 — "그냥 DMA 를 wire 로 확장하면?"** (단순 remote DMA)
"내 메모리 ↔ 내 디바이스" 의 DMA 를 "내 메모리 ↔ 원격 메모리" 로 일반화하면 안 되나? → 두 가지가 막힘:

- **보안**: 원격 노드가 임의 메모리 주소를 쓸 수 있으면 OS isolation 붕괴. → "사전 등록(MR) + 키(R_Key — Remote Key, 원격 노드가 내 MR 에 접근할 때 제시해야 하는 보호 키)" 같은 권한 제어 필요.
- **주소**: 원격 노드는 내 가상 주소도, 물리 주소도 모름. → IOVA(IO virtual address — 디바이스가 메모리를 가리킬 때 쓰는 가상 주소) 와 MR 등록으로 매핑 필요.

**시도 3 — "MMIO 로 원격 메모리 직접 쓰면?"** (memory-mapped over wire)
PCIe 같은 메모리-매핑 IO 를 네트워크로 확장? → 거리/지연 때문에 cache coherence 가 불가능. cache flush latency 만 ~10 µs. **결론: per-load/store 가 아닌 _메시지 단위_ 의 비동기 모델 필요.**

세 시도의 _부분 정답_ 을 합치면 다음 세 가지가 _동시에_ 만족돼야 한다는 결론에 도달합니다:

| 축 | 시도 1 이 못 푼 것 | 시도 2 가 못 푼 것 | 시도 3 이 못 푼 것 |
|----|------------------|------------------|------------------|
| **Kernel bypass** | ✗ (socket 잔존) | — | — |
| **Zero-copy** | ✗ (copy 잔존) | — | — |
| **Transport offload** | △ (부분만) | △ (DMA 만) | — |
| **메모리 등록 + 키** | — | ✗ (보안 구멍) | — |
| **메시지 단위 비동기** | — | — | ✗ (per-load/store) |

이 다섯이 동시에 만족돼야 _100 Gbps 라인레이트 + p99 안정 + 보안_ 이라는 세 마리 토끼가 잡힙니다. 이게 RDMA 의 설계 결정 — **kernel bypass + zero-copy + transport offload** — 가 _하나라도 빠지면 전체가 무너지는_ 이유.

100 Gbps 라인레이트에서는 패킷 1개 도착 간격이 **~120 ns** (1.1 의 계산). CPU 가 인터럽트 받고 컨텍스트 전환만 해도 수백 ns. 즉 **CPU 가 끼는 한 라인레이트를 못 채웁니다**. 그래서 세 축이 _동시에_ 만족돼야 의미가 있고, 셋 중 하나라도 빠지면 전체가 의미를 잃습니다. 이 세 축이 곧 IB/RoCE 패킷 포맷, Verbs API 디자인, 검증 환경의 구조를 결정합니다.

---

## 3. 작은 예 — 1 KB RDMA WRITE 를 step by step 으로 따라가기

가장 단순한 시나리오. 노드 **A** 가 노드 **B** 의 메모리에 **1 KB** 를 RDMA WRITE(원격 메모리에 데이터를 직접 쓰는 RDMA 동작 — 상대 CPU 를 깨우지 않음) 합니다. 아래 그림에 나오는 핵심 약어를 미리 풀어두면: **QP**(Queue Pair — 송신 큐와 수신 큐 한 쌍으로 이루어진 RDMA 통신 endpoint), **WQE**(Work Queue Element — 큐에 넣는 한 개의 작업 지시서), **CQE/WC**(완료 통지 항목), **ACK**(수신 확인 신호) 입니다.

```d2
shape: sequence_diagram

AppA: "Node A\napp + lbuf"
HA: "HCA_A"
HB: "HCA_B"
AppB: "Node B\napp + rbuf"

# Note over HB: ① ibv_reg_mr(rbuf)\npinning + rkey 발급
# Note over HB: B 의 CPU 한 번도\n안 깨움 ⭐
AppB -> AppA: "② (remote_va, rkey) 전달\nout-of-band\n(RDMA-CM / TCP)"
AppA -> HA: "③ post_send WQE"
HA -> HA: "④ DMA read lbuf"
HA -> HB: "BTH + RETH + payload\n(over wire)"
HB -> HB: "⑤ rkey verify\n⑥ DMA write → rbuf"
HB -> HA: "⑦ ACK packet" { style.stroke-dash: 4 }
HA -> AppA: "⑧ CQE 생성\n(poll_cq)" { style.stroke-dash: 4 }
```

| Step | 누가 | 무엇을 | 의미 |
|---|---|---|---|
| ① | B 의 app | `ibv_reg_mr(rbuf, len, R/W)` 로 rbuf 등록 | NIC 가 DMA 가능하게 핀(pinning) + rkey 발급 |
| ② | B → A | (remote_va, rkey) 를 out-of-band(데이터 경로와 별개의 통로) 로 알려줌 | RDMA 자체는 채널이 없음 — 보통 RDMA-CM(RDMA Connection Manager, TCP 위에서 연결 정보를 교환하는 프로토콜) 또는 sockets |
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

:::note[여기서 잡아야 할 두 가지]
**(1) 양 노드의 CPU 가 거의 안 쓰임** — A 는 post_send + poll_cq, B 는 0회. 이게 RDMA 의 본질. <br>
**(2) "원격 메모리 주소" 가 미리 약속돼야 한다** — RDMA 는 _주소를 알고 직접 쓰는_ 모델. 그래서 connection setup (control path) 과 data 전송 (data path) 이 분리됩니다.
:::

#### 메커니즘 1 — Doorbell MMIO 가 실제로 하는 일 (Step ③)

Step ③ 의 "도어벨 MMIO**(memory-mapped IO — 디바이스 레지스터를 메모리 주소처럼 읽고 써서 제어하는 방식)** 1번" 은 단순히 "신호를 보낸다" 가 아니라, _구체적으로_ **SQ**(Send Queue — QP 에서 보낼 작업을 쌓아두는 큐)** 의 producer pointer (tail) 값을 NIC 의 BAR**(base address register — PCIe 디바이스의 레지스터/메모리가 호스트 주소 공간에 매핑되는 영역)** 영역에 write** 하는 동작입니다. 흐름은 이렇습니다:

1. App 이 WQE 를 SQ ring buffer (host memory) 의 다음 슬롯에 채워 넣는다. 이 시점엔 NIC 가 아직 모릅니다.
2. App 이 NIC 의 MMIO doorbell register (PCIe BAR 안의 한 주소) 에 **새 tail 값** 을 write 한다.
3. 이 write 가 PCIe 를 타고 NIC 에 도달하면, NIC 는 "내가 알던 tail 보다 producer pointer 가 앞섰다 → 새 WQE 가 생겼다" 를 인식하고, host memory 에서 WQE 를 **DMA fetch** 합니다.

즉 doorbell 은 _데이터를 옮기는_ write 가 아니라 **"여기까지 WQE 가 찼다" 는 포인터 갱신** 입니다. 이게 kernel bypass 의 물리적 실체입니다 — syscall 없이, user-space 에서 BAR 주소에 한 번 store 하면 NIC 가 깨어납니다. (구현에 따라 doorbell write 는 write-combining 영역으로 매핑돼 여러 store 가 하나의 PCIe transaction 으로 묶이기도 합니다 — 확인 필요한 디테일이지만 핵심은 "포인터를 BAR 에 쓴다" 입니다.)

#### 메커니즘 2 — Scatter-Gather: 흩어진 버퍼를 하나의 stream 으로 (sg_list)

위 코드의 `sg_list` 와 `num_sge` 를 보세요. 한 WQE 는 **여러 개의 SGE (Scatter-Gather Element)** 를 가질 수 있습니다 — 각 SGE 는 `(addr, length, lkey)` 한 쌍입니다. 왜 여러 개가 필요한가? Application 의 데이터가 메모리에 **연속으로 놓여 있지 않은** 경우가 흔하기 때문입니다 (예: 헤더는 한 버퍼, 페이로드는 다른 버퍼).

NIC 의 DMA 엔진은 한 WQE 를 처리할 때 **sg_list 를 순서대로 순회 (descriptor walk)** 합니다: SGE[0] 의 addr 에서 length 만큼 DMA read → SGE[1] 의 addr 에서 length 만큼 DMA read → … 그리고 이렇게 읽어들인 조각들을 **하나의 연속된 payload stream 으로 이어 붙여** 패킷에 싣습니다. 수신 측에서는 반대로, 도착한 stream 을 RECV WQE 의 sg_list 가 가리키는 여러 버퍼에 **흩어서 (scatter)** DMA write 합니다.

이게 "zero-copy 인데도 흩어진 데이터를 보낼 수 있는" 이유입니다 — SW 가 미리 한 버퍼로 memcpy 해 모을 필요 없이, NIC 가 DMA 단계에서 gather/scatter 를 직접 합니다.

#### 메커니즘 3 — 왜 MR 등록에 "pinning" 이 전제인가 (Step ①)

Step ① 의 `ibv_reg_mr` 가 메모리를 **pin** 한다고 했습니다. 왜 핀이 필수일까요? 핵심은 **NIC DMA 는 물리주소 (PA) 로 동작한다** 는 사실입니다.

App 이 다루는 주소는 가상주소 (VA) 지만, NIC 가 실제로 메모리에 read/write 하려면 그 VA 에 대응하는 PA 를 알아야 합니다. MR 등록 시점에 OS 가 VA→PA 매핑을 NIC (의 translation table) 에 알려줍니다. 그런데 일반적인 OS 는 메모리 압박이 생기면 페이지를 **swap-out 하거나 다른 PA 로 이동** 시킬 수 있습니다 (page migration). 만약 NIC 가 기억하던 PA 의 페이지가 그 사이에 옮겨지면, NIC 는 **이미 다른 데이터가 들어찬 stale PA** 에 DMA 를 해버립니다 → silent corruption.

그래서 MR 등록은 해당 페이지들을 **pin (= swap/이동 금지로 PA 고정)** 합니다. PA 가 고정돼야 NIC 가 CPU 개입 없이 안전하게 DMA 할 수 있고, 이것이 zero-copy 의 전제 조건입니다. 동시에 이게 MR 등록이 _비싼_ control-path 동작인 이유 — 대량 메모리를 핀하면 OS 의 페이지 관리 유연성이 줄기 때문에, 데이터 패스에서가 아니라 connection setup 단계에서 미리 해두는 것입니다.
:::tip[🤔 잠깐 — 만약 step ⑥ 에서 B 의 CPU 를 깨우려면?]
위 그림에서 B 의 CPU 는 한 번도 안 깨워졌습니다. 만약 B 의 application 이 "데이터 도착했음" 을 알아야 한다면 (예: 메시지 큐에 새 항목 push), A 는 어떤 opcode 를 써야 할까요?

<details>
<summary>정답</summary>

**SEND**(메시지를 보내 상대의 수신 큐를 소비시키는 RDMA 동작) 또는 **WRITE_WITH_IMMEDIATE**.
- **SEND** 는 B 의 RQ(Receive Queue — QP 에서 수신 작업을 쌓아두는 큐) 에서 RECV WQE 를 소비 → CQ 에 WC 가 떨어짐 → B 의 application 이 `poll_cq` 로 알아챔.
- **WRITE_WITH_IMMEDIATE** 는 WRITE 본체와 함께 4 byte ImmDt 도 전달, 마찬가지로 B 의 CQ 에 WC 생성.
- **일반 WRITE** 는 _완전 비동기_ — 데이터만 도착, B 의 application 은 다른 방법(polling memory, signal flag)으로 감지해야 함.

이게 M06 의 "왜 SEND 와 WRITE_WITH_IMM 가 따로 존재하는가?" 질문의 답: **completion 통지 의무** 가 다릅니다.

</details>
:::
---

## 4. 일반화 — 세 가지 축과 6 객체

### 4.1 RDMA 의 세 축 — 그리고 각 축이 빠지면 무엇이 부서지는가

| 축 | 무엇을 제거 | TCP/IP 와의 차이 | **이 축이 빠지면 발생하는 시스템 실패** |
|---|---|---|---|
| **Kernel bypass** | Syscall + context switch | post_send 는 user-space MMIO doorbell | 매 메시지마다 context switch (~500 ns) → p99 latency jitter 폭주 → AI training step 시간 분산 큼 → 동기 barrier 가 _가장 느린 GPU_ 에 의해 결정 → 평균 throughput 폭락 |
| **Zero-copy** | `copy_from/to_user` | NIC 가 user buffer 에서 직접 DMA (MR pinning 으로 가능) | 매 메시지마다 memcpy → 100 Gbps 양방향이면 25 GB/s memcpy → DDR4 25.6 GB/s 한 채널 통째로 점유 → application 의 메모리 대역폭이 0 으로 수렴 |
| **Transport offload** | TCP stack (PSN, ACK, retransmit, congestion) 의 SW 처리 | HCA hardware 가 RC PSN/ACK/NAK/retry 처리 | 100 Gbps 채우려면 4~8 코어 통째로 통신 처리에 점유 (Mellanox WP 2014 측정) → 64 코어 서버에서 12% 의 코어가 _학습/추론_ 이 아닌 _통신_ 에 소진 |

:::note[Internal (Confluence: [RDMA) basic, id=934608922)]
사내 보고서도 같은 결론: "1Gbps 네트워크 시대에 설계된 소켓 통신 방식은 100Gbps, 400Gbps, 나아가 800Gbps에 이르는 현대의 고속 네트워크 대역폭을 감당하기에 지나치게 비효율적이다. 100Gbps 대역폭을 TCP/IP로 포화시키기 위해서는 최신 멀티코어 프로세서의 상당수 코어를 오직 통신 처리에만 할당해야 하는 비효율이 발생한다."

**사내 자료가 외부 자료(Mellanox WP, Oracle Cloud benchmark)와 일치하므로 이 측정은 신뢰 가능.**
:::
### 4.1.1 대안 비교 — 왜 iWARP 가 시장에서 사실상 졌나?

세 축이 모두 만족돼야 한다면, _부분만_ 만족시키는 대안은 어떻게 됐을까? iWARP 의 흥망에서 답을 찾을 수 있습니다.

| 변형 | Kernel bypass | Zero-copy | Transport offload | 결과 |
|------|---------------|-----------|-------------------|------|
| **TCP/IP** | ✗ | ✗ | ✗ | 100 Gbps 부적합 (CPU 폭주) |
| **iWARP** | ✓ | ✓ | △ (TCP 위라 retransmit/PSN 결국 SW 도움) | 3 µs latency. RoCE 의 1.3 µs 에 비해 **2.3 배 느림**. 시장 outcompete 됨 |
| **RoCEv2** | ✓ | ✓ | ✓ (BTH 가 IB Transport 그대로) | 7~10 µs latency (DC 라우팅 시), IB 의 1~2 µs 에 가까운 성능 |
| **InfiniBand** | ✓ | ✓ | ✓ | 1~2 µs latency, switch port-port 100 ns |

**교훈**: iWARP 는 "TCP 위에서 RDMA 의 _프로그래밍 모델_ 만 제공" — 호환성은 좋지만 transport offload 가 _TCP 의 제약_ 을 그대로 안고 감. 그래서 latency 와 throughput 모두 RoCE 에 밀림. 2026 년 현재 iWARP 는 legacy 로 분류[NVIDIA RoCE vs iWARP WP, 2025; AI Journal RoCEv2 vs IB vs iWARP, 2025].

:::note[외부 자료]
"There are RoCE HCAs with a latency as low as 1.3 microseconds while the lowest known iWARP HCA latency in 2011 was 3 microseconds." — *RDMA over Converged Ethernet, Wikipedia, 2025*
:::
### 4.2 DMA vs RDMA — 한 글자 차이의 의미

:::note[정의 (ISO 11179)]
- **DMA**: CPU 의 직접 개입 없이 디바이스가 호스트 메모리를 직접 read/write 하는 메커니즘.
- **RDMA**: 네트워크의 양 끝에서 DMA 가 동시에 일어나, **원격** 노드의 메모리를 read/write 하는 메커니즘.
:::
```d2
direction: right

DMAg: "Local DMA\n(CPU 개입 없음)" {
  direction: down
  LD_CPU: CPU
  LD_MEM: memory
  LD_DISK: disk
  LD_CPU -- LD_MEM: { style.stroke-dash: 4 }
  LD_MEM <-> LD_DISK: "DMA"
}

RDMAg: "RDMA\n(원격 메모리 직접 액세스)" {
  direction: down
  R_CPU1: "CPU₁"
  R_MEM1: "mem₁"
  R_HCA1: "HCA₁"
  R_HCA2: "HCA₂"
  R_MEM2: "mem₂"
  R_CPU2: "CPU₂"
  R_CPU1 -- R_MEM1: { style.stroke-dash: 4 }
  R_CPU2 -- R_MEM2: { style.stroke-dash: 4 }
  R_MEM1 <-> R_HCA1: "DMA"
  R_HCA1 <-> R_HCA2: "R_Key + VA"
  R_HCA2 <-> R_MEM2: "DMA"
}
```

RDMA 가 일반 DMA 와 다른 점은 "원격" 이라는 한 단어에 있습니다. 송신 측이 먼저 Memory Registration 으로 원격 노드의 메모리 영역을 RDMA 에 노출하고, 그 영역에는 보호 키인 R_Key 가 발급됩니다. 이후 양 끝 NIC 는 R_Key 와 가상 주소를 패킷에 실어 주고받으며, CPU 개입 없이 직접 DMA 로 메모리를 읽고 씁니다.

### 4.3 Verbs 6 객체 — 협력 관계

**Verbs**(RDMA 자원을 만들고 다루기 위한 표준 API — 대표 구현은 `libibverbs`) 가 다루는 핵심 객체는 여섯 개입니다. 아래 그림이 그 협력 관계입니다.

```d2
direction: down

PD: "**PD** · Protection Domain\n같은 PD 안에서만 cross-access 허용"
MR: "**MR** · Memory Region\nDMA 가능 영역 + access flag\nlkey / rkey"
QP: "**QP** · Queue Pair\nservice: RC / UC / UD / XRC"
SQ: "**SQ** · Send Queue"
RQ: "**RQ** · Recv Queue"
CQ: "**CQ** · Completion Queue"
WQE: "WQE — operation 디스크립터" { shape: oval }
WC: "WC — 처리 결과" { shape: oval }
PD -> MR
PD -> QP
QP -> SQ
QP -> RQ
WQE -> SQ: "post_send"
WQE -> RQ: "post_recv"
QP -> CQ: "완료 통지" { style.stroke-dash: 4 }
CQ -> WC: "poll_cq"
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
Send Queue + Receive Queue. 한 QP 가 한 endpoint. RC(Reliable Connection, 신뢰성 보장 1:1)/UC(Unreliable Connection, 1:1 이지만 재전송 없음)/UD(Unreliable Datagram, 연결 없이 보내는 방식)/XRC(여러 송신 QP 가 한 수신 QP 를 공유) 중 한 service type(QP 가 제공하는 전달 보증 수준).
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

```d2
direction: down

TX: "송신 측" {
  direction: right
  AppS: "App"
  SBS: "Socket buf"
  NICS: NIC
  AppS -> SBS: "(1) copy_from_user"
  SBS -> NICS: "(2) TCP/IP stack · CPU"
}
RX: "수신 측" {
  direction: right
  NICR: NIC
  SBR: "Socket buf"
  AppR: "App"
  NICR -> SBR: "IRQ → ksoftirqd · CPU"
  SBR -> AppR: "(3) copy_to_user"
}
TX -> RX: "wire"
```

| 비용 | 발생 위치 | RDMA 의 해결 |
|------|----------|-------------|
| **(1) Send-side memcpy** | `copy_from_user` | Memory Registration → NIC 가 사용자 메모리 직접 read |
| **(2) Stack processing** | TCP segment, retransmit timer, congestion control 모두 SW | Transport offload → HCA hardware 가 PSN/ACK/NAK 처리 |
| **(3) Recv-side memcpy + interrupt** | `copy_to_user`, IRQ → softirq → 스케줄링 | Zero-copy 직접 DMA, polling completion (선택) |

**결과**: 100 Gbps 링크에서 TCP/IP 는 **~10–15 µs** RTT, RDMA 는 **~1–3 µs** RTT. CPU 사용률은 보통 **5–10× 차이**.

### 5.2 RDMA 의 세 가지 변형 — IB / iWARP / RoCE

```d2
direction: down

ROOT: "RDMA 패밀리"
IB: "**InfiniBand (IB)**\n━━━━━━━━━━━━\nIB Link / Net Layer\nIB SerDes (1x..12x)\nHPC, 전용 Fabric\n_IBTA Vol1_"
IW: "**iWARP**\n━━━━━━━━━━━━\nTCP/IP 위에 RDMA\n표준 IP 인프라\n느림 (TCP overhead)\nLong-distance, WAN\n_IETF spec_"
ROCE: "**RoCE (v1, v2)**\n━━━━━━━━━━━━\nEthernet 위에 RDMA\nv1: Eth L2 직결\nv2: IP/UDP(4791) + BTH\n데이터센터 표준\n_IBTA Annex A16/A17_"
ROOT -> IB
ROOT -> IW
ROOT -> ROCE
```

| 항목 | InfiniBand | iWARP | RoCEv1 | RoCEv2 |
|------|-----------|-------|--------|--------|
| L1/L2 | IB SerDes + Link | Ethernet | Ethernet (L2) | Ethernet (L2) |
| L3 | IB Network (GRH) | IP | (없음 — L2 only) | IPv4 / IPv6 |
| L4 | IB Transport (BTH) | TCP + DDP/RDMAP | BTH | UDP(4791) + BTH |
| 라우팅 | IB Subnet Manager | Standard IP routing | 같은 broadcast domain 내 | Standard IP routing |
| 설치 환경 | HPC, AI 클러스터 | 일반 IP 망 | 단일 L2 도메인 | 데이터센터 일반 |
| 성능 | 가장 좋음 (~600 ns) | TCP 오버헤드 | IB와 유사 | IB와 거의 동등 |

위 표의 헤더 약어를 미리 풀면: **BTH**(Base Transport Header — 모든 IB transport 패킷에 붙는 기본 헤더, OpCode·목적지 QP·PSN 등을 담음), **GRH**(Global Route Header — subnet 간 라우팅용 IPv6 형식 헤더), **iWARP**(TCP/IP 위에 RDMA 를 얹은 변형), **RoCE**(RDMA over Converged Ethernet — 이더넷 위에서 RDMA 를 돌리는 방식; v2 는 IP/UDP 위에 BTH 를 얹음) 입니다.

**오늘 (2026)**: 데이터센터/하이퍼스케일러는 거의 **RoCEv2**, HPC/AI 트레이닝 팜은 여전히 **InfiniBand**, iWARP 는 사실상 레거시.

:::note[Spec 인용]
"RoCEv2 packets share the same Base Transport Header (BTH) and Extended Transport Headers (xTH) used in InfiniBand transport. The IB Network Layer (GRH) is replaced with the IP header." — IBTA, *Annex A17 RoCEv2*, §A17.4
:::
### 5.3 Verbs API — Control path vs Data path

```d2
direction: down

APP: "User application"
LIB: "**libibverbs** (Verbs)\n_OFED user-space lib_"
KER: "**ib_uverbs / rdma_cm**\n_kernel module_"
HW: "HCA / RNIC"
APP -> LIB
LIB -> KER: "ioctl / uverbs\n(control path)"
KER -> HW: "MMIO + DMA"
LIB -> HW: "data path: MMIO doorbell\n(kernel bypass)" { style.stroke-dash: 4 }
```

:::note[Internal (Confluence: RDMA Verbs (basic), id=32178388)]
실제 host 측 RDMA 스택은 **user-level driver** 와 **kernel-level driver** 두 갈래가 모두 있다.
user-level driver 는 `libibverbs` 가 RNIC 의 BAR 영역과 직접 통신해 syscall context-switch 를 회피하고, completion 을 polling 방식으로 가져온다 — datapath verbs (`ibv_post_send`, `ibv_poll_cq`) 가 여기에 속한다.
반면 kernel-level driver 는 자원 할당·매핑·MR pinning 처럼 **권한 / 안전성 검증** 이 필요한 control path verbs (`ibv_open_device`, `ibv_alloc_pd`, `ibv_reg_mr`, `ibv_create_qp`) 를 처리한다.
두 드라이버는 **기능 차이가 없고**, 같은 verb 가 user-level 에서는 `ibv_*`, kernel-level 에서는 `ib_*` 로 명명된다.
검증 환경에서도 control path 와 datapath 를 분리하는 이 모델을 그대로 따른다 — TB 의 sequence 는 verb-level 로 작성하고, agent 가 BAR write / mailbox 으로 변환한다.
:::
| Path | 대표 Verb | Kernel 개입 | TB 모델링 |
|------|----------|------------|----------|
| Control | `ibv_open_device` `ibv_alloc_pd` `ibv_reg_mr` `ibv_create_qp` | O (자원·권한) | 초기화 sequence + RAL |
| Data | `ibv_post_send` `ibv_post_recv` `ibv_poll_cq` | X (kernel bypass) | scoreboard + agent |

### 5.4 실패 모드 — "이 축이 빠지면 정확히 어떤 증상이 보이나"

각 축이 빠지면 시스템 레벨에서 _관찰 가능한 증상_ 이 어떻게 나타나는지를 알면, DV 환경에서 fault injection(고의로 오류/지연을 주입해 시스템 반응을 보는 검증 기법) 시나리오를 설계할 수 있습니다. 참고로 **NCCL**(NVIDIA Collective Communications Library — GPU 간 all-reduce 등 집합 통신을 수행하는 라이브러리; AMD 판은 RCCL) 은 이런 통신을 실제로 수행하는 대표 소프트웨어입니다.

#### 실패 모드 1 — Kernel bypass 미적용 (예: TCP 로 같은 워크로드)

```
   AI training step 의 NCCL allreduce, 1024 GPU
                          │
                          ▼
   매 메시지마다 context switch (~500 ns)
                          │
                          ▼
   p50: 평소 1 µs → 5 µs (5× degradation)
   p99: 평소 2 µs → 50 µs (25× degradation, tail 폭주)
                          │
                          ▼
   barrier 가 _가장 느린 GPU_ 를 기다림
                          │
                          ▼
   step 시간이 _평균이 아닌 worst-case_ 에 의해 결정
                          │
                          ▼
   1024 GPU x 600 ms compute = 614 s wall  →  실제로는 ~1500 s (2.4× slowdown)
```

**관측 증상**: `nccl-tests/all_reduce_perf` 에서 latency variance 가 크고, throughput 이 fabric peak 의 30 ~ 40 % 에서 cap. DV TB 에서는 _CPU latency injection_ 시나리오로 재현 가능.

#### 실패 모드 2 — Zero-copy 미적용 (예: 일반 socket-buf 통신)

100 Gbps 양방향 = 25 GB/s 의 송수신 memcpy. DDR4 한 채널 대역폭이 ~25.6 GB/s 이므로:

```
   네트워크 처리에 DDR 한 채널 통째로 점유
                  │
                  ▼
   application 의 메모리 대역폭이 0 으로 수렴
                  │
                  ▼
   `numactl --membind` 으로 봐도 application 이 cache 에만 의존
                  │
                  ▼
   working set > L3 cache 이면 throughput 0 (사실상 hang)
```

**관측 증상**: `perf stat` 으로 본 memory bandwidth 가 saturated, application 의 IPC 가 0.1 이하로 떨어짐, top 에서 `kworker` 또는 `ksoftirqd` 가 CPU 점유. DV 관점: scoreboard 의 buffer copy count 가 0 이 아닌 시나리오를 시각화.

#### 실패 모드 3 — Transport offload 미적용 (예: SW PSN/ACK)

```
   HCA 가 PSN/ACK 를 SW 에 위임
                  │
                  ▼
   CPU 코어 4~8 개 통째로 통신 처리에 점유 [Mellanox WP, 2014]
                  │
                  ▼
   64 코어 서버에서 12 % 의 코어가 _학습_ 이 아닌 _통신_ 에 소진
                  │
                  ▼
   동일 GPU 클러스터에서 1024-GPU job 의 effective throughput 이
   12 % 의 코어 손실만큼 추가로 감소
```

**관측 증상**: `mpstat 1` 에서 특정 코어들이 100 % `sys` 점유. iWARP 가 실패한 정확한 이유.

:::note[Internal (Confluence: RDMA AI Workload Performance Modeling, id=98795521 / 98140444)]
AI workload 관점에서 step time = compute time + comm time 일 때, RDMA 가 없으면 comm time 이 compute time 의 _배수_ 가 되어 학습 자체가 _경제성_ 을 잃는다.
사내 모델링에서도 1024-GPU 학습 시 comm overhead 가 25 % 이내로 들어와야 손익분기점이라는 분석.
:::
### 5.5 어울리는 워크로드 / 어울리지 않는 워크로드

| 워크로드 | RDMA 적합성 | 이유 |
|---------|------------|------|
| **HPC MPI Allreduce** | ★★★★★ | 작은 latency, 반복 패턴, 동기 |
| **AI training all-to-all** | ★★★★★ | 동일 |
| **분산 KV (Memcached, Redis-like)** | ★★★★ | Small message, 짧은 latency |
| **분산 storage (NVMe-oF)** | ★★★★★ | Block 크기 transfer, kernel bypass 효과 큼 |
| **일반 웹 서비스 (HTTP)** | ★★ | RDMA 의 setup 비용이 connection 짧은 워크로드에 비해 큼 |
| **WAN (대륙간)** | ★ | RDMA reliability 는 LAN/DC 가정 |

### 5.6 인접 영역 — AI Server, NRT, GPUBoost

:::note[Internal (Confluence: AI Servers, RDMA for NRT, Latest GPUBoost Specification)]
사내 RDMA-IP 의 운용 환경은 **AI training / inference 노드** (예: NVIDIA DGX, AMD MI325X) 와 **NRT (Non-RDMA Transport) fallback** 시나리오를 모두 포함한다.

- **AI Servers** — RCCL/NCCL allreduce, all-to-all, scatter/gather 가 핵심. RDMA-IP 는 GPU peer-memory 를 IOVA 로 노출하기 위해 **MR Large MR 모드** 를 자주 사용한다 (참조: M05).
- **RDMA for NRT** — RDMA QP 를 사용할 수 없는 경로 (예: CPU-only flow) 를 위해 IP 가 fallback path 를 노출. 검증에서는 두 path 가 **동일 application 시맨틱** 을 보장하는지 비교 scoreboard 로 확인.
- **GPUBoost spec** — 사내 RNIC 의 외부 spec. opcode·MTU·QP 수 등의 cap 은 spec 에서 직접 인용한다.
:::
### 5.7 RDMA Communication Lifecycle — 한 장 그림

지금까지 본 객체와 verb 가 _실제 통신 한 번_ 에서 **어떤 순서로 등장하는가** 를 끝에서 끝으로 따라갑니다. 다음 모듈들이 각 구간을 잘게 쪼개 다루므로, 이 그림은 **앞으로의 모듈을 어디에 끼워 읽을지** 의 지도로 사용하세요.

```
   ┌── Phase 1. Initialization ───────────────────────────────────────────┐
   │   ibv_open_device  →  ibv_alloc_pd  →  ibv_reg_mr  →  ibv_create_cq  │
   │   ibv_create_qp(PD, CQ, service_type=RC)                              │
   │   Modify(Reset → Init)        ← pkey_index, port, access_flags       │
   │   상태: QP=Init, MR 등록 완료, CQ 준비됨                                │
   └──────────────────────────────────────────────────────────────────────┘
                                ↓ (RC 만 해당)
   ┌── Phase 2. Connection Setup (RC service) — Module 03, 04 ────────────┐
   │   RDMA CM (또는 OOB) 으로 양 끝이 교환:                                  │
   │       peer QPN, init PSN, MTU, retry/timeout, rkey                    │
   │   Modify(Init → RTR)          ← peer QPN, rq_psn, path_mtu, ah_attr   │
   │   Modify(RTR → RTS)           ← sq_psn, timeout, retry_cnt            │
   │   상태: QP=RTS (양방향 data 가능)                                       │
   │                                                                       │
   │   UD 는 Phase 2 가 가벼움 — Init → RTR (Q_Key 만) → RTS, AH 만 더 만들면 │
   │   임의 peer 로 SEND. Connection 자체는 안 맺음.                          │
   └──────────────────────────────────────────────────────────────────────┘
                                ↓
   ┌── Phase 3. Data Transfer — Module 05, 06, 07 ────────────────────────┐
   │   ① ibv_post_send / ibv_post_recv  → SQ/RQ 에 WQE 쓰기                 │
   │   ② Doorbell MMIO write           → RNIC 가 새 WQE 알아챔                │
   │   ③ RNIC: WQE fetch, MPT/MTT 로 access 검증, DMA read payload        │
   │   ④ RNIC: BTH+xTH 패킷 만들어 wire 로 송신 (PSN 부여)                    │
   │   ⑤ 상대 RNIC: PSN/rkey/range 검증 → DMA write to peer MR             │
   │   ⑥ ACK / NAK / READ-RESP / ATOMIC-ACK (AETH + MSN)                  │
   │   ⑦ 요청자 RNIC: WQE retire → CQE 생성                                │
   │   ⑧ ibv_poll_cq → user 가 완료 회수                                    │
   │                                                                       │
   │   장애 시:                                                              │
   │     packet/ack drop → timer 만료 → Go-Back-N 재전송 (Module 07)          │
   │     receiver RECV 없음 → RNR NAK → min_rnr_timer 후 재전송               │
   │     rkey/range 위반 → NAK + QP→Err                                    │
   └──────────────────────────────────────────────────────────────────────┘
                                ↓
   ┌── Phase 4. Disconnection / Cleanup ──────────────────────────────────┐
   │   (RC) RDMA CM: rdma_disconnect → DREQ / DREP (UD QP1 의 MAD)         │
   │   Modify(Any → Reset) — in-flight WR flush + WC FLUSH_ERR             │
   │   ibv_destroy_qp → ibv_destroy_cq → ibv_dereg_mr → ibv_dealloc_pd     │
   │   ibv_close_device                                                    │
   └──────────────────────────────────────────────────────────────────────┘
```

#### Phase 별 책임자

| Phase | 누가 | 무엇을 | 어디서 자세히 |
|------|------|--------|------------|
| **1. Init** | host SW (control verb) | 자원 할당, MR pin, QP/CQ 생성, kernel/IOMMU 매핑 | M04 §3, M05 |
| **2. Setup** | host SW + UD QP1 (control plane) | metadata 합의 — peer QPN, init PSN, MTU, retry, rkey | M03 §5.9, M04 §3 |
| **3. Data** | RNIC hardware (data verb) | doorbell, WQE fetch, DMA, packet build, PSN/ACK | M05 §4, M06 전체, M07 |
| **4. Teardown** | host SW + RNIC | flush in-flight, dereg, dealloc | M04 §5.3 (FSM) |

#### RC vs UD 의 lifecycle 차이 (한 표)

| 단계 | RC | UD |
|------|----|----|
| Phase 1 (init) | 동일 | 동일 |
| Phase 2 (setup) | **RDMA CM 으로 양 끝 metadata 합의 + Modify(RTR/RTS)** | Init → RTR(Q_Key) → RTS 만. 1:1 합의 없음 |
| 매 SEND 마다 | 사전에 합의된 peer QPN(목적지 QP 번호)/PSN 사용 | **AH (Address Handle — 보낼 상대의 주소 정보를 미리 묶어둔 핸들)** 가 dest LID/QPN 을 매번 지정 |
| Phase 3 (data) | SEND / WRITE / READ / ATOMIC 전부 | SEND only (write_with_imm 일부 변형 가능) |
| ACK / retry | RNIC 가 자동 처리 | 없음 — drop = 메시지 loss |
| Phase 4 (disconnect) | DREQ/DREP MAD + cleanup | RTS 에서 바로 Reset 가능 (peer 통보 없음) |

:::note[왜 이 lifecycle 을 한 번에 봐야 하나]
Phase 1·4 는 **kernel** 이 처리, Phase 2 는 host SW + UD QP1 (control plane), Phase 3 만 **RNIC hardware** 의 데이터 패스 — 검증 환경도 이 경계를 따라 분리됩니다. 사내 RDMA-TB 는 Phase 1·2 를 sequence 의 _init_phase_ 로, Phase 3 을 _io_phase_ 로 분리해 대다수 시나리오가 Phase 3 의 변형이라는 사실을 반영합니다.
:::
---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'RDMA = 빠른 TCP']
**실제**: RDMA 는 transport semantics 가 아예 다릅니다. TCP 는 byte stream + 양 끝의 user-space socket. RDMA 는 message + 원격 메모리 주소 (rkey + virtual address) 모델. RC service 의 reliability 도 hardware ACK/NAK + PSN + retry 로 구현되며, TCP 의 reliability 와는 다른 mechanism. **"빠른 TCP" 가 아니라 "원격 메모리 access"** 입니다.<br>
**왜 헷갈리는가**: "high-performance networking" 카테고리에 같이 묶이고, RoCEv2 가 IP/UDP 위에 올라가서.
:::
:::danger[❓ 오해 2 — 'RDMA-CM 도 RDMA 다']
**실제**: RDMA-CM 자체는 _TCP 위에서 동작하는 "RDMA connection 만들기" 프로토콜_ 입니다. 노드끼리 (rkey, remote_va, QPN) 같은 메타데이터를 교환하는 control path. 데이터는 그 후 RDMA QP 로 갑니다. <br>
**왜 헷갈리는가**: 이름이 RDMA 로 시작.
:::
:::danger[❓ 오해 3 — 'RDMA 는 throughput 이 빠른 거다']
**실제**: TCP/IP 도 100 Gbps 라인레이트 자체는 잘 채웁니다. RDMA 의 차별점은 **CPU 점유율** 과 **tail latency** 입니다. 1 µs vs 10 µs 는 `p99.9` 에서 큰 차이.<br>
**왜 헷갈리는가**: 마케팅 자료가 "fast" 만 강조.
:::
:::danger[❓ 오해 4 — 'rkey 만 알면 안전']
**실제**: rkey 가 노출되면 원격 노드가 임의 메모리에 RDMA WRITE 가능 → MR 의 access flag (Local R/W, Remote R/W/Atomic) 와 PD 격리는 **spec 가 아니라 구현 책임**. 검증 시 access flag 위반 시 어떤 CQE 가 떨어지는지 직접 확인.
:::
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

:::caution[실무 주의점]
- "RDMA 빠르다" 는 **latency / CPU 점유율**. throughput 만 보면 TCP 도 라인레이트 가능.
- **RDMA-CM ≠ RDMA**. RDMA-CM 은 TCP 위 connection setup.
- 보안: rkey 노출 = remote write 가능 → MR access flag 와 PD 격리는 구현 책임.
:::
### 7.1 자가 점검 — 이 모듈을 진짜로 이해했는지

다음 3 문제를 _책 안 보고_ 풀어보세요. 답이 막히면 본문 어디로 돌아가야 하는지가 보일 겁니다.

:::tip[🤔 Q1 — 1024-GPU 학습의 step time 계산 (Bloom: Analyze)]
1024 H100 GPU, 매 step compute 600 ms, gradient 32 GB allreduce.
- **(a)** 100 GbE TCP/IP 로 통신하면 step time 은 대략 얼마? 왜?
- **(b)** 100 GbE RoCEv2 로 통신하면? 왜?
- **(c)** 두 시나리오에서 _가장 큰 차이_ 가 throughput 인가 latency variance 인가? 한 줄로 답.

<details>
<summary>정답</summary>

- (a) ~6.4 s (10× compute) — TCP/IP 는 100 Gbps 의 ~30~40% 만 실제로 활용, 그리고 CPU 점유 → 결과적으로 step time 이 compute 의 10 배.
- (b) ~0.4 s — RoCEv2 는 fabric peak 의 ~92% 활용 (NCCL all_reduce_perf 측정), compute 와 overlap 가능.
- (c) **Latency variance (p99 tail)**. 1024-GPU barrier 는 _가장 느린 GPU_ 가 step 시간을 결정하므로 throughput 보다 _tail latency_ 가 더 치명적.

</details>
:::
:::tip[🤔 Q2 — opcode 선택 (Bloom: Apply)]
노드 B 의 application 이 "데이터가 도착했음" 을 알 _필요가 없는_ 경우 (예: 주기적으로 메모리를 polling) A 는 어떤 opcode 를 써야 가장 효율적일까? 그리고 알 _필요가 있는_ 경우는?

<details>
<summary>정답</summary>

- **알 필요 없음** → **RDMA WRITE** (일반). B 의 CPU 안 깨움, CQE 도 B 측에 안 생김.
- **알 필요 있음** → **WRITE_WITH_IMMEDIATE** (WRITE 의 효율 + 통지 결합) 또는 **SEND** (RECV WQE 가 미리 필요, 메시지 모델).

</details>
:::
:::tip[🤔 Q3 — DV scoreboard 설계 (Bloom: Evaluate)]
당신이 RDMA-TB scoreboard 를 설계한다. _zero-copy_ 가 깨졌음 (예: HCA RTL bug 로 user buffer 가 아닌 임시 buffer 를 거침) 을 어떤 measurement 로 감지할 수 있을까? 한 줄로.

<details>
<summary>정답</summary>

Host memory model 의 **buffer access trace** 에서 user-MR 영역이 아닌 _다른 주소_ 가 등장하는지 검사. 또는 DMA channel 의 source/destination 주소가 MR base ± len 범위 밖이면 fail. 더 단순하게는 _DMA 사이즈 ≠ 메시지 사이즈_ 면 copy 가 끼었다는 신호.

</details>
:::
### 7.2 출처

**Internal (Confluence)**
- `[RDMA] basic` (id=934608922) — 본 모듈 §1.1, §4.1 의 3 축 모티베이션과 100 Gbps 코어 점유 통계
- `RDMA AI Workload Performance Modeling` (id=98795521 / 98140444) — §5.4 실패 모드의 step time 모델링
- `[RDMA] SEND` (id=973439000) — §3 의 opcode 별 시맨틱
- `RDMA Verbs (basic)` (id=32178388) — §5.3 control vs data path
- `NCCL official docs summary` (id=99779475) — §1.1 의 allreduce throughput 측정 컨텍스트

**External**
- IBTA, *InfiniBand Architecture Specification Volume 1, Release 1.7* (2023)
- IBTA, *Annex A17: RoCEv2 — RDMA over Converged Ethernet v2*
- NVIDIA/Mellanox, *RoCE vs iWARP Competitive Analysis WP* (2014; rev. 2024)
- *RoCEv2 vs InfiniBand vs iWARP for Large-Scale Training Fabrics* — AI Journal (2025)
- *Demystifying NCCL: An In-depth Analysis of GPU Communication Protocols and Algorithms* — arXiv:2507.04786 (2025)
- *RDMA over Converged Ethernet* — Wikipedia (revision 2025) — latency 1.3 µs vs 3 µs 인용

---

## 다음 모듈

→ [Module 02 — InfiniBand 프로토콜 스택](../02_ib_protocol_stack/): RDMA 의 가정 위에서 IB 가 패킷을 어떻게 그렸는지. LRH/GRH/BTH/xTH 와 ICRC/VCRC 의 분리.

[퀴즈 풀어보기 →](../quiz/01_rdma_motivation_quiz/)
