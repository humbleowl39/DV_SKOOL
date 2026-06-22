---
title: "Module 03 — Memory Interface / PHY"
---

:::tip[학습 목표]
이 모듈을 마치면 (**LPDDR5 PHY 를 주축**으로, server DDR5 PHY 를 비교축으로):

- **Diagram** PHY의 주요 블럭(PLL, CK/WCK, DQ/CA TX/RX, Training engine, 임피던스 보정)을 그릴 수 있다.
- **Distinguish** LPDDR5 의 CK(명령용 저속) + WCK(데이터용 고속, WCK:CK = 2:1/4:1) 2-클럭 구조를 server DDR5 의 단일 CK + DQS 구조와 구분할 수 있다.
- **Apply** LPDDR5 Training(CBT Mode1/2, WCK2CK leveling, DQ/Write/Read)의 순서와 목적을 시나리오에 매핑하고, DDR5 CA Training 과 비교할 수 있다.
- **Analyze** PVT(Process/Voltage/Temperature) 변동이 timing margin에 미치는 영향과 보정 메커니즘을 분석할 수 있다.
- **Distinguish** CTLE / DFE 같은 equalization 기법과 적용 위치(Write/Read), 그리고 DVFSC 저gear 에서의 EQ 완화를 구분할 수 있다.
- **Compare** LPDDR5 의 point-to-point single-rank 종단을 server DDR5 DIMM 의 multi-rank RTT_NOM/WR/PARK 와 비교할 수 있다.
:::
:::note[사전 지식]
- [Module 01-02](../01_dram_fundamentals_ddr/) (cell, MC scheduler)
- 아날로그/디지털 인터페이스 기본 (signal integrity 개념)
- Eye diagram, jitter 일반 지식
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _가끔만_ 깨지는 메모리

당신의 SoC. 메모리 functional test 통과. 그런데 _수 시간 후_ random data corruption. 재현 어려움.

원인은 **온도 변화로 인한 PHY timing 변동**입니다. boot 시 25°C 에서 training 을 완료하면 모든 lane 의 delay tap 이 수렴합니다. 그런데 SoC 가 부하 상태에서 75°C 까지 가열되면 PCB trace 의 전파 지연이 ~5 ps 변동합니다. DDR5 의 데이터 유효 윈도우는 ~208 ps 이므로 5 ps 변동은 전체 윈도우의 약 2.4% 에 해당하며, 윈도우 가장자리에 걸쳐 있던 샘플링 포인트가 유효 범위 밖으로 밀려납니다. 그 결과 "가끔 wrong bit" — 재현이 어렵고 랜덤 데이터 테스트로는 잡히지 않는 silent corruption 이 됩니다.

**해법**: _운영 중에도 주기적 calibration_ — ZQ Calibration, periodic DQ training. PHY 가 _자기 진단_ 하고 _재조정_ 함.

Module 02 에서 MC 가 발행한 ACT/RD/WR/PRE 명령은 _전기 신호_ 가 되어 PCB 트레이스를 건너 DRAM 에 도달해야 합니다. DDR4 3200 MT/s 의 _데이터 유효 윈도우_ 는 ~312 ps, DDR5 4800 MT/s 는 ~208 ps. PCB 배선 차이, PVT 변동, 크로스토크가 그 윈도우를 더 좁힙니다. **PHY 의 임무는 이 ns 도 안 되는 시간 안에서 정확한 샘플링을 보장하는 것** — 그리고 그것은 정적 설정으로는 불가능합니다. **Training 실패 = silent corruption** — silicon 이 동작하는 것처럼 보이지만 데이터 변조.

이 모듈을 건너뛰면 timing parameter 의 의미가 _ns 단위 사이클 카운트_ 에 머무르고, 왜 boot 시 BL2 가 수십 KB 의 training 코드를 돌리는지, 왜 운영 중에도 임피던스/타이밍 calibration 이 주기적으로 돌아야 하는지 답할 수 없습니다.

:::note[이 모듈의 주축 — LPDDR5 PHY 와 WCK]
이 모듈은 **LPDDR5 PHY 를 주축**으로 설명합니다. LPDDR5 의 정체성은 **2개의 클럭**입니다 — 명령/주소용 저속 차동 클럭 **CK** 와, 데이터용 고속 클럭 **WCK**. WCK:CK 비는 gear 에 따라 **2:1 또는 4:1** 이고, 데이터 스트로브는 DDR5 의 DQS 대신 **WCK/RDQS** 가 맡습니다. 또 CA 버스가 **CA[6:0] 단일종단 다중사이클** 이라 **CBT(Command Bus Training)** 가 필수입니다. 비교축인 **server DDR5** 는 단일 CK + DQS, CA[13:0] 2-cycle 구조입니다. 아래 scenario 의 ps 수치는 DDR5 4800 기준 예시이며, LPDDR5X 의 고gear 도 동급 이상으로 윈도우가 좁습니다.
:::

---

## 2. Intuition — 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**Memory PHY** ≈ **고속 도로의 톨게이트 + 차량 정렬 (training)**.<br>
DDR 의 GHz 동작은 strobe 정렬, drive strength, ZQ calibration, training 같은 PHY 레이어 작업이 매 순간 보정해 가능합니다. **컨트롤러보다 PHY 가 더 미묘한 영역** — 같은 chip 이라도 온도가 바뀌면 전파 지연이 바뀌어 어제 맞춘 값이 오늘 안 맞을 수 있습니다.
:::
### 한 장 그림 — PHY 는 timing 을 _주기적으로 다시 맞추는_ layer

```d2
direction: down

MC: "Memory Controller (logic)\nACT/RD/WR/PRE 명령 시퀀스"
PHY: "PHY" {
  direction: down
  PLL: "PLL — DDR clock\n(수 GHz)"
  TX: "CA/DQ/DQS TX\ndelay tap → pin"
  RX: "DQ RX (delay tap + VREF)\nDQS RX (90° shift, read)"
  ZQ: "ZQ — 임피던스 보정\n(240Ω 기준)"
  ODT: "ODT —\nRTT_NOM/WR/PARK"
  EQ: "CTLE / DFE — EQ (DDR5)"
  TR: "Training engine\n· WL → Gate → DQ → Eye → VREF\n· DDR5: + CA Training, DFE coef\n· LPDDR5: + WCK2CK, CBT\n· 주기 retraining (PVT drift)\nresult → MR / delay-tap reg"
  PLL -> TX
  PLL -> RX
  TR -> TX
  TR -> RX
  TR -> EQ
}
DRAM: "DRAM device" {
  DLL: "DLL (DQS-CK 정렬, DDR4)"
  SENSE: "ODT, sense amp"
}
MC -> PHY
PHY -> DRAM: "PCB trace\n(수 cm, ps 단위 차이)"
```

### 왜 이렇게 설계됐는가 — Design rationale

세 물리적 사실이 _동시에_ 작동합니다.

1. **유효 윈도우가 ps 단위로 좁다** → 정적 setup/hold 로 cover 불가능 → _샘플링 시점_ 자체를 chip-by-chip / lane-by-lane 으로 학습해야 함.
2. **PVT 가 시간에 따라 drift 한다** → 한 번 학습한 값이 영원히 맞을 수 없음 → 주기적 ZQ + retraining 필요.
3. **GHz 신호는 채널 손실이 크다** → ISI 가 eye 를 닫음 → 선형/비선형 등화 (CTLE + DFE) 필요.

