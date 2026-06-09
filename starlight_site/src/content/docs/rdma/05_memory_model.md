---
title: "Module 05 — Memory Model: PD, MR, L_Key/R_Key, IOVA"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Define** PD, MR, L_Key, R_Key, IOVA 의 정의와 역할을 ISO 11179 형식으로 진술한다.
- **Trace** Memory Registration 흐름을 단계별로 추적한다 (`ibv_reg_mr` → kernel → HCA pin/PRI → key 발급).
- **Trace** 한 RDMA WRITE 가 도착했을 때 responder 가 5단계 key/access/range/PD 검증을 어떻게 하는지 따라간다.
- **Apply** access flag (Local Write, Remote Read/Write, Atomic) 를 시나리오에 매핑한다.
- **Diagram** RDMA-TB 의 MMU/PTW/TLB 가 IOVA 변환에서 하는 역할을 그릴 수 있다.
:::
:::note[사전 지식]
- Module 01 의 Verbs 6 객체
- PCIe ATS / IOMMU 기본 (선택)
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — 보안 사고가 한 번에 1000 노드를 망친다

분산 KV store 를 RDMA WRITE 로 구현하고 막상 돌려보면 잘 동작합니다. 그런데 어느 날 한 노드의 메모리가 application 이 쓰지도 않은 영역까지 이상하게 변조되기 시작합니다. 추적해 보면 외부 공격자가 R_Key(Remote Key — 원격 노드가 내 메모리에 접근할 때 제시해야 하는 보호 키) 를 어떤 경로로 알아내고, 그 키를 이용해 노드의 임의 주소에 RDMA WRITE 를 쏘고 있는 상황입니다. (이 모듈의 핵심 객체 — **PD**·**MR**·**L_Key**·**R_Key**·**IOVA** — 의 정식 정의는 §4.1 표에 있으니, 막히면 그쪽을 먼저 보세요.)

이 사고가 가능한 이유는 RDMA 의 인증 모델이 TCP 와 근본적으로 다르기 때문입니다. TCP 는 connection 자체가 인증 단위여서 연결이 맺어진 상대만 데이터를 보낼 수 있지만, RDMA 는 **키가 곧 권한 토큰**입니다. R_Key 만 알면 연결 상태와 무관하게 접근이 허용되므로, 키 유출은 곧 보안 사고입니다. 따라서 RDMA 는 키 하나에 의존하지 않고 다음 네 가지 방어층을 겹쳐 사용합니다.

1. **PD**(Protection Domain — RDMA 객체들을 한 묶음으로 격리하는 보호 경계) **격리** — 다른 PD 의 MR(Memory Region, 등록된 메모리 영역) 은 못 봄.
2. **Access flag**(이 영역에 읽기/쓰기/atomic 중 무엇을 허용할지 정한 권한 비트) **제한** — Remote Read 만 줄지, Remote Write 도 줄지.
3. **Range 제한** — MR base + len 범위 안에서만.
4. **R_Key 자체의 lifetime 제한** — Memory Window(MR 의 일부에 짧은 기간만 별도 R_Key 를 발급하는 객체) 패턴.

이 네 가지 검증 단계는 **하드웨어가 패킷 수신 시점에 즉시** 처리해야 합니다. SW 가 끼는 순간 µs 단위 latency 목표가 무너지기 때문에, 5-step 검증이 _hardware ASIC 레벨_ 로 명세돼 있습니다.

**RDMA 의 모든 데이터 path 는 "주소 + key" 의 쌍으로 표현** 됩니다. local 측 sg_list 는 (`addr`, `length`, `lkey`), remote 측 RDMA WRITE 의 RETH 는 (`remote_va`, `length`, `rkey`). 이 키 검증과 IOVA → PA(physical address, 실제 물리 메모리 주소) 변환을 누가 어떻게 하는지가 RDMA 보안과 성능의 핵심.

검증 환경에서 **가장 디버그가 어려운 영역** 도 이쪽입니다 — `WC_LOC_PROT_ERR`, `WC_REM_ACCESS_ERR` 같은 에러는 lkey/rkey/PD/access flag/range 5가지 중 하나라도 틀리면 발생하므로, 정확한 진단을 위해 5가지 모두를 알아야 합니다.

:::tip[🤔 잠깐 — L_Key 와 R_Key 를 _분리_ 한 이유]
같은 MR 등록에서 _두 키_ 가 발급됩니다. "한 키" 로 통일했다면 무엇이 깨질까?

<details>
<summary>정답</summary>

**_자기_ 가 쓸 때와 _남_ 이 쓸 때 권한이 달라야 한다**.

예: GPU memory 를 RDMA 가 _자기_ buffer (Local Read) 로 쓰는 건 OK. 그러나 _외부 노드_ 가 임의로 쓰게 하는 건 보안 위험.
- 해법 A (단일 키): MR 에 access flag 만 두고 같은 키를 양쪽 모두 사용 → "자기 access" 와 "외부 access" 권한을 _별도로_ 줄 수가 없음 (한 키, 한 access set).
- 해법 B (이중 키): L_Key 만 발급하고 R_Key 발급 _안 함_ 가능 → 외부 노출 자체를 차단. 더 fine-grained.

IBTA 는 해법 B 채택. _R_Key 가 없으면_ 외부 노드는 _이름조차 모름_.

