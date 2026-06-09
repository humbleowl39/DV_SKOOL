---
title: "Module 01 — cocotb란 무엇인가 + vs UVM"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** "COroutine-based COsimulation TestBench"라는 이름의 각 단어가 무엇을 의미하는지 설명할 수 있다.
- **State** cocotb에서 테스트는 Python으로 쓰고 DUT는 그대로 HDL로 둔다는 핵심 분리를 진술할 수 있다.
- **Differentiate** cocotb와 UVM을 언어·표준·라이선스·학습곡선·생태계 다섯 축으로 구분할 수 있다.
- **Recognize** cocotb를 채택한 실제 업계 사례(OpenTitan, WD, Tenstorrent 등)와 그들이 그것을 택한 이유를 식별할 수 있다.
- **Evaluate** "UVM 하나로 모든 것을 한다"는 관점의 한계를 검증 도구 지형 안에서 평가할 수 있다.
:::
:::note[사전 지식]
- Python 기본 (class, 함수, `import`)
- UVM의 큰 그림 — `uvm_test`, `run_test()` 정도의 개념 ([UVM 코스](../../uvm/) 참고)
- HDL 시뮬레이터를 한 번이라도 돌려본 경험
:::
---

## 1. Why care? — 검증 도구가 UVM 하나뿐이라는 착각

### 1.1 시나리오 — 며칠짜리 검증을 몇 주로 만드는 환경 오버헤드

작은 DSP 필터 블록 하나를 검증한다고 합시다. 입력 샘플을 넣고 출력이 기대 응답과 맞는지 보는 것이 전부인데, 기대 응답을 계산하는 황금 모델은 이미 Python NumPy로 존재합니다. UVM으로 가면 sequence_item, sequence, driver, monitor, scoreboard, agent, env, test를 모두 SystemVerilog로 작성하고, 그 NumPy 레퍼런스 로직을 SystemVerilog로 다시 포팅하거나 DPI로 연결해야 합니다. 블록 자체보다 환경 구축이 더 오래 걸리는 역전이 벌어집니다.

이때 떠올려야 할 질문은 이것입니다. "DUT는 HDL인데, 테스트까지 반드시 HDL이어야 하는가?" cocotb의 출발점이 바로 이 질문입니다. cocotb는 DUT는 Verilog/SystemVerilog/VHDL로 그대로 두고, 테스트만 Python으로 작성하게 합니다. 그러면 NumPy 레퍼런스를 `import numpy`로 그냥 가져다 쓸 수 있습니다.

### 1.2 왜 지금 이 주제가 중요한가

이것은 "Python이 더 쉽다" 수준의 취향 문제가 아닙니다. OpenTitan(Google·lowRISC의 보안 칩), Western Digital·Seagate의 SSD 컨트롤러, Tenstorrent·Groq·Rain AI 같은 AI 가속기 회사들이 검증 *핵심 플로우*로 cocotb를 채택하고 있습니다(`cocotb_note.md` Real-World Users). "UVM 하나로 모든 것을 하는 시대는 끝나간다"는 것이 이 흐름의 요약입니다. 이 모듈을 건너뛰면, 적합한 도구를 선택할 어휘 자체를 갖지 못한 채 모든 과제를 같은 망치로 두드리게 됩니다.

---

## 2. Intuition — 한 줄 비유 + 한 장 그림

:::tip[💡 한 줄 비유]
**cocotb** ≈ **HDL 시뮬레이터를 원격 조종하는 Python 리모컨**.<br>
DUT(RTL)는 시뮬레이터 *안*에서 평소처럼 돌아가고, 테스트(Python)는 시뮬레이터 *밖*에서 표준 인터페이스(VPI)를 통해 신호를 읽고 쓰며 "다음 clock까지 기다려" 같은 명령을 보냅니다. UVM은 테스트가 시뮬레이터 *안*에 함께 들어가 있는 모델입니다.
:::

### 한 장 그림 — 안에서 도는 UVM vs 밖에서 조종하는 cocotb

```d2
direction: right

UVM: "UVM 모델 (single simulation)" {
  SIM1: "HDL Simulator" {
    TB1: "**UVM TB**\n(SystemVerilog)\nuvm_test / env / driver"
    DUT1: "**DUT**\n(RTL)"
    TB1 -> DUT1: "vif (내부)"
  }
}

COCO: "cocotb 모델 (cosimulation)" {
  PY: "**Python process**\n@cocotb.test()\nasync def ..."
  SIM2: "HDL Simulator\n(VCS/Questa/Icarus/Verilator)" {
    DUT2: "**DUT**\n(RTL)"
  }
  PY -> SIM2: "VPI interface\n(표준)"
}
```

