# Debugging Cases


## Debugging Cases
## 
시뮬레이션 실패 시 에러/fatal 유형별 디버깅 가이드입니다. 각 케이스는 에러 메시지 ID, 발생 조건, 디버깅 순서를 포함합니다.

## 케이스 목록
## 

 | 
케이스
 | | 
대표 에러 ID
 | | 
발생 컴포넌트
 | | 
설명
 | 

 | 
Data Integrity Error
 | | 
 E-SB-MATCH-* 
 | | 
1side/2side/imm compare
 | | 
데이터 비교 실패 (src vs dest 불일치)
 | 

 | 
CQ Poll Timeout
 | | 
 E-DRV-TBERR-0001 
 | | 
cq_handler → driver
 | | 
CQE 폴링 타임아웃
 | 

 | 
C2H Tracker Error
 | | 
 F-C2H-MATCH-* 
 | | 
c2h_tracker
 | | 
C2H DMA PA 매칭/ordering 실패
 | 

 | 
Unexpected Error CQE
 | | 
 F-CQHDL-TBERR-0003 
 | | 
cq_handler
 | | 
예상치 못한 에러 CQE 수신
 | 


