---
title: "Module 09 — 분기 예측 & speculation"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Compare** 정적/동적 분기 예측기(static, 2-bit saturating counter, local/global history, tournament, TAGE)를 정확도·비용 기준으로 비교할 수 있다.
- **Differentiate** 분기의 _방향_(taken/not-taken) 예측과 _타겟_(점프 주소) 예측(BTB/RAS/ITTAGE)이 왜 별개의 구조인지 구분할 수 있다.
- **Describe** speculative execution 이 미해결 분기 너머를 어떻게 실행하고 misprediction 시 ROB squash 로 어떻게 복구하는지 기술할 수 있다.
- **Evaluate** speculation 이 성능을 주면서 동시에 Spectre/Meltdown 류 side-channel 을 낳는 trade-off 를 평가할 수 있다.
:::
:::note[사전 지식]
- [Module 08 — Tomasulo & ROB](../08_tomasulo_rob/) (ROB, squash, RAT 복원)
- [Module 06 — Pipeline & Hazard](../06_pipeline_hazard/) (분기 페널티, flush)
:::

:::note[이 모듈의 위치]
OoO 3부작의 마지막입니다. [M07](../07_ooo_motivation/) 동기 → [M08](../08_tomasulo_rob/) 부품(Tomasulo·ROB) → **M09(지금)** speculation 과 분기 예측. ROB 가 받쳐 주는 "취소 가능한 실행" 위에서 분기 예측이 어떻게 IPC 를 끌어올리고, 같은 메커니즘이 어떻게 보안 취약점이 되는지 봅니다.
:::
---

## 1. Why care? — 예측은 성능의 핵심이자 보안의 구멍

깊은 파이프라인일수록 분기 misprediction 페널티는 커집니다([M06](../06_pipeline_hazard/)에서 본 10–20 사이클). 그래서 정확한 분기 예측은 IPC 유지의 핵심 장치입니다. 동시에, 예측이 틀린 경로를 미리 실행했다가 되돌리는 **speculation** 은 — [M08](../08_tomasulo_rob/)의 ROB squash 로 architectural state 는 깨끗이 복원되더라도 — 캐시 같은 micro-architectural 흔적은 남겨, Spectre/Meltdown 의 뿌리가 됩니다. 검증 관점에서 "방향은 맞는데 엉뚱한 주소로 fetch", "misprediction 후 stale 결과가 살아남음"은 전부 이 모듈의 메커니즘에서 출발합니다.

---

## 2. 분기 예측 — 정확도 사다리

분기를 잘못 예측하면 파이프라인을 flush(잘못 fetch 된 명령들을 비움)해야 하고(현대 깊은 파이프라인에서 페널티 10–20 사이클), 그래서 정확한 예측이 IPC(Instructions Per Cycle — 사이클당 완료 명령 수, 클수록 빠름; CPI 의 역수) 유지의 핵심입니다.

| 예측기 | 원리 | 대략 정확도 |
|---|---|---|
| Static (predict not/taken) | 항상 한 방향; 컴파일러 힌트 | ~60–70% |
| 2-bit saturating counter | 분기별 2-bit 상태기(SN→WN→WT→ST); 1회 오답에 안 뒤집힘 | 단일 anomaly 내성 |
| Local / Global history | BHR(Branch History Register, 최근 N 분기의 taken/not 결과 기록) + PHT(Pattern History Table, 그 이력 패턴별 예측을 담은 표) 인덱싱 | 패턴 의존 분기 포착 |
| Tournament (hybrid) | local/global 두 sub-predictor 가 경쟁, meta-predictor 가 분기별 선택 | DEC Alpha 21264 |
| TAGE | 기하급수적 history length 의 다중 태그 테이블 | SPEC CPU >95% |

