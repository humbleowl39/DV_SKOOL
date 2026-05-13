# Module 03 — TB Top & AI Automation

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🏗️</span>
    <span class="chapter-back-text">SoC Integration</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 03</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-재사용-가능한-도시-검사-장비-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-새-npu-ip-한-개를-tb-top-에-통합하는-1-cycle">3. 작은 예 — 새 NPU IP 통합 1 cycle</a>
  <a class="page-toc-link" href="#4-일반화-tb-top-3-층-과-ai-3-phase">4. 일반화 — TB Top 3층 + AI 3 Phase</a>
  <a class="page-toc-link" href="#5-디테일-config-uvm-env-ai-파이프라인-release">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Plan** TB Top 환경의 layered architecture 를 Config (JSON) → Generator → UVM Env 3 층으로 설계한다.
    - **Apply** AI (LLM + RAG/FAISS) 자동화로 sequence / coverage gap / 디버그를 보조하는 workflow 를 도입한다.
    - **Identify** AI 자동화의 한계와 인간 검토 필수 영역 (silent corruption, race condition, CDC, 비결정적 타이밍) 을 식별한다.
    - **Implement** Config 기반 동적 Agent / Checker 인스턴스화와 RAL + multi-clock 도메인을 통합한 TB Top 구조를 구현한다.
    - **Justify** 소규모 프로젝트의 Gap Rate 가 더 높은 이유를 정량 데이터 (Project A 2.75% vs Project B 4.99%) 로 설명한다.

!!! info "사전 지식"
    - [Module 01-02](01_soc_top_integration.md) — SoC Top 검증의 5 축 + CCTV 매트릭스
    - LLM 사용 경험 ([AI Engineering 코스](../../ai_engineering/) 참고)

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _8 개월 vs 1 주_

당신은 SoC 검증. 새 SoC release 마다 TB 작성 _4 주_, 검증 8 개월 → 다음 SoC 시작.

DVCon 2025 데이터 [Cadence / Synopsys]:
- **Config-driven TB + AI Gap discovery**: 4 주 → _1 주_.
- 8 개월 검증 사이클을 _1.5 개월_ 단축 가능.

**핵심 패턴**:
1. **TB Top 의 모든 component 가 _Config 기반_**: JSON 한 파일이 IP list, base address, common task matrix 정의.
2. **AI Gap discovery**: 새 IP 추가 시 _LLM 이_ 기존 spec → 자동 _Gap candidates_ 제시.
3. **사람 review + commit**: AI 가 _제안_, 사람이 _승인_.

8 개월 → 1 주 = _32 배 throughput_. 같은 팀 크기로 _8 배_ chip 가능.

이게 modern SoC DV 의 _가장 큰 ROI_ 영역.

Module 02 의 매트릭스만으로는 _Gap 을 발견_ 하지만, 발견된 Gap 을 _누가 어떤 테스트로 메우는지_ 는 여전히 수동입니다. 새 IP 가 들어오거나 base address 가 바뀌면 TB 의 agent / checker / monitor / coverage 가 _전부 손으로 갱신_ 돼야 하고, 이 과정에서 "TB 작업 4 주 → 검증 시작" 의 병목이 다시 발생합니다.

이 모듈을 건너뛰면 CCTV 가 그저 "한 번 만든 매트릭스" 로 끝나고, _다음 SoC_ 에서는 다시 처음부터 시작하게 됩니다. 반대로 **Config (JSON) 한 파일만 교체하면 모든 layer 가 자동 재구성** 되는 패턴을 잡으면, 8 개월에 한 번 짓던 TB 가 _1 주일_ 만에 release 가능한 상태가 됩니다 — 이게 DVCon 2025 가 정량적으로 보여준 가치입니다.

---

## 2. Intuition — 재사용 가능한 도시 검사 장비 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **TB Top** = _도시별로 다시 만들지 않는_ 검사 장비 세트. 도로/전기/배수 검사 절차는 도시가 바뀌어도 동일 — _도시 지도 (Config)_ 만 갈아 끼우면 같은 장비가 다른 도시도 검사할 수 있어야 한다.<br>
    **AI 자동화** = 도시 지도가 바뀔 때마다 _새 점검 항목 (Gap)_ 을 자동으로 찾아주는 보조원. 보조원이 만든 목록은 _경험 있는 검사관 (DV 엔지니어)_ 이 최종 리뷰.

### 한 장 그림 — Config → Generator → UVM Env → AI Gap loop

```d2
direction: down

CFGA: "Project A · Config_A (JSON)"
CFGB: "Project B · Config_B (JSON)"
GEN: "TB Top Generator (공통 코드)\n· parse Config\n· foreach ip in ip_list\n&nbsp;&nbsp;· spawn agent (APB/AXI 자동 판별)\n&nbsp;&nbsp;· register region in mmap_checker\n&nbsp;&nbsp;· bind interrupt monitor to irq_map\n&nbsp;&nbsp;· update CCTV ignore_bins from common_tasks\n· generate reset_seq SVA, power monitor, RAL"
ENV: "UVM Env (자동 구성, 프로젝트별 동일 구조)\nAgents · Checkers · Monitors · CCTV Coverage · Scoreboard"
AI: "AI Gap Detection Pipeline (DVCon 2025)\nIP-XACT (구조) + Spec (시맨틱) → IP profile\n→ FAISS 유사 IP 검색\n→ LLM Gap detection\n→ mrun 명령 + V-Plan bin 자동 생성"
CFGA -> GEN: "ip_list, mmap, irq_map, pd,\nreset_seq + common_tasks per IP"
CFGB -> GEN: "ip_list, mmap, irq_map, pd,\nreset_seq + common_tasks per IP"
GEN -> ENV
ENV -> AI: "regression 결과 + V-Plan"
```

### 왜 이 구조인가 — Design rationale

세 가지 변화가 동시에 흡수돼야 합니다.

1. **프로젝트 간 IP 차이**: A 는 UFS / DMA / GPU, B 는 NPU / 영상 codec / DSP. _IP 종류_ 는 다르지만 _통합 패턴_ (bus, irq, pd) 은 동일.
2. **프로젝트 내 변경**: 첫 release 후 base address 시프트, IRQ 재배치, 새 IP 추가 — TB 코드 손대기 시작하면 회귀 사이클이 깨짐.
3. **새 IP 의 Common Task 누락**: V-Plan 갱신은 인간 작업. 자동화 없이는 96.30% Human Oversight (Module 02).

