---
title: "DFD 용어집"
---

이 페이지는 본 코스에서 사용되는 DFD(Design For Debug) 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

:::tip[검색 활용]
상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.
:::
---

## A — ADI / Access Port (AP) / Authentication Signals

### ADI (Arm Debug Interface)

**Definition.** 외부 디버그 프로브와 온칩 디버그 버스 사이의 표준 다리인 Debug Access Port(DAP)를 정의하는 Arm 아키텍처 사양.

**Source.** Arm IHI 0031 — Arm Debug Interface Architecture Specification (HDG `dfd_spec.md` §2).

**Related.** DAP, DP, AP, ADIv5, ADIv6.

**Example.** ADIv5는 32비트 AP 주소 공간을 가지며 Cortex-M/A/R에 널리 배포되고, ADIv6는 64비트 주소와 계층적 ROM table을 지원한다.

**See also.** [N03 — Arm ADI(DAP) & CoreSight](../03_adi_dap_coresight/)

### Access Port (AP)

**Definition.** DAP의 시스템 측 인터페이스로, 외부 디버그 접근을 온칩 자원에 대한 접근으로 노출하는 컴포넌트.

**Source.** Arm IHI 0031 (HDG `dfd_spec.md` §2).

**Related.** MEM-AP, JTAG-AP, DP, SELECT.

**Example.** MEM-AP(AHB-AP/AXI-AP/APB-AP)는 메모리-맵 접근을, JTAG-AP는 SoC 내부 레거시 scan chain 접근을 제공한다.

**See also.** [N03](../03_adi_dap_coresight/)

### Authentication Signals (DBGEN / NIDEN / SPIDEN / SPNIDEN)

**Definition.** invasive/non-invasive 및 secure/non-secure 디버그를 각각 enable하거나 차단하는 CoreSight 인증 입력 신호 집합.

**Source.** Arm IHI 0029 (HDG `dfd_spec.md` §3 Authentication signals).

**Related.** Invasive Debug, Non-invasive Debug, Secure Debug, fuse/lifecycle.

**Example.** DBGEN은 non-secure halt를, NIDEN은 non-secure trace를, SPIDEN은 secure halt를, SPNIDEN은 secure trace를 enable한다.

**See also.** [N01 §1.2](../01_why_dfd/), [N03 §5.1](../03_adi_dap_coresight/)

---

## B — Boundary Scan / BYPASS

### Boundary Scan

**Definition.** 칩 IO 핀 옆의 scan cell을 직렬 register로 연결해 핀 상태를 capture/제어함으로써 PCB 연결을 검사하는 JTAG 기능.

**Source.** IEEE Std 1149.1 (HDG `dfd_spec.md` §1).

**Related.** TAP, EXTEST, SAMPLE, Data Register.

**Example.** EXTEST instruction으로 boundary scan register에 패턴을 shift하면 칩을 떼지 않고 납땜 단선을 검출한다.

**See also.** [N02 §4.3](../02_jtag_boundary_scan/)

### BYPASS

**Definition.** daisy chain에서 해당 TAP을 1비트 지연으로만 통과시키도록 TDI와 TDO 사이에 1비트 register를 연결하는 JTAG instruction.

**Source.** IEEE Std 1149.1 (HDG `dfd_spec.md` §1).

**Related.** Daisy Chain, Instruction Register, Data Register.

**Example.** 8개 TAP 중 하나의 500비트 register에만 접근할 때 나머지 7개를 BYPASS로 두면 총 507비트만 shift한다.

**See also.** [N02 §5.2](../02_jtag_boundary_scan/)

---

## C — CoreSight / Cross Trigger (CTI/CTM) / CSW

### CoreSight

**Definition.** DAP 너머에서 디버그 제어, cross-triggering, 실시간 trace를 제공하는 Arm의 온칩 디버그·trace IP family.

**Source.** Arm IHI 0029 (HDG `dfd_spec.md` §3).

**Related.** ETM, CTI, ETR, ROM table, Trace Source/Link/Sink.

**Example.** trace source(ETM) → link(Funnel) → sink(ETR)로 이어지는 trace 파이프라인이 CoreSight 컴포넌트로 구성된다.

**See also.** [N03 §4.4](../03_adi_dap_coresight/)

### CTI / CTM (Cross Trigger Interface / Matrix)

**Definition.** halt/restart/trigger 이벤트를 코어와 trace 블록 사이에 라우팅해 멀티코어 동기 디버그를 가능하게 하는 CoreSight 제어 컴포넌트.

