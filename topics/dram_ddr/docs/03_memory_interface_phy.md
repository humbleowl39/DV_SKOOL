# Module 03 — Memory Interface / PHY

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">💾</span>
    <span class="chapter-back-text">DRAM / DDR</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 03</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#ddr-신호-구성">DDR 신호 구성</a>
  <a class="page-toc-link" href="#odt-on-die-termination-신호-무결성의-핵심">ODT (On-Die Termination) — 신호 무결성의 핵심</a>
  <a class="page-toc-link" href="#dll-pll-클럭-생성과-분배">DLL / PLL — 클럭 생성과 분배</a>
  <a class="page-toc-link" href="#equalization-고속-신호-보상-기법">Equalization — 고속 신호 보상 기법</a>
  <a class="page-toc-link" href="#training-왜-필요한가">Training — 왜 필요한가?</a>
  <a class="page-toc-link" href="#zq-calibration-임피던스-매칭">ZQ Calibration — 임피던스 매칭</a>
  <a class="page-toc-link" href="#bl2에서의-dram-training-bootrom-연결">BL2에서의 DRAM Training (BootROM 연결)</a>
  <a class="page-toc-link" href="#qa">Q&A</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Diagram** PHY의 주요 블럭(DLL/PLL, DQ/CA TX/RX, Training engine, ZQ calibration)을 그릴 수 있다.
    - **Apply** Write Leveling, Read DQ Training, CA Training, ZQ Calibration의 순서와 목적을 시나리오에 매핑.
    - **Analyze** PVT(Process/Voltage/Temperature) 변동이 timing margin에 미치는 영향과 보정 메커니즘.
    - **Distinguish** CTLE / DFE 같은 equalization 기법과 적용 위치(Write/Read).
    - **Identify** DDR4 → DDR5에서 추가된 Training 항목과 동기.

!!! info "사전 지식"
    - [Module 01-02](01_dram_fundamentals_ddr.md)
    - 아날로그/디지털 인터페이스 기본 (signal integrity 개념)

## 왜 이 모듈이 중요한가

**PHY는 MC와 DRAM 사이의 물리 계층**으로, 고속(4800+ MT/s)에서 신호 무결성이 가장 큰 도전. **Training 실패 = silent corruption** — silicon이 동작하는 것처럼 보이지만 데이터 변조. PVT 변동(같은 칩이라도 온도 다르면 timing 변경)을 보정하는 것이 검증의 가장 미묘한 영역입니다.

!!! tip "💡 이해를 위한 비유"
    **Memory PHY** ≈ **고속 도로의 톨게이트 + 차량 정렬 (training)**

    DDR 의 GHz 동작은 strobe 정렬, drive strength, ZQ calibration, training 같은 PHY 레이어 작업이 매 순간 보정해 가능. 컨트롤러보다 PHY 가 더 미묘한 영역.

---

## 핵심 개념
**Memory Interface(MI) / PHY = MC의 명령을 DDR 전기 신호로 변환하고, 고속 데이터 전송을 위한 타이밍 캘리브레이션(Training)을 수행하는 물리 계층. PVT(공정/전압/온도) 변동에도 안정적인 데이터 수신을 보장하는 것이 핵심.**

!!! danger "❓ 흔한 오해"
    **오해**: PHY 는 한 번 training 하면 그대로다

    **실제**: Training 은 boot 시 + 주기적 재training (온도 / 전압 변화 대응) 필요. 운영 중 ZQ Calibration 도 수십 초마다 자동.

    **왜 헷갈리는가**: "한 번 잘 맞추면 계속 맞을 것" 이라는 직관. 실제로는 환경 drift 보정이 상시적.
---

## DDR 신호 구성

```
Memory Controller / PHY ←→ DRAM Device

Command/Address (CA) Bus:
  CK/CK# (차동 클럭)
  CS#     (Chip Select)
  RAS#/CAS#/WE# (DDR4) 또는 CA[13:0] (DDR5)
  BA[1:0] (Bank Address)
  BG[1:0] (Bank Group, DDR4) / BG[2:0] (DDR5)
  A[16:0] (Row/Column Address)

Data Bus (per byte lane):
  DQ[7:0]   (데이터, 8-bit per lane)
  DQS/DQS#  (데이터 스트로브, 차동)
  DM/DBI    (데이터 마스크 / Data Bus Inversion)

  DDR4: 8 byte lanes × 8 = 64-bit
  DDR5: Sub-Ch A: 4 lanes × 8 = 32-bit
        Sub-Ch B: 4 lanes × 8 = 32-bit
```

### DQS와 DQ의 관계

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

---

## ODT (On-Die Termination) — 신호 무결성의 핵심

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

  Multi-Rank에서의 ODT:
    Rank 0 (타겟): ODT OFF (데이터 구동 중)
    Rank 1 (비타겟): ODT ON (반사 방지)
    → 비타겟 Rank의 ODT가 더 중요 (park termination)

DDR4 ODT 설정 (Mode Register):
  RTT_NOM (MR1):  Nominal termination (60/120/40/240Ω 등)
  RTT_WR  (MR2):  Write 시 dynamic termination
  RTT_PARK (MR5): 항상 활성화된 park termination

