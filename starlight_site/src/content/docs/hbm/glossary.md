---
title: "HBM 용어집"
---

이 페이지는 본 코스에서 사용하는 HBM 핵심 용어의 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

Definition은 **그 개념이 무엇인가(concept that IS)** 를 단일 문장으로 진술하며, 예시는 별도 필드로 분리합니다.

:::tip[검색 활용]
상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.
:::

:::note[출처 표기에 대하여]
**Source**가 "JEDEC 공개 자료"인 항목은 표준 보도자료·벤더 기술 문서 등 공개 출처에 근거한 것이며, JEDEC 원문의 절 번호를 인용한 것이 아닙니다. 정밀한 규정은 해당 세대의 원문을 확인하세요. "본 코스 정의"는 학습 목적으로 이 코스가 도입한 정리입니다.
:::

---

## 2 — 2.5D Packaging

### 2.5D Packaging

**Definition.** 복수의 다이를 실리콘 인터포저 위에 수평으로 나란히 배치하고 인터포저의 미세 배선으로 상호 연결하는 패키징 방식.

**Source.** JEDEC 공개 자료 / 업계 통용.

**Related.** Interposer, TSV, Microbump.

**Example.** HBM 스택과 GPU 다이를 하나의 인터포저 위에 올려 마이크로미터 거리로 연결하는 구성.

**See also.** [Ch03 — 스택 구조와 DUT 경계](../03_stack_architecture/)

---

## A — Assertion

### Assertion

**Definition.** 설계가 만족해야 할 시간적·논리적 규칙을 인터페이스에 상주하며 시뮬레이션 내내 상시 평가하고 위반 시점에 즉시 보고하는 검증 구성요소.

**Source.** Common DV usage; IEEE 1800 (SystemVerilog Assertions).

**Related.** Protocol Checker, Scoreboard, Coverage.

**Example.** 특정 뱅크에 activate가 발행된 뒤 규정 간격이 지나기 전에 같은 뱅크로 read가 발행되면 오류를 보고하는 규칙.

**See also.** [Ch05 — 인터페이스 프로토콜](../05_interface_protocol/) · [UVM 코스](../../uvm/)

---

## B — Base Die / Bank / Behavioral Model / Burst

### Base Die (Logic Die)

**Definition.** HBM 스택 최하단에 위치하여 채널별 읽기·쓰기 관리, refresh 주기 운영, 트레이닝, 호스트 인터페이스를 담당하는 다이.

**Source.** JEDEC 공개 자료 / 벤더 기술 문서.

**Related.** Core Die, PHY, Controller, Custom HBM.

**Example.** HBM4 세대의 base die는 2048-bit PHY I/O와 클럭 네트워크를 탑재하며, 로직 공정으로 제조된다.

**See also.** [Ch06 — Base Die = 미니 SoC](../06_base_die_soc/)

### Bank

**Definition.** 독립적으로 activate와 precharge를 수행할 수 있는 DRAM 셀 어레이의 단위 구획.

**Source.** Common DRAM usage.

**Related.** Channel, Pseudo-channel, Row, Column.

**Example.** 한 뱅크가 activate 상태인 동안 다른 뱅크에서 별도의 읽기를 진행할 수 있다.

**See also.** [Ch04 — 채널 · Pseudo-channel · 주소맵](../04_channels_addressing/) · [DRAM / DDR 코스](../../dram_ddr/)

### Behavioral Model

**Definition.** 검증 대상이 아닌 주변 구성요소의 동작을 시뮬레이션에서 대신 수행하도록 작성된 코드.

**Source.** Common DV usage.

**Related.** DUT Boundary, VIP, Scoreboard.

**Example.** DRAM core die를 대체하여 커맨드에 응답하고 데이터를 반환하는 DRAM 모델.

**See also.** [Ch03 — 스택 구조와 DUT 경계](../03_stack_architecture/)

### Burst

**Definition.** 하나의 읽기 또는 쓰기 커맨드에 대해 연속된 여러 사이클에 걸쳐 전송되는 데이터의 묶음.

**Source.** Common DRAM usage; JEDEC 공개 자료.

**Related.** Access Granularity, Pseudo-channel, DQ.

**Example.** HBM2의 pseudo-channel 모드에서 64-bit 세그먼트 위로 4 사이클에 걸쳐 256비트를 전송하는 단위.

**See also.** [Ch05 — 인터페이스 프로토콜](../05_interface_protocol/)

