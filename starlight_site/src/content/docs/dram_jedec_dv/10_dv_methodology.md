---
title: "Ch10. DV Methodology 통합 — Spec → TB → Coverage"
---

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">CH 10</span>
</div>

## 🎯 Learning Objectives

- **Design**: DRAM 검증 환경의 agent / monitor / scoreboard 책임 분할을 설계한다.
- **Compose**: Coverage 카테고리 6가지(command / timing / MR / training / refresh / ECC)를 한 testbench에 통합한다.
- **Classify**: SVA 패턴을 *timing violation* / *command order* / *training protocol* 세 부류로 분류한다.
- **Plan**: DDR5/LPDDR5 sign-off checklist를 수립한다.

## Prerequisites

- Ch01~Ch09 (모든 챕터)
- UVM 1.2 component 구조 (env, agent, sequencer, driver, monitor)

## 1. DRAM TB의 구조 — 큰 그림

```d2
direction: down

TB: "DDR5 Testbench" {
  VS: "Virtual Sequence"
  ENV: ddr5_env
  ENV2: "Inside Env" {
    AGT: "ddr5_agent (Active)"
    CGT: ddr5_cov
    SB: ddr5_scoreboard
    REF: "Memory Reference Model"
    CHK: "Protocol Checker SVA bind"
  }
  VS -> ENV
  ENV -> ENV2.AGT
  ENV -> ENV2.CGT
  ENV -> ENV2.SB
  ENV -> ENV2.REF
}

DUT: DUT {
  CTRL: "Memory Controller RTL"
  DRAM: "DRAM Model (BFM)"
}

TB.ENV2.AGT -> DUT.CTRL: drives/monitors
DUT.CTRL -> DUT.DRAM: DDR5 bus
TB.ENV2.CHK -> DUT.CTRL: bind {style.stroke-dash: 5}
TB.ENV2.AGT -> TB.ENV2.SB: analysis port
TB.ENV2.AGT -> TB.ENV2.CGT: analysis port
TB.ENV2.SB -> TB.ENV2.REF: compares
```

### 1.1 컴포넌트별 책임

위 그림은 **UVM**(Universal Verification Methodology, 재사용 가능한 검증 환경을 만드는 SystemVerilog 표준 클래스 라이브러리)으로 짠 검증 환경입니다. 표를 읽기 전에 구성 요소를 먼저 풀어 둡니다 — **env**(environment, 검증 컴포넌트들을 묶는 최상위 컨테이너), **agent**(한 인터페이스의 자극 생성·구동·관찰을 담당하는 묶음), **sequencer**(트랜잭션을 만들어 driver로 흘려보내는 컴포넌트), **driver**(트랜잭션을 받아 핀 신호로 인가), **monitor**(핀 신호를 관찰해 트랜잭션으로 복원), **scoreboard**(기대값과 실제값을 비교), **virtual sequence**(여러 시나리오를 조합해 지휘하는 상위 시퀀스), **reference model**(정답을 계산하는 golden model), **BFM**(bus functional model, 실제 RTL 대신 버스 동작만 흉내 내는 모델 — 여기서는 DRAM 역할), **bind**(RTL을 수정하지 않고 외부에서 검사 모듈을 붙이는 SystemVerilog 구문)입니다.

| 컴포넌트 | 책임 |
|---|---|
| **virtual sequence** | 시나리오 조합 — init / training / traffic / refresh stress |
| **agent** | DDR5 protocol drive/monitor — driver, monitor, sequencer |
| **driver** | sequence_item을 *cycle-accurate*로 핀에 driving (또는 controller cmd interface) |
| **monitor** | 핀 신호를 transaction으로 reconstruct (2-cycle command 처리) |
| **scoreboard** | data integrity 검증 — write/read 매칭, ECC 동작 확인 |
| **memory reference model** | DRAM의 *기능적* 모델 — mem[addr]=data + bank state FSM |
| **coverage collector** | 모든 covergroup 집계 |
| **SVA bind module** | RTL controller에 bind되어 protocol 위반 즉시 catch |

---

## 2. Memory Reference Model — 핵심 설계 결정

DRAM 검증의 척추는 memory reference model입니다. scoreboard가 실제 DUT의 동작과 비교할 때 "예상값"을 계산해주는 golden model이기 때문입니다.

