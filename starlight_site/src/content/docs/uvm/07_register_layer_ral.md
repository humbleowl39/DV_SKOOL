---
title: "Module 07 — Register Layer (RAL)"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** RAL 이 해결하는 문제(주소 하드코딩, 재사용성, mirror 추적)와 frontdoor / backdoor 의 차이를 설명할 수 있다.
- **Differentiate** `read/write`, `peek/poke`, `get/set`, `update`, `mirror` 다섯 가지 접근 API 가 DUT 를 건드리는지·mirror 를 어떻게 바꾸는지 구분할 수 있다.
- **Trace** mirrored value 와 desired value 가 `set → update`, `read`, `mirror` 흐름에서 각각 어떻게 갱신되는지 추적할 수 있다.
- **Implement** `uvm_reg_adapter` (reg2bus / bus2reg) 와 env 의 시퀀서·predictor 연결을 작성할 수 있다.
- **Evaluate** implicit prediction 과 explicit prediction 중 어느 것을 써야 하는지, `set_auto_predict` 설정을 근거 있게 판단할 수 있다.
- **Design** field/register/block 계층을 가진 register model 의 `build`/`configure`/`map` 구조를 설계할 수 있다.
:::
:::note[사전 지식]
- [Module 01-06](../01_architecture_and_phase/) — 특히 [M04 config_db & Factory](../04_config_db_factory/), [M03 Sequence](../03_sequence_and_item/)
- 레지스터/메모리-맵 IO 의 기본 개념 (offset, access policy RW/RO/W1C 등)
- 버스 프로토콜 트랜잭션 1 개의 구조 (addr, data, kind) — 예: APB/AHB/AXI-Lite
:::
---

## 1. Why care? — 주소를 외우는 순간 테스트는 깨진다

### 1.1 시나리오 — 레지스터 맵이 한 칸 밀렸다

CSR(Control/Status Register) 블록을 검증하는 시퀀스를 이렇게 짰다고 합시다.

```systemverilog
// 주소를 직접 박은 시퀀스 — 안티패턴
apb_write(16'h0040, 32'h1);   // CTRL.enable
apb_write(16'h0044, 32'hFF);  // THRESHOLD
apb_read (16'h0048, rdata);   // STATUS
```

다음 RTL 리비전에서 설계자가 `CTRL` 앞에 레지스터 하나를 추가해 모든 오프셋이 `0x4` 씩 밀렸습니다. 시퀀스는 컴파일도 잘 되고 시뮬도 PASS 처럼 보이지만, 실제로는 엉뚱한 주소를 두드리고 있습니다. 수백 개 레지스터를 쓰는 환경이라면 이 한 줄짜리 변경이 수백 줄의 silent 오동작으로 번집니다.

RAL(Register Abstraction Layer)은 이 문제를 **이름으로 접근**해서 없앱니다.

```systemverilog
// RAL — 이름으로 접근. 주소가 바뀌어도 시퀀스는 그대로
regmodel.CTRL.ENABLE.write(status, 1'b1, .parent(this));
regmodel.THRESHOLD.write(status, 32'hFF, .parent(this));
regmodel.STATUS.read(status, rdata, .parent(this));
```

오프셋이 밀려도 고치는 곳은 register model 의 `map()` 안 오프셋 값 _한 군데_ 뿐입니다. 시퀀스 코드는 한 줄도 바뀌지 않습니다.

### 1.2 RAL 이 주는 네 가지

| 가치 | 의미 |
|------|------|
| **추상화** | 주소가 바뀌어도 이름으로 접근하니 테스트 코드 불변 |
| **재사용성** | 블록 레벨에서 짠 레지스터 테스트를 시스템 레벨에서 그대로 재활용 |
| **Front/Back-door** | 실제 버스를 타는 방식과 시뮬레이터 신호 직접 접근을 모두 지원 → 속도 ↔ 정확도 선택 |
| **자동화** | 레지스터가 수천 개일 수 있으므로 IP-XACT / 스프레드시트에서 generator 로 모델 생성 |

이 모듈을 건너뛰면 CSR 검증 환경은 _주소에 결합된_ 깨지기 쉬운 코드가 되고, mirror 개념이 없어 "DUT 가 지금 무슨 값을 들고 있어야 하는가"를 TB 가 스스로 알지 못합니다.

