---
title: "Quiz — Module 10: 캐시는 왜 존재하는가"
---

[← Module 10 본문으로 돌아가기](../../10_why_cache/)

---

## Q1. (Remember)

메모리 계층을 빠른 것부터 느린 것 순으로 바르게 나열한 것은?

- [ ] A. DRAM → L3 → L2 → L1 → register
- [ ] B. register → L1 → L2 → L3 → DRAM → storage
- [ ] C. L1 → register → DRAM → L2 → L3
- [ ] D. storage → DRAM → register → L1

<details>
<summary>정답 / 해설</summary>

**B**. register file(~1 cycle) → L1(~4) → L2(~12) → L3/LLC(~40) → DRAM(~100+) → storage(NVMe ~µs) 순으로, _가까울수록 빠르고 작으며, 멀수록 느리고 크다_. 이 계층 자체가 Memory Wall(프로세서와 메모리 속도 격차)을 메우려는 구조입니다.

</details>
## Q2. (Understand)

시간 지역성(temporal locality)과 공간 지역성(spatial locality)의 차이와, 캐시가 각각을 어떻게 활용하는지 설명하라.

<details>
<summary>정답 / 해설</summary>

**시간 지역성**은 "방금 접근한 데이터가 곧 다시 접근될 가능성이 높다"(루프 변수, 자주 부르는 함수)는 성질로, 캐시는 한 번 가져온 데이터를 _가까이 붙잡아 두어_ 재접근을 hit 으로 만듭니다. **공간 지역성**은 "방금 접근한 데이터 _근처_ 가 곧 접근될 가능성이 높다"(배열 순회, 순차 코드 실행)는 성질로, 캐시는 한 바이트가 아니라 _블록(캐시 라인, 보통 64 byte) 단위_ 로 통째로 가져와 인접 접근을 미리 담아 둡니다. 이 두 베팅이 맞을 때 대부분의 접근이 빠른 상위 계층에서 해결되며, 베팅이 빗나가는 불규칙 접근(포인터 추적·해시)에서는 캐시 효율이 떨어집니다.

</details>
## Q3. (Understand)

공유 L3(LLC)가 사설 L1/L2 와 별개로 존재하는 두 가지 이유는?

<details>
<summary>정답 / 해설</summary>

첫째, **off-chip bandwidth wall** — DRAM 으로 나가는 핀 대역폭은 코어 수만큼 늘릴 수 없으므로, 칩 위에 크고 느린 SRAM 한 층(L1/L2 보다 크지만 DRAM 보다 빠름)을 두어 DRAM 트래픽을 흡수합니다. 둘째, **코어 간 공유** — 멀티코어가 공유 데이터를 각자 사설 캐시에만 두면 중복·비효율이 크므로, 모든 코어가 공유하는 한 층을 두어 공유 working set 을 한 번만 담고 코어 간 데이터 교환의 접점으로 씁니다. LLC 가 상위 캐시 내용을 어떻게 포함하느냐(inclusion policy: inclusive/exclusive/NINE)가 coherence 추적 방식과 유효 용량을 가릅니다.

</details>
