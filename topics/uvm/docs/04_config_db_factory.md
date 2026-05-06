# Module 04 — config_db & Factory

<div class="learning-meta">
  <span class="meta-badge meta-time">⏱ 17분</span>
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Apply** `config_db::set` / `get`을 사용해 virtual interface, configuration object를 계층으로 전달할 수 있다.
    - **Use** Factory의 `type_id::create`와 type/instance override로 테스트별 동작 변형을 구현할 수 있다.
    - **Debug** `uvm_config_db::dump`와 `factory.print()`로 경로 불일치 / 누락 override를 분석할 수 있다.
    - **Decide** type override vs instance override 중 적절한 범위(scope)를 선택할 수 있다.

!!! info "사전 지식"
    - [Module 01](01_architecture_and_phase.md), [Module 02](02_agent_driver_monitor.md), [Module 03](03_sequence_and_item.md)
    - hierarchical naming(`uvm_test_top.env.agent.*`) 이해

## 왜 이 모듈이 중요한가

UVM 환경의 **유연성과 재사용성은 모두 config_db + Factory에서 나옵니다**. 동시에 두 메커니즘은 가장 silent한 실패 원천: 경로 한 글자 차이로 set한 값이 get에 안 잡혀도 시뮬은 그냥 default로 동작합니다. **silent failure → cascading bug**의 전형적 패턴입니다.

## 핵심 개념
**config_db = 계층 구조를 통해 설정을 전달하는 글로벌 데이터베이스. Factory = 클래스 이름(타입)으로 객체를 생성하되, 런타임에 다른 타입으로 대체 가능한 메커니즘. 이 둘이 UVM 환경의 유연성과 재사용성의 핵심.**

---

## config_db — 설정 전달

### 기본 사용법

```systemverilog
// Set: 값 저장 (보통 test 또는 env에서)
uvm_config_db #(virtual my_if)::set(this, "env.agent.*", "vif", my_vif);
uvm_config_db #(int)::set(this, "env.agent", "num_transactions", 100);
uvm_config_db #(bit)::set(this, "env.agent", "is_active", UVM_ACTIVE);

// Get: 값 읽기 (보통 driver, monitor에서)
if (!uvm_config_db #(virtual my_if)::get(this, "", "vif", vif))
  `uvm_fatal("NOVIF", "Virtual interface not found in config_db")
```

### set/get 파라미터

```
set(context, inst_name, field_name, value)
get(context, inst_name, field_name, variable)

  context:    this (현재 컴포넌트) 또는 null (글로벌)
  inst_name:  대상 계층 경로 ("env.agent.*" = 와일드카드)
  field_name: 필드 이름 (문자열)
  value:      전달할 값

경로 매칭 규칙:
  "env.agent.driver"  → 정확히 일치
  "env.agent.*"       → agent 하위 모든 컴포넌트
  "*"                 → 모든 컴포넌트
  ""                  → get에서: 자기 자신의 경로
```

### config_db 설계 패턴 — Config Object

```systemverilog
// 여러 설정을 하나의 객체로 묶기
class my_agent_config extends uvm_object;
  `uvm_object_utils(my_agent_config)

  virtual my_if       vif;
  uvm_active_passive_e is_active = UVM_ACTIVE;
  int                  num_transactions = 100;
  bit                  enable_coverage = 1;
  bit                  enable_checker = 1;
endclass

// Test에서 한 번에 set
my_agent_config cfg = my_agent_config::type_id::create("cfg");
cfg.vif = my_vif;
cfg.num_transactions = 200;
uvm_config_db #(my_agent_config)::set(this, "env.agent", "cfg", cfg);

// Agent에서 한 번에 get
my_agent_config cfg;
uvm_config_db #(my_agent_config)::get(this, "", "cfg", cfg);
```

**장점**: set/get 호출 수 감소, 관련 설정을 논리적으로 그룹화, 타입 안전성.

---

## Factory — 객체 생성과 오버라이드

### Factory 생성

```systemverilog
// 일반 생성 (Factory 미사용) — 재사용 불가
my_driver drv = new("drv", this);

// Factory 생성 (권장) — 오버라이드 가능
my_driver drv = my_driver::type_id::create("drv", this);

// 차이: Factory는 "my_driver" 대신 다른 타입을 반환할 수 있음
```

### Factory Override