### 2.1 두 가지 전략

| 전략 | 설명 | 장단점 |
|---|---|---|
| **Cycle-accurate model** | 모든 timing을 모델링 (tRCD, tRP, bank FSM 포함) | 정확하지만 느림. controller IP의 timing model에 의존성 ↑ |
| **Functional model** | data integrity만 추적 (mem[addr]=data) — timing은 SVA가 별도 검증 | 빠르고 깔끔. 권장. |

이 두 전략의 차이를 생각해보면, cycle-accurate model은 타이밍 위반 자체도 reference model이 잡으려 하는데, 이것은 책임을 하나의 컴포넌트에 너무 많이 몰아주는 설계입니다. functional model은 "데이터가 맞는가"만 묻고, "타이밍이 맞는가"는 SVA에 완전히 위임합니다. 두 역할을 분리하면 각자의 디버그가 훨씬 쉬워집니다. 권장 방식은 **Functional model + 별도 SVA timing checker의 2분 분리**입니다.

### 2.2 Functional model skeleton

```systemverilog
class ddr5_mem_ref_model extends uvm_object;
    `uvm_object_utils(ddr5_mem_ref_model)

    // Address → data mapping
    bit [127:0] mem[longint];

    // Per-bank state — for spec compliance check
    typedef enum {BANK_IDLE, BANK_ACTIVE, BANK_REFRESH} bank_state_e;
    bank_state_e bank_st[256];      // 8 BG × 4 BA × 8 ranks = 256
    bit [16:0]   bank_active_row[256];

    function new(string name = "ddr5_mem_ref_model");
        super.new(name);
        foreach (bank_st[i]) bank_st[i] = BANK_IDLE;
    endfunction

    function int bank_idx(int bg, int ba, int rank);
        return (rank * 32) + (bg * 4) + ba;
    endfunction

    // ACT — open row
    function void do_act(int bg, int ba, int rank, bit [16:0] row);
        int idx = bank_idx(bg, ba, rank);
        if (bank_st[idx] != BANK_IDLE)
            `uvm_error("REF_MODEL",
                $sformatf("ACT to non-idle bank (rank=%0d bg=%0d ba=%0d state=%s)",
                          rank, bg, ba, bank_st[idx].name()))
        bank_st[idx] = BANK_ACTIVE;
        bank_active_row[idx] = row;
    endfunction

    // PRE — close row
    function void do_pre(int bg, int ba, int rank);
        int idx = bank_idx(bg, ba, rank);
        if (bank_st[idx] != BANK_ACTIVE)
            `uvm_error("REF_MODEL",
                $sformatf("PRE to non-active bank state=%s", bank_st[idx].name()))
        bank_st[idx] = BANK_IDLE;
    endfunction

    // WR — record data
    function void do_wr(longint addr, bit [127:0] data);
        mem[addr] = data;
    endfunction

    // RD — fetch data (returns 'x if not written)
    function bit [127:0] do_rd(longint addr);
        if (!mem.exists(addr)) return 'x;
        return mem[addr];
    endfunction
