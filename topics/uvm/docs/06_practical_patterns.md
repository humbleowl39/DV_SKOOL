# Module 06 — 실무 패턴 & 안티패턴

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Recognize** 자주 쓰이는 UVM 설계 패턴(Config Object, Sequencer Hierarchy, Layered Sequence)을 구분할 수 있다.
    - **Identify** 흔한 안티패턴(God Env, Monitor가 sequence 시작, 하드코딩된 경로)을 코드에서 찾아낼 수 있다.
    - **Plan** 새 검증 프로젝트의 from-scratch 환경 구축 체크리스트를 따라 디렉토리/파일 구조와 1주 차 작업을 계획할 수 있다.
    - **Critique** 동료의 UVM 코드 리뷰에서 근거를 들어 안티패턴을 지적하고 리팩터링을 제안할 수 있다.

!!! info "사전 지식"
    - [Module 01-05](01_architecture_and_phase.md) 전체
    - 한 번 이상 from-scratch 환경 구축 경험이 있으면 본문이 더 와닿음

## 왜 이 모듈이 중요한가

UVM 안티패턴은 **처음에는 작동하지만 환경이 커지면 cascading failure**를 만듭니다. 6년+ 경력자도 새 프로젝트에서 자주 반복하는 실수가 있고, 코드 리뷰에서 근거 없이 "이건 좀..." 같은 피드백은 무력합니다. 이 모듈은 **재현 가능한 좋은 설계 결정**을 내리는 어휘를 제공합니다.

## 핵심 개념
**실무에서 반복되는 설계 패턴을 익히면 환경 구축 속도와 품질이 동시에 향상. 안티패턴을 알면 디버그 시간을 대폭 줄일 수 있다. 이 Unit은 6년 실무에서 축적된 패턴/안티패턴을 정리.**

---

## 설계 패턴

### 패턴 1: Config Object 패턴

```
문제: config_db set/get가 수십 개 → 관리 불가, 오타 위험

해결: 관련 설정을 Config Object로 묶기

  class agent_config extends uvm_object;
    virtual my_if vif;
    bit is_active = 1;
    int timeout = 1000;
    bit enable_coverage = 1;
  endclass

→ set/get 1회로 모든 설정 전달
→ 새 설정 추가 시 Config Object에만 필드 추가
→ 포팅 시 Config Object만 교체 (Apple/Meta 사례)
```

### 패턴 2: Base Test + 상속 패턴

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
    super.build_phase(phase);
    // Factory Override로 Stress용 Sequence 교체
    set_type_override_by_type(
      normal_seq::get_type(), stress_seq::get_type());
  endfunction
endclass

→ 공통 환경은 base_test에, 시나리오별 차이만 하위 Test에
→ 새 테스트 추가 시 base_test 상속 + 시나리오만 작성
```

### 패턴 3: Layered Sequence 패턴

```
높은 추상 레벨 → 낮은 추상 레벨로 변환:

  System Sequence: "파일 읽기" (Application 레벨)
       ↓
  Protocol Sequence: "READ(LBA=0x100, len=8)" (SCSI 레벨)
       ↓
  Transport Sequence: "Command UPIU + Data-In UPIU" (UFS 레벨)
       ↓
  Pin-level: Driver가 신호 구동

각 레벨의 Sequence가 독립적으로 재사용 가능
→ UFS HCI 검증에서 이 계층 활용
```

### 패턴 4: Parameterized Agent

```systemverilog
class generic_axi_agent #(int DATA_W = 32, int ADDR_W = 32)
  extends uvm_agent;

  typedef generic_axi_item #(DATA_W, ADDR_W) item_t;
  typedef generic_axi_driver #(DATA_W, ADDR_W) driver_t;
  ...
endclass

// 사용
generic_axi_agent #(512, 40) wide_agent;   // 512-bit 데이터
generic_axi_agent #(32, 32)  narrow_agent; // 32-bit 데이터

→ 데이터/주소 폭만 다른 인터페이스에 같은 Agent 재사용
→ DCMAC (512-bit), 레지스터 (32-bit) 모두 커버
```

---

## 안티패턴 — 피해야 할 것

### 안티패턴 1: config_db 경로 하드코딩

```systemverilog
// BAD: 경로 문자열이 코드 전체에 분산
uvm_config_db #(int)::set(this, "env.axi_agent.driver", "timeout", 100);
uvm_config_db #(int)::set(this, "env.axi_agent.monitor", "timeout", 100);
// → 컴포넌트 이름 변경 시 모든 경로 수동 수정