---

## C — CA Bus / CA Parity / Channel / Core Die / Custom HBM / Custom UVM Agent

### CA Bus (Command/Address Bus)

**Definition.** 호스트가 메모리에 커맨드와 주소를 전달하는 신호 그룹.

**Source.** JEDEC 공개 자료.

**Related.** Pseudo-channel, CA Parity, Row Command, Column Command.

**Example.** 같은 채널에 속한 두 pseudo-channel이 하나의 CA 버스를 공유하며 각자 커맨드를 해석한다.

**See also.** [Ch04 — 채널 · Pseudo-channel · 주소맵](../04_channels_addressing/)

### CA Parity

**Definition.** 커맨드와 주소가 전송 중 손상되었는지를 검출하기 위한 오류 검출 수단.

**Source.** JEDEC 공개 자료 / Synopsys 기술 문서.

**Related.** CA Bus, Data Bus Parity, Error Injection.

**Example.** HBM2E에서는 커맨드 안에 인코딩되었고, HBM3에서는 CA 버스의 별도 신호로 분리되었다.

**See also.** [Ch05 — 인터페이스 프로토콜](../05_interface_protocol/)

### Channel

**Definition.** 자체 데이터 경로와 자체 CA 버스를 보유하여 다른 채널과 독립적으로 동작하는 HBM의 접근 단위.

**Source.** JEDEC 공개 자료 (JESD238, JESD270-4).

**Related.** Pseudo-channel, Bank, CA Bus.

**Example.** HBM3는 스택당 16개 채널을 가지며 각 채널의 데이터 폭은 64-bit이다.

**See also.** [Ch04 — 채널 · Pseudo-channel · 주소맵](../04_channels_addressing/)

### Core Die

**Definition.** HBM 스택에서 셀 어레이와 뱅크를 보유하여 실제 데이터를 저장하는 DRAM 다이.

**Source.** JEDEC 공개 자료 / 업계 통용.

**Related.** Base Die, Stack Height, TSV.

**Example.** 12-high 구성의 스택은 12장의 core die로 이루어진다.

**See also.** [Ch03 — 스택 구조와 DUT 경계](../03_stack_architecture/)

### Custom HBM (cHBM)

**Definition.** Base die에 특정 고객의 요구에 맞춘 로직을 통합하여 제작하는 HBM 제품 형태.

**Source.** SemiEngineering / Counterpoint 공개 분석.

**Related.** Base Die, Custom UVM Agent, UCIe.

**Example.** 고객 전용 가속 로직과 커스텀 PHY를 base die에 통합한 구성.

**See also.** [Ch02 — 세대 지형도](../02_generations/) · [Ch06 — Base Die = 미니 SoC](../06_base_die_soc/)

### Custom UVM Agent

**Definition.** 비표준 인터페이스를 대상으로 스펙으로부터 직접 설계·구현하는 UVM 검증 구성요소 묶음.

**Source.** Common DV usage; UVM 1.2 Reference Manual.

**Related.** VIP, Custom HBM, Sequence.

**Example.** 고객이 정의한 비표준 인터페이스에 대해 트랜잭션·driver·monitor·coverage를 처음부터 작성한 agent.

**See also.** [Ch06 — Base Die = 미니 SoC](../06_base_die_soc/) · [UVM 코스](../../uvm/)

---

## D — DBI / DUT Boundary

### DBI (Data Bus Inversion)

**Definition.** 동시에 전환되는 비트 수를 줄이기 위해 데이터를 조건부로 반전하여 전송하는 인코딩 기법.

**Source.** JEDEC 공개 자료 / Synopsys 기술 문서.

**Related.** DQ, Data Bus Parity.

**Example.** HBM2E에서 HBM3로 계승된 DBI(ac) 방식.

**See also.** [Ch05 — 인터페이스 프로토콜](../05_interface_protocol/)

### DUT Boundary (검증 대상 경계)

**Definition.** 검증 환경에서 실제 검증 대상으로 삼는 설계 영역과 그 바깥을 가르는 선.

**Source.** 본 코스 정의 (Common DV usage 기반).

**Related.** Behavioral Model, VIP, Mixed-level Verification.

**Example.** HBM 검증에서 base die의 digital·mixed IP를 안쪽으로, core die와 호스트를 바깥쪽으로 두는 구분.

**See also.** [Ch03 — 스택 구조와 DUT 경계](../03_stack_architecture/)

---

