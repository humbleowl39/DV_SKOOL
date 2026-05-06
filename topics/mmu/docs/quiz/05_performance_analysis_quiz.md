# Quiz — Module 05: Performance Analysis

[← Module 05 본문으로 돌아가기](../05_performance_analysis.md)

---

## Q1. (Remember)

MMU 성능을 평가하는 3가지 핵심 지표는?

??? answer "정답 / 해설"
    1. **TLB Hit Rate** — TLB hit / total access
    2. **Throughput** — 단위 시간당 변환 수
    3. **Latency** — 단일 access의 지연 (평균 + tail)

    이 셋의 곱이 system effective performance.

## Q2. (Understand)

Dual-Reference Model이 single-reference보다 강력한 이유는?

??? answer "정답 / 해설"
    Single-reference (functional only)는 PA 정확성만 검증. Dual-reference는:
    1. **Functional reference**: 정확한 PA 예측 → 기능 정확성
    2. **Performance reference**: Ideal latency 예측 → 성능 갭 측정

    Performance ratio (DUT / Ideal) > 임계값 시 회귀 즉시 감지. Functional만 보면 PASS인데 성능 25% 저하된 회귀를 놓침.

## Q3. (Apply)

평균 latency = 5 cycle, P99 latency = 80 cycle인 시스템. 다음 중 더 시급한 문제는?

??? answer "정답 / 해설"
    **P99 = 80 cycle이 더 시급**. 평균은 양호해 보이지만 상위 1% access가 극심한 지연 → SLA 위반 원인. 가능한 원인:
    - TLB thrashing (작은 working set + invalidation 패턴)
    - Memory bandwidth contention
    - Page walk이 deep cache miss 동반

    조치: P99 access만 trace해 hotspot 식별 → ASID 격리, TLB size 증가, Huge page 검토.

## Q4. (Analyze)

UVM Performance Monitor가 수집해야 하는 핵심 데이터는?

??? answer "정답 / 해설"
    1. **Per-transaction latency** — histogram + percentile
    2. **Hit source** — micro-TLB / L1 / L2 / Walk (어디서 히트했는지)
    3. **Walk depth** — 4-level / PWC hit / cache miss
    4. **Performance Ratio** — DUT vs Ideal Model
    5. **Throughput** — outstanding transaction 수

    실시간 수집 + 임계값 자동 회귀 검출.

## Q5. (Evaluate)

다음 중 MMU 성능 회귀의 silent killer는?

- [ ] A. TLB miss rate 급증
- [ ] B. P99 latency 50% 증가 (평균은 동일)
- [ ] C. Page fault 다수 발생
- [ ] D. Throughput 감소

??? answer "정답 / 해설"
    **B**. 평균만 모니터링하면 잡을 수 없음. P99 회귀는 SLA 위반의 직접 원인이지만 functional pass 하에 숨음. Dual-Reference Model + tail latency 모니터링이 필수인 이유.

    A/C/D는 보통 functional 또는 throughput 지표에서 catch됨.
