---
title: "Module 03 — Tesla FSD Case Study"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Recall** 2023–2026 Tesla FSD 탈옥 체인의 단계 (sniff / RE / inject / region 변조 / 지속 주입) 를 나열할 수 있다.
- **Explain** "SoC 에 SCS (보안 칩) 가 있어도 CAN 인증이 없으면 무력화" 되는 이유를 설명할 수 있다.
- **Decompose** 탈옥 체인의 각 단계를 ① 기술적 결함 ② 정책적 결함 ③ 아키텍처 결함으로 분해할 수 있다.
- **Justify** TARA 관점에서 same 사건이 SecOC + TEE 적용 OEM 에서 재현 가능한지 평가할 수 있다.
- **Apply** Threat-modeling 시 Tesla 사례의 5 단계를 자기 프로젝트의 ECU 에 적용할 수 있다.
:::
:::note[사전 지식]
- [Module 01](../01_can_bus_fundamentals/) (CAN 무인증, OBD-II 진입점, Bus-Off)
- [Module 02](../02_automotive_soc_security/) (HSM, SecOC, Gateway, TEE — _없을 때_ 무엇이 깨지는지 알려면 _있을 때_ 모습을 알아야)
- Bug bounty / responsible disclosure 일반 상식
- 차량 OTA 흐름 (서버 → 차량 → 인증 → 적용) 의 큰 그림
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _$10K 짜리 FSD 옵션_ 을 _$0_ 으로 해킹

2023 년 Berlin TU 의 연구팀이 **Tesla Model 3 의 FSD (Full Self-Driving) 옵션을 무료 활성화** 하는 방법을 발표했습니다.

Tesla 의 보안 스택은 업계 최고 수준이었습니다. L1 에서는 SCS (Secure Computing Stack — Tesla 자체 보안 칩/펌웨어 묶음) 와 Boot ROM 으로 신뢰 chain 을 완성했고, L5 에서는 **OTA**(Over-the-Air — 무선 원격 소프트웨어 업데이트) 인증, 코드 서명, 강한 **PKI**(Public Key Infrastructure — 공개키와 인증서로 신원·서명을 관리하는 체계) 를 갖췄습니다. 그러나 L2, 즉 CAN bus 위의 메시지 인증은 완전히 비어 있었습니다 — **SecOC**(Secure Onboard Communication — CAN 메시지에 인증 태그를 붙여 위조·재전송을 막는 통신 보안 계층) 가 미적용된 상태였습니다. 연구팀은 이 빈틈을 통해 OBD-II 로 차량에 진입한 뒤, CAN bus 에 임의의 프레임을 송신해 Region 을 US 로 변경하고 FSD feature flag 를 켰습니다. FSD SoC 는 보안 layer 통과 검증 없이 이 프레임을 수용해 **무료 FSD 활성화** 로 이어졌습니다. L1 과 L5 가 강해도 L2 가 비어 있으면 금고 옆에 누구나 앉을 수 있는 상황이 됩니다.

이론으로 배운 보안 메커니즘이 실제 어디에서 깨지는지 가장 빠르게 배우는 방법은 **공개된 케이스 스터디 분석** 입니다. Tesla FSD 사례는 _"비싼 보안 IP (SCS) 를 넣었는데도 한 줄 잘못된 가정 (CAN = 신뢰) 때문에 무력화"_ 된 대표 예시입니다.

Module 02 의 5-Layer 스택을 _Tesla 가 어디까지 가지고 있었고 어디가 비어 있었는지_ 로 정확히 매핑하면, 학습자는 **"동일 사건이 우리 ECU 에서 가능한가?"** 를 던지는 사고 패턴을 얻습니다. 이것이 **ISO 21434**(차량 사이버보안 엔지니어링 국제 표준) 의 **TARA**(Threat Analysis & Risk Assessment — 자산·위협·위험을 식별하고 등급을 매겨 대응을 정하는 활동) 그 자체이고, Module 04 의 attack surface (공격 표면 — 외부에서 침입할 수 있는 모든 진입점의 총합) 분석으로 직접 이어집니다.

:::tip[🤔 잠깐 — Tesla 가 _왜_ SecOC 안 적용했을까?]
Tesla 는 _보안에 적극적_ — Boot, Cloud 다 강함. 왜 CAN 만 약점이었을까?

<details>
<summary>정답</summary>

**레거시 + 성능 + 비용** trade-off 추정 (Tesla 비공개):

- **레거시**: 초기 Tesla 모델이 _전통 자동차 CAN_ 기반 설계 (2008-2012). 그 시절 SecOC 미보편.
- **Latency**: SecOC 의 MAC 계산 + 검증 = _100~300 µs_ 추가. 차량 _제어 critical_ 메시지에 부담.
- **CPU 부담**: 모든 ECU 가 _MAC 계산 + verify_ → SoC 부담 ↑.
- **호환성**: SecOC 적용 시 _기존 진단 도구_ 와 호환성 깨질 수 있음.

교훈: **보안 결정은 _historical reason_ 으로 종종 미적용**. 새 모델은 SecOC 적용 (Model Y/S 의 최신 firmware). 하지만 _레거시 모델_ 은 여전히 노출.

</details>
:::
---

