# Quiz — Module 03: Sequence & Sequence Item

[← Module 03 본문으로 돌아가기](../03_sequence_and_item.md)

---

## Q1. (Remember)

Sequence Item이 상속하는 클래스는?

- [ ] A. `uvm_component`
- [ ] B. `uvm_object`
- [ ] C. `uvm_sequence_item`
- [ ] D. `uvm_transaction` 만

??? answer "정답 / 해설"
    **C**. Sequence Item은 `uvm_sequence_item`을 직접 상속합니다. 클래스 계층은 `uvm_sequence_item → uvm_transaction → uvm_object → uvm_void`로 이어지며, `uvm_component` 분기와는 완전히 다른 가지입니다. component가 아니므로 phase callback이 없고, 트랜잭션 데이터를 담는 순수한 데이터 컨테이너로 동작합니다. A(uvm_component 상속)는 phase를 가져 생명주기가 맞지 않고, B(uvm_object 직접 상속)는 sequence_id 같은 트랜잭션 필드가 빠져 Driver와 통신 불가, D(uvm_transaction 단독)는 실제로도 가능하지만 sequence 메커니즘을 쓰려면 uvm_sequence_item이 필요합니다.

## Q2. (Understand)

`uvm_do_with`와 `start_item / finish_item`의 가장 큰 차이는?

??? answer "정답 / 해설"
    `uvm_do_with`는 내부적으로 create → randomize(with constraint) → start_item → finish_item을 한 번에 실행하므로 randomize 후 필드를 수정할 시점이 없습니다. 반면 `start_item / finish_item`을 직접 사용하면 두 호출 사이에서 randomize 결과를 검사하거나, 테스트별 offset을 덧붙이거나, 다른 트랜잭션의 값을 참조해 필드를 계산하는 등 세밀한 제어가 가능합니다. 따라서 단순한 constrained-random 시나리오에는 `uvm_do_with`가 간결하고, 생성 후 가공이 필요한 시나리오에는 `start_item / finish_item`을 사용합니다.

## Q3. (Apply)

주소가 `[32'h2000:32'h2FFF]` 범위인 write 50건을 만드는 sequence body를 한 줄로 작성하세요.

??? answer "정답 / 해설"
    ```systemverilog
    repeat (50) `uvm_do_with(req, { req.kind == WRITE; req.addr inside {[32'h2000:32'h2FFF]}; })
    ```

## Q4. (Analyze)

Virtual Sequence가 multi-agent 시나리오에 사용되는 가장 큰 이유는?

- [ ] A. body() 안에서 시간을 소비할 수 있어서
- [ ] B. 한 sequence가 여러 sequencer에 동시 송출 가능해 시간/순서 조율을 한 곳에서 관리할 수 있어서
- [ ] C. Sequencer 없이도 driver에 직접 보낼 수 있어서
- [ ] D. uvm_object를 상속하지 않아 가벼워서

??? answer "정답 / 해설"
    **B**. Virtual Sequence의 핵심 가치는 여러 Agent의 Sequencer에 동시에, 그리고 순서 있게 트랜잭션을 보낼 수 있다는 점입니다. `p_sequencer`를 통해 `apb_sqr`, `axi_sqr` 같은 sub-sequencer에 접근하고, `fork...join` 또는 순차 실행으로 타이밍을 한 곳에서 통제합니다. A(body 안에서 시간 소비)는 일반 sequence도 가능하므로 Virtual Sequence만의 이유가 아니고, C(Sequencer 없이 Driver 직접 접근)는 UVM의 구조에 위배되며, D(uvm_object 상속)는 사실과 다릅니다.

## Q5. (Apply)

`set_id_info`를 빠뜨리면 어떤 환경에서 즉시 깨지는가?

- [ ] A. Single sequence + single agent
- [ ] B. Multiple sequences sharing one sequencer with response handling
- [ ] C. Passive agent only environment
- [ ] D. RAL을 사용하는 환경

??? answer "정답 / 해설"
    **B**. `set_id_info`는 응답 item에 원래 요청 item의 `sequence_id`와 `transaction_id`를 복사하는 역할을 합니다. 하나의 Sequencer를 여러 Sequence가 공유할 때 Driver가 응답을 `put_response`로 돌려보내면, Sequencer는 응답의 `sequence_id`를 기준으로 어느 Sequence의 `get_response` 호출에 전달할지 결정합니다. `set_id_info`를 빠뜨리면 모든 응답의 `sequence_id`가 초기값(0)으로 남아, 첫 번째 Sequence만 응답을 받거나 잘못된 Sequence에 응답이 전달되는 오동작이 발생합니다. A(단일 sequence)나 C(Passive agent)는 응답 라우팅 문제가 없으므로 증상이 나타나지 않습니다.
