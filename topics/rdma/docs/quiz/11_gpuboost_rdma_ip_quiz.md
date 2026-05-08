# Quiz — Module 11: GPUBoost / RDMA-IP Hardware Architecture

[← Module 11 본문으로 돌아가기](../11_gpuboost_rdma_ip.md)

---

## Q1. (Remember)

RDMA-IP 의 5 wrapper 를 들고 각각의 1 줄 책임을 적어라.

??? answer "정답 / 해설"
    - `requester_frontend` — host SQ → packet build, BTH/RETH 채움.
    - `completer_frontend` — incoming response (ACK/NAK/Read Response) 처리, CQE 생성.
    - `completer_retry` — timer / NAK / SACK 기반 재전송 결정.
    - `responder_frontend` — incoming request 처리, ACK 생성, MSN 증가.
    - `cc_module` — DCQCN / RTTCC 등 CC 알고리즘.

    (+ `mmu_wrapper` — IOVA→PA 변환).

## Q2. (Understand)

`completer_frontend` 의 `m_comp_payload_drop1`, `drop2`, `drop3` 신호가 의미하는 바는?

??? answer "정답 / 해설"
    응답 패킷에 payload 가 동승했을 때 그 payload 를 *어느 단계에서 drop 할지* 를 알리는 1-bit 신호 3 종 (각 stage 별).
    - `drop1=1` → 종료, `drop2` 없음.
    - `drop1=0, drop2=1` → 종료.
    - `drop1=0, drop2=0` → 다음 stage 로 계속.

    Confluence: *Completer* §3.1.3.2.

## Q3. (Apply)

`s_data_port_0` (SWQ read port modify/delete), `s_data_port_3` (read_init), `s_data_port_4` (read) 가 분리된 이유는?

??? answer "정답 / 해설"
    각 channel 은 **다른 thread / 다른 outstanding 한도** 를 가짐. modify(완료) ↔ retry-fetch 가 같은 channel 에 들어가야 ordering 이 보장된다. read_init / read 는 multi-packet read 응답을 staging 하는 별도 흐름이라 분리.

## Q4. (Analyze)

200G + 250 MHz + 1K MTU 환경에서 T_arrival ≈ 11 cycle, broken `th_dma_write` II = 12 cycle. 왜 throughput 이 0 으로 수렴하나?

??? answer "정답 / 해설"
    1 cycle 의 deficit 가 매 패킷마다 누적 → input buffer 점유율 단조 증가 → buffer overflow → flow control oscillation → wire 위 throughput cliff.
    pipeline 구조상 **이미 출발한 패킷의 deficit 는 회복 불가**. 즉 II 와 T_arrival 의 = 또는 < 관계가 절대적이다.

    Confluence: *[completer_frontend] 1K MTU RDMA Read >4KB throughput 저하 분석* (id=1276379157).

## Q5. (Analyze)

HLS C++ 의 `pipelined for-loop` 가 hot path 에서 위험한 이유는?

??? answer "정답 / 해설"
    pipelined for-loop 는 **항상 최소 1 FSM state 를 소비**한다 (loop counter 의 register stage). T_arrival 에 직접 묶인 thread 에서는 이 1 state 가 II 를 1 cycle 늘려 throughput cliff 를 유발.
    대안: unrolled if-chain, sticky pop, 또는 flatten 후 dataflow.

## Q6. (Evaluate)

`completer_frontend` 와 `completer_retry` 를 별도 wrapper 로 분리한 설계 결정의 근거를 평가하라.

??? answer "정답 / 해설"
    - Frontend = 도착 즉시 처리 (II 가 T_arrival 에 직접 종속, dense pipeline).
    - Retry = sparse trigger (timer / NAK / SACK), FSM 이 큼.
    - 한 pipeline 에 묶으면 sparse retry FSM 이 frontend critical path 를 잠식 → 둘 다 timing fail.
    - 분리 결과: frontend 는 dense, retry 는 high-state 로 별도 최적화 가능. **timing closure 의 명확한 결정**.
