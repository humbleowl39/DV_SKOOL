---
title: "Module 01 — UFS Protocol Stack"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Diagram** UFS 프로토콜 스택 (Application / UTP / UPIU / UniPro / M-PHY) 을 그릴 수 있다.
- **Distinguish** 각 계층의 책임과 데이터 변환 흐름 (host application → physical signal) 을 추적할 수 있다.
- **Compare** UFS 와 eMMC / SATA / NVMe 의 핵심 차이를 표로 정리할 수 있다.
- **Identify** UFS 버전 (2.x → 4.x) 진화의 핵심 변경점.
- **Trace** 4 KB READ 한 건이 application → UPIU → UniPro → M-PHY 까지 어떻게 변환되는지 추적할 수 있다.
:::
:::note[사전 지식]
- 스토리지 프로토콜 일반 (SCSI 기본, queue 모델)
- 시리얼 인터페이스 기본 (PHY, CDR 개념)
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _스마트폰 storage_ 의 _read latency_

스마트폰 OEM(주문자 상표 부착 생산 — 여기선 단말 제조사)에서 사진 앱의 read latency(읽기 요청을 보내고 데이터가 돌아오기까지의 지연)를 추적한다고 해 봅시다. 100 KB 이미지 하나를 읽으면 1 ms 가 걸리지만, 4 장을 순차로 읽으면 4 ms 가 됩니다. UFS(Universal Flash Storage — JEDEC 가 정한 모바일/서버용 플래시 스토리지 표준)는 이 문제를 UTRD(UTP Transfer Request Descriptor — SW 가 메모리에 적어 두는, 명령 한 건의 정보를 담은 기술자 구조)의 32 슬롯으로 해결합니다. 32 개 명령을 동시에 in-flight(이미 발행됐지만 아직 완료 응답이 안 온, 처리 중인 상태)로 둘 수 있기 때문에, 4 장을 병렬로 요청하면 이론상 1 ms 안에 처리됩니다.

여기서 "왜 하필 32" 인지는 HCI(Host Controller Interface — SW 드라이버와 UFS 하드웨어 사이의 표준 register/메모리 인터페이스)의 doorbell(SW 가 메모리에 명령을 적어 둔 뒤 "이제 처리하라"고 HW 에 알리는 register write 신호) 레지스터 구조에서 곧장 나옵니다. host 가 슬롯을 켜는 doorbell 레지스터(UTRLDBR, UTP Transfer Request List Door Bell Register)는 **32-bit 폭**이고, 그 **비트 하나가 슬롯 하나**에 1:1 로 대응합니다 — 비트 5 를 세우면 슬롯 5 의 명령을 시작하라는 뜻입니다. 즉 32 라는 숫자는 임의의 설계 선택이 아니라 *32-bit 레지스터의 비트 수* 가 만든 구조적 상한입니다. 이 비트=슬롯 대응은 02·03 모듈 전체에서 반복되는 핵심 골격이므로 여기서 먼저 못 박아 둡니다.

그런데 HCI 가 multi-slot doorbell 을 구현하지 않아 슬롯을 1 개만 사용하는 버그가 있다면, 4 장은 다시 순차 4 ms 로 돌아옵니다. **원인은 5 계층 중 HCI layer 의 doorbell 구현 누락**입니다. UPIU(UFS Protocol Information Unit — 명령/데이터/응답을 담는 UFS 표준 패킷)를 정확히 조립하고 UniPro(MIPI 가 정한, PHY 위에서 프레임·재전송·흐름제어를 담당하는 직렬 link 프로토콜)가 오류 없이 전송하더라도, HCI 슬롯 관리가 단일 직렬로 고정되면 그 우수성이 전혀 발휘되지 않습니다. 이것이 5 계층 _책임 분리_ 의 핵심 의미입니다. 한 계층의 결함은 다른 계층이 아무리 잘 동작해도 전체 성능을 무력화합니다.

이후 모든 UFS HCI 모듈은 **"하나의 SCSI(Small Computer System Interface — 디스크 같은 저장장치에 READ/WRITE 등을 지시하는 오래된 표준 명령 집합; UFS 는 이 명령 어휘를 재사용) 명령이 어떻게 시리얼 라인 비트로 내려가고 다시 올라오는가"** 라는 한 질문에 답을 더해 갑니다. UTRD 가 왜 32 슬롯인지, doorbell 이 왜 SW/HW 분리의 핵심인지, gear(M-PHY 의 전송 속도 단계 — 숫자가 클수록 lane 당 속도가 빠름) 변경이 왜 그렇게 까다로운지 — 모두 이 5 계층 스택이 책임을 나눠 가지기 때문입니다.

