# Module 02 — Memory Controller

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">💾</span>
    <span class="chapter-back-text">DRAM / DDR</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 02</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#mc-블록-다이어그램">MC 블록 다이어그램</a>
  <a class="page-toc-link" href="#command-scheduler-mc의-두뇌">Command Scheduler — MC의 두뇌</a>
  <a class="page-toc-link" href="#qos-quality-of-service-arbitration">QoS (Quality of Service) / Arbitration</a>
  <a class="page-toc-link" href="#read-write-turnaround-숨은-성능-병목">Read-Write Turnaround — 숨은 성능 병목</a>
  <a class="page-toc-link" href="#reorder-buffer-write-coalescing">Reorder Buffer / Write Coalescing</a>
  <a class="page-toc-link" href="#address-mapping-인터리빙">Address Mapping (인터리빙)</a>
  <a class="page-toc-link" href="#refresh-관리">Refresh 관리</a>
  <a class="page-toc-link" href="#dram-초기화-시퀀스">DRAM 초기화 시퀀스</a>
  <a class="page-toc-link" href="#power-management-전력-상태-머신">Power Management — 전력 상태 머신</a>
  <a class="page-toc-link" href="#주요-dram-명령">주요 DRAM 명령</a>
  <a class="page-toc-link" href="#qa">Q&A</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Apply** Row Hit / Bank-level parallelism / Bank Group interleaving 개념을 throughput 최적화에 적용할 수 있다.
    - **Implement** Read/Write reordering, Write batching, batch drain의 스케줄러 정책을 설계할 수 있다.
    - **Plan** Refresh scheduling (per-bank, fine-grain), tREFI 충족 + 트래픽 영향 최소화 전략을 수립할 수 있다.
    - **Apply** ECC (SECDED, on-die ECC) 구현 시 코드 종류와 검증 시나리오 매핑.
    - **Diagnose** QoS / Aging / Bandwidth Regulation으로 multi-master starvation 방지 기법.

!!! info "사전 지식"
    - [Module 01 — DRAM Fundamentals](01_dram_fundamentals_ddr.md)
    - AXI / handshake 기본
    - Scheduler / FIFO 일반 지식

## 왜 이 모듈이 중요한가

**MC는 SoC 성능의 가장 직접적인 결정자**입니다. CPU/GPU/Display 등 모든 마스터의 메모리 access가 통과. 잘못된 스케줄링 정책 하나가 BW 50% 저하를 만들 수 있고, refresh 누락은 데이터 손실, write batching 부족은 R↔W 전환 폭증 → throughput 절벽. **검증의 핵심은 functional correctness + performance regression**.

!!! tip "💡 이해를 위한 비유"
    **Memory Controller scheduler** ≈ **도로의 신호 제어기 + 회전 교차로 우선순위**

    여러 master 의 read/write request 를 받아 bank 충돌, refresh, bus turnaround 를 고려해 순서 결정. FR-FCFS 등 정책으로 throughput 과 fairness 균형.

---

## 핵심 개념
**Memory Controller(MC) = SoC의 메모리 접근 요청을 DRAM 명령(ACT/RD/WR/PRE/REF)으로 변환하고, 타이밍 제약을 준수하면서 처리량을 최대화하는 스케줄러. 성능의 핵심은 Row Hit 극대화와 Bank-level Parallelism 활용.**

!!! danger "❓ 흔한 오해"
    **오해**: Open-page 정책이 항상 좋다

    **실제**: Open-page 는 row hit 시 빠르지만 row conflict (다른 row access) 시 페널티 큼. workload 가 random 이면 close-page 가 더 좋을 수 있음.

    **왜 헷갈리는가**: "row 열어 두면 다음에 빠름" 만 보고 row conflict 페널티는 직관에 잘 안 들어와서.
---

## MC 블록 다이어그램