이 셋의 교집합이 **Config 기반 layered TB + AI 보조 Gap detection** 이라는 패턴입니다.

---

## 3. 작은 예 — 새 NPU IP 한 개를 TB Top 에 통합하는 1 cycle

가장 단순한 시나리오. 영상 SoC 에 _새로운 NPU (Neural Processing Unit) IP_ 가 추가됨 — AXI master, DMA, sysMMU 사용, irq_out, PD_AI 도메인. 이 한 IP 가 TB Top 에 _자동 통합되는_ 1 cycle 을 추적합니다.

```d2
direction: down

T0: "**T0** · NPU IP 의 IP-XACT + Spec 도착\n· regs (control, status)\n· AXI Master, irq_out\n· 'uses sysMMU for weights' (Spec 키워드)\n· 'DVFS supported, 2 OPP'"
T1: "**T1** · Config_v2.json 갱신 (1 line edit per field)\n+ ip_list[].name='NPU'\n+ base_addr='0x15000000', size='0x10000'\n+ bus_if='AXI', has_dma=true, has_sysmmu=true\n+ irq_spi=70, power_domain='PD_AI'\n+ common_tasks=[SYSMMU,SECURITY,DVFS,CLK_GATE,POWER,RESET,IRQ]"
T2: "**T2** · TB Top Generator 재실행\n· axi_agent::create('axi_NPU', env) — Agent 자동\n· mmap_checker.add_region(NPU, 0x15000000, 64K) — MMAP 자동\n· irq_monitor.bind(NPU, spi=70) — IRQ 자동\n· cctv_cov add row IP_NPU — CCTV 자동"
T3: "**T3** · AI Gap Pipeline\nIP profile(NPU) → FAISS 검색 → 유사 IP = GPU\nLLM: 'NPU 에 sysMMU bypass→enable 검증 필요'\n'GPU 와 동일 패턴으로 추론, priority=HIGH'"
T4: "**T4** · Gap Report\nNPU × SYSMMU_bypass_enable = NOT_TESTED\n→ mrun test --test_name npu_sysmmu_test\nNPU × DVFS_transition = NOT_TESTED\n→ mrun test --test_name npu_dvfs_test"
T5: "**T5** · 엔지니어 리뷰 (15 분)\n· NPU 는 weight 캐시 때문에 DVFS race 심함 → priority HIGH 확인\n· sysMMU 는 GPU 와 동일 패턴 적용 가능 → True Positive"
T6: "**T6** · mrun 실행 → PASS\ncctv.record_result(IP_NPU, TASK_*, RESULT_PASS)\n매트릭스 NPU row 의 cell 들이 ✅ 로 채워짐"
T0 -> T1
T1 -> T2
T2 -> T3
T3 -> T4
T4 -> T5
T5 -> T6
```

### 단계별 추적

| Step | 누가 | 무엇을 | 의미 |
|---|---|---|---|
| T0 | 설계팀 | IP-XACT + Spec 전달 | 구조 + 시맨틱의 이중 입력 |
| T1 | TB Top Lead | `Config.json` 의 `ip_list` 에 NPU 추가 (단일 파일 edit) | 모든 layer 에 변경 전파 시작 |
| T2 | Generator | Agent / MMAP / IRQ / CCTV 자동 갱신 | 사람 손 필요 0 |
| T3 | AI 파이프라인 | IP profile 만들고 FAISS 로 유사 IP (GPU) 의 검증 이력 참조 | 새 IP 의 누락 가능성 _예측_ |
| T4 | LLM | Gap 별 mrun 명령 + V-Plan bin 자동 생성 | 명령어까지 그대로 실행 가능 |
| T5 | DV 엔지니어 | 15 분 리뷰: False Positive 걸러내고 priority 확인 | 인간 검토는 _quality gate_ 만 |
| T6 | regression | 실행 → PASS → matrix 갱신 | 1 cycle 끝 |

```python
# T2 의 Generator 핵심 — 단순화
def generate_tb_top(config):
    env = UvmEnv("soc_top_env")
    for ip in config["ip_list"]:
        if ip["bus_if"] == "AXI":
            env.add_agent(AxiAgent(name=f"axi_{ip['name']}", base=ip["base_addr"]))
        env.mmap_checker.add_region(ip["name"], ip["base_addr"], ip["size"])
        env.irq_monitor.bind(ip["name"], ip["irq_spi"])
        env.cctv_cov.add_row(ip["name"], applicable_tasks=ip["common_tasks"])
    env.generate_reset_seq_sva(config["reset_sequence"])
    return env
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) Config 한 파일이 모든 layer 의 single source of truth** — 사람이 두 곳을 동시에 갱신하다 어긋날 위험이 사라집니다. NPU base address 가 바뀌면 _Config 만_ 갱신, agent / mmap / SVA / RAL 이 자동 재생성.<br>
    **(2) AI 는 _제안기_ 이지 _결정기_ 가 아니다** — T3 → T4 까지는 AI 가 list 를 만들지만, T5 의 _15 분 인간 리뷰_ 가 quality gate. False Positive 는 자연스러운 비용이고, _Recall (실제 Gap 의 발견율)_ 이 더 중요한 지표입니다.

---

## 4. 일반화 — TB Top 3 층 과 AI 3 Phase

### 4.1 TB Top 의 3 층 구조

```d2
direction: down

L1: "**Layer 1 : Config** (project-specific)\nJSON — ip_list, mmap, irq_map, pd, reset\ncommon_tasks per IP"
L2: "**Layer 2 : Generator** (project-agnostic)\nparse Config → spawn Agents / Checkers / RAL\nemit reset_seq SVA, power monitor\npropagate config_db"
L3: "**Layer 3 : UVM Env** (runtime)\nAgents · Common Task Checker Layer · CCTV\nScoreboard · Coverage · Virtual Sequencer"
L1 -> L2
L2 -> L3
```

> 프로젝트 교체 ⇔ Layer 1 만 교체 (Layer 2, 3 는 불변)

### 4.2 AI 파이프라인의 3 Phase (DVCon 2025)

```
Phase 1: Hybrid Data Extraction
  IP-XACT (구조)  ─┐
  IP Spec (시맨틱) ─┴─► IP Profile { needs_sysmmu, needs_security, ... }

