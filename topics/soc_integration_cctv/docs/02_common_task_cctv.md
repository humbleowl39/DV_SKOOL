# Module 02 — Common Task & CCTV

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🏗️</span>
    <span class="chapter-back-text">SoC Integration</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 02</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#왜-common-task가-누락되는가">왜 Common Task가 누락되는가?</a>
  <a class="page-toc-link" href="#common-task-항목-상세">Common Task 항목 상세</a>
  <a class="page-toc-link" href="#cctv-방법론">CCTV 방법론</a>
  <a class="page-toc-link" href="#cctv-coverage-model">CCTV Coverage Model</a>
  <a class="page-toc-link" href="#코드-예시-cctv-coverage-matrix-systemverilog">코드 예시: CCTV Coverage Matrix (SystemVerilog)</a>
  <a class="page-toc-link" href="#코드-예시-sysmmu-통합-검증-시나리오">코드 예시: sysMMU 통합 검증 시나리오</a>
  <a class="page-toc-link" href="#코드-예시-security-access-control-검증">코드 예시: Security Access Control 검증</a>
  <a class="page-toc-link" href="#실전-사례-gap이-silicon-bug로-이어지는-시나리오">실전 사례: Gap이 Silicon Bug로 이어지는 시나리오</a>
  <a class="page-toc-link" href="#연습-문제">연습 문제</a>
  <a class="page-toc-link" href="#퀴즈">퀴즈</a>
  <a class="page-toc-link" href="#qa">Q&A</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Identify** SoC 내 Common Task (sysMMU, Security/Access Control, DVFS, Clock Gating 등) 구분
    - **Apply** CCTV (Common Task Coverage Verification) 패턴으로 모든 IP에 task 적용 추적
    - **Implement** 재사용 가능한 sequence library + virtual sequencer
    - **Plan** Coverage matrix (IP × Common Task) 닫는 전략

!!! info "사전 지식"
    - [Module 01](01_soc_top_integration.md)
    - UVM Sequence Library 패턴

## 핵심 개념
**Common Task = SoC 내 모든(또는 대부분의) IP에 공통적으로 적용되는 검증 항목 (sysMMU, Security/Access Control, DVFS, Clock Gating 등). CCTV = 이 Common Task가 모든 IP에 대해 빠짐없이 수행되었는지 추적하는 Coverage 방법론. DVCon 2025 논문의 핵심 주제.**

!!! tip "💡 이해를 위한 비유"
    **Common Task** ≈ **건물 입주 공통 점검 항목**

    도시 내 모든 건물(IP)은 소방, 전기, 배수 공통 점검을 받아야 한다. CCTV는 어떤 건물이 어떤 점검을 통과했는지 추적하는 점검 대장이다. 점검 항목이 빠지거나 특정 건물이 누락되면, 입주 허가(Silicon tape-out)를 내줄 수 없다.

!!! danger "❓ 흔한 오해"
    **오해**: Reset을 한 번 인가하면 모든 IP가 안전하게 초기화된다.

    **실제**: Reset 도메인이 다른 IP들은 서로 다른 시점에 해제되며, 잘못된 순서로 해제되면 초기화되지 않은 상태로 동작을 시작한다.

    **왜 헷갈리는가**: 단일 IP 검증 환경에서는 Reset 타이밍이 단순하지만, SoC Top에서는 여러 Reset 도메인이 복잡하게 얽혀 있다는 사실을 과소평가하기 때문이다.
---

## 왜 Common Task가 누락되는가?

### 문제의 구조

```
SoC 내 IP 수: 50~200개
각 IP에 공통 적용되는 검증 항목:

  +-------+  +-------+  +-------+     +-------+
  | IP_0  |  | IP_1  |  | IP_2  | ... | IP_N  |
  +---+---+  +---+---+  +---+---+     +---+---+
      |          |          |              |
  Common Tasks (모든 IP에 필요):
  ☑ sysMMU 연동      ← 이 IP에 sysMMU가 연결되어 있나?
  ☑ Security 접근제어 ← Secure/Non-Secure 접근이 올바른가?
  ☑ DVFS 동작        ← 전압/주파수 변경 시 정상 동작?
  ☑ Clock Gating     ← Idle 시 클럭 차단 + 복구?
  ☑ Power Domain     ← Power Off/On 시 상태 보존?
  ☑ Reset 동작       ← Reset 후 기본값?
  ☑ Interrupt 동작   ← 인터럽트 발생/클리어 정확?

  IP_0: ☑☑☑☑☑☑☑  (모두 완료)
  IP_1: ☑☑☐☑☑☑☑  (DVFS 누락!)
  IP_2: ☑☐☑☑☑☐☑  (Security, Power 누락!)
  ...
  IP_N: ☐☑☑☐☑☑☑  (sysMMU, DVFS 누락!)

  → 엔지니어 수십 명이 각자 담당 IP의 Common Task를 관리
  → 수백 개 조합에서 3~5%가 누락 (Human Oversight)
```

