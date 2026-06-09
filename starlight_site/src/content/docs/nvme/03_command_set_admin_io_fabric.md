---
title: "03 — 커맨드 분류: Admin / IO / Fabric"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Differentiate** NVMe 커맨드의 세 분류 — Admin / IO / Fabric — 가 각각 무엇을 하고 어느 큐에서 동작하는지 구분할 수 있다.
- **Explain** Admin 커맨드(controller 설정·identify·get-log-page)와 IO 커맨드(Read/Write 및 변형)의 역할 차이를 설명할 수 있다.
- **Trace** Fabric 커맨드가 opcode 0x7F를 마커로 쓰고 sub-opcode로 실제 명령(Connect/Property Get·Set 등)을 식별하는 인코딩을 추적할 수 있다.
- **Apply** NRT DV 환경의 IO 변형(Flush/Write Zeros/Compare 등)을 `io_type` knob에 맞춰 시나리오로 선택할 수 있다.
:::
:::note[사전 지식]
- [02 — SQ/CQ 큐 메커니즘 & Doorbell](../02_sq_cq_doorbell/)
- NVMe 명령은 64바이트 SQE로 SQ에 적재된다는 점(2장)
- (Fabric 절) NVMe-oF가 패브릭 위에서 동작한다는 큰 그림 — 자세한 건 [4장](../04_nvmeof_over_rdma/)
:::
---

## 1. Why care? — 모든 명령이 데이터를 옮기는 건 아니다

### 1.1 시나리오 — IO 큐를 만들기 전에 해야 할 일

NVMe 검증을 막 시작한 사람이 흔히 하는 실수가 있습니다. controller를 켜자마자 곧장 NVM Write 명령을 IO 큐에 던지는 것입니다. 그런데 IO 큐는 아직 존재하지 않습니다. IO 큐를 만들려면 먼저 **Admin** 커맨드(Create IO Submission/Completion Queue)를 admin 큐로 보내야 하고, 디바이스가 어떤 namespace와 능력을 가졌는지 알려면 **Identify** Admin 커맨드를 먼저 실행해야 합니다.

NVMe 명령은 평평한 하나의 집합이 아니라 세 가지 분류 — **Admin / IO / Fabric** — 로 나뉩니다. controller를 *설정·관리*하는 명령(Admin), 실제로 *데이터를 옮기는* 명령(IO), 그리고 NVMe-oF 패브릭 환경에서만 쓰이는 *연결·속성* 명령(Fabric)입니다. 이 분류를 모르면 어떤 명령을 어느 큐로, 어떤 순서로 보내야 하는지 판단할 수 없습니다.

---

## 2. Intuition — 한 줄 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**커맨드 분류** ≈ **식당의 업무 구분**.<br>
**Admin** = 개점 준비(테이블 세팅, 메뉴 확인, 주방 인원 배치) — 손님을 받기 전 controller를 *구성*. **IO** = 실제 주문 처리(요리를 내고 치움) — *데이터*를 읽고 씀. **Fabric** = 배달 플랫폼 등록(가게를 네트워크에 연결) — 패브릭 위에서만 필요한 *연결/협상* 절차.
:::

### 한 장 그림 — 세 분류와 큐 매핑

```d2
direction: right

HOST: "Host"

ADMIN: "**Admin Commands**\nadmin SQ/CQ (qid=0,\nNVMe-oF에선 qid=5)\nIdentify · Get Log Page\nCreate/Delete IO Queue" 
IO: "**IO Commands**\nIO SQ/CQ (qid≥1)\nNVM Read · NVM Write\nFlush · Write Zeros · Compare"
FABRIC: "**Fabric Commands**\nopcode 0x7F (marker)\nNVMe-oF 전용\nConnect · Property Get/Set\nAuth · Disconnect"

HOST -> ADMIN: "controller 설정·관리"
HOST -> IO: "실제 데이터 전송"
HOST -> FABRIC: "패브릭 연결·협상\n(NVMe-oF only)"
```

순서의 직관: 보통 **Fabric(연결) → Admin(설정·큐 생성) → IO(데이터)** 순으로 진행합니다. 로컬 PCIe NVMe라면 Fabric 단계가 없고, NVMe-oF라면 먼저 Connect로 큐 쌍을 세웁니다.

---

## 3. 작은 예 — 세 분류가 실제로 어떻게 등장하나

NRT DV(NVMe-oF over RDMA) 환경의 전형적 bring-up 순서를 봅니다.

### 단계별 다이어그램

