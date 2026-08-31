---
title: "10 — 테스트와 복구"
description: JESD270-4 §6.7·6.8·6.13 · Lane remapping 3계층, MISR/LFSR 루프백, Self Repair
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Explain** lane remapping이 시프트 구조로 동작하는 방식과 여분 레인이 하는 역할을 설명한다.
- **Identify** remapping이 불가능한 신호들을 지목하고 왜 그것들이 제외되는지 판단한다.
- **Derive** DWORD 40비트·AWORD 38비트 MISR 폭을 신호 수와 샘플링 구조로 유도한다.
- **Sequence** Self Repair의 self-test → auto-repair 흐름과 채널·SID 순회 요구를 정리한다.
- **Evaluate** 한 번에 한 레인만 복구 가능하다는 제약이 초기화 펌웨어에 부과하는 절차를 판단한다.
:::

:::note[Prerequisites]
- [03 — 초기화·리셋·전원](../03_init_reset_power/) — lane repair가 초기화 시퀀스에 끼어드는 지점, soft/hard 덮어쓰기 위험
- [01 — 규격 지형도](../01_landscape_organization/) — 여분 신호(`RD[3:0]`, 여분 주소, `RM`)의 존재
:::

:::caution[인용 고지]
본 장은 **JESD270-4 (2025-04, WIP draft)** §6.7·§6.8·§6.13을 근거로 **요약·재구성**한 것입니다. remapping 표와 그림은 옮기지 않고 **구조와 규칙만** 서술합니다. 정밀 인코딩은 **JEDEC 원문 우선**.
:::

---

## 1. 왜 복구 기능이 필수인가

[01장](../01_landscape_organization/)에서 스택 하나가 요구하는 신호 마이크로범프를 계산했습니다 — **약 3,896개**. 이 규모에서는 조립 후 일부 연결이 불량일 확률이 통계적으로 무시할 수 없습니다.

규격이 목적을 명시합니다.

> HBM4 DRAM은 **SiP 조립 수율을 개선하고 HBM4 스택의 기능을 회복**하기 위해 interconnect lane remapping을 지원한다. — §6.7 (요약)

즉 lane repair는 "고장 대응"이 아니라 **양산 수율 확보 수단**입니다. 그래서 규격이 여분 신호(`RD[3:0]`, 여분 주소, `RM`)를 처음부터 배정해 두었습니다.

## 2. Lane Remapping — 시프트로 밀어내기

### 기본 구조

동작 원리는 단순합니다. **불량 레인을 비활성화하고, 그 뒤의 신호들을 한 칸씩 밀어, 마지막을 여분 레인이 받습니다.**

```d2
direction: right

NORMAL: "정상 (No Repair)" {
  style.fill: "#e8f5e9"; style.font-color: "#0A0F25"
  n: "위치1: R1   위치2: R2   위치3: R3   …   위치10: R9   RA: (미사용)"
}

BROKEN: "위치2 불량 → Repair" {
  style.fill: "#ffebee"; style.font-color: "#0A0F25"
  b: "위치1: R1   위치2: XX   위치3: R2   …   위치10: R8   RA: R9"
}

NOTE: "불량 레인의 입력 버퍼는 꺼지고\n여분 범프(RA)의 버퍼가 켜진다\n→ 모든 기능이 보존된다" {
  style.fill: "#fff8e1"; style.font-color: "#0A0F25"
}

NORMAL -> BROKEN: "SOFT/HARD_LANE_REPAIR"
BROKEN -> NOTE
```

레지스터 인코딩은 **불량 레인이 나르던 신호를 지시**하며, 기본값 `1111`은 "복구 없음"입니다.

> 레인이 remapping된 뒤, **불량 레인의 입력 버퍼는 꺼지고 여분 범프(RA)의 입력 버퍼가 켜진다. 모든 기능이 보존된다.** — §6.7.1 (요약)

### 세 계층

remapping은 세 영역에서 독립적으로 이뤄집니다.

| 계층 | 여분 자원 | 범위 |
|---|---|---|
| **AWORD** | **채널당 여분 레인 1개** | row 커맨드 버스 **또는** column 커맨드 버스 중 **하나** |
| **DWORD** | 더블 바이트당 여분 레인 (`RD`) | 데이터 버스 |
| **WSO** | 여분 WSO (`RM`) | IEEE 1500 직렬 출력 |

