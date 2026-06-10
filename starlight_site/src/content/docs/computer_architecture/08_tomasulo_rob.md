---
title: "Module 08 — Tomasulo & ROB"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Describe** Tomasulo 알고리즘의 세 메커니즘(Reservation Station — 실행 유닛 앞에서 operand 가 찰 때까지 명령을 대기시키는 슬롯, Common Data Bus — 완료된 결과를 기다리던 모든 곳에 한 번에 방송하는 버스, Register Renaming — 같은 이름의 레지스터가 만드는 가짜 의존성을 물리 레지스터 매핑으로 없애는 기법)이 어떻게 협력하는지 기술할 수 있다.
- **Analyze** 물리 레지스터 free list 와 RAT(speculative/retirement)가 dispatch stall·misprediction rollback 과 어떻게 얽히는지 분석할 수 있다.
- **Differentiate** ROB(Reorder Buffer)가 execution 의 out-of-order 와 retirement 의 in-order 를 분리해 precise exception(예외 발생 시 그 명령 직전까지의 상태를 정확히 복원할 수 있게 하는 것)을 가능케 함을 구분할 수 있다.
- **Explain** load/store 가 왜 일반 RS 가 아니라 LSQ 에서 다뤄지고, superscalar 의 wakeup-select 가 왜 O(N²) 비용을 갖는지 설명할 수 있다.
:::
:::note[사전 지식]
- [Module 07 — 왜 순서를 바꿔 실행하는가](../07_ooo_motivation/) (dispatch→execute→retire 골격, RS/CDB/ROB 큰 그림)
- [Module 06 — Pipeline & Hazard](../06_pipeline_hazard/) (WAR/WAW 해저드)
:::

:::note[이 모듈의 위치]
[M07](../07_ooo_motivation/)에서 OoO 의 _큰 그림_ 을 봤다면, 여기 **M08** 은 그 세 부품(RS·CDB·ROB)과 register renaming 의 _실제 동작_ 을 뜯어봅니다. 그 위에서 도는 분기 예측·speculation 은 [M09](../09_branch_prediction/)로 이어집니다.
:::
---

## 1. Why care? — 가짜 의존성과 부정확한 예외는 어떻게 생기나

[M07](../07_ooo_motivation/)에서 "실행은 뒤섞여도 retire 는 순서대로"라는 불변 조건을 세웠습니다. 그런데 그것을 _실제로_ 보장하는 부품이 없으면 두 가지가 무너집니다. 첫째, 이름만 같은 레지스터(WAR/WAW)가 가짜 의존을 만들어 OoO 가 막히거나, renaming 이 잘못되면 엉뚱한 값을 읽습니다. 둘째, 예외/인터럽트가 났을 때 어느 명령까지가 "확정"인지 경계가 흐려지면 복귀가 부정확해집니다(imprecise exception). Tomasulo 의 세 부품과 ROB 가 바로 이 둘을 막는 장치이고, 검증에서 "가짜 의존 stall", "CDB 로 안 깨어남", "예외 후 상태 부정확"은 전부 여기서 출발합니다.

---

## 2. Tomasulo 의 세 메커니즘

Tomasulo 알고리즘(원래 IBM System/360 FPU 용)은 세 부품으로 OoO 를 구현합니다. 먼저 용어 정리: **operand**(연산이 입력으로 받는 값 — 예: `ADD`의 두 소스 레지스터 값), **functional unit**(실제 연산을 수행하는 실행 유닛 — ALU/FPU/LSU 등), **dispatch**(디코드된 명령을 실행 대기 슬롯에 배정하는 단계), **tag**(아직 계산 안 끝난 결과를 가리키는 임시 이름표). **Reservation Station(RS)** 은 각 functional unit 앞의 대기 슬롯으로, dispatch 된 명령은 소스 operand 가 준비되거나 생산 명령의 tag 로 표시된 채 RS 에서 기다립니다. **Common Data Bus(CDB)** 는 functional unit 이 완료 시 결과와 tag 를 방송하는 버스로, 그 tag 를 감시하던 모든 RS 가 값을 capture 해 operand 를 ready 로 표시합니다. **Register Renaming** 은 물리 레지스터를 architectural 레지스터보다 많이 두고, rename 단계에서 각 목적 architectural 레지스터를 빈 물리 레지스터에 매핑해 rename 경계에서 WAW/WAR 해저드를 _제거_ 합니다.