```
+------------------------------------------------------------------+
|                    Memory Controller                              |
|                                                                   |
|  AXI/ACE Interface                                                |
|  +------------------------------------------------------------+  |
|  | Request Queue (RQ)                                          |  |
|  |  - AXI Read/Write 요청 수신                                 |  |
|  |  - 주소 → Rank/BG/Bank/Row/Col 디코딩                      |  |
|  +------------------------------------------------------------+  |
|           |                                                       |
|  +--------+-------+                                               |
|  | Address Mapper  |  주소 매핑 정책:                             |
|  | (Interleaving)  |  Row:Bank:Col / Row:BG:Bank:Col 등          |
|  +--------+-------+                                               |
|           |                                                       |
|  +--------+--------------------------------------------+          |
|  | Command Scheduler                                    |          |
|  |                                                      |          |
|  |  - Row Buffer 상태 관리 (Open/Closed per Bank)       |          |
|  |  - 타이밍 제약 검사 (tRCD, tRP, tCCD, tRAS, ...)     |          |
|  |  - 스케줄링 정책 (FR-FCFS, Open/Close Page, ...)     |          |
|  |  - Bank-level Parallelism 활용                       |          |
|  +--------+--------------------------------------------+          |
|           |                                                       |
|  +--------+-------+    +------------------+                       |
|  | Refresh Engine  |    | Power Manager    |                       |
|  |                 |    |                  |                       |
|  | - Periodic REF  |    | - CKE 제어      |                       |
|  | - Postpone/Pull |    | - Self-Refresh   |                       |
|  | - Per-bank (DDR5)|   | - Power-Down     |                       |
|  +--------+-------+    +------------------+                       |
|           |                                                       |
|  +--------+--------------------------------------------+          |
|  | PHY Interface                                        |          |
|  |  - CA (Command/Address) Bus 구동                     |          |
|  |  - DQ/DQS 데이터 버스 제어                           |          |
|  |  - Training 시퀀스 제어                              |          |
|  +------------------------------------------------------+          |
+------------------------------------------------------------------+
```

---

## Command Scheduler — MC의 두뇌

### 스케줄링 정책

| 정책 | 동작 | 장단점 |
|------|------|--------|
| **FCFS** (First Come First Served) | 도착 순서대로 처리 | 공정, 그러나 Row Hit 활용 못함 |
| **FR-FCFS** (First Ready, First Come FS) | Row Hit 명령 우선 → 나머지 FCFS | **가장 일반적**, Row Hit 극대화 |
| **Open Page** | Row를 가능한 오래 열어둠 | Row Hit 높음, Conflict 시 비용 큼 |
| **Close Page** | RD/WR 후 즉시 PRE | Row Conflict 비용 없음, Hit 활용 못함 |
| **Adaptive** | 트래픽 패턴에 따라 Open/Close 전환 | 최적이지만 구현 복잡 |

### Bank-level Parallelism

```
Bank 0: ACT ── RD ── PRE
Bank 1:    ACT ── RD ── PRE
Bank 2:       ACT ── RD ── PRE
Bank 3:          ACT ── RD ── PRE

→ 여러 Bank의 명령을 파이프라인처럼 겹쳐서 실행
→ 하나의 Bank가 tRCD 대기 중에 다른 Bank에서 데이터 전송
→ 대역폭 활용 극대화

Bank Group Interleaving (DDR4/5):
  같은 BG 내 Bank: tCCD_L (긴 간격)
  다른 BG의 Bank:  tCCD_S (짧은 간격) ← 더 빠름
  → 다른 BG로 분산 → 처리량 향상
```

---

## QoS (Quality of Service) / Arbitration

