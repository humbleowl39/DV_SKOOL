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
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#tb-top-환경-설계-이력서-직결">TB Top 환경 설계 (이력서 직결)</a>
  <a class="page-toc-link" href="#ai-기반-cctv-자동화-파이프라인">AI 기반 CCTV 자동화 파이프라인</a>
  <a class="page-toc-link" href="#성과-정량적-데이터">성과 — 정량적 데이터</a>
  <a class="page-toc-link" href="#면접-종합-qa">면접 종합 Q&A</a>
  <a class="page-toc-link" href="#코드-예시-구체적-json-config">코드 예시: 구체적 JSON Config</a>
  <a class="page-toc-link" href="#코드-예시-config-기반-uvm-env-자동-구성">코드 예시: Config 기반 UVM Env 자동 구성</a>
  <a class="page-toc-link" href="#ai-파이프라인-상세-실무-구현">AI 파이프라인 상세: 실무 구현</a>
  <a class="page-toc-link" href="#gap-report-v-plan-반영-실무-워크플로우">Gap Report → V-Plan 반영 실무 워크플로우</a>
  <a class="page-toc-link" href="#tb-top-release-프로세스-상세">TB Top Release 프로세스 상세</a>
  <a class="page-toc-link" href="#연습-문제">연습 문제</a>
  <a class="page-toc-link" href="#퀴즈">퀴즈</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Plan** TB Top 환경의 재사용성을 위한 layered architecture 설계
    - **Apply** AI (LLM) 자동화로 sequence/coverage gap/디버그를 보조하는 workflow 도입
    - **Identify** AI 자동화의 한계와 인간 검토 필수 영역 (silent corruption, race condition)
    - **Implement** RAL + multi-clock domain + 다양한 IP를 통합한 TB Top 구조

!!! info "사전 지식"
    - [Module 01-02](01_soc_top_integration.md)
    - LLM 사용 경험 ([AI Engineering 코스](../../ai_engineering/) 참고)

## 핵심 개념
**TB Top = SoC 전체를 감싸는 검증 환경으로 여러 프로젝트에 재사용 가능하도록 설계. AI 자동화 = CCTV 매트릭스의 Gap을 자동 발견하고 테스트 생성까지 수행. 이 둘의 조합이 SoC 통합 검증의 효율을 극대화.**

!!! tip "💡 이해를 위한 비유"
    **TB Top** ≈ **재사용 가능한 도시 검사 장비 세트**

    도시마다 건물 종류는 달라도 전기·수도·소방 검사 절차는 동일하다. TB Top은 프로젝트가 바뀌어도 공통 검사 장비(VIP, Scoreboard)는 그대로 쓰고, IP별 어댑터(Config JSON)만 교체하는 방식으로 검증 효율을 높인다.

!!! danger "❓ 흔한 오해"
    **오해**: AI가 커버리지 갭을 자동으로 발견하고 테스트까지 생성하면 DV 엔지니어 없이도 검증이 완료된다.

    **실제**: AI는 구조 정보(IP-XACT, 스펙 문서)에서 패턴을 생성하지만, Clock Domain 경계·비결정적 타이밍·하드웨어 특화 제약은 DV 엔지니어가 검토하고 보완해야 한다.

    **왜 헷갈리는가**: 소프트웨어 테스트 자동화와 달리 하드웨어 검증은 타이밍·물리적 제약이 존재하는데, AI 도구의 마케팅이 이 차이를 과소 설명하기 때문이다.
---

## TB Top 환경 설계 (이력서 직결)

### 재사용 가능한 TB Top 구조