이 셋이 PHY 의 모든 기능 — DLL/PLL, training engine, ZQ, ODT, EQ — 의 존재 이유입니다.

---

## 3. 작은 예 — Write Leveling 한 byte lane 을 step-by-step 으로 맞추기

가장 단순한 시나리오. 64-bit DDR4 모듈에서 _byte lane 0_ 의 Write Leveling(쓰기 레벨링 — 각 데이터 묶음의 strobe 시점을 클럭에 맞춰 정렬하는 보정) 한 lane 을 추적합니다.

용어 먼저 — **PHY**(Physical Layer, 물리 계층 — MC 의 논리적 명령을 실제 전기 신호로 바꿔 핀으로 내보내고, 받은 신호를 다시 0/1 로 판정하는 회로 블록). **byte lane**(바이트 레인 — DQ 8개를 한 묶음으로 다루는 데이터 경로 단위; 64-bit 버스 = 8 lane). **DQ**(Data — 실제 데이터가 흐르는 핀), **DQS**(Data Strobe — DQ 가 "지금 유효하다"고 알려 주는 동반 클럭 신호), **CK**(Clock — 시스템 기준 클럭). **delay tap**(딜레이 탭 — 신호를 아주 조금씩 늦추는 조절 눈금; 한 tap 이 약 5~10 ps). **MRS**(Mode Register Set — DRAM 의 동작 모드를 설정하는 명령으로, 여기서는 DRAM 을 training 전용 모드로 진입시키는 데 씀).

### 사전 상황

- MC 가 lane 0 의 DQS 출력 delay 를 0 tap 부터 시작.
- DRAM 은 Write Leveling mode (MRS 로 진입). DRAM 은 **CK 의 rising edge 에서 DQS 를 sample** 하여 그 값을 DQ 로 돌려보냅니다.

### 단계별 추적

```
   delay tap   DQS edge vs CK rising      DRAM 이 보는 DQS value     DQ reply
   ──────     ──────────────────────     ──────────────────────     ─────────
     0       DQS 가 CK 보다 _많이_ 빠름        '0'                    0x00 (= 0)
     1       조금 덜 빠름                      '0'                    0x00
     2       조금 덜 빠름                      '0'                    0x00
     3       조금 덜 빠름                      '0'                    0x00
     4       살짝 빠름                          '0'                    0x00
     5       (전환점) DQS rising edge 가 CK 와 거의 정렬   '1' (or '0')   0x01 ⭐
     6       이제 DQS 가 CK 와 정렬 또는 약간 늦음          '1'           0xFF
     7       늦음                                          '1'           0xFF
     ...
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | MC | `MRS` 로 DRAM 을 Write Leveling mode 진입 | DRAM 의 정상 RD/WR 동작 정지, sample-and-reply mode 활성 |
| ② | MC PHY | lane 0 의 DQS 출력 delay tap = 0 으로 set | 가장 이른 위상부터 시작 |
| ③ | MC | DQS 토글 출력 → DRAM | DRAM 의 sample 동작 트리거 |
| ④ | DRAM | `posedge CK` 시점의 DQS 값을 latch → DQ 에 reply | sample 시점의 DQS 위상을 reflect |
| ⑤ | MC | DQ 값을 read → '0' 이면 _DQS 가 CK 보다 빠름_ → tap 증가 | 더 늦추면 정렬에 가까워짐 |
| ⑥ | MC | tap = 1, 2, 3, 4 ... 반복하며 DQ 변화 monitor | 전환점 탐색 |
| ⑦ | MC | DQ 가 0 → 1 로 바뀐 첫 tap (`tap = 5`) 을 lane 0 의 _최적 delay_ 로 채택 | DQS 의 rising edge 가 CK 와 정렬된 시점 |
| ⑧ | MC | lane 1, 2, ... 7 도 같은 절차 (각 lane 의 PCB 길이가 다름) | per-lane 보정 |
| ⑨ | MC | `MRS` 로 Write Leveling mode exit | 정상 RD/WR 가능 |

```c
// Write Leveling pseudocode (per lane)
function int wl_train_lane(int lane) {
    int prev_dq = 0;
    for (int tap = 0; tap < MAX_TAP; tap++) {
        phy.set_dqs_delay(lane, tap);
        toggle_dqs(lane);
        int dq = sample_dq_reply(lane);   // 0 or 1
        if (prev_dq == 0 && dq == 1)      // 0→1 transition
            return tap;                    // optimal delay found
        prev_dq = dq;
    }
    return ERROR_NOT_FOUND;
}
```

:::note[여기서 잡아야 할 두 가지]
**(1) DQS-CK 정렬은 _lane 별로 다른 delay tap_ 을 요구한다.** PCB 배선 길이가 lane 마다 mm 단위로 달라서 — 한 lane 5 tap, 다른 lane 7 tap 처럼. 정적 설정으로는 절대 cover 불가.<br>
**(2) Training 결과는 _런타임 데이터_ 다.** boot 시 BL2 가 학습한 tap 값이 chip-specific / 온도-specific 이라 BootROM 에 hardcoding 할 수 없습니다. DRAM 도 retraining 시 다른 값이 나옵니다.
:::
---

## 4. 일반화 — PHY 블록 과 Training 순서

### 4.1 PHY 의 기능 블록

| 블록 | 책임 | 정확도 단위 |
|------|------|------|
| **PLL** | system clock → DDR clock 합성 | jitter ps |
| **CK / WCK 생성** (LPDDR5) | CK(명령용 저속) + WCK(데이터용 고속), WCK:CK = 2:1/4:1 | ps |
| **DLL** (DDR4 only) | DRAM 내부 DQS-CK 정렬 (DDR5/LPDDR5 는 DLL-less 경향, PHY 가 처리) | ps |
| **CA / DQ / DQS(WCK) TX/RX** | 신호 driver / receiver | mV / ps |
| **Per-lane delay tap** | DQ/DQS(WCK) 위상 조정 | tap (~5-10 ps each) |
| **Internal VREF** (LPDDR5) | 수신 판정 기준 전압 (LPDDR5 는 내부 Vref) | mV |
| **ODT** | 종단 임피던스 (DDR5 DIMM: RTT_NOM/WR/PARK / LPDDR5: point-to-point 단순) | Ω |
| **임피던스 보정 engine** | 출력 임피던스 보정 (240Ω 기준) | Ω, % |
| **EQ (CTLE + DFE)** | ISI / 고주파 손실 보상 (고gear 필수, 저gear 완화) | dB |
| **Training engine** | LPDDR5: CBT → WCK2CK → DQ/Write/Read / DDR5: CA → WL → Gate → DQ → Eye → VREF | per-lane |

### 4.2 Training 시퀀스 — 표준 순서

**LPDDR5(주축)** 는 단계가 가장 많습니다 — CBT 로 CA 정렬, WCK2CK 로 데이터 클럭 정렬을 먼저 잡은 뒤 DQ/Write/Read 를 맞춥니다. 비교를 위해 server DDR5 열을 함께 둡니다.

| Training | 목적 | 시점 | LPDDR5 (주축) | DDR5 (비교) |
|---------|------|------|------|------|
| **CBT (Command Bus Training, Mode1/2)** | CA[6:0] 단일종단 다중사이클 정렬 | init | ✓ (필수) | — |
| **CA / CS Training** | CA[13:0] 2-cycle 버스 정렬 | init | — | ✓ |
| **WCK2CK Leveling** | WCK-CK 위상 정렬 (LPDDR5 고유) | init / gear 전환 시 | ✓ (고유) | — (DQS 사용) |
| **Write Leveling** | 데이터 스트로브-to-CK 스큐 보정 (Write) | init | ✓ | ✓ |
| **Read Gate Training** | 스트로브 수신 시작 타이밍 결정 | init | ✓ | ✓ |
| **Read/Write DQ Training** | DQ-to-스트로브 비트별 지연 보정 | init | ✓ | ✓ |
| **Read Eye Training** | 데이터 유효 윈도우 중앙 | init | ✓ | ✓ |
| **VREF Training (internal Vref)** | 수신 판정 기준 전압 최적화 | init | ✓ (내부 Vref) | ✓ |
| **DFE coef Training** | Decision Feedback EQ 계수 | init | ✓ (고gear) | ✓ |
| **임피던스 보정 (Init/Long/Short)** | 출력 임피던스 | init + 주기 | ✓ | ✓ |
| **Periodic Retraining** | 온도 변화 / DVFSC gear 전환 보상 | runtime | ✓ | ✓ |

핵심 차이: LPDDR5 는 데이터 클럭이 별도의 고속 **WCK** 라서 **WCK2CK Leveling**(WCK 와 CK 위상 정렬)이 LPDDR5 고유 단계로 추가되고, gear(DVFSC)가 바뀌어 WCK:CK 비가 달라질 때마다 재정렬이 필요합니다. server DDR5 는 단일 CK + DQS 라 이 단계가 없습니다.

### 4.3 PVT drift 와 retraining 의 동기

```
                Training 결과 (한 시점)
                          │
                          ▼
                 |◄──── 유효 margin ────►|
   eye 중심  ──── ●  ─────────────────  ●  ──── eye 가장자리
                          │
   온도 ↑ → 전파지연 변경 │ → eye 가 좌/우로 shift
   전압 droop → drive 강도 변경 → eye 중앙 이동
                          ▼
                 새로운 eye 중심을 다시 학습
                          │
                          ▼
                 → ZQ Short / periodic retraining
