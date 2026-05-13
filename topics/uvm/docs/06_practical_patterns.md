# Module 06 — 실무 패턴 & 안티패턴

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="core">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🧪</span>
    <span class="chapter-back-text">UVM</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 06</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-처음엔-동작하지만-환경이-커지면-깨지는-패턴들">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-onboarding-매뉴얼-과-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-god-env-안티-패턴-을-agent-구조-로-리팩터링하는-한-사이클">3. 작은 예 — God Env 리팩터링 한 사이클</a>
  <a class="page-toc-link" href="#4-일반화-4-가지-주요-패턴-과-5-가지-안티패턴">4. 일반화 — 패턴/안티패턴 분류</a>
  <a class="page-toc-link" href="#5-디테일-각-패턴의-코드-와-from-scratch-체크리스트">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Recognize** 자주 쓰이는 UVM 설계 패턴 (Config Object, Sequencer Hierarchy, Layered Sequence) 을 구분할 수 있다.
    - **Identify** 흔한 안티패턴 (God Env, Monitor 가 sequence 시작, 하드코딩된 경로) 을 코드에서 찾아낼 수 있다.
    - **Plan** 새 검증 프로젝트의 from-scratch 환경 구축 체크리스트를 따라 디렉토리 / 파일 구조와 1주 차 작업을 계획할 수 있다.
    - **Critique** 동료의 UVM 코드 리뷰에서 근거를 들어 안티패턴을 지적하고 리팩터링을 제안할 수 있다.
    - **Apply** Base Test + Factory Override 패턴으로 같은 env 위에서 시나리오만 다른 N 개의 derived test 를 작성할 수 있다.

!!! info "사전 지식"
    - [Module 01-05](01_architecture_and_phase.md) 전체
    - 한 번 이상 from-scratch 환경 구축 경험이 있으면 본문이 더 와닿음

---

## 1. Why care? — 처음엔 동작하지만 환경이 커지면 깨지는 패턴들

### 1.1 시나리오 — _God Env_ 의 죽음

당신은 _작은_ TB 시작. `env` 안에 모든 component 직접 instantiate. 작동 OK.

6 개월 후:
- 새 protocol 추가 → env 에 component 더 추가.
- 새 sequence 추가 → env 가 sequencer ref 들고 시작.
- 새 scoreboard → env 가 직접 connect.

1 년 후: **env class 2000 줄**. 모든 component 의 _hidden coupling_:
- env 에서 a 변경하면 b 도 깨짐 (test 가 그것에 의존).
- 새 project 포팅 → env 통째로 _copy_ → 많은 변경 → 새 bug.

해법: **Agent 캡슐화**:
- env 는 _agent들의 컨테이너_ 만.
- 각 agent 가 _자기 component_ 관리.
- env 추가/변경이 _다른 agent 에 영향 없음_.

UVM 안티패턴은 **처음에는 작동하지만 환경이 커지면 cascading failure** 를 만듭니다. 6 년+ 경력자도 새 프로젝트에서 자주 반복하는 실수가 있고, 코드 리뷰에서 근거 없이 "이건 좀..." 같은 피드백은 무력합니다.

이 모듈은 **재현 가능한 좋은 설계 결정** 을 내리는 어휘를 제공합니다 — Config Object, Base Test 상속, Layered Sequence, Parameterized Agent 의 4 패턴과, God Env / Driver 안 DUT 로직 / Sequence 의 #delay / 다중 곳 Objection / 경로 하드코딩의 5 안티패턴. 이 어휘 위에서 코드 리뷰는 **"이 부분은 God Env 안티패턴 — Agent 로 캡슐화하자"** 처럼 _근거 있는_ 피드백이 됩니다.

---

## 2. Intuition — Onboarding 매뉴얼, 과 한 장 그림

!!! tip "💡 한 줄 비유"
    **Base Test ↔ Derived Test** ≈ **회사 표준 onboarding 절차 (base) ↔ 부서별 onboarding (derived)**.<br>
    `base_test` 가 env 만들고 config_db 채우는 것이 _회사 공통 절차_, `derived_test` 가 _부서 특화_. derived 가 `super.build_phase(phase)` 호출 안 하면 회사 표준이 적용 안 된 채 시작.