// GOOD: Config Object + 와일드카드
uvm_config_db #(agent_cfg)::set(this, "env.axi_agent*", "cfg", cfg);
```

### 안티패턴 2: Driver에 DUT 로직 삽입

```systemverilog
// BAD: Driver가 기대값을 계산
task drive_and_check(my_item item);
  vif.data <= item.data;
  @(posedge vif.clk);
  if (vif.result != item.data * 2)  // ← DUT 로직!
    `uvm_error(...)
endtask

// GOOD: Driver는 구동만, 비교는 Scoreboard
// Driver: vif.data <= item.data;
// Scoreboard: ref_model.predict(item) vs monitor.actual
```

### 안티패턴 3: Sequence에서 시간 대기

```systemverilog
// BAD: Sequence가 DUT 타이밍에 의존
task body();
  start_item(item); finish_item(item);
  #100ns;  // ← 하드코딩 지연!
  start_item(next_item); finish_item(next_item);
endtask

// GOOD: 이벤트/핸드셰이크 기반
task body();
  start_item(item); finish_item(item);
  wait(env.monitor.transaction_complete);  // 이벤트 기반
  start_item(next_item); finish_item(next_item);
endtask
```

### 안티패턴 4: $display / $finish 사용

```systemverilog
// BAD: UVM 외부 출력
$display("Error: data mismatch");
$finish;

// GOOD: UVM 리포팅 사용
`uvm_error("SB", "Data mismatch")
`uvm_fatal("DRV", "Critical failure — cannot continue")

// 이유: UVM 리포팅은 컴포넌트 경로, 시간, 심각도를 자동 포함
//       필터링/카운팅/파일 출력 등 제어 가능
```

### 안티패턴 5: 모든 곳에서 Objection

```systemverilog
// BAD: 여러 컴포넌트에서 raise/drop → 종료 시점 예측 불가
// Driver: phase.raise_objection(this);
// Monitor: phase.raise_objection(this);
// Scoreboard: phase.raise_objection(this);

// GOOD: Test에서만 raise/drop
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

---

## From Scratch 환경 구축 체크리스트 (이력서 연결)

```
MangoBoost / Samsung에서 반복한 환경 구축 순서:

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

---

## Q&A

**Q: UVM 환경을 from scratch로 구축한 경험을 설명하라.**
> "MangoBoost에서 MMU IP와 DCMAC 서브시스템의 UVM 환경을 from scratch로 구축했다. 핵심 설계 원칙: (1) Config Object 패턴 — 포팅 시 Config만 교체. (2) Parameterized Agent — 데이터 폭만 다른 인터페이스에 재사용. (3) Base Test 상속 — 공통 환경 + 시나리오별 Test. (4) Virtual Sequence — 멀티 Agent 조합. 이 원칙들로 환경을 여러 프로젝트에 빠르게 포팅할 수 있었다."

**Q: UVM에서 가장 흔한 실수는?**
> "세 가지: (1) config_db 경로 오타 — 컴파일 타임에 안 잡히고 런타임에 get 실패. Config Object로 완화. (2) Driver에 DUT 로직 삽입 — 같은 버그를 양쪽에 구현하여 검출 불가. Scoreboard 분리 필수. (3) Objection 관리 — 여러 곳에서 raise/drop하면 종료 시점을 예측할 수 없음. Test에서만 관리."

**Q: 환경 포팅을 빠르게 하는 핵심은?**
> "세 가지 분리: (1) DUT 독립적 Agent — 프로토콜만 구현, DUT 로직 배제. (2) Config Object — SoC별 차이를 설정 객체로 흡수. (3) OTP/메모리 맵 추상화 — 물리 주소가 아닌 의미 기반 접근. Samsung에서 Apple/Meta 프로젝트 포팅 시 수 주 → 3-5일로 단축한 것이 이 원칙 덕분이다."

---

## 연습문제

