---
title: "Module 04 — ACE / CHI Coherency"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** AXI 위에 ACE 의 snoop 채널이 얹히면서 "주소만 옮기는 버스" 가 "캐시 상태까지 추적하는 coherent interconnect" 로 바뀌는 이유를 설명할 수 있다.
- **Differentiate** ACE(양방향 full coherency) · ACE-Lite(단방향 IO coherency) · CHI(packet 기반 scalable) 를 use-case 와 채널 구조 기준으로 구분할 수 있다.
- **Trace** GPGPU 가 CPU 의 dirty 캐시 라인을 읽을 때 interconnect 가 발행하는 snoop 트랜잭션을 단계별로 추적할 수 있다.
- **Apply** SWMR / Data-Value invariant 를 검증 체크로 환산해 coherent interconnect 의 scoreboard 시나리오를 작성할 수 있다.
- **Evaluate** 어떤 master 에 full ACE 를, 어떤 master 에 ACE-Lite 를 붙일지 면적/성능/coherency 요구로 판단할 수 있다.
:::
:::note[사전 지식]
- [Module 02 — AXI](../02_axi/) (5채널, VALID/READY, AxID/outstanding/OoO)
- 캐시 기본 (cache line, hit/miss, dirty/clean, write-back vs write-through)
- MESI 류 상태 머신의 대략적 개념 (Modified / Exclusive / Shared / Invalid)
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — CPU 가 쓴 행렬을 GPGPU 가 곧바로 읽는다

이기종 SoC 에서 흔한 작업 하나를 생각해 봅시다. CPU 가 행렬을 계산해 메모리에 쓰고, 곧바로 GPGPU 에게 "이 포인터부터 읽어서 처리해" 라고 넘깁니다. 문제는 CPU 가 방금 쓴 값이 아직 CPU 의 L1/L2 캐시 안에 _dirty_ 상태로 머물러 있고, DRAM 에는 옛날 값이 들어 있다는 데 있습니다. GPGPU 가 순진하게 DRAM 을 읽으면 _stale data_ 를 가져옵니다.

과거에는 이 문제를 소프트웨어가 떠안았습니다. 프로그래머가 명시적으로 CPU 캐시를 flush 하고 DMA 복사를 트리거한 뒤에야 GPU 가 데이터를 볼 수 있었습니다. 코드가 복잡해지고, flush 를 한 줄만 빠뜨려도 데이터가 깨집니다.

현대 SoC 는 이 부담을 하드웨어 인터커넥트로 옮깁니다. ARM 의 **ACE / CHI** 가 그 인터커넥트입니다. GPGPU 가 읽기를 시도하면 인터커넥트가 그 트랜잭션을 가로채(intercept) CPU 의 캐시를 **snoop** 하고, dirty 데이터가 있으면 DRAM 을 우회해 그 데이터를 곧장 GPGPU 로 라우팅합니다. 소프트웨어는 이 복잡한 거래를 전혀 보지 못합니다.

### 1.2 왜 이게 AMBA 모듈에 들어오는가

여기서 검증 엔지니어가 헷갈리는 지점이 생깁니다. coherence 는 "캐시 이론" 처럼 들리지만, 실제로는 **AXI 위에 얹힌 추가 채널과 트랜잭션** 으로 구현됩니다(ARM IHI 0022). 즉 ACE 는 새 프로토콜이 아니라 AXI 의 _확장_ 입니다 — 기존 AW/W/B/AR/R 5채널은 그대로 두고, snoop 을 위한 채널을 덧붙입니다.

이 모듈을 건너뛰면 "AMBA = AXI/APB/AHB" 라는 좁은 그림에 갇혀, 멀티코어·이기종 SoC 의 인터커넥트에서 왜 같은 주소에 대한 read 가 갑자기 다른 master 의 캐시를 건드리는지, scoreboard 에서 왜 DRAM 값과 실제 반환값이 다른지 설명하지 못합니다. 반대로 ACE/CHI 의 snoop 모델을 한 번 손으로 그려 보면, coherent interconnect 검증의 핵심 — _같은 주소에 대한 여러 master 의 관점이 일관되는가_ — 를 체크로 환산하는 길이 보입니다.

:::tip[🤔 잠깐 — _snoop 이 없다면_?]
GPGPU 가 CPU 의 dirty 캐시 라인을 모른 채 DRAM 만 읽으면 무슨 일이 벌어질까요?

<details>
<summary>정답</summary>

