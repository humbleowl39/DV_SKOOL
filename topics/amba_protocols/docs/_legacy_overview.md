# AMBA Protocols (APB / AHB / AXI / AXI-Stream) — 개요

## 학습 플랜
- **레벨**: Intermediate (SoC 검증 실무에서 전 프로토콜 사용 경험)
- **목표**: 각 프로토콜의 위치, 핸드셰이크, 차이점을 화이트보드에 그리며 설명할 수 있는 수준

---

## 핵심 용어집 (Glossary)

### 프로토콜 계층

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **AMBA** | Advanced Microcontroller Bus Architecture | ARM의 SoC 버스 아키텍처 표준 |
| **APB** | Advanced Peripheral Bus | 저속 주변장치용 간단한 버스 (Timer, UART, GPIO) |
| **AHB** | Advanced High-performance Bus | 중간 성능 버스, 파이프라인 지원 (DMA, Boot ROM) |
| **AXI** | Advanced eXtensible Interface | 고성능 5채널 버스, Out-of-Order 지원 (CPU↔MC) |
| **AXI-Stream** | AXI Streaming Protocol | 주소 없는 단방향 스트리밍 (TOE↔DCMAC, DSP) |
| **ACE** | AXI Coherency Extension | 캐시 일관성 프로토콜 (멀티코어) |
| **CHI** | Coherent Hub Interface | ACE 후속, AMBA 5의 고성능 일관성 인터페이스 |

### 핸드셰이크 & 신호

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **VALID/READY** | — | AXI 핵심 핸드셰이크. VALID=송신 유효, READY=수신 준비. 동시 asserted 시 전송 |
| **PSEL/PENABLE** | Peripheral Select/Enable | APB 2-phase 핸드셰이크 (Setup → Access) |
| **PREADY** | Peripheral Ready | APB Slave 준비 신호 (Wait State 삽입용, APB3+) |
| **PSLVERR** | Slave Error | APB 에러 응답 (APB3+) |
| **HTRANS** | AHB Transfer Type | IDLE/BUSY/NONSEQ/SEQ 전송 타입 |

### AXI 채널 & Burst

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **AR/AW/W/R/B** | — | AXI 5채널: Read Addr / Write Addr / Write Data / Read Data / Write Response |
| **AxLEN** | Burst Length | Burst 내 beat 수 = AxLEN + 1 (AXI3: 최대 16, AXI4: 최대 256) |
| **AxSIZE** | Beat Size | Beat 당 바이트 수 = 2^AxSIZE |
| **WSTRB** | Write Strobe | 바이트 단위 쓰기 마스크 |
| **AxID** | Transaction ID | 트랜잭션 추적 및 Out-of-Order 완료용 ID |
| **INCR/WRAP/FIXED** | Burst Type | 주소 증가 / 경계 순환 / 고정 주소 |

### AXI-Stream 신호

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **tdata** | Transfer Data | 스트림 데이터 |
| **tvalid/tready** | — | 핸드셰이크 신호 (AXI와 동일 원리) |
| **tlast** | Transfer Last | 패킷/프레임 마지막 beat 표시 |
| **tkeep** | Transfer Keep | 유효 바이트 마스크 |

### 응답 & 보호

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **OKAY/SLVERR/DECERR** | — | AXI 응답: 정상 / Slave 에러 / 주소 범위 밖 에러 |
| **EXOKAY** | Exclusive OK | Exclusive Access 성공 응답 |
| **AxPROT** | Protection Control | Privileged/Secure/Instruction 접근 속성 |
| **AxCACHE** | Cache Policy | Bufferable/Modifiable/Allocate 캐시 정책 |
| **AxQOS** | Quality of Service | AXI4의 우선순위 제어 (0~15) |

### 상호연결

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **Interconnect** | — | 다수 Master/Slave를 연결하는 중앙 스위치 |
| **Bridge** | Bus Bridge | 프로토콜 간 변환 (AXI→AHB, AHB→APB) |
| **Write Interleaving** | — | AXI3에서 지원, AXI4에서 제거된 Write Data 인터리브 기능 |

---

## AMBA 진화 역사

```
1996  AMBA 2   ── APB (v1), AHB
2003  AMBA 3   ── APB3 (PREADY/PSLVERR 추가), AHB-Lite, AXI3
2010  AMBA 4   ── APB4 (PPROT/PSTRB 추가), AXI4, AXI4-Lite, AXI4-Stream, ACE
2021  AMBA 5   ── APB5 (PWAKEUP/PAUSER 추가), AXI5, CHI (Coherent Hub Interface)
```

