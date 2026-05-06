# Module 06 — MMU DV Methodology

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Design** MMU 검증 환경 아키텍처(Reference Model / Custom VIP / SVA bind / Constrained Random)를 설계할 수 있다.
    - **Apply** Custom Thin VIP를 사용해 상용 VIP의 메모리/성능 한계를 극복하는 시나리오를 작성할 수 있다.
    - **Implement** Dual-Reference Model로 기능 + 성능을 동시 검증하는 scoreboard 구조를 구현할 수 있다.
    - **Plan** 시나리오 매트릭스(VA distribution × PTE 구성 × Fault injection)로 coverage 닫는 전략을 수립할 수 있다.
    - **Critique** SVA bind 패턴으로 RTL 무수정 검증 + Vacuous Pass 방지 cover 짝까지 검토할 수 있다.

!!! info "사전 지식"
    - [Module 01-05](01_mmu_fundamentals.md) MMU 전반
    - [UVM 코스](../../uvm/) — Agent / Sequence / Scoreboard / Coverage
    - [Formal](../../formal_verification/) — SVA 활용

## 왜 이 모듈이 중요한가

**MMU 검증은 일반 IP보다 복잡**합니다 — 기능 정확성(주소 변환) + 성능(TLB/throughput) + 프로토콜(AXI/AXI-S) 3축을 동시에 검증해야 하고, 상용 VIP의 메모리 한계로 large dataset 시뮬에서 OOM이 발생합니다. **Custom Thin VIP + Dual-Reference Model**이 이 코스의 시그니처 패턴이며, 이력서/면접의 핵심 차별화 요소입니다.

## 핵심 개념
**MMU 검증 = 기능 정확성(주소 변환) + 성능 검증(TLB/Throughput) + 프로토콜 준수(AXI-S). 상용 VIP의 한계를 Custom VIP으로 극복하고, Dual-Reference Model로 기능과 성능을 동시에 검증하며, AI로 스펙 변경에 즉시 대응하는 것이 핵심.**

---

## 검증 환경 아키텍처

```
+------------------------------------------------------------------+
|                    MMU UVM Verification Env                        |
|                                                                   |
|  +------------------+  +------------------+                       |
|  | Translation Req  |  | Page Table       |                       |
|  | Agent            |  | Memory Model     |                       |
|  |                  |  |                  |                       |
|  | - Random VA gen  |  | - Multi-level PT |                       |
|  | - Traffic pattern|  | - PTE 동적 변경  |                       |
|  |   (Seq/Rand/Hot) |  | - Fault injection|                       |
|  | - Burst/Single   |  |   (Invalid PTE)  |                       |
|  +--------+---------+  +--------+---------+                       |
|           |                      |                                |
|           v                      v                                |
|  +------------------------------------------------------------+  |
|  |              Virtual Sequence (시나리오 조합)                |  |
|  |  예: Random VA + Huge Page + TLB Full + Page Fault          |  |
|  +------------------------------------------------------------+  |
|           |                                                       |
|           v                                                       |
|  +------------------------------------------------------------+  |
|  |                    DUT (MMU IP)                              |  |
|  +------------------------------------------------------------+  |
|           |                      |                                |
|           v                      v                                |
|  +------------------+  +------------------+                       |
|  | Custom "Thin" VIP|  | Memory Response  |                       |
|  | (AXI-S)          |  | Model            |                       |
|  |                  |  |                  |                       |
|  | - tdata/valid/   |  | - Page Walk 응답 |                       |
|  |   ready만 처리   |  | - 지연 모델링    |                       |
|  | - 경량 메모리    |  | - 에러 주입      |                       |
|  +--------+---------+  +------------------+                       |
|           |                                                       |
|           v                                                       |
|  +------------------------------------------------------------+  |
|  |              Dual Scoreboard                                |  |
|  |                                                             |  |
|  |  Functional Check: DUT.PA == FuncModel.PA?                  |  |
|  |  Performance Check: DUT.Latency vs IdealModel.Latency       |  |
|  |  Protocol Check: AXI-S handshake compliance                 |  |
|  +------------------------------------------------------------+  |
|           |                                                       |
|           v                                                       |
|  +------------------------------------------------------------+  |
|  |              Functional Coverage                             |  |
|  |  - Translation type × Page size × TLB state                |  |
|  |  - Miss Ratio bins × Traffic pattern                        |  |
|  |  - Fault type × Recovery                                    |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

---

## Custom "Thin" VIP — 상용 VIP 메모리 문제 해결

### 문제: 상용 AXI-S VIP의 메모리 폭발

```
상용 VIP 문제:

  고스트레스 Translation 요청 테스트 시:
  - 상용 AXI-S VIP이 시스템 메모리의 80% 이상 소비
  - 시뮬레이션 크래시 및 Stall 빈발
  - 벤더 지원 대기 → Tape-out 일정 위협

  근본 원인:
  - 상용 VIP은 풀 프로토콜 스택을 시뮬레이션
  - AXI-S의 모든 채널, 에러 케이스, 프로토콜 체커 포함
  - 고스트레스 시 내부 큐와 히스토리 버퍼가 메모리 폭발
