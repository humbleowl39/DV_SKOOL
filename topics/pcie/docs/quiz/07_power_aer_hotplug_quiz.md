# Quiz — Module 07: Power, AER, Hot Plug

[← Module 07 본문으로 돌아가기](../07_power_aer_hotplug.md)

---

## Q1. (Remember)

D-state 와 L-state 의 의미 차이는?

??? answer "정답 / 해설"
    - **D-state**: **device** 의 power state — D0/D1/D2/D3hot/D3cold. OS / driver 가 PCI-PM Capability 로 관리.
    - **L-state**: **link** 의 LTSSM 상태 — L0/L0s/L1/L1.1/L1.2/L2. ASPM 이 자동 진입 가능.

    독립적이지만 보통 D 가 깊으면 L 도 깊음. D3hot + L0 (link up but device sleep) 같은 조합도 가능.

    D-state 는 "디바이스의 전원 상태"이고 L-state 는 "링크 자체의 전원 상태"다. 관리 주체가 다른 것이 핵심이다. D-state 는 OS/드라이버가 소프트웨어로 전환하고, L-state 는 ASPM 이 링크 양쪽의 idle 감지에 따라 자동으로 진입한다. 두 상태는 독립적으로 동작하므로 D3hot(디바이스 잠듦)인데 링크는 L0(활성)으로 유지하는 구성이 가능하며, 반대로 디바이스가 D0 이어도 링크가 L1 에 있을 수 있다.

## Q2. (Understand)

AER 의 3 error class 와 처리를 매칭하라.

??? answer "정답 / 해설"
    | Class | 예 | 처리 |
    |-------|-----|------|
    | Correctable | LCRC error, Bad TLP, Replay rollover | log only, HW 자동 회복 |
    | Uncorrectable Non-Fatal | Cpl Timeout, UR, ECRC, Poisoned TLP | driver notify, recovery 가능 |
    | Uncorrectable Fatal | Surprise Down, Malformed TLP, DLL Protocol | link retrain 또는 system reset |

    AER 분류의 기준은 "하드웨어가 스스로 복구할 수 있는가"와 "복구 불가능하더라도 시스템이 계속 동작할 수 있는가"다. Correctable 은 DLL 의 retry 메커니즘이 이미 처리했으므로 SW 에는 카운터 증가만 보고된다. Uncorrectable Non-Fatal 은 해당 트랜잭션은 실패했지만 링크 자체는 살아있어 드라이버가 에러 복구를 시도할 수 있다. Fatal 은 링크 또는 디바이스 자체의 상태가 신뢰할 수 없어 재훈련이나 리셋이 필요한 가장 심각한 수준이다.

## Q3. (Apply)

ASPM L1 이 enable 된 환경에서 idle 직후 packet 도착 시 latency 영향은?

??? answer "정답 / 해설"
    - L1 entry 후 link 는 electrical idle.
    - Wakeup: L1 → Recovery → L0 의 LTSSM 전이 필요.
    - **Exit latency ≈ 5-10 us** (Gen3+ 기준).

    이 시간 동안 packet 송신 불가 → first packet 의 latency 가 ~ μs 단위로 spike.

    Latency-sensitive 워크로드 (NVMe SLA, GPU 통신) 에서는 ASPM L1 disable 권장. Throughput-only 에서는 enable 가능.

    L1 에 진입하면 링크 양쪽의 SerDes 가 저전력 모드로 전환되어 전기적으로 idle 상태가 된다. 패킷이 도착하면 링크를 깨워야 하는데, L1 → Recovery → L0 의 LTSSM 전이에 수 마이크로초가 소요된다. 이 기간 동안 패킷은 버퍼에서 대기하므로 첫 번째 패킷의 지연이 급격히 커진다. NVMe 의 I/O 레이턴시 SLA 나 GPU 간 통신처럼 수 마이크로초 단위가 중요한 워크로드에서 ASPM L1 을 활성화하면 예측 불가능한 지연 스파이크가 발생할 수 있다.

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

    Surprise Removal 시 Hot Plug 와 AER 가 동시에 신호를 발생시키는 것이 핵심이다. Hot Plug handler 가 "디바이스가 물리적으로 사라졌음"을 이미 알고 있으므로, AER 의 Surprise Down 에 대해 reset 을 시도하면 안 된다. 디바이스가 없는데 reset 을 반복하면 무한 루프에 빠지는 것이 드라이버 버그의 전형적인 패턴이다. 올바른 처리는 Hot Plug handler 가 주도권을 가지고 드라이버 언바인드 → 디바이스 트리 제거 → 슬롯 전원 차단 순서로 정리하는 것이다.

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

    Correctable error 는 "지금 당장은 복구됐다"는 의미이지 "문제가 없다"는 의미가 아니다. 하드웨어가 자동으로 회복했다는 것은 그 회복 메커니즘(DLL retry, EQ 재조정)이 동작했다는 뜻이고, 이 빈도가 높아진다는 것은 시스템이 점점 한계에 가까워지고 있다는 선행 지표다. 데이터센터 운영에서 correctable error 가 증가하는 링크를 preventive 교체하는 정책은 이 이유 때문이며, "동작하니까 무시"는 eventual Uncorrectable Fatal 로 가는 지름길이다.
