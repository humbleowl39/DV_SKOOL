# Module 06 — MMU DV Methodology

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🧭</span>
    <span class="chapter-back-text">MMU</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 06</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-검수원-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-한-translation-이-driver-dut-monitor-scoreboard-를-흐르는-경로">3. 작은 예 — TB 흐름 추적</a>
  <a class="page-toc-link" href="#4-일반화-검증-환경-아키텍처-계층-전략">4. 일반화 — 환경 + 계층</a>
  <a class="page-toc-link" href="#5-디테일-thin-vip-ref-model-ral-sva-cr-시퀀스-coverage-ai">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Design** MMU 검증 환경 아키텍처 (Reference Model / Custom VIP / SVA bind / Constrained Random) 를 설계할 수 있다.
    - **Apply** Custom Thin VIP 를 사용해 상용 VIP 의 메모리/성능 한계를 극복하는 시나리오를 작성할 수 있다.
    - **Implement** Dual-Reference Model 로 기능 + 성능을 동시 검증하는 scoreboard 구조를 구현할 수 있다.
    - **Plan** 시나리오 매트릭스 (VA distribution × PTE 구성 × Fault injection) 로 coverage 닫는 전략을 수립할 수 있다.
    - **Critique** SVA bind 패턴으로 RTL 무수정 검증 + Vacuous Pass 방지 cover 짝까지 검토할 수 있다.

!!! info "사전 지식"
    - [Module 01-05](01_mmu_fundamentals.md) MMU 전반
    - [UVM 코스](../../uvm/) — Agent / Sequence / Scoreboard / Coverage
    - [Formal](../../formal_verification/) — SVA 활용

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — 상용 VIP 가 _OOM_

당신은 MMU 검증. 상용 VIP (Cadence / Synopsys) 사용 시도:
- 4 KB granule × 1 GB address range = 250K page entries.
- VIP 내부 모델: page entry 당 _~100 byte_ overhead.
- 250K × 100 = **25 GB RAM**.

대부분 시뮬 환경: _16 GB / job_ 한계. → **OOM**.

해법: **Custom Thin VIP**:
- Page entry 당 _10 byte_ (8x 감소).
- 250K × 10 = 2.5 GB → 16 GB 안에 OK.

또한 _Dual-Reference Model_:
- **Functional**: 모든 PTE 정확히 추적.
- **Ideal**: 최적 TLB / PWC 모델 — DUT 의 _성능 gap_ 자동 측정.

이 _Custom + Dual_ 패턴이 MMU DV 의 _시그니처_. 일반 IP 의 VIP 직접 사용 어려움.

**MMU 검증은 일반 IP 보다 복잡**합니다 — 기능 정확성 (주소 변환) + 성능 (TLB / throughput) + 프로토콜 (AXI / AXI-S) **3 축** 을 _동시_ 검증해야 하고, 상용 VIP 의 메모리 한계 때문에 large-dataset stress 시뮬에서 OOM 이 발생합니다. **Custom Thin VIP + Dual-Reference Model** 이 이 코스의 시그니처 패턴이며, 이력서 / 면접의 핵심 차별화 요소.

또한 _스펙 변경이 잦은_ MMU IP 환경에서 **AI-assisted 환경 자동화** 가 검증 일정을 _설계 일정 앞_ 으로 가져오는 핵심 도구가 됩니다 (DAC 2026). 이 모듈을 마치면 _개념_ 에서 _체계_ 로 — 검증 작업의 reproducibility 와 회귀 자동화가 가능해집니다.

---

## 2. Intuition — 검수원 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **MMU DV** ≈ **주소록 검수원**. 검증 환경은 _golden 주소록_ (reference model) 을 들고 있고, RTL 의 변환 결과를 매번 _같은 입력_ 으로 비교. 거기에 _빠르기_ (Ideal model) 까지 같이 측정. 새 주소록 (스펙 변경) 이 오면 검수원 노트도 자동 업데이트 (AI 자동화).<br>
    **3 축 검증** = "주소가 맞나?" + "얼마나 빨리 줬나?" + "프로토콜대로 줬나?" — 어느 하나만 봐도 검증이 부족.

### 한 장 그림 — MMU UVM Verification Env

