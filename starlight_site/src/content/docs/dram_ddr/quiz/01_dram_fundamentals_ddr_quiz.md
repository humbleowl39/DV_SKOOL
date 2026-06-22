---
title: "Quiz — Module 01: DRAM Fundamentals + LPDDR5"
---

[← Module 01 본문으로 돌아가기](../../01_dram_fundamentals_ddr/)

---

## Q1. (Remember)

DRAM의 한 cell은 어떤 기본 회로 요소로 구성되나?

<details>
<summary>정답 / 해설</summary>

**1 capacitor + 1 access transistor (1T1C)**. DRAM cell은 커패시터 한 개에 전하를 저장해 논리 1/0을 표현하고, 트랜지스터 한 개가 그 전하를 격리하거나 읽기 경로로 연결하는 스위치 역할을 한다. 커패시터는 시간이 지나면 전하가 자연 누설되므로, 데이터를 잃기 전에 일정 주기(tREFI)마다 row 내용을 다시 쓰는 Refresh가 반드시 필요하다. 이 1T1C 구조가 SRAM(flip-flop) 대비 면적을 극적으로 줄이지만, Refresh라는 관리 비용을 수반한다.

</details>
## Q2. (Understand)

ACT → RD → PRE 명령 시퀀스에서 각 명령의 역할은?

<details>
<summary>정답 / 해설</summary>

- **ACT**: 해당 row의 수만 개 cell 전하를 bit line에 올려 sense amplifier가 증폭하도록 한다. 이 단계 이후에야 column 접근이 가능하므로, ACT와 RD/WR 사이에는 반드시 tRCD만큼 기다려야 한다.
- **RD**: sense amplifier에 이미 올라온 row 데이터 중 원하는 column의 값을 burst 단위로 출력한다. row가 열린 상태에서 같은 row에 대한 RD는 반복 가능하며, 이것이 Row Hit 성능 이득의 원천이다.
- **PRE**: sense amplifier를 초기화하고 bit line을 다시 VDD/2 수준으로 프리차지해 다음 ACT를 받을 수 있는 상태로 만든다. PRE 이후 tRP를 기다리지 않고 다른 row를 ACT하면 데이터 손상 또는 timing violation이 발생한다.

</details>
## Q3. (Apply)

LPDDR5가 직전 세대(LPDDR4)와 서버용 DDR5에 대비해 갖는 핵심 차이 5가지를 들어보세요.

<details>
<summary>정답 / 해설</summary>

1. **WCK/CK 분리 클럭**: LPDDR5는 명령/주소용 저속 차동 CK와 데이터용 고속 **WCK**를 분리하고, gear에 따라 WCK:CK = 2:1 또는 4:1로 동작한다. 이는 단일 CK + DQS를 쓰는 DDR5와 구분되는 LPDDR5의 정체성으로, 데이터 idle 구간에 WCK 토글을 멈춰 전력을 절감한다.
2. **유연한 뱅크 구성**: LPDDR5는 MR(Mode Register)로 뱅크 모드를 선택한다 — **BG 모드(4 BG × 4 = 16뱅크) / 8B 모드(8뱅크) / 16B 모드(16뱅크)**. 직전 세대 LPDDR4는 BG가 없는 8뱅크였고, 서버용 DDR5는 8 BG × 4 = 32뱅크로 고정이다.
3. **이중 ECC (직교)**: LPDDR5는 셀 내부 비트를 정정하는 **On-die ECC**(디바이스 의존)와, DQ 전송경로를 보호하는 **Link ECC**(LPDDR5 고유, DDR5에는 없음)를 모두 지원한다. 둘은 보호 대상이 달라 서로 직교하므로 함께 쓸 수 있다.
4. **저전압 IO**: LPDDR5는 VDD1=1.8V, VDD2H≈1.05V, **VDDQ=0.5V**로 IO 전압을 크게 낮춰 모바일 전력 효율을 높였다. 비교로 DDR5는 VDD=1.1V·VPP=1.8V, LPDDR4X는 VDDQ=0.6V다.
5. **DVFSC + PASR**: LPDDR5는 동적 주파수/전압 gear(F0~F4 등, DVFSC)로 운용 중 주파수를 바꾸며, gear 전환 시 WCK:CK 비가 바뀌어 WCK2CK 재정렬이 필요하다. 또한 **PASR**(Partial Array Self-Refresh)로 사용하지 않는 배열의 refresh를 꺼 self-refresh 전력을 줄인다 — 이는 LPDDR 고유 기능으로 DDR5에는 없다.

(참고) Refresh granularity: tREFI(REF 명령 평균 간격)는 LPDDR5/DDR5 모두 3.9 μs, DDR4는 7.8 μs이며, LPDDR5는 per-bank refresh를 지원한다.

</details>
## Q4. (Analyze)

