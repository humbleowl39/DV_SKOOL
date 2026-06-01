# Quiz — Module 09: Quick Reference Card

[← Module 09 본문으로 돌아가기](../09_quick_reference_card.md)

---

## Q1. (Remember)

Extended Capability ID 0x0001, 0x000F, 0x0010 의 이름을 적어라.

??? answer "정답 / 해설"
    - 0x0001 = **AER** (Advanced Error Reporting)
    - 0x000F = **ATS** (Address Translation Service)
    - 0x0010 = **SR-IOV** (Single Root IO Virtualization)

    Extended Capability ID 는 4KB Configuration Space 의 256 byte 이후 영역(Extended Capability list)에서 각 Capability 를 식별하는 12-bit 코드다. 이 세 값은 DV 검증이나 디버깅 시 lspci 출력에서 자주 보이므로 기억해두면 유용하다. AER(0x0001)은 오류 분류 및 리포팅, ATS(0x000F)는 IOMMU 주소 변환 캐싱, SR-IOV(0x0010)는 가상화를 위한 VF 생성이라는 각각의 기능을 연결해 외우면 쉽다.

## Q2. (Understand)

Address Routing 과 ID Routing 이 사용되는 TLP 는 각각 무엇인가?

??? answer "정답 / 해설"
    - **Address Routing**: MRd, MWr, IORd, IOWr (memory/IO address 기반)
    - **ID Routing**: CfgRd0/Wr0, CfgRd1/Wr1, Cpl/CplD (BDF 기반), 일부 ID-routed Msg

    Implicit routing 도 있음 (일부 Msg, "to RC" / "broadcast").

    라우팅 방식의 차이는 "어떤 정보로 목적지를 찾는가"로 구분된다. Address Routing 은 TLP header 안의 메모리/IO 주소를 Switch 의 Memory Base/Limit 레지스터와 비교해 포워딩 방향을 결정한다. ID Routing 은 목적지 BDF 가 헤더에 명시되어 있어 Switch 가 Bus 번호 범위를 기준으로 포워딩한다. Configuration 은 아직 주소가 없으므로 BDF 로 라우팅하고, Completion 은 Requester ID(출발지 BDF)를 보고 돌아가는 방향을 찾는다.

## Q3. (Apply)

Linux 에서 device BDF 0000:01:00.0 의 Link status (현재 speed/width) 를 확인하는 명령은?

??? answer "정답 / 해설"
    ```bash
    lspci -vvv -s 0000:01:00.0 | grep -A2 LnkSta
    ```

    출력 예:
    ```
    LnkSta: Speed 16GT/s, Width x16
            TrErr- Train- SlotClk+ DLActive+ BWMgmt- ABWMgmt-
    ```

    Speed = Gen rate (16 GT/s = Gen4), Width = lane 수.

    `lspci -vvv` 는 모든 Capability 를 펼쳐 보여주는데, `-s` 플래그로 특정 BDF 만 선택하면 출력이 간결해진다. `LnkSta` 는 Link Status 레지스터로, 협상이 완료된 실제 동작 속도와 레인 수를 보여준다. `LnkCap` 이 "이 디바이스가 지원하는 최대치"라면 `LnkSta` 는 "지금 실제로 동작 중인 값"이므로, Gen 다운그레이드나 레인 축소 문제를 진단할 때 두 필드를 함께 비교하는 것이 좋다.

## Q4. (Analyze)

"DV checklist 의 30-second mental check 8 항목" 중 가장 자주 놓치는 항목은? 그 이유는?

??? answer "정답 / 해설"
    **"Sequence # wraparound (4096 modulo) 처리 modulo-aware"** 가 가장 자주 놓침.

    이유:

    - Sequence # 는 12-bit modulo 4096 — 정상 traffic 으로는 도달까지 시간 걸려 sanity test 에서 안 보임.
    - 일반 sequence number 코드를 그대로 옮기면 `>` 비교가 정상 looking 하지만 wrap 시점에 false fail/silent miss.
    - Code review 에서 "이 비교는 modulo-aware 인가?" 명시 검증이 없으면 통과되기 쉬움.

    추가로 자주 놓침: AER counter 의 trend monitoring, ASPM L1 latency 영향, ACS 정책의 P2P 차단 default.

    Sequence # wraparound 는 정상 트래픽으로 4095 패킷을 보내야 발생하기 때문에 단기 smoke test 에서는 절대 재현되지 않는다. 이 때문에 TB 가 비교 로직을 단순한 `>` 대신 modulo-aware 한 방식으로 구현하지 않으면, 코드 리뷰에서도 "숫자가 맞아 보인다"고 통과되기 쉽다. 실제로 번인(burn-in) 이나 장시간 regression 에서 처음 터지는 유형이므로, DV checklist 에 "Sequence # 비교가 4096 modulo 기준인가?" 항목을 명시적으로 포함시키는 것이 베스트 프랙티스다.

## Q5. (Evaluate)

"BAR sizing 의 'write all-1' 은 device register 를 망가뜨릴 위험이 있다" 는 우려를 평가하라.

??? answer "정답 / 해설"
    **틀림 — 안전하다**.

    이유:

    1. **PCIe spec 가 정의** — BAR sizing 동작 시 device 는 0xFFFFFFFF write 를 받으면 size 검증 모드만 활성화, 실제 register 는 변경 안 됨.
    2. 그래서 OS 가 부팅 때마다 안전하게 호출, hot plug 시에도.
    3. SW 가 sizing 후 read → ~size+1 = 요청 size, 정상 base 주소 write 시 device 가 그 영역을 자기 영역으로 인식.

    이는 spec 의 안전 보장 — device 구현이 잘못되어 진짜 register 가 망가지면 spec 위반 (compliance fail).

    "위험" 이라는 우려는 spec 을 모르는 직관 — 실제로는 가장 안전하게 설계된 메커니즘 중 하나.

    PCIe 스펙은 BAR 에 0xFFFFFFFF 를 쓰는 행위를 "크기 질의"로 정의하고, 이 상황에서 디바이스는 실제 동작 레지스터가 아닌 "크기 응답 모드"로만 반응하도록 규정한다. 따라서 OS 가 부팅할 때마다, Hot Plug 때마다 이 write 를 반복해도 디바이스 상태가 변하지 않는다. 만약 어떤 디바이스 구현이 이 write 에 의해 실제 상태가 변한다면, 그것은 PCIe compliance 위반이므로 spec 을 올바르게 구현한 디바이스에서는 이 우려 자체가 성립하지 않는다.