```d2
direction: down

ENV: "MMU UVM Verification Env" {
  REQ: "Translation Req Agent\n- Random VA gen\n- Traffic pattern\n  (Seq / Rand / Hot)\n- Burst / Single"
  PT: "Page Table Memory Model\n- Multi-level PT\n- PTE 동적 변경\n- Fault injection\n  (Invalid PTE)"
  VSEQ: "Virtual Sequence\n(시나리오 조합)\n예: Random VA + Huge Page\n+ TLB Full + Page Fault"
  DUT: "DUT (MMU IP)"
  THIN: "Custom Thin VIP (AXI-S)\n- tdata/valid/ready 만\n- 경량 메모리"
  MEM: "Memory Response Model\n- Page Walk 응답\n- 지연 모델링\n- 에러 주입"
  SB: "Dual Scoreboard\n① DUT.PA == FuncModel.PA?\n② DUT.Latency vs IdealModel.Latency\n③ AXI-S handshake compliance"
  COV: "Functional Coverage\n- Translation × Page size × TLB state\n- Miss Ratio × Traffic pattern\n- Fault type × Recovery"
}
REQ -> VSEQ
PT -> VSEQ
VSEQ -> DUT
DUT -> THIN
DUT -> MEM
THIN -> SB
SB -> COV
```

### 왜 이 디자인인가 — Design rationale

세 가지 요구가 동시에 만족돼야 했습니다.

1. **메모리 폭발 회피** — 상용 AXI-S VIP 가 stress 시 GB 단위 메모리 소비 → Custom Thin VIP 으로 tdata/valid/ready 만 구현, 메모리 사용량 100× 절감.
2. **기능과 성능을 동시에** — Single Reference Model 만으로는 "충분히 빠른가?" 를 못 잡음 → Dual (Functional + Ideal) 의 두 reference.
3. **스펙 변경 즉시 대응** — UVM 환경 수동 업데이트는 수일 → AI-assisted 자동 생성으로 _수 시간_.

이 세 요구의 교집합이 위 환경 다이어그램의 _구성 요소 분리_ 와 _scoreboard 의 3 check_ 입니다.

---

## 3. 작은 예 — 한 translation 이 driver → DUT → monitor → scoreboard 를 흐르는 경로

가장 단순한 시나리오. UVM `mmu_basic_trans_seq` 가 1개 transaction 을 생성: `va = 0x4000_1000`, `acc_type = READ`, `asid = 5`. DUT 가 처리, 결과가 dual scoreboard 에서 검증되는 _full path_.

### 단계별 추적

```d2
shape: sequence_diagram

SEQ: "Sequence\n(mmu_basic_trans_seq)"
DRV: "Driver"
DUT: "DUT (MMU IP, RTL)"
MON: "Monitor (passive)"
SB: "Dual Scoreboard"

# Note over SEQ: T0: tr.randomize()\nva=0x4000_1000, asid=5, READ
# Note over DRV: T1: AXI-S 구동\ntdata={va,asid,READ}\ntvalid=1, wait(tready)
# Note over DUT: T2:\n① TLB lookup → miss\n② Page Walk (4 mem read)\n③ Permission OK → PA=0x9_2000\n④ TLB fill\n⑤ resp_valid, lat=42
# Note over MON: T3: capture req/resp\n→ analysis_port
# Note over SB: T4: 3-axis check\n① observed.pa == ref_pa? PASS\n② lat ≤ ideal × K(2.0)?\n   42 ≤ 16? FAIL → uvm_warning\n③ handshake (SVA bind)\ncoverage.sample → CG1/CG2/CG4
SEQ -> DRV: "uvm_seq_item_pull"
DRV -> DUT: "req"
DUT -> MON: "AXI-S response"
MON -> SB: "analysis_port_write"
```

### 단계별 의미

| Step | 누가 | 무엇 | 왜 |
|---|---|---|---|
| T0 | Sequence | tr 생성 + randomize | 시나리오 layer — _무엇을 시키나_ |
| T1 | Driver | AXI-S signal toggling | sequence_item → pin-level |
| T2 | DUT | actual MMU 동작 | 검증 대상 |
| T3 | Monitor | passive sniff + 합성 | RTL 수정 없이 trans 추출 |
| T4 | Scoreboard | 3-way check | _3 axis 동시_ 검증 (정확성 / 성능 / 프로토콜) |

