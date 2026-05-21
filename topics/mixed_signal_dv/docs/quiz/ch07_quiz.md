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

**Q2.** PLL은 VCO로 새 주파수 생성, DLL은 입력 주파수를 유지하면서 가변 delay로 위상만 정렬.

**Q3.** PD가 REF·feedback 위상 차이를 감지 → LF가 ctrl 값을 증감 → DL의 delay가 변해 차이를 줄임 → 안정점에 수렴.

**Q4.** N cycle(N≥2) 거리에 lock하는 false lock. 출력이 REF와 다른 주기로 정렬되어 시스템 timing 전체가 어긋남.

**Q5.** 목표 = 1 - 0.2 = 0.8 ns = 800 ps. step = 5 ps → 160 cycle. 1 cycle = 1 ns → 160 ns + 16 cycle 안정 = **176 ns**.

**Q6.** Dead zone 추가:
```systemverilog
if (phase_err_ps > DEAD_ZONE && ctrl > 0)
  ctrl <= ctrl - 1;
else if (phase_err_ps < -DEAD_ZONE && ctrl < MAX)
  ctrl <= ctrl + 1;
// else: hold
```

**Q7.** ① Delay line의 최대 delay < 필요 delay (range 부족) ② Initial condition 잘못 — 반대 방향에 lock 시도. (또는 phase wrap-around 처리 미흡).

**Q8.** Jitter가 큰 환경에서는 16 cycle 안정 후에도 일시적으로 lock_cnt가 리셋될 수 있어 false unlock 발생. **개선책**: ① N 늘리기 (32, 64 cycle) ② threshold relaxation ③ hysteresis (`lock_cnt` 감소 시 천천히).

[← 퀴즈 인덱스](index.md) · [본문 ↗](../07_deepdive_dll_rnm.md)
