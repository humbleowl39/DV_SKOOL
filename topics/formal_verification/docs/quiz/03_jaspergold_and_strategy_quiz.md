# Quiz — Module 03: JasperGold & Strategy

[← Module 03 본문으로 돌아가기](../03_jaspergold_and_strategy.md)

---

## Q1. (Remember)

JasperGold의 표준 워크플로 5단계를 순서대로 답하세요.

??? answer "정답 / 해설"
    1. **Elaborate** — RTL 컴파일 + DUT 계층 구성
    2. **Assume** — 입력 제약 적용 (실제 환경 모델링)
    3. **Assert** — spec 규칙을 property로 등록
    4. **Run** — Formal 엔진 실행 (SAT/SMT solving)
    5. **Analyze** — 결과 (PROVEN/BOUNDED/CEX) 분석 및 디버그

    이 순서는 이유가 있는 인과 흐름이다. Elaborate가 먼저인 이유는 DUT 계층이 확정되어야 assume과 assert에서 정확한 신호 이름을 참조할 수 있기 때문이다. Assume을 Assert보다 먼저 설정하는 이유는 solver가 property를 검사할 때 이미 제약된 입력 공간 안에서만 탐색하도록 하기 위해서다. Assume 없이 assert를 실행하면 엔진이 실제로는 절대 발생하지 않는 입력 조합으로 false CEX를 만들어낸다. Run과 Analyze는 불가분이며, BOUNDED 결과를 받으면 Analyze 단계에서 원인을 파악하고 assume 또는 abstraction을 추가해 다시 Run하는 반복 루프를 형성한다.

## Q2. (Understand)

다음 시나리오에 적합한 JasperGold App을 답하세요.

| 시나리오 | App |
|----------|-----|
| (a) RTL spec 규칙 검증 | ? |
| (b) RTL2RTL 등가 검증 (synthesis 후) | ? |
| (c) 클럭 도메인 교차 검증 | ? |
| (d) 핀 연결 정합성 검증 | ? |

??? answer "정답 / 해설"
    - (a) **JG-Apex (Functional)** — 일반 property checking
    - (b) **Equivalence Checking (FEV)** — 두 RTL의 equivalence
    - (c) **CDC App** — 클럭 도메인 신호 핸들링 검증
    - (d) **Connectivity App** — top 인터커넥트 핀 매핑 검증

    각 App은 풀려는 문제의 수학적 구조가 다르기 때문에 분리되어 있다. JG-Apex는 사용자 정의 property를 SAT/SMT solver로 증명하는 범용 엔진이고, Equivalence Checking(FEV)은 두 netlist가 동일한 입출력 관계를 갖는지 비교하는 bijective 증명이므로 synthesis 이후 변환 정확성 검증에 특화된다. CDC App은 클럭 도메인 교차 신호에서 metastability나 reconvergence 패턴을 구조적으로 찾아내는 데 특화되어 있고, Connectivity App은 top-level 포트 연결 정합성을 정적 분석으로 검사하므로 integration 초기에 wiring 오류를 빠르게 잡는다. 시나리오마다 적합한 App을 선택하지 않으면 분석 시간이 늘고 적합하지 않은 결과가 나온다.

## Q3. (Apply)

BOUNDED 결과를 PROVEN으로 만들려면 일반적으로 어떤 순서로 시도하는가?

