# `hbm4_jedec_dd` — JESD270-4 스펙 인덱스 (S1)

작성일 2026-08-30 · 용도: 12개 챕터 집필 시 **인용 근거 좌표**

## 원문 정보

| 항목 | 값 |
|---|---|
| 제목 | High Bandwidth Memory (HBM4) DRAM |
| 표준 번호 | **JESD270-4** |
| 발행 | 2025-04 |
| 분량 | 280쪽 · 표 147개 · 그림 123개 |
| 저작권자 | JEDEC Solid State Technology Association |
| 문서 상태 | **WIP draft** (PDF 속성 Keywords) — 최종 발행본과 다를 수 있음 |

> ⚠️ **취급 규칙**
> 1. **PDF를 저장소에 커밋하지 않는다.**
> 2. 표·그림을 **그대로 옮기지 않는다.** 구조와 의미를 재구성하고 **절/표/그림 번호로 인용**한다.
> 3. 각 챕터와 index에 고지 배너를 넣는다 — *"학습 목적의 요약·참조이며 원문의 복제가 아님. 정밀 수치는 JEDEC 원문 우선."*
> 4. 문서가 **draft**임을 명시한다.

---

## 절 → 챕터 매핑

| 챕터 | 규격 절 | 핵심 표·그림 |
|---|---|---|
| **01** 규격 지형도·조직 | §1 Scope · §2 Features · §3 Organization · §3.1 Channel Definition (3.1.1 Signal Count / 3.1.2 Pseudo Channel Definition / 3.1.3 Dual Command Interfaces) | Table 1–3, Figure 1–2 |
| **02** 주소 체계·뱅크 그룹 | §3.2 Channel Addressing · §3.2.1 Bank Groups · §3.3 Simplified State Diagram | Table 4–6, Figure 3 |
| **03** 초기화·리셋·전원 | §4 Initialization · §4.1 Power-up · §4.2 Stable Power · §4.3 Controlled Power-off · §4.4 IEEE1500 경유 (Lane Repair / Channel Disable) | Table 7–8, Figure 4–8 |
| **04** Mode Register | §5 Mode Registers | Table 9(개요)–23+ (MR0~MR12+), Table 18(DWORD MISR) |
| **05** 클럭킹·DBIac | §6.1 Clocking Overview · §6.1.1 WDQS-to-CK Alignment Training · §6.2 DBIac | Figure 9–16 |
| **06** Row 커맨드 | §6.3.1 Command Truth Tables · §6.3.2 Row Commands (RNOP / ACT / PREpb·PREab / Rounding Rules / Refresh) · §6.3.2.5.1 REFab · .2 REFpb · .3 RFM · .4 **ARFM** · .5 **DRFM** | Figure 17–32 |
| **07** Column 커맨드 | §6.3.3 Column Commands (CNOP / RD·RDA / WR·WRA / MRS) · §6.3.4 Power-Mode (PDE·PDX / SRE·SRX) | Figure 33–60 |
| **08** Parity | §6.4.1 Command/Address Parity · §6.4.2 Data Parity | Figure 61–69 |
| **09** On-die ECC·ECS·SEV | §6.9.1 Overview · .2 Requirements · .3 Fault Isolation · .4 **ECS** · .5 Transparency Protocol · .6 ECC Engine Test Mode | Figure 77–83 |
| **10** 테스트·복구 | §6.7 Interconnect Redundancy Remapping (6.7.1 AWORD / 6.7.2 DWORD / 6.7.3 WSO) · §6.8 Loopback Test Modes (6.8.1 Polynomial ~ 6.8.7 LFSR Compare) · §6.13 Self Repair | Figure 70–76 |
| **11** 트레이닝·IEEE 1500 | §6.10 WOSC (6.10.1 WDQS Interval Oscillator) · §6.11 DCA/DCM · §6.12 Rx Offset Calibration · §13 Test and Boundary Scan | Table 134–148, Figure 다수 |
| **12** 전기·타이밍·패키지 + Base Die 종합 | §7 Operating Conditions · §8 Electrical Characteristics · §9 IDD · §10 AC Timings · §11 Package/Bump Map · §12 Assembly | Table 다수 |

---

## §13 IEEE1500 테스트 명령 인벤토리 (챕터 11용)

§13.4 명령 인코딩 / §13.5 개별 명령. 21개.

| # | 명령 | 성격 |
|---|---|---|
| 13.5.1 | `BYPASS` | 기본 |
| 13.5.2 | `EXTEST_RX` | 경계 스캔 |
| 13.5.3 | `HBM_RESET` | 리셋 |
| 13.5.4 | `MBIST` | 내장 자가 시험 |
| 13.5.5 | `SOFT_REPAIR` | 복구(휘발) |
| 13.5.6 | `HARD_REPAIR` | 복구(영구) |
| 13.5.7 | `DWORD_MISR` | 루프백 |
| 13.5.8 | `AWORD_MISR` | 루프백 |
| 13.5.9 | `CHANNEL_ID` | 식별 |
| 13.5.10 | `AWORD_MISR_CONFIG` | 루프백 설정 |
| 13.5.11 | `DEVICE_ID` | 식별 (밀도 코드 [43:40]) |
| 13.5.12 | `TEMPERATURE` | 센서 |
| 13.5.13 | `MODE_REGISTER_DUMP_SET` | MR 접근 |
| 13.5.14 | `READ_LFSR_COMPARE_STICKY` | 루프백 결과 |
| 13.5.15 | `SOFT_LANE_REPAIR` | 레인 복구 |
| 13.5.16 | `CHANNEL_DISABLE` | 채널 비활성 |
| 13.5.17 | `CHANNEL_TEMPERATURE` | 센서 |
| 13.5.18 | `WOSC_RUN` | 오실레이터 |
| 13.5.19 | `ECS Error Log` | ECC 로그 |
| 13.5.20 | `HS_REP_CAP` | 복구 자원 |
| 13.5.21 | `SELF_REP` | 자가 복구 |

