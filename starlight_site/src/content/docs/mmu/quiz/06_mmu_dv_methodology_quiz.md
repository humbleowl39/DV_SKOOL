---
title: "Quiz — Module 06: MMU DV Methodology"
---

[← Module 06 본문으로 돌아가기](../../06_mmu_dv_methodology/)

---

## Q1. (Remember)

MMU 검증의 3가지 검증 축은?

<details>
<summary>정답 / 해설</summary>

1. **기능 정확성** — VA→PA 변환의 정확성
2. **성능** — TLB Hit Rate, Throughput, Latency
3. **프로토콜** — AXI / AXI-S 핸드셰이크 준수

단일 축만 검증하면 silent bug 발생.

세 축이 왜 동시에 필요한지는 각 축이 서로 독립된 실패 모드를 커버하기 때문입니다. 기능 정확성만 검증하면 PA가 맞아도 latency 회귀를 놓칩니다. 성능만 측정하면 PA가 틀린데 빠른 경우를 감지하지 못합니다. 프로토콜만 확인하면 핸드셰이크가 맞아도 PA가 잘못 계산될 수 있습니다. 세 축이 같은 트랜잭션을 다른 관점에서 동시에 검사함으로써, 어느 한 축에서 살아남은 버그가 다른 축에서 걸리는 방어 계층이 형성됩니다.

</details>
## Q2. (Understand)

상용 VIP 대신 Custom Thin VIP를 만든 가장 큰 동기는?

<details>
<summary>정답 / 해설</summary>

**메모리 제약**. 상용 VIP는 모든 PTE를 dense array로 보관 → 대용량 page table (GB 규모)에서 시뮬 OOM. Custom Thin VIP는 **sparse 표현 (associative array)**과 **on-demand allocation**으로 100x 메모리 절감. SoC-level 시뮬에서 필수.

상용 VIP의 dense array 방식이 문제가 되는 이유는, 64-bit VA 공간의 모든 가능한 VA에 대한 PTE 슬롯을 미리 확보하면 시뮬레이터 메모리가 실제 테스트하는 주소 수와 무관하게 폭발적으로 증가하기 때문입니다. Sparse 표현은 실제로 매핑된 VA에 대해서만 PTE 객체를 생성하고 나머지는 null로 처리하므로, 프로세스가 수백 개의 페이지만 사용한다면 수백 개의 객체만 메모리에 존재합니다. 이 차이가 SoC-level 시뮬에서 OOM 회피의 핵심이며, 시뮬레이터가 감당할 수 있는 페이지 테이블 규모를 수십~수백 배 확장합니다.

</details>
## Q3. (Apply)

SVA bind로 적용할 MMU 검증 카테고리 3가지를 들고 각각 cover와의 짝을 설명하세요.

<details>
<summary>정답 / 해설</summary>

1. **TLB 동작**: assert "Hit 시 1-cycle 응답", cover "TLB Hit 발생"
2. **Page Walk**: assert "Miss 후 walk 시작 + walk 완료 후 TLB fill", cover "Walk 발생", "Walk depth = 4"
3. **프로토콜**: assert "valid-ready 핸드셰이크", cover "Stall 발생", "Fault 응답 발생"

모든 assert에 짝지은 cover로 Vacuous Pass 방지.

assert와 cover를 반드시 짝지어야 하는 이유는 Vacuous Pass 때문입니다. assertion만 있고 cover가 없으면, 해당 assertion이 한 번도 체크될 기회가 없어도 시뮬레이션이 통과됩니다. 예를 들어 "TLB hit 시 1-cycle 응답" assertion에 "TLB Hit 발생" cover가 없으면, 시뮬 전체에서 TLB hit이 한 번도 일어나지 않았는데 assertion이 통과됩니다. cover가 achieved되어야 해당 assertion이 실제로 검증되었음을 보장합니다. Walk depth cover는 특히 중요한데, 항상 L1이나 L2에서 walk를 멈추는 huge page만 사용된 경우 4-level full walk assertion이 전혀 체크되지 않는 상황을 방지합니다.

</details>
## Q4. (Analyze)

Constrained Random sequence에서 VA 분포를 Hotspot 60% / 일반 30% / 넓은 범위 10%로 한 이유는?

<details>
<summary>정답 / 해설</summary>

실제 워크로드의 VA 분포 모사:
- **Hotspot 60%**: 대부분의 access는 좁은 영역 (cache locality) → TLB hit pattern 검증
- **일반 30%**: 보통의 다양성 → 일반 case
- **넓은 범위 10%**: TLB capacity miss / PWC 효과 검증

100% 균등 분포는 비현실적이고 corner case 도달 어려움. 실제 트래픽 패턴 + targeted scenario의 균형.

이 분포를 실제 워크로드 특성에서 도출했다는 점이 핵심입니다. 대부분의 응용 프로그램은 temporal locality를 가지며, 최근 접근한 주소 근처를 다시 접근하는 경향이 있습니다. Hotspot 60%는 이 현실을 반영하며, TLB가 이런 locality를 얼마나 잘 활용하는지 검증합니다. 넓은 범위 10%는 역설적으로 가장 까다로운 케이스인데, TLB capacity miss와 PWC invalidation이 집중적으로 발생해 DUT의 성능 한계 지점을 탐색합니다. 100% 균등 분포로는 이 두 극단 시나리오를 동시에 충분히 자극할 수 없어, 실제 배포 환경에서는 나타나지 않는 인위적 패턴만 검증하게 됩니다.

</details>
## Q5. (Evaluate)

다음 시나리오 중 MMU 검증에서 가장 catch하기 어려운 silent bug는?

- [ ] A. PA 계산 오류 (잘못된 비트 분할)
- [ ] B. TLB invalidation 후 stale entry 잔존
- [ ] C. Permission check 누락
- [ ] D. Walk depth 5 (4-level인데 5번 walk)

<details>
<summary>정답 / 해설</summary>

**B**. 다음 access에서 잘못된 PA 사용하지만 fault나 error 발생 안 함 → 데이터 corruption만 silent하게 발생. 다른 옵션:
- A: scoreboard에서 즉시 mismatch
- C: permission fault assert로 catch
- D: walk count counter assertion으로 catch

B는 invalidation 시점 검증 cover가 있어야만 catch 가능 → SVA bind 패턴의 가치를 보여주는 케이스.

B가 가장 catch하기 어려운 이유는 하드웨어 관점에서 아무 이상이 없어 보이기 때문입니다. TLB의 stale entry는 valid=1이고 PA 필드도 가지고 있으므로, MMU는 정상적으로 변환을 완료합니다. 단지 그 PA가 더 이상 올바른 매핑이 아닐 뿐입니다. A(PA 계산 오류)는 scoreboard가 reference model의 PA와 비교할 때 즉시 불일치를 감지합니다. C(permission check 누락)는 잘못된 권한으로 접근이 허용되는 순간 permission fault를 검사하는 SVA assertion이 발화합니다. D(walk depth 5)는 walk step counter assertion이 5번째 walk를 감지해 즉시 에러를 보고합니다. B만이 어떤 observable한 에러 신호도 발생시키지 않아, invalidation 이벤트와 그 이후 접근을 연결하는 시간 기반 assertion이 없으면 detection이 불가능합니다.

</details>
