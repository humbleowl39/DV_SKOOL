# Ch02 퀴즈 — 세 시뮬레이션 세계

## Q1. (Remember)
Digital · SPICE · RNM의 신호 표현 차이를 한 줄씩 쓰시오.

## Q2. (Remember)
RNM이 사용하는 시간 처리 방식은? (이벤트 기반 / 연속시간 / 양쪽)

## Q3. (Understand)
AMS와 RNM 두 통합 방식의 가장 큰 차이를 설명하시오.

## Q4. (Understand)
RNM이 DRAM 산업에서 표준이 된 가장 핵심적인 이유 두 가지를 쓰시오.

## Q5. (Apply)
다음 시나리오에 RNM/AMS/IBIS-AMI 중 적합한 것을 선택하시오.
a) PCIe Gen5 link training back-channel
b) PMIC buck regulator dynamic response
c) DDR5 PHY full-chip functional regression

## Q6. (Apply)
RNM 5단계 정확도 모델에서, DRAM 산업이 일반적으로 사용하는 단계는?

## Q7. (Analyze)
한 SerDes 검증에서 BER 1e-12를 달성해야 한다. 일반 RNM 시뮬레이션이 부족한 이유는?

## Q8. (Evaluate)
"AMS가 RNM보다 항상 정확하므로 AMS만 쓰면 된다"는 주장을 평가하시오.

---

## 정답 및 해설

**Q1.** Digital: logic 0/1/X/Z. SPICE: 실수 전압/전류 (연속). RNM: 실수값 (`real`, event-driven).

세 패러다임은 "무엇을 신호로 표현하는가"에서 근본적으로 갈린다. Digital simulator는 4-state logic으로 전압을 추상화하기 때문에 0.7 V 같은 중간 레벨을 표현할 수 없다. SPICE는 시간에 따라 연속으로 변화하는 실수 전압·전류를 매 timestep마다 계산하므로 가장 정확하지만 가장 느리다. RNM은 digital simulator 안에 `real` 타입 변수를 도입해서 이벤트가 발생할 때만 값을 갱신한다 — 연속 계산 없이도 voltage 레벨을 다룰 수 있어 속도와 표현력을 동시에 확보한다.

**Q2.** 이벤트 기반.

RNM은 SPICE처럼 매 time step마다 계산하지 않고, 이벤트(신호 변화, 활성화 트리거 등)가 일어날 때만 `real` 값을 다시 계산한다. 이것이 SPICE 대비 속도 우위의 핵심 이유다. "연속시간"을 선택한다면 그것은 SPICE(또는 Verilog-AMS analog 부분)의 동작 방식이고, RNM과는 구별된다.

**Q3.** AMS는 두 시뮬레이터(digital + SPICE)를 결합해 connect module로 잇고, RNM은 하나의 digital simulator 안에서 real-valued 함수로 모든 것을 처리.

AMS는 두 개의 별도 엔진이 협력하는 구조이기 때문에 두 엔진 사이의 동기화 오버헤드와 SPICE 라이선스가 모두 필요하다. RNM은 digital simulator 하나만 사용하므로 추가 라이선스가 없고 simulator-to-simulator 동기화 비용도 없다. 이 차이가 속도와 비용에 직접적인 영향을 준다.

**Q4.** ① DRAM 셀 수가 너무 많아 SPICE 불가 ② `nettype`이 SV 표준이라 vendor lock-in 없음 (UVM과 공존).

DRAM은 단일 칩에 수십억 개의 bit cell이 있어 SPICE는 물리적으로 불가능하다. 여기에 더해 `nettype`은 IEEE 1800-2012 표준에 정의된 기능이어서 VCS, Xcelium, Questa 중 어느 simulator에서도 동일하게 동작한다 — 특정 벤더에 묶이지 않으면서 UVM 환경과 자연스럽게 통합된다. 이 두 이점이 맞물려 DRAM 산업에서 RNM이 사실상 표준이 되었다.

**Q5.** a) IBIS-AMI  b) RNM + SPICE corner  c) RNM (only).

a) PCIe Gen5 back-channel은 수 Gbps의 직렬 신호로 equalizer(CTLE/DFE/CDR)의 behavioral 모델이 필요하므로 IBIS-AMI가 표준이다. b) PMIC buck regulator는 동적 응답(전압 ripple, 과도 응답)을 보는데 대량 시나리오는 RNM으로 빠르게 돌리고 critical margin은 SPICE corner로 확인한다. c) DDR5 PHY 전체 functional regression은 수천 시나리오를 빠르게 돌려야 하므로 RNM만으로도 충분하다.

**Q6.** Level 2~3 (ramp transition + threshold/hysteresis).

Level 0은 단순 logic delay, Level 1은 real 출력을 추가한 수준이다. DRAM 산업에서는 bit-line 전압 발달 곡선(ramp)과 sense amp의 threshold/hysteresis를 모두 표현해야 timing margin 검증이 가능하므로 Level 2~3이 필요하다. Level 4 이상(noise, jitter, charge conservation)은 특수 sign-off 시나리오에서만 쓴다.

**Q7.** 1e-12는 1조 sample이 필요 — 일반 RNM은 ~10⁶ sample 한계. **Statistical eye + IBIS-AMI**가 표준 해법.

BER 1e-12를 직접 시뮬레이션으로 확인하려면 적어도 1조 비트를 전송해야 통계적으로 유의미한 결과가 나온다. 일반 RNM은 한 시뮬레이션 run에서 수백만 이벤트 수준이 한계여서 이 요구를 충족하지 못한다. 대신 statistical eye 기법으로 jitter/noise 분포를 수학적으로 합성하거나 IBIS-AMI의 algorithmic 블록으로 equalizer 효과를 모델링하면 수십억 비트 equivalent의 eye를 현실적 시간 안에 계산할 수 있다.

**Q8.** AMS는 SPICE 부분이 병목 → 큰 칩 sim 불가능. 또한 칩 전체를 AMS로 돌리면 sign-off 한 번에 며칠 ~ 수 주 걸려 비현실적. RNM 우선 + AMS corner가 산업 표준.

AMS가 RNM보다 항상 정확한 것은 맞지만, "항상 더 정확하므로 항상 더 낫다"는 주장은 성립하지 않는다. 정확도가 높아도 시뮬레이션이 수 주가 걸린다면 tape-out 전에 충분한 scenario를 검증할 수 없어 오히려 위험해진다. 산업 표준은 RNM으로 빠르게 넓은 scenario를 cover하고, AMS와 SPICE는 정밀한 sign-off가 필요한 특정 critical block에 국한해서 사용하는 것이다.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../02_three_worlds_spice_ams_rnm.md)