**AWORD와 DWORD remapping은 채널마다 독립**입니다.

`WSO`는 배치가 특이합니다 — **`WSO0`~`WSO15`는 채널 1**, **`WSO16`~`WSO31`은 채널 17**에 연관됩니다. 그리고 `WIR[13:8]`이 `01h`(채널 1) 또는 `11h`(채널 17)일 때 **WDR 길이가 45**, 그 외에는 **40**입니다.

### AWORD — 하나뿐인 여분 레인

채널당 여분 AWORD 레인이 **하나**이므로, **row 버스와 column 버스를 통틀어 한 레인만** 복구할 수 있습니다.

- **`APAR`과 `ARFU`는 column 커맨드 버스 복구에 포함**됩니다([06장](../06_row_commands/)에서 본 두 신호가 여기서 복구 대상이 됩니다).
- **`CK_c`, `CK_t`, `AERR`는 remapping할 수 없습니다.**

:::tip[왜 클럭과 AERR은 제외인가]
`CK_t`/`CK_c`는 **차동 쌍**이고 나머지 레인들과 전기적 특성이 다릅니다. 시프트 구조에 끼워 넣으면 클럭 무결성이 깨집니다.

`AERR`는 **출력**이고, 무엇보다 **복구 과정 자체를 관측하는 데 쓰이는 신호**입니다. 그것이 고장 났다면 복구 결과를 확인할 방법이 없어집니다.

일반 원리로 정리하면 — **자기 자신을 관측·구동하는 데 필요한 신호는 복구 대상이 될 수 없습니다.**
:::

### DWORD — 더블 바이트 단위

데이터 버스는 **더블 바이트당 불량 레인 하나**를 복구합니다. 인접한 두 바이트가 쌍을 이루며(`DQ[15:0]`, `DQ[31:16]`, `DQ[47:32]`, `DQ[63:48]`), **각 더블 바이트는 독립적으로 처리**됩니다.

여기에 프로그래밍 규칙이 하나 붙습니다.

> 더블 바이트 안에서 **정상인 바이트에 대해서는 `1111b`를 프로그램해야** 하며, 다른 바이트의 불량 레인은 표에 따라 인코딩한다. — §6.7.2 (요약)

즉 **쌍 단위로 값을 써야** 하고, 손대지 않을 쪽에도 "복구 없음"을 명시해야 합니다.

복구 후 동작도 AWORD와 다릅니다 — 데이터 버스는 양방향이므로 **불량 레인의 입력 버퍼가 꺼지고 출력 드라이버가 tri-state** 되며, **여분 레인(`RD`)의 입력 버퍼가 켜지고 출력 드라이버가 활성화**됩니다.

보존되는 것과 제외되는 것도 명확합니다.

- **DBI 기능은 보존**됩니다 (MR의 DBI 설정이 활성인 한).
- **Data Parity 기능에는 영향이 없습니다.**
- **`WDQS_c`/`WDQS_t`, `RDQS_c`/`RDQS_t`, `PAR`, `DERR`는 remapping할 수 없습니다.**

제외 목록의 논리가 AWORD와 같습니다 — 스트로브는 차동 쌍이고, `PAR`/`DERR`는 무결성 판정 경로입니다.

그리고 read 시 여분 레인의 드라이버 활성 타이밍이 **바이트의 홀짝을 따릅니다.**

> `RD0`과 `RD2`는 **짝수 바이트** 안에 있어 첫 유효 데이터 비트보다 **1 WDQS 사이클 앞서** 활성화되고, `RD1`과 `RD3`은 **홀수 바이트** 안에 있어 **2 WDQS 사이클 앞서** 활성화된다. — §6.7.2 (요약)

[07장](../07_column_commands/)에서 본 *"홀수 바이트는 2 RDQS 펄스, 짝수 바이트는 1 펄스 앞서 구동"* 과 정확히 같은 규칙입니다. 여분 레인도 **자신이 속한 물리 바이트의 타이밍을 그대로 따릅니다.**

### ⚠️ 한 번에 하나만

이 절에서 초기화 펌웨어에 가장 큰 제약입니다.

> **관련 회로의 전류 제약을 제한하기 위해, 한 번에 단일 채널 또는 WSO의 불량 레인 하나만 복구할 수 있다.** 여러 레인을 복구하려면 각 불량 레인에 대한 복구 벡터를 **순차적으로 시프트 인**해야 하며, **다른 모든 레인 복구 설정은 `Fh`로** 두고 **각각의 실제 레인 복구를 별도의 `UpdateWR` 이벤트로 개시**해야 한다. — §6.7 (요약)

