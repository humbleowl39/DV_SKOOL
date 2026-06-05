---
title: "Quiz — Module 03: 메인 메모리·Paging·TLB"
---

[← Module 03 본문으로 돌아가기](../../03_memory_paging_tlb/)

---

## Q1. (Remember)

paging 에서 logical address 가 두 부분으로 나뉠 때 그 두 부분은?

- [ ] A. base 와 limit
- [ ] B. page number(p) 와 page offset(d)
- [ ] C. seek 와 rotational
- [ ] D. ASID 와 frame

<details>
<summary>정답 / 해설</summary>

**B**. CPU 가 내는 주소는 **page number `p`** 와 **page offset `d`** 로 나뉩니다(§9.3.1). p 로 page table 을 인덱싱해 frame 번호를 얻고, 그 frame 에 d 를 붙이면 physical address 가 됩니다. A(base/limit)는 contiguous allocation 보호 장치, C(seek/rotational)는 HDD 접근 시간 요소입니다.

</details>
## Q2. (Understand)

paging 이 external fragmentation 을 없애는데도 internal fragmentation 은 남는 이유를 설명하라.

<details>
<summary>정답 / 해설</summary>

paging 은 process 의 page 들을 *아무 빈 frame 에나* 흩어 담으므로(§9.3.1), "총량은 충분한데 연속 자리가 없어 할당 못 하는" external fragmentation 이 사라집니다 — frame 마다 relocation register 를 둔 셈이기 때문입니다. 그러나 process 크기가 page 크기의 정수배가 아니면 *마지막 page* 가 frame 을 다 채우지 못해, 그 frame 안에 남는 공간이 생깁니다 — 이것이 internal fragmentation(평균 half page)입니다. 그래서 큰 버퍼에는 huge page 를 씁니다.

</details>
## Q3. (Apply)

page 크기 4 KB, logical address `0x00002C58` 이 주어졌다. page number 와 offset 을 구하라.

<details>
<summary>정답 / 해설</summary>

4 KB = 2^12 → 하위 12 bit 이 offset.
- offset d = `0x2C58 & 0xFFF` = `0xC58`
- page number p = `0x00002C58 >> 12` = `0x2`
- 즉 p=2, d=0xC58. p 로 page table[2] 를 찾아 frame 번호를 얻고, 거기에 offset `0xC58` 을 그대로 붙입니다 — offset 은 번역되지 않습니다(§9.3.1).

</details>
## Q4. (Apply)

메모리 접근이 10 ns, TLB hit 시 추가 비용 0, miss 시 page table 접근으로 한 번 더 메모리에 가야 한다. TLB hit ratio 가 99% 일 때 실효 접근 시간(EAT)은?

- [ ] A. 약 10.1 ns
- [ ] B. 약 20 ns
- [ ] C. 약 11 ns
- [ ] D. 약 10 ns 정확히

<details>
<summary>정답 / 해설</summary>

**A**. EAT = 0.99 × 10 ns(hit: 한 번 접근) + 0.01 × 20 ns(miss: page table + 실제 = 두 번 접근) = 9.9 + 0.2 = **10.1 ns** (§9.3.2.1). hit 99% 면 1%만 느려집니다. 이 계산은 TLB 가 paging 을 실용적으로 만드는 핵심 — TLB 가 없으면 모든 접근이 20 ns 로 두 배 느려집니다.

</details>
## Q5. (Analyze)

context switch 후 새 process 가 잘못된 frame 을 참조하는 버그가 있다. TLB 관점에서 가능한 원인 두 가지를 분석하라.

<details>
<summary>정답 / 해설</summary>

(§9.3.2.1):
1. **TLB flush 누락**: 이전 process 의 번역이 TLB 에 남아 있는데 비우지 않아, 새 process 가 같은 page number 를 내면 *이전 process 의 frame* 이 hit 됨.
2. **ASID 미태깅/오태깅**: ASID 를 쓰는 시스템에서 entry 에 ASID 가 없거나 잘못 달리면, 여러 process 번역이 섞인 TLB 에서 다른 process 의 entry 를 자기 것으로 hit 함.
- 부차적으로 PTBR(page-table base register)이 새 process 의 page table 로 갱신되지 않았으면 TLB miss 후 walk 도 잘못된 table 을 읽습니다.
- 해법: switch 시 flush 하거나 ASID 를 올바로 태깅하고 PTBR 을 갱신.

</details>
## Q6. (Evaluate)

64-bit 주소공간에서 multi-level(hierarchical) page table 의 한계를 평가하고, sparse 한 대형 주소공간에 더 나은 구조를 제시하라.

<details>
<summary>정답 / 해설</summary>

- **한계**: 64-bit 에서는 page number 비트가 너무 많아 multi-level 의 단계가 깊어집니다(예: UltraSPARC 7단계, §9.4.1). 번역 한 번에 단계 수만큼 메모리 접근이 필요해 비용이 폭증합니다.
- **대안**: **hashed page table**(virtual page number 를 hash, 충돌은 linked list; clustered 변형은 sparse 에 유리) 또는 **inverted page table**(frame 당 entry 1개 `<pid, page#>`, 시스템 전체 1개라 메모리 대폭 절약, 단 virtual 검색용 hash table 곁들임)(§9.4.2–9.4.3).
- 평가: 메모리 사용량과 번역 시간의 trade-off — inverted 는 메모리를 가장 아끼지만 검색 구조가 추가로 필요합니다.

</details>