Phase 2: FAISS Similarity Search
  IP profile ──► embedding ──► nearest-neighbor 검색
                              ──► 유사 IP 의 검증 이력 참조

Phase 3: LLM Gap Detection + Test Generation
  IP profile + 유사 IP 이력 + 기존 V-Plan
                              ──► Gap list (priority 분류)
                              ──► mrun 명령 + V-Plan bin 자동 생성
```

### 4.3 정량 결과 (DVCon 2025)

| 지표 | Project A (대규모) | Project B (소규모) |
|------|-------------------|-------------------|
| SoC 내 IP 수 | ~200 | ~50 |
| 발견 Gap 수 | **293** | **216** |
| Gap Rate | **2.75%** | **4.99%** |
| Human Oversight 비율 | - | **96.30%** |
| New IP/Feature 누락 감소 | **~40%** | - |

**인사이트**:

```
1. 소규모 프로젝트의 Gap Rate가 더 높음 (4.99% > 2.75%)
   → 엔지니어 수가 적어 교차 검증 부족
   → 자동화의 필요성이 오히려 소규모에서 더 큼

2. Human Oversight가 96.30%
   → 기술적 어려움이 아닌 "단순 누락"이 대부분
   → 자동 체크리스트/매트릭스 관리로 해결 가능

3. New IP/Feature 누락이 40% 감소
   → 새 IP 추가 시 자동으로 Common Task 목록 갱신
   → "이전 칩에서 했으니까" 가정을 제거
```

---

## 5. 디테일 — Config, UVM Env, AI 파이프라인, Release

### 5.1 TB Top 환경 설계 (이력서 직결)

```d2
direction: down

CFGDB: "**Config DB** (JSON / CSV)\n· IP 목록, Base Address, Interrupt Map\n· Memory Map, Power Domain\n· Common Task 적용 목록"
GEN: "**TB Top Generator**\n· Config 기반 자동 인스턴스화\n· IP별 Agent 자동 연결\n· Checker / Monitor 자동 배치"
STIM: "자극원 (External Models)" {
  direction: right
  CPUM: "CPU Model / AXI Master VIP"
  MEMM: "Memory Model"
  IFM: "External IF Models"
}
DUT: "**DUT** (SoC RTL)"
CHK: "**Common Task Checker Layer**\n· Connectivity Checker (Formal / Sim)\n· Memory Map Checker (주소 접근 → 응답)\n· Interrupt Monitor (발생 → GIC → CPU)\n· Power / Clock Monitor (상태 전이)\n· CCTV Coverage Collector"
CFGDB -> GEN
GEN -> STIM
STIM -> DUT
DUT -> CHK
```

재사용 핵심:

- 프로젝트 A → `Config_A.json` → TB Top 자동 구성
- 프로젝트 B → `Config_B.json` → 같은 TB Top 프레임워크 재사용
- → "8개월 동안 구축한 환경을 여러 SoC에 배포" (이력서)

### 5.2 코드 예시 — 구체적 JSON Config

```json
{
  "soc_name": "HAWK_SoC",
  "version": "2.1",

  "ip_list": [
    {
      "name": "UFS_HCI",
      "id": "IP_UFS",
      "base_addr": "0x12000000",
      "size": "0x00100000",
      "bus_if": "APB",
      "has_dma": true,
      "has_sysmmu": true,
      "power_domain": "PD_STORAGE",
      "irq_spi": 47,
      "common_tasks": ["SYSMMU", "SECURITY", "DVFS", "CLK_GATE", "POWER", "RESET", "IRQ"]
    },
    {
      "name": "DMA_Controller",
      "id": "IP_DMA",
      "base_addr": "0x12100000",
      "size": "0x00010000",
      "bus_if": "AXI",
      "has_dma": true,
      "has_sysmmu": true,
      "power_domain": "PD_CORE",
      "irq_spi": 52,
      "common_tasks": ["SYSMMU", "SECURITY", "DVFS", "CLK_GATE", "POWER", "RESET", "IRQ"]
    },
    {
      "name": "UART_0",
      "id": "IP_UART",
      "base_addr": "0x13000000",
      "size": "0x00001000",
      "bus_if": "APB",
      "has_dma": false,
      "has_sysmmu": false,
      "power_domain": "PD_PERI",
      "irq_spi": 60,
      "common_tasks": ["SECURITY", "CLK_GATE", "POWER", "RESET", "IRQ"]
    }
  ],

  "memory_map": {
    "bootrom":  {"base": "0x00000000", "size": "0x00010000"},
    "sram":     {"base": "0x10000000", "size": "0x00100000"},
    "dram":     {"base": "0x40000000", "size": "0x80000000"}
  },

  "interrupt_map": {
    "UFS_HCI":        {"spi": 47, "type": "level", "group": "secure"},
    "DMA_Controller": {"spi": 52, "type": "edge",  "group": "non_secure"},
    "UART_0":         {"spi": 60, "type": "level", "group": "non_secure"}
  },

  "power_domains": {
    "PD_CORE":    {"always_on": true},
    "PD_STORAGE": {"always_on": false, "depends_on": "PD_CORE"},
    "PD_PERI":    {"always_on": false, "depends_on": "PD_CORE"}
  },

  "reset_sequence": [
    "PLL_LOCK",
    "BUS_FABRIC",
    "MEMORY_CONTROLLER",
    "PD_CORE_IPS",
    "PD_STORAGE_IPS",
    "PD_PERI_IPS",
    "CPU"
  ]
}
```

**Config 설계 핵심**:

| 필드 | 용도 |
|------|------|
| `ip_list[].common_tasks` | CCTV 매트릭스의 N/A 자동 결정 — 목록에 없는 Task = ignore_bins |
| `interrupt_map[].type` | Edge/Level 불일치 자동 검출 |
| `power_domains[].depends_on` | Power 시퀀스 순서 자동 검증 |
| `reset_sequence` | Reset 해제 순서 SVA 자동 생성 |

→ **프로젝트 A → Config_A.json, 프로젝트 B → Config_B.json 만 교체하면 동일 TB 프레임워크 재사용**

### 5.3 코드 예시 — Config 기반 UVM Env 자동 구성

```systemverilog
class soc_top_env extends uvm_env;
  `uvm_component_utils(soc_top_env)

  // Config (JSON에서 파싱된 데이터)
  soc_config m_cfg;

  // 동적 생성되는 컴포넌트들
  soc_memmap_checker      m_mmap_chk;
  soc_irq_monitor         m_irq_mon;
  soc_power_monitor       m_pwr_mon;
  soc_connectivity_chk    m_conn_chk;
  cctv_coverage           m_cctv_cov;

  // IP별 동적 생성되는 Agent (IP 수에 따라)
  apb_agent               m_apb_agents[$];
  axi_agent               m_axi_agents[$];

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // ---- Config 로드 ----
    if (!uvm_config_db#(soc_config)::get(this, "", "soc_cfg", m_cfg))
      `uvm_fatal("CFG", "soc_config not found")

    // ---- IP 목록 기반 Agent 동적 생성 ----
    foreach (m_cfg.ip_list[i]) begin
      ip_config ip = m_cfg.ip_list[i];

      if (ip.bus_if == "APB") begin
        apb_agent agt = apb_agent::type_id::create(
          $sformatf("apb_%s", ip.name), this);
        m_apb_agents.push_back(agt);
        // Agent에 해당 IP의 주소 범위 설정
        uvm_config_db#(apb_config)::set(this,
          $sformatf("apb_%s", ip.name), "cfg",
          create_apb_cfg(ip.base_addr, ip.size));
      end
      else if (ip.bus_if == "AXI") begin
        axi_agent agt = axi_agent::type_id::create(
          $sformatf("axi_%s", ip.name), this);
        m_axi_agents.push_back(agt);
      end
    end

    // ---- Checker 생성 (Config 기반) ----
    m_mmap_chk = soc_memmap_checker::type_id::create("mmap_chk", this);
    m_irq_mon  = soc_irq_monitor::type_id::create("irq_mon", this);
    m_conn_chk = soc_connectivity_chk::type_id::create("conn_chk", this);

    // Power Domain이 있는 IP가 하나라도 있으면 Power Monitor 생성
    if (m_cfg.has_any_power_domain())
      m_pwr_mon = soc_power_monitor::type_id::create("pwr_mon", this);

    // ---- CCTV Coverage ----
    // Config의 ip_list + common_tasks로 ignore_bins 자동 결정
    m_cctv_cov = cctv_coverage::type_id::create("cctv_cov", this);
    uvm_config_db#(soc_config)::set(this, "cctv_cov", "soc_cfg", m_cfg);

    // ---- Memory Map을 Checker에 전파 ----
    uvm_config_db#(memmap_config)::set(this, "mmap_chk", "cfg",
      build_memmap_from_config(m_cfg));

    // ---- Interrupt Map을 Monitor에 전파 ----
    uvm_config_db#(irq_config)::set(this, "irq_mon", "cfg",
      build_irq_map_from_config(m_cfg));
  endfunction

  // Config에서 Memory Map 구조체 생성
  function memmap_config build_memmap_from_config(soc_config cfg);
    memmap_config mmap = new();
    foreach (cfg.ip_list[i]) begin
      mmap.add_region(
        .name(cfg.ip_list[i].name),
        .base(cfg.ip_list[i].base_addr),
        .size(cfg.ip_list[i].size)
      );
    end
    return mmap;
  endfunction