이 모듈을 건너뛰면 이후의 register 비트, UPIU 필드, error 시나리오가 **"외워야 하는 규칙"** 으로 보입니다. 반대로 5 계층을 정확히 잡고 나면, 디테일을 만날 때마다 **"이건 UTP 책임"**, **"이건 UniPro 책임"** 처럼 _어디에 속한 문제인지_ 가 자동으로 보입니다.

---

## 2. Intuition — 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**UFS protocol stack** = 국제 택배. 보내는 쪽이 박스(SCSI command)에 담아 송장(UPIU)을 붙이고, 운송회사(UniPro)가 차량(M-PHY lane)에 실어 도로(serial wire)로 전달. 각 단계마다 책임이 분리돼 있어 한 단계가 망가져도 어디서 뭐가 빠졌는지 추적 가능.
:::
### 한 장 그림 — 5 계층의 데이터 흐름

```d2
direction: down
grid-columns: 2

H_APP: "[Host] App\nREAD 4KB @LBA=0x1000"
D_PHY: "[Device] M-PHY RX"
H_UTP: "[Host] UTP / UPIU"
D_UNI: "[Device] UniPro"
H_UNI: "[Host] UniPro\nL4/L3/L2/L1.5"
D_UTP: "[Device] UTP / UPIU 디코드"
H_PHY: "[Host] M-PHY TX"
D_MEDIA: "[Device] Storage media\n(NAND read)"

H_APP -> H_UTP: "SCSI CDB\n(16B, opcode=0x28)"
H_UTP -> H_UNI: "Command UPIU"
H_UNI -> H_PHY: "DL Frame\nSOF+Hdr+UPIU+CRC+EOF"
H_PHY -> D_PHY: "TX lane"
D_PHY -> D_UNI: "M-PHY symbol\n(8b/10b or PWM)"
D_UNI -> D_UTP: "DL Frame 재조립"
D_UTP -> D_MEDIA: "SCSI 명령 실행"
```

### 왜 이 디자인인가 — Design rationale

세 가지 요구가 동시에 풀려야 했습니다.

1. **Mobile / server 양쪽에서 쓰일 고속 storage** → 직렬·full-duplex·저전력 PHY 가 필요 → M-PHY.
2. **고속 라인 위에서 안전하게** → CRC, NAK, credit-based flow control 이 link 단에 필요 → UniPro.
3. **OS / driver 가 익숙한 어휘로** → SCSI command set 을 그대로 재사용 → UTP/UPIU.

세 요구의 교집합이 바로 **SCSI 위에 UPIU 를 얹고, UPIU 를 UniPro 가 운반하고, UniPro 를 M-PHY 가 직렬화** 하는 5 계층 구조입니다. 이 분리가 _layer 단위 디버그_ 를 가능하게 만듭니다.

---

## 3. 작은 예 — 4 KB READ 한 건이 host 에서 NAND 까지

가장 단순한 시나리오. Host 가 LUN(Logical Unit Number — 한 UFS 장치 안에서 독립 디스크처럼 동작하는 저장 영역의 번호) 0, LBA(Logical Block Address — 저장 매체를 512 B 등 고정 블록으로 나눴을 때의 블록 주소) = 0x1000 에서 **4 KB (8 block × 512 B)** 를 READ 합니다. UFS 3.1, HS-G3 × 2-lane(데이터 선 한 쌍 = 1 lane; 2-lane 이면 두 쌍을 병렬로 사용), MTU(Maximum Transmission Unit — 한 프레임에 담을 수 있는 최대 바이트, 여기선 UniPro DL frame) = 256 B 가정.

```d2
shape: sequence_diagram

App
Drv: "Driver"
HCI
Dev: "UFS Device"

# Note over Drv: 2. UTRD@slot=5 작성\n+ Cmd UPIU (16B CDB)\n+ PRDT (1 entry, 4 KB)
# Note over HCI: 4. UTRD DMA fetch\n5. Cmd UPIU 조립
# Note over Dev: UTP 디코드\n8. NAND read
# Note over HCI: 10. PRDT 주소에 DMA write
# Note over HCI: 12. UTRD.OCS = SUCCESS\n13. UTRLDBR[5]=0 + IRQ
App -> Drv: "1. read(fd, buf, 4096)"
Drv -> HCI: "3. UTRLDBR |= (1<<5)\ndoorbell ring"
HCI -> Dev: "6/7. DL frame × 16\n(SOF/Hdr/UPIU/CRC-16/EOF)"
Dev -> HCI: "9. Data-In UPIU × N\n(DL frame 16 개)" { style.stroke-dash: 4 }
Dev -> HCI: "11. Response UPIU\nStatus=GOOD, Resid=0" { style.stroke-dash: 4 }
HCI -> Drv: "IRQ" { style.stroke-dash: 4 }
Drv -> App: "14. ISR → buf 반환 → app 복귀"
```

