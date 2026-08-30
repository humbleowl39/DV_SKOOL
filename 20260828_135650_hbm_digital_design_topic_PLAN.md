# Plan: HBM4 Digital Design Deep-Dive 토픽 (`hbm4_jedec_dd`)

> **개정 2026-08-30** — JESD270-4 원문 확보로 근거 제약 해제. 챕터 구조를 규격 조직에 맞춰 전면 재설계.

## Objective

HBM을 **digital design 관점에서 설명할 수 있는 수준**까지 파는 심화 토픽을 만든다.
`dram_jedec_dv`(LPDDR5 심화, 12장+부록3, 약 11,400줄)와 같은 밀도·형식을 목표로 하되,
관점을 **DV가 아니라 Digital Design(RTL·Front-end·SoC)** 에 둔다.

## Context

### 1차 근거 — JESD270-4 원문 확보 ★

`eetop.cn_JESD270-4.pdf` — **High Bandwidth Memory (HBM4) DRAM, JESD270-4, April 2025, 280쪽**
(문서 속성상 *WIP draft*. JEDEC Solid State Technology Association 저작).

이로써 초안 계획의 최대 제약(*"정밀 MR 비트맵·타이밍 표는 만들 수 없다"*)이 **해제**된다.
규격이 실제로 담고 있는 것:

| 절 | 내용 | 쪽 |
|---|---|---|
| 1–3 | Scope · Features · Organization · Channel Definition · Channel Addressing · State Diagram | 1–9 |
| 4 | Initialization — power-up, stable-power, controlled power-off, IEEE1500 경유 init | 10–18 |
| 5 | **Mode Registers** MR0~ (Table 9~) | 19–31 |
| 6.1–6.2 | Clocking Overview · **DBIac** | 32–39 |
| 6.3 | **Commands** — RNOP/ACT/PRE/REF/RFM/DRFM/CNOP/RD/WR/MRS/PDE/SRE | 40–97 |
| 6.4 | **Parity** — CA parity, write/read parity, PL | 98–104 |
| 6.5–6.7 | 클럭 주파수 변경 · CATTRIP · **Interconnect Redundancy Remapping(Lane Repair)** | 105–115 |
| 6.8 | **Loopback Test Modes** — MISR/LFSR | 116–130 |
| 6.9 | **On-die DRAM ECC** · ECS · SEV | 131–142 |
| 6.10–6.13 | **WOSC** · DCA/DCM · Rx Offset Calibration · **Self Repair** | 143–161 |
| 7–10 | DC/AC 조건 · 전기 특성 · IDD · **AC Timings** | 162–198 |
| 11–12 | **Package/Bump Map** · Assembly | 199–209 |
| 13 | **IEEE 1500 Test Port** · WDR · 명령 인코딩 · Boundary Scan | 210–265 |

### 원문에서 확인한 핵심 사실 (초안 대비 정정 포함)

- 채널당 **64 DQ + ECC/SEV 핀**, PC 모드에서 **32 DQ**. 32ch × 64 = 2048-bit ✅ (기존 서술 일치)
- **256-bit prefetch / access, BL = 8**, PC당 **page 1 KB**
- 커맨드 사이클: **Row ACTIVATE 1.5, 그 외 row 0.5, PDE/SRE 1, column 1** — 리서치와 일치
- 채널당 **16 / 32 / 48 / 64 뱅크** (밀도별), **bank group 2/4/6/8개**
- 주소: **RA[13:0] · CA[4:0] · BA[3:0] · SID[1:0]**. SID는 커맨드 실행에서 뱅크 주소 비트로 동작
- 스택 **4/8/12/16-high**, 32채널을 위해 **최소 4 die** 필요. 이후 die는 용량·SID·뱅크를 추가
- **Base Logic Die는 규격상 선택 사항** — *"vendor may choose to require an optional interface die… This standard does not explicitly require nor prohibit such a solution."*
  → ⚠️ **기존 `hbm` 토픽이 base die를 사실상 필수처럼 서술**한다. 이 대목은 교차 점검·수정 필요
- 전압: I/O는 **vendor specific**, **Tx driver 0.4 V**, **DRAM core 1.05 V** (초안 리서치의 VDDQ 0.7~0.9 V 표기와 다름 → 원문 우선)
- 채널은 서로 **비동기 가능**. 클럭은 **채널 내 두 PC가 공유**
- 단일 채널 내 모든 접근은 **동일 레이턴시**여야 함 (채널이 여러 die에 분산되더라도)