endclass
```

**자동 구성 흐름**:
```
JSON Config
  │
  ├─→ ip_list → Agent 동적 생성 (APB/AXI 자동 판별)
  ├─→ memory_map → Memory Map Checker 설정
  ├─→ interrupt_map → Interrupt Monitor 설정
  ├─→ power_domains → Power Monitor 생성 여부 결정
  ├─→ common_tasks → CCTV ignore_bins 자동 생성
  └─→ reset_sequence → Reset 순서 SVA 자동 생성

→ 새 프로젝트: JSON만 교체하면 모든 Checker가 자동 재설정
```

### 5.4 AI 기반 CCTV 자동화 파이프라인

```d2
direction: down

IN: "입력" {
  direction: right
  IPXACT: "IP-XACT\n(구조)"
  SPEC: "IP Spec\n(시맨틱)"
  VPLAN: "기존\nV-Plan"
}
P1: "**Phase 1 : IP 프로파일 생성**\nIP-XACT → 레지스터, 버스, 메모리맵\nIP Spec → 기능, 보안, 동작 모드\n결합 → IP별 '필요 Common Task 목록'"
P2: "**Phase 2 : Gap Detection**\nIP별 필요 Task vs 기존 V-Plan 항목\n차이 = Gap (누락)\nFAISS 검색: 유사 IP 검증 이력 참조"
P3: "**Phase 3 : Test Generation**\nGap별 테스트 명령어 자동 생성 (mrun)\nV-Plan bin 자동 생성\n우선순위 분류 (보안 > 기능 > 성능)"
OUT: "**CCTV Gap Report**\n· IP별 누락 항목 목록\n· 테스트 실행 명령어\n· V-Plan 추가 항목\n· 우선순위별 정렬"
IPXACT -> P1
SPEC -> P1
VPLAN -> P2
P1 -> P2
P2 -> P3
P3 -> OUT
```

#### Gap Report 예시

```json
{
  "ip": "DMA_Controller",
  "gap_task": "sysMMU",
  "gap_detail": "sysMMU Bypass→Enable 전환 시 DMA 동작 검증 누락",
  "source": "IP_Spec_Section_4.3 + IP-XACT_sysMMU_connection",
  "priority": "HIGH",
  "test_cmd": "mrun test --test_name dma_sysmmu_bypass_to_enable --sys_name soc_top",
  "vplan_bin": "DMA.common_task.sysMMU.bypass_enable_transition"
}
```

### 5.5 AI 파이프라인 상세 — 실무 구현

#### Phase 1: IP 프로파일 Embedding

```python
# IP Spec + IP-XACT에서 IP 프로파일 생성
def create_ip_profile(ip_xact_path, ip_spec_path):
    """
    IP-XACT: 구조적 정보 (레지스터, 버스, 메모리맵)
    IP Spec: 시맨틱 정보 (기능 설명, 보안 요구사항, 동작 모드)
    """
    # 구조 정보 추출
    structural = parse_ip_xact(ip_xact_path)
    # 시맨틱 정보 추출 (PDF → 텍스트 → 키워드)
    semantic = extract_from_spec(ip_spec_path, keywords=[
        "secure", "DMA", "interrupt", "clock gating",
        "power domain", "DVFS", "sysMMU", "IOMMU"
    ])

    # IP 프로파일 = 구조 + 시맨틱 결합
    profile = {
        "ip_name": structural["name"],
        "has_dma": structural["has_axi_master"] or "DMA" in semantic,
        "needs_sysmmu": structural["has_axi_master"] and "sysMMU" in semantic,
        "needs_security": any(r["secure"] for r in structural["registers"]),
        "needs_dvfs": "DVFS" in semantic or "frequency scaling" in semantic,
        "needs_clk_gate": "clock gating" in semantic or "idle" in semantic,
        "needs_power": structural["power_domain"] is not None,
        "common_tasks_required": []  # 아래에서 결정
    }

    # Common Task 필요 여부 판단
    task_map = {
        "SYSMMU": profile["needs_sysmmu"],
        "SECURITY": profile["needs_security"],
        "DVFS": profile["needs_dvfs"],
        "CLK_GATE": profile["needs_clk_gate"],
        "POWER": profile["needs_power"],
        "RESET": True,  # 모든 IP에 필수
        "IRQ": structural["has_interrupt"],
    }
    profile["common_tasks_required"] = [k for k, v in task_map.items() if v]

    return profile
