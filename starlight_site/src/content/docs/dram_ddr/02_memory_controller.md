---
title: "Module 02 — Memory Controller"
---

:::tip[학습 목표]
이 모듈을 마치면 (**LPDDR5 mobile SoC-통합 MC 를 주제로**):

- **Apply** Row Hit / Bank-level parallelism / Bank Group interleaving 개념을 throughput 최적화에 적용할 수 있다.
- **Design** Read/Write reordering, Write batching, batch drain 의 스케줄러 정책을 설계할 수 있다.
- **Plan** LPDDR5 Refresh scheduling (per-bank + PASR) 으로 tREFI 충족 + 트래픽 영향 최소화 전략을 수립할 수 있다.
- **Apply** ECC (on-die ECC + Link ECC) 구현 시 코드 종류와 검증 시나리오 매핑을 적용할 수 있다.
- **Diagnose** QoS / Aging / Bandwidth Regulation 으로 mobile multi-master (Display/ISP) starvation 방지 기법을 진단할 수 있다.
- **Explain** mobile LPDDR5 MC 의 DVFSC 전력 gear / Deep Sleep / PASR 가 대역폭·실시간 QoS 와 맺는 trade-off 를 설명할 수 있다.
:::
:::note[사전 지식]
- [Module 01 — DRAM Fundamentals](../01_dram_fundamentals_ddr/) (Row Hit/Miss/Conflict, timing parameter)
- AXI / handshake 기본
- Scheduler / FIFO 일반 지식
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _같은 IP, 다른 BW_

같은 GPU IP 를 두 SoC 에 통합했을 때 _A SoC_ 에서 대역폭 80 GB/s, _B SoC_ 에서 50 GB/s 가 나온다면, 차이는 어디서 올까요? Memory channel 수·frequency·DDR rank 가 모두 동일하다면 원인은 한 곳으로 수렴합니다 — **Memory Controller 의 scheduling 정책**입니다.

A SoC 는 **FR-FCFS**(First Ready First Come First Served) 정책으로 같은 row 에 대기 중인 요청을 먼저 처리하고 GPU 에 priority bin 을 할당합니다. 이렇게 하면 row hit rate 가 올라가고 row miss 패널티(약 42 cycle)를 회피할 수 있어 대역폭이 높게 유지됩니다. B SoC 는 단순 round-robin 으로 row 상태를 무시하고 ID 별로 공평하게 발행하는데, 그 결과 row miss 가 빈발하여 대역폭이 크게 떨어집니다. 40% 차이는 알고리즘 한 줄의 결과입니다.

Module 01 에서 우리는 _하나의 DRAM access_ 가 어떻게 일어나는지 봤습니다. 그러나 실제 SoC 에서는 **CPU + GPU + Display + DMA + ISP** 가 동시에 메모리에 access 하고, 각 요청은 bank conflict, refresh 충돌, R/W turnaround 라는 _시간_ 차원의 충돌을 겪습니다. **Memory Controller (MC) 는 이 모든 충돌을 해소하는 단일 결정자** — SoC 성능의 가장 직접적인 결정자입니다.

이 모듈을 건너뛰면 "왜 같은 IP 에 같은 트래픽을 줘도 BW 가 다른가?" 같은 질문에 답할 수 없고, 검증 시 _기능적 정합성_ 외에 _성능 회귀_ 를 평가할 기준을 잡을 수 없습니다. 잘못된 스케줄링 정책 하나가 BW 50% 저하를 만들 수 있고, refresh 누락은 데이터 손실로 이어집니다. **MC 검증의 핵심은 functional correctness + performance regression 동시 관리**.

:::note[이 모듈의 주제 — mobile SoC 에 통합된 LPDDR5 MC]
이 모듈은 **LPDDR5 MC** 를 다룹니다. LPDDR5 의 MC 는 별도 칩이 아니라 **모바일 SoC(AP) 내부에 통합**되어 있고, 메모리는 SoC 위에 PoP 로 적층됩니다(DIMM/PMIC/RCD 없이 SoC PMIC 가 전원 공급). 따라서 LPDDR5 MC 는 대역폭뿐 아니라 **실시간 QoS(Display/ISP underrun 방지)** 와 **DVFSC 전력 gear** 를 동시에 책임집니다.
:::

---

## 2. Intuition — 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**Memory Controller scheduler** ≈ **도로의 신호 제어기 + 회전 교차로 우선순위**.<br>
여러 master 의 read/write 요청을 받아 bank 충돌, refresh, bus turnaround 를 고려해 발행 순서를 결정. **FR-FCFS** 같은 정책으로 throughput 과 fairness 의 균형을 잡습니다 — 빨간불에 차를 세워 두는 것 같아 보여도 사실은 _전체 처리량_ 을 위한 결정.
:::
### 한 장 그림 — MC 가 만드는 변환

```d2
direction: down

HOST: "input side (host)" {
  direction: right
  CPU: "CPU"
  GPU: "GPU"
  DMA: "DMA"
  DISP: "Display"
  ISP: "ISP"
}
MC: "Memory Controller" {
  direction: down
  RQ: "① RQ 수집\n주소 디코드"
  SCH: "② Row buffer 추적\ntiming 체크"
  OPT: "③ FR-FCFS 재배치\nRefresh / Write batching"
  CMD: "④ 명령 발행\n(ACT/RD/WR/PRE/REF)"
  RQ -> SCH
  SCH -> OPT
  OPT -> CMD
}
DRAM: "output side (DRAM)" {
  DEV: "DRAM device(s)"
}
HOST -> RQ: "AXI"
CMD -> DEV: "DDR phy / CA bus"
```