</details>
:::
---

## 2. Intuition — 비유와 한 장 그림

:::tip[💡 한 줄 비유 — Memory Registration ≈ 공항 보안 검색대 통과 + 게이트 번호 발급]
- **PD** = 항공사 (다른 항공사 게이트로는 못 들어감)
- **MR** = 보안 검색대 통과한 짐 (이미 X-ray 끝)
- **L_Key** = 내 짐 표 (나만 사용)
- **R_Key** = 상대에게 알려주는 픽업 코드 (가지고 와도 됨)
- **IOVA** = 게이트 번호 (실제 비행기 위치는 ground crew 가 매핑)
- **Access flag** = 짐 라벨 (RO/RW/ATOMIC 권한)
:::
### 한 장 그림 — 객체 묶음 + 검증 chain

```d2
direction: down

PD: "**PD** 보호 도메인"
MR: "**MR**\n(lkey, rkey, [iova, len], access_flags)\npages pinned + IOVA→PA mapping in HCA's ATS"
QP: "**QP**\n같은 PD 안에서만 MR 사용 가능"
PD -> MR: "owns"
PD -> QP: "owns"
WR: "incoming RDMA WRITE"
V1: "rkey 일치?\n(key table)" { shape: diamond }
V2: "access?\n(remote_w?)" { shape: diamond }
V3: "PD 같음?\nqp.pd == mr.pd" { shape: diamond }
V4: "range 안?\n[va, va+len] ⊆ MR" { shape: diamond }
V5: "IOVA→PA?\nTLB hit? else PTW" { shape: diamond }
OK: "DMA write"
NAK: "NAK"
WR -> V1
V1 -> V2: "Yes"
V2 -> V3: "Yes"
V3 -> V4: "Yes"
V4 -> V5: "Yes"
V5 -> OK: "Yes"
V1 -> NAK: "No"
V2 -> NAK: "No"
V3 -> NAK: "No"
V4 -> NAK: "No"
V5 -> NAK: "No"
```

### 왜 이렇게 설계했는가 — Design rationale

RDMA 의 보안 모델은 "**키만 알면 누구든 접근 가능**" 이라는 전제 위에 서 있습니다. TCP 처럼 connection 자체가 인증 단위인 게 아니라, 키가 곧 권한 토큰입니다. 그래서 키가 유출되면 보안 사고로 이어지므로 다중 방어층이 필요합니다. 즉 PD 로 격리하고, access flag 로 기능을 제한하고, range 로 영역을 좁히는 것이 동시에 작동해야 합니다. 이 5단계 검증이 hardware 로 수행되는 이유도 같습니다. SW 가 한 단계라도 끼면 RDMA 의 zero-copy latency 가 무너지기 때문입니다.

L_Key 와 R_Key 를 굳이 두 개로 분리한 이유도 여기에 있습니다. 같은 메모리 영역이라도 _자신이_ 쓸 때와 _원격 노드가_ 쓸 때의 권한이 달라야 합니다. 예를 들어 GPU memory 를 RDMA 가 자기 payload buffer (Local Read) 로 읽어가는 건 허용하면서, 외부 노드가 그 영역에 임의로 쓰는 건 막고 싶다면 L_Key 만 발급하고 R_Key 는 발급하지 않으면 됩니다. 두 키를 하나로 합치면 이런 세밀한 접근 제어가 불가능해집니다.

---

## 3. 작은 예 — 한 MR 등록부터 원격 WRITE 수신까지

A 가 1 MB buffer 를 등록하고, B 가 그 영역에 1 KB RDMA WRITE.

```
   ──── Step 1~6: A 측 등록 ────
   ① user code:
        buf = malloc(1<<20);
        mr = ibv_reg_mr(pd, buf, 1<<20,
                        IBV_ACCESS_LOCAL_WRITE | IBV_ACCESS_REMOTE_WRITE);
   ② kernel:
        get_user_pages_pin(buf, 256 pages)        ← page-pin (swap 방지)
        build IOVA mapping table                  ← IOVA = buf_va (or assigned)
   ③ kernel → HCA via PCIe MMIO:
        push descriptor: (PD=p1, IOVA=0x1000, len=1<<20, access=LW|RW)
   ④ HCA:
        ATS table: IOVA 0x1000..0x101000 → PA list
        PD lookup: p1 가 valid 인지
        Key table 발급:
            lkey = 0x12340001  (24-bit index 0x123400 + 8-bit tag 0x01)
            rkey = 0x12340101  (다른 tag 발급)
   ⑤ HCA → kernel:
        (lkey, rkey) 반환
   ⑥ user code: 받은 (mr->lkey, mr->rkey)

   ──── Step 7~9: A 가 B 에게 (remote_va, rkey) 전달 ────
   ⑦ A → B 로 RDMA-CM 또는 sockets out-of-band 로
        (remote_va = buf_va = 0x1000, rkey = 0x12340101) 전송

   ──── Step 8~12: B 가 RDMA WRITE 1 KB 송신 ────
   ⑧ B 의 ibv_post_send(WRITE, sg_list=(local_buf, 1024, B_lkey),
                          remote_va=0x1000, rkey=0x12340101)
   ⑨ B 의 HCA: local_buf 에서 1024 B DMA read
   ⑩ packet (BTH + RETH(rkey=0x12340101, va=0x1000, dmalen=1024) + payload) → A

   ──── Step 13~17: A 의 HCA 가 5-step 검증 ────
   ⑪ A 의 HCA 가 RETH.rkey = 0x12340101 으로 key table lookup
        → MR p1 찾음 (matched)                   ✓ (1)
   ⑫ MR access flag = LW|RW; incoming = WRITE
        → Remote Write 권한 있음                 ✓ (2)
   ⑬ MR.pd = p1; QP.pd = p1
        → 같은 PD                                ✓ (3)
   ⑭ MR range = [0x1000, 0x101000]; va+len = [0x1000, 0x1400]
        → 범위 내                                ✓ (4)
   ⑮ ATS lookup IOVA 0x1000 → TLB miss → PTW → PA 0x80000000
        → 변환 성공                              ✓ (5)
   ⑯ HCA 가 PA 0x80000000 에 1024 B DMA write
   ⑰ ACK 송신 → B 측 CQE SUCCESS

   ──── 만약 B 가 잘못된 rkey 보냈으면 ────
   ⑪' rkey 0x12340999 (틀림) → key table 미일치 → 즉시 NAK Remote Access Error
   B 측 CQE = IBV_WC_REM_ACCESS_ERR
```

