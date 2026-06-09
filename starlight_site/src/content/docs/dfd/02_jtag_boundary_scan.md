---
title: "N02 — JTAG & Boundary Scan"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Identify** JTAG의 다섯 신호(TCK/TMS/TDI/TDO/TRSTn)와 각각의 역할을 식별할 수 있다.
- **Trace** TAP controller 16-state FSM이 TMS 시퀀스로 IR scan과 DR scan을 어떻게 수행하는지 추적할 수 있다.
- **Differentiate** IDCODE / BYPASS / boundary scan / 벤더 정의(DAP access) 같은 Data Register의 용도를 구분할 수 있다.
- **Apply** daisy chain으로 여러 TAP을 연결하고, SWD가 같은 DAP를 어떻게 2핀으로 노출하는지 설명할 수 있다.
:::
:::note[사전 지식]
- [N01 — 왜 DFD인가](../01_why_dfd/) (4계층 스택 조망)
- 동기 FSM과 shift register의 동작
- 직렬 데이터 전송의 기본 (MSB/LSB, shift in/out)
:::
---

## 1. Why care? — 4핀으로 칩 전체에 접근한다

### 1.1 시나리오 — 핀이 모자란다

테스트 엔지니어가 새 칩을 보드에 올렸는데, 디버그와 **production test**(양산 단계에서 칩·납땜이 정상인지 대량으로 걸러내는 제조 테스트) 양쪽 모두 필요한 상황입니다. 칩 핀은 수백 개지만 디버그 전용으로 쓸 수 있는 것은 극소수입니다. 칩 안의 수백만 게이트, 모든 코어 레지스터, 전체 메모리 공간에 접근해야 하는데, 이걸 병렬 핀으로 다 빼면 핀이 폭발합니다.

JTAG(Joint Test Action Group; 그 이름의 위원회가 만든 IEEE 1149.1 표준 — 직렬 핀으로 칩 내부에 접근)의 답은 **직렬화**입니다. 단 4개(또는 TRSTn 포함 5개) 핀으로 칩 내부의 임의의 레지스터에 비트를 밀어 넣고(shift in) 빼냅니다(shift out). 클럭(TCK) 한 줄, 상태 제어(TMS) 한 줄, 데이터 입력(TDI) 한 줄, 데이터 출력(TDO) 한 줄이면, 칩 안 어떤 **scan chain**(여러 저장 소자를 하나의 긴 직렬 줄로 엮어, 한 핀으로 차례차례 값을 넣고 뺄 수 있게 한 사슬)에도 도달할 수 있습니다. 이 직렬 접근 위에 [N03](../03_adi_dap_coresight/)의 DAP가 얹혀 메모리-맵 디버그가 됩니다.

### 1.2 JTAG 신호

| Signal | 방향 | 용도 |
|--------|------|------|
| **TCK** | In | Test clock — 모든 JTAG 동작의 클럭 |
| **TMS** | In | TAP state machine control — FSM 이동을 결정 |
| **TDI** | In | Test Data In — 칩으로 들어가는 직렬 데이터 |
| **TDO** | Out | Test Data Out — 칩에서 나오는 직렬 데이터 |
| **TRSTn** | In (optional) | 비동기 TAP reset (생략 시 TMS로 reset 가능) |

핵심은 TCK·TMS·TDI가 모두 _입력_이고 TDO만 _출력_이라는 점입니다. 데이터는 TDI로 들어와 칩 안 register를 거쳐 TDO로 나오는 한 방향 파이프이며, 그 파이프의 동작을 결정하는 것이 TMS입니다.

---

## 2. Intuition — TMS는 운전대, 그리고 한 장 그림

:::tip[💡 한 줄 비유]
**TAP controller** ≈ **TMS라는 운전대 하나로 모는 16칸 보드게임**.<br>
매 TCK마다 TMS가 0이냐 1이냐에 따라 다음 칸으로 한 칸 이동합니다. 어떤 칸에 멈추느냐에 따라 "명령 레지스터에 비트를 채워라(IR)" 또는 "데이터 레지스터로 데이터를 흘려라(DR)"가 정해집니다. 칩은 운전대(TMS) 조작 패턴만으로 무엇을 할지 압니다.
:::

### 한 장 그림 — TAP을 통한 IR/DR 접근

