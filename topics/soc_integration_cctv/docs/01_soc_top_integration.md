# Module 01 — SoC Top Integration

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🏗️</span>
    <span class="chapter-back-text">SoC Integration</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 01</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#ip-검증-vs-soc-top-검증">IP 검증 vs SoC Top 검증</a>
  <a class="page-toc-link" href="#soc-top-검증-항목">SoC Top 검증 항목</a>
  <a class="page-toc-link" href="#soc-top-tb-아키텍처-이력서-연결">SoC Top TB 아키텍처 (이력서 연결)</a>
  <a class="page-toc-link" href="#코드-예시-connectivity-검증-sva">코드 예시: Connectivity 검증 SVA</a>
  <a class="page-toc-link" href="#코드-예시-memory-map-검증-uvm-sequence">코드 예시: Memory Map 검증 UVM Sequence</a>
  <a class="page-toc-link" href="#실전-디버그-시나리오-interrupt-라우팅-오류">실전 디버그 시나리오: Interrupt 라우팅 오류</a>
  <a class="page-toc-link" href="#soc-top-tb의-uvm-env-구조">SoC Top TB의 UVM Env 구조</a>
  <a class="page-toc-link" href="#연습-문제">연습 문제</a>
  <a class="page-toc-link" href="#퀴즈">퀴즈</a>
  <a class="page-toc-link" href="#qa">Q&A</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Distinguish** IP-level DV vs SoC-level DV의 검증 책임 차이를 설명
    - **Identify** Top-level만 catch되는 결함 (connectivity, clock domain, interrupt routing, memory map, power)
    - **Design** Multi-IP UVM env에 multiple agent + virtual sequencer 통합 구조
    - **Plan** Multi-clock / multi-power domain SoC의 reset / handshake 시나리오

!!! info "사전 지식"
    - [UVM](../../uvm/) Module 01-06
    - SoC architecture 일반

## 왜 이 모듈이 중요한가

**SoC integration bug는 가장 비싸게 잡힙니다**. IP-level은 모두 PASS인데 통합 후 connectivity 한 줄 누락 → silicon revision 또는 software workaround. Top-level DV는 IP DV가 catch 못 하는 issue category 전체를 책임집니다.

## 핵심 개념
**SoC Top 검증 = IP 단위에서 검증할 수 없는 "IP 간 상호작용"을 확인하는 단계. Connectivity, Clock/Reset, Interrupt, Memory Map, Power Domain 등 통합에서만 드러나는 문제를 검증. IP DV가 "각 부품이 정상"이라면, Top DV는 "부품을 조립한 완제품이 정상"인지 확인.**

!!! tip "💡 이해를 위한 비유"
    **SoC Top** ≈ **도시 전체 설계 검증**

    각 건물(IP)이 개별적으로 완공되었어도, 도로망(interconnect)이 잘못 연결되거나 지번 매핑(connectivity)이 틀리면 도시 전체가 작동하지 않는다. SoC Top 검증은 완공된 건물들을 도시로 연결하는 단계의 오류를 잡는 작업이다.

!!! danger "❓ 흔한 오해"
    **오해**: SoC Top 시뮬레이션을 통과하면 IP 단독 검증 없이도 충분하다.

    **실제**: SoC Top 검증은 IP 간 연결 오류를 잡지만, IP 내부 기능 버그는 IP-level DV에서만 발견된다.

    **왜 헷갈리는가**: "통합 테스트가 단위 테스트를 포함한다"는 소프트웨어 직관을 하드웨어 검증에 잘못 적용하기 때문이다.
---

## IP 검증 vs SoC Top 검증

| 항목 | IP-Level DV | SoC Top-Level DV |
|------|------------|-------------------|
| 범위 | 단일 IP (MMU, UFS HCI 등) | 전체 SoC (수십~수백 IP 통합) |
| 초점 | IP 기능 완전성 | IP 간 **연결/상호작용** 정확성 |
| 환경 | VIP + UVM Agent | **실제 IP RTL** + 최소 자극 |
| 시뮬레이션 속도 | 빠름 (블록 단위) | 느림 (전체 SoC RTL) |
| 버그 유형 | 기능 버그 | **통합 버그** (연결 오류, 매핑 오류) |
| TB 복잡도 | 중간 | 높음 (다수 인터페이스) |

