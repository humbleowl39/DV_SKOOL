# Module 08 퀴즈 — Data Integrity Error

본문: [Module 08](../08_debug_data_integrity.md)

---

### Q1. (Remember) `E-SB-MATCH-0001` 에러 ID 는 어느 컴포넌트에서 발생하는가? (3 가지 가능 컴포넌트 모두)
**정답.** `vrdma_1side_compare`, `vrdma_2side_compare`, `vrdma_imm_compare` — 3 comparator 가 동일 ID 를 공유. 컨텍스트(메시지 본문)로 분리.
**Why.** 동일 ID 라도 instance name 으로 구분.

### Q2. (Understand) 1side 와 2side 의 mismatch 출력 정책 차이는?
**정답.** 1side = 최대 10 개 mismatch 까지 byte 별로 출력 (`E-SB-MATCH-0003`), 초과 시 `E-SB-MATCH-0004` 로 총 개수만. 2side = 첫 mismatch 에서 즉시 리턴.
**Why.** Module 08 §발생 경로 분류.

### Q3. (Apply) 첫 mismatch byte 가 0 byte 이고 다중 byte 가 mismatch 다. 첫 가설은?
**정답.** Source fetch 자체가 잘못 — H2C QID 8(REQ) 또는 9(RSP) 에서 잘못된 데이터를 읽어옴. 또는 IOVA→PA 변환이 source 영역에서 빗나감.
**Why.** Module 08 §빠른 트리아지 표.

### Q4. (Analyze) `E-SB-TBERR-0016` (컨테이너 크기 불일치) 가 발생했다. 어떻게 디버그?
**정답.** `local_total`, `remote_total`, `transfer_size` 비교 → 어느 쪽이 잘못되었나. SGE 의 size 합계 vs WQE 의 transfer_size 비교. 보통 DUT 의 전송 측이 zero-padding 을 더 추가했거나 페이지 boundary 처리 오류.
**Why.** Module 08 §흔한 원인 표.

### Q5. (Apply) IMM mismatch (`E-SB-MATCH-0001` from `imm_compare`): `send_immdt=0xCAFEBABE, cqe_immdt=0xDEADBEEF`. OPS QP 다. 어디부터 보나?
**정답.** OPS IMM 경로의 `ops_immdt_q_base_addr` 설정 확인. `I-SB-DATA-0001` 로그에서 base_addr / dest_qp 가 expected 와 일치하는지. 경로상 다른 immdt 와 섞였을 가능성.
**Why.** Module 08 §Case C IMM 보충 정보.

### Q6. (Analyze) "간헐적 실패, 데이터 일부만 정확" 패턴이 있다. 어떤 원인?
**정답.** 타이밍 이슈 (stale data) — C2H 완료 시점 vs comparator 가 destination 메모리를 읽는 시점이 race. 보통 c2h_tracker 의 tracking 타이밍 또는 comparator 의 read trigger 동기화.
**Why.** Module 08 §흔한 원인 표.

### Q7. (Evaluate) 첫 가설로 "DUT 데이터 경로 버그" 라고 단정해도 되는가?
**정답.** 안 됨. Module 08 의 5단계는 DUT 검증을 4단계에 두고 그 전에 SW 엔티티(2)와 HW 인터페이스(3)를 먼저 본다 — TB 측 설정 오류를 먼저 배제해야 함. DUT 결론은 다른 가능성을 모두 배제한 후에만 valid.
**Why.** Module 08 §5단계 + 일반 디버그 원칙(루트 코즈 first).

### Q8. (Create) 첫 mismatch byte 가 4096 이다 (정확히 4 KB 경계). 가설을 작성하고 검증 절차 3단계를 답하시오.
**정답.**
- 가설: page boundary 의 PTE 변환이 잘못됨. iova 가 page 1 → page 2 로 넘어가는 지점에서 PA 가 잘못 계산됨.
- 검증:
  1. `iova_translator` 로그에서 해당 iova 의 PA 변환 추적 (page 0 vs page 1 경계 PTE 확인)
  2. DUT PTW 로그/fsdb 에서 동일 iova 의 PTW 결과와 비교
  3. `buildPageTable` 로그에서 PD0/PD1/PD2 의 해당 page 1 entry 가 정상인지
**Why.** Module 08 §Step 5 MR/SGE 와 §빠른 트리아지.
