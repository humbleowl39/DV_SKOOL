# Module 04 — DRAM DV Methodology

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">💾</span>
    <span class="chapter-back-text">DRAM / DDR</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 04</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#검증-환경-아키텍처">검증 환경 아키텍처</a>
  <a class="page-toc-link" href="#핵심-테스트-시나리오">핵심 테스트 시나리오</a>
  <a class="page-toc-link" href="#coverage-model">Coverage Model</a>
  <a class="page-toc-link" href="#초기화-검증-시나리오">초기화 검증 시나리오</a>
  <a class="page-toc-link" href="#성능-검증-bandwidth-latency">성능 검증 (Bandwidth / Latency)</a>
  <a class="page-toc-link" href="#error-injection-ecc-검증">Error Injection / ECC 검증</a>
  <a class="page-toc-link" href="#sva-systemverilog-assertions-예시-ddr-타이밍">SVA (SystemVerilog Assertions) 예시 — DDR 타이밍</a>
  <a class="page-toc-link" href="#protocol-checker-타이밍-검증">Protocol Checker — 타이밍 검증</a>
  <a class="page-toc-link" href="#이력서-연결">이력서 연결</a>
  <a class="page-toc-link" href="#qa">Q&A</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Design** DRAM/MC 검증 환경 (Behavioral Model + Traffic Generator + Reference Scoreboard) 아키텍처를 설계할 수 있다.
    - **Apply** Timing Compliance Check (SVA bind), Refresh check, ECC injection 시나리오를 작성할 수 있다.
    - **Implement** Performance Reference로 Bandwidth / Latency 회귀를 측정.
    - **Plan** Training 시퀀스 검증 시나리오 (PVT corner, retraining trigger).

!!! info "사전 지식"
    - [Module 01-03](01_dram_fundamentals_ddr.md) DRAM/MC/PHY 전반
    - [UVM](../../uvm/), [Formal](../../formal_verification/) 코스

## 왜 이 모듈이 중요한가

**DRAM 검증은 타이밍 + 무결성 + 성능의 동시 검증**으로 일반 IP보다 복잡. tRC/tFAW/tREFI 등 수십 개의 timing constraint를 모두 trace해야 하고, ECC injection / refresh 누락 / training 실패 같은 silent corruption 시나리오를 빠짐없이 다뤄야 합니다.

!!! tip "💡 이해를 위한 비유"
    **DRAM DV** ≈ **도서관 사서 검수 — 모든 책 입출고 시간이 spec 과 일치하는지 stopwatch 검증**

    tRCD, tRP, tFAW 같은 timing 제약을 모두 준수했는지, refresh / training / scheduler 정책이 모든 시나리오에서 동작하는지 검증.

---

## 핵심 개념
**DRAM MC/MI 검증 = 타이밍 준수 + 데이터 무결성 + 스케줄링 정확성 + Training 동작 + Refresh + 전력 관리. DRAM 프로토콜의 엄격한 타이밍 제약과 방대한 상태 조합이 검증 난이도를 높이는 핵심 요인.**

!!! danger "❓ 흔한 오해"
    **오해**: DRAM 검증 = timing 위반 검사

    **실제**: Timing 외에 refresh 누락, ECC scrubbing, training 실패 복구, throttle 정책, command bus protocol 등 광범위.

    **왜 헷갈리는가**: "DRAM = timing critical" 라는 명성 때문에 timing 만 보면 다 본 것 같지만 실제 협업 시나리오가 더 다양.
---

## 검증 환경 아키텍처

