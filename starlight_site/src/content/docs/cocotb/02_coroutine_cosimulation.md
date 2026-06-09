---
title: "Module 02 — Coroutine & Cosimulation 아키텍처"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** coroutine(`async def`)이 무엇이며 `await`가 어떻게 Python 실행을 중단·재개하는지 설명할 수 있다.
- **Trace** `@cocotb.test()` → `await RisingEdge(dut.clk)` → 시뮬레이터 재개로 이어지는 cosimulation 제어 흐름을 단계별로 추적할 수 있다.
- **Explain** "어느 순간에도 active coroutine은 하나뿐"이라는 원칙이 왜 SV와 같은 race 동작을 만드는지 설명할 수 있다.
- **Apply** UVM의 test/env/driver/monitor/scoreboard 구조를 cocotb의 Python 등가물로 매핑할 수 있다.
- **Differentiate** UVM의 sequence push(TLM handshake) 모델과 cocotb의 direct-call 모델을 구분할 수 있다.
:::
:::note[사전 지식]
- [Module 01 — cocotb란 무엇인가](../01_what_is_cocotb/)
- Python `async`/`await` 문법에 대한 최소한의 노출
- UVM driver-sequencer handshake(`get_next_item`/`item_done`)의 개념
:::
---

## 1. Why care? — 'Python인데 어떻게 시뮬레이터와 박자를 맞추나'

### 1.1 시나리오 — 두 세계의 시간 맞추기

cocotb 테스트는 Python 프로세스에서 돌고, DUT는 HDL 시뮬레이터 안에서 clock에 맞춰 돕니다. 그런데 Python 코드의 `for i in range(100)` 루프와 시뮬레이터의 `posedge clk`는 서로 다른 세계의 시간입니다. Python이 멋대로 빨리 돌아 버리면 DUT는 아직 reset 중인데 Python은 벌써 데이터를 읽으려 합니다. 두 세계가 박자를 맞추지 못하면 검증은 의미가 없습니다.

핵심 질문은 이것입니다. "시뮬레이터 밖의 Python이 어떻게 안의 clock에 정확히 동기화되는가?" 답은 coroutine입니다. Python은 `await RisingEdge(dut.clk)`에서 *스스로 멈추고* 시뮬레이터에게 "이 이벤트가 오면 나를 깨워 줘"라고 콜백을 등록한 뒤 제어를 넘깁니다. 시뮬레이터가 그 edge에 도달하면 Python을 그 지점부터 재개시킵니다. 이 중단·재개 메커니즘이 cocotb 동작의 심장입니다.

### 1.2 왜 지금 이 주제가 중요한가

이 메커니즘을 모르면 두 부류의 버그를 만납니다. 하나는 `await`를 빠뜨려 시뮬레이터 시간을 진행시키지 않은 채 무한 루프를 도는 hang이고, 다른 하나는 "Python이니 멀티스레드처럼 병렬"이라고 착각해 존재하지 않는 race를 가정하거나 진짜 race를 놓치는 것입니다. 1장에서 "밖에서 VPI로 조종한다"고 했던 추상을, 이 모듈에서 코드 수준의 제어 흐름으로 내립니다.

---

## 2. Intuition — 한 줄 비유 + 한 장 그림

:::tip[💡 한 줄 비유]
**coroutine + await** ≈ **번호표 뽑고 의자에 앉아 호출을 기다리는 손님**.<br>
손님(coroutine)은 창구에서 "다음 clock에 불러 주세요"(`await RisingEdge`)라고 말하고 자리에 앉습니다(Python 중단). 직원(시뮬레이터)이 그 시점이 되면 번호를 부르고(콜백), 손님은 *멈췄던 그 줄부터* 다시 일을 진행합니다. 한 번에 창구에서 일을 보는 손님은 단 한 명입니다.
:::

### 한 장 그림 — await 한 번의 제어 왕복