## 2. Intuition — 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**Tesla FSD 탈옥** ≈ **금고는 강한데 문은 열려 있는 집**. SCS 가 boot / Cloud 인증은 _업계 최고_ 수준으로 보호했지만, CAN 통신은 미적용 — 외부에서 OBD-II 로 위조 GPS·Region·Feature 프레임을 주입하면 FSD SoC 가 그것을 정상 신호로 수용. 강한 금고가 있어도 문이 열려 있으면 도둑이 _금고 옆_ 까지 걸어 들어옵니다.
:::
### 한 장 그림 — Tesla 가 가진 것 vs 빠진 것

```d2
direction: down

HAS: "Tesla 가 가진 것 (강함)" {
  direction: down
  H1: "L5 Cloud 인증 · OTA signing"
  H2: "L5 Code-signing · Anti-Rollback"
  H3: "L1 SCS Secure Boot"
  H4: "L5 Telemetry 모니터링"
}
MISS: "비어 있는 layer" {
  direction: down
  M1: "✗ L2 SecOC"
  M2: "✗ L3 Secure Gateway"
  M3: "✗ L1 TEE"
  M4: "△ L4 IDS"
}
DONGLE: "탈옥 동글"
BUS: "CAN Bus" { shape: oval }
FSD: "FSD SoC\n위조 GPS/Region 수용\n→ 비승인 지역 자율주행"
HAS -> MISS { style.stroke-dash: 4 }
MISS -> DONGLE
DONGLE -> BUS: "OBD-II"
BUS -> FSD: "위조 GPS / Region"
```

### 왜 이 일이 발생했는가 — Architecture rationale (추론)

Tesla 의 설계 가정 (추론): Tesla 는 AUTOSAR 를 채택하지 않고 자체 SW 스택을 구축했습니다. 이는 뛰어난 실행력과 통합성을 가져다 주었지만, SecOC 가 AUTOSAR 에코시스템 안에 있다 보니 Tesla 는 자연스럽게 그 바깥에 위치하게 되었습니다. 또한 모든 ECU 를 자체 설계하는 중앙집중 아키텍처 덕분에 "내부 통신은 신뢰할 수 있다" 는 가정이 합리적으로 보였을 것입니다. 그리고 서버 측 보안이 강력하다면 — VIN 기반 인증, OTA 서명, 텔레메트리 모니터링 — 내부 통신의 약점을 충분히 보상할 수 있다고 판단했을 가능성이 높습니다(추론).

세 가정 모두 _합리적으로 보였지만_, OBD-II 라는 _법적 의무 진입점_ 앞에서 무너졌습니다. Module 02 의 표현을 빌리면 — "Secure Boot 의 BootROM 만 강력하고 OTP 가 비어 있는 구조" 와 같습니다.

---

## 3. 작은 예 — FSD 탈옥 1 주입 사이클 (CAN injection)

가장 단순한 한 사이클. €500 동글이 **OBD-II**(On-Board Diagnostics II — 법으로 의무화된 차량 진단 커넥터; 내부 CAN 에 직결) 로 연결되어 _GPS CAN 프레임 한 개_ 를 위조 주입하는 과정. 이 절에 나오는 동작 용어를 먼저 풀면 — **sniff/sniffing**(스니핑 — 버스에 흐르는 메시지를 가만히 엿들어 수집), **RE/reverse engineering**(역공학 — 정해진 규격 없이 관측만으로 데이터의 의미·구조를 알아내는 것), **DBC**(CAN Database — 각 메시지 ID 의 발신자·신호 배치를 정의한 설정 파일), **geofence**(지오펜스 — GPS 위치가 허용 구역 안인지 판정하는 가상 울타리) 입니다.

```d2
shape: sequence_diagram

OBD: "OBD-II Port\n(Pin 6 CAN-H · Pin 14 CAN-L · Pin 16 +12V)"
DON: "탈옥 동글\n(MCU + MCP2515, €500~€2,000)"
BUS: "CAN Bus"
FSD: "FSD SoC (HW3/HW4)"

# Note over BUS: ⑥ 두 ID=0x318 frame 공존
OBD -> DON: "+12V 공급, CAN-H/L 연결"
BUS -> DON: "① CAN sniff"
DON -> DON: "② 정상 GPS frame 식별\nID=0x318 [37.5665, 126.9780] Seoul"
DON -> DON: "③ Frame RE (DBC 매핑 추정)\nbyte 0..3=lat, byte 4..7=lon"
DON -> DON: "④ 위조 frame 생성\nID=0x318 [37.3861, -122.0839] CA US"
DON -> BUS: "⑤ 50 ms 주기로 위조 송신\n(정상 100 ms 보다 고빈도)"
BUS -> FSD: "⑦ frame 수신\n(MAC/FV 검증 없음)"
FSD -> FSD: "⑧ GPS state ← 위조 frame (CA 좌표)"
FSD -> FSD: "⑨ geofence_check(CA)\n→ '승인 지역' → FSD 활성화"
FSD -> FSD: "⑩ 비승인 지역에서\n자율주행 동작 시작"
```

