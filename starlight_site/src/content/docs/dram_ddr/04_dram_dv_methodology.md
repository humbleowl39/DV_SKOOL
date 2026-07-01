---
title: "Module 04 — LPDDR5 DV Methodology"
---

:::tip[학습 목표]
이 모듈을 마치면 (주제: **LPDDR5**):

- **Design** LPDDR5/MC 검증 환경 (Behavioral Model + Traffic Generator + Reference Scoreboard) 아키텍처를 설계할 수 있다 — bank mode(BG/8B/16B), WCK/CK 분리, gear(DVFSC) 축 포함.
- **Apply** gear-dependent Timing Compliance Check 를 **절차적 SV 타이밍 체커(ns/`$realtime` 기준)** 로 구현하고, per-bank refresh + PASR, On-die ECC 와 Link ECC 를 분리한 injection 시나리오를 작성할 수 있다.
- **Implement** Performance Reference 로 Bandwidth / Latency 회귀 + 모바일 실시간 deadline(Display/ISP underrun 방지) scoreboard 를 구현할 수 있다.
- **Plan** LPDDR5 Training 시퀀스 (CBT, WCK2CK leveling, DVFSC gear 전환 시 WCK2CK 재정렬, Deep Sleep entry/exit) 검증 시나리오를 PVT corner 와 함께 수립할 수 있다.
- **Justify** 어떤 실패가 TB bug 인지 DUT bug 인지 분류 기준을 제시하고, MC/subsystem 레벨 timing 검증에서 절차적 SV 와 SVA 를 언제 각각 쓰는지 설명할 수 있다.
:::
:::note[사전 지식]
- [Module 01-03](../01_dram_fundamentals_ddr/) (cell + MC + PHY 전반)
- UVM 기본 (factory, sequence, scoreboard, agent)
- SystemVerilog 절차적 코드 + SVA 기본
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _Silent corruption_ 의 비싼 대가

DRAM 검증은 일반 IP DV(Design Verification, 설계 검증 — 만든 하드웨어가 명세대로 동작하는지 시뮬레이션으로 확인하는 일)와 _근본적으로_ 다릅니다. 이 모듈에 등장하는 검증 용어를 먼저 풀어 둡니다 — **DUT**(Design Under Test, 검증 대상 설계 = 여기서는 MC+PHY), **TB**(testbench — DUT 에 자극을 주고 결과를 채점하는 검증 환경), **UVM**(Universal Verification Methodology — SystemVerilog 기반의 표준 검증 프레임워크), **scoreboard**(스코어보드 — DUT 출력과 "정답"을 비교해 일치 여부를 판정하는 컴포넌트), **SVA**(SystemVerilog Assertion — "이 조건은 항상 참이어야 한다"를 코드로 박아 위반 즉시 잡아내는 검사문), **behavioral model**(동작 모델 — 실제 DRAM 대신 명세대로 타이밍·데이터를 흉내 내는 참조 모델), **traffic generator**(트래픽 생성기 — 다양한 read/write 패턴을 만들어 DUT 에 흘려보내는 자극원). 일반 IP:
- Functional test 통과 → silicon 에서도 거의 OK.

DRAM:
- Functional test 통과 → silicon 에서 _가끔_ 데이터 깨짐. **Silent corruption**.

이유는 DRAM 의 구조적 특수성에서 나옵니다. tRC, tRCD, tRP, tRAS, tFAW 등 수십 개의 timing parameter 가 존재하고, 이 중 하나라도 특정 명령 조합에서 위반되면 실리콘에서 간헐적 fail 이 발생합니다. LPDDR5 에서는 이 timing 들이 **gear(DVFSC) 의존** 이어서, F0↔F4 같은 gear 전환 시 WCK:CK 비율(2:1↔4:1)이 바뀌고 WCK2CK 재정렬이 끝나기 전에 데이터를 발행하면 또 다른 silent corruption 이 생깁니다. 더 어려운 것은 이 fail 이 silent — 장치는 동작하는 것처럼 보이지만 특정 address 의 데이터가 조용히 손상됩니다. On-die ECC / Link ECC, per-bank refresh + PASR, Deep Sleep entry/exit, training 실패 복구 같은 stateful 시나리오는 무작위 입출력 테스트로는 재현조차 되지 않습니다. 2014 년에 알려진 Rowhammer 공격이 대표적인 사례입니다 — refresh interval 이 허용 범위 내라고 표시되지만 공격적으로 반복 접근하면 이웃 row 의 전하가 누설되어 비트 플립이 발생했고, 이 취약점이 발견되기까지 수년이 걸렸습니다.

DRAM 검증은 **타이밍 + 무결성 + 성능 의 동시 검증** 입니다. 일반 IP 처럼 "input/output mapping 만 맞으면 OK" 가 아니라 _수십 개의 timing constraint_ (`tRC`, `tRCD`, `tRP`, `tRAS`, `tFAW`, `tREFI`, `tCCD_S/L`, `tWTR`, `tRTW`, `tRFC` ...) 가 _모든 명령 조합_ 에서 충족되어야 합니다. 게다가 ECC injection / refresh 누락 / training 실패 같은 **silent corruption** 시나리오 — 동작은 하지만 데이터가 깨지는 — 를 빠짐없이 다뤄야 합니다.

이 모듈을 건너뛰면 단위 test 는 통과하는데 silicon 에서 random 워크로드가 실패하는 경험을 하게 됩니다. 반대로 이 모듈의 _3축 검증 + protocol checker + performance reference_ 구조를 잡고 나면 어떤 실패가 들어와도 어느 축 (timing / data / perf) 의 문제인지 즉시 분류 가능합니다.

---

## 2. Intuition — 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**DRAM DV** ≈ **도서관 사서 검수 — 모든 책 입출고 시간이 spec 과 일치하는지 stopwatch 검증**.<br>
`tRCD`, `tRP`, `tFAW` 같은 timing 제약을 모두 준수했는지 + refresh / training / scheduler 정책이 모든 시나리오에서 동작하는지 + 성능이 회귀하지 않는지 — 세 stopwatch 를 동시에 들고 보는 작업.
:::
### 한 장 그림 — TB 의 3 stopwatch

```d2
direction: down

DUT: "DUT (MC + PHY)"
HOST: "Host Agent (AXI master)\n· traffic gen\n· QoS / burst"
MODEL: "DRAM Behavioral Model (JEDEC)\n· timing checker\n· refresh model"
SB1: "① Data Stopwatch\nScoreboard:\nAXI W == AXI R\n(data integrity)"
SB2: "② Timing Stopwatch\nProcedural SV timing checker\n(ns/realtime, gear-aware)\n(tRCD, tRP, ...)"
SB3: "③ Perf Stopwatch\nBW / latency\nregressors\nvs reference"
HOST -> DUT: "AXI"
DUT -> MODEL: "DDR IF"
HOST -> SB1: "AXI request/response" { style.stroke-dash: 4 }
HOST -> SB3: "" { style.stroke-dash: 4 }
MODEL -> SB2: "DDR command/data" { style.stroke-dash: 4 }
MODEL -> SB1: "" { style.stroke-dash: 4 }
```

### 왜 이렇게 설계됐는가 — Design rationale

세 가지 실패 모드가 _서로 다른 메커니즘_ 으로 발생합니다.

