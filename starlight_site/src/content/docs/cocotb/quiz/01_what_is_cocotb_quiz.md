---
title: "Quiz — Module 01: cocotb란 무엇인가 + vs UVM"
---

[← Module 01 본문으로 돌아가기](../../01_what_is_cocotb/)

---

## Q1. (Remember)

"cocotb"라는 약어가 풀어 쓴 것은?

- [ ] A. COde-COverage TestBench
- [ ] B. COroutine-based COsimulation TestBench
- [ ] C. COmpiled COmponent TestBench
- [ ] D. COntinuous COverage TestBench

<details>
<summary>정답 / 해설</summary>

**B**. cocotb는 **CO**routine-based **CO**simulation **T**est**B**ench의 약어입니다. 첫 CO는 테스트가 coroutine(`async def`)으로 작성됨을, 둘째 CO는 Python(시뮬레이터 밖)이 HDL 시뮬레이터(안의 DUT)를 함께 구동하는 cosimulation을 의미합니다. 나머지 보기는 모두 실재하지 않는 확장입니다.

</details>
## Q2. (Understand)

cocotb를 쓸 때 DUT는 어떤 언어로 작성되는가?

<details>
<summary>정답 / 해설</summary>

DUT는 cocotb에서도 그대로 Verilog/SystemVerilog/VHDL로 작성됩니다. cocotb가 Python으로 바꾸는 것은 *테스트*뿐이고, DUT는 시뮬레이터 안에서 평소처럼 컴파일되어 돕니다. Python 코드의 `dut`는 그 RTL의 핸들일 뿐이며, Python은 신호를 read/write하고 "다음 clock까지 기다려"를 명령할 뿐입니다. "Python 기반 검증"을 "Python 기반 설계"로 오해하지 않는 것이 핵심입니다.

</details>
## Q3. (Apply)

UVM의 `class my_test extends uvm_test`와 `run_test()` 호출을 cocotb에서 대신하는 것은?

- [ ] A. `import cocotb`
- [ ] B. `@cocotb.test()` 데코레이터를 붙인 `async def` 함수
- [ ] C. `cocotb.start_soon()`
- [ ] D. `class my_test(Scoreboard)`

<details>
<summary>정답 / 해설</summary>

**B**. `@cocotb.test()`로 데코레이트된 `async def` 함수 하나가 UVM의 test 클래스 선언과 `run_test()` 호출을 통째로 대신합니다. factory 등록도 phase 선언도 필요 없습니다. A(`import cocotb`)는 단순 모듈 임포트, C(`start_soon`)는 백그라운드 coroutine(fork) 기동, D는 무관한 클래스 상속입니다.

</details>
## Q4. (Analyze)

cocotb의 "언어가 Python", "무료 시뮬레이터 가능", "Python 라이브러리 전체 사용 가능"이라는 세 특성이 공통으로 파생되는 근본 구조는?

<details>
<summary>정답 / 해설</summary>

세 특성은 모두 "테스트가 시뮬레이터 *밖*에서 표준 VPI 인터페이스로 시뮬레이터(안의 DUT)를 조종한다"는 cosimulation 구조에서 파생됩니다. 밖에서 별도 프로세스로 돌기 때문에 그 프로세스의 언어를 Python으로 할 수 있고(언어), 그 결과 Python 생태계 전체를 `import`로 쓸 수 있으며(라이브러리), VPI만 지원하면 어떤 시뮬레이터든 붙으므로 Icarus/Verilator 같은 무료 시뮬레이터도 가능합니다(무료). UVM은 시뮬레이션 *안*에 함께 들어가 IEEE 1800.2 위에서 동작하므로 이 자유가 없습니다.

</details>
## Q5. (Evaluate)

"cocotb를 도입하면 우리 PCIe Gen5 SoC 검증의 라이선스 비용과 시간을 모두 줄일 수 있다." 이 주장을 평가하라.

<details>
<summary>정답 / 해설</summary>

타당하지 않습니다. 두 가지가 걸립니다. (1) PCIe Gen5는 상용 VIP가 필요한 프로토콜인데, 상용 VIP는 압도적으로 UVM 기반이라 cocotb로는 스택을 직접 모델링해야 하는 큰 비용이 듭니다. (2) 대규모 SoC full-simulation에서는 Python 오버헤드로 cocotb가 오히려 느립니다. 게다가 "라이선스 절감"도 무료 시뮬레이터와 조합할 때만 성립하는데, PCIe Gen5급 검증을 무료 시뮬레이터로 감당하기는 현실적으로 어렵습니다. 이 과제는 UVM이 적합합니다.

</details>
## Q6. (Analyze)

다음 중 cocotb가 *강하게* 채택되는 분야의 공통 특징으로 가장 적절한 것은? (OpenTitan, Tenstorrent, WD 등)

- [ ] A. 모두 대규모 SoC full-simulation이 주 목적이다
- [ ] B. 모두 상용 PCIe/DDR VIP에 크게 의존한다
- [ ] C. 알고리즘 모델 통합 또는 오픈소스/IP 성격이 강하다
- [ ] D. 모두 SystemVerilog 자산이 전혀 없다

<details>
<summary>정답 / 해설</summary>

**C**. AI 가속기(Tenstorrent/Groq)는 검증 기대값이 PyTorch/NumPy 모델이라 알고리즘 통합이 핵심이고, OpenTitan은 오픈소스 보안 칩, WD/Seagate는 IP·컨트롤러 레벨입니다. 모두 cocotb의 강점(Python 생태계 통합, IP/블록 레벨, 오픈소스 친화)에 정확히 맞습니다. A·B는 오히려 cocotb의 *부적합* 영역이고, D는 사실과 무관한 단정입니다.

</details>