```
문제: SoC에는 여러 마스터(CPU, GPU, DMA, Display, ISP...)가 동시에
     메모리에 접근한다. 각 마스터의 요구사항이 다르다:

  | 마스터   | 특성              | 요구사항               |
  |---------|------------------|----------------------|
  | CPU     | 짧은 Burst, 랜덤  | 낮은 Latency (최우선) |
  | GPU     | 긴 Burst, 순차    | 높은 Bandwidth        |
  | Display | 주기적 읽기       | 보장된 Bandwidth (끊기면 화면 깨짐) |
  | DMA     | 대용량 전송       | 높은 Bandwidth, Latency 관대 |
  | ISP     | 실시간 스트림     | 보장된 Latency        |

QoS 메커니즘:

  1. 우선순위 기반 (Priority-based)
     - 각 AXI 포트에 QoS 레벨 할당 (AxQOS[3:0])
     - 높은 우선순위 요청이 Command Queue에서 먼저 스케줄링
     - 단점: 저우선순위 마스터 기아(Starvation) 가능

  2. Bandwidth 할당 (Bandwidth Regulation)
     - 각 마스터에 최소 보장 Bandwidth 설정
     - 특정 마스터가 할당량 초과 시 Throttle
     - Display 같은 실시간 마스터에 필수

  3. Latency QoS
     - 요청이 큐에서 대기하는 시간을 모니터링
     - 임계값 초과 시 우선순위 자동 승격 (Aging)
     - CPU의 캐시 미스 지연 최소화에 중요

  4. Urgent 시그널
     - Display FIFO가 거의 비면 Urgent 발생
     - MC가 즉시 해당 요청을 최우선 처리
     - Underrun(화면 깨짐) 방지

MC Arbiter 구조 (간략):
  +--------+  +--------+  +--------+
  | CPU    |  | GPU    |  | Display|
  | Port   |  | Port   |  | Port   |
  +---+----+  +---+----+  +---+----+
      |           |           |
  +---+-----------+-----------+----+
  |         QoS Arbiter            |
  |  - Priority check              |
  |  - Bandwidth regulation        |
  |  - Aging / Urgent              |
  +--------+-----------------------+
           |
  +--------+---+
  | Cmd Queue   |  ← 여기서 FR-FCFS 스케줄링 적용
  +-------------+
```

---

## Read-Write Turnaround — 숨은 성능 병목

```
문제: Read와 Write는 데이터 방향이 반대 (DQ 버스 양방향)
     → R→W 또는 W→R 전환 시 "버스 턴어라운드" 지연 발생

  Read → Write (tRTW / tRDWR):
    Read 완료 후 DQ 방향 전환 + DQS preamble 시간 필요
    DDR4 기준: ~4 tCK 이상

  Write → Read (tWTR):
    Write 데이터가 DRAM에 완전히 쓰인 후에만 Read 가능
    DDR4 기준: tWTR_S = 2.5ns (다른 BG), tWTR_L = 7.5ns (같은 BG)

  타임라인 예시:
    ... WR ──[tWTR_L]── RD ...    ← 같은 BG: 긴 대기
    ... WR ──[tWTR_S]── RD ...    ← 다른 BG: 짧은 대기
    ... RD ──[tRTW]─── WR ...     ← 방향 전환 대기

MC 스케줄러의 최적화:
  - Write 요청을 모아서 연속 발행 (Write Batching)
    → R→W/W→R 전환 횟수 최소화
  - Write 배치 후 Read 배치 → "Write Drain" 정책
  - High/Low Watermark: Write Buffer가 일정 수준 차면 Write Drain 시작

  WR WR WR WR ──[tWTR]── RD RD RD RD ──[tRTW]── WR WR WR
  ^^^^^^^^^^^             ^^^^^^^^^^^             ^^^^^^^^^
  Write Batch             Read Batch              Write Batch
  → 전환 2번 (vs 매번 전환 시 8번)

면접 포인트:
  "R/W 터널라운드 비용을 줄이기 위해 MC는 Write Batching을 사용한다.
   Write Buffer의 Watermark를 기반으로 Write Drain 시점을 결정하며,
   이 Watermark 설정이 Latency(낮을수록 좋음)와 Bandwidth(높을수록 좋음)의
   트레이드오프를 결정한다."
```

---

## Reorder Buffer / Write Coalescing