### 만약 Check 1 이 fail 이면? (vs Check 2 fail)

| 시나리오 | 의미 | 다음 액션 |
|---|---|---|
| Check 1 (PA mismatch) | _DUT 의 walk 가 잘못_ — 즉시 stop, log dump | walk engine RTL inspect |
| Check 2 (latency too high) | _DUT 가 정확하나 느림_ — warning, 누적 → 회귀 리포트 | 마이크로아키 분석 (Module 05) |
| Check 3 (protocol violation) | _handshake / valid drop / x-prop_ — uvm_error | SVA bind 의 fail 위치 확인 |

!!! note "여기서 잡아야 할 두 가지"
    **(1) 정확성 fail 은 즉시 stop, 성능 fail 은 누적 회귀** — 두 _다른_ severity 의 fail 을 같은 scoreboard 가 분리 처리. 이게 dual-reference 의 본질입니다. <br>
    **(2) Monitor 는 RTL 을 _수정하지 않고_ pin-level 을 sniff** — 그래서 SVA 도 `bind` 로 외부 모듈에서 연결하는 게 표준. RTL 에 `$display` 또는 assertion 을 inline 하면 _제품 코드가 검증에 오염_ 됨.

---

## 4. 일반화 — 검증 환경 아키텍처 + 계층 전략

### 4.1 계층적 검증 — TLB 서브모듈 → MMU Top

```d2
direction: right

L1: "Level 1: TLB Unit TB\n- TLB Hit/Miss\n- Replacement\n- Invalidation\n- ASID/VMID\n- Multi-size page"
L2: "Level 2: PWE Unit TB\n- Multi-level walk\n- Block Descriptor\n- Walk error\n- Concurrent walks"
L3: "Level 3: MMU Top TB\n- End-to-End flow\n- TLB + PWE 통합\n- 성능 측정\n- Stress test\n- Error recovery"
L1 -> L2
L2 -> L3
```

### 4.2 각 레벨의 검증 초점

| 레벨 | 초점 | 장점 |
|------|------|------|
| TLB 서브모듈 | 캐시 동작 정확성 | 빠른 시뮬레이션, 정밀 디버그 |
| Page Walk Engine | Walk 로직 정확성 | 복잡한 Walk 시나리오 집중 |
| MMU Top | 통합 동작 + 성능 | End-to-End, 실제 시나리오 |

---

## 5. 디테일 — Thin VIP, Ref Model, RAL, SVA, CR 시퀀스, Coverage, AI

### 5.1 Custom "Thin" VIP — 상용 VIP 메모리 문제 해결

#### 문제: 상용 AXI-S VIP 의 메모리 폭발

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

#### 해결: Custom "Thin" VIP

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

#### Thin VIP 설계 원칙

| 원칙 | 적용 | 효과 |
|------|------|------|
| 필수 경로만 | tdata/tvalid/tready | 80% 이상 코드 제거 |
| Bounded 자료구조 | 고정 크기 큐, Sliding Window | 메모리 상한 보장 |
| Lazy Evaluation | 필요 시점에만 프로토콜 검사 | CPU 시간 절약 |
| 선택적 기능 | Config로 기능 ON/OFF | 디버그 시만 활성화 |

**면접 답변 준비**:

**Q: 상용 VIP 를 왜 교체했나?**
> "상용 AXI-S VIP이 고스트레스 Translation 테스트에서 시스템 메모리의 80%를 소비하여 시뮬레이션이 크래시했다. 벤더 지원을 기다리면 Tape-out 일정이 위험해져서 즉각적인 아키텍처 전환이 필요했다. MMU 검증에 필수적인 데이터 경로(tdata, valid, ready)만 처리하는 경량 Custom VIP을 개발하여, 메모리 사용량을 수십 MB로 줄이고 0% 크래시율을 달성했다."

### 5.2 Page Table Reference Model 구현 전략

#### 왜 SW Reference Model 이 필수인가?

```
문제: DUT가 VA=0x1000을 PA=0x8000으로 변환했다. 맞는가?
→ Page Table 내용을 직접 읽어서 Walk을 재현해야 판단 가능
→ SW Reference Model이 동일한 입력에 대해 Golden PA를 계산

핵심: Reference Model = UVM 환경 내에서 Page Table Walk을 SW로 재현
```

