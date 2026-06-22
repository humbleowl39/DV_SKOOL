---
title: "Quiz — Module 03: Memory Interface / PHY"
---

[← Module 03 본문으로 돌아가기](../../03_memory_interface_phy/)

---

## Q1. (Remember)

PHY Training의 핵심 4가지 종류를 답하세요.

<details>
<summary>정답 / 해설</summary>

1. **CBT (Command Bus Training, Mode 1/2)**: LPDDR5의 CA 버스는 단일종단 다중사이클(CA[6:0])이라 CBT가 필수다. PHY가 CA delay와 내부 Vref를 조정하면서 DRAM이 명령/주소를 정확히 디코딩하는 지점을 찾는다. (서버용 DDR5는 CA[13:0] 2-cycle 구조로 CA(CS) Training을 수행한다.)
2. **WCK2CK Leveling**: LPDDR5 고유 단계로, 데이터용 고속 WCK와 명령용 저속 CK 사이의 위상을 정렬한다. DVFSC로 gear가 바뀌어 WCK:CK 비(2:1/4:1)가 변하면 이 leveling을 다시 수행해야 한다.
3. **Read/Write DQ Training**: PHY·DRAM 양 수신단에서 DQ를 샘플할 최적 지점을 찾는다. eye diagram의 수평·수직 중앙을 탐색해 노이즈 마진을 최대화한다.
4. **VREF Training**: 수신 threshold 전압을 최적화한다. LPDDR5는 내부 Vref를 사용하며, VREF가 너무 높거나 낮으면 eye의 전압 마진이 감소해 같은 타이밍에도 bit error가 증가한다.

LPDDR5는 CBT + WCK2CK Leveling + DQ(Read/Write) 단계까지 포함해 직전 세대보다 training 단계가 가장 많다. ZQ Calibration은 training은 아니지만 온도 변화에 따른 드라이버/ODT 임피던스를 주기적으로 보정해 신호 품질을 유지한다.

</details>
## Q2. (Understand)

PVT 변동이 timing에 미치는 영향과 보정 방법은?

<details>
<summary>정답 / 해설</summary>

**영향**: 시리콘 Process variation은 트랜지스터의 구동 능력을, 전압 droop은 전파 속도를, 온도 변화는 캐리어 이동도를 바꾼다. 세 요인 모두 신호 propagation delay를 변화시켜 eye diagram의 위치와 크기가 초기 training 시점과 달라진다. 마진이 좁은 고속 인터페이스에서는 이 변화가 bit error를 유발하기에 충분하다.

**보정**: 전원 인가 후 초기 training으로 시작점을 잡은 뒤, 운용 중에는 주기적 retraining이나 온도 센서 트리거를 통해 재보정한다. ZQ Calibration은 임피던스 변화를 수시로 수정해 신호 무결성을 유지한다. 모든 보정은 traffic이 없는 idle 구간에 수행하거나 짧은 stall을 수반하므로, MC와 PHY 간 handshake 프로토콜이 중요하다.

</details>
## Q3. (Apply)

CTLE와 DFE의 차이와 각각의 적용 위치는?

<details>
<summary>정답 / 해설</summary>

- **CTLE**: 채널을 통과하면서 고주파 성분이 감쇠된 신호를 아날로그 필터로 부스트해 원래 파형에 가깝게 복원한다. 전체 비트에 동일하게 적용되므로 구현이 단순하지만, 노이즈도 같이 증폭되는 단점이 있다.
- **DFE**: 이전에 수신한 비트의 판정 결과를 피드백해 현재 비트에 얹힌 ISI(Inter-Symbol Interference) 성분을 디지털로 빼낸다. 노이즈를 증폭하지 않고 ISI만 선별적으로 제거하므로 고속·고마진 설계에 적합하다.

