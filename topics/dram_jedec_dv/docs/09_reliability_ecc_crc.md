# Ch09. 신뢰성·ECC·CRC·PPR

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="./"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">CH 09</span>
</div>

## 🎯 Learning Objectives

- **Distinguish**: DDR5 Transparency (On-die) ECC와 LPDDR5 Link ECC의 *보호 대상*과 *동작 시점*을 구별한다.
- **Explain**: CRC (Cyclic Redundancy Check) 가 *write data*만 보호하는 이유를 설명한다.
- **Compare**: hPPR (hard Post Package Repair) vs sPPR (soft) 의 영구성과 사용 시점을 비교한다.
- **Apply**: ECC syndrome injection + scoreboard 검증 로직을 설계한다.

## Prerequisites

- [Ch08. Training](08_training.md)
- 기본 ECC 개념 (SECDED, Hamming code, syndrome)

## 1. 신뢰성 보호의 두 영역 — 어디서 무엇을 보호하는가

DRAM 데이터는 두 단계에서 *오류*가 발생할 수 있습니다:

1. **DRAM 셀 내부** — cap leakage, soft error (alpha particle), aging → *on-die ECC*가 보호
2. **DRAM ↔ Controller 링크** — high-speed signaling의 ISI, jitter, crosstalk → *Link ECC* 또는 *CRC*가 보호

```
        ┌────────────────────────────────┐
        │     Controller (SoC)           │
        │    ┌────────┐                  │
        │    │ Logic  │                  │
        │    └───┬────┘                  │
        └────────┼───────────────────────┘
                 │  ← *링크 오류* (Link ECC / CRC가 보호)
                 │
        ┌────────┼───────────────────────┐
        │        ▼                       │
        │    ┌────────┐                  │
        │    │ DQ I/O │                  │
        │    └───┬────┘                  │
        │        │   ← *셀-I/O 사이* (on-die ECC가 보호)
        │    ┌───▼────┐                  │
        │    │ Array  │                  │
        │    └────────┘                  │
        └────────────────────────────────┘
            DRAM Device
```

**핵심 통찰**: 같은 "ECC" 라도 보호 대상이 *완전히 다름*. DV는 두 가지를 *별도*로 검증해야 함.

---

## 2. DDR4 의 신뢰성 메커니즘 — 기본 셋

> 출처: JESD79-4D §4.16 (CRC), §4.17 (CA Parity), §4.32 (hPPR), §4.33 (sPPR)

### 2.1 Write CRC (§4.16)

- *Write data*만 보호
- DRAM이 write burst를 받을 때 CRC 비교 → mismatch면 `ALERT_n` 토글
- CRC 계산 식: standardized polynomial (CRC-8)

```
Write data (BL8 + DBI) → CRC encoder → DRAM
                                     ↓
                              CRC validate
                                     ↓
                            mismatch → ALERT_n
```

### 2.2 CA Parity (§4.17)

- *Command + Address* 신호의 *parity* 검증
- DRAM이 명령 수신 시 parity bit 확인 → mismatch면 *명령 폐기* + `ALERT_n`

```
[CA + ADDR + Parity_bit] → DRAM → parity check
                                  ↓
                           OK    또는    Fail
                                          ↓
                                     ALERT_n + CA Parity Error Log
```

### 2.3 hPPR / sPPR (§4.32, §4.33)

**PPR (Post Package Repair)**: 제조 후 *fail row*가 발견되면 *spare row*로 redirect 가능.

- **hPPR (hard)**: *영구* — DRAM의 fuse를 *물리적으로* 변경
- **sPPR (soft)**: *power-cycle까지만* — fuse는 안 바꾸고 메모리 controller의 redirect table만 변경

PPR 절차:
1. controller가 *fail row 주소* 식별
2. PPR mode 진입 (MR 설정)
3. WRA (Write with Auto Precharge) 같은 명령에 *PPR 지시*
4. tPGM (program time) 대기 — hPPR은 더 길음
5. PPR exit

---

## 3. DDR5 Transparency ECC — 가장 중요한 신규 기능

