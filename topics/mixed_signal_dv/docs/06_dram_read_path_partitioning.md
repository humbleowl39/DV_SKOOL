# Ch06. DRAM Read Path — 어떤 블록을 어떤 방법으로 검증할까

## 학습 목표

- **(Remember)** DRAM read 경로의 7개 stage(decoder → WL → cell → BL → SA → column mux → IO)를 나열할 수 있다
- **(Understand)** 각 stage에서 어떤 물리/전기 현상이 핵심인지 설명할 수 있다
- **(Apply)** 각 블록에 RNM/SPICE/Digital 중 적합한 패러다임을 매핑할 수 있다
- **(Analyze)** tRCD margin 검증 시나리오에서 어디서 무엇을 측정해야 하는지 분해할 수 있다
- **(Evaluate)** 새 블록(예: VPP pump)에 어떤 검증 패러다임이 적합한지 결정할 수 있다

## 1. DRAM Read 경로 — 7 단계

DRAM의 read 동작을 이해하면, 왜 mixed-signal 검증이 필수인지가 자연스럽게 보입니다. ACT 커맨드가 들어오면 row decoder가 활성화할 행을 선택하고, word line driver가 그 행의 WL을 높은 전압으로 구동합니다. WL이 올라가면 비트 셀의 access transistor가 켜지고, 수십 펨토패럿(fF) 크기의 cell capacitor에 저장된 전하가 bit line으로 흘러나옵니다. 이 때 bit line은 precharge 전압 근처에서 미세하게 — 보통 수십 밀리볼트 — 변합니다. sense amplifier가 이 미세한 전압 차이를 감지하고 full-swing 디지털 신호로 증폭한 뒤, column mux를 통해 IO buffer로 보내지고 DQ 핀으로 출력됩니다.

```
[Command]                  [Bit cell]
ACT/RD                      │
   │                        │
   ▼                        ▼
[Row Decoder] ──→ [Word Line Driver] ──→ Word Line (WL)
                                              │
                                              ▼ (WL active)
                                          [Bit Cell]: capacitor 방전
                                              │
                                              ▼ Charge sharing
                                          [Bit Line (BL)]
                                              │
                                              ▼ (Sensing window)
                                          [Sense Amp]: 미세 차이 증폭
                                              │
                                              ▼ Latch
                                          [Column Mux]
                                              │
                                              ▼
                                          [IO buffer] ──→ DQ pin
```

이 7개 stage 중 row decoder, mode register, FSM 같은 순수 디지털 로직은 기존 digital sim으로 충분합니다. 그러나 WL driver부터 DQ 출력까지는 전압·전하·임피던스가 의미를 갖는 영역입니다. 각 stage가 검증 관점에서 무엇을 요구하는지를 정리하면 다음과 같습니다.

| Stage | 입력 | 출력 | 핵심 물리 |
|---|---|---|---|
| 1. Row Decoder | row addr | one-hot WL select | logic only |
| 2. WL Driver | digital WL_pre | analog WL voltage (0 → VPP) | Driver R · WL load C, slew |
| 3. Bit Cell | WL high | cell→BL charge transfer | Charge sharing, leakage |
| 4. Bit Line | shared charge | BL voltage 변화 (~100 mV) | Capacitive divider |
| 5. Sense Amp | BL, BL_ref | full-swing digital | Differential gain, offset, mismatch |
| 6. Column Mux | column sel | 1-bit data | logic + RDS_on |
| 7. IO buffer | digital data | DQ pin (driven) | Driver Z, slew, eye, ODT |

## 2. 어느 부분을 어떤 방법으로?

각 블록에 어떤 시뮬레이션 패러다임이 맞는지는 "이 블록의 동작이 전압·전류 값에 직접 의존하는가"라는 질문으로 판단할 수 있습니다. command decoder나 refresh counter처럼 순수한 디지털 로직은 전압을 알 필요가 없으므로 digital sim으로 충분합니다. WL driver는 VPP까지 올라가는 전압 천이와 큰 capacitance load가 핵심이므로 RNM이 필요합니다. sense amplifier는 수십 mV의 차이를 감지하는 DRAM의 심장으로, 대량 검증은 RNM으로 하되 트랜지스터 mismatch 통계는 SPICE Monte Carlo로 sign-off합니다.

