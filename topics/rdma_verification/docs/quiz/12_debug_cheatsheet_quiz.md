# Module 12 퀴즈 — Debug Cheatsheet

본문: [Module 12](../12_debug_cheatsheet.md)

---

### Q1. (Remember) `E-DRV-TBERR-0001` 의 모듈은? `F-C2H-MATCH-0002` 의 모듈은?
**정답.** `E-DRV-TBERR-0001` → Module 09 (CQ Poll Timeout). `F-C2H-MATCH-0002` → Module 10 (C2H Tracker Error).
**Why.** Module 12 §1 표.

### Q2. (Apply) 시뮬 실패 후 첫 명령(grep)은?
**정답.** `grep -nE "(UVM_FATAL|UVM_ERROR|F-|E-)" run.log | head -5` — 첫 5 개 에러로 cascading 효과 무시하고 root 부터 분석.
**Why.** Module 12 §6 grep 패턴.

### Q3. (Apply) 한 시뮬에서 첫 5 줄에 `F-C2H-MATCH-0002` 와 `E-DRV-TBERR-0001` 둘 다 보인다. 어느 것부터?
**정답.** 시간 더 빠른 것 먼저 — 보통 `F-C2H-MATCH-0002` (PA 매칭 실패는 fatal 이라 즉시) 가 먼저면 그게 root, CQ Poll Timeout 은 cascading. 하지만 timestamp 로 결정해야 함.
**Why.** Cascading 무시 + 시간순 root 분석.

### Q4. (Analyze) 한 줄 그림(§4 ErrQP 흐름)을 보고, "ErrQP 가 정리되었는데도 c2h_tracker fatal" 이 발생한다면 어디를 의심하나?
**정답.** `is_err_qp_registered[node][qp]` 가 set 되지 않았을 가능성 — `RDMAQPDestroy(.err)` 호출이 아닌 다른 경로로 ErrQP 가 되었거나, `vrdma_c2h_tracker::deregisterQP` 가 호출되기 전에 C2H 가 도착.
**Why.** Module 06 + Module 10 의 ErrQP 게이트 메커니즘.

### Q5. (Apply) 한 줄로 답하시오: timeout_count 의 default 값과 동일한 timeout 까지 걸린 시간(ms)은?
**정답.** 50000 → ~50ms (`vrdma_top_sequence::RDMACQPoll`). 10000 → ~10ms (sequence / cmd 기본).
**Why.** Module 09 §timeout_count 표 + Module 12 cheatsheet 보충.

### Q6. (Evaluate) "static `err_enabled = 1` 만 켜면 모든 에러를 회피할 수 있다" 를 평가하시오.
**정답.** 잘못됨. `err_enabled` 는 comparator/tracker 의 deregister/매칭 fatal 을 회피만 — 에러 CQE 자체(`F-CQHDL-TBERR-0003`)나 timeout(`E-DRV-TBERR-0001`)은 별도 게이트 필요. per-cmd `expected_error`, `enable_error_cq_poll = 0` 같은 도구를 조합해야 함.
**Why.** Module 06 §static flag 적용 범위.

### Q7. (Apply) `grep -oE "(E-DRV-|E-SB-|F-CQHDL-|F-C2H-|E-C2H-)[A-Z]+-[0-9]{4}" run.log | sort | uniq -c` 의 의도는?
**정답.** 에러 ID 별 발생 카운트 — 어떤 카테고리가 dominant 인지 빠르게 파악. 예: `F-C2H-MATCH-0002 x 50` 이면 PA 매칭 실패가 주된 문제.
**Why.** Module 12 §6.

### Q8. (Create) "처음 보는 RDMA-TB 시뮬 fail 을 받았다. 5 분 안에 어디까지 좁혀야 하나" 를 단계별로 답하시오 (5 단계).
**정답.**
1. `grep -nE "(F-|E-)" run.log | head -5` 로 첫 에러 ID 5개.
2. 에러 ID prefix → Module 12 §1 매핑 표 → 어느 모듈로 갈지 결정.
3. 해당 모듈의 §빠른 트리아지 1행 결정.
4. 적용 가능한 QID/static flag 확인 (Module 12 §2, §3).
5. 해당 모듈의 5단계 디버그 절차 Step 1-2 까지 (로그/SW 엔티티) — 5분 안에 못 가면 escalate.
**Why.** Cheatsheet 의 활용 통합 점검.
