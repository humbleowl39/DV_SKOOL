---
title: "Unit 4 — Computer Architecture / Performance Modeling"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Compute** N-way set associative cache 의 index/tag/offset 비트 폭과 hit/miss 시나리오를 계산한다.
- **Compare** Von Neumann vs Harvard, RISC vs CISC, 그리고 inclusive vs exclusive cache 의 트레이드오프를 비교한다.
- **Trace** 5-stage in-order pipeline 에서 data / structural / control hazard 가 어떻게 발생하고 forwarding / stall 이 어떻게 해결하는지 추적한다.
- **Explain** Tomasulo 알고리즘, register renaming, reorder buffer 의 역할을 설명한다.
- **Distinguish** bimodal / gshare / TAGE / BTB / RAS 의 동작 차이와 사용처를 구분한다.
- **Apply** VIPT vs PIPT vs VIVT 의 alias 문제를 분석하고 OS / 하드웨어가 어떻게 대응하는지 설명한다.
:::
:::note[사전 지식]
- 디지털 회로, 메모리 계층, [Unit 1](../01_digital_rtl/) 의 파이프라인 개념
- 운영체제 기본 (process, scheduling, paging)
:::
---

## 1. Cache & Memory Hierarchy

### 1.1 한 줄 그림

```
CPU register (1ns) → L1 (~3ns) → L2 (~10ns) → L3 (~30ns) → DRAM (~100ns) → NVMe (~100us) → HDD (~10ms)
                    [SRAM, on-chip]                       [DDR DRAM]      [Flash]      [Disk]
```

위는 **memory hierarchy**(메모리 계층 — 빠르고 작은 저장소부터 느리고 큰 저장소까지 단계로 쌓아, 자주 쓰는 데이터는 위쪽 빠른 층에 두는 구조)입니다. **L1/L2/L3**는 CPU에 가까운 순서의 캐시 레벨, **SRAM**(빠르지만 비싼 온칩 메모리 — 캐시 재료), **DRAM**(느리지만 싼 대용량 메인 메모리), **NVMe**(고속 플래시 SSD), **HDD**(자기 디스크)입니다. 위로 갈수록 빠르고 작고 비쌉니다.

### 1.2 Cache Mapping — 3가지

| 방식 | 한 라인이 갈 수 있는 위치 | Hardware | 충돌 |
|------|--------------------------|----------|------|
| **Direct mapped** | 1 곳 | 단순, 빠름 | 같은 index → 충돌 많음 |
| **N-way set associative** | N 곳 | 가장 흔함 (4/8/16-way) | trade-off |
| **Fully associative** | 어디든 | 복잡, 느림, 비쌈 | 충돌 거의 없음 (TLB 에서 흔함) |

