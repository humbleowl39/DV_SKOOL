# Quiz — Module 07: MMU Quick Reference

[← Module 07 본문으로 돌아가기](../07_quick_reference_card.md)

---

## Q1. (Recall)

VA → PA 변환의 표준 절차를 4단계로 답하세요.

??? answer "정답 / 해설"
    1. **TLB lookup** — hit이면 즉시 PA 반환 (1 cycle)
    2. **TLB miss → Page Walk 시작** — Walk Engine 활성화
    3. **Multi-level walk** — L0→L1→L2→L3 (4KB granule)로 PTE traverse
    4. **TLB fill + PA 반환** — 결과를 TLB에 저장 후 access 진행

## Q2. (Recall)

TLBI 명령어 3가지 variant와 의미를 한 줄씩 답하세요.

??? answer "정답 / 해설"
    - **TLBI VAE1**: 특정 VA의 entry만 무효화 (가장 좁은 범위)
    - **TLBI ASIDE1**: 특정 ASID의 모든 entry 무효화 (process 단위)
    - **TLBI VMALLE1**: EL1의 모든 TLB entry 무효화 (전체 flush)

    범위가 좁을수록 비용 ↓. 가능한 가장 좁은 variant 사용 권장.

## Q3. (Apply)

가상화 환경에서 GPU SVM이 동작하는 데 필요한 IOMMU 기능 3가지는?

??? answer "정답 / 해설"
    1. **Stage 1 + Stage 2 translation** — VA → IPA → PA
    2. **ATS** — device-side TLB로 변환 결과 캐싱
    3. **PRI** — device가 page fault 시 OS와 협력해 lazy 페이지 할당

    + (선택) **Process Address Space ID (PASID)** for SubstreamID — 같은 device 내 여러 process 격리.

## Q4. (Apply)

TLB hit rate를 높이는 기법 3가지를 들어보세요.

??? answer "정답 / 해설"
    1. **ASID/VMID tagging** — context switch 시 flush 회피
    2. **Huge page** — 같은 메모리를 더 적은 TLB entry로 커버
    3. **TLB hierarchy** — L1 + L2 TLB로 capacity 확보

    추가: PWC로 walk 비용 자체를 절감 (hit rate가 낮아도 miss penalty 감소).

## Q5. (Evaluate)

다음 중 MMU + 캐시 일관성 시나리오에서 가장 미묘한 함정은?

- [ ] A. TLB hit 시 cache hit
- [ ] B. Aliasing — 같은 PA에 다른 VA mapping 시 cache duplicate
- [ ] C. TLB miss + cache hit
- [ ] D. Cold start

??? answer "정답 / 해설"
    **B**. 두 process가 같은 PA를 다른 VA로 매핑하면 (shared memory), VIVT cache는 두 entry를 갖고 일관성 깨짐. PIPT cache는 PA 기반이라 자동 해결. ARM은 PIPT 사용으로 일반적으로 안전하지만, VIPT cache의 경우 Page Coloring 같은 OS 협력 필요.