```
+------------------------------------------------------------------+
|  SoC Top TB (프로젝트 공통 프레임워크)                             |
|                                                                   |
|  +-----------+  프로젝트별 설정                                   |
|  | Config DB |  - IP 목록, Base Address, Interrupt Map            |
|  | (JSON/CSV)|  - Memory Map, Power Domain                       |
|  +-----------+  - Common Task 적용 목록                           |
|       |                                                           |
|  +----+---------------------------------------------------+      |
|  | TB Top Generator                                        |      |
|  |  - Config 기반 자동 인스턴스화                           |      |
|  |  - IP별 Agent 자동 연결                                  |      |
|  |  - Checker/Monitor 자동 배치                             |      |
|  +----------------------------------------------------------+     |
|       |                                                           |
|  +----+-----------+  +----------+  +------------------+           |
|  | CPU Model /    |  | Memory   |  | External IF      |           |
|  | AXI Master VIP |  | Model    |  | Models           |           |
|  +----------------+  +----------+  +------------------+           |
|       |                   |               |                       |
|  +----+-------------------+---------------+---+                   |
|  |              DUT (SoC RTL)                  |                   |
|  +---------------------------------------------+                   |
|       |                                                           |
|  +----+---------------------------------------------------+      |
|  | Common Task Checker Layer                                |      |
|  |  - Connectivity Checker (Formal 또는 Sim 기반)           |      |
|  |  - Memory Map Checker (주소 접근 → 응답 확인)            |      |
|  |  - Interrupt Monitor (발생 → GIC → CPU 경로 추적)        |      |
|  |  - Power/Clock Monitor (상태 전이 추적)                  |      |
|  |  - CCTV Coverage Collector                               |      |
|  +----------------------------------------------------------+     |
+------------------------------------------------------------------+

재사용 핵심:
  프로젝트 A → Config_A.json → TB Top 자동 구성
  프로젝트 B → Config_B.json → 같은 TB Top 프레임워크 재사용
  → "8개월 동안 구축한 환경을 여러 SoC에 배포" (이력서)
```

### TB Top Release 프로세스

```
1. SoC 설계 팀에서 RTL + IP-XACT 전달
2. Config 생성 (IP 목록, 메모리 맵, 인터럽트 맵)
3. TB Top Generator로 환경 자동 구성
4. Sanity Test 실행 (부팅, 기본 R/W)
5. Common Task 시나리오 배포
6. 각 IP 담당 엔지니어에게 환경 + 시나리오 릴리즈

→ TB Top Lead의 역할: 이 프로세스 전체를 설계하고 운영
```

---

## AI 기반 CCTV 자동화 파이프라인

### 전체 흐름

```
+------------------------------------------------------------------+
|  CCTV Automation Pipeline (DVCon 2025)                            |
|                                                                   |
|  입력:                                                            |
|  +--------+  +---------+  +--------+                              |
|  | IP-XACT|  | IP Spec |  | 기존   |                              |
|  | (구조) |  | (시맨틱)|  | V-Plan |                              |
|  +---+----+  +----+----+  +---+----+                              |
|      |            |            |                                   |
|      v            v            v                                   |
|  +--------------------------------------------------+            |
|  | Phase 1: IP 프로파일 생성                         |            |
|  |  IP-XACT → 레지스터, 버스, 메모리맵               |            |
|  |  IP Spec → 기능, 보안, 동작 모드                  |            |
|  |  결합 → IP별 "필요 Common Task 목록"              |            |
|  +--------------------------------------------------+            |
|      |                                                            |
|      v                                                            |
|  +--------------------------------------------------+            |
|  | Phase 2: Gap Detection                            |            |
|  |  IP별 필요 Task 목록 vs 기존 V-Plan 항목          |            |
|  |  차이 = Gap (누락)                                |            |
|  |  FAISS 검색: 유사 IP의 검증 이력 참조             |            |
|  +--------------------------------------------------+            |
|      |                                                            |
|      v                                                            |
|  +--------------------------------------------------+            |
|  | Phase 3: Test Generation                          |            |
|  |  Gap별 테스트 명령어 자동 생성 (mrun 형식)        |            |
|  |  V-Plan bin 자동 생성                             |            |
|  |  우선순위 분류 (보안 > 기능 > 성능)               |            |
|  +--------------------------------------------------+            |
|      |                                                            |
|      v                                                            |
|  출력:                                                            |
|  +--------------------------------------------------+            |
|  | CCTV Gap Report                                   |            |
|  |  - IP별 누락 항목 목록                            |            |
|  |  - 테스트 실행 명령어                             |            |
|  |  - V-Plan 추가 항목                               |            |
|  |  - 우선순위별 정렬                                |            |
|  +--------------------------------------------------+            |
+------------------------------------------------------------------+
```

