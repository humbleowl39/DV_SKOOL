# C2H Tracker Error


## C2H Tracker Error
## 
C2H DMA 트랜잭션의 PA 매칭 실패 또는 ordering 위반 시 발생합니다.
 
## 대표 에러 메시지
## 
## PA 매칭 실패
## 

 | 
ID
 | | 
심각도
 | | 
메시지
 | 

 | 
 F-C2H-MATCH-0001 
 | | 
FATAL
 | | 
 C2H transaction not found for node %s (빈 노드)
 | 

 | 
 F-C2H-MATCH-0002 
 | | 
FATAL
 | | 
 C2H transaction not found for QP 0x%h on %s: addr=0x%h, size=0x%h 
 | 

 | 
 W-C2H-MATCH-0001 
 | | 
WARNING
 | | 
 Current WRITE unprocessed PA List: %p (fatal 직전 진단)
 | 

 | 
 W-C2H-MATCH-0002 
 | | 
WARNING
 | | 
 Current READ unprocessed PA List: %p 
 | 

 | 
 W-C2H-MATCH-0003 
 | | 
WARNING
 | | 
 Current RECV unprocessed PA List: %p 
 | 

## Ordering 위반
## 

 | 
ID
 | | 
심각도
 | | 
메시지
 | 

 | 
 E-C2H-MATCH-0001 
 | | 
ERROR
 | | 
Ordering violation — QP, op type, tag, 실제 주소, 발견 인덱스, 기대 인덱스, 기대 주소
 | 

## 크기 초과
## 

 | 
ID
 | | 
심각도
 | | 
메시지
 | 

 | 
 F-C2H-MATCH-0003 
 | | 
FATAL
 | | 
C2H transfer size > expected PA block size (OPS)
 | 

 | 
 F-C2H-MATCH-0004 
 | | 
FATAL
 | | 
C2H transfer size > expected PA block size (non-OPS)
 | 

 
## 동작 메커니즘
## 
## Ordering 규칙
## 

 | 
QP 타입
 | | 
규칙
 | | 
Phase 1 동작
 | 

 | 
RC
 | | 
 FIFO 순서 강제 
 | | 
index 0만 체크
 | 

 | 
OPS/SR
 | | 
 Out-of-order 허용 
 | | 
전체 인덱스 범위 체크
 | 

 
## 디버깅 순서
## 
## Step 1: Ordering 위반 — 원본 I/O WQE 확인
## 
Ordering violation ( E-C2H-MATCH-0001 )이 발생하면, 에러 로그에 C2H가 올라와야 하는 순서 가 표시됩니다. 이를 바탕으로 원본 WQE를 추적합니다.
 
 원본 I/O WQE 추적: 
 
## Step 2: PA 매칭 실패 — C2H QID와 메모리 범위 확인
## 
아예 매칭이 안 되는 C2H가 도착하면 ( F-C2H-MATCH-0002 ), fatal 직전에 진단 로그가 출력됩니다.
 
 C2H QID로 원인 분류: 
 
 메모리 범위 매핑: 
 
## Step 3: TB vs DUT PA 변환 비교
## 
## Step 4: trackCommand에서 커맨드가 등록되었는지 확인
## 
## Step 5: C2H DMA 트랜잭션 자체 확인
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
DUT PTW 버그
 | | 
addr가 PA 리스트 어디에도 없음
 | | 
TB translateIOVA vs DUT PTW 비교
 | 

 | 
DUT QP routing 오류
 | | 
C2H QID가 잘못된 QP를 가리킴
 | | 
C2H QID vs 원본 WQE의 QP 번호 비교
 | 

 | 
MR page table 설정 오류
 | | 
특정 MR의 커맨드만 실패
 | | 
buildPageTable 로그, PA 범위 대조
 | 

 | 
DUT out-of-order 처리 (RC)
 | | 
E-C2H-MATCH-0001 ordering violation
 | | 
원본 WQE 두 개의 DUT 처리 순서 비교
 | 

 | 
C2H addr가 다른 QP의 PA에 매칭
 | | 
잘못된 QP의 데이터가 도착
 | | 
addr를 전체 QP PA 리스트와 교차 검증
 | 

 | 
Zero-length drop
 | | 
커맨드가 등록 안 됨
 | | 
transfer_size 확인
 | 

 | 
QP deregister 타이밍
 | | 
에러 QP 정리 후 지연 C2H 도착
 | | 
err_qp_registered 상태 확인
 | 

 | 
MR re-register race
 | | 
구버전 PA가 사용됨
 | | 
gen_id, Fast Register 타이밍 확인
 | 

 | 
C2H 크기 초과
 | | 
F-C2H-MATCH-0003/0004
 | | 
DUT C2H size vs WQE transfer size
 | 