:::caution[N개 불량 = N번의 UpdateWR]
불량 레인이 3개면 복구 절차를 3번 반복해야 합니다. 한 번에 벡터를 몰아 넣으면 **전류 제약을 위반**합니다.

```
for 각 불량 레인:
    다른 모든 레인 설정 = Fh
    이 레인의 복구 벡터를 시프트 인
    UpdateWR 이벤트 발생          ← 여기서 실제 복구가 일어난다
```

[03장](../03_init_reset_power/)에서 본 **"soft가 hard를 덮어쓴다"** 규칙과 합치면 초기화 펌웨어의 절차가 완성됩니다.

```
1. hard lane repair 데이터를 읽는다
2. 새로 필요한 repair를 병합한다
3. 병합된 목록을 한 레인씩, UpdateWR로 나눠 적용한다
4. BYPASS (또는 WRST_n LOW)로 정상 모드 복귀
```
:::

### 발행 시점 제약

> `SOFT_LANE_REPAIR`와 `HARD_LANE_REPAIR` 명령은 **장치 초기화의 일부로서, 정상 메모리 동작이 시작되기 전에만** 발행될 수 있다 — 예를 들어 **CK 클럭이 토글을 시작하기 전에.** — §6.7 (요약)

[03장](../03_init_reset_power/)의 초기화 5단계(CK 토글 시작)보다 **앞**이어야 합니다. 정상 동작 중에는 레인 구성을 바꿀 수 없습니다.

그리고 영속성 선택지가 있습니다.

> HBM4 DRAM은 **스택에서 전원이 완전히 제거되어도 remapping된 레인 정보를 유지하도록 프로그램될 수 있다.** — §6.7

이것이 `SOFT_LANE_REPAIR`(휘발)와 `HARD_LANE_REPAIR`(퓨즈, 영속)의 차이입니다.

## 3. MISR/LFSR 루프백 — 링크를 시험하는 회로

### 목적과 배치

> MISR/LFSR 회로가 HBM4의 **AWORD와 DWORD I/O 블록 안에** 정의된다. 이 회로들은 **호스트와 HBM4 장치 사이의 링크를 테스트하고 트레이닝**하기 위한 것이다. — §6.8 (요약)

메모리 배열이 아니라 **링크(I/O)** 를 겨냥한 기능입니다.

### 폭을 유도해 보기

규격이 제시한 숫자들이 신호 구성에서 그대로 나옵니다.

**DWORD — 바이트당 40비트**

```
한 바이트의 신호 : DQ 8개 + DBI 1개 + ECC/SEV 1개  = 10 신호
샘플링          : WDQS 2사이클 × Rise/Fall        =  4 비트/신호
──────────────────────────────────────────────────────────────
                                  10 × 4          = 40 비트  ✅
```

`Q0`~`Q3`가 각 신호의 반 WDQS 사이클을 가리키며, **BL0~BL3이 앞 두 WDQS 사이클의 Q0~Q3에, BL4~BL7이 다음 두 사이클의 Q0~Q3에** 대응합니다.

**AWORD — 38비트**

```
신호 : R[9:0] 10개 + C[7:0] 8개 = 18 커맨드 비트  + ARFU 1개 = 19 신호
샘플 : CK DDR Rise/Fall                          =  2 비트/신호
──────────────────────────────────────────────────────────────
                          19 × 2                  = 38 비트  ✅
```

**여기서도 `ARFU`가 포함됩니다.** [06장](../06_row_commands/)·[08장](../08_parity/)에 이어 세 번째입니다 — 진리표에 없는 신호가 패리티에도, MISR에도 참여합니다.

**읽어내는 양**

```
바이트 4개 × 40비트 = 160비트 (DWORD 1개)
DWORD 2개           = 320비트  ← IEEE 1500 DWORD_MISR로 직렬 시프트 아웃  ✅
AWORD_MISR          =  38비트
```

MISR/LFSR 회로는 **바이트 간에 독립적으로 동작**합니다.

### 네 가지 모드

규격은 "MISR modes"를 네 모드의 총칭으로 씁니다.