UVM에서는 testbench와 DUT가 한 시뮬레이션 안에 함께 컴파일되어 돕니다. cocotb에서는 Python 프로세스가 시뮬레이터 *밖*에 따로 있고, VPI(Verilog Procedural Interface)라는 표준 통로로 시뮬레이터를 제어합니다. 이 "밖에서 표준 통로로 조종한다"는 한 가지 사실에서 cocotb의 거의 모든 특성(시뮬레이터 독립성, Python 생태계 사용 가능, 라이선스 없는 무료 시뮬레이터 활용)이 따라 나옵니다.

:::note[VPI란 무엇인가 — cocotb 전체가 여기서 파생된다]
**VPI(Verilog Procedural Interface)는 시뮬레이터가 외부의 C 코드에 자신을 열어 주는 *표준 C API*** 입니다(IEEE 1800에 규정). 구체적으로 VPI는 외부 코드가 (1) 시뮬레이션 안의 신호·객체 핸들을 *이름으로 찾고*, (2) 그 신호 값을 *읽고 쓰며*, (3) "이 신호가 바뀌면" 또는 "이 시각이 되면" 나를 다시 불러 달라고 **콜백을 등록**할 수 있게 합니다. cocotb는 이 C API 위에 얇은 C 계층(시뮬레이터에 로드되는 VPI 라이브러리)을 두고, 그 위에서 Python을 구동합니다. 그래서 "신호를 읽고 쓴다", "다음 clock까지 기다린다", "어느 시뮬레이터든 같은 코드가 돈다"는 cocotb의 모든 특성이 *VPI라는 표준 C API 하나*에서 파생됩니다 — VPI를 지원하는 시뮬레이터면 무엇이든 cocotb가 붙을 수 있는 것도 이 때문입니다. (VHDL 쪽은 대응 표준인 VHPI를 씁니다.)
:::

---

## 3. 작은 예 — 이름 한 글자씩 뜯어보기

cocotb라는 이름 자체가 이 프레임워크의 설계를 압축하고 있습니다. **CO**routine-based **CO**simulation **T**est**B**ench를 단계별로 펼쳐 봅니다.

### 단계별 다이어그램 — 이름의 구성

```d2
direction: down

N1: "**CO**routine-based" {
  d1: "테스트가 coroutine(async def)\n으로 작성됨 — 중단/재개 가능"
}
N2: "**CO**simulation" {
  d2: "Python(시뮬레이터 밖)이\nHDL 시뮬레이터(안의 DUT)를\nVPI로 함께 구동"
}
N3: "**T**est**B**ench" {
  d3: "결국 하는 일은 검증 환경\n— 자극 인가 + 결과 확인"
}
N1 -> N2 -> N3: "이름 그대로 읽으면 설계가 보인다"
```

### 단계별 의미

| 구성 요소 | 의미 | UVM에서의 대응 |
|---|---|---|
| **CO**routine | 테스트를 `async def` coroutine으로 작성. `await`로 중단했다가 이벤트에 재개 | `task` 안의 `@(posedge clk)` 대기 |
| **CO**simulation | Python(밖) + HDL 시뮬레이터(안)를 VPI로 묶어 함께 실행 | 단일 시뮬레이션 — 별도 cosim 없음 |
| **T**est**B**ench | 자극을 넣고 출력을 확인하는 검증 환경 | UVM env 전체 |

### 가장 작은 cocotb 테스트

```python
import cocotb
from cocotb.triggers import RisingEdge

@cocotb.test()                       # UVM의 `class my_test extends uvm_test` + run_test()
async def smoke_test(dut):           # dut = 시뮬레이터 안 DUT의 핸들
    dut.rst_n.value = 0              # DUT 신호에 직접 write
    await RisingEdge(dut.clk)        # 다음 rising edge까지 Python 중단 → 시뮬레이터 진행
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    assert dut.ready.value == 1, "reset 후 ready가 1이 아님"   # 직접 read + 확인
```

