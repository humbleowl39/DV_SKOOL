# Error Handling Path


## Error Handling Path
## 
에러 발생 시 TB 각 컴포넌트의 예외처리 경로와 체커 비활성화 방법을 기술합니다.
 
## 전체 에러 처리 흐름
## 
## 시작점: 시퀀스에서 에러 QP Destroy
## systemverilog 

 | 
파라미터
 | | 
값
 | | 
설명
 | 

 | 
 err 
 | | 
 0 (기본)
 | | 
정상 QP destroy — outstanding 체크 시 fatal
 | 

 | 
 err 
 | | 
 1 
 | | 
에러 QP destroy — outstanding 허용, flush 수행
 | 

 
## 경로 1: Driver → QP Error State
## 
 vrdma_sq_destroy_command.err → vrdma_driver::RDMASQDestroy :
 
 이후 드라이버 영향: 

- 
 EntryPoint → chkSQErrQP(cmd) → qp.isErrQP() == 1 → 해당 QP로의 모든 이후 command skip (warning 로그 후 return)

- 
- 
 completeOutstanding(cmd) → !t_qp.isErrQP() 일 때만 completed_wqe_ap.write(cmd) → 에러 QP의 WQE는 스코어보드에 전달되지 않음 

- 
 
## 경로 2: CQ Handler → Error CQE
## 
DUT에서 에러 CQE가 발생하면 (예: IB_WC_REM_ACCESS_ERR ):
 
 expected_error 사용법: 
 systemverilog 
## 경로 3: Error CQ 백그라운드 모니터링
## 
 enable_error_cq_poll static 플래그로 비활성화 가능:
 systemverilog 
## 컴포넌트별 에러 시 동작
## 
## Data Env (Comparators)
## 

 | 
컴포넌트
 | | 
에러 감지 조건
 | | 
동작
 | 

 | 
 vrdma_1side_compare 
 | | 
 qp.isErrQP() \|\| err_enabled at deregisterQP
 | | 
 flushQP() — 해당 QP의 pending write/read 큐 전체 삭제
 | 

 | 
 vrdma_2side_compare 
 | | 
 qp.isErrQP() \|\| err_enabled at deregisterQP
 | | 
 flushQP() — 해당 QP의 send/recv tracker 전체 삭제
 | 

 | 
 vrdma_imm_compare 
 | | 
 qp.isErrQP() \|\| err_enabled at deregisterQP
 | | 
 flushQP() — 해당 QP의 send/cqe tracker 전체 삭제
 | 

 err_enabled static flag:
 systemverilog 
## DMA Env (C2H Tracker)
## 

 | 
조건
 | | 
동작
 | 

 | 
 qp.isErrQP() \|\| err_enabled at deregisterQP
 | | 
 is_err_qp_registered[node][qp] = 1 — 해당 QP를 에러 등록
 | 

 | 
 processC2hTransaction — QP 매칭 실패
 | | 
 is_err_qp_registered.size() > 0 이면 skip (fatal 대신)
 | 

 | 
 check_phase — outstanding 잔존
 | | 
 qp.isErrQP() \|\| err_enabled 이면 fatal 대신 경고
 | 

 err_enabled static flag:
 systemverilog 
## Network Env (Packet Monitors)
## 

 | 
컴포넌트
 | | 
방법
 | | 
동작
 | 

 | 
 vrdma_pkt_base_monitor 
 | | 
 turnOff() 
 | | 
 turn_off = 1 — 패킷 처리 비활성화
 | 

 | 
 vrdma_pkt_base_monitor 
 | | 
 turnOn() 
 | | 
 turn_off = 0 — 패킷 처리 재활성화
 | 

 | 
 vrdma_ops_monitor 
 | | 
상속
 | | 
 turnOff() 시 OPS 프로토콜 체크 중단
 | 

 | 
 vrdma_rc_monitor 
 | | 
상속
 | | 
 turnOff() 시 RC 프로토콜 체크 중단
 | 

## vrdma_cfg (글로벌 체커 제어)
## 

 | 
필드
 | | 
기본값
 | | 
설명
 | 

 | 
 has_dma_chk 
 | | 
YES
 | | 
DMA 체커 enable/disable
 | 

 | 
 has_packet_chk 
 | | 
YES
 | | 
패킷 체커 enable/disable
 | 

 | 
 has_data_chk 
 | | 
YES
 | | 
데이터 체커 enable/disable
 | 

현재 로그용으로만 사용 ( start_of_simulation_phase 에서 출력). 향후 체커 조건부 연결에 활용 예정.
 
## 에러 테스트 시퀀스 작성 패턴
## systemverilog 0) begin
 $display("Error status: %s", t_seqr.wc_error_status[qp_num][0].name());
end

// 5. 에러 QP 정리 (err=1)
this.RDMAQPDestroy(.t_seqr(seqr), .qp_num(qp_num), .err(1));
// → 각 comparator/tracker가 flushQP() 수행]]> 
## Static Flag 요약
## 

 | 
Flag
 | | 
위치
 | | 
기본값
 | | 
영향 범위
 | 

 | 
 vrdma_1side_compare::err_enabled 
 | | 
data_env
 | | 
0
 | | 
1side comparator — 모든 QP deregister 시 flush
 | 

 | 
 vrdma_2side_compare::err_enabled 
 | | 
data_env
 | | 
0
 | | 
2side comparator — 동일
 | 

 | 
 vrdma_imm_compare::err_enabled 
 | | 
data_env
 | | 
0
 | | 
IMM comparator — 동일
 | 

 | 
 vrdma_c2h_tracker::err_enabled 
 | | 
dma_env
 | | 
0
 | | 
C2H tracker — 매칭 실패 시 skip + deregister 시 에러 등록
 | 

 | 
 vrdma_cq_handler::enable_error_cq_poll 
 | | 
agent
 | | 
1
 | | 
Error CQ 백그라운드 폴링 on/off
 | 

 | 
 vrdma_pkt_base_monitor::turn_off 
 | | 
network_env
 | | 
0
 | | 
패킷 모니터 on/off (turnOn/turnOff로 제어)
 | 


