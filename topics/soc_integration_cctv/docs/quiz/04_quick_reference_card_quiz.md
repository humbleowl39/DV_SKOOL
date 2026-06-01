# Quiz — Module 04: SoC Quick Reference

[← Module 04 본문으로 돌아가기](../04_quick_reference_card.md)

---

## Q1. (Recall)

CCTV 약어와 핵심 정의 한 줄?

??? answer "정답 / 해설"
    **Common Task Coverage Verification** — SoC 내 모든 IP에 공통 task가 빠짐없이 적용되었는지 추적하는 coverage 방법론.

    CCTV의 이름에서 "Coverage"와 "Verification"이 함께 등장하는 것은 이 방법론이 단순히 테스트 목록을 관리하는 것이 아니라, 커버리지를 sign-off 기준으로 삼는다는 철학을 반영한다. IP가 몇 개인지, Common Task가 몇 가지인지와 무관하게 "모든 조합(cell)이 covered 또는 명시적 N/A"라는 단일 기준으로 검증 완료를 판단할 수 있기 때문에, 대규모 SoC에서도 검증 완료 기준이 모호해지지 않는다.

## Q2. (Recall)

Top-level DV에서만 catch되는 결함 카테고리 5가지?

??? answer "정답 / 해설"
    Connectivity, CDC, Interrupt routing, Memory map decoding, Power domain isolation. (+ DFT scan path, voltage level conversion).

    이 카테고리들은 한 가지 공통된 특징이 있다. 모두 "두 개 이상의 IP 또는 도메인이 동시에 인스턴스화된 환경"에서만 관찰된다는 점이다. 각 IP를 독립적으로 검증하는 IP-level DV는 이 인터페이스 경계를 볼 수 없으므로, 아무리 완벽한 IP-level coverage를 달성해도 위의 5가지 카테고리는 반드시 top-level에서 별도로 검증해야 한다. 이것이 IP-level DV와 SoC top-level DV가 서로 대체가 아닌 보완 관계인 근본 이유이다.

## Q3. (Apply)

SoC Top DV에 가장 효과적인 보조 기법 3가지?

??? answer "정답 / 해설"
    1. **Formal connectivity check** (JasperGold Connectivity App)
    2. **Emulation / FPGA prototyping** (real software 시뮬 가능)
    3. **AI-assisted sequence/coverage** (gap 자동 식별)

    시뮬만으로는 SoC scale 한계.

    세 기법은 각각 서로 다른 공백을 채운다. Formal connectivity check는 시뮬 없이 수학적으로 연결 완전성을 증명하여 Connectivity 카테고리를 효율적으로 커버한다. Emulation/FPGA는 시뮬보다 수백 배 빠른 속도로 실제 운영체제와 드라이버를 포함한 소프트웨어-하드웨어 통합 시나리오를 수행할 수 있어, 시뮬로는 현실적으로 실행하기 어려운 긴 boot sequence나 OS 레벨 시나리오를 커버한다. AI-assisted 기법은 coverage report를 분석해 인간이 놓치기 쉬운 coverage gap을 빠르게 식별한다. 어느 한 가지만으로 SoC top-level의 검증 공백을 모두 채울 수는 없으며, 세 방법을 조합하는 것이 현실적인 전략이다.

## Q4. (Apply)

새 IP가 SoC에 추가될 때 가장 먼저 해야 할 검증은?

??? answer "정답 / 해설"
    1. **Connectivity check**: 모든 input/output이 정확히 연결됐는지
    2. **Memory map**: 새 IP 영역 access가 정확히 라우팅
    3. **Reset/clock**: 새 IP의 reset/clock이 정상 toggle
    4. **CCTV cell 채움**: Common Task 매트릭스에 새 IP 행 추가 + 각 task 적용

    이 순서에는 논리적 이유가 있다. Connectivity와 Memory map은 IP가 SoC에 물리적으로 올바르게 연결되어 있는지 확인하는 "기초 공사"이며, 이것이 실패하면 이후의 모든 기능 검증이 의미 없다. Reset/clock이 정상적으로 동작하는지는 IP의 동작 상태를 초기화할 수 있는지 여부를 결정하므로, 기능 시나리오 이전에 반드시 확인해야 한다. CCTV cell 채움은 기초가 완성된 후, 새 IP에 SoC 공통 플랫폼 규칙이 올바르게 적용되는지 체계적으로 확인하는 단계이다. 이 네 단계를 순서대로 진행하면 새 IP 통합 시 발생하는 대부분의 결함 카테고리를 체계적으로 커버할 수 있다.

## Q5. (Evaluate)

다음 중 Production silicon에 가장 위험한 SoC integration bug는?

- [ ] A. CDC metastability 1/10000 발생
- [ ] B. Interrupt routing 1개 IP 누락
- [ ] C. DVFS transition 100ms 지연
- [ ] D. Memory map decoding 1개 alias 영역

??? answer "정답 / 해설"
    **A**. CDC metastability는 silent + intermittent → field에서만 발견 + 재현 어려움. B는 boot 중 catch될 가능성 높음. C는 성능. D는 software workaround 가능.

    A가 가장 위험한 이유는 "발견이 어렵다"는 특성 때문이다. CDC metastability는 확률적으로 발생하므로 수만 번 시뮬을 돌려도 잡히지 않다가 실제 칩이 특정 온도·전압 조건에서 field에 배포된 후에야 간헐적으로 나타날 수 있다. 재현도 어렵고 디버그는 더 어렵다. 반면 B(Interrupt routing 누락)는 boot 과정에서 인터럽트가 오지 않으면 즉시 시스템이 멈추므로 개발 초기에 발견된다. C(DVFS 지연 100ms)는 기능 오류가 아닌 성능 문제이며, D(Memory map alias)는 소프트웨어에서 해당 주소 범위를 사용하지 않도록 우회할 수 있다. Production silicon 관점에서 "발견 타이밍이 늦을수록 + 재현이 어려울수록" 더 위험한 버그이다.
