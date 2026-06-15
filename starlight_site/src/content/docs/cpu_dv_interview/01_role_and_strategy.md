---
title: "01 — 역할·전략·갭 분석"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Analyze** CPU DV 채용 공고의 요구 역량을 실제 업무로 분해하고, 자신의 경력과 대조해 갭을 식별한다.
- **Explain** unit/multi-unit/core/subsystem 계층 검증 인프라가 각각 무엇을 검증하는지 설명한다.
- **Evaluate** 자신의 HLS·블록레벨 경험을 CPU 코어 검증 문맥으로 재포지셔닝하는 메시지를 정당화한다.
- **Apply** 면접까지 남은 기간에 맞춰 학습 순서(로드맵)를 구성한다.
:::
:::note[사전 지식]
- UVM/SystemVerilog 실무 경험 (TB 구축·회귀·coverage) — 부족하면 [UVM](../uvm/)
- 이 코스의 [개요](../)에서 면접 구조를 먼저 훑을 것
:::

---

## 1. 왜 CPU DV 면접은 다른가

먼저 토대 용어부터. **DV**(Design Verification, 설계 검증 — 설계한 RTL이 스펙대로 동작함을 시뮬레이션·formal로 보장하는 일)에서 검증 대상을 **DUT**(Design Under Test, 검증 대상 설계)라 부른다. 대부분의 DV 면접은 DUT가 프로토콜 블록(AXI 브리지, FIFO, arbiter 등)이라 "프로토콜대로 동작하는가"가 질문의 축이다.

그런데 CPU 코어가 DUT면 축이 바뀐다. CPU는 **모든 소프트웨어가 그 위에서 도는 기계**이고, 명령어가 파이프라인·캐시·분기예측기를 거치며 수백 가지 상태 조합을 만든다. 그래서 면접관은 "정상 동작"을 묻는 대신 *"어디서 깨질 수 있는가"*와 *"왜 그렇게 동작하는가"*를 파고든다. "out-of-order 실행이 왜 정확한 예외를 보장하나?" 같은 질문에 한 줄 정의로 답하면 반드시 두 번째 꼬리질문("그럼 store는 언제 메모리에 반영되나?")에서 막힌다. 이 코스 전체가 그 *인과를 말로 설명하는 훈련*인 이유다.

## 2. 공고를 업무로 분해하기

ARM CPU DV 공고(예: Google custom silicon)의 책임 문장은 거의 정해진 4개다. 각 문장이 실제로 무슨 일인지 풀어 보자.

### 2.1 "Design verification for future CPU developments"

차세대 CPU 코어를 검증한다. 메모리 컨트롤러·주변 IP가 아니라 **코어 자체**다. 핵심 차이는 정답의 출처다. 프로토콜 블록은 스코어보드가 프로토콜 규칙으로 정답을 계산하지만, CPU는 **ISS**(Instruction Set Simulator, 명령어 집합을 스펙대로 실행해 "정답" 아키텍처 상태를 내놓는 소프트웨어 — golden reference)와 명령 단위로 비교한다. 이걸 **step-and-compare**라 부르며 05장에서 깊게 다룬다.

### 2.2 "Build functional verification infrastructure: unit, multi-unit, core, subsystem"

이게 *핵심 업무*다. 검증 환경을 계층으로 짓는다.

- **Unit**: 코어 내부 개별 블록 — decoder, **ALU**(Arithmetic Logic Unit), **LSU**(Load-Store Unit, 메모리 접근을 담당하는 블록), **BPU**(Branch Prediction Unit, 분기 예측기). 자극을 직접 제어하기 쉬워 깊은 corner를 빠르게 친다.
- **Multi-unit**: 블록 몇 개를 묶어 상호작용을 본다.
- **Core**: 코어 전체. ISS step-and-compare가 여기서 돈다.
- **Subsystem**: 코어 + 캐시 + 인터커넥트 — 멀티코어 일관성과 ordering이 핵심.

면접에서는 "unit 환경을 어떻게 core·subsystem으로 *재사용*하는가"를 설계 관점으로 말할 수 있어야 한다. 재사용은 UVM의 config·factory로 구조를 바꾸는 데서 나온다(05장).

### 2.3 "Produce diagnostic code repositories"

CPU 위에서 도는 작은 테스트 프로그램(ARM 어셈블리·bare-metal C) 모음을 만든다. 이를 **diagnostic**(진단 코드)이라 한다. 부팅·예외 핸들러·MMU 설정 후 본문을 실행하고, 결과를 스스로 검사하거나(self-checking) ISS와 비교한다. 같은 diag를 pre-silicon(시뮬)과 post-silicon(실제 칩)에서 **재사용**하는 게 핵심 가치다 — 그래서 ARM ISA 지식(03장)이 필요하다.

### 2.4 "Verify and validate performance for pre-silicon and post-silicon"

기능뿐 아니라 성능을, 칩 제작 전(pre-silicon, 정확하지만 느림)과 후(post-silicon, 빠르지만 관측성 낮음) 양쪽에서 본다. **IPC**(Instructions Per Cycle), 파이프라인 stall, 캐시 미스율 같은 성능 지표를 성능 카운터로 측정한다. 면접 포인트는 이 trade-off를 알고, pre-silicon의 자극·체크를 post-silicon으로 재사용하는 개념을 말하는 것이다.

## 3. 갭 분석과 재포지셔닝

전형적인 지원자는 **HLS**(High-Level Synthesis, C++ 알고리즘을 RTL로 합성하는 흐름) 또는 프로토콜 블록 검증 경험을 갖고 CPU DV에 지원한다. 강점과 갭을 정직하게 나누자.

