# Quiz — Module 03: TLB

[← Module 03 본문으로 돌아가기](../03_tlb.md)

---

## Q1. (Remember)

TLB hit과 TLB miss의 latency 차이는 일반적으로 몇 자릿수인가?

??? answer "정답 / 해설"
    - **TLB hit**: 1 cycle
    - **TLB miss + 4-level walk**: 100+ cycle (walk 4번 + cache miss 가능)
    - **차이**: 약 **2 자릿수** (100x).

    이 격차가 TLB hit rate가 IPC를 좌우하는 이유.

## Q2. (Understand)

ASID가 없으면 context switch 시 어떤 문제가 발생하는가?

??? answer "정답 / 해설"
    Context switch마다 TLB 전체 flush 필요 → 새 process의 모든 access가 cold miss → page walk 폭증 → 성능 절벽. ASID로 process tag를 붙이면 TLB entry 공유 가능 → flush 회피.

## Q3. (Apply)

다음 시나리오에서 TLBI가 필요한지 답하세요.

| 시나리오 | TLBI 필요? |
|----------|-----------|
| (a) 새 process를 fork | ? |
| (b) Existing PTE의 R→RW로 권한 변경 | ? |
| (c) TLB hit으로 정상 access 발생 | ? |
| (d) ASID 재사용 (256개 한도 도달 후) | ? |

??? answer "정답 / 해설"
    - (a) **불필요** — 새 ASID 사용하면 기존 TLB entry와 격리
    - (b) **필요** — old PTE가 TLB에 남아있으면 새 권한 미반영. TLBI VA 필요.
    - (c) **불필요** — 정상 동작
    - (d) **필요** — 재사용된 ASID로 매핑된 모든 entry 무효화. TLBI ASID.

## Q4. (Analyze)

TLB shootdown은 왜 비싼가? 어떻게 비용을 줄이는가?

??? answer "정답 / 해설"
    **비싼 이유**: SMP 환경에서 한 코어가 page table을 변경하면 다른 코어들의 TLB도 무효화해야 함. IPI(Inter-Processor Interrupt)로 알림 → 각 코어가 invalidation 수행 → 응답. 동기화 비용 + interrupt overhead.

    **비용 절감**:
    - Batch processing (여러 invalidation을 모아서 한 번에)
    - Per-core ASID로 cross-core invalidation 회피 가능 영역 확대
    - 최근 ARM은 broadcast TLBI (`TLBI ALLE1IS`)로 IPI 없이 일괄 처리

## Q5. (Evaluate)

다음 중 TLB stale entry로 인한 silent bug 발생 가능성이 가장 높은 시나리오는?

- [ ] A. 정상 read access
- [ ] B. Page table 업데이트 후 TLBI 누락
- [ ] C. Context switch 시 ASID 변경
- [ ] D. PWC fill

??? answer "정답 / 해설"
    **B**. PTE를 변경했지만 TLBI를 빠뜨리면 TLB의 old PTE가 그대로 유지 → 잘못된 PA 사용. **silent**한 이유: page fault나 error 발생 안 함. 정상처럼 보이지만 데이터 corruption. 검증에서 가장 catch하기 어려운 종류의 버그.