```d2
direction: right

SN: "Strongly\nNot Taken"
WN: "Weakly\nNot Taken"
WT: "Weakly\nTaken"
ST: "Strongly\nTaken"

SN -> WN: "taken"
WN -> SN: "not taken"
WN -> WT: "taken"
WT -> WN: "not taken"
WT -> ST: "taken"
ST -> WT: "not taken"
```

2-bit saturating counter 의 핵심 가치는 _한 번의 예외적 결과로 예측을 뒤집지 않는_ 것입니다 — 대부분 taken 인 루프 분기가 마지막 iteration 에서 한 번 not-taken 이어도 예측을 유지해, 다음 루프 진입 시 다시 옳게 맞춥니다.

### 2.1 방향(direction)과 타겟(target)은 별개의 예측이다 — BTB·RAS

위 사다리는 전부 분기의 _방향_(taken/not-taken)만 예측합니다. 그런데 fetch 단계가 _다음 사이클에 어디서 명령을 읽을지_ 를 정하려면 방향만으로는 부족합니다 — taken 이라고 예측했다면 **어느 주소로** 점프하는지(타겟)까지 같은 사이클에 알아야 fetch 가 끊기지 않습니다. 그래서 방향 예측기와 _별개로_ **타겟 예측 구조**가 존재합니다.

- **BTB(Branch Target Buffer)**: 분기 명령의 PC 를 키로 그 분기의 _예측 타겟 주소_ 를 캐시합니다. 분기 명령을 디코드하기도 _전_ 에, fetch 단계가 현재 PC 로 BTB 를 조회해 "이 PC 가 분기이고 타겟은 여기"임을 알아내, 방향 예측이 taken 이면 즉시 그 타겟으로 fetch 를 redirect 합니다. BTB 가 없으면 타겟을 알려면 분기를 디코드(+주소 계산)해야 해서 taken 분기마다 fetch bubble 이 생깁니다.
- **indirect branch 와 RAS/ITTAGE**: 타겟이 _매번 바뀌는_ 분기는 단순 BTB 로 부족합니다. 함수 _return_ 은 호출한 곳으로 돌아가는데 그곳은 호출 위치마다 다르므로, call 시 복귀 주소를 push 하고 return 시 pop 하는 **RAS(Return Address Stack)**(LIFO)로 정확히 예측합니다. 가상 함수·switch 의 jump table 같은 _일반 indirect branch_ 는 같은 PC 라도 타겟이 여러 개라, 이력에 따라 타겟을 고르는 **ITTAGE** 같은 전용 예측기를 둡니다.

핵심 인과: fetch 가 한 사이클에 "분기인가 + taken 인가 + 타겟 어디인가"를 _모두_ 알아야 파이프라인이 안 끊기므로, 방향 예측(2-bit/TAGE)과 타겟 예측(BTB/RAS/ITTAGE)은 협력하는 _서로 다른_ 구조입니다. 검증에서 "방향은 맞는데 엉뚱한 주소로 fetch"면 BTB/RAS 쪽을, "타겟은 맞는데 갈지 말지를 틀림"이면 방향 예측기를 의심합니다.

---

## 3. Speculative execution

깊은 OoO 파이프라인과 분기 예측으로, 프로세서는 _미해결 분기 너머_ 의 명령을 예측이 맞다는 가정하에 실행합니다. 결과는 ROB 에 보관되고 분기가 옳게 해결될 때만 commit 됩니다. 예측이 틀리면 misprediction 이 branch resolution(EX 또는 전용 분기 유닛)에서 검출되고, ROB 의 해당 분기 이후 명령이 모두 squash 되며, fetch 가 올바른 target 부터 재개됩니다.

### 3.1 squash 가 architectural state 를 건드리면 안 되는 이유

