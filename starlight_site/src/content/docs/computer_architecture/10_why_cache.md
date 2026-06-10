---
title: "Module 10 — 캐시는 왜 존재하는가"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** Memory Wall 의 원인과, 작고 빠른 저장소를 크고 느린 저장소 앞에 두는 메모리 계층의 동기를 설명할 수 있다.
- **Describe** 시간 지역성(temporal locality)과 공간 지역성(spatial locality)이 왜 캐시가 통하는 전제인지 기술할 수 있다.
- **Explain** LLC(공유 L3)가 왜 따로 존재하며 inclusion policy(inclusive/exclusive/NINE)가 무엇을 가르는지 설명할 수 있다.
:::
:::note[사전 지식]
- [Module 02 — 메모리와 레지스터](../02_memory_and_registers/) (주소·저장·레지스터 vs 메모리)
- [Module 06 — Pipeline & Hazard](../06_pipeline_hazard/) (cache miss = stall 원천)
:::

:::note[이 모듈의 위치]
메모리 계층은 분량이 많아 세 모듈로 나눕니다. **M10(지금)** 은 _왜_ 캐시가 필요한지(Memory Wall·지역성·계층), **[M11](../11_cache_organization/)** 은 캐시의 _내부 조직_ 과 miss·write 정책, **[M12](../12_vm_and_dram/)** 는 가상 메모리(TLB)와 DRAM 을 다룹니다.
:::
---

## 1. Why care? — "같은 주소가 왜 빠르기도 느리기도 한가"

캐시를 검증하거나 성능을 분석할 때 가장 먼저 부딪히는 질문은 "왜 같은 주소가 어떤 때는 빠르고 어떤 때는 느린가"입니다. 답은 그 데이터가 _지금 어느 계층에 있느냐_ 에 달렸습니다 — 레지스터·L1 에 있으면 몇 사이클, DRAM 까지 내려가면 100 사이클 이상입니다. 이 100배 가까운 차이를 모르면, 정상적인 cache miss 로 인한 stall 을 설계 버그로 오인하거나, 반대로 prefetcher 가 숨겨 준 latency 를 "원래 빠른 것"으로 착각합니다.

그 근본 원인이 **Memory Wall** — 프로세서 속도와 메모리 속도가 수십 년간 벌어져 온 격차입니다. 이 격차를 메우려고 컴퓨터는 _작고 빠른 저장소를 크고 느린 저장소 앞에 겹겹이_ 쌓습니다. 이 모듈은 그 계층이 왜·어떻게 생겼는지를 세워, 이후 [M11](../11_cache_organization/)의 캐시 내부 동작과 [M12](../12_vm_and_dram/)의 DRAM 비용 구조를 읽을 토대를 만듭니다.

---

## 2. Intuition — 책상·책장·도서관, 과 한 장 그림

:::tip[💡 한 줄 비유]
**메모리 계층** ≈ **책상 → 책장 → 도서관**.<br>
지금 보는 책은 책상 위(L1, 빠르지만 작음)에, 자주 보는 책은 책장(L2/L3)에, 나머지는 도서관(DRAM)에 둔다. 가까울수록 빠르고 작다. 캐시는 "방금 쓴 것/근처의 것을 또 쓸 것"이라는 _지역성(locality)_ 에 베팅한 자동 책상 정리이며, 베팅이 빗나가면 도서관까지 다녀와야 한다(miss).
:::
### 한 장 그림 — 지연/용량의 피라미드

```d2
direction: down

RF: "Register file\n~1 cycle / ~1 KB"
L1: "L1 cache\n~4 cycles / ~32–64 KB"
L2: "L2 cache\n~12 cycles / ~256 KB–1 MB"
L3: "L3 (LLC)\n~40 cycles / ~4–64 MB"
DRAM: "DRAM\n~100+ cycles / GBs"
NVMe: "Storage (NVMe)\n~10 µs / TBs"

RF -> L1 -> L2 -> L3 -> DRAM -> NVMe: "느려지고 커진다"
```

