# Quiz — Module 01: CAN Bus Fundamentals

[← Module 01 본문으로 돌아가기](../01_can_bus_fundamentals.md)

---

## Q1. (Remember)

CAN Bus 는 어느 레이어 모델에서 어떤 두 계층을 정의하는가?

??? answer "정답 / 해설"
    OSI 모델의 **데이터 링크 계층(L2)** 과 **물리 계층(L1)** 을 정의한다. 상위 계층(전송, 응용) 은 별도 프로토콜(UDS, OBD-II 등) 이 담당.

## Q2. (Understand)

CAN 의 비파괴적 비트별 중재(non-destructive bitwise arbitration) 방식이 어떻게 동작하며, 왜 "낮은 ID 가 우선"이 되는가?

??? answer "정답 / 해설"
    각 노드는 ID 를 비트 단위로 송출하며, **dominant(0)** 이 **recessive(1)** 을 덮어쓴다. 0이 더 우세하므로 ID 의 상위 비트에 0이 더 많은(즉 수치가 작은) 메시지가 충돌 시 살아남고, 진 쪽은 자동으로 전송을 멈춘다. 충돌해도 데이터가 깨지지 않는다는 점에서 "비파괴적" 이라 불린다.

## Q3. (Apply)

회사가 OBD-II 포트를 항상 살아 있도록 두는 양산 차량에 대한 보안 검토를 의뢰받았다. 가장 먼저 확인해야 할 두 가지 위협 시나리오는?

??? answer "정답 / 해설"
    1. **Diag 인증 누락** — UDS Security Access(0x27) 가 없거나 약한 키로 보호되어 외부에서 진단 모드 진입이 가능한가?
    2. **버스 격리 부재** — OBD-II 가 Powertrain CAN 까지 직접 연결되어 있어, 외부에서 ABS/Engine 메시지를 그대로 주입할 수 있는가? Secure Gateway 를 사이에 두는지 확인.

## Q4. (Analyze)

CAN 의 "broadcast + 무인증" 특성이 만들어내는 4가지 구조적 약점을 분류해 설명하라.

??? answer "정답 / 해설"
    1. **Spoofing** — 누가 보낸 메시지인지 검증할 방법이 없다 → 임의 노드가 Engine ECU 를 가장 가능.
    2. **Replay** — 카운터/타임스탬프가 없으므로 정상 메시지를 녹음 후 재전송 가능.
    3. **DoS by Flooding** — 낮은 ID 메시지를 1ms 주기로 보내면 정상 메시지가 영원히 중재에서 진다.
    4. **Eavesdropping** — 모든 메시지가 broadcast 되어 같은 버스 위 모든 노드에서 청취 가능.

    이 네 가지 모두 **프로토콜 자체로는 해결 불가** — SecOC + Gateway + IDS 같은 상위 계층 통제가 필요하다.

## Q5. (Evaluate)

CAN-FD 가 SecOC 를 더 실용적으로 만드는 결정적 변화 두 가지는?

??? answer "정답 / 해설"
    1. **Payload 64B 까지 확장** — 8B payload 시 MAC 16B 를 동봉하면 데이터가 거의 남지 않는다. 64B 가 되면 freshness + truncated MAC 을 충분히 실을 수 있다.
    2. **Data-phase 비트레이트 분리(최대 5~8 Mbps)** — MAC 부착으로 인해 늘어난 메시지 길이의 전송 시간을 만회. 결국 SecOC overhead 를 감춘다.

    둘이 합쳐져야 SecOC 가 "버스 대역 다 잡아먹는 부담" 이 아니라 일상적으로 켤 수 있는 기능이 된다.