1. **Data corruption** — bit 가 잘못 read/write. ECC, RAW bypass, address mapping 버그가 원인. → Scoreboard 가 잡음.
2. **Timing violation** — protocol 자체는 맞는데 spec 보다 짧은 간격으로 명령 발행. silicon 에서는 metastable / sense-amp 실패. → 절차적 SV 타이밍 체커(ns 기준, gear-aware)가 잡음 — 고정 클럭 도메인은 SVA 보조.
3. **Performance regression** — 기능은 맞는데 throughput/latency 가 spec 미달. 이건 silent — assertion 안 잡힘. → Performance reference 와의 차이로만 검출.

세 도구를 _분리_ 한 이유는 각각이 _다른 신호_ 를 본다는 것입니다. 통합하려 하면 false-negative 가 늘어 silent fail 이 생깁니다.

---

## 3. 작은 예 — tRCD 위반을 절대시간(ns)으로 잡아내기

가장 단순한 시나리오. DUT 가 ACT 발행 후 `tRCD` 최소 시간을 다 채우기 직전에 RD 를 발행합니다. DRAM 셀에서는 sense amp 가 아직 안정되지 않았으나 silicon 은 _가끔_ 동작합니다 — random data 로 잡기 어려운 silent bug. 이걸 잡는 체커를 어떻게 짜야 할까요?

여기서 **왜 SVA 가 아니라 절차적 SV 로 짜는지** 를 먼저 짚어야 합니다. `tRCD` 는 spec 상 **절대시간(ns) 최소값** 이고, cycle 수는 `ceil(tRCD_ns / tCK)` 로 파생됩니다. LPDDR5 는 DVFSC gear(F0~F4)에 따라 **tCK 와 WCK:CK 비가 런타임에 바뀌므로**, 같은 tRCD_ns 라도 gear 마다 cycle 수가 달라집니다. 그런데 SVA 의 cycle-delay `##N` 이나 반복 `[*N]` 의 `N` 은 **elaboration-time 상수** 여야 합니다(IEEE 1800 §16.7) — 런타임에 바뀌는 gear 값으로 지연 cycle 수를 줄 수 없습니다. 그래서 MC/memory-subsystem 레벨에서는 명령 발행 시각을 `$realtime` 으로 기록하고 **경과 ns 를 현재 gear 의 tRCD_ns 와 직접 비교** 하는 절차적 SV 체커가 정답입니다. gear 가 바뀌어도 그때의 tCK/tRCD_ns 를 읽어 비교하면 되므로 gear 전환·클럭도메인 전환을 자동으로 따라갑니다. (SVA 는 클럭이 고정된 PHY 도메인의 edge 관계나 coverage 에 보조로 씁니다 — §5.7.)

### 단계별 추적

```
   시각    │  t=0ns   ...        t=tRCD-Δ      t=tRCD      t=...
   CMD     │  ACT                 RD ⚠                    
           │  (Bank0,Row5)        (col=0)
           │
   DUT     │  ─ ACT 발행 ─           ─ RD 발행 ──
           │                        ↑ (tRCD_ns 를 다 못 채우고 발행)
           │
   SV체커  │  act_time[b0]=$realtime ─ RD 시각에서 (now - act_time[b0]) 계산
           │                        ↓  (now - act_time[b0]) < TRCD_NS[gear]
           │                        ★ `uvm_error("LPDDR5_TCHK", ...)
```

### 단계별 의미

| Step | 시점 | 누가 | 무엇을 | 왜 |
|---|---|---|---|---|
| ① | `t=0` | DUT | `ACT` (Bank=0, Row=5) 발행 | row open 시작 |
| ② | `t=0` | SV 체커 | `act_time[bank0] = $realtime` 기록 | 절대시각 timestamp |
| ③ | `t=0..tRCD` | DRAM model | sense amp 동작 → row buffer 안정화 진행 중 | `tRCD_ns` 동안 RD/WR 금지 |
| ④ | `t=tRCD-Δ` | DUT | `RD` (col=0) 발행 — 조금 빨리! | scheduler 의 timing 계산 버그 |
| ⑤ | `t=tRCD-Δ` | SV 체커 | `($realtime - act_time[bank0]) < TRCD_NS[gear]` 판정 | 위반 감지 |
| ⑥ | `t=tRCD-Δ` | SV 체커 | `uvm_error("LPDDR5_TCHK", "tRCD violation ...")` | error 보고 |
| ⑦ | post-sim | scoreboard | RD 데이터가 _가끔_ 깨짐 (sense amp 미안정) | 데이터 corruption 도 감지될 수 있으나 random — 타이밍 체커가 더 안정적 |
| ⑧ | post-sim | coverage | tRCD margin bin 이 _violation 근처_ 에 hit 표시 | 회귀 시 동일 시나리오 재현 보장 |

```systemverilog
// MC/subsystem 레벨 tRCD 체크 — 절대시간(ns) 기준, gear-aware (절차적 SV)
// TRCD_NS[gear] : 현재 gear 의 tRCD 최소값(ns). gear 전환 시 갱신되는 배열/함수.
realtime act_time [NUM_BANKS];   // bank 별 마지막 ACT 시각

always @(posedge clk) begin
  if (!rst_n) begin
    // reset: 필요 시 act_time 무효화
  end else begin
    if (act)                       // ACT 발행 시 절대시각 기록
      act_time[{bg, bank}] <= $realtime;

    if (rd || wr) begin            // RD/WR 발행 시 경과 ns 검사
      int b = {bg, bank};
      realtime elapsed = $realtime - act_time[b];
      if (elapsed < TRCD_NS[cur_gear])   // 현재 gear 의 ns 제약과 직접 비교
        `uvm_error("LPDDR5_TCHK",
          $sformatf("tRCD violation @Bank%0d: %.3f ns elapsed < %.3f ns (gear=%0d)",
                    b, elapsed, TRCD_NS[cur_gear], cur_gear))
    end
  end
end
```

:::note[여기서 잡아야 할 세 가지]
**(1) 타이밍 체커가 silent bug 를 _즉시_ 잡는다.** Scoreboard 에 의존했다면 random data 패턴에 따라 corruption 이 발생/미발생 — flaky 한 fail 이 됩니다. 타이밍 체커는 위반 명령이 들어온 그 시점에 fire 합니다.<br>
**(2) 왜 cycle 이 아니라 ns 인가.** 위 체커는 `$realtime` 차이(ns)를 본다. gear 가 바뀌어 tCK 가 달라져도 `TRCD_NS[cur_gear]` 만 갱신하면 그대로 동작한다 — 고정 `##TRCD` SVA 였다면 gear 마다 재-elaborate 하거나 gear 를 얼려야 한다.<br>
**(3) Bank/BG 별로 독립 timestamp 가 필요하다.** `act_time[]` 를 bank 단위로 두고, bank mode 에 맞춰 크기를 잡는다: LPDDR5 BG 모드(4 BG×4=16뱅크) / 8B 모드(8뱅크) / 16B 모드(16뱅크). tRCD_ns 는 gear 단위로 관리.
:::
---

## 4. 일반화 — 3축 검증 과 TB 구성

### 4.1 3축 검증 — 무엇을 어떻게

