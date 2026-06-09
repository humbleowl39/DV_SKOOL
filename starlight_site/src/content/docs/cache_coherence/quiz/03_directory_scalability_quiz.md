---
title: "Quiz — Module 03: Directory & 확장성"
---

[← Module 03 본문으로 돌아가기](../../03_directory_scalability/)

---

## Q1. (Remember)

LLC가 유지하는 **Snoop Filter(Directory)** 의 역할은?

- [ ] A. 캐시 line의 데이터를 압축 저장
- [ ] B. 어느 상위 캐시가 어느 line을 보유하는지 추적해 targeted snoop을 가능하게 함
- [ ] C. 메모리 접근 순서를 재배열
- [ ] D. DRAM refresh 타이밍 관리

<details>
<summary>정답 / 해설</summary>

**B**. Snoop Filter(Directory)는 정확히 어느 상위 캐시가 어느 cache line을 보유하는지를 추적하는 장부(ledger)입니다. 코어/GPGPU가 데이터를 요청하면 LLC가 directory를 조회해 *해당 데이터를 가진 특정 코어에만* targeted snoop을 보내, 모든 L1/L2에 broadcast할 때 발생하는 인터커넥트 혼잡을 크게 줄입니다.

</details>
## Q2. (Understand)

broadcast snooping이 코어 수가 늘어날 때 왜 확장성 문제를 일으키는지 설명하라.

<details>
<summary>정답 / 해설</summary>

broadcast snooping은 sharer 정보가 없어 한 코어의 read miss마다 "이 데이터 누가 가졌어?"를 *나머지 모든* L1/L2에 broadcast합니다. 코어가 64개·128개로 늘면 대부분의 캐시가 "없어"라고 답할 뿐인 무의미한 질문-응답이 인터커넥트를 가득 채웁니다. 트래픽이 코어 수 N에 비례(O(N))해 증가하므로, 코어를 더 붙여도 coherence 트래픽이 대역폭을 잠식해 성능이 오히려 떨어집니다.

</details>
## Q3. (Apply)

64코어 중 단 2개(Core2, Core7)만 line X를 공유 중이다. Core7이 X에 write할 때 broadcast snooping과 directory 각각 무효화를 몇 곳에 보내는가?

<details>
<summary>정답 / 해설</summary>

broadcast snooping은 sharer 정보가 없어 *나머지 모든* 캐시(최대 63곳)에 무효화/질문을 broadcast합니다. directory는 sharer 목록 `{Core2, Core7}`을 알기에 write를 하는 자신(Core7)을 제외한 *Core2 한 곳에만* targeted invalidate를 보냅니다. 즉 directory의 무효화 트래픽은 코어 수가 아니라 *실제 sharer 수*에 비례합니다.

</details>
## Q4. (Analyze)

directory가 이미 evict된 캐시를 sharer로 착각하는 경우(over-snoop)와, 실제 sharer를 목록에서 빠뜨리는 경우(under-snoop) 중 correctness 버그는 어느 쪽인가?

- [ ] A. over-snoop — 불필요한 트래픽이므로
- [ ] B. under-snoop — 무효화 누락으로 SWMR 위반이므로
- [ ] C. 둘 다 correctness 버그
- [ ] D. 둘 다 성능 문제일 뿐

<details>
<summary>정답 / 해설</summary>

**B**. under-snoop(sharer 누락)이 correctness 버그입니다. 빠뜨린 캐시는 무효화를 못 받아 stale 사본을 유지하고, write 중인 코어와 공존해 SWMR을 위반합니다. 반면 over-snoop(stale sharer에 보내는 불필요 snoop)은 *성능* 손해일 뿐 정확성은 유지됩니다. directory 검증의 1순위는 "sharer 누락이 없는가"입니다.

</details>
## Q5. (Evaluate)

"directory를 도입하면 broadcast가 절대 일어나지 않고 지연도 항상 줄어든다"는 주장을 평가하라.

<details>
<summary>정답 / 해설</summary>

두 부분 모두 과장입니다. 첫째, limited pointer directory는 sharer 수가 pointer 한도를 넘으면 *broadcast로 fallback*하므로 directory가 broadcast를 *줄일* 뿐 항상 없애지는 못합니다. 둘째, directory는 *트래픽*을 줄여 대규모에서 확장성을 주지만, 매 접근에 directory 조회 한 단계가 추가되어 *지연*은 오히려 늘 수 있습니다 — 소규모(수 코어)에서는 broadcast snooping이 더 빠를 수 있습니다. directory는 "확장성↔지연/저장비용"의 trade-off입니다.

</details>