### 단계별 의미

| Step | 위치 | 의미 |
|---|---|---|
| ①~⑥ | A 측 1회 setup | MR 등록 = page pin + IOVA 매핑 + PD 묶기 + key 발급. **datapath 호출 비용 0** |
| ⑦ | out-of-band | RDMA 자체에는 채널이 없음. CM 또는 socket 으로 (rkey, va) 약속 |
| ⑧ | B 측 datapath | post_send = 도어벨 1번 (kernel 안 거침) |
| ⑨~⑩ | wire | RETH 가 첫 packet 에 (rkey, va, len) 운반 |
| ⑪~⑮ | A HCA | **5-step 검증을 hardware 가 packet 수신 시점에 수행** |
| ⑯ | A HCA | DMA write — A 의 CPU 안 깨움 |
| ⑰ | wire + B HCA | RC 의 reliability 마무리 |

:::note[여기서 잡아야 할 두 가지]
**(1) 5-step 검증은 모두 hardware** — sw 가 한 단계라도 끼면 RDMA 의 의미가 사라집니다. 검증 시 "각 step 의 NAK 가 정확히 발생하는가" 를 individually inject 해야 합니다.<br>
**(2) lkey 와 rkey 는 같은 MR 인데 다른 tag** — 같은 영역이라도 자기 vs 남의 사용을 별개 키로. 위 예에서 A_lkey=`0x12340001`, A_rkey=`0x12340101` — index 같지만 tag 다름.
:::
---

## 4. 일반화 — 객체 계층과 검증 체인

### 4.1 객체 계층

```d2
direction: down
PD: "**PD**\nProtection Domain (보호 경계)" { style.stroke: "#1a73e8"; style.stroke-width: 2 }
MR: "**MR** (region)"
QPSRQ: "QP / SRQ"
LK: "L_Key" { style.stroke: "#137333"; style.stroke-width: 2 }
RK: "R_Key" { style.stroke: "#137333"; style.stroke-width: 2 }
PD -> MR: "owns"
MR <-> QPSRQ: "pairs"
MR -> LK: "has"
MR -> RK: "has"
```

| 객체 | 정의 (ISO 11179) |
|------|-----------------|
| **PD (Protection Domain)** | QP 와 MR 등 RDMA 객체들을 그룹으로 묶어 cross-domain 접근을 차단하는 보호 경계 식별자. |
| **MR (Memory Region)** | Memory Registration 으로 NIC 에 등록된 가상-주소 연속 영역과 그에 대한 access 권한, key, PD 의 묶음. |
| **L_Key (Local Key)** | MR 을 같은 노드의 sg_list 등 local reference 에서 검증할 때 사용하는 24+ bit 식별자. |
| **R_Key (Remote Key)** | MR 을 원격 노드의 RDMA WRITE/READ/ATOMIC 가 RETH/AtomicETH 에 넣어 보내, responder side 에서 검증하는 식별자. |
| **IOVA (IO Virtual Address)** | Device 에서 사용하는 가상 주소로, NIC 의 ATS/PTW/TLB 가 PA 로 변환한다. |

### 4.2 5-step 검증 체인 (responder)

```d2
direction: down

IN: "incoming RDMA WRITE (PSN=N)\nRETH: remote_va, len, rkey"
S1: "1) rkey 로 MR 찾기"
S2: "2) MR 의 access flag 검증"
S3: "3) MR 의 PD 와 QP 의 PD 비교"
S4: "4) [remote_va, remote_va+len] 가\nMR 영역 안에 있는지"
S5: "5) IOVA → PA 변환 (TLB/PTW)"
S6: "6) DMA write 수행"
NAK1: "NAK Remote Access Error"
NAK2: "NAK"
NAK3: "NAK"
NAK4: "NAK"
NAK5: "NAK"
IN -> S1
S1 -> NAK1: "미일치"
S1 -> S2: "match"
S2 -> NAK2: "Remote Write 없음"
S2 -> S3: "ok"
S3 -> NAK3: "다름"
S3 -> S4: "같음"
S4 -> NAK4: "범위 벗어남"
S4 -> S5: "안"
S5 -> NAK5: "변환 실패"
S5 -> S6: "ok"
```

