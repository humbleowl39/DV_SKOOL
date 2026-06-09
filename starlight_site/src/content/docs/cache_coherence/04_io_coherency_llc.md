---
title: "Module 04 — IO-Coherency & LLC as Point of Coherence"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** IO-coherency(one-way coherency)가 DMA/NIC 같은 비캐싱 마스터의 통합을 어떻게 단순화하는지 설명할 수 있다.
- **Differentiate** 양방향 full coherency(CPU↔GPU)와 one-way IO-coherency(NIC/DMA)를 sharer·snoop 방향 기준으로 구분할 수 있다.
- **Explain** LLC가 Point of Coherence(PoC)로서, snoop filter와 inclusive back-invalidation으로 수직(hierarchical) coherence를 유지하는 방식을 설명할 수 있다.
- **Implement** IO-coherent DMA/NIC 시나리오와 LLC back-invalidation을 검증 시퀀스/체커로 구성하고, DV가 잡아야 할 corner case를 식별할 수 있다.
:::
:::note[사전 지식]
- [Module 02 — Snooping & MESI/MOESI](../02_snooping_mesi_moesi/), [Module 03 — Directory](../03_directory_scalability/)
- (선택) [AMBA AXI/ACE](../../amba_protocols/02_axi/), [UVM scoreboard](../../uvm/05_tlm_scoreboard_coverage/)
:::
---

## 1. Why care? — NIC가 cache flush 없이 최신 패킷을 읽어야 한다

### 1.1 시나리오 — NIC가 stale 패킷을 전송하던 옛날

**IO-coherency**(DMA·NIC 같은 캐시 없는 장치가 메모리를 접근할 때, 인터커넥트가 CPU 캐시를 대신 snoop해 최신값을 반영해 주는 단방향 coherence)가 없던 시절의 고전 버그입니다. CPU가 네트워크 패킷을 *자기 캐시에* 준비하고 **NIC**(Network Interface Card — 네트워크 송수신을 담당하는 장치)에 "전송하라"고 명령합니다. NIC는 main **DDR**(DRAM의 한 종류로, 여기서는 주 메모리를 가리킴)에서 패킷을 읽는데, 수정된 패킷은 여전히 CPU 캐시에 dirty(캐시본이 메모리보다 최신인 상태)로 남아 있으므로 NIC는 *stale 데이터*(낡아서 더 이상 최신이 아닌 값)를 전송합니다. 이를 막으려고 소프트웨어 엔지니어는 NIC를 트리거하기 *전에* 값비싼 cache flush/clean 명령을 직접 실행해야 했습니다.

**IO-coherent 해법**은 이 부담을 하드웨어로 옮깁니다. NIC를 시스템 인터커넥트의 *IO-coherent 포트*에 연결하면, NIC가 main memory로 read를 보낼 때 인터커넥트가 자동으로 CPU 캐시를 snoop합니다. CPU가 더 최신 패킷을 들고 있으면 하드웨어가 read를 가로채 dirty 데이터를 CPU 캐시에서 꺼내 NIC로 전달합니다. 그 결과 디바이스 드라이버는 cache maintenance(소프트웨어가 직접 캐시를 flush/clean/invalidate해 메모리와 맞추는 관리 작업)를 더 이상 관리할 필요가 없어지고, 성능도 좋아지며 드라이버 코드도 단순해집니다.

검증 엔지니어에게 이건 매일의 일입니다 — DMA/NIC가 끼는 **SoC**(System on Chip — CPU·캐시·가속기·인터커넥트를 한 칩에 집적한 시스템)에서 "패킷이 깨져 나간다"의 1순위 의심은 IO-coherency 경로의 snoop 누락입니다.

---

## 2. Intuition — 단방향 알림, 한 장 그림

:::tip[💡 한 줄 비유]
**Full coherency** ≈ 두 사람이 *서로의* 메모를 항상 동기화(양방향).<br>
**IO-coherency (one-way)** ≈ NIC/DMA는 캐시가 없어 *남이 들고 있을지 모를 최신본을 받기만* 하면 됨. 그래서 인터커넥트가 CPU 캐시를 대신 snoop해 최신본을 끌어다 줌 — 한 방향.
:::
### 한 장 그림 — IO-coherent read가 CPU 캐시를 snoop