### 저작권 취급 (반드시 준수)

원문에 *"This document is copyrighted by JEDEC and may not be reproduced without permission"* 명시.

- **PDF를 커밋하지 않는다** (`.gitignore` 처리 또는 untracked 유지)
- 표·그림을 **그대로 옮기지 않는다.** 구조와 의미를 **요약·재구성**하고 **절·표 번호로 인용**한다
- 수치는 설명에 필요한 최소한만, 출처(절 번호)와 함께
- `dram_jedec_dv`와 동일한 고지 배너를 각 챕터/인덱스에 넣는다:
  *"본 자료의 인용은 학습 목적의 요약·참조이며 스펙 원문의 복제가 아닙니다. 정밀 수치는 항상 JEDEC 원문 우선."*
- 문서가 **WIP draft**임을 명시 (최종본과 다를 수 있음)

### 기존 HBM 토픽과의 관계

| 토픽 | 챕터 | 관점 | 이 토픽과의 차이 |
|---|---|---|---|
| `hbm` | 6 | 검증 대상으로서의 **개괄** | 구조 소개 후 "검증 문제"로 착지 |
| `hbm_dv` | 12 | 검증 **실무** | 환경·Agent·Coverage |
| `hbm_dv_interview` | 9 | 면접 **답변** | 숨김 토픽 |
| **`hbm4_jedec_dd` (신규)** | 12+3 | **규격 상세 + Digital Design** | 스펙이 무엇을 요구하고 그것을 **어떤 로직으로 구현하는가** |

중복 방지: 개괄은 `hbm`으로, 검증은 `hbm_dv`로 **링크만**. 이 토픽은 규격 조문과 RTL 구현에 집중.

## Steps

- [x] **S0** 사전 리서치(WebSearch 6건) + **JESD270-4 원문 확보·구조 파악**
- [ ] **S1** `topics/hbm4_jedec_dd/_research/spec_index.md` — 절·표·그림 번호 인덱스 (집필 시 인용 근거)
- [ ] **S2** 디렉터리 + `index.mdx` — 학습목표·사전지식·모듈맵·**저작권 고지**·직무 매핑
- [ ] **S3** `01_landscape_organization.md` — §1–3.1 규격 지형도, 채널/PC, SID, 스택, **선택적 base logic die**
- [ ] **S4** `02_addressing_bank_groups.md` — §3.2–3.3 주소 체계, 뱅크 그룹, BG 의존 타이밍, 상태도
- [ ] **S5** `03_init_reset_power.md` — §4 전원·리셋·초기화 시퀀스, IEEE1500 경유 init
- [ ] **S6** `04_mode_registers.md` — §5 MR 맵 구조와 설정 반영 로직
- [ ] **S7** `05_clocking_dbi.md` — §6.1–6.2 클럭킹, WDQS 분주, write→read, DBIac
- [ ] **S8** `06_row_commands.md` — §6.3 RNOP·ACT·PRE·REFab/pb·RFM·**DRFM**
- [ ] **S9** `07_column_commands.md` — §6.3 CNOP·RD/WR·버스트·tCCD·MRS·PDE/SRE
- [ ] **S10** `08_parity.md` — §6.4 CA/Write/Read parity, PL
- [ ] **S11** `09_ecc_ecs_sev.md` — §6.9 on-die ECC, ECS, severity 신호
- [ ] **S12** `10_test_repair.md` — §6.7–6.8, 6.13 MISR/LFSR, Lane Repair, Self Repair
- [ ] **S13** `11_training_ieee1500.md` — §6.10–6.12 WOSC·DCA/DCM·Rx offset + §13 IEEE 1500·Boundary Scan
- [ ] **S14** `12_electrical_timing_package.md` — §7–11 DC/AC·IDD·AC timing·bump map이 디지털 설계에 주는 제약 + **Base Die 종합**
- [ ] **S15** `appendix_a_quick_reference.md` — 커맨드·MR·타이밍 파라미터 요약
- [ ] **S16** `appendix_b_glossary.md` — ISO 11179, 50개 내외
- [ ] **S17** `appendix_c_rtl_patterns.md` — SystemVerilog 설계 패턴 (커맨드 디코더·refresh 스케줄러·parity·CDC)
- [ ] **S18** `quiz/` — index + 챕터별 12개 (문항 6개)
- [ ] **S19** 기존 `hbm` 토픽 교차 점검 — base die 필수/선택 서술, 전압 수치 정정
- [ ] **S20** 사이드바 등록 + 홈 카드 (메모리 5 → 6 토픽)
- [ ] **S21** 전수 검증 — 링크, `$display` 0건, d2 대비 검사(`check_d2_contrast.mjs`), 인용 표기
- [ ] **S22** 커밋 + 푸시 + 배포 후 본문 렌더 확인