### 한 장 그림 — 좋은 환경 vs 나쁜 환경

```d2
direction: down

GOOD: "좋은 환경" {
  style.stroke: "#137333"
  style.stroke-width: 2

  GT: "Test\n(시나리오 선택만)"
  GE: Env
  GA: Agent_A
  GAD: Driver
  GAM: Monitor
  GAS: Sequencer
  GB: "Agent_B (Passive)"
  GBM: Monitor
  GSB: Scoreboard
  GCOV: Coverage

  GT -> GE
  GE -> GA
  GA -> GAD
  GA -> GAM
  GA -> GAS
  GE -> GB
  GB -> GBM
  GE -> GSB
  GE -> GCOV
}

BAD: "나쁜 환경 (God Env)" {
  style.stroke: "#c5221f"
  style.stroke-width: 2

  BT: Test
  BE: Env
  BD: "Driver (직접 보유)"
  BM: Monitor
  BD2: "Driver_B (다른 인터페이스도)"
  BM2: Monitor_B
  BSB: Scoreboard

  BT -> BE
  BE -> BD
  BE -> BM
  BE -> BD2
  BE -> BM2
  BE -> BSB
}
```

<div class="parallel-grid">
<div>

**좋은 환경 — 장점**

- Agent 단위로 재사용 (다른 프로젝트로)
- Active/Passive 모드 분기
- Config Object 1 개로 SoC 차이 흡수
</div>
<div>

**나쁜 환경 — 문제**

- Agent 단위 재사용 불가
- Active/Passive 분리 안 됨
- Driver/Monitor 책임 분산
- 한 신호 추가 = env 수정
</div>
</div>

### 왜 이 디자인인가 — Design rationale

좋은 환경의 모든 패턴은 **세 가지 _분리_** 로 환원됩니다.

1. **DUT 독립적 Agent** — 프로토콜만 구현, DUT 로직 배제. 그래서 Agent 1 개로 여러 DUT 검증.
2. **Config Object** — SoC 별 차이를 _설정 객체_ 로 흡수. Test 가 의미 (`secure_boot_en=1`) 로 설정, Agent 가 물리 주소로 변환.
3. **Base Test 상속** — 공통 환경 + 시나리오별 차이만. derived test 는 `set_type_override` 한 줄로 동작 변형.

이 세 분리가 곧 **포팅 비용을 _수 주 → 3-5 일_** 로 줄이는 비결.

---

## 3. 작은 예 — God Env 안티 패턴 을 Agent 구조 로 리팩터링하는 한 사이클

가장 흔한 실수 시나리오. Junior 엔지니어가 첫 환경을 빠르게 만들기 위해 Env 가 driver 를 _직접 보유_ 한 코드를 가져왔습니다. 한 사이클의 리팩터링.

### 단계별 다이어그램

