# Module 05 — Physical Layer & LTSSM

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="intercon">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🔌</span>
    <span class="chapter-back-text">PCI Express</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 05</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-공항-관제-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-power-on-부터-l0-도달까지의-ltssm-경로">3. 작은 예 — Power-on → L0 의 한 사이클</a>
  <a class="page-toc-link" href="#4-일반화-phy-의-3-축과-ltssm-의-3-그룹">4. 일반화 — PHY 3 축 + LTSSM 3 그룹</a>
  <a class="page-toc-link" href="#5-디테일-sub-block-eq-4-phase-lane-자동-처리">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Diagram** PHY 의 sub-block (PCS / PMA / SerDes / Equalization) 과 신호 흐름을 그릴 수 있다.
    - **Trace** LTSSM 의 11 state 진입/탈출 트리거를 신호 (TS1/TS2, Electrical Idle) 와 함께 추적한다.
    - **Compare** Gen3+ 의 4-phase Equalization (Phase 0/1/2/3) 와 그 의도를 비교한다.
    - **Diagnose** "Link up 안 됨" 시나리오를 LTSSM state 별로 가능한 원인을 좁힌다.
    - **Explain** "PCIe link 는 항상 Gen 1 으로 시작" 이라는 원칙과 그 이후 Recovery + EQ 로 Gen up 되는 절차를 설명한다.

!!! info "사전 지식"
    - Module 01 (lane / encoding 기본)
    - Module 02 (PHY 의 책임)

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _Link up 안 됨_

당신은 새 SoC + PCIe device. Boot 시 _link 가 L0 진입 안 됨_. driver 가 _device 인식 못함_.

진단:
- LTSSM trace 확인.
- `Detect → Polling → Polling.Compliance` 에서 멈춤.
- 원인: _RX 전기 신호_ 가 _threshold_ 보다 약함 → polling 단계에서 _peer 인식 실패_.

해법:
- **EQ preset** 조정 (Tx 의 pre-emphasis).
- **CTLE/DFE** 조정 (Rx 의 amplification).
- PCB **trace length** 짧게.

**LTSSM 11 state 의 의미**: 각 state 가 _link bring-up_ 의 _한 단계_. 어디서 멈췄는지 = _문제의 layer_.

| State | 의미 | 멈춤 원인 |
|-------|------|---------|
| Detect | RX 신호 감지 | RX path 단선 |
| Polling | TS1/TS2 교환 | 전기 신호 약함 |
| Configuration | Lane width, speed 협상 | 협상 mismatch |
| L0 | 정상 동작 | (성공) |
| Recovery | 일시 회복 | 신호 품질 변동 |

**PCIe link bring-up 의 모든 진단은 LTSSM state 를 보는 데서 시작** 합니다. 그리고 Gen3+ 부터는 equalization 단계를 거쳐 link 가 안정화 — 잘못된 EQ preset 이나 channel 특성 misalignment 가 무수한 production failure 의 원인. PHY 와 LTSSM 을 모르면 "link recovery 빈발" 이라는 증상 앞에서 black box.

이 모듈의 어휘 — **Detect/Polling/Configuration/L0/Recovery, TS1/TS2, EQ Phase 0..3, Tx FFE/Rx CTLE/DFE** — 가 이후 모든 link bring-up 디버그, Gen 변경, ASPM 설계 (Module 07), retimer 구성의 기본 단위.

---

## 2. Intuition — 공항 관제 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **LTSSM** ≈ **공항의 항공기 관제 절차**.<br>
    Detect = 활주로 도착. Polling = 관제와 무선 시범 통신. Configuration = 게이트 / lane / link width 협상. L0 = 정상 운항. Recovery = 난기류 — 잠시 회복. L1 / L2 = 주기 (저전력). Disabled / Loopback / Hot Reset = 비상 / 테스트.

### 한 장 그림 — PHY 의 3 sub-block + LTSSM 의 큰 흐름