### IP 검증에서 잡을 수 없는 버그

```
1. Connectivity 오류
   - IP_A의 irq_out이 GIC의 SPI[47]에 연결되어야 하는데 SPI[48]에 연결
   - IP 단독으로는 발견 불가 — 연결은 Top에만 존재

2. Clock/Reset 오류
   - IP에 잘못된 클럭 공급 (200MHz 필요한데 100MHz 연결)
   - Reset 해제 순서 오류 (IP_A가 IP_B보다 먼저 해제되어야 하는데 반대)

3. Memory Map 오류
   - IP의 Base Address가 스펙과 다르게 배치
   - 주소 범위 중첩 (IP_A와 IP_B 주소가 겹침)

4. Interrupt Routing 오류
   - 인터럽트가 잘못된 CPU/GIC 입력에 연결
   - 인터럽트 우선순위/보안 그룹 설정 오류

5. Power Domain 오류
   - IP가 꺼진 Power Domain의 버스에 접근 → 행(hang)
   - Power 순서 위반
```

---

## SoC Top 검증 항목

### 1. Connectivity Verification

```
모든 IP 간 신호 연결이 설계 의도와 일치하는가?

검증 방법:
  (a) Formal (JasperGold Connectivity):
      - 연결 스펙(CSV/JSON) → Property 자동 생성 → 증명
      - "IP_A.data_out이 IP_B.data_in에 연결됨" 증명

  (b) Simulation:
      - IP_A에서 특정 패턴 출력 → IP_B에서 동일 패턴 수신 확인

  (c) DFT Scan:
      - Scan Chain으로 신호 값 직접 관찰

대상:
  - 데이터 버스 (AXI, AHB, APB)
  - 인터럽트 (IP → GIC)
  - DMA 요청 (IP → DMAC)
  - Clock/Reset 트리
  - Power 스위치 제어
```

### 2. Memory Map Verification

```
모든 IP가 올바른 주소에 배치되어 있는가?

+------------------------------------------+
| 0x0000_0000 | BootROM                     |
| 0x1000_0000 | Internal SRAM               |
| 0x1200_0000 | UFS HCI Registers (APB)     |
| 0x1300_0000 | DRAM Controller Regs        |
| 0x1400_0000 | Crypto Engine               |
| ...         | ...                         |
| 0x4000_0000 | DRAM (via MC)               |
+------------------------------------------+

검증:
  - 각 IP의 Base Address에 접근 → 응답 확인
  - 할당되지 않은 주소 접근 → DECERR 확인
  - 주소 중첩 없음 확인
  - IP-XACT 메타데이터와 실제 RTL 비교
```

### 3. Clock/Reset Verification

```
검증 항목:
  - 각 IP에 올바른 클럭 주파수 공급
  - Clock Gating 동작 (IP Idle 시 클럭 차단)
  - Reset 해제 순서 (의존성에 따른 순서)
  - Reset 후 모든 IP의 레지스터 기본값

Reset 순서 예시:
  1. PLL Lock 확인
  2. Bus Fabric Reset 해제
  3. Memory Controller Reset 해제 (DRAM 접근 필요)
  4. 나머지 IP Reset 해제
  → 순서 위반 시 IP가 초기화되지 않은 버스에 접근 → 행(hang)
```

### 4. Interrupt Routing Verification

```
검증 항목:
  - IP_A의 인터럽트 → GIC의 올바른 SPI 번호
  - 인터럽트 트리거 타입 (Edge/Level) 일치
  - 인터럽트 보안 그룹 (Secure/Non-Secure)
  - 인터럽트 우선순위
  - 인터럽트 마스킹 동작

시나리오:
  IP에서 인터럽트 발생 → GIC에서 올바른 CPU에 전달 →
  ISR 실행 → 인터럽트 클리어 → GIC 상태 복귀
```