```
MC는 AXI 요청을 도착 순서대로 처리하지 않는다 (Out-of-Order).

Reorder Buffer (ROB):
  - AXI 요청을 수신하면 ROB에 저장
  - DRAM 상태(Row Buffer, Bank 가용성)에 따라 최적 순서로 재배치
  - Row Hit 명령을 먼저 → Row Conflict는 나중에
  - 단, AXI ID 순서는 보장해야 함 (같은 ID 내 순서 유지)

  AXI 요청 도착 순서:     DRAM 발행 순서:
    Req A: Bank0, Row 5     Req B: Bank0, Row 5 (Row Hit → 우선)
    Req B: Bank0, Row 5     Req A: Bank0, Row 5 (같은 Row → 연속)
    Req C: Bank1, Row 3     Req C: Bank1, Row 3 (다른 Bank → 병렬)
    Req D: Bank0, Row 7     Req D: Bank0, Row 7 (Row Conflict → 후순위)

Write Coalescing (쓰기 병합):
  - Write Buffer에서 같은 주소(같은 Cache Line)에 대한 여러 Write를 병합
  - 최종 값만 DRAM에 1회 전송 → 불필요한 Write 제거

  예: CPU가 같은 주소에 3번 Write (a=1, a=2, a=3)
      → MC는 a=3만 DRAM에 전송 (병합)

Read-After-Write Hazard:
  - Write Buffer에 있는 데이터를 Read가 요청하면?
  - → Write Buffer에서 직접 Read에 데이터 포워딩 (RAW Bypass)
  - → DRAM 접근 없이 즉시 응답 가능
```

---

## Address Mapping (인터리빙)

```
물리 주소를 Rank/BG/Bank/Row/Col로 매핑하는 방식:

방식 1: Row:Bank:Column (Row 인터리빙)
  → 연속 주소가 같은 Bank의 같은 Row → Row Hit 높음
  → 순차 접근에 유리

방식 2: Row:BG:Bank:Column (Bank Group 인터리빙)
  → 연속 주소가 다른 BG → tCCD_S 활용 → 대역폭 향상
  → 랜덤 접근에 유리

방식 3: Bank:Row:Column (Bank 인터리빙)
  → 연속 주소가 다른 Bank → Bank Parallelism 극대화
  → 혼합 접근에 유리

실무: SoC 트래픽 패턴에 따라 최적 매핑 선택 (configurable)
```

---

## Refresh 관리

```
문제: Refresh 중 해당 Bank(또는 전체)에 접근 불가 → 성능 저하

DDR4 All-Bank Refresh:
  REF 명령 → 전체 Bank 접근 불가 (tRFC ≈ 350ns)
  tREFI = 7.8μs마다 → 대역폭의 ~5% 손실

DDR5 Same-Bank Refresh:
  REF 명령 → 특정 Bank만 접근 불가
  나머지 Bank는 정상 접근 → 성능 저하 대폭 감소

MC의 Refresh 최적화:
  - Postpone: 바쁠 때 REF 지연 (최대 8개까지 축적)
  - Pull-in: 한가할 때 미리 REF 수행
  - Staggering: Rank별/Bank별 REF 시점 분산
```

---

## DRAM 초기화 시퀀스

```
전원 인가 후 DRAM을 사용하기까지 MC가 수행하는 초기화 절차:

Phase 1: 전원 안정화
  - VDD, VDDQ 인가 → tPW (전원 안정화 대기, 200μs 이상)
  - CK 시작 → CKE = LOW 유지 (대기 상태)
  - RESET# 해제 → tRST 대기

Phase 2: DRAM 초기화
  - CKE = HIGH → DRAM 활성화
  - tXPR 대기 (Reset exit to MRS)
  - MRS 명령 발행 순서 (DDR4 기준):
    1. MR3 → MPR, Fine Granularity Refresh 설정
    2. MR6 → VREF Training, tCCD_L
    3. MR5 → ODT(RTT_PARK), CA Parity
    4. MR4 → Temperature Sensor
    5. MR2 → CWL, RTT_WR
    6. MR1 → DLL, Output Impedance, RTT_NOM
    7. MR0 → BL, CL, DLL Reset
    ※ 순서가 중요 — JEDEC 스펙에 명시

Phase 3: ZQ Calibration
  - ZQCL (ZQ Calibration Long) 명령 발행
  - tZQinit 대기 (512 tCK)
  - 출력 임피던스 초기 보정

Phase 4: Training (BL2에서 수행)
  - Write Leveling → Gate Training → DQ Training
  - → Eye Training → VREF Training
  - (Unit 3에서 상세 설명)

Phase 5: Refresh 시작
  - 초기화 완료 후 tREFI 주기로 Refresh 시작
  - 이제 DRAM 사용 가능

DDR5 초기화 차이:
  - MPC (Multi-Purpose Command) 추가: 다양한 내부 설정 제어
  - CS Training 추가: CA 버스 타이밍 정렬
  - Per-DRAM Addressability: 개별 칩에 독립 MRS
  - 초기화가 DDR4보다 복잡하고 단계가 많음
```

