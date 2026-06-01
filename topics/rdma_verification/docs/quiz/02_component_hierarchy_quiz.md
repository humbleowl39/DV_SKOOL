# Module 02 퀴즈 — Component 계층

본문: [Module 02](../02_component_hierarchy.md)

---

### Q1. (Remember) `lib/base/component/` 의 7개 직속 디렉토리를 나열하시오.
**정답.** `config`, `custom_phase`, `env`, `model`, `pool`, `test`, `util`.
**Why.** 이 7개 디렉토리는 RDMA-TB 컴포넌트를 역할별로 분리한 최상위 분류다. `config`는 검증 설정 오브젝트, `env`는 계층 컴포넌트, `pool`은 QP/MR 리소스 관리, `test`는 테스트 클래스, `util`은 공통 유틸리티를 담는다. 이 구조를 머릿속에 그려 두면, 에러 메시지나 로그에서 컴포넌트 이름만 봐도 어느 디렉토리 파일인지 즉시 추론할 수 있어 디버깅 속도가 크게 향상된다.

### Q2. (Understand) `agent/` 안의 driver / handler / sequencer 분리의 의도를 한 줄로 설명하시오.
**정답.** driver = stateful(WQE 발행, outstanding 추적), handler = stateless forwarder(opcode 별 라우팅), sequencer = per-QP state owner. 책임을 분리해 시퀀스 재사용·flush 시 stale state 누적을 방지.
**Why.** driver가 "WQE를 발행하고 outstanding을 추적"하는 stateful 역할을 맡는 반면, handler는 수신된 verb를 opcode별 AP로 라우팅하기만 하고 자체 state를 갖지 않는다. 만약 handler에 state가 생기면 재사용 시 stale state가 누적되어 다음 테스트에 오염을 남긴다. sequencer는 per-QP 에러 상태(`wc_error_status`)처럼 노드별로 관리되어야 하는 state를 보유한다. 이 삼자 분리는 Module 05의 Stateless 보존 원칙이 실제 코드에 반영된 형태다.

### Q3. (Apply) `E-SB-MATCH-0003` 에러를 보았다. 어느 파일을 먼저 열어야 하는가?
**정답.** `lib/base/component/env/data_env/vrdma_1side_compare.svh` (또는 2side/imm 의 같은 ID — 컨텍스트로 분리). prefix `E-SB-MATCH` → comparator(data_env).
**Why.** 에러 ID prefix는 발생 컴포넌트를 인코딩한 레이블이다. `E-SB-MATCH`는 scoreboard의 match 비교기, 즉 `data_env` 내 comparator임을 뜻한다. 1side/2side/imm 세 comparator가 동일 prefix를 공유하므로, 에러 메시지 본문의 instance 이름으로 어느 comparator인지 좁혀야 한다. 파일을 열기 전에 prefix만으로 디렉토리를 좁히는 이 습관이 디버깅 시간을 절반으로 단축한다.

### Q4. (Analyze) `pool/vrdma_qpool.svh` 와 `pool/vrdma_pool.svh` 의 관계를 추론하시오.
**정답.** `vrdma_pool` 이 통합 풀(QP/MR/PD/CQ/SQ/RQ), `vrdma_qpool` 은 QP 만 별도로 lifecycle 을 자세히 다룬다고 추론(파일 분리 패턴 + Confluence 설명). 정확한 관계는 코드에서 확인 필요.
**Why.** 이 문제는 의도적으로 **추론** 훈련을 위해 설계되었다. 두 파일의 이름 패턴과 Confluence 설명만으로 관계를 추정할 수 있지만, 코드를 직접 읽기 전까지는 단정해서는 안 된다. "추론임을 명시"하는 습관이 anti-hallucination의 핵심이다 — 확인하지 않은 구조를 사실처럼 서술하면 디버깅 오판으로 이어진다. 실무에서도 파일 이름만 보고 구현을 가정하지 말고 반드시 코드를 열어야 한다.