DDR5 ODT 변경점:
  - ODTL (ODT Latency): 명령 대비 ODT ON/OFF 타이밍 정밀 제어
  - NT_ODT (Non-Target ODT): 비타겟 Rank ODT 독립 제어
  - Per-Pin ODT: DQ 핀별 ODT 값 설정 가능

면접 포인트:
  "ODT는 고속 DDR 버스에서 신호 반사를 방지하는 핵심 메커니즘이다.
   DRAM 내부에 종단 저항을 내장하여 PCB 간소화와 신호 무결성을 동시에 달성한다.
   Multi-Rank 구성에서 비타겟 Rank의 Park Termination이 특히 중요하며,
   RTT_NOM, RTT_WR, RTT_PARK 세 값의 최적 조합은 시뮬레이션으로 결정한다."
```

---

## DLL / PLL — 클럭 생성과 분배

```
DLL (Delay-Locked Loop) — DRAM 내부:
  목적: 내부 클럭과 외부 CK의 위상을 정렬
  원리: 지연(delay)을 조절하여 피드백 클럭과 기준 클럭의 위상을 맞춤

  외부 CK ──→ [Variable Delay] ──→ 내부 CK (DQS 생성용)
                    ↑
              [Phase Detector] ←── 피드백
              (지연 증가/감소)

  DLL이 하는 일:
  - Read 시 DQS를 CK에 정렬하여 출력
  - 온도/전압 변화에 따라 지연을 자동 조절
  - DDR4: DLL 필수, DDR5: DLL 제거 (PHY측에서 처리)

PLL (Phase-Locked Loop) — MC/PHY 내부:
  목적: 시스템 클럭에서 DDR 클럭과 그 분주/배수 클럭 생성
  원리: VCO(전압제어발진기)의 주파수를 조절하여 기준 주파수에 Lock

  System CLK ──→ [PFD] ──→ [Loop Filter] ──→ [VCO] ──→ CK 출력
                   ↑                                |
                   +──── [Divider (÷N)] ←───────────+

  PLL이 하는 일:
  - 200 MHz 시스템 클럭 → 1600 MHz DDR 클럭 생성 (×8)
  - 90° 위상 시프트된 클럭 생성 (Read DQS 샘플링용)
  - Jitter 최소화 → Eye Diagram 품질에 직접 영향

DLL vs PLL 차이:
  | 항목    | DLL              | PLL              |
  |--------|------------------|------------------|
  | 동작    | 지연 조절 (위상만)| 주파수 합성       |
  | 위치    | DRAM 내부        | MC/PHY 내부       |
  | 주 목적 | DQS-CK 정렬      | DDR 클럭 생성     |
  | DDR5    | 제거             | 필수 (더 복잡)    |
```

---

## Equalization — 고속 신호 보상 기법

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

---

## Training — 왜 필요한가?

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

### 주요 Training 단계

| Training | 목적 | 시점 |
|---------|------|------|
| **Write Leveling** | DQS-to-CK 스큐 보정 (Write 경로) | 초기화 시 |
| **Read Gate Training** | DQS 수신 시작 타이밍 결정 | 초기화 시 |
| **Read/Write DQ Training** | DQ-to-DQS 비트별 지연 보정 | 초기화 시 |
| **Read Eye Training** | 데이터 유효 윈도우(Eye) 중앙 찾기 | 초기화 시 |
| **VREF Training** | 수신 판정 기준 전압 최적화 | 초기화 시 |
| **ZQ Calibration** | 출력 임피던스 보정 | 주기적 |
| **Periodic Retraining** | 온도 변화 보상 | 런타임 |

### DDR5 CA Training (CS Training) — DDR5에서 새로 추가

```
DDR5에서 CA(Command/Address) 버스도 고속화 → CA 타이밍 정렬 필요

문제:
  DDR4: RAS#/CAS#/WE# 개별 핀 → 상대적으로 저속, 마진 충분
  DDR5: CA[13:0] 멀티플렉싱 → 클럭 속도에 동기 → 타이밍 마진 축소

CS Training 과정:
  1. MC가 CS Training 모드 진입 (MPC 명령)
  2. MC가 CA 핀에 알려진 패턴 전송
  3. DRAM이 CK 엣지에서 CA를 샘플링 → DQ로 결과 반환
  4. MC가 CA 지연을 조절하며 반복
  5. 최적 CA-CK 정렬 지점 결정

  이것이 중요한 이유:
  - CA 타이밍 오류 → 잘못된 명령 해석 → 치명적 오동작
  - DDR4에서는 불필요했으나 DDR5에서 필수가 됨
  - LPDDR5에서는 CBT (Command Bus Training)이라 부름