### Gap Report 예시

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

---

## 성과 — 정량적 데이터

### DVCon 2025 결과

| 지표 | Project A (대규모) | Project B (소규모) |
|------|-------------------|-------------------|
| SoC 내 IP 수 | ~200 | ~50 |
| 발견 Gap 수 | **293** | **216** |
| Gap Rate | **2.75%** | **4.99%** |
| Human Oversight 비율 | - | **96.30%** |
| New IP/Feature 누락 감소 | **~40%** | - |

### 인사이트

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

## 면접 종합 Q&A

**Q: TB Top 환경을 어떻게 설계했고, 어떤 가치가 있었나?**
> "프로젝트 공통 프레임워크로 설계했다. IP 목록, 메모리 맵, 인터럽트 맵을 Config(JSON)으로 정의하면 TB Top Generator가 자동으로 환경을 구성한다. Common Task Checker Layer를 내장하여 Connectivity, Memory Map, Interrupt, Power 검증을 자동 수행한다. 이 환경을 여러 SoC 프로젝트에 배포하여 프로젝트마다 TB를 처음부터 만드는 비용을 제거했다."

**Q: DVCon 논문의 CCTV 방법론을 설명하라.**
> "SoC 내 모든 IP에 공통적으로 필요한 검증 항목(sysMMU, Security, DVFS 등)이 빠짐없이 수행되었는지 자동 추적하는 방법론이다. IP-XACT(구조) + IP Spec(시맨틱)의 Hybrid Extraction으로 IP별 필요 Common Task를 판단하고, 기존 V-Plan과 비교하여 Gap을 자동 발견한다. LLM이 테스트 명령어까지 생성한다. Project A에서 293개(2.75%), Project B에서 216개(4.99%)의 Gap을 발견했고, Human Oversight가 96.30%임을 정량적으로 증명했다."

**Q: 소규모 프로젝트의 Gap Rate가 더 높은 이유는?**
> "엔지니어 수가 적어 교차 검증이 부족하기 때문이다. 대규모에서는 IP별 전담 인력이 있어 상호 검토가 자연스럽지만, 소규모에서는 한 사람이 여러 IP를 담당하여 누락 가능성이 높아진다. 이것이 '자동화가 소규모에서 오히려 더 필요하다'는 논문의 핵심 인사이트이다."

---

## 코드 예시: 구체적 JSON Config

### SoC Top Config (프로젝트별 교체되는 유일한 파일)

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

→ **프로젝트 A → Config_A.json, 프로젝트 B → Config_B.json만 교체하면 동일 TB 프레임워크 재사용**

---

## 코드 예시: Config 기반 UVM Env 자동 구성

### Config 파싱 및 동적 Checker 생성

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

---

## AI 파이프라인 상세: 실무 구현

### Phase 1: IP 프로파일 Embedding

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

### Phase 2: FAISS 기반 유사 IP 검색

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

### Phase 3: LLM 기반 Gap Detection 프롬프트

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

---

## Gap Report → V-Plan 반영 실무 워크플로우

