# Unit 1: UFS 프로토콜 스택

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

## 핵심 개념
**UFS = SCSI 명령을 UniPro 링크 위에서 M-PHY 시리얼 인터페이스로 전달하는 3계층 프로토콜. eMMC 대비 고속(2.9GB/s+), Full-duplex, 명령 큐잉(최대 32개)을 지원하는 모바일/서버 스토리지 표준.**

---

## 3계층 구조

```
+------------------------------------------------------------------+
|  UFS Application Layer (UTP — UFS Transport Protocol)             |
|    - SCSI 명령 세트 (READ/WRITE/QUERY)                            |
|    - UPIU (UFS Protocol Information Unit) 패킷 구성               |
|    - Task Management (Abort, LUN Reset 등)                        |
+------------------------------------------------------------------+
         | UPIU
+------------------------------------------------------------------+
|  UniPro (Unified Protocol) — Link Layer                           |
|    - L4: DME (Device Management Entity)                           |
|    - L3: N-Layer (Network, 보통 point-to-point)                  |
|    - L2: DL (Data Link — CRC, ACK/NAK, Flow Control)             |
|    - L1.5: PHY Adapter (인터페이스 어댑터)                        |
+------------------------------------------------------------------+
         | 시리얼 데이터
+------------------------------------------------------------------+
|  M-PHY (MIPI Physical Layer)                                      |
|    - HS (High Speed) Gear 1~4: 1.46~11.6 Gbps/lane              |
|    - PWM (저전력 모드): Gear 1~7                                  |
|    - 1~2 Lane (데이터 레인 수)                                    |
|    - CDR, Calibration, Power Mode 전환                            |
+------------------------------------------------------------------+
```

---

## UFS vs eMMC 비교

| 항목 | UFS 3.1/4.0 | eMMC 5.1 |
|------|------------|----------|
| 인터페이스 | 시리얼 (M-PHY) | 병렬 (8-bit bus) |
| 듀플렉스 | **Full-duplex** (동시 R/W) | Half-duplex |
| 최대 속도 | 2.9 GB/s (UFS 3.1) / 4.2 GB/s (4.0) | 400 MB/s |
| 명령 큐잉 | **최대 32개** (MCQ: 최대 64+) | 1개 (순차) |
| 프로토콜 스택 | SCSI + UniPro + M-PHY | MMC 명령 |
| 전력 관리 | HS/PWM Gear + Hibernate | Sleep/Standby |
| 용도 | 플래그십 모바일, 서버 | 중급 모바일, IoT |

**핵심 차이**: 명령 큐잉과 Full-duplex가 UFS의 압도적 성능 차이를 만든다. eMMC는 명령 하나를 보내고 응답을 기다려야 하지만, UFS는 32개 명령을 동시에 처리할 수 있다.

---

## UPIU (UFS Protocol Information Unit)

### UPIU 구조

```
+-------------------------------------------+
| UPIU Header (12 bytes)                     |
|                                            |
|  Transaction Type (1B): Command/Response/  |
|                          Data-In/Data-Out/ |
|                          Query/Task Mgmt   |
|  Flags (1B)                                |
|  LUN (1B): Logical Unit Number             |
|  Task Tag (1B): 명령 식별자 (0~31)         |
|  Command Set Type (1B)                     |
|  Total EHS Length (1B)                     |
|  Device Info / Response (2B)               |
|  Data Segment Length (2B)                  |
+-------------------------------------------+
| Command UPIU:                              |
|   Expected Data Transfer Length (4B)       |
|   CDB (Command Descriptor Block, 16B)     |
|     - SCSI 명령 (READ_10, WRITE_10 등)    |
+-------------------------------------------+
| Data Segment (가변)                        |
|   실제 데이터 또는 Query 파라미터          |
+-------------------------------------------+
```

### UPIU 유형