> **Source.** 이 모듈의 클래스/메서드 정의는 *UVM 1.2 User's Guide* §5 (Register Abstraction) 및 사내 Confluence "[UVM Basics] Using the Register Layer Classes" 를 근거로 합니다.

---

## 2. Intuition — 미러(mirror), 그리고 두 개의 문

:::tip[💡 한 줄 비유]
**Register model** ≈ **DUT 레지스터의 거울(mirror)**.<br>
TB 는 DUT 안을 직접 못 보므로, 자기가 한 read/write 로 _"DUT 가 지금 이 값일 것"_ 이라고 **추측한 사본**을 들고 있습니다. 이 추측값이 mirror 입니다. 거울이므로 — DUT 가 _스스로_(카운터 증가, 상태 비트 set) 값을 바꾸면 거울은 그 사실을 모릅니다. 그래서 가끔 `mirror()` 로 거울을 닦아(DUT 를 다시 읽어) 줘야 합니다.
:::

RAL 에는 **두 개의 문(door)** 이 있습니다.

- **Front-door**: 실제 버스 트랜잭션을 발생시킵니다(드라이버 → DUT 핀). 느리지만 실제 경로를 검증합니다.
- **Back-door**: 버스를 우회해 시뮬레이터의 HDL 계층 경로(`tb_top.dut.u_csr.ctrl_reg`)에 직접 접근합니다. Zero-time 이며 빠르지만 버스 로직은 검증하지 않습니다.

### 한 장 그림 — RAL 이 버스 위에 얹히는 구조

```d2
direction: right

SEQ: "**Register Sequence**\nregmodel.CTRL.write(...)\n(이름 기반, 버스 무관)"
MODEL: "**Register Model**\nblock / reg / field 계층\nmirror + desired 값 보관"
ADAPTER: "**uvm_reg_adapter**\nreg2bus / bus2reg\n(추상 ↔ 버스 변환)"
SEQR: "Bus Sequencer\n(APB/AHB/AXI)"
DRV: "Driver"
DUT: "**DUT**\n물리 레지스터"
PRED: "**uvm_reg_predictor**\n(explicit prediction)"
MON: "Bus Monitor"

SEQ -> MODEL: "frontdoor 호출"
MODEL -> ADAPTER: "uvm_reg_bus_op"
ADAPTER -> SEQR: "bus item"
SEQR -> DRV
DRV -> DUT: "물리 read/write"
DUT -> MON: "관찰"
MON -> PRED: "bus item"
PRED -> MODEL: "predict() → mirror 갱신" { style.stroke-dash: 4 }
MODEL -> DUT: "**back-door**\nHDL path 직접 접근" { style.stroke-dash: 2; style.stroke: "#c0392b" }
```

### 왜 이 구조인가 — Design rationale

세 가지 요구의 교집합입니다.

1. **시퀀스는 버스 종류를 몰라야 한다** → register model 은 추상 동작(`write`)만 내고, `uvm_reg_adapter` 가 APB/AHB/AXI 트랜잭션으로 번역. 버스를 바꿔도 시퀀스 불변.
2. **TB 는 DUT 의 현재 값을 알아야 한다** → mirror. 그리고 제3의 마스터가 만든 버스 트랜잭션까지 반영하려면 monitor + `uvm_reg_predictor`(explicit prediction).
3. **빠른 초기화/검사가 필요하다** → back-door(zero-time)로 reset 값 확인이나 대량 설정을 버스 사이클 없이 수행.

---

## 3. 작은 예 — `set → update` 한 번이 DUT 에 닿기까지

가장 헷갈리는 지점이 **mirrored value** 와 **desired value** 의 분리입니다. 작은 시나리오로 흐름을 봅시다: 모델 안에서 원하는 값을 정해두고(`set`), 실제와 다를 때만 버스에 쓴다(`update`).

### 단계별 다이어그램

```d2
direction: down

S1: "**① set(0xAB)**\ndesired = 0xAB\nmirror 는 그대로 (예: 0x00)\nDUT 접근 없음 (zero-time)"
S2: "**② update()**\ndesired(0xAB) ≠ mirror(0x00)?\n→ 다르므로 write 발생"
S3: "**③ frontdoor write(0xAB)**\nadapter → bus → DUT\n물리 트랜잭션 실행"
S4: "**④ mirror = 0xAB**\n관찰된 결과로 mirror 갱신\n이제 desired == mirror"
S1 -> S2 -> S3 -> S4
```