```

여기서 **eye**(아이 다이어그램 — 수신 신호 파형을 한 비트 구간마다 겹쳐 그렸을 때 가운데에 생기는 눈 모양의 빈 공간; 이 "눈"이 넓을수록 0/1 을 안정적으로 구분할 시간·전압 여유가 크다)와 **margin**(마진 — 정확히 샘플링할 수 있는 안전 여유)이 핵심 개념입니다. **PVT**(Process/Voltage/Temperature — 공정 편차·전압·온도; 칩마다, 순간마다 신호 속도를 바꾸는 세 변동 요인)도 함께 짚어 둡니다. Training 은 특정 시점의 PVT 조건을 기준으로 margin 을 확보하는 작업입니다. 온도가 변하거나 전압이 흔들리면 그 기준이 어긋나므로, 한 번 학습한 결과를 영구히 재사용할 수는 없습니다. 그래서 ZQ Short 는 수십 초마다 impedance 를 재조정하고, full retraining 은 주기적으로 또는 온도가 임계값을 초과할 때 새로 trigger 됩니다.

온도가 _왜_ 전파 지연을 바꾸는지는 트랜지스터·배선의 물리에 뿌리가 있습니다. 신호가 게이트와 PCB trace 를 통과하는 속도는 캐리어 이동도(carrier mobility)와 배선 저항에 달려 있는데, 온도가 오르면 실리콘 격자의 열진동이 심해져 캐리어가 더 자주 산란되어 **이동도가 떨어지고**(트랜지스터가 느려짐), 동시에 금속 배선의 **저항이 커져** RC 지연이 늘어납니다. 두 효과가 합쳐져 부팅 시 25 °C 에서 맞춘 delay tap 이 75 °C 에서는 신호 도착 시각을 ps 단위로 밀어 버립니다 — eye 가 좌/우로 shift 하는 것입니다. 이 drift 가 윈도우 가장자리를 넘어서기 전에 다시 측정해 tap 을 옮겨 주는 것이 retraining 이 _주기적_ 이어야 하는 근본 이유입니다.

---

## 5. 디테일 — 신호, ODT, DLL/PLL, EQ, ZQ, BL2

### 5.1 DDR 신호 구성

```
Memory Controller / PHY ←→ DRAM Device

== LPDDR5 (주축) ==

Clock:
  CK_t/CK_c (명령용, 저속 차동 클럭)
  WCK_t/WCK_c (데이터용, 고속 클럭) — WCK:CK = 2:1 또는 4:1 (gear 의존)
  → LPDDR5 의 정체성: 명령(느림)과 데이터(빠름) 클럭이 분리됨

Command/Address (CA) Bus:
  CA[6:0]  (단일종단, 다중사이클로 명령/주소 전송) → CBT 필수
  CS       (Chip Select)

Data Bus (per byte lane):
  DQ[7:0]   (데이터, 8-bit per lane)
  WCK / RDQS (데이터 스트로브 역할 — DDR5의 DQS 대신 WCK 계열 사용)
  DMI       (Data Mask / Inversion)

== DDR5 (server 비교) ==

Command/Address (CA) Bus:
  CK_t/CK_c (단일 차동 클럭)
  CS#      (Chip Select)
  CA[13:0] (2-cycle 멀티플렉싱)
  BG[2:0]  (Bank Group)

Data Bus (per byte lane):
  DQ[7:0]   (데이터, 8-bit per lane)
  DQS/DQS#  (데이터 스트로브, 차동)
  DM/DBI    (데이터 마스크 / Data Bus Inversion)

  Sub-Ch A: 4 lanes × 8 = 32-bit
  Sub-Ch B: 4 lanes × 8 = 32-bit
