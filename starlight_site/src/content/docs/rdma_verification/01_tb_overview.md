---
title: "Module 01 — TB Overview & Multi-Node 구조"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Diagram** RDMA-TB 가 두 노드(host) 간 RDMA 트랜잭션을 어떻게 모델링하는지 그릴 수 있다.
- **Identify** `vrdmatb_top_env` 가 컨테이너로 가지는 sub-env 5종을 식별할 수 있다.
- **Differentiate** `lib/base` / `lib/ext` / `lib/external` / `lib/submodule` 의 분류 기준을 설명할 수 있다.
- **Trace** 한 RDMA WRITE 가 두 노드 + 횡단 env 를 가로지르는 경로를 추적할 수 있다.
:::
:::note[사전 지식]
- [RDMA Module 04 — Service Types & QP FSM](../../rdma/04_service_types_qp/) (RC vs OPS/SR 의 의미)
- [UVM Topic — Environment / Agent](../../uvm/) (env 계층, agent 패턴)
- DMA / PCIe 기본 — host memory 모델
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — RDMA-TB 가 _2 노드_ 인 이유

먼저 용어부터. **RDMA**(Remote Direct Memory Access — 한 컴퓨터가 상대 컴퓨터의 메모리에 CPU/OS 개입 없이 직접 읽고 쓰는 기술)는 네트워크 카드(**NIC**, network interface card — 네트워크 통신을 담당하는 하드웨어)가 host CPU 를 거치지 않고 상대 노드 메모리에 데이터를 옮깁니다. 여기서 **DUT**(Design Under Test — 검증 대상 하드웨어 설계)는 우리가 검증하려는 RDMA IP 이고, **DV**(Design Verification — 설계가 명세대로 동작하는지 검증하는 작업)는 그 검증 활동, **TB**(testbench — DUT 에 자극을 주고 출력을 검사하는 검증 환경)는 그 환경입니다.

일반 ASIC DV: DUT 한 개 + agent(자극을 주고 관찰하는 UVM 검증 컴포넌트 묶음) + scoreboard(DUT 출력과 "정답" 기대값을 비교하는 컴포넌트). 단순.

RDMA-TB: DUT _2 개_ (NODE 0 + NODE 1) + 양쪽 host 메모리 + 가운데 네트워크 + 횡단 scoreboard. _훨씬 복잡_.

왜? **RDMA 의 정의가 "양 끝 node 의 hardware 가 _서로_ 통신"**:
- Send 측만 검증하면 _packet(네트워크로 오가는 데이터 묶음 한 단위) 발신_ 만 OK 인지 확인. _수신_ 의 정확성 누락.
- Recv 측만 검증하면 _packet 수신_ 만 OK. _발신_ 의 정확성 누락.
- _두 NIC 사이의 protocol consistency(프로토콜 일관성 — 두 끝이 같은 통신 규약을 어긋남 없이 따르는 것)_ (PSN(Packet Sequence Number — 패킷 순서를 매기는 일련번호) / ACK(acknowledgement — 잘 받았다는 응답) / retry(실패 시 재전송) / flow control(수신 측이 못 따라오면 송신 속도를 늦추는 흐름 제어)) 는 _양쪽_ 동시 보는 환경에서만 검증.

또한 _interoperability_: 같은 RTL 의 두 instance 가 _서로_ 보낸 패킷을 처리. 한 instance 의 _Tx bug_ 가 다른 instance 의 _Rx_ 에서 catch 가능.

