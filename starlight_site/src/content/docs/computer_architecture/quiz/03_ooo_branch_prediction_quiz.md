---
title: "Quiz — Module 03: OoO 실행 & 분기 예측"
---

[← Module 03 본문으로 돌아가기](../../03_ooo_branch_prediction/)

---

## Q1. (Remember)

Tomasulo 알고리즘의 세 가지 핵심 메커니즘은?

- [ ] A. L1/L2/L3 캐시
- [ ] B. Reservation Station, Common Data Bus, Register Renaming
- [ ] C. IF, ID, EX
- [ ] D. TLB, PTW, page fault

<details>
<summary>정답 / 해설</summary>

**B**. Reservation Station(RS, functional unit 앞의 operand 대기 슬롯), Common Data Bus(CDB, 완료 결과+tag 를 RS 들에 방송), Register Renaming(물리 레지스터 ≥ architectural 레지스터로 WAR/WAW 가짜 의존성 제거)입니다. A 는 메모리 계층(M04), C 는 파이프라인 단계(M02), D 는 주소 변환(M04)으로 모두 Tomasulo 와 무관합니다.

</details>
## Q2. (Understand)

OoO 코어에서 "execution 은 out-of-order 인데 retirement 는 in-order" 라는 말의 의미는?

<details>
<summary>정답 / 해설</summary>

명령의 _실행_(issue/완료)은 operand 가 준비된 순서로 프로그램 순서와 무관하게 일어나지만, architectural state(레지스터·메모리의 관찰 가능한 값)를 갱신하는 _retire(commit)_ 는 ROB 가 program order 대로 수행한다는 뜻입니다. 그래서 cache-miss 한 load 뒤의 독립 명령이 먼저 실행 완료되어도, 최종 상태 변화는 program order 를 따릅니다. 검증에서 reference model 과 scoreboard 는 _완료 순서_ 가 아니라 _retire 순서_ 로 비교해야 하며, 이를 혼동하면 정상 동작을 mismatch 로 신고합니다.

</details>
## Q3. (Apply)

2-bit saturating counter 예측기가 루프 분기(대부분 taken, 마지막 1회 not-taken)에서 1-bit 예측기보다 유리한 이유를 적용해 설명하라.

<details>
<summary>정답 / 해설</summary>

2-bit counter 는 네 상태(Strongly Not Taken → Weakly Not Taken → Weakly Taken → Strongly Taken)를 가져, 한 번의 예외적 결과로 예측을 _뒤집지 않습니다_. 루프가 N 번 taken 후 마지막에 한 번 not-taken 이면, 2-bit 는 "Strongly Taken"에서 "Weakly Taken"으로만 내려가 _여전히 taken 을 예측_ 합니다. 다음 루프 진입 시 다시 taken 이므로 misprediction 은 루프당 1 회(마지막 iteration)뿐입니다. 반면 1-bit 예측기는 마지막 not-taken 에 즉시 not-taken 으로 뒤집혀, 다음 루프 첫 진입(taken)에서 또 틀려 루프당 2 회 misprediction 이 발생합니다. 즉 2-bit 의 hysteresis 가 단일 anomaly 에 대한 내성을 줍니다.

</details>
## Q4. (Analyze)

misprediction 이 발생했을 때 "fetch 만 다시 하면 된다"가 불충분한 이유를 분석하라.

- [ ] A. 캐시를 비워야 하기 때문
- [ ] B. ROB 의 해당 분기 이후 speculative 명령을 squash 하고 RS 를 drain 해야 architectural state 가 오염되지 않기 때문
- [ ] C. TLB 를 flush 해야 하기 때문
- [ ] D. 클럭을 재동기화해야 하기 때문

<details>
<summary>정답 / 해설</summary>

**B**. 분기 misprediction 시 이미 예측 경로의 명령들이 OoO 로 실행되어 ROB 와 RS 에 결과를 들고 있습니다. fetch 를 올바른 target 부터 재개하는 것뿐 아니라, ROB 에서 그 분기 _이후_ 의 모든 speculative 명령을 squash 하고 RS 에서도 해당 항목을 drain 해야 합니다. 그래야 잘못된 경로의 결과가 commit 되어 architectural state 를 오염시키는 것을 막습니다. squash 가 불완전해 일부 speculative 결과가 살아남으면 silent corruption 이 됩니다. A/C/D 는 misprediction 복구의 직접적 요건이 아닙니다(캐시 흔적은 복원되지 _않으며_, 이는 별개의 보안 이슈 — Q5/본문 §5.2).

</details>
## Q5. (Evaluate)

"misprediction 은 정확히 복구되는데 Spectre 같은 누출이 가능하다"는 모순처럼 보인다. architectural vs micro-architectural state 로 평가하라.

<details>
<summary>정답 / 해설</summary>

모순이 아니라 두 종류 상태의 비대칭입니다. squash 는 _architectural state_(레지스터·메모리의 관찰 가능한 값)만 program order 로 복원합니다 — 잘못 실행된 speculative 명령의 결과는 ROB 에서 버려져 정확성(correctness)은 보장됩니다. 그러나 그 명령이 실행 중 만진 _micro-architectural state_, 특히 speculative load 가 캐시에 끌어온 라인은 squash 로 제거되지 않습니다. 공격자는 이후 그 주소의 캐시 hit/miss 타이밍 차이를 측정해 squash 된 load 가 접근한 비밀 값을 역추론합니다. 즉 ISA 레벨(architectural)의 정확성은 지켜지지만 micro-architectural 부수효과(캐시 점유)를 통해 비밀성(confidentiality)이 깨집니다. 이는 성능을 위한 speculation 이 만든 근본적 보안 trade-off 로, 완화책(캐시 분할, speculation barrier)도 성능 비용을 수반합니다.

</details>
