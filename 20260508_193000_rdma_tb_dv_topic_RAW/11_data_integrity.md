# Data Integrity Error


## Data Integrity Error (Data Mismatch)
## 
데이터 비교 실패 — source 메모리와 destination 메모리의 내용이 불일치할 때 발생합니다.
 
## 대표 에러 메시지
## 

 | 
ID
 | | 
컴포넌트
 | | 
메시지
 | 

 | 
 E-SB-MATCH-0001 
 | | 
1side_compare
 | | 
 INVALID: Write command %s, Reason: %s 
 | 

 | 
 E-SB-MATCH-0002 
 | | 
1side_compare
 | | 
 INVALID: Read command %s, Reason: %s 
 | 

 | 
 E-SB-MATCH-0003 
 | | 
1side_compare
 | | 
 Mismatch[%0d]: byte %0d, local=0x%02x(0x%0h), remote=0x%02x(0x%0h) 
 | 

 | 
 E-SB-MATCH-0005 
 | | 
1side_compare
 | | 
 Write inline data validation failed: %s 
 | 

 | 
 E-SB-MATCH-0003 
 | | 
2side_compare
 | | 
 MISMATCH: Send %s <-> Recv %s, Reason: %s 
 | 

 | 
 E-SB-MATCH-0005 
 | | 
imm_compare
 | | 
 MISMATCH: Send %s <-> CQE %s, Reason: %s 
 | 

 | 
 E-SB-MATCH-0001 
 | | 
imm_compare
 | | 
 IMM data mismatch: send_immdt=0x%08h, cqe_immdt=0x%08h 
 | 

 
## 발생 경로별 분류
## 
## Case 1: 1-Sided (Write/Read) — vrdma_1side_compare 
## 
 비교 대상: source 노드 메모리 vs destination 노드 메모리
 
 로그에서 확인할 정보: 

- 
 E-SB-MATCH-0003 : 바이트 인덱스, local 값(PA), remote 값(PA) — 최대 10개까지 출력

- 
- 
 E-SB-MATCH-0004 : 10개 초과 시 총 불일치 수

- 
- 
 E-SB-TBERR-0016 : 컨테이너 크기 불일치 — local_total=%0d, remote_total=%0d, transfer_size=%0d 

- 

## Case 2: 2-Sided (Send/Recv) — vrdma_2side_compare 
## 
 비교 대상: sender 메모리 vs receiver 메모리 (QP 매칭 후)
 
 주의: 2side는 첫 번째 불일치에서 즉시 리턴 (1side처럼 전체 불일치 목록을 보여주지 않음)

 로그 포맷: "Data mismatch at byte %0d: send=0x%02h(0x%0h), recv=0x%02h(0x%0h)" 

 알려진 이슈: 비인라인 경로에서 result.send_pa[] / recv_pa[] 가 채워지지 않아 PA 값이 0으로 표시될 수 있음

## Case 3: IMM Data — vrdma_imm_compare 
## 
 비교 대상: Send command의 immdt vs CQE의 union_ex (32-bit)
 
 OPS/SR 경로 추가 정보: I-SB-DATA-0001: OPS IMM QP information: base_addr=0x%0h, dest_qp=%0d, cqe_immdt(union_ex)=0x%08h 
 
## 디버깅 순서
## 
## Step 1: 에러 로그에서 기본 정보 수집
## 
## Step 2: SW 로그에서 엔티티 상태 확인
## 
Data mismatch의 근본 원인은 대부분 SW 엔티티의 설정 불일치 또는 HW 인터페이스의 데이터 손상 에 있습니다.

## IOVA Translator 확인
## 
## Page Table 확인
## 
## MR 엔티티 확인
## 
## QP 엔티티 확인
## 
## Step 3: HW 인터페이스 확인 (C2H / H2C)
## 
## C2H (Card-to-Host) 패턴 확인
## 
## H2C (Host-to-Card) 패턴 확인
## 
## Step 4: DUT 데이터 경로 추적
## 
## Step 5: MR/SGE 설정 확인
## MR boundary)
├── page table 변환이 정확한지 (iova_translator)
└── SGE 개수와 각 SGE의 size 합계 = 전체 transfer_size 인지]]> 
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
DUT 데이터 경로 버그
 | | 
특정 바이트 위치에서 일관된 불일치
 | | 
fsdb에서 C2H data payload 대조
 | 

 | 
IOVA→PA 변환 불일치
 | | 
랜덤한 위치에서 전혀 다른 데이터
 | | 
iova_translator 로그 vs DUT PTW 비교
 | 

 | 
H2C fetch 오류
 | | 
source 데이터 자체가 잘못 읽힘
 | | 
H2C addr/data vs source 메모리 비교
 | 

 | 
C2H write 주소 오류
 | | 
올바른 데이터가 잘못된 위치에 기록
 | | 
C2H addr vs 기대 PA 비교
 | 

 | 
컨테이너 크기 불일치
 | | 
 E-SB-TBERR-0016 
 | | 
transfer_size와 실제 DMA size 비교
 | 

 | 
타이밍 이슈 (stale data)
 | | 
간헐적 실패, 데이터 일부만 정확
 | | 
C2H 완료 시점 vs comparator 읽기 시점
 | 

 | 
Page table 구축 오류
 | | 
특정 MR/page 경계에서만 실패
 | | 
buildPageTable 로그, PD0/PD1/PD2 확인
 | 

 | 
MR key 불일치
 | | 
 E-SB-TBERR-0007~0014 
 | | 
MR pool에서 lkey/rkey 조회
 | 

 | 
Inline padding 오류
 | | 
Inline 커맨드에서만 발생
 | | 
inline_data.size vs transfer_size
 | 

 | 
OPS IMM base addr 오류
 | | 
IMM compare에서만 OPS/SR QP 실패
 | | 
ops_immdt_q_base_addr 설정 확인
 | 