```
   Step 1 — 안티패턴 코드를 발견
   ┌──────────────────────────────────────────┐
   │ class my_env extends uvm_env;             │
   │   apb_driver  drv;     // ◀ Agent 없이    │
   │   virtual apb_if vif;                      │
   │   function void connect_phase(...);       │
   │     drv.vif = vif;     // ◀ config_db 우회 │
   │   endfunction                              │
   │   task run_phase(...);                    │
   │     my_seq seq = new();                    │
   │     seq.start(drv);   // ◀ sequencer 없이  │
   │   endtask                                  │
   │ endclass                                   │
   └──────────────────────────────────────────┘
                       │
                       │  ① 안티패턴 3 개 식별
                       ▼
   Step 2 — Agent 추출
   ┌──────────────────────────────────────────┐
   │ class apb_agent extends uvm_agent;        │
   │   apb_driver    drv;                       │
   │   apb_monitor   mon;                       │
   │   apb_sequencer sqr;                       │
   │   function void build_phase(...);          │
   │     mon = apb_monitor::type_id::create(... │
   │     if (get_is_active() == UVM_ACTIVE)    │
   │       drv = apb_driver::type_id::create(. │
   │       sqr = apb_sequencer::type_id::create│
   │   endfunction                              │
   │   function void connect_phase(...);       │
   │     drv.seq_item_port.connect(             │
   │           sqr.seq_item_export);            │
   │   endfunction                              │
   │ endclass                                   │
   └──────────────────────────────────────────┘
                       │
                       │  ② vif 전달 → config_db 경로
                       ▼
   Step 3 — top.set 수정
   ┌──────────────────────────────────────────┐
   │ initial begin                             │
   │   uvm_config_db#(virtual apb_if)::set(    │
   │     null, "uvm_test_top.env.agent.*",     │
   │     "vif", intf);                          │
   │   run_test();                              │
   │ end                                        │
   └──────────────────────────────────────────┘
                       │
                       │  ③ Test → sequencer 로 start
                       ▼
   Step 4 — Test 시나리오 정정
   ┌──────────────────────────────────────────┐
   │ class my_test extends uvm_test;           │
   │   ...                                      │
   │   task run_phase(uvm_phase phase);        │
   │     phase.raise_objection(this);          │
   │     my_seq seq = my_seq::type_id::create( │
   │                    "seq");                 │
   │     seq.start(env.agent.sqr);  // sqr      │
   │     phase.drop_objection(this);           │
   │   endtask                                  │
   │ endclass                                   │
   └──────────────────────────────────────────┘
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | reviewer | 안티패턴 식별 — (a) Agent 없이 driver 직접, (b) connect_phase 에서 vif 직접 대입, (c) sequencer 없이 driver 에 start | 셋 다 _재사용성_ 을 깨는 패턴 |
| ② | refactor | Agent 클래스 신설 — driver/monitor/sequencer 캡슐화 | Active/Passive 분기 가능, 다른 프로젝트로 Agent 째 이전 |
| ③ | refactor | top.set 의 inst 경로를 `uvm_test_top.env.agent.*` 로 | config_db 표준 경로 — 하드코딩 제거 |
| ④ | refactor | Test 의 `seq.start` 인자를 `env.agent.sqr` 로 | sequencer 가 driver 와 sequence 의 표준 중개 |

### 비교 표 — Before vs After

| 측면 | Before (God Env) | After (Agent 구조) |
|---|---|---|
| 재사용성 | env 째 가져가야 함 | apb_agent 만 가져가도 됨 |
| Active / Passive | 분리 불가 (driver 항상 존재) | `get_is_active()` 분기로 자동 |
| vif 전달 | 직접 대입 (하드코딩) | config_db (경로 일치만) |
| 시나리오 시작 | `seq.start(drv)` (잘못) | `seq.start(env.agent.sqr)` (표준) |
| Factory override | 적용 어려움 (new 직접) | type_id::create 로 자동 적용 |

!!! note "여기서 잡아야 할 두 가지"
    **(1) "동작하면 OK" 가 아니다.** God Env 도 시뮬은 PASS 가능. 그러나 _재사용성_ 이 깨져 있어서 다음 프로젝트에서 비용이 폭발. 안티패턴은 _스케일에서 깨진다_.<br>
    **(2) 리팩터링은 _분리_ 가 핵심.** Agent 추출 → 책임 분리, config_db 경로 → vif 전달 분리, sequencer → sequence/driver 분리. 셋이 한 묶음의 결정.

---

## 4. 일반화 — 4 가지 주요 패턴 과 5 가지 안티패턴

### 4.1 4 가지 주요 패턴

| 패턴 | 핵심 아이디어 | 어디에 쓰나 |
|---|---|---|
| **Config Object** | 관련 설정을 1 개 object 로 묶어 set/get 1 회 | SoC 별 차이 흡수 |
| **Base Test + 상속** | 공통 환경은 base, 시나리오별 차이만 derived | 새 시나리오 추가 시 short class |
| **Layered Sequence** | 추상 레벨 별 sequence (system → protocol → transport) | UFS / SCSI 같은 다층 프로토콜 |
| **Parameterized Agent** | data/addr 폭만 다른 인터페이스에 같은 Agent 재사용 | DCMAC 512-bit, register 32-bit |

### 4.2 5 가지 안티패턴

| 안티패턴 | 무엇이 잘못 | 결과 |
|---|---|---|
| **God Env** | env 가 driver/monitor 직접 보유 (Agent 없이) | 재사용 불가, Active/Passive 분리 안 됨 |
| **Driver 안 DUT 로직** | Driver 가 기대값 계산 / 비교 | 같은 버그를 양쪽에 구현해 검출 불가 |
| **Sequence 의 #delay** | `body()` 안에서 `#100ns` 같은 하드코딩 지연 | DUT 타이밍 변경 시 일제히 깨짐 |
| **다중 곳 Objection** | Driver / Monitor / SB 모두 raise/drop | 종료 시점 분산 → 디버그 어려움 |
| **config_db 경로 하드코딩** | `"env.axi_agent.driver"` 를 코드 전체에 흩어 set/get | 컴포넌트 이름 변경 시 silent miss |