**Stale data 를 읽습니다**.

CPU 가 방금 쓴 값은 CPU 캐시에 dirty 로 있고 DRAM 에는 옛날 값이 있습니다. snoop 이 없으면 인터커넥트는 GPGPU 의 read 를 그냥 DRAM 으로 보내고, GPGPU 는 _옛날 값_ 을 받습니다.

즉 Core A 가 자기 로컬 캐시에서 변수를 갱신했는데 Core B 는 계속 옛 값을 읽는 상황입니다. 해결책이 바로 snooping protocol — read 가 올 때 인터커넥트가 다른 캐시를 자동으로 조회해 최신 dirty 데이터를 끌어옵니다.

</details>
:::
---

## 2. Intuition — 비유와 한 장 그림

:::tip[💡 한 줄 비유 — coherent interconnect ≈ 회의실 공유 화이트보드 관리자]
여러 사람(코어)이 각자 노트(캐시)에 같은 안건의 메모를 적는다. 누군가 "이 안건 최신 내용?" 이라 물으면, 관리자(interconnect)가 _벽에 붙은 원본_(DRAM)만 보는 게 아니라 _가장 최근에 고친 사람의 노트_(dirty cache line)를 찾아 그 내용을 건넨다. 모두가 항상 같은 최신 내용을 보도록 강제하는 게 coherence.
:::
### 한 장 그림 — AXI vs ACE coherent interconnect

```d2
direction: right

AXI: "AXI (non-coherent)\n주소만 옮긴다 — 캐시는 모름" {
  direction: right
  C: "CPU\n(L1/L2 cache)"
  IC: "Interconnect"
  D: "DRAM"
  C -> IC: "AR / R (read)"
  IC -> D: "그냥 DRAM 읽음\n→ stale 가능"
}
ACE: "ACE (coherent)\nsnoop 으로 캐시 상태까지 추적" {
  direction: right
  C2: "CPU\n(L1/L2 cache)"
  IC2: "Coherent\nInterconnect\n(+ snoop filter)"
  G2: "GPGPU"
  D2: "DRAM"
  G2 -> IC2: "ReadShared (AR + ACE attr)"
  IC2 -> C2: "snoop: 'dirty 있니?' (AC)"
  C2 -> IC2: "dirty line 전달 (CR/CD)"
  IC2 -> G2: "최신 데이터 (R)"
  IC2 -> D2: "필요시 write-back"
}
```

위 그림의 핵심은, ACE 에서는 read 트랜잭션 하나가 **DRAM 으로 직행하지 않고 다른 master 의 캐시를 먼저 거친다** 는 점입니다. 이를 위해 AXI 의 5채널에 더해 snoop 을 운반하는 채널이 추가됩니다.

### 왜 이렇게 설계됐는가 — Design rationale

coherence 가 지켜야 할 두 invariant 가 있습니다.

1. **SWMR (Single-Writer, Multiple-Reader)**: 임의 시점·임의 주소에 대해, 쓸 수 있는 코어는 _하나뿐_ 이거나, 읽기만 하는 코어가 _여럿_ 이거나 — 둘 중 하나만 성립한다.
2. **Data-Value invariant**: 새 epoch 시작 시점의 값은, 직전 read-write epoch 끝 시점의 값과 일치해야 한다.

이 두 규칙을 하드웨어가 _프로그래머 몰래_ 유지하려면(coherence 는 프로그래머에게 투명), read/write 트랜잭션이 올 때마다 "다른 캐시가 이 라인을 어떤 상태로 들고 있나" 를 확인하고 필요하면 invalidate 하거나 데이터를 끌어와야 합니다. 그 확인·강제 행위가 **snoop** 이고, AXI 위에 snoop 채널을 얹은 게 ACE 입니다.

---

## 3. 작은 예 — GPGPU 가 CPU 의 dirty 라인을 읽는 과정 단계 추적

HSA 시나리오를 트랜잭션 단계로 펼쳐 봅니다. CPU 가 주소 `A` 에 행렬 한 줄을 써서 L2 에 **dirty(Modified)** 로 들고 있고, GPGPU 가 같은 `A` 를 읽으려 합니다.

### 단계 다이어그램

