# Quiz — Module 06: Data Path Operations

[← Module 06 본문으로 돌아가기](../06_data_path.md)

---

## Q1. (Remember)

RDMA WRITE 8KB 메시지를 MTU=4KB 환경에서 보낼 때, 송출되는 packet 의 OpCode 시퀀스는?

??? answer "정답 / 해설"
    1. `RDMA_WRITE_FIRST` (RETH 포함) — 4KB
    2. `RDMA_WRITE_LAST` — 4KB (보통 A=1)

    8KB 가 정확히 2 packet 으로 나뉘므로 MIDDLE 은 없음. 12KB 였으면 FIRST/MIDDLE/LAST 의 3 packet.

## Q2. (Understand)

PSN 24-bit 의 window = 2^23 인 의미는?

??? answer "정답 / 해설"
    Receiver 가 받은 packet 의 PSN 을 expected PSN (ePSN) 과 비교해 분류:

    - PSN == ePSN → 정상
    - PSN ∈ [ePSN-2^23, ePSN-1] (modulo 2^24) → 중복 (이미 처리, ACK 다시)
    - PSN ∈ [ePSN+1, ePSN+2^23-1] → 미래 (drop 또는 NAK Sequence Error)

    Window 가 절반 이유: modulo 산술에서 "어느 쪽이 과거고 미래인지" 를 명확히 분류 가능.

## Q3. (Apply)

Sender 가 PSN=100,101,102 를 보내고 LAST (102) 에 A=1 을 set 했다.
Receiver 가 PSN=100,102 를 받고 (101 drop) 수신했다면 어떤 동작이 일어나는가?

??? answer "정답 / 해설"
    1. Receiver: PSN=100 정상 수신 → ePSN=101.
    2. Receiver: PSN=102 도착 → ePSN=101 보다 큼 → **NAK Sequence Error (syndrome 0x80)** 송신, syndrome 의 PSN 은 expected 인 101.
    3. Sender: NAK 받음 → PSN=101 부터 retransmit.
    4. Receiver: PSN=101, 102 받음 → 정상, ePSN=103.
    5. Receiver: 마지막 packet 의 A=1 → ACK PSN=102 송신.
    6. Sender: ACK 받음 → SQ 에서 WR retire.

    Retry timer 가 먼저 만료되면 sender 가 NAK 보다 먼저 재시도할 수도 있음.

## Q4. (Analyze)

RDMA READ 의 max_rd_atomic 과 max_dest_rd_atomic 이 mismatch 되면 어떤 문제가 생길 수 있는가?

??? answer "정답 / 해설"
    - `max_rd_atomic` (sender) > `max_dest_rd_atomic` (responder) → sender 가 여러 READ 를 outstanding 으로 보낼 수 있는데 responder 가 처리 못 함.
    - 결과: responder 가 **`WC_REM_INV_RD_REQ_ERR`** 로 응답 (`WC_FLAG_RESP_OP`).
    - sender 의 send CQ 에 error → QP 가 Err state.

    → 검증 (RDMA-TB S9) 에서 정확히 이 시나리오를 inject (read 중복 callback 으로) 해 검증.

    반대 (sender max_rd_atomic 이 더 작음) 는 throughput 만 낮아질 뿐 spec 위반 아님.

## Q5. (Evaluate)

"RDMA READ Response 의 모든 packet 에 AETH 가 들어간다" 는 진술을 평가하라.

??? answer "정답 / 해설"
    **부정확**.

    - `RDMA_READ_RESPONSE_FIRST` 와 `RDMA_READ_RESPONSE_LAST`, `RDMA_READ_RESPONSE_ONLY` 에는 AETH 있음.
    - `RDMA_READ_RESPONSE_MIDDLE` 에는 **AETH 없음** (data only).

    이유: AETH 는 ACK/NAK 의 정보 (syndrome, MSN) 와 implicit ACK 역할을 하는데, 중간 packet 에 매번 넣을 필요 없음 — credit 은 처음과 끝에 한 번씩 충분.

    검증 시 packet decoder 가 MIDDLE 에서 AETH 를 기대하면 false fail 발생.
