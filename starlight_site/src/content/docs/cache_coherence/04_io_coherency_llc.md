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

IO-coherency가 없던 시절의 고전 버그입니다. CPU가 네트워크 패킷을 *자기 캐시에* 준비하고 NIC에 "전송하라"고 명령합니다. NIC는 main DDR에서 패킷을 읽는데, 수정된 패킷은 여전히 CPU 캐시에 dirty로 남아 있으므로 NIC는 *stale 데이터*를 전송합니다. 이를 막으려고 소프트웨어 엔지니어는 NIC를 트리거하기 *전에* 값비싼 cache flush/clean 명령을 직접 실행해야 했습니다 (출처: HDG §3).

**IO-coherent 해법**은 이 부담을 하드웨어로 옮깁니다. NIC를 시스템 인터커넥트의 *IO-coherent 포트*에 연결하면, NIC가 main memory로 read를 보낼 때 인터커넥트가 자동으로 CPU 캐시를 snoop합니다. CPU가 더 최신 패킷을 들고 있으면 하드웨어가 read를 가로채 dirty 데이터를 CPU 캐시에서 꺼내 NIC로 전달합니다. 그 결과 디바이스 드라이버는 cache maintenance를 더 이상 관리할 필요가 없어지고, 성능도 좋아지며 드라이버 코드도 단순해집니다 (출처: HDG §3).

검증 엔지니어에게 이건 매일의 일입니다 — DMA/NIC가 끼는 SoC에서 "패킷이 깨져 나간다"의 1순위 의심은 IO-coherency 경로의 snoop 누락입니다.

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

IO-coherency가 *one-way*인 이유는 비캐싱 마스터의 특성에서 나옵니다. NIC/DMA는 자체 캐시를 두지 않으므로, *다른 캐시가 그들의 데이터를 snoop할* 필요가 없습니다(그들은 보유하지 않으니까). 필요한 건 단 하나 — 그들이 메모리를 읽거나 쓸 때, *CPU 캐시의 최신본을 반영*하는 것입니다. 그래서 snoop이 CPU→디바이스 방향으로만 흐릅니다 (출처: HDG §3; 비대칭성은 추론).

이 비대칭성 덕분에 full coherency보다 구현이 가볍고, 비캐싱 가속기를 SoC에 통합하는 비용이 낮아집니다. DMA/NIC/fixed-function 가속기 통합에 IO-coherency가 표준이 된 이유입니다.

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
inclusive LLC는 "상위 캐시가 가진 line은 LLC에도 있어야 한다"는 invariant를 지킵니다. 그래서 LLC가 victim을 버릴 때 그냥 못 버리고, 상위 캐시에 **back-invalidation**을 보내 해당 사본을 *함께* 버리게 합니다. 이걸 빼먹으면 상위 캐시에 LLC가 추적하지 못하는 **orphan line**이 생기고, 그 line에 대한 coherence가 깨집니다 (출처: HDG §4).
:::
---

## 4. 일반화 — full vs IO coherency, LLC의 세 역할

### 4.1 Full coherency vs IO-coherency

| 축 | Full Coherency | IO-Coherency (one-way) |
|---|---|---|
| 대상 | peer CPU, GPGPU (캐싱 마스터) | DMA, NIC, fixed-function 가속기 (비캐싱) |
| snoop 방향 | 양방향 | 단방향 (CPU→디바이스만 snoop) |
| 디바이스 캐시 | 있음 | 없음 |
| 소프트웨어 부담 | barrier 위주 | cache flush 불필요 (HW가 처리) |
| 비용 | 높음 | 낮음 (통합 단순) |

### 4.2 LLC의 세 가지 coherence 역할

지금까지 coherence를 *수평*(peer-to-peer)으로 봤다면, LLC/SLC는 **수직(hierarchical) coherence**를 도입해 시스템의 중앙 동기화 허브가 됩니다 (출처: HDG §4). LLC는 단순한 대용량 메모리 풀이 아니라 능동적 참여자입니다.

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

### 4.3 Point of Coherence (PoC)의 의미