→ **모든 단계에서 fail 시 NAK + WC error** (`IBV_WC_REM_ACCESS_ERR` 류).

:::note[Spec 인용]
"When a memory access reference (lkey or rkey) does not validate against the receiver's protection domain, access flags, or address range, the responder shall generate a NAK and the requester shall mark the corresponding WR with completion error." — IB Spec 1.7, §10.6 (R-407 ~ R-500 영역)
:::
---

## 5. 디테일 — Registration flow, Access, IOVA, MW, ODP, MPE

### 5.1 Memory Registration 흐름 상세

```d2
shape: sequence_diagram

U: "User-space"
K: "Kernel"
H: "HCA / RNIC"

U -> K: "ibv_reg_mr(pd, addr,\nlength, access_flags)"
K -> K: "1) get_user_pages_pin\npin pages → PA list"
K -> K: "2) build IOVA mapping"
K -> H: "3) PCIe MMIO\npush descriptor"
H -> H: "4) ATS table\nIOVA→PA 등록"
H -> H: "5) PD lookup\nPD 와 묶기"
H -> H: "6) Key table\nL/R Key 발급"
H -> K: "(lkey, rkey)" { style.stroke-dash: 4 }
K -> U: "(lkey, rkey)" { style.stroke-dash: 4 }
```

각 단계에서 발생할 수 있는 검증 포인트:

| 단계 | 검증 |
|------|------|
| 1. pin pages | OOM 시 reg_mr 실패. RDMA-TB 는 host memory model 이 swap-out 가능성 무시 (모든 페이지 pinned 가정). |
| 2. IOVA mapping | 동일 PD 안에서 IOVA 겹침 → 거부 |
| 3. MMIO descriptor push | Doorbell write 와 descriptor 의 timing 검증 |
| 4. ATS table | TLB miss → PTW (Page Table Walker) 호출 → page table 읽음 |
| 5. PD 묶기 | QP 의 PD 와 MR 의 PD 다르면 access 시 fail |
| 6. Key 발급 | 24-bit key index + 8-bit tag (변형 가능) — 이전에 사용한 key 의 reuse 시 epoch 체크 필요 |

:::note[메커니즘 — rkey 의 index+tag 가 use-after-free 를 막는 원리]
rkey(또는 lkey) 는 보통 **24-bit index + 8-bit tag** 로 나뉩니다. index 는 NIC 안의 key table 에서 _몇 번째 슬롯_ 인지를 가리키는 직접 주소이고, tag 는 그 슬롯의 _현재 세대(generation/epoch)_ 를 나타내는 작은 값입니다. lookup 은 두 단계로 이뤄집니다: ① index 로 슬롯을 찾고, ② 패킷이 들고 온 tag 와 슬롯에 저장된 현재 tag 가 **일치하는지** 확인합니다.

왜 이게 중요한가? key table 슬롯은 한정돼 있어서, MR 을 dereg 하면 그 index 슬롯이 **나중에 다른 MR 에 재사용** 됩니다. 만약 index 만으로 검증한다면, 옛 MR 의 rkey 를 들고 온 (혹은 유출된) stale 패킷이 _같은 index 를 재사용한 새 MR_ 에 접근해버립니다 — 전형적인 use-after-free. tag 가 이를 막습니다: dereg→재할당 때마다 tag 를 증가시키므로, 옛 rkey 의 tag 는 슬롯의 새 tag 와 **불일치** → 즉시 거부됩니다. 즉 index 는 "어디" 를, tag 는 "그게 아직 그 MR 이 맞는지" 를 검증하는 역할 분담입니다. 이것이 §5.6 의 "dereg 후 같은 IOVA 재등록" corner case 와 §5.8 의 invalidate 가 안전하게 동작하는 hardware 근거입니다.
:::

### 5.2 Access Flag

```
   IBV_ACCESS_LOCAL_WRITE      ← 로컬 sender 가 이 영역에 write (예: SEND payload 가 들어옴)
   IBV_ACCESS_REMOTE_READ      ← 원격 노드가 RDMA READ 가능
   IBV_ACCESS_REMOTE_WRITE     ← 원격 노드가 RDMA WRITE 가능
   IBV_ACCESS_REMOTE_ATOMIC    ← 원격 노드가 ATOMIC (CMP_SWAP/FADD) 가능
   IBV_ACCESS_MW_BIND          ← Memory Window bind 가능
   IBV_ACCESS_ZERO_BASED       ← VA = 0 부터 시작하는 zero-based 등록
   IBV_ACCESS_ON_DEMAND        ← ODP (On-Demand Paging) — pin 없이 page fault 처리
```

#### 권한 매트릭스

| Operation | Sender side 검증 | Receiver/Responder side 검증 |
|-----------|------------------|----------------------------|
| RDMA WRITE 발신 | sg_list `lkey` + Local Write/Read on payload buffer | RETH `rkey` + Remote Write |
| RDMA READ 발신 | sg_list `lkey` + Local Write on local buf | RETH `rkey` + Remote Read |
| RDMA ATOMIC 발신 | sg_list `lkey` + Local Write on local buf | AtomicETH `rkey` + Remote Atomic |
| SEND 발신 | sg_list `lkey` + Local Read on payload | (RECV) WR sg_list `lkey` + Local Write |
| SEND with IMM 수신 | — | RECV WR sg_list `lkey` |

