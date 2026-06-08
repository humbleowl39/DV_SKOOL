---
title: "Quiz — Module 04: UVM 코어 검증 환경"
---

[← Module 04 본문으로 돌아가기](../../04_uvm_core_env/)

---

## Q1. (Remember)

CPU UVM 환경에서 _reference model(ISS)로 expected 결과를 산출_ 하는 책임을 지는 컴포넌트는?

- [ ] A. retire monitor
- [ ] B. predictor
- [ ] C. coverage collector
- [ ] D. driver

<details>
<summary>정답 / 해설</summary>

**B**. predictor 가 reference model(ISS)을 DPI-C 등으로 호출해 "이 명령이 무엇을 했어야 했는가"(expected)를 산출합니다. retire monitor(A)는 코어가 _실제로_ 무엇을 했는지(actual)를 RVFI 로 관찰하고, scoreboard 가 둘을 대조하며, coverage collector(C)는 발생 상황을 셉니다. CPU 코어 검증에서 자극은 메모리의 ELF 로 들어가므로 전통적 driver(D)는 보통 능동 역할이 약합니다.

</details>

## Q2. (Understand)

monitor 의 analysis port 가 "1:N broadcast" 라는 말의 의미와, 그것이 환경 확장에 주는 이점을 설명하라.

<details>
<summary>정답 / 해설</summary>

monitor 가 `ap.write(retire_item)` 을 한 번 호출하면 그 item 이 _연결된 모든 수신자_(predictor·scoreboard·coverage·logger)에 동시에 전달된다는 뜻입니다(publisher/subscriber 분리). monitor 는 누가 듣는지 모르고, 수신자 추가는 _수신자 측에서 connect_ 만 하면 됩니다. 이점은 **새 검증 컴포넌트(예: 새 coverage)를 추가해도 monitor 코드가 불변** 이라는 점 — 결함 발견(scoreboard)과 완전성 측정(coverage)이 같은 retire stream 에서 독립적으로 확장됩니다.

</details>

## Q3. (Apply)

ISS predictor 를 DPI-C 로 통합할 때, monitor 가 만든 retire_item 에 `it.intr`(인터럽트 진입 여부)를 담아 ISS step 에 전달해야 하는 이유는?

<details>
<summary>정답 / 해설</summary>

**RTL-driven lockstep 에서 비동기 인터럽트의 시점을 ISS 에 동기화하기 위해서** 입니다. 인터럽트는 _언제_ 도착하느냐가 비결정적이며, ISS 는 ISA 의미만 알 뿐 RTL 이 어느 명령 경계에서 인터럽트를 받았는지는 모릅니다. RTL 이 `rvfi_intr` 로 "이 명령에서 인터럽트 핸들러에 진입했다"고 알려주면, predictor 가 그 정보를 ISS step 에 전달해 ISS 도 _같은 명령 경계_ 에서 trap 을 산출합니다. 이 전달을 빠뜨리면 ISS 와 RTL 이 서로 다른 명령에서 trap 해 인터럽트 직후부터 체계적으로 발산합니다(이는 RTL 버그가 아니라 TB 동기화 버그).

</details>

## Q4. (Apply)

scoreboard 가 retire 를 하나도 못 받아 비교가 전혀 일어나지 않는다. UVM 환경 결선 관점에서 점검할 두 곳은?

<details>
<summary>정답 / 해설</summary>

1. **`connect_phase` 에서 monitor 의 analysis port ↔ scoreboard 의 analysis_imp connect 누락**: `mon.ap.connect(sb.ap_imp)` 가 빠지면 broadcast 가 scoreboard 에 도달하지 않습니다.
2. **코어 RVFI 가드 미빌드 / virtual interface 미전달**: RVFI define 없이 빌드돼 `rvfi_valid` 가 토글 안 하거나, `rvfi_vif` 가 config_db 로 monitor 에 전달 안 되면 monitor 자체가 retire 를 못 잡아 애초에 broadcast 할 item 이 없습니다.

(즉 "scoreboard 가 안 받는다"는 monitor→scoreboard 결선 또는 monitor 입력(RVFI) 중 하나의 단절을 의미합니다.)

</details>

## Q5. (Analyze)

어떤 팀이 monitor 안에서 직접 ISS 를 호출하고 비교·로깅까지 하는 "한 덩어리" 컴포넌트를 만들었다. 재사용성 관점에서 무엇이 문제이고 어떻게 분해해야 하는가?

- [ ] A. 문제없다 — 컴포넌트가 적을수록 좋다
- [ ] B. 관찰·정답산출·판정·기록이 한 클래스에 묶여, 코어/ISS/coverage 교체 시 매번 monitor 전체를 수정해야 한다 — monitor/predictor/scoreboard/coverage 로 분해해야 한다
- [ ] C. coverage 가 빨라진다
- [ ] D. DPI-C 를 쓸 수 없게 된다

<details>
<summary>정답 / 해설</summary>

**B**. 한 덩어리 monitor 는 네 책임을 묶어 재사용성을 잃습니다. 코어를 바꾸면 RVFI 결선뿐 아니라 ISS·비교 코드까지 영향받고, ISS 교체나 coverage 추가도 monitor 를 다시 손대야 합니다(broadcast 가 없으므로). 올바른 분해는 monitor(RVFI 관찰 → broadcast) / predictor(ISS step → expected) / scoreboard(actual vs expected 순수 비교) / coverage(sample). 그러면 각 변경이 _한 컴포넌트_ 에만 국한됩니다. 이는 "scoreboard 는 transaction 레벨에서 비교"라는 reusable TB 원칙의 적용입니다.

</details>

## Q6. (Evaluate)

predictor 를 별도 컴포넌트로 빼서 scoreboard 를 "순수 비교기"로 만드는 구성과, ISS step 을 scoreboard 안에서 직접 호출하는 구성 중, ISS 를 Spike 에서 ImperasDV 로 교체할 계획이 있다면 어느 쪽이 낫고 왜인가?

<details>
<summary>정답 / 해설</summary>

**predictor 분리형이 낫습니다.**
- predictor 를 분리하면 scoreboard 는 reference model 종류를 모르고 _actual stream 과 expected stream 을 비교_ 만 합니다. ISS 를 Spike→ImperasDV 로 바꿔도 _predictor 만_ 교체하면 되고 scoreboard 코드는 불변입니다.
- 반대로 ISS step 을 scoreboard 안에서 호출하는 합본형은 ISS 인터페이스가 scoreboard 비교 로직과 얽혀 있어, ISS 교체가 scoreboard 까지 흔듭니다.
- 트레이드오프: 합본형은 컴포넌트가 적어 초기 구현이 빠르고, 단일 고정 ISS 로 끝낼 소규모 환경에선 충분할 수 있습니다. 그러나 _ISS 교체·여러 reference model 비교_ 가 예정돼 있다면 분리형이 유지보수 비용을 크게 낮춥니다. 교체 계획이 _있다_ 는 조건에서는 분리형이 정당화됩니다.

</details>
