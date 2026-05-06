# Unit 2: DCMAC 아키텍처

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

## 핵심 개념
**DCMAC = AMD(Xilinx)의 100/200/400GbE 하드 IP MAC. FPGA/ASIC에 통합되어 라인 레이트 Ethernet 프레임 처리를 제공. 상위 계층(TOE, IP)과 AXI-Stream으로, 하위 계층(PCS/PHY)과 Segmented 인터페이스로 연결.**

---

## DCMAC 블록 다이어그램

```
+------------------------------------------------------------------+
|                          DCMAC IP                                 |
|                                                                   |
|  User Side (AXI-Stream)              Line Side (Segmented IF)     |
|                                                                   |
|  +----------+    +-----------+    +----------+    +----------+    |
|  | AXI-S    | →  | TX MAC    | →  | TX PCS   | →  | GT/SerDes| → |
|  | TX IF    |    | Engine    |    | Encoder  |    | TX       |   |
|  | (tdata,  |    |           |    | 64b/66b  |    |          |   |
|  |  tvalid, |    | - Preamble|    | Scramble |    |          |   |
|  |  tready, |    | - FCS Gen |    | RS-FEC   |    |          |   |
|  |  tlast,  |    | - Pad     |    | Lane Dist|    |          |   |
|  |  tkeep)  |    | - IFG     |    |          |    |          |   |
|  +----------+    +-----------+    +----------+    +----------+    |
|                                                                   |
|  +----------+    +-----------+    +----------+    +----------+    |
|  | AXI-S    | ←  | RX MAC    | ←  | RX PCS   | ←  | GT/SerDes| ← |
|  | RX IF    |    | Engine    |    | Decoder  |    | RX       |   |
|  |          |    |           |    | Descramb |    |          |   |
|  |          |    | - FCS Chk |    | RS-FEC   |    |          |   |
|  |          |    | - Filter  |    | Align    |    |          |   |
|  |          |    | - Stat    |    | Deskew   |    |          |   |
|  +----------+    +-----------+    +----------+    +----------+    |
|                                                                   |
|  +------------------------------------------------------------+  |
|  | Configuration / Status Registers (AXI-Lite)                |  |
|  | - MAC 주소 설정, 모드 설정, 통계 카운터, 에러 상태          |  |
|  | - RS-FEC 설정, PTP 타임스탬프, Flow Control 설정            |  |
|  +------------------------------------------------------------+  |
|                                                                   |
|  +------------------------------------------------------------+  |
|  | Flow Control Engine          | PTP/1588 Engine             |  |
|  | - Pause Frame 생성/처리      | - TX Timestamp Capture      |  |
|  | - PFC (Priority Flow Ctrl)   | - RX Timestamp Capture      |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

---

## Multi-Port 아키텍처 및 속도 모드

DCMAC은 단일 IP 블록으로 다양한 속도 구성을 지원한다.

```
400GbE (1×400G):
  +----------------------------------------------------------+
  |                    DCMAC (Single Port)                    |
  |  Port 0: 400G                                            |
  |  AXI-S: 1개 (1024-bit+)                                  |
  |  SerDes: 8 × 53.125G (PAM4) 또는 4 × 106.25G            |
  +----------------------------------------------------------+

200GbE (2×200G):
  +----------------------------------------------------------+
  |                    DCMAC (Dual Port)                      |
  |  Port 0: 200G    |    Port 1: 200G                       |
  |  AXI-S: 각각 1개  |    AXI-S: 각각 1개                    |
  |  SerDes: 4레인    |    SerDes: 4레인                      |
  +----------------------------------------------------------+

100GbE (4×100G):
  +----------------------------------------------------------+
  |                    DCMAC (Quad Port)                      |
  |  Port 0 | Port 1 | Port 2 | Port 3                      |
  |  100G   | 100G   | 100G   | 100G                        |
  |  각각 독립 AXI-S + 독립 SerDes 2레인                      |
  +----------------------------------------------------------+

Mixed Mode (예: 1×200G + 2×100G):
  포트 매핑은 레지스터 설정으로 구성
  → 하나의 DCMAC IP로 유연한 배치 가능
