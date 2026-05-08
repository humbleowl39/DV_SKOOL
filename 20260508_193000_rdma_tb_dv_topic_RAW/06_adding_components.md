# Adding New Components


## Adding New Components
## 
새로운 UVM 컴포넌트를 TB에 추가할 때 반드시 지켜야 하는 아키텍처 원칙입니다.
 
## 원칙 1: Open-Closed Principle — 기존 컴포넌트에 대한 비침투적 확장
## 
 기존 연결 구조(topology)를 수정하지 않고 새 컴포넌트를 추가해야 합니다. 

새 컴포넌트가 추가된다고 해서 기존 컴포넌트의 동작이 변경되거나 side-effect가 발생하는 구조는 지양합니다. 기존 컴포넌트의 build_phase, connect_phase, 내부 로직을 수정해야 한다면, 그 변경이 정말로 모든 하위 컴포넌트에 공통으로 필요한 것인지 먼저 검토합니다.

 | 
상황
 | | 
올바른 접근
 | | 
잘못된 접근
 | 

 | 
특정 기능에만 필요한 컴포넌트
 | | 
별도의 연결 구조로 독립 추가
 | | 
기존 env의 connect_phase에 조건부 분기 추가
 | 

 | 
모든 노드에 공통으로 필요
 | | 
기존 계층에 자연스럽게 통합
 | | 
—
 | 

 | 
기존 데이터 흐름 일부가 필요
 | | 
Analysis port 구독으로 tap
 | | 
기존 컴포넌트 내부에 새 로직 삽입
 | 

 
## 원칙 2: Interface Stability — 안정된 인터페이스와 메시지 기반 통신
## 
 컴포넌트 간 인터페이스(TLM port/export)는 고정되어야 하며, 데이터 교환은 Object(transaction)를 통해 이루어져야 합니다. 

컴포넌트의 public API(port 시그니처)가 변경되면 연결된 모든 컴포넌트에 파급됩니다. 새로운 정보를 전달해야 할 때는 기존 Object에 필드를 추가하거나 새 Object 타입을 정의하여 해결합니다.

 | 
방법
 | | 
설명
 | | 
영향 범위
 | 

 | 
Object에 필드 추가
 | | 
기존 vrdma_base_command 에 새 필드
 | | 
Object만 변경, 포트/컴포넌트 불변
 | 

 | 
새 Object 타입 정의
 | | 
새 transaction class 생성
 | | 
새 컴포넌트만 사용
 | 

 | 
새 analysis port 추가
 | | 
기존 컴포넌트에 새 AP 추가
 | | 
기존 연결 불변, 새 구독자만 연결
 | 

 | 
기존 port 시그니처 변경
 | | 
파라미터 타입 변경
 | | 
 모든 연결 컴포넌트 수정 필요 — 금지 
 | 

 
## 원칙 3: DRY via Analysis Port Reuse — 기존 AP를 활용한 중복 방지
## 
 동일한 데이터를 생성하는 로직을 중복 구현하지 말고, 기존 컴포넌트의 analysis port를 구독하여 재사용합니다. 

UVM analysis port는 1:N broadcast 구조이므로, 새 subscriber를 추가해도 기존 연결 구조에 영향을 주지 않습니다. 이미 driver, scoreboard, CQ handler가 브로드캐스팅하는 데이터를 새 컴포넌트에서도 필요하다면 해당 AP에 연결하면 됩니다.

 | 
기존 AP
 | | 
브로드캐스트 데이터
 | | 
활용 예시
 | 

 | 
 drv.issued_wqe_ap 
 | | 
발행된 WQE
 | | 
새 프로토콜 모니터가 WQE 추적
 | 

 | 
 drv.completed_wqe_ap 
 | | 
완료된 WQE
 | | 
새 성능 카운터가 latency 측정
 | 

 | 
 drv.cqe_ap 
 | | 
CQE
 | | 
새 커버리지 collector가 CQE 샘플링
 | 

 | 
 drv.qp_reg_ap / mr_reg_ap 
 | | 
QP/MR 등록 이벤트
 | | 
새 리소스 모니터가 lifecycle 추적
 | 

 | 
 cq_handler.cqe_validation_cqe_ap 
 | | 