### 단계별 의미

| Step | API | DUT 접근 | mirror | desired | 핵심 |
|------|-----|---------|--------|---------|------|
| ① | `set(0xAB)` | ❌ | 0x00 (불변) | 0xAB | 모델 내부 의도만 수정. 매우 빠름 |
| ② | `update()` | 조건부 | — | — | desired ≠ mirror 일 때만 write |
| ③ | (내부 `write`) | ✅ frontdoor | — | — | 실제 버스 사이클 |
| ④ | (write 완료) | — | 0xAB | 0xAB | 관찰 결과로 mirror 동기화 |

:::caution[update 의 함정 — "이미 같으면 안 쓴다"]
`update()` 는 desired == mirror 면 **버스 트랜잭션을 생략**해 시뮬레이션 시간을 아낍니다. 하지만 _0 을 write 하고 싶은데 mirror 가 이미 0_ 이면 write 가 일어나지 않습니다. W1C(write-1-to-clear)처럼 "같은 값을 다시 써야 의미가 있는" 레지스터에서는 `update` 대신 명시적 `write` 를 쓰세요.
:::

### 다섯 가지 접근 API 한눈에

| API | DUT 접근 | 경로 | mirror 갱신 | 용도 |
|-----|---------|------|-------------|------|
| `read` / `write` | **YES** | Front/Back | 갱신 | 가장 표준. 버스 트랜잭션 실행 |
| `peek` / `poke` | **YES** | Back-door | 갱신 | 인터페이스 우회, 강제 주입/추출 (side-effect 흉내 ❌) |
| `get` / `set` | **NO** | — | desired 만 | 모델 내부 값만. zero-time |
| `update` | 조건부 | Front/Back | 갱신 | desired ≠ mirror 일 때만 write |
| `mirror` | **YES** | Front/Back | 갱신+비교 | DUT 값을 읽어와 mirror 갱신 / 검증 |

핵심 구분: **`peek/poke` 는 side-effect 를 흉내내지 않고 값을 강제**하지만, **back-door `read/write` 는 front-door 와 같은 효과를 흉내**냅니다. 예를 들어 clear-on-read 필드를 back-door `read` 하면 읽은 뒤 0 을 다시 써서 클리어까지 재현하지만, `peek` 은 값만 가져오고 클리어하지 않습니다.

---

## 4. 일반화 — mirror / prediction / 모델 계층

### 4.1 Mirror 가 틀어지는 경우와 대응

mirror 는 _TB 가 한 접근_ 만 알기 때문에, DUT 내부 동작으로 값이 바뀌면 어긋납니다.

| 상황 | mirror 정확? | 대응 |
|------|:---:|------|
| TB 가 write 후 다시 read | ✅ | 자동 갱신 |
| DUT 가 status bit 를 스스로 set | ❌ | `mirror()` 로 다시 읽기 |
| 제3의 버스 마스터가 write | ❌ (implicit 시) | **explicit prediction** (predictor) |
| 메모리(`uvm_mem`) | mirror 없음 | `peek`/`poke` 로 직접 접근 |

> 메모리는 용량 때문에 mirror 를 두지 않습니다(`uvm_mem` 은 mirrored 되지 않음). 항상 `peek`/`poke` 로 실제 값을 직접 다룹니다.

### 4.2 Prediction 세 가지 통합 방식

mirror 를 _누가_ 갱신하느냐에 따라 세 가지 통합 구조가 있습니다.

```d2
direction: down

IMP: "**1. Implicit Prediction**\n모델 ↔ 시퀀서만 연결\n모델이 한 read/write 직후 스스로 mirror 갱신\n→ 가장 단순, 제3 마스터 관찰 불가"
EXP: "**2. Explicit Prediction** (권장)\n모델 ↔ 시퀀서 + 모니터 + predictor\nset_auto_predict(0)\n→ 모든 버스 트랜잭션 관찰, 정확"
PAS: "**3. Passive Integration**\n모델 ↔ 모니터만\n모델로 직접 read/write 불가\n→ 추적·검증 전용"
```

