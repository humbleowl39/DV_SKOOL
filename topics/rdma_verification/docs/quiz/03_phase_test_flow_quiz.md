# Module 03 퀴즈 — UVM Phase & Test Flow

본문: [Module 03](../03_phase_test_flow.md)

---

### Q1. (Remember) UVM phase 8단계 중 RDMA-TB 가 default sequence (`vrdma_init_seq`) 를 자동 시작하는 phase 는?
**정답.** `post_configure_phase`.
**Why.** `post_configure_phase`는 `configure_phase`(RAL을 통한 레지스터 초기값 설정) 직후에 실행된다. RDMA HW 초기화(QP/CQ/MR 등록)는 레지스터 설정이 완료된 후에야 의미가 있으므로, `vrdma_init_seq`를 이 시점에 배치하는 것이 논리적으로 올바르다. 만약 `build_phase`나 `connect_phase`에서 초기화를 시도하면 RAL 설정이 아직 완료되지 않아 HW가 응답하지 않는다. UVM phase 순서와 RDMA 초기화 의존성을 연결하는 것이 이 문제의 핵심이다.

### Q2. (Understand) `start_item` / `finish_item` 패턴에서 `.sequencer(t_seqr)` 를 명시해야 하는 이유는?
**정답.** `vrdma_top_sequence` 는 `top_vseqr` 에서 시작되지만, 개별 verb 는 어느 노드의 `vrdma_sequencer` 로 보낼지 명시적 라우팅이 필요. 노드 격리 보장.
**Why.** `top_vseqr`(virtual sequencer)는 모든 노드의 `vrdma_sequencer`를 children으로 가지는 진입점이지, 특정 노드로 자동 라우팅하지 않는다. `.sequencer(t_seqr)`를 명시하지 않으면 UVM은 현재 실행 중인 sequencer(즉 `top_vseqr`)로 transaction을 보내려 하는데, virtual sequencer는 driver와 연결되지 않으므로 항목이 드롭되거나 deadlock이 발생한다. 멀티노드 환경에서 "어느 노드에 verb를 보낼지"를 명시하는 것은 의도를 코드로 표현하는 필수 패턴이다.

### Q3. (Apply) CQ 폴링을 `start_item` / `finish_item` 으로 시도하면 무엇이 잘못되는가?
**정답.** CQ 폴링은 transaction 발행이 아니라 **완료 대기** 이므로 driver 의 WQE 발행 큐와 충돌. dead-lock 가능. 정답: `cq_handler.RDMACQPoll` 직접 호출(패턴 3).
**Why.** `start_item/finish_item`은 driver로 새 transaction을 발행하는 패턴이다. CQ 폴링은 이미 발행된 WQE의 완료를 기다리는 행위이므로, driver의 WQE 발행 파이프라인을 통해 처리하는 것은 의미론적으로 잘못되었다. driver가 "폴링 transaction"을 처리하려 할 때 실제 WQE outstanding이 남아 있으면 순서가 뒤바뀌거나 deadlock이 생긴다. `cq_handler.RDMACQPoll` 직접 호출이 올바른 이유는, 폴링이 "driver 발행 큐 밖에서" 완료를 대기하는 별도 경로이기 때문이다.

### Q4. (Analyze) 시퀀스에 per-QP outstanding 카운터를 추가하면 어떤 문제가 생기는가? 두 가지 이상 답하시오.
**정답.** (1) 시퀀스 재사용 시 이전 카운터 잔존(`stale state`), (2) 멀티노드에서 한 시퀀스가 두 노드에 동시 사용되면 카운터 cross-talk, (3) flush/reset 메커니즘 부재 → 디버깅 어려움. 정답: `vrdma_sequencer` 에 둠.
**Why.** sequence 오브젝트는 테스트마다 새로 생성되거나 재사용될 수 있어, 내부 카운터가 이전 실행 상태를 유지하는 stale state 문제가 생긴다. 멀티노드 시뮬에서 동일 시퀀스 인스턴스를 두 노드가 공유하면 카운터 업데이트가 섞여 cross-talk가 발생한다. state는 lifetime이 명확한 컴포넌트(`vrdma_sequencer`)에 두어야 flush/reset 시점을 제어할 수 있다. 이것이 Module 05 Stateless 보존 원칙의 직접 적용 사례다.

### Q5. (Evaluate) "main_phase 에서 raise/drop_objection 없이 시퀀스를 시작해도 어차피 main_phase 끝까지는 동작한다" 는 주장을 평가하시오.
**정답.** 잘못됨. UVM phase 는 모든 컴포넌트가 objection 을 raise 하지 않으면 즉시 종료. 시퀀스가 시작되기도 전에 phase 가 끝나 verb 발행 자체가 안 됨.
**Why.** UVM의 objection 메커니즘은 "아직 할 일이 있다"는 신호를 phase manager에게 전달하는 장치다. 어떤 컴포넌트도 objection을 raise하지 않으면, phase manager는 "모두 완료"로 판단하고 main_phase를 종료한다. 이 경우 시퀀스가 start()를 호출하기도 전에 phase가 끝나버린다. "main_phase 끝까지는 동작한다"는 주장은 default objection이 존재한다고 가정한 오해에서 비롯된 것이다.

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
**Why.** `fork-join`을 사용하지 않으면 노드 0의 SEND가 완료된 후에야 노드 1의 SEND가 시작되므로 동시성을 보장할 수 없다. `.sequencer(rdma_seqr[0])`과 `.sequencer(rdma_seqr[1])`을 각 branch에 명시해야 각 SEND가 올바른 노드의 driver로 라우팅된다. 이 패턴은 RDMA의 two-sided verb(SEND/RECV 쌍)처럼 두 노드가 동시에 동작해야 하는 시나리오에서 필수다.

### Q7. (Analyze) `check_phase` 에서 `c2h_tracker` 가 fatal 을 안 내고 warning 만 내는 시나리오는 언제인가?
**정답.** ErrQP 가 deregister 되었거나 `vrdma_c2h_tracker::err_enabled = 1` 인 경우. `qp_obj.isErrQP() || err_enabled` 면 outstanding 잔존도 fatal 대신 warning(Module 06 §5).
**Why.** 정상적인 검증에서는 `check_phase` 에 outstanding이 남아 있으면 fatal이 맞다 — 뭔가 완료되지 않았다는 뜻이기 때문이다. 그러나 에러 테스트에서는 ErrQP를 선언한 이후 남은 DMA가 있을 수 있고, 이를 fatal로 처리하면 의도된 에러 시나리오가 항상 시뮬 실패로 끝난다. 따라서 `isErrQP() || err_enabled` 조건으로 fatal을 warning으로 격하해 에러 테스트가 "에러가 예상대로 발생했다"는 PASS 결론을 낼 수 있도록 설계되어 있다.

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
**Why.** UVM factory의 `set_type_override`는 기존 class를 파생 class로 투명하게 교체하는 메커니즘이다. `vrdma_init_seq`가 `post_configure_phase`에서 자동 시작되는 구조를 유지하면서도, 실제로 생성되는 인스턴스만 `my_init_seq`로 바꿀 수 있다. `build_phase`에서 `super.build_phase()` 이후 override를 등록해야 TB 계층의 기본 세팅 후에 override가 적용된다. 이 패턴은 RDMA-TB가 표준 UVM 1.2 메커니즘을 그대로 활용한다는 증거이기도 하다.
