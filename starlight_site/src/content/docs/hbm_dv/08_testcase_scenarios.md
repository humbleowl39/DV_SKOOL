---
title: "Ch08 — Test Case & 시나리오 라이브러리"
---

:::tip[학습 목표]
이 챕터를 마치면:

- **Design** 원자 → 조합 → 시나리오의 3계층 시퀀스 라이브러리를 설계할 수 있다.
- **Implement** 정상 트래픽 배경 위에 오류를 주입하는 시나리오를 구현할 수 있다.
- **Differentiate** 레지스터 접근 검증과 설정 효과 검증을 구분하고 후자를 시나리오로 구현할 수 있다.
- **Construct** 지연·대역폭을 측정하는 성능 시나리오와 측정 수집기를 구성할 수 있다.
:::

:::note[사전 지식]
- [Ch03 — Custom UVM Agent A-to-Z](../03_custom_uvm_agent/): item의 `inject_*` 필드와 `t_req`·`t_rsp`
- [Ch07 — V-Plan & 검증 프로세스](../07_vplan_process/): 이 챕터는 V-Plan의 "테스트" 수단 행들을 구현합니다
- [UVM 코스 Module 03 — Sequence & Sequence Item](../../uvm/): **시퀀스의 동작 원리는 여기서 다룹니다**
:::

---

## 1. Why care? — 시나리오가 목록으로 쌓이면 생기는 일

V-Plan에 "테스트" 수단을 가진 행이 여러 개 있습니다. 하나씩 구현하기 시작합니다.

`test_basic_rw`를 만듭니다. 잘 돌아갑니다. `test_burst`를 만듭니다. 앞의 것을 복사해 조금 고칩니다. `test_csr_access`를 만듭니다. 또 복사합니다. `test_bank_sweep`… 복사합니다.

두 달 뒤 상황을 보면:

- 테스트 클래스가 40개인데 **상당 부분이 서로 복사본**입니다
- 새 시나리오를 추가할 때마다 **어느 것을 복사할지** 고민합니다
- 초기화 시퀀스를 고쳤더니 **40개 중 몇 개가 깨졌는지** 알 수 없습니다
- 그리고 **오류 주입 시나리오는 아직 하나도 없습니다.** V-Plan에는 있지만 "나중에" 미뤄졌고, 지금은 그 나중이 언제인지 아무도 모릅니다

마지막 항목이 특히 중요합니다. 오류 주입은 **정상 시나리오보다 만들기 번거롭고 급하지 않아 보이므로** 항상 뒤로 밀립니다. 그런데 선행 코스가 확인한 대로, 오류 검출 기능은 **오류를 주입하지 않으면 원리적으로 검증되지 않습니다.**

이 챕터는 두 가지를 다룹니다. **시나리오를 목록이 아니라 라이브러리로 만드는 방법**, 그리고 **뒤로 밀리기 쉬운 세 부류**(오류 주입·설정 효과·성능)를 실제로 구현하는 방법입니다.

---

## 2. 직관 — 재사용 단위는 테스트가 아니라 시퀀스다

### 순진한 시도 1 — 시나리오마다 독립적인 테스트 클래스

각 테스트가 자기 완결적이라 읽기 쉽고, 하나를 고쳐도 다른 것에 영향이 없습니다.

**어디서 막히나?** 영향이 없는 것이 아니라 **영향을 줄 수 없는 것**입니다. 공통 부분을 개선해도 이미 복사된 40곳에는 반영되지 않습니다. 그리고 시나리오를 **조합할 수 없습니다** — "버스트 트래픽 중에 모드를 전환하면서 동시에 오류를 주입"하는 시나리오를 만들려면 세 테스트의 코드를 손으로 합쳐야 합니다.

### 순진한 시도 2 — 하나의 거대한 랜덤 시퀀스로 전부 커버

제약을 잘 걸면 모든 조합이 언젠가 나올 것입니다. 코드도 하나뿐입니다.

**어디서 막히나?** **특정 조건을 조준할 수 없습니다.** 스펙 R17~R20(테스트 모드 진입·복귀)처럼 순서가 정해진 시나리오는 무작위로 나오기를 기다릴 수 없습니다. 그리고 실패했을 때 **무엇을 하려던 시나리오인지** 알기 어려워 디버깅이 힘듭니다.

### 일반화 — 3계층 시퀀스 라이브러리