endclass
```

### 2.3 Reference model의 위치 — scoreboard 안 또는 별도

권장: *별도 component*. scoreboard는 *비교 전담*, reference model은 *상태 추적 전담*.

---

## 3. Coverage 카테고리 6가지 — 모두 통합

DRAM 검증에서 coverage closure는 다음 6가지 카테고리가 모두 채워져야 의미가 있습니다. 어느 하나가 빠지면 검증되지 않은 동작 경로가 남습니다. 예를 들어 command coverage만 채우고 timing coverage를 무시하면, 명령 자체는 모두 발급되었지만 corner timing 상황에서의 동작은 전혀 검증되지 않은 상태가 됩니다.

### 3.1 Command Coverage (Ch05)

```systemverilog
// 모든 명령이 *적어도 한 번* 발급되었는가
// (BL 옵션 × Auto-precharge 옵션 × Rank 옵션의 cross까지 권장)
```

### 3.2 Timing Parameter Coverage (Ch06)

```systemverilog
// 각 timing parameter의 *min/normal/long_idle* bin이 hit
// tRCD/tRP/tRRD_S/tRRD_L/tCCD_S/tCCD_L/tWTR_S/tWTR_L/tFAW
```

### 3.3 Mode Register Coverage (Ch04)

```systemverilog
// MR0~254 중 *DV 우선순위 카테고리*의 모든 MR이 write + read 되었는가
// 카테고리 cross: basic/ecc/odt/dca/refresh/ppr/dfe
```

### 3.4 Training Scenario Coverage (Ch08)

```systemverilog
// FSM 의 모든 state hit + 각 step에서 fail injection 시나리오 cover
// training_step_cg + training_fail_cg
```

### 3.5 Refresh / RFM Coverage (Ch07)

```systemverilog
// tREFI mode (normal/extended), deferred count, RFM RAA threshold cross
// + Rowhammer aggressor scenario
```

### 3.6 ECC / Error Injection Coverage (Ch09)

```systemverilog
// Single-bit / Multi-bit / no-error 비율
// CRC error count distribution
// PPR type × guard key 가 cross
```

### 3.7 통합 weighting — 어떤 카테고리가 더 중요한가

| 카테고리 | weight (예시) | 이유 |
|---|---|---|
| Command coverage | 1.0 | 기본 |
| Timing coverage | **2.0** | corner timing bug가 가장 심각 |
| MR coverage | 0.8 | 일부 MR은 default 만으로 충분 |
| Training | 1.5 | high-speed device의 핵심 |
| Refresh / RFM | 1.2 | Rowhammer 대응 |
| ECC / Error | **1.5** | 신뢰성 직결 |

> weight는 organization마다 다름. *sign-off goal*과 함께 정의.

---

## 4. SVA 패턴 — 3 분류

SVA를 작성할 때 "어떤 종류의 검사인가"를 분류해두면 관리가 쉬워집니다. 아래 3가지 카테고리로 나누면 각 assertion의 목적이 명확해지고, 나중에 assertion fail이 발생했을 때 어느 계층의 문제인지 즉시 좁혀낼 수 있습니다.

### 4.1 Timing Violation Assertions

타이밍 제약을 위반했을 때 즉시 fail을 내는 assertion입니다. tRCD/tRP/tRC/tRAS/tRRD/tFAW/tCCD_L/S 위반, tREFI 9 deferred 초과, preamble length 위반을 catch합니다. 이 assertion이 없으면 timing 위반이 데이터 오류로 나타날 때까지 수십 us를 더 기다려야 합니다.

> Ch06 §5 참조

### 4.2 Command Order Assertions

명령 순서의 논리적 정확성을 검사하는 assertion입니다. DRAM state machine이 허용하지 않는 명령 순서를 즉시 catch합니다. ACT→ACT without PRE(same bank), PRE→ACT within tRP, RD→WR within tRTW, WR→RD within tWTR를 다룹니다.

> Ch05 §6 참조

### 4.3 Training Protocol Assertions

초기화 및 훈련 시퀀스의 절차적 정확성을 검사하는 assertion입니다. CBT entry MR 발급 후 일반 traffic 발급 금지, WCK2CK leveling 단계에서 RD/WR 금지, training mode 진입/종료 절차의 정확한 sequence를 다룹니다. 이 assertion이 없으면 training이 완료되지 않은 상태에서 normal traffic이 시작되어 silent data corruption이 발생할 수 있습니다.

> Ch08 §6 참조

### 4.4 SVA Bind 패턴

```systemverilog
// 파일: ddr5_protocol_check.sv
module ddr5_protocol_check (
    input bit clk,
    input bit reset_n,
    input bit [6:0] ca_t,         // 2-cycle command — sampled
    input bit cs_n,
    input bit cke,
    // ... 다른 핀 ...
);
    // Timing assertions
    `include "sva_timing_checks.svh"

    // Command order assertions
    `include "sva_command_order.svh"

    // Training protocol assertions
    `include "sva_training_protocol.svh"
endmodule

// 사용 — DUT 외부에서 bind
bind ddr5_top ddr5_protocol_check u_proto_check (
    .clk(clk),
    .reset_n(reset_n),
    .ca_t(ca_signal),
    .cs_n(cs_n_signal),
    .cke(cke_signal)
    // ...
);
```