### 5. Power Domain Verification

```
검증 항목:
  - Power On/Off 시퀀스 정확성
  - 꺼진 도메인의 IP 접근 시 적절한 에러 응답
  - Power Isolation (꺼진 IP의 출력이 버스를 오염시키지 않음)
  - 전력 상태 전이 (Active → Idle → Retention → Off)
  - DVFS (Dynamic Voltage Frequency Scaling) 동작
```

---

## SoC Top TB 아키텍처 (이력서 연결)

```
+------------------------------------------------------------------+
|                    SoC Top-Level TB                                |
|                                                                   |
|  +------------------+  +------------------+  +------------------+ |
|  | CPU Model        |  | External Memory  |  | External IF      | |
|  | (C-model or      |  | Model            |  | Model            | |
|  |  Processor VIP)  |  | (DRAM BFM)       |  | (UFS/Ethernet)   | |
|  +--------+---------+  +--------+---------+  +--------+---------+ |
|           |                      |                      |         |
|           v                      v                      v         |
|  +------------------------------------------------------------+  |
|  |                DUT (Full SoC RTL)                           |  |
|  |  +------+ +-----+ +------+ +-------+ +------+ +------+    |  |
|  |  | CPU  | | MC  | | UFS  | |DCMAC  | | MMU  | | ...  |    |  |
|  |  +------+ +-----+ +------+ +-------+ +------+ +------+    |  |
|  +------------------------------------------------------------+  |
|                                                                   |
|  +------------------------------------------------------------+  |
|  | Checker / Monitor Layer                                     |  |
|  |  - Bus Protocol Checker (AXI/AHB/APB)                      |  |
|  |  - Interrupt Monitor                                        |  |
|  |  - Memory Map Checker                                       |  |
|  |  - Power State Monitor                                      |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+

특징:
  - CPU Model이 FW(BootROM, BL2 등)를 실행 → 실제 부팅 시뮬레이션
  - 또는 AXI Master VIP으로 레지스터 접근 시나리오 실행
  - 외부 메모리/디바이스는 BFM(Bus Functional Model)으로 대체
```

---

## 코드 예시: Connectivity 검증 SVA

### Formal Connectivity Property

```systemverilog
// Connectivity Spec (CSV 등)에서 자동 생성되는 SVA
// "IP_A.irq_out → GIC.spi[47]" 연결 증명

module soc_connectivity_check (
  input logic        clk,
  input logic        rst_n,
  // IP_A 인터럽트 출력
  input logic        ip_a_irq_out,
  // GIC SPI 입력
  input logic [63:0] gic_spi
);

  // ---- Connectivity Assertion ----
  // ip_a_irq_out은 gic_spi[47]에 1:1 연결되어야 함
  property p_irq_connectivity;
    @(posedge clk) disable iff (!rst_n)
    ip_a_irq_out == gic_spi[47];
  endproperty

  ast_irq_conn: assert property (p_irq_connectivity)
    else `uvm_error("CONN_CHK", $sformatf(
      "IRQ Connectivity Mismatch: ip_a_irq_out=%0b, gic_spi[47]=%0b",
      ip_a_irq_out, gic_spi[47]))

  // ---- 데이터 버스 Connectivity ----
  // IP_A.axi_wdata가 Bus Fabric을 거쳐 IP_B.axi_wdata에 도달
  property p_data_connectivity;
    @(posedge clk) disable iff (!rst_n)
    (ip_a_axi_wvalid && ip_a_axi_wready)
    |-> ##[1:10] (ip_b_axi_wvalid && ip_b_axi_wdata == ip_a_axi_wdata);
  endproperty

  ast_data_conn: assert property (p_data_connectivity)
    else `uvm_error("CONN_CHK", "Data path connectivity failure: IP_A → IP_B")

  // ---- Negative Check: 잘못된 연결 없음 ----
  // ip_a_irq_out이 gic_spi[48]에 연결되면 안 됨
  property p_irq_no_cross;
    @(posedge clk) disable iff (!rst_n)
    ip_a_irq_out |-> !gic_spi[48];  // 다른 SPI에 영향 없음
  endproperty

  ast_irq_no_cross: assert property (p_irq_no_cross);

endmodule
```