## E — ECC (On-die) / ECS / Error Injection

### ECC, On-die

**Definition.** 각 DRAM 다이 내부에서 오류 검출용 부호를 저장하고 정정을 수행하는 오류 정정 기능.

**Source.** JEDEC 공개 자료 (HBM3) / Synopsys 기술 문서.

**Related.** ECS, RAS, MBIST, IEEE 1500 TAP.

**Example.** 데이터가 호스트로 전달되기 전에 다이 내부에서 단일 비트 오류를 정정하는 동작.

**See also.** [Ch06 — Base Die = 미니 SoC](../06_base_die_soc/)

### ECS (Error Check and Scrub)

**Definition.** 저장된 데이터를 주기적으로 읽어 오류를 검사하고 정정하는 유지 동작.

**Source.** JEDEC 공개 자료 (HBM3) / Synopsys 기술 문서.

**Related.** On-die ECC, IEEE 1500 TAP, RAS.

**Example.** self-refresh 상태이거나 호스트가 전체 뱅크 refresh를 지시했을 때 수행되며, 결과는 ECC 투명성 레지스터를 통해 조회된다.

**See also.** [Ch06 — Base Die = 미니 SoC](../06_base_die_soc/)

### Error Injection (오류 주입)

**Definition.** 오류 상황에서만 동작하는 기능을 검증하기 위해 의도적으로 결함 조건을 발생시키는 시나리오 기법.

**Source.** Common DV usage.

**Related.** CA Parity, On-die ECC, RAS.

**Example.** parity 오류를 주입한 뒤 검출 여부와 보고 동작, 이후 상태 전이를 확인하는 시나리오.

**See also.** [Ch05 — 인터페이스 프로토콜](../05_interface_protocol/)

---

## H — HBM / Hybrid Bonding

### HBM (High Bandwidth Memory)

**Definition.** DRAM 다이를 수직으로 적층하고 TSV로 연결하여 초광폭 인터페이스로 높은 대역폭을 제공하는 메모리 규격군.

**Source.** JEDEC 공개 자료 (JESD235 / JESD238 / JESD270-4).

**Related.** TSV, Base Die, 2.5D Packaging, Channel.

**Example.** HBM3는 1024-bit 인터페이스에서 per-pin 6.4 Gb/s로 스택당 최대 819 GB/s를 제공한다.

**See also.** [Ch01 — 왜 HBM인가](../01_why_hbm/)

### Hybrid Bonding

**Definition.** 범프를 거치지 않고 구리 패드를 직접 접합하여 다이를 연결하는 접합 방식.

**Source.** 업계 공개 자료.

**Related.** Microbump, TSV, Stack Height.

**Example.** 미세 범프를 대체하여 열 저항과 스택 높이를 줄이는 접합 방식.

**See also.** [Ch03 — 스택 구조와 DUT 경계](../03_stack_architecture/)

---

## I — IEEE 1500 TAP / Interposer

### IEEE 1500 TAP (Test Access Port)

**Definition.** 내장 코어의 테스트 제어와 상태 조회를 위해 표준화된 테스트 접근 포트.

**Source.** IEEE 1500 표준 / JEDEC 공개 자료.

**Related.** MBIST, ECS, On-die ECC, DFT.

**Example.** ECS 수행 결과를 담은 ECC 투명성 레지스터를 이 포트를 통해 읽는다.

**See also.** [Ch06 — Base Die = 미니 SoC](../06_base_die_soc/)

### Interposer

**Definition.** 복수의 다이를 그 위에 얹고 미세 배선으로 상호 연결하는 중간 기판.

**Source.** 업계 공개 자료.

**Related.** 2.5D Packaging, Microbump, TSV.

**Example.** HBM 스택과 호스트 프로세서를 같은 실리콘 인터포저 위에 배치하는 구성.

**See also.** [Ch03 — 스택 구조와 DUT 경계](../03_stack_architecture/)

---

## J — JEDEC 표준 번호

### JESD235 / JESD238 / JESD270-4

**Definition.** HBM 세대별 규격을 정의하는 JEDEC 표준 문서의 식별 번호.

**Source.** JEDEC 공개 보도자료.

**Related.** HBM, SPHBM4.

**Example.** JESD235 계열은 HBM1·HBM2·HBM2E를, JESD238은 HBM3·HBM3E를, JESD270-4는 HBM4를 규정한다.

**See also.** [Ch02 — 세대 지형도](../02_generations/)

---

