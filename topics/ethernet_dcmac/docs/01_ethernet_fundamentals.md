# Unit 1: Ethernet 기본 + 프레임 구조

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

## 핵심 개념
**Ethernet = LAN/데이터센터의 사실상 표준 L2 프로토콜. MAC(Media Access Control)이 프레임 생성/파싱/에러 검출을 담당하고, PHY가 물리적 전송을 담당.**

---

## Ethernet 속도 진화

| 세대 | 속도 | 표준 | 매체 | 데이터센터 용도 |
|------|------|------|------|---------------|
| GbE | 1 Gbps | 802.3ab | Cat5e 구리 | 레거시 |
| 10GbE | 10 Gbps | 802.3ae | SFP+ 광 | 서버 연결 |
| 25GbE | 25 Gbps | 802.3by | SFP28 | 서버 NIC |
| 40GbE | 40 Gbps | 802.3ba | QSFP+ | 스위치 업링크 |
| 100GbE | 100 Gbps | 802.3ck | QSFP28/56 | 현재 주류 |
| 200GbE | 200 Gbps | 802.3ck | QSFP56-DD | 차세대 |
| 400GbE | 400 Gbps | 802.3ck | OSFP/QSFP-DD | 최신 스파인 |
| 800GbE | 800 Gbps | 802.3df | OSFP-XD | 개발 중 |

**MangoBoost 맥락**: DCMAC = 100/200/400GbE MAC → 서버급 SmartNIC/DPU용

---

## Ethernet 프레임 구조

```
+----------+--------+--------+------+--------+---------+-----+-----+
| Preamble | SFD    | Dst    | Src  | Type/  | Payload | FCS | IFG |
| (7B)     | (1B)   | MAC    | MAC  | Length |         |(4B) |(12B)|
|          |        | (6B)   | (6B) | (2B)   |(46-1500)| CRC |     |
+----------+--------+--------+------+--------+---------+-----+-----+
|← PHY 영역 →|←          MAC 영역                    →|← PHY →|

총 크기: 64B (최소) ~ 1518B (표준 최대) ~ 9022B (Jumbo)
```

### 각 필드 상세

| 필드 | 크기 | 역할 |
|------|------|------|
| **Preamble** | 7B | 10101010... 패턴, 수신측 클럭 동기화 |
| **SFD** (Start Frame Delimiter) | 1B | 10101011 — 프레임 시작 표시 |
| **Dst MAC** | 6B | 목적지 MAC 주소 (Unicast/Multicast/Broadcast) |
| **Src MAC** | 6B | 출발지 MAC 주소 |
| **EtherType / Length** | 2B | ≥0x0600: 프로토콜 타입 (0x0800=IPv4, 0x86DD=IPv6) |
| | | <0x0600: Payload 길이 (IEEE 802.3) |
| **Payload** | 46-1500B | 상위 계층 데이터 (IP 패킷 등) |
| **FCS** (Frame Check Sequence) | 4B | CRC-32, Dst MAC부터 Payload까지의 무결성 검증 |
| **IFG** (Inter-Frame Gap) | 12B | 프레임 간 최소 간격 (96 bit time) |

### VLAN Tag (802.1Q)

```
VLAN 태그 삽입 시:

+--------+------+----------+------+---------+-----+
| Dst MAC| Src  | VLAN Tag | Type | Payload | FCS |
| (6B)   | MAC  | (4B)     | (2B) |         |(4B) |
+--------+------+----------+------+---------+-----+

VLAN Tag (4B):
  TPID (2B): 0x8100 (VLAN 식별)
  TCI (2B):
    PCP (3bit): Priority (0-7, QoS)
    DEI (1bit): Drop Eligible
    VID (12bit): VLAN ID (0-4095)
```

---

## FCS (CRC-32) — 핵심 에러 검출

### CRC-32 동작

```
TX:
  1. Dst MAC ~ Payload까지 CRC-32 계산
  2. 결과 4B를 FCS 필드에 삽입
  3. 프레임 전송

RX:
  1. 수신된 프레임의 Dst MAC ~ Payload에 대해 CRC-32 재계산
  2. 계산 결과 vs FCS 필드 비교
  3. 일치 → 정상, 불일치 → 프레임 폐기

CRC-32 다항식: x^32 + x^26 + x^23 + ... + x + 1
  (IEEE 802.3 표준)
```