### 왜 이렇게 설계됐는가 — Design rationale

세 가지 동시 요구가 있습니다.

1. **Functional correctness** — 모든 timing constraint (tRCD = ACT→RD 최소 간격, tRP = PRE→ACT, tRAS = ACT→PRE 최소, **tFAW** = Four Activate Window — 임의의 한 시간 창 안에서 ACT 를 최대 4번으로 제한하는 전류 보호 규칙, tREFI = refresh 주기 ...) 를 위반하지 않아야 한다 → DRAM model(DUT 대신 정답 타이밍/데이터를 흉내 내는 참조 모델)의 contract.
2. **Maximum throughput** — Row Hit 극대화 + Bank-level Parallelism + tCCD_S 활용 + R/W batching → 효율을 nominal BW 의 80~95% 까지.
3. **Fairness / QoS** — 어떤 master 도 starvation 되지 않고, 실시간 master (Display) 는 deadline 을 놓치지 않아야 한다.

이 셋은 서로 trade-off 관계입니다. FR-FCFS 는 ①+② 에 강하지만 ③ 이 약하고, strict round-robin 은 ③ 에 강하지만 ② 가 약합니다. 그래서 실제 MC 는 _두 단계 (QoS Arbiter → Cmd Scheduler)_ 로 분할해 각 단계가 다른 목적을 책임집니다 — §5 의 블록도가 이 분할입니다.

---

## 3. 작은 예 — 네 개 AXI 요청을 FR-FCFS 로 재배치하기

가장 단순한 시나리오. AXI(AMBA AXI — ARM 이 정의한 SoC 내부 표준 버스 프로토콜로, CPU·GPU 같은 master 가 메모리/주변장치에 read/write 요청을 보내는 통로) 4 개의 read request 가 거의 동시에 도착했고, MC 는 FR-FCFS + open-page 정책입니다 (아래 cycle 수는 LPDDR5 한 gear 를 가정한 대표 예시). 여기서 **master**(마스터)는 메모리를 요청하는 주체(CPU, GPU, DMA 등)를, **AXI ID** 는 같은 요청자가 보낸 트랜잭션을 묶는 식별자를 뜻합니다. 현재 bank 상태: Bank 0 에 Row 5 가 open, 나머지 bank 는 idle.

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
// FR-FCFS pseudo code — 매 cycle 호출
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

:::note[여기서 잡아야 할 두 가지]
**(1) FR-FCFS 의 본질은 "Hit 부터 짜내고 Conflict 는 가장 뒤로"**. Row Hit 두 번 (① 와 ④) 사이에 ② 의 PRE/ACT 를 끼워 넣으면 Hit 의 가속을 잃기 때문. <br>
**(2) 다른 BG 는 _완전히_ 병렬**. ③ 의 ACT 가 `T=4` 에 발행돼도 ① 의 데이터 회수와 타임라인이 겹칩니다. 이것이 BG interleaving 으로 effective BW 를 늘리는 메커니즘.
:::
---

## 4. 일반화 — MC 의 책임 과 스케줄링 축

### 4.1 MC 가 하는 일 — 단일 책임 → 다층 책임

| Layer | 책임 | 대표 알고리즘 / 정책 |
|------|------|---------|
| **Address Mapping** | 물리주소 → (Rank, BG, Bank, Row, Col) | row:bg:bank:col 등 (§5.7) |
| **QoS Arbiter** | master 간 priority / fairness / urgency (QoS = Quality of Service, 서비스 품질 — 어떤 master 에게 얼마만큼의 대역폭·우선순위를 보장할지 정하는 규칙) | priority + aging + urgent + BW regulation (§5.4) |
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

:::note[mobile LPDDR5 MC 의 무게중심]
LPDDR5 MC 는 전통적인 throughput 스케줄러(FR-FCFS, BG interleaving, refresh engine) 위에 **실시간 QoS 레이어 + DVFSC 전력 레이어**를 얹은 형태입니다. 모바일 SoC 에 통합되어 있어 다음이 특징입니다.

| 축 | mobile LPDDR5 MC |
|---|---|
| 1차 목표 | 실시간 QoS(Display/ISP underrun 방지) + 저전력, 그 위에서 대역폭 |
| 결정적 master | Display / ISP (frame/line deadline) + CPU/GPU |
| 전력 관리 | **DVFSC gear(F0~F4)** + **Deep Sleep** + **PASR** |
| refresh | per-bank + **PASR**(부분배열) |
| 폼팩터 | PoP 적층, **DIMM/PMIC/RCD 없음**(SoC PMIC) |
:::

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
  REF: "Refresh Engine\n· Periodic REF\n· Postpone/Pull\n· Per-bank REF + PASR (LPDDR5)"
  PM: "Power/DVFSC Manager\n· gear F0~F4 전환\n· Deep Sleep / Self-Refresh\n· WCK on/off"
  PHY: "PHY Interface\n· CA(저속) + CK/WCK(고속) 구동\n· DQ 데이터 버스 제어\n· Training(CBT/WCK2CK/DQ) 제어"
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