→ **주의**: RDMA WRITE 의 sender 자신의 buffer 는 "Local Read" 가 필요 (HCA 가 읽어가야 함). "Local Write" 는 RDMA READ 의 sender 측에서 필요 (HCA 가 받은 데이터를 local 에 쓴다).

### 5.3 IOVA, ATS, PTW, TLB

세 약어를 먼저 풀면: **ATS**(Address Translation Service — PCIe 디바이스가 IOVA→PA 변환을 하고 그 결과를 캐시하도록 하는 표준), **PTW**(Page Table Walker — TLB 에 없는 변환을 page table 을 따라가며 찾아내는 하드웨어), **TLB**(Translation Lookaside Buffer — 최근 변환 결과를 저장해 재계산을 피하는 캐시) 입니다.

```d2
direction: down

PKT: "RDMA packet → BTH → RETH\n(rkey, IOVA, len)"
HCA: "HCA" {
  direction: down
  ATS: "ATS / TLB\n(변환 캐시)"
  PTW: "PTW · Page Table Walker\n(page table walk)"
  DMA: "PCIe DMA"
  ATS -> PTW: "TLB miss"
  PTW -> DMA: "PA"
  ATS -> DMA: "TLB hit · PA"
}
HOST: "host memory"
PKT -> ATS
DMA -> HOST
```

:::note[메커니즘 — PTW 가 다단계 page table 을 걷는 과정, 그리고 latency 가 변동하는 이유]
가상주소(IOVA)→물리주소(PA) 매핑은 한 칸짜리 표가 아니라 **여러 level 의 page table 이 트리처럼 연결된 구조** 입니다. IOVA 의 비트들을 위에서부터 잘라 각 level 의 인덱스로 씁니다 — 예컨대 최상위 비트들로 1단계 표에서 entry 를 찾고, 그 entry 가 가리키는 _다음 level 표_ 의 base 주소에 다음 비트들을 인덱스로 더해 또 읽고… 를 leaf entry (실제 PA frame) 에 닿을 때까지 반복합니다. **PTW (Page Table Walker)** 가 하는 일이 바로 이 단계적 인덱싱입니다. 각 단계가 _메모리를 한 번씩 읽는_ 동작이므로, L 단계 page table 이면 한 번의 변환에 최악 L 번의 메모리 접근이 듭니다.

여기서 **latency 변동** 이 생깁니다. 자주 쓰는 변환은 **TLB (변환 캐시)** 에 들어 있어 TLB hit 이면 한 사이클 수준으로 끝나지만, **TLB miss 면 PTW 가 전체 walk 를 수행** 해야 하고 그 walk 자체도 중간 level 표가 캐시에 있느냐 없느냐에 따라 걸리는 메모리 접근 횟수가 달라집니다. 그래서 같은 RDMA WRITE 라도 "TLB hit (빠름)" 과 "TLB miss → multi-level walk (느림)" 사이에서 처리 시간이 출렁입니다. 이것이 large MR·sparse access 패턴에서 tail latency 가 커지는 근본 원인이고, RDMA-TB 가 PTW/TLB 를 module-level 로 따로 떼어 _miss 시나리오와 walk 단계_ 를 집중 검증하는 이유입니다.
:::

RDMA-TB 의 sub-IP 검증 환경은 이 변환 chain 을 직접 검증:

| RDMA-TB 위치 | 검증 대상 |
|--------------|----------|
| `lib/submodule/metadata/mmu/` | MMU 전체 |
| `lib/submodule/metadata/mmu/.../ptw/` | Page Table Walker — 다단계 page walk |
| `lib/submodule/metadata/mmu/.../tlb/` | TLB caching, eviction, invalidate |
| `lib/submodule/metadata/mmu/.../reset/` | MMU reset 시퀀스 |
| `lib/submodule/metadata/rq_fetcher/` | Receive Queue fetcher (WQE prefetch) |

→ 자세한 환경 구조는 [Module 08 RDMA-TB DV](../08_rdma_tb_dv/).

:::note[RDMA-TB MMU 의 5 hierarchy]
`class_hier.md` 기준 — board → ip_top → plane (metadata) → sub_ip (mmu) → module (ptw/tlb/reset).

각 module 마다 standalone TB 가 존재해, MMU 전체를 한 번에 검증하지 않고 module 별로 빠르게 쪼개 검증.
:::
### 5.4 Memory Window (MW)

MW 는 **MR 의 부분 영역에 대해 일시적으로 다른 R_Key 를 발급** 하는 메커니즘:

- Type 1 MW: bind 시 verbs 호출, posting overhead 있음
- Type 2 MW: bind 가 send WQE 의 일부 — fast path

용도: 짧은 lifetime 의 권한 위임. 예: "이 한 RPC 동안만 1 KB 영역에 RDMA WRITE 를 허용".

→ 검증 시 **MW 의 R_Key invalidate 시 in-flight RDMA WRITE 가 어떻게 처리되는가** 가 corner case.

### 5.5 ODP (On-Demand Paging)

