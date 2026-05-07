# Module 01 — CAN Bus Fundamentals

<div class="learning-meta">
  <span class="meta-badge meta-level-intermediate">📊 Intermediate</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Diagram** CAN bus topology와 메시지 frame 구조 (ID, DLC, data, CRC)
    - **Identify** CAN의 보안 한계 (no auth, broadcast, no encryption)
    - **Distinguish** CAN 2.0, CAN-FD, CAN-XL의 차이
    - **Apply** SecOC (Secure Onboard Communication)으로 인증 추가

!!! info "사전 지식"
    - 직렬 통신 기본
    - 자동차 ECU / 네트워크 일반

## 핵심 개념
**CAN Bus = 1980년대 설계된 브로드캐스트 직렬 버스 — 인증/암호화 없이 모든 노드가 모든 메시지를 읽고 쓸 수 있다.**

"자동차 보안의 대부분의 문제는 CAN이 '신뢰할 수 있는 폐쇄 네트워크'라는 가정에서 시작된다. OBD-II 포트가 그 가정을 깨뜨린다."

---

## CAN Bus 탄생 배경

| 항목 | 내용 |
|------|------|
| **설계 시기** | 1983년 (Robert Bosch GmbH) |
| **표준화** | ISO 11898 (1993) |
| **원래 목적** | ECU 간 저비용, 내잡음 통신 — 배선 수 감소 |
| **설계 가정** | 물리적으로 폐쇄된 네트워크, 모든 노드는 신뢰할 수 있음 |
| **보안 고려** | **없음** — 1980년대에 차량 해킹은 위협 모델에 없었음 |

---

## CAN 프레임 구조

### Standard CAN (CAN 2.0A)

```
+-----+----+-----+---+------+-----+-----+-----+---+-----+
| SOF | ID | RTR |IDE| DLC  | Data| CRC | ACK | EOF|IFS  |
| 1b  |11b | 1b  |1b | 4b   |0-8B | 15b | 2b  | 7b| 3b  |
+-----+----+-----+---+------+-----+-----+-----+---+-----+
        ^                     ^
        |                     |
   Arbitration ID         Payload
   (우선순위 결정)       (실제 데이터)

※ 보안 필드 없음 — MAC도, 발신자 ID도, 암호화도 없다
```

### 보안 관점에서의 구조적 문제

| 필드 | 보안 문제 |
|------|----------|
| **Arbitration ID (11b)** | 발신자를 식별하는 것이 아닌 메시지 우선순위만 결정 — 누구든 같은 ID로 전송 가능 |
| **Data (0-8B)** | 평문 전송 — 버스에 연결된 모든 노드가 읽을 수 있음 |
| **CRC (15b)** | 전송 오류 검출용 — 악의적 변조 탐지 불가 (공격자도 유효한 CRC 계산 가능) |
| **ACK** | 수신 확인만 — 발신자 인증과 무관 |

---

## CAN Bus 통신 메커니즘

### 브로드캐스트 + 중재 (Arbitration)

```
ECU-A (엔진) ──┐
ECU-B (브레이크)──┼── CAN Bus (shared medium) ── 모든 노드가 수신
ECU-C (ADAS) ──┤
OBD-II 포트 ───┘  ← 외부 장치 연결 가능!

동시 전송 시 중재:
  - Dominant(0) > Recessive(1) — 낮은 ID가 우선
  - 패배한 노드는 자동 재시도
  - 중재는 공정성이 아닌 우선순위 기반
```

### 핵심 특성

| 특성 | 설명 | 보안 함의 |
|------|------|----------|
| **멀티마스터** | 모든 노드가 자유롭게 전송 | 외부 장치도 마스터로 동작 가능 |
| **브로드캐스트** | 모든 메시지가 전체 버스에 전파 | 도청(eavesdropping) 즉시 가능 |
| **ID 기반 필터링** | 수신측이 관심 있는 ID만 처리 | 발신자 검증 없이 ID만 일치하면 수용 |
| **비연결형** | 세션/핸드셰이크 없음 | Replay attack에 무방비 |

