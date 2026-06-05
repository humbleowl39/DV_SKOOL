---
title: "Quiz — 02: Side-effect & 메모리 배리어"
---

[← 02 본문으로 돌아가기](../../02_side_effects_barriers/)

---

## Q1. (Remember)

`wmb()`가 보장하는 것은?

- [ ] A. 배리어 앞의 모든 read가 뒤보다 먼저 완료
- [ ] B. 배리어 앞의 모든 write가 뒤보다 먼저 완료·가시화
- [ ] C. 컴파일러 재정렬만 막음(CPU는 아님)
- [ ] D. 캐시를 비활성화

<details>
<summary>정답 / 해설</summary>

**B**. `wmb()`는 write barrier로, 배리어 이전의 write가 이후 write보다 먼저 완료·가시화되도록 강제합니다. A는 `rmb()`(read barrier), C는 `barrier()`(컴파일러 전용), D는 배리어가 아니라 uncached 매핑(`ioremap`)의 역할입니다.

</details>

## Q2. (Understand)

I/O 레지스터 접근의 "side-effect"가 일반 메모리 접근과 다른 점을 설명하라.

<details>
<summary>정답 / 해설</summary>

일반 메모리는 write의 유일한 효과가 값 저장이고 read는 마지막에 쓴 값을 돌려줄 뿐, 부수 효과가 없습니다. 반면 I/O 레지스터는 read가 비트를 클리어(clear-on-read)하거나 FIFO를 pop하고, write가 디바이스 동작을 트리거하는 등 접근 자체에 부수 효과가 있습니다. 그래서 "값이 같으니 생략", "순서 바꿔도 결과 동일" 같은 컴파일러/CPU 최적화가 I/O에서는 틀린 전제가 됩니다.

</details>

## Q3. (Apply)

디바이스에 디스크립터(DRAM)를 쓴 뒤 도어벨 레지스터에 tail을 써야 한다. 두 write 사이에 무엇을 넣어야 하며 그 이유는?

<details>
<summary>정답 / 해설</summary>

`wmb()`(write barrier)를 넣습니다. 디스크립터 write들이 도어벨 write보다 **먼저** 디바이스에 가시화되도록 강제하기 위함입니다. 이것이 없으면 컴파일러/CPU 재정렬로 도어벨이 먼저 도달해, 디바이스가 아직 유효하지 않은(쓰레기) 디스크립터를 읽어 잘못된 DMA를 일으킵니다. 도어벨은 "준비됐다"는 side-effect 있는 write이므로 순서가 의미를 갖습니다.

</details>

## Q4. (Analyze)

어떤 드라이버가 MMIO를 uncached로 매핑했음에도, 디스크립터 준비와 도어벨 write의 순서가 가끔 뒤집혀 디바이스가 옛 데이터를 읽는다. uncached인데 왜 이런 일이 생기는가?

<details>
<summary>정답 / 해설</summary>

uncached 매핑과 메모리 배리어는 **서로 다른 층위의 문제**를 해결합니다. uncached는 캐싱(stale read, 미도달 write)을 막아 접근이 디바이스에 *닿게* 할 뿐, 두 연산의 *순서*는 보장하지 않습니다. 컴파일러/CPU의 재정렬(store buffer, out-of-order)은 uncached와 무관하게 일어나므로, 순서를 고정하려면 별도로 `wmb()` 같은 배리어가 필요합니다. 즉 이 드라이버는 uncached는 했지만 배리어를 빠뜨린 것입니다.

</details>

## Q5. (Evaluate)

한 동료가 "단일 코어 시스템이니 메모리 배리어는 불필요하다"고 주장한다. 디바이스 드라이버 맥락에서 이 주장을 평가하라.

<details>
<summary>정답 / 해설</summary>

**틀렸습니다.** 단일 코어여도 (1) 컴파일러가 명령을 재정렬하고, (2) CPU의 store buffer/out-of-order 실행으로 디바이스가 관찰하는 store 순서가 소스와 달라질 수 있습니다. 디바이스는 CPU와 별개의 *관찰자*이므로, 같은 코어 하나뿐이어도 디바이스가 두 write의 순서를 봐야 한다면 배리어가 필요합니다. `barrier()`는 컴파일러만 막으므로 디바이스가 끼면 보통 `wmb()`/`rmb()`/`mb()` 같은 CPU 레벨 배리어가 요구됩니다. "멀티코어에서만 배리어"는 흔한 오해입니다.

</details>
