# Quiz — Module 08: RDMA-TB 검증 환경 & DV 전략

[← Module 08 본문으로 돌아가기](../08_rdma_tb_dv.md)

---

## Q-Conf-A. (Understand — Confluence)

사내 *Coverage define* 운영에서 PR 단위로 의무화된 두 항목은?

??? answer "정답 / 해설"
    1. **Coverage define module list** 의 갱신 (단일 진실).
    2. PR description 의 **min cov plan 한 단락** (새 feature 의 first PR).

    추가로 격주 coverage sync meeting 에서 hole / dropped bin / cross 추가 확정.

## Q-Conf-B. (Apply — Confluence)

새 wrapper 의 *base coverage* 와 *feature coverage* 를 설계할 때 다음 중 어디에 분류해야 하는지 답하라.

> (i) MTU=1024 의 4-packet WRITE 의 first/middle/last 분포
> (ii) Atomic Write (MPE) opcode 적중 분포
> (iii) NAK syndrome 종류별 발생 분포
> (iv) Adaptive Routing 활성 시 OOO PSN gap 분포

??? answer "정답 / 해설"
    - (i) **base** — 모든 wrapper 에서 닫혀야 할 데이터 path.
    - (ii) **feature** — MPE 지원이 옵션이므로.
    - (iii) **base** — 표준 RC 동작.
    - (iv) **feature** — AR mode 활성 시에만.

---

## Q1. (Remember)

RDMA-TB 의 `lib/` 분류 4 가지를 들어라.

??? answer "정답 / 해설"
    1. **base/** — 모든 feature 가 알아야 하는 핵심 인프라
    2. **ext/** — 특정 feature 에서만 필요한 확장 (CCMAD, ECN, error_handling, rdma_verbs, application 등)
    3. **external/** — 3rd party VIP wrapper (예: VPFC)
    4. **submodule/** — Sub-IP 전용 verification (design hierarchy 따라; MMU/PTW/TLB, RQ fetcher, CRC)

## Q2. (Understand)

`vrdmatb_top_env` 에 포함되는 env 의 종류를 5 개 이상 들어라.

??? answer "정답 / 해설"
    `vrdma_host_env`, `vrdma_node_env`, `vrdma_ntw_env`, `vrdma_ntw_model_env`, `vrdma_memory_env`, `vrdma_data_env`, `vrdma_dma_env`, `vrdma_ral_env`, `vrdma_ipshell_env`, `vrdma_lp_env`, `vrdma_elc_env`.

    각 env 가 host CPU 모델 / 네트워크 / DMA / RAL / 데이터 path 검증 등 별도 책임을 가짐.

## Q3. (Apply)

새로운 RDMA WRITE 의 corner case 검증 (예: 8-byte aligned write 의 byte order) 을 추가하려면 어디에 코드를 배치해야 하는가?

??? answer "정답 / 해설"
    `lib/ext/component/rdma_verbs/write/` 에 **새 test 추가** — 기존 write test 와 같은 디렉토리.

    Sequence/scoreboard 가 base 의 기능으로 충분하면 base 수정 없이 test 만 추가. Base 수정이 필요하면 그 이유를 명확히 (다른 feature 에도 도움 되는지) 검증 후 base/ 에 추가.

## Q4. (Analyze)

Agent 의 handler 가 GoF Strategy 패턴을 따르는 이유와, 그렇게 함으로써 얻는 검증 환경의 이점을 분석하라.

??? answer "정답 / 해설"
    **이유**: 각 OpCode (SEND/RECV/READ/WRITE) 마다 처리 단계 (sg_list 검증, RETH 구성, ACK 대기, completion 생성, error 처리) 가 다름. 한 Driver 가 if-else 로 모든 OpCode 를 다루면 거대한 monolith.

    **이점**:

    1. **확장성**: 새 OpCode 추가 = 새 handler 클래스 추가, 다른 코드 영향 없음.
    2. **테스트 가능성**: 각 handler 를 단독 테스트 가능 (mock sequencer).
    3. **재사용**: 같은 handler 를 다른 환경에서도 재사용 가능 (sub-IP TB, IP-top TB 모두).
    4. **명확한 책임 분리**: SEND 처리에 read_handler 가 끼어드는 일이 없음.

## Q5. (Evaluate)

`vrdma_io_err_top_seq` 의 callback 메커니즘이 새 error 시나리오 추가 시 코드 변경량을 어떻게 줄이는가? 이 메커니즘의 한계는?

??? answer "정답 / 해설"
    **장점**:

    - 새 error 시나리오 = 새 callback 객체 (e.g. `vrdma_callback_corrupt_rkey_obj`) 등록 + 기존 sequence 재사용.
    - Sequence/test 본문은 수정 없이, callback 만으로 RX/TX path 의 packet 을 drop/duplicate/corrupt.
    - 9 시나리오 (S1~S9) 모두 동일 sequence 의 다른 callback.

    **한계**:

    - Callback 이 packet 단위 hook 이므로 **transaction-level 에러** (예: WQE 의 attribute 이상) 는 callback 으로 못 표현.
    - Callback 시점이 RX/TX 만 — middle (e.g. switch buffer) 의 동작은 모델 외부.
    - Stateful error (예: 시간 경과 후 자동 회복) 는 callback 만으로 어렵 — 별도 model 필요.

    → 따라서 callback 으로 안 되는 시나리오는 새 sequence 또는 새 model 추가가 필요.