```d2
direction: down

S1: "**① Fabric: Connect**\nadmin QP 활성화 (NRT DV: qid=5,\n표준 로컬 NVMe는 qid=0)\n→ admin 큐 쌍 수립"
S2: "**② Admin: Identify / 설정**\ncontroller·namespace 정보 취득\nIO 큐 생성"
S3: "**③ IO: Write / Read**\nNVM Write로 데이터 적재\nNVM Read로 검증"
S1 -> S2: "Connect 완료 후 admin cmd 가능"
S2 -> S3: "IO 큐 생성 후 IO cmd 가능"
```

### 단계별 의미

| Step | 분류 | 명령 예 | 핵심 |
|---|---|---|---|
| ① | Fabric | Connect | NVMe-oF에서 admin QP(qid=5)를 활성화 — 이후 admin cmd 처리 가능 |
| ② | Admin | Identify, Create IO Queue, Get Log Page | controller/namespace 능력 취득, IO 큐 생성 |
| ③ | IO | NVM Write, NVM Read | 실제 데이터 전송 및 readback 검증 |

:::note[로컬 PCIe vs NVMe-oF]
①의 Fabric 단계는 *NVMe-oF 환경에서만* 등장합니다. 로컬 PCIe NVMe에서는 admin 큐가 PCIe 초기화로 바로 서므로 Connect 없이 Admin부터 시작합니다. NRT DV는 NVMe-oF이므로 Connect 후 admin QP(qid=5)가 활성화되는 흐름을 따릅니다.
:::

---

## 4. 일반화 — 세 분류 상세

### 4.1 Admin Commands

Admin 커맨드는 controller를 *설정·관리*합니다. 큐 관리(Create/Delete IO Queue), 디바이스 식별(Identify), 로그 취득(Get Log Page) 등이 여기 속합니다. NRT DV에서는 NVMe-oF Connect 후 admin QP(qid=5)가 활성화되면 admin 커맨드를 처리할 수 있습니다. 전체 opcode 정의는 NVM Express Base Specification을 참조합니다.

### 4.2 IO Commands

IO 커맨드는 실제 데이터를 옮깁니다. IO 명령 분류와 NRT DV의 `io_type` knob 매핑은 다음과 같습니다.

| 카테고리 | 명령 예 | NRT DV `NrtIoControlKnob_t.io_type` |
|---|---|---|
| Read / Write | NVM Read, NVM Write | `WR_ONLY`, `RD_ONLY`, `WR_AND_RD` |
| Variants | Flush, Write Zeros, Write Uncorrectable, Compare, Cancel | `FLUSH`, `WR_ZERO`, `WR_UNCOR`, `CANCEL` |
| Mixed | Full random opcode mix | `IO_FULL_RAND` |

NRT-TB의 IO 시퀀스는 `lib/vnrttb/include/seq_lib/vnrttb_nvme_io_virtual_sequence_lib.svh`에 있습니다. 검증에서는 단순 Write/Read뿐 아니라 Flush(데이터 영속화), Write Zeros(데이터 없이 0 기록), Compare(읽은 값 비교) 같은 변형과, `IO_FULL_RAND`로 opcode를 무작위 섞은 스트레스 시나리오를 모두 자극해야 합니다.

#### 64바이트 SQE — 한 명령이 담아야 하는 것

2장에서 SQE가 **64바이트 고정 크기**라고 했는데, 이 크기는 임의가 아니라 *한 IO 명령이 자기 일을 완전히 기술하는 데 필요한 필드들의 합*에서 나옵니다. 명령 하나에는 무엇을 할지(opcode), 어느 디바이스에(namespace identifier), 어느 위치를(starting LBA), 얼마나(length), 그리고 **데이터가 host 메모리의 어디에 있는지를 가리키는 포인터**가 들어가야 합니다. 이 포인터 필드가 특히 자리를 차지합니다 — 큰 전송을 위해 여러 메모리 영역을 가리켜야 하기 때문입니다. 이 모든 필드를 담되 큐 슬롯을 규칙적으로 배치(인덱싱·DMA가 단순해지도록)하기 위해, NVMe는 SQE를 64바이트라는 고정 크기로 정했습니다.

#### 데이터는 어디에 있나 — PRP vs SGL

여기서 핵심 질문 하나가 빠져 있습니다. SQE는 64바이트짜리 *명령 기술자*일 뿐인데, 실제로 읽거나 쓸 **데이터 버퍼**(예: 4 KB, 128 KB…)는 SQE 안에 들어갈 수 없습니다. 그렇다면 64바이트 SQE는 데이터를 어떻게 찾아갈까요? 답은 SQE 안의 **data pointer 필드**가 host 메모리에 있는 데이터 버퍼를 *가리킨다*는 것입니다. 데이터 자체는 SQE와 별개로 host 메모리에 살고, controller가 그 포인터를 따라가 DMA로 읽거나 씁니다. NVMe는 이 포인터를 표현하는 두 가지 방식을 정의합니다.

