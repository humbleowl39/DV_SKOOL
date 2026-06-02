---
title: "Quiz — Module 01: APB & AHB"
---

[← Module 01 본문으로 돌아가기](../../01_apb_ahb/)

---

## Q1. (Remember)

APB 단일 트랜잭션의 최소 cycle 수와 phase 이름은?

<details>
<summary>정답 / 해설</summary>

**2 cycle**, **SETUP** (PSEL=1, PENABLE=0) → **ACCESS** (PSEL=1, PENABLE=1, PREADY=1). Wait state 없으면 이 2 cycle이 minimum.

APB는 "느린 peripheral을 단순하게 붙이기 위한" 버스이므로, 설계 자체가 최소 제어 신호로 동작하도록 만들어졌습니다. SETUP phase에서는 "누구에게 요청할지(PSEL)"만 알리고, ACCESS phase에서 비로소 PENABLE을 올려 실제 read/write를 확정합니다. Slave가 준비되지 않았을 때는 PREADY를 0으로 유지해 ACCESS phase를 연장하는데, 이것이 wait state(N ≥ 1 cycle)입니다. 따라서 최소 트랜잭션은 wait state가 전혀 없는 2 cycle입니다.

</details>
## Q2. (Understand)

AHB-to-APB Bridge는 AHB INCR4 burst를 어떻게 처리하는가?

- [ ] A. APB도 INCR4를 그대로 지원하므로 1번에 전송
- [ ] B. APB는 burst를 지원하지 않으므로 4개의 독립적 APB 단일 전송으로 분해
- [ ] C. Bridge가 4 cycle 한 번에 묶어서 처리
- [ ] D. Bridge가 ERROR 응답

<details>
<summary>정답 / 해설</summary>

**B**. APB는 burst 개념이 없음. Bridge는 AHB의 burst를 풀어서 APB에 4번의 단일 전송으로 보냄. 면적 절약 vs 성능의 trade-off.

APB 사양에는 burst 전송 메커니즘 자체가 정의되어 있지 않습니다. 따라서 AHB-to-APB Bridge는 AHB 쪽에서 받은 INCR4 burst를 그대로 APB로 넘길 수 없고, SETUP→ACCESS를 4회 반복하는 독립적인 단일 전송 4개로 분해합니다. 이 때문에 A처럼 "APB가 burst를 지원한다"는 것은 사실이 아니고, C처럼 "4 cycle을 묶어서 한 번에 처리"하는 것도 APB의 동작 방식이 아닙니다. D의 ERROR 응답은 슬레이브가 전송 자체를 거부할 때 사용하는 것이지 burst 처리 방식이 아닙니다.

</details>
## Q3. (Apply)

AHB Master가 3 연속 Write를 수행 중 A2의 Data Phase에서 Slave가 HREADY=0을 1 cycle 삽입했다. T2의 HADDR 값이 A2일 때, T3의 HADDR 값은?

<details>
<summary>정답 / 해설</summary>

**A2** (변하지 않음). Wait state 동안 HADDR과 HWDATA 모두 유지. T3에서 HREADY=1이 되면 T4에 A3로 진행. Wait state 중 신호 변경은 가장 흔한 AHB 버그.

AHB는 주소-데이터 파이프라인 구조이기 때문에, 슬레이브가 HREADY=0을 내리면 전체 파이프라인이 그 자리에서 "얼어붙습니다". 즉, 현재 Data phase의 HWDATA와 Address phase의 HADDR 모두 값을 유지해야 합니다. HREADY=0인 사이클에서 Master가 HADDR를 A3로 전진시키면, 슬레이브는 A2 데이터를 샘플해야 하는 시점에 A3 주소를 보게 되므로 트랜잭션이 깨집니다. 이것이 wait state 중 신호 변경이 AHB에서 가장 흔히 발생하는 프로토콜 위반 유형인 이유입니다.

</details>
## Q4. (Analyze)

AHB HRESP ERROR가 1 cycle이 아닌 2 cycle에 걸쳐 응답되는 이유는?

<details>
<summary>정답 / 해설</summary>

AHB는 주소-데이터 파이프라인이라 Master가 에러 응답을 받을 때 이미 다음 주소를 발행한 상태. Cycle 1에서 HREADY=0으로 파이프라인을 멈추고 에러를 알리고, Cycle 2에서 HREADY=1로 에러를 확정해 Master가 다음 주소를 안전하게 취소할 시간을 보장.

AHB의 파이프라인 구조에서는 슬레이브가 데이터를 처리하는 동안 마스터는 이미 다음 주소를 버스에 올려놓습니다. 에러가 발생했을 때 즉시 HREADY=1로 에러를 알리면, 마스터는 이미 발행된 다음 주소를 취소할 클럭이 없습니다. 그래서 AHB 사양은 에러 응답을 반드시 2 cycle로 처리하도록 규정합니다. 첫 번째 사이클에 HREADY=0 + HRESP=ERROR로 파이프라인을 정지시키고, 두 번째 사이클에 HREADY=1 + HRESP=ERROR로 에러를 확정해서 마스터가 진행 중인 다음 트랜잭션을 안전하게 중단(idle)할 시간을 확보합니다.

</details>
## Q5. (Evaluate)

APB4에서 PSTRB가 추가된 가장 큰 동기는?

- [ ] A. burst 지원
- [ ] B. byte-level write로 Read-Modify-Write 회피 (원자성)
- [ ] C. multi-master 지원
- [ ] D. clock domain crossing

<details>
<summary>정답 / 해설</summary>

**B**. APB3까지는 단어 단위 write만 가능 → 32-bit 레지스터의 일부 바이트만 변경하려면 RMW 필요. RMW 도중 다른 주체(예: HW)가 status bit를 set하면 race. PSTRB로 byte-level write가 가능해져 원자성 + 성능 모두 개선.

APB3 이하에서는 레지스터에 1 바이트만 기록하고 싶어도 반드시 32비트 전체를 Read한 뒤 수정하고 다시 Write해야 했습니다. 이 Read-Modify-Write(RMW) 사이에 하드웨어 로직이 같은 레지스터의 status bit를 변경하면, SW가 Read한 값은 구식이 되고 이전 값이 덮어씌워지는 경쟁 조건이 발생합니다. A처럼 burst를 지원하기 위한 신호가 아니고, C·D처럼 multi-master나 클럭 도메인과도 무관합니다. PSTRB는 정확히 이 RMW 경쟁 조건을 없애고 byte 단위의 원자적 쓰기를 보장하기 위해 APB4에서 추가되었습니다.

</details>
