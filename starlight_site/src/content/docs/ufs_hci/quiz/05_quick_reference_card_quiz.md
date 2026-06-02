---
title: "Quiz — Module 05: UFS HCI Quick Reference"
---

[← Module 05 본문으로 돌아가기](../../05_quick_reference_card/)

---

## Q1. (Recall)

UFS 5계층의 약어와 한 줄 책임:

<details>
<summary>정답 / 해설</summary>

- **Application** — SCSI command 발행
- **UTP/UPIU** — frame 캡슐화 (transport)
- **UniPro** — link/network (MIPI)
- **M-PHY** — physical 시리얼 (MIPI)
- **Storage** — NAND flash media

이 5계층 구조가 중요한 이유는 각 계층이 DV에서 독립적인 검증 경계를 형성하기 때문입니다. UTP/UPIU 레이어는 SCSI 명령이 올바르게 캡슐화되는지를 검증하는 구간이고, UniPro는 링크 신뢰성, M-PHY는 신호 무결성을 담당합니다. 계층별 책임을 명확히 알아야 버그가 어느 계층에서 발생했는지 분류할 수 있습니다.

</details>
## Q2. (Recall)

Queue depth 최대값과 식별 메커니즘은?

<details>
<summary>정답 / 해설</summary>

Queue depth = **32** (UFS spec). 식별: **Task Tag (5-bit, 0-31)**. Driver가 free Task Tag 할당해 명령 발행, response의 Task Tag로 매칭.

Queue depth 32와 Task Tag의 관계를 이해하는 핵심은 "Task Tag가 식별자이고 queue depth가 동시 허용 개수"라는 것입니다. Driver는 사용 가능한 Task Tag를 비트맵으로 관리하며, 명령을 발행할 때마다 free slot을 할당하고 응답이 돌아오면 해당 Tag를 반환합니다. 이 메커니즘이 없으면 동시에 여러 명령이 진행 중일 때 어떤 응답이 어떤 명령에 대한 것인지 알 수 없어 다중 명령 큐잉 자체가 불가능합니다.

</details>
## Q3. (Apply)

UTRD 어디에 sense data가 저장되나?

<details>
<summary>정답 / 해설</summary>

UTRD 자체에는 저장 안 됨. UTRD는 Response UPIU의 메모리 pointer를 보유. **Response UPIU** 안에 sense data가 포함되어, driver가 그 위치를 읽어 sense key/ASC/ASCQ 파싱.

"UTRD 자체에 저장되지 않는다"는 것이 핵심입니다. UTRD는 32 bytes로 고정된 경량 디스크립터이므로 가변 길이의 sense data를 직접 담을 수 없습니다. 대신 UTRD는 Response UPIU가 있는 메모리 위치를 포인터로 가리키고, Response UPIU 내부의 sense data 섹션에 실제 에러 정보가 들어 있습니다. 드라이버는 명령 완료 후 OCS를 확인하고, 에러가 있을 경우 UTRD 포인터를 따라가 Response UPIU에서 sense key/ASC/ASCQ를 읽어 복구 동작을 결정합니다.

</details>
## Q4. (Apply)

UFS 4.0의 raw bandwidth는 (HS Gear-5, 2 lane)?

<details>
<summary>정답 / 해설</summary>

Gear-5 = 23.32 Gb/s/lane. 2 lane → **약 46 Gb/s ≈ 5.8 GB/s** raw. UPIU/UniPro overhead 제외 후 실효 약 4-5 GB/s.

이 수치를 기억해야 하는 이유는 DV 성능 테스트에서 목표 대역폭을 설정할 때 raw 수치와 실효 수치를 구분해야 하기 때문입니다. 단순히 "5.8 GB/s가 나와야 한다"고 테스트하면 UPIU와 UniPro 오버헤드로 인해 항상 실패합니다. 실제 달성 가능한 실효 대역폭(4~5 GB/s)을 기준으로 성능 커버리지 목표를 설정해야 하며, raw 값과 실효 값의 차이를 오버헤드 분석의 데이터로 활용할 수 있습니다.

</details>
## Q5. (Evaluate)

다음 중 UFS 특징이 **아닌** 것은?

- [ ] A. Full-duplex
- [ ] B. SCSI command 기반
- [ ] C. Queue depth 32
- [ ] D. PCIe 인터페이스

<details>
<summary>정답 / 해설</summary>

**D**. UFS는 **MIPI M-PHY** 시리얼 인터페이스. PCIe는 NVMe. M-PHY는 모바일/저전력에 최적화 (보통 1-4 lane).

D가 정답인 이유는 UFS의 물리 계층이 MIPI M-PHY이기 때문입니다. PCIe 인터페이스는 NVMe에서 사용하며, UFS와는 목표 시장도 다르고 전력 소비 특성도 다릅니다. 나머지 보기 A(Full-duplex), B(SCSI command 기반), C(Queue depth 32)는 모두 UFS의 실제 특징이므로 오답입니다. UFS와 NVMe를 혼동하는 가장 흔한 오류가 인터페이스 혼용이므로, 이 구분은 반드시 기억해야 합니다.

</details>
