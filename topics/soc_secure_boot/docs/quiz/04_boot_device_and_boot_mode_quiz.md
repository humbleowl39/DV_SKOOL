# Quiz — Module 04: Boot Device & Boot Mode

[← Module 04 본문으로 돌아가기](../04_boot_device_and_boot_mode.md)

---

## Q1. (Remember)

Boot mode 결정 우선순위는?

??? answer "정답 / 해설"
    **OTP > Pinstrap > Default**. OTP가 최우선 (양산 후 변경 불가). Pinstrap은 board 설계로 결정. Default는 BootROM hardcoded.

## Q2. (Understand)

eMMC, UFS, QSPI NOR의 boot 시점 trade-off는?

??? answer "정답 / 해설"
    - **QSPI NOR**: 가장 빠름 (간단한 protocol), 작은 capacity → BootROM은 QSPI 선호
    - **eMMC**: 모바일 표준, mid speed
    - **UFS**: 고속이지만 protocol 복잡 (UPIU/UniPro/M-PHY) → BootROM이 fully support 어려움. BL2 단계에서 본격 사용.

## Q3. (Apply)

Fail-over boot 시나리오 설계 시 고려사항은?

??? answer "정답 / 해설"
    1. **Primary fail trigger**: 서명 실패, device 응답 timeout, image checksum 실패
    2. **Secondary path**: 다른 device (eMMC primary fail → SD secondary)
    3. **Recovery image**: 다른 partition 또는 USB recovery
    4. **Brick 방지**: 모든 path fail해도 minimum recovery 가능
    5. **OTP fuse 후 변경 불가**: fail-over 경로는 사전 설계 + OTP에 정의

## Q4. (Analyze)

Cold boot vs Warm boot의 차이는?

??? answer "정답 / 해설"
    - **Cold boot**: POR (Power-On Reset). 모든 state 0, DRAM 미초기화 → 전체 init sequence (training 포함).
    - **Warm boot**: 시스템 reset. Power 유지, DRAM retention 가능 → DRAM training skip 가능. 빠른 reboot.

    검증: warm boot에서 DRAM retention 정상, cold/warm 둘 다 정상 sequence.

## Q5. (Evaluate)

BootROM이 UFS를 직접 support하지 않고 BL2에서 처음 활성화하는 이유는?

??? answer "정답 / 해설"
    **BootROM 크기 제약**. BootROM은 mask ROM이라 small (수십 KB). UFS는 protocol stack 크고 (UPIU/UniPro/M-PHY 모두), training/initialization 코드 많음 → BootROM에 fit 불가.

    대신 QSPI NOR 또는 단순 eMMC로 BL1/BL2 load → BL2에서 UFS driver init + 본격 image load. **BL2 = "DRAM + 복잡한 storage 활성화" 단계**.