| 축 | 검증 도구 | 잡는 실패 종류 | 핵심 데이터 |
|---|---|---|---|
| **① Data integrity** | UVM Scoreboard | bit 변조, ECC 실패, RAW bypass 버그 | AXI W data ≡ AXI R data |
| **② Timing compliance** | 절차적 SV 타이밍 체커 (ns/gear-aware) + 고정도메인 SVA 보조 | tRCD/tRP/tRAS/tFAW/tREFI/... 위반 | DDR command `$realtime` timestamp |
| **③ Performance** | Perf scoreboard / regression | BW/latency 회귀, QoS 미달 | request/response timestamp |

### 4.2 TB 의 일반 구성

```d2
direction: down

AXI: "AXI master (host agent)"
DUT: "DUT: MC + PHY"
MODEL: "DRAM Behavioral Model\n(JEDEC compliant + timing checker + refresh + training reply)"
SB: "Scoreboard / Checker\n① data · ② time · ③ perf"
AXI -> DUT
DUT -> MODEL
AXI -> SB { style.stroke-dash: 4 }
DUT -> SB { style.stroke-dash: 4 }
MODEL -> SB { style.stroke-dash: 4 }
```

### 4.3 Coverage axis — "무엇이 빠졌는지"

DRAM 의 시나리오 공간은 폭발적입니다 (rank × BG × bank × row × col × command × interleave × refresh state × training × power state). 그래서 **functional coverage 는 cross 형태로 정의되어야** 빠진 영역을 detect 할 수 있습니다 — §5.4. (**functional coverage** = 기능 커버리지; "어떤 상황을 실제로 테스트해 봤는지"를 세는 척도. **coverpoint** = 세고 싶은 한 항목(예: 명령 종류), **cross** = 두 항목의 조합(예: 명령 × bank)까지 빠짐없이 봤는지 세는 것.)

### 4.4 검증 자료의 분류 — TB bug 인가 DUT bug 인가

| 증상 | TB bug 가능성 | DUT bug 가능성 | 1차 판단 |
|---|---|---|---|
| Scoreboard mismatch | data 변형/모델 불일치 | RAW bypass / ECC / address map | DRAM model 의 expected data 를 직접 quote |
| tRCD 타이밍 위반 | 체커의 TRCD_NS[gear] 오설정 | scheduler 의 timing 계산 | spec/MR 의 tRCD(ns) 와 체커 값, 현재 gear 확인 |
| BW < expected | traffic generator 가 row hit 형성 못함 | scheduler 가 hit 활용 못함 | request 패턴의 row hit 비율 측정 |
| Training fail | DRAM model 의 reply 패턴이 spec 위반 | MC 의 tap 갱신 logic | CBT / WCK2CK leveling 의 transition 위치 확인 |
| Gear 전환 후 data 깨짐 | gear 전환 시 timing param 미갱신 | WCK2CK 재정렬 전 데이터 발행 | gear 전환 시점의 WCK:CK 비율 + WCK2CK done flag 확인 |
| Link ECC 오류인데 On-die 미검출 | injection 위치가 array 가 아닌 DQ link | MC Link ECC 디코더 | 주입 지점이 cell(On-die) vs DQ link(Link ECC) 인지 확인 |

---

## 5. 디테일 — TB, Coverage, Init, Perf, ECC, SVA, Confluence

### 5.1 검증 환경 아키텍처

```d2
direction: down

ENV: "MC / MI UVM Verification Env" {
  direction: down
  HOST: "Host Agent (AXI Master)\n· R/W 트래픽 생성\n· 주소 패턴\n· QoS / Burst"
  MODEL: "DRAM Model (Behavioral)\n· 타이밍 체커\n· 데이터 저장\n· Refresh 모델"
  DUT: "DUT (Memory Controller + PHY)"
  SB: "Scoreboard / Checker\n· 데이터 무결성: AXI Write == AXI Read\n· 타이밍 위반 검사: tRCD, tRP, tCCD, tRAS, tFAW\n· Refresh 주기 준수: tREFI 내 REF 발행\n· Bank 상태 정합성: Open/Close 추적"
  PC: "Protocol Checker (DDR Timing Monitor)\n· DDR VIP 또는 DRAM Behavioral Model 내장 체커\n· 모든 타이밍 파라미터 위반 시 즉시 에러 보고"
  COV: "Functional Coverage"
  HOST -> DUT: "AXI"
  DUT -> MODEL: "DDR IF"
  DUT -> SB { style.stroke-dash: 4 }
  DUT -> PC { style.stroke-dash: 4 }
  DUT -> COV { style.stroke-dash: 4 }
}
```

### 5.2 핵심 테스트 시나리오

#### Positive

| 카테고리 | 시나리오 | 검증 포인트 |
|---------|---------|-----------|
| **기본 R/W** | 단일 주소 Write → Read | 데이터 일치 |
| | 연속 주소 Burst | 정확한 Column 접근 |
| | 전체 주소 공간 | 모든 Rank/BG/Bank/Row 접근 가능 |
| **스케줄링** | Row Hit 패턴 | ACT 없이 RD/WR 연속 |
| | Row Conflict 패턴 | PRE→ACT→RD/WR 시퀀스 정확 |
| | Bank Interleaving | 다른 Bank 명령 겹침 실행 |
| | BG Interleaving | tCCD_S vs tCCD_L 정확 적용 |
| **Refresh** | 주기적 REF | tREFI 준수, 데이터 보존 |
| | Postpone/Pull-in | 바쁠 때 지연, 한가할 때 선행 |
| **Bank Mode** | BG 모드(4 BG×4=16뱅크) | tCCD_S/L 구분, BG interleave |
| | 8B 모드(8뱅크) / 16B 모드(16뱅크) | MR 로 모드 선택, 뱅크 수 정합성 |
| **Training (LPDDR5)** | CBT (Command Bus Training, Mode1/2) | CA[6:0] 다중사이클 캡처 정합 |
| | WCK2CK Leveling | WCK 와 CK 의 위상 정렬 수렴 |
| | DQ / Write / Read Training | 레인별 지연값 + Vref 수렴 |
| | Eye Training | 유효 윈도우 중앙 탐색 |
| **DVFSC / Gear** | F0↔F4 gear 전환 | WCK:CK(2:1↔4:1) 변경 → WCK2CK 재정렬 완료 후 데이터 |
| | gear 전환 중 traffic | 재정렬 done 전 데이터 발행 금지 |
| **Refresh (LPDDR5)** | per-bank refresh (REFpb) | bank 별 독립 refresh, 나머지 bank access 가능 |
| | PASR (부분배열 Self-Refresh) | 활성 bank/segment 만 보존, 나머지 비보존 허용 |
| **전력 (LPDDR5)** | Power-Down 진입/복귀 | 데이터 보존 + 정상 동작 재개 |
| | Self-Refresh | 데이터 유지 + 복귀 후 정상 |
| | Deep Sleep entry/exit | 진입 후 array 비보존, exit 시 재초기화/재training 정합 |

#### Negative / Stress