```

### 속도 모드별 인터페이스 매핑

| 모드 | 포트 수 | AXI-S 폭 | SerDes 레인 | 레인 속도 |
|------|--------|----------|------------|----------|
| 1×400G | 1 | 1024-bit+ | 8 (또는 4 PAM4) | 53.125G / 106.25G |
| 2×200G | 2 | 각 512-bit | 각 4레인 | 53.125G |
| 4×100G | 4 | 각 512-bit | 각 2레인 | 53.125G |
| Mixed | 가변 | 포트별 | 포트별 | 53.125G |

**DV 관점**: 각 속도 모드 전환 시 포트 매핑, AXI-S 연결, SerDes 할당이 올바른지 검증 필요. 특히 런타임 모드 전환 없이 리셋 후 재설정하는 구조인지 확인.

---

## AXI-Stream 인터페이스 (User Side)

### TX AXI-Stream (사용자 → DCMAC)

```
신호:
  tx_axis_tdata   [511:0]  // 512-bit 데이터 (100G 기준)
  tx_axis_tvalid            // 데이터 유효
  tx_axis_tready            // DCMAC 수신 준비
  tx_axis_tlast             // 프레임 마지막 beat
  tx_axis_tkeep   [63:0]   // 바이트 유효 마스크 (마지막 beat)
  tx_axis_tuser   [N:0]    // 사이드밴드 (에러, VLAN 등)

동작:
  사용자가 Ethernet Payload(Dst MAC ~ Payload)를 전달
  → DCMAC이 Preamble, SFD, FCS, IFG를 자동 추가
  → 완전한 Ethernet Frame으로 변환하여 PCS로 전달
```

### RX AXI-Stream (DCMAC → 사용자)

```
신호:
  rx_axis_tdata   [511:0]
  rx_axis_tvalid
  rx_axis_tlast
  rx_axis_tkeep   [63:0]
  rx_axis_tuser   [N:0]   // FCS 결과(good/bad), 에러 플래그

동작:
  DCMAC이 PCS에서 Ethernet Frame 수신
  → Preamble/SFD 제거, FCS 검증
  → Payload(Dst MAC ~ Payload)를 사용자에게 전달
  → tuser에 FCS 결과(good/bad) 표시
```

### tuser 필드 상세

AXI-S tuser는 사이드밴드 정보를 전달한다. DCMAC의 구체적 비트 할당:

```
TX tuser (사용자 → DCMAC):
  bit 0:     tx_poison — 이 프레임에 의도적으로 bad FCS 생성 요청
  bit 1:     tx_preamble_en — Custom Preamble 사용 (1=사용자 Preamble, 0=자동)
  [기타]:    구현에 따라 VLAN 처리 힌트 등 확장 가능

RX tuser (DCMAC → 사용자):
  bit 0:     rx_bad_fcs — FCS 검증 실패 (1=bad)
  bit 1:     rx_bad_frame — 기타 프레임 에러 (Runt, Oversize, Bad SFD 등)
  bit 2:     rx_vlan_tagged — VLAN 태그 포함 여부
  [기타]:    rx_timestamp_valid, rx_port_id 등 확장 필드

DV 관점:
  - TX에서 tx_poison=1 설정 시 실제로 bad FCS가 생성되는지 확인
  - RX에서 에러 유형별 tuser 비트가 정확히 설정되는지 확인
  - tuser 비트 조합 (예: bad_fcs + vlan_tagged 동시) 검증
```

### 데이터 폭과 속도의 관계

| Ethernet 속도 | AXI-S 데이터 폭 | 클럭 | 이유 |
|--------------|-----------------|------|------|
| 100 Gbps | 512-bit (64B) | ~322 MHz | 100G / 512bit = ~195M beat/s |
| 200 Gbps | 512-bit × 2 또는 1024-bit | ~322 MHz | 대역폭 2배 |
| 400 Gbps | 1024-bit 이상 | ~322 MHz+ | 대역폭 4배 |

**핵심**: 라인 레이트를 유지하려면 AXI-S 폭 × 클럭 ≥ Ethernet 속도.

---

## TX MAC Engine 상세

```
사용자 데이터 수신 (AXI-S)
         |
         v
+---------------------------+
| 1. Preamble + SFD 삽입    |
|    7B(10101010) + 1B(SFD) |
+---------------------------+
         |
         v
+---------------------------+
| 2. 패딩 (필요 시)          |
|    Payload < 46B → 패딩   |
|    최소 프레임 64B 보장    |
+---------------------------+
         |
         v
+---------------------------+
| 3. FCS (CRC-32) 계산      |
|    Dst MAC ~ Payload       |
|    → 4B CRC 추가          |
+---------------------------+
         |
         v
+---------------------------+
| 4. IFG 삽입               |
|    최소 12B 간격 보장      |
|    (Rate Adaptation 포함)  |
+---------------------------+
         |
         v
    PCS/SerDes로 전달
```

## RX MAC Engine 상세

```
PCS/SerDes에서 수신
         |
         v
