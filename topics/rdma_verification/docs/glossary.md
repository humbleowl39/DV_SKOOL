# 용어집 (Glossary)

ISO 11179 — 단일 문장 정의 + Source + Related + Example + See also

---

## A

### Analysis Port (AP)
**Definition.** UVM TLM 1:N broadcast 메커니즘으로, producer 가 publish 한 transaction 을 0 개 이상의 subscriber 가 동일한 시각에 수신하는 export/imp 통신 구조.
**Source.** UVM 1.2 Reference Manual §12.2.
**Related.** subscriber, `analysis_export`, `analysis_imp`.
**Example.**
```systemverilog
uvm_analysis_export #(vrdma_base_command) issued_wqe_ap;
```
**See also.** [M04 — Analysis Port Topology](04_analysis_port_topology.md).

---

## C

### `c2h_tracker`
**Definition.** DUT 가 host 메모리로 발생시키는 모든 C2H DMA 트랜잭션을 추적·검증하는 RDMA-TB 의 dma_env 컴포넌트.
**Source.** `lib/base/component/env/dma_env/vrdma_c2h_tracker/vrdma_c2h_tracker.svh`.
**Related.** PA matching, ordering, ErrQP, `is_err_qp_registered`.
**Example.** `m_qp_tracker[node][qp].write_pa_queue` 가 expected PA 큐.
**See also.** [M10 — C2H Tracker Error](10_debug_c2h_tracker.md).

### Comparator (data_env)
**Definition.** RDMA-TB 에서 두 노드의 메모리 또는 transaction object 를 비교하여 데이터 정합성을 검증하는 컴포넌트(1side / 2side / imm) 의 통칭.
**Source.** `lib/base/component/env/data_env/vrdma_{1side,2side,imm}_compare.svh`.
**Related.** `flushQP`, `err_enabled`.
**See also.** [M08 — Data Integrity](08_debug_data_integrity.md).

### `cmd.expected_error`
**Definition.** 단일 RDMA verb command 에 대해 에러 CQE 가 발생할 것을 미리 알려 fatal 을 회피시키는 per-cmd 게이트 플래그.
**Source.** `lib/base/component/env/agent/handler/vrdma_cq_handler.svh:233-234, 349-350`.
**Related.** `isErrQP`, `error_occured`, `F-CQHDL-TBERR-0003`.
**Example.** `read_cmd.expected_error = 1;`
**See also.** [M06 — Error Handling Path](06_error_handling_path.md), [M11 — Unexpected Error CQE](11_debug_unexpected_err_cqe.md).

### Completion Queue Entry (CQE)
**Definition.** 한 RDMA work request 의 완료를 알리는 host-memory entry 로, work request id, status (success/error), 타입별 부가 정보를 담는 구조체.
**Source.** IBTA Specification Volume 1 §11 (Completion Queue).
**Related.** `wc_status`, `cq_handler`, CQ polling.
**See also.** [M09 — CQ Poll Timeout](09_debug_cq_poll_timeout.md).

---

## D

### Default Sequence
**Definition.** UVM phase 진입 시 sequencer 에 자동으로 create + start 되는 등록된 sequence 클래스.
**Source.** UVM 1.2 RM §10.10.
**Related.** `vrdma_init_seq`, `post_configure_phase`.
**Example.** `uvm_config_db#(uvm_object_wrapper)::set(this, "*.sequencer.post_configure_phase", "default_sequence", vrdma_init_seq::get_type());`
**See also.** [M03 — Phase & Test Flow](03_phase_test_flow.md).

### `deregisterQP`
**Definition.** 한 QP 를 comparator/tracker 의 추적 대상에서 제거하면서 pending 큐를 flush 하는 lifecycle 메서드.
**Source.** `vrdma_1side_compare.svh:1316`, `vrdma_c2h_tracker.svh:330`.
**Related.** `flushQP`, `err_enabled`, `RDMAQPDestroy`.
**See also.** [M06 — Error Handling Path](06_error_handling_path.md).

---

## E