```systemverilog
// Type Override: 모든 my_driver를 enhanced_driver로 대체
set_type_override_by_type(my_driver::get_type(),
                          enhanced_driver::get_type());

// Instance Override: 특정 인스턴스만 대체
set_inst_override_by_type("env.agent.driver",
                          my_driver::get_type(),
                          enhanced_driver::get_type());

// Test에서 활용
class error_injection_test extends base_test;
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    // 정상 Driver를 에러 주입 Driver로 교체
    set_type_override_by_type(
      my_driver::get_type(),
      error_inject_driver::get_type()
    );
  endfunction
endclass
```

### Factory Override 활용 패턴

| 패턴 | 예시 | 효과 |
|------|------|------|
| **Driver 교체** | 정상 Driver → 에러 주입 Driver | 코드 수정 없이 Negative 테스트 |
| **Sequence Item 교체** | base_item → constrained_item | 다른 트래픽 패턴 |
| **Scoreboard 교체** | func_scoreboard → perf_scoreboard | 성능 검증 모드 전환 |
| **Env 교체** | base_env → extended_env | 환경 확장 |

---

## config_db 경로 디버그

```systemverilog
// 흔한 실수: 경로 불일치
// set: uvm_config_db #(int)::set(this, "env.agent", "count", 10);
// get: uvm_config_db #(int)::get(this, "", "cnt", val);  // "count" vs "cnt" 오타!

// 디버그 방법:
// 1. UVM_CONFIG_DB_TRACE
//    +UVM_CONFIG_DB_TRACE  (시뮬레이션 옵션)
//    → 모든 set/get 호출을 로그로 출력

// 2. get 실패 시 `uvm_fatal 사용
if (!uvm_config_db #(int)::get(this, "", "count", val))
  `uvm_fatal("CFG", $sformatf("config_db get failed for 'count' in %s",
                               get_full_name()))

// 3. 경로 확인
`uvm_info("CFG", $sformatf("My path: %s", get_full_name()), UVM_LOW)
```

---

## OTP Abstraction Layer와 config_db (이력서 연결)

```
BootROM 검증에서의 config_db 활용:

  Test:
    otp_config cfg = otp_config::type_id::create("cfg");
    cfg.secure_boot_en = 1;
    cfg.boot_device    = UFS;
    cfg.rotpk_hash     = 256'hDEAD...;
    uvm_config_db #(otp_config)::set(this, "env.otp_agent", "otp_cfg", cfg);

  OTP Agent:
    uvm_config_db #(otp_config)::get(this, "", "otp_cfg", cfg);
    → cfg 기반으로 OTP 값을 DUT에 force

  Config 객체가 OTP Abstraction Layer의 인터페이스:
    Test는 의미(secure_boot_en)로 설정
    Agent가 물리 주소로 변환
    → 물리 주소 은닉 = 재사용성의 핵심
```

---

## Q&A

**Q: config_db의 장점과 주의점은?**
> "장점: 계층 구조를 통해 설정을 전달하여 하드코딩을 제거하고 재사용성을 높인다. Test에서 설정을 변경하면 하위 컴포넌트가 자동으로 반영한다. 주의점: (1) 경로 문자열 오타 — 컴파일 타임에 검출 불가, 런타임에 get 실패. (2) 타입 불일치 — set과 get의 파라미터 타입이 다르면 무시됨. (3) 순서 — build_phase에서 set한 것을 같은 build_phase에서 get할 때 Phase 순서(Top→Down) 주의."

**Q: Factory Override가 왜 강력한가?**
> "코드 수정 없이 컴포넌트를 교체할 수 있다. 예를 들어 base_test에서 사용하는 정상 Driver를 error_injection_test에서 에러 주입 Driver로 교체하면, Agent/Env 코드는 일절 변경하지 않고도 Negative 테스트 환경이 된다. 이것이 UVM의 '코드를 바꾸지 않고 동작을 바꾸는' 핵심 메커니즘이다."

---

## 연습문제

!!! question "Exercise 1 (Apply, ★)"
    `my_test`에서 `apb_cfg`(파라미터화된 config object)를 `config_db::set`으로 등록하고, `apb_agent`의 `build_phase`에서 `get`으로 받아 사용하는 코드를 작성하세요.

    ??? answer "모범 답안"
        ```systemverilog
        // test
        function void build_phase(uvm_phase phase);
          super.build_phase(phase);
          apb_cfg cfg = new();
          cfg.timeout_ns = 1000;
          uvm_config_db#(apb_cfg)::set(this, "env.agent", "cfg", cfg);
          env = my_env::type_id::create("env", this);
        endfunction

        // agent
        function void build_phase(uvm_phase phase);
          super.build_phase(phase);
          if (!uvm_config_db#(apb_cfg)::get(this, "", "cfg", m_cfg))
            `uvm_fatal("CFG", "apb_cfg missing for this agent")
          // 이후 m_cfg.timeout_ns 등 사용
        endfunction
        ```
        **포인트**: 첫 인자 `this`는 set의 시작 컨텍스트, 두 번째 인자는 상대 경로. get의 `""`는 자기 자신의 경로.

!!! question "Exercise 2 (Analyze, ★★)"
    `config_db::set(this, "env.*.agent.*", "vif", vif)`의 wildcard와 `config_db::set(this, "env.agent", "vif", vif)`는 어떻게 다른가요? 어느 쪽이 silent failure를 만들기 쉬운지 설명하세요.

    ??? answer "모범 답안"
        - **Wildcard `env.*.agent.*`**: env 아래 어떤 중간 컴포넌트가 있든 그 아래 agent의 자식까지 모두 매칭. 유연하지만 의도와 다른 자식까지 hit할 수 있음.
        - **명시 경로 `env.agent`**: 정확히 `env.agent`만 매칭. 컴포넌트 이름이 변경되면(예: `env.apb_agent`로 리팩터링) 매칭 실패 → silent default.
        - **Silent failure 위험**: 명시 경로 쪽이 더 위험. wildcard는 너무 넓은 매칭이 문제, 명시 경로는 한 글자 오타가 문제. 권장: get 측에서 `if (!get(...)) `uvm_fatal(...)` 으로 강제 검출.

!!! question "Exercise 3 (Decide, ★★★)"
    다음 두 시나리오에 type override / instance override 중 무엇이 적절한지 정하고 이유를 설명하세요.
    - (a) 모든 환경의 Driver를 error-injecting 변형으로 한 번에 교체
    - (b) `env.cpu_agent.driver`만 시그널 글리치를 주입하는 변형으로 교체

    ??? answer "모범 답안"
        - **(a) type override**: `set_type_override_by_type(my_normal_drv::get_type(), my_err_drv::get_type())` — 모든 인스턴스에 적용. 환경 전체의 동작을 한 줄로 변경.
        - **(b) instance override**: `set_inst_override_by_type("uvm_test_top.env.cpu_agent.driver", my_normal_drv::get_type(), my_glitch_drv::get_type())` — 특정 경로만 교체. 다른 driver들은 정상.
        - **결정 규칙**: 변경의 scope가 *모든 곳*이면 type, *특정 경로/인스턴스*면 instance.

## 핵심 정리

- **`config_db`는 hierarchical path 기반**. 첫 인자(시작 컨텍스트) + 두 번째 인자(상대 경로)의 결합이 실제 경로.
- **set/get은 build_phase에서**. get 누락 시 silent default 동작 → 항상 `if (!get(...)) `uvm_fatal` 패턴.
- **`type_id::create`가 모든 컴포넌트 생성의 표준** (`new` 직접 호출 금지). Factory가 override를 반영.
- **type override = 모든 인스턴스, instance override = 특정 경로**. 변경 scope에 따라 선택.
- **디버그 도구**: `uvm_config_db::dump()` (전체 set 기록), `factory.print()` (등록된 type + override 매핑) — UVM_FATAL 이전에 호출.
- 자주 발생하는 cascading bug 패턴: 한 곳의 경로 오타 → silent → 의도와 다른 default → 다운스트림 false error.

## 다음 단계

- 📝 [**Module 04 퀴즈**](quiz/04_config_db_factory_quiz.md)
- ➡️ [**Module 05 — TLM, Scoreboard, Coverage**](05_tlm_scoreboard_coverage.md)

<div class="chapter-nav">
  <a class="nav-prev" href="03_sequence_and_item.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Sequence & Sequence Item</div>
  </a>
  <a class="nav-next" href="05_tlm_scoreboard_coverage.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">TLM, Scoreboard, Coverage</div>
  </a>
</div>