### 단계별 역할

아래 표에서 처음 등장하는 약어를 먼저 풀어 둡니다. **PRDT**(Physical Region Description Table — 데이터를 담을 메모리 버퍼들의 물리 주소·길이 목록; HCI 가 이 목록을 보고 DMA 로 데이터를 흩어 읽고/씀). **DMA**(Direct Memory Access — CPU 를 거치지 않고 하드웨어가 직접 메모리를 읽고 쓰는 방식). **OCS**(Overall Command Status — HCI 가 명령 완료 시 UTRD 에 적는 최종 성공/실패 코드). **IRQ**(Interrupt Request — HW 가 "일이 끝났다"고 CPU 에 보내는 신호) / **ISR**(Interrupt Service Routine — 그 인터럽트를 받아 처리하는 SW 함수).

| Step | 누가 | 무엇을 | 의미 (어느 계층의 책임?) |
|---|---|---|---|
| ① | App | `read(fd, buf, 4096)` | Application — POSIX/file IO |
| ② | Driver | UTRD + Cmd UPIU + PRDT 작성 | UTP — SCSI CDB → UPIU 캡슐화 |
| ③ | Driver | `UTRLDBR[5] = 1` | HCI — SW→HW doorbell 트리거 |
| ④ | HCI | UTRD 를 시스템 메모리에서 DMA fetch | HCI — register-driven descriptor pull |
| ⑤ | HCI | Cmd UPIU 를 UniPro 로 hand-off | UTP/UniPro 경계 |
| ⑥ | UniPro TX | DL frame 화 (SOF/Hdr/CRC/EOF) | UniPro DL — 무결성 + flow control |
| ⑦ | UniPro RX | DL frame 디코드, CRC 검증 | UniPro DL — frame → UPIU 재조립 |
| ⑧ | Device | NAND read 실행 | Device 내부 (spec 외) |
| ⑨ | Device | Data-In UPIU × N 송신 (256 B 단위) | UTP — multi-frame data segment |
| ⑩ | HCI | PRDT 주소로 DMA write | HCI — DMA scatter/gather |
| ⑪ | Device | Response UPIU (Status=GOOD) 송신 | UTP — completion semantics |
| ⑫ | HCI | UTRD 의 OCS 필드를 SUCCESS 로 갱신 | HCI — status writeback |
| ⑬ | HCI | UTRLDBR slot bit clear + IS[UTRCS] set | HCI — completion notify |
| ⑭ | ISR | App 으로 buffer 반환 | Driver — async completion |

```c
// 실제 driver code 의 골격 (Linux ufs core 의 스타일을 단순화)
struct utp_transfer_req_desc utrd = {
    .header.dword_0 = UTP_CMD_TYPE_SCSI | UTP_DD_DEV_TO_HOST,  // ②
    .response_upiu_offset = sizeof(struct utp_upiu_req) / 4,
    .prd_table_offset    = (sizeof(req) + sizeof(rsp)) / 4,
    .prd_table_length    = 1,
    .ocs                 = OCS_INVALID,
};
build_read10_cdb(&cmd_upiu, lba=0x1000, len=8);   // 8 blocks of 512B
prdt[0].data_base_addr = virt_to_phys(buf);
prdt[0].data_byte_count = 4096 - 1;               // 0-based
hci_writel(BIT(5), UTRLDBR);                      // ③ doorbell
wait_for_completion(&done);                       // ⑭
```

:::note[여기서 잡아야 할 두 가지]
**(1) 5 계층은 _책임 분리_ 다.** 같은 4 KB 가 SCSI CDB → UPIU → DL frame × 16 → M-PHY symbol stream 으로 변환되는데, 각 단계가 자기 layer 의 무결성/flow control 만 책임진다. 한 layer 의 실패 = 그 layer 의 어휘로 진단. <br>
**(2) Doorbell + UTRD + IRQ 는 한 세트** 다. SW 가 메모리에 미리 다 적어두고 doorbell 한 번으로 시작, 완료는 IRQ + UTRLDBR clear 로 알림 — 이 세 점만 잡으면 어떤 명령이든 동일 패턴.
:::
---

## 4. 일반화 — 3 계층과 책임 분리

### 4.1 책임 분리 원칙

UFS 는 IB(InfiniBand — 고성능 서버/클러스터용 네트워크 표준) / NVMe(Non-Volatile Memory Express — PCIe 위에서 SSD 를 다루는 고속 스토리지 프로토콜)처럼 자체 5 계층을 정의하지만, 가장 거칠게 보면 **3 계층** 으로 압축 가능합니다.

