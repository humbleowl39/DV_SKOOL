# 부록 A. JEDEC Spec 빠른 참조 (Quick Reference)

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="index.md"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">부록 A</span>
</div>

!!! tip "사용법"
    챕터 본문을 읽을 때 *수치/약어/MR 번호*가 헷갈리면 여기로 돌아오세요. 정확한 spec은 *항상 원본 JEDEC 문서*를 우선.

---

## A.1 핵심 timing 약어 표

| 약어 | 풀어쓰기 | 일반 의미 | 챕터 |
|---|---|---|---|
| tCK | Clock Period | 클럭 한 주기 시간 | Ch01 |
| nCK | number of CKs | 클럭 사이클 수 | Ch06 |
| **tRCD** | Row-to-Column Delay | ACT → RD/WR 최소 cycle | Ch06 |
| **tRP** | Row Precharge | PRE → ACT 최소 cycle | Ch06 |
| **tRAS** | Row Active Strobe | ACT → PRE 최소 active 시간 | Ch06 |
| **tRC** | Row Cycle | ACT → 같은 bank의 다음 ACT (= tRAS+tRP) | Ch06 |
| tWR | Write Recovery | WR 종료 → PRE | Ch06 |
| tRTP | Read to Precharge | RD 종료 → PRE | Ch06 |
| **tRRD_S** | Row-to-Row Delay Short | ACT → 다른 BG의 ACT | Ch06 |
| **tRRD_L** | Row-to-Row Delay Long | ACT → 같은 BG 다른 bank의 ACT | Ch06 |
| **tFAW** | Four Activate Window | 4 ACT in 한 윈도우 | Ch06 |
| **tCCD_S** | CAS-to-CAS Short | RD/WR → 다른 BG의 RD/WR | Ch06 |
| **tCCD_L** | CAS-to-CAS Long | RD/WR → 같은 BG의 RD/WR | Ch06 |
| tCCD_L_WR | CCD_L for Write | DDR5 신규 | Ch06 |
| tWTR_S / tWTR_L | Write-to-Read Short/Long | WR → RD transition | Ch06 |
| **tREFI** | Refresh Interval | REF 평균 간격 (~7.8us) | Ch07 |
| **tRFC** | Refresh Cycle | REF → 다음 명령 가능 | Ch07 |
| CL | CAS Latency | RD 명령 → 첫 data | Ch06 |
| CWL | CAS Write Latency | WR 명령 → 첫 data drive | Ch06 |
| tRPRE / tWPRE | Read/Write Preamble | DQS preamble 시간 | Ch06 |
| tRPST / tWPST | Read/Write Postamble | DQS postamble 시간 | Ch06 |
| tXPR | Exit Reset to CKE | reset → CKE HIGH | Ch03 |
| tZQinit | Initial ZQ Calibration | ZQCL → 정상 | Ch03 |

---

## A.2 DDR5 주요 MR 번호 → 기능 매핑

> 출처: JESD79-5C.01 v1.31 §3.5

| MR | 기능 | 챕터 |
|---|---|---|
| MR0 | Burst Length, CAS Latency | Ch04 |
| MR1 | PDA Mode | Ch04 |
| MR2 | Functional Modes (DLL on/off, Test mode) | Ch04 |
| MR3 | DQS Training | Ch08 |
| MR4 | Refresh Settings (tREFI mode, temp range) | Ch04, Ch07 |
| MR5 | IO Settings (output drive, ODT) | Ch04 |
| MR6 | Write Recovery, tRTP | Ch06 |
| MR7 | Write Leveling Internal +0.5tCK Offset | Ch08 |
| MR8 | Preamble / Postamble | Ch06 |
| MR9 | Writeback Suppression, TM | Ch04 |
| MR10 | VrefDQ Calibration | Ch08 |
| MR11 | VrefCA Calibration | Ch08 |
| MR12 | VrefCS Calibration | Ch08 |
| MR13 | SRX/NOP Clock-Sync, CS Geardown, tCCD_L, tDLLK | Ch03 |
| **MR14** | **Transparency ECC Configuration** | Ch09 |
| **MR15** | **Transparency ECC Threshold + ECS in Self Refresh** | Ch09 |
| MR16~18 | Row Address with Max Errors (1, 2, 3) | Ch09 |
| MR19 | Max Row Error Count | Ch09 |
| MR20 | Error Count (EC) | Ch09 |
| MR21 | Rx CTLE Control Setting (DQS) | Ch08 |
| MR22 | MBIST/mPPR Transparency, Rx CTLE | Ch08 |
| MR23 | MBIST/PPR Settings | Ch09 |
| **MR24** | **PPR Guard Key** | Ch09 |
| MR25~31 | Read Training Mode, Read Pattern, LFSR | Ch08 |
| MR32~40 | ODT — RTT_PARK/WR/NOM, ODTL offset | Ch04 |
| MR41 | RFU | — |
| MR42~48 | DCA Settings (group) | Ch08 |
| MR50 | Write CRC Settings | Ch09 |
| MR51 | Write CRC Auto-Disable Threshold | Ch09 |
| MR52 | Write CRC Auto-Disable Window | Ch09 |
| MR53 | Loopback | Ch08 |
| MR54~57 | hPPR Resources | Ch09 |
| **MR58** | **Refresh Management (RFM)** | Ch07 |
| **MR59** | **DRFM, ARFM, RFM RAA Counter** | Ch07 |
| MR60 | Partial Array Self Refresh (PASR) | Ch07 |
| MR61 | Package Output Driver Test Mode | — |
| MR62 | Vendor Specified | — |
| MR63 | DRAM Scratch Pad | — |
| MR64~69 | Serial Number / NVRAM Paging | — |
| MR70~75 | DFE (global) | Ch08 |
| MR103~254 | DCA per-DQ + DFE per-tap + VrefDQ per-DQ offset | Ch08 |