```

### 5.2 DQS 와 DQ 의 관계

데이터 스트로브는 DDR 데이터 버스에서 DQ 가 언제 유효한지를 알려 주는 기준 클럭 역할을 합니다. **server DDR5 는 이 역할을 DQS** 가, **mobile LPDDR5(주축)는 고속 데이터 클럭인 WCK(읽기 시 RDQS)** 가 맡습니다 — 명칭은 다르지만 DQ 정렬 원리는 동일합니다. Write 경로에서는 MC 가 스트로브를 DQ 와 center-aligned 로 정렬하여 전송하고, DRAM 은 스트로브 에지에서 DQ 를 샘플링합니다. Read 경로에서는 DRAM 이 스트로브를 DQ 와 edge-aligned 로 내보내고, MC/PHY 는 이를 90° 지연시켜 DQ 의 중앙에서 샘플링합니다. Write 와 Read 의 스트로브-DQ 관계가 서로 다르다는 점이 Training 을 방향별로 구분해야 하는 이유입니다. LPDDR5 에서는 추가로 이 데이터 클럭(WCK)을 명령 클럭(CK)에 맞추는 **WCK2CK leveling** 이 선행되어야 합니다.

이 center/edge 의 비대칭은 "누가 샘플링하는 쪽인가" 에서 나옵니다. 샘플링하는 쪽은 안정적으로 데이터를 잡으려면 strobe 에지를 데이터 비트의 **한가운데(center)** — setup/hold 마진이 양쪽으로 가장 넓은 지점 — 에 두고 싶어 합니다. **Write** 에서는 _DRAM_ 이 샘플링하는 쪽인데, DRAM 안에는 DQS 를 옮길 마땅한 지연 회로가 없습니다. 그래서 보내는 쪽인 MC 가 미리 DQS 를 데이터 중앙에 맞춰(center-aligned) 보내 줍니다 — DRAM 은 받은 에지에서 곧장 latch 만 하면 됩니다. 반대로 **Read** 에서는 _MC/PHY_ 가 샘플링하는 쪽입니다. DRAM 은 회로를 단순하게 두려고 DQS 와 DQ 를 그냥 같은 타이밍, 즉 **edge-aligned** 로 함께 내보냅니다. 받는 MC/PHY 가 DQS 를 90° (≈ 비트 폭의 절반) 지연시켜 데이터 중앙으로 옮긴 뒤 샘플링합니다. 정리하면 — **마진을 만드는 90° 시프트 책임을 항상 "받는(샘플링하는) 쪽"이 진다**는 한 가지 원리에서 Write 의 center-aligned 송신과 Read 의 수신측 90° 시프트가 모두 따라 나옵니다.

```
DDR에서 DQS는 데이터의 "스트로브":

  Write (MC → DRAM):
    MC가 DQS를 DQ와 정렬하여 전송
    DRAM이 DQS 엣지에서 DQ를 샘플링
    → DQS center-aligned with DQ

  Read (DRAM → MC):
    DRAM이 DQS를 DQ와 edge-aligned로 전송
    MC/PHY가 DQS를 90° 지연시켜 DQ 중앙에서 샘플링
    → Read DQS needs 90° phase shift at receiver

  +----+    +----+    +----+    DQS
  |    |    |    |    |    |
  +    +----+    +----+    +---
       ↑         ↑         ↑   DQS edge (Write: DRAM 샘플링)
    +------+  +------+  +------+ DQ
    | D0   |  | D1   |  | D2   |
    +------+  +------+  +------+
         ↑         ↑         ↑  DQS center (Read: MC 샘플링, 90° shift)
```

### 5.3 ODT (On-Die Termination) — 신호 무결성의 핵심

고속 신호는 전송선 끝에서 임피던스 불일치를 만나면 반사가 발생하고, 그 반사파가 원래 신호에 간섭하여 데이터 오류로 이어집니다. 이 문제를 해결하려면 전송선의 임피던스와 동일한 저항으로 종단해야 하는데, DDR2 이전에는 PCB 에 외부 저항을 실장했고 DDR2 이후부터 DRAM 칩 내부에 이 종단 저항을 내장한 것이 ODT 입니다.

여기서 토폴로지가 세대별로 크게 다릅니다. **mobile LPDDR5(주축)는 SoC 와 메모리가 PoP 로 매우 짧게 연결된 point-to-point, single-rank 구성**입니다. 전송선이 짧고 비타겟 rank 가 없으므로 종단 요구가 단순합니다(일반적으로 LPDDR 계열은 DIMM 대비 종단 구조가 단순하다는 토폴로지 기반 일반론). 반면 **server DDR5 는 DIMM 위 multi-rank** 라, 타겟 Rank 가 데이터를 구동하는 동안 비타겟 Rank 의 RTT_PARK(park termination) 를 활성화하는 것이 특히 중요합니다 — 비타겟이 floating 이면 그쪽에서 반사가 발생해 타겟의 eye 가 닫히기 때문입니다. 따라서 RTT_NOM/WR/PARK 의 정교한 조합은 주로 **DDR5 DIMM multi-rank 의 관심사**입니다.

```
문제: 고속 신호가 전송선 끝에서 임피던스 불일치를 만나면
     신호가 반사되어 원래 신호에 간섭 → 데이터 오류

  반사 없는 조건: 소스 임피던스 = 전송선 임피던스 = 종단 임피던스

  DDR 이전: 외부 종단 저항을 PCB에 실장
  DDR2+: DRAM 칩 내부에 종단 저항 내장 = ODT (On-Die Termination)
  → 외부 부품 제거 → PCB 간소화, 비용 절감, 신호 품질 향상

ODT의 동작:

  Write 시 (MC → DRAM):
    +------+    전송선 (Z0=40Ω)    +------+
    |  MC  |========================| DRAM |
    | Ron  |                        | ODT  |
    | 34Ω  |                        | 40Ω  | ← 수신측 종단
    +------+                        +------+
    → 타겟 DRAM의 ODT 활성화 → 반사 방지

  Read 시 (DRAM → MC):
    +------+    전송선 (Z0=40Ω)    +------+
    |  MC  |========================| DRAM |
    | ODT  |                        | Ron  |
    | 40Ω  | ← 수신측 종단         | 34Ω  |
    +------+                        +------+
    → MC측 ODT 활성화

  Multi-Rank에서의 ODT (server DDR5 DIMM):
    Rank 0 (타겟): ODT OFF (데이터 구동 중)
    Rank 1 (비타겟): ODT ON (반사 방지)
    → 비타겟 Rank의 ODT가 더 중요 (park termination)

  LPDDR5 (주축, point-to-point single-rank):
    → 비타겟 rank가 없고 전송선이 짧음 (PoP)
    → 종단 구조가 단순 (토폴로지 기반 일반론)
    → RTT_NOM/WR/PARK 의 multi-rank 조합은 LPDDR5의 관심사가 아님

DDR5 DIMM ODT 설정 (Mode Register, multi-rank 비교):
  RTT_NOM:  Nominal termination (60/120/40/240Ω 등)
  RTT_WR:   Write 시 dynamic termination
  RTT_PARK: 항상 활성화된 park termination
  ODTL (ODT Latency): 명령 대비 ODT ON/OFF 타이밍 정밀 제어
  NT_ODT (Non-Target ODT): 비타겟 Rank ODT 독립 제어
  Per-Pin ODT: DQ 핀별 ODT 값 설정 가능

면접 포인트:
  "ODT는 고속 DDR 버스에서 신호 반사를 방지하는 핵심 메커니즘이다.
   DRAM 내부에 종단 저항을 내장하여 PCB 간소화와 신호 무결성을 동시에 달성한다.
   mobile LPDDR5는 point-to-point single-rank라 종단이 단순한 반면,
   server DDR5 DIMM의 multi-rank 구성에서는 비타겟 Rank의 Park Termination이
   특히 중요하며, RTT_NOM/WR/PARK 세 값의 최적 조합은 시뮬레이션으로 결정한다."
```

### 5.4 DLL / PLL — 클럭 생성과 분배

```
**DLL (Delay-Locked Loop) — DRAM 내부**

목적: 내부 클럭과 외부 CK의 위상을 정렬. 원리: 지연(delay)을 조절하여 피드백 클럭과 기준 클럭의 위상을 맞춤.