```d2
direction: right

TDI: "TDI →"
IR: "**Instruction Register (IR)**\n어느 DR을 TDI↔TDO에\n연결할지 선택"
MUX: "선택된 DR"
BS: "Boundary Scan DR"
ID: "IDCODE DR"
BY: "BYPASS DR (1-bit)"
DAP: "벤더 DR\n(DAP access)"
TDO: "→ TDO"
TAP: "**TAP Controller**\n16-state FSM\n(TMS로 구동)"

TDI -> IR: "shift (IR scan)"
IR -> MUX: "선택"
MUX -> BS
MUX -> ID
MUX -> BY
MUX -> DAP
MUX -> TDO: "shift (DR scan)"
TAP -> IR: "Capture/Shift/Update-IR 제어"
TAP -> MUX: "Capture/Shift/Update-DR 제어"
```

### 왜 이 구조인가 — Design rationale

세 가지 요구의 교집합입니다.

1. **하나의 직렬 핀으로 여러 종류의 접근을 해야 한다** → IR(Instruction Register)이 "지금 어떤 DR을 쓸지" 골라 주므로, 같은 TDI/TDO 핀으로 boundary scan도 하고 IDCODE도 읽고 DAP도 접근합니다.
2. **상태 전이가 신호 한 줄(TMS)로 결정돼야 한다** → 16-state FSM을 두면 TMS 비트열만으로 capture/shift/update 단계를 명확히 시퀀싱할 수 있습니다.
3. **체인에 안 쓰는 칩은 빠르게 통과해야 한다** → BYPASS DR(1비트)이 있어, daisy chain의 관심 없는 TAP은 1비트만 지연시켜 통과시킵니다.

---

## 3. 작은 예 — IDCODE 한 번 읽기가 FSM을 통과하는 과정

가장 단순한 JTAG 동작인 IDCODE 읽기로 TAP FSM의 흐름을 봅시다. IDCODE는 칩의 제조사/부품 번호를 담은 32비트 식별자입니다.

### 단계별 다이어그램

```d2
direction: down

S0: "**① Test-Logic-Reset**\nTMS=1을 5클럭 → 무조건 reset 상태\nIDCODE가 기본 선택됨"
S1: "**② Run-Test/Idle 경유**\nTMS=0으로 idle 진입"
S2: "**③ Select-DR → Capture-DR**\nIDCODE 값을 DR에 capture(병렬 로드)"
S3: "**④ Shift-DR**\nTMS=0 유지하며 32 TCK\nTDO로 IDCODE 비트가 LSB부터 출력"
S4: "**⑤ Update-DR → Idle**\nDR scan 종료"
S0 -> S1 -> S2 -> S3 -> S4
```

### 단계별 의미

| Step | TAP 상태 | TMS 패턴 | 무엇이 | 왜 |
|------|---------|---------|--------|-----|
| ① | Test-Logic-Reset | `1`×5 | FSM을 알려진 상태로, IDCODE를 기본 IR로 | 전원 직후 알려진 시작점 확보 |
| ② | Run-Test/Idle | `0` | 동작 대기 상태 진입 | scan 시작 전 정지점 |
| ③ | Capture-DR | `1,0,0` | IDCODE 32비트를 DR에 병렬 로드 | shift 전에 읽을 값을 준비 |
| ④ | Shift-DR | `0`×32 | 매 TCK마다 1비트씩 TDO로 출력 | 직렬로 값 회수 |
| ⑤ | Update-DR | `1,1,0` | scan 종료, idle 복귀 | 다음 동작 준비 |

:::note[여기서 잡아야 할 핵심]
어떤 동작이든 패턴이 똑같습니다 — **Capture(값 로드) → Shift(직렬 이동) → Update(반영)**. IR scan이든 DR scan이든 이 3단계이며, TMS가 어느 칸으로 가느냐만 다릅니다. IDCODE는 IR scan 없이 reset 후 기본 선택되므로 DR scan만으로 읽힙니다.
:::

---

## 4. 일반화 — TAP FSM 16상태와 Data Register 종류

### 4.1 16-state FSM의 두 갈래

```d2
direction: down

TLR: "Test-Logic-Reset"
IDLE: "Run-Test/Idle"
SEL_DR: "Select-DR-Scan"
SEL_IR: "Select-IR-Scan"

DRPATH: "**DR scan 경로**\nCapture-DR → Shift-DR\n→ Exit1-DR → Update-DR"
IRPATH: "**IR scan 경로**\nCapture-IR → Shift-IR\n→ Exit1-IR → Update-IR"

TLR -> IDLE: "TMS=0"
IDLE -> SEL_DR: "TMS=1"
SEL_DR -> SEL_IR: "TMS=1"
SEL_DR -> DRPATH: "TMS=0 (DR scan)"
SEL_IR -> IRPATH: "TMS=0 (IR scan)"
DRPATH -> IDLE
IRPATH -> IDLE
```