| Step | 누가 | 무엇을 | 의미 |
|---|---|---|---|
| ① | 동글 | OBD-II 에 꽂아 +12V 로 동작, 모든 CAN frame sniff | _물리 접근 1 회_ 만 필요 |
| ② | 동글 | GPS 좌표를 운반하는 ID 식별 | DBC 가 reverse 됐거나 패턴 분석으로 추정 |
| ③ | 동글 | byte 매핑 분석 | DBC 의 일부 정보가 OEM 수리 매뉴얼에서 누출된 사례 있음 |
| ④ | 동글 | 위조 frame 생성 (CRC 만 정상 계산) | _MAC 가 없으니 추가 검증 없음_ |
| ⑤ | 동글 | 정상보다 높은 빈도로 송신 | 마지막 수신값을 덮어쓰기 위함 |
| ⑥ | CAN Bus | 두 ID 0x318 frame 공존 | CAN 은 ID 충돌 시 비파괴 중재만 — _발신자 검증 없음_ |
| ⑦ | FSD SoC | CAN driver 가 frame 수신 | SecOC 미적용이므로 무조건 통과 |
| ⑧ | FSD SoC | GPS state 갱신 | 마지막 수신값으로 덮어쓰기 |
| ⑨ | FSD SoC | geofence_check | 위조 좌표 (CA) 통과 |
| ⑩ | FSD | 비승인 지역에서 자율주행 동작 | 비즈니스 모델 자체가 무너지는 결과 |

```c
// Step ⑧ 의 추정 pseudo code (FSD CAN handler — SecOC 미적용 가정)
void can_rx_handler(can_frame_t *f) {
    if (f->id == 0x318) {       // GPS frame
        // !!! MAC 검증 없음, FV 검증 없음
        gps_state.lat = decode_f32(f->data + 0);
        gps_state.lon = decode_f32(f->data + 4);
        gps_state.last_update_ms = now_ms();
    }
    // ... 다른 ID 처리
}

// SecOC 가 있었다면 추가됐을 코드 (Module 02 의 §5.5)
void can_rx_handler_secoc(can_frame_t *f) {
    if (f->id == 0x318) {
        secoc_pdu_t *pdu = (secoc_pdu_t *)f->data;
        if (!secoc_verify_freshness(0x318, pdu->fv))
            return;  // replay 차단
        if (!hsm_cmac_verify(K_SECOC_GPS, pdu->data, 8,
                             pdu->fv, pdu->mac, 4))
            return;  // ★ 여기서 위조 frame 폐기
        gps_state.lat = decode_f32(pdu->data + 0);
        gps_state.lon = decode_f32(pdu->data + 4);
    }
}
```

:::note[여기서 잡아야 할 두 가지]
**(1) 단 한 줄 — `hsm_cmac_verify` — 가 빠져서 10 만 대 fleet 이 탈옥됐다.** 이것이 "L2 SecOC 가 비어 있을 때" 의 정확한 비용. <br>
**(2) GPS 가 _CAN 을 경유_ 한다는 것 자체가 아키텍처 결함.** GPS 수신기가 SoC 에 직결되거나 **TEE**(Trusted Execution Environment — CPU 안에 하드웨어로 격리된 보안 실행 영역) 안에서 multi-source fusion (여러 센서 값을 합쳐 신뢰도를 높이는 것) 됐다면, CAN injection 으로 위조 불가.
:::
---

## 4. 일반화 — 3 약점 교집합 과 Root Cause Tree

### 4.1 세 약점이 _동시에_ 존재해야 탈옥이 성립

```d2
direction: down

W1: "CAN 무인증\n(Module 01)"
W2: "GPS 단일 의존\n(TEE 미적용)"
W3: "로컬 캐시 의존\n(오프라인 시 서버 검증 우회)"
JB: "Tesla FSD 탈옥 성립\n(세 약점의 교집합)"
W1 -> JB
W2 -> JB
W3 -> JB
```

세 약점 중 _어느 하나라도_ 방어됐다면 공격 난이도는 _차원이 다른 수준_ 으로 상승했을 것입니다.

| 약점 | 대응 방어 (Module 02 layer) |
|---|---|
| ❶ CAN 무인증 (GPS frame 위조 가능) | **L2 SecOC** — HSM (Hardware Security Module — 키를 칩 내부에 봉인하는 보안 모듈) 키로 MAC (Message Authentication Code — 키로 계산한 위조 방지 검증값) + FV (Freshness Value — 재전송을 막는 증가 카운터) |
| ❷ GPS 단일 소스 의존 | **L1 TEE** — Secure World 에서 GPS + IMU (Inertial Measurement Unit — 가속도·각속도로 움직임을 측정하는 관성 센서) + WheelSpeed + CellTower 융합 |
| ❸ 로컬 캐시 의존 (오프라인 우회) | **L5 Cloud + Heartbeat** — 주기 검증 실패 시 기능 비활성화 |

### 4.2 Root Cause Tree

```d2
direction: right

TOP: "FSD 가 비승인\n지역에서 동작"
GPS: "GPS 좌표 위조됨"
REG: "Region Code 변조됨"
SRV: "서버 검증 우회됨"
RC1A: "RC ❶ SecOC 부재\nCAN frame MAC 없음"
RC1B: "RC ❷ TEE 부재\nGPS 가 CAN 경유"
RC2: "설정 frame 인증 없음\n(❶ 와 동일)"
RC3A: "RC ❸ Heartbeat 부재\n오프라인 시 로컬 캐시"
RC3B: "텔레메트리 주기적\n→ 실시간 아님"

TOP -> GPS
TOP -> REG
TOP -> SRV
GPS -> RC1A
GPS -> RC1B
REG -> RC2
SRV -> RC3A
SRV -> RC3B
```