```
+------------------------------------------------------------------+
|                MC / MI UVM Verification Env                        |
|                                                                   |
|  +------------------+                    +------------------+     |
|  | Host Agent       |                    | DRAM Model       |     |
|  | (AXI Master)     |                    | (Behavioral)     |     |
|  |                  |                    |                  |     |
|  | - R/W 트래픽 생성|                    | - 타이밍 체커    |     |
|  | - 주소 패턴      |                    | - 데이터 저장    |     |
|  | - QoS / Burst    |                    | - Refresh 모델   |     |
|  +--------+---------+                    +--------+---------+     |
|           | AXI                           DDR IF   |              |
|           v                                        v              |
|  +------------------------------------------------------------+  |
|  |              DUT (Memory Controller + PHY)                  |  |
|  +------------------------------------------------------------+  |
|                                                                   |
|  +------------------------------------------------------------+  |
|  |              Scoreboard / Checker                           |  |
|  |  - 데이터 무결성: AXI Write 데이터 == AXI Read 데이터       |  |
|  |  - 타이밍 위반 검사: tRCD, tRP, tCCD, tRAS, tFAW 등        |  |
|  |  - Refresh 주기 준수: tREFI 내 REF 발행                     |  |
|  |  - Bank 상태 정합성: Open/Close 추적                        |  |
|  +------------------------------------------------------------+  |
|                                                                   |
|  +------------------------------------------------------------+  |
|  |              Protocol Checker (DDR Timing Monitor)          |  |
|  |  - DDR VIP 또는 DRAM Behavioral Model 내장 체커             |  |
|  |  - 모든 타이밍 파라미터 위반 시 즉시 에러 보고              |  |
|  +------------------------------------------------------------+  |
|                                                                   |
|  +------------------------------------------------------------+  |
|  |              Functional Coverage                             |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

---

## 핵심 테스트 시나리오

### Positive

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
| **Training** | Write Leveling | 레인별 지연값 수렴 |
| | Eye Training | 유효 윈도우 중앙 탐색 |
| **전력** | Power-Down 진입/복귀 | 데이터 보존 + 정상 동작 재개 |
| | Self-Refresh | 데이터 유지 + 복귀 후 정상 |

### Negative / Stress

| 카테고리 | 시나리오 | 검증 포인트 |
|---------|---------|-----------|
| **타이밍 경계** | 타이밍 파라미터 최소값 사용 | 위반 없음 |
| **트래픽 혼합** | R/W 혼합 최대 부하 | 대역폭 유지, 데이터 무결성 |
| **Refresh 충돌** | REF 중 R/W 요청 | 요청 대기, REF 후 처리 |
| **Full Bank** | 모든 Bank 동시 Open | 스케줄링 정확, tFAW 준수 |
| **연속 Row Conflict** | 매번 다른 Row 접근 | PRE+ACT 오버헤드, 타이밍 준수 |
| **ECC** | 비트 에러 주입 (DDR5 On-die) | 단일 비트 자동 수정 |
| **온도 변화** | DRAM 온도 상승 시뮬레이션 | Refresh Rate 조정, Retraining |

---

## Coverage Model

```
[CG1] Access Pattern Coverage
  - cp_access_type: {READ, WRITE, RMW}
  - cp_burst_length: {1, 2, 4, 8, 16}
  - cp_row_state: {ROW_HIT, ROW_MISS, ROW_CONFLICT}
  - cross: access_type × row_state

[CG2] Address Coverage
  - cp_rank: {0, 1, ...}
  - cp_bank_group: {BG0, BG1, BG2, BG3, ...}
  - cp_bank: {B0, B1, B2, B3}
  - cp_row_region: {FIRST, MIDDLE, LAST}
  - cross: rank × bank_group × bank

[CG3] Scheduling Coverage
  - cp_interleave: {SAME_BG, DIFF_BG, SAME_BANK, DIFF_RANK}
  - cp_cmd_type: {ACT, RD, WR, PRE, REF, MRS}
  - cp_back_to_back: {ACT_ACT, RD_RD, WR_WR, RD_WR, WR_RD}
  - cross: interleave × back_to_back

[CG4] Refresh Coverage
  - cp_ref_type: {ALL_BANK, SAME_BANK(DDR5)}
  - cp_ref_timing: {ON_TIME, POSTPONED, PULLED_IN}
  - cp_ref_vs_traffic: {IDLE, LIGHT, HEAVY}