## M — MBIST / Memory Wall / Microbump / Mixed-level / Mode Register

### MBIST (Memory Built-In Self-Test)

**Definition.** 메모리 어레이를 시험하기 위해 칩 내부에 내장된 자체 시험 회로.

**Source.** Common DFT usage / 공개 특허 문헌.

**Related.** IEEE 1500 TAP, Repair, On-die ECC.

**Example.** on-die ECC가 단일 비트 오류를 가리는 조건에서 다중 비트 오류가 발생한 행을 식별하고, 호스트가 그 결과로 리페어 절차를 개시한다.

**See also.** [Ch06 — Base Die = 미니 SoC](../06_base_die_soc/)

### Memory Wall

**Definition.** 연산 성능의 증가 속도를 메모리의 데이터 공급 능력이 따라가지 못해 시스템 성능이 메모리에 의해 제한되는 현상.

**Source.** 컴퓨터 구조 분야 통용 용어.

**Related.** HBM, Bandwidth, Effective Bandwidth.

**Example.** 가중치 70 GB를 매 토큰마다 읽어야 하는 추론 작업에서 연산 유닛이 데이터를 기다리며 유휴 상태가 되는 상황.

**See also.** [Ch01 — 왜 HBM인가](../01_why_hbm/)

### Microbump (µbump)

**Definition.** 적층된 다이 사이를 물리적·전기적으로 접합하는 미세 범프 구조.

**Source.** 업계 공개 자료.

**Related.** TSV, Hybrid Bonding, Interposer.

**Example.** 현행 선단 공정에서 40 µm 안팎의 피치로 형성되는 접합 구조.

**See also.** [Ch03 — 스택 구조와 DUT 경계](../03_stack_architecture/)

### Mixed-level Verification

**Definition.** 회로도 수준으로 기술된 블록과 RTL로 기술된 블록을 하나의 시뮬레이션에서 함께 검증하는 방법.

**Source.** Common DV usage.

**Related.** PHY, DUT Boundary, Behavioral Model.

**Example.** base die의 PHY를 회로 수준으로, 나머지 로직을 RTL로 두고 함께 시뮬레이션하는 구성.

**See also.** [Ch03 — 스택 구조와 DUT 경계](../03_stack_architecture/) · [Mixed-Signal DV 코스](../../mixed_signal_dv/)

### Mode Register

**Definition.** 메모리의 동작 방식을 결정하는 설정값을 보관하는 레지스터.

**Source.** Common DRAM usage; JEDEC 공개 자료.

**Related.** Configuration Space, Low-power Mode.

**Example.** 지연 파라미터나 기능의 활성 여부를 지정하여 이후 동작을 변경하는 설정.

**See also.** [Ch05 — 인터페이스 프로토콜](../05_interface_protocol/)

---

## P — PDN / PHY / Pseudo-channel

### PDN (Power Delivery Network)

**Definition.** 전원을 각 회로 블록에 분배하는 배선과 소자의 집합.

**Source.** 업계 공개 자료.

**Related.** Base Die, 2.5D Packaging.

**Example.** base die의 네 가지 주요 기능 갈래 중 전력 전달을 담당하는 영역.

**See also.** [Ch06 — Base Die = 미니 SoC](../06_base_die_soc/)

### PHY (Physical Layer)

**Definition.** 디지털 로직과 외부 전송 매체 사이에서 신호의 물리적 송수신을 담당하는 회로 블록.

**Source.** Common usage / 벤더 기술 문서.

**Related.** Mixed-level Verification, Base Die, Training.

**Example.** HBM4의 base die가 탑재하는 2048-bit I/O와 그 클럭 네트워크.

**See also.** [Ch06 — Base Die = 미니 SoC](../06_base_die_soc/)

### Pseudo-channel

**Definition.** 하나의 채널을 데이터 경로와 뱅크 기준으로 분할하되 CA 버스는 공유하는 하위 접근 단위.

**Source.** JEDEC 공개 자료 / McMaster ICCAD 2021.

**Related.** Channel, CA Bus, Semi-independent.

**Example.** HBM3의 64-bit 채널이 32-bit짜리 두 개의 pseudo-channel로 나뉘어 스택당 32개가 존재하는 구성.

**See also.** [Ch04 — 채널 · Pseudo-channel · 주소맵](../04_channels_addressing/)

---

## R — RAS

### RAS (Reliability, Availability, Serviceability)

