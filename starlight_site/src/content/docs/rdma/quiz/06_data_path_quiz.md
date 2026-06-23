---
pagefind: false
title: "Quiz — Module 06: Data Path Operations"
---

[← Module 06 본문으로 돌아가기](../../06_data_path/)

---

## Q1. (Remember)

RDMA WRITE 8KB 메시지를 MTU=4KB 환경에서 보낼 때, 송출되는 packet 의 OpCode 시퀀스는?

<details>
<summary>정답 / 해설</summary>

1. `RDMA_WRITE_FIRST` (RETH 포함) — 4KB
2. `RDMA_WRITE_LAST` — 4KB (보통 A=1)

8KB 가 정확히 2 packet 으로 나뉘므로 MIDDLE 은 없음. 12KB 였으면 FIRST/MIDDLE/LAST 의 3 packet.

FIRST 와 LAST 만 있고 MIDDLE 이 없는 이유는 메시지가 MTU 의 정확한 2배일 때 첫 패킷과 마지막 패킷의 역할이 명확하게 갈리기 때문이다. RETH 는 FIRST 에만 포함되는데, 이 헤더가 원격 버퍼의 시작 주소와 전체 길이를 알려주는 역할을 하기 때문이다. MIDDLE 이 없다는 것을 패킷 디코더가 제대로 처리하지 못하면 scoreboard 에서 "MIDDLE 없이 LAST 가 왔다"를 오류로 판정하는 false fail 이 발생한다.

</details>
## Q2. (Understand)

PSN 24-bit 의 window = 2^23 인 의미는?

<details>
<summary>정답 / 해설</summary>

Receiver 가 받은 packet 의 PSN 을 expected PSN (ePSN) 과 비교해 분류:

- PSN == ePSN → 정상
- PSN ∈ [ePSN-2^23, ePSN-1] (modulo 2^24) → 중복 (이미 처리, ACK 다시)
- PSN ∈ [ePSN+1, ePSN+2^23-1] → 미래 (drop 또는 NAK Sequence Error)

Window 가 절반 이유: modulo 산술에서 "어느 쪽이 과거고 미래인지" 를 명확히 분류 가능.

window 를 24-bit 전체(16M)가 아닌 절반(8M)으로 제한하는 이유는 모듈러 산술의 모호성 때문이다. PSN 공간이 환형(circular)이기 때문에 window 가 절반을 넘으면 특정 PSN 이 "과거 중복"인지 "미래 값"인지 구별할 수 없는 영역이 생긴다. window = 2^23 으로 제한하면 ePSN 을 기준으로 왼쪽 절반은 확실히 과거, 오른쪽 절반은 확실히 미래로 분류된다. 검증 환경에서 PSN 비교 함수를 단순 `>` 연산으로 작성하면 wrap-around 시점에 이 분류가 뒤집혀 버그가 생긴다.

</details>
## Q3. (Apply)

Sender 가 PSN=100,101,102 를 보내고 LAST (102) 에 A=1 을 set 했다.
Receiver 가 PSN=100,102 를 받고 (101 drop) 수신했다면 어떤 동작이 일어나는가?

<details>
<summary>정답 / 해설</summary>

1. Receiver: PSN=100 정상 수신 → ePSN=101.
2. Receiver: PSN=102 도착 → ePSN=101 보다 큼 → **NAK Sequence Error (syndrome 0x80)** 송신, syndrome 의 PSN 은 expected 인 101.
3. Sender: NAK 받음 → PSN=101 부터 retransmit.
4. Receiver: PSN=101, 102 받음 → 정상, ePSN=103.
5. Receiver: 마지막 packet 의 A=1 → ACK PSN=102 송신.
6. Sender: ACK 받음 → SQ 에서 WR retire.

Retry timer 가 먼저 만료되면 sender 가 NAK 보다 먼저 재시도할 수도 있음.

</details>
## Q4. (Analyze)

RDMA READ 의 max_rd_atomic 과 max_dest_rd_atomic 이 mismatch 되면 어떤 문제가 생길 수 있는가?

<details>
<summary>정답 / 해설</summary>

- `max_rd_atomic` (sender) > `max_dest_rd_atomic` (responder) → sender 가 여러 READ 를 outstanding 으로 보낼 수 있는데 responder 가 처리 못 함.
- 결과: responder 가 **`WC_REM_INV_RD_REQ_ERR`** 로 응답 (`WC_FLAG_RESP_OP`).
- sender 의 send CQ 에 error → QP 가 Err state.

→ 검증 (RDMA-TB S9) 에서 정확히 이 시나리오를 inject (read 중복 callback 으로) 해 검증.

반대 (sender max_rd_atomic 이 더 작음) 는 throughput 만 낮아질 뿐 spec 위반 아님.

</details>
## Q5. (Evaluate)

"RDMA READ Response 의 모든 packet 에 AETH 가 들어간다" 는 진술을 평가하라.

<details>
<summary>정답 / 해설</summary>

**부정확**.

- `RDMA_READ_RESPONSE_FIRST` 와 `RDMA_READ_RESPONSE_LAST`, `RDMA_READ_RESPONSE_ONLY` 에는 AETH 있음.
- `RDMA_READ_RESPONSE_MIDDLE` 에는 **AETH 없음** (data only).

이유: AETH 는 ACK/NAK 의 정보 (syndrome, MSN) 와 implicit ACK 역할을 하는데, 중간 packet 에 매번 넣을 필요 없음 — credit 은 처음과 끝에 한 번씩 충분.

검증 시 packet decoder 가 MIDDLE 에서 AETH 를 기대하면 false fail 발생.

</details>
