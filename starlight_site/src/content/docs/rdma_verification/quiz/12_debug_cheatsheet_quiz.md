---
title: "Module 12 퀴즈 — Debug Cheatsheet"
---

본문: [Module 12](../../12_debug_cheatsheet/)

---

### Q1. (Remember) `E-DRV-TBERR-0001` 의 모듈은? `F-C2H-MATCH-0002` 의 모듈은?
**정답.** `E-DRV-TBERR-0001` → Module 09 (CQ Poll Timeout). `F-C2H-MATCH-0002` → Module 10 (C2H Tracker Error).
**Why.** 에러 ID prefix와 담당 모듈의 매핑이 cheatsheet의 핵심이다. `E-DRV-TBERR`는 `vrdma_driver`에서 발생하는 에러로, driver가 CQ 폴링 타임아웃을 선언할 때 사용된다(Module 09). `F-C2H-MATCH`는 `vrdma_c2h_tracker`에서 발생하는 PA 매칭 실패로(Module 10), C2H DMA 주소 검증과 관련된다. 이 매핑을 암기해 두면 grep 결과 한 줄만 보고도 어느 챕터를 열어야 할지 즉시 결정할 수 있다.

### Q2. (Apply) 시뮬 실패 후 첫 명령(grep)은?
**정답.** `grep -nE "(UVM_FATAL|UVM_ERROR|F-|E-)" run.log | head -5` — 첫 5 개 에러로 cascading 효과 무시하고 root 부터 분석.
**Why.** 시뮬 실패 로그에는 수십~수백 개의 에러가 찍히는 경우가 많은데, 대부분은 첫 번째 에러에서 파생된 cascading 에러다. `head -5`로 앞 5개만 보는 이유는 첫 에러(루트)를 찾기 위함이다. 이후 에러들은 첫 에러의 증상이므로 독립적으로 디버깅하면 시간을 낭비하게 된다. 로그 전체를 순서대로 읽는 것보다 이 grep 한 줄이 디버그 시작을 훨씬 빠르게 해준다.

### Q3. (Apply) 한 시뮬에서 첫 5 줄에 `F-C2H-MATCH-0002` 와 `E-DRV-TBERR-0001` 둘 다 보인다. 어느 것부터?
**정답.** 시간 더 빠른 것 먼저 — 보통 `F-C2H-MATCH-0002` (PA 매칭 실패는 fatal 이라 즉시) 가 먼저면 그게 root, CQ Poll Timeout 은 cascading. 하지만 timestamp 로 결정해야 함.
**Why.** "fatal(F-)이 error(E-)보다 먼저"라는 직관은 유용하지만 항상 옳지는 않다. 올바른 판단 기준은 항상 timestamp(시뮬 시간)다. `F-C2H-MATCH-0002`가 C2H 데이터를 받자마자 발생하는 반면, `E-DRV-TBERR-0001`은 폴링 타임아웃 카운터가 소진된 후 발생하므로 시간적으로 뒤에 오는 경우가 많다. 그러나 반대의 경우도 있으므로 timestamp를 확인하지 않고 순서를 가정하는 것은 위험하다.

### Q4. (Analyze) 한 줄 그림(§4 ErrQP 흐름)을 보고, "ErrQP 가 정리되었는데도 c2h_tracker fatal" 이 발생한다면 어디를 의심하나?
**정답.** `is_err_qp_registered[node][qp]` 가 set 되지 않았을 가능성 — `RDMAQPDestroy(.err)` 호출이 아닌 다른 경로로 ErrQP 가 되었거나, `vrdma_c2h_tracker::deregisterQP` 가 호출되기 전에 C2H 가 도착.
**Why.** ErrQP 정리 흐름은 `RDMAQPDestroy(.err(1))` → driver `setErrState(1)` → `qp_reg_ap` broadcast → c2h_tracker `deregisterQP` 호출로 이어진다. 이 연쇄 중 어느 링크가 끊어지면 `is_err_qp_registered`가 set되지 않아 이후 도착하는 C2H가 silent skip 대신 fatal로 처리된다. 가장 흔한 원인은 c2h_tracker의 `deregisterQP`가 호출되기 전에 파이프라인상 C2H DMA가 이미 도착하는 타이밍 레이스다.

