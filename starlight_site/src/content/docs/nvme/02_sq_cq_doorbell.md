---
title: "02 — SQ/CQ 큐 메커니즘 & Doorbell"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** Submission Queue(SQ)와 Completion Queue(CQ)가 host 메모리의 circular ring buffer로 구성되는 큐 쌍(queue pair) 모델을 설명할 수 있다.
- **Trace** 명령 하나가 host의 SQE 작성 → SQ tail doorbell → controller 처리 → CQE 작성 → CQ head doorbell까지 흐르는 전 과정을 단계별로 추적할 수 있다.
- **Differentiate** SQ tail doorbell과 CQ head doorbell이 각각 누가·언제·왜 갱신하는지 구분할 수 있다.
- **Explain** ring buffer의 empty(`H==T`)·full(`H==T+1`) 판정과 wrap-around를 설명할 수 있다.
- **Evaluate** polling 환경과 interrupt(MSI-X) 환경 중 어느 completion 통지 방식을 쓸지 검증 맥락에서 판단할 수 있다.
:::
:::note[사전 지식]
- [01 — 왜 NVMe인가](../01_motivation_vs_sata_sas/)
- Ring buffer (circular queue) — head/tail 포인터, wrap-around
- PCIe memory-mapped register, BAR ([PCIe 코스](../../pcie/)), MSI/MSI-X 개념
:::
---

## 1. Why care? — 명령은 메모리에 있는데 controller가 모른다

### 1.1 시나리오 — SQE는 썼는데 시뮬이 멈췄다

NVMe 검증 환경에서 host 모델이 명령(SQE, Submission Queue Entry)을 host 메모리의 SQ ring buffer에 정확히 써 넣었습니다. 그런데 시뮬레이션이 영원히 멈춥니다. controller는 아무 일도 안 하고, completion도 오지 않습니다. 로그를 봐도 에러는 없습니다.

원인은 거의 항상 하나입니다. **SQ tail doorbell을 안 울린 것.** NVMe에서 **host**(명령을 보내는 쪽, 즉 CPU/소프트웨어) 가 명령을 메모리에 써 넣는 것만으로는 **controller**(SSD 안에서 명령을 받아 처리하는 제어 칩) 가 알 방법이 없습니다. host는 명령을 큐에 넣은 뒤 *반드시* SQ tail **doorbell**(큐에 새 항목이 생겼음을 상대에게 통지하는 레지스터) 레지스터(**BAR**(Base Address Register, 장치 레지스터가 매핑되는 메모리 주소 영역) 공간의 **MMIO**(Memory-Mapped I/O, 장치 레지스터를 메모리 주소처럼 읽고 써서 제어하는 방식)) 에 새 tail 값을 써서 "여기까지 명령이 도착했다"고 controller에 신호해야 합니다. 이 doorbell write가 빠지면 controller는 큐가 비어 있다고 믿고 영원히 기다립니다.

이 장은 그 메커니즘 — host와 controller가 ring buffer 한 쌍과 doorbell로 어떻게 손발을 맞추는지 — 를 다룹니다. 이걸 모르면 NVMe 검증의 가장 흔한 hang을 진단할 수 없습니다.

---

## 2. Intuition — 한 줄 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**SQ/CQ + doorbell** ≈ **주방의 주문판과 종(bell)**.<br>
손님(host)이 주문서(SQE)를 주문판(SQ ring buffer)에 꽂고 **종을 친다**(SQ tail doorbell). 종소리를 들은 셰프(controller)가 주문을 가져가 요리하고, 완성되면 픽업대(CQ)에 영수증(CQE)을 올립니다. 손님이 영수증을 가져가면 픽업대를 **다시 비웠다고 알린다**(CQ head doorbell). 종을 안 치면 셰프는 주문이 들어온 줄 모릅니다.
:::

### 한 장 그림 — 큐 쌍과 두 개의 doorbell