> **재사용 단위는 테스트가 아니라 시퀀스다.** 시퀀스를 세 계층으로 나누고, 테스트는 **조립만** 한다.

| 계층 | 단위 | 예 |
|---|---|---|
| **① 원자 시퀀스** | 단일 트랜잭션 | `cci_read_seq`, `cci_write_seq`, `cci_csr_write_seq` |
| **② 조합 시퀀스** | 의미 있는 묶음 | `write_then_read_seq`, `bank_sweep_seq`, `burst_traffic_seq` |
| **③ 시나리오 시퀀스** | V-Plan 항목에 대응 | `par_err_inject_seq`, `sched_mode_effect_seq`, `perf_load_seq` |

```d2
direction: up

A: "**① 원자 시퀀스**\n단일 트랜잭션\nread / write / csr_wr / csr_rd" { style.fill: "#e8f5e9" }
B: "**② 조합 시퀀스**\n의미 있는 묶음\nwrite-then-read · bank sweep · burst 트래픽" { style.fill: "#fff8e1" }
C: "**③ 시나리오 시퀀스**\nV-Plan 항목에 대응\n오류 주입 · 설정 효과 · 성능 부하 · 모드 전이" { style.fill: "#e3f2fd" }
T: "**테스트 클래스**\n조립만 — 어떤 시나리오를 어떤 순서로" { style.fill: "#f3e5f5" }

A -> B -> C -> T
```

**그리고 하나의 원칙이 이 구조를 지탱합니다.**

> **시나리오는 자극만 만들고 판정하지 않는다.** 판정은 scoreboard와 assertion이 한다 (Ch09).

시나리오 안에서 값을 비교하기 시작하면 그 시나리오는 **특정 환경에 묶입니다.** 계층이 바뀌거나(Ch06) 프로파일이 바뀌면(Ch05) 깨집니다. 자극과 판정을 분리해야 같은 시나리오가 IP-level부터 full-chip까지 재사용됩니다.

---

## 3. 작은 예 — 뒤로 밀리기 쉬운 세 부류

### 3.1 오류 주입 시나리오 — #16

**설계 원칙: 오류는 정상 트래픽 배경 위에 놓는다.**

오류만 연속으로 보내면 *"오류 처리 중에도 정상 트랜잭션이 영향받지 않는가"* 를 확인할 수 없습니다. 실제 시스템에서 오류는 정상 흐름 사이에 드물게 발생합니다.