```d2
direction: down

G: "GPGPU"
IC: "Coherent Interconnect\n(snoop filter)"
C: "CPU L2\n(line A = Modified/dirty)"
M: "DRAM"

G -> IC: "① ReadShared(A)"
IC -> C: "② snoop A — 'dirty 있나?'"
C -> IC: "③ dirty data + state Modified→Shared"
IC -> G: "④ 최신 data 반환"
IC -> M: "⑤ (정책에 따라) write-back A"
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | GPGPU | `A` 에 대한 coherent read 발행 (AXI AR + ACE 속성으로 "공유 의도" 표시) | 행렬을 읽어 처리하려 함 |
| ② | Interconnect | snoop filter 조회 → `A` 를 CPU L2 가 들고 있음을 확인 → CPU 에 snoop 발행 | 어느 캐시를 건드릴지 결정(Targeted Snoop) |
| ③ | CPU L2 | 자신이 dirty(Modified) 임을 응답하고 그 라인 데이터를 interconnect 에 넘김; 상태를 Shared 로 낮춤 | SWMR — 이제 reader 가 둘이므로 writer 권한 회수 |
| ④ | Interconnect | DRAM 을 _우회_ 하고 CPU 에서 받은 최신 데이터를 GPGPU 로 라우팅 | Data-Value invariant — 최신 값 보장 |
| ⑤ | Interconnect | 정책에 따라 dirty 데이터를 DRAM 에 write-back | DRAM 도 최신화(또는 Owned 상태로 지연)(추론) |

### invariant 검산

```
read 전:  A = Modified @ CPU(dirty),  DRAM = 옛값
snoop 후: A = Shared   @ CPU + @ GPGPU,  값은 둘 다 CPU 의 최신값

SWMR 확인:        writer 0개 + reader 2개 (CPU, GPGPU) → 합법 ✓
Data-Value 확인:  GPGPU 가 받은 값 == CPU 가 마지막에 쓴 값 ✓ (DRAM 옛값 아님)
```

> 핵심은 ④ 와 ⑤ 의 분리입니다. GPGPU 가 받는 데이터의 _출처_ 는 DRAM 이 아니라 **CPU 캐시** 이고(느린 main memory 를 완전히 우회), DRAM 갱신은 별개의 정책 문제입니다. scoreboard 가 "DRAM 값" 을 expected 로 잡으면 mismatch 가 나는 이유가 바로 여기 있습니다.

```systemverilog
// coherent read 의 expected 모델 (의사 코드 — scoreboard 관점)
// 주의: 단순히 DRAM 을 expected 로 쓰면 false mismatch.
function automatic data_t expected_coherent_read(addr_t a);
  // 1) 다른 master 가 a 를 dirty 로 들고 있으면 그 값이 정답
  foreach (cache_model[m]) begin
    if (cache_model[m].holds_dirty(a))
      return cache_model[m].line(a);   // snoop 으로 끌려올 값
  end
  // 2) 아무도 dirty 가 아니면 DRAM 이 정답
  return dram_model.read(a);
endfunction
```

:::note[여기서 잡아야 할 두 가지]
**(1) coherent read 의 정답은 DRAM 이 아닐 수 있다** — dirty 를 들고 있는 다른 master 의 캐시 값이 정답. scoreboard 의 expected 계산이 캐시 상태를 반영해야 false mismatch 를 피한다.<br>
**(2) snoop 은 상태 전이를 동반한다** — read 한 번이 다른 master 의 라인 상태를 Modified→Shared 로 낮춘다. SWMR invariant 가 이 전이를 강제한다.
:::
---

## 4. 일반화 — ACE / ACE-Lite / CHI

### 4.1 세 변종의 위치

AXI 를 기반으로 coherency 를 어디까지 넣느냐에 따라 세 가지로 갈립니다(아래 채널/명칭 디테일은 ARM IHI 0022(ACE), IHI 0050(CHI) 사양 기준).

| 변종 | coherency | 캐시 보유 | 대표 master | 핵심 추가 |
|------|-----------|----------|------------|----------|
| **ACE** (full) | 양방향 (two-way) | Yes (자기 캐시 있음) | CPU cluster, GPGPU | snoop **수신** 채널(AC/CR/CD) + 캐시라인 state |
| **ACE-Lite** | 단방향 (one-way, IO coherency) | No (캐시 없음) | DMA, NIC, 고정기능 accel | snoop **발행/응답 참여** 만, 자기 캐시 없음 |
| **CHI** | 양방향, scalable | Yes | many-core mesh, 대규모 SoC | 채널→**packet 기반**, 분산 directory, mesh NoC |

CPU↔GPGPU 처럼 _서로 상대를 snoop_ 하는 관계가 **full ACE(two-way)** 이고, NIC/DMA 처럼 _자기 캐시는 없지만 다른 캐시를 snoop 해서 최신 데이터를 받는_ 관계가 **ACE-Lite(one-way / IO coherency)** 입니다.

### 4.2 IO coherency — ACE-Lite 의 자리

NIC/DMA 가 정확히 ACE-Lite 의 use-case 입니다. NIC 이 CPU 가 캐시에 준비한 패킷을 전송할 때, 과거에는 소프트웨어가 cache clean/flush 를 직접 실행해야 했습니다. IO-coherent 포트에 붙은 NIC 은 read 를 발행하면 인터커넥트가 _자동으로_ CPU 캐시를 snoop 해서 dirty 패킷을 끌어옵니다. NIC 자신은 캐시가 없으므로 _남의 캐시를 snoop 하기만_ 하면 됩니다 — 그래서 full ACE 보다 가볍습니다.

```d2
direction: right