speculative 명령은 ROB 에 결과를 _격리_ 한 채 commit 전까지 architectural state(레지스터 파일·메모리)를 바꾸지 않아야 합니다. 그래야 misprediction 시 단순히 ROB 항목만 버리면(squash) 상태가 깨끗이 복원됩니다. 만약 speculative store 가 메모리에 일찍 반영되거나 speculative 결과가 architectural 레지스터에 새면, 잘못된 경로의 효과가 영구화되어 silent corruption 이 됩니다. 검증에서는 "misprediction 직후 architectural state 가 분기 직전과 동일한가"를 반드시 확인해야 합니다.

### 3.2 Spectre/Meltdown — speculation 의 어두운 면

같은 squash-on-misprediction 메커니즘이 side-channel 취약점의 뿌리입니다. squash 된 speculative load 라도 그 데이터를 캐시에 끌어왔다면 _캐시 타이밍 흔적_ 은 지워지지 않습니다. 공격자는 이 타이밍 차이로 squash 된 명령이 만진 비밀 값을 역추론합니다. 즉 architectural state 는 복원되어도 micro-architectural state(캐시 점유)는 복원되지 않는다는 비대칭이 핵심입니다.

---

## 4. DV 관점 — OoO 코어 검증의 기대값 모델

OoO 코어 검증에서 reference model 은 항상 **retire 순서 = program order** 로 architectural state 를 갱신해야 하며, scoreboard 는 실행 완료 순서가 아니라 retire 순서로 비교합니다. WAR/WAW 가 renaming 으로 제거되었는지([M08](../08_tomasulo_rob/)), CDB forwarding 이 올바른 tag 로 깨우는지, misprediction squash 가 완전한지가 핵심 coverage 입니다. 이는 OoO 응답을 가진 프로토콜의 scoreboard(예: AXI ID 별 큐, [UVM M05](../../uvm/05_tlm_scoreboard_coverage/))와 동일한 사고 — "도착(완료) 순서로 비교하지 말고 의미 있는 순서(retire/ID)로 매칭하라".

---

## 5. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'misprediction 이면 그냥 fetch 만 다시 하면 된다']
**실제**: fetch 재개뿐 아니라 ROB 의 해당 분기 _이후_ 모든 speculative 명령을 squash 하고 RS 를 drain 해야 합니다. squash 가 불완전하면 잘못된 경로 결과가 architectural state 에 새어 silent corruption.<br>
**왜 헷갈리는가**: "예측 실패 = 다시 시작" 이라는 단순 모델이 squash 범위를 과소평가해서.
:::
:::danger[❓ 오해 2 — 'speculation 이 squash 되면 흔적이 전혀 안 남는다']
**실제**: architectural state 는 복원되지만 **micro-architectural state(캐시 점유)는 복원되지 않습니다**. squash 된 speculative load 가 끌어온 캐시 라인의 타이밍 흔적이 Spectre/Meltdown 의 누출 경로입니다.<br>
**왜 헷갈리는가**: "취소 = 완전 원상복구" 라는 가정이 캐시 부수효과를 빠뜨려서.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 방향은 맞는데 엉뚱한 주소로 fetch | BTB/RAS 타겟 예측 오류 | BTB 갱신, RAS push/pop 균형 |
| misprediction 후 stale 결과가 살아남음 | squash 범위 오류(분기 이후 일부만 버림) | ROB squash 인덱스, RS flush |
| 예측 정확도가 비정상적으로 낮음 | 예측기 history/PHT 갱신 타이밍 오류 | BHR/PHT 업데이트 경로 |
| misprediction 직후 architectural state 가 분기 직전과 다름 | speculative 결과가 commit 전에 새어 나감 | speculative store 격리, ROB commit 게이팅 |

---

## 6. 핵심 정리 (Key Takeaways)

- **분기 예측 사다리**: static(60–70%) → 2-bit(anomaly 내성) → history → tournament → TAGE(>95%).
- **방향과 타겟은 별개**: 2-bit/TAGE 가 taken 여부를, BTB/RAS/ITTAGE 가 점프 주소를 예측 — 둘 다 맞아야 fetch 가 안 끊긴다.
- **Speculation** 은 미해결 분기 너머를 실행; misprediction 시 ROB squash + fetch 재개.
- **squash 는 architectural state 만 복원**, micro-architectural(캐시 흔적)은 남아 Spectre/Meltdown 의 뿌리.
- **검증 핵심 coverage**: squash 범위 완전성, retire 순서 비교, 타겟/방향 예측 분리.

