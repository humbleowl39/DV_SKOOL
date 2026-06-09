---
title: "04 — NVMe-oF over RDMA"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** NVMe-oF가 NVMe의 transport 추상화 위에서 원격 스토리지를 로컬처럼 보이게 하는 원리를 설명할 수 있다.
- **Trace** NVMe 큐 쌍(SQ+CQ) 하나가 RDMA QP 한 쌍에 매핑되고, capsule이 RDMA SEND/RECV로 운반되는 데이터 경로를 추적할 수 있다.
- **Differentiate** In-Capsule Data(ICD)와 Out-of-line(SGL + RDMA Read/Write) 전송 모델을, write/read 시나리오와 데이터 크기 기준으로 구분할 수 있다.
- **Apply** NRT DV(NVMe-oF over RDMA) 검증 환경에서 polling·shared CQ·scoreboard·recovery 같은 요소를 어떤 검증 항목에 매핑할지 적용할 수 있다.
:::
:::note[사전 지식]
- [02 — SQ/CQ 큐 메커니즘](../02_sq_cq_doorbell/), [03 — 커맨드 분류](../03_command_set_admin_io_fabric/)
- RDMA 기본 — QP(Queue Pair), SEND/RECV, RDMA Read/Write, Memory Region/SGL ([RDMA 코스](../../rdma/))
- RoCEv2가 Ethernet 위 RDMA transport라는 큰 그림
:::
---

## 1. Why care? — 스토리지를 케이블이 아니라 네트워크로

### 1.1 시나리오 — SSD가 다른 랙에 있다

데이터센터에서 컴퓨트 노드와 스토리지를 분리(**disaggregation**, 컴퓨팅 자원과 저장 자원을 별도 장비로 떼어내 네트워크로 연결하는 설계)하고 싶다고 합시다. **SSD**(Solid-State Drive, 플래시 메모리 기반 드라이브)를 각 서버에 꽂는 대신 별도 스토리지 노드에 모아두고, 네트워크로 끌어다 쓰는 구조입니다. 문제는 "원격인데 로컬만큼 빠르고 지연이 낮아야 한다"는 것입니다. 일반 네트워크 스토리지(예: **iSCSI**, SCSI 스토리지 명령을 TCP/IP 네트워크로 실어 나르는 프로토콜)는 **TCP/IP**(인터넷 표준 네트워크 프로토콜 스택) 스택과 CPU 카피 때문에 NVMe SSD의 마이크로초 지연을 다 까먹습니다. 구체적으로 그 손실은 *매 I/O마다* 쌓입니다 — 데이터가 애플리케이션 버퍼와 소켓 버퍼(커널) 사이를 CPU가 복사하고, 패킷 도착마다 인터럽트가 발생해 컨텍스트 전환을 일으키며, TCP 프로토콜 처리(시퀀스·ACK·재조립)가 CPU에서 돌아갑니다. 이 카피·인터럽트·프로토콜 처리 비용이 I/O 한 건 한 건에 더해져, 정작 SSD 매체가 마이크로초로 응답해도 그 이득이 소프트웨어 스택에서 묻혀 버립니다.