??? answer "정답 / 해설"
    1. **Cut Point** — 큰 블록을 작게 분할
    2. **Blackbox** — 무관한 모듈 제거 (COI 축소)
    3. **Abstraction** — 큰 카운터/데이터 폭 축소
    4. **Assume tightening** — 입력 공간 좁히기 (단, over-constraint 주의)
    5. **Helper Assertion** — Inductive invariant 강화

    1번부터 시도하고 안 되면 다음 기법 추가. 효율 vs 정확성 trade-off 고려.

    이 순서는 "부작용이 적은 것부터"라는 원칙에서 나온다. Cut Point는 DUT 내부 신호를 free input으로 만드는 것으로, 그 뒤편 논리만 검증하는 대신 앞편은 검증에서 빠지므로 sign-off 시 명시가 필요하다. Blackbox는 COI 외부 모듈을 제거하므로 property와 무관한 영역에 한해 적용해야 하고, 적용 범위를 잘못 설정하면 버그가 있는 모듈을 빠뜨린다. Abstraction과 Assume tightening은 모델 자체를 바꾸므로 over-constraint나 soundness 손실 위험이 있어 마지막 수단으로 쓰고 검증 범위를 문서화해야 한다. Helper Assertion은 가장 수학적으로 엄밀한 방법으로, 불변조건을 명시적으로 추가해 solver가 귀납을 완성하도록 돕는다.

## Q4. (Analyze)

CEX(Counterexample)를 받았을 때 RTL 버그인지 Assume 부족인지 어떻게 구분하는가?

??? answer "정답 / 해설"
    1. **반례 입력의 의미 분석** — 입력 시퀀스가 실제 환경에서 가능한가?
    2. **Spec 확인** — 해당 입력 패턴이 spec에서 허용되는가?
    3. **결론**:
       - 가능한 입력 + spec 허용 → **RTL 버그** (수정 필요)
       - 불가능한 입력 (spec이 금지) → **Assume 부족** (입력 제약 추가)

    **False negative (실제 버그 아닌 fail)**의 흔한 원인: 환경에서 절대 발생 안 하는 입력 조합을 엔진이 시도. 해결: 해당 조합을 금지하는 assume 추가 + 대응 cover로 over-constraint 검사.

    CEX 분류는 Formal 워크플로에서 가장 판단력이 필요한 단계다. 엔진은 property를 깨는 입력 시퀀스를 제시할 뿐, 그것이 현실적인 시나리오인지는 판단하지 않는다. 반례를 받았을 때 먼저 해야 할 일은 그 입력 시퀀스를 waveform viewer에서 재현해 "이런 상황이 실제 시스템에서 발생 가능한가"를 spec과 대조하는 것이다. 가능하다면 RTL 버그이므로 설계 팀에 전달하고, 불가능하다면 환경 모델(assume)에 빈 곳이 있는 것이므로 해당 조합을 금지하는 assume을 추가한다. 이때 새 assume에 대응하는 cover도 함께 추가해 over-constraint가 발생하지 않았는지 검증하는 것이 올바른 절차다.

## Q5. (Evaluate)

다음 중 Sign-off 5가지 기준에 **포함되지 않는** 것은?

- [ ] A. 모든 assert PROVEN 또는 정당한 BOUNDED
- [ ] B. 모든 cover COVERED
- [ ] C. Assume이 spec과 1:1 매핑 + 대응 cover
- [ ] D. CPU 시간 < 1시간

??? answer "정답 / 해설"
    **D**. 검증 시간은 sign-off 기준이 아님. 5가지: (1) assert 결과, (2) cover, (3) Assume 감사, (4) COI(블랙박스 영향), (5) Property 완전성. 시간은 효율의 지표지 신뢰성 지표가 아님.

    오답인 A, B, C가 sign-off 기준에 포함되는 이유를 이해하면 D가 왜 빠지는지 명확해진다. A는 assert가 PROVEN 또는 정당한 이유가 기록된 BOUNDED여야 하므로 결과의 신뢰성 기준이다. B는 cover가 COVERED여야 vacuous pass가 없음을 보장하므로 검증의 실질성 기준이다. C는 assume이 spec과 1:1 매핑되어야 over-constraint가 없음을 보장하므로 입력 모델의 건전성 기준이다. 반면 D는 CPU 시간이 짧으면 효율이 좋다는 의미이지, 결과가 신뢰할 수 있다는 증거가 아니다. 1시간 안에 끝난 BOUNDED는 여전히 불완전한 결과일 수 있다.