부속 §13.6 Mission Mode 상호작용 · §13.7 AC 타이밍 · §13.8 Boundary Scan.

---

## 원문에서 확정한 핵심 사실 (집필 시 근거)

### 구성 (§1–3)

- 채널은 **서로 완전 독립**, **비동기 가능**. 클럭은 **채널 내 두 PC가 공유** (§3.1)
- 채널당 **64-bit 데이터 버스, DDR** (§1). PC 모드에서 **32 DQ** (§2)
- 채널당 **64 DQ + ECC/SEV 핀** (§2)
- **256-bit prefetch / access**, **BL = 8**, PC당 **page 1 KB** (§2)
- 스택당 최대 **32채널 / 64 PC**. **32채널에 최소 4 die** 필요. **4/8/12/16-high** 지원 (§3)
- 추가 die는 용량 + **SID** + PC당 뱅크를 늘린다 (§3)
- 채널당 **16 / 32 / 48 / 64 뱅크** (밀도별), **bank group 2/4/6/8개** (§2, §3.2.1)
- 채널 밀도 **3 Gb ~ 16 Gb** (§2)
- **Base Logic Die는 선택 사항** — 규격은 요구하지도 금지하지도 않는다 (§3)
- 채널이 여러 die에 분산되어도 **한 채널 내 모든 접근은 동일 레이턴시** (§3)

### 커맨드 (§2, §6.3)

- **Row ACTIVATE 1.5 사이클**, 그 외 row 커맨드 **0.5 사이클**, **PDE/SRE 1 사이클**, **column 커맨드 1 사이클** (§2)
- **Semi-independent row/column 커맨드 인터페이스** — ACT/PRE를 RD/WR과 병렬 발행 (§2, §3.1.3)
- 데이터 스트로브: **RDQS_t/_c, WDQS_t/_c — DWORD당 한 쌍** (§2)

### 주소 (§3.2, Table 4)

- **RA[13:0]** (RA[13:12]=11 무효) · **CA[4:0]** · **BA[3:0]** · **SID[1:0]** (SID[1:0]=11 무효, 4Hi에서 SID[0]=1 무효)
- **SID는 커맨드 실행에서 뱅크 주소 비트로 동작**하며, 일부 AC 타이밍이 SID에 연동될 수 있다 (Table 4 Note 4)
- BL8의 8 UI를 구분하는 **column 주소 비트는 장치로 전달되지 않는다** — 버스트 순서 고정 (Note 2)
- Page Size = 2^COLBITS × (Prefetch/8). **RA의 MSB가 열린 2 KB 페이지의 절반을 선택** (Note 3)

### 뱅크 그룹 의존 타이밍 (Table 6)

| 커맨드 시퀀스 | 다른 BG | 같은 BG |
|---|---|---|
| ACTIVATE → ACTIVATE | `tRRDS` | `tRRDL` |
| WRITE → WRITE | `tCCDS` | `tCCDL` |
| READ → READ | `tCCDS` / `tCCDR` | `tCCDL` |
| Internal WRITE → READ | `tWTRS` | `tWTRL` |
| READ → PRECHARGE | — | `tRTP` |

### 전기 (§2)

- I/O 전압 **vendor specific**, **Tx driver 0.4 V**, **DRAM core 1.05 V** (I/O와 독립)
- **무종단(unterminated)** 데이터/주소/커맨드/클럭 인터페이스, **비정합(unmatched)** 데이터 인터페이스

---

## 기존 토픽과의 충돌 — S19에서 정정할 항목

| 항목 | 기존 서술 | 원문 | 조치 |
|---|---|---|---|
| Base logic die | `hbm` 토픽이 사실상 **필수 구성**처럼 서술 | **선택 사항** (§3) | 정정. "규격이 열어둔 자리라서 Custom HBM이 성립한다"로 서사 강화 |
| 전압 | 리서치 단계 VDDQ 0.7/0.75/0.8/0.9 V, VDDC 1.0/1.05 V | I/O vendor specific, Tx driver **0.4 V**, core **1.05 V** (§2) | 원문 우선으로 정정 |
| HBM4 pseudo-channel 수 | 32ch × 2pc = **64 pc** | 일치 (§3) | 유지 |
| 채널/PC 폭 | 채널 64-bit, PC 32-bit | 일치 (§1, §2) | 유지 |

---

## 보조 근거 (원문 밖 — DFI·PHY·컨트롤러 구현)

규격은 DRAM 측을 정의하고 **컨트롤러/PHY 구현은 다루지 않는다.** 챕터 12(Base Die 종합)는
아래 공개 자료를 보조 근거로 쓰고 **[확인]/[추론]** 등급을 붙인다.

| 주제 | 출처 |
|---|---|
| DFI 5.0/5.1, 클럭비 1:1:2 / 1:2:4 / 1:4:8, PUB(PHY Utility Block) | Synopsys HBM3/HBM4 PHY IP 제품 문서 |
| 컨트롤러 구조, PC당 AXI 포트, global address mode | AMD/Xilinx **PG276** (공개) |
| Base die 기능 4분류(Controller/PDN/RAS/PHY), HBM4 비호환성 | Siemens IC design guide, SemiEngineering |
| HBM4 하위 호환 주장 | JEDEC 보도자료 — Siemens 서술과 **상충**. 층위(프로토콜 vs 물리 구현)를 구분해 양쪽 제시 |