| 모드 | 성격 |
|---|---|
| **LFSR mode** | 패턴 **생성** |
| **Register mode** | 값을 직접 적재·판독 |
| **MISR mode** | 수신 데이터를 **서명(signature)으로 압축** |
| **LFSR Compare mode** | 생성 패턴과 수신 데이터를 **비교** |

`MR7`이 DWORD 쪽 제어(**DWORD MISR Control**, **DWORD Read Mux**, **DWORD Loopback Control**)를 담당하고([04장](../04_mode_registers/)), IEEE 1500 쪽에서는 `AWORD_MISR`·`DWORD_MISR`·`MISR_MASK`·`READ_LFSR_COMPARE_STICKY`·`AWORD_MISR_CONFIG` 명령이 관여합니다.

다항식은 **Galois 형 MISR/LFSR** 구조이며, 규격은 `f(x) = X⁴ + X³ + 1`을 **예시로만** 제시하고 실제 정의는 별도 절에서 규정합니다.

:::tip[MISR가 검증에 주는 것]
MISR는 긴 데이터 스트림을 **고정 폭 서명으로 압축**합니다. 호스트가 알려진 패턴을 보내고 장치의 MISR 값을 읽어 기대값과 비교하면, **전 비트를 하나씩 확인하지 않고도** 링크 무결성을 판정할 수 있습니다.

대가는 **압축 손실**입니다 — 서로 다른 오류가 같은 서명을 낼 수 있습니다(aliasing). 그래서 `LFSR Compare mode`처럼 **실시간 비교** 경로가 따로 있고, 그 결과를 `READ_LFSR_COMPARE_STICKY`로 읽습니다. **sticky**라는 이름이 말하듯, 한 번 발생한 불일치는 남습니다.
:::

## 4. Self Repair — 배열 결함을 스스로 고친다

lane repair가 **연결**을 고친다면, Self Repair는 **배열 자체**의 하드 결함을 고칩니다.

> HBM4 DRAM은 **초기화 과정 중에 DRAM의 결함을 스캔하고 복구**함으로써 **SiP 조립 수율을 개선하거나 높은 시스템 신뢰성을 달성**하기 위해 self repair를 지원한다. — §6.13 (요약)

### 두 단계

```
① self-test    : 벤더 지정 패턴으로 하드 결함을 식별
        ↓
② auto-repair  : ①에서 나온 불량 주소를 자동 복구
                  (복구 가능한 주소 개수는 벤더 지정)
```

`REP_TYPE` 필드(`SELF_REP` 명령의 bits[3:2])를 `11b`로 두면 첫 단계인 self-test가 시작됩니다.

### 순회 구조 — 채널과 SID

한 번에 전체를 처리하지 못합니다.

- 명령은 **8채널 또는 16채널 단위**로 동작합니다. `WIR[13:8]`을 `38h`/`39h`로 두면 절반(16채널), `3Ah`~`3Dh`로 두면 1/4(8채널)을 선택합니다.
- **모든 그룹에 대한 병렬 동작은 지원되지 않습니다.**
- **한 번에 하나의 SID만** 처리하며, `SID_SELECT` 필드(bits[5:4])로 지정합니다.

따라서 전 채널·전 SID를 덮으려면 **`SID 수 × 그룹 수`** 만큼 명령을 반복해야 합니다. 8채널 그룹 기준으로 4-high는 4회, 8-high는 8회, 12-high는 12회입니다(Table 82).

:::caution[스택이 높을수록 초기화가 길어진다]
Self Repair 횟수가 **SID 수에 비례**합니다. 16-high 구성은 4-high의 네 배를 돌아야 합니다.

[03장](../03_init_reset_power/)에서 초기화 시간을 `tINIT3`(4 ms)가 지배한다고 했는데, **Self Repair를 수행하면 그 위에 self-test + auto-repair 시간이 SID 수만큼 곱해져 얹힙니다.**

그리고 병렬화가 **규격상 금지**되어 있으므로 이 시간을 줄일 방법이 없습니다. 부팅 시간 예산을 잡을 때 스택 높이를 반영해야 합니다.
:::

### 발행 조건과 진행 관측

