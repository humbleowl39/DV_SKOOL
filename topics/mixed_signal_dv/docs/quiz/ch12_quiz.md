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

**Q2.** Driver: digital은 cycle 단위 transaction → 신호, analog는 transaction → **시간×값 sub-event 시퀀스** (수 ns/sample)로 풀어야 함. Monitor: digital은 cycle 단위 sample → transaction, analog는 **trigger 기반(zero-cross/settled/eoc)** sampling으로 의미 단위 transaction을 만듦.

**Q3.** Mixed-signal 시나리오는 보통 register write → analog ramp 시작 → settled 대기 → 결과 읽기처럼 **여러 도메인의 동기**가 필요하므로, 한 sequence가 모든 sequencer로 sub-seq를 적절히 보내는 virtual sequence 패턴이 가독성·재사용성에 필수.

**Q4.** `real`/nettype 신호의 clocking 지원이 **vendor마다 다르고** elaboration 결과가 달라집니다. 안전 패턴은 **별도 `always @(posedge clk) sampled <= vif.vsig.V` 블록**에서 sample하고 monitor가 그 sample을 transaction화하는 것 — vendor 호환성 최고이고 race-free.

**Q5.** (a) `rand real ampl, bias, freq_hz, T_ns, int steps` 등 sine 파라미터. (b) driver는 `case (it.kind) ADC_SINE: vif.apply_sine(...)`로 interface helper에 위임 (driver 자체에 wave 알고리즘 없음). (c) interface helper(`apply_sine` task)가 cycle 당 N step으로 `vsig.V = bias + ampl*sin(...)` 직접 sub-event 발생, dt만큼 `#(dt * 1ns)` 대기 반복.

**Q6.** `diff = |1.205 - 1.207| = 0.002 V (=2 mV)`. `allow = abs_tol + rel_tol × |exp| = 1e-3 + 5e-3 × 1.205 = 1.0e-3 + 6.025e-3 = 7.025e-3 V`. `diff (2 mV) ≤ allow (7.025 mV)` → **match**.

**Q7.** (1) **시간 key**: 두 monitor 각자 `t_ns` 필드를 transaction에 포함, "reg write 이후 첫 lock 이벤트가 100 us 안" 같은 시간 윈도우로 match. 장점: 직관적 / 단점: drop·추가 1회면 모두 어긋남. (2) **id/일련번호 key**: 양쪽이 동일한 transaction id를 공유하는 hash matching. 장점: drop에 robust / 단점: id를 두 도메인이 합의해야 하므로 도구 지원 필요.

**Q8.** ① noise model을 끄고 같은 seed로 회귀 — fail이 사라지면 noise 모델 자체가 의심 (예: `$dist_normal` σ 단위 스케일 오류). ② noise 회귀에서 tolerance를 spec band까지 일시 완화 → fail 패턴 변화 관찰. ③ noise 주입 위치를 DUT 입력으로 옮겨 reference model에도 같은 noise 시퀀스 적용 → ref 단독 unit test. (Ch10 §8.5 표의 "tolerance 한시 완화" + "reference unit test" + "noise on/off 비교" 3가지에 해당.)

**Q9.** **`ifdef`가 mixed-signal에 보통 더 적합**. 이유: ① elaboration log에 model 종류가 한 줄로 보여 build option ↔ regression list 일대일 추적. ② Spice subckt 호출은 elaboration time에 결정되어야 하는 vendor-specific 구문 — runtime factory override로는 swap이 어렵거나 불가. ③ factory override는 같은 SV class 계열에 강력하지만, Spice/VAMS instance까지는 못 다룸. UVM factory override는 **agent/scoreboard 레벨의 동작 swap**(strict/relaxed scoreboard 등)에 더 적합.

**Q10.** ① `env_cfg` object에 sequencer 핸들·tolerance·model_kind·noise_seed를 모아두기 ② `uvm_config_db`로 cfg를 외부에서 inject 가능하게 ③ agent를 `is_active`로 SoC에서 monitor-only 전환 가능하게 ④ virtual sequencer가 cfg.sequencer 핸들을 통해 작동하도록 분리 ⑤ DUT wrapper의 RNM/SPICE swap을 build-time option으로 분리해 IP regression list와 SoC regression list 양쪽에서 같은 wrapper 재사용.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../12_uvm_rnm_integration.md)