---

## CAN 프로토콜 진화

### CAN 2.0 → CAN-FD → CAN-XL

| | CAN 2.0 | CAN-FD | CAN-XL |
|--|---------|--------|--------|
| **최대 속도** | 1 Mbps | 8 Mbps (data phase) | 20 Mbps |
| **Payload** | 8 bytes | 64 bytes | 2048 bytes |
| **ID 비트** | 11/29 | 11/29 | 11/29 |
| **보안** | ❌ 없음 | ❌ 없음 | ✅ CANsec (Layer 2 보안) |
| **인증** | ❌ | ❌ (SecOC로 상위 계층 추가) | ✅ (프로토콜 내장) |
| **암호화** | ❌ | ❌ | ✅ (AES-GCM / AES-CCM) |
| **표준** | ISO 11898-1 | ISO 11898-1:2015 | CiA 610-3 |

### CAN-FD: 더 큰 payload, 여전히 무방비

```
CAN-FD 프레임:
+-----+----+-----+---+-----+------+------+-----+-----+
| SOF | ID | ... |BRS| DLC | Data | CRC  | ACK | EOF |
|     |    |     |   |     | 0-64B| 17/21b|     |     |
+-----+----+-----+---+-----+------+------+-----+-----+
                   ^
                   |
          Bit Rate Switch: data phase에서 속도 증가
          → payload 증가로 SecOC MAC을 데이터에 포함 가능!
```

**CAN-FD + SecOC**: 64바이트 payload 중 일부를 MAC(4~8B) + Freshness(2~4B)에 할당하여 상위 계층 인증 구현. 하지만 프로토콜 자체가 아닌 **어플리케이션 레벨 추가** — 모든 ECU가 지원해야 동작.

### CAN-XL: 프로토콜 레벨 보안 (CANsec)

```
CAN-XL 프레임 (CANsec 활성):
+-----+----+------+---------------------------+------+-----+
| SOF | ID | HDR  |    Encrypted Data         | AUTH | EOF |
|     |    |      |    + Integrity Tag         | TAG  |     |
+-----+----+------+---------------------------+------+-----+
                    ^                           ^
                    |                           |
              AES-GCM/CCM 암호화            인증 태그
              → 도청 불가                   → 위조 불가

CANsec = CAN-XL의 Layer 2 보안 프로토콜
  - AES-128/256-GCM 또는 AES-CCM
  - 프레임 단위 암호화 + 인증
  - Freshness Value로 replay 방어
  - 키 관리: HSM + 초기 키 교환 프로토콜
```

---

## CAN 에러 처리 메커니즘 (Bus-Off 공격의 기반)

CAN 프로토콜은 에러 감지 및 복구 메커니즘을 내장하고 있다. 이 메커니즘을 **악용**하면 특정 ECU를 네트워크에서 강제 퇴장시키는 **Bus-Off 공격**이 가능하다.

### Error Frame 구조

```
정상 프레임 전송 중 에러 감지 시:

[정상 프레임 ...] ──에러 감지──> [Error Flag (6b)] + [Error Delimiter (8b)]
                                      │
                                 6개 dominant bit 연속
                                 → Bit Stuffing 규칙 위반을 강제하여
                                   모든 노드에게 "이 프레임은 무효"를 알림
```

### Error Counter와 상태 전이

각 CAN 노드는 **TEC**(Transmit Error Counter)와 **REC**(Receive Error Counter) 두 개의 에러 카운터를 유지한다.

