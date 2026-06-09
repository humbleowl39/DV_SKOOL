---
title: "Module 03 — Directory 기반 Coherence & 확장성"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** broadcast snooping이 코어 수 증가에 따라 왜 인터커넥트를 포화시키는지 설명할 수 있다.
- **Differentiate** broadcast snooping과 directory 기반 추적의 확장성·지연·저장 비용 trade-off를 비교할 수 있다.
- **Explain** directory(snoop filter)가 sharer 정보를 들고 targeted snoop만 보내 트래픽을 줄이는 원리를 설명할 수 있다.
- **Trace** directory 항목의 sharer/owner 갱신이 한 read/write에서 어떻게 일어나는지 추적할 수 있다.
:::
:::note[사전 지식]
- [Module 02 — Snooping & MESI/MOESI](../02_snooping_mesi_moesi/)
- coherence state(M/E/S/I), SWMR invariant
:::
---

## 1. Why care? — 코어가 64개면 broadcast가 버스를 막는다

### 1.1 시나리오 — snoop broadcast의 폭발

snooping은 우아하지만 한 가지 전제에 의존합니다 — *모든* 캐시가 *모든* 트랜잭션을 엿들을 수 있어야 합니다. 코어가 4개일 때는 괜찮지만, 64개·128개로 늘어나면 한 코어의 read miss마다 "이 데이터 누구 갖고 있어?"라는 질문이 나머지 모든 L1/L2로 broadcast됩니다. 대부분의 캐시는 "나 없어"라고 답할 뿐인데, 이 무의미한 질문-응답이 인터커넥트를 가득 채웁니다.

결과적으로 코어를 더 붙여도 coherence 트래픽이 대역폭을 잡아먹어 성능이 오히려 떨어집니다. 이 확장성 벽을 넘기 위해 등장한 것이 **directory(= snoop filter)** 입니다. directory는 "어느 캐시가 어느 line을 들고 있는가"를 *장부(ledger)* 로 추적해, 질문을 *해당 캐시에만* 보냅니다(targeted snoop). 이것이 ARM ACE에서 CHI로, 그리고 LLC 기반 directory로 진화한 핵심 동기입니다.

---

## 2. Intuition — 사서의 대출 장부, 한 장 그림

:::tip[💡 한 줄 비유]
**Broadcast snooping** ≈ 동네 전체에 "이 책 누구 가졌어?"를 *확성기로 외치는* 것. 사람이 많아지면 소음만 커짐.<br>
**Directory** ≈ 사서가 **대출 장부**를 들고 있어, 그 책을 빌려간 *특정 사람에게만* 연락. 동네가 커져도 연락은 딱 필요한 만큼만.
:::
### 한 장 그림 — directory가 targeted snoop을 보낸다

```d2
direction: down

REQ: "**Requester (Core 7)**\nread miss on line X"
DIR: "**Directory / Snoop Filter (at LLC)**\nX → {sharers: Core2, owner: Core2}\n장부 조회" {
  style.fill: "#fff4e5"
}
C2: "**Core 2 cache**\nX: M (dirty)"
OTHERS: "**Core 0,1,3..63**\n(질문 받지 않음)" {
  style.fill: "#eeeeee"
}

REQ -> DIR: "① request"
DIR -> C2: "② targeted snoop\n(only the holder)"
C2 -> REQ: "③ data forward + state 갱신"
DIR -> OTHERS: "broadcast 안 함" { style.stroke-dash: 4; style.stroke: "#999" }
```

### 왜 이 디자인인가 — Design rationale

directory가 답이 되는 이유는 두 요구의 충돌을 해소하기 때문입니다.

1. **coherence는 여전히 SWMR/Data-Value를 지켜야** → 누가 사본을 들고 있는지 정확히 알아야 무효화/공급이 가능.
2. **그러나 broadcast는 코어 수에 따라 트래픽이 O(N)으로 폭발** → 모두에게 묻지 말고 *아는 캐시에만* 물어야.

