---
title: "Quiz — Module 11: 캐시 조직 & miss"
---

[← Module 11 본문으로 돌아가기](../../11_cache_organization/)

---

## Q1. (Remember)

3C miss 모델의 세 가지 miss 종류는?

- [ ] A. Read, Write, Execute
- [ ] B. Compulsory, Capacity, Conflict
- [ ] C. L1, L2, L3
- [ ] D. RAW, WAR, WAW

<details>
<summary>정답 / 해설</summary>

**B**. Compulsory(cold, 블록의 첫 접근 — 불가피), Capacity(working set 이 캐시 용량을 초과), Conflict(두 블록이 같은 set 에 매핑되어 반복 축출). conflict miss 는 associativity 를 높이면 줄고 full associativity 로 제거됩니다. D 는 데이터 해저드(M06)로 캐시 miss 와 무관합니다.

</details>
## Q2. (Apply)

64-byte 블록, 1024 set, 4-way 캐시(32-bit 물리 주소)에서 tag/index/offset 비트 수는?

- [ ] A. tag 16, index 10, offset 6
- [ ] B. tag 18, index 8, offset 6
- [ ] C. tag 14, index 12, offset 6
- [ ] D. tag 16, index 12, offset 4

<details>
<summary>정답 / 해설</summary>

**A**. offset = log₂(64) = 6 bit, index = log₂(1024) = 10 bit, tag = 32 − 10 − 6 = 16 bit. way 수(4)는 주소 분해에 영향을 주지 않습니다 — 같은 index 의 4 way 는 tag 비교로 구분되며, way 수는 한 set 이 흡수하는 충돌 블록 수만 정합니다. [Tag 16 | Index 10 | Offset 6] = 32 bit. B 는 set 수를 256 으로, C 는 4096 으로 오인한 경우입니다.

</details>
## Q3. (Understand)

write-back 캐시에서 "메모리가 항상 최신이 아니다"라는 말의 의미는?

<details>
<summary>정답 / 해설</summary>

write-back 정책은 캐시 hit 시 _캐시 라인만_ 갱신하고 dirty bit 를 세우며, 하위 계층(메모리)에는 그 라인이 _축출(eviction)될 때만_ 기록합니다. 따라서 dirty 라인이 축출되기 전까지 메모리는 stale(오래된) 값을 가지고, 진짜 최신 값은 캐시에만 존재합니다. 이는 write-through(hit 시 캐시+메모리 동시 갱신)와의 핵심 차이입니다. 다른 agent(다른 코어·DMA·가속기)가 같은 주소를 읽으면 stale 메모리를 볼 수 있어 coherence 프로토콜이 dirty 라인을 snoop 해야 하며, 검증의 reference model 은 "이 시점 최신 값이 캐시(dirty)인지 메모리인지"를 추적해야 합니다.

</details>
## Q4. (Evaluate)

"associativity 를 높이면 무조건 캐시가 빨라진다"는 주장을 AMAT 관점에서 평가하라.

<details>
<summary>정답 / 해설</summary>

부정확합니다. AMAT = Hit Time + Miss Rate × Miss Penalty 입니다. associativity 를 높이면 같은 set 의 충돌 블록을 더 많이 흡수해 conflict miss(=Miss Rate)가 줄어듭니다 — 이는 AMAT 를 낮추는 방향입니다. 그러나 더 많은 way 의 tag 를 _병렬 비교_ 해야 하므로 Hit Time 이 늘고 전력도 증가합니다 — 이는 AMAT 를 높이는 방향입니다. 두 항이 상충하므로 무한정 높이는 것이 답이 아니며, 워크로드의 conflict miss 비중과 hit time 민감도에 따라 최적 associativity 가 존재합니다. 예를 들어 conflict miss 가 거의 없는 워크로드에서는 associativity 증가가 hit time 만 늘려 오히려 손해입니다. 따라서 "무조건 빠르다"는 Miss Rate 한 항만 보고 Hit Time 증가를 놓친 잘못된 일반화입니다.

</details>
## Q5. (Analyze)

같은 코어가 한 store 직후 그 주소를 다시 load 하면 항상 최신 값을 받는데, _다른_ 코어는 그 store 를 한동안 못 볼 수 있다. 이 비대칭이 어디서 오는지 store buffer 로 분석하라.

<details>
<summary>정답 / 해설</summary>

retire 된 store 는 캐시에 곧장 안 내려가고 **store buffer(FIFO)** 에 잠시 머뭅니다(라인이 캐시에 없어도 코어를 안 멈추려고). 그동안 _자기 코어_ 가 그 주소를 load 하면 store buffer 에서 직접 값을 꺼내 줍니다(store-to-load forwarding) — 그래서 자기 자신엔 항상 최신입니다. 그러나 _다른 코어_ 는 store buffer 를 볼 수 없고, 그 store 가 buffer 에서 캐시/메모리로 drain 되어 globally visible 해진 뒤에야 봅니다. 그 store _뒤_ 의 내 load 는 buffer 를 우회해 먼저 진행하므로, 다른 코어 관점에선 "내 load 가 내 store 보다 먼저 일어난 것"처럼 보입니다(store→load reordering). 즉 비대칭의 근원은 "store 는 buffer 에서 지연되지만 load 는 앞질러 나간다"이며, 이것이 x86 TSO 가 store→load 만 허용하는 이유이고 fence 는 이 buffer 를 drain 해 순서를 강제합니다.

</details>
