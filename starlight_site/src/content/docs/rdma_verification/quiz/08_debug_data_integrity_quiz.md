---
title: "Module 08 퀴즈 — Data Integrity Error"
---

본문: [Module 08](../../08_debug_data_integrity/)

---

### Q1. (Remember) `E-SB-MATCH-0001` 에러 ID 는 어느 컴포넌트에서 발생하는가? (3 가지 가능 컴포넌트 모두)
**정답.** `vrdma_1side_compare`, `vrdma_2side_compare`, `vrdma_imm_compare` — 3 comparator 가 동일 ID 를 공유. 컨텍스트(메시지 본문)로 분리.
**Why.** 동일한 에러 ID를 여러 컴포넌트가 공유하는 이유는, 비교 실패라는 행위 자체가 3개 comparator 모두에서 공통적으로 발생하기 때문이다. 로그에서 `E-SB-MATCH-0001`을 보면 즉시 "data_env의 comparator"임을 알 수 있지만, 어느 comparator인지는 UVM instance 이름(예: `env.data_env.1side_compare`)을 봐야 구분된다. 에러 ID만으로 파일을 특정하지 말고 instance 이름까지 확인하는 습관이 필요하다.

### Q2. (Understand) 1side 와 2side 의 mismatch 출력 정책 차이는?
**정답.** 1side = 최대 10 개 mismatch 까지 byte 별로 출력 (`E-SB-MATCH-0003`), 초과 시 `E-SB-MATCH-0004` 로 총 개수만. 2side = 첫 mismatch 에서 즉시 리턴.
**Why.** 1side comparator는 단방향 write 결과 검증이므로 어느 byte 범위에 문제가 있는지 알아야 근본 원인을 좁힐 수 있다. 반면 2side comparator는 양방향 send/recv 시나리오에서 첫 mismatch 자체가 치명적 증거이므로 즉시 리턴하는 것이 더 효율적이다. 출력 정책 차이를 알면, 1side의 경우 10개 mismatch 위치를 분석해 "byte 범위 X~Y에서만 틀렸다"는 패턴을 발견할 수 있고, 이는 page boundary 버그나 IOVA 변환 오류 특정에 직접 쓰인다.

### Q3. (Apply) 첫 mismatch byte 가 0 byte 이고 다중 byte 가 mismatch 다. 첫 가설은?
**정답.** Source fetch 자체가 잘못 — H2C QID 8(REQ) 또는 9(RSP) 에서 잘못된 데이터를 읽어옴. 또는 IOVA→PA 변환이 source 영역에서 빗나감.
**Why.** mismatch가 byte 0부터 시작한다는 것은 "데이터 시작부터 틀렸다"는 의미다. 일부 구간만 틀렸다면 page boundary 문제나 offset 계산 오류를 의심할 수 있지만, byte 0부터 틀린 경우는 source 데이터 자체를 잘못 fetch했을 가능성이 높다. H2C QID 8 또는 9에서 payload를 제대로 읽어왔는지, 또는 IOVA→PA 변환이 source 영역에서부터 이미 빗나갔는지를 먼저 확인해야 한다. 이 접근법이 Module 08 빠른 트리아지 표의 첫 행이다.

### Q4. (Analyze) `E-SB-TBERR-0016` (컨테이너 크기 불일치) 가 발생했다. 어떻게 디버그?
**정답.** `local_total`, `remote_total`, `transfer_size` 비교 → 어느 쪽이 잘못되었나. SGE 의 size 합계 vs WQE 의 transfer_size 비교. 보통 DUT 의 전송 측이 zero-padding 을 더 추가했거나 페이지 boundary 처리 오류.
**Why.** `E-SB-TBERR-0016`은 "보낸 크기와 받은 크기가 다르다"는 의미다. 여기서 핵심은 "어느 쪽 크기가 잘못되었나"를 먼저 특정하는 것이다. `local_total`(송신 측 버퍼 크기), `remote_total`(수신 측 버퍼 크기), `transfer_size`(WQE에 명시된 전송 크기)를 삼각 비교하면 어느 값이 outlier인지 드러난다. DUT가 zero-padding을 추가하거나 page boundary에서 추가 바이트를 전송하는 경우가 흔한 원인이다.