---

## 5. 디테일 — 각 패턴의 코드 와 From-Scratch 체크리스트

### 5.1 패턴 1: Config Object 패턴

```
문제: config_db set/get 가 수십 개 → 관리 불가, 오타 위험

해결: 관련 설정을 Config Object 로 묶기

  class agent_config extends uvm_object;
    virtual my_if vif;
    bit is_active = 1;
    int timeout = 1000;
    bit enable_coverage = 1;
  endclass

→ set/get 1 회로 모든 설정 전달
→ 새 설정 추가 시 Config Object 에만 필드 추가
→ 포팅 시 Config Object 만 교체 (Apple/Meta 사례)
```

### 5.2 패턴 2: Base Test + 상속 패턴

```systemverilog
class base_test extends uvm_test;
  my_env env;

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = my_env::type_id::create("env", this);
    // 공통 설정
  endfunction

  // 공통 헬퍼 메서드
  task wait_for_reset();
    @(posedge vif.rst_n);
  endtask
endclass

class smoke_test extends base_test;
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    wait_for_reset();
    // smoke 시나리오
    phase.drop_objection(this);
  endtask
endclass

class stress_test extends base_test;
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);   // ★ 누락 시 base 의 env 가 사라짐
    // Factory Override 로 Stress 용 Sequence 교체
    set_type_override_by_type(
      normal_seq::get_type(), stress_seq::get_type());
  endfunction
endclass

→ 공통 환경은 base_test 에, 시나리오별 차이만 하위 Test 에
→ 새 테스트 추가 시 base_test 상속 + 시나리오만 작성
```

### 5.3 패턴 3: Layered Sequence 패턴

```
높은 추상 레벨 → 낮은 추상 레벨로 변환:

  System Sequence: "파일 읽기" (Application 레벨)
       ↓
  Protocol Sequence: "READ(LBA=0x100, len=8)" (SCSI 레벨)
       ↓
  Transport Sequence: "Command UPIU + Data-In UPIU" (UFS 레벨)
       ↓
  Pin-level: Driver 가 신호 구동

각 레벨의 Sequence 가 독립적으로 재사용 가능
→ UFS HCI 검증에서 이 계층 활용
```

### 5.4 패턴 4: Parameterized Agent

```systemverilog
class generic_axi_agent #(int DATA_W = 32, int ADDR_W = 32)
  extends uvm_agent;

  typedef generic_axi_item   #(DATA_W, ADDR_W) item_t;
  typedef generic_axi_driver #(DATA_W, ADDR_W) driver_t;
  // ...
endclass

// 사용
generic_axi_agent #(512, 40) wide_agent;   // 512-bit 데이터
generic_axi_agent #(32, 32)  narrow_agent; // 32-bit 데이터

→ 데이터 / 주소 폭만 다른 인터페이스에 같은 Agent 재사용
→ DCMAC (512-bit), 레지스터 (32-bit) 모두 커버
```

### 5.5 안티패턴 1: config_db 경로 하드코딩

```systemverilog
// BAD: 경로 문자열이 코드 전체에 분산
uvm_config_db #(int)::set(this, "env.axi_agent.driver",  "timeout", 100);
uvm_config_db #(int)::set(this, "env.axi_agent.monitor", "timeout", 100);
// → 컴포넌트 이름 변경 시 모든 경로 수동 수정

// GOOD: Config Object + 와일드카드
uvm_config_db #(agent_cfg)::set(this, "env.axi_agent*", "cfg", cfg);
```

### 5.6 안티패턴 2: Driver 에 DUT 로직 삽입

```systemverilog
// BAD: Driver 가 기대값을 계산
task drive_and_check(my_item item);
  vif.data <= item.data;
  @(posedge vif.clk);
  if (vif.result != item.data * 2)  // ← DUT 로직!
    `uvm_error(...)