- `SELF_REP`은 **장치가 제대로 초기화된 뒤 — 구체적으로 `tINIT3`가 충족되고 DRAM이 all-banks-idle 상태일 때 — 언제든** 발행할 수 있습니다.
- 선택된 채널들이 **all-banks-idle 상태**여야 합니다.
- 호스트는 `SR_PROGRESS` 필드를 **폴링**해 진행 상황(self-test 진행 중 / auto-repair 진행 중 / 완료 / 미실행)을 확인합니다.
- **그동안 `SELF_REP` 명령이 WIR에 유지되어야** 합니다.
- 클럭 소스는 `WRCK`(직접 또는 기준)일 수도, **`WRCK`와 I/O 기능 클럭 양쪽으로부터 독립적인 내부 클럭 모드**일 수도 있습니다.
- `SELFR_REF_RATE` 필드(bits[7:6])로 **온도 보상 refresh 속도**를 호스트가 제어해야 합니다.

### 결과 판정

`SELF_REP_RESULTS` 명령으로 **SID별** 결과를 읽습니다. 보고 항목은 네 가지입니다.

1. **결함이 남아 있음**
2. **복구 불가능한 결함이 남아 있음**
3. **`SELF_REP`을 다시 실행해야 함**
4. 초기화 이후 실행되지 않았거나, 최근 실행 후 결함 없음

3번이 있다는 것은 **한 번의 실행으로 끝나지 않을 수 있다**는 뜻입니다. 초기화 펌웨어는 **반복 실행 루프**를 가져야 하고, 종료 조건과 최대 시도 횟수를 정해야 합니다.

## ⚙️ 설계 적용 (RTL / Front-end)

### 5.1 Lane repair 시퀀서 — 한 레인씩

```systemverilog
// 전류 제약 때문에 한 번에 한 레인만 (§6.7)
// 다른 모든 레인 설정은 Fh, 각 복구는 별도 UpdateWR 이벤트로.
typedef struct { logic [5:0] ch; logic [3:0] enc; lane_domain_e dom; } repair_item_t;

task automatic apply_lane_repairs(input repair_item_t items[$]);
  foreach (items[i]) begin
    set_all_lanes_to_no_repair();            // 전부 4'hF
    set_lane_repair(items[i].ch, items[i].dom, items[i].enc);
    pulse_update_wr();                       // ← 여기서 실제 복구
    wait_t_slrep();                          // tSLREP 등 명령 타이밍 준수
  end
endtask
```

**흔한 실수**: 여러 레인의 벡터를 한 번에 시프트 인하고 `UpdateWR`를 한 번만 주는 것. 규격 위반이며 전류 제약을 깨뜨립니다.

### 5.2 DWORD는 쌍 단위로 쓴다

```systemverilog
// 더블 바이트 단위 — 정상인 바이트에도 1111b를 명시해야 한다 (§6.7.2)
function automatic logic [7:0] dword_repair_pair(
    input logic [3:0] enc, input logic broken_is_upper);
  return broken_is_upper ? {enc, 4'hF}    // 상위 바이트가 불량
                         : {4'hF, enc};   // 하위 바이트가 불량
endfunction
```

### 5.3 복구 불가 신호 목록을 코드로 고정

```systemverilog
// remapping 불가 (§6.7.1, §6.7.2)
//   AWORD: CK_t, CK_c, AERR
//   DWORD: WDQS_t/_c, RDQS_t/_c, PAR, DERR
// 이 신호들에 대한 복구 요청은 발생 자체를 막는다.
`ifndef SYNTHESIS
  a_no_repair_clock: assert property (@(posedge wrck) disable iff (!wrst_n)
    repair_req |-> !(repair_target inside {SIG_CK_T, SIG_CK_C, SIG_AERR,
                                           SIG_WDQS_T, SIG_WDQS_C,
                                           SIG_RDQS_T, SIG_RDQS_C,
                                           SIG_PAR, SIG_DERR}))
    else $error("Attempted to remap a non-remappable signal");
`endif
```

### 5.4 MISR 서명 비교

```systemverilog
// DWORD: 바이트당 40b × 4바이트 × 2 DWORD = 320b
// AWORD: 38b                                       (§6.8)
localparam int DWORD_MISR_BITS = 40 * 4 * 2;   // 320
localparam int AWORD_MISR_BITS = 38;

// 호스트 측에서도 동일한 다항식으로 기대 서명을 계산해 비교한다.
// aliasing 때문에 서명 일치가 "무오류"를 보장하지는 않는다 -> LFSR Compare Sticky 병행.
wire misr_match = (dword_misr_read == dword_misr_expected);
wire link_clean = misr_match && !lfsr_compare_sticky;
```

