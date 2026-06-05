---
title: "Quiz — Module 03: 언제 쓰나 + DV 트레이드오프"
---

[← Module 03 본문으로 돌아가기](../../03_when_to_use_tradeoffs/)

---

## Q1. (Remember)

다음 중 `cocotb_note.md`가 cocotb의 **Poor fit**(부적합)으로 든 경우가 아닌 것은?

- [ ] A. 대규모 SoC full-simulation
- [ ] B. 상용 VIP가 필요한 프로토콜 (PCIe Gen5, DDR)
- [ ] C. IP / 블록 레벨 검증
- [ ] D. 기존 대규모 UVM 자산 위의 검증

<details>
<summary>정답 / 해설</summary>

**C**. IP/블록 레벨 검증은 cocotb의 대표적 **Good fit**입니다. UVM 풀 환경 오버헤드 없이 빠르게 시작할 수 있기 때문입니다. A(대규모 full-sim, Python 오버헤드), B(상용 VIP는 UVM 기반), D(기존 UVM 자산 재사용)는 모두 Poor fit 사례입니다.

</details>
## Q2. (Understand)

cocotb가 "알고리즘 모델 통합이 중요한 분야(DSP/ML/이미지 처리)"에 잘 맞는 이유를 설명하라.

<details>
<summary>정답 / 해설</summary>

이런 분야는 검증 기대값을 계산하는 황금 레퍼런스 모델이 보통 NumPy/PyTorch 같은 Python 라이브러리로 이미 작성되어 있습니다. cocotb는 테스트가 Python이므로 그 모델을 `import numpy`처럼 평범한 import로 가져와 기대값 계산에 직접 쓸 수 있습니다. UVM이라면 같은 레퍼런스를 SystemVerilog로 다시 포팅하거나 DPI로 연결해야 하는데, cocotb는 이 비용이 없습니다. 그래서 Tenstorrent·Groq 같은 AI 가속기 회사가 Python 기반 검증을 핵심 플로우로 씁니다.

</details>
## Q3. (Apply)

"NumPy 황금 모델이 있는 소규모 FFT IP를 라이선스 없는 CI에서 검증하고 싶다." cocotb와 UVM 중 무엇을 권하는가?

- [ ] A. UVM — 회사 표준이므로
- [ ] B. cocotb — 알고리즘 통합 + 무료 CI + 소규모 IP
- [ ] C. UVM — 상용 VIP가 필요하므로
- [ ] D. 둘 다 불가능

<details>
<summary>정답 / 해설</summary>

**B**. 세 조건이 모두 cocotb 강점에 맞습니다. NumPy 황금 모델을 직접 import해 기대값에 쓸 수 있고(알고리즘 통합), Icarus/Verilator + cocotb로 시뮬레이터 라이선스 없이 CI를 돌릴 수 있으며(무료 CI), 소규모 IP라 대규모 full-sim의 Python 오버헤드 약점에도 걸리지 않습니다. A는 표준 관성, C는 이 과제에 상용 VIP가 필요 없으므로 틀린 근거입니다.

</details>
## Q4. (Analyze)

cocotb 선택 판단에서 "결정적 변수" 두 가지는 무엇이며, 왜 그 둘이 먼저인가?

<details>
<summary>정답 / 해설</summary>

두 결정적 변수는 (1) 상용 VIP(PCIe/DDR 등)가 필수인가, (2) 대규모 SoC full-sim인가입니다. 이 둘이 먼저인 이유는 둘 중 하나라도 해당하면 cocotb의 *근본 약점*(상용 VIP가 UVM 기반, full-sim에서 Python 오버헤드)에 정면으로 걸려 다른 장점들이 무의미해지기 때문입니다. 즉 이 둘은 다른 고려보다 우선하는 배제 조건(disqualifier)으로 작동합니다. 둘 다 해당하지 않을 때 비로소 알고리즘 통합·PoC·무료 CI 같은 cocotb의 강점이 결정에 의미를 갖습니다.

</details>
## Q5. (Evaluate)

"우리 회사는 모든 검증을 UVM으로 통일했으니 cocotb는 필요 없다." 이 입장을 도구 지형 관점에서 평가하라.

<details>
<summary>정답 / 해설</summary>

부분적으로만 타당합니다. 대규모 SoC·상용 VIP 영역에서는 표준 통일과 UVM이 실제로 옳고, 인력·자산 재사용 가치도 큽니다. 그러나 "모든 검증"으로 일반화하면 비효율이 생깁니다. IP/블록 레벨, 알고리즘 통합, 빠른 PoC, 무료 CI에서는 cocotb가 전체 비용을 줄입니다. 더 넓게 보면 검증 도구 지형은 cocotb/pyuvm, Verilator+C++, formal(Jasper/SymbiYosys), AI/LLM 보조가 *조합*되는 방향이며, "UVM 하나의 시대가 끝나간다"는 것이 핵심 메시지입니다. 따라서 이 입장은 특정 영역엔 맞지만 단일 도구 사고로 전체에 적용하는 것은 재고가 필요합니다.

</details>
## Q6. (Evaluate)

cocotb의 "시뮬레이터 독립성"을 활용해 비용과 속도를 함께 잡는 검증 전략을 하나 제시하라.

<details>
<summary>정답 / 해설</summary>

같은 cocotb 테스트 코드가 VPI 지원 시뮬레이터에서 변경 없이 돈다는 점을 활용하면, 평소 개발·CI는 무료 시뮬레이터(Icarus/Verilator) + GitHub Actions로 라이선스 없이 돌려 비용을 줄이고, 대규모 야간 회귀나 최종 sign-off 회귀만 상용 시뮬레이터(VCS/Questa)로 돌려 속도를 확보하는 이원 전략이 가능합니다. 코드를 한 줄도 바꾸지 않고 시뮬레이터만 교체하면 되므로, 무료 CI의 비용 이점과 상용 시뮬레이터의 성능 이점을 동시에 취할 수 있습니다.

</details>
