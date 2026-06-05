---
title: "Quiz — N02: JTAG & Boundary Scan"
---

[← N02 본문으로 돌아가기](../../02_jtag_boundary_scan/)

---

## Q1. (Remember)

JTAG 신호 중 TAP state machine을 제어하는(상태 전이를 결정하는) 신호는?

- [ ] A. TCK
- [ ] B. TDI
- [ ] C. TMS
- [ ] D. TDO

<details>
<summary>정답 / 해설</summary>

**C (TMS)**. TMS(Test Mode Select)는 매 TCK마다 그 값(0/1)에 따라 TAP 16-state FSM의 다음 상태를 결정합니다. TCK(A)는 클럭, TDI(B)는 칩으로 들어가는 데이터 입력, TDO(D)는 칩에서 나오는 데이터 출력입니다. 데이터는 TDI/TDO로 흐르고, _제어_는 TMS가 합니다. TMS=1을 5클럭 주면 어느 상태에서든 Test-Logic-Reset에 도달합니다.

</details>
## Q2. (Understand)

TAP의 IR(Instruction Register)과 DR(Data Register)의 관계를 설명하시오.

<details>
<summary>정답 / 해설</summary>

IR은 "지금 TDI↔TDO 사이에 어떤 DR을 연결할지"를 선택합니다. IR에 실린 instruction(IDCODE, BYPASS, EXTEST, 벤더 정의 등)에 따라 대응하는 DR이 TDI와 TDO 사이의 직렬 경로에 연결됩니다. 예를 들어 IR이 IDCODE면 32비트 IDCODE register가, BYPASS면 1비트 register가, EXTEST면 boundary scan register가, 벤더 instruction이면 DAP access register가 연결됩니다. 즉 같은 직렬 핀으로 여러 종류의 접근을 하기 위해, IR이 먼저 "무엇을"을 고르고 DR이 실제 데이터를 shift합니다.

</details>
## Q3. (Apply)

Test-Logic-Reset 직후, IR scan 없이 곧바로 읽을 수 있는 Data Register는 무엇이며 그 이유는?

- [ ] A. Boundary Scan — reset 시 EXTEST가 기본
- [ ] B. IDCODE — reset 후 IR에 IDCODE가 기본 선택됨
- [ ] C. BYPASS — reset 시 항상 BYPASS
- [ ] D. 없음 — 항상 IR scan을 먼저 해야 함

<details>
<summary>정답 / 해설</summary>

**B (IDCODE)**. Test-Logic-Reset 상태에 들어가면 IR이 IDCODE instruction으로 기본 초기화됩니다. 따라서 reset 직후 IR scan을 거치지 않고 바로 DR scan(Capture-DR → Shift-DR)만 하면 32비트 IDCODE를 TDO로 읽을 수 있습니다. 이는 "DR을 쓰려면 항상 IR scan부터"라는 일반 규칙의 예외이며, 디버거가 connect 시 가장 먼저 칩을 식별하는 데 사용됩니다.

</details>
## Q4. (Analyze)

8개의 TAP이 daisy chain으로 연결되어 있고, 그중 하나의 boundary scan register(500비트)에만 접근하려 한다. 나머지 7개를 BYPASS로 두면 총 몇 비트를 shift해야 하는가? BYPASS가 없을 때와 비교해 설명하시오.

<details>
<summary>정답 / 해설</summary>

`500 + 7 = 507`비트입니다. daisy chain은 한 TAP의 TDO를 다음 TAP의 TDI에 이어 붙인 하나의 긴 직렬 register입니다. 관심 TAP은 500비트 boundary scan register를, 나머지 7개는 각각 1비트 BYPASS register를 끼워 넣으므로 총 507비트만 shift하면 됩니다. BYPASS가 없다면 나머지 7개 TAP의 긴 register(각각 수백 비트)를 모두 통과해야 해 수천 비트를 헛돌려야 합니다. BYPASS는 "관심 없는 TAP을 1비트 비용으로 건너뛰는" 장치입니다.

</details>
## Q5. (Evaluate)

"우리 칩은 핀이 극도로 부족하다. boundary scan과 디버그를 위해 JTAG 4핀 + 디버그용 별도 핀이 필요하다"는 주장을 평가하시오.

<details>
<summary>정답 / 해설</summary>

**과한 핀 요구입니다.** 첫째, boundary scan과 디버그(DAP access)는 _같은 TAP 인프라_(같은 TCK/TMS/TDI/TDO 핀)를 재사용합니다 — IR에 어떤 instruction을 싣느냐(EXTEST/SAMPLE vs 벤더 DAP access)로 무엇을 할지 갈리므로 디버그용 별도 핀이 불필요합니다. 둘째, 핀이 더 부족하다면 오히려 SWD(SWCLK + SWDIO, 2핀)로 줄일 수 있고, SWD는 JTAG과 _같은 DAP_를 노출하므로 디버그 기능 손실이 없습니다(SWJ-DP는 둘을 자동 전환). 따라서 4핀(또는 SWD 2핀) 하나로 boundary scan과 디버그를 모두 처리하는 것이 옳습니다.

</details>
