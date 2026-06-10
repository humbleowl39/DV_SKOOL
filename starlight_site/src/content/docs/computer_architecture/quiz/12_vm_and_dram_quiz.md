---
title: "Quiz — Module 12: 가상 메모리 & DRAM"
---

[← Module 12 본문으로 돌아가기](../../12_vm_and_dram/)

---

## Q1. (Analyze)

DMA scoreboard 가 "발행 순서와 다른 순서로 DRAM 접근이 일어난다"며 mismatch 를 낸다. 이것이 버그가 아닐 가능성과 올바른 검증 방법을 분석하라.

<details>
<summary>정답 / 해설</summary>

버그가 아닐 가능성이 높습니다. 메모리 컨트롤러는 row hit 을 최대화하려고 같은 DRAM row 를 노리는 요청을 모아 처리하며, 이를 위해 요청 순서를 의도적으로 재정렬합니다 — row hit 은 CAS(CL ~14 ns)만으로 빠르지만 row miss 는 precharge+RAS+CAS 로 ~28–40 ns 가 더 들기 때문입니다. 이는 bandwidth 를 높이는 정상 최적화입니다. 올바른 검증은 (1) scoreboard 비교 기준을 발행 순서가 아니라 주소별 데이터 정확성으로 바꾸고, (2) 같은 주소에 대한 read-after-write 순서 같은 _의미적_ 일관성 제약만 검사하는 것입니다. 이는 OoO 코어(M07)나 AXI OoO scoreboard 와 동일하게 "도착 순서가 아니라 의미로 매칭"하는 원리입니다. 단, 같은 주소의 RAW 순서까지 깨지면 그때는 진짜 버그입니다.

</details>
## Q2. (Understand)

TLB miss 가 발생하면 그 뒤에 무슨 일이 일어나는지 page table walk 와 page fault 를 구분해 설명하라.

<details>
<summary>정답 / 해설</summary>

**TLB miss** 는 "최근 가상→물리 매핑 캐시(TLB)에 해당 페이지의 매핑이 없다"는 뜻이고, 이때 하드웨어 **PTW(Page Table Walker)** 가 메모리에 있는 다단계 페이지 테이블을 순회(**page table walk**)하며 그 페이지의 **PTE(Page Table Entry)** 를 찾아 TLB 에 채웁니다 — 매핑이 메모리에 _존재하는_ 한, 이것은 (느리지만) 하드웨어가 자동으로 끝내는 일입니다. 반면 **page fault** 는 그 PTE 가 _아예 없는_ 경우(해당 페이지가 아직 물리 메모리에 올라와 있지 않음)로, 하드웨어가 OS 커널로 trap 하고 커널이 디스크/swap 에서 페이지를 로드한 뒤 PTE 를 갱신하고 실행을 재개합니다 — 디스크 접근이라 훨씬 비쌉니다. 즉 TLB miss→page walk 는 "캐시에 없지만 표에는 있음", page fault 는 "표에도 없어 OS 개입 필요"의 차이입니다.

</details>
## Q3. (Understand)

L1 캐시가 흔히 VIPT 인 이유와, 그 때문에 L1 용량을 무작정 키우지 못하는 제약을 설명하라.

<details>
<summary>정답 / 해설</summary>

VIPT(Virtually-Indexed, Physically-Tagged)는 _변환되지 않는_ page offset 비트로 set index 를 만들기 때문에, TLB 가 가상→물리 변환을 하는 _동시에_ 같은 사이클에 set 을 고를 수 있습니다 — 변환과 index 가 병렬이라 L1 임계 경로가 짧아져 빠릅니다(PIPT 면 변환이 끝나야 lookup 시작 가능). 제약은 **(way 크기) ≤ (page 크기)** 입니다. index 비트가 전부 page offset(변환 불변 영역) 안에 들어가야 하는데, set 수 × 블록 크기가 한 페이지를 넘으면 index 가 변환되는 상위 비트를 침범합니다. 그러면 같은 물리 주소가 서로 다른 가상 index 로 두 set 에 사본을 만드는 aliasing(synonym)이 생겨 일관성이 깨집니다. 그래서 VIPT L1 은 way 크기를 page 이하로 묶어야 하며, 용량을 키우려면 way 크기 대신 associativity 를 늘립니다.

</details>