| 계층 | 정의 (ISO 11179) | 핵심 책임 | 데이터 단위 |
|------|------------------|-----------|------------|
| **UTP / Application** | UFS 가 사용하는 transport-level 명령 / 응답 / 데이터 단위. SCSI CDB 를 캡슐화. | Command set, queueing, task management | UPIU |
| **UniPro / Link** | MIPI 가 정의한 PHY-agnostic 직렬 link protocol. CRC + flow control + DME. | Link reliability, frame, power mode | DL frame |
| **M-PHY / Physical** | MIPI 가 정의한 저전력 시리얼 PHY. HS / PWM / Hibernate gear 보유. | Bit serialization, CDR, calibration | Symbol |

```d2
direction: down

APP: "**UFS Application Layer (UTP — UFS Transport Protocol)**\n· SCSI 명령 세트 (READ / WRITE / QUERY)\n· UPIU (UFS Protocol Information Unit) 패킷 구성\n· Task Management (Abort, LUN Reset 등)"
UNI: "**UniPro (Unified Protocol) — Link Layer**\n· L4: DME (Device Management Entity)\n· L3: N-Layer (Network, 보통 point-to-point)\n· L2: DL (Data Link — CRC, ACK/NAK, Flow Control)\n· L1.5: PHY Adapter (인터페이스 어댑터)"
PHY: "**M-PHY (MIPI Physical Layer)**\n· HS (High Speed) Gear 1~4: 1.46~11.6 Gbps/lane\n· PWM (저전력 모드): Gear 1~7\n· 1~2 Lane (데이터 레인 수)\n· CDR, Calibration, Power Mode 전환"
APP -> UNI: "UPIU"
UNI -> PHY: "시리얼 데이터"
```

### 4.2 변환 단위가 layer 마다 다르다

| Layer | 변환 입력 | 변환 출력 | 변환 책임 |
|-------|----------|----------|----------|
| Application | 파일 IO | SCSI CDB | OS 에 의존 |
| UTP | SCSI CDB | UPIU (12B header + payload) | HCI 가 자동화 |
| UniPro DL | UPIU | DL frame (SOF + Hdr + Data + CRC-16 + EOF) | UniPro IP |
| L1.5 PHY Adapter | DL frame | M-PHY symbol stream | UniPro/M-PHY 경계 |
| M-PHY | symbol | bit on wire | 아날로그 + 디지털 |

이 표는 검증의 **monitor / scoreboard 위치 결정** 에도 그대로 매핑됩니다 — 어떤 계층의 변환을 검증하느냐에 따라 monitor 가 어디에 붙어야 하는지 정해집니다.

### 4.3 다른 storage 와의 비교

| 항목 | UFS 3.1/4.0 | eMMC 5.1 | NVMe |
|------|------------|----------|------|
| Command set | SCSI | MMC | NVMe (자체) |
| Transport | UPIU | MMC bus protocol | NVMe submission queue |
| Physical | M-PHY (직렬) | 8-bit 병렬 | PCIe |
| Duplex | **Full-duplex** | Half-duplex | Full-duplex |
| Queue depth | **32 (SDB) / 多 (MCQ)** | 1 | 64 K queue × 64 K depth |
| 용도 | mobile + server | 중급 mobile | server + workstation |

핵심 차이: UFS 는 **SCSI 호환성** 과 **mobile-grade 저전력** 을 동시에 잡기 위해 직렬 PHY + UPIU 캡슐화를 선택했습니다.

---

## 5. 디테일 — UPIU / UniPro / M-PHY / 버전 진화

### 5.1 UPIU 구조

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

### 5.2 UPIU 유형

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

### 5.3 UFS 버전 진화

| 버전 | 연도 | 최대 속도 | 핵심 추가 기능 |
|------|------|----------|--------------|
| UFS 2.0 | 2013 | 1.2 GB/s (HS-G2×2) | 기본 SCSI 명령, 32 슬롯 큐잉 |
| UFS 2.1 | 2016 | 1.2 GB/s | Crypto 엔진 (Inline Encryption), Device Health 리포트 |
| UFS 3.0 | 2018 | 2.9 GB/s (HS-G3×2) | HS-G3, 2-Lane 필수, Write Booster |
| UFS 3.1 | 2020 | 2.9 GB/s | Write Booster 강화, Host Performance Booster (HPB), DeepSleep |
| UFS 4.0 | 2022 | 4.6 GB/s (HS-G4×2) | HS-G4, **MCQ** (Multi-Circular Queue), Advanced RPMB |
| UFS 5.0 | 2024 | 9.2 GB/s (HS-G5×2) | HS-G5, 향상된 전력 관리 |

