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
    **C**. `uvm_sequence_item`이 직접 상속 대상. 이는 `uvm_transaction → uvm_object → uvm_void` 계층의 일부. component 분기가 아니므로 Phase 없음.

## Q2. (Understand)

`uvm_do_with`와 `start_item / finish_item`의 가장 큰 차이는?

??? answer "정답 / 해설"
    `uvm_do_with`는 create + randomize + start + finish를 한 매크로로 묶어 실행하므로 randomization 결과를 finish 전에 검사/수정할 수 없습니다. `start_item / finish_item`은 사이에 직접 필드 수정(예: 테스트별 offset 추가)이 가능. 단순 랜덤은 do_with, 데이터 후처리 필요하면 start/finish.

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
    **B**. Virtual Sequence는 `p_sequencer`를 통해 여러 sub-sequencer에 sequence를 시작시켜 시스템 레벨 시나리오(예: APB로 enable 후 AXI로 traffic)를 한 곳에서 조율합니다.

## Q5. (Apply)

`set_id_info`를 빠뜨리면 어떤 환경에서 즉시 깨지는가?

- [ ] A. Single sequence + single agent
- [ ] B. Multiple sequences sharing one sequencer with response handling
- [ ] C. Passive agent only environment
- [ ] D. RAL을 사용하는 환경

??? answer "정답 / 해설"
    **B**. 여러 sequence가 같은 sequencer를 공유할 때 driver가 응답을 보내면 sequencer는 응답의 `sequence_id`를 보고 어느 sequence에 라우팅할지 결정합니다. `set_id_info` 누락 시 sequence_id가 기본값(0)이라 매칭이 깨짐.