!!! question "Exercise 1 (Evaluate, ★★)"
    다음 코드 스니펫에서 안티패턴 3개를 찾고, 각각 어떻게 수정해야 하는지 답하세요.

    ```systemverilog
    class my_env extends uvm_env;
      apb_driver  drv;     // (a) Agent 없이 driver 직접 보유
      virtual apb_if vif;
      function void connect_phase(uvm_phase phase);
        drv.vif = vif;     // (b) config_db 안 쓰고 직접 대입
      endfunction
      task run_phase(uvm_phase phase);
        my_seq seq = new();
        seq.start(drv);    // (c) sequencer 없이 driver에 start
      endtask
    endclass
    ```

    ??? answer "모범 답안"
        - **(a) Agent 누락**: env가 driver를 직접 보유 → 재사용 불가, Active/Passive 분리 안 됨. 수정: `apb_agent`를 만들고 driver/monitor/sequencer를 그 안에 두기.
        - **(b) Direct VIF 전달**: connect_phase에서 핸들 직접 대입 — config_db를 우회. 수정: top에서 `uvm_config_db#(virtual apb_if)::set(null, "uvm_test_top.env.agent.*", "vif", vif);`.
        - **(c) Sequencer 누락**: `seq.start(drv)`는 잘못. Sequence는 Sequencer에 start해야 함. 수정: `seq.start(env.agent.sqr);`.

!!! question "Exercise 2 (Create, ★★★)"
    새 SoC IP의 검증을 from scratch로 시작합니다. 첫 1주차에 끝낼 작업 5개를 의존 순서로 나열하세요.

    ??? answer "예시 답안"
        1. **인터페이스 sv 작성** (DUT 포트 매핑 + clocking block + modport)
        2. **Sequence Item 정의** (트랜잭션 필드 + 기본 constraint)
        3. **최소 Agent** (Driver 시그널 인가만 + Monitor sample만)
        4. **Top + Test 1개** (build → connect → reset → 1 transaction → smoke)
        5. **Smoke test 통과** (1 트랜잭션이 인가되고 Monitor가 캡처 + log 확인)
        의존성: 1→2 (item이 interface 신호 폭에 맞춰야), 2→3 (driver가 item 형식 알아야), 3→4 (env에 agent 인스턴스화), 4→5 (시뮬 실행).

!!! question "Exercise 3 (Analyze, ★★★)"
    Legacy SystemVerilog testbench(uvm 미사용, task 기반 자극)를 UVM으로 전환할 때의 단계 4개를 설계하고, 각 단계에서 무엇을 검증해 위험을 줄일지 답하세요.

    ??? answer "예시 답안"
        1. **Wrapper UVM env**: 기존 task 기반 자극은 그대로 두고 그 위에 빈 UVM env. 검증: 기존 시뮬 결과와 동일한지 sanity.
        2. **Monitor만 UVM화**: 신호 관찰을 UVM Monitor로 옮김. 자극은 여전히 legacy. 검증: Scoreboard에 actual이 잘 도착하는지 + legacy 결과와 일치.
        3. **Driver 도입**: 기존 task 자극을 Sequence + Driver로 재구성. 검증: 같은 시드에서 같은 자극 인가 패턴 (signal-level diff).
        4. **Sequence Library 정비**: 시나리오를 sequence 단위로 모듈화 + Virtual Sequence. 검증: 기존 테스트 리스트와 1:1 매핑 확인 + coverage가 떨어지지 않았는지.
        **위험 감소 포인트**: 각 단계에서 *기능 동등성*을 sanity로 확인하는 게 핵심. 한 번에 다 갈아엎지 않기.

## 핵심 정리

- **Config Object 패턴**: 환경 설정을 한 객체에 모아 config_db로 전달 — 흩어진 set/get 폭발 방지.
- **Sequencer Hierarchy**: virtual sequencer가 sub-sequencer 핸들을 보유 → multi-agent 시나리오의 표준.
- **Layered Sequence**: 상위 sequence가 하위 sequence를 호출 → 시나리오 재사용성 + 의도 명확화.
- **Anti: God Env** — env가 driver/monitor를 직접 보유하면 재사용 불가. Agent로 캡슐화.
- **Anti: Monitor에서 sequence 시작** — 책임 분리 위반. Monitor는 관찰만, sequence는 test 또는 vseq에서 시작.
- **Anti: 하드코딩된 config_db 경로** — 컴포넌트 이름 변경 시 silent failure. wildcard 또는 utility 함수.
- **From-scratch 체크리스트**: 인터페이스 → sequence item → 최소 agent → top + test → smoke 통과. 이 순서를 어기면 디버그 어려움.

## 다음 단계

- 📝 [**Module 06 퀴즈**](quiz/06_practical_patterns_quiz.md)
- ➡️ [**Module 07 — Quick Reference Card**](07_quick_reference_card.md) (인터뷰/리뷰 시 빠르게 참조)

<div class="chapter-nav">
  <a class="nav-prev" href="../05_tlm_scoreboard_coverage/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">TLM, Scoreboard, Coverage</div>
  </a>
  <a class="nav-next" href="../07_quick_reference_card/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">UVM — Quick Reference Card</div>
  </a>
</div>