```d2
direction: down

PY: "**Python (cocotb)**\nasync def test(dut)" {
  s1: "① dut.din.value = x\n  (신호 write)"
  s2: "② await RisingEdge(dut.clk)\n  → 콜백 등록 후 Python 중단"
  s5: "⑤ 재개: dut.dout.value 읽기\n  + assert"
  s1 -> s2 -> s5
}

SIM: "**HDL Simulator**" {
  s3: "③ 시뮬레이션 시간 진행\n  posedge clk 발생"
  s4: "④ 등록된 콜백 실행\n  → Python coroutine resume"
  s3 -> s4
}

s2 -> s3: "VPI: 콜백 등록 + 제어 양보"
s4 -> s5: "VPI: resume"
```

손님 비유의 핵심은 "한 번에 한 명"입니다. cocotb에서도 어느 순간에든 active한 coroutine은 단 하나입니다. 그래서 Python 코드가 여러 coroutine으로 나뉘어 있어도, 진짜 동시에 두 줄이 실행되는 일은 없고, race 동작은 SystemVerilog와 동일하게 결정적입니다(`cocotb_note.md` "Only one coroutine active at any moment → race conditions behave the same as in SV").

---

## 3. 작은 예 — driver coroutine 한 개가 도는 과정

UVM의 driver는 `get_next_item` → 신호 구동 → `item_done`을 반복합니다. cocotb의 driver는 그냥 `async def` coroutine으로, 같은 일을 `await`로 시간을 진행하며 합니다.

### 단계별 다이어그램

```d2
direction: down

D: "**driver coroutine**\nasync def drive(dut, item)"
S1: "① dut.valid.value = 1\n   dut.data.value = item.data\n   (신호 구동)"
S2: "② await RisingEdge(dut.clk)\n   (한 clock 진행 — Python 중단)"
S3: "③ while dut.ready.value == 0:\n      await RisingEdge(dut.clk)\n   (handshake 대기)"
S4: "④ dut.valid.value = 0\n   (구동 해제 → 전송 완료)"
D -> S1 -> S2 -> S3 -> S4
```

### 단계별 의미

| Step | 무엇을 | 왜 | UVM 대응 |
|---|---|---|---|
| ① | DUT 신호에 직접 값 write | 자극 인가 | `vif.valid <= 1` |
| ② | `await RisingEdge(dut.clk)` | 한 clock 진행, 시뮬레이터에 제어 양보 | `@(posedge vif.clk)` |
| ③ | ready==0이면 다시 await | valid/ready handshake 완료 대기 | `wait(vif.ready)` |
| ④ | valid를 0으로 | 전송 종료 | `vif.valid <= 0` |

### 실제 코드 (driver + monitor + scoreboard 골격)

```python
import cocotb
from cocotb.triggers import RisingEdge
from cocotb.queue import Queue          # UVM TLM analysis port에 대응

# --- driver: UVM uvm_driver에 대응하는 coroutine ---
async def drive(dut, item):
    dut.valid.value = 1
    dut.data.value  = item["data"]
    await RisingEdge(dut.clk)           # ②
    while dut.ready.value == 0:         # ③ handshake 대기
        await RisingEdge(dut.clk)
    dut.valid.value = 0                 # ④

# --- monitor: uvm_monitor에 대응, Queue로 broadcast ---
async def monitor(dut, ap: Queue):
    while True:
        await RisingEdge(dut.clk)
        if dut.out_valid.value == 1:
            await ap.put(int(dut.out_data.value))   # analysis port write에 대응

# --- scoreboard: Python class + Queue ---
class Scoreboard:
    def __init__(self):
        self.expected = []
    def add_expected(self, v):
        self.expected.append(v)
    async def run(self, ap: Queue):
        while True:
            actual = await ap.get()
            exp = self.expected.pop(0)
            assert actual == exp, f"Mismatch exp={exp} act={actual}"

@cocotb.test()                          # uvm_test + run_test()
async def basic_test(dut):
    ap = Queue()
    sb = Scoreboard()
    cocotb.start_soon(monitor(dut, ap)) # 백그라운드 coroutine으로 monitor 기동 (fork)
    cocotb.start_soon(sb.run(ap))
    for d in [0x10, 0x20, 0x30]:
        sb.add_expected(d)              # 기대값 등록 (ref 계산은 여기선 identity)
        await drive(dut, {"data": d})   # ★ sequence가 driver를 '직접 호출' — TLM handshake 없음
```

