# Quiz — Module 03: DCMAC DV Methodology

[← Module 03 본문으로 돌아가기](../03_dcmac_dv_methodology.md)

---

## Q1. (Remember)

DCMAC 검증의 4가지 축은?

??? answer "정답 / 해설"
    1. **Frame integrity** (FCS)
    2. **AXI-S protocol** (host interface)
    3. **Flow control** (Pause/PFC)
    4. **Error handling** (FEC, undersized/oversized frame)

## Q2. (Understand)

RS-FEC injection 시나리오에서 within / beyond correction limit의 검증 의도는?

??? answer "정답 / 해설"
    - **Within (≤7 symbol error)**: FEC가 자동 복원 → frame이 손상 없이 RX에 도달. 검증: 정상 처리, error counter 정확히 증가.
    - **Beyond (>7 symbol error)**: FEC 복원 불가 → frame drop. 검증: drop 발생, uncorrected error counter ↑, 다음 frame 정상 처리.

## Q3. (Apply)

Line-rate throughput 검증을 위해 traffic generator는 어떻게 동작해야 하나?

??? answer "정답 / 해설"
    - **Back-to-back frame**: IFG 최소(12 bytes)로 연속 발행
    - **Mixed sizes**: small (64) + large (9000) — small frame이 더 IFG overhead 많음
    - **No idle**: TX가 idle하지 않게 buffer 충분히
    - **Long duration**: 통계적 안정성 위해 minimum 100M frames

## Q4. (Analyze)

IFG 위반이 silent bug인 이유는?

??? answer "정답 / 해설"
    IFG는 12 bytes(96 bit time) 이상 필요. 위반 시:
    - 표준 host는 frame을 정상 수신
    - 일부 host의 PHY는 timing slack 의존, IFG < 12면 frame 시작 detect 실패 → drop
    - 즉, host 따라 동작이 다름 — interop 문제로 발현. Self loopback에선 발견 안 됨.

    검증: traffic generator IFG measurement + assertion.

## Q5. (Evaluate)

다음 중 Production silicon에서 가장 위험한 bug는?

- [ ] A. Throughput 5% 저하
- [ ] B. Lane mismatch silent — CRC pass but wrong channel
- [ ] C. RS-FEC 복원율 99% (1% drop)
- [ ] D. Pause frame 응답 지연

??? answer "정답 / 해설"
    **B**. Silent corruption — 검출 메커니즘 자체가 의미 없게 됨. Network 환경에서 데이터가 잘못된 호스트에 도달 → 보안/correctness 모두 영향. C는 drop이라도 명시적으로 catch 가능. A/D는 성능/응답 영향이지만 silent 아님.