:::caution[실무 주의점]
- misprediction squash 의 _범위 완전성_ 을 타겟 테스트로 검증(예측 오류 직후 분기 직전 상태 동일성 확인).
- "방향 맞고 주소 틀림" vs "주소 맞고 방향 틀림"을 나눠 BTB/RAS 와 방향 예측기를 따로 의심.
- AXI 등 OoO 프로토콜 scoreboard 의 per-ID 매칭(UVM M05)과 동일한 사고를 코어 검증에 적용.
:::
### 6.1 자가 점검

:::tip[🤔 Q1 — speculation 의 비대칭 (Bloom: Evaluate)]
"misprediction 이 정확히 복구되는데 왜 Spectre 같은 누출이 가능한가?"를 architectural vs micro-architectural state 로 평가하라.
<details>
<summary>정답</summary>

squash 는 architectural state(레지스터·메모리의 관찰 가능한 값)만 program order 로 복원합니다 — 잘못 실행된 speculative 명령의 결과는 ROB 에서 버려져 영구화되지 않습니다. 그러나 그 명령이 실행 중 만진 micro-architectural state, 특히 캐시에 끌어온 라인은 squash 로 _제거되지 않습니다_. 공격자는 이후 캐시 hit/miss 의 타이밍 차이로 squash 된 speculative load 가 접근한 비밀 값을 역추론합니다. 즉 정확성(correctness)은 architectural 레벨에서 보장되지만 비밀성(confidentiality)은 micro-architectural 부수효과에서 깨집니다 — 성능을 위한 speculation 이 만든 보안 trade-off 입니다.

</details>
:::
:::tip[🤔 Q2 — 방향 vs 타겟 (Bloom: Analyze)]
분기의 방향 예측은 정확한데 fetch 가 자꾸 엉뚱한 주소에서 명령을 읽어 온다. 어느 구조를 의심해야 하며, 함수 return 의 경우 특히 무엇을 보나?
<details>
<summary>정답</summary>

방향(taken/not-taken)이 맞는데 타겟 주소가 틀리므로 **타겟 예측 구조(BTB/RAS)** 를 의심해야 합니다. 방향 예측기(2-bit/TAGE)는 "갈지 말지"만 정하고, "어디로 갈지"는 BTB 가 PC 를 키로 캐시한 타겟에서 옵니다. 특히 함수 _return_ 은 타겟이 호출 위치마다 달라 단순 BTB 로 부족하고 **RAS(Return Address Stack)** 가 call 시 push·return 시 pop 으로 예측하므로, return 타겟이 틀리면 RAS 의 push/pop 균형(예: 호출 깊이 초과, 비정상 흐름으로 인한 스택 오염)을 봐야 합니다.

</details>
:::
### 6.2 출처

**External**
- Hennessy & Patterson, *Computer Architecture: A Quantitative Approach* — dynamic branch prediction, speculation
- Seznec & Michaud, *A case for (partially) TAgged GEometric history length branch prediction* — TAGE
- Kocher et al., *Spectre Attacks: Exploiting Speculative Execution* — side-channel

---

## 다음 모듈

→ [Module 10 — 캐시는 왜 존재하는가](../10_why_cache/): OoO 가 cache miss 한 load 를 _건너뛸 수_ 있어도, 그 miss 자체를 줄이는 것은 메모리 계층의 몫이다. 왜 작고 빠른 저장소를 크고 느린 저장소 앞에 두는가 — Memory Wall 과 locality 부터.

[퀴즈 풀어보기 →](../quiz/09_branch_prediction_quiz/)
