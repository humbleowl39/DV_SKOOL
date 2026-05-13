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
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-네-개-axi-요청을-fr-fcfs-로-재배치하기">3. 작은 예 — FR-FCFS 재배치 추적</a>
  <a class="page-toc-link" href="#4-일반화-mc-의-책임-과-스케줄링-축">4. 일반화 — MC 책임 + 스케줄링 축</a>
  <a class="page-toc-link" href="#5-디테일-블록도-정책-qos-refresh-init-코드">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Apply** Row Hit / Bank-level parallelism / Bank Group interleaving 개념을 throughput 최적화에 적용할 수 있다.
    - **Design** Read/Write reordering, Write batching, batch drain 의 스케줄러 정책을 설계할 수 있다.
    - **Plan** Refresh scheduling (per-bank, fine-grain) 으로 tREFI 충족 + 트래픽 영향 최소화 전략을 수립할 수 있다.
    - **Apply** ECC (SECDED, on-die ECC) 구현 시 코드 종류와 검증 시나리오 매핑을 적용할 수 있다.
    - **Diagnose** QoS / Aging / Bandwidth Regulation 으로 multi-master starvation 방지 기법을 진단할 수 있다.

!!! info "사전 지식"
    - [Module 01 — DRAM Fundamentals](01_dram_fundamentals_ddr.md) (Row Hit/Miss/Conflict, timing parameter)
    - AXI / handshake 기본
    - Scheduler / FIFO 일반 지식

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _같은 IP, 다른 BW_

당신은 SoC 디자이너. 같은 GPU IP 를 두 SoC 에 통합. _A SoC_ 에서 BW 80 GB/s, _B SoC_ 에서 BW 50 GB/s. 똑같은 IP 인데 _40% 차이_.

원인 추적:
- Memory channel 수, frequency, DDR rank — _동일_.
- 차이: **Memory Controller 의 scheduling 정책**.
  - A: FR-FCFS (row hit 우선) + GPU 에 priority bin 할당.
  - B: Round-robin (단순 fair).

**FR-FCFS**: 같은 row 의 pending request 를 _먼저_ 처리 → row hit rate ↑ → row miss penalty (~42 cycle) 회피 → BW ↑.

**Round-robin**: row 무시하고 ID 별 fair → row miss 폭증 → BW 폭락.

Module 01 에서 우리는 _하나의 DRAM access_ 가 어떻게 일어나는지 봤습니다. 그러나 실제 SoC 에서는 **CPU + GPU + Display + DMA + ISP** 가 동시에 메모리에 access 하고, 각 요청은 bank conflict, refresh 충돌, R/W turnaround 라는 _시간_ 차원의 충돌을 겪습니다. **Memory Controller (MC) 는 이 모든 충돌을 해소하는 단일 결정자** — SoC 성능의 가장 직접적인 결정자입니다.

이 모듈을 건너뛰면 "왜 같은 IP 에 같은 트래픽을 줘도 BW 가 다른가?" 같은 질문에 답할 수 없고, 검증 시 _기능적 정합성_ 외에 _성능 회귀_ 를 평가할 기준을 잡을 수 없습니다. 잘못된 스케줄링 정책 하나가 BW 50% 저하를 만들 수 있고, refresh 누락은 데이터 손실로 이어집니다. **MC 검증의 핵심은 functional correctness + performance regression 동시 관리**.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **Memory Controller scheduler** ≈ **도로의 신호 제어기 + 회전 교차로 우선순위**.<br>
    여러 master 의 read/write 요청을 받아 bank 충돌, refresh, bus turnaround 를 고려해 발행 순서를 결정. **FR-FCFS** 같은 정책으로 throughput 과 fairness 의 균형을 잡습니다 — 빨간불에 차를 세워 두는 것 같아 보여도 사실은 _전체 처리량_ 을 위한 결정.

### 한 장 그림 — MC 가 만드는 변환