> 출처: JESD79-5C.01 v1.31 §3.5.16 (MR14), §3.5.17 (MR15), §3.5.18~3.5.22 (MR16~MR20)

### 3.1 Transparency ECC란

"Transparency" = controller에게 *투명* (controller가 ECC 동작을 *모르고* 일반 RD/WR 처리). 그러나 DRAM 내부에서:

```
Write:  data → DRAM ECC encoder → [data + parity bits] → cell array
Read:   cell array → ECC decoder → error correct → data → DQ
```

### 3.2 핵심 MR

- **MR14 — Transparency ECC Configuration**: ECC enable, mode
- **MR15 — Transparency ECC Threshold**: 누적 에러 임계치 + ECS (Error Check & Scrub) in self refresh
- **MR16, MR17, MR18 — Row Address with Max Errors**: 가장 에러 많은 row의 주소
- **MR19 — Max Row Error Count**: max error 발생한 row의 error count
- **MR20 — Error Count (EC)**: 누적 error count

### 3.3 controller가 알 수 있는 정보

DDR5 ECC는 *transparent* 이지만, controller는 *MR read*로 *통계 정보*를 얻을 수 있습니다:
- 어느 row가 가장 자주 에러
- 누적 에러 개수
- threshold 도달 여부

→ DV는 *ECC 통계*가 *정확하게 update*되는지 검증해야 함.

### 3.4 ECS (Error Check & Scrub) in Self Refresh

Self Refresh 동안 DRAM이 *내부적*으로 cell을 *스크럽*. soft error를 *조용히* 정정.

---

## 4. LPDDR5 Link ECC — DRAM↔Controller 보호

> 출처: JESD209-5C §7.7.8

### 4.1 Link ECC란

DDR5의 "transparency ECC" 가 *셀 내부* 보호라면, LPDDR5의 **Link ECC** 는 *링크* (DQ pin) 의 SI (Signal Integrity) 보호.

```
Controller → encoder (ECC) → DQ → DRAM → decoder (ECC) → array (no on-die ECC)
                              ↑
                           link 오류
                       (ISI, jitter, crosstalk)
```

### 4.2 Link ECC 동작 (§7.7.8.1 ~ §7.7.8.6)

- ENCODING: controller 측에서 data + parity 생성
- DECODING: DRAM 측에서 syndrome 계산
- Error Detection / Correction
- Error Reporting: DRAM이 controller에게 *epoch error report*

### 4.3 Link ECC vs DBI 순서 (§7.7.8.6)

DBI(Data Bus Inversion)와 Link ECC가 *함께 enable*되면, *순서가 정의*되어 있어야 함. 일반적으로:
- Write: data → ECC encode → DBI → DQ
- Read: DQ → DBI decode → ECC decode → data

DV는 *이 순서를 정확히* 모델링해야 scoreboard가 옳음.

---

## 5. CRC (DDR5에서도) — Write Data 보호

> 출처: JESD79-5C.01 v1.31 §3.5.51~3.5.53 (MR50~MR52)

DDR5에서도 CRC는 유효. *Write CRC만 표준화* (Read CRC는 일반적 X).

### 5.1 Write CRC 동작

```
Controller: write burst data → CRC computation → append 1+ CRC bits → DQ
DRAM: receive DQ → CRC check
       OK         → 정상 write
       Mismatch   → ALERT_n toggle + write abort (또는 retry 정책)
```

### 5.2 MR50~MR52

- **MR50 — Write CRC Settings**: enable, polynomial
- **MR51 — Write CRC Auto-Disable Threshold**: CRC 오류 연속 발생 시 *자동 disable*
- **MR52 — Auto-Disable Window**: threshold 적용 시간 윈도우

---

## 6. PPR — DDR5 / LPDDR5 의 확장

> 출처: JESD79-5C.01 §3.5.55~3.5.58 (MR54~MR57), §3.5.26 (MR24 PPR Guard Key), JESD209-5C §7.7.4

### 6.1 DDR5 hPPR Resources (MR54~MR57)

DDR5는 *PPR resources*를 MR로 *추적* 가능:
- 사용 가능한 spare row 개수
- 이미 repair된 row의 주소