아래 상세 설명에 나오는 NAND 저장 용어를 먼저 풀어 둡니다. **SLC/TLC/QLC**는 NAND 셀 하나에 몇 비트를 저장하느냐의 구분으로, SLC(1비트)는 빠르고 수명이 길지만 비싸고, TLC(3비트)·QLC(4비트)로 갈수록 용량당 가격은 싸지지만 쓰기가 느려집니다. **L2P**(Logical-to-Physical — host 가 쓰는 논리 주소를 NAND 의 실제 물리 위치로 바꾸는 매핑 테이블). **AES-256-XTS**는 저장장치 암호화에 쓰는 표준 블록 암호 방식입니다.

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
    → Module 02 에서 상세 설명
```

### 5.4 UFS vs eMMC

| 항목 | UFS 3.1/4.0 | eMMC 5.1 |
|------|------------|----------|
| 인터페이스 | 시리얼 (M-PHY) | 병렬 (8-bit bus) |
| 듀플렉스 | **Full-duplex** (동시 R/W) | Half-duplex |
| 최대 속도 | 2.9 GB/s (UFS 3.1) / 4.2 GB/s (4.0) | 400 MB/s |
| 명령 큐잉 | **최대 32개** (MCQ: 최대 64+) | 1개 (순차) |
| 프로토콜 스택 | SCSI + UniPro + M-PHY | MMC 명령 |
| 전력 관리 | HS/PWM Gear + Hibernate | Sleep/Standby |
| 용도 | 플래그십 모바일, 서버 | 중급 모바일, IoT |

**핵심 차이**: 명령 큐잉과 Full-duplex 가 UFS 의 압도적 성능 차이를 만든다. eMMC 는 명령 하나를 보내고 응답을 기다려야 하지만, UFS 는 32 개 명령을 동시에 처리할 수 있다.

Full-duplex 가 성능에 기여하는 메커니즘은 *레인 분리* 에 있다. UFS 의 M-PHY 는 송신(TX)과 수신(RX) 레인이 물리적으로 따로 있어, 같은 순간에 양방향이 동시에 흐를 수 있다. 그래서 device 가 이전 READ 의 응답 데이터를 RX 레인으로 올려보내는 *동안*, host 는 다음 WRITE 명령을 TX 레인으로 내려보낼 수 있다 — 두 방향이 서로를 기다리지 않는다. 반면 eMMC 는 half-duplex 라 같은 선을 방향만 바꿔 번갈아 쓰므로, read 응답이 끝나야 다음 명령을 보낼 수 있어 방향 전환마다 라인이 한쪽으로만 쓰인다. 이 동시성이 큐잉과 곱해져 UFS 의 성능 격차를 만든다.

### 5.5 UniPro DL Layer — 프레임과 Flow Control

UniPro DL(Data Link) 레이어는 UPIU 를 물리 라인에 내려보내기 전에 SOF(Start of Frame — 프레임 시작 표시)·헤더·CRC(Cyclic Redundancy Check — 비트가 깨졌는지 검출하는 체크섬)·EOF(End of Frame — 프레임 끝 표시)로 감싸 무결성을 확보하고, credit(수신측이 "이만큼 받을 수 있다"고 미리 발행하는 전송 허가량) 기반 흐름 제어로 수신 버퍼 초과를 막습니다.

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

왜 *credit* 모델일까요? 고속 직렬 링크에서는 데이터가 한번 라인에 올라가면 RX 의 수신 버퍼에 곧장 쌓입니다. 만약 TX 가 RX 버퍼 상태를 모른 채 계속 보내다 버퍼가 가득 차면, 넘치는 프레임은 그냥 *버려지고*(overrun) 재전송 비용이 발생합니다. 게다가 고속에서는 "버퍼가 찼으니 멈춰라" 라는 사후 신호가 도착할 때쯤이면 이미 여러 프레임이 날아간 뒤입니다. credit 은 이 문제를 *사전 허가* 로 뒤집습니다 — RX 가 받을 수 있는 만큼만 미리 허락(credit)을 주고, TX 는 보유 credit 안에서만 전송합니다. 즉 버퍼 오버런을 *보내기 전에* 원천 차단하는 것이 credit 모델을 쓰는 근본 이유입니다.

TX 는 수신 측이 발행한 크레딧(AFC) 범위 안에서만 프레임을 내보낼 수 있습니다. RX 가 프레임을 수신하고 버퍼를 소비한 뒤 AFC 프레임으로 크레딧을 돌려주면 TX 는 그 양만큼 추가 전송 자격을 얻습니다. CRC 에러가 검출되면 RX 는 NAK(Negative Acknowledgement — "제대로 못 받았으니 다시 보내라"는 부정 응답)을 보내고, TX 는 해당 프레임을 자동으로 재전송합니다 — 이 재전송은 HCI 나 driver 에 노출되지 않는 link-level 투명 처리입니다.

```
Credit 기반 흐름 제어:

  TX 측: 잔여 크레딧 확인 → 크레딧 있으면 전송
  RX 측: 프레임 수신 → 크레딧 반환 (AFC — Ack Flow Control)

  AFC Frame:
    RX → TX: "크레딧 N개 반환" → TX가 N개 더 전송 가능

  NAK:
    CRC 에러 → RX가 NAK → TX가 재전송
