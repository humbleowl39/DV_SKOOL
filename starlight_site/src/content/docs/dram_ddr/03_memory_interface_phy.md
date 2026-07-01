---
title: "Module 03 — Memory Interface / PHY"
---

:::tip[학습 목표]
이 모듈을 마치면 (**LPDDR5 PHY** 중심):

- **Diagram** LPDDR5 PHY의 주요 블럭(PLL, CK/WCK, DQ/CA TX/RX, Training engine, 임피던스 보정)을 그릴 수 있다.
- **Explain** LPDDR5 의 CK(명령용 저속) + WCK(데이터용 고속, WCK:CK = 2:1/4:1) 2-클럭 구조와, 데이터 스트로브를 WCK/RDQS 가 맡는 이유를 설명할 수 있다.
- **Apply** LPDDR5 Training(CBT Mode1/2, WCK2CK leveling, DQ/Write/Read)의 순서와 목적을 시나리오에 매핑할 수 있다.
- **Analyze** PVT(Process/Voltage/Temperature) 변동이 timing margin에 미치는 영향과 보정 메커니즘을 분석할 수 있다.
- **Distinguish** CTLE / DFE 같은 equalization 기법과 적용 위치(Write/Read), 그리고 DVFSC 저gear 에서의 EQ 완화를 구분할 수 있다.
- **Explain** LPDDR5 의 point-to-point single-rank 구성이 왜 종단(ODT)을 단순하게 만드는지 설명할 수 있다.
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

원인은 **온도 변화로 인한 PHY timing 변동**입니다. boot 시 25°C 에서 training 을 완료하면 모든 lane 의 delay tap 이 수렴합니다. 그런데 SoC 가 부하 상태에서 75°C 까지 가열되면 PCB trace 의 전파 지연이 수 ps 변동합니다. LPDDR5X 고gear 의 데이터 유효 윈도우는 수백 ps 로 좁으므로, 이 정도의 변동만으로도 윈도우 가장자리에 걸쳐 있던 샘플링 포인트가 유효 범위 밖으로 밀려납니다. 그 결과 "가끔 wrong bit" — 재현이 어렵고 랜덤 데이터 테스트로는 잡히지 않는 silent corruption 이 됩니다.

**해법**: _운영 중에도 주기적 calibration_ — ZQ Calibration, periodic DQ training. PHY 가 _자기 진단_ 하고 _재조정_ 함.

Module 02 에서 MC 가 발행한 ACT/RD/WR/PRE 명령은 _전기 신호_ 가 되어 PCB 트레이스를 건너 DRAM 에 도달해야 합니다. LPDDR5X 고gear 의 _데이터 유효 윈도우_ 는 수백 ps 수준으로 좁습니다(직전 세대 LPDDR4 보다 훨씬 더 좁아졌습니다). PCB 배선 차이, PVT 변동, 크로스토크가 그 윈도우를 더 좁힙니다. **PHY 의 임무는 이 ns 도 안 되는 시간 안에서 정확한 샘플링을 보장하는 것** — 그리고 그것은 정적 설정으로는 불가능합니다. **Training 실패 = silent corruption** — silicon 이 동작하는 것처럼 보이지만 데이터 변조.

이 모듈을 건너뛰면 timing parameter 의 의미가 _ns 단위 사이클 카운트_ 에 머무르고, 왜 boot 시 BL2 가 수십 KB 의 training 코드를 돌리는지, 왜 운영 중에도 임피던스/타이밍 calibration 이 주기적으로 돌아야 하는지 답할 수 없습니다.

