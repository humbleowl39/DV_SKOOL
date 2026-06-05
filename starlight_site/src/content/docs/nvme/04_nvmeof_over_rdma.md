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

데이터센터에서 컴퓨트 노드와 스토리지를 분리(disaggregation)하고 싶다고 합시다. SSD를 각 서버에 꽂는 대신 별도 스토리지 노드에 모아두고, 네트워크로 끌어다 쓰는 구조입니다. 문제는 "원격인데 로컬만큼 빠르고 지연이 낮아야 한다"는 것입니다. 일반 네트워크 스토리지(예: iSCSI)는 TCP/IP 스택과 CPU 카피 때문에 NVMe SSD의 마이크로초 지연을 다 까먹습니다.

**NVMe over Fabrics(NVMe-oF)**가 이 문제를 풉니다. NVMe spec은 transport layer를 추상화해 두었기 때문에, 그 위에 PCIe 대신 RDMA(InfiniBand/RoCEv2/iWARP), TCP, Fibre Channel을 끼울 수 있습니다(HDG §3). 특히 **RDMA over Fabrics**는 host CPU를 거치지 않는 zero-copy 전송으로 원격 NVMe를 거의 로컬처럼 만듭니다. NRT DV 환경은 바로 이 **NVMe-oF over RDMA**(RoCEv2가 주 use-case)를 검증합니다.

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

핵심 매핑: **RDMA QP 한 쌍 = NVMe 큐 쌍(SQ+CQ) 하나**(HDG §3.1). control-plane(Connect/Disconnect/Property/Auth)도 모두 capsule 형태로 이 QP 위를 흐릅니다.

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

### 세 가지 전송 모델 (HDG §3.2)

| Model | 설명 | NRT-TB 시각화 |
|---|---|---|
| **In-Capsule Data (ICD)** | 작은 write 데이터를 capsule 안에 inline (RDMA SEND 한 번) | `NRT_TB/docs/img/nvmeof-write-icd-flow.svg` |
| **Out-of-line** | SGL + RDMA Read/Write로 큰 데이터를 별도 전송 | `NRT_TB/docs/img/nvmeof-write-large-flow.svg` |
| **Read** | Capsule(cmd) → RDMA Write(data) → Capsule(completion) | `NRT_TB/docs/img/nvmeof-read-flow.svg` |

### 왜 두 모델인가

작은 데이터를 매번 별도 RDMA Read/Write로 옮기면 왕복 지연이 낭비입니다. 그래서 작은 write는 capsule 봉투 안에 데이터를 같이 실어(**ICD**) SEND 한 번으로 끝냅니다. 반대로 큰 데이터를 capsule에 다 넣으면 SEND 버퍼가 감당 못 하므로, capsule엔 SGL(Scatter-Gather List, 데이터가 어디 있는지 알려주는 주소표)만 넣고 본체는 **RDMA Read/Write**로 따로 운반합니다(**Out-of-line**). Read의 경우 데이터가 target→host 방향이므로 target이 **RDMA Write**로 host 버퍼에 데이터를 직접 써 넣고 마지막에 completion capsule을 보냅니다.

---

## 4. 일반화 — Architecture와 control-plane

### 4.1 큐 쌍과 capsule

HDG §3.1의 아키텍처 요점은 셋입니다. 첫째, **Host ↔ Target controller 사이 RDMA QP 한 쌍 = NVMe 큐 쌍(SQ+CQ) 하나**. 둘째, **capsule**(NVMe cmd 64B + 부속 data)이 RDMA SEND/RECV로 운반됩니다. 셋째, **control-plane**(Connect/Disconnect/Property Get·Set/Authentication)도 capsule 형태로 같은 경로를 흐릅니다 — 즉 3장의 Fabric 커맨드가 바로 이 control-plane capsule입니다.

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

NVMe-oF가 올라갈 수 있는 transport는 PCIe(로컬 NVMe), RDMA(InfiniBand/RoCEv2/iWARP), TCP, Fibre Channel입니다(HDG §3). **NRT DV 환경은 NVMe-oF over RDMA이며 RoCEv2가 주 use-case**입니다. RDMA를 고른 이유는 zero-copy·CPU 우회로 NVMe SSD의 저지연을 네트워크 너머까지 보존하기 때문입니다.

### 4.3 control-plane = Fabric 커맨드

3장에서 본 Fabric 커맨드(opcode 0x7F)가 여기서 의미를 갖습니다. Connect로 QP 쌍(=NVMe 큐 쌍)을 세우고, Property Get/Set으로 원격 controller의 레지스터(CAP/CC/CSTS 등)를 capsule을 통해 읽고 씁니다 — 로컬 NVMe에서 BAR MMIO로 했던 일을, NVMe-oF에서는 capsule로 합니다. Disconnect로 QP를 해제합니다.

---

## 5. 디테일 — DV 레퍼런스 (NRT 검증 환경)

NVMe-oF over RDMA의 검증은 로컬 NVMe보다 검증 면이 넓습니다. HDG §1·§6의 NRT DV 내용을 검증 항목으로 정리합니다.

