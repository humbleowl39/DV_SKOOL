# Quiz — Module 07: Congestion Control & Error Handling

[← Module 07 본문으로 돌아가기](../07_congestion_error.md)

---

## Q1. (Remember)

RDMA-TB 의 error_handling vplan 에서 다음 WC status 의 트리거를 매칭하라.

a) `WC_RETRY_EXC_ERR`
b) `WC_RNR_RETRY_EXC_ERR`
c) `WC_REM_ACCESS_ERR`
d) `WC_REM_INV_RD_REQ_ERR`

선택지: (1) Max read outstanding 위반, (2) RNR retry exhaust, (3) Local ACK / PSE / Implied NAK retry exhaust, (4) MR access flag / range / PD / R-Key 위반

??? answer "정답 / 해설"
    a → (3), b → (2), c → (4), d → (1).

    `RNR_RETRY_EXC_ERR` 는 `RETRY_EXC_ERR` 와 별도 status — RNR 메커니즘 자체가 별도 카운터.

## Q2. (Understand)

PFC 만 사용하고 ECN+DCQCN 을 안 쓰는 환경의 위험성을 두 가지 들어라.

??? answer "정답 / 해설"
    1. **Cyclic dependency → Deadlock / PFC storm**: 여러 priority 가 서로 PAUSE 신호를 전달해 fabric 전체가 멈출 수 있음.
    2. **Head-of-line blocking**: PFC 는 priority 전체를 멈추므로 한 flow 의 혼잡이 같은 priority 의 다른 flow 를 모두 stall.

    추가: PFC 는 fast reaction 이지만 점진적인 rate adjust 가 없어 거시적 fairness 부족.

## Q3. (Apply)

S5 (Remote MR access flag violation) 시나리오를 RDMA-TB 환경에서 구현하려면 어떤 callback 을 어디에 등록해야 하는가?

??? answer "정답 / 해설"
    - NODE1 의 MR 등록 시 `mr_access_flag_node1` 에서 **Remote Write/Read 를 클리어**.
    - 그 외 traffic 은 `vrdma_io_err_top_seq` 로 정상 실행.
    - 결과: requester (NODE0) 의 send CQ 에 `WC_REM_ACCESS_ERR`, responder (NODE1) 의 Error CQ 에 `IB_EVENT_QP_ACCESS_ERR` + `WC_FLAG_RESP_ACCESS`.

    검증 항목: C1 (sender WC), C2 (responder Error CQ), C3 (debug flag), C4 (Error CQE 존재), C5 (IRQ 발생).

## Q4. (Analyze)

DCQCN 에서 sender 의 rate 회복 곡선이 너무 느리면 (parameter 가 conservative) 어떤 부작용이 생길 수 있는가?

??? answer "정답 / 해설"
    - **Throughput 손실**: congestion 해소 후에도 rate 가 낮은 상태로 남아 link bandwidth 미활용.
    - **Tail latency 악화**: 회복 늦어 backlog 가 길어지면 일부 flow 의 latency 가 spike.
    - **Fairness 왜곡**: 선두 flow 가 회복하기 전에 새 flow 가 들어오면 비대칭 분배.

    → 실무에서 α (감소 비율), R_min, recovery time 의 tuning 이 deployment 별로 중요. Conservative parameter 가 stability 와 efficiency 사이의 균형 결정.

## Q5. (Evaluate)

"S1~S9 모든 시나리오가 pass 하면 error handling 검증은 충분하다" 는 주장을 평가하라.

??? answer "정답 / 해설"
    **불충분**.

    - S1~S9 는 각 시나리오의 **단일 path** 만 커버.
    - 실제 검증 가치는 **cross coverage** — `status × outstanding × node × CQ` 등의 cross 가 아직 hole 일 수 있음.
    - 그래서 RDMA-TB 의 `vrdma_error_handling_cov` 는 cg_error_type, cg_outstanding, cg_status_x_outstanding, cg_node_x_status, cg_cq_x_status 의 cross 를 정의.
    - Closure 전략: 시나리오 × traffic mix × seed 변경으로 cross 를 메움.

    또한 S1~S9 외에 transient 상태 (Err → Reset 의 cleanup), parameter 경계 (retry_cnt=0, retry_cnt=max), multi-error coexistence 등 추가 시나리오 필요.