---

## Power Management — 전력 상태 머신

```
DRAM의 전력 상태:

  +----------+    CKE LOW    +-----------+
  |  Active  | -----------> | Power-Down |
  | (정상)   | <----------- |  (PD)      |
  +----+-----+    CKE HIGH   +-----------+
       |                           |
       |    Self-Refresh 진입      |
       |    (CKE LOW + SRE)        |
       v                           v
  +----------+              +-----------+
  |   Idle   |              |   Self-   |
  | (Prechar |              |  Refresh  |
  |  ged)    |              | (SR)      |
  +----------+              +-----------+

각 상태 설명:

  Active Power-Down (APD):
    - CKE LOW, Bank은 Open 상태 유지
    - 복귀 빠름 (tXP ≈ 6 tCK)
    - 짧은 Idle 구간에 사용
    - 절감: ~30-40% (vs Active)

  Precharge Power-Down (PPD):
    - CKE LOW, 모든 Bank Precharged
    - 복귀 빠름 (tXP)
    - APD보다 전력 절감 큼
    - 절감: ~50-60% (vs Active)

  Self-Refresh (SR):
    - CKE LOW, 내부에서 자체 Refresh 수행
    - 외부 클럭 불필요 → 최대 절전
    - 복귀 느림 (tXS ≈ tRFC + 10ns)
    - 절감: ~90% (vs Active)
    - LPDDR5: Deep Sleep 모드로 더욱 깊은 절전

MC의 역할:
  - Idle 시간 모니터링 → 적절한 시점에 PD/SR 진입
  - 요청 도착 시 즉시 복귀 트리거
  - 전력 모드 전환 비용(복귀 Latency)과 절감 효과의 균형
  - LPDDR5: DVFSC와 연계하여 주파수+전력 동시 조절
```

---

## 주요 DRAM 명령

| 명령 | 기능 | 주요 타이밍 |
|------|------|-----------|
| ACT (Activate) | Row를 Row Buffer에 로드 | tRCD 후 RD/WR 가능 |
| RD (Read) | Column 주소로 데이터 읽기 | tCL 후 데이터 출력 |
| WR (Write) | Column 주소로 데이터 쓰기 | tWL 후 데이터 수신 |
| PRE (Precharge) | Row Buffer 닫기 | tRP 후 ACT 가능 |
| REF (Refresh) | 전체/Bank 리프레시 | tRFC 동안 접근 불가 |
| MRS (Mode Register Set) | DRAM 설정 변경 | 초기화 시 사용 |
| ZQ Calibration | 출력 임피던스 보정 | 주기적 수행 |

---

## Q&A

**Q: Memory Controller의 가장 중요한 역할은?**
> "DRAM 타이밍 제약(tRCD, tRP, tCCD 등)을 준수하면서 처리량을 최대화하는 스케줄링이다. 핵심 기법은 두 가지: (1) FR-FCFS로 Row Hit 명령을 우선 처리하여 불필요한 PRE+ACT를 피함. (2) Bank-level Parallelism으로 한 Bank가 대기 중일 때 다른 Bank에서 전송을 수행하여 대역폭을 극대화."

**Q: Address Mapping이 성능에 미치는 영향은?**
> "연속 주소가 같은 Bank/Row에 매핑되면 Row Hit가 높아지고(순차 접근 유리), 다른 Bank Group에 매핑되면 tCCD_S를 활용하여 대역폭이 향상된다(랜덤 접근 유리). SoC의 주요 트래픽 패턴(CPU: 캐시 라인 크기 순차, GPU: 큰 블록 랜덤)에 따라 최적 매핑이 달라지므로 configurable로 설계한다."