```d2
direction: right

HOST: "input side (host)" {
  direction: down
  CPU: "CPU"
  GPU: "GPU"
  DMA: "DMA"
  DISP: "Display"
  ISP: "ISP"
}
MC: "Memory Controller" {
  direction: down
  MC1: "1. AXI request 수집 (RQ)"
  MC2: "2. 주소 → R/BG/B/Row/Col 디코드"
  MC3: "3. Row buffer state 추적"
  MC4: "4. timing constraint 체크"
  MC5: "5. FR-FCFS 등 정책으로 재배치"
  MC6: "6. Refresh 끼워넣기"
  MC7: "7. Write batching / R/W turn"
  MC8: "8. ACT/RD/WR/PRE/REF 발행"
  MC1 -> MC2
  MC2 -> MC3
  MC3 -> MC4
  MC4 -> MC5
  MC5 -> MC6
  MC6 -> MC7
  MC7 -> MC8
}
DRAM: "output side (DRAM)" {
  DEV: "DRAM device(s)"
}
CPU -> MC1
GPU -> MC1
DMA -> MC1
DISP -> MC1
ISP -> MC1
MC8 -> DEV: "DDR phy / CA bus"
```

### 왜 이렇게 설계됐는가 — Design rationale

세 가지 동시 요구가 있습니다.

1. **Functional correctness** — 모든 timing constraint (tRCD, tRP, tRAS, tFAW, tREFI ...) 를 위반하지 않아야 한다 → DRAM model 의 contract.
2. **Maximum throughput** — Row Hit 극대화 + Bank-level Parallelism + tCCD_S 활용 + R/W batching → 효율을 nominal BW 의 80~95% 까지.
3. **Fairness / QoS** — 어떤 master 도 starvation 되지 않고, 실시간 master (Display) 는 deadline 을 놓치지 않아야 한다.

이 셋은 서로 trade-off 관계입니다. FR-FCFS 는 ①+② 에 강하지만 ③ 이 약하고, strict round-robin 은 ③ 에 강하지만 ② 가 약합니다. 그래서 실제 MC 는 _두 단계 (QoS Arbiter → Cmd Scheduler)_ 로 분할해 각 단계가 다른 목적을 책임집니다 — §5 의 블록도가 이 분할입니다.

---

## 3. 작은 예 — 네 개 AXI 요청을 FR-FCFS 로 재배치하기

가장 단순한 시나리오. AXI 4 개의 read request 가 거의 동시에 도착했고, MC 는 FR-FCFS + open-page 정책 (DDR4-3200) 입니다. 현재 bank 상태: Bank 0 에 Row 5 가 open, 나머지 bank 는 idle.

### 도착 순서 (AXI ID 순)

| 도착 # | AXI ID | 주소 디코드 결과 | Row buffer 상태 |
|---|---|---|---|
| ① | A | (Rank0, BG0, B0, Row=5, Col=0)  | Row 5 가 이미 open → **Row Hit** |
| ② | B | (Rank0, BG0, B0, Row=9, Col=0)  | 같은 bank, 다른 row → **Row Conflict** |
| ③ | C | (Rank0, BG1, B0, Row=3, Col=0)  | 다른 BG, idle → **Row Miss** |
| ④ | D | (Rank0, BG0, B0, Row=5, Col=64) | Row 5 → **Row Hit** |

### MC 가 다시 짜는 발행 순서

```
                  T=0       T=4      T=8      T=12     T=...    T=22     T=44     T=66
 cycle             │         │        │         │       │         │        │        │
 issue (BG0,B0)    │ RD-① Row5,col0   │ RD-④ Row5,col64                                  
 issue (BG1,B0)    │         │ ACT-③ Row3                                                
 issue (BG1,B0)    │         │        │         │       RD-③ Row3                         
 issue (BG0,B0)    │         │        │         │       │         │ PRE     ACT-Row9 │ RD-② 
                   ▲         ▲        ▲         ▲                          
                   Hit       BG split  Hit       Conflict 마지막                       
```