directory는 1을 만족하기 위한 정보(sharer/owner 집합)를 *중앙 장부*에 모아, 2를 위해 broadcast 대신 targeted snoop을 보냅니다. 대가는 directory를 저장할 메모리와 directory 조회 한 단계가 추가되는 지연입니다.

---

## 3. 작은 예 — directory가 sharer를 추적하는 read/write

line X에 대해 Core2가 dirty 보유 중인 상태에서, Core7이 read miss를 내고, 이어 Core7이 write합니다.

### 단계별 다이어그램

```d2
direction: down

S1: "**① Core7 read miss → Directory**\ndir[X] = {owner: Core2(M)}\ntargeted snoop → Core2" {
  style.fill: "#e8f0fe"
}
S2: "**② Core2 → Core7 data forward**\nCore2: M → S (또는 O)\nCore7: I → S\ndir[X] = {sharers: Core2, Core7}" {
  style.fill: "#e6f4ea"
}
S3: "**③ Core7 write X → Directory**\ndir[X] sharer 목록 = {Core2, Core7}\ntargeted invalidate → Core2 (only)\nCore7: S → M, dir[X] = {owner: Core7(M)}" {
  style.fill: "#fff4e5"
}
S1 -> S2 -> S3
```

### 단계별 의미

| Step | 무엇을 | directory 상태 | snoop 대상 |
|---|---|---|---|
| ① | Core7 read miss | `{owner: Core2}` 조회 | Core2 **only** |
| ② | Core2 데이터 공급 | `{sharers: Core2, Core7}` | — |
| ③ | Core7 write | sharer 목록으로 무효화 | Core2 **only** (나머지 62코어엔 안 보냄) |

③이 핵심입니다. broadcast였다면 write 시 64개 캐시 전부에 무효화를 보냈겠지만, directory는 `{Core2, Core7}`만 sharer임을 알기에 *Core2 하나에만* 무효화를 보냅니다. 코어 수와 무관하게 무효화 트래픽이 *실제 sharer 수*에 비례합니다.

:::note[여기서 잡아야 할 핵심]
directory의 가치는 "정확한 sharer 정보"에서 나옵니다. sharer 목록이 정확하면 targeted snoop으로 트래픽을 sharer 수만큼만 씁니다. 반대로 sharer 정보가 *부정확하면* (예: 이미 evict된 캐시를 sharer로 착각) 불필요한 snoop을 보내거나, 더 위험하게는 *실제 sharer를 빠뜨려* 무효화 누락 → SWMR 위반이 됩니다.
:::
---

## 4. 일반화 — broadcast vs directory, directory 표현 방식

### 4.1 broadcast snooping vs directory

| 축 | Broadcast Snooping | Directory 기반 |
|---|---|---|
| sharer 추적 | 없음 (매번 모두에게 질문) | 중앙 장부에 명시 추적 |
| 트래픽 | O(N) — 코어 수에 비례 | O(실제 sharer 수) |
| 지연 | 낮음 (직접 broadcast) | directory 조회 1단계 추가 |
| 저장 비용 | 없음 | directory 메모리 필요 |
| 확장성 | 소규모(수 코어) | 대규모(수십~수백 코어) |
| 대표 | 초기 SMP 버스 | 현대 SoC LLC/인터커넥트(ACE/CHI) |

### 4.2 directory를 어떻게 저장하나 (sharer 표현)

directory는 line마다 "누가 들고 있나"를 표현해야 하는데, 표현 방식에 따라 저장 비용과 정확도가 달라집니다.

```d2
direction: right

FULL: "**Full bit-vector**\nline당 N비트 (코어 1개=1비트)\n정확하지만 N 커지면 비쌈"
LIMITED: "**Limited pointer**\nsharer 몇 개만 포인터로 저장\n초과 시 broadcast로 fallback"
COARSE: "**Coarse-grained**\n코어 그룹 단위로 추적\n저장 절약, 일부 over-snoop"
```