---

## A.3 LPDDR5 주요 섹션 → 기능 매핑

> 출처: JESD209-5C

| Section | 내용 | 챕터 |
|---|---|---|
| §2 | Overview, Bank Architecture (4B/8B/16B/BG mode) | Ch02 |
| §3 | WCK Clocking | Ch08 |
| §4.1 | Power-up, Initialization, Power-off | Ch03 |
| §4.2.1 | ZQ Calibration | Ch08 |
| §4.2.2 | **Command Bus Training (CBT Mode1, Mode2)** | Ch08 |
| §4.2.3~4 | CA VREF / DQ VREF Training | Ch08 |
| §4.2.5 | **WCK2CK Leveling** | Ch08 |
| §4.2.6~7 | DCA (Duty Cycle Adjuster) + Read DCA | Ch08 |
| §4.2.8 | DCM (Duty Cycle Monitor) | Ch08 |
| §4.2.9 | READ DQ Calibration | Ch08 |
| §4.2.10 | WCK-DQ Training | Ch08 |
| §4.2.11~12 | RDQS Toggle Mode / Enhanced RDQS Training | Ch08 |
| §4.2.13 | Read/Write-based WCK-RDQS_t Training | Ch08 |
| §4.2.14 | Rx Offset Calibration | Ch08 |
| §6 | Mode Register Definitions | Ch04 |
| §7.2 | WCK Operation, WCK2CK Sync | Ch08 |
| §7.3 | Row Operation | Ch05 |
| §7.4 | Read/Write Operation, RDQS Mode | Ch05 |
| §7.5 | **Refresh Operation, PASR, PARC, Deep Sleep** | Ch07 |
| §7.6.3 | **Frequency Set Point** | Ch08 |
| §7.6.4~6 | ODT (Data Bus, Command/Address, CS, NT-ODT) | Ch04 |
| §7.7.1 | **DVFS (DVFSC, Enhanced DVFSC, DVFSQ)** | Ch08 |
| §7.7.4 | **Post Package Repair (PPR) + Guard Key** | Ch09 |
| §7.7.5 | **Refresh Management Command** | Ch07 |
| §7.7.6 | **ARFM / DRFM** | Ch07 |
| §7.7.7 | **DFE (Per-pin)** | Ch08 |
| §7.7.8 | **Link ECC** (encode/decode/error report) | Ch09 |
| §8 | Command Constraint and AC Timing | Ch06 |
| §9 | AC Timing tables | Ch06 |

---

## A.4 DDR4 주요 섹션

> 출처: JESD79-4D

| Section | 내용 | 챕터 |
|---|---|---|
| §2 | Package Pinout and Addressing | Ch02 |
| §3 | Functional Description, Init, MR | Ch03, Ch04 |
| §4.1 | Command Truth Table | Ch05 |
| §4.7 | Write Leveling | Ch08 |
| §4.8 | Temperature Controlled Refresh | Ch07 |
| §4.9 | Fine Granularity Refresh | Ch07 |
| §4.10 | Multi Purpose Register (MPR) | Ch08 |
| §4.13 | DQ Vref Training | Ch08 |
| §4.16 | **CRC** | Ch09 |
| §4.17 | **CA Parity** | Ch09 |
| §4.20 | Programmable Preamble | Ch06 |
| §4.21 | Postamble | Ch06 |
| §4.26 | Refresh Command | Ch07 |
| §4.32 | **hPPR** | Ch09 |
| §4.33 | **sPPR** | Ch09 |
| §5 | On-Die Termination (ODT) | Ch04 |
| §13 | AC Timing tables | Ch06 |

---

## A.5 LPDDR4 주요 섹션

> 출처: JESD209-4E

