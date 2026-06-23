---
title: "DRAM DV Interview 용어집"
pagefind: false
---

이 페이지는 본 코스 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**). DRAM 도메인·검증 방법론·AI 검증 용어를 함께 묶었습니다.

:::tip[검색 활용]
상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.
:::

---

## D — DFI / Dual Reference Model

### DFI (DDR PHY Interface)

**Definition.** 메모리 컨트롤러와 DRAM PHY 사이의 신호·타이밍을 규정하는 표준 인터페이스다.

**Source.** DFI Specification.

**Related.** Memory Controller, PHY, STA.

**Example.** 컨트롤러가 발행한 command를 PHY가 DRAM으로 전달하는 경계에서 DFI 타이밍을 검증한다.

**See also.** [02 — DRAM 도메인](../02_dram_domain/#5-왜-dram은-dv가-timingsta을-직접-보는가)

### Dual Reference Model

**Definition.** 정확성을 보는 golden(functional) 모델과 성능 상한을 정의하는 ideal 모델을 함께 두어, DUT를 두 기준과 비교하는 검증 전략이다.

**Source.** 공통 DV 실무 (본 코스 MMU 사례).

**Related.** Scoreboard, Golden Model, Coverage.

**Example.** DUT의 TLB miss ratio가 ideal 모델 대비 초과하는 구간을 찾아 마이크로아키텍처 병목을 발굴.

**See also.** [03 — 검증 방법론](../03_verification_methodology/#4-reference-model-전략)

---

## R — RAG / Refresh / Root of Trust

### RAG (Retrieval-Augmented Generation)

**Definition.** 외부 문서를 검색(retrieval)해 그 근거를 LLM 생성에 결합함으로써, 모델이 가진 지식의 한계와 hallucination을 줄이는 기법이다.

**Source.** 본 코스 DVCon 2025 방법론.

**Related.** FAISS, LLM, Coverage Gap Detection.

**Example.** 방대한 IP DB를 FAISS로 인덱싱해 설계 feature를 필요한 검증 시나리오로 매핑.

**See also.** [05 — AI 검증](../05_ai_verification/#2-dvcon-2025--coverage-gap-detection)

### Refresh

**Definition.** DRAM cell 커패시터의 전하 누설로 인한 데이터 소실을 막기 위해, 일정 간격(tREFI) 안에 row의 데이터를 주기적으로 재기록하는 동작이다.

**Source.** JEDEC DRAM 표준.

**Related.** tREFI, tRFC, Self-Refresh, 1T1C cell.

**Example.** self-refresh entry/exit, per-bank refresh 중 다른 bank 접근을 coverage corner로 관리.

**See also.** [02 — DRAM 도메인](../02_dram_domain/#3-refresh--dram-검증의-단골-corner)

### Root of Trust

**Definition.** SoC 보안 체계에서 신뢰의 시작점이 되는 하드웨어/펌웨어 요소로, 이후 모든 보안 검증이 이 신뢰에 기반한다.

**Source.** SoC 보안 일반 / 본 코스 Secure Boot 사례.

**Related.** Secure Boot, OTP, DPI-C.

**Example.** BootROM 검증은 부팅이 아니라 SoC 전체 보안의 시작점을 검증하는 일이다.

**See also.** [04 — 프로젝트 심화](../04_project_deepdive/#1-secure-boot--soc-보안의-root-of-trust-lead-3년)

---

## S — STA / SVA

### STA (Static Timing Analysis)

**Definition.** 자극(stimulus) 없이 모든 timing path의 setup·hold·slack을 셀 delay(.lib)와 배선 기생(SPEF)·제약(SDC)으로 전수 분석해, 목표 클럭 주파수에서 회로가 동작 가능한지 판정하는 정적 분석이다.

**Source.** 표준 STA 정설.

**Related.** Setup, Hold, Slack, Functional Timing.

**Example.** STA는 tRFI를 모른다 — 오직 플립플롭 간 setup/hold만 본다 (functional timing과 레이어가 다름).

**See also.** [02 — DRAM 도메인](../02_dram_domain/#4-sta-vs-functional-timing--timing이라는-단어의-두-세계--갭-방어-핵심)

### SVA (SystemVerilog Assertions)

**Definition.** 설계의 시간적·논리적 속성을 시뮬레이션 중 연속적으로 감시하는 SystemVerilog 단언으로, functional/protocol timing을 cycle 단위로 검증한다.

**Source.** IEEE 1800.

**Related.** Cover Property, Functional Timing, Coverage.

**Example.** ACT 후 tRCD cycle 이전에 RD/WR이 오면 fail하는 assertion + 동일 조건 cover.

**See also.** [03 — 검증 방법론](../03_verification_methodology/#5-sva로-protocoltiming을-거는-법)

---

## T — Timing Parameter

### tRCD / tRP / tRAS / tREFI

**Definition.** DRAM 동작의 물리적 제약을 cycle 수로 규정한 값으로, 각각 ACT→RD/WR(tRCD), PRE→ACT(tRP), ACT→PRE 최소(tRAS), refresh 평균 간격(tREFI)을 의미한다.

**Source.** JEDEC DRAM 표준.

**Related.** Refresh, Sense Amplifier, Functional Timing.

**Example.** tRCD는 row를 열고 sense amp가 안정될 시간 — 이전에 column 접근하면 데이터가 부정확.

**See also.** [02 — DRAM 도메인](../02_dram_domain/#2-timing-parameter--왜-그-제약이-존재하는가)