TAP FSM은 16개 상태를 가지며, 핵심은 **DR scan 경로**와 **IR scan 경로**가 거의 대칭이라는 점입니다. 두 경로 모두 Capture → Shift → Exit1 → Update의 4단계를 거치고, Shift 상태에 머무는 동안 TDI/TDO로 비트가 직렬 이동합니다. Select-DR-Scan에서 TMS=1을 한 번 더 주면 Select-IR-Scan으로 넘어가 IR scan을 하게 됩니다. Test-Logic-Reset은 어느 상태에서든 TMS=1을 5번 주면 도달하는 안전 복귀점입니다.

**왜 하필 "5번"인가 — FSM 그래프 거리.** 16-state FSM에서 _TMS=1로 갈 수 있는 간선만_ 따라가는 부분 그래프를 그리면, 모든 상태가 결국 Test-Logic-Reset으로 흘러들도록 설계되어 있습니다(TLR은 TMS=1 자기루프 — 한번 들어오면 계속 머묾). 이때 TLR에서 _가장 먼_ 상태에서 TMS=1만 밟아 TLR까지 가는 최단 경로의 길이가 정확히 **5** 입니다(예: Shift/Exit/Update 계열의 깊은 상태 → Exit → Update → Select-DR → Select-IR → TLR). 따라서 어느 상태에서 출발하든 TMS=1을 5번 연속 주면 _반드시_ TLR에 도달합니다 — 시작 상태를 모르더라도 reset이 보장되므로, 디버거가 "상태가 꼬였을 때 무조건 복귀"하는 안전장치로 씁니다.

### 4.2 Data Register 종류

IR에 어떤 instruction을 싣느냐에 따라 TDI↔TDO 사이에 연결되는 DR이 달라집니다.

| DR | IR instruction | 용도 |
|----|---------------|------|
| **IDCODE** | IDCODE | 32비트 칩 식별자 읽기 (reset 후 기본) |
| **BYPASS** | BYPASS | 1비트 — daisy chain에서 이 TAP을 통과만 시킴 |
| **Boundary Scan** | EXTEST / SAMPLE | 칩 핀 상태를 capture/제어 (원래 용도) |
| **벤더 정의** | (벤더별) | DAP access 등 — Arm SoC 디버그의 핵심 |

### 4.3 boundary scan — JTAG의 원래 임무

JTAG이 처음 정의된 이유는 boundary scan입니다. 칩의 각 IO 핀 옆에 boundary scan cell을 두고, 이 cell들을 하나의 긴 shift register로 연결합니다. EXTEST instruction을 IR에 싣고 이 register에 패턴을 shift하면, 칩 핀을 외부 회로처럼 구동/관찰할 수 있어 PCB의 납땜 불량이나 단선을 칩을 떼지 않고 검사합니다. SAMPLE은 정상 동작 중 핀 값을 capture만 합니다. 현대 SoC에서 같은 TAP 인프라가 boundary scan과 디버그(DAP access) 양쪽에 _재사용_됩니다.

**EXTEST가 핀을 _가로채는_ 회로 — mux intercept.** "핀을 외부 회로처럼 구동"이 가능한 이유는, boundary scan cell이 코어 로직과 실제 핀 사이의 정상 경로에 **mux로 끼어들기** 때문입니다. 각 출력 핀 앞에 mux가 하나 있어, 평소(정상 동작/SAMPLE)에는 _코어 로직의 신호_ 를 핀으로 통과시키지만, EXTEST 중에는 mux의 select가 바뀌어 _scan cell에 shift해 둔 값_ 을 핀으로 내보냅니다. 입력 핀 쪽도 대칭으로, EXTEST 중에는 외부 핀 값을 cell이 capture해 코어로는 격리합니다. 즉 cell은 정상 데이터 경로 위에 얹힌 "전환 스위치 + 관찰점"이며, EXTEST는 그 스위치를 scan 측으로 넘겨 핀을 강제 구동/관찰합니다. 정상 동작(EXTEST 아님)에서는 mux가 코어 경로를 그대로 통과시켜 cell이 회로 동작을 방해하지 않습니다.

