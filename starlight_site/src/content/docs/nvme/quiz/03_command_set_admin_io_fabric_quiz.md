---
title: "Quiz — 03: 커맨드 분류 (Admin / IO / Fabric)"
---

[← 03 본문으로 돌아가기](../../03_command_set_admin_io_fabric/)

---

## Q1. (Remember)

NVMe 명령의 세 가지 분류는?

- [ ] A. Read / Write / Erase
- [ ] B. Admin / IO / Fabric
- [ ] C. Setup / Transfer / Teardown
- [ ] D. Control / Data / Status

<details>
<summary>정답 / 해설</summary>

**B**. HDG §2에 따르면 NVMe 명령은 Admin(controller 설정·관리), IO(실제 데이터 전송), Fabric(NVMe-oF 전용 연결·속성)의 세 분류로 나뉩니다. A는 IO 명령의 일부 동작이고, C·D는 NVMe 분류 용어가 아닙니다.

</details>

## Q2. (Understand)

Fabric 커맨드가 사용하는 opcode 0x7F의 역할과, 실제 명령을 식별하는 방법을 설명하라.

<details>
<summary>정답 / 해설</summary>

opcode 0x7F는 "이 명령은 Fabric 커맨드"라는 **마커** 역할만 합니다(HDG §2.3). 실제 어떤 Fabric 명령인지(Connect/Property Set·Get/Auth/Disconnect)는 SQE 안의 **sub-opcode** field로 식별합니다. 예를 들어 sub-opcode 0x01은 Connect, 0x00은 Property Set, 0x02는 Property Get, 0x08은 Disconnect입니다. 따라서 디코더는 opcode 0x7F로 Fabric임을 인지한 뒤 sub-opcode로 분기하는 2단계 구조여야 합니다.

</details>

## Q3. (Apply)

NRT DV(NVMe-oF) 환경에서 controller bring-up 후 IO Write를 보내기까지의 올바른 순서는?

- [ ] A. IO Write → Connect → Identify
- [ ] B. Connect → Admin(Identify·IO 큐 생성) → IO Write
- [ ] C. Identify → IO Write → Connect
- [ ] D. IO 큐 생성 → Connect → IO Write

<details>
<summary>정답 / 해설</summary>

**B**. NVMe-oF에서는 먼저 Fabric Connect로 admin QP(qid=5)를 활성화하고, 그 위에서 Admin 커맨드(Identify로 controller/namespace 파악, Create IO Queue로 IO 큐 생성)를 실행한 뒤, 비로소 IO Write를 보낼 수 있습니다(HDG §2). IO 큐는 admin 명령으로 만들어야 존재하므로, 큐 생성 전 IO 명령은 거부됩니다. 나머지 보기는 의존 순서를 위반합니다.

</details>

## Q4. (Apply)

NRT DV에서 "데이터 없이 LBA 영역을 0으로 채우는" 동작과 "읽은 값을 기대값과 비교하는" 동작에 해당하는 IO 변형은 각각 무엇인가?

<details>
<summary>정답 / 해설</summary>

데이터 없이 0으로 채우는 것은 **Write Zeros**(NRT DV `io_type=WR_ZERO`)이고, 읽은 값을 비교하는 것은 **Compare**입니다(HDG §2.2). Write Zeros는 host가 0 데이터를 실제로 전송하지 않고 controller가 해당 영역을 0으로 만들게 하여 대역폭을 아끼고, Compare는 매체의 데이터가 host가 제시한 값과 일치하는지 controller가 검사해 mismatch를 보고합니다. 그 외 변형으로 Flush, Write Uncorrectable, Cancel이 있습니다.

</details>

## Q5. (Analyze)

같은 NVM Read opcode가 admin 큐로 들어왔다. controller는 어떻게 처리해야 하며, 이는 Admin/IO 구분이 무엇에 기반함을 보여주는가?

<details>
<summary>정답 / 해설</summary>

controller는 이를 invalid command로 거부해야 합니다. NVM Read 같은 IO opcode는 IO 큐에서만 유효하고, admin 큐(qid=0 또는 NVMe-oF의 qid=5)는 Admin 커맨드 집합만 받기 때문입니다. 이는 Admin과 IO의 구분이 opcode 자체가 아니라 **명령이 들어온 큐의 종류**에 기반함을 보여줍니다(Fabric만 opcode 0x7F로 식별). 검증은 이 큐-부적합 명령에 대한 적절한 에러 status 반환을 확인합니다.

</details>

## Q6. (Evaluate)

"NVMe controller라면 Connect/Disconnect 같은 Fabric 명령 처리도 반드시 검증해야 한다"는 주장이 항상 옳은가? 환경을 근거로 판단하라.

<details>
<summary>정답 / 해설</summary>

항상 옳지는 않습니다. Fabric 커맨드는 **NVMe-oF 환경에서만** 사용되며 capsule transport(RDMA SEND/RECV) 위에서 동작합니다(HDG §2.3). 로컬 PCIe NVMe controller는 PCIe 초기화가 큐 수립 역할을 하므로 Connect/Disconnect 같은 Fabric 절차가 없습니다. 따라서 Fabric 명령 검증의 필요 여부는 *대상이 PCIe NVMe인지 NVMe-oF target인지*에 달려 있습니다. NRT(NVMe RDMA Target) 같은 NVMe-oF IP라면 Fabric 명령 검증이 필수이지만, 순수 PCIe NVMe라면 해당되지 않습니다.

</details>
