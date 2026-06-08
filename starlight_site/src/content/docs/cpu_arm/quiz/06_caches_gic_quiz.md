---
title: "Quiz — Module 06: Caches & GIC"
---

[← Module 06 본문으로 돌아가기](../../06_caches_gic/)

---

## Q1. (Remember)

GICv3 에서 INTID `0 – 15` 범위에 해당하는 인터럽트 종류는?

- [ ] A. SPI (Shared Peripheral)
- [ ] B. PPI (Private Peripheral)
- [ ] C. SGI (Software Generated)
- [ ] D. LPI (Locality-specific)

<details>
<summary>정답 / 해설</summary>

**C**. SGI (Software Generated Interrupt) 는 INTID 0–15 로, inter-core IPI (코어 간 신호) 에 쓰입니다. PPI(B)는 16–31 의 core-local (예: generic timer), SPI(A)는 32–1019 의 일반 주변장치, LPI(D)는 8192+ 의 MSI(ITS 경유) 입니다.

</details>
## Q2. (Understand)

PoU (Point of Unification) 와 PoC (Point of Coherency) 의 차이를 가장 정확히 설명한 것은?

- [ ] A. PoU 는 DRAM, PoC 는 L1
- [ ] B. PoU 는 한 코어의 I/D 캐시가 같은 데이터를 보는 지점, PoC 는 DMA 등 모든 마스터가 동의하는 지점
- [ ] C. 둘은 같은 의미의 다른 이름
- [ ] D. PoU 는 멀티코어, PoC 는 단일 코어 전용

<details>
<summary>정답 / 해설</summary>

**B**. PoU 는 한 코어의 I-cache 와 D-cache (그리고 그 코어의 TLB walk) 가 같은 데이터를 보는 지점으로 보통 L2 이고, self-modifying code 는 `DC CVAU` (to PoU) 면 충분합니다. PoC 는 DMA 같은 외부 마스터까지 포함한 모든 관측자가 동의하는 지점으로 보통 DRAM 이며, 장치 IO 는 `DC CVAC` (to PoC) 로 끝까지 밀어야 합니다. A 는 둘을 뒤집은 오답, C/D 는 개념을 혼동한 오답입니다.

</details>
## Q3. (Apply)

CPU 가 채운 버퍼를 DMA 엔진으로 보내기 직전, 데이터 정합성을 위해 필요한 CMO 동작은?

- [ ] A. Invalidate (라인을 버림)
- [ ] B. Clean to PoC + DSB (dirty 라인을 DRAM 까지 밀고 완료 대기)
- [ ] C. 아무것도 필요 없음
- [ ] D. I-cache invalidate

<details>
<summary>정답 / 해설</summary>

**B**. DMA-out 에서는 CPU 의 store 가 write-back D-cache 에만 머물 수 있으므로, `DC CVAC` 로 PoC(DRAM)까지 **clean** 한 뒤 `DSB` 로 완료를 기다리고 DMA 를 킥해야 장치가 새 데이터를 봅니다. A(invalidate)는 DMA-in (장치가 채운 뒤 CPU 읽기 전)에 쓰는 동작이고, C 는 stale DRAM 버그를 부르며, D 는 명령 캐시용이라 데이터 DMA 와 무관합니다.

</details>
## Q4. (Apply)

self-modifying code 시퀀스에서 `IC IVAU` (I-cache invalidate) 를 빠뜨리면 어떤 일이 일어나는가?

- [ ] A. D-cache 의 새 명령이 사라진다
- [ ] B. I-cache 에 옛 명령이 남아 fetch 시 옛 코드가 실행된다
- [ ] C. DMA 가 실패한다
- [ ] D. 아무 문제 없다

<details>
<summary>정답 / 해설</summary>

**B**. `DC CVAU` 로 새 명령을 PoU 까지 밀어도, I-cache 에는 여전히 _옛_ 명령 라인이 캐시돼 있습니다. `IC IVAU` 로 그 라인을 invalidate 해야 CPU 가 PoU 에서 새 명령을 다시 fetch 합니다. 이걸 빠뜨리면 fetch 시 옛 명령이 실행됩니다. A 는 clean 의 효과와 무관, C 는 DMA 와 무관, D 는 틀렸습니다. 이어서 `ISB` 로 이미 prefetch 된 옛 명령까지 flush 해야 완전합니다.

</details>
## Q5. (Analyze)

ISR 에서 `ICC_IAR1_EL1` 을 읽어 처리는 했지만 `ICC_EOIR1_EL1` 에 EOI 를 쓰지 않았다. 시스템에 어떤 증상이 나타나는가?

<details>
<summary>정답 / 해설</summary>

`ICC_IAR1_EL1` read 가 인터럽트를 acknowledge 하면서 우선순위를 **running priority** 로 올립니다. `ICC_EOIR1_EL1` 에 EOI 를 써야 그 우선순위가 내려가는데, 이를 빠뜨리면 priority 가 계속 높게 유지되어 **같거나 낮은 우선순위의 후속 인터럽트가 모두 차단**됩니다. 결과적으로 그 우선순위 이하의 인터럽트가 영영 전달되지 않아 타이머·IO 가 멈추고 시스템이 hang 처럼 보입니다. IAR(acknowledge)과 EOIR(완료)은 반드시 짝으로 발행해야 합니다.

</details>
## Q6. (Evaluate)

검증 환경에서 level-triggered 주변장치 인터럽트를 모델링한다. 어떤 모델링 결정이 interrupt storm 을 정확히 재현/검출하는 데 가장 중요한가?

<details>
<summary>정답 / 해설</summary>

**device 의 인터럽트 소스 신호를 handler 의 ack 동작과 연동해 모델링하는 것** 이 핵심입니다. level-triggered 는 신호선이 active level 에 있는 _동안_ 계속 트리거하므로, 검증 모델이 "handler 가 device status 를 clear 할 때만 신호가 내려간다" 를 정확히 반영해야 합니다. 만약 TB 가 인터럽트를 한 번의 펄스로만 모델링하면(edge 처럼) handler 가 ack 를 빠뜨려도 storm 이 재현되지 않아 실제 DUT/펌웨어의 ack 누락 버그를 놓칩니다. 반대로 device ack 와 신호 하강을 충실히 모델링하면, 펌웨어가 ack 를 안 할 때 GIC 가 EOI 후 즉시 재전달하는 storm 을 정확히 검출할 수 있습니다. 따라서 "신호 상태(level)와 ack 의 인과 연결" 을 모델링하는 것이 edge/level 구분보다 우선되는 검증 설계 판단입니다.

</details>
