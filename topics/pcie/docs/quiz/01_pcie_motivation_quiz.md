# Quiz — Module 01: PCIe 동기와 진화

[← Module 01 본문으로 돌아가기](../01_pcie_motivation.md)

---

## Q1. (Remember)

PCIe 가 PCI parallel 의 어떤 한계를 해결했는지 3가지 들어라.

??? answer "정답 / 해설"
    1. **Skew** — 32-bit 병렬 라인의 도착 시간 편차 → serial + embedded clock 으로 해결
    2. **Multi-drop 부하** → point-to-point 로 해결
    3. **Half-duplex** → full-duplex per lane 으로 해결

    추가: signal integrity, pin count, arbitration overhead.

## Q2. (Understand)

Switch 와 Bridge 의 역할 차이는?

??? answer "정답 / 해설"
    - **Switch**: PCIe 의 fan-out (1 upstream + N downstream port). 모든 port 가 PCIe.
    - **Bridge**: PCIe ↔ legacy PCI 변환 (또는 PCI-PCI). 한쪽이 PCI.

    Configuration 관점에서는 둘 다 Type 1 Header. 동작 모델은 다름.

## Q3. (Apply)

PCIe Gen4 x8 link 의 한 방향 raw bandwidth 는?

??? answer "정답 / 해설"
    Gen4 = 16 GT/s per lane.
    16 × 8 = 128 GT/s.
    Encoding 128b/130b → 128 × 128/130 ≈ 126 Gbps ≈ 15.75 GB/s ≈ 16 GB/s.

    빠른 추산: 16 × 8 / 8 = 16 GB/s.

## Q4. (Analyze)

Gen5 (32 GT/s NRZ) 에서 Gen6 (64 GT/s) 로 갈 때 단순 2× clock 으로 가지 못한 이유는?

??? answer "정답 / 해설"
    NRZ 의 channel loss 가 32 GT/s 에서 한계 — connector + 일정 길이의 PCB 위로 64 GT/s NRZ 신호는 receiver 의 EQ 마진 부족.

    해결: **PAM4** 도입 — 1 symbol 에 2 bit (4-level), symbol rate 는 32 G symbols/s 유지하면서 64 Gbps 달성. 단 PAM4 의 BER 이 NRZ 대비 훨씬 높아 (1e-6) FEC + FLIT mode 가 필요.

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
