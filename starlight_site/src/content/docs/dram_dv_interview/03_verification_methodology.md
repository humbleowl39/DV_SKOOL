---
title: "03 — 검증 방법론"
pagefind: false
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** UVM의 component 계층·phase·factory·config_db·RAL·TLM이 각각 왜 존재하는지 설명한다.
- **Differentiate** functional coverage와 code coverage를 구분하고 언제 무엇을 신뢰할지 판단한다.
- **Evaluate** "검증이 끝났다(sign-off)"를 무엇으로 판단하는지 기준을 정당화한다.
- **Apply** reference model 전략(golden / dual model)을 검증 대상에 맞게 적용한다.
:::

---

## 1. UVM은 왜 이렇게 생겼나

UVM을 "외운 구조"가 아니라 *왜 그렇게 나뉘었나*로 설명할 수 있어야 한다.

- **component 계층 + phase**: build → connect → run → report 순서로 테스트벤치를 *조립하고 → 연결하고 → 돌리고 → 정리*한다. build/connect를 분리한 이유는 "객체 생성"과 "객체 연결"의 의존성을 끊어 재사용을 가능케 하기 위해서다.
- **factory**: 컴포넌트를 이름으로 생성/오버라이드해 *테스트별로 구조를 바꾸되 코드를 안 건드리게* 한다.
- **config_db**: 설정을 계층 경로로 주입해 *동작을 바꾸되 구조를 안 바꾸게* 한다. (factory=구조, config_db=동작)
- **RAL (Register Abstraction Layer)**: 레지스터를 추상 객체로 다뤄 물리 주소 의존성을 제거한다. — 04장의 OTP Abstraction Layer가 바로 이 아이디어를 OTP에 적용한 것.
- **TLM port**: 컴포넌트 간 트랜잭션을 추상 채널로 주고받아 monitor↔scoreboard를 느슨하게 결합한다.

## 2. Coverage — 무엇을 믿을 것인가

검증의 완성도는 테스트 개수가 아니라 **coverage closure**다.

- **code coverage**: RTL의 line·toggle·FSM·branch가 실행됐나. *"코드가 돌긴 했나"*를 본다.
- **functional coverage**: 의도한 *기능 시나리오*(covergroup/coverpoint/cross)가 일어났나. *"의미 있는 corner를 쳤나"*를 본다.

둘은 보완 관계다. code coverage 100%여도 functional corner를 못 쳤을 수 있고, 그 반대도 가능하다. 그래서 sign-off는 둘 다 본다. constrained-random으로 안 닿는 corner는 directed test나 constraint 튜닝으로 닫고, 도달 불가능한 bin은 waiver 근거를 문서화한다.

## 3. "검증이 끝났다"를 어떻게 판단하나

Sign-off는 DRAM DV 공고의 핵심 책임이다. "언제 끝인가"에 대한 답은 단일 지표가 아니라 *기준의 집합*이다.

1. code + functional coverage closure (목표치 도달 + 미달 bin waiver)
2. verification plan의 모든 항목이 테스트로 매핑됨
3. regression이 clean (전 seed pass)
4. 모든 assertion(SVA) pass, 미발화 assertion 원인 규명
5. negative/보안/corner 시나리오까지 bin으로 관리됨

이 다섯을 충족하고 그 근거를 문서로 남길 수 있을 때 비로소 "DB를 책임지고 내보낼 수 있다"고 말한다.

## 4. Reference model 전략

스코어보드가 DUT 출력을 무엇과 비교하느냐가 검증의 신뢰도를 결정한다.

- **golden(functional) model**: bit-accurate한 정답 모델. translation·mapping 무결성처럼 *정확성*을 본다.
- **dual model**: golden에 더해 **ideal 성능 모델**을 둔다. ideal은 이론적 best(miss 없음·최소 latency)를 정의하고, DUT와 ideal의 gap이 곧 *성능 개선 여지*다. (04장 MMU 사례에서 TLB miss ratio 초과 구간을 이 방식으로 발굴했다.)
- **DRAM controller의 경우**: command/timing 스코어보드로 발행 command 순서와 timing 제약 위반을 체크하고, data integrity는 메모리 모델과 비교한다.

## 5. SVA로 protocol/timing을 거는 법

DRAM controller 검증에서 SVA는 timing 제약과 command 순서를 *연속적으로* 감시한다.

- assertion과 cover property는 짝이다 — assertion은 "위반 없음"을, cover는 "그 상황이 실제로 일어났음"을 보장한다.
- `disable iff (reset)`로 리셋 중 거짓 발화를 막고, `$past`·`|->`(overlapping)·`|=>`(non-overlapping)로 cycle 관계를 표현한다.
- 예: tRCD 위반 감시 — ACT 후 tRCD cycle 이전에 RD/WR이 오면 fail. 이때 동일 조건의 cover로 "tRCD 경계 케이스를 실제로 쳤는지"까지 확인한다.

이것이 02장에서 말한 functional timing 검증의 실체다 — STA(physical)와 레이어가 다르다는 점을 다시 상기하라.

:::note[다음 단계]
이 방법론들이 실제 프로젝트에서 어떻게 적용·디버깅됐는지는 [04 — 프로젝트 심화 & 디버깅](../04_project_deepdive/)에서 STAR로 정리한다.
:::