### 버전별 핵심 변화

| 버전 | 핵심 추가 사항 |
|------|--------------|
| **AMBA 2** (1996) | APB 원본(PREADY 없음, wait 불가), AHB 도입 |
| **AMBA 3** (2003) | APB3에 PREADY/PSLVERR 추가 → wait state+에러 지원. AXI3 도입(5채널, OOO, Write Interleaving) |
| **AMBA 4** (2010) | APB4에 PPROT/PSTRB 추가. AXI4에서 Write Interleaving 제거, Burst 256까지 확장, QoS 추가. AXI4-Stream 신규 |
| **AMBA 5** (2021) | APB5에 PWAKEUP(저전력), PAUSER/PWUSER(보안). AXI5에 Atomic Operation, Trace 신호. CHI가 ACE 대체 |

> **면접 포인트**: "AXI3→AXI4에서 Write Interleaving이 제거된 이유?"
> → Interconnect 구현 복잡도 대비 실질적 성능 이득이 미미했기 때문. 대부분의 Slave가 interleaving을 지원하지 않았음.

---

## 컨셉 맵

```
                    AMBA Protocol Family
                           |
        ┌──────────────────┼──────────────────┐
        │                  │                  │
      APB               AHB                AXI ──────── ACE/CHI
    (최소 면적)        (중간)            (고성능)       (Coherency)
   Config/Reg     Legacy/단순DMA     CPU↔MC, IP↔IP   Cache Coherent
   APB3→APB4→APB5  AHB→AHB-Lite     AXI3→AXI4→AXI5
        │                │                │
        │           AHB-APB Bridge        │
        │◄──────────────┘                │
        │                          AXI4-Stream
        │                          (스트리밍, 주소 없음)
        │                          TOE↔DCMAC, DSP
        │                                │
        └────── 모두 VALID/READY 기반 핸드셰이크 ──────┘
                (APB만 PSEL/PENABLE 방식)
```

### SoC 내 프로토콜 계층 — "왜 여러 개가 필요한가?"

```
  성능 높음 ←──────────────────────────────→ 게이트 비용 낮음

  AXI/ACE     AHB          APB
  ┌─────┐    ┌─────┐      ┌──────┐
  │CPU  │    │DMA  │      │Timer │
  │GPU  │    │Boot │      │UART  │
  │MC   │    │ROM  │      │GPIO  │
  │DMA  │    │     │      │OTP   │
  └──┬──┘    └──┬──┘      └──┬───┘
     │          │             │
  ═══╪══════════╪═════════════╪═══  AXI Interconnect
     │          │             │
     │     AXI→AHB Bridge    │
     │          │        AHB→APB Bridge
     │          │             │
     │     AHB 버스        APB 버스

  → 고성능 IP는 AXI, 레거시 IP는 AHB, 저속 말단은 APB
  → Bridge가 프로토콜을 변환하여 연결
  → 각 IP에 적합한 복잡도의 인터페이스 = 면적 최적화
```

---

## 학습 단위

| # | 단위 | 핵심 질문 |
|---|------|----------|
| 1 | **APB & AHB** | 간단한 레지스터 접근과 중간 복잡도 전송은 어떻게 다른가? |
| 2 | **AXI (Full)** | 고성능 메모리 매핑 전송의 5채널 구조는 어떻게 동작하는가? |
| 3 | **AXI-Stream** | 스트리밍 데이터 전송은 AXI와 어떻게 다른가? |

---

## 이력서 연결

| 이력서 항목 | 프로토콜 | 면접 시 활용 |
|------------|---------|-------------|
| BootROM 검증 (레지스터 접근) | APB | OTP/보안 레지스터 접근 |
| UFS HCI (Host 인터페이스) | AHB/AXI | UTRD DMA, 레지스터 |
| MC (메모리 접근) | AXI/ACE | 고성능 메모리 트래픽 |
| TOE ↔ DCMAC | **AXI-Stream** | 패킷 스트리밍 |
| MMU (변환 요청/응답) | AXI-Stream | Translation 인터페이스 |
| Custom Thin VIP | AXI-Stream | tdata/tvalid/tready 핵심 경로 |


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