### 4.4 daisy chain — 여러 TAP을 한 체인으로

```d2
direction: right
HOST: "Debugger"
T1: "TAP 1\n(TDI→TDO)"
T2: "TAP 2\n(TDI→TDO)"
T3: "TAP 3\n(TDI→TDO)"
HOST -> T1: "TDI"
T1 -> T2: "TDO→TDI"
T2 -> T3: "TDO→TDI"
T3 -> HOST: "TDO"
```

여러 TAP은 TCK와 TMS를 공유하고, 한 TAP의 TDO를 다음 TAP의 TDI에 이어 붙여 **하나의 긴 직렬 체인**을 만듭니다. 관심 있는 TAP만 실제 DR을 선택하고 나머지는 BYPASS(1비트)로 두면, 디버거는 체인 전체를 하나의 긴 shift register로 다루되 관심 TAP의 데이터만 정확한 비트 위치에서 읽습니다.

---

## 5. 디테일 — IR scan, BYPASS의 가치, SWD 대안

### 5.1 IR scan으로 instruction 바꾸기

DR을 바꾸려면 먼저 IR scan으로 IR에 새 instruction을 실어야 합니다. 흐름은 DR scan과 대칭입니다.

```
Test-Logic-Reset → Run-Test/Idle
  → Select-DR-Scan → Select-IR-Scan   (TMS=1, 1)
  → Capture-IR                         (TMS=0)  : IR에 현재 상태 capture
  → Shift-IR                           (TMS=0)  : 새 instruction 비트를 TDI로 shift in
  → Exit1-IR → Update-IR               (TMS=1, 1): IR에 반영 → 선택된 DR이 바뀜
  → Run-Test/Idle                      (TMS=0)
```

Update-IR 순간 IR 값이 확정되고, 그 instruction에 대응하는 DR이 다음 DR scan에서 TDI↔TDO 사이에 연결됩니다.

### 5.2 BYPASS가 daisy chain을 빠르게 만드는 이유

8개 TAP이 체인에 있는데 그중 하나만 긴 boundary scan register(예: 500비트)에 접근하고 싶다고 합시다. 나머지 7개 TAP에 BYPASS instruction을 실으면 각각 1비트짜리 register만 끼어들므로, 디버거는 `500 + 7 = 507`비트만 shift하면 됩니다. BYPASS가 없다면 7개의 긴 register를 모두 통과해야 해 수천 비트를 헛돌려야 합니다. BYPASS는 daisy chain에서 "관심 없는 TAP을 최소 비용으로 건너뛰는" 장치입니다.

### 5.3 SWD — 2핀 대안

```d2
direction: right
JTAG: "**JTAG**\nTCK TMS TDI TDO (+TRSTn)\n4~5핀" {
  DAP_J: "→ 같은 DAP"
}
SWD: "**SWD (Serial Wire Debug)**\nSWCLK + SWDIO\n2핀" {
  DAP_S: "→ 같은 DAP"
}
```

핀이 극히 부족한 디바이스(소형 MCU(Microcontroller Unit, 코어·메모리·주변장치를 한 칩에 담은 소형 제어용 칩) 등)에서는 JTAG의 4~5핀도 부담입니다. **SWD(Serial Wire Debug)** 는 ADI가 정의한 2핀(SWCLK 클럭 + SWDIO 양방향 데이터) 대안으로, JTAG을 대체하면서도 _같은 DAP_를 노출합니다. 즉 물리 프로토콜만 다르고 그 너머의 디버그 세계(DP/AP, ROM table, CoreSight)는 완전히 동일합니다. SWJ-DP는 JTAG와 SWD를 핀에서 자동 선택하는 DP 변종입니다([N03](../03_adi_dap_coresight/)에서 다룸).

### 5.4 scan cell은 왜 2단(shift FF + update latch)인가

§3의 "Capture → Shift → Update" 3단계는 FSM 상태일 뿐 아니라 _각 scan cell 회로_ 의 구조와 직접 대응합니다. 셀 하나는 **두 개의 저장 소자**로 이루어집니다.

```
                 ┌──────────────┐        ┌──────────────┐
 capture/TDI ───►│  Shift FF    ├──TCK──►│ Update latch │───► (DR 출력/핀 구동)
                 │ (1단: 이동용) │        │ (2단: shadow)│
                 └──────┬───────┘        └──────────────┘
                        └──► TDO (다음 셀의 TDI로)
```