**Q: MC는 Read/Write 전환 시 성능 저하를 어떻게 최소화하는가?**
> "DQ 버스 방향 전환 시 tWTR(W→R)과 tRTW(R→W) 지연이 발생한다. MC는 Write Batching으로 Write 요청을 모아서 연속 발행하고, Write Buffer의 High/Low Watermark로 Write Drain 시점을 결정한다. 이를 통해 R↔W 전환 횟수를 최소화하여 대역폭 손실을 줄인다. Watermark가 낮으면 Latency 우선, 높으면 Bandwidth 우선이다."

**Q: MC에서 QoS는 어떻게 동작하는가?**
> "SoC의 여러 마스터(CPU, GPU, Display 등)가 동시에 메모리에 접근할 때, AXI QoS 필드를 기반으로 우선순위를 부여한다. Bandwidth Regulation으로 각 마스터의 최소 보장 대역폭을 설정하고, Aging 메커니즘으로 오래 대기한 요청의 우선순위를 승격시켜 Starvation을 방지한다. Display 같은 실시간 마스터는 Urgent 시그널로 즉각 최우선 처리하여 Underrun을 방지한다."

**Q: DRAM 초기화 시퀀스의 핵심 단계는?**
> "전원 안정화(tPW) → RESET 해제 → CKE 활성화 → MRS 명령으로 Mode Register 프로그래밍(BL, CL, CWL, ODT 등) → ZQ Calibration(임피던스 보정) → Training(WL, DQ, Eye, VREF) → Refresh 시작. 특히 MRS 설정 순서는 JEDEC 스펙에 명시되어 있으며, Training은 코드량이 크고 PVT 의존적이어서 BootROM이 아닌 BL2에서 수행한다."

---
!!! warning "실무 주의점 — tFAW 위반으로 Rank 내 동시 ACT 과전류 위험"
    **현상**: 짧은 시간 내에 서로 다른 Bank에 4개 초과의 ACT 명령이 발행되어 DRAM의 순간 전류가 스펙을 초과, 전압 강하(Vdd Droop)로 인한 데이터 오류 발생.
    
    **원인**: tFAW(Four Activate Window)는 임의의 tFAW 시간 창 내에 ACT를 최대 4회로 제한함. MC 스케줄러가 Bank 병렬화 극대화를 추구하다가 tFAW 윈도우를 무시하고 5번째 ACT를 발행할 수 있음. Open Page Policy에서 Row Conflict가 많은 워크로드일수록 ACT 빈도가 높아 위험 증가.
    
    **점검 포인트**: Timing SVA에서 `tFAW_window` assertion 활성화 여부 확인. 시뮬레이션 파형에서 슬라이딩 윈도우(tFAW 길이) 내 ACT 명령 수 카운트. 랜덤 워크로드 시 Bank 분산 패턴을 로그로 수집하여 tFAW 위반 발생 seed 식별.

## 핵심 정리

- **MC = scheduler + 명령 변환기**: AXI request → ACT/RD/WR/PRE/REF 시퀀스로 변환, timing 종속성 준수.
- **Row Hit 극대화**: 같은 row에 연속 access면 PRE-ACT 회피 → throughput ↑.
- **Bank-level parallelism**: 다른 bank에 동시 ACT 가능. BG 분산으로 tCCD_S 활용.
- **Read/Write reordering + Write batching**: R↔W 전환 비용(tWTR/tRTW) 회피. Watermark로 batch 시점 제어.
- **Refresh scheduling**: tREFI 내 모든 row REF, 트래픽 영향 최소화. per-bank refresh로 다른 bank는 계속 동작.
- **QoS**: AXI QoS + Aging + Bandwidth Regulation. Display 같은 실시간 마스터는 Urgent 우선.
- **Initialization**: tPW → RESET → CKE → MRS → ZQ → Training → Refresh start. MRS 순서는 JEDEC 표준.

## 다음 단계

- 📝 [**Module 02 퀴즈**](quiz/02_memory_controller_quiz.md)
- ➡️ [**Module 03 — PHY**](03_memory_interface_phy.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../01_dram_fundamentals_ddr/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">DRAM 기본 원리 + DDR4/5</div>
  </a>
  <a class="nav-next" href="../03_memory_interface_phy/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Memory Interface / PHY</div>
  </a>
</div>