```d2
direction: right

HOST: "**Host** (소프트웨어)" {
  SQ: "**SQ** (ring buffer)\nhost memory\n← host가 tail 갱신\nSQE 작성"
  CQ: "**CQ** (ring buffer)\nhost memory\n→ host가 head 갱신\nCQE 소비"
}

CTRL: "**Controller** (NVMe device)" {
  DB: "**Doorbell registers**\n(BAR MMIO)\nSQ tail / CQ head"
  ENG: "command\nengine"
  DB -> ENG
}

HOST.SQ -> CTRL.DB: "① SQ tail doorbell write\n(명령 도착 신호)"
CTRL.ENG -> HOST.SQ: "② SQE fetch (controller reads)"
CTRL.ENG -> HOST.CQ: "③ CQE write (completion)\n+ phase bit"
HOST.CQ -> CTRL.DB: "④ CQ head doorbell write\n(CQE 소비 완료 신호)"
```

핵심 비대칭: **SQ tail은 host가**(명령을 넣었으니), **CQ head도 host가**(완성된 것을 가져갔으니) 갱신합니다. doorbell은 모두 host → controller 방향의 MMIO write입니다. controller가 host에게 알리는 방향은 doorbell이 아니라 CQE 작성(+ 선택적 인터럽트)입니다.

---

## 3. 작은 예 — 명령 하나가 도는 한 바퀴

가장 단순한 시나리오: host가 명령 1개를 발행하고 completion을 받습니다.

### 단계별 다이어그램