### `enable_error_cq_poll`
**Definition.** `vrdma_cq_handler` 가 `monitorErrCQ` 백그라운드 task 를 실행할지 제어하는 static 플래그(default 1).
**Source.** `lib/base/component/env/agent/handler/vrdma_cq_handler.svh:16, 80`.
**Related.** ERR_CQ, `try_once`.
**Example.** `vrdma_cq_handler::enable_error_cq_poll = 0;`
**See also.** [M06 — Error Handling Path](06_error_handling_path.md).

### `err_enabled` (static)
**Definition.** comparator(1side/2side/imm) 와 c2h_tracker 에서 모든 QP 의 deregister 시 자동으로 flush/skip 동작을 활성화하는 컴포넌트별 static 플래그.
**Source.** `vrdma_1side_compare.svh:85`, `vrdma_2side_compare.svh:101`, `vrdma_imm_compare.svh:99`, `vrdma_c2h_tracker.svh:98`.
**Related.** `isErrQP`, `flushQP`.
**See also.** [M06 — Error Handling Path](06_error_handling_path.md).

### ErrQP (Error QP)
**Definition.** `setErrState(1)` 호출로 마킹된 QP 로, 이후 모든 verb 가 driver 에서 silent skip 되며 `completed_wqe_ap` 로도 전달되지 않는다.
**Source.** `vrdma_driver.svh:530, 1208, 1327`.
**Related.** `expected_error`, `RDMAQPDestroy(.err(1))`.
**See also.** [M06 — Error Handling Path](06_error_handling_path.md).

---

## F

### `flushQP`
**Definition.** 특정 QP 와 관련된 comparator/tracker 의 pending 큐(write/read/send/recv/cqe 등)를 일괄 삭제하는 정리 메서드.
**Source.** `vrdma_1side_compare.svh`, `vrdma_2side_compare.svh`, `vrdma_imm_compare.svh`.
**Related.** `deregisterQP`, `err_enabled`, ErrQP.
**See also.** [M06 — Error Handling Path](06_error_handling_path.md).

---

## G

### `gen_id` Pool
**Definition.** RDMA-TB 가 MR Fast Register / Re-register 를 추적하기 위해 부여하는 generation identifier 의 풀.
**Source.** `lib/base/component/pool/vrdma_gen_id_pool.svh`.
**Related.** Fast Register, MR re-register race.
**See also.** [M02 — Component Hierarchy](02_component_hierarchy.md), [M08 — Data Integrity](08_debug_data_integrity.md).

---

## H

### Handler (`*_handler`)
**Definition.** RDMA verb opcode 별 stateless forwarder 컴포넌트(send/recv/write/read/cq) 로, AP 라우팅만 수행하고 자체 state 를 보유하지 않는다.
**Source.** `lib/base/component/env/agent/handler/vrdma_*_handler.svh`.
**Related.** Stateless 보존 원칙, `cq_handler`.
**See also.** [M02 — Component Hierarchy](02_component_hierarchy.md), [M05 — Extension 4원칙](05_extension_principles.md).

### H2C QID
**Definition.** Host → Card 방향의 QDMA bypass queue ID 로, RDMA-TB 에서 6개 카테고리(REQ/RSP/RECV/CMD/CTRL/MISS_PA) 로 정의된다.
**Source.** `lib/base/def/vrdma_defs.svh:75-80`.
**Related.** C2H QID, `RDMA_REQ_H2C_QID`, `RDMA_CMD_H2C_QID`.
**See also.** [M07 — H2C/C2H QID Reference](07_h2c_c2h_qid_map.md).

---

## I

### IOVA Translator (`vrdma_iova_translator`)
**Definition.** TB 측에서 IOVA(IO Virtual Address) 를 PA(Physical Address) 로 변환하여 expected DMA 주소를 산출하는 data_env 의 helper 컴포넌트.
**Source.** `lib/base/component/env/data_env/vrdma_iova_translator.svh`.
**Related.** PTW, `buildPageTable`.
**See also.** [M08 — Data Integrity](08_debug_data_integrity.md).

### `isErrQP()`
**Definition.** QP 객체가 ErrQP 상태인지 반환하는 메서드로, driver / comparator / tracker 의 모든 에러 게이트의 1차 분기 조건이다.
**Source.** `vrdma_driver.svh:1208, 1327`, `vrdma_2side_compare.svh:697`.
**Related.** `setErrState`, ErrQP.
**See also.** [M06 — Error Handling Path](06_error_handling_path.md).