Bank-level Parallelism 의 핵심은 "서로 다른 Bank 는 완전히 독립적으로 동작한다"는 물리적 사실입니다. Bank 0 이 tRCD 를 기다리는 동안 Bank 1 은 이미 RD 명령을 실행할 수 있고, Bank 2 는 PRE 를 진행할 수 있습니다. MC 스케줄러는 이 독립성을 최대한 활용하여 여러 Bank 의 ACT → RD → PRE 시퀀스를 파이프라인처럼 겹쳐 실행하고, 그 결과 대역폭 활용을 극대화합니다.

```
Bank 0: ACT ── RD ── PRE
Bank 1:    ACT ── RD ── PRE
Bank 2:       ACT ── RD ── PRE
Bank 3:          ACT ── RD ── PRE
```

여기에 Bank Group 의 계층이 추가되면 인터리빙 효율이 더 올라갑니다. 같은 BG 내 Bank 들은 I/O 회로를 공유하므로 연속 CAS 사이에 tCCD_L 이라는 긴 간격이 필요하지만, 다른 BG 의 Bank 에서 받은 CAS 는 독립 회로를 사용하므로 tCCD_S 의 짧은 간격으로 이어붙일 수 있습니다. 따라서 MC 스케줄러가 연속 access 를 다른 BG 로 분산할수록 처리량이 높아집니다 — LPDDR5 가 BG 모드에서 Bank Group interleaving 을 지원하는 이유가 바로 이 분산 기회를 얻기 위해서입니다.

### 5.4 QoS (Quality of Service) / Arbitration

실제 mobile SoC(LPDDR5 가 붙는 환경)에서는 CPU, GPU, DMA, Display, ISP 같은 여러 마스터가 동시에 메모리를 요청합니다. QoS 는 특히 **LPDDR5/mobile 의 핵심 관심사**입니다 — Display 와 ISP 는 프레임/라인 deadline 을 가진 실시간 master 라, MC 가 이를 보장하지 못하면 즉시 화면 깨짐(Display Underrun)이나 카메라 프레임 드롭으로 사용자에게 노출되기 때문입니다. 그런데 이들의 요구사항은 서로 충돌합니다. CPU 는 캐시 미스 지연을 최소화해야 하므로 낮은 latency 를 원하고, GPU 는 큰 블록을 연속으로 전송해야 하므로 높은 bandwidth 를 원하며, Display 는 1 프레임 단위로 반드시 데이터를 확보해야 하므로 보장된 bandwidth 와 deadline 이 필요합니다. FR-FCFS 같은 스케줄러만으로는 이 다양한 요구를 모두 충족할 수 없습니다 — 우선순위 없이 Row Hit 만 따르면 Display 처럼 랜덤 패턴을 쓰는 마스터가 굶어 죽게(starvation) 되기 때문입니다. 그래서 MC 에는 QoS Arbiter 가 별도로 존재하여 마스터별 우선순위, 대역폭 할당, aging 승격, Urgent 처리를 담당합니다.

여기서 starvation 이 _우연한 부작용_ 이 아니라 FR-FCFS 정책 _구조 자체_ 에서 나온다는 점이 중요합니다. FR-FCFS 는 매 cycle "지금 Row Hit 인 요청을 먼저" 라는 규칙을 무조건 적용합니다. 그런데 순차 패턴(GPU 텍스처 스트림, CPU 캐시라인 prefetch)을 쓰는 마스터는 한 번 Row 를 열면 그 안에서 Hit 를 계속 만들어 내므로 큐의 맨 앞을 끝없이 차지합니다. 반대로 랜덤·소량 패턴을 쓰는 마스터(Display, 포인터 추적형 CPU 워크로드)는 매 요청이 다른 Row 라 거의 항상 Row Miss/Conflict 입니다. 즉 "Hit 우선" 이라는 한 줄의 규칙이, miss 만 내는 마스터를 **영구적으로 후순위로 밀어내는** 편향을 만듭니다 — 트래픽이 멈추지 않는 한 그 마스터의 차례는 영원히 오지 않습니다. 그래서 Hit 효율을 살리되 후순위 마스터를 구제하려면, 대기 시간을 추적해 일정 시간이 지나면 강제로 우선순위를 올리는 **aging** 같은 보정 장치가 필수가 됩니다.

SoC 의 여러 마스터는 요구사항이 서로 다릅니다.

| 마스터 | 특성 | 요구사항 |
|--------|------|----------|
| CPU | 짧은 Burst, 랜덤 | 낮은 Latency (최우선) |
| GPU | 긴 Burst, 순차 | 높은 Bandwidth |
| Display | 주기적 읽기 | 보장된 Bandwidth (끊기면 화면 깨짐) |
| DMA | 대용량 전송 | 높은 Bandwidth, Latency 관대 |
| ISP | 실시간 스트림 | 보장된 Latency |

QoS Arbiter 는 이 상충하는 요구를 네 가지 메커니즘으로 조정합니다.