```d2
direction: right

CKIN: "외부 CK"
VD: "Variable Delay"
CKIN -> VD
CKOUT: "내부 CK\n(DQS 생성용)"
VD -> CKOUT
PD: "Phase Detector\n(지연 증가/감소)"
CKOUT -> PD: "피드백"
PD -> VD
```

DLL이 하는 일:

- Read 시 스트로브를 CK에 정렬하여 출력
- 온도/전압 변화에 따라 지연을 자동 조절
- DDR4: DLL 필수
- DDR5 / LPDDR5(주축): DLL-less 경향 (PHY측에서 위상 처리)
  · LPDDR5는 데이터 클럭 WCK를 명령 클럭 CK에 맞추는
    WCK2CK Training으로 정렬을 수행 (DLL 대신)

왜 DDR5 는 DRAM 내부 DLL 을 제거했는가? DLL 은 _고정된 동작 주파수_ 에서 한 클럭 주기를 잘게 나눠 위상을 맞추는 회로라, 동작 주파수가 넓게 바뀌거나 런타임에 DVFS 로 주파수를 갈아탈 때마다 lock 을 다시 잡아야 해서 유연성이 떨어집니다. 게다가 항상 켜져 있어 무시 못 할 전력을 소모합니다. DDR5 는 동작 범위가 훨씬 넓고 저전력이 중요해졌기 때문에, 위상 정렬을 DRAM 내부의 고정 회로(DLL)에서 떼어내 **MC/PHY 측의 training 으로** 옮겼습니다 — PHY 가 측정해 학습한 delay tap 으로 DQS-CK 관계를 맞추므로, 주파수가 바뀌면 그 주파수에서 다시 학습하면 됩니다. 즉 "고정 하드웨어 정렬" 을 "측정 기반 소프트웨어 정렬" 로 바꿔 넓은 주파수 범위와 DVFS 대응을 얻은 것입니다.

**PLL (Phase-Locked Loop) — MC/PHY 내부**

목적: 시스템 클럭에서 DDR 클럭과 그 분주/배수 클럭 생성. 원리: VCO(전압제어발진기)의 주파수를 조절하여 기준 주파수에 Lock.

```d2
direction: down

SYS: "System CLK"
PFD: "PFD"
SYS -> PFD
LF: "Loop Filter"
PFD -> LF
VCO: "VCO"
LF -> VCO
CKOUT: "CK 출력"
VCO -> CKOUT
DIV: "Divider (÷N)"
VCO -> DIV
DIV -> PFD
```

PLL이 하는 일:

- 200 MHz 시스템 클럭 → 1600 MHz DDR 클럭 생성 (×8)
- 90° 위상 시프트된 클럭 생성 (Read DQS 샘플링용)
- Jitter 최소화 → Eye Diagram 품질에 직접 영향

DLL vs PLL 차이:
  | 항목       | DLL                | PLL              |
  |-----------|--------------------|------------------|
  | 동작       | 지연 조절 (위상만) | 주파수 합성       |
  | 위치       | DRAM 내부          | MC/PHY 내부       |
  | 주 목적    | 스트로브-CK 정렬   | DDR 클럭 생성     |
  | DDR4       | 필수               | 필수             |
  | DDR5/LPDDR5| DLL-less 경향(제거) | 필수 (더 복잡)    |
  ※ LPDDR5는 DLL 대신 WCK2CK Training으로 WCK-CK 정렬
```

### 5.5 Equalization — 고속 신호 보상 기법

고속 동작에서는 비트 간격(UI)이 극히 좁아집니다 — server DDR5 4800 MT/s 기준 약 208 ps, 그리고 **mobile LPDDR5X 의 고gear** 도 동급 이상으로 좁아집니다. 이 좁은 간격 때문에 이전 비트의 잔여 신호가 현재 비트와 겹치는 ISI(Inter-Symbol Interference) 가 심각해져, 수신단의 eye 다이어그램이 거의 닫힙니다. 이를 보상하지 않으면 데이터를 올바르게 샘플링할 수 없습니다. Equalization 은 이 eye 를 복원하는 기법입니다. CTLE 는 아날로그 필터로 채널의 고주파 감쇠를 보상하지만 노이즈도 함께 증폭한다는 단점이 있습니다. 그 이유는 CTLE 가 **선형(linear) 필터**이기 때문입니다 — CTLE 는 "신호" 와 "노이즈" 를 구분하지 못하고, 그저 _고주파 성분_ 을 무차별적으로 부스트합니다. 채널이 깎아먹은 신호의 고주파를 되살리는 그 동작이, 같은 대역에 있는 고주파 노이즈와 crosstalk 도 똑같은 비율로 키웁니다. 결과적으로 신호 대 노이즈 비(SNR)는 거의 개선되지 않고 진폭만 커집니다. 반면 DFE 는 이미 결정된 이전 비트들의 ISI 기여분을 디지털로 빼는 방식이라 노이즈를 증폭하지 않으며 — _이미 판정된 값_ 만 쓰므로 빼는 양에 노이즈가 섞이지 않습니다 — CTLE 와 상호 보완적으로 동작합니다. DDR5/LPDDR5 에서 두 기법을 함께 사용하는 이유가 바로 이 상보 관계 때문입니다. 단, **LPDDR5 의 DVFSC 저gear(낮은 주파수)** 에서는 UI 가 넓어져 ISI 부담이 줄므로 EQ 요구가 완화됩니다 — gear 에 따라 EQ 세기를 조절할 수 있다는 점이 mobile 의 전력 이점입니다.

```
문제: DDR5 4800+ MT/s에서 채널 손실(ISI, 크로스토크)이 심각
     → 수신단에서 Eye가 거의 닫힘 → 보상 없이는 데이터 수신 불가

  ISI (Inter-Symbol Interference):
    이전 비트의 잔여 신호가 현재 비트에 간섭
    → 고속일수록 심각 (비트 간격이 좁아지므로)

CTLE (Continuous-Time Linear Equalizer):
  - 수신단에 아날로그 필터 적용
  - 고주파 성분을 증폭하여 채널 손실 보상
  - 간단하지만 노이즈도 함께 증폭하는 단점

  채널 응답:    ─────────╲  (고주파 감쇠)
  CTLE 보상:    ─────────╱  (고주파 부스트)
  결과:         ───────────  (평탄화)

DFE (Decision Feedback Equalizer):
  - 이미 결정된 비트 값을 이용하여 ISI 제거
  - 현재 비트에서 이전 비트의 예상 간섭을 빼줌
  - 노이즈를 증폭하지 않는 장점 (CTLE와 상호 보완)

  수신 신호 = 현재 비트 + h1×(이전 비트) + h2×(2번 전 비트) + ...
  DFE 보상: 수신 신호 - h1×(이전 결정값) - h2×(2번 전 결정값)
  → ISI 성분 제거 → 깨끗한 Eye 복원

  DDR5에서의 적용:
  - DRAM 수신단(Write 경로): DFE 1-tap 이상 지원
  - PHY 수신단(Read 경로): CTLE + DFE 조합
  - Training으로 DFE 계수(h1, h2) 최적화

면접 포인트:
  "DDR5 고속에서는 채널 ISI로 Eye가 닫히므로 Equalization이 필수이다.
   CTLE는 아날로그 고주파 부스트, DFE는 이전 비트의 ISI를 디지털로
   제거한다. DRAM과 PHY 양측에서 적용하며, Training으로 계수를 최적화한다."