| 블록 | 추천 시뮬레이션 | 이유 |
|------|----------------|------|
| Command decoder | **Digital** | 순수 디지털 로직 |
| Mode register | **Digital** | 순수 디지털 로직 |
| Row/Column address decoder | **Digital** | 순수 디지털 로직 |
| Refresh counter | **Digital** | 순수 디지털 로직 |
| Word line driver | **RNM** | Voltage 천이 + 큰 capacitance load |
| **Bit cell** | **RNM (대다수) / SPICE (정밀 검증)** | Charge sharing 물리 |
| **Sense amplifier** | **SPICE 정밀 / RNM 대량** | DRAM의 심장. 정확도 매우 중요 |
| Bit line precharge | **RNM** | Voltage level 결정 |
| Column mux | **RNM** | Voltage 전달 |
| **DLL / PLL** | **SPICE / RNM hybrid** | Jitter, lock behavior 필요 시 SPICE |
| **VPP / VBB pump** | **SPICE** | 정확한 voltage level 필요 |
| IO buffer | **RNM 대량 / SPICE 정밀** | Signal integrity 필요 시 SPICE |
| **DFI interface** | **Digital** | Controller와의 디지털 계약 |
| ZQ cal FSM | **Digital + RNM** | FSM digital, 저항 측정 RNM |

## 3. 검증 시나리오 #1 — "ACT → RD → PRE 한 cycle 동작 확인"

```
TB (SV) → ACT command → DRAM
         (digital)
              │
              ▼
        Internal signals (mostly digital)
              │
              ▼
        Word line activation
        ← RNM/AMS boundary 시작
              │
              ▼
        Bit line voltage development
        (RNM: charge sharing)
              │
              ▼
        Sense amp activation
        (RNM 또는 SPICE)
              │
              ▼
        Data latched
        ← Digital boundary 복귀
              │
              ▼
        IO buffer drives DQ
              │
              ▼
        TB checks DQ value (digital)
```

핵심 checkpoint:

1. **t_RCD 만족**: ACT부터 RD까지 ≥ t_RCD ns
2. **BL voltage 발달**: WL high 후 sense margin (≥ 80 mV in DDR5) 확보
3. **Sense amp 활성화 timing**: BL 발달 후 충분한 sensing window
4. **DQ valid**: t_AA 후 데이터 valid

## 4. 검증 시나리오 #2 — "tRCD margin 검증"

### 핵심 질문

> WL이 충분히 발달했을 때 sense amp가 활성화되는가? **t_RCD를 최소값으로 줄이면 어디서 fail 하는가?**

### 분해

| 측정 항목 | 어디서 보나? | 어떤 패러다임? |
|---|---|---|
| ACT 시점 timestamp | digital command interface | Digital |
| WL voltage trajectory | RNM signal | RNM |
| WL 발달 완료 시점 (90% VPP) | RNM signal threshold | RNM |
| BL voltage 발달 곡선 | RNM signal | RNM |
| Sense amp activation timestamp | digital control | Digital |
| Read fail 여부 | TB scoreboard | Digital |

### 가장 worst case는 어디?

- WL load capacitance가 큰 row (배선 길고, fan-out 많은 row)
- WL driver의 process slow corner
- Cell capacitance가 작은 cell (leakage 누적)
- Temperature high (leakage 큼)

→ 이 corner는 **SPICE로 한 번 더 검증**, 나머지는 RNM Monte Carlo.

## 5. Testbench Stimulus 측 — SV로 작성

```systemverilog
class dram_stim_seq;
  task automatic activate(int row);
    drive_command(CMD_ACT);
    drive_address(row);
    @(posedge ck);
  endtask

  task automatic read(int col);
    drive_command(CMD_RD);
    drive_address(col);
    @(posedge ck);
  endtask

  task automatic check_dq(logic [7:0] expected);
    @(posedge ck);
    assert (dq === expected)
      else `uvm_error("DRAM_RD",
                       $sformatf("DQ mismatch: got %h, expected %h", dq, expected))
  endtask
endclass
```

> UVM agent까지 만들 필요는 보통 없음 — 간단한 SV class 또는 module-level TB로 충분. RNM 검증은 inline TB가 더 흔합니다.

## 6. RNM/SPICE 경계 — 어떻게 잇나

### 6.1 RNM 단독 (대부분의 시나리오)

```
[TB SV] → [Digital RTL] → [RNM blocks: WL/BL/SA/IO] → [DQ logic check]
```

장점: 단일 simulator. 빠름. 디버그 쉬움.

### 6.2 RNM + SPICE corner (sign-off)

```
[TB SV] → [Digital RTL] → [RNM blocks: WL/BL/IO]
                              │
                              ▼
                          [SPICE: 1개 SA]  ← critical block만
                              │
                              ▼
                          [SA digital output]