**Source.** Arm IHI 0029 (HDG `dfd_spec.md` §3 Control).

**Related.** CoreSight, Invasive Debug, multi-core halt.

**Example.** 코어 0이 breakpoint에 걸릴 때 CTI/CTM이 코어 1·2·3도 동시에 halt시킨다.

**See also.** [N03 §4.6](../03_adi_dap_coresight/)

### CSW (Control/Status Word)

**Definition.** MEM-AP에서 전송 size와 auto-increment 같은 버스 트랜잭션 속성을 지정하는 레지스터.

**Source.** Arm IHI 0031 (HDG `dfd_spec.md` §2 Typical access flow).

**Related.** MEM-AP, TAR, DRW, SELECT.

**Example.** 32비트 워드 접근과 auto-increment를 켜려면 DRW 접근 전에 CSW를 설정한다.

**See also.** [N03 §3](../03_adi_dap_coresight/)

---

## D — DAP / Debug Port (DP)

### DAP (Debug Access Port)

**Definition.** 하나의 Debug Port와 하나 이상의 Access Port로 구성되어, 외부 디버그 프로브와 온칩 디버그 버스를 잇는 ADI 정의 브리지.

**Source.** Arm IHI 0031 (HDG `dfd_spec.md` §2).

**Related.** DP, AP, MEM-AP, ROM table.

**Example.** 디버거가 JTAG로 DAP에 접근해 SELECT/CSW/TAR/DRW로 시스템 버스 트랜잭션을 발행한다.

**See also.** [N03](../03_adi_dap_coresight/)

### Debug Port (DP)

**Definition.** DAP의 물리 측 인터페이스로, JTAG 또는 Serial Wire 프로토콜을 처리하고 SELECT로 사용할 AP를 지정하는 컴포넌트.

**Source.** Arm IHI 0031 (HDG `dfd_spec.md` §2 DAP architecture).

**Related.** JTAG-DP, SW-DP, SWJ-DP, AP.

**Example.** SWJ-DP는 JTAG와 Serial Wire를 핀에서 자동 선택하는 DP 변종이다.

**See also.** [N03 §4.1](../03_adi_dap_coresight/)

---

## E — ETM / ETB·ETF·ETR

### ETM (Embedded Trace Macrocell)

**Definition.** 코어별 instruction(및 선택적 data) 실행 trace 스트림을 생성하는 CoreSight trace source.

**Source.** Arm IHI 0029 (HDG `dfd_spec.md` §3 Trace sources).

**Related.** Trace Source, ITM, STM, Funnel, ETR.

**Example.** 4개 코어의 ETM 출력을 Funnel로 병합한 뒤 ETR로 DRAM에 기록한다.

**See also.** [N03 §4.5](../03_adi_dap_coresight/)

### ETB / ETF / ETR

**Definition.** trace 데이터를 각각 on-chip SRAM 버퍼(ETB), FIFO link(ETF), AXI 경유 시스템 DRAM(ETR)에 저장하는 CoreSight trace sink 변종.

**Source.** Arm IHI 0029, Arm DDI 0480 (HDG `dfd_spec.md` §3 Trace sinks).

**Related.** TMC, TPIU, Trace Sink.

**Example.** TMC는 ETB/ETF/ETR 세 모드를 구성으로 선택하는 현대적 블록이다.

**See also.** [N03 §4.5](../03_adi_dap_coresight/)

---

## I — Invasive / Non-invasive Debug

### Invasive Debug

**Definition.** 코어 실행에 직접 개입해 halt, single-step, breakpoint, 레지스터/메모리 write를 수행하는 디버그 동작 분류.

**Source.** Arm IHI 0029 (HDG `dfd_spec.md` §3 Authentication signals).

**Related.** DBGEN, SPIDEN, Non-invasive Debug, CTI.

**Example.** 코어를 halt하고 PC를 읽으려면 DBGEN(non-secure) 또는 SPIDEN(secure)이 enable되어야 한다.

**See also.** [N01 §1.2](../01_why_dfd/)

### Non-invasive Debug

**Definition.** 코어 실행을 멈추지 않고 trace 수집과 성능 카운터(PMU) 읽기로 관찰만 하는 디버그 동작 분류.

**Source.** Arm IHI 0029 (HDG `dfd_spec.md` §3).

**Related.** NIDEN, SPNIDEN, Invasive Debug, Trace.