적용 위치로는, PHY 수신단(Read path)에 CTLE + DFE 조합을 쓰는 것이 일반적이다. CTLE로 전반적 채널 감쇠를 보상한 뒤 DFE로 잔여 ISI를 제거한다. DRAM 수신단(Write path)은 면적·전력 제약으로 DFE만 탑재하는 경우가 많다.

</details>
## Q4. (Analyze)

LPDDR5에서 CBT(Command Bus Training)가 필수인 이유는?

<details>
<summary>정답 / 해설</summary>

LPDDR5의 CA 버스는 핀 수를 줄이기 위해 **단일종단(single-ended) CA[6:0]를 다중사이클로 운용**한다. 단일종단이라 차동 대비 노이즈 마진이 작고, 다중사이클로 명령을 나눠 보내므로 각 사이클의 setup/hold 마진이 빠듯하다. 마진이 부족하면 DRAM이 CA를 잘못 디코딩해 전혀 의도하지 않은 명령이 실행될 수 있으며, 이런 오류는 데이터가 아닌 제어 흐름 오류이므로 ECC로도 잡을 수 없다. CBT(Mode 1/2)는 각 CA 핀의 delay와 내부 Vref를 조정해 DRAM의 setup/hold window 중앙에 신호가 들어오도록 보정함으로써 이 위험을 해소한다. (비교: 서버용 DDR5는 CA[13:0] 2-cycle 구조에서 CA(CS) Training을 수행한다.)

</details>
## Q5. (Evaluate)

Training 실패의 silent corruption은 어떻게 catch하는가?

<details>
<summary>정답 / 해설</summary>

Training이 "pass"를 선언해도 실제로 마진이 매우 좁은 상태일 수 있어, 정상 traffic에서는 문제없다가 PVT 변동·high-speed burst 등 stress 조건에서 조용히 bit error를 내는 것이 silent corruption의 전형적인 패턴이다.

- **Functional 검증**: training 직후 패턴 기반 write/read test를 수행해 데이터 불일치 여부를 확인한다. 이상이 없으면 eye는 열려 있지만, 마진은 좁을 수 있다.
- **Performance 지표**: training 결과로 달성된 BW·latency가 spec의 하한에 근접하거나 미달하면 sub-optimal training을 의심하고 재training이나 파라미터 조정을 검토한다.
- **SVA 검증**: training 완료 핸드셰이크 시퀀스가 JEDEC spec의 순서와 일치하는지 assertion으로 자동 검사해, 시퀀스 자체의 오류로 인한 잘못된 training 완료 선언을 포착한다.
- **PVT corner sweep**: cold boot, hot steady-state, low VDD corner에서 training을 실행해 marginal pass가 발생하는 환경을 선별한다.

</details>
## Q6. (Understand)

LPDDR5의 DVFSC와 DVFSQ는 각각 무엇을 스케일링하며, PHY 검증에 어떤 영향을 주는가?

<details>
<summary>정답 / 해설</summary>

- **DVFSC (Dynamic Voltage Frequency Scaling – Core)**: 코어/주파수 gear(F0~F4 등)를 동적으로 전환해 동작 주파수와 그에 맞는 코어 전압을 함께 낮추거나 올린다. gear 전환 시 WCK:CK 비(2:1↔4:1)가 바뀌므로 **WCK2CK leveling을 재수행**해야 한다.
- **DVFSQ (Dynamic Voltage Frequency Scaling – IO/Q)**: IO 측(VDDQ)을 동적으로 스케일링해 데이터 IO 전력을 줄인다. LPDDR5의 VDDQ는 0.5V 수준까지 낮아져 있어, IO 전압이 바뀌면 수신 eye와 Vref 동작점이 달라진다.

검증 관점에서는 두 스케일링이 독립적으로 또는 함께 일어날 수 있으므로, **각 gear 조합에서 retraining(특히 WCK2CK)과 데이터 무결성**이 보장되는지, 그리고 gear 전환 도중(transient)에 명령이 깨지지 않는지를 별도 시나리오로 커버해야 한다.

</details>
