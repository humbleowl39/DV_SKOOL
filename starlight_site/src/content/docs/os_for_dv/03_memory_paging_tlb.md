---
title: "Module 03 — 메인 메모리 · Paging · TLB"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** address binding 의 세 시점(compile/load/execution time)과 logical vs physical 주소가 갈리는 이유를 설명할 수 있다.
- **Trace** CPU 가 낸 logical address 가 page number/offset 으로 분할되어 page table·TLB 를 거쳐 physical address 가 되는 경로를 추적할 수 있다.
- **Differentiate** external vs internal fragmentation, 그리고 contiguous allocation 의 한계와 paging 의 해결책을 구분할 수 있다.
- **Explain** TLB 가 왜 필요하고 ASID 가 context switch 비용을 어떻게 줄이는지 설명할 수 있다.
- **Evaluate** hit ratio 가 실효 접근 시간에 미치는 영향을 계산하고, multi-level/hashed/inverted page table 의 trade-off 를 평가할 수 있다.
:::
:::note[사전 지식]
- [Module 01](../01_os_overview/) — privileged instruction(base/limit register 변경)
- [Module 02](../02_process_scheduling/) — PCB 가 담는 memory-management 정보(base/limit·page table)
- 2진수·2의 거듭제곱, bit 분할
- (출처) Silberschatz, *Operating System Concepts* 10th ed., Ch.9
:::
---

## 1. Why care? — 우리가 검증하는 MMU/IOMMU 가 바로 이 번역기다

검증 엔지니어가 MMU 나 IOMMU 를 다룰 때, 그 핵심은 *주소 번역*입니다. CPU(또는 device)가 낸 logical/virtual address 를 page table 을 거쳐 physical address 로 바꾸고, 그 과정에서 protection bit 으로 접근을 보호하는 일이죠. 이 모듈에서 다루는 page/frame·page table·TLB·protection bit 은 정확히 우리가 RTL 로 검증하는 MMU 의 구성요소입니다.

DMA 가 어느 주소를 쓰는지(physical 인가 virtual 인가)도 이 모듈의 logical/physical 구분 위에서만 정확히 이해됩니다(M04 에서 이어짐). 주소 번역 경로를 손으로 그릴 수 있으면, MMU/IOMMU 검증에서 "TLB miss 시 page table walk 가 맞게 일어났는가", "valid-invalid bit 위반이 trap 되는가" 같은 체크포인트가 명확해집니다.

---

## 2. Intuition — 한 줄 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**Paging** ≈ **큰 책을 아무 빈 사물함에나 페이지 단위로 흩어 보관하기**.<br>
책(process)의 페이지(page)들이 연속된 사물함에 있을 필요가 없습니다. "이 페이지는 몇 번 사물함"을 적은 색인(page table)만 있으면 흩어져 있어도 찾을 수 있죠. TLB 는 "최근에 찾은 색인 몇 개"를 손에 들고 있는 메모지입니다.
:::
### 한 장 그림 — logical address 가 physical 로 번역되는 경로

```d2
direction: right

CPU: "CPU\nlogical address\n[ p | d ]"
TLB: "**TLB**\n(작고 빠른 cache)\nhit → frame 즉시"
PT: "**Page Table**\n(메모리, PTBR 가 가리킴)\np → frame#"
PHY: "Physical Memory\n[ frame# | d ]"

CPU -> TLB: "page number p"
TLB -> PHY: "hit: frame#"
TLB -> PT: "miss"
PT -> PHY: "frame#"
CPU -> PHY: "offset d (그대로)"
```

### 왜 이 디자인인가 — Design rationale

여러 process 를 동시에 메모리에 올리려면 서로의 영역을 침범하지 못하게 막아야 하고(보호), 물리 메모리가 작아도 큰 논리 주소공간을 줘야 하며(추상화), 빈 공간이 조각나도 할당이 가능해야 합니다(fragmentation 해결). contiguous allocation 은 이 셋을 다 만족하지 못해 external fragmentation 에 시달립니다. **paging** 은 process 의 물리 주소를 *연속이 아니게* 허용해 이 문제를 풉니다 — 그 대가가 page table 과, 그것을 빠르게 만드는 TLB 입니다.

---

## 3. 작은 예 — logical 주소 한 개가 physical 로 번역되는 과정

page 크기가 2의 거듭제곱이라, 논리 주소공간이 2^m, page 가 2^n 이면 상위 m−n bit 이 page number `p`, 하위 n bit 이 page offset `d` 로 깔끔히 갈립니다(Ch.9.3.1).

### 단계별 다이어그램