:::note[메커니즘 — "같은 RTL 두 instance" 가 protocol consistency 를 잡는 구조]
dual-node 는 같은 DUT RTL 을 **두 번 elaborate** 해 NODE 0, NODE 1 두 instance 로 두고, 둘의 wire 인터페이스(TX/RX)를 _서로 교차_ 연결합니다 — NODE 0 의 TX 출력이 (네트워크 모델을 거쳐) NODE 1 의 RX 입력이 되고, 반대도 마찬가지인 **loopback 결선**입니다. 이렇게 하면 한쪽이 만든 _실제 패킷_(PSN, ACK, retry, flow-control 신호 포함)이 상대의 _실제 수신 로직_ 으로 그대로 들어갑니다. 그래서 TB 가 패킷을 "흉내" 내는 게 아니라, **양쪽 hardware 가 직접 서로의 출력에 반응** 하므로 PSN 연속성·ACK 타이밍·retry 협상 같은 _두 끝의 합의가 필요한 속성_ 이 자동으로 검증됩니다. 한 instance 의 TX 버그는 상대 instance 의 RX 검증에서, RX 버그는 상대의 retry/timeout 으로 드러납니다 — 단일 노드 TB 로는 한쪽을 model 로 대체해야 해서 놓치는 영역입니다.
:::

**Trade-off**: dual-node 가 _2 배 시뮬 시간_ — 대신 _system-level bug catch_ 능력 압도적.

RDMA 검증은 본질적으로 **두 노드 간 통신** 의 검증입니다. 한 노드에서 보낸 데이터가 다른 노드의 메모리에 정확히 도착하는지 (**1-side**(상대 CPU 개입 없이 한쪽이 상대 메모리를 직접 read/write — RDMA Write/Read), **2-side**(양쪽 CPU 가 모두 관여 — 한쪽 Send, 상대가 미리 준비한 버퍼로 Recv) 두 통신 방식) 확인해야 하므로, TB 자체가 multi-node 모델을 그대로 반영해야 합니다.

이 모듈을 건너뛰면 이후 모든 모듈에서 만나는 `node[0]/node[1]`, `data_env`, `dma_env`, `ntw_env` 같은 이름이 그저 "디렉토리 명" 으로 보이고, 디버그 로그의 `[node][qp]` 키가 어디서 왔는지 모르게 됩니다. 반대로 5-부 구조 (두 노드 + 네트워크 + 횡단 검증) 를 잡고 나면, 모든 후속 모듈이 "이 5 영역 중 어느 영역의 디테일" 인지로 정렬됩니다.

---

## 2. Intuition — 두 사무실, 한 도로, 감시 카메라

:::tip[💡 한 줄 비유]
RDMA-TB ≈ **두 개의 동일한 사무실 + 가운데 도로 + 상시 감시 카메라**.<br>
각 사무실(`vrdma_node_env`) 은 host 메모리, IP shell, agent 가 모두 들어 있어 자체적으로 verb(RDMA 의 동작 명령 단위 — Write/Read/Send/Recv 등 "무엇을 하라"는 요청)를 발행한다. 가운데 도로(`ntw_env`) 는 두 사무실을 잇는 네트워크 패킷을 본다. 그리고 가운데에 매달린 감시 카메라 3대 (`data_env` / `dma_env` / 검증 scoreboard) 가 두 사무실을 동시에 본다 — "양쪽 메모리가 일치하는가?", "DMA 가 기대된 위치/순서로 갔는가?", "트랜잭션 의미가 보존됐는가?"
:::
### 한 장 그림 — Top env 의 5-부 구조

```d2
direction: down

TBTOP: "vrdmatb_top_env" {
  N0: "node[0] (vrdma_node_env)" {
    N0H: "host mem"
    N0I: "ip shell"
    N0A: "agent\ndriver / sequencer / handlers"
  }
  CROSS: "횡단 검증 (cross-node)" {
    DATA: "data_env\nmemory compare" { style.stroke: "#1a73e8"; style.stroke-width: 2 }
    DMA: "dma_env\nc2h_tracker" { style.stroke: "#1a73e8"; style.stroke-width: 2 }
    NTW: "ntw_env\npacket monitor" { style.stroke: "#1a73e8"; style.stroke-width: 2 }
  }
  N1: "node[1] (vrdma_node_env)" {
    N1H: "host mem"
    N1I: "ip shell"
    N1A: "agent\ndriver / sequencer / handlers"
  }
}

TBTOP.N0.N0A -> TBTOP.CROSS: "AP"
TBTOP.N1.N1A -> TBTOP.CROSS: "AP"
TBTOP.N0.N0I <-> TBTOP.N1.N1I: "network\nRDMA packet flow"
TBTOP.CROSS.NTW -> TBTOP.N0.N0I: "monitor" { style.stroke-dash: 4 }
TBTOP.CROSS.NTW -> TBTOP.N1.N1I: "monitor" { style.stroke-dash: 4 }
```