### 4.3 같은 사건이 _다른 OEM_ 에서 가능한가? — TARA

| Layer | Tesla | BMW/Mercedes (최신) | 현대/기아 (최신) |
|---|---|---|---|
| **CAN 인증 (L2)** | ❌ | ✅ SecOC (부분) | ✅ SecOC (신차) |
| **Gateway (L3)** | △ Flat | ✅ Central GW | ✅ ccGW |
| **HSM (L1)** | SCS (Boot) | EVITA Full | SHE → HSE 전환 중 |
| **OBD 격리 (L3)** | ❌ | ✅ | ✅ |
| **IDS (L4)** | Telemetry | ✅ 차량 내 IDS | ✅ |
| **OTA 보안 (L5)** | ✅ 업계 최고 | ✅ | ✅ |

**아이러니**: Tesla 는 OTA / 클라우드 보안에서 업계 선도. _차량 내부 통신 보안_ 에서는 전통 OEM 보다 뒤처짐.

---

## 5. 디테일 — 타임라인, 역사적 사례, HW 아키텍처, Tesla 대응

### 5.1 사건 타임라인

| 시기 | 사건 |
|---|---|
| **2019.04** | HW3 (FSD Computer 1) 양산 — SCS 로 Secure Boot 적용, CAN 인증 미적용 |
| **2020** | HW3 MCU 탈옥 (보안 연구자) — voltage glitching 으로 Secure Boot 우회 |
| **2023** | HW4 (FSD Computer 2) 양산 — 7 nm, 여전히 CAN 인증 미적용 |
| **2024.H1** | Pwn2Own Automotive 2024 — Tesla 인포테인먼트 다수 취약점 |
| **2024.H2** | FSD 탈옥 동글 첫 등장 — 동유럽 / 중국 지하 시장 |
| **2025.Q1** | 탈옥 규모 확대 — 온라인 판매 증가, 비승인 지역 중심 |
| **2025.Q2** | Tesla 텔레메트리로 대규모 탐지 — GPS vs Cell Tower 불일치 패턴 |
| **2025.H2** | Pwn2Own Automotive 2025 — FSD SoC 추가 취약점, Fault Injection 시연 |
| **2026.Q1** | Tesla 원격 비활성화 — 10 만+ 대 동시 FSD 차단, VIN 블랙리스트 |
| **2026.Q1** | 각국 규제 대응 — 한국 자동차관리법 집행 강화 (2 년 징역 / 2 천만 원) |
| **2026.Q2** | 업계 파급 — SecOC 의무화 논의 가속, ISO 21434 구현 가이드라인 강화 |

**핵심 교훈**: SCS (Secure Boot + Cloud Auth) 는 2019 년부터 있었지만, _CAN 통신 인증_ 을 적용하지 않은 아키텍처 판단이 5 년 후 10 만 대 규모 보안 사고로 이어짐.

### 5.2 역사적 차량 해킹 사례 — FSD 탈옥과 비교

#### Jeep Cherokee 원격 해킹 (2015)

```d2
direction: down

NET: "인터넷"
UC: "Uconnect 인포테인먼트\n(Sprint 3G)"
DBUS: "D-Bus 내부 통신"
GW: "V850 CAN\n게이트웨이 ECU"
BUS: "CAN Bus" { shape: oval }
CTRL: "조향 · 브레이크 · 가속 제어"
NET -> UC: "Cellular"
UC -> DBUS: "OS 취약점으로 RCE"
DBUS -> GW
GW -> BUS: "FW 리플래시 (인증 없음)"
BUS -> CTRL
```

위 그림의 **RCE**(Remote Code Execution — 공격자가 원격에서 임의 코드를 실행시키는 가장 위험한 취약점) 가 인포테인먼트 OS 에서 일어나, 거기서 게이트웨이를 거쳐 CAN 으로 번진 것이 Jeep 사례의 핵심 경로입니다.

| 항목 | Jeep Cherokee (2015) | Tesla FSD (2025–26) |
|---|---|---|
| **진입점** | Cellular (원격, 물리 접근 불필요) | OBD-II (물리 접근 필요) |
| **핵심 취약점** | 게이트웨이 FW 리플래시 무인증 | CAN 메시지 무인증 |
| **영향** | 조향/브레이크 물리 제어 → **안전 위협** | 기능 잠금 우회 → **매출 손실** |
| **규모** | 140 만 대 리콜 | 10 만+ 대 원격 비활성화 |
| **근본 원인** | 도메인 미격리 + FW 서명 없음 | CAN 인증 없음 + GPS 단일 의존 |
| **산업 영향** | 차량 보안 연구 폭발적 증가 | SecOC 의무화 논의 가속 |

#### BMW ConnectedDrive (2015)

**공격** (ADAC, 독일자동차클럽 발견): BMW 의 ConnectedDrive 서비스는 차량과 서버 사이에 HTTP 비암호화 통신을 사용하고 있었습니다. ADAC 연구팀은 MITM(중간자 공격)으로 이 트래픽을 가로채 도어 잠금 해제 명령을 위조하는 데 성공했고, 220만 대가 영향을 받았습니다. 차량-서버 간 통신에도 TLS 가 필수임을 업계 전체에 각인시킨 사건입니다.

