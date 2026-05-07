# Module 03 — Sequence & Sequence Item

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Define** `rand` 필드와 constraint를 갖춘 Sequence Item 클래스를 설계할 수 있다.
    - **Implement** `body()` 안에서 `uvm_do_with` / `start_item`+`finish_item` 두 패턴을 구분해 작성할 수 있다.
    - **Compose** 여러 Agent의 Sequence를 조율하는 Virtual Sequence를 `p_sequencer`로 작성할 수 있다.
    - **Decide** Sequence Library / Layered Sequence / In-line constraint 중 시나리오에 맞는 패턴을 고를 수 있다.

!!! info "사전 지식"
    - [Module 01](01_architecture_and_phase.md), [Module 02](02_agent_driver_monitor.md)
    - SystemVerilog `randomize()` + constraint, in-line constraint 문법

## 왜 이 모듈이 중요한가

검증 가치의 절반은 **자극의 다양성과 의도성**에서 나옵니다. Sequence가 부실하면 coverage가 안 메워지고, 너무 hard-coded면 재사용이 안 됩니다. Virtual Sequence는 SoC-level 시나리오의 핵심 — 여러 Agent를 시간/순서로 조율해야 의미 있는 시스템 검증이 됩니다.

!!! tip "💡 이해를 위한 비유"
    **Sequence ↔ Sequence Item** ≈ **각본가(Sequence) ↔ 대사 한 줄(Item)**

    각본가는 어떤 대사를 어떤 순서로 던질지 계획하고, item 은 실제로 던지는 한 줄. 같은 대사도 누가 어떤 흐름에서 던지느냐에 따라 의미가 달라진다.

---

## 핵심 개념
**Sequence Item = 하나의 트랜잭션 데이터 (주소, 데이터, 제어). Sequence = Sequence Item들을 생성하는 시나리오 로직. Virtual Sequence = 여러 Agent의 Sequence를 조합하는 시스템 레벨 시나리오. 이 계층이 자극 생성의 핵심.**

!!! danger "❓ 흔한 오해"
    **오해**: `finish_item` 만 호출하면 충분하다

    **실제**: `start_item` + `randomize` + `finish_item` 의 3-단계가 모두 필요. start_item 없이 finish_item 호출하면 sequencer arbitration 을 거치지 않아 race / hang.

    **왜 헷갈리는가**: convenience 매크로(`uvm_do`) 가 이 셋을 한꺼번에 감춰주기 때문에 직접 작성할 때 한 단계를 빼먹기 쉽다.
---

## Sequence Item — 트랜잭션 데이터