> 횡단 env 는 `[node][qp]` 키로 모든 트랜잭션을 추적합니다.

### 왜 이 디자인인가 — Design rationale

세 가지가 동시에 풀려야 했습니다.

1. **노드 추가가 단순해야** — `cfg.num_nodes++` 만으로 동일 구조 재인스턴스화 → `vrdma_node_env` 가 한 노드의 모든 host+ip 컴포넌트를 캡슐화.
2. **횡단 검증은 노드 수와 무관해야** — 두 노드 간 데이터 비교, DMA 추적, 패킷 모니터링은 본질적으로 "여러 노드를 한꺼번에 보는" 컴포넌트 → 노드와 별도 sub-env (`data_env`, `dma_env`, `ntw_env`) 로 분리.
3. **모든 디버그/추적은 동일 키 형태로** — 모든 횡단 컴포넌트가 `[node][qp]` associative array 키를 공유 → 디버그 로그가 노드/QP 단위로 자동 정렬.

이 세 요구의 교집합이 5-부 구조 (Node × 2 + 횡단 env × 3) 입니다.

---

## 3. 작은 예 — 1 KB WRITE 가 TB 를 가로지르는 궤적

가장 단순한 시나리오 — `rdma_basic_test` 가 `num_nodes=2` 로 실행되고 `node[0]` 이 `node[1]` 에 1 KB RDMA WRITE 를 합니다.

> 흐름에 나오는 핵심 용어: **WQE**(Work Queue Entry — SW 가 "이 verb 를 처리하라"고 하드웨어에게 남기는 작업 지시 항목), **SQ**(Send Queue — 보낼 작업(WQE)을 쌓아두는 큐), **doorbell**(SW 가 "큐에 새 작업을 넣었다"고 하드웨어를 깨우는 신호 — 보통 특정 레지스터에 쓰기), **MMIO**(Memory-Mapped I/O — 하드웨어 레지스터를 메모리 주소처럼 읽고 써서 제어하는 방식), **QID**(Queue ID — DMA 트랜잭션이 어느 큐/서브시스템에 속하는지 식별하는 번호), **C2H**(Card-to-Host — 카드(DUT)가 host 메모리 방향으로 일으키는 DMA), **CQE**(Completion Queue Entry — 한 작업이 끝났음을 알리는 완료 항목), **AP**(Analysis Port — UVM 에서 한 컴포넌트가 만든 transaction 을 여러 구독자에게 동시에 뿌리는 1:N 방송 통로).

