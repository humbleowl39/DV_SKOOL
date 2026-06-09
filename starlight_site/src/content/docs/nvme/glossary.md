---
title: "NVMe / NVMe-oF 용어집"
---

이 페이지는 본 코스에서 사용되는 NVMe / NVMe-oF 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

:::tip[검색 활용]
상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.
:::
---

## C — Capsule / Completion Queue / CQE

### Capsule

**Definition.** NVMe-oF 환경에서 NVMe 명령(64바이트)과 부속 데이터를 묶어 RDMA SEND/RECV로 운반하는 전송 단위.

**Source.** NVM Express over Fabrics Specification.

**Related.** In-Capsule Data, RDMA SEND/RECV, Fabric Command, SGL.

**Example.** 작은 write에서는 capsule = NVMe Write 명령 + inline write data(ICD)이고, 큰 write에서는 capsule = NVMe 명령 + SGL(데이터 주소표)이다.

**See also.** [04 — NVMe-oF over RDMA](../04_nvmeof_over_rdma/)

### Completion Queue (CQ)

**Definition.** controller가 명령 처리 결과(CQE)를 기록하고 host가 소비하는, host 메모리에 위치한 circular ring buffer.

**Source.** NVM Express Base Specification.

**Related.** Submission Queue, CQE, CQ head doorbell, Phase Tag, Queue Pair.

**Example.** controller가 CQ의 tail 위치에 CQE를 쓰고 phase bit을 설정하면, host는 head 위치에서 phase bit으로 새 CQE를 인지한 뒤 CQ head doorbell로 슬롯을 반환한다.

**See also.** [02 — SQ/CQ 큐 메커니즘 & Doorbell](../02_sq_cq_doorbell/)

### CQE (Completion Queue Entry)

**Definition.** controller가 한 명령의 처리 결과를 담아 Completion Queue에 기록하는 항목으로, 상태 코드와 phase bit을 포함한다.

**Source.** NVM Express Base Specification.

**Related.** Completion Queue, Phase Tag, Status, Command Identifier.

**Example.** polling host는 head 위치 CQE의 phase bit을 기대값과 비교해 유효한 completion인지 판정한다.

**See also.** [02 — SQ/CQ 큐 메커니즘 & Doorbell](../02_sq_cq_doorbell/)

---

## D — Doorbell

### Doorbell

**Definition.** host가 controller의 BAR MMIO 레지스터에 큐 포인터(SQ tail 또는 CQ head)를 기록해 큐 상태 변화를 controller에 통지하는 메커니즘.

**Source.** NVM Express Base Specification.

**Related.** Submission Queue, Completion Queue, BAR0, MMIO.

**Example.** host는 SQE를 SQ에 채운 뒤 SQ tail doorbell에 새 tail 값을 써 명령 도착을 알리고, CQE를 소비한 뒤 CQ head doorbell에 새 head 값을 써 슬롯을 반환한다.

**See also.** [02 — SQ/CQ 큐 메커니즘 & Doorbell](../02_sq_cq_doorbell/)

---

## F — Fabric Command

### Fabric Command

**Definition.** NVMe-oF 환경에서 큐 쌍 연결과 controller property 접근을 수행하기 위해 opcode 0x7F를 마커로 사용하고 sub-opcode로 실제 명령을 식별하는 NVMe 명령 분류.

**Source.** NVM Express over Fabrics Specification.

**Related.** Connect, Property Get/Set, Disconnect, NVMe-oF, Capsule.

**Example.** sub-opcode 0x01은 Connect(큐 쌍 수립), 0x00은 Property Set, 0x02는 Property Get, 0x08은 Disconnect를 의미한다.

**See also.** [03 — 커맨드 분류: Admin / IO / Fabric](../03_command_set_admin_io_fabric/)

---

## I — In-Capsule Data / IO Command

### In-Capsule Data (ICD)

**Definition.** 작은 write 데이터를 capsule 안에 inline으로 실어 RDMA SEND 한 번으로 전송하는 NVMe-oF 데이터 전송 모델.

**Source.** NVM Express over Fabrics Specification.

**Related.** Capsule, Out-of-line, SGL, RDMA SEND.

**Example.** 작은 4KB write는 capsule(NVMe cmd + data)을 RDMA SEND로 한 번 보내 완료하지만, 큰 데이터는 Out-of-line 모델을 사용한다.

**See also.** [04 — NVMe-oF over RDMA](../04_nvmeof_over_rdma/)

### IO Command

**Definition.** IO 큐를 통해 실제 데이터를 읽고 쓰는 NVMe 명령 분류로, NVM Read/Write와 Flush·Compare 등의 변형을 포함한다.

**Source.** NVM Express Base Specification.

**Related.** Admin Command, NVM Read, NVM Write, io_type knob.

**Example.** NRT DV에서 `io_type` knob은 `WR_ONLY`/`RD_ONLY`/`WR_AND_RD`/`FLUSH`/`WR_ZERO`/`IO_FULL_RAND` 등으로 IO 변형을 선택한다.

**See also.** [03 — 커맨드 분류: Admin / IO / Fabric](../03_command_set_admin_io_fabric/)

---

## A — Admin Command

### Admin Command

**Definition.** admin 큐를 통해 controller를 설정·관리하는 NVMe 명령 분류로, Identify·Get Log Page·Create/Delete IO Queue 등을 포함한다.

**Source.** NVM Express Base Specification.

**Related.** IO Command, Identify, NVMe-oF Connect, admin queue.

**Example.** NRT DV에서는 NVMe-oF Connect 후 admin QP(qid=5)가 활성화되어야 admin 커맨드를 처리할 수 있다.