`bind` 의 장점: RTL 수정 *없이* checker 추가/제거 가능.

---

## 5. Regression Strategy — Tier 기반

### 5.1 3-Tier Regression

```
Tier 1 — Smoke (~5 min, seed=0)
├── basic_init_test       — init sequence 정상
├── basic_wr_rd_test      — single WR + RD
├── basic_refresh_test    — REF 발급
└── basic_training_test   — training 진입/탈출

Tier 2 — Constrained-random (~30 min, 100 seeds × 10 tests)
├── random_traffic        — random WR/RD pattern
├── timing_corner_test    — tight timing constraint
├── refresh_stress        — high refresh load
├── training_fail_inject  — 각 step별 fail
├── ecc_error_inject      — single/multi bit
└── rowhammer_attack      — RFM 검증

Tier 3 — Coverage closure (~hours, hole-filling tests)
└── directed tests for specific coverage holes
```

### 5.2 Seed strategy

- **Tier 1**: seed=0 (deterministic, debug용)
- **Tier 2**: random seeds — *failure 발생 시 seed 기록*
- **Tier 3**: *failed seed*를 회귀 풀에 영구 추가 (regression list)

---

## 6. Sign-off Checklist (DDR5)

### 6.1 Functional / Protocol

- [ ] 모든 명령 (ACT/PRE/RD/WR/REF/MRW/MRR/RFM/ZQ/PDE/PDX) 이 적어도 1회 발급
- [ ] 2-cycle command monitor가 *모든 명령*을 정확 reconstruct
- [ ] BL16 / BL32 모두 사용
- [ ] Auto-precharge (RDA/WRA) 사용
- [ ] 모든 BG/BA 조합 사용 (BG ×8, BA ×4)

### 6.2 Timing

- [ ] tRCD/tRP/tRAS/tRC 위반 catch SVA pass (한 번도 fail 없음)
- [ ] tFAW sliding window 위반 catch SVA pass
- [ ] tCCD_L (same BG) / tCCD_S (different BG) 위반 catch
- [ ] tREFI deferred 9+ 위반 catch
- [ ] Timing parameter coverage *all bins* hit

### 6.3 Mode Register

- [ ] DV 우선순위 Top 10 MR 모두 write + read
- [ ] init-only MR을 runtime에 변경 시 SVA fail 확인
- [ ] MR mirror value가 DUT internal MR과 *일치* (RAL verify)

### 6.4 Training

- [ ] Training FSM 의 모든 state hit (failure 포함)
- [ ] Each training step 에 fail injection 후 controller가 *graceful*하게 처리
- [ ] retry count distribution이 reasonable

### 6.5 Refresh / RFM

- [ ] Normal-temp / Extended-temp 모두 검증
- [ ] RFM RAA threshold 도달 시 RFM 명령 발급 확인
- [ ] Rowhammer aggressor pattern 후 victim data integrity 확인

### 6.6 ECC

- [ ] Single-bit error → 정정 확인 (data 일치)
- [ ] Double-bit error → 검출 확인 (epoch error report)
- [ ] MR20 error count 증가 확인
- [ ] CRC error injection → ALERT_n 토글

### 6.7 PPR

- [ ] hPPR sequence success 확인
- [ ] sPPR sequence success 확인
- [ ] Guard key incorrect → PPR fail 확인

### 6.8 Coverage 목표

- [ ] Functional coverage 95%+ (waive 1.5% 미만)
- [ ] Code coverage (line/toggle) 95%+
- [ ] FSM coverage 100% (모든 state + transition)

### 6.9 Regression

- [ ] Tier 1 (smoke): 100% pass
- [ ] Tier 2 (1000+ seeds): 0 unexplained fail
- [ ] Tier 3 (coverage hole tests): 모든 hole이 *intent로 waive*되거나 hit

---

## 7. Sign-off Checklist (LPDDR5 추가 항목)

LPDDR5 검증 시 DDR5의 위 체크리스트 + 다음 추가:

- [ ] WCK Clocking — WCK2CK Leveling 시퀀스 성공
- [ ] DVFS Frequency Set Point 전환 시퀀스 정상
- [ ] CBT Mode1 / Mode2 모두 진행
- [ ] DCA / DCM 동작 확인 (duty cycle 50% 근접)
- [ ] Link ECC encoding/decoding *spec matrix*와 일치
- [ ] PASR / PARC self-refresh 시나리오
- [ ] ARFM / DRFM 모두 발급되었는지
- [ ] Single-ended mode (low-frequency operation) 시나리오
- [ ] Deep Sleep Mode 진입/탈출

---

## 8. 대표 문제 — 검증 환경 책임 분배 시나리오

:::tip[Q. 다음 상황에서 어떤 컴포넌트가 어떻게 동작해야 하는지 책임을 분배하라.]

상황: DDR5 controller가 ACT 발급 후 tRCD-1 cycles 만에 RD 발급. DRAM model은 이 RD를 *수락*하지만 *invalid data*를 반환 (모델의 timing 가정 위반). 시뮬레이션은 *통과*하지만 silicon에서는 fail."
:::
<details>
<summary>풀이 (책임 분배 + 개선안)</summary>


**Step 1 — 누가 *현재* fail을 catch해야 하나?**

| 컴포넌트 | 현재 상태 | 문제 |
|---|---|---|
| DRAM model | RD를 수락하고 invalid data 반환 | *너무 관대* — spec violation을 *조용히* 받아들임 |
| Monitor | RD transaction을 publish | *순수 capture* 만 함 — timing 검증 X |
| Scoreboard | RD data를 *write data*와 비교 | *invalid data*가 *write data*와 우연히 일치 가능 → false pass |
| SVA timing checker | tRCD assertion이 *제대로 작성되었으면* fail | 만약 *없거나 약하게* 작성되었으면 못 잡음 |
| Reference model | bank state는 추적 — `do_rd()` 호출 | 그러나 *timing*은 추적 X (functional model) |

**Step 2 — 책임 분배 — *올바른* 설계**

- **SVA timing checker** (필수): `tRCD` 위반을 *즉시* catch. RD 명령 발급 시점이 ACT 후 *< tRCD* 라면 fail.
- **DRAM model** (개선): timing 위반을 *수락하지 말고* — *X data* 반환 + UVM_WARNING. 그러나 *fail은 SVA가 책임*.
- **Scoreboard** (보조): RD data가 *X*면 *write data와 비교하지 않음* — *valid data only* 검증.
- **Monitor**: 그대로 — capture만 (timing은 SVA).

**Step 3 — 개선된 시퀀스**

1. Driver가 ACT 후 *tRCD-1 cycle*에 RD 발급 (시퀀스 자체는 의도적 위반)
2. SVA `a_trcd` 가 *즉시* fail → uvm_error
3. DRAM model이 *X data* 반환
4. Scoreboard가 *X*를 보고 *비교 skip* (또는 warning)
5. UVM_FATAL 또는 UVM_ERROR로 시뮬레이션 fail 종료
6. Failure log에 *정확한 cycle + 위반된 timing parameter* 기록

**Step 4 — DV 적용 — 시스템적 보완**

1. **SVA 작성 빠짐 없이**: 모든 critical timing 에 대해 SVA. 이 학습 자료의 Ch06이 가이드.
2. **DRAM model의 정직성**: 위반을 *조용히 수락* 하지 않도록 model을 *strict mode*로 설정.
3. **Scoreboard의 X handling**: `===` 비교 + X면 warning.
4. **Coverage**: `timing_corner_cg` 의 *min_spec* bin이 hit되도록 directed test.
5. **Regression**: SVA fail 시 *seed log* → 영구 회귀 풀에 추가.

</details>
---

## 9. PDF 정밀 인용 — JEDEC 스펙 기반 sign-off corner cases

### 9.1 DDR5-specific Corner Cases (Ch01~Ch09 통합)

> 출처 종합: JESD79-5C.01 v1.31

다음은 *spec 원문이 명시하는 corner case* 들로, sign-off 시 *반드시 검증* 해야 함:

| Case | 검증 포인트 | 출처 |
|---|---|---|
| 2-Cycle Command Cancel | tCMD_cancel = 8 nCK. cancel 후 PRE 없이 MRR 발급 시 fail | §4.1.1 Table 31 |
| 24 Gb non-binary row | row[16]=H 일 때 row[15]=L 강제 (1/4 of row space invalid) | §2.7 Table 6 NOTE 1 |
| MR23 mutual exclusion | hPPR/sPPR/sPPR_UndoLock/mPPR/MBIST 동시 단 하나만 1 | §3.5.25 NOTE 1 |
| MR58:OP[0]=0 시 RFM 동작 | RFM 명령이 REF처럼 동작 (vendor 보장 X) | Table 30 NOTE 23 |
| MR4:OP[3]=1 (2x Refresh Rate) 도달 시간 | DRAM Tj 2°C 이내 update 의무 | §3.5.6 NOTE 4 |
| Wide Range (MR4:OP[5]=1) >95°C | data integrity 보장 X | §3.5.6 NOTE 3 |
| TUF flag (MR4:OP[7]) | MRR 후 자동 clear, 다음 OP[2:0] 변경 시 set | §3.5.6 |
| ECS Threshold (MR15:OP[2:0]) | default 256. ETC 도달 시 *MR16~20 통계 update* | §3.5.17 |
| PASR (MR60) | **deprecated** since v1.30 — RFU 처리 | §3.5.61 |
| MR3 Optional OPcode | 0111B~1111B (= -7~-15 tCK) speed bin 따라 필요 | §3.5.5 NOTE 5 |
| WR Partial = L | partial write — DRAM이 internal read 발생 (RMW) | Table 30 NOTE 12 |
| CW = H (Control Word) | MRW의 마지막 cycle CW=H면 DRAM 무시, RCD만 처리 | Table 30 NOTE 13 |
| NOP vs DES | NOP는 valid 명령 (timing 적용), DES는 non-command | Table 30 NOTE 26 |
| x4 device DM/TDQS | MR5:OP[4]=0, OP[5]=0 강제 (둘 다 unsupported) | §3.5.7 |
| 3DS rank addressing | MR14:OP[3:0] (CID) 로 transparency MR/PPR resource select | §3.5.16 NOTE 1 |

### 9.2 LPDDR5 Sign-off Specific (LPDDR5/5X)

> 출처: JESD209-5C

| Case | 검증 포인트 |
|---|---|
| WCK2CK Sync | CAS WCK Sync bits 활용. WCK 미정렬 시 데이터 corruption |
| DVFS FSP transition | FSP 변경 시 모든 timing/voltage *원자적* 변경. partial state 금지 |
| DRFM target address validity | DRFM 발급 시 target row가 *현재 active*가 아니어야 함 |
| Link ECC + DBI 순서 | encode(DBI then ECC) vs (ECC then DBI) — spec 강제 순서 |
| Bank mode 전환 | 16B/8B/BG mode 전환은 *재초기화 필요*. 동작 중 전환 금지 |
| Deep Sleep Mode 진입 | Self Refresh와 다른 *전력 상태*. 진입 절차 별도 |

### 9.3 RAL 모델링 정밀 — DDR5 핵심 MR 모두 등록