```d2
shape: sequence_diagram

TS: "top_seq"
DRV0: "node[0].driver"
WH: "write_handler"
C1: "1side_compare"
CT: "c2h_tracker"
DUT0: "DUT IP_0"
PM: "pkt_monitor\n(ntw_env)"
DUT1: "DUT IP_1"
MEM1: "host mem[1]"
CQH: "cq_handler"
SB: "data_scoreboard"

TS -> DRV0: "RDMAWrite(.t_seqr=seqr[0])"
DRV0 -> WH: "issued_wqe_ap.write(cmd)"
WH -> C1: "write 큐에 enqueue"
WH -> CT: "expected PA 계산"
DRV0 -> DUT0: "doorbell"
DUT0 -> PM: "pkt"
PM -> DUT1: "pkt"
DUT1 -> MEM1: "payload DMA"
DUT1 -> CT: "C2H 매칭"
MEM1 -> C1: "mem[0] vs mem[1] 비교"
DUT1 -> CQH: "pkt 도착 / completion" { style.stroke-dash: 4 }
CQH -> DRV0: "cqe_ap" { style.stroke-dash: 4 }
DRV0 -> SB: "completed_wqe_ap.write(cmd)"
```

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | test → top_vseqr | `RDMAWrite(.t_seqr(seqr[0]))` 발행 | top sequence 가 노드 0 의 seqr 를 명시적으로 지정 |
| ② | `node[0].driver` | WQE post 후 `issued_wqe_ap.write(cmd)` | 발행 정보를 모든 횡단 subscriber 에게 broadcast |
| ② | `write_handler` | opcode 따라 1side_compare / c2h_tracker 로 라우팅 | stateless forwarder — state 없음 |
| ③ | driver | DUT IP shell 로 doorbell MMIO | DUT 가 SQ 에서 WQE fetch (QID 14–17) |
| ④ | DUT IP_1 | host mem[1] 에 payload DMA | C2H QID 8–9 로 가시화 |
| ⑤ | `c2h_tracker` | 받은 C2H 의 (addr, size) 가 expected PA 와 일치하는지 | DMA 정합성 검증 (M10) |
| ⑥ | `1side_compare` | mem[0] 의 source 와 mem[1] 의 dest 를 byte-byte 비교 | 데이터 정합성 검증 (M08) |
| ⑦ | `cq_handler` | CQE 도착 → `cqe_ap.write(cqe)` | comparator 들에게 완료 통지 |
| ⑧ | driver | `completed_wqe_ap.write(cmd)` | scoreboard 에서 outstanding 정리 (단, ErrQP 면 skip) |

:::note[여기서 잡아야 할 두 가지]
**(1) 한 verb 가 driver→handler→3개 횡단 env 로 1:N broadcast** — 이게 [Module 04 AP 토폴로지](../04_analysis_port_topology/) 의 핵심 패턴.<br>
**(2) `[node][qp]` 키가 모든 횡단 env 에 공통** — 여기서 **QP**(Queue Pair — RDMA 통신의 기본 단위로, 보낼 작업을 쌓는 Send Queue 와 받을 작업을 쌓는 Receive Queue 한 쌍; 통신 상대마다 하나씩 만든다)는 한 통신 채널을 가리킵니다. 디버그 시 한 트랜잭션을 `node 0, qp X` 로 좁히면 1side_compare / c2h_tracker / data_scoreboard 의 로그가 동시에 정렬됩니다.
:::

:::note[메커니즘 — analysis port 의 1:N broadcast 가 실제로 어떻게 전달되나 (TLM 기초)]
UVM 의 **analysis port (`uvm_analysis_port`)** 는 한 producer 가 만든 transaction 을 등록된 _모든_ subscriber 에게 동시에 뿌리는 1:N 채널입니다. 동작은 단순합니다: subscriber 쪽은 `uvm_analysis_imp`(또는 export)를 producer 의 port 에 connect 해 두고, producer 가 `ap.write(txn)` 을 호출하면 — port 는 자기에게 **connect 된 imp 들의 리스트를 순회하며 각각의 `write()` 콜백을 차례로(동기적으로) 호출** 합니다. 즉 `write()` 한 번이 N 개의 subscriber `write()` 로 fan-out 되고, 모두 같은 transaction 핸들을 보게 됩니다. 반환은 즉시(non-blocking) — analysis port 는 handshake 나 backpressure 가 없습니다(그래서 monitoring 용). subscriber 가 0 개여도 에러가 아니며, 이 느슨한 결합 덕분에 scoreboard·coverage·tracker 를 자유롭게 붙였다 떼었다 할 수 있습니다. 위 표의 "1:N broadcast" 가 바로 이 `write()→connected imp들` 전개입니다. (자세한 토폴로지는 [Module 04](../04_analysis_port_topology/).)
:::
---