| Step | 시점 (cycle) | MC action | 정책 근거 |
|---|---|---|---|
| ① | `T=0`   | `RD ①` (Bank 0, Row 5 hit, col=0) 발행 | Row Hit 우선 — 즉시 발행 가능 |
| ② | `T=0`   | ④ 도 같은 row → 큐에서 ③ 보다 먼저 발행 가능으로 표시 | open-page hit 우선 |
| ③ | `T=4`   | `ACT ③` (BG1, Bank 0, Row 3) 발행 — 다른 BG 라 ① 의 RD 와 병렬 | Bank-level Parallelism (다른 BG, tCCD_S 조차 적용) |
| ④ | `T=4`   | `RD ④` (BG0, Bank 0, col=64) 발행 (`tCCD_L=8` 만족 전이라면 stall, 그 후 발행) | 같은 bank → tCCD_L 간격 |
| ⑤ | `T=22`  | ② 차례 — 그러나 Row 5 가 아직 open. 이제 PRE 발행 | Row 5 의 hit 가능 요청 모두 소진. Row Conflict 를 _마지막에_ 처리 |
| ⑥ | `T=44`  | `ACT ②` (BG0, B0, Row 9) — `tRP` 만족 후 | tRP 충족 보장 |
| ⑦ | `T=66`  | `RD ②` (col=0) 발행 — `tRCD` 만족 후 | tRCD 충족 보장 |
| ⑧ | `T=` ...| 전 요청 데이터 회수, AXI ID 순서대로 응답 (A→B→C→D) | AXI ordering rule (같은 ID 안 순서 보존) |

```c
// FR-FCFS 의사코드 — 매 cycle 호출
function command_t mc_pick_next() {
    // 1. Row Hit 후보 우선 (가장 빠름)
    foreach (req in pending_queue) {
        if (req.row == bank[req.bank].open_row && timing_ok(req))
            return req;                    // Hit
    }
    // 2. Idle bank (Row Miss) 다음
    foreach (req in pending_queue) {
        if (bank[req.bank].open_row == NONE && timing_ok(req))
            return req;                    // Miss
    }
    // 3. 마지막으로 Row Conflict — PRE/ACT 시작
    foreach (req in pending_queue) {
        if (timing_ok_for_pre_act(req)) return req;  // Conflict 진입
    }
    return NOP;
}
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) FR-FCFS 의 본질은 "Hit 부터 짜내고 Conflict 는 가장 뒤로"**. Row Hit 두 번 (① 와 ④) 사이에 ② 의 PRE/ACT 를 끼워 넣으면 Hit 의 가속을 잃기 때문. <br>
    **(2) 다른 BG 는 _완전히_ 병렬**. ③ 의 ACT 가 `T=4` 에 발행돼도 ① 의 데이터 회수와 타임라인이 겹칩니다. 이것이 BG interleaving 으로 effective BW 를 늘리는 메커니즘.

---

## 4. 일반화 — MC 의 책임 과 스케줄링 축

### 4.1 MC 가 하는 일 — 단일 책임 → 다층 책임

| Layer | 책임 | 대표 알고리즘 / 정책 |
|------|------|---------|
| **Address Mapping** | 물리주소 → (Rank, BG, Bank, Row, Col) | row:bg:bank:col 등 (§5.7) |
| **QoS Arbiter** | master 간 priority / fairness / urgency | priority + aging + urgent + BW regulation (§5.4) |
| **Command Scheduler** | timing-aware 명령 발행 | FR-FCFS / open vs close page / bank parallelism (§5.2) |
| **Refresh Engine** | tREFI 보장, traffic 회피 | postpone / pull-in / per-bank (§5.6, Module 01 §5.6) |
| **Power Manager** | idle 시 PD/SR 진입, latency 보전 | active-PD / precharge-PD / self-refresh (§5.9) |
| **Init / Training** | 부팅 시 MRS / ZQ / Training | JEDEC sequence (§5.8) |
| **PHY Interface** | CA/DQ/DQS 신호 형성 | Module 03 |

### 4.2 두 핵심 자원 축

```
   throughput 자원         │  fairness / latency 자원
   ─────────────────────   │  ──────────────────────
   Row Hit                 │  AXI QoS field
   Bank-level Parallelism  │  Aging counter
   Bank Group Interleaving │  Urgent signal (Display)
   Write Batching          │  Bandwidth Regulation
   tCCD_S 분산             │  Round-robin fall-back