:::note[이 모듈의 정체성 — LPDDR5 PHY 와 WCK]
이 모듈은 **LPDDR5 PHY** 를 다룹니다. LPDDR5 의 정체성은 **2개의 클럭**입니다 — 명령/주소용 저속 차동 클럭 **CK** 와, 데이터용 고속 클럭 **WCK**. WCK:CK 비는 gear 에 따라 **2:1 또는 4:1** 이고, 데이터 스트로브는 (직전 세대 LPDDR4 가 DQS 를 쓰던 것과 달리) **WCK/RDQS** 가 맡습니다. 또 CA 버스가 **CA[6:0] 단일종단 다중사이클** 이라 **CBT(Command Bus Training)** 가 필수입니다. 아래 scenario 의 ps 수치는 예시이며, LPDDR5X 의 고gear 에서 데이터 유효 윈도우는 수백 ps 로 좁습니다.
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
  ODT: "ODT —\npoint-to-point 단순 종단"
  EQ: "CTLE / DFE — EQ (고gear)"
  TR: "Training engine\n· CBT → WCK2CK → DQ/WL/Read\n· Eye → 내부 VREF, DFE coef\n· 주기 retraining (PVT drift)\nresult → MR / delay-tap reg"
  PLL -> TX
  PLL -> RX
  TR -> TX
  TR -> RX
  TR -> EQ
}
DRAM: "DRAM device (LPDDR5)" {
  PHASE: "WCK-CK 정렬은\nWCK2CK Training 이 처리 (DLL-less 경향)"
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

가장 단순한 시나리오. LPDDR5 데이터 버스의 _byte lane 0_ 에서 Write Leveling(쓰기 레벨링 — 각 데이터 묶음의 strobe 시점을 클럭에 맞춰 정렬하는 보정) 한 lane 을 추적합니다. 여기서 "strobe" 는 LPDDR5 의 데이터 클럭 WCK 를 가리킵니다(원리는 이전 세대의 DQS 정렬과 동일합니다).

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
| **CK / WCK 생성** | CK(명령용 저속) + WCK(데이터용 고속), WCK:CK = 2:1/4:1 | ps |
| **위상 정렬** | WCK-CK 정렬을 PHY 측 WCK2CK Training 으로 처리 (LPDDR5 는 DLL-less 경향) | ps |
| **CA / DQ / WCK TX/RX** | 신호 driver / receiver | mV / ps |
| **Per-lane delay tap** | DQ/WCK 위상 조정 | tap (~5-10 ps each) |
| **Internal VREF** | 수신 판정 기준 전압 (LPDDR5 는 내부 Vref) | mV |
| **ODT** | 종단 임피던스 (point-to-point single-rank 라 단순) | Ω |
| **임피던스 보정 engine** | 출력 임피던스 보정 (240Ω 기준) | Ω, % |
| **EQ (CTLE + DFE)** | ISI / 고주파 손실 보상 (고gear 필수, DVFSC 저gear 완화) | dB |
| **Training engine** | CBT → WCK2CK → DQ/Write/Read → Eye → 내부 VREF | per-lane |

### 4.2 Training 시퀀스 — 표준 순서

LPDDR5 는 단계가 많습니다 — CBT 로 CA 정렬, WCK2CK 로 데이터 클럭 정렬을 먼저 잡은 뒤 DQ/Write/Read 를 맞춥니다.

| Training | 목적 | 시점 |
|---------|------|------|
| **CBT (Command Bus Training, Mode1/2)** | CA[6:0] 단일종단 다중사이클 정렬 | init |
| **WCK2CK Leveling** | WCK-CK 위상 정렬 (LPDDR5 고유) | init / gear 전환 시 |
| **Write Leveling** | 데이터 스트로브(WCK)-to-CK 스큐 보정 (Write) | init |
| **Read Gate Training** | 스트로브 수신 시작 타이밍 결정 | init |
| **Read/Write DQ Training** | DQ-to-스트로브 비트별 지연 보정 | init |
| **Read Eye Training** | 데이터 유효 윈도우 중앙 | init |
| **VREF Training (internal Vref)** | 수신 판정 기준 전압 최적화 | init |
| **DFE coef Training** | Decision Feedback EQ 계수 (고gear) | init |
| **임피던스 보정 (Init/Long/Short)** | 출력 임피던스 | init + 주기 |
| **Periodic Retraining** | 온도 변화 / DVFSC gear 전환 보상 | runtime |

핵심: LPDDR5 는 데이터 클럭이 별도의 고속 **WCK** 라서 **WCK2CK Leveling**(WCK 와 CK 위상 정렬)이 고유 단계로 추가되고, gear(DVFSC)가 바뀌어 WCK:CK 비가 달라질 때마다 재정렬이 필요합니다. 데이터 스트로브를 DQS 하나로 해결하던 직전 세대 LPDDR4 에는 없던 단계입니다.

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

### 5.1 LPDDR5 신호 구성

LPDDR5 인터페이스(Memory Controller / PHY ↔ DRAM Device)의 핵심은 **명령 클럭과 데이터 클럭이 분리**되어 있다는 점입니다.

**Clock**

- `CK_t/CK_c` — 명령용, 저속 차동 클럭
- `WCK_t/WCK_c` — 데이터용, 고속 클럭. WCK:CK = 2:1 또는 4:1 (gear 의존)
- → LPDDR5 의 정체성: 명령(느림)과 데이터(빠름) 클럭이 분리됨

**Command/Address (CA) Bus**

- `CA[6:0]` — 단일종단, 다중사이클로 명령/주소 전송 → CBT 필수
- `CS` — Chip Select

**Data Bus (per byte lane)**

- `DQ[7:0]` — 데이터, 8-bit per lane
- `WCK / RDQS` — 데이터 스트로브 역할. 직전 세대 LPDDR4 가 쓰던 DQS 대신 WCK 계열이 이 역할을 맡습니다.
- `DMI` — Data Mask / Inversion

### 5.2 DQS 와 DQ 의 관계

데이터 스트로브는 데이터 버스에서 DQ 가 언제 유효한지를 알려 주는 기준 클럭 역할을 합니다. **LPDDR5 는 이 역할을 고속 데이터 클럭인 WCK(읽기 시 RDQS)** 가 맡습니다 — 직전 세대 LPDDR4 가 DQS 를 쓰던 것과 명칭은 다르지만 DQ 정렬 원리는 동일합니다. Write 경로에서는 MC 가 스트로브를 DQ 와 center-aligned 로 정렬하여 전송하고, DRAM 은 스트로브 에지에서 DQ 를 샘플링합니다. Read 경로에서는 DRAM 이 스트로브를 DQ 와 edge-aligned 로 내보내고, MC/PHY 는 이를 90° 지연시켜 DQ 의 중앙에서 샘플링합니다. Write 와 Read 의 스트로브-DQ 관계가 서로 다르다는 점이 Training 을 방향별로 구분해야 하는 이유입니다. LPDDR5 에서는 추가로 이 데이터 클럭(WCK)을 명령 클럭(CK)에 맞추는 **WCK2CK leveling** 이 선행되어야 합니다.

이 center/edge 의 비대칭은 "누가 샘플링하는 쪽인가" 에서 나옵니다. 샘플링하는 쪽은 안정적으로 데이터를 잡으려면 strobe 에지를 데이터 비트의 **한가운데(center)** — setup/hold 마진이 양쪽으로 가장 넓은 지점 — 에 두고 싶어 합니다. **Write** 에서는 _DRAM_ 이 샘플링하는 쪽인데, DRAM 안에는 DQS 를 옮길 마땅한 지연 회로가 없습니다. 그래서 보내는 쪽인 MC 가 미리 DQS 를 데이터 중앙에 맞춰(center-aligned) 보내 줍니다 — DRAM 은 받은 에지에서 곧장 latch 만 하면 됩니다. 반대로 **Read** 에서는 _MC/PHY_ 가 샘플링하는 쪽입니다. DRAM 은 회로를 단순하게 두려고 DQS 와 DQ 를 그냥 같은 타이밍, 즉 **edge-aligned** 로 함께 내보냅니다. 받는 MC/PHY 가 DQS 를 90° (≈ 비트 폭의 절반) 지연시켜 데이터 중앙으로 옮긴 뒤 샘플링합니다. 정리하면 — **마진을 만드는 90° 시프트 책임을 항상 "받는(샘플링하는) 쪽"이 진다**는 한 가지 원리에서 Write 의 center-aligned 송신과 Read 의 수신측 90° 시프트가 모두 따라 나옵니다.

스트로브(LPDDR5 에서는 WCK)와 DQ 의 관계를 방향별로 정리하면:

- **Write (MC → DRAM)**: MC 가 스트로브를 DQ 와 정렬하여 전송하고, DRAM 이 스트로브 엣지에서 DQ 를 샘플링합니다. → 스트로브가 DQ 와 **center-aligned**.
- **Read (DRAM → MC)**: DRAM 이 스트로브를 DQ 와 **edge-aligned** 로 전송하고, MC/PHY 가 스트로브를 90° 지연시켜 DQ 중앙에서 샘플링합니다. → 수신단에서 90° phase shift 필요.

```
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

여기서 LPDDR5 의 토폴로지가 종단을 단순하게 만듭니다. **LPDDR5 는 SoC 와 메모리가 PoP 로 매우 짧게 연결된 point-to-point, single-rank 구성**입니다. 전송선이 짧고 비타겟 rank 가 없으므로, 타겟과 비타겟을 구분해 종단을 절환할 필요가 없어 종단 요구가 근본적으로 단순합니다. Write 시에는 수신측(DRAM)의 ODT 를, Read 시에는 수신측(MC/PHY)의 ODT 를 켜서 반사를 억제하는 정도로 충분합니다.

반사가 없으려면 **소스 임피던스 = 전송선 임피던스 = 종단 임피던스** 여야 합니다. DDR 이전에는 외부 종단 저항을 PCB 에 실장했지만, DDR2 부터 DRAM 칩 내부에 종단 저항을 내장한 것이 ODT 입니다 — 외부 부품을 제거해 PCB 간소화, 비용 절감, 신호 품질 향상을 동시에 얻습니다.

ODT 는 항상 **수신하는 쪽**을 종단합니다. 아래는 방향별 종단 위치입니다.

```
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
```

LPDDR5 는 point-to-point single-rank(PoP) 라 위 두 경우가 전부입니다. 비타겟 rank 를 위한 park termination 이나 rank 별 ODT 절환 같은 복잡한 조합이 필요 없다는 점이 mobile 토폴로지의 종단 이점입니다.

:::note[면접 포인트]
"ODT 는 고속 DRAM 버스에서 신호 반사를 방지하는 핵심 메커니즘으로, DRAM 내부에 종단 저항을 내장하여 PCB 간소화와 신호 무결성을 동시에 달성한다. LPDDR5 는 point-to-point single-rank 구성이라 수신측 종단만 켜면 되어 종단 제어가 단순하다."
:::

### 5.4 DLL / PLL — 클럭 생성과 분배

**위상 정렬 회로 — DLL 은 왜 사라지는 추세인가**

과거 세대의 DRAM 은 내부 **DLL(Delay-Locked Loop)** 로 내부 클럭과 외부 CK 의 위상을 정렬했습니다. 원리는 지연(delay)을 조절해 피드백 클럭과 기준 클럭의 위상을 맞추는 것입니다.

```d2
direction: right

CKIN: "외부 CK"
VD: "Variable Delay"
CKIN -> VD
CKOUT: "내부 CK\n(스트로브 생성용)"
VD -> CKOUT
PD: "Phase Detector\n(지연 증가/감소)"
CKOUT -> PD: "피드백"
PD -> VD
```

DLL 이 하는 일은 스트로브를 CK 에 정렬해 출력하고, 온도/전압 변화에 따라 지연을 자동 조절하는 것입니다.

**LPDDR5 는 DLL-less 경향**입니다 — 위상 정렬을 DRAM 내부 고정 회로가 아니라 PHY 측에서 처리합니다. 구체적으로는 데이터 클럭 WCK 를 명령 클럭 CK 에 맞추는 **WCK2CK Training** 으로 정렬을 수행합니다(DLL 대신).

왜 DRAM 내부 DLL 을 떼어냈을까요? DLL 은 _고정된 동작 주파수_ 에서 한 클럭 주기를 잘게 나눠 위상을 맞추는 회로라, 동작 주파수가 넓게 바뀌거나 런타임에 DVFS 로 주파수를 갈아탈 때마다 lock 을 다시 잡아야 해서 유연성이 떨어집니다. 게다가 항상 켜져 있어 무시 못 할 전력을 소모합니다. LPDDR5 는 DVFSC 로 동작 주파수를 넓게 바꾸고 저전력이 특히 중요하므로, 위상 정렬을 DRAM 내부 고정 회로에서 떼어내 **MC/PHY 측의 training 으로** 옮겼습니다 — PHY 가 측정해 학습한 delay tap 으로 스트로브-CK 관계를 맞추므로, 주파수가 바뀌면 그 gear 에서 다시 학습하면 됩니다. 즉 "고정 하드웨어 정렬" 을 "측정 기반 소프트웨어 정렬" 로 바꿔 넓은 주파수 범위와 DVFS 대응을 얻은 것입니다.

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

PLL 이 하는 일은 시스템 클럭에서 DDR 클럭과 그 분주/배수 클럭을 합성하는 것입니다 — 예컨대 시스템 클럭을 체배(×N)해 GHz 대의 DDR 클럭을 만들고, Read 스트로브 샘플링용 90° 위상 시프트 클럭도 생성합니다. Jitter 최소화가 Eye Diagram 품질에 직접 영향을 주므로 PLL 품질은 신호 무결성과 직결됩니다.

**DLL vs PLL 차이**

| 항목 | DLL | PLL |
|------|-----|-----|
| 동작 | 지연 조절 (위상만) | 주파수 합성 |
| 위치 | DRAM 내부 | MC/PHY 내부 |
| 주 목적 | 스트로브-CK 정렬 | DDR 클럭 생성 |
| LPDDR5 | DLL-less 경향 (제거) | 필수 |

LPDDR5 는 DLL 대신 WCK2CK Training 으로 WCK-CK 를 정렬한다는 점이 핵심입니다.

### 5.5 Equalization — 고속 신호 보상 기법

고속 동작에서는 비트 간격(UI)이 극히 좁아집니다 — **LPDDR5X 의 고gear** 에서 UI 는 수백 ps 이하로 좁아집니다. 이 좁은 간격 때문에 이전 비트의 잔여 신호가 현재 비트와 겹치는 ISI(Inter-Symbol Interference) 가 심각해져, 수신단의 eye 다이어그램이 거의 닫힙니다. 이를 보상하지 않으면 데이터를 올바르게 샘플링할 수 없습니다. Equalization 은 이 eye 를 복원하는 기법입니다. CTLE 는 아날로그 필터로 채널의 고주파 감쇠를 보상하지만 노이즈도 함께 증폭한다는 단점이 있습니다. 그 이유는 CTLE 가 **선형(linear) 필터**이기 때문입니다 — CTLE 는 "신호" 와 "노이즈" 를 구분하지 못하고, 그저 _고주파 성분_ 을 무차별적으로 부스트합니다. 채널이 깎아먹은 신호의 고주파를 되살리는 그 동작이, 같은 대역에 있는 고주파 노이즈와 crosstalk 도 똑같은 비율로 키웁니다. 결과적으로 신호 대 노이즈 비(SNR)는 거의 개선되지 않고 진폭만 커집니다. 반면 DFE 는 이미 결정된 이전 비트들의 ISI 기여분을 디지털로 빼는 방식이라 노이즈를 증폭하지 않으며 — _이미 판정된 값_ 만 쓰므로 빼는 양에 노이즈가 섞이지 않습니다 — CTLE 와 상호 보완적으로 동작합니다. LPDDR5(X) 고gear 에서 두 기법을 함께 사용하는 이유가 바로 이 상보 관계 때문입니다. 단, **LPDDR5 의 DVFSC 저gear(낮은 주파수)** 에서는 UI 가 넓어져 ISI 부담이 줄므로 EQ 요구가 완화됩니다 — gear 에 따라 EQ 세기를 조절할 수 있다는 점이 mobile 의 전력 이점입니다.

**문제**: LPDDR5X 고gear 에서는 채널 손실(ISI, 크로스토크)이 심각해 수신단에서 Eye 가 거의 닫힙니다 — 보상 없이는 데이터 수신이 불가능합니다. ISI(Inter-Symbol Interference)는 이전 비트의 잔여 신호가 현재 비트에 간섭하는 현상으로, 비트 간격이 좁아지는 고속일수록 심각해집니다.

**CTLE (Continuous-Time Linear Equalizer)** 는 수신단에 아날로그 필터를 적용해 고주파 성분을 증폭함으로써 채널 손실을 보상합니다. 간단하지만 노이즈도 함께 증폭한다는 단점이 있습니다. 주파수 응답으로 보면 채널이 깎은 고주파를 CTLE 가 되살려 전체 응답을 평탄화하는 그림입니다.

```
  채널 응답:    ─────────╲  (고주파 감쇠)
  CTLE 보상:    ─────────╱  (고주파 부스트)
  결과:         ───────────  (평탄화)
```

**DFE (Decision Feedback Equalizer)** 는 이미 결정된 비트 값을 이용해 ISI 를 제거합니다 — 현재 비트에서 이전 비트들의 예상 간섭을 빼주므로 노이즈를 증폭하지 않아 CTLE 와 상호 보완적입니다.

- 수신 신호 = 현재 비트 + h1×(이전 비트) + h2×(2번 전 비트) + ...
- DFE 보상: 수신 신호 − h1×(이전 결정값) − h2×(2번 전 결정값)
- → ISI 성분 제거 → 깨끗한 Eye 복원

LPDDR5(X) 에서의 적용은 DRAM 수신단(Write 경로)에 DFE, PHY 수신단(Read 경로)에 CTLE + DFE 조합을 두고, Training 으로 DFE 계수(h1, h2)를 최적화하는 방식입니다.

:::note[면접 포인트]
"LPDDR5X 고gear 에서는 채널 ISI 로 Eye 가 닫히므로 Equalization 이 필수이다. CTLE 는 아날로그 고주파 부스트, DFE 는 이전 비트의 ISI 를 디지털로 제거하며, DRAM 과 PHY 양측에서 적용하고 Training 으로 계수를 최적화한다. 단 DVFSC 저gear 에서는 UI 가 넓어져 EQ 요구가 완화된다."
:::

### 5.6 Training — 왜 필요한가?

고속 데이터 유효 윈도우는 ps 단위로 좁습니다(LPDDR5X 고gear 는 수백 ps 수준, 직전 세대 LPDDR4 보다 훨씬 좁습니다). 이 좁은 윈도우 안에서 정확히 샘플링해야 데이터가 정상입니다. 그런데 PCB 배선 길이는 byte lane 마다 mm 단위로 다르고, 온도와 전압 변동은 트랜지스터의 속도를 바꾸며, 크로스토크는 신호를 왜곡합니다. 이런 변수들이 모두 겹치면 고정된 타이밍 설정으로는 모든 lane 에서 윈도우 중앙을 찌르는 것이 불가능합니다. Training 은 이 문제를 "직접 측정해서 학습하는" 방식으로 해결합니다.

**LPDDR5** 의 training 은 단계가 많습니다 — 먼저 **CBT(Command Bus Training, Mode1/2)** 로 CA[6:0] 단일종단 다중사이클 버스를 정렬하고, **WCK2CK leveling**(LPDDR5 고유) 으로 고속 데이터 클럭 WCK 를 명령 클럭 CK 에 맞춘 뒤, DQ/Write/Read training 으로 비트별 지연과 eye 중앙을 찾습니다. 수신 판정 기준 전압은 **내부 Vref** 를 학습합니다. 이렇게 chip-specific, lane-specific, 심지어 온도-specific 한 최적 타이밍 값을 찾아 PHY 레지스터에 기록합니다.

Training 이 없으면 왜 안 되는지는 한 그림으로 정리됩니다.

```
데이터 유효 윈도우가 수백 ps 로 좁은데,

  - PCB 배선 길이 차이 → 신호 도착 시간 차이 (Skew)
  - PVT 변동 → 트랜지스터 속도 변화
  - 온도 변화 → 전파 지연 변화
  - 크로스토크 → 신호 왜곡

  → 고정된 타이밍으로는 정확한 샘플링 불가능
  → 동적으로 타이밍을 조정(Training)해야 함
```

#### CA 버스 Training — LPDDR5 CBT (Command Bus Training)

명령/주소(CA) 버스가 고속화되면 CA 타이밍도 데이터처럼 정렬해 주어야 합니다. 타이밍이 맞지 않으면 잘못된 명령이 DRAM 에 전달되어 치명적 오동작이 됩니다.

LPDDR5 의 CA 버스는 **CA[6:0] 단일종단(single-ended) 다중사이클** 방식입니다. 핀 수가 적은 대신 한 명령을 여러 사이클에 나눠 보내고 단일종단이라 노이즈 마진이 작아, CA-CK 정렬이 특히 까다롭습니다. 그래서 **CBT 가 필수**이며 Mode1/Mode2 두 단계로 수행됩니다. 판정 전압은 내부 Vref 를 함께 학습합니다. 참고로 직전 세대 LPDDR4 의 CA 는 상대적으로 저속이라 이런 정밀 training 부담이 작았습니다.

CBT 의 흐름은 다음과 같습니다.

1. CBT 진입 (MRW 로 training 모드 활성)
2. MC 가 CA 핀에 알려진 패턴 전송
3. DRAM 이 CK 엣지에서 CA 를 샘플링 → DQ 로 결과 반환
4. MC 가 CA 지연을 조절하며 반복
5. 최적 CA-CK 정렬 지점 결정 (+ 내부 Vref 학습 병행)

이것이 중요한 이유는 CA 타이밍 오류가 곧 잘못된 명령 해석 → 치명적 오동작으로 이어지기 때문입니다.

#### Write Leveling 상세

목적은 각 Byte Lane 의 데이터 스트로브(LPDDR5 에서는 WCK)가 DRAM 의 CK 에 정렬되도록 지연을 조정하는 것입니다. 과정은 다음과 같습니다.

1. MC 가 Write Leveling 모드 진입 (MRS 설정)
2. MC 가 스트로브 토글 전송
3. DRAM 이 CK 엣지에서 스트로브를 샘플링 → DQ 로 결과 반환
   - DQ = 0: 스트로브가 CK 보다 빠름 (더 지연 필요)
   - DQ = 1: 스트로브가 CK 와 정렬됨 (완료)
4. MC 가 스트로브 지연을 증가시키며 반복
5. 0→1 전환점 = 최적 지연값

lane 마다 PCB 배선 길이가 달라 최적 tap 이 다릅니다 — 예컨대 Lane 0 은 5 taps, Lane 1 은 7 taps, Lane 2 는 4 taps 처럼 lane 별로 수렴합니다.

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
  |       strobe    strobe
  |         (최적 샘플링 포인트 = Eye 중앙)
```

Eye 가 클수록 타이밍 마진이 충분해 안정적이고, Eye 가 작으면 비트 에러가 발생할 수 있어 Training 으로 최적점을 탐색합니다.

### 5.7 ZQ Calibration — 임피던스 매칭

DRAM 과 MC 의 출력 드라이버 임피던스가 전송선 임피던스(보통 40 Ω)와 일치하지 않으면 신호 반사가 발생해 데이터 오류로 이어집니다. 문제는 이 임피던스가 온도와 전압에 따라 계속 변한다는 것입니다. ZQ Calibration 은 DRAM 의 ZQ 핀에 연결된 정밀 기준 저항(240 Ω)을 기준으로 내부 드라이버 임피던스를 주기적으로 재보정하는 절차입니다. 초기화 시에는 긴 버전인 ZQ Long(또는 ZQCL, 256 tCK)을 사용하고, 운영 중에는 짧은 버전인 ZQ Short(ZQCS, 64 tCK)를 수십 초 단위로 반복합니다. 이 주기적 보정 없이는 온도가 올라갈수록 임피던스가 벗어나 eye 가 서서히 닫힙니다.

DRAM 과 MC 의 출력 임피던스가 전송선 임피던스(보통 40Ω)와 불일치하면 신호 반사가 데이터 오류를 유발합니다. ZQ Calibration 은 DRAM 의 ZQ 핀에 연결된 정밀 저항(240Ω)을 기준으로 내부 출력 드라이버 임피던스를 조정하는 절차이며, MC/PHY 도 동일한 캘리브레이션을 수행합니다. 종류는 다음과 같습니다.

- **ZQ Init**: 초기화 시 (512 tCK)
- **ZQ Long**: 주기적 (256 tCK)
- **ZQ Short**: 빈번 (64 tCK)

이렇게 PVT 변동에 따른 임피던스 드리프트를 주기적으로 보상합니다.

### 5.8 DFI (DDR PHY Interface) — MC 와 PHY 의 표준 경계

지금까지 "MC 가 명령을 발행하면 PHY 가 전기 신호로 바꾼다" 고 말했는데, 그 **MC ↔ PHY 사이의 신호 규약** 이 바로 **DFI(DDR PHY Interface)** 입니다. DFI 는 업계 표준 스펙(DFI Specification, 최신 세대가 LPDDR5 지원)으로, 컨트롤러 IP 공급사와 PHY IP 공급사를 분리(decouple)해 서로 다른 벤더의 MC 와 PHY 를 조합할 수 있게 해 줍니다. DFI 위에서 오가는 것은 크게 세 가지입니다 — (1) **명령/주소**(dfi_address, dfi_cs, dfi_cke ...), (2) **write/read 데이터**(dfi_wrdata(_en), dfi_rddata(_valid) ...), (3) **제어 핸드셰이크**(update / low-power / frequency / init). 앞의 둘은 데이터 경로라 직관적이고, DV 에서 특히 챙겨야 하는 것은 **핸드셰이크** 입니다.

DFI 의 타이밍은 `dfi_t*` 파라미터(예: DFI 명령→DRAM 핀 사이의 write/read latency)로 표현되는데, 이 값들도 **gear/주파수마다 달라지므로** MC 가 gear 전환 시 갱신해야 합니다 — §5.4·Module 04 §5.7 의 "타이밍은 gear 의존" 이라는 이야기가 DFI 레벨에서도 그대로 반복됩니다.

#### 핵심 핸드셰이크 신호 요약

| 인터페이스 | Req | Ack | 방향(주도권) | 주요 발생 상황 |
|---|---|---|---|---|
| **Controller Update** | `dfi_ctrlupd_req` | `dfi_ctrlupd_ack` | 컨트롤러 → PHY | 주기 타이머 만료, self-refresh 탈출 시 — PHY 에 ZQ/retraining 등 내부 업데이트 창을 부여 |
| **PHY Update** | `dfi_phyupd_req` | `dfi_phyupd_ack` | PHY → 컨트롤러 | PHY 가 긴급 캘리브레이션/retraining 이 필요해 창을 요청 |
| **PHY Master** | `dfi_phymstr_req` | `dfi_phymstr_ack` | PHY → 컨트롤러 | PHY 가 버스 주도권을 요청(예: 자체 필요로 self-refresh 진입) |
| **Low Power** | `dfi_lp_ctrl_req` / `dfi_lp_data_req` | `dfi_lp_*_ack` | 컨트롤러 → PHY | 절전 모드(clock gating / power-down / self-refresh) 진입·탈출 |
| **Init / Status** | `dfi_init_start` | `dfi_init_complete` | 컨트롤러 → PHY (complete 는 PHY → 컨트롤러) | 초기화 시퀀스 시작/완료 |
| **Frequency Change** | `dfi_freq_fsp` / `dfi_frequency` | (Controller Update 창에서 처리) | 컨트롤러 → PHY | **DVFSC gear(FSP) 전환** — PHY 가 새 gear 의 지연/EQ 값을 다시 로드 |

핸드셰이크의 공통 규칙은 "**req 는 대응 ack 가 올 때까지 유지되고, 그 사이(업데이트/절전/주파수전환 창) 에는 정상 트래픽이 멈춘다**" 는 것입니다. 특히 LPDDR5 에서 **DVFSC gear 전환은 Frequency Change + Controller Update 창을 통해 일어나고, 이때 PHY 가 WCK2CK 재정렬과 gear 별 지연 재로드를 수행** 합니다 — Module 04 §5.7 의 "gear 재정렬이 끝나기 전에는 데이터를 발행하지 않는다" 는 체크가 바로 이 DFI 창과 맞물립니다.

:::note[DV 관점 — DFI 에서 무엇을 검증하나]
- **핸드셰이크 프로토콜** — req↔ack 순서, req 가 ack 전에 내려가지 않는지, ctrlupd/phyupd 창 동안 명령·데이터 발행이 금지되는지.
- **gear 의존 latency** — `dfi_t*`(write/read latency 등)가 현재 gear 에 맞게 프로그래밍됐는지. cycle 이 아니라 ns/gear 기준으로 보므로 **절차적 SV 체커**가 적합(Module 04 §5.7).
- **update ↔ retraining 연동** — phyupd/ctrlupd 창에서 재정렬·ZQ 가 실제 수행되고, 창이 닫힌 뒤에만 트래픽이 재개되는지.
:::

### 5.9 BL2 에서의 DRAM Training (BootROM 연결)

부팅 직후에는 DRAM 이 아직 초기화되지 않은 상태이므로, BL1(BootROM) 은 on-chip SRAM 에서만 실행됩니다. BootROM 은 BL2 를 SRAM 에 로드한 뒤 검증까지만 담당합니다. 실제 DRAM Training 은 BL2(First Stage Bootloader) 에서 수행됩니다. Training 코드는 수 KB 에서 수십 KB 에 달하고 PVT 마다 다른 결과를 만들어 내므로 불변인 BootROM 에 넣기 부적합합니다. 또한 메모리 세대가 바뀌면 Training 알고리즘도 바뀌므로 업데이트가 가능한 BL2 에 두는 것이 맞습니다. BL2 가 Training 을 완료하면 DRAM 이 사용 가능한 상태가 되고, 이후 BL3x 를 DRAM 에 로드하여 정상 부팅을 이어갑니다.

부팅 시퀀스에서 DRAM Training 의 위치를 정리하면:

- **BL1 (BootROM)**: SRAM 에서 실행, DRAM 미초기화(Training 전), BL2 를 SRAM 에 로드 + 검증.
- **BL2 (FSBL)**: DRAM Controller 초기화 ← _여기서 Training 수행_. MC 레지스터 설정 → DRAM Device MRS 설정 → Training 시퀀스 실행(CBT → WCK2CK → WL → Gate → DQ → Eye → VREF) → Training 완료로 DRAM 사용 가능 → BL3x 를 DRAM 에 로드.

Training 이 BL2 에 있는 이유는 코드가 크고 복잡하며(수 KB ~ 수십 KB), PVT 마다 다른 결과라 런타임 결정이 필요하고, 메모리 세대별로 Training 이 달라 업데이트가 가능해야 하기 때문입니다 — 불변인 BootROM 에 넣기 부적합합니다.

### 5.10 Q&A — 자주 묻는 질문

**Q: DRAM Training이 왜 필요한가?**
> "데이터 유효 윈도우가 수백 ps로 극히 좁기 때문이다(LPDDR5X 고gear 기준). PCB 배선 차이, PVT 변동, 크로스토크로 인해 고정 타이밍으로는 정확한 샘플링이 불가능하다. LPDDR5는 CBT(CA[6:0] 정렬) → WCK2CK leveling(WCK-CK 정렬, LPDDR5 고유) → DQ/Write/Read Training 순으로 단계가 많고 내부 Vref를 학습한다. 이렇게 각 채널/바이트 레인의 타이밍을 동적으로 최적화한다."

**Q: Write Leveling의 원리는?**
> "MC가 스트로브(WCK)를 점진적으로 지연시키면서 DRAM이 CK 엣지에서 스트로브를 샘플링한 결과를 DQ로 반환한다. DQ가 0→1로 전환되는 지점이 스트로브와 CK가 정렬된 최적 지연값이다. 바이트 레인마다 PCB 배선 길이가 다르므로, 각 레인의 최적 지연값이 다르다."

**Q: ODT가 필요한 이유와 LPDDR5의 종단은?**
> "고속 버스에서 전송선 끝의 임피던스 불일치는 신호 반사를 일으켜 데이터 오류를 유발한다. ODT는 DRAM 내부에 종단 저항을 내장하여 반사를 방지한다. LPDDR5는 PoP point-to-point single-rank라 전송선이 짧고 비타겟 rank가 없어, 수신하는 쪽의 ODT만 켜면 되므로 종단 제어가 근본적으로 단순하다."

**Q: LPDDR5X 고gear에서 Equalization이 필수인 이유는?**
> "LPDDR5X 고gear에서는 비트 간격이 극히 좁아 ISI(Inter-Symbol Interference)로 수신단의 Eye가 거의 닫힌다. CTLE(아날로그 고주파 부스트)와 DFE(이전 비트의 ISI를 디지털로 제거)를 조합하여 Eye를 복원한다. DRAM 수신단(Write)에는 DFE, PHY 수신단(Read)에는 CTLE+DFE를 적용하며, Training으로 계수를 최적화한다. 단 DVFSC 저gear에서는 UI가 넓어져 EQ 요구가 완화된다."

**Q: LPDDR5 Training의 고유 항목은?**
> "LPDDR5의 고유 항목은 WCK2CK Leveling(고속 데이터 클럭 WCK를 명령 클럭 CK에 정렬)과 CBT(Command Bus Training, CA[6:0] 단일종단 다중사이클 정렬, Mode1/2)이다. DVFSC로 gear가 바뀌어 WCK:CK 비가 달라지면 WCK2CK를 재정렬해야 한다. 데이터 스트로브를 DQS 하나로 해결하던 직전 세대 LPDDR4와 달리, 데이터 클럭이 별도의 WCK로 분리되어 정렬 단계가 더 많다."

**Q: DFI 가 무엇이고, DV 에서 왜 중요한가?**
> "DFI(DDR PHY Interface)는 MC와 PHY 사이의 업계 표준 신호 규약으로, 컨트롤러 IP와 PHY IP 공급사를 분리해 조합 가능하게 한다. 명령/주소·write/read 데이터 외에, DV에서 핵심은 제어 핸드셰이크다 — Controller Update(dfi_ctrlupd_req/ack, 컨트롤러가 PHY에 ZQ/retraining 창 부여), PHY Update(dfi_phyupd_req/ack, PHY가 긴급 캘리브레이션 창 요청), Low Power, Init(dfi_init_start/complete), 그리고 Frequency Change(dfi_freq_fsp)다. 특히 LPDDR5의 DVFSC gear 전환은 Frequency Change + Controller Update 창에서 WCK2CK 재정렬과 함께 일어나므로, '창 동안 트래픽 정지 / 창 종료 후 재개'와 gear별 dfi_t* latency 갱신을 검증한다."

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'PHY 는 한 번 training 하면 그대로다']
**실제**: Training 은 boot 시 + 운영 중 주기적 retraining 이 모두 필요합니다. ZQ Short 가 수십 초마다 자동, full retraining 이 온도 임계 초과 시 trigger.<br>
**왜 헷갈리는가**: "한 번 잘 맞추면 계속 맞을 것" 이라는 직관 — 실제로는 PVT drift 가 상시.
:::
:::danger[❓ 오해 2 — 'DLL 과 PLL 은 비슷한 회로다']
**실제**: PLL 은 _주파수 합성_ (system clock → DDR clock), DLL 은 _위상 정렬_ (스트로브-CK). 위치도 다르고 (PLL: MC/PHY, DLL: DRAM 내부), LPDDR5 는 DLL-less 경향으로 PHY 가 WCK2CK Training 을 통해 phase 를 처리합니다.
:::
:::danger[❓ 오해 3 — 'CTLE 만 있으면 충분, DFE 까지 필요 없다']
**실제**: CTLE 는 _노이즈도_ 함께 증폭합니다. DFE 는 이미 결정된 비트의 ISI 만 빼므로 노이즈 증폭이 없습니다. LPDDR5X 고gear 는 CTLE + DFE 의 _상호 보완_ 으로 eye 를 복원합니다.
:::
:::danger[❓ 오해 4 — 'LPDDR5 는 종단(ODT)을 신경쓸 필요가 없다']
**실제**: LPDDR5 는 point-to-point single-rank 라 rank 별 종단 절환 같은 복잡함은 없지만, 종단 자체가 없는 것은 아닙니다. Write/Read 방향에 따라 _수신하는 쪽_ 의 ODT 를 켜서 반사를 억제해야 하며, 이 값도 신호 무결성에 영향을 줍니다.
:::
:::danger[❓ 오해 5 — 'LPDDR5 의 CA 는 저속이라 training 이 불필요하다']
**실제**: 직전 세대 LPDDR4 의 CA 는 상대적으로 저속이라 정밀 training 부담이 작았습니다. 그러나 **LPDDR5 의 CA 는 CA[6:0] 단일종단 다중사이클** 이라 노이즈 마진이 작아 **CBT(Command Bus Training, Mode1/2)** 가 필수이고, 판정 전압으로 내부 Vref 까지 함께 학습합니다.
:::
### DV 디버그 체크리스트 (PHY/Training 영역의 흔한 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Boot 시 Training 무한 실패 / converge 안 함 | DRAM 미초기화 / CKE/RESET 시퀀스 문제 | Phase 1 power sequence, MRS 발행 timestamp |
| 특정 lane 만 read error | per-lane DQ delay tap 학습 실패 | lane 별 tap 수렴 값, eye margin |
| 고온에서만 read corruption | retraining trigger 조건 / VREF drift | 온도 센서 (MR4), VREF 학습 timestamp |
| Write 만 fail (Read OK) | Write Leveling 학습 결과 / 스트로브(WCK)-CK 정렬 | WL tap 값 vs PCB 길이 추정 |
| 특정 ZQ short 직후 RD/WR fail | ZQ 와 RD/WR 명령 충돌 (tZQCS 위반) | ZQCS issue timestamp + 인접 RD/WR |
| CA decode error | CBT(Command Bus Training) 누락 또는 실패 | CBT Mode1/2 흐름, CA delay tap, 내부 Vref |
| LPDDR5 DVFSC 전환 후 fail | WCK2CK retraining 누락 / 저장된 값 복원 실패 | DVFSC FSM, WCK 위상 |