```

#### Phase 2: FAISS 기반 유사 IP 검색

```python
import faiss
import numpy as np

class IPProfileIndex:
    """
    IP 프로파일을 Embedding하여 FAISS로 인덱싱.
    새 IP가 추가되면 유사 IP의 검증 이력을 참조하여 Gap 예측.
    """
    def __init__(self, embedding_model):
        self.model = embedding_model
        self.index = faiss.IndexFlatL2(768)  # 768-dim embedding
        self.ip_names = []
        self.ip_profiles = []

    def add_ip(self, profile):
        # IP 프로파일을 텍스트로 변환 → Embedding
        text = profile_to_text(profile)
        embedding = self.model.encode(text)
        self.index.add(np.array([embedding], dtype=np.float32))
        self.ip_names.append(profile["ip_name"])
        self.ip_profiles.append(profile)

    def find_similar(self, new_ip_profile, top_k=5):
        """새 IP와 유사한 기존 IP 검색 → 검증 이력 참조"""
        text = profile_to_text(new_ip_profile)
        query = self.model.encode(text)
        distances, indices = self.index.search(
            np.array([query], dtype=np.float32), top_k)
        return [(self.ip_names[i], self.ip_profiles[i], distances[0][j])
                for j, i in enumerate(indices[0])]

# 사용 예시:
# 새 NPU IP 추가 시 → 유사 IP(GPU, DSP)의 검증 이력 참조
# → GPU에 적용된 Common Task가 NPU에도 필요할 가능성 높음
```

#### Phase 3: LLM 기반 Gap Detection 프롬프트

```python
def detect_gaps(ip_profile, existing_vplan, similar_ips):
    """
    IP 프로파일 + 기존 V-Plan + 유사 IP 이력 → Gap 발견
    """
    prompt = f"""
    당신은 SoC 검증 전문가입니다.

    [IP 정보]
    IP 이름: {ip_profile['ip_name']}
    필요 Common Tasks: {ip_profile['common_tasks_required']}
    특성: DMA={ip_profile['has_dma']}, sysMMU={ip_profile['needs_sysmmu']},
          Security={ip_profile['needs_security']}

    [기존 V-Plan에서 수행된 검증 항목]
    {format_vplan_items(existing_vplan)}

    [유사 IP의 검증 이력]
    {format_similar_ip_history(similar_ips)}

    [요청]
    1. 필요 Common Tasks 중 V-Plan에 없는 항목(Gap)을 나열하세요.
    2. 각 Gap에 대해:
       - 왜 필요한지 (근거: IP 특성 또는 유사 IP 이력)
       - 구체적 테스트 시나리오 (1-2문장)
       - 우선순위 (HIGH/MEDIUM/LOW)
       - mrun 테스트 명령어
    3. 유사 IP에서 수행되었지만 이 IP에 없는 추가 검증도 제안하세요.

    JSON 형식으로 출력하세요.
    """
    return llm_call(prompt)
```

**AI 파이프라인 핵심 차별점**:
```
기존 (IP-XACT only):
  "이 IP에 AXI Master 포트가 있다" → 구조적 사실만 알 수 있음
  "이 IP에 sysMMU 검증이 필요한가?" → 판단 불가

Hybrid (IP-XACT + Spec + FAISS + LLM):
  IP-XACT: AXI Master 포트 존재 확인
  IP Spec: "sysMMU를 통해 메모리 접근" 기술 발견
  FAISS: 유사 IP(GPU)에서 sysMMU 검증이 수행된 이력 참조
  LLM: 종합 판단 → "sysMMU 검증 필요, 특히 Bypass→Enable 전환 중요"
```

### 5.6 Gap Report → V-Plan 반영 실무 워크플로우

```d2
direction: down

S1: "**Step 1 · CCTV Gap Report 생성** (AI 파이프라인)\nDMA × sysMMU_bypass_enable = NOT_TESTED\nGPU × Security_TZPC = NOT_TESTED\nUSB × DVFS_transition = NOT_TESTED\nTotal: 12 gaps"
S2: "**Step 2 · 우선순위 분류** (자동)\nHIGH (보안/안정성): GPU × Security_TZPC,\n&nbsp;&nbsp;DMA × sysMMU_bypass_enable\nMEDIUM (기능): USB × DVFS_transition · ...\nLOW (성능): ..."
S3: "**Step 3 · V-Plan bin 자동 생성**\nvplan_additions.json:\n{ feature: 'DMA.common_task.sysMMU',\n&nbsp;&nbsp;bin: 'bypass_enable_transition',\n&nbsp;&nbsp;test: 'dma_sysmmu_bypass_test',\n&nbsp;&nbsp;priority: 'HIGH' }, ..."
S4: "**Step 4 · 테스트 명령어 자동 생성**\nmrun test --test_name dma_sysmmu_bypass_test --sys_name soc_top\nmrun test --test_name gpu_security_tzpc_test --sys_name soc_top"
S5: "**Step 5 · IP 담당 엔지니어 배포**\n담당자별 Gap 목록 + 테스트 명령어 + 우선순위"
S6: "**Step 6 · 실행 후 CCTV 매트릭스 갱신**\ncctv_cov.record_result(IP_DMA, TASK_SYSMMU, RESULT_PASS)\n→ Coverage 재집계 → Gap 감소 확인"
S1 -> S2
S2 -> S3
S3 -> S4
S4 -> S5
S5 -> S6
```

### 5.7 TB Top Release 프로세스 상세

```
Phase 1: RTL 수령 및 Config 생성 (1-2일)
  ☐ RTL freeze 확인 (feature freeze, not bug-free)
  ☐ IP-XACT 메타데이터 수령
  ☐ SoC Config JSON 생성/갱신
    - 새 IP 추가, 삭제된 IP 제거
    - 주소 변경 반영
    - 인터럽트 맵 갱신
  ☐ Config 리뷰 (설계팀과 크로스체크)