```
                 TEC/REC < 128           TEC/REC ≥ 128          TEC > 255
[Error Active] ──────────────> [Error Passive] ──────────────> [Bus-Off]
  │                               │                              │
  │ 정상 동작                      │ 전송 가능하나                 │ 통신 완전 차단
  │ Active Error Flag 전송         │ Passive Error Flag 전송      │ 128 × 11 recessive bit
  │ (다른 노드의 전송도 중단시킴)   │ (다른 노드 방해 안 함)       │ 관찰 후 복귀 시도
  │                               │                              │
  └── 에러 시 +8, 성공 시 -1 ─────┘                              │
                                                                 │
  ※ Bus-Off 상태의 ECU는 CAN Bus에서 완전히 격리됨               │
  → 브레이크/조향 ECU가 Bus-Off 되면? → 안전 기능 상실!           │
                                                                 │
  복귀: 128번의 11 recessive bit 시퀀스 관찰 후 Error Active 복귀  ┘
```

### 에러 카운터 변화 규칙

| 이벤트 | TEC 변화 | REC 변화 |
|--------|---------|---------|
| 송신 에러 감지 | **+8** | — |
| 수신 에러 감지 | — | **+1** |
| 수신 에러 (첫 감지자) | — | **+8** |
| 성공적 송/수신 | **-1** | **-1** |
| Bus-Off 복귀 | 0으로 리셋 | 0으로 리셋 |

**핵심**: 에러 시 +8, 성공 시 -1 → **에러 비율이 12.5%(1/8)만 넘어도 카운터가 증가** → 공격자가 지속적으로 에러를 유발하면 대상 ECU를 Bus-Off로 몰 수 있다.

### Bus-Off 공격 시나리오 (dry-run)

```
공격 목표: 브레이크 ECU(ID 0x101)를 Bus-Off 상태로 만들기

Step 1: 타겟 프레임 식별
  - 브레이크 ECU가 ID 0x101로 주기적(20ms) 전송 확인

Step 2: 동시 전송으로 에러 유발
  [공격자]      [브레이크 ECU]     [CAN Bus]
      │              │                │
      │   ID 0x101 전송 시작 ──────>  │  ← 정상 전송 시작
      │              │                │
      │   같은 ID로 다른 데이터 전송 ─>│  ← 데이터 필드에서 비트 충돌!
      │              │                │
      │              │   ← Error Frame │  ← 둘 다 에러 감지
      │              │                │
      │   TEC: +8    │   TEC: +8      │  ← 양쪽 다 에러 카운터 증가
      │              │                │

Step 3: 비대칭 에러 축적
  - 공격자: 에러 후 즉시 정상 프레임 성공 전송 → TEC -1
  - 브레이크 ECU: 다시 전송 시도 → 공격자가 또 방해 → TEC +8
  
  반복 32회 후:
    공격자 TEC: ~32 (에러 +8, 성공 -1 반복)
    브레이크 ECU TEC: 256 → Bus-Off! ✗

Step 4: 결과
  - 브레이크 ECU가 CAN Bus에서 격리됨
  - 차량은 브레이크 상태 메시지를 수신할 수 없음
  - → 안전 임계 기능 상실
```

**방어**: CAN Bus에는 이 공격에 대한 프로토콜 레벨 방어가 없다 → Gateway의 Rate Limiting + IDS의 에러 프레임 빈도 모니터링으로 탐지해야 한다.

---

## CAN Arbitration 상세 (비트 단위 dry-run)

### 3개 ECU 동시 전송 예시