| Section | 내용 | 챕터 |
|---|---|---|
| §2 | Package Ballout (POP, MCP, Discrete) | Ch02 |
| §3 | Addressing, State Diagram, Init, MR | Ch03, Ch04 |
| §4.5~9 | Read/Write timing, Preamble/Postamble | Ch06 |
| §4.19 | Refresh Command (All-bank, Per-bank) | Ch07 |
| §4.20 | Self Refresh | Ch07 |
| §4.26 | CA VREF Training | Ch08 |
| §4.27 | DQ VREF Training | Ch08 |
| §4.28 | **Command Bus Training (CBT)** | Ch08 |
| §4.29 | Frequency Set Point | Ch08 |
| §4.30 | Write Leveling | Ch08 |
| §4.31 | RD DQ Calibration | Ch08 |
| §4.32 | DQS-DQ Training | Ch08 |
| §4.34 | READ Preamble Training | Ch08 |
| §4.41 | On-Die Termination | Ch04 |
| §4.47 | **Refresh Management Command** | Ch07 |
| §4.48 | **Post Package Repair** | Ch09 |
| §10 | AC Timing | Ch06 |

---

## A.6 DV 카테고리별 우선순위 체크리스트 요약

> 자세한 sign-off는 [Ch10. DV Methodology](10_dv_methodology.md) 또는 [Ch11. DV 프로젝트 End-to-End](11_dv_project_endtoend.md)

**Tier 1 — 반드시 검증**
- [ ] 모든 명령 (ACT/PRE/RD/WR/REF/MRW/MRR) 발급
- [ ] tRCD/tRP/tFAW SVA pass
- [ ] Init sequence + ZQCL
- [ ] WR/RD data integrity (scoreboard)

**Tier 2 — Strongly recommended**
- [ ] RFM (DDR5) / ARFM/DRFM (LPDDR5)
- [ ] Training all steps + fail injection
- [ ] ECC single/multi error scenarios
- [ ] CRC error injection

**Tier 3 — Sign-off 권장**
- [ ] Rowhammer aggressor scenario
- [ ] DVFS FSP transition (LPDDR5)
- [ ] PPR hPPR/sPPR + guard key
- [ ] Extended temperature refresh
- [ ] Deep Sleep Mode (LPDDR5)

---

## A.7 자주 헷갈리는 개념 정리

### "ECC" 가 두 종류 — 어디서 보호?

| ECC 종류 | 보호 대상 | 스펙 |
|---|---|---|
| **DDR5 Transparency (On-die)** | DRAM 셀 내부 (cap, soft error) | JESD79-5C.01 §3.5.16 |
| **LPDDR5 Link ECC** | DRAM ↔ Controller 링크 (DQ pin) | JESD209-5C §7.7.8 |
| (System ECC) | DIMM 또는 host buffer 단위 | non-JEDEC, 시스템 spec |

### "Refresh Management" 가 세 종류 — 어떻게 다른가?

| RM 종류 | 주체 | 정밀도 | 스펙 |
|---|---|---|---|
| DDR5 **RFM** | Controller (RAA tracking) | Counter threshold | JESD79-5C.01 §3.5.59 |
| LPDDR5 **ARFM** | DRAM hint + Controller | Coarse 영역 | JESD209-5C §7.7.6.1 |
| LPDDR5 **DRFM** | Controller 명시 지정 | Fine row 단위 | JESD209-5C §7.7.6.2 |

### "Training" 단계 너무 많아 — 한 줄로 정리

| Training | 무엇을 정렬 | 스펙 위치 |
|---|---|---|
| ZQ Calibration | output impedance | DDR5 §3.5.65 / LPDDR5 §4.2.1 |
| CS Training | CS signal | DDR5 §3.5.16 (CS Geardown) |
| CA / Command Bus Training | CA[6:0] | DDR4 MPR / LPDDR4 §4.28 / LPDDR5 §4.2.2 |
| DQ Vref Training | DQ Vref | DDR5 MR10 / LPDDR5 §4.2.4 |
| DQS / Read DQS Training | DQS strobe | DDR5 MR3 |
| Write Leveling | DQS vs CK | DDR4 §4.7 / DDR5 MR7 / LPDDR5 WCK2CK §4.2.5 |
| WCK2CK Leveling | WCK vs CK | LPDDR5 §4.2.5 |
| DCA / DCM | duty cycle | DDR5 MR42~ / LPDDR5 §4.2.6~4.2.8 |
| DFE | ISI 보상 | DDR5 MR70~ / LPDDR5 §7.7.7 |

---

<div class="chapter-nav">
  <a class="nav-prev" href="11_dv_project_endtoend.md">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch11. DV 프로젝트 End-to-End</div>
  </a>
  <a class="nav-next" href="appendix_b_glossary.md">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">부록 B. Glossary</div>
  </a>
</div>
