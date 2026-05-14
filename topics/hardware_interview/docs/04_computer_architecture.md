# Unit 4 — Computer Architecture / Performance Modeling

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Compute** N-way set associative cache 의 index/tag/offset 비트 폭과 hit/miss 시나리오를 계산한다.
    - **Compare** Von Neumann vs Harvard, RISC vs CISC, 그리고 inclusive vs exclusive cache 의 트레이드오프를 비교한다.
    - **Trace** 5-stage in-order pipeline 에서 data / structural / control hazard 가 어떻게 발생하고 forwarding / stall 이 어떻게 해결하는지 추적한다.
    - **Explain** Tomasulo 알고리즘, register renaming, reorder buffer 의 역할을 설명한다.
    - **Distinguish** bimodal / gshare / TAGE / BTB / RAS 의 동작 차이와 사용처를 구분한다.
    - **Apply** VIPT vs PIPT vs VIVT 의 alias 문제를 분석하고 OS / 하드웨어가 어떻게 대응하는지 설명한다.

!!! info "사전 지식"
    - 디지털 회로, 메모리 계층, [Unit 1](01_digital_rtl.md) 의 파이프라인 개념
    - 운영체제 기본 (process, scheduling, paging)

---

## 1. Cache & Memory Hierarchy

### 1.1 한 줄 그림

```
CPU register (1ns) → L1 (~3ns) → L2 (~10ns) → L3 (~30ns) → DRAM (~100ns) → NVMe (~100us) → HDD (~10ms)
                    [SRAM, on-chip]                       [DDR DRAM]      [Flash]      [Disk]
```

### 1.2 Cache Mapping — 3가지

| 방식 | 한 라인이 갈 수 있는 위치 | Hardware | 충돌 |
|------|--------------------------|----------|------|
| **Direct mapped** | 1 곳 | 단순, 빠름 | 같은 index → 충돌 많음 |
| **N-way set associative** | N 곳 | 가장 흔함 (4/8/16-way) | trade-off |
| **Fully associative** | 어디든 | 복잡, 느림, 비쌈 | 충돌 거의 없음 (TLB 에서 흔함) |

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

| Policy | 동작 | 비용 |
|--------|------|------|
| **LRU** | Least Recently Used eviction | N-way 에서 O(N) 비트 + 갱신 로직 |
| **Pseudo-LRU** | tree 기반 근사 | 비트 적음, hardware 단순 (3-bit per 4-way) |
| **Random** | 무작위 | 가장 단순 |
| **MRU** | 가장 최근 것 eviction (특수) | 스캔 패턴에 유리 |
| **FIFO** | 가장 오래된 것 | LRU 보다 약간 나쁨, hardware 단순 |

### 1.5 Write Policy

- **Write-through** — 항상 RAM 같이 갱신. 다음 레벨 cache 가 항상 최신.
- **Write-back** — Dirty 비트 set, eviction 시에만 RAM 갱신. Bandwidth 절약, coherency 복잡.
- **Write-allocate** — Write miss 시 line 을 가져옴 → 이후 write 는 cache 에.
- **No-write-allocate** — Write miss 는 RAM 에 바로 (cache 안 채움).

조합 — *Write-back + Write-allocate* 가 가장 흔함.

### 1.6 Inclusive vs Exclusive vs NINE

- **Inclusive** — 상위 (L1) 의 모든 데이터가 하위 (L2) 에도 *반드시* 존재. 검색 단순, snooping 효율 ↑. *공간 낭비*.
- **Exclusive** — L1 에 있는 데이터는 L2 에 *없다*. 공간 효율 ↑. AMD 자주 사용.
- **NINE** (Non-Inclusive Non-Exclusive) — 강제 안 함. Intel 흔함.

---

## 2. Architecture Fundamentals

### 2.1 Von Neumann vs Harvard

| 항목 | Von Neumann | Harvard |
|------|-------------|---------|
| Memory | 단일 (instr + data 같이) | 분리 (instr / data 각각) |
| Bus | 단일 → 병목 | 두 개 → 동시 fetch + load/store |
| 사용처 | x86, 범용 PC | DSP, Cortex-M MCU |

**Modified Harvard** — *cache 레벨에서만* 분리 (L1 I-cache + L1 D-cache), main memory 는 통합. 현대 CPU 가 대부분 이 방식.

### 2.2 RISC vs CISC

