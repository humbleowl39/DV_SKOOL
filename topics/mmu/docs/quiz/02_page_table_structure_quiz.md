# Quiz — Module 02: Page Table Structure

[← Module 02 본문으로 돌아가기](../02_page_table_structure.md)

---

## Q1. (Remember)

ARMv8 4KB granule의 4-level translation에서 64-bit VA의 비트 분할을 답하세요.

??? answer "정답 / 해설"
    - VA[63:48]: sign-extension (모두 0 또는 모두 1)
    - VA[47:39]: **L0 index** (9 bits)
    - VA[38:30]: **L1 index** (9 bits)
    - VA[29:21]: **L2 index** (9 bits)
    - VA[20:12]: **L3 index** (9 bits)
    - VA[11:0]: **Page offset** (12 bits, 4KB)

## Q2. (Understand)

Single-level page table 대비 Multi-level이 메모리를 절약하는 원리는?

??? answer "정답 / 해설"
    Single-level은 모든 VA에 대해 PTE 슬롯을 미리 할당 → 64-bit VA면 거대한 페이지 테이블 (TB 단위). Multi-level은 사용 중인 영역의 sub-tree만 할당 → unused VA 영역의 메모리 0. Sparse VA 사용 패턴(대부분 프로세스)에서 메모리 절감 1000x+.

## Q3. (Apply)

VA = 0x0000_0000_DEAD_BEEF. ARMv8 4KB granule. 각 level의 index와 page offset을 계산하세요.

??? answer "정답 / 해설"
    - 이진: 0x0000_0000_DEAD_BEEF
    - VA[47:39] = 0 (L0 idx = 0)
    - VA[38:30] = 0b000000011 = 3 (L1 idx = 3)
    - VA[29:21] = 0b011110110 = 246 (L2 idx = 246, 0xF6)
    - VA[20:12] = 0b101011011 = 347 (L3 idx = 347, 0x15B)
    - VA[11:0] = 0xEEF (page offset)

## Q4. (Analyze)

Block Descriptor (Huge page)의 장점과 단점을 답하세요.

??? answer "정답 / 해설"
    **장점**:
    - Walk 깊이 감소 (L1 stop → 1GB page, L2 stop → 2MB page)
    - 동일 VA 범위에 TLB entry 1개로 커버 → TLB 효율 ↑
    - 커널/BSS/대용량 dataset에 유리

    **단점**:
    - 메모리 fragmentation (1GB 단위 contiguous 필요)
    - Permission/속성 변경 시 큰 단위로만 가능
    - copy-on-write 비용 ↑ (큰 페이지 복사)

## Q5. (Evaluate)

Page Walk Cache (PWC)가 가장 효과적인 access pattern은?

- [ ] A. 완전 랜덤한 VA access
- [ ] B. 좁은 VA 범위에서 순차 access
- [ ] C. 다른 process 간 context switch
- [ ] D. TLB invalidation 직후

??? answer "정답 / 해설"
    **B**. 좁은 VA 범위 = 같은 L0/L1 PTE 공유 → PWC hit rate 높음. 순차 access는 인접 페이지 → 하위 레벨 PTE도 가까이 있어 cache 효율 ↑.

    A는 PWC가 거의 도움 안 됨 (각 access가 다른 path). C/D는 invalidation 발생.