PoC는 모든 메모리 observer(CPU, GPU, DMA)가 *같은 갱신 데이터를 보는 것이 보장되는 물리적 지점*입니다. IO-coherent 트래픽과 heterogeneous 트랜잭션에서 LLC가 흔히 이 PoC 역할을 맡아, 트랜잭션이 외부 DRAM에 영구 commit되기 *전에* 모든 관찰자의 뷰를 일치시킵니다 (출처: HDG §4). DMA read가 CPU dirty를 끌어오는 §3.1의 동작이 *어디서* 일어나는가에 대한 답이 바로 PoC=LLC입니다.

---

## 5. 디테일 — DV 관점: 무엇을 어떻게 검증하나

IO-coherency와 LLC PoC를 검증하는 환경은 [UVM scoreboard 패턴](../../uvm/05_tlm_scoreboard_coverage/)을 그대로 활용하되, reference model이 *coherence-aware*여야 합니다. 핵심 아이디어는 "어떤 observer가 어느 시점에 무엇을 봐야 하는가"를 reference가 알고, 실제 관찰값과 비교하는 것입니다.

가장 중요한 corner case는 **race**입니다. CPU가 dirty line을 들고 있는 *바로 그 순간* DMA가 같은 주소를 read하면, snoop이 dirty를 끌어와야 합니다. 반대로 DMA write와 CPU read가 겹치면 PoC에서 순서가 결정되어야 합니다. 이런 동시성 race는 directed sequence로 *의도적으로 겹치게* 만들고, scoreboard가 "DMA가 받은 값 == CPU의 최신 dirty 값"을 확인해야 합니다.

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
**실제**: IO-coherency는 *one-way* — 비캐싱 마스터는 자체 캐시가 없어 *남이 그들을 snoop할* 필요가 없습니다. snoop은 CPU 캐시 방향으로만 흐릅니다 (출처: HDG §3).<br>
**왜 헷갈리는가**: "coherent = 양방향"이라는 full coherency 경험의 일반화.
:::
:::danger[❓ 오해 2 — 'IO-coherent면 드라이버가 항상 cache flush를 안 해도 된다']
**실제**: IO-coherent *포트*에 연결되어 하드웨어 snoop이 동작할 때만 그렇습니다. 비-coherent 포트나 device-side 버퍼가 끼면 여전히 maintenance가 필요할 수 있습니다 (출처: HDG §3은 IO-coherent 연결 전제).<br>
**왜 헷갈리는가**: 기능과 연결 토폴로지를 분리하지 않음.
:::
:::danger[❓ 오해 3 — 'inclusive LLC eviction은 그냥 LLC만 비우면 된다']
**실제**: inclusive 정책에서 상위 캐시가 가진 line은 LLC에도 있어야 하므로, LLC가 그 line을 버리려면 *반드시* back-invalidation으로 상위 사본도 함께 버려야 합니다. 안 그러면 orphan line → coherence 붕괴 (출처: HDG §4).<br>
**왜 헷갈리는가**: eviction을 "내 레벨만의 일"로 봄. inclusive는 수직 invariant.
:::
:::danger[❓ 오해 4 — 'LLC는 그냥 큰 캐시일 뿐 coherence와 무관']
**실제**: LLC는 snoop filter(directory) + back-invalidation + PoC라는 세 가지 *능동적* coherence 역할을 수행합니다. 단순 메모리 풀이 아닙니다 (출처: HDG §4).<br>
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

**Internal (HDG / Confluence)**
- `Consistency & Coherency Overview` (HDG `memory_consistency_coherence_spec.md`) §3 — IO Coherency(one-way), NIC stale 패킷 문제와 해법; §4 — LLC의 Snoop Filter / Back-Invalidation(Inclusive) / Point of Coherence

**External**
- ARM AMBA AXI/ACE & CHI Architecture Specification — IO-coherent port, PoC 정의
- *A Primer on Memory Consistency and Cache Coherence* — inclusion / hierarchical coherence

---

## 다음 단계

이 코스의 마지막 모듈입니다. 개념을 다지려면 [용어집](../glossary/)에서 SWMR·MOESI·directory·PoC 정의를 다시 확인하고, [퀴즈](../quiz/)로 네 모듈 전체를 점검하세요. 신호 단위로 더 파고들고 싶다면 [AMBA AXI/ACE 모듈](../../amba_protocols/02_axi/)로, 검증 환경 구축은 [UVM scoreboard/coverage 모듈](../../uvm/05_tlm_scoreboard_coverage/)로 이어집니다.

[퀴즈 풀어보기 →](../quiz/04_io_coherency_llc_quiz/)