## 4. 일반화 — 노드 격리 + 횡단 검증 패턴

### 4.1 두 가지 격리 원칙

| 원칙 | 적용 대상 | 이유 |
|------|----------|-----|
| **노드 격리** | `vrdma_node_env` 가 한 노드의 모든 host + ip 컴포넌트를 캡슐화 | 노드 수 변경 시 단순 인스턴스화 |
| **횡단 검증 분리** | `data_env` / `dma_env` / `ntw_env` 는 두 노드를 가로지르는 검증 → 노드와 분리되어 top env 직속 | 노드 수와 무관하게 1 인스턴스, 모든 노드 AP 를 구독 |

### 4.2 노드 간 통신 모델

```d2
direction: down

NODES: "두 노드" {
  direction: right
  Node0: "Node 0" {
    H0: "Host Mem 0"
    IP0: "IP Shell 0"
    H0 <-> IP0
  }
  Node1: "Node 1" {
    H1: "Host Mem 1"
    IP1: "IP Shell 1"
    H1 <-> IP1
  }
  Node0.IP0 <-> Node1.IP1: "Network"
}

CROSS: "횡단 검증 env" {
  direction: right
  Net: "ntw_env"
  Data: "data_env\n1side/2side/imm compare"
  Dma: "dma_env\nc2h_tracker"
}

NODES.Node0.IP0 -> CROSS.Net: "monitor" { style.stroke-dash: 4 }
NODES.Node1.IP1 -> CROSS.Net: "monitor" { style.stroke-dash: 4 }
NODES.Node0.H0 -> CROSS.Data: { style.stroke-dash: 4 }
NODES.Node1.H1 -> CROSS.Data: { style.stroke-dash: 4 }
NODES.Node0.IP0 -> CROSS.Dma: "C2H DMA" { style.stroke-dash: 4 }
NODES.Node1.IP1 -> CROSS.Dma: "C2H DMA" { style.stroke-dash: 4 }
```

- **data_env** — 양 노드의 호스트 메모리 영역을 비교 (write/read/send/recv 정합성). 비교를 수행하는 컴포넌트를 **comparator**(두 노드의 메모리/transaction 을 대조해 데이터가 일치하는지 판정하는 검증 컴포넌트)라 부릅니다.
- **dma_env** — 각 노드의 IP 가 host 로 발생시키는 C2H DMA 트랜잭션을 추적
- **ntw_env** — 두 노드 사이의 RDMA 패킷 (BTH(Base Transport Header — 모든 RDMA 패킷에 붙는 공통 전송 헤더, opcode/PSN/목적 QP 등 포함) / RETH(RDMA Extended Transport Header — Write/Read 의 원격 주소·길이·rkey) / AETH(ACK Extended Transport Header — ACK/NAK 응답 정보) / ...) 을 모니터링

이 패턴은 노드를 N 개로 확장해도 동일하게 작동합니다 — 횡단 env 는 모든 노드의 AP 를 한 번에 구독.

---

## 5. 디테일 — env 계층, 노드 모델, lib 분류

### 5.1 Top env 의 12 svh 파일

`lib/base/component/env/` 디렉토리에는 환경 계층의 12개 svh 파일이 있습니다.

```
vrdmatb_top_env.svh        ← 두 노드 + 네트워크 + RAL 통합
├── vrdma_node_env.svh     ← 한 노드의 모든 sub-env (host + ip)
│   ├── vrdma_host_env.svh ← 호스트 측 (메모리, driver 일부)
│   └── vrdma_ipshell_env.svh / vrdma_elc_env.svh ← IP shell / 엣지 logic
├── vrdma_ntw_env.svh      ← 두 노드를 잇는 네트워크
│   └── vrdma_ntw_model_env.svh / vrdma_ntw_sb_env.svh
├── vrdma_data_env.svh     ← 데이터 정합성 검증 (comparator)
├── vrdma_dma_env.svh      ← DMA 트랜잭션 검증 (c2h_tracker)
├── vrdma_lp_env.svh       ← 로컬 패킷 환경
├── vrdma_memory_env.svh   ← 메모리 시뮬레이션
├── vrdma_ral_env.svh / vrdma_mbshell_ral_env.svh ← RAL
```