```
   ┌────────────────────────── PHY ──────────────────────────┐
   │                                                           │
   │   ┌── PCS ──┐    ┌── PMA ──┐    ┌── Analog ──┐            │
   │   │ Frame   │ →  │ SerDes  │ →  │ Tx FFE     │ → wire     │
   │   │ Encode  │    │ PLL     │    │ Rx CTLE    │            │
   │   │ Stripe  │    │ CDR     │    │ Rx DFE     │            │
   │   └─────────┘    └─────────┘    └────────────┘            │
   │                                                           │
   │   ┌────────────────── LTSSM ────────────────────────┐     │
   │   │                                                  │     │
   │   │   Bring-up    : Detect → Polling → Config → L0  │     │
   │   │   Steady      : L0 (normal)                      │     │
   │   │   Power-saving: L0s, L1 (.1 .2), L2              │     │
   │   │   Recovery    : EQ retrain, Gen change           │     │
   │   │   Test/Reset  : Disabled, Loopback, Hot Reset    │     │
   │   │                                                  │     │
   │   └──────────────────────────────────────────────────┘     │
   │                                                           │
   └───────────────────────────────────────────────────────────┘
```

### 왜 이 디자인인가 — Design rationale

PHY 가 풀어야 하는 세 문제는 _시간 척도가 다름_.

1. **Bit-level**: Tx 가 0/1 을 보낼 때 wire 위에서 ISI 와 noise 를 어떻게 견디는가 → SerDes + Equalization (ps ~ ns).
2. **Symbol-level**: 받은 bit 를 의미 있는 symbol/byte 로 어떻게 align 하는가 → Bit Lock + Symbol Lock (μs).
3. **Link-level**: 양 끝 device 가 어떤 width/speed/EQ 로 합의할 것인가 → LTSSM (ms).

세 문제를 한 모듈로 풀려고 하면 디버그가 불가능 — _bit 가 깨지나, symbol 이 align 안 되나, capability 가 mismatch 인가_ 가 섞여 보임. **PCS + PMA + Analog + LTSSM** 의 sub-block 분리가 이 문제를 풀고, 각 단계의 진단을 독립화합니다.

---

## 3. 작은 예 — Power-on 부터 L0 도달까지의 LTSSM 경로

가장 단순한 시나리오. RC 와 EP 모두 Gen3 capable, x4 link. Power-on 후 L0 에 도달하는 한 사이클.