1. **우선순위 기반 (Priority-based)** — 각 AXI 포트에 QoS 레벨(AxQOS[3:0])을 할당하고, 높은 우선순위 요청을 Command Queue 에서 먼저 스케줄링합니다. 단점은 저우선순위 마스터의 기아(starvation) 가능성입니다.
2. **Bandwidth 할당 (Bandwidth Regulation)** — 각 마스터에 최소 보장 대역폭을 설정하고, 할당량을 초과하는 마스터는 throttle 합니다. Display 같은 실시간 마스터에 필수입니다.
3. **Latency QoS (Aging)** — 요청이 큐에서 대기하는 시간을 모니터링하여, 임계값을 넘으면 우선순위를 자동 승격합니다. CPU 캐시 미스 지연 최소화에 중요합니다.
4. **Urgent 시그널** — Display FIFO 가 거의 비면 Urgent 가 발생하고, MC 가 즉시 해당 요청을 최우선 처리하여 Underrun(화면 깨짐)을 방지합니다.

MC Arbiter 의 대략적 구조는 다음과 같습니다.

```d2
direction: down

MASTERS: "Masters" {
  direction: right
  CPU: "CPU Port"
  GPU: "GPU Port"
  DISP: "Display Port"
}
ARB: "QoS Arbiter\n· Priority check\n· Bandwidth regulation\n· Aging / Urgent"
CQ: "Cmd Queue\n(FR-FCFS 스케줄링)"
CPU -> ARB
GPU -> ARB
DISP -> ARB
ARB -> CQ
```

### 5.5 Read-Write Turnaround — 숨은 성능 병목

DQ 버스는 단방향이 아니라 양방향입니다. Read 는 DRAM → MC 방향, Write 는 MC → DRAM 방향으로 데이터가 흐릅니다. 그러므로 Read 다음에 Write 를 발행하거나, Write 다음에 Read 를 발행하려면 버스 방향을 전환하는 시간이 반드시 필요합니다. Write → Read 전환 시 tWTR, Read → Write 전환 시 tRTW 라는 대기 시간이 삽입됩니다. 그리고 이 전환이 빈번하게 일어날수록 유효 대역폭이 줄어듭니다. MC 가 Write Batching 을 통해 Write 요청을 모아 연속으로 발행하는 이유가 바로 이 전환 횟수를 최소화하기 위해서입니다.

tWTR 이 단순한 "버스 방향 전환 시간" 이상인 이유는 데이터 위험(data hazard)에 있습니다. WR 명령에서 DQ 로 들어온 데이터는 곧바로 cell 에 안착하지 않습니다 — DRAM 내부에서 write driver 가 그 값을 해당 row 의 sense amplifier 를 거쳐 cell capacitor 에 실제로 써넣는 **internal write** 에 시간이 걸립니다. 만약 이 internal write 가 끝나기 전에 같은 위치를 RD 하면, sense amp 에는 아직 _옛값_ 또는 _쓰는 중인 불안정한 값_ 이 있어 stale 데이터를 읽게 됩니다. tWTR 은 바로 "방금 쓴 데이터가 cell 에 확정될 때까지 read 를 막아 두는" 최소 시간이며, 그래서 단순한 버스 turnaround 보다 길고 같은 BG(tWTR_L) 일 때 더 깁니다 — 같은 I/O 경로를 재사용해야 하기 때문입니다.

전환 지연은 방향에 따라 두 가지입니다.

- **Read → Write (tRTW)**: Read 완료 후 DQ 방향 전환 + preamble 시간이 필요합니다.
- **Write → Read (tWTR)**: Write 데이터가 cell 에 확정된 후에만 Read 가 가능합니다. 같은 BG 는 `tWTR_L`(길다), 다른 BG 는 `tWTR_S`(짧다)로 구분됩니다.

```
타임라인:
  ... WR ──[tWTR_L]── RD ...   ← 같은 BG: 긴 대기
  ... WR ──[tWTR_S]── RD ...   ← 다른 BG: 짧은 대기
  ... RD ──[tRTW]─── WR ...    ← 방향 전환 대기
```

MC 스케줄러는 이 전환 횟수를 줄이려고 **Write Batching** 을 씁니다 — Write 요청을 모아 연속 발행한 뒤 Read 로 넘어가는 "Write Drain" 정책이고, Write Buffer 의 High/Low Watermark 로 drain 시점을 결정합니다.

```
  WR WR WR WR ──[tWTR]── RD RD RD RD ──[tRTW]── WR WR WR
  └── Write Batch ──┘     └─ Read Batch ─┘      └ Write Batch
  → 전환 2번 (매번 전환 시 8번 대비 절감)
```

:::note[면접 포인트 — Watermark 트레이드오프]
R/W 턴어라운드 비용을 줄이려 MC 는 Write Batching 을 쓰고, Write Buffer 의 Watermark 로 Write Drain 시점을 결정합니다. 이 Watermark 설정이 Latency(낮을수록 좋음)와 Bandwidth(높을수록 좋음)의 트레이드오프를 결정합니다.
:::

### 5.6 Reorder Buffer / Write Coalescing / RAW bypass

MC 는 AXI 요청을 도착 순서대로 처리하지 않고 **Out-of-Order** 로 재배치합니다.

- **Reorder Buffer (ROB)** — 수신한 AXI 요청을 ROB 에 저장하고, DRAM 상태(Row Buffer, Bank 가용성)에 따라 최적 순서로 재배치합니다. Row Hit 명령을 먼저, Row Conflict 는 나중에 발행하되 **같은 AXI ID 안의 순서는 반드시 보존** 합니다.
- **Write Coalescing (쓰기 병합)** — Write Buffer 에서 같은 주소(같은 Cache Line)에 대한 여러 Write 를 병합해 최종 값만 1회 전송합니다. 예: 같은 주소에 `a=1, a=2, a=3` 이면 `a=3` 만 DRAM 에 전송.
- **RAW Bypass** — Write Buffer 에 있는 데이터를 Read 가 요청하면, DRAM 접근 없이 Write Buffer 에서 직접 forward 합니다.