### Q5. (Apply) IMM mismatch (`E-SB-MATCH-0001` from `imm_compare`): `send_immdt=0xCAFEBABE, cqe_immdt=0xDEADBEEF`. OPS QP 다. 어디부터 보나?
**정답.** OPS IMM 경로의 `ops_immdt_q_base_addr` 설정 확인. `I-SB-DATA-0001` 로그에서 base_addr / dest_qp 가 expected 와 일치하는지. 경로상 다른 immdt 와 섞였을 가능성.
**Why.** OPS(Out-of-order Packet Sending) QP에서 IMM 값이 달라지는 경우, `ops_immdt_q_base_addr` 설정 오류로 다른 WQE의 immediate data가 섞이는 경우가 많다. `I-SB-DATA-0001` 로그는 data_env가 수신한 정보(base_addr, dest_qp 등)를 기록하므로, 이 로그와 TB가 발행한 원래 WQE 정보를 비교하면 어느 시점에서 값이 바뀌었는지 추적할 수 있다.

### Q6. (Analyze) "간헐적 실패, 데이터 일부만 정확" 패턴이 있다. 어떤 원인?
**정답.** 타이밍 이슈 (stale data) — C2H 완료 시점 vs comparator 가 destination 메모리를 읽는 시점이 race. 보통 c2h_tracker 의 tracking 타이밍 또는 comparator 의 read trigger 동기화.
**Why.** "간헐적 실패"는 deterministic 버그가 아닌 타이밍 race의 전형적인 증상이다. comparator가 destination 메모리를 읽는 시점이 DUT의 C2H DMA 완료보다 빨리 발생하면, 아직 기록되지 않은 메모리를 읽어 stale 데이터와 비교하게 된다. "데이터 일부만 정확"한 것은 DMA가 진행 중일 때 comparator가 읽어서 이미 쓰인 앞부분은 맞고 아직 안 쓰인 뒷부분은 틀린 상태이기 때문이다. `c2h_tracker::active`를 활용한 동기화 메커니즘이 이 문제를 방지하기 위해 존재한다.

### Q7. (Evaluate) 첫 가설로 "DUT 데이터 경로 버그" 라고 단정해도 되는가?
**정답.** 안 됨. Module 08 의 5단계는 DUT 검증을 4단계에 두고 그 전에 SW 엔티티(2)와 HW 인터페이스(3)를 먼저 본다 — TB 측 설정 오류를 먼저 배제해야 함. DUT 결론은 다른 가능성을 모두 배제한 후에만 valid.
**Why.** DUT 버그 단정은 조사의 출발점이 아니라 도달점이다. 데이터 mismatch의 상당 부분은 TB 측 설정 오류(잘못된 IOVA, MR 범위 오류, TB 메모리 초기화 누락)에서 비롯된다. SW 엔티티 검증(IOVA 계산 정확성, MR 설정)과 HW 인터페이스 검증(H2C QID payload, C2H DMA 주소)을 먼저 수행해야 한다. 이 두 단계를 건너뛰고 DUT 버그라 단정하면, TB 수정으로 해결될 문제를 DUT 쪽에서 무한히 찾게 된다.

### Q8. (Create) 첫 mismatch byte 가 4096 이다 (정확히 4 KB 경계). 가설을 작성하고 검증 절차 3단계를 답하시오.
**정답.**
- 가설: page boundary 의 PTE 변환이 잘못됨. iova 가 page 1 → page 2 로 넘어가는 지점에서 PA 가 잘못 계산됨.
- 검증:
  1. `iova_translator` 로그에서 해당 iova 의 PA 변환 추적 (page 0 vs page 1 경계 PTE 확인)
  2. DUT PTW 로그/fsdb 에서 동일 iova 의 PTW 결과와 비교
  3. `buildPageTable` 로그에서 PD0/PD1/PD2 의 해당 page 1 entry 가 정상인지
**Why.** mismatch가 정확히 4 KB 경계(4096 byte)에서 시작하는 것은 page boundary에서 PTE 변환이 틀렸다는 강한 증거다. 두 가지 가능성이 있다: TB의 `iova_translator`가 page 1의 PTE를 잘못 계산하거나, DUT의 PTW가 page table walk에서 다음 페이지 엔트리를 잘못 읽는 경우다. 검증 절차는 먼저 TB 측 변환을 확인한 후 DUT 측과 비교하는 순서를 따른다 — TB 버그를 먼저 배제해야 DUT 버그라 단정할 수 있다.