```

### 해결: Custom "Thin" VIP

```
설계 철학: MMU 검증에 필수적인 데이터 경로만 구현

  상용 VIP (Full Stack):
  +--------------------------------------------------+
  | AXI-S Full Protocol                               |
  | - 모든 채널 (AW/W/B/AR/R)                         |
  | - OOO (Out-of-Order) 관리                         |
  | - Protocol checker (200+ rules)                   |
  | - Coverage collector                               |
  | - Error injection engine                           |
  | - Transaction history (무한 큐)                    |
  | 메모리: ~수 GB (고스트레스 시)                      |
  +--------------------------------------------------+

  Custom "Thin" VIP:
  +--------------------------------------------------+
  | AXI-S Essential Path Only                          |
  | - tdata, tvalid, tready만 처리                     |
  | - 고정 크기 버퍼 (bounded queue)                   |
  | - 필수 핸드셰이크 체크만                           |
  | - 트랜잭션 히스토리 제한 (sliding window)          |
  | 메모리: ~수십 MB (고스트레스에서도 안정)            |
  +--------------------------------------------------+
```

### Thin VIP 설계 원칙

| 원칙 | 적용 | 효과 |
|------|------|------|
| 필수 경로만 | tdata/tvalid/tready | 80% 이상 코드 제거 |
| Bounded 자료구조 | 고정 크기 큐, Sliding Window | 메모리 상한 보장 |
| Lazy Evaluation | 필요 시점에만 프로토콜 검사 | CPU 시간 절약 |
| 선택적 기능 | Config로 기능 ON/OFF | 디버그 시만 활성화 |

**면접 답변 준비**:

**Q: 상용 VIP를 왜 교체했나?**
> "상용 AXI-S VIP이 고스트레스 Translation 테스트에서 시스템 메모리의 80%를 소비하여 시뮬레이션이 크래시했다. 벤더 지원을 기다리면 Tape-out 일정이 위험해져서 즉각적인 아키텍처 전환이 필요했다. MMU 검증에 필수적인 데이터 경로(tdata, valid, ready)만 처리하는 경량 Custom VIP을 개발하여, 메모리 사용량을 수십 MB로 줄이고 0% 크래시율을 달성했다."

---

## 계층적 검증 전략 — TLB 서브모듈 → MMU Top

### 검증 계층

```
Level 1: TLB 서브모듈 검증
  +-------------------+
  | TLB Unit TB       |
  |                   |
  | - TLB Hit/Miss    |
  | - Replacement     |
  | - Invalidation    |
  | - ASID/VMID       |
  | - Multi-size page |
  +-------------------+

Level 2: Page Walk Engine 검증
  +-------------------+
  | PWE Unit TB       |
  |                   |
  | - Multi-level walk|
  | - Block Descriptor|
  | - Walk error      |
  | - Concurrent walks|
  +-------------------+

Level 3: MMU Top-level 검증
  +-------------------+
  | MMU Top TB        |
  |                   |
  | - End-to-End flow |
  | - TLB + PWE 통합  |
  | - 성능 측정       |
  | - Stress test     |
  | - Error recovery  |
  +-------------------+
```

### 각 레벨의 검증 초점

| 레벨 | 초점 | 장점 |
|------|------|------|
| TLB 서브모듈 | 캐시 동작 정확성 | 빠른 시뮬레이션, 정밀 디버그 |
| Page Walk Engine | Walk 로직 정확성 | 복잡한 Walk 시나리오 집중 |
| MMU Top | 통합 동작 + 성능 | End-to-End, 실제 시나리오 |

---

## Page Table Reference Model 구현 전략

### 왜 SW Reference Model이 필수인가?

```
문제: DUT가 VA=0x1000을 PA=0x8000으로 변환했다. 맞는가?
→ Page Table 내용을 직접 읽어서 Walk을 재현해야 판단 가능
→ SW Reference Model이 동일한 입력에 대해 Golden PA를 계산