**`misr_match`만으로 판정하면 안 됩니다.** 압축 손실로 서로 다른 오류가 같은 서명을 낼 수 있으므로 **sticky 비교 결과를 함께** 봐야 합니다.

### 5.5 Self Repair 순회 루프

```systemverilog
// SID × 채널 그룹을 순회한다. 병렬 실행은 규격상 금지 (§6.13)
// 결과가 "다시 실행 필요"이면 반복 — 최대 시도 횟수를 정해야 한다.
localparam int MAX_SELF_REP_PASSES = 3;

for (int pass = 0; pass < MAX_SELF_REP_PASSES; pass++) begin
  for (int sid = 0; sid < NUM_SID; sid++) begin
    for (int grp = 0; grp < NUM_CH_GROUPS; grp++) begin
      require_all_banks_idle(grp);
      issue_self_rep(sid, grp, REP_TYPE_SELF_TEST, ref_rate);
      do poll_sr_progress(); while (!sr_done);   // SELF_REP을 WIR에 유지한 채
    end
  end
  read_self_rep_results();
  if (!needs_rerun) break;
end
```

**폴링 중 `SELF_REP`을 WIR에 유지**해야 한다는 조건을 놓치면 진행 상태를 읽을 수 없습니다.

## 6. 대표 문제 — dry-run

### 문제 1 — 복구 절차

> 초기화 중 `EXTEST`로 채널 5의 row 버스 레인 1개와 채널 12의 DWORD 레인 1개, 총 2개의 불량을 찾았다. 복구 절차를 순서대로 쓰라.

<details>
<summary>풀이</summary>

**두 레인이므로 복구를 두 번 나눠 수행한다**(§6.7 — 한 번에 하나만).

```
0. EXTEST 이후 RESET_n 토글 (필수)              ← 03장 §4.4
   tINIT3 경과 → WRST_n HIGH

1. hard lane repair 데이터를 읽어 새 항목과 병합  ← 03장 (soft가 hard를 덮어씀)

2. [채널 5 row 레인]
   모든 레인 설정 = Fh
   채널 5의 AWORD row 복구 벡터 시프트 인
   UpdateWR                                    ← 실제 복구
   tSLREP 등 타이밍 준수

3. [채널 12 DWORD 레인]
   모든 레인 설정 = Fh
   해당 더블 바이트에 대해 {불량 바이트 enc, 정상 바이트 Fh} 시프트 인
   UpdateWR

4. BYPASS (또는 WRST_n LOW) → 정상 기능 모드 복귀

5. CK 토글 시작 → 초기화 4~6단계 계속
```

**핵심 세 가지**: `EXTEST` 후 리셋 필수 / hard 데이터 병합 / **레인마다 별도 `UpdateWR`**.
</details>

### 문제 2 — MISR 폭 유도

> DWORD 한 바이트의 MISR가 40비트인 이유를 신호 구성으로 유도하라. AWORD가 38비트인 이유도.

<details>
<summary>풀이</summary>

**DWORD 바이트**
```
신호 : DQ 8 + DBI 1 + ECC/SEV 1        = 10
샘플 : WDQS 2사이클 × Rise/Fall        =  4 비트/신호
       (Q0~Q3가 각 신호의 반 WDQS 사이클)
                          10 × 4       = 40 b  ✅
```

**AWORD**
```
신호 : R[9:0] 10 + C[7:0] 8 = 18 커맨드 + ARFU 1 = 19
샘플 : CK DDR Rise/Fall                          =  2 비트/신호
                          19 × 2                 = 38 b  ✅
```

**읽어내는 총량**
```
DWORD_MISR : 40 × 4바이트 × 2 DWORD = 320 b
AWORD_MISR :                          38 b
```

**함정**: AWORD에서 `ARFU`를 빼면 36비트가 되어 맞지 않는다. `ARFU`는 진리표에 없지만 **구동 대상이고, 패리티 대상이고, MISR 대상**이다([06장](../06_row_commands/), [08장](../08_parity/)).
</details>

### 문제 3 — 부팅 시간 예산

> 16-high 구성에서 Self Repair를 8채널 그룹 단위로 전 채널·전 SID에 대해 수행하려 한다. 몇 번의 `SELF_REP` 명령이 필요하며, 병렬로 줄일 수 있는가?

<details>
<summary>풀이</summary>

