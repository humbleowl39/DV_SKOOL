---
title: "Quiz — Module 09: 분기 예측 & speculation"
---

[← Module 09 본문으로 돌아가기](../../09_branch_prediction/)

---

## Q1. (Apply)

2-bit saturating counter 예측기가 루프 분기(대부분 taken, 마지막 1회 not-taken)에서 1-bit 예측기보다 유리한 이유를 적용해 설명하라.

<details>
<summary>정답 / 해설</summary>

2-bit counter 는 네 상태(Strongly Not Taken → Weakly Not Taken → Weakly Taken → Strongly Taken)를 가져, 한 번의 예외적 결과로 예측을 _뒤집지 않습니다_. 루프가 N 번 taken 후 마지막에 한 번 not-taken 이면, 2-bit 는 "Strongly Taken"에서 "Weakly Taken"으로만 내려가 _여전히 taken 을 예측_ 합니다. 다음 루프 진입 시 다시 taken 이므로 misprediction 은 루프당 1 회(마지막 iteration)뿐입니다. 반면 1-bit 예측기는 마지막 not-taken 에 즉시 not-taken 으로 뒤집혀, 다음 루프 첫 진입(taken)에서 또 틀려 루프당 2 회 misprediction 이 발생합니다. 즉 2-bit 의 hysteresis 가 단일 anomaly 에 대한 내성을 줍니다.

</details>
## Q2. (Analyze)

분기의 방향 예측은 정확한데 fetch 가 자꾸 엉뚱한 주소에서 명령을 읽어 온다. 어느 구조를 의심해야 하며, 함수 return 의 경우 특히 무엇을 보나?

- [ ] A. 2-bit saturating counter
- [ ] B. 타겟 예측 구조(BTB/RAS); return 은 RAS push/pop 균형
- [ ] C. Reservation Station
- [ ] D. free list

<details>
<summary>정답 / 해설</summary>

**B**. 방향(taken/not-taken)이 맞는데 타겟 주소가 틀리므로 타겟 예측 구조를 의심합니다. 방향 예측기(2-bit/TAGE)는 "갈지 말지"만 정하고, "어디로 갈지"는 BTB 가 PC 를 키로 캐시한 타겟에서 옵니다. 특히 함수 _return_ 은 타겟이 호출 위치마다 달라 단순 BTB 로 부족하고 RAS(Return Address Stack)가 call 시 push·return 시 pop 으로 예측하므로, return 타겟이 틀리면 RAS 의 push/pop 균형(호출 깊이 초과, 비정상 흐름으로 인한 스택 오염)을 봐야 합니다. A/C/D 는 방향·자원 관련으로 타겟 오류와 무관합니다.

</details>
## Q3. (Analyze)

misprediction 이 발생했을 때 "fetch 만 다시 하면 된다"가 불충분한 이유를 분석하라.

- [ ] A. 캐시를 비워야 하기 때문
- [ ] B. ROB 의 해당 분기 이후 speculative 명령을 squash 하고 RS 를 drain 해야 architectural state 가 오염되지 않기 때문
- [ ] C. TLB 를 flush 해야 하기 때문
- [ ] D. 클럭을 재동기화해야 하기 때문

<details>
<summary>정답 / 해설</summary>

**B**. 분기 misprediction 시 이미 예측 경로의 명령들이 OoO 로 실행되어 ROB 와 RS 에 결과를 들고 있습니다. fetch 를 올바른 target 부터 재개하는 것뿐 아니라, ROB 에서 그 분기 _이후_ 의 모든 speculative 명령을 squash 하고 RS 에서도 해당 항목을 drain 해야 합니다. 그래야 잘못된 경로의 결과가 commit 되어 architectural state 를 오염시키는 것을 막습니다. squash 가 불완전해 일부 speculative 결과가 살아남으면 silent corruption 이 됩니다. A/C/D 는 misprediction 복구의 직접적 요건이 아닙니다(캐시 흔적은 복원되지 _않으며_, 이는 별개의 보안 이슈 — Q4).

</details>
## Q4. (Evaluate)

"misprediction 은 정확히 복구되는데 Spectre 같은 누출이 가능하다"는 모순처럼 보인다. architectural vs micro-architectural state 로 평가하라.

<details>
<summary>정답 / 해설</summary>

모순이 아니라 두 종류 상태의 비대칭입니다. squash 는 _architectural state_(레지스터·메모리의 관찰 가능한 값)만 program order 로 복원합니다 — 잘못 실행된 speculative 명령의 결과는 ROB 에서 버려져 정확성(correctness)은 보장됩니다. 그러나 그 명령이 실행 중 만진 _micro-architectural state_, 특히 speculative load 가 캐시에 끌어온 라인은 squash 로 제거되지 않습니다. 공격자는 이후 그 주소의 캐시 hit/miss 타이밍 차이를 측정해 squash 된 load 가 접근한 비밀 값을 역추론합니다. 즉 ISA 레벨(architectural)의 정확성은 지켜지지만 micro-architectural 부수효과(캐시 점유)를 통해 비밀성(confidentiality)이 깨집니다. 이는 성능을 위한 speculation 이 만든 근본적 보안 trade-off 로, 완화책(캐시 분할, speculation barrier)도 성능 비용을 수반합니다.

</details>
