# Module 05 — Adding New Components: 4원칙

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🧪</span>
    <span class="chapter-back-text">RDMA Verification</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 05</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#원칙-1--open-closed-기존-컴포넌트-비침투적-확장">#1 Open-Closed</a>
  <a class="page-toc-link" href="#원칙-2--interface-stability-안정된-인터페이스--객체-기반-통신">#2 Interface Stability</a>
  <a class="page-toc-link" href="#원칙-3--dry-via-analysis-port-reuse">#3 DRY via Analysis Port Reuse</a>
  <a class="page-toc-link" href="#원칙-4--stateless-클래스에-state-추가-금지">#4 Stateless 보존</a>
  <a class="page-toc-link" href="#새-컴포넌트-추가-체크리스트">체크리스트</a>
  <a class="page-toc-link" href="#케이스-스터디--congestion-control-추가">케이스 스터디</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-모듈">다음 모듈</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Apply** Open-Closed / Interface Stability / DRY via AP / Stateless 보존 원칙을 새 컴포넌트 설계에 적용할 수 있다.
    - **Evaluate** 어떤 변경이 기존 컴포넌트를 침투(intrusive)하는지 평가할 수 있다.
    - **Justify** state 가 sequence 가 아니라 sequencer 에 있어야 하는 이유를 설명할 수 있다.

!!! info "사전 지식"
    - [Module 02 — Component 계층](02_component_hierarchy.md) (handler stateless 의 의도)
    - [Module 04 — Analysis Port Topology](04_analysis_port_topology.md) (1:N broadcast)
    - SOLID 원칙 중 Open-Closed 의 일반 개념

!!! danger "❓ 흔한 오해"
    **오해**: "내가 필요한 정보는 driver 안에 있으니 driver 안에 hook 을 추가하자" 가 가장 빠른 길이다.

    **실제**: driver 가 이미 5개 AP 로 broadcasting 하고 있다(M04). hook 추가는 (1) Open-Closed 위반 (driver 코드 변경), (2) DRY 위반 (이미 있는 정보 재계산), (3) Interface Stability 위험 (port 시그니처가 흔들림) — 3 원칙 동시 위반.

## 왜 이 모듈이 중요한가
RDMA-TB 는 수십 명이 동시에 변경하는 코드베이스입니다. "기존 동작을 바꾸지 않으면서 새 기능을 추가한다"는 규율이 깨지면 회귀(regression)가 폭증합니다. 이 4 원칙은 그 규율을 명문화한 것입니다.