### 두 가지 지역성 — 캐시가 통하는 전제

캐시가 통하는 이유는 프로그램의 접근이 무작위가 아니라 **지역성(locality)** 을 갖기 때문입니다. **시간 지역성(temporal locality)**: 방금 접근한 데이터는 곧 다시 접근될 가능성이 높다(루프 변수, 자주 부르는 함수) — 그래서 한 번 가져온 것을 가까이 붙잡아 둡니다. **공간 지역성(spatial locality)**: 방금 접근한 데이터 _근처_ 가 곧 접근될 가능성이 높다(배열 순회, 코드의 순차 실행) — 그래서 한 바이트가 아니라 _블록(캐시 라인, 보통 64 byte) 단위_ 로 통째로 가져옵니다. 이 두 베팅이 맞아떨어질 때 대부분의 접근이 빠른 상위 계층에서 해결됩니다.

### 왜 계층인가 — Design rationale

프로세서 사이클 시간과 메모리 접근 시간은 1980년대 이후 100–1000× 로 벌어졌습니다(Memory Wall). 단일 메모리로는 빠르거나(작음) 크거나(느림) 둘 중 하나만 가능합니다. 계층은 세 요구의 교집합입니다. 첫째, 대부분의 접근을 빠르게 만들되 전체 용량은 커야 한다 → 빠른 작은 캐시 + 느린 큰 DRAM. 둘째, 프로그램은 시간/공간 지역성을 가지므로 최근/근처 데이터를 가까이 두면 적중률이 높다 → 블록 단위 캐싱. 셋째, 비용을 감당해야 한다 → 비싼 SRAM 은 작게, 싼 DRAM 은 크게. 이 균형이 곧 계층 구조의 디자인 결정입니다.

---

## 3. LLC(L3) 는 왜 생겼고, inclusion policy 가 무엇인가

피라미드 그림의 맨 아래 캐시인 **LLC(Last-Level Cache, 흔히 공유 L3)** 가 따로 존재하는 데는 두 가지 압력이 있습니다. 첫째, **off-chip bandwidth wall** — DRAM 으로 나가는 핀 대역폭은 코어 수만큼 늘릴 수 없으므로, 칩 위에 크고 느린 SRAM 한 층을 더 두어 DRAM 트래픽을 흡수합니다(L1/L2 보다 크지만 DRAM 보다 빠름). 둘째, **코어 간 공유** — 멀티코어가 공유 데이터를 각자의 사설 캐시에만 두면 중복·비효율이 크므로, 모든 코어가 공유하는 한 층(LLC)을 두어 공유 working set 을 한 번만 담고 코어 간 데이터 교환의 접점으로 씁니다.

여기서 갈리는 설계 선택이 **inclusion policy** — LLC 가 상위 캐시(L1/L2)의 내용을 어떻게 포함하느냐입니다.

- **Inclusive**: 상위 캐시에 있는 라인은 _반드시_ LLC 에도 있습니다. coherence 검증이 단순해집니다 — 다른 코어가 어떤 라인을 가졌는지 알려면 LLC 만 보면 되고(snoop filter 역할), LLC 에서 한 라인을 축출하면 상위 캐시에서도 그 라인을 _back-invalidate_ 해야 합니다.
- **Exclusive**: 한 라인은 상위 캐시 _또는_ LLC 중 한 곳에만 있어 중복을 없애 유효 용량을 키웁니다. 대신 라인 추적이 복잡해집니다.
- **NINE(Non-Inclusive Non-Exclusive)**: 둘을 강제하지 않는 중간 정책으로, 상위에 있는 라인이 LLC 에 있을 수도 없을 수도 있습니다.

inclusion policy 의 coherence 함의(왜 inclusive 가 snoop 을 줄이는지, exclusive 가 어떤 추가 추적을 요구하는지)는 깊은 주제이므로 여기서는 "셋이 존재하고 coherence 와 직결된다"까지만 짚고, 전체 treatment 는 [Cache Coherence M04 — I/O coherency & LLC](../../cache_coherence/04_io_coherency_llc/)에서 다룹니다.