#### Reference Model 구조 (Pseudo-code)

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

#### Reference Model 검증 포인트

| 항목 | Model이 정확히 재현해야 하는 것 |
|------|-------------------------------|
| Walk 경로 | 각 레벨 인덱스 추출 + PTE 주소 계산 |
| Block Descriptor | Level 1/2에서 조기 종료 + 올바른 PA 계산 |
| Fault 생성 | Invalid PTE, Permission 위반 시 정확한 Fault 타입 + 레벨 |
| TLB 상태 | Hit/Miss 판정, Replacement 후 상태 일관성 |
| Invalidation | TLB Invalidation 후 해당 엔트리 제거 확인 |

### 5.3 Register Model (MMU CSR 검증)

#### MMU 핵심 레지스터

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

#### UVM RAL 활용 전략

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

### 5.4 SVA Assertions for MMU

#### TLB 관련 Assertions

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

#### Page Walk 관련 Assertions

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

#### 프로토콜 / 핸드셰이크 Assertions

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

### 5.5 Constrained Random 전략

#### VA Randomization

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

#### PTE Randomization (Page Table 구성)

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

### 5.6 UVM Sequence 예제

#### Basic Translation Sequence

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

#### TLB Thrashing Sequence

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

#### Page Fault Injection Sequence

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

#### Virtual Sequence — 시나리오 조합

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

### 5.7 AI-Assisted 환경 자동화 (DAC 2026)

#### 문제: 빈번한 스펙 변경

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

#### 해결: 표준화 템플릿 + AI 자동 생성

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

### 5.8 Coverage Model

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

### 5.9 주요 테스트 시나리오

#### Positive 시나리오

| 시나리오 | 설명 | 검증 포인트 |
|---------|------|-----------|
| Basic Translation | 단일 VA→PA 변환 | 정확한 PA + 권한 |
| Multi-size Page | 4KB, 2MB, 1GB 혼합 | 크기별 변환 정확 |
| TLB Hit/Miss | 반복 접근 + 새 주소 | Hit시 1-cycle, Miss시 Walk |
| ASID 전환 | 같은 VA, 다른 ASID | 각각 다른 PA |
| TLB Invalidation | Invalidate + 재접근 | Miss 발생 + 재캐싱 |
| Concurrent Requests | 동시 다수 요청 | 모두 정확 처리 |

#### Negative / Stress 시나리오

| 시나리오 | 설명 | 검증 포인트 |
|---------|------|-----------|
| Invalid PTE | Valid=0인 PTE 접근 | Page Fault 정확 보고 |
| Permission Violation | Write to RO page | Permission Fault |
| TLB Thrashing | 워킹셋 > TLB 크기 | Miss 폭발, 성능 저하 패턴 확인 |
| Walk Error | 중간 레벨 PTE Invalid | Walk 중단 + Fault |
| Memory Timeout | Walk 중 메모리 무응답 | Timeout + 에러 처리 |
| Max Concurrent | Walk Engine 한계까지 | 백프레셔, 큐 오버플로 없음 |
| Address Boundary | 페이지 경계 걸치는 접근 | 정확한 분리 처리 |

#### 성능 시나리오 (Ideal Model 비교)

| 시나리오 | 트래픽 패턴 | 측정 항목 |
|---------|-----------|----------|
| Streaming DMA | 순차 대량 접근 | Throughput, TLB 재사용률 |
| Random Access | 완전 랜덤 VA | Miss Ratio, Latency P99 |
| Hotspot | 소수 영역 집중 | TLB Hit Rate, 응답 시간 |
| Mixed Workload | 순차+랜덤 혼합 | 종합 성능 |
| Stress (Full Queue) | 최대 동시 요청 | 백프레셔 동작, 처리량 유지 |

### 5.10 면접 종합 Q&A

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

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'MMU DV = TLB 검증 + Page Table walk 검증'"
    **실제**: MMU DV 의 _절반 이상_ 은 fault handling (no perm, no PTE, AF=0, level mismatch), Stage 2 + Stage 1 결합, ASID rotation, TLBI / DSB / ISB 시퀀스 동작, page fault 의 동기/비동기 차이입니다. _가시적인_ TLB hit/miss 가 검증의 중심이 아니라, _보이지 않는_ fault path 와 maintenance op 가 _진짜 버그 모음_.<br>
    **왜 헷갈리는가**: TLB 가 가장 visible 한 지표라서 "검증 = TLB" 로 단축.