:::note[여기서 잡아야 할 두 가지]
**(1) DUT는 Python 코드 어디에도 없습니다.** `dut`는 시뮬레이터 안에서 돌고 있는 RTL의 핸들일 뿐이고, Python은 그 신호를 읽고 쓰기만 합니다. 이것이 "테스트는 Python, DUT는 HDL"이라는 분리의 실체입니다. 더 정확히는, `dut`와 `dut.rst_n`은 시뮬레이터 안 RTL 계층을 비추는 *Python 프록시 객체*입니다. 그래서 `dut.rst_n.value = 0`은 Python 변수에 대입하는 게 아니라 — 프록시가 그 대입을 받아 **VPI write 호출로 변환**해 시뮬레이터 안 신호를 실제로 바꾸는 것이고, `dut.ready.value`를 읽는 것은 **VPI read**입니다. "DUT가 Python에 없다"는 말의 실체가 이 프록시-VPI 변환입니다.<br>
**(2) `@cocotb.test()` 데코레이터 하나가 UVM의 `uvm_test` 클래스 + `run_test()` 호출을 통째로 대신합니다.** factory 등록도, phase 선언도 없습니다. 그리고 `async def`로 선언된 이 함수는 보통 함수가 아니라 **coroutine** — *호출 스택(어디까지 실행했는지)을 보존한 채 중간에 멈췄다가, 그 지점부터 다시 이어 실행*할 수 있는 함수입니다. `await RisingEdge(dut.clk)`에서 멈추고 시뮬레이터가 깨우면 *바로 다음 줄*부터 재개되는 것이 그래서 가능합니다. 이는 OS 스레드 병렬이 아니라 UVM task가 `@(posedge clk)`에서 멈췄다 재개되는 것과 같은 *협력적 중단*입니다 — 메커니즘은 Module 02에서 깊게 다룹니다.
:::
---

## 4. 일반화 — cocotb vs UVM 다섯 축 비교

cocotb를 한마디로 위치시키려면 UVM과 나란히 놓고 보는 것이 가장 빠릅니다. `cocotb_note.md`의 비교 표를 다섯 축으로 정리하면 다음과 같습니다.

| 축 | UVM | cocotb |
|---|---|---|
| 언어 | SystemVerilog | Python 3 |
| 표준 | IEEE 1800.2 | 오픈소스 (FOSSi) |
| 라이선스 비용 | 시뮬레이터 라이선스 필요 | 무료 시뮬레이터(Icarus/Verilator) 가능 |
| 학습 곡선 | 가파름 (수개월) | 완만함 (수일~수주) |
| 라이브러리 생태계 | Verification IP(VIP) 풍부 | Python 라이브러리 전체 접근 가능 |

이 표의 각 행은 독립적인 사실이 아니라 하나의 뿌리에서 갈라져 나옵니다. cocotb가 "시뮬레이터 밖에서 표준 VPI로 조종한다"는 구조를 택했기 때문에, 언어가 Python이 될 수 있고, 그 결과 Python 라이브러리 전체를 쓸 수 있으며, 무료 시뮬레이터(Icarus/Verilator)도 VPI만 지원하면 그대로 붙고, IEEE 표준에 묶이지 않은 오픈소스로 남으며, SystemVerilog의 무거운 OOP·factory·phase 체계가 없으니 학습 곡선이 완만해집니다. 반대로 UVM은 시뮬레이션 안에 함께 들어가 IEEE 1800.2 표준 위에서 동작하기에, 표준화·VIP 생태계라는 강점과 라이선스·학습곡선이라는 비용을 함께 가집니다.

:::caution[표를 "어느 쪽이 우월한가"로 읽지 말 것]
다섯 축 중 어느 것도 일방적 우위가 아닙니다. "라이브러리 생태계"에서 UVM은 상용 VIP(AXI/PCIe/DDR)가 압도적으로 풍부하고, cocotb는 NumPy/PyTorch 같은 *소프트웨어* 라이브러리가 풍부합니다. 같은 단어가 양쪽에서 다른 것을 가리킵니다. 선택은 3장에서 trade-off로 다룹니다.
:::

---

## 5. 디테일 — 누가, 왜 cocotb를 쓰는가

### 5.1 실제 채택 사례

이름만 들어도 알 만한 곳들이 cocotb를 실제 검증 플로우에 쓰고 있습니다.