```

### Write Leveling 상세

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

### Eye Diagram — 데이터 유효 윈도우

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

---

## ZQ Calibration — 임피던스 매칭

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

---

## BL2에서의 DRAM Training (BootROM 연결)

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

---

## Q&A

**Q: DRAM Training이 왜 필요한가?**
> "DDR4/5의 데이터 유효 윈도우가 수백 ps로 극히 좁기 때문이다. PCB 배선 차이, PVT 변동, 크로스토크로 인해 고정 타이밍으로는 정확한 샘플링이 불가능하다. Training은 Write Leveling(DQS-CK 정렬), DQ Training(비트별 지연 보정), Eye Training(최적 샘플링 포인트 탐색), VREF Training(판정 전압 최적화)을 통해 각 채널/바이트 레인의 타이밍을 동적으로 최적화한다."

**Q: Write Leveling의 원리는?**
> "MC가 DQS를 점진적으로 지연시키면서 DRAM이 CK 엣지에서 DQS를 샘플링한 결과를 DQ로 반환한다. DQ가 0→1로 전환되는 지점이 DQS와 CK가 정렬된 최적 지연값이다. 바이트 레인마다 PCB 배선 길이가 다르므로, 각 레인의 최적 지연값이 다르다."

**Q: ODT가 필요한 이유와 Multi-Rank에서의 동작은?**
> "고속 DDR 버스에서 전송선 끝의 임피던스 불일치는 신호 반사를 일으켜 데이터 오류를 유발한다. ODT는 DRAM 내부에 종단 저항을 내장하여 반사를 방지한다. Multi-Rank 구성에서는 타겟 Rank가 데이터를 구동할 때 비타겟 Rank의 ODT(RTT_PARK)가 특히 중요하다. RTT_NOM(Nominal), RTT_WR(Write 시), RTT_PARK(상시)의 세 값을 Mode Register로 설정하며, 최적 조합은 채널 시뮬레이션으로 결정한다."

**Q: DDR5에서 Equalization이 필수인 이유는?**
> "DDR5 4800+ MT/s에서는 비트 간격이 극히 좁아 ISI(Inter-Symbol Interference)로 수신단의 Eye가 거의 닫힌다. CTLE(아날로그 고주파 부스트)와 DFE(이전 비트의 ISI를 디지털로 제거)를 조합하여 Eye를 복원한다. DRAM 수신단(Write)에는 DFE, PHY 수신단(Read)에는 CTLE+DFE를 적용하며, Training으로 계수를 최적화한다."

**Q: DDR4 대비 DDR5에서 추가된 Training 항목은?**
> "CA Training(CS Training)이 가장 중요한 추가 항목이다. DDR5에서 CA 버스가 멀티플렉싱으로 변경되어 타이밍 마진이 축소되었기 때문이다. 또한 DFE 계수 Training, Read/Write Preamble Training이 추가되었다. LPDDR5에서는 WCK2CK Training(WCK-CK 위상 정렬)과 CBT(Command Bus Training)가 추가된다."

---
!!! warning "실무 주의점 — ZQ Calibration 타이밍 위반으로 ODT 임피던스 오동작"
    **현상**: 온도 변화 이후 Write 데이터가 Eye 중심에서 벗어나 비트 오류율이 증가하거나, 주기적 ZQ Calibration 도중 RD/WR 명령이 겹쳐 데이터 오염 발생.
    
    **원인**: ZQCS(Short Calibration)는 tZQCS(80ns) 동안 DQ/DQS 드라이버를 완전히 점유하므로, 이 구간에 RD/WR 명령이 발행되면 정의되지 않은 동작. MC가 Calibration 스케줄러와 명령 스케줄러를 독립적으로 운용할 때 충돌 발생 가능.
    
    **점검 포인트**: ZQCS 명령 발행 시점에서 tZQCS 이전 RD/WR 명령의 완료 여부 확인. SVA에서 `zq_start → ##[1:tZQCS_ns] (no_rd && no_wr)` assertion 구현. 주기적 Calibration 간격이 온도 변화 속도보다 충분히 짧은지 스펙(tZQCAL_interval ≤ 1ms) 확인.

## 핵심 정리

- **PHY = 명령/데이터의 전기적 변환 + 캘리브레이션**: DLL/PLL로 클럭 위상 정렬, ZQ로 임피던스 보정.
- **Training 종류**: Write Leveling(CK-DQS 정렬), Read DQ Training(eye center), CA Training(CMD bus margin), VREF Training.
- **PVT 보정**: 온도/전압 변동에 따라 timing 변경 → 주기적 ZQ + retraining.
- **Equalization**: 고속 신호의 ISI 제거. CTLE(아날로그) + DFE(디지털). Write에는 DRAM 측 DFE, Read에는 PHY 측 CTLE+DFE.
- **DDR5 추가 Training**: CA Training (CA 멀티플렉싱), DFE 계수, Preamble. LPDDR5는 WCK2CK + CBT 추가.
- **Initialization 흐름**: BootROM에서 PHY power-up → BL2가 Training 수행 (코드 큼, PVT 의존). Training 완료 후 정상 traffic 시작.

## 다음 단계

- 📝 [**Module 03 퀴즈**](quiz/03_memory_interface_phy_quiz.md)
- ➡️ [**Module 04 — DV Methodology**](04_dram_dv_methodology.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../02_memory_controller/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Memory Controller 아키텍처</div>
  </a>
  <a class="nav-next" href="../04_dram_dv_methodology/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">DRAM DV 검증 전략</div>
  </a>
</div>