### 누락 원인 분류 (DVCon 논문 데이터)

| 원인 | 비율 | 설명 |
|------|------|------|
| **Human Oversight** | **96.30%** (소형 SoC) | 엔지니어가 단순히 빠뜨림 |
| New IP/Feature | ~40% 감소 가능 | 새 IP 추가 시 Common Task 목록 미갱신 |
| Legacy 의존 | 높음 | "이전 칩에서 했으니까" 가정 → 변경사항 누락 |
| 문서 불일치 | 중간 | 스펙과 실제 구현의 차이 |

---

## Common Task 항목 상세

### 1. sysMMU 연동 검증

```
SoC 내 대부분의 DMA-capable IP는 sysMMU를 통해 메모리 접근

검증 항목:
  - IP → sysMMU → Memory 경로의 주소 변환 정확성
  - Page Fault 발생 시 IP의 에러 처리
  - sysMMU Bypass 모드 동작
  - TLB Invalidation 후 재접근
  - Secure/Non-Secure 접근 제어

누락 시 영향:
  - IP가 잘못된 물리 주소에 접근 → 데이터 오염
  - Page Fault 무한 루프 → 시스템 행(hang)
```

### 2. Security / Access Control

```
각 IP의 레지스터와 메모리 영역에 대한 접근 권한:

검증 항목:
  - Secure IP에 Non-Secure 접근 → 차단 확인 (TZPC)
  - 레지스터별 접근 권한 (RO/WO/RW × EL × S/NS)
  - Firewall 설정 후 불법 접근 차단
  - 보안 레지스터 Lock (한번 설정 후 변경 불가)

누락 시 영향:
  - Normal World에서 Secure 레지스터 접근 가능 → 보안 붕괴
  - 잘못된 접근 권한 → 실리콘 보안 인증 실패
```

### 3. DVFS (Dynamic Voltage Frequency Scaling)

```
전압/주파수 동적 변경 시 IP 정상 동작:

검증 항목:
  - 클럭 변경 중 IP 동작 (Glitch-free?)
  - 변경 완료 후 IP 기능 정상
  - 변경 중 진행 중인 트랜잭션 보호
  - 최저/최고 주파수에서의 동작

누락 시 영향:
  - 클럭 전환 중 데이터 오류 → 간헐적 버그 (재현 어려움)
```

### 4. Clock Gating / Power Gating

```
IP Idle 시 클럭/전원 차단 + 복구:

검증 항목:
  - Idle 감지 → Clock Gate 활성화 → IP 상태 유지
  - Wake-up 요청 → Clock 복귀 → 즉시 동작 가능
  - Power Gate: 상태 저장 → 전원 차단 → 복원
  - Isolation Cell 동작 (꺼진 IP 출력이 버스 오염 방지)

누락 시 영향:
  - Clock Gate 후 복귀 실패 → IP 죽음
  - Isolation 미동작 → 버스 X 전파 → 시스템 불안정
```

---

## CCTV 방법론

### CCTV의 핵심 아이디어

```
CCTV = Common Task × IP 매트릭스의 Coverage를 체계적으로 추적

              | sysMMU | Security | DVFS | ClkGate | Power | Reset | IRQ |
  IP_0 (UFS)  |   ✅   |    ✅    |  ✅  |   ✅    |  ✅   |  ✅   | ✅  |
  IP_1 (DMA)  |   ✅   |    ✅    |  ❌  |   ✅    |  ✅   |  ✅   | ✅  |
  IP_2 (GPU)  |   ✅   |    ❌    |  ✅  |   ❌    |  ✅   |  ✅   | ✅  |
  IP_3 (Crypto)|  N/A  |    ✅    |  ✅  |   ✅    |  ✅   |  ✅   | ✅  |
  ...
  IP_N         |   ✅   |    ✅    |  ✅  |   ✅    |  ❌   |  ✅   | ✅  |

  ❌ = Gap (누락된 검증 항목)
  N/A = 해당 IP에 적용되지 않음

→ 이 매트릭스의 모든 칸이 ✅ 또는 N/A가 되어야 Coverage Closure
→ 수동으로 추적 시 3~5% 누락 → CCTV 자동화 필요
```

### 기존 방법의 한계

| 방법 | 한계 |
|------|------|
| **JIRA/Confluence 수동 추적** | SoC 규모 확장 시 관리 불가, 엔지니어 의존 |
| **IP-XACT 자동화** | 구조 정보만 → "이 IP에 sysMMU가 필요한가?"의 시맨틱 판단 불가 |
| **체크리스트 기반** | 새 IP/Feature 추가 시 갱신 누락, 레거시 의존 |

