# `hbm` 토픽 — 리서치 인덱스 (S0)

수집일: 2026-08-25 / 수단: WebSearch
용도: 6챕터 집필 시 수치·구조 주장의 근거. **JEDEC 원문 미보유** — 정밀 수치는 항상 원문 우선.

---

## ⚠️ 소스 간 불일치 — 산술로 검증한 결과

집필 시 **그대로 베끼면 안 되는** 항목. 공개 소스 여러 곳이 서로 다르게 서술한다.

### 불일치 1 — HBM3의 pseudo-channel 수와 폭

| 소스 주장 | 판정 |
|---|---|
| "HBM3는 채널을 **4개**의 32-bit pseudo-channel로 나눈다" (Lumenci) | ❌ **오류** |
| "HBM3 = 16 channel / **32** pseudo-channel" (JEDEC 보도자료, HBM3E 자료 다수) | ✅ 채택 |
| "HBM3 pseudo-channel은 **독립 64-bit I/O**" (Lumenci) | ❌ HBM2 pseudo-channel 설명이 잘못 섞임 |

**산술 교차검증** — 총 인터페이스 폭 × per-pin 속도 ÷ 8 = per-stack 대역폭

| 세대 | 폭 | per-pin | 계산 | 공표값 | 일치 |
|---|---|---|---|---|---|
| HBM3 | 1024 bit | 6.4 Gb/s | 1024 × 6.4 / 8 = **819.2 GB/s** | 819 GB/s | ✅ |
| HBM3E | 1024 bit | 9.6 Gb/s | 1024 × 9.6 / 8 = **1228.8 GB/s** | ~1.2 TB/s | ✅ |
| HBM4 | 2048 bit | 8 Gb/s | 2048 × 8 / 8 = **2048 GB/s** | 최대 2 TB/s | ✅ |

→ 총 폭 1024-bit가 고정이므로 **16채널이면 채널당 64-bit**, pseudo-channel 2분할이면 **32-bit씩 32개**.
"4분할" 주장은 총 폭과 모순. **채택: HBM3 = 16 ch × 64-bit, 32 pc × 32-bit.**

