---
title: "Module 03 — RAS-node & Fault Injection (DV)"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** RAS-node의 error record 레지스터(`ERR<n>STATUS` 계열)가 무엇을 기록하고 어떻게 인터럽트/telemetry로 이어지는지 설명할 수 있다.
- **Implement** error record를 RAL register model로, fault injection을 시퀀스 레벨로 작성할 수 있다.
- **Trace** 주입한 에러가 검출→기록→인터럽트→clear까지 RAS 로직을 통과하는 경로를 추적할 수 있다.
- **Evaluate** fault injection을 RTL force가 아닌 inject 레지스터/시퀀스 레벨로 해야 하는 이유를 trade-off 기반으로 판단할 수 있다.
:::
:::note[사전 지식]
- [Module 01](../01_why_ras/), [Module 02](../02_ecc_parity_poison/) (세 기둥, CE/UE/poison)
- UVM 검증 기본: sequence, sequencer, RAL — [UVM 코스](../../uvm/), 특히 [M07 RAL](../../uvm/07_register_layer_ral/)
- 메모리-맵 레지스터 access policy(RO/RW/**W1C**)
:::
---

## 1. Why care? — RAS 로직은 "에러가 나야" 동작한다

### 1.1 시나리오 — 검증할 수 없는 RAS 경로

RAS-node의 error record 로직, 인터럽트 경로, telemetry는 모두 _에러가 발생했을 때만_ 동작합니다. 그런데 검증 환경에서 실제 비트 플립이나 메모리 노화를 일으킬 수는 없습니다. 그러면 이 경로들을 어떻게 자극할까요?

```
나쁜 방법 — RTL force (안티패턴):
  force tb_top.dut.u_cache.ecc_err = 1'b1;
  → 특정 RTL 신호명·계층에 결합 → 리비전마다 깨짐
  → 재사용 불가, 다른 블록에 못 옮김, 검토자가 의도를 못 읽음

좋은 방법 — Fault Injection 레지스터 + 시퀀스 레벨:
  ral.ERRFR/inject_reg.write(...) 로 "다음 접근에서 에러 주입" 프로그래밍
  → HW가 의도한 inject 경로를 통해 자극
  → 버스/RAL로 추상화 → 재사용·이식·가독 모두 확보
```

HDG 스펙이 명시하듯, fault injection은 "특정 레지스터를 프로그래밍해 runtime에 가짜 에러를 주입"하는 HW 기능입니다. 즉 _RTL을 건드리는 것이 아니라 칩이 제공하는 inject 레지스터를 시퀀스로 쓰는 것_ 이 정석입니다. 이 모듈은 그 검증 방법론을 다룹니다.

---

## 2. Intuition — 블랙박스 레코더, 한 장 그림

:::tip[💡 한 줄 비유]
**RAS-node** ≈ **항공기의 블랙박스 + 비상벨**.<br>
에러(사고)가 나면 무엇이·어디서·언제 잘못됐는지를 `ERR<n>STATUS`/`ERR<n>ADDR` 레지스터(블랙박스)에 자동 기록하고, 동시에 비상벨(인터럽트)을 눌러 SCP/BMC(관제탑)를 부릅니다. **Fault injection** 은 사고를 _실제로 내지 않고_ 비상벨·블랙박스가 제대로 작동하는지 점검하는 **소방 훈련** 입니다.
:::

### 한 장 그림 — RAS-node 와 검증 환경

```d2
direction: right

SEQ: "**Fault Inject Sequence**\nral.INJECT.write(err_type)\n→ 다음 접근에 에러 주입"
RAL: "**RAL reg model**\nERRSTATUS / ERRADDR\nERRCTLR(inject)\n(이름 기반 접근)"
DUT: "**DUT RAS-node**\n에러 검출 → record 기록\n인터럽트 raise"
MON: "Bus / IRQ Monitor\n(record + 인터럽트 관찰)"
PRED: "uvm_reg_predictor\n(mirror 갱신)"
SB: "**Scoreboard**\n기대 record/IRQ vs 실제"

SEQ -> RAL: "frontdoor"
RAL -> DUT: "adapter → bus"
DUT -> MON: "record read / IRQ"
MON -> PRED: "bus item"
PRED -> RAL: "predict" { style.stroke-dash: 4 }
MON -> SB: "관찰값"
SEQ -> SB: "기대값(reference)"
```

### 왜 이 구조인가 — Design rationale

세 요구의 교집합입니다.

1. **물리 고장 없이 RAS 로직을 자극** → DUT가 제공하는 inject 레지스터를 시퀀스로 프로그래밍(RTL force 금지).
2. **error record가 정확한지 비교** → record 레지스터를 RAL로 모델링하고, 기대값(주입한 type/addr)과 관찰값을 scoreboard에서 비교.
3. **인터럽트/telemetry 경로까지 검증** → IRQ를 monitor로 관찰하고, clear(W1C) 후 인터럽트가 내려가는지까지 자극.

---

## 3. 작은 예 — 주입 한 번이 기록·인터럽트·clear까지

UE를 한 번 주입하고, error record가 기록되고, 인터럽트가 올라갔다가, W1C로 clear되어 내려가는 흐름을 봅시다.

### 단계별 다이어그램

```d2
direction: down

S1: "**① INJECT.write(UE, addr=A)**\nDUT에 '다음 접근에서 UE 주입' 프로그래밍\n(시퀀스 레벨, RTL force 아님)"
S2: "**② 해당 접근 발생 → UE 검출**\nERRSTATUS.UE=1, ERRSTATUS.V=1\nERRADDR=A 캡처"
S3: "**③ 인터럽트 raise**\nerror IRQ → SCP/BMC\n(telemetry 경로)"
S4: "**④ STATUS read → 기대값 비교**\nScoreboard: UE=1, addr=A 확인"
S5: "**⑤ W1C: STATUS.V/UE에 1 write → clear**\n인터럽트 deassert\nrecord 정리"
S1 -> S2 -> S3 -> S4 -> S5
```

### 단계별 의미

| Step | 누가 | 무엇을 | 검증 포인트 |
|------|------|--------|------------|
| ① | inject 시퀀스 | `INJECT.write(UE, addr=A)` | 시퀀스 레벨 주입 (RTL force ❌) |
| ② | DUT RAS-node | UE 검출 → `ERRSTATUS.V/UE` set, `ERRADDR=A` | record가 정확히 기록되는가 |
| ③ | DUT | error 인터럽트 raise | IRQ가 실제로 올라가는가 |
| ④ | scoreboard | 기대(UE, A) vs 관찰 record 비교 | type/addr 정확성 |
| ⑤ | clear 시퀀스 | `STATUS`에 1 write(W1C) → clear, IRQ 내려감 | W1C 동작 + 인터럽트 deassert |

핵심: **주입은 시퀀스로, 기록은 RAL로 읽어 scoreboard와 비교, 인터럽트는 monitor로 관찰, clear는 W1C 시퀀스로** — 전 과정이 재사용 가능한 검증 레이어 위에서 일어납니다.

### 코드 — error record RAL 모델 (개념적 형태)

```systemverilog
// ERRSTATUS 레지스터: 에러 type/valid 비트 (W1C clear)
class err_status_reg extends uvm_reg;
  `uvm_object_utils(err_status_reg)
  rand uvm_reg_field V;    // Valid: 유효 에러 기록 존재
  rand uvm_reg_field CE;   // Corrected Error
  rand uvm_reg_field UE;   // Uncorrectable Error

  function new(string name = "err_status_reg");
    super.new(name, 32, UVM_NO_COVERAGE);
  endfunction

  virtual function void build();
    V  = uvm_reg_field::type_id::create("V");
    CE = uvm_reg_field::type_id::create("CE");
    UE = uvm_reg_field::type_id::create("UE");
    // configure(parent, size, lsb, access, volatile, reset, has_reset, is_rand, indiv)
    V.configure (this, 1, 0,  "W1C", 1, 1'h0, 1, 0, 1);  // 1 write → clear
    CE.configure(this, 1, 1,  "W1C", 1, 1'h0, 1, 0, 1);
    UE.configure(this, 1, 2,  "W1C", 1, 1'h0, 1, 0, 1);
  endfunction
endclass

// ERRADDR: failing address (RO — HW가 캡처)
class err_addr_reg extends uvm_reg;
  `uvm_object_utils(err_addr_reg)
  uvm_reg_field ADDR;
  function new(string name = "err_addr_reg");
    super.new(name, 32, UVM_NO_COVERAGE);
  endfunction
  virtual function void build();
    ADDR = uvm_reg_field::type_id::create("ADDR");
    ADDR.configure(this, 32, 0, "RO", 1, 32'h0, 1, 0, 1);
  endfunction
endclass
```

### 코드 — 시퀀스 레벨 fault injection (RTL force ❌)

```systemverilog
class ras_inject_seq extends uvm_reg_sequence;
  `uvm_object_utils(ras_inject_seq)
  ras_reg_model model;

  virtual task body();
    uvm_status_e   status;
    uvm_reg_data_t rdata;

    // ① inject 레지스터 프로그래밍 — DUT가 제공하는 inject 경로 사용
    //    (RTL 신호를 force 하지 않는다)
    model.ERRCTLR.write(status, 32'h1 /*UE inject enable*/, .parent(this));

    // ② 에러를 트리거할 접근 발생 (예: 해당 주소 read)
    model.DATA_AT_A.read(status, rdata, .parent(this));

    // ③ error record 읽어 기대값과 비교 (scoreboard가 판정)
    model.ERRSTATUS.read(status, rdata, .parent(this));
    if (model.ERRSTATUS.UE.get_mirrored_value() != 1'b1)
      `uvm_error("RAS", "UE not recorded after injection")

    // ④ W1C clear: STATUS에 set 비트를 1로 write → clear
    model.ERRSTATUS.write(status, 32'h7 /*V|CE|UE*/, .parent(this));
  endtask
endclass
```

:::caution[왜 RTL force가 아니라 시퀀스인가]
`force tb_top.dut.u_cache.ecc_err = 1` 은 _특정 RTL 신호명·계층_ 에 결합됩니다. RTL 리비전에서 신호명이 바뀌거나 모듈이 재구성되면 테스트가 조용히 깨지고, 다른 블록·다른 프로젝트로 옮길 수 없습니다. 반면 DUT가 제공하는 inject 레지스터를 RAL 시퀀스로 쓰면 — 버스 추상화 위에서 동작하므로 재사용·이식이 되고, "이 테스트가 무엇을 주입하는지"가 코드에 드러납니다. (프로젝트 규칙: 에러 주입은 시퀀스 레벨에서만, RTL 수정 금지.)
:::
---

## 4. 일반화 — error record / 인터럽트 / 주입 전략

### 4.1 RAS-node error record 레지스터 (Arm `ERR<n>` 계열)

| 레지스터(계열) | 역할 | 전형적 access |
|----------------|------|---------------|
| `ERR<n>STATUS` | 에러 type(CE/UE/DE), valid, overflow 등 상태 | W1C (1 write로 clear) |
| `ERR<n>ADDR` | failing address 캡처 | RO |
| `ERR<n>CTLR` | error 검출/인터럽트 enable, **fault injection enable** | RW |
| `ERR<n>FR` | feature register — 어떤 기능을 지원하는지 | RO |
| `ERR<n>MISC` | 추가 진단 정보(timestamp 등) | RO/W1C |

> 정확한 비트 필드·인코딩은 Arm® RAS System Architecture 사양에서 재확인이 필요합니다(HDG 스펙 주석에 명시). 위 표는 아키텍처 수준의 일반 형태입니다(추론).

### 4.2 인터럽트 / telemetry 경로

에러 기록이 valid가 되면 RAS-node는 비동기 인터럽트를 외부 **SCP**(System Control Processor)나 **BMC**(Baseboard Management Controller)로 올립니다. 운영자/펌웨어는 이 telemetry로 어느 FRU가 문제인지 진단합니다. 검증에서는 (1) 인터럽트가 _올라가는가_, (2) record clear(W1C) 후 _내려가는가_, (3) enable이 꺼져 있으면 안 올라가는가를 자극합니다.

### 4.3 주입 시나리오 매트릭스

| 주입 type | 기대 기록 | 기대 후속 |
|-----------|----------|-----------|
| CE 1회 | `STATUS.CE=1`, addr 캡처 | 정정 후 동작 계속, IRQ(임계 시) |
| CE 반복(임계 초과) | CE 카운터 누적 | threshold 보고/IRQ |
| UE 1회 | `STATUS.UE=1`, addr 캡처 | poison/exception, IRQ |
| record 미clear 상태 추가 UE | overflow 비트 | 다중 에러 처리 정책 확인 |
| inject disable 상태 접근 | 기록 없음 | 음성 케이스(오검출 없어야) |

### 4.4 Coverage 관점

fault injection 검증은 covergroup으로 "어떤 에러 type × 어떤 위치 × clear 여부"의 조합을 추적해야 합니다. 단일 type만 100%여도 CE→UE 악화, overflow, clear-after-inject 같은 조합이 빠지면 RAS 로직의 코너가 미검증으로 남습니다.

---

## 5. 디테일 — W1C, overflow, scoreboard, 음성 케이스

### 5.1 W1C 와 RAL update 의 함정

error record의 status 비트는 보통 **W1C(write-1-to-clear)** 입니다. 즉 1을 써야 _clear_ 됩니다. 여기서 RAL의 `update()`를 쓰면 함정에 빠집니다 — desired==mirror면 write를 생략하기 때문입니다. clear는 "같은 비트에 1을 다시 써야 의미"가 있으므로, `update` 대신 명시적 `write`를 써야 합니다. (이 함정은 [UVM M07 RAL](../../uvm/07_register_layer_ral/)의 update 주의와 동일한 패턴입니다.)

### 5.2 Overflow — 다중 에러

첫 에러가 clear되기 전에 두 번째 에러가 나면, 보통 record는 첫 에러를 보존하고 overflow 비트를 set합니다(추론: 일반 RAS 동작). 검증에서는 "미clear 상태에서 추가 주입 시 overflow가 set되고 첫 record가 덮어쓰이지 않는가"를 자극합니다.

### 5.3 Scoreboard — 기대 record 예측

inject 시퀀스가 _무엇을_ 주입했는지(type, addr)를 reference로 두고, monitor가 관찰한 record(또는 RAL mirror)와 비교합니다. explicit prediction을 쓰면 monitor→predictor로 mirror가 갱신되므로, scoreboard는 mirror와 기대값을 비교할 수 있습니다. 핵심 비교 대상은 type(CE/UE), failing address, valid/overflow입니다.

```systemverilog
// 주입 기대값을 reference로 만들어 scoreboard에 등록 (개념)
class ras_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(ras_scoreboard)
  // inject 시퀀스가 push: 기대 (type, addr)
  err_record_t expected_q[$];

  function void add_expected(err_record_t e);
    expected_q.push_back(e);
  endfunction

  // monitor가 관찰한 record write
  function void write(err_record_t actual);
    err_record_t exp;
    if (expected_q.size() == 0) begin
      `uvm_error("RAS_SB", "Unexpected error record (오검출?)")  // 음성 케이스
      return;
    end
    exp = expected_q.pop_front();
    if (actual.etype != exp.etype || actual.addr != exp.addr)
      `uvm_error("RAS_SB", $sformatf("Mismatch exp(type=%0d,addr=%h) act(type=%0d,addr=%h)",
                 exp.etype, exp.addr, actual.etype, actual.addr))
  endfunction

  // 미clear/누락 검출
  function void check_phase(uvm_phase phase);
    if (expected_q.size() > 0)
      `uvm_error("RAS_SB", $sformatf("%0d injected errors not recorded", expected_q.size()))
  endfunction
endclass
```

### 5.4 음성 케이스 — 주입 안 했는데 에러 보고?

가장 중요한 음성 케이스는 "inject가 disable인데 정상 접근에서 에러가 기록되는가"입니다. RAS 로직이 정상 트래픽을 _오검출_ 하면 false alarm으로 가용성을 해칩니다. scoreboard의 "Unexpected error record" 분기가 이를 잡습니다. poison의 음성 케이스(소비 안 하면 무사)는 [M02](../02_ecc_parity_poison/)와 연결됩니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '에러 주입은 RTL 신호를 force하면 된다']
**실제**: RTL force는 특정 신호명·계층에 결합되어 리비전마다 깨지고 재사용이 안 됩니다. 정석은 DUT가 제공하는 **inject 레지스터를 시퀀스 레벨**로 프로그래밍하는 것입니다. 스펙도 fault injection을 "레지스터 프로그래밍으로 가짜 에러 주입"으로 정의합니다.<br>
**왜 헷갈리는가**: force가 빠르고 직관적으로 보여서 — 그러나 검증 자산이 되지 못합니다.
:::
:::danger[❓ 오해 2 — 'error record를 read하면 clear된다']
**실제**: status 비트는 보통 **W1C** — read가 아니라 _1을 write_ 해야 clear됩니다. read는 값만 가져옵니다. RAL `update()`로 clear를 시도하면 desired==mirror일 때 write가 생략되어 clear가 안 될 수 있으니, 명시적 `write`로 1을 써야 합니다.<br>
**왜 헷갈리는가**: clear-on-read 레지스터와 혼동해서.
:::
:::danger[❓ 오해 3 — 'CE는 동작에 지장 없으니 검증 안 해도 된다']
**실제**: CE는 정정되지만, _반복되면_ permanent fault의 전조이고 임계 초과 시 보고/인터럽트가 트리거되어야 합니다. CE 카운터·threshold·보고 경로는 RAS 검증의 정식 대상입니다.<br>
**왜 헷갈리는가**: "정정됨 = 문제없음"이라는 인상 때문에.
:::
:::danger[❓ 오해 4 — '인터럽트가 올라가는 것만 보면 된다']
**실제**: clear(W1C) 후 인터럽트가 _내려가는지_, enable이 꺼졌을 때 _안 올라가는지_ 도 검증해야 합니다. raise만 보면 stuck interrupt나 mask 미동작을 놓칩니다.<br>
**왜 헷갈리는가**: "에러=인터럽트 발생"이라는 단순 모델 때문에.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| inject했는데 record 없음 | inject enable 미설정 또는 트리거 접근 누락 | `ERR<n>CTLR` inject 비트, 트리거 시퀀스 |
| record는 맞는데 addr가 틀림 | failing address 캡처 로직 또는 정렬 | `ERR<n>ADDR` 캡처, 주소 mask |
| W1C write 후에도 안 clear됨 | RAL `update` 사용(생략됨) 또는 access policy 오설정 | 명시적 `write` 사용, field access=W1C |
| 인터럽트가 안 내려감 | clear 후 IRQ deassert 로직 | record clear↔IRQ 연동 |
| 정상 트래픽에서 에러 기록(오검출) | RAS 검출 로직 false positive | inject disable 상태 음성 케이스 |
| 다중 주입 시 첫 record 덮어씀 | overflow 처리 미동작 | overflow 비트, record 보존 정책 |
| mirror가 record와 어긋남 | explicit prediction `set_auto_predict(0)` 누락 | predictor 연결 + auto_predict off |

---

## 7. 핵심 정리 (Key Takeaways)

- **RAS-node = 블랙박스 + 비상벨**: `ERR<n>STATUS`(type/valid, W1C), `ERR<n>ADDR`(failing addr, RO), `ERR<n>CTLR`(enable + inject)로 에러를 기록하고 SCP/BMC로 인터럽트.
- **Fault injection은 시퀀스 레벨**: DUT의 inject 레지스터를 RAL 시퀀스로 프로그래밍 — RTL force는 결합·비재사용으로 안티패턴(프로젝트 규칙).
- **검증 흐름**: 주입(시퀀스) → 검출/기록(DUT) → record 비교(scoreboard) → 인터럽트 관찰(monitor) → W1C clear(시퀀스).
- **W1C 함정**: status clear는 1을 write — RAL `update`는 같은 값이면 생략하므로 명시적 `write` 사용.
- **음성 케이스 필수**: inject disable 시 오검출 없음, clear 후 IRQ deassert, poison 비소비 시 무사 — raise/검출만 보면 escape.
- **Coverage**: error type × 위치 × clear/overflow 조합을 추적해 RAS 로직의 코너까지 닫음.

:::caution[실무 주의점]
- 에러 주입은 **시퀀스 레벨에서만** — DUT RTL을 force/수정하지 말 것.
- explicit prediction이면 `set_auto_predict(0)` 필수(mirror 이중 갱신 방지) — [UVM M07](../../uvm/07_register_layer_ral/) 참고.
- W1C status는 명시적 `write(1)`로 clear — `update` 사용 금지.
- 인터럽트는 raise + deassert + mask 셋을 모두 자극.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — RTL force vs 시퀀스 주입 (Bloom: Evaluate)]
동료가 `force dut.u_mem.ecc_err = 1;` 으로 ECC 에러를 주입해 테스트를 통과시켰다. 이 접근의 문제를 검증 자산 관점에서 평가하라.
<details>
<summary>정답</summary>

문제는 **재사용성·이식성·가독성**입니다. (1) `dut.u_mem.ecc_err`는 특정 RTL 계층·신호명에 결합되어, 설계자가 모듈을 재구성하거나 신호명을 바꾸면 테스트가 _조용히_ 깨집니다. (2) 다른 블록이나 다른 프로젝트로 옮길 수 없습니다 — RAS 메커니즘은 비슷해도 RTL 경로가 다르기 때문입니다. (3) 검토자가 "이 테스트가 무엇을·왜 주입하는지"를 신호 force만 보고 알기 어렵습니다. 정석은 DUT가 제공하는 **inject 레지스터를 RAL 시퀀스로** 프로그래밍하는 것입니다 — 버스 추상화 위에서 동작해 재사용·이식이 되고, 스펙이 정의한 fault injection 경로(레지스터 프로그래밍)를 그대로 검증합니다. 또한 프로젝트 규칙상 에러 주입은 시퀀스 레벨에서만 허용되고 RTL 수정은 금지입니다.

</details>
:::
:::tip[🤔 Q2 — W1C clear와 RAL update (Bloom: Apply)]
`ERRSTATUS.UE`가 W1C로 set되어 있다. RAL `update()`로 clear를 시도했더니 인터럽트가 안 내려간다. 원인과 수정은?
<details>
<summary>정답</summary>

원인은 **`update()`의 생략 동작**입니다. `update()`는 desired ≠ mirror일 때만 버스 write를 발생시킵니다. W1C 비트를 clear하려면 1을 _써야_ 하는데, mirror가 이미 그 상태와 같다고 판단되면(또는 desired를 set하지 않았으면) write가 생략되어 실제 버스 트랜잭션이 안 나가고, 따라서 HW의 W1C clear가 일어나지 않아 인터럽트가 그대로 떠 있습니다. 수정: `update` 대신 **명시적 `write`** 로 clear할 비트에 1을 직접 씁니다 — 예: `model.ERRSTATUS.write(status, 32'h4 /*UE 비트*/, .parent(this));`. W1C처럼 "같은 값을 다시 써야 의미가 있는" 레지스터에서는 항상 명시적 write를 사용합니다.

</details>
:::
### 7.2 출처

**Internal (HDG)**
- `wiki/common/ras_spec.md` — §2 (3) Serviceability: Error Recording & Telemetry(`ERR<n>STATUS` 아키텍처, SCP/BMC 인터럽트), Fault Injection Model(레지스터 프로그래밍으로 runtime 가짜 에러 주입)
- 프로젝트 규칙: 에러 주입은 시퀀스 레벨에서만, RTL 수정 금지

**External**
- Arm® *RAS System Architecture* — `ERR<n>STATUS`/`ERR<n>ADDR`/`ERR<n>CTLR` 레지스터 (정확한 비트 필드는 사양 재확인 필요)
- *UVM 1.2 User's Guide* §5 (Register Abstraction) — RAL register model, W1C, explicit prediction

---

## 다음 모듈

이 코스의 마지막 모듈입니다. 학습한 내용을 정리하려면 [용어집](../glossary/)에서 핵심 용어(CE/UE/poison/SEC-DED/RAS-node/fault injection)를 다시 확인하고, [퀴즈](../quiz/)로 전체 이해도를 점검하세요. RAS 검증을 실제 UVM 환경에 얹는 방법은 [UVM 코스의 RAL](../../uvm/07_register_layer_ral/)과 [TLM/Scoreboard](../../uvm/05_tlm_scoreboard_coverage/)에서 이어집니다.

[퀴즈 풀어보기 →](../quiz/03_ras_node_fault_injection_quiz/)
