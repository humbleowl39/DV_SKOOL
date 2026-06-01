# Ch12 퀴즈 — UVM × RNM Integration

## Q1. (Remember)
UVM-DMS env의 표준 토폴로지를 구성하는 핵심 component 6가지를 나열하시오.

## Q2. (Remember)
Analog agent의 driver와 monitor가 digital agent와 다른 "비대칭" 두 측면을 한 문장씩 쓰시오.

## Q3. (Understand)
Virtual sequence가 mixed-signal env에서 특히 중요한 이유를 한두 줄로 설명하시오.

## Q4. (Understand)
`clocking` block에 `real` 신호를 직접 넣는 것을 권장하지 않는 이유와 안전 패턴은?

## Q5. (Apply)
`sequence_item`이 sine wave 자극을 표현하려고 한다. (a) sequence_item 필드 (b) driver의 처리 방식 (c) interface helper의 책임을 각각 한 줄로 쓰시오.

## Q6. (Apply)
ADC scoreboard에서 `expected.vin_volt = 1.205 V`, `observed.vin_sampled = 1.207 V`, abs_tol = 1 mV, rel_tol = 5 ‰일 때 match인가 mismatch인가? 계산식과 함께 답하시오.

## Q7. (Analyze)
Multi-rate sync 문제: analog monitor가 zero-crossing 이벤트(sparse)를 publish하고 register monitor가 cycle마다 publish할 때, 같은 scoreboard에서 두 stream을 정렬하는 두 가지 matching key를 쓰고 각각의 장단점을 설명하시오.

## Q8. (Analyze)
scoreboard에서 fail이 났는데 mismatch가 noise 모드에서만 발생한다. Ch10 §8.5의 "model bug vs DUT bug 구별법" 표를 활용해 첫 한 시간 안에 좁힐 수 있는 실험 3가지를 제안하시오.

## Q9. (Evaluate)
DUT wrapper의 ``ifdef`` 기반 RNM/SPICE swap-in과 UVM factory override 기반 swap 중, mixed-signal 환경에 어느 것이 더 적합한지 trade-off와 함께 평가하시오.

## Q10. (Create)
한 IP env(adc_env)가 SoC env(soc_env)에서 재사용될 수 있게 하는 최소 설계 결정 5가지를 나열하시오 (config object, sequencer 핸들, factory override, virtual sequencer, agent active/passive 관점).

---

## 정답 및 해설

**Q1.** ① analog_agent (sequencer + driver + monitor) ② reg_agent / RAL ③ irq_agent ④ virtual sequencer ⑤ DUT wrapper (RNM + RTL) ⑥ scoreboard + ref model + coverage. (UVM test가 가장 위, 모두 한 env 안.)

이 6개 컴포넌트가 UVM-DMS env의 표준 뼈대를 이룬다. analog_agent는 real-valued interface를 통해 아날로그 자극을 인가하고 관측한다. reg_agent/RAL은 디지털 register 인터페이스 접근을 담당하고, irq_agent는 비동기 인터럽트/event를 모니터링한다. virtual sequencer는 여러 agent를 동기화하는 역할이며, DUT wrapper는 RNM 모델과 RTL을 묶는 껍데기다. scoreboard, ref model, coverage는 functional correctness를 판단한다.

**Q2.** Driver: digital은 cycle 단위 transaction → 신호, analog는 transaction → **시간×값 sub-event 시퀀스** (수 ns/sample)로 풀어야 함. Monitor: digital은 cycle 단위 sample → transaction, analog는 **trigger 기반(zero-cross/settled/eoc)** sampling으로 의미 단위 transaction을 만듦.

digital agent의 driver는 clock edge마다 transaction을 신호로 변환하는 단순한 사이클 기반 루프이다. analog driver는 하나의 "input voltage ramp" transaction을 수십~수백 ns에 걸쳐 sub-event(시간 + 전압 값) 시퀀스로 펼쳐야 한다. monitor도 마찬가지로, digital monitor는 clock edge마다 샘플링하지만 analog monitor는 "신호가 threshold를 넘었다", "변화가 멈추고 settled 됐다" 같은 물리적 event를 기준으로 transaction을 만든다.