`IBV_ACCESS_ON_DEMAND` 로 등록된 MR 은 pin(페이지를 물리 메모리에 고정해 swap·이동을 막는 것) 안 함 → page fault(접근하려는 페이지가 물리 메모리에 없어 OS 가 채워 넣어야 하는 상황) 가능 → HCA 가 PCIe PRI (Page Request Interface — 디바이스가 OS 에 "이 페이지를 메모리로 올려달라"고 요청하는 인터페이스) 로 OS 에 page-in 요청.

장점: 큰 영역도 메모리 부담 없이 등록.<br>
단점: page fault 시 latency 큼, retry/timeout 가능성.

검증: page fault → PRI → OS handle → ATS update → packet 재시도 의 전체 chain.

### 5.6 자주 보는 메모리 모델 문제

| 문제 | 원인 | 진단 |
|------|------|-----|
| `IBV_WC_LOC_PROT_ERR` | sg_list lkey 잘못 / access flag 부족 / addr 범위 벗어남 | requester side WC, sender 의 책임 |
| `IBV_WC_REM_ACCESS_ERR` | RETH rkey 잘못 / access flag 부족 / 범위 벗어남 | responder NAK, requester WC error |
| `IBV_WC_REM_INV_REQ_ERR` | OpCode 와 service type 불일치 (예: UC 에 READ) | responder NAK |
| Silent corruption | 동일 IOVA 가 두 MR 에 매핑됨 (구현 버그) | scoreboard 가 expected vs actual 불일치 catch |
| TLB stale 변환 | MR dereg 후 TLB invalidate 누락 | 검증: dereg → 새 MR 같은 IOVA 등록 → 첫 packet 의 PA 확인 |

### 5.7 Confluence 보강 — Memory Window (DH 변형)

:::note[Internal (Confluence: Memory Window (feat. DH), id=155812337)]
MW 는 기존 MR 의 부분 영역에 **임시 R_Key** 를 부여한다. IBTA 는 두 종류의 MW 를 정의한다.

| MW Type | Bind | Use case |
|---|---|---|
| **Type 1** | verb 호출로 bind / unbind | 표준 MW, Steering Tag 변경 빈도 낮음 |
| **Type 2 (DH)** | data-path 에서 SEND_BIND_MW / SEND_INVALIDATE 패킷으로 bind | DH (Dynamic Handle) — 동적/단명 R_Key, RPC-style 보안 |

사내 IP 는 Type 2 (DH) MW 를 우선 지원해 **R_Key lifetime** 을 단일 RPC 단위로 짧게 가져가는 패턴을 유도한다. M01 의 "R_Key 노출은 짧게 + MW 패턴" 권장과 직접 연결된다.
:::
### 5.8 Confluence 보강 — Local / Remote Invalidation

:::note[Internal (Confluence: Local/Remote Invalidation, id=155844886)]
R_Key 또는 MW 의 유효성을 즉시 무효화한다.

- **Local Invalidate**: SQ 에 `IBV_WR_LOCAL_INV` 를 post → 자기 IP 가 해당 R_Key 를 invalid 처리.
- **Remote Invalidate**: 송신측이 `SEND_WITH_INVALIDATE` 패킷으로 R_Key 를 운반 → 수신측이 SEND 처리 후 즉시 R_Key invalid.
- 검증: invalidate 후 동일 R_Key 로 들어오는 WRITE/READ → `IBV_WC_REM_ACCESS_ERR` (M07 §3 의 S5).
:::
### 5.9 Confluence 보강 — Memory Placement Extensions (MPE)

:::note[Internal (Confluence: Memory Placement Extensions (MPE), id=217808945) — IBTA Annex A19]
MPE 는 RDMA WRITE 시 receiver 측 cache·persistent memory placement 를 송신자가 제어할 수 있게 한다.

- **FLUSH** opcode: 이전 RDMA WRITE payload 가 PMEM 까지 **durable** 하게 flush 됐음을 ACK 받기 전 보장.
- **ATOMIC WRITE**: 1, 2, 4, 8 byte naturally aligned write 의 atomicity 보장 (메모리 controller 단위).
- **RDMA WRITE with Partial Flush**: WRITE 와 FLUSH 시맨틱 결합.
- 검증: FLUSH ACK 까지 latency, persistent memory model (예: nvdimm-style), 동일 영역의 ATOMIC WRITE + RDMA WRITE 순서.
:::
### 5.10 Confluence 보강 — Large MR 와 In-flight WR 관리