:::caution[실무 주의점 — ZQ Calibration 타이밍 위반으로 ODT 임피던스 오동작]
**현상**: 온도 변화 이후 Write 데이터가 Eye 중심에서 벗어나 비트 오류율이 증가하거나, 주기적 ZQ Calibration 도중 RD/WR 명령이 겹쳐 데이터 오염 발생.

**원인**: ZQCS(Short Calibration)는 tZQCS(80ns) 동안 DQ/스트로브 드라이버를 완전히 점유하므로, 이 구간에 RD/WR 명령이 발행되면 정의되지 않은 동작. MC가 Calibration 스케줄러와 명령 스케줄러를 독립적으로 운용할 때 충돌 발생 가능.

**점검 포인트**: ZQCS 명령 발행 시점에서 tZQCS 이전 RD/WR 명령의 완료 여부 확인. ZQ 는 PHY 의 고정 클럭 도메인에 묶인 관계라 SVA 로 검증하기 적합하다 — `zq_start → ##[1:tZQCS_ns] (no_rd && no_wr)` assertion 으로 확인. 참고로 MC/서브시스템 레벨의 ns 기반 timing(gear/DVFS 의존)은 SVA `##N` 대신 절차적 SV 체커로 검증하는 것이 맞다(Module 04 §5.7 참고). 주기적 Calibration 간격이 온도 변화 속도보다 충분히 짧은지 스펙(tZQCAL_interval ≤ 1ms) 확인.
:::
---