Phase 2: TB Top 자동 구성 (1일)
  ☐ TB Top Generator 실행 → 환경 자동 생성
  ☐ 새 IP에 대한 Agent stub 확인
  ☐ Memory Map Checker 설정 갱신 확인
  ☐ Interrupt Monitor 맵 갱신 확인
  ☐ CCTV ignore_bins 자동 갱신 확인

Phase 3: Sanity 검증 (2-3일)
  ☐ Compile 성공
  ☐ Elaboration 성공
  ☐ Boot test (BootROM 실행 → DRAM 접근)
  ☐ 각 IP Base Address R/W (Memory Map 정상)
  ☐ 각 IP 인터럽트 발생/클리어 (IRQ Routing 정상)

Phase 4: Common Task 시나리오 배포 (1-2일)
  ☐ CCTV Gap Report 생성 (AI 파이프라인)
  ☐ 이전 프로젝트 대비 새 Gap 식별
  ☐ IP별 담당자에게 Gap 목록 + 테스트 배포
  ☐ V-Plan 갱신

Phase 5: Release (1일)
  ☐ TB Top 환경 패키지화
  ☐ Release Note 작성 (변경사항, 알려진 이슈)
  ☐ 각 IP DV 엔지니어에게 환경 배포
  ☐ Kick-off 미팅 (환경 사용법, CCTV 목표 공유)

→ 총 ~1주일, 이후 각 IP 팀이 Common Task 검증 수행
→ TB Top Lead 역할: 이 프로세스 전체를 설계하고 운영 + CCTV 추적
```

### 5.8 면접 종합 Q&A

**Q: TB Top 환경을 어떻게 설계했고, 어떤 가치가 있었나?**
> "프로젝트 공통 프레임워크로 설계했다. IP 목록, 메모리 맵, 인터럽트 맵을 Config(JSON)으로 정의하면 TB Top Generator 가 자동으로 환경을 구성한다. Common Task Checker Layer 를 내장하여 Connectivity, Memory Map, Interrupt, Power 검증을 자동 수행한다. 이 환경을 여러 SoC 프로젝트에 배포하여 프로젝트마다 TB 를 처음부터 만드는 비용을 제거했다."

**Q: DVCon 논문의 CCTV 방법론을 설명하라.**
> "SoC 내 모든 IP 에 공통적으로 필요한 검증 항목 (sysMMU, Security, DVFS 등) 이 빠짐없이 수행되었는지 자동 추적하는 방법론이다. IP-XACT (구조) + IP Spec (시맨틱) 의 Hybrid Extraction 으로 IP 별 필요 Common Task 를 판단하고, 기존 V-Plan 과 비교하여 Gap 을 자동 발견한다. LLM 이 테스트 명령어까지 생성한다. Project A 에서 293 개 (2.75%), Project B 에서 216 개 (4.99%) 의 Gap 을 발견했고, Human Oversight 가 96.30% 임을 정량적으로 증명했다."

**Q: 소규모 프로젝트의 Gap Rate 가 더 높은 이유는?**
> "엔지니어 수가 적어 교차 검증이 부족하기 때문이다. 대규모에서는 IP 별 전담 인력이 있어 상호 검토가 자연스럽지만, 소규모에서는 한 사람이 여러 IP 를 담당하여 누락 가능성이 높아진다. 이것이 '자동화가 소규모에서 오히려 더 필요하다' 는 논문의 핵심 인사이트이다."

### 5.9 연습 — 한 번 더 손으로 풀어보기

#### 문제 1: Config 에서 CCTV ignore_bins 자동 도출

다음 JSON Config 의 IP 3 개에 대해 CCTV 매트릭스를 그리고, ignore_bins 가 되어야 할 셀을 표시하라.

```json
{
  "ip_list": [
    {"name": "GPU",  "has_dma": true, "has_sysmmu": true,
     "common_tasks": ["SYSMMU","SECURITY","DVFS","CLK_GATE","POWER","RESET","IRQ"]},
    {"name": "I2C",  "has_dma": false, "has_sysmmu": false,
     "common_tasks": ["SECURITY","CLK_GATE","RESET","IRQ"]},
    {"name": "Temp_Sensor", "has_dma": false, "has_sysmmu": false,
     "common_tasks": ["RESET"]}
  ]
}
```

**사고과정**:
```
1. 매트릭스 (✅ = 검증 필요, ⬜ = ignore_bins):

              | SYSMMU | SECURITY | DVFS | CLK_GATE | POWER | RESET | IRQ |
   GPU        |   ✅   |    ✅    |  ✅  |    ✅    |  ✅   |  ✅   | ✅  |
   I2C        |   ⬜   |    ✅    |  ⬜  |    ✅    |  ⬜   |  ✅   | ✅  |
   Temp_Sensor|   ⬜   |    ⬜    |  ⬜  |    ⬜    |  ⬜   |  ✅   | ⬜  |

2. ignore_bins 수: GPU 0, I2C 3, Temp_Sensor 6 → 총 9
3. 유효 조합: 21 - 9 = 12 → 이 12개가 모두 PASS여야 closure
4. 코드:
   ignore_bins i2c_no_mmu = binsof(cp_ip) intersect {IP_I2C}
                           && binsof(cp_task) intersect {TASK_SYSMMU};
   // ... (총 9개)