| 메커니즘 | 해결하는 문제 | 비유 |
|---|---|---|
| Reservation Station | 멈춘 명령이 뒤를 막지 않게 | 재료 대기 주문 슬롯 |
| Common Data Bus | 결과를 기다리는 모든 명령에 동시 전달 | 주방 호출 방송 |
| Register Renaming | 이름만 같은 가짜 의존성(WAR/WAW) 제거 | 같은 이름 손님에 다른 번호표 |

### 2.1 물리 레지스터는 언제 할당되고 언제 free 되는가 — free list 와 dispatch stall

renaming 을 "아키텍처 레지스터 → 물리 레지스터 매핑"이라고만 하면, _물리 레지스터가 유한한 자원_ 이라는 결정적 사실이 빠집니다. 물리 레지스터 파일(PRF)은 아키텍처 레지스터보다 많지만(예: 32개 아키텍처 vs 100여 개 물리) 무한하지 않으며, 누가 비어 있는지를 **free list** 가 관리합니다.

생애 주기는 이렇습니다. 명령이 rename 단계에 들어오면 _목적 레지스터를 위해_ free list 에서 빈 물리 레지스터를 하나 꺼내(pop) 새 매핑으로 등록합니다 — **할당은 rename 시점**. 그 물리 레지스터는 이후 그 값을 읽는 모든 후속 명령이 끝날 때까지 살아 있어야 하므로, 곧바로 반환할 수 없습니다. 반환 시점은 **retire 시점**입니다 — 같은 아키텍처 레지스터에 _덮어쓴 다음 명령_ 이 retire 될 때, 그 명령이 밀어낸 _이전 매핑_ 의 물리 레지스터가 비로소 free list 로 돌아갑니다(더 이상 아무도 옛 값을 볼 수 없으므로). 즉 "할당 = rename, 해제 = 이전 매핑이 retire 로 죽을 때"입니다.

이 유한성의 직접적 귀결이 **dispatch stall** 입니다. long-latency miss 가 ROB head 를 오래 붙잡고 있으면 그 뒤 명령들이 retire 를 못 해 물리 레지스터를 반환하지 못하고, free list 가 비면 새 명령이 목적 레지스터를 못 받아 rename/dispatch 가 멈춥니다. 그래서 ROB 에 빈 자리가 있어도 _PRF 고갈_ 만으로 코어가 stall 할 수 있으며(ARM M07 의 "PRF 가 ROB 보다 먼저 찬다"), 검증에서 "가짜 의존도 없는데 dispatch 가 멈춤"이면 free list 잔량을 의심해야 합니다.

### 2.2 RAT 의 실체 — speculative RAT vs retirement RAT, 그리고 1-cycle rollback

renaming 의 매핑을 담는 표가 **RAT(Register Alias Table)** 인데, 고성능 코어는 이를 _두 벌_ 둡니다. **speculative RAT**(front-end RAT)은 rename 단계가 매 명령마다 갱신하는 "지금 in-flight 까지 반영된 최신 매핑"이고, **retirement RAT**(architectural RAT)은 retire 된 명령까지만 반영한 "확정된 매핑"입니다. 평소엔 speculative RAT 이 앞서 달리고, 명령이 retire 될 때마다 그 결과가 retirement RAT 으로 확정됩니다.

이 이중화의 가치는 **misprediction/예외 시 RAT 복원**에 있습니다. 분기 예측이 틀리면 그 분기 이후 speculative 하게 갱신된 매핑이 전부 무효이므로, speculative RAT 을 _그 분기 시점의 올바른 매핑_ 으로 되돌려야 합니다. 가장 단순한 방법은 retirement RAT 을 복사해 오는 것이지만, 그러면 분기와 그 사이 retire 된 명령들의 매핑이 사라집니다. 그래서 실용적 코어는 _각 분기마다 speculative RAT 의 snapshot(checkpoint)_ 을 떠 두고, misprediction 시 해당 checkpoint 를 한 번에 로드해 **1-cycle 에 rollback** 합니다 — 명령별로 매핑을 하나씩 되돌리는 느린 복구를 피하는 것입니다(ARM M07 §3.2 와 동일 메커니즘). 검증에서 "misprediction 후 가짜 의존이나 잘못된 소스를 읽음"이면 RAT 복원의 정확성을 의심합니다.

### 2.3 load/store 는 왜 일반 RS 가 아니라 LSQ 에서 다뤄지나