### CRC의 한계

| 검출 가능 | 검출 불가능 |
|----------|-----------|
| 단일 비트 에러 | 일부 다중 비트 패턴 (확률적) |
| 버스트 에러 (32bit 이하) | CRC 자체가 변조된 경우 |
| 대부분의 랜덤 에러 | 의도적 변조 (보안 → MAC 범위 밖) |

---

## Ethernet 흐름 제어

### Pause Frame (IEEE 802.3x)

```
수신 버퍼 거의 가득 참:
  RX → TX: PAUSE Frame (pause_time = N × 512 bit time)
  TX: N 단위 시간 동안 전송 중단

문제: 포트 전체를 멈춤 → 다른 트래픽도 영향
```

### PFC (Priority-based Flow Control, 802.1Qbb)

```
우선순위별 개별 제어:

  RX → TX: PFC Frame (priority 3만 멈춰라)
  TX: priority 3 트래픽만 중단, 나머지 우선순위는 계속 전송

  8개 우선순위 × 개별 Pause → 세밀한 흐름 제어
  → 데이터센터에서 필수 (RoCE, Storage 등 무손실 네트워크)
```

---

## MAC 주소 구조

```
MAC 주소 = 48비트 (6바이트), 16진수 표기: AA:BB:CC:DD:EE:FF

  +--------+--------+--------+--------+--------+--------+
  | Byte 0 | Byte 1 | Byte 2 | Byte 3 | Byte 4 | Byte 5 |
  +--------+--------+--------+--------+--------+--------+
  |←   OUI (24bit)  →|←   NIC Specific (24bit)  →|

  Byte 0의 비트 구조:
    bit 0: 0 = Unicast, 1 = Multicast
    bit 1: 0 = Globally Unique (OUI 기반), 1 = Locally Administered

  특수 주소:
    FF:FF:FF:FF:FF:FF = Broadcast (모든 노드에 전달)
    01:80:C2:00:00:01 = Pause Frame 목적지 (IEEE 802.3x)
    01:00:5E:xx:xx:xx = IPv4 Multicast 매핑
```

**DV 관점**: MAC 주소 필터링 검증 시 Unicast/Multicast/Broadcast 각각의 동작을 확인해야 하고, Promiscuous 모드에서는 모든 주소를 수신하는지 확인.

---

## Ethernet 계층 구조 (MAC / PCS / PMA / PMD)

```
+--------------------------------------------------+
| MAC (Media Access Control)                        |
|   프레임 생성/파싱, FCS, 흐름 제어                |
|   ← DCMAC이 이 계층                              |
+--------------------------------------------------+
         | MII / XLGMII / CGMII / Segmented
         v
+--------------------------------------------------+
| PCS (Physical Coding Sublayer)                    |
|   인코딩 (64b/66b), Scrambling, Alignment         |
|   RS-FEC (100G+), Lane Distribution               |
+--------------------------------------------------+
         | PMA Service Interface
         v
+--------------------------------------------------+
| PMA (Physical Medium Attachment)                  |
|   SerDes, CDR, Signal Conditioning                |
+--------------------------------------------------+
         | PMD
         v
+--------------------------------------------------+
| PMD (Physical Medium Dependent)                   |
|   광모듈 (QSFP, SFP), 전기 인터페이스             |
+--------------------------------------------------+
         |
    Physical Medium (광섬유 / 구리)
```

**DV 관점**: MAC 검증은 주로 MAC ↔ PCS 경계(MII 인터페이스)와 MAC ↔ 상위 계층(AXI-S) 경계에서 수행.

---

## MII 인터페이스 종류

MAC과 PCS 사이의 인터페이스. 속도가 올라갈수록 데이터 폭이 넓어진다.