!!! danger "❓ 오해 2 — '상용 VIP 가 항상 더 안전하다'"
    **실제**: 상용 VIP 는 _full protocol_ 이라 검증 stress 시 GB 단위 메모리 폭발. 검증 _목표_ 가 protocol compliance 가 아니라 _MMU 동작_ 이면, custom thin VIP 가 _목표 대비 더 안전_ (시뮬 안 죽음). 트레이드오프는 protocol coverage 가 별도 환경 책임이 됨.<br>
    **왜 헷갈리는가**: "상용 = 검증된 것 = 더 안전" 의 일반론.

!!! danger "❓ 오해 3 — 'SVA 만 잘 짜면 functional check 는 불필요하다'"
    **실제**: SVA 는 _temporal property_ 검증에 강하지만 _value-level_ 비교 (DUT.PA == ref_pa) 는 scoreboard 가 더 적합. 또 SVA 만으로는 _coverage closure_ 가 어려움 — vacuous pass (`req` 가 안 들어와서 assertion 이 trivially true) 위험. SVA + scoreboard + cover 의 _조합_ 이 표준.<br>
    **왜 헷갈리는가**: SVA 의 "always true" 의 강한 인상.

!!! danger "❓ 오해 4 — 'Reference model 은 RTL 과 1:1 일치해야 한다'"
    **실제**: 두 종류의 reference 가 _다른 목적_ 에 쓰입니다. **Functional model** 은 RTL 의 _기능_ 과 1:1 (PA 정확). **Ideal performance model** 은 RTL 보다 _빠른_ 이론 상한 (무한 TLB, 0-cycle walk). 둘이 1:1 이면 성능 갭 측정 자체가 불가능.<br>
    **왜 헷갈리는가**: "reference" 라는 단어가 _golden_ 의 의미로 단순화돼서.

!!! danger "❓ 오해 5 — 'Constrained random = 그냥 random. Coverage 가 닫히면 끝'"
    **실제**: "그냥 random" 은 working set 분포가 없어 _hotspot / capacity miss / conflict miss_ 같은 의미 있는 시나리오를 못 만듭니다. CR 의 핵심은 **분포 weighting** + **constraint 의 의도된 conflict** + **hotspot vs random vs stride 의 mix**. Coverage 닫히기 전에 _의도된 패턴_ 이 들어왔는지 봐야 함.<br>
    **왜 헷갈리는가**: random 의 단어 의미가 "치우침 없음" 이라서.

### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 시뮬 메모리 사용량 8 GB 초과 후 crash | 상용 VIP 의 transaction history 무한 큐 | VIP 설정의 buffer size, log retention |
| Functional check 통과인데 P99 가 SLA 초과 | Ideal model 이 너무 느려 (DUT 보다 빠르지 않음) | Ideal model 의 TLB / walk 모델링 (무한 TLB 인지) |
| SVA 가 모두 PASS 인데 RTL 버그 | Vacuous pass — antecedent 가 한 번도 활성화 안 됨 | SVA 의 cover 짝 결과, antecedent hit count |
| Coverage 닫혔는데 RTL 버그 missed | Coverage 모델이 _증상_ 만 cover, _원인_ 누락 | covergroup 의 cross 항목, edge case bins |
| Fault injection 시 scoreboard 가 false negative | ref model 이 fault 를 정확한 type/level 로 안 만듦 | ref model 의 fault encoding (ESR.IFSC/DFSC) |
| 동일 seed 에서 random fail | Sequence 의 ordering 이 simulator-dependent (fork ordering) | fork-join 의 race, `randc` vs `rand` 사용 |
| Spec change 후 모든 test 가 일주일 동안 fail | UVM env 가 spec change 를 자동 반영 안 함 | AI-assisted regen 적용 여부, port mapping 자동화 |
| Stage 2 시나리오에서 ref model 의 PA 가 다름 | ref model 이 Stage 2 walk 미구현 | mmu_ref_model.translate 가 nested walk 처리하는지 |