이 사례를 Tesla FSD 와 비교하면 흥미로운 대조가 나타납니다. Tesla 는 서버 통신에 TLS와 강력한 서명을 적용해 BMW 의 약점을 미리 보완했습니다. 그러나 역설적으로 차량 내부 CAN 통신은 BMW 보다 더 취약한 상태였습니다.

#### Tesla Model S Key Fob 클론 (2018)

**공격** (KU Leuven 연구팀):

- Tesla Model S 키폭이 DST40 암호화 사용 (40-bit, 취약)
- Proximity Reader ($600) + Raspberry Pi 로 키폭 신호 캡처
- 1.6 초 만에 키 복제 → 차량 탈취

**교훈**:

- 약한 암호 알고리즘 (DST40) 은 시간이 지나면 반드시 깨짐
- Tesla 대응: AES-128 키폭 교체 + PIN to Drive

→ FSD 비교: SCS 의 AES 는 강력하지만, CAN 통신에 미적용.

#### 사례들의 공통 패턴

세 사례를 나란히 놓고 보면 **반복되는 3 패턴** 이 뚜렷하게 드러납니다.

첫째는 **"여기는 안전" 가정의 붕괴**입니다. CAN 버스는 "물리적으로 폐쇄된 네트워크" 라는 가정 위에서 설계되었고, Jeep 은 "인포테인먼트는 파워트레인과 격리된다" 고 가정했으며, Tesla FSD 는 "서버 인증이 충분하다면 내부 통신은 신뢰해도 된다" 고 가정했습니다. 세 가정 모두 어느 시점에 외부 연결이나 법적 의무 포트(OBD-II) 로 인해 깨졌습니다.

둘째는 **가장 약한 고리에서 깨진다**는 것입니다. Jeep 은 수백 개의 보안 설계 결정 중 게이트웨이 FW 서명 하나가 없었고, BMW 는 HTTP 하나가 HTTPS 여야 했으며, Tesla FSD 는 CAN 메시지에 MAC 한 줄이 빠져 있었습니다. 나머지가 아무리 강해도 이 하나로 전부 무너졌습니다.

셋째는 **사후 대응 비용이 사전 설계 비용을 압도**한다는 것입니다. Jeep 의 140만 대 리콜 비용은 게이트웨이 서명 기능을 처음부터 넣었을 비용과 비교할 수 없고, Tesla 의 연간 $118M+ 매출 손실은 차당 $10~30 의 SecOC 도입 비용과 비교되지 않습니다. 보안은 설계 단계에서 가장 저렴합니다.

### 5.3 Tesla FSD 하드웨어 아키텍처

#### HW3 (FSD Computer 1, 2019~)

```d2
direction: down

HW3: "FSD Computer 1 (HW3)" {
  direction: down
  CHIPA: "FSD Chip A (Turbo A)" {
    grid-rows: 5
    A1: "ARM Cortex-A72 x12"
    A2: "NPU x2"
    A3: "GPU (Mali) · ISP"
    ASCS: "SCS"
    ASMS: "SMS"
  }
  CHIPB: "FSD Chip B (Turbo B)" {
    B1: "동일 구성\nDual Redundancy\nA/B 독립 연산·비교\n불일치 시 경고"
  }
}
SENS: "Camera x8\nRadar · Ultrasonic"
VEH: "Vehicle CAN Bus\nGPS Module · IMU"
HW3 -> SENS: "PCIe"
HW3 -> VEH: "CAN"
```

위 칩 구성에서 **NPU**(Neural Processing Unit — 신경망 추론을 가속하는 전용 연산기) 가 카메라 영상으로 자율주행 인식을 돌리고, **ISP**(Image Signal Processor — 카메라 원신호를 보정·가공하는 회로) 가 그 전처리를 맡습니다.

- **SCS** (Security Subsystem) — Secure Boot (BL 서명 검증), FMP Key (Firmware Protection), Weight Encryption Key (모델 보호), Board Credentials (Cloud 인증)
- **SMS** (Safety Management System) — Watchdog, ECC (Error-Correcting Code — 메모리 비트 오류를 검출·정정하는 코드), 오류 복구

#### HW3 vs HW4 비교

| 항목 | HW3 | HW4 |
|---|---|---|
| 공정 | Samsung 14 nm | Samsung 7 nm |
| NPU | 2 개 (칩당 1) | 2 개 (성능 3–5×) |
| 카메라 입력 | 8 대 (1.2 MP) | 최대 11 대 (5 MP) |
| Ethernet | 미지원 | 지원 (고속 카메라) |
| 보안 | SCS (Secure Boot + Cloud Auth) | SCS 강화 + Anti-Tamper |
| **CAN 인증** | **❌ 미적용** | **❌ 여전히 미적용** |

### 5.4 FSD 기능 활성화 메커니즘 — 정상 vs 공격 지점

#### 정상 활성화 흐름

