# Ch07 퀴즈 — DLL Deep Dive

## Q1. (Remember)
DLL의 4가지 구성요소를 나열하시오.

## Q2. (Remember)
PLL과 DLL의 가장 큰 차이는?

## Q3. (Understand)
DLL이 lock을 잡는 메커니즘을 한 문장으로 설명하시오.

## Q4. (Understand)
Harmonic lock이란 무엇이며 왜 위험한가?

## Q5. (Apply)
다음 사양에서 DLL lock 시간을 계산하시오.
- REF 1 ns, replica 0.2 ns, 초기 ctrl=0, step 5 ps/cycle, lock 안정 16 cycle.

## Q6. (Apply)
Limit cycle oscillation을 막기 위해 추가해야 할 메커니즘 한 가지를 코드로 보여주시오.

## Q7. (Analyze)
DLL의 ctrl이 max value에 saturate 했을 때 가능한 원인 두 가지를 분석하시오.

## Q8. (Evaluate)
"Lock detector는 16 cycle 안정이면 충분하다"는 주장을 jitter 환경에서 평가하시오.

---

## 정답 및 해설

**Q1.** Phase Detector (PD), Loop Filter (LF), Delay Line (DL), Replica Delay.

DLL의 4 블록은 각자 뚜렷한 역할을 한다. PD는 REF clock과 feedback 사이의 위상 오차를 측정하고, LF는 그 오차를 누적해 ctrl 신호로 평탄화한다. DL은 ctrl에 따라 delay를 조절하는 가변 delay chain이다. Replica Delay는 실제 데이터 경로의 delay를 모방하여 feedback 신호를 만들어주는 핵심 요소다. PLL과 달리 VCO가 없고 주파수 생성도 없다는 점이 구조상 큰 차이다.

**Q2.** PLL은 VCO로 새 주파수 생성, DLL은 입력 주파수를 유지하면서 가변 delay로 위상만 정렬.

PLL의 VCO는 제어 전압에 따라 새로운 주파수를 발진시키므로 출력 주파수가 입력과 다를 수 있다(체배, 분주 등). DLL은 발진기 없이 입력 clock을 그대로 통과시키면서 delay만 조절하여 위상을 정렬한다. 따라서 DLL은 출력 주파수가 항상 입력과 같고, 주파수 가변이나 체배 기능이 없다. DRAM처럼 외부 clock을 내부에서 정확하게 정렬하는 용도에 DLL이 적합한 이유다.

**Q3.** PD가 REF·feedback 위상 차이를 감지 → LF가 ctrl 값을 증감 → DL의 delay가 변해 차이를 줄임 → 안정점에 수렴.

이 negative feedback loop는 "feedback이 REF보다 늦으면 delay를 줄이고, 빠르면 늘린다"는 원리로 동작한다. LF는 고주파 잡음을 걸러내어 ctrl 신호가 매 cycle 크게 진동하지 않도록 한다. 안정점에서는 PD 출력이 0에 가까워 ctrl이 더 이상 변하지 않는다.

**Q4.** N cycle(N≥2) 거리에 lock하는 false lock. 출력이 REF와 다른 주기로 정렬되어 시스템 timing 전체가 어긋남.

DLL은 REF clock의 rising edge 중 어느 것이든 feedback과 맞추면 "lock"으로 판정할 수 있다. 원하는 것은 1 cycle 이내 정렬이지만, 2 cycle 또는 3 cycle 전의 edge에 맞추는 것도 PD 입장에서 phase error가 0으로 보일 수 있다. 이렇게 되면 출력 데이터의 타이밍이 시스템이 기대하는 위치와 N cycle 어긋나고, 읽기 윈도우 전체가 잘못 정렬된다.

**Q5.** 목표 = 1 - 0.2 = 0.8 ns = 800 ps. step = 5 ps → 160 cycle. 1 cycle = 1 ns → 160 ns + 16 cycle 안정 = **176 ns**.

DLL은 replica delay가 1 ns(한 REF cycle)와 같아질 때 lock된다. replica의 초기 delay는 0.2 ns이므로 0.8 ns를 더 추가해야 한다. 5 ps/cycle로 증가하면 800/5 = 160 cycle이 필요하다. REF 주기가 1 ns이므로 160 cycle은 160 ns이고, 여기에 lock 안정 판정에 필요한 16 cycle(16 ns)을 더하면 176 ns다.

**Q6.** Dead zone 추가:
```systemverilog
if (phase_err_ps > DEAD_ZONE && ctrl > 0)
  ctrl <= ctrl - 1;
else if (phase_err_ps < -DEAD_ZONE && ctrl < MAX)
  ctrl <= ctrl + 1;
// else: hold
```

Limit cycle oscillation은 PD 감도가 높아서 lock 근방에서 ctrl이 +1 → -1 → +1을 반복하는 현상이다. Dead zone을 설정하면 phase error가 ±DEAD_ZONE 이내일 때 ctrl을 변경하지 않고 그대로 유지(hold)하여 진동을 막는다. Dead zone이 너무 크면 phase error가 남아도 보정하지 않아 lock 정확도가 떨어지므로 적절한 크기 설정이 중요하다.

**Q7.** ① Delay line의 최대 delay < 필요 delay (range 부족) ② Initial condition 잘못 — 반대 방향에 lock 시도. (또는 phase wrap-around 처리 미흡).

ctrl이 max value에 saturate한 상태는 "delay를 더 늘려야 하는데 더 이상 늘릴 수 없다"는 뜻이다. 이는 delay line의 물리적 range가 부족하거나(회로 설계 문제), 또는 초기 위상 관계가 반대 방향이어서 delay를 줄여야 하는데 엉뚱하게 늘리는 방향으로 lock을 시도하고 있는 경우다. 두 원인 모두 DLL 설계 단계에서 worst-case range 분석으로 사전에 검출해야 한다.

**Q8.** Jitter가 큰 환경에서는 16 cycle 안정 후에도 일시적으로 lock_cnt가 리셋될 수 있어 false unlock 발생. **개선책**: ① N 늘리기 (32, 64 cycle) ② threshold relaxation ③ hysteresis (`lock_cnt` 감소 시 천천히).

"16 cycle 안정"은 jitter가 없거나 작은 환경에서는 충분할 수 있다. 그러나 jitter가 크면 lock 근방에서 PD 출력이 일시적으로 threshold를 넘어 lock_cnt가 리셋될 수 있다. 이는 실제로 lock이 깨진 게 아닌데 false unlock이 보고되는 상황이다. N을 32나 64 cycle로 늘리면 일시적 jitter burst에도 lock 판정이 유지되고, hysteresis를 주면 lock_cnt가 한 번에 0으로 떨어지지 않아 판정이 더 안정적이다.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../07_deepdive_dll_rnm.md)