| 인터페이스 | 속도 | 데이터 폭 | 클럭 | 특징 |
|-----------|------|----------|------|------|
| **MII** | 10/100M | 4-bit | 2.5/25 MHz | 원조 |
| **GMII** | 1G | 8-bit | 125 MHz | GbE용 |
| **XGMII** | 10G | 32-bit (DDR 64-bit) | 156.25 MHz | 10G용, Control 캐릭터 포함 |
| **XLGMII** | 40G | 128-bit | 156.25 MHz | 4×10G 레인 기반 |
| **CGMII** | 100G | 256-bit | 390.625 MHz | 100G용 |
| **Segmented** | 100G+ | 가변 | 가변 | AMD DCMAC이 사용, 아래 상세 |

### Segmented 인터페이스 (DCMAC Line Side)

```
기존 MII: 한 번에 하나의 프레임만 전송 가능

Segmented: 하나의 버스 사이클에 여러 프레임의 세그먼트가 공존 가능

  +---------+---------+---------+---------+
  | Seg 0   | Seg 1   | Seg 2   | Seg 3   |
  | Frame A | Frame A | Frame B | Frame B |
  | (끝)    | (IFG)   | (시작)  | (계속)  |
  +---------+---------+---------+---------+

  → 프레임 간 IFG를 최소화하여 대역폭 효율 극대화
  → 100G+에서 라인 레이트 달성에 필수
  → 각 세그먼트에 Control 정보(SOP, EOP, Error) 포함

DV 관점:
  - 세그먼트 경계에서 프레임 시작/종료 정확성 검증
  - 동일 사이클 내 다중 프레임 세그먼트 처리 검증
  - 에러 세그먼트 주입 및 전파 검증
```

---

## PCS 64b/66b 인코딩

100G+ Ethernet에서 사용하는 표준 인코딩 방식. (이전 세대의 8b/10b보다 오버헤드가 낮음)

```
8b/10b vs 64b/66b 오버헤드 비교:
  8b/10b:  10bit 중 8bit 유효 → 오버헤드 20%
  64b/66b: 66bit 중 64bit 유효 → 오버헤드 ~3%

64b/66b 블록 구조:
  +----+-------------------------------+
  | SH | Payload (64 bits)             |
  |(2b)|                               |
  +----+-------------------------------+

  Sync Header (SH):
    01 = Data Block (64비트 전부 데이터)
    10 = Control Block (제어 정보 포함 — SOP, EOP, Idle, Error 등)

인코딩 과정:
  1. MAC에서 64비트 데이터 또는 제어 문자를 받음
  2. 2비트 Sync Header를 앞에 붙여 66비트 블록 생성
  3. Scrambling 적용 (DC 밸런스 + 클럭 복원 지원)
  4. SerDes로 전달

디코딩 과정 (RX):
  1. SerDes에서 비트 스트림 수신
  2. Block Lock: Sync Header 패턴(01/10)을 찾아 66비트 경계 정렬
  3. Descrambling
  4. Data/Control 블록 분리 → MAC에 전달
```

### Lane Distribution (Multi-Lane)

```
100GbE = 4 × 25G 또는 2 × 50G 레인

Lane Distribution:
  PCS가 66비트 블록들을 Round-Robin으로 레인에 분배

  Block 0 → Lane 0
  Block 1 → Lane 1
  Block 2 → Lane 2
  Block 3 → Lane 3
  Block 4 → Lane 0  (다시)
  ...

Alignment Marker (AM):
  각 레인에 주기적으로 삽입 (약 16K 블록마다)
  → RX 측에서 레인 순서 복원 + 레인 간 Skew 보정

  PCS Lane 0: ...data... [AM0] ...data... [AM0] ...
  PCS Lane 1: ...data... [AM1] ...data... [AM1] ...
  ...

DV 관점:
  - Lane 순서 뒤바뀜(Lane Swizzle) 시 PCS가 복원하는지 검증
  - Lane 간 Skew 보정 정확성
  - AM 삽입/제거 주기 정확성
```

---

## RS-FEC (Reed-Solomon Forward Error Correction)

100G+ Ethernet에서 BER(Bit Error Rate)을 낮추기 위한 필수 기술.

