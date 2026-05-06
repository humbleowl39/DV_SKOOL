# Quiz — Module 02: Memory Controller

[← Module 02 본문으로 돌아가기](../02_memory_controller.md)

---

## Q1. (Remember)

MC의 핵심 책임 3가지는?

??? answer "정답 / 해설"
    1. AXI 요청 → DRAM 명령 (ACT/RD/WR/PRE/REF) 변환
    2. Timing constraint 준수 (tRCD, tRP, tFAW, tREFI 등)
    3. 스케줄링 (Row Hit 극대화, Bank parallelism, R/W batching)

## Q2. (Understand)

Row Hit / Row Miss / Row Closed의 latency 차이는?

??? answer "정답 / 해설"
    - **Row Hit** (이미 active row에 access): tCAS만 (가장 빠름)
    - **Row Miss** (다른 row, bank active): tRP + tRCD + tCAS (느림)
    - **Row Closed** (PRE 후): tRCD + tCAS (Row Miss보다 약간 빠름)

    Scheduler 정책이 Row Hit 비율을 결정.

## Q3. (Apply)

R↔W 전환 비용을 줄이는 기법은?

??? answer "정답 / 해설"
    **Write Batching + Watermark**. Write 요청을 buffer에 모아 두고 high watermark 도달 시 batch drain → 연속 Write로 발행. 그동안 Read를 우선 처리. R↔W 전환 횟수를 최소화하여 tWTR/tRTW 비용 절감.

## Q4. (Analyze)

Refresh가 throughput에 미치는 영향과 완화 기법은?

??? answer "정답 / 해설"
    **영향**: REF 동안 해당 bank 또는 device 전체 access 불가 → 평균 1-2% throughput 손실. Refresh 폭이 늘어나면 더 심각.

    **완화**:
    - Per-bank refresh: 다른 bank는 정상 동작
    - Fine-grain refresh: refresh를 작게 쪼개서 stall 시간 단축
    - Postponed refresh: traffic 많을 때 미루고 idle 때 보충 (단 너무 미루면 retention 위험)

## Q5. (Evaluate)

QoS에서 starvation 방지에 가장 효과적인 메커니즘은?

- [ ] A. Strict priority
- [ ] B. Round-robin
- [ ] C. Aging (대기 시간에 따라 우선순위 승격)
- [ ] D. Random selection

??? answer "정답 / 해설"
    **C**. Strict priority는 starvation 발생. Round-robin은 우선순위 무시. Aging은 두 장점 결합 — 평소엔 priority 기반 + 오래 대기한 요청은 자동 승격. Display 같은 실시간 마스터에는 Urgent + Aging 조합.