| 방식 | 연결 | `set_auto_predict` | 언제 |
|------|------|:---:|------|
| Implicit | 시퀀서만 | 1 (on) | 모델만이 유일한 버스 마스터일 때 |
| **Explicit** | 시퀀서 + 모니터 + predictor | **0 (off)** | 다른 마스터도 레지스터를 건드릴 때 (표준 권장) |
| Passive | 모니터만 | 0 | DUT 상태 추적/검증 전용 |

:::danger[explicit 인데 auto_predict 를 안 끄면]
explicit prediction 을 쓰면서 `set_auto_predict(0)` 을 호출하지 않으면, 모델이 _스스로도_ 갱신하고 predictor 도 갱신해 **mirror 가 두 번 업데이트**되어 꼬입니다. explicit 의 필수 짝은 `regmodel.MAP.set_auto_predict(0)` 입니다.
:::

### 4.3 모델 계층 — block ⊃ regfile ⊃ reg ⊃ field

```d2
direction: down
BLK: "uvm_reg_block\n(주소 맵 보유)"
RF: "uvm_reg_file\n(논리적 그룹, 선택)"
REG: "uvm_reg\n(주소 1개 = 레지스터)"
FLD: "uvm_reg_field\n(비트 슬라이스 + access policy)"
MEM: "uvm_mem\n(주소 공간, mirror 없음)"
BLK -> RF
BLK -> MEM
RF -> REG
REG -> FLD
```

- **field**: `configure(parent, size, lsb, access, ...)` 로 비트 위치·access policy(RW/RO/W1C…) 지정.
- **reg**: 필드들을 `build()` 에서 생성, public 속성으로 노출(이름은 base 클래스 충돌 방지 위해 권장상 대문자).
- **block**: `create_map()` 으로 주소 맵 생성, `add_reg(reg, offset, access)` 로 등록. 하위 블록은 `add_submap()`.

---

## 5. 디테일 — adapter / 통합 / 모델 구축 코드

### 5.1 uvm_reg_adapter — 추상 동작 ↔ 버스 트랜잭션 변환

RAL 의 추상 동작(`uvm_reg_bus_op`)을 프로젝트의 버스 트랜잭션으로 옮기는 두 함수만 구현하면 됩니다.

```systemverilog
class reg2apb_adapter extends uvm_reg_adapter;
  `uvm_object_utils(reg2apb_adapter)

  function new(string name = "reg2apb_adapter");
    super.new(name);
    supports_byte_enables = 0;  // APB 는 보통 byte-enable 없음
    provides_responses    = 1;  // 드라이버가 응답을 별도로 반환하면 1
  endfunction

  // 모델 → 버스 (write/read 를 APB 아이템으로)
  virtual function uvm_sequence_item reg2bus(const ref uvm_reg_bus_op rw);
    apb_rw apb = apb_rw::type_id::create("apb_rw");
    apb.kind = (rw.kind == UVM_READ) ? apb_rw::READ : apb_rw::WRITE;
    apb.addr = rw.addr;
    apb.data = rw.data;
    return apb;
  endfunction

  // 버스 → 모델 (관찰된 APB 아이템을 추상 동작으로)
  virtual function void bus2reg(uvm_sequence_item bus_item, ref uvm_reg_bus_op rw);
    apb_rw apb;
    if (!$cast(apb, bus_item)) begin
      `uvm_fatal("NOT_APB", "bus_item 이 APB 타입이 아닙니다")
      return;
    end
    rw.kind   = (apb.kind == apb_rw::READ) ? UVM_READ : UVM_WRITE;
    rw.addr   = apb.addr;
    rw.data   = apb.data;
    rw.status = UVM_IS_OK;
  endfunction
endclass
```

:::note[supports_byte_enables 가 개별 필드 접근을 가른다]
한 레지스터 안의 _특정 필드만_ write 하려 할 때, 버스가 byte-enable 을 지원하면(`supports_byte_enables=1`) 해당 바이트 레인만 접근합니다. 아니면 레지스터 _전체_ 를 read-modify-write 하므로, 같은 레지스터의 다른 필드에 의도치 않은 side-effect 가 생길 수 있습니다.
:::

### 5.2 env 통합 — implicit (시퀀서만)