| 표현 | 저장 비용 | 정확도 | 단점 |
|---|---|---|---|
| Full bit-vector | line당 N비트 | 정확 | N 커지면 비용 폭발 |
| Limited pointer | 적음 | sharer 수 한도 내 정확 | 초과 시 broadcast fallback |
| Coarse-grained | 중간 | 그룹 단위 | over-snoop 발생 |

:::note[directory가 어디에 사나 — in-memory(full-map) vs in-cache(sparse)]
sharer를 *어떻게* 표현하느냐와 별개로, directory를 물리적으로 *어디에 두느냐* 도 핵심 설계 갈림입니다.

- **In-memory directory (고전 full-map):** directory entry를 **메모리 controller 옆**, 즉 모든 DRAM line마다 하나씩 둡니다. 어떤 주소든 그 line의 sharer 정보가 DRAM 영역에 *항상* 존재하므로 누락이 없고 구조가 단순합니다. 그러나 비용이 주소 공간 *전체* 에 비례합니다 — 캐시에 한 번도 올라온 적 없는 line까지 모두 entry를 들고 있어야 하니, 대용량 메모리에서는 directory 저장량이 막대해집니다(line당 N비트 × 전체 DRAM line 수).
- **In-cache / sparse directory (LLC 기반):** 실제로 캐시에 *올라온* line만 추적하면 충분하다는 관찰에서 출발합니다. directory를 **LLC 태그에 붙여**, LLC에 존재하는 line에 대해서만 sharer 정보를 둡니다(§4.3의 inclusive 구현). 저장량이 DRAM 전체가 아니라 *캐시 용량* 에 비례하므로 훨씬 작습니다. 대가는 directory가 LLC처럼 *유한하고 eviction 가능* 한 구조가 된다는 점입니다 — entry가 밀려나면 그 line을 보유한 상위 캐시를 강제로 비워야 하고(back-invalidation, Module 04), 이는 in-memory 방식엔 없던 부담입니다.

요약하면 trade-off는 "전체 주소 공간을 빠짐없이 덮는 대신 비싼" in-memory full-map 과, "캐시에 올라온 것만 싸게 덮되 eviction/back-invalidation을 떠안는" in-cache sparse directory 사이의 선택입니다.
:::

### 4.3 inclusion과 snoop filter

directory를 LLC에 함께 두는 흔한 구현에서는, LLC가 상위 캐시(L1/L2)가 가진 line을 *포함(inclusive)* 하도록 설계해 directory를 LLC 태그에 붙입니다. 이렇게 하면 LLC 조회 = directory 조회가 되어 별도 구조가 줄어듭니다. 단 inclusive 정책은 LLC eviction 시 상위 캐시를 강제로 비우는 **back-invalidation**을 요구하는데, 이는 다음 모듈에서 다룹니다.

### 4.4 directory는 단순 장부가 아니라 per-line ordering point다

Module 02에서 본 공유 버스의 직렬화 지점(ordering point)을 떠올려 봅시다 — 모든 경쟁 트랜잭션이 버스라는 한 점을 통과하며 전역 순서로 줄 섰습니다. directory 구조에서는 그 *버스가 사라집니다*. 그렇다면 두 코어가 같은 line X에 동시에 write를 시도할 때, 누가 먼저인지는 무엇이 정할까요?

답은 **directory(home node)** 입니다. 각 line은 그 주소를 담당하는 단 하나의 home node(보통 그 주소 영역을 관할하는 LLC slice/directory)를 가지며, *그 line에 대한 모든 요청은 반드시 이 home을 거칩니다*. home은 한 line에 대해 들어온 요청들을 한 줄로 받아 *하나씩* 처리합니다 — 먼저 도착한 write를 owner로 확정하고, 그 처리가 끝날 때까지 같은 line의 다음 요청을 직렬화(대기/순서화)합니다. 즉 버스가 *모든 주소* 를 하나의 전역 순서로 묶었다면, directory는 *주소(line)마다 따로* 그 line의 home에서 per-line 순서를 잡습니다.

