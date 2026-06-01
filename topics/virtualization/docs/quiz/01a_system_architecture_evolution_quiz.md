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

    각 milestone은 이전 단계의 한계를 명확히 인식하고 HW로 해결한 역사입니다. 고정 기능 HW는 한 가지 일밖에 못 하므로 프로그래머블 CPU가 등장했고, 프로그래머블 CPU만으로는 process 간 메모리가 서로 침범해 OS 자체가 안전하지 않았습니다. MMU가 이를 해결하자 이번에는 여러 OS를 동시에 올리고 싶어졌고, 그 결과 CPU 가상화(VT-x/EL2)와 DMA 격리를 위한 IOMMU가 추가되었습니다. 각 단계는 "다음 요구사항을 가능하게 한 토대"임을 기억하세요.

## Q2. (Understand)

MMU 없이 multi-process가 안 되는 이유는?

??? answer "정답 / 해설"
    Process 간 메모리 격리 불가능. 한 process가 다른 process의 메모리를 직접 read/write 가능 → 보안/안정성 모두 깨짐. MMU의 가상 주소 + page table이 process 간 격리의 토대.

    MMU 없이는 모든 process가 물리 주소 공간을 직접 공유합니다. 따라서 버그가 있는 process 하나가 OS 커널 영역이나 다른 process의 데이터를 덮어쓸 수 있고, 이는 시스템 전체 붕괴로 이어집니다. MMU가 각 process에 독립된 가상 주소 공간을 제공하고 page table을 통해 물리 주소로 변환함으로써, process는 자신의 공간만 "볼 수" 있게 됩니다. 현대 OS의 process 모델은 이 MMU 격리 위에서만 성립합니다.

## Q3. (Apply)

CPU 가상화 (VT-x) 도입 동기는?

??? answer "정답 / 해설"
    Software-only virtualization (binary translation)는 너무 느림. Multi-tenant cloud의 등장으로 server에서 multiple OS 동시 호스팅 필요 → near-native 성능 + 격리 → HW 지원 필수. Intel VT-x (2005), AMD-V (2006).

    소프트웨어만으로 가상화를 구현하면 모든 privileged instruction을 인터셉트하고 에뮬레이션해야 하므로 오버헤드가 수십 배에 달했습니다. AWS 같은 클라우드 서비스가 본격화되면서 한 서버에 수십 개의 OS 인스턴스를 near-native 성능으로 실행해야 한다는 요구가 생겼고, 이것이 CPU 제조사들이 VT-x와 AMD-V를 하드웨어에 직접 통합하게 된 직접적 동기입니다. HW 가상화 도입 이후 비로소 퍼블릭 클라우드의 경제성이 현실화되었습니다.

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

    이 표가 보여주는 패턴은 "소프트웨어가 해결하지 못한 문제를 HW 메커니즘이 직접 흡수"하는 반복입니다. Privilege level 없이는 악성 앱이 OS를 덮어쓰고, IOMMU 없이는 passthrough device가 DMA로 hypervisor 메모리를 침범합니다. 각 HW 추가가 어떤 공격 벡터 또는 성능 병목을 없앴는지를 연결해 이해하면, 새로운 HW 기능이 왜 등장했는지를 원리적으로 예측할 수 있습니다.

## Q5. (Evaluate)

다음 중 가장 큰 architectural shift는?

- [ ] A. user/kernel mode 분리
- [ ] B. MMU 도입
- [ ] C. CPU 가상화 (VT-x)
- [ ] D. IOMMU 도입

??? answer "정답 / 해설"
    **B (MMU)**. MMU 없이는 modern OS (Linux/Windows) 자체가 불가능. process model의 토대. 다른 milestone은 MMU 위에 add-on. CPU 가상화 (C)도 결국 MMU의 확장 (Stage 2).

    A의 user/kernel mode 분리도 중요하지만, 이는 CPU 실행 권한만 분리할 뿐 메모리 공간은 여전히 공유됩니다. C의 CPU 가상화(VT-x)는 Stage 2 page table을 통해 실질적으로 MMU 개념을 한 단계 더 확장한 것이고, D의 IOMMU 역시 MMU의 원리를 device DMA에 적용한 파생 기술입니다. 따라서 MMU는 이후 모든 격리 메커니즘의 근본 아이디어이며, MMU가 없었다면 나머지 milestone도 존재하지 않았을 것입니다.