| UPIU Type | 방향 | 용도 |
|-----------|------|------|
| Command UPIU | Host → Device | SCSI 명령 전달 (READ, WRITE 등) |
| Response UPIU | Device → Host | 명령 완료 응답 + 상태 |
| Data-Out UPIU | Host → Device | Write 데이터 전달 |
| Data-In UPIU | Device → Host | Read 데이터 전달 |
| Query Request | Host → Device | 디바이스 설정/상태 조회 |
| Query Response | Device → Host | 조회 응답 |
| Task Mgmt Request | Host → Device | 명령 중단, LUN 리셋 등 |
| Task Mgmt Response | Device → Host | Task Mgmt 결과 |
| NOP OUT / NOP IN | 양방향 | 링크 상태 확인 (ping) |

---

## UFS 버전 진화

| 버전 | 연도 | 최대 속도 | 핵심 추가 기능 |
|------|------|----------|--------------|
| UFS 2.0 | 2013 | 1.2 GB/s (HS-G2×2) | 기본 SCSI 명령, 32 슬롯 큐잉 |
| UFS 2.1 | 2016 | 1.2 GB/s | Crypto 엔진 (Inline Encryption), Device Health 리포트 |
| UFS 3.0 | 2018 | 2.9 GB/s (HS-G3×2) | HS-G3, 2-Lane 필수, Write Booster |
| UFS 3.1 | 2020 | 2.9 GB/s | Write Booster 강화, Host Performance Booster (HPB), DeepSleep |
| UFS 4.0 | 2022 | 4.6 GB/s (HS-G4×2) | HS-G4, **MCQ** (Multi-Circular Queue), Advanced RPMB |
| UFS 5.0 | 2024 | 9.2 GB/s (HS-G5×2) | HS-G5, 향상된 전력 관리 |

```
핵심 기능 상세:

  Write Booster (UFS 3.0+):
    - SLC 버퍼를 임시 Write 캐시로 사용
    - 순간 Write 성능을 SLC 수준으로 끌어올림
    - 이후 Idle 시 TLC/QLC로 데이터 이동 (flush)
    - Device Descriptor에서 WB 크기/상태 확인

  HPB — Host Performance Booster (UFS 3.1+):
    - Host가 L2P(Logical-to-Physical) 맵의 일부를 DRAM에 캐싱
    - Random Read 시 Device 내부 L2P 테이블 접근 비용 제거
    - HPB Read 명령으로 캐싱된 물리 주소 직접 전달

  Inline Encryption (UFS 2.1+):
    - HCI에 내장된 Crypto 엔진
    - 데이터가 UniPro로 나가기 전 자동 암호화 (AES-256-XTS)
    - UTRD에 Crypto Config Index 지정 → 키/알고리즘 선택
    - SW가 평문으로 DMA → HCI가 자동 암호화 → Device에 암호문 전달

  MCQ — Multi-Circular Queue (UFS 4.0+):
    → Unit 2에서 상세 설명
```

---

## UniPro 핵심 — DL Layer

### 프레임 구조

```
UniPro DL Frame:
+------+--------+--------+---------+-----+
| SOF  | Header | Data   | CRC-16  | EOF |
| (1B) | (3B)   | (가변) | (2B)    |(1B) |
+------+--------+--------+---------+-----+

  SOF: Start of Frame
  Header: TC (Traffic Class), Frame Type, Length
  Data: UPIU 패킷 (또는 일부)
  CRC-16: Header + Data의 무결성 검증
  EOF: End of Frame
```

### DL Flow Control

```
Credit 기반 흐름 제어:

  TX 측: 잔여 크레딧 확인 → 크레딧 있으면 전송
  RX 측: 프레임 수신 → 크레딧 반환 (AFC — Ack Flow Control)

  AFC Frame:
    RX → TX: "크레딧 N개 반환" → TX가 N개 더 전송 가능

  NAK:
    CRC 에러 → RX가 NAK → TX가 재전송
```

---

## UniPro 상세 — L4(DME) / L3 / L1.5

### L4: DME (Device Management Entity)