+---------------------------+
| 1. Preamble/SFD 감지+제거  |
|    프레임 시작 인식         |
+---------------------------+
         |
         v
+---------------------------+
| 2. FCS 검증               |
|    CRC-32 재계산 vs FCS    |
|    불일치 → bad 플래그     |
+---------------------------+
         |
         v
+---------------------------+
| 3. 주소 필터링             |
|    Dst MAC == 자신?        |
|    Broadcast? Multicast?   |
|    Promiscuous 모드?       |
+---------------------------+
         |
         v
+---------------------------+
| 4. 길이/타입 검사          |
|    최소 64B? Jumbo 허용?   |
|    Runt/Oversize 감지      |
+---------------------------+
         |
         v
+---------------------------+
| 5. 통계 카운터 업데이트    |
|    RX frames, bytes,       |
|    CRC errors, etc.        |
+---------------------------+
         |
         v
    사용자에게 전달 (AXI-S)
    tuser에 FCS good/bad 표시
```

---

## AXI-Lite 레지스터 인터페이스 (Configuration/Status)

```
AXI-Lite Bus:
  s_axi_awaddr / s_axi_wdata / s_axi_bresp   (Write)
  s_axi_araddr / s_axi_rdata / s_axi_rresp   (Read)

주요 레지스터 영역:

  +------------------+-------------------------------------------+
  | Offset Range     | 용도                                      |
  +------------------+-------------------------------------------+
  | 0x0000 - 0x00FF  | Global Config (리셋, 모드, 속도 설정)      |
  | 0x0100 - 0x01FF  | TX Config (MAC 주소, MTU, TX Enable)       |
  | 0x0200 - 0x02FF  | RX Config (Promiscuous, Filter, RX Enable) |
  | 0x0300 - 0x03FF  | Flow Control (Pause Quanta, PFC 설정)      |
  | 0x0400 - 0x04FF  | RS-FEC Config/Status                       |
  | 0x0800 - 0x0FFF  | Statistics Counters (RMON, 읽기 전용)      |
  | 0x1000 - 0x10FF  | PTP/1588 Config + Timestamp Capture        |
  +------------------+-------------------------------------------+

레지스터 접근 패턴:
  - 통계 카운터: Read-on-Clear 또는 Latch-on-Read 방식
    → 읽기 시 값이 0으로 리셋되거나 스냅샷 래치됨
    → DV에서 읽기 순서/타이밍에 따른 정확성 검증 중요
  - Config 레지스터: Write 후 즉시 적용 또는 다음 프레임부터 적용
    → "When does config take effect?" 가 검증 포인트
```

**DV 관점 (RAL 연결)**: UVM RAL (Register Abstraction Layer)로 레지스터 맵을 모델링하고, frontdoor/backdoor 접근, reset value 검증, read-only/write-only 속성 검증 수행.

---

## PTP/IEEE 1588 타임스탬프

정밀 시간 동기화를 위한 하드웨어 타임스탬프 기능.

```
왜 필요한가?
  - 데이터센터 내 서버 간 μs~ns 단위 시간 동기화
  - 금융 거래, 5G 프론트홀 등에서 정밀 타이밍 필수
  - 소프트웨어 타임스탬프는 OS 지터로 정밀도 부족

DCMAC의 PTP 지원:
  TX Timestamp:
    - 프레임이 MAC을 떠나는 정확한 시점 캡처
    - AXI-S 사이드밴드 또는 별도 FIFO로 전달
    - 1-step (수정 후 전송) / 2-step (캡처만 후 SW 처리) 모드

  RX Timestamp:
    - 프레임이 MAC에 도착하는 정확한 시점 캡처
    - tuser 또는 별도 인터페이스로 상위 계층에 전달

  +---------+    +------+    +----------+
  | PTP     | →  | MAC  | →  | TX       |
  | Frame   |    |      |    | (ts 캡처)|
  +---------+    +------+    +----------+
                    ↓
              Timestamp FIFO
              → SW가 읽어서 PTP 프로토콜 처리

DV 관점:
  - 타임스탬프 정밀도: 캡처 시점이 실제 전송/수신 시점과 일치하는지
  - 1-step 모드: Correction Field가 정확히 수정되었는지
  - 타임스탬프 FIFO 오버플로우 시 동작
  - PTP 프레임 식별 (EtherType 0x88F7) 정확성