핵심: Reference Model = UVM 환경 내에서 Page Table Walk을 SW로 재현
```

### Reference Model 구조 (Pseudo-code)

```systemverilog
class mmu_ref_model extends uvm_component;

  // Page Table을 associative array로 모델링
  // key = 물리 주소, value = PTE 값
  bit [63:0] page_table_mem [bit [47:0]];

  // TLB 모델 (Functional Model용)
  tlb_entry_t tlb_cache[$];  // bounded queue
  int unsigned tlb_capacity = 128;

  // 주소 변환 함수 — 4-level Page Walk 재현
  function mmu_result_t translate(bit [47:0] va, asid_t asid);
    mmu_result_t result;

    // Step 1: TLB Lookup
    if (tlb_lookup(va, asid, result)) begin
      result.source = TLB_HIT;
      return result;
    end

    // Step 2: Page Walk (L0 → L1 → L2 → L3)
    bit [47:0] table_base = ttbr_reg;  // TTBR에서 시작

    for (int level = 0; level < 4; level++) begin
      bit [8:0] index = extract_index(va, level);  // VA에서 9-bit 인덱스 추출
      bit [47:0] pte_addr = table_base + (index * 8);
      bit [63:0] pte = page_table_mem[pte_addr];

      // Valid 체크
      if (!pte[0]) begin
        result.fault = PAGE_FAULT_INVALID;
        result.fault_level = level;
        return result;
      end

      // Block Descriptor 체크 (Level 1/2에서 조기 종료)
      if (level < 3 && pte[1] == 0) begin  // Block
        result.pa = extract_block_pa(pte, va, level);
        result.attrs = extract_attrs(pte);
        break;
      end

      // Table Descriptor → 다음 레벨
      if (level < 3)
        table_base = {pte[47:12], 12'b0};
      else  // Level 3: Page Descriptor
        result.pa = {pte[47:12], va[11:0]};
    end

    // Step 3: Permission Check
    if (!check_permission(result.attrs, access_type))
      result.fault = PAGE_FAULT_PERMISSION;

    // Step 4: TLB 캐싱
    if (result.fault == NO_FAULT)
      tlb_insert(va, asid, result);

    result.source = PAGE_WALK;
    return result;
  endfunction

endclass
```

### Reference Model 검증 포인트

| 항목 | Model이 정확히 재현해야 하는 것 |
|------|-------------------------------|
| Walk 경로 | 각 레벨 인덱스 추출 + PTE 주소 계산 |
| Block Descriptor | Level 1/2에서 조기 종료 + 올바른 PA 계산 |
| Fault 생성 | Invalid PTE, Permission 위반 시 정확한 Fault 타입 + 레벨 |
| TLB 상태 | Hit/Miss 판정, Replacement 후 상태 일관성 |
| Invalidation | TLB Invalidation 후 해당 엔트리 제거 확인 |

---

## Register Model (MMU CSR 검증)

### MMU 핵심 레지스터

```
MMU 동작을 제어하는 시스템 레지스터 (ARMv8 기준):

+----------+----------------------------------------------+
| SCTLR_EL1| bit[0] M = MMU Enable/Disable                |
|          | bit[2] C = Data Cache Enable                 |
|          | bit[12] I = Instruction Cache Enable          |
+----------+----------------------------------------------+
| TTBR0_EL1| Translation Table Base Register 0             |
|          | [47:1] BADDR = Level 0 Table 물리 주소        |
|          | [63:48] ASID (ASID 16-bit 모드 시)            |
+----------+----------------------------------------------+
| TTBR1_EL1| 커널 주소 공간용 Table Base (VA 상위 비트 = 1)  |
+----------+----------------------------------------------+
| TCR_EL1  | Translation Control Register                  |
|          | T0SZ/T1SZ: VA 크기 설정                       |
|          | TG0/TG1: Granule 크기 (4KB/16KB/64KB)         |
|          | SH/ORGN/IRGN: Shareability + 캐시 속성         |
+----------+----------------------------------------------+
| MAIR_EL1 | Memory Attribute Indirection Register          |
|          | 8개 Attr 슬롯 (PTE의 AttrIdx가 참조)          |
+----------+----------------------------------------------+
```

### UVM RAL 활용 전략

```
UVM Register Model 활용:

  1. 레지스터 정의 → uvm_reg 클래스
  2. 레지스터 블록 → uvm_reg_block (MMU CSR 그룹)
  3. Adapter → Front-door (AXI/APB) 또는 Back-door (HDL path)

검증 포인트:
  - SCTLR.M = 0 → MMU Bypass (VA = PA)
  - SCTLR.M = 1 → MMU Enable (정상 변환)
  - TTBR 변경 → Page Walk이 새 Table Base 사용
  - TCR.TG0 변경 → Granule 크기 반영
  - 잘못된 TCR 설정 → 예측 가능한 에러 동작
```

---

## SVA Assertions for MMU

### TLB 관련 Assertions

```systemverilog
// 1. TLB Hit 시 1-cycle 응답 보장
property p_tlb_hit_latency;
  @(posedge clk) disable iff (!rst_n)
  (req_valid && tlb_hit) |-> ##1 resp_valid;
endproperty
a_tlb_hit_latency: assert property (p_tlb_hit_latency)
  else `uvm_error("SVA", "TLB Hit but response not in 1 cycle")
c_tlb_hit_latency: cover property (p_tlb_hit_latency);

// 2. TLB Invalidation 후 같은 VA → 반드시 Miss
property p_inv_then_miss;
  @(posedge clk) disable iff (!rst_n)
  (tlb_inv_valid && tlb_inv_va == $past(req_va))
  |-> ##[1:$] (req_valid && req_va == tlb_inv_va) |-> !tlb_hit;
endproperty
a_inv_then_miss: assert property (p_inv_then_miss)
  else `uvm_error("SVA", "Stale TLB entry after invalidation")
c_inv_then_miss: cover property (p_inv_then_miss);

// 3. TLB 엔트리 수가 최대 용량을 초과하지 않음
property p_tlb_no_overflow;
  @(posedge clk) disable iff (!rst_n)
  tlb_entry_count <= TLB_MAX_ENTRIES;
endproperty
a_tlb_no_overflow: assert property (p_tlb_no_overflow);
```

### Page Walk 관련 Assertions

```systemverilog
// 4. TLB Miss → Page Walk 시작 (N cycle 이내)
property p_miss_triggers_walk;
  @(posedge clk) disable iff (!rst_n)
  (req_valid && !tlb_hit) |-> ##[1:MAX_WALK_START_DELAY] pw_start;
endproperty
a_miss_triggers_walk: assert property (p_miss_triggers_walk);
c_miss_triggers_walk: cover property (p_miss_triggers_walk);

// 5. Page Walk 완료 후 TLB에 캐싱 (Fault 아닌 경우)
property p_walk_done_tlb_fill;
  @(posedge clk) disable iff (!rst_n)
  (pw_done && !pw_fault) |-> ##[1:2] tlb_write_valid;
endproperty
a_walk_done_tlb_fill: assert property (p_walk_done_tlb_fill);

// 6. Page Walk 중 메모리 요청은 최대 4회 (4-level)
property p_walk_max_mem_access;
  @(posedge clk) disable iff (!rst_n)
  pw_start |-> ##[1:$] pw_done throughout (pw_mem_access_count <= 4);
endproperty
```

### 프로토콜 / 핸드셰이크 Assertions

```systemverilog
// 7. valid-ready 핸드셰이크: valid 올리면 ready 전까지 유지
property p_valid_until_ready;
  @(posedge clk) disable iff (!rst_n)
  (req_valid && !req_ready) |=> req_valid;
endproperty
a_valid_until_ready: assert property (p_valid_until_ready)
  else `uvm_error("SVA", "req_valid dropped before ready")

// 8. Fault 발생 시 반드시 Fault 응답 생성
property p_fault_reported;
  @(posedge clk) disable iff (!rst_n)
  (pw_done && pw_fault) |-> ##[1:3] (resp_valid && resp_fault);
endproperty
a_fault_reported: assert property (p_fault_reported);
c_fault_reported: cover property (p_fault_reported);
```

**DV 활용**: 위 SVA들은 bind module로 DUT 외부에서 연결하여, RTL 수정 없이 검증한다. 모든 assert에 대응하는 cover를 두어 assertion이 실제로 활성화되었는지 확인한다.

---

## Constrained Random 전략

### VA Randomization

```systemverilog
class mmu_trans extends uvm_sequence_item;

  // VA 랜덤화 — 의미 있는 분포 생성
  rand bit [47:0] va;
  rand page_size_e page_size;    // {KB4, MB2, GB1}
  rand access_type_e acc_type;   // {READ, WRITE, EXECUTE}
  rand bit [15:0] asid;

  // 제약 1: Page-aligned VA
  constraint c_page_aligned {
    page_size == KB4 -> va[11:0] == 0;
    page_size == MB2 -> va[20:0] == 0;
    page_size == GB1 -> va[29:0] == 0;
  }

  // 제약 2: 워킹셋 크기 제어 (TLB Thrashing 조절)
  rand int unsigned working_set_pages;
  constraint c_working_set {
    working_set_pages inside {[1:16], [64:128], [256:1024]};
    // 소수 = TLB 내 유지, 중간 = TLB 경계, 대량 = Thrashing 유발
  }

  // 제약 3: VA 분포 — Hotspot + Random 혼합
  constraint c_va_distribution {
    va dist {
      [48'h0000_0000_0000 : 48'h0000_0000_FFFF] := 60,  // Hotspot (하위 64KB)
      [48'h0000_0001_0000 : 48'h0000_FFFF_FFFF] := 30,  // 일반 범위
      [48'h0001_0000_0000 : 48'hFFFF_FFFF_FFFF] := 10   // 넓은 범위 (Capacity Miss 유발)
    };
  }

  // 제약 4: Page 크기 분포
  constraint c_page_size_dist {
    page_size dist { KB4 := 70, MB2 := 25, GB1 := 5 };
  }

endclass
```

### PTE Randomization (Page Table 구성)

```systemverilog
class mmu_pt_config extends uvm_object;

  rand bit [63:0] pte_template;
  rand fault_inject_e fault_mode;  // {NONE, INVALID, PERM_VIOLATION, AF_CLEAR}

  // 정상 PTE vs Fault 주입 비율
  constraint c_fault_ratio {
    fault_mode dist { NONE := 85, INVALID := 5, PERM_VIOLATION := 7, AF_CLEAR := 3 };
  }

  // Permission 조합 커버리지 유도
  constraint c_perm_variety {
    pte_template[7:6] dist { 2'b00 := 30, 2'b01 := 30, 2'b10 := 20, 2'b11 := 20 };
  }

endclass
```

---

## UVM Sequence 예제

### Basic Translation Sequence

```systemverilog
class mmu_basic_trans_seq extends uvm_sequence #(mmu_trans);

  `uvm_object_utils(mmu_basic_trans_seq)

  rand int unsigned num_trans;
  constraint c_num { num_trans inside {[100:500]}; }

  task body();
    mmu_trans tr;
    repeat (num_trans) begin
      tr = mmu_trans::type_id::create("tr");
      start_item(tr);
      if (!tr.randomize() with {
        acc_type != EXECUTE;  // 기본: Read/Write만
        page_size == KB4;     // 기본: 4KB Page
      }) `uvm_fatal("SEQ", "Randomization failed")
      finish_item(tr);
    end
  endtask

endclass
```

### TLB Thrashing Sequence

```systemverilog
class mmu_tlb_thrash_seq extends uvm_sequence #(mmu_trans);

  `uvm_object_utils(mmu_tlb_thrash_seq)

  rand int unsigned tlb_size;       // DUT TLB 크기 (config_db에서 가져옴)
  rand int unsigned overshoot_factor; // TLB 대비 몇 배의 워킹셋

  constraint c_overshoot { overshoot_factor inside {[2:4]}; }

  task body();
    int unsigned num_unique_pages = tlb_size * overshoot_factor;
    bit [47:0] va_pool[];

    // Phase 1: 고유 VA 풀 생성
    va_pool = new[num_unique_pages];
    foreach (va_pool[i])
      va_pool[i] = i * 48'h1000;  // 4KB 간격

    // Phase 2: 랜덤 순서로 반복 접근 → TLB Thrashing 유도
    repeat (num_unique_pages * 3) begin
      mmu_trans tr = mmu_trans::type_id::create("tr");
      start_item(tr);
      if (!tr.randomize() with {
        va == va_pool[$urandom_range(0, num_unique_pages-1)];
      }) `uvm_fatal("SEQ", "Randomization failed")
      finish_item(tr);
    end
  endtask

endclass
```

### Page Fault Injection Sequence

```systemverilog
class mmu_fault_inject_seq extends uvm_sequence #(mmu_trans);

  `uvm_object_utils(mmu_fault_inject_seq)

  mmu_pt_config pt_cfg;  // Page Table 설정 핸들

  task body();
    // Phase 1: 정상 매핑으로 Baseline 확인
    repeat (20) begin
      mmu_trans tr = mmu_trans::type_id::create("tr");
      start_item(tr);
      if (!tr.randomize() with { va inside {[0:48'hFFFF]}; })
        `uvm_fatal("SEQ", "Randomization failed")
      finish_item(tr);
    end

    // Phase 2: Page Table에 Invalid PTE 주입
    pt_cfg.inject_invalid_pte(target_va);  // 특정 VA의 PTE를 Invalid로 변경

    // Phase 3: Invalid VA 접근 → Fault 발생 확인
    begin
      mmu_trans tr = mmu_trans::type_id::create("tr");
      start_item(tr);
      tr.va = target_va;
      tr.acc_type = READ;
      finish_item(tr);
      // Scoreboard에서 Fault 응답 검증
    end

    // Phase 4: PTE 복구 후 정상 접근 확인
    pt_cfg.restore_pte(target_va);
    // TLB Invalidation 필요!
    send_tlb_invalidate(target_va);

    begin
      mmu_trans tr = mmu_trans::type_id::create("tr");
      start_item(tr);
      tr.va = target_va;
      finish_item(tr);
      // Scoreboard에서 정상 PA 응답 검증
    end
  endtask

endclass
```

### Virtual Sequence — 시나리오 조합

```systemverilog
class mmu_stress_vseq extends uvm_sequence;

  `uvm_object_utils(mmu_stress_vseq)

  task body();
    mmu_basic_trans_seq   basic_seq;
    mmu_tlb_thrash_seq    thrash_seq;
    mmu_fault_inject_seq  fault_seq;

    // 병렬 실행: Translation + Invalidation 동시 발생
    fork
      begin  // Thread 1: 대량 Translation
        basic_seq = mmu_basic_trans_seq::type_id::create("basic");
        basic_seq.start(p_sequencer.trans_sqr);
      end
      begin  // Thread 2: 주기적 TLB Invalidation
        repeat (10) begin
          #($urandom_range(100, 500));  // 랜덤 간격
          send_tlb_invalidate_all();
        end
      end
      begin  // Thread 3: 간헐적 Fault 주입
        fault_seq = mmu_fault_inject_seq::type_id::create("fault");
        fault_seq.start(p_sequencer.trans_sqr);
      end
    join
  endtask

endclass
```

---

## AI-Assisted 환경 자동화 (DAC 2026)

### 문제: 빈번한 스펙 변경

```
Agile 개발에서의 MMU 스펙 변경:

  Week 1: TLB 크기 64 → 128 엔트리
  Week 2: AXI-S 인터페이스 포트 추가
  Week 3: Page Walk Engine 파이프라인 변경
  Week 4: 새로운 에러 코드 추가

  전통적 대응:
  - 매번 UVM 환경 수동 업데이트 → 수 일 소요
  - 스펙이 설계보다 빨리 변경 → 검증이 설계를 따라가지 못함
```

### 해결: 표준화 템플릿 + AI 자동 생성

```
+--------------------------------------------------+
|  UVM Environment Template (표준화)                |
|                                                   |
|  1. Interface Definition (JSON/YAML)              |
|     - Port name, direction, width                 |
|     - Protocol type (AXI-S, AXI, custom)         |
|                                                   |
|  2. AI Code Assistant                             |
|     - 인터페이스 정의 → UVM Agent 자동 생성       |
|     - Port 변경 감지 → Driver/Monitor 자동 업데이트|
|     - 새 에러 코드 → Checker 자동 확장            |
|                                                   |
|  결과:                                            |
|     스펙 변경 대응: 수 일 → 수 시간                |
|     "Zero-day latency" in spec response           |
+--------------------------------------------------+
```

---

## Coverage Model

### MMU Functional Coverage

```
[CG1] Translation Coverage
  - cp_page_size:     {4KB, 2MB, 1GB}
  - cp_access_type:   {READ, WRITE, EXECUTE}
  - cp_privilege:     {EL0, EL1, EL2}
  - cp_result:        {SUCCESS, FAULT}
  - cross: page_size × access_type × privilege × result

[CG2] TLB Coverage
  - cp_tlb_state:     {EMPTY, PARTIAL, FULL}
  - cp_lookup_result: {L1_HIT, L2_HIT, MISS}
  - cp_replacement:   {LRU_EVICT, RANDOM_EVICT}
  - cp_invalidation:  {ALL, VA, ASID, VMID}
  - cross: tlb_state × lookup_result

[CG3] Page Walk Coverage
  - cp_walk_depth:    {L0_BLOCK, L1_BLOCK, L2_BLOCK, L3_PAGE}
  - cp_walk_error:    {NONE, INVALID_PTE, PERMISSION, ACCESS_FLAG}
  - cp_concurrent:    {SINGLE, DUAL, MAX_CONCURRENT}
  - cross: walk_depth × walk_error

[CG4] Performance Coverage
  - cp_miss_ratio_bin: {<0.1%, 0.1-1%, 1-5%, 5-10%, >10%}
  - cp_latency_bin:    {1-2cyc, 3-5cyc, 6-20cyc, >20cyc}
  - cp_throughput_bin: {>0.9, 0.7-0.9, 0.5-0.7, <0.5} req/cycle
  - cp_traffic_pattern:{SEQUENTIAL, STRIDE, RANDOM, HOTSPOT}
  - cross: miss_ratio_bin × traffic_pattern

[CG5] Error/Edge Case Coverage
  - cp_fault_type:    {INVALID, PERMISSION, ALIGNMENT, SIZE}
  - cp_recovery:      {FAULT_REPORTED, RETRY_SUCCESS}
  - cp_edge:          {ADDR_BOUNDARY, MAX_VA, ZERO_VA, WRAP}
```

---

## 주요 테스트 시나리오

### Positive 시나리오

| 시나리오 | 설명 | 검증 포인트 |
|---------|------|-----------|
| Basic Translation | 단일 VA→PA 변환 | 정확한 PA + 권한 |
| Multi-size Page | 4KB, 2MB, 1GB 혼합 | 크기별 변환 정확 |
| TLB Hit/Miss | 반복 접근 + 새 주소 | Hit시 1-cycle, Miss시 Walk |
| ASID 전환 | 같은 VA, 다른 ASID | 각각 다른 PA |
| TLB Invalidation | Invalidate + 재접근 | Miss 발생 + 재캐싱 |
| Concurrent Requests | 동시 다수 요청 | 모두 정확 처리 |

### Negative / Stress 시나리오

| 시나리오 | 설명 | 검증 포인트 |
|---------|------|-----------|
| Invalid PTE | Valid=0인 PTE 접근 | Page Fault 정확 보고 |
| Permission Violation | Write to RO page | Permission Fault |
| TLB Thrashing | 워킹셋 > TLB 크기 | Miss 폭발, 성능 저하 패턴 확인 |
| Walk Error | 중간 레벨 PTE Invalid | Walk 중단 + Fault |
| Memory Timeout | Walk 중 메모리 무응답 | Timeout + 에러 처리 |
| Max Concurrent | Walk Engine 한계까지 | 백프레셔, 큐 오버플로 없음 |
| Address Boundary | 페이지 경계 걸치는 접근 | 정확한 분리 처리 |

### 성능 시나리오 (Ideal Model 비교)

| 시나리오 | 트래픽 패턴 | 측정 항목 |
|---------|-----------|----------|
| Streaming DMA | 순차 대량 접근 | Throughput, TLB 재사용률 |
| Random Access | 완전 랜덤 VA | Miss Ratio, Latency P99 |
| Hotspot | 소수 영역 집중 | TLB Hit Rate, 응답 시간 |
| Mixed Workload | 순차+랜덤 혼합 | 종합 성능 |
| Stress (Full Queue) | 최대 동시 요청 | 백프레셔 동작, 처리량 유지 |

---

## 면접 종합 Q&A

**Q: MMU 검증 환경을 어떻게 설계했나?**
> "계층적으로 설계했다. TLB 서브모듈 TB로 캐시 동작을 정밀 검증하고, MMU Top TB로 End-to-End 통합 동작과 성능을 검증했다. 핵심은 세 가지: (1) Custom Thin VIP — 상용 VIP의 메모리 폭발 문제를 해결하여 고스트레스 테스트를 안정화. (2) Dual-Reference Model — Functional Model로 정확성, Ideal Model로 성능 기준을 동시에 검증. (3) AI-Assisted 자동화 — 빈번한 스펙 변경에 수 시간 내 대응."

**Q: 상용 VIP 대신 Custom VIP을 만든 이유와 트레이드오프는?**
> "상용 VIP이 고스트레스 시 80% 메모리를 소비하여 크래시가 발생했고, 벤더 지원 대기는 Tape-out을 위협했다. Custom VIP은 tdata/valid/ready 핵심 경로만 구현하여 메모리를 수십 MB로 줄였다. 트레이드오프: 풀 프로토콜 체커가 없으므로 프로토콜 준수 검증은 별도 환경(또는 린트)에서 수행해야 한다. 그러나 MMU 기능/성능 검증이라는 핵심 목표에는 영향 없었다."

**Q: TLB 성능 병목을 어떻게 발견하고 해결했나?**
> "Ideal Performance Model과 DUT를 비교하여 TLB Miss Ratio가 이론치의 수 배인 것을 발견했다. 3C 분석(Compulsory/Capacity/Conflict)으로 원인을 분류한 결과, 특정 트래픽 패턴에서 Capacity Miss가 과도하게 발생하고 있었다. 마이크로아키텍처 분석으로 교체 정책과 TLB 구조의 비효율을 특정하여 설계팀에 피드백했고, 서버급 처리량 요구사항을 충족시켰다."

**Q: 빈번한 스펙 변경에 어떻게 대응했나?**
> "표준화된 UVM 환경 템플릿을 설계하고, AI 코드 어시스턴트를 활용하여 인터페이스 정의 변경 시 UVM 컴포넌트를 자동으로 재생성했다. 스펙 변경 대응 시간을 수 일에서 수 시간으로 단축하여, 검증 일정이 설계보다 앞서가도록 유지했다. 이 방법론은 2026 DAC에 제출했다."

**Q: MMU Reference Model을 어떻게 구현했나?**
> "UVM 환경 내에서 SW로 4-level Page Walk을 재현하는 Reference Model을 구현했다. Page Table을 associative array로 모델링하고, DUT와 동일한 인덱스 추출 → PTE 읽기 → Permission 체크 → TLB 캐싱 흐름을 거쳐 Golden PA를 계산한다. Functional Model은 DUT와 동일한 TLB 크기/정책으로 비트 정확한 비교를, Ideal Model은 무한 TLB로 성능 상한 기준을 제공한다."

**Q: MMU 검증에서 SVA를 어떻게 활용했나?**
> "세 가지 카테고리의 SVA를 bind module로 연결했다: (1) TLB 동작 — Hit 시 1-cycle 응답, Invalidation 후 반드시 Miss 발생. (2) Page Walk — Miss 후 Walk 시작 보장, Walk 완료 후 TLB fill, 메모리 접근 최대 4회. (3) 프로토콜 — valid-ready 핸드셰이크 유지, Fault 시 Fault 응답 생성. 모든 assert에 대응하는 cover를 두어 assertion이 실제로 활성화되었는지까지 확인했다."

**Q: Constrained Random으로 어떤 시나리오를 만들었나?**
> "세 가지 축으로 랜덤화했다: (1) VA 분포 — Hotspot(60%), 일반 범위(30%), 넓은 범위(10%)로 가중하여 실제 트래픽 패턴을 모사. (2) Page Table 구성 — 정상 PTE 85%, Invalid 5%, Permission 위반 7%, AF 미설정 3%로 Fault 주입. (3) 시나리오 조합 — 대량 Translation + 주기적 TLB Invalidation + 간헐적 Fault 주입을 병렬로 실행하여 실제 운영 환경의 복잡한 상호작용을 검증했다."

---

## 핵심 정리

- **MMU 검증 3축**: 기능(주소 변환) + 성능(TLB/throughput) + 프로토콜(AXI/AXI-S). 단일 axis 검증으론 부족.
- **Custom Thin VIP의 동기**: 상용 VIP의 메모리 부담(GB 단위 page table) → SoC 시뮬 OOM. Sparse 표현으로 100x 메모리 절감.
- **Dual-Reference Model**: 기능 reference (정확한 PA 예측) + 성능 reference (Ideal latency). 둘 다 비교해 회귀 즉시 catch.
- **SVA bind 카테고리**: TLB 동작 (hit/invalidation) + Walk (miss → walk → fill) + 프로토콜 (handshake / fault response). 모두 cover 짝.
- **Constrained Random 3축**: VA 분포 (hotspot/일반/넓음) × PTE 구성 (정상/invalid/permission) × 시나리오 조합 (대량 + invalidation + fault injection).
- **AI 활용**: spec 변경 시 LLM으로 sequence/coverage 자동 생성 → 회귀 시간 단축.

## 다음 단계

- 📝 [**Module 06 퀴즈**](quiz/06_mmu_dv_methodology_quiz.md)
- ➡️ [**Module 07 — Quick Reference Card**](07_quick_reference_card.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../05_performance_analysis/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">MMU 성능 분석 및 최적화</div>
  </a>
  <a class="nav-next" href="../07_quick_reference_card/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">MMU — Quick Reference Card</div>
  </a>
</div>