```
DME = UniPro 링크 전체를 관리하는 최상위 제어 엔티티

주요 기능:
  1. Link Startup — 초기 링크 수립
     DME_LINKSTARTUP 명령 → M-PHY 초기화 → 양측 UniPro 협상
     → 링크 수립 완료 (또는 실패)

  2. 속성 관리 (MIB — Management Information Base)
     DME_GET / DME_SET: 로컬 UniPro 속성 읽기/쓰기
     DME_PEER_GET / DME_PEER_SET: 상대측(Device) 속성 읽기/쓰기

     주요 MIB 속성:
       PA_TxGear / PA_RxGear: TX/RX Gear 설정
       PA_ActiveTxDataLanes / PA_ActiveRxDataLanes: 활성 레인 수
       PA_HSSeries: HS Series (A 또는 B)
       PA_PWRMode: Power Mode (Slow/SlowAuto/Fast/FastAuto)

  3. Power Mode 전환
     DME_SET으로 Gear/Lane/Mode 설정 후 PA_PWRMode 쓰기
     → UniPro가 M-PHY 설정 변경 수행
     → 완료 시 DME_POWERON / Power Mode Ind 통지

  4. Hibernate
     DME_HIBERNATE_ENTER: 최저 전력 상태 진입
     DME_HIBERNATE_EXIT: 복귀 (M-PHY 재초기화 포함)
```

### L3: Network Layer

```
UFS에서 L3(Network Layer)는 단순화:
  - Point-to-point 연결 (Host ↔ Device 1:1)
  - 라우팅 불필요 → DeviceID는 항상 0
  - 멀티디바이스 UFS는 별도 링크 (버스가 아님)

  L3 헤더: Src DeviceID + Dst DeviceID (각 1 byte)
  → UFS에서는 사실상 고정값 (0x00 ↔ 0x01)
```

### L1.5: PHY Adapter Layer

```
L1.5 = UniPro와 M-PHY 사이의 인터페이스 어댑터

역할:
  1. UniPro 프레임을 M-PHY Symbol로 변환
  2. Gear/Lane 설정을 M-PHY 파라미터로 변환
  3. Power Mode 전환 시 M-PHY 제어 시퀀스 생성
  4. Lane 간 Skew 보정 (2-Lane 모드)

  DL Frame → L1.5가 Symbol 인코딩 → M-PHY TX로 전달
  M-PHY RX → L1.5가 Symbol 디코딩 → DL Frame으로 재구성
```

---

## M-PHY — 물리 계층

### HS Gear와 속도

| Gear | 속도/Lane | 2-Lane 속도 | UFS 버전 |
|------|----------|------------|---------|
| HS-G1 | 1.46 Gbps | 2.9 Gbps | UFS 2.0 |
| HS-G2 | 2.9 Gbps | 5.8 Gbps | UFS 2.1 |
| HS-G3 | 5.8 Gbps | 11.6 Gbps | UFS 3.0/3.1 |
| HS-G4 | 11.6 Gbps | 23.2 Gbps | UFS 4.0 |
| HS-G5 | 23.2 Gbps | 46.4 Gbps | UFS 5.0 (예정) |

### CDR과 Calibration

```
CDR (Clock and Data Recovery):
  HS 모드에서 데이터에서 클럭을 복원하는 회로
  - TX: 데이터를 시리얼 스트림으로 전송 (임베디드 클럭)
  - RX: CDR이 수신 데이터의 에지에서 클럭 추출
  - Lock 시간: CDR이 안정된 클럭을 복원하는 데 필요한 시간
  - Gear가 높을수록 CDR Lock이 까다로움 (더 높은 주파수)

Calibration:
  M-PHY의 아날로그 파라미터를 최적화하는 과정

  1. Impedance Calibration
     - TX/RX의 출력/입력 임피던스를 50Ω에 맞춤
     - PVT(Process/Voltage/Temperature) 변화 보상

  2. Eye Training (HS 모드)
     - RX가 데이터 아이(eye)의 최적 샘플링 포인트 탐색
     - 수직(Voltage) + 수평(Timing) 마진 최대화
     - Gear 전환 시마다 재수행

  3. 전환 시 Calibration 순서
     PWM → HS 전환:
       a. TX Calibration (임피던스)
       b. CDR Lock 대기
       c. RX Eye Training
       d. 전환 완료 → 데이터 전송 가능
```