**Cache mapping**(캐시 매핑 — 메모리 라인이 캐시의 어느 칸에 들어갈 수 있는가를 정하는 규칙)의 세 방식입니다. **Direct mapped**(라인마다 갈 자리가 딱 한 곳), **N-way set associative**(N개 후보 자리 중 하나 — set은 그 N개 묶음), **Fully associative**(어느 자리든 가능)이며, 뒤(§1.3)의 **tag**(주소의 상위 식별 비트 — 그 칸에 들어 있는 게 정말 찾는 라인인지 확인)/**index**(어느 set인지 고르는 중간 비트)/**offset**(라인 안에서 몇 번째 바이트인지)으로 주소를 분해합니다.

### 1.3 주소 분해

32-bit 주소, 64B 라인, 32 KB 8-way 캐시:

```
Cache size       = 32 KB
Line size        = 64 B  → offset = log2(64) = 6 bits
Number of lines  = 32K / 64 = 512
Number of sets   = 512 / 8 (way) = 64 → index = log2(64) = 6 bits
Tag              = 32 - 6 - 6 = 20 bits
```

```
[ 20-bit tag ][ 6-bit index ][ 6-bit offset ]
```

### 1.4 Replacement Policy

**Replacement policy**(교체 정책 — set이 꽉 찼을 때 새 라인을 넣기 위해 어떤 기존 라인을 내보낼지 고르는 규칙)입니다. **LRU**(Least Recently Used, 가장 오래 안 쓴 라인을 내보냄)가 대표적입니다.

| Policy | 동작 | 비용 |
|--------|------|------|
| **LRU** | Least Recently Used eviction | N-way 에서 O(N) 비트 + 갱신 로직 |
| **Pseudo-LRU** | tree 기반 근사 | 비트 적음, hardware 단순 (3-bit per 4-way) |
| **Random** | 무작위 | 가장 단순 |
| **MRU** | 가장 최근 것 eviction (특수) | 스캔 패턴에 유리 |
| **FIFO** | 가장 오래된 것 | LRU 보다 약간 나쁨, hardware 단순 |

### 1.5 Write Policy

**Write policy**(쓰기 정책 — 캐시에 쓸 때 RAM에도 언제 반영할지 정하는 규칙)입니다.

- **Write-through** — 항상 RAM 같이 갱신. 다음 레벨 cache 가 항상 최신.
- **Write-back** — Dirty(캐시가 RAM보다 새것임을 표시하는) 비트 set, eviction(자리 비우려 라인을 내보냄) 시에만 RAM 갱신. Bandwidth 절약, coherency(여러 사본 간 값 일관성) 복잡.
- **Write-allocate** — Write miss 시 line 을 가져옴 → 이후 write 는 cache 에.
- **No-write-allocate** — Write miss 는 RAM 에 바로 (cache 안 채움).

조합 — *Write-back + Write-allocate* 가 가장 흔함.

### 1.6 Inclusive vs Exclusive vs NINE

- **Inclusive** — 상위 (L1) 의 모든 데이터가 하위 (L2) 에도 *반드시* 존재. 검색 단순, snooping(다른 코어들의 캐시 트래픽을 엿들어 일관성을 유지하는 방식) 효율 ↑. *공간 낭비*.
- **Exclusive** — L1 에 있는 데이터는 L2 에 *없다*. 공간 효율 ↑. AMD 자주 사용.
- **NINE** (Non-Inclusive Non-Exclusive) — 강제 안 함. Intel 흔함.

---

## 2. Architecture Fundamentals

### 2.1 Von Neumann vs Harvard

| 항목 | Von Neumann | Harvard |
|------|-------------|---------|
| Memory | 단일 (instr + data 같이) | 분리 (instr / data 각각) |
| Bus | 단일 → 병목 | 두 개 → 동시 fetch + load/store |
| 사용처 | x86, 범용 PC | DSP(Digital Signal Processor, 신호 처리 전용 프로세서), Cortex-M MCU |

**Von Neumann**(명령과 데이터를 한 메모리·한 버스로 다루는 구조)과 **Harvard**(명령용·데이터용 메모리/버스를 분리해 동시에 가져오는 구조)의 대비입니다.

**Modified Harvard** — *cache 레벨에서만* 분리 (L1 I-cache + L1 D-cache), main memory 는 통합. 현대 CPU 가 대부분 이 방식.

### 2.2 RISC vs CISC

| 항목 | RISC (ARM, RISC-V, MIPS) | CISC (x86) |
|------|---------------------------|------------|
| Instruction 수 | 적음, 단순 | 많음, 복잡 |
| 길이 | 고정 (32b 또는 16b) | 가변 (1~15 byte) |
| Load/store | 메모리 접근은 load/store 만 | 메모리 직접 연산 가능 |
| Pipeline | 단순 | 복잡 (decoder → uop 변환) |

**현실** — **RISC**(Reduced Instruction Set Computing, 단순·고정길이 명령으로 빠른 파이프라인을 노리는 설계)와 **CISC**(Complex ISC, 복잡·가변길이 명령으로 명령당 일을 많이 하는 설계)의 대비이지만, 현대 x86 도 내부적으로 uop(micro-operation, 복잡한 명령을 쪼갠 RISC-like 내부 마이크로 연산) 로 디코드 → 본질적으로 차이 줄어듦.

---

## 3. Pipeline & Execution

### 3.1 5-Stage Classic Pipeline

**Pipeline**(파이프라인 — 명령 처리를 여러 단계로 쪼개 조립 라인처럼 겹쳐 실행해, 매 클럭 한 명령씩 완료되게 하는 기법)의 고전적 5단계입니다.

```
IF (instruction fetch) → ID (decode + register read) → EX (execute / ALU) → MEM (memory access) → WB (write back)
```

### 3.2 Hazard 3종

**Hazard**(해저드 — 파이프라인에서 명령을 겹쳐 실행하다 의존성·자원 충돌로 그냥 진행하면 틀린 결과가 나는 상황)는 세 종류입니다.

**1. Structural** — 한 자원을 두 stage 가 동시에 요구.

단일 메모리 포트를 가진 시스템에서 IF (instruction fetch) 와 MEM (data load) 가 같은 사이클에 메모리를 요청하면 충돌이 생깁니다. 해결책은 Instruction cache 와 Data cache 를 분리하는 Harvard 구조를 채택하거나, 둘 중 하나를 한 사이클 stall 시키는 것입니다.

**2. Data** — 이전 명령의 결과를 다음 명령이 *아직 완료되기 전에* 읽으려 하는 RAW (Read-After-Write) 의존입니다.

```
I1: ADD r1, r2, r3       # EX 에서 r1 계산
I2: SUB r4, r1, r5       # ID 에서 r1 필요 → I1 의 EX 결과 필요
```

일반적인 RAW 는 **forwarding (bypassing)** 으로 해결할 수 있습니다. EX stage 에서 나온 결과를 다음 명령의 EX 입력으로 직접 연결하는 것입니다. 그러나 load 명령 직후에 그 결과를 사용하는 *load-use hazard* 는 load 결과가 MEM stage 가 끝나야 나오므로 forwarding 만으로 부족해 1 사이클 **stall (bubble)** 이 불가피합니다.

**3. Control (Branch)** — Branch 의 결과가 EX stage 에서 확정될 때까지, 그 사이에 IF 가 이미 잘못된 명령을 fetch 해버리는 문제입니다.

파이프라인이 깊을수록 잘못 fetch 한 명령 수(branch penalty) 가 커집니다. 대응 방법은 크게 세 가지입니다. **Branch prediction** 으로 올바른 경로를 미리 예측하고, mispredict 시에만 flush 후 refetch 합니다. MIPS 에서는 branch 다음 명령을 무조건 실행하는 **delay slot** 을 도입했는데, 이는 컴파일러에 부담을 주는 *최후 수단*으로 여겨집니다.

- Branch prediction
- Delay slot (MIPS 의 *최후 수단*)
- Flush + refetch (mispredict 시)

### 3.3 Out-of-Order Execution — Tomasulo

**Out-of-Order(OoO) execution**(명령을 프로그램 순서가 아니라 operand가 준비된 것부터 실행해 빈 시간을 메우는 기법)의 고전 알고리즘이 **Tomasulo**(1967 IBM이 고안 — reservation station·common data bus·register renaming으로 동적 스케줄링을 구현)입니다. 아래 그림의 구성요소는 본문에서 하나씩 풀이합니다.

```d2
direction: right
grid-rows: 3
RS.label: "Reservation Station"
FU.label: "FU (ALU/Mem/FP)"
CDB.label: "CDB"
ROB.label: "ROB (in-order commit)"
Fetch -> Decode -> Rename -> Dispatch
Dispatch -> RS: "waiting for operands"
RS -> FU: "operand ready"
FU -> CDB: broadcast
CDB -> ROB
```

**핵심**:

Tomasulo 알고리즘의 각 구성 요소는 서로 다른 문제를 해결하기 위해 도입됩니다. **Register renaming** 은 architectural register `r1` 을 내부 physical register 에 동적으로 매핑함으로써 WAW (Write-After-Write) 와 WAR (Write-After-Read) false dependency 를 제거합니다. 이 덕분에 서로 관련 없는 명령들이 같은 architectural register 를 재사용하더라도 병렬 실행이 가능해집니다. **Reservation Station** 은 명령이 dispatch 된 후 operand 가 준비될 때까지 대기하는 버퍼로, operand 가 모두 갖춰지면 FU(Functional Unit) 로 issue 합니다. **CDB (Common Data Bus)** 는 FU 가 계산을 마쳤을 때 그 결과를 모든 RS 와 ROB 에 broadcast 해서 기다리던 명령들이 즉시 operand 를 받아 실행 준비 상태로 전환되게 합니다. 마지막으로 **ROB (Reorder Buffer)** 는 실행은 out-of-order 로 하더라도 *program order 순서대로 commit* 하도록 강제해서, exception 이나 branch mispredict 발생 시 중간 결과를 깨끗하게 rollback 할 수 있게 합니다.

- **Register renaming** — architectural register `r1` 을 *내부 physical register* 로 매핑 → WAW / WAR hazard 제거.
- **Reservation Station** — 명령이 *operand 준비될 때까지* 대기, 준비되면 FU 로 issue.
- **CDB** — FU 결과를 모든 RS / ROB 로 broadcast (RS 의 대기 명령이 깨어남).
- **ROB** — *In-order commit* → exception / branch mispredict 시 *깨끗하게 rollback*.

### 3.4 Memory Disambiguation

Load 와 Store 의 주소가 같은지 *모르면* 순서 보존을 위해 stall. **Load forwarding** 또는 **memory dependence predictor** 가 *speculative load*.

---

## 4. Branch Prediction

**Branch prediction**(분기 예측 — 조건 분기의 결과(taken/not-taken)와 목적지를 결과가 확정되기 전에 미리 맞혀, 파이프라인이 멈추지 않게 하는 기법)은 깊은 파이프라인의 성능을 좌우합니다. 틀리면(mispredict) 잘못 가져온 명령을 버리고(flush) 다시 가져옵니다.

### 4.1 종류 — 진화 순서

| 종류 | 설명 | 정확도 |
|------|------|--------|
| **Static** | Backward taken, forward not-taken | ~ 70% |
| **Bimodal (2-bit saturating counter)** | 각 PC 마다 *Strongly NT / Weakly NT / Weakly T / Strongly T* | ~ 85% |
| **Local history** | 같은 branch 의 *과거 N번* pattern → counter table 인덱스 | ~ 90% |
| **Gshare** | Global history XOR PC → counter table | ~ 95% |
| **TAGE** | 여러 history 길이의 tag-based 테이블 — *가장 긴 match 사용* | ~ 97%+ (현대 CPU) |
| **Perceptron** | Linear classifier — Intel 일부 | TAGE 와 비슷 |

표의 용어: **saturating counter**(0~3 같은 작은 카운터로 taken 쪽이면 증가, 한쪽 끝에서 더 안 넘어가게 포화 — 한두 번 빗나가도 예측이 흔들리지 않음), **global history**(최근 분기들의 taken/NT 이력 비트열), **Gshare**(global history와 PC를 XOR해 카운터 표를 인덱싱), **TAGE**(여러 이력 길이의 태그 달린 표 중 가장 긴 일치를 쓰는 최신 예측기)입니다.

### 4.2 BTB (Branch Target Buffer)

**BTB**(Branch Target Buffer — 분기 명령의 PC를 키로 예측 목적지 주소를 저장한 캐시; IF 단계에서 곧장 다음 주소를 알려줌)입니다.

```
[PC] → [BTB lookup] → predicted target + taken/NT
```

- BTB hit 이면 *target 도 IF stage 에 알려줌* → 곧장 다음 fetch.
- BTB miss 면 decode 까지 가서 target 계산.

### 4.3 RAS (Return Address Stack)

**RAS**(Return Address Stack — 함수 호출 시 복귀 주소를 스택에 쌓아 `ret`의 목적지를 정확히 예측하는 보조 구조)입니다.

- `call` 시 return address 를 RAS 에 push.
- `ret` 시 RAS pop → 정확한 return prediction (보통 99%+).
- Stack overflow / mismatched call-ret 가 *유일한 mispredict* 원인.

---

## 5. Virtual Memory & OS

**Virtual memory**(가상 메모리 — 프로그램이 보는 가상 주소(VA)를 실제 물리 주소(PA)로 매핑해, 프로세스마다 독립된 큰 주소 공간을 주고 격리하는 메커니즘)가 OS·하드웨어 협업의 핵심입니다. 그 매핑 정보가 **page table**(페이지 테이블), 빠른 변환 캐시가 **TLB**입니다.

### 5.1 Page Table — Multi-Level

64-bit Linux 의 *4-level paging*:

```
VA[63:48] = sign extension
VA[47:39] = PGD index   (Page Global Dir)
VA[38:30] = PUD index   (Page Upper Dir)
VA[29:21] = PMD index   (Page Middle Dir)
VA[20:12] = PTE index   (Page Table Entry)
VA[11:0]  = page offset (4 KB page)
```

각 단계 *4 KB 페이지 * 512 엔트리 (8B 씩)*. **Walk 가 4 번 메모리 접근** → 매우 느림 → TLB 필수.

### 5.2 TLB (Translation Lookaside Buffer)

**TLB**(Translation Lookaside Buffer — 최근 사용한 가상→물리 주소 변환 결과를 담는 작은 캐시; 매번 page table을 다 걷지 않게 함)입니다.

- **Fully-associative**, 작음 (수십~수백 엔트리).
- **TLB miss** 시 page table walk (수십 사이클).
- **Context switch** 시 TLB flush 필요 (또는 ASID(Address Space ID, 각 프로세스에 붙이는 식별자로 flush 없이 TLB 항목을 구분) 사용해 process 별 격리).

### 5.3 VIPT vs PIPT vs VIVT

캐시 인덱싱 / 태그를 *가상* 주소로 하느냐 *물리* 로 하느냐의 조합입니다. **VIVT**(Virtually Indexed Virtually Tagged), **VIPT**(Virtually Indexed Physically Tagged), **PIPT**(Physically Indexed Physically Tagged) — V는 virtual, P는 physical을 뜻하며 각각 index/tag를 어느 주소로 쓰는지를 나타냅니다. 여기서 **alias**(앨리어스 — 같은 물리 주소를 가리키는 서로 다른 가상 주소가 캐시에 사본을 둘 만들어 일관성이 깨지는 문제)가 핵심 쟁점입니다.

| 방식 | Index | Tag | Alias 문제 |
|------|-------|-----|-------------|
| **VIVT** | Virtual | Virtual | 두 process 의 같은 VA 가 *다른 PA* 면 충돌 → context switch 마다 flush |
| **VIPT** | Virtual | Physical | Index 비트가 page offset 범위 안이면 alias 없음. 그래서 *cache 크기 ≤ way × page* 제약 |
| **PIPT** | Physical | Physical | Alias 없음. 단, *TLB 먼저 거쳐야* 하므로 latency 추가 |

**현대 L1**: VIPT (alias-free 한 사이즈로 제한). L2+: PIPT.

**왜 "index 가 page offset 안" 이면 alias 가 없나 — VA/PA 가 공유하는 비트.** VIPT 는 _가상 주소(VA)로 index 를 뽑아 set 을 고르면서 동시에 TLB 로 변환해 얻은 물리 주소(PA)로 tag 를 비교_ 하는, 둘을 병렬화한 구조다. 문제는 같은 물리 페이지를 가리키는 서로 다른 VA(aliasing) 가 _다른 set_ 에 들어가면 같은 데이터가 캐시에 두 벌 생겨 일관성이 깨진다는 것이다. 핵심 통찰은 **주소 변환이 page 단위로만 일어난다** 는 점이다 — VA 와 PA 는 _page offset 비트(하위 12 비트, 4 KB 기준)가 항상 동일_ 하고, 변환은 그 위(page number)만 바꾼다. 따라서 index 로 쓰는 비트가 _전부 page offset 범위 안_ 에 들어가면, 그 index 비트들은 VA 든 PA 든 _값이 같다_ — 어떤 VA 로 접근하든 같은 물리 주소는 항상 _같은 set_ 으로 매핑되어 alias 가 원천적으로 생기지 않는다. 반대로 index 가 page offset 경계(비트 12)를 넘어가면, 그 초과 비트는 VA 와 PA 에서 _다를 수 있어_ 같은 PA 가 VA 에 따라 다른 set 으로 흩어진다 — 이것이 alias 다.

이 조건을 식으로 옮긴 것이 §6 Q5 의 `cache_size_per_way ≤ page_size` 다. way 당 크기 = `(set 수) × (line 크기)` 이고, index+offset 비트가 곧 way 당 크기의 로그이므로, "index+offset 가 page offset(12비트) 이내" = "way 당 크기 ≤ page 크기" 와 같은 말이다. 그래서 더 큰 L1 을 원하면 set(=index) 을 늘리는 대신 _way 수_ 를 늘리거나(전체 크기는 키우되 index 비트는 그대로) huge page 로 offset 범위 자체를 넓혀야 한다.

### 5.4 Synchronization Primitives — Hardware 측면

**Synchronization primitive**(동기화 기본 연산 — 여러 코어/스레드가 공유 데이터를 안전하게 다루도록 하드웨어가 제공하는 원자적 명령)들입니다.

- **Test-and-set / xchg** — (값을 읽으면서 동시에 설정하는) atomic. 가장 단순한 lock.
- **CAS (Compare-and-Swap)** — `cmpxchg` (x86), `LDREX/STREX` (ARM). lock-free(잠금 없이 진행) 자료구조 기반.
- **LL/SC (Load-Linked / Store-Conditional)** — ARM, RISC-V. Load 후 동일 주소 store 시 *그 사이* memory 가 변하지 않았다면 성공.
- **Memory barrier (fence)** — (그 지점을 넘어 메모리 접근 순서를 재배치하지 못하게 막는 명령) Reordering 방지. `DMB`, `DSB`, `mfence`.

---

## 6. 샘플 인터뷰 Q&A

<details>
<summary>Q1. (Compute) 32-bit 주소, 64B 라인, 256 KB 4-way 캐시 — tag/index/offset 비트?</summary>

- offset = log2(64) = **6**
- sets = 256K / 64 / 4 = 1024 → index = log2(1024) = **10**
- tag = 32 - 10 - 6 = **16**

</details>
<details>
<summary>Q2. (Trace) 다음 명령 시퀀스의 hazard 와 해결?</summary>

```
I1: LD  r1, [r2]
I2: ADD r3, r1, r4
I3: SUB r5, r3, r6
```
- I1 → I2: **Load-use hazard**. LD 의 결과는 MEM stage 끝에 나옴 → I2 의 EX 입력으로 forward 불가. **1 사이클 stall** + MEM→EX forward.
- I2 → I3: 일반 RAW. EX→EX forward 로 stall 없음.

</details>
<details>
<summary>Q3. (Compare) Inclusive vs Exclusive — snoop coherence 에 어느 게 유리?</summary>

**Inclusive**. L2 만 검색해도 L1 내용을 *반드시* 알 수 있어 *snoop filter* 가 단순. Exclusive 는 L1 / L2 둘 다 검색 → snoop 트래픽 증가.

*단점*: Inclusive 는 L1 의 hot line 이 L2 에서도 차지 → effective cache 작아짐.

</details>
<details>
<summary>Q4. (Explain) Register renaming 이 왜 필요한가?</summary>

Architectural register 가 *재사용* 되면 WAR / WAW false dependency 가 ILP(instruction-level parallelism) 를 막는다.
```
I1: r1 = r2 + r3
I2: r4 = r1 + r5    # I1 -> I2 (true RAW)
I3: r1 = r6 + r7    # I1, I2 가 r1 끝나야 → WAW false dep
```
Renaming 으로 I3 의 r1 을 *physical p17* 같은 새 register 로 매핑 → I1 과 *완전 독립* → 병렬 가능.

</details>
<details>
<summary>Q5. (Apply) VIPT 캐시에서 alias 가 발생하지 않으려면 cache 크기 제약은?</summary>

`cache_size_per_way ≤ page_size` 여야 *index 가 page offset 범위 안* 에 들어 alias 없음.

예: 4 KB page, 4-way cache → way 당 4 KB → 총 cache size ≤ 16 KB.
더 큰 캐시를 원하면 way 수를 늘리거나 page size 를 키워야 한다 (예: huge page).

</details>
---

## 7. 핵심 정리 (Key Takeaways)

1. Cache 주소 분해 = offset + index + tag. 비트 계산은 *반드시* 손으로 풀어볼 것.
2. Hazard 3종 — Structural / Data / Control. Forwarding + Stall + Branch prediction 으로 해결.
3. Tomasulo 의 핵심 = Renaming + RS + CDB + ROB.
4. Branch predictor 는 *gshare → TAGE* 로 진화. RAS 는 ret 예측에 필수.
5. VIPT 는 alias-free 사이즈 제약이 있고, PIPT 는 TLB latency 가 있다.
6. CAS / LL-SC 가 lock-free 자료구조의 하드웨어 기반.

## 8. Further Reading

- *Computer Architecture: A Quantitative Approach* (Hennessy & Patterson) — 정석
- *Modern Processor Design* (Shen & Lipasti) — OoO / 예측 심화
- ARM Cortex-A Programmer's Guide
- [DV SKOOL — Computer Architecture](https://humbleowl39.github.io/DV_SKOOL/computer_architecture/) — ISA·파이프라인·OoO·메모리 계층·성능 법칙 심화 코스
- [DV SKOOL — MMU](https://humbleowl39.github.io/DV_SKOOL/mmu/) — TLB / 페이지 테이블 심화
- [DV SKOOL — Operating Systems (for DV)](https://humbleowl39.github.io/DV_SKOOL/os_for_dv/) — process / scheduling / paging 배경
- [Unit 4 퀴즈](../quiz/04_computer_architecture_quiz/) 로 자기 점검