이로써 controller가 *resource 고갈*을 미리 알 수 있음.

### 6.2 PPR Guard Key (MR24)

PPR은 *영구* 동작이라 *잘못된 발급 방지*를 위해 *guard key* 필요. 정확한 key를 MR24에 write해야 *PPR이 가능*. 보안/안전 메커니즘.

### 6.3 LPDDR5 PPR — Guard Key + Fail Row Repair

- §7.7.4.1 Guard Key Protection
- §7.7.4.2 PPR Fail Row Address Repair

LPDDR5도 *guard key*가 있어 *우발적 PPR* 방지.

---

## 7. DV 적용 — ECC Syndrome Injection

### 7.1 단일 비트 에러 injection

```systemverilog
// DDR5 transparency ECC 검증 — 1-bit error injection
class ddr5_single_bit_error_inject_seq extends uvm_sequence;
    `uvm_object_utils(ddr5_single_bit_error_inject_seq)

    rand int  bit_position;   // [0:127] for 128-bit access
    rand bit [31:0] target_addr;

    virtual task body();
        ddr5_transaction wr_t, rd_t;
        bit [127:0] orig_data, corrupted_data;

        // Step 1: 알려진 data로 WR
        orig_data = 128'h0123_4567_89AB_CDEF_FEDC_BA98_7654_3210;
        `uvm_do_with(wr_t, {
            wr_t.cmd  == CMD_WR;
            wr_t.addr == target_addr;
            wr_t.data == orig_data;
        })

        // Step 2: backdoor로 1 비트 flip
        corrupted_data = orig_data;
        corrupted_data[bit_position] = ~corrupted_data[bit_position];
        backdoor_write(target_addr, corrupted_data);
        `uvm_info("ECC_INJECT",
            $sformatf("Flipped bit %0d at addr 0x%x", bit_position, target_addr),
            UVM_MEDIUM)

        // Step 3: RD → DDR5 on-die ECC가 정정해야 함
        `uvm_do_with(rd_t, {
            rd_t.cmd  == CMD_RD;
            rd_t.addr == target_addr;
        })

        // Step 4: scoreboard가 expected = orig_data 비교
        // → ECC 정상이면 read data == orig_data
        // → ECC 미동작이면 corrupted_data 반환

        // Step 5: MR20 (Error Count) 읽어서 *증가했는지* 확인
        check_mr_error_count();
    endtask

    extern task backdoor_write(bit [31:0] addr, bit [127:0] data);
    extern task check_mr_error_count();
endclass
```

### 7.2 Multi-bit error injection

```systemverilog
// 2-bit 에러 — SECDED 가정 시 detect만 가능 (correct 불가)
class ddr5_double_bit_error_inject_seq extends uvm_sequence;
    `uvm_object_utils(ddr5_double_bit_error_inject_seq)

    rand int bit_pos_1, bit_pos_2;
    constraint c_different { bit_pos_1 != bit_pos_2; }

    virtual task body();
        // ... WR original data ...
        // ... flip 2 bits at bit_pos_1, bit_pos_2 ...
        // ... RD ...
        // → ECC detect (but not correct) → uncorrectable error reported
    endtask
endclass
```

### 7.3 ECC scoreboard 로직

```systemverilog
class ddr5_ecc_scoreboard extends uvm_scoreboard;
    `uvm_component_utils(ddr5_ecc_scoreboard)

    bit [127:0] mem_model [longint];
    int error_count;       // expected = MR20 mirror
    int error_max_row;     // expected = MR19 mirror

    function void write_wr(ddr5_transaction t);
        mem_model[t.addr] = t.data;
    endfunction

    function void write_rd(ddr5_transaction t);
        bit [127:0] expected = mem_model[t.addr];

        // Case 1: 정상 (ECC가 자동 정정)
        if (t.data == expected) begin
            // PASS
        end
        // Case 2: data가 *원본*과 다른데 ECC가 *정정 못한 경우*
        else if (popcount(t.data ^ expected) > 1) begin
            // 2+ bit error — uncorrectable
            // controller가 *이미 알아챈* 상태인지 확인
            if (!t.ecc_error_reported)
                `uvm_error("ECC_UNREPORTED",
                    "Uncorrectable error not reported to controller")
        end
        else begin
            // 1-bit이 살아남았다 = ECC 미동작
            `uvm_error("ECC_DEGRADED", "1-bit error not corrected by on-die ECC")
        end
    endfunction
endclass
```