[CG5] Training / Power Coverage
  - cp_training_type: {WR_LEVEL, GATE, DQ, EYE, VREF, ZQ}
  - cp_power_mode: {ACTIVE, POWER_DOWN, SELF_REFRESH}
  - cp_gear_lane: {DDR4_3200, DDR5_4800, DDR5_6400, ...}
```

---

## 초기화 검증 시나리오

```
DRAM 초기화 시퀀스는 엄격한 순서와 타이밍을 요구 — 검증 필수

주요 검증 항목:

  1. 전원 시퀀싱 (Power-on Sequence)
     - VDD → VDDQ 순서 준수?
     - RESET# 해제 타이밍 (tPW 이상)?
     - CKE 활성화 전 CK 안정?

  2. MRS 설정 순서
     - JEDEC 명시 순서대로 MRS 발행?
     - 각 MRS 간 tMRD(MRS to MRS delay) 준수?
     - 설정값이 현재 속도/구성에 적합?

  3. ZQ Calibration
     - ZQCL이 초기화 시 발행되는지?
     - tZQinit(512 tCK) 대기 후 다음 명령?
     - 주기적 ZQCS/ZQCL 발행?

  4. Training 시퀀스
     - 올바른 순서: WL → Gate → DQ → Eye → VREF?
     - Training 결과(지연값, VREF)가 Mode Register에 반영?
     - Training 실패 시 재시도/에러 보고?

  5. 첫 Refresh
     - 초기화 완료 후 tREFI 이내 첫 REF 발행?

테스트 접근:
  - Golden Sequence 비교: JEDEC 스펙의 참조 시퀀스와 DUT 시퀀스를 비교
  - 순서 위반 주입: MRS 순서를 어겼을 때 DRAM 모델이 에러 보고하는지 확인
  - 타이밍 경계 테스트: tMRD, tZQinit 등을 최소값으로 설정하여 위반 없는지 확인
```

---

## 성능 검증 (Bandwidth / Latency)

```
성능 검증 = "기능적으로 맞다"를 넘어 "성능 요구사항을 충족하는가?"

1. Bandwidth 측정
   - 일정 시간 동안 전송된 총 데이터량 / 경과 시간
   - 시뮬레이션에서 측정:
     transaction_count × burst_size × data_width / simulation_time

   검증 시나리오:
     - 순차 접근 최대 Bandwidth (이론적 최대 대비 %)
     - 랜덤 접근 Bandwidth (Row Conflict로 인한 감소율)
     - 혼합 R/W Bandwidth (터널라운드 비용 포함)
     - Multi-Master 동시 접근 Bandwidth

   효율 기준 (예시):
     DDR4-3200, 64-bit: 이론적 최대 = 25.6 GB/s
     Sequential Read: >90% 효율 기대
     Random R/W Mixed: ~50-70% 효율 (구성에 따라)

2. Latency 측정
   - AXI 요청 발행 ~ AXI 응답 수신까지의 시간
   - 시뮬레이션에서 측정:
     response_time - request_time (per transaction)

   검증 시나리오:
     - Idle 상태 Read Latency (Row Miss): tRCD + tCL + PHY 지연
     - Row Hit Latency: tCL + PHY 지연
     - 부하 상태 Latency: 큐잉 지연 포함
     - QoS 우선순위별 Latency 차이

3. Scoreboard 기반 성능 수집
   UVM Scoreboard에서 timestamp 기록:

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

---

## Error Injection / ECC 검증