```d2
direction: down

A: "① CPU: logical address\n상위 m−n bit = p, 하위 n bit = d"
B: "② TLB 조회 (p)\nhit? → frame# 즉시"
C: "③ TLB miss → page table[p]\n(메모리 접근 1회 추가)"
D: "④ frame# 확보\n+ protection bit / valid-invalid 체크"
E: "⑤ physical address = frame# : d\n결과를 TLB 에 채움"

A -> B
B -> D: "hit"
B -> C: "miss"
C -> D
D -> E
```

### 단계별 의미

| Step | 무엇이 | 무엇을 | 왜 |
|---|---|---|---|
| ① | CPU | 주소를 p/d 로 분할 | page 크기가 2^n 이라 bit 경계로 분리 (Ch.9.3.1) |
| ② | TLB | p 로 frame# 조회 | pipeline 안 조회라 사실상 추가 비용 없음 (Ch.9.3.2.1) |
| ③ | (miss 시) page table | PTBR 기준 page table[p] 읽기 | 메모리 접근 1회 추가 → 느려짐 |
| ④ | MMU | protection bit(R/W/X) + valid-invalid 체크 | 위반은 OS 로 trap (Ch.9.3.3) |
| ⑤ | MMU | frame# 에 d 붙여 physical 완성 + TLB 채움 | 다음 번 hit 을 위해 |

:::note[여기서 잡아야 할 두 가지]
**(1) offset d 는 번역되지 않고 그대로 간다.** page 안의 위치는 frame 안의 같은 위치이므로, 번역되는 것은 page number p → frame number 뿐입니다.<br>
**(2) 보호는 page table 에서 한다.** frame 마다 read-only/read-write/execute 를 정하는 **protection bit** 과, 그 page 가 합법 영역인지 표시하는 **valid-invalid bit** 으로(Ch.9.3.3). DV 관점에서 이 두 bit 의 위반 trap 이 MMU 검증의 핵심 체크포인트입니다.
:::
---

## 4. 일반화 — binding · fragmentation · paging

### 4.1 Address binding 의 세 시점 (Ch.9.1.2)

| 시점 | 무엇 | 특징 |
|------|------|------|
| **Compile time** | 적재 위치를 미리 알면 absolute code | 위치 바뀌면 재컴파일 |
| **Load time** | 위치 모르면 relocatable code, 적재 시 최종 주소 결정 | — |
| **Execution time** | 실행 중 process 이동 가능 | binding 을 런타임까지 미룸, 특별 하드웨어(MMU) 필요. **현대 OS 대부분** |

그래서 CPU 가 내는 주소(**logical address**, 실행 시점 binding 에서는 **virtual address**)와 메모리가 보는 주소(**physical address**)가 갈립니다. 둘을 런타임에 잇는 하드웨어가 **MMU(memory-management unit)** 입니다(Ch.9.1.3). 가장 단순한 MMU 는 base register 를 **relocation register** 로 삼아 user 주소에 그 값을 더합니다 — relocation register 가 14000 이면 logical 0 → physical 14000, logical 346 → 14346.

보호의 가장 단순한 장치는 **base register + limit register** 한 쌍입니다(Ch.9.1.1). base 가 300040, limit 이 120900 이면 process 는 300040~420939 만 접근 가능하고, 벗어나면 OS 로 trap 합니다. 이 두 register 는 privileged instruction 으로 kernel mode 에서만 바꿀 수 있어(M01 연결), user 가 제 울타리를 넓힐 수 없습니다.

### 4.2 Fragmentation: contiguous allocation 의 한계 (Ch.9.2)

```d2
direction: right
EXT: "**External fragmentation**\n총량은 충분한데\n연속 자리가 없어 할당 불가\n(50-percent rule: ~1/3 손실)"
INT: "**Internal fragmentation**\n고정 블록 할당 시\n블록 안에 남는 공간"
```

contiguous allocation 은 빈 공간(**hole**)에 process 를 채울 때 first fit / best fit / worst fit 전략을 쓰지만(Ch.9.2.2), process 가 들고 나기를 반복하면 빈 공간이 조각나는 **external fragmentation** 에 시달립니다(50-percent rule: 메모리의 약 1/3 이 못 쓰게 될 수 있음, Ch.9.2.3). compaction 은 비싸고 execution-time relocation 일 때만 가능합니다. 더 나은 해법이 paging 입니다.

### 4.3 Paging: 흩어 담기 (Ch.9.3.1)

paging 은 물리 메모리를 고정 크기 **frame** 으로, 논리 메모리를 같은 크기 **page** 로 쪼개, process 의 page 들을 아무 빈 frame 에나 흩어 담습니다. 덕분에 logical address space 가 physical 과 완전히 분리됩니다. paging 은 곧 frame 마다 relocation register 를 둔 셈이라 external fragmentation 이 없지만, 마지막 frame 이 다 안 차는 **internal fragmentation**(평균 half page)은 남습니다 — 그래서 큰 버퍼에는 **huge page**(예: x86-64 의 4 KB·2 MB)를 씁니다. page table 은 process 마다 따로라 context switch 비용을 늘립니다(M02 연결).