CPU: "CPU\n(packet in L2, dirty)"
IC: "IO-coherent port\n(interconnect)"
NIC: "NIC\n(no cache)\nACE-Lite master"
NIC -> IC: "read packet @ A"
IC -> CPU: "snoop A"
CPU -> IC: "dirty packet"
IC -> NIC: "최신 packet → 전송"
```

> 결과: 디바이스 드라이버에서 cache maintenance 코드가 사라지고, 성능은 오르고, 드라이버는 단순해진다.

### 4.3 snoop 트랜잭션의 일반 형태

coherent read/write 가 오면 인터커넥트는 (1) 어느 캐시를 snoop 할지 정하고, (2) snoop 을 발행하고, (3) 응답(데이터 유무 + 상태)을 모아 (4) 요청자에게 최종 데이터를 준다. 이 4 단계는 ACE 든 CHI 든 동형입니다 — CHI 는 이를 _채널_ 대신 _packet_ 으로 나른다는 점만 다릅니다(추론, ARM IHI 0050).

```
요청자 read → [interconnect: snoop filter 조회]
            → snoop 발행 → 대상 캐시 응답(hit dirty / hit clean / miss)
            → 데이터 출처 결정(캐시 우회 or DRAM) → 요청자에게 반환
            → 상태 전이(SWMR 유지) → (필요시) write-back
