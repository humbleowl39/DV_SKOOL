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

    이 4단계가 MMU의 전체 동작을 요약하며, 단계 간 의존성이 핵심입니다. TLB lookup이 항상 첫 단계인 이유는, walk가 실제로 필요한지 먼저 확인하기 위해서입니다. Walk는 TLB miss라는 조건이 충족될 때만 시작됩니다. Multi-level walk의 결과로 얻은 PA는 TLB에 저장(fill)되므로, 같은 VA의 다음 접근은 walk 없이 1단계에서 바로 해결됩니다. 이 4단계가 반복 접근에서 점점 빨라지는 "self-warming" 특성을 만들어냅니다.

## Q2. (Recall)

TLBI 명령어 3가지 variant와 의미를 한 줄씩 답하세요.

??? answer "정답 / 해설"
    - **TLBI VAE1**: 특정 VA의 entry만 무효화 (가장 좁은 범위)
    - **TLBI ASIDE1**: 특정 ASID의 모든 entry 무효화 (process 단위)
    - **TLBI VMALLE1**: EL1의 모든 TLB entry 무효화 (전체 flush)

    범위가 좁을수록 비용 ↓. 가능한 가장 좁은 variant 사용 권장.

    세 variant의 범위는 "무엇이 변경되었는가"에 따라 선택합니다. 단일 페이지의 PTE만 수정했다면 TLBI VAE1으로 그 VA 하나만 무효화하면 충분하며, 나머지 TLB entry는 유효한 채로 유지됩니다. 프로세스를 종료하거나 ASID를 재사용할 때는 TLBI ASIDE1으로 해당 프로세스의 모든 entry를 한 번에 날립니다. TLBI VMALLE1은 전체 flush이므로 가장 비싸지만, 커널 address space 전체가 바뀌는 경우처럼 어떤 entry가 stale인지 특정할 수 없을 때 사용합니다. 지나치게 넓은 범위를 invalidate하면 불필요한 TLB cold miss가 대규모로 발생합니다.

## Q3. (Apply)

가상화 환경에서 GPU SVM이 동작하는 데 필요한 IOMMU 기능 3가지는?

??? answer "정답 / 해설"
    1. **Stage 1 + Stage 2 translation** — VA → IPA → PA
    2. **ATS** — device-side TLB로 변환 결과 캐싱
    3. **PRI** — device가 page fault 시 OS와 협력해 lazy 페이지 할당

    + (선택) **Process Address Space ID (PASID)** for SubstreamID — 같은 device 내 여러 process 격리.

    가상화 환경에서 GPU SVM이 동작하려면 이 세 가지가 모두 갖춰져야 하는 이유는 각각이 서로 다른 조건을 충족하기 때문입니다. Stage 1+2 translation이 없으면 VM 내 GPU의 VA가 실제 PA에 매핑될 방법이 없으며, 하이퍼바이저가 물리 메모리를 격리할 수 없습니다. ATS 없이는 매 GPU DMA마다 IOMMU를 거쳐야 해 GPU의 메모리 대역폭 이점이 상쇄됩니다. PRI 없이는 GPU가 아직 매핑되지 않은 CPU virtual 페이지에 접근할 때 그 fault를 처리할 방법이 없어 SVM의 "pin 없이 공유"라는 핵심 특성이 깨집니다.

## Q4. (Apply)

TLB hit rate를 높이는 기법 3가지를 들어보세요.

??? answer "정답 / 해설"
    1. **ASID/VMID tagging** — context switch 시 flush 회피
    2. **Huge page** — 같은 메모리를 더 적은 TLB entry로 커버
    3. **TLB hierarchy** — L1 + L2 TLB로 capacity 확보

    추가: PWC로 walk 비용 자체를 절감 (hit rate가 낮아도 miss penalty 감소).

    세 기법은 서로 다른 원인의 TLB miss를 해결합니다. ASID/VMID tagging은 context switch로 인한 cold flush miss를 없애며, 기존 entry를 유지한 채 tag를 비교하는 방식으로 작동합니다. Huge page는 capacity miss를 해결하는데, 동일한 물리 메모리를 더 적은 TLB entry 수로 커버하므로 TLB가 더 많은 유효 주소 범위를 관리할 수 있습니다. TLB hierarchy는 capacity 자체를 늘려, L1에서 miss가 났을 때 L2에서 hit 할 확률을 높입니다. PWC는 이 세 기법과 직교하는 접근으로, miss가 발생하더라도 walk 자체의 latency를 줄입니다.

## Q5. (Evaluate)

다음 중 MMU + 캐시 일관성 시나리오에서 가장 미묘한 함정은?

- [ ] A. TLB hit 시 cache hit
- [ ] B. Aliasing — 같은 PA에 다른 VA mapping 시 cache duplicate
- [ ] C. TLB miss + cache hit
- [ ] D. Cold start

??? answer "정답 / 해설"
    **B**. 두 process가 같은 PA를 다른 VA로 매핑하면 (shared memory), VIVT cache는 두 entry를 갖고 일관성 깨짐. PIPT cache는 PA 기반이라 자동 해결. ARM은 PIPT 사용으로 일반적으로 안전하지만, VIPT cache의 경우 Page Coloring 같은 OS 협력 필요.

    B가 "미묘한 함정"인 이유는 두 process가 모두 자신의 VA→PA 매핑을 정확히 갖고 있어 MMU 관점에서는 이상이 없기 때문입니다. 문제는 cache에서 발생합니다. VIVT(Virtually Indexed, Virtually Tagged) cache는 VA를 key로 data를 저장하므로, 같은 PA라도 VA가 다르면 두 개의 별도 cache entry가 생기고, 한쪽이 수정되면 다른 쪽은 stale 상태가 됩니다. 나머지 오답의 경우 A(TLB hit + cache hit)는 가장 이상적인 정상 경로이고, C(TLB miss + cache hit)는 변환만 느릴 뿐 data 일관성에 문제가 없으며, D(cold start)는 예측 가능한 초기 miss일 뿐입니다.
