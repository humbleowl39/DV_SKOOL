---
title: "Quiz — 02: SQ/CQ 큐 메커니즘 & Doorbell"
---

[← 02 본문으로 돌아가기](../../02_sq_cq_doorbell/)

---

## Q1. (Remember)

NVMe의 host↔controller 통신 단위인 큐 쌍(queue pair)을 구성하는 두 큐는?

- [ ] A. Read Queue + Write Queue
- [ ] B. Submission Queue + Completion Queue
- [ ] C. Admin Queue + IO Queue
- [ ] D. Inbound Queue + Outbound Queue

<details>
<summary>정답 / 해설</summary>

**B**. NVMe의 기본 통신 단위는 Submission Queue(host→controller 명령)와 Completion Queue(controller→host 완료)의 쌍입니다. 둘 다 host 메모리의 circular ring buffer입니다. C(Admin/IO)는 큐의 *용도* 구분이지 큐 쌍을 이루는 두 큐가 아니고, A·D는 NVMe 용어가 아닙니다.

</details>

## Q2. (Understand)

ring buffer에서 Empty와 Full을 어떻게 판정하며, 실효 용량이 `size − 1`인 이유는?

<details>
<summary>정답 / 해설</summary>

Empty는 `Head == Tail`, Full은 `Head == Tail + 1`로 판정합니다. 만약 size개를 모두 채울 수 있게 하면, 가득 찬 상태와 완전히 빈 상태가 모두 `Head == Tail`이 되어 둘을 구분할 수 없습니다. 이를 피하려고 항상 한 슬롯을 비워두고 그 상태를 Full로 정의하므로, 실제로 채울 수 있는 항목은 `size − 1`개가 됩니다.

</details>

## Q3. (Apply)

host가 SQE 3개를 SQ에 채운 뒤 controller가 명령을 처리하게 하려면 마지막으로 무엇을 해야 하며, 그 동작은 어느 방향인가?

- [ ] A. controller가 host에게 인터럽트를 보낸다
- [ ] B. host가 SQ tail doorbell에 새 tail 값을 write한다
- [ ] C. host가 CQ head doorbell을 갱신한다
- [ ] D. controller가 SQ를 polling하므로 아무 것도 안 해도 된다

<details>
<summary>정답 / 해설</summary>

**B**. host는 SQE를 메모리에 쓰는 것만으로는 controller에 알릴 수 없고, SQ tail doorbell 레지스터(BAR MMIO)에 새 tail 값을 write해야 controller가 명령 도착을 인지합니다. 이 doorbell write는 host→controller 방향입니다. A는 통지 방향이 반대이고, C는 completion 소비용 doorbell이며, D처럼 doorbell 없이는 controller가 명령을 보지 못해 hang이 발생합니다.

</details>

## Q4. (Apply)

polling 기반 host가 CQ에서 새 completion을 정확히 인지하려면 무엇을 확인해야 하는가?

- [ ] A. CQ head 포인터가 증가했는지
- [ ] B. SQ tail doorbell 값
- [ ] C. head 위치 CQE의 phase bit이 기대 phase와 같은지
- [ ] D. MSI-X 인터럽트 수신 여부

<details>
<summary>정답 / 해설</summary>

**C**. polling 환경에서는 인터럽트가 없으므로, host는 head 위치 CQE의 **phase bit**을 자신이 기대하는 phase와 비교해 유효성을 판정합니다. controller는 CQ를 한 바퀴 돌 때마다 새로 쓰는 CQE의 phase bit을 토글하므로, stale 슬롯에는 이전 phase가 남아 구분됩니다. A(head 포인터)만으로는 stale 슬롯을 유효한 것으로 오인할 수 있고, D는 polling이 아닌 interrupt 방식입니다.

</details>

## Q5. (Analyze)

NVMe 검증 환경에서 명령 발행 후 시뮬레이션이 hang하고 completion이 전혀 오지 않는다. 가장 가능성 높은 원인과 확인 위치는?

<details>
<summary>정답 / 해설</summary>

가장 흔한 원인은 **SQ tail doorbell write 누락**입니다. host가 SQE를 ring buffer에 정확히 써도 doorbell을 안 울리면 controller는 큐가 비어 있다고 믿고 영원히 기다립니다. 확인 위치는 host의 명령 발행(submit) 경로에 SQ tail doorbell MMIO write가 실제로 존재하는지, 그리고 그 doorbell 주소(큐별 doorbell stride 포함)가 올바른지입니다. 에러 로그 없이 조용히 멈추는 것이 이 버그의 특징입니다.

</details>

## Q6. (Analyze)

CQ head doorbell을 host가 갱신하지 않으면 시간이 지나며 어떤 연쇄 문제가 발생하는가?

<details>
<summary>정답 / 해설</summary>

CQ head doorbell은 host가 CQE를 소비했음을 controller에 알려 슬롯을 반환하는 역할입니다. host가 이를 갱신하지 않으면 controller 관점에서 CQ가 점점 차다가 Full(`Head == Tail+1`)에 도달하고, 더 이상 새 CQE를 쓸 공간이 없어집니다. 그러면 controller는 완료된 명령의 결과를 통지하지 못해 새 명령 처리도 막히고, 결국 전체 큐 처리가 정지합니다. 즉 head doorbell 누락은 즉각적 hang은 아니어도 CQ full로 이어지는 지연된 정지를 만듭니다.

</details>
