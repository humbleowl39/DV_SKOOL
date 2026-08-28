---
title: "Ch06 — UVM 환경 계층"
---

:::tip[학습 목표]
이 챕터를 마치면:

- **Design** IP → Subsystem → Full-chip으로 이어지는 환경 계층을 설계하고 각 계층의 역할을 배정할 수 있다.
- **Classify** 구성값을 컴파일 타임 파라미터 · 런타임 설정 · 테스트별 선택의 세 종류로 분류할 수 있다.
- **Justify** 폭은 컴파일 타임에, 개수와 값은 런타임에 두어야 하는 이유를 세대 이관 시나리오로 정당화할 수 있다.
- **Evaluate** 자극의 현실성이 계층마다 달라야 하는 이유를 판단하고 그 균형을 잡는 방법을 제시할 수 있다.
:::

:::note[사전 지식]
- [Ch03 — Custom UVM Agent A-to-Z](../03_custom_uvm_agent/): `is_active`를 처음부터 넣어 둔 이유가 여기서 드러납니다
- [Ch05 — Full-Chip Mixed-Level](../05_mixed_level/): "하나의 환경 + 구성 전환"
- [UVM 코스 Module 01(아키텍처·Phase)](../../uvm/), [Module 04(config_db·Factory)](../../uvm/): **환경 구성과 config_db의 동작 원리는 여기서 다룹니다**
:::

---

## 1. Why care? — 계층이 올라갈 때 무엇이 남는가

Ch03에서 CCI Agent를 만들었습니다. `hbm_ch_ctrl` 하나를 검증하는 환경이 섭니다. 스펙 R1~R20을 자극할 수 있고, 회귀도 돌아갑니다.

그런데 프로젝트는 거기서 끝나지 않습니다.

- **Subsystem**: `hbm_ch_ctrl`이 여러 개 모이고, 그 위에 채널 간 중재 로직이 붙습니다. 이제 CCI를 구동하는 것은 우리 Agent가 아니라 **실제 상위 로직**입니다
- **Full-chip**: base die 전체가 들어옵니다. 초기화는 CPU가 **실제 펌웨어 코드**를 실행해서 수행합니다

각 계층에서 환경을 새로 만들어야 할까요? 그러면 세 벌의 환경이 생기고, 스펙 규칙을 검사하는 checker도 세 벌이 됩니다. 규칙 하나를 고치면 세 곳을 고쳐야 하고, 곧 세 환경이 서로 다르게 동작하기 시작합니다.

반대로 처음부터 full-chip 환경만 만들면? Ch02에서 이미 결론이 났습니다 — 발견이 늦고 디버깅 후보가 폭증합니다.

