---
title: "Quiz — Module 02: Memory Controller"
---

[← Module 02 본문으로 돌아가기](../../02_memory_controller/)

---

## Q1. (Remember)

MC의 핵심 책임 3가지는?

<details>
<summary>정답 / 해설</summary>

1. **AXI 요청 → DRAM 명령 변환**: CPU나 GPU에서 오는 고수준의 AXI read/write 요청을 JEDEC이 정의한 ACT/RD/WR/PRE/REF 등의 저수준 명령 시퀀스로 번역한다. DRAM은 AXI를 직접 이해하지 못하므로 이 변환이 MC의 첫 번째 존재 이유다.
2. **Timing constraint 준수**: tRCD, tRP, tRC, tFAW, tREFI 등 JEDEC이 규정한 수십 개의 파라미터를 모두 지키면서 명령을 발행해야 한다. 한 개라도 위반하면 데이터 손상이나 DRAM 오동작이 발생하므로 타이밍 엔진이 매 사이클 이를 검사한다.
3. **스케줄링**: Row Hit 비율을 높이고, bank parallelism을 극대화하며, Read/Write를 배치로 묶어 전환 횟수를 줄인다. 동일한 DRAM 자원에서도 스케줄링 품질에 따라 실효 대역폭이 크게 달라진다.

</details>
## Q2. (Understand)

Row Hit / Row Miss / Row Closed의 latency 차이는?

<details>
<summary>정답 / 해설</summary>

- **Row Hit**: 요청 주소가 이미 활성화된 row에 있으므로 추가 ACT·PRE 없이 CAS latency만 기다리면 된다. 가장 빠른 경로이며, 스케줄러가 같은 row에 대한 연속 요청을 묶는 이유가 바로 이 이득이다.
- **Row Miss**: 해당 bank에 다른 row가 활성화되어 있으므로 먼저 PRE로 닫은 뒤(tRP 대기) 새로 ACT(tRCD 대기)해야 한다. tRP + tRCD + tCAS가 모두 직렬로 발생해 Row Hit보다 수십 cycle 느리다.
- **Row Closed**: bank가 이미 idle 상태이므로 PRE는 생략하고 ACT(tRCD 대기)만 하면 된다. Row Miss에서 tRP 비용이 빠진 만큼 약간 더 빠르다. 스케줄러 정책에 따라 세 경우의 발생 비율이 결정되며, 이것이 실효 대역폭을 좌우한다.

</details>
## Q3. (Apply)

R↔W 전환 비용을 줄이는 기법은?

<details>
<summary>정답 / 해설</summary>

**Write Batching + Watermark** 기법이 대표적이다. Read와 Write 사이를 전환할 때마다 DRAM은 tWTR(Write-to-Read) 또는 tRTW(Read-to-Write) 전환 사이클을 소비해야 하는데, 이 사이클 동안 유효한 데이터 이동이 없어 대역폭이 낭비된다. Write 요청을 내부 버퍼에 쌓아두고 high watermark에 도달하면 한꺼번에 batch로 flush함으로써 전환 횟수를 최소화한다. 그동안 Read 요청은 우선 소진하므로 Read latency도 함께 개선된다.

</details>
## Q4. (Analyze)

Refresh가 throughput에 미치는 영향과 완화 기법은?

<details>
<summary>정답 / 해설</summary>

**영향**: Refresh 명령이 발행되는 동안 해당 bank(또는 디바이스 전체)에 대한 access가 차단된다. tREFI마다 한 번씩 발생하는 이 stall이 평균 1~2% throughput 손실로 나타나며, 고집적·고온 환경처럼 refresh 빈도가 높아지면 손실이 더 커진다.

**완화**:
- **Per-bank refresh**: 특정 bank만 refresh 중에도 나머지 bank는 정상 동작하므로 stall 영향을 분산한다.
- **Fine-grain refresh**: refresh를 작은 단위로 쪼개 한 번의 stall 시간을 줄인다. 짧은 stall이 자주 발생하지만 worst-case latency spike를 완화한다.
- **Postponed refresh**: traffic 집중 구간에 refresh를 잠시 미루고 idle 시 보충한다. 단, JEDEC 규격에서 허용하는 최대 지연 횟수를 초과하면 cell 데이터가 손실되는 retention 위험이 있다.

</details>
## Q5. (Evaluate)

QoS에서 starvation 방지에 가장 효과적인 메커니즘은?

- [ ] A. Strict priority
- [ ] B. Round-robin
- [ ] C. Aging (대기 시간에 따라 우선순위 승격)
- [ ] D. Random selection

<details>
<summary>정답 / 해설</summary>

**C**. Aging이 정답이다. Strict priority(A)는 높은 우선순위 마스터가 계속 요청을 보내면 낮은 우선순위 마스터는 영원히 기다리는 starvation을 초래한다. Round-robin(B)은 모든 마스터를 동등하게 취급하므로 실시간 요구사항이 있는 마스터가 불이익을 받는다. Random selection(D)은 결정론적 보장을 전혀 제공하지 않는다. 반면 Aging은 평상시에는 우선순위 기반으로 동작하되, 대기 시간이 임계값을 넘은 요청을 자동으로 승격시키므로 starvation을 구조적으로 방지한다. 디스플레이처럼 마감 시간이 있는 실시간 마스터는 Urgent flag와 Aging을 조합해 사용하는 것이 일반적이다.

</details>