```

### 5.6 Training — 왜 필요한가?

고속 데이터 유효 윈도우는 ps 단위로 좁습니다(server DDR5 4800 MT/s ~208 ps, LPDDR5X 고gear 도 동급 이상, 직전 세대 DDR4 3200 MT/s 는 ~312 ps). 이 좁은 윈도우 안에서 정확히 샘플링해야 데이터가 정상입니다. 그런데 PCB 배선 길이는 byte lane 마다 mm 단위로 다르고, 온도와 전압 변동은 트랜지스터의 속도를 바꾸며, 크로스토크는 신호를 왜곡합니다. 이런 변수들이 모두 겹치면 고정된 타이밍 설정으로는 모든 lane 에서 윈도우 중앙을 찌르는 것이 불가능합니다. Training 은 이 문제를 "직접 측정해서 학습하는" 방식으로 해결합니다.

**mobile LPDDR5(주축)** 의 training 은 단계가 가장 많습니다 — 먼저 **CBT(Command Bus Training, Mode1/2)** 로 CA[6:0] 단일종단 다중사이클 버스를 정렬하고, **WCK2CK leveling**(LPDDR5 고유) 으로 고속 데이터 클럭 WCK 를 명령 클럭 CK 에 맞춘 뒤, DQ/Write/Read training 으로 비트별 지연과 eye 중앙을 찾습니다. 수신 판정 기준 전압은 **내부 Vref** 를 학습합니다. server DDR5 는 CA(CS) Training → Write Leveling → DQ/Eye/VREF 순서입니다. 어느 경우든 chip-specific, lane-specific, 심지어 온도-specific 한 최적 타이밍 값을 찾아 PHY 레지스터에 기록합니다.

```
문제: DDR4 3200MT/s 기준 데이터 유효 윈도우 = ~312 ps
     DDR5 4800MT/s 기준 = ~208 ps

     이 좁은 윈도우 안에서 정확히 샘플링해야 함.

     그러나:
     - PCB 배선 길이 차이 → 신호 도착 시간 차이 (Skew)
     - PVT 변동 → 트랜지스터 속도 변화
     - 온도 변화 → 전파 지연 변화
     - 크로스토크 → 신호 왜곡

     → 고정된 타이밍으로는 정확한 샘플링 불가능
     → 동적으로 타이밍을 조정(Training)해야 함
```

#### CA 버스 Training — LPDDR5 CBT (주축) vs DDR5 CA Training

명령/주소(CA) 버스가 고속화되면 CA 타이밍도 데이터처럼 정렬해 주어야 합니다. 타이밍이 맞지 않으면 잘못된 명령이 DRAM 에 전달되어 치명적 오동작이 됩니다. 다만 CA 버스의 _구조_ 가 세대별로 다르므로 training 도 다릅니다.

**mobile LPDDR5(주축) — CBT (Command Bus Training):** LPDDR5 의 CA 버스는 **CA[6:0] 단일종단(single-ended) 다중사이클** 방식입니다. 핀 수가 적은 대신 한 명령을 여러 사이클에 나눠 보내고 단일종단이라 노이즈 마진이 작아, CA-CK 정렬이 특히 까다롭습니다. 그래서 **CBT 가 필수**이며 Mode1/Mode2 두 단계로 수행됩니다. 판정 전압은 내부 Vref 를 함께 학습합니다.

**server DDR5 — CA / CS Training (비교):** DDR5 는 명령·주소를 **CA[13:0] 차동 클럭에 2-cycle 멀티플렉싱**합니다. 직전 세대 DDR4 의 RAS#/CAS#/WE# 개별 핀 대비 마진이 줄어 CA(CS) Training 이 필수가 되었습니다.

```
CA 버스도 고속화 → CA-CK 타이밍 정렬 필요 (세대별 구조 차이)

LPDDR5 (주축):
  - CA[6:0] 단일종단, 다중사이클 전송 → 마진 작음
  - CBT (Command Bus Training) 필수, Mode1/Mode2 2단계
  - 내부 Vref 학습 병행

DDR5 (server 비교):
  - DDR4: RAS#/CAS#/WE# 개별 핀 → 상대적 저속, 마진 충분
  - DDR5: CA[13:0] 차동 2-cycle 멀티플렉싱 → 마진 축소

CA Training 공통 흐름:
  1. CA Training 모드 진입 (LPDDR5: MRW로 CBT 진입 / DDR5: MPC 명령)
  2. MC가 CA 핀에 알려진 패턴 전송
  3. DRAM이 CK 엣지에서 CA를 샘플링 → DQ로 결과 반환
  4. MC가 CA 지연을 조절하며 반복
  5. 최적 CA-CK 정렬 지점 결정

  이것이 중요한 이유:
  - CA 타이밍 오류 → 잘못된 명령 해석 → 치명적 오동작
  - DDR4에서는 불필요했으나 LPDDR5/DDR5에서 필수
```

#### Write Leveling 상세

```
목적: 각 Byte Lane의 DQS가 DRAM의 CK에 정렬되도록 지연 조정

과정:
  1. MC가 Write Leveling 모드 진입 (MRS 설정)
  2. MC가 DQS 토글 전송
  3. DRAM이 CK 엣지에서 DQS를 샘플링 → DQ로 결과 반환
     DQ = 0: DQS가 CK보다 빠름 (더 지연 필요)
     DQ = 1: DQS가 CK와 정렬됨 (완료)
  4. MC가 DQS 지연을 증가시키며 반복
  5. 0→1 전환점 = 최적 지연값

  Lane 0: delay = 5 taps
  Lane 1: delay = 7 taps  ← PCB 배선 차이 반영
  Lane 2: delay = 4 taps
  ...
```

#### Eye Diagram — 데이터 유효 윈도우

```
전압
  ^
  |    +--------+   +--------+
  |   /          \ /          \
  |  /   Eye      X    Eye     \
  | /   Opening  / \  Opening   \
  |/____________/___\____________\___> 시간
  |            |     |
  |       DQS edge  DQS edge
  |         (최적 샘플링 포인트 = Eye 중앙)

Eye가 클수록 → 타이밍 마진 충분 → 안정적
Eye가 작으면 → 비트 에러 발생 가능 → Training으로 최적점 탐색
```

### 5.7 ZQ Calibration — 임피던스 매칭

DRAM 과 MC 의 출력 드라이버 임피던스가 전송선 임피던스(보통 40 Ω)와 일치하지 않으면 신호 반사가 발생해 데이터 오류로 이어집니다. 문제는 이 임피던스가 온도와 전압에 따라 계속 변한다는 것입니다. ZQ Calibration 은 DRAM 의 ZQ 핀에 연결된 정밀 기준 저항(240 Ω)을 기준으로 내부 드라이버 임피던스를 주기적으로 재보정하는 절차입니다. 초기화 시에는 긴 버전인 ZQ Long(또는 ZQCL, 256 tCK)을 사용하고, 운영 중에는 짧은 버전인 ZQ Short(ZQCS, 64 tCK)를 수십 초 단위로 반복합니다. 이 주기적 보정 없이는 온도가 올라갈수록 임피던스가 벗어나 eye 가 서서히 닫힙니다.

```
문제: DRAM과 MC의 출력 임피던스가 전송선 임피던스(보통 40Ω)와
     불일치하면 신호 반사 → 데이터 오류