| 카테고리 | 시나리오 | 검증 포인트 |
|---------|---------|-----------|
| **타이밍 경계** | 타이밍 파라미터 최소값 사용 | 위반 없음 |
| **트래픽 혼합** | R/W 혼합 최대 부하 | 대역폭 유지, 데이터 무결성 |
| **Refresh 충돌** | REF 중 R/W 요청 | 요청 대기, REF 후 처리 |
| **Full Bank** | 모든 Bank 동시 Open | 스케줄링 정확, tFAW 준수 |
| **연속 Row Conflict** | 매번 다른 Row 접근 | PRE+ACT 오버헤드, 타이밍 준수 |
| **On-die ECC** | cell 내부 비트 에러 주입 (투명) | 단일 비트 자동 수정, 외부 비가시 |
| **Link ECC** | DQ 전송경로 비트 에러 주입 (LPDDR5 고유) | link 단 검출/정정, On-die 와 직교 |
| **Gear 전환 stress** | gear 전환 + 동시 traffic 최대부하 | WCK2CK 재정렬 경계에서 무결성 |
| **온도 변화** | DRAM 온도 상승 시뮬레이션 | Refresh Rate 조정, Retraining |

### 5.3 Coverage Model

아래 모델에 나오는 **RMW** 는 Read-Modify-Write(읽어서 일부만 고쳐 다시 쓰는 접근; 예: 1 바이트만 바꿀 때 워드 전체를 읽고 수정해 되쓰기), **cp_** 접두어는 coverpoint(세는 항목)를 뜻합니다.

```
[CG1] Access Pattern Coverage
  - cp_access_type: {READ, WRITE, RMW}
  - cp_burst_length: {1, 2, 4, 8, 16}
  - cp_row_state: {ROW_HIT, ROW_MISS, ROW_CONFLICT}
  - cross: access_type × row_state

[CG2] Address Coverage
  - cp_rank: {0, 1, ...}
  - cp_bank_mode: {BG_MODE, 8B_MODE, 16B_MODE}   // LPDDR5 MR 선택
  - cp_bank_group: {BG0, BG1, BG2, BG3, ...}     // BG 모드에서만 유효
  - cp_bank: {B0, B1, B2, B3, ...}
  - cp_row_region: {FIRST, MIDDLE, LAST}
  - cross: rank × bank_mode × bank_group × bank

[CG3] Scheduling Coverage
  - cp_interleave: {SAME_BG, DIFF_BG, SAME_BANK, DIFF_RANK}
  - cp_cmd_type: {ACT, RD, WR, PRE, REF, REFpb, MRS, MRR}
  - cp_back_to_back: {ACT_ACT, RD_RD, WR_WR, RD_WR, WR_RD}
  - cross: interleave × back_to_back

[CG4] Refresh / PASR Coverage
  - cp_ref_type: {ALL_BANK, PER_BANK(LPDDR5 REFpb)}
  - cp_ref_timing: {ON_TIME, POSTPONED, PULLED_IN}
  - cp_ref_vs_traffic: {IDLE, LIGHT, HEAVY}
  - cp_pasr_region: {FULL_ARRAY, HALF, QUARTER, SEGMENT}  // LPDDR5 PASR

[CG5] Training / Power / Gear Coverage
  - cp_training_type: {CBT, WCK2CK, DQ, WRITE, READ, EYE, VREF}  // LPDDR5
  - cp_power_mode: {ACTIVE, POWER_DOWN, SELF_REFRESH, DEEP_SLEEP}
  - cp_gear: {F0, F1, F2, F3, F4}             // DVFSC gear
  - cp_wck_ratio: {WCK_CK_2_1, WCK_CK_4_1}    // gear 의존 WCK:CK
  - cp_gear_lane: {LPDDR5_6400, LPDDR5_8533, LPDDR5X_..., ...}   // 속도/gear lane
  - cross: gear × wck_ratio   // gear 전환 시 WCK2CK 재정렬 경로 커버

[CG6] ECC Coverage
  - cp_ecc_kind: {ONDIE, LINK}   // On-die(cell, 투명) vs Link(DQ link, LPDDR5 고유)
  - cp_error_type: {NO_ERROR, SEC, DED, CORRECTED, DETECTED}
  - cross: ecc_kind × error_type
```

### 5.4 초기화 검증 시나리오

DRAM 초기화는 전원 인가부터 첫 번째 사용자 명령까지 엄격한 순서와 타이밍을 요구합니다. 이 순서가 조금이라도 어긋나면 DRAM 이 예측 불가능한 상태에 빠지고, 그 결과는 부팅 실패 또는 silent corruption 으로 나타납니다. 따라서 초기화 시퀀스 자체도 독립적인 검증 시나리오로 다뤄야 합니다. 핵심 항목은 전원 시퀀싱 타이밍, MRS 발행 순서, ZQ Calibration 발행 여부, Training 순서 정합성, 그리고 첫 번째 refresh 까지의 간격입니다. 특히 "JEDEC 참조 시퀀스와 DUT 시퀀스를 비교" → "의도적 순서 위반 주입" → "타이밍 최소값 경계 테스트" 의 세 단계로 접근하면 초기화 관련 버그를 체계적으로 커버할 수 있습니다.

주요 검증 항목은 다음과 같습니다.

1. **전원 시퀀싱** — VDD1/VDD2/VDDQ 인가 순서, RESET# 해제 타이밍, CKE 활성화 전 CK 안정 여부.
2. **MRW 설정 순서** — JEDEC(JESD209-5) 명시 순서대로 발행하는지, 각 MRW 간 tMRW/tMRD 준수, 설정값이 현재 gear/구성에 적합한지.
3. **ZQ Calibration** — 초기화 시 발행되는지, tZQ 대기 후 다음 명령, 주기적 재보정.
4. **Training 시퀀스** — CBT → WCK2CK → DQ/Write/Read 순서, 결과(지연값/VREF)가 Mode Register 에 반영되는지, 실패 시 재시도/에러 보고.
5. **첫 Refresh** — 초기화 완료 후 tREFI 이내 첫 REF 발행.

접근은 세 단계입니다 — **Golden Sequence 비교**(JEDEC 참조 시퀀스 vs DUT), **순서 위반 주입**(MRW 순서를 어겼을 때 모델이 에러를 보고하는지), **타이밍 경계 테스트**(tMRW/tZQ 등을 최소값으로 설정해 위반 없는지).

### 5.5 성능 검증 (Bandwidth / Latency)

성능 검증은 "기능적으로 맞다" 를 넘어 "성능 요구사항을 충족하는가?" 를 봅니다.

**1. Bandwidth 측정** — `transaction_count × burst_size × data_width / simulation_time`. 시나리오: 순차 접근 최대 BW(이론 대비 %), 랜덤 접근 BW(Row Conflict 감소율), 혼합 R/W BW(turnaround 포함), Multi-Master 동시 접근 BW.
- 효율 기준(예시): LPDDR5-6400 16-bit 채널의 이론 최대 = `6400 MT/s × 16b / 8 = 12.8 GB/s`(2 채널이면 ~25.6 GB/s). Sequential Read >90%, Random R/W Mixed ~50–70%(구성에 따라).

**2. Latency 측정** — `response_time - request_time` (per transaction). 시나리오: Idle Read Latency(Row Miss = tRCD+tCL+PHY), Row Hit Latency(tCL+PHY), 부하 상태 Latency(큐잉 포함), QoS 우선순위별 Latency 차이.

