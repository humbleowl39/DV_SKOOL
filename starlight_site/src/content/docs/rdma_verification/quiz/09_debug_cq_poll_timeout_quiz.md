---
title: "Module 09 퀴즈 — CQ Poll Timeout"
---

본문: [Module 09](../../09_debug_cq_poll_timeout/)

---

### Q1. (Remember) 타임아웃 발동 두 조건을 답하시오.
**정답.** `try_cnt > timeout_count` AND `!c2h_tracker::active`. 둘 다 충족해야 발동.
**Why.** 두 조건이 모두 필요한 이유가 중요하다. `try_cnt > timeout_count`만으로는 DUT가 여전히 DMA 작업 중인 상황(c2h_tracker active)에서 성급하게 timeout을 선언할 수 있다. `!c2h_tracker::active`는 "현재 진행 중인 C2H DMA도 없다"는 것을 확인해 DUT가 진짜로 멈춘 상황에서만 timeout을 발동시킨다. 이 두 조건은 `vrdma_driver.svh:1484`에서 AND 논리로 구현되어 있다.

### Q2. (Understand) 타임아웃 시 fatal 이 아니라 `uvm_shutdown_phase` 로 점프하는 이유는?
**정답.** Graceful 종료 시 outstanding 진단 정보(unprocessed wqe, PA queues 등)가 보존되어 디버깅 가능. fatal 이면 즉시 종료 → 진단 손실.
**Why.** timeout이 발생한 상황에서 가장 중요한 것은 "어디서 막혔는가"를 알아내는 것이다. fatal로 즉시 종료하면 `check_phase`에서 수행되는 outstanding WQE 목록, PA queue 상태, 잔여 CQE 기대치 같은 진단 정보가 출력되지 않는다. `uvm_shutdown_phase`로 점프하면 TB가 graceful하게 종료 절차를 밟으면서 outstanding 상태를 보고하므로, 어느 QP의 몇 번째 WQE에서 멈췄는지 추적할 수 있다. "빠른 실패"보다 "완전한 진단"이 더 가치 있는 경우가 바로 이것이다.

### Q3. (Apply) 타임아웃 직전 `unprocessed wqe = 0` 인데도 timeout 이 발생했다. 의미는?
**정답.** 카운팅 오류 — `signaled` 비트 또는 `sq_sig_type` 설정으로 unsignaled WQE 가 폴링 대상에 포함되었거나 제외됨. CQ 가 expected entry 를 안 보고 있음.
**Why.** `unprocessed wqe = 0`은 "TB가 기대하는 완료 entry가 없다"는 뜻인데 timeout이 발생했다면, TB와 DUT 사이에 "몇 개의 CQE가 도착해야 하는가"에 대한 불일치가 있다는 의미다. `sq_sig_type`(signaled/unsignaled 설정)이 TB와 DUT에서 다르게 인식되면, DUT는 CQE를 N개 보내는데 TB는 M개를 기다리는 상황이 생긴다. `signaled` 비트 설정을 TB 설정과 DUT 행동 양쪽에서 확인해야 한다.

### Q4. (Analyze) c2h_tracker 가 active 인 동안 timeout 이 무한 지연된다. 이는 디버깅에 어떤 의미가 있나? (긍정 / 부정 모두)
**정답.**
- 긍정: DUT DMA 가 살아있다는 신호 — 어떤 작업은 진행 중.
- 부정: timeout 진단을 가린다 — 다른 문제(예: phase bit 동기화)는 timeout 으로 발견되지 않음.
**Why.** c2h_tracker active 상태는 DUT가 현재 C2H DMA를 수행 중이라는 의미이므로, DUT 전체가 죽은 것은 아니다(긍정). 그러나 CQ completion이 오지 않는 이유(예: phase bit 토글 오류로 polling이 CQE를 인식하지 못함)는 c2h_tracker active와 무관하게 발생할 수 있는데, active 상태가 timeout을 지연시키면 이런 별개 버그가 오래 발견되지 않는다(부정). 따라서 c2h_tracker active가 지속되면, CQ polling 상태(phase bit, head pointer 등)도 병행 확인해야 한다.