### Q5. (Evaluate) "handler 는 어차피 forwarder 니까 driver 안에 인라인하자" 는 제안을 평가하시오.
**정답.** 잘못됨. Stateless forwarder 분리는 (1) 새 op type 추가 시 새 handler 만 추가하면 됨(Open-Closed), (2) handler 별 AP 구독자가 다를 수 있음(DRY via AP), (3) driver 가 비대해지지 않음. 인라인 하면 4 원칙 중 3 개 위반.
**Why.** handler를 driver에 인라인하면 새 opcode가 추가될 때마다 driver 코드를 수정해야 하므로 Open-Closed 원칙에 위반된다. 또한 opcode별로 서로 다른 AP 구독자가 존재하는데, driver가 그 라우팅을 전담하면 DRY 원칙도 깨진다. 무엇보다 driver는 이미 WQE 발행과 outstanding 추적이라는 복잡한 stateful 역할을 담당하고 있으므로, 여기에 라우팅 로직까지 더하면 단일 책임 원칙(SRP)까지 위반된다.

### Q6. (Apply) `F-CQHDL-TBERR-0003` 에러 ID prefix 만 보고 어느 파일에서 발생했는지 답하시오.
**정답.** `vrdma_cq_handler.svh` (`F-CQHDL` = `vrdma_cq_handler`). 정확히 line 244.
**Why.** `F-CQHDL`은 "Fatal - CQ Handler"의 약어로, prefix 디코딩 규칙을 알면 해당 파일로 즉시 이동할 수 있다. 이 prefix 매핑은 Module 02의 컴포넌트-에러 prefix 표에 정리되어 있으며, 실제 디버깅에서 grep한 에러 ID를 파일로 매핑하는 첫 단계가 된다. prefix를 무시하고 전체 소스를 검색하면 수십 분을 낭비할 수 있다.

### Q7. (Apply) `vrdma_sequencer::wc_error_status[5][0]` 가 의미하는 바는?
**정답.** QP 5 번의 첫(시간순 첫) 에러 CQE 의 `wc_status`. Module 11 의 expected_error 검증 패턴에서 활용.
**Why.** `wc_error_status`는 per-QP 에러 이력을 시간순으로 기록하는 큐다. `[5][0]`은 QP 5번에 발생한 첫 번째 에러 CQE의 status를 의미한다. Module 11의 의도된 에러 테스트 패턴에서는 시나리오 실행 후 `wc_error_status[qp][0]`을 읽어 예상한 에러 코드와 일치하는지 검증한다. 이 필드를 모르면 "에러가 발생했는지"만 확인하고 "어떤 에러인지"를 검증하지 못하게 된다.

### Q8. (Create) 새 검증 컴포넌트 `vrdma_latency_collector` 를 추가해 issue→complete latency 를 수집한다. 어느 디렉토리에 두는가? 어떤 AP 를 구독하는가?
**정답.** `lib/ext/component/perf/` 또는 `lib/base/component/env/data_env/` (옵션이면 ext, 공통이면 base). 구독 AP: `drv.issued_wqe_ap` (start), `drv.completed_wqe_ap` (end). 두 transaction id 매칭으로 latency 산출.
**Why.** latency 수집이 모든 시뮬에서 필요한 공통 기능이면 `lib/base`에, 특정 성능 분석 목적으로만 쓰이면 `lib/ext`에 둔다. AP 선택에서 핵심은 "WQE 발행 시점"과 "WQE 완료 시점"을 각각 포착해야 한다는 점이다. `issued_wqe_ap`는 driver가 WQE를 발행할 때, `completed_wqe_ap`는 완료 확인 시 broadcast된다. 두 이벤트를 transaction ID로 매칭하면 per-WQE latency를 계산할 수 있으며, 이 접근법은 기존 driver/handler 코드를 전혀 수정하지 않는다.
