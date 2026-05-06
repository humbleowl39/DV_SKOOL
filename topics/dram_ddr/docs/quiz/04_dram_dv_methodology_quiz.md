# Quiz — Module 04: DRAM DV Methodology

[← Module 04 본문으로 돌아가기](../04_dram_dv_methodology.md)

---

## Q1. (Remember)

DRAM 검증의 3가지 검증 축은?

??? answer "정답 / 해설"
    1. **Timing**: 모든 timing constraint (tRCD/tRP/tRC/tFAW/tREFI 등) 준수
    2. **Data integrity**: write/read 데이터 정합성, ECC 동작
    3. **Performance**: BW, latency, QoS 효율

## Q2. (Understand)

DRAM Behavioral Model이 검증에서 하는 역할은?

??? answer "정답 / 해설"
    JEDEC 명령 sequence에 정의된 DRAM의 응답을 모사. MC가 ACT/RD/WR/PRE/REF를 발행하면 spec대로 동작 (timing 응답, data return, refresh 동작 등). DV에서는 실제 DRAM 칩 없이 timing/integrity 검증 가능.

    + Error injection: ECC fault, refresh miss, training failure 시나리오를 model에 삽입해 corner case 검증.

## Q3. (Apply)

다음 시나리오에 적합한 검증 기법을 매핑하세요.

| 시나리오 | 기법 |
|----------|------|
| (a) tRCD 위반 검출 | ? |
| (b) BW regression | ? |
| (c) Refresh 누락 | ? |
| (d) ECC SECDED 동작 | ? |

??? answer "정답 / 해설"
    - (a) **SVA bind**: timing constraint를 SVA로 표현, simulator가 자동 위반 catch
    - (b) **Performance Reference + Scoreboard**: AXI request/response timestamp로 BW 계산
    - (c) **Refresh Counter assertion**: tREFI 내 모든 row가 한 번 이상 REF 받았는지 확인
    - (d) **Behavioral Model error injection**: 1-bit 에러 주입 → MC가 수정해 정확한 데이터 반환 확인

## Q4. (Analyze)

Performance Reference로 측정해야 하는 핵심 지표 3가지는?

??? answer "정답 / 해설"
    1. **순차 read/write BW** — 이론 대비 효율%
    2. **랜덤 access BW** — bank/row hit 패턴 영향
    3. **R/W mix 시 BW** — batch drain의 효과
    + (추가) **Per-master latency** — QoS별 차등 처리 검증

## Q5. (Evaluate)

다음 중 silent corruption 위험이 가장 큰 시나리오는?

- [ ] A. Refresh count assertion fail
- [ ] B. Training이 marginal하게 pass
- [ ] C. ECC double-bit error 검출
- [ ] D. tRCD violation

??? answer "정답 / 해설"
    **B**. Training pass면 정상 동작처럼 보이지만 PVT 변동 시 fail 가능 → silent corruption. A/C/D는 모두 직접적 fail/error 신호 발생. PVT corner sweep + stress test로 marginal training catch 필요.