:::note[여기서 잡아야 할 두 가지]
**(1) sequence가 driver를 *직접 호출*합니다.** `await drive(dut, item)` 한 줄이면 끝입니다. UVM의 `get_next_item`/`item_done` **TLM**(Transaction-Level Modeling — 컴포넌트끼리 비트 신호가 아니라 트랜잭션 객체를 주고받게 하는 UVM의 표준 통신 방식) handshake boilerplate가 통째로 사라집니다(`cocotb_note.md` "CocoTB uses a direct call model").<br>
**(2) `cocotb.start_soon`은 UVM의 fork에 해당하는 백그라운드 coroutine 기동입니다.** monitor와 scoreboard는 이렇게 띄워 두고, 메인 테스트가 자극을 인가하면 그들이 `await`로 깨어나며 처리합니다 — 그래도 동시에 도는 줄은 하나뿐입니다. 다만 `fork`와 *완전히* 같지는 않습니다. `start_soon`은 *같은 협력 스케줄러* 위에 새 coroutine을 예약할 뿐 진짜 병렬을 만들지 않고, 무엇보다 **호출자가 그 coroutine의 완료를 기다리지 않습니다**(fire-and-forget). 즉 `fork...join`의 join 대기가 없는 셈입니다. 완료를 기다리려면 `await`로 해당 coroutine을 직접 기다려야 하고, 반대로 `start_soon`은 "띄워 놓고 메인은 계속 진행"하는 수명/대기 모델입니다 — monitor·scoreboard처럼 테스트 내내 백그라운드로 도는 것에 맞습니다.
:::
---

## 4. 일반화 — UVM ↔ cocotb 구조 매핑

cocotb를 빨리 익히는 가장 좋은 방법은 "UVM의 이것은 cocotb의 무엇인가"로 대응시키는 것입니다. `cocotb_note.md`의 Structural Mapping 표를 그대로 가져옵니다.

| UVM | cocotb |
|---|---|
| `uvm_test` | `@cocotb.test()` 데코레이트된 함수 |
| `uvm_env` | 평범한 Python class |
| `uvm_driver` | `async def` coroutine |
| `uvm_monitor` | `async def` coroutine |
| `uvm_scoreboard` | Python class + Queue |
| `uvm_config_db` | Python 객체 속성, dict |
| TLM analysis port | `cocotb.queue.Queue` |
| objection 메커니즘 | 자연스러운 coroutine 종료 |
| `uvm_reg` (RAL) | 외부 라이브러리 필요 (cocotb-bus, peakrdl-python) |
| Functional coverage | `cocotb-coverage` 라이브러리 |

표를 보면 cocotb 쪽이 한결같이 "평범한 Python 것"임을 알 수 있습니다. env가 별도 기반 클래스가 아니라 그냥 class이고, config_db가 전용 데이터베이스가 아니라 그냥 dict나 객체 속성입니다. UVM이 *프레임워크가 제공하는 인프라*로 푸는 것을, cocotb는 *언어가 이미 가진 기능*으로 풉니다. 그 대가로 RAL과 coverage처럼 UVM이 표준으로 제공하던 것은 외부 라이브러리에 의존해야 합니다.

### 4.1 가장 중요한 구조적 차이 — push vs direct call

```d2
direction: right

UVM: "UVM — sequence push 모델" {
  SEQ1: "sequence"
  SQR: "sequencer"
  DRV1: "driver"
  SEQ1 -> SQR: "start_item / finish_item"
  SQR -> DRV1: "get_next_item (TLM handshake)"
  DRV1 -> SQR: "item_done"
}

COCO: "cocotb — direct call 모델" {
  SEQ2: "test / sequence\n(coroutine)"
  DRV2: "driver\n(coroutine)"
  SEQ2 -> DRV2: "await drive(dut, item)\n(직접 호출)"
}
```