```d2
direction: right

SRV: "Tesla 서버" {
  S1: "VIN 확인"
  S2: "구독 / 구매 상태"
  S3: "지역 승인"
  S4: "규제 버전 매칭"
  PROF: "Configuration Profile\n· 암호학적 서명 (VIN bind)\n· FSD Enable / Disable\n· Region Lock\n· SW Version"
}
CAR: "차량 FSD SoC" {
  LOCAL: "로컬 Configuration\n· Feature Flags\n· Region Code\n· GPS Geofence\n· 서버 프로파일 캐시"
}
PROF -> LOCAL
```

#### 취약점 발생 지점

```d2
direction: down

SRV: "서버 검증 OK"
PROF: "Configuration Profile\n(서명 검증 후 로컬 캐시)"
FF: "Feature Flag\n(로컬 저장)"
GF: "Geofence\n(GPS 기반 판단)"
GPS: "GPS Module"
BUS: "CAN Bus" { shape: oval }
DONGLE: "탈옥 동글\n위조 GPS / Region 주입"
FSD: "FSD Software Stack\n'미국에 있고 FSD 활성화됨'\n→ 동작 시작"
SRV -> PROF
PROF -> FF
PROF -> GF
GF -> GPS
GF -> BUS
DONGLE -> BUS: "공격 지점"
FF -> FSD
GPS -> FSD
BUS -> FSD
```

### 5.5 탈옥 기법 상세 — 5 단계

**Step 1 — CAN Bus sniffing**

동글을 OBD-II 에 연결하면 CAN 버스의 모든 프레임이 보입니다. 공격자는 정상 동작 시 GPS 좌표를 운반하는 Arbitration ID 를 식별하기 위해 먼저 수동 청취(passive sniffing) 를 수행합니다. 차량이 이동할 때 좌표값이 바뀌는 ID 를 찾으면, 그것이 GPS 프레임입니다. Region Code 를 운반하는 ID 도 같은 방식으로 식별합니다.

**Step 2 — Frame 역공학**

ID 를 찾았으면 Data 필드의 바이트 배치를 분석합니다. GPS 좌표는 보통 IEEE 754 단정밀도 부동소수점 4바이트 두 개(위도·경도)로 인코딩되므로, 알려진 위치에서 캡처한 값과 대조해 바이트 매핑을 확정합니다. DBC 파일이 온라인에 부분적으로 유출된 경우도 있어 이 단계를 수분 안에 끝낼 수 있다고 보고된 바 있습니다.

**Step 3 — 위조 frame 주입**

```d2
direction: down

ORIG: "원본 GPS frame (실제 위치: Seoul)\nID: 0x318  Data: [37.5665, 126.9780]"
FAKE: "위조 GPS frame (가짜 위치: California)\nID: 0x318  Data: [37.3861, -122.0839]"
ORIG -> FAKE: "동글이 차단/대체"
```

바이트 매핑이 확정되면 동글이 California 좌표를 인코딩한 위조 프레임을 생성하고, 정상 프레임과 동일한 ID 로 버스에 주입합니다. MAC 이 없으니 수신 ECU 는 위조 여부를 알 방법이 없습니다.

**Step 4 — Region Code 변조**

GPS 좌표 위조만으로는 부족한 경우가 있습니다. FSD SoC 가 Region Code 를 별도로 확인해 "이 차량이 FSD 승인 시장인가?" 를 체크하기 때문입니다. 동글은 Region Code 프레임도 찾아내 US 코드를 담은 위조 프레임을 함께 주입합니다. 이렇게 FSD SW 가 "미국에 있는 차량" 으로 인식하게 만듭니다.

**Step 5 — 지속 주입**

한 번 주입하는 것으로는 부족합니다. 실제 GPS ECU 도 자신의 좌표 프레임을 계속 전송하기 때문에, FSD SoC 가 마지막으로 받은 값을 사용한다는 점을 이용해 동글은 정상 GPS ECU 보다 높은 빈도로 위조 프레임을 송신합니다. 그 결과 FSD SoC 는 항상 위조 값을 최신 값으로 채택하게 됩니다.

### 5.6 Tesla 의 사후 대응 (2026 Q1)

| 대응 | 방법 | 효과 | 한계 |
|---|---|---|---|
| **원격 비활성화** | OTA 로 FSD 차단 | 즉각, 10 만+ 대 동시 처리 | _사후 대응_ — 이미 수개월 운행 |
| **텔레메트리 탐지** | GPS 궤적 vs 셀 타워 / IP 위치 불일치 | 높은 탐지율 | 인터넷 미연결 시 탐지 지연 |
| **영구 FSD 차단** | VIN 블랙리스트, 보증 거부 | 강력한 억제 | 합법 중고차 구매자 피해 가능 |
| **법적 대응** | 각국 규제 협력 | 판매자 처벌 | 오픈소스 도구 근절 어려움 |

### 5.7 "했어야 했던 것" vs "한 것"

| 방어 수단 | Tesla 가 한 것 | 했어야 한 것 |
|---|---|---|
| **Secure Boot** | ✅ SCS 로 FW 서명 검증 | ✅ (이미 적용) |
| **Cloud Auth** | ✅ VIN 기반 서버 검증 | ✅ (이미 적용) |
| **CAN 메시지 인증 (L2)** | ❌ 미적용 | ✅ SecOC + HSM |
| **도메인 격리 (L3)** | ❌ Flat CAN | ✅ Secure Gateway |
| **GPS 무결성 (TEE)** | ❌ CAN 경유 GPS 신뢰 | ✅ TEE 다중 소스 검증 |
| **OBD-II 격리** | ❌ 전체 CAN 접근 | ✅ 진단 도메인 분리 |
| **IDS** | △ 텔레메트리 기반 | ✅ 실시간 CAN IDS |