```
   Time →

   Power-on
       │
       ▼
   ┌──────────────┐
   │   Detect     │  ← Tx 가 short pulse 송신, 상대 receiver 의 termination 검출
   └──────┬───────┘     (양 끝의 termination 이 켜져 있어야 함)
          │ receiver detected
          ▼
   ┌──────────────┐
   │   Polling    │  ← Gen 1 (2.5 GT/s) 으로 시작
   │   .Active    │     TS1 송신 + 수신 시도
   │              │     ├─ Bit Lock (CDR 동기) ─ 0101.. 박자
   │              │     └─ Symbol Lock (COM 발견) ─ 10b/130b 경계
   │              │     TS1 8 개 받으면 → .Configuration
   │   .Config    │     TS2 송신 + 수신 (capability 광고)
   │              │     TS2 8 개 받으면 → 다음 state
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Configuration│  ← Link Number, Lane Number 협상
   │              │     Lane reversal / polarity inversion 자동 보정
   │              │     Link width 결정 (x4)
   │              │     Configuration.Idle 8 cycle → L0
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │      L0      │  ← Gen 1 의 L0! 아직 Gen 3 아님!
   │   (Gen 1)    │     TLP/DLLP 송수신 가능
   └──────┬───────┘
          │ SW 가 Gen up 명령 또는 capability 합의에 따라 자동
          ▼
   ┌──────────────┐
   │   Recovery   │  ← Gen 3 으로 speed change 시도
   │   .RcvrLock  │     속도 올린 뒤 Bit/Symbol Lock 재달성
   │   .RcvrCfg   │     TS1/TS2 재교환
   │   .Equaliz.  │  ← Gen3+ 만의 4 phase EQ
   │              │     Phase 0 → 1 → 2 → 3 (양 끝 Tx FFE 협상)
   │   .Idle      │     안정화
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │      L0      │  ← 이제 Gen 3 의 L0 — 정상 운영
   │   (Gen 3)    │
   └──────────────┘
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | 양 끝 PHY | Detect — Tx pulse 로 상대 termination 검출 | 케이블/connector 가 연결되었는지 |
| ② | 양 끝 | Polling.Active — Gen1 으로 TS1 송신 | 호환성 보장 (모두 Gen1 부터) |
| ③ | Receiver | Bit Lock (CDR) → Symbol Lock (COM 검출) | 박자 + 경계 |
| ④ | 양 끝 | Polling.Configuration — TS2 교환, capability 광고 | 양쪽이 어디까지 지원하는지 |
| ⑤ | 양 끝 | Configuration — Link/Lane #, width 결정 | Lane reversal/polarity 자동 보정 |
| ⑥ | 양 끝 | L0 (Gen1) 도달 | 임시 안정 — 합의된 width 의 최저 속도 |
| ⑦ | 양 끝 | Recovery 진입, Gen3 으로 retrain | speed change |
| ⑧ | 양 끝 | EQ Phase 0..3 — Tx FFE coefficient 협상 | channel 별 BER 최적화 |
| ⑨ | 양 끝 | L0 (Gen3) — 정상 운영 | spec 의 정점 |

!!! note "여기서 잡아야 할 두 가지"
    **(1) PCIe link 는 _항상_ Gen 1 으로 시작한다.** Gen3 capable 이라도 처음에는 Gen1 의 L0 에 들어간 뒤, Recovery 를 거쳐 속도를 올린다. "Gen3 capable 인데 Gen1 으로 떠 있다" → Recovery + speed change 가 안 일어났다는 신호. <br>
    **(2) Recovery 는 실패가 아니라 _기능_ 이다.** Gen up, EQ 재실행, BER 임계 초과 회복, Hot Reset 등 여러 시나리오의 공통 경로. L0 ↔ Recovery 를 자주 왕복하는 link 는 이상이지만, _bring-up 시_ Recovery 통과는 정상.

---

## 4. 일반화 — PHY 의 3 축과 LTSSM 의 3 그룹

### 4.1 PHY 의 3 sub-block

| Sub-block | 책임 | 핵심 회로 |
|---|---|---|
| **PCS (Physical Coding Sublayer)** | Framing, Encoding, Scrambling, Lane stripe | Encoder/Decoder, LFSR, Stripe FIFO |
| **PMA (Physical Medium Attachment)** | SerDes, PLL, CDR | Tx FIFO + Serializer / Rx CDR + Deserializer |
| **Analog Front-End** | Tx driver + FFE, Rx CTLE / DFE / AGC | analog circuit |

### 4.2 LTSSM 의 3 그룹 (11 state)

| 그룹 | State | 역할 |
|---|---|---|
| **Bring-up** | Detect, Polling, Configuration, L0 | Power-on → 정상 운영 도달 |
| **Power-saving** | L0s, L1 (.1, .2), L2 | Idle 시 전력 절감 |
| **Recovery / Test** | Recovery, Disabled, Loopback, Hot Reset | EQ retrain, Gen change, 진단, reset |

### 4.3 EQ Phase 의 의미 (Gen3+)

Gen3 부터 _link 가 channel 별 best EQ 를 협상_ 합니다. 한 가지 EQ 로 모든 channel (PCB trace + connector + cable) 을 cover 할 수 없기 때문.

```
   Phase 0 (initial)  : preset 적용
   Phase 1 (DP →)    : DP 의 Tx FFE 를 UP 의 Rx 가 측정 + 변경 요청
   Phase 2 (UP →)    : UP 의 Tx FFE 를 DP 의 Rx 가 측정 + 변경 요청
   Phase 3 (final)   : 안정화 확인, EQ 종료