```

### 5.6 UniPro L4 / L3 / L1.5

이 절의 핵심은 **DME**(Device Management Entity — UniPro 스택을 켜고 끄고 속성을 읽고/쓰는 관리 엔티티)입니다. host 는 **UIC command**(UFS Interconnect command — host 가 UniPro/M-PHY 동작을 제어하려고 보내는 표준 명령; `DME_GET`/`DME_SET`/`DME_LINKSTARTUP` 등)로 DME 에 접근합니다. **MIB**(Management Information Base — UniPro 가 읽고/쓰는 설정 속성들의 모음; 각 속성이 `PA_TxGear` 같은 이름을 가짐)는 그 속성 저장소입니다.

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

```
UFS에서 L3(Network Layer)는 단순화:
  - Point-to-point 연결 (Host ↔ Device 1:1)
  - 라우팅 불필요 → DeviceID는 항상 0
  - 멀티디바이스 UFS는 별도 링크 (버스가 아님)

  L3 헤더: Src DeviceID + Dst DeviceID (각 1 byte)
  → UFS에서는 사실상 고정값 (0x00 ↔ 0x01)
```

```
L1.5 = UniPro와 M-PHY 사이의 인터페이스 어댑터
```

L1.5 는 UniPro 의 DL 프레임과 M-PHY 의 심볼 스트림 사이를 중개하는 얇은 어댑터 계층입니다. UniPro 는 "이 데이터를 Gear 3, 2-Lane 으로 보내라" 는 의미의 지시를 내리고, L1.5 는 그 지시를 M-PHY 가 이해하는 아날로그 파라미터와 심볼 인코딩 시퀀스로 변환합니다. 2-Lane 모드에서 레인 간 도착 타이밍이 미세하게 벌어지는 skew 도 이 계층이 보정합니다.

```
  DL Frame → L1.5가 Symbol 인코딩 → M-PHY TX로 전달
  M-PHY RX → L1.5가 Symbol 디코딩 → DL Frame으로 재구성
```

### 5.7 M-PHY — Gear 와 Calibration

여기서 **Calibration**(보정 — 아날로그 회로 파라미터를 실제 칩·전압·온도에 맞춰 최적값으로 조정하는 과정)과 **Hibernate**(동면 — M-PHY 대부분을 끈 최저 전력 상태로, 복귀에 ms 단위 시간이 듦)가 처음 본격적으로 등장합니다. 아래 코드 설명에 나오는 **CDR**(Clock and Data Recovery — 별도 클럭 선 없이 데이터 신호 자체에서 클럭을 복원하는 회로)와 **PVT**(Process/Voltage/Temperature — 칩마다·전압마다·온도마다 달라지는 동작 조건)도 함께 짚어 둡니다.

| Gear | 속도/Lane | 2-Lane 속도 | UFS 버전 |
|------|----------|------------|---------|
| HS-G1 | 1.46 Gbps | 2.9 Gbps | UFS 2.0 |
| HS-G2 | 2.9 Gbps | 5.8 Gbps | UFS 2.1 |
| HS-G3 | 5.8 Gbps | 11.6 Gbps | UFS 3.0/3.1 |
| HS-G4 | 11.6 Gbps | 23.2 Gbps | UFS 4.0 |
| HS-G5 | 23.2 Gbps | 46.4 Gbps | UFS 5.0 (예정) |

```
Line coding (왜 8b/10b · PWM 인가):
  M-PHY 는 클럭 신호를 별도 선으로 보내지 않고 데이터 선 하나에
  클럭을 "섞어" 보낸다 (embedded clock). 그래서 RX 가 데이터 자체에서
  클럭을 복원(CDR)할 수 있으려면, 데이터에 충분한 0↔1 전이(edge)가
  주기적으로 나타나야 한다.
  - 만약 0 이나 1 이 길게 이어지면 edge 가 없어 CDR 이 클럭을 놓친다.
  - 8b/10b (HS 모드): 8비트를 10비트로 인코딩해 전이를 보장하고,
    동시에 0 과 1 의 개수를 맞춰 DC balance 를 유지한다 (라인 평균
    전압이 한쪽으로 쏠리지 않게 → AC 결합·수신단 안정).
  - PWM (저속 모드): 비트를 펄스 폭으로 표현해 매 비트마다 전이가
    생기므로, 느린 속도에서도 클럭 복원이 가능하다.
  요약: 라인 코딩은 "클럭 복원용 전이 보장 + DC balance" 를 위해 존재한다.

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