```
목적: On-die ECC(DDR5), 외부 ECC, 에러 핸들링의 정확성 검증

1. Single-Bit Error Injection (SEC — Single Error Correction)
   - DRAM Behavioral Model에서 특정 비트를 반전시켜 전달
   - On-die ECC가 자동 수정하는지 확인
   - 외부에서 관찰 시 에러가 보이지 않아야 함 (투명)

   테스트:
     Write(addr=0x100, data=0xFF00) → Model이 1-bit 오류 주입
     → Read(addr=0x100) → 기대: data=0xFF00 (수정된 값)

2. Multi-Bit Error Injection (DED — Double Error Detection)
   - 2-bit 이상 에러 → On-die ECC 수정 불가
   - MC 외부 ECC(SECDED)가 검출하는지 확인
   - 에러 인터럽트 발생 확인

3. Address Parity Error
   - CA 버스에서 Parity Error 주입
   - MC가 에러 감지 후 재발행 또는 에러 보고?
   - DDR4: CA Parity 선택적, DDR5: 기본 활성화

4. Scrubbing 검증
   - MC가 주기적으로 모든 주소를 Read → ECC 확인 → 수정 → Write-back
   - Scrub 주기가 설정대로 동작하는지?
   - Scrub 중 정상 트래픽과의 경합 처리?

Coverage:
  - cp_error_type: {NO_ERROR, SEC, DED, ADDRESS_PARITY}
  - cp_error_location: {DQ_BIT[0:7], DQ_BYTE[0:7]}
  - cp_ecc_action: {CORRECTED, DETECTED, INTERRUPT}
  - cross: error_type × error_location
```

---

## SVA (SystemVerilog Assertions) 예시 — DDR 타이밍

```systemverilog
// DDR 타이밍 위반 감시 SVA 예시

module ddr_timing_checker (
  input logic        clk,
  input logic        rst_n,
  input logic        act,      // Activate 명령
  input logic        rd,       // Read 명령
  input logic        wr,       // Write 명령
  input logic        pre,      // Precharge 명령
  input logic        ref_cmd,  // Refresh 명령
  input logic [3:0]  bank,     // Bank 주소
  input logic [1:0]  bg        // Bank Group
);

  // 타이밍 파라미터 (DDR4-3200 기준, tCK 단위)
  localparam int TRCD  = 22;  // ACT → RD/WR
  localparam int TRP   = 22;  // PRE → ACT
  localparam int TRAS  = 52;  // ACT → PRE (minimum)
  localparam int TCCD_S = 4;  // CAS→CAS (다른 BG)
  localparam int TCCD_L = 8;  // CAS→CAS (같은 BG)
  localparam int TRFC  = 560; // REF → ACT (tCK 단위)

  // ── tRCD 검사: ACT 후 최소 tRCD 경과 후 RD/WR ──
  // 각 Bank별 ACT 시점 기록
  int act_time [16];  // 16 Banks

  always_ff @(posedge clk) begin
    if (act) act_time[{bg, bank}] <= $time;
  end

  // Bank 단위 tRCD assertion
  property p_tRCD(int b);
    @(posedge clk) disable iff (!rst_n)
    (act && {bg, bank} == b) |->
      ##TRCD (1'b1);  // tRCD 사이클 후에야 RD/WR 허용
  endproperty

  // ── tRAS 검사: ACT 후 최소 tRAS 경과 전 PRE 금지 ──
  property p_tRAS(int b);
    @(posedge clk) disable iff (!rst_n)
    (act && {bg, bank} == b) |->
      !pre[*1:TRAS-1] ##1 1'b1;
  endproperty

  // ── tCCD_S 검사: 다른 BG 간 CAS-to-CAS ──
  sequence cas_any;
    rd || wr;
  endsequence

  property p_tCCD_S;
    @(posedge clk) disable iff (!rst_n)
    (cas_any, bg == $past(bg)) |->  // 같은 BG가 아닌 경우
      ##TCCD_S cas_any;
  endproperty

  // ── tRP 검사: PRE 후 최소 tRP 경과 전 ACT 금지 ──
  property p_tRP(int b);
    @(posedge clk) disable iff (!rst_n)
    (pre && {bg, bank} == b) |->
      ##TRP (1'b1);
  endproperty

  // ── tRFC 검사: REF 후 최소 tRFC 경과 전 ACT 금지 ──
  property p_tRFC;
    @(posedge clk) disable iff (!rst_n)
    ref_cmd |-> !act[*1:TRFC-1] ##1 1'b1;
  endproperty

  // ── Assertion & Cover 인스턴스 ──
  // (실제 구현에서는 generate로 Bank별 인스턴스 생성)
  assert_tRFC: assert property (p_tRFC)
    else `uvm_error("DDR_SVA", "tRFC violation: ACT too early after REF")

  cover_tRFC: cover property (p_tRFC);