- **1단 — shift flip-flop**: Capture-DR에서 값(IDCODE 비트, 핀 상태 등)을 병렬 로드하고, Shift-DR 동안 매 TCK마다 옆 셀로 한 칸씩 이동시킵니다. TDI→shift FF→TDO 사슬이 곧 scan chain입니다.
- **2단 — update(shadow) latch**: Update-DR 상태에서만 1단의 현재 값을 받아 _출력_ 으로 반영합니다.

**왜 굳이 2단인가?** Shift 동안에는 1단 FF의 값이 매 TCK마다 마구 바뀝니다(체인을 따라 비트가 흐르므로). 만약 출력이 1단을 직접 보고 있다면, EXTEST로 핀을 구동하는 경우 _shift하는 내내 핀이 중간 비트값으로 덜덜 떨려_ 외부 회로에 글리치(glitch; 의도치 않게 잠깐 튀는 신호 펄스)를 줍니다. 2단 update latch가 있으면 Shift 중 출력은 _직전 Update에서 확정된 값_ 으로 **안정 유지** 되고, 모든 비트를 다 밀어 넣은 뒤 Update-DR 한 순간에만 새 값이 일제히 반영됩니다. 즉 "준비(Shift)"와 "반영(Update)"을 분리해, 직렬로 채우는 과도 상태가 출력/핀에 새어 나가지 않게 하는 것이 2단 구조의 이유입니다. IR도 같은 이유로 shift단 + update단을 가져, Update-IR 순간에만 새 instruction이 확정됩니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'TDI/TDO로 바로 메모리 주소를 보낸다']
**실제**: JTAG은 _직렬 비트 스트림_만 다룹니다. 메모리 주소·데이터 개념은 그 위에 얹힌 DAP(벤더 DR)의 의미이지, JTAG 자체에는 없습니다. JTAG은 "어떤 register에 비트를 채우고 뺀다"만 합니다.<br>
**왜 헷갈리는가**: 최종 결과가 메모리 접근이라, JTAG이 직접 메모리를 다룬다고 착각하기 쉬워서.
:::
:::danger[❓ 오해 2 — 'TMS는 데이터 신호다']
**실제**: TMS는 데이터가 아니라 **FSM 제어** 신호입니다. 데이터는 TDI(입력)/TDO(출력)로 흐르고, TMS는 매 TCK마다 다음 상태를 결정합니다. TMS=1을 5번 주면 무조건 Test-Logic-Reset.<br>
**왜 헷갈리는가**: 같은 직렬 핀들이라 다 데이터처럼 보여서.
:::
:::danger[❓ 오해 3 — 'IDCODE를 읽으려면 IR scan부터 해야 한다']
**실제**: Test-Logic-Reset 직후 IR에 _IDCODE가 기본 선택_됩니다. 따라서 reset 후 바로 DR scan만 하면 IDCODE를 읽을 수 있습니다(IR scan 불필요). 다른 DR을 쓸 때만 IR scan이 필요합니다.<br>
**왜 헷갈리는가**: "DR을 쓰려면 항상 IR부터"라는 일반 규칙의 예외라서.
:::
:::danger[❓ 오해 4 — 'daisy chain의 모든 TAP을 매번 다 shift해야 한다']
**실제**: 관심 없는 TAP은 BYPASS(1비트)로 두면 됩니다. 그래서 체인 전체가 아니라 (관심 register 길이 + 나머지 TAP 수)만 shift합니다.<br>
**왜 헷갈리는가**: 체인이 하나의 긴 register라 전부 통과해야 할 것 같아서.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| IDCODE가 all-1 또는 all-0로 읽힘 | TAP이 connect 안 됨, TDO floating, TCK 미인가 | 핀 배선, TCK 토글 여부, pull 저항 |
| IDCODE는 맞는데 DAP 접근 실패 | IR scan으로 DAP instruction 미선택 | IR scan 시퀀스, 벤더 DR 코드 |
| daisy chain에서 엉뚱한 비트가 읽힘 | BYPASS 비트 수 계산 오류(체인 위치) | 각 TAP의 IR 길이, BYPASS 1비트 오프셋 |
| TAP이 가끔 임의 상태로 빠짐 | TMS reset 시퀀스(1×5) 누락 또는 TRSTn 미처리 | reset 전략, TRSTn pull |
| 핀이 모자라 JTAG을 못 뺌 | SWD 2핀으로 전환 검토 | SWJ-DP 지원 여부, SWCLK/SWDIO 배선 |