## 챕터 공통 구조

1. 🎯 Learning Objectives (Bloom 동사)
2. Prerequisites
3. 규격이 요구하는 것 — 조문 요약 + **절·표 번호 인용**
4. 왜 그렇게 정했는가 — 대안과 트레이드오프
5. **⚙️ 설계 적용 (RTL / Front-end)** ← 이 토픽의 척추
6. **대표 문제 dry-run** (타이밍 계산 · 주소 디코드 · FSM 추적)
7. 🔍 검증 연결 — [`hbm_dv`](../hbm_dv/)로 **링크만**
8. 핵심 정리 / Further Reading

## Success Criteria

1. 12개 챕터 각각에 **⚙️ 설계 적용** 절이 있고 RTL 수준의 구체적 요구사항을 서술한다
2. 모든 규격 주장에 **절·표·그림 번호 인용**이 붙는다
3. 표·그림을 원문 그대로 옮기지 않는다. 저작권 고지가 index와 각 챕터에 있다
4. `hbm`·`hbm_dv`와 중복 서술 아님 — 개괄·검증은 링크
5. 내부 링크 해석 100%, d2 대비 검사 0건, `$display` 0건
6. **PDF는 커밋되지 않는다**
7. S19에서 기존 토픽과의 사실 충돌이 정리된다

## Risks / Open Questions

| 리스크 | 대응 |
|---|---|
| **저작권** — 원문 복제 금지 | 요약·재구성 + 절 번호 인용. 표 통째 이식 금지. PDF 미커밋. 고지 배너 |
| 문서가 **WIP draft** | 그 사실을 명시. 최종 JESD270-4/-4A와 다를 수 있음을 배너에 표기 |
| 기존 `hbm` 토픽과 사실 충돌 | S19에서 교차 점검. 확인된 항목: **base logic die 선택성**, **전압 수치** |
| 분량 과다 | 챕터 1개씩 micro-step, 각 단계 후 커밋 가능 상태 유지 |
| d2 다이어그램 가시성 | 신규 도구(`fix_d2_contrast`/`gen_d2`/`check_d2_contrast`) 사용, S21에서 검사 |

## Deviations / Results

### 결과

산출물: `starlight_site/src/content/docs/hbm4_jedec_dd/` — **31개 파일 8,733줄** + d2 다이어그램 7개

| 구성 | 줄 수 | 내용 |
|---|---|---|
| `index.mdx` | 120 | 저작권 고지·모듈맵·직무 대응 |
| 본문 12장 | 5,172 | 각 장에 **⚙️ 설계 적용** + dry-run + 🔍 검증 연결 |
| 부록 A 빠른 참조 | 374 | 17절 조회표 (되돌릴 수 없는 상태 3종, 자주 틀리는 것 15가지 포함) |
| 부록 B 용어집 | 756 | **59개 용어**, ISO 11179, Source 전부 JESD270-4 절 번호 |
| 부록 C RTL 패턴 | 679 | **14개 패턴**, 합성 가능 SystemVerilog |
| `quiz/` 13파일 | 1,632 | **72문항**, Bloom 혼합 |

부수 변경: `astro.config.mjs`(사이드바), 홈 `index.mdx`(메모리 5→6, 히어로 30→31),
`hbm/index.mdx`·`hbm_dv/index.mdx`(교차 링크), `hbm/03_stack_architecture.md`(규격 조문 note).

### 성공 기준 검증

