# Quiz — Module 05: UFS HCI Quick Reference

[← Module 05 본문으로 돌아가기](../05_quick_reference_card.md)

---

## Q1. (Recall)

UFS 5계층의 약어와 한 줄 책임:

??? answer "정답 / 해설"
    - **Application** — SCSI command 발행
    - **UTP/UPIU** — frame 캡슐화 (transport)
    - **UniPro** — link/network (MIPI)
    - **M-PHY** — physical 시리얼 (MIPI)
    - **Storage** — NAND flash media

## Q2. (Recall)

Queue depth 최대값과 식별 메커니즘은?

??? answer "정답 / 해설"
    Queue depth = **32** (UFS spec). 식별: **Task Tag (5-bit, 0-31)**. Driver가 free Task Tag 할당해 명령 발행, response의 Task Tag로 매칭.

## Q3. (Apply)

UTRD 어디에 sense data가 저장되나?

??? answer "정답 / 해설"
    UTRD 자체에는 저장 안 됨. UTRD는 Response UPIU의 메모리 pointer를 보유. **Response UPIU** 안에 sense data가 포함되어, driver가 그 위치를 읽어 sense key/ASC/ASCQ 파싱.

## Q4. (Apply)

UFS 4.0의 raw bandwidth는 (HS Gear-5, 2 lane)?

??? answer "정답 / 해설"
    Gear-5 = 23.32 Gb/s/lane. 2 lane → **약 46 Gb/s ≈ 5.8 GB/s** raw. UPIU/UniPro overhead 제외 후 실효 약 4-5 GB/s.

## Q5. (Evaluate)

다음 중 UFS 특징이 **아닌** 것은?

- [ ] A. Full-duplex
- [ ] B. SCSI command 기반
- [ ] C. Queue depth 32
- [ ] D. PCIe 인터페이스

??? answer "정답 / 해설"
    **D**. UFS는 **MIPI M-PHY** 시리얼 인터페이스. PCIe는 NVMe. M-PHY는 모바일/저전력에 최적화 (보통 1-4 lane).