---

## 7. 핵심 정리 (Key Takeaways)

- **JTAG은 직렬 접근 통로**. TCK(클럭)/TMS(FSM 제어)/TDI(입력)/TDO(출력) (+TRSTn)로 칩 내부 register에 비트를 shift in/out 한다.
- **TAP controller = 16-state FSM**, TMS 하나로 구동. DR scan과 IR scan 경로가 대칭이며 둘 다 Capture→Shift→Update 단계.
- **IR이 DR을 선택**: IDCODE / BYPASS / boundary scan / 벤더 정의(DAP access). reset 후 IDCODE가 기본.
- **boundary scan**이 JTAG의 원래 임무(핀 연결 테스트, EXTEST/SAMPLE)이고, 현대 SoC는 같은 TAP을 디버그에 재사용한다.
- **daisy chain**: TCK/TMS 공유 + TDO→TDI 체인. BYPASS(1비트)로 관심 없는 TAP을 최소 비용으로 통과.
- **SWD**는 2핀(SWCLK+SWDIO) 대안으로 _같은 DAP_를 노출 — 물리만 다르고 그 위 세계는 동일.

:::caution[실무 주의점]
- Test-Logic-Reset은 TMS=1을 5클럭 — 상태가 꼬이면 항상 여기로 복귀.
- TRSTn을 안 쓰면 pull과 TMS reset 시퀀스로 reset을 보장해야 한다.
- daisy chain에서는 각 TAP의 IR 길이와 BYPASS 오프셋을 정확히 계산해야 비트가 안 어긋난다.
:::

### 7.1 자가 점검

:::tip[🤔 Q1 — FSM 추적 (Bloom: Analyze)]
디버거가 IR을 BYPASS로 바꾸려 한다. Run-Test/Idle에서 시작해 어떤 TMS 패턴으로 IR scan 경로를 통과하는가(상태 이름으로)?
<details>
<summary>정답</summary>

`Run-Test/Idle → Select-DR-Scan(TMS=1) → Select-IR-Scan(TMS=1) → Capture-IR(TMS=0) → Shift-IR(TMS=0, 여기서 BYPASS 코드 비트를 TDI로 shift) → Exit1-IR(마지막 비트와 함께 TMS=1) → Update-IR(TMS=1, IR 확정) → Run-Test/Idle(TMS=0)`. Update-IR 순간 IR이 BYPASS로 확정되어, 이후 DR scan에서는 1비트 BYPASS register만 TDI↔TDO에 연결됩니다. 핵심은 DR/IR 경로가 대칭이고 Capture→Shift→Update 3단계를 거친다는 점입니다.

</details>
:::
:::tip[🤔 Q2 — 재사용 판단 (Bloom: Evaluate)]
"우리 칩은 boundary scan을 쓰니까 디버그용 JTAG은 따로 핀을 더 둬야 한다"는 주장은 옳은가?
<details>
<summary>정답</summary>

**옳지 않습니다.** 같은 TAP 인프라(같은 TCK/TMS/TDI/TDO 핀)가 boundary scan과 디버그(DAP access)에 _재사용_됩니다. 무엇을 할지는 IR에 어떤 instruction을 싣느냐로 갈립니다 — EXTEST/SAMPLE이면 boundary scan DR이, 벤더 정의 instruction이면 DAP access DR이 TDI↔TDO에 연결됩니다. 따라서 디버그용으로 핀을 추가할 필요가 없습니다. 핀이 오히려 부족하면 SWD(2핀)로 줄이는 방향을 검토합니다.

</details>
:::
### 7.2 출처

**External**
- IEEE Std 1149.1 — Standard Test Access Port and Boundary-Scan Architecture (TAP FSM, IR/DR, boundary scan)
- Arm IHI 0031 — Arm Debug Interface (SW-DP / SWJ-DP 정의)

---

## 다음 모듈

→ [N03 — Arm ADI(DAP) & CoreSight](../03_adi_dap_coresight/): JTAG 직렬 통로 위에 DAP가 얹혀 어떻게 메모리-맵 디버그가 되고, 그 너머 CoreSight 생태계가 코어를 멈추고 trace를 뽑는지 본다.

[퀴즈 풀어보기 →](../quiz/02_jtag_boundary_scan_quiz/)