```d2
direction: down

NIC: "**NIC / DMA (비캐싱 마스터)**\nread packet @addr"
IC: "**System Interconnect**\nIO-coherent port" {
  style.fill: "#fff4e5"
}
CPU: "**CPU cache**\npacket @addr: M (dirty)"
DDR: "**Main Memory (DDR)**\nstale packet"

NIC -> IC: "① read request"
IC -> CPU: "② snoop CPU cache"
CPU -> IC: "③ dirty data forward"
IC -> NIC: "④ 최신 packet 전달 (DDR 우회)"
IC -> DDR: "CPU에 없을 때만 fetch" { style.stroke-dash: 4 }
```

### 왜 이 디자인인가 — Design rationale

IO-coherency가 *one-way*(한 방향)인 이유는 비캐싱 마스터(자체 캐시가 없는 버스 주체 — DMA·NIC처럼 데이터를 들고 있지 않고 그때그때 메모리만 읽고 쓰는 장치)의 특성에서 나옵니다. NIC/DMA는 자체 캐시를 두지 않으므로, *다른 캐시가 그들의 데이터를 snoop할* 필요가 없습니다(그들은 보유하지 않으니까). 필요한 건 단 하나 — 그들이 메모리를 읽거나 쓸 때, *CPU 캐시의 최신본을 반영*하는 것입니다. 그래서 snoop이 CPU→디바이스 방향으로만 흐릅니다.