**핵심 포인트**:
- Positive check (올바른 연결 확인) + Negative check (잘못된 연결 배제) 모두 필요
- Formal 도구(JasperGold)는 모든 입력 조합을 exhaustive하게 증명 → 시뮬레이션보다 확실
- CSV/JSON 스펙에서 이런 property를 **자동 생성**하는 것이 실무 핵심

---

## 코드 예시: Memory Map 검증 UVM Sequence

```systemverilog
class soc_memory_map_test_seq extends uvm_sequence #(axi_txn);
  `uvm_object_utils(soc_memory_map_test_seq)

  // SoC Memory Map 정의 (Config에서 로드)
  typedef struct {
    bit [31:0] base_addr;
    bit [31:0] size;
    string     ip_name;
    bit        is_secure;
  } mem_region_t;

  mem_region_t regions[$];

  function new(string name = "soc_memory_map_test_seq");
    super.new(name);
  endfunction

  task body();
    axi_txn txn;

    // ---- Phase 1: 각 IP Base Address에 R/W 접근 ----
    foreach (regions[i]) begin
      // Write
      txn = axi_txn::type_id::create($sformatf("wr_%s", regions[i].ip_name));
      start_item(txn);
      txn.addr   = regions[i].base_addr;
      txn.data   = 32'hDEAD_BEEF;
      txn.wr_rd  = AXI_WRITE;
      txn.expect_resp = AXI_RESP_OKAY;  // 정상 응답 기대
      finish_item(txn);

      `uvm_info("MMAP", $sformatf("[%s] Write 0x%08h → resp=%s",
        regions[i].ip_name, regions[i].base_addr, txn.resp.name()), UVM_MEDIUM)

      // Read back
      txn = axi_txn::type_id::create($sformatf("rd_%s", regions[i].ip_name));
      start_item(txn);
      txn.addr   = regions[i].base_addr;
      txn.wr_rd  = AXI_READ;
      finish_item(txn);

      if (txn.resp != AXI_RESP_OKAY)
        `uvm_error("MMAP", $sformatf("[%s] Base addr 0x%08h unreachable!",
          regions[i].ip_name, regions[i].base_addr))
    end

    // ---- Phase 2: 할당되지 않은 주소 → DECERR 확인 ----
    test_unmapped_address(32'hFFFF_0000);
    test_unmapped_address(32'h0000_0100);

    // ---- Phase 3: 주소 경계 테스트 ----
    foreach (regions[i]) begin
      // IP 영역 마지막 주소 접근 → OKAY
      test_boundary(regions[i].base_addr + regions[i].size - 4, AXI_RESP_OKAY);
      // IP 영역 직후 주소 접근 → DECERR (다음 IP 영역이 아닌 경우)
      test_boundary(regions[i].base_addr + regions[i].size, AXI_RESP_DECERR);
    end
  endtask

  task test_unmapped_address(bit [31:0] addr);
    axi_txn txn = axi_txn::type_id::create("unmapped");
    start_item(txn);
    txn.addr  = addr;
    txn.wr_rd = AXI_READ;
    finish_item(txn);

    if (txn.resp != AXI_RESP_DECERR)
      `uvm_error("MMAP", $sformatf("Unmapped 0x%08h should return DECERR, got %s",
        addr, txn.resp.name()))
    else
      `uvm_info("MMAP", $sformatf("Unmapped 0x%08h correctly returned DECERR", addr), UVM_MEDIUM)
  endtask

  task test_boundary(bit [31:0] addr, axi_resp_e expect);
    // ... 경계 테스트 구현
  endtask
endclass
```

**검증 전략 3단계**:
1. **Positive**: 각 IP Base Address R/W → OKAY 응답
2. **Negative**: 미할당 주소 → DECERR 응답
3. **Boundary**: 영역 경계에서 정확히 잘리는지 확인

---

## 실전 디버그 시나리오: Interrupt 라우팅 오류

### 증상
```
[UVM_ERROR] @ 125000ns: ISR not triggered within timeout.
  Expected: GIC SPI[47] → CPU0 IRQ
  Actual:   CPU0 IRQ never asserted after IP_A interrupt
```

### 디버그 트레이싱 (사고과정)

```
Step 1: IP_A에서 인터럽트 발생 확인
  → 로그: "IP_A irq_out asserted at 124500ns" ✅ 정상

Step 2: GIC 입력 확인
  → 로그에 GIC SPI[47] 관련 메시지 없음 ❌
  → 의심: IP_A.irq_out → GIC.spi[47] 연결 문제

Step 3: 실제 연결 추적 (RTL)
  soc_top.sv:
    .spi_47 (ip_b_irq_out),  // ← ip_a가 아닌 ip_b가 연결!
    .spi_48 (ip_a_irq_out),  // ← ip_a가 48에 잘못 연결!

Step 4: 근본 원인
  RTL 통합 시 IP_A와 IP_B의 인터럽트 포트가 뒤바뀜
  → IP 단독 검증에서는 발견 불가 (인터럽트는 외부 연결)

Step 5: 수정
  soc_top.sv:
    .spi_47 (ip_a_irq_out),  // 수정
    .spi_48 (ip_b_irq_out),  // 수정

Step 6: 검증
  Connectivity SVA를 추가하여 재발 방지:
  assert property (ip_a_irq_out == gic_spi[47]);
```

### 교훈
| 항목 | 내용 |
|------|------|
| **버그 분류** | 통합 버그 (Connectivity) |
| **발견 레벨** | SoC Top 검증에서만 발견 가능 |
| **근본 원인** | RTL Integration 시 수동 포트 매핑 실수 |
| **예방책** | Connectivity SVA 자동 생성 + Formal 검증 |
| **IP 검증 한계** | IP_A TB에서 irq_out은 정상 → 연결 대상은 IP TB 범위 밖 |

---

## SoC Top TB의 UVM Env 구조

```systemverilog
class soc_top_env extends uvm_env;
  `uvm_component_utils(soc_top_env)

  // ---- Agents ----
  axi_master_agent   m_cpu_agent;      // CPU Model (AXI Master VIP)
  axi_slave_agent    m_dram_agent;     // DRAM BFM
  apb_master_agent   m_apb_agent;      // APB 접근용

  // ---- Checkers (Common Task Layer) ----
  soc_connectivity_checker  m_conn_chk;
  soc_memmap_checker        m_mmap_chk;
  soc_interrupt_monitor     m_irq_mon;
  soc_power_monitor         m_pwr_mon;
  soc_clock_monitor         m_clk_mon;

  // ---- Coverage ----
  soc_cctv_coverage         m_cctv_cov;    // CCTV 매트릭스

  // ---- Scoreboard ----
  soc_top_scoreboard        m_scbd;

  // ---- Config ----
  soc_top_config            m_cfg;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // Config 가져오기
    if (!uvm_config_db#(soc_top_config)::get(this, "", "soc_cfg", m_cfg))
      `uvm_fatal("CFG", "soc_top_config not found in config_db")

    // Agent 생성
    m_cpu_agent  = axi_master_agent::type_id::create("m_cpu_agent", this);
    m_dram_agent = axi_slave_agent::type_id::create("m_dram_agent", this);

    // Checker 생성 (Config 기반으로 동적 결정)
    m_conn_chk = soc_connectivity_checker::type_id::create("m_conn_chk", this);
    m_mmap_chk = soc_memmap_checker::type_id::create("m_mmap_chk", this);
    m_irq_mon  = soc_interrupt_monitor::type_id::create("m_irq_mon", this);

    if (m_cfg.has_power_domain)
      m_pwr_mon = soc_power_monitor::type_id::create("m_pwr_mon", this);

    // CCTV Coverage
    m_cctv_cov = soc_cctv_coverage::type_id::create("m_cctv_cov", this);

    // Config 전파
    uvm_config_db#(soc_memmap_config)::set(this, "m_mmap_chk", "mmap_cfg", m_cfg.mmap);
    uvm_config_db#(soc_irq_config)::set(this, "m_irq_mon", "irq_cfg", m_cfg.irq_map);
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);

    // Agent → Scoreboard 연결
    m_cpu_agent.m_monitor.ap.connect(m_scbd.cpu_export);
    m_dram_agent.m_monitor.ap.connect(m_scbd.mem_export);

    // Agent → Checker 연결
    m_cpu_agent.m_monitor.ap.connect(m_mmap_chk.txn_export);
    m_cpu_agent.m_monitor.ap.connect(m_cctv_cov.txn_export);
  endfunction
endclass
```

**구조 핵심**:
- `soc_top_config`에 IP 목록/메모리맵/인터럽트맵 → 모든 Checker가 Config 기반 동작
- Common Task Checker Layer가 Agent와 별도 계층으로 분리
- CCTV Coverage Collector가 모든 트랜잭션을 수집하여 매트릭스 자동 갱신

---

## 연습 문제

### 문제 1: Memory Map 충돌 진단

**문제**: 다음 SoC Memory Map 설정에서 문제를 찾고, 어떤 증상이 나타날지 설명하라.

```
IP_A (UFS HCI):  Base=0x1200_0000, Size=0x0010_0000
IP_B (Crypto):   Base=0x1208_0000, Size=0x0008_0000
IP_C (DMA):      Base=0x1300_0000, Size=0x0001_0000
```

**사고과정**:
```
1. 각 IP의 주소 범위를 계산:
   IP_A: 0x1200_0000 ~ 0x120F_FFFF (1MB)
   IP_B: 0x1208_0000 ~ 0x120F_FFFF (512KB)
   IP_C: 0x1300_0000 ~ 0x1300_FFFF (64KB)

2. 범위 겹침 확인:
   IP_A 끝: 0x120F_FFFF
   IP_B 시작: 0x1208_0000
   → IP_B가 IP_A 범위 안에 완전히 포함됨! (0x1208_0000 < 0x120F_FFFF)

3. 증상:
   - CPU가 0x1208_0000에 접근 시 IP_A와 IP_B 모두 응답
   - Bus Fabric에서 두 slave 동시 응답 → 버스 프로토콜 위반
   - 또는 Decoder가 먼저 매칭되는 IP로 라우팅 → IP_B 접근 불가
   - AXI DECERR 또는 데이터 오염

4. 수정:
   IP_B를 IP_A 범위 밖으로 이동: Base=0x1210_0000
   또는 IP_A Size를 줄여 IP_B 영역을 분리
```

### 문제 2: Reset 순서 위반 디버그

**문제**: 다음 로그에서 근본 원인을 찾아라.

```
[  0ns] Reset de-asserted
[ 10ns] CPU: Accessing DRAM at 0x4000_0000
[ 10ns] MC (Memory Controller): DRAM initialization not complete
[ 10ns] AXI BUS: SLVERR response from MC
[ 15ns] CPU: Bus error exception
[ 15ns] [UVM_FATAL] CPU halted — unrecoverable bus error during boot
```

**사고과정**:
```
1. FIRST error 확인: 10ns에 MC가 "DRAM initialization not complete"
   → MC가 아직 초기화되지 않았는데 CPU가 접근

2. Reset 해제 순서 추적:
   - 0ns: Reset이 해제됨 → CPU와 MC가 동시에 reset 해제
   - CPU는 즉시 BootROM 실행 → DRAM 접근 시도
   - MC는 DRAM 초기화에 수십~수백 ns 필요

3. 근본 원인:
   Reset 해제 순서 오류
   - 올바른 순서: PLL Lock → MC Reset 해제 → DRAM Init 완료 → CPU Reset 해제
   - 실제: 모든 IP가 동시에 Reset 해제 → CPU가 MC보다 먼저 동작

4. 수정:
   soc_top_reset_controller에서 순차 해제 구현:
   Phase 1: Bus Fabric + MC reset 해제
   Phase 2: MC DRAM init 완료 대기 (init_done 신호)
   Phase 3: CPU + 나머지 IP reset 해제

5. 검증:
   SVA로 순서 보장:
   assert property (@(posedge clk)
     $rose(mc_rst_n) |-> !cpu_rst_n until mc_init_done);
```

### 문제 3: Connectivity 검증 전략 선택

**문제**: 200개 IP가 있는 SoC에서 Connectivity 검증을 Simulation으로만 수행하려 한다. 왜 이것이 불충분한지 설명하고, 최적의 검증 전략을 제시하라.

**사고과정**:
```
1. Simulation의 한계:
   - 200개 IP × 평균 50개 신호 = ~10,000개 연결 포인트
   - 각 연결을 확인하려면 해당 경로에 트래픽 발생 필요
   - 모든 조합을 커버하는 테스트 작성 = 수천 개 시나리오
   - 시뮬레이션 시간: SoC Full RTL에서 1개 테스트 = 수 시간
   - 현실적으로 모든 연결을 테스트하기 불가능

2. 추가 문제:
   - 시뮬레이션은 실행된 경로만 확인 (exercised path)
   - 연결은 되었지만 테스트에서 사용하지 않은 경로 = 미검증
   - "연결이 없다"는 것을 시뮬레이션으로 증명 불가

3. 최적 전략: Formal + Simulation Hybrid
   a) Formal (JasperGold Connectivity):
      - 연결 스펙(CSV) → SVA 자동 생성 → exhaustive 증명
      - 모든 연결을 입력 무관하게 완전 증명
      - 수 시간 내 10,000개 연결 모두 검증
      - "이 연결이 존재한다" + "다른 연결이 없다" 모두 증명

   b) Simulation:
      - Formal이 커버하지 못하는 동적 시나리오
      - 데이터 무결성 (올바른 데이터가 전달되는가)
      - 타이밍 관련 동작 (CDC 등)
      - End-to-end 기능 시나리오

   c) 역할 분담:
      Formal = 구조적 연결 완전성 (static)
      Simulation = 동적 동작 정확성 (dynamic)