**3. 모바일 실시간 Deadline / Underrun 방지 (LPDDR5 고유 지표)** — Display/ISP 같은 isochronous master 는 frame deadline 이 hard real-time 입니다. deadline 까지 남은 시간이 임계치 미만이면 Urgent 로 승격되는지 측정합니다. 시나리오: Display refresh 중 DRAM stall(refresh/gear 전환)이 frame buffer underrun 을 유발하지 않는지(Urgent 승격 후 deadline 내 서비스), gear down(저전력)에서도 isochronous BW 보장, gear 별 전력효율(BW/mW).

**4. Scoreboard 기반 성능 수집** — UVM Scoreboard 에서 `$realtime` timestamp 를 기록합니다.

```systemverilog
class perf_scoreboard extends uvm_scoreboard;
       real total_bytes;
       real start_time, end_time;
       real latency_sum;
       int  txn_count;

       function void write_axi_req(axi_txn t);
         t.req_time = $realtime;  // 요청 시점 기록
       endfunction

       function void write_axi_rsp(axi_txn t);
         real lat = $realtime - t.req_time;
         latency_sum += lat;
         total_bytes += t.burst_len * t.data_width / 8;
         txn_count++;
       endfunction

       function void report_phase(uvm_phase phase);
         real bw = total_bytes / ($realtime - start_time);
         real avg_lat = latency_sum / txn_count;
         `uvm_info("PERF", $sformatf("BW=%.2f GB/s, Avg Lat=%.1f ns",
                   bw/1e9, avg_lat), UVM_LOW)
       endfunction
     endclass
```

### 5.6 Error Injection / ECC 검증

LPDDR5 의 ECC 는 **두 종류가 직교(보호 대상이 다름)** 한다는 점이 핵심이며, 각각을 별개 시나리오로 검증해야 합니다. **On-die ECC** 는 DRAM cell array 내부의 soft error 를 정정하며 외부에서 투명(에러가 보이지 않음)합니다(디바이스 의존). **Link ECC** 는 DQ 전송경로(link) 에서 발생한 비트 에러를 보호하는 **LPDDR5 고유** 기능입니다. 따라서 ECC 검증은 (1) On-die ECC 가 cell 비트를 투명하게 정정하는지, (2) Link ECC 가 DQ link 비트 에러를 검출/정정하는지 — 이 둘을 서로 다른 주입 지점(cell vs DQ link)으로 분리 검증하고, (3) On-die 가 커버 못 하는 multi-bit 에러에서 상위(시스템) ECC/인터럽트가 올바르게 동작하는지, (4) CA parity 에러 주입 시 MC 재발행/에러 보고를 수행하는지를 독립 경로로 검증해야 합니다. 또한 MC 의 ECC Scrubbing 이 주기적으로 모든 주소를 순회하며 축적된 soft error 를 교정하는지, Scrubbing 과 정상 트래픽 경합 시 순서가 올바른지도 확인 대상입니다.

시나리오는 세 그룹으로 나눕니다.

**A. On-die ECC (cell array 내부, 투명)**
- **Single-Bit Error (SEC)** — Behavioral Model 의 cell 비트를 1개 반전해 전달 → On-die ECC 가 자동 수정하는지, 외부에서 에러가 안 보이는지(투명) 확인. 예: `Write(0x100, 0xFF00)` 에 cell 1-bit 오류 주입 → `Read(0x100)` 기대값 `0xFF00`.
- **Multi-Bit Error (DED)** — 2-bit 이상 cell 에러는 On-die ECC 로 수정 불가 → 상위(시스템) ECC 검출 + 에러 인터럽트 발생 확인.

**B. Link ECC (DQ 전송경로, LPDDR5 고유)**
- **DQ Link Bit Error** — cell 이 아닌 DQ link 비트를 반전(전송 중 에러 모사) → Link ECC 가 link 단에서 검출/정정하는지, On-die 와 독립적으로(주입 지점이 다름) 동작하는지 확인.

**C. 공통 에러 핸들링**
- **Address(CA) Parity Error** — CA 버스에 parity error 주입 → MC 가 감지 후 재발행/에러 보고하는지. LPDDR5 CA[6:0] 다중사이클에서 parity 적용 위치 확인.
- **Scrubbing** — MC 가 주기적으로 전 주소를 Read→ECC 확인→수정→Write-back 하는지, scrub 주기가 설정대로인지, 정상 트래픽과의 경합 처리가 올바른지.

```
Coverage:
  cp_ecc_kind      : {ONDIE, LINK}                 // 직교 — 별개 보호 대상
  cp_error_type    : {NO_ERROR, SEC, DED, ADDRESS_PARITY}
  cp_error_location: {CELL_BIT, DQ_LINK_BIT, CA_BUS}
  cp_ecc_action    : {CORRECTED, DETECTED, INTERRUPT}
  cross: ecc_kind × error_type × error_location
```

### 5.7 타이밍 체커 — 왜 MC/subsystem 레벨은 SVA 가 아니라 절차적 SV 인가

타이밍 체크의 핵심은 "명령 발행 시각을 관측해 spec 의 최소 간격을 위반했는지 즉각 감지" 하는 것입니다. scoreboard 가 데이터 값의 정합성을 보는 것과 달리, 타이밍 체커는 "언제" 명령이 발행됐는지를 봅니다. tRCD 를 조금이라도 위반하면 sense amplifier 가 아직 안정되지 않은 상태에서 데이터가 읽혀 silent corruption 이 될 수 있는데, scoreboard 로는 랜덤 데이터 패턴에서 운 좋게 통과할 수도 있습니다.

문제는 **이 체커를 SVA 로 짤 수 없다는 점** 입니다. 두 가지 이유가 겹칩니다.

1. **DRAM timing 은 절대시간(ns) 규정이다.** `tRCD`, `tRP`, `tRAS`, `tRFC`, `tWTR`, `tFAW` 등은 spec 상 ns 최소값이고, cycle 수는 `ceil(t_ns / tCK)` 로 파생될 뿐입니다.
2. **LPDDR5 timing 은 DVFSC gear 의존이다.** gear(F0~F4)가 바뀌면 tCK 와 WCK:CK 비율(2:1↔4:1)이 **런타임에** 바뀌므로, 같은 tRCD_ns 라도 cycle 수가 gear 마다 달라집니다. 그런데 SVA 의 cycle-delay `##N` · 반복 `[*N]` · `[*m:n]` 의 `N` 은 **elaboration-time 상수식** 이어야 합니다(IEEE 1800 §16.7). 런타임에 바뀌는 gear 값을 지연 cycle 수로 넣을 수 없습니다.

따라서 고정 `##TRCD` SVA 로 가려면 gear 마다 파라미터를 다르게 준 인스턴스를 여러 벌 만들어 "지금 gear 에 맞는 것만 활성화" 하거나, 아예 gear 를 고정(freeze)해야 합니다 — DVFS 가 상시 도는 memory subsystem 에서는 비현실적입니다. 대신 **명령 발행 시각을 `$realtime` 으로 기록하고 경과 ns 를 현재 gear 의 ns 제약과 직접 비교** 하는 절차적 SV 체커가 자연스럽습니다. gear 가 바뀌면 그 gear 의 tCK/ns 값을 읽어 비교하므로 전환을 자동으로 따라가고, CK 가 멈추는 power-down 이나 CK/WCK 다중 클럭 도메인도 문제없이 다룹니다.