```
Step 1: CCTV Gap Report 생성 (AI 파이프라인)
  ┌─────────────────────────────────────────┐
  │ Gap Report                              │
  │ DMA × sysMMU_bypass_enable = NOT_TESTED │
  │ GPU × Security_TZPC = NOT_TESTED        │
  │ USB × DVFS_transition = NOT_TESTED      │
  │ Total: 12 gaps                          │
  └─────────────────────────────────────────┘
          │
Step 2: 우선순위 분류 (자동)
  ┌─────────────────────────────────────────┐
  │ HIGH (보안/안정성):                     │
  │   GPU × Security_TZPC                   │
  │   DMA × sysMMU_bypass_enable            │
  │                                         │
  │ MEDIUM (기능):                          │
  │   USB × DVFS_transition                 │
  │   ...                                   │
  │                                         │
  │ LOW (성능):                             │
  │   ...                                   │
  └─────────────────────────────────────────┘
          │
Step 3: V-Plan bin 자동 생성
  ┌─────────────────────────────────────────┐
  │ vplan_additions.json:                   │
  │ [                                       │
  │   {                                     │
  │     "feature": "DMA.common_task.sysMMU",│
  │     "bin": "bypass_enable_transition",  │
  │     "test": "dma_sysmmu_bypass_test",   │
  │     "priority": "HIGH"                  │
  │   }, ...                                │
  │ ]                                       │
  └─────────────────────────────────────────┘
          │
Step 4: 테스트 명령어 자동 생성
  mrun test --test_name dma_sysmmu_bypass_test --sys_name soc_top
  mrun test --test_name gpu_security_tzpc_test --sys_name soc_top
          │
Step 5: IP 담당 엔지니어에게 배포
  담당자별 Gap 목록 + 테스트 명령어 + 우선순위
          │
Step 6: 실행 후 CCTV 매트릭스 갱신
  cctv_cov.record_result(IP_DMA, TASK_SYSMMU, RESULT_PASS);
  → Coverage 재집계 → Gap 감소 확인
```

---

## TB Top Release 프로세스 상세

### Phase별 체크리스트

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

---

## 연습 문제

### 문제 1: Config에서 CCTV ignore_bins 자동 도출

**문제**: 아래 JSON Config의 IP 3개에 대해 CCTV 매트릭스를 그리고, ignore_bins가 되어야 할 셀을 표시하라.

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
1. 각 IP의 common_tasks 목록 확인:
   GPU: 7개 모두 해당
   I2C: SECURITY, CLK_GATE, RESET, IRQ (4개)
   Temp_Sensor: RESET만 (1개)

2. 매트릭스 그리기 (✅ = 검증 필요, ⬜ = ignore_bins):

              | SYSMMU | SECURITY | DVFS | CLK_GATE | POWER | RESET | IRQ |
   GPU        |   ✅   |    ✅    |  ✅  |    ✅    |  ✅   |  ✅   | ✅  |
   I2C        |   ⬜   |    ✅    |  ⬜  |    ✅    |  ⬜   |  ✅   | ✅  |
   Temp_Sensor|   ⬜   |    ⬜    |  ⬜  |    ⬜    |  ⬜   |  ✅   | ⬜  |

3. ignore_bins 수:
   GPU: 0개
   I2C: 3개 (SYSMMU, DVFS, POWER)
   Temp_Sensor: 6개 (SYSMMU, SECURITY, DVFS, CLK_GATE, POWER, IRQ)
   총 ignore_bins = 9개

4. 유효 조합 수:
   전체 조합: 3 IP × 7 Tasks = 21
   ignore_bins: 9
   유효 조합: 12 → 이 12개가 모두 PASS여야 CCTV Closure

5. 코드 변환:
   ignore_bins i2c_no_mmu = binsof(cp_ip) intersect {IP_I2C}
                           && binsof(cp_task) intersect {TASK_SYSMMU};
   ignore_bins i2c_no_dvfs = binsof(cp_ip) intersect {IP_I2C}
                            && binsof(cp_task) intersect {TASK_DVFS};
   // ... (총 9개)