```
세 ECU가 동시에 전송을 시작하는 상황:
  ECU-A: ID = 0x100 = 0001_0000_0000 (엔진 RPM, 높은 우선순위)
  ECU-B: ID = 0x130 = 0001_0011_0000 (변속기)
  ECU-C: ID = 0x200 = 0010_0000_0000 (에어컨, 낮은 우선순위)

비트 단위 중재 과정 (ID bit 10 → bit 0, MSB first):

Bit#  | ECU-A | ECU-B | ECU-C | Bus 값 | 결과
------+-------+-------+-------+--------+------------------
 10   |   0   |   0   |   0   |   0    | 세 ECU 모두 진행
  9   |   0   |   0   |   1   |   0    | ECU-C 탈락! ★
      |       |       |       |        |  (1 보냈는데 bus=0 → 패배 감지)
  8   |   0   |   0   |  ---  |   0    | A, B 진행
  7   |   1   |   1   |  ---  |   1    | A, B 진행
  6   |   0   |   0   |  ---  |   0    | A, B 진행
  5   |   0   |   0   |  ---  |   0    | A, B 진행
  4   |   0   |   1   |  ---  |   0    | ECU-B 탈락! ★
      |       |       |       |        |  (1 보냈는데 bus=0 → 패배 감지)
  3   |   0   |  ---  |  ---  |   0    | ECU-A만 진행
  2   |   0   |  ---  |  ---  |   0    |
  1   |   0   |  ---  |  ---  |   0    |
  0   |   0   |  ---  |  ---  |   0    |

→ ECU-A(0x100) 승리! 엔진 RPM 메시지 전송 완료
→ ECU-B, ECU-C는 bus가 idle 되면 자동 재시도

핵심 원리:
  - Dominant(0) > Recessive(1) — wired-AND 로직
  - 각 노드는 자신이 보낸 비트와 bus 값을 비교
  - 불일치 감지 시 전송 포기 (비파괴적 중재)
  - ID 숫자가 낮을수록 우선순위 높음
```

### 보안 관점에서의 중재 문제

| 문제 | 설명 |
|------|------|
| **우선순위 하이재킹** | 공격자가 ID=0x000 프레임을 전송하면 모든 정상 ECU를 이길 수 있음 |
| **DoS via 중재** | 최고 우선순위 ID로 연속 전송 → 다른 ECU 영원히 중재 패배 |
| **ID 충돌** | 정상 ECU와 같은 ID로 전송 → 데이터 불일치 → 에러 프레임 → Bus-Off 유도 |

---

## OBD-II: 공격의 물리적 진입점

### OBD-II 포트란?

```
차량 운전석 하단 (법적 의무 장착)
        │
+-------v-------+
|  OBD-II Port  |  ← 16핀 커넥터 (SAE J1962)
|               |
|  Pin 6: CAN-H |  ← CAN Bus에 직접 연결
|  Pin 14: CAN-L|
|  Pin 16: +12V |
|  Pin 4/5: GND |
+---------------+
        │
        v
  CAN Bus 전체에 접근 가능
```

| 원래 목적 | 보안 문제 |
|----------|----------|
| 배기가스 진단 (미국 EPA 규정, 1996~) | **인증 없이** CAN Bus에 물리적 접근 가능 |
| 정비소 고장 진단 | 읽기뿐 아니라 **쓰기(injection)도 가능** |
| 차량 검사 | 방화벽/게이트웨이 없는 차량은 전체 도메인 접근 |

### Tesla FSD 탈옥에서의 역할

```
[탈옥 동글] ──OBD-II──> [CAN Bus]
     │
     ├── GPS 좌표 위조 CAN 프레임 주입
     ├── Region Code 프레임 변조
     └── Feature Flag 프레임 위조
          │
          v
     [FSD SoC가 위조 프레임을 정상으로 수용]
     → CAN 메시지 인증이 없으므로 구별 불가
```

---

## 구조적 취약점 요약

```
1980년대 설계 가정:
  "버스에 연결된 노드는 모두 신뢰할 수 있다"
       │
       v
  ┌─────────────────────────────────────────┐
  │  CAN의 4가지 구조적 결함                 │
  │                                         │
  │  1. 무인증: 발신자 검증 없음             │
  │  2. 무암호화: 평문 전송                  │
  │  3. 브로드캐스트: 전체 노드에 전파        │
  │  4. 무상태: 세션/시퀀스 관리 없음         │
  └─────────────────────────────────────────┘
       │
       v
  현대 차량에서의 결과:
  - OBD-II로 외부 장치가 CAN에 접근
  - 위조 메시지와 정상 메시지를 구별할 방법 없음
  - GPS, 속도, 기능 플래그 등 모든 데이터 조작 가능
```