```

§3 의 worked example 은 _throughput_ 축을 보여줬습니다. 실 시스템에서는 _fairness_ 축이 아주 자주 throughput 을 제한합니다 — Display 의 Urgent 1번이 큐의 Hit 행렬을 통째로 깨고 들어옵니다.

### 4.3 변형 / Edge case

- **Row buffer thrashing**: 같은 bank 의 multiple-row 동시 access → row conflict 연쇄 → effective BW 50% 미만. 해결: address mapping 에서 hot bit 을 BG 로 옮김.
- **Read starvation under heavy write**: write batching 이 너무 길면 read latency 폭발. Watermark 기반 drain 정책.
- **Refresh storm**: postpone 누적 후 한 번에 8 REF 직렬 발행 → BW 절벽. Pull-in / staggering 으로 분산.
- **Closed-page in random workload**: open-page 가 conflict 비싸므로 무조건 PRE close → 반대 trade-off.

---

## 5. 디테일 — 블록도, 정책, QoS, Refresh, Init, 코드

### 5.1 MC 블록 다이어그램

```d2
direction: down

AXI: "AXI/ACE Interface"
MC: "Memory Controller" {
  direction: down
  RQ: "Request Queue (RQ)\n· AXI Read/Write 요청 수신\n· 주소 → Rank/BG/Bank/Row/Col 디코딩"
  ADM: "Address Mapper (Interleaving)\nRow:Bank:Col / Row:BG:Bank:Col 등"
  CS: "Command Scheduler\n· Row Buffer 상태 관리 (Open/Closed per Bank)\n· 타이밍 제약 검사 (tRCD, tRP, tCCD, tRAS, ...)\n· 스케줄링 정책 (FR-FCFS, Open/Close Page, ...)\n· Bank-level Parallelism 활용"
  REF: "Refresh Engine\n· Periodic REF\n· Postpone/Pull\n· Per-bank (DDR5)"
  PM: "Power Manager\n· CKE 제어\n· Self-Refresh\n· Power-Down"
  PHY: "PHY Interface\n· CA Bus 구동\n· DQ/DQS 데이터 버스 제어\n· Training 시퀀스 제어"
  RQ -> ADM
  ADM -> CS
  CS -> REF
  CS -> PM
  CS -> PHY
}
AXI -> RQ
```

### 5.2 Command Scheduler — 정책별 비교

| 정책 | 동작 | 장단점 |
|------|------|--------|
| **FCFS** (First Come First Served) | 도착 순서대로 처리 | 공정, 그러나 Row Hit 활용 못함 |
| **FR-FCFS** (First Ready, First Come FS) | Row Hit 명령 우선 → 나머지 FCFS | **가장 일반적**, Row Hit 극대화 |
| **Open Page** | Row를 가능한 오래 열어둠 | Row Hit 높음, Conflict 시 비용 큼 |
| **Close Page** | RD/WR 후 즉시 PRE | Row Conflict 비용 없음, Hit 활용 못함 |
| **Adaptive** | 트래픽 패턴에 따라 Open/Close 전환 | 최적이지만 구현 복잡 |

### 5.3 Bank-level Parallelism + BG Interleaving

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

### 5.4 QoS (Quality of Service) / Arbitration

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

### 5.5 Read-Write Turnaround — 숨은 성능 병목

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

### 5.6 Reorder Buffer / Write Coalescing / RAW bypass

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

### 5.7 Address Mapping (인터리빙)

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

### 5.8 Refresh 관리

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

### 5.9 DRAM 초기화 시퀀스

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

### 5.10 Power Management — 전력 상태 머신

```d2
direction: right