**PRP (Physical Region Page)** — host 메모리를 **페이지 단위**로 가리키는 방식입니다. SQE에는 PRP entry 두 개(PRP1·PRP2)를 담을 자리가 있습니다. 전송이 작아 한두 페이지면 충분하면 PRP1·PRP2가 곧장 그 페이지들을 가리킵니다. 더 많은 페이지가 필요하면 PRP2가 **PRP list**(페이지 주소들의 배열)를 가리키고, controller가 그 리스트를 따라가며 페이지들을 모읍니다. PRP의 전제는 *각 영역이 한 페이지에 정렬된 고정 크기*라는 점 — 그래서 구조가 단순하지만 임의의 byte-offset·가변 길이 영역은 표현하기 어렵습니다.

**SGL (Scatter Gather List)** — host 메모리를 **(주소, 길이) 쌍의 리스트**로 가리키는 더 일반적인 방식입니다. 각 SGL descriptor가 임의의 시작 주소와 임의의 길이를 가질 수 있어, 페이지 정렬에 묶이지 않고 흩어진(scattered) 버퍼를 유연하게 기술합니다. descriptor들을 이어 붙이거나 다음 리스트를 가리키게 해서 큰 전송도 표현합니다. NVMe-oF(패브릭) 전송에서는 SGL이 기본인데, 원격 메모리 영역을 (주소, 길이, key)로 기술하는 RDMA 모델과 자연스럽게 들어맞기 때문입니다(4장).

```d2
direction: right

SQE: "**64B SQE**\nopcode · NSID · LBA · length\n+ data pointer" {
  PRP1: "PRP1 / SGL entry0"
  PRP2: "PRP2 / SGL next"
}

PRP_PATH: "**PRP 방식** (페이지 단위)" {
  P1: "page (4KB 정렬)"
  PLIST: "PRP list\n(page 주소 배열)"
  P2: "page"
  P3: "page"
  PLIST -> P2
  PLIST -> P3
}

SGL_PATH: "**SGL 방식** ((addr,len) 리스트)" {
  D1: "desc: addr0,len0"
  D2: "desc: addr1,len1"
  D3: "desc: → next list"
  D1 -> D2 -> D3
}

SQE.PRP1 -> PRP_PATH.P1: "작은 전송"
SQE.PRP2 -> PRP_PATH.PLIST: "여러 페이지"
SQE.PRP1 -> SGL_PATH.D1: "가변 길이/흩어진 버퍼"
```

요약하면, **64바이트 SQE는 데이터를 담는 게 아니라 데이터를 *가리킨다***. PRP는 페이지 정렬을 전제한 단순한 표현, SGL은 (주소, 길이)로 흩어진 메모리를 유연하게 다루는 표현이며, 패브릭 환경에서는 SGL이 RDMA와 맞물려 쓰입니다.

### 4.3 Fabric Commands

Fabric 커맨드는 **NVMe-oF 환경에서만** 사용하며, capsule transport(RDMA SEND/RECV) 위에서 동작합니다. 인코딩이 독특합니다: **opcode `0x7F`가 Fabric command의 마커**이고, opcode의 sub-field(sub-opcode)가 실제 명령을 식별합니다.

왜 하필 `0x7F` 하나를 마커로 골랐을까요? Fabric은 기존 NVMe보다 나중에 추가된 명령 집합이라, 이미 쓰이고 있던 Admin/IO opcode 공간과 **충돌하지 않는 예약값**을 하나 잡아야 했습니다. 그 자리(0x7F)를 "여기서부터는 Fabric"이라는 단일 진입점으로 정해 두고, 실제 명령 수십 종은 그 안의 sub-opcode로 확장하는 방식입니다. 이렇게 하면 기존 디코더의 opcode 의미를 건드리지 않으면서 Fabric 명령군을 통째로 덧붙일 수 있습니다 — 하나의 예약 opcode를 게이트로 삼아 명령 공간을 *2단계*로 넓힌 설계 의도입니다.

| Sub-opcode | 명령 | 역할 |
|---|---|---|
| 0x00 | Property Set | controller property(레지스터) 쓰기 |
| 0x01 | Connect | 큐 쌍(= RDMA QP) 수립 |
| 0x02 | Property Get | controller property 읽기 |
| 0x05 | Authentication Send | 인증 데이터 송신 |
| 0x06 | Authentication Receive | 인증 데이터 수신 |
| 0x08 | Disconnect | 큐 쌍 해제 |