```
AXI 요청 도착 순서        DRAM 발행 순서(재배치)
  A: Bank0, Row 5    →    B: Bank0, Row 5  (Row Hit → 우선)
  B: Bank0, Row 5         A: Bank0, Row 5  (같은 Row → 연속)
  C: Bank1, Row 3         C: Bank1, Row 3  (다른 Bank → 병렬)
  D: Bank0, Row 7         D: Bank0, Row 7  (Row Conflict → 후순위)
```

RAW bypass 가 단순한 latency 최적화가 아니라 **correctness** 를 위한 필수 동작이라는 점을 짚어야 합니다. MC 는 R/W turnaround 비용 때문에 write 를 Write Buffer 에 모아 두었다가 나중에 drain 합니다. 그 사이에 같은 주소로 read 가 들어오면, DRAM 셀에는 _아직 drain 되지 않은 옛값_ 이 들어 있습니다 — 가장 최신 값은 DRAM 이 아니라 Write Buffer 안에 있습니다. 만약 이 read 를 그냥 DRAM 으로 보내면 방금 쓴 값을 보지 못하고 stale 데이터를 돌려주어 프로그램의 read-after-write 순서 의미가 깨집니다. 그래서 MC 는 read 주소가 Write Buffer 의 pending write 와 겹치는지 검사하고, 겹치면 DRAM 대신 Write Buffer 의 값을 직접 forward 합니다. 즉 "buffer 의 값이 DRAM 보다 최신" 이라는 사실이 forwarding 을 _선택이 아니라 의무_ 로 만드는 것입니다.

### 5.7 Address Mapping (인터리빙)

물리 주소의 어느 비트를 Rank·BG·Bank·Row·Col 에 할당하느냐에 따라 연속 주소가 어느 Bank 에 분산되는지가 결정되고, 그 결과가 workload 의 Row Hit 률과 대역폭을 크게 바꿉니다. 그 메커니즘의 핵심은 "주소의 **하위 비트일수록 연속 접근에서 빠르게 변한다**" 는 사실입니다. CPU 가 메모리를 순차로 훑으면 주소는 1씩 증가하므로 LSB 쪽이 가장 자주 바뀝니다. 따라서 어떤 주소 비트를 어느 필드로 보내느냐가 곧 "연속 접근을 한 Row 에 모을지(집중), 여러 Bank/BG 로 흩뿌릴지(분산)" 를 결정합니다 — 자주 바뀌는 하위 비트를 Column 에 두면 연속 접근이 같은 Row 안에 머물러 Row Hit 가 쌓이고(집중), 같은 하위 비트를 Bank/BG 필드에 두면 연속 접근이 매번 다른 Bank/BG 로 튀어 Bank parallelism·tCCD_S 를 얻습니다(분산). 같은 주소 스트림이라도 이 비트 배치 하나로 Row Hit 율과 병렬성이 정반대로 갈리는 것입니다. 순차 접근이 주를 이루는 경우에는 같은 Row 에 연속으로 접근하는 패턴이 유리하여 Row 인터리빙이 적합하고, 랜덤 접근이 많은 경우에는 연속 주소를 다른 BG 로 분산하는 Bank Group 인터리빙으로 tCCD_S 를 활용하는 것이 유리합니다. SoC 의 주요 마스터(CPU 캐시 라인 순차 패턴, GPU 랜덤 텍스처 패턴)가 혼재하기 때문에 실무에서는 매핑 방식을 configurable 레지스터로 설계하고 테스트 후 결정합니다.

물리 주소를 Rank/BG/Bank/Row/Col 로 매핑하는 대표 방식은 다음과 같습니다.

| 방식 | 배치 | 효과 | 유리한 접근 |
|------|------|------|------|
| Row 인터리빙 | `Row : Bank : Column` | 연속 주소가 같은 Bank·Row → Row Hit ↑ | 순차 접근 |
| Bank Group 인터리빙 | `Row : BG : Bank : Column` | 연속 주소가 다른 BG → tCCD_S 활용 → 대역폭 ↑ | 랜덤 접근 |
| Bank 인터리빙 | `Bank : Row : Column` | 연속 주소가 다른 Bank → Bank Parallelism ↑ | 혼합 접근 |

실무에서는 SoC 트래픽 패턴에 따라 최적 매핑이 달라지므로 configurable 레지스터로 설계하고 테스트 후 결정합니다.

### 5.8 Refresh 관리