| 영역 | 보통 보유 | 흔한 갭 | 메우는 장 |
|------|-----------|---------|-----------|
| UVM/SV 방법론·환경 구축 | 강함 | — | 05장(설명력 점검) |
| 스크립팅 자동화(회귀·분석) | 보유 | — | "인프라 자동화 경험"으로 강조 |
| CPU 마이크로아키텍처 | 일반 지식 | OoO·BPU·일관성 깊이 | 02장 |
| ARM ISA/아키텍처 | 얕음 | EL·PSTATE·barrier·MMU | 03장 |
| CPU DV 특유 기법 | 얕음 | ISS step-and-compare·랜덤 명령 | 05장 |
| post-silicon | 얕음 | bring-up·디버그 | 01·05장(개념) |

### 재포지셔닝 — HLS 경험을 강점으로 뒤집기

HLS 검증 경험은 약점이 아니다. HLS는 C++ 알고리즘을 파이프라인·핸드셰이크·자원 공유를 가진 RTL로 바꾸는데, 이를 검증하려면 *생성된 마이크로아키텍처*(II = Initiation Interval, stall 조건, 자원 경합)를 RTL 레벨에서 읽어내야 한다. 이건 정확히 CPU 마이크로아키텍처 독해 훈련이다. 면접에서 쓸 한 줄:

> "HLS 생성 RTL을 검증하며 생성된 파이프라인·II·자원 경합을 RTL에서 추적해 왔습니다 — CPU 코어의 stall·해저드·자원 경합을 읽어내는 것과 같은 작업이고, ISS step-and-compare 같은 CPU DV 기법으로 자연스럽게 확장됩니다."

### 솔직함의 원칙

CPU 코어를 직접 검증한 적이 없거나 ARM이 얕다면, 숨기지 말고 *"방법론은 동형이며 이렇게 적용하겠다"*는 설계로 답한다. post-silicon 경험이 없으면 인정하되 "pre-silicon 자극·체크를 post로 재사용하는 개념"을 말한다. 모르는 것을 아는 척하다 꼬리질문에서 무너지는 것이 가장 나쁜 시나리오다.

## 4. 면접 구조와 학습 로드맵

ARM CPU DV 면접은 보통 ① UVM/방법론 ② 컴퓨터 구조 ③ ARM/ISA ④ 코딩 ⑤ 행동(영어)으로 구성된다(실제 라운드는 리크루터 확인). 우선순위는 배점이 크고 갭이 큰 순서다.

1. **CPU 마이크로아키텍처**(02장) — 갭 클 가능성, 배점 큼
2. **ARM 아키텍처**(03장)
3. **일관성·메모리 모델**(04장)
4. **CPU DV 방법론·UVM 재정비**(05장)
5. **Hands-on 작성 연습**(06장)
6. **코딩·행동·영어**(07장)

### 4주 로드맵 (하루 2~3시간 기준)

| 주차 | 집중 | 통과 기준 |
|------|------|-----------|
| Week 1 | 02장 — 파이프라인→OoO→ROB→분기→캐시 | "load-use hazard가 왜 1 stall인가", "ROB가 왜 precise exception을 보장하나"를 말로 설명 |
| Week 2 | 03·04장 — ARM EL/barrier/MMU, MESI | EL0~EL3 역할, DMB/DSB/ISB 차이, MESI 4상태 전이를 말로 |
| Week 3 | 05장 — CPU DV 방법론 + UVM 복습 | "CPU 코어 검증 환경을 0부터" 5분 설계 발표 |
| Week 4 | 06·07장 — 작성 연습 + 코딩 + 행동 STAR + 모의면접 | 즉석 constraint/covergroup 작성, STAR 3개 |

시간이 촉박하면 Week 1·2만 하고 각 장의 샘플 Q&A를 소리 내어 리허설한다.

## 5. 샘플 Q&A

답을 가린 채 스스로 답해 본 뒤 펼쳐 확인하라.

**Q. "CPU 코어 검증이 프로토콜 블록 검증과 무엇이 다른가?"**

<details>
<summary>모범 답변 방향</summary>

정답의 출처가 다르다. 프로토콜 블록은 스코어보드가 프로토콜 규칙으로 예측값을 만들지만, CPU는 ISS라는 golden reference와 명령 단위 step-and-compare로 검증한다. 또한 상태 공간이 방대해(파이프라인·캐시·추측 실행의 조합) 순수 directed로는 불가능하고, 랜덤 명령 생성 + coverage + formal을 함께 쓴다. 마지막으로 unit→core→subsystem 계층 재사용이 필수다.
</details>

**Q. "왜 CPU DV를 하고 싶은가?"**

<details>
<summary>모범 답변 방향</summary>

CPU는 모든 소프트웨어가 의존하는 IP라 검증의 leverage가 가장 크다 — 한 버그가 위의 모든 것에 영향을 준다. 가장 복잡한 IP를 검증하는 지적 도전과, 수억 사용자 제품에 들어가는 실리콘이라는 임팩트가 동기다.
</details>

## 6. 핵심 요약

- CPU DV 면접은 "정상 동작"이 아니라 *인과와 corner*를 묻는다 — 정의 암기로는 꼬리질문에서 막힌다.
- 공고의 4대 책임 = ① 코어 검증(ISS 비교) ② 계층 인프라 구축(핵심 업무) ③ diagnostic 작성 ④ pre/post-silicon 성능 검증.
- HLS·블록 경험은 "마이크로아키텍처 독해력"으로 재포지셔닝하면 강점이 된다.
- 학습 순서: 마이크로아키텍처 → ARM → 일관성 → 방법론 → 작성 → 코딩/행동.

다음 장에서 가장 배점이 큰 **CPU 마이크로아키텍처**로 들어간다.

→ 자기 점검: [퀴즈 — 01장](./quiz/01_role_and_strategy_quiz/)