```
왜 필요한가?
  - 25Gbps+ SerDes에서는 신호 품질 열화로 BER이 높아짐
  - CRC(FCS)는 에러를 "검출"만 함 → 프레임 폐기 → 재전송 필요
  - RS-FEC는 에러를 "정정"함 → 폐기 없이 복구 → 처리량 유지

동작 원리:
  TX: PCS 인코딩 후, RS 부호화 (패리티 심볼 추가)
  RX: RS 복호화로 에러 정정 → PCS 디코딩

  +------+    +------+    +--------+    +--------+
  | MAC  | → | PCS  | → | RS-FEC | → | SerDes |
  |      |    |64b66b|    |Encode  |    |   TX   |
  +------+    +------+    +--------+    +--------+

                         RS(544, 514):
                           514 심볼 데이터 + 30 심볼 패리티
                           → 최대 16 심볼 에러 정정 가능

성능 지표:
  - Pre-FEC BER: ~1e-5 (RS-FEC 투입 전, SerDes 출력)
  - Post-FEC BER: ~1e-13 이하 (RS-FEC 정정 후)
  → 8자릿수 이상의 BER 개선

종류:
  | 표준 | 속도 | FEC 방식 | 레이턴시 |
  |------|------|----------|---------|
  | 802.3bj (Clause 91) | 100G | RS(528,514) | ~50ns |
  | 802.3cd (Clause 119) | 200G/400G | RS(544,514) | ~50ns |

DV 관점:
  - FEC 카운터(corrected/uncorrected codeword) 정확성
  - FEC 바이패스 모드 동작
  - Pre-FEC BER vs Post-FEC BER 통계 수집 검증
```

---

## Q&A

**Q: Ethernet 프레임의 최소/최대 크기는 왜 정해져 있는가?**
> "최소 64B: CSMA/CD 충돌 감지에 필요한 최소 전송 시간 보장을 위해 역사적으로 설정됨. 현대 Full-Duplex에서는 충돌 없지만 호환성을 위해 유지. Payload가 46B 미만이면 패딩 추가. 최대 1518B(표준) / 9022B(Jumbo): 수신 버퍼 크기와 지연 제한을 위해 설정. Jumbo Frame은 서버 환경에서 오버헤드 감소를 위해 사용."

**Q: PFC가 Pause Frame보다 나은 이유는?**
> "Pause Frame은 포트 전체를 멈추므로, 한 트래픽의 혼잡이 모든 트래픽에 영향을 준다(Head-of-Line Blocking). PFC는 8개 우선순위별로 독립적으로 Pause할 수 있어, RoCE 같은 무손실 트래픽만 보호하면서 나머지는 계속 전송 가능하다."

**Q: 64b/66b 인코딩이 8b/10b보다 유리한 이유는?**
> "오버헤드 차이가 핵심이다. 8b/10b는 20% 오버헤드(10GbE에서 실제 SerDes 속도 12.5Gbps 필요), 64b/66b는 ~3% 오버헤드(25GbE에서 25.78Gbps). 고속에서 SerDes 속도를 낮출 수 있어 구현 비용과 전력이 줄어든다. 단점은 DC 밸런스를 별도 Scrambling으로 확보해야 하는 점."

**Q: RS-FEC는 왜 100G+에서 필수인가?**
> "25Gbps+ SerDes에서 신호 감쇠와 크로스톡으로 Pre-FEC BER이 ~1e-5 수준이다. FEC 없이 CRC만으로는 프레임 폐기율이 높아 사실상 라인 레이트를 유지할 수 없다. RS-FEC(544,514)가 Post-FEC BER을 1e-13 이하로 낮추므로, 물리적 열악한 채널에서도 무결성 있는 통신이 가능해진다."

**Q: Segmented 인터페이스란 무엇이고 왜 필요한가?**
> "기존 MII는 한 사이클에 하나의 프레임만 처리하므로 짧은 프레임이 연속되면 IFG 오버헤드가 커진다. Segmented 인터페이스는 하나의 버스 사이클 내에 여러 프레임의 세그먼트를 담을 수 있어 IFG를 최소화하고 대역폭 활용률을 극대화한다. 100G+에서 라인 레이트 달성에 필수적이다."

<div class="chapter-nav">
  <a class="nav-prev" href="index.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">코스 홈</div>
  </a>
  <a class="nav-next" href="02_dcmac_architecture.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">DCMAC 아키텍처</div>
  </a>
</div>