**무엇을 재사용하고 무엇을 바꿀 것인가.** 이 질문의 답이 환경 구조를 결정하고, 그 구조가 세대 이관 비용까지 좌우합니다. 선행 코스가 세 챕터에 걸쳐 반복한 요구(**#8 구성값 파라미터화**)를 여기서 닫습니다.

---

## 2. 직관 — 재사용 단위는 env, 바뀌는 것은 config

### 순진한 시도 1 — 계층마다 환경을 새로 만든다

각 계층에 맞게 최적화된 환경을 따로 구축합니다. 각각 단순해집니다.

**어디서 막히나?** 재사용되어야 할 것들이 복제됩니다 — Agent, scoreboard, checker, 커버리지 모델, 시나리오. 그리고 복제된 것들은 **반드시 갈라집니다.** 스펙 R6의 검사 로직을 IP-level에서 고쳤는데 subsystem 쪽은 그대로 남아, 같은 규칙에 대해 두 계층이 다른 판정을 내리는 상황이 생깁니다.

### 순진한 시도 2 — Full-chip 환경 하나로 통일한다

가장 실제에 가까운 환경 하나만 만들고 거기서 전부 검증합니다.

**어디서 막히나?** Ch02의 대안 B와 같습니다. 발견이 늦고, 실패 하나의 원인 후보가 수십 개이며, 초기에는 full-chip RTL이 아예 없어 착수할 수도 없습니다.

### 일반화 — 계층은 포함 관계이고, 차이는 설정으로 표현한다

> **환경은 계층을 이루며 상위 환경은 하위 환경을 포함한다.**
> 재사용 단위는 **env**이고, 계층 간 차이는 **config**로 표현한다.

```d2
direction: up

IP: "**IP-level env**\nDUT: hbm_ch_ctrl\nCCI Agent: **ACTIVE**\nDRAM: VIP\n\n목적: 스펙 R1~R20 전수, 대량 CRT" { style.fill: "#e8f5e9"; style.font-color: "#0A0F25" }

SUB: "**Subsystem env**\nDUT: ch_ctrl 다수 + 중재 로직\nCCI Agent: **PASSIVE** (실제 로직이 구동)\n일부 Agent만 ACTIVE\n\n목적: 블록 간 상호작용, 통합 I1~I8" { style.fill: "#fff8e1"; style.font-color: "#0A0F25" }

TOP: "**Full-chip env**\nDUT: base die 전체\n자극원: **Test Firmware** (CPU 실행)\nAgent: 대부분 PASSIVE\n\n목적: 초기화·시스템 시나리오" { style.fill: "#e3f2fd"; style.font-color: "#0A0F25" }

IP -> SUB: "env를 인스턴스로 포함\nconfig만 변경"
SUB -> TOP: "동일"
```

계층이 올라갈 때 무엇이 바뀌는지 정리하면:

| 요소 | IP-level | Subsystem | Full-chip |
|---|---|---|---|
| **Agent** | ACTIVE (자극 생성) | 대부분 PASSIVE | PASSIVE |
| **자극원** | UVM 시퀀스 | 상위 로직 + 일부 시퀀스 | **Test Firmware (CPU)** |
| **Checker · Assertion** | 동일하게 사용 | 동일 | 동일 |
| **Scoreboard** | 동일 | 동일 (범위 확장) | 동일 |
| **Coverage 모델** | 동일 | 동일 | 동일 |
| **회귀 규모** | 수천~수만 | 수백~수천 | 수십~수백 |

**Checker·Scoreboard·Coverage가 세 계층에서 동일하다**는 점이 핵심입니다. 이들이 계층마다 복제되면 실패 3이 발생합니다. Agent의 `is_active`가 설정값인 덕분에 **같은 Agent를 관측 전용으로 재사용**할 수 있고 — Ch03에서 미리 넣어 둔 이유가 여기서 드러납니다.

---

## 3. 작은 예 — 구성값의 세 종류

`hbm_ch_ctrl` 환경의 구성값을 나열해 보면 성격이 다릅니다. 이 구분이 **#8을 실제로 닫는 열쇠**입니다.

| 종류 | 특징 | 예 | 구현 수단 |
|---|---|---|---|
| **(a) 컴파일 타임 파라미터** | **타입**에 영향. 바꾸면 재컴파일 | `DATA_W`, `ADDR_W`, `ID_W` | 클래스·인터페이스 파라미터 |
| **(b) 런타임 설정값** | 동작에 영향. 재컴파일 불필요 | 채널 수, 뱅크 수, `tRCD_CYC`, 프로파일 | **config 객체 필드** |
| **(c) 테스트별 선택** | 실행마다 다름 | 시나리오, 시드, `is_active` | 테스트 클래스 · 플러스아그 |

**원칙: 폭은 컴파일 타임, 개수와 값은 런타임.**

왜 이 경계인가 하면, 신호 폭은 인터페이스와 트랜잭션 필드의 **타입**을 결정하므로 런타임에 바꿀 수 없습니다. 반면 채널이 몇 개인지, 타이밍 기준값이 얼마인지는 **동작에 영향을 줄 뿐 타입을 바꾸지 않습니다.**

이 구분을 틀리면 두 방향으로 고통이 옵니다.

- 폭을 런타임 설정으로 만들려 하면 → 최대 폭으로 선언하고 마스킹하는 복잡한 코드가 생깁니다
- 개수를 컴파일 파라미터로 만들면 → 구성이 바뀔 때마다 **전체 재컴파일**이 필요해 회귀 회전이 느려집니다

### Config 객체 계층

```systemverilog
// 계층 최상위 — 모든 계층이 공유하는 구성
class hbm_dv_cfg extends uvm_object;
  `uvm_object_utils(hbm_dv_cfg)

  // (b) 런타임 설정값 — 재컴파일 없이 바뀐다
  int unsigned num_pc        = 2;    // 스펙 A.2 NUM_PC
  int unsigned num_bank      = 16;   // 스펙 A.2 NUM_BANK
  int unsigned num_channel   = 16;   // 세대에 따라 16 또는 32

  // 스펙 A.7 MR_TIMING 기준값
  int unsigned trcd_cyc      = 8;
  int unsigned trp_cyc       = 8;
  int unsigned tras_cyc      = 16;

  // Ch05의 구성 프로파일
  typedef enum { PROF_P0, PROF_P1, PROF_P2 } profile_e;
  profile_e    profile       = PROF_P0;

  // 하위 config
  cci_agent_cfg cci_cfg;

  function new(string name = "hbm_dv_cfg");
    super.new(name);
    cci_cfg = cci_agent_cfg::type_id::create("cci_cfg");
  endfunction
endclass
```

```systemverilog
// IP-level 환경
class hbm_ch_ctrl_env #(parameter int DATA_W=32, ADDR_W=34, ID_W=4)
  extends uvm_env;

  `uvm_component_param_utils(hbm_ch_ctrl_env#(DATA_W, ADDR_W, ID_W))

  hbm_dv_cfg                            cfg;
  cci_agent #(DATA_W, ADDR_W, ID_W)     cci_agt;
  hbm_ch_ctrl_scoreboard                sb;
  hbm_ch_ctrl_coverage                  cov;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(hbm_dv_cfg)::get(this, "", "cfg", cfg))
      `uvm_fatal("ENV", "hbm_dv_cfg를 config_db에서 찾을 수 없습니다")

    // 하위 config를 주입 — 계층이 올라가도 이 구조는 그대로
    uvm_config_db#(cci_agent_cfg)::set(this, "cci_agt*", "cfg", cfg.cci_cfg);

    cci_agt = cci_agent#(DATA_W, ADDR_W, ID_W)::type_id::create("cci_agt", this);
    sb      = hbm_ch_ctrl_scoreboard::type_id::create("sb", this);
    cov     = hbm_ch_ctrl_coverage::type_id::create("cov", this);
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    cci_agt.ap.connect(sb.cci_export);
    cci_agt.ap.connect(cov.analysis_export);
  endfunction
endclass
```

```systemverilog
// Subsystem 환경 — IP-level env를 포함하고 config만 바꾼다
class hbm_subsys_env #(parameter int DATA_W=32, ADDR_W=34, ID_W=4)
  extends uvm_env;

  `uvm_component_param_utils(hbm_subsys_env#(DATA_W, ADDR_W, ID_W))

  hbm_dv_cfg                                       cfg;
  hbm_ch_ctrl_env #(DATA_W, ADDR_W, ID_W)          ch_env[];
  hbm_subsys_scoreboard                            subsys_sb;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(hbm_dv_cfg)::get(this, "", "cfg", cfg))
      `uvm_fatal("SUBSYS", "hbm_dv_cfg를 찾을 수 없습니다")

    // 상위 계층에서는 상위 로직이 CCI를 구동한다 → Agent는 관측 전용
    cfg.cci_cfg.is_active = UVM_PASSIVE;

    // 채널 수는 (b) 런타임 설정값 — 재컴파일 없이 16 → 32
    ch_env = new[cfg.num_channel];
    foreach (ch_env[i]) begin
      uvm_config_db#(hbm_dv_cfg)::set(this, $sformatf("ch_env_%0d*", i), "cfg", cfg);
      ch_env[i] = hbm_ch_ctrl_env#(DATA_W, ADDR_W, ID_W)::type_id::create(
                    $sformatf("ch_env_%0d", i), this);
    end

    subsys_sb = hbm_subsys_scoreboard::type_id::create("subsys_sb", this);
  endfunction