출처: NVM Express over Fabrics Specification (Fabric Command Set).

:::caution[Fabric은 opcode 0x7F 하나로 시작한다]
Fabric 커맨드는 IO/Admin처럼 opcode가 명령마다 다른 게 아니라, *모두* opcode `0x7F`로 시작합니다. 실제 명령(Connect인지 Property Get인지)은 SQE 안의 sub-opcode field로 구분합니다. 그래서 디코더가 opcode만 보고 "Fabric"임을 인지한 뒤, sub-opcode로 분기해야 합니다.
:::

---

## 5. 디테일 — 명령 디코딩과 검증 포인트

### 5.1 opcode 디코딩 — pseudo code

세 분류의 디코딩을 한 흐름으로 보면 다음과 같습니다(검증 모델 관점 예시).

```c
/* 수신한 SQE의 opcode로 분류 — 개념 예시 */
nvme_cmd_class_t classify(nvme_sqe_t *sqe, nvme_queue_t *q) {
    if (sqe->opcode == 0x7F) {
        /* Fabric: 실제 명령은 sub-opcode로 */
        switch (sqe->fabric.fctype) {   /* fabric command type */
            case 0x00: return FAB_PROPERTY_SET;
            case 0x01: return FAB_CONNECT;
            case 0x02: return FAB_PROPERTY_GET;
            case 0x05: return FAB_AUTH_SEND;
            case 0x06: return FAB_AUTH_RECV;
            case 0x08: return FAB_DISCONNECT;
            default:   return FAB_RESERVED;
        }
    }
    /* opcode가 0x7F가 아니면 큐 종류로 Admin/IO 구분:
       admin 큐(qid=0 또는 NVMe-oF의 qid=5)면 Admin, 그 외 IO 큐면 IO */
    return (q->is_admin) ? CMD_ADMIN : CMD_IO;
}
```

핵심: Fabric은 opcode `0x7F`로 즉시 식별되지만, Admin과 IO의 구분은 *어느 큐로 들어왔는가*(admin 큐 vs IO 큐)로 결정됩니다. 같은 NVM opcode라도 admin 큐로 오면 invalid입니다.

### 5.2 검증에서 챙길 점

검증 시 세 분류 각각에 고유 리스크가 있습니다. Admin은 *순서 의존성*(Identify 없이 IO 큐 생성, 큐 생성 없이 IO 명령) — 잘못된 순서에 controller가 적절히 에러를 반환하는지. IO는 *변형 명령의 부작용*(Flush가 실제로 영속화하는지, Compare가 mismatch를 정확히 보고하는지)과 OoO completion. Fabric은 *opcode 0x7F 디코딩*과 Connect/Disconnect의 상태 전이(연결 안 된 상태에서 IO 시도 시 거부) 검증이 핵심입니다.

---

## 6. 흔한 오해와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'controller를 켜면 바로 IO Write를 보낼 수 있다']
**실제**: IO 큐는 처음에 존재하지 않습니다. **Admin** 커맨드(Create IO Submission/Completion Queue)로 IO 큐를 먼저 만들어야 하고, 그 전에 Identify로 controller/namespace를 파악합니다. NVMe-oF라면 그보다 먼저 Fabric Connect가 필요합니다.<br>
**왜 헷갈리는가**: "controller ready = 데이터 전송 준비 완료"라고 단순화해서 — 큐 생성이라는 admin 단계가 빠짐.
:::
:::danger[❓ 오해 2 — 'Fabric 명령마다 고유 opcode가 있다']
**실제**: 모든 Fabric 명령은 opcode `0x7F` 하나를 공유하고, 실제 명령(Connect/Property/Auth/Disconnect)은 sub-opcode로 구분합니다. opcode만 보고 어떤 Fabric 명령인지 알 수 없습니다.<br>
**왜 헷갈리는가**: Admin/IO는 opcode마다 명령이 다르므로 Fabric도 그럴 거라 유추해서.
:::
:::danger[❓ 오해 3 — 'Fabric 명령은 PCIe NVMe에서도 쓴다']
**실제**: Fabric 커맨드는 **NVMe-oF 환경에서만** 사용하며 capsule transport(RDMA SEND/RECV) 위에서 동작합니다. 로컬 PCIe NVMe에는 Connect/Disconnect 같은 Fabric 절차가 없습니다(PCIe 초기화가 그 역할).<br>
**왜 헷갈리는가**: "NVMe 명령 집합"을 하나로 보고 환경에 무관하게 모두 쓰인다고 생각해서.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| IO Write가 invalid command로 거부됨 | IO 큐 미생성 또는 admin 큐로 IO 명령 발송 | Create IO Queue admin cmd 선행 여부, 큐 qid |
| Fabric 명령이 모두 같은 명령으로 디코딩됨 | sub-opcode field 무시, opcode 0x7F만 봄 | 디코더의 fctype/sub-opcode 분기 |
| Connect 전 IO 시도 시 hang/거부 | NVMe-oF에서 큐 쌍 미수립 | Fabric Connect 완료 후 admin QP(qid=5) 활성 여부 |
| Compare가 항상 통과 | Compare 데이터 경로 미구현/스텁 | IO variant 처리, `io_type=CANCEL`/`FLUSH` 등 분기 |
| `IO_FULL_RAND`에서 특정 opcode만 안 나옴 | 시퀀스의 opcode 분포 제약 과다 | `vnrttb_nvme_io_virtual_sequence_lib.svh`의 randomize 제약 |