UVM은 sequence가 sequencer를 거쳐 driver에게 item을 *밀어 넣는*(push) 모델이라, `get_next_item`/`item_done`이라는 TLM handshake 계약이 반드시 필요합니다. cocotb는 sequence(테스트)가 driver 함수를 *직접 부르는* 모델이라 그 중간 계층과 boilerplate가 전부 사라집니다(`cocotb_note.md` 4.2 직후 "Key architectural difference"). 단순함을 얻는 대신, sequencer가 제공하던 arbitration(여러 sequence가 같은 driver를 동시에 쓰려 할 때 누구 차례인지 정해 주는 중재)·grab/lock(한 sequence가 driver를 잠시 독점하도록 잡아 두는 기능) 같은 기능은 직접 구현해야 합니다.

---

## 5. 디테일 — coroutine 동작 규칙과 시뮬레이터 독립성

### 5.1 await가 만드는 협력적 스케줄링

cocotb는 OS 스레드를 쓰지 않습니다. coroutine들은 *협력적*으로 양보합니다. `await`를 만나야만 다른 coroutine이 돌 기회가 생기고, `await`를 만나기 전까지는 한 coroutine이 제어를 쥐고 끝까지 실행합니다(`cocotb_note.md` "registers a callback ... suspends Python; simulator resumes it on event"). 그래서 다음 규칙이 따라 나옵니다.

- `await RisingEdge(dut.clk)`는 *시뮬레이션 시간을 진행*시키는 유일한 통로다. `await` 없는 무한 루프는 시간을 진행시키지 못하고 hang한다.
- 어느 순간에도 active coroutine은 하나뿐 → 두 coroutine이 같은 신호를 같은 delta(시뮬레이션 시간은 그대로인 채 신호 값만 갱신되는 0-시간 미세 단계 — 같은 시각 안의 "찰나")에 건드려도 동작은 결정적이며 SV race와 동일하다.
- `cocotb.start_soon(coro)`로 띄운 백그라운드 coroutine도 같은 협력 스케줄러 위에서 돈다 — 진짜 병렬이 아니다.

:::note[콜백이 *어느 시점*에 실행되는가 — race 결정성의 근거]
"콜백 등록 후 중단 → 시뮬레이터가 resume"의 *어느 순간에* resume되는지가 race 결정성을 떠받칩니다. cocotb의 edge trigger(`RisingEdge` 등)는 해당 clock edge가 발생한 뒤, 시뮬레이터가 그 delta의 신호 업데이트를 끝낸 *읽기 안정 시점*에 coroutine을 깨웁니다. 그래서 깨어난 Python이 `dut.q.value`를 읽으면 *이번 edge에서 갱신된 값*을 일관되게 봅니다 — driving은 값 쓰기 단계로, sampling은 값이 안정된 단계로 분리되어 두 coroutine이 같은 신호를 같은 edge에 건드려도 결과가 결정적입니다. 이는 SystemVerilog 스케줄러의 Active/NBA/Observed region 분리가 driver-monitor race를 막는 것과 정확히 대응합니다 — SV 스케줄러 region의 전체 메커니즘(왜 driving은 NBA, sampling은 안정 시점인가)은 [UVM Module 02](../../uvm/02_agent_driver_monitor/)에서 다룹니다.
:::

### 5.2 주요 trigger와 UVM 대응

| cocotb trigger | 의미 | UVM 대응 |
|---|---|---|
| `RisingEdge(dut.clk)` | clock rising edge까지 대기 | `@(posedge vif.clk)` |
| `FallingEdge(dut.clk)` | falling edge까지 대기 | `@(negedge vif.clk)` |
| `Timer(10, "ns")` | 절대 시간 대기 | `#10ns` |
| `ClockCycles(dut.clk, 5)` | N clock 대기 | `repeat(5) @(posedge clk)` |
| `await coro` / `start_soon` | coroutine 종료 대기 / fork | `fork...join` |

### 5.3 시뮬레이터 독립성 — 한 번 쓰면 어디서나