**NVMe over Fabrics(NVMe-oF)**(NVMe를 네트워크 패브릭으로 확장해 원격 스토리지를 로컬처럼 쓰게 한 사양) 가 이 문제를 풉니다. NVMe spec은 **transport layer**(명령·데이터를 실제로 운반하는 하부 전송 계층)를 추상화해 두었기 때문에, 그 위에 PCIe 대신 **RDMA**(Remote Direct Memory Access, 원격 장치가 CPU를 거치지 않고 네트워크 너머 메모리를 직접 읽고 쓰는 기술)(**InfiniBand**(고성능 RDMA 전용 네트워크)/**RoCEv2**(RDMA over Converged Ethernet v2, 일반 Ethernet 위에서 RDMA를 구현하는 방식)/**iWARP**(TCP/IP 위에서 RDMA를 구현하는 방식)), TCP, Fibre Channel을 끼울 수 있습니다. 특히 **RDMA over Fabrics**는 host CPU를 거치지 않는 **zero-copy**(데이터를 CPU가 버퍼 사이로 복사하지 않고 곧바로 전달하는 방식) 전송으로 원격 NVMe를 거의 로컬처럼 만듭니다. NRT DV 환경은 바로 이 **NVMe-oF over RDMA**(RoCEv2가 주 use-case)를 검증합니다.

이 장을 모르면 원격 스토리지 IP(NRT, NVMe RDMA Target)에서 *왜 NVMe 큐가 RDMA QP가 되는지*, *데이터가 어떻게 capsule로 운반되는지*를 설명하지 못해 검증을 시작조차 못 합니다.

---

## 2. Intuition — 한 줄 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**NVMe-oF over RDMA** ≈ **택배로 보내는 주문서와 물건**.<br>
로컬 NVMe에서는 주문판(SQ)과 픽업대(CQ)가 *같은 건물*(host memory)에 있었습니다. NVMe-oF에서는 셰프가 *다른 도시*에 있어, 주문서(NVMe 명령 64B)를 **capsule**이라는 봉투에 담아 RDMA SEND로 부칩니다. 작은 물건은 봉투 안에 같이 넣고(**In-Capsule Data**), 큰 물건은 봉투엔 주소표(SGL)만 넣고 본체는 RDMA Read/Write로 따로 운송(**Out-of-line**)합니다.
:::

### 한 장 그림 — NVMe 큐 쌍 = RDMA QP 한 쌍

```d2
direction: right

HOST: "**Host** (initiator)" {
  HQP: "RDMA QP\n= NVMe 큐 쌍\n(SQ + CQ)"
}

FABRIC: "**RDMA Fabric**\n(RoCEv2 / Ethernet)"

TARGET: "**Target controller**\n(NVMe RDMA Target)" {
  TQP: "RDMA QP"
  SSD: "NVMe SSD"
  TQP -> SSD
}

HOST.HQP -> FABRIC: "capsule (SEND/RECV)\nNVMe cmd 64B + 부속"
FABRIC -> TARGET.TQP
TARGET.TQP -> FABRIC: "RDMA Read/Write (data)\n+ completion capsule"
FABRIC -> HOST.HQP
```

여기서 **host**(명령을 보내는 쪽, initiator)와 **target controller**(원격에서 명령을 받아 SSD를 제어하는 쪽)가 RDMA 패브릭을 사이에 두고 마주봅니다. 핵심 매핑: **RDMA QP 한 쌍 = NVMe 큐 쌍(SQ+CQ) 하나**. **control-plane**(데이터 전송이 아니라 연결 수립·설정을 담당하는 제어 경로)(Connect/Disconnect/Property/Auth)도 모두 capsule 형태로 이 QP 위를 흐릅니다.

---

## 3. 작은 예 — 작은 write 한 건 (In-Capsule Data)

가장 단순한 데이터 경로: 작은 write 데이터가 capsule 안에 inline으로 실려 RDMA SEND 한 번으로 끝나는 경우.

### 단계별 다이어그램

```d2
direction: down

S1: "**① host**: capsule 구성\nNVMe Write cmd(64B) + write data\n(작으므로 inline = ICD)"
S2: "**② RDMA SEND**: capsule을\ntarget QP로 전송 (한 번)"
S3: "**③ target**: capsule 수신\ncmd 디코드 + inline data를\nSSD에 write"
S4: "**④ target → host**: completion capsule\n(RDMA SEND) → host CQ에 반영"
S1 -> S2 -> S3 -> S4
```

### 세 가지 전송 모델

| Model | 설명 | NRT-TB 시각화 |
|---|---|---|
| **In-Capsule Data (ICD)** | 작은 write 데이터를 capsule 안에 inline (RDMA SEND 한 번) | `NRT_TB/docs/img/nvmeof-write-icd-flow.svg` |
| **Out-of-line** | SGL + RDMA Read/Write로 큰 데이터를 별도 전송 | `NRT_TB/docs/img/nvmeof-write-large-flow.svg` |
| **Read** | Capsule(cmd) → RDMA Write(data) → Capsule(completion) | `NRT_TB/docs/img/nvmeof-read-flow.svg` |

### 왜 두 모델인가

작은 데이터를 매번 별도 RDMA Read/Write로 옮기면 왕복 지연이 낭비입니다. 그래서 작은 write는 capsule 봉투 안에 데이터를 같이 실어(**ICD**) SEND 한 번으로 끝냅니다. 반대로 큰 데이터를 capsule에 다 넣으면 SEND 버퍼가 감당 못 하므로, capsule엔 SGL(Scatter-Gather List, 데이터가 어디 있는지 알려주는 주소표)만 넣고 본체는 **RDMA Read/Write**로 따로 운반합니다(**Out-of-line**).

그렇다면 "작다/크다"를 가르는 임계값은 어디서 올까요? inline으로 실을 수 있는 한도는 **RDMA SEND가 한 번에 운반하는 버퍼 크기**가 정합니다 — capsule은 결국 SEND 한 건에 담겨야 하고, 그 SEND 페이로드는 수신 측이 미리 마련해 둔 RECV 버퍼와 전송 **MTU**(Maximum Transmission Unit, 한 번에 보낼 수 있는 최대 패킷 크기) 같은 transport 제약 안에 들어가야 하기 때문입니다. 즉 data가 capsule(명령 64B + inline 여유분)에 들어가고도 한 SEND 버퍼를 넘지 않으면 ICD, 넘으면 Out-of-line입니다(정확한 임계 byte 수는 구성·spec 협상값으로 확인 필요). Read의 경우 데이터가 target→host 방향이므로 target이 **RDMA Write**로 host 버퍼에 데이터를 직접 써 넣고 마지막에 completion capsule을 보냅니다.

---

## 4. 일반화 — Architecture와 control-plane

### 4.1 큐 쌍과 capsule

NVMe-oF over RDMA 아키텍처의 요점은 셋입니다. 첫째, **Host ↔ Target controller 사이 RDMA QP**(Queue Pair, RDMA에서 송신 큐와 수신 큐를 한 쌍으로 묶은 통신 단위) **한 쌍 = NVMe 큐 쌍(SQ+CQ) 하나**. 둘째, **capsule**(NVMe cmd 64B + 부속 data)이 RDMA SEND/RECV로 운반됩니다. 셋째, **control-plane**(Connect/Disconnect/Property Get·Set/Authentication)도 capsule 형태로 같은 경로를 흐릅니다 — 즉 3장의 Fabric 커맨드가 바로 이 control-plane capsule입니다.

```d2
direction: right
CMD: "NVMe command\n(64 bytes)"
ICD: "+ In-Capsule Data\n(작은 write 데이터, 선택)"
SGL: "또는 SGL\n(큰 데이터 주소표)"
CAP: "**Capsule**"
CMD -> CAP
ICD -> CAP: "ICD model"
SGL -> CAP: "Out-of-line model"
CAP -> RDMA: "RDMA SEND/RECV"
RDMA: "RDMA transport\n(RoCEv2)"
```

### 4.2 지원 transport

NVMe-oF가 올라갈 수 있는 transport는 PCIe(로컬 NVMe), RDMA(InfiniBand/RoCEv2/iWARP), TCP, Fibre Channel입니다. **NRT DV 환경은 NVMe-oF over RDMA이며 RoCEv2가 주 use-case**입니다. RDMA를 고른 이유는 zero-copy·CPU 우회로 NVMe SSD의 저지연을 네트워크 너머까지 보존하기 때문입니다.

RDMA가 *물리적으로* zero-copy가 되는 이유는 **NIC**(Network Interface Card, 네트워크 통신을 담당하는 카드/칩)**가 호스트 메모리에 직접 DMA**(Direct Memory Access, CPU를 거치지 않고 장치가 메모리를 직접 읽고 쓰는 방식)하기 때문입니다. iSCSI/TCP에서는 CPU가 소켓 버퍼와 애플리케이션 버퍼 사이를 복사했지만, RDMA에서는 NIC 하드웨어가 미리 등록된 메모리 영역을 향해 데이터를 직접 읽고 씁니다. 커널 카피도, 매 패킷마다의 CPU 개입도 없으므로 host CPU는 전송 경로에서 빠집니다. 바로 이 "NIC가 직접 DMA"가 위 1.1에서 본 카피·인터럽트·프로토콜 비용을 제거하는 메커니즘입니다.

이것이 안전하려면 전제가 하나 있습니다 — NIC가 건드릴 메모리를 **미리 Memory Region(MR)으로 등록**해 두어야 합니다. RDMA는 원격이 임의의 host 주소에 직접 쓰는 모델이므로, 무방비로 두면 잘못된 주소를 덮어쓰는 위험이 있습니다. 그래서 host는 대상 버퍼를 사전에 **핀(pin)**하고(OS가 그 페이지를 옮기거나 swap하지 못하게 고정) MR로 등록해, NIC가 안전하게 접근할 수 있는 주소·권한 범위를 정해 둡니다. MR 등록이 선행되지 않으면 NIC는 그 영역에 DMA할 권한이 없습니다 — Read 데이터가 host 버퍼에 도착하지 않는 디버그의 단골 원인이 여기 있습니다.

### 4.3 control-plane = Fabric 커맨드

3장에서 본 Fabric 커맨드(opcode 0x7F)가 여기서 의미를 갖습니다. Connect로 QP 쌍(=NVMe 큐 쌍)을 세우고, Property Get/Set으로 원격 controller의 레지스터(CAP/CC/CSTS 등)를 capsule을 통해 읽고 씁니다 — 로컬 NVMe에서 BAR MMIO로 했던 일을, NVMe-oF에서는 capsule로 합니다. Disconnect로 QP를 해제합니다.

---

## 5. 디테일 — DV 레퍼런스 (NRT 검증 환경)

NVMe-oF over RDMA의 검증은 로컬 NVMe보다 검증 면이 넓습니다. NRT DV의 검증 항목을 정리합니다.

### 5.1 Polling 기반 completion

NRT DV는 **polling 위주**(host가 새 결과를 직접 반복 확인, MSI 비활성)입니다. NVMe-oF에서 completion은 completion capsule로 도착해 host CQ에 반영되고, host는 [2장](../02_sq_cq_doorbell/)에서 본 것처럼 **phase bit**(슬롯의 CQE가 새것인지 옛것인지 구별하는 1비트 표식)으로 유효성을 판정합니다. 여러 QP가 CQ를 공유하는 **shared CQ dispatcher**(여러 큐의 completion을 하나의 CQ에서 받아 알맞은 곳으로 분배하는 로직)가 — abort(진행 중 명령 취소), stale CQE(이전 바퀴의 옛 항목) fast-forward 포함 — NRT 환경의 검증 대상입니다.

### 5.2 Scoreboard — OoO completion

서로 다른 명령의 completion은 발행 순서와 다르게 도착할 수 있습니다(**OoO**, Out-of-Order — 완료가 명령을 보낸 순서와 무관하게 뒤섞여 도착함). 따라서 **scoreboard**(DUT의 실제 출력과 기대값을 비교해 정오답을 판정하는 검증 컴포넌트)를 단일 큐로 짜면 false mismatch(정상인데 틀렸다고 잘못 신고하는 것)가 납니다 — [UVM M05 TLM/Scoreboard](../../uvm/05_tlm_scoreboard_coverage/)에서 본 OoO 패턴 그대로입니다. NRT-TB의 scoreboard는 SRB(submission request block, 발행한 명령을 기록한 블록) ↔ SQE를 비교하는 구조입니다.

```systemverilog
// NVMe-oF completion scoreboard — OoO 매칭 개념 (예시)
class nvmeof_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(nvmeof_scoreboard)

  // 키 = command identifier (CID), 값 = 기대 결과
  expected_t expected_map[int];

  uvm_tlm_analysis_fifo #(nvme_capsule_item) cmd_fifo;   // 발행된 명령
  uvm_tlm_analysis_fifo #(nvme_cqe_item)     cqe_fifo;   // 도착한 completion

  task run_phase(uvm_phase phase);
    fork collect_cmd(); match_cqe(); join
  endtask

  task collect_cmd();
    nvme_capsule_item c;
    forever begin
      cmd_fifo.get(c);
      expected_map[c.cid] = predict(c);   // CID를 키로 기대 결과 저장
    end
  endtask

  task match_cqe();
    nvme_cqe_item cqe;
    forever begin
      cqe_fifo.get(cqe);
      // completion이 OoO로 와도 CID로 정확히 매칭
      if (!expected_map.exists(cqe.cid))
        `uvm_error("SB", $sformatf("No expected cmd for CID=%0d", cqe.cid))
      else begin
        compare(expected_map[cqe.cid], cqe);
        expected_map.delete(cqe.cid);
      end
    end
  endtask
endclass
```

### 5.3 Recovery / Disconnect-Reconnect

NVMe-oF는 네트워크 위에서 동작하므로 *연결이 끊기는* 시나리오가 검증의 큰 축입니다. accidental disconnect, partial disconnect(일부 QP만 끊기고 나머지가 동시 IO를 계속), ssd_timeout, drop, retry-exceed 같은 복구 시나리오를 검증합니다. Disconnect path는 3장의 Fabric Disconnect(sub-opcode 0x08)와 연결됩니다.

### 5.4 검증 항목 매핑

| NVMe-oF 요소 | 검증 항목 | NRT 자료 |
|---|---|---|
| QP = 큐 쌍 | Connect로 QP 수립, admin QP(qid=5) 활성 | Fabric Connect, runtime-mechanisms |
| Capsule transport | ICD vs Out-of-line write, Read 3-step | `nvmeof-*-flow.svg` |
| Polling completion | phase bit 판정, shared CQ dispatcher | CQ Dispatcher, runtime-mechanisms |
| OoO completion | CID 키 scoreboard 매칭 | scoreboard-architecture (SRB/SQE) |
| Recovery | disconnect/partial/timeout/drop/retry | Recovery Mechanisms, Destroy-Reconnect |

---

## 6. 흔한 오해와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'NVMe-oF는 NVMe와 완전히 다른 프로토콜이다']
**실제**: NVMe-oF는 NVMe의 *transport layer만* 교체한 것입니다. SQ/CQ 큐 모델, 명령 구조(64B SQE), completion 개념은 그대로이고, PCIe MMIO 대신 capsule/RDMA로 운반될 뿐입니다. RDMA QP 한 쌍이 NVMe 큐 쌍 하나에 대응합니다.<br>
**왜 헷갈리는가**: "over Fabrics"라는 이름과 RDMA 용어가 별개 프로토콜처럼 들려서.
:::
:::danger[❓ 오해 2 — '모든 write 데이터는 capsule 안에 들어간다']
**실제**: 작은 write만 capsule 안에 inline(ICD)됩니다. 큰 데이터는 capsule에 SGL(주소표)만 넣고 본체는 RDMA Read/Write로 별도 전송(Out-of-line)합니다. 데이터 크기에 따라 모델이 갈립니다.<br>
**왜 헷갈리는가**: "capsule = 명령 + 데이터"라는 ICD 그림만 보고 일반화해서.
:::
:::danger[❓ 오해 3 — 'Read도 host가 RDMA Read로 데이터를 끌어온다']
**실제**: NVMe-oF Read에서 데이터는 target→host 방향이므로, **target이 RDMA Write로 host 버퍼에 데이터를 써 넣습니다.** 흐름은 Capsule(cmd) → RDMA Write(data) → Capsule(completion)입니다. 이름의 "Read"와 RDMA 동사 방향을 혼동하기 쉽습니다.<br>
**왜 헷갈리는가**: "Read니까 RDMA Read"라고 동사를 1:1로 매핑해서.
:::
:::danger[❓ 오해 4 — 'completion은 발행 순서대로 온다']
**실제**: 서로 다른 명령의 completion은 OoO로 도착할 수 있습니다. scoreboard를 단일 큐로 짜면 false mismatch가 납니다. CID(command identifier)를 키로 한 매칭이 필요합니다.<br>
**왜 헷갈리는가**: 로컬 단순 시나리오에서 우연히 in-order로 와서.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 큰 write가 데이터 누락/오류 | ICD 경로로 처리됐는데 Out-of-line이어야 함 | capsule 크기 임계, SGL 사용 여부 (`nvmeof-write-large-flow`) |
| Read 데이터가 host 버퍼에 안 옴 | target의 RDMA Write 방향/주소(host MR) 오류 | host Memory Region 등록, RDMA Write target addr |
| Connect 전 IO가 거부/hang | QP 미수립 (admin QP qid=5 비활성) | Fabric Connect 완료, QP state |
| completion scoreboard false mismatch | 단일 큐로 OoO completion 비교 | CID 키 associative 매칭 (scoreboard-architecture) |
| disconnect 후 surviving QP의 IO가 멈춤 | partial disconnect 시 정상 QP 영향 받음 | Partial Disconnect 시나리오, recovery 경로 |
| stale CQE를 새 completion으로 오인 | shared CQ에서 fast-forward 누락 | CQ Dispatcher의 fastForwardStaleCQEs, phase bit |

---

## 7. 핵심 정리 (Key Takeaways)

- **NVMe-oF는 NVMe의 transport layer만 교체**해 원격 스토리지를 로컬처럼 만듭니다. 지원 transport: PCIe·RDMA·TCP·FC. **NRT DV는 RDMA(RoCEv2)**.
- **RDMA QP 한 쌍 = NVMe 큐 쌍(SQ+CQ) 하나.** control-plane(Connect/Property/Disconnect)도 capsule로 같은 경로를 흐릅니다 — 3장의 Fabric 커맨드가 곧 control-plane.
- **Capsule** = NVMe cmd 64B + 부속. RDMA SEND/RECV로 운반.
- **전송 모델**: ICD(작은 write inline, SEND 1회), Out-of-line(SGL + RDMA Read/Write로 큰 데이터), Read(cmd capsule → target RDMA Write → completion capsule).
- **DV 핵심**: polling completion + phase bit, OoO completion → CID 키 scoreboard, recovery(disconnect/partial/timeout/retry).

:::caution[실무 주의점]
- Read에서 데이터를 옮기는 RDMA 동사는 *target의 RDMA Write*입니다 — "Read=RDMA Read" 혼동 금지.
- completion scoreboard는 OoO를 전제로 CID 키 매칭 — [UVM M05](../../uvm/05_tlm_scoreboard_coverage/)의 OoO 패턴 적용.
- NVMe-oF는 연결이 끊길 수 있는 환경 — recovery/partial-disconnect를 반드시 검증 범위에 포함.
:::

### 7.1 자가 점검

:::tip[🤔 Q1 — ICD vs Out-of-line (Bloom: Apply)]
host가 8MB짜리 write를 보내려 한다. ICD와 Out-of-line 중 어느 모델이 쓰이며, 데이터는 어떻게 운반되는가?
<details>
<summary>정답 / 해설</summary>

**Out-of-line** 모델이 쓰입니다. 8MB는 capsule(NVMe cmd 64B + 작은 inline 공간) 안에 담을 수 없으므로, capsule에는 데이터의 위치를 가리키는 **SGL(Scatter-Gather List)**만 넣고, 실제 8MB 본체는 **RDMA Read/Write**로 별도 전송합니다. ICD는 작은 write 데이터가 capsule 안에 inline되어 RDMA SEND 한 번으로 끝나는, 작은 전송 전용 최적화입니다.

</details>
:::

:::tip[🤔 Q2 — QP와 큐 쌍 (Bloom: Trace)]
NVMe-oF target에서 host가 동시에 4개의 NVMe 큐 쌍으로 IO를 한다면 RDMA QP는 최소 몇 개 필요하며, 그 이유는?
<details>
<summary>정답 / 해설</summary>

최소 4개의 RDMA QP가 필요합니다. **RDMA QP 한 쌍 = NVMe 큐 쌍(SQ+CQ) 하나**로 매핑되기 때문입니다. NVMe-oF에서는 SQ/CQ가 host 메모리의 ring buffer가 아니라 RDMA QP 위의 capsule 흐름으로 구현되므로, 각 NVMe 큐 쌍마다 대응하는 QP가 있어야 합니다. 여기에 더해 admin 트래픽을 위한 admin QP(NRT DV에서 qid=5)도 별도로 필요하므로, 실제로는 IO용 4개 + admin 1개가 됩니다.

</details>
:::

### 7.2 출처

**External**
- *NVM Express over Fabrics Specification* (transport binding, capsule, SGL) — NVM Express, Inc.
- RoCEv2 / InfiniBand Architecture — RDMA transport 기반 ([RDMA 코스](../../rdma/))

---

## 다음 모듈

이 코스의 마지막 챕터입니다. 배운 용어를 [용어집](../glossary/)에서 ISO 11179 정의로 다시 확인하고, [퀴즈](../quiz/)로 전 챕터 이해도를 점검하세요. 더 넓은 맥락은 transport 기반인 [RDMA 코스](../../rdma/)와 모바일 스토리지 비교 관점의 [UFS/HCI 코스](../../ufs_hci/)로 이어집니다.

[퀴즈 풀어보기 →](../quiz/04_nvmeof_over_rdma_quiz/)
