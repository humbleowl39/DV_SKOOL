# Quiz — Module 04: AMBA Quick Reference

[← Module 04 본문으로 돌아가기](../04_quick_reference_card.md)

---

## Q1. (Recall)

다음 4개 프로토콜을 게이트 비용 / 성능 순으로 정렬하세요: APB, AHB, AXI, AXI-Stream

??? answer "정답 / 해설"
    **게이트 비용**: APB < AHB < AXI ≈ AXI-Stream
    **성능 (대역폭)**: APB ≪ AHB < AXI ≈ AXI-Stream

    게이트 비용과 성능은 프로토콜의 복잡도에 비례합니다. APB는 SETUP→ACCESS 2단계 핸드셰이크와 소수의 제어 신호만으로 구성되어 구현이 가장 단순하고 면적이 가장 작습니다. AHB는 파이프라인과 burst를 지원하면서 복잡도와 면적이 커지지만, 5채널 분리·outstanding·OoO를 갖춘 AXI에 비하면 훨씬 작습니다. AXI-Stream은 주소 채널이 없는 대신 데이터 경로 신호(TDATA/TKEEP/TLAST 등)가 많아서 채널 수 관점에서는 AXI보다 단순하지만, 데이터 버스가 넓을 때 게이트 비용은 AXI와 비슷한 수준이 됩니다.

## Q2. (Understand)

VALID/READY 데드락 방지 규칙을 한 문장으로 표현하세요.

??? answer "정답 / 해설"
    **"VALID(Source)는 READY와 무관하게 올라가야 한다."** Source는 READY를 기다리지 않음. Sink는 자유롭게 READY 토글 가능.

    이 규칙이 존재하는 이유는 데드락 방지입니다. Source가 "READY가 1이 되면 VALID를 올리겠다"고 기다리고, Sink가 "VALID가 1이 되면 READY를 올리겠다"고 기다리면, 둘 다 상대방이 먼저 움직이기를 기다리는 교착 상태가 됩니다. 이를 방지하기 위해 AXI/AXI-Stream 사양은 Source에게 일방적으로 먼저 움직이도록 강제합니다. 반면 Sink(READY 측)는 Source의 VALID와 무관하게 자유롭게 READY를 올리거나 내릴 수 있습니다.

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

    각 선택의 이유를 살펴보면, GPU는 대규모 메모리 접근과 높은 대역폭이 필요하고 여러 요청을 동시에 처리하는 outstanding 능력이 핵심이므로 AXI가 적합합니다. Timer는 클럭 설정, 카운터 제어 등 단순한 레지스터 몇 개를 읽고 쓰는 것이 전부이므로, 면적이 가장 작은 APB로 충분합니다. 네트워크 패킷은 가변 길이이고 주소 지정 없이 순서대로 처리되는 스트림 특성을 가지므로 TLAST를 지원하는 AXI-Stream이 자연스럽습니다. Legacy DMA는 오랜 기간 AHB IP로 구현된 경우가 많아 그대로 활용 가능하고, 새로 설계할 경우에는 AXI를 선택하는 것도 타당합니다.

## Q4. (Analyze)

AXI에서 WSTRB이 모두 0인 W beat는 protocol 위반인가?

??? answer "정답 / 해설"
    **위반 아님**. 유효한 전송이지만 실질적 쓰기는 발생하지 않음 (모든 byte mask 0). Burst 중 특정 beat skip용으로 활용 가능.

    WSTRB는 Write beat 내에서 어느 byte를 실제로 메모리에 기록할지를 나타내는 마스크입니다. WSTRB가 모두 0이면 beat 자체는 전송되지만 슬레이브에게 "이 beat는 아무 byte도 쓰지 말라"고 지시하는 것이므로, 프로토콜 관점에서는 완전히 유효한 전송입니다. 이는 예를 들어 INCR burst 중 특정 주소를 건너뛰어야 할 때, 전체 burst를 중단하지 않고 해당 beat만 WSTRB=0으로 마킹하여 실질적인 쓰기를 억제하는 용도로 활용됩니다. AXI 사양에는 이 동작을 금지하는 규정이 없습니다.

## Q5. (Evaluate)

AHB가 AXI에 대부분 대체된 현대에도 여전히 사용되는 이유 두 가지를 들어보세요.

??? answer "정답 / 해설"
    1. **레거시 IP 호환** — 수십 년간 누적된 AHB IP 그대로 통합 가능
    2. **AXI 대비 작은 게이트 + 충분한 중간 성능** — 단순한 인터커넥트에서는 AXI의 5채널 분리가 과잉

    AHB가 현역을 유지하는 첫 번째 이유는 경제성입니다. ARM Cortex-M 계열 MCU, USB 컨트롤러, legacy DMA 등 수십 년에 걸쳐 축적된 검증된 AHB IP를 새로운 SoC에 그대로 통합하면 재검증 비용과 위험이 줄어듭니다. 두 번째 이유는 적정 성능입니다. AXI는 5개 독립 채널, outstanding ID 관리, OoO 응답 처리 등으로 구현 복잡도와 면적이 크게 늘어나는데, 저전력 MCU나 단순 peripheral 서브시스템처럼 고성능이 불필요한 곳에서는 AHB의 파이프라인 burst만으로도 성능 요구사항을 충족하면서 면적을 크게 절약할 수 있습니다.
