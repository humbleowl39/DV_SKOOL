# Quiz — Module 05: DRAM Quick Reference

[← Module 05 본문으로 돌아가기](../05_quick_reference_card.md)

---

## Q1. (Recall)

다음 timing parameter를 한 줄로:

- tRCD
- tRP
- tCAS / CL
- tRAS
- tREFI

??? answer "정답 / 해설"
    - **tRCD**: ACT → RD/WR 최소 간격 (Row to Column Delay)
    - **tRP**: PRE → ACT 최소 간격 (Row Precharge)
    - **tCAS / CL**: RD → 첫 데이터 (CAS Latency)
    - **tRAS**: ACT → PRE 최소 시간 (Row Active Strobe)
    - **tREFI**: refresh 주기 (DDR4: 7.8μs, DDR5: 3.9μs)

## Q2. (Recall)

Row Hit / Row Miss / Row Closed 중 가장 빠른 access는?

??? answer "정답 / 해설"
    **Row Hit**. tCAS만 필요. 이미 active row에 column access. Scheduler가 Row Hit 비율을 높이는 게 BW 핵심.

## Q3. (Apply)

DDR4 16-bank vs DDR5 32-bank의 검증 영향은?

??? answer "정답 / 해설"
    - DDR5는 BG가 4→8 → tCCD_S 활용 기회 ↑ → BW 측정 시 다른 BG 분산 효과 검증 필요
    - 더 많은 bank → 더 많은 동시 ACT 가능 → BLP 시나리오 확장
    - Refresh도 per-bank refresh 활용폭 ↑ — refresh 동안 traffic 영향 측정에 영향

## Q4. (Analyze)

DDR5 on-die ECC의 한계는?

??? answer "정답 / 해설"
    On-die ECC는 SECDED — single-bit 수정만. **2-bit 이상 에러는 detect만 가능, 수정 불가**. 따라서:
    1. 외부 SECDED ECC도 함께 사용 권장
    2. 2-bit 에러는 system error 인터럽트 발생 → OS/firmware가 처리
    3. ECC scrubbing으로 single-bit 누적 → 2-bit 진행 방지

## Q5. (Evaluate)

다음 DV 버그 중 production silicon에 가장 위험한 것은?

- [ ] A. tRCD 1 cycle 미달
- [ ] B. Refresh 주기 5% 초과
- [ ] C. Training이 cold corner에서 fail
- [ ] D. Scheduler가 Row Hit을 놓침 (BW 5% 저하)

??? answer "정답 / 해설"
    **C**. cold corner training fail = 추운 환경(데이터센터 입고 직후 등)에서만 fail → 발견 어렵고 field에서 발생 가능. A/B는 직접적 fail로 catch 쉬움. D는 functional 정상이지만 성능 저하. 실제 field 위험은 environment-dependent silent corruption이 가장 큼.
