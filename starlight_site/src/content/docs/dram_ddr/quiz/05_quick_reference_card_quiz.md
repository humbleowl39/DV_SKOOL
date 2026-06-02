---
title: "Quiz — Module 05: DRAM Quick Reference"
---

[← Module 05 본문으로 돌아가기](../../05_quick_reference_card/)

---

## Q1. (Recall)

다음 timing parameter를 한 줄로:

- tRCD
- tRP
- tCAS / CL
- tRAS
- tREFI

<details>
<summary>정답 / 해설</summary>

- **tRCD (Row to Column Delay)**: ACT를 발행한 뒤 sense amplifier가 row 데이터를 완전히 증폭할 때까지 기다리는 시간으로, 이 후에야 RD/WR가 가능하다.
- **tRP (Row Precharge)**: PRE 이후 bit line이 VDD/2로 다시 충전될 때까지의 최소 대기 시간으로, 이 후에야 다음 ACT를 발행할 수 있다.
- **tCAS / CL (CAS Latency)**: RD 명령을 발행한 뒤 첫 번째 유효 데이터가 DQ 버스에 나타날 때까지의 clock 사이클 수다.
- **tRAS (Row Active Strobe)**: ACT 이후 PRE를 발행하기 전에 row가 활성화 상태를 유지해야 하는 최소 시간으로, 데이터를 완전히 센스·증폭하기 위해 필요하다.
- **tREFI**: 각 row가 보존 시간 내에 적어도 한 번 refresh를 받도록 MC가 REF를 발행하는 주기다. DDR4는 7.8 μs, DDR5는 3.9 μs다.

</details>
## Q2. (Recall)

Row Hit / Row Miss / Row Closed 중 가장 빠른 access는?

<details>
<summary>정답 / 해설</summary>

**Row Hit**가 가장 빠르다. 이미 sense amplifier에 올라온 row에 접근하므로 ACT나 PRE 없이 CAS latency 만큼만 기다리면 첫 데이터를 받을 수 있다. Row Miss는 tRP + tRCD + tCAS, Row Closed는 tRCD + tCAS가 직렬로 필요해 수십 cycle이 더 걸린다. 스케줄러가 동일 row에 대한 연속 요청을 묶거나 재정렬하는 이유가 바로 이 Row Hit 이득을 극대화하기 위해서다.

</details>
## Q3. (Apply)

DDR4 16-bank vs DDR5 32-bank의 검증 영향은?

<details>
<summary>정답 / 해설</summary>

DDR5가 Bank Group을 4개에서 8개로 늘림에 따라 검증에서 고려해야 할 사항이 세 가지 측면으로 확장된다. 첫째, 같은 BG 내 연속 access에는 긴 tCCD_L이, 다른 BG 간에는 짧은 tCCD_S가 적용되므로, 스케줄러가 BG를 제대로 분산하고 있는지 BW 측정 시 BG 분산 효과를 포함한 시나리오를 별도로 검증해야 한다. 둘째, bank가 32개로 늘어나 BLP 시나리오가 더욱 다양해지므로 bank conflict 테스트 벡터도 DDR5의 bank 구조에 맞게 업데이트해야 한다. 셋째, per-bank refresh 활용 범위가 넓어져 refresh 중 다른 bank traffic에 미치는 영향 측정 시나리오도 DDR5 구조를 반영해야 한다.

</details>
## Q4. (Analyze)

DDR5 on-die ECC의 한계는?

<details>
<summary>정답 / 해설</summary>

DDR5 on-die ECC는 SECDED(Single Error Correct, Double Error Detect) 방식이므로, 1-bit 오류는 DRAM 내부에서 자동 수정하지만 2-bit 이상 오류는 검출만 할 수 있고 수정하지 못한다. 이것이 핵심 한계다. 실제 메모리 서브시스템에서는 이 한계를 보완하기 위해 외부(MC 또는 별도 ECC 칩)의 추가 SECDED ECC를 함께 사용하는 것을 권장한다. 2-bit 오류가 on-die ECC에서 검출되면 system error 인터럽트로 올라가고 OS나 firmware가 해당 메모리 영역을 격리 처리한다. 그리고 ECC scrubbing이 중요한 이유도 여기에 있다. 방치된 single-bit 오류가 누적되면 확률적으로 2-bit 오류로 진행할 수 있으므로, 주기적 scrubbing으로 single-bit 오류를 조기에 교정해 double-bit 오류로 발전하는 것을 막는다.

</details>
## Q5. (Evaluate)

다음 DV 버그 중 production silicon에 가장 위험한 것은?

- [ ] A. tRCD 1 cycle 미달
- [ ] B. Refresh 주기 5% 초과
- [ ] C. Training이 cold corner에서 fail
- [ ] D. Scheduler가 Row Hit을 놓침 (BW 5% 저하)

<details>
<summary>정답 / 해설</summary>

**C**. cold corner training fail이 가장 위험하다. 저온 환경에서만 발생하는 오류는 일반 온도 조건의 시뮬레이션이나 테스트에서 잡히지 않고, 실제 데이터센터 입고 직후처럼 칩이 저온인 상황에서만 재현된다. 이런 오류는 field에서 간헐적으로 나타나 원인 파악이 극히 어렵다. A(Refresh count assertion fail)와 B(Refresh 주기 5% 초과)는 검증 환경에서 assertion이나 performance check로 직접 검출되므로 shipping 전에 수정할 수 있다. D(Row Hit 미스로 BW 5% 저하)는 기능적으로 올바르고 단지 성능 저하이므로 가장 심각도가 낮다. 검출 불가능한 환경 의존성 silent corruption이 production에서 가장 위험한 유형이다.

</details>
