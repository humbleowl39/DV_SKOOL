---
title: "Quiz — Module 04: DRAM DV Methodology"
---

[← Module 04 본문으로 돌아가기](../../04_dram_dv_methodology/)

---

## Q1. (Remember)

DRAM 검증의 3가지 검증 축은?

<details>
<summary>정답 / 해설</summary>

1. **Timing**: tRCD, tRP, tRC, tFAW, tREFI 등 JEDEC이 규정한 모든 timing constraint가 매 명령마다 지켜지는지 검증한다. 단 하나의 위반도 데이터 손상이나 DRAM 오동작으로 이어질 수 있으므로, assertion 기반으로 자동화하는 것이 필수다.
2. **Data integrity**: MC가 write한 데이터가 read 시 정확히 돌아오는지 확인한다. 여기에는 ECC 경로도 포함되므로 1-bit error injection 후 자동 수정, 2-bit error detection 같은 시나리오를 명시적으로 테스트해야 한다.
3. **Performance**: 특정 traffic 패턴에서 실효 대역폭, read latency, QoS별 처리량이 설계 목표를 충족하는지 측정한다. 기능적으로 정상 동작해도 성능이 기준 미달이면 스케줄러 또는 타이밍 설정에 문제가 있는 것이다.

</details>
## Q2. (Understand)

DRAM Behavioral Model이 검증에서 하는 역할은?

<details>
<summary>정답 / 해설</summary>

DRAM Behavioral Model은 JEDEC 명령 프로토콜을 소프트웨어로 구현해 실제 DRAM 칩 없이 시뮬레이션에서 MC의 타이밍·기능을 검증할 수 있게 한다. MC가 ACT를 발행하면 model이 해당 row를 활성화하고, tRCD 이후 RD를 발행하면 저장된 데이터를 돌려보내는 방식으로 동작한다. Refresh 미준수, timing 위반 같은 프로토콜 오류도 model이 감지해 에러를 보고하므로, assertion과 함께 사용하면 timing 위반을 자동으로 검출할 수 있다. Error injection 기능으로는 1-bit ECC fault를 심어 MC의 수정 동작을 확인하거나, refresh를 강제 누락시켜 retention 경계 동작을 테스트하는 corner case 시나리오에 활용한다.

</details>
## Q3. (Apply)

다음 시나리오에 적합한 검증 기법을 매핑하세요.

| 시나리오 | 기법 |
|----------|------|
| (a) tRCD 위반 검출 | ? |
| (b) BW regression | ? |
| (c) Refresh 누락 | ? |
| (d) ECC SECDED 동작 | ? |

<details>
<summary>정답 / 해설</summary>

- **(a) SVA bind**: tRCD는 "ACT 발행 후 RD/WR까지의 최소 간격"이므로 property로 표현해 simulator가 매 ACT마다 자동 검사하도록 한다. 사람이 파형을 일일이 확인하는 것보다 누락 없이 커버할 수 있다.
- **(b) Performance Reference + Scoreboard**: AXI 요청 timestamp와 응답 timestamp의 차이에서 latency를, 단위 시간 내 완료된 byte 수에서 BW를 계산한다. 기준값 대비 regression을 자동으로 감지할 수 있다.
- **(c) Refresh Counter assertion**: tREFI 주기를 카운팅하며 해당 기간 내 row가 적어도 한 번 REF를 받았는지 추적한다. 카운터 기반 assertion이 refresh 누락을 구조적으로 보장한다.
- **(d) Behavioral Model error injection**: model에 1-bit fault를 심은 뒤 MC가 SECDED ECC로 자동 수정해 원본 데이터를 돌려보내는지 확인한다. 수정 후 data가 원본과 일치하면 ECC 경로가 올바르게 동작하는 것이다.

</details>
## Q4. (Analyze)

Performance Reference로 측정해야 하는 핵심 지표 3가지는?

<details>
<summary>정답 / 해설</summary>

1. **순차 read/write BW**: 이론 peak 대비 실효 효율(%)로 측정한다. 순차 access는 Row Hit이 대부분이므로 이론치에 가장 가까워야 하며, 여기서 큰 손실이 나오면 스케줄러 또는 burst 길이 설정에 문제가 있다는 신호다.
2. **랜덤 access BW**: 주소가 무작위로 분산되면 Row Hit 비율이 낮아지고 bank conflict가 빈번해진다. 순차와 랜덤의 BW 비율이 설계 예상 범위에 있는지 확인해야 한다.
3. **R/W mix BW**: Read와 Write가 섞일 때 전환 비용(tWTR/tRTW)이 얼마나 발생하는지, batch drain이 의도대로 전환 횟수를 줄이는지 직접 측정한다.
+ **Per-master latency**: QoS 설정이 다른 마스터 간에 latency가 실제로 차등화되는지 확인한다. 실시간 마스터가 배경 traffic에 묻혀 지연되면 QoS 회로가 제대로 동작하지 않는 것이다.

</details>
## Q5. (Evaluate)

다음 중 silent corruption 위험이 가장 큰 시나리오는?

- [ ] A. Refresh count assertion fail
- [ ] B. Training이 marginal하게 pass
- [ ] C. ECC double-bit error 검출
- [ ] D. tRCD violation

<details>
<summary>정답 / 해설</summary>

**B**. Training이 marginal하게 pass했다는 것은 시뮬레이션 기준으로 "성공"이지만 실제 마진이 매우 좁은 상태임을 의미한다. 정상 traffic에서는 아무런 오류가 없다가 PVT 변동(온도 상승, 전압 droop) 또는 high-speed burst stress에서 bit error가 발생하므로, 원인을 파악하기 극히 어려운 field 버그로 이어진다. 반면 A(Refresh assertion fail)는 시뮬레이션에서 즉시 검출되고, C(ECC double-bit error)는 system 인터럽트 또는 error report로 직접 신호가 발생하며, D(tRCD violation)도 assertion이나 DRAM model 오류로 즉각 포착된다. 발견하기 어려운 정도 자체가 위험도를 높이므로, B가 production silicon에서 가장 위험하다.

</details>