```d2
direction: down

S1: "**① host**: SQE를 SQ[tail]에 작성\n(host memory 쓰기)"
S2: "**② host**: SQ tail doorbell write\ntail = tail+1 → controller에 신호"
S3: "**③ controller**: SQE fetch\n(host memory read)\n명령 실행"
S4: "**④ controller**: CQE를 CQ[ ]에 작성\nphase bit 토글 + status"
S5: "**⑤ host**: CQE 인지\n(polling: phase bit 확인 /\ninterrupt: MSI-X)"
S6: "**⑥ host**: CQ head doorbell write\nhead = head+1 → 슬롯 반환"
S1 -> S2 -> S3 -> S4 -> S5 -> S6
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | host | SQE를 SQ ring buffer의 tail 위치에 작성 | 명령을 큐에 적재 |
| ② | host | SQ tail doorbell 레지스터에 새 tail write | controller에 "명령 도착" 신호 — **빠지면 hang** |
| ③ | controller | host memory에서 SQE를 fetch해 실행 | doorbell로 깨어남 |
| ④ | controller | CQ에 CQE 작성, **phase bit** 토글 + 상태 코드 | 완료 통지 |
| ⑤ | host | polling이면 phase bit 확인, interrupt면 MSI-X 수신 | CQE 유효성 판정 |
| ⑥ | host | CQ head doorbell에 새 head write | CQ 슬롯 반환 — controller가 재사용 가능 |

:::caution[doorbell의 두 방향 — 헷갈리지 말 것]
**SQ tail doorbell**은 "명령을 *넣었다*"(host → controller에게 일 시킴), **CQ head doorbell**은 "completion을 *가져갔다*"(host → controller에게 슬롯 반환). 둘 다 host가 쓰지만 의미가 반대입니다. SQ tail을 안 울리면 controller가 일을 시작 못 하고(hang), CQ head를 안 갱신하면 CQ가 가득 차 controller가 더 이상 CQE를 못 씁니다.
:::

### CQE 유효성 — phase bit

NRT DV 환경은 **polling 위주**(**polling**은 host가 새 결과가 왔는지 직접 반복해서 확인하는 방식, MSI 비활성)입니다. polling에서는 host가 인터럽트를 못 받으므로, CQ의 어느 슬롯이 *새로 쓰인 유효한 **CQE**(Completion Queue Entry, controller가 한 명령의 처리 결과를 담아 CQ에 기록하는 항목)*인지 따로 판정해야 합니다. 이를 위해 각 CQE에는 **phase tag(P) bit**(controller가 CQ를 한 바퀴 돌 때마다 뒤집는 1비트 표식 — 그 슬롯의 CQE가 새것인지 옛것인지 구별)이 있고, controller가 CQ를 한 바퀴 돌 때마다 이 bit의 기대값을 토글합니다. host는 현재 head 위치 CQE의 phase bit이 기대 phase와 같으면 "새 CQE"로 인지합니다. 즉, head 포인터만으로 유효성을 판단하면 안 되고 phase bit을 확인해야 합니다.

왜 별도의 "valid" 비트를 따로 두고 매번 켜고 끄는 대신 phase 반전을 쓸까요? valid 비트 방식이라면 host가 CQE를 소비할 때마다 그 슬롯을 명시적으로 "무효(0)"로 *되돌려 써야* 합니다 — 즉 매 completion마다 host의 추가 write가 생깁니다. phase bit은 *controller가 한 바퀴 돌 때마다 기대값을 토글*하는 규약이라, host가 슬롯을 지울 필요가 없습니다. 이전 바퀴에 쓰인 CQE는 자연히 *옛 phase*를 들고 있어 새 CQE와 구별되기 때문입니다. 결과적으로 wrap마다 슬롯을 clear하는 비용이 사라지는 것이 phase 반전 설계의 동기입니다.

---

## 4. 일반화 — Ring buffer 동작 규칙

SQ와 CQ는 모두 **circular ring buffer**입니다. 동작 규칙은 다음과 같습니다.

| 개념 | 규칙 |
|---|---|
| Submitter / Consumer | Submitter가 **Tail**을 갱신, Consumer가 **Head**를 갱신 |
| Empty 판정 | `Head == Tail` |
| Full 판정 | `Head == Tail + 1` (한 슬롯을 비워둠) |
| 실효 용량 | `size − 1` (full 판정을 위해 1슬롯 희생) |
| Wrap-around | 포인터가 `size − 1`에 도달하면 0으로 되돌아감 |

SQ에서는 host가 Submitter(tail 갱신), controller가 Consumer(SQE를 fetch). CQ에서는 controller가 Submitter(CQE를 쓰며 tail 진행), host가 Consumer(head 갱신). full을 위해 한 슬롯을 항상 비워두므로, 큐 크기가 N이면 실제로 채울 수 있는 항목은 N−1개입니다.

```d2
direction: right
EMPTY: "**Empty**\nHead == Tail\n(채워진 항목 0)"
SOME: "**일부 채움**\nHead < Tail\n(또는 wrap 상태)"
FULL: "**Full**\nHead == Tail + 1\n(1 슬롯 비워둠)"
EMPTY -> SOME: "submitter가 tail++"
SOME -> FULL: "계속 적재"
FULL -> SOME: "consumer가 head++"
SOME -> EMPTY: "모두 소비"
```

### Capability / Config / Status 레지스터

NVMe controller는 BAR0에 매핑된 레지스터로 설정·상태를 노출합니다.

| 레지스터 | 역할 |
|---|---|
| `CAP` | Capability — controller가 지원하는 큐 깊이·doorbell stride 등 |
| `CC` | Controller Configuration — enable, 큐 entry 크기 설정 |
| `CSTS` | Controller Status — ready 비트 등 |

host는 reset 후 `CC.EN`을 세팅하고 `CSTS.RDY`가 올라오기를 기다린 뒤 큐를 만들고 명령을 보냅니다. 이 BAR0 layout과 doorbell 영역이 PCIe memory-mapped 공간 위에 있으므로, [PCIe 기반](../../pcie/)이 정상이어야 합니다.

---

## 5. 디테일 — polling vs interrupt, 큐 용량, doorbell 코드

### 5.1 Polling vs Interrupt

| 방식 | 동작 | 검증 맥락 |
|---|---|---|
| **Polling** | host가 CQ head 위치 CQE의 phase bit을 반복 확인 | **NRT DV 환경의 기본** (MSI 비활성) |
| **Interrupt (MSI-X)** | controller가 CQE 작성 후 MSI-X 인터럽트 발생 → host가 ISR에서 처리 | spec 지원, 하지만 NRT DV에선 비활성 |

여기서 **interrupt**(인터럽트, 사건이 생기면 하드웨어가 CPU를 강제로 깨워 처리 루틴으로 넘기는 통지 방식)와 **MSI-X**(Message Signaled Interrupt eXtended, 별도 신호선 대신 메모리 write로 인터럽트를 전달하는 PCIe 방식)가 대비됩니다. polling은 인터럽트 인프라 없이도 동작하고 시뮬레이션에서 결정적(**deterministic**, 같은 입력이면 매번 같은 순서·결과가 나오는 성질)이라 검증에 편합니다. 대신 host가 CPU를 써 가며 phase bit을 계속 확인해야 합니다. interrupt는 CPU 효율적이지만 **ISR**(Interrupt Service Routine, 인터럽트가 발생했을 때 실행되는 처리 함수)·MSI-X 벡터 라우팅이라는 추가 검증 면을 만듭니다.

MSI-X가 polling보다 CPU 효율적인 근본 이유는 *언제 CPU를 쓰느냐*의 차이입니다. polling은 completion이 아직 없어도 host가 빈 CQ 슬롯의 phase bit을 끊임없이 다시 읽으며 CPU 사이클을 태웁니다 — 일이 없을 때도 계속 도는 busy loop입니다. MSI-X는 controller가 CQE를 실제로 쓴 *그 순간에만* 인터럽트로 host를 깨우므로, 그 전까지 host CPU는 다른 일을 하거나 쉴 수 있습니다. 즉 polling은 "쉴 새 없이 확인", interrupt는 "사건이 생기면 알림"이라는 대비입니다. 그래서 실제 시스템은 부하가 낮을 때 특히 interrupt가 유리하고, 검증에서는 결정성을 위해 polling을 기본으로 두는 trade-off가 생깁니다.

### 5.2 큐 용량

NVMe는 최대 **64K 큐 × 64K 명령/큐**를 지원합니다. 실제 controller가 지원하는 큐 깊이는 `CAP` 레지스터로 노출됩니다. 검증에서는 단일 큐뿐 아니라 *여러 큐의 동시 트래픽*과 *큐가 full에 근접한 경계*를 자극해야 합니다.

:::note[doorbell stride — 큐별 doorbell 주소는 어떻게 정해지나]
큐가 수천 개라도 controller는 각 큐의 doorbell 레지스터를 따로따로 디코딩하지 않습니다. 대신 doorbell 레지스터들이 BAR 공간에 **일정한 간격(stride)으로 연속 배치**되어 있어, host가 `doorbell_base + (큐 index × stride)` 식으로 주소를 *계산*합니다. 그 간격이 바로 doorbell **stride**이고, `CAP` 레지스터가 노출합니다. 이렇게 규칙적으로 배치하기 때문에 controller는 들어온 write 주소만 보고 어느 큐의 doorbell인지 역산할 수 있습니다. 다중 큐인데 한 큐만 동작한다면 이 stride 계산이 어긋났을 가능성이 큽니다.
:::

### 5.3 doorbell write — pseudo code

doorbell은 BAR 공간의 MMIO 레지스터입니다. host가 ring buffer에 SQE를 채운 뒤 새 tail 값을 doorbell에 씁니다. 아래는 검증 환경(C/펌웨어 관점)에서의 전형적 흐름을 보여주는 예시입니다.

통지 수단으로 *read*가 아니라 *write*를 고른 데는 이유가 있습니다. PCIe에서 memory write는 **posted** 트랜잭션 — 즉 보낸 쪽이 완료 응답을 기다리지 않고 곧장 다음 일을 합니다. 반대로 read는 완료 데이터가 돌아올 때까지 round-trip을 기다려야 하므로 그 시간 동안 host가 묶입니다. host가 명령을 넣을 때마다 통지를 보내야 하는 hot path에서, 응답을 기다리지 않는 posted write는 read보다 훨씬 효율적입니다. 그래서 doorbell은 host가 "쏘고 잊는(fire-and-forget)" MMIO write로 설계되었습니다.

```c
/* host 측: 명령 발행 — 개념 흐름 (예시) */
void nvme_submit(nvme_sq_t *sq, nvme_cmd_t *cmd) {
    /* ① SQE를 ring buffer의 tail 위치에 작성 */
    sq->entries[sq->tail] = *cmd;

    /* tail 진행 + wrap-around */
    sq->tail = (sq->tail + 1) % sq->size;

    /* ② SQ tail doorbell write — controller에 명령 도착 신호.
       이 줄이 빠지면 controller는 명령을 영원히 못 봄 (hang). */
    mmio_write32(sq->tail_doorbell, sq->tail);
}