---

## Automotive Ethernet과의 비교

최신 차량은 CAN과 함께 Automotive Ethernet도 사용한다:

| | CAN / CAN-FD | Automotive Ethernet |
|--|--------------|-------------------|
| **토폴로지** | 버스 (브로드캐스트) | 스위치 기반 (유니캐스트) |
| **속도** | 1~8 Mbps | 100 Mbps ~ 10 Gbps |
| **보안** | 프로토콜 없음 | MACsec (802.1AE), TLS |
| **격리** | 물리적 격리 어려움 | VLAN, 스위치 ACL |
| **용도** | ECU 제어, 센서 | ADAS, 카메라, 인포테인먼트 |
| **비용** | 매우 저렴 | 상대적으로 높음 |

**현실**: CAN은 사라지지 않는다 — 수십 년의 레거시, 낮은 비용, 실시간 보장. 보안은 SoC 레벨(HSM + SecOC + Gateway)에서 추가해야 한다.

---

## 대표 문제

### Q1. "CAN Bus에 왜 인증이 없는가? 설계 결함인가?"

**사고 과정**:

1. CAN은 1983년 설계 — 당시 차량 ECU는 5~10개, 외부 연결 없음
2. 설계 목표: 배선 비용 절감 + 실시간 통신 + 내잡음성
3. 인증을 추가하면: 지연 시간 증가, 대역폭 소모, ECU 연산 부담
4. 1980년대 위협 모델에 "차량 해킹"은 존재하지 않았음

**핵심 답변**: "설계 결함이 아닌 **설계 가정의 변화**다. CAN은 물리적으로 폐쇄된 환경을 가정했고, 그 가정 하에서는 합리적 설계였다. 문제는 OBD-II, 텔레매틱스, V2X 등으로 차량이 개방형 시스템이 되면서 가정이 무너진 것이다. SoC Secure Boot에서 BootROM이 '변경 불가능'이라는 가정에 의존하듯, CAN은 '폐쇄 네트워크'라는 가정에 의존했다 — 차이는 BootROM 가정은 여전히 유효하지만 CAN 가정은 깨졌다는 것."

### Q2. "CAN-FD가 보안을 해결하지 못하는 이유는?"

**사고 과정**:

1. CAN-FD는 payload를 8B → 64B로 확장
2. 더 큰 payload에 MAC을 넣을 수 있다 (SecOC)
3. 하지만 SecOC는 **프로토콜 계층이 아닌 어플리케이션 계층** 추가
4. 모든 ECU가 SecOC를 지원해야 하고, 키 관리 인프라 필요
5. 레거시 ECU와 혼재하면 보안 체인 끊김

**핵심 답변**: "CAN-FD는 대역폭 문제를 해결했지 보안 문제를 해결하지 않았다. SecOC를 통해 상위 계층에서 인증을 추가할 수 있지만, 이는 모든 ECU의 펌웨어 업데이트와 HSM 탑재, 키 관리 인프라를 전제한다. CAN-XL의 CANsec이 프로토콜 레벨에서 보안을 내장한 것과 대조적이다 — Secure Boot에서 서명 검증이 BootROM에 내장되어야 의미가 있듯이, 통신 보안도 프로토콜 레벨에 있어야 한다."

---

## 확인 퀴즈

### Quiz 1. CAN Bus에서 Bus-Off 공격이 가능한 근본적 이유는?

<details>
<summary>정답 보기</summary>

CAN의 에러 처리 메커니즘이 **에러 카운터를 노드별로 독립 관리**하기 때문이다. 에러 발생 시 TEC가 +8 증가하지만 성공 시 -1만 감소하므로, 공격자가 특정 ECU의 전송을 지속적으로 방해하면 해당 ECU의 TEC만 선택적으로 증가시켜 255를 초과하게 만들 수 있다. 프로토콜 레벨에서 "정당한 에러"와 "공격에 의한 에러"를 구분하는 메커니즘이 없는 것이 근본 원인이다.
</details>

