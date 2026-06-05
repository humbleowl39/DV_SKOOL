---
title: "Quiz — Module 02: Coroutine & Cosimulation 아키텍처"
---

[← Module 02 본문으로 돌아가기](../../02_coroutine_cosimulation/)

---

## Q1. (Remember)

cocotb에서 시뮬레이션 시간을 진행시키는 동시에 Python coroutine을 중단시키는 표현은?

- [ ] A. `time.sleep(10)`
- [ ] B. `await RisingEdge(dut.clk)`
- [ ] C. `dut.clk.value = 1`
- [ ] D. `print(dut.clk)`

<details>
<summary>정답 / 해설</summary>

**B**. `await RisingEdge(dut.clk)`는 콜백을 시뮬레이터에 등록하고 Python을 중단시킨 뒤 제어를 양보하여, 시뮬레이터가 다음 rising edge에 도달하면 그 지점부터 재개시킵니다. A(`time.sleep`)는 OS 시간을 멈출 뿐 시뮬레이션 시간과 무관하고, C는 신호 write일 뿐 시간을 진행시키지 않으며, D는 단순 출력입니다.

</details>
## Q2. (Understand)

UVM의 `uvm_scoreboard`와 TLM analysis port는 cocotb에서 각각 무엇에 대응하는가?

<details>
<summary>정답 / 해설</summary>

`uvm_scoreboard`는 cocotb에서 평범한 Python class + Queue 조합에 대응하고, TLM analysis port는 `cocotb.queue.Queue`에 대응합니다. monitor coroutine이 관찰한 트랜잭션을 `await ap.put(...)`로 Queue에 넣으면, scoreboard가 `await ap.get()`으로 꺼내 기대값과 비교합니다. UVM이 전용 인프라(analysis port, uvm_scoreboard 기반 클래스)로 제공하는 것을 cocotb는 언어가 이미 가진 class와 Queue로 푼다는 점이 핵심입니다.

</details>
## Q3. (Apply)

cocotb에서 monitor coroutine을 백그라운드로 띄워 두고 메인 테스트가 자극을 인가하려 한다. monitor를 기동하는 올바른 호출은?

- [ ] A. `monitor(dut, ap)` (그냥 호출)
- [ ] B. `await monitor(dut, ap)`
- [ ] C. `cocotb.start_soon(monitor(dut, ap))`
- [ ] D. `import monitor`

<details>
<summary>정답 / 해설</summary>

**C**. `cocotb.start_soon(monitor(dut, ap))`은 UVM의 fork에 대응하여 monitor coroutine을 백그라운드로 기동합니다. A처럼 그냥 호출하면 coroutine 객체만 만들어지고 스케줄되지 않으며, B처럼 `await`하면 monitor가 *끝날 때까지* 메인이 멈춰 자극을 인가하지 못합니다(monitor는 보통 `while True`라 끝나지 않음). D는 무관합니다. monitor/scoreboard는 자극 인가 *전에* start_soon으로 띄워야 초기 트랜잭션을 놓치지 않습니다.

</details>
## Q4. (Analyze)

cocotb 테스트가 시뮬레이션 시간 0에서 멈춘 채 hang했다. coroutine 안에 다음 코드가 있다. 무엇이 문제인가?
```python
while dut.ready.value == 0:
    pass
```

<details>
<summary>정답 / 해설</summary>

`while` 루프 안에 시간을 진행시키는 `await` trigger가 없는 것이 문제입니다. cocotb는 협력적 스케줄링이라 `await`를 만나야만 제어를 시뮬레이터에 넘겨 시간이 진행됩니다. `pass`만 도는 이 루프는 Python만 무한히 돌 뿐 시뮬레이션 시간을 한 틱도 진행시키지 못해 `dut.ready`가 영원히 갱신되지 않고 hang합니다. 올바른 코드는 `while dut.ready.value == 0: await RisingEdge(dut.clk)`처럼 루프 안에서 clock을 진행시켜야 합니다.

</details>
## Q5. (Analyze)

"cocotb는 Python async를 쓰니 여러 coroutine이 진짜 병렬로 실행되어 SystemVerilog보다 race가 더 많이 생긴다." 이 진술의 오류를 지적하라.

<details>
<summary>정답 / 해설</summary>

오류는 "진짜 병렬"이라는 전제입니다. cocotb의 coroutine은 OS 스레드 병렬이 아니라 *협력적 스케줄링*이며, 어느 순간에도 active한 coroutine은 단 하나뿐입니다. 한 coroutine은 `await`를 만나야만 양보하고, 그 전까지는 제어를 독점합니다. 그래서 race 동작이 더 많아지는 것이 아니라, 오히려 SystemVerilog와 *동일하게* 결정적입니다. 여기서 async는 "동시 실행"이 아니라 "중단·재개 가능"을 뜻합니다.

</details>
## Q6. (Evaluate)

cocotb의 direct-call 모델(`await drive(dut, item)`)은 UVM의 sequencer push 모델보다 단순하다. 이 단순함이 항상 이득인가?

<details>
<summary>정답 / 해설</summary>

항상은 아닙니다. direct-call은 `get_next_item`/`item_done` TLM handshake boilerplate를 없애 IP/블록 레벨처럼 자극원이 단순한 경우 큰 이득입니다. 그러나 그 대가로 sequencer가 제공하던 arbitration, grab/lock 독점, 다중 sequence 흐름 제어를 잃습니다. 여러 자극원이 한 인터페이스를 두고 경쟁하는 복잡한 시나리오에서는 이를 직접 구현해야 하므로, 단순함이 오히려 재구현 비용으로 돌아올 수 있습니다. 따라서 과제 복잡도에 따라 이득의 크기가 달라집니다.

</details>