→ Config의 common_tasks 필드에서 자동으로 도출 가능
→ 새 프로젝트에서 Config만 교체하면 ignore_bins도 자동 갱신
```

### 문제 2: AI Gap Detection 정확도 분석

**문제**: AI 파이프라인이 다음 결과를 냈다. False Positive와 True Positive를 분류하고, 정밀도(Precision)를 계산하라.

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
1. 분류:
   True Positive (TP): #1, #2, #4, #7, #8, #10 = 6개
   False Positive (FP): #3, #5, #6, #9 = 4개

2. Precision = TP / (TP + FP) = 6 / 10 = 60%

3. False Positive 원인 분석:
   #3 (UART × sysMMU): IP-XACT에서 UART의 "DMA 없음"을 파악 못함
     → IP-XACT 파싱 개선 필요 (bus_if 필드 확인)
   #5 (I2C × Power): Power Domain 정보가 IP-XACT에 없음
     → Config의 power_domains 정보 활용 필요
   #6 (Crypto × sysMMU): 내부 메모리 사용 = Spec의 시맨틱
     → IP Spec에서 "internal memory only" 키워드 추출 필요
   #9 (SPI × DVFS): 고정 클럭 정보가 Spec에만 있음
     → 시맨틱 추출 정밀도 개선 필요

4. 개선 방향:
   - IP-XACT 파싱 정밀도 향상 (DMA 유무, 버스 타입)
   - Spec 키워드 확장 ("fixed clock", "internal memory", "always-on")
   - FAISS 유사 IP 검색으로 Cross-validation

5. 실무 관점:
   Precision 60%는 낮아 보이지만, 10개 Gap 중 6개가 실제 Critical Gap
   → 자동화 없이는 이 6개를 모두 놓칠 수 있었음
   → False Positive는 엔지니어가 리뷰에서 빠르게 걸러낼 수 있음
   → Recall(실제 Gap 중 발견 비율)이 더 중요한 지표
```

### 문제 3: TB Top Release 시 Config 변경 영향 분석

**문제**: 이전 프로젝트에서 새 프로젝트로 Config를 갱신할 때, 다음 변경사항이 TB Top에 미치는 영향을 분석하라.

```
변경사항:
  1. 새 IP 추가: NPU (Neural Processing Unit), AXI, DMA 지원
  2. 기존 IP 제거: I2C_1 (사용하지 않음)
  3. UFS Base Address 변경: 0x1200_0000 → 0x1400_0000
  4. Interrupt 변경: DMA SPI 52 → SPI 55
```

**사고과정**:
```
1. 새 IP 추가 (NPU):
   영향 범위:
   - Agent: AXI agent 새로 인스턴스화 필요
   - Memory Map Checker: NPU base addr 추가
   - Interrupt Monitor: NPU SPI 번호 등록
   - Connectivity Checker: NPU 포트 연결 property 추가
   - CCTV: NPU에 대한 Common Task 행 추가
     (DMA 지원 → sysMMU, Security, DVFS, ClkGate, Power, Reset, IRQ)
   - FAISS: 유사 IP(GPU) 검색 → GPU의 검증 이력 참조하여 NPU Gap 예측

   자동 처리: Config에 NPU 추가 → TB Top Generator가 위 항목 자동 생성
   수동 처리: NPU 전용 시나리오 (AI 추론 정확도 등) 추가 필요

2. 기존 IP 제거 (I2C_1):
   영향 범위:
   - Agent: I2C_1 agent 제거 (인스턴스화 skip)
   - Memory Map Checker: I2C_1 주소 영역 제거
     → 해당 주소 접근 시 DECERR 반환으로 변경
   - CCTV: I2C_1 행 제거

   자동 처리: Config에서 삭제 → 자동 제거
   주의: I2C_1 주소에 새 IP가 배치되었는지 확인 필요

3. UFS Base Address 변경:
   영향 범위:
   - Memory Map Checker: 주소 갱신
   - 기존 테스트에서 하드코딩된 0x1200_0000 → 실패
   - Config 기반이면: 자동 갱신 → 테스트 수정 불필요

   교훈: 이것이 Config 기반 TB의 가치 — 주소가 변해도 Config만 갱신

4. DMA Interrupt 변경:
   영향 범위:
   - Interrupt Monitor: SPI 52 → 55 갱신
   - Connectivity SVA: DMA IRQ → GIC SPI[55]로 변경
   - 기존 테스트에서 SPI[52] 확인 → 실패

   자동 처리: interrupt_map 갱신 → Monitor/SVA 자동 재생성
   리스크: 테스트에 SPI 번호가 하드코딩되어 있으면 수동 수정 필요

총 영향:
  Config 기반: JSON 갱신 → TB Top Generator 재실행 → 대부분 자동 처리
  수동 필요: NPU 전용 시나리오, 하드코딩된 주소/SPI 수정
  CCTV: NPU 행 추가 + I2C_1 행 제거 → Gap Report 재생성
```