**Q3.** Mixed-signal 시나리오는 보통 register write → analog ramp 시작 → settled 대기 → 결과 읽기처럼 **여러 도메인의 동기**가 필요하므로, 한 sequence가 모든 sequencer로 sub-seq를 적절히 보내는 virtual sequence 패턴이 가독성·재사용성에 필수.

mixed-signal 시나리오의 본질은 "디지털 제어 → 아날로그 반응 → 다시 디지털로 읽기"의 순환이다. 예를 들어 ADC 변환을 검증할 때 register write(디지털), analog 입력 ramp 인가(아날로그), EOC 대기(디지털 interrupt), 코드 read back(디지털 register)이 특정 순서로 조율되어야 한다. 각 agent에 별도 sequence를 보내는 것보다 virtual sequence 하나가 전체 흐름을 orchestrate하면 시나리오 의도가 한눈에 보이고 재사용성도 높다.

**Q4.** `real`/nettype 신호의 clocking 지원이 **vendor마다 다르고** elaboration 결과가 달라집니다. 안전 패턴은 **별도 `always @(posedge clk) sampled <= vif.vsig.V` 블록**에서 sample하고 monitor가 그 sample을 transaction화하는 것 — vendor 호환성 최고이고 race-free.

`clocking` block은 digital signal의 setup/hold 관계를 정의하기 위해 설계된 것으로, IEEE 1800 표준에서 `real`/nettype 신호에 대한 clocking block 동작이 명확히 정의되어 있지 않다. 실제로 VCS, Xcelium, Questa에서 동일한 코드가 다르게 elaboration되거나 runtime에 다르게 동작하는 사례가 있다. `always` 블록으로 수동 샘플링하는 방식은 모든 simulator에서 동일하게 동작하며 clocking block의 race 조건도 피할 수 있다.

**Q5.** (a) `rand real ampl, bias, freq_hz, T_ns, int steps` 등 sine 파라미터. (b) driver는 `case (it.kind) ADC_SINE: vif.apply_sine(...)`로 interface helper에 위임 (driver 자체에 wave 알고리즘 없음). (c) interface helper(`apply_sine` task)가 cycle 당 N step으로 `vsig.V = bias + ampl*sin(...)` 직접 sub-event 발생, dt만큼 `#(dt * 1ns)` 대기 반복.

책임 분리가 핵심이다. sequence_item은 "어떤 파형을 원하는가"를 데이터로 표현하고(파라미터만 보유), driver는 "이 요청을 interface에 전달하라"는 dispatcher 역할을 하며, interface helper(task)가 실제 waveform 생성을 담당한다. driver에 직접 `sin(...)` 계산을 넣으면 driver가 특정 waveform 타입에 묶여 재사용성이 떨어진다.

**Q6.** `diff = |1.205 - 1.207| = 0.002 V (=2 mV)`. `allow = abs_tol + rel_tol × |exp| = 1e-3 + 5e-3 × 1.205 = 1.0e-3 + 6.025e-3 = 7.025e-3 V`. `diff (2 mV) ≤ allow (7.025 mV)` → **match**.

이 tolerance 모델은 절대 오차(abs_tol)와 상대 오차(rel_tol)를 합산한다. abs_tol은 "측정값 크기에 관계없이 최소 허용 오차"이고, rel_tol은 "expected 값에 비례한 오차"이다. 두 가지를 합산하는 이유는 신호가 0에 가까울 때 relative tolerance만으로는 과도하게 엄격해지고, 신호가 클 때 absolute tolerance만으로는 너무 관대해지는 극단을 피하기 위해서다. 이 문제에서 diff = 2 mV가 allow = 7.025 mV보다 작으므로 match다.

**Q7.** (1) **시간 key**: 두 monitor 각자 `t_ns` 필드를 transaction에 포함, "reg write 이후 첫 lock 이벤트가 100 us 안" 같은 시간 윈도우로 match. 장점: 직관적 / 단점: drop·추가 1회면 모두 어긋남. (2) **id/일련번호 key**: 양쪽이 동일한 transaction id를 공유하는 hash matching. 장점: drop에 robust / 단점: id를 두 도메인이 합의해야 하므로 도구 지원 필요.

