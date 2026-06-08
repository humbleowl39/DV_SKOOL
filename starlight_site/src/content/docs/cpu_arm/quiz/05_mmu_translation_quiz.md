---
title: "Quiz — Module 05: AArch64 MMU & 주소 변환"
---

[← Module 05 본문으로 돌아가기](../../05_mmu_translation/)

---

## Q1. (Remember)

4KB granule, 48-bit VA 의 AArch64 페이지 테이블 walk 은 몇 레벨인가?

- [ ] A. 2 레벨 (L0, L1)
- [ ] B. 3 레벨 (L1, L2, L3)
- [ ] C. 4 레벨 (L0, L1, L2, L3)
- [ ] D. 5 레벨 (L0 ~ L4)

<details>
<summary>정답 / 해설</summary>

**C**. 4KB granule + 48-bit VA 는 VA 를 9-bit 씩 네 조각(`L0=[47:39], L1=[38:30], L2=[29:21], L3=[20:12]`)과 12-bit offset 으로 자르므로 4-level walk 입니다. B(3 레벨)는 64KB granule 의 구조(L1~L3)이고, A 와 D 는 4KB granule 의 표준이 아닙니다. 참고로 huge page 면 L1/L2 의 block descriptor 에서 walk 이 중간 종료될 수 있습니다.

</details>
## Q2. (Remember)

TLB entry 에 ASID 를 태깅하는 주된 목적은?

- [ ] A. 페이지 크기를 구별하기 위해
- [ ] B. context switch 시 TLB 전체 flush 를 피하기 위해
- [ ] C. cache coherence 를 위해
- [ ] D. write 권한을 확인하기 위해

<details>
<summary>정답 / 해설</summary>

**B**. ASID (Address Space IDentifier) 는 프로세스마다 부여되어 TLB entry 에 함께 저장됩니다. 다른 ASID 의 entry 는 자동으로 매칭되지 않으므로, context switch 시 `TTBR0_EL1` 에 새 ASID 만 바꿔 쓰면 TLB 를 flush 하지 않아도 됩니다. A 는 page size 필드의 역할, C 는 coherence fabric/DVM 의 역할, D 는 PTE 의 `AP` 비트의 역할입니다.

</details>
## Q3. (Apply)

페이지 테이블의 한 PTE 를 바꾼 뒤 멀티코어에서 안전하게 새 매핑을 적용하는 표준 시퀀스 순서는?

- [ ] A. `TLBI → STR → ISB`
- [ ] B. `STR → DSB ISHST → TLBI VAE1IS → DSB ISH → ISB`
- [ ] C. `STR → ISB → TLBI`
- [ ] D. `STR → TLBI → STR`

<details>
<summary>정답 / 해설</summary>

**B**. ① `STR` 로 새 PTE 작성 → ② `DSB ISHST` 로 store 가 메모리에 visible → ③ `TLBI VAE1IS` 로 모든 코어에서 그 VA invalidate → ④ `DSB ISH` 로 invalidate 완료 대기 → ⑤ `ISB` 로 자기 파이프라인 re-fetch. A 는 PTE 를 쓰기 전에 invalidate 해 무의미하고, C 는 invalidate 가 store 뒤에 와도 DSB 가 없어 race, D 는 시퀀스가 아닙니다. ② 가 빠지면 walker 가 옛 PTE 를, ④ 가 빠지면 다른 코어가 stale TLB 를 봅니다.

</details>
## Q4. (Apply)

`VA = 0x0000_0000_0040_2000` (4KB granule, 48-bit) 의 L3 index 는? (`L3 = VA[20:12]`)

- [ ] A. 0
- [ ] B. 2
- [ ] C. 0x40
- [ ] D. 0x402

<details>
<summary>정답 / 해설</summary>

**B**. `0x40_2000` 에서 set 된 비트는 bit 22 (`0x40_0000`) 와 bit 13 (`0x2000`) 입니다. `VA[20:12]` 구간을 보면 bit 13 만 이 범위에 들어가고, bit 13 은 `VA[20:12]` 의 bit 1 위치이므로 **L3 index = 2** 입니다 (`0x2000 >> 12 = 2`). bit 22 는 `VA[29:21]` 구간이므로 L2 index 에 기여합니다(L2 = 2). A 는 offset 만 본 오답, C/D 는 비트 시프트를 안 한 오답입니다.

</details>
## Q5. (Analyze)

가상화 환경에서 같은 단일-stage walk 대비 nested (2-stage) walk 의 PTE fetch 수가 최대 24 까지 폭증하는 이유는?

<details>
<summary>정답 / 해설</summary>

단일 stage 는 `VA → PA` 로 4 PTE fetch (L0~L3) 면 됩니다. 그러나 nested walk 은 `Guest VA → IPA → PA` 의 2단계이고, **stage-1 walk 의 각 PTE 가 IPA 에 위치**합니다. 그 IPA 를 실제 PA 로 풀려면 매번 stage-2 walk (최대 5 PTE fetch) 가 추가로 필요합니다. stage-1 의 5개 단계(L0~L3 의 4 PTE + 마지막 leaf) 각각에 stage-2 walk 가 동반되어 4×5 ≈ 24 PTE fetch 가 됩니다. 그래서 가상화에서는 중간 레벨 PTE 를 캐시하는 **PWC (Page Walk Cache)** 가 사실상 필수이며, PWC miss 시 nested walk latency 가 single 의 5~6배까지 치솟습니다.

</details>
## Q6. (Evaluate)

메모리 컨트롤러를 검증하는 TB 가 페이지 테이블을 직접 갱신한 직후 곧바로 변환 결과를 scoreboard 와 비교하는데, 가끔 mismatch 가 발생한다. 이것을 DUT 버그로 단정하기 전에 무엇을 먼저 검토해야 하는가?

<details>
<summary>정답 / 해설</summary>

**TB 가 PTE 변경 후 TLB invalidate barrier 시퀀스를 넣었는지** 를 먼저 검토해야 합니다. TLB 는 PTE 의 hot cache 이고 페이지 테이블 변경을 자동 추적하지 않으므로, `STR → DSB ISHST → TLBI → DSB ISH → ISB` 시퀀스 없이 곧바로 접근하면 **stale TLB entry** 로 옛 매핑이 적용되어 spurious mismatch 가 생깁니다. 이는 전형적인 TB 버그(자극 측 정합성 결함)이지 DUT 버그가 아닐 가능성이 높습니다. mismatch 가 "가끔" 발생하는 것도 TLB hit/miss 타이밍에 의존하는 race 의 전형적 징후입니다. DUT 버그로 단정하려면 먼저 TB 의 barrier 시퀀스와 `AT` 명령(`PAR_EL1`)으로 변환 경로를 독립 검증해야 합니다.

</details>