```systemverilog
class block_env extends uvm_env;
  block_reg_model regmodel;
  apb_agent       apb;

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (regmodel == null) begin
      regmodel = block_reg_model::type_id::create("regmodel");
      regmodel.build();
      regmodel.lock_model();                       // 구성 완료 후 잠금
      regmodel.set_hdl_path_root("tb_top.dut");    // back-door 용 루트 경로
    end
    apb = apb_agent::type_id::create("apb", this);
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    if (regmodel.get_parent() == null) begin
      reg2apb_adapter reg2apb = reg2apb_adapter::type_id::create("reg2apb");
      regmodel.default_map.set_sequencer(apb.sequencer, reg2apb);
      regmodel.default_map.set_auto_predict(1);    // implicit
    end
  endfunction
endclass
```

### 5.3 env 통합 — explicit (시퀀서 + 모니터 + predictor)

```systemverilog
class block_env extends uvm_env;
  block_reg_model            regmodel;
  apb_agent                  apb;
  uvm_reg_predictor #(apb_rw) apb2reg_predictor;

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    // ... regmodel 생성/build/lock 동일 ...
    apb2reg_predictor = uvm_reg_predictor#(apb_rw)::type_id::create("apb2reg_predictor", this);
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    if (regmodel.get_parent() == null) begin
      reg2apb_adapter reg2apb = reg2apb_adapter::type_id::create("reg2apb");
      regmodel.default_map.set_sequencer(apb.sequencer, reg2apb);

      apb2reg_predictor.map     = regmodel.default_map;
      apb2reg_predictor.adapter = reg2apb;
      regmodel.default_map.set_auto_predict(0);    // ★ 중복 갱신 방지
    end
    // 모니터 → predictor
    apb.monitor.ap.connect(apb2reg_predictor.bus_in);
  endfunction
endclass
```

### 5.4 register model 구축 (generator 가 만드는 코드의 형태)