ZQ Calibration:
  - DRAM의 ZQ 핀에 정밀 저항(240Ω) 연결
  - DRAM이 이를 기준으로 내부 출력 드라이버 임피던스 조정
  - MC/PHY도 동일한 캘리브레이션 수행

  종류:
  - ZQ Init: 초기화 시 (512 tCK)
  - ZQ Long: 주기적 (256 tCK)
  - ZQ Short: 빈번 (64 tCK)

  → PVT 변동에 따른 임피던스 드리프트를 주기적으로 보상
```

### 5.8 BL2 에서의 DRAM Training (BootROM 연결)

부팅 직후에는 DRAM 이 아직 초기화되지 않은 상태이므로, BL1(BootROM) 은 on-chip SRAM 에서만 실행됩니다. BootROM 은 BL2 를 SRAM 에 로드한 뒤 검증까지만 담당합니다. 실제 DRAM Training 은 BL2(First Stage Bootloader) 에서 수행됩니다. Training 코드는 수 KB 에서 수십 KB 에 달하고 PVT 마다 다른 결과를 만들어 내므로 불변인 BootROM 에 넣기 부적합합니다. 또한 DDR 세대가 바뀌면 Training 알고리즘도 바뀌므로 업데이트가 가능한 BL2 에 두는 것이 맞습니다. BL2 가 Training 을 완료하면 DRAM 이 사용 가능한 상태가 되고, 이후 BL3x 를 DRAM 에 로드하여 정상 부팅을 이어갑니다.

```
부팅 시퀀스에서 DRAM Training 위치:

  BL1 (BootROM):
    - SRAM에서 실행
    - DRAM 미초기화 (Training 전)
    - BL2를 SRAM에 로드 + 검증

  BL2 (FSBL):
    - DRAM Controller 초기화 ← 여기서 Training 수행
    - MC 레지스터 설정
    - DRAM Device MRS 설정
    - Training 시퀀스 실행 (WL → Gate → DQ → Eye → VREF)
    - Training 완료 → DRAM 사용 가능
    - BL3x를 DRAM에 로드

  Training이 BL2에 있는 이유:
    - Training 코드가 크고 복잡 (수 KB ~ 수십 KB)
    - PVT마다 다른 결과 → 런타임 결정 필요
    - DRAM 세대별로 다른 Training → 업데이트 가능해야 함
    → BootROM(불변)에 넣기 부적합
```

### 5.9 Q&A — 자주 묻는 질문

**Q: DRAM Training이 왜 필요한가?**
> "데이터 유효 윈도우가 수백 ps로 극히 좁기 때문이다(LPDDR5X 고gear / DDR5 ~208 ps). PCB 배선 차이, PVT 변동, 크로스토크로 인해 고정 타이밍으로는 정확한 샘플링이 불가능하다. mobile LPDDR5(주축)는 CBT(CA[6:0] 정렬) → WCK2CK leveling(WCK-CK 정렬, LPDDR5 고유) → DQ/Write/Read Training 순으로 단계가 가장 많고 내부 Vref를 학습한다. server DDR5는 CA(CS) Training → Write Leveling → DQ/Eye/VREF 순이다. 어느 경우든 각 채널/바이트 레인의 타이밍을 동적으로 최적화한다."

**Q: Write Leveling의 원리는?**
> "MC가 DQS를 점진적으로 지연시키면서 DRAM이 CK 엣지에서 DQS를 샘플링한 결과를 DQ로 반환한다. DQ가 0→1로 전환되는 지점이 DQS와 CK가 정렬된 최적 지연값이다. 바이트 레인마다 PCB 배선 길이가 다르므로, 각 레인의 최적 지연값이 다르다."

**Q: ODT가 필요한 이유와 토폴로지별 차이는?**
> "고속 DDR 버스에서 전송선 끝의 임피던스 불일치는 신호 반사를 일으켜 데이터 오류를 유발한다. ODT는 DRAM 내부에 종단 저항을 내장하여 반사를 방지한다. mobile LPDDR5(주축)는 PoP point-to-point single-rank라 전송선이 짧고 비타겟 rank가 없어 종단이 단순하다(토폴로지 기반 일반론). server DDR5 DIMM의 multi-rank 구성에서는 타겟 Rank가 데이터를 구동할 때 비타겟 Rank의 ODT(RTT_PARK)가 특히 중요하며, RTT_NOM/WR/PARK 세 값을 Mode Register로 설정하고 최적 조합은 채널 시뮬레이션으로 결정한다."

**Q: DDR5에서 Equalization이 필수인 이유는?**
> "DDR5 4800+ MT/s에서는 비트 간격이 극히 좁아 ISI(Inter-Symbol Interference)로 수신단의 Eye가 거의 닫힌다. CTLE(아날로그 고주파 부스트)와 DFE(이전 비트의 ISI를 디지털로 제거)를 조합하여 Eye를 복원한다. DRAM 수신단(Write)에는 DFE, PHY 수신단(Read)에는 CTLE+DFE를 적용하며, Training으로 계수를 최적화한다."

**Q: LPDDR5 와 DDR5 의 Training 차이는?**
> "mobile LPDDR5(주축)의 고유 항목은 WCK2CK Leveling(고속 데이터 클럭 WCK를 명령 클럭 CK에 정렬)과 CBT(Command Bus Training, CA[6:0] 단일종단 다중사이클 정렬, Mode1/2)이다. DVFSC로 gear가 바뀌어 WCK:CK 비가 달라지면 WCK2CK를 재정렬해야 한다. server DDR5는 CA(CS) Training(CA[13:0] 2-cycle 멀티플렉싱)과 DFE 계수 Training이 직전 세대 DDR4 대비 추가된 항목이다. 즉 LPDDR5는 데이터 클럭이 분리(WCK)되어 정렬 단계가 더 많다."

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'PHY 는 한 번 training 하면 그대로다']
**실제**: Training 은 boot 시 + 운영 중 주기적 retraining 이 모두 필요합니다. ZQ Short 가 수십 초마다 자동, full retraining 이 온도 임계 초과 시 trigger.<br>
**왜 헷갈리는가**: "한 번 잘 맞추면 계속 맞을 것" 이라는 직관 — 실제로는 PVT drift 가 상시.
:::
:::danger[❓ 오해 2 — 'DLL 과 PLL 은 비슷한 회로다']
**실제**: PLL 은 _주파수 합성_ (system clock → DDR clock), DLL 은 _위상 정렬_ (DQS-CK). 위치도 다르고 (PLL: MC/PHY, DLL: DRAM 내부), DDR5 는 DLL 을 _제거_ 하고 PHY 가 phase 를 처리합니다.
:::
:::danger[❓ 오해 3 — 'CTLE 만 있으면 충분, DFE 까지 필요 없다']
**실제**: CTLE 는 _노이즈도_ 함께 증폭합니다. DFE 는 이미 결정된 비트의 ISI 만 빼므로 노이즈 증폭이 없습니다. DDR5 는 CTLE + DFE 의 _상호 보완_ 으로 eye 를 복원합니다.
:::
:::danger[❓ 오해 4 — 'Multi-Rank 에서 ODT 는 타겟 Rank 만 신경쓰면 된다']
**실제**: 비타겟 Rank 의 RTT_PARK (park termination) 가 _더 중요_ 합니다. 비타겟이 floating 이면 신호가 그쪽에서 반사되어 타겟 RX 의 eye 를 닫습니다.
:::
:::danger[❓ 오해 5 — 'CA Training 은 DDR4 에도 있다']
**실제**: 직전 세대 DDR4 의 CA 버스 (RAS#/CAS#/WE# 개별 핀) 는 상대적으로 저속이라 별도 training 불필요. **mobile LPDDR5(주축)는 CA[6:0] 단일종단 다중사이클** 이라 **CBT(Command Bus Training, Mode1/2)** 가 필수이고, **server DDR5 는 CA[13:0] 2-cycle 멀티플렉싱** 이라 CA(CS) Training 이 필수입니다. 구조는 다르지만 둘 다 CA-CK 정렬을 학습한다는 목적은 같습니다.
:::
### DV 디버그 체크리스트 (PHY/Training 영역의 흔한 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Boot 시 Training 무한 실패 / converge 안 함 | DRAM 미초기화 / CKE/RESET 시퀀스 문제 | Phase 1 power sequence, MRS 발행 timestamp |
| 특정 lane 만 read error | per-lane DQ delay tap 학습 실패 | lane 별 tap 수렴 값, eye margin |
| 고온에서만 read corruption | retraining trigger 조건 / VREF drift | 온도 센서 (MR4), VREF 학습 timestamp |
| Multi-Rank 에서만 fail (single-rank OK) | 비타겟 Rank 의 RTT_PARK 미설정 | MR5, RTT_PARK 활성 여부 |
| Write 만 fail (Read OK) | Write Leveling 학습 결과 / DQS-CK 정렬 | WL tap 값 vs PCB 길이 추정 |
| 특정 ZQ short 직후 RD/WR fail | ZQ 와 RD/WR 명령 충돌 (tZQCS 위반) | ZQCS issue timestamp + 인접 RD/WR |
| DDR5 에서만 CA decode error | CA / CS Training 누락 또는 실패 | MPC 명령 흐름, CS Training tap |
| LPDDR5 DVFSC 전환 후 fail | WCK2CK retraining 누락 / 저장된 값 복원 실패 | DVFSC FSM, WCK 위상 |

:::caution[실무 주의점 — ZQ Calibration 타이밍 위반으로 ODT 임피던스 오동작]
**현상**: 온도 변화 이후 Write 데이터가 Eye 중심에서 벗어나 비트 오류율이 증가하거나, 주기적 ZQ Calibration 도중 RD/WR 명령이 겹쳐 데이터 오염 발생.

**원인**: ZQCS(Short Calibration)는 tZQCS(80ns) 동안 DQ/DQS 드라이버를 완전히 점유하므로, 이 구간에 RD/WR 명령이 발행되면 정의되지 않은 동작. MC가 Calibration 스케줄러와 명령 스케줄러를 독립적으로 운용할 때 충돌 발생 가능.

**점검 포인트**: ZQCS 명령 발행 시점에서 tZQCS 이전 RD/WR 명령의 완료 여부 확인. SVA에서 `zq_start → ##[1:tZQCS_ns] (no_rd && no_wr)` assertion 구현. 주기적 Calibration 간격이 온도 변화 속도보다 충분히 짧은지 스펙(tZQCAL_interval ≤ 1ms) 확인.
:::
---