endmodule
```

```
SVA 설계 포인트:
  - 모든 assertion에는 대응하는 cover property 필요
  - Bank별/BG별로 generate를 사용하여 개별 인스턴스 생성
  - disable iff는 reset 극성에 맞춰야 함
  - 타이밍 파라미터는 localparam으로 변경 용이하게
  - bind 모듈로 DUT에 비침투적 연결
```

---

## Protocol Checker — 타이밍 검증

```
DDR 타이밍 위반 감시:

  Protocol Checker (DDR VIP 또는 DRAM Model 내장):
    - ACT→RD: tRCD 이상 간격?
    - ACT→PRE: tRAS 이상 간격?
    - PRE→ACT: tRP 이상 간격?
    - RD→RD(같은 BG): tCCD_L 이상?
    - RD→RD(다른 BG): tCCD_S 이상?
    - ACT 4개 윈도우: tFAW 이상?
    - REF 간격: tREFI 이내?

    위반 시 → 즉시 UVM_ERROR + 위반 내용 보고

핵심: MC의 스케줄러가 타이밍을 위반하면 실리콘에서 데이터 오류 발생
→ Protocol Checker는 MC 검증의 필수 인프라
```

---

## 이력서 연결

```
Resume:
  "DRAM Memory Controller IP Verification – Follow (TF)" × 2
  "DRAM Memory Interface Verification – Follow"

기여 포인트:
  1. MC 검증 (S5E9945, V920)
     - AXI Host Agent로 다양한 트래픽 패턴 생성
     - Row Hit/Miss/Conflict 시나리오 개발
     - Refresh 타이밍 준수 검증

  2. MI/PHY 검증 (S5E9945)
     - Training 시퀀스 정확성 검증
     - Write Leveling, DQ Training 시나리오
     - 타이밍 마진 경계 테스트

  3. BootROM과의 연결
     - BL2의 DRAM 초기화 시퀀스가
       MC 레지스터 설정 → Training → DRAM 사용 가능
       이 과정의 정확성이 MC/MI 검증에서 보장됨