### Q5. (Apply) 한 줄로 답하시오: timeout_count 의 default 값과 동일한 timeout 까지 걸린 시간(ms)은?
**정답.** 50000 → ~50ms (`vrdma_top_sequence::RDMACQPoll`). 10000 → ~10ms (sequence / cmd 기본).
**Why.** timeout_count와 실제 시뮬 시간을 연결하는 이유는, 실제 하드웨어 응답 시간과 비교해 "이 timeout이 합리적인가"를 판단하기 위함이다. 50ms는 PCIe 기반 시스템에서 DMA 완료에 충분한 시간이지만, 시뮬레이션 속도에 따라 실제 시뮬 wall-clock 시간은 크게 다를 수 있다. timeout_count를 조절할 때 이 스케일을 이해하지 못하면 너무 짧게 설정해 정상 동작도 timeout으로 오판할 수 있다.

### Q6. (Evaluate) "static `err_enabled = 1` 만 켜면 모든 에러를 회피할 수 있다" 를 평가하시오.
**정답.** 잘못됨. `err_enabled` 는 comparator/tracker 의 deregister/매칭 fatal 을 회피만 — 에러 CQE 자체(`F-CQHDL-TBERR-0003`)나 timeout(`E-DRV-TBERR-0001`)은 별도 게이트 필요. per-cmd `expected_error`, `enable_error_cq_poll = 0` 같은 도구를 조합해야 함.
**Why.** `err_enabled`는 comparator와 c2h_tracker가 QP deregister 시 fatal을 내지 않도록 하는 게이트다. 그러나 에러 CQE 자체가 `F-CQHDL-TBERR-0003`를 발생시키는 경로는 `cq_handler`에 있으며, 이는 `expected_error` 게이트로만 제어된다. 또한 CQ poll timeout은 driver에서 발생하는 `E-DRV-TBERR-0001`으로 `err_enabled`와 무관하다. 에러 테스트는 에러 경로 3개 각각에 적합한 게이트를 조합해야 완전하게 제어할 수 있다.

### Q7. (Apply) `grep -oE "(E-DRV-|E-SB-|F-CQHDL-|F-C2H-|E-C2H-)[A-Z]+-[0-9]{4}" run.log | sort | uniq -c` 의 의도는?
**정답.** 에러 ID 별 발생 카운트 — 어떤 카테고리가 dominant 인지 빠르게 파악. 예: `F-C2H-MATCH-0002 x 50` 이면 PA 매칭 실패가 주된 문제.
**Why.** 이 grep은 로그에서 에러 ID를 추출해 카테고리별로 정렬하고 빈도를 세는 명령이다. "어떤 에러가 몇 번 발생했는가"를 집계하면 시뮬 실패의 주된 원인을 빠르게 특정할 수 있다. 특정 에러 ID가 수십 번 반복된다면 그 에러가 root cause이거나 매우 광범위한 파급 효과를 가진 버그임을 시사한다. 로그를 줄 단위로 읽는 것보다 이 집계 뷰가 전체 그림을 보는 데 훨씬 효과적이다.

### Q8. (Create) "처음 보는 RDMA-TB 시뮬 fail 을 받았다. 5 분 안에 어디까지 좁혀야 하나" 를 단계별로 답하시오 (5 단계).
**정답.**
1. `grep -nE "(F-|E-)" run.log | head -5` 로 첫 에러 ID 5개.
2. 에러 ID prefix → Module 12 §1 매핑 표 → 어느 모듈로 갈지 결정.
3. 해당 모듈의 §빠른 트리아지 1행 결정.
4. 적용 가능한 QID/static flag 확인 (Module 12 §2, §3).
5. 해당 모듈의 5단계 디버그 절차 Step 1-2 까지 (로그/SW 엔티티) — 5분 안에 못 가면 escalate.
**Why.** 5분이라는 제한은 "에스컬레이션 판단 시점"을 정하는 기준이다. 1단계(grep)는 30초, 2단계(prefix 매핑)는 1분이면 충분하다. 3단계(빠른 트리아지 1행)에서 이미 "SQ doorbell 인식 실패" 또는 "PA 매칭 실패"로 좁혀지는 경우도 많다. 4단계(QID 확인)는 가설을 증거로 전환하는 단계이고, 5단계 Step 1-2까지 도달하면 "TB 설정 오류인지 DUT 버그인지"의 초기 판단이 가능해진다. 5분 안에 이 지점까지 오지 못하면 더 많은 컨텍스트가 필요한 문제이므로 팀에 에스컬레이션하는 것이 맞다.