16-high는 SID가 **4개**(`SID0`~`SID3`)이고, 32채널을 8채널 그룹으로 나누면 **4그룹**이다.

```
4 SID × 4 그룹 = 16회        ← Table 82와 일치
```

**병렬화는 불가능하다.** §6.13이 *"8 또는 16채널의 모든 그룹에 대한 Self Repair 병렬 동작은 지원되지 않는다"* 고 명시한다. `SELF_REP`은 **한 번에 하나의 SID**만 처리한다.

**부팅 시간 함의**: 4-high(4회)의 **네 배**다. 각 회차는 self-test + auto-repair 시간을 포함하며, 결과가 "다시 실행 필요"로 나오면 더 반복해야 한다.

**설계 결론**: 부팅 시간 예산은 **스택 높이에 비례**해 잡아야 하고, Self Repair를 **매 부팅마다 할지 특정 조건에서만 할지**가 시스템 설계 판단이 된다. `SELF_REP_RESULTS`의 "초기화 이후 실행되지 않음" 상태가 그 판단을 지원한다.
</details>

## 🔍 검증 연결

- DFT 경로와 mission mode의 교차 → [`hbm_dv` Ch11 DFT·RAS](../../hbm_dv/11_dft_ras/)
- 복구 시나리오를 테스트로 구성 → [`hbm_dv` Ch08 시나리오](../../hbm_dv/08_testcase_scenarios/)
- 테스트 구조가 검증 환경에 요구하는 것 → [`hbm_dv` Ch11](../../hbm_dv/11_dft_ras/)

## 핵심 정리

- lane repair는 고장 대응이 아니라 **SiP 조립 수율 확보 수단**이다. 약 3,896개 신호 범프 규모에서 필수다.
- 동작 원리는 **시프트** — 불량 레인을 끄고 뒤를 한 칸씩 밀어 **여분 레인이 마지막을 받는다.**
- 계층은 셋 — **AWORD**(채널당 1개, row **또는** column), **DWORD**(더블 바이트당 `RD`), **WSO**(`RM`).
- **복구할 수 없는 신호**: `CK_t`/`CK_c`, `AERR`, `WDQS_t`/`_c`, `RDQS_t`/`_c`, `PAR`, `DERR`. **자기 자신을 관측·구동하는 신호는 복구 대상이 아니다.**
- DWORD는 **쌍 단위로 프로그램**한다 — 정상 바이트에도 `1111b`를 명시해야 한다.
- ⚠️ **한 번에 한 레인만.** 전류 제약 때문이며, N개면 **N번의 `UpdateWR`** 이 필요하다.
- lane repair는 **CK 토글 이전**, 즉 초기화 중에만 가능하다. `HARD_LANE_REPAIR`는 **전원이 제거되어도 유지**된다.
- MISR 폭은 신호 구성에서 유도된다 — **DWORD 바이트 40b**(10 신호 × 4), **AWORD 38b**(19 신호 × 2). **`ARFU`가 포함**된다.
- 모드는 넷 — **LFSR / Register / MISR / LFSR Compare**. 서명은 **압축 손실(aliasing)** 이 있으므로 `READ_LFSR_COMPARE_STICKY`를 함께 봐야 한다.
- Self Repair는 **self-test → auto-repair** 2단계이며, **패턴과 복구 가능 개수가 벤더 지정**이다.
- Self Repair는 **SID 하나씩, 채널 그룹 하나씩** 순회한다. **병렬 실행은 규격상 금지**이므로 **부팅 시간이 스택 높이에 비례**한다.
- `SELF_REP_RESULTS`에 **"다시 실행 필요"** 상태가 있다 — 펌웨어는 **반복 루프와 최대 시도 횟수**를 가져야 한다.

## Further Reading

- **규격**: JESD270-4 §6.7 Interconnect Redundancy Remapping (Table 48–54, Figure 70) · §6.8 Loopback Test Modes (Figure 71–76) · §6.13 Self Repair (Table 82)
- **다음 장**: [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/)
- **관련**: [03 — 초기화](../03_init_reset_power/) (soft/hard 덮어쓰기) · [04 — Mode Register](../04_mode_registers/) (`MR7`) · [07 — Column 커맨드](../07_column_commands/) (홀짝 바이트 타이밍)
- **이해도 점검**: [퀴즈](../quiz/10_test_repair_quiz/)