### 5.8 BootROM 의 UFS 부팅 시퀀스

**BootROM**(칩 안에 굽혀 있는, 전원이 켜지면 가장 먼저 실행되는 변경 불가 부팅 코드)은 가장 먼저 UFS 에서 다음 단계 부트로더 **BL2**(2nd-stage Boot Loader — BootROM 이 불러오는 후속 부팅 이미지)를 읽어 와야 합니다. 아래는 그 과정에서 등장하는 **QUERY**(host 가 device 의 설정 값을 읽고/쓰는 UFS 명령; 예: `bBootLunEn` 같은 부팅 관련 속성)와 **Boot LU**(부팅 이미지가 들어 있는 전용 Logical Unit)의 흐름입니다.

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

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'UFS = SCSI 의 단순 변형']
**실제**: UFS 는 SCSI command set 만 _재사용_ 하고, 그 위에 UPIU 캡슐화 + UniPro link + M-PHY PHY 라는 독립된 계층을 쌓았습니다. SCSI 호환은 driver 가 같은 CDB 어휘를 쓸 수 있다는 뜻이지, **wire protocol** 은 전혀 다릅니다. UPIU header / DL frame / M-PHY symbol — 어떤 것도 SCSI spec 에 없습니다.<br>
**왜 헷갈리는가**: SCSI 의 친숙함 때문에 "새 구현 = 단순 wrapping" 으로 보고 layer 의 의미를 흘려듣는 경향.
:::
:::danger[❓ 오해 2 — 'UFS = NAND flash 인터페이스다']
**실제**: UFS 는 _storage protocol_ 이고 NAND 는 그 아래 media 입니다. UFS spec 자체에 NAND 는 등장하지 않습니다 — eMMC 와 UFS 가 모두 NAND 를 쓰지만, UFS 가 정의하는 건 host ↔ device controller 간 약속뿐. NAND 의 program/erase 주기, GC(Garbage Collection — 흩어진 유효 데이터를 모아 빈 블록을 회수하는 정리 작업), wear-leveling(쓰기를 여러 블록에 고르게 분산해 특정 셀만 빨리 닳는 것을 막는 기법)은 device controller 내부 일.<br>
**왜 헷갈리는가**: "스마트폰 storage = NAND" 라는 시장 인식.
:::
:::danger[❓ 오해 3 — 'UniPro DL CRC 가 깨지면 host 가 바로 보임']
**실제**: UniPro DL 의 CRC 는 link 단에서 처리됩니다 — RX 가 CRC error 를 보면 NAK → TX 가 재전송. 정상 시나리오에서는 host driver/HCI 에 노출되지 않습니다 (transparent retry). HCI 가 보는 건 _재전송 후에도 실패한 link error_ 뿐.<br>
**왜 헷갈리는가**: "CRC 에러 = 명령 실패" 라는 일반 직관.
:::
:::danger[❓ 오해 4 — 'HS-G3 → HS-G4 는 그냥 register write']
**실제**: Gear 변경은 **DME_SET 시퀀스 + PA_PWRMode 트리거 + M-PHY recalibration** 3 단계입니다. 그 사이에 in-flight UPIU 가 남아 있으면 새 gear 의 라인 코딩으로 잘못 디코딩되어 CRC 폭증. UTRLDBR 이 0 이고 RTT(Ready To Transfer UPIU — device 가 host 에게 "write 데이터를 보낼 준비가 됐다"고 알리는 UPIU)/Data-Out 이 모두 drain(처리 중인 것들을 모두 빼내 비움)된 상태에서만 수행해야 합니다.<br>
**왜 헷갈리는가**: 다른 register write 처럼 보임.
:::
:::danger[❓ 오해 5 — 'BootROM 은 빠른 gear 로 부팅한다']
**실제**: 거의 모든 BootROM 은 **HS-G1 (또는 PWM)** 으로 시작합니다. 캘리브레이션이 단순하고, BL2 이미지가 작아 고속이 불필요. Gear 업은 BL2 이후 OS / driver 가 수행.<br>
**왜 헷갈리는가**: "빠를수록 좋다" 라는 직관.
:::
### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Link Startup 실패 (DME_LINKSTARTUP timeout) | M-PHY calibration 미완료 / lane 수 mismatch | UICCMDARG 의 에러 코드, PA_AvailTx/RxDataLanes |
| Cmd UPIU 에서 CDB 가 깨짐 | UPIU header offset 오해 (12B vs 32B) | UPIU header 12B + Cmd-specific 16B 위치 |
| Data-In UPIU 가 일부 누락 | DL frame CRC 재전송 도중 host timeout | UniPro CRC error counter, NAK 재전송 횟수 |
| Gear 변경 후 CRC 에러 폭증 | Gear 전환 중 in-flight UPIU 잔존 | UTRLDBR 가 0 이고 RTT 모두 종료됐는지 |
| NOP OUT 후 NOP IN 안 옴 | UniPro link 는 up 인데 UTP 상위가 reset 안 됨 | NOP 의 Task Tag, Response Code |
| Boot LU READ 가 0 byte 만 받음 | bBootLunEn 미설정 / Boot LU = B 인데 A 로 시도 | Query Read Attribute (bBootLunEn) |
| HS-G4 협상이 항상 G3 로 떨어짐 | PA_HSSeries 또는 PA_TxGear 양측 불일치 | DME_PEER_GET 으로 device side 의 supported gear |
| Hibernate exit 후 첫 명령 fail | M-PHY 재캘리브레이션 미완 상태에서 doorbell | DME_HIBERNATE_EXIT 완료 IRQ 대기했는지 |

