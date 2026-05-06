# Quiz — Module 01: MMU Fundamentals

[← Module 01 본문으로 돌아가기](../01_mmu_fundamentals.md)

---

## Q1. (Remember)

VA(가상 주소)가 필요한 이유 3가지를 답하세요.

??? answer "정답 / 해설"
    1. **Process isolation** — 프로세스 간 메모리 격리
    2. **Memory efficiency** — Demand paging, Copy-on-Write 등 lazy 할당
    3. **Fragmentation 해결** — 가상으로 연속이지만 물리는 분산 가능

## Q2. (Understand)

CPU MMU와 SoC IOMMU/SMMU의 위치 차이는?

??? answer "정답 / 해설"
    - **CPU MMU**: CPU 코어 내장. CPU가 직접 발행하는 메모리 access만 변환.
    - **IOMMU/SMMU**: SoC-level. CPU 외 모든 device 마스터(GPU/DMA/NIC/가속기)의 메모리 access를 변환.

## Q3. (Apply)

MMU enable 순서를 답하세요. 그리고 ISB가 왜 필요한지 설명하세요.

??? answer "정답 / 해설"
    순서: **Page Table 구성 → TTBR 설정 → TCR/MAIR 설정 → SCTLR.M=1 → ISB**.

    ISB 이유: SCTLR.M=1로 MMU enable되면 다음 instruction부터 주소 변환 적용. ISB 없으면 파이프라인의 이전 fetch된 명령어가 untranslated 주소로 실행될 수 있음.

## Q4. (Analyze)

PTE의 핵심 필드를 4개 들고 각각의 의미를 답하세요.

??? answer "정답 / 해설"
    - **PFN (Physical Frame Number)**: 매핑되는 물리 페이지 번호
    - **V (Valid)**: 0이면 page fault → OS가 lazy 할당
    - **R/W**: 쓰기 권한
    - **U/S (User/Supervisor)**: privilege 레벨
    - 추가: **ASID** (process tag), **dirty/access** (HW가 자동 set), **NS** (Secure/Non-secure)

## Q5. (Evaluate)

다음 중 MMU enable 후 발생할 수 있는 가장 위험한 버그는?

- [ ] A. ISB 누락
- [ ] B. Identity Mapping 누락 (현재 실행 코드 영역)
- [ ] C. TCR 설정 오류
- [ ] D. MAIR 메모리 속성 미설정

??? answer "정답 / 해설"
    **B**. Identity Mapping (VA=PA) 없이 MMU enable하면 다음 instruction의 fetch가 실패 → undefined behavior 또는 즉시 fault. A/C/D도 위험하지만 B는 즉사. 모든 MMU enable 시퀀스의 첫 단계.
