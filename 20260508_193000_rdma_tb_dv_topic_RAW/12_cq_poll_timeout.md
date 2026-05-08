# CQ Poll Timeout


## CQ Poll Timeout
## 
CQ 폴링 중 DUT가 CQE를 생성하지 않아 타임아웃이 발생하는 케이스입니다.
 
## 대표 에러 메시지
## 

 | 
ID
 | | 
심각도
 | | 
메시지
 | 

 | 
 E-DRV-TBERR-0001 
 | | 
ERROR
 | | 
 CQ POLLING TIMEOUT : Unprocessed CQE 
 | 

 | 
 E-DRV-TBERR-0002 
 | | 
ERROR
 | | 
 CQ HANDLER: CQ POLLING TIMEOUT 
 | 

 동작: fatal이 아닌 uvm_shutdown_phase 로 점프하여 시뮬레이션을 graceful 종료합니다.
 
## 발생 메커니즘
## timeout_count) && (!c2h_tracker::active)
 → exceptionTimeout()]]> 
## 타임아웃 조건 (두 가지 동시 충족)
## 

 | 
조건
 | | 
설명
 | 

 | 
 try_cnt > timeout_count 
 | | 
폴링 반복 횟수 초과
 | 

 | 
 !c2h_tracker::active 
 | | 
C2H DMA 활동 없음 (10ms 이상 비활성)
 | 

 핵심: C2H tracker가 active인 동안은 타임아웃이 무한히 지연 됩니다. DUT가 DMA를 계속하고 있으면 타임아웃이 발생하지 않습니다.

## timeout_count 기본값
## 

 | 
호출 위치
 | | 
기본값
 | | 
실효 시간
 | 

 | 
 vrdma_top_sequence::RDMACQPoll 
 | | 
50000
 | | 
~50ms
 | 

 | 
 vrdma_sequence::RDMACQPoll 
 | | 
10000
 | | 
~10ms
 | 

 | 
 vrdma_cq_poll_command::new() 
 | | 
10000
 | | 
~10ms
 | 

 | 
 monitorErrCQ (try_once=1)
 | | 
10000
 | | 
타임아웃 불가
 | 

 
## 로그에서 확인할 정보
## 
## 폴링 중 주기적 로그 (10회마다, ~10us)
## 

 | 
필드
 | | 
의미
 | | 
확인 포인트
 | 

 | 
CQ number
 | | 
폴링 대상 CQ
 | | 
올바른 CQ인지
 | 

 | 
Try Count
 | | 
폴링 반복 횟수
 | | 
timeout_count와 비교
 | 

 | 
unprocessed wqe
 | | 
미처리 CQE 예상 수
 | | 
0이면 카운팅 오류 의심
 | 

 | 
address
 | | 
CQ phase bit 주소
 | | 
DUT가 쓰는 주소와 일치하는지
 | 

 | 
PHASE
 | | 
기대하는 phase bit 값
 | | 
DUT phase와 동기 맞는지
 | 

 | 
TAIL POINTER
 | | 
CQ tail pointer 위치
 | | 
CQ wrap-around 상태 확인
 | 

## 타임아웃 시 출력
## 
## 디버깅 순서
## 
## Step 1: 어떤 CQ에서 타임아웃인지 확인
## 
## Step 2: DUT가 WQE를 처리했는지 확인
## 
## Step 3: CQE가 생성되었는지 확인
## 
## Step 4: Phase bit 동기화 확인
## 
## Step 5: C2H tracker active 상태 확인
## 
## 흔한 원인
## 

 | 
원인
 | | 
증상
 | | 
확인 방법
 | 

 | 
DUT WQE 처리 실패
 | | 
Outstanding WQE가 모두 같은 QP
 | | 
DUT 내부 SQ dequeue 로직
 | 

 | 
Doorbell 미전달
 | | 
WQE 발행 후 첫 CQE부터 안 옴
 | | 
BAR4 SQ_DB 레지스터 쓰기 확인
 | 

 | 
Completion engine 버그
 | | 
패킷은 나갔는데 CQE 미생성
 | | 
DUT completion engine FSM
 | 

 | 
C2H DMA 경로 고장
 | | 
CQE 생성됐으나 host memory 미도착
 | | 
C2H DMA controller 상태
 | 

 | 
Phase bit 불일치
 | | 
폴링 주소는 맞는데 phase 안 맞음
 | | 
CQ depth / wrap 로직
 | 

 | 
CQ base address 불일치
 | | 
아예 다른 주소에 CQE 기록
 | | 
configure_phase CQ 설정 vs DUT
 | 

 | 
Error CQE가 ERR_CQ에 도착
 | | 
정상 CQ 대신 에러 CQ에 기록됨
 | | 
monitorErrCQ 로그 확인
 | 

 | 
unprocessed_cqe_cnt 불균형
 | | 
unsignaled WQE가 잘못 카운트됨
 | | 
signaled/sq_sig_type 설정 확인
 | 