### Q5. (Apply) QID 14–17 fetch 가 0 회. 첫 가설과 다음 액션은?
**정답.** DUT 가 SQ doorbell 인식 실패. 다음: BAR4 의 SQ_DB 레지스터 쓰기 추적 → RAL config 가 정확한지 → DUT BAR decoding fsdb 추적.
**Why.** QID 14-17은 DUT가 SQ에서 WQE를 fetch하는 채널이다. 이 채널에 트랜잭션이 없다는 것은 DUT가 "새 WQE가 있다"는 doorbell 신호를 아예 받지 못했다는 의미다. 다음 단계는 TB가 BAR4의 SQ_DB 레지스터에 올바른 주소와 값을 썼는지 RAL 설정을 먼저 확인하는 것이다. RAL 설정이 맞다면 DUT의 BAR address decoding이 올바르게 동작하는지 fsdb에서 추적해야 한다.

### Q6. (Analyze) QID 14–17 OK, QID 8 OK, packet 송신 OK, 그러나 QID 10/11 (CQE write) 가 없다. 무엇을 의미?
**정답.** DUT 가 work 를 끝까지 처리했지만 completion engine 이 CQE 를 만들지 못함. completion FSM 버그 또는 CQ base addr 가 DUT 에 잘못 등록됨.
**Why.** QID 14-17(SQ fetch), QID 8(payload fetch), 네트워크 패킷 송신까지 모두 성공했다는 것은 DUT의 데이터 경로가 WQE를 완전히 처리했음을 의미한다. 그러나 CQE write(QID 10/11)가 없다면, DUT의 completion engine이 작업이 완료됐음을 인식하고 CQE를 생성하는 단계에서 실패한 것이다. CQ base address가 올바르게 등록되지 않아 DUT가 CQE를 쓸 위치를 모르거나, completion FSM에 버그가 있을 가능성을 조사해야 한다.

### Q7. (Evaluate) "timeout_count 를 100000 으로 늘리면 모든 timeout 이 사라진다" 를 평가하시오.
**정답.** 잘못됨. timeout 의 근본 원인은 DUT 가 work 를 처리하지 못하거나 CQE 가 도착하지 않는 것. 시간 늘려봐야 결과는 같음(또는 c2h_tracker active 가 끝나지 않으면 무한 대기). 진짜 해결은 root cause 추적.
**Why.** timeout_count를 늘리는 것은 "좀 더 기다리겠다"는 의미다. 그러나 DUT가 구조적으로 CQE를 생성하지 못하는 상태라면, 아무리 오래 기다려도 CQE는 도착하지 않는다. 오히려 `timeout_count`를 키우면 실패를 발견하는 시점만 늦어져 디버깅 사이클이 길어진다. "설정값 조정으로 버그를 회피하려는" 접근은 루트 코즈를 숨기는 위험한 습관이다.

### Q8. (Create) 새 테스트가 한 시뮬에서 RDMA verb 5000 개 발행. CQ poll 이 4900 개에서 timeout. 가설 3개를 작성하고 각각의 검증 명령을 답하시오.
**정답.**
- 가설 1 — DUT 가 4900 개 후 stall (예: 큐 overflow). 검증: DUT 의 SQ pointer 시간 그래프 fsdb.
- 가설 2 — `unprocessed_cqe_cnt` 누적 오류. 검증: 각 cqe 의 signaled 필드 누적 vs expected.
- 가설 3 — Phase bit 토글이 wrap-around 시점에서 누락. 검증: 폴링 주기 로그에서 PHASE 값 추적, CQ depth 와 wrap 시점 비교.
**Why.** 5000개 중 4900개에서 멈췄다는 것은 "특정 지점"에서 문제가 생겼다는 의미로, 조건부 버그 패턴을 시사한다. 큐 overflow(가설 1)는 깊이가 충분한지 확인해야 한다. signaled 비트 오류(가설 2)는 counted WQE 수와 CQE 도착 수의 누적 불일치를 만들 수 있다. phase bit wrap-around 버그(가설 3)는 CQ depth만큼 completion이 쌓인 후 첫 번째 wrap에서만 나타나는 경계 조건 버그로, 테스트 규모가 클 때만 재현된다.