```

---

## 통계 카운터 (RMON)

| 카운터 | 설명 |
|--------|------|
| tx_frames / rx_frames | 송수신 프레임 수 |
| tx_bytes / rx_bytes | 송수신 바이트 수 |
| rx_fcs_errors | FCS 에러 프레임 수 |
| rx_runt_frames | 최소 크기 미달 프레임 |
| rx_oversize_frames | 최대 크기 초과 프레임 |
| tx_pause / rx_pause | Pause 프레임 수 |
| tx_pfc / rx_pfc | PFC 프레임 수 |

---

## TOE ↔ DCMAC 연동 상세 (이력서 직결)

```
MangoBoost Data Path:

  Host ↔ TOE ↔ DCMAC ↔ PHY ↔ Network

  TOE → DCMAC (TX):
    TOE가 TCP 세그먼트를 IP 패킷으로 완성
    → AXI-S로 DCMAC에 전달 (Dst MAC부터 시작)
    → DCMAC이 Preamble + FCS + IFG 추가
    → Ethernet Frame으로 PHY에 전달

  DCMAC → TOE (RX):
    PHY에서 Ethernet Frame 수신
    → DCMAC이 Preamble 제거, FCS 검증
    → AXI-S로 TOE에 전달 (tuser에 FCS 결과)
    → TOE가 IP/TCP 헤더 파싱 시작

  검증 핵심 인터페이스:
    +-------+  AXI-S (512-bit)  +-------+
    |  TOE  | ←─────────────── | DCMAC |
    |       | ──────────────→  |       |
    +-------+                   +-------+
      tdata, tvalid, tready, tlast, tkeep, tuser
```

### 연동 검증 포인트

| 항목 | 시나리오 | 확인 사항 |
|------|---------|----------|
| 핸드셰이크 | tvalid/tready 조합 | 데드락 없음, 데이터 손실 없음 |
| 프레임 경계 | tlast 정확성 | 프레임 단위 정확한 분리 |
| 바이트 마스크 | tkeep 마지막 beat | 유효 바이트만 전달 |
| 백프레셔 | DCMAC busy (tready=0) | TOE가 올바르게 대기 |
| FCS 에러 전파 | DCMAC이 bad FCS 수신 | tuser로 TOE에 통지, TOE가 폐기 |
| Pause 동작 | DCMAC이 Pause 수신 | TX 일시 중단 → TOE 백프레셔 |

---

## Q&A

**Q: DCMAC이 하는 일과 하지 않는 일은?**
> "DCMAC은 Ethernet L2 MAC이다. 하는 일: 프레임 생성(Preamble, FCS, IFG 추가), FCS 검증, 주소 필터링, 흐름 제어(Pause/PFC), 통계 수집. 하지 않는 일: IP/TCP 처리(→ TOE), 라우팅(→ IP 계층), 물리 전송(→ PHY/SerDes). 계층 분리가 명확하다."

**Q: DCMAC 서브시스템 검증에서 E2E란?**
> "Host에서 TOE를 통해 DCMAC까지의 전체 데이터 경로를 의미한다. Host가 보낸 데이터가 TOE의 TCP 처리를 거쳐 DCMAC의 Ethernet Frame으로 정확히 변환되는지, 반대 방향도 마찬가지로 DCMAC이 수신한 Frame이 TOE를 거쳐 Host에 정확히 전달되는지를 검증한다. 중간의 AXI-S 인터페이스 핸드셰이크, FCS 에러 전파, 백프레셔 동작이 핵심 포인트다."

**Q: DCMAC이 Multi-port를 지원하는 방식은?**
> "하나의 DCMAC IP가 내부적으로 SerDes 레인을 포트에 매핑하는 구조다. 8레인을 1×400G로 쓸 수도, 4+4로 2×200G, 2+2+2+2로 4×100G로 쓸 수도 있다. 모드는 레지스터 설정으로 결정되고, 변경 시 리셋이 필요하다. 각 포트는 독립적인 AXI-S 인터페이스와 통계 카운터를 가진다."

**Q: DCMAC 레지스터 검증에서 주의할 점은?**
> "세 가지: (1) 통계 카운터의 Read-on-Clear 특성 — 읽기 순서를 잘못하면 값이 사라지므로 Latch-on-Read 구현을 검증. (2) Config 레지스터 적용 시점 — Write 직후 적용인지, 다음 프레임부터인지. (3) Reset Value — 모든 레지스터가 리셋 후 스펙상의 기본값을 가지는지. RAL frontdoor/backdoor 양쪽으로 확인한다."

<div class="chapter-nav">
  <a class="nav-prev" href="01_ethernet_fundamentals.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Ethernet 기본 + 프레임 구조</div>
  </a>
  <a class="nav-next" href="03_dcmac_dv_methodology.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">DCMAC DV 검증 전략</div>
  </a>
</div>