:::note[Internal (Confluence: Large MR support, id=93814912; In-flight WR management, id=133497307)]
- **Large MR**: GPU peer-memory (≥수십 GB) 를 단일 MR 로 등록. PTW/TLB 의 sparse range 를 지원해야 하며, dereg 시 in-flight DMA 를 모두 drain 해야 R_Key invalidate 안전.
- **In-flight WR management**: 사내 IP 는 SWQ 의 read port 다중화 (M11 의 `s_data_port_0/3/4` 참조) 로 **modify / read_init / read** 를 분리. 각 채널은 outstanding 한도가 다르며 retry 시 같은 read port 로 다시 fetch 된다.
- 검증: outstanding WR 한도까지 채운 상태에서 dereg → drain 동작; large MR 에서 PSN wraparound (24-bit) 까지 갈 수 있는 long-running WRITE.
:::
---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'L_Key 와 R_Key 는 같은 MR 의 같은 키']
**실제**: 같은 MR 한 번 등록하면 둘 다 발급되지만 **의미와 검증 경로가 다름** — L_Key 는 같은 노드 안에서 sender 자신이 사용 (sg_list 의 lkey), R_Key 는 원격 노드가 RDMA WRITE/READ/ATOMIC 의 RETH/AtomicETH 에 넣어 보내는 보호 키. 또한 access flag 도 다르게 검증됨 — Local Write 권한과 Remote Write 권한은 별도. R_Key 만 노출하고 access 를 Remote Read 로만 제한할 수도 있음.<br>
**왜 헷갈리는가**: 같은 verb 호출 (`ibv_reg_mr`) 한 번에 둘 다 받는 API 모양 때문.
:::
:::danger[❓ 오해 2 — 'RDMA WRITE 의 sender 는 access flag 가 필요 없다']
**실제**: sender 의 sg_list 도 lkey + Local Read 권한이 필요 (HCA 가 읽어가야 함). RDMA READ sender 는 Local Write 가 필요 (HCA 가 받은 데이터를 local 에 쓴다). 단어 "Local" 이 같아 보여도 **operation 별로 미묘하게 다른 access** 가 요구됨.<br>
**왜 헷갈리는가**: "remote 가 쓰는 거니까 sender 는 신경 안 써도" 같은 직관.
:::
:::danger[❓ 오해 3 — 'PD 가 같으면 무조건 access 가 된다']
**실제**: PD 는 5-step 의 한 단계일 뿐. 나머지 4개 (rkey 일치, access flag, range, IOVA 변환) 가 다 통과해야 함. PD 만으로는 부족.<br>
**왜 헷갈리는가**: PD = "Protection Domain" 이 전부의 보호처럼 들림.
:::
:::danger[❓ 오해 4 — 'ODP MR 도 일반 MR 처럼 즉시 access 된다']
**실제**: ODP 는 page fault 가능 → HCA 가 PRI → OS page-in → ATS update 의 chain. latency 가 평소 µs 단위 → ms 단위로 증가 가능. retry timer 와 상호작용 주의.<br>
**왜 헷갈리는가**: "On-Demand 도 결국 페이지가 채워지면 같은 거 아닌가" 같은 단순화.
:::
:::danger[❓ 오해 5 — 'MR dereg 만 하면 메모리 즉시 회수 가능']
**실제**: in-flight DMA 가 진행 중인 MR 을 dereg 하면 R_Key 는 invalid 되지만 DMA 는 끝나야 안전. RDMA-TB 의 in-flight WR drain (§5.10) 이 이 corner case 를 검증.<br>
**왜 헷갈리는가**: dereg verb 가 즉시 반환하므로 "끝났다" 고 오인.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| `IBV_WC_LOC_PROT_ERR` | sg_list 의 lkey 가 다른 MR 의 것 또는 dereg 된 것 | sender WC + sg_list 의 lkey vs 생존 MR 들 |
| `IBV_WC_REM_ACCESS_ERR` (모든 WRITE) | rkey 또는 access flag 또는 PD | responder NAK syndrome |
| `IBV_WC_REM_ACCESS_ERR` (특정 offset 부터) | range 벗어남 (large MR 끝부분) | RETH.va + dmalen vs MR.range |
| 의도한 NAK 가 안 발생 | 5-step 검증 중 하나가 silently bypass | individual inject test 로 각 step 검증 |
| Silent corruption | 동일 IOVA 두 MR 에 매핑 | dereg 후 새 MR 의 첫 packet PA 확인 |
| TLB stale (예전 MR 의 PA 로 DMA) | dereg → reg 사이 TLB invalidate 누락 | TLB log + ATS update 시점 |
| ODP MR 에서 RC retry exhausted | page fault latency > retry timeout | retry timer 와 PRI latency 측정 |
| MR dereg 후 응용이 hang | in-flight WR drain 미완료 | outstanding WQE 카운트 |
| RDMA READ 가 `IBV_WC_LOC_PROT_ERR` | sender 의 local buf 가 Local Write 권한 없음 | sender MR access flag |
| MW invalidate 후 in-flight WRITE | corner case — implementation-defined | spec § + 사내 정책 |

---

## 7. 핵심 정리 (Key Takeaways)

- PD/MR/Key 는 RDMA 의 **address space + protection** 을 동시에 표현하는 객체.
- L_Key 와 R_Key 는 같은 등록에서 발급되지만 **검증 경로와 의미가 다름**.
- Access flag 는 작업별로 미세하게 검증됨 — Local Write vs Remote Write 분리.
- IOVA → PA 변환은 ATS/TLB/PTW 가 담당, RDMA-TB 는 이를 module-level TB 로 분해 검증.
- Memory Window 와 ODP 는 corner-case 가 많아 검증 포인트.