커패시터가 전하를 잃지 않으려면 평균 tREFI 간격마다 REF 명령을 발행해야 합니다(LPDDR5 tREFI ≈ 3.9 µs, 온도 가변). 여기서 tREFI 는 tCK 가 아니라 ns/µs 단위, tRFC 는 밀도에 의존하는 ns 단위임에 주의하세요. Refresh 가 진행되는 동안 해당 array 는 tRFC(밀도 의존, 수백 ns) 동안 묶여 접근이 막힙니다. 게다가 MC 가 트래픽이 바쁠 때 refresh 를 뒤로 미루다(postpone) 가 JEDEC 허용 한도를 초과하면 한꺼번에 여러 REF 가 직렬로 발행되는 "refresh storm" 이 발생해 BW 가 절벽처럼 떨어집니다. LPDDR5 는 이를 두 가지로 완화합니다 — **per-bank refresh(REFpb)** 로 한 Bank 만 refresh 하는 동안 나머지 Bank 를 계속 사용하고, **PASR**(Partial Array Self-Refresh) 로 실제 데이터를 담고 있는 뱅크/세그먼트만 self-refresh 하고 빈 영역은 refresh 를 생략해 전력을 절감합니다. 공통적으로 한가한 시점에 미리 refresh 를 당겨(pull-in) 발행하는 기법도 사용합니다.

LPDDR5 MC 의 refresh 관리 요점은 다음과 같습니다.

- **per-bank refresh (REFpb)** — 한 Bank 만 tRFC 동안 묶고 나머지 Bank 는 정상 접근 → 유효 BW 손실 감소.
- **PASR** — 데이터가 있는 뱅크/세그먼트만 self-refresh, 빈 영역은 생략 → 전력 절감(LPDDR 계열 고유).
- **Postpone / Pull-in / Staggering** — 바쁠 때 REF 지연(허용 한도까지 축적), 한가할 때 미리 수행, Rank/Bank 별 REF 시점 분산으로 storm 회피.

### 5.9 DRAM 초기화 시퀀스

전원을 켠 직후 DRAM 은 사용 가능한 상태가 아닙니다. MC 가 정해진 순서대로 초기화 절차를 밟아야 비로소 첫 번째 ACT 명령을 발행할 수 있습니다. 이 절차는 크게 다섯 단계로 나뉩니다. 먼저 전원이 안정화될 때까지 충분히 기다린 뒤(Phase 1), CKE 를 HIGH 로 올려 DRAM 을 활성화하고 Mode Register 명령으로 Burst Length, CAS Latency, ODT 등의 동작 파라미터를 프로그래밍합니다(Phase 2). 다음으로 (필요 시) 임피던스를 초기 보정하고(Phase 3), training 시퀀스를 실행합니다(Phase 4). 마지막으로 refresh 를 시작하면 DRAM 이 정상 동작 상태에 들어갑니다(Phase 5). Mode Register 설정 순서는 JEDEC 스펙에 명시되어 있으며 이 순서를 지키지 않으면 DRAM 이 예상치 않은 상태에 빠질 수 있습니다.

