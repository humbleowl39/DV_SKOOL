---
title: "Memory Consistency & Cache Coherence 용어집"
---

이 페이지는 본 코스에서 사용되는 일관성/코히런스 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

:::tip[검색 활용]
상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.
:::
---

## B — Back-Invalidation

### Back-Invalidation

**Definition.** Inclusive LLC가 cache line을 evict할 때 상위 L1/L2 캐시에 그 line의 사본을 버리도록 강제하는 무효화 명령.

**Source.** A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood).

**Related.** Inclusive cache, LLC, orphan line, eviction.

**Example.** LLC가 새 line을 받기 위해 victim Y를 evict하는데 Y가 상위 캐시에도 존재하면, LLC는 상위에 back-invalidation을 보내 Y를 함께 버리게 한다(dirty면 write-back 동반).

**See also.** [Module 04 — IO-Coherency & LLC PoC](../04_io_coherency_llc/)

---

## C — Cache Coherence / Consistency

### Cache Coherence

**Definition.** 여러 로컬 캐시에 흩어진 단일 메모리 위치의 사본을 동기화하여 어떤 처리 요소도 stale 데이터를 읽지 않도록 하는 투명한 하드웨어 메커니즘.

**Source.** A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood).

**Related.** SWMR, Data-Value invariant, Snooping, Directory, Memory Consistency.

**Example.** Core A가 변수 X를 쓰면 coherence 프로토콜이 Core B의 X 사본을 무효화해, B가 다음에 X를 읽을 때 최신값을 받게 한다.

**See also.** [Module 01 — Consistency vs Coherence](../01_consistency_vs_coherence/)

### Memory Consistency

**Definition.** 로드와 스토어의 순서 규칙 및 동적 로드가 반환할 수 있는 값을 정의하는, 하드웨어와 소프트웨어 간의 아키텍처적으로 가시적인 계약.

**Source.** A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood).

**Related.** Memory Model, memory barrier, ISA, Cache Coherence.

**Example.** "Core A가 X=1을 쓰고 barrier를 실행하면 그 이후 Core B의 로드는 1을 본다"는 순서 보장은 consistency 모델이 정의한다.

**See also.** [Module 01](../01_consistency_vs_coherence/)

---

## D — Data-Value Invariant / Directory

### Data-Value Invariant

**Definition.** 새 epoch 시작 시점의 메모리 위치 값이 직전 read-write epoch 종료 시점의 값과 일치해야 한다는 coherence 불변식.

**Source.** A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood).

**Related.** SWMR, Cache Coherence, epoch.

**Example.** 무효화 후 같은 line을 다시 읽으면 반드시 가장 최근에 쓰인 값을 반환해야 한다.

**See also.** [Module 01](../01_consistency_vs_coherence/)

### Directory

**Definition.** 어느 상위 캐시가 어느 cache line을 보유하는지를 추적하는 장부 구조로, broadcast 대신 targeted snoop을 보내기 위해 사용된다.

**Source.** A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood).

**Related.** Snoop Filter, Targeted Snoop, sharer, LLC, broadcast snooping.

**Example.** Core7의 read miss 시 directory가 `{owner: Core2}`를 조회해 Core2에만 snoop을 보낸다.

**See also.** [Module 03 — Directory & 확장성](../03_directory_scalability/)

---

## I — IO-Coherency / Inclusive Cache

### IO-Coherency

**Definition.** DMA·NIC 같은 비캐싱 마스터가 메모리를 접근할 때 인터커넥트가 자동으로 CPU 캐시를 snoop해 최신 데이터를 반영하는, 단방향(one-way) coherence.

**Source.** A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood).

**Related.** Point of Coherence, cache maintenance, snoop, DMA, NIC.

**Example.** NIC가 패킷을 read하면 인터커넥트가 CPU의 dirty 사본을 snoop으로 끌어와 전달하므로, 드라이버가 사전 cache flush를 하지 않아도 된다.

**See also.** [Module 04](../04_io_coherency_llc/)

### Inclusive Cache

**Definition.** 상위 L1/L2 캐시에 존재하는 모든 cache line이 하위 LLC에도 반드시 존재해야 한다는 정책을 가진 캐시 계층.

