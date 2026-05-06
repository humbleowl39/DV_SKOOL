# Quiz — Module 04: SoC Quick Reference

[← Module 04 본문으로 돌아가기](../04_quick_reference_card.md)

---

## Q1. (Recall)

CCTV 약어와 핵심 정의 한 줄?

??? answer "정답 / 해설"
    **Common Task Coverage Verification** — SoC 내 모든 IP에 공통 task가 빠짐없이 적용되었는지 추적하는 coverage 방법론.

## Q2. (Recall)

Top-level DV에서만 catch되는 결함 카테고리 5가지?

??? answer "정답 / 해설"
    Connectivity, CDC, Interrupt routing, Memory map decoding, Power domain isolation. (+ DFT scan path, voltage level conversion).

## Q3. (Apply)

SoC Top DV에 가장 효과적인 보조 기법 3가지?

??? answer "정답 / 해설"
    1. **Formal connectivity check** (JasperGold Connectivity App)
    2. **Emulation / FPGA prototyping** (real software 시뮬 가능)
    3. **AI-assisted sequence/coverage** (gap 자동 식별)

    시뮬만으로는 SoC scale 한계.

## Q4. (Apply)

새 IP가 SoC에 추가될 때 가장 먼저 해야 할 검증은?

??? answer "정답 / 해설"
    1. **Connectivity check**: 모든 input/output이 정확히 연결됐는지
    2. **Memory map**: 새 IP 영역 access가 정확히 라우팅
    3. **Reset/clock**: 새 IP의 reset/clock이 정상 toggle
    4. **CCTV cell 채움**: Common Task 매트릭스에 새 IP 행 추가 + 각 task 적용

## Q5. (Evaluate)

다음 중 Production silicon에 가장 위험한 SoC integration bug는?

- [ ] A. CDC metastability 1/10000 발생
- [ ] B. Interrupt routing 1개 IP 누락
- [ ] C. DVFS transition 100ms 지연
- [ ] D. Memory map decoding 1개 alias 영역

??? answer "정답 / 해설"
    **A**. CDC metastability는 silent + intermittent → field에서만 발견 + 재현 어려움. B는 boot 중 catch될 가능성 높음. C는 성능. D는 software workaround 가능.