### 5.1 Polling 기반 completion

NRT DV는 **polling 위주**(MSI 비활성)입니다(HDG §1). NVMe-oF에서 completion은 completion capsule로 도착해 host CQ에 반영되고, host는 [2장](../02_sq_cq_doorbell/)에서 본 것처럼 phase bit으로 유효성을 판정합니다. 여러 QP가 CQ를 공유하는 **shared CQ dispatcher**(abort, stale CQE fast-forward 포함)가 NRT 환경의 검증 대상입니다(HDG §6, Confluence *CQ Dispatcher*).

### 5.2 Scoreboard — OoO completion

서로 다른 명령의 completion은 발행 순서와 다르게 도착할 수 있습니다. 따라서 scoreboard를 단일 큐로 짜면 false mismatch가 납니다 — [UVM M05 TLM/Scoreboard](../../uvm/05_tlm_scoreboard_coverage/)에서 본 OoO 패턴 그대로입니다. NRT-TB의 scoreboard는 SRB(submission) ↔ SQE를 비교하는 구조입니다(HDG §6, Confluence *scoreboard-architecture*).

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

NVMe-oF는 네트워크 위에서 동작하므로 *연결이 끊기는* 시나리오가 검증의 큰 축입니다. accidental disconnect, partial disconnect(일부 QP만 끊기고 나머지가 동시 IO를 계속), ssd_timeout, drop, retry-exceed 같은 복구 시나리오를 검증합니다(HDG §6, Confluence *Recovery Mechanisms*, *Destroy-Reconnect Sequence* Step 1~10, *Partial Disconnect*). Disconnect path는 3장의 Fabric Disconnect(sub-opcode 0x08)와 연결됩니다.

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

**Out-of-line** 모델이 쓰입니다. 8MB는 capsule(NVMe cmd 64B + 작은 inline 공간) 안에 담을 수 없으므로, capsule에는 데이터의 위치를 가리키는 **SGL(Scatter-Gather List)**만 넣고, 실제 8MB 본체는 **RDMA Read/Write**로 별도 전송합니다(HDG §3.2). ICD는 작은 write 데이터가 capsule 안에 inline되어 RDMA SEND 한 번으로 끝나는, 작은 전송 전용 최적화입니다.

</details>
:::

:::tip[🤔 Q2 — QP와 큐 쌍 (Bloom: Trace)]
NVMe-oF target에서 host가 동시에 4개의 NVMe 큐 쌍으로 IO를 한다면 RDMA QP는 최소 몇 개 필요하며, 그 이유는?
<details>
<summary>정답 / 해설</summary>

최소 4개의 RDMA QP가 필요합니다. HDG §3.1에 따르면 **RDMA QP 한 쌍 = NVMe 큐 쌍(SQ+CQ) 하나**로 매핑되기 때문입니다. NVMe-oF에서는 SQ/CQ가 host 메모리의 ring buffer가 아니라 RDMA QP 위의 capsule 흐름으로 구현되므로, 각 NVMe 큐 쌍마다 대응하는 QP가 있어야 합니다. 여기에 더해 admin 트래픽을 위한 admin QP(NRT DV에서 qid=5)도 별도로 필요하므로, 실제로는 IO용 4개 + admin 1개가 됩니다.

</details>
:::

### 7.2 출처

**Internal (HDG / Confluence)**
- HDG `nvme_dv_reference.md` §3 — "NVMe-oF Overview" (3.1 Architecture: QP=큐쌍, capsule; 3.2 Data Transfer Models: ICD/Out-of-line/Read), §6 (NRT 검증 환경 link)
- Confluence: *NVMe-oF / RDMA 흐름* (DV 한국어, page 1359642693) — Read/Write/ICD flow top-level
- Confluence: *CQ Dispatcher* (1359904907), *scoreboard-architecture*, *Recovery Mechanisms* (1399160863), *Destroy-Reconnect Sequence* (1359282279), *Partial Disconnect* (1359675471)
- `NRT_TB/docs/img/nvmeof-write-icd-flow.svg`, `nvmeof-write-large-flow.svg`, `nvmeof-read-flow.svg`
- NRT-TB docs: `runtime-mechanisms.md`, `scoreboard-architecture.md`, `destroy-reconnect-flow.md`

**External**
- *NVM Express over Fabrics Specification* (transport binding, capsule, SGL) — NVM Express, Inc.
- RoCEv2 / InfiniBand Architecture — RDMA transport 기반 ([RDMA 코스](../../rdma/))

---

## 다음 모듈

이 코스의 마지막 챕터입니다. 배운 용어를 [용어집](../glossary/)에서 ISO 11179 정의로 다시 확인하고, [퀴즈](../quiz/)로 전 챕터 이해도를 점검하세요. 더 넓은 맥락은 transport 기반인 [RDMA 코스](../../rdma/)와 모바일 스토리지 비교 관점의 [UFS/HCI 코스](../../ufs_hci/)로 이어집니다.

[퀴즈 풀어보기 →](../quiz/04_nvmeof_over_rdma_quiz/)