---

## 퀴즈

**Q1**: TB Top을 "Config 기반"으로 설계하면, 새 프로젝트에 적용할 때 최소한 무엇을 교체해야 하는가?

<details>
<summary>정답</summary>

JSON Config 파일 1개만 교체하면 된다. Config에 IP 목록, Memory Map, Interrupt Map, Power Domain, Reset Sequence, Common Task 적용 목록이 모두 포함되어 있으므로, TB Top Generator가 이를 기반으로 Agent, Checker, Monitor, CCTV Coverage를 자동 재구성한다.
</details>

**Q2**: AI 파이프라인에서 IP-XACT만으로 판단할 수 없고 IP Spec이 필요한 Common Task 항목 2가지와 그 이유는?

<details>
<summary>정답</summary>

1. **Security**: IP-XACT에는 레지스터 맵만 있고, 어떤 레지스터가 Secure-only인지는 IP Spec에만 기술됨. "이 IP에 보안 접근 제어가 필요한가?"는 시맨틱 판단.
2. **DVFS**: IP-XACT에는 클럭 포트 정보만 있고, "이 IP가 동적 주파수 변경을 지원하는가?"는 IP Spec의 동작 모드 설명에서만 파악 가능.

공통 이유: IP-XACT는 구조(structure)만, Spec은 의미(semantics)를 담고 있음.
</details>

**Q3**: CCTV Gap Report를 받은 IP 담당 엔지니어가 수행하는 5단계 워크플로우를 순서대로 나열하라.

<details>
<summary>정답</summary>

1. Gap 목록 리뷰 → False Positive 걸러내기 (N/A 확인)
2. True Gap에 대한 테스트 시나리오 확인/보완
3. 제공된 mrun 명령어로 테스트 실행
4. PASS/FAIL 결과 확인 및 디버그
5. CCTV Coverage에 결과 기록 → 매트릭스 갱신

→ 1에서 걸러지지 않은 Gap = 실제 누락이므로 반드시 검증 수행
</details>

---
!!! warning "실무 주의점 — AI 생성 시퀀스의 Clock Domain 무시"
    **현상**: AI가 생성한 시퀀스가 단일 클럭 기준으로 작성되어, 멀티 클럭 도메인 TB에서 적용 시 서로 다른 도메인 에이전트에 동기화 없이 동시 구동되어 데이터 레이스가 발생한다.

    **원인**: LLM은 IP-XACT 구조 정보에서 clock domain 경계를 추론하지 못한다. AI가 생성한 시퀀스 초안은 단일 클럭 가정하에 fork/join 패턴을 사용하는 경우가 많아, 리뷰 없이 그대로 적용하면 CDC 무검증 상태가 된다.

    **점검 포인트**: AI 생성 시퀀스에서 각 에이전트 `start_item`/`finish_item` 앞에 해당 에이전트의 클럭 도메인을 명시했는지 확인. TB Top Config JSON의 `clock_domain` 필드가 에이전트 연결과 일치하는지 대조.

## 핵심 정리

- **TB Top 재사용성**: 프로젝트마다 IP 종류는 다르지만 통합 패턴은 비슷 → layered TB (Common 부분 + 프로젝트별 customization).
- **AI 자동화 활용 영역**: (1) coverage gap → targeted sequence 생성, (2) 디버그 시 log/wave 분석, (3) RAL 자동 생성, (4) spec → constraint 자동 변환.
- **AI 한계**: silent corruption, race condition, timing-sensitive bug는 human inspection 필수. AI는 hypothesis 제안, 검증은 사람.
- **RAL 통합**: 모든 IP의 register map을 단일 RAL block으로 통합 → CPU SW 모델과 동등한 access pattern.
- **Workflow**: spec change → AI가 sequence 초안 생성 → reviewer → 시뮬 → 회귀 자동화.

## 다음 단계

- 📝 [**Module 03 퀴즈**](quiz/03_tb_top_and_ai_quiz.md)
- ➡️ [**Module 04 — Quick Reference Card**](04_quick_reference_card.md)

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
