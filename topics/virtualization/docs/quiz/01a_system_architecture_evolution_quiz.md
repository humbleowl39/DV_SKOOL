# Quiz — Module 01A: System Architecture Evolution

[← Module 01A 본문으로 돌아가기](../01a_system_architecture_evolution.md)

---

## Q1. (Remember)

시스템 아키텍처 진화의 4가지 milestone은?

??? answer "정답 / 해설"
    1. **고정 기능 HW** (단일 task)
    2. **프로그래머블 CPU** (다양한 SW 실행)
    3. **MMU 도입** (메모리 격리)
    4. **IOMMU + CPU 가상화** (다중 OS 동시 호스팅)

## Q2. (Understand)

MMU 없이 multi-process가 안 되는 이유는?

??? answer "정답 / 해설"
    Process 간 메모리 격리 불가능. 한 process가 다른 process의 메모리를 직접 read/write 가능 → 보안/안정성 모두 깨짐. MMU의 가상 주소 + page table이 process 간 격리의 토대.

## Q3. (Apply)

CPU 가상화 (VT-x) 도입 동기는?

??? answer "정답 / 해설"
    Software-only virtualization (binary translation)는 너무 느림. Multi-tenant cloud의 등장으로 server에서 multiple OS 동시 호스팅 필요 → near-native 성능 + 격리 → HW 지원 필수. Intel VT-x (2005), AMD-V (2006).

## Q4. (Analyze)

각 milestone에서 추가된 HW 메커니즘 vs 해결한 문제?

??? answer "정답 / 해설"
    | Milestone | HW | 해결한 문제 |
    |-----------|-----|------------|
    | CPU + ISA | program counter, register | 프로그램 실행 |
    | Privilege levels | kernel/user mode | OS와 app 분리 |
    | MMU | page table walker, TLB | process 메모리 격리 |
    | IOMMU | SMMU | DMA 격리, device 보호 |
    | VT-x/EL2 | root/non-root mode | multi-OS 동시 호스팅 |

## Q5. (Evaluate)

다음 중 가장 큰 architectural shift는?

- [ ] A. user/kernel mode 분리
- [ ] B. MMU 도입
- [ ] C. CPU 가상화 (VT-x)
- [ ] D. IOMMU 도입

??? answer "정답 / 해설"
    **B (MMU)**. MMU 없이는 modern OS (Linux/Windows) 자체가 불가능. process model의 토대. 다른 milestone은 MMU 위에 add-on. CPU 가상화 (C)도 결국 MMU의 확장 (Stage 2).