이 비대칭성 덕분에 full coherency(서로의 캐시를 양방향으로 snoop하는 완전 coherence)보다 구현이 가볍고, 비캐싱 가속기를 SoC에 통합하는 비용이 낮아집니다. DMA/NIC/**fixed-function 가속기**(한 가지 고정된 기능만 하드웨어로 수행하는 가속기, 예: 영상 코덱·암호 엔진) 통합에 IO-coherency가 표준이 된 이유입니다.

---

## 3. 작은 예 — IO-coherent DMA read와 LLC back-invalidation

두 가지 핵심 시나리오를 봅니다: (A) IO-coherent DMA read가 CPU dirty를 끌어오는 경로, (B) inclusive LLC가 가득 차 back-invalidation을 일으키는 경로.

### 단계별 다이어그램 — (A) IO-coherent DMA read

```d2
direction: down

A1: "**① DMA read @X → 인터커넥트**\nIO-coherent port 진입" { style.fill: "#e8f0fe" }
A2: "**② 인터커넥트가 PoC(LLC) directory 조회**\nX의 owner = CPU(L1, dirty)" { style.fill: "#fff4e5" }
A3: "**③ CPU L1 snoop → dirty 추출**\nDDR 우회" { style.fill: "#e6f4ea" }
A4: "**④ 최신 X를 DMA로 전달**\n드라이버는 flush 불필요"
A1 -> A2 -> A3 -> A4
```

### 단계별 다이어그램 — (B) inclusive LLC back-invalidation

```d2
direction: down

B1: "**① LLC full, 새 line 위해 victim 선택**\nvictim line Y가 상위 L1/L2에도 존재" { style.fill: "#e8f0fe" }
B2: "**② inclusive 정책: 상위가 가진 line은\n   LLC에도 반드시 존재해야**\n→ LLC가 Y를 그냥 못 버림" { style.fill: "#fff4e5" }
B3: "**③ Back-Invalidation 발행**\nL1/L2에 'Y 버려라' 명령\n(dirty면 write-back 동반)" { style.fill: "#fce8e6" }
B4: "**④ 상위 캐시 Y 무효화 완료 후\n   LLC가 victim 교체**\norphan(고아) line 방지"
B1 -> B2 -> B3 -> B4
```

### 단계별 의미

| 시나리오 | 핵심 동작 | 왜 |
|---|---|---|
| (A) DMA read | 인터커넥트가 CPU 캐시 snoop → dirty 추출 → DDR 우회 | 드라이버의 cache flush 제거 (출처 §3) |
| (B) back-invalidation | inclusive LLC eviction 시 상위 L1/L2 강제 무효화 | inclusion 유지, orphan line 방지 (출처 §4) |

:::note[여기서 잡아야 할 핵심]
**inclusive**(상위 캐시에 있는 line은 하위 LLC에도 반드시 있어야 한다는 포함 정책) LLC는 "상위 캐시가 가진 line은 LLC에도 있어야 한다"는 invariant(항상 지켜져야 하는 불변 규칙)를 지킵니다. 그래서 LLC가 victim(자리를 비우려고 쫓아낼 대상으로 고른 line)을 버릴 때 그냥 못 버리고, 상위 캐시에 **back-invalidation**(LLC가 evict하는 line을 상위 L1/L2도 함께 버리게 강제하는 무효화)을 보내 해당 사본을 *함께* 버리게 합니다. 이걸 빼먹으면 상위 캐시에 LLC가 추적하지 못하는 **orphan line**(LLC가 더 이상 추적하지 못한 채 상위 캐시에 남은 사본)이 생기고, 그 line에 대한 coherence가 깨집니다.
:::
---

## 4. 일반화 — full vs IO coherency, LLC의 기원·inclusion·세 역할

### 4.1 Full coherency vs IO-coherency

| 축 | Full Coherency | IO-Coherency (one-way) |
|---|---|---|
| 대상 | peer CPU, GPGPU (캐싱 마스터) | DMA, NIC, fixed-function 가속기 (비캐싱) |
| snoop 방향 | 양방향 | 단방향 (CPU→디바이스만 snoop) |
| 디바이스 캐시 | 있음 | 없음 |
| 소프트웨어 부담 | barrier 위주 | cache flush 불필요 (HW가 처리) |
| 비용 | 높음 | 낮음 (통합 단순) |

### 4.2 LLC는 왜 생겼나 — off-chip 벽과 공유의 경제학

LLC(Last Level Cache)를 "그냥 제일 큰 캐시" 로만 보면 그 존재 이유를 놓칩니다. LLC는 세 가지 압력이 겹친 지점에서 태어났습니다.

**(1) off-chip DRAM 대역폭·latency 벽.** CPU 코어의 성능은 수십 년간 가파르게 올랐지만, off-chip DRAM의 latency는 그만큼 줄지 않았습니다 — DRAM 접근은 코어 입장에서 수백 cycle의 stall입니다. 게다가 die 밖으로 나가는 메모리 핀과 채널의 대역폭은 물리적으로 제한됩니다. 모든 L2 miss가 곧장 DRAM으로 직행하면, 이 좁고 느린 off-chip 경로가 시스템 전체의 병목이 됩니다. die *안에* 한 단계 더 큰 캐시를 두어 L2 miss의 상당수를 on-chip에서 흡수하면, 느린 DRAM 왕복과 귀한 off-chip 대역폭 소비를 모두 줄일 수 있습니다. LLC는 본질적으로 "off-chip 벽 앞에 세운 마지막 on-chip 방어선" 입니다.

**(2) capacity vs latency tradeoff.** 캐시는 클수록 더 많은 데이터를 담아 miss를 줄이지만(capacity↑), 크면 물리적으로 멀고 느려집니다(latency↑) — 둘은 근본적으로 상충합니다. 그래서 단일 거대 캐시 대신 *계층* 을 둡니다: 코어 옆에 작고 빠른 L1, 그 뒤에 중간 L2, 그리고 die 차원에서 크지만 상대적으로 느린 LLC. LLC는 이 계층의 맨 끝에서 "DRAM보다는 훨씬 빠르고, L1/L2보다는 훨씬 큰" 자리를 메웁니다 — capacity와 latency 사이의 마지막 절충점입니다.

**(3) cross-core sharing.** 코어가 여러 개면, 한 코어가 끌어온 데이터를 다른 코어도 곧 쓰는 경우가 많습니다(공유 라이브러리, 공유 자료구조). 각 코어 전용 L2에만 데이터가 있으면 코어 간 공유 때마다 cache-to-cache 전송이나 DRAM 왕복이 필요하지만, 코어들이 *공유하는* LLC에 그 데이터가 있으면 한 번 채워 둔 것을 여러 코어가 빠르게 재사용합니다. 즉 LLC는 단일 코어의 miss 흡수를 넘어, *코어 간 공유 데이터의 공통 저장소* 역할도 합니다 — 그래서 coherence의 자연스러운 중앙 허브가 됩니다.

:::note[LLC vs SLC — 용어 정리]
**LLC(Last Level Cache)** 는 캐시 *계층* 상의 위치를 가리키는 상대적 용어입니다 — "코어에서 가장 먼, 메모리 직전의 마지막 캐시 레벨". 3-레벨 구조면 보통 L3가 LLC입니다.

**SLC(System Level Cache)** 는 CPU 캐시 계층 *밖*, 시스템 인터커넥트 수준에 놓인 캐시를 강조하는 용어입니다 — CPU뿐 아니라 GPU·DMA·기타 IP까지 *모든* 시스템 master가 공유하는 캐시라는 관점입니다. 모바일/SoC 맥락에서 자주 쓰입니다.

둘은 물리적으로 같은 구조를 가리키는 경우가 많지만 강조점이 다릅니다 — LLC는 "CPU 캐시 계층의 끝", SLC는 "시스템 전체가 공유하는 캐시". 이 모듈에서 LLC/SLC를 함께 적는 것은 이 둘이 흔히 같은 블록을 지칭하기 때문입니다. (구체 명칭·범위는 SoC 구현마다 다름.)
:::

### 4.2.1 Inclusion policy — inclusive / exclusive / NINE

LLC와 상위 캐시(L1/L2)가 *같은 데이터를 중복 보유하는가* 를 규정하는 것이 **inclusion policy** 입니다. 이 선택이 snoop filter의 정확도, 중복 capacity, back-invalidation 부담을 모두 좌우합니다.

| 정책 | 정의 | snoop filter | 중복 capacity | back-invalidation |
|---|---|---|---|---|
| **Inclusive** (strictly inclusive) | 상위 캐시가 가진 line은 LLC에도 *반드시* 존재 | LLC 태그가 곧 directory — 상위 보유 여부를 LLC 한 곳에서 알 수 있어 정확 | 큼 — 같은 line이 L1/L2와 LLC에 중복 | **필요** — LLC eviction 시 상위 사본도 강제 무효화 |
| **Exclusive** | 한 line은 상위 *또는* LLC 중 한 곳에만 존재(중복 금지) | LLC에 없는 line도 상위엔 있을 수 있어 별도 directory 필요 | 없음 — 유효 캐시 용량이 합집합으로 최대화 | 불필요 — LLC eviction이 상위 사본을 함의하지 않음. 대신 fill/victim 이동 로직이 복잡 |
| **NINE** (Non-Inclusive Non-Exclusive) | inclusion을 *강제도 금지도 안 함* — 우연히 중복될 수도, 아닐 수도 | LLC 태그만으로는 상위 보유를 확신 못 해 보통 별도 snoop filter를 둠 | 일부 중복 가능(보장 없음) | 강제 back-invalidation은 없으나, snoop filter 정확성 유지 로직이 별도로 필요 |

각 정책의 결과를 인과로 풀면:

- **Inclusive → snoop filter 정확 + back-invalidation 부담.** LLC가 상위의 superset이므로, "이 line을 상위 캐시가 갖고 있나?" 를 LLC 태그만 보고 정확히 답할 수 있습니다(LLC에 없으면 상위에도 없음). snoop filter를 공짜로 얻는 셈입니다. *그 대가* 가 back-invalidation입니다 — LLC가 어떤 line을 evict하려면, 그 line을 상위가 들고 있을 수 있으므로 inclusion invariant를 지키기 위해 상위에 "그 line 버려라" 를 강제해야 합니다. 또한 같은 line을 두 곳에 중복 보관하니 유효 캐시 용량이 줄어듭니다.
- **Exclusive → capacity 이득 + fill/victim 복잡.** 중복을 금지하므로 L1+L2+LLC의 유효 용량이 거의 합집합이 되어 capacity가 큽니다. back-invalidation도 불필요합니다(LLC가 그 line을 갖고 있다는 것은 상위가 *안* 갖고 있다는 뜻이므로). *대가* 는 데이터 이동 로직입니다 — 상위 캐시가 LLC에서 line을 가져오면 LLC에서 그 line을 빼야 하고, 상위에서 evict된 line은 LLC로 내려보내야 합니다(victim 이동). 이 fill/victim 흐름이 복잡하고, snoop filter도 LLC 태그로는 부족해 별도 구조가 필요합니다.
- **NINE → 절충.** inclusion을 강제하지 않으니 inclusive의 강제 back-invalidation 부담은 없습니다. 하지만 LLC 태그가 상위 보유를 보장하지 못하므로, 대규모 시스템에서는 보통 별도 snoop filter를 둬서 정확도를 챙깁니다. inclusive의 단순한 directory도, exclusive의 최대 capacity도 아닌 중간 지점입니다.

> 핵심 인과 한 줄: **back-invalidation은 inclusion policy의 직접 산물** 입니다 — strictly inclusive이기 *때문에* LLC eviction이 상위 무효화를 강제합니다. exclusive였다면 그 강제가 없고, NINE이면 강제 back-invalidation 대신 snoop filter 정확성 유지로 문제가 옮겨갑니다. 본문 §3 (B)의 back-invalidation 시나리오는 "inclusive를 택했을 때 치르는 비용" 으로 이해해야 합니다.

### 4.3 LLC의 세 가지 coherence 역할

지금까지 coherence를 *수평*(peer-to-peer)으로 봤다면, LLC/SLC는 **수직(hierarchical) coherence**를 도입해 시스템의 중앙 동기화 허브가 됩니다. LLC는 단순한 대용량 메모리 풀이 아니라 능동적 참여자입니다.

```d2
direction: down

LLC: "**Last Level Cache (LLC / SLC)**" {
  R1: "**① Snoop Filter (Directory)**\n어느 상위 캐시가 어느 line 보유 추적\n→ targeted snoop"
  R2: "**② Back-Invalidation (Inclusive)**\nLLC eviction 시 상위 L1/L2 강제 무효화\n→ orphan 방지"
  R3: "**③ Point of Coherence (PoC)**\nIO/heterogeneous 트래픽의 최종 합류점\n→ 모든 observer 동일 데이터 보장 후 DRAM commit"
}
```

| 역할 | 무엇을 | 왜 (출처 §4) |
|---|---|---|
| Snoop Filter (Directory) | 상위 캐시 sharer 추적 → targeted snoop | broadcast 트래픽 절감 |
| Back-Invalidation | inclusive eviction 시 상위 무효화 | inclusion 유지, orphan 방지 |
| Point of Coherence | IO/heterogeneous 트래픽의 최종 junction | DRAM commit 전 모든 observer가 동일값 보장 |

### 4.4 Point of Coherence (PoC)의 의미 — 그리고 PoU와의 구분

PoC는 모든 메모리 observer(메모리를 읽고 쓰는 주체 — CPU, GPU, DMA 등)가 *같은 갱신 데이터를 보는 것이 보장되는 물리적 지점*입니다. IO-coherent 트래픽과 heterogeneous(서로 다른 종류의 처리 요소가 섞인) 트랜잭션에서 LLC가 흔히 이 PoC 역할을 맡아, 트랜잭션이 외부 DRAM에 영구 commit(메모리에 최종 확정 반영)되기 *전에* 모든 관찰자의 뷰를 일치시킵니다. DMA read가 CPU dirty를 끌어오는 본문 §3 (A) 시나리오의 동작이 *어디서* 일어나는가에 대한 답이 바로 PoC=LLC입니다.

:::note[PoC vs PoU — 두 "통합 지점" 은 무엇이 다른가]
coherence/cache maintenance 논의에는 비슷해 보이지만 의미가 다른 두 지점이 있습니다.

- **PoC (Point of Coherence):** 그 지점에서 보면 *모든 observer*(여러 코어, GPU, DMA 등)가 한 주소에 대해 같은 값을 보도록 보장되는 곳. "시스템 전체가 일관된 뷰를 갖는 합류점" 으로, 위에서 본 LLC가 흔히 이 역할을 합니다.
- **PoU (Point of Unification):** *한 관찰자(또는 한 코어)* 의 관점에서, 그 코어의 instruction cache·data cache·(있다면) 변환 테이블 walk가 *같은 사본* 을 보게 되는 지점. 이름 그대로 한 agent 내부의 여러 접근 경로가 "하나로 합쳐지는" 레벨입니다.

왜 둘을 구분할까요? cache maintenance가 노리는 대상이 다르기 때문입니다. 대표적으로 self-modifying code(코드를 데이터로 써 놓고 그 자리를 실행)에서는, 방금 *data 경로로 쓴* 값을 같은 코어의 *instruction 경로* 가 봐야 합니다 — 이건 시스템 전체의 일관성(PoC)이 아니라 한 코어 안에서 I-side와 D-side가 합쳐지는 PoU까지만 데이터를 밀어 내리면 충분합니다. 반대로 DMA/다른 코어에까지 데이터를 보이게 하려면 PoU로는 부족하고 *PoC* 까지 내려야 합니다. 즉 "어디까지 flush/clean해야 하는가" 의 답이 PoU냐 PoC냐에 따라 갈리고, 그래서 cache maintenance 연산은 보통 "to PoU" 와 "to PoC" 변형을 따로 둡니다.

검증 관점에서도 둘은 다른 질문입니다 — PoC 검증은 "모든 observer가 같은 값을 보는가(멀티 master coherence)", PoU 검증은 "한 코어의 I/D(및 table walk)가 같은 값을 보는가" 입니다. 이 코스의 주 범위는 멀티 master coherence라 PoC가 중심이고, PoU는 여기서는 개념 수준으로만 짚습니다. (구체 정의·레벨은 아키텍처 사양 의존.)
:::

---

## 5. 디테일 — DV 관점: 무엇을 어떻게 검증하나

IO-coherency와 LLC PoC를 검증하는 환경은 [UVM(UVM — SystemVerilog 검증 환경을 짜는 표준 방법론) scoreboard 패턴](../../uvm/05_tlm_scoreboard_coverage/)을 그대로 활용하되, **reference model**(설계가 내야 할 "정답"을 따로 계산해 두는 소프트웨어 모델)이 *coherence-aware*여야 합니다. 핵심 아이디어는 "어떤 observer가 어느 시점에 무엇을 봐야 하는가"를 reference가 알고, 실제 관찰값과 비교하는 것입니다. 이때 **scoreboard**(설계의 실제 출력과 reference의 기대값을 비교해 일치 여부를 판정하는 검증 컴포넌트)가 둘을 맞대 봅니다.

가장 중요한 **corner case**(드물게만 발생해 놓치기 쉬운 경계 상황)는 **race**(둘 이상의 동작이 거의 동시에 일어나 결과 순서가 불확정인 경쟁 상황)입니다. CPU가 dirty line을 들고 있는 *바로 그 순간* DMA가 같은 주소를 read하면, snoop이 dirty를 끌어와야 합니다. 반대로 DMA write와 CPU read가 겹치면 PoC에서 순서가 결정되어야 합니다. 이런 동시성 race는 directed sequence(특정 상황을 노려 일부러 만들어 내는 시험 자극)로 *의도적으로 겹치게* 만들고, scoreboard가 "DMA가 받은 값 == CPU의 최신 dirty 값"을 확인해야 합니다.

back-invalidation은 별도 체커를 요구합니다. inclusive LLC에서 victim eviction이 일어날 때마다 상위 L1/L2의 해당 line이 *실제로* 무효화되는지, dirty victim이면 write-back이 동반되는지를 추적해야 합니다. 이를 빠뜨리면 orphan line이 생겨 *나중에* coherence 버그로 터지는데, 발생 시점과 증상 시점이 멀어 디버그가 어렵습니다 (추론: 검증 전략은 일반 DV 관용).

```systemverilog
// IO-coherency scoreboard 골격 — DMA가 받은 값과 CPU dirty 기대값 비교
// (UVM Module 05의 dual-port scoreboard 패턴 차용)
class iocoh_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(iocoh_scoreboard)

  // CPU 캐시 상태를 추적하는 coherence-aware reference model
  // 키 = address, 값 = {최신 데이터, dirty 여부, owner}
  cpu_cache_model_t ref_model;   // 사용자 정의 (추론)

  uvm_tlm_analysis_fifo #(mem_txn) dma_read_fifo;   // DMA read 결과 (actual)

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    dma_read_fifo = new("dma_read_fifo", this);
  endfunction

  task run_phase(uvm_phase phase);
    mem_txn dma_rd;
    forever begin
      dma_read_fifo.get(dma_rd);                       // DMA가 실제로 받은 값
      // reference: 해당 주소를 CPU가 dirty로 들고 있었다면 그 값이 정답
      if (!ref_model.lookup(dma_rd.addr).compare(dma_rd.data))
        `uvm_error("IOCOH",
          $sformatf("Stale data to DMA @%0h: got %0h, expected latest %0h",
                    dma_rd.addr, dma_rd.data, ref_model.lookup(dma_rd.addr).data))
    end
  endtask
endclass
```

| DV 검증 항목 | 무엇을 확인 | 어떻게 |
|---|---|---|
| IO-coherent read 정확성 | DMA가 CPU dirty 최신값을 받는가 | coherence-aware reference vs DMA 관찰값 |
| CPU-dirty / DMA-read race | 동시 접근 시 snoop이 dirty 끌어오는가 | directed overlap sequence + scoreboard |
| back-invalidation | LLC eviction 시 상위 무효화 + dirty write-back | victim eviction 추적 체커 |
| PoC 순서 | DMA write/CPU read의 commit 순서 | 순서 모델 + 관찰 비교 |
| orphan line | inclusion invariant 유지 | 상위 캐시 line ⊆ LLC line 검사 (추론) |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'IO-coherency면 디바이스도 양방향으로 snoop된다']
**실제**: IO-coherency는 *one-way* — 비캐싱 마스터는 자체 캐시가 없어 *남이 그들을 snoop할* 필요가 없습니다. snoop은 CPU 캐시 방향으로만 흐릅니다.<br>
**왜 헷갈리는가**: "coherent = 양방향"이라는 full coherency 경험의 일반화.
:::
:::danger[❓ 오해 2 — 'IO-coherent면 드라이버가 항상 cache flush를 안 해도 된다']
**실제**: IO-coherent *포트*에 연결되어 하드웨어 snoop이 동작할 때만 그렇습니다. 비-coherent 포트나 device-side 버퍼가 끼면 여전히 maintenance가 필요할 수 있습니다.<br>
**왜 헷갈리는가**: 기능과 연결 토폴로지를 분리하지 않음.
:::
:::danger[❓ 오해 3 — 'inclusive LLC eviction은 그냥 LLC만 비우면 된다']
**실제**: inclusive 정책에서 상위 캐시가 가진 line은 LLC에도 있어야 하므로, LLC가 그 line을 버리려면 *반드시* back-invalidation으로 상위 사본도 함께 버려야 합니다. 안 그러면 orphan line → coherence 붕괴.<br>
**왜 헷갈리는가**: eviction을 "내 레벨만의 일"로 봄. inclusive는 수직 invariant.
:::
:::danger[❓ 오해 4 — 'LLC는 그냥 큰 캐시일 뿐 coherence와 무관']
**실제**: LLC는 snoop filter(directory) + back-invalidation + PoC라는 세 가지 *능동적* coherence 역할을 수행합니다. 단순 메모리 풀이 아닙니다.<br>
**왜 헷갈리는가**: "캐시 = 용량/속도"라는 단일 관점.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| DMA/NIC가 stale 데이터 전송 | IO-coherent read의 CPU-snoop 누락 또는 비-coherent 포트 연결 | snoop 발행 여부, 디바이스 포트 coherency 속성 |
| DMA-read와 CPU-write race에서 간헐 불일치 | PoC 순서 결정 버그 | 동시 접근 타이밍, PoC commit 순서 로그 |
| 한참 뒤에 터지는 coherence 버그 | inclusive LLC back-invalidation 누락 → orphan line | victim eviction 시 상위 무효화 발행 여부 |
| LLC eviction 후 데이터 손실 | dirty victim의 write-back 누락 | eviction 경로의 write-back 동반 여부 |
| heterogeneous(GPU/DMA) read가 옛 값 | PoC(LLC)에서 observer 뷰 미일치 | PoC commit 전 snoop 완료 여부 |

---

## 7. 핵심 정리 (Key Takeaways)

- **IO-coherency = one-way**: NIC/DMA 같은 비캐싱 마스터가 메모리를 접근할 때 인터커넥트가 CPU 캐시를 자동 snoop해 최신본을 전달 → 드라이버의 cache flush 제거 (출처 §3).
- **full vs IO**: full은 양방향(peer CPU/GPU), IO는 단방향(디바이스는 캐시 없으니 snoop 대상 아님) → 통합 비용 낮음.
- **LLC의 세 역할**: ① snoop filter(directory)로 targeted snoop, ② inclusive back-invalidation으로 orphan 방지, ③ Point of Coherence로 DRAM commit 전 모든 observer 뷰 일치 (출처 §4).
- **back-invalidation**: inclusive LLC eviction 시 상위 L1/L2를 강제 무효화(+dirty write-back). 빠뜨리면 orphan line → 지연된 coherence 버그.
- **DV 관점**: coherence-aware reference model + dual-port scoreboard로 "DMA 관찰값 == CPU 최신 dirty" 검증, race를 directed로 의도 생성, back-invalidation은 별도 체커.

:::caution[실무 주의점]
- IO-coherency 버그의 1순위는 *snoop 누락* — "DMA가 stale" 증상은 거의 항상 여기.
- back-invalidation 누락은 *발생 시점과 증상 시점이 멀어* 가장 디버그하기 어려운 부류 — eviction 경로를 항상 체커로 감시.
- coherence checker(단일 line)와 consistency checker(멀티-주소 순서)는 별개 — Module 01의 경계를 잊지 말 것.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — one-way 이유 (Bloom: Analyze)]
NIC가 IO-coherent 포트에 연결되어 있다. 왜 인터커넥트는 CPU→NIC 방향으로만 snoop하고, NIC→CPU 방향 snoop은 두지 않는가?
<details>
<summary>정답</summary>

NIC는 비캐싱 마스터로 자체 캐시가 없습니다. 따라서 *다른 마스터가 NIC의 사본을 찾으러 snoop할* 일이 없습니다 — NIC는 데이터를 보유하지 않으니까요. 필요한 보장은 단 하나, NIC가 메모리를 읽을 때 CPU 캐시의 최신 dirty본을 반영하는 것뿐입니다. 그래서 snoop은 CPU 방향으로만 흐르는 one-way가 됩니다.
</details>
:::
:::tip[🤔 Q2 — back-invalidation 검증 (Bloom: Evaluate)]
inclusive LLC를 검증할 때, back-invalidation 체커를 빠뜨리면 어떤 종류의 버그가 silent하게 통과하며, 왜 디버그가 특히 어려운가?
<details>
<summary>정답</summary>

LLC가 victim line을 evict하면서 상위 L1/L2의 사본을 무효화하지 않으면 **orphan line**(LLC가 추적 못 하는 상위 사본)이 생깁니다. 이 line은 directory에서 빠져 이후 그 주소에 대한 무효화/공급이 누락되어 SWMR이 깨집니다. 디버그가 어려운 이유는 *eviction이 일어난 시점*과 *coherence 버그가 증상으로 터지는 시점*이 멀리 떨어져 있어, 증상 지점만 봐서는 원인(과거의 eviction)을 찾기 어렵기 때문입니다. 그래서 eviction 경로 자체를 체커로 상시 감시해야 합니다.
</details>
:::
### 7.2 출처

**External**
- ARM AMBA AXI/ACE & CHI Architecture Specification — IO-coherent port, PoC 정의
- *A Primer on Memory Consistency and Cache Coherence* — inclusion / hierarchical coherence

---

## 다음 단계

이 코스의 마지막 모듈입니다. 개념을 다지려면 [용어집](../glossary/)에서 SWMR·MOESI·directory·PoC 정의를 다시 확인하고, [퀴즈](../quiz/)로 네 모듈 전체를 점검하세요. 신호 단위로 더 파고들고 싶다면 [AMBA AXI/ACE 모듈](../../amba_protocols/02_axi/)로, 검증 환경 구축은 [UVM scoreboard/coverage 모듈](../../uvm/05_tlm_scoreboard_coverage/)로 이어집니다.

[퀴즈 풀어보기 →](../quiz/04_io_coherency_llc_quiz/)
