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

## Q3. (Apply)

BOUNDED 결과를 PROVEN으로 만들려면 일반적으로 어떤 순서로 시도하는가?

??? answer "정답 / 해설"
    1. **Cut Point** — 큰 블록을 작게 분할
    2. **Blackbox** — 무관한 모듈 제거 (COI 축소)
    3. **Abstraction** — 큰 카운터/데이터 폭 축소
    4. **Assume tightening** — 입력 공간 좁히기 (단, over-constraint 주의)
    5. **Helper Assertion** — Inductive invariant 강화

    1번부터 시도하고 안 되면 다음 기법 추가. 효율 vs 정확성 trade-off 고려.

## Q4. (Analyze)

CEX(Counterexample)를 받았을 때 RTL 버그인지 Assume 부족인지 어떻게 구분하는가?

??? answer "정답 / 해설"
    1. **반례 입력의 의미 분석** — 입력 시퀀스가 실제 환경에서 가능한가?
    2. **Spec 확인** — 해당 입력 패턴이 spec에서 허용되는가?
    3. **결론**:
       - 가능한 입력 + spec 허용 → **RTL 버그** (수정 필요)
       - 불가능한 입력 (spec이 금지) → **Assume 부족** (입력 제약 추가)

    **False negative (실제 버그 아닌 fail)**의 흔한 원인: 환경에서 절대 발생 안 하는 입력 조합을 엔진이 시도. 해결: 해당 조합을 금지하는 assume 추가 + 대응 cover로 over-constraint 검사.

## Q5. (Evaluate)

다음 중 Sign-off 5가지 기준에 **포함되지 않는** 것은?

- [ ] A. 모든 assert PROVEN 또는 정당한 BOUNDED
- [ ] B. 모든 cover COVERED
- [ ] C. Assume이 spec과 1:1 매핑 + 대응 cover
- [ ] D. CPU 시간 < 1시간

??? answer "정답 / 해설"
    **D**. 검증 시간은 sign-off 기준이 아님. 5가지: (1) assert 결과, (2) cover, (3) Assume 감사, (4) COI(블랙박스 영향), (5) Property 완전성. 시간은 효율의 지표지 신뢰성 지표가 아님.
