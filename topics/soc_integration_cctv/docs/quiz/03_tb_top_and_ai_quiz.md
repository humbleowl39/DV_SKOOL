# Quiz — Module 03: TB Top & AI Automation

[← Module 03 본문으로 돌아가기](../03_tb_top_and_ai.md)

---

## Q1. (Remember)

AI 자동화가 가장 효과적인 검증 영역 3가지는?

??? answer "정답 / 해설"
    1. **Coverage gap → targeted sequence 생성** (LLM이 spec + 미커버 영역 보고 sequence 작성)
    2. **RAL 자동 생성** (spec doc → uvm_reg/uvm_reg_field 변환)
    3. **로그/wave 디버그 보조** (long log에서 root cause 후보 식별)

## Q2. (Understand)

AI가 검증할 수 **없는** 영역은?

??? answer "정답 / 해설"
    - **Silent corruption** — 명시적 fail signal 없는 결함
    - **Race condition** — 비결정론적 timing-dependent
    - **Spec ambiguity** — spec 자체가 모호하면 AI도 잘못 해석
    - **새로운 architecture** — 학습 데이터에 없는 novel design

    AI는 hypothesis 제안 + 반복 작업 자동화 ↑, 최종 sign-off는 human inspection.

## Q3. (Apply)

Layered TB Top 설계를 위한 layer 분리는?

??? answer "정답 / 해설"
    - **Layer 1 (Common)**: 모든 SoC에 공통 (clock/reset/power 모델, DRAM 모델, 기본 monitor)
    - **Layer 2 (Common Task)**: CCTV sequence library, virtual sequencer base
    - **Layer 3 (Project-specific)**: 이번 프로젝트 IP들의 agent + 특수 시나리오

    프로젝트 변경 시 Layer 3만 수정 → 재사용성.

## Q4. (Analyze)

LLM에게 sequence 작성을 시킬 때 가장 중요한 input은?

??? answer "정답 / 해설"
    1. **Spec 정확한 인용** (RFC, datasheet, custom spec)
    2. **Existing sequence 예시** (style guide 역할)
    3. **명확한 coverage goal** (what bin to cover)
    4. **Constraint 명시** (어떤 register는 read-only 등)

    위 4개가 input이 부족하면 LLM은 hallucinate하거나 generic sequence만 생성.

## Q5. (Evaluate)

다음 중 AI 자동화 도입이 **위험한** 시나리오는?

- [ ] A. RAL 자동 생성 후 사람 검토
- [ ] B. AI가 생성한 sequence를 검토 없이 회귀에 추가
- [ ] C. AI가 디버그 hypothesis 제안
- [ ] D. AI가 coverage gap 식별

??? answer "정답 / 해설"
    **B**. 검토 없이 회귀에 추가하면 잘못된 sequence가 testbench를 corrupt할 수 있음. 그 sequence가 spec 위반인지 확인 안 됨. AI 결과는 human review 필수 + small set으로 confidence 확인 후 회귀 추가.
