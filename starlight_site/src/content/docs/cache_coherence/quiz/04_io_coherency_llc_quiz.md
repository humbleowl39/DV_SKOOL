---
title: "Quiz — Module 04: IO-Coherency & LLC PoC"
---

[← Module 04 본문으로 돌아가기](../../04_io_coherency_llc/)

---

## Q1. (Remember)

IO-Coherency가 NIC/DMA 같은 비캐싱 마스터 통합에 주는 직접적 이점은?

- [ ] A. 디바이스에 큰 캐시를 추가해 성능을 높인다
- [ ] B. 드라이버가 cache flush/clean을 직접 관리하지 않아도 된다
- [ ] C. 메모리 용량을 두 배로 늘린다
- [ ] D. 인터럽트 지연을 제거한다

<details>
<summary>정답 / 해설</summary>

**B**. IO-coherent 포트에 연결된 NIC가 메모리를 read하면 인터커넥트가 자동으로 CPU 캐시를 snoop해, CPU가 dirty 최신본을 들고 있으면 그것을 끌어와 전달합니다. 그 결과 소프트웨어 엔지니어는 디바이스 드라이버에서 cache maintenance(flush/clean)를 더 이상 관리할 필요가 없어 드라이버 코드가 단순해지고 성능도 좋아집니다.

</details>
## Q2. (Understand)

inclusive LLC에서 **back-invalidation**이 왜 필요한지 설명하라.

<details>
<summary>정답 / 해설</summary>

strictly inclusive 정책에서는 상위 L1/L2에 있는 line이 반드시 LLC에도 존재해야 합니다. LLC가 가득 차 victim line을 evict해야 할 때, 그 line이 상위 캐시에도 있다면 LLC가 그냥 버릴 수 없습니다 — 버리면 상위 캐시에 LLC가 추적 못 하는 orphan(고아) line이 남기 때문입니다. 그래서 LLC는 상위 L1/L2에 **back-invalidation** 명령을 보내 해당 사본을 함께 버리게 합니다(dirty면 write-back 동반). 이로써 inclusion invariant와 수직 coherence가 유지됩니다.

</details>
## Q3. (Apply)

IO-coherent DMA가 주소 X를 read하는데, 그 순간 CPU가 X를 dirty(M)로 보유 중이다. 데이터가 DMA에 전달되기까지의 경로를 단계로 기술하라.

<details>
<summary>정답 / 해설</summary>

① DMA read @X가 인터커넥트의 IO-coherent 포트로 진입합니다. ② 인터커넥트가 Point of Coherence(보통 LLC) directory를 조회해 X의 owner가 CPU(dirty)임을 확인합니다. ③ 인터커넥트가 CPU 캐시를 snoop해 dirty 데이터를 추출하고, stale한 DRAM을 *우회*합니다. ④ 최신 X를 DMA로 전달합니다. 드라이버는 사전에 cache flush를 할 필요가 없습니다.

</details>
## Q4. (Analyze)

IO-Coherency가 *one-way*인 이유를 비캐싱 마스터의 특성으로 분석하라.

- [ ] A. 디바이스가 느려서 단방향만 가능
- [ ] B. 디바이스에 캐시가 없어 남이 디바이스를 snoop할 필요가 없으므로
- [ ] C. 인터커넥트 대역폭 절약을 위해 임의로 제한
- [ ] D. 보안상 디바이스→CPU 접근을 막기 위해

<details>
<summary>정답 / 해설</summary>

**B**. NIC/DMA는 비캐싱 마스터로 자체 캐시가 없습니다. 따라서 다른 마스터가 *디바이스의 사본을 찾으러 snoop할* 일이 없습니다 — 디바이스는 데이터를 보유하지 않으니까요. 필요한 보장은 단 하나, 디바이스가 메모리를 접근할 때 CPU 캐시의 최신 dirty본을 반영하는 것뿐입니다. 그래서 snoop은 CPU 방향으로만 흐르는 one-way가 됩니다.

</details>
## Q5. (Evaluate)

inclusive LLC를 검증할 때 back-invalidation 체커를 빠뜨리면 어떤 버그가 silent하게 통과하며, 왜 특히 디버그가 어려운가?

<details>
<summary>정답 / 해설</summary>

LLC가 victim line을 evict하면서 상위 L1/L2 사본을 무효화하지 않으면 **orphan line**(LLC가 추적 못 하는 상위 사본)이 생깁니다. 이 line은 directory에서 빠져 이후 그 주소에 대한 무효화/공급이 누락되어 SWMR이 깨집니다. 디버그가 어려운 이유는 *eviction이 일어난 시점*과 *coherence 버그가 증상으로 터지는 시점*이 시간적으로 멀리 떨어져 있어, 증상 지점만 봐서는 과거의 eviction이 원인임을 찾기 어렵기 때문입니다. 그래서 eviction 경로 자체를 별도 체커로 상시 감시해야 합니다.

</details>
