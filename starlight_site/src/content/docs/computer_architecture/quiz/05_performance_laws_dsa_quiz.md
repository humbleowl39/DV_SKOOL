---
title: "Quiz — Module 05: 성능 법칙 & 이종 SoC/DSA"
---

[← Module 05 본문으로 돌아가기](../../05_performance_laws_dsa/)

---

## Q1. (Remember)

Iron Law of Performance 의 식은?

- [ ] A. CPU Time = IC + CPI + Cycle Time
- [ ] B. CPU Time = IC × CPI × Cycle Time
- [ ] C. CPU Time = IC / (CPI × Cycle Time)
- [ ] D. CPU Time = CPI × Frequency

<details>
<summary>정답 / 해설</summary>

**B**. CPU Time = Instruction Count(IC) × CPI × Cycle Time = IC × CPI / Clock Frequency. 세 _독립_ 축의 곱으로, IC 는 알고리즘/컴파일러/ISA, CPI 는 마이크로아키텍처(파이프라인·캐시·분기 예측), Cycle Time 은 회로 임계 경로가 결정합니다. 곱이므로 한 축의 이득이 다른 축의 손해로 상쇄될 수 있습니다(A 의 합·C/D 형태는 오답).

</details>
## Q2. (Understand)

Amdahl's Law 가 가속기 오프로드에 주는 핵심 통찰은?

<details>
<summary>정답 / 해설</summary>

병렬화 가능 비율 f, 그 부분의 speedup S 일 때 전체 speedup = 1/((1−f)+f/S) 이고, 핵심은 _직렬 비율 (1−f)이 절대 천장을 만든다_ 는 것입니다. 가속기가 워크로드의 95%(f=0.95)를 무한히 빠르게 처리해도(S→∞), 전체 speedup 은 1/(1−0.95) = 20× 를 넘지 못합니다 — 남은 5% 직렬 부분(CPU 측 처리·데이터 이동·동기화)이 시스템 상한을 막기 때문입니다. 따라서 가속기 성능 검증의 목표는 "가속기 자체 속도"가 아니라 "직렬 경로를 포함한 시스템 speedup"이어야 하며, 직렬 부분을 줄이는 것이 더 큰 시스템 이득을 줍니다.

</details>
## Q3. (Apply)

한 커널의 arithmetic intensity 가 0.1 FLOP/byte 이다. compute 유닛을 2× 늘리면 성능이 오를까? 무엇을 늘려야 하는가?

<details>
<summary>정답 / 해설</summary>

오르지 않을 가능성이 높습니다. AI = 0.1 FLOP/byte 는 매우 낮아 이 커널은 memory-bandwidth bound 입니다. Roofline 에서 perf = min(compute roof, AI × memory BW) 이고, AI 가 낮으면 `AI × memory BW`(memory roof)가 compute roof 보다 작아 성능이 memory roof 에 막힙니다. 따라서 compute roof 를 2× 올려도 min 값은 그대로라 성능이 변하지 않습니다. 늘려야 할 것은 memory bandwidth(예: HBM 채택), 또는 PIM 으로 데이터 이동 자체를 줄이거나, 알고리즘 재구성으로 AI 를 높이는 것입니다. 이것이 DMA/스트리밍 엔진 검증에서 마이크로벤치 목표를 "memory roof saturate"로 잡는 이유입니다.

</details>
## Q4. (Analyze)

새 마이크로아키텍처가 IC 를 10% 줄였지만 CPI 가 20% 늘었고 주파수는 동일하다. 성능 변화를 Iron Law 로 분석하라.

- [ ] A. 약 10% 향상
- [ ] B. 약 8% 악화
- [ ] C. 변화 없음
- [ ] D. 약 20% 향상

<details>
<summary>정답 / 해설</summary>

**B**. CPU Time = IC × CPI × Cycle Time. Cycle Time(주파수) 동일이므로 상대 CPU Time = (0.90 × IC) × (1.20 × CPI) × (1.0 × CT) = 1.08 × 원래 값입니다. 즉 실행 시간이 ~8% _증가_ 해 성능이 8% 악화됩니다. IC 감소(10%)가 CPI 증가(20%)를 상쇄하지 못한 경우입니다. Iron Law 의 핵심은 세 축이 독립적이라 한 축 이득이 다른 축 손해로 상쇄될 수 있다는 점 — 이 변화는 단독으로는 채택하면 안 되고, CPI 증가의 원인을 분석해 회복하거나 주파수로 보상할 수 있을 때만 의미가 있습니다.

</details>
## Q5. (Evaluate)

Dennard scaling 종료 이후 업계가 도메인 특화 가속기(DSA)로 전환하는 것이 합리적인지 평가하라.

<details>
<summary>정답 / 해설</summary>

합리적입니다. Dennard scaling(트랜지스터 축소 시 전압·전력 비례 축소)이 끝나면서 전력 밀도가 급증해 단일 코어 주파수가 3–4 GHz 에서 정체했고(Power Wall), 고급 공정에서는 열 한계로 전체 트랜지스터의 일부만 동시 full-voltage 가동 가능한 dark silicon 이 등장했습니다. 이 상황에서 범용 CPU 의 추가 트랜지스터로는 더 이상 비례하는 성능/효율을 얻기 어렵습니다. DSA 는 타겟 워크로드에 맞춰 ISA 범용성 오버헤드·깊은 디코드 논리·큰 레지스터 파일을 제거해, 같은 전력 예산에서 범용 CPU 대비 10–1000× 에너지 효율을 냅니다(예: TPU 의 systolic array + on-chip SRAM). trade-off 는 유연성 상실(특정 도메인 외에는 무용)과 설계/검증 비용 증가이지만, dark silicon 시대에는 "특화가 보답한다(specialization pays)"는 명제가 성립합니다. 다만 Amdahl 의 직렬 천장 때문에 가속기만으로 시스템 전체가 빨라지지는 않으므로, 이종 SoC 에서 CPU·DSA·메모리(HBM/PIM)를 워크로드별로 조합하고 coherence·변환·RAS 를 시스템 레벨에서 검증하는 것이 동반되어야 합니다.

</details>
