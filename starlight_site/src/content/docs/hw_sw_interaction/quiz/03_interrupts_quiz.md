---
title: "Quiz — 03: 인터럽트 (level/edge/MSI/doorbell/IPI)"
---

[← 03 본문으로 돌아가기](../../03_interrupts/)

---

## Q1. (Remember)

PCI Express가 인터럽트를 위해 전적으로 사용하는 방식은?

- [ ] A. INTx 물리 IRQ 선
- [ ] B. MSI (Message-Signaled Interrupt)
- [ ] C. 폴링
- [ ] D. NMI

<details>
<summary>정답 / 해설</summary>

**B**. 순수 PCIe 링크에는 INTx 물리 선이 없어 MSI를 전적으로 사용합니다. 인터럽트의 정체는 메시지 payload에 실립니다. 레거시 호환이 필요한 엔드포인트는 in-band 메시지로 emulated INTx를 만들 뿐, 실제 물리 INTx 선(A)을 쓰지 않습니다. C·D는 PCIe의 기본 인터럽트 전달 방식이 아닙니다.

</details>

## Q2. (Understand)

도어벨이 "인터럽트의 역방향"이라고 불리는 이유를 설명하라.

<details>
<summary>정답 / 해설</summary>

인터럽트는 **디바이스 → CPU** 방향으로 디바이스가 CPU의 주의를 요청하는 신호입니다. 도어벨은 그 반대로 **소프트웨어 → 하드웨어** 방향으로, SW가 데이터를 메모리에 둔 뒤 다른 위치에 write하여 디바이스에게 "처리할 일이 있다"고 알립니다. 즉 알림의 방향이 정반대이므로 "역방향"이라 부릅니다.

</details>

## Q3. (Apply)

level-triggered 인터럽트를 처리하는 ISR을 작성할 때, 인터럽트가 멈추게 하려면 반드시 해야 하는 동작은?

<details>
<summary>정답 / 해설</summary>

ISR이 인터럽트 **원인을 처리하고 acknowledge(예: `INT_CLEAR` write 또는 원인 해소)** 하여 디바이스가 IRQ 선을 deassert하게 해야 합니다. level은 처리 전까지 선을 active로 유지하므로, acknowledge로 선을 내리지 않으면 ISR이 반환되자마자 다시 인터럽트가 걸려 **무한 재진입(stuck)** 합니다. (edge였다면 펄스가 자동 해제되지만, 그 경우엔 INT_STATUS 래치 보존이 관건입니다.)

</details>

## Q4. (Analyze)

완료 인터럽트가 *간헐적으로* 사라져 드라이버가 가끔 영영 깨어나지 못한다. 트리거가 level일 가능성이 높은가 edge일 가능성이 높은가? 근거는?

<details>
<summary>정답 / 해설</summary>

**edge** 가능성이 높습니다. edge는 순간 펄스라, 마침 그 시점에 인터럽트가 마스킹되어 있고 status 래치가 없으면 신호가 영영 분실됩니다(missed edge) — "간헐적 소실"의 전형적 증상입니다. level은 처리 전까지 선을 유지하므로 사라지기보다는 stuck(무한 재진입)이 문제 양상입니다. 따라서 INT_STATUS가 마스킹 구간에서도 펜딩을 래치·보존하는지 검증해야 합니다.

</details>

## Q5. (Evaluate)

설계 리뷰에서 누군가 "인터럽트는 항상 폴링보다 효율적이니 모든 경로를 인터럽트로 하자"고 제안한다. 이 제안을 평가하라.

<details>
<summary>정답 / 해설</summary>

**부분적으로만 맞습니다.** 저부하·산발 이벤트에서는 인터럽트가 idle CPU 비용이 ~0이라 유리합니다. 그러나 *초고율* 이벤트에서는 이벤트마다 ISR 진입/복귀 오버헤드가 누적되어 **인터럽트 스톰**으로 시스템 throughput이 붕괴할 수 있습니다. 따라서 고율 경로에는 interrupt coalescing(N 이벤트/T μs 지연), RSS(코어 분산), 또는 인터럽트 후 임계 폴링 하이브리드(NAPI/NVMe)가 더 효율적입니다. "항상 인터럽트"는 워크로드를 무시한 과일반화입니다.

</details>