```

---

## 퀴즈

**Q1**: SoC Top 검증에서 발견되는 5대 통합 버그 유형을 나열하라.

<details>
<summary>정답</summary>

1. Connectivity 오류 (신호 연결 오류)
2. Memory Map 오류 (주소 매핑/중첩)
3. Clock/Reset 오류 (주파수 불일치, 해제 순서)
4. Interrupt Routing 오류 (잘못된 GIC 매핑)
5. Power Domain 오류 (격리 실패, 순서 위반)
</details>

**Q2**: Reset 해제의 올바른 순서는? (PLL, CPU, Bus Fabric, Memory Controller)

<details>
<summary>정답</summary>

PLL Lock → Bus Fabric → Memory Controller (+ DRAM Init 완료 대기) → CPU + 나머지 IP

이유: CPU가 부팅 시 DRAM에 접근하므로, MC가 먼저 초기화 완료되어야 함. Bus Fabric은 모든 IP 간 통신 경로이므로 가장 먼저 활성화.
</details>

**Q3**: Formal Connectivity 검증이 시뮬레이션보다 우수한 점 2가지와, 시뮬레이션이 여전히 필요한 이유 1가지를 설명하라.

<details>
<summary>정답</summary>

**Formal 우위**:
1. Exhaustive 증명 — 모든 입력 조합에서 연결 정확성을 완전히 증명 (시뮬레이션은 실행한 경로만)
2. Negative 증명 — "잘못된 연결이 없다"를 증명 가능 (시뮬레이션으로는 부재를 증명 불가)

**시뮬레이션 필요**:
- 동적 동작 검증 — 데이터가 연결을 통해 실제로 올바르게 전달되는지, 타이밍이 맞는지는 Formal만으로 부족. End-to-end 기능 시나리오(부팅, DMA 전송 등)는 시뮬레이션이 필수.
</details>

---

## Q&A

**Q: IP 검증을 완벽히 했는데 왜 SoC Top 검증이 필요한가?**
> "IP 검증은 각 IP가 독립적으로 정상인지 확인한다. 그러나 통합 시 발생하는 문제 — 연결 오류, 주소 매핑 오류, 인터럽트 라우팅 오류, 클럭/리셋 순서 오류, 전력 도메인 격리 — 는 IP 단독으로는 발견할 수 없다. 실제로 post-silicon 버그의 상당수가 통합 문제에서 발생한다."

**Q: SoC Top TB를 어떻게 설계했나?**
> "CPU Model(또는 AXI Master VIP) + DRAM BFM + 외부 디바이스 모델로 전체 SoC를 감싸는 구조다. Checker Layer에서 버스 프로토콜, 인터럽트 라우팅, 메모리 맵, 전력 상태를 상시 모니터링한다. 실제 FW(BootROM)를 CPU Model에서 실행하여 부팅 시뮬레이션까지 수행했다. 이 환경을 여러 SoC 프로젝트에 재사용 가능하도록 설계했다."

**Q: Connectivity 검증을 어떻게 수행했나?**
> "Formal과 Simulation의 Hybrid 전략이다. 연결 스펙(CSV)에서 SVA property를 자동 생성하여 JasperGold로 exhaustive 증명을 수행하고, 구조적 연결 완전성을 보장했다. 시뮬레이션에서는 실제 데이터 전달의 end-to-end 정확성과 타이밍을 검증했다. Positive check(올바른 연결)과 Negative check(잘못된 연결 배제)을 모두 수행하는 것이 핵심이다."

**Q: Memory Map 검증에서 어떤 시나리오를 포함했나?**
> "3단계로 진행했다. (1) 각 IP의 Base Address에 R/W 접근하여 OKAY 응답 확인, (2) 미할당 주소 접근 시 DECERR 응답 확인, (3) 주소 경계에서 정확히 잘리는지 boundary test. 특히 주소 중첩은 두 slave가 동시 응답하여 버스 프로토콜 위반으로 이어지므로, IP-XACT 메타데이터와 실제 RTL의 주소 디코더를 크로스 체크했다."

---
!!! warning "실무 주의점 — 인터럽트 SPI 번호 1씩 오프셋 뒤바뀜"
    **현상**: IP는 단독 테스트에서 인터럽트를 정상 발생시키지만, SoC 통합 후 ISR이 전혀 실행되지 않거나 엉뚱한 핸들러가 호출된다.

    **원인**: soc_top.sv의 포트 매핑에서 GIC SPI 인덱스가 스펙 대비 1 차이나게 연결된 경우, IP-level DV는 GIC 없이 인터럽트 신호만 확인하므로 통과된다. SoC 통합 시점에서야 드러나는 전형적인 connectivity 버그.

    **점검 포인트**: SVA `assert property (@(posedge clk) ip_a_irq_out == gic_spi[47])` 구문에서 GIC SPI 인덱스를 IP-XACT interrupt_map과 1:1 대조. `soc_top.sv` 포트 매핑에서 `irq_out` 연결 라인을 grep하여 스펙 CSV와 직접 비교.

## 핵심 정리

- **IP DV vs Top DV**: IP는 부품 정확성, Top은 조립 정확성 (IP 간 상호작용).
- **Top-only 결함**: connectivity (signal mis-route), clock domain (CDC), interrupt routing, memory map decoding, power domain isolation.
- **Multi-IP UVM env**: env에 여러 agent + virtual sequencer가 sub-sequencer 핸들 보유.
- **Multi-clock**: 각 clock domain마다 별도 agent + clocking block. Reset sequence가 모든 domain에서 정상 deassert.
- **Power domain**: ON/OFF 시퀀스, isolation cell 동작, retention register.

## 다음 단계

- 📝 [**Module 01 퀴즈**](quiz/01_soc_top_integration_quiz.md)
- ➡️ [**Module 02 — Common Task & CCTV**](02_common_task_cctv.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">코스 홈</div>
  </a>
  <a class="nav-next" href="../02_common_task_cctv/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Common Task & CCTV (Common Task Coverage Verification)</div>
  </a>
</div>
