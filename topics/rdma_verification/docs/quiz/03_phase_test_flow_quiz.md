# Module 03 퀴즈 — UVM Phase & Test Flow

본문: [Module 03](../03_phase_test_flow.md)

---

### Q1. (Remember) UVM phase 8단계 중 RDMA-TB 가 default sequence (`vrdma_init_seq`) 를 자동 시작하는 phase 는?
**정답.** `post_configure_phase`.
**Why.** Module 03 §1 — HW 초기화(QP/CQ/MR 등록)는 RAL 컨피그(configure_phase) 직후에 실행.

### Q2. (Understand) `start_item` / `finish_item` 패턴에서 `.sequencer(t_seqr)` 를 명시해야 하는 이유는?
**정답.** `vrdma_top_sequence` 는 `top_vseqr` 에서 시작되지만, 개별 verb 는 어느 노드의 `vrdma_sequencer` 로 보낼지 명시적 라우팅이 필요. 노드 격리 보장.
**Why.** 멀티노드 설계의 핵심.

### Q3. (Apply) CQ 폴링을 `start_item` / `finish_item` 으로 시도하면 무엇이 잘못되는가?
**정답.** CQ 폴링은 transaction 발행이 아니라 **완료 대기** 이므로 driver 의 WQE 발행 큐와 충돌. dead-lock 가능. 정답: `cq_handler.RDMACQPoll` 직접 호출(패턴 3).
**Why.** 4 시퀀스 패턴의 의도 차이.

### Q4. (Analyze) 시퀀스에 per-QP outstanding 카운터를 추가하면 어떤 문제가 생기는가? 두 가지 이상 답하시오.
**정답.** (1) 시퀀스 재사용 시 이전 카운터 잔존(`stale state`), (2) 멀티노드에서 한 시퀀스가 두 노드에 동시 사용되면 카운터 cross-talk, (3) flush/reset 메커니즘 부재 → 디버깅 어려움. 정답: `vrdma_sequencer` 에 둠.
**Why.** Module 05 #4 Stateless 보존.

### Q5. (Evaluate) "main_phase 에서 raise/drop_objection 없이 시퀀스를 시작해도 어차피 main_phase 끝까지는 동작한다" 는 주장을 평가하시오.
**정답.** 잘못됨. UVM phase 는 모든 컴포넌트가 objection 을 raise 하지 않으면 즉시 종료. 시퀀스가 시작되기도 전에 phase 가 끝나 verb 발행 자체가 안 됨.
**Why.** UVM phase semantics 점검.

### Q6. (Apply) 한 테스트에서 두 노드 모두에 동시에 SEND 를 발행하려면 어떻게 해야 하는가?
**정답.**
```systemverilog
fork
  begin
    send_seq.start_item(send_cmd0, .sequencer(rdma_seqr[0]));
    send_seq.finish_item(send_cmd0);
  end
  begin
    send_seq.start_item(send_cmd1, .sequencer(rdma_seqr[1]));
    send_seq.finish_item(send_cmd1);
  end
join
```
**Why.** `fork-join` + `.sequencer(t_seqr)` 명시.

### Q7. (Analyze) `check_phase` 에서 `c2h_tracker` 가 fatal 을 안 내고 warning 만 내는 시나리오는 언제인가?
**정답.** ErrQP 가 deregister 되었거나 `vrdma_c2h_tracker::err_enabled = 1` 인 경우. `qp_obj.isErrQP() || err_enabled` 면 outstanding 잔존도 fatal 대신 warning(Module 06 §5).
**Why.** Error gate 의 적용 범위 비교.

### Q8. (Create) 새 테스트에서 init seq 를 override 하고 싶다. UVM factory 로 어떻게 하는가?
**정답.**
```systemverilog
class my_test extends rdma_base_test;
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    vrdma_init_seq::type_id::set_type_override(my_init_seq::get_type());
  endfunction
endclass
```
**Why.** UVM factory 의 type_id override 패턴 — RDMA-TB 도 표준 UVM 1.2 메커니즘 사용.
