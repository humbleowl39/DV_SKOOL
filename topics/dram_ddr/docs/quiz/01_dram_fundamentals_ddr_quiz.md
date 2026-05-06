# Quiz — Module 01: DRAM Fundamentals + DDR4/5

[← Module 01 본문으로 돌아가기](../01_dram_fundamentals_ddr.md)

---

## Q1. (Remember)

DRAM의 한 cell은 어떤 기본 회로 요소로 구성되나?

??? answer "정답 / 해설"
    **1 capacitor + 1 access transistor (1T1C)**. 커패시터에 전하를 저장하여 1비트 저장. 누설 때문에 주기적 refresh 필수.

## Q2. (Understand)

ACT → RD → PRE 명령 시퀀스에서 각 명령의 역할은?

??? answer "정답 / 해설"
    - **ACT**: row 데이터를 sense amplifier로 가져옴 (row open).
    - **RD**: open된 row의 column을 읽음 (가능한 여러 번).
    - **PRE**: row를 닫고 bank를 다음 ACT 가능 상태로 (precharge).

## Q3. (Apply)

DDR4 vs DDR5 핵심 차이 4가지를 들어보세요.

??? answer "정답 / 해설"
    1. **2-channel split**: DDR5 single 64-bit → dual 32-bit channels (HPC BW ↑)
    2. **Bank Group**: 4→8 (interleaving 기회 ↑)
    3. **on-die ECC**: DDR5는 SECDED on-die 표준
    4. **VDD**: 1.2V → 1.1V (전력 ↓)
    5. (추가) Refresh: refresh granularity 향상

## Q4. (Analyze)

같은 bank에 연속 access하면 throughput이 떨어지는 이유는?

??? answer "정답 / 해설"
    같은 bank에서 다른 row에 access하려면 PRE → ACT 필요 (tRP + tRCD 비용). 같은 row면 row hit이지만 다른 row면 row miss → 수십 cycle 패널티. **다른 bank로 분산하면 동시 ACT 가능** → BLP 활용.

## Q5. (Evaluate)

LPDDR5에서 WCK를 CK와 분리한 동기는?

??? answer "정답 / 해설"
    **전력 절감**. 명령(CK)은 저주파로 충분, 데이터(WCK)만 고주파. 같은 클럭이면 CK도 불필요한 고주파 토글 → 전력 낭비. WCK는 traffic 있을 때만 토글, idle 시 정지로 추가 절감.