endclass
```

**주목할 두 줄**

- `cfg.cci_cfg.is_active = UVM_PASSIVE;` — Ch03에서 넣어 둔 설정값 하나로 Agent가 관측 전용이 됩니다. Agent 코드는 손대지 않습니다
- `ch_env = new[cfg.num_channel];` — 채널 수가 런타임 설정이므로 **16 → 32 변경에 재컴파일이 필요 없습니다**

### 세대 이관에서 보상받는 지점

선행 코스 [Ch04](../../hbm/04_channels_addressing/)에서 산술로 확인한 사실이 여기서 값을 냅니다.

| 항목 | HBM3E | HBM4 | 종류 |
|---|---|---|---|
| pseudo-channel 폭 | 32-bit | **32-bit (동일)** | (a) 컴파일 타임 |
| 채널당 폭 | 64-bit | **64-bit (동일)** | (a) 컴파일 타임 |
| 채널 수 | 16 | **32** | **(b) 런타임** |
| pseudo-channel 총수 | 32 | **64** | (b) 런타임 |

**폭은 그대로이고 개수만 두 배**입니다. 구성값을 (a)/(b)로 올바르게 나눠 두었다면 **세대 이관에 재컴파일이 필요하지 않습니다** — `num_channel`을 32로 바꾸면 됩니다.

선행 코스 Ch04의 Active Recall이 *"HBM4의 변화는 각 채널이 넓어진 것이 아니라 같은 규격의 채널이 두 배로 늘어난 것"* 이라고 했던 관찰이, 여기서 **환경 구조의 설계 근거**가 됩니다.

:::note[🤔 잠깐 — 세 종류로 분류하세요]
다음 구성값을 (a) 컴파일 타임 / (b) 런타임 설정 / (c) 테스트별 선택으로 분류하고, 잘못 분류하면 무슨 일이 생기는지 말하세요.

- **① `MR_TIMING.tRCD_CYC` 기준값**
- **② `cci_req_addr`의 폭 (`ADDR_W`)**
- **③ 오류 주입을 켤지 여부**
- **④ Ch05의 구성 프로파일 (P0/P1/P2)**

<details>
<summary>정답 / 해설</summary>

**① `tRCD_CYC` → (b) 런타임 설정**

스펙 A.7에서 이 값은 CSR 필드이며, **테스트 중에도 바뀔 수 있습니다**(R6의 기준값이 설정에 의존). 따라서 config 객체 필드이자 시나리오가 변경하는 대상입니다.

*잘못 분류하면*: (a)로 만들면 타이밍 값마다 재컴파일이 필요하고, **설정 효과 검증(#17)이 불가능**해집니다 — 한 테스트 안에서 값을 바꿔 동작 변화를 관측할 수 없기 때문입니다.

**② `ADDR_W` → (a) 컴파일 타임 파라미터**

신호와 트랜잭션 필드의 **타입**을 결정합니다. 런타임에 바꿀 수 없습니다.

*잘못 분류하면*: (b)로 만들려면 최대 폭으로 선언하고 유효 비트를 마스킹해야 하며, 코드가 복잡해지고 파형에서 실제 폭을 알기 어려워집니다.

**③ 오류 주입 여부 → (c) 테스트별 선택** (그리고 item 필드)

Ch03에서 확인한 대로 **어느 트랜잭션에 주입할지는 시퀀스가 고릅니다.** 따라서 환경 설정이 아니라 시나리오/테스트의 선택입니다.

*잘못 분류하면*: (b)로 두면 켜져 있는 동안 모든 요청에 적용되어 "정상 사이에 오류 하나" 시나리오를 만들 수 없습니다 (Ch03 자가 점검).

**④ 구성 프로파일 → (b) 런타임 설정** — 단 주의가 필요합니다

프로파일 선택 자체는 config 필드로 두는 것이 맞습니다. 그러나 **프로파일이 바뀌면 인스턴스화되는 모델이 달라지므로**, 실제로는 build 시점에 결정되며 컴파일 옵션과 함께 관리되는 경우가 많습니다(회로 수준 모델은 별도 컴파일이 필요할 수 있음).

*실무적 처리*: config 필드로 노출해 **시나리오는 프로파일을 알 필요가 없게** 하고(Ch05의 프로파일 독립성), 빌드 스크립트가 그 값에 맞는 컴파일 구성을 고르게 합니다.

**공통 원리**: 분류 기준은 *"이것이 **타입**을 바꾸는가"* 입니다. 타입을 바꾸면 (a), 동작만 바꾸면 (b), 실행마다 다르면 (c)입니다.

</details>
:::

### 자극의 현실성 — 계층마다 다르다

계층이 올라가면 자극원이 바뀝니다. 그리고 자극의 **성격**도 바뀝니다.

| 계층 | 자극원 | 자극 범위 | 목적 |
|---|---|---|---|
| IP-level | UVM 시퀀스 (CRT) | **스펙이 허용하는 전 범위** | 견고성 — 이상한 입력에도 규칙대로 동작 |
| Subsystem | 상위 로직 + 일부 시퀀스 | 상위 로직이 실제로 만드는 범위 | 상호작용 |
| Full-chip | **Test Firmware** (CPU 코드) | 실제 소프트웨어가 만드는 범위 | 현실성 |

**두 방향의 위험이 있습니다.**

자극이 **너무 좁으면** 실제 시스템에서 발생하는 조합을 재현하지 못합니다. 선행 코스가 경고한 *"단일 채널 순차 시나리오"* 가 이것입니다.

자극이 **너무 넓으면** 실제로는 발생할 수 없는 입력으로 실패가 나옵니다. 이것도 손실입니다 — 조사에 시간을 쓰고, 결론이 *"이런 조합은 실제로 안 생긴다"* 이면 그 시간은 회수되지 않습니다. 게다가 그런 실패가 반복되면 팀이 실패 보고를 신뢰하지 않게 됩니다.

**균형 잡는 방법**

1. **IP-level은 넓게** 둔다 — 견고성 확인이 목적. 단 스펙이 금지한 입력은 넣지 않는다
2. **Full-chip에서 관측한 실제 자극 패턴을 IP-level 제약에 역방향 반영**한다 — Test Firmware가 만드는 요청 분포를 보고, IP-level CRT의 가중치를 조정
3. 시나리오 리뷰에 *"실제 호스트가 이 순서를 낼 수 있는가"* 를 항목으로 둔다
4. 실제로 불가능한 조합이라 판단되면 **제약으로 배제하고 그 근거를 기록**한다 — 기록이 없으면 나중에 누군가 다시 같은 논쟁을 한다

이 역방향 피드백이 **#12(자극의 현실성)** 의 실질적 내용입니다.

### Test Firmware — Full-chip의 자극원

Full-chip 계층에서는 CPU가 실제 코드를 실행해 초기화와 설정을 수행합니다. UVM 시퀀스가 아니라 **C 코드가 자극원**입니다.

| 측면 | UVM 시퀀스 | Test Firmware |
|---|---|---|
| 현실성 | 낮음 (우리가 만든 순서) | **높음** (실제 소프트웨어 경로) |
| 제어 가능성 | **높음** (원하는 조합을 직접 지정) | 낮음 (코드 흐름에 종속) |
| 무작위화 | 쉬움 | 어려움 |
| 디버깅 | 쉬움 | 어려움 (SW·HW 양쪽) |

**결합 방식**: UVM 시퀀스가 펌웨어 실행을 트리거하고, 그 결과는 여전히 **monitor·scoreboard·assertion이 관측**합니다. 즉 자극원만 바뀌고 관측 구조는 그대로입니다 — 이것이 checker를 계층 간에 공유해야 하는 또 다른 이유입니다.

---

## 4. 일반화 — 두 가지 구조적 선택

### 대안 A — 계층 없이 full-chip만 만든다면?

Ch02의 대안 B와 같은 판단입니다. 여기서는 **환경 구조** 관점으로 다시 봅니다.

**왜 안 되나**: 착수 시점 문제가 추가됩니다. full-chip RTL은 프로젝트 후반에야 통합되므로, 그때까지 검증을 시작할 수 없습니다. IP-level 환경은 **IP RTL만 있으면 착수 가능**하며, 이것이 검증이 설계와 병행할 수 있는 이유입니다.

### 대안 B — Checker를 계층마다 새로 짠다면?

각 계층에 맞게 checker를 최적화하는 방식입니다. 상위 계층에서는 일부 규칙만 보면 되니 가볍게 만들 수 있습니다.

**왜 안 되나**: 규칙이 **한 곳에서만 정의되어야** 합니다. 스펙 R6이 바뀌면 checker 한 곳만 고쳐야 하는데, 세 벌이면 세 곳을 고쳐야 하고 하나를 놓치면 계층 간 판정이 갈립니다. 그리고 그 불일치는 **어느 쪽이 맞는지 판단하는 데 또 시간이 듭니다.**

**올바른 처리**: checker·assertion·scoreboard는 **단일 구현을 계층 간에 공유**합니다. 계층별로 다르게 하고 싶다면 **활성화 여부를 설정값으로** 둡니다 — 구현을 복제하지 않습니다.

---

## 5. 디테일 — 환경 계층에서 실제로 벌어지는 일

### 실패 1 — Agent가 passive를 지원하지 않는다

IP-level만 생각하고 Agent를 만들면 driver가 항상 인스턴스화되고, 상위 계층에서 실제 로직과 **동시에 버스를 구동**하려 합니다.

**관측되는 증상**: subsystem 환경에서 버스 충돌이 나거나, 그것을 피하려고 Agent를 아예 빼면 **관측도 함께 사라집니다.** monitor가 없으면 그 인터페이스의 트랜잭션이 scoreboard·coverage에 도달하지 않으므로, 상위 계층에서 그 부분이 **측정되지 않습니다.**

**처방**: Agent는 **처음부터 active/passive를 설정값으로** 둡니다 (Ch03에서 그렇게 했습니다). monitor는 어느 모드에서도 인스턴스화됩니다.

### 실패 2 — 구성값의 종류를 잘못 나눈다

개수를 컴파일 파라미터로 두거나, 폭을 런타임에 바꾸려 한 경우입니다.

**관측되는 증상**: 전자는 구성이 바뀔 때마다 전체 재컴파일이 필요해 **회귀 회전이 느려집니다.** 야간 회귀에서 여러 구성을 돌리려면 컴파일도 여러 번 해야 하고, 그 시간이 시뮬레이션 시간을 잡아먹습니다. 후자는 최대 폭 선언과 마스킹 코드로 환경이 복잡해집니다.

**처방**: **폭은 (a), 개수와 값은 (b)** 라는 경계를 초기에 정하고 문서화합니다. 새 구성값이 추가될 때마다 *"이것이 타입을 바꾸는가"* 를 묻습니다.

### 실패 3 — 계층마다 checker가 복제된다

대안 B의 결과입니다.

**관측되는 증상**: 같은 시나리오가 IP-level에서는 통과하고 subsystem에서는 실패합니다(또는 반대). 원인을 찾아보면 **두 계층의 checker가 규칙을 다르게 구현**하고 있습니다. 어느 쪽이 맞는지 판단하려면 스펙으로 돌아가야 하고, 그동안 두 팀이 각자 자기 checker가 맞다고 봅니다.

**처방**: 규칙의 **단일 구현**을 유지합니다. 계층별 차이는 활성화 설정으로 표현합니다.

---

## 6. 흔한 오해

| 오해 | 실제 |
|---|---|
| "계층마다 환경을 만들어야 최적화된다" | 재사용되어야 할 것이 복제되고 **반드시 갈라집니다** |
| "Full-chip 환경 하나면 충분" | 착수가 늦고 디버깅 후보가 폭증합니다 |
| "구성값은 다 config에 넣으면 된다" | **폭은 타입을 바꿉니다** — 컴파일 타임이어야 합니다 |
| "개수는 파라미터로 두는 게 안전" | 재컴파일 지옥이 됩니다. 개수는 **런타임**입니다 |
| "상위 계층에서 Agent는 필요 없다" | driver는 빠지지만 **monitor는 남아야** 측정이 유지됩니다 |
| "자극은 넓을수록 좋다" | 실제로 불가능한 조합의 실패는 **시간을 태우고 신뢰를 깎습니다** |
| "Test Firmware는 SW팀 일" | Full-chip 자극원입니다. **검증 계획의 일부**입니다 |

---

## 🔧 이 문제를 이렇게 푼다

> **닫는 항목: #8 — 구성값 전면 파라미터화 / #12 — 자극의 현실성 확보**

### #8 — 구성값 3분류 원칙

| 종류 | 판정 질문 | 구현 | 변경 비용 |
|---|---|---|---|
| **(a) 컴파일 타임** | 이것이 **타입**을 바꾸는가? | 클래스·인터페이스 파라미터 | 재컴파일 |
| **(b) 런타임 설정** | 동작만 바꾸는가? | config 객체 필드 | 없음 |
| **(c) 테스트별 선택** | 실행마다 다른가? | 테스트 클래스·플러스아그 | 없음 |

**원칙: 폭은 (a), 개수와 값은 (b), 시나리오 선택은 (c).**

**적용 절차**
1. 스펙의 파라미터 목록(A.2)과 CSR 맵(A.7)을 나열한다
2. 각각에 *"타입을 바꾸는가"* 를 묻는다
3. (b)는 config 객체에 모으고 **계층 간에 주입**한다
4. 새 구성값이 생길 때마다 같은 질문을 반복한다

**검증되는 이득**: 세대 이관(HBM3E → HBM4)에서 폭은 그대로이고 채널 수만 두 배이므로, 올바르게 분류했다면 **재컴파일 없이 설정 변경만으로** 대응됩니다.

### #12 — 자극 현실성의 균형

| 계층 | 자극 폭 | 이유 |
|---|---|---|
| IP-level | **넓게** (스펙 허용 전 범위) | 견고성 확인 |
| Subsystem | 중간 | 상위 로직이 만드는 범위 |
| Full-chip | 실제 (Test Firmware) | 현실성 확인 |

**운영 규칙**
- **역방향 피드백**: Full-chip에서 관측한 실제 자극 패턴을 IP-level CRT의 **가중치·제약에 반영**한다
- 시나리오 리뷰에 *"실제 호스트가 이 순서를 낼 수 있는가"* 항목을 둔다
- 불가능하다고 판단해 제약으로 배제할 때는 **근거를 기록**한다 — 기록이 없으면 같은 논쟁이 반복된다
- Test Firmware를 **검증 계획의 항목**으로 잡는다 (SW팀에 위임하지 않는다)

### 환경 구조 규칙

- **Agent는 active/passive를 설정값으로.** monitor는 어느 모드에서도 존재한다
- **Checker·assertion·scoreboard·coverage는 단일 구현을 계층 간 공유.** 계층별 차이는 활성화 설정으로
- 상위 env는 하위 env를 **인스턴스로 포함**하고 config만 바꾼다
- 프로파일(Ch05)은 config 필드로 노출해 **시나리오가 프로파일을 모르게** 한다

---

## 7. 핵심 정리

- 환경은 **계층을 이루고 상위는 하위를 포함**한다. 재사용 단위는 env, 차이는 config
- 계층이 올라가면 **자극원만 바뀌고 관측 구조는 그대로**다 — Agent는 PASSIVE로, checker는 공유
- 구성값은 세 종류다 — **(a) 폭=컴파일 타임 / (b) 개수·값=런타임 / (c) 시나리오 선택=테스트별**
- 분류 기준은 *"이것이 **타입**을 바꾸는가"*
- 올바르게 분류하면 **세대 이관에 재컴파일이 필요 없다** — HBM4는 폭 동일·개수 두 배이므로
- 자극은 **넓기만 해서도 좁기만 해서도** 안 된다. 계층별로 다르게 두고 **Full-chip → IP-level 역방향 피드백**으로 조정한다
- **Test Firmware는 Full-chip의 자극원**이며 검증 계획의 항목이다
- Checker를 복제하면 **계층 간 판정이 갈리고** 어느 쪽이 맞는지 판단하는 데 또 시간이 든다

:::note[🤔 마무리 자가 점검]
프로젝트가 HBM3E에서 **HBM4로 이관**됩니다. 선행 코스에서 확인한 변화는 이렇습니다.

> 총 폭 1024 → **2048-bit**, 채널 16 → **32개**, 채널당 폭 64-bit **동일**, pseudo-channel 폭 32-bit **동일**

현재 환경의 구성값이 올바르게 (a)/(b)/(c)로 분류되어 있다고 가정할 때,

(a) **재컴파일이 필요한 것**은 무엇입니까? (b) **설정 변경만으로 되는 것**은? (c) 그런데 **분류와 무관하게 반드시 손봐야 하는 것**이 하나 있습니다. 무엇입니까?

<details>
<summary>정답 / 해설</summary>

**(a) 재컴파일이 필요한 것 — 원칙적으로 없습니다**

폭이 전부 동일합니다. `DATA_W`(pseudo-channel 32-bit), 채널당 64-bit, `ADDR_W`(용량에 따라 달라질 수 있으나 채널 수와는 무관), `ID_W` — 어느 것도 바뀌지 않습니다.

이것이 선행 코스 Ch04의 관찰(*"규격은 그대로, 개수만 두 배"*)이 환경 설계에서 보상받는 지점입니다.

**(b) 설정 변경만으로 되는 것**

- `num_channel`: 16 → **32**
- `num_pc` 총수: 32 → 64 (채널당 2는 그대로)
- 주소 맵 관련 설정 (용량이 바뀌면 `ADDR_W`가 영향받을 수 있으나 이는 채널 수와 별개)
- 채널 인스턴스 배열이 `new[cfg.num_channel]`이므로 **자동으로 32개 생성**

**(c) 분류와 무관하게 반드시 손봐야 하는 것 — Coverage 모델**

선행 코스 [Ch02](../../hbm/02_generations/)가 경고한 바로 그 지점입니다.

> 16 → 32채널 변화에서 위험한 것은 테스트가 **깨지는** 것이 아니라 **깨지지 않는** 것이다.

covergroup의 bin이 16개 기준으로 정의되어 있으면, 채널 인스턴스는 32개로 잘 생성되고 시뮬레이션도 정상 동작하는데 **새로 늘어난 16개 채널이 측정 대상에서 빠집니다.** 그리고 기존 bin은 모두 채워지므로 커버리지는 **100%를 보고**합니다.

파라미터화는 **환경이 동작하게** 만들어 주지만, **coverage 모델이 새 구성을 반영하는지는 별개 문제**입니다. bin 정의가 `cfg.num_channel`을 참조하도록 되어 있는지 확인해야 하며, 이것이 21항목 #6(세대 이관 시 coverage 모델 반영 확인)이고 Ch10에서 다룹니다.

**교훈**: 파라미터화가 잘 되어 있을 때 오히려 이 함정이 위험합니다. **환경이 조용히 잘 도는 것이 검증이 잘 되고 있다는 증거가 아닙니다.**

</details>
:::

**다음 챕터**: [Ch07 — V-Plan & 검증 프로세스](../07_vplan_process/)에서 지금까지 만든 것들(경계표·매핑표·프로파일·환경 계층)을 하나의 검증 계획으로 묶고, 진행을 추적하는 방법을 다룹니다.

**퀴즈**: [Ch06 퀴즈](../quiz/06_env_hierarchy_quiz/)

---

## 참고 자료

- [부록 A — `hbm_ch_ctrl` 스펙](../appendix_a_hbm_ch_ctrl_spec/) — A.2 파라미터, A.7 CSR 맵
- [UVM 코스 Module 01 — 아키텍처 & Phase](../../uvm/) — env 계층과 phase의 원리
- [UVM 코스 Module 04 — config_db & Factory](../../uvm/) — config 주입 경로 매칭
- [UVM 코스 Module 06 — 실무 패턴 & 안티패턴](../../uvm/) — God Env 안티패턴과 재사용 구조
- [HBM 아키텍처 Ch04 — 채널 · Pseudo-channel](../../hbm/04_channels_addressing/) — 폭 동일·개수 두 배라는 관찰
- [HBM 아키텍처 Ch02 — 세대 지형도](../../hbm/02_generations/) — coverage 모델이 조용히 무력화되는 문제