endtask

// GOOD: Driver 는 구동만, 비교는 Scoreboard
// Driver:     vif.data <= item.data;
// Scoreboard: ref_model.predict(item) vs monitor.actual
```

### 5.7 안티패턴 3: Sequence 에서 시간 대기

```systemverilog
// BAD: Sequence 가 DUT 타이밍에 의존
task body();
  start_item(item); finish_item(item);
  #100ns;  // ← 하드코딩 지연!
  start_item(next_item); finish_item(next_item);
endtask

// GOOD: 이벤트 / 핸드셰이크 기반
task body();
  start_item(item); finish_item(item);
  wait(env.monitor.transaction_complete);  // 이벤트 기반
  start_item(next_item); finish_item(next_item);
endtask
```

### 5.8 안티패턴 4: $display / $finish 사용

```systemverilog
// BAD: UVM 외부 출력
$display("Error: data mismatch");
$finish;

// GOOD: UVM 리포팅 사용
`uvm_error("SB", "Data mismatch")
`uvm_fatal("DRV", "Critical failure — cannot continue")

// 이유: UVM 리포팅은 컴포넌트 경로, 시간, 심각도를 자동 포함
//       필터링 / 카운팅 / 파일 출력 등 제어 가능
```

### 5.9 안티패턴 5: 모든 곳에서 Objection

```systemverilog
// BAD: 여러 컴포넌트에서 raise/drop → 종료 시점 예측 불가
// Driver: phase.raise_objection(this);
// Monitor: phase.raise_objection(this);
// Scoreboard: phase.raise_objection(this);

// GOOD: Test 에서만 raise/drop
class my_test extends uvm_test;
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    vseq.start(null);
    // drain time
    #1000ns;
    phase.drop_objection(this);
  endtask
endclass
```

### 5.10 From Scratch 환경 구축 체크리스트

```
사내 / 사외 프로젝트에서 반복한 환경 구축 순서:

1. [ ] Interface 정의 (.sv)
2. [ ] Sequence Item 정의 (필드 + Constraint)
3. [ ] Driver 구현 (Pin-level 구동)
4. [ ] Monitor 구현 (Pin-level → Transaction)
5. [ ] Sequencer (보통 기본 uvm_sequencer 사용)
6. [ ] Agent (Active/Passive, Config Object)
7. [ ] Scoreboard (Reference Model + 비교)
8. [ ] Coverage (Covergroup + Coverpoint + Cross)
9. [ ] Env (Agent + Scoreboard + Coverage 연결)
10. [ ] Base Test + Config 설정
11. [ ] 기본 Sequence (smoke, directed)
12. [ ] Virtual Sequence (시스템 레벨)
13. [ ] Package 파일 (.sv, .f)
14. [ ] Sanity 실행 + 디버그
15. [ ] Coverage 분석 + 추가 시나리오
```

### 5.11 Legacy → UVM 전환 4 단계

| Step | 작업 | 검증 포인트 |
|---|---|---|
| 1 | Wrapper UVM env (기존 task 자극은 그대로, 위에 빈 env) | 기존 시뮬 결과와 동일 sanity |
| 2 | Monitor 만 UVM 화 (자극은 여전히 legacy) | Scoreboard 에 actual 도달 + legacy 결과 일치 |
| 3 | Driver 도입 (기존 task 자극을 Sequence + Driver 로) | 같은 시드에서 같은 자극 인가 (signal-level diff) |
| 4 | Sequence Library 정비 + Virtual Sequence | 기존 테스트 리스트와 1:1 매핑 + coverage 유지 |

핵심: 한 번에 다 갈아엎지 않기. 각 단계에서 _기능 동등성_ 을 sanity 로 확인.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Sequence library 를 한 폴더에 모아 두기만 하면 재사용 가능하다'"
    **실제**: Sequence 재사용 = **같은 sequencer / agent 인터페이스를 가정함**. 다른 프로젝트에서 재사용하려면 sequencer type, item type 이 호환되어야 합니다. 폴더 분리만 하고 sequencer/item 이 프로젝트마다 다르면 그대로 재사용 못 함.<br>
    **왜 헷갈리는가**: "코드를 분리해 둠 = 재사용 가능" 이라는 단순 가정 — 실제 재사용성은 _type 호환과 config object 의존성_ 에 달려 있음.

!!! danger "❓ 오해 2 — '`super.build_phase(phase)` 는 의례적인 첫 줄'"
    **실제**: derived test 의 build_phase 첫 줄에 `super.build_phase(phase)` 가 빠지면 base 가 만든 _env / config_db / factory override 가 모두 사라집니다_. UVM_FATAL 도 안 뜨고 시뮬은 통과하는데 _결과가 이상한_ silent 버그. 모든 `*_phase` 함수의 첫 줄에 super 호출은 _의무_.<br>
    **왜 헷갈리는가**: 일반 OOP 에서 super 호출이 선택적인 경우가 많아서 — UVM 은 phase chain 을 자동 안 해 줌.

!!! danger "❓ 오해 3 — 'Pattern 을 다 외우면 좋은 환경을 짤 수 있다'"
    **실제**: 패턴은 _도구 인덱스_ 일 뿐. _언제 어느 패턴을 꺼낼지_ 의 직관이 중요. 예를 들어 "SoC 별 차이가 작다" 면 Config Object 가 과도할 수 있고, "다중 agent 동기화 없음" 이면 Virtual Sequence 도 과도. **컨텍스트 → 패턴 매핑** 이 마스터의 핵심.<br>
    **왜 헷갈리는가**: 학습 단계에서는 _카탈로그식_ 학습이 주가 되어서.

!!! danger "❓ 오해 4 — '안티패턴은 절대 쓰면 안 된다'"
    **실제**: 안티패턴이라도 _작은 prototype_ 또는 _illustration code_ 에서는 적절할 수 있습니다 (예: `$display` 가 매우 빠른 디버그용). 안티패턴의 본질은 _scale 에서 깨진다_ 는 점 — 일회용 코드에서는 cost 가 안 드러남. 다만 _실제 환경 코드_ 에 들어가는 순간 cascading.<br>
    **왜 헷갈리는가**: "BAD" 라는 단순 라벨 때문에.

!!! danger "❓ 오해 5 — 'Driver 가 vif 응답을 _보고_ 만 있는데 왜 검증하면 안 되나'"
    **실제**: Driver 가 vif 를 통해 DUT 응답을 _볼 수 있는 것_ 과 _검증해도 되는 것_ 은 다릅니다. Driver 는 transaction → pin 변환만 — 검증은 _scoreboard 와 reference model_ 의 책임. 분리가 깨지면 (1) 같은 버그를 양쪽에 구현, (2) DUT 변경 시 Driver 도 수정, (3) 다른 DUT 에 재사용 불가. _기술적으로_ 가능해도 _구조적으로_ 금지.<br>
    **왜 헷갈리는가**: vif 핸들이 양방향 정보 (driving + sampling) 를 가져서.

### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Derived test 가 시작은 되는데 env 인스턴스가 안 만들어짐 | `super.build_phase(phase)` 누락 | derived test 의 build_phase 첫 줄 |
| `set_type_override` 가 안 먹힘 | 컴포넌트가 `new()` 로 직접 생성 | `grep "= new(" *_pkg.sv` |
| Sequence 가 다른 시드에서 재현 안 됨 | sequence body 에 `#100ns` 같은 하드코딩 지연 | sequence body 내 `#`/`@` |
| Test 에서 `seq.start(drv)` 호출 컴파일 에러 / 동작 안 함 | sequencer 없이 driver 에 start | sequencer 만들고 `seq.start(env.agent.sqr)` |
| 한 vif 변경했는데 여러 곳 수정 필요 | config_db 경로 하드코딩 분산 | config_db set/get 의 inst 경로 grep |
| `$display` 출력이 실제 레퍼런스와 안 맞음 | UVM reporting 과 다른 채널 — 동기화 안 됨 | `$display` → `uvm_info`/`uvm_error` 변환 |
| Multiple component raise/drop → 종료 시점 예측 불가 | objection 분산 | grep `raise_objection` — Test 외에 있는지 |
| Layered sequence 에서 lower seq 의 sequencer 못 찾음 | `start(sequencer)` 의 인자 누락 / 잘못된 sub_sqr 핸들 | virtual sequence 의 sub_sqr 대입 줄 |

