# Quiz — Module 02: Agent / Driver / Monitor

[← Module 02 본문으로 돌아가기](../02_agent_driver_monitor.md)

---

## Q1. (Remember)

Active Agent와 Passive Agent의 가장 큰 구조적 차이는?

- [ ] A. Active만 Phase를 가진다
- [ ] B. Active만 Driver와 Sequencer를 인스턴스화한다
- [ ] C. Passive만 Monitor를 가진다
- [ ] D. Active만 Virtual Interface를 사용한다

??? answer "정답 / 해설"
    **B**. Passive 모드는 외부에서 인가하는 traffic을 관찰만 하므로 Driver/Sequencer가 불필요. Monitor는 Active/Passive 양쪽 모두 보유.

## Q2. (Understand)

Driver의 `forever` 루프에서 `get_next_item / item_done` 짝이 lockstep이라는 의미를 설명하세요.

??? answer "정답 / 해설"
    Sequencer는 한 시점에 하나의 트랜잭션만 driver에 전달합니다. `get_next_item`으로 빌려온 item은 driver가 처리 완료를 `item_done`으로 알리기 전까지 sequencer가 다음 item을 꺼내지 않습니다. 따라서 두 호출은 짝지어 사용해야 하며, 누락 시 두 번째 트랜잭션부터 sequencer가 대기 상태로 빠집니다.

## Q3. (Apply)

다음 build_phase에서 빠진 한 줄은?

```systemverilog
function void build_phase(uvm_phase phase);
  super.build_phase(phase);
  mon = apb_monitor::type_id::create("mon", this);
  if (get_is_active() == UVM_ACTIVE) begin
    drv = apb_driver::type_id::create("drv", this);
    // ?? 빠진 한 줄
  end
endfunction
```

??? answer "정답 / 해설"
    `sqr = apb_sequencer::type_id::create("sqr", this);`
    Active 모드에서는 Driver와 함께 Sequencer도 만들어야 함. 그렇지 않으면 driver가 sequence로부터 item을 받을 경로가 없음.

## Q4. (Analyze)

Monitor가 절대 해서는 안 되는 동작은?

- [ ] A. `analysis_port::write()` 호출
- [ ] B. clocking block으로 신호 sampling
- [ ] C. DUT의 입력 신호를 driving
- [ ] D. trans_collected 객체 생성

??? answer "정답 / 해설"
    **C**. Monitor는 비침투적 관찰자입니다. DUT 입력을 driving하면 격리 원칙이 무너져 Active Driver와 충돌하거나 의도치 않은 자극이 인가됩니다.

## Q5. (Evaluate)

다음 중 Pipelining Driver가 **부적절한** 상황은?

- [ ] A. AXI write 채널 outstanding throughput 검증
- [ ] B. PCIe TLP credit-based 흐름 검증
- [ ] C. APB read/write 시퀀스 검증
- [ ] D. AHB burst 트래픽 검증

??? answer "정답 / 해설"
    **C**. APB는 outstanding 개념이 없고 매 트랜잭션이 SETUP→ACCESS→IDLE로 완료된 후 다음이 시작됩니다. Pipelining은 outstanding을 가정한 모델이라 APB에 적용 시 protocol 위반.