:::caution[실무 주의점]
- 같은 PD 안 두 MR 의 IOVA 가 겹치는 corner case: spec 은 금지, 구현은 silently 허용 후 corruption 가능 → 검증에서 명시적으로 inject 해 reject 되는지 확인.
- R_Key 를 외부에 "노출" 하는 것은 보안 책임 — RDMA spec 은 access flag 에서 제한할 뿐, key 자체는 노출 가정. 따라서 **R_Key 는 짧은 lifetime + MW 패턴이 권장**.
- PCIe ATS 가 비활성화된 환경에서는 IOMMU/SMMU(IO Memory Management Unit — 디바이스의 IOVA 를 PA 로 변환·보호하는 칩셋 측 유닛; ARM 에서는 SMMU) 가 모든 변환을 처리 → host platform 별 검증.
- ODP 와 RC retry 의 상호작용: page fault 가 길면 sender retry 가 먼저 발동 → packet duplicate 처리 필요.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — 5-step 검증 추적 (Bloom: Analyze)]
Sender 가 외부에서 _훔친_ R_Key 로 노드 B 에 RDMA WRITE 합니다. _5-step 중 어디서_ 차단되는가? 만약 어떤 step 도 차단 못 하면 어떤 단계가 _부족_ 한 것인가?

<details>
<summary>정답</summary>

- Step 1 (rkey 일치) → 통과 (정확한 rkey 라).
- Step 2 (access flag) → MR 의 Remote Write 권한이 켜져 있으면 통과.
- Step 3 (PD same) → attacker QP 와 MR 이 같은 PD 면 통과 (attacker 가 RDMA-CM 으로 같은 PD 와 합의했을 수도 있음).
- Step 4 (range) → MR base + len 범위 안에서 통과.
- Step 5 (IOVA → PA) → 통과.

즉 **5-step 다 통과 가능**. RDMA spec 의 보안은 "**R_Key 가 비밀이라는 가정**" 에 의존. R_Key 가 유출되면 5-step 으로는 안 됨 → 그래서 _Memory Window_ + _짧은 lifetime_ 정책이 권장됨.

</details>
:::
:::tip[🤔 Q2 — `WC_REM_ACCESS_ERR` 진단 (Bloom: Apply)]
Receiver B 가 _모든 RDMA WRITE_ 에 대해 `WC_REM_ACCESS_ERR` 를 NAK 로 보냅니다. 5-step 중 어디부터 의심해야 효율적인가?

<details>
<summary>정답</summary>

효율 순서:
1. **Step 2 (access flag)** — 가장 흔한 실수. MR 등록 시 `IBV_ACCESS_REMOTE_WRITE` 안 켰을 가능성. read-back 으로 첫 확인.
2. **Step 1 (rkey)** — 두 노드의 rkey 동기 실패. CM 에서 받은 값 vs sender 가 보낸 RETH.RKey.
3. **Step 3 (PD)** — QP 와 MR 가 다른 PD. 다중 PD 환경에서만 가능.
4. **Step 4 (range)** — RETH.VA + DMALen 이 MR 범위 밖. 보통 _특정 offset_ 부터만 실패.
5. **Step 5 (IOVA)** — TLB stale 또는 PTW 실패.

Step 1, 2 가 80% 의 케이스. read-back 으로 빠르게 확인.

</details>
:::
:::tip[🤔 Q3 — MR dereg 의 race (Bloom: Evaluate)]
_RDMA WRITE in-flight_ 상태에서 MR 을 dereg 하면 어떤 race 가 발생할 수 있는가? 그리고 RDMA-TB 가 이 시나리오를 반드시 검증해야 하는 이유는?

<details>
<summary>정답</summary>

Race: **R_Key 는 invalidate 됐지만 DMA 가 _이미 wire 위_ 에 있는 경우**.
- 수신 측에서 새 R_Key 로 재할당이 발생하면 _다른 MR_ 의 메모리에 DMA write 가 들어갈 수 있음 (use-after-free / aliasing).
- 또는 in-flight DMA 가 dereg 후 도착해서 _이미 회수된 메모리_ 에 corruption.

RDMA-TB 의 검증: dereg 시 in-flight WR drain (§5.10 의 Confluence id=133497307) — 모든 outstanding WR 완료 후 R_Key invalidate. 이게 _구현 책임_ 인 이유는 spec 이 명시적으로 drain 을 요구하지 않기 때문 (race 가 _silent corruption_ 으로 나타날 수 있음).

</details>
:::
### 7.2 출처

**Internal (Confluence)**
- `[RDMA] MMU Basic` (id=992346170) — IOVA → PA 변환의 ATS/PTW/TLB
- `[RDMA] Memory Window (MW)` (id=989561005) — Type 1 vs Type 2 (DH)
- `[RDMA] Transfer functions` (id=992804897) — sg_list 처리
- `RDMA atomic operation` (id=93880360) — CAS/FAA
- `Local/Remote Invalidation` (id=155844886) — invalidate semantics
- `Memory Placement Extensions (MPE)` (id=217808945) — FLUSH/ATOMIC WRITE
- `Large MR support` (id=93814912), `In-flight WR management` (id=133497307) — corner case

**External**
- IBTA Spec 1.7, §10.6 Memory Management
- IBTA Annex A19 — Memory Placement Extensions
- PCIe Spec — ATS (Address Translation Service)

---

## 다음 모듈

→ [Module 06 — Data Path Operations](../06_data_path/): 등록된 메모리를 SEND/WRITE/READ/ATOMIC opcode 가 어떻게 사용하는지.

[퀴즈 풀어보기 →](../quiz/05_memory_model_quiz/)