---

## 7. 핵심 정리 (Key Takeaways)

- **4 패턴**: Config Object (설정 묶음) / Base Test 상속 (시나리오 차이만) / Layered Sequence (추상 레벨 분리) / Parameterized Agent (폭만 다른 인터페이스 재사용).
- **5 안티패턴**: God Env / Driver 안 DUT 로직 / Sequence 의 #delay / 다중 곳 Objection / config_db 경로 하드코딩.
- **From-scratch 15 단계 체크리스트**: Interface → Item → Driver → Monitor → Sequencer → Agent → Scoreboard → Coverage → Env → Test → Sequence → VSeq → Package → Sanity → Coverage 분석.
- **Legacy → UVM 4 단계**: Wrapper env → Monitor 만 UVM 화 → Driver 도입 → Sequence library 정비. 한 번에 다 갈아엎지 않고 각 단계 _기능 동등성_ sanity.
- **포팅 비결의 3 분리**: DUT 독립적 Agent + Config Object + OTP/메모리 맵 추상화 → 수 주 → 3-5 일.

!!! warning "실무 주의점"
    - **모든 `*_phase` 함수의 첫 줄에 `super.<phase>(phase)`** — 빠지면 base 의 모든 작업 무효.
    - **`new()` 직접 호출 금지** — type_id::create 만 사용해야 factory override 가 적용.
    - **Sequence 의 `#delay` 는 코드 리뷰의 1 차 reject 사유** — 이벤트 / 핸드셰이크로 대체.
    - **Test 외에서 raise/drop 하지 말 것** — 종료 시점이 _분산_ 되면 디버그 어려움.

### 7.1 자가 점검

!!! question "🤔 Q1 — Sequence `#delay` 금지 (Bloom: Analyze)"
    `#10ns` 를 sequence 에 쓰면 안 되는 _구조적_ 이유?
    ??? success "정답"
        Sequence 는 _시나리오_ 층, 시간 단위 의존은 다른 계층의 책임:
        - **재사용성**: protocol 의 cycle time 이 바뀌면 (10ns clock → 5ns) sequence 전부 수정 필요. 이벤트 기반이면 무관.
        - **테스트 환경 변경**: emulator vs sim 의 timing 이 다름 → hard-coded delay 가 _flaky_ 의 주범.
        - **handshake 인 경우 잘못된 추상화**: driver 가 `ready/valid` 로 자연 동기화하므로 `#10` 은 race 또는 무의미.
        - **대안**: `wait(event)`, `@posedge vif.clk iff (vif.ready)`, 또는 별도 sync_seq.

!!! question "🤔 Q2 — Objection raise/drop 위치 (Bloom: Evaluate)"
    Test 의 `run_phase` 만 raise/drop 하라는 규칙. 만약 sequence 안에서 raise 하면?
    ??? success "정답"
        분산 종료 = 디버그 지옥:
        - **증상**: test 가 _이상한 시점_ 에 종료. 어떤 sequence/agent 가 마지막으로 drop 했는지 추적해야 함.
        - **race**: 여러 sequence 가 동시에 raise/drop 시 ordering 에 따라 매번 다른 종료 시점.
        - **모범**: test 의 run_phase 에서 raise → fork-join 으로 모든 seq.start → drop. 시작/끝 1 지점.
        - 예외: long-running monitor 가 끝나야 의미 있는 검사라면 monitor 의 raise 가 정당화될 수 있음 — 단, 문서화 필수.

### 7.2 출처

**Internal (Confluence)**
- `UVM Code Review Checklist` — 안티패턴 매트릭스
- `Objection Management` — raise/drop 위치 규칙

**External**
- *UVM 1.2 User's Guide* §10 (End of Test) — Accellera
- *UVM Cookbook* (Mentor) — Common Pitfalls

---

## 다음 모듈

→ [Module 07 — Quick Reference Card](07_quick_reference_card.md): 인터뷰 / 코드 리뷰 / 디버그 중에 빠르게 펴보는 _치트시트_. 정독은 Module 01-06 으로 끝내고, 마지막에 한 장으로 정리.

[퀴즈 풀어보기 →](quiz/06_practical_patterns_quiz.md)


--8<-- "abbreviations.md"