```systemverilog
class axi_item extends uvm_sequence_item;
  `uvm_object_utils(axi_item)

  // 필드: 랜덤화 대상
  rand bit [31:0] addr;
  rand bit [31:0] data;
  rand bit        wr_rd;     // 1=Write, 0=Read
  rand int        burst_len; // 1~256

  // 제약: 유효한 조합만 생성
  constraint c_addr   { addr[1:0] == 2'b00; }        // 4-byte aligned
  constraint c_burst  { burst_len inside {[1:16]}; }  // 최대 16-beat
  constraint c_addr_range { addr < 32'h1000_0000; }   // 유효 주소 범위

  function new(string name = "axi_item");
    super.new(name);
  endfunction
endclass
```

### Sequence Item Automation — do 메서드

```systemverilog
class axi_item extends uvm_sequence_item;
  `uvm_object_utils(axi_item)

  rand bit [31:0] addr;
  rand bit [31:0] data;
  rand bit        wr_rd;
  rand int        burst_len;

  // --- do_copy: 깊은 복사 ---
  function void do_copy(uvm_object rhs);
    axi_item rhs_;
    super.do_copy(rhs);
    $cast(rhs_, rhs);
    this.addr      = rhs_.addr;
    this.data      = rhs_.data;
    this.wr_rd     = rhs_.wr_rd;
    this.burst_len = rhs_.burst_len;
  endfunction

  // --- do_compare: 필드별 비교 (Scoreboard에서 사용) ---
  function bit do_compare(uvm_object rhs, uvm_comparer comparer);
    axi_item rhs_;
    bit result;
    result = super.do_compare(rhs, comparer);
    $cast(rhs_, rhs);
    result &= (this.addr      == rhs_.addr);
    result &= (this.data      == rhs_.data);
    result &= (this.wr_rd     == rhs_.wr_rd);
    result &= (this.burst_len == rhs_.burst_len);
    return result;
  endfunction

  // --- do_print: 로그 출력 형식 정의 ---
  function void do_print(uvm_printer printer);
    super.do_print(printer);
    printer.print_field_int("addr",      addr,      32, UVM_HEX);
    printer.print_field_int("data",      data,      32, UVM_HEX);
    printer.print_field_int("wr_rd",     wr_rd,     1,  UVM_BIN);
    printer.print_field_int("burst_len", burst_len, 32, UVM_DEC);
  endfunction

  // --- convert2string: 간결한 문자열 표현 ---
  function string convert2string();
    return $sformatf("%s addr=0x%08h data=0x%08h burst=%0d",
                     wr_rd ? "WR" : "RD", addr, data, burst_len);
  endfunction
endclass
```

### do 메서드 vs Field Automation 매크로

```
방법 1: `uvm_field_* 매크로 (편리하지만 비추천)
  `uvm_object_utils_begin(axi_item)
    `uvm_field_int(addr, UVM_ALL_ON)
    `uvm_field_int(data, UVM_ALL_ON)
  `uvm_object_utils_end
  → 단점: 시뮬레이션 속도 저하 (10~30%), 디버그 어려움
  → Synopsys/Cadence 모두 do 메서드 직접 구현을 권장

방법 2: do 메서드 직접 구현 (권장)
  do_copy, do_compare, do_print, convert2string
  → 장점: 성능 최적, 비교 로직 커스터마이즈 가능
  → 예: 특정 필드를 비교에서 제외, 조건부 출력 등

실무 규칙:
  - 새 필드 추가 시 4개 메서드 모두 업데이트 (누락 → 비교 오류)
  - convert2string은 로그 가독성에 직접 영향 → 반드시 구현
  - do_compare에서 comparer 활용하면 mismatch 상세 리포트 가능
```

### Constraint 전략

| 전략 | 예시 | 용도 |
|------|------|------|
| 기본 제약 (Item) | `addr[1:0] == 0` | 항상 적용 (프로토콜 규칙) |
| Sequence 제약 | `item.addr == 32'h100` | 특정 시나리오 |
| Inline 제약 | `item.randomize() with { data > 0; }` | 호출 시점 오버라이드 |
| Disable 제약 | `item.c_burst.constraint_mode(0)` | 기존 제약 비활성화 |

---

## Sequence — 시나리오 로직

```systemverilog
class write_read_seq extends uvm_sequence #(axi_item);
  `uvm_object_utils(write_read_seq)

  task body();
    axi_item wr_item, rd_item;

    // Write
    wr_item = axi_item::type_id::create("wr_item");
    start_item(wr_item);
    assert(wr_item.randomize() with {
      wr_rd == 1;
      addr == 32'h0000_1000;
    });
    finish_item(wr_item);

    // Read back
    rd_item = axi_item::type_id::create("rd_item");
    start_item(rd_item);
    assert(rd_item.randomize() with {
      wr_rd == 0;
      addr == 32'h0000_1000;  // 같은 주소
    });
    finish_item(rd_item);
  endtask
endclass
```

### start_item / finish_item 흐름

```
Sequence                    Sequencer                Driver
   |                           |                       |
   |-- start_item(item) ----->|                       |
   |   (Sequencer에 요청)      |                       |
   |                           |-- grant ------------>|
   |                           |   (Driver 준비됨)     |
   |<-- (randomize here) -----|                       |
   |                           |                       |
   |-- finish_item(item) ---->|                       |
   |   (item 전달)             |-- get_next_item ---->|
   |                           |   (item 전달)         |
   |                           |                       |-- drive(item)
   |                           |                       |
   |                           |<-- item_done --------|
   |<-- (반환) --------------- |                       |
```

---

## Virtual Sequence — 멀티 Agent 시나리오

```systemverilog
class boot_vseq extends uvm_sequence;
  `uvm_object_utils(boot_vseq)

  // 여러 Agent의 Sequencer 핸들
  uvm_sequencer #(otp_item)    otp_sqr;
  uvm_sequencer #(ufs_item)    ufs_sqr;
  uvm_sequencer #(security_item) sec_sqr;

  task body();
    // 1. OTP 설정: Secure Boot ON, UFS 부팅
    otp_config_seq otp_seq = otp_config_seq::type_id::create("otp_seq");
    otp_seq.start(otp_sqr);

    // 2. UFS에 정상 이미지 로드
    ufs_load_seq ufs_seq = ufs_load_seq::type_id::create("ufs_seq");
    ufs_seq.start(ufs_sqr);

    // 3. 보안 공격: Fault Injection (선택)
    if (inject_fault) begin
      fi_attack_seq fi_seq = fi_attack_seq::type_id::create("fi_seq");
      fi_seq.start(sec_sqr);
    end
  endtask
endclass

// Test에서 사용
class secure_boot_test extends uvm_test;
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    boot_vseq vseq = boot_vseq::type_id::create("vseq");
    vseq.otp_sqr = env.otp_agent.sequencer;
    vseq.ufs_sqr = env.ufs_agent.sequencer;
    vseq.sec_sqr = env.sec_agent.sequencer;
    vseq.start(null);  // Virtual Sequencer 또는 null
    phase.drop_objection(this);
  endtask
endclass
```

### Sequence 계층 구조

```
uvm_test
  └── Virtual Sequence (시나리오 조합)
        ├── Agent_A Sequence (OTP 설정)
        │     └── Sequence Item (OTP 필드 값)
        ├── Agent_B Sequence (UFS 이미지 로드)
        │     └── Sequence Item (UFS 명령/데이터)
        └── Agent_C Sequence (보안 공격)
              └── Sequence Item (공격 유형/타이밍)

장점:
  - 개별 Sequence 재사용 가능
  - Virtual Sequence에서 조합만 변경하여 새 시나리오 생성
  - Test에서는 어떤 VSeq를 사용할지만 선택
```

---

## p_sequencer — Sequencer 리소스 접근

```systemverilog
// 문제: body() 안에서 Sequencer의 멤버에 접근하고 싶을 때
// m_sequencer는 uvm_sequencer_base 타입 → 커스텀 멤버 접근 불가

// 해결: `uvm_declare_p_sequencer로 타입 캐스팅 자동화
class my_seq extends uvm_sequence #(axi_item);
  `uvm_object_utils(my_seq)
  `uvm_declare_p_sequencer(my_sequencer)
  // → p_sequencer 멤버가 my_sequencer 타입으로 자동 선언

  task body();
    // p_sequencer를 통해 Sequencer의 커스텀 멤버에 접근
    if (p_sequencer.cfg.enable_error_injection) begin
      // 에러 주입 시나리오
    end

    // Sequencer가 보유한 다른 정보 활용
    `uvm_info("SEQ", $sformatf("Running on %s", p_sequencer.get_full_name()), UVM_LOW)
  endtask
endclass

// 커스텀 Sequencer 예시
class my_sequencer extends uvm_sequencer #(axi_item);
  `uvm_component_utils(my_sequencer)

  my_agent_config cfg;  // Sequence에서 접근할 설정

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db #(my_agent_config)::get(this, "", "cfg", cfg))
      `uvm_fatal("CFG", "Agent config not found")
  endfunction
endclass
```

### p_sequencer 사용 시 주의

| 주의사항 | 설명 |
|---------|------|
| 재사용성 저하 | 특정 Sequencer 타입에 의존 → 다른 Agent에 재사용 어려움 |
| 대안: config_db | Sequence에서 `uvm_config_db::get` 으로 설정을 직접 획득 |
| 사용 적합 시점 | Sequencer 고유 기능 필요 시 (arbitration 제어, 큐 상태 등) |
| 기본 원칙 | 단순 설정 전달 → config_db, Sequencer 제어 필요 → p_sequencer |

---

## Response 핸들링 — Driver → Sequence 응답

```systemverilog
// 기본 흐름은 Sequence → Driver (단방향)
// Response를 사용하면 Driver → Sequence (양방향) 가능

// --- Sequence 측: Response 수신 ---
class read_seq extends uvm_sequence #(axi_item);
  `uvm_object_utils(read_seq)

  task body();
    axi_item req, rsp;

    req = axi_item::type_id::create("req");
    start_item(req);
    assert(req.randomize() with { wr_rd == 0; });  // Read
    finish_item(req);

    // Driver로부터 응답 수신 (Read 데이터)
    get_response(rsp);
    `uvm_info("SEQ", $sformatf("Read data: 0x%08h", rsp.data), UVM_LOW)
  endtask
endclass

// --- Driver 측: Response 송신 ---
class my_driver extends uvm_driver #(axi_item);
  task run_phase(uvm_phase phase);
    forever begin
      seq_item_port.get_next_item(req);

      // Pin-level 구동
      drive_item(req);

      // Read인 경우 DUT로부터 읽은 데이터를 Response로 전달
      if (!req.wr_rd) begin
        axi_item rsp = axi_item::type_id::create("rsp");
        rsp.set_id_info(req);  // ★ 필수: req의 ID를 복사하여 매칭
        rsp.data = vif.rdata;
        seq_item_port.put_response(rsp);  // Sequence로 응답
      end

      seq_item_port.item_done();
    end
  endtask
endclass
```

### Response 흐름

```
Sequence                    Sequencer                Driver
   |                           |                       |
   |-- start_item(req) ------>|                       |
   |-- finish_item(req) ----->|-- get_next_item ----->|
   |                           |                       |-- drive(req)
   |                           |                       |
   |                           |<-- put_response(rsp) -|
   |                           |<-- item_done ---------|
   |<-- get_response(rsp) ----|                       |
   |   (rsp.data 사용)         |                       |

핵심:
  - set_id_info(req): rsp에 req의 transaction_id/sequence_id 복사
    → Sequencer가 어떤 Sequence의 응답인지 매칭
  - get_response는 blocking — 응답이 올 때까지 대기
  - item_done()과 put_response() 순서 주의 (put_response 먼저)
```

### item_done(rsp) 단축 패턴

```systemverilog
// put_response + item_done을 한 줄로:
task run_phase(uvm_phase phase);
  forever begin
    seq_item_port.get_next_item(req);
    drive_item(req);
    req.data = vif.rdata;        // req 자체에 응답 데이터 기록
    seq_item_port.item_done(req); // item_done에 rsp 전달 = 한 번에 처리
  end
endtask

// Sequence 측에서는 동일하게 get_response(rsp) 사용
// 장점: 별도 rsp 객체 생성 불필요, 코드 간결
// 주의: req 객체를 재사용하므로 Sequence 측에서 즉시 복사해야 함
```

---

## Sequencer Arbitration — 다중 Sequence 제어

```systemverilog
// 하나의 Sequencer에 여러 Sequence가 동시에 실행될 때 순서 결정

// Arbitration 모드 설정
env.agent.sequencer.set_arbitration(UVM_SEQ_ARB_FIFO);
```

### Arbitration 모드

| 모드 | 동작 | 용도 |
|------|------|------|
| `UVM_SEQ_ARB_FIFO` | 요청 순서대로 (기본값) | 대부분의 경우 |
| `UVM_SEQ_ARB_WEIGHTED` | 우선순위 가중치 기반 | 트래픽 믹스 비율 제어 |
| `UVM_SEQ_ARB_RANDOM` | 랜덤 선택 | 랜덤 트래픽 패턴 |
| `UVM_SEQ_ARB_STRICT_FIFO` | 우선순위 → FIFO | 긴급 트랜잭션 우선 처리 |
| `UVM_SEQ_ARB_STRICT_RANDOM` | 우선순위 → 랜덤 | 우선순위 내 랜덤 |
| `UVM_SEQ_ARB_USER` | 사용자 정의 | 커스텀 스케줄링 |

### grab / lock — Sequencer 독점

```systemverilog
// grab: 즉시 독점 (현재 진행 중인 item 이후부터)
class critical_seq extends uvm_sequence #(axi_item);
  task body();
    // Sequencer를 독점 — 다른 Sequence는 대기
    grab();

    // 이 구간에서는 이 Sequence의 item만 Driver로 전달
    repeat (10) begin
      axi_item item = axi_item::type_id::create("item");
      start_item(item);
      assert(item.randomize());
      finish_item(item);
    end

    // 독점 해제
    ungrab();
  endtask
endclass

// lock: grab과 유사하지만 우선순위가 낮음
// → 현재 큐에 있는 모든 pending 요청이 처리된 후 독점
// grab: 즉시 독점 (더 공격적)
// lock: 대기 후 독점 (더 안전)
```

### grab vs lock 비교

```
시나리오: Seq_A, Seq_B가 동시 실행 중, Seq_C가 독점 요청

grab():
  Seq_A: item3 대기중 → ★ 즉시 중단
  Seq_B: item2 대기중 → ★ 즉시 중단
  Seq_C: grab() → 바로 독점 시작
  → 용도: Reset Sequence, Error Recovery 등 긴급 상황

lock():
  Seq_A: item3 대기중 → 처리 완료까지 대기
  Seq_B: item2 대기중 → 처리 완료까지 대기
  Seq_C: lock() → pending 모두 처리 후 독점
  → 용도: Atomic 트랜잭션 (연속 burst 등)
```

---

## Sequence Library 패턴

```systemverilog
// 기본 시퀀스들을 라이브러리로 관리
// seq_lib/axi_base_seq.sv          — 공통 베이스
// seq_lib/axi_write_seq.sv         — 단순 Write
// seq_lib/axi_read_seq.sv          — 단순 Read
// seq_lib/axi_burst_seq.sv         — Burst 전송
// seq_lib/axi_error_seq.sv         — 에러 주입
// vseq_lib/boot_normal_vseq.sv     — 정상 부팅
// vseq_lib/boot_attack_vseq.sv     — 공격 시나리오

패키지:
// my_seq_lib_pkg.sv
package my_seq_lib_pkg;
  `include "axi_base_seq.sv"
  `include "axi_write_seq.sv"
  ...
endpackage
```

---

## Q&A

**Q: Sequence와 Driver의 역할 분리 이유는?**
> "Sequence는 '무엇을 보낼지'(시나리오 로직), Driver는 '어떻게 보낼지'(핀 레벨 구동)를 담당한다. 분리하면 (1) 같은 Driver에 다른 Sequence를 붙여 다양한 시나리오 실행 가능. (2) 같은 Sequence를 다른 Driver(다른 DUT)에 재사용 가능. (3) Sequence는 프로토콜 독립적이므로 추상 레벨에서 시나리오를 기술할 수 있다."

**Q: Virtual Sequence를 왜 사용하는가?**
> "시스템 레벨 시나리오는 여러 Agent를 동시에 조정해야 한다. 예를 들어 BootROM 검증에서 OTP 설정 + UFS 이미지 로드 + 보안 공격을 동기화해야 한다. Virtual Sequence가 여러 Agent의 Sequencer를 참조하여 이 조정을 한 곳에서 관리한다. 개별 Sequence를 재사용하면서 조합만 변경하여 새 시나리오를 만들 수 있다."

**Q: Constrained Random의 장점은?**
> "두 가지: (1) 인간이 생각하지 못한 코너 케이스를 자동 생성. (2) Seed 변경만으로 다른 시나리오를 무한히 생성. 그러나 순수 Random은 비효율적이므로, Constraint로 유효 범위를 제한하고(프로토콜 규칙, 주소 범위), Coverage 기반으로 미커버 영역에 집중하는 것이 Coverage-Driven Random의 핵심이다."

**Q: `uvm_field_*` 매크로 대신 do 메서드를 직접 구현하는 이유는?**
> "성능과 제어 두 가지이다. (1) `uvm_field_*` 매크로는 내부적으로 reflection 기반 처리를 하여 시뮬레이션 속도가 10~30% 저하된다. 수십만 개 트랜잭션을 처리하는 검증에서 이 오버헤드는 무시할 수 없다. (2) do_compare에서 특정 필드만 비교하거나, do_print에서 조건부 출력 등 커스터마이즈가 불가능하다. 실무에서는 do_copy, do_compare, do_print, convert2string 4개를 직접 구현하는 것이 표준이다."

**Q: Sequence에서 Driver의 Response를 받아야 하는 경우는?**
> "Read 트랜잭션이 대표적이다. Sequence가 Read 요청을 보내고, Driver가 DUT에서 읽은 데이터를 Response로 돌려줘야 Sequence에서 후속 로직(예: 읽은 값 기반으로 다음 Write 주소 결정)을 실행할 수 있다. 핵심은 `set_id_info(req)`로 Response에 원본 Request의 ID를 복사하는 것이다. 이것이 없으면 Sequencer가 Response를 올바른 Sequence에 매칭할 수 없다."

**Q: grab과 lock의 차이는?**
> "둘 다 Sequencer를 독점하지만 타이밍이 다르다. grab은 즉시 독점 — 현재 pending된 다른 Sequence 요청을 밀어내고 바로 제어권을 가져간다. Reset Sequence처럼 긴급 상황에 사용한다. lock은 현재 pending된 모든 요청이 처리된 후 독점한다. Atomic burst 전송처럼 중간에 다른 트래픽이 끼면 안 되는 경우에 사용한다. 실무에서는 grab은 드물고 lock을 더 자주 사용한다 — grab의 즉시 중단은 프로토콜 위반을 유발할 수 있기 때문이다."

---

## 연습문제

!!! question "Exercise 1 (Apply, ★)"
    주소가 `[32'h1000:32'h1FFF]` 범위에서 균등 분포된 read 트랜잭션 100건을 생성하는 Sequence를 작성하세요.

    ??? answer "모범 답안"
        ```systemverilog
        class read_seq extends uvm_sequence#(my_item);
          `uvm_object_utils(read_seq)
          function new(string name="read_seq"); super.new(name); endfunction

          task body();
            repeat (100) begin
              `uvm_do_with(req, {
                req.kind == READ;
                req.addr inside {[32'h1000:32'h1FFF]};
              })
            end
          endtask
        endclass
        ```

!!! question "Exercise 2 (Analyze, ★★)"
    `uvm_do_with`를 사용한 코드와 `start_item / finish_item`을 사용한 코드의 동작 차이를 두 가지 이상 들고, 각각이 적절한 시나리오를 설명하세요.

    ??? answer "모범 답안"
        - **`uvm_do_with`**: 매크로가 `create + randomize + start_item + finish_item`을 묶어서 처리. 짧고 깔끔. 단점: randomization 결과를 send 전에 검사/수정 불가.
        - **`start_item / finish_item`**: create + randomize 후 start_item과 finish_item 사이에 직접 필드 수정 가능. 예: `req.addr += offset_from_test;`. 단점: 코드가 길어짐.
        - **적절 시나리오**: 단순 랜덤은 `uvm_do_with`, 시퀀스 계층 간 데이터 forwarding이나 conditional constraint relaxation은 start/finish.

!!! question "Exercise 3 (Create, ★★★)"
    APB(register access) Agent와 AXI(data) Agent를 동시에 사용하는 Virtual Sequence를 설계하세요. 시나리오: APB로 DUT 활성화 레지스터 set → AXI로 100건 traffic → APB로 status 읽기.

    ??? answer "예시 답안"
        ```systemverilog
        class boot_vseq extends uvm_sequence;
          `uvm_object_utils(boot_vseq)
          `uvm_declare_p_sequencer(my_virtual_sequencer)
          function new(string name="boot_vseq"); super.new(name); endfunction

          task body();
            apb_write_seq w_seq; axi_traffic_seq t_seq; apb_read_seq r_seq;
            // 1) DUT enable
            `uvm_do_on_with(w_seq, p_sequencer.apb_sqr,
                            { addr == 32'h0010; data == 32'h1; })
            // 2) Data traffic
            `uvm_do_on(t_seq, p_sequencer.axi_sqr)
            // 3) Status
            `uvm_do_on_with(r_seq, p_sequencer.apb_sqr,
                            { addr == 32'h0014; })
          endtask
        endclass
        ```
!!! warning "실무 주의점 — `start_item` / `finish_item` 없이 `randomize()` 단독 호출"
    **현상**: Sequence Item이 randomize는 되지만 Sequencer/Driver로 전달되지 않아 DUT에 자극이 인가되지 않음. 시뮬은 정상 종료되고 커버리지도 0이지만 에러 메시지는 없음.

    **원인**: `uvm_do` / `uvm_do_with` 매크로를 쓰지 않고 `req.randomize()` 후 바로 다음 로직으로 넘어갈 때 발생한다. `start_item(req)`가 Sequencer에 item 전달 요청을 등록하고, `finish_item(req)`가 Driver로 item을 실제 전송한다. 이 둘 중 하나라도 빠지면 item은 Sequencer 큐에 들어가지 않는다.

    **점검 포인트**: `UVM_HIGH` verbosity 로그에서 `[Sequencer]` 수신 메시지 카운트를 확인. Sequence `body()` 안에 `start_item(req)` → `req.randomize()` → `finish_item(req)` 순서로 3개가 모두 존재하는지 코드 리뷰. `uvm_do_with` 사용 시에는 내부에서 자동 처리되므로 이 문제가 없다.

## 핵심 정리

- **Sequence Item = 데이터+constraint, Sequence = 시나리오 로직.** 둘은 다른 클래스 계층 (`uvm_sequence_item` vs `uvm_sequence`).
- **`uvm_do_with` 짧음 / `start_item+finish_item` 세밀.** 데이터 후처리 필요하면 후자.
- **Virtual Sequence는 multi-agent 동기화의 표준.** `p_sequencer`로 sub-sequencer 핸들 접근.
- **Sequence Library 패턴**으로 시나리오 재사용. Constraint를 sequence 내부에 두지 말고 sequence item이나 별도 bag에.
- **Response 핸들링**: `has_response` 체크 후 `get_response`. set_id_info 빠뜨리면 multi-sequence 환경에서 응답 매칭 실패.
- **Sequencer Arbitration**: 다중 sequence 동시 실행 시 정책으로 트래픽 믹스/우선순위 제어.

## 다음 단계

- 📝 [**Module 03 퀴즈**](quiz/03_sequence_and_item_quiz.md)
- ➡️ [**Module 04 — config_db & Factory**](04_config_db_factory.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../02_agent_driver_monitor/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Agent / Driver / Monitor</div>
  </a>
  <a class="nav-next" href="../04_config_db_factory/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">config_db & Factory</div>
  </a>
</div>