> **RAL**(Register Abstraction Layer — DUT 의 제어/상태 레지스터를 UVM 객체로 모델링해 이름으로 읽고 쓰게 해주는 계층) 은 하드웨어 레지스터를 주소 대신 `reg.field.read()` 같은 추상 API 로 다루게 해, 테스트가 레지스터 맵 세부에 묶이지 않게 합니다.

이 계층의 핵심 원칙은 두 가지입니다. 먼저 **노드 격리**입니다. `vrdma_node_env` 는 한 노드의 모든 host + ip 컴포넌트를 캡슐화하기 때문에, 노드가 둘이면 `vrdma_node_env` 인스턴스도 두 개가 됩니다. 이렇게 격리해 두어야 `cfg.num_nodes` 를 변경하는 것만으로 동일 구조가 자동 재인스턴스화됩니다. 두 번째는 **횡단 검증 분리**입니다. `data_env` / `dma_env` / `ntw_env` 는 두 노드를 동시에 바라봐야 하는 검증이므로 어느 한 노드의 자식이 될 수 없습니다. 그래서 이 세 env 는 노드와 분리되어 top env 에 직속으로 배치되어 있고, 결과적으로 노드 수와 무관하게 항상 1 인스턴스만 유지되면서 모든 노드의 AP 를 구독할 수 있습니다.

### 5.2 lib 디렉토리 분류 (Confluence Submodule + 코드 검증)

`/home/jaehyeok.lee/RDMA/RDMA-TB/lib/` 는 4개 layer 로 분리되어 있습니다.

| 디렉토리 | 역할 | 예 |
|---------|------|----|
| `lib/base/` | RDMA IP-top 공통 검증 자산 (config, env, agent, comparator, tracker, sequence) | `lib/base/component/env/` |
| `lib/ext/` | 기능 확장 — congestion control, sva, error_handling 등 옵션 컴포넌트 | `lib/ext/test/error_handling/`, `lib/ext/component/congestion_control/` |
| `lib/external/` | 외부에서 가져온 IP/component (vendor IP, third-party VIP) | `lib/external/vpfc/` |
| `lib/submodule/` | sub-IP 검증 환경 (data_plane, metadata) | `lib/submodule/data_plane/crc/`, `lib/submodule/metadata/mmu/` |

:::tip[검증 가치 우선순위]
새 기능을 추가할 때 어느 layer 에 둘지 결정하는 기준:

1. **모든 RDMA IP 인스턴스에서 공통 필요** → `lib/base/`
2. **특정 feature flag 가 켜진 경우만** → `lib/ext/`
3. **외부 IP 의존** → `lib/external/`
4. **IP 의 한 sub-block 만 검증** → `lib/submodule/`
:::
### 5.3 코드 walkthrough — Top env 정의 위치

- `lib/base/component/env/vrdmatb_top_env.svh` — top env 컨테이너
- `lib/base/component/env/vrdma_node_env.svh` — 노드 env
- `lib/base/component/env/vrdma_data_env.svh` (실제 본체는 `data_env/vrdma_data_env.svh`)

#### 노드 인스턴스화

TB 는 `cfg.num_nodes` 만큼 `vrdma_node_env` 를 build 단계에서 생성합니다. 두 노드 간 모든 트랜잭션은 노드 ID (`local_node`, `remote_node`) 로 태깅되어 흐릅니다. data_env / dma_env 의 comparator/tracker 는 모두 `[node][qp]` 키 형태의 associative array 를 사용합니다.

#### 환경 분리의 효과

