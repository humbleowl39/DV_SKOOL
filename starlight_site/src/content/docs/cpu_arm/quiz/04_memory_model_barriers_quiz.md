---
title: "Quiz — Module 04: 메모리 모델 & 배리어"
---

[← Module 04 본문으로 돌아가기](../../04_memory_model_barriers/)

---

## Q1. (Remember)

세 배리어 `DMB`/`DSB`/`ISB` 의 보장을 옳게 짝지은 것은?

- [ ] A. DMB=파이프라인 flush, DSB=관측 순서, ISB=완료 대기
- [ ] B. DMB=메모리 접근 관측 순서, DSB=메모리 접근 완료 대기, ISB=파이프라인 flush + 재-fetch
- [ ] C. 셋 다 같은 보장
- [ ] D. DMB=완료 대기, DSB=재-fetch, ISB=관측 순서

<details>
<summary>정답 / 해설</summary>

**B**. `DMB` 는 메모리 접근의 *관측 순서* 만 정리하고 완료를 기다리지 않아 가볍습니다. `DSB` 는 메모리 접근이 *완료* 될 때까지 CPU 를 세우므로 비쌉니다. `ISB` 는 파이프라인을 flush 하고 새 컨텍스트로 재-fetch 합니다. A/D 는 셋의 역할을 뒤섞었고, C 는 틀렸습니다. 보장 강도와 비용이 비례합니다.

</details>
## Q2. (Understand)

`LDAR`/`STLR`(acquire/release)가 `DMB` 보다 가벼운 근본 이유는?

- [ ] A. 캐시를 사용하지 않아서
- [ ] B. DMB 는 양방향 순서를 강제하지만 LDAR/STLR 은 한 방향만 막아 CPU/컴파일러가 더 최적화할 수 있어서
- [ ] C. LDAR/STLR 은 메모리를 건드리지 않아서
- [ ] D. DMB 는 EL3 에서만 동작해서

<details>
<summary>정답 / 해설</summary>

**B**. `DMB` 는 앞뒤 양방향 순서를 모두 강제하므로 한쪽만 필요해도 비용을 다 치릅니다. 반면 `STLR`(release)은 *이전* 접근을, `LDAR`(acquire)은 *이후* 접근을 각각 한 방향만 막아 CPU 와 컴파일러가 나머지 방향을 자유롭게 재배치·최적화할 수 있습니다. 그래서 C++ `memory_order_acquire/release` 의 native 매핑이며 단순 핸드오프에서 권장됩니다. A/C/D 는 사실과 다릅니다.

</details>
## Q3. (Apply)

CPU 가 MMIO 레지스터에 DMA START 비트를 쓴 직후, 장치가 그 쓰기를 실제로 받았는지에 다음 동작이 의존한다. 올바른 배리어는?

- [ ] A. `DMB ISH` — 관측 순서만
- [ ] B. `DSB SY` — 쓰기 완료까지 대기
- [ ] C. `ISB` — 파이프라인 재-fetch
- [ ] D. 배리어 불필요

<details>
<summary>정답 / 해설</summary>

**B**. `DMB` 는 순서만 정리할 뿐 *완료를 기다리지 않습니다*. 다음 명령이 장치가 쓰기를 실제로 받았는지에 의존한다면 `DSB`(여기선 외부 장치 대상이라 `SY` scope)로 완료를 기다려야 합니다. A 처럼 DMB 만 쓰면 드물게 race 가 나 디버깅 지옥이 되고, C 는 파이프라인용, D 는 stale/race 버그를 부릅니다.

</details>
## Q4. (Apply)

페이지 테이블 엔트리(PTE)를 바꾼 뒤 모든 코어가 새 매핑을 보게 하려는 표준 시퀀스로 옳은 것은?

- [ ] A. `str pte` 만
- [ ] B. `str pte; dsb ishst; tlbi vae1is; dsb ish; isb`
- [ ] C. `str pte; isb` 만
- [ ] D. `str pte; dmb ish`

<details>
<summary>정답 / 해설</summary>

**B**. 커널 페이지테이블 변경의 표준형은 ① `str` 로 PTE 쓰기 → ② `dsb ishst`(PTE 가 메모리에 보임) → ③ `tlbi vae1is`(inner-shareable TLB invalidate) → ④ `dsb ish`(TLBI 가 모든 코어에서 완료) → ⑤ `isb`(파이프라인이 새 매핑으로 재-fetch)입니다. 한 명령이라도 빠뜨리면 stale TLB 로 잘못된 페이지를 접근합니다. A/C/D 는 모두 단계가 빠져 stale TLB 버그를 일으킵니다.

</details>
## Q5. (Analyze)

어떤 lock-free 코드가 x86 에서는 항상 통과하는데 ARM 에서만 드물게 깨진다. 근본 원인과 검증에서 이 버그를 잡기 위한 모델링 포인트를 분석하라.

<details>
<summary>정답 / 해설</summary>

근본 원인은 **메모리 모델 차이** 입니다. x86 은 TSO 라 store→load 외 재정렬을 막아 store-store 순서가 자동 보장되지만, ARM 은 weakly-ordered 라 load→load, load→store, store→store 까지 재정렬·병합·추측 실행됩니다. x86 의 TSO 에 암묵적으로 의존하던 lock-free 코드(예: 데이터 store 후 ready flag store 의 순서를 가정)는 ARM 에서 두 store 가 재정렬돼 consumer 가 flag 를 먼저 보고 stale data 를 읽는 일이 *드물게* 발생합니다. 대부분의 실행은 우연히 in-order 로 보여 "되는 것처럼" 착각하게 됩니다. 검증 포인트: (1) 공유 변수 핸드오프마다 배리어(DMB ISH 또는 LDAR/STLR) 누락을 검출하는 시나리오, (2) 코어 간 interleaving 을 적극적으로 흔드는 stress 테스트로 희귀 재정렬을 재현, (3) scoreboard 가 단일 program order 가 아닌 *허용되는 관측 순서 집합* 으로 판정하도록 모델링하는 것입니다.

</details>
## Q6. (Evaluate)

"`dsb sy` 는 가장 보수적이니 모든 배리어를 SY 로 통일하면 안전하다" 는 주장을 평가하라.

<details>
<summary>정답 / 해설</summary>

기능적 안전성 면에서는 틀리지 않지만 **성능 면에서 나쁜 판단** 입니다. `dsb sy` 는 모든 관측자(외부 장치·MMIO 포함)에 대한 완료를 기다리는 가장 강하고 가장 느린 배리어입니다. 실제 필요한 범위는 보통 더 좁습니다 — SMP 코어들끼리의 공유 메모리라면 `ISH`(inner shareable)로 충분하고, 자기 코어 한정이면 `NSH` 면 됩니다. 커널 핫패스에서 `SY` 를 남발하면 불필요하게 외부 도메인까지 기다려 처리량이 크게 떨어집니다. 또한 배리어는 scope(SY/ISH/OSH/NSH)와 direction(LD/ST)을 직교로 조합해 차단 범위를 최소화할 수 있으므로(예: producer 는 `dmb ishst`), "관측자 집합이 누구인가" 를 먼저 따져 가장 좁은 옵션을 고르는 것이 옳은 설계입니다. "강할수록 안전" 이라는 직관은 비용을 무시한 과잉 보수입니다.

</details>
