# Quiz — Module 03: Memory Virtualization

[← Module 03 본문으로 돌아가기](../03_memory_virtualization.md)

---

## Q1. (Remember)

VA → IPA → PA 2단계 변환에서 각 단계는 누가 관리하나?

??? answer "정답 / 해설"
    - **Stage 1 (VA → IPA)**: **Guest OS** (자기 페이지 테이블)
    - **Stage 2 (IPA → PA)**: **Hypervisor** (VM 별 페이지 테이블)

## Q2. (Understand)

Shadow Page Table 방식이 EPT/NPT로 대체된 이유는?

??? answer "정답 / 해설"
    Shadow PT는 hypervisor가 VA→PA 직접 매핑하는 별도 PT. Guest가 자기 PT 변경할 때마다 hypervisor sync 필요 → trap 폭증 + 성능 절벽.

    EPT/NPT는 HW가 두 단계 walk를 자동. Guest PT 변경에 hypervisor 개입 불필요. 성능 5-10x 향상.

## Q3. (Apply)

KSM이 메모리 절감하는 원리는?

??? answer "정답 / 해설"
    같은 내용의 메모리 페이지가 여러 VM에 존재 (예: Linux kernel image, libc) → hypervisor가 hash로 detect → COW로 공유. 한 VM이 변경 시도하면 fault → 새 페이지 할당.

    "보일러플레이트" 페이지 deduplication으로 30-50% 메모리 절감 가능.

## Q4. (Analyze)

EPT의 TLB miss penalty가 일반 OS의 TLB miss보다 큰 이유는?

??? answer "정답 / 해설"
    **2단계 walk** 필요. 일반 OS는 1단계 (VA→PA). EPT는 VA→IPA (4 levels) + IPA→PA (4 levels) → 최악 16 access.

    **PWC (Page Walk Cache)**가 효과 큰 이유 — 중간 PTE caching으로 walk 비용 절감.

## Q5. (Evaluate)

Memory ballooning의 trade-off는?

??? answer "정답 / 해설"
    Hypervisor가 guest OS의 메모리를 회수하기 위해 ballooning driver를 통해 guest에게 "메모리를 적게 써달라" 요청. Guest는 internal swap-out 등으로 free 메모리 증가 → hypervisor가 그 페이지 다른 VM에 재할당.

    **장점**: 메모리 over-commit 가능 (1 host가 더 많은 VM)
    **단점**: Guest 성능 저하 가능 (실제 swap 발생 시), guest cooperation 필수
