# Quiz — Module 01: APB & AHB

[← Module 01 본문으로 돌아가기](../01_apb_ahb.md)

---

## Q1. (Remember)

APB 단일 트랜잭션의 최소 cycle 수와 phase 이름은?

??? answer "정답 / 해설"
    **2 cycle**, **SETUP** (PSEL=1, PENABLE=0) → **ACCESS** (PSEL=1, PENABLE=1, PREADY=1). Wait state 없으면 이 2 cycle이 minimum.

## Q2. (Understand)

AHB-to-APB Bridge는 AHB INCR4 burst를 어떻게 처리하는가?

- [ ] A. APB도 INCR4를 그대로 지원하므로 1번에 전송
- [ ] B. APB는 burst를 지원하지 않으므로 4개의 독립적 APB 단일 전송으로 분해
- [ ] C. Bridge가 4 cycle 한 번에 묶어서 처리
- [ ] D. Bridge가 ERROR 응답

??? answer "정답 / 해설"
    **B**. APB는 burst 개념이 없음. Bridge는 AHB의 burst를 풀어서 APB에 4번의 단일 전송으로 보냄. 면적 절약 vs 성능의 trade-off.

## Q3. (Apply)

AHB Master가 3 연속 Write를 수행 중 A2의 Data Phase에서 Slave가 HREADY=0을 1 cycle 삽입했다. T2의 HADDR 값이 A2일 때, T3의 HADDR 값은?

??? answer "정답 / 해설"
    **A2** (변하지 않음). Wait state 동안 HADDR과 HWDATA 모두 유지. T3에서 HREADY=1이 되면 T4에 A3로 진행. Wait state 중 신호 변경은 가장 흔한 AHB 버그.

## Q4. (Analyze)

AHB HRESP ERROR가 1 cycle이 아닌 2 cycle에 걸쳐 응답되는 이유는?

??? answer "정답 / 해설"
    AHB는 주소-데이터 파이프라인이라 Master가 에러 응답을 받을 때 이미 다음 주소를 발행한 상태. Cycle 1에서 HREADY=0으로 파이프라인을 멈추고 에러를 알리고, Cycle 2에서 HREADY=1로 에러를 확정해 Master가 다음 주소를 안전하게 취소할 시간을 보장.

## Q5. (Evaluate)

APB4에서 PSTRB가 추가된 가장 큰 동기는?

- [ ] A. burst 지원
- [ ] B. byte-level write로 Read-Modify-Write 회피 (원자성)
- [ ] C. multi-master 지원
- [ ] D. clock domain crossing

??? answer "정답 / 해설"
    **B**. APB3까지는 단어 단위 write만 가능 → 32-bit 레지스터의 일부 바이트만 변경하려면 RMW 필요. RMW 도중 다른 주체(예: HW)가 status bit를 set하면 race. PSTRB로 byte-level write가 가능해져 원자성 + 성능 모두 개선.