### DVCon 논문의 해결 — AI 기반 CCTV

```
(ai_engineering_ko Unit 7과 직결)

Phase 1: Hybrid Data Extraction
  IP-XACT → 구조(레지스터, 버스, 메모리맵)
  IP Spec → 시맨틱(기능, 보안, 동작 모드)
  → IP별 "어떤 Common Task가 필요한가" 판단

Phase 2: RAG + FAISS
  대규모 IP DB → Embedding → 인덱싱
  "IP_X에 sysMMU 검증이 필요한가?" → 관련 스펙 검색 → 판단

Phase 3: LLM-Based Gap Detection
  IP별 필요 Common Task 목록 (Phase 1-2)
  vs 기존 V-Plan의 실제 검증 항목
  → 차이 = Gap (누락)
  → 테스트 명령어 자동 생성

결과:
  Project A (대규모 SoC): 293 gaps (2.75%)
  Project B (소규모 SoC): 216 gaps (4.99%)
  Human Oversight: 96.30%
```

---

## CCTV Coverage Model

```
[CG_CCTV] Common Task Coverage Matrix

  // IP 목록 (SoC 설정에서 동적 생성)
  cp_ip: {UFS, DMA, GPU, CRYPTO, DISPLAY, ...}

  // Common Task 목록
  cp_task: {SYSMMU, SECURITY, DVFS, CLK_GATE, POWER, RESET, IRQ}

  // 검증 결과
  cp_result: {PASS, FAIL, NOT_APPLICABLE, NOT_TESTED}

  // 핵심: IP × Task 교차 커버리지
  cross: cp_ip × cp_task × cp_result

  // Closure 조건:
  // 모든 (ip, task) 쌍이 PASS 또는 NOT_APPLICABLE
  // NOT_TESTED가 0개 = Gap 없음
```

---

## 코드 예시: CCTV Coverage Matrix (SystemVerilog)

### 실제 구현 가능한 Covergroup

```systemverilog
// ---- CCTV Coverage Matrix Covergroup ----
// IP × Common Task × Result 교차 커버리지

typedef enum {
  IP_UFS, IP_DMA, IP_GPU, IP_CRYPTO, IP_DISPLAY,
  IP_ETHERNET, IP_USB, IP_I2C, IP_SPI, IP_UART
} ip_id_e;

typedef enum {
  TASK_SYSMMU, TASK_SECURITY, TASK_DVFS,
  TASK_CLK_GATE, TASK_POWER, TASK_RESET, TASK_IRQ
} common_task_e;

typedef enum {
  RESULT_PASS, RESULT_FAIL, RESULT_NOT_APPLICABLE, RESULT_NOT_TESTED
} task_result_e;

class cctv_coverage extends uvm_component;
  `uvm_component_utils(cctv_coverage)

  // Coverage 수집용 변수
  ip_id_e        sampled_ip;
  common_task_e  sampled_task;
  task_result_e  sampled_result;

  covergroup cg_cctv;
    cp_ip: coverpoint sampled_ip;
    cp_task: coverpoint sampled_task;
    cp_result: coverpoint sampled_result {
      // NOT_TESTED는 Gap — 이것이 0이 되어야 closure
      illegal_bins gap = {RESULT_NOT_TESTED};
    }

    // 핵심: IP × Task 교차 — 모든 조합이 커버되어야 함
    cx_ip_task: cross cp_ip, cp_task {
      // N/A 조합 제외 (예: CRYPTO는 sysMMU 불필요)
      ignore_bins crypto_no_mmu = binsof(cp_ip) intersect {IP_CRYPTO}
                                && binsof(cp_task) intersect {TASK_SYSMMU};
      ignore_bins uart_no_dvfs  = binsof(cp_ip) intersect {IP_UART}
                                && binsof(cp_task) intersect {TASK_DVFS};
    }

    // IP × Task × Result 삼중 교차 — PASS로 채워져야 함
    cx_full: cross cp_ip, cp_task, cp_result {
      ignore_bins crypto_no_mmu = binsof(cp_ip) intersect {IP_CRYPTO}
                                && binsof(cp_task) intersect {TASK_SYSMMU};
    }
  endgroup

  function new(string name, uvm_component parent);
    super.new(name, parent);
    cg_cctv = new();
  endfunction

  // 테스트 결과 수집
  function void record_result(ip_id_e ip, common_task_e task, task_result_e result);
    sampled_ip     = ip;
    sampled_task   = task;
    sampled_result = result;
    cg_cctv.sample();

    `uvm_info("CCTV", $sformatf("[%s × %s] = %s",
      ip.name(), task.name(), result.name()), UVM_MEDIUM)
  endfunction

  // Regression 종료 시 Gap 리포트
  function void report_phase(uvm_phase phase);
    real coverage_pct = cg_cctv.cx_ip_task.get_coverage();
    `uvm_info("CCTV", $sformatf("CCTV Matrix Coverage: %.2f%%", coverage_pct), UVM_NONE)

    if (coverage_pct < 100.0)
      `uvm_warning("CCTV", $sformatf(
        "CCTV Gap detected! Coverage=%.2f%% — uncovered IP×Task combinations exist",
        coverage_pct))
  endfunction
endclass
```