지금까지는 ALU 명령 중심이지만, 메모리 명령(load/store)에는 _일반 RS 가 못 푸는 추가 문제_ 가 있습니다. ALU 명령의 의존성은 레지스터 번호로 _명령 진입 시점에_ 알 수 있지만, 메모리 명령의 의존성은 **주소가 계산되기 전까지 알 수 없습니다.** `store [x1]` 다음에 오는 `load [x2]` 가 서로 충돌하는지는 x1·x2 가 가리키는 _실제 주소_ 가 같은지에 달렸는데, 그 주소는 명령이 실행되며 늦게 확정됩니다.

그래서 메모리 명령은 별도의 **LSQ(load/store queue)** — 보통 load queue(LDQ)와 store queue(STQ) — 에서 프로그램 순서로 추적되며, **memory disambiguation**(주소가 확정되는 대로 충돌 여부를 판정)을 수행합니다. 앞선 store 의 주소가 아직 미정인데 뒤의 load 를 먼저 실행하는 _투기적 load_ 도 LSQ 가 가능하게 하고, 나중에 충돌이 드러나면 그 load 와 이후를 squash 해 다시 실행합니다. 또 같은 주소에 직전 store 한 값을 곧 load 하면 메모리까지 안 가고 STQ 에서 직접 넘기는 store-to-load forwarding 도 LSQ 의 일입니다. 이 일반 챕터는 LSU 를 깊이 다루지 않으므로, 자세한 LDQ/STQ·STLF·MSHR 메커니즘은 [ARM Microarchitecture M07](../../cpu_arm/07_microarchitecture/)을 참조하세요.

### 2.4 superscalar — 한 사이클에 여러 명령을, 그리고 wakeup-select 의 O(N²) 비용

지금까지 암묵적으로 "한 사이클에 명령 하나"를 가정했지만, 현대 OoO 코어는 한 사이클에 _여러_ 명령을 fetch/issue/retire 하는 **superscalar** 입니다(예: 4-wide, 8-wide). issue width 가 N 이면 한 사이클에 준비된 명령 N 개를 동시에 functional unit 으로 보냅니다.

여기서 핵심 비용이 **wakeup-select 의 O(N²)** 입니다. 한 명령이 끝나면 그 결과 tag 를 _대기 중인 모든 명령_ 에 broadcast 해 깨워야 하는데(wakeup), N-wide 면 한 사이클에 N 개의 결과가 동시에 broadcast 되고, 윈도우의 각 대기 명령은 그 N 개 tag 를 자기 소스와 _전부 비교_ 해야 합니다. 비교기 수가 (대기 엔트리 수 × 발행 폭)에 비례해 늘고, 깨어난 것 중 N 개를 고르는 select 회로까지 더해져, 윈도우를 키우거나 폭을 넓힐수록 이 회로가 임계 경로가 되어 _주파수를 끌어내립니다_. 그래서 issue width 와 윈도우 크기에는 실용적 상한이 있습니다 — 일반론은 여기까지이고, 실측 자원 규모와 정량 분석은 [ARM Microarchitecture M07](../../cpu_arm/07_microarchitecture/)에서 다룹니다.

---

## 3. ROB — precise exception 의 토대

현대 프로세서는 **Reorder Buffer(ROB)** 를 더해 precise exception 과 speculative execution 을 지원합니다. 명령은 dispatch 시 _순서대로_ ROB 에 들어가고 _순서대로_ retire(commit)합니다 — 중간의 실행만 out-of-order 입니다. 분기 misprediction 이나 예외가 발생하면 ROB 에서 그 명령 _이후_ 의 모든 것을 squash 해 architectural state 의 일관성을 유지합니다(squash 의 정확성과 speculation 은 [M09](../09_branch_prediction/)).

```d2
direction: right

ROB: "**ROB (순환 큐)**" {
  head: "head → retire(in-order)"
  mid: "middle: 실행 완료/진행 중(OoO)"
  tail: "tail ← dispatch(in-order)"
}
EXC: "예외/misprediction"
EXC -> ROB: "offending 이후 전부 squash"
```

ROB 가 있기에 "실행은 OoO, retire 는 in-order"가 물리적으로 성립합니다 — head 부터만 commit 하므로 retire 는 자동으로 program order 이고, 예외는 그 명령이 ROB head 에 도달했을 때만 처리하면 _그 직전까지_ 의 상태가 정확히 확정되어 precise exception 이 보장됩니다.

---