이 관점이 중요한 이유는, directory를 "누가 갖고 있나를 적어 둔 수동적 장부" 로만 이해하면 race를 놓치기 때문입니다. directory는 *능동적인 serialization 지점* 입니다 — 동시 요청이 경쟁할 때 그 충돌을 풀어 SWMR을 지키는 곳이 바로 home node입니다. 검증에서 directory race(동시 write, write vs eviction, snoop과 요청의 교차)를 짤 때, "이 line의 home이 두 요청을 어떤 순서로 직렬화했는가" 가 expected 결과를 결정합니다.

---

## 5. 디테일 — directory의 정확성과 trade-off

directory의 가장 까다로운 부분은 **sharer 정보의 정확성 유지**입니다. 캐시가 line을 silent하게 evict(상태를 알리지 않고 버림)하면 directory는 그 캐시를 여전히 sharer로 착각합니다. 그러면 다음 write 때 *이미 없는* 캐시에 무효화를 보내는 over-snoop이 발생합니다 — 성능 손해지만 정확성은 유지됩니다. 반대로 directory가 sharer를 *빠뜨리면* 실제 사본이 무효화되지 않아 SWMR이 깨집니다 — 이것이 더 위험한 버그입니다 (추론: silent eviction 처리 정책에 따라 다름).

trade-off의 본질은 "정보를 얼마나 정확히, 얼마의 비용으로 들고 있느냐"입니다. full bit-vector는 정확하지만 코어 수에 비례해 SRAM을 먹고, limited pointer는 싸지만 sharer가 한도를 넘으면 broadcast로 fallback해 일시적으로 snooping의 단점을 되살립니다. coarse-grained는 그룹 단위로 묶어 절약하지만 그룹 내 일부 캐시에 불필요한 snoop이 갑니다. 어떤 표현을 쓰든 *정확성(빠뜨림 없음)* 은 절대 양보할 수 없고, *효율(over-snoop 최소)* 만 trade 대상입니다.

| 정책 이슈 | 효과 | 정확성 영향 |
|---|---|---|
| silent eviction 허용 | directory에 stale sharer 잔존 | over-snoop (성능만 손해) |
| sharer 누락 | 무효화 못 받는 사본 존재 | **SWMR 위반 (정확성 깨짐)** |
| limited pointer overflow | broadcast fallback | 정확 유지, 효율 일시 하락 |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'directory는 snooping보다 항상 빠르다']
**실제**: directory는 *트래픽*을 줄여 대규모에서 확장성을 주지만, 매 접근에 directory 조회 한 단계가 추가되어 *지연*은 늘 수 있습니다. 소규모(수 코어)에서는 broadcast snooping이 더 빠를 수 있습니다.<br>
**왜 헷갈리는가**: "트래픽 감소 = 빠름"으로 단순화. directory는 확장성↔지연의 trade-off.
:::
:::danger[❓ 오해 2 — 'directory가 있으면 broadcast가 절대 안 일어난다']
**실제**: limited pointer directory는 sharer가 한도를 넘으면 *broadcast로 fallback*합니다. directory는 broadcast를 *줄이는* 것이지 항상 없애는 것은 아닙니다.<br>
**왜 헷갈리는가**: "directory = no broadcast"라는 이분법.
:::
:::danger[❓ 오해 3 — 'over-snoop은 correctness 버그다']
**실제**: over-snoop(stale sharer에 보내는 불필요 snoop)은 *성능* 손해일 뿐 정확성은 유지됩니다. 정작 위험한 건 *under-snoop*(실제 sharer 누락) — 이건 SWMR을 깹니다.<br>
**왜 헷갈리는가**: "불필요한 트래픽 = 버그"로 보지만, correctness 관점에서는 누락이 진짜 버그.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 코어 수 늘리니 성능 급락 | broadcast snooping (directory 미사용) 또는 limited pointer overflow 잦음 | snoop 트랜잭션 수 vs sharer 수 비율 |
| write 후 일부 코어만 stale | directory sharer **누락**(under-snoop) → SWMR 위반 | directory sharer 목록 vs 실제 사본 보유 캐시 대조 |
| 불필요한 snoop 다수 | silent eviction으로 stale sharer 잔존 (over-snoop) | eviction 시 directory 갱신 정책 |
| directory full인데 새 line 못 받음 | directory 자체가 캐시처럼 eviction 필요 → back-invalidation 동반 | directory 용량 정책, back-invalidation 동작 |
| limited pointer 시스템에서 간헐 broadcast | sharer 수가 pointer 한도 초과 → fallback | sharer 수 분포, fallback 빈도 |

