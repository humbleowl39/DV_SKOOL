# Ethernet & DCMAC — 개요 및 컨셉 맵

## 학습 플랜
- **레벨**: Intermediate (DCMAC 서브시스템 E2E 검증 Lead 경험 기반)
- **목표**: Ethernet 프레임 구조와 DCMAC 아키텍처를 설명하고, DV 검증 전략을 논리적으로 전개할 수 있는 수준

## 핵심 용어집 (Glossary)

### Ethernet 계층

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **MAC** | Media Access Control | L2 계층. 프레임 생성, FCS 계산/검증, 흐름 제어 담당 |
| **PCS** | Physical Coding Sublayer | 64b/66b 인코딩, Scrambling, Lane Alignment |
| **PMA** | Physical Medium Attachment | SerDes, CDR (Clock Data Recovery) |
| **PMD** | Physical Medium Dependent | 광모듈, 전기 인터페이스 |
| **DCMAC** | Dual Channel MAC | AMD(Xilinx)의 100/200/400GbE MAC IP |

### 프레임 구조

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **SFD** | Start Frame Delimiter | 프레임 시작 표시 (10101011) |
| **FCS** | Frame Check Sequence | CRC-32 체크섬으로 에러 검출 |
| **IFG** | Inter-Frame Gap | 프레임 간 최소 간격 (12B = 96 bit time) |
| **MTU** | Maximum Transmission Unit | 최대 프레임 크기 (표준:1518B, Jumbo:9022B) |
| **VLAN** | Virtual LAN | 802.1Q 가상 LAN 태그로 트래픽 분류 |
| **PFC** | Priority-based Flow Control | 802.1Qbb 우선순위별 개별 흐름 제어 |

### 인코딩 & FEC

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **64b/66b** | — | 64비트 데이터 + 2비트 Sync Header (오버헤드 ~3%) |
| **RS-FEC** | Reed-Solomon FEC | 전방 에러 정정 코드 (100G+ 필수) |
| **AM** | Alignment Marker | 다중 레인 간 Skew 보정용 주기적 마커 |
| **SerDes** | Serializer/Deserializer | 병렬↔직렬 변환 (고속 전송의 핵심) |

### MII 인터페이스

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **XGMII** | 10G MII | 10GbE용 (32-bit DDR, 156.25MHz) |
| **CGMII** | 100G MII | 100GbE용 (256-bit, 390.625MHz) |
| **Segmented IF** | — | 100G+에서 한 사이클에 다중 프레임 세그먼트 처리 |

### AXI-Stream 연동

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **AXI-S** | AXI-Stream | 스트리밍 데이터 전송 프로토콜 (TOE↔DCMAC) |
| **tdata/tvalid/tready** | — | 데이터/유효/준비 핸드셰이크 신호 |
| **tlast/tkeep** | — | 프레임 종료 표시 / 바이트 유효 마스크 |
| **RMON** | Remote Monitoring | 통계 카운터 (tx/rx frames, FCS errors 등) |
| **PTP** | Precision Time Protocol | IEEE 1588 정밀 타임스탬프 |
| **TOE** | TCP/IP Offload Engine | TCP 처리를 HW로 오프로드하는 엔진 |

---

## 컨셉 맵

```
        +-----------------+
        | Upper Layer     |
        | (TOE / IP)      |
        +--------+--------+
                 |  AXI-Stream
                 v
        +--------+--------+
        |     DCMAC       |
        |  (Ethernet MAC) |
        |                 |
        | - Frame 생성    |
        | - FCS 계산/검증 |
        | - Flow Control  |
        | - Rate Adapt    |
        +--------+--------+
                 |  PCS/PMA
                 v
        +--------+--------+
        |   Ethernet PHY  |
        | (SerDes, Optic)  |
        +-----------------+
                 |
            Ethernet Link
         (100G/200G/400G)
```

## 학습 단위 (Units)

| # | 단위 | 핵심 질문 |
|---|------|----------|
| 1 | **Ethernet 기본 + 프레임 구조** | Ethernet 프레임은 어떻게 구성되고, 각 필드의 역할은? |
| 2 | **DCMAC 아키텍처** | AMD DCMAC은 내부적으로 어떻게 동작하고, 인터페이스는? |
| 3 | **DCMAC DV 검증 전략** | UVM으로 DCMAC 서브시스템을 어떻게 검증하는가? |

## 이력서 연결

| 이력서 항목 | 관련 Unit | 면접 시 활용 |
|------------|----------|-------------|
| DCMAC 서브시스템 E2E 검증 Lead | Unit 2, 3 | 환경 아키텍처 + 검증 전략 |
| TOE ↔ DCMAC 연동 | Unit 2 | AXI-S 인터페이스 검증 |
| UVM 환경 from scratch | Unit 3 | 환경 설계 경험 |