```systemverilog
// MC/memory-subsystem 레벨 LPDDR5 타이밍 체커 — 절대시간(ns) 기준, gear-aware (절차적 SV)
// bind 로 DUT 에 비침투적 연결. 값(ns)은 현재 gear 로 갱신되는 함수/배열에서 읽는다.
module lpddr5_timing_checker #(
  parameter int NUM_BANKS = 16          // bank mode 에 맞춰: BG(16)/8B(8)/16B(16)
)(
  input logic       clk,          // CK (명령용 저속)
  input logic       rst_n,
  input logic       act, rd, wr, pre, ref_cmd,
  input logic [3:0] bank,
  input logic [1:0] bg,
  input logic       wck2ck_done,  // WCK2CK 정렬 완료 (LPDDR5)
  input logic       gear_switch,  // DVFSC gear 전환(재정렬) 진행 중
  input int         cur_gear      // 현재 gear index → ns 제약 조회 키
);
  // gear 별 ns 제약 (spec 의 ns 최소값을 gear 표로 관리; 전환 시 갱신)
  // 예: TRCD_NS[F0]=18.0, TRP_NS[F0]=18.0, TRAS_NS[F0]=42.0 ...
  //     (실제 값은 JESD209-5 의 gear/속도별 표에서 채운다)
  function automatic real TRCD_NS(int g); /* gear별 tRCD(ns) */ endfunction
  function automatic real TRP_NS (int g); endfunction
  function automatic real TRAS_NS(int g); endfunction
  function automatic real TRFC_NS(int g); endfunction
  function automatic real TCCD_L_NS(int g); endfunction
  function automatic real TCCD_S_NS(int g); endfunction

  // bank 별 마지막 이벤트 시각(ns)
  realtime t_act [NUM_BANKS];
  realtime t_pre [NUM_BANKS];
  realtime t_ref;
  realtime t_cas_bg [4];   // BG 별 마지막 CAS 시각 (BG 모드)
  logic [1:0] last_bg;     // 직전 CAS 의 BG (tCCD_S/L 구분용)

  always @(posedge clk) begin
    if (!rst_n) begin
      // reset: 필요 시 시각 무효화 (음수/NaN sentinel)
    end else begin
      int b = {bg, bank};

      // ── tRCD: ACT → RD/WR 최소 간격(ns) ──
      if (act) t_act[b] <= $realtime;
      if (rd || wr) begin
        if ($realtime - t_act[b] < TRCD_NS(cur_gear))
          `uvm_error("LPDDR5_TCHK", $sformatf(
            "tRCD violation @Bank%0d: %.3f ns < %.3f ns (gear=%0d)",
            b, $realtime - t_act[b], TRCD_NS(cur_gear), cur_gear))
      end

      // ── tRAS: ACT → PRE 최소 간격(ns) ──
      if (pre) begin
        t_pre[b] <= $realtime;
        if ($realtime - t_act[b] < TRAS_NS(cur_gear))
          `uvm_error("LPDDR5_TCHK", $sformatf("tRAS violation @Bank%0d (gear=%0d)", b, cur_gear))
      end

      // ── tRP: PRE → ACT 최소 간격(ns) ──
      if (act && $realtime - t_pre[b] < TRP_NS(cur_gear))
        `uvm_error("LPDDR5_TCHK", $sformatf("tRP violation @Bank%0d (gear=%0d)", b, cur_gear))

      // ── tRFC: REF → ACT 최소 간격(ns) ──
      if (ref_cmd) t_ref <= $realtime;
      if (act && $realtime - t_ref < TRFC_NS(cur_gear))
        `uvm_error("LPDDR5_TCHK", "tRFC violation: ACT too early after REF")

      // ── tCCD_S/L: CAS→CAS (같은 BG 는 L, 다른 BG 는 S) ──
      if (rd || wr) begin
        real limit = (bg == last_bg) ? TCCD_L_NS(cur_gear) : TCCD_S_NS(cur_gear);
        if ($realtime - t_cas_bg[bg] < limit)
          `uvm_error("LPDDR5_TCHK", $sformatf("tCCD violation (gear=%0d)", cur_gear))
        t_cas_bg[bg] <= $realtime;
        last_bg      <= bg;
      end

      // ── LPDDR5: WCK2CK 정렬 완료 후에만 데이터 발행 ──
      if ((rd || wr) && !wck2ck_done)
        `uvm_error("LPDDR5_TCHK", "Data issued before WCK2CK aligned")

      // ── LPDDR5: gear 재정렬 중 데이터 발행 금지 ──
      if (gear_switch && (rd || wr))
        `uvm_error("LPDDR5_TCHK", "Data issued during DVFSC gear re-alignment")
    end
  end
endmodule
```

:::note[SVA 는 언제 쓰나 — 보조 역할]
SVA 를 버리라는 뜻이 아닙니다. **클럭이 고정된 도메인**(예: PHY 내부의 특정 subblock, 단일 gear 로 고정된 IP)에서는 cycle 정확한 edge 관계를 `##N`·`[*N]` 로 간결하게 표현할 수 있고, `cover property` 로 타이밍 코너가 실제로 hit 됐는지 세는 데도 SVA 가 유용합니다. 정리하면:

- **절차적 SV 타이밍 체커 (1차)** — MC/memory-subsystem 레벨의 ns 기준·gear 의존 제약(tRCD/tRP/tRAS/tRFC/tCCD/tFAW/tWTR + WCK2CK/gear 무결성). `$realtime` 비교라 gear 전환을 자동 추종.
- **SVA (보조)** — 고정 클럭 도메인의 cycle/edge 관계 + `cover` 로 코너 커버리지. `bind` 로 비침투 연결.
- **공통** — reset 처리(체커는 `rst_n` 로 시각 무효화), bank mode 에 맞춰 배열 크기/인스턴스 조정.
:::

### 5.8 Protocol Checker — 타이밍 검증

Protocol Checker 는 DRAM VIP 또는 Behavioral Model 에 내장된 타이밍 감시 모듈로, 위 §5.7 의 절차적 SV 타이밍 체커와 같은 성격입니다(ns 기준, gear-aware). 시뮬레이션 전 구간에 걸쳐 다음을 상시 감시하고, 위반 시 즉시 UVM_ERROR 를 보고합니다.

- **명령 간 최소 간격(ns)** — ACT→RD(tRCD), ACT→PRE(tRAS), PRE→ACT(tRP), 같은 BG RD→RD(tCCD_L)·다른 BG(tCCD_S), REF→ACT(tRFC).
- **윈도우/평균 제약** — tFAW 윈도우 안 ACT ≤ 4, tREFI 안에 REF 발행(LPDDR5 per-bank REFpb 포함).
- **LPDDR5 고유** — WCK2CK 정렬 완료 후에만 데이터(RD/WR) 발행, DVFSC gear 전환(WCK:CK 재정렬) 중 데이터 발행 금지.

MC 스케줄러가 타이밍을 위반하면 실리콘에서 데이터 오류가 발생하므로, 이 체커는 MC 검증의 필수 인프라입니다. 값이 gear 에 따라 바뀌므로 cycle 고정 SVA 가 아니라 ns/`$realtime` 기반으로 두는 것이 핵심입니다.

### 5.9 이력서 연결

이력서에 이 경험을 적을 때의 예시 기여 포인트입니다(실제 프로젝트/메모리 세대에 맞춰 수정).

