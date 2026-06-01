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

    100배의 차이가 실제로 어디서 오는지 이해하는 것이 중요합니다. 4-level walk는 최소 4번의 메모리 읽기를 요구하는데, 각 읽기가 L1/L2 캐시 미스를 동반하면 DRAM latency(수십 cycle)가 4회 중첩됩니다. TLB hit은 변환 결과를 레지스터 수준의 전용 하드웨어에서 단 1 cycle에 조회합니다. 따라서 TLB hit rate가 99%에서 95%로 낮아지는 것은 "1% 차이"처럼 보이지만, miss penalty가 100배이므로 실효 메모리 접근 지연이 평균적으로 수 배 증가할 수 있습니다.

## Q2. (Understand)

ASID가 없으면 context switch 시 어떤 문제가 발생하는가?

??? answer "정답 / 해설"
    Context switch마다 TLB 전체 flush 필요 → 새 process의 모든 access가 cold miss → page walk 폭증 → 성능 절벽. ASID로 process tag를 붙이면 TLB entry 공유 가능 → flush 회피.

    ASID가 없으면 TLB entry에 "이 변환이 어느 프로세스의 것인가"라는 태그가 없으므로, 다른 프로세스로 전환할 때 이전 프로세스의 모든 TLB entry가 잘못된 PA를 가리킬 수 있습니다. OS는 안전을 위해 전체 TLB를 flush할 수밖에 없고, 새 프로세스의 첫 수백~수천 번의 메모리 접근은 모두 walk를 거쳐야 합니다. ASID를 부여하면 TLB entry에 {ASID, VA}를 함께 저장하므로 프로세스 A와 B의 entry가 TLB 안에 공존 가능하며, switch 시 flush 없이 ASID만 바꾸면 됩니다.

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

    각 시나리오에서 TLBI 필요 여부를 판단하는 기준은 "TLB에 stale entry가 존재할 수 있는가"입니다. (a)에서 fork된 새 프로세스는 새 ASID를 할당받으므로 이전 프로세스의 TLB entry와 tag가 달라 충돌하지 않습니다. (b)는 기존 PTE를 변경하는 상황이므로 TLB에 이미 캐싱된 이전 권한 정보가 남아있을 수 있고, 이것이 새 R/W 권한을 우선합니다. (d)에서 ASID를 재사용하면 새 프로세스와 이전 프로세스가 동일한 ASID tag를 가지므로, 이전 프로세스의 VA→PA 매핑이 새 프로세스에 잘못 적용될 수 있어 반드시 해당 ASID를 먼저 invalidate해야 합니다.

## Q4. (Analyze)

TLB shootdown은 왜 비싼가? 어떻게 비용을 줄이는가?

??? answer "정답 / 해설"
    **비싼 이유**: SMP 환경에서 한 코어가 page table을 변경하면 다른 코어들의 TLB도 무효화해야 함. IPI(Inter-Processor Interrupt)로 알림 → 각 코어가 invalidation 수행 → 응답. 동기화 비용 + interrupt overhead.

    **비용 절감**:
    - Batch processing (여러 invalidation을 모아서 한 번에)
    - Per-core ASID로 cross-core invalidation 회피 가능 영역 확대
    - 최근 ARM은 broadcast TLBI (`TLBI ALLE1IS`)로 IPI 없이 일괄 처리

    TLB shootdown이 비싼 이유를 구체적으로 파악하면, IPI를 받은 각 코어는 현재 실행 중인 작업을 잠시 중단하고 invalidation 루틴을 수행한 후 완료 신호를 보내야 합니다. 코어 수가 많아질수록 이 동기화 비용이 선형 이상으로 증가합니다. ARM의 broadcast TLBI 명령어는 하드웨어 레벨에서 이 신호를 전파하므로 소프트웨어 IPI 왕복 비용을 피할 수 있고, batch 처리는 N번의 개별 shootdown을 1번으로 압축해 interrupt 빈도 자체를 줄입니다.

## Q5. (Evaluate)

다음 중 TLB stale entry로 인한 silent bug 발생 가능성이 가장 높은 시나리오는?

- [ ] A. 정상 read access
- [ ] B. Page table 업데이트 후 TLBI 누락
- [ ] C. Context switch 시 ASID 변경
- [ ] D. PWC fill

??? answer "정답 / 해설"
    **B**. PTE를 변경했지만 TLBI를 빠뜨리면 TLB의 old PTE가 그대로 유지 → 잘못된 PA 사용. **silent**한 이유: page fault나 error 발생 안 함. 정상처럼 보이지만 데이터 corruption. 검증에서 가장 catch하기 어려운 종류의 버그.

    B가 "silent"한 이유는 TLB의 stale entry가 여전히 valid하기 때문입니다. MMU 관점에서 해당 entry는 valid bit가 1인 정상적인 PTE처럼 보이므로 fault를 발생시키지 않고 단지 이전 PA를 사용합니다. 그 PA가 이미 다른 프로세스나 용도로 재할당되었다면 데이터가 조용히 덮어쓰입니다. 나머지 오답의 경우, A(정상 read)는 stale entry가 없는 상황이고, C(ASID 변경 context switch)는 ASID tag가 달라져 충돌이 없으며, D(PWC fill)는 write가 아닌 read 부수효과입니다.
