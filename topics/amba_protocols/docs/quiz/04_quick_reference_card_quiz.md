# Quiz — Module 04: AMBA Quick Reference

[← Module 04 본문으로 돌아가기](../04_quick_reference_card.md)

---

## Q1. (Recall)

다음 4개 프로토콜을 게이트 비용 / 성능 순으로 정렬하세요: APB, AHB, AXI, AXI-Stream

??? answer "정답 / 해설"
    **게이트 비용**: APB < AHB < AXI ≈ AXI-Stream
    **성능 (대역폭)**: APB ≪ AHB < AXI ≈ AXI-Stream

## Q2. (Understand)

VALID/READY 데드락 방지 규칙을 한 문장으로 표현하세요.

??? answer "정답 / 해설"
    **"VALID(Source)는 READY와 무관하게 올라가야 한다."** Source는 READY를 기다리지 않음. Sink는 자유롭게 READY 토글 가능.

## Q3. (Apply)

다음 SoC 시나리오에서 가장 적절한 인터페이스를 고르세요.

| 시나리오 | 추천 |
|----------|------|
| GPU 메모리 access (high BW) | ? |
| Timer 레지스터 설정 | ? |
| Network packet input | ? |
| Legacy DMA controller | ? |

??? answer "정답 / 해설"
    - GPU 메모리 → **AXI** (high BW + outstanding)
    - Timer 레지스터 → **APB** (단순, 면적 최소)
    - Network packet input → **AXI-Stream** (가변 길이 + TLAST)
    - Legacy DMA → **AHB** 또는 AXI

## Q4. (Analyze)

AXI에서 WSTRB이 모두 0인 W beat는 protocol 위반인가?

??? answer "정답 / 해설"
    **위반 아님**. 유효한 전송이지만 실질적 쓰기는 발생하지 않음 (모든 byte mask 0). Burst 중 특정 beat skip용으로 활용 가능.

## Q5. (Evaluate)

AHB가 AXI에 대부분 대체된 현대에도 여전히 사용되는 이유 두 가지를 들어보세요.

??? answer "정답 / 해설"
    1. **레거시 IP 호환** — 수십 년간 누적된 AHB IP 그대로 통합 가능
    2. **AXI 대비 작은 게이트 + 충분한 중간 성능** — 단순한 인터커넥트에서는 AXI의 5채널 분리가 과잉
