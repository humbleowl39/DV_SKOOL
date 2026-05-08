# H2C / C2H QID Reference


## H2C / C2H QID Reference
## 
QDMA bypass queue의 QID 정의와 디버깅 활용법입니다. fsdb에서 H2C/C2H 트랜잭션의 QID를 확인하면 어떤 DUT 서브시스템이 DMA를 발생시켰는지 즉시 파악할 수 있습니다.

 정의 파일: lib/base/def/vrdma_defs.svh:75-88 
 
## H2C QID (Host-to-Card)
## 
DUT가 호스트 메모리에서 데이터를 읽어오는 방향입니다.

 | 
QID
 | | 
상수명
 | | 
용도
 | | 
설명
 | 

 | 
8
 | | 
 RDMA_REQ_H2C_QID 
 | | 
 Requester 데이터 fetch 
 | | 
Send/Write 시 source 메모리에서 payload 읽기
 | 

 | 
9
 | | 
 RDMA_RSP_H2C_QID 
 | | 
 Responder 데이터 fetch 
 | | 
Read Response 시 source 메모리에서 payload 읽기
 | 

 | 
10-13
 | | 
 RDMA_RECV_H2C_QID[0:3] 
 | | 
 Recv WQE fetch 
 | | 
RQ에서 Recv WQE descriptor 읽기 (4채널)
 | 

 | 
14-17
 | | 
 RDMA_CMD_H2C_QID[0:3] 
 | | 
 Command WQE fetch 
 | | 
SQ에서 Send/Write/Read WQE descriptor 읽기 (4채널)
 | 

 | 
18
 | | 
 RDMA_CTRL_H2C_QID 
 | | 
 Control WQE fetch 
 | | 
CTRL_QP의 SQ에서 QP/MR/CQ 관리 명령 읽기
 | 

 | 
20
 | | 
 RDMA_MISS_PA_H2C_QID 
 | | 
 Page table miss fetch 
 | | 
PTW miss 시 page table entry 읽기
 | 

## C2H QID (Card-to-Host)
## 
DUT가 호스트 메모리에 데이터를 쓰는 방향입니다.

 | 
QID
 | | 
상수명
 | | 
용도
 | | 
설명
 | 

 | 
8-9
 | | 
 RESP_C2H_QID[0:1] 
 | | 
 Responder 데이터 쓰기 
 | | 
Write/Send 수신 시 destination 메모리에 payload 쓰기 (2채널)
 | 

 | 
10-11
 | | 
 COMP_C2H_QID[0:1] 
 | | 
 CQE 쓰기 
 | | 
Completion Queue Entry를 호스트 CQ 메모리에 쓰기 (2채널)
 | 

 | 
12-13
 | | 
 ZERO_C2H_QID[0:1] 
 | | 
 Zero init 쓰기 
 | | 
메모리 초기화 용도 (2채널)
 | 

 | 
14
 | | 
 CC_NOTIFY_C2H_QID 
 | | 
 CC 알림 쓰기 
 | | 
Congestion Control 이벤트 알림 쓰기
 | 

 
## QID 기반 디버깅
## 
## fsdb에서 QID 확인 방법
## 
QDMA 인터페이스의 DMA 트랜잭션에서 qid 필드를 확인합니다. QID 값으로 아래 테이블을 역참조하면 문제 서브시스템을 특정할 수 있습니다.

## H2C QID로 문제 원인 특정
## 

 | 
증상
 | | 
QID 확인
 | | 
의미
 | 

 | 
CQ Poll Timeout
 | | 
QID 14-17 (CMD) 확인
 | | 
WQE descriptor fetch가 일어났는지 → DUT가 SQ doorbell을 인식했는지
 | 

 | 
CQ Poll Timeout
 | | 
QID 8 (REQ) 확인
 | | 
Requester payload fetch가 일어났는지 → WQE 처리가 시작됐는지
 | 

 | 
Data Mismatch
 | | 
QID 8 (REQ) / 9 (RSP) 데이터 확인
 | | 
H2C로 읽어온 source 데이터가 올바른지
 | 

 | 
Recv 미동작
 | | 
QID 10-13 (RECV) 확인
 | | 
Recv WQE fetch가 일어났는지 → RQ doorbell 인식 여부
 | 

 | 
Page Table 오류
 | | 
QID 20 (MISS_PA) 확인
 | | 
PTW miss가 발생했는지, 어떤 주소의 PTE를 fetch했는지
 | 

 | 
Control 명령 미완료
 | | 
QID 18 (CTRL) 확인
 | | 
Control WQE fetch가 일어났는지
 | 

## C2H QID로 문제 원인 특정
## 

 | 
증상
 | | 
QID 확인
 | | 
의미
 | 

 | 
Data Mismatch
 | | 
QID 8-9 (RESP) 주소/데이터 확인
 | | 
DUT가 destination에 쓴 데이터와 주소가 올바른지
 | 

 | 
CQ Poll Timeout
 | | 
QID 10-11 (COMP) 확인
 | | 
CQE가 호스트 메모리에 기록되었는지
 | 

 | 
C2H Tracker 매칭 실패
 | | 
QID 8-9 (RESP) 주소 확인
 | | 
C2H의 대상 주소가 기대 PA와 일치하는지
 | 

 | 
CC 이벤트 미수신
 | | 
QID 14 (CC_NOTIFY) 확인
 | | 
CC notification이 발생했는지
 | 

 
## 디버깅 워크플로우
## 
## Case 1: 특정 QID의 DMA가 아예 안 나오는 경우
## 
## Case 2: DMA는 나오지만 주소/데이터가 잘못된 경우
## 
## Case 3: 다른 에러와 교차 분석
## 
## 채널 매핑 참고
## 
H2C/C2H 일부 QID는 복수 채널 로 구성됩니다:

 | 
카테고리
 | | 
채널 수
 | | 
QID 범위
 | | 
비고
 | 

 | 
RECV H2C
 | | 
4
 | | 
10, 11, 12, 13
 | | 
RQ WQE fetch 병렬화
 | 

 | 
CMD H2C
 | | 
4
 | | 
14, 15, 16, 17
 | | 
SQ WQE fetch 병렬화
 | 

 | 
RESP C2H
 | | 
2
 | | 
8, 9
 | | 
데이터 write 병렬화
 | 

 | 
COMP C2H
 | | 
2
 | | 
10, 11
 | | 
CQE write 병렬화
 | 

 | 
ZERO C2H
 | | 
2
 | | 
12, 13
 | | 
초기화 write 병렬화
 | 

복수 채널인 경우, 디버깅 시 모든 채널의 QID를 함께 검색 해야 합니다.

