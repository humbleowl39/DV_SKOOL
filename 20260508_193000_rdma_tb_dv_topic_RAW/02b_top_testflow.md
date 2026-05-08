# Test Flow


## Test Flow
## 
RDMA IP-top 테스트의 UVM phase별 실행 흐름과 시퀀스 라이프사이클을 기술합니다.
 
## 전체 흐름 요약
## 
## Phase별 상세
## 
## 1. build_phase (function)
## 
## 2. connect_phase (function)
## 
## 3. reset_phase (task)
## 
## 4. configure_phase (task)
## 
## 5. post_configure_phase (task) — HW 초기화 자동 실행
## 
 vrdma_init_seq 가 default_sequence 로 자동 시작됩니다.
 
## 6. main_phase (task) — 테스트 실행
## 
 백그라운드 태스크 (agent 내부): 
 
 드라이버 (run_phase에서 이미 시작됨): 
 
 테스트 시퀀스 (concrete test에서): 
 
## 7. shutdown_phase (task)
## 
## 8. check_phase (function)
## 
## 시퀀스 실행 패턴
## 
## 패턴 1: Default Sequence (자동 시작)
## 
초기화에 사용됩니다. Agent가 post_configure_phase 에 vrdma_init_seq 를 default로 등록하면, UVM이 해당 phase에서 자동으로 생성/시작합니다.
 
## 패턴 2: start_item / finish_item (멀티노드 타겟팅)
## 
 vrdma_top_sequence 의 Verb 함수에서 사용됩니다. .sequencer(t_seqr) 파라미터로 특정 노드의 시퀀서를 명시적으로 지정 합니다.
 systemverilog 
## 패턴 3: CQ Polling (직접 호출)
## 
CQ 폴링은 start_item/finish_item을 사용하지 않습니다 . 시퀀서의 cq_handler를 직접 호출합니다.
 systemverilog 
## 패턴 4: 테스트 레벨 시퀀스 시작
## 
Concrete 테스트에서 시퀀스를 생성하고 top_vseqr 에서 시작합니다.
 
## 시퀀서 계층과 시퀀스 매핑
## 
 핵심: vrdma_top_sequence 는 top_vseqr 에서 실행되지만, 개별 command는 .sequencer(t_seqr) 로 **특정 노드의 rdma_seqr **에 직접 라우팅됩니다.
 
## 테스트 클래스 구조
## 
 테스트 작성 패턴: 

- 
 rdma_base_test (또는 중간 base) 상속

- 
- 
 main_phase 또는 run_sanity 오버라이드

- 
- 
시퀀스 객체 생성 → 파라미터 설정 → randomize → start(top_vseqr) 

- 