> Confluence 출처: [Adding New Components](https://mangoboost.atlassian.net/wiki/spaces/RDMADV/pages/1333297423/Adding+New+Components)

## 핵심 개념

### 원칙 1 — Open-Closed: 기존 컴포넌트 비침투적 확장

**규칙**: 기존 연결 구조(topology)를 수정하지 않고 새 컴포넌트를 추가한다. 새 컴포넌트가 추가된다고 해서 기존 컴포넌트의 동작이 변경되거나 side-effect 가 발생하면 안 된다.

| 상황 | ✅ 올바른 접근 | ❌ 잘못된 접근 |
|------|----------------|----------------|
| 특정 기능에만 필요한 컴포넌트 | 별도의 연결 구조로 독립 추가 | 기존 env 의 connect_phase 에 조건부 분기 |
| 모든 노드에 공통으로 필요 | 기존 계층에 자연스럽게 통합 | — |
| 기존 데이터 흐름 일부가 필요 | Analysis port 구독으로 tap | 기존 컴포넌트 내부에 새 로직 삽입 |

!!! example "예 — Congestion control 모니터 추가"
    잘못된 접근: `vrdma_driver` 에 `if(cc_enabled) ...` 분기 추가
    올바른 접근: `vrdma_cc_monitor` 라는 새 컴포넌트가 `drv.completed_wqe_ap` 와 `cq_handler.cqe_validation_cqe_ap` 를 구독. driver 코드는 한 줄도 안 변함.

### 원칙 2 — Interface Stability: 안정된 인터페이스 + 객체 기반 통신

**규칙**: 컴포넌트 간 인터페이스(TLM port/export)는 고정. 데이터 교환은 transaction object 를 통해서만.

| 변경 방법 | 영향 범위 | 권장? |
|----------|----------|-------|
| Object 에 필드 추가 (`vrdma_base_command` 에 새 필드) | object 만 변경, port 불변 | ✅ |
| 새 transaction class 정의 | 새 컴포넌트만 사용 | ✅ |
| 새 analysis port 추가 | 기존 연결 불변, 새 subscriber 만 | ✅ |
| 기존 port 시그니처 변경 (parameter 타입 변경) | 모든 연결 컴포넌트 수정 필요 | ❌ 금지 |

이 원칙의 결과: AP 시그니처가 한 번 정해지면 "새 필드 추가"로 진화시키지 "타입 변경"으로 진화시키지 않습니다.

### 원칙 3 — DRY via Analysis Port Reuse

**규칙**: 동일한 데이터를 생성하는 로직을 중복 구현하지 말고, 기존 컴포넌트의 AP 를 구독해서 재사용한다.

UVM analysis port 는 1:N broadcast 이므로, 새 subscriber 추가는 기존 연결에 영향을 주지 않습니다.

| 기존 AP | 활용 예시 |
|---------|----------|
| `drv.issued_wqe_ap` | 새 protocol 모니터가 WQE 추적 |
| `drv.completed_wqe_ap` | 새 성능 카운터가 latency 측정 |
| `drv.cqe_ap` | 새 커버리지 collector 가 CQE 샘플링 |
| `drv.qp_reg_ap` / `mr_reg_ap` | 새 리소스 모니터가 lifecycle 추적 |
| `cq_handler.cqe_validation_cqe_ap` | 새 에러 분석기가 CQE 필드 검사 |

!!! warning "안티패턴"
    "내가 필요한 데이터는 driver 내부에 있으니 driver 에 직접 hook 을 추가하자" — 이는 DRY 위반(driver 가 이미 broadcasting 하고 있음) 이자 Open-Closed 위반(driver 코드 변경).

### 원칙 4 — Stateless 클래스에 State 추가 금지

**규칙**: TB 의 일부 클래스는 의도적으로 **stateless** 로 설계되어 있다. 거기에 state 를 추가하면 예측 불가능한 부작용과 테스트 간 오염이 발생한다.

| 클래스 | 설계 의도 | State 추가 시 문제 |
|--------|----------|-------------------|
| `vrdma_send/recv/write/read_handler` | Stateless forwarder — AP 라우팅만 | flush/reset 누락 시 stale state, 기존 forwarding 경로 side-effect |
| `vrdma_top_sequence` | Stateless function set — body() 없는 유틸리티 | 시퀀스 재사용 시 이전 상태 잔존, 멀티노드 state 공유 문제 |
| `vrdma_data_cqe_handler` | Stateless CQE router — 조건부 forwarding | 라우팅 조건이 내부 state 에 의존 → 비결정적 동작 |

#### State 가 필요할 때의 올바른 접근

`vrdma_top_sequence` 와 `vrdma_sequencer` 의 관계가 정답입니다.

```
vrdma_top_sequence (stateless functions)
        │
        │ uses
        ▼
vrdma_sequencer (stateful: wc_error_status[qp][$], debug_wc_flag[qp][$], outstanding 카운터)
```

이 설계가 올바른 4가지 이유:

1. **Sequence 재사용** — `vrdma_top_sequence` 는 state 가 없으므로 여러 테스트에서 자유롭게 상속/재사용. State 는 sequencer 에 바인딩되어 노드별로 격리.
2. **멀티노드 격리** — 각 노드의 `vrdma_sequencer` 가 독립 state. 시퀀스가 `t_seqr` 를 명시적으로 받으므로 노드 간 오염 없음.
3. **Reset / Flush** — sequencer 의 `flush()` / `clearErrorStatus()` 가 모든 inflight 카운터·에러 큐를 초기화. Sequence 는 flush 대상이 아님.
4. **State 소유권 명확** — "누가 이 state 를 관리하는가?" 가 항상 sequencer 로 귀결. 디버깅 시 단일 지점.

> 코드: `lib/base/component/env/agent/sequencer/vrdma_sequencer.svh:19-20, 36, 75-76, 179-181`

## 새 컴포넌트 추가 체크리스트

새 컴포넌트를 추가할 때 아래를 확인:

- [ ] 기존 컴포넌트의 `build_phase` / `connect_phase` 를 수정하지 않고 추가 가능한가?
- [ ] 기존 컴포넌트의 내부 로직(`run_phase`, `EntryPoint` 등)을 수정하지 않는가?
- [ ] 컴포넌트 간 통신이 Object(transaction) 기반인가?
- [ ] 기존 analysis port 를 재사용할 수 있는데 중복 구현하고 있지는 않은가?
- [ ] Stateless 클래스에 state 를 추가하고 있지는 않은가?
- [ ] 새 컴포넌트를 제거해도 기존 TB 가 정상 동작하는가? (opt-in 구조)

> Confluence 출처: [Adding New Components — 체크리스트](https://mangoboost.atlassian.net/wiki/spaces/RDMADV/pages/1333297423/Adding+New+Components)

## 케이스 스터디 — Congestion Control 추가

`lib/ext/component/congestion_control/` 가 위 4 원칙의 좋은 사례입니다.

- **Opt-in** — `lib/ext/` 아래 별도 폴더로 분리. cfg 플래그로 enable/disable.
- **AP 구독** — `vrdma_rtt_scoreboard` 가 driver 의 AP 를 구독 (`E-SB-MATCH-0001`, `0003` 메시지가 거기서 발행됨).
- **Stateless 보존** — congestion 트래커는 sequencer 가 아닌 새 컴포넌트가 보유.
- **기존 연결 불변** — base TB 는 한 줄도 변경되지 않음.

## 핵심 정리

- 4원칙: Open-Closed / Interface Stability / DRY via AP / Stateless 보존
- 핵심 안티패턴: 기존 컴포넌트 내부 수정 / port 시그니처 변경 / driver 데이터 재계산 / handler 에 state 추가
- State 가 필요하면 sequencer (또는 별도 stateful subscriber)에 둔다 — sequence/handler 에 두지 않는다
- 새 컴포넌트가 제거되어도 기존 TB 는 동작해야 한다 — 제거 가능한가? 가 가장 강한 검증

## 다음 모듈
[Module 06 — Error Handling Path](06_error_handling_path.md): 위 4원칙이 에러 처리 경로에서 어떻게 구현되어 있는지.

[퀴즈 풀어보기 →](quiz/05_extension_principles_quiz.md)


--8<-- "abbreviations.md"