---

## 7. 핵심 정리 (Key Takeaways)

- **NVMe 명령은 Admin / IO / Fabric 세 분류**입니다. Admin은 controller 설정·관리, IO는 데이터 전송, Fabric은 NVMe-oF 전용 연결·속성.
- **순서**: (NVMe-oF면) Fabric Connect → Admin(Identify·IO 큐 생성) → IO. IO 큐는 admin 명령으로 *만들어야* 존재합니다.
- **IO 변형**: Read/Write 외에 Flush, Write Zeros, Write Uncorrectable, Compare, Cancel 등 — NRT DV는 `io_type` knob으로 선택.
- **Fabric 인코딩**: opcode `0x7F`가 마커, sub-opcode로 Connect(0x01)/Property Set(0x00)·Get(0x02)/Auth(0x05·0x06)/Disconnect(0x08) 식별.
- **Fabric은 NVMe-oF 전용** — capsule transport(RDMA SEND/RECV) 위에서만 동작합니다.

:::caution[실무 주의점]
- IO 명령 전 *반드시* Admin으로 IO 큐를 생성했는지 확인 — bring-up 순서 버그의 단골.
- Fabric 디코더는 opcode 0x7F 인지 → sub-opcode 분기의 2단계여야 합니다.
- Admin/IO 구분은 opcode가 아니라 *큐 종류*(admin 큐 vs IO 큐)로 결정됩니다.
:::

### 7.1 자가 점검

:::tip[🤔 Q1 — 분류와 큐 (Bloom: Differentiate)]
같은 NVM opcode가 admin 큐로 들어왔다. controller는 이를 어떻게 처리해야 하며 왜 그런가?
<details>
<summary>정답 / 해설</summary>

거부(invalid command 상태 반환)해야 합니다. Admin과 IO의 구분은 opcode 자체가 아니라 *어느 큐로 들어왔는가*로 결정됩니다. NVM Read/Write 같은 IO opcode는 IO 큐에서만 유효하며, admin 큐(qid=0 또는 NVMe-oF의 qid=5)는 Admin 커맨드 집합만 받습니다. controller가 큐 종류에 맞지 않는 opcode를 받으면 적절한 에러 status로 응답해야 하고, 검증은 이 거부가 정확히 일어나는지를 확인합니다.

</details>
:::

:::tip[🤔 Q2 — Fabric 디코딩 (Bloom: Apply)]
NVMe-oF target 모델이 opcode 0x7F인 SQE를 받았다. 다음으로 어떤 field를 보고 무엇을 결정해야 하며, sub-opcode 0x01이면 무슨 명령인가?
<details>
<summary>정답 / 해설</summary>

opcode 0x7F는 "이것은 Fabric 커맨드"라는 마커일 뿐이므로, 다음으로 SQE 안의 **sub-opcode(fabric command type)** field를 보고 실제 명령을 결정해야 합니다. sub-opcode가 `0x01`이면 **Connect** — 큐 쌍(NVMe-oF에서는 RDMA QP 한 쌍)을 수립하는 명령입니다. Connect가 성공해야 그 위에서 admin/IO 커맨드를 주고받을 수 있습니다.

</details>
:::

### 7.2 출처

**External**
- *NVM Express Base Specification 2.1* — Admin/IO command set
- *NVM Express over Fabrics Specification* §6 (Fabric Command Set) — NVM Express, Inc.

---

## 다음 모듈

→ [04 — NVMe-oF over RDMA](../04_nvmeof_over_rdma/): Fabric 커맨드가 동작하는 무대 — NVMe 큐 쌍이 RDMA QP에 매핑되고, capsule이 SEND/RECV로 운반되는 원격 스토리지 검증.

[퀴즈 풀어보기 →](../quiz/03_command_set_admin_io_fabric_quiz/)