---

## M

### `monitorErrCQ`
**Definition.** `vrdma_cq_handler` 가 ERR_CQ 를 백그라운드로 폴링하여 에러 CQE 를 발견·처리하는 task.
**Source.** `vrdma_cq_handler.svh:80`.
**Related.** `enable_error_cq_poll`, `try_once`.
**See also.** [M06](06_error_handling_path.md), [M11](11_debug_unexpected_err_cqe.md).

---

## P

### `post_configure_phase`
**Definition.** UVM `configure_phase` 직후에 실행되는 task phase 로, RDMA-TB 에서 `vrdma_init_seq` 가 default sequence 로 자동 시작되어 HW 초기화(QP/CQ/MR 등록)를 수행하는 시점이다.
**Source.** UVM 1.2 RM §9.8 + `lib/base/object/sequence/vrdma_init_seq.svh`.
**Related.** Default sequence, `vrdma_init_seq`.
**See also.** [M03 — Phase & Test Flow](03_phase_test_flow.md).

---

## Q

### QDMA bypass interface
**Definition.** RDMA IP 와 host 간 모든 DMA 가 흐르는 단일 QDMA 인터페이스로, 각 트랜잭션에 부여된 QID 가 서브시스템을 식별한다.
**Source.** `lib/base/def/vrdma_qdma_defs.svh`, `lib/base/def/vrdma_defs.svh:75-88`.
**Related.** H2C QID, C2H QID.
**See also.** [M07 — H2C/C2H QID Reference](07_h2c_c2h_qid_map.md).

### QP Pool (`vrdma_qpool`)
**Definition.** TB 가 생성·관리하는 모든 Queue Pair 객체를 보관하는 RDMA-TB 의 리소스 풀.
**Source.** `lib/base/component/pool/vrdma_qpool.svh`.
**Related.** MR pool, `RDMAQPCreate`, `qp_reg_ap`.
**See also.** [M02 — Component Hierarchy](02_component_hierarchy.md).

---

## R

### `RDMAQPDestroy(.err)`
**Definition.** QP 를 destroy 하면서 outstanding 잔존을 허용할지(err=1) 여부를 결정하는 verb 로, err=1 시 모든 횡단 컴포넌트가 `flushQP` 를 수행한다.
**Source.** `vrdma_top_sequence.svh:99, 107, 983`, `vrdma_driver.svh:530`.
**Related.** ErrQP, `flushQP`, `err_enabled`.
**See also.** [M06 — Error Handling Path](06_error_handling_path.md).

### RC (Reliable Connected)
**Definition.** RDMA service type 중 하나로, 단일 connected QP 페어 간 packet ordering 과 reliable delivery 를 보장한다.
**Source.** IBTA Volume 1 §9.7.4.
**Related.** OPS/SR (Out-of-order / Reliable Datagram), C2H ordering.
**See also.** [M10 — C2H Tracker Error](10_debug_c2h_tracker.md).

---

## S

### Sequencer (`vrdma_sequencer`)
**Definition.** RDMA-TB 의 노드별 stateful 컴포넌트로, per-QP 에러 상태(`wc_error_status`, `debug_wc_flag`) 와 outstanding 카운터를 보유하며 stateless `vrdma_top_sequence` 에 state 소유권을 제공한다.
**Source.** `lib/base/component/env/agent/sequencer/vrdma_sequencer.svh:19-20, 36, 75-76, 179-181`.
**Related.** `top_vseqr`, Stateless 보존 원칙.
**See also.** [M03 — Phase & Test Flow](03_phase_test_flow.md), [M05 — Extension 4원칙](05_extension_principles.md).

### `setErrState(1)`
**Definition.** QP 객체를 ErrQP 상태로 전이시키는 메서드로, driver 가 SQDestroy.err 또는 cq_handler 가 에러 CQE 를 받을 때 호출된다.
**Source.** `vrdma_driver.svh:530`, `vrdma_cq_handler.svh:223`.
**Related.** `isErrQP`, ErrQP.
**See also.** [M06 — Error Handling Path](06_error_handling_path.md).

