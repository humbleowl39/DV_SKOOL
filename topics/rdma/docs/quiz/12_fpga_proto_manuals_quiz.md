# Quiz — Module 12: FPGA Prototyping & Lab Manuals

[← Module 12 본문으로 돌아가기](../12_fpga_proto_manuals.md)

---

## Q1. (Remember)

FPGA Prototyping 101 의 6 단계를 순서대로 나열하라.

??? answer "정답 / 해설"
    0. Prepare the project (modified) — empty calculator
    1. Build user application
    2. Build a device driver
    3. Design a calculator engine
    4. Send result to device driver
    5. Send interrupt to device driver

## Q2. (Understand)

새 bitfile 을 받았을 때 *sanity check* 도구는 어느 것을 가장 먼저 사용하며 그 이유는?

??? answer "정답 / 해설"
    **rdma-test (또는 mango-rdma-test)**. 5 분 안에 small SEND/WRITE/READ 1000회 정도가 끝나며, GPU 환경 의존성이 없어 빠르게 1차 통과 여부를 본다.
    fio 와 RCCL 은 production-stage workload — perf regression 또는 AI 시나리오에 사용.

## Q3. (Apply)

Adaptive Routing 활성화 환경에서 RDMA-IP 검증 시 추가로 켜야 하는 사내 기능 두 가지는?

??? answer "정답 / 해설"
    - **SACK (Selective ACK)** — packet 별 OOO 도착 처리.
    - **per-path PSN tracking** — multipath 별 PSN 누적 추적.

    이 두 기능 없이는 RC strict in-order 가정이 깨지면서 false NAK 다발.

## Q4. (Analyze)

SR-IOV QoS 의 두 설정 방식 (`ip link set vf` 기반 best-effort, TC + DSCP 매핑 기반 강제) 의 차이를 분석하라.

??? answer "정답 / 해설"
    - `ip link set vf` (best-effort) — `min_tx_rate` / `max_tx_rate` 만으로 분배. 보장이 약함, 다른 VF 의 burst 영향 받음.
    - TC + DSCP 매핑 (강제) — RoCEv2 의 PFC priority class 와 결합해 traffic class 별로 강제 분리. Lossless / SLA 환경에 적합. 단, switch fabric 도 같은 매핑을 알아야 함.

## Q5. (Evaluate)

RDMA debug register 의 sticky bit 를 bring-up 직후 *clear-on-read* 로 한 번 패스하는 절차를 의무화한 이유를 평가하라.

??? answer "정답 / 해설"
    - Sticky bit 는 reset 후에도 잔여 상태를 유지할 수 있음 (HW 디자인 결정).
    - 잔여 상태가 남아 있으면 **첫 testcase 의 진단 reg read 가 *과거* 결과를 반영** 해 false fail / 잘못된 root cause 분석.
    - 따라서 **bring-up sequence 자체에 clear pass 를 포함** 해야 모든 testcase 가 깨끗한 출발점에서 시작 — 검증 결과의 재현성과 진단성을 동시에 보장.
