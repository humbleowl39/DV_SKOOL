# Unexpected Error CQE


## Unexpected Error CQE
## 
DUT에서 예상치 못한 에러 CQE가 발생하여 시뮬레이션이 중단되는 케이스입니다.
 
## 중요: 에러 CQE 발생 원칙
## 
 RETRY_EXC 계열을 제외한 모든 에러 CQE는 정상 시뮬레이션에서 발생하면 안 됩니다. 발생 시 DUT 버그를 의미합니다.

 | 
분류
 | | 
에러 코드
 | | 
정상 발생 가능 여부
 | | 
설명
 | 

 | 
 조건부 발생 가능 
 | | 
 WC_RETRY_EXC_ERR (12)
 | | 
O
 | | 
HW 내부 리소스 부족이나 처리 성능 부족으로 패킷 드롭 발생 시
 | 

 | 
 조건부 발생 가능 
 | | 
 WC_RNR_RETRY_EXC_ERR (13)
 | | 
O
 | | 
HW 내부 리소스 부족으로 Recv 처리 지연 시
 | 

 | 
 절대 발생 불가 
 | | 
그 외 모든 에러
 | | 
X
 | | 
발생 시 DUT 버그 — TB 설정이 올바르다면 DUT 내부 문제
 | 

 RETRY_EXC 발생 원인: DUT 내부 리소스(버퍼, 큐, 처리 파이프라인) 부족으로 인해 패킷이 드롭되면, Requester가 재전송을 반복하다가 retry 한도를 초과합니다. 이는 DUT의 성능 한계를 나타내는 것으로, 트래픽 부하나 동시성을 조절하여 해결할 수 있습니다.
 
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
 F-CQHDL-TBERR-0003 
 | | 
FATAL
 | | 
 Unexpected Error Handler: <cqe.sprint()> 
 | 

 발생 조건: cqe.wc_status != IB_WC_SUCCESS (에러 CQE) AND cmd.expected_error == 0 (예상하지 않음)
 
## CQE sprint 출력에서 확인할 핵심 필드
## 
## wc_status 에러 코드 레퍼런스
## 
## RETRY 계열 (조건부 발생 가능 — HW 리소스/성능 문제)
## 

 | 
wc_status
 | | 
이름
 | | 
의미
 | | 
원인
 | 

 | 
12
 | | 
 WC_RETRY_EXC_ERR 
 | | 
재시도 횟수 초과
 | | 
 HW 내부 리소스 부족 → 패킷 드롭 → 재전송 한도 초과. Responder 측 처리 성능 부족이 근본 원인
 | 

 | 
13
 | | 
 WC_RNR_RETRY_EXC_ERR 
 | | 
RNR 재시도 초과
 | | 
 HW 내부 리소스 부족 → Recv 처리 지연. Recv WQE는 포스팅됐으나 DUT가 처리 못 함
 | 

## 나머지 (발생 시 DUT 버그)
## 

 | 
wc_status
 | | 
이름
 | | 
의미
 | | 
DUT 버그 유형
 | 

 | 
1
 | | 
 WC_LOC_LEN_ERR 
 | | 
로컬 길이 에러
 | | 
DUT의 SGE 처리 로직 오류
 | 

 | 
2
 | | 
 WC_LOC_QP_OP_ERR 
 | | 
QP 상태 머신 에러
 | | 
DUT QP FSM이 잘못된 상태에서 operation 수행
 | 

 | 
4
 | | 
 WC_LOC_PROT_ERR 
 | | 
로컬 보호 에러
 | | 
DUT의 lkey 검증 로직 오류
 | 

 | 
5
 | | 
 WC_WR_FLUSH_ERR 
 | | 
WQE flush
 | | 
선행 에러의 2차 영향 (선행 에러부터 추적)
 | 

 | 
8
 | | 
 WC_LOC_ACCESS_ERR 
 | | 
로컬 접근 에러
 | | 
DUT의 MR 접근 권한 체크 로직 오류
 | 

 | 
9
 | | 
 WC_REM_INV_REQ_ERR 
 | | 
리모트 잘못된 요청
 | | 
DUT가 잘못된 요청 패킷 생성
 | 

 | 
10
 | | 
 WC_REM_ACCESS_ERR 
 | | 
리모트 접근 에러
 | | 
DUT의 rkey 검증 또는 MR 경계 체크 오류
 | 

 | 
11
 | | 
 WC_REM_OP_ERR 
 | | 
리모트 operation 에러
 | | 
DUT Responder 처리 로직 오류
 | 

 | 
19
 | | 
 WC_FATAL_ERR 
 | | 
DUT 내부 fatal
 | | 
DUT 내부 assertion 또는 복구 불가 상태
 | 

 | 
20
 | | 
 WC_RESP_TIMEOUT_ERR 
 | | 
응답 타임아웃
 | | 
DUT 내부 ACK 생성 로직 오류
 | 

 | 
0xBF
 | | 
 WC_BF_FATAL_ERR 
 | | 
HW fatal
 | | 
HW 레벨 복구 불가 에러
 | 

 
## 에러 발생 경로
## 
## 경로 A: 데이터 CQ에서 발견
## 
## 경로 B: Error CQ 백그라운드 모니터에서 발견
## 
## 디버깅 순서
## 
## Step 1: wc_status로 에러 분류 — RETRY vs 나머지
## 
## Step 2A: RETRY_EXC — HW 리소스/성능 문제 디버깅
## 
## Step 2B: 나머지 에러 — DUT 버그 디버깅
## 
 이 에러들은 TB 설정이 올바르다면 DUT 내부 문제입니다. 
 
## Step 3: 시퀀스 로직 확인 (TB 설정 오류 배제)
## 
## 에러 발생 후 TB 상태
## 

 | 
항목
 | | 
동작
 | 

 | 
QP 상태
 | | 
 setErrState(1) → 이후 모든 command skip
 | 

 | 
Outstanding WQE
 | | 
전체 flush ( completeOutstanding 호출)
 | 

 | 
CQ 폴링
 | | 
 cmd.error_occured = 1 → 루프 즉시 종료
 | 

 | 
스코어보드
 | | 
에러 CQE는 cqe_ap 로 전달되지 않음 (validation checker에만 전달)
 | 

 | 
시퀀서
 | | 
 wc_error_status[qp] , debug_wc_flag[qp] 에 에러 정보 기록
 | 

 
## Expected Error로 전환하는 방법
## 
에러가 의도된 테스트 시나리오라면:
 systemverilog 0) begin
 RDMAWCStatus_t status = t_seqr.wc_error_status[qp_num][0];
 // 예상한 에러인지 검증
end

// 에러 QP 정리
this.RDMAQPDestroy(.t_seqr(seqr), .qp_num(qp_num), .err(1));
t_seqr.clearErrorStatus(qp_num);]]> 