### Quiz 2. CAN 2.0, CAN-FD, CAN-XL 중 프로토콜 자체에 보안이 내장된 것은? 나머지 두 개는 어떻게 보안을 추가하는가?

<details>
<summary>정답 보기</summary>

**CAN-XL**만 CANsec(Layer 2 보안)이 프로토콜에 내장되어 있다 (AES-GCM/CCM 암호화 + 인증).
- CAN 2.0: 8B payload로 MAC 추가 공간이 부족 → 별도 프레임 필요하여 비실용적
- CAN-FD: 64B payload에서 SecOC를 **어플리케이션 계층**으로 추가 (Data + Truncated MAC + Freshness)
- 핵심 차이: SecOC는 모든 ECU가 지원해야 동작하는 상위 계층 추가이고, CANsec은 프로토콜 레벨 내장이다.
</details>

### Quiz 3. CAN Arbitration에서 ID 0x080과 ID 0x0A0이 동시에 전송을 시작하면, 어느 시점에서 승패가 결정되는가?

<details>
<summary>정답 보기</summary>

두 ID를 이진수로 변환:
- 0x080 = `000_1000_0000`
- 0x0A0 = `000_1010_0000`

bit 10~8: 둘 다 `000` → 동일, 계속 진행
bit 7: 둘 다 `1` → 동일
**bit 6**: 0x080은 `0`(dominant), 0x0A0은 `1`(recessive) → **여기서 결정!**
0x0A0이 recessive(1)을 보냈는데 bus 값이 dominant(0)이므로 패배를 감지하고 전송 포기.
→ **ID 0x080 승리** (bit 5에서 결정, MSB부터 5번째 비트)
</details>

---

!!! warning "실무 주의점 — OBD-II 포트는 항상 열려있다"
    **현상**: OBD-II 포트에 진단 장비를 연결하면 SecOC가 적용된 ECU조차 raw CAN 메시지를 그대로 수신하며, 임의 ID로 메시지를 주입할 수 있다.

    **원인**: OBD-II는 법적 의무로 항상 접근 가능해야 하므로, Gateway가 진단 포트 트래픽을 화이트리스트에서 예외 처리하는 구현이 흔하다.

    **점검 포인트**: Gateway 화이트리스트에서 `0x7DF`(OBD broadcast), `0x7E0~0x7EF`(ECU 진단 주소) 범위가 내부 도메인으로 무조건 포워딩되는지 확인. 진단 세션 활성화 없이 기능 제어 메시지(예: 조향, 제동)가 통과되면 즉시 차단 규칙 추가 필요.

## 핵심 정리

- **CAN bus**: 1980년대 broadcast 직렬 버스. **인증/암호화 없음** — 보안 한계의 근원.
- **메시지 형식**: ID + DLC + Data (0-8 bytes) + CRC. 모든 ECU가 모든 메시지 수신.
- **CAN-FD (Flexible Data)**: 가변 길이 (최대 64 bytes), 빠른 BR.
- **CAN-XL**: 최대 2048 bytes, 10 Mbps.
- **SecOC**: AUTOSAR의 인증 추가 — Freshness Value (counter) + MAC. CAN 위에 보안 layer.
- **보안 강화 한계**: SecOC도 하드웨어 자원 제약 (8-byte MAC, freshness sync issue).

## 다음 단계

- 📝 [**Module 01 퀴즈**](quiz/01_can_bus_fundamentals_quiz.md)
- ➡️ [**Module 02 — Automotive SoC Security**](02_automotive_soc_security.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">코스 홈</div>
  </a>
  <a class="nav-next" href="../02_automotive_soc_security/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Automotive SoC Security (차량 SoC 보안 아키텍처)</div>
  </a>
</div>
