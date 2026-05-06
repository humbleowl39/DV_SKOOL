# Unit 4: config_db & Factory

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