/* host 측: completion 수거 — polling */
int nvme_poll_cq(nvme_cq_t *cq) {
    nvme_cqe_t *cqe = &cq->entries[cq->head];

    /* ⑤ phase bit이 기대 phase와 같으면 새 CQE */
    if (cqe->phase != cq->expected_phase)
        return 0;  /* 아직 새 completion 없음 */

    process_completion(cqe);

    /* head 진행 + wrap 시 expected_phase 토글 */
    cq->head = (cq->head + 1) % cq->size;
    if (cq->head == 0)
        cq->expected_phase ^= 1;

    /* ⑥ CQ head doorbell write — 슬롯 반환 */
    mmio_write32(cq->head_doorbell, cq->head);
    return 1;
}
```

:::note[검증 환경에서의 위치]
NRT-TB의 host↔controller 9-step 흐름은 `NRT_TB/docs/img/nvme-sq-cq-flow.svg`에 시각화되어 있습니다. 위 pseudo code는 그 흐름의 ① SQE 작성 → ② doorbell → … → ⑥ head doorbell을 C 관점으로 압축한 것입니다.
:::

---

## 6. 흔한 오해와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'SQE를 메모리에 쓰면 controller가 알아서 가져간다']
**실제**: host가 SQE를 ring buffer에 써도 controller는 모릅니다. *반드시* SQ tail doorbell을 write해야 controller가 명령 도착을 인지합니다. doorbell 누락은 NVMe 검증에서 가장 흔한 hang의 원인입니다.<br>
**왜 헷갈리는가**: "메모리에 썼으니 보이겠지"라는 공유 메모리 직관 때문에 — doorbell이라는 명시적 통지가 필요한 모델임을 놓침.
:::
:::danger[❓ 오해 2 — 'CQ head 포인터가 진행했으면 CQE가 유효하다']
**실제**: polling 환경에서 CQE 유효성은 **phase bit**으로 판정합니다. head 위치 CQE의 phase가 기대 phase와 같아야 새 completion입니다. head만 보면 controller가 아직 안 쓴 stale 슬롯을 유효한 것으로 오인합니다.<br>
**왜 헷갈리는가**: 일반 FIFO의 head/tail 직관을 그대로 적용해서 — NVMe CQ는 phase bit이라는 별도 유효성 표식을 가짐.
:::
:::danger[❓ 오해 3 — 'doorbell은 controller가 host에게 알리는 신호다']
**실제**: 모든 doorbell write는 **host → controller** 방향(BAR MMIO write)입니다. SQ tail doorbell도 CQ head doorbell도 host가 씁니다. controller가 host에 알리는 방향은 doorbell이 아니라 *CQE 작성*(+ 선택적 MSI-X 인터럽트)입니다.<br>
**왜 헷갈리는가**: "벨을 울려 상대를 부른다"는 비유가 양방향처럼 들려서.
:::
:::danger[❓ 오해 4 — 'ring buffer를 size만큼 가득 채울 수 있다']
**실제**: full 판정(`Head == Tail+1`)을 위해 항상 한 슬롯을 비워두므로 실효 용량은 `size − 1`입니다. size개를 모두 채우려 하면 full과 empty(`Head==Tail`)를 구분할 수 없습니다.<br>
**왜 헷갈리는가**: "버퍼 크기 = 담을 수 있는 개수"라는 단순 등식 때문에.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 명령 발행 후 시뮬 hang, completion 없음 | SQ tail doorbell write 누락 | host의 submit 경로에 doorbell MMIO write 존재 여부 |
| host가 completion을 영원히 못 봄 | CQE phase bit 판정 오류 (head만 봄) | polling 루프의 phase 비교 + wrap 시 phase 토글 |
| 일정 명령 이후 controller가 SQE를 더 안 가져감 | SQ full인데 CQ head doorbell 안 갱신 → CQ full로 연쇄 정체(한쪽 큐가 막히면 다른 쪽까지 멈추는 의존) | CQ head doorbell write, completion 수거 루프 |
| `CSTS.RDY`가 안 올라옴 | `CC.EN` 미설정 또는 큐 base 주소 오류 | BAR0의 CC/CSTS, admin 큐 base 주소 |
| 다중 큐인데 한 큐만 처리됨 | 큐별 doorbell offset(doorbell stride) 계산 오류 | `CAP`의 doorbell stride, 큐 index별 doorbell 주소 |

---

## 7. 핵심 정리 (Key Takeaways)

- **NVMe의 host↔controller 통신은 SQ/CQ 큐 쌍 + doorbell** 모델입니다. SQ(host→controller 명령), CQ(controller→host 완료) 둘 다 host 메모리의 circular ring buffer.
- **SQ tail doorbell**(명령 도착)과 **CQ head doorbell**(completion 소비) 모두 host가 쓰는 MMIO write이며, 의미가 반대입니다.
- **doorbell 누락 = hang.** SQE를 메모리에 써도 doorbell 없이는 controller가 모릅니다.
- **polling 환경에서 CQE 유효성은 phase bit**으로 판정합니다. head 포인터만으로는 안 됩니다.
- **ring buffer**: empty `H==T`, full `H==T+1`, 실효 용량 `size−1`, `size−1`에서 wrap-around.
- **BAR0의 CAP/CC/CSTS** 레지스터로 controller를 설정·확인하고, doorbell도 BAR 공간에 있으므로 PCIe 기반이 정상이어야 합니다.

:::caution[실무 주의점]
- submit 경로에 SQ tail doorbell write가 있는지 *항상* 확인 — NVMe hang의 1순위 원인.
- polling 검증에서는 phase bit 토글(wrap 시점)을 정확히 구현해야 stale CQE 오인을 피합니다.
- NRT DV는 polling 기본(MSI 비활성) — interrupt 경로를 가정한 코드는 동작하지 않습니다.
:::

### 7.1 자가 점검

:::tip[🤔 Q1 — doorbell 방향 (Bloom: Analyze)]
host가 명령 5개를 SQ에 넣은 뒤 SQ tail doorbell을 한 번만 (tail=5로) 울렸다. controller는 명령을 몇 개 가져갈 수 있는가?
<details>
<summary>정답 / 해설</summary>

5개 모두 가져갈 수 있습니다. doorbell은 매 명령마다 울릴 필요가 없습니다. host가 여러 SQE를 채운 뒤 tail을 한 번에 5로 갱신하면, controller는 자기가 알고 있던 이전 tail부터 새 tail(5)까지의 모든 SQE를 fetch할 수 있습니다. 이것이 doorbell 횟수를 줄여(batching) MMIO 오버헤드를 낮추는 일반적 최적화입니다. 핵심은 *마지막 tail 값*이 controller에게 "여기까지 유효"를 알려준다는 점입니다.

</details>
:::

:::tip[🤔 Q2 — polling 유효성 (Bloom: Evaluate)]
polling host가 CQ head 위치의 CQE를 읽었더니 직전 바퀴의 오래된 데이터였다. host가 이를 새 completion으로 오인하지 않으려면 무엇을 확인해야 하며, controller는 그 표식을 언제 바꾸는가?
<details>
<summary>정답 / 해설</summary>

host는 CQE의 **phase(P) bit**을 자신이 기대하는 phase 값과 비교해야 합니다. controller는 CQ ring buffer를 한 바퀴 돌(wrap)아 같은 슬롯을 재사용할 때마다 새로 쓰는 CQE의 phase bit을 토글합니다. 따라서 stale 슬롯에는 *이전 바퀴*의 phase가 남아 있어 기대 phase와 다르고, host는 "아직 새 CQE 없음"으로 정확히 판정합니다. head 포인터는 슬롯 위치만 알려줄 뿐 유효성을 보장하지 않습니다.

</details>
:::

### 7.2 출처

**External**
- *NVM Express Base Specification 2.1* §3 (NVM Subsystem), §4 (Submission/Completion Queue) — NVM Express, Inc.

---

## 다음 모듈

→ [03 — 커맨드 분류: Admin / IO / Fabric](../03_command_set_admin_io_fabric/): SQ로 보내는 명령에도 종류가 있다 — controller를 설정하는 Admin, 데이터를 옮기는 IO, 패브릭 전용 Fabric.

[퀴즈 풀어보기 →](../quiz/02_sq_cq_doorbell_quiz/)
