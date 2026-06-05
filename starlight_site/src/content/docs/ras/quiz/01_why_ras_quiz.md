---
title: "Quiz — Module 01: 왜 RAS인가"
---

[← Module 01 본문으로 돌아가기](../../01_why_ras/)

---

## Q1. (Remember)

RAS의 세 기둥을 올바르게 나열한 것은?

- [ ] A. Reliability, Accuracy, Speed
- [ ] B. Redundancy, Availability, Safety
- [ ] C. Reliability, Availability, Serviceability
- [ ] D. Resilience, Authentication, Security

<details>
<summary>정답 / 해설</summary>

**C**. RAS = **Reliability(신뢰성)**, **Availability(가용성)**, **Serviceability(정비성)** 로, 서버급 HW의 의존성(dependability) 세 기둥입니다. Reliability는 에러를 즉시 흡수(ECC/parity), Availability는 결함 속에서도 uptime 유지(격리/poison), Serviceability는 진단·기록·보고(error record + 인터럽트)를 담당합니다. 나머지 보기는 단어가 비슷해 보이지만 RAS의 정의가 아닙니다.

</details>
## Q2. (Understand)

"RAS가 있으면 에러가 발생하지 않는다"는 설명이 왜 틀린지 한 문장으로 설명하라.

<details>
<summary>정답 / 해설</summary>

RAS는 에러를 _없애는_ 기술이 아니라, 에러가 _반드시 발생하는_ 고밀도·고가동률 환경에서 그 에러를 검출·정정·격리·보고하는 기술이기 때문입니다. advanced node(sub-3nm)와 100% 가동률은 transient/permanent fault를 불가피하게 만들며, RAS의 가치는 "에러가 났을 때 시스템이 정직하고 우아하게 대응"하는 데 있습니다. "Reliability"라는 단어가 "에러 없음"처럼 들리지만 실제 의미는 "에러를 흡수하고도 기능을 유지"입니다.

</details>
## Q3. (Apply)

SRAM 캐시의 한 워드에 비트 1개가 뒤집혔다(transient). SEC-DED ECC가 있는 시스템에서 이 에러는 어떻게 분류·처리되는가?

- [ ] A. Uncorrectable Error로 분류, 즉시 panic
- [ ] B. Corrected Error로 분류, ECC가 정정해 동작 계속
- [ ] C. Deferred Error로 분류, poison 태그 후 전파
- [ ] D. 검출되지 않고 그대로 통과

<details>
<summary>정답 / 해설</summary>

**B**. 1-bit 플립은 SEC-DED ECC가 _정정_ 할 수 있으므로 **Corrected Error(CE)** 로 분류되고, on-the-fly로 정정되어 데이터가 정상화되고 동작이 계속됩니다(Reliability). A·C는 2-bit(UE)에 해당하는 처리이고, D는 보호가 없거나 parity 2-bit 맹점에 해당합니다. 단, CE가 같은 위치에서 _반복_ 되면 permanent fault 전조로 보아 카운터/threshold로 Serviceability 경로에 보고합니다.

</details>
## Q4. (Apply)

다음 처리는 RAS 세 기둥 중 어디에 속하는가?
"특정 메모리 bank가 반복적으로 에러를 내자 HW가 그 bank를 논리적으로 offline하고 남은 자원으로 계속 운영했다."

- [ ] A. Reliability
- [ ] B. Availability
- [ ] C. Serviceability
- [ ] D. 어디에도 속하지 않음

<details>
<summary>정답 / 해설</summary>

**B (Availability)**. failing 컴포넌트를 논리적으로 격리(offline)하고 남은 정상 자원으로 운영을 지속하는 것은 fault recovery & isolation으로, 결함 속에서도 uptime을 유지하는 **가용성(Availability)** 의 핵심 메커니즘입니다. Reliability(A)는 ECC/parity로 에러를 즉시 흡수하는 것, Serviceability(C)는 에러를 기록·보고해 진단·수리하는 것입니다. 이 사례에서 record/인터럽트로 운영자에게 알리는 부분이 추가되면 그 부분은 Serviceability에 해당합니다.

</details>
## Q5. (Analyze)

비트가 정확히 2개 뒤집힌 워드를 SEC-DED ECC로 read했다. 이후 데이터는 어느 기둥들을 거치며, 각 기둥이 무엇을 하는가?

<details>
<summary>정답 / 해설</summary>

세 기둥을 차례로 거칩니다. (1) **Reliability**: SEC-DED는 2-bit를 _정정하지 못하고 검출만_ 합니다(Double Error Detection) → Uncorrectable Error(UE)로 플래그. (2) **Availability**: 즉시 panic하지 않고 데이터에 Poison Bit를 달아 버스로 전파(deferred error). 실제 소비 시점(ALU/NPU)에 정밀 exception으로 영향 프로세스만 종료하고, 소비되지 않으면 시스템은 무사. (3) **Serviceability**: `ERR<n>STATUS`에 type/addr/timestamp를 기록하고 SCP/BMC로 인터럽트를 올려 진단·격리·수리를 가능케 함. 즉 같은 비트 플립이라도 2-bit는 검출→격리→보고의 파이프라인을 탑니다.

</details>
## Q6. (Evaluate)

"시스템 crash보다 SDC(Silent Data Corruption)가 더 위험하다"는 주장을 LLM 학습 맥락에서 정당화하라.

<details>
<summary>정답 / 해설</summary>

crash는 **가시적 실패** 입니다 — 잡이 멈추고 운영자가 알아채며 체크포인트에서 복구할 수 있어 손실이 compute 시간으로 한정됩니다. 반면 SDC는 **비가시적** 입니다. HW가 오염 데이터를 검출·보고하지 못하면 그 데이터가 학습 파이프라인으로 조용히 흘러 들어가 모델 weight를 미세 오염시키고, _어떤 알람도 없이_ 결과 무결성이 깨집니다. 언제·어디서 오염됐는지 사후 특정이 거의 불가능하며, 오염된 모델이 배포되면 추론까지 영향이 전파됩니다. 그래서 RAS의 최우선 목표가 silicon 레벨 SDC 방지이고, 검증도 "정상 동작"이 아니라 "에러 검출·격리"를 1급 대상으로 삼아야 합니다.

</details>