### `start_item` / `finish_item` 패턴
**Definition.** UVM sequence 가 특정 sequencer 로 transaction 을 발행하기 위해 사용하는 표준 호출 페어로, RDMA-TB 에서 멀티노드 verb 라우팅의 핵심 메커니즘이다.
**Source.** UVM 1.2 RM §10.7.
**Related.** `.sequencer(t_seqr)` 명시 인자.
**See also.** [M03 — Phase & Test Flow](03_phase_test_flow.md).

### Stateless (Stateless Class)
**Definition.** 입력을 받아 변환·전달만 수행하고 내부 state(트랜잭션 히스토리, 카운터 등)를 보유하지 않도록 의도적으로 설계된 클래스.
**Source.** Confluence "Adding New Components" §원칙 4.
**Related.** Handler, `vrdma_top_sequence`, `vrdma_data_cqe_handler`.
**See also.** [M05 — Extension 4원칙](05_extension_principles.md).

---

## T

### `top_vseqr` (`vrdma_top_virtual_sequencer`)
**Definition.** 모든 노드의 `vrdma_sequencer` 들을 children 으로 가지는 top-level virtual sequencer 로, 테스트 진입점에서 sequence 가 시작되는 위치이다.
**Source.** `lib/base/component/env/agent/sequencer/vrdma_top_virtual_sequencer.svh`.
**Related.** `host_vseqr`, `rdma_seqr`.
**See also.** [M03 — Phase & Test Flow](03_phase_test_flow.md).

### `try_cnt` / `timeout_count`
**Definition.** CQ polling 의 반복 시도 횟수(`try_cnt`) 와 그 한계값(`timeout_count`) 으로, `try_cnt > timeout_count` 와 `!c2h_tracker::active` 가 동시에 충족되면 `exceptionTimeout` 이 트리거된다.
**Source.** `vrdma_driver.svh:1484-1488`.
**Related.** `c2h_tracker::active`, `RDMACQPoll`.
**See also.** [M09 — CQ Poll Timeout](09_debug_cq_poll_timeout.md).

---

## V

### `vrdma_init_seq`
**Definition.** post_configure_phase 의 default sequence 로 자동 실행되어 RDMA HW 초기화(QP/CQ/MR 등록 등)를 수행하는 sequence 클래스.
**Source.** `lib/base/object/sequence/vrdma_init_seq.svh`.
**Related.** Default Sequence, `post_configure_phase`.
**See also.** [M03 — Phase & Test Flow](03_phase_test_flow.md).

### `vrdmatb_top_env`
**Definition.** RDMA-TB 의 top env 컨테이너로, 두 노드(`vrdma_node_env`)와 횡단 검증 env(data_env, dma_env, ntw_env, RAL env)를 포함한다.
**Source.** `lib/base/component/env/vrdmatb_top_env.svh`.
**Related.** `vrdma_node_env`, `data_env`, `dma_env`.
**See also.** [M01 — TB Overview](01_tb_overview.md).

---

## W

### `wc_status`
**Definition.** Completion Queue Entry 의 결과 코드 enum 으로, `IB_WC_SUCCESS` 외 RETRY 계열(12, 13)은 조건부 발생 가능, 그 외 모든 값은 RDMA-TB 정상 시뮬에서 발생 시 DUT 버그를 의미한다.
**Source.** IBTA Volume 1 §11.6.
**Related.** `WC_RETRY_EXC_ERR`, `WC_LOC_PROT_ERR`, `WC_REM_ACCESS_ERR`, `WC_WR_FLUSH_ERR`.
**See also.** [M11 — Unexpected Error CQE](11_debug_unexpected_err_cqe.md).

### `wc_error_status[qp][$]`
**Definition.** `vrdma_sequencer` 가 보유하는 per-QP 에러 상태 큐로, 에러 CQE 의 `wc_status` 들을 시간 순으로 기록한다.
**Source.** `lib/base/component/env/agent/sequencer/vrdma_sequencer.svh:19`.
**Related.** `clearErrorStatus`, `debug_wc_flag`.
**See also.** [M11 — Unexpected Error CQE](11_debug_unexpected_err_cqe.md).