```

VCS-AMS / Spectre-XPS 같은 도구가 두 영역을 자동 동기화. 그러나 SPICE 영역이 커지면 속도가 급락 — 한 번에 한 SA만 SPICE로.

## 7. 대표 문제 — Sense Margin 계산 + 검증 stage 식별

### 문제

DDR5 cell:

- V_cell ('1') = 1.1 V
- V_cell ('0') = 0.0 V
- C_cell = 25 fF, C_bl = 200 fF, V_BL_pre = 0.55 V

(a) Read '1' 시 BL 변화량은? (b) Read '0' 시 BL 변화량은? (c) Sense margin은? (d) 다음 중 sense margin 보장이 가장 어려운 stage는?

- ① ACT command 디코딩
- ② WL 활성화 timing
- ③ BL charge sharing
- ④ Sense amp activation
- ⑤ DQ output

### 풀이

(a) Read '1':
```
q_cell = 25e-15 × 1.1 = 27.5e-15 C
q_bl   = 200e-15 × 0.55 = 110e-15 C
v_shared = (27.5 + 110) / (25 + 200) = 137.5 / 225 ≈ 0.611 V
ΔBL = 0.611 - 0.55 = +0.061 V (+61 mV)
```

(b) Read '0':
```
q_cell = 0
q_bl   = 110e-15 C
v_shared = 110 / 225 ≈ 0.489 V
ΔBL = 0.489 - 0.55 = -0.061 V (-61 mV)
```

(c) Sense margin = ±61 mV (대칭).

(d) **④ Sense amp activation** — 61 mV는 매우 작아 sense amp offset(σ ≈ 15~20 mV at 5nm)에 직접 노출됨. ①·②·⑤는 digital/RNM으로 충분히 marginal한 case 검출 가능하나, SA offset의 통계는 Monte Carlo 필요.

### 통찰

- Sense margin은 **C_bl / C_cell 비율**이 클수록 줄어듦 → 1Gb 이상 DRAM에서 매우 challenging
- 1차 검증: RNM (functional)
- 2차 검증: RNM Monte Carlo (offset σ 효과)
- 3차 검증: SPICE Monte Carlo (corner 통계 sign-off)

## 8. 패러다임 결정 체크리스트

새 블록을 만났을 때:

```
□ 외부 핀에 닿는가? (DQ, CK, CA, DQS) → mixed-signal (RNM 최소)
□ Voltage trajectory가 중요한가? → RNM
□ Pelgrom mismatch가 결과를 좌우하는가? → SPICE Monte Carlo (또는 RNM MC + SPICE corner)
□ Jitter/phase noise가 중요한가? → SPICE
□ Charge pump · regulator? → SPICE
□ FSM/decode/protocol만 있는가? → Digital
□ 수만 트랜지스터 이상인가? → RNM 필수
```

## 9. 흔한 함정

| 함정 | 결과 | 대응 |
|------|------|------|
| Pure digital sim만으로 sign-off | Silicon fail (SA offset, eye 등) | 최소 RNM corner check |
| Single SA SPICE만으로 sign-off | Statistical fail rate 미평가 | SPICE Monte Carlo |
| RNM 모델 update 누락 | SPICE 결과와 괴리 | Process/temp 변경 시 RNM 재추출 |
| Sensitive corner 빼먹음 | Worst case fail 누락 | SS/FF + hot/cold + slow/fast clk |
| WL load capacitance 단순화 | Margin overestimate | 실제 layout의 worst row 반영 |

## 핵심 정리

1. DRAM read 경로 7 stage 중 **WL/BL/SA/IO 4개**가 mixed-signal
2. Digital: command/decoder/MR/refresh/FSM. RNM: WL/BL/IO 대량. SPICE: SA offset/VCO/charge pump.
3. tRCD margin 검증은 **RNM voltage trajectory + digital timing trigger** 결합
4. Sense margin은 1Gb급 DRAM에서 ±60~100 mV — SA offset (σ ≈ 15~20 mV at 5nm)과 직접 충돌
5. Sign-off는 SPICE Monte Carlo 필수 — RNM 단독 불가

## 더 읽을거리

- 다음: [Ch07. Deep Dive — DLL RNM](07_deepdive_dll_rnm.md)
- Rabaey, *Digital Integrated Circuits: A Design Perspective* — DRAM 챕터
- JEDEC JESD79-5C (DDR5) — sense window 관련
- 퀴즈: [Ch06 퀴즈](quiz/ch06_quiz.md)