| 사용처 | 분야 | 사용 양상 |
|---|---|---|
| **OpenTitan** (Google, lowRISC) | 보안 칩 | 프로젝트 전체가 cocotb 사용 |
| **Western Digital, Seagate** | SSD 컨트롤러 | 컨트롤러 검증 |
| **Tenstorrent, Groq, Rain AI** | AI 가속기 | Python 기반 검증이 핵심 플로우 |
| **DPU/SmartNIC 벤더** | NIC/DPU | NIC TB를 cocotb로 구성 — LLM 보조로 전체 플로우를 빠르게 부트스트랩 |

여기서 패턴이 보입니다. *알고리즘 모델 통합이 중요한 분야*(AI 가속기, SSD)와 *오픈소스·교육 성격*(OpenTitan)이 cocotb로 강하게 기웁니다. AI 가속기는 검증 기대값이 곧 PyTorch/NumPy 모델이므로, 그 모델을 `import` 한 줄로 가져올 수 있는 cocotb가 자연스럽습니다.

### 5.2 cocotb의 장점 — 구조에서 따라 나오는 결과들

`cocotb_note.md`가 정리한 장점은 모두 2장의 "밖에서 VPI로 조종"이라는 구조에서 파생됩니다.

- Python을 아는 사람이라면 며칠 안에 테스트를 작성한다 (완만한 학습 곡선).
- NumPy, PyTorch, Scapy 같은 전체 Python 생태계를 평범한 `import`로 쓴다.
- 시뮬레이터 독립성 — 같은 Python 코드가 모든 시뮬레이터에서 변경 없이 동작한다.
- 무료 시뮬레이터를 쓸 수 있어 라이선스 없는 CI가 가능하다.
- pytest 통합, GitHub Actions 친화적.
- 알고리즘 모델(DSP, ML 가속기) 통합이 쉽다.

### 5.3 cocotb의 단점 — 같은 구조의 대가

장점과 단점은 동전의 양면입니다. 표준이 없다는 것은 자유롭다는 뜻이지만 동시에 팀마다 구조가 제각각이라는 뜻이기도 합니다.

- 대규모 SoC full-simulation에서는 Python 오버헤드 때문에 UVM보다 느리다.
- 표준화가 없어 팀마다 구조가 다르다.
- 상용 VIP(AXI, PCIe, DDR)는 압도적으로 UVM 기반이다.
- RAL과 coverage 지원이 약하다 — 외부 라이브러리(cocotb-bus, peakrdl-python, cocotb-coverage)에 의존하며 아직 표준화되지 않았다.

이 단점들은 3장의 "언제 쓰나" 판단으로 곧장 이어집니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'cocotb는 UVM의 상위 호환 대체재다']
**실제**: cocotb는 대체재가 아니라 *추가 카드*입니다. 상용 VIP가 필수인 프로토콜(PCIe Gen5, DDR), 대규모 SoC full-sim, 이미 쌓인 대규모 UVM 자산이 있는 환경에서는 UVM이 여전히 맞습니다.<br>
**왜 헷갈리는가**: "더 쉽고 무료"라는 인상이 "모든 면에서 낫다"로 과장되기 때문.
:::
:::danger[❓ 오해 2 — 'DUT도 Python으로 작성한다']
**실제**: DUT는 끝까지 Verilog/SystemVerilog/VHDL입니다. cocotb가 Python으로 바꾸는 것은 *테스트*뿐이고, DUT는 시뮬레이터 안에서 평소처럼 돕니다(2장의 cosimulation 구조).<br>
**왜 헷갈리는가**: "Python 기반 검증"이라는 표현을 "Python 기반 설계"로 잘못 확장하기 때문.
:::
:::danger[❓ 오해 3 — 'Python이니 라이선스가 항상 공짜다']
**실제**: cocotb는 *무료 시뮬레이터(Icarus/Verilator)와 조합할 때* 라이선스 없는 CI가 가능하다는 것이지, cocotb 자체가 상용 시뮬레이터(VCS/Questa)를 무료로 만들어 주지는 않습니다. VCS 위에서 cocotb를 돌리면 VCS 라이선스는 여전히 필요합니다.<br>
**왜 헷갈리는가**: "무료"가 프레임워크 라이선스와 시뮬레이터 라이선스를 뭉뚱그려서.
:::

### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 판단들)