---

## 5. 디테일 — TLB · hit ratio · page table 구조

### 5.1 TLB — 두 번 접근 문제의 해법 (Ch.9.3.2)

page table 은 너무 커서(수십만~수백만 entry) 메모리에 두고 **PTBR(page-table base register)** 가 위치를 가리킵니다. 그런데 이러면 한 번의 메모리 접근마다 page table 을 읽느라 접근이 *두 번*씩 들어 느려집니다. 이를 막는 것이 **TLB(translation look-aside buffer)** — 최근 번역을 담는 작고 빠른 associative cache(보통 32~1,024 entry)로, instruction pipeline 안에서 조회돼 사실상 추가 비용이 없습니다(Ch.9.3.2.1).

각 entry 에 **ASID(address-space identifier)** 를 달면 여러 process 의 번역을 섞어 두고도 context switch 마다 TLB 를 비우지 않아도 됩니다. DV 관점에서 ASID 태깅과 flush 동작이 MMU 검증의 중요한 corner case 입니다.

### 5.2 Hit ratio 와 실효 접근 시간 (Ch.9.3.2.1)

hit 비율이 성능을 좌우합니다. 메모리 접근이 10 ns 일 때:

```
hit 99% → 실효 접근 시간 ≈ 10.1 ns (1%만 느려짐)
  = 0.99 × 10 ns (TLB hit, 한 번 접근)
  + 0.01 × 20 ns (miss, page table + 실제 = 두 번 접근)
```

이 계산은 cache hit ratio 분석과 동형이라, 컴퓨터 구조에서 본 적 있을 것입니다.

### 5.3 Page table 자체를 어떻게 담나 (Ch.9.4)

주소공간이 커지면 page table 자체가 거대해집니다(32-bit·4 KB page → entry 100만 개 초과, process 당 4 MB).

| 구조 | 방법 | 적합/한계 |
|------|------|----------|
| **Hierarchical (multi-level)** | page table 을 또 paging, p 를 p1/p2 로 분할 | 32-bit two-level OK; 64-bit 은 단계 너무 깊음(UltraSPARC 7단계) |
| **Hashed** | virtual page number 를 hash, 충돌은 linked list | clustered 변형은 sparse 주소공간에 유리 |
| **Inverted** | frame 마다 entry 하나(`<pid, page#>`) | 시스템 전체 1개라 메모리 절약, 검색 위해 hash table 곁들임 |

### 5.4 메모리가 모자랄 때: Swapping (Ch.9.5)

process 나 그 일부를 잠시 **backing store**(보조 저장장치)로 내보냈다(**swap out**) 다시 들이는(**swap in**) 것이 **swapping** 입니다. 통째로 옮기는 standard swapping 은 비싸서 요즘은 **swapping with paging**(page out/in)을 씁니다(Ch.9.5.2). mobile 시스템은 flash 수명·용량 때문에 대개 swapping 을 지원하지 않고, 메모리가 부족하면 앱에 반납을 요청하거나 종료합니다(Ch.9.5.3). backing store 가 바로 M04 의 저장장치입니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'logical address 와 physical address 는 보통 같다']
**실제**: execution-time binding(현대 OS 대부분)에서는 MMU 가 매 참조마다 번역하므로 둘이 *다릅니다*(Ch.9.1.3). 같아 보이는 건 relocation register 가 0 인 특수 경우뿐.<br>
**왜 헷갈리는가**: 디버거가 보여주는 주소가 일관돼 보여서 — 실제론 process 별 virtual 공간.
:::
:::danger[❓ 오해 2 — 'paging 은 fragmentation 을 완전히 없앤다']
**실제**: paging 은 *external* fragmentation 을 없애지만, 마지막 frame 이 다 안 차는 **internal** fragmentation(평균 half page)은 남습니다(Ch.9.3.1).<br>
**왜 헷갈리는가**: "frame 에 흩어 담으니 빈틈 없음"으로 단순화해서.
:::
:::danger[❓ 오해 3 — 'TLB 는 그냥 있으면 좋은 캐시일 뿐 필수는 아니다']
**실제**: TLB 가 없으면 *모든* 메모리 접근이 page table 때문에 두 배 느려집니다(Ch.9.3.2). hit ratio 가 곧 시스템 성능 — TLB 는 paging 을 실용적으로 만드는 핵심입니다.<br>
**왜 헷갈리는가**: "cache 는 옵션"이라는 일반 인상 때문 — 여기선 사실상 필수.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 번역 결과 frame 은 맞는데 offset 이 틀림 | offset d 를 잘못 번역/마스킹 | p/d bit 분할 경계, page 크기 정렬 |
| context switch 후 잘못된 process 의 frame 참조 | ASID 미태깅 또는 TLB flush 누락 | TLB entry 의 ASID, switch 시 flush 정책 |
| read-only page 에 write 가 통과됨 | protection bit 체크 누락 | page table entry 의 R/W/X bit, trap 경로 |
| 합법 영역 밖 접근이 trap 안 됨 | valid-invalid bit / limit 체크 누락 | valid bit, base/limit 비교 로직 |
| TLB miss 후 page table walk 가 잘못된 PTBR 사용 | PTBR 업데이트 타이밍 | context switch 시 PTBR 로드 순서 |