cocotb는 VPI라는 *표준* 인터페이스로만 시뮬레이터와 대화하므로, VPI를 지원하는 시뮬레이터(VCS, Questa, Icarus, Verilator 등)면 같은 Python 코드가 변경 없이 돕니다(`cocotb_note.md` "Simulator independence: the same Python code runs unchanged across all simulators"). 검증 코드를 한 번 작성해 무료 시뮬레이터로 CI를 돌리고, 필요할 때 상용 시뮬레이터로 더 빠르게 회귀하는 식의 조합이 가능해지는 근거가 이것입니다.

:::note[`int(dut.sig.value)` — 왜 캐스팅이 필요한가]
§3 코드에서 `int(dut.out_data.value)`처럼 `.value`를 `int()`로 감싸는 데에는 이유가 있습니다. `.value`가 돌려주는 것은 평범한 Python 정수가 아니라 **각 비트의 0/1/X/Z를 담는 전용 타입**(BinaryValue/LogicArray 계열)입니다. RTL 신호는 4-state라서 미지(X)·고임피던스(Z)를 표현해야 하므로 정수로 바로 환원될 수 없습니다. 그래서 산술 비교(`== exp`, `< N`)나 인덱싱 전에 `int()`로 정수 변환을 해줘야 의도대로 동작합니다. 주의: 비트에 X/Z가 섞여 있으면 정수로 해석할 수 없어 `int()`가 예외를 던질 수 있습니다 — reset 직후나 미구동 신호를 읽을 때 자주 만나는 함정이며, 비교 전에 X 여부를 확인하는 것이 안전합니다.
:::

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'Python이니 coroutine들이 진짜 병렬로 돈다']
**실제**: 어느 순간에도 active coroutine은 하나뿐입니다. cocotb는 협력적 스케줄링이며 OS 스레드 병렬이 아닙니다. 그래서 race 동작이 SystemVerilog와 동일하게 결정적입니다.<br>
**왜 헷갈리는가**: "async = 비동기 = 병렬"이라는 일반적 오해 때문. 여기서 async는 *중단·재개 가능*이라는 뜻이지 *동시 실행*이 아닙니다.
:::
:::danger[❓ 오해 2 — 'await 없이도 루프를 돌면 시뮬레이션이 진행된다']
**실제**: `await`(특히 시간/이벤트 trigger)가 없는 루프는 시뮬레이션 시간을 진행시키지 못한 채 Python만 무한히 돌아 hang합니다. 시간을 진행시키는 것은 `await RisingEdge`/`Timer` 같은 trigger뿐입니다.<br>
**왜 헷갈리는가**: 일반 Python 루프 감각으로는 "루프가 돌면 뭔가 진행된다"고 느끼지만, 여기서 시간의 주인은 시뮬레이터입니다.
:::
:::danger[❓ 오해 3 — 'cocotb는 UVM처럼 sequencer/handshake가 필요하다']
**실제**: cocotb는 direct-call 모델이라 sequence가 driver를 직접 호출합니다(`await drive(...)`). `get_next_item`/`item_done` 같은 TLM handshake가 없습니다. 그 대신 arbitration이 필요하면 직접 구현해야 합니다.<br>
**왜 헷갈리는가**: UVM 멘탈 모델을 그대로 옮기려 하기 때문.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 테스트가 hang, 시뮬 시간 0에서 멈춤 | 루프 안에 `await` trigger 누락 | coroutine 안의 `while`/`for`에 `await RisingEdge` 등이 있는지 |
| monitor가 트랜잭션을 못 잡음 | `start_soon`으로 기동 안 했거나 sampling edge가 어긋남 | `cocotb.start_soon(monitor(...))` 호출 여부, 어느 edge에서 read하는지 |
| scoreboard mismatch인데 값은 맞아 보임 | Queue 순서 vs DUT 순서 불일치 (OoO) | Queue 1개로 OoO를 받고 있지 않은지 (UVM과 같은 함정) |
| 같은 코드가 시뮬레이터 바꾸니 안 됨 | 시뮬레이터별 VPI 빌드/연동 설정 | Makefile/runner의 SIM 변수, VPI 라이브러리 빌드 |
| signal 값이 항상 0/X | `.value` 대입을 안 했거나 read 시 `int()` 캐스팅 누락 | `dut.sig.value = x` 형식, `int(dut.sig.value)` |

---