```systemverilog
// 출처: Ch04 §8 + Ch07 §10 + Ch08 §9 + Ch09 §12 종합
package ddr5_ral_pkg;
  import uvm_pkg::*;
  `include "uvm_macros.svh"

  // 우선순위 MR 모두 등록 (Top 25 covers >90% of DV scenarios)
  class ddr5_ral_block extends uvm_reg_block;
    `uvm_object_utils(ddr5_ral_block)

    // 기본 동작
    rand ddr5_reg_MR0    MR0;   // BL, CL
    rand ddr5_reg_MR1    MR1;   // PDA
    rand ddr5_reg_MR2    MR2;   // Functional Modes
    rand ddr5_reg_MR3    MR3;   // DQS Training (WL Internal Cycle Alignment)
    rand ddr5_reg_MR4    MR4;   // Refresh Settings
    rand ddr5_reg_MR5    MR5;   // IO Settings
    rand ddr5_reg_MR6    MR6;   // tWR, tRTP
    rand ddr5_reg_MR7    MR7;   // WL Internal +0.5tCK Alignment Offset
    rand ddr5_reg_MR8    MR8;   // Preamble/Postamble

    // Training
    rand ddr5_reg_MR10   MR10;  // VrefDQ
    rand ddr5_reg_MR11   MR11;  // VrefCA
    rand ddr5_reg_MR12   MR12;  // VrefCS
    rand ddr5_reg_MR13   MR13;  // CS Geardown, tCCD_L, tDLLK

    // ECC
    rand ddr5_reg_MR14   MR14;  // Transparency ECC Config
    rand ddr5_reg_MR15   MR15;  // ECC Threshold + Auto ECS
    rand ddr5_reg_MR16   MR16;  // Max Row Error Addr R[7:0]
    rand ddr5_reg_MR17   MR17;  // Max Row Error Addr R[15:8]
    rand ddr5_reg_MR18   MR18;  // Max Row Error Addr R[17:16] + BG + BA
    rand ddr5_reg_MR19   MR19;  // Max Row Error Count + PASR
    rand ddr5_reg_MR20   MR20;  // Error Count EC

    // Rx CTLE / MBIST
    rand ddr5_reg_MR21   MR21;  // Rx DQS CTLE
    rand ddr5_reg_MR22   MR22;  // MBIST/mPPR Transparency + Rx CTLE CA/CS
    rand ddr5_reg_MR23   MR23;  // MBIST/PPR Settings
    rand ddr5_reg_MR24   MR24;  // PPR Guard Key

    // Refresh Management
    rand ddr5_reg_MR58   MR58;  // RFM (RAAIMT, RAAMMT)
    rand ddr5_reg_MR59   MR59;  // DRFM, ARFM, RAA Counter

    function new(string name = "ddr5_ral_block");
        super.new(name, UVM_NO_COVERAGE);
    endfunction

    virtual function void build();
        default_map = create_map("default_map", 0, 1, UVM_LITTLE_ENDIAN, 0);
        // 각 MR을 build + add_reg
        // ...
        lock_model();
    endfunction
  endclass
endpackage
```

### 9.4 Sign-off Spec-Compliance Checklist (정밀)

기존 §6 checklist에 *spec 원문 corner case* 통합:

#### Functional / Protocol (강화)
- [ ] 모든 명령 (ACT/PRE/RD/WR/REF/MRW/MRR/RFM/ZQ/PDE/PDX/RFM/SRE/SREF) 발급
- [ ] PRE 3 mode (PREab/PREsb/PREpb) 모두 사용
- [ ] REF 2 mode (REFab/REFsb) + RFM 2 mode (RFMab/RFMsb) 모두 사용
- [ ] 2-cycle command (ACT/WRP/WRPA/MRW) cancel 시나리오 검증 — tCMD_cancel=8 nCK
- [ ] BL16 / BL32 / BC8 모두 사용 (MR0:OP[1:0] 4 값 모두)
- [ ] CW=H 시 DRAM이 MRW 무시 확인

#### Mode Register (정밀)
- [ ] MR0~MR24 (priority 25개) 모두 RAL register model 보유
- [ ] MR23 mutual exclusion SVA pass
- [ ] MR4 Wide Range mode (OP[5]=1) 검증 — 95~100°C, >100°C 시나리오
- [ ] MR4 TUF (OP[7]) 동작 — set 후 MRR로 clear 확인
- [ ] MR58/MR59 RFM 설정 + ARFM Level Default/A/B/C 모두 hit
- [ ] MR14 CID 설정 (3DS-DDR5) — 모든 logical rank coverage

#### Timing (정밀)
- [ ] DDR5 speed bin 3개 이상 (예: 4800, 6400, 8400) 별도 SVA threshold
- [ ] tCMD_cancel (8 nCK) 검증
- [ ] tPPD (Precharge to Precharge) 검증
- [ ] MR6 의 PRAC vs Legacy mode 별 tWR/tRTP 둘 다 검증
- [ ] tDFE (80 ns) — DFE MR write 후 settling

#### Refresh / RFM
- [ ] tREFI x1 / tREFI/2 (2x) 두 모드 검증
- [ ] Temperature transition (80°C → 95°C → 100°C) 시 TUF + tREFI 자동 전환
- [ ] RAAIMT threshold 도달 시 RFM 발급 확인
- [ ] RAAMMT 도달 직전 RFM 발급 완료 (overflow 방지)
- [ ] ARFM Level 전환 시나리오 (Default ↔ A ↔ B ↔ C)
- [ ] DRFM enable 시 directed row refresh