## 4. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 — 'WAR/WAW 가짜 의존성은 renaming 만 켜면 저절로 사라진다']
**실제**: renaming 은 _물리 레지스터가 남아 있을 때만_ 가짜 의존을 없앱니다. free list 가 고갈되면 dispatch 가 멈추고(가짜 의존이 없어도 stall), RAT 복원이 부정확하면 misprediction 후 _틀린_ 소스를 읽습니다. renaming 은 "끄고 켜는 스위치"가 아니라 free list·RAT·rollback 이 함께 맞물려야 정확합니다.<br>
**왜 헷갈리는가**: renaming 을 매핑 한 줄로만 보고, 자원 유한성과 복원 메커니즘을 빠뜨려서.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 이름만 같은 레지스터에서 가짜 의존 stall | register renaming 미동작 | rename 테이블(RAT), free list |
| 가짜 의존도 없는데 dispatch 가 멈춤 | 물리 레지스터(PRF) 고갈 | free list 잔량, retire 지연 원인 |
| CDB 로 깨워야 할 명령이 영원히 대기 | tag 매칭 오류 또는 CDB broadcast 누락 | RS tag 비교, CDB 연결 |
| misprediction 후 가짜 의존/잘못된 소스 사용 | RAT 복원(checkpoint rollback) 오류 | speculative RAT snapshot 복원 경로 |
| 예외 후 architectural state 부정확 | precise exception 미보장(in-order retire 깨짐) | ROB head 부터 commit, 예외 표시 |

---

## 5. 핵심 정리 (Key Takeaways)

- **Tomasulo 3 부품**: RS(멈춘 명령이 뒤를 안 막게), CDB(결과+tag 방송), Register Renaming(WAR/WAW 제거).
- **renaming 은 유한 자원**: 할당 = rename 시점, 해제 = 이전 매핑이 retire 로 죽을 때. free list 고갈 → dispatch stall.
- **RAT 두 벌**: speculative(최신) vs retirement(확정). misprediction 시 분기 checkpoint 로 1-cycle rollback.
- **LSQ** 가 메모리 명령의 _늦게 확정되는 주소 의존성_ 을 disambiguation·store-to-load forwarding 으로 처리.
- **ROB** 가 OoO execution 과 in-order retire 를 분리 → precise exception 보장.
- **superscalar wakeup-select 는 O(N²)** — 윈도우·폭 확장의 주파수 한계.

:::caution[실무 주의점]
- 가짜 의존 stall vs PRF 고갈 stall 을 구분 — 전자는 RAT, 후자는 free list 잔량을 본다.
- misprediction 후 잘못된 소스를 읽으면 RAT checkpoint 복원의 정확성을 타겟 테스트.
:::
### 5.1 자가 점검

:::tip[🤔 Q1 — renaming 과 free list (Bloom: Analyze)]
가짜 의존성이 전혀 없는 독립 명령들인데도 dispatch 가 멈췄다. ROB 에는 빈 자리가 있다. 무엇을 의심해야 하는가?
<details>
<summary>정답</summary>

물리 레지스터 파일(PRF)의 **free list 고갈**을 의심해야 합니다. renaming 은 목적 레지스터마다 free list 에서 물리 레지스터를 하나 꺼내 쓰고, 그 레지스터는 _이전 매핑을 덮어쓴 명령이 retire 될 때_ 에야 반환됩니다. long-latency 명령(예: cache miss)이 ROB head 를 오래 붙잡으면 그 뒤 명령들이 retire 를 못 해 물리 레지스터를 반환하지 못하고, free list 가 비면 ROB 에 자리가 남아도 새 명령이 목적 레지스터를 못 받아 rename/dispatch 가 멈춥니다. 즉 stall 원인이 _의존성_ 이 아니라 _자원 고갈_ 입니다.

</details>
:::
### 5.2 출처

**External**
- Hennessy & Patterson, *Computer Architecture: A Quantitative Approach* — Tomasulo, register renaming, ROB, precise exception
- R. M. Tomasulo, *An Efficient Algorithm for Exploiting Multiple Arithmetic Units*, IBM J. R&D, 1967

---

## 다음 모듈

→ [Module 09 — 분기 예측 & speculation](../09_branch_prediction/): ROB 가 받쳐 주는 speculation 위에서, 분기 방향과 타겟을 어떻게 예측하고(2-bit/TAGE/BTB/RAS), misprediction squash 가 왜 architectural state 만 복원하고 캐시 흔적은 남겨 Spectre/Meltdown 을 낳는가.

[퀴즈 풀어보기 →](../quiz/08_tomasulo_rob_quiz/)
