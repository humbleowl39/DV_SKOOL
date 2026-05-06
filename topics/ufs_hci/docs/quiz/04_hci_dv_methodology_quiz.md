# Quiz — Module 04: HCI DV Methodology

[← Module 04 본문으로 돌아가기](../04_hci_dv_methodology.md)

---

## Q1. (Remember)

UFS HCI 검증의 양방향 검증 두 측은?

??? answer "정답 / 해설"
    - **Driver-side**: Register/UTRD/메모리 인터페이스
    - **Device-side**: UPIU/UniPro/M-PHY 측 응답

## Q2. (Understand)

UFS Device Model이 검증에서 하는 역할은?

??? answer "정답 / 해설"
    - SCSI command를 받아 spec대로 응답 (Read/Write/Query)
    - LU별 storage state 모델링 (가상 NAND 영역)
    - 에러 시나리오 inject (CRC, timeout, sense data variants)
    - UPIU 응답 형식 정확성 검증의 reference

## Q3. (Apply)

다음 시나리오의 검증 기법을 매핑하세요.

| 시나리오 | 기법 |
|----------|------|
| (a) UTRD field accuracy | ? |
| (b) Queue depth 32 동작 | ? |
| (c) CRC error 복구 | ? |
| (d) Linux driver 호환성 | ? |

??? answer "정답 / 해설"
    - (a) **UTRD field assertion** + reference compare in scoreboard
    - (b) **Multi-command sequence** + queue depth coverage
    - (c) **Error injection** in M-PHY layer + 복구 sequence 검증
    - (d) **Linux UFS driver 시뮬레이션** (real driver code on virtual SoC)

## Q4. (Analyze)

UFS 검증에서 가장 catch 어려운 silent bug 카테고리는?

??? answer "정답 / 해설"
    **Race condition between SW driver and HW HCI**. 예:
    - SW가 doorbell ring 직후 다른 slot 업데이트 → HCI fetch 시점에 따라 다른 결과
    - SW가 UTRD 작성 완료 전에 doorbell ring → HCI가 incomplete 데이터 fetch
    - Multi-core SW에서 같은 slot을 두 thread가 동시 업데이트

    검증: SW timing variance (delay injection), thread scheduling chaos.

## Q5. (Evaluate)

다음 중 Production silicon에 가장 위험한 결함은?

- [ ] A. Performance 5% 저하
- [ ] B. Linux 5.0 driver와 5.10 driver 모두 동작하지만 5.15에서 fail
- [ ] C. CRC error 복구 50% 성공
- [ ] D. Boot LU read 1% 실패

??? answer "정답 / 해설"
    **D**. Boot 실패는 system 자체가 부팅 안 됨 → 디바이스 brick. 1% rate라도 production scale에서 수만 대 영향. C는 복구 메커니즘이지만 부분적 fail라 silent하게 진행. A는 성능, B는 호환성으로 mitigation 가능.