## 7. 핵심 정리 (Key Takeaways)

- **LPDDR5 PHY 정체성 = CK + WCK 2-클럭**: 명령용 저속 CK + 데이터용 고속 WCK(WCK:CK = 2:1/4:1). 데이터 스트로브는 WCK/RDQS(직전 세대 LPDDR4 가 쓰던 DQS 대신).
- **PHY = 명령/데이터의 전기적 변환 + 캘리브레이션**: 클럭 위상 정렬, 임피던스 보정, training 으로 lane-by-lane timing 최적화. LPDDR5 는 DLL-less 경향 — WCK2CK Training 으로 위상을 정렬.
- **Training 은 boot 시 한 번이 아니다** — 운영 중 임피던스 Short / 주기적 retraining + DVFSC gear 전환 시 WCK2CK 재정렬로 PVT/주파수 변동 보상.
- **LPDDR5 Training**: CBT(CA[6:0] 정렬) + **WCK2CK Leveling(LPDDR5 고유)** + DQ/Write/Read + 내부 Vref + DFE 계수(고gear).
- **Equalization (CTLE + DFE)**: LPDDR5X 고gear 에서 필수, **DVFSC 저gear 에서는 EQ 완화**. CTLE 가 고주파 부스트, DFE 가 ISI 제거.
- **ODT/종단**: LPDDR5 = point-to-point single-rank 라 수신측 종단만 켜면 되어 단순.
- **DFI = MC↔PHY 표준 경계**: 명령/데이터 + 제어 핸드셰이크(Controller/PHY Update, Low Power, Init, Frequency Change). LPDDR5 DVFSC gear 전환은 Frequency Change + Update 창에서 WCK2CK 재정렬과 함께 일어남. `dfi_t*` latency 는 gear 의존.
- **BL2 에서 Training 수행** — 코드 크고 PVT 의존이라 BootROM 부적합. Training 결과는 chip-by-chip / 온도-by-온도 다름.