multi-rate 문제는 두 monitor의 transaction 발생 빈도가 근본적으로 다르기 때문에 생긴다. register monitor는 매 cycle마다 transaction을 만들지만 analog monitor는 lock event처럼 수백 us에 한 번 만들 수 있다. scoreboard에서 이 두 stream을 어떻게 짝 지을 것인가가 핵심 설계 결정이다. 시간 key는 구현이 단순하지만 event 한 개 누락에도 전체 정렬이 무너지는 취약점이 있고, id key는 구현 복잡도가 높지만 누락에 robust하다.

**Q8.** ① noise model을 끄고 같은 seed로 회귀 — fail이 사라지면 noise 모델 자체가 의심 (예: `$dist_normal` σ 단위 스케일 오류). ② noise 회귀에서 tolerance를 spec band까지 일시 완화 → fail 패턴 변화 관찰. ③ noise 주입 위치를 DUT 입력으로 옮겨 reference model에도 같은 noise 시퀀스 적용 → ref 단독 unit test. (Ch10 §8.5 표의 "tolerance 한시 완화" + "reference unit test" + "noise on/off 비교" 3가지에 해당.)

"noise 모드에서만 발생"이라는 단서는 두 가지 가능성을 시사한다. 첫째는 noise 자체가 문제(주입 양이 너무 크거나 단위 오류), 둘째는 noise로 인해 드러나는 실제 DUT/모델 버그다. ①번 실험으로 전자를 먼저 배제하고, ②번으로 fail이 tolerance 경계 근방인지 확인하며, ③번으로 reference model에 같은 noise를 주었을 때 ref가 올바르게 동작하는지 검증하면 세 가지 실험만으로 1시간 안에 범위를 크게 좁힐 수 있다.

**Q9.** **`ifdef`가 mixed-signal에 보통 더 적합**. 이유: ① elaboration log에 model 종류가 한 줄로 보여 build option ↔ regression list 일대일 추적. ② Spice subckt 호출은 elaboration time에 결정되어야 하는 vendor-specific 구문 — runtime factory override로는 swap이 어렵거나 불가. ③ factory override는 같은 SV class 계열에 강력하지만, Spice/VAMS instance까지는 못 다룸. UVM factory override는 **agent/scoreboard 레벨의 동작 swap**(strict/relaxed scoreboard 등)에 더 적합.

UVM factory override는 SV class 계층에서 한 class를 다른 class로 동적으로 교체하는 강력한 메커니즘이다. 그러나 "RNM SV 모듈"과 "SPICE netlist 인스턴스"는 SV class 계층에 속하지 않는 다른 언어 객체이므로 factory가 다루기 어렵다. `ifdef`는 compile/elaboration 시점에 어떤 모델을 연결할지를 명확하게 결정하고, regression script에서 compile 옵션 하나로 mode를 바꿀 수 있어 mixed-signal flow에 더 실용적이다.

**Q10.** ① `env_cfg` object에 sequencer 핸들·tolerance·model_kind·noise_seed를 모아두기 ② `uvm_config_db`로 cfg를 외부에서 inject 가능하게 ③ agent를 `is_active`로 SoC에서 monitor-only 전환 가능하게 ④ virtual sequencer가 cfg.sequencer 핸들을 통해 작동하도록 분리 ⑤ DUT wrapper의 RNM/SPICE swap을 build-time option으로 분리해 IP regression list와 SoC regression list 양쪽에서 같은 wrapper 재사용.

IP를 SoC env에서 재사용할 때 가장 흔한 문제는 IP env가 내부 state를 하드코딩하거나, sequencer 핸들이 고정되어 있거나, agent가 항상 active mode로 동작하거나, DUT wrapper가 IP-specific compile 옵션에 의존하는 것이다. 이 5가지 설계 결정을 올바르게 해두면 SoC 통합 시 IP env를 거의 수정 없이 재사용할 수 있다. 특히 `is_active` 설정은 SoC에서 다른 master가 이미 구동 중인 interface를 IP env가 중복으로 구동하는 충돌을 막는다.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../12_uvm_rnm_integration.md)