| 항목 | RISC (ARM, RISC-V, MIPS) | CISC (x86) |
|------|---------------------------|------------|
| Instruction 수 | 적음, 단순 | 많음, 복잡 |
| 길이 | 고정 (32b 또는 16b) | 가변 (1~15 byte) |
| Load/store | 메모리 접근은 load/store 만 | 메모리 직접 연산 가능 |
| Pipeline | 단순 | 복잡 (decoder → uop 변환) |

**현실** — 현대 x86 도 내부적으로 uop(RISC-like) 로 디코드 → 본질적으로 차이 줄어듦.

---

## 3. Pipeline & Execution

### 3.1 5-Stage Classic Pipeline

```
IF (instruction fetch) → ID (decode + register read) → EX (execute / ALU) → MEM (memory access) → WB (write back)
```

### 3.2 Hazard 3종

**1. Structural** — 한 자원을 두 stage 가 동시에 요구.
- 예: 단일 메모리 포트인데 IF (instr fetch) 와 MEM (data load) 가 같은 사이클.
- *해결*: Harvard 캐시 분리, 또는 한 stage stall.

**2. Data** — 이전 명령의 결과를 다음 명령이 *아직 안 끝났을 때* 읽음.

```
I1: ADD r1, r2, r3       # EX 에서 r1 계산
I2: SUB r4, r1, r5       # ID 에서 r1 필요 → I1 의 EX 결과 필요
```

*해결*:
- **Forwarding (bypassing)** — EX 결과를 *다음 사이클 EX 입력* 으로 직접 연결.
- **Stall (bubble)** — Load-use hazard 처럼 forwarding 불가 시.

**3. Control (Branch)** — Branch 의 결과가 EX 에서 정해지면 그 사이 IF 가 잘못된 명령 fetch.

*해결*:
- Branch prediction
- Delay slot (MIPS 의 *최후 수단*)
- Flush + refetch (mispredict 시)

### 3.3 Out-of-Order Execution — Tomasulo

```
[Front-end]
  Fetch → Decode → Rename → Dispatch
                              ↓
                  [Reservation Station] (waiting for operands)
                              ↓ (operand ready)
                          [FU] (ALU, Mem, FP)
                              ↓
                          [CDB] (Common Data Bus broadcast)
                              ↓
                      [ROB] (Reorder Buffer) — in-order commit
```

**핵심**:
- **Register renaming** — architectural register `r1` 을 *내부 physical register* 로 매핑 → WAW / WAR hazard 제거.
- **Reservation Station** — 명령이 *operand 준비될 때까지* 대기, 준비되면 FU 로 issue.
- **CDB** — FU 결과를 모든 RS / ROB 로 broadcast (RS 의 대기 명령이 깨어남).
- **ROB** — *In-order commit* → exception / branch mispredict 시 *깨끗하게 rollback*.

### 3.4 Memory Disambiguation

Load 와 Store 의 주소가 같은지 *모르면* 순서 보존을 위해 stall. **Load forwarding** 또는 **memory dependence predictor** 가 *speculative load*.

---

## 4. Branch Prediction

### 4.1 종류 — 진화 순서

| 종류 | 설명 | 정확도 |
|------|------|--------|
| **Static** | Backward taken, forward not-taken | ~ 70% |
| **Bimodal (2-bit saturating counter)** | 각 PC 마다 *Strongly NT / Weakly NT / Weakly T / Strongly T* | ~ 85% |
| **Local history** | 같은 branch 의 *과거 N번* pattern → counter table 인덱스 | ~ 90% |
| **Gshare** | Global history XOR PC → counter table | ~ 95% |
| **TAGE** | 여러 history 길이의 tag-based 테이블 — *가장 긴 match 사용* | ~ 97%+ (현대 CPU) |
| **Perceptron** | Linear classifier — Intel 일부 | TAGE 와 비슷 |

### 4.2 BTB (Branch Target Buffer)

```
[PC] → [BTB lookup] → predicted target + taken/NT
```

- BTB hit 이면 *target 도 IF stage 에 알려줌* → 곧장 다음 fetch.
- BTB miss 면 decode 까지 가서 target 계산.

### 4.3 RAS (Return Address Stack)

- `call` 시 return address 를 RAS 에 push.
- `ret` 시 RAS pop → 정확한 return prediction (보통 99%+).
- Stack overflow / mismatched call-ret 가 *유일한 mispredict* 원인.