---

## 8. DV 적용 — CRC error injection

```systemverilog
// Write 시 CRC만 의도적 corruption → DRAM이 ALERT_n 응답해야 함
class ddr5_crc_error_inject_seq extends uvm_sequence;
    `uvm_object_utils(ddr5_crc_error_inject_seq)

    virtual task body();
        ddr5_transaction t;
        `uvm_do_with(t, {
            t.cmd       == CMD_WR;
            t.bl        == 16;
            t.corrupt_crc == 1;       // CRC만 의도적으로 잘못
        })
        // ... ALERT_n monitor — toggle 발생해야 함 ...
        @(negedge alert_n);
        `uvm_info("CRC_INJECT", "ALERT_n triggered as expected", UVM_MEDIUM)
    endtask
endclass

// Coverage
covergroup crc_inject_cg with function sample (int num_burst_with_bad_crc);
    cp: coverpoint num_burst_with_bad_crc {
        bins single      = {1};
        bins burst       = {[2:5]};
        bins many        = {[6:$]};  // auto-disable threshold 도달
    }
endgroup
```

---

## 9. DV 적용 — PPR sequence coverage

```systemverilog
typedef enum {
    PPR_HPPR_WRA,    // hPPR with Write Auto-precharge case
    PPR_HPPR_WR,     // hPPR with Write case
    PPR_SPPR         // soft PPR
} ppr_type_e;

covergroup ppr_cg with function sample (
    ppr_type_e type_,
    bit guard_key_correct,
    bit ppr_success
);
    cp_type: coverpoint type_ {
        bins hppr_wra = {PPR_HPPR_WRA};
        bins hppr_wr  = {PPR_HPPR_WR};
        bins sppr     = {PPR_SPPR};
    }
    cp_guard: coverpoint guard_key_correct {
        bins correct   = {1};
        bins incorrect = {0};   // PPR must fail
    }
    cp_success: coverpoint ppr_success {
        bins yes = {1};
        bins no  = {0};
    }
    cx_full: cross cp_type, cp_guard, cp_success {
        ignore_bins illegal_pass_with_bad_key =
            binsof(cp_guard.incorrect) && binsof(cp_success.yes);
    }
