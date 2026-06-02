---
title: "Quiz — Module 02: Page Table Structure"
---

[← Module 02 본문으로 돌아가기](../../02_page_table_structure/)

---

## Q1. (Remember)

ARMv8 4KB granule의 4-level translation에서 64-bit VA의 비트 분할을 답하세요.

<details>
<summary>정답 / 해설</summary>

- VA[63:48]: sign-extension (모두 0 또는 모두 1)
- VA[47:39]: **L0 index** (9 bits)
- VA[38:30]: **L1 index** (9 bits)
- VA[29:21]: **L2 index** (9 bits)
- VA[20:12]: **L3 index** (9 bits)
- VA[11:0]: **Page offset** (12 bits, 4KB)

이 비트 분할이 4-level walk의 직접적인 근거입니다. 각 level의 index는 9비트이므로 512개(2^9)의 엔트리를 가진 테이블 하나를 인덱싱합니다. 4KB 페이지의 오프셋이 12비트인 이유는 2^12 = 4096이기 때문입니다. 상위 16비트(VA[63:48])는 실제로 사용되지 않지만 sign-extension으로 유효성 검사에 활용되며, 이 값이 모두 0이면 유저 공간(TTBR0_EL1 사용), 모두 1이면 커널 공간(TTBR1_EL1 사용)임을 나타냅니다.

</details>
## Q2. (Understand)

Single-level page table 대비 Multi-level이 메모리를 절약하는 원리는?

<details>
<summary>정답 / 해설</summary>

Single-level은 모든 VA에 대해 PTE 슬롯을 미리 할당 → 64-bit VA면 거대한 페이지 테이블 (TB 단위). Multi-level은 사용 중인 영역의 sub-tree만 할당 → unused VA 영역의 메모리 0. Sparse VA 사용 패턴(대부분 프로세스)에서 메모리 절감 1000x+.

절약이 가능한 이유는 대부분의 프로세스가 VA 공간 전체를 사용하지 않기 때문입니다. 64-bit 주소 공간 전체를 single-level로 커버하려면 이론상 수 TB의 page table이 필요하지만, 실제 프로세스는 텍스트/스택/힙 등 일부 영역만 사용합니다. Multi-level에서는 특정 상위 PTE가 가리키는 하위 테이블이 필요해질 때 비로소 그 테이블을 할당합니다. 사용되지 않는 VA 영역은 상위 레벨 PTE의 valid bit을 0으로 두기만 하면 되므로, 해당 하위 sub-tree 전체를 메모리에서 생략할 수 있습니다.

</details>
## Q3. (Apply)

VA = 0x0000_0000_DEAD_BEEF. ARMv8 4KB granule. 각 level의 index와 page offset을 계산하세요.

<details>
<summary>정답 / 해설</summary>

- 이진: 0x0000_0000_DEAD_BEEF
- VA[47:39] = 0 (L0 idx = 0)
- VA[38:30] = 0b000000011 = 3 (L1 idx = 3)
- VA[29:21] = 0b011110110 = 246 (L2 idx = 246, 0xF6)
- VA[20:12] = 0b101011011 = 347 (L3 idx = 347, 0x15B)
- VA[11:0] = 0xEEF (page offset)

이 계산이 중요한 이유는 Walk Engine이 하드웨어적으로 정확히 이 비트 추출 연산을 수행하기 때문입니다. Walk는 TTBR이 가리키는 L0 테이블을 base로 VA[47:39]를 인덱스로 사용해 L1 테이블 주소를 가져오고, 같은 방식으로 L2, L3까지 내려갑니다. 오프셋(VA[11:0])은 walk와 무관하게 PA에 그대로 더해집니다. 이 예제에서 L0 index가 0이므로 walk의 첫 번째 단계는 L0 테이블의 entry 0을 읽는 것입니다.

</details>
## Q4. (Analyze)

Block Descriptor (Huge page)의 장점과 단점을 답하세요.

<details>
<summary>정답 / 해설</summary>

**장점**:
- Walk 깊이 감소 (L1 stop → 1GB page, L2 stop → 2MB page)
- 동일 VA 범위에 TLB entry 1개로 커버 → TLB 효율 ↑
- 커널/BSS/대용량 dataset에 유리

**단점**:
- 메모리 fragmentation (1GB 단위 contiguous 필요)
- Permission/속성 변경 시 큰 단위로만 가능
- copy-on-write 비용 ↑ (큰 페이지 복사)

장점과 단점이 같은 뿌리에서 나온다는 점이 핵심입니다. 큰 단위로 매핑하기 때문에 TLB 한 entry가 더 넓은 범위를 커버(장점)하지만, 같은 이유로 그 넓은 범위 전체가 물리적으로 연속된 메모리를 요구(단점)합니다. TLB 효율 개선은 특히 HPC나 커널 코드처럼 대규모의 연속 메모리를 반복 접근하는 워크로드에서 두드러집니다. 반면 copy-on-write가 빈번한 fork-heavy 워크로드에서는 작은 페이지가 유리한데, copy-on-write는 쓰기 접근 시 그 페이지만 복사하는 메커니즘이므로 페이지가 클수록 복사 비용이 선형으로 증가하기 때문입니다.

</details>
## Q5. (Evaluate)

Page Walk Cache (PWC)가 가장 효과적인 access pattern은?

- [ ] A. 완전 랜덤한 VA access
- [ ] B. 좁은 VA 범위에서 순차 access
- [ ] C. 다른 process 간 context switch
- [ ] D. TLB invalidation 직후

<details>
<summary>정답 / 해설</summary>

**B**. 좁은 VA 범위 = 같은 L0/L1 PTE 공유 → PWC hit rate 높음. 순차 access는 인접 페이지 → 하위 레벨 PTE도 가까이 있어 cache 효율 ↑.

A는 PWC가 거의 도움 안 됨 (각 access가 다른 path). C/D는 invalidation 발생.

B가 정답인 이유를 구체적으로 설명하면, PWC는 walk 도중 거쳐간 L0/L1/L2 중간 PTE를 캐싱하는 구조이므로, 다음 VA가 같은 상위 테이블 경로를 공유할수록 캐시 적중률이 높아집니다. 좁은 VA 범위의 순차 접근은 L0·L1 PTE가 대부분 동일하므로 매 miss마다 전체 4단계 walk 대신 L2 또는 L3 단 하나만 읽으면 됩니다. A(완전 랜덤)는 VA마다 다른 L0 subtree를 traversal하므로 PWC 적중 기회가 거의 없고, C(context switch)와 D(invalidation 직후)는 PWC 자체가 비워지는 시점이므로 효과를 논할 수 없습니다.

</details>