**Example.** NIDEN이 enable이고 DBGEN이 disable이면 실시간 trace는 되지만 코어 halt는 차단된다.

**See also.** [N01 §1.2](../01_why_dfd/)

---

## J — JTAG

### JTAG (IEEE 1149.1)

**Definition.** TCK/TMS/TDI/TDO(및 선택적 TRSTn) 핀과 TAP controller로 칩 내부 register에 직렬 접근하는 표준 테스트/디버그 access port.

**Source.** IEEE Std 1149.1 (HDG `dfd_spec.md` §1).

**Related.** TAP, IR, DR, SWD, Boundary Scan.

**Example.** 현대 SoC는 boundary scan용 JTAG TAP을 DAP 접근 통로로 재사용한다.

**See also.** [N02](../02_jtag_boundary_scan/)

---

## M — MEM-AP

### MEM-AP (Memory Access Port)

**Definition.** SELECT/CSW/TAR/DRW 레지스터를 통해 메모리-맵 시스템 버스(AHB/AXI/APB) 트랜잭션을 발행하는 Access Port 유형.

**Source.** Arm IHI 0031 (HDG `dfd_spec.md` §2).

**Related.** AP, DAP, ROM table, APB-AP, CSW, TAR, DRW.

**Example.** 대부분의 CoreSight 컴포넌트는 APB-AP 형태의 MEM-AP를 통해 접근된다.

**See also.** [N03 §3](../03_adi_dap_coresight/)

---

## R — ROM table

### ROM table

**Definition.** MEM-AP의 base 주소에 위치해 SoC에 존재하는 CoreSight 컴포넌트들의 주소를 열거하는 디렉터리.

**Source.** Arm IHI 0031 (HDG `dfd_spec.md` §2 ROM table).

**Related.** MEM-AP, DAP, ADIv6 hierarchical ROM table.

**Example.** 디버거는 connect 시점에 ROM table을 walk해 코어·trace source·trigger 블록을 발견한다.

**See also.** [N03 §4.3](../03_adi_dap_coresight/)

---

## S — SWD / TAP

### SWD (Serial Wire Debug)

**Definition.** SWCLK와 SWDIO 두 핀으로 JTAG와 동일한 DAP를 노출하는, ADI가 정의한 핀 절약형 디버그 프로토콜.

**Source.** Arm IHI 0031 (HDG `dfd_spec.md` §1 Role in debug).

**Related.** SW-DP, SWJ-DP, JTAG, DAP.

**Example.** 핀이 부족한 디바이스에서 JTAG 4~5핀 대신 SWD 2핀을 쓰되 같은 DAP에 접근한다.

**See also.** [N02 §5.3](../02_jtag_boundary_scan/)

### TAP (Test Access Port) Controller

**Definition.** TMS 입력으로 구동되는 16-state FSM으로, IR scan과 DR scan을 Capture/Shift/Update 단계로 시퀀싱하는 JTAG 제어 블록.

**Source.** IEEE Std 1149.1 (HDG `dfd_spec.md` §1 Key concepts).

**Related.** TMS, IR, DR, Test-Logic-Reset.

**Example.** TMS=1을 5클럭 인가하면 어느 상태에서든 Test-Logic-Reset에 도달한다.

**See also.** [N02 §4.1](../02_jtag_boundary_scan/)

---

## 추가 약어

| 약어 | 풀네임 | 한 줄 의미 |
|------|--------|-----------|
| **DFD** | Design For Debug | 칩 내부를 외부에서 관찰·제어하게 만드는 디버그 설계 인프라 |
| **TAR** | Target Address Register | MEM-AP에서 접근할 목표 주소를 담는 레지스터 |
| **DRW** | Data Read/Write | MEM-AP의 데이터 레지스터 — 접근 시 버스 트랜잭션을 트리거 |
| **SELECT** | — | DP에서 사용할 AP와 레지스터 뱅크를 지정하는 레지스터 |
| **IR / DR** | Instruction / Data Register | IR이 DR을 선택, DR이 실제 직렬 데이터를 shift |
| **IDCODE** | — | reset 후 기본 선택되는 32비트 칩 식별 DR |
| **TPIU** | Trace Port Interface Unit | off-chip 병렬 trace export 블록 |
| **TMC** | Trace Memory Controller | ETB/ETF/ETR 모드를 구성으로 선택하는 trace 블록 |
| **PMU** | Performance Monitoring Unit | 성능 카운터 — non-invasive 디버그로 읽음 |