## 7. 핵심 정리 (Key Takeaways)

- **coroutine + await가 동기화의 핵심**: `await RisingEdge(dut.clk)`에서 Python이 콜백을 등록하고 중단 → 시뮬레이터가 그 이벤트에 재개. 이것이 시뮬레이터 밖 Python을 안의 clock에 맞추는 메커니즘.
- **한 번에 한 coroutine**: 협력적 스케줄링이라 진짜 병렬이 아니며, race 동작이 SystemVerilog와 동일하게 결정적.
- **구조 매핑**: uvm_test→`@cocotb.test()`, driver/monitor→coroutine, scoreboard→class+Queue, config_db→dict, analysis port→Queue. UVM이 인프라로 푸는 것을 cocotb는 언어 기능으로 푼다.
- **direct call vs push**: cocotb는 sequence가 driver를 직접 호출 → `get_next_item`/`item_done` boilerplate 소멸. 대신 arbitration 등은 직접 구현.
- **시뮬레이터 독립성**: VPI 표준만 쓰므로 같은 Python 코드가 모든 시뮬레이터에서 변경 없이 동작.

:::caution[실무 주의점]
- `await` 없는 루프 = hang. 시간 진행의 주인은 시뮬레이터이고, trigger만이 시간을 민다.
- `start_soon`으로 monitor/scoreboard를 *먼저* 띄운 뒤 자극을 인가 — 순서가 바뀌면 초기 트랜잭션을 놓친다.
- direct-call의 단순함은 arbitration·grab/lock을 잃는 대가 — 필요하면 직접 만든다.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — await의 역할 (Bloom: Analyze)]
`await RisingEdge(dut.clk)` 한 줄이 정확히 무슨 일을 하는지, "Python 입장"과 "시뮬레이터 입장"으로 나눠 설명하라.
<details>
<summary>정답</summary>

- **Python 입장**: 이 줄에서 실행을 멈추고, 자신을 깨워 달라는 콜백을 시뮬레이터에 등록한 뒤 제어를 양보한다. 다음 rising edge가 오면 *바로 다음 줄부터* 재개된다.
- **시뮬레이터 입장**: 제어를 돌려받아 시뮬레이션 시간을 진행시키다가, posedge clk에 도달하면 등록된 콜백을 실행해 Python coroutine을 resume한다.
- 결과적으로 두 세계의 시간이 이 한 줄로 동기화된다. `await`가 없으면 시간이 진행되지 않아 hang한다.

</details>
:::
:::tip[🤔 Q2 — push vs direct call 트레이드오프 (Bloom: Evaluate)]
cocotb의 direct-call 모델은 UVM의 sequencer push 모델보다 단순하다. 이 단순함의 대가는 무엇인가?
<details>
<summary>정답</summary>

대가는 sequencer가 제공하던 인프라를 잃는 것이다. UVM은 sequencer를 통해 여러 sequence 간 arbitration, grab/lock 독점, item-level 흐름 제어를 표준으로 제공한다. cocotb에서 sequence가 driver를 직접 호출하면 `get_next_item`/`item_done` boilerplate는 사라지지만, 여러 자극원이 한 인터페이스를 두고 경쟁할 때의 arbitration은 직접 구현해야 한다. IP/블록 레벨처럼 자극원이 단순하면 이 대가가 거의 없지만, 복잡한 다중 sequence 조율에서는 비용이 된다.

</details>
:::
### 7.2 출처

**External**
- cocotb 공식 문서 Triggers/Coroutines — https://docs.cocotb.org/
- IEEE 1800-2017 §VPI — 콜백 등록/이벤트 메커니즘
- *UVM 1.2 User's Guide* §driver-sequencer handshake — Accellera (비교 기준)

---

## 다음 모듈

→ [Module 03 — 언제 쓰나 + DV 트레이드오프](../03_when_to_use_tradeoffs/): 동작 원리를 알았으니, 이제 *언제 cocotb를 택하고 언제 UVM을 택할지*를 적합/부적합 사례와 도구 지형으로 판단한다.

[퀴즈 풀어보기 →](../quiz/02_coroutine_cosimulation_quiz/)