```

---

## 5. 디테일 — 채널, 상태, snoop filter, 검증

### 5.1 ACE 가 AXI 에 더하는 것

ACE 는 AXI 의 AW/W/B/AR/R 5채널을 그대로 두고, snoop 을 위한 채널 묶음과 추가 신호를 얹습니다(추론, ARM IHI 0022).

| 그룹 | 역할 | AXI 와의 관계 |
|------|------|--------------|
| 기존 5채널 (AW/W/B/AR/R) | 주소·데이터·응답 | 그대로 유지 |
| 트랜잭션 속성 (예: AxDOMAIN, AxSNOOP, AxBAR)(추론) | "이 access 가 coherent 인가, 어느 shareability domain 인가" | AR/AW 에 부가 |
| snoop address (AC) channel(추론) | interconnect → cached master: "이 주소 snoop 해" | 신규 |
| snoop response (CR) channel(추론) | master → interconnect: hit/dirty 여부 | 신규 |
| snoop data (CD) channel(추론) | master → interconnect: dirty 라인 데이터 | 신규 |

핵심 직관: **AXI 의 master 는 "주소를 옮기는" 쪽이지만, ACE 의 cached master 는 "snoop 을 받아 자기 캐시를 응답하는" 쪽이기도 하다.** 즉 ACE master 는 slave 역할(snoop 수신)을 겸합니다.

:::note[shareability domain — coherency 를 "어디까지" 적용할 것인가]
ACE 의 트랜잭션 속성 중 _domain_ (AxDOMAIN, 추론)은 "이 access 의 coherency 가 어느 캐시들까지 미치는가" 를 지정합니다. 개념적으로 보통 안쪽부터 바깥쪽으로 계층을 나눕니다 — 같은 cluster 안의 캐시들만 묶는 **inner**, 더 넓은 캐시 집합까지 포함하는 **outer**, 시스템 전체 관찰자(다른 cluster·IO master 등)를 포함하는 **system** 같은 식입니다(구체 명칭·범위는 사양 의존).

왜 굳이 범위를 나눌까요? snoop 은 공짜가 아니기 때문입니다. 어떤 데이터가 _한 cluster 안에서만_ 공유된다고 software 가 알고 있다면, 그 라인에 대한 snoop 을 시스템 전체로 broadcast 할 이유가 없습니다 — 바깥 cluster 들은 그 라인을 가질 수 없으니, 거기까지 snoop 을 보내면 순전한 낭비 트래픽이고 latency 만 늘립니다. domain 을 좁게 선언하면 interconnect 는 _그 domain 안의 캐시들만_ snoop 하고 밖으로는 트래픽을 내보내지 않습니다. 즉 shareability domain 은 "불필요한 snoop 을 도메인 경계 밖으로 새지 않게 막는" coherency 의 범위 한정 knob 입니다 — coherency 자체를 끄는 것이 아니라, _필요한 만큼만_ 적용해 트래픽과 latency 를 줄이는 도구입니다.
:::

### 5.2 캐시 라인 상태와 두 invariant

두 invariant 가 상태 머신으로 구현됩니다. MESI/MOESI 류의 구체 인코딩은 구현마다 다르므로, 여기서는 invariant 수준으로만 다룹니다.

- **SWMR**: 어떤 라인이든 _한 master 만 writable(Modified/Exclusive)_ 이거나 _여럿이 read-only(Shared)_ 다. write 가 발생하면 다른 모든 Shared 사본은 Invalid 로 떨어진다.
- **Data-Value**: 새 read epoch 가 보는 값은 직전 write epoch 가 남긴 값과 같다. snoop 이 dirty 사본을 끌어오는 것이 이 invariant 의 실행 수단.

:::note[dirty 를 write-back 없이 공유하려면 — Owned 상태와 ACE 의 dirty-shared]
§3 의 예에서 GPGPU 가 CPU 의 dirty 라인을 snoop 으로 받을 때, interconnect 는 그 dirty 데이터를 _꼭 DRAM 에 먼저 write-back 한 뒤_ 넘길 필요가 없습니다. 그렇다면 한 가지 의문이 남습니다 — DRAM 에는 여전히 옛값이 있고, 이제 그 라인을 _둘 이상_ 의 캐시가 공유하는데, "DRAM 과 다른 최신값을 누가 책임지고 들고 있는가?"

MESI 만으로는 이 상태를 표현할 수 없습니다. MESI 에서 Shared 는 "DRAM 과 같은 clean 사본" 을 뜻하므로, dirty 를 공유하려면 일단 write-back 해서 clean 으로 만든 뒤 Shared 로 가야 합니다 — 매 공유마다 DRAM write 가 강제됩니다. **MOESI 의 Owned 상태** 가 바로 이 비용을 없앱니다. Owned = "이 라인은 dirty(=DRAM 보다 최신)이고 공유 중이며, _내가_ 그 최신값을 책임지고 보관·공급한다" 는 상태입니다. owner 한 곳만 dirty 책임을 지고 나머지는 Shared 로 두면, write-back 없이 dirty line 을 공유하고 snoop 요청이 올 때마다 owner 가 데이터를 공급할 수 있습니다.

ACE 의 cache state 모델은 이 "dirty 인 채로 공유 가능" 개념을 (정확한 인코딩은 사양 의존, 추론) 담고 있어, 위 GPGPU 예에서 CPU 가 dirty 데이터를 넘긴 뒤에도 누군가가 그 dirty 책임을 보유한 채 공유 상태로 남을 수 있습니다. MOESI 의 Owned 와 그 상태 전이의 정식 treatment 는 [MESI/MOESI 스누핑](../../cache_coherence/02_snooping_mesi_moesi/) 에서 다룹니다.
:::

### 5.3 Snoop Filter (Directory) 와 LLC

코어가 많아지면 모든 L1/L2 에 "이 데이터 있니?" 를 broadcast 하는 것 자체가 버스를 막습니다. LLC(Last Level Cache / SLC)가 **snoop filter(directory)** 를 들고 어느 upstream 캐시가 어느 라인을 가졌는지 추적해, 요청이 오면 _그 캐시에만_ targeted snoop 을 보냅니다. 이로써 인터커넥트 트래픽이 급감합니다.

> **LLC 가 왜 생겼고, inclusion policy(inclusive/exclusive/NINE)가 무엇인지** — 그 등장 동기(off-chip DRAM 대역폭·latency 벽)와 정책 분류는 cache coherence 모듈에서 깊이 다룹니다: [I/O Coherency 와 LLC](../../cache_coherence/04_io_coherency_llc/). 여기서는 ACE 맥락에서 LLC 가 snoop filter + PoC 역할을 한다는 점만 짚습니다.

LLC 는 coherence 의 수직(hierarchical) 축도 담당합니다.

- **Back-Invalidation**: LLC 가 strictly inclusive 면 L1/L2 의 데이터는 LLC 에도 있어야 한다. LLC 가 라인을 evict 하면 upstream 에 back-invalidation 을 보내 그 사본도 버리게 해 orphan 데이터를 막는다. (back-invalidation 은 inclusive 정책의 직접 산물 — exclusive/NINE 이면 양상이 달라진다. 위 링크 참조.)
- **Point of Coherence (PoC)**: IO-coherent / 이기종 트랜잭션에서 LLC 가 PoC 역할 — 모든 관찰자(CPU/GPU/DMA)가 같은 값을 보도록 보장한 뒤 DRAM 에 commit 하는 최종 junction.

```d2
direction: down