```

→ EQ 가 잘 안 맞으면 BER 폭증 → Recovery 빈발 → throughput 저하.

---

## 5. 디테일 — sub-block, EQ 4 phase, Lane 자동 처리

### 5.1 Physical Layer Sub-block

```
                ┌──────────────────────────────────┐
                │    PCS (Physical Coding Sublayer)│
                │  - Framing (STP/END / SDP/EDS)   │
                │  - Scrambling (LFSR)              │
                │  - 8b/10b ↔ 128b/130b ↔ FLIT     │
                │  - Lane stripe / de-stripe       │
                └────────────────┬─────────────────┘
                                  │
                ┌────────────────▼─────────────────┐
                │    PMA (Physical Medium Attachmt)│
                │  - SerDes (Serializer/Deserializer)
                │  - PLL / clock multiplier        │
                │  - CDR (Clock-Data Recovery)     │
                └────────────────┬─────────────────┘
                                  │
                ┌────────────────▼─────────────────┐
                │    Analog Front-End              │
                │  - Tx driver + FFE (Pre/Post tap)│
                │  - Rx CTLE / DFE / AGC          │
                └────────────────┬─────────────────┘
                                  │ differential pair (TX+/TX-, RX+/RX-)
                                  ▼
                            Connector / wire
```

#### Equalization (Gen3+ 핵심)

| 단계 | 위치 | 역할 |
|------|------|------|
| **Tx FFE** (Feed Forward Equalizer) | Tx | Pre-cursor + main + Post-cursor 3-tap, channel ISI 미리 보상 |
| **Rx CTLE** (Continuous-Time Linear Equalizer) | Rx | Frequency-domain low-freq attenuation 보상 |
| **Rx DFE** (Decision Feedback Equalizer) | Rx | 이전 결정으로 ISI 제거, 가장 효과적 |
| **AGC** (Automatic Gain Control) | Rx | 신호 amplitude 정규화 |

→ Gen6 PAM4 는 EQ 가 더 복잡 (eye 가 3 개 → 마진 ↓), CTLE+DFE 마진이 핵심.

### 5.2 LTSSM — 11 States (전체)

```
                 ┌──────────┐
                 │ Detect   │ Receiver detection (TX 가 short pulse)
                 └────┬─────┘
                      │ receiver detected
                      ▼
                 ┌──────────┐
                 │ Polling  │ TS1/TS2 교환, lane 동기, 속도 협상
                 └────┬─────┘
                      │ TS2 교환 완료
                      ▼
                 ┌──────────┐
                 │Configurat│ Link/Lane number 결정, link width, speed
                 │   -ion   │
                 └────┬─────┘
                      │
                      ▼
                ┌──────────┐
                │   L0     │ ◀─────────────────┐
                │  정상    │                    │
                └─┬─┬──────┘                    │ Link 회복 / Gen up
                  │ │                            │
                  │ │ ASPM L0s                  │
                  │ ▼                            │
                  │ ┌──────────┐                │
                  │ │  L0s     │ ── FTS ───────┘ (저전력 짧은 기간)
                  │ └──────────┘
                  │
                  │ ASPM/PCI-PM L1, L2
                  ▼
                ┌──────────┐         ┌──────────┐
                │   L1     │         │   L2     │  (Aux power만, deep sleep)
                └─┬────────┘         └──────────┘
                  │
                  │ Recovery 트리거
                  ▼
                ┌──────────┐
                │ Recovery │  → EQ phase 재실행, retrain
                │          │  → 성공 시 L0 복귀
                └────┬─────┘
                     │ 실패
                     ▼
                ┌──────────┐ ┌──────────┐ ┌──────────┐
                │ Disabled │ │ Loopback │ │ Hot Reset│
                └──────────┘ └──────────┘ └──────────┘