이 체크리스트의 모든 항목은 **"어느 layer 의 책임인가?"** 로 분류 가능 — UTP / UniPro / M-PHY 중 어디에 속하는지 답할 수 있어야 효율적인 디버그가 됩니다.

---

## 7. 핵심 정리 (Key Takeaways)

- **5 계층** (Application → UTP → UPIU → UniPro → M-PHY) 은 _책임 분리_ 의 모델. 각 layer 가 자기 무결성/flow control 만 책임.
- **UPIU** 가 UFS 의 통신 단위 — SCSI CDB 를 캡슐화하고 Task Tag 로 32 명령 식별.
- **UniPro DL** 은 CRC + AFC + NAK 재전송으로 link 무결성 책임. RoCEv2 의 PFC, IB 의 credit FC 와 같은 역할.
- **M-PHY** 는 HS / PWM / Hibernate gear 와 CDR + Calibration. Gear 변경은 단순 register write 가 아니라 시퀀스.
- **UFS vs eMMC**: full-duplex + 32 큐잉 + 시리얼 고속 = 10× 이상 성능. SCSI 호환이 driver 재사용 가치.
- **버전 진화**: 2.x (HS-G2) → 3.x (HS-G3 + WB + HPB) → 4.0 (HS-G4 + MCQ) → 5.0 (HS-G5).

:::caution[실무 주의점 — HS-Gear 전환 중 in-flight UPIU 손실]
**현상**: Gear 변경 직후 CRC 에러가 폭증하면서 다수 명령이 retry/abort 로 빠진다.

**원인**: HS-Gear 전환 시 PHY recalibration 동안 in-flight 상태였던 UPIU 가 drain 되지 않아, 새 Gear 의 라인 코딩으로 잘못 디코딩된다.

**점검 포인트**: DME_SET(PA_PWRMode) 발행 전 UTRLDBR 이 0 인지, RTT/Data-Out 흐름이 모두 종료됐는지 sequence-level 에서 확인.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — 5 계층 분류 (Bloom: Apply)]
`LU=0 의 sense data` 가 wrong. 어느 계층 의심?

<details>
<summary>정답</summary>

**UTP (Application)** - SCSI Logical Unit / sense response 생성.

다른 가능성:
- UPIU header field 인코딩 → UTP transport.
- UniPro CRC → 안 잡힘 (전체 transfer 통과).

Sense data 는 _SCSI 응답_ 의 일부 → UTP 의 application 모듈이 주된 의심.

</details>
:::
:::tip[🤔 Q2 — Gear 전환 race (Bloom: Analyze)]
HS-Gear 변경 시 _in-flight UPIU loss_. Drain 시퀀스?

<details>
<summary>정답</summary>

1. **Quiesce SW**: 새 command issue 정지.
2. **Wait in-flight**: UTRLDBR 모니터 → 0 까지 wait.
3. **Drain link**: RTT/Data-Out 의 _residual buffer_ flush.
4. **DME_SET**: Gear 변경 명령 발행.
5. **PHY recal**: 새 Gear 로 PLL/CDR 재training.
6. **Resume**: SW restart.

각 step 사이 SVA(SystemVerilog Assertion — 신호가 지켜야 할 조건을 시뮬레이션 중 자동 검사하는 단언문)로 invariant(항상 참이어야 하는 불변 조건)를 강제.

</details>
:::
### 7.2 출처

**External**
- JEDEC JESD220 *UFS Specification*
- MIPI Alliance *UniPro Specification*

---

## 다음 모듈

→ [Module 02 — HCI Architecture](../02_hci_architecture/): UFS 5 계층 위에 host controller (HCI) 가 register / UTRD / doorbell / interrupt 로 어떤 SW 인터페이스를 제공하는지.

[퀴즈 풀어보기 →](../quiz/01_ufs_protocol_stack_quiz/)

