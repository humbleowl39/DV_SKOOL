---
title: "Ch09. 신뢰성·ECC·CRC·PPR"
---

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">CH 09</span>
</div>

## 🎯 Learning Objectives

- **Distinguish**: DDR5 Transparency (On-die) ECC와 LPDDR5 Link ECC의 *보호 대상*과 *동작 시점*을 구별한다.
- **Explain**: CRC (Cyclic Redundancy Check) 가 *write data*만 보호하는 이유를 설명한다.
- **Compare**: hPPR (hard Post Package Repair) vs sPPR (soft) 의 영구성과 사용 시점을 비교한다.
- **Apply**: ECC syndrome injection + scoreboard 검증 로직을 설계한다.

## Prerequisites

- [Ch08. Training](../08_training/)
- 기본 ECC 개념 (SECDED, Hamming code, syndrome)

## 1. 신뢰성 보호의 두 영역 — 어디서 무엇을 보호하는가

DRAM 데이터는 두 단계에서 오류가 발생할 수 있습니다. 첫째는 DRAM 셀 내부에서 발생하는 오류입니다. capacitor의 자연 leakage, 우주선에서 날아오는 alpha particle에 의한 soft error, 시간이 지남에 따른 cell aging 등이 원인입니다. 둘째는 DRAM과 controller 사이의 링크에서 발생하는 오류입니다. 수 GT/s의 고속 신호에서 ISI(심볼 간 간섭), jitter, 크로스토크로 인해 전송 중 비트가 바뀔 수 있습니다.

```d2
direction: down

Controller: "Controller (SoC)" {
  Logic: Logic
}

DRAM: "DRAM Device" {
  DQ_IO: "DQ I/O"
  Array: Array
}

Controller.Logic -> DRAM.DQ_IO: "링크 오류 (Link ECC / CRC가 보호)"
DRAM.DQ_IO -> DRAM.Array: "셀-I/O 사이 (on-die ECC가 보호)"
```

같은 "ECC"라는 단어를 쓰더라도 보호 대상이 완전히 다릅니다. DDR5의 Transparency ECC는 셀 내부를 보호하고 controller에게는 투명하게 동작하는 반면, LPDDR5의 Link ECC는 DQ 핀과 controller 사이 링크를 보호합니다. DV는 두 가지를 별도로 설계하고 검증해야 합니다. 한 가지만 검증하고 다른 것을 빠뜨리면 보호되지 않는 오류 경로가 생깁니다.

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

**PPR (Post Package Repair)**: DRAM이 패키지로 나온 후에 fail row가 발견되면 spare row로 redirect하는 수리 기능입니다.

- **hPPR (hard)**: 영구적입니다. DRAM 내부의 antifuse를 물리적으로 프로그래밍하여 fail row 대신 spare row가 사용되도록 영구히 바꿉니다. power cycle 후에도 설정이 유지됩니다.
- **sPPR (soft)**: 임시적입니다. fuse를 바꾸지 않고 controller의 redirect table만 변경합니다. power cycle이 발생하면 설정이 사라지므로, 재부팅 후 다시 적용해야 합니다.

PPR은 강력한 기능인 만큼 보안 메커니즘도 있습니다. 실수로 정상 row를 수리하거나 악의적인 접근을 막기 위해 Guard Key 시퀀스(MR24)를 정확히 입력해야만 PPR이 발동됩니다.

PPR 절차:
1. controller가 fail row 주소 식별
2. Guard Key 시퀀스 — MR24에 정해진 순서로 key write
3. PPR mode 진입 (MR23 설정)
4. WRA (Write with Auto Precharge) 같은 명령에 PPR 지시
5. tPGM (program time) 대기 — hPPR은 ms 단위로 더 길음
6. PPR exit

---

## 3. DDR5 Transparency ECC — 가장 중요한 신규 기능

> 출처: JESD79-5C.01 v1.31 §3.5.16 (MR14), §3.5.17 (MR15), §3.5.18~3.5.22 (MR16~MR20)

### 3.1 Transparency ECC란

"Transparency"는 controller에게 투명하다는 의미입니다. controller가 WR 명령을 발급하면 DRAM이 내부에서 ECC 인코딩을 수행한 뒤 데이터와 parity를 cell array에 함께 저장합니다. RD 명령에서는 array에서 읽은 값을 ECC 디코딩하여 1-bit 오류면 자동으로 정정한 후 DQ에 출력합니다. controller는 이 과정을 전혀 알지 못하고 단지 정상 데이터를 받습니다.