:::caution[실무 주의점]
- "PHY 가 한 번 set up 되면 끝" 은 가장 빈번한 오해 — retraining trigger 조건을 검증 시나리오에 반드시 포함.
- LPDDR5 종단은 단순하지만 방향(Write/Read)에 따라 수신측 ODT 가 제대로 켜지는지는 확인해야 — 반사가 남으면 eye 가 닫힘.
- LPDDR5 의 DVFSC 전환은 _train 결과 보존 또는 재train_ 둘 중 하나가 일관되게 동작해야 — 둘 다 안 되면 silent corruption.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — Eye width 계산 (Bloom: Apply)]
LPDDR5X 고gear 에서 데이터 전송률이 8533 MT/s 라고 가정하자. _UI (Unit Interval)_ 와 _data valid window_ 는 대략 얼마인가?

<details>
<summary>정답</summary>

- UI = 1 / (8533 × 10^6) ≈ **117 ps** (전송률에 따라 달라짐).
- 데이터 유효 윈도우는 _half UI_ 수준: 수십 ps.
- 실제 jitter / skew 를 제외한 _eye opening_ 은 더 좁아진다.

매우 좁아서 PHY training (CTLE, DFE) 정확도가 critical. (정확한 수치는 gear/전송률에 따라 달라지므로 여기서는 개념적 예시로 본다.)

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
- JEDEC JESD209-5 (LPDDR5/5X) — PHY / training 관련 항목
- *LPDDR5 PHY Training Algorithms* — Cadence / Synopsys WP

---

## 다음 모듈

→ [Module 04 — DRAM DV Methodology](../04_dram_dv_methodology/): 지금까지 본 cell + MC + PHY 를 _어떻게 검증하는가_. Behavioral model, traffic generator, scoreboard, timing SVA, ECC injection.

[퀴즈 풀어보기 →](../quiz/03_memory_interface_phy_quiz/)