디코딩된 CQE
 | | 
새 에러 분석기가 CQE 필드 검사
 | 

 
## 원칙 4: Respect Component Statefulness — Stateless 클래스에 State 추가 금지
## 
 Stateless로 설계된 클래스에 상태(state)를 추가하면 안 됩니다. 

TB 내 일부 클래스는 의도적으로 stateless(무상태)로 설계되어 있습니다. 이들은 입력을 받아 변환/전달만 수행하고, 내부에 트랜잭션 히스토리나 카운터를 유지하지 않습니다. 이런 클래스에 state를 추가하면 예측 불가능한 부작용과 테스트 간 오염이 발생합니다.

 | 
클래스
 | | 
설계 의도
 | | 
State 추가 시 문제
 | 

 | 
 vrdma_send/recv/write/read_handler 
 | | 
Stateless forwarder — AP 간 라우팅만 수행
 | | 
flush/reset 누락 시 stale state, 기존 forwarding 경로에 side-effect
 | 

 | 
 vrdma_top_sequence 
 | | 
Stateless function set — body() 없는 유틸리티
 | | 
시퀀스 재사용 시 이전 상태 잔존, 멀티노드 간 state 공유 문제
 | 

 | 
 vrdma_data_cqe_handler 
 | | 
Stateless CQE router — 조건부 포워딩만 수행
 | | 
라우팅 조건이 내부 state에 의존하면 비결정적 동작
 | 

## State가 필요한 경우의 올바른 접근
## 
현재 TB에서 이 패턴이 적용된 실제 사례: vrdma_top_sequence 와 vrdma_sequencer 의 관계.

 vrdma_top_sequence 는 stateless 함수 세트이지만, RDMA operation의 inflight 추적이 필요합니다. 이 state는 시퀀스가 아닌 vrdma_sequencer 에 저장됩니다:
 
 이 설계가 올바른 이유: 

 | 
관점
 | | 
설명
 | 

 | 
 Sequence 재사용 
 | | 
 vrdma_top_sequence 는 state가 없으므로 여러 테스트에서 자유롭게 상속/재사용 가능. State는 sequencer에 바인딩되어 노드별로 격리됨
 | 

 | 
 멀티노드 격리 
 | | 
각 노드의 vrdma_sequencer 가 독립적인 state를 관리. 시퀀스가 t_seqr 를 명시적으로 받으므로 노드 간 state 오염 없음
 | 

 | 
 Reset/Flush 
 | | 
Sequencer의 flush() 가 모든 inflight 카운터와 에러 큐를 초기화. Sequence는 state가 없으므로 flush 대상이 아님
 | 

 | 
 State 소유권 명확 
 | | 
"누가 이 state를 관리하는가?"가 항상 sequencer로 귀결. 디버깅 시 state 추적이 단일 지점
 | 

 
## 체크리스트
## 
새 컴포넌트 추가 시 아래 항목을 확인합니다:
 
 
 7 
 46898775-86b8-42da-b107-6a828b42f16f 
 incomplete 
 기존 컴포넌트의 build_phase/connect_phase를 수정하지 않고 추가 가능한가? 
 
 
 8 
 40c5164a-1f95-44e4-9edd-27fa078b4d77 
 incomplete 
 기존 컴포넌트의 내부 로직(run_phase, EntryPoint 등)을 수정하지 않는가? 
 
 
 9 
 36e83c8b-3da1-42df-b506-d900d3c3e30a 
 incomplete 
 컴포넌트 간 통신이 Object(transaction) 기반인가? 
 
 
 10 
 b13ccf5e-dcfd-4026-a8de-7f071e9dc88a 
 incomplete 
 기존 analysis port를 재사용할 수 있는데 중복 구현하고 있지는 않은가? 
 
 
 11 
 9dedf726-f69f-4853-8dbe-430f78733d42 
 incomplete 
 Stateless 클래스에 state를 추가하고 있지는 않은가? 
 
 
 12 
 20d23814-b8d2-4142-bd7a-b76937bd8318 
 incomplete 
 새 컴포넌트를 제거해도 기존 TB가 정상 동작하는가? (opt-in 구조) 
 
 