**핵심 설계 포인트**:
| 요소 | 설명 |
|------|------|
| `illegal_bins gap` | NOT_TESTED가 발생하면 coverage tool이 경고 → Gap 자동 감지 |
| `ignore_bins` | N/A 조합을 제외하여 false gap 방지 (Crypto에 sysMMU 불필요 등) |
| `cx_ip_task` cross | IP × Task 모든 조합이 실행되어야 closure |
| `report_phase` | Regression 후 자동으로 Gap 리포트 출력 |

---

## 코드 예시: sysMMU 통합 검증 시나리오

### sysMMU 검증 테스트 시퀀스

```systemverilog
class sysmmu_integration_test_seq extends uvm_sequence #(axi_txn);
  `uvm_object_utils(sysmmu_integration_test_seq)

  // 테스트 대상 IP
  string target_ip_name;
  bit [31:0] ip_base_addr;

  function new(string name = "sysmmu_integration_test_seq");
    super.new(name);
  endfunction

  task body();
    // ---- Scenario 1: 정상 주소 변환 ----
    `uvm_info("SMMU", $sformatf("[%s] Testing normal translation", target_ip_name), UVM_LOW)
    setup_page_table(
      .va(32'h0000_1000),      // Virtual Address
      .pa(32'h8000_1000),      // Physical Address
      .perm(PERM_RW),          // Read/Write 허용
      .ns(1'b0)                // Secure
    );
    // IP가 VA로 DMA 수행 → sysMMU가 PA로 변환 → Memory에 도달
    trigger_ip_dma(.addr(32'h0000_1000), .size(256));
    check_memory_write(.expected_pa(32'h8000_1000), .size(256));

    // ---- Scenario 2: Page Fault 처리 ----
    `uvm_info("SMMU", $sformatf("[%s] Testing page fault handling", target_ip_name), UVM_LOW)
    // 매핑되지 않은 VA로 DMA → Page Fault 발생
    trigger_ip_dma(.addr(32'hDEAD_0000), .size(64));
    check_page_fault(
      .expected_fault_addr(32'hDEAD_0000),
      .expected_fault_type(TRANSLATION_FAULT)
    );
    // IP가 에러를 gracefully 처리하는지 확인
    check_ip_error_status(.expected(IP_DMA_ERROR));

    // ---- Scenario 3: Bypass → Enable 전환 ----
    `uvm_info("SMMU", $sformatf("[%s] Testing bypass-to-enable transition", target_ip_name), UVM_LOW)
    set_sysmmu_bypass(1'b1);   // Bypass ON: VA == PA
    trigger_ip_dma(.addr(32'h8000_2000), .size(128));
    check_memory_write(.expected_pa(32'h8000_2000), .size(128));  // PA == VA

    set_sysmmu_bypass(1'b0);   // Bypass OFF: 변환 활성화
    setup_page_table(.va(32'h8000_2000), .pa(32'hA000_2000), .perm(PERM_RW), .ns(1'b0));
    trigger_ip_dma(.addr(32'h8000_2000), .size(128));
    check_memory_write(.expected_pa(32'hA000_2000), .size(128));  // PA ≠ VA

    // ---- Scenario 4: TLB Invalidation ----
    `uvm_info("SMMU", $sformatf("[%s] Testing TLB invalidation", target_ip_name), UVM_LOW)
    // 기존 매핑으로 DMA 성공 (TLB에 캐시됨)
    trigger_ip_dma(.addr(32'h0000_1000), .size(64));
    // Page Table 변경 (VA → 다른 PA로 재매핑)
    update_page_table(.va(32'h0000_1000), .new_pa(32'hC000_1000));
    // TLB Invalidation 수행
    invalidate_tlb(.va(32'h0000_1000));
    // 재접근 → 새 PA로 변환되어야 함
    trigger_ip_dma(.addr(32'h0000_1000), .size(64));
    check_memory_write(.expected_pa(32'hC000_1000), .size(64));
  endtask
endclass
```

### sysMMU 검증 4대 시나리오 요약

```
Scenario 1: Normal Translation
  IP → VA → sysMMU → PA → Memory ✅
  검증: 변환된 PA가 Page Table 설정과 일치

Scenario 2: Page Fault
  IP → 매핑없는 VA → sysMMU → Fault!
  검증: Fault 발생 + IP가 에러 처리 + 시스템 hang 없음

Scenario 3: Bypass ↔ Enable 전환
  Bypass ON: VA == PA (직접 접근)
  Bypass OFF: VA → PA 변환 활성화
  검증: 전환 중 진행 중인 트랜잭션 보호

Scenario 4: TLB Invalidation
  Page Table 변경 → TLB Invalidation → 재접근
  검증: 오래된 TLB 엔트리가 아닌 새 매핑 사용
```

---

## 코드 예시: Security Access Control 검증

### TrustZone (TZPC) 접근 제어 테스트

```systemverilog
class security_access_ctrl_seq extends uvm_sequence #(axi_txn);
  `uvm_object_utils(security_access_ctrl_seq)

  function new(string name = "security_access_ctrl_seq");
    super.new(name);
  endfunction

  task body();
    // ---- Test 1: Secure 레지스터에 Non-Secure 접근 → 차단 ----
    `uvm_info("SEC", "Testing NS access to Secure register", UVM_LOW)
    do_axi_read(
      .addr(CRYPTO_SECURE_KEY_REG),  // Secure-only 레지스터
      .prot({1'b1, 1'b0, 1'b0}),    // AxPROT[1]=1 → Non-Secure
      .expect_resp(AXI_RESP_SLVERR)  // 차단 → SLVERR
    );

    // ---- Test 2: Secure 레지스터에 Secure 접근 → 허용 ----
    `uvm_info("SEC", "Testing S access to Secure register", UVM_LOW)
    do_axi_read(
      .addr(CRYPTO_SECURE_KEY_REG),
      .prot({1'b0, 1'b0, 1'b0}),    // AxPROT[1]=0 → Secure
      .expect_resp(AXI_RESP_OKAY)    // 허용 → OKAY
    );

    // ---- Test 3: Non-Secure 레지스터에 Non-Secure 접근 → 허용 ----
    `uvm_info("SEC", "Testing NS access to NS register", UVM_LOW)
    do_axi_read(
      .addr(UART_DATA_REG),          // Non-Secure 레지스터
      .prot({1'b1, 1'b0, 1'b0}),    // Non-Secure
      .expect_resp(AXI_RESP_OKAY)    // 허용
    );

    // ---- Test 4: 보안 레지스터 Lock 후 재변경 시도 → 차단 ----
    `uvm_info("SEC", "Testing security lock", UVM_LOW)
    // Lock 설정 (Secure 모드에서)
    do_axi_write(.addr(TZPC_LOCK_REG), .data(32'h1), .prot(3'b000));  // Lock ON
    // Lock 해제 시도 → 실패해야 함
    do_axi_write(.addr(TZPC_LOCK_REG), .data(32'h0), .prot(3'b000));
    do_axi_read(.addr(TZPC_LOCK_REG), .prot(3'b000));
    // Lock이 여전히 1인지 확인
    if (read_data != 32'h1)
      `uvm_error("SEC", "Security lock was illegally cleared!")
  endtask
endclass
```

**AXI AxPROT 비트 해석**:
```
AxPROT[0] = Privileged(0) / Unprivileged(1)
AxPROT[1] = Secure(0) / Non-Secure(1)        ← Security 검증의 핵심
AxPROT[2] = Data(0) / Instruction(1)
```

---

## 실전 사례: Gap이 Silicon Bug로 이어지는 시나리오

### 사례: DMA Controller의 sysMMU 검증 누락

```
배경:
  - DMA Controller IP 검증 완료 (IP-Level)
  - SoC Top 검증에서 DMA의 Common Task 중 "sysMMU Bypass→Enable 전환" 누락
  - CCTV 매트릭스에서 Gap으로 표시되지 않음 (수동 관리)

Silicon 이후 발생한 버그:
  1. Linux 부팅 초기: sysMMU Bypass 모드로 DMA 동작 (부트로더)
  2. Linux kernel이 sysMMU를 Enable으로 전환
  3. 전환 시점에 진행 중이던 DMA 트랜잭션이 존재
  4. 이 트랜잭션이 VA로 발행되었지만, sysMMU가 아직 Page Table 설정 미완료
  5. → Translation Fault → DMA 실패 → 커널 패닉

디버그 난이도:
  - 부트로더에서는 재현 불가 (Bypass 모드)
  - Linux 부팅 시 "가끔" 발생 (타이밍 의존)
  - 간헐적 버그 → Silicon debug에 수 주 소요

CCTV로 사전 발견했다면:
  CCTV 매트릭스:
    DMA × sysMMU_bypass_to_enable = NOT_TESTED (Gap!)
  → 자동 감지 → 테스트 생성 → Pre-silicon에서 발견
  → Silicon debug 수 주 절약

교훈:
  - 간헐적 Silicon 버그의 상당수가 Common Task 누락에서 발생
  - sysMMU 전환 시나리오는 모든 DMA-capable IP에 공통 적용
  - 한 IP에서 발견되면 모든 IP에 전파하는 것이 CCTV의 가치
```

---

## 연습 문제

### 문제 1: CCTV ignore_bins 설계

**문제**: 다음 IP 목록에서 각 IP에 적용되지 않는(N/A) Common Task를 판별하고, ignore_bins를 작성하라.

```
IP 목록:
  - UART: 단순 직렬 통신, DMA 없음, 고정 클럭
  - GPU: 대용량 메모리 접근, DMA 있음, DVFS 지원
  - Crypto: 보안 전용, sysMMU 불필요 (내부 메모리만 사용)
  - Temperature Sensor: 읽기 전용, 인터럽트 없음, 전력 상시 ON
```

**사고과정**:
```
1. 각 IP의 특성 → Common Task 필요 여부 판단:

   UART:
   - sysMMU: ❌ N/A (DMA 없음 → sysMMU 불필요)
   - Security: ✅ (레지스터 접근 제어 필요)
   - DVFS: ❌ N/A (고정 클럭 → 주파수 변경 없음)
   - ClkGate: ✅ (Idle 시 클럭 차단 가능)
   - Power: ✅ (Power domain에 포함)
   - Reset: ✅ (Reset 후 기본값 확인)
   - IRQ: ✅ (RX 완료 인터럽트 등)

   GPU:
   - 모든 항목 ✅ (DMA, DVFS, sysMMU 모두 해당)

   Crypto:
   - sysMMU: ❌ N/A (내부 메모리만 사용)
   - Security: ✅ (보안 핵심 IP)
   - 나머지: ✅

   Temperature Sensor:
   - sysMMU: ❌ N/A (DMA 없음)
   - Security: ✅ (읽기 전용이라도 접근 제어 필요)
   - DVFS: ❌ N/A (센서는 고정 동작)
   - ClkGate: ❌ N/A (상시 ON 필요 — 온도 모니터링)
   - Power: ❌ N/A (전력 상시 ON)
   - Reset: ✅
   - IRQ: ❌ N/A (인터럽트 없음)

2. ignore_bins 코드:

   ignore_bins uart_no_mmu = binsof(cp_ip) intersect {IP_UART}
                            && binsof(cp_task) intersect {TASK_SYSMMU};
   ignore_bins uart_no_dvfs = binsof(cp_ip) intersect {IP_UART}
                             && binsof(cp_task) intersect {TASK_DVFS};
   ignore_bins crypto_no_mmu = binsof(cp_ip) intersect {IP_CRYPTO}
                              && binsof(cp_task) intersect {TASK_SYSMMU};
   ignore_bins tsensor_no_mmu = binsof(cp_ip) intersect {IP_TEMP_SENSOR}
                               && binsof(cp_task) intersect {TASK_SYSMMU};
   ignore_bins tsensor_no_dvfs = binsof(cp_ip) intersect {IP_TEMP_SENSOR}
                                && binsof(cp_task) intersect {TASK_DVFS};
   ignore_bins tsensor_no_clk = binsof(cp_ip) intersect {IP_TEMP_SENSOR}
                               && binsof(cp_task) intersect {TASK_CLK_GATE};
   ignore_bins tsensor_no_pwr = binsof(cp_ip) intersect {IP_TEMP_SENSOR}
                               && binsof(cp_task) intersect {TASK_POWER};
   ignore_bins tsensor_no_irq = binsof(cp_ip) intersect {IP_TEMP_SENSOR}
                               && binsof(cp_task) intersect {TASK_IRQ};

3. 주의점:
   - "읽기 전용 IP"라도 Security는 필요 (NS 접근으로 센서값 위조 방지)
   - ignore_bins를 잘못 설정하면 실제 필요한 검증이 누락됨
   - N/A 판단은 IP Spec 기반 — 이것이 IP-XACT만으로 부족한 이유
```

### 문제 2: Gap → 테스트 시나리오 생성

**문제**: CCTV 매트릭스에서 다음 Gap이 발견되었다. 이 Gap에 대한 구체적 테스트 시나리오를 설계하라.

```
Gap: IP_ETHERNET × TASK_CLK_GATE = NOT_TESTED
```

**사고과정**:
```
1. Gap 의미 파악:
   Ethernet IP의 Clock Gating 검증이 한 번도 실행되지 않음
   → Idle 시 클럭 차단 + 복구가 검증되지 않은 상태

2. Ethernet IP의 Clock Gating 특성 파악:
   - Ethernet은 패킷 수신/송신이 없을 때 Idle
   - Clock Gate 활성화 → MAC/PHY 클럭 차단
   - 패킷 도착 시 Wake-up → 클럭 복귀 → 즉시 수신 가능해야 함

3. 테스트 시나리오 설계:

   Scenario A: Basic Clock Gate & Wake-up
     Step 1: Ethernet으로 패킷 10개 송수신 (정상 동작 확인)
     Step 2: 트래픽 중단 → Idle 감지 대기
     Step 3: Clock Gate 활성화 확인 (클럭 모니터)
     Step 4: 외부에서 패킷 전송 → Wake-up
     Step 5: 클럭 복귀 확인
     Step 6: 패킷 정상 수신 확인 (데이터 무결성)

   Scenario B: Clock Gate 중 레지스터 접근
     Step 1: Clock Gate 활성화 상태
     Step 2: CPU가 Ethernet 레지스터 R/W 시도
     Step 3: 자동 Wake-up → 레지스터 접근 성공 확인
     Step 4: 또는 적절한 에러 응답 확인

   Scenario C: 빈번한 Gate/Ungate 반복
     Step 1: 짧은 패킷 burst → Idle → Gate → 패킷 → Ungate 반복
     Step 2: 100회 반복 중 데이터 오류/패킷 손실 없음 확인

4. CCTV 기록:
   record_result(IP_ETHERNET, TASK_CLK_GATE, RESULT_PASS);
```

### 문제 3: Human Oversight vs Technical Gap 분류

**문제**: 다음 3가지 Gap의 원인을 "Human Oversight"와 "Technical Gap"으로 분류하고 이유를 설명하라.

```
Gap A: USB IP의 Security 검증 누락 — IP 담당자가 "USB는 보안 불필요"라고 판단
Gap B: 새로 추가된 NPU IP의 sysMMU 검증 누락 — V-Plan이 갱신되지 않음
Gap C: DMA의 DVFS 검증 누락 — DVFS 중 DMA burst 테스트가 기술적으로 구현 어려움
```

**사고과정**:
```
Gap A: Human Oversight
  - USB도 DFU(Device Firmware Update) 모드에서 보안 중요
  - 담당자의 잘못된 판단으로 누락
  - AI가 IP Spec에서 "DFU", "Secure Boot" 키워드를 발견하여 보안 필요성 판단 가능
  - CCTV 자동화로 방지 가능

Gap B: Human Oversight (New IP/Feature 누락)
  - 새 IP 추가 시 V-Plan에 Common Task를 수동으로 추가해야 함
  - 자동화 없이는 "이전 칩에 없던 IP"의 검증 항목이 누락됨
  - DVCon 논문에서 "New IP/Feature 누락 40% 감소"의 대상

Gap C: Technical Gap
  - Human Oversight가 아닌, 실제 기술적 제약
  - DVFS 클럭 전환 중 DMA burst의 타이밍을 시뮬레이션하기 어려움
  - 해결: (1) Clock 전환 모델링 VIP 개발, (2) SVA로 타이밍 체크,
    (3) 필요 시 FPGA 프로토타입에서 검증

분류 요약:
  Gap A: Human Oversight (잘못된 판단) → 자동화로 방지
  Gap B: Human Oversight (프로세스 누락) → 자동화로 방지
  Gap C: Technical Gap (구현 난이도) → 기술적 해결 필요

→ DVCon 결과: 96.30%가 Gap A/B 유형 = 자동화만으로 대부분 해결
```

---

## 퀴즈

**Q1**: CCTV covergroup에서 `illegal_bins`와 `ignore_bins`의 차이와, 각각 CCTV에서의 역할은?

<details>
<summary>정답</summary>

- **`illegal_bins`**: 해당 bin이 hit되면 시뮬레이션 에러 발생. CCTV에서 `NOT_TESTED`에 적용 — Gap(미검증)이 남아있으면 경고.
- **`ignore_bins`**: 해당 bin을 coverage 계산에서 제외. CCTV에서 N/A 조합에 적용 — Crypto IP에 sysMMU가 불필요한 경우 등.
- 핵심 차이: illegal은 "이것이 발생하면 안 됨", ignore는 "이것은 해당 없음"
</details>

**Q2**: DVCon 논문에서 소규모 프로젝트(Project B)의 Gap Rate가 대규모(Project A)보다 높은 이유 2가지는?

<details>
<summary>정답</summary>

1. **교차 검증 부족**: 소규모에서는 한 명이 여러 IP를 담당하여 상호 리뷰가 적음
2. **인력 대비 조합 수**: IP 수는 적지만 Common Task 항목 수는 동일 → 1인당 관리해야 할 조합이 상대적으로 많음

→ 자동화의 ROI(투자 대비 효과)가 소규모에서 오히려 더 큼
</details>

**Q3**: sysMMU의 "Bypass → Enable 전환" 검증이 누락되면 어떤 Silicon 버그가 발생할 수 있는가?

<details>
<summary>정답</summary>

부트로더(Bypass 모드)에서 Linux kernel(Enable 모드)로 전환하는 시점에, 진행 중인 DMA 트랜잭션이 VA로 발행되었지만 sysMMU의 Page Table이 아직 설정 미완료인 경우 Translation Fault 발생. 이는 타이밍 의존적이므로 간헐적으로 발생하며, Silicon debug에 수 주가 소요될 수 있는 위험한 버그.
</details>

---

## Q&A

**Q: Common Task Coverage가 왜 중요한가?**
> "SoC에 50~200개 IP가 있고, 각각에 sysMMU/Security/DVFS/ClkGate 등 7~10개 공통 항목이 필요하다. 수백~수천 개 조합을 수동 관리하면 3~5%가 누락되고, 소규모 프로젝트에서는 Human Oversight가 96%를 차지한다. DVCon 논문에서 이를 정량적으로 증명했고, AI 기반 자동화로 293개/216개의 Critical Gap을 발견했다."

**Q: IP-XACT만으로는 왜 부족한가?**
> "IP-XACT는 레지스터 맵, 버스 인터페이스, 메모리 맵 등 구조적 정보만 제공한다. 그러나 'IP_X에 보안 접근 제어 검증이 필요한가?'는 시맨틱 판단이 필요하다 — IP 스펙에 '이 레지스터는 Secure-only'라고 기술되어 있어야 알 수 있다. 그래서 IP-XACT(구조) + IP Spec(시맨틱)을 Hybrid로 추출하는 것이 DVCon 논문의 핵심 차별점이다."

**Q: CCTV Coverage를 SystemVerilog로 어떻게 구현하나?**
> "IP enum × Common Task enum × Result enum의 cross coverage로 구현한다. 핵심은 ignore_bins로 N/A 조합을 제외하고, illegal_bins로 NOT_TESTED(Gap)를 감지하는 것이다. Regression 후 report_phase에서 cross coverage가 100% 미만이면 Gap이 존재함을 자동으로 경고한다. 이 covergroup을 SoC Top TB에 내장하여 모든 테스트에서 자동 수집한다."

**Q: sysMMU 통합 검증에서 가장 중요한 시나리오는?**
> "Bypass→Enable 전환이다. 부트로더에서는 sysMMU Bypass로 동작하다가 OS가 Enable로 전환하는데, 이 시점에 진행 중인 DMA 트랜잭션과 Page Table 설정의 Race Condition이 발생할 수 있다. 타이밍 의존적 간헐 버그로, Silicon에서 디버그하면 수 주가 걸린다. Pre-silicon에서 반드시 검증해야 한다."

---
!!! warning "실무 주의점 — Common Task 호출 순서 의존성 무시"
    **현상**: 개별 Common Task 시퀀스는 단독 실행 시 PASS지만, sysMMU Enable → DVFS transition 조합 시나리오에서 간헐적으로 DMA 트랜잭션이 손실된다.

    **원인**: CCTV 매트릭스는 각 (IP, Task) 쌍의 독립 검증 여부만 추적한다. Task 간 순서 의존성(sysMMU 활성화 완료 전 DVFS 주파수 변경 → 진행 중 트랜잭션 중단)은 매트릭스 커버리지에 표현되지 않아 놓치기 쉽다.

    **점검 포인트**: Virtual sequencer의 Common Task 호출 순서를 확인. `fork/join` 또는 sequential 실행 여부를 검토. CCTV 매트릭스에 Task pair 커버리지 (`cx_task_order`) 크로스 빈을 추가하여 순서 조합을 명시적으로 추적.

## 핵심 정리

- **Common Task 후보**: sysMMU access, Security 권한 검사, DVFS transition, Clock Gating, Power Domain ON/OFF.
- **CCTV 매트릭스**: IP × Common Task의 2D coverage. 모든 cell이 covered 되어야 sign-off.
- **재사용 sequence library**: 한 sequence가 여러 IP의 sequencer에 generic하게 동작 (parametric).
- **Virtual sequencer**: sub-sequencer 핸들 + Common Task별 wrapper sequence.
- **Coverage 자동 누적**: 각 IP test가 자기 Common Task 영역을 mark → 통합 시 매트릭스 자동 업데이트.

## 다음 단계

- 📝 [**Module 02 퀴즈**](quiz/02_common_task_cctv_quiz.md)
- ➡️ [**Module 03 — TB Top & AI**](03_tb_top_and_ai.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../01_soc_top_integration/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">SoC Top Integration 검증</div>
  </a>
  <a class="nav-next" href="../03_tb_top_and_ai/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">TB Top 환경 구축 + AI 자동화</div>
  </a>
</div>