### 5.8 비용 분석 — SecOC 도입 vs 탈옥 피해

| 항목 | 추정 비용 |
|---|---|
| HSM 탑재 ECU 추가 비용 | $1–5 / ECU (대량 생산) |
| SecOC 펌웨어 개발 | 일회성 엔지니어링 비용 |
| 키 관리 인프라 | 서버 인프라 + PKI |
| **합계 (차량당)** | **$10–30 추정** |
| | |
| FSD 탈옥 피해 (10 만 대) | $99/월 × 12 개월 × 100,000 = **$118 M+/년 매출 손실** |
| 브랜드 / 규제 리스크 | 정량화 불가 — 자율주행 신뢰도 훼손 |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'Tesla 는 보안에 신경 안 썼다']
**실제**: Tesla 의 _서버 보안 / boot 보안 / OTA 서명_ 은 업계 최고 수준입니다. 문제는 _"내부 CAN = 신뢰"_ 라는 _아키텍처 가정의 실패_. **의도 부재가 아니라 가정 오류** 입니다. <br>
**왜 헷갈리는가**: 결과 (탈옥 발생) 만 보고 "처음부터 보안 무시" 로 단순화. 실제는 design assumption 의 잘못.
:::
:::danger[❓ 오해 2 — 'SCS 가 있으면 CAN 도 자동으로 안전']
**실제**: SCS 는 _Secure Boot + Cloud Auth_ 만 적용된 보안 IP 입니다. 같은 하드웨어가 SecOC 도 할 수 있지만 _Tesla 는 CAN 통신에 적용하지 않음_. 즉 **HW 가 있는 것 ≠ 사용된 것**. <br>
**왜 헷갈리는가**: "SCS 라는 보안 칩이 있다 = 모든 보안 OK" 의 단순화.
:::
:::danger[❓ 오해 3 — 'GPS spoofing 은 RF 위조가 본질']
**실제**: Tesla FSD 탈옥은 _RF GPS spoofing_ 이 아니라 _CAN 내부 frame 위조_ 입니다. GPS 수신기와 SoC 사이에 CAN 이 끼어 있고, 그 CAN 이 무인증이라 _수신기 출력을 동글이 대체_. 즉 GPS 안테나는 정상, 신호 위조는 _차량 내부에서_ 발생. <br>
**왜 헷갈리는가**: "GPS spoofing" 이라는 용어가 RF 공격을 자연스럽게 떠올림.
:::
:::danger[❓ 오해 4 — 'Feature Flag 는 보안 기능이다']
**실제**: Feature Flag 는 _UX 편의_ 목적의 정책 변수입니다. 서명 검증이나 HSM 봉인 없이 평문 NVM 에 저장되는 경우가 많고, _공격자가 변조 가능_. **정책 ≠ 보안 경계**. <br>
**왜 헷갈리는가**: "FSD 비활성화 = 안전" 라는 결과 중심 사고.
:::
:::danger[❓ 오해 5 — 'Telemetry 만 있으면 IDS 역할 충분']
**실제**: Telemetry 는 _서버 측 사후 분석_ 에 가깝습니다. 차량 내부의 _실시간 CAN IDS_ 와는 다릅니다 — 인터넷 미연결 / 산악 지역 / 지하 주차장에서는 Telemetry 가 끊기고, 그 동안 공격이 진행 중입니다. <br>
**왜 헷갈리는가**: "데이터 수집 = 모니터링 = IDS" 의 단순화.
:::
### DV 디버그 체크리스트 (Tesla 사례를 자기 ECU 에 매핑할 때)

| 증상 / 자가진단 질문 | 1차 의심 | 어디 보나 |
|---|---|---|
| 외부 동글이 OBD-II 로 GPS frame 을 위조 주입 가능한가? | L2 SecOC 부재 | DBC 의 GPS ID 가 SecOC 적용 목록에 있나, RX side 의 MAC verify call |
| GPS 좌표 한 ID 로 단일 의존하는가? | L1 TEE 부재 | sensor fusion 코드가 Normal World 인지, multi-source plausibility 체크 유무 |
| 오프라인 시 로컬 캐시로 기능이 동작하는가? | L5 Heartbeat 부재 | "마지막 서버 검증 후 N 시간 경과" 시 fallback 정책 |
| Region / Feature Flag 가 평문 NVM 에 저장되는가? | L1 Secure Boot Measurement 미포함 | NVM dump → 서명 검증 영역 vs 실제 저장 영역 |
| 진단 ID (0x7DF, 0x7E0..0x7EF) 가 모든 도메인에 도달하는가? | L3 OBD 격리 부재 | Gateway routing table |
| 동일 ID 가 _두 source_ 에서 송신 시 어떻게 처리하는가? | spoofing 탐지 부재 | RX handler 의 source 검증 (불가능 — SecOC 가 답) |
| 실시간 CAN IDS 가 있는가? | L4 IDS 부재 (Tesla 의 정확한 패턴) | 차량 내 IDS 컴포넌트 존재 여부, telemetry 와 분리 |
| Feature 활성화 결정이 로컬 플래그만으로 일어나는가? | L5 Heartbeat 부재 | 활성화 코드 경로 trace, 서버 재검증 빈도 |