```
Write:  data → DRAM ECC encoder → [data + parity bits] → cell array
Read:   cell array → ECC decoder → error correct → data → DQ
```

투명하다는 것이 "DV가 신경 쓸 필요 없다"는 의미는 아닙니다. ECC가 제대로 동작하지 않으면 단일 비트 오류가 정정되지 않고 controller에 전달될 수 있는데, 이는 silent corruption으로 매우 위험합니다. 또한 DRAM이 MR14~MR20을 통해 에러 통계를 노출하므로, 이 통계가 정확히 갱신되는지도 검증해야 합니다.

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

:::tip[Q. LPDDR5 Link ECC가 8-bit data + 4-bit parity로 SECDED 동작한다고 *가정*하자 (실제 LPDDR5 ECC matrix는 spec §7.7.8 참조). data=8'b1010_1100, parity=4'b0110 으로 전송되었는데 DRAM이 receive한 값이 data=8'b1010_1101 (bit 0 flip)이라면, syndrome은 어떻게 나오고 ECC가 어떻게 정정하는가?]
:::
<details>
<summary>풀이 (개념적 syndrome 계산)</summary>


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

</details>
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

## 12. PDF 정밀 인용 — DDR5 §3.5.16~§3.5.26 (Transparency ECC + PPR)

> 출처: JESD79-5C.01 v1.31 §3.5.16~§3.5.26

### 12.1 MR14 (MA[7:0]=0EH) — Transparency ECC Configuration

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| ECS Mode | Reset ECS Counter | Row Mode / Code Word Mode | RFU | CID3 | CID2 | CID1 | CID0 |

| Function | Type | Operand | Data |
|---|---|---|---|
| **ECS Error Register Index / MBIST Rank Select** | R/W | OP[3:0] | CID[3:0] — 3DS stack 내 어느 slice를 reference |
| **Code Word / Row Count** | R/W | OP[5] | `0B`: ECS counts **Rows** with errors<br>`1B`: ECS counts **Code words** with errors |
| **ECS Reset Counter** | W | OP[6] | `0B`: Normal (Default)<br>`1B`: Reset ECC Counter |
| **ECS Mode** | R/W | OP[7] | `0B`: Manual ECS Mode **Disabled** (Default)<br>`1B`: Manual ECS Mode **Enabled** |

> NOTE 1: "MR14:OP[3:0] must be setup by MRW to indicate which slice in the 3DS-DDR5 stack is referenced by the MRR for MR14~MR20 ECS transparency data, MR22 MBIST transparency data, and MR54-MR57 hPPR resource availability."
>
> NOTE 4: "ECS stands for **Error Check Scrub operation**."

### 12.2 MR15 (MA[7:0]=0FH) — Transparency ECC Threshold per Gb + Auto ECS in Self Refresh

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| x4 Writes | ECS Writeback | RFU | RFU | Automatic ECS in Self Refresh | ECS Error Threshold Count (ETC) [OP2:0] | ← | ← |

**OP[2:0] — ECS Error Threshold Count (ETC) R/W**:

| OP[2:0] | Threshold |
|---|---|
| `000B` | 4 |
| `001B` | 16 |
| `010B` | 64 |
| `011B` (Default) | **256** |
| `100B` | 1024 |
| `101B` | 4096 |
| `110B`-`111B` | RFU |

| Function | Type | Operand | Data |
|---|---|---|---|
| Automatic ECS in Self Refresh | W | OP[3] | `0B`: Disabled in Manual ECS mode (default)<br>`1B`: Enabled in Manual ECS mode |
| ECS Writeback | R/W | OP[6] | `0B`: Do not suppress writeback of Data and ECC Check Bits (Default)<br>`1B`: Suppress writeback (Optional) |
| x4 Writes | R/W | OP[7] | `0B`: Do not suppress writeback of Data during RMW (Default)<br>`1B`: Suppress writeback of Data during RMW (Optional) |

DV 시사점:
- **ETC = 256 default** → 누적 error count가 256 도달 시 *통계 update* (controller가 MR20 read로 감지 가능)
- **ECS Writeback suppress** = ECC 정정한 결과를 *cell에 다시 write 하지 않음* — soft error 누적 위험 ↑ 그러나 다른 시스템 효과 (예: power 절약)
- **x4 Writes suppress** = RMW (Read-Modify-Write) 시 *partial data writeback 억제*

### 12.3 MR16/17/18 — Row Address with Max Errors (Read-Only)

> §3.5.18~3.5.20

**MR16 (MA[7:0]=10H)** — Max Row Error Address R[7:0]:

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| R7 | R6 | R5 | R4 | R3 | R2 | R1 | R0 |

**MR17 (MA[7:0]=11H)** — Max Row Error Address R[15:8]:

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| R15 | R14 | R13 | R12 | R11 | R10 | R9 | R8 |

**MR18 (MA[7:0]=12H)** — Max Row Error Address (BG, BA, R17/R16):

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| RFU | BG2 | BG1 | BG0 | BA1 | BA0 | R17 | R16 |

> NOTE 2 (MR18): BG2 is don't care for x16.
> NOTE 3: BA1 is don't care for 8 Gb.
> NOTE 4: R16 is don't care for 8 Gb and 16 Gb.
> NOTE 5: R17 is don't care for 8 Gb, 16 Gb, 24 Gb, and 32 Gb.

DV 시사점:
- MR16+MR17+MR18 = **완전한 BG/BA/Row 주소** of *가장 많은 error 발생한 row*
- Controller는 *3개의 MRR* 명령으로 *전체 주소* 회수 → repair 또는 monitoring
- Density별 don't care 비트 다름 — RAL register model이 density-aware

### 12.4 MR19 (MA[7:0]=13H) — Max Row Error Count (R)

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| PASR | RFU | REC5 | REC4 | REC3 | REC2 | REC1 | REC0 |

| Function | Type | Operand | Data |
|---|---|---|---|
| **Max Row Error Count REC[5:0]** | R | OP[5:0] | Contains number of errors within the row with the most errors (0~63) |
| RFU | RFU | OP[6] | |
| **PASR support indicator** | R | OP[7] | `0` = PASR not supported, `1` = PASR supported |

> NOTE 2: Support of **PASR has been deprecated starting with spec working revision 1.90 of JESD79-5C-v1.30**.

### 12.5 MR20 (MA[7:0]=14H) — Error Count (EC, R)

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| EC7 | EC6 | EC5 | EC4 | EC3 | EC2 | EC1 | EC0 |

| Function | Type | Operand | Data |
|---|---|---|---|
| Error Count EC[7:0] | R | OP[7:0] | Contains the **error count range data** |

> EC[7:0] = 8-bit error count "range" (실제 count보다는 *range/bucket* 표현 — vendor specific 가능)

### 12.6 MR21 (MA[7:0]=15H) — Rx CTLE Control Setting (DQS)

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| RFU | RFU | RFU | RFU | RFU | Rx DQS CTLE Control (Optional) [OP2:0] | ← | ← |

| OP[2:0] | Setting |
|---|---|
| `000B` (Default) | Vendor Optimized Setting |
| `001B` ~ `111B` | Vendor defined |

> NOTE 1: "Rx CTLE is an optional feature on DDR5. It may be needed for DRAMs that operate at **≥6000 Mbps**. MR22:OP[3] indicates host whether Rx CTLE is supported or not."
>
> NOTE 5: "MR21:OP[2:0] controls **both upper and lower DQS** (U/LDQS) for X16 DRAMs."

→ Rx CTLE (Continuous Time Linear Equalizer) 는 *DFE와 별도의 receiver-side equalizer*. 6000 Mbps 이상 device에서 typically 필요.

### 12.7 MR22 (MA[7:0]=16H) — MBIST/mPPR Transparency, Rx CTLE Control

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| Rx CS_n CTLE Control [OP7:6] | ← | Rx CA CTLE Control [OP5:4] | ← | Rx CTLE Support | MBIST/mPPR Transparency [OP2:0] | ← | ← |

**OP[2:0] — MBIST/mPPR Transparency (R)**:

| Code | 의미 |
|---|---|
| `000B` (Default) | MBIST hasn't run since INIT OR no fails remain after most recent run |
| `001B` | Fails remain |
| `010B` | **Unrepairable fails remain** |
| `011B` | MBIST should be run again |
| `100B`-`111B` | Reserved |

**OP[3] — Rx CTLE Support (R)**: 0B not supported, 1B supported

**OP[5:4] — Rx CA CTLE Control (R/W)**: 00B Vendor Optimized (Default), 01B/10B/11B Vendor defined

**OP[7:6] — Rx CS_n CTLE Control (R/W)**: same encoding

### 12.8 MR23 (MA[7:0]=17H) — MBIST/PPR Settings (핵심)

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| RFU | RFU | MBIST (Optional) | mPPR (Optional) | sPPR Undo/Lock | sPPR | hPPR | (note) |

| Function | Type | Operand | Data |
|---|---|---|---|
| **hPPR** | R/W | OP[0] | `0B`: Disable<br>`1B`: Enable |
| **sPPR** | R/W | OP[1] | `0B`: Disable<br>`1B`: Enable (See OP[2] for sPPR Undo/Lock) |
| **sPPR Undo/Lock** | SR/W | OP[2] | SR: `0B`= Not Implemented (Default), `1B`= sPPR Undo/Lock Implemented<br>Host Write (W) for OP[2:1]: `00B`= Disabled (Normal), `01B`= sPPR Enabled, `10B`= sPPR Undo Enabled, `11B`= sPPR Lock Enabled |
| **mPPR** | W | OP[3] | `0B`: Disable<br>`1B`: Enable (Optional) |
| **MBIST** | SR/W | OP[4] | SR: `0B`= No MBIST/mPPR Support, `1B`= Supports MBIST/mPPR (Optional)<br>Host Write (W): `0B`= MBIST Disabled, `1B`= MBIST Enable |

> NOTE 1: "**Only one of these opcode bits may be programmed by the host to 1 at any given time**. If any one of these opcode bits are enabled, the remaining bits must be programmed to 0."
>
> NOTE 2: "DRAM will automatically write to 0 when MBIST completes."
>
> NOTE 3: "For 3DS-DDR5 devices, MBIST Enable (MR23:OP[4]=1) is only enabled on the target logical rank designated by CID[3:0] and programmed by MRW via MR14:OP[3:0]."

→ **PPR / MBIST 상호 배타**: hPPR / sPPR / sPPR Undo / sPPR Lock / mPPR / MBIST 중 *동시에 단 하나*만 enabled. 다른 비트는 0 강제. DV는 SVA로 위반 검증.

```systemverilog
property p_mr23_mutually_exclusive;
    @(posedge clk) (ral.MR23.value != 8'h00) |->
        $countones(ral.MR23.value[4:0]) == 1;
endproperty
a_mr23_excl: assert property (p_mr23_mutually_exclusive)
    else `uvm_error("MR23_VIOL", "Multiple PPR/MBIST bits set simultaneously")
```

### 12.9 MR24 (MA[7:0]=18H) — PPR Guard Key

| OP[7] | OP[6] | OP[5] | OP[4] | OP[3] | OP[2] | OP[1] | OP[0] |
|---|---|---|---|---|---|---|---|
| PPR Guard Key [OP7:0] | ← | ← | ← | ← | ← | ← | ← |

| Function | Type | Operand | Data |
|---|---|---|---|
| PPR Guard Key | W | OP[7:0] | See PPR Section for Sequence |

> **PPR Guard Key 시퀀스**: PPR (hPPR/sPPR) 발급 *전에* 정해진 sequence로 *Guard Key 값들*을 MR24에 write. 잘못된 key 시퀀스 시 PPR은 *발급되지 않음* (안전장치).

### 12.10 DV 통합 — ECC error injection + MR mirror verify

```systemverilog
// 출처: JESD79-5C.01 §3.5.17~22
// ECC injection + 모든 통계 MR readback 확인
class ddr5_full_ecc_verify_seq extends uvm_sequence;
    `uvm_object_utils(ddr5_full_ecc_verify_seq)

    rand int n_errors;        // 주입할 error 개수
    rand bit [16:0] target_row;
    constraint c_errors { n_errors inside {[1:300]}; }
                          // ETC=256 threshold 넘는 cases 포함

    virtual task body();
        uvm_status_e status;
        bit [7:0] mr_val;

        // 1. ETC threshold 설정 (256 default)
        ral.MR15.ecs_threshold.set(3'b011);
        ral.MR15.update(status);

        // 2. Auto ECS in Self Refresh 활성화
        ral.MR15.auto_ecs_sref.set(1'b1);
        ral.MR15.update(status);

        // 3. ECS Mode 활성화 + Counter Reset
        ral.MR14.ecs_mode.set(1'b1);
        ral.MR14.reset_ecs_counter.set(1'b1);
        ral.MR14.update(status);

        // 4. N errors 주입 (backdoor force in target row)
        for (int i = 0; i < n_errors; i++) begin
            inject_single_bit_error(target_row, i);  // 다른 col마다
        end

        // 5. Self Refresh 진입 → Auto ECS 실행
        do_self_refresh_with_duration(.duration_us(10000));

        // 6. Self Refresh 종료 후 모든 통계 MR readback
        ral.MR16.read(status, mr_val, UVM_FRONTDOOR);  // R[7:0]
        bit [17:0] err_row;
        err_row[7:0] = mr_val;
        ral.MR17.read(status, mr_val, UVM_FRONTDOOR);  // R[15:8]
        err_row[15:8] = mr_val;
        ral.MR18.read(status, mr_val, UVM_FRONTDOOR);  // R[17:16] + BG + BA
        err_row[17:16] = mr_val[1:0];

        if (err_row != target_row)
            `uvm_error("ECC_ROW_MISMATCH",
                $sformatf("MR16/17/18 row=0x%x, expected=0x%x", err_row, target_row))

        ral.MR19.read(status, mr_val, UVM_FRONTDOOR);  // Max Row Error Count
        if (mr_val[5:0] < n_errors && n_errors < 64)
            `uvm_warning("ECC_REC", "REC less than expected n_errors")

        ral.MR20.read(status, mr_val, UVM_FRONTDOOR);  // Error Count range
        `uvm_info("ECC_EC", $sformatf("MR20 EC=0x%x for %0d errors", mr_val, n_errors), UVM_MEDIUM)
    endtask

    extern task inject_single_bit_error(bit [16:0] row, int col);
    extern task do_self_refresh_with_duration(int duration_us);
endclass
```

### 12.11 PPR sequence — Guard Key 활용

```systemverilog
// 출처: JESD79-5C.01 §3.5.25, §3.5.26 + PPR section
class ddr5_hppr_with_guard_key_seq extends uvm_sequence;
    `uvm_object_utils(ddr5_hppr_with_guard_key_seq)

    rand bit [16:0] fail_row;
    rand bit [2:0]  fail_bg;
    rand bit [1:0]  fail_ba;

    // Guard Key sequence (vendor specific — example only)
    // 실제 sequence는 DRAM vendor spec 참조
    bit [7:0] guard_keys[$] = '{8'hA5, 8'h5A, 8'h3C, 8'hC3};

    virtual task body();
        uvm_status_e status;
        bit [7:0] mr23_val;

        // 1. Guard Key 시퀀스 — MR24에 정해진 값들 순차 write
        foreach (guard_keys[i]) begin
            ral.MR24.guard_key.set(guard_keys[i]);
            ral.MR24.update(status);
            `uvm_info("PPR_KEY", $sformatf("Guard key #%0d = 0x%x", i, guard_keys[i]), UVM_HIGH)
        end

        // 2. hPPR enable (MR23:OP[0]=1, 다른 비트 = 0)
        ral.MR23.hppr.set(1'b1);
        ral.MR23.sppr.set(1'b0);
        ral.MR23.sppr_undo_lock.set(1'b0);
        ral.MR23.mppr.set(1'b0);
        ral.MR23.mbist.set(1'b0);
        ral.MR23.update(status);

        // 3. ACT fail_row → WRA에 *모두 1로* write (PPR 발급 시그널)
        do_act(fail_bg, fail_ba, fail_row);
        do_wra_with_all_ones(fail_bg, fail_ba, 'h0);

        // 4. tPGM (program time) 대기 — hPPR은 길음 (~ms 단위)
        # `THPGM_MS;

        // 5. hPPR disable
        ral.MR23.hppr.set(1'b0);
        ral.MR23.update(status);

        // 6. Verify — 같은 row에 RD해서 모두 1인지 확인 (spare row 활성)
        do_act(fail_bg, fail_ba, fail_row);
        do_rd(fail_bg, fail_ba, 'h0);
        // ... scoreboard에서 data==all-1 확인 ...
    endtask
endclass

// Negative test — wrong guard key
class ddr5_hppr_wrong_key_seq extends ddr5_hppr_with_guard_key_seq;
    `uvm_object_utils(ddr5_hppr_wrong_key_seq)
    virtual task body();
        // 의도적으로 *잘못된 key* 사용
        guard_keys = '{8'hFF, 8'h00, 8'hFF, 8'h00};   // wrong sequence

        // ... 같은 절차 ...
        // 결과: PPR이 *발급 안 됨*. fail_row가 그대로.
        // scoreboard에서 *fail data*가 read되는지 확인 (PPR 실패 시 정상 동작)
    endtask
endclass
```

### 12.12 ECC + PPR 통합 Coverage

```systemverilog
covergroup ddr5_ecc_ppr_cg with function sample (
    int          ecs_threshold,        // MR15:OP[2:0]
    bit          auto_ecs_sref,        // MR15:OP[3]
    bit          ecs_writeback_supp,   // MR15:OP[6]
    int          ecs_mode,             // MR14:OP[7]
    int          n_errors,             // 주입된 error 개수
    bit [5:0]    rec_value,            // MR19:OP[5:0]
    ppr_type_e   ppr_type,
    bit          guard_key_valid,
    bit          ppr_success
);
    cp_threshold: coverpoint ecs_threshold {
        bins thr_4   = {0};
        bins thr_16  = {1};
        bins thr_64  = {2};
        bins thr_256 = {3};       // default
        bins thr_1k  = {4};
        bins thr_4k  = {5};
    }
    cp_auto_sref: coverpoint auto_ecs_sref;
    cp_n_errors: coverpoint n_errors {
        bins few     = {[1:9]};
        bins medium  = {[10:99]};
        bins many    = {[100:255]};
        bins over_thresh = {[256:$]};
    }
    cp_ppr_type: coverpoint ppr_type;
    cp_guard: coverpoint guard_key_valid;
    cp_ppr_pass: coverpoint ppr_success;

    cx_thresh_errors: cross cp_threshold, cp_n_errors;
    cx_ppr_full: cross cp_ppr_type, cp_guard, cp_ppr_pass {
        ignore_bins illegal_bypass = binsof(cp_guard) intersect {0} &&
                                     binsof(cp_ppr_pass) intersect {1};
    }
endgroup
```

## 13. 핵심 정리 (Key Takeaways)

- 신뢰성 보호는 *두 영역*: 셀 내부(on-die ECC), 링크(Link ECC / CRC).
- **DDR5 Transparency ECC** — controller에게 *투명*하지만 MR14~MR22로 *통계 조회* 가능.
- **MR14 정밀**: ECS Mode (OP[7]), Reset Counter (OP[6]), Row/CodeWord Count Mode (OP[5]), CID[3:0] (OP[3:0]) for 3DS.
- **MR15 정밀**: ETC threshold (OP[2:0], default=256), Auto ECS in Self Refresh (OP[3]), ECS Writeback Suppress (OP[6]), x4 Writes Suppress (OP[7]).
- **MR16+MR17+MR18**: 가장 많은 error row의 *완전한 BG/BA/Row 주소* (3개 MRR로 회수).
- **MR19**: Max Row Error Count REC[5:0] + PASR support 표시 (deprecated).
- **MR20**: Error Count range EC[7:0].
- **MR21/MR22**: Rx CTLE (≥6000 Mbps device에서 사용) + MBIST/mPPR Transparency 상태.
- **MR23 PPR/MBIST**: hPPR/sPPR/sPPR_Undo_Lock/mPPR/MBIST 중 *동시 단 하나*만 enable. SVA로 위반 검증.
- **MR24 Guard Key**: PPR 발급 전 *정해진 sequence*로 key write. 잘못된 key 시 PPR 무시 (안전장치).
- **ECS (Error Check Scrub)**: Self Refresh 중 background에서 cell scan + correct + writeback. ETC threshold 도달 시 *통계 update*.
- **LPDDR5 Link ECC** — 링크 신호 무결성 보호. DBI와의 *순서*가 중요.
- **CRC** — write data만 보호. 검증 시 ALERT_n 토글로 응답.
- DV는 *ECC syndrome injection*, *CRC error injection*, *PPR sequence (정확한 guard key 포함)* 를 *별도 testcase*로 검증.
- Scoreboard는 *원본 data*, *MR16~MR20 통계 mirror*, *ECC report flag* 를 *모두* 추적해야 함.

## 14. Further Reading

- 이전: [Ch08. Training](../08_training/)
- 다음: [Ch10. DV Methodology 통합](../10_dv_methodology/)
- 부록 C: [SVA / Coverage 예제 모음](../appendix_c_sva_coverage_examples/)
- 퀴즈: [Ch09 퀴즈](../quiz/ch09_quiz/)