**Source.** A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood).

**Related.** Back-Invalidation, LLC, orphan line.

**Example.** Inclusive LLC는 victim eviction 시 상위 캐시에 back-invalidation을 보내 inclusion을 유지한다.

**See also.** [Module 04](../04_io_coherency_llc/)

---

## L — LLC

### LLC (Last Level Cache)

**Definition.** 캐시 계층의 최하위에 위치하며 snoop filter·back-invalidation·Point of Coherence 역할로 시스템 전역 coherence를 능동적으로 유지하는 공유 캐시.

**Source.** A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood).

**Related.** SLC (System Level Cache), Directory, Back-Invalidation, Point of Coherence.

**Example.** LLC는 directory로 targeted snoop을 보내고, inclusive eviction 시 back-invalidation을 발행하며, IO-coherent 트래픽의 PoC로 동작한다.

**See also.** [Module 04](../04_io_coherency_llc/)

---

## M — MESI / MOESI

### MESI

**Definition.** cache line을 Modified·Exclusive·Shared·Invalid 네 상태로 추적해 사본의 일관성을 관리하는 snooping 기반 coherence 프로토콜.

**Source.** A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood).

**Related.** Snooping, MOESI, dirty bit, Exclusive state.

**Example.** read miss 시 사본이 자신뿐이면 E로 받고, 이어지는 write는 무효화 broadcast 없이 E→M으로 전이한다.

**See also.** [Module 02 — Snooping & MESI/MOESI](../02_snooping_mesi_moesi/)

### MOESI

**Definition.** MESI에 Owned 상태를 추가해, dirty cache line을 메모리에 write-back하지 않고도 다른 캐시와 공유할 수 있게 하는 coherence 프로토콜.

**Source.** Sweazey & Smith (MOESI 분류); A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood).

**Related.** MESI, Owned state, write-back, cache-to-cache transfer.

**Example.** producer가 O(Owned) 상태로 dirty를 보유한 채 여러 consumer에게 S로 공급해 반복 write-back을 제거한다.

**See also.** [Module 02](../02_snooping_mesi_moesi/)

---

## O — Owned State / Orphan Line

### Owned (O) State

**Definition.** MOESI에서 cache line이 dirty인 채로 여러 캐시에 공유될 수 있으며, owner가 데이터 공급과 최종 메모리 반영 책임을 지는 상태.

**Source.** Sweazey & Smith, "A Class of Compatible Cache Consistency Protocols".

**Related.** MOESI, write-back, sharer.

**Example.** Owner는 메모리가 stale인 동안에도 다른 캐시에 S로 데이터를 공급하고, eviction 시 write-back을 수행한다.

**See also.** [Module 02](../02_snooping_mesi_moesi/)

### Orphan Line

**Definition.** Inclusive LLC가 eviction 후 추적하지 못하는, 상위 캐시에 남은 cache line 사본.

**Source.** A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood).

**Related.** Back-Invalidation, Inclusive Cache, SWMR.

**Example.** back-invalidation을 빠뜨리면 상위 L1/L2에 orphan line이 남아, 이후 그 주소의 무효화가 누락되어 coherence가 깨진다.

**See also.** [Module 04](../04_io_coherency_llc/)

---

## P — Point of Coherence / Protocol

### Point of Coherence (PoC)

**Definition.** 모든 메모리 observer(CPU·GPU·DMA)가 동일한 갱신 데이터를 보는 것이 보장되며 트랜잭션이 외부 DRAM에 commit되기 전 일치되는 물리적 지점.

**Source.** A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood).

**Related.** LLC, IO-Coherency, heterogeneous transaction.

**Example.** IO-coherent DMA read가 CPU dirty를 끌어오는 동작은 PoC(흔히 LLC)에서 일어나며, 모든 observer 뷰가 일치된 뒤 데이터가 전달된다.

**See also.** [Module 04](../04_io_coherency_llc/)

---

## S — Snooping / SWMR / Snoop Filter / Sharer

### Snooping

**Definition.** 모든 캐시가 공유 버스나 broadcast 인터커넥트의 트랜잭션을 관찰하여 peer 사본을 자동으로 무효화·갱신하는 coherence 메커니즘.