**Definition.** 시스템이 오류에 대응하여 정확성과 가용성을 유지하도록 하는 기능들의 총칭.

**Source.** 업계 통용 / JEDEC 공개 자료.

**Related.** On-die ECC, ECS, CA Parity, MBIST.

**Example.** on-die ECC, ECS, parity 검출, 리페어 절차가 함께 구성하는 기능군.

**See also.** [Ch06 — Base Die = 미니 SoC](../06_base_die_soc/) · [RAS 코스](../../ras/)

---

## S — Scoreboard / Semi-independent / SPHBM4 / Stack Height

### Scoreboard

**Definition.** 설계의 실제 출력과 검증 환경이 계산한 기대값을 비교하여 정합성을 판정하는 검증 구성요소.

**Source.** Common DV usage; UVM 1.2 Reference Manual.

**Related.** Assertion, Behavioral Model, VIP.

**Example.** 주소로부터 목적지 채널과 pseudo-channel을 자체 계산하여 실제 접근 위치와 대조하는 구현.

**See also.** [Ch04 — 채널 · Pseudo-channel · 주소맵](../04_channels_addressing/) · [UVM 코스](../../uvm/)

### Semi-independent

**Definition.** 일부 자원은 분리되어 있고 일부 자원은 공유하는 상태의 독립성 수준.

**Source.** 본 코스 정의 (McMaster ICCAD 2021의 서술 기반).

**Related.** Pseudo-channel, CA Bus, Concurrency.

**Example.** pseudo-channel이 뱅크와 데이터 경로는 분리하되 CA 버스를 공유하고 커맨드는 각자 해석·실행하는 동작 방식.

**See also.** [Ch04 — 채널 · Pseudo-channel · 주소맵](../04_channels_addressing/)

### SPHBM4

**Definition.** 인터페이스 폭을 512-bit로 좁혀 정의한 HBM4 계열의 별도 표준.

**Source.** JEDEC 공개 보도자료 / Tom's Hardware.

**Related.** HBM4, Interposer, 2.5D Packaging.

**Example.** 실리콘 인터포저 대신 유기 기판 사용을 겨냥하여 원가 절감을 목표로 하는 규격.

**See also.** [Ch02 — 세대 지형도](../02_generations/)

### Stack Height (N-high)

**Definition.** 하나의 HBM 스택에 적층된 core die의 장수.

**Source.** JEDEC 공개 자료 / 벤더 제품 자료.

**Related.** Core Die, Capacity, TSV.

**Example.** 12-high 구성은 core die 12장을 적층한 것으로 8-high 대비 용량이 크다.

**See also.** [Ch03 — 스택 구조와 DUT 경계](../03_stack_architecture/)

---

## T — TSV

### TSV (Through-Silicon Via)

**Definition.** 실리콘 기판을 수직으로 관통하여 적층된 다이 사이를 전기적으로 연결하는 배선 구조.

**Source.** 업계 공개 자료.

**Related.** Microbump, Stack Height, Hybrid Bonding, 2.5D Packaging.

**Example.** 직경 10~20 µm 규모의 수직 비아로 core die와 base die를 연결하는 구조.

**See also.** [Ch01 — 왜 HBM인가](../01_why_hbm/) · [Ch03 — 스택 구조와 DUT 경계](../03_stack_architecture/)

---

## V — VIP

### VIP (Verification IP)

**Definition.** 특정 프로토콜의 자극 생성·관측·검사 기능을 재사용 가능하게 패키지한 검증 구성요소.

**Source.** Common DV usage.

**Related.** Custom UVM Agent, Behavioral Model, Scoreboard.

**Example.** 표준 인터페이스에 대해 상용으로 제공되는 것과, 비표준 인터페이스를 위해 사내에서 개발하는 것이 함께 쓰인다.

**See also.** [Ch06 — Base Die = 미니 SoC](../06_base_die_soc/) · [UVM 코스](../../uvm/)

---

## 관련 자료

- [코스 홈](../) — 6개 챕터 안내와 JD 매핑
- [퀴즈](../quiz/) — 챕터별 이해도 점검
- [DRAM / DDR 코스](../../dram_ddr/) — DRAM 기본 원리
- [DRAM JEDEC Deep-Dive](../../dram_jedec_dv/) — JEDEC 스펙 기반 검증
- [Mixed-Signal DV](../../mixed_signal_dv/) — RNM/AMS 검증 방법론
- [UVM 코스](../../uvm/) — 검증 방법론 기초