---

## 7. 핵심 정리 (Key Takeaways)

- **logical ≠ physical (execution-time binding).** MMU 가 매 참조마다 번역하며, 가장 단순한 MMU 는 relocation register 로 base 를 더한다.
- **base/limit register 가 가장 단순한 보호**, paging 의 protection bit/valid-invalid bit 이 그 일반화. 둘 다 위반은 OS 로 trap.
- **paging = 흩어 담기.** external fragmentation 제거(대신 internal half-page 남음). logical address = [p|d], p 로 page table 인덱싱.
- **TLB 가 paging 을 실용적으로 만든다.** 두 번 접근 문제를 hit 으로 회피, ASID 로 context switch 시 flush 회피. hit ratio 가 실효 접근 시간을 좌우.
- **page table 도 쪼갠다** — multi-level(32-bit), hashed(sparse), inverted(메모리 절약). swapping 은 page 단위로 backing store 와 주고받는다.

:::caution[실무 주의점]
- MMU/IOMMU 검증에서 protection bit·valid-invalid bit 위반의 trap 경로를 반드시 직접 테스트하세요 — silent pass 가 보안 구멍입니다.
- ASID 태깅·TLB flush 는 context switch corner case 의 단골 버그 지점입니다.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — 번역 경로 추적 (Bloom: Trace)]
page 크기 4 KB, logical address `0x00003ABC` 가 주어졌다. page number 와 offset 을 구하고, TLB miss 라면 physical address 가 만들어지기까지의 접근 횟수는?
<details>
<summary>정답</summary>

4 KB = 2^12 → offset 은 하위 12 bit.
- offset d = `0x3ABC & 0xFFF` = `0xABC`
- page number p = `0x00003ABC >> 12` = `0x3`
- TLB miss → page table[3] 읽기(메모리 접근 1회) → frame# 확보 → 실제 데이터 접근(1회) = **총 2회** 메모리 접근(Ch.9.3.2). TLB hit 이었다면 1회.
- offset `0xABC` 는 번역 없이 frame# 뒤에 그대로 붙는다.

</details>
:::
:::tip[🤔 Q2 — page table 구조 선택 (Bloom: Evaluate)]
64-bit 주소공간에서 hierarchical(multi-level) page table 이 부적합한 이유와, sparse 하게 쓰이는 큰 주소공간에 어떤 구조가 나은가?
<details>
<summary>정답</summary>

- **부적합 이유**: 64-bit 에서는 page number bit 이 너무 많아 multi-level 의 단계가 깊어진다(예: UltraSPARC 7단계, Ch.9.4.1). 단계마다 메모리 접근이 늘어 번역 비용이 폭증.
- **대안**: **hashed page table**(virtual page number 를 hash, 충돌은 linked list)이나 **inverted page table**(frame 당 entry 1개, 시스템 전체 1개)이 sparse·대형 주소공간에 유리(Ch.9.4.2–9.4.3). inverted 는 메모리를 크게 아끼지만 virtual 주소 검색을 위해 hash table 을 곁들여야 한다.
- trade-off: 메모리 사용량 vs 검색/번역 시간.

</details>
:::
### 7.2 출처

**Internal (HDG)**
- `os_main_memory_spec.md` — address binding, MMU/relocation, fragmentation, paging, TLB/ASID, page table 구조, swapping (Ch.9 정독 요약)
- `os_concepts_guide.md` — 시리즈 2번 "어디서 도는가"

**External**
- Silberschatz et al. *Operating System Concepts*, 10th ed. — **Ch.9 Main Memory**(§9.1 binding/MMU, §9.2 fragmentation, §9.3 paging/TLB, §9.4 page table 구조, §9.5 swapping)

---

## 다음 모듈

→ [Module 04 — Mass Storage · I/O 시스템 · DMA](../04_storage_io_dma/): 메모리 밖 영속 저장(HDD/SSD/FTL)과, CPU 가 device 와 데이터를 주고받는 네 방법(MMIO·polling·interrupt·DMA) — 우리 testbench 가 직접 자극·관찰하는 메커니즘.

[퀴즈 풀어보기 →](../quiz/03_memory_paging_tlb_quiz/)