```

#### State 별 핵심 동작

| State | 송신 신호 | 다음 state 트리거 |
|-------|-----------|------------------|
| **Detect** | Detect pulse | Receiver detected → Polling |
| **Polling** | TS1 (Polling.Active) → TS2 (Polling.Configuration) | TS2 8 개 송수신 완료 → Configuration |
| **Configuration** | TS1/TS2 with link/lane #s | Configuration.Idle 8 cycle → L0 |
| **L0** | TLP / DLLP | 트리거에 따라 L0s, L1, Recovery, … |
| **L0s** | EIOS → idle | FTS 받음 → L0 (몇 백 ns) |
| **L1** | EIOS → idle | TS1 → Recovery → L0 (몇 us) |
| **L2** | (전원 거의 차단) | Beacon / WAKE# → Detect → … |
| **Recovery** | TS1/TS2 + EQ | EQ 성공 → L0; 실패 → Detect 또는 Hot Reset |
| **Disabled** | Electrical idle | SW 가 enable 시 Detect |
| **Loopback** | (test pattern echo) | LB exit 명령 시 Detect |
| **Hot Reset** | TS1 with Hot Reset bit | 끝나면 Detect |

### 5.3 Polling 상세

```
   Detect → Polling.Active
       │
       │ TS1 송신, TS1/TS2 받기 시작
       │
       │ TS1 8 개 받으면 → Polling.Configuration
       ▼
   Polling.Configuration
       │
       │ TS2 송신, TS2 받음
       │
       │ TS2 8 개 송수신 완료 → Configuration
       ▼
   Configuration
```

**TS1/TS2 Ordered Set** 의 주요 field:

- Link Number, Lane Number — 링크/lane 식별
- Symbol 5: Data Rate Identifier — 협상 가능 속도 (Gen2/3/4/5/6/7)
- Symbol 6-9: Training Control bits — Hot Reset, Disable Link, Loopback, Compliance, Equalization

→ Polling 단계에서 서로 capable 한 최대 속도 가 정해짐. 하지만 실제로 그 속도로 link 진입하려면 **Configuration → L0 → Recovery (EQ) → 새 속도의 L0** 절차를 거침 (Gen3+).

!!! example "Bit Lock ↔ Symbol Lock — Polling 의 두 단계 박자 맞추기"
    **Bit Lock (비트 박자 맞추기)**:

    - Sender 가 `01010101...` 처럼 1-bit 단위로 규칙적으로 변하는 훈련용 신호 (TS1/TS2 의 일부) 를 송출.
    - Receiver 의 **CDR (Clock Data Recovery)** 회로가 이 신호의 transition 을 보고 자기 내부 시계를 sender 의 박자에 동기화.
    - 이 단계에서는 "한 비트의 시작/끝" 만 알아냄.

    **Symbol Lock (문자 경계 찾기)**:

    - Bit 박자는 맞췄지만 10-bit (8b/10b) 또는 130-bit (128b/130b) 의 시작/끝을 알아야 데이터로 해석 가능.
    - Sender 가 **COM (Comma) symbol** 이라는 특수 패턴을 주기적으로 섞어 송출.
    - Receiver 가 COM 을 발견하는 순간 "그 위치가 symbol 경계" 로 인식, alignment 완료.

    → 두 lock 이 모두 끝나야 Polling 이 다음 state 로 진행. PHY 검증 시 "Polling 에서 stuck" 의 진단은 Bit Lock 단계 vs Symbol Lock 단계 어디서 막혔는지부터.

!!! note "PCIe link 는 항상 Gen 1 부터 시작"
    모든 PCIe device 는 처음 깨어날 때 **무조건 Gen 1 (2.5 GT/s)** 으로 시작. 이유: 호환성 보장 — 양 끝의 capability 를 모를 때 가장 보수적인 속도가 안전.

    절차:

    1. Detect → Polling.Active 진입 시 **Gen 1** 으로 동작.
    2. Polling 단계에서 양 끝이 TS1/TS2 안에 "나는 Gen N 까지 지원" 정보 교환.
    3. 합의된 최대 속도가 정해진 뒤, **Recovery 상태로 일부러 넘어가** clock 을 새 Gen 으로 올리고 retraining.
    4. Retraining 성공 시 합의 속도의 L0 진입.

    검증 시 "Gen 4 capable 인데 link 가 Gen 1 으로 떠 있다" → Recovery + speed change 가 안 일어났다는 의미. 보통 LTSSM trace 에서 EQ phase 결과 또는 양 끝 capability mismatch 가 원인.

### 5.4 Equalization — Gen3+ 의 4 Phase

```
   Recovery → Recovery.Equalization → 4 phase
       │
       ├─ Phase 0:
       │     • Downstream Port (DP) 가 Upstream (UP) 에 preset 송신
       │     • 양 끝이 Phase 1 진입 합의
       │
       ├─ Phase 1:
       │     • DP 가 자기 Tx FFE preset 으로 송신
       │     • UP 의 Rx 가 받아서 BER 측정
       │     • UP 가 DP 의 Tx FFE coefficient 변경 요청 (어느 tap 을 키우거나 줄여라)
       │
       ├─ Phase 2:
       │     • DP 가 UP 의 Tx FFE 를 변경 요청
       │     • UP Tx → DP Rx 의 BER 최적화
       │
       └─ Phase 3:
             • 양 끝의 EQ 안정화 확인, 종료
             • Recovery → L0 (with new speed)
