# Quiz — Module 03: Memory Virtualization

[← Module 03 본문으로 돌아가기](../03_memory_virtualization.md)

---

## Q1. (Remember)

VA → IPA → PA 2단계 변환에서 각 단계는 누가 관리하나?

??? answer "정답 / 해설"
    - **Stage 1 (VA → IPA)**: **Guest OS** (자기 페이지 테이블)
    - **Stage 2 (IPA → PA)**: **Hypervisor** (VM 별 페이지 테이블)

    이 2단계 분리의 의미는 guest OS와 hypervisor가 서로의 내부를 모르면서도 각자의 주소 공간을 독립적으로 관리할 수 있다는 것입니다. Guest OS는 자신이 "실제 물리 메모리를 직접 관리한다"고 믿으며 Stage 1을 유지하지만, 실제로 guest가 "물리 주소"라고 생각하는 IPA는 hypervisor가 관리하는 Stage 2 테이블을 거쳐 진짜 PA로 변환됩니다. 어느 한 단계라도 빠지면 guest가 다른 VM의 물리 메모리에 접근할 수 있게 됩니다.

## Q2. (Understand)

Shadow Page Table 방식이 EPT/NPT로 대체된 이유는?

??? answer "정답 / 해설"
    Shadow PT는 hypervisor가 VA→PA 직접 매핑하는 별도 PT. Guest가 자기 PT 변경할 때마다 hypervisor sync 필요 → trap 폭증 + 성능 절벽.

    EPT/NPT는 HW가 두 단계 walk를 자동. Guest PT 변경에 hypervisor 개입 불필요. 성능 5-10x 향상.

    Shadow PT의 근본 문제는 "guest의 모든 page table 변경을 hypervisor가 실시간으로 추적해야 한다"는 것입니다. 메모리 집약적 워크로드는 page table을 빈번하게 갱신하므로 trap이 폭발적으로 늘어나 성능 절벽을 만듭니다. EPT/NPT는 이 추적 부담을 없애는 대신 TLB miss 시 walk 길이를 2배로 늘리는 트레이드오프를 선택했습니다. 결과적으로 TLB hit율이 높은 일반 워크로드에서는 EPT/NPT가 압도적으로 빠르지만, TLB miss가 잦은 일부 워크로드에서는 walk 비용이 부각될 수 있습니다.

## Q3. (Apply)

KSM이 메모리 절감하는 원리는?

??? answer "정답 / 해설"
    같은 내용의 메모리 페이지가 여러 VM에 존재 (예: Linux kernel image, libc) → hypervisor가 hash로 detect → COW로 공유. 한 VM이 변경 시도하면 fault → 새 페이지 할당.

    "보일러플레이트" 페이지 deduplication으로 30-50% 메모리 절감 가능.

    KSM이 효과적인 이유는 같은 Linux 배포판을 실행하는 수십 개의 VM이 커널 이미지, C 라이브러리 같은 read-only 페이지를 그대로 복사해 보유하기 때문입니다. KSM은 이런 동일 내용 페이지들을 하나의 물리 페이지로 합치고, 각 VM의 page table은 그 공유 페이지를 가리키도록 조용히 업데이트합니다. Copy-on-Write(COW) 덕분에 VM 중 하나가 해당 페이지를 수정하려 하면 즉시 새 물리 페이지를 할당받아 쓰기를 수행하므로, 다른 VM의 데이터가 영향을 받지 않습니다.

## Q4. (Analyze)

EPT의 TLB miss penalty가 일반 OS의 TLB miss보다 큰 이유는?

??? answer "정답 / 해설"
    **2단계 walk** 필요. 일반 OS는 1단계 (VA→PA). EPT는 VA→IPA (4 levels) + IPA→PA (4 levels) → 최악 16 access.

    **PWC (Page Walk Cache)**가 효과 큰 이유 — 중간 PTE caching으로 walk 비용 절감.

    일반 OS에서 TLB miss가 나면 HW page table walker가 4단계 page directory를 순차 접근해 PA를 찾습니다. EPT 환경에서는 이 4단계 중 각 단계마다 Stage 2 변환이 추가로 필요하므로, 최악의 경우 (4 Stage-1 levels) × (4 Stage-2 levels) = 최대 16번의 메모리 접근이 발생합니다. PWC는 이 중간 PTE 계산 결과를 캐싱해 재사용하므로 실제 평균 walk 비용을 크게 줄여줍니다. TLB miss가 상대적으로 드문 일반 워크로드에서 EPT가 여전히 실용적인 것은 PWC가 이 오버헤드를 흡수하기 때문입니다.

## Q5. (Evaluate)

Memory ballooning의 trade-off는?

??? answer "정답 / 해설"
    Hypervisor가 guest OS의 메모리를 회수하기 위해 ballooning driver를 통해 guest에게 "메모리를 적게 써달라" 요청. Guest는 internal swap-out 등으로 free 메모리 증가 → hypervisor가 그 페이지 다른 VM에 재할당.

    **장점**: 메모리 over-commit 가능 (1 host가 더 많은 VM)
    **단점**: Guest 성능 저하 가능 (실제 swap 발생 시), guest cooperation 필수

    Memory ballooning의 핵심은 hypervisor가 guest의 메모리를 강제로 빼앗는 대신 guest 내부에 설치된 balloon driver를 통해 "협상"하는 방식이라는 점입니다. Balloon driver가 메모리 할당을 팽창(inflate)시켜 guest 내부에서 압박을 만들면, guest OS의 자체 메모리 관리자가 덜 중요한 페이지를 swap out하거나 해제해 버립니다. Hypervisor는 이렇게 해제된 물리 페이지를 회수해 다른 VM에게 줄 수 있습니다. 단점은 guest가 ballooning driver를 설치하고 실행 중이어야 하며, 극단적으로 메모리가 압박되면 guest 자체의 성능이 저하될 수 있다는 것입니다.