```systemverilog
// 레지스터 타입: CTRL
class ctrl_reg extends uvm_reg;
  `uvm_object_utils(ctrl_reg)
  rand uvm_reg_field ENABLE;
  rand uvm_reg_field MODE;

  function new(string name = "ctrl_reg");
    super.new(name, 32, UVM_NO_COVERAGE);   // n_bits=32
  endfunction

  virtual function void build();
    ENABLE = uvm_reg_field::type_id::create("ENABLE");
    MODE   = uvm_reg_field::type_id::create("MODE");
    // configure(parent, size, lsb_pos, access, volatile, reset, has_reset, is_rand, individually_accessible)
    ENABLE.configure(this, 1, 0, "RW", 0, 1'h0, 1, 1, 1);
    MODE.configure  (this, 2, 1, "RW", 0, 2'h0, 1, 1, 0);
  endfunction
endclass

// 블록 타입
class block_reg_model extends uvm_reg_block;
  `uvm_object_utils(block_reg_model)
  rand ctrl_reg CTRL;

  function new(string name = "block_reg_model");
    super.new(name, UVM_NO_COVERAGE);
  endfunction

  virtual function void build();
    default_map = create_map("default_map", 'h0, 4, UVM_LITTLE_ENDIAN);
    CTRL = ctrl_reg::type_id::create("CTRL");
    CTRL.configure(this, null, "u_csr.ctrl_reg");   // contxt=this, hdl path
    CTRL.build();
    default_map.add_reg(CTRL, 'h40, "RW");          // 오프셋 0x40 — 여기만 고치면 됨
  endfunction
endclass
```

### 5.5 레지스터 시퀀스와 내장 시퀀스

```systemverilog
class my_reg_sequence extends uvm_reg_sequence;
  `uvm_object_utils(my_reg_sequence)
  block_reg_model model;

  virtual task body();
    uvm_status_e   status;
    uvm_reg_data_t data;
    model.CTRL.write(status, 32'h1, .parent(this));
    model.CTRL.read (status, data,  .parent(this));
    if (data != 32'h1) `uvm_error("RAL", "Readback mismatch")
  endtask
endclass
```

UVM 라이브러리는 모델만 통합되면 바로 돌릴 수 있는 **내장 검증 시퀀스**를 제공합니다 — `uvm_reg_hw_reset_seq`(reset 값 확인), `uvm_reg_bit_bash_seq`(각 비트 RW 토글), `uvm_reg_access_seq`(frontdoor/backdoor 일치), `uvm_mem_walk_seq`(메모리 walking-1). 새 CSR 블록의 _smoke test_ 로 가장 먼저 돌리는 것들입니다.

### 5.6 특수 레지스터 (개념 요약)

| 종류 | 클래스/기법 | 한 줄 설명 |
|------|------------|-----------|
| Indirect/Indexed | `uvm_reg_indirect_data` | index 레지스터에 오프셋 쓰고 data 레지스터로 접근 |
| FIFO | `uvm_reg_fifo` | 같은 주소 write=push / read=pop |
| Aliased | callback (`post_predict`) | 한 레지스터가 여러 주소에서 보임 → mirror 동기화 |
| Unimplemented | user front-door | spec 엔 있으나 RTL 미구현 — 모델만 응답 |
| Indexed array | user `uvm_reg_frontdoor` | 주소 없는 레지스터 배열을 index 경유 접근 |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'mirror 값은 항상 DUT 의 실제 값이다']
**실제**: mirror 는 _TB 가 수행/관찰한 접근_ 으로 추측한 값일 뿐입니다. DUT 가 내부 동작으로 status bit 를 set 하거나 카운터를 증가시키면 mirror 는 모릅니다. 정확한 현재 값이 필요하면 `mirror()`(frontdoor read) 또는 `peek()`(backdoor)로 다시 읽어야 합니다.<br>
**왜 헷갈리는가**: "모델이 DUT 를 안다" 는 인상 때문에 — 실제로는 _자기가 본 것만_ 압니다.
:::
:::danger[❓ 오해 2 — 'update() 는 항상 write 를 발생시킨다']
**실제**: `update()` 는 desired ≠ mirror 일 때만 write 합니다. 같으면 버스 트랜잭션을 생략합니다. 0 을 쓰려는데 이미 0 이면 아무 일도 안 일어나, W1C 같은 레지스터에서 의도와 어긋납니다.<br>
**왜 헷갈리는가**: 이름이 "update" 라 무조건 반영할 것 같아서.
:::
:::danger[❓ 오해 3 — 'explicit prediction 을 켜면 set_auto_predict 는 신경 안 써도 된다']
**실제**: predictor 를 연결했어도 `set_auto_predict(0)` 을 안 부르면 모델이 _스스로도_ mirror 를 갱신해 **이중 갱신**으로 꼬입니다. explicit 의 필수 짝은 auto_predict OFF.<br>
**왜 헷갈리는가**: predictor 만 추가하면 완성이라고 생각해서.
:::
:::danger[❓ 오해 4 — 'peek/poke 와 backdoor read/write 는 같다']
**실제**: 둘 다 버스를 우회하지만, **backdoor read/write 는 frontdoor 의 side-effect 를 흉내**(clear-on-read 재현 등)하고 **peek/poke 는 값을 그대로 강제**(흉내 없음)합니다. clear-on-read 필드를 디버그로 _건드리지 않고_ 보고 싶으면 `peek`.<br>
**왜 헷갈리는가**: 둘 다 "backdoor" 라 동일해 보여서.
:::
:::danger[❓ 오해 5 — '메모리도 mirror 로 값을 비교하면 된다']
**실제**: `uvm_mem` 은 용량 때문에 mirror 를 두지 않습니다. 메모리 값은 항상 `peek`/`poke`(또는 frontdoor read/write + scoreboard)로 다뤄야 합니다.<br>
**왜 헷갈리는가**: 레지스터와 메모리를 같은 모델 계층에서 다루다 보니 동일하게 취급하기 쉬워서.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 모든 레지스터 read 가 mismatch | adapter 의 `addr` 스케일(byte vs word) 또는 endian 불일치 | `reg2bus`/`bus2reg`, `create_map` 의 byte-width |
| reset 값은 맞는데 write 후 read 가 틀림 | access policy 오설정(RO 인데 RW 기대 등) | field `configure` 의 access 인자 |
| mirror 가 실제 DUT 와 계속 어긋남 | implicit 인데 제3 마스터 존재 / explicit 인데 auto_predict 미해제 | predictor 연결 + `set_auto_predict(0)` |
| backdoor 접근이 X (`UVM_NOT_OK`) | HDL path 오류 또는 `set_hdl_path_root` 누락 | `configure` 의 hdl path, env 의 root 설정 |
| `update()` 가 write 를 안 함 | desired == mirror | `set` 후 mirror 값 확인, 필요시 직접 `write` |
| 개별 필드 write 가 옆 필드를 망침 | byte-enable 미지원 → 전체 RMW | adapter `supports_byte_enables`, field 의 `individually_accessible` |
| `lock_model` 후 build 에러 | lock 이후 구조 변경 시도 | regmodel build/lock 순서 |

---

## 7. 핵심 정리 (Key Takeaways)

- **RAL = 이름으로 접근 + mirror**. 주소 하드코딩을 없애 RTL 오프셋 변경에도 시퀀스 불변, 블록↔시스템 재사용.
- **mirror(추측) vs desired(원하는 값)** 분리. `set` 은 desired 만, `update` 는 둘이 다를 때만 write, `mirror` 는 DUT 를 읽어 갱신·검증.
- **다섯 API**: `read/write`(표준), `peek/poke`(강제·흉내❌), `get/set`(모델 내부), `update`(조건부), `mirror`(갱신+비교).
- **frontdoor(실제 버스, 느림, 경로 검증) vs backdoor(HDL 직접, zero-time)**. backdoor read/write 는 side-effect 흉내, peek/poke 는 흉내 없음.
- **adapter(`reg2bus`/`bus2reg`)** 가 버스 독립성의 핵심. 버스를 바꿔도 시퀀스 불변.
- **explicit prediction(권장)** = 시퀀서+모니터+predictor + `set_auto_predict(0)`. 제3 마스터까지 mirror 정확.
- **내장 시퀀스**(hw_reset / bit_bash / access / mem_walk)로 새 CSR 블록 smoke test 를 즉시 시작.

:::caution[실무 주의점]
- explicit 이면 **반드시 `set_auto_predict(0)`** — 빠뜨리면 mirror 이중 갱신.
- back-door 쓰려면 `set_hdl_path_root` + field/reg 의 정확한 HDL path 필수.
- `lock_model()` 이후엔 구조 변경 불가 — build 완료 후에 lock.
- 메모리는 mirror 없음 — `peek`/`poke`.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — set vs write (Bloom: Analyze)]
`regmodel.CTRL.set(0xAB)` 만 호출하고 시뮬을 끝냈다. DUT 의 CTRL 레지스터 값은?
<details>
<summary>정답</summary>

**바뀌지 않습니다(reset 값 그대로).** `set()` 은 모델 내부 desired value 만 수정하고 DUT 에는 전혀 접근하지 않습니다. 실제 DUT 에 반영하려면 이후 `update()`(desired≠mirror 면 write) 또는 직접 `write()` 를 호출해야 합니다. `set`+`update` 조합은 "여러 레지스터를 0-time 으로 desired 세팅해두고 마지막에 한 번에 반영" 하는 패턴에 유용합니다.

</details>
:::
:::tip[🤔 Q2 — explicit prediction 누락 (Bloom: Evaluate)]
predictor 를 monitor 에 연결했는데 mirror 값이 가끔 두 배로 토글되거나 어긋난다. 가장 가능성 높은 원인과 수정은?
<details>
<summary>정답</summary>

`set_auto_predict(0)` 을 호출하지 않은 것입니다. 모델이 자신이 낸 트랜잭션으로 implicit 하게 mirror 를 갱신하고, predictor 도 같은 트랜잭션을 모니터로 받아 또 갱신 → **이중 predict**. 수정: `regmodel.<map>.set_auto_predict(0);` 으로 implicit 을 끄고 predictor 단독으로 갱신하게 합니다. explicit prediction 의 필수 짝입니다.

</details>
:::
### 7.2 출처

**Internal (Confluence)**
- `[UVM Basics] Using the Register Layer Classes` — RAL 클래스/메서드/통합 패턴 (사내 import)

**External**
- *UVM 1.2 User's Guide* §5 (Register Abstraction) — Accellera
- *UVM 1.2 Class Reference* — `uvm_reg`, `uvm_reg_field`, `uvm_reg_block`, `uvm_reg_adapter`, `uvm_reg_predictor`
- IEEE 1685 (IP-XACT) — field access policy 매핑

---

## 다음 모듈

→ [Module 08 — Quick Reference Card](../08_quick_reference_card/): 지금까지의 UVM 핵심 API·패턴을 한 장으로 정리한 치트시트.

[퀴즈 풀어보기 →](../quiz/07_register_layer_ral_quiz/)