## 7. 핵심 정리 (Key Takeaways)

- **LPDDR5 PHY 정체성 = CK + WCK 2-클럭**: 명령용 저속 CK + 데이터용 고속 WCK(WCK:CK = 2:1/4:1). 데이터 스트로브는 WCK/RDQS. server DDR5 는 단일 CK + DQS.
- **PHY = 명령/데이터의 전기적 변환 + 캘리브레이션**: 클럭 위상 정렬, 임피던스 보정, training 으로 lane-by-lane timing 최적화. DDR5/LPDDR5 는 DLL-less 경향 — LPDDR5 는 WCK2CK Training 으로 정렬.
- **Training 은 boot 시 한 번이 아니다** — 운영 중 임피던스 Short / 주기적 retraining + DVFSC gear 전환 시 WCK2CK 재정렬로 PVT/주파수 변동 보상.
- **LPDDR5 Training(주축)**: CBT(CA[6:0] 정렬) + **WCK2CK Leveling(LPDDR5 고유)** + DQ/Write/Read, 내부 Vref. server DDR5 비교: CA(CS) Training + DFE 계수.
- **Equalization (CTLE + DFE)**: 고gear(LPDDR5X / DDR5)에서 필수, **DVFSC 저gear 에서는 EQ 완화**. CTLE 가 고주파 부스트, DFE 가 ISI 제거.
- **ODT/종단**: LPDDR5 = point-to-point single-rank(단순), server DDR5 DIMM = multi-rank RTT_NOM/WR/PARK.
- **BL2 에서 Training 수행** — 코드 크고 PVT 의존이라 BootROM 부적합. Training 결과는 chip-by-chip / 온도-by-온도 다름.

:::caution[실무 주의점]
- "PHY 가 한 번 set up 되면 끝" 은 가장 빈번한 오해 — retraining trigger 조건을 검증 시나리오에 반드시 포함.
- Multi-Rank ODT 는 비타겟 RTT_PARK 가 더 중요. 무시하면 single-rank 에서는 깨끗했던 eye 가 multi-rank 에서 닫힘.
- LPDDR5 의 DVFSC 전환은 _train 결과 보존 또는 재train_ 둘 중 하나가 일관되게 동작해야 — 둘 다 안 되면 silent corruption.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — Eye width 계산 (Bloom: Apply)]
DDR5 4800 MT/s. _UI (Unit Interval)_ 와 _data valid window_ ?

<details>
<summary>정답</summary>

- UI = 1 / (4800 × 10^6) = **208 ps**.
- DDR 은 _half UI_ valid window: ~104 ps.
- 실제 jitter / skew 제외 후 _eye opening_ ~50-80 ps.

매우 좁아서 PHY training (CTLE, DFE) 정확도가 critical.

</details>
:::
:::tip[🤔 Q2 — Retraining trigger (Bloom: Analyze)]
PHY retraining 이 _언제_ 필요한가?

<details>
<summary>정답</summary>

- **온도 변화**: ΔT 10°C 마다 _propagation delay_ 변동. 자동 retraining.
- **DVFSC**: clock frequency 변경 시.
- **Refresh-induced disturb**: drift 누적.
- **Long idle**: PLL/CDR lock drift.

DV 시 _각 trigger_ inject + retraining 시퀀스 정확 동작 확인.

</details>
:::
### 7.2 출처

**External**
- JEDEC DDR5 PHY guidelines
- *DDR5 PHY Training Algorithms* — Cadence / Synopsys WP

---

## 다음 모듈

→ [Module 04 — DRAM DV Methodology](../04_dram_dv_methodology/): 지금까지 본 cell + MC + PHY 를 _어떻게 검증하는가_. Behavioral model, traffic generator, scoreboard, timing SVA, ECC injection.

[퀴즈 풀어보기 →](../quiz/03_memory_interface_phy_quiz/)

