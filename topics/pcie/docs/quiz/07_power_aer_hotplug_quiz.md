# Quiz — Module 07: Power, AER, Hot Plug

[← Module 07 본문으로 돌아가기](../07_power_aer_hotplug.md)

---

## Q1. (Remember)

D-state 와 L-state 의 의미 차이는?

??? answer "정답 / 해설"
    - **D-state**: **device** 의 power state — D0/D1/D2/D3hot/D3cold. OS / driver 가 PCI-PM Capability 로 관리.
    - **L-state**: **link** 의 LTSSM 상태 — L0/L0s/L1/L1.1/L1.2/L2. ASPM 이 자동 진입 가능.

    독립적이지만 보통 D 가 깊으면 L 도 깊음. D3hot + L0 (link up but device sleep) 같은 조합도 가능.

## Q2. (Understand)

AER 의 3 error class 와 처리를 매칭하라.

??? answer "정답 / 해설"
    | Class | 예 | 처리 |
    |-------|-----|------|
    | Correctable | LCRC error, Bad TLP, Replay rollover | log only, HW 자동 회복 |
    | Uncorrectable Non-Fatal | Cpl Timeout, UR, ECRC, Poisoned TLP | driver notify, recovery 가능 |
    | Uncorrectable Fatal | Surprise Down, Malformed TLP, DLL Protocol | link retrain 또는 system reset |

## Q3. (Apply)

ASPM L1 이 enable 된 환경에서 idle 직후 packet 도착 시 latency 영향은?

??? answer "정답 / 해설"
    - L1 entry 후 link 는 electrical idle.
    - Wakeup: L1 → Recovery → L0 의 LTSSM 전이 필요.
    - **Exit latency ≈ 5-10 us** (Gen3+ 기준).

    이 시간 동안 packet 송신 불가 → first packet 의 latency 가 ~ μs 단위로 spike.

    Latency-sensitive 워크로드 (NVMe SLA, GPU 통신) 에서는 ASPM L1 disable 권장. Throughput-only 에서는 enable 가능.

## Q4. (Analyze)

Surprise Removal 시 Hot Plug 와 AER 가 어떻게 협력해 처리하는지 분석하라.

??? answer "정답 / 해설"
    1. **Hot Plug 의 Presence Detect Changed** 비트 set → MSI.
    2. **동시에 AER 의 Surprise Down (Uncorrectable Fatal)** 검출 → ERR_FATAL Message + AER 카운터.
    3. SW 의 Hot Plug handler 가 두 신호를 받아:
        - Driver unbind (in-flight transaction 정리)
        - Device tree 에서 제거
        - AER 의 추가 reset 시도 안 함 (device 자체가 사라짐 — reset fail = 무한 loop 위험)
    4. Slot Power off (있다면).

    → Hot Plug capability 를 인식하지 못하는 SW 는 AER 의 Surprise Down 만 보고 reset 시도 → 무한 loop. 이게 driver bug 의 단골.

## Q5. (Evaluate)

"Correctable error 가 자주 발생해도 동작은 정상이니 무시해도 된다" 는 정책의 평가는?

??? answer "정답 / 해설"
    **부적절**.

    Correctable error 가 자주 발생 = silent reliability 악화의 신호일 수 있음:

    1. **PHY BER 점진 악화**: Connector 노화, PCB cracks, 온도 변화 → LCRC error 증가.
    2. **EQ margin 감소**: Recovery 빈발 직전.
    3. **부분 channel 손상**: 일부 lane 만 fail → eventually surprise down 가능.

    **올바른 정책**:

    - Threshold-based alert: 단위 시간당 correctable count 가 임계 초과 시 log + alert.
    - Trend monitoring: 동일 baseline 의 link 들 사이 비교.
    - Replacement policy: data center 에서는 임계 초과 device 를 preventive replace.

    "동작 정상 = 무시" 는 production 환경의 리스크 관리 실패.