```systemverilog
// ③ 시나리오 계층 — 정상 트래픽 배경 위에 패리티 오류 주입
class par_err_inject_seq #(parameter int DATA_W=32, ADDR_W=34, ID_W=4)
  extends uvm_sequence #(cci_item#(DATA_W, ADDR_W, ID_W));

  `uvm_object_param_utils(par_err_inject_seq#(DATA_W, ADDR_W, ID_W))

  typedef cci_item#(DATA_W, ADDR_W, ID_W) item_t;

  // 강도 조절 파라미터 — 테스트가 설정
  rand int unsigned num_normal_before = 20;
  rand int unsigned num_normal_after  = 20;
  rand bit          target_pc         = 0;

  constraint c_reasonable {
    num_normal_before inside {[5:100]};
    num_normal_after  inside {[5:100]};
  }

  function new(string name = "par_err_inject_seq");
    super.new(name);
  endfunction

  virtual task body();
    item_t it;

    // ① 정상 트래픽 배경
    repeat (num_normal_before) send_normal();

    // ② 오류 하나 주입 — 스펙 R12
    it = item_t::type_id::create("err_it");
    start_item(it);
    if (!it.randomize() with {
          op                 == CCI_WRITE;
          pc                 == target_pc;
          inject_req_par_err == 1'b1;      // soft 제약을 덮어쓴다
        })
      `uvm_error("PAR_INJ", "오류 주입 트랜잭션 randomize 실패")
    finish_item(it);

    `uvm_info("PAR_INJ",
              $sformatf("패리티 오류 주입: pc=%0d id=%0d", it.pc, it.id), UVM_LOW)

    // ③ 오류 이후에도 정상 트래픽이 유지되는가
    repeat (num_normal_after) send_normal();
  endtask

  protected task send_normal();
    item_t it = item_t::type_id::create("it");
    start_item(it);
    if (!it.randomize() with { op inside {CCI_READ, CCI_WRITE}; })
      `uvm_error("PAR_INJ", "정상 트랜잭션 randomize 실패")
    finish_item(it);
  endtask
endclass
```

**이 시나리오가 만드는 것과 만들지 않는 것**

- **만드는 것**: 오류 하나가 정상 흐름 사이에 놓인 상황
- **만들지 않는 것**: 판정. `PARITY_ERR`로 응답했는지, `MR_ERR_STS.PAR_ERR`이 set됐는지는 **scoreboard와 assertion이 확인**합니다

R13(`PAR_CHK_EN=0`이면 미검사)·R14(W1C)까지 확인하려면 CSR 조작이 함께 필요하며, 그것은 **가상 시퀀스**에서 조립합니다.

```systemverilog
// 여러 시퀀스를 조립 — R12·R13·R14를 한 흐름에서
class par_err_full_seq extends uvm_sequence;
  `uvm_object_utils(par_err_full_seq)
  // ... p_sequencer 선언 생략 (UVM 코스 Module 03 참고)

  virtual task body();
    // R12 — 검사 켜진 상태에서 주입 → PARITY_ERR 기대
    csr_write(MR_ERR_EN_ADDR, 32'h1);      // PAR_CHK_EN = 1
    run_inject_seq();

    // R14 — 상태가 sticky인지, W1C로만 지워지는지
    csr_read(MR_ERR_STS_ADDR);             // set 확인 (판정은 scoreboard)
    csr_read(MR_ERR_STS_ADDR);             // 읽어도 유지되는지
    csr_write(MR_ERR_STS_ADDR, 32'h1);     // W1C
    csr_read(MR_ERR_STS_ADDR);             // clear 확인

    // R13 — 검사 끈 상태에서 주입 → 정상 처리 기대
    csr_write(MR_ERR_EN_ADDR, 32'h0);      // PAR_CHK_EN = 0
    run_inject_seq();
  endtask
endclass
```

Ch07의 자가 점검에서 R14를 **세 행**(set / sticky / W1C)으로 나눴던 것이 여기서 세 단계의 CSR 접근으로 구현됩니다.

### 3.2 설정 효과 시나리오 — #17

**핵심: 레지스터 접근 검증과 설정 효과 검증은 다른 것입니다.**

| | 확인하는 것 | 방법 |
|---|---|---|
| 레지스터 접근 검증 | 값이 저장·조회되는가 | write → read 비교 |
| **설정 효과 검증** | 그 값이 **동작을 바꾸는가** | 설정 변경 → **동작 관측** |

선행 코스 Ch05의 실패 3이 정확히 이 구분을 놓친 경우였습니다. 레지스터 비트는 저장되는데 그 비트를 참조하는 로직이 연결되지 않아도 read/write 테스트는 통과합니다.

```systemverilog
// tRCD 설정이 실제 ACT→RD 간격을 바꾸는가 — 스펙 R6 + A.7
class trcd_effect_seq extends uvm_sequence;
  `uvm_object_utils(trcd_effect_seq)

  // 두 설정값으로 같은 트래픽을 돌린다
  rand int unsigned trcd_low  = 8;
  rand int unsigned trcd_high = 16;

  virtual task body();
    // 단계 1 — 낮은 tRCD로 트래픽
    csr_write(MR_TIMING_ADDR, encode_timing(.trcd(trcd_low)));
    `uvm_info("TRCD_EFF", $sformatf("tRCD_CYC=%0d 구간 시작", trcd_low), UVM_LOW)
    run_bank_sweep_traffic();

    // 단계 2 — 높은 tRCD로 같은 트래픽
    csr_write(MR_TIMING_ADDR, encode_timing(.trcd(trcd_high)));
    `uvm_info("TRCD_EFF", $sformatf("tRCD_CYC=%0d 구간 시작", trcd_high), UVM_LOW)
    run_bank_sweep_traffic();
  endtask
endclass
```

**판정은 어디서 하는가**: 시나리오는 두 구간을 만들 뿐입니다. 확인은 두 곳에서 이루어집니다.

1. **Assertion** — 각 구간에서 실제 `ACT`→`RD` 간격이 그 시점의 `tRCD_CYC` **이상**인지 (R6). 설정을 참조하는 assertion이므로 Ch09에서 다룹니다
2. **Scoreboard·측정** — 두 구간의 간격 분포가 **실제로 달라졌는지**. 설정을 바꿨는데 간격이 그대로면 **설정이 동작에 연결되지 않은 것**입니다

두 번째가 핵심입니다. Assertion만 있으면 *"간격이 기준 이상"* 은 확인되지만, tRCD를 16으로 올렸는데 여전히 8 간격으로 동작해도 — 8은 16 이상이 아니므로 이 경우엔 잡힙니다. 그러나 반대 방향(내렸는데 안 줄어듦)은 assertion이 잡지 못하고 **분포 비교**로만 드러납니다.

**`SCHED_MODE`는 더 명확한 사례입니다.** 스펙 A.7의 세 모드(IN_ORDER / BANK_FIRST / PC_RR)는 **커맨드 발행 순서**를 바꿉니다. 순서는 규칙 위반이 아니므로 assertion이 잡지 않습니다. 오직 **관측된 순서 패턴을 비교**해야 확인됩니다.

:::note[🤔 잠깐 — 설정 효과 시나리오를 설계하세요]
스펙 A.7의 `MR_CTRL.SCHED_MODE`에 세 값이 있습니다.

> `0` IN_ORDER (도착 순) · `1` BANK_FIRST (이미 ACTIVE인 뱅크 우선) · `2` PC_RR (두 pseudo-channel 라운드로빈)

이 설정이 **실제로 동작을 바꾸는지** 검증하는 시나리오를 설계하세요. 무엇을 자극하고 무엇을 관측해야 합니까? 그리고 **assertion으로는 왜 부족합니까?**

<details>
<summary>정답 / 해설</summary>

**자극 설계 — 세 모드가 구분되는 트래픽을 만들어야 합니다**

모드 차이가 드러나려면 트래픽이 **선택의 여지**를 줘야 합니다.

- 미해결 요청이 **여러 개 동시에** 있어야 합니다 (하나뿐이면 어느 모드든 그것을 처리)
- 요청들이 **서로 다른 뱅크**를 향해야 합니다 (BANK_FIRST가 구분됨)
- 요청들이 **두 pseudo-channel에 분산**되어야 합니다 (PC_RR이 구분됨)
- 일부 뱅크는 **이미 ACTIVE 상태**여야 합니다 (BANK_FIRST의 판단 근거)

Ch03에서 driver를 non-blocking으로 만든 것이 여기서 필수 조건이 됩니다 — **미해결 요청이 1개면 이 시나리오가 성립하지 않습니다.**

**관측 — DCMD 쪽 커맨드 발행 순서**

CCI 쪽 요청 순서와 DCMD 쪽 `row_cmd`/`col_cmd` 발행 순서를 나란히 기록하고, 모드별로 그 **관계 패턴**을 비교합니다.

| 모드 | 기대 패턴 |
|---|---|
| IN_ORDER | 요청 도착 순서와 발행 순서가 일치 |
| BANK_FIRST | ACTIVE 뱅크 대상 요청이 **앞당겨짐** |
| PC_RR | 두 pc의 커맨드가 **번갈아** 나감 |

**왜 assertion으로 부족한가**

Assertion은 **규칙 위반**을 잡습니다. 그런데 세 모드 중 어느 것으로 동작하든 **스펙 규칙은 전부 지켜집니다** — R3(CA 공유), R4~R8(뱅크 상태·타이밍)은 순서와 무관하게 만족됩니다.

즉 `SCHED_MODE`를 무시하고 항상 IN_ORDER로 동작하는 DUT도 **모든 assertion을 통과합니다.** 잡히지 않는 이유는 그것이 위반이 아니기 때문입니다.

이것이 선행 코스 Ch05의 결론과 이어집니다 — *VIP도 assertion도 "규칙을 어겼는가"를 볼 뿐 "지시한 대로 했는가"를 보지 않습니다.* 후자는 **관측된 동작의 비교**로만 확인됩니다.

**추가로 필요한 것 — Coverage**

세 모드가 **실제로 모두 사용되었는지**는 coverage bin으로 확인합니다 (Ch07 V-Plan의 C-02). 시나리오가 있어도 회귀에서 한 모드만 돌았다면 나머지는 미검증입니다.

</details>
:::

### 3.3 성능 시나리오 — #2

성능은 **판정이 아니라 측정**입니다. 시나리오는 부하를 만들고, 별도의 수집기가 값을 모읍니다.

```systemverilog
// 부하 패턴을 파라미터로 받는 성능 시나리오
class perf_load_seq extends uvm_sequence;
  `uvm_object_utils(perf_load_seq)

  typedef enum { PAT_SEQUENTIAL, PAT_RANDOM, PAT_BANK_FOCUS, PAT_PC_SPREAD } pattern_e;

  rand pattern_e    pattern       = PAT_RANDOM;
  rand int unsigned num_txn       = 1000;
  rand int unsigned sched_mode    = 0;

  virtual task body();
    csr_write(MR_CTRL_ADDR, encode_ctrl(.en(1), .sched(sched_mode)));
    `uvm_info("PERF",
              $sformatf("패턴=%s 트랜잭션=%0d SCHED_MODE=%0d 측정 시작",
                        pattern.name(), num_txn, sched_mode), UVM_LOW)
    repeat (num_txn) send_by_pattern(pattern);
  endtask
endclass
```

```systemverilog
// 측정 수집기 — monitor의 analysis port를 구독
class perf_collector #(parameter int DATA_W=32, ADDR_W=34, ID_W=4)
  extends uvm_subscriber #(cci_item#(DATA_W, ADDR_W, ID_W));

  `uvm_component_param_utils(perf_collector#(DATA_W, ADDR_W, ID_W))

  typedef cci_item#(DATA_W, ADDR_W, ID_W) item_t;

  protected time         lat_sum, lat_max;
  protected int unsigned txn_cnt, beat_cnt;
  protected time         t_first, t_last;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void write(item_t t);
    time lat = t.t_rsp - t.t_req;      // Ch03에서 item에 넣어 둔 필드

    if (txn_cnt == 0) t_first = t.t_req;
    t_last    = t.t_rsp;
    lat_sum  += lat;
    if (lat > lat_max) lat_max = lat;
    txn_cnt++;
    beat_cnt += (t.rdata.size() > 0) ? t.rdata.size() : (t.len + 1);
  endfunction

  function void report_phase(uvm_phase phase);
    real elapsed_ns, bw_gbps, lat_avg;
    if (txn_cnt == 0) begin
      `uvm_warning("PERF", "측정된 트랜잭션이 없습니다")
      return;
    end
    elapsed_ns = real'(t_last - t_first);
    lat_avg    = real'(lat_sum) / real'(txn_cnt);
    bw_gbps    = (real'(beat_cnt) * DATA_W / 8.0) / elapsed_ns;   // bytes/ns = GB/s

    `uvm_info("PERF",
      $sformatf("트랜잭션=%0d | 지연 평균=%.1f 최악=%0t | 실효 대역폭=%.2f GB/s",
                txn_cnt, lat_avg, lat_max, bw_gbps), UVM_LOW)
  endfunction
endclass
```

**주목할 점 세 가지**

- `t.t_rsp - t.t_req` — **Ch03에서 item에 넣어 둔 필드**가 여기서 쓰입니다. 나중에 추가하려 했다면 monitor와 item을 모두 고쳐야 했습니다
- **지연과 대역폭을 함께 보고**합니다 — Ch07 #4의 요구. 한쪽만 보면 트레이드오프가 감춰집니다
- **수집기는 판정하지 않습니다** — 목표치 대비 판정은 V-Plan의 성능 항목에서 하며, 여기서는 값을 냅니다

`SCHED_MODE`를 바꿔 가며 같은 부하를 돌리면 **설정이 성능에 미치는 영향**이 나오고, 이것이 #2와 #17을 동시에 다룹니다.

---

## 4. 일반화 — 두 가지 구조적 선택

### 대안 A — 시나리오 안에서 직접 판정한다면?

시퀀스가 응답을 받아 기대값과 비교합니다. 테스트가 자기 완결적이 되어 읽기 좋습니다.

**왜 안 되나**: 세 가지가 걸립니다.

- **계층 이동 시 깨집니다** — Subsystem·Full-chip에서 Agent는 PASSIVE이고 시퀀스가 응답을 직접 받지 않습니다 (Ch06)
- **판정 로직이 분산됩니다** — 같은 규칙을 여러 시나리오가 각자 구현해 갈라집니다 (Ch06 실패 3과 같은 구조)
- **Ch03의 driver 구조와 충돌합니다** — driver가 응답을 기다리지 않으므로 시퀀스는 응답을 즉시 알 수 없습니다

**올바른 처리**: 시나리오는 자극만, 판정은 scoreboard·assertion. 이 분리가 시나리오를 계층·프로파일 독립적으로 만듭니다.

### 대안 B — 전부 constrained-random으로 만든다면?

제약만 잘 쓰면 조합 다양성이 확보되고 코드도 적습니다.

**왜 부족한가**: 순서가 정해진 시나리오를 조준할 수 없습니다. 테스트 모드 진입(R17) → 미해결 완료 대기 → ACK 확인(R18) → 복귀(R20)는 **정해진 순서**이며, 무작위로 나오기를 기다리는 것은 비효율적입니다.

**올바른 처리**: **혼합**입니다.

| 성격 | 방식 |
|---|---|
| 순서가 정해진 시나리오 (모드 전이, 오류 주입 타이밍) | **Directed** |
| 조합 다양성이 필요한 것 (주소 분포, 동시성) | **CRT** |
| 대부분의 실전 시나리오 | **Directed 골격 + 랜덤 요소** |

위의 `par_err_inject_seq`가 혼합의 예입니다 — 오류 위치는 directed(정확히 한 번, 지정된 위치), 주변 트래픽은 랜덤.

---

## 5. 디테일 — 시나리오 개발에서 실제로 벌어지는 일

### 실패 1 — 오류 주입이 계속 뒤로 밀린다

V-Plan에는 있는데 구현이 안 됩니다. 정상 시나리오가 급하고, 오류 주입은 만들기 번거롭기 때문입니다.

**관측되는 증상**: 프로젝트 후반까지 오류 검출 경로가 **한 번도 활성화되지 않습니다.** 회귀는 통과하고 코드 커버리지도 높습니다(선행 코스 Ch05: 조건이 참이 된 적 없어도 그 줄은 실행된 것으로 집계). 실리콘에서 실제 오류가 발생했을 때 검출 로직이 오작동합니다.

**처방**: 오류 주입 시나리오를 **기능 시나리오와 같은 마일스톤에 배치**합니다. 그리고 Ch03에서 확보한 구조(item의 `inject_*` 필드) 덕분에 **구현 비용이 낮다**는 점을 이용합니다 — 이 챕터의 `par_err_inject_seq`는 짧습니다. 비용이 낮으면 미룰 이유가 줄어듭니다.

### 실패 2 — 설정 효과를 레지스터 접근으로 대체한다

`csr_write` → `csr_read` → 값 일치. 이것으로 설정 검증을 마쳤다고 보는 경우입니다.

**관측되는 증상**: 선행 코스 Ch05 실패 3 그대로입니다. 레지스터 비트는 저장되는데 **그 비트를 참조하는 로직이 연결되지 않았거나 잘못 연결**되어 있어도 통과합니다. `SCHED_MODE`를 무시하고 항상 한 모드로 동작하는 DUT가 모든 테스트를 통과합니다.

**처방**: V-Plan에서 두 항목을 **분리**하고(Ch07), 설정 효과 항목의 측정 수단을 *"설정 변경 → 동작 관측 → 구간 비교"* 로 명시합니다.

### 실패 3 — 시나리오가 특정 환경에 종속된다

시나리오가 백도어 접근을 직접 호출하거나, 고정 지연을 넣거나, 판정 로직을 포함한 경우입니다.

**관측되는 증상**: Ch05·Ch06에서 예고한 대로 **프로파일이나 계층을 바꾸는 순간 대량으로 깨집니다.** 그리고 원인이 DUT가 아니라 시나리오 자신이므로, 고쳐야 할 파일이 수십 개입니다.

**처방**: 시나리오 코드 리뷰 체크리스트를 둡니다.

| 체크 | 이유 |
|---|---|
| 백도어를 직접 호출하지 않는가 | 프로파일 독립성 (Ch05) |
| 고정 사이클 대기가 없는가 | 프로파일 독립성 |
| 판정 로직이 없는가 | 계층 독립성 (Ch06) |
| 강도가 파라미터인가 | 회귀 규모 조절 |

---

## 6. 흔한 오해

| 오해 | 실제 |
|---|---|
| "테스트마다 독립적인 것이 안전하다" | 공통 개선이 반영되지 않고 **조합이 불가능**해집니다 |
| "CRT로 충분히 커버된다" | 순서가 정해진 시나리오는 **조준**해야 합니다 |
| "시나리오가 자기 결과를 확인하는 게 자연스럽다" | 계층·프로파일 이동 시 깨집니다. **자극과 판정을 분리**합니다 |
| "오류 주입은 여유 있을 때" | 뒤로 밀리면 결국 안 합니다. **기능 시나리오와 같은 마일스톤**에 둡니다 |
| "레지스터 read/write가 통과하면 설정 검증 완료" | **저장되는 것과 동작에 반영되는 것은 다릅니다** |
| "성능은 assertion으로 잡으면 된다" | 성능은 **위반이 아니라 값**입니다. 측정하고 목표와 비교합니다 |
| "오류만 연속으로 보내면 오류 처리를 잘 검증한다" | **정상 트래픽 배경**이 있어야 "오류 중 정상 유지"가 확인됩니다 |

---

## 🔧 이 문제를 이렇게 푼다

> **닫는 항목: #16 — 에러 주입을 시나리오의 독립 축으로 / #17 — Mode register 설정과 효과를 분리 검증 / #2 — 실효 대역폭·스케줄링 효율 측정**

### 라이브러리 구조

| 계층 | 규칙 |
|---|---|
| ① 원자 | 단일 트랜잭션. 다른 계층이 재사용 |
| ② 조합 | 의미 있는 묶음. 강도를 **파라미터**로 |
| ③ 시나리오 | **V-Plan 항목과 1:1 또는 1:N 대응** |
| 테스트 | **조립만.** 로직을 넣지 않음 |

**공통 원칙: 시나리오는 자극만, 판정은 scoreboard·assertion.**

### #16 — 오류 주입

- **정상 트래픽 배경 위에** 오류를 놓는다 (오류만 연속으로 보내지 않는다)
- 오류 **전·후 정상 동작 유지**까지 시나리오 범위에 포함
- 검사 활성/비활성 **양쪽**을 돌린다 (R12 / R13)
- 상태 레지스터의 **set → sticky → W1C** 전 과정을 밟는다 (R14)
- **기능 시나리오와 같은 마일스톤**에 배치한다 — 뒤로 밀리면 안 한다

### #17 — 설정 효과

- V-Plan에서 **레지스터 접근 항목과 설정 효과 항목을 분리**한다
- 설정 효과 시나리오는 **같은 트래픽을 설정만 바꿔 두 구간 이상** 돌린다
- 판정은 **구간 간 동작 비교** — assertion만으로는 부족하다
- `SCHED_MODE`처럼 **위반이 아닌 차이**는 관측 비교로만 확인된다
- 각 설정값이 실제로 사용됐는지는 **coverage bin**으로 (Ch10)

### #2 — 성능

- 부하 패턴을 **파라미터**로 (순차·랜덤·뱅크 집중·pc 분산)
- **지연과 대역폭을 함께** 수집·보고 (Ch07 #4)
- `SCHED_MODE`별로 측정해 **설정 효과와 성능을 동시에** 확인
- 수집기는 **값만 낸다.** 목표 대비 판정은 V-Plan 성능 항목에서
- 측정에는 Ch03의 `t_req`·`t_rsp`를 쓴다 — **자극 능력과 마찬가지로 측정 능력도 Agent 설계 시점에 확보**된다

---

## 7. 핵심 정리

- **재사용 단위는 테스트가 아니라 시퀀스**다. 원자 → 조합 → 시나리오 3계층, 테스트는 조립만
- **시나리오는 자극만 만들고 판정하지 않는다.** 이 분리가 계층·프로파일 독립성을 만든다
- 오류 주입은 **정상 트래픽 배경 위에** 놓는다. 오류 전후의 정상 동작 유지가 함께 확인되어야 한다
- 오류 주입은 **뒤로 밀리는 것이 기본값**이다. 기능 시나리오와 같은 마일스톤에 배치해 막는다
- **레지스터 접근 검증 ≠ 설정 효과 검증.** 후자는 설정을 바꿔 **동작을 관측·비교**해야 한다
- `SCHED_MODE` 같은 **위반이 아닌 차이**는 assertion이 잡지 못한다 — 관측 비교로만 확인된다
- 성능은 **판정이 아니라 측정**이다. 지연과 대역폭을 함께 내고, 목표 대비 판정은 V-Plan에서
- 측정 능력도 자극 능력처럼 **Agent 설계 시점에 확보**된다 (`t_req`·`t_rsp`)

:::note[🤔 마무리 자가 점검]
성능 시나리오를 돌린 결과가 나왔습니다.

> | SCHED_MODE | 실효 대역폭 | 평균 지연 | 최악 지연 |
> |---|---|---|---|
> | IN_ORDER | 1.42 TB/s | 84 사이클 | 210 사이클 |
> | BANK_FIRST | **1.78 TB/s** | 79 사이클 | **396 사이클** |
> | PC_RR | 1.61 TB/s | 81 사이클 | 245 사이클 |

팀에서 *"BANK_FIRST가 대역폭이 가장 높으니 기본값으로 하자"* 는 의견이 나왔습니다. 이 판단을 평가하고, **추가로 확인해야 할 것**을 제시하세요.

<details>
<summary>정답 / 해설</summary>

**대역폭만 보면 맞지만, 표가 이미 대가를 보여 주고 있습니다.**

BANK_FIRST는 대역폭이 25% 높은 대신 **최악 지연이 210 → 396 사이클로 거의 두 배**입니다. 평균 지연은 오히려 좋아졌으므로(84 → 79), **평균만 봤다면 이 대가가 보이지 않았을 것입니다.**

이것이 Ch07 #4에서 *"지연과 대역폭을 함께 보고하라"* 고 한 이유이고, 여기에 더해 **평균만이 아니라 최악값을 함께 내야 하는 이유**입니다.

**왜 이런 결과가 나오는가**: BANK_FIRST는 이미 ACTIVE인 뱅크 대상 요청을 앞당깁니다. 그래서 처리량은 오르지만, **다른 뱅크를 향한 요청이 계속 밀리는** 상황이 생길 수 있습니다. 밀린 요청의 지연이 최악값을 끌어올립니다.

**추가로 확인해야 할 것**

1. **최악 지연의 목표치가 있는가** — 시스템에 지연 상한 요구가 있다면 396이 그것을 넘는지가 판단 기준입니다. 목표치 없이 "대역폭이 높다"로 결정하면 Ch07 실패 2(목표치 없는 성능 판정)입니다
2. **기아(starvation) 가능성** — 특정 요청이 무한정 밀릴 수 있는지. 최악 396이 상한인지 아니면 부하가 더 높으면 더 커지는지 확인해야 합니다. 부하를 올려 가며 최악 지연의 추이를 보는 것이 방법입니다
3. **부하 패턴별 차이** — 이 표가 어떤 패턴에서 나왔는지가 중요합니다. `PAT_BANK_FOCUS`에서는 BANK_FIRST가 유리하지만 `PAT_PC_SPREAD`에서는 PC_RR이 나을 수 있습니다. **패턴 × 모드**로 표를 채워야 합니다
4. **지연 분포** — 평균과 최악만으로는 부족합니다. 소수의 요청만 심하게 밀리는 것인지 전반적으로 퍼진 것인지에 따라 시스템 영향이 다릅니다

**그리고 검증 관점의 결론**

기본값을 무엇으로 하느냐는 **설계·시스템 팀의 결정**이지 검증의 결정이 아닙니다. 검증이 해야 할 일은 **판단에 필요한 데이터를 정확히 제공하는 것**입니다 — 그리고 이 표는 그 역할을 이미 하고 있습니다. 최악 지연 열이 없었다면 팀은 대가를 모른 채 결정했을 것입니다.

또한 어느 모드를 기본값으로 하든, **세 모드 모두 검증 대상으로 남습니다.** 설정 가능하다면 누군가는 언젠가 바꿔 쓰기 때문입니다.

</details>
:::

**다음 챕터**: [Ch09 — Assertion · Protocol Checker](../09_assertion_checker/)에서 이 챕터가 계속 미뤄 온 "판정"을 구현합니다. 21항목 중 4건이 걸린 챕터입니다.

**퀴즈**: [Ch08 퀴즈](../quiz/08_testcase_scenarios_quiz/)

---

## 참고 자료

- [부록 A — `hbm_ch_ctrl` 스펙](../appendix_a_hbm_ch_ctrl_spec/) — R12~R16(오류), R17~R20(모드), A.7(CSR·SCHED_MODE)
- [Ch03 — Custom UVM Agent A-to-Z](../03_custom_uvm_agent/) — `inject_*` 필드와 `t_req`·`t_rsp`가 여기서 쓰입니다
- [UVM 코스 Module 03 — Sequence & Sequence Item](../../uvm/) — 시퀀스 계층과 virtual sequence
- [UVM 코스 Module 07 — Register Layer (RAL)](../../uvm/) — CSR 접근을 RAL로 다루는 방법
- [HBM 아키텍처 Ch05 — 인터페이스 프로토콜](../../hbm/05_interface_protocol/) — 설정과 효과의 분리, 에러 주입의 필요성