L1A: "CPU0 L1/L2"
L1B: "CPU1 L1/L2"
GPU: "GPGPU"
LLC: "LLC / SLC\n(snoop filter = directory)\n= Point of Coherence"
DRAM: "DRAM"

L1A -> LLC: "req / snoop resp"
L1B -> LLC: "req / snoop resp"
GPU -> LLC: "coherent req"
LLC -> L1A: "targeted snoop / back-invalidate"
LLC -> L1B: "targeted snoop / back-invalidate"
LLC -> DRAM: "commit (PoC 통과 후)"
```

### 5.4 CHI 가 ACE 와 다른 점

CHI(Coherent Hub Interface)는 ACE 의 _채널 기반_ 신호 묶음을 **packet 기반 transport** 로 바꿉니다(ARM IHI 0050). 코어 수가 수십~수백으로 늘면 ACE 의 와이어 묶음이 라우팅 부담이 되기 때문에, CHI 는 request/response/snoop/data 를 packet 으로 정의하고 mesh NoC 위에서 분산 directory 로 coherence 를 유지합니다. 정교한 directory 기반·interconnect 주도 구조의 현대적 정점이 CHI 입니다.

> 검증 관점에서 ACE↔CHI 의 차이는 "어떻게 나르냐(채널 vs packet)" 이지, _무엇을 보장하냐(SWMR / Data-Value)_ 가 아닙니다. invariant 체크는 동일하게 쓰입니다.

### 5.5 DV 핵심 검증 포인트

| 항목 | 시나리오 | 확인 사항 |
|------|---------|----------|
| coherent read 정답 | 다른 master 가 dirty 보유 | 반환값 == 그 master 의 dirty 값 (DRAM 옛값 아님) |
| SWMR | 한 master 가 write 시 | 다른 모든 Shared 사본이 Invalid 로 전이 |
| Data-Value | write→다른 master read | read 가 직전 write 값을 본다 |
| Targeted snoop | snoop filter hit | snoop 이 _해당 master 에만_ 가는지 (broadcast 아님) |
| Back-invalidation | inclusive LLC evict | upstream 사본이 실제로 invalidate 되는지 |
| IO coherency | NIC/DMA read | SW flush 없이 dirty 데이터 자동 수신 |
| PoC ordering | 여러 관찰자 | DRAM commit 전 모든 관찰자 일관 |

### 5.6 검증 함정 — non-coherent scoreboard

가장 흔한 함정은 AXI 시절의 scoreboard 를 그대로 가져오는 것입니다. AXI scoreboard 는 "주소 A 의 expected = DRAM 모델의 A" 로 둡니다. ACE 에서는 dirty 를 들고 있는 다른 master 가 있으면 이 expected 가 _틀립니다_. coherent scoreboard 는 **모든 master 의 캐시 상태를 모델링** 하고, read 가 올 때 (1) dirty holder 가 있으면 그 값을, (2) 없으면 DRAM 값을 expected 로 계산해야 합니다(§3 의사 코드 참조).

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'ACE 는 AXI 와 별개의 새 프로토콜이다']
**실제**: ACE 는 AXI 의 _확장_ 입니다. 기존 5채널(AW/W/B/AR/R)을 그대로 두고 snoop 채널과 트랜잭션 속성을 얹은 것(추론, ARM IHI 0022). 그래서 AXI 의 VALID/READY·outstanding·OoO 지식이 그대로 재사용됩니다.<br>
**왜 헷갈리는가**: 이름이 다르고 "coherency" 라는 무거운 단어가 붙어 완전히 다른 것으로 보임.
:::
:::danger[❓ 오해 2 — 'coherence = consistency']
**실제**: 다릅니다. **Consistency** 는 프로그래머에게 보이는 _ordering 계약_ (ISA·barrier 로 노출), **Coherence** 는 프로그래머에게 투명한 _하드웨어 메커니즘_ 으로 단일 주소의 사본들을 동기화. ACE/CHI 는 coherence 쪽 기계.<br>
**왜 헷갈리는가**: 둘 다 "메모리가 올바르게 보인다" 를 다루지만, 가시성과 범위(전체 ordering vs 단일 주소)가 다름.
:::
:::danger[❓ 오해 3 — 'coherent read 는 항상 DRAM 에서 온다']
**실제**: dirty 를 들고 있는 다른 master 가 있으면 데이터는 _그 캐시_ 에서 옵니다 — DRAM 을 우회. scoreboard 가 DRAM 을 expected 로 쓰면 false mismatch.<br>
**왜 헷갈리는가**: non-coherent AXI 의 직관(read = 메모리 읽기)을 그대로 가져옴.
:::
:::danger[❓ 오해 4 — 'IO coherency 면 NIC/DMA 도 자기 캐시가 있어야 한다']
**실제**: ACE-Lite master 는 _자기 캐시가 없습니다_ — 남의 캐시를 snoop 해서 최신 데이터를 받기만 하는 one-way(IO) coherency.<br>
**왜 헷갈리는가**: "coherent" 라는 단어가 양방향 캐시 참여를 연상시킴.
:::
:::danger[❓ 오해 5 — 'snoop 은 모든 캐시에 broadcast 된다']
**실제**: snoop filter(directory)가 있으면 _해당 라인을 가진 캐시에만_ targeted snoop 을 보냅니다. broadcast 는 코어가 적은 옛 방식.<br>
**왜 헷갈리는가**: "snooping protocol" 이라는 역사적 용어가 bus broadcast 를 연상시킴(초기 MESI/MOESI).
:::
### DV 디버그 체크리스트

#### Coherent read/write

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| read 반환값이 DRAM 과 다름 (정상일 수 있음) | dirty holder 의 값이 정답인지 | scoreboard 가 캐시 상태 모델하는지(§5.6) |
| 다른 master write 후에도 옛 Shared 값 read | SWMR 위반 — invalidate 누락 | write 시 Shared 사본의 Invalid 전이 |
| write→read 가 옛 값 | Data-Value invariant 깨짐 | snoop 이 dirty 를 끌어왔는지 |

#### Snoop / Directory

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| snoop 트래픽 폭증 | broadcast 되고 있음 | snoop filter/directory 동작 여부(§5.3) |
| snoop 이 엉뚱한 master 에 감 | directory 매핑 오류 | snoop filter 의 line→master 추적 |
| inclusive LLC evict 후 stale upstream | back-invalidation 누락 | LLC evict 경로의 back-invalidate 발행(§5.3) |

#### IO coherency (ACE-Lite)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| NIC 이 stale 패킷 전송 | IO-coherent 포트 미연결/속성 누락 | master 의 coherent 속성 설정 |
| DMA read 가 SW flush 필요 | one-way coherency 미동작 | interconnect 의 자동 snoop 경로 |

---

## 7. 핵심 정리 (Key Takeaways)

- **ACE = AXI + snoop**: 새 프로토콜이 아니라 AXI 5채널 위에 snoop 채널·속성을 얹은 확장. VALID/READY 등 AXI 지식 재사용(추론).
- **coherence ≠ consistency**: coherence 는 단일 주소 사본 동기화의 _투명한 하드웨어 메커니즘_, consistency 는 ordering 의 _프로그래머 가시 계약_.
- **두 invariant 가 검증 골격**: SWMR(쓰는 자 하나 or 읽는 자 여럿) + Data-Value(새 epoch = 직전 write 값).
- **coherent read 정답은 DRAM 이 아닐 수 있다**: dirty holder 의 캐시 값이 정답 — scoreboard 가 캐시 상태를 모델해야 함.
- **ACE vs ACE-Lite vs CHI**: full two-way(자기 캐시 O) / one-way IO coherency(캐시 X, NIC·DMA) / packet 기반 scalable mesh.
- **LLC = snoop filter + PoC**: targeted snoop 으로 트래픽 절감, back-invalidation 으로 inclusive 유지, PoC 로 모든 관찰자 일관 보장.

:::caution[실무 주의점 — non-coherent scoreboard 를 coherent DUT 에 재사용]
**현상**: AXI 시절 scoreboard(expected = DRAM 모델)를 ACE/CHI DUT 에 그대로 붙이면, 다른 master 가 dirty 를 들고 있을 때 read 반환값이 DRAM 옛값과 달라 _대량의 false mismatch_ 가 난다.

**원인**: coherent read 의 정답은 dirty holder 의 캐시 값이지 DRAM 값이 아니다(interconnect 가 DRAM 을 우회해 캐시 데이터를 라우팅).

**점검 포인트**: scoreboard 가 (1) 모든 cached master 의 라인 상태를 모델링하고, (2) read 시 dirty holder 우선·없으면 DRAM 으로 expected 를 계산하며, (3) write 시 다른 Shared 사본을 Invalid 로 전이시키는지 확인(§3 의사 코드, §5.5 표).
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — coherent read 의 정답 (Bloom: Apply)]
CPU 가 주소 A 에 0xDEAD 를 써서 L2 에 dirty 로 들고 있고 DRAM 의 A 는 0xBEEF 다. GPGPU 가 ACE 로 A 를 read 하면 받는 값은?

<details>
<summary>정답</summary>

**0xDEAD**. interconnect 가 CPU L2 를 snoop 해 dirty 값을 끌어와 GPGPU 로 라우팅하고 DRAM(0xBEEF)을 우회한다(Data-Value invariant). scoreboard 가 DRAM(0xBEEF)을 expected 로 잡으면 false mismatch.

</details>
:::
:::tip[🤔 Q2 — ACE vs ACE-Lite 선택 (Bloom: Evaluate)]
캐시가 없는 NIC 에 full ACE 와 ACE-Lite 중 무엇을 붙일까? 이유는?

<details>
<summary>정답</summary>

**ACE-Lite**. NIC 은 자기 캐시가 없으므로 snoop 을 _수신_ 할 라인이 없다. 필요한 건 "남의 캐시를 snoop 해서 최신 데이터를 받는" one-way(IO) coherency 뿐. full ACE 의 snoop 수신 채널·캐시 state 머신은 NIC 에 불필요한 면적·복잡도다.

</details>
:::
:::tip[🤔 Q3 — coherence vs consistency (Bloom: Analyze)]
"barrier 를 넣었는데도 다른 코어가 옛 값을 본다" 는 버그가 coherence 문제인지 consistency 문제인지 어떻게 가르나?

<details>
<summary>정답</summary>

둘의 _범위_ 로 가른다. 한 주소의 사본이 동기화 안 돼 옛 값을 본다면 **coherence**(SWMR/invalidate 누락) 문제 — snoop·invalidate 경로를 본다. 여러 주소 간 _순서_ 가 barrier 가 약속한 대로 안 보인다면 **consistency**(ordering) 문제 — 파이프라인·메모리 모델·barrier 구현을 본다. coherence 는 단일 주소, consistency 는 전체 ordering 을 다룬다.

</details>
:::
### 7.2 출처

**External**
- ARM, *AMBA AXI and ACE Protocol Specification* (IHI 0022) — ACE/ACE-Lite snoop 채널·속성
- ARM, *AMBA CHI Architecture Specification* (IHI 0050) — packet 기반 coherent transport
- *A Primer on Memory Consistency and Cache Coherence*, Nagarajan/Sorin/Hill/Wood (Morgan & Claypool)

:::note[채널·상태 디테일 검증 주의]
본 모듈에서 AC/CR/CD 채널명·AxDOMAIN/AxSNOOP 등 채널 레벨 표기는 ARM IHI 0022/0050 기준의 (추론) 이며, 권위 있는 인용 전 사양서로 재확인해야 합니다.
:::
---

## 다음 단계

- 📝 [**Module 04 퀴즈**](../quiz/04_ace_chi_coherency_quiz/)
- ➡️ [**Module 05 — Quick Reference Card**](../05_quick_reference_card/)
- 🔗 관련 토픽: [MMU](../../mmu/) (주소 변환과 shareability domain), [RAS](../../ras/) (poison bit 가 같은 coherent interconnect 를 타고 전파), [DPU](../../dpu/) (IO-coherent accelerator 통합)