### Power Mode

```
Active (HS): 고속 전송 — 데이터 전송 중
Active (PWM): 저속 전송 — 저전력 유지 통신
Stall: 일시 정지 — 링크 유지, 전송 없음
Sleep: 저전력 — M-PHY RX 비활성, TX 유지
Hibernate: 최저 전력 — M-PHY 대부분 비활성, 복귀 시간 필요 (ms 단위)

전력 소비 순서: Hibernate < Sleep < Stall < Active(PWM) < Active(HS)
복귀 시간 순서: Active(HS) < Stall < Active(PWM) < Sleep < Hibernate

전환: BootROM은 보통 HS-G1에서 시작 → BL2/OS가 최대 Gear로 전환
```

---

## BootROM에서의 UFS 접근 (기존 자료 연결)

```
BootROM의 UFS 부팅 시퀀스 (soc_secure_boot_ko Unit 4와 연결):

  1. M-PHY 초기화 (캘리브레이션)
  2. UniPro Link Startup (DME_LINKSTARTUP)
  3. NOP OUT → NOP IN (디바이스 생존 확인)
  4. QUERY: bBootLunEn (Boot LU 활성화 확인)
  5. READ(Boot LU) → BL2 이미지 로드
  6. Secure Boot 서명 검증
  7. BL2 실행

  BootROM은 HS-G1 (최저 속도)로 동작:
    - 빠른 초기화 (캘리브레이션 단순)
    - 부팅 이미지 크기가 작으므로 충분
    - Gear 업은 BL2/OS가 수행
```

---

## Q&A

**Q: UFS가 eMMC보다 빠른 근본 이유는?**
> "세 가지: (1) Full-duplex — 읽기와 쓰기를 동시에 수행 가능(eMMC는 Half-duplex). (2) 명령 큐잉 — 최대 32개 명령을 동시 처리(eMMC는 1개 순차). (3) 시리얼 고속 인터페이스 — M-PHY HS-G4 기준 lane당 11.6Gbps(eMMC 병렬 버스는 400MB/s 한계). 이 세 가지가 결합되어 10배 이상의 성능 차이를 만든다."

**Q: UniPro의 역할은?**
> "UFS의 링크 계층으로, 두 가지 핵심 기능: (1) 신뢰성 — CRC-16으로 무결성 검증, NAK으로 재전송, Credit 기반 흐름 제어로 오버플로 방지. (2) 링크 관리 — DME를 통한 Gear/Lane 협상, Power Mode 전환, Link Startup 시퀀스. UPIU 패킷을 안전하게 전달하는 '파이프' 역할이다."

**Q: UFS 3.0 → 4.0의 가장 큰 변화는?**
> "두 가지: (1) 속도 — HS-G3(5.8Gbps/lane)에서 HS-G4(11.6Gbps/lane)로 2배 향상. (2) MCQ(Multi-Circular Queue) — NVMe처럼 복수의 독립 Submission/Completion Queue를 도입하여 멀티코어 환경에서의 Lock 경합을 제거하고, 큐별 코어 바인딩으로 병렬성을 극대화했다. 단순히 속도만 올린 것이 아니라 SW 인터페이스 아키텍처 자체를 혁신한 것이 핵심이다."

**Q: M-PHY HS 모드에서 CDR이 왜 중요한가?**
> "HS 모드는 별도 클럭 라인 없이 데이터에 클럭을 임베딩하여 전송한다. RX 측의 CDR 회로가 수신 데이터 에지에서 클럭을 복원해야 정확한 샘플링이 가능하다. CDR Lock이 실패하면 모든 데이터가 오류가 된다. Gear가 높을수록(G3→G4) 주파수가 높아져 CDR Lock이 까다로워지고, Eye Opening이 좁아져 정밀한 Calibration이 필수적이다."

<div class="chapter-nav">
  <a class="nav-prev" href="index.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">코스 홈</div>
  </a>
  <a class="nav-next" href="02_hci_architecture.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">UFS HCI 아키텍처</div>
  </a>
</div>
