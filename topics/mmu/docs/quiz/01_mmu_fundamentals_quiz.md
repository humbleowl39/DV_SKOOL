# Quiz — Module 01: MMU Fundamentals

[← Module 01 본문으로 돌아가기](../01_mmu_fundamentals.md)

---

## Q1. (Remember)

VA(가상 주소)가 필요한 이유 3가지를 답하세요.

??? answer "정답 / 해설"
    1. **Process isolation** — 프로세스 간 메모리 격리
    2. **Memory efficiency** — Demand paging, Copy-on-Write 등 lazy 할당
    3. **Fragmentation 해결** — 가상으로 연속이지만 물리는 분산 가능

    VA가 필요한 핵심 이유는 물리 메모리의 한계를 소프트웨어 계층에서 숨기는 데 있습니다. Process isolation이 없으면 프로세스 A가 프로세스 B의 PA에 직접 접근할 수 있어 시스템 보안과 안정성이 붕괴됩니다. Memory efficiency 측면에서는 물리 페이지가 실제로 접근될 때까지 할당을 미룸으로써(demand paging), 대용량 가상 공간을 작은 물리 메모리 위에서 운용할 수 있습니다. Fragmentation 해결은 VA 연속성과 PA 연속성을 분리함으로써 OS가 흩어진 물리 페이지를 하나의 연속 가상 공간으로 제공하게 해 줍니다.

## Q2. (Understand)

CPU MMU와 SoC IOMMU/SMMU의 위치 차이는?

??? answer "정답 / 해설"
    - **CPU MMU**: CPU 코어 내장. CPU가 직접 발행하는 메모리 access만 변환.
    - **IOMMU/SMMU**: SoC-level. CPU 외 모든 device 마스터(GPU/DMA/NIC/가속기)의 메모리 access를 변환.

    CPU MMU는 프로세서 파이프라인의 일부로서 fetch·load·store 명령어가 생성하는 VA를 실시간으로 변환하며, 코어당 하나씩 존재합니다. 반면 IOMMU/SMMU는 SoC 버스 상에 별도 하드웨어 블록으로 존재하며, DMA 컨트롤러나 GPU처럼 CPU 파이프라인을 경유하지 않고 시스템 메모리에 직접 접근하는 디바이스들을 감시합니다. 이 위치 차이가 중요한 이유는, IOMMU 없이는 CPU MMU가 아무리 잘 설정되어 있어도 DMA 마스터가 임의의 PA를 읽고 쓸 수 있어 격리가 무력화되기 때문입니다.

## Q3. (Apply)

MMU enable 순서를 답하세요. 그리고 ISB가 왜 필요한지 설명하세요.

??? answer "정답 / 해설"
    순서: **Page Table 구성 → TTBR 설정 → TCR/MAIR 설정 → SCTLR.M=1 → ISB**.

    ISB 이유: SCTLR.M=1로 MMU enable되면 다음 instruction부터 주소 변환 적용. ISB 없으면 파이프라인의 이전 fetch된 명령어가 untranslated 주소로 실행될 수 있음.

    이 순서가 중요한 이유는 각 단계가 다음 단계의 전제 조건이기 때문입니다. Page table을 먼저 구성하지 않으면 TTBR에 유효하지 않은 base address가 설정되고, TTBR이 확정되기 전에 SCTLR.M을 1로 세우면 MMU가 쓰레기 주소로 walk를 시도합니다. ISB는 파이프라인 내에 이미 fetch된 명령어 스트림을 강제 폐기하고 새 context(MMU enabled)에서 다시 fetch하도록 보장하는 명시적 장벽입니다. ISB 없이는 in-flight 명령어가 MMU enable 이전의 flat mapping으로 실행되어 예측 불가능한 동작이 발생합니다.

## Q4. (Analyze)

PTE의 핵심 필드를 4개 들고 각각의 의미를 답하세요.

??? answer "정답 / 해설"
    - **PFN (Physical Frame Number)**: 매핑되는 물리 페이지 번호
    - **V (Valid)**: 0이면 page fault → OS가 lazy 할당
    - **R/W**: 쓰기 권한
    - **U/S (User/Supervisor)**: privilege 레벨
    - 추가: **ASID** (process tag), **dirty/access** (HW가 자동 set), **NS** (Secure/Non-secure)

    PTE의 각 필드는 서로 독립적인 역할을 수행하며, MMU가 올바른 결정을 내리기 위해 모두 필요합니다. PFN은 "어디로 갈 것인가"를 결정하고, V 비트는 "이 매핑이 현재 유효한가"를 판단합니다. V=0이면 MMU는 page fault 예외를 발생시켜 OS가 페이지를 실제 메모리에 로드할 기회를 주는데, 이것이 demand paging의 핵심 메커니즘입니다. R/W와 U/S는 "누가 어떤 권한으로 접근할 수 있는가"를 제어하며, 이 두 필드가 없으면 사용자 공간 코드가 커널 메모리를 임의로 쓸 수 있게 됩니다.

## Q5. (Evaluate)

다음 중 MMU enable 후 발생할 수 있는 가장 위험한 버그는?

- [ ] A. ISB 누락
- [ ] B. Identity Mapping 누락 (현재 실행 코드 영역)
- [ ] C. TCR 설정 오류
- [ ] D. MAIR 메모리 속성 미설정

??? answer "정답 / 해설"
    **B**. Identity Mapping (VA=PA) 없이 MMU enable하면 다음 instruction의 fetch가 실패 → undefined behavior 또는 즉시 fault. A/C/D도 위험하지만 B는 즉사. 모든 MMU enable 시퀀스의 첫 단계.

    MMU를 enable하는 순간 CPU는 즉시 VA 기반으로 다음 instruction을 fetch하려 합니다. 이때 현재 PC 값(물리 주소)에 해당하는 VA 매핑이 page table에 없으면 fetch 자체가 fault를 유발하므로, 실행이 즉시 멈춥니다. B가 "즉사"인 이유는 이것입니다. 반면 A(ISB 누락)는 파이프라인 race condition이므로 일부 환경에서는 우연히 정상 동작할 수 있고, C(TCR 오류)나 D(MAIR 미설정)는 변환 범위나 메모리 속성이 잘못될 뿐 당장 실행이 멈추지는 않습니다. Identity mapping을 현재 실행 코드 영역에 반드시 설치해야 하는 이유가 여기에 있습니다.
