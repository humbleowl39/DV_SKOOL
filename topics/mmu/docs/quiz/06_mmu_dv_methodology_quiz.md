# Quiz — Module 06: MMU DV Methodology

[← Module 06 본문으로 돌아가기](../06_mmu_dv_methodology.md)

---

## Q1. (Remember)

MMU 검증의 3가지 검증 축은?

??? answer "정답 / 해설"
    1. **기능 정확성** — VA→PA 변환의 정확성
    2. **성능** — TLB Hit Rate, Throughput, Latency
    3. **프로토콜** — AXI / AXI-S 핸드셰이크 준수

    단일 축만 검증하면 silent bug 발생.

## Q2. (Understand)

상용 VIP 대신 Custom Thin VIP를 만든 가장 큰 동기는?

??? answer "정답 / 해설"
    **메모리 제약**. 상용 VIP는 모든 PTE를 dense array로 보관 → 대용량 page table (GB 규모)에서 시뮬 OOM. Custom Thin VIP는 **sparse 표현 (associative array)**과 **on-demand allocation**으로 100x 메모리 절감. SoC-level 시뮬에서 필수.

## Q3. (Apply)

SVA bind로 적용할 MMU 검증 카테고리 3가지를 들고 각각 cover와의 짝을 설명하세요.

??? answer "정답 / 해설"
    1. **TLB 동작**: assert "Hit 시 1-cycle 응답", cover "TLB Hit 발생"
    2. **Page Walk**: assert "Miss 후 walk 시작 + walk 완료 후 TLB fill", cover "Walk 발생", "Walk depth = 4"
    3. **프로토콜**: assert "valid-ready 핸드셰이크", cover "Stall 발생", "Fault 응답 발생"

    모든 assert에 짝지은 cover로 Vacuous Pass 방지.

## Q4. (Analyze)

Constrained Random sequence에서 VA 분포를 Hotspot 60% / 일반 30% / 넓은 범위 10%로 한 이유는?

??? answer "정답 / 해설"
    실제 워크로드의 VA 분포 모사:
    - **Hotspot 60%**: 대부분의 access는 좁은 영역 (cache locality) → TLB hit pattern 검증
    - **일반 30%**: 보통의 다양성 → 일반 case
    - **넓은 범위 10%**: TLB capacity miss / PWC 효과 검증

    100% 균등 분포는 비현실적이고 corner case 도달 어려움. 실제 트래픽 패턴 + targeted scenario의 균형.

## Q5. (Evaluate)

다음 시나리오 중 MMU 검증에서 가장 catch하기 어려운 silent bug는?

- [ ] A. PA 계산 오류 (잘못된 비트 분할)
- [ ] B. TLB invalidation 후 stale entry 잔존
- [ ] C. Permission check 누락
- [ ] D. Walk depth 5 (4-level인데 5번 walk)

??? answer "정답 / 해설"
    **B**. 다음 access에서 잘못된 PA 사용하지만 fault나 error 발생 안 함 → 데이터 corruption만 silent하게 발생. 다른 옵션:
    - A: scoreboard에서 즉시 mismatch
    - C: permission fault assert로 catch
    - D: walk count counter assertion으로 catch

    B는 invalidation 시점 검증 cover가 있어야만 catch 가능 → SVA bind 패턴의 가치를 보여주는 케이스.