```

---

## Q&A

**Q: MC 검증에서 가장 중요한 검증 항목은?**
> "타이밍 준수와 데이터 무결성이다. 타이밍: tRCD, tRP, tCCD 등 수십 개의 DDR 타이밍 파라미터를 모든 명령 조합에서 위반 없이 준수하는지 Protocol Checker로 상시 감시한다. 데이터: AXI Write 데이터와 AXI Read 데이터가 모든 주소, 모든 패턴에서 일치하는지 Scoreboard로 검증한다. 이 두 가지가 실리콘 수준의 데이터 무결성을 보장한다."

**Q: MC 검증의 트래픽 패턴은 어떻게 설계하나?**
> "Row Hit/Miss/Conflict 비율을 제어하는 것이 핵심이다. 순차 접근(같은 Row 반복) → Row Hit 높음, 랜덤 접근 → Row Conflict 높음, Bank Group 분산 → tCCD_S 활용. 실제 SoC 트래픽(CPU 캐시 라인, GPU 텍스처, DMA 버스트)을 모사하는 패턴과, 최악 조건(모든 접근이 Row Conflict)을 모두 포함하여 스케줄러의 정확성과 성능을 동시에 검증한다."

**Q: DDR 타이밍 검증에 SVA를 어떻게 활용하는가?**
> "tRCD, tRP, tRAS, tCCD, tRFC 등 핵심 타이밍 파라미터를 SVA property로 정의하여 시뮬레이션 전 구간에서 상시 감시한다. Bank별로 generate 문을 사용해 개별 assertion을 인스턴스화하고, bind 모듈로 DUT에 비침투적으로 연결한다. 모든 assertion에 대응하는 cover property를 만들어 실제로 해당 타이밍 경계가 테스트되었는지 확인한다."

**Q: MC 검증에서 성능(Bandwidth/Latency)은 어떻게 측정하나?**
> "Scoreboard에서 AXI 요청/응답 시점의 timestamp를 기록하여, 트랜잭션별 Latency와 구간별 Bandwidth를 계산한다. 순차 접근 최대 대역폭(이론 대비 효율%), 랜덤 R/W 혼합 대역폭, QoS 우선순위별 Latency 차이를 측정하여 설계 요구사항 대비 충족 여부를 판정한다."

**Q: DDR5 On-die ECC 검증은 어떻게 하나?**
> "DRAM Behavioral Model에서 단일 비트 에러를 주입하고, Read 시 수정된 값이 반환되는지 확인한다(투명성). 2-bit 이상 에러는 On-die ECC로 수정 불가하므로, 외부 SECDED ECC의 검출과 에러 인터럽트 발생을 검증한다. 또한 MC의 ECC Scrubbing이 주기적으로 모든 주소를 순회하며 에러를 교정하는지 확인한다."

---
!!! warning "실무 주의점 — Open Page Policy에서 Row Conflict 폭증 시 Latency 급등"
    **현상**: 랜덤 주소 패턴 워크로드에서 Bank당 Active Row가 지속적으로 교체되어, Row Miss 비율이 90%를 초과하고 평균 Latency가 순차 접근 대비 3-5배 이상으로 폭증.
    
    **원인**: Open Page Policy는 마지막으로 열린 Row를 유지하는 최적화인데, 랜덤 주소 패턴에서는 오히려 매 접근마다 PRE(현재 Row 닫기) + ACT(새 Row 열기) 오버헤드가 필연적으로 발생. Closed Page Policy 또는 Adaptive Policy와 비교 없이 설계 고정 시 실제 워크로드에서 성능 미달.
    
    **점검 포인트**: 성능 시뮬레이션에서 Row Hit/Miss/Conflict 비율을 Bank별로 수집하여 Conflict Rate 30% 초과 시 Page Policy 파라미터 재검토. `tRC`(ACT→ACT 같은 Bank) 위반 여부를 Timing SVA로 동시에 검증.

## 핵심 정리

- **3축 검증**: 타이밍 (timing constraint 준수) + 무결성 (data correctness, ECC) + 성능 (BW, latency).
- **DRAM Behavioral Model**: JEDEC 명령 sequence를 모사. write/read 응답 + refresh + training 응답.
- **Timing SVA**: tRCD/tCAS/tRP/tRC/tRAS/tFAW/tREFI 등 수십 개 + violation count cover.
- **Traffic Generator**: 순차/랜덤/realistic mix. CPU-like (cache line burst) + GPU-like (large block) 시나리오.
- **Performance Reference**: AXI 요청 시점 + 응답 시점 timestamp → BW/Latency. 이론 대비 효율%, QoS별 latency.
- **ECC injection**: 1-bit (correctable) + 2-bit (detectable but not correctable) → 수정/검출/인터럽트 동작 검증.
- **Training 검증**: PVT corner에서 sequence 정상 종료, retraining trigger 발생 시 동작.

## 다음 단계

- 📝 [**Module 04 퀴즈**](quiz/04_dram_dv_methodology_quiz.md)
- ➡️ [**Module 05 — Quick Reference Card**](05_quick_reference_card.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../03_memory_interface_phy/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Memory Interface / PHY</div>
  </a>
  <a class="nav-next" href="../05_quick_reference_card/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">DRAM Memory Controller & DDR4/5 — Quick Reference Card</div>
  </a>
</div>


--8<-- "abbreviations.md"
