---
title: "Quiz — N03: Arm ADI(DAP) & CoreSight"
---

[← N03 본문으로 돌아가기](../../03_adi_dap_coresight/)

---

## Q1. (Remember)

DAP에서 DP(Debug Port)와 AP(Access Port)의 책임을 올바르게 짝지은 것은?

- [ ] A. DP=시스템 측 메모리 접근, AP=물리 측 프로토콜
- [ ] B. DP=물리 측(JTAG/SWD) + AP 선택, AP=시스템 측 메모리-맵 접근
- [ ] C. DP와 AP 모두 trace 데이터 수집
- [ ] D. DP=ROM table 저장, AP=인증 신호 게이팅

<details>
<summary>정답 / 해설</summary>

**B**. DP는 물리 측 인터페이스로 JTAG/SWD 프로토콜을 처리하고 SELECT 레지스터로 어느 AP를 쓸지 고릅니다. AP(특히 MEM-AP)는 시스템 측으로 메모리-맵 접근을 버스 트랜잭션으로 발행합니다. 하나의 DP가 여러 AP를 거느립니다. A는 책임이 뒤바뀌었고, C(trace)는 CoreSight source의 역할이며, D는 ROM table/인증을 잘못 귀속했습니다.

</details>
## Q2. (Understand)

ROM table이 무엇이며, 디버거가 이를 어떻게 사용하는지 설명하시오.

<details>
<summary>정답 / 해설</summary>

ROM table은 각 MEM-AP의 base 주소에 놓인, 그 칩에 존재하는 CoreSight 컴포넌트들의 _주소 목록 디렉터리_입니다. 디버거는 칩에 connect할 때 그 칩의 구체적 구성(코어 몇 개, trace 블록 어디)을 미리 알지 못하므로, base부터 ROM table을 읽어 내려가며(walk) 코어, trace source, trigger 블록의 주소를 _런타임에 발견_합니다. 덕분에 한 디버거가 표준 ADI 프로토콜만 알면 다양한 Arm SoC를 지원할 수 있습니다. ADIv6에서는 ROM table이 다른 ROM table을 가리키는 계층 구조를 가져 대규모 시스템을 표현합니다.

</details>
## Q3. (Apply)

MEM-AP로 어떤 CoreSight 레지스터에 32비트 값을 쓰려고 한다. 접근해야 하는 DAP 레지스터 순서로 올바른 것은?

- [ ] A. DRW → TAR → CSW → SELECT
- [ ] B. SELECT → CSW → TAR → DRW
- [ ] C. TAR → DRW (CSW/SELECT 불필요)
- [ ] D. CSW → DRW → TAR → SELECT

<details>
<summary>정답 / 해설</summary>

**B**. `SELECT`로 사용할 AP와 레지스터 뱅크를 지정하고, `CSW`로 전송 size와 auto-increment를 설정하고, `TAR`에 목표 주소를 쓰고, 마지막으로 `DRW`에 데이터를 씁니다. 핵심은 _DRW 접근이 실제 버스 트랜잭션을 트리거_한다는 점 — TAR는 주소만 설정할 뿐 전송을 일으키지 않습니다. C처럼 SELECT/CSW를 건너뛰면 어느 AP·어떤 size인지 정해지지 않습니다.

</details>
## Q4. (Analyze)

CoreSight 컴포넌트 ETB, ETF, ETR을 trace sink 관점에서 구분하고, 어느 것이 시스템 DRAM에 trace를 쓰는지 설명하시오.

<details>
<summary>정답 / 해설</summary>

셋 다 trace sink(또는 link)지만 동작이 다릅니다. **ETB(Embedded Trace Buffer)** 는 on-chip SRAM 버퍼에 trace를 저장합니다. **ETF(Embedded Trace FIFO)** 는 FIFO link로 trace 스트림을 버퍼링·중계합니다. **ETR(Embedded Trace Router)** 는 AXI 마스터로서 trace를 _시스템 DRAM_에 직접 씁니다 — 따라서 on-chip 버퍼 용량의 제약 없이 DRAM 크기만큼 길게 수집할 수 있습니다. 현대적 블록인 **TMC(Trace Memory Controller)** 는 이 ETB/ETF/ETR 세 모드를 구성으로 선택합니다. 질문의 "DRAM에 쓰는 것"은 ETR입니다.

</details>
## Q5. (Evaluate)

off-chip trace 핀(TPIU)을 둘 여유가 없는데 코어 4개의 instruction trace를 길게 수집해야 한다. 어떤 CoreSight 구성이 적절하며 그 이유는?

<details>
<summary>정답 / 해설</summary>

**4개 코어의 ETM(trace source)을 Funnel(link)로 병합한 뒤 sink를 ETR(또는 TMC를 ETR 모드)로 두어 시스템 DRAM에 trace를 쓰는** 구성이 적절합니다. ETR은 AXI 마스터로 DRAM에 기록하므로 off-chip trace 핀(TPIU)이 전혀 필요 없고, DRAM 용량만큼 길게 수집할 수 있습니다. 수집 후 디버거가 DAP(MEM-AP)로 DRAM의 trace 버퍼를 읽어 갑니다. 대역이 극히 높아 DRAM 대역으로 부족하면 HSSTP(고속 직렬)가 대안이지만 핀이 필요하므로, 핀 제약 상황에서는 ETR→DRAM이 최선입니다. 멀티코어 trace 정렬이 필요하면 CTI/CTM으로 trace 시작/정지를 동기화합니다.

</details>