endgroup
```

---

## 10. 대표 문제 — LPDDR5 Link ECC syndrome 계산 예시

!!! question "Q. LPDDR5 Link ECC가 8-bit data + 4-bit parity로 SECDED 동작한다고 *가정*하자 (실제 LPDDR5 ECC matrix는 spec §7.7.8 참조). data=8'b1010_1100, parity=4'b0110 으로 전송되었는데 DRAM이 receive한 값이 data=8'b1010_1101 (bit 0 flip)이라면, syndrome은 어떻게 나오고 ECC가 어떻게 정정하는가?"

???+ answer "풀이 (개념적 syndrome 계산)"

    **Step 1 — SECDED Hamming 기본 원리** *(추론 — LPDDR5 실제 행렬은 스펙 참조)*

    SECDED (Single Error Correction, Double Error Detection) 의 일반 형태:
    - encoder: H matrix × data = parity
    - decoder: H × [data | parity] = syndrome
    - syndrome = 0: no error
    - syndrome ≠ 0 + 단일 column 매칭: single bit error → 그 비트 flip
    - syndrome ≠ 0 + double bit pattern: uncorrectable

    **Step 2 — 단순 예시 (4-bit data, 3-bit parity Hamming(7,4))**

    위 문제의 8+4 = 12-bit 코드워드는 실제 SECDED가 아닐 수 있지만, *원리*는 같음. 단순화해서 Hamming(7,4) 로 시연:

    - data d3 d5 d6 d7 = 1 0 1 0 (예시)
    - parity p1 p2 p4 = computed from H matrix
    - 전송: [p1 p2 d3 p4 d5 d6 d7]

    DRAM 수신 시 bit 0이 flip 되었다고 가정:
    - syndrome = received × H^T
    - syndrome ≠ 0 → 어떤 column index의 H column과 일치 → 그 비트가 flip된 것
    - 정정: 해당 비트 toggle

    **Step 3 — LPDDR5 Link ECC 의 실제 동작**

    LPDDR5 §7.7.8 의 *ECC Check Matrix*가 정의되어 있음 (스펙 figure 참조).
    - Encoding: data 64-bit + parity 8-bit (예시 가정) → 72-bit 전송
    - Decoding: syndrome 계산 → table lookup으로 *어느 비트가 오류*인지
    - Single bit: 자동 정정
    - Double bit: detect만, controller에게 *epoch error report*

    **Step 4 — DV 적용**

    1. ECC encoder/decoder 모델을 *reference model*로 구현
    2. WR 시 controller가 encoding한 parity가 *spec matrix*와 일치하는지 검증
    3. DQ에 *force*로 1-bit flip 후 RD → 정정되는지 확인
    4. *2-bit flip* 후 RD → uncorrectable detect 되는지 확인 (epoch error report)
    5. covergroup `link_ecc_cg`:
       - bins `no_error`, `single_bit_corrected`, `double_bit_detected`
       - 각 bin이 *충분한 횟수* hit되어야 sign-off 가능

    **Step 5 — 함정 — DBI와의 상호작용**

    LPDDR5 §7.7.8.6 — *ECC and DBI – Order of Operations*. 만약 ECC가 DBI 전에 적용되는데 scoreboard가 *DBI 적용 후*에 비교하면 false fail. 순서를 *정확히* 모델링해야 함.

---

## 11. 비교 표 — 4 스펙의 신뢰성 메커니즘

| 메커니즘 | DDR4 | DDR5 | LPDDR4 | LPDDR5 |
|---|---|---|---|---|
| Write CRC | ✓ | ✓ (MR50~52) | (옵션) | (옵션) |
| CA Parity | ✓ | (다른 방식) | (옵션) | (옵션) |
| On-die ECC | — | **Transparency ECC** (MR14~20) | — | (있음, 일부 device) |
| Link ECC | — | — | — | **있음** (§7.7.8) |
| hPPR | ✓ | ✓ (MR54~57) | ✓ | ✓ (§7.7.4) |
| sPPR | ✓ | ✓ | — | — |
| MBIST PPR | ✓ (§4.34) | ✓ | — | — |
| Guard Key | — | ✓ (MR24) | — | ✓ |
| ECS in Self Refresh | — | ✓ (MR15) | — | (옵션) |

---

## 12. 핵심 정리 (Key Takeaways)

- 신뢰성 보호는 *두 영역*: 셀 내부(on-die ECC), 링크(Link ECC / CRC).
- **DDR5 Transparency ECC** — controller에게 *투명*하지만 MR20 등으로 *통계 조회* 가능.
- **LPDDR5 Link ECC** — 링크 신호 무결성 보호. DBI와의 *순서*가 중요.
- **CRC** — write data만 보호. 검증 시 ALERT_n 토글로 응답.
- **PPR** (hard / soft) — fail row redirect. *Guard Key* 가 안전장치.
- DV는 *ECC syndrome injection*, *CRC error injection*, *PPR sequence* 를 *별도 testcase*로 검증.
- Scoreboard는 *원본 data*, *MR error count mirror*, *ECC report flag* 를 *모두* 추적해야 함.

## 13. Further Reading

- 이전: [Ch08. Training](08_training.md)
- 다음: [Ch10. DV Methodology 통합](10_dv_methodology.md)
- 부록 C: [SVA / Coverage 예제 모음](appendix_c_sva_coverage_examples.md)
- 퀴즈: [Ch09 퀴즈](quiz/ch09_quiz.md)

<div class="chapter-nav">
  <a class="nav-prev" href="08_training/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch08. Training</div>
  </a>
  <a class="nav-next" href="10_dv_methodology/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch10. DV Methodology 통합</div>
  </a>
</div>