- **MC 검증** — AXI Host Agent 로 다양한 트래픽 패턴 생성, Row Hit/Miss/Conflict 시나리오 개발, Refresh 타이밍 준수 검증.
- **MI/PHY 검증** — Training 시퀀스 정확성 검증(CBT/WCK2CK/DQ), 타이밍 마진 경계 테스트.
- **BootROM 연결** — BL2 의 DRAM 초기화 시퀀스(MC 레지스터 설정 → Training → 사용 가능)의 정확성이 MC/MI 검증에서 보장됨을 확인.

### 5.10 Q&A — 자주 묻는 질문

**Q: MC 검증에서 가장 중요한 검증 항목은?**
> "타이밍 준수와 데이터 무결성이다. 타이밍: tRCD, tRP, tCCD 등 수십 개의 LPDDR5 타이밍 파라미터를 모든 명령 조합에서 위반 없이 준수하는지 절차적 SV 타이밍 체커(ns 기준, gear-aware)로 상시 감시한다. 데이터: AXI Write 데이터와 AXI Read 데이터가 모든 주소, 모든 패턴에서 일치하는지 Scoreboard로 검증한다. 이 두 가지가 실리콘 수준의 데이터 무결성을 보장한다."

**Q: MC 검증의 트래픽 패턴은 어떻게 설계하나?**
> "Row Hit/Miss/Conflict 비율을 제어하는 것이 핵심이다. 순차 접근(같은 Row 반복) → Row Hit 높음, 랜덤 접근 → Row Conflict 높음, Bank Group 분산 → tCCD_S 활용. 실제 SoC 트래픽(CPU 캐시 라인, GPU 텍스처, DMA 버스트)을 모사하는 패턴과, 최악 조건(모든 접근이 Row Conflict)을 모두 포함하여 스케줄러의 정확성과 성능을 동시에 검증한다."

**Q: LPDDR5 타이밍 검증은 SVA 로 하나, 절차적 SV 로 하나?**
> "MC/memory-subsystem 레벨에서는 **절차적 SV** 로 한다. tRCD/tRP/tRAS/tCCD/tRFC 등은 spec 상 ns 최소값이고, LPDDR5 는 DVFSC gear 에 따라 tCK 가 런타임에 바뀌어 같은 ns 제약도 cycle 수가 달라진다. SVA 의 `##N` cycle 지연은 elaboration-time 상수여야 해서 gear 변화를 따라갈 수 없으므로, 명령 발행 시각을 `$realtime` 으로 기록하고 경과 ns 를 현재 gear 의 ns 제약과 비교하는 체커를 bind 로 붙인다. SVA 는 클럭이 고정된 도메인(예: PHY 서브블록)의 edge 관계와 `cover` 로 타이밍 코너 커버리지를 보는 보조 역할로 쓴다."

**Q: MC 검증에서 성능(Bandwidth/Latency)은 어떻게 측정하나?**
> "Scoreboard에서 AXI 요청/응답 시점의 timestamp를 기록하여, 트랜잭션별 Latency와 구간별 Bandwidth를 계산한다. 순차 접근 최대 대역폭(이론 대비 효율%), 랜덤 R/W 혼합 대역폭, QoS 우선순위별 Latency 차이를 측정하여 설계 요구사항 대비 충족 여부를 판정한다."

**Q: LPDDR5 의 On-die ECC 와 Link ECC 검증은 어떻게 다른가?**
> "둘은 보호 대상이 직교한다. On-die ECC 는 DRAM cell array 내부의 soft error 를 투명하게 정정하므로, cell 비트를 주입하고 Read 시 수정된 값이 반환되는지(외부 비가시) 확인한다. Link ECC 는 LPDDR5 고유로 DQ 전송경로의 비트 에러를 보호하므로, cell 이 아닌 DQ link 비트를 주입하고 link 단에서 검출/정정되는지를 별개 시나리오로 본다. 주입 지점(cell vs DQ link)이 다르다는 것이 핵심이다. 2-bit 이상 cell 에러는 On-die 로 수정 불가하므로 상위 ECC 검출/인터럽트를, 그리고 MC 의 ECC Scrubbing 동작을 추가 검증한다."

**Q: LPDDR5 의 DVFSC gear 전환 검증은 어떻게 하나?**
> "F0↔F4 같은 gear 전환 시 WCK:CK 비율(2:1↔4:1)이 바뀌고 WCK2CK 재정렬이 필요하다. 핵심은 '재정렬이 끝나기 전에는 데이터(RD/WR)를 발행하지 않는다' 를 타이밍 체커에서 `wck2ck_done`·`gear_switch` 신호로 상시 감시하는 것이다. 또 타이밍 체커의 ns 제약 표(TRCD_NS 등)가 전환 직후 새 gear 값으로 갱신되는지, 전환 중 동시 traffic 최대부하에서 무결성이 유지되는지를 stress 로 본다. (이 체크가 gear 마다 값이 바뀌므로 고정 `##N` SVA 가 아니라 `$realtime` 기반 절차적 SV 가 자연스럽다.)"

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'DRAM 검증 = timing 위반 검사']
**실제**: Timing 외에 refresh 누락, ECC scrubbing, training 실패 복구, throttle 정책, command bus protocol, RAW bypass, address mapping 등 광범위. timing 만 보면 silent corruption 의 절반을 놓칩니다.<br>
**왜 헷갈리는가**: "DRAM = timing critical" 라는 명성 때문에 timing 만 보면 다 본 것 같지만, 실제 협업 시나리오 (MC ↔ PHY ↔ DRAM ↔ master) 가 더 다양.
:::
:::danger[❓ 오해 2 — 'Scoreboard 만 PASS 면 검증 끝']
**실제**: Scoreboard 는 _읽은 값이 쓴 값과 일치_ 만 확인. timing violation 은 random data 패턴에서 운 좋게 통과할 수 있습니다 (sense amp 가 _가끔_ 안정). 절차적 SV 타이밍 체커(+ 고정도메인 SVA)가 _독립적으로_ 동작해야 silent fail 을 잡습니다.
:::
:::danger[❓ 오해 3 — '성능은 silicon 에 가서 측정하면 된다']
**실제**: silicon bring-up 단계에서 BW 미달이 발견되면 RTL 수정 cost 가 polynomial 로 폭발합니다. Performance reference scoreboard 를 시뮬에서 _회귀_ 로 돌려 변경마다 BW/latency 차이를 추적해야 합니다.
:::
:::danger[❓ 오해 4 — 'Coverage 100% = 검증 완료']
**실제**: Coverage 는 _hit_ 만 셉니다. cross 에서 일부 bin 이 unreachable 일 수 있고, _시간 차원_ 의 race condition (ZQ 와 RD 가 같은 cycle) 은 일반 cross-coverage 로 잡히지 않습니다. directed test 와 stress test 가 추가로 필요.
:::
:::danger[❓ 오해 5 — 'Behavioral DRAM model 은 spec 대로니 신뢰해도 된다']
**실제**: 일부 model 은 _refresh-induced delay_ 나 _per-bank refresh_ 같은 신규 feature 가 빠져 있습니다. 기준 DRAM model 의 정확성 자체도 검증 대상 — 가능하면 vendor VIP + reference behavioral 두 개를 cross-check.
:::
### DV 디버그 체크리스트 (DRAM DV 환경의 흔한 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Scoreboard FAIL — 특정 주소만 mismatch | RAW bypass 누락 / address mapping 충돌 | write buffer forward path, address decode |
| 타이밍 체커 mass-fire (수백 개) | reset 중 시각 미무효화(체커) / SVA disable iff 미동작 | reset polarity, 체커의 rst_n 처리 / SVA disable iff |
| Coverage 가 reach 못 하는 cross bin | traffic generator 의 randomization constraint | cp 정의 vs 실제 발생 분포, constraint 완화 |
| Performance regression — BW 가 갑자기 떨어짐 | scheduler patch / address mapper 변경 | 변경 commit 의 `git log`, BW 시계열 |
| DRAM model 의 expected data 가 틀림 | model 의 PRE/ACT 시점 추적 버그 | model 내부 bank state vs DUT 명령 sequence |
| Training 시나리오에서 무한 loop | model 의 reply 패턴 spec 불일치 | Write Leveling 의 0→1 transition tap |
| ECC SEC 시 데이터 mismatch | On-die/Link injection 위치(cell vs DQ link) 혼동, syndrome 잘못 | ECC kind(ONDIE/LINK) 별 injection 지점, syndrome 디코드 |
| per-bank refresh(REFpb) 시 다른 bank fail | LPDDR5 model 의 per-bank state machine | model 의 refresh state (per-bank vs all) |
| Deep Sleep exit 후 access fail | exit 시 재초기화/재training 누락 | model 의 Deep Sleep state + CBT/WCK2CK 재수행 |