INITIAL { shape: circle; style.fill: "#333" }
INITIAL -> Active
Active -> PowerDown: "CKE LOW"
PowerDown -> Active: "CKE HIGH"
Active -> Idle: "PRE all"
Idle -> SelfRefresh: "CKE LOW + SRE"
SelfRefresh -> Idle: "SRX"
# unparsed: note right of Active: 정상 동작
# unparsed: note right of PowerDown: Power-Down (PD)
# unparsed: note left of Idle: 모든 Bank precharged
# unparsed: note left of SelfRefresh: Self-Refresh (SR)
```

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

### 5.11 주요 DRAM 명령

| 명령 | 기능 | 주요 타이밍 |
|------|------|-----------|
| ACT (Activate) | Row를 Row Buffer에 로드 | tRCD 후 RD/WR 가능 |
| RD (Read) | Column 주소로 데이터 읽기 | tCL 후 데이터 출력 |
| WR (Write) | Column 주소로 데이터 쓰기 | tWL 후 데이터 수신 |
| PRE (Precharge) | Row Buffer 닫기 | tRP 후 ACT 가능 |
| REF (Refresh) | 전체/Bank 리프레시 | tRFC 동안 접근 불가 |
| MRS (Mode Register Set) | DRAM 설정 변경 | 초기화 시 사용 |
| ZQ Calibration | 출력 임피던스 보정 | 주기적 수행 |

### 5.12 Q&A — 자주 묻는 질문

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

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Open-page 정책이 항상 좋다'"
    **실제**: Open-page 는 row hit 시 빠르지만 row conflict 시 `tRP+tRCD` 페널티가 큽니다. random/streaming workload 에서 close-page 또는 adaptive 가 더 좋을 수 있습니다.<br>
    **왜 헷갈리는가**: "row 열어 두면 다음에 빠름" 만 보고 row conflict 페널티는 직관에 잘 안 들어와서.

!!! danger "❓ 오해 2 — 'AXI 요청은 도착 순서대로 처리된다'"
    **실제**: MC 는 ROB 로 의도적으로 _Out-of-Order_ 처리합니다. 단 같은 AXI ID 안의 순서만 보장. 이 사실을 모르고 응답 순서를 가정하는 master 는 deadlock / data hazard 를 일으킬 수 있습니다.<br>
    **왜 헷갈리는가**: "메모리 = 순차 모델" 이라는 software 측 직관 때문.

!!! danger "❓ 오해 3 — 'Write Batching 이 길수록 throughput 이 높다'"
    **실제**: Write batch 가 길면 R/W 전환은 줄지만 그 동안 _read latency tail_ 이 폭발합니다. CPU 의 cache miss latency 는 OS scheduling 까지 영향. Watermark 는 BW 와 latency 의 정밀한 균형점.

!!! danger "❓ 오해 4 — 'QoS 우선순위만 잘 주면 starvation 없다'"
    **실제**: Strict priority 는 저우선순위 master 의 _완전 starvation_ 을 만듭니다. Aging counter 가 명령 대기 시간을 추적하고, 임계값을 넘으면 priority 를 자동 승격해야 starvation 이 방지됩니다.

!!! danger "❓ 오해 5 — 'Refresh 는 그냥 주기적인 background. MC 가 신경쓸 일 적음'"
    **실제**: Postpone 가 누적되면 한 번에 8 REF 직렬 발행 → BW 절벽. 또 tREFI 위반은 Row Hammer 보안 취약점으로 직결. MC 의 refresh 엔진은 staggering / pull-in 을 신중히 설계합니다.

### DV 디버그 체크리스트 (MC 검증 시 자주 보는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 평균 BW 정상이나 burst 단위로 급락 | tFAW 4-ACT 한도 초과 / Refresh storm | tFAW SVA, refresh queue depth 그래프 |
| Read latency tail 이 길다 (p99) | Write batching watermark 가 너무 높음 / starvation | Write drain timestamp, aging counter |
| 같은 row 인데 Row Hit 가 안 됨 | bank state tracker 에 PRE 누락 / open-row 갱신 버그 | bank tracker dump, ACT/PRE 로그 |
| AXI ID 순서가 깨짐 | ROB 가 같은 ID 응답을 reorder | ROB rule check, ID-별 timestamp |
| Display Underrun (FIFO empty) | Urgent signal 미인식 / BW regulation 부족 | Urgent assertion 발생, Display 트래픽 BW 측정 |
| tCCD_L 이 적용돼야 할 자리에 tCCD_S 발행 | bank-group bit 매핑 mismatch | address mapper 의 BG 추출 logic |
| Refresh interval 이 점점 길어짐 | postpone 카운터 race / pull-in 실패 | refresh issue timestamp 와 tREFI 비교 |
| Write 후 즉시 Read 시 stale value | RAW bypass forward 누락 | write buffer 의 read-forward path |

!!! warning "실무 주의점 — tFAW 위반으로 Rank 내 동시 ACT 과전류 위험"
    **현상**: 짧은 시간 내에 서로 다른 Bank에 4개 초과의 ACT 명령이 발행되어 DRAM의 순간 전류가 스펙을 초과, 전압 강하(Vdd Droop)로 인한 데이터 오류 발생.

    **원인**: tFAW(Four Activate Window)는 임의의 tFAW 시간 창 내에 ACT를 최대 4회로 제한함. MC 스케줄러가 Bank 병렬화 극대화를 추구하다가 tFAW 윈도우를 무시하고 5번째 ACT를 발행할 수 있음. Open Page Policy에서 Row Conflict가 많은 워크로드일수록 ACT 빈도가 높아 위험 증가.

    **점검 포인트**: Timing SVA에서 `tFAW_window` assertion 활성화 여부 확인. 시뮬레이션 파형에서 슬라이딩 윈도우(tFAW 길이) 내 ACT 명령 수 카운트. 랜덤 워크로드 시 Bank 분산 패턴을 로그로 수집하여 tFAW 위반 발생 seed 식별.

---

## 7. 핵심 정리 (Key Takeaways)

- **MC = scheduler + 명령 변환기**: AXI request → ACT/RD/WR/PRE/REF 시퀀스로 변환하면서 모든 timing 종속성을 보장.
- **Row Hit 극대화**: 같은 row 연속 access 면 PRE/ACT 회피 → throughput ↑ — FR-FCFS 의 핵심.
- **Bank-level parallelism + BG interleaving**: 다른 bank/BG 에 동시 ACT 가능. tCCD_S 활용으로 latency 겹침.
- **Write batching + RAW bypass + ROB**: R↔W 전환 비용 회피, 단 latency tail 과의 trade-off.
- **Refresh scheduling**: tREFI 보장 + traffic 영향 최소화. per-bank / staggering / pull-in.
- **QoS**: AXI QoS field + Aging + Bandwidth Regulation. Display 같은 실시간 master 는 Urgent 우선.

!!! warning "실무 주의점"
    - 평균 BW 가 정상이라도 latency tail / starvation 은 별도로 감시.
    - Open-page 는 random workload 에서 _역효과_ 가능 — workload profiling 필수.
    - Refresh 정책은 Module 01 의 cell physics 와 직결 — RFM/Row Hammer 와 반드시 함께 검증.

### 7.1 자가 점검

!!! question "🤔 Q1 — FR-FCFS vs round-robin (Bloom: Analyze)"
    Multi-master DRAM (CPU + GPU + Display). FR-FCFS 정책이 _Display starvation_ 가능?

    ??? success "정답"
        가능. FR-FCFS 는 _row-hit_ 우선 — Display 의 _random pattern_ 은 항상 row-miss → 우선순위 낮음.

        해법: **QoS + Aging**:
        - Display request 의 _AXI QoS_ field 가 high.
        - _Aging counter_: 오래된 request 자동 priority 상승.
        - 두 가지로 starvation 방어 + row-hit 효율 둘 다.

!!! question "🤔 Q2 — Scheduler 비교 (Bloom: Evaluate)"
    Open-page FR-FCFS vs Close-page Round-Robin. 어느 workload?

    ??? success "정답"
        - **HPC/AI** (sequential, high reuse): Open + FR-FCFS. row hit ↑.
        - **OLTP database** (random small reads): Close + Round-Robin. row miss 어차피 많음, fairness 중요.
        - **Hybrid (modern SoC)**: 동적 정책 전환 — workload 측정 후 5초마다 재결정.

### 7.2 출처

**External**
- JEDEC DDR4/5 *Memory Controller* guidelines
- Mutlu et al. *Memory Scheduling* 논문들

---

## 다음 모듈

→ [Module 03 — Memory Interface / PHY](03_memory_interface_phy.md): MC 의 명령이 _전기 신호_ 가 되는 layer. DLL/PLL, ODT, equalization, training. ns-단위 timing margin 의 영역.

[퀴즈 풀어보기 →](quiz/02_memory_controller_quiz.md)

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


--8<-- "abbreviations.md"
