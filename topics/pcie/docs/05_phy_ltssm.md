# Module 05 — Physical Layer & LTSSM

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Diagram** PHY 의 sub-block (PCS / PMA / SerDes / Equalization) 과 신호 흐름을 그릴 수 있다.
    - **Trace** LTSSM 의 11 state 진입/탈출 트리거를 신호 (TS1/TS2, Electrical Idle) 와 함께 추적한다.
    - **Compare** Gen3+ 의 4-phase Equalization (Phase 0/1/2/3) 와 그 의도를 비교한다.
    - **Diagnose** "Link up 안 됨" 시나리오를 LTSSM state 별로 가능한 원인을 좁힌다.

!!! info "사전 지식"
    - Module 01 (lane / encoding 기본)
    - Module 02 (PHY 의 책임)

## 왜 이 모듈이 중요한가

**PCIe link bring-up 의 모든 진단은 LTSSM state 를 보는 데서 시작** 합니다. 그리고 Gen3+ 부터는 equalization 단계를 거쳐 link 가 안정화 — 잘못된 EQ preset 이나 channel 특성 misalignment 가 무수한 production failure 의 원인. PHY 와 LTSSM 을 모르면 "link recovery 빈발" 이라는 증상 앞에서 black box.

!!! tip "💡 이해를 위한 비유"
    **LTSSM** ≈ **공항의 항공기 관제 절차**

    - Detect = 활주로 도착
    - Polling = 관제와 무선 시범 통신
    - Configuration = 게이트 / lane / link width 협상
    - L0 = 정상 운항
    - Recovery = 난기류 — 잠시 회복
    - L1 / L2 = 주기 (저전력)
    - Disabled / Loopback / Hot Reset = 비상 / 테스트

## 핵심 개념

**Physical Layer 는 PCS (encoding/scrambling/framing) + PMA (SerDes) + analog driver/receiver + LTSSM. LTSSM 은 11 state 의 hierarchical state machine 으로 Detect → Polling → Configuration → L0 → (선택적) L0s/L1/L2/Recovery/Loopback/Disabled/Hot Reset 의 전이를 관리. Gen3+ 는 Recovery 안에 Equalization 4 phase 를 가지며, 양 끝의 Tx FFE coefficient 를 Rx 가 요청해 BER 최적화.**

!!! danger "❓ 흔한 오해"
    **오해**: "Link 가 L0 에 가면 끝, 추가 EQ 는 동작 안 한다."

    **실제**: Gen3+ 는 L0 진입 후에도 BER 모니터링 + 필요 시 Recovery → Equalization 재실행 가능. 또한 Gen 변경 (Gen3→Gen4 upgrade) 시에도 Recovery + EQ 재실행. **"L0 = 안정" 은 정적인 의미가 아님**.

    **왜 헷갈리는가**: "트레이닝 끝" = "정상" 으로 단순 매핑하기 쉬움.

---

## 1. Physical Layer Sub-block

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

### Equalization (Gen3+ 핵심)

| 단계 | 위치 | 역할 |
|------|------|------|
| **Tx FFE** (Feed Forward Equalizer) | Tx | Pre-cursor + main + Post-cursor 3-tap, channel ISI 미리 보상 |
| **Rx CTLE** (Continuous-Time Linear Equalizer) | Rx | Frequency-domain low-freq attenuation 보상 |
| **Rx DFE** (Decision Feedback Equalizer) | Rx | 이전 결정으로 ISI 제거, 가장 효과적 |
| **AGC** (Automatic Gain Control) | Rx | 신호 amplitude 정규화 |

→ Gen6 PAM4 는 EQ 가 더 복잡 (eye 가 3 개 → 마진 ↓), CTLE+DFE 마진이 핵심.

---

## 2. LTSSM — 11 States

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

### State 별 핵심 동작

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

---

## 3. Polling 상세

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

---

## 4. Equalization — Gen3+ 의 4 Phase

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

---

## 5. Lane Reversal / Polarity Inversion / De-skew

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

---

## 6. Lane Width Down-train

```
   양 끝이 x16 capable 이지만:
     - 일부 lane 의 EQ 실패 / electrical idle
     - 보드 손상 / connector pin issue

   → Configuration 단계에서 정상 lane 만으로 link 형성
   → x16 → x8 → x4 → x2 → x1 down-train 가능
   → 성능은 떨어지지만 link 는 유지
```

→ "왜 x16 이 x4 로 떨어졌나?" 라는 질문이 오면 LTSSM trace 에서 어느 lane 이 fail 인지 확인.

---

## 7. 디버그 — Link up 안 됨

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

## 핵심 정리 (Key Takeaways)

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

---

## 다음 모듈

→ [Module 06 — Configuration Space & Enumeration](06_config_enumeration.md)