```

**Preset**: 11 가지 사전 정의 (P0..P10) 의 Tx FFE coefficient set. 양 끝의 시작점 결정.

**EQ 의 가치**: Channel 특성 (PCB trace + connector + cable) 이 다양해, 한 가지 EQ 로 모든 channel 커버 불가. 양 끝이 협상해 best EQ 결정.

### 5.5 Lane Reversal / Polarity Inversion / De-skew

```
   Lane Reversal
   ─────────────
   보드 라우팅상 lane 0..N 의 순서가 뒤집혀 연결됨
   → Polling 단계에서 자동 검출, internal 으로 매핑 reverse
   → SW 는 정상으로 봄

   Polarity Inversion
   ──────────────────
   Differential pair 의 + / - 가 뒤집힘
   → Receiver 가 자동으로 invert 처리

   Lane De-skew
   ────────────
   각 lane 의 도착 시간 차이 (PCB 길이 차)
   → SKP Ordered Set 으로 align
   → Tolerance 는 lane 간 ~ 1.5 ns
```

→ 이런 자동화 덕에 보드 라우팅이 유연해짐. 단, **PCB 의 length matching** 은 여전히 중요 (특히 Gen5+).

### 5.6 Lane Width Down-train

```
   양 끝이 x16 capable 이지만:
     - 일부 lane 의 EQ 실패 / electrical idle
     - 보드 손상 / connector pin issue

   → Configuration 단계에서 정상 lane 만으로 link 형성
   → x16 → x8 → x4 → x2 → x1 down-train 가능
   → 성능은 떨어지지만 link 는 유지
```

→ "왜 x16 이 x4 로 떨어졌나?" 라는 질문이 오면 LTSSM trace 에서 어느 lane 이 fail 인지 확인.

### 5.7 디버그 — Link up 안 됨

```
   LTSSM state 가 어디서 stuck?
       │
       ├─ Detect 에서 stuck
       │      → Receiver 가 detect 안 됨
       │      → 케이블/connector/board, Tx 가 켜졌는지
       │
       ├─ Polling 에서 stuck
       │      → TS1/TS2 송신 OK 인데 받기 실패
       │      → Polarity inversion / Lane reversal 자동검출 미동작
       │      → 또는 receiver 의 EQ 가 너무 부족 → BER 너무 높음
       │
       ├─ Configuration 에서 stuck
       │      → Link/Lane number 협상 실패
       │      → 한쪽이 다른쪽의 width capability 와 다른 값을 강제
       │
       ├─ Recovery 빈발
       │      → BER 임계 초과 — 채널 issue
       │      → EQ preset 이 channel 에 안 맞음
       │      → 온도 / 전원 노이즈
       │
       └─ L0 에 갔는데 Recovery 자주 빠짐
              → SerDes margin 낮음
              → SW 가 일부러 retrain (e.g. Gen 변경)