| 상황 | 1차 판단 | 근거 |
|---|---|---|
| "이 블록을 cocotb로?" | IP/블록 레벨이고 알고리즘 레퍼런스가 Python에 있으면 강한 후보 | 5.1 채택 패턴 |
| "라이선스 없이 CI 돌리고 싶다" | Icarus/Verilator + cocotb 조합인지 확인 — 상용 시뮬레이터면 라이선스 여전히 필요 | 오해 3 |
| "상용 AXI/PCIe VIP가 필요하다" | UVM 쪽이 현실적 — cocotb는 상용 VIP가 약함 | 5.3 단점 |
| "팀마다 cocotb 구조가 달라 헷갈린다" | 정상 — cocotb는 표준이 없음. 팀 컨벤션 문서 확인 | 5.3 단점 |
| "RAL/coverage가 필요하다" | 외부 라이브러리(peakrdl-python, cocotb-coverage) 도입 필요 | 5.3 단점 |

---

## 7. 핵심 정리 (Key Takeaways)

- **cocotb = COroutine-based COsimulation TestBench**. 테스트는 Python coroutine, DUT는 그대로 HDL, 둘을 VPI cosimulation으로 묶는다.
- **핵심 분리**: cocotb가 Python으로 바꾸는 것은 *테스트*뿐. DUT는 끝까지 Verilog/SystemVerilog/VHDL.
- **다섯 축 비교**: 언어(SV vs Python), 표준(IEEE 1800.2 vs 오픈소스), 라이선스, 학습곡선, 생태계 — 모두 "안에서 도는가 밖에서 조종하는가"라는 한 구조에서 파생.
- **채택 패턴**: 알고리즘 모델 통합이 중요한 분야(AI 가속기, SSD)와 오픈소스/교육 성격에서 cocotb가 강하다 — OpenTitan, WD, Tenstorrent 등.
- **대체가 아니라 추가**: 상용 VIP·대규모 SoC·기존 UVM 자산 환경에서는 UVM이 여전히 맞다. "UVM 하나로 끝나는 시대가 끝나간다"는 것이 핵심.

:::caution[실무 주의점]
- "Python이니 빠르고 무료"라는 단순화 금지 — full-sim에서는 Python 오버헤드로 *느릴 수* 있고, 무료는 무료 시뮬레이터와 조합할 때만.
- 선택 기준은 취향이 아니라 IP 규모·VIP 가용성·팀 자산 — 다음 모듈과 3장에서 trade-off로 다룬다.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — 이름 해부 (Bloom: Understand)]
"cocotb"의 두 CO가 각각 무엇을 의미하며, 그 둘이 합쳐져 UVM과 무엇이 달라지는가?
<details>
<summary>정답</summary>

- 첫 CO = **COroutine**: 테스트가 `async def` coroutine으로, `await`에서 중단·재개된다.
- 둘째 CO = **COsimulation**: Python(시뮬레이터 밖)과 HDL 시뮬레이터(안의 DUT)를 VPI로 묶어 함께 구동한다.
- UVM과의 차이: UVM은 TB와 DUT가 *한 시뮬레이션 안*에 함께 있다. cocotb는 테스트가 *밖*에서 표준 VPI로 시뮬레이터를 조종한다. 이 한 가지가 언어·라이선스·생태계 차이의 뿌리다.

</details>
:::
:::tip[🤔 Q2 — 무료의 정확한 범위 (Bloom: Evaluate)]
"cocotb를 쓰면 시뮬레이터 라이선스가 필요 없다"는 주장은 항상 맞는가?
<details>
<summary>정답</summary>

항상 맞지 않다. cocotb는 VPI를 지원하는 *어떤* 시뮬레이터와도 동작한다. 무료 시뮬레이터(Icarus/Verilator)와 조합하면 라이선스 없는 CI가 가능하지만, VCS·Questa 위에서 cocotb를 돌리면 그 상용 시뮬레이터의 라이선스는 여전히 필요하다. 무료인 것은 cocotb 프레임워크 자체이지 시뮬레이터가 아니다.

</details>
:::
### 7.2 출처

**External**
- cocotb 공식 문서 — https://docs.cocotb.org/ (COroutine-based COsimulation TestBench 정의)
- *UVM 1.2 User's Guide* — Accellera (비교 기준)
- IEEE 1800-2017 §VPI — Verilog Procedural Interface (cosimulation 통로)

---

## 다음 모듈

→ [Module 02 — Coroutine & Cosimulation 아키텍처](../02_coroutine_cosimulation/): "밖에서 VPI로 조종한다"가 코드 수준에서 어떻게 동작하는가 — `async`/`await` coroutine 모델과 UVM 구조의 Python 매핑.

[퀴즈 풀어보기 →](../quiz/01_what_is_cocotb_quiz/)