**See also.** [03 — 커맨드 분류: Admin / IO / Fabric](../03_command_set_admin_io_fabric/)

---

## N — NVMe / NVMe-oF

### NVMe (Non-Volatile Memory Express)

**Definition.** PCIe 버스에 연결된 비휘발성 스토리지 매체에 접근하기 위해 플래시 SSD를 전제로 설계된 논리 디바이스 인터페이스 사양.

**Source.** NVM Express Base Specification.

**Related.** PCIe, SATA/SAS, Submission Queue, Completion Queue, SSD.

**Example.** NVMe는 최대 64K 큐 × 64K 명령의 병렬성을 제공해, 단일 큐 32명령의 SATA 대비 멀티코어 동시 I/O를 효율적으로 처리한다.

**See also.** [01 — 왜 NVMe인가: vs SATA/SAS](../01_motivation_vs_sata_sas/)

### NVMe-oF (NVMe over Fabrics)

**Definition.** NVMe의 transport layer 추상화 위에서 NVMe 프로토콜을 네트워크 패브릭으로 확장해 원격 NVMe 스토리지를 로컬처럼 접근하게 하는 사양.

**Source.** NVM Express over Fabrics Specification.

**Related.** RDMA, RoCEv2, Capsule, Fabric Command, Queue Pair.

**Example.** NRT DV 환경은 NVMe-oF over RDMA(RoCEv2 주 use-case)로, RDMA QP 한 쌍이 NVMe 큐 쌍 하나에 매핑된다.

**See also.** [04 — NVMe-oF over RDMA](../04_nvmeof_over_rdma/)

---

## O — Out-of-line Data

### Out-of-line Data

**Definition.** 큰 데이터를 capsule에 포함하지 않고 SGL과 RDMA Read/Write를 통해 별도로 전송하는 NVMe-oF 데이터 전송 모델.

**Source.** NVM Express over Fabrics Specification.

**Related.** In-Capsule Data, SGL, RDMA Read/Write, Capsule.

**Example.** 8MB write는 capsule에 SGL만 담고 본체는 RDMA로 전송하며, Read는 target이 RDMA Write로 host 버퍼에 데이터를 써 넣는다.

**See also.** [04 — NVMe-oF over RDMA](../04_nvmeof_over_rdma/)

---

## P — Phase Tag

### Phase Tag (Phase Bit)

**Definition.** CQE에 포함되어 controller가 Completion Queue를 한 바퀴 돌 때마다 토글되는 비트로, polling host가 해당 슬롯의 CQE가 새로 쓰인 유효한 항목인지 판정하는 표식.

**Source.** NVM Express Base Specification.

**Related.** CQE, Completion Queue, polling, wrap-around.

**Example.** polling host는 head 위치 CQE의 phase bit이 기대 phase와 같을 때만 새 completion으로 인지하므로, head 포인터만으로는 유효성을 판단하지 않는다.

**See also.** [02 — SQ/CQ 큐 메커니즘 & Doorbell](../02_sq_cq_doorbell/)

---

## Q — Queue Pair / Queue Model

### Queue Pair (NVMe)

**Definition.** Submission Queue와 Completion Queue를 한 쌍으로 묶어 host와 controller 간 명령 제출과 완료 통지를 담당하는 NVMe의 기본 통신 단위.

**Source.** NVM Express Base Specification.

**Related.** Submission Queue, Completion Queue, RDMA QP, doorbell.

**Example.** NVMe-oF에서는 RDMA QP 한 쌍이 NVMe 큐 쌍(SQ+CQ) 하나에 매핑된다.

**See also.** [02 — SQ/CQ 큐 메커니즘 & Doorbell](../02_sq_cq_doorbell/) · [RDMA 코스](../../rdma/)

### Ring Buffer (Circular Queue)

**Definition.** Submitter가 Tail을, Consumer가 Head를 갱신하며 포인터가 끝에서 처음으로 되돌아가는(wrap-around) 고정 크기 순환 큐 구조.

**Source.** NVM Express Base Specification.

**Related.** Submission Queue, Completion Queue, head, tail, doorbell.

**Example.** Empty는 `Head == Tail`, Full은 `Head == Tail + 1`로 판정하며, full 판정을 위해 한 슬롯을 비워두므로 실효 용량은 `size − 1`이다.

**See also.** [02 — SQ/CQ 큐 메커니즘 & Doorbell](../02_sq_cq_doorbell/)

---

## S — Submission Queue / SGL

### Submission Queue (SQ)

**Definition.** host가 controller에 보낼 명령(SQE)을 기록하는, host 메모리에 위치한 circular ring buffer.

**Source.** NVM Express Base Specification.

**Related.** Completion Queue, SQE, SQ tail doorbell, Queue Pair.

**Example.** host는 SQE를 SQ의 tail 위치에 쓴 뒤 SQ tail doorbell을 갱신해야 controller가 명령 도착을 인지한다.

**See also.** [02 — SQ/CQ 큐 메커니즘 & Doorbell](../02_sq_cq_doorbell/)

### SGL (Scatter-Gather List)

**Definition.** 데이터가 메모리에 흩어져 위치한 여러 영역을 가리키는 디스크립터 목록으로, Out-of-line 전송에서 RDMA Read/Write 대상 위치를 지정한다.

**Source.** NVM Express over Fabrics Specification.

**Related.** Out-of-line Data, RDMA Read/Write, Capsule.

**Example.** 큰 write의 capsule에는 데이터 본체 대신 SGL이 들어가고, target은 SGL이 가리키는 위치에서 RDMA로 데이터를 전송한다.

**See also.** [04 — NVMe-oF over RDMA](../04_nvmeof_over_rdma/)
