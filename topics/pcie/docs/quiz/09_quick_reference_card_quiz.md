# Quiz — Module 09: Quick Reference Card

[← Module 09 본문으로 돌아가기](../09_quick_reference_card.md)

---

## Q1. (Remember)

Extended Capability ID 0x0001, 0x000F, 0x0010 의 이름을 적어라.

??? answer "정답 / 해설"
    - 0x0001 = **AER** (Advanced Error Reporting)
    - 0x000F = **ATS** (Address Translation Service)
    - 0x0010 = **SR-IOV** (Single Root IO Virtualization)

## Q2. (Understand)

Address Routing 과 ID Routing 이 사용되는 TLP 는 각각 무엇인가?

??? answer "정답 / 해설"
    - **Address Routing**: MRd, MWr, IORd, IOWr (memory/IO address 기반)
    - **ID Routing**: CfgRd0/Wr0, CfgRd1/Wr1, Cpl/CplD (BDF 기반), 일부 ID-routed Msg

    Implicit routing 도 있음 (일부 Msg, "to RC" / "broadcast").

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

## Q4. (Analyze)

"DV checklist 의 30-second mental check 8 항목" 중 가장 자주 놓치는 항목은? 그 이유는?

??? answer "정답 / 해설"
    **"Sequence # wraparound (4096 modulo) 처리 modulo-aware"** 가 가장 자주 놓침.

    이유:

    - Sequence # 는 12-bit modulo 4096 — 정상 traffic 으로는 도달까지 시간 걸려 sanity test 에서 안 보임.
    - 일반 sequence number 코드를 그대로 옮기면 `>` 비교가 정상 looking 하지만 wrap 시점에 false fail/silent miss.
    - Code review 에서 "이 비교는 modulo-aware 인가?" 명시 검증이 없으면 통과되기 쉬움.

    추가로 자주 놓침: AER counter 의 trend monitoring, ASPM L1 latency 영향, ACS 정책의 P2P 차단 default.

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