LPDDR5 는 Mode Register 를 **MRW**(Mode Register Write)/**MRR**(Mode Register Read) 명령으로 설정하고, training 으로 **CBT(Command Bus Training, Mode1/2)** 와 **WCK2CK leveling**(WCK-CK 위상 정렬, LPDDR5 고유), 그리고 DQ/Write/Read Training 을 수행합니다. 메모리는 SoC 위에 PoP 로 적층되므로 **DIMM 도, 온보드 PMIC/RCD 도 없고** 전원은 SoC 의 PMIC 가 공급합니다. training 단계(특히 CBT/WCK2CK)가 많다는 것이 LPDDR5 초기화의 특징입니다.

전원 인가 후 첫 사용자 명령까지 MC 가 밟는 절차는 다섯 단계입니다.

1. **전원 안정화** — VDD1/VDD2/VDDQ 인가 후 안정화 대기, CK 시작(CKE=LOW 유지), RESET# 해제 후 대기.
2. **초기화 / Mode Register** — CKE=HIGH 로 활성화 후 **MRW** 로 RL/WL, BL, ODT, WCK 비율, VREF 등을 프로그래밍. 발행 순서는 JEDEC(JESD209-5)에 명시.
3. **ZQ Calibration** — 출력 임피던스 초기 보정, tZQinit 대기.
4. **Training (BL2 에서 수행)** — **CBT → WCK2CK leveling → DQ/Write/Read → Eye/VREF** (Module 03 에서 상세). CBT·WCK2CK 가 LPDDR5 고유 단계.
5. **Refresh 시작** — 초기화 완료 후 평균 tREFI 간격으로 refresh 시작 → DRAM 사용 가능.

### 5.10 Power Management — 전력 상태 머신

```d2
direction: down

INITIAL { shape: circle; style.fill: "#333" }
INITIAL -> Active: ""
Active: "Active\n(정상 동작)"
PowerDown: "Power-Down (PD)"
Idle: "Idle\n(모든 Bank precharged)"
SelfRefresh: "Self-Refresh (SR)"
Active -> PowerDown: "CKE LOW"
PowerDown -> Active: "CKE HIGH"
Active -> Idle: "PRE all"
Idle -> SelfRefresh: "CKE LOW + SRE"
SelfRefresh -> Idle: "SRX"
```

각 전력 상태의 특징은 다음과 같습니다.

| 상태 | 조건 | 복귀 | 절감(vs Active) |
|------|------|------|------|
| **Active Power-Down (APD)** | CKE LOW, Bank Open 유지 | 빠름 (tXP) | ~30–40% |
| **Precharge Power-Down (PPD)** | CKE LOW, 모든 Bank Precharged | 빠름 (tXP) | ~50–60% |
| **Self-Refresh (SR)** | CKE LOW, 내부 자체 Refresh, 외부 클럭 불필요 | 느림 (tXS ≈ tRFC + 마진) | ~90% |

LPDDR5 는 여기에 모바일 고유의 저전력 축을 더합니다.

- **DVFSC (Dynamic Voltage/Frequency Scaling)** — 주파수/전압 gear(F0~F4)를 트래픽에 맞춰 동적 전환합니다. gear 전환 시 WCK:CK 비가 바뀌므로 **WCK2CK 재정렬** 이 필요합니다.
- **Deep Sleep** — SR 보다 더 깊은 절전(컨텍스트 최소 보존).
- **PASR** — 데이터가 있는 영역만 self-refresh 하고 빈 영역은 생략.

**MC 의 역할** — Idle 시간을 모니터링해 적절한 시점에 PD/SR 로 진입하고, 요청이 도착하면 즉시 복귀를 트리거하며, 전환 비용(복귀 latency)과 절감 효과의 균형을 잡습니다. LPDDR5 에서는 DVFSC 와 연계해 주파수+전압을 동시 조절하고, gear 전환 후 WCK2CK 재정렬을 PHY 와 협조하여 트리거합니다.

### 5.11 주요 DRAM 명령

| 명령 | 기능 | 주요 타이밍 |
|------|------|-----------|
| ACT (Activate) | Row를 Row Buffer에 로드 | tRCD 후 RD/WR 가능 |
| RD (Read) | Column 주소로 데이터 읽기 | tCL 후 데이터 출력 |
| WR (Write) | Column 주소로 데이터 쓰기 | tWL 후 데이터 수신 |
| PRE (Precharge) | Row Buffer 닫기 | tRP 후 ACT 가능 |
| REF (Refresh) | 전체/Bank 리프레시 (LPDDR5 per-bank REFpb) | tRFC 동안 접근 불가 |
| MRW / MRR (Mode Register Write/Read) | DRAM 설정 쓰기/읽기 | 초기화·training 시 사용 |
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

**Q: LPDDR5 초기화 시퀀스의 핵심 단계는?**
> "전원 안정화 → RESET 해제 → CKE 활성화 → Mode Register 프로그래밍(BL, RL/WL, ODT, WCK 비율 등)을 MRW 명령으로 → ZQ 보정 → Training → Refresh 시작. LPDDR5 는 Training 에 CBT + WCK2CK leveling(LPDDR5 고유)이 포함되고, DIMM/PMIC/RCD 없이 SoC PMIC + PoP 적층으로 동작한다. 설정 순서는 JEDEC(JESD209-5)에 명시되며, Training 은 코드량이 크고 PVT 의존적이어서 BootROM 이 아닌 BL2 에서 수행한다."

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'Open-page 정책이 항상 좋다']
**실제**: Open-page 는 row hit 시 빠르지만 row conflict 시 `tRP+tRCD` 페널티가 큽니다. random/streaming workload 에서 close-page 또는 adaptive 가 더 좋을 수 있습니다.<br>
**왜 헷갈리는가**: "row 열어 두면 다음에 빠름" 만 보고 row conflict 페널티는 직관에 잘 안 들어와서.
:::
:::danger[❓ 오해 2 — 'AXI 요청은 도착 순서대로 처리된다']
**실제**: MC 는 ROB 로 의도적으로 _Out-of-Order_ 처리합니다. 단 같은 AXI ID 안의 순서만 보장. 이 사실을 모르고 응답 순서를 가정하는 master 는 deadlock / data hazard 를 일으킬 수 있습니다.<br>
**왜 헷갈리는가**: "메모리 = 순차 모델" 이라는 software 측 직관 때문.
:::
:::danger[❓ 오해 3 — 'Write Batching 이 길수록 throughput 이 높다']
**실제**: Write batch 가 길면 R/W 전환은 줄지만 그 동안 _read latency tail_ 이 폭발합니다. CPU 의 cache miss latency 는 OS scheduling 까지 영향. Watermark 는 BW 와 latency 의 정밀한 균형점.
:::
:::danger[❓ 오해 4 — 'QoS 우선순위만 잘 주면 starvation 없다']
**실제**: Strict priority 는 저우선순위 master 의 _완전 starvation_ 을 만듭니다. Aging counter 가 명령 대기 시간을 추적하고, 임계값을 넘으면 priority 를 자동 승격해야 starvation 이 방지됩니다.
:::
:::danger[❓ 오해 5 — 'Refresh 는 그냥 주기적인 background. MC 가 신경쓸 일 적음']
**실제**: Postpone 가 누적되면 한 번에 8 REF 직렬 발행 → BW 절벽. 또 tREFI 위반은 Row Hammer 보안 취약점으로 직결. MC 의 refresh 엔진은 staggering / pull-in 을 신중히 설계합니다.
:::
### DV 디버그 체크리스트 (MC 검증 시 자주 보는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 평균 BW 정상이나 burst 단위로 급락 | tFAW 4-ACT 한도 초과 / Refresh storm | tFAW 타이밍 체커, refresh queue depth 그래프 |
| Read latency tail 이 길다 (p99) | Write batching watermark 가 너무 높음 / starvation | Write drain timestamp, aging counter |
| 같은 row 인데 Row Hit 가 안 됨 | bank state tracker 에 PRE 누락 / open-row 갱신 버그 | bank tracker dump, ACT/PRE 로그 |
| AXI ID 순서가 깨짐 | ROB 가 같은 ID 응답을 reorder | ROB rule check, ID-별 timestamp |
| Display Underrun (FIFO empty) | Urgent signal 미인식 / BW regulation 부족 | Urgent assertion 발생, Display 트래픽 BW 측정 |
| tCCD_L 이 적용돼야 할 자리에 tCCD_S 발행 | bank-group bit 매핑 mismatch | address mapper 의 BG 추출 logic |
| Refresh interval 이 점점 길어짐 | postpone 카운터 race / pull-in 실패 | refresh issue timestamp 와 tREFI 비교 |
| Write 후 즉시 Read 시 stale value | RAW bypass forward 누락 | write buffer 의 read-forward path |

:::caution[실무 주의점 — tFAW 위반으로 Rank 내 동시 ACT 과전류 위험]
**현상**: 짧은 시간 내에 서로 다른 Bank에 4개 초과의 ACT 명령이 발행되어 DRAM의 순간 전류가 스펙을 초과, 전압 강하(Vdd Droop)로 인한 데이터 오류 발생.

**원인**: tFAW(Four Activate Window)는 임의의 tFAW 시간 창 내에 ACT를 최대 4회로 제한함. MC 스케줄러가 Bank 병렬화 극대화를 추구하다가 tFAW 윈도우를 무시하고 5번째 ACT를 발행할 수 있음. Open Page Policy에서 Row Conflict가 많은 워크로드일수록 ACT 빈도가 높아 위험 증가.

**점검 포인트**: 타이밍 체커(절차적 SV — MC 레벨에서는 gear 에 따라 tCK 가 바뀌므로 ns 기준 체커가 적합, Module 04 §5.7)에서 tFAW window 감시가 동작하는지 확인. 시뮬레이션 파형에서 슬라이딩 윈도우(tFAW 길이) 내 ACT 명령 수 카운트. 랜덤 워크로드 시 Bank 분산 패턴을 로그로 수집하여 tFAW 위반 발생 seed 식별.
:::
---

## 7. 핵심 정리 (Key Takeaways)

- **MC = scheduler + 명령 변환기**: AXI request → ACT/RD/WR/PRE/REF 시퀀스로 변환하면서 모든 timing 종속성을 보장.
- **Row Hit 극대화**: 같은 row 연속 access 면 PRE/ACT 회피 → throughput ↑ — FR-FCFS 의 핵심.
- **Bank-level parallelism + BG interleaving**: 다른 bank/BG 에 동시 ACT 가능. tCCD_S 활용으로 latency 겹침.
- **Write batching + RAW bypass + ROB**: R↔W 전환 비용 회피, 단 latency tail 과의 trade-off.
- **Refresh scheduling**: 평균 tREFI 보장 + traffic 영향 최소화. LPDDR5 = **per-bank(REFpb) + PASR**(LPDDR 고유).
- **QoS (mobile LPDDR5 핵심)**: AXI QoS field + Aging + Bandwidth Regulation. Display/ISP 같은 실시간 master 는 Urgent 우선 — underrun 방지.
- **전력 (mobile LPDDR5)**: PD/SR 위에 **DVFSC gear(F0~F4)** + **Deep Sleep** + **PASR**. gear 전환 시 WCK2CK 재정렬 필요.
- **초기화**: LPDDR5 = MRW + CBT/WCK2CK training, DIMM/PMIC/RCD 없음(SoC PMIC, PoP 적층).

:::caution[실무 주의점]
- 평균 BW 가 정상이라도 latency tail / starvation 은 별도로 감시.
- Open-page 는 random workload 에서 _역효과_ 가능 — workload profiling 필수.
- Refresh 정책은 Module 01 의 cell physics 와 직결 — RFM/Row Hammer 와 반드시 함께 검증.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — FR-FCFS vs round-robin (Bloom: Analyze)]
Multi-master DRAM (CPU + GPU + Display). FR-FCFS 정책이 _Display starvation_ 가능?

<details>
<summary>정답</summary>

가능. FR-FCFS 는 _row-hit_ 우선 — Display 의 _random pattern_ 은 항상 row-miss → 우선순위 낮음.

해법: **QoS + Aging**:
- Display request 의 _AXI QoS_ field 가 high.
- _Aging counter_: 오래된 request 자동 priority 상승.
- 두 가지로 starvation 방어 + row-hit 효율 둘 다.

</details>
:::
:::tip[🤔 Q2 — Scheduler 비교 (Bloom: Evaluate)]
Open-page FR-FCFS vs Close-page Round-Robin. 어느 workload?

<details>
<summary>정답</summary>

- **HPC/AI** (sequential, high reuse): Open + FR-FCFS. row hit ↑.
- **OLTP database** (random small reads): Close + Round-Robin. row miss 어차피 많음, fairness 중요.
- **Hybrid (modern SoC)**: 동적 정책 전환 — workload 측정 후 5초마다 재결정.

</details>
:::
### 7.2 출처

**External**
- JEDEC **JESD209-5** *LPDDR5/5X*
- Mutlu et al. *Memory Scheduling* 논문들

---

## 다음 모듈

→ [Module 03 — Memory Interface / PHY](../03_memory_interface_phy/): MC 의 명령이 _전기 신호_ 가 되는 layer. DLL/PLL, ODT, equalization, training. ns-단위 timing margin 의 영역.

[퀴즈 풀어보기 →](../quiz/02_memory_controller_quiz/)