이 분리 구조 덕분에 노드 추가가 단순해집니다. `cfg.num_nodes++` 만으로 `vrdma_node_env` 가 N 개 자동 생성되고, 횡단 env (`data_env`, `dma_env`) 는 노드 수와 무관하게 항상 1 인스턴스를 유지하면서 늘어난 모든 노드의 AP 를 그대로 구독합니다. 즉 검증 범위는 자동으로 확장되지만 횡단 env 코드는 한 줄도 고칠 필요가 없습니다.

### 5.4 실전 — 한 테스트의 컴포넌트 인스턴스 그림

`rdma_basic_test` 가 `num_nodes=2` 로 실행될 때 인스턴스화되는 컴포넌트 (간략):

```d2
direction: down

TOP: "uvm_test_top\n(rdma_basic_test)" {
  ENV: "env\n(vrdmatb_top_env)" {
    N0: "node[0]\n(vrdma_node_env)" {
      H0: "host_env\n(vrdma_host_env)"
      I0: "ipshell_env\n(vrdma_ipshell_env)"
      A0: "agent\n(vrdma_agent)" {
        DRV: "driver\n(vrdma_driver)"
        SQR: "sequencer\n(vrdma_sequencer)"
        HND: "handlers\n(cq/send/recv/write/read_handler)"
      }
    }
    N1: "node[1]\n(vrdma_node_env)\n— 동일 구조 —"
    NTW: "ntw_env\n(vrdma_ntw_env)" {
      PM: "pkt_monitor[0,1]\n(vrdma_pkt_monitor)"
    }
    DATA: "data_env\n(vrdma_data_env)" {
      CMP: "1side / 2side / imm_compare"
      DSB: "data_scoreboard\ncqe_validation_checker"
    }
    DMA: "dma_env\n(vrdma_dma_env)" {
      C2H: "c2h_tracker"
    }
    VSEQR: "top_vseqr\n(vrdma_top_virtual_sequencer)"
  }
}
```

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '두 노드는 두 개의 별도 TB 다']
**실제**: 두 노드는 **같은** UVM env (`vrdmatb_top_env`) 의 두 인스턴스입니다 (`vrdma_node_env[0]`, `vrdma_node_env[1]`). config_db, factory, top_vseqr 는 모두 공유. 노드 간 라우팅은 sequencer 의 `t_seqr` 파라미터로 결정.<br>
**왜 헷갈리는가**: "RDMA = network = 두 호스트" 라는 일반 직관이 강해서.
:::
:::danger[❓ 오해 2 — 'data_env / dma_env 는 한 노드에 속한다']
**실제**: 두 env 는 모두 **횡단 검증** — top env 직속 (`vrdmatb_top_env` 의 자식). 양 노드의 host memory 또는 C2H DMA 를 동시에 보는 것이 본질. 한 노드 안에 두면 다른 노드 데이터 비교가 불가능.<br>
**왜 헷갈리는가**: "한 노드의 메모리를 검증" 이라는 일반적 모델 때문.
:::
:::danger[❓ 오해 3 — '`lib/ext/` 는 "extra" 의 줄임말로 미사용 코드']
**실제**: `lib/ext/` 는 **기능 확장 (extension)** — congestion control, sva, error_handling 같은 **옵션 컴포넌트**. cfg 플래그로 enable/disable. 테스트 시나리오에 따라 자주 사용됩니다.
:::
:::danger[❓ 오해 4 — '노드를 추가하려면 env 를 새로 만들어야 한다']
**실제**: `cfg.num_nodes` 만 늘리면 build_phase 에서 `vrdma_node_env` 가 N 개 자동 생성. 횡단 env 는 그대로 1 인스턴스. 대신 시퀀스가 `seqr[i]` 를 모든 노드에 대해 라우팅하도록 작성돼 있어야 함.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 시뮬 시작 시 `num_nodes` 관련 build 에러 | cfg 미설정 또는 노드 인덱스 out-of-range | `vrdma_topology_cfg.num_nodes`, build_phase 의 `for(i=0; i<num_nodes; i++)` 루프 |
| `node[1]` 의 verb 만 발행 안 됨 | top_seq 가 `t_seqr` 를 항상 `seqr[0]` 으로 보냄 | top_sequence 의 `t_seqr` 인자 |
| `data_env` 가 한 노드 데이터만 봄 | data_env 가 노드 안에 인스턴스화됨 (잘못된 위치) | env 계층 — top env 직속이어야 함 |
| 1 KB WRITE 의 mem[0] vs mem[1] 비교 실패 | comparator 가 [node][qp] 키 매칭 못 함 | qp_reg_ap 가 양 노드의 QP 모두에 도달했는지 |
| `lib/ext/congestion_control/` 의 컴포넌트가 동작 안 함 | cfg 의 enable flag off | `vrdma_cfg.has_*_chk` / 별도 ext flag |
| `lib/external/vpfc/` 가 not-found | submodule 미체크아웃 | git submodule update |
| 노드 1 추가했더니 ntw_env 가 노드 0 만 모니터 | pkt_monitor 인스턴스가 cfg.num_nodes 따라 안 늘어남 | ntw_env 의 build_phase 루프 |

