---
title: "Quiz — Module 02: Agent / Driver / Monitor"
---

[← Module 02 본문으로 돌아가기](../../02_agent_driver_monitor/)

---

## Q1. (Remember)

Active Agent와 Passive Agent의 가장 큰 구조적 차이는?

- [ ] A. Active만 Phase를 가진다
- [ ] B. Active만 Driver와 Sequencer를 인스턴스화한다
- [ ] C. Passive만 Monitor를 가진다
- [ ] D. Active만 Virtual Interface를 사용한다

<details>
<summary>정답 / 해설</summary>

**B**. Passive Agent는 이미 다른 마스터가 DUT를 구동하는 환경에서 트래픽을 관찰만 합니다. 따라서 자극을 인가하는 Driver와 항목을 중개하는 Sequencer가 필요 없고, Monitor만 존재합니다. A(phase 차이)는 사실이 아니며 두 모드 모두 동일한 phase에 참여합니다. C(Monitor의 독점)도 틀렸는데, Monitor는 Active Agent에도 반드시 존재합니다. D(virtual interface 독점)도 아닌데, Passive 모드에서도 신호 관찰을 위해 virtual interface를 사용합니다.

</details>
## Q2. (Understand)

Driver의 `forever` 루프에서 `get_next_item / item_done` 짝이 lockstep이라는 의미를 설명하세요.

<details>
<summary>정답 / 해설</summary>

`get_next_item`과 `item_done`은 하나의 트랜잭션을 처리하는 계약입니다. `get_next_item`을 호출하면 Sequencer는 다음 item을 Driver에게 "빌려주고" 대기 상태로 전환됩니다. Driver가 DUT에 신호를 인가한 뒤 `item_done`을 호출해야 비로소 Sequencer가 "반납받았다"고 인식하고 다음 item을 꺼낼 준비를 합니다. 만약 `item_done`을 누락하면 첫 트랜잭션 이후 Sequencer가 영원히 대기하므로, 두 번째 트랜잭션부터 시뮬레이션이 hang에 빠지게 됩니다.

</details>
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

<details>
<summary>정답 / 해설</summary>

빠진 한 줄은 `sqr = apb_sequencer::type_id::create("sqr", this);`입니다. Active Agent에서 Driver는 `seq_item_port`를 통해 Sequencer로부터 트랜잭션을 받습니다. Sequencer 인스턴스가 없으면 connect_phase에서 `drv.seq_item_port.connect(sqr.seq_item_export)`가 null handle에 접근해 런타임 오류가 발생하고, 트랜잭션 공급 경로가 아예 존재하지 않게 됩니다.

</details>
## Q4. (Analyze)

Monitor가 절대 해서는 안 되는 동작은?

- [ ] A. `analysis_port::write()` 호출
- [ ] B. clocking block으로 신호 sampling
- [ ] C. DUT의 입력 신호를 driving
- [ ] D. trans_collected 객체 생성

<details>
<summary>정답 / 해설</summary>

**C**. Monitor의 역할은 DUT 신호를 수동적으로 샘플링해 트랜잭션으로 변환하는 것입니다. DUT 입력을 driving하면 두 가지 문제가 생깁니다. 첫째, Active Agent의 Driver와 동시에 같은 신호를 구동하면 multiple-driver 충돌이 발생합니다. 둘째, Passive 모드에서도 Monitor가 존재하는데 이 경우 자극 인가 주체가 없어야 하는 시나리오에서 의도치 않은 DUT 동작을 유발합니다. A(analysis_port 사용), B(clocking block 샘플링), D(트랜잭션 객체 생성)는 모두 Monitor의 정상적인 동작입니다.

</details>
## Q5. (Evaluate)

다음 중 Pipelining Driver가 **부적절한** 상황은?

- [ ] A. AXI write 채널 outstanding throughput 검증
- [ ] B. PCIe TLP credit-based 흐름 검증
- [ ] C. APB read/write 시퀀스 검증
- [ ] D. AHB burst 트래픽 검증

<details>
<summary>정답 / 해설</summary>

**C**. Pipelining Driver는 이전 트랜잭션의 응답을 기다리지 않고 다음 요청을 즉시 발행하는 모델로, AXI의 outstanding transaction이나 PCIe의 credit-based flow처럼 파이프라인을 허용하는 프로토콜에 적합합니다. 반면 APB는 SETUP → ACCESS → 완료의 단계가 끝난 뒤에야 다음 트랜잭션이 시작되는 단순 프로토콜로 outstanding 개념이 없습니다. Pipelining Driver를 APB에 적용하면 이전 사이클이 끝나기 전에 다음 psel·penable을 구동해 APB 프로토콜 위반이 발생합니다.

</details>