---

## 5. Virtual Memory & OS

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

- **Fully-associative**, 작음 (수십~수백 엔트리).
- **TLB miss** 시 page table walk (수십 사이클).
- **Context switch** 시 TLB flush 필요 (또는 ASID 사용해 process 별 격리).

### 5.3 VIPT vs PIPT vs VIVT

캐시 인덱싱 / 태그를 *가상* 주소로 하느냐 *물리* 로 하느냐:

| 방식 | Index | Tag | Alias 문제 |
|------|-------|-----|-------------|
| **VIVT** | Virtual | Virtual | 두 process 의 같은 VA 가 *다른 PA* 면 충돌 → context switch 마다 flush |
| **VIPT** | Virtual | Physical | Index 비트가 page offset 범위 안이면 alias 없음. 그래서 *cache 크기 ≤ way × page* 제약 |
| **PIPT** | Physical | Physical | Alias 없음. 단, *TLB 먼저 거쳐야* 하므로 latency 추가 |

**현대 L1**: VIPT (alias-free 한 사이즈로 제한). L2+: PIPT.

### 5.4 Synchronization Primitives — Hardware 측면

- **Test-and-set / xchg** — atomic. 가장 단순한 lock.
- **CAS (Compare-and-Swap)** — `cmpxchg` (x86), `LDREX/STREX` (ARM). lock-free 자료구조 기반.
- **LL/SC (Load-Linked / Store-Conditional)** — ARM, RISC-V. Load 후 동일 주소 store 시 *그 사이* memory 가 변하지 않았다면 성공.
- **Memory barrier (fence)** — Reordering 방지. `DMB`, `DSB`, `mfence`.

---

## 6. 샘플 인터뷰 Q&A

??? question "Q1. (Compute) 32-bit 주소, 64B 라인, 256 KB 4-way 캐시 — tag/index/offset 비트?"
    - offset = log2(64) = **6**
    - sets = 256K / 64 / 4 = 1024 → index = log2(1024) = **10**
    - tag = 32 - 10 - 6 = **16**

??? question "Q2. (Trace) 다음 명령 시퀀스의 hazard 와 해결?"
    ```
    I1: LD  r1, [r2]
    I2: ADD r3, r1, r4
    I3: SUB r5, r3, r6
    ```
    - I1 → I2: **Load-use hazard**. LD 의 결과는 MEM stage 끝에 나옴 → I2 의 EX 입력으로 forward 불가. **1 사이클 stall** + MEM→EX forward.
    - I2 → I3: 일반 RAW. EX→EX forward 로 stall 없음.

??? question "Q3. (Compare) Inclusive vs Exclusive — snoop coherence 에 어느 게 유리?"
    **Inclusive**. L2 만 검색해도 L1 내용을 *반드시* 알 수 있어 *snoop filter* 가 단순. Exclusive 는 L1 / L2 둘 다 검색 → snoop 트래픽 증가.

    *단점*: Inclusive 는 L1 의 hot line 이 L2 에서도 차지 → effective cache 작아짐.

??? question "Q4. (Explain) Register renaming 이 왜 필요한가?"
    Architectural register 가 *재사용* 되면 WAR / WAW false dependency 가 ILP(instruction-level parallelism) 를 막는다.
    ```
    I1: r1 = r2 + r3
    I2: r4 = r1 + r5    # I1 -> I2 (true RAW)
    I3: r1 = r6 + r7    # I1, I2 가 r1 끝나야 → WAW false dep
    ```
    Renaming 으로 I3 의 r1 을 *physical p17* 같은 새 register 로 매핑 → I1 과 *완전 독립* → 병렬 가능.

??? question "Q5. (Apply) VIPT 캐시에서 alias 가 발생하지 않으려면 cache 크기 제약은?"
    `cache_size_per_way ≤ page_size` 여야 *index 가 page offset 범위 안* 에 들어 alias 없음.

    예: 4 KB page, 4-way cache → way 당 4 KB → 총 cache size ≤ 16 KB.
    더 큰 캐시를 원하면 way 수를 늘리거나 page size 를 키워야 한다 (예: huge page).

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
- [DV SKOOL — MMU](https://humbleowl39.github.io/DV_SKOOL/mmu/) — TLB / 페이지 테이블 심화
- [Unit 4 퀴즈](quiz/04_computer_architecture_quiz.md) 로 자기 점검