!!! warning "실무 주의점 — Page Walk 중 중간 레벨 PTE Fault 미검증"
    **현상**: 최하위(L3) PTE는 정상이지만 상위(L1/L2) 테이블 디스크립터의 Valid 비트가 0인 경우, Walk Engine이 올바른 Fault Type(Translation Fault at Level N)을 생성하지 않고 잘못된 PA를 반환하는 버그가 릴리즈까지 미검출.

    **원인**: 대부분의 DV 시나리오가 L3 PTE만 Invalid로 주입하고 중간 레벨 디스크립터 Fault는 커버하지 않음. Walk Engine 구현 버그는 상위 레벨 Fault 발생 시 Fault Level 인코딩을 잘못 보고하거나 스킵하는 형태로 나타남.

    **점검 포인트**: Fault 주입 시나리오에 L0/L1/L2 각각의 `valid=0` 케이스를 독립적으로 포함시키고, ESR_EL1의 `IFSC/DFSC[3:2]` 필드(Fault Level)가 실제 Walk 깊이와 일치하는지 검증.

---

## 7. 핵심 정리 (Key Takeaways)

- **MMU 검증 3 축**: 기능 (주소 변환) + 성능 (TLB / throughput) + 프로토콜 (AXI / AXI-S). 단일 axis 검증으론 부족.
- **Custom Thin VIP 의 동기**: 상용 VIP 의 메모리 부담 (GB 단위 history) → SoC sim OOM. tdata/valid/ready 만 → 100× 메모리 절감.
- **Dual-Reference Model**: 기능 reference (정확한 PA 예측) + 성능 reference (Ideal latency). 둘 다 비교해 회귀 즉시 catch.
- **SVA bind 카테고리**: TLB 동작 (hit / invalidation) + Walk (miss → walk → fill) + 프로토콜 (handshake / fault response). 모두 cover 짝 필수 (vacuous pass 방지).
- **Constrained Random 3 축**: VA 분포 (hotspot / 일반 / 넓음) × PTE 구성 (정상 / invalid / permission) × 시나리오 조합 (대량 + invalidation + fault injection).
- **AI 활용**: spec 변경 시 LLM 으로 sequence / coverage 자동 생성 → 회귀 시간 _수 일 → 수 시간_.

### 7.1 자가 점검

!!! question "🤔 Q1 — Thin VIP 메모리 분석 (Bloom: Apply)"
    상용 VIP: 250K page × 100 B = 25 GB. Thin VIP: 250K × 10 B = 2.5 GB. _10 B 가 어떻게 가능_?

    ??? success "정답"
        Thin VIP 의 _per-page state_:
        - PA (8 byte).
        - Permission flags (1 byte).
        - LRU info (1 byte).

        상용 VIP 가 _100 B_ 인 이유: history (access pattern), full audit trail, statistics, ECC model 등 _DV 무관한_ 부가 정보.

        Thin VIP 는 _필수만_ — 검증 정확도 동일, 메모리 1/10.

!!! question "🤔 Q2 — SVA + Coverage 짝 (Bloom: Evaluate)"
    TLB hit assertion: `assert property (tlb_hit |-> data_valid_next_cycle)`. Cover 가 _hit 0_ 면?

    ??? success "정답"
        **Vacuous pass** — TLB hit 시나리오가 _시뮬에서 발생 안 함_. Assertion 이 _의미 있는 검증_ 못 함.

        대응:
        - Cover 짝: `cover property (tlb_hit)`. Hit rate _최소 1_ 이상.
        - 부족하면 _stimulus 강화_: TLB hit-friendly workload (sequential access) 추가.

        모든 SVA 가 _cover 짝_ 갖고 _hit ≥ 1_ 만 sign-off.

### 7.2 출처

**External**
- *Verification Methodology Manual for SystemVerilog*
- DAC 2026 *AI-assisted MMU Verification* paper

---
## 다음 단계

- 📝 [**Module 06 퀴즈**](quiz/06_mmu_dv_methodology_quiz.md)
- ➡️ [**Module 07 — Quick Reference Card**](07_quick_reference_card.md): 면접 / 디버그 / 코드 리뷰 시 _빠른 참조_ 카드.

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


--8<-- "abbreviations.md"