→ Config의 common_tasks 필드에서 자동으로 도출 가능
→ 새 프로젝트에서 Config만 교체하면 ignore_bins도 자동 갱신
```

#### 문제 2: AI Gap Detection 정확도 분석

AI 파이프라인이 다음 결과를 냈다. False Positive 와 True Positive 를 분류하고, 정밀도 (Precision) 를 계산하라.

```
AI가 발견한 Gap 목록 (10개):
1. DMA × sysMMU_bypass_enable       → 실제 Gap (V-Plan에 없음)
2. GPU × Security_TZPC              → 실제 Gap
3. UART × sysMMU                    → False Positive (UART에 DMA 없음, N/A)
4. UFS × DVFS_transition            → 실제 Gap
5. I2C × Power_domain               → False Positive (I2C는 Always-ON)
6. Crypto × sysMMU                  → False Positive (내부 메모리만 사용)
7. Ethernet × CLK_GATE_wakeup       → 실제 Gap
8. Display × IRQ_edge_level         → 실제 Gap
9. SPI × DVFS                       → False Positive (고정 클럭 IP)
10. USB × Security_DFU              → 실제 Gap
```

**사고과정**:
```
1. TP: #1, #2, #4, #7, #8, #10 = 6개
   FP: #3, #5, #6, #9 = 4개

2. Precision = TP / (TP + FP) = 6 / 10 = 60%

3. False Positive 원인:
   #3, #5: IP-XACT 정보 부족 (DMA / Power 정보)
   #6, #9: Spec 시맨틱 추출 부족 ("internal memory", "fixed clock")
   → 개선: IP-XACT 파싱 정밀도 + Spec keyword 확장 + FAISS cross-validation

4. 실무 관점:
   Precision 60% 는 낮아 보이지만, 10 개 중 6 개가 실제 Critical Gap
   → 자동화 없이는 이 6 개를 모두 놓칠 수 있었음
   → False Positive 는 엔지니어 리뷰에서 빠르게 제거 가능
   → Recall (실제 Gap 발견율) 이 더 중요한 지표
```

#### 문제 3: TB Top Release 시 Config 변경 영향 분석

이전 프로젝트에서 새 프로젝트로 Config 를 갱신할 때, 다음 변경사항이 TB Top 에 미치는 영향을 분석하라.

```
변경사항:
  1. 새 IP 추가: NPU (Neural Processing Unit), AXI, DMA 지원
  2. 기존 IP 제거: I2C_1 (사용하지 않음)
  3. UFS Base Address 변경: 0x1200_0000 → 0x1400_0000
  4. Interrupt 변경: DMA SPI 52 → SPI 55
```

**사고과정**:
```
1. NPU 추가:
   Agent (AXI), MMAP, IRQ Monitor, Connectivity, CCTV row 추가
   FAISS: 유사 IP(GPU) 검색 → 검증 이력 전이
   자동: Config 변경만으로 모든 layer 자동 갱신
   수동: NPU 전용 시나리오 (AI 추론 정확도 등)

2. I2C_1 제거:
   Agent / MMAP / CCTV row 자동 제거
   주의: 해당 주소에 새 IP 가 배치됐는지 확인

3. UFS Base 변경:
   MMAP Checker 자동 갱신 (Config 기반이라면)
   하드코딩된 0x1200_0000 사용 테스트는 갱신 필요

4. DMA SPI 변경:
   IRQ Monitor + Connectivity SVA 자동 재생성
   하드코딩된 SPI[52] 테스트는 갱신 필요

총 영향:
  Config 기반: JSON 갱신 → Generator 재실행 → 대부분 자동
  수동 필요: NPU 전용 시나리오, 하드코딩된 주소/SPI 수정
  CCTV: NPU row 추가, I2C_1 row 제거 → Gap Report 재생성
