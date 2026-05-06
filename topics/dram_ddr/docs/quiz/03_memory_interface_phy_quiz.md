# Quiz — Module 03: Memory Interface / PHY

[← Module 03 본문으로 돌아가기](../03_memory_interface_phy.md)

---

## Q1. (Remember)

PHY Training의 핵심 4가지 종류를 답하세요.

??? answer "정답 / 해설"
    1. **Write Leveling (WL)**: CK ↔ DQS 위상 정렬
    2. **Read DQ Training**: read eye center 찾기
    3. **CA Training**: CMD bus margin (DDR5에서 중요)
    4. **VREF Training**: reference voltage 최적화

    + ZQ Calibration: 임피던스 보정.

## Q2. (Understand)

PVT 변동이 timing에 미치는 영향과 보정 방법은?

??? answer "정답 / 해설"
    **영향**: 시리콘 process variation, 전압 droop, 온도 변화 모두 신호 propagation delay 변경 → eye 위치 이동.

    **보정**: 주기적 retraining (긴 시간 후), 온도 monitoring으로 trigger, ZQ Calibration (임피던스). 모든 보정은 traffic 일시 중단 또는 idle 시 수행.

## Q3. (Apply)

CTLE와 DFE의 차이와 각각의 적용 위치는?

??? answer "정답 / 해설"
    - **CTLE (Continuous Time Linear Equalizer)**: 아날로그 고주파 부스트로 신호 왜곡 보정. 모든 비트에 동등 적용.
    - **DFE (Decision Feedback Equalizer)**: 이전 비트의 ISI를 디지털로 제거. 비트별로 동작.

    적용:
    - **DRAM 수신단 (Write)**: DFE
    - **PHY 수신단 (Read)**: CTLE + DFE 조합

## Q4. (Analyze)

DDR5에서 CA Training이 새로 필수가 된 이유는?

??? answer "정답 / 해설"
    DDR5는 CA bus가 **multiplexed** (저속에서 적어진 핀 수). 멀티플렉싱으로 timing 마진 축소 → 별도 training 없이는 잘못된 명령 디코딩 가능. Training으로 CA의 setup/hold 마진 최적화.

## Q5. (Evaluate)

Training 실패의 silent corruption은 어떻게 catch하는가?

??? answer "정답 / 해설"
    - **Functional**: training 후 data integrity test (write/read pattern). Pattern mismatch면 fail.
    - **Performance**: training 후 BW/latency가 spec 이하면 sub-optimal training 의심.
    - **Assertion**: training 완료 sequence가 spec과 일치하는지 SVA로 검증.
    - **Corner cases**: PVT corner (cold/hot, low/high VDD)에서 training 동작 확인.

    Silent corruption의 흔한 패턴: training이 marginal pass → 정상 traffic은 OK이지만 stress 상황에서 fail.