---

## 7. 핵심 정리 (Key Takeaways)

- **broadcast snooping의 한계**: 코어 수 N에 따라 snoop 트래픽이 O(N)으로 폭발해 대규모에서 인터커넥트 포화.
- **directory(snoop filter)**: "어느 캐시가 어느 line을 들고 있나"를 중앙 장부로 추적 → **targeted snoop**으로 실제 sharer 수만큼만 트래픽 발생.
- **trade-off**: directory는 확장성을 주지만 조회 지연 + 저장 비용이 추가됨. 소규모에선 broadcast가 더 단순/빠를 수 있음.
- **sharer 표현**: full bit-vector(정확/비쌈), limited pointer(싸지만 overflow 시 broadcast fallback), coarse-grained(그룹 단위/over-snoop).
- **정확성 vs 효율**: over-snoop은 성능 손해(허용), **under-snoop(sharer 누락)은 SWMR 위반(절대 금지)**.

:::caution[실무 주의점]
- directory 검증의 1순위는 "sharer 누락이 없는가" — 누락은 silent coherence 버그로 이어진다.
- directory도 유한 구조라 가득 차면 eviction(=상위 캐시 back-invalidation)이 필요 — 다음 모듈에서 다룸.
- limited pointer 시스템은 sharer 수가 한도를 넘는 corner case(broadcast fallback)를 반드시 커버.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — 트래픽 모델 (Bloom: Analyze)]
64코어 중 단 2개만 line X를 공유 중일 때, X에 write가 발생하면 broadcast snooping과 directory 각각 몇 개의 무효화를 보내는가?
<details>
<summary>정답</summary>

broadcast snooping은 sharer 정보가 없으므로 *나머지 모든* 캐시(최대 63개)에 질문/무효화를 broadcast합니다. directory는 sharer 목록 `{2개}`를 알기에 *그 2개에만* targeted invalidate를 보냅니다(write를 하는 자신 제외하면 1개). 즉 directory의 무효화 트래픽은 코어 수가 아니라 *실제 sharer 수*에 비례합니다.
</details>
:::
:::tip[🤔 Q2 — over vs under snoop (Bloom: Evaluate)]
directory가 이미 evict된 캐시를 sharer로 착각하는 경우와, 실제 sharer를 목록에서 빠뜨리는 경우 — 둘 중 어느 것이 correctness 버그인가? 이유는?
<details>
<summary>정답</summary>

*sharer를 빠뜨리는 경우(under-snoop)* 가 correctness 버그입니다. 빠뜨린 캐시는 무효화를 못 받아 stale 사본을 유지 → 다음에 그 캐시가 읽으면 옛 값을 보고, write 중인 코어와 공존해 SWMR을 위반합니다. 반대로 evict된 캐시를 sharer로 착각하는 경우(over-snoop)는 불필요한 snoop을 보낼 뿐 정확성은 유지됩니다 — 성능 손해에 그칩니다.
</details>
:::
### 7.2 출처

**External**
- *A Primer on Memory Consistency and Cache Coherence* — directory coherence 장
- Censier & Feautrier, "A New Solution to Coherence Problems in Multicache Systems" (directory 원전)

---

## 다음 모듈

→ [Module 04 — IO-Coherency & LLC PoC](../04_io_coherency_llc/): DMA/NIC 같은 비캐싱 마스터의 one-way coherency, LLC가 Point of Coherence가 되는 방식, snoop filter + back-invalidation, 그리고 DV가 무엇을 검증해야 하는가.

[퀴즈 풀어보기 →](../quiz/03_directory_scalability_quiz/)
