---
title: "Quiz — N01: 왜 DFD인가"
---

[← N01 본문으로 돌아가기](../../01_why_dfd/)

---

## Q1. (Remember)

Arm 기반 SoC 디버그 스택을 외부에서 안쪽 순서로 올바르게 나열한 것은?

- [ ] A. CoreSight → DAP → JTAG → External Debugger
- [ ] B. External Debugger → JTAG/SWD 핀 → DAP(ADI) → CoreSight
- [ ] C. JTAG → CoreSight → DAP → 시스템 메모리
- [ ] D. DAP → JTAG → External Debugger → CoreSight

<details>
<summary>정답 / 해설</summary>

**B**. 호스트의 External Debugger가 JTAG(또는 SWD) 핀으로 칩에 진입하고, DAP(ADI)가 그 직렬 접근을 메모리-맵 버스 접근으로 변환하며, 그 버스 너머에 CoreSight 컴포넌트와 시스템 메모리가 있습니다. 즉 물리 핀(가장 바깥) → 아키텍처 다리(DAP) → IP 생태계(CoreSight) 순서입니다. 나머지는 계층 순서가 뒤섞여 있습니다.

</details>
## Q2. (Understand)

invasive debug와 non-invasive debug의 차이를 설명하고, 각각의 예를 드시오.

<details>
<summary>정답 / 해설</summary>

**invasive debug**는 코어 실행에 직접 개입합니다 — halt(정지), single-step, breakpoint, 레지스터/메모리 write 등. 코어를 멈추므로 동작 타이밍을 바꿉니다. **non-invasive debug**는 실행을 건드리지 않고 관찰만 합니다 — 실시간 trace 수집, 성능 카운터(PMU) 읽기 등. 코어는 정상 속도로 계속 돕니다. 이 둘이 분리되어 있기 때문에 인증 신호도 invasive용(DBGEN/SPIDEN)과 non-invasive용(NIDEN/SPNIDEN)으로 나뉩니다.

</details>
## Q3. (Apply)

"코어를 halt하고 PC를 읽는다"는 요청을 처리할 때, 디버거가 보낸 직렬 비트 스트림이 시스템 버스 트랜잭션으로 바뀌는 곳은 어느 층인가?

- [ ] A. JTAG TAP controller
- [ ] B. DAP의 MEM-AP
- [ ] C. CoreSight ETM
- [ ] D. External Debugger 내부

<details>
<summary>정답 / 해설</summary>

**B**. JTAG/SWD 핀으로 들어온 직렬 데이터는 DP가 디코딩해 어느 AP를 쓸지 정하고(SELECT), MEM-AP가 TAR/CSW/DRW를 받아 비로소 APB/AHB/AXI 버스 트랜잭션을 발행합니다. A(TAP)는 직렬 scan만 다루지 메모리-맵 트랜잭션을 만들지 않고, C(ETM)는 trace source이며, D는 호스트 측입니다. 핀↔직렬은 JTAG의 세계, 그 너머는 AMBA 버스의 세계이고 DAP가 변환기입니다.

</details>
## Q4. (Analyze)

디버그 서브시스템을 코어 전원/클럭과 _독립_으로(always-on, 독립 DBG clock) 두는 이유를 설계 관점에서 설명하시오.

<details>
<summary>정답 / 해설</summary>

디버그가 가장 필요한 순간이 바로 시스템이 비정상일 때 — 코어가 power-gating으로 꺼졌거나, 시스템 클럭이 멈췄거나, warm reset 직후 — 이기 때문입니다. 만약 디버그 로직이 코어 전원/클럭에 종속되면, 문제가 생긴 그 순간 디버그 통로도 같이 죽어 진단이 불가능해집니다. 따라서 독립 DBG clock과 always-on 전원에 두어, 코어가 꺼져 있어도 디버거가 DAP에 붙어 코어를 깨우거나 상태를 읽을 수 있게 합니다. 추가로 reset isolation을 두어 warm/cold reset을 넘어 디버그 세션이 유지되도록 합니다.

</details>
## Q5. (Evaluate)

양산 칩에서 "실시간 trace는 되는데 코어 halt만 안 된다"는 보고가 들어왔다. 가장 가능성 높은 원인과 점검 대상은?

- [ ] A. JTAG 핀이 단선됨 — 보드 배선 점검
- [ ] B. NIDEN은 enable인데 DBGEN이 disable — fuse/lifecycle 상태 점검
- [ ] C. ROM table base 주소 오류 — DAP 구성 점검
- [ ] D. TCK가 인가되지 않음 — 클럭 점검

<details>
<summary>정답 / 해설</summary>

**B**. trace/PMU는 non-invasive라 NIDEN으로 동작하고, halt/step은 invasive라 DBGEN이 필요합니다. "trace는 되는데 halt만 안 된다"는 것은 NIDEN=enable, DBGEN=disable 상태를 정확히 가리킵니다. 양산 칩에서 실행 개입은 막되 진단용 trace는 허용하는 정책은 흔하므로 fuse/lifecycle이 DBGEN을 껐을 가능성이 높습니다. A·D(핀/클럭 문제)라면 trace조차 안 됐을 것이고, C(ROM table)라면 컴포넌트 발견 자체가 실패했을 것입니다. secure 코드라면 SPIDEN/SPNIDEN을 같은 논리로 봅니다.

</details>
