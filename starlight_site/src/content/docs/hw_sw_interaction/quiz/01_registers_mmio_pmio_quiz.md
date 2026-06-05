---
title: "Quiz — 01: 디바이스 레지스터 & MMIO/PMIO"
---

[← 01 본문으로 돌아가기](../../01_registers_mmio_pmio/)

---

## Q1. (Remember)

다음 중 디바이스 레지스터의 다섯 기능 분류에 **해당하지 않는** 것은?

- [ ] A. Control
- [ ] B. Status
- [ ] C. Cache
- [ ] D. Data

<details>
<summary>정답 / 해설</summary>

**C**. HDG 스펙이 드는 다섯 분류는 Control / Status / Interrupt / Data / Address(pointer)입니다. Cache는 레지스터 분류가 아니라 CPU의 메모리 계층 요소이며, 오히려 MMIO 영역에서는 *비활성화(uncached)* 해야 하는 대상입니다(2장). A·B·D는 모두 정식 분류에 속합니다.

</details>

## Q2. (Understand)

MMIO와 PMIO의 가장 근본적인 차이를 한 문장으로 설명하면?

<details>
<summary>정답 / 해설</summary>

MMIO는 디바이스 레지스터를 RAM과 **동일한 통합 주소 공간**에 매핑해 평범한 load/store 명령으로 접근하는 반면, PMIO는 디바이스를 **별도의 격리된 I/O 주소 공간**에 두고 `in`/`out` 같은 전용 명령으로 접근합니다. 동작(레지스터 read/write)은 같지만 주소 공간과 접근 명령이 다릅니다.

</details>

## Q3. (Apply)

x86에서 STATUS 레지스터(I/O 포트 0x04)를 PMIO로 읽으려 한다. 올바른 코드 형태는?

- [ ] A. `readl(0x04)`
- [ ] B. `inl(0x04)`
- [ ] C. `ioremap(0x04)` 후 역참조
- [ ] D. `*(volatile u32*)0x04`

<details>
<summary>정답 / 해설</summary>

**B**. PMIO는 전용 명령 `in`/`out` 계열로 접근하며, 32비트는 `inl(port)`입니다. A의 `readl`과 C의 `ioremap`, D의 포인터 역참조는 모두 *MMIO*(메모리 주소 공간) 접근 관용구입니다. PMIO에서 데이터는 `EAX`로, 포트 번호는 immediate 또는 `DX`로 제한된다는 점도 함께 기억하세요.

</details>

## Q4. (Analyze)

새 PCIe 디바이스의 MMIO 영역을 메모리 맵에 배치했는데, 같은 주소 범위에 DRAM도 백킹되도록 설정되어 있었다. 어떤 문제가 생기며 근본 원인은?

<details>
<summary>정답 / 해설</summary>

MMIO 영역은 물리 메모리 맵에 **구멍(hole)** 으로 남아야 하며 그 범위는 DRAM이 차지할 수 없습니다. 같은 주소에 DRAM과 디바이스가 동시에 매핑되면 주소 디코더가 어디로 라우팅할지 충돌이 생겨, 해당 주소 접근이 DRAM으로 가거나(디바이스 미도달) 정의되지 않은 동작을 합니다. 근본 원인은 통합 주소 공간에서 I/O hole이 DRAM과 겹치지 않게 예약되어야 한다는 MMIO의 전제를 위반한 것입니다. 해법은 BAR가 광고한 크기만큼 충돌 없는 물리 주소를 할당하는 것입니다.

</details>

## Q5. (Evaluate)

"현대 시스템에서는 MMIO가 PMIO보다 거의 항상 선호된다"는 주장을 평가하고 근거를 제시하라.

<details>
<summary>정답 / 해설</summary>

**대체로 타당합니다.** 근거: (1) MMIO는 전용 I/O 명령셋이 불필요해 CPU 복잡도가 낮고 RISC 친화적, (2) *모든* 범용 레지스터와 addressing mode로 접근 가능해 명령 수가 줄고 컴파일러 최적화 자유도가 큼, (3) PMIO는 `EAX`/`DX` 제약과 x86-64에서도 32비트 cap. 대부분의 PCI/PCIe 디바이스가 레지스터를 MMIO로 매핑합니다. 다만 PMIO의 격리 버스가 메모리 경합을 피하는 장점은 존재하므로 "거의 항상"은 맞되 "절대적"은 아닙니다 — 레거시 호환 목적의 I/O 포트는 여전히 쓰입니다.

</details>
