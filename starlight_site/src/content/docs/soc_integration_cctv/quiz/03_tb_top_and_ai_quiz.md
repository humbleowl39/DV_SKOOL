---
title: "Quiz — Module 03: TB Top & AI Automation"
---

[← Module 03 본문으로 돌아가기](../../03_tb_top_and_ai/)

---

## Q1. (Remember)

AI 자동화가 가장 효과적인 검증 영역 3가지는?

<details>
<summary>정답 / 해설</summary>

1. **Coverage gap → targeted sequence 생성** (LLM이 spec + 미커버 영역 보고 sequence 작성)
2. **RAL 자동 생성** (spec doc → uvm_reg/uvm_reg_field 변환)
3. **로그/wave 디버그 보조** (long log에서 root cause 후보 식별)

이 세 영역의 공통점은 모두 "반복적이고 패턴이 명확한 작업"이라는 것이다. Coverage gap 분석은 미커버 bin 목록과 spec을 대조하는 반복 작업이고, RAL 생성은 spec 표의 레지스터 필드 정보를 SystemVerilog 클래스로 변환하는 정형화된 변환이며, 로그 디버그는 수천 줄의 텍스트에서 특정 패턴을 찾는 검색 작업이다. AI는 이런 구조화된 반복 작업에서 엔지니어의 수작업 시간을 줄여주고, 엔지니어는 AI가 생성한 결과를 검토하고 판단하는 역할에 집중할 수 있게 된다.

</details>
## Q2. (Understand)

AI가 검증할 수 **없는** 영역은?

<details>
<summary>정답 / 해설</summary>

- **Silent corruption** — 명시적 fail signal 없는 결함
- **Race condition** — 비결정론적 timing-dependent
- **Spec ambiguity** — spec 자체가 모호하면 AI도 잘못 해석
- **새로운 architecture** — 학습 데이터에 없는 novel design

AI는 hypothesis 제안 + 반복 작업 자동화 ↑, 최종 sign-off는 human inspection.

AI가 이 영역들에서 한계를 보이는 이유는, 모두 "정답이 텍스트나 패턴으로 명확히 정의되지 않는" 문제이기 때문이다. Silent corruption은 에러 신호가 없으므로 AI가 로그를 읽어도 이상 징후 자체를 감지하기 어렵고, race condition은 재현 조건이 seed나 타이밍에 의존하여 인과관계를 확정하기 어렵다. Spec ambiguity는 AI가 모호한 문장을 자신 있게 한 가지 방향으로 해석해 잘못된 시퀀스를 생성할 위험이 있다. 결국 AI가 강한 영역은 "명확한 입력 → 명확한 출력"이 있는 작업이고, 판단과 해석이 필요한 영역은 여전히 엔지니어의 몫이다.

</details>
## Q3. (Apply)

Layered TB Top 설계를 위한 layer 분리는?

<details>
<summary>정답 / 해설</summary>

- **Layer 1 (Common)**: 모든 SoC에 공통 (clock/reset/power 모델, DRAM 모델, 기본 monitor)
- **Layer 2 (Common Task)**: CCTV sequence library, virtual sequencer base
- **Layer 3 (Project-specific)**: 이번 프로젝트 IP들의 agent + 특수 시나리오

프로젝트 변경 시 Layer 3만 수정 → 재사용성.

이 계층 구조가 실제 프로젝트에서 중요한 이유는 변경의 영향 범위를 최소화하기 때문이다. Layer 1은 clock/reset/DRAM처럼 모든 SoC에 공통인 인프라이므로 한 번 검증되면 수년간 재사용된다. Layer 2의 CCTV sequence library는 새 프로젝트에서 새 IP가 추가되어도 그대로 사용 가능하다. Layer 3만 프로젝트마다 바뀌므로 전체 TB를 처음부터 다시 작성하는 비용 없이 빠르게 새 SoC를 검증할 수 있다. 이 분리가 없으면 매 프로젝트마다 동일한 infrastructure 코드를 반복 작성하게 되고, 각 복사본 간 버그가 다르게 쌓이는 기술 부채가 발생한다.

</details>
## Q4. (Analyze)

LLM에게 sequence 작성을 시킬 때 가장 중요한 input은?

<details>
<summary>정답 / 해설</summary>

1. **Spec 정확한 인용** (RFC, datasheet, custom spec)
2. **Existing sequence 예시** (style guide 역할)
3. **명확한 coverage goal** (what bin to cover)
4. **Constraint 명시** (어떤 register는 read-only 등)

위 4개가 input이 부족하면 LLM은 hallucinate하거나 generic sequence만 생성.

LLM의 출력 품질이 입력 품질에 정비례한다는 원칙이 검증 영역에서도 동일하게 적용된다. Spec 없이 "DVFS sequence 작성해줘"라고 요청하면 LLM은 일반적인 레지스터 write 패턴만 생성하고, 이 설계 고유의 voltage-frequency 전환 순서나 settling time 요구사항을 모른다. 기존 sequence 예시를 제공하면 프로젝트의 코딩 스타일과 네이밍 컨벤션을 학습할 수 있고, coverage goal을 명시하면 "어느 bin을 채우려는 것인지"를 알고 타겟화된 코드를 생성한다. Constraint 명시는 read-only 레지스터에 write를 시도하는 잘못된 sequence 생성을 방지한다. 결국 "좋은 프롬프트 = 좋은 spec + 좋은 예시 + 명확한 목표"라는 공식이 성립한다.

</details>
## Q5. (Evaluate)

다음 중 AI 자동화 도입이 **위험한** 시나리오는?

- [ ] A. RAL 자동 생성 후 사람 검토
- [ ] B. AI가 생성한 sequence를 검토 없이 회귀에 추가
- [ ] C. AI가 디버그 hypothesis 제안
- [ ] D. AI가 coverage gap 식별

<details>
<summary>정답 / 해설</summary>

**B**. 검토 없이 회귀에 추가하면 잘못된 sequence가 testbench를 corrupt할 수 있음. 그 sequence가 spec 위반인지 확인 안 됨. AI 결과는 human review 필수 + small set으로 confidence 확인 후 회귀 추가.

A(RAL 자동 생성 후 사람 검토), C(디버그 hypothesis 제안), D(coverage gap 식별)는 모두 AI가 초안을 만들고 사람이 최종 판단하는 안전한 구조이다. B가 위험한 이유는 "검토 없이"라는 조건 때문이다. AI가 생성한 sequence는 spec을 정확히 반영하지 못하거나 존재하지 않는 레지스터를 참조하거나, 올바르지 않은 타이밍 가정을 포함할 수 있다. 이 sequence가 회귀에 들어가면 기존에 통과하던 테스트가 오염되거나, 잘못된 시나리오가 통과로 오인되어 실리콘까지 결함이 숨어드는 최악의 결과를 낳는다. AI는 반드시 "제안자" 역할에 머물러야 하고, "최종 결정자"는 엔지니어이어야 한다.

</details>