#### ECC + PPR
- [ ] Single-bit error → ECC correct → MR16~MR20 통계 update
- [ ] Multi-bit (2-bit) error → detect (epoch error report) + MR19 REC update
- [ ] ECS in Self Refresh 시나리오 (MR15:OP[3]=1)
- [ ] ETC threshold (4, 16, 64, 256, 1024, 4096) 별 동작
- [ ] hPPR + sPPR + sPPR Undo + sPPR Lock + mPPR + MBIST 6가지 동작
- [ ] Guard Key correct vs incorrect 둘 다 검증
- [ ] **MR23 mutual exclusion**: 동시에 2비트+ enable 시 spec violation catch

### 9.5 Spec Violation 시뮬레이션 (negative testing)

DRAM 모델이 *spec violation을 거부*하는지 검증:

```systemverilog
// Negative test set — 의도적 위반 발생 → SVA/Scoreboard가 catch해야 함
class ddr5_negative_test_suite extends uvm_sequence;
    `uvm_object_utils(ddr5_negative_test_suite)

    virtual task body();
        // 1. tRCD 위반: ACT 후 tRCD-1 cycle에 RD
        do_violation_act_then_rd_too_soon();

        // 2. 24 Gb non-binary: row[16]=1 + row[15]=1 (1/4 invalid space)
        if (density == DENSITY_24Gb) do_violation_invalid_row();

        // 3. MR23 multi-bit enable: hPPR + sPPR 동시 1
        do_violation_mr23_multi_enable();

        // 4. CKE=0 동안 MRW 발급
        do_violation_mrw_during_cke_low();

        // 5. 2-cycle command cancel 후 PRE 없이 MRR
        do_violation_mrr_after_cancel();

        // 6. RFM Required=1 인데 CA9=L 로 REF 발급
        do_violation_ref_without_ca9_high();

        // 7. x4 device에 DM/TDQS enable
        if (organization == ORG_X4) do_violation_x4_dm_tdqs();

        // 8. tFAW 윈도우 안에 5번째 ACT
        do_violation_5_acts_in_tfaw();

        // 9. Guard Key 잘못된 후 PPR 시도 — PPR이 *발급 안 됨* 확인
        do_negative_test_ppr_with_wrong_key();

        // 모든 negative test는 SVA fail + UVM_ERROR 발생 또는
        // DRAM이 명령 거부 + 데이터 무결성 유지를 확인
    endtask
endclass
```

## 10. 핵심 정리 (Key Takeaways)

- DRAM TB는 *5개 컴포넌트*: agent(driver/monitor/seqr) + scoreboard + reference model + coverage collector + SVA bind.
- Memory reference model은 *functional* (mem[addr]=data) 전략 권장. timing은 SVA가 별도 검증.
- Coverage 6 카테고리: command / timing / MR / training / refresh / ECC. 모두 *통합*해야 sign-off 의미.
- SVA 3 분류: *timing violation* / *command order* / *training protocol*.
- SVA는 `bind`로 부착 — RTL 수정 없이.
- Regression은 *3-Tier*: smoke / constrained-random / coverage-hole 채우기.
- Sign-off는 *checklist 기반* — 모든 항목 명시적 통과 또는 *waive 사유* 기록.
- **Spec corner cases**: 24 Gb non-binary row, MR23 mutual exclusion, MR4 TUF flag, MR58:OP[0]=0 RFM 동작, ECC ETC threshold, 2-cycle cancel 후 sequence 제약 등 *반드시 명시적 SVA + directed test*.
- **Negative testing**: 의도적 spec violation 시퀀스로 SVA/scoreboard *실제 동작* 확인.
- **RAL register model**: 핵심 MR 25개 이상 모델링 — MR0~MR8 + MR10~MR24 + MR58/MR59.

## 11. Further Reading

- 이전: [Ch09. 신뢰성·ECC·CRC·PPR](../09_reliability_ecc_crc/)
- 다음: [Ch11. DV 프로젝트 End-to-End](../11_dv_project_endtoend/)
- 부록 C: [SVA / Coverage 예제 모음](../appendix_c_sva_coverage_examples/)
- 퀴즈: [Ch10 퀴즈](../quiz/ch10_quiz/)