```

검증 도구:

- **Protocol analyzer** (LeCroy / Teledyne): packet level + LTSSM
- **PCIe debug card / interposer**: physical layer 모니터
- **Aurora ↔ JTAG → SerDes Eye scan**: PHY 직접 점검 (벤더 도구)

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Link 가 L0 에 가면 끝, 추가 EQ 는 동작 안 한다'"
    **실제**: Gen3+ 는 L0 진입 후에도 BER 모니터링 + 필요 시 Recovery → Equalization 재실행 가능. 또한 Gen 변경 (Gen3→Gen4 upgrade) 시에도 Recovery + EQ 재실행. **"L0 = 안정" 은 정적인 의미가 아님**.<br>
    **왜 헷갈리는가**: "트레이닝 끝" = "정상" 으로 단순 매핑하기 쉬움.

!!! danger "❓ 오해 2 — 'Recovery 발생 = link 가 망가진 것이다'"
    **실제**: Recovery 는 _기능_ 이다 — Gen up, EQ 재실행, ASPM L1 exit, Hot Reset 등 정상 시나리오의 공통 경로. _빈도_ 가 문제 — bring-up 시 한두 번은 정상, 운영 중 자주 빠지면 channel/EQ issue.<br>
    **왜 헷갈리는가**: "Recovery" 라는 단어의 부정적 어감.

!!! danger "❓ 오해 3 — 'Embedded clock 이라 reference clock 이 필요 없다'"
    **실제**: 100 MHz refclk 가 양 끝 PHY 에 공급되어야 정상 동작. Common Refclock vs Independent Refclock (SRIS — Separate Refclock Independent SSC) 모드 결정은 board design. SRIS 가 modern 옵션이지만 SerDes margin 더 빡빡.<br>
    **왜 헷갈리는가**: "embedded clock" 의 단어 의미.

!!! danger "❓ 오해 4 — 'PCIe link 는 spec 한 Gen 으로 떠 있다'"
    **실제**: 항상 Gen1 으로 시작 → Recovery 거쳐 합의된 최고 Gen 으로 올라감. Configuration Space 의 LnkSta 의 current speed 가 _실제_ 동작 속도 — capability 와 다를 수 있음.<br>
    **왜 헷갈리는가**: capability 만 보면 max speed 로 동작한다고 가정.

!!! danger "❓ 오해 5 — 'x16 connector = x16 link width'"
    **실제**: 일부 lane 의 EQ 실패 / electrical issue 로 down-train 발생 가능 (x16 → x8 → x4 → x2 → x1). 항상 LnkSta 의 current width 확인. Down-train 자체가 board/silicon issue 의 신호.

### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Link up 안 됨 — Detect 에서 stuck | Termination 안 켜짐 또는 board/cable | Tx pulse 송신 여부, board 전원 |
| Polling 에서 stuck | Bit Lock 또는 Symbol Lock 실패 | refclk, polarity inversion 자동 보정, EQ margin |
| Configuration 에서 stuck | Link/Lane # 협상 실패 | TS1/TS2 의 capability 광고, width 강제 설정 |
| L0 도달했는데 Gen 1 그대로 | Recovery + speed change 미발생 | LnkSta current speed, EQ Phase 결과 |
| L0 ↔ Recovery 빈번 왕복 | BER 임계 초과 (channel/EQ issue) | EQ preset, eye margin, 온도/전원 |
| x16 → x4 로 down-train | 일부 lane 의 EQ 실패 또는 보드 손상 | 각 lane 의 LTSSM status, eye scan |
| Gen 변경 후 link drop | speed change 시 EQ 부족 | LTSSM Recovery trace, EQ Phase 0..3 |
| Loopback mode 진입 안 됨 | LB 명령 전달 실패 또는 vendor-specific | TS1 Training Control bits |

---

## 7. 핵심 정리 (Key Takeaways)

- PHY = PCS + PMA + Analog + LTSSM. 각 sub-block 의 책임 분리.
- LTSSM 11 state — Detect/Polling/Configuration/L0 + L0s/L1/L2/Recovery/Disabled/Loopback/Hot Reset.
- Gen3+ 의 EQ 는 Recovery 안의 4 phase, 양 끝의 Tx FFE 를 Rx 가 요청.
- Lane reversal / polarity inversion / de-skew 는 자동, lane width down-train 도 자동.
- "Link 안 올라옴" 디버그는 LTSSM state stuck 위치 + EQ 결과부터.

!!! warning "실무 주의점"
    - Gen 변경 시 Recovery + EQ 재실행 — bring-up 시 Gen 강제 진입 시퀀스 검증 필수.
    - Common Refclock vs Independent Refclock 모드는 spec 에 양 옵션 존재 — board design 시 결정. SRIS (Separate Refclock Independent SSC) 가 modern 옵션.
    - Loopback mode 는 production silicon 의 PHY 검증 도구 — DV 시 LB 진입 시퀀스도 검증.
    - Gen6 PAM4 의 BER 은 Gen5 NRZ 보다 훨씬 높음 (보통 1e-6) — FEC 가 이를 1e-12 미만으로 보정. FEC 가 disabled 면 link 가 동작 안 함.
    - "x16 → x4 down-train" 의 발생 자체가 board 또는 silicon 문제의 신호 — 그냥 받아들이고 넘기지 말 것.

### 7.1 자가 점검

!!! question "🤔 Q1 — LTSSM stuck (Bloom: Analyze)"
    LTSSM 이 _Recovery → Recovery.Speed → Recovery.RcvrCfg → Recovery_ loop. 원인?

    ??? success "정답"
        EQ (Equalization) 실패:
        - **Tx FFE / Rx CTLE preset** 부적절.
        - **Channel insertion loss** spec 초과 (긴 trace 또는 connector 손실).
        - **Retimer EQ** 와 RC EQ 의 conflict.

        대응:
        - Eye diagram 측정 + EQ preset 재조정.
        - 또는 _lower Gen_ 으로 down-train 후 동작.

!!! question "🤔 Q2 — Common vs SRIS Refclock (Bloom: Evaluate)"
    카드 design. Common Refclock 가 _좋은데_ SRIS 를 _쓰는 이유_?

    ??? success "정답"
        Common Refclock 장점: SerDes clock recovery _간단_, EQ 쉬움.

        Common 단점: _refclk wire_ 가 _카드까지_ 가야 — _긴 trace_, _다중 카드_ 분배 어려움. _Hot-plug 카드_ 부적합 (카드 마다 다른 refclk source).

        SRIS: 각 카드가 _자체 refclk_. _Hot-plug + 다중 카드_ 친화적. 단 _CDR이 SSC compensate_ 가 더 복잡.

        Modern data center NIC: SRIS 일반화.

### 7.2 출처

**External**
- PCIe Specification — PHY chapter, LTSSM state diagram
- *PCIe Gen5/6 PHY Design* — Synopsys / Cadence WP

---

## 다음 모듈

→ [Module 06 — Configuration Space & Enumeration](06_config_enumeration.md): L0 도달 후 OS 가 device 를 발견하고 BAR 를 할당하는 표준 절차.

[퀴즈 풀어보기 →](quiz/05_phy_ltssm_quiz.md)

--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
