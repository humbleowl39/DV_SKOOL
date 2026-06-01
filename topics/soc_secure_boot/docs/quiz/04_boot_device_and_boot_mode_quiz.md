# Quiz — Module 04: Boot Device & Boot Mode

[← Module 04 본문으로 돌아가기](../04_boot_device_and_boot_mode.md)

---

## Q1. (Remember)

Boot mode 결정 우선순위는?

??? answer "정답 / 해설"
    **OTP > Pinstrap > Default**. OTP가 최우선 (양산 후 변경 불가). Pinstrap은 board 설계로 결정. Default는 BootROM hardcoded.

    우선순위가 이 순서인 이유는 각 설정 수단의 변조 저항성과 직결됩니다. OTP는 물리적으로 변경 불가능하므로, 공급망에서 또는 운영 중에 아무도 이 설정을 바꿀 수 없어 가장 높은 신뢰를 받습니다. Pinstrap은 board 조립 시 결정되므로 제조 이후 변경이 어렵지만, 솔더링을 변조하면 이론상 바꿀 수 있습니다. Default는 BootROM에 코드로 박혀 있으나, 위 두 설정이 없을 때의 fallback에 불과합니다. 결국 양산 제품에서는 OTP가 boot 경로를 최종 결정해야 안전합니다.

## Q2. (Understand)

eMMC, UFS, QSPI NOR의 boot 시점 trade-off는?

??? answer "정답 / 해설"
    - **QSPI NOR**: 가장 빠름 (간단한 protocol), 작은 capacity → BootROM은 QSPI 선호
    - **eMMC**: 모바일 표준, mid speed
    - **UFS**: 고속이지만 protocol 복잡 (UPIU/UniPro/M-PHY) → BootROM이 fully support 어려움. BL2 단계에서 본격 사용.

    각 스토리지가 부팅 단계에서 다른 역할을 하는 이유는 BootROM 크기 제약과 초기화 복잡도의 균형입니다. QSPI NOR는 단순한 SPI 프로토콜로 수십 KB 정도의 코드만으로 구동할 수 있어 BootROM의 초기 BL1 로드에 적합합니다. eMMC는 적당한 복잡도로 모바일 환경의 주력입니다. UFS는 GB급 대용량과 고속을 자랑하지만, UniPro/M-PHY 링크 레이어 초기화 코드만으로도 BootROM 용량을 초과하므로, 먼저 QSPI/eMMC로 BL2를 올린 뒤 BL2에서 UFS 드라이버를 초기화하는 2단계 방식이 현실적입니다.

## Q3. (Apply)

Fail-over boot 시나리오 설계 시 고려사항은?

??? answer "정답 / 해설"
    1. **Primary fail trigger**: 서명 실패, device 응답 timeout, image checksum 실패
    2. **Secondary path**: 다른 device (eMMC primary fail → SD secondary)
    3. **Recovery image**: 다른 partition 또는 USB recovery
    4. **Brick 방지**: 모든 path fail해도 minimum recovery 가능
    5. **OTP fuse 후 변경 불가**: fail-over 경로는 사전 설계 + OTP에 정의

    Fail-over 설계에서 가장 자주 놓치는 함정은 "보안성과 복구 가능성의 균형"입니다. fail-over 경로를 너무 넓게 열어 두면 공격자가 의도적으로 primary를 실패시켜 덜 보호된 secondary로 유도할 수 있습니다. 반면 너무 엄격하게 막으면 필드에서 firmware 업데이트 실패 시 기기가 영구적으로 벽돌(brick)이 됩니다. 핵심 원칙은 "recovery path도 동일한 서명 검증을 통과해야 한다"이며, fail-over 허용 횟수나 조건을 OTP에 미리 정의해 공격자가 악용할 수 없게 만들어야 합니다.

## Q4. (Analyze)

Cold boot vs Warm boot의 차이는?

??? answer "정답 / 해설"
    - **Cold boot**: POR (Power-On Reset). 모든 state 0, DRAM 미초기화 → 전체 init sequence (training 포함).
    - **Warm boot**: 시스템 reset. Power 유지, DRAM retention 가능 → DRAM training skip 가능. 빠른 reboot.

    검증: warm boot에서 DRAM retention 정상, cold/warm 둘 다 정상 sequence.

    DV 관점에서 Cold/Warm boot 구분이 중요한 이유는 Secure Boot 시퀀스가 두 경로에서 다르게 동작할 수 있기 때문입니다. Cold boot에서는 DRAM이 초기화되지 않은 상태이므로 검증에 사용할 임시 버퍼를 SRAM에 잡아야 합니다. Warm boot에서는 이전 boot에서 DRAM에 올라온 데이터가 retention되어 있을 수 있으므로, 이 상태가 검증 로직에 영향을 주지 않는지 확인해야 합니다. 두 경로 모두에서 서명 검증이 독립적으로 올바르게 동작하는지를 테스트하는 것이 BootROM DV의 필수 항목입니다.

## Q5. (Evaluate)

BootROM이 UFS를 직접 support하지 않고 BL2에서 처음 활성화하는 이유는?

??? answer "정답 / 해설"
    **BootROM 크기 제약**. BootROM은 mask ROM이라 small (수십 KB). UFS는 protocol stack 크고 (UPIU/UniPro/M-PHY 모두), training/initialization 코드 많음 → BootROM에 fit 불가.

    대신 QSPI NOR 또는 단순 eMMC로 BL1/BL2 load → BL2에서 UFS driver init + 본격 image load. **BL2 = "DRAM + 복잡한 storage 활성화" 단계**.

    이 구조에서 보안 관점의 핵심 질문은 "BL2가 UFS를 활성화할 때 그 UFS 위의 이미지를 믿을 수 있는가?"입니다. 신뢰 체인이 BootROM → BL1 → BL2 순서로 이미 성립해 있으므로, BL2는 검증된 코드입니다. BL2가 UFS에서 읽어 온 BL31/BL33 이미지를 서명 검증한 뒤에만 실행하면, 비록 UFS가 늦게 활성화되더라도 chain of trust는 유지됩니다. 즉, 스토리지의 초기화 순서가 늦더라도 "검증 없이는 실행 없다"는 원칙이 지켜지는 한 보안은 성립합니다.
