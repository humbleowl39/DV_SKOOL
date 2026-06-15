---
title: "Quiz — 01: 역할·전략·갭 분석"
---

본 모듈의 핵심 개념 이해도를 점검합니다. 정답은 펼치면 보입니다.

[← 01장 본문으로 돌아가기](../../01_role_and_strategy/)

---

## Q1. (Remember)

ARM CPU DV 공고의 4대 책임이 *아닌* 것은?

- [ ] A. Design verification for future CPU developments (코어 자체 검증)
- [ ] B. unit/multi-unit/core/subsystem 기능 검증 인프라 구축
- [ ] C. diagnostic code repository 작성
- [ ] D. analog 회로의 PSRR·CMRR 특성 측정

<details>
<summary>정답 / 해설</summary>

**D**. 공고의 4대 책임은 ① 차세대 CPU 코어 검증(메모리 컨트롤러·주변 IP가 아니라 *코어 자체*), ② unit→multi-unit→core→subsystem 계층 기능 검증 인프라 구축(핵심 업무), ③ diagnostic code repository 작성, ④ pre/post-silicon 성능 검증이다. D의 PSRR·CMRR은 아날로그 회로 특성으로 디지털 CPU DV 직무와 무관하다. 이 4대 책임을 업무로 분해할 수 있어야 자기 경험과의 갭을 정직하게 식별할 수 있다.

</details>

## Q2. (Understand)

unit / multi-unit / core / subsystem 계층이 각각 무엇을 검증하는지, 그리고 왜 이렇게 계층을 나누는지 설명하라.

<details>
<summary>정답 / 해설</summary>

- **Unit**: 코어 내부 개별 블록(decoder, ALU, LSU, BPU). 자극을 직접 제어하기 쉬워 깊은 corner를 빠르게 친다.
- **Multi-unit**: 블록 몇 개를 묶어 상호작용을 본다.
- **Core**: 코어 전체. 여기서 ISS step-and-compare가 돈다.
- **Subsystem**: 코어 + 캐시 + 인터커넥트. 멀티코어 일관성과 ordering이 핵심.

계층을 나누는 이유는 *제어성과 관측성의 trade-off* 때문이다. 낮은 계층일수록 자극을 정밀하게 넣어 corner를 빠르게 치지만 시스템 상호작용은 못 본다. 높은 계층일수록 현실적 시나리오를 보지만 깊은 corner를 유도하기 어렵다. 면접에서는 한 걸음 더 나아가 "unit 환경을 어떻게 core·subsystem으로 *재사용*하는가"를 UVM의 config·factory로 구조를 바꾸는 설계 관점으로 말할 수 있어야 한다.

</details>

## Q3. (Analyze)

프로토콜 블록의 스코어보드와 CPU 코어의 ISS step-and-compare는 *정답을 만드는 방식*이 어떻게 다른가? 이 차이가 검증 전략에 무엇을 강제하는가?

<details>
<summary>정답 / 해설</summary>

핵심은 **정답(reference)의 출처**다. 프로토콜 블록(AXI 브리지·FIFO 등)은 스코어보드가 *프로토콜 규칙*으로 예측값을 계산해 트랜잭션 단위로 비교한다. 반면 CPU 코어는 단순 규칙으로 정답을 못 만든다 — 명령이 파이프라인·캐시·추측 실행을 거치며 상태가 폭발하기 때문이다. 그래서 명령어 집합을 스펙대로 실행하는 **ISS(golden reference)**와 명령 단위로 비교하는 step-and-compare를 쓴다.

이 차이가 강제하는 것: ① 상태 공간이 방대해 순수 directed로는 불가능 → 랜덤 명령 생성 + coverage + formal을 함께 써야 한다. ② 비교 시점이 *retire(commit)*여야 한다 — execution 단계엔 폐기될 추측 결과가 섞여 ISS와 비교하면 false mismatch가 난다. ③ unit→core→subsystem 계층 재사용이 필수다.

</details>

## Q4. (Evaluate)

"CPU 코어를 직접 검증한 적이 없으니 HLS 검증 경험은 이 직무에서 약점이다"라는 자기 평가를 비판적으로 검토하고, 더 나은 재포지셔닝을 제시하라.

<details>
<summary>정답 / 해설</summary>

**약점이 아니다 — 오히려 강점으로 뒤집을 수 있다.** HLS는 C++ 알고리즘을 파이프라인·핸드셰이크·자원 공유를 가진 RTL로 합성하는데, 이를 검증하려면 *생성된 마이크로아키텍처*(II=Initiation Interval, stall 조건, 자원 경합)를 RTL 레벨에서 읽어내야 한다. 이것은 정확히 CPU 코어의 stall·해저드·자원 경합을 읽어내는 훈련과 동형이다.

따라서 솔직함의 원칙을 지키되 "방법론은 동형이며 이렇게 적용하겠다"는 설계로 답한다 — 예: *"HLS 생성 RTL을 검증하며 파이프라인·II·자원 경합을 RTL에서 추적해 왔고, 이는 CPU 코어의 해저드·자원 경합 독해와 같은 작업이며 ISS step-and-compare 같은 CPU DV 기법으로 자연스럽게 확장됩니다."* 모르는 것을 아는 척하다 꼬리질문에서 무너지는 것이 가장 나쁜 시나리오이므로, 갭(코어 직접 경험·ARM 깊이·post-silicon)은 인정하되 *전이 가능성*을 논거로 제시하는 것이 핵심이다.

</details>

## Q5. (Apply)

배점이 크고 갭이 클 가능성이 가장 높아 학습 1순위로 권장되는 주제는 무엇이며, 그 이유는?

- [ ] A. ARM ISA/아키텍처
- [ ] B. CPU 마이크로아키텍처(파이프라인·OoO·ROB·분기·캐시)
- [ ] C. 코딩·행동·영어
- [ ] D. UVM 방법론 복습

<details>
<summary>정답 / 해설</summary>

**B**. 학습 우선순위는 *배점이 크고 갭이 큰 순서*로 정하며, 1순위는 CPU 마이크로아키텍처다. 전형적 지원자(HLS·프로토콜 블록 경험)는 UVM/SV 방법론은 강하지만 OoO·BPU·일관성의 *깊이*에서 갭이 크고, 면접에서 컴퓨터 구조 배점이 크기 때문이다. 권장 순서는 마이크로아키텍처(02) → ARM(03) → 일관성·메모리 모델(04) → 방법론·UVM 재정비(05) → Hands-on 작성(06) → 코딩·행동·영어(07)다. D(UVM)는 이미 강한 영역이라 후순위로 "설명력 점검"에 그치고, 시간이 촉박하면 Week 1·2(02·03·04)에 집중하고 각 장의 샘플 Q&A를 소리 내어 리허설한다.

</details>