---

## 4. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 — '캐시는 크게 만들수록 무조건 빠르다']
**실제**: 캐시를 키우면 더 많은 데이터를 담아 capacity miss 는 줄지만, 더 큰 SRAM 은 _접근 자체가 느려져_ hit time 이 늘고 전력도 늡니다. 그래서 한 칸을 키우는 대신 _계층_ 으로 나눠(빠른 작은 L1 + 느린 큰 L3) 평균 접근 시간을 최적화합니다. "크다 = 빠르다"가 아니라 "가깝다 = 빠르다, 멀다 = 크다"입니다.<br>
**왜 헷갈리는가**: 용량과 속도를 한 축으로 묶어, 둘이 _상충_ 한다는 점을 놓쳐서.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 정상 cache miss stall 을 버그로 신고 | 계층 간 latency 차이(100×)를 미반영 | 기대 AMAT 모델([M11](../11_cache_organization/)) |
| 멀티코어에서 공유 데이터가 비일관 | LLC inclusion/coherence 경계 | inclusion policy, [cache coherence](../../cache_coherence/) |

---

## 5. 핵심 정리 (Key Takeaways)

- **Memory Wall**: 프로세서와 메모리 속도 격차(100–1000×)가 계층의 근본 동기.
- **계층**: register → L1 → L2 → L3 → DRAM → storage. 가까울수록 빠르고 작다.
- **지역성에 베팅**: 시간 지역성(또 쓴다) + 공간 지역성(근처를 쓴다) → 블록 단위 캐싱.
- **LLC(공유 L3)** 는 off-chip bandwidth 흡수 + 코어 간 공유 접점.
- **inclusion policy**(inclusive/exclusive/NINE)가 coherence 추적 방식과 유효 용량을 가른다.

:::caution[실무 주의점]
"크다=빠르다"가 아니라 "가깝다=빠르다". 정상 miss stall 과 버그를 가르려면 먼저 계층별 latency 를 아는 기대 모델([M11](../11_cache_organization/)의 AMAT)을 세운다.
:::
### 5.1 자가 점검

:::tip[🤔 Q1 — 지역성과 블록 (Bloom: Understand)]
캐시가 한 바이트가 아니라 64-byte 블록 단위로 데이터를 가져오는 것은 어느 지역성에 베팅한 것이며, 어떤 접근 패턴에서 이 베팅이 빗나가는가?
<details>
<summary>정답</summary>

블록 단위 전송은 **공간 지역성(spatial locality)** 에 베팅한 것입니다 — 방금 접근한 주소 근처가 곧 접근될 것이라 가정해, 한 바이트만 필요해도 그 주변 64 byte 를 통째로 가져옵니다. 배열 순회·코드의 순차 실행처럼 _인접 주소를 연달아_ 쓰는 패턴에서는 한 번의 fetch 로 여러 접근을 hit 으로 만들어 효율적입니다. 반대로 포인터 추적·해시 테이블·큰 stride 처럼 _접근이 메모리 곳곳에 흩어진_ 패턴에서는, 가져온 블록의 나머지 63 byte 를 거의 쓰지 못해 대역폭만 낭비됩니다(베팅 실패). 이때는 블록을 작게 하거나 다른 자료구조가 답이 됩니다.

</details>
:::
### 5.2 출처

**External**
- Hennessy & Patterson, *Computer Architecture: A Quantitative Approach* — Memory Wall, 메모리 계층, locality
- Patterson & Hennessy, *Computer Organization and Design* — 캐시의 동기

---

## 다음 모듈

→ [Module 11 — 캐시 조직 & miss](../11_cache_organization/): 캐시가 물리 주소를 tag/index/offset 으로 어떻게 쪼개 hit/miss 를 판정하고, 3C miss·write 정책·store buffer·MSHR 이 어떻게 동작하는가.

[퀴즈 풀어보기 →](../quiz/10_why_cache_quiz/)
