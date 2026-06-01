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

    세 지표가 독립적으로 중요한 이유를 각각 이해해야 합니다. TLB hit rate는 "얼마나 자주 느린 경로(page walk)를 피했는가"를 나타내며, 이것이 낮으면 나머지 지표가 아무리 좋아도 전체 성능이 walk latency에 지배됩니다. Throughput은 병렬 트랜잭션 처리 능력을 나타내며, MMU가 파이프라인 병목이 되는지를 측정합니다. Latency, 특히 tail latency(P99)는 SLA 위반의 직접 원인이 되므로 평균만 보면 놓치는 outlier를 식별합니다. 세 지표를 함께 모니터링해야 한 지표가 좋아 보여도 다른 지표에서 회귀가 숨어 있는 상황을 방지합니다.

## Q2. (Understand)

Dual-Reference Model이 single-reference보다 강력한 이유는?

??? answer "정답 / 해설"
    Single-reference (functional only)는 PA 정확성만 검증. Dual-reference는:
    1. **Functional reference**: 정확한 PA 예측 → 기능 정확성
    2. **Performance reference**: Ideal latency 예측 → 성능 갭 측정

    Performance ratio (DUT / Ideal) > 임계값 시 회귀 즉시 감지. Functional만 보면 PASS인데 성능 25% 저하된 회귀를 놓침.

    Single-reference 모델의 맹점은 "PA가 맞으면 통과"라는 이분법적 판단에 있습니다. PA 정확성은 유지되면서 latency만 나빠지는 버그(예: TLB hit인데 추가 pipeline stage가 삽입됨)는 scoreboard 불일치를 발생시키지 않아 완전히 통과합니다. Dual-reference 모델은 두 번째 reference인 Ideal 모델을 통해 "이 트랜잭션은 이론적으로 N cycle에 완료되어야 한다"는 기준을 제공하고, DUT의 실제 latency와 비율을 비교함으로써 기능은 맞지만 성능이 열화된 회귀를 자동으로 포착합니다.

## Q3. (Apply)

평균 latency = 5 cycle, P99 latency = 80 cycle인 시스템. 다음 중 더 시급한 문제는?

??? answer "정답 / 해설"
    **P99 = 80 cycle이 더 시급**. 평균은 양호해 보이지만 상위 1% access가 극심한 지연 → SLA 위반 원인. 가능한 원인:
    - TLB thrashing (작은 working set + invalidation 패턴)
    - Memory bandwidth contention
    - Page walk이 deep cache miss 동반

    조치: P99 access만 trace해 hotspot 식별 → ASID 격리, TLB size 증가, Huge page 검토.

    P99가 더 시급한 이유는 SLA 위반이 평균이 아니라 꼬리(tail) 분포에서 발생하기 때문입니다. 평균 5 cycle은 95% 이상의 트랜잭션이 매우 빠름을 의미하지만, 1%의 트랜잭션이 80 cycle에 묶여 있다면 이 트랜잭션들이 전체 파이프라인을 블록할 수 있습니다. 특히 스트리밍이나 실시간 처리 워크로드에서는 단 한 개의 느린 트랜잭션이 뒤에 대기 중인 수십 개의 정상 트랜잭션을 지연시킵니다. 평균만 보고 문제없다고 판단하는 것은 빙산의 수면 위 부분만 보는 것과 같습니다.

## Q4. (Analyze)

UVM Performance Monitor가 수집해야 하는 핵심 데이터는?

??? answer "정답 / 해설"
    1. **Per-transaction latency** — histogram + percentile
    2. **Hit source** — micro-TLB / L1 / L2 / Walk (어디서 히트했는지)
    3. **Walk depth** — 4-level / PWC hit / cache miss
    4. **Performance Ratio** — DUT vs Ideal Model
    5. **Throughput** — outstanding transaction 수

    실시간 수집 + 임계값 자동 회귀 검출.

    각 항목이 독립적인 진단 가치를 가집니다. Per-transaction latency histogram은 성능 분포의 전체 모양을 보여주므로, 단순 평균이 숨기는 bimodal 분포(대부분 빠른데 일부가 극단적으로 느린 패턴)를 드러냅니다. Hit source 분류는 "왜 느린가"의 원인을 계층별로 분리합니다. Walk depth는 PWC가 실제로 효과를 발휘하는지 확인하는 직접 증거입니다. Performance Ratio는 회귀 감지의 자동화를 가능하게 합니다. Throughput은 MMU가 파이프라인 병목인지 여부를 판별합니다.

## Q5. (Evaluate)

다음 중 MMU 성능 회귀의 silent killer는?

- [ ] A. TLB miss rate 급증
- [ ] B. P99 latency 50% 증가 (평균은 동일)
- [ ] C. Page fault 다수 발생
- [ ] D. Throughput 감소

??? answer "정답 / 해설"
    **B**. 평균만 모니터링하면 잡을 수 없음. P99 회귀는 SLA 위반의 직접 원인이지만 functional pass 하에 숨음. Dual-Reference Model + tail latency 모니터링이 필수인 이유.

    A/C/D는 보통 functional 또는 throughput 지표에서 catch됨.

    B가 "silent killer"인 이유는 평균 latency가 동일한 상태에서 P99만 50% 증가하는 회귀는 scoreboard 불일치도, TLB miss rate 이상도, throughput 저하도 일으키지 않을 수 있기 때문입니다. 전통적인 functional regression suite는 이를 전혀 감지하지 못합니다. 반면 A(TLB miss rate 급증)는 hit rate counter로, C(page fault 다수)는 fault handler 진입 횟수로, D(throughput 감소)는 transaction rate 모니터로 각각 직접 측정 가능합니다. P99 회귀만이 tail latency histogram 또는 Dual-Reference Model의 percentile 비교로만 탐지됩니다.