---

## 7. 핵심 정리 (Key Takeaways)

- RDMA-TB 는 **두 노드 + 네트워크 + 횡단 검증 env (data/dma/ntw)** 의 5-부 구조.
- **노드 격리** (`vrdma_node_env`) + **횡단 검증 분리** (`data_env`/`dma_env`/`ntw_env`) 가 핵심 패턴.
- `lib/{base,ext,external,submodule}` 4-layer 분류 기준은 "공통 vs 옵션 vs 외부 vs sub-IP".
- 모든 횡단 env 는 `[node][qp]` 키로 트랜잭션 추적 — 후속 모듈 (M08-M11) 디버그 키.
- 한 verb 는 driver → handler → 횡단 env 로 1:N broadcast (M04 AP 토폴로지).

:::caution[실무 주의점]
- 새 횡단 검증 컴포넌트는 항상 top env 직속에 두기 — 노드 안에 두면 cross-node 비교 불가.
- 노드를 N 개로 확장 전에 모든 시퀀스가 `t_seqr[i]` 를 정확히 라우팅하는지 점검.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — Cross-node scoreboard 위치 (Bloom: Apply)]
"Node 0 가 보낸 메시지가 Node 1 메모리에 정확히 도착" 검증 컴포넌트. 어디에?

<details>
<summary>정답</summary>

**Top env 직속**.

- Node 안에 두면: 한 node 의 view 만 → cross-node 비교 불가.
- Top env 에 두면: 양 node 의 monitor AP 모두 subscribe → 양쪽 데이터 비교.

</details>
:::
:::tip[🤔 Q2 — Dual-node simulation cost (Bloom: Evaluate)]
Dual-node 가 single-node 의 _2× 비용_. 정당화?

<details>
<summary>정답</summary>

Single-node + BFM(Bus Functional Model — 실제 DUT 대신 그 인터페이스 동작만 흉내 내는 모델):
- BFM 이 _real DUT 응답_ 흉내내야 — protocol 복잡.
- BFM 의 _버그_ 가 false test pass 가능.

Dual-node:
- 두 instance 가 _서로_ 통신 → _real protocol_ check.
- 한 instance bug 가 _다른 instance_ 에서 catch.

_2× sim 비용_ vs _10× bug catch 능력_. 정당화.

</details>
:::
### 7.2 출처

**Internal (Confluence)**
- 사내 RDMA-TB ARCHITECTURE.md

---

## 다음 모듈

→ [Module 02 — Component 계층](../02_component_hierarchy/): `lib/base/component/` 의 11 하위 디렉토리를 분해.

[퀴즈 풀어보기 →](../quiz/01_tb_overview_quiz/)