```

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'AI 가 커버리지 갭과 테스트를 자동 생성하면 DV 엔지니어 불필요'"
    **실제**: AI 는 구조 정보 (IP-XACT, 스펙 문서) 에서 패턴을 생성하지만, Clock Domain 경계·비결정적 타이밍·하드웨어 특화 제약은 DV 엔지니어가 검토하고 보완해야 합니다. AI 는 _제안기_, 사람은 _quality gate_.<br>
    **왜 헷갈리는가**: 소프트웨어 테스트 자동화와 달리 하드웨어 검증은 타이밍·물리적 제약이 존재하는데, AI 도구의 마케팅이 이 차이를 과소 설명.

!!! danger "❓ 오해 2 — 'Config 기반 TB 는 처음 만들 때만 어렵다'"
    **실제**: Layer 2 (Generator) 의 _초기 추상화 비용_ 이 크지만, _다음 프로젝트부터_ ROI 가 폭발적으로 좋아집니다. 8 개월 → 1 주일. DVCon 의 핵심 메시지.<br>
    **왜 헷갈리는가**: 단일 프로젝트만 보면 "그냥 만든 게 빠르다" 가 맞지만, 멀티 프로젝트에서는 정반대.

!!! danger "❓ 오해 3 — 'AI 가 만든 시퀀스는 multi-clock 환경에서도 그대로 동작'"
    **실제**: LLM 은 IP-XACT 구조 정보에서 clock domain 경계를 추론하지 못합니다. AI 가 생성한 시퀀스 초안은 단일 클럭 가정 하에 fork/join 패턴을 사용하는 경우가 많아, 리뷰 없이 적용하면 CDC 무검증 상태가 됩니다.<br>
    **왜 헷갈리는가**: 코드가 컴파일되고 동작하는 것처럼 보이기 때문.

!!! danger "❓ 오해 4 — 'AI Precision 60% 는 못 쓸 수준'"
    **실제**: Recall (실제 Gap 의 발견율) 이 더 중요합니다. False Positive 는 _15 분 인간 리뷰_ 로 제거되지만, 발견 못한 Gap 은 _silicon 에서_ 만나게 됩니다. 60% Precision + 90% Recall 이면 자동화의 가치가 큼.<br>
    **왜 헷갈리는가**: 분류 모델 평가에서 Precision 만 강조되는 일반 ML 직관.

!!! danger "❓ 오해 5 — 'IP-XACT 만 잘 정리하면 자동화 끝'"
    **실제**: IP-XACT 는 _구조_ 만 담습니다. "이 IP 에 보안 검증이 필요한가?", "DVFS 를 지원하는가?" 같은 시맨틱 판단은 _IP Spec_ 의 텍스트에서만 추출 가능. 그래서 Hybrid extraction.<br>
    **왜 헷갈리는가**: IP-XACT 가 _machine readable_ 이라 모든 정보를 담고 있을 것 같은 인상.

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| `soc_config not found` UVM_FATAL | Config 파일 로드 실패 | `uvm_config_db::set` 의 호출 위치 / JSON 경로 |
| 새 IP 추가 후 agent 가 안 만들어짐 | Generator 가 `bus_if` 분기 못 처리 | Generator 의 APB/AXI dispatch + Config 의 `bus_if` 값 |
| MMAP checker 가 새 IP 무시 | `build_memmap_from_config` 미호출 | `build_phase` 의 config_db propagation |
| CCTV ignore_bins 가 자동 갱신 안 됨 | covergroup 이 build 시점에 freeze | covergroup 인스턴스화를 Config 로드 _이후로_ 이동 |
| IRQ SPI 변경했는데 옛날 인덱스가 SVA 에 남음 | reset_seq SVA 가 코드 내장 | Generator 의 SVA emit 단계 / 컴파일 캐시 |
| AI Gap Report 의 50%+ 가 False Positive | Phase 1 IP profile 정확도 | IP-XACT 파싱 + Spec keyword 추출 + FAISS top-k |
| AI 생성 시퀀스가 multi-clock 환경에서 race | clock_domain 정보 누락 | Config 의 `clock_domain` 필드 + virtual sequencer fork/join |
| Project A → Project B 이전 시 컴파일 실패 | Layer 2 (Generator) 가 project-specific 누설 | Layer 분리 위반 — IP 이름 hardcoding 검색 |

---

## 7. 핵심 정리 (Key Takeaways)

- **TB Top 3 층**: Config (project-specific) / Generator (project-agnostic) / UVM Env (runtime). 프로젝트 교체 = Config 만 교체.
- **AI 3 Phase**: Hybrid Extraction (IP-XACT + Spec) → FAISS 유사 IP 검색 → LLM Gap detection + 명령 생성. Recall 중심으로 평가.
- **AI 한계**: silent corruption / race / CDC / 비결정적 타이밍은 _인간 검토 필수_. AI 는 _제안기_, 사람은 _quality gate_.
- **정량 결과**: Project A 293 gaps (2.75%), Project B 216 gaps (4.99%), Human Oversight 96.30%, New IP/Feature 누락 -40%.
- **Workflow**: spec change → Config 갱신 → Generator → AI Gap report → 인간 리뷰 → mrun → CCTV 매트릭스 갱신.

!!! warning "실무 주의점 — AI 생성 시퀀스의 Clock Domain 무시"
    **현상**: AI 가 생성한 시퀀스가 단일 클럭 기준으로 작성되어, 멀티 클럭 도메인 TB 에서 적용 시 서로 다른 도메인 에이전트에 동기화 없이 동시 구동되어 데이터 레이스가 발생한다.

    **원인**: LLM 은 IP-XACT 구조 정보에서 clock domain 경계를 추론하지 못한다. AI 가 생성한 시퀀스 초안은 단일 클럭 가정 하에 fork/join 패턴을 사용하는 경우가 많아, 리뷰 없이 그대로 적용하면 CDC 무검증 상태가 된다.

    **점검 포인트**: AI 생성 시퀀스에서 각 에이전트 `start_item` / `finish_item` 앞에 해당 에이전트의 클럭 도메인을 명시했는지 확인. TB Top Config JSON 의 `clock_domain` 필드가 에이전트 연결과 일치하는지 대조.

### 7.1 자가 점검

!!! question "🤔 Q1 — Config-driven TB 설계 (Bloom: Apply)"
    JSON config 에 _어떤 필드_ 가 있어야 _TB top 자동 생성_?

    ??? success "정답"
        - **IP list**: instance name, type, parameters.
        - **Interface map**: port → bus connections.
        - **Clock domain**: 각 IP 의 clock_domain field.
        - **Base address**: BAR / register map.
        - **Interrupt map**: SPI / MSI number.
        - **Common Task list**: 각 IP 가 받을 task.

        Generator 가 이 JSON 으로 _UVM agent / scoreboard / connect_ 자동 작성.

!!! question "🤔 Q2 — AI 생성 결과 검증 (Bloom: Analyze)"
    AI 가 sequence 생성. 어떻게 _human review 효율_?

    ??? success "정답"
        3-step:
        1. **Lint**: 문법 / UVM 패턴 / 명명 규칙 자동 체크. 50% reject.
        2. **Diff**: 기존 sequence 와 비교 — 새로운 부분만 highlight. 인간 부담 ↓.
        3. **Test pilot**: AI 생성 sequence 를 _short regression_ → fail / pass 로 신뢰도 측정.

        Final human review = _high-confidence_ sequence 만. 시간 _10×_ 단축.

!!! question "🤔 Q3 — AI 자동화 ROI (Bloom: Evaluate)"
    8 개월 → 1 주. _과대 평가_ 가능성?

    ??? success "정답"
        Caveats:
        - **First-time setup**: 자동화 인프라 (Generator, AI prompt template) 구축 _수개월_.
        - **Maintenance**: spec 변경 시 _Generator update_ 필요.
        - **Edge case**: 자동 생성된 90% 의 _확장 가능_, 10% 는 _수동_ 작성.

        실제 ROI: 첫 SoC _8 개월_, 두 번째 _3 주_, 세 번째부터 _1 주_. _누적_ 으로 _10×+_ 효과.

### 7.2 출처

**External**
- DVCon 2025 *AI-assisted Verification* papers
- Synopsys VC Spyglass AI / Cadence Verisium AI
- ChipNeMo (NVIDIA), 2023

---

## 다음 모듈

→ [Module 04 — Quick Reference Card](04_quick_reference_card.md): 5 축, CCTV 매트릭스, 정량 데이터, 디버그 체크리스트를 한 장에 정리.

[퀴즈 풀어보기 →](quiz/03_tb_top_and_ai_quiz.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../02_common_task_cctv/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Common Task & CCTV (Common Task Coverage Verification)</div>
  </a>
  <a class="nav-next" href="../04_quick_reference_card/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">SoC Integration & CCTV — Quick Reference Card</div>
  </a>
</div>


--8<-- "abbreviations.md"