:::caution[실무 주의점 — Open Page Policy에서 Row Conflict 폭증 시 Latency 급등]
**현상**: 랜덤 주소 패턴 워크로드에서 Bank당 Active Row가 지속적으로 교체되어, Row Miss 비율이 90%를 초과하고 평균 Latency가 순차 접근 대비 3-5배 이상으로 폭증.

**원인**: Open Page Policy는 마지막으로 열린 Row를 유지하는 최적화인데, 랜덤 주소 패턴에서는 오히려 매 접근마다 PRE(현재 Row 닫기) + ACT(새 Row 열기) 오버헤드가 필연적으로 발생. Closed Page Policy 또는 Adaptive Policy와 비교 없이 설계 고정 시 실제 워크로드에서 성능 미달.

**점검 포인트**: 성능 시뮬레이션에서 Row Hit/Miss/Conflict 비율을 Bank별로 수집하여 Conflict Rate 30% 초과 시 Page Policy 파라미터 재검토. `tRC`(ACT→ACT 같은 Bank) 위반 여부를 절차적 SV 타이밍 체커(ns 기준)로 동시에 검증.
:::
---

## 7. 핵심 정리 (Key Takeaways)

- **3 축 검증** — timing (절차적 SV 타이밍 체커 + 고정도메인 SVA), data integrity (scoreboard), performance (perf scoreboard). 셋이 _독립_ 으로 동작해야 silent fail 회피.
- **LPDDR5 검증 축** — bank mode(BG/8B/16B), gear(DVFSC: F0~F4)·WCK:CK(2:1/4:1), per-bank refresh + PASR, Deep Sleep entry/exit, WCK2CK-aligned-before-data.
- **DRAM Behavioral Model** = JEDEC sequence 모사 + timing checker + per-bank/PASR refresh + CBT/WCK2CK training reply. 그 정확성도 검증 대상.
- **타이밍 체커 = 절차적 SV(ns/`$realtime`, gear-aware)** — `tRCD`/`tCL`/`tRP`/`tRC`/`tRAS`/`tFAW`/`tREFI`/`tCCD_S/L`/`tWTR`/`tRTW`/`tRFC` 등은 ns 규정이고 cycle 수는 gear 의존이므로, 발행 시각을 `$realtime` 으로 재고 현재 gear 의 ns 제약과 비교한다. SVA(`##N` cycle 지연은 elaboration 상수 필요)는 고정 클럭 도메인 edge 관계 + `cover` 에 보조로. WCK2CK/gear 전환 무결성도 체커로.
- **Traffic Generator** — 순차/랜덤/realistic mix. CPU-like (cache line burst) + GPU-like (large block) + 모바일 isochronous(Display/ISP) + worst-case (모두 conflict).
- **Performance Reference** — request/response timestamp → BW/latency. 모바일 deadline(Underrun 방지/Urgent) + gear별 전력효율. 회귀로 변경 영향 추적.
- **ECC injection** — On-die(cell, SEC/DED, transparent) 와 Link ECC(DQ link, LPDDR5 고유) 를 직교 시나리오로 분리 + address parity + scrubbing.
- **Training 검증** — LPDDR5 CBT + WCK2CK leveling + DQ/Write/Read, PVT corner 에서 sequence 정상 종료, gear 전환·Deep Sleep exit 시 retraining 동작.

:::caution[실무 주의점]
- SVA 100% PASS + Scoreboard 100% PASS 로도 _BW 미달_ 은 잡히지 않음. perf reference 를 회귀에 반드시 포함.
- DRAM model 자체의 신규 feature 누락이 silent corruption 의 근원이 됨 — vendor VIP + behavioral 의 cross-check 가 안전.
- Coverage 100% 가 검증 완료를 보증하지 않음 — directed stress (ZQ + RD race, refresh storm) 는 cross-coverage 가 잡지 못함.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — 3 축 검증 (Bloom: Apply)]
DRAM DV 의 3 축 (Timing / Data / Performance). 각각의 _signal/metric_?

<details>
<summary>정답</summary>

- **Timing**: 절차적 SV 타이밍 체커(ns/`$realtime`, gear-aware)로 tRC/tRCD/tRP/tFAW/... 모든 spec parameter 감시. Violation = fail. (고정 도메인은 SVA 보조)
- **Data**: Scoreboard 의 read data == write data. ECC injection 시나리오.
- **Performance**: BW (GB/s), latency P50/P99, row hit rate, refresh overhead. Reference vs DUT 비교.

3 축 _모두 pass_ 가 sign-off. 한 축만 보면 false safety.

</details>
:::
:::tip[🤔 Q2 — Silent corruption 검증 (Bloom: Evaluate)]
Refresh + ECC + Training 의 _복합 silent corruption_. 어떤 시나리오?

<details>
<summary>정답</summary>

- **Refresh skip + drift**: tREFI 일부러 위반 → row 의 _drift bit_ 발생 → ECC correct 까지 시간.
- **ECC fail at training boundary**: retraining 중 read → ECC 정정 실패.
- **Multi-rank + ECC race**: ODT 미세 변동 + ECC bit flip 동시 발생.

각 시나리오의 _data integrity_ 추적 — scoreboard 가 silent corruption catch.

</details>
:::
### 7.2 출처

**External**
- JEDEC **JESD209-5** *LPDDR5/5X* spec
- IEEE 1800 (SystemVerilog — SVA cycle-delay 상수 규정 §16.7)
- *DRAM Verification Methodology* — academic/industry
- Cadence/Synopsys DDR/LPDDR VIP guides

---

## 다음 모듈

→ [Module 05 — Quick Reference Card](../05_quick_reference_card/): 면접/코드 리뷰/디버그 중 빠르게 떠올릴 한 장 카드. 모든 모듈의 핵심을 한 곳에.

[퀴즈 풀어보기 →](../quiz/04_dram_dv_methodology_quiz/)