이 8 개 질문에 _하나라도_ "예" 가 있으면 Tesla 사례의 일부 재현 가능성이 있는 ECU 입니다.

---

## 7. 핵심 정리 (Key Takeaways)

- **외부 방어 ≠ 내부 방어** — Secure Boot 로 부팅 체인을 지켜도 CAN 인증이 없으면 OBD-II 한 번에 무력.
- **3 약점 교집합** — CAN 무인증 ❶ + GPS 단일 의존 ❷ + 로컬 캐시 ❸. 셋 중 하나만 깨도 공격 난이도 차원이 다름.
- **Feature Flag = 정책일 뿐 보안 경계가 아님** — 서명·봉인 없는 플래그를 신뢰하면 차량이 곧 정책 결정자가 됨.
- **자체 SW 스택의 함정** — AUTOSAR / SecOC 에코시스템 밖이면 같은 기능을 자체 구현해야 하며, 누락 위험 큼.
- **케이스 스터디 = TARA 의 출발점** — 공개된 익스플로잇 체인은 자체 ECU 가정을 검증하는 가장 빠른 도구.
- **비용 비대칭** — SecOC $10–30/대 ≪ FSD 탈옥 $118 M+/년 매출 손실.

:::caution[실무 주의점 — Feature Flag 로 보안 기능을 제어하면 안 된다]
**현상**: FSD 활성화 여부를 차량 로컬 플래그로 판단하면, 공격자가 해당 플래그 값을 변조해 구매하지 않은 기능을 무료로 활성화하거나, 반대로 인가되지 않은 자율 주행 모드를 강제 진입시킬 수 있다.

**원인**: Feature Flag 는 UX 편의 목적으로 설계되었으며, 서명 검증이나 HSM 봉인 없이 플래시 메모리에 평문 저장되는 경우가 많다.

**점검 포인트**: Feature 활성 여부를 결정하는 NVM 주소를 특정하고, 해당 값이 Secure Boot 검증 범위 (Measurement) 안에 포함되는지 확인. 외부 서버 재검증 없이 로컬 플래그만으로 안전 기능이 전환되는 코드 경로가 있으면 즉시 수정 대상.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — Tesla 의 5 layer 분석 (Bloom: Analyze)]
Tesla 가 _L1 Boot 강함_, _L5 Cloud 강함_. 그런데 _L2 Communication 약함_. 왜?

<details>
<summary>정답</summary>

가능한 원인 (Tesla 비공개):
- **레거시 design**: 2008-2012 model 의 CAN bus 기반, SecOC 미보편 시절.
- **Latency 비용**: SecOC MAC 검증이 _100~300 µs_ 추가, 일부 control 경로에 부담.
- **호환성**: 외부 diagnostic tool 과 호환.

교훈: _historical 결정_ 이 _현재 보안 hole_ 로 남음. 새 design 에 _retrofit_ 어려움.

</details>
:::
:::tip[🤔 Q2 — Feature flag 검증 (Bloom: Apply)]
FSD feature flag 를 _NVM_ 에 저장. 어떻게 _spoofing 방어_?

<details>
<summary>정답</summary>

- **서명 + HSM 봉인**: NVM flag 가 _서명_ 되고, HSM 이 _verify_. Random NVM write 무효.
- **Server 재검증**: 차량이 _주기적_ Tesla server 에 _feature 인증_ 재검증.
- **Secure boot measurement**: NVM flag 가 _boot measurement_ 에 포함 → 변경 시 boot fail.

세 가지 모두 적용 = defense in depth.

</details>
:::
:::tip[🤔 Q3 — 비용 비대칭 추정 (Bloom: Evaluate)]
SecOC retrofit _$10-30/대_, FSD 탈옥 _$118M+/년 매출 손실_. 왜 _즉시 retrofit_ 안 함?

<details>
<summary>정답</summary>

- **레거시 차량 retrofit 불가**: 출시된 차량은 _firmware update_ 만, hardware 한계.
- **인증 / regulation**: 차량 보안 변경은 _ISO 26262 인증_ 재취득 필요 — 비용/시간 큼.
- **신모델 적용**: 신차에 적용 _현재 진행 중_.
- **위험 평가**: 일부 OEM 은 _ROI 계산_ — 탈옥 빈도 vs retrofit 비용.

교훈: _보안 retrofit_ 은 _design 시점_ 보다 _수십 배 비쌈_.

</details>
:::
### 7.2 출처

**External**
- 학술 / industry 발표: FSD jailbreak research (2023)
- Berlin TU 차량 보안 연구 그룹
- Tesla cybersecurity disclosure (limited public)

---

## 다음 모듈

→ [Module 04 — Attack Surface & Defense](../04_attack_surface_and_defense/): Tesla 사례를 일반화 — 차량의 _전체 attack surface_ (물리 / 무선 / 공급망) 와 각 layer 에 매핑된 방어 계층.

[퀴즈 풀어보기 →](../quiz/03_tesla_fsd_case_study_quiz/)