| # | 기준 | 결과 |
|---|---|---|
| 1 | 12장 각각에 ⚙️ 설계 적용 절 | ✅ 12/12 |
| 2 | 규격 주장에 절·표 번호 인용 | ✅ 전 장 |
| 3 | 표·그림 원문 미복제 + 고지 배너 | ✅ 16/16 (부록 C는 S21에서 보완) |
| 4 | `hbm`·`hbm_dv`와 중복 없음 | ✅ 개괄·검증은 링크로 위임 |
| 5 | 링크 해석 / d2 대비 / `$display` | ✅ **542/542** · **150건 미달 0** · **0건** |
| 6 | PDF 미커밋 | ✅ 추적 PDF 0건 |
| 7 | 기존 토픽 사실 충돌 정리 | ✅ 아래 참조 |

### S19 교차 점검 — 계획 대비 정정

계획서에 "정정 필요"로 적었던 두 항목을 실제 확인한 결과, **둘 다 정정 대상이 아니었다.**

| 항목 | 계획의 판단 | 실제 | 조치 |
|---|---|---|---|
| 전압 수치 | `hbm` 본문 정정 필요 | **본문에 수치가 없음** (리서치 인덱스에만 존재) | 불필요 |
| base die 필수 서술 | "필수처럼 서술" | **틀리지 않음** — 실제 제품 구조와 설계 근거를 서술 | **보강**(정정 아님) |

그리고 §2 Features와 §7.2의 전압 서술이 **모순이 아니라 요약과 상세**의 관계임을 확인했다 —
§2는 헤드라인(I/O는 vendor specific, Tx 0.4 V, core 1.05 V), §7.2는 완전한 지원 집합
(`VDDQ` 4값, `VDDC` 2값 + 허용 오차). 초기 리서치 수치가 **옳았다.** 12장에 이 관계를 명시했다.

`hbm/03`에는 규격이 base die를 **요구하지도 금지하지도 않는다**는 조문(§3)을 note로 추가했다.
이 한 조문이 **Custom HBM 성립**과 **표준 VIP 부재**를 동시에 설명하므로 서사가 강해졌다.

### 계획 대비 편차

| 항목 | 계획 | 실제 | 사유 |
|---|---|---|---|
| 용어집 | 50개 내외 | **59개** | 규격 고유 용어가 예상보다 많음 (ARFU·WOSC·DCA/DCM·tCCDR 등) |
| 부록 C 패턴 수 | 4종 예시 | **14종** | 12장에서 도출된 설계 제약이 많아 패턴으로 분리 |
| 챕터 분량 | 균등 | 06장 487줄 ~ 04장 393줄 | refresh 5갈래·라운딩 규칙이 집중된 06장이 최장 |
| d2 다이어그램 | 미정 | **7개** | 신규 도구로 안전하게 생성. 대비 검사 전부 통과 |

### 원문이 준 것 — 초안 계획 대비

계획 초안의 최대 제약(*"정밀 MR 비트맵·타이밍 표를 만들 수 없다"*)이 원문 확보로 해제되어,
다음이 가능해졌다.

- MR 20개 전체 지도와 필드별 범위 (`RL` 17–90 nCK 등)
- **HBM4 고유 라운딩 공식** `0.5 × RU(2·t/tCK)`와 `tRP` 예외
- Refresh **5갈래**와 RAA 카운터 모델, ARFM 조합 진리표
- ECC codeword 산술 (256+16+32 = 304 b)과 `SEV` 인코딩
- **변동 계수 2.5 ps/mV · 1.0 ps/°C** — 코스 전체의 트레이닝 기능을 설명하는 근거
- `tRAS` **최대** 제약(`9 × tREFI`), `tCCDR`의 SID 의존성

### 도구

이번 작업은 직전 커밋(`9d76a63`)에서 만든 d2 도구 3종을 그대로 사용했다.
`gen_d2.mjs`로 대상 파일만 생성하고 `check_d2_contrast.mjs`로 매 장마다 검사했으며,
02장에서 연결선 라벨에 과잉 적용한 것을 검사기가 잡아내 되돌렸다(캔버스 위 라벨은 테마를 따라야 함).

### 미결 사항

- 배포 후 본문 렌더 확인 (S22)
- `fix_d2_contrast.mjs`는 도형만 처리하고 **채색된 컨테이너 안의 연결선 라벨**은 다루지 않는다.
  01장에서 수동 보완했다. 빈도가 낮아 스크립트 확장은 보류.