같은 bank에 연속 access하면 throughput이 떨어지는 이유는?

<details>
<summary>정답 / 해설</summary>

DRAM bank는 한 번에 단 하나의 row만 활성화할 수 있다. 따라서 같은 bank에서 다른 row에 접근하려면 현재 row를 PRE(tRP 대기)로 닫은 뒤, 새로운 row를 ACT(tRCD 대기)해야 한다. 이 tRP + tRCD 합산이 수십 cycle에 달하는 패널티가 된다. 반면 접근을 서로 다른 bank로 분산하면 각 bank가 독립적으로 ACT를 진행하므로 패널티 없이 병렬 처리가 가능하다. 이것이 Bank-Level Parallelism(BLP)이며, 스케줄러가 bank 분산을 우선하는 이유다.

</details>
## Q5. (Evaluate)

LPDDR5에서 WCK를 CK와 분리한 동기는?

<details>
<summary>정답 / 해설</summary>

**전력 절감**이 핵심 목적이다. LPDDR5의 데이터 레이트는 수 Gbps에 달하지만, 명령/주소 버스(CK)는 그보다 낮은 주파수로도 충분히 동작한다. 만약 단일 클럭을 쓰면 CK도 데이터 속도에 맞춰 고주파로 토글해야 하므로 불필요한 dynamic 전력이 낭비된다. WCK를 분리하면 데이터 전송이 없는 idle 구간에 WCK 토글을 멈출 수 있어, 모바일·엣지 환경에서 중요한 추가 절감 효과를 얻는다. WCK:CK 비는 gear에 따라 2:1 또는 4:1이며, DVFSC로 gear가 바뀌면 이 비도 바뀌어 WCK2CK 재정렬(leveling)이 다시 필요하다.

</details>
## Q6. (Analyze)

LPDDR5의 뱅크 구성과 prefetch는 직전 세대 LPDDR4 및 서버용 DDR5와 어떻게 다른가?

<details>
<summary>정답 / 해설</summary>

- **뱅크 구성**: LPDDR5는 MR로 모드를 선택한다 — **BG 모드(4 BG × 4 = 16뱅크), 8B 모드(8뱅크), 16B 모드(16뱅크)**. 동일 BG 내 연속 접근에는 긴 tCCD_L, 다른 BG 간에는 짧은 tCCD_S가 적용되므로, BG 모드는 BG 분산으로 throughput을 높일 수 있는 반면 8B/16B 모드는 BG 제약 없이 단순한 스케줄링을 제공한다. 비교로 LPDDR4는 BG 없는 8뱅크 고정이고, DDR5(×4/×8)는 8 BG × 4 = 32뱅크 고정이다.
- **Prefetch**: LPDDR5는 **16n prefetch**(BL16), 그리고 BL32 모드를 지원한다. LPDDR4도 이미 16n이며, DDR5도 16n(BL16, +BC8 chop), DDR4는 8n(BL8)이다. 즉 prefetch 16n은 LPDDR4 세대부터의 특징이지 DDR5만의 신규 항목이 아니다.

검증 관점에서는 동작 중 선택된 뱅크 모드에 따라 BG 타이밍(tCCD_L/S) 적용 여부와 bank conflict 시나리오가 달라지므로, 세 모드 각각에 대한 테스트 벡터를 분리해 커버해야 한다.

</details>
## Q7. (Evaluate)

LPDDR5의 On-die ECC와 Link ECC가 "직교(orthogonal)"하다는 말의 의미는? 둘 중 하나로 다른 하나를 대체할 수 있는가?

<details>
<summary>정답 / 해설</summary>

대체할 수 **없다**. 둘은 보호 대상이 서로 다르기 때문이다.

- **On-die ECC**: DRAM 다이 내부의 셀 비트 오류(retention 약화, 미세 결함 등)를 정정한다. SECDED 형태로 DRAM 내부에서 투명하게 동작하며, DDR5에서는 표준이고 LPDDR5에서는 디바이스 의존이다. 보호 범위는 셀~센스앰프 경로에 한정된다.
- **Link ECC**: MC와 DRAM 사이의 **DQ 전송경로**에서 발생하는 비트 오류(채널 노이즈, ISI, crosstalk)를 보호한다. 이는 LPDDR5 고유 기능으로 DDR5에는 없으며, 셀 내부가 아니라 "링크"를 보호한다.

따라서 셀 내부가 완벽해도 채널이 나쁘면 Link ECC가 필요하고, 채널이 완벽해도 셀이 약하면 On-die ECC가 필요하다 — 보호 구간이 겹치지 않으므로 직교적이며, 신뢰도를 위해 둘을 함께 사용한다. 검증에서는 각각에 대해 별도의 error injection 시나리오(셀 비트 fault vs DQ 라인 fault)를 구성해야 한다.

</details>
