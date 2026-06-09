---
title: "Quiz — 04: NVMe-oF over RDMA"
---

[← 04 본문으로 돌아가기](../../04_nvmeof_over_rdma/)

---

## Q1. (Remember)

NVMe-oF over RDMA에서 RDMA QP 한 쌍은 무엇에 매핑되는가?

- [ ] A. NVMe 명령 한 개
- [ ] B. NVMe 큐 쌍(SQ + CQ) 하나
- [ ] C. 하나의 SSD namespace
- [ ] D. 하나의 capsule

<details>
<summary>정답 / 해설</summary>

**B**. NVMe-oF over RDMA에서 RDMA QP 한 쌍 = NVMe 큐 쌍(SQ+CQ) 하나로 매핑됩니다. 로컬 NVMe에서 host 메모리 ring buffer로 구현되던 SQ/CQ가, NVMe-oF에서는 RDMA QP 위의 capsule 흐름으로 구현됩니다. A·C·D는 매핑 단위가 아닙니다.

</details>

## Q2. (Understand)

In-Capsule Data(ICD)와 Out-of-line 전송 모델의 차이를 데이터 크기와 RDMA 동사 관점에서 설명하라.

<details>
<summary>정답 / 해설</summary>

ICD는 **작은 write** 데이터를 capsule 안에 inline으로 실어 RDMA SEND 한 번으로 전송합니다. Out-of-line은 **큰 데이터**를 capsule에 담지 못하므로 capsule에는 SGL(데이터 주소표)만 넣고, 본체는 RDMA Read/Write로 별도 전송합니다. 즉 작은 전송은 왕복을 줄이려 inline+SEND, 큰 전송은 capsule 용량 한계 때문에 SGL+RDMA Read/Write로 갈립니다.

</details>

## Q3. (Apply)

host가 8MB write를 NVMe-oF로 보낸다. 어떤 모델이 쓰이고 데이터는 어떻게 운반되는가?

- [ ] A. ICD — capsule 안에 8MB를 inline
- [ ] B. Out-of-line — capsule엔 SGL, 본체는 RDMA Read/Write
- [ ] C. capsule을 8MB 크기로 키워 SEND
- [ ] D. doorbell로 데이터 직접 전송

<details>
<summary>정답 / 해설</summary>

**B**. 8MB는 capsule(NVMe cmd 64B + 작은 inline 공간)에 담을 수 없으므로 Out-of-line 모델이 쓰입니다. capsule에는 데이터 위치를 가리키는 SGL만 넣고, 8MB 본체는 RDMA Read/Write로 별도 전송합니다. A는 작은 write 전용(ICD)이고, C·D는 실제 메커니즘이 아닙니다.

</details>

## Q4. (Analyze)

NVMe-oF **Read**에서 데이터를 host 버퍼로 옮기는 RDMA 동사는 무엇이며, "Read니까 RDMA Read"라는 직관이 왜 틀리는가?

<details>
<summary>정답 / 해설</summary>

데이터를 옮기는 동사는 **target의 RDMA Write**입니다. NVMe Read는 데이터가 target→host 방향이므로, target이 RDMA Write로 host의 버퍼에 데이터를 직접 써 넣습니다. 흐름은 Capsule(cmd) → RDMA Write(data) → Capsule(completion)입니다. "Read니까 RDMA Read"가 틀린 이유는, NVMe 명령 이름(Read/Write)은 *host 관점의 데이터 방향*을 가리키는 반면, RDMA 동사는 *누가 어느 메모리에 접근하는가*를 가리켜 둘이 1:1로 대응하지 않기 때문입니다.

</details>

## Q5. (Analyze)

NVMe-oF completion scoreboard를 단일 큐(pop_front 비교)로 구현하면 무엇이 잘못되며, 올바른 키는 무엇인가?

<details>
<summary>정답 / 해설</summary>

서로 다른 명령의 completion은 발행 순서와 다르게(OoO) 도착할 수 있습니다. 단일 큐는 expected를 삽입 순서대로 pop_front해 비교하므로, completion이 OoO로 오면 첫 비교부터 false mismatch가 폭발합니다. 올바른 구현은 **command identifier(CID)**를 키로 한 associative array 매칭입니다 — completion이 어떤 순서로 와도 CID로 해당 expected를 찾아 비교합니다. 이는 [UVM M05](../../../uvm/05_tlm_scoreboard_coverage/)의 OoO scoreboard 패턴과 동일하며, NRT-TB는 SRB/SQE 비교 구조를 씁니다.

</details>

## Q6. (Evaluate)

NVMe-oF over RDMA 검증 계획에서 로컬 PCIe NVMe에는 없는, 반드시 추가해야 할 검증 축은 무엇이며 왜 중요한가?

<details>
<summary>정답 / 해설</summary>

**연결 복구(recovery) 검증 축**입니다. NVMe-oF는 네트워크 패브릭 위에서 동작하므로 로컬 PCIe에는 없는 *연결 단절* 시나리오가 존재합니다 — accidental disconnect, partial disconnect(일부 QP만 끊기고 나머지가 동시 IO 지속), ssd_timeout, drop, retry-exceed 등입니다. 이들은 데이터 무결성과 가용성에 직결되므로 중요합니다. 추가로 capsule transport(ICD/Out-of-line), shared CQ dispatcher의 stale CQE 처리, OoO completion 매칭도 NVMe-oF 고유의 검증 면입니다. 따라서 로컬 NVMe의 검증 항목에 recovery/disconnect-reconnect 경로를 반드시 더해야 합니다.

</details>