**Source.** A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood).

**Related.** MESI, MOESI, BusRdX, Directory, broadcast.

**Example.** writer가 BusRdX를 보내면 같은 line 사본을 가진 모든 캐시가 snoop해 자기 사본을 무효화한다.

**See also.** [Module 02](../02_snooping_mesi_moesi/)

### SWMR (Single-Writer, Multiple-Reader)

**Definition.** 임의의 메모리 위치에 대해 임의의 순간 한 코어만 쓰기/읽기를 하거나 여러 코어가 읽기만 할 수 있다는 coherence 불변식.

**Source.** A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood).

**Related.** Data-Value Invariant, Cache Coherence, invalidation.

**Example.** 한 코어가 write 권한을 가지는 동안 다른 어떤 캐시도 쓰기 가능 사본을 보유할 수 없다.

**See also.** [Module 01](../01_consistency_vs_coherence/)

### Snoop Filter

**Definition.** 상위 캐시의 line 보유 정보를 추적해 불필요한 snoop broadcast를 걸러내고 targeted snoop만 보내게 하는 directory 구현.

**Source.** A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood).

**Related.** Directory, Targeted Snoop, LLC.

**Example.** snoop filter가 없으면 모든 L1/L2에 broadcast하지만, 있으면 데이터를 가진 특정 코어에만 snoop을 보낸다.

**See also.** [Module 03](../03_directory_scalability/)

### Sharer

**Definition.** 특정 cache line의 사본을 보유하고 있다고 directory가 추적하는 상위 캐시.

**Source.** Directory coherence 일반 용어.

**Related.** Directory, Snoop Filter, Targeted Snoop, under-snoop.

**Example.** directory의 sharer 목록이 부정확해 실제 sharer를 빠뜨리면(under-snoop) 무효화가 누락되어 SWMR이 깨진다.

**See also.** [Module 03](../03_directory_scalability/)

---

## H — HSA / False Sharing

### HSA (Heterogeneous System Architecture)

**Definition.** CPU·GPGPU·NPU 등 서로 다른 처리 요소가 동일한 물리 메모리와 가상 주소 공간(Shared Virtual Memory)을 공유하는 시스템 아키텍처.

**Source.** A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood).

**Related.** Memory Consistency, Cache Coherence, ACE, CHI, Shared Virtual Memory.

**Example.** CPU가 행렬을 쓰고 barrier를 실행하면 GPGPU가 같은 포인터로 즉시 최신값을 읽는다고 가정하며, 인터커넥트가 coherence로 이를 떠받친다.

**See also.** [Module 01](../01_consistency_vs_coherence/)

### False Sharing

**Definition.** 논리적으로 무관한 변수들이 동일한 cache line에 배치되어, 한 변수의 갱신이 line 전체를 무효화함으로써 다른 변수 접근에 불필요한 coherence 트래픽을 유발하는 성능 저하 현상.

**Source.** Cache coherence 일반 용어 (snooping 트래픽 맥락).

**Related.** cache line, invalidation, Snooping.

**Example.** 두 코어가 같은 line의 서로 다른 변수만 써도 매번 line 무효화가 일어나, "기능은 정상이나 성능 급락"으로 나타난다.

**See also.** [Module 02](../02_snooping_mesi_moesi/)

---

## 추가 약어

| 약어 | 풀네임 | 한 줄 의미 |
|------|--------|-----------|
| **SMP** | Symmetric Multiprocessing | 여러 코어가 단일 주소 공간을 대칭적으로 공유하는 구조 |
| **SLC** | System Level Cache | LLC의 다른 명칭, 시스템 레벨 공유 캐시 |
| **ACE** | AXI Coherency Extensions | AMBA의 coherence 확장 (양방향/IO coherency 지원) |
| **CHI** | Coherent Hub Interface | ARM의 차세대 coherent 인터커넥트 프로토콜 |
| **PoC** | Point of Coherence | observer 뷰가 일치되는 물리적 지점 (흔히 LLC) |
| **BusRdX** | Bus Read-for-Ownership | write 의도의 read, 다른 사본 무효화 동반 |
