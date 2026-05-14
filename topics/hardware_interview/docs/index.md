# Hardware Interview Prep

<div class="topic-hero" data-cat="career">
  <div class="topic-hero-mark">🎯</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">Hardware Interview Prep</div>
    <p class="topic-hero-sub">반도체 하드웨어 엔지니어 인터뷰 — Digital RTL, DV, Embedded, Architecture, Analog, Physical Design 6대 영역 종합</p>
  </div>
</div>

## 🎯 학습 목표

이 코스를 마치면 다음을 할 수 있습니다:

- **Recall (암기)** 6대 영역(Digital RTL, DV, Embedded, Architecture, Analog, Physical Design)의 빈출 인터뷰 키워드 목록을 떠올린다.
- **Explain (이해)** blocking vs non-blocking, Mealy vs Moore, VIPT vs PIPT, CCM vs DCM 같은 핵심 비교 개념을 자기 언어로 설명한다.
- **Apply (적용)** 실제 인터뷰 질문(예: "두 클럭 도메인 간 신호 전송 방법은?")에 대해 그림과 코드로 답변을 구성한다.
- **Analyze (분석)** 주어진 코드/회로 스니펫이 갖는 잠재 버그(race, glitch, metastability, setup violation)를 식별한다.
- **Evaluate (평가)** 후보 설계 옵션(synchronizer 종류, branch predictor 종류, LDO topology 등)의 장단점을 비교하고 상황별로 선택을 정당화한다.

## 📋 사전 지식

본 코스는 학부 4학년 ~ 신입/경력 인터뷰 수준입니다. 다음 항목을 알고 있는 것이 좋습니다.

- **디지털 회로 기본**: 조합/순차 회로, FF, MUX, 인코더, 카운터
- **Verilog 기초**: module/wire/reg, always block, assign
- **컴퓨터 구조 기본**: 5단 파이프라인, 캐시 계층
- **선택 사항**: 아날로그 회로(저학년 OP-amp), C 언어, 운영체제 기본

부족하면 본 챕터 안에서 1차 보충하지만, 도서로는 *Digital Design and Computer Architecture* (Harris), *CMOS VLSI Design* (Weste), *SystemVerilog for Verification* (Spear) 를 권장합니다.

## 🗺️ 개념 맵

```
[01 Digital RTL] ──┬──> [02 Design Verification]
                   │
                   ├──> [04 Computer Architecture] ──> [03 Embedded / Firmware]
                   │
                   └──> [06 Physical Design]

[05 Analog / Mixed-Signal] (독립 영역, RF/PMIC/SerDes 인터뷰)
```

- **01 → 02**: RTL 을 알아야 DV(테스트벤치, assertion) 가 의미를 가진다.
- **01 → 04**: 파이프라인/캐시/분기 예측의 microarch 는 RTL 로 구현된다.
- **01 → 06**: synth → P&R → 타이밍 클로저 — RTL 이 PD 의 입력.
- **04 → 03**: CPU/캐시/MMU 이해는 펌웨어/드라이버 작성의 전제.
- **05** 는 ASIC 의 analog/mixed-signal 블록(PLL, ADC/DAC, IO, regulator) 인터뷰 — Digital RTL 과는 결이 다름.

## 📚 학습 모듈

<div class="grid cards" markdown>

-   **[Unit 1: Digital Design / RTL](01_digital_rtl.md)**

    ---

    Verilog/SV 문법, FSM(Mealy/Moore), STA(setup/hold), CDC, AMBA/PCIe/SPI 등 protocols, FPGA vs ASIC.

    *⏱ 약 60분 · 난이도: 중급*

-   **[Unit 2: Design Verification](02_design_verification.md)**

    ---

    UVM phase/agent/factory, constraint randomization, SVA, monitor/scoreboard, CDC 검증, FIFO/arbiter verification.

    *⏱ 약 60분 · 난이도: 중급+*

-   **[Unit 3: Embedded / Firmware](03_embedded_firmware.md)**

    ---

    System design(thermostat, RTOS), I2C/SPI/CAN, volatile/linker/malloc, mutex/semaphore, cache coherency 펌웨어 관점.

    *⏱ 약 50분 · 난이도: 중급*

-   **[Unit 4: Computer Architecture](04_computer_architecture.md)**

    ---

    Cache mapping/replacement, pipeline hazards/Tomasulo, branch prediction(gshare/BTB), VIPT vs PIPT, TLB, coherence.

    *⏱ 약 60분 · 난이도: 중급+*

-   **[Unit 5: Analog / Mixed-Signal](05_analog_mixed_signal.md)**

    ---

    Op-amp 구성, CMOS small-signal, bandgap reference, LDO/Buck topology, layout(common-centroid), GaN.

    *⏱ 약 50분 · 난이도: 중급*

-   **[Unit 6: Physical Design](06_physical_design.md)**

    ---

    Floorplan, placement, CTS, IR drop, clock gating, multi-Vt, derating, signoff STA, low-power 기법.

    *⏱ 약 40분 · 난이도: 중급+*

</div>

## 🎓 코스 운영 방식

1. **챕터 본문**을 먼저 통독 — 인터뷰 빈출 개념과 1줄 답변을 습득.
2. **샘플 Q&A** 절에서 답을 가린 채 스스로 답해 본 뒤 해설 확인.
3. **챕터 퀴즈**(Bloom 분포 — Remember/Understand/Apply/Analyze/Evaluate) 로 자기 점검.
4. **용어집** 으로 휘발성 용어(예: VIPT, drain time, Miller compensation) 를 다시 정리.
5. 약점 영역은 [DV SKOOL 다른 토픽](https://humbleowl39.github.io/DV_SKOOL/) (UVM, AMBA, MMU 등) 으로 심화.

## 📖 관련 자료

- **Original**: [hardware-interview.com/study](https://www.hardware-interview.com/study) — 본 코스의 토픽 분류 출처
- **Verilog/SV 연습**: [HDLBits](https://hdlbits.01xz.net/), [EDA Playground](https://www.edaplayground.com/)
- **UVM 심화**: [DV SKOOL — UVM](https://humbleowl39.github.io/DV_SKOOL/uvm/)
- **AMBA 프로토콜 심화**: [DV SKOOL — AMBA Protocols](https://humbleowl39.github.io/DV_SKOOL/amba_protocols/)
- **컴퓨터 구조 도서**: Harris & Harris *Digital Design and Computer Architecture*, Hennessy & Patterson *Computer Architecture: A Quantitative Approach*
- **아날로그 도서**: Razavi *Design of Analog CMOS Integrated Circuits*
- **알고리즘**: LeetCode 인터뷰 빈출 (bit manipulation, arrays, strings, linked list)

## 💡 학습 팁

!!! tip "인터뷰 답변 구조"
    1. **한 줄 정의** — "X는 ~다." (15초)
    2. **그림/예시** — 화이트보드 또는 손짓으로 설명 (1분)
    3. **트레이드오프** — "장점/단점, 언제 쓰고 언제 안 쓰는가" (30초)
    4. **체험담** — "프로젝트에서 ~를 만났을 때 ~로 해결" (선택)

!!! warning "흔한 실수"
    - 외운 정의만 나열하고 *왜* 그런지 설명을 못함.
    - "blocking 이 빠르고 non-blocking 이 느리다" 같은 *틀린* 단순화.
    - 회로 그림 없이 말로만 설명 — 면접관이 이해 못 함.
    - 트레이드오프 질문에 한 쪽만 답함 — 양쪽을 다 알고 있어야 함.
