# Quiz — Module 05: Memory Model

[← Module 05 본문으로 돌아가기](../05_memory_model.md)

---

## Q1. (Remember)

`ibv_reg_mr` 가 발급하는 두 종류의 key 와 그 사용 위치를 짝지어라.

??? answer "정답 / 해설"
    - **L_Key** → 같은 노드 내 sg_list 의 `lkey` 필드. Sender 자신의 buffer 검증.
    - **R_Key** → RDMA WRITE 의 RETH, ATOMIC 의 AtomicETH 등 원격이 사용하는 보호 키. Responder 측 MR 검증.

## Q2. (Understand)

"같은 MR 에 대해 L_Key 와 R_Key 가 둘 다 발급되니 같은 키" 라는 말이 왜 부정확한가?

??? answer "정답 / 해설"
    값은 다르고 (별도 24+8 bit), 검증 경로도 다름.

    - L_Key 는 **local access 시점** 에 lkey 와 access flag (Local Read/Write) 검증.
    - R_Key 는 **원격에서 들어온 RETH** 를 보고 access flag (Remote Read/Write/Atomic) + PD + MR 범위 검증.

    또한 `ibv_reg_mr` 호출 시 access flag 를 다르게 줄 수 있어 (예: Local Write 만 / Remote Read 만), 두 키의 효과가 비대칭이 될 수 있음.

## Q3. (Apply)

다음 RDMA WRITE 시나리오에서 sender 와 responder 가 각각 검증해야 하는 access flag 를 적어라.

> Sender 가 자기 buffer A 의 1KB 를 원격 buffer B 로 RDMA WRITE.

??? answer "정답 / 해설"
    - **Sender 측**: A 의 MR 의 access flag 에 **Local Read** 가 있어야 함 (HCA 가 A 를 읽어가야 함).
    - **Responder 측**: B 의 MR 의 access flag 에 **Remote Write** 가 있어야 함.

    추가로:
    - Sender 의 sg_list 의 lkey == A 의 L_Key
    - 패킷 RETH 의 rkey == B 의 R_Key
    - Sender QP 와 A 의 MR 이 같은 PD
    - Responder QP 와 B 의 MR 이 같은 PD
    - [remote_va, remote_va+len] 이 B 의 MR 영역 안

## Q4. (Analyze)

`IBV_WC_LOC_PROT_ERR` 와 `IBV_WC_REM_ACCESS_ERR` 의 차이를 분석하라. 어느 쪽이 발생했을 때 sender 측 코드의 버그를 의심해야 하는가?

??? answer "정답 / 해설"
    - `LOC_PROT_ERR` (Local Protection Error) — sender 자신의 sg_list 가 잘못. lkey 가 잘못이거나 access flag 부족 또는 addr 범위 벗어남. **sender 측 코드 버그 의심**.
    - `REM_ACCESS_ERR` (Remote Access Error) — responder 가 RETH/AtomicETH 의 rkey/range/PD/access flag 검증 실패. **responder 측 (또는 양쪽 합의된 R_Key) 의 문제**.

    Sender 가 의심받는 경우는 LOC_PROT_ERR 가 가장 명확. REM_ACCESS_ERR 는 양쪽 setup 의 mismatch 일 가능성 큼.

## Q5. (Evaluate)

ODP (On-Demand Paging) 가 큰 영역을 등록할 때 메모리 효율적이라는 장점에도 불구하고 검증/운영 관점에서 어떤 trade-off 를 가지는가?

??? answer "정답 / 해설"
    Trade-off:

    - **Page fault latency**: 첫 access 시 OS 까지 page-in 요청 (PCIe PRI) → 수 us ~ ms latency.
    - **Retry interaction**: page fault 가 길면 RC retry timer 가 먼저 발동 → packet duplicate.
    - **PRI 처리량**: OS 가 page-in 처리 못 따라가면 throughput 급락.
    - **검증 복잡도**: page-fault → PRI → ATS update → packet 재시도 의 전체 chain 검증 필요. RDMA-TB 가 host memory model 을 cycle-accurate 로 가져야 함.

    → "메모리 절약" 의 가치 vs "complexity + corner case" 의 비용. 일반 deployment 보다는 큰 영역 (TB-scale) registration 이 정말 필요한 경우에만 사용.