### 불일치 2 — HBM4 per-stack 대역폭
"최대 2 TB/s"(JEDEC·Tom's Hardware) vs "1.5+ TB/s"(Spheron). 전자는 8 Gb/s 최대 속도 기준,
후자는 초기 양산 파트 기준으로 보임. → **집필 시 "8 Gb/s 기준 2 TB/s"처럼 조건을 명시**.

---

## Ch01 — 왜 HBM인가

| 사실 | 출처 |
|---|---|
| HBM은 클럭이 아니라 **버스 폭**으로 대역폭 확보 → per-watt 유리. GDDR6는 클럭 상승으로 달성 → 전력 불리 | wevolver (HBM2 vs GDDR6) |
| HBM ~1–6 TB/s/GPU, per-bit 수 pJ 수준 / GDDR ~0.7–1.0 TB/s per card (320–384-bit @ 15–20 Gb/s) / DDR DIMM 100–400 GB/s per CPU | IntuitionLabs |
| HBM3 최대 141.2 GB/s/W — **벤더성 수치, 조건부 인용** | wevolver |
| die edge 당 대역폭 밀도: HBM2E 60+ GB/s/mm vs GDDR6 약 1/6 | semiengineering |
| 동작 전압 HBM 1.2 V vs GDDR6 I/O 1.35 V | wevolver |

- https://www.wevolver.com/article/hbm2-vs-gddr6
- https://intuitionlabs.ai/articles/hbm-vs-ddr-memory-comparison
- https://semiengineering.com/hbm2e-the-e-stands-for-evolutionary/

## Ch02 — 세대 지형도

| 세대 | 표준 | per-pin | 총 폭 | per-stack BW | 용량 |
|---|---|---|---|---|---|
| HBM1 | JESD235 | ~1 Gb/s | 1024 bit | ~128 GB/s | 1 GB/stack (4-high) |
| HBM2 | JESD235 계열 | 2.4 Gb/s | 1024 bit (8 ch × 128-bit) | ~256 GB/s | 8 GB |
| HBM2E | (2020 정식화) | 3.6 Gb/s | 1024 bit | ~460 GB/s **추론(산술)** | 16 GB |
| HBM3 | **JESD238** (2022-01 공표) | 6.4 Gb/s | 1024 bit (16 ch × 64-bit) | 최대 819 GB/s | 16 GB |
| HBM3E | JESD238 계열 | 9.2–9.8 (최대 12.4) Gb/s | 1024 bit, 16 ch / 32 pc | >1.2 TB/s (최대 1.33) | 24 GB(8H×3) / 36 GB(12H×3), 2026 파트 48 GB(12H×4) |
| HBM4 | **JESD270-4** (2025-04) | 최대 8 Gb/s | **2048 bit** (32 ch × 2 pc) | 최대 2 TB/s | — |

추가:
- **SPHBM4** — 512-bit 협폭 변형. 실리콘 인터포저 없이 **유기 기판** 사용 목표 (원가 절감)
- **C-HBM4E** — TSMC N3P 로직 base die, 2027년 최대 12.8 GT/s 목표 (TSMC/GUC 발표)

- https://www.jedec.org/news/pressreleases/jedec-publishes-hbm3-update-high-bandwidth-memory-hbm-standard
- https://www.jedec.org/news/pressreleases/jedec%C2%AE-and-industry-leaders-collaborate-release-jesd270-4-hbm4-standard-advancing
- https://www.tomshardware.com/pc-components/ram/jedec-finalizes-hbm4-memory-standard-with-major-bandwidth-and-efficiency-upgrades
- https://www.tomshardware.com/pc-components/dram/jedec-releases-new-sphbm4-standard-to-slash-ai-memory-costs-narrow-512-bit-interface-enables-dropping-expensive-interposers-for-organic-substrates
- https://www.spheron.network/blog/hbm3e-vs-hbm4-vs-hbm4e-llm-inference-guide/

## Ch03 — 스택 구조 (DUT 경계 확정)

| 사실 | 출처 |
|---|---|
| DRAM die들을 **TSV**로 수직 연결하고, 그 아래 **logic/base die** 위에 본딩. base die가 refresh·training·data scheduling 관리 | wevolver |
| TSV = 직경 **10–20 µm** micro-via. void-free 충전, stress 관리 난제 | wevolver / semiengineering |
| microbump pitch 현행 **40 µm**, 선단 40→36 µm | semiengineering |
| **Hybrid bonding** (Cu-Cu 직접 접합)이 microbump 대체 중 — 열저항 22–47% 감소, 스택 높이 15%+ 감소 | tspasemiconductor |
| 2.5D: HBM 스택과 GPU/CPU die가 **실리콘 인터포저** 위에 나란히(CoWoS) → 유기 기판에 부착 | wevolver / Qnity |
| 스택 단수: HBM1 4-high, HBM2/2E 8-high, HBM3E 8/12-high | 종합 |

- https://www.wevolver.com/article/what-is-hbm-high-bandwidth-memory-deep-dive-into-architecture-packaging-and-applications
- https://semiengineering.com/scaling-bump-pitches-in-advanced-packaging/

> **주의**: 본 토픽은 검증 JD 한정이므로 hybrid bonding·thinning의 **공정 상세는 배제**.
> "base die가 로직 공정으로 간다 → 검증 대상이 SoC가 된다"는 **결과만** 사용.

## Ch04 — 채널 · Pseudo-channel · 주소맵

| 사실 | 출처 |
|---|---|
| HBM2 = 8 ch × **128-bit** = 1024-bit. pseudo-channel 모드가 128-bit를 **2×64-bit**로 분할 | Tom's Hardware / Intel FPGA UG |
| HBM3 = 1024-bit를 **16 ch × 64-bit**, **32 pc × 32-bit**로 분할 | Synopsys / JEDEC PR |
| HBM4 = 2048-bit, **32 ch**, 채널당 **2 pseudo-channel** (= 64 pc) | JEDEC PR / Tom's Hardware |
| pseudo-channel은 **CA 버스를 공유**하되 bank는 분리, 커맨드는 **개별 decode·실행** (semi-independent) | McMaster ICCAD 2021 논문 |
| HBM2에서 **BA4**가 PS0(=0)/PS1(=1) 선택 | McMaster 논문 / US10162522B1 |
| HBM은 **row/column address 핀이 분리**. HBM3는 **독립 row/column 커맨드 인터페이스 2벌** → activate/precharge를 read/write와 **병렬** 발행 가능 | Synopsys |

- https://www.synopsys.com/articles/hbm3-ip-dwtb.html
- https://www.ece.mcmaster.ca/faculty/hassan/assets/publications/hbm_iccad2021.pdf
- https://patents.google.com/patent/US10162522B1/en

**→ 검증 함의(🔍 섹션 소재)**: 채널/pseudo-channel 독립성 = concurrency coverage 축.
CA 공유 + 개별 실행이라는 **semi-independent** 성질이 race/ordering 검증 포인트.

## Ch05 — 인터페이스 프로토콜

| 사실 | 출처 |
|---|---|
| CA parity가 HBM2E의 **커맨드 내 인코딩** → HBM3에서 **CA 버스의 별도 신호**로 변경 | Synopsys |
| DBI(ac), data bus parity는 HBM2E에서 계승 | Synopsys |
| HBM2 pseudo-channel: 64-bit 세그먼트에서 burst 4 cycle × 64-bit = **256-bit/transaction** | Tom's Hardware |
| 독립 row/column 커맨드 인터페이스 (Ch04와 공유) | Synopsys |

- https://www.synopsys.com/designware-ip/technical-bulletin/hbm3-ip-dwtb.html

> 저전력/mode 커맨드는 Ch05에서 **동작 모드 관점만** 다루고, thermal throttling 시나리오는 `hbm_dv` Ch08로 이관.

## Ch06 — Base Die = 미니 SoC (이 토픽의 종착점)

| 사실 | 출처 |
|---|---|
| base die 기능은 크게 **Controller / PDN / RAS / PHY** 4가지 | viksnewsletter |
| base die 로직이 각 독립 채널의 read/write 관리 + **refresh cycle 관리 + precharge/activate 발행** | nomadsemi |
| HBM4 base die는 **2048-bit PHY I/O**(HBM3E의 2배)와 clock network를 탑재 | Siemens blog |
| **지금까지 base die는 DRAM 공정** → HBM4부터 **로직 공정으로 전환** (Samsung 4nm, TSMC 3/12nm) | Counterpoint / semiengineering |
| 로직 공정 전환으로 on-die power management, ECC, **고객 전용 accelerator** 탑재 여지 발생 | semiengineering |
| C-HBM4E는 **메모리 컨트롤러를 스택 내부로 통합**, PHY도 완전 커스텀 + custom D2D PHY | TrendForce / TechPowerUp |
| RAS: HBM3 **on-die ECC**(die 내부에서 정정), **ECS**(self-refresh 중 또는 refresh-all bank 시), 결과는 **IEEE 1500 TAP**의 ECC transparency register로 읽음 | Synopsys / IEEE |
| MBIST가 MBE row 식별(SBE는 on-die ECC가 마스킹) → host가 **MBIST-MPPR** repair 개시 | USPTO 11984180 |

- https://counterpointresearch.com/en/reports/HBM4-Inflection:The-Transition-to-Logic-Base-Dies,Custom-Memory,and-Disaggregated-Architectures
- https://semiengineering.com/how-will-the-custom-hbm-business-work/
- https://blogs.sw.siemens.com/semiconductor-packaging/2026/04/24/hbm3e-hbm4-ic-design-guide/
- https://www.synopsys.com/glossary/what-is-high-bandwitdth-memory-3.html
- https://www.viksnewsletter.com/p/faster-phy-design-in-custom-hbm

**→ JD 직결**: "base die가 로직 공정 SoC가 된다"가 곧
*"HBM 내 In-house·3rd Party Digital IP 및 Mixed 설계를 UVM으로 검증한다"* 는 JD의 성립 근거.
IEEE 1500 TAP / MBIST / on-die ECC는 `hbm_dv` Ch10(DFT·MBIST·RAS 검증)의 진입점.

---

## 집필 시 인용 규칙

1. 표에 들어가는 수치는 위 출처 중 **2곳 이상 교차 확인**되거나 **산술 검증**을 통과한 것만 단정
2. 단일 출처·벤더 마케팅 수치(예: 141.2 GB/s/W)는 "벤더 발표 기준" 명시
3. 계산으로 유도한 값(HBM2E ~460 GB/s 등)은 **추론(산술)** 태그
4. SK hynix 내부 구현·제품 로드맵은 **추측하지 않음**
5. 각 챕터 말미 `참고 자료`에 해당 챕터 출처 2개 이상 링크
