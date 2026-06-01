# Quiz — Module 01: PCIe 동기와 진화

[← Module 01 본문으로 돌아가기](../01_pcie_motivation.md)

---

## Q1. (Remember)

PCIe 가 PCI parallel 의 어떤 한계를 해결했는지 3가지 들어라.

??? answer "정답 / 해설"
    1. **Skew** — 32-bit 병렬 라인의 도착 시간 편차 → serial + embedded clock 으로 해결
    2. **Multi-drop 부하** → point-to-point 로 해결
    3. **Half-duplex** → full-duplex per lane 으로 해결

    PCI 병렬 버스는 배선이 길어질수록 각 라인의 전기적 지연 차이(skew)가 커져 수십 MHz 이상으로 클럭을 높이기가 불가능해졌다. 또한 여러 슬롯이 같은 버스를 공유하는 multi-drop 구조는 전기적 부하가 누적되고 arbitration 지연도 증가했다. PCIe 는 레인 당 단방향 차동 시리얼 쌍으로 분리해 이 세 가지를 동시에 해결한 것이다.

## Q2. (Understand)

Switch 와 Bridge 의 역할 차이는?

??? answer "정답 / 해설"
    - **Switch**: PCIe 의 fan-out (1 upstream + N downstream port). 모든 port 가 PCIe.
    - **Bridge**: PCIe ↔ legacy PCI 변환 (또는 PCI-PCI). 한쪽이 PCI.

    Configuration 관점에서는 둘 다 Type 1 Header. 동작 모델은 다름.

    Switch 는 PCIe 도메인 안에서 TLP 를 라우팅하는 팬아웃 장치이며 모든 포트가 PCIe 로 동일한 규칙을 따른다. 반면 Bridge 는 한쪽이 레거시 PCI 나 PCI-X 이기 때문에 프로토콜 변환 역할을 한다는 점이 핵심 차이다. 헤더 타입이 같다고 동작 모델까지 같다고 혼동하지 말아야 한다.

## Q3. (Apply)

PCIe Gen4 x8 link 의 한 방향 raw bandwidth 는?

??? answer "정답 / 해설"
    Gen4 = 16 GT/s per lane.
    16 × 8 = 128 GT/s.
    Encoding 128b/130b → 128 × 128/130 ≈ 126 Gbps ≈ 15.75 GB/s ≈ 16 GB/s.

    빠른 추산: 16 × 8 / 8 = 16 GB/s.

    Gen4 는 레인 당 16 GT/s 를 전송하므로 x8 링크는 단순히 16 × 8 = 128 GT/s 가 된다. 여기에 128b/130b 인코딩 오버헤드(128/130)를 적용하면 실질적인 데이터 대역폭은 약 15.75 GB/s 가 되고 실무에서는 이를 16 GB/s 로 근사하여 기억한다. 오답이 되기 쉬운 함정은 8b/10b 처럼 오버헤드가 20%라고 착각하는 것인데, Gen3 부터는 128b/130b 로 바뀌어 오버헤드가 약 1.5% 에 불과하다.

## Q4. (Analyze)

Gen5 (32 GT/s NRZ) 에서 Gen6 (64 GT/s) 로 갈 때 단순 2× clock 으로 가지 못한 이유는?

??? answer "정답 / 해설"
    NRZ 의 channel loss 가 32 GT/s 에서 한계 — connector + 일정 길이의 PCB 위로 64 GT/s NRZ 신호는 receiver 의 EQ 마진 부족.

    해결: **PAM4** 도입 — 1 symbol 에 2 bit (4-level), symbol rate 는 32 G symbols/s 유지하면서 64 Gbps 달성. 단 PAM4 의 BER 이 NRZ 대비 훨씬 높아 (1e-6) FEC + FLIT mode 가 필요.

    단순히 클럭을 2배로 올리면 신호가 채널을 통과하는 동안 더 많은 감쇠와 반사를 겪어 수신 측 eye 가 닫혀버린다. 이것이 채널 손실(channel loss)의 물리적 한계이다. Gen6 는 심볼 속도를 늘리는 대신 PAM4 로 심볼당 비트 수를 2배로 올려 동일한 채널에서 2배 처리량을 확보했다. 다만 4-레벨 신호는 eye 간격이 NRZ 의 1/3 수준으로 좁아지므로 BER 이 크게 높아지고, 이를 보완하기 위해 FEC 와 FLIT 모드가 함께 도입된 것이다.

## Q5. (Evaluate)

"PCIe x16 connector 가 있으니 이 device 는 무조건 x16 으로 동작한다" 는 주장을 평가하라.

??? answer "정답 / 해설"
    **틀림**. Connector 는 물리적 lane 갯수 capacity 일 뿐.

    실제 link width 결정 요소:

    1. **양 끝의 capability** — RC 또는 EP 가 x8 만 지원하면 x8 collapse.
    2. **Board routing** — x16 traces 가 모두 라우팅된 보드인가.
    3. **LTSSM Polling/Configuration** — 일부 lane 의 EQ/electrical idle 실패 시 down-train.
    4. **BIOS / firmware 설정** — Bifurcation (x16 → x8+x8) 가능.

    실제 동작 width 는 PCIe Capability 의 Link Status register 에서 확인.

    커넥터가 x16 이라는 사실은 "최대 x16 까지 꽂을 수 있는 슬롯"을 의미할 뿐이다. 실제 링크 폭은 LTSSM 의 Configuration 단계에서 양측이 지원하는 레인 수의 최솟값으로 결정되며, 일부 레인이 전기적 훈련에 실패하면 그보다 더 낮은 폭으로 down-train 된다. BIOS 의 bifurcation 설정까지 개입할 수 있으므로, 실제 동작 폭은 반드시 Link Status 레지스터로 확인해야 한다는 점이 이 문제의 핵심이다.
