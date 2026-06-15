---
title: "Quiz — 07: 코딩·행동·영어"
---

코딩·디버깅 스토리·행동·영어 모의면접 핵심을 점검합니다. 정답은 펼치면 보입니다.

[← 07장 본문으로 돌아가기](../../07_coding_behavioral_english/)

---

## Q1. (Remember)

다음 C++ 표현 `n & (n - 1)` 은 정수 `n`에 대해 무슨 일을 하는가?

- [ ] A. 모든 비트를 1로 만든다
- [ ] B. 가장 낮은(최하위) set bit 하나를 0으로 지운다
- [ ] C. 최상위 set bit만 남긴다
- [ ] D. n을 2로 나눈다

<details>
<summary>정답 / 해설</summary>

**B**. `n - 1`은 최하위 set bit를 0으로 바꾸고 그 아래 비트를 모두 1로 만든다(예: `...1000` → `...0111`). 따라서 `n & (n-1)`은 그 최하위 set bit 위치만 0이 되고 나머지는 보존되어, 결과적으로 가장 낮은 set bit 하나가 제거된다. 이 성질이 `isPow2`(2의 거듭제곱이면 set bit가 하나뿐이라 한 번 지우면 0)와 Brian Kernighan popcount의 토대다. A·C·D는 이 연산의 동작이 아니다.

</details>

## Q2. (Apply)

다음 popcount 구현의 **시간 복잡도**는?

```cpp
int popcount(unsigned n){ int c=0; while(n){ n &= n-1; ++c; } return c; }
```

- [ ] A. O(1)
- [ ] B. O(32) 항상 고정
- [ ] C. O(set bit 수)
- [ ] D. O(n)

<details>
<summary>정답 / 해설</summary>

**C**. 루프 본문의 `n &= n-1`이 매 반복마다 최하위 set bit를 정확히 하나씩 제거하므로, 루프는 *set bit 개수만큼만* 돈다. 따라서 비트 폭(32)을 끝까지 시프트하는 O(32) 방식(B)보다 빠른 O(set bit 수)다 — set bit가 적은 입력에서 특히 유리하다. A는 단일 연산이 아니라 루프이므로 틀리고, D는 `n`의 값 크기가 아니라 set bit 수에 비례하므로 부정확하다. 면접에서는 "naive는 O(32), Kernighan은 O(set bits)"를 대비해 말하면 좋다.

</details>

## Q3. (Apply)

LRU 캐시를 get/put 모두 **O(1)**로 구현하려 할 때 표준적으로 조합하는 두 자료구조는?

<details>
<summary>정답 / 해설</summary>

**해시맵 + 이중 연결 리스트(doubly linked list)**. 해시맵은 키→노드 포인터를 O(1)로 조회하고, 이중 연결 리스트는 노드를 O(1)로 떼어내 head(가장 최근 사용)로 옮기거나 tail(가장 오래된 것)을 제거한다. get/put 시 접근한 노드를 head로 이동시키고, capacity 초과 시 tail을 evict한다. 둘 중 하나만으로는 안 되는 이유는, 해시맵만으로는 "사용 순서"를 O(1)로 유지할 수 없고 리스트만으로는 키 조회가 O(n)이기 때문이다. 이 구조가 캐시 replacement 정책 검증과 직결되어 DV 면접에서 가산점이 된다. (Python에서는 `OrderedDict.move_to_end` / `popitem(last=False)`로 동일 동작을 간결히 구현한다.)

</details>

## Q4. (Analyze)

시뮬레이션 로그에 UVM_ERROR가 수십 개 찍혀 있다. 디버깅을 시작할 때 가장 먼저 해야 할 일과 그 이유는?

<details>
<summary>정답 / 해설</summary>

**타임스탬프 기준으로 *첫 번째* 에러를 격리한다.** 대부분의 후속 에러는 첫 에러가 깨뜨린 상태에서 파생된 **cascading**(연쇄 파급)이라, 마지막이나 가장 빈번한 에러를 쫓으면 증상만 보고 근본 원인을 놓친다. 첫 에러의 소스 위치를 file:line으로 짚고, 이것이 **TB 버그인지 DUT 버그인지** 분류한 뒤, 고정 seed로 재현해 수정·회귀 확인까지 가는 것이 정석 흐름이다. "증상이 아니라 근본 원인", "first error를 cascading에서 분리"가 면접관이 듣고 싶어하는 키워드다.

</details>

## Q5. (Evaluate)

"가장 어려웠던 버그" 질문에 STAR로 답할 때, Action 단계에 반드시 넣어야 강한 신호가 되는 요소는 무엇이며 왜 중요한가?

<details>
<summary>정답 / 해설</summary>

핵심은 **first error 격리 → TB/DUT 분류 → 근본 원인 file:line 추적 → 고정 seed 재현 → coverage 보강**의 흐름을 Action에 담는 것이다. 이유: 이 다섯 요소가 각각 시니어 DV 엔지니어의 역량 신호이기 때문이다 — cascading을 거르는 분석력, 책임 소재를 가르는 분류력, 증상이 아닌 원인을 짚는 깊이, 재현 가능성을 보장하는 엄밀함, 그리고 *재발 방지*까지 닫는 검증자의 사고. 단순히 "버그를 고쳤다"로 끝내면 결과(R)만 있고 과정(A)이 비어 평가가 어렵다. HLS 경험이 있다면 "C++가 spec, RTL이 구현 — 둘의 divergence를 추적"을 넣으면 직무 적합도까지 어필된다.

</details>

## Q6. (Evaluate)

면접 끝에 면접관에게 던질 질문으로, 단순한 호기심을 넘어 *직무 이해도와 시니어리티*를 가장 잘 드러내는 것은?

- [ ] A. "복지와 연봉은 어떻게 되나요?"
- [ ] B. "검증 대상 코어가 in-order인지 OoO인지, 어느 ARM 세대인지요?"
- [ ] C. "야근이 많은가요?"
- [ ] D. "언제 결과를 알 수 있나요?"

<details>
<summary>정답 / 해설</summary>

**B**. in-order/OoO와 ARM 세대를 묻는 것은 검증 난이도·corner·필요 기법(ISS step-and-compare, 일관성 검증 등)이 거기에 따라 달라진다는 사실을 이해하고 있다는 신호다. 같은 맥락에서 "pre/post-silicon 업무 비중", "검증 환경 성숙도(ISS·formal 도입 정도)", "신규 인력이 맡는 레벨(unit/core/subsystem)"도 강한 질문이다 — 모두 공고의 책임을 읽고 직무를 구체적으로 그려봤음을 드러낸다. A·C·D는 정당한 관심사이긴 하나 직무 이해도를 보여주지 못하고, 마지막 라운드에 던지면 인상이 약해진다(채용 절차 질문은 리크루터에게).

</details>
